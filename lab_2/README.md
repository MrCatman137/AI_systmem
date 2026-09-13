# Laboratory Work 2: BFS and DFS on Graphs

This CustomTkinter application demonstrates blind breadth-first and depth-first search on a fixed 30-vertex graph. Select BFS or DFS in the algorithm control; both support animation, step-by-step execution, traversal orders, reverse search, result comparison, graph editing, and JSON persistence.

## Run

From the repository root:

```text
python lab_2/main.py
```

Install the only external dependency when needed:

```text
python -m pip install -r lab_2/requirements.txt
```

## Structure

- `graph.py`: vertex, edge, graph operations, tree invariants, JSON conversion.
- `bfs.py`: manual `deque`-based BFS, `BFSResult`, and stateful `BFSRunner`.
- `dfs.py`: manual stack-based DFS, `DFSResult`, and stateful `DFSRunner`.
- `data/default_graph.py`: explicit fixed coordinates and edges for the initial graph.
- `main.py`: template-based interface, canvas rendering, controls, experiments, and save/load.

The initial graph is deterministic and is never randomly generated. Select BFS or DFS, choose `ascending`, `descending`, or `custom` neighbor order, reverse Start and Target, use `Крок` to inspect the queue or stack process, and save completed searches from the Results page.

The laboratory page also has a random graph generator. Enter the required number of vertices and edges before generating. Vertices are placed on a spaced canvas grid, and edges are created only between nearby vertices; this prevents long connections from one side of the canvas to the other. Generated trees use exactly `V - 1` local edges and remain connected.