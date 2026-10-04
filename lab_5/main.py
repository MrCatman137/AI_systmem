from __future__ import annotations

import base64
import json
import sys
import tkinter as tk
from io import BytesIO
from pathlib import Path
from time import perf_counter
from tkinter import filedialog, messagebox, simpledialog, ttk

import customtkinter as ctk
from PIL import Image, ImageTk

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from template import COLORS, create_button, create_card, create_combobox, create_entry, create_label, create_title

from lab_5.dijkstra import DijkstraResult, DijkstraRunner
from lab_5.graph import Graph, GraphError, Vertex

DEFAULT_GRAPH_PATH = Path(__file__).resolve().parent / "graphs" / "ukraine_roads.json"


def read_graph_document(path: Path) -> tuple[Graph, str, str, Image.Image]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict) or document.get("format_version") != 1:
        raise ValueError("Непідтримуваний формат файла графа.")
    graph_data = document.get("graph")
    image_data = document.get("background_image")
    if not isinstance(graph_data, dict) or not isinstance(image_data, dict):
        raise ValueError("Файл має містити граф і фонове зображення.")
    encoded_image = image_data.get("data")
    mime_type = image_data.get("mime_type", "image/jpeg")
    if not isinstance(encoded_image, str) or not isinstance(mime_type, str):
        raise ValueError("У файлі відсутні дані фонового зображення.")
    image_bytes = base64.b64decode(encoded_image, validate=True)
    with Image.open(BytesIO(image_bytes)) as source_image:
        background = source_image.convert("RGBA")
    return Graph.from_dict(graph_data), encoded_image, mime_type, background


def write_graph_document(path: Path, graph: Graph, image_data: str, mime_type: str) -> None:
    document = {
        "format_version": 1,
        "graph": graph.to_dict(),
        "background_image": {"mime_type": mime_type, "data": image_data},
    }
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")


