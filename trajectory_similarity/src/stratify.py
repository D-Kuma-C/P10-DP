import pandas as pd


TRIP_GROUPS = ["small", "medium", "large"]


def trip_length_group(length_m: float) -> str:
    length_km = length_m / 1000.0

    if length_km <= 0.75:
        return "small"
    if length_km <= 1.25:
        return "medium"
    if length_km >= 2.0:
        return "large"

    return "medium_large_gap"


def assign_trip_length_groups(trajectories, roadmap=None):
    rows = []

    for t in trajectories:
        length_m = t.length(roadmap=roadmap)
        rows.append({
            "dataset": t.dataset,
            "traj_id": t.traj_id,
            "trip_length_m": length_m,
            "trip_length_km": length_m / 1000.0,
            "length_group": trip_length_group(length_m),
        })

    return pd.DataFrame(rows)