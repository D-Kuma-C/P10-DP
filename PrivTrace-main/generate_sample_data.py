import numpy as np

num_trajectories = 500
points_per_trajectory = 300

with open("datasets/sample_data_large.dat", "w") as f:
    for i in range(num_trajectories):
        f.write(f"#{i}:\n")
        f.write(">0:")
        traj = np.cumsum(np.random.randn(points_per_trajectory, 2) * 0.1, axis=0) + 5.0
        f.write(";".join([f"{x:.3f},{y:.3f}" for x, y in traj]))
        f.write(";\n")