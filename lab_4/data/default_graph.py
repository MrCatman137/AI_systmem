from __future__ import annotations

from ..graph import Maze

DEFAULT_MAZE = [
    [-1, -1, 0, 0, -1],
    [-1, 0, 0, 0, -1],
    [0, 0, -1, 0, 0],
    [0, -1, 0, 0, 0],
]

DEFAULT_START = (2, 0)
DEFAULT_TARGET = (3, 4)


def create_default_maze() -> Maze:
    return Maze(4, 5, [row[:] for row in DEFAULT_MAZE])