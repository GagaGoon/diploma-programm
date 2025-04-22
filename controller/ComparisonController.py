# controller/ComparisonController.py
import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
# --- ИСПРАВЛЕНИЕ ИМПОРТА ---
# Было: from .DrawingModel import DrawingModel
from model.DrawingModel import DrawingModel # Импортируем из пакета model
# --- КОНЕЦ ИСПРАВЛЕНИЯ ---
from model.ComparisonModel import ComparisonModel
from view.ComparisonView import ComparisonView, SCALE_INCREMENT

class ComparisonController:
    """
    Контроллер для вкладки сравнения.
    Связывает ComparisonModel и ComparisonView.
    ИСПРАВЛЕНО: Импорт DrawingModel.
    """
    def __init__(self, parent_frame):
        self.model = ComparisonModel()
        self.view = ComparisonView(parent_frame, self)
        self._drag_start_info = None
        self._update_view_state()
        self.view.update_info_label(None, (-1, -1))
        self.view.update_scale_controls(self.model.template_scale, tk.DISABLED)

    def _update_view_state(self):
        """ Обновляет состояние кнопок и элементов управления масштабом """
        img_loaded = self.model.grayscale_image is not None
        original_tpl_loaded = self.model.original_template_pixels is not None
        sobel_applied = self.model.sobel_image is not None
        current_tpl_exists = self.model.template_pixels is not None

        self.view.set_widget_state("load_template_button", tk.NORMAL if img_loaded else tk.DISABLED)
        self.view.set_widget_state("sobel_button", tk.NORMAL if img_loaded else tk.DISABLED)
        scale_controls_state = tk.NORMAL if original_tpl_loaded else tk.DISABLED
        self.view.update_scale_controls(self.model.template_scale, scale_controls_state)
        self.view.set_widget_state("find_best_button", tk.NORMAL if sobel_applied and current_tpl_exists else tk.DISABLED)

    def _update_full_view(self, update_info=True, update_scale_display=False):
        """ Полное обновление отображения View на основе Model """
        display_image = self.model.get_display_image()
        self.view.update_canvas(display_image, self.model.template_pixels, self.model.current_pos)
        if update_info: self.view.update_info_label(self.model.current_score, self.model.current_pos)
        if update_scale_display:
             scale_controls_state = tk.NORMAL if self.model.original_template_pixels is not None else tk.DISABLED
             self.view.update_scale_controls(self.model.template_scale, scale_controls_state)
        self._update_view_state()

    # --- Обработчики кнопок и событий ---
    def handle_load_image(self):
        filename = filedialog.askopenfilename(
            title="Загрузить изображение",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff"), ("All files", "*.*")],
            parent=self.view.frame)
        if filename:
            try:
                self.model.load_image(filename)
                self._update_full_view(update_info=True, update_scale_display=True)
                self.view.show_info("Успех", f"Изображение {self.model.image_rows}x{self.model.image_cols} загружено.")
            except Exception as e:
                self._update_full_view(update_info=True, update_scale_display=True)
                self.view.show_error("Ошибка загрузки изображения", str(e))

    def handle_load_template(self):
        """ Обработчик кнопки 'Загрузить шаблон' (ожидает формат <polygon>) """
        if self.model.grayscale_image is None:
             self.view.show_error("Ошибка", "Сначала загрузите изображение!")
             return
        filename = filedialog.askopenfilename(
            title="Загрузить шаблон из XML",
            filetypes=[("XML Polygon files", "*.xml"), ("All files", "*.*")], # Можно уточнить тип
            parent=self.view.frame)
        if filename:
            try:
                # ComparisonModel.load_template_from_xml теперь ожидает <polygon>
                self.model.load_template_from_xml(filename)
                self._update_full_view(update_info=True, update_scale_display=True)
                orig_shape = self.model.original_template_pixels.shape if self.model.original_template_pixels is not None else "N/A"
                # Сообщаем размер оригинального шаблона (определенного по точкам)
                self.view.show_info("Успех", f"Шаблон загружен (размер {orig_shape}). Масштаб: {self.model.template_scale:.1f}")
            except Exception as e:
                self._update_full_view(update_info=True, update_scale_display=True)
                self.view.show_error("Ошибка загрузки шаблона", str(e))

    def handle_apply_sobel(self):
        if self.model.grayscale_image is None: self.view.show_error("Ошибка", "Сначала загрузите изображение!"); return
        try:
            self.model.apply_sobel()
            self._update_full_view(update_info=True, update_scale_display=False)
            self.view.show_info("Успех", "Фильтр Собеля применен.")
        except Exception as e: self.view.show_error("Ошибка применения фильтра Собеля", str(e))

    def handle_find_best_match(self):
        if self.model.sobel_image is None: self.view.show_error("Ошибка", "Сначала примените фильтр Собеля!"); return
        if self.model.template_pixels is None: self.view.show_error("Ошибка", "Шаблон не загружен или не масштабирован."); return
        try:
            score, pos_rc = self.model.find_best_match()
            self._update_full_view(update_info=True, update_scale_display=False)
            if pos_rc != (-1, -1): self.view.show_info("Поиск завершен", f"Найдено лучшее совпадение со счетом {score:.4f} в позиции {pos_rc}.")
            else: self.view.show_info("Поиск завершен", "Совпадений не найдено или произошла ошибка.")
        except Exception as e: self.view.show_error("Ошибка при поиске", str(e))

    # --- Обработчики масштаба ---
    def handle_scale_up(self):
        if self.model.original_template_pixels is None: return
        current_scale = round(self.model.template_scale, 1)
        new_scale = current_scale + SCALE_INCREMENT
        self._apply_new_scale(new_scale)

    def handle_scale_down(self):
        if self.model.original_template_pixels is None: return
        current_scale = round(self.model.template_scale, 1)
        new_scale = current_scale - SCALE_INCREMENT
        if new_scale < SCALE_INCREMENT: new_scale = SCALE_INCREMENT
        self._apply_new_scale(new_scale)

    def handle_scale_entry_change(self, event=None):
        if self.model.original_template_pixels is None: return
        try:
            scale_value_str = self.view.get_scale_entry_value().replace(',', '.')
            new_scale = float(scale_value_str)
            if new_scale <= 0: raise ValueError("Масштаб должен быть положительным числом.")
            self._apply_new_scale(new_scale)
        except ValueError:
            self.view.show_error("Ошибка ввода", "Масштаб должен быть положительным числом.")
            self._update_full_view(update_info=False, update_scale_display=True)
        except Exception as e:
             self.view.show_error("Ошибка масштабирования", str(e))
             self._update_full_view(update_info=False, update_scale_display=True)

    def _apply_new_scale(self, new_scale):
        if self.model.original_template_pixels is None: return
        new_scale = round(new_scale, 2)
        if abs(new_scale - self.model.template_scale) < 1e-5:
            self._update_full_view(update_info=False, update_scale_display=True); return
        scale_changed = self.model.set_template_scale(new_scale)
        self._update_full_view(update_info=True, update_scale_display=True)

    # --- Обработчики холста (без изменений) ---
    def handle_canvas_press(self, event):
        if self.model.template_pixels is None or self.model.get_display_image() is None: self._drag_start_info = None; return
        click_row, click_col = self.view.get_original_coords_from_canvas(event.x, event.y)
        tpl_r, tpl_c = self.model.current_pos; offset_r = click_row - tpl_r; offset_c = click_col - tpl_c
        if 0 <= offset_r < self.model.template_rows and 0 <= offset_c < self.model.template_cols: self._drag_start_info = {'offset_r': offset_r, 'offset_c': offset_c}
        else: self._drag_start_info = None

    def handle_canvas_drag(self, event):
        if self._drag_start_info is None or self.model.template_pixels is None or self.model.get_display_image() is None: return
        current_row, current_col = self.view.get_original_coords_from_canvas(event.x, event.y)
        offset_r = self._drag_start_info['offset_r']; offset_c = self._drag_start_info['offset_c']
        new_tpl_r = current_row - offset_r; new_tpl_c = current_col - offset_c
        position_changed = self.model.set_current_pos(new_tpl_r, new_tpl_c)
        if position_changed:
            self.view.update_canvas(self.model.get_display_image(), self.model.template_pixels, self.model.current_pos)
            self.view.update_info_label(self.model.current_score, self.model.current_pos)

    def handle_canvas_configure(self, event):
        self._update_full_view(update_info=True, update_scale_display=False)