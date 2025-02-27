import numpy as np
import matplotlib.pyplot as plt
from flygym.arena import OdorArena
from flygym import Fly, Camera
from flygym.examples.locomotion import HybridTurningController
from pathlib import Path
from tqdm import trange

# Define positions odor sources
odor_source = np.array([
    [24.0,  6.0, 1.5],
    [24.0,  -6.0, 1.5],
    [24.0,  0.0, 1.5],
    [8.0,  4.0, 1.5],
    [16.0,  4.0, 1.5],
    [16.0, -4.0, 1.5],
    [8.0, -4.0, 1.5],
    [8.0,  8.0, 1.5],
    [16.0,  8.0, 1.5],
    [16.0, -8.0, 1.5],
    [8.0, -8.0, 1.5]
])
# Each source's peak intensity in the odor space (attractive, aversive)
peak_odor_intensity = np.array([
    [1.0, 0.0],
    [1.0, 0.0],
    [0.0, 1.0],
    [0.0, 1.0],
    [0.0, 1.0],
    [0.0, 1.0],
    [0.0, 1.0],
    [0.0, 1.0],
    [0.0, 1.0],
    [0.0, 1.0],
    [0.0, 1.0]
])
# Colors for markers representing sources
marker_colors = [[255, 127, 14], [255, 127, 14], [31, 119, 180], [31, 119, 180], [31, 119, 180], [31, 119, 180], [31, 119, 180], [31, 119, 180], [31, 119, 180], [31, 119, 180], [31, 119, 180]]
marker_colors = np.array([[*np.array(color)/255, 1.0] for color in marker_colors])

# Odor arena
arena = OdorArena(
    odor_source=odor_source, 
    peak_odor_intensity=peak_odor_intensity,
    diffuse_func=lambda dist: dist**-2,
    marker_colors=marker_colors,
    marker_size=0.3
)


# List of body parts for contact sensors
contact_sensor_placements = [
    f"{leg}{segment}"
    for leg in ["LF", "LM", "LH", "RF", "RM", "RH"]
    for segment in ["Tibia", "Tarsus1", "Tarsus2", "Tarsus3", "Tarsus4", "Tarsus5"]
]

# Initialize the fly in the arena with olfaction
fly = Fly(
    spawn_pos=(0, 0, 0.2),                       
    contact_sensor_placements=contact_sensor_placements, 
    enable_olfaction=True,                      
    enable_adhesion=True,                       
    draw_adhesion=False                         
)

# Define fixed overhead camera
cam_params = {
    "mode": "fixed", 
    "pos": (odor_source[:, 0].max() / 2, 0, 35), 
    "euler": (0, 0, 0),                         
    "fovy": 45                                  
}
# Create the camera
cam = Camera(
    attachment_point=arena.root_element.worldbody, 
    camera_name="birdeye_cam",                     
    timestamp_text=False,                          
    camera_parameters=cam_params                   
)
# Set up the environment with a hybrid turning controller
sim = HybridTurningController(
    fly=fly,
    arena=arena,
    cameras=[cam],
    timestep=1e-4
)

outputs_dir = Path("./outputs/olfaction_simulation")
outputs_dir.mkdir(parents=True, exist_ok=True)

# Stabilization phase
for _ in range(500):  
    sim.step(np.zeros(2))   
    sim.render()            

# Capture the camera and save as image
last_frame = cam._frames[-1]               
fig, ax = plt.subplots(figsize=(5, 4))
ax.imshow(last_frame)                      
ax.axis("off")                             
fig.savefig(outputs_dir / "olfaction_env.png")  
plt.close(fig)                             


# Controller parameters
attractive_gain = -500.0   
aversive_gain  = 80.0      
delta_min = 0.2            
delta_max = 1.0            
decision_interval = 0.05   
run_time = 5.0            

# simulation steps per interval
physics_steps_per_decision = int(decision_interval / sim.timestep)  

obs_history = []          
obs, _ = sim.reset()     

# Main control
for _ in trange(int(run_time / decision_interval), desc="Odor-taxis simulation"):
    # Assuming 2 dimensions and 4 sensors (left/right antenna & palp), reshape to (2 sensor_types x 2 sides)
    attractive_raw = obs["odor_intensity"][0, :].reshape(2, 2)
    aversive_raw  = obs["odor_intensity"][1, :].reshape(2, 2)
    # Compute weighted average intensity
    attractive_intensities = np.average(attractive_raw, axis=0, weights=[9, 1])
    aversive_intensities  = np.average(aversive_raw,  axis=0, weights=[10, 0])
    # Calculate asymmetry
    attractive_bias = attractive_gain * (attractive_intensities[0] - attractive_intensities[1]) / attractive_intensities.mean()
    aversive_bias   = aversive_gain   * (aversive_intensities[0]  - aversive_intensities[1])  / aversive_intensities.mean()
    s = attractive_bias + aversive_bias
    # b = tanh(s^2) * sign(s)
    b = np.tanh(s**2) * np.sign(s)
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
        obs_history.append(obs)          

    # Check termination
    fly_xy = obs["fly"][0, :2]
    if np.linalg.norm(fly_xy - odor_source[0, :2]) < 2.0 or np.linalg.norm(fly_xy - odor_source[1, :2]) < 2.0:
        print("Fly has reached the attractive odor source!")
        break


fly_positions = np.array([obs_t["fly"][0, :2] for obs_t in obs_history])

# Plot
fig_traj, ax_traj = plt.subplots(figsize=(6, 5))
# Plot odor sources
ax_traj.scatter(odor_source[:2, 0], odor_source[:2, 1], marker="o", color="orange", s=50, label="Attractive source")
ax_traj.scatter(odor_source[2:, 0], odor_source[2:, 1], marker="o", color="blue",   s=50, label="Aversive sources")
# Plot the fly's path
ax_traj.plot(fly_positions[:, 0], fly_positions[:, 1], color="k", label="Fly trajectory")
ax_traj.set_aspect("equal")
ax_traj.set_xlim(-1, 25); ax_traj.set_ylim(-10, 10)
ax_traj.set_xlabel("x (mm)"); ax_traj.set_ylabel("y (mm)")
ax_traj.legend(loc="upper right")
fig_traj.savefig(outputs_dir / "odor_taxis_trajectory.png")
plt.close(fig_traj)

cam.save_video(outputs_dir / "odor_taxis.mp4")

print(f"Simulation complete. Outputs saved in {outputs_dir.resolve()}")
