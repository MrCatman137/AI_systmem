from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from math import inf
from time import perf_counter

from .graph import Graph


@dataclass
class DijkstraResult:
    found: bool
    path: list[int]
    path_names: list[str]
    total_distance: float
    visited_vertices: list[int]
    expanded_vertices: list[int]
    distances: dict[int, float]
    iterations: int
    elapsed_time: float


@dataclass
class DijkstraRunner:
    graph: Graph
    start: int
    target: int
    priority_queue: list[tuple[float, int]] = field(default_factory=list, init=False)
    visited: list[int] = field(default_factory=list, init=False)
    expanded: list[int] = field(default_factory=list, init=False)
    distances: dict[int, float] = field(default_factory=dict, init=False)
    previous: dict[int, int] = field(default_factory=dict, init=False)
    settled: set[int] = field(default_factory=set, init=False)
    current_vertex: int | None = field(default=None, init=False)
    found: bool = field(default=False, init=False)
    finished: bool = field(default=False, init=False)
    iterations: int = field(default=0, init=False)
    started_at: float = field(default_factory=perf_counter, init=False)
    elapsed_time: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        if self.start not in self.graph.vertices or self.target not in self.graph.vertices:
            raise ValueError("Початкове та цільове міста мають існувати.")
        self.distances = {vertex_id: inf for vertex_id in self.graph.vertices}
        self.distances[self.start] = 0.0
        self.visited.append(self.start)
        heapq.heappush(self.priority_queue, (0.0, self.start))

    def step(self) -> bool:
        if self.finished:
            return False
        while self.priority_queue:
            cost, vertex_id = heapq.heappop(self.priority_queue)
            if vertex_id in self.settled or cost != self.distances[vertex_id]:
                continue
            self.iterations += 1
            self.current_vertex = vertex_id
            self.settled.add(vertex_id)
            self.expanded.append(vertex_id)
            if vertex_id == self.target:
                self.found = True
                self._finish()
                return False
            for neighbor, weight in self.graph.get_weighted_neighbors(vertex_id):
                candidate = cost + weight
                if candidate < self.distances[neighbor]:
                    if self.distances[neighbor] == inf:
                        self.visited.append(neighbor)
                    self.distances[neighbor] = candidate
                    self.previous[neighbor] = vertex_id
                    heapq.heappush(self.priority_queue, (candidate, neighbor))
            if not self.priority_queue:
                self._finish()
                return False
            return True
        self._finish()
        return False

    def _finish(self) -> None:
        self.finished = True
        self.elapsed_time = perf_counter() - self.started_at

    def run(self) -> DijkstraResult:
        while not self.finished:
            self.step()
        return self.result()

    def result(self) -> DijkstraResult:
        path: list[int] = []
        if self.found:
            current = self.target
            path.append(current)
            while current != self.start:
                current = self.previous[current]
                path.append(current)
            path.reverse()
        path_names = [self.graph.vertices[vertex_id].name for vertex_id in path]
        return DijkstraResult(
            found=self.found,
            path=path,
            path_names=path_names,
            total_distance=self.distances.get(self.target, inf) if self.found else inf,
            visited_vertices=self.visited.copy(),
            expanded_vertices=self.expanded.copy(),
            distances=self.distances.copy(),
            iterations=self.iterations,
            elapsed_time=self.elapsed_time,
        )