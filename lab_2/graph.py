from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable


@dataclass(frozen=True)
class Vertex:
    id: int
    x: float
    y: float


@dataclass(frozen=True)
class Edge:
    source: int
    target: int
    directed: bool = False


class GraphError(ValueError):
    """Raised when an operation would make the graph invalid."""


class Graph:
    def __init__(self, graph_type: str = "undirected") -> None:
        self.graph_type = graph_type
        self.vertices: dict[int, Vertex] = {}
        self.edges: list[Edge] = []

    @property
    def edge_count(self) -> int:
        return len(self.edges)

    def copy(self) -> Graph:
        result = Graph(self.graph_type)
        result.vertices = self.vertices.copy()
        result.edges = self.edges.copy()
        return result

    def add_vertex(self, vertex: Vertex) -> None:
        if vertex.id in self.vertices:
            raise GraphError(f"Vertex {vertex.id} already exists.")
        self.vertices[vertex.id] = vertex

    def remove_vertex(self, vertex_id: int) -> None:
        if vertex_id not in self.vertices:
            raise GraphError(f"Vertex {vertex_id} does not exist.")
        self.vertices.pop(vertex_id)
        self.edges = [edge for edge in self.edges if edge.source != vertex_id and edge.target != vertex_id]

    def get_vertex(self, vertex_id: int) -> Vertex | None:
        return self.vertices.get(vertex_id)

    def _validate_endpoints(self, source: int, target: int) -> None:
        if source == target:
            raise GraphError("Loops are not supported.")
        if source not in self.vertices or target not in self.vertices:
            raise GraphError("Both edge endpoints must exist.")

    def has_edge(self, source: int, target: int, directed: bool | None = None) -> bool:
        return any(
            edge.source == source and edge.target == target
            and (directed is None or edge.directed == directed)
            for edge in self.edges
        ) or any(
            not edge.directed and edge.source == target and edge.target == source
            and (directed is None or directed is False)
            for edge in self.edges
        )

    def add_edge(self, source: int, target: int, directed: bool = False) -> None:
        self._validate_endpoints(source, target)
        if self.graph_type == "tree":
            directed = False
        if self.has_edge(source, target):
            raise GraphError("This edge already exists.")
        if self.graph_type == "tree" and len(self.edges) >= len(self.vertices) - 1:
            raise GraphError("A tree must contain exactly V - 1 edges.")
        edge = Edge(source, target, directed or self.graph_type == "directed")
        self.edges.append(edge)
        if self.graph_type == "tree" and not self.is_tree_structure():
            self.edges.pop()
            raise GraphError("This operation would create a cycle in the tree.")

    def remove_edge(self, source: int, target: int) -> None:
        for index, edge in enumerate(self.edges):
            if ((edge.source, edge.target) == (source, target)
                    or (not edge.directed and (edge.target, edge.source) == (source, target))):
                if self.graph_type == "tree":
                    raise GraphError("Removing an edge would disconnect the tree.")
                self.edges.pop(index)
                return
        raise GraphError("This edge does not exist.")

    def convert_edge(self, source: int, target: int, directed: bool) -> None:
        for index, edge in enumerate(self.edges):
            matches = (edge.source, edge.target) == (source, target)
            reverse_matches = not edge.directed and (edge.target, edge.source) == (source, target)
            if matches or reverse_matches:
                if self.graph_type == "tree" and directed:
                    raise GraphError("Tree edges must remain undirected.")
                self.edges[index] = Edge(source, target, directed)
                return
        raise GraphError("This edge does not exist.")

    def set_graph_type(self, graph_type: str) -> None:
        if graph_type not in {"undirected", "directed", "tree"}:
            raise GraphError("Unknown graph type.")
        previous = self.graph_type
        old_edges = self.edges.copy()
        self.graph_type = graph_type
        if graph_type == "tree":
            adjacency = {vertex_id: [] for vertex_id in self.vertices}
            for edge in self.edges:
                adjacency[edge.source].append(edge.target)
                if not edge.directed:
                    adjacency[edge.target].append(edge.source)
            tree_edges: list[Edge] = []
            seen: set[int] = set()
            first_vertex = next(iter(self.vertices), None)
            stack = [first_vertex] if first_vertex is not None else []
            if first_vertex is not None:
                seen.add(first_vertex)
            while stack:
                current = stack.pop()
                for neighbor in sorted(adjacency[current], reverse=True):
                    if neighbor not in seen:
                        seen.add(neighbor)
                        tree_edges.append(Edge(current, neighbor, False))
                        stack.append(neighbor)
            self.edges = tree_edges
            if not self.is_tree_structure():
                self.graph_type, self.edges = previous, old_edges
                raise GraphError("The graph must be connected before it can become a tree.")
        elif graph_type == "directed":
            self.edges = [Edge(edge.source, edge.target, True) for edge in self.edges]
        else:
            self.edges = [Edge(edge.source, edge.target, False) for edge in self.edges]

    def is_tree_structure(self) -> bool:
        if not self.vertices:
            return True
        if len(self.edges) != len(self.vertices) - 1:
            return False
        adjacency = {vertex_id: [] for vertex_id in self.vertices}
        for edge in self.edges:
            adjacency[edge.source].append(edge.target)
            adjacency[edge.target].append(edge.source)
        seen: set[int] = set()
        stack = [next(iter(self.vertices))]
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            stack.extend(adjacency[current])
        return len(seen) == len(self.vertices)

    def get_neighbors(self, vertex_id: int) -> list[int]:
        neighbors: list[int] = []
        for edge in self.edges:
            if edge.source == vertex_id:
                neighbors.append(edge.target)
            elif not edge.directed and edge.target == vertex_id:
                neighbors.append(edge.source)
        return neighbors

    def to_dict(self) -> dict:
        return {
            "graph_type": self.graph_type,
            "vertices": [asdict(vertex) for vertex in self.vertices.values()],
            "edges": [asdict(edge) for edge in self.edges],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Graph:
        graph = cls(data.get("graph_type", "undirected"))
        for item in data.get("vertices", []):
            graph.add_vertex(Vertex(int(item["id"]), float(item["x"]), float(item["y"])))
        for item in data.get("edges", []):
            graph.edges.append(Edge(int(item["source"]), int(item["target"]), bool(item.get("directed"))))
        if graph.graph_type == "tree" and not graph.is_tree_structure():
            raise GraphError("Loaded graph is not a valid tree.")
        return graph

    def ordered_neighbors(self, vertex_id: int, order: str = "ascending", custom: Iterable[int] = ()) -> list[int]:
        neighbors = self.get_neighbors(vertex_id)
        if order == "descending":
            return sorted(neighbors, reverse=True)
        if order == "custom":
            priority = {value: index for index, value in enumerate(custom)}
            return sorted(neighbors, key=lambda value: (priority.get(value, len(priority)), value))
        return sorted(neighbors)