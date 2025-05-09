# controller/DrawingController.py
import tkinter as tk
from tkinter import messagebox, filedialog
from model.DrawingModel import DrawingModel
from view.DrawingView import DrawingView, DRAWING_PIXEL_SIZE

class DrawingController:
    def __init__(self, parent_frame):
        self.model = DrawingModel(40, 40)
        self.view = DrawingView(parent_frame, self)
        self._update_view()

    def _update_view(self):
        self.view.update_canvas(self.model.pixel_field)
        self.view.update_vertices_label(self.model.get_vertices_string())
        self.view.update_size_entries(self.model.rows, self.model.cols)
        self.view.update_physical_height_entry(self.model.template_physical_height_meters) # Обновляем
        self._update_view_state()

    def _update_view_state(self):
        undo_state = tk.NORMAL if self.model.undo_stack else tk.DISABLED; redo_state = tk.NORMAL if self.model.redo_stack else tk.DISABLED
        self.view.set_widget_state("undo_button", undo_state); self.view.set_widget_state("redo_button", redo_state)
        overlay_state = tk.NORMAL if self.model.overlay_image_pil else tk.DISABLED
        self.view.set_widget_state("overlay_left_btn", overlay_state); self.view.set_widget_state("overlay_right_btn", overlay_state)
        self.view.set_widget_state("overlay_up_btn", overlay_state); self.view.set_widget_state("overlay_down_btn", overlay_state)
        self.view.set_widget_state("overlay_zoom_in_btn", overlay_state); self.view.set_widget_state("overlay_zoom_out_btn", overlay_state)

    def canvas_click_handler(self, event):
        grid_x = self.view.canvas.canvasx(event.x) // DRAWING_PIXEL_SIZE; grid_y = self.view.canvas.canvasy(event.y) // DRAWING_PIXEL_SIZE
        if self.model.add_vertex(grid_x, grid_y): self._update_view()

    def clear_field(self):
        if messagebox.askyesno("Подтверждение", "Очистить поле и удалить все вершины?", parent=self.view.frame):
            self.model.clear(); self._update_view()

    def apply_size(self):
        rows, cols = self.view.get_size_entries()
        if rows is not None and cols is not None:
            if rows > 0 and cols > 0:
                 if not self.model.vertices or messagebox.askyesno("Подтверждение", "Изменение размера удалит вершины и историю. Продолжить?", parent=self.view.frame):
                     if self.model.resize(rows, cols): self._update_view()
                     else: self.view.show_error("Ошибка", "Не удалось изменить размер сетки.")
            else: self.view.show_error("Ошибка", "Размеры сетки должны быть положительными!")

    def add_vertex_by_input(self):
        x, y = self.view.get_vertex_entries()
        if x is not None and y is not None:
            if self.model.add_vertex(x, y): self._update_view(); self.view.clear_vertex_entries()
            else: self.view.show_error("Ошибка", f"Не удалось добавить вершину ({x},{y})...")

    # --- ОБРАБОТЧИК для физической высоты ---
    def handle_physical_height_entry_change(self, event=None): # event=None для вызова без события
        height_m = self.view.get_physical_height_entry()
        if height_m is not None:
            if height_m >= 0:
                self.model.template_physical_height_meters = height_m
                # Обновляем поле в View, чтобы отформатировать (если пользователь ввел "5" -> "5.000")
                self.view.update_physical_height_entry(self.model.template_physical_height_meters)
                print(f"Физическая высота шаблона установлена: {self.model.template_physical_height_meters:.3f} м.")
            else:
                self.view.show_error("Ошибка", "Физическая высота не может быть отрицательной.")
                # Восстанавливаем значение в поле из модели
                self.view.update_physical_height_entry(self.model.template_physical_height_meters)

    def save_as_template(self):
        # Убедимся, что последняя введенная высота сохранена в модель
        self.handle_physical_height_entry_change()

        filename = filedialog.asksaveasfilename(defaultextension=".xml", filetypes=[("XML Polygon files", "*.xml"), ("All files", "*.*")], title="Сохранить шаблон как...", parent=self.view.frame)
        if filename:
            try: self.model.save_to_xml(filename); self.view.show_info("Успех", f"Шаблон сохранён в {filename}")
            except Exception as e: self.view.show_error("Ошибка сохранения", f"Не удалось сохранить файл:\n{str(e)}")

    def load_from_xml(self):
        filename = filedialog.askopenfilename(filetypes=[("XML Polygon files", "*.xml"), ("All files", "*.*")], title="Загрузить шаблон из...", parent=self.view.frame)
        if filename:
            try: self.model.load_from_xml(filename); self._update_view(); self.view.show_info("Успех", f"Шаблон загружен из {filename}")
            except Exception as e: self.view.show_error("Ошибка загрузки", f"Не удалось загрузить файл:\n{str(e)}")

    def handle_undo(self):
        if self.model.undo_vertex(): self._update_view()
    def handle_redo(self):
        if self.model.redo_vertex(): self._update_view()
    def handle_load_overlay(self):
        filename = filedialog.askopenfilename(title="Выбрать фоновое изображение", filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff"), ("All files", "*.*")], parent=self.view.frame)
        if filename:
            try:
                if self.model.load_overlay_image(filename): self._update_view(); self.view.show_info("Успех", "Изображение загружено как фон.")
            except Exception as e: self.view.show_error("Ошибка загрузки изображения", str(e)); self._update_view_state()
    def handle_move_overlay(self, dx, dy):
        if self.model.move_overlay(dx, dy): self.view.update_canvas(self.model.pixel_field)
    def handle_scale_overlay(self, factor):
        if self.model.scale_overlay(factor): self.view.update_canvas(self.model.pixel_field)