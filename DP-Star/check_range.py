

import pickle

with open("data/Geolife Trajectories 1.3/GPS_trajs_range.pkl", "rb") as f:
    print("GPS range:", pickle.load(f))

with open("data/Geolife Trajectories 1.3/MDL_trajs_range.pkl", "rb") as f:
    print("MDL range:", pickle.load(f))