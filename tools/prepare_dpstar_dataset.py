from pathlib import Path
import argparse
import pickle
import shutil
import math
import numpy as np


ROOT_DIR = Path(__file__).resolve().parents[1]

DP_STAR_DATASET_DIR = (
    ROOT_DIR
    / "DP_Star"
    / "data"
    / "Geolife Trajectories 1.3"
)

TRAJECTORIES_DIR = DP_STAR_DATASET_DIR / "Trajectories"
MDL_DIR = DP_STAR_DATASET_DIR / "MDL"
MIDDLEWARE_DIR = DP_STAR_DATASET_DIR / "Middleware"
SD_DIR = DP_STAR_DATASET_DIR / "SD"

GPS_RANGE_FILE = DP_STAR_DATASET_DIR / "GPS_trajs_range.pkl"
MDL_RANGE_FILE = DP_STAR_DATASET_DIR / "MDL_trajs_range.pkl"
TRAJ_NAME_LIST_FILE = DP_STAR_DATASET_DIR / "trajs_file_name_list.pkl"


# -----------------------------
# MDL helper functions from DP-Star logic
# -----------------------------

def to_vec_sub(a, b):
    return np.array(a) - np.array(b)


def to_vec_dot(a, b):
    return float(np.dot(a, b))


def to_vec_add(a, b):
    return np.array(a) + np.array(b)


def to_vec_times(k, a):
    return k * np.array(a)


def vlen(a, b):
    a = np.array(a)
    b = np.array(b)
    return float(np.linalg.norm(a - b))


def lt(t_traj, start_ind, curr_ind):
    length = vlen(t_traj[start_ind], t_traj[curr_ind])
    return math.log2(length) if length else np.spacing(1)


def cal_perpendicular(si, ei, sj, ej):
    si_sj = to_vec_sub(sj, si)
    si_ei = to_vec_sub(ei, si)
    si_ej = to_vec_sub(ej, si)

    base = to_vec_dot(si_ei, si_ei)
    if base == 0:
        return np.spacing(1)

    u1 = to_vec_dot(si_sj, si_ei) / base
    u2 = to_vec_dot(si_ej, si_ei) / base

    ps = to_vec_add(si, to_vec_times(u1, si_ei))
    pe = to_vec_add(si, to_vec_times(u2, si_ei))

    lp1 = vlen(ps, sj)
    lp2 = vlen(pe, ej)

    if lp1 + lp2 == 0:
        return 0

    return (lp1 ** 2 + lp2 ** 2) / (lp1 + lp2)


def angular(si, ei, sj, ej):
    si_ei = to_vec_sub(ei, si)
    sj_ej = to_vec_sub(ej, sj)

    if si_ei[0] == sj_ej[0] and si_ei[1] == sj_ej[1]:
        return 0

    if to_vec_dot(si_ei, sj_ej) <= 0:
        return math.sqrt(to_vec_dot(sj_ej, sj_ej))

    denom = math.sqrt(to_vec_dot(si_ei, si_ei)) * math.sqrt(to_vec_dot(sj_ej, sj_ej))
    if denom == 0:
        return 0

    cos0 = to_vec_dot(si_ei, sj_ej) / denom
    sin_square = 1 - cos0 ** 2
    sin0 = math.sqrt(sin_square) if sin_square > 0 else 0

    return math.sqrt(to_vec_dot(sj_ej, sj_ej)) * sin0


