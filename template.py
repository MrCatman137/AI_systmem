import customtkinter as ctk


# ============================================================
# НАЛАШТУВАННЯ ТЕМИ
# ============================================================

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


# ============================================================
# КОЛЬОРИ ТА СТИЛІ
# ============================================================

COLORS = {
    "background": "#f8fafc",      # Основний фон
    "sidebar": "#f1f5f9",         # Бічна панель
    "card": "#ffffff",            # Картки

    "primary": "#b2caff",         # Основний синій
    "primary_hover": "#93acf0",

    "success": "#16a34a",         # Зелений
    "success_hover": "#15803d",

    "danger": "#dc2626",          # Червоний
    "danger_hover": "#b91c1c",

    "secondary": "#e2e8f0",       # Світло-сірий
    "secondary_hover": "#cbd5e1",

    "text": "#0f172a",             # Основний текст
    "text_secondary": "#64748b",  # Другорядний текст

    "border": "#858e97",           # Межі
}


# ============================================================
# БАЗОВІ ФУНКЦІЇ ДЛЯ СТВОРЕННЯ WIDGETS
# ============================================================

def create_button(
    parent,
    text,
    command=None,
    width=180,
    height=40,
    style="primary"
):
    """
    Універсальна кнопка.

    style:
        primary
        secondary
        success
        danger
    """

    styles = {
        "primary": (
            COLORS["primary"],
            COLORS["primary_hover"]
        ),

        "secondary": (
            COLORS["secondary"],
            COLORS["secondary_hover"]
        ),

        "success": (
            COLORS["success"],
            COLORS["success_hover"]
        ),

        "danger": (
            COLORS["danger"],
            COLORS["danger_hover"]
        ),
    }

    fg, hover = styles.get(
        style,
        styles["primary"]
    )

    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        width=width,
        height=height,
        corner_radius=3,
        fg_color=fg,
        hover_color=hover,
        text_color=COLORS["text"],
        font=("Segoe UI", 14)
    )


def create_label(
    parent,
    text,
    size=14,
    bold=False,
    color=None
):
    """
    Звичайний текстовий Label.
    """

    weight = "bold" if bold else "normal"

    return ctk.CTkLabel(
        parent,
        text=text,
        text_color=color or COLORS["text"],
        font=("Segoe UI", size, weight)
    )


def create_title(parent, text):
    """
    Великий заголовок.
    """

    return ctk.CTkLabel(
        parent,
        text=text,
        text_color=COLORS["text"],
        font=("Segoe UI", 24, "bold")
    )


def create_entry(
    parent,
    placeholder="",
    width=220
):
    """
    Поле введення.
    """

    return ctk.CTkEntry(
        parent,
        width=width,
        height=40,
        placeholder_text=placeholder,
        corner_radius=3,
        border_width=1,
        border_color=COLORS["border"],
        font=("Segoe UI", 14)
    )


def create_combobox(
    parent,
    values,
    width=220
):
    """
    Випадаючий список.
    """

    return ctk.CTkComboBox(
        parent,
        values=values,
        width=width,
        height=40,
        corner_radius=3,
        font=("Segoe UI", 14)
    )


def create_slider(
    parent,
    width=220,
    from_=0,
    to=100,
    command=None
):
    """
    Повзунок.
    """

    return ctk.CTkSlider(
        parent,
        width=width,
        from_=from_,
        to=to,
        command=command
    )


def create_checkbox(
    parent,
    text,
    command=None
):
    """
    Checkbox.
    """

    return ctk.CTkCheckBox(
        parent,
        text=text,
        command=command,
        font=("Segoe UI", 14)
    )


def create_switch(
    parent,
    text,
    command=None
):
    """
    Switch.
    """

    return ctk.CTkSwitch(
        parent,
        text=text,
        command=command,
        font=("Segoe UI", 14)
    )


def create_card(parent):
    """
    Універсальна картка/панель.
    """

    return ctk.CTkFrame(
        parent,
        fg_color=COLORS["card"],
        corner_radius=5,
        border_width=1,
        border_color=COLORS["border"]
    )


# ============================================================
# ГОЛОВНЕ ВІКНО
# ============================================================

