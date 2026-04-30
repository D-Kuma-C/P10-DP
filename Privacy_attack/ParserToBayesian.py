from typing import List, Tuple, Dict, Hashable
import math


PointTrajectory = List[Tuple[float, float]]
CellTrajectory = List[int]


def parse_dat_trajectories(path: str) -> List[PointTrajectory]:
    """
    Parses files like:

    #0:
    >0:x1,y1;x2,y2;x3,y3;
    #1:
    >0:x1,y1;x2,y2;

    Returns:
        [
            [(x1, y1), (x2, y2), ...],
            ...
        ]
    """
    trajectories = []

    with open(path, "r", encoding="utf-8") as f:
        current_points = []

        for raw_line in f:
            line = raw_line.strip()

            if not line:
                continue

            if line.startswith("#"):
                if current_points:
                    trajectories.append(current_points)
                    current_points = []
                continue

            if line.startswith(">"):
                # Remove prefix like >0:
                if ":" in line:
                    line = line.split(":", 1)[1]

                pieces = line.split(";")

                for piece in pieces:
                    piece = piece.strip()
                    if not piece:
                        continue

                    x_str, y_str = piece.split(",")
                    x = float(x_str)
                    y = float(y_str)
                    current_points.append((x, y))

        if current_points:
            trajectories.append(current_points)

    return trajectories



def build_grid_from_data(point_datasets: List[List[PointTrajectory]], x_bins: int, y_bins: int,):
    """
    Builds a rectangular grid covering all points in all datasets.

    Returns:
        grid_info dictionary
        grid_cells list
    """
    all_x = []
    all_y = []

    for dataset in point_datasets:
        for traj in dataset:
            for x, y in traj:
                all_x.append(x)
                all_y.append(y)

    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)

    cell_width = (max_x - min_x) / x_bins
    cell_height = (max_y - min_y) / y_bins

    grid_info = {
        "min_x": min_x,
        "max_x": max_x,
        "min_y": min_y,
        "max_y": max_y,
        "x_bins": x_bins,
        "y_bins": y_bins,
        "cell_width": cell_width,
        "cell_height": cell_height,
    }

    grid_cells = list(range(x_bins * y_bins))

    return grid_info, grid_cells


def point_to_cell_id(x: float, y: float, grid_info: Dict,) -> int:
    """
    Converts one coordinate point into a grid cell ID.

    Cell ID is row-major:
        cell_id = y_index * x_bins + x_index
    """
    min_x = grid_info["min_x"]
    min_y = grid_info["min_y"]
    x_bins = grid_info["x_bins"]
    y_bins = grid_info["y_bins"]
    cell_width = grid_info["cell_width"]
    cell_height = grid_info["cell_height"]

    x_idx = int((x - min_x) / cell_width)
    y_idx = int((y - min_y) / cell_height)

    # Handle points exactly on max boundary.
    x_idx = min(max(x_idx, 0), x_bins - 1)
    y_idx = min(max(y_idx, 0), y_bins - 1)

    return y_idx * x_bins + x_idx


def convert_points_to_cells(point_trajs: List[PointTrajectory], grid_info: Dict, remove_consecutive_duplicates: bool = True,) -> List[CellTrajectory]:
    """
    Converts coordinate trajectories into grid-cell trajectories.

    If remove_consecutive_duplicates=True:
        [5, 5, 5, 8, 8, 9] becomes [5, 8, 9]

    This is often useful because repeated GPS samples inside the same cell
    can otherwise dominate Markov transition counts.
    """
    cell_trajs = []

    for traj in point_trajs:
        cells = [
            point_to_cell_id(x, y, grid_info)
            for x, y in traj
        ]

        if remove_consecutive_duplicates:
            compacted = []
            for cell in cells:
                if not compacted or compacted[-1] != cell:
                    compacted.append(cell)
            cells = compacted

        if len(cells) > 0:
            cell_trajs.append(cells)

    return cell_trajs