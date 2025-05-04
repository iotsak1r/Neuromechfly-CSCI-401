# Neuromechfly-CSCI-401
## Overview
Neuromechfly-CSCI-401 is a research codebase demonstrating the integration of olfactory-driven navigation algorithms (Neuromechfly) with simulated environments. It provides:
- Sandbox simulations of an agent ("MechFly") navigating in response to odor sources under various conditions.
- Integration tests combining olfaction and vision, and coupling with MineRL-powered Minecraft environments using custom mods to track in-game entities.

## Repository Structure
```sh
├── olfaction_mechfly.py
├── olf_vis_integration_mechfly.py
├── olfaction_mineRL_integration_test.py
├── test_olfaction.py
├── 0.4.4_mods/                   # Custom MineRL integration
│   ├── Villagertracker-1.0.jar   # MineRL 0.4.4 mod for villager tracking
│   └── Villagertracker.java      # Source for the villager tracker mod
├── 1.0.2_mods/                   # Custom MineRL integration
│   ├── Villagertracker-1.0.jar   # MineRL 1.0.2 mod for villager tracking
│   ├── villager_positions.json   # JSON file recording villager position
│   └── Villagertracker.java      # Source for the villager tracker mod
└── outputs/
    ├── olfaction_simulation/     # Visualizations from sandbox-only runs
    └── minerl_olfaction_integration/  # Plots from integration tests
```

## How to Setup
- For MineRL 1.0.2
  
```sh
conda create -n envname python=3.10 anaconda
conda activate envname
pip install flygym
pip install flyvis
```

- For MineRL 0.4.4

Refer to [neuromechcraft](https://github.com/jason-s-yu/neuromechcraft)

## Scripts Breakdown
1. olfaction_mechfly.py
- Purpose: Standalone sandbox simulating MechFly movement driven by two odor sources (one attractive, one aversive).
- Key Components:
  - odor positions perform a constrained random walk in 3D space.
3. olf_vis_integration_mechfly.py
4. olfaction_mineRL_integration_test.py
5. test_olfaction.py



