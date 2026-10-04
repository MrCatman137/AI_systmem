from __future__ import annotations

import json
import math
import random
import sys
from collections import deque
from pathlib import Path
from tkinter import Canvas, filedialog, messagebox, ttk

import customtkinter as ctk

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from template import COLORS, create_button, create_card, create_combobox, create_entry, create_label, create_title

from lab_4.bfs import WaveResult, WaveRunner
from lab_4.data.default_graph import DEFAULT_START, DEFAULT_TARGET, create_default_maze
from lab_4.graph import Maze, MazeError


class SearchApplication(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Штучний інтелект | Лабораторія №3")
        self.geometry("1400x900")
        self.minsize(1100, 700)
        self.configure(fg_color=COLORS["background"])
        self.maze = create_default_maze()
        self.start = DEFAULT_START
        self.target = DEFAULT_TARGET
        self.operator = "UP_DOWN_LEFT_RIGHT"
        self.search_type = "Однонаправлений"
        self.runner: WaveRunner | None = None
        self.last_result: WaveResult | None = None
        self.experiments: list[dict[str, str | int | float | tuple[int, int]]] = []
        self.animation_job: str | None = None
        self.edit_mode = "wall"
        self.build_shell()
        self.show_lab()

    def build_shell(self) -> None:
        self.sidebar = ctk.CTkFrame(self, width=230, corner_radius=0, fg_color=COLORS["sidebar"])
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        create_label(self.sidebar, "AI Systems", 20, True).pack(padx=25, pady=(30, 5), anchor="w")
        create_label(self.sidebar, "Лабораторна №4", 11, color=COLORS["text_secondary"]).pack(padx=25, anchor="w")
        self.lab_button = create_button(self.sidebar, "Лабораторія", self.show_lab, width=180)
        self.lab_button.pack(padx=25, pady=(40, 10))
        self.results_button = create_button(self.sidebar, "Результати", self.show_results, width=180, style="secondary")
        self.results_button.pack(padx=25, pady=10)
        self.theory_button = create_button(self.sidebar, "Теорія", self.show_theory, width=180, style="secondary")
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
        create_title(self.main, "Лабораторна робота №4").pack(anchor="w")
        create_label(self.main, "Одно- та двонаправлений хвильовий пошук у лабіринті", 13, color=COLORS["text_secondary"]).pack(anchor="w", pady=(5, 15))
        content = ctk.CTkFrame(self.main, fg_color="transparent")
        content.pack(fill="both", expand=True)
        self.build_controls(content)
        self.build_visualization(content)
        self.draw_maze()

    def build_controls(self, parent) -> None:
        card = create_card(parent)
        card.pack(side="left", fill="y", padx=(0, 15))
        card.configure(width=330)
        card.pack_propagate(False)

        left = ctk.CTkScrollableFrame(
            card,
            corner_radius=5,
            fg_color=COLORS["card"],
            scrollbar_button_color=COLORS["secondary"],
            scrollbar_button_hover_color=COLORS["secondary_hover"],
        )
        left.pack(fill="both", expand=True)

        create_label(left, "Параметри лабіринту", 18, True).pack(padx=18, pady=(18, 10), anchor="w")

        self.add_field(left, "Рядки")
        self.rows_entry = create_entry(left, "Рядки", 275)
        self.rows_entry.insert(0, str(self.maze.rows))
        self.rows_entry.pack(padx=18, pady=(0, 8))

        self.add_field(left, "Стовпці")
        self.cols_entry = create_entry(left, "Стовпці", 275)
        self.cols_entry.insert(0, str(self.maze.cols))
        self.cols_entry.pack(padx=18, pady=(0, 8))

        create_button(left, "Застосувати розмір", self.apply_maze_size, width=275).pack(padx=18, pady=(2, 8))

        self.add_field(left, "Оператор переходів")
        self.operator_var = ctk.StringVar(value=self.operator)
        self.operator_combo = create_combobox(left, ["UP_DOWN_LEFT_RIGHT", "DIAGONAL", "COMBINATION"], 275)
        self.operator_combo.configure(variable=self.operator_var)
        self.operator_combo.pack(padx=18, pady=(0, 12))

        self.add_field(left, "Тип пошуку")
        self.search_type_var = ctk.StringVar(value=self.search_type)
        self.search_type_combo = create_combobox(left, ["Однонаправлений", "Двонаправлений"], 275)
        self.search_type_combo.configure(variable=self.search_type_var)
        self.search_type_combo.pack(padx=18, pady=(0, 12))

        self.add_field(left, "Затримка анімації")
        self.speed_var = ctk.StringVar(value="250 ms")
        self.speed_combo = create_combobox(left, ["100 ms", "250 ms", "500 ms", "1000 ms"], 275)
        self.speed_combo.configure(variable=self.speed_var)
        self.speed_combo.pack(padx=18, pady=(0, 12))

        buttons = ctk.CTkFrame(left, fg_color="transparent")
        buttons.pack(fill="x", padx=18, pady=(0, 5))
        create_button(buttons, "Пуск", self.run_search, width=130, style="success").pack(side="left", padx=(0, 4))
        create_button(buttons, "Крок", self.step_search, width=130).pack(side="left", padx=(4, 0))

        create_button(left, "Запустити миттєво", self.run_search_instant, width=275, style="secondary").pack(padx=18, pady=(5, 7))
        create_button(left, "Скинути пошук", self.reset_search, width=275, style="secondary").pack(padx=18, pady=(0, 7))

        self.add_field(left, "Режим редагування")
        self.edit_mode_var = ctk.StringVar(value="стіна")
        self.edit_mode_combo = create_combobox(left, ["стіна", "прохід", "старт", "мета"], 275)
        self.edit_mode_combo.configure(variable=self.edit_mode_var, command=lambda _value: self.set_edit_mode())
        self.edit_mode_combo.pack(padx=18, pady=(0, 8))
        create_button(left, "Поміняти S/T", self.swap_start_target, width=275, style="secondary").pack(padx=18, pady=(0, 8))

        self.add_field(left, "Режим генерації")
        self.generation_var = ctk.StringVar(value="випадково")
        self.generation_combo = create_combobox(left, ["випадково", "місто", "природа", "каньйони"], 275)
        self.generation_combo.configure(variable=self.generation_var)
        self.generation_combo.pack(padx=18, pady=(0, 8))
        create_button(left, "Згенерувати лабіринт", self.generate_maze, width=275, style="success").pack(padx=18, pady=(0, 10))

        create_button(left, "Стандартний лабіринт", self.load_default_maze, width=275, style="secondary").pack(padx=18, pady=(0, 10))
        create_button(left, "Очистити лабіринт", self.clear_maze, width=275, style="danger").pack(padx=18, pady=(0, 8))
        create_button(left, "Зберегти лабіринт", self.save_maze, width=275, style="secondary").pack(padx=18, pady=(0, 8))
        create_button(left, "Завантажити лабіринт", self.load_maze, width=275, style="secondary").pack(padx=18, pady=(0, 8))

        self.status_label = create_label(left, "Готово", 11, color=COLORS["text_secondary"])
        self.status_label.pack(padx=18, pady=(10, 5), anchor="w")

    def add_field(self, parent, text: str) -> None:
        create_label(parent, text, 12, color=COLORS["text_secondary"]).pack(padx=18, anchor="w")

    def set_edit_mode(self) -> None:
        self.edit_mode = self.edit_mode_var.get()

    def build_visualization(self, parent) -> None:
        right = create_card(parent)
        right.pack(side="left", fill="both", expand=True)
        header = ctk.CTkFrame(right, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(15, 6))
        self.visualization_title = create_label(header, "Візуалізація лабіринту", 18, True)
        self.visualization_title.pack(side="left")
        self.maze_stats = create_label(header, f"{self.maze.rows} × {self.maze.cols}", 12, color=COLORS["text_secondary"])
        self.maze_stats.pack(side="right")

        self.canvas = Canvas(right, bg=COLORS["background"], highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=18, pady=(0, 5))
        self.canvas.bind("<Configure>", lambda event: self.draw_maze())
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<Shift-Button-1>", self.on_canvas_click)
        self.canvas.bind("<Shift-B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<Button-3>", self.on_canvas_right_click)
        self.canvas.bind("<Control-Button-3>", self.on_canvas_right_click)

        legend = create_label(
            right,
            "Стіна = #, S = старт, T = мета, синій = хвиля S, фіолетовий = хвиля T, помаранчевий = шлях",
            11,
            color=COLORS["text_secondary"],
        )
        legend.pack(anchor="w", padx=18, pady=(0, 10))

        self.result_textbox = ctk.CTkTextbox(
            right,
            height=120,
            fg_color=COLORS["card"],
            text_color=COLORS["text"],
            corner_radius=8,
            wrap="word",
            font=("Segoe UI", 12),
        )
        self.result_textbox.pack(fill="x", padx=18, pady=(0, 12))
        self.set_result_text("Результат: пошук ще не виконано")

        self.result_label = create_label(right, "", 12)
        self.result_label.pack_forget()

    def _cell_from_event(self, event) -> tuple[int, int] | None:
        if self.maze.rows == 0 or self.maze.cols == 0:
            return None
        cell_width = max(self.canvas.winfo_width() / self.maze.cols, 1)
        cell_height = max(self.canvas.winfo_height() / self.maze.rows, 1)
        col = int(event.x // cell_width)
        row = int(event.y // cell_height)
        if 0 <= row < self.maze.rows and 0 <= col < self.maze.cols:
            return row, col
        return None

    def set_result_text(self, text: str) -> None:
        self.result_textbox.configure(state="normal")
        self.result_textbox.delete("0.0", "end")
        self.result_textbox.insert("0.0", text)
        self.result_textbox.configure(state="disabled")

    def validate_search_input(self) -> None:
        if self.start is None or self.target is None:
            raise ValueError("Потрібно визначити початок і мету. Вкажіть старт і ціль вручну або після очищення лабіринту.")
        if self.maze.count_passable_vertices() == 0:
            raise ValueError("Лабіринт має містити принаймні одну вільну клітинку.")
        if not self.maze.is_inside(self.start):
            raise ValueError("Початкова клітинка виходить за межі лабіринту.")
        if not self.maze.is_inside(self.target):
            raise ValueError("Клітинка мети виходить за межі лабіринту.")
        if not self.maze.is_passable(self.start):
            raise ValueError("Початкова клітинка є стіною. Виберіть іншу.")
        if not self.maze.is_passable(self.target):
            raise ValueError("Клітинка мети є стіною. Виберіть іншу.")
        if self.start == self.target:
            raise ValueError("Початок і мета мають бути різними.")
        if self.operator_var.get() not in {"UP_DOWN_LEFT_RIGHT", "DIAGONAL", "COMBINATION"}:
            raise ValueError("Оберіть коректний оператор переходів.")

    def create_runner(self) -> WaveRunner:
        self.operator = self.operator_var.get()
        self.search_type = self.search_type_var.get()
        self.validate_search_input()
        return WaveRunner(self.maze, self.start, self.target, self.operator, self.search_type)

    def apply_maze_size(self) -> None:
        try:
            rows = int(self.rows_entry.get())
            cols = int(self.cols_entry.get())
            if rows <= 0 or cols <= 0:
                raise ValueError("Кількість рядків і стовпців повинна бути більшою за нуль.")
        except ValueError:
            messagebox.showerror("Некоректний розмір", "Рядки та стовпці мають бути цілими числами більше нуля.")
            return

        old_maze = self.maze.copy()
        new_maze = Maze(rows, cols)
        for row in range(min(rows, old_maze.rows)):
            for col in range(min(cols, old_maze.cols)):
                new_maze.grid[row][col] = old_maze.grid[row][col]
        self.maze = new_maze
        if not self.maze.is_passable(self.start):
            first_passable = self.maze.find_first_passable()
            if first_passable is not None:
                self.start = first_passable
        if not self.maze.is_passable(self.target):
            first_passable = self.maze.find_first_passable()
            if first_passable is not None and first_passable != self.start:
                self.target = first_passable
        self.maze_stats.configure(text=f"{self.maze.rows} × {self.maze.cols}")
        self.draw_maze()

    def load_default_maze(self) -> None:
        self.maze = create_default_maze()
        self.start = DEFAULT_START
        self.target = DEFAULT_TARGET
        self.rows_entry.delete(0, "end")
        self.cols_entry.delete(0, "end")
        self.rows_entry.insert(0, str(self.maze.rows))
        self.cols_entry.insert(0, str(self.maze.cols))
        self.maze_stats.configure(text=f"{self.maze.rows} × {self.maze.cols}")
        self.reset_search()
        self.draw_maze()

    def clear_maze(self) -> None:
        self.maze = Maze(self.maze.rows, self.maze.cols)
        self.start = None
        self.target = None
        self.runner = None
        self.last_result = None
        self.set_result_text("Лабіринт очищено. Вкажіть старт і мету вручну.")
        self.status_label.configure(text="Старт і мета не визначені")
        self.draw_maze()

    def _save_json_maze(self, path: str) -> None:
        data = {
            "rows": self.maze.rows,
            "cols": self.maze.cols,
            "start": list(self.start),
            "target": list(self.target),
            "grid": [row[:] for row in self.maze.grid],
        }
        Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _save_txt_maze(self, path: str) -> None:
        lines = [f"{self.maze.rows} {self.maze.cols}", f"{self.start[0]} {self.start[1]}", f"{self.target[0]} {self.target[1]}"]
        lines.extend(" ".join(str(cell) for cell in row) for row in self.maze.grid)
        Path(path).write_text("\n".join(lines), encoding="utf-8")

    def save_maze(self) -> None:
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON файли", "*.json"), ("TXT файли", "*.txt")],
            title="Зберегти лабіринт",
        )
        if not file_path:
            return
        if file_path.lower().endswith(".txt"):
            self._save_txt_maze(file_path)
        else:
            self._save_json_maze(file_path)
        self.status_label.configure(text="Лабіринт збережено")

    def _load_json_maze(self, path: str) -> None:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        rows = int(data["rows"])
        cols = int(data["cols"])
        grid = data.get("grid")
        if grid is None:
            raise ValueError("У файлі відсутні дані лабіринту.")
        self.maze = Maze(rows, cols, grid)
        self.start = tuple(data.get("start", (0, 0)))
        self.target = tuple(data.get("target", (rows - 1, cols - 1)))
        if not self.maze.is_passable(self.start):
            self.start = self.maze.find_first_passable() or (0, 0)
        if not self.maze.is_passable(self.target):
            self.target = self.maze.find_first_passable() or (0, 0)

    def _load_txt_maze(self, path: str) -> None:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
        if len(lines) < 3:
            raise ValueError("Файл має бути у форматі TXT лабіринту.")
        rows, cols = map(int, lines[0].split())
        start = tuple(map(int, lines[1].split()))
        target = tuple(map(int, lines[2].split()))
        grid_lines = lines[3:]
        if len(grid_lines) != rows:
            raise ValueError("Файл має невірну кількість рядків лабіринту.")
        grid = []
        for line in grid_lines:
            grid.append([int(value) for value in line.split()])
        self.maze = Maze(rows, cols, grid)
        self.start = start
        self.target = target

    def load_maze(self) -> None:
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON файли", "*.json"), ("TXT файли", "*.txt")],
            title="Завантажити лабіринт",
        )
        if not file_path:
            return
        try:
            if file_path.lower().endswith(".txt"):
                self._load_txt_maze(file_path)
            else:
                self._load_json_maze(file_path)
            self.rows_entry.delete(0, "end")
            self.cols_entry.delete(0, "end")
            self.rows_entry.insert(0, str(self.maze.rows))
            self.cols_entry.insert(0, str(self.maze.cols))
            self.maze_stats.configure(text=f"{self.maze.rows} × {self.maze.cols}")
            self.reset_search()
            self.draw_maze()
            self.status_label.configure(text="Лабіринт завантажено")
        except (OSError, ValueError, json.JSONDecodeError, KeyError) as error:
            messagebox.showerror("Помилка завантаження", f"Не вдалося прочитати файл: {error}")

    def _connect_generated_maze(self, grid: list[list[int]]) -> None:
        rows = len(grid)
        cols = len(grid[0]) if rows else 0
        if rows == 0 or cols == 0:
            return
        directions = ((-1, 0), (1, 0), (0, -1), (0, 1))

        passable_cells = [(row, col) for row in range(rows) for col in range(cols) if grid[row][col] == 0]
        if not passable_cells:
            grid[0][0] = 0
            return

        connected = {passable_cells[0]}
        queue = deque([passable_cells[0]])
        while queue:
            row, col = queue.popleft()
            for delta_row, delta_col in directions:
                next_cell = (row + delta_row, col + delta_col)
                if 0 <= next_cell[0] < rows and 0 <= next_cell[1] < cols and next_cell in passable_cells and next_cell not in connected:
                    connected.add(next_cell)
                    queue.append(next_cell)

        for row, col in passable_cells:
            if (row, col) in connected:
                continue
            for delta_row, delta_col in directions:
                next_cell = (row + delta_row, col + delta_col)
                if 0 <= next_cell[0] < rows and 0 <= next_cell[1] < cols and next_cell in connected:
                    grid[row][col] = 0
                    connected.add((row, col))
                    break

        for row, col in passable_cells:
            if (row, col) in connected:
                continue
            grid[row][col] = 0
            connected.add((row, col))

    def generate_maze(self) -> None:
        try:
            rows = int(self.rows_entry.get())
            cols = int(self.cols_entry.get())
        except ValueError:
            messagebox.showerror("Помилка генерації", "Рядки і стовпці мають бути цілими числами.")
            return

        mode_text = self.generation_var.get()
        mode_map = {
            "випадково": "random",
            "місто": "city",
            "природа": "nature",
            "каньйони": "canyons",
        }
        mode = mode_map.get(mode_text, "random")
        rng = random.Random()
        grid = [[-1 for _ in range(cols)] for _ in range(rows)]

        if mode == "random":
            for row in range(rows):
                for col in range(cols):
                    grid[row][col] = 0 if rng.random() < 0.72 else -1
        elif mode == "city":
            for row in range(rows):
                for col in range(cols):
                    if row % 3 == 0 or col % 4 == 0:
                        grid[row][col] = 0
                    elif rng.random() < 0.25:
                        grid[row][col] = 0
        elif mode == "nature":
            centers = [(rows * 0.28, cols * 0.32), (rows * 0.68, cols * 0.38), (rows * 0.4, cols * 0.75)]
            for row in range(rows):
                for col in range(cols):
                    best = min(abs(row - cx) + abs(col - cy) for cx, cy in centers)
                    wall_chance = 0.85 if best <= 2 else 0.35 if best <= 5 else 0.12
                    grid[row][col] = 0 if rng.random() > wall_chance else -1
        elif mode == "canyons":
            for row in range(rows):
                for col in range(cols):
                    wall_chance = 0.0
                    if row % 5 == 0:
                        wall_chance += 0.58
                    if col % 6 == 0:
                        wall_chance += 0.42
                    if abs(row - col) % 7 == 0:
                        wall_chance += 0.28
                    if (row + col) % 10 == 0:
                        wall_chance += 0.18
                    grid[row][col] = 0 if rng.random() > wall_chance else -1

        self._connect_generated_maze(grid)

        passable_cells = [(row, col) for row in range(rows) for col in range(cols) if grid[row][col] == 0]
        if not passable_cells:
            grid[0][0] = 0
            passable_cells = [(0, 0)]

        start = passable_cells[0]
        furthest = start
        farthest_distance = -1
        for cell in passable_cells:
            distance = abs(cell[0] - start[0]) + abs(cell[1] - start[1])
            if distance > farthest_distance:
                farthest_distance = distance
                furthest = cell

        self.maze = Maze(rows, cols, grid)
        self.start = start
        self.target = furthest
        self.maze_stats.configure(text=f"{self.maze.rows} × {self.maze.cols}")
        self.rows_entry.delete(0, "end")
        self.cols_entry.delete(0, "end")
        self.rows_entry.insert(0, str(rows))
        self.cols_entry.insert(0, str(cols))
        self.reset_search()
        self.draw_maze()
        self.status_label.configure(text=f"Згенеровано лабіринт ({mode_text})")

    def set_cell_value(self, row: int, col: int, invert: bool = False) -> None:
        if not self.maze.is_inside((row, col)):
            return

        mode = self.edit_mode_var.get()
        mode_map = {"стіна": "wall", "прохід": "passable", "старт": "start", "мета": "target"}
        effective_mode = mode_map.get(mode, "wall")
        if invert:
            if effective_mode == "wall":
                effective_mode = "passable"
            elif effective_mode == "passable":
                effective_mode = "wall"
            elif effective_mode == "start":
                effective_mode = "target"
            elif effective_mode == "target":
                effective_mode = "start"

        if effective_mode in {"start", "target"}:
            if not self.maze.is_passable((row, col)):
                messagebox.showwarning("Некоректне призначення", "Для старту або мети потрібна вільна клітинка.")
                return
            if effective_mode == "start":
                self.start = (row, col)
                self.status_label.configure(text=f"Початок оновлено: ({row}, {col})")
            else:
                self.target = (row, col)
                self.status_label.configure(text=f"Мета оновлена: ({row}, {col})")
            self.draw_maze()
            return

        if effective_mode == "wall":
            self.maze.set_cell((row, col), -1)
            self.status_label.configure(text=f"Клітинка ({row}, {col}) перетворена на стіну")
        else:
            self.maze.set_cell((row, col), 0)
            self.status_label.configure(text=f"Клітинка ({row}, {col}) перетворена на прохід")
        self.draw_maze()

    def on_canvas_click(self, event) -> None:
        cell = self._cell_from_event(event)
        if cell is not None:
            self.set_cell_value(*cell, invert=bool(event.state & 0x0001))

    def on_canvas_drag(self, event) -> None:
        if self.maze.rows == 0 or self.maze.cols == 0:
            return
        mode = self.edit_mode_var.get()
        if mode not in {"стіна", "прохід"}:
            return
        cell = self._cell_from_event(event)
        if cell is None:
            return
        self.set_cell_value(cell[0], cell[1], invert=bool(event.state & 0x0001))

    def on_canvas_right_click(self, event) -> None:
        cell = self._cell_from_event(event)
        if cell is None:
            return
        row, col = cell
        is_control = bool(event.state & 0x0004)
        if not self.maze.is_passable((row, col)):
            if is_control:
                messagebox.showwarning("Некоректна мета", "Мета має бути вільною клітинкою.")
            else:
                messagebox.showwarning("Некоректний старт", "Старт має бути вільною клітинкою.")
            return
        if is_control:
            self.target = (row, col)
            self.status_label.configure(text=f"Мета змінена через ПКМ+Ctrl: ({row}, {col})")
        else:
            self.start = (row, col)
            self.status_label.configure(text=f"Старт змінено через ПКМ: ({row}, {col})")
        self.draw_maze()

    def swap_start_target(self) -> None:
        self.start, self.target = self.target, self.start
        self.status_label.configure(text="Початок і мета поміняні місцями")
        self.draw_maze()

    def run_search(self) -> None:
        try:
            self.runner = self.create_runner()
        except (MazeError, ValueError) as error:
            messagebox.showerror("Помилка пошуку", str(error))
            return
        self.last_result = None
        self.result_label.configure(text="Пошук в процесі...")
        self.status_label.configure(text="Пошук...", text_color=COLORS["text_secondary"])
        self.animate_step()

    def animate_step(self) -> None:
        if self.runner is None:
            return
        self.runner.step()
        self.draw_maze()
        if not self.runner.finished:
            delay = int(self.speed_var.get().split()[0])
            self.animation_job = self.after(delay, self.animate_step)
        else:
            self.finish_search()

    def step_search(self) -> None:
        try:
            if self.runner is None or self.runner.finished:
                self.runner = self.create_runner()
            self.runner.step()
            self.draw_maze()
            if self.runner.finished:
                self.finish_search()
        except (MazeError, ValueError) as error:
            messagebox.showerror("Помилка пошуку", str(error))

    def run_search_instant(self) -> None:
        if self.animation_job:
            self.after_cancel(self.animation_job)
            self.animation_job = None
        try:
            self.runner = self.create_runner()
            self.runner.run()
        except (MazeError, ValueError) as error:
            messagebox.showerror("Помилка пошуку", str(error))
            return
        self.finish_search()

    def finish_search(self) -> None:
        if self.runner is None:
            return
        result = self.runner.result()
        self.last_result = result
        self.record_experiment(result)

        if result.found:
            path_text = " -> ".join(f"({row}, {col})" for row, col in result.path)
            color = COLORS["success"]
            label = f"{result.search_type} | Шлях знайдено | {path_text} | довжина шляху = {result.path_length} | хвильові цикли = {result.wave_cycles} | відвідано = {len(result.visited_vertices)} | час = {result.elapsed_time * 1000:.3f} ms"
        else:
            color = COLORS["danger"]
            label = f"{result.search_type} | Шлях не знайдено | хвильові цикли = {result.wave_cycles} | відвідано = {len(result.visited_vertices)} | час = {result.elapsed_time * 1000:.3f} ms"
        self.set_result_text(label)
        self.result_label.configure(text=label)
        self.status_label.configure(text="Пошук завершено", text_color=color)
        self.draw_maze()

    def record_experiment(self, result: WaveResult) -> None:
        entry = {
            "maze_size": f"{self.maze.rows} × {self.maze.cols}",
            "vertices": self.maze.count_passable_vertices(),
            "operator": self.operator_var.get(),
            "search_type": result.search_type,
            "start": self.start,
            "target": self.target,
            "path_length": result.path_length,
            "wave_cycles": result.wave_cycles,
            "opened_vertices": len(result.visited_vertices),
            "execution_time": result.elapsed_time,
        }
        self.experiments.append(entry)

    def reset_search(self) -> None:
        if self.animation_job:
            self.after_cancel(self.animation_job)
            self.animation_job = None
        self.runner = None
        self.last_result = None
        self.set_result_text("Результат: пошук ще не виконано")
        self.result_label.configure(text="Результат: пошук ще не виконано")
        self.status_label.configure(text="Готово", text_color=COLORS["text_secondary"])
        self.draw_maze()

    def draw_maze(self) -> None:
        if not hasattr(self, "canvas") or not self.canvas.winfo_exists():
            return
        self.canvas.delete("all")
        width = max(self.canvas.winfo_width(), 100)
        height = max(self.canvas.winfo_height(), 100)
        cell_width = width / self.maze.cols
        cell_height = height / self.maze.rows

        path_cells = set(self.last_result.path) if self.last_result and self.last_result.found else set()
        visited_cells = set(self.runner.visited) if self.runner else set()
        visited_start = set(self.runner.visited_start) if self.runner else set()
        visited_target = set(self.runner.visited_target) if self.runner else set()
        expanded_cells = set(self.runner.expanded) if self.runner else set()
        current_cell = self.runner.current_cell if self.runner else None
        meeting_cell = self.runner.meeting_cell if self.runner else None

        for row in range(self.maze.rows):
            for col in range(self.maze.cols):
                x0 = col * cell_width
                y0 = row * cell_height
                x1 = x0 + cell_width
                y1 = y0 + cell_height
                cell = (row, col)

                if self.maze.grid[row][col] == -1:
                    fill = "#475569"
                elif cell == self.start:
                    fill = "#86efac"
                elif cell == self.target:
                    fill = "#fca5a5"
                elif cell in path_cells:
                    fill = "#fbbf24"
                elif cell == meeting_cell:
                    fill = "#f97316"
                elif cell in visited_start:
                    fill = "#bfdbfe"
                elif cell in visited_target:
                    fill = "#d8b4fe"
                elif cell in visited_cells:
                    fill = "#bfdbfe"
                elif cell in expanded_cells:
                    fill = "#dbeafe"
                else:
                    fill = "#f8fafc"

                self.canvas.create_rectangle(x0, y0, x1, y1, fill=fill, outline="#cbd5e1", width=1)

                if self.maze.grid[row][col] == -1:
                    self.canvas.create_text(x0 + cell_width / 2, y0 + cell_height / 2, text="#", font=("Segoe UI", 14, "bold"), fill="white")
                elif cell == self.start:
                    self.canvas.create_text(x0 + cell_width / 2, y0 + cell_height / 2, text="S", font=("Segoe UI", 14, "bold"), fill="#14532d")
                elif cell == self.target:
                    self.canvas.create_text(x0 + cell_width / 2, y0 + cell_height / 2, text="T", font=("Segoe UI", 14, "bold"), fill="#7f1d1d")
                elif self.runner and self.runner.search_type == "Двонаправлений" and cell in self.runner.dist_start:
                    self.canvas.create_text(x0 + cell_width / 2, y0 + cell_height / 2, text=f"S:{self.runner.dist_start[cell]}", font=("Segoe UI", 9, "bold"), fill="#1e3a8a")
                elif self.runner and self.runner.search_type == "Двонаправлений" and cell in self.runner.dist_target:
                    self.canvas.create_text(x0 + cell_width / 2, y0 + cell_height / 2, text=f"T:{self.runner.dist_target[cell]}", font=("Segoe UI", 9, "bold"), fill="#581c87")
                elif self.runner and cell in self.runner.distance:
                    text = str(self.runner.distance[cell])
                    self.canvas.create_text(x0 + cell_width / 2, y0 + cell_height / 2, text=text, font=("Segoe UI", 12, "bold"), fill="#1e293b")
                if current_cell == cell:
                    self.canvas.create_rectangle(x0 + 2, y0 + 2, x1 - 2, y1 - 2, outline="#7c3aed", width=2)
                if meeting_cell == cell and cell not in path_cells:
                    self.canvas.create_oval(x0 + 4, y0 + 4, x1 - 4, y1 - 4, outline="#ea580c", width=3)

    def show_results(self) -> None:
        self.clear_main()
        create_title(self.main, "Результати").pack(anchor="w")
        create_label(self.main, "Таблиця експериментів", 13, color=COLORS["text_secondary"]).pack(anchor="w", pady=(5, 15))
        table_holder = ctk.CTkFrame(self.main, fg_color="transparent")
        table_holder.pack(fill="both", expand=True)

        columns = (
            "Розмір",
            "Клітинки",
            "Оператор",
            "Тип пошуку",
            "Старт",
            "Мета",
            "Довжина шляху",
            "Хвильові цикли",
            "Відкрито",
            "Час виконання",
        )

        tree = ttk.Treeview(table_holder, columns=columns, show="headings")
        tree.pack(fill="both", expand=True)
        for column in columns:
            tree.heading(column, text=column)
            tree.column(column, width=120, anchor="center")

        for experiment in self.experiments:
            tree.insert(
                "",
                "end",
                values=(
                    experiment["maze_size"],
                    experiment["vertices"],
                    experiment["operator"],
                    experiment["search_type"],
                    experiment["start"],
                    experiment["target"],
                    experiment["path_length"],
                    experiment["wave_cycles"],
                    experiment["opened_vertices"],
                    f"{experiment['execution_time'] * 1000:.3f} ms",
                ),
            )

        if not self.experiments:
            tree.insert("", "end", values=("—", "—", "—", "—", "—", "—", "—", "—", "—", "—"))

    def show_theory(self) -> None:
        self.clear_main()
        create_title(self.main, "Теорія").pack(anchor="w")
        create_label(self.main, "Одно- та двонаправлений хвильовий пошук у лабіринті", 13, color=COLORS["text_secondary"]).pack(anchor="w", pady=(5, 15))
        text = """
Односпрямований хвильовий пошук використовує чергу FIFO для поширення хвилі від стартової клітинки до мети.

    Двонаправлений пошук одночасно поширює дві FIFO-хвилі: від старту та від мети. Хвилі чергуються на кожному кроці. Коли клітинка стає доступною для обох хвиль, вона є кандидатом на точку зустрічі, а пошук продовжується лише настільки, щоб гарантувати найкоротший шлях.

Кожна вільна клітина лабіринту є вершиною графа, а сусідні клітини утворюють ребра залежно від обраного оператора переходів.

Матриця лабіринту: -1 означає стіну, 0 означає вільну клітинку. Граф не задається окремо — він формується динамічно за координатами (рядок, стовпець).

Алгоритм працює як хвиля: стартова клітина отримує дистанцію 0, кожна наступна клітина — на одиницю дальшу від попередника. Завдяки FIFO-черзі найкоротший шлях до мети знаходиться першою виявленою хвилею.

Оператори переходів визначають, які сусіди доступні:
- UP_DOWN_LEFT_RIGHT: чотири напрямки по сторонах світла
- DIAGONAL: чотири діагональні напрямки
- COMBINATION: всі вісім сусідів

Коли сусідня клітинка доступна, вільна й ще не відвідана, алгоритм записує батьківську посилання та зберігає відстань. Після знаходження мети шлях відновлюється за ланцюжком батьків.

Це відрізняється від звичайного графового BFS тим, що граф не зберігається як список вершин і ребер. Натомість він генерується з матриці лабіринту під час виконання.

Хвильові цикли відповідають максимальній досягнутій дистанції. Довжина шляху дорівнює відстані до мети, а не просто числу кроків виконання циклу. У двонаправленому режимі статистика відвіданих клітинок є сумою обох хвиль.
"""
        frame = ctk.CTkTextbox(self.main, width=950, height=560, fg_color=COLORS["card"], text_color=COLORS["text"], corner_radius=8)
        frame.insert("0.0", text)
        frame.configure(state="disabled")
        frame.pack(fill="both", expand=True)


def main() -> None:
    app = SearchApplication()
    app.mainloop()


if __name__ == "__main__":
    main()