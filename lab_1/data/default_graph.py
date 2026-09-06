from __future__ import annotations

from ..graph import Graph, Vertex


VERTICES = [
    Vertex(1, 70, 70), Vertex(2, 180, 45), Vertex(3, 290, 70), Vertex(4, 400, 45), Vertex(5, 510, 70),
    Vertex(6, 620, 45), Vertex(7, 730, 70), Vertex(8, 840, 45), Vertex(9, 950, 70), Vertex(10, 1060, 45),
    Vertex(11, 120, 160), Vertex(12, 240, 140), Vertex(13, 360, 165), Vertex(14, 480, 140), Vertex(15, 600, 165),
    Vertex(16, 720, 140), Vertex(17, 840, 165), Vertex(18, 960, 140), Vertex(19, 1080, 165), Vertex(20, 1180, 140),
    Vertex(21, 70, 275), Vertex(22, 210, 250), Vertex(23, 350, 285), Vertex(24, 490, 250), Vertex(25, 630, 285),
    Vertex(26, 770, 250), Vertex(27, 910, 285), Vertex(28, 1050, 250), Vertex(29, 1160, 285), Vertex(30, 640, 410),
]

EDGES = [
    (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 9), (9, 10),
    (1, 11), (2, 12), (3, 13), (4, 14), (5, 15), (6, 16), (7, 17), (8, 18), (9, 19), (10, 20),
    (11, 12), (12, 13), (13, 14), (14, 15), (15, 16), (16, 17), (17, 18), (18, 19), (19, 20),
    (11, 21), (12, 22), (13, 23), (14, 24), (15, 25), (16, 26), (17, 27), (18, 28), (19, 29),
    (21, 22), (22, 23), (23, 24), (24, 25), (25, 26), (26, 27), (27, 28), (28, 29),
    (15, 30), (25, 30), (20, 29),
]


def create_default_graph() -> Graph:
    graph = Graph("undirected")
    for vertex in VERTICES:
        graph.add_vertex(vertex)
    for source, target in EDGES:
        graph.add_edge(source, target)
    return graph