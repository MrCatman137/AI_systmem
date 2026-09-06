from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from template import COLORS, create_button, create_card, create_combobox, create_entry, create_label, create_title

from lab_1.bfs import BFSResult, BFSRunner
from lab_1.data.default_graph import create_default_graph
from lab_1.graph import Edge, Graph, GraphError, Vertex


class BFSApplication(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("AI Systems Laboratory | BFS")
        self.geometry("1450x900")
        self.minsize(1050, 680)
        self.configure(fg_color=COLORS["background"])
        self.graph = create_default_graph()
        self.runner: BFSRunner | None = None
        self.last_result: BFSResult | None = None
        self.experiments: list[dict[str, str]] = []
        self.animation_job: str | None = None
        self.selection_mode: str | None = None
        self.drag_vertex_id: int | None = None
        self.drag_moved = False
        self.drag_offset = (0.0, 0.0)
        self.build_shell()
        self.show_lab()

    def build_shell(self) -> None:
        self.sidebar = ctk.CTkFrame(self, width=230, corner_radius=0, fg_color=COLORS["sidebar"])
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        create_label(self.sidebar, "Системи штучного\nінтелекту", 20, True).pack(padx=25, pady=(30, 5), anchor="w")
        create_label(self.sidebar, "Лабораторна робота №1", 11, color=COLORS["text_secondary"]).pack(padx=25, anchor="w")
        self.lab_button = create_button(self.sidebar, "Лабораторна", self.show_lab, width=180)
        self.lab_button.pack(padx=25, pady=(40, 10))
        self.results_button = create_button(self.sidebar, "Результати", self.show_results, width=180, style="secondary")
        self.results_button.pack(padx=25, pady=10)
        self.theory_button = create_button(self.sidebar, "Теорія BFS", self.show_theory, width=180, style="secondary")
        self.theory_button.pack(padx=25, pady=10)
        self.main = ctk.CTkFrame(self, fg_color="transparent")
        self.main.pack(side="left", fill="both", expand=True, padx=25, pady=25)

    def clear_main(self) -> None:
        if self.animation_job:
            self.after_cancel(self.animation_job)
            self.animation_job = None
        for widget in self.main.winfo_children():
            widget.destroy()

    def show_lab(self) -> None:
        self.clear_main()
        create_title(self.main, "Лабораторна робота №1").pack(anchor="w")
        create_label(self.main, "Сліпий пошук на графах: пошук у ширину (BFS)", 13, color=COLORS["text_secondary"]).pack(anchor="w", pady=(5, 15))
        content = ctk.CTkFrame(self.main, fg_color="transparent")
        content.pack(fill="both", expand=True)
        self.build_controls(content)
        self.build_visualization(content)
        self.refresh_controls()
        self.draw_graph()

    def build_controls(self, parent) -> None:
        card = create_card(parent)
        card.pack(side="left", fill="y", padx=(0, 15))
        card.configure(width=315)
        card.pack_propagate(False)

        left = ctk.CTkScrollableFrame(
            card,
            corner_radius=5,
            fg_color=COLORS["card"],
            scrollbar_button_color=COLORS["secondary"],
            scrollbar_button_hover_color=COLORS["secondary_hover"],
        )
        left.pack(fill="both", expand=True)
        create_label(left, "Параметри експерименту", 18, True).pack(padx=18, pady=(18, 12), anchor="w")
        self.add_field(left, "Тип графа")
        self.graph_type_var = ctk.StringVar(value=self.graph.graph_type)
        self.graph_type = create_combobox(left, ["undirected", "directed", "tree"], 275)
        self.graph_type.configure(variable=self.graph_type_var, command=self.change_graph_type)
        self.graph_type.pack(padx=18, pady=(3, 10))
        self.add_field(left, "Розмір випадкового графа")
        generation_size_row = ctk.CTkFrame(left, fg_color="transparent")
        generation_size_row.pack(fill="x", padx=10, pady=(3, 8))
        self.generate_vertex_count = create_entry(generation_size_row, "Vertices", 125)
        self.generate_edge_count = create_entry(generation_size_row, "Edges", 125)
        self.generate_vertex_count.insert(0, "30")
        self.generate_edge_count.insert(0, "48")
        self.generate_vertex_count.pack(side="left", fill="x", expand=True, padx=2)
        self.generate_edge_count.pack(side="left", fill="x", expand=True, padx=2)
        self.add_field(left, "Початкова вершина")
        self.start_var = ctk.StringVar(value="1")
        self.start_combo = create_combobox(left, [], 275)
        self.start_combo.configure(variable=self.start_var)
        self.start_combo.pack(padx=18, pady=(3, 8))
        create_button(left, "Вибрати Start на графі", lambda: self.select_on_canvas("start"), width=275, style="secondary").pack(padx=18, pady=(0, 5))
        self.add_field(left, "Цільова вершина")
        self.target_var = ctk.StringVar(value="30")
        self.target_combo = create_combobox(left, [], 275)
        self.target_combo.configure(variable=self.target_var)
        self.target_combo.pack(padx=18, pady=(3, 8))
        create_button(left, "Вибрати Target на графі", lambda: self.select_on_canvas("target"), width=275, style="secondary").pack(padx=18, pady=(0, 5))
        self.add_field(left, "Порядок сусідів")
        self.order_var = ctk.StringVar(value="ascending")
        self.order_combo = create_combobox(left, ["ascending", "descending", "custom"], 275)
        self.order_combo.configure(variable=self.order_var)
        self.order_combo.pack(padx=18, pady=(3, 5))
        self.custom_order = create_entry(left, "Custom: 8, 3, 12", 275)
        self.custom_order.pack(padx=18, pady=(0, 8))
        self.speed_var = ctk.StringVar(value="250 ms")
        self.speed_combo = create_combobox(left, ["100 ms", "250 ms", "500 ms", "1000 ms"], 275)
        self.speed_combo.configure(variable=self.speed_var)
        self.speed_combo.pack(padx=18, pady=(0, 10))
        buttons = ctk.CTkFrame(left, fg_color="transparent")
        buttons.pack(fill="x", padx=18)
        create_button(buttons, "Запустити BFS", self.run_bfs, width=132, style="success").pack(side="left", padx=(0, 4))
        create_button(buttons, "Крок", self.step_bfs, width=132).pack(side="left", padx=(4, 0))
        create_button(left, "Побудувати шлях без анімації", self.run_bfs_instant, width=260, style="success").pack(padx=10, pady=(5, 7))
        create_button(left, "Згенерувати випадковий граф", self.generate_random_graph, width=260, style="secondary").pack(padx=10, pady=2)
        create_button(left, "Очистити пошук", self.reset_search, width=275, style="secondary").pack(padx=18, pady=7)
        create_button(left, "Поміняти Start ↔ Target", self.reverse_search, width=275, style="secondary").pack(padx=18, pady=2)
        create_label(left, "Редагування графа", 15, True).pack(padx=18, pady=(15, 7), anchor="w")

        vertex_row = ctk.CTkFrame(left, fg_color="transparent")
        vertex_row.pack(fill="x", padx=10, pady=2)
        self.vertex_id = create_entry(vertex_row, "ID", 82)
        self.vertex_x = create_entry(vertex_row, "X", 82)
        self.vertex_y = create_entry(vertex_row, "Y", 82)
        for entry in (self.vertex_id, self.vertex_x, self.vertex_y):
            entry.pack(in_=vertex_row, side="left", fill="x", expand=True, padx=2)
        create_button(left, "Додати вершину", self.add_vertex, width=260).pack(padx=10, pady=5)

        edge_row = ctk.CTkFrame(left, fg_color="transparent")
        edge_row.pack(fill="x", padx=10, pady=2)
        self.edge_a = create_entry(edge_row, "A", 125)
        self.edge_b = create_entry(edge_row, "B", 125)
        self.edge_a.pack(in_=edge_row, side="left", fill="x", expand=True, padx=2)
        self.edge_b.pack(in_=edge_row, side="left", fill="x", expand=True, padx=2)
        self.directed_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(left, text="Directed edge", variable=self.directed_var, font=("Segoe UI", 12)).pack(padx=18, pady=4, anchor="w")
        edge_buttons = ctk.CTkFrame(left, fg_color="transparent")
        edge_buttons.pack(fill="x", padx=10, pady=3)
        create_button(edge_buttons, "Додати edge", self.add_edge, width=125).pack(side="left", fill="x", expand=True, padx=2)
        create_button(edge_buttons, "Видалити edge", self.remove_edge, width=125, style="danger").pack(side="left", fill="x", expand=True, padx=2)
        create_button(left, "Перетворити edge", self.convert_edge, width=260, style="secondary").pack(padx=10, pady=3)
        create_button(left, "Видалити вершину", self.remove_vertex, width=260, style="danger").pack(padx=10, pady=5)
        create_button(left, "Reset graph", self.reset_graph, width=260, style="secondary").pack(padx=10, pady=2)
        self.status_label = create_label(left, "Готово", 11, color=COLORS["text_secondary"])
        self.status_label.pack(padx=18, pady=(12, 5), anchor="w")

    def add_field(self, parent, text: str) -> None:
        create_label(parent, text, 12, color=COLORS["text_secondary"]).pack(padx=18, anchor="w")

    def build_visualization(self, parent) -> None:
        right = create_card(parent)
        right.pack(side="left", fill="both", expand=True)
        header = ctk.CTkFrame(right, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(15, 6))
        create_label(header, "Візуалізація BFS", 18, True).pack(side="left")
        self.graph_stats = create_label(header, "", 12, color=COLORS["text_secondary"])
        self.graph_stats.pack(side="right")
        self.canvas = __import__("tkinter").Canvas(right, bg=COLORS["background"], highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=18, pady=(0, 5))
        self.canvas.bind("<Configure>", lambda event: self.draw_graph())
        self.canvas.bind("<Button-1>", self.canvas_press)
        self.canvas.bind("<B1-Motion>", self.canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.canvas_release)
        legend = create_label(right, "Shift + клік: Start | Ctrl + клік: Target | зелений: відвідані | контур: шлях", 11, color=COLORS["text_secondary"])
        legend.pack(anchor="w", padx=18, pady=(0, 10))
        bottom = ctk.CTkFrame(right, fg_color="transparent")
        bottom.pack(fill="x", padx=18, pady=(0, 15))
        self.result_label = create_label(bottom, "Результат: пошук ще не запускався", 12)
        self.result_label.pack(side="left", anchor="w")
        create_button(bottom, "Зберегти граф", self.save_graph, width=125, style="secondary").pack(side="right", padx=(5, 0))
        create_button(bottom, "Завантажити", self.load_graph, width=125, style="secondary").pack(side="right")

    def refresh_controls(self) -> None:
        values = [str(value) for value in sorted(self.graph.vertices)]
        self.start_combo.configure(values=values)
        self.target_combo.configure(values=values)
        if values:
            if self.start_var.get() not in values:
                self.start_var.set(values[0])
            if self.target_var.get() not in values:
                self.target_var.set(values[-1])
        self.graph_stats.configure(text=f"V = {len(self.graph.vertices)}   E = {self.graph.edge_count}   {self.graph.graph_type}")

    def parse_custom_order(self) -> list[int]:
        if self.order_var.get() != "custom":
            return []
        raw = self.custom_order.get().replace(";", ",").split(",")
        try:
            order = [int(value.strip()) for value in raw if value.strip()]
        except ValueError as error:
            raise ValueError("Custom order must contain vertex IDs separated by commas.") from error
        if set(order) - set(self.graph.vertices):
            raise ValueError("Custom order contains a vertex that does not exist.")
        return order

    def create_runner(self) -> BFSRunner:
        try:
            start, target = int(self.start_var.get()), int(self.target_var.get())
            custom = self.parse_custom_order()
        except ValueError as error:
            raise ValueError(str(error)) from error
        return BFSRunner(self.graph, start, target, self.order_var.get(), custom)

    def run_bfs(self) -> None:
        try:
            self.runner = self.create_runner()
        except (ValueError, GraphError) as error:
            messagebox.showerror("Помилка BFS", str(error))
            return
        self.last_result = None
        self.result_label.configure(text="BFS виконується...")
        self.animate_step()

    def run_bfs_instant(self) -> None:
        if self.animation_job:
            self.after_cancel(self.animation_job)
            self.animation_job = None
        try:
            self.runner = self.create_runner()
            self.runner.run()
        except (ValueError, GraphError) as error:
            messagebox.showerror("Помилка BFS", str(error))
            return
        self.finish_search()

    def animate_step(self) -> None:
        if self.runner is None:
            return
        self.runner.step()
        self.draw_graph()
        if not self.runner.finished:
            delay = int(self.speed_var.get().split()[0])
            self.animation_job = self.after(delay, self.animate_step)
        else:
            self.finish_search()

    def step_bfs(self) -> None:
        try:
            if self.runner is None or self.runner.finished:
                self.runner = self.create_runner()
            self.runner.step()
            self.draw_graph()
            if self.runner.finished:
                self.finish_search()
        except (ValueError, GraphError) as error:
            messagebox.showerror("Помилка BFS", str(error))

    def finish_search(self) -> None:
        if self.runner is None:
            return
        self.last_result = self.runner.result()
        result = self.last_result
        path = " → ".join(map(str, result.path)) if result.found else "не знайдено"
        self.result_label.configure(text=f"{'Шлях: ' + path if result.found else 'Шлях не знайдено'} | відкрито: {len(result.expanded_vertices)} | ітерацій: {result.iterations}")
        self.status_label.configure(text="Пошук завершено", text_color=COLORS["success"] if result.found else COLORS["danger"])
        self.draw_graph()

    def reset_search(self) -> None:
        self.runner = None
        self.last_result = None
        self.status_label.configure(text="Пошук очищено", text_color=COLORS["text_secondary"])
        if hasattr(self, "result_label"):
            self.result_label.configure(text="Результат: пошук ще не запускався")
            self.draw_graph()

    def reverse_search(self) -> None:
        start, target = self.start_var.get(), self.target_var.get()
        self.start_var.set(target)
        self.target_var.set(start)
        self.reset_search()

    def draw_graph(self) -> None:
        if not hasattr(self, "canvas") or not self.canvas.winfo_exists():
            return
        self.canvas.delete("all")
        width, height = max(self.canvas.winfo_width(), 500), max(self.canvas.winfo_height(), 400)
        sx, sy = (width - 35) / 1230, (height - 35) / 460
        def point(vertex: Vertex) -> tuple[float, float]:
            return 18 + vertex.x * sx, 18 + vertex.y * sy
        path = set(self.last_result.path if self.last_result else [])
        visited = set(self.runner.visited if self.runner else [])
        expanded = set(self.runner.expanded if self.runner else [])
        current = self.runner.current_vertex if self.runner else None
        for edge in self.graph.edges:
            source, target = point(self.graph.vertices[edge.source]), point(self.graph.vertices[edge.target])
            color = COLORS["primary_hover"] if edge.source in path and edge.target in path else COLORS["border"]
            self.canvas.create_line(*source, *target, fill=color, width=3 if color != COLORS["border"] else 1.5, arrow="last" if edge.directed else None)
            if edge.directed:
                marker_x, marker_y = self.directed_marker(source, target)
                self.canvas.create_oval(
                    marker_x - 4, marker_y - 4, marker_x + 4, marker_y + 4,
                    fill=color, outline=color,
                )
        for vertex_id, vertex in self.graph.vertices.items():
            x, y = point(vertex)
            radius = 16
            if vertex_id in path:
                fill, outline = COLORS["primary"], COLORS["primary_hover"]
            elif vertex_id == current:
                fill, outline = "#fbbf24", "#d97706"
            elif vertex_id in expanded:
                fill, outline = "#86efac", COLORS["success"]
            elif vertex_id in visited:
                fill, outline = "#dcfce7", COLORS["success"]
            else:
                fill, outline = COLORS["card"], COLORS["text_secondary"]
            if str(vertex_id) == self.start_var.get():
                fill, outline = "#bfdbfe", "#2563eb"
            if str(vertex_id) == self.target_var.get():
                outline = COLORS["danger"]
            self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=fill, outline=outline, width=3 if vertex_id in {int(self.start_var.get() or 0), int(self.target_var.get() or 0)} else 1)
            self.canvas.create_text(x, y, text=str(vertex_id), fill=COLORS["text"], font=("Segoe UI", 10, "bold"))

    @staticmethod
    def directed_marker(source: tuple[float, float], target: tuple[float, float]) -> tuple[float, float]:
        dx, dy = target[0] - source[0], target[1] - source[1]
        length = max((dx * dx + dy * dy) ** 0.5, 1)
        offset = 22
        return target[0] - dx / length * offset, target[1] - dy / length * offset

    def canvas_position(self, event) -> tuple[Vertex | None, float, float, float, float]:
        width, height = max(self.canvas.winfo_width(), 500), max(self.canvas.winfo_height(), 400)
        sx, sy = (width - 35) / 1230, (height - 35) / 460
        nearest = min(
            self.graph.vertices.values(),
            key=lambda vertex: ((18 + vertex.x * sx - event.x) ** 2 + (18 + vertex.y * sy - event.y) ** 2),
            default=None,
        )
        if nearest is None:
            return None, sx, sy, 0.0, 0.0
        canvas_x, canvas_y = 18 + nearest.x * sx, 18 + nearest.y * sy
        distance = ((canvas_x - event.x) ** 2 + (canvas_y - event.y) ** 2) ** 0.5
        return nearest, sx, sy, distance, 16

    def canvas_press(self, event) -> None:
        if not self.graph.vertices:
            return
        nearest, sx, sy, distance, radius = self.canvas_position(event)
        if nearest is None or distance > radius + 5:
            return
        if event.state & 0x0001:
            self.start_var.set(str(nearest.id))
            self.selection_mode = None
            self.reset_search()
            return
        elif event.state & 0x0004:
            self.target_var.set(str(nearest.id))
            self.selection_mode = None
            self.reset_search()
            return
        self.drag_vertex_id = nearest.id
        self.drag_moved = False
        self.drag_offset = (event.x - (18 + nearest.x * sx), event.y - (18 + nearest.y * sy))

    def canvas_drag(self, event) -> None:
        if self.drag_vertex_id is None:
            return
        width, height = max(self.canvas.winfo_width(), 500), max(self.canvas.winfo_height(), 400)
        sx, sy = (width - 35) / 1230, (height - 35) / 460
        x = max(25, min(1225, (event.x - self.drag_offset[0] - 18) / sx))
        y = max(25, min(455, (event.y - self.drag_offset[1] - 18) / sy))
        vertex = self.graph.vertices[self.drag_vertex_id]
        self.graph.vertices[self.drag_vertex_id] = Vertex(vertex.id, x, y)
        self.drag_moved = True
        self.reset_search()
        self.draw_graph()

    def canvas_release(self, event) -> None:
        if self.drag_vertex_id is None:
            return
        vertex_id = self.drag_vertex_id
        moved = self.drag_moved
        self.drag_vertex_id = None
        self.drag_moved = False
        if moved:
            self.status_label.configure(text=f"Вершину {vertex_id} переміщено", text_color=COLORS["success"])
            return
        if self.selection_mode == "target":
            self.target_var.set(str(vertex_id))
            self.selection_mode = None
        elif self.selection_mode == "start":
            self.start_var.set(str(vertex_id))
            self.selection_mode = None
        else:
            self.start_var.set(str(vertex_id))
        self.reset_search()

    def select_on_canvas(self, selection: str) -> None:
        self.selection_mode = selection
        self.status_label.configure(text=f"Клікніть вершину для {selection}", text_color=COLORS["primary_hover"])

    def change_graph_type(self, _value: str = "") -> None:
        previous = self.graph.graph_type
        try:
            self.graph.set_graph_type(self.graph_type_var.get())
        except GraphError as error:
            self.graph_type_var.set(previous)
            messagebox.showerror("Тип графа", str(error))
            return
        if self.graph_type_var.get() == "tree" and hasattr(self, "generate_edge_count"):
            self.generate_edge_count.delete(0, "end")
            self.generate_edge_count.insert(0, str(len(self.graph.vertices) - 1))
        self.reset_search()
        self.refresh_controls()
        self.draw_graph()

    def add_vertex(self) -> None:
        try:
            vertex = Vertex(int(self.vertex_id.get()), float(self.vertex_x.get()), float(self.vertex_y.get()))
            self.graph.add_vertex(vertex)
            self.refresh_after_edit()
        except (ValueError, GraphError) as error:
            messagebox.showerror("Вершина", str(error))

    def remove_vertex(self) -> None:
        try:
            self.graph.remove_vertex(int(self.vertex_id.get() or self.target_var.get()))
            self.refresh_after_edit()
        except (ValueError, GraphError) as error:
            messagebox.showerror("Вершина", str(error))

    def add_edge(self) -> None:
        try:
            self.graph.add_edge(int(self.edge_a.get()), int(self.edge_b.get()), self.directed_var.get())
            self.refresh_after_edit()
        except (ValueError, GraphError) as error:
            messagebox.showerror("Edge", str(error))

    def remove_edge(self) -> None:
        try:
            self.graph.remove_edge(int(self.edge_a.get()), int(self.edge_b.get()))
            self.refresh_after_edit()
        except (ValueError, GraphError) as error:
            messagebox.showerror("Edge", str(error))

    def convert_edge(self) -> None:
        try:
            self.graph.convert_edge(int(self.edge_a.get()), int(self.edge_b.get()), self.directed_var.get())
            self.refresh_after_edit()
        except (ValueError, GraphError) as error:
            messagebox.showerror("Edge", str(error))

    def refresh_after_edit(self) -> None:
        self.reset_search()
        self.refresh_controls()
        self.draw_graph()

    def reset_graph(self) -> None:
        self.graph = create_default_graph()
        self.start_var.set("1")
        self.target_var.set("30")
        self.graph_type_var.set("undirected")
        self.refresh_after_edit()

    def generate_random_graph(self) -> None:
        graph_type = self.graph_type_var.get()
        try:
            vertex_count = int(self.generate_vertex_count.get())
            edge_count = int(self.generate_edge_count.get())
        except ValueError as error:
            messagebox.showerror("Генерація графа", "Vertices and Edges must be whole numbers.")
            return
        if not 2 <= vertex_count <= 80:
            messagebox.showerror("Генерація графа", "Vertices must be between 2 and 80.")
            return
        if edge_count < vertex_count - 1:
            messagebox.showerror("Генерація графа", "At least V - 1 edges are required to keep the graph connected.")
            return
        if graph_type == "tree" and edge_count != vertex_count - 1:
            messagebox.showerror("Генерація графа", "A tree must contain exactly V - 1 edges.")
            return

        # Build a tree as an undirected graph first; the Graph tree invariant
        # validates the completed structure when the mode is applied below.
        graph = Graph("undirected" if graph_type == "tree" else graph_type)
        generator = random.Random()
        columns = min(10, max(2, int(vertex_count ** 0.5) + 1))
        horizontal_step = 1120 / max(columns - 1, 1)
        rows = (vertex_count + columns - 1) // columns
        vertical_step = 400 / max(rows - 1, 1)
        positions: dict[int, tuple[float, float]] = {}
        for vertex_id in range(1, vertex_count + 1):
            column, row = (vertex_id - 1) % columns, (vertex_id - 1) // columns
            x = 55 + column * horizontal_step + generator.uniform(-12, 12)
            y = 45 + row * vertical_step + generator.uniform(-10, 10)
            positions[vertex_id] = (x, y)
            graph.add_vertex(Vertex(vertex_id, x, y))

        def distance(first: int, second: int) -> float:
            first_x, first_y = positions[first]
            second_x, second_y = positions[second]
            return ((first_x - second_x) ** 2 + (first_y - second_y) ** 2) ** 0.5

        local_limit = max(horizontal_step * 1.55, vertical_step * 1.55, 145)
        candidates = [
            (source, target)
            for source in range(1, vertex_count + 1)
            for target in range(source + 1, vertex_count + 1)
            if distance(source, target) <= local_limit
        ]
        candidate_set = set(candidates)

        # Start with local links that guarantee connectivity without long jumps.
        spanning_edges: list[tuple[int, int]] = []
        for vertex_id in range(2, vertex_count + 1):
            possible_parents = [
                parent for parent in range(1, vertex_id)
                if tuple(sorted((vertex_id, parent))) in candidate_set
            ]
            if not possible_parents:
                messagebox.showerror("Генерація графа", "Could not build a connected local graph with these dimensions.")
                return
            parent = generator.choice(possible_parents)
            spanning_edges.append(tuple(sorted((vertex_id, parent))))

        generator.shuffle(candidates)
        selected = list(dict.fromkeys(spanning_edges + candidates))[:edge_count]
        if len(selected) < edge_count:
            messagebox.showerror("Генерація графа", "There are not enough nearby vertex pairs for this edge count.")
            return
        for source, target in selected:
            if graph_type == "directed" and generator.choice([True, False]):
                source, target = target, source
            graph.add_edge(source, target)
        if graph_type == "tree":
            graph.set_graph_type("tree")

        self.graph = graph
        self.start_var.set("1")
        self.target_var.set(str(vertex_count))
        self.reset_search()
        self.refresh_controls()
        self.draw_graph()
        self.status_label.configure(text=f"Згенеровано граф: {graph_type}", text_color=COLORS["success"])

    def save_graph(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if path:
            Path(path).write_text(json.dumps(self.graph.to_dict(), indent=2), encoding="utf-8")

    def load_graph(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not path:
            return
        try:
            self.graph = Graph.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
            self.graph_type_var.set(self.graph.graph_type)
            self.refresh_after_edit()
        except (OSError, json.JSONDecodeError, KeyError, ValueError, GraphError) as error:
            messagebox.showerror("Завантаження", str(error))

    def show_results(self) -> None:
        self.clear_main()
        create_title(self.main, "Результати та експерименти").pack(anchor="w")
        create_label(self.main, "Зберігайте результати запусків для порівняння типів графів і порядку обходу.", 13, color=COLORS["text_secondary"]).pack(anchor="w", pady=(5, 15))
        card = create_card(self.main)
        card.pack(fill="both", expand=True)
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=18, pady=15)
        create_button(top, "Додати поточний результат", self.add_experiment, width=220, style="success").pack(side="left")
        create_button(top, "Очистити таблицю", self.clear_experiments, width=160, style="secondary").pack(side="left", padx=8)
        columns = ("№", "Type", "V", "E", "Start", "Target", "Order", "Path", "Expanded", "Iterations", "Time")
        table = ttk.Treeview(card, columns=columns, show="headings")
        for column in columns:
            table.heading(column, text=column)
            table.column(column, width=82, anchor="center")
        table.pack(fill="both", expand=True, padx=18, pady=(0, 18))
        for row in self.experiments:
            table.insert("", "end", values=[row[column] for column in columns])
        self.experiment_table = table

    def add_experiment(self) -> None:
        if not self.last_result:
            messagebox.showinfo("Експеримент", "Спочатку виконайте BFS.")
            return
        result = self.last_result
        self.experiments.append({
            "№": str(len(self.experiments) + 1), "Type": self.graph.graph_type,
            "V": str(len(self.graph.vertices)), "E": str(self.graph.edge_count),
            "Start": self.start_var.get(), "Target": self.target_var.get(),
            "Order": self.order_var.get(), "Path": str(len(result.path) - 1 if result.found else "-") if result.found else "-",
            "Expanded": str(len(result.expanded_vertices)), "Iterations": str(result.iterations),
            "Time": f"{result.elapsed_time * 1000:.3f} ms",
        })
        self.show_results()

    def clear_experiments(self) -> None:
        self.experiments.clear()
        self.show_results()

    def show_theory(self) -> None:
        self.clear_main()
        create_title(self.main, "Теорія: пошук у ширину").pack(anchor="w")
        card = create_card(self.main)
        card.pack(fill="both", expand=True, pady=(15, 0))
        text = (
            "BFS explores a graph level by level using a FIFO queue.\n\n"
            "Algorithm:\n"
            "1. Put Start in the queue and mark it visited.\n"
            "2. Remove the first vertex from the queue.\n"
            "3. Add every unvisited neighbor and remember its parent.\n"
            "4. Stop at Target or when the queue is empty.\n\n"
            "Time complexity: O(V + E)\n"
            "Space complexity: O(V)\n\n"
            "Advantages: complete for finite graphs; finds a shortest path in an unweighted graph;"
            " systematic and effective when the target is close.\n\n"
            "Disadvantages: can use significant memory, expand unnecessary vertices,"
            " ignore edge weights, and slow down on graphs with a large branching factor."
        )
        create_label(card, text, 15).pack(padx=28, pady=28, anchor="nw")


if __name__ == "__main__":
    app = BFSApplication()
    app.mainloop()