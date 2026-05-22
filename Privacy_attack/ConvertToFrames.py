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
    time_period_hours=24,
    interval_minutes=15,
    n_clusters=4,
    random_state=42,
):
    """
    Reads a .dat file and converts it into a discrete Pandas DataFrame.

    input_coordinates:
        "xy"     means the file already contains x,y coordinates
        "latlon" means the file contains lat/lon coordinates

    coordinate_order:
        "lonlat" means each coordinate pair is lon,lat
        "latlon" means each coordinate pair is lat,lon

    time_period_hours:
        Total time period represented by each trajectory.
        Example: 24 means one full day.

    interval_minutes:
        Time interval between bins.
        Example: 15 means 15-minute bins.

    n_clusters:
        Number of spatial regions used by KMeans.

    Example:
        time_period_hours=24, interval_minutes=15
        gives 96 time bins.
    """
    os.environ["LOKY_MAX_CPU_COUNT"] = "4"
    warnings.filterwarnings("ignore", category=UserWarning)

    if time_period_hours <= 0:
        raise ValueError("time_period_hours must be positive")

    if interval_minutes <= 0:
        raise ValueError("interval_minutes must be positive")

    total_minutes = time_period_hours * 60

    if total_minutes % interval_minutes != 0:
        raise ValueError(
            "time_period_hours * 60 must be divisible by interval_minutes. "
            f"Got {total_minutes} minutes and interval {interval_minutes} minutes."
        )

    num_time_bins = int(total_minutes / interval_minutes)

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
                        parts = [p.strip() for p in pair.split(",")]

                        if len(parts) < 2:
                            continue

                        a = float(parts[0])
                        b = float(parts[1])

                        timestamp = parts[2] if len(parts) >= 3 else None
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
    print(
        f"Using {num_time_bins} time bins "
        f"({time_period_hours} hours, {interval_minutes}-minute intervals)."
    )

    print("Finding spatial hotspots with K-Means...")
    all_coords = np.vstack(trajectories)

    kmeans = KMeans(
        n_clusters=n_clusters,
        random_state=random_state,
        n_init="auto",
    ).fit(all_coords)

    discrete_trajectories = []

    for traj in tqdm(trajectories, desc="Assigning regions"):
        labels = kmeans.predict(np.array(traj)) + 1
        discrete_trajectories.append(labels)

    final_data = []

    for seq in tqdm(discrete_trajectories, desc=f"Binning to {num_time_bins} time bins"):
        indices = np.linspace(0, len(seq) - 1, num_time_bins).astype(int)
        sampled_seq = [seq[i] for i in indices]
        final_data.append(sampled_seq)

    print("Building final DataFrame...")

    df = pd.DataFrame(
        final_data,
        columns=[
            f"{interval_minutes}min_{i}"
            for i in range(num_time_bins)
        ],
    ).astype(str)

    df["User"] = range(len(df))
    df = df.set_index("User")

    print("Conversion complete!")

    if return_projection_info:
        return df, projection_info

    return df