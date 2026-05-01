from __future__ import annotations
from tqdm import tqdm

from typing import List

from geometry import Cell, Grid, Point, Trajectory


GridTrajectory = List[Cell]


def point_to_cell(point: Point, grid: Grid) -> Cell:
    for cell in grid.cells:
        if cell.in_cell(point):
            return cell
    x, y = point
    shifted_point = (x - 0.001, y - 0.001)
    for cell in grid.cells:
        if cell.in_cell(shifted_point):
            return cell
    return grid.get_cell_matrix()[0][0]


def convert_traj_to_grid_traj(traj: Trajectory, grid: Grid, interp_wanted: bool = True, remove_duplicates: bool = True) -> GridTrajectory:
    if len(traj) == 0:
        return []
    traj_cells: GridTrajectory = [point_to_cell(point, grid) for point in traj]
    if remove_duplicates:
        new_traj_cells: GridTrajectory = [traj_cells[0]]
        for i in range(1, len(traj_cells) - 1):
            if traj_cells[i] != new_traj_cells[-1]:
                new_traj_cells.append(traj_cells[i])
        try:
            if traj_cells[-1] != traj_cells[-2]:
                new_traj_cells.append(traj_cells[-1])
        except Exception:
            pass
        if len(new_traj_cells) == 1:
            new_traj_cells.append(traj_cells[-1])
        traj_cells = new_traj_cells
    if interp_wanted:
        final_cells: GridTrajectory = []
        for i in range(len(traj_cells) - 1):
            current = traj_cells[i]
            next_cell = traj_cells[i + 1]
            if current == next_cell or grid.are_adjacent(current, next_cell):
                final_cells.append(current)
            else:
                final_cells.extend(grid.give_interpolated_route(current, next_cell))
        final_cells.append(traj_cells[-1])
        traj_cells = final_cells
    return traj_cells


def convert_all_to_grid_trajs(trajs: List[Trajectory], grid: Grid, interp_wanted: bool = True, remove_duplicates: bool = True, desc: str = "Converting trajectories to grid") -> List[GridTrajectory]:
    iterator = tqdm(trajs, total=len(trajs), desc=desc)
    return [convert_traj_to_grid_traj(traj=traj, grid=grid, interp_wanted=interp_wanted, remove_duplicates=remove_duplicates) for traj in iterator]


def get_nth_densest_cell(
    orig_grid_trajs: List[GridTrajectory],
    grid: Grid,
    n: int,
) -> Cell:
    """
    Equivalent to Main.getNthDensestCell.

    Uses descending sort by density, matching AdaTrace sortByValue reverse order.
    """
    if n < 1:
        raise ValueError("n must be >= 1")

    cell_densities = {cell: 0 for cell in grid.cells}

    for traj_cells in orig_grid_trajs:
        for cell in traj_cells:
            cell_densities[cell] += 1

    sorted_cells = sorted(
        cell_densities.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    if n > len(sorted_cells):
        raise ValueError(f"n={n} exceeds number of cells={len(sorted_cells)}")

    return sorted_cells[n - 1][0]
