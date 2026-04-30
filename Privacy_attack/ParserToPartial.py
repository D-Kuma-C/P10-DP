from __future__ import annotations

from typing import List

from geometry import Trajectory


def parse_dat_trajectories(path: str) -> List[Trajectory]:
    """
    Parses AdaTrace-like .dat trajectory files:

        #0:
        >0:x1,y1;x2,y2;
        #1:
        >0:x1,y1;x2,y2;

    Returns:
        [
            [(x1, y1), (x2, y2), ...],
            ...
        ]
    """
    trajectories: List[Trajectory] = []
    current_points: Trajectory = []

    with open(path, "r", encoding="utf-8") as file:
        for raw_line in file:
            line = raw_line.strip()

            if not line:
                continue

            if line.startswith("#"):
                if current_points:
                    trajectories.append(current_points)
                    current_points = []
                continue

            if line.startswith(">"):
                if ":" in line:
                    line = line.split(":", 1)[1]

                for piece in line.split(";"):
                    piece = piece.strip()
                    if not piece:
                        continue

                    x_str, y_str = piece.split(",")
                    current_points.append((float(x_str), float(y_str)))

        if current_points:
            trajectories.append(current_points)

    return trajectories
