import tkinter as tk
from tkinter import messagebox, filedialog
from Model import Model
from View import View

class Controller:
    def __init__(self, root):
        self.root = root
        self.model = Model(40, 40)  # Изменено с 100x100 на 40x40
        self.view = View(root, self)
        self.view.update_canvas(self.model.pixel_field)
        self.view.update_vertices_label(self.model.get_vertices_string())

    def canvas_click(self, event):
        pixel_size = 15
        x = event.x // pixel_size
        y = event.y // pixel_size
        if 0 <= x < self.model.cols and 0 <= y < self.model.rows:
            self.model.add_vertex(x, y)
            self.view.update_canvas(self.model.pixel_field, pixel_size)
            self.view.update_vertices_label(self.model.get_vertices_string())

    def clear_field(self):
        self.model.clear()
        self.view.update_canvas(self.model.pixel_field)
        self.view.update_vertices_label(self.model.get_vertices_string())

    def apply_size(self):
        try:
            new_rows = int(self.view.rows_entry.get())
            new_cols = int(self.view.cols_entry.get())
            if new_rows > 0 and new_cols > 0:
                self.model.resize(new_rows, new_cols)
                self.view.update_canvas(self.model.pixel_field)
                self.view.update_vertices_label(self.model.get_vertices_string())
            else:
                messagebox.showerror("Ошибка", "Размеры поля должны быть положительными!")
        except ValueError:
            messagebox.showerror("Ошибка", "Пожалуйста, введите целые числовые значения для размеров!")

    def add_vertex_by_input(self):
        try:
            x = int(self.view.x_entry.get())
            y = int(self.view.y_entry.get())
            self.model.add_vertex(x, y)
            self.view.update_canvas(self.model.pixel_field)
            self.view.update_vertices_label(self.model.get_vertices_string())
            # Очищаем поля ввода после добавления
            self.view.x_entry.delete(0, tk.END)
            self.view.y_entry.delete(0, tk.END)
        except ValueError:
            messagebox.showerror("Ошибка", "Пожалуйста, введите целые числовые значения для координат!")

    def save_to_xml(self):
        try:
            self.model.save_to_xml("template.xml")
            messagebox.showinfo("Успех", "Шаблон успешно сохранён в template.xml")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {str(e)}")

    def load_from_xml(self):
        try:
            filename = filedialog.askopenfilename(filetypes=[("XML files", "*.xml")])
            if filename:
                self.model.load_from_xml(filename)
                self.view.update_canvas(self.model.pixel_field)
                self.view.update_vertices_label(self.model.get_vertices_string())
                # Обновляем поля ввода размера
                self.view.rows_entry.delete(0, tk.END)
                self.view.rows_entry.insert(0, str(self.model.rows))
                self.view.cols_entry.delete(0, tk.END)
                self.view.cols_entry.insert(0, str(self.model.cols))
                messagebox.showinfo("Успех", "Шаблон успешно загружен")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить файл: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Поле с пикселями")
    app = Controller(root)
    root.mainloop()