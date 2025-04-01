# controller/DrawingController.py
import tkinter as tk
from tkinter import messagebox, filedialog # FileDialog используется здесь
# Используем относительные импорты внутри пакета controller
from model.DrawingModel import DrawingModel
from view.DrawingView import DrawingView, DRAWING_PIXEL_SIZE

class DrawingController:
    """
    Контроллер для редактора шаблонов.
    Связывает DrawingModel и DrawingView.
    """
    def __init__(self, parent_frame):
        self.model = DrawingModel(40, 40)
        self.view = DrawingView(parent_frame, self)
        self._update_view()

    def _update_view(self):
        """ Обновляет все элементы представления на основе модели """
        self.view.update_canvas(self.model.pixel_field)
        self.view.update_vertices_label(self.model.get_vertices_string())
        self.view.update_size_entries(self.model.rows, self.model.cols)

    def canvas_click_handler(self, event):
        """ Обработчик клика мыши по холсту редактора """
        x = event.x // DRAWING_PIXEL_SIZE
        y = event.y // DRAWING_PIXEL_SIZE
        if self.model.add_vertex(x, y):
            self.view.update_canvas(self.model.pixel_field)
            self.view.update_vertices_label(self.model.get_vertices_string())

    def clear_field(self):
        """ Обработчик кнопки 'Очистить поле' """
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите очистить поле и удалить все вершины?", parent=self.view.frame):
            self.model.clear()
            self._update_view()

    def apply_size(self):
        """ Обработчик кнопки 'Применить размер' """
        rows, cols = self.view.get_size_entries()
        if rows is not None and cols is not None:
            if rows > 0 and cols > 0:
                 if not self.model.vertices or \
                    messagebox.askyesno("Подтверждение", "Изменение размера удалит текущие вершины. Продолжить?", parent=self.view.frame):
                     if self.model.resize(rows, cols):
                         self._update_view()
                     else:
                         self.view.show_error("Ошибка", "Не удалось изменить размер.")
            else:
                self.view.show_error("Ошибка", "Размеры поля должны быть положительными!")

    def add_vertex_by_input(self):
        """ Обработчик кнопки '+' для добавления вершины по координатам """
        x, y = self.view.get_vertex_entries()
        if x is not None and y is not None:
            if self.model.add_vertex(x, y):
                self.view.update_canvas(self.model.pixel_field)
                self.view.update_vertices_label(self.model.get_vertices_string())
                self.view.clear_vertex_entries()
            else:
                self.view.show_error("Ошибка", f"Не удалось добавить вершину ({x},{y}).\n"
                                              f"Возможно, она вне поля ({self.model.rows}x{self.model.cols}) или уже существует.")

    # --- ИЗМЕНЕНО: Метод для сохранения как шаблон ---
    def save_as_template(self):
        """ Обработчик кнопки 'Сохранить как шаблон' """
        filename = filedialog.asksaveasfilename(
            defaultextension=".xml",
            filetypes=[("XML Template files", "*.xml"), ("All files", "*.*")],
            title="Сохранить шаблон как...",
            parent=self.view.frame
        )
        if filename:
            try:
                # Вызываем старый метод сохранения модели (который сохраняет вершины)
                self.model.save_to_xml(filename)
                self.view.show_info("Успех", f"Шаблон успешно сохранён в {filename}")
            except Exception as e:
                self.view.show_error("Ошибка сохранения шаблона", f"Не удалось сохранить файл:\n{str(e)}")

    # --- ДОБАВЛЕНО: Метод для сохранения как изображение ---
    def save_as_image(self):
        """ Обработчик кнопки 'Сохранить как изображение' """
        filename = filedialog.asksaveasfilename(
            defaultextension=".xml",
            filetypes=[("XML Image files", "*.xml"), ("All files", "*.*")],
            title="Сохранить как изображение...",
            parent=self.view.frame
        )
        if filename:
            try:
                # Вызываем НОВЫЙ метод сохранения модели (который сохраняет пиксели)
                self.model.save_as_image_xml(filename)
                self.view.show_info("Успех", f"Изображение успешно сохранено в {filename}")
            except Exception as e:
                self.view.show_error("Ошибка сохранения изображения", f"Не удалось сохранить файл:\n{str(e)}")
    # --- Конец изменений ---

    def load_from_xml(self):
        """ Обработчик кнопки 'Загрузить шаблон' (загружает только формат шаблона) """
        filename = filedialog.askopenfilename(
            filetypes=[("XML Template files", "*.xml"), ("All files", "*.*")],
            title="Загрузить шаблон из...",
            parent=self.view.frame
        )
        if filename:
            try:
                # Метод load_from_xml в модели ожидает формат <template>
                self.model.load_from_xml(filename)
                self._update_view()
                self.view.show_info("Успех", f"Шаблон успешно загружен из {filename}")
            except Exception as e:
                # Ошибка может быть из-за неверного формата (например, попытка загрузить <image>)
                self.view.show_error("Ошибка загрузки шаблона", f"Не удалось загрузить файл:\n{str(e)}")