from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from coordinate_conversion import convert_trajectories_latlon_to_xy_meters


Point = Tuple[float, float]
Trajectory = List[Point]

PointTrajectory = Trajectory
CellTrajectory = List[int]


def parse_dat_trajectories(
    path: str,
    input_coordinates: str = "xy",
    coordinate_order: str = "lonlat",
    origin_lon: Optional[float] = None,
    origin_lat: Optional[float] = None,
):
    """
    Parses AdaTrace-like .dat trajectory files.

    input_coordinates:
        "xy"     means the file already contains x,y coordinates
        "latlon" means the file contains latitude/longitude coordinates

    coordinate_order:
        "lonlat" means each file pair is lon,lat
        "latlon" means each file pair is lat,lon

    Returns:
        If input_coordinates == "xy":
            trajectories

        If input_coordinates == "latlon":
            trajectories_xy_meters, projection_info
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

                    parts = [p.strip() for p in piece.split(",")]

                    if len(parts) < 2:
                        continue

                    a = float(parts[0])
                    b = float(parts[1])

                    timestamp = parts[2] if len(parts) >= 3 else None
                    current_points.append((float(a), float(b)))

        if current_points:
            trajectories.append(current_points)

    if input_coordinates == "xy":
        return trajectories

    if input_coordinates == "latlon":
        converted, origin = convert_trajectories_latlon_to_xy_meters(
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

        return converted, projection_info

    raise ValueError("input_coordinates must be 'xy' or 'latlon'")


def build_grid_from_data(
    point_datasets: List[List[PointTrajectory]],
    x_bins: int,
    y_bins: int,
):
    """
    Builds a rectangular grid covering all points in all datasets.

    Returns:
        grid_info dictionary
        grid_cells list

    grid_cells are integer cell IDs:
        0, 1, ..., x_bins * y_bins - 1
    """
    all_x = []
    all_y = []

    for dataset in point_datasets:
        for traj in dataset:
            for x, y in traj:
                all_x.append(x)
                all_y.append(y)

    if not all_x or not all_y:
        raise ValueError("No points found. Cannot build grid.")

    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)

    if max_x == min_x:
        raise ValueError("All x coordinates are identical. Cannot build grid.")
    if max_y == min_y:
        raise ValueError("All y coordinates are identical. Cannot build grid.")

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


def point_to_cell_id(
    x: float,
    y: float,
    grid_info: Dict,
) -> int:
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


def convert_points_to_cells(
    point_trajs: List[PointTrajectory],
    grid_info: Dict,
    remove_consecutive_duplicates: bool = True,
) -> List[CellTrajectory]:
    """
    Converts coordinate trajectories into grid-cell trajectories.

    If remove_consecutive_duplicates=True:
        [5, 5, 5, 8, 8, 9] becomes [5, 8, 9]
    """
    cell_trajs: List[CellTrajectory] = []

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


def parse_dat_for_bayesian(
    original_path: str,
    synthetic_path: str,
    x_bins: int = 20,
    y_bins: int = 20,
    input_coordinates: str = "xy",
    coordinate_order: str = "lonlat",
    remove_consecutive_duplicates: bool = True,
):
    """
    Convenience function for Bayesian attack.

    Returns:
        orig_trajs
        syn_trajs
        grid_cells
        grid_info
        projection_info

    orig_trajs and syn_trajs are cell trajectories.
    """
    projection_info = None

    if input_coordinates == "xy":
        orig_points = parse_dat_trajectories(
            original_path,
            input_coordinates="xy",
        )

        syn_points = parse_dat_trajectories(
            synthetic_path,
            input_coordinates="xy",
        )

    elif input_coordinates == "latlon":
        orig_points, projection_info = parse_dat_trajectories(
            original_path,
            input_coordinates="latlon",
            coordinate_order=coordinate_order,
        )

        syn_points, _ = parse_dat_trajectories(
            synthetic_path,
            input_coordinates="latlon",
            coordinate_order=coordinate_order,
            origin_lon=projection_info["origin_lon"],
            origin_lat=projection_info["origin_lat"],
        )

    else:
        raise ValueError("input_coordinates must be 'xy' or 'latlon'")

    grid_info, grid_cells = build_grid_from_data(
        point_datasets=[orig_points, syn_points],
        x_bins=x_bins,
        y_bins=y_bins,
    )

    orig_trajs = convert_points_to_cells(
        point_trajs=orig_points,
        grid_info=grid_info,
        remove_consecutive_duplicates=remove_consecutive_duplicates,
    )

    syn_trajs = convert_points_to_cells(
        point_trajs=syn_points,
        grid_info=grid_info,
        remove_consecutive_duplicates=remove_consecutive_duplicates,
    )

    return orig_trajs, syn_trajs, grid_cells, grid_info, projection_info