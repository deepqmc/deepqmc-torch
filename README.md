# DeepQMC

DeepQMC implements variational quantum Monte Carlo for electrons in molecules, using deep neural networks written in [PyTorch](https://pytorch.org) as trial wave functions. Besides the core functionality, it contains implementations of the following ansatzes:

- PauliNet: https://doi.org/ghcm5p
- DeepErwin: http://arxiv.org/abs/2105.08351

> **Warning**
> This version of the deepqmc package is no longer actively developed. For the latest version visit [deepqmc](https://github.com/deepqmc/deepqmc).

## Installing

Install and update using [Pip](https://pip.pypa.io/en/stable/quickstart/).

```
pip install -U deepqmc[wf,train,cli]
```

## A simple example

```python
from deepqmc import Molecule, evaluate, train
from deepqmc.wf import PauliNet

mol = Molecule.from_name('LiH')
net = PauliNet.from_hf(mol).cuda()
train(net)
evaluate(net)
```

Or on the command line:

```
$ cat lih/param.toml
system = 'LiH'
ansatz = 'paulinet'
[train_kwargs]
n_steps = 40
$ deepqmc train lih --save-every 20
converged SCF energy = -7.9846409186467
equilibrating: 49it [00:07,  6.62it/s]
training: 100%|███████| 40/40 [01:30<00:00,  2.27s/it, E=-8.0302(29)]
$ ln -s chkpts/state-00040.pt lih/state.pt
$ deepqmc evaluate lih
evaluating:  24%|▋  | 136/565 [01:12<03:40,  1.65it/s, E=-8.0396(17)]
```

## Links

- Documentation: https://deepqmc.github.io