class Application(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("AI Systems Laboratory")
        self.geometry("1200x750")
        self.minsize(900, 600)

        self.configure(
            fg_color=COLORS["background"]
        )

        self.create_interface()


    # ========================================================
    # ІНТЕРФЕЙС
    # ========================================================

    def create_interface(self):

        # ----------------------------------------------------
        # SIDEBAR
        # ----------------------------------------------------

        self.sidebar = ctk.CTkFrame(
            self,
            width=230,
            corner_radius=0,
            fg_color=COLORS["sidebar"]
        )

        self.sidebar.pack(
            side="left",
            fill="y"
        )

        self.sidebar.pack_propagate(False)


        # Назва програми

        title = create_label(
            self.sidebar,
            "Системи штучного\nінтелекту",
            size=20,
            bold=True
        )

        title.pack(
            padx=25,
            pady=(30, 5),
            anchor="w"
        )


        subtitle = create_label(
            self.sidebar,
            "Студент: Трофимов Володимир",
            size=11,
            color=COLORS["text_secondary"]
        )

        subtitle.pack(
            padx=25,
            anchor="w"
        )


        # ----------------------------------------------------
        # SIDEBAR BUTTONS
        # ----------------------------------------------------

        self.btn_lab = create_button(
            self.sidebar,
            "Лабораторна",
            command=self.show_lab,
            width=180,
            style="primary"
        )

        self.btn_lab.pack(
            padx=25,
            pady=(40, 10)
        )


        self.btn_results = create_button(
            self.sidebar,
            "Результати",
            command=self.show_results,
            width=180,
            style="secondary"
        )

        self.btn_results.pack(
            padx=25,
            pady=10
        )


        # self.btn_about = create_button(
        #     self.sidebar,
        #     "Про програму",
        #     command=self.show_about,
        #     width=180,
        #     style="secondary"
        # )

        # self.btn_about.pack(
        #     padx=25,
        #     pady=10
        # )


        # ----------------------------------------------------
        # MAIN AREA
        # ----------------------------------------------------

        self.main = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        self.main.pack(
            side="left",
            fill="both",
            expand=True,
            padx=25,
            pady=25
        )


        self.show_lab()


    # ========================================================
    # ОЧИЩЕННЯ MAIN
    # ========================================================

    def clear_main(self):

        for widget in self.main.winfo_children():
            widget.destroy()


    # ========================================================
    # ЛАБОРАТОРНА
    # ========================================================

    def show_lab(self):

        self.clear_main()


        # Заголовок

        create_title(
            self.main,
            "Лабораторна робота"
        ).pack(
            anchor="w"
        )


        create_label(
            self.main,
            "<Назва лабораторної роботи>.",
            size=13,
            color=COLORS["text_secondary"]
        ).pack(
            anchor="w",
            pady=(5, 20)
        )


        # ----------------------------------------------------
        # ОСНОВНИЙ КОНТЕЙНЕР
        # ----------------------------------------------------

        content = ctk.CTkFrame(
            self.main,
            fg_color="transparent"
        )

        content.pack(
            fill="both",
            expand=True
        )


        # ====================================================
        # ЛІВА ПАНЕЛЬ
        # ====================================================

        left = create_card(content)

        left.pack(
            side="left",
            fill="y",
            padx=(0, 15)
        )

        left.configure(width=260)


        create_label(
            left,
            "Параметри",
            size=18,
            bold=True
        ).pack(
            padx=20,
            pady=(20, 20),
            anchor="w"
        )


        # Приклад ComboBox

        create_label(
            left,
            "Алгоритм"
        ).pack(
            padx=20,
            anchor="w"
        )


        algorithm = create_combobox(
            left,
            [
                "Вибрати алгоритм",
                "Алгоритм 1",
                "Алгоритм 2",
                "Алгоритм 3"
            ],
            width=220
        )

        algorithm.pack(
            padx=20,
            pady=(5, 15)
        )


        # Приклад Entry

        create_label(
            left,
            "Кількість елементів"
        ).pack(
            padx=20,
            anchor="w"
        )


        number = create_entry(
            left,
            "Наприклад: 100",
            width=220
        )

        number.pack(
            padx=20,
            pady=(5, 15)
        )


        # Checkbox

        checkbox = create_checkbox(
            left,
            "Показувати анімацію"
        )

        checkbox.pack(
            padx=20,
            pady=10,
            anchor="w"
        )


        # ----------------------------------------------------
        # КНОПКИ
        # ----------------------------------------------------

        create_button(
            left,
            "Запустити",
            command=self.run_algorithm,
            width=220,
            style="primary"
        ).pack(
            padx=20,
            pady=(20, 8)
        )


        create_button(
            left,
            "Очистити",
            command=self.clear_result,
            width=220,
            style="secondary"
        ).pack(
            padx=20,
            pady=8
        )


        # ====================================================
        # ЦЕНТРАЛЬНА ОБЛАСТЬ
        # ====================================================

        center = create_card(content)

        center.pack(
            side="left",
            fill="both",
            expand=True
        )


        create_label(
            center,
            "Область результату",
            size=18,
            bold=True
        ).pack(
            padx=20,
            pady=(20, 10),
            anchor="w"
        )


        # ----------------------------------------------------
        # Тут пізніше можна розмістити:
        #
        # Canvas
        # Matplotlib
        # Граф
        # Таблицю
        # Зображення
        # Нейронну мережу
        # Візуалізацію алгоритму
        # ----------------------------------------------------

        self.result_area = ctk.CTkFrame(
            center,
            fg_color=COLORS["background"],
            corner_radius=5
        )

        self.result_area.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(5, 20)
        )


        create_label(
            self.result_area,
            "Тут буде твоя візуалізація",
            size=16,
            color=COLORS["text_secondary"]
        ).place(
            relx=0.5,
            rely=0.5,
            anchor="center"
        )


    # ========================================================
    # РЕЗУЛЬТАТИ
    # ========================================================

    def show_results(self):

        self.clear_main()


        create_title(
            self.main,
            "Результати"
        ).pack(
            anchor="w"
        )


        create_label(
            self.main,
            "Тут можна розмістити таблицю, графіки або статистику.",
            size=13,
            color=COLORS["text_secondary"]
        ).pack(
            anchor="w",
            pady=(5, 20)
        )


        # Приклад карток статистики

        stats = ctk.CTkFrame(
            self.main,
            fg_color="transparent"
        )

        stats.pack(
            fill="x",
            pady=10
        )


        self.create_stat_card(
            stats,
            "Час виконання",
            "0.00 s"
        ).pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 10)
        )


        self.create_stat_card(
            stats,
            "Кількість кроків",
            "0"
        ).pack(
            side="left",
            fill="x",
            expand=True,
            padx=10
        )


        self.create_stat_card(
            stats,
            "Результат",
            "—"
        ).pack(
            side="left",
            fill="x",
            expand=True,
            padx=(10, 0)
        )


    # ========================================================
    # STAT CARD
    # ========================================================

    def create_stat_card(
        self,
        parent,
        title,
        value
    ):

        card = create_card(parent)

        card.configure(
            height=120
        )

        create_label(
            card,
            title,
            size=13,
            color=COLORS["text_secondary"]
        ).pack(
            padx=20,
            pady=(20, 5),
            anchor="w"
        )


        create_label(
            card,
            value,
            size=24,
            bold=True
        ).pack(
            padx=20,
            anchor="w"
        )


        return card


    # ========================================================
    # ПРО ПРОГРАМУ
    # ========================================================

    def show_about(self):

        self.clear_main()


        create_title(
            self.main,
            "Про програму"
        ).pack(
            anchor="w"
        )


        card = create_card(
            self.main
        )

        card.pack(
            fill="x",
            pady=25
        )


        create_label(
            card,
            "AI Systems Laboratory",
            size=20,
            bold=True
        ).pack(
            padx=25,
            pady=(25, 10),
            anchor="w"
        )


        create_label(
            card,
            "Універсальний графічний шаблон "
            "для лабораторних робіт із систем штучного інтелекту.",
            size=14,
            color=COLORS["text_secondary"]
        ).pack(
            padx=25,
            pady=(0, 25),
            anchor="w"
        )


    # ========================================================
    # ДІЇ
    # ========================================================

    def run_algorithm(self):

        # ====================================================
        # СЮДИ ТИ ПОТІМ ДОДАЄШ СВОЮ ЛОГІКУ
        # ====================================================

        print("Алгоритм запущено")


    def clear_result(self):

        print("Результат очищено")


# ============================================================
# ЗАПУСК
# ============================================================

if __name__ == "__main__":

    app = Application()

    app.mainloop()