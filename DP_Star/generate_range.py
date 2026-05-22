


import os
import pickle
import ast
import numpy as np

USE_DATA = "Geolife Trajectories 1.3"

base_path = f"data/{USE_DATA}"
mdl_path = os.path.join(base_path, "MDL")
gps_path = os.path.join(base_path, "Trajectories")


def compute_range_from_txt(folder, is_mdl=False):
    lat_vals = []
    lon_vals = []

    for file in os.listdir(folder):
        file_path = os.path.join(folder, file)

        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()

                if is_mdl:
                    # MDL format: "(x, y)"
                    point = ast.literal_eval(line)
                    lat, lon = point
                else:
                    # GPS format: "lat,lon"
                    lat, lon = map(float, line.split(","))

                lat_vals.append(lat)
                lon_vals.append(lon)

    return [
        (min(lat_vals), max(lat_vals)),
        (min(lon_vals), max(lon_vals))
    ]


print("Computing GPS range...")
gps_range = compute_range_from_txt(gps_path)

print("Computing MDL range...")
mdl_range = compute_range_from_txt(mdl_path, is_mdl=True)


# Save files
with open(os.path.join(base_path, "GPS_trajs_range.pkl"), "wb") as f:
    pickle.dump(gps_range, f)

with open(os.path.join(base_path, "MDL_trajs_range.pkl"), "wb") as f:
    pickle.dump(mdl_range, f)


print("Done!")
print("GPS Range:", gps_range)
print("MDL Range:", mdl_range)