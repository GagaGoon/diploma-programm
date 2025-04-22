# controller/DrawingController.py
import tkinter as tk
from tkinter import messagebox, filedialog
from model.DrawingModel import DrawingModel
from view.DrawingView import DrawingView, DRAWING_PIXEL_SIZE

class DrawingController:
    """
    Контроллер для редактора шаблонов.
    Связывает DrawingModel и DrawingView.
    ДОБАВЛЕНО: Обработчики Undo/Redo, Overlay Image.
    """
    def __init__(self, parent_frame):
        self.model = DrawingModel(40, 40)
        self.view = DrawingView(parent_frame, self)
        self._update_view() # Первоначальное обновление вида и состояния кнопок

    def _update_view(self):
        """ Обновляет все элементы представления и состояние кнопок """
        self.view.update_canvas(self.model.pixel_field)
        self.view.update_vertices_label(self.model.get_vertices_string())
        self.view.update_size_entries(self.model.rows, self.model.cols)
        self._update_view_state() # Обновляем состояние кнопок

    def _update_view_state(self):
        """ Обновляет состояние кнопок Undo, Redo и управления оверлеем """
        # Undo/Redo
        undo_state = tk.NORMAL if self.model.undo_stack else tk.DISABLED
        redo_state = tk.NORMAL if self.model.redo_stack else tk.DISABLED
        self.view.set_widget_state("undo_button", undo_state)
        self.view.set_widget_state("redo_button", redo_state)

        # Overlay controls
        overlay_state = tk.NORMAL if self.model.overlay_image_pil else tk.DISABLED
        self.view.set_widget_state("overlay_left_btn", overlay_state)
        self.view.set_widget_state("overlay_right_btn", overlay_state)
        self.view.set_widget_state("overlay_up_btn", overlay_state)
        self.view.set_widget_state("overlay_down_btn", overlay_state)
        self.view.set_widget_state("overlay_zoom_in_btn", overlay_state)
        self.view.set_widget_state("overlay_zoom_out_btn", overlay_state)

    def canvas_click_handler(self, event):
        """ Обработчик клика мыши по холсту редактора """
        # Преобразуем координаты холста в координаты сетки
        grid_x = self.view.canvas.canvasx(event.x) // DRAWING_PIXEL_SIZE
        grid_y = self.view.canvas.canvasy(event.y) // DRAWING_PIXEL_SIZE

        # Добавляем вершину через модель
        if self.model.add_vertex(grid_x, grid_y):
            self._update_view() # Обновляем вид и состояние кнопок

    def clear_field(self):
        """ Обработчик кнопки 'Очистить поле' """
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите очистить поле и удалить все вершины?", parent=self.view.frame):
            self.model.clear()
            self._update_view() # Обновляем вид и состояние кнопок

    def apply_size(self):
        """ Обработчик кнопки 'Применить размер' """
        rows, cols = self.view.get_size_entries()
        if rows is not None and cols is not None:
            if rows > 0 and cols > 0:
                 if not self.model.vertices or \
                    messagebox.askyesno("Подтверждение", "Изменение размера удалит текущие вершины и историю. Продолжить?", parent=self.view.frame):
                     if self.model.resize(rows, cols): # resize очистит историю
                         self._update_view() # Обновляем вид и состояние кнопок
                     else:
                         self.view.show_error("Ошибка", "Не удалось изменить размер.")
            else:
                self.view.show_error("Ошибка", "Размеры поля должны быть положительными!")

    def add_vertex_by_input(self):
        """ Обработчик кнопки '+' для добавления вершины по координатам """
        x, y = self.view.get_vertex_entries()
        if x is not None and y is not None:
            if self.model.add_vertex(x, y):
                self._update_view() # Обновляем вид и состояние кнопок
                self.view.clear_vertex_entries()
            else:
                self.view.show_error("Ошибка", f"Не удалось добавить вершину ({x},{y})...") # Сообщение как раньше

    def save_as_template(self):
        """ Обработчик кнопки 'Сохранить как шаблон' (сохраняет вершины) """
        filename = filedialog.asksaveasfilename(
            defaultextension=".xml",
            filetypes=[("XML Template files", "*.xml"), ("All files", "*.*")],
            title="Сохранить шаблон как...",
            parent=self.view.frame
        )
        if filename:
            try:
                self.model.save_to_xml(filename)
                self.view.show_info("Успех", f"Шаблон успешно сохранён в {filename}")
            except Exception as e:
                self.view.show_error("Ошибка сохранения шаблона", f"Не удалось сохранить файл:\n{str(e)}")

    # Метод save_as_image УДАЛЕН

    def load_from_xml(self):
        """ Обработчик кнопки 'Загрузить шаблон' (загружает вершины) """
        filename = filedialog.askopenfilename(
            filetypes=[("XML Template files", "*.xml"), ("All files", "*.*")],
            title="Загрузить шаблон из...",
            parent=self.view.frame
        )
        if filename:
            # Спросить подтверждение, если есть несохраненные изменения? (Опционально)
            # if self.model.undo_stack or self.model.vertices:
            #     if not messagebox.askyesno("Подтверждение", "Загрузка нового шаблона очистит текущее поле и историю. Продолжить?", parent=self.view.frame):
            #         return
            try:
                self.model.load_from_xml(filename) # load_from_xml вызовет resize, который очистит историю
                self._update_view() # Обновляем вид и состояние кнопок
                self.view.show_info("Успех", f"Шаблон успешно загружен из {filename}")
            except Exception as e:
                self.view.show_error("Ошибка загрузки шаблона", f"Не удалось загрузить файл:\n{str(e)}")

    # --- Обработчики Undo/Redo ---
    def handle_undo(self):
        """ Обработчик кнопки Undo """
        if self.model.undo_vertex():
            self._update_view() # Обновляем вид и состояние кнопок

    def handle_redo(self):
        """ Обработчик кнопки Redo """
        if self.model.redo_vertex():
            self._update_view() # Обновляем вид и состояние кнопок

    # --- Обработчики Overlay ---
    def handle_load_overlay(self):
        """ Обработчик кнопки 'Наложить изображение' """
        filename = filedialog.askopenfilename(
            title="Выбрать фоновое изображение",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff"),
                       ("All files", "*.*")],
            parent=self.view.frame
        )
        if filename:
            try:
                if self.model.load_overlay_image(filename):
                    self._update_view() # Обновляем вид (холст) и состояние кнопок
                    self.view.show_info("Успех", "Изображение загружено как фон.")
            except Exception as e:
                self.view.show_error("Ошибка загрузки изображения", str(e))
                self._update_view() # Обновляем состояние кнопок (должны остаться disabled)

    def handle_move_overlay(self, dx, dy):
        """ Обработчик кнопок перемещения оверлея """
        if self.model.move_overlay(dx, dy):
            self.view.update_canvas(self.model.pixel_field) # Перерисовываем только холст

    def handle_scale_overlay(self, factor):
        """ Обработчик кнопок масштабирования оверлея """
        if self.model.scale_overlay(factor):
            self.view.update_canvas(self.model.pixel_field) # Перерисовываем только холст