def lt_tilde(t_traj, start_ind, curr_ind):
    score1 = 0
    score2 = 0

    for j in range(start_ind, curr_ind):
        if t_traj[start_ind] == t_traj[j] and t_traj[curr_ind] == t_traj[j + 1]:
            continue

        if vlen(t_traj[start_ind], t_traj[curr_ind]) > vlen(t_traj[j], t_traj[j + 1]):
            p_result = cal_perpendicular(t_traj[start_ind], t_traj[curr_ind], t_traj[j], t_traj[j + 1])
            a_result = angular(t_traj[start_ind], t_traj[curr_ind], t_traj[j], t_traj[j + 1])
        else:
            p_result = cal_perpendicular(t_traj[j], t_traj[j + 1], t_traj[start_ind], t_traj[curr_ind])
            a_result = angular(t_traj[j], t_traj[j + 1], t_traj[start_ind], t_traj[curr_ind])

        score1 += p_result
        score2 += a_result

    score1 = math.log2(score1) if score1 != 0 else 0
    score2 = math.log2(score2) if score2 != 0 else 0

    return score1 + score2


def t_mdl(t_traj):
    trajectory_length = len(t_traj)

    if trajectory_length == 0:
        return []

    representative_points = [t_traj[0]]

    start_index = 0
    length = 1

    while start_index + length < trajectory_length:
        curr_index = start_index + length

        if lt_tilde(t_traj, start_index, curr_index) > 0:
            representative_points.append(t_traj[curr_index - 1])
            start_index = curr_index - 1
            length = 1
        else:
            length += 1

    representative_points.append(t_traj[-1])

    return representative_points


# -----------------------------
# DAT parsing
# -----------------------------

def parse_clean_dat(dat_file: Path):
    """
    Reads cleaned .dat format:

        #0
        >0:lon,lat,timestamp;lon,lat,timestamp;

    Returns:
        list[list[tuple[lat, lon]]]
    """
    trajectories = []
    current_id = None

    with dat_file.open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()

            if not line:
                continue

            if line.startswith("#"):
                current_id = line.replace("#", "").replace(":", "").strip()
                continue

            if not line.startswith(">"):
                continue

            if current_id is None:
                continue

            point_text = line.split(":", 1)[1]
            raw_points = point_text.split(";")

            trajectory = []

            for raw_point in raw_points:
                raw_point = raw_point.strip()
                if not raw_point:
                    continue

                parts = [p.strip() for p in raw_point.split(",")]

                if len(parts) < 2:
                    continue

                lon = float(parts[0])
                lat = float(parts[1])

                if not (-180.0 <= lon <= 180.0 and -90.0 <= lat <= 90.0):
                    raise ValueError(
                        "Input does not look like GPS lon,lat.\n"
                        f"Found first coordinate={lon}, second coordinate={lat}.\n"
                        "Expected longitude in [-180, 180] and latitude in [-90, 90].\n"
                        "You are probably using projected x,y coordinates instead of GPS lon,lat."
                    )

                # DP-Star Trajectories files use lat,lon order.
                trajectory.append((lat, lon))

            if len(trajectory) >= 2:
                trajectories.append(trajectory)

    return trajectories


def compute_range(trajectories):
    """
    Returns DP-Star range format:
        [[lat_min, lat_max], [lon_min, lon_max]]
    """
    all_lats = []
    all_lons = []

    for traj in trajectories:
        for lat, lon in traj:
            all_lats.append(lat)
            all_lons.append(lon)

    if not all_lats or not all_lons:
        raise ValueError("No valid points found.")

    return [
        [min(all_lats), max(all_lats)],
        [min(all_lons), max(all_lons)],
    ]


def scale_to_mdl_points(trajectory, gps_range, scaling_rate):
    """
    Converts GPS lat,lon to DP-Star MDL coordinate system:

        mdl_lat = (lat - min_lat) * scaling_rate
        mdl_lon = (lon - min_lon) * scaling_rate
    """
    min_lat = gps_range[0][0]
    min_lon = gps_range[1][0]

    mdl_points = []

    for lat, lon in trajectory:
        mdl_lat = (lat - min_lat) * scaling_rate
        mdl_lon = (lon - min_lon) * scaling_rate
        mdl_points.append((mdl_lat, mdl_lon))

    return mdl_points


