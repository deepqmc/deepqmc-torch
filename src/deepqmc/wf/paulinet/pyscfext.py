import logging
import re
import shutil
from pathlib import Path

import numpy as np
import pyscf.lib.chkfile as chk
from pyscf import dft, gto
from pyscf.mcscf import CASSCF
from pyscf.scf import RHF

gto.mole.float32 = float

__all__ = ()

log = logging.getLogger(__name__)
PYSCF_CHKFILE = 'pyscf.chk'
TRAIL_ZEROS = re.compile(r'0+$')


def eval_ao_normed(mol, *args, **kwargs):
    aos = dft.numint.eval_ao(mol, *args, **kwargs)
    if mol.cart:
        aos /= np.sqrt(np.diag(mol.intor('int1e_ovlp_cart')))
    return aos


def electron_density_of(mf, rs):
    aos = eval_ao_normed(mf.mol, rs)
    return dft.numint.eval_rho2(mf.mol, aos, mf.mo_coeff, mf.mo_occ, xctype='LDA')


def pyscf_from_mol(mol, basis, cas=None, workdir=None):
    if workdir:
        workdir = Path(workdir)
        chkfile = workdir / PYSCF_CHKFILE
        if chkfile.is_file():
            mf, mc = pyscf_from_file(chkfile)
            log.info(f'Restored PySCF object from {chkfile}')
            assert mf.mol.basis == basis
            assert (
                not mc and not cas or (mc.ncas == cas[0] and sum(mc.nelecas) == cas[1])
            )
            return mf, mc
    mol = gto.M(
        atom=mol.as_pyscf(),
        unit='bohr',
        basis=basis,
        charge=mol.charge,
        spin=mol.spin,
        cart=True,
        parse_arg=False,
    )
    log.info('Running HF...')
    mf = RHF(mol)
    mf.kernel()
    if cas:
        log.info('Running MCSCF...')
        mc = CASSCF(mf, *cas)
        mc.kernel()
        if workdir:
            # mf and mc use the same chkfile
            chk.dump(mc.chkfile, 'ci', mc.ci)
            chk.dump(mc.chkfile, 'nelecas', mc.nelecas)
    if workdir:
        shutil.copy(mf.chkfile, chkfile)
    return mf, mc if cas else None


def pyscf_from_file(chkfile):
    mol = chk.load_mol(chkfile)
    mf = RHF(mol)
    mf.__dict__.update(chk.load(chkfile, 'scf'))
    mc_dict = chk.load(chkfile, 'mcscf')
    if mc_dict:
        mc_dict['ci'] = chk.load(chkfile, 'ci')
        mc_dict['nelecas'] = tuple(map(int, chk.load(chkfile, 'nelecas')))
        mc = CASSCF(mf, 0, 0)
        mc.__dict__.update(mc_dict)
    else:
        mc = None
    return mf, mc


def confs_from_mc(mc, tol=0):
    conf_coeff, *confs = zip(
        *mc.fcisolver.large_ci(mc.ci, mc.ncas, mc.nelecas, tol=tol, return_strs=False)
    )
    confs = [
        [np.tile(np.arange(mc.ncore), (len(conf_coeff), 1)), np.array(cfs) + mc.ncore]
        for cfs in confs
    ]
    confs = [np.concatenate(cfs, axis=-1) for cfs in confs]
    strs = np.zeros((len(confs[0]), len(mc.mo_energy)), dtype='i1')
    for i in range(2):
        strs.flat[confs[i] + (np.arange(len(strs)) * strs.shape[-1])[:, None]] += i + 1
    strs = np.array(['0', 'a', 'b', '2'])[strs].view(f'U{strs.shape[-1]}')[:, 0]
    strs = [TRAIL_ZEROS.sub('', s) for s in strs]
    confs = np.concatenate(confs, axis=-1)
    confs = sorted(zip(strs, conf_coeff, confs), key=lambda x: -x[1] ** 2)
    return confs
