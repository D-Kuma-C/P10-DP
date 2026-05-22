from trajectory import Point, Trajectory


def load_dat_trajectories(file_path: str, dataset: str):
    trajectories = []
    current_traj_id = None

    with open(file_path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue

            if line.startswith("#"):
                current_traj_id = int(line.replace("#", "").replace(":", ""))
                continue

            if line.startswith(">"):
                if current_traj_id is None:
                    continue

                point_text = line.split(":", 1)[1]
                raw_points = point_text.split(";")

                points = []
                for raw_point in raw_points:
                    raw_point = raw_point.strip()
                    if not raw_point:
                        continue

                    parts = [p.strip() for p in raw_point.split(",")]

                    if len(parts) < 2:
                        continue

                    lon = float(parts[0])
                    lat = float(parts[1])
                    timestamp = parts[2] if len(parts) >= 3 else None

                    points.append(Point(lon=lon, lat=lat, timestamp=timestamp))

                trajectories.append(
                    Trajectory(
                        traj_id=current_traj_id,
                        dataset=dataset,
                        points=points,
                    )
                )

    return trajectories