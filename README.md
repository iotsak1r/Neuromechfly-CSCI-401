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
├── 0.4.4_mods/
│   ├── Villagertracker-1.0.jar   # MineRL 0.4.4 mod for villager tracking
│   └── Villagertracker.java      # Source for the villager tracker mod
├── 1.0.2_mods/
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
    - Purpose: Standalone sandbox simulation of MechFly navigating in response to two odor sources (one attractive, one aversive).
    - Logging: Opens simulation_log.csv in the working directory and writes at each step:
    ```sh
    time,fly_x,fly_y,fly_z,odor_x,odor_y,odor_z,intensity
    ```
    - Movement policy (MechFlySimulator.update):
      1. Compare current  to last recorded intensity:
         - If weaker, randomly perturb heading by ±45°.
         - Otherwise, maintain heading.
      2. Set speed proportional to  (clamped to [0.25, 1.0]).
      3. Return speed for forward movement.
    - Output plots (saved under outputs/olfaction_simulation):
      - agent.png: X–Z trajectories of agent and odor sources.
      - odor.png: Odor intensity vs. simulation step.
2. olf_vis_integration_mechfly.py
- Purpose: Extends the above with a basic vision module to avoid obstacles.
- Vision module: Sends out rays or checks a proximity threshold; if an obstacle is detected, the agent computes an avoidance vector orthogonal to its heading.
- Decision fusion: Weighted sum of olfactory heading and obstacle‐avoidance vector.
- Logging & visualization: Same CSV logger and plotting routines as in olfaction_mechfly.py.
3. olfaction_mineRL_integration_test.py
- Purpose: Work‐in‐progress integration of Neuromechfly olfaction with a MineRL Basalt task (CreateVillageAnimalPen-v0), using villagers as odor sources.
- Current behavior:
  - Launches a MineRL environment and steps through it using gradient‐based headings, but does not yet read/write villager_positions.json. JSON I/O is WIP.
- Intended workflow:
  1. Villagertracker mod writes /run/villager_positions.json each server tick:
     ```sh
     [{"name":"Villager","x":...,"y":...,"z":...}, ...]
     ```
  2. Python script loads these positions with json.load(...), computes intensities, and updates MechFlySimulator state.
  3. New action (camera yaw, forward/back) is issued back to MineRL.
- Status: Integration test harness is in place; JSON‐I/O and shared‐state synchronization remain under development.
4. test_olfaction.py
- Purpose: Unit tests for core olfactory navigation routines.
- Coverage:
  - Intensity computation correctness.
  - Heading perturbation on signal drop.
  - Speed clamping behavior.

## Neuromechfly Olfaction & Movement Principles
1. Odor dispersion model: Exponential decay with distance (), optionally with Gaussian noise to simulate sensor unreliability.
2. Gradient ascent/descent: Agent compares successive intensity readings:
   - If intensity increases, continue moving straight (exploit plume).
   - If intensity decreases, introduce a random heading change (explore).
3. Speed modulation: , with a minimum baseline speed to avoid stalling.
4. Loop: Sense → Decide (heading/speed) → Act (move/jump) → Sense.

## Villager Tracker Mod
Two versions of the same Forge coremod, one for MineRL 1.0.2 and one for 0.4.4, which:
- Hooks into server ticks.
- Finds EntityVillager within a configurable radius.
- Dumps an array of {name,x,y,z} to villager_positions.json each tick.

## Data Flow
1. Launch MineRL with villager‐tracker mod.
2. Mod writes villager_positions.json each tick.
3. Python polls JSON, computes actions, sends back to MineRL.
4. Loop until episode end.

## Mod Integration Progress
I’m documenting my current progress integrating custom Forge mods into MineRL 0.4.4:
1. Missing run/mods: After installing MineRL 0.4.4, the embedded Malmo clone under .../minerl/Malmo/Minecraft/run/ lacks a mods/ folder. Manually creating one had no effect—launchClient.sh never populates it.
2. Standalone Malmo works: Downloaded the official Malmo release, ran its launchClient.sh, and saw it populate run/ with mods/, logs/, resourcepacks/, etc.
3. MineRL’s launchClient.sh stalls at asset‐download step (getAssets), never reaching the Gradle or Java client launch phases that create those folders.
4. Workaround: Pre‐populate ~/.gradle/caches/minecraft/assets/ with official MC 1.11.2 assets, so getAssets completes locally.
5. Now launchClient.sh runs in the MineRL folder and populates run/mods/—but Python’s env.reset() still crashes with Malmo errors when using custom villager trackers.
6. Next steps:
   - Investigate Forge/FML deobfuscation errors (srg-mcp.srg missing) by ensuring correct gradle.properties and mappings settings.
   - Automate mod‐copy into MineRL’s gradle run directory before each Python launch.
   - Validate villager_positions.json generation under MineRL 0.4.4.
