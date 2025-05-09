# controller/ComparisonController.py
import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
from model.DrawingModel import DrawingModel # Используется в ComparisonModel
from model.ComparisonModel import ComparisonModel
from view.ComparisonView import ComparisonView # SCALE_INCREMENT больше не нужен

class ComparisonController:
    """
    Контроллер для вкладки сравнения.
    Добавлены обработчики для нового интерфейса масштаба изображения и поворота шаблона.
    ИСПРАВЛЕНО: Синтаксическая ошибка и логика в _update_view_state.
    """
    def __init__(self, parent_frame):
        self.model = ComparisonModel()
        self.view = ComparisonView(parent_frame, self)
        self._drag_start_info = None
        self._update_view_state() # Инициализируем состояние всех виджетов
        # Инициализируем информационную метку и поля
        self.view.update_info_label(None, (-1, -1), 0) # score, pos, angle
        self.view.update_image_parameters_entries(
            self.model.image_meters_per_pixel,
            self.model.image_physical_height_meters,
            tk.DISABLED
        )
        # Инициализация поля угла (должно быть после _update_view_state, если оно там обновляется)
        # Но лучше сразу установить начальное состояние здесь, а _update_view_state подтвердит.
        self.view.update_angle_entry(self.model.template_angle_degrees, tk.DISABLED)

    def _update_view_state(self):
        """ Обновляет состояние всех кнопок и элементов управления """
        img_loaded = self.model.grayscale_image is not None
        original_tpl_loaded = self.model.original_template_pixels is not None
        filter_applied = self.model._get_active_edge_image() is not None
        current_tpl_exists = self.model.template_pixels is not None

        # Базовые кнопки
        self.view.set_widget_state("load_template_button", tk.NORMAL if img_loaded else tk.DISABLED)

        # Фильтры
        filter_button_state = tk.NORMAL if img_loaded else tk.DISABLED
        self.view.set_widget_state("sobel_button", filter_button_state)
        self.view.set_widget_state("kirsch_button", filter_button_state)
        self.view.set_widget_state("roberts_button", filter_button_state)
        self.view.set_widget_state("prewitt_button", filter_button_state)
        self.view.update_gauss_button_visuals(self.model.gaussian_blur_active, filter_button_state)

        # Параметры изображения (м/пкс, физ. высота)
        image_params_state = tk.NORMAL if img_loaded else tk.DISABLED
        self.view.update_image_parameters_entries(
            self.model.image_meters_per_pixel,
            self.model.image_physical_height_meters,
            image_params_state
        )

        # Управление шаблоном (поворот, поле угла)
        template_controls_state = tk.NORMAL if original_tpl_loaded else tk.DISABLED
        self.view.set_widget_state("rotate_left_button", template_controls_state)
        self.view.set_widget_state("rotate_right_button", template_controls_state)
        # --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
        self.view.update_angle_entry(self.model.template_angle_degrees, template_controls_state)
        # --- КОНЕЦ ИСПРАВЛЕНИЯ ---

        # Поиск
        self.view.set_widget_state("find_best_button", tk.NORMAL if filter_applied and current_tpl_exists else tk.DISABLED)

    def _update_full_view(self, update_info=True, update_image_params_display=False, update_angle_display=False):
        """ Полное обновление отображения View на основе Model """
        display_image = self.model.get_display_image()
        self.view.update_canvas(display_image, self.model.template_pixels, self.model.current_pos)

        if update_info:
            self.view.update_info_label(
                self.model.current_score,
                self.model.current_pos,
                self.model.template_angle_degrees
            )
        if update_image_params_display:
             image_params_state = tk.NORMAL if self.model.grayscale_image is not None else tk.DISABLED
             self.view.update_image_parameters_entries(
                 self.model.image_meters_per_pixel,
                 self.model.image_physical_height_meters,
                 image_params_state
             )
        if update_angle_display: # Обновляем поле угла, если нужно
            angle_entry_state = tk.NORMAL if self.model.original_template_pixels is not None else tk.DISABLED
            self.view.update_angle_entry(self.model.template_angle_degrees, angle_entry_state)

        self._update_view_state() # Обновляем состояние всех виджетов

    # --- Обработчики загрузки ---
    def handle_load_image(self, filename=None):
        if not filename:
            filename = filedialog.askopenfilename(
                title="Загрузить изображение",
                filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff"), ("All files", "*.*")],
                parent=self.view.frame)
        if filename:
            try:
                self.model.load_image(filename)
                self._update_full_view(update_info=True, update_image_params_display=True, update_angle_display=True)
                self.view.show_info("Успех", f"Изображение {self.model.image_rows}x{self.model.image_cols} загружено.")
            except Exception as e:
                self._update_full_view(update_info=True, update_image_params_display=True, update_angle_display=True)
                self.view.show_error("Ошибка загрузки изображения", str(e))

    def handle_load_template(self, filename=None):
        if self.model.grayscale_image is None: self.view.show_error("Ошибка", "Сначала загрузите изображение!"); return
        if not filename:
            filename = filedialog.askopenfilename(
                title="Загрузить шаблон из XML",
                filetypes=[("XML Polygon files", "*.xml"), ("All files", "*.*")],
                parent=self.view.frame)
        if filename:
            try:
                self.model.load_template_from_xml(filename)
                self._update_full_view(update_info=True, update_image_params_display=False, update_angle_display=True)
                orig_shape = self.model.original_template_pixels.shape if self.model.original_template_pixels is not None else "N/A"
                self.view.show_info("Успех", f"Шаблон загружен (размер {orig_shape}). Текущий угол: {self.model.template_angle_degrees:.0f}°")
            except Exception as e:
                self._update_full_view(update_info=True, update_image_params_display=False, update_angle_display=True)
                self.view.show_error("Ошибка загрузки шаблона", str(e))

    # --- Обработчики фильтров ---
    def handle_toggle_gauss(self):
        if self.model.grayscale_image is None: self.view.show_error("Ошибка", "Сначала загрузите изображение!"); self.view.update_gauss_button_visuals(False, tk.DISABLED); return
        try:
            success = self.model.toggle_gaussian_blur()
            if success: self._update_full_view(update_info=True)
            else: self._update_view_state()
        except Exception as e: self.view.show_error("Ошибка размытия Гаусса", str(e)); self._update_view_state()

    def handle_apply_sobel(self):
        if self.model.grayscale_image is None: self.view.show_error("Ошибка", "Сначала загрузите изображение!"); return
        try: self.model.apply_sobel(); self._update_full_view(update_info=True)
        except Exception as e: self.view.show_error("Ошибка применения фильтра Собеля", str(e))

    def handle_apply_kirsch(self):
        if self.model.grayscale_image is None: self.view.show_error("Ошибка", "Сначала загрузите изображение!"); return
        try: self.model.apply_kirsch(); self._update_full_view(update_info=True)
        except Exception as e: self.view.show_error("Ошибка применения оператора Кирша", str(e))

    def handle_apply_roberts(self):
        if self.model.grayscale_image is None: self.view.show_error("Ошибка", "Сначала загрузите изображение!"); return
        try: self.model.apply_roberts(); self._update_full_view(update_info=True)
        except Exception as e: self.view.show_error("Ошибка применения оператора Робертса", str(e))

    def handle_apply_prewitt(self):
        if self.model.grayscale_image is None: self.view.show_error("Ошибка", "Сначала загрузите изображение!"); return
        try: self.model.apply_prewitt(); self._update_full_view(update_info=True)
        except Exception as e: self.view.show_error("Ошибка применения оператора Превитта", str(e))

    # --- Обработчики для физических параметров изображения ---
    def handle_image_m_per_px_entry_change(self, event=None):
        if self.model.grayscale_image is None: return
        m_per_px_val = self.view.get_image_m_per_px_entry()
        if m_per_px_val is not None:
            if m_per_px_val > 0:
                self.model.set_image_physical_parameters(meters_per_pixel=m_per_px_val)
                self._update_full_view(update_info=True, update_image_params_display=True, update_angle_display=True)
            else:
                self.view.show_error("Ошибка", "Масштаб изображения (м/пкс) должен быть положительным.")
                self._update_full_view(update_info=False, update_image_params_display=True)

    def handle_image_phys_height_entry_change(self, event=None):
        if self.model.grayscale_image is None: return
        phys_height_val = self.view.get_image_phys_height_entry()
        if phys_height_val is not None:
            if phys_height_val > 0:
                self.model.set_image_physical_parameters(physical_height_meters=phys_height_val)
                self._update_full_view(update_info=True, update_image_params_display=True, update_angle_display=True)
            else:
                self.view.show_error("Ошибка", "Физическая высота изображения должна быть положительной.")
                self._update_full_view(update_info=False, update_image_params_display=True)

    # --- Обработчик поиска ---
    def handle_find_best_match(self):
        if self.model._get_active_edge_image() is None: self.view.show_error("Ошибка", "Сначала примените фильтр границ!"); return
        if self.model.template_pixels is None: self.view.show_error("Ошибка", "Шаблон не загружен или не масштабирован."); return
        try:
            score, pos_rc = self.model.find_best_match()
            self._update_full_view(update_info=True, update_angle_display=True)
            if pos_rc != (-1, -1): self.view.show_info("Поиск завершен", f"Найдено лучшее совпадение со счетом {score:.4f} в позиции {pos_rc} (угол {self.model.template_angle_degrees:.0f}°).")
            else: self.view.show_info("Поиск завершен", "Совпадений не найдено или произошла ошибка.")
        except Exception as e: self.view.show_error("Ошибка при поиске", str(e))

    # --- Обработчики поворота шаблона ---
    def handle_rotate_template_left(self):
        if self.model.original_template_pixels is None: self.view.show_error("Ошибка", "Шаблон не загружен."); return
        new_angle = (self.model.template_angle_degrees - 1)
        if self.model.set_template_angle(new_angle):
            self._update_full_view(update_info=True, update_angle_display=True)
        else:
            self._update_full_view(update_info=False, update_angle_display=True)

    def handle_rotate_template_right(self):
        if self.model.original_template_pixels is None: self.view.show_error("Ошибка", "Шаблон не загружен."); return
        new_angle = (self.model.template_angle_degrees + 1)
        if self.model.set_template_angle(new_angle):
            self._update_full_view(update_info=True, update_angle_display=True)
        else:
            self._update_full_view(update_info=False, update_angle_display=True)

    def handle_angle_entry_change(self, event=None):
        """ Обработка изменения поля ввода угла """
        if self.model.original_template_pixels is None: return
        try:
            angle_str = self.view.get_angle_entry_value() # Убедись, что этот метод есть в View
            new_angle = float(angle_str.replace(',', '.'))
            if self.model.set_template_angle(new_angle):
                self._update_full_view(update_info=True, update_angle_display=True)
            else:
                self._update_full_view(update_info=False, update_angle_display=True)
        except ValueError:
            self.view.show_error("Ошибка ввода", "Угол должен быть числом.")
            self._update_full_view(update_info=False, update_angle_display=True)
        except Exception as e:
            self.view.show_error("Ошибка установки угла", str(e))
            self._update_full_view(update_info=False, update_angle_display=True)

    # --- Обработчики холста ---
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
            self.view.update_info_label(self.model.current_score, self.model.current_pos, self.model.template_angle_degrees)

    def handle_canvas_configure(self, event):
        self._update_full_view(update_info=True, update_image_params_display=False, update_angle_display=False)