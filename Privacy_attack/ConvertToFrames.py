import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
import os
import warnings
from tqdm import tqdm

def convert_dat_to_dataframe(path):
    """
    Reads a .dat file containing continuous trajectories and converts it
    into a discrete 12-hour Pandas DataFrame format.
    """
    # 1. Suppress the Windows Loky/Joblib CPU core warning
    os.environ["LOKY_MAX_CPU_COUNT"] = "4"
    warnings.filterwarnings("ignore", category=UserWarning)

    trajectories = []
    current_traj = []

    # 2. Read and parse the whole file directly from the given path
    print(f"Reading data from '{path}'...")
    with open(path, 'r') as file:
        for line in file:
            line = line.strip()

            # A new '#' marks the start of a new user's trajectory
            if line.startswith('#'):
                if current_traj:
                    trajectories.append(current_traj)
                    current_traj = []

            # Extract coordinates
            elif line.startswith('>0:'):
                coords_str = line[3:].strip(';')
                pairs = coords_str.split(';')
                for pair in pairs:
                    if pair:  # Ignore empty strings from trailing semicolons
                        x, y = map(float, pair.split(','))
                        current_traj.append([x, y])

    # Catch the very last trajectory after the loop finishes
    if current_traj:
        trajectories.append(current_traj)

    # Safety check: if the file was empty, return an empty DataFrame
    if not trajectories:
        print("Warning: No trajectories found in the file.")
        return pd.DataFrame()

    print(f"Successfully loaded {len(trajectories)} user trajectories.")

    # 3. Discretize spatial coordinates into 4 Regions using K-Means
    print("Finding spatial hotspots (training K-Means)... this might take a moment for large files.")
    all_coords = np.vstack(trajectories)
    kmeans = KMeans(n_clusters=4, random_state=42, n_init='auto').fit(all_coords)

    discrete_trajectories = []
    for traj in tqdm(trajectories, desc="Assigning regions"):
        labels = kmeans.predict(traj) + 1  # +1 to make it 1, 2, 3, 4
        discrete_trajectories.append(labels)

    # 4. Time-Binning: Resample varying lengths to exactly 12 "Hour" bins
    final_data = []
    for seq in tqdm(discrete_trajectories, desc="Binning to 12 hours"):
        indices = np.linspace(0, len(seq) - 1, 12).astype(int)
        sampled_seq = [seq[i] for i in indices]
        final_data.append(sampled_seq)

    # 5. Build and format the final Pandas DataFrame
    print("Building final DataFrame...")
    df = pd.DataFrame(
        final_data,
        columns=[f"1_Hour{i}" for i in range(12)]
    ).astype(str)

    df['User'] = range(len(df))
    df = df.set_index('User')

    print("Conversion complete!")
    return df