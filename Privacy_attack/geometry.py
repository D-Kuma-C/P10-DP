from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import List, Tuple


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

    def __str__(self) -> str:
        return self.name


class Grid:
    def __init__(self, cell_count: int, min_x: float, max_x: float, min_y: float, max_y: float):
        self.cell_count = cell_count
        self.min_x = min_x
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = max_y

        x_increment = (max_x - min_x) / cell_count
        y_increment = (max_y - min_y) / cell_count

        self.top_level_cells: List[List[Cell]] = []

        for i in range(cell_count):
            row: List[Cell] = []
            for j in range(cell_count):
                row.append(
                    Cell(
                        min_x=min_x + x_increment * i,
                        min_y=min_y + y_increment * j,
                        max_x=min_x + x_increment * (i + 1),
                        max_y=min_y + y_increment * (j + 1),
                        name=f"{i},{j}",
                    )
                )
            self.top_level_cells.append(row)

        self.cells = self.get_cells()

    def get_n(self) -> int:
        return self.cell_count

    def get_cells(self) -> List[Cell]:
        cells: List[Cell] = []
        for i in range(self.cell_count):
            for j in range(self.cell_count):
                cells.append(self.top_level_cells[i][j])
        return cells

    def get_cell_matrix(self) -> List[List[Cell]]:
        return self.top_level_cells

    def get_x_of_cell(self, cell: Cell) -> int:
        x, _ = self._cell_coords(cell)
        return x

    def get_y_of_cell(self, cell: Cell) -> int:
        _, y = self._cell_coords(cell)
        return y

    def _cell_coords(self, cell: Cell) -> Tuple[int, int]:
        for i in range(self.cell_count):
            for j in range(self.cell_count):
                if self.top_level_cells[i][j] == cell:
                    return i, j
        raise ValueError(f"Cell {cell.name} not found in grid")

    def are_adjacent(self, c1: Cell, c2: Cell) -> bool:
        c1x, c1y = self._cell_coords(c1)
        c2x, c2y = self._cell_coords(c2)

        if c1 == c2:
            return False

        return abs(c1x - c2x) <= 1 and abs(c1y - c2y) <= 1

    def give_interpolated_route(self, start: Cell, end: Cell) -> List[Cell]:
        """
        Equivalent to AdaTrace Grid.giveInterpolatedRoute.

        Adds the start cell but not the end cell.
        """
        start_x, start_y = self._cell_coords(start)
        end_x, end_y = self._cell_coords(end)

        route: List[Cell] = []
        curr_x = start_x
        curr_y = start_y

        while True:
            route.append(self.top_level_cells[curr_x][curr_y])

            if end_x > curr_x:
                curr_x += 1
            elif end_x < curr_x:
                curr_x -= 1

            if end_y > curr_y:
                curr_y += 1
            elif end_y < curr_y:
                curr_y -= 1

            if curr_x == end_x and curr_y == end_y:
                break

        return route


def euclidean_dist(p1: Point, p2: Point) -> float:
    return sqrt((p1[1] - p2[1]) ** 2 + (p1[0] - p2[0]) ** 2)
