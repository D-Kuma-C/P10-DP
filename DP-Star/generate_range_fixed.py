

import os
import pickle
import numpy as np

USE_DATA = "Geolife Trajectories 1.3"

base = f"data/{USE_DATA}/Trajectories"

lat = []
lon = []

for file in os.listdir(base):
    with open(os.path.join(base, file)) as f:
        for line in f:
            x,y = map(float, line.strip().split(","))
            lat.append(x)
            lon.append(y)

gps_range = [(min(lat), max(lat)), (min(lon), max(lon))]

with open(f"data/{USE_DATA}/GPS_trajs_range.pkl", "wb") as f:
    pickle.dump(gps_range, f)

print("GPS range:", gps_range)