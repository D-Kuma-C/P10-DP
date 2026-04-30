


import os
import pickle

USE_DATA = "Geolife Trajectories 1.3"

base_path = f"data/{USE_DATA}"
traj_path = os.path.join(base_path, "MDL")

file_list = sorted(os.listdir(traj_path))

with open(os.path.join(base_path, "trajs_file_name_list.pkl"), "wb") as f:
    pickle.dump(file_list, f)

print("Generated trajs_file_name_list.pkl")
print("Number of trajectories:", len(file_list))