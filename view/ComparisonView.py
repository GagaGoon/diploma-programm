# view/ComparisonView.py
import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import cv2
from PIL import Image, ImageTk

BACKGROUND_COLOR = '#F0F0F0'
TEMPLATE_PIXEL_COLOR = 'red'
GAUSS_ACTIVE_BG = '#90EE90'

class ComparisonView:
    """
    Представление (View) для вкладки сравнения.
    ИЗМЕНЕНО: Добавлено поле для ввода/отображения угла.
    """
    def __init__(self, parent_frame, controller):
        self.frame = parent_frame
        self.controller = controller
        self._photo_image = None; self._current_scale = 1.0
        self._img_original_width = 1; self._img_original_height = 1
        self._display_width = 1; self._display_height = 1
        self._default_button_bg = None

        # --- Панель загрузки ---
        self.load_frame = tk.Frame(self.frame)
        self.load_frame.pack(pady=5, padx=10, fill=tk.X)
        self.load_image_button = tk.Button(self.load_frame, text="Загрузить изображение (jpg, png...)", command=self.controller.handle_load_image)
        self.load_image_button.pack(side=tk.LEFT, padx=5)
        self.load_template_button = tk.Button(self.load_frame, text="Загрузить шаблон (.xml)", command=self.controller.handle_load_template)
        self.load_template_button.pack(side=tk.LEFT, padx=5)
        self.load_template_button.config(state=tk.DISABLED)

        # --- Панель управления ---
        self.control_frame = tk.Frame(self.frame)
        self.control_frame.pack(pady=5, padx=10, fill=tk.X)

        # --- 1. Верхняя строка: Поиск, Результат, Поворот, Поле Угла ---
        self.top_control_frame = tk.Frame(self.control_frame)
        self.top_control_frame.pack(fill=tk.X, pady=(0, 5))

        self.find_best_button = tk.Button(self.top_control_frame, text="Найти лучшее совпадение", command=self.controller.handle_find_best_match)
        self.find_best_button.pack(side=tk.LEFT, padx=5)
        self.find_best_button.config(state=tk.DISABLED)

        self.info_label = tk.Label(self.top_control_frame, text="Результат: - | Позиция: (-, -)") # Угол убран отсюда
        self.info_label.pack(side=tk.LEFT, padx=10)

        # Кнопки поворота шаблона
        self.rotate_left_button = tk.Button(self.top_control_frame, text="↺", command=self.controller.handle_rotate_template_left, width=3, state=tk.DISABLED)
        self.rotate_left_button.pack(side=tk.LEFT, padx=(10, 0)) # Убрал правый отступ

        # --- ДОБАВЛЕНО: Поле для ввода/отображения угла ---
        tk.Label(self.top_control_frame, text="Угол:").pack(side=tk.LEFT, padx=(5,0))
        self.angle_entry_var = tk.StringVar(value="0.0")
        self.angle_entry = tk.Entry(self.top_control_frame, textvariable=self.angle_entry_var, width=5, state=tk.DISABLED)
        self.angle_entry.pack(side=tk.LEFT, padx=(0,2))
        self.angle_entry.bind("<Return>", self.controller.handle_angle_entry_change)
        self.angle_entry.bind("<FocusOut>", self.controller.handle_angle_entry_change)
        # --- КОНЕЦ ДОБАВЛЕНИЯ ПОЛЯ УГЛА ---

        self.rotate_right_button = tk.Button(self.top_control_frame, text="↻", command=self.controller.handle_rotate_template_right, width=3, state=tk.DISABLED)
        self.rotate_right_button.pack(side=tk.LEFT, padx=0)


        # --- 2. Средняя строка: Фильтры ---
        self.filter_control_frame = tk.Frame(self.control_frame)
        self.filter_control_frame.pack(fill=tk.X, pady=(0, 5))
        self.gauss_button = tk.Button(self.filter_control_frame, text="Гаусс", command=self.controller.handle_toggle_gauss)
        self.gauss_button.pack(side=tk.LEFT, padx=5)
        if self._default_button_bg is None:
             try: self._default_button_bg = self.gauss_button.cget('background')
             except tk.TclError: self._default_button_bg = BACKGROUND_COLOR
        self.gauss_button.config(state=tk.DISABLED, bg=self._default_button_bg)
        self.sobel_button = tk.Button(self.filter_control_frame, text="Собель", command=self.controller.handle_apply_sobel); self.sobel_button.pack(side=tk.LEFT, padx=5); self.sobel_button.config(state=tk.DISABLED)
        self.kirsch_button = tk.Button(self.filter_control_frame, text="Кирш", command=self.controller.handle_apply_kirsch); self.kirsch_button.pack(side=tk.LEFT, padx=5); self.kirsch_button.config(state=tk.DISABLED)
        self.roberts_button = tk.Button(self.filter_control_frame, text="Робертс", command=self.controller.handle_apply_roberts); self.roberts_button.pack(side=tk.LEFT, padx=5); self.roberts_button.config(state=tk.DISABLED)
        self.prewitt_button = tk.Button(self.filter_control_frame, text="Превитт", command=self.controller.handle_apply_prewitt); self.prewitt_button.pack(side=tk.LEFT, padx=5); self.prewitt_button.config(state=tk.DISABLED)

        # --- 3. Нижняя строка: Управление физическим масштабом ИЗОБРАЖЕНИЯ ---
        self.image_scale_control_frame = tk.Frame(self.control_frame)
        self.image_scale_control_frame.pack(fill=tk.X)
        tk.Label(self.image_scale_control_frame, text="Масштаб изобр. (м/пкс):").pack(side=tk.LEFT)
        self.image_m_per_px_var = tk.StringVar(value="0.0000")
        self.image_m_per_px_entry = tk.Entry(self.image_scale_control_frame, textvariable=self.image_m_per_px_var, width=8, state=tk.DISABLED)
        self.image_m_per_px_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.image_m_per_px_entry.bind("<Return>", self.controller.handle_image_m_per_px_entry_change)
        self.image_m_per_px_entry.bind("<FocusOut>", self.controller.handle_image_m_per_px_entry_change)
        tk.Label(self.image_scale_control_frame, text="Высота изобр. (метры):").pack(side=tk.LEFT)
        self.image_phys_height_var = tk.StringVar(value="0.00")
        self.image_phys_height_entry = tk.Entry(self.image_scale_control_frame, textvariable=self.image_phys_height_var, width=7, state=tk.DISABLED)
        self.image_phys_height_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.image_phys_height_entry.bind("<Return>", self.controller.handle_image_phys_height_entry_change)
        self.image_phys_height_entry.bind("<FocusOut>", self.controller.handle_image_phys_height_entry_change)

        # --- Холст для отображения с прокруткой ---
        canvas_frame = tk.Frame(self.frame); canvas_frame.pack(pady=10, padx=10, expand=True, fill=tk.BOTH)
        self.h_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL); self.v_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        self.canvas = tk.Canvas(canvas_frame, bg=BACKGROUND_COLOR, relief=tk.SUNKEN, borderwidth=1, xscrollcommand=self.h_scrollbar.set, yscrollcommand=self.v_scrollbar.set)
        self.h_scrollbar.config(command=self.canvas.xview); self.v_scrollbar.config(command=self.canvas.yview)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X); self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y); self.canvas.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        self.canvas.bind("<ButtonPress-1>", self.controller.handle_canvas_press); self.canvas.bind("<B1-Motion>", self.controller.handle_canvas_drag); self.canvas.bind("<Configure>", self.controller.handle_canvas_configure)

    def update_canvas(self, image_to_display, template_pixels, template_pos_rc):
        self.canvas.delete("all"); self._photo_image = None
        if image_to_display is None: self.canvas.config(scrollregion=(0, 0, 1, 1), width=100, height=100, bg=BACKGROUND_COLOR); self._img_original_height, self._img_original_width = 1, 1; self._display_width, self._display_height = 1, 1; self._current_scale = 1.0; return
        canvas_width = self.canvas.winfo_width(); canvas_height = self.canvas.winfo_height()
        if canvas_width <= 1: canvas_width = self._display_width if self._display_width > 1 else 400
        if canvas_height <= 1: canvas_height = self._display_height if self._display_height > 1 else 400
        self._img_original_height, self._img_original_width = image_to_display.shape[:2]
        if self._img_original_width > 0 and self._img_original_height > 0: scale = min(canvas_width / self._img_original_width, canvas_height / self._img_original_height)
        else: scale = 1.0
        if scale <= 0: scale = 1.0
        self._current_scale = scale
        self._display_width = int(self._img_original_width * scale); self._display_height = int(self._img_original_height * scale)
        resized_image = None
        if self._display_width > 0 and self._display_height > 0:
            try: interpolation = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR; resized_image = cv2.resize(image_to_display, (self._display_width, self._display_height), interpolation=interpolation)
            except cv2.error as e: print(f"Error resizing image: {e}"); self.canvas.config(scrollregion=(0, 0, 1, 1), width=100, height=100, bg=BACKGROUND_COLOR); return
        else: resized_image = np.zeros((10, 10), dtype=image_to_display.dtype); self._display_width, self._display_height = 10, 10
        try: pil_image = Image.fromarray(resized_image); self._photo_image = ImageTk.PhotoImage(image=pil_image)
        except Exception as e: print(f"Error converting image: {e}"); self.canvas.config(scrollregion=(0, 0, 1, 1), width=100, height=100, bg=BACKGROUND_COLOR); return
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self._photo_image, tags="background_image")
        self.canvas.config(scrollregion=(0, 0, self._display_width, self._display_height))
        if template_pixels is not None and template_pos_rc != (-1,-1) and self._current_scale > 0:
            tpl_rows, tpl_cols = template_pixels.shape; start_row, start_col = template_pos_rc
            scaled_pixel_side = self._current_scale; min_pixel_size = 1.0
            draw_pixel_w = max(min_pixel_size, scaled_pixel_side); draw_pixel_h = max(min_pixel_size, scaled_pixel_side)
            for r_tpl in range(tpl_rows):
                for c_tpl in range(tpl_cols):
                    if template_pixels[r_tpl, c_tpl] == 1:
                        r_img, c_img = start_row + r_tpl, start_col + c_tpl
                        x0 = c_img * self._current_scale; y0 = r_img * self._current_scale
                        x1 = x0 + draw_pixel_w; y1 = y0 + draw_pixel_h
                        self.canvas.create_rectangle(x0, y0, x1, y1, fill=TEMPLATE_PIXEL_COLOR, outline="", tags="template_pixel")

    def update_info_label(self, score, pos_rc, angle_deg=0): # Угол убран из этой метки
        r, c = pos_rc
        if score is None or score == -np.inf or r == -1: score_str = "-"; pos_str = "(-, -)"
        else:
             try: f_score = float(score); score_str = f"{f_score:.4f}"
             except (ValueError, TypeError): score_str = "?"
             pos_str = f"({r}, {c})"
        self.info_label.config(text=f"Результат: {score_str} | Позиция: {pos_str}") # Угол теперь в отдельном поле

    def update_image_parameters_entries(self, m_per_px, phys_height_m, state=tk.NORMAL):
        self.image_m_per_px_var.set(f"{m_per_px:.4f}")
        self.image_phys_height_var.set(f"{phys_height_m:.2f}")
        entry_state = state if state != tk.DISABLED else 'readonly'
        self.image_m_per_px_entry.config(state=entry_state)
        self.image_phys_height_entry.config(state=entry_state)

    def get_image_m_per_px_entry(self):
        try: return float(self.image_m_per_px_var.get().replace(',', '.'))
        except ValueError: self.show_error("Ошибка ввода", "Масштаб изображения (м/пкс) должен быть числом."); return None

    def get_image_phys_height_entry(self):
        try: return float(self.image_phys_height_var.get().replace(',', '.'))
        except ValueError: self.show_error("Ошибка ввода", "Физическая высота изображения должна быть числом."); return None

    # --- НОВЫЕ МЕТОДЫ для поля угла ---
    def update_angle_entry(self, angle_degrees, state=tk.NORMAL):
        self.angle_entry_var.set(f"{angle_degrees:.1f}")
        entry_state = state if state != tk.DISABLED else 'readonly'
        self.angle_entry.config(state=entry_state)

    def get_angle_entry_value(self):
        return self.angle_entry_var.get()
    # --- КОНЕЦ НОВЫХ МЕТОДОВ ---

    def update_gauss_button_visuals(self, is_active, state=tk.NORMAL):
        bg_color = GAUSS_ACTIVE_BG if is_active else (self._default_button_bg if self._default_button_bg else BACKGROUND_COLOR)
        try: self.gauss_button.config(state=state, bg=bg_color, activebackground=bg_color)
        except tk.TclError: pass

    def get_original_coords_from_canvas(self, canvas_x, canvas_y):
        if self._current_scale <= 0: return 0, 0
        scaled_x = self.canvas.canvasx(canvas_x); scaled_y = self.canvas.canvasy(canvas_y)
        original_col = int(scaled_x / self._current_scale); original_row = int(scaled_y / self._current_scale)
        if self._img_original_height > 0 and self._img_original_width > 0:
            original_row = min(original_row, self._img_original_height - 1); original_col = min(original_col, self._img_original_width - 1)
        original_row = max(0, original_row); original_col = max(0, original_col)
        return original_row, original_col

    def set_widget_state(self, widget_name, state):
        widget = getattr(self, widget_name, None)
        if widget:
            try:
                valid_state = state if state in [tk.NORMAL, tk.DISABLED] else tk.DISABLED
                if widget_name == "gauss_button": self.update_gauss_button_visuals(self.controller.model.gaussian_blur_active, valid_state)
                elif widget_name in ["image_m_per_px_entry", "image_phys_height_entry", "angle_entry"]:
                    widget.config(state=(valid_state if valid_state == tk.NORMAL else 'readonly'))
                else: widget.config(state=valid_state)
            except tk.TclError as e: print(f"Warning: Could not set state '{state}' for widget '{widget_name}'. Error: {e}")
        else: print(f"Warning: Widget '{widget_name}' not found in ComparisonView.")

    def show_error(self, title, message): messagebox.showerror(title, message, parent=self.frame)
    def show_info(self, title, message): messagebox.showinfo(title, message, parent=self.frame)