import tkinter as tk

class View:
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller

        self.size_frame = tk.Frame(self.root)
        self.size_frame.pack(pady=10)

        tk.Label(self.size_frame, text="Rows:").pack(side=tk.LEFT)
        self.rows_entry = tk.Entry(self.size_frame, width=5)
        self.rows_entry.insert(0, "100")
        self.rows_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(self.size_frame, text="Cols:").pack(side=tk.LEFT)
        self.cols_entry = tk.Entry(self.size_frame, width=5)
        self.cols_entry.insert(0, "100")
        self.cols_entry.pack(side=tk.LEFT, padx=5)

        self.apply_button = tk.Button(self.size_frame, text="Применить размер", command=self.controller.apply_size)
        self.apply_button.pack(side=tk.LEFT, padx=10)

        self.clear_button = tk.Button(self.size_frame, text="Очистить поле", command=self.controller.clear_field)
        self.clear_button.pack(side=tk.LEFT, padx=10)

        self.canvas = tk.Canvas(self.root, width=500, height=500, bg='white')
        self.canvas.pack(pady=10)
        self.canvas.bind("<Button-1>", self.controller.canvas_click)

    def update_canvas(self, pixel_field, pixel_size=15):  # Изменено с 5 на 15
        self.canvas.delete("all")
        rows, cols = len(pixel_field), len(pixel_field[0])
        for i in range(rows):
            for j in range(cols):
                color = 'blue' if pixel_field[i][j] == 1 else 'gray'
                x0 = j * pixel_size
                y0 = i * pixel_size
                x1 = x0 + pixel_size
                y1 = y0 + pixel_size
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline='white')

        canvas_width = cols * pixel_size
        canvas_height = rows * pixel_size
        self.canvas.config(width=canvas_width, height=canvas_height)
        self.root.update_idletasks()
        window_width = canvas_width + 20
        window_height = canvas_height + self.size_frame.winfo_height() + 40
        self.root.geometry(f"{window_width}x{window_height}")