def overwrite_folder(folder: Path):
    if folder.exists():
        shutil.rmtree(folder)

    folder.mkdir(parents=True, exist_ok=True)


def prepare_dpstar_dataset(dat_file: Path, max_trajectories=None, scaling_rate=500):
    if not dat_file.exists():
        raise FileNotFoundError(f"Input file not found: {dat_file}")

    print(f"Reading cleaned .dat file: {dat_file}")
    trajectories = parse_clean_dat(dat_file)

    if max_trajectories is not None:
        trajectories = trajectories[:max_trajectories]

    if not trajectories:
        raise ValueError("No valid trajectories were parsed from the input file.")

    print(f"Parsed trajectories: {len(trajectories)}")

    DP_STAR_DATASET_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Overwriting: {TRAJECTORIES_DIR}")
    overwrite_folder(TRAJECTORIES_DIR)

    print(f"Overwriting: {MDL_DIR}")
    overwrite_folder(MDL_DIR)

    print(f"Deleting and recreating: {MIDDLEWARE_DIR}")
    overwrite_folder(MIDDLEWARE_DIR)

    print(f"Deleting and recreating: {SD_DIR}")
    overwrite_folder(SD_DIR)

    gps_range = compute_range(trajectories)

    trajectory_names = []
    mdl_trajectories = []

    for i, trajectory in enumerate(trajectories):
        name = f"traj_{i:06d}"
        trajectory_names.append(name)

        trajectory_file = TRAJECTORIES_DIR / f"{name}.txt"

        with trajectory_file.open("w", encoding="utf-8") as f:
            for lat, lon in trajectory:
                f.write(f"{lat},{lon}\n")

        mdl_points = scale_to_mdl_points(
            trajectory=trajectory,
            gps_range=gps_range,
            scaling_rate=scaling_rate,
        )

        mdl_simplified = t_mdl(mdl_points)
        mdl_trajectories.append(mdl_simplified)

        mdl_file = MDL_DIR / f"{name}.txt"

        with mdl_file.open("w", encoding="utf-8") as f:
            for point in mdl_simplified:
                f.write(f"{tuple(point)}\n")

        if (i + 1) % 1000 == 0:
            print(f"Processed {i + 1}/{len(trajectories)} trajectories")

    mdl_range = compute_range(mdl_trajectories)

    with GPS_RANGE_FILE.open("wb") as f:
        pickle.dump(gps_range, f)

    with MDL_RANGE_FILE.open("wb") as f:
        pickle.dump(mdl_range, f)

    with TRAJ_NAME_LIST_FILE.open("wb") as f:
        pickle.dump(trajectory_names, f)

    print()
    print("DP-Star dataset prepared.")
    print(f"Dataset folder: {DP_STAR_DATASET_DIR}")
    print(f"Trajectories: {TRAJECTORIES_DIR}")
    print(f"MDL: {MDL_DIR}")
    print(f"GPS range: {gps_range}")
    print(f"MDL range: {mdl_range}")
    print(f"Trajectory name list: {TRAJ_NAME_LIST_FILE}")
    print()
    print("Remember: DP-Star config.py should still use:")
    print("USE_DATA = 'Geolife Trajectories 1.3'")


def main():
    parser = argparse.ArgumentParser(
        description="Prepare cleaned .dat trajectories for DP-Star."
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Path to cleaned .dat file, for example root/input/cleandata/porto/porto.dat",
    )

    parser.add_argument(
        "--max-trajectories",
        type=int,
        default=None,
        help="Optional maximum number of trajectories to export.",
    )

    parser.add_argument(
        "--scaling-rate",
        type=float,
        default=500,
        help="DP-Star MDL scaling rate. Default: 500.",
    )

    args = parser.parse_args()

    prepare_dpstar_dataset(
        dat_file=Path(args.input),
        max_trajectories=args.max_trajectories,
        scaling_rate=args.scaling_rate,
    )


if __name__ == "__main__":
    main()