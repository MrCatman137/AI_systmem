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
    search_type: str = "Однонаправлений"
    visited_start: list[Coordinate] = field(default_factory=list)
    visited_target: list[Coordinate] = field(default_factory=list)
    distance_start: dict[Coordinate, int] = field(default_factory=dict)
    distance_target: dict[Coordinate, int] = field(default_factory=dict)
    meeting_cell: Coordinate | None = None

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
    search_type: str = "Однонаправлений"
    queue_start: deque[Coordinate] = field(default_factory=deque, init=False)
    queue_target: deque[Coordinate] = field(default_factory=deque, init=False)
    visited_start: list[Coordinate] = field(default_factory=list, init=False)
    visited_target: list[Coordinate] = field(default_factory=list, init=False)
    parent_start: dict[Coordinate, Coordinate | None] = field(default_factory=dict, init=False)
    parent_target: dict[Coordinate, Coordinate | None] = field(default_factory=dict, init=False)
    dist_start: dict[Coordinate, int] = field(default_factory=dict, init=False)
    dist_target: dict[Coordinate, int] = field(default_factory=dict, init=False)
    meeting_cell: Coordinate | None = field(default=None, init=False)
    expanding_start: bool = field(default=True, init=False)
    best_path_length: int | None = field(default=None, init=False)

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
        if self.search_type not in {"Однонаправлений", "Двонаправлений"}:
            raise ValueError("Unsupported search type selected.")
        self.queue.append(self.start)
        self.visited.append(self.start)
        self.parent[self.start] = None
        self.distance[self.start] = 0
        if self.search_type == "Двонаправлений":
            self.queue_start.append(self.start)
            self.queue_target.append(self.target)
            self.visited_start.append(self.start)
            self.visited_target.append(self.target)
            self.parent_start[self.start] = None
            self.parent_target[self.target] = None
            self.dist_start[self.start] = 0
            self.dist_target[self.target] = 0

    def step(self) -> bool:
        if self.finished:
            return False
        self.iterations += 1
        if self.search_type == "Двонаправлений":
            return self._step_bidirectional()
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

    def _step_bidirectional(self) -> bool:
        from_start = self.expanding_start
        queue = self.queue_start if from_start else self.queue_target
        own_dist = self.dist_start if from_start else self.dist_target
        own_parent = self.parent_start if from_start else self.parent_target
        own_visited = self.visited_start if from_start else self.visited_target
        other_dist = self.dist_target if from_start else self.dist_start

        if not queue:
            if not self.queue_start and not self.queue_target:
                self.finished = True
                self.elapsed_time = perf_counter() - self.started_at
            self.expanding_start = not self.expanding_start
            return False

        self.current_cell = queue.popleft()
        self.expanded.append(self.current_cell)
        for neighbor in self.maze.get_neighbors(self.current_cell, self.operator):
            if neighbor in own_dist:
                continue
            own_parent[neighbor] = self.current_cell
            own_dist[neighbor] = own_dist[self.current_cell] + 1
            own_visited.append(neighbor)
            self.distance[neighbor] = own_dist[neighbor]
            queue.append(neighbor)
            if neighbor in other_dist:
                candidate_length = own_dist[neighbor] + other_dist[neighbor]
                if self.best_path_length is None or candidate_length < self.best_path_length:
                    self.best_path_length = candidate_length
                    self.meeting_cell = neighbor
                self.found = True
        self.expanding_start = not self.expanding_start

        if self.best_path_length is not None and self._bidirectional_search_complete():
            self.finished = True
        elif not self.queue_start and not self.queue_target:
            self.finished = True
        if self.finished:
            self.elapsed_time = perf_counter() - self.started_at
        return True

    def _bidirectional_search_complete(self) -> bool:
        if self.best_path_length is None:
            return False
        next_start = self.dist_start[self.queue_start[0]] if self.queue_start else float("inf")
        next_target = self.dist_target[self.queue_target[0]] if self.queue_target else float("inf")
        return next_start + next_target >= self.best_path_length

    def run(self) -> "WaveResult":
        while not self.finished:
            self.step()
        return self.result()

    def result(self) -> WaveResult:
        path: list[Coordinate] = []
        if self.found:
            if self.search_type == "Двонаправлений":
                current: Coordinate | None = self.meeting_cell
                start_path: list[Coordinate] = []
                while current is not None:
                    start_path.append(current)
                    current = self.parent_start.get(current)
                start_path.reverse()
                current = self.parent_target.get(self.meeting_cell)
                target_path: list[Coordinate] = []
                while current is not None:
                    target_path.append(current)
                    current = self.parent_target.get(current)
                path = start_path + target_path
            else:
                current = self.target
                while current is not None:
                    path.append(current)
                    current = self.parent.get(current)
                path.reverse()

        if self.search_type == "Двонаправлений":
            wave_cycles = max(
                max(self.dist_start.values(), default=0),
                max(self.dist_target.values(), default=0),
            )
            visited_vertices = self.visited_start + self.visited_target
        else:
            wave_cycles = max(self.distance.values(), default=0)
            visited_vertices = self.visited.copy()
        return WaveResult(
            found=self.found,
            path=path,
            visited_vertices=visited_vertices,
            expanded_vertices=self.expanded.copy(),
            parent=self.parent.copy(),
            distance=self.distance.copy(),
            iterations=self.iterations,
            wave_cycles=wave_cycles,
            elapsed_time=self.elapsed_time,
            search_type=self.search_type,
            visited_start=self.visited_start.copy(),
            visited_target=self.visited_target.copy(),
            distance_start=self.dist_start.copy(),
            distance_target=self.dist_target.copy(),
            meeting_cell=self.meeting_cell,
        )


def wave_search(
    maze: Maze,
    start: Coordinate,
    target: Coordinate,
    operator: str = "UP_DOWN_LEFT_RIGHT",
    search_type: str = "Однонаправлений",
) -> WaveResult:
    return WaveRunner(maze, start, target, operator, search_type).run()