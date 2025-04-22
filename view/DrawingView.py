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
    ДОБАВЛЕНО: Scrollbars, Undo/Redo, Overlay Image + Controls.
    ИЗМЕНЕНО: Расположение кнопок, логика отрисовки Canvas.
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

        # Кнопка "Сохранить как изображение" ЗАМЕНЕНА на "Наложить изображение"
        self.load_overlay_button = tk.Button(self.file_frame, text="Наложить изображение", command=self.controller.handle_load_overlay)
        self.load_overlay_button.pack(side=tk.LEFT, padx=5)

        self.load_button = tk.Button(self.file_frame, text="Загрузить шаблон", command=self.controller.load_from_xml)
        self.load_button.pack(side=tk.LEFT, padx=5)

        # --- Панель управления размером ---
        self.size_frame = tk.Frame(self.frame)
        self.size_frame.pack(pady=5, fill=tk.X, padx=10)

        tk.Label(self.size_frame, text="Строк:").pack(side=tk.LEFT)
        self.rows_entry = tk.Entry(self.size_frame, width=5)
        self.rows_entry.pack(side=tk.LEFT, padx=(0,5))

        tk.Label(self.size_frame, text="Столбцов:").pack(side=tk.LEFT)
        self.cols_entry = tk.Entry(self.size_frame, width=5)
        self.cols_entry.pack(side=tk.LEFT, padx=(0,10))

        self.apply_button = tk.Button(self.size_frame, text="Применить размер", command=self.controller.apply_size)
        self.apply_button.pack(side=tk.LEFT, padx=5)
        # Кнопка "Очистить поле" перенесена ниже

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

        # Кнопки Undo/Redo
        self.undo_button = tk.Button(self.input_frame, text="Undo", command=self.controller.handle_undo, width=4, state=tk.DISABLED)
        self.undo_button.pack(side=tk.LEFT, padx=(0,2))
        self.redo_button = tk.Button(self.input_frame, text="Redo", command=self.controller.handle_redo, width=4, state=tk.DISABLED)
        self.redo_button.pack(side=tk.LEFT, padx=(0,5))

        # Кнопка "Очистить поле" перенесена сюда
        self.clear_button = tk.Button(self.input_frame, text="Очистить поле", command=self.controller.clear_field)
        self.clear_button.pack(side=tk.LEFT, padx=5) # Или side=tk.RIGHT, если нужно справа

        # --- Панель управления оверлеем ---
        self.overlay_control_frame = tk.Frame(self.frame)
        self.overlay_control_frame.pack(pady=5, fill=tk.X, padx=10)

        tk.Label(self.overlay_control_frame, text="Изменить изображение:").pack(side=tk.LEFT, padx=(0, 10))

        # Кнопки управления оверлеем
        self.overlay_left_btn = tk.Button(self.overlay_control_frame, text="←", width=3, command=lambda: self.controller.handle_move_overlay(-10, 0), state=tk.DISABLED)
        self.overlay_left_btn.pack(side=tk.LEFT, padx=1)
        self.overlay_right_btn = tk.Button(self.overlay_control_frame, text="→", width=3, command=lambda: self.controller.handle_move_overlay(10, 0), state=tk.DISABLED)
        self.overlay_right_btn.pack(side=tk.LEFT, padx=1)
        self.overlay_up_btn = tk.Button(self.overlay_control_frame, text="↑", width=3, command=lambda: self.controller.handle_move_overlay(0, -10), state=tk.DISABLED)
        self.overlay_up_btn.pack(side=tk.LEFT, padx=1)
        self.overlay_down_btn = tk.Button(self.overlay_control_frame, text="↓", width=3, command=lambda: self.controller.handle_move_overlay(0, 10), state=tk.DISABLED)
        self.overlay_down_btn.pack(side=tk.LEFT, padx=1)
        self.overlay_zoom_in_btn = tk.Button(self.overlay_control_frame, text="+", width=3, command=lambda: self.controller.handle_scale_overlay(1.1), state=tk.DISABLED)
        self.overlay_zoom_in_btn.pack(side=tk.LEFT, padx=(5,1))
        self.overlay_zoom_out_btn = tk.Button(self.overlay_control_frame, text="-", width=3, command=lambda: self.controller.handle_scale_overlay(1/1.1), state=tk.DISABLED)
        self.overlay_zoom_out_btn.pack(side=tk.LEFT, padx=1)

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

        self.canvas = tk.Canvas(self.canvas_frame,
                                bg='white', # Фон холста
                                relief=tk.SUNKEN, borderwidth=1,
                                xscrollcommand=self.h_scrollbar.set,
                                yscrollcommand=self.v_scrollbar.set)

        self.h_scrollbar.config(command=self.canvas.xview)
        self.v_scrollbar.config(command=self.canvas.yview)

        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, expand=True, fill=tk.BOTH) # Холст заполняет оставшееся место

        self.canvas.bind("<Button-1>", self.controller.canvas_click_handler)

        # Устанавливаем начальные значения размеров в поля ввода
        self.update_size_entries(self.controller.model.rows, self.controller.model.cols)

    def update_canvas(self, pixel_field):
        """
        Обновляет холст: рисует оверлей (если есть), затем сетку пикселей поверх.
        Неактивные пиксели не заливаются, чтобы был виден оверлей.
        """
        self.canvas.delete("all") # Очищаем холст
        self._overlay_photo = None # Сбрасываем ссылку на PhotoImage оверлея

        rows = len(pixel_field)
        cols = len(pixel_field[0]) if rows > 0 else 0

        # Рассчитываем необходимые размеры холста по сетке пикселей
        canvas_width = cols * DRAWING_PIXEL_SIZE
        canvas_height = rows * DRAWING_PIXEL_SIZE
        # Устанавливаем размер видимой области холста (не обязательно, т.к. есть pack)
        # self.canvas.config(width=canvas_width, height=canvas_height)

        # --- 1. Рисуем оверлейное изображение (если есть) ---
        overlay_img_pil, ox, oy, scale = self.controller.model.get_overlay_data()
        if overlay_img_pil:
            try:
                # Масштабируем PIL изображение
                overlay_w = int(overlay_img_pil.width * scale)
                overlay_h = int(overlay_img_pil.height * scale)
                # Используем LANCZOS для лучшего качества при масштабировании
                resampling_method = Image.Resampling.LANCZOS
                # Избегаем нулевых размеров
                if overlay_w > 0 and overlay_h > 0:
                    scaled_overlay = overlay_img_pil.resize((overlay_w, overlay_h), resampling_method)
                    self._overlay_photo = ImageTk.PhotoImage(scaled_overlay)
                    # Рисуем оверлей со смещением (ox, oy) относительно левого верхнего угла холста
                    self.canvas.create_image(ox, oy, anchor=tk.NW, image=self._overlay_photo, tags="overlay")
            except Exception as e:
                print(f"Ошибка при обработке или отрисовке оверлея: {e}")
                self._overlay_photo = None # Сбрасываем, если ошибка

        # --- 2. Рисуем сетку пикселей поверх оверлея ---
        for r in range(rows):
            for c in range(cols):
                x0 = c * DRAWING_PIXEL_SIZE
                y0 = r * DRAWING_PIXEL_SIZE
                x1 = x0 + DRAWING_PIXEL_SIZE
                y1 = y0 + DRAWING_PIXEL_SIZE

                if pixel_field[r][c] == 1:
                    # Рисуем активный пиксель (синий)
                    self.canvas.create_rectangle(x0, y0, x1, y1,
                                                 fill=ACTIVE_PIXEL_COLOR,
                                                 outline='white', # Контур активного пикселя
                                                 width=1, tags="pixel_active")
                else:
                    # Рисуем ТОЛЬКО КОНТУР неактивного пикселя (чтобы сетка была видна)
                    # Фон остается прозрачным (т.е. виден оверлей или фон холста)
                    self.canvas.create_rectangle(x0, y0, x1, y1,
                                                 fill="", # НЕ ЗАЛИВАЕМ ФОНОМ
                                                 outline=GRID_OUTLINE_COLOR, # Светло-серый контур
                                                 width=1, tags="pixel_inactive_outline")

        # --- 3. Настраиваем область прокрутки ---
        # Область прокрутки равна размеру сетки пикселей
        self.canvas.config(scrollregion=(0, 0, canvas_width, canvas_height))


    def update_vertices_label(self, vertices_string):
        """ Обновляет текст метки вершин. (Без изменений) """
        self.vertices_label.config(text=vertices_string)

    def update_size_entries(self, rows, cols):
        """ Обновляет поля ввода размеров. (Без изменений) """
        self.rows_entry.delete(0, tk.END); self.rows_entry.insert(0, str(rows))
        self.cols_entry.delete(0, tk.END); self.cols_entry.insert(0, str(cols))

    def get_size_entries(self):
        """ Возвращает значения размеров. (Без изменений) """
        try: return int(self.rows_entry.get()), int(self.cols_entry.get())
        except ValueError: self.show_error("Ошибка ввода", "Размеры..."); return None, None

    def get_vertex_entries(self):
        """ Возвращает значения координат. (Без изменений) """
        try: return int(self.x_entry.get()), int(self.y_entry.get())
        except ValueError: self.show_error("Ошибка ввода", "Координаты..."); return None, None

    def clear_vertex_entries(self):
        """ Очищает поля ввода координат. (Без изменений) """
        self.x_entry.delete(0, tk.END); self.y_entry.delete(0, tk.END)

    def show_error(self, title, message):
        """ Отображает ошибку. (Без изменений) """
        messagebox.showerror(title, message, parent=self.frame)

    def show_info(self, title, message):
        """ Отображает информацию. (Без изменений) """
        messagebox.showinfo(title, message, parent=self.frame)

    # --- Метод для управления состоянием виджетов ---
    def set_widget_state(self, widget_name, state):
        """ Управляет состоянием виджетов (normal/disabled) """
        widget = getattr(self, widget_name, None)
        if widget:
            try:
                # Убедимся, что состояние допустимо
                valid_state = state if state in [tk.NORMAL, tk.DISABLED] else tk.DISABLED
                widget.config(state=valid_state)
            except tk.TclError as e:
                print(f"Warning: Could not set state '{state}' for widget '{widget_name}'. Error: {e}")
        else:
            print(f"Warning: Widget '{widget_name}' not found in DrawingView.")