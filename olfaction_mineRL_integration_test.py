import gym, minerl
import math, random, time
import numpy as np
import matplotlib.pyplot as plt

env = gym.make('MineRLBasaltFindCave-v0')
obs = env.reset()
fly_position = np.array([0.0, 0.0, 0.0])
odor_position = np.array([10.0, 0.0, 3.0])
odor_speed = 0.2
odor_direction = random.uniform(0, 2*math.pi)

decay_rate = 0.1
noise_enabled = True

class MechFlySimulator:
    def __init__(self):
        self.heading = 0.0
        self.speed = 0.0
        self.last_intensity = 0.0
    def update(self, odor_intensity):
        if odor_intensity < self.last_intensity:
            # random turn
            self.heading += random.uniform(-math.pi/4, math.pi/4)
        self.speed = min(1.0, odor_intensity * 2.0)
        if self.speed < 0.25:
            self.speed = 0.25
        self.last_intensity = odor_intensity
        return self.speed

mechfly = MechFlySimulator()

log_file = open('simulation_log.csv', 'w')
log_file.write('time,fly_x,fly_y,fly_z,odor_x,odor_y,odor_z,intensity\n')

fly_trajectory = []
odor_trajectory = []
intensity_history = []

target_step_time = 1.0 / 20.0  # 20 FPS

for t in range(1000):
    loop_start = time.time()
    # Odor random move
    odor_direction += random.uniform(-math.pi/16, math.pi/16)
    next_x = odor_position[0] + odor_speed * math.cos(odor_direction)
    next_z = odor_position[2] + odor_speed * math.sin(odor_direction)
    obstacle_ahead = False
    if obstacle_ahead:
        odor_position[1] += 1  # jump up if obstacle
    odor_position[0] = next_x
    odor_position[2] = next_z

    # Odor intensity
    dx, dy, dz = odor_position[0] - fly_position[0], odor_position[1] - fly_position[1], odor_position[2] - fly_position[2]
    distance = math.sqrt(dx*dx + dy*dy + dz*dz)
    odor_intensity = math.exp(-decay_rate * distance)
    # Exp decay
    if noise_enabled:
        odor_intensity += random.uniform(-0.01, 0.01)
        if odor_intensity < 0: odor_intensity = 0.0

    # MechFly to fly agent
    prev_heading = mechfly.heading
    fly_speed = mechfly.update(odor_intensity)
    new_heading = mechfly.heading
    yaw_change_deg = math.degrees(new_heading - prev_heading)
    
    prev_fly_position = fly_position.copy()

    action = env.action_space.no_op()
    action['camera'] = [0, yaw_change_deg]
    if fly_speed > 0:
        action['forward'] = 1
        action['back'] = 0
    else:
        action['forward'] = 0
        action['back'] = 1
    action['jump'] = 1
    

    obs, reward, done, info = env.step(action)
    env.render()
    if 'position' in info:
        fly_position = np.array(info['position'], dtype=float)
    else:
        fly_position[0] += fly_speed * math.cos(new_heading)
        fly_position[2] += fly_speed * math.sin(new_heading)

    last_move_distance = np.linalg.norm(fly_position - prev_fly_position)

    # Synchronize
    elapsed = time.time() - loop_start
    if elapsed < target_step_time:
        time.sleep(target_step_time - elapsed)

    # Log
    log_file.write(f"{time.time()},{fly_position[0]},{fly_position[1]},{fly_position[2]},"
                   f"{odor_position[0]},{odor_position[1]},{odor_position[2]},{odor_intensity}\n")
    fly_trajectory.append(fly_position.copy())
    odor_trajectory.append(odor_position.copy())
    intensity_history.append(odor_intensity)

    if done:
        break

log_file.close()
env.close()

# Visualization
import matplotlib.pyplot as plt
import shutil
from pathlib import Path

fly_traj = np.array(fly_trajectory)
odor_traj = np.array(odor_trajectory)
output_dir = Path("./outputs")
output_dir.mkdir(parents=True, exist_ok=True)

plt.figure()
plt.plot(odor_traj[:, 0], odor_traj[:, 2], label='Odor Source')
plt.plot(fly_traj[:, 0], fly_traj[:, 2], label='Fly Agent')
plt.xlabel('X coordinate')
plt.ylabel('Z coordinate')
plt.title('Agent and Odor')
plt.legend()
trajectory_file = output_dir / "agent.png"
plt.savefig(trajectory_file)
plt.close()
plt.figure()
plt.plot(intensity_history, 'r-')
plt.xlabel('Sim Step')
plt.ylabel('Odor Intensity')
plt.title('OI vs Time')
intensity_file = output_dir / "odor.png"
plt.savefig(intensity_file)
plt.close()
