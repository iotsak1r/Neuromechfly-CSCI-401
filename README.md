# Neuromechfly-CSCI-401
Testing neuromechfly with cases.

## Available Cases in the Sandbox
- Olfaction with attractive and aversive odor source.
- Integration of olfaction with attractive odor source and vison with obstacle.

## Available Cases in the MineRL Environment
- Olfaction with villagers as attractive source.

## Available Mods
- The mod to find villagers' position and write into a json file.

## How to Setup

- For Cases in the Sandbox
They are only tested in MineRL 1.0.2 version
```sh
conda create -n envname python=3.10 anaconda
conda activate envname
pip install flygym
pip install flyvis
```

- For Cases in the MineRL Environment<br>
It is tested in MineRL 1.0.2 and 0.4.4 version
[neuromechfly 0.4.4 instruction](https://github.com/jason-s-yu/neuromechcraft)

## How to Run
```sh
python filename
```

## Notes
Simulation takes time. Change run_time variable for faster sims and shorter videos.
