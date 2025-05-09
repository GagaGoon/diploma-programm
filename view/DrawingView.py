# view/DrawingView.py
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk # Добавляем PIL для оверлея

# Константа для размера пикселя на холсте редактора
DRAWING_PIXEL_SIZE = 15
# Цвет неактивных пикселей (для прозрачности не используется, но нужен для контура)
INACTIVE_PIXEL_BG = '#F0F0F0'
# Цвет контура неактивных пикселей (чтобы сетка была видна поверх оверлея)
GRID_OUTLINE_COLOR = '#D0D0D0'
# Цвет активных пикселей
ACTIVE_PIXEL_COLOR = 'blue'

class DrawingView:
    """
    Представление (View) для редактора шаблонов.
    Добавлено поле для ввода физической высоты шаблона.
    ИСПРАВЛЕНО: Синтаксис в get_size_entries, get_vertex_entries, clear_vertex_entries, show_error, show_info, set_widget_state.
    """
    def __init__(self, parent_frame, controller):
        self.frame = parent_frame
        self.controller = controller
        self._overlay_photo = None # Храним PhotoImage для оверлея

        # --- Верхняя панель: Файловые операции ---
        self.file_frame = tk.Frame(self.frame)
        self.file_frame.pack(pady=5, fill=tk.X, padx=10)

        self.save_template_button = tk.Button(self.file_frame, text="Сохранить как шаблон", command=self.controller.save_as_template)
        self.save_template_button.pack(side=tk.LEFT, padx=5)

        self.load_overlay_button = tk.Button(self.file_frame, text="Наложить изображение", command=self.controller.handle_load_overlay)
        self.load_overlay_button.pack(side=tk.LEFT, padx=5)

        self.load_button = tk.Button(self.file_frame, text="Загрузить шаблон", command=self.controller.load_from_xml)
        self.load_button.pack(side=tk.LEFT, padx=5)

        # --- Панель управления размером сетки ---
        self.size_frame = tk.Frame(self.frame)
        self.size_frame.pack(pady=5, fill=tk.X, padx=10)

        tk.Label(self.size_frame, text="Строк сетки:").pack(side=tk.LEFT)
        self.rows_entry = tk.Entry(self.size_frame, width=5)
        self.rows_entry.pack(side=tk.LEFT, padx=(0,5))

        tk.Label(self.size_frame, text="Столбцов сетки:").pack(side=tk.LEFT)
        self.cols_entry = tk.Entry(self.size_frame, width=5)
        self.cols_entry.pack(side=tk.LEFT, padx=(0,10))

        self.apply_button = tk.Button(self.size_frame, text="Применить размер сетки", command=self.controller.apply_size)
        self.apply_button.pack(side=tk.LEFT, padx=5)

        # --- Панель физической высоты шаблона ---
        self.physical_size_frame = tk.Frame(self.frame)
        self.physical_size_frame.pack(pady=5, fill=tk.X, padx=10)
        tk.Label(self.physical_size_frame, text="Высота шаблона (метры):").pack(side=tk.LEFT)
        self.physical_height_entry_var = tk.StringVar()
        self.physical_height_entry = tk.Entry(self.physical_size_frame, textvariable=self.physical_height_entry_var, width=7)
        self.physical_height_entry.pack(side=tk.LEFT, padx=(0,5))
        self.physical_height_entry.bind("<Return>", self.controller.handle_physical_height_entry_change)
        self.physical_height_entry.bind("<FocusOut>", self.controller.handle_physical_height_entry_change)

        # --- Панель добавления вершин вручную + Undo/Redo + Clear ---
        self.input_frame = tk.Frame(self.frame)
        self.input_frame.pack(pady=5, fill=tk.X, padx=10)
        tk.Label(self.input_frame, text="Вершина:").pack(side=tk.LEFT)
        tk.Label(self.input_frame, text="X:").pack(side=tk.LEFT, padx=(5,0))
        self.x_entry = tk.Entry(self.input_frame, width=5)
        self.x_entry.pack(side=tk.LEFT, padx=(0,5))
        tk.Label(self.input_frame, text="Y:").pack(side=tk.LEFT)
        self.y_entry = tk.Entry(self.input_frame, width=5)
        self.y_entry.pack(side=tk.LEFT, padx=(0,5))
        self.add_button = tk.Button(self.input_frame, text="+", command=self.controller.add_vertex_by_input, width=3)
        self.add_button.pack(side=tk.LEFT, padx=5)
        self.undo_button = tk.Button(self.input_frame, text="Undo", command=self.controller.handle_undo, width=4, state=tk.DISABLED)
        self.undo_button.pack(side=tk.LEFT, padx=(0,2))
        self.redo_button = tk.Button(self.input_frame, text="Redo", command=self.controller.handle_redo, width=4, state=tk.DISABLED)
        self.redo_button.pack(side=tk.LEFT, padx=(0,5))
        self.clear_button = tk.Button(self.input_frame, text="Очистить поле", command=self.controller.clear_field)
        self.clear_button.pack(side=tk.LEFT, padx=5)

        # --- Панель управления оверлеем ---
        self.overlay_control_frame = tk.Frame(self.frame)
        self.overlay_control_frame.pack(pady=5, fill=tk.X, padx=10)
        tk.Label(self.overlay_control_frame, text="Изменить изображение:").pack(side=tk.LEFT, padx=(0, 10))
        self.overlay_left_btn = tk.Button(self.overlay_control_frame, text="←", width=3, command=lambda: self.controller.handle_move_overlay(-10, 0), state=tk.DISABLED); self.overlay_left_btn.pack(side=tk.LEFT, padx=1)
        self.overlay_right_btn = tk.Button(self.overlay_control_frame, text="→", width=3, command=lambda: self.controller.handle_move_overlay(10, 0), state=tk.DISABLED); self.overlay_right_btn.pack(side=tk.LEFT, padx=1)
        self.overlay_up_btn = tk.Button(self.overlay_control_frame, text="↑", width=3, command=lambda: self.controller.handle_move_overlay(0, -10), state=tk.DISABLED); self.overlay_up_btn.pack(side=tk.LEFT, padx=1)
        self.overlay_down_btn = tk.Button(self.overlay_control_frame, text="↓", width=3, command=lambda: self.controller.handle_move_overlay(0, 10), state=tk.DISABLED); self.overlay_down_btn.pack(side=tk.LEFT, padx=1)
        self.overlay_zoom_in_btn = tk.Button(self.overlay_control_frame, text="+", width=3, command=lambda: self.controller.handle_scale_overlay(1.1), state=tk.DISABLED); self.overlay_zoom_in_btn.pack(side=tk.LEFT, padx=(5,1))
        self.overlay_zoom_out_btn = tk.Button(self.overlay_control_frame, text="-", width=3, command=lambda: self.controller.handle_scale_overlay(1/1.1), state=tk.DISABLED); self.overlay_zoom_out_btn.pack(side=tk.LEFT, padx=1)

        # --- Метка для отображения списка вершин ---
        self.vertex_display_frame = tk.Frame(self.frame)
        self.vertex_display_frame.pack(pady=5, fill=tk.X, padx=10)
        tk.Label(self.vertex_display_frame, text="Вершины:", anchor='w').pack(side=tk.LEFT)
        self.vertices_label = tk.Label(self.vertex_display_frame, text="", font=("Arial", 10), anchor='w', justify=tk.LEFT, wraplength=500)
        self.vertices_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # --- Холст для пикселей с прокруткой ---
        self.canvas_frame = tk.Frame(self.frame)
        self.canvas_frame.pack(pady=10, padx=10, expand=True, fill=tk.BOTH)
        self.h_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL)
        self.v_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL)
        self.canvas = tk.Canvas(self.canvas_frame, bg='white', relief=tk.SUNKEN, borderwidth=1, xscrollcommand=self.h_scrollbar.set, yscrollcommand=self.v_scrollbar.set)
        self.h_scrollbar.config(command=self.canvas.xview)
        self.v_scrollbar.config(command=self.canvas.yview)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        self.canvas.bind("<Button-1>", self.controller.canvas_click_handler)

        self.update_size_entries(self.controller.model.rows, self.controller.model.cols)
        self.update_physical_height_entry(self.controller.model.template_physical_height_meters)

    def update_canvas(self, pixel_field):
        self.canvas.delete("all"); self._overlay_photo = None; rows = len(pixel_field); cols = len(pixel_field[0]) if rows > 0 else 0
        canvas_width = cols * DRAWING_PIXEL_SIZE; canvas_height = rows * DRAWING_PIXEL_SIZE
        overlay_img_pil, ox, oy, scale = self.controller.model.get_overlay_data()
        if overlay_img_pil:
            try:
                overlay_w = int(overlay_img_pil.width * scale); overlay_h = int(overlay_img_pil.height * scale)
                if overlay_w > 0 and overlay_h > 0:
                    try: resampling_method = Image.Resampling.LANCZOS
                    except AttributeError: resampling_method = Image.LANCZOS
                    scaled_overlay = overlay_img_pil.resize((overlay_w, overlay_h), resampling_method)
                    self._overlay_photo = ImageTk.PhotoImage(scaled_overlay)
                    self.canvas.create_image(ox, oy, anchor=tk.NW, image=self._overlay_photo, tags="overlay")
            except Exception as e: print(f"Ошибка оверлея: {e}"); self._overlay_photo = None
        for r in range(rows):
            for c in range(cols):
                x0 = c * DRAWING_PIXEL_SIZE; y0 = r * DRAWING_PIXEL_SIZE; x1 = x0 + DRAWING_PIXEL_SIZE; y1 = y0 + DRAWING_PIXEL_SIZE
                if pixel_field[r][c] == 1: self.canvas.create_rectangle(x0, y0, x1, y1, fill=ACTIVE_PIXEL_COLOR, outline='white', width=1, tags="pixel_active")
                else: self.canvas.create_rectangle(x0, y0, x1, y1, fill="", outline=GRID_OUTLINE_COLOR, width=1, tags="pixel_inactive_outline")
        self.canvas.config(scrollregion=(0, 0, canvas_width, canvas_height))

    def update_vertices_label(self, vertices_string):
        self.vertices_label.config(text=vertices_string)

    def update_size_entries(self, rows, cols):
        self.rows_entry.delete(0, tk.END); self.rows_entry.insert(0, str(rows))
        self.cols_entry.delete(0, tk.END); self.cols_entry.insert(0, str(cols))

    def update_physical_height_entry(self, height_meters):
        self.physical_height_entry_var.set(f"{height_meters:.3f}")

    def get_physical_height_entry(self):
        try:
            value_str = self.physical_height_entry_var.get().replace(',', '.')
            return float(value_str)
        except ValueError:
            self.show_error("Ошибка ввода", "Физическая высота шаблона должна быть числом.")
            return None

    # --- ИСПРАВЛЕННЫЙ СИНТАКСИС ---
    def get_size_entries(self):
        try:
            return int(self.rows_entry.get()), int(self.cols_entry.get())
        except ValueError:
            self.show_error("Ошибка ввода", "Размеры сетки должны быть целыми числами.")
            return None, None

    def get_vertex_entries(self):
        try:
            return int(self.x_entry.get()), int(self.y_entry.get())
        except ValueError:
            self.show_error("Ошибка ввода", "Координаты вершин должны быть целыми числами.")
            return None, None

    def clear_vertex_entries(self):
        self.x_entry.delete(0, tk.END)
        self.y_entry.delete(0, tk.END)

    def show_error(self, title, message):
        messagebox.showerror(title, message, parent=self.frame)

    def show_info(self, title, message):
        messagebox.showinfo(title, message, parent=self.frame)

    def set_widget_state(self, widget_name, state):
        widget = getattr(self, widget_name, None)
        if widget:
            try:
                valid_state = state if state in [tk.NORMAL, tk.DISABLED] else tk.DISABLED
                widget.config(state=valid_state)
            except tk.TclError as e:
                print(f"Warning: Could not set state '{state}' for widget '{widget_name}'. Error: {e}")
        else:
            print(f"Warning: Widget '{widget_name}' not found in DrawingView.")