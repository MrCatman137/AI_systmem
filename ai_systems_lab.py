import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from collections import deque
import random
import time
import json


class AISystemsApp(tk.Tk):
    """Universal GUI shell for AI / search / graph laboratory assignments."""

    BG = "#f4f6f8"
    PANEL = "#ffffff"
    TEXT = "#1f2937"
    MUTED = "#6b7280"
    ACCENT = "#2563eb"
    ACCENT_DARK = "#1d4ed8"
    BORDER = "#d9dee5"
    SUCCESS = "#16a34a"
    WARNING = "#d97706"

    def __init__(self):
        super().__init__()
        self.title("AI Systems Laboratory")
        self.geometry("1280x780")
        self.minsize(1050, 680)
        self.configure(bg=self.BG)

        self.nodes = {}
        self.edges = []
        self.adjacency = {}
        self.search_path = []
        self.visited_order = []
        self.running = False
        self.step_index = 0
        self.animation_job = None

        self._build_style()
        self._build_header()
        self._build_main()
        self._build_statusbar()

        self.generate_graph()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---------- UI ----------
    def _build_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("TFrame", background=self.BG)
        style.configure("Panel.TFrame", background=self.PANEL)

        style.configure(
            "TNotebook",
            background=self.BG,
            borderwidth=0,
        )
        style.configure(
            "TNotebook.Tab",
            padding=(16, 9),
            background="#e9edf2",
            foreground=self.TEXT,
            borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", self.PANEL)],
            foreground=[("selected", self.ACCENT)],
        )

        style.configure(
            "TButton",
            font=("Segoe UI", 10),
            padding=(12, 7),
            background="#e8edf3",
            foreground=self.TEXT,
            borderwidth=0,
        )
        style.map(
            "TButton",
            background=[("active", "#dbe3ec")],
        )

        style.configure(
            "Accent.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=(13, 8),
            background=self.ACCENT,
            foreground="white",
            borderwidth=0,
        )
        style.map(
            "Accent.TButton",
            background=[("active", self.ACCENT_DARK)],
        )

        style.configure(
            "Danger.TButton",
            font=("Segoe UI", 10),
            padding=(12, 7),
            background="#fee2e2",
            foreground="#991b1b",
            borderwidth=0,
        )

        style.configure(
            "TLabel",
            background=self.PANEL,
            foreground=self.TEXT,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Title.TLabel",
            background=self.BG,
            foreground=self.TEXT,
            font=("Segoe UI", 18, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            background=self.BG,
            foreground=self.MUTED,
            font=("Segoe UI", 9),
        )
        style.configure(
            "Section.TLabel",
            background=self.PANEL,
            foreground=self.TEXT,
            font=("Segoe UI", 11, "bold"),
        )
        style.configure(
            "Muted.TLabel",
            background=self.PANEL,
            foreground=self.MUTED,
            font=("Segoe UI", 9),
        )

    def _build_header(self):
        header = ttk.Frame(self)
        header.pack(fill="x", padx=26, pady=(20, 10))

        left = ttk.Frame(header)
        left.pack(side="left")

        ttk.Label(
            left,
            text="AI Systems Laboratory",
            style="Title.TLabel"
        ).pack(anchor="w")

        ttk.Label(
            left,
            text="Універсальний інтерфейс для лабораторних робіт із систем штучного інтелекту",
            style="Subtitle.TLabel"
        ).pack(anchor="w", pady=(3, 0))

        ttk.Label(
            header,
            text="LAB • AI",
            foreground=self.ACCENT,
            background=self.BG,
            font=("Segoe UI", 10, "bold")
        ).pack(side="right", pady=8)

    def _build_main(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=20, pady=5)

        self.lab_tab = ttk.Frame(notebook, style="Panel.TFrame")
        self.analysis_tab = ttk.Frame(notebook, style="Panel.TFrame")
        self.about_tab = ttk.Frame(notebook, style="Panel.TFrame")

        notebook.add(self.lab_tab, text="  Лабораторна  ")
        notebook.add(self.analysis_tab, text="  Аналіз результатів  ")
        notebook.add(self.about_tab, text="  Про програму  ")

        self._build_lab_tab()
        self._build_analysis_tab()
        self._build_about_tab()

    def _card(self, parent):
        frame = tk.Frame(
            parent,
            bg=self.PANEL,
            highlightbackground=self.BORDER,
            highlightthickness=1,
            bd=0,
        )
        return frame

    def _build_lab_tab(self):
        container = ttk.Frame(self.lab_tab, style="Panel.TFrame")
        container.pack(fill="both", expand=True)

        left = self._card(container)
        left.pack(side="left", fill="y", padx=(0, 10), pady=10)
        left.configure(width=315)
        left.pack_propagate(False)

        right = self._card(container)
        right.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)

        # Left controls
        tk.Label(
            left, text="Параметри експерименту",
            bg=self.PANEL, fg=self.TEXT,
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", padx=18, pady=(18, 14))

        self._field_label(left, "Алгоритм")
        self.algorithm = ttk.Combobox(
            left,
            values=[
                "Пошук у ширину (BFS)",
                "Пошук у глибину (DFS)",
                "Пошук A*",
                "Greedy Best-First Search",
                "Інший алгоритм..."
            ],
            state="readonly"
        )
        self.algorithm.set("Пошук у ширину (BFS)")
        self.algorithm.pack(fill="x", padx=18, pady=(0, 12))

        self._field_label(left, "Тип графа")
        self.graph_type = ttk.Combobox(
            left,
            values=[
                "Випадковий",
                "Розріджений",
                "Щільний",
                "Дерево",
                "Орієнтований"
            ],
            state="readonly"
        )
        self.graph_type.set("Випадковий")
        self.graph_type.pack(fill="x", padx=18, pady=(0, 12))

        self._field_label(left, "Кількість вершин")
        self.node_count = ttk.Spinbox(
            left, from_=4, to=80, increment=1, width=10
        )
        self.node_count.set("14")
        self.node_count.pack(fill="x", padx=18, pady=(0, 12))

        self._field_label(left, "Початкова вершина")
        self.start_node = ttk.Combobox(left, state="readonly")
        self.start_node.pack(fill="x", padx=18, pady=(0, 12))

        self._field_label(left, "Цільова вершина")
        self.goal_node = ttk.Combobox(left, state="readonly")
        self.goal_node.pack(fill="x", padx=18, pady=(0, 16))

        ttk.Button(
            left, text="Згенерувати граф",
            style="Accent.TButton",
            command=self.generate_graph
        ).pack(fill="x", padx=18, pady=(0, 8))

        ttk.Button(
            left, text="Запустити пошук",
            command=self.run_search
        ).pack(fill="x", padx=18, pady=4)

        row = ttk.Frame(left, style="Panel.TFrame")
        row.pack(fill="x", padx=18, pady=4)

        ttk.Button(row, text="Крок", command=self.step_search).pack(
            side="left", fill="x", expand=True, padx=(0, 4)
        )
        ttk.Button(row, text="Очистити", command=self.clear_search).pack(
            side="left", fill="x", expand=True, padx=(4, 0)
        )

        # Right visualization
        top = tk.Frame(right, bg=self.PANEL)
        top.pack(fill="x", padx=18, pady=(15, 8))

        tk.Label(
            top, text="Візуалізація",
            bg=self.PANEL, fg=self.TEXT,
            font=("Segoe UI", 12, "bold")
        ).pack(side="left")

        self.experiment_status = tk.Label(
            top,
            text="Готово до експерименту",
            bg=self.PANEL,
            fg=self.MUTED,
            font=("Segoe UI", 9)
        )
        self.experiment_status.pack(side="right")

        self.canvas = tk.Canvas(
            right,
            bg="#fbfcfd",
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True, padx=18, pady=(0, 12))
        self.canvas.bind("<Configure>", lambda e: self.draw_graph())

        # Metrics strip
        metrics = tk.Frame(right, bg="#f7f9fb")
        metrics.pack(fill="x", padx=18, pady=(0, 16))

        self.metric_labels = {}
        for key, label in [
            ("visited", "Відвідано"),
            ("path", "Довжина шляху"),
            ("steps", "Кроків"),
            ("time", "Час, мс"),
        ]:
            box = tk.Frame(
                metrics, bg="#f7f9fb",
                highlightbackground=self.BORDER,
                highlightthickness=1
            )
            box.pack(side="left", fill="x", expand=True, padx=3, pady=6)

            tk.Label(
                box, text=label, bg="#f7f9fb", fg=self.MUTED,
                font=("Segoe UI", 8)
            ).pack(pady=(6, 0))
            value = tk.Label(
                box, text="—", bg="#f7f9fb", fg=self.TEXT,
                font=("Segoe UI", 13, "bold")
            )
            value.pack(pady=(0, 6))
            self.metric_labels[key] = value

    def _build_analysis_tab(self):
        frame = self._card(self.analysis_tab)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(
            frame,
            text="Аналіз результатів експериментів",
            bg=self.PANEL, fg=self.TEXT,
            font=("Segoe UI", 14, "bold")
        ).pack(anchor="w", padx=20, pady=(20, 5))

        tk.Label(
            frame,
            text="Цей розділ можна використовувати для таблиць, графіків, статистики та порівняння алгоритмів.",
            bg=self.PANEL, fg=self.MUTED,
            font=("Segoe UI", 9)
        ).pack(anchor="w", padx=20, pady=(0, 15))

        columns = ("algorithm", "graph", "nodes", "visited", "path", "time")
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=14)

        headings = {
            "algorithm": "Алгоритм",
            "graph": "Тип графа",
            "nodes": "Вершин",
            "visited": "Відвідано",
            "path": "Шлях",
            "time": "Час, мс"
        }
        widths = {
            "algorithm": 220, "graph": 130, "nodes": 80,
            "visited": 100, "path": 80, "time": 90
        }

        for col in columns:
            tree.heading(col, text=headings[col])
            tree.column(col, width=widths[col], anchor="center")

        tree.pack(fill="both", expand=True, padx=20, pady=10)
        self.results_tree = tree

        actions = ttk.Frame(frame, style="Panel.TFrame")
        actions.pack(fill="x", padx=20, pady=(0, 20))

        ttk.Button(
            actions, text="Експорт JSON",
            command=self.export_results
        ).pack(side="left")

        ttk.Button(
            actions, text="Очистити таблицю",
            style="Danger.TButton",
            command=lambda: self._clear_tree()
        ).pack(side="left", padx=8)

    def _build_about_tab(self):
        frame = self._card(self.about_tab)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(
            frame,
            text="Універсальний каркас для лабораторних робіт",
            bg=self.PANEL, fg=self.TEXT,
            font=("Segoe UI", 16, "bold")
        ).pack(anchor="w", padx=30, pady=(30, 12))

        text = (
            "Ідея інтерфейсу — не прив'язувати GUI до одного алгоритму.\n\n"
            "Ліва панель відповідає за параметри експерименту:\n"
            "• алгоритм;\n"
            "• вхідні дані / тип задачі;\n"
            "• параметри генерації;\n"
            "• початкові та кінцеві умови.\n\n"
            "Центральна область призначена для візуалізації роботи алгоритму.\n"
            "Нижня частина показує кількісні характеристики.\n\n"
            "Для інших лабораторних тут можна замінити граф на:\n"
            "• нечітку систему;\n"
            "• дерево рішень;\n"
            "• нейронну мережу;\n"
            "• класифікацію даних;\n"
            "• генетичний алгоритм;\n"
            "• експертну систему.\n\n"
            "Основна перевага такого підходу — однакова структура GUI для різних робіт."
        )

        tk.Label(
            frame,
            text=text,
            justify="left",
            anchor="nw",
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Segoe UI", 10),
            padx=30
        ).pack(fill="both", expand=True)

    def _build_statusbar(self):
        self.status = tk.Label(
            self,
            text="Статус: готово",
            anchor="w",
            bg="#e9edf2",
            fg=self.MUTED,
            font=("Segoe UI", 8),
            padx=20,
            pady=6
        )
        self.status.pack(fill="x", side="bottom")

    def _field_label(self, parent, text):
        tk.Label(
            parent, text=text,
            bg=self.PANEL, fg=self.MUTED,
            font=("Segoe UI", 9)
        ).pack(anchor="w", padx=18, pady=(2, 4))

    # ---------- Graph ----------
    def generate_graph(self):
        try:
            n = int(self.node_count.get())
        except ValueError:
            n = 14
            self.node_count.set("14")

        n = max(4, min(80, n))
        self.nodes = {}
        self.edges = []
        self.adjacency = {}
        self.clear_search()

        graph_type = self.graph_type.get()

        for i in range(n):
            self.nodes[i] = {"x": 0, "y": 0}
            self.adjacency[i] = []

        # Guarantee a connected backbone.
        for i in range(n - 1):
            self._add_edge(i, i + 1, graph_type == "Орієнтований")

        # Additional edges.
        probability = {
            "Випадковий": 0.16,
            "Розріджений": 0.06,
            "Щільний": 0.38,
            "Дерево": 0.0,
            "Орієнтований": 0.14
        }.get(graph_type, 0.16)

        if graph_type == "Дерево":
            # Rewire a little while keeping it a tree.
            self.edges = []
            self.adjacency = {i: [] for i in range(n)}
            for i in range(1, n):
                parent = random.randrange(i)
                self._add_edge(parent, i, False)

        else:
            for i in range(n):
                for j in range(i + 2, n):
                    if random.random() < probability:
                        self._add_edge(i, j, graph_type == "Орієнтований")

        self._update_node_selectors()
        self.draw_graph()
        self._set_status("Граф згенеровано")

    def _add_edge(self, a, b, directed=False):
        if b not in self.adjacency[a]:
            self.adjacency[a].append(b)
            self.edges.append((a, b, directed))

        if not directed and a not in self.adjacency[b]:
            self.adjacency[b].append(a)

    def _update_node_selectors(self):
        values = [str(i) for i in self.nodes]
        self.start_node["values"] = values
        self.goal_node["values"] = values

        self.start_node.set(values[0])
        self.goal_node.set(values[-1])

    def draw_graph(self):
        if not hasattr(self, "canvas"):
            return

        self.canvas.delete("all")
        if not self.nodes:
            return

        width = max(400, self.canvas.winfo_width())
        height = max(350, self.canvas.winfo_height())

        # Circular layout for clarity.
        cx, cy = width / 2, height / 2
        radius = min(width, height) * 0.36
        count = len(self.nodes)

        for idx, node in enumerate(self.nodes):
            angle = 2 * 3.141592653589793 * idx / count - 3.141592653589793 / 2
            self.nodes[node]["x"] = cx + radius * __import__("math").cos(angle)
            self.nodes[node]["y"] = cy + radius * __import__("math").sin(angle)

        # Edges
        for a, b, directed in self.edges:
            x1, y1 = self.nodes[a]["x"], self.nodes[a]["y"]
            x2, y2 = self.nodes[b]["x"], self.nodes[b]["y"]

            color = "#b9c2cc"
            width_line = 2

            if a in self.search_path and b in self.search_path:
                try:
                    if abs(self.search_path.index(a) - self.search_path.index(b)) == 1:
                        color = self.SUCCESS
                        width_line = 4
                except ValueError:
                    pass

            self.canvas.create_line(
                x1, y1, x2, y2,
                fill=color, width=width_line,
                arrow=tk.LAST if directed else tk.NONE,
                arrowshape=(10, 12, 5)
            )

        # Nodes
        start = self._safe_int(self.start_node.get(), 0)
        goal = self._safe_int(self.goal_node.get(), len(self.nodes) - 1)

        for node, pos in self.nodes.items():
            x, y = pos["x"], pos["y"]

            fill = "#ffffff"
            outline = "#64748b"
            radius_node = 21
            outline_width = 2

            if node in self.visited_order:
                fill = "#dbeafe"
                outline = self.ACCENT

            if node == start:
                fill = "#dcfce7"
                outline = self.SUCCESS

            if node == goal:
                fill = "#fef3c7"
                outline = self.WARNING

            if node in self.search_path:
                fill = "#bbf7d0"
                outline = self.SUCCESS
                outline_width = 3

            self.canvas.create_oval(
                x - radius_node, y - radius_node,
                x + radius_node, y + radius_node,
                fill=fill, outline=outline, width=outline_width
            )

            self.canvas.create_text(
                x, y,
                text=str(node),
                fill=self.TEXT,
                font=("Segoe UI", 9, "bold")
            )

    # ---------- BFS ----------
    def run_search(self):
        if self.running:
            return

        start = self._safe_int(self.start_node.get(), 0)
        goal = self._safe_int(self.goal_node.get(), len(self.nodes) - 1)
        algorithm = self.algorithm.get()

        if algorithm != "Пошук у ширину (BFS)":
            messagebox.showinfo(
                "Шаблон алгоритму",
                "У цьому прикладі реалізовано BFS.\n"
                "Інші алгоритми можна підключити до тієї ж GUI без зміни дизайну."
            )
            return

        self.clear_search()
        self.running = True
        self.experiment_status.config(text="Виконується пошук...", fg=self.ACCENT)
        self._set_status("BFS: виконання")

        queue = deque([start])
        parent = {start: None}
        visited = {start}
        order = []

        t0 = time.perf_counter()

        while queue:
            current = queue.popleft()
            order.append(current)

            if current == goal:
                break

            for neighbor in self.adjacency.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    parent[neighbor] = current
                    queue.append(neighbor)

        elapsed = (time.perf_counter() - t0) * 1000

        path = []
        if goal in parent:
            current = goal
            while current is not None:
                path.append(current)
                current = parent[current]
            path.reverse()

        self.visited_order = order
        self.search_path = path

        self.metric_labels["visited"].config(text=str(len(order)))
        self.metric_labels["path"].config(
            text=str(len(path) - 1) if path else "—"
        )
        self.metric_labels["steps"].config(text=str(len(order)))
        self.metric_labels["time"].config(text=f"{elapsed:.3f}")

        self.draw_graph()
        self.running = False
        self.experiment_status.config(
            text="Пошук завершено" if path else "Ціль не знайдена",
            fg=self.SUCCESS if path else self.WARNING
        )
        self._set_status(
            f"BFS завершено • відвідано {len(order)} • шлях {len(path) - 1 if path else '—'}"
        )

        self.results_tree.insert(
            "",
            "end",
            values=(
                "BFS",
                self.graph_type.get(),
                len(self.nodes),
                len(order),
                len(path) - 1 if path else "—",
                f"{elapsed:.3f}"
            )
        )

    def step_search(self):
        """Simple educational step mode: reveals BFS traversal one node at a time."""
        if not self.nodes:
            return

        start = self._safe_int(self.start_node.get(), 0)
        goal = self._safe_int(self.goal_node.get(), len(self.nodes) - 1)

        # Build BFS order once.
        queue = deque([start])
        visited = {start}
        order = []

        while queue:
            current = queue.popleft()
            order.append(current)
            if current == goal:
                break
            for neighbor in self.adjacency.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        if self.step_index >= len(order):
            self.step_index = 0
            self.visited_order = []
            self.draw_graph()

        self.visited_order = order[:self.step_index + 1]
        self.step_index += 1
        self.draw_graph()
        self._set_status(
            f"Крок {self.step_index}/{len(order)} • поточна вершина {self.visited_order[-1]}"
        )

        self.metric_labels["visited"].config(text=str(len(self.visited_order)))
        self.metric_labels["steps"].config(text=str(self.step_index))

    def clear_search(self):
        self.running = False
        self.step_index = 0
        self.visited_order = []
        self.search_path = []

        if hasattr(self, "metric_labels"):
            for label in self.metric_labels.values():
                label.config(text="—")

        if hasattr(self, "experiment_status"):
            self.experiment_status.config(
                text="Готово до експерименту",
                fg=self.MUTED
            )

        if hasattr(self, "canvas"):
            self.draw_graph()

    # ---------- Utility ----------
    @staticmethod
    def _safe_int(value, default):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _set_status(self, text):
        self.status.config(text=f"Статус: {text}")

    def _clear_tree(self):
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

    def export_results(self):
        rows = []
        for item in self.results_tree.get_children():
            values = self.results_tree.item(item, "values")
            rows.append({
                "algorithm": values[0],
                "graph": values[1],
                "nodes": values[2],
                "visited": values[3],
                "path": values[4],
                "time_ms": values[5],
            })

        if not rows:
            messagebox.showinfo("Експорт", "Таблиця результатів порожня.")
            return

        path = filedialog.asksaveasfilename(
            title="Зберегти результати",
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All files", "*.*")]
        )
        if not path:
            return

        with open(path, "w", encoding="utf-8") as file:
            json.dump(rows, file, ensure_ascii=False, indent=2)

        self._set_status(f"Результати збережено: {path}")

    def _on_close(self):
        if self.animation_job:
            self.after_cancel(self.animation_job)
        self.destroy()


if __name__ == "__main__":
    app = AISystemsApp()
    app.mainloop()
