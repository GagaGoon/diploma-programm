# view/ComparisonView.py
import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import cv2
from PIL import Image, ImageTk

BACKGROUND_COLOR = '#F0F0F0'
TEMPLATE_PIXEL_COLOR = 'red'
TEMPLATE_OUTLINE_COLOR = 'yellow'
SCALE_INCREMENT = 0.1 # Шаг изменения масштаба кнопками

class ComparisonView:
    """
    Представление (View) для вкладки сравнения изображений и шаблонов.
    Отображает реальные изображения и шаблон поверх.
    ИЗМЕНЕНО: Слайдер заменен на Entry + кнопки +/-.
    """
    def __init__(self, parent_frame, controller):
        self.frame = parent_frame
        self.controller = controller
        self._photo_image = None
        self._current_scale = 1.0
        self._img_original_width = 1
        self._img_original_height = 1
        self._display_width = 1
        self._display_height = 1

        # --- Панель загрузки (без изменений) ---
        self.load_frame = tk.Frame(self.frame)
        self.load_frame.pack(pady=5, padx=10, fill=tk.X)

        self.load_image_button = tk.Button(self.load_frame, text="Загрузить изображение (jpg, png...)", command=self.controller.handle_load_image)
        self.load_image_button.pack(side=tk.LEFT, padx=5)

        self.load_template_button = tk.Button(self.load_frame, text="Загрузить шаблон (.xml)", command=self.controller.handle_load_template)
        self.load_template_button.pack(side=tk.LEFT, padx=5)
        self.load_template_button.config(state=tk.DISABLED)

        # --- Панель управления: Разделена на верхнюю и нижнюю части ---
        self.control_frame = tk.Frame(self.frame)
        self.control_frame.pack(pady=5, padx=10, fill=tk.X)

        # --- Верхняя часть панели управления (Собель, Поиск, Инфо) ---
        self.top_control_frame = tk.Frame(self.control_frame)
        self.top_control_frame.pack(fill=tk.X, pady=(0, 5)) # Отступ снизу

        self.sobel_button = tk.Button(self.top_control_frame, text="Собель", command=self.controller.handle_apply_sobel)
        self.sobel_button.pack(side=tk.LEFT, padx=5)
        self.sobel_button.config(state=tk.DISABLED)

        self.find_best_button = tk.Button(self.top_control_frame, text="Найти лучшее совпадение", command=self.controller.handle_find_best_match)
        self.find_best_button.pack(side=tk.LEFT, padx=5)
        self.find_best_button.config(state=tk.DISABLED)

        self.info_label = tk.Label(self.top_control_frame, text="Результат: - | Позиция: (-, -)")
        self.info_label.pack(side=tk.LEFT, padx=10)

        # --- Нижняя часть панели управления (Масштаб) ---
        self.bottom_control_frame = tk.Frame(self.control_frame)
        self.bottom_control_frame.pack(fill=tk.X)

        # --- НОВОЕ: Управление масштабом через Entry и кнопки ---
        self.scale_label = tk.Label(self.bottom_control_frame, text="Масштаб:") # Изменена надпись
        self.scale_label.pack(side=tk.LEFT, padx=(0, 5)) # Отступ справа

        # Переменная для хранения значения в Entry
        self.scale_entry_var = tk.StringVar(value="1.0")
        self.scale_entry = tk.Entry(
            self.bottom_control_frame,
            textvariable=self.scale_entry_var,
            width=6 # Ширина поля ввода
        )
        self.scale_entry.pack(side=tk.LEFT, padx=(0, 2))

        # Привязка событий к Entry для обработки ввода
        self.scale_entry.bind("<Return>", self.controller.handle_scale_entry_change) # При нажатии Enter
        self.scale_entry.bind("<FocusOut>", self.controller.handle_scale_entry_change) # При потере фокуса

        # Кнопка уменьшения масштаба
        self.scale_down_button = tk.Button(
            self.bottom_control_frame,
            text="▼", # Стрелка вниз (или "-")
            width=2,
            command=self.controller.handle_scale_down
        )
        self.scale_down_button.pack(side=tk.LEFT, padx=(0, 2))

        # Кнопка увеличения масштаба
        self.scale_up_button = tk.Button(
            self.bottom_control_frame,
            text="▲", # Стрелка вверх (или "+")
            width=2,
            command=self.controller.handle_scale_up
        )
        self.scale_up_button.pack(side=tk.LEFT, padx=0)

        # Изначально элементы управления масштабом недоступны
        self.scale_entry.config(state=tk.DISABLED)
        self.scale_down_button.config(state=tk.DISABLED)
        self.scale_up_button.config(state=tk.DISABLED)
        # --- Конец нового управления масштабом ---

        # --- Холст для отображения с прокруткой (без изменений) ---
        canvas_frame = tk.Frame(self.frame)
        canvas_frame.pack(pady=10, padx=10, expand=True, fill=tk.BOTH)

        self.h_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        self.v_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL)

        self.canvas = tk.Canvas(canvas_frame,
                                bg=BACKGROUND_COLOR,
                                relief=tk.SUNKEN, borderwidth=1,
                                xscrollcommand=self.h_scrollbar.set,
                                yscrollcommand=self.v_scrollbar.set)

        self.h_scrollbar.config(command=self.canvas.xview)
        self.v_scrollbar.config(command=self.canvas.yview)

        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        # Биндинги холста (без изменений)
        self.canvas.bind("<ButtonPress-1>", self.controller.handle_canvas_press)
        self.canvas.bind("<B1-Motion>", self.controller.handle_canvas_drag)
        self.canvas.bind("<Configure>", self.controller.handle_canvas_configure)

    # --- Методы обновления View ---

    def update_canvas(self, image_to_display, template_pixels, template_pos_rc):
        """ Отображает изображение и ТЕКУЩИЙ шаблон поверх него. (Без изменений) """
        self.canvas.delete("all")
        self._photo_image = None

        if image_to_display is None:
            self.canvas.config(scrollregion=(0, 0, 1, 1), width=100, height=100, bg=BACKGROUND_COLOR)
            self._img_original_height, self._img_original_width = 1, 1
            self._display_width, self._display_height = 1, 1
            self._current_scale = 1.0
            return

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width <= 1: canvas_width = self._display_width if self._display_width > 1 else 400
        if canvas_height <= 1: canvas_height = self._display_height if self._display_height > 1 else 400

        self._img_original_height, self._img_original_width = image_to_display.shape[:2]

        if self._img_original_width > 0 and self._img_original_height > 0:
            scale_x = canvas_width / self._img_original_width
            scale_y = canvas_height / self._img_original_height
            scale = min(scale_x, scale_y)
        else: scale = 1.0
        if scale <= 0: scale = 1.0
        self._current_scale = scale # Масштаб отображения картинки

        self._display_width = int(self._img_original_width * scale)
        self._display_height = int(self._img_original_height * scale)

        resized_image = None
        if self._display_width > 0 and self._display_height > 0:
            try:
                interpolation = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR
                resized_image = cv2.resize(image_to_display, (self._display_width, self._display_height), interpolation=interpolation)
            except cv2.error as e:
                print(f"Error resizing image with OpenCV: {e}")
                self.canvas.config(scrollregion=(0, 0, 1, 1), width=100, height=100, bg=BACKGROUND_COLOR)
                return
        else:
            resized_image = np.zeros((10, 10), dtype=image_to_display.dtype)
            self._display_width, self._display_height = 10, 10

        try:
            pil_image = Image.fromarray(resized_image)
            self._photo_image = ImageTk.PhotoImage(image=pil_image)
        except Exception as e:
            print(f"Error converting image for Tkinter: {e}")
            self.canvas.config(scrollregion=(0, 0, 1, 1), width=100, height=100, bg=BACKGROUND_COLOR)
            return

        self.canvas.create_image(0, 0, anchor=tk.NW, image=self._photo_image, tags="background_image")
        self.canvas.config(scrollregion=(0, 0, self._display_width, self._display_height))

        if template_pixels is not None and template_pos_rc != (-1,-1) and self._current_scale > 0:
            tpl_rows, tpl_cols = template_pixels.shape
            start_row, start_col = template_pos_rc

            scaled_pixel_side = self._current_scale
            min_pixel_size = 1.0
            draw_pixel_w = max(min_pixel_size, scaled_pixel_side)
            draw_pixel_h = max(min_pixel_size, scaled_pixel_side)

            for r_tpl in range(tpl_rows):
                for c_tpl in range(tpl_cols):
                    if template_pixels[r_tpl, c_tpl] == 1:
                        r_img, c_img = start_row + r_tpl, start_col + c_tpl
                        x0 = c_img * self._current_scale
                        y0 = r_img * self._current_scale
                        x1 = x0 + draw_pixel_w
                        y1 = y0 + draw_pixel_h
                        self.canvas.create_rectangle(x0, y0, x1, y1, fill=TEMPLATE_PIXEL_COLOR, outline="", tags="template_pixel")

    def update_info_label(self, score, pos_rc):
        """ Обновляет метку с результатом и позицией шаблона. (Без изменений) """
        r, c = pos_rc
        if score is None or score == -np.inf or r == -1:
             score_str = "-"
             pos_str = "(-, -)"
        else:
             try:
                 f_score = float(score)
                 if -1.0001 <= f_score <= 1.0001: score_str = f"{f_score:.4f}"
                 else: score_str = f"{f_score:.0f}"
             except (ValueError, TypeError): score_str = "?"
             pos_str = f"({r}, {c})"
        self.info_label.config(text=f"Результат: {score_str} | Позиция: {pos_str}")

    # --- ИЗМЕНЕНО: Метод обновления для Entry и кнопок ---
    def update_scale_controls(self, scale_value, state=tk.NORMAL):
        """ Обновляет значение в поле Entry и состояние элементов управления масштабом """
        # Форматируем значение для отображения (например, 1 знак после запятой)
        formatted_value = f"{scale_value:.1f}"
        self.scale_entry_var.set(formatted_value)

        # Устанавливаем состояние для Entry и кнопок
        entry_state = state
        button_state = state

        # Дополнительная логика: отключаем кнопки +/- на границах (если нужно)
        # Например, если scale_value <= 0.1, отключить кнопку "вниз"
        # if state == tk.NORMAL and scale_value <= SCALE_INCREMENT:
        #     button_down_state = tk.DISABLED
        # else:
        #     button_down_state = button_state
        # self.scale_down_button.config(state=button_down_state)

        self.scale_entry.config(state=entry_state)
        self.scale_down_button.config(state=button_state)
        self.scale_up_button.config(state=button_state)

    def get_original_coords_from_canvas(self, canvas_x, canvas_y):
        """ Преобразует координаты холста в координаты изображения. (Без изменений) """
        if self._current_scale <= 0: return 0, 0
        scaled_x = self.canvas.canvasx(canvas_x)
        scaled_y = self.canvas.canvasy(canvas_y)
        original_col = int(scaled_x / self._current_scale)
        original_row = int(scaled_y / self._current_scale)
        if self._img_original_height > 0 and self._img_original_width > 0:
            original_row = min(original_row, self._img_original_height - 1)
            original_col = min(original_col, self._img_original_width - 1)
        original_row = max(0, original_row)
        original_col = max(0, original_col)
        return original_row, original_col

    def set_widget_state(self, widget_name, state):
        """ Управляет состоянием виджетов (normal/disabled) """
        widget = getattr(self, widget_name, None)
        if widget:
            # Обработка для новых виджетов масштаба
            if widget_name in ["scale_entry", "scale_down_button", "scale_up_button"]:
                 # Используем общий метод обновления, который сам установит состояние
                 # Но нам нужно знать текущее значение масштаба из модели,
                 # поэтому этот метод не очень подходит для прямого вызова извне для этих виджетов.
                 # Контроллер должен вызывать update_scale_controls.
                 # Здесь просто пропустим или вызовем config напрямую.
                 try:
                     # Убедимся, что состояние допустимо (normal или disabled)
                     valid_state = state if state in [tk.NORMAL, tk.DISABLED] else tk.DISABLED
                     widget.config(state=valid_state)
                 except tk.TclError as e:
                     print(f"Warning: Could not set state '{state}' for widget '{widget_name}'. Error: {e}")
            else:
                # Стандартная обработка для других виджетов
                try:
                    valid_state = state if state in [tk.NORMAL, tk.DISABLED] else tk.DISABLED
                    widget.config(state=valid_state)
                except tk.TclError as e:
                    print(f"Warning: Could not set state '{state}' for widget '{widget_name}'. Error: {e}")
        else:
            print(f"Warning: Widget '{widget_name}' not found in ComparisonView.")

    def show_error(self, title, message):
        messagebox.showerror(title, message, parent=self.frame)

    def show_info(self, title, message):
        messagebox.showinfo(title, message, parent=self.frame)

    # --- Дополнительно: метод для получения значения из Entry ---
    def get_scale_entry_value(self):
        """ Возвращает значение из поля ввода масштаба как строку """
        return self.scale_entry_var.get()