from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

Coordinate = tuple[int, int]


class MazeError(ValueError):
    """Raised when the maze state is invalid."""


TRANSITION_OPERATORS: dict[str, tuple[Coordinate, ...]] = {
    "UP_DOWN_LEFT_RIGHT": ((-1, 0), (1, 0), (0, -1), (0, 1)),
    "DIAGONAL": ((-1, -1), (-1, 1), (1, -1), (1, 1)),
    "COMBINATION": (
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1),
    ),
}


@dataclass
class Maze:
    rows: int
    cols: int
    grid: list[list[int]] | None = None

    def __post_init__(self) -> None:
        if self.rows <= 0 or self.cols <= 0:
            raise MazeError("Maze dimensions must be positive.")
        if self.grid is None:
            self.grid = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        if len(self.grid) != self.rows:
            raise MazeError("The maze rows do not match the declared dimensions.")
        normalized: list[list[int]] = []
        for row_index, row in enumerate(self.grid):
            if len(row) != self.cols:
                raise MazeError(f"Row {row_index} does not match the declared number of columns.")
            normalized_row: list[int] = []
            for value in row:
                if value not in (-1, 0):
                    raise MazeError("Maze cells may only contain -1 or 0.")
                normalized_row.append(int(value))
            normalized.append(normalized_row)
        self.grid = normalized

    def copy(self) -> "Maze":
        return Maze(self.rows, self.cols, [row[:] for row in self.grid])

    def resize(self, rows: int, cols: int) -> "Maze":
        if rows <= 0 or cols <= 0:
            raise MazeError("Maze dimensions must be positive.")
        new_grid = [[0 for _ in range(cols)] for _ in range(rows)]
        for row in range(min(rows, self.rows)):
            for col in range(min(cols, self.cols)):
                new_grid[row][col] = self.grid[row][col]
        self.rows = rows
        self.cols = cols
        self.grid = new_grid
        return self

    def is_inside(self, cell: Coordinate) -> bool:
        row, col = cell
        return 0 <= row < self.rows and 0 <= col < self.cols

    def is_passable(self, cell: Coordinate) -> bool:
        if not self.is_inside(cell):
            return False
        row, col = cell
        return self.grid[row][col] == 0

    def set_cell(self, cell: Coordinate, value: int) -> None:
        if value not in (-1, 0):
            raise MazeError("Cell value must be -1 (wall) or 0 (passable).")
        if not self.is_inside(cell):
            raise MazeError("Cell coordinates are outside the maze bounds.")
        row, col = cell
        self.grid[row][col] = int(value)

    def count_passable_vertices(self) -> int:
        return sum(1 for row in self.grid for cell in row if cell == 0)

    def count_impassable_cells(self) -> int:
        return sum(1 for row in self.grid for cell in row if cell == -1)

    def get_neighbors(self, cell: Coordinate, operator: str = "UP_DOWN_LEFT_RIGHT") -> list[Coordinate]:
        if operator not in TRANSITION_OPERATORS:
            raise MazeError(f"Unknown transition operator: {operator}")
        row, col = cell
        neighbors: list[Coordinate] = []
        for delta_row, delta_col in TRANSITION_OPERATORS[operator]:
            next_cell = (row + delta_row, col + delta_col)
            if self.is_inside(next_cell) and self.is_passable(next_cell):
                neighbors.append(next_cell)
        return neighbors

    def find_first_passable(self) -> Coordinate | None:
        for row in range(self.rows):
            for col in range(self.cols):
                if self.grid[row][col] == 0:
                    return row, col
        return None

    def to_dict(self) -> dict:
        return {"rows": self.rows, "cols": self.cols, "grid": [row[:] for row in self.grid]}

    @classmethod
    def from_dict(cls, data: dict) -> "Maze":
        return cls(int(data["rows"]), int(data["cols"]), data.get("grid"))

    @staticmethod
    def format_cell(cell: Coordinate) -> str:
        return f"({cell[0]}, {cell[1]})"
