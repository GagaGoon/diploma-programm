import tkinter as tk
from Model import Model
from View import View

class Controller:
    def __init__(self, root):
        self.root = root
        self.model = Model(100, 100)  # Начальный размер 100x100
        self.view = View(root, self)
        self.view.update_canvas(self.model.pixel_field)

    def canvas_click(self, event):
        pixel_size = 15  # Изменено с 5 на 15
        x = event.x // pixel_size
        y = event.y // pixel_size
        if 0 <= x < self.model.cols and 0 <= y < self.model.rows:
            self.model.add_vertex(x, y)
            self.view.update_canvas(self.model.pixel_field, pixel_size)

    def clear_field(self):
        self.model.clear()
        self.view.update_canvas(self.model.pixel_field)

    def apply_size(self):
        try:
            new_rows = int(self.view.rows_entry.get())
            new_cols = int(self.view.cols_entry.get())
            if new_rows > 0 and new_cols > 0:
                self.model.resize(new_rows, new_cols)
                self.view.update_canvas(self.model.pixel_field)
            else:
                tk.messagebox.showerror("Ошибка", "Размеры поля должны быть положительными!")
        except ValueError:
            tk.messagebox.showerror("Ошибка", "Пожалуйста, введите целые числовые значения для размеров!")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Поле с пикселями")
    app = Controller(root)
    root.mainloop()