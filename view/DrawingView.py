# view/DrawingView.py
import tkinter as tk
from tkinter import messagebox # Убираем filedialog отсюда

# Константа для размера пикселя на холсте редактора
DRAWING_PIXEL_SIZE = 15

class DrawingView:
    """
    Представление (View) для редактора шаблонов.
    Отвечает за создание и отображение GUI редактора внутри родительского фрейма.
    """
    def __init__(self, parent_frame, controller):
        self.frame = parent_frame # Используем переданный фрейм
        self.controller = controller

        # --- Верхняя панель: Файловые операции ---
        self.file_frame = tk.Frame(self.frame)
        self.file_frame.pack(pady=5, fill=tk.X, padx=10)

        # --- ИЗМЕНЕНО: Две кнопки сохранения ---
        self.save_template_button = tk.Button(self.file_frame, text="Сохранить как шаблон", command=self.controller.save_as_template)
        self.save_template_button.pack(side=tk.LEFT, padx=5)

        self.save_image_button = tk.Button(self.file_frame, text="Сохранить как изображение", command=self.controller.save_as_image)
        self.save_image_button.pack(side=tk.LEFT, padx=5)
        # --- Конец изменений ---

        self.load_button = tk.Button(self.file_frame, text="Загрузить шаблон", command=self.controller.load_from_xml)
        self.load_button.pack(side=tk.LEFT, padx=5)

        # --- Панель управления размером и очисткой ---
        # (остальная часть __init__ без изменений)
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

        self.clear_button = tk.Button(self.size_frame, text="Очистить поле", command=self.controller.clear_field)
        self.clear_button.pack(side=tk.RIGHT, padx=5)

        # --- Панель добавления вершин вручную ---
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

        # --- Метка для отображения списка вершин ---
        self.vertex_display_frame = tk.Frame(self.frame)
        self.vertex_display_frame.pack(pady=5, fill=tk.X, padx=10)
        tk.Label(self.vertex_display_frame, text="Вершины:", anchor='w').pack(side=tk.LEFT)
        self.vertices_label = tk.Label(self.vertex_display_frame, text="", font=("Arial", 10), anchor='w', justify=tk.LEFT, wraplength=500)
        self.vertices_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # --- Холст для пикселей ---
        self.canvas = tk.Canvas(self.frame, width=100, height=100, bg='white', relief=tk.SUNKEN, borderwidth=1)
        self.canvas.pack(pady=10, padx=10, expand=True, fill=tk.BOTH)
        self.canvas.bind("<Button-1>", self.controller.canvas_click_handler)

        # Устанавливаем начальные значения размеров в поля ввода
        self.update_size_entries(self.controller.model.rows, self.controller.model.cols)

    # (остальные методы View без изменений)
    def update_canvas(self, pixel_field):
        """
        Обновляет (перерисовывает) содержимое холста (Canvas) на основе pixel_field.
        """
        self.canvas.delete("all") # Очищаем холст перед перерисовкой
        rows = len(pixel_field)
        cols = len(pixel_field[0]) if rows > 0 else 0

        if rows == 0 or cols == 0:
            self.canvas.config(width=10, height=10) # Минимальный размер, если поле пустое
            return

        # Рассчитываем необходимые размеры холста
        canvas_width = cols * DRAWING_PIXEL_SIZE
        canvas_height = rows * DRAWING_PIXEL_SIZE
        self.canvas.config(width=canvas_width, height=canvas_height)

        # Рисуем сетку пикселей
        for r in range(rows):
            for c in range(cols):
                color = 'blue' if pixel_field[r][c] == 1 else '#F0F0F0' # Светло-серый фон
                x0 = c * DRAWING_PIXEL_SIZE
                y0 = r * DRAWING_PIXEL_SIZE
                x1 = x0 + DRAWING_PIXEL_SIZE
                y1 = y0 + DRAWING_PIXEL_SIZE
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline='white', width=1)

    def update_vertices_label(self, vertices_string):
        """ Обновляет текст метки, отображающей список вершин. """
        self.vertices_label.config(text=vertices_string)

    def update_size_entries(self, rows, cols):
        """ Обновляет значения в полях ввода размеров """
        self.rows_entry.delete(0, tk.END)
        self.rows_entry.insert(0, str(rows))
        self.cols_entry.delete(0, tk.END)
        self.cols_entry.insert(0, str(cols))

    def get_size_entries(self):
        """ Возвращает значения из полей ввода размеров как кортеж (rows, cols) """
        try:
            rows = int(self.rows_entry.get())
            cols = int(self.cols_entry.get())
            return rows, cols
        except ValueError:
            self.show_error("Ошибка ввода", "Размеры должны быть целыми числами.")
            return None, None

    def get_vertex_entries(self):
        """ Возвращает значения из полей ввода координат как кортеж (x, y) """
        try:
            x = int(self.x_entry.get())
            y = int(self.y_entry.get())
            return x, y
        except ValueError:
            self.show_error("Ошибка ввода", "Координаты X и Y должны быть целыми числами.")
            return None, None

    def clear_vertex_entries(self):
        """ Очищает поля ввода координат X и Y """
        self.x_entry.delete(0, tk.END)
        self.y_entry.delete(0, tk.END)

    def show_error(self, title, message):
        """ Отображает диалоговое окно с ошибкой """
        messagebox.showerror(title, message, parent=self.frame) # Указываем родителя

    def show_info(self, title, message):
        """ Отображает информационное диалоговое окно """
        messagebox.showinfo(title, message, parent=self.frame)