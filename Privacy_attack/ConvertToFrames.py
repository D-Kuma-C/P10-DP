import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
import os
import warnings
from tqdm import tqdm

from coordinate_conversion import convert_trajectories_latlon_to_xy_meters

def convert_dat_to_dataframe(
    path,
    input_coordinates="xy",
    coordinate_order="lonlat",
    origin_lon=None,
    origin_lat=None,
    return_projection_info=False,
):
    """
    Reads a .dat file and converts it into a discrete 12-hour Pandas DataFrame.

    input_coordinates:
        "xy"     means the file already contains x,y coordinates
        "latlon" means the file contains lat/lon coordinates

    coordinate_order:
        "lonlat" means each coordinate pair is lon,lat
        "latlon" means each coordinate pair is lat,lon
    """
    os.environ["LOKY_MAX_CPU_COUNT"] = "4"
    warnings.filterwarnings("ignore", category=UserWarning)

    trajectories = []
    current_traj = []

    print(f"Reading data from '{path}'...")

    with open(path, "r") as file:
        for line in file:
            line = line.strip()

            if line.startswith("#"):
                if current_traj:
                    trajectories.append(current_traj)
                    current_traj = []

            elif line.startswith(">0:") or line.startswith(">"):
                if ":" in line:
                    coords_str = line.split(":", 1)[1].strip(";")
                else:
                    coords_str = line.strip(";")

                pairs = coords_str.split(";")

                for pair in pairs:
                    if pair:
                        a, b = map(float, pair.split(","))
                        current_traj.append((a, b))

    if current_traj:
        trajectories.append(current_traj)

    if not trajectories:
        print("Warning: No trajectories found in the file.")
        empty = pd.DataFrame()
        if return_projection_info:
            return empty, None
        return empty

    projection_info = None

    if input_coordinates == "latlon":
        trajectories, origin = convert_trajectories_latlon_to_xy_meters(
            trajectories,
            coordinate_order=coordinate_order,
            origin_lon=origin_lon,
            origin_lat=origin_lat,
        )

        projection_info = {
            "type": "local_equirectangular",
            "origin_lon": origin[0],
            "origin_lat": origin[1],
            "coordinate_order": coordinate_order,
            "units": "meters",
        }

    elif input_coordinates != "xy":
        raise ValueError("input_coordinates must be 'xy' or 'latlon'")

    print(f"Successfully loaded {len(trajectories)} user trajectories.")

    print("Finding spatial hotspots with K-Means...")
    all_coords = np.vstack(trajectories)

    kmeans = KMeans(
        n_clusters=4,
        random_state=42,
        n_init="auto",
    ).fit(all_coords)

    discrete_trajectories = []

    for traj in tqdm(trajectories, desc="Assigning regions"):
        labels = kmeans.predict(np.array(traj)) + 1
        discrete_trajectories.append(labels)

    final_data = []

    for seq in tqdm(discrete_trajectories, desc="Binning to 12 hours"):
        indices = np.linspace(0, len(seq) - 1, 12).astype(int)
        sampled_seq = [seq[i] for i in indices]
        final_data.append(sampled_seq)

    print("Building final DataFrame...")

    df = pd.DataFrame(
        final_data,
        columns=[f"1_Hour{i}" for i in range(12)],
    ).astype(str)

    df["User"] = range(len(df))
    df = df.set_index("User")

    print("Conversion complete!")

    if return_projection_info:
        return df, projection_info

    return df