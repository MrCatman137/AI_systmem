from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from time import perf_counter

from .graph import Coordinate, Maze


@dataclass
class WaveResult:
    found: bool
    path: list[Coordinate]
    visited_vertices: list[Coordinate]
    expanded_vertices: list[Coordinate]
    parent: dict[Coordinate, Coordinate | None]
    distance: dict[Coordinate, int]
    iterations: int
    wave_cycles: int
    elapsed_time: float

    @property
    def path_length(self) -> int:
        return len(self.path) - 1 if self.found else 0


@dataclass
class WaveRunner:
    maze: Maze
    start: Coordinate
    target: Coordinate
    operator: str = "UP_DOWN_LEFT_RIGHT"
    queue: deque[Coordinate] = field(default_factory=deque, init=False)
    visited: list[Coordinate] = field(default_factory=list, init=False)
    expanded: list[Coordinate] = field(default_factory=list, init=False)
    parent: dict[Coordinate, Coordinate | None] = field(default_factory=dict, init=False)
    distance: dict[Coordinate, int] = field(default_factory=dict, init=False)
    current_cell: Coordinate | None = field(default=None, init=False)
    found: bool = field(default=False, init=False)
    finished: bool = field(default=False, init=False)
    iterations: int = field(default=0, init=False)
    started_at: float = field(default_factory=perf_counter, init=False)
    elapsed_time: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        if not self.maze.is_inside(self.start):
            raise ValueError("Start cell is outside the maze bounds.")
        if not self.maze.is_inside(self.target):
            raise ValueError("Target cell is outside the maze bounds.")
        if not self.maze.is_passable(self.start):
            raise ValueError("Start cell must be passable.")
        if not self.maze.is_passable(self.target):
            raise ValueError("Target cell must be passable.")
        if self.start == self.target:
            raise ValueError("Start and target cells must be different.")
        if self.operator not in {"UP_DOWN_LEFT_RIGHT", "DIAGONAL", "COMBINATION"}:
            raise ValueError("Unsupported transition operator selected.")
        self.queue.append(self.start)
        self.visited.append(self.start)
        self.parent[self.start] = None
        self.distance[self.start] = 0

    def step(self) -> bool:
        if self.finished:
            return False
        self.iterations += 1
        if not self.queue:
            self.finished = True
            self.elapsed_time = perf_counter() - self.started_at
            return False

        self.current_cell = self.queue.popleft()
        self.expanded.append(self.current_cell)

        if self.current_cell == self.target:
            self.found = True
            self.finished = True
            self.elapsed_time = perf_counter() - self.started_at
            return True

        for neighbor in self.maze.get_neighbors(self.current_cell, self.operator):
            if neighbor in self.parent:
                continue
            self.parent[neighbor] = self.current_cell
            self.distance[neighbor] = self.distance[self.current_cell] + 1
            self.visited.append(neighbor)
            self.queue.append(neighbor)
            if neighbor == self.target:
                self.found = True
                self.finished = True
                self.elapsed_time = perf_counter() - self.started_at
                return True

        if not self.queue and not self.found:
            self.finished = True
        if self.finished:
            self.elapsed_time = perf_counter() - self.started_at
        return True

    def run(self) -> "WaveResult":
        while not self.finished:
            self.step()
        return self.result()

    def result(self) -> WaveResult:
        path: list[Coordinate] = []
        if self.found:
            current: Coordinate | None = self.target
            while current is not None:
                path.append(current)
                current = self.parent.get(current)
            path.reverse()

        wave_cycles = max(self.distance.values(), default=0)
        return WaveResult(
            found=self.found,
            path=path,
            visited_vertices=self.visited.copy(),
            expanded_vertices=self.expanded.copy(),
            parent=self.parent.copy(),
            distance=self.distance.copy(),
            iterations=self.iterations,
            wave_cycles=wave_cycles,
            elapsed_time=self.elapsed_time,
        )


def wave_search(maze: Maze, start: Coordinate, target: Coordinate, operator: str = "UP_DOWN_LEFT_RIGHT") -> WaveResult:
    return WaveRunner(maze, start, target, operator).run()