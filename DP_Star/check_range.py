

import pickle

with open("DP_Star/save/GPS_trajs_range.pkl", "rb") as f:
    print("GPS range:", pickle.load(f))

with open("DP_Star/save/MDL_trajs_range.pkl", "rb") as f:
    print("MDL range:", pickle.load(f))