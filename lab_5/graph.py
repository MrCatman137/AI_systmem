from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite


@dataclass(frozen=True)
class Vertex:
    id: int
    name: str
    x: float
    y: float


@dataclass(frozen=True)
class Edge:
    source: int
    target: int
    weight: float
    directed: bool = False


class GraphError(ValueError):
    """Raised when an operation would make the graph invalid."""


class Graph:
    def __init__(self) -> None:
        self.vertices: dict[int, Vertex] = {}
        self.edges: list[Edge] = []

    @property
    def edge_count(self) -> int:
        return len(self.edges)

    def add_vertex(self, vertex: Vertex) -> None:
        if vertex.id in self.vertices:
            raise GraphError(f"Місто з ідентифікатором {vertex.id} вже існує.")
        if self.get_vertex_by_name(vertex.name) is not None:
            raise GraphError(f"Місто «{vertex.name}» вже існує.")
        if not vertex.name.strip():
            raise GraphError("Назва міста не може бути порожньою.")
        if not isfinite(vertex.x) or not isfinite(vertex.y):
            raise GraphError("Координати мають бути скінченними числами.")
        self.vertices[vertex.id] = vertex

    def remove_vertex(self, vertex_id: int) -> None:
        if vertex_id not in self.vertices:
            raise GraphError("Місто не знайдено.")
        del self.vertices[vertex_id]
        self.edges = [edge for edge in self.edges if edge.source != vertex_id and edge.target != vertex_id]

    def get_vertex(self, vertex_id: int) -> Vertex | None:
        return self.vertices.get(vertex_id)

    def get_vertex_by_name(self, name: str) -> Vertex | None:
        return next((vertex for vertex in self.vertices.values() if vertex.name == name), None)

    def _validate_edge(self, source: int, target: int, weight: float) -> None:
        if source == target:
            raise GraphError("Петлі не підтримуються.")
        if source not in self.vertices or target not in self.vertices:
            raise GraphError("Обидва міста мають існувати.")
        if not isfinite(weight) or weight < 0:
            raise GraphError("Відстань має бути невід'ємним скінченним числом.")

    def _edge_index(self, source: int, target: int) -> int | None:
        return next(
            (
                index for index, edge in enumerate(self.edges)
                if (edge.source, edge.target) == (source, target)
                or (not edge.directed and (edge.source, edge.target) == (target, source))
            ),
            None,
        )

    def has_edge(self, source: int, target: int) -> bool:
        return self._edge_index(source, target) is not None

    def add_edge(self, source: int, target: int, weight: float, directed: bool = False) -> None:
        weight = float(weight)
        self._validate_edge(source, target, weight)
        index = self._edge_index(source, target)
        edge = Edge(source, target, weight, directed)
        if index is None:
            self.edges.append(edge)
        else:
            self.edges[index] = edge

    def update_weight(self, source: int, target: int, weight: float) -> None:
        index = self._edge_index(source, target)
        if index is None:
            raise GraphError("Дорогу між цими містами не знайдено.")
        edge = self.edges[index]
        self.add_edge(edge.source, edge.target, weight, edge.directed)

    def remove_edge(self, source: int, target: int) -> None:
        index = self._edge_index(source, target)
        if index is None:
            raise GraphError("Дорогу між цими містами не знайдено.")
        self.edges.pop(index)

    def convert_edge(self, source: int, target: int, directed: bool) -> None:
        index = self._edge_index(source, target)
        if index is None:
            raise GraphError("Дорогу між цими містами не знайдено.")
        edge = self.edges[index]
        self.edges[index] = Edge(edge.source, edge.target, edge.weight, directed)

    def get_weighted_neighbors(self, vertex_id: int) -> list[tuple[int, float]]:
        if vertex_id not in self.vertices:
            return []
        neighbors: list[tuple[int, float]] = []
        for edge in self.edges:
            if edge.source == vertex_id:
                neighbors.append((edge.target, edge.weight))
            elif not edge.directed and edge.target == vertex_id:
                neighbors.append((edge.source, edge.weight))
        return neighbors

    def to_dict(self) -> dict[str, list[dict[str, int | float | str | bool]]]:
        return {
            "vertices": [asdict(vertex) for vertex in self.vertices.values()],
            "edges": [asdict(edge) for edge in self.edges],
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Graph:
        graph = cls()
        vertices = data.get("vertices", [])
        edges = data.get("edges", [])
        if not isinstance(vertices, list) or not isinstance(edges, list):
            raise GraphError("Список міст або доріг у файлі має хибний формат.")
        for item in vertices:
            if not isinstance(item, dict):
                raise GraphError("Опис міста у файлі має хибний формат.")
            graph.add_vertex(
                Vertex(
                    int(item["id"]),
                    str(item["name"]),
                    float(item["x"]),
                    float(item["y"]),
                )
            )
        for item in edges:
            if not isinstance(item, dict):
                raise GraphError("Опис дороги у файлі має хибний формат.")
            graph.add_edge(
                int(item["source"]),
                int(item["target"]),
                float(item["weight"]),
                bool(item.get("directed", False)),
            )
        return graph