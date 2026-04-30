from dataclasses import dataclass
from math import sqrt, inf
from typing import List, Tuple, Dict, Any, Optional


Point = Tuple[float, float]
Trajectory = List[Point]


@dataclass(frozen=True)
class Cell:
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    name: str

    def in_cell(self, point: Point) -> bool:
        x, y = point
        return (
            x >= self.min_x and x <= self.max_x
            and y >= self.min_y and y <= self.max_y
        )


class Grid:
    def __init__(self, cell_count: int, min_x: float, max_x: float, min_y: float, max_y: float):
        self.cell_count = cell_count
        self.min_x = min_x
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = max_y

        x_inc = (max_x - min_x) / cell_count
        y_inc = (max_y - min_y) / cell_count

        self.top_level_cells = []

        for i in range(cell_count):
            row = []
            for j in range(cell_count):
                cell = Cell(
                    min_x=min_x + x_inc * i,
                    min_y=min_y + y_inc * j,
                    max_x=min_x + x_inc * (i + 1),
                    max_y=min_y + y_inc * (j + 1),
                    name=f"{i},{j}",
                )
                row.append(cell)
            self.top_level_cells.append(row)

        self.cells = self.get_cells()
        self.pos_in_list_form = {
            cell: idx for idx, cell in enumerate(self.cells)
        }

    def get_cells(self) -> List[Cell]:
        cells = []
        for i in range(self.cell_count):
            for j in range(self.cell_count):
                cells.append(self.top_level_cells[i][j])
        return cells

    def get_cell_matrix(self):
        return self.top_level_cells

    def are_adjacent(self, c1: Cell, c2: Cell) -> bool:
        c1x, c1y = self._cell_coords(c1)
        c2x, c2y = self._cell_coords(c2)

        return abs(c1x - c2x) <= 1 and abs(c1y - c2y) <= 1 and c1 != c2

    def _cell_coords(self, cell: Cell) -> Tuple[int, int]:
        for i in range(self.cell_count):
            for j in range(self.cell_count):
                if self.top_level_cells[i][j] == cell:
                    return i, j
        raise ValueError(f"Cell {cell.name} not found in grid")

    def give_interpolated_route(self, start: Cell, end: Cell) -> List[Cell]:
        startx, starty = self._cell_coords(start)
        endx, endy = self._cell_coords(end)

        route = []
        currx = startx
        curry = starty

        while True:
            route.append(self.top_level_cells[currx][curry])

            if endx > currx:
                currx += 1
            elif endx < currx:
                currx -= 1

            if endy > curry:
                curry += 1
            elif endy < curry:
                curry -= 1

            if currx == endx and curry == endy:
                break

        return route

    def parse_dat_trajectories(path: str) -> List[Trajectory]:
        trajectories = []
        current_points = []

        with open(path, "r", encoding="utf-8") as f:
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
                    if ":" in line:
                        line = line.split(":", 1)[1]

                    pieces = line.split(";")

                    for piece in pieces:
                        piece = piece.strip()
                        if not piece:
                            continue

                        x_str, y_str = piece.split(",")
                        current_points.append((float(x_str), float(y_str)))

            if current_points:
                trajectories.append(current_points)

        return trajectories


def point_to_cell(point: Point, grid: Grid) -> Cell:
    for cell in grid.cells:
        if cell.in_cell(point):
            return cell

    # Java fallback: subtract 0.001 due to precision / boundary issues
    x, y = point
    shifted_point = (x - 0.001, y - 0.001)

    for cell in grid.cells:
        if cell.in_cell(shifted_point):
            return cell

    # Java fallback: bottom-left cell
    return grid.get_cell_matrix()[0][0]


def convert_traj_to_grid_traj(
    traj: Trajectory,
    grid: Grid,
    interp_wanted: bool = True,
    remove_duplicates: bool = True,
) -> List[Cell]:
    if len(traj) == 0:
        return []

    traj_cells = [point_to_cell(point, grid) for point in traj]

    if remove_duplicates:
        new_traj_cells = [traj_cells[0]]

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
        fin_traj_cells = []

        for i in range(len(traj_cells) - 1):
            current = traj_cells[i]
            next_cell = traj_cells[i + 1]

            if current == next_cell or grid.are_adjacent(current, next_cell):
                fin_traj_cells.append(current)
            else:
                fin_traj_cells.extend(
                    grid.give_interpolated_route(current, next_cell)
                )

        fin_traj_cells.append(traj_cells[-1])
        traj_cells = fin_traj_cells

    return traj_cells


def convert_all_to_grid_trajs(
    trajs: List[Trajectory],
    grid: Grid,
    interp_wanted: bool = True,
    remove_duplicates: bool = True,
) -> List[List[Cell]]:
    return [
        convert_traj_to_grid_traj(
            traj,
            grid,
            interp_wanted=interp_wanted,
            remove_duplicates=remove_duplicates,
        )
        for traj in trajs
    ]