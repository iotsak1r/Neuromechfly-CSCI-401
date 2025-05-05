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
├── olfaction_movement.py
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
   
    - Purpose: Standalone sandbox simulation of MechFly navigating in an odor‐only arena (no MineRL).
    - Setup:
      - Defines multiple odor sources (odor_source) with peak intensities.
      - Builds an OdorArena and spawns a Fly with olfaction and adhesion enabled.
      - Uses a fixed overhead Camera.
    - Control loop:
      - Stabilization: 500 steps of zero control to settle the fly.
      - Decision: At each interval, read obs["odor_intensity"] for attractive and aversive channels, reshape into (2 sensor types × 2 sides), compute weighted averages, then asymmetry bias:


      ```sh
      attractive_bias = G_attr * (I_left - I_right) / I_mean
      aversive_bias   = G_ave * (I_left - I_right) / I_mean
      b = tanh((attractive_bias + aversive_bias)**2) * sign(attr+ave)
      ```
      - Turning: Compute left/right delta signals from b and send to HybridTurningController.
    - Outputs (in outputs/olfaction_simulation):
      - olfaction_env.png: snapshot of the arena after stabilization.
      - odor_taxis_trajectory.png: X–Y plot of fly path vs odor sources.
      - odor_taxis.mp4: video of the fly’s odor‐taxis behavior.

2. olf_vis_integration_mechfly.py
    - Purpose: Extends the above MechFly olfaction demo with a basic vision module to avoid obstacles.
    - Setup:
      - Uses ObstacleOdorArena with defined obstacle positions, colors, and odor source.
      - Spawns Fly with both enable_vision=True and enable_olfaction=True.
      - Attaches a fixed‐camera bird’s‐eye view.
    - Fusion & Control:
      1. Olfaction: same bias b as in olfaction_mechfly.py.
      2. Vision:
        - Compute mean brightness in left/right retina images.
        - vision_bias = G_vis * (B_left - B_right) / B_mean.
      3. Combined bias:
         
      ```sh
      combined_bias = tanh(olfaction_bias + vision_bias)
      ```
      
      4. Turning & movement: map combined_bias to motor commands and step the physics.
    - Outputs:
      - initial_setup.png: arena layout with obstacles & odor source.
      - fly_trajectory.png: 2D scatter of fly path vs. odor & obstacles.
      - multimodal_navigation.mp4: video of combined olfactory–visual navigation.

3. olfaction_mineRL_integration_test.py
    - Purpose: Work‑in‑progress integration of NeuromechFly olfaction with a MineRL BASALT task (FindCave-v0), planning to use villagers as odor sources.
    - Current behavior:
      - Calls gym.make('MineRLBasaltFindCave-v0') and env.reset().
      - Simulates a moving odor point in 3D; computes exponential‑decay intensity with optional noise:
      
      ```sh
      intensity = exp(-decay_rate * distance)
      ```
      
      - Uses MechFlySimulator.update() (random ±45° turn on drop; speed = 2×intensity, clamped to [0.25, 1.0]).
      - Converts heading & speed into MineRL actions (camera, forward/back, jump), steps & renders the env.
    - Logging & outputs:
      - Writes simulation_log.csv with header:
      
      ```sh
      time,fly_x,fly_y,fly_z,odor_x,odor_y,odor_z,intensity
      ```
      
    - After exit, produces in outputs/:
      - agent.png: X–Z trajectory of agent vs odor source.
      - odor.png: odor‐intensity vs simulation step.
    - Intended workflow (WIP):
      1. VillagerTracker mod writes /run/villager_positions.json each server tick:
      
      ```sh
      [{"name":"Villager","x":…,"y":…,"z":…}, …]
      ```
      
      2. Script reads that JSON (json.load(...)), computes per‑villager intensities, updates MechFlySimulator.
      3. Issues new MineRL actions for closed‑loop integration.

4. test_olfaction.py
    - Purpose: Prototype MineRL integration harness; not true unit tests.
    - Behavior:
      - Very similar to olfaction_mineRL_integration_test.py but with a lower speed clamp (min 0.1) and no CSV logging or plots.
      - Collects fly/odor trajectories in memory, then exits.
    - Status: Blueprint for a proper test suite; should be refactored into real unit tests with assertions and remove MineRL dependency.
  
5. olfaction_movement.py
    - Purpose: Latest iteration of the MineRL‐integrated MechFly simulation, targeting the CreateVillageAnimalPen-v0 BASALT task.
    - Setup & env:
      - env = gym.make('MineRLBasaltCreateVillageAnimalPen-v0'); obs = env.reset().
      - Initializes fly_position & a wandering 3D odor_position.
      - Configurable decay_rate and optional noise.
    - Control loop (up to 1000 steps):
      1. Odor movement: Random walk for odor_position (with simple obstacle‐jump stub).
      2. Intensity: exp(-decay_rate·distance) ± noise.
      3. MechFly update: Same ±45° logic & speed clamp to [0.25, 1.0].
      4. MineRL action:
      
      ```sh
      action = env.action_space.no_op()
      action['camera'] = [0, yaw_change_deg]
      action['forward'], action['back'] = (1,0) if speed>0 else (0,1)
      action['jump'] = 1
      obs, reward, done, info = env.step(action)
      ```
      
      5. Render & position update: Uses info['position'] if available; else approximates.
      6. Sync & log: Sleeps to cap at 20 FPS, writes to simulation_log.csv, and appends to in‑memory trajectories.
      7. Break on done.
    - Visualization:
      - After env.close(), converts trajectories to NumPy, and:
        - Plots X–Z agent vs. odor → outputs/agent.png.
        - Plots intensity vs. step → outputs/odor.png.
        
## Neuromechfly Olfaction & Movement Principles
1. Signal comparison: Each antenna/palp pair yields a 2 × 2 intensity array (attractive vs. aversive × left vs. right).
2. Bias calculation: Differences between left/right means drive a signed bias, scaled by separate gains (G_attr, G_ave).
3. Noise‑triggered exploration: If intensity drops vs. the last step, perturb heading by up to ±45° to re‑orient sampling.
4. Speed modulation: Proportional to instantaneous intensity (×2), but never below a set minimum (0.25 or 0.1), ensuring continuous movement.
5. Sensor fusion (in multimodal demo): Visual obstacle signal (brightness asymmetry) is combined additively with olfactory bias, then nonlinearly normalized (tanh) for smooth steering.

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
