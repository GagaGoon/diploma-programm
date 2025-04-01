# view/ComparisonView.py
import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np # Добавим импорт numpy здесь для проверки None

# Размер пикселя для вкладки сравнения
COMPARISON_PIXEL_SIZE = 8
# Цвет фона неактивных пикселей (как в DrawingView)
BACKGROUND_COLOR = '#F0F0F0'
# Цвет активных пикселей изображения
IMAGE_PIXEL_COLOR = 'blue'
# Цвет активных пикселей шаблона
TEMPLATE_PIXEL_COLOR = 'red'
# Цвет обводки шаблона
TEMPLATE_OUTLINE_COLOR = 'yellow'
# Цвет обводки пикселей фона/изображения
GRID_OUTLINE_COLOR = 'white'


class ComparisonView:
    """
    Представление (View) для вкладки сравнения изображений и шаблонов.
    """
    def __init__(self, parent_frame, controller):
        self.frame = parent_frame
        self.controller = controller

        # --- Панель загрузки ---
        self.load_frame = tk.Frame(self.frame)
        self.load_frame.pack(pady=5, padx=10, fill=tk.X)

        self.load_image_button = tk.Button(self.load_frame, text="Загрузить изображение (.xml)", command=self.controller.handle_load_image)
        self.load_image_button.pack(side=tk.LEFT, padx=5)

        self.load_template_button = tk.Button(self.load_frame, text="Загрузить шаблон (.xml)", command=self.controller.handle_load_template)
        self.load_template_button.pack(side=tk.LEFT, padx=5)
        self.load_template_button.config(state=tk.DISABLED)

        # --- Панель управления и результатов ---
        self.control_frame = tk.Frame(self.frame)
        self.control_frame.pack(pady=5, padx=10, fill=tk.X)

        self.find_best_button = tk.Button(self.control_frame, text="Найти лучшее совпадение", command=self.controller.handle_find_best_match)
        self.find_best_button.pack(side=tk.LEFT, padx=5)
        self.find_best_button.config(state=tk.DISABLED)

        # --- ИЗМЕНЕНО: Метка для результата и позиции ---
        self.info_label = tk.Label(self.control_frame, text="Результат: - | Позиция: (-, -)")
        self.info_label.pack(side=tk.LEFT, padx=10)
        # --- Конец изменений ---

        # --- Холст для отображения с прокруткой ---
        canvas_frame = tk.Frame(self.frame)
        canvas_frame.pack(pady=10, padx=10, expand=True, fill=tk.BOTH)

        self.h_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        self.v_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL)

        self.canvas = tk.Canvas(canvas_frame,
                                width=400, height=400,
                                bg=BACKGROUND_COLOR, # Устанавливаем фон холста сразу
                                relief=tk.SUNKEN, borderwidth=1,
                                xscrollcommand=self.h_scrollbar.set,
                                yscrollcommand=self.v_scrollbar.set)

        self.h_scrollbar.config(command=self.canvas.xview)
        self.v_scrollbar.config(command=self.canvas.yview)

        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        self.canvas.bind("<ButtonPress-1>", self.controller.handle_canvas_press)
        self.canvas.bind("<B1-Motion>", self.controller.handle_canvas_drag)
        self.canvas.bind("<Motion>", self.controller.handle_canvas_motion)
        self.canvas.bind("<Configure>", self.controller.handle_canvas_configure)

    def update_canvas(self, image_pixels, template_pixels, template_pos_rc):
        """ Отображает изображение и шаблон поверх него """
        self.canvas.delete("all")
        if image_pixels is None:
            self.canvas.config(scrollregion=(0, 0, 1, 1), width=100, height=100)
            # Убедимся, что фон холста правильный
            self.canvas.config(bg=BACKGROUND_COLOR)
            return

        img_rows, img_cols = image_pixels.shape
        canvas_width = img_cols * COMPARISON_PIXEL_SIZE
        canvas_height = img_rows * COMPARISON_PIXEL_SIZE

        # Устанавливаем scrollregion и размер холста
        # Важно: config может не сразу обновить размер, но scrollregion важнее
        self.canvas.config(scrollregion=(0, 0, canvas_width, canvas_height))
        # Можно попробовать установить и размер, но он может быть ограничен окном
        # self.canvas.config(width=canvas_width, height=canvas_height)

        # --- ИЗМЕНЕНО: Рисуем все пиксели изображения (фон и активные) ---
        for r in range(img_rows):
            for c in range(img_cols):
                x0, y0 = c * COMPARISON_PIXEL_SIZE, r * COMPARISON_PIXEL_SIZE
                x1, y1 = x0 + COMPARISON_PIXEL_SIZE, y0 + COMPARISON_PIXEL_SIZE
                # Определяем цвет пикселя изображения
                fill_color = IMAGE_PIXEL_COLOR if image_pixels[r, c] == 1 else BACKGROUND_COLOR
                # Рисуем прямоугольник пикселя
                self.canvas.create_rectangle(x0, y0, x1, y1,
                                             fill=fill_color,
                                             outline=GRID_OUTLINE_COLOR, # Белая обводка для сетки
                                             width=1,
                                             tags="image_pixel") # Тег для возможного будущего использования
        # --- Конец изменений ---

        # Рисуем шаблон поверх (красные пиксели), если он есть и позиция корректна
        if template_pixels is not None and template_pos_rc != (-1,-1):
            tpl_rows, tpl_cols = template_pixels.shape
            start_row, start_col = template_pos_rc

            for r_tpl in range(tpl_rows):
                for c_tpl in range(tpl_cols):
                    # Рисуем только '1' пиксели шаблона
                    if template_pixels[r_tpl, c_tpl] == 1:
                        r_img, c_img = start_row + r_tpl, start_col + c_tpl
                        if 0 <= r_img < img_rows and 0 <= c_img < img_cols:
                             x0, y0 = c_img * COMPARISON_PIXEL_SIZE, r_img * COMPARISON_PIXEL_SIZE
                             x1, y1 = x0 + COMPARISON_PIXEL_SIZE, y0 + COMPARISON_PIXEL_SIZE
                             # Рисуем красный квадрат поверх
                             self.canvas.create_rectangle(x0, y0, x1, y1,
                                                          fill=TEMPLATE_PIXEL_COLOR,
                                                          outline=TEMPLATE_OUTLINE_COLOR,
                                                          width=1,
                                                          tags="template_pixel") # Тег для шаблона

    # --- ИЗМЕНЕНО: Метод для обновления информации (результат и позиция) ---
    def update_info_label(self, score, pos_rc):
        """ Обновляет метку с текущим/лучшим результатом и позицией шаблона """
        r, c = pos_rc
        # Форматируем счет
        if score is None or score == -np.inf or r == -1:
             score_str = "-"
             pos_str = "(-, -)"
        else:
             # Проверяем, является ли score числом перед форматированием
             try:
                 score_str = f"{float(score):.0f}" # Показываем целое число совпадений
             except (ValueError, TypeError):
                 score_str = str(score) # Если не число, показываем как есть
             pos_str = f"({r}, {c})"

        self.info_label.config(text=f"Результат: {score_str} | Позиция: {pos_str}")
    # --- Конец изменений ---

    # Метод update_current_info_label удален

    def set_widget_state(self, widget_name, state):
        """ Управляет состоянием кнопок (normal/disabled) """
        widget = getattr(self, widget_name, None)
        if widget:
            widget.config(state=state)
        else:
            print(f"Warning: Widget '{widget_name}' not found in ComparisonView.")

    def show_error(self, title, message):
        messagebox.showerror(title, message, parent=self.frame)

    def show_info(self, title, message):
        messagebox.showinfo(title, message, parent=self.frame)