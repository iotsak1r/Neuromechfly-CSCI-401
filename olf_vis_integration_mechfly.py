import numpy as np
from flygym import Fly, Camera
from flygym.arena import FlatTerrain
from flygym.examples.vision import ObstacleOdorArena  # Arena with obstacles + odor
from flygym.examples.locomotion import HybridTurningController
from pathlib import Path
import matplotlib.pyplot as plt
from tqdm import trange

# Define odor source position and intensity
odor_source = np.array([[20.0, 0.0, 1.5]])  
peak_odor_intensity = np.array([[1.0]])    

diffuse_func = lambda dist: dist**-2

# Define visual obstacle
obstacle_positions = np.array([(10.0, 2.0), (10.0, 4.0), (10.0, -2.0), (10.0, .0)])
obstacle_colors = [(0.0, 0.0, 0.0, 1.0), (0.0, 0.0, 0.0, 1.0), (0.0, 0.0, 0.0, 1.0), (0.0, 0.0, 0.0, 1.0)]
obstacle_radius = 1.0 
obstacle_height = 4.0 

# Colors for markers representing sources
marker_colors = np.array([[1.0, 0.5, 0.055, 1.0]])

# Flat terrain
terrain = FlatTerrain()
arena = ObstacleOdorArena(
    terrain=terrain,
    obstacle_positions=obstacle_positions,
    obstacle_colors=obstacle_colors,
    obstacle_radius=obstacle_radius,
    obstacle_height=obstacle_height,
    odor_source=odor_source,
    peak_odor_intensity=peak_odor_intensity,
    diffuse_func=diffuse_func,
    marker_colors=marker_colors,
    marker_size=0.3
)


# List of body parts for contact sensors
contact_sensor_placements = [
    f"{leg}{segment}" 
    for leg in ["LF", "LM", "LH", "RF", "RM", "RH"]
    for segment in ["Tibia", "Tarsus1", "Tarsus2", "Tarsus3", "Tarsus4", "Tarsus5"]
]

# Initialize the fly in the arena with olfaction and vision
fly = Fly(
    spawn_pos=(0.0, 0.0, 0.2),
    spawn_orientation=(0.0, 0.0, 0.0),
    contact_sensor_placements=contact_sensor_placements,
    enable_vision=True,    
    enable_olfaction=True, 
    enable_adhesion=True,  
    draw_adhesion=False
)

# Define fixed overhead camera
cam_params = {
    "mode": "fixed",
    "pos": (10.0, 0.0, 30.0),    
    "euler": (0.0, 0.0, 0.0),    
    "fovy": 45
}
# Create the camera
camera = Camera(
    attachment_point=arena.root_element.worldbody,
    camera_name="birdseye_view",
    camera_parameters=cam_params,
    timestamp_text=False 
)

# Set up the environment with a hybrid turning controller
sim = HybridTurningController(
    fly=fly,
    arena=arena,
    cameras=[camera],
    timestep=1e-4
)

outputs_dir = Path("./outputs/olfaction_simulation")
outputs_dir.mkdir(parents=True, exist_ok=True)

# Stabilization phase
for _ in range(500):
    sim.step(np.zeros(2))  # no turning input (stay still)
    sim.render()           # render frames for visualization

# Capture the camera and save as image
init_frame = camera._frames[-1]
plt.figure(figsize=(5,4))
plt.imshow(init_frame)
plt.axis('off')
plt.title("Initial environment setup")
plt.savefig(outputs_dir / "initial_setup.png")
plt.close()

# Controller parameters
attractive_gain = -500.0 
avoid_distance = 5.0    
obstacle_gain = 200.0  
decision_interval = 0.05  
total_time = 5
delta_min = 0.2            
delta_max = 1.0   

num_decision_steps = int(total_time / decision_interval)
physics_steps_per_decision = int(decision_interval / sim.timestep)

obs_history = []
fly_positions = []

# Reset simulation
obs, _ = sim.reset()

for i in trange(num_decision_steps, desc="Simulating"):
    # Assuming 2 dimensions and 4 sensors (left/right antenna & palp), reshape to (2 sensor_types x 2 sides)
    attractive_raw = obs["odor_intensity"][0, :].reshape(2, 2)

    # Compute weighted average intensity
    attractive_intensities = np.average(attractive_raw, axis=0, weights=[9, 1])

    # Calculate asymmetry
    attractive_bias = attractive_gain * (attractive_intensities[0] - attractive_intensities[1]) / attractive_intensities.mean()
    s = attractive_bias
    if len(obs["odor_intensity"]) > 1:
        aversive_raw  = obs["odor_intensity"][1, :].reshape(2, 2)
        aversive_intensities  = np.average(aversive_raw,  axis=0, weights=[10, 0])
        aversive_bias   = aversive_gain   * (aversive_intensities[0]  - aversive_intensities[1])  / aversive_intensities.mean()
        s = attractive_bias + aversive_bias

    # Process Visual
    vision_data = obs["vision"]
    left_eye_img = vision_data[0]   # Left retina image
    right_eye_img = vision_data[1]  # Right retina image
    # Convert to average brightness
    if left_eye_img.ndim == 3 and left_eye_img.shape[2] == 3:
        left_brightness = left_eye_img.mean()
        right_brightness = right_eye_img.mean()
    else:
        left_brightness = left_eye_img.mean()
        right_brightness = right_eye_img.mean()
    # Compute difference
    vision_diff = (-left_brightness + right_brightness) / ((left_brightness + right_brightness) / 2 + 1e-6)
    vision_bias = obstacle_gain * vision_diff
    combined_bias = s + vision_bias
    # b = tanh(s^2) * sign(s)
    combined_bias_norm = np.tanh(combined_bias**2) * np.sign(combined_bias)
    b = combined_bias_norm

    # Descending signals for left and right
    delta_left = delta_max
    delta_right = delta_max
    if b > 0:   # odor stronger on left side -> turn left
        delta_right = delta_max - abs(b) * (delta_max - delta_min)
    else:       # odor stronger on right side -> turn right
        delta_left  = delta_max - abs(b) * (delta_max - delta_min)
    control_signal = np.array([delta_left, delta_right])

    # Apply the control
    for _ in range(physics_steps_per_decision):
        obs, *_ = sim.step(control_signal)
        sim.render()              
        fly_positions.append(obs["fly"][0, :2]) 
        obs_history.append(obs)
    # Check terminate
    if np.linalg.norm(obs["fly"][0, :2] - odor_source[0, :2]) < 2.0:
        break


fly_positions = np.array(fly_positions)

# Plot
fig, ax = plt.subplots(figsize=(5,4), tight_layout=True)
ax.scatter(odor_source[0,0], odor_source[0,1], s=60, c="orange", marker="o", label="Odor source")
ax.scatter(obstacle_positions[0,0], obstacle_positions[0,1], s=60, c="gray", marker="s", label="Obstacle")
ax.plot(fly_positions[:,0], fly_positions[:,1], 'k-', label="Fly trajectory")
ax.set_xlabel("x (mm)")
ax.set_ylabel("y (mm)")
ax.set_aspect('equal')
ax.legend(loc="upper right")
plt.savefig(outputs_dir / "fly_trajectory.png")
plt.close()

camera.save_video(outputs_dir / "multimodal_navigation.mp4")
print("Simulation complete. Trajectory plot saved as fly_trajectory.png and video saved as multimodal_navigation.mp4.")
