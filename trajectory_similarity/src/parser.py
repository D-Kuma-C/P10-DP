import pandas as pd
from collections import defaultdict

from trajectory import Trajectory, Point

def load_segment_trajectories(file_path: str):
    df = pd.read_csv(file_path)

    grouped = defaultdict(list)

    for _, row in df.iterrows():
        traj_id = int(row["trajectory_id"])
        seg_id = int(row["segment_id"])
        grouped[traj_id].append(seg_id)

    trajectories = []
    for traj_id, segment_ids in grouped.items():
        trajectories.append(
            Trajectory(
                traj_id=traj_id,
                segment_ids=segment_ids,
            )
        )

    return trajectories

def load_dat_trajectories(file_path: str):
    trajectories = []

    with open(file_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    current_traj_id = None

    for line in lines:
        if line.startswith("#"):
            current_traj_id = int(line.replace("#", "").replace(":", ""))

        elif line.startswith(">"):
            if current_traj_id is None:
                continue

            point_part = line.split(":", 1)[1]
            raw_points = point_part.split(";")

            points = []
            for raw_point in raw_points:
                raw_point = raw_point.strip()
                if not raw_point:
                    continue

                try:
                    x_str, y_str = raw_point.split(",")
                    x = float(x_str)
                    y = float(y_str)
                except ValueError:
                    continue

                points.append(
                    Point(
                        osm_id=None,
                        y=y,
                        x=x,
                        timestamp=None,
                    )
                )

            trajectories.append(
                Trajectory(
                    traj_id=current_traj_id,
                    points=points,
                    segment_ids=list(range(len(points)))
                )
            )

    return trajectories