class DijkstraApplication(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Лабораторна робота №5 | Алгоритм Дейкстри")
        self.geometry("1480x920")
        self.minsize(1100, 700)
        self.configure(fg_color=COLORS["background"])
        self.graph_file = DEFAULT_GRAPH_PATH
        (
            self.graph,
            self.background_image_data,
            self.background_image_mime_type,
            self.background_source,
        ) = read_graph_document(self.graph_file)
        self.background_photo: ImageTk.PhotoImage | None = None
        self.background_photo_size: tuple[int, int] | None = None
        self.runner: DijkstraRunner | None = None
        self.last_result: DijkstraResult | None = None
        self.experiments: list[dict[str, str]] = []
        self.animation_job: str | None = None
        self.selected_vertices: list[int] = []
        self.zoom_factor = 1.0
        self.zoom_offset_x = 0.0
        self.zoom_offset_y = 0.0
        self.pan_start: tuple[float, float, float, float] | None = None
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
        create_label(self.sidebar, "Лабораторна робота №5", 11, color=COLORS["text_secondary"]).pack(padx=25, anchor="w")
        self.lab_button = create_button(self.sidebar, "Лабораторна", self.show_lab, width=180)
        self.lab_button.pack(padx=25, pady=(40, 10))
        self.results_button = create_button(self.sidebar, "Результати", self.show_results, width=180, style="secondary")
        self.results_button.pack(padx=25, pady=10)
        self.theory_button = create_button(self.sidebar, "Теорія Дейкстри", self.show_theory, width=180, style="secondary")
        self.theory_button.pack(padx=25, pady=10)
        self.main = ctk.CTkFrame(self, fg_color="transparent")
        self.main.pack(side="left", fill="both", expand=True, padx=25, pady=25)

    def clear_main(self) -> None:
        if self.animation_job:
            self.after_cancel(self.animation_job)
            self.animation_job = None
        for key in ("a", "A", "g", "G", "f", "F", "d", "D"):
            self.unbind_all(f"<KeyPress-{key}>")
        for widget in self.main.winfo_children():
            widget.destroy()

    def show_lab(self) -> None:
        self.clear_main()
        create_title(self.main, "Лабораторна робота №5").pack(anchor="w")
        create_label(
            self.main,
            "Пошук найкоротшого шляху на зваженому графі: автошляхи України",
            13,
            color=COLORS["text_secondary"],
        ).pack(anchor="w", pady=(5, 15))
        content = ctk.CTkFrame(self.main, fg_color="transparent")
        content.pack(fill="both", expand=True)
        self.build_controls(content)
        self.build_visualization(content)
        self.refresh_controls()
        self.draw_graph()

    def build_controls(self, parent: ctk.CTkFrame) -> None:
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

        create_label(left, "Параметри маршруту", 18, True).pack(padx=18, pady=(18, 12), anchor="w")
        self.add_field(left, "Початкове місто")
        self.start_var = ctk.StringVar(value="Львів")
        self.start_combo = create_combobox(left, [], 275)
        self.start_combo.configure(variable=self.start_var)
        self.start_combo.pack(padx=18, pady=(3, 8))
        self.add_field(left, "Цільове місто")
        self.target_var = ctk.StringVar(value="Севастополь")
        self.target_combo = create_combobox(left, [], 275)
        self.target_combo.configure(variable=self.target_var)
        self.target_combo.pack(padx=18, pady=(3, 8))
        create_button(left, "Поміняти початок ↔ ціль", self.reverse_search, width=275, style="secondary").pack(padx=18, pady=2)

        self.add_field(left, "Швидкість анімації")
        self.speed_var = ctk.StringVar(value="250 мс")
        self.speed_combo = create_combobox(left, ["100 мс", "250 мс", "500 мс", "1000 мс"], 275)
        self.speed_combo.configure(variable=self.speed_var)
        self.speed_combo.pack(padx=18, pady=(3, 10))
        buttons = ctk.CTkFrame(left, fg_color="transparent")
        buttons.pack(fill="x", padx=18)
        create_button(buttons, "Запустити", self.run_search, width=132, style="success").pack(side="left", padx=(0, 4))
        create_button(buttons, "Крок", self.step_search, width=132).pack(side="left", padx=(4, 0))
        create_button(left, "Побудувати шлях без анімації", self.run_search_instant, width=275, style="success").pack(padx=18, pady=(6, 5))
        create_button(left, "Очистити пошук", self.reset_search, width=275, style="secondary").pack(padx=18, pady=5)
        create_button(left, "Детальний звіт про маршрут", self.show_route_report, width=275, style="secondary").pack(padx=18, pady=(5, 8))

        create_label(left, "Редагування графа", 15, True).pack(padx=18, pady=(12, 7), anchor="w")
        self.add_field(left, "Назва міста")
        self.city_name_entry = create_entry(left, "Назва міста", 275)
        self.city_name_entry.pack(padx=18, pady=(3, 5))
        coordinate_row = ctk.CTkFrame(left, fg_color="transparent")
        coordinate_row.pack(fill="x", padx=16, pady=2)
        self.vertex_x_entry = create_entry(coordinate_row, "X", 130)
        self.vertex_y_entry = create_entry(coordinate_row, "Y", 130)
        self.vertex_x_entry.pack(side="left", fill="x", expand=True, padx=2)
        self.vertex_y_entry.pack(side="left", fill="x", expand=True, padx=2)
        vertex_buttons = ctk.CTkFrame(left, fg_color="transparent")
        vertex_buttons.pack(fill="x", padx=16, pady=3)
        create_button(vertex_buttons, "Додати місто", self.add_vertex, width=132).pack(side="left", padx=2)
        create_button(vertex_buttons, "Видалити місто", self.remove_vertex, width=132, style="danger").pack(side="left", padx=2)

        self.add_field(left, "Кінцеві міста дороги")
        edge_row = ctk.CTkFrame(left, fg_color="transparent")
        edge_row.pack(fill="x", padx=16, pady=(3, 2))
        self.edge_a_var = ctk.StringVar()
        self.edge_b_var = ctk.StringVar()
        self.edge_a_combo = create_combobox(edge_row, [], 130)
        self.edge_b_combo = create_combobox(edge_row, [], 130)
        self.edge_a_combo.configure(variable=self.edge_a_var)
        self.edge_b_combo.configure(variable=self.edge_b_var)
        self.edge_a_combo.pack(side="left", fill="x", expand=True, padx=2)
        self.edge_b_combo.pack(side="left", fill="x", expand=True, padx=2)
        self.directed_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            left,
            text="Орієнтоване ребро",
            variable=self.directed_var,
            font=("Segoe UI", 12),
        ).pack(padx=18, pady=4, anchor="w")
        edge_buttons = ctk.CTkFrame(left, fg_color="transparent")
        edge_buttons.pack(fill="x", padx=16, pady=3)
        create_button(edge_buttons, "Додати ребро", self.add_edge, width=132).pack(side="left", padx=2)
        create_button(edge_buttons, "Видалити ребро", self.remove_edge, width=132, style="danger").pack(side="left", padx=2)
        create_button(left, "Змінити напрям ребра", self.convert_edge, width=275, style="secondary").pack(padx=18, pady=3)
        file_buttons = ctk.CTkFrame(left, fg_color="transparent")
        file_buttons.pack(fill="x", padx=16, pady=3)
        create_button(file_buttons, "Завантажити JSON", self.load_graph, width=132, style="secondary").pack(side="left", padx=2)
        create_button(file_buttons, "Зберегти JSON", self.save_graph, width=132, style="secondary").pack(side="left", padx=2)
        create_button(left, "Відновити граф", self.reset_graph, width=275, style="secondary").pack(padx=18, pady=3)
        self.status_label = create_label(left, "Готово", 11, color=COLORS["text_secondary"])
        self.status_label.pack(padx=18, pady=(10, 12), anchor="w")

    @staticmethod
    def add_field(parent: ctk.CTkFrame, text: str) -> None:
        create_label(parent, text, 12, color=COLORS["text_secondary"]).pack(padx=18, anchor="w")

    def build_visualization(self, parent: ctk.CTkFrame) -> None:
        right = create_card(parent)
        right.pack(side="left", fill="both", expand=True)
        header = ctk.CTkFrame(right, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(15, 6))
        create_label(header, "Візуалізація алгоритму Дейкстри: Автошляхи України", 18, True).pack(side="left")
        self.graph_stats = create_label(header, "", 12, color=COLORS["text_secondary"])
        self.graph_stats.pack(side="right")
        self.canvas = tk.Canvas(right, bg=COLORS["background"], highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=18, pady=(0, 5))
        self.canvas.bind("<Configure>", lambda _event: self.draw_graph())
        self.canvas.bind("<Button-1>", self.canvas_press)
        self.canvas.bind("<B1-Motion>", self.canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.canvas_release)
        self.canvas.bind("<ButtonPress-2>", self.canvas_pan_start)
        self.canvas.bind("<B2-Motion>", self.canvas_pan)
        self.canvas.bind("<ButtonRelease-2>", self.canvas_pan_end)
        self.canvas.bind("<MouseWheel>", self.canvas_mousewheel)
        self.canvas.bind("<Button-4>", lambda _event: self.adjust_zoom(1.1))
        self.canvas.bind("<Button-5>", lambda _event: self.adjust_zoom(1 / 1.1))
        zoom_controls = ctk.CTkFrame(right, fg_color="transparent")
        zoom_controls.pack(fill="x", padx=18, pady=(0, 5))
        create_label(zoom_controls, "Масштаб", 11, color=COLORS["text_secondary"]).pack(side="left", padx=(0, 8))
        create_button(zoom_controls, "−", lambda: self.adjust_zoom(1 / 1.2), width=36, height=30).pack(side="left", padx=2)
        self.zoom_label = create_label(zoom_controls, "100%", 11)
        self.zoom_label.pack(side="left", padx=8)
        create_button(zoom_controls, "+", lambda: self.adjust_zoom(1.2), width=36, height=30).pack(side="left", padx=2)
        create_button(zoom_controls, "Скинути масштаб", self.reset_zoom, width=140, height=30, style="secondary").pack(side="left", padx=8)
        self.bind_all("<KeyPress-a>", self.add_keyboard_vertex)
        self.bind_all("<KeyPress-A>", self.add_keyboard_vertex)
        self.bind_all("<KeyPress-g>", self.delete_selected_items)
        self.bind_all("<KeyPress-G>", self.delete_selected_items)
        self.bind_all("<KeyPress-f>", self.make_undirected_selected_edge)
        self.bind_all("<KeyPress-F>", self.make_undirected_selected_edge)
        self.bind_all("<KeyPress-d>", self.make_directed_selected_edge)
        self.bind_all("<KeyPress-D>", self.make_directed_selected_edge)
        create_label(
            right,
            "Середня кнопка: переміщення | Shift + клік: вибір міст | клік: початок | Ctrl + клік: ціль | A: додати | G: видалити | F: неорієнтоване | D: орієнтоване",
            10,
            color=COLORS["text_secondary"],
        ).pack(anchor="w", padx=18, pady=(0, 8))
        summary_frame = ctk.CTkFrame(right, fg_color="transparent")
        summary_frame.pack(fill="x", padx=18, pady=(0, 15))
        self.result_label = tk.Text(
            summary_frame,
            height=3,
            wrap="word",
            font=("Segoe UI", 10),
            bg=COLORS["card"],
            fg=COLORS["text"],
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            padx=8,
            pady=5,
            state="disabled",
        )
        self.result_scrollbar = ttk.Scrollbar(summary_frame, orient="vertical", command=self.result_label.yview)
        self.result_label.configure(yscrollcommand=self.result_scrollbar.set)
        self.result_label.pack(side="left", fill="both", expand=True)
        self.result_scrollbar.pack(side="right", fill="y")
        self.set_result_text("Шлях: — | Відстань: —\nВідкрито: 0 | Розкрито: 0 | Час: 0 мс\nНаступні: —")

    def refresh_controls(self) -> None:
        city_names = [vertex.name for vertex in sorted(self.graph.vertices.values(), key=lambda item: item.name)]
        self.start_combo.configure(values=city_names)
        self.target_combo.configure(values=city_names)
        self.edge_a_combo.configure(values=city_names)
        self.edge_b_combo.configure(values=city_names)
        if city_names:
            if self.start_var.get() not in city_names:
                self.start_var.set(city_names[0])
            if self.target_var.get() not in city_names:
                self.target_var.set(city_names[-1])
            if self.edge_a_var.get() not in city_names:
                self.edge_a_var.set(self.start_var.get())
            if self.edge_b_var.get() not in city_names:
                self.edge_b_var.set(self.target_var.get())
        self.graph_stats.configure(text=f"Міст: {len(self.graph.vertices)}   Доріг: {self.graph.edge_count}")

    def selected_city_ids(self) -> tuple[int, int]:
        start = self.graph.get_vertex_by_name(self.start_var.get())
        target = self.graph.get_vertex_by_name(self.target_var.get())
        if start is None or target is None:
            raise ValueError("Оберіть початкове та цільове міста.")
        return start.id, target.id

    def create_runner(self) -> DijkstraRunner:
        start, target = self.selected_city_ids()
        return DijkstraRunner(self.graph, start, target)

    def run_search(self) -> None:
        if self.animation_job:
            self.after_cancel(self.animation_job)
            self.animation_job = None
        try:
            self.runner = self.create_runner()
        except (ValueError, GraphError) as error:
            messagebox.showerror("Помилка пошуку", str(error))
            return
        self.last_result = None
        self.animate_step()

    def run_search_instant(self) -> None:
        if self.animation_job:
            self.after_cancel(self.animation_job)
            self.animation_job = None
        try:
            self.runner = self.create_runner()
            self.runner.run()
        except (ValueError, GraphError) as error:
            messagebox.showerror("Помилка пошуку", str(error))
            return
        self.finish_search()

    def animate_step(self) -> None:
        if self.runner is None:
            return
        active = self.runner.step()
        self.update_search_summary()
        self.draw_graph()
        if active:
            self.animation_job = self.after(int(self.speed_var.get().split()[0]), self.animate_step)
        else:
            self.animation_job = None
            self.finish_search()

    def step_search(self) -> None:
        if self.animation_job:
            self.after_cancel(self.animation_job)
            self.animation_job = None
        try:
            if self.runner is None or self.runner.finished:
                self.runner = self.create_runner()
                self.last_result = None
            active = self.runner.step()
            self.update_search_summary()
            self.draw_graph()
            if not active:
                self.finish_search()
        except (ValueError, GraphError) as error:
            messagebox.showerror("Помилка пошуку", str(error))

    def finish_search(self) -> None:
        if self.runner is None:
            return
        self.last_result = self.runner.result()
        result = self.last_result
        self.update_search_summary()
        self.status_label.configure(
            text="Пошук завершено" if result.found else "Маршрут не знайдено",
            text_color=COLORS["success"] if result.found else COLORS["danger"],
        )
        self.draw_graph()

    def reset_search(self) -> None:
        if self.animation_job:
            self.after_cancel(self.animation_job)
            self.animation_job = None
        self.runner = None
        self.last_result = None
        if hasattr(self, "status_label"):
            self.status_label.configure(text="Пошук очищено", text_color=COLORS["text_secondary"])
        if hasattr(self, "result_label") and self.result_label.winfo_exists():
            self.set_result_text("Шлях: — | Відстань: —\nВідкрито: 0 | Розкрито: 0 | Час: 0 мс\nНаступні: —")
            self.draw_graph()

    def set_result_text(self, text: str) -> None:
        self.result_label.configure(state="normal")
        self.result_label.delete("1.0", "end")
        self.result_label.insert("1.0", text)
        self.result_label.configure(state="disabled")
        self.result_label.yview_moveto(0)

    def update_search_summary(self) -> None:
        if self.runner is None:
            self.set_result_text("Шлях: — | Відстань: —\nВідкрито: 0 | Розкрито: 0 | Час: 0 мс\nНаступні: —")
            return

        runner = self.runner
        result = runner.result() if runner.finished else None
        if result is not None:
            route = " → ".join(result.path_names) if result.found else "не знайдено"
            distance = f"{result.total_distance:g} км" if result.found else "—"
            elapsed_ms = result.elapsed_time * 1000
        else:
            route = "пошук триває"
            target_distance = runner.distances.get(runner.target, float("inf"))
            distance = f"{target_distance:g} км" if target_distance != float("inf") else "—"
            elapsed_ms = (perf_counter() - runner.started_at) * 1000

        next_vertices = {
            vertex_id: cost
            for cost, vertex_id in runner.priority_queue
            if vertex_id not in runner.settled and cost == runner.distances[vertex_id]
        }
        next_cities = sorted(
            next_vertices.items(),
            key=lambda item: (item[1], self.graph.vertices[item[0]].name),
        )
        next_text = ", ".join(
            f"{self.graph.vertices[vertex_id].name} (d={cost:g} км)"
            for vertex_id, cost in next_cities
        ) or "—"
        self.set_result_text(
            f"Шлях: {route} | Відстань: {distance}\n"
            f"Відкрито: {len(runner.visited)} | Розкрито: {len(runner.expanded)} | "
            f"Час: {elapsed_ms:.3f} мс\n"
            f"Наступні: {next_text}"
        )

    def reverse_search(self) -> None:
        start, target = self.start_var.get(), self.target_var.get()
        self.start_var.set(target)
        self.target_var.set(start)
        self.reset_search()

    def canvas_point(self, vertex: Vertex) -> tuple[float, float]:
        width, height = max(self.canvas.winfo_width(), 500), max(self.canvas.winfo_height(), 400)
        scale_x = (width - 50) / 1230
        scale_y = (height - 50) / 460
        center_x, center_y = width / 2, height / 2
        base_x, base_y = 25 + vertex.x * scale_x, 25 + vertex.y * scale_y
        return (
            center_x + (base_x - center_x) * self.zoom_factor + self.zoom_offset_x,
            center_y + (base_y - center_y) * self.zoom_factor + self.zoom_offset_y,
        )

    def adjust_zoom(self, factor: float, anchor_x: float | None = None, anchor_y: float | None = None) -> None:
        old_zoom = self.zoom_factor
        new_zoom = max(0.5, min(4.0, old_zoom * factor))
        if new_zoom == old_zoom:
            return
        width, height = max(self.canvas.winfo_width(), 500), max(self.canvas.winfo_height(), 400)
        center_x, center_y = width / 2, height / 2
        anchor_x = center_x if anchor_x is None else anchor_x
        anchor_y = center_y if anchor_y is None else anchor_y
        self.zoom_offset_x = anchor_x - center_x - (anchor_x - center_x - self.zoom_offset_x) * new_zoom / old_zoom
        self.zoom_offset_y = anchor_y - center_y - (anchor_y - center_y - self.zoom_offset_y) * new_zoom / old_zoom
        self.zoom_factor = new_zoom
        self.zoom_label.configure(text=f"{round(new_zoom * 100)}%")
        self.background_photo_size = None
        self.draw_graph()

    def canvas_mousewheel(self, event: tk.Event) -> str:
        factor = 1.1 if event.delta > 0 else 1 / 1.1
        self.adjust_zoom(factor, event.x, event.y)
        return "break"

    def reset_zoom(self) -> None:
        self.zoom_factor = 1.0
        self.zoom_offset_x = 0.0
        self.zoom_offset_y = 0.0
        if hasattr(self, "zoom_label") and self.zoom_label.winfo_exists():
            self.zoom_label.configure(text="100%")
        self.background_photo_size = None
        self.draw_graph()

    def canvas_pan_start(self, event: tk.Event) -> str:
        self.pan_start = (event.x, event.y, self.zoom_offset_x, self.zoom_offset_y)
        return "break"

    def canvas_pan(self, event: tk.Event) -> str:
        if self.pan_start is None:
            return "break"
        start_x, start_y, offset_x, offset_y = self.pan_start
        self.zoom_offset_x = offset_x + event.x - start_x
        self.zoom_offset_y = offset_y + event.y - start_y
        self.draw_graph()
        return "break"

    def canvas_pan_end(self, _event: tk.Event) -> str:
        self.pan_start = None
        return "break"

    def draw_graph(self) -> None:
        if not hasattr(self, "canvas") or not self.canvas.winfo_exists():
            return
        self.canvas.delete("all")
        width, height = max(self.canvas.winfo_width(), 500), max(self.canvas.winfo_height(), 400)
        scale_x = (width - 50) / 1230
        scale_y = (height - 50) / 460
        image_size = (
            max(round(1230 * scale_x * self.zoom_factor), 1),
            max(round(460 * scale_y * self.zoom_factor), 1),
        )
        if image_size != self.background_photo_size:
            resized_background = self.background_source.resize(image_size, Image.Resampling.LANCZOS)
            self.background_photo = ImageTk.PhotoImage(resized_background)
            self.background_photo_size = image_size
        center_x, center_y = width / 2, height / 2
        image_x = center_x + (25 - center_x) * self.zoom_factor + self.zoom_offset_x
        image_y = center_y + (25 - center_y) * self.zoom_factor + self.zoom_offset_y
        self.canvas.create_image(image_x, image_y, image=self.background_photo, anchor="nw", tags=("background",))
        path = set(self.last_result.path if self.last_result else [])
        path_edges: set[tuple[int, int]] = set()
        if self.last_result:
            for source, target in zip(self.last_result.path, self.last_result.path[1:]):
                path_edges.add((source, target))
                path_edges.add((target, source))
        settled = self.runner.settled if self.runner else set()
        queued = {
            vertex_id for cost, vertex_id in (self.runner.priority_queue if self.runner else [])
            if self.runner and cost == self.runner.distances[vertex_id] and vertex_id not in settled
        }
        current = self.runner.current_vertex if self.runner else None

        for edge in self.graph.edges:
            source = self.graph.vertices[edge.source]
            target = self.graph.vertices[edge.target]
            first, second = self.canvas_point(source), self.canvas_point(target)
            on_path = (edge.source, edge.target) in path_edges
            color = COLORS["primary_hover"] if on_path else "#000000"
            line_start, line_end = first, second
            if edge.directed:
                dx, dy = second[0] - first[0], second[1] - first[1]
                length = max((dx * dx + dy * dy) ** 0.5, 1)
                unit_x, unit_y = dx / length, dy / length
                line_start = (first[0] + unit_x * 10, first[1] + unit_y * 10)
                line_end = (second[0] - unit_x * 15, second[1] - unit_y * 15)
            edge_width = 3 if on_path else 1.7
            arrow = "last" if edge.directed else None
            arrow_shape = (12, 14, 5)
            self.canvas.create_line(
                *line_start,
                *line_end,
                fill="#ffffff",
                width=edge_width + 3,
                arrow=arrow,
                arrowshape=(15, 17, 7),
            )
            self.canvas.create_line(
                *line_start,
                *line_end,
                fill=color,
                width=edge_width,
                arrow=arrow,
                arrowshape=arrow_shape,
            )
            middle_x, middle_y = (first[0] + second[0]) / 2, (first[1] + second[1]) / 2
            self.canvas.create_rectangle(middle_x - 23, middle_y - 9, middle_x + 23, middle_y + 9, fill=COLORS["background"], outline="")
            self.canvas.create_text(middle_x, middle_y, text=f"{edge.weight:g}", fill=COLORS["text"], font=("Segoe UI", 8))

        start_city = self.graph.get_vertex_by_name(self.start_var.get())
        target_city = self.graph.get_vertex_by_name(self.target_var.get())
        vertex_labels: list[tuple[str, float, float, tuple[str, int, str]]] = []
        for vertex_id, vertex in self.graph.vertices.items():
            x, y = self.canvas_point(vertex)
            if vertex_id in path:
                fill, outline = COLORS["primary"], COLORS["primary_hover"]
            elif vertex_id == current:
                fill, outline = "#fbbf24", "#d97706"
            elif vertex_id in settled:
                fill, outline = "#86efac", COLORS["success"]
            elif vertex_id in queued:
                fill, outline = "#fef3c7", "#f59e0b"
            else:
                fill, outline = COLORS["card"], COLORS["text_secondary"]
            if start_city and vertex_id == start_city.id:
                outline = "#2563eb"
            if target_city and vertex_id == target_city.id:
                outline = COLORS["danger"]
            if vertex_id in self.selected_vertices:
                outline = "#7e22ce"
            radius = 10
            halo_radius = radius + 1
            self.canvas.create_oval(
                x - halo_radius,
                y - halo_radius,
                x + halo_radius,
                y + halo_radius,
                fill="#ffffff",
                outline="#ffffff",
                width=2,
            )
            self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=fill, outline=outline, width=2)
            known_distance = self.runner.distances.get(vertex_id, float("inf")) if self.runner else float("inf")
            distance_label = f"d={known_distance:g}" if known_distance != float("inf") else "d=∞"
            vertex_labels.append((distance_label, x, y - 17, ("Segoe UI", 8, "bold")))
            vertex_labels.append((vertex.name, x, y + 24, ("Segoe UI", 9, "bold")))

        vertex_label_items: list[tuple[int, tuple[int, int, int, int]]] = []
        for text, x, y, font in vertex_labels:
            label = self.canvas.create_text(x, y, text=text, fill=COLORS["text"], font=font)
            bounds = self.canvas.bbox(label)
            if bounds is not None:
                vertex_label_items.append((label, bounds))

        for label, bounds in vertex_label_items:
            left, top, right, bottom = bounds
            background = self.canvas.create_rectangle(
                left - 3,
                top - 2,
                right + 3,
                bottom + 2,
                fill="#ffffff",
                outline="#ffffff",
            )
            self.canvas.tag_lower(background, label)

        for label, _bounds in vertex_label_items:
            self.canvas.tag_raise(label)

    def nearest_vertex(self, event: tk.Event) -> tuple[Vertex | None, float, float, float]:
        if not self.graph.vertices:
            return None, 0.0, 0.0, float("inf")
        nearest = min(
            self.graph.vertices.values(),
            key=lambda vertex: (self.canvas_point(vertex)[0] - event.x) ** 2 + (self.canvas_point(vertex)[1] - event.y) ** 2,
        )
        x, y = self.canvas_point(nearest)
        distance = ((x - event.x) ** 2 + (y - event.y) ** 2) ** 0.5
        return nearest, x, y, distance

    def canvas_press(self, event: tk.Event) -> None:
        vertex, x, y, distance = self.nearest_vertex(event)
        if vertex is None or distance > 22:
            return
        if event.state & 0x0001:
            self.select_vertex(vertex.id)
            return
        if event.state & 0x0004:
            self.target_var.set(vertex.name)
            self.reset_search()
            return
        self.drag_vertex_id = vertex.id
        self.drag_moved = False
        self.drag_offset = (event.x - x, event.y - y)

    def canvas_drag(self, event: tk.Event) -> None:
        if self.drag_vertex_id is None:
            return
        width, height = max(self.canvas.winfo_width(), 500), max(self.canvas.winfo_height(), 400)
        scale_x, scale_y = (width - 50) / 1230, (height - 50) / 460
        center_x, center_y = width / 2, height / 2
        canvas_x = (event.x - self.drag_offset[0] - center_x - self.zoom_offset_x) / self.zoom_factor + center_x
        canvas_y = (event.y - self.drag_offset[1] - center_y - self.zoom_offset_y) / self.zoom_factor + center_y
        x = max(50.0, min(1180.0, (canvas_x - 25) / scale_x))
        y = max(50.0, min(430.0, (canvas_y - 25) / scale_y))
        vertex = self.graph.vertices[self.drag_vertex_id]
        self.graph.vertices[self.drag_vertex_id] = Vertex(vertex.id, vertex.name, x, y)
        self.drag_moved = True
        self.draw_graph()

    def canvas_release(self, _event: tk.Event) -> None:
        if self.drag_vertex_id is None:
            return
        vertex_id, moved = self.drag_vertex_id, self.drag_moved
        self.drag_vertex_id = None
        self.drag_moved = False
        if moved:
            self.reset_search()
            self.status_label.configure(text="Місто переміщено", text_color=COLORS["success"])
        else:
            self.start_var.set(self.graph.vertices[vertex_id].name)
            self.reset_search()

    def select_vertex(self, vertex_id: int) -> None:
        if vertex_id in self.selected_vertices:
            self.selected_vertices.remove(vertex_id)
        else:
            if len(self.selected_vertices) == 2:
                self.selected_vertices.pop(0)
            self.selected_vertices.append(vertex_id)
        if self.selected_vertices:
            first = self.graph.vertices[self.selected_vertices[0]]
            self.edge_a_var.set(first.name)
        if len(self.selected_vertices) == 2:
            second = self.graph.vertices[self.selected_vertices[1]]
            self.edge_b_var.set(second.name)
            self.status_label.configure(text="Вибрано два міста для операції з дорогою", text_color="#7e22ce")
        elif self.selected_vertices:
            self.status_label.configure(text="Місто вибрано", text_color="#7e22ce")
        else:
            self.status_label.configure(text="Вибір очищено", text_color=COLORS["text_secondary"])
        self.draw_graph()

    def selected_edge_ids(self) -> tuple[int, int] | None:
        if len(self.selected_vertices) != 2:
            messagebox.showinfo("Вибір міст", "Виберіть два міста за допомогою Shift + клацання.")
            return None
        return self.selected_vertices[0], self.selected_vertices[1]

    def set_selected_edge_direction(self, directed: bool) -> None:
        selected = self.selected_edge_ids()
        if selected is None:
            return
        try:
            if self.graph.has_edge(*selected):
                self.graph.convert_edge(*selected, directed)
                action = "Напрям дороги змінено"
            else:
                weight = simpledialog.askfloat(
                    "Додати дорогу",
                    "Відстань між містами, км:",
                    parent=self,
                    minvalue=0,
                )
                if weight is None:
                    return
                self.graph.add_edge(*selected, weight, directed)
                action = "Дорогу додано"
            self.directed_var.set(directed)
            self.refresh_after_edit(clear_selection=False)
            self.status_label.configure(text=action, text_color=COLORS["success"])
        except GraphError as error:
            messagebox.showerror("Дорога", str(error))

    def make_undirected_selected_edge(self, _event: tk.Event | None = None) -> str:
        self.set_selected_edge_direction(False)
        return "break"

    def make_directed_selected_edge(self, _event: tk.Event | None = None) -> str:
        self.set_selected_edge_direction(True)
        return "break"

    def delete_selected_items(self, _event: tk.Event | None = None) -> None:
        if len(self.selected_vertices) == 1:
            self.graph.remove_vertex(self.selected_vertices[0])
            self.refresh_after_edit()
        elif len(self.selected_vertices) == 2:
            try:
                self.graph.remove_edge(*self.selected_vertices)
                self.refresh_after_edit()
            except GraphError as error:
                messagebox.showerror("Видалення дороги", str(error))
        else:
            self.status_label.configure(text="Виберіть місто або два міста", text_color=COLORS["danger"])

    def add_keyboard_vertex(self, _event: tk.Event | None = None) -> None:
        name = simpledialog.askstring("Додати місто", "Назва міста:", parent=self)
        if not name:
            return
        x = simpledialog.askfloat("Додати місто", "Координата X (50–1180):", parent=self, minvalue=50, maxvalue=1180)
        y = simpledialog.askfloat("Додати місто", "Координата Y (50–430):", parent=self, minvalue=50, maxvalue=430)
        if x is None or y is None:
            return
        self.create_city(name, x, y)

    def add_vertex(self) -> None:
        try:
            name = self.city_name_entry.get().strip()
            x, y = float(self.vertex_x_entry.get()), float(self.vertex_y_entry.get())
            if not 50 <= x <= 1180 or not 50 <= y <= 430:
                raise ValueError("Координати мають бути в межах X: 50–1180, Y: 50–430.")
            self.create_city(name, x, y)
        except (ValueError, GraphError) as error:
            messagebox.showerror("Місто", str(error))

    def create_city(self, name: str, x: float, y: float) -> None:
        try:
            next_id = max(self.graph.vertices, default=0) + 1
            self.graph.add_vertex(Vertex(next_id, name.strip(), x, y))
            self.city_name_entry.delete(0, "end")
            self.refresh_after_edit()
        except GraphError as error:
            messagebox.showerror("Місто", str(error))

    def remove_vertex(self) -> None:
        vertex = self.graph.get_vertex_by_name(self.city_name_entry.get().strip())
        if vertex is None:
            messagebox.showerror("Місто", "Вкажіть назву наявного міста.")
            return
        self.graph.remove_vertex(vertex.id)
        self.refresh_after_edit()

    def edge_endpoints(self) -> tuple[int, int]:
        source = self.graph.get_vertex_by_name(self.edge_a_var.get())
        target = self.graph.get_vertex_by_name(self.edge_b_var.get())
        if source is None or target is None:
            raise ValueError("Оберіть обидва кінцеві міста дороги.")
        return source.id, target.id

    def add_edge(self) -> None:
        try:
            source, target = self.edge_endpoints()
            weight = simpledialog.askfloat(
                "Додати дорогу",
                "Відстань між містами, км:",
                parent=self,
                minvalue=0,
            )
            if weight is None:
                return
            self.graph.add_edge(source, target, weight, self.directed_var.get())
            self.refresh_after_edit()
        except (ValueError, GraphError) as error:
            messagebox.showerror("Дорога", str(error))

    def remove_edge(self) -> None:
        try:
            self.graph.remove_edge(*self.edge_endpoints())
            self.refresh_after_edit()
        except (ValueError, GraphError) as error:
            messagebox.showerror("Дорога", str(error))

    def convert_edge(self) -> None:
        try:
            self.graph.convert_edge(*self.edge_endpoints(), self.directed_var.get())
            self.refresh_after_edit()
        except (ValueError, GraphError) as error:
            messagebox.showerror("Дорога", str(error))

    def refresh_after_edit(self, clear_selection: bool = True) -> None:
        self.reset_search()
        if clear_selection:
            self.selected_vertices.clear()
        self.refresh_controls()
        self.draw_graph()

    def reset_graph(self) -> None:
        try:
            (
                self.graph,
                self.background_image_data,
                self.background_image_mime_type,
                self.background_source,
            ) = read_graph_document(DEFAULT_GRAPH_PATH)
            self.graph_file = DEFAULT_GRAPH_PATH
            self.background_photo_size = None
            self.start_var.set("Львів")
            self.target_var.set("Севастополь")
            self.selected_vertices.clear()
            self.refresh_after_edit()
            self.status_label.configure(text="Початкову мережу автошляхів відновлено", text_color=COLORS["success"])
        except (OSError, ValueError, KeyError, TypeError, GraphError) as error:
            messagebox.showerror("Відновлення графа", str(error))

    def load_graph(self) -> None:
        file_path = filedialog.askopenfilename(
            parent=self,
            title="Завантажити граф із JSON",
            initialdir=self.graph_file.parent,
            filetypes=[("Файли JSON", "*.json")],
        )
        if not file_path:
            return
        try:
            path = Path(file_path)
            graph, image_data, mime_type, background = read_graph_document(path)
            self.graph = graph
            self.background_image_data = image_data
            self.background_image_mime_type = mime_type
            self.background_source = background
            self.background_photo_size = None
            self.graph_file = path
            self.selected_vertices.clear()
            self.refresh_after_edit()
            self.status_label.configure(text="Граф і зображення завантажено", text_color=COLORS["success"])
        except (OSError, ValueError, KeyError, TypeError, GraphError) as error:
            messagebox.showerror("Завантаження графа", str(error))

    def save_graph(self) -> None:
        file_path = filedialog.asksaveasfilename(
            parent=self,
            title="Зберегти граф і зображення",
            initialdir=self.graph_file.parent,
            initialfile=self.graph_file.name,
            defaultextension=".json",
            filetypes=[("Файли JSON", "*.json")],
        )
        if not file_path:
            return
        try:
            path = Path(file_path)
            write_graph_document(path, self.graph, self.background_image_data, self.background_image_mime_type)
            self.graph_file = path
            self.status_label.configure(text="Граф і зображення збережено", text_color=COLORS["success"])
        except OSError as error:
            messagebox.showerror("Збереження графа", str(error))

    def show_route_report(self) -> None:
        if self.last_result is None:
            messagebox.showinfo("Звіт про маршрут", "Спочатку виконайте пошук маршруту.")
            return
        result = self.last_result
        popup = ctk.CTkToplevel(self)
        popup.title("Детальний звіт про маршрут")
        popup.geometry("680x620")
        popup.minsize(520, 420)
        popup.transient(self)
        create_title(popup, "Детальний звіт про маршрут").pack(anchor="w", padx=22, pady=(20, 12))
        report = ctk.CTkTextbox(popup, wrap="word", font=("Segoe UI", 13))
        report.pack(fill="both", expand=True, padx=22, pady=(0, 20))
        lines = ["Відвідані міста:"]
        lines.extend(
            f"{index}. {self.graph.vertices[vertex_id].name}"
            for index, vertex_id in enumerate(result.visited_vertices, start=1)
            if vertex_id in self.graph.vertices
        )
        lines.extend(["", "Сегменти найкоротшого маршруту:"])
        if result.found:
            for source, target in zip(result.path, result.path[1:]):
                edge = next(
                    (
                        item for item in self.graph.edges
                        if (item.source, item.target) == (source, target)
                        or (not item.directed and (item.source, item.target) == (target, source))
                    ),
                    None,
                )
                if edge is not None:
                    lines.append(
                        f"{self.graph.vertices[source].name} → {self.graph.vertices[target].name}: {edge.weight:g} км"
                    )
            lines.append(f"Сума: {result.total_distance:g} км")
        else:
            lines.append("Маршрут не знайдено.")
        report.insert("1.0", "\n".join(lines))
        report.configure(state="disabled")

    def show_results(self) -> None:
        self.clear_main()
        create_title(self.main, "Результати пошуку").pack(anchor="w")
        card = create_card(self.main)
        card.pack(fill="both", expand=True, pady=(15, 0))
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=18, pady=15)
        create_button(top, "Додати поточний результат", self.add_experiment, width=225, style="success").pack(side="left")
        create_button(top, "Очистити таблицю", self.clear_experiments, width=165, style="secondary").pack(side="left", padx=8)
        columns = ("№", "Початок", "Ціль", "Маршрут", "Відстань (км)", "Розкрито", "Ітерацій", "Час")
        table_frame = ctk.CTkFrame(card, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, padx=18, pady=(0, 18))
        table = ttk.Treeview(table_frame, columns=columns, show="headings")
        vertical_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
        horizontal_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=table.xview)
        table.configure(yscrollcommand=vertical_scrollbar.set, xscrollcommand=horizontal_scrollbar.set)
        widths = (45, 110, 110, 330, 115, 85, 80, 100)
        for column, width in zip(columns, widths):
            table.heading(column, text=column)
            table.column(column, width=width, anchor="center")
        table.grid(row=0, column=0, sticky="nsew")
        vertical_scrollbar.grid(row=0, column=1, sticky="ns")
        horizontal_scrollbar.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        for row in self.experiments:
            table.insert("", "end", values=[row[column] for column in columns])
        self.experiment_table = table

    def add_experiment(self) -> None:
        if self.last_result is None:
            messagebox.showinfo("Результати", "Спочатку виконайте пошук маршруту.")
            return
        result = self.last_result
        path_text = " → ".join(result.path_names) if result.found else "не знайдено"
        self.experiments.append(
            {
                "№": str(len(self.experiments) + 1),
                "Початок": self.start_var.get(),
                "Ціль": self.target_var.get(),
                "Маршрут": path_text,
                "Відстань (км)": f"{result.total_distance:g}" if result.found else "—",
                "Розкрито": str(len(result.expanded_vertices)),
                "Ітерацій": str(result.iterations),
                "Час": f"{result.elapsed_time * 1000:.3f} мс",
            }
        )
        self.show_results()

    def clear_experiments(self) -> None:
        self.experiments.clear()
        self.show_results()

    def show_theory(self) -> None:
        self.clear_main()
        create_title(self.main, "Теорія Дейкстри").pack(anchor="w")
        card = create_card(self.main)
        card.pack(fill="both", expand=True, pady=(15, 0))
        theory = (
            "Алгоритм Дейкстри знаходить найкоротші шляхи у зваженому графі з невід’ємними вагами. \n"
            "На відміну від пошуку в ширину (BFS), який вважає всі ребра однаковими та використовує чергу FIFO, \n"
            "Дейкстра зберігає найкращу відому відстань до кожної вершини й обирає наступною вершину \n"
            "з найменшою відстанню за допомогою мінімальної черги пріоритетів.\n\n"
            "Основні кроки:\n"
            "1. Призначити початковій вершині відстань 0, іншим — нескінченність.\n"
            "2. Вилучити з черги вершину з найменшою відстанню.\n"
            "3. Для кожного сусіда перевірити, чи скорочує шлях через поточну вершину відому відстань.\n"
            "4. Додати покращені відстані до черги та повторювати, доки ціль не буде остаточно оброблена.\n\n"
            "Часова складність із бінарною купою: O((V + E) log V).\n"
            "Просторова складність: O(V + E).\n\n"
            "Обмеження: алгоритм коректний лише для невід’ємних ваг. Ребра з від’ємною вагою можуть \n"
            "порушити остаточність уже оброблених відстаней; для таких графів потрібен інший алгоритм, \n"
            "наприклад Беллмана—Форда. У незваженому графі пошук у ширину зазвичай простіший і має \n"
            "складність O(V + E)."
        )
        create_label(card, theory, 15).pack(padx=28, pady=28, anchor="nw")


if __name__ == "__main__":
    application = DijkstraApplication()
    application.mainloop()