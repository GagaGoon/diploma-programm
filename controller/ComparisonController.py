# controller/ComparisonController.py
import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
from model.ComparisonModel import ComparisonModel
# Обновляем импорт View, чтобы использовать новые константы цветов, если они там определены
from view.ComparisonView import ComparisonView, COMPARISON_PIXEL_SIZE

class ComparisonController:
    """
    Контроллер для вкладки сравнения.
    Связывает ComparisonModel и ComparisonView.
    """
    def __init__(self, parent_frame):
        self.model = ComparisonModel()
        self.view = ComparisonView(parent_frame, self)
        self._drag_start_info = None
        self._update_view_state()
        # Инициализируем метку начальными значениями
        self.view.update_info_label(None, (-1, -1)) # Используем новый метод

    def _update_view_state(self):
        """ Обновляет состояние кнопок в зависимости от состояния модели """
        img_loaded = self.model.image_pixels is not None
        tpl_loaded = self.model.template_pixels is not None

        self.view.set_widget_state("load_template_button", tk.NORMAL if img_loaded else tk.DISABLED)
        self.view.set_widget_state("find_best_button", tk.NORMAL if img_loaded and tpl_loaded else tk.DISABLED)

    def _update_full_view(self, update_info=True):
        """ Полное обновление отображения View на основе Model """
        self.view.update_canvas(
            self.model.image_pixels,
            self.model.template_pixels,
            self.model.current_pos if self.model.template_pixels is not None else (-1,-1)
        )
        if update_info:
            # Определяем, какой счет и позицию показывать
            score_to_show = None
            pos_to_show = (-1, -1)
            if self.model.template_pixels is not None:
                 # Если шаблон загружен, показываем его текущий счет и позицию
                 score_to_show = self.model.current_score
                 pos_to_show = self.model.current_pos
            # Если шаблон не загружен, но есть лучший результат (маловероятно, но для полноты)
            elif self.model.best_pos != (-1, -1):
                 score_to_show = self.model.best_score
                 pos_to_show = self.model.best_pos

            self.view.update_info_label(score_to_show, pos_to_show)

        self._update_view_state()


    def handle_load_image(self):
        """ Обработчик кнопки 'Загрузить изображение' """
        filename = filedialog.askopenfilename(
            title="Загрузить изображение из XML",
            filetypes=[("XML Image files", "*.xml"), ("All files", "*.*")],
            parent=self.view.frame
        )
        if filename:
            try:
                self.model.load_image_from_xml(filename)
                self._update_full_view()
                self.view.show_info("Успех", f"Изображение {self.model.image_rows}x{self.model.image_cols} загружено.")
            except Exception as e:
                self.view.show_error("Ошибка загрузки изображения", str(e))
                self.model = ComparisonModel()
                self._update_full_view()


    def handle_load_template(self):
        """ Обработчик кнопки 'Загрузить шаблон' """
        if self.model.image_pixels is None:
             self.view.show_error("Ошибка", "Сначала загрузите изображение!")
             return

        filename = filedialog.askopenfilename(
            title="Загрузить шаблон из XML",
            filetypes=[("XML Template files", "*.xml"), ("All files", "*.*")],
            parent=self.view.frame
        )
        if filename:
            try:
                self.model.load_template_from_xml(filename)
                self.model.set_current_pos(0, 0) # Ставим в начало, вычисляем счет
                self._update_full_view(update_info=False) # Обновляем холст
                # Обновляем инфо-метку текущим состоянием
                self.view.update_info_label(self.model.current_score, self.model.current_pos)
                self.view.show_info("Успех", f"Шаблон {self.model.template_rows}x{self.model.template_cols} загружен.")

            except Exception as e:
                self.model.reset_template_and_results()
                self._update_full_view()
                self.view.show_error("Ошибка загрузки шаблона", str(e))

    def handle_find_best_match(self):
        """ Обработчик кнопки 'Найти лучшее совпадение' """
        if self.model.image_pixels is None or self.model.template_pixels is None:
             self.view.show_error("Ошибка", "Изображение и шаблон должны быть загружены.")
             return
        try:
            score, pos_rc = self.model.find_best_match()
            # find_best_match обновляет current_pos и current_score
            # Обновляем холст, чтобы показать шаблон в лучшей позиции
            self.view.update_canvas(
                self.model.image_pixels,
                self.model.template_pixels,
                self.model.current_pos # Это лучшая позиция
            )
            # Обновляем инфо-метку лучшим результатом
            self.view.update_info_label(score, pos_rc)
            self._update_view_state()

            if pos_rc != (-1, -1):
                 self.view.show_info("Поиск завершен", f"Найдено лучшее совпадение со счетом {score:.0f} в позиции {pos_rc}.")
            else:
                 self.view.show_info("Поиск завершен", "Совпадений не найдено.")

        except Exception as e:
             self.view.show_error("Ошибка при поиске", str(e))

    # --- Обработчики событий холста ---

    def _get_canvas_coords_from_event(self, event):
         canvas_x = self.view.canvas.canvasx(event.x)
         canvas_y = self.view.canvas.canvasy(event.y)
         return canvas_x, canvas_y

    def _get_grid_coords_from_canvas(self, canvas_x, canvas_y):
        col = int(canvas_x // COMPARISON_PIXEL_SIZE)
        row = int(canvas_y // COMPARISON_PIXEL_SIZE)
        if self.model.image_pixels is not None:
             row = min(row, self.model.image_rows - 1)
             col = min(col, self.model.image_cols - 1)
        row = max(0, row)
        col = max(0, col)
        return row, col

    def handle_canvas_press(self, event):
        """ Начало перетаскивания шаблона """
        if self.model.template_pixels is None: return

        canvas_x, canvas_y = self._get_canvas_coords_from_event(event)
        click_row, click_col = self._get_grid_coords_from_canvas(canvas_x, canvas_y)
        tpl_r, tpl_c = self.model.current_pos

        offset_r = click_row - tpl_r
        offset_c = click_col - tpl_c

        if 0 <= offset_r < self.model.template_rows and 0 <= offset_c < self.model.template_cols:
            self._drag_start_info = {'offset_r': offset_r, 'offset_c': offset_c}
        else:
            self._drag_start_info = None

    def handle_canvas_drag(self, event):
        """ Перетаскивание шаблона """
        if self._drag_start_info is None or self.model.template_pixels is None: return

        canvas_x, canvas_y = self._get_canvas_coords_from_event(event)
        offset_r = self._drag_start_info['offset_r']
        offset_c = self._drag_start_info['offset_c']

        new_tpl_r_float = (canvas_y / COMPARISON_PIXEL_SIZE) - offset_r
        new_tpl_c_float = (canvas_x / COMPARISON_PIXEL_SIZE) - offset_c
        new_tpl_r = int(round(new_tpl_r_float))
        new_tpl_c = int(round(new_tpl_c_float))

        position_changed = self.model.set_current_pos(new_tpl_r, new_tpl_c)

        if position_changed:
            # Обновляем холст
            self.view.update_canvas(
                self.model.image_pixels,
                self.model.template_pixels,
                self.model.current_pos
            )
            # Обновляем инфо-метку текущим счетом и позицией
            self.view.update_info_label(
                self.model.current_score,
                self.model.current_pos
            )

    # --- ИЗМЕНЕНО: handle_canvas_motion ---
    def handle_canvas_motion(self, event):
        """
        Обработчик движения мыши БЕЗ нажатия.
        НЕ изменяет отображаемую информацию о результате/позиции шаблона.
        Информация обновляется только при перетаскивании или поиске.
        """
        # Можно оставить пустым, если совсем ничего не нужно делать при простом движении мыши.
        # Или можно отображать координаты самого курсора где-то еще, если понадобится.
        # canvas_x, canvas_y = self._get_canvas_coords_from_event(event)
        # cursor_row, cursor_col = self._get_grid_coords_from_canvas(canvas_x, canvas_y)
        # print(f"Mouse at: row={cursor_row}, col={cursor_col}") # Для отладки
        pass # Ничего не делаем с основной меткой info_label
    # --- Конец изменений ---

    def handle_canvas_configure(self, event):
        """ Обновляет scrollregion при изменении размера холста """
        if self.model.image_pixels is not None:
            rows, cols = self.model.image_pixels.shape
            width = cols * COMPARISON_PIXEL_SIZE
            height = rows * COMPARISON_PIXEL_SIZE
            self.view.canvas.config(scrollregion=(0, 0, width, height))
        else:
             self.view.canvas.config(scrollregion=(0, 0, event.width, event.height))