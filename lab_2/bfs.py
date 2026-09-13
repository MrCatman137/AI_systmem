from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from time import perf_counter
from typing import Iterable

from .graph import Graph


@dataclass
class BFSResult:
    found: bool
    path: list[int]
    visited_vertices: list[int]
    expanded_vertices: list[int]
    parent: dict[int, int | None]
    distance: dict[int, int]
    iterations: int
    elapsed_time: float


@dataclass
class BFSRunner:
    graph: Graph
    start: int
    target: int
    order: str = "ascending"
    custom_order: list[int] = field(default_factory=list)
    queue: deque[int] = field(default_factory=deque, init=False)
    visited: list[int] = field(default_factory=list, init=False)
    expanded: list[int] = field(default_factory=list, init=False)
    parent: dict[int, int | None] = field(default_factory=dict, init=False)
    distance: dict[int, int] = field(default_factory=dict, init=False)
    current_vertex: int | None = field(default=None, init=False)
    found: bool = field(default=False, init=False)
    finished: bool = field(default=False, init=False)
    iterations: int = field(default=0, init=False)
    started_at: float = field(default_factory=perf_counter, init=False)
    elapsed_time: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        if self.start not in self.graph.vertices or self.target not in self.graph.vertices:
            raise ValueError("Start and target vertices must exist.")
        self.queue.append(self.start)
        self.visited.append(self.start)
        self.parent[self.start] = None
        self.distance[self.start] = 0
        if self.start == self.target:
            self.found = True
            self.finished = True
            self.elapsed_time = perf_counter() - self.started_at

    def step(self) -> bool:
        if self.finished:
            return False
        self.iterations += 1
        if not self.queue:
            self.finished = True
            self.elapsed_time = perf_counter() - self.started_at
            return False
        self.current_vertex = self.queue.popleft()
        self.expanded.append(self.current_vertex)
        if self.current_vertex == self.target:
            self.found = True
            self.finished = True
        else:
            for neighbor in self.graph.ordered_neighbors(self.current_vertex, self.order, self.custom_order):
                if neighbor not in self.parent:
                    self.parent[neighbor] = self.current_vertex
                    self.distance[neighbor] = self.distance[self.current_vertex] + 1
                    self.visited.append(neighbor)
                    self.queue.append(neighbor)
        if not self.queue and not self.found:
            self.finished = True
        if self.finished:
            self.elapsed_time = perf_counter() - self.started_at
        return True

    def run(self) -> BFSResult:
        while not self.finished:
            self.step()
        return self.result()

    def result(self) -> BFSResult:
        path: list[int] = []
        if self.found:
            current: int | None = self.target
            while current is not None:
                path.append(current)
                current = self.parent.get(current)
            path.reverse()
        return BFSResult(
            self.found, path, self.visited.copy(), self.expanded.copy(),
            self.parent.copy(), self.distance.copy(), self.iterations, self.elapsed_time,
        )


def breadth_first_search(graph: Graph, start: int, target: int, order: str = "ascending", custom_order: Iterable[int] = ()) -> BFSResult:
    return BFSRunner(graph, start, target, order, list(custom_order)).run()