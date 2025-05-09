# model/ComparisonModel.py
import xml.etree.ElementTree as ET
import numpy as np
import cv2
from .DrawingModel import DrawingModel, GRID_MARGIN

CV2_MATCH_METHOD = cv2.TM_CCORR # Используем базовую кросс-корреляцию

# Ядра для операторов (определяем один раз)
PREWITT_KERNEL_X = np.array([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]], dtype=np.float32)
PREWITT_KERNEL_Y = np.array([[-1,-1,-1], [ 0, 0, 0], [ 1, 1, 1]], dtype=np.float32)
ROBERTS_KERNEL_X = np.array([[+1, 0], [ 0,-1]], dtype=np.float32)
ROBERTS_KERNEL_Y = np.array([[ 0,+1], [-1, 0]], dtype=np.float32)
KIRSCH_KERNELS = [
    np.array([[ 5,  5,  5], [-3,  0, -3], [-3, -3, -3]], dtype=np.float32), # N
    np.array([[ 5,  5, -3], [ 5,  0, -3], [-3, -3, -3]], dtype=np.float32), # NW
    np.array([[ 5, -3, -3], [ 5,  0, -3], [ 5, -3, -3]], dtype=np.float32), # W
    np.array([[-3, -3, -3], [ 5,  0, -3], [ 5,  5, -3]], dtype=np.float32), # SW
    np.array([[-3, -3, -3], [-3,  0, -3], [ 5,  5,  5]], dtype=np.float32), # S
    np.array([[-3, -3, -3], [-3,  0,  5], [-3,  5,  5]], dtype=np.float32), # SE
    np.array([[-3, -3,  5], [-3,  0,  5], [-3, -3,  5]], dtype=np.float32), # E
    np.array([[-3,  5,  5], [-3,  0,  5], [-3, -3, -3]], dtype=np.float32)  # NE
]

class ComparisonModel:
    def __init__(self):
        self.original_image = None; self.grayscale_image = None;
        self.image_rows = 0; self.image_cols = 0;
        self.gaussian_blur_active = False; self.blurred_image = None
        self.sobel_image = None; self.kirsch_image = None
        self.roberts_image = None; self.prewitt_image = None
        self.image_display_mode = 'original'
        self.image_meters_per_pixel = 0.0
        self.image_physical_height_meters = 0.0
        self.original_template_pixels = None
        self.template_pixels = None
        self.template_scale_factor = 1.0
        self.template_angle_degrees = 0.0
        self.template_rows = 0; self.template_cols = 0
        self.template_max_score = 0
        self.template_physical_height_meters_from_xml = 0.0
        self.template_height_pixels_from_xml = 0
        self.best_score = 0.0; self.best_pos = (-1, -1)
        self.current_pos = (0, 0); self.current_score = 0.0

    def load_image(self, filename):
        try:
            img = cv2.imread(filename, cv2.IMREAD_GRAYSCALE)
            if img is None: raise ValueError(f"Не удалось загрузить изображение.")
            self.original_image = img; self.grayscale_image = img
            self.image_rows, self.image_cols = img.shape[:2]
            self.gaussian_blur_active = False; self.blurred_image = None
            self.sobel_image = None; self.kirsch_image = None
            self.roberts_image = None; self.prewitt_image = None
            self.image_display_mode = 'original'
            self.image_meters_per_pixel = 0.0
            self.image_physical_height_meters = 0.0
            self.reset_template_and_results()
            print(f"Изображение загружено: {self.image_rows}x{self.image_cols}")
        except FileNotFoundError: raise Exception(f"Файл '{filename}' не найден.")
        except Exception as e: self.__init__(); raise Exception(f"Ошибка при загрузке '{filename}': {str(e)}")

    def _get_image_for_filtering(self):
        if self.gaussian_blur_active and self.blurred_image is not None: return self.blurred_image
        elif self.grayscale_image is not None: return self.grayscale_image
        else: return None

    def toggle_gaussian_blur(self, ksize=(5, 5), sigmaX=0):
        if self.grayscale_image is None: return False
        if not self.gaussian_blur_active:
            try: self.blurred_image = cv2.GaussianBlur(self.grayscale_image, ksize, sigmaX); self.gaussian_blur_active = True
            except Exception as e: print(f"Error Gaussian Blur: {e}"); self.gaussian_blur_active = False; self.blurred_image = None; return False
        else: self.gaussian_blur_active = False; self.blurred_image = None
        current_mode = self.image_display_mode
        try:
            if not self.gaussian_blur_active or current_mode != 'original': self.image_display_mode = 'original'
            if current_mode == 'sobel': self.apply_sobel()
            elif current_mode == 'kirsch': self.apply_kirsch()
            elif current_mode == 'roberts': self.apply_roberts()
            elif current_mode == 'prewitt': self.apply_prewitt()
            else: self._recalculate_current_score()
        except Exception as e: print(f"Error re-applying filter: {e}"); self.image_display_mode = 'original'; self.reset_results(); return False
        return True

    def _apply_edge_filter(self, filter_func, *args, **kwargs):
        input_img = self._get_image_for_filtering()
        if input_img is None: raise ValueError("Нет изображения для применения фильтра.")
        try:
            edge_image_01 = filter_func(input_img, *args, **kwargs)
            return edge_image_01
        except Exception as e:
            raise Exception(f"Ошибка при применении фильтра {filter_func.__name__}: {str(e)}")

    def _sobel_logic(self, img, ksize=3, threshold_value=50):
        sobelx = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=ksize)
        sobely = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=ksize)
        magnitude = np.sqrt(sobelx**2 + sobely**2)
        if np.max(magnitude) > 0: magnitude = (magnitude / np.max(magnitude) * 255)
        magnitude = magnitude.astype(np.uint8)
        _, binary = cv2.threshold(magnitude, threshold_value, 255, cv2.THRESH_BINARY)
        return (binary // 255).astype(np.uint8)

    def _kirsch_logic(self, img, threshold_value=60):
        gray_float = img.astype(np.float32)
        convolved_images = [cv2.filter2D(gray_float, -1, k) for k in KIRSCH_KERNELS]
        max_magnitude = np.max(np.abs(np.stack(convolved_images, axis=0)), axis=0)
        if np.max(max_magnitude) > 0: max_magnitude = (max_magnitude / np.max(max_magnitude) * 255)
        max_magnitude = max_magnitude.astype(np.uint8)
        _, binary = cv2.threshold(max_magnitude, threshold_value, 255, cv2.THRESH_BINARY)
        return (binary // 255).astype(np.uint8)

    def _roberts_logic(self, img, threshold_value=30):
        img_float = img.astype(np.float64)
        roberts_x_img = cv2.filter2D(img_float, -1, ROBERTS_KERNEL_X)
        roberts_y_img = cv2.filter2D(img_float, -1, ROBERTS_KERNEL_Y)
        magnitude = np.sqrt(roberts_x_img**2 + roberts_y_img**2)
        if np.max(magnitude) > 0: magnitude = (magnitude / np.max(magnitude) * 255)
        magnitude = magnitude.astype(np.uint8)
        _, binary = cv2.threshold(magnitude, threshold_value, 255, cv2.THRESH_BINARY)
        return (binary // 255).astype(np.uint8)

    def _prewitt_logic(self, img, threshold_value=50):
        img_float = img.astype(np.float64)
        prewitt_x_img = cv2.filter2D(img_float, -1, PREWITT_KERNEL_X)
        prewitt_y_img = cv2.filter2D(img_float, -1, PREWITT_KERNEL_Y)
        magnitude = np.sqrt(prewitt_x_img**2 + prewitt_y_img**2)
        if np.max(magnitude) > 0: magnitude = (magnitude / np.max(magnitude) * 255)
        magnitude = magnitude.astype(np.uint8)
        _, binary = cv2.threshold(magnitude, threshold_value, 255, cv2.THRESH_BINARY)
        return (binary // 255).astype(np.uint8)

    def apply_sobel(self, ksize=3, threshold_value=50):
        self.sobel_image = self._apply_edge_filter(self._sobel_logic, ksize=ksize, threshold_value=threshold_value)
        self.image_display_mode = 'sobel'
        self.reset_results(); self._recalculate_current_score()
        print(f"Собель применен {'с размытием' if self.gaussian_blur_active else 'без размытия'}.")

    def apply_kirsch(self, threshold_value=60):
        self.kirsch_image = self._apply_edge_filter(self._kirsch_logic, threshold_value=threshold_value)
        self.image_display_mode = 'kirsch'
        self.reset_results(); self._recalculate_current_score()
        print(f"Кирш применен {'с размытием' if self.gaussian_blur_active else 'без размытия'}.")

    def apply_roberts(self, threshold_value=30):
        self.roberts_image = self._apply_edge_filter(self._roberts_logic, threshold_value=threshold_value)
        self.image_display_mode = 'roberts'
        self.reset_results(); self._recalculate_current_score()
        print(f"Робертс применен {'с размытием' if self.gaussian_blur_active else 'без размытия'}.")

    def apply_prewitt(self, threshold_value=50):
        self.prewitt_image = self._apply_edge_filter(self._prewitt_logic, threshold_value=threshold_value)
        self.image_display_mode = 'prewitt'
        self.reset_results(); self._recalculate_current_score()
        print(f"Превитт применен {'с размытием' if self.gaussian_blur_active else 'без размытия'}.")

    def _recalculate_current_score(self):
        if self.template_pixels is not None and self._get_active_edge_image() is not None:
            self.current_score = self.get_score_at(self.current_pos[0], self.current_pos[1])
        else:
            self.current_score = 0.0

    def get_display_image(self):
        active_edge_image = self._get_active_edge_image()
        if active_edge_image is not None: return (active_edge_image * 255).astype(np.uint8)
        elif self.gaussian_blur_active and self.blurred_image is not None: return self.blurred_image
        elif self.grayscale_image is not None: return self.grayscale_image
        else: return None

    def load_template_from_xml(self, filename):
        try:
            parser_model = DrawingModel(1, 1)
            parser_model.load_from_xml(filename)
            if not parser_model.vertices: raise ValueError("В файле не найдено корректных вершин.")
            self.template_physical_height_meters_from_xml = parser_model.template_physical_height_meters
            min_y_tpl, max_y_tpl = float('inf'), float('-inf')
            if parser_model.vertices:
                for _, y_coord in parser_model.vertices:
                    if y_coord < min_y_tpl: min_y_tpl = y_coord
                    if y_coord > max_y_tpl: max_y_tpl = y_coord
                self.template_height_pixels_from_xml = (max_y_tpl - min_y_tpl + 1) if max_y_tpl >= min_y_tpl else 0
            else: self.template_height_pixels_from_xml = 0
            print(f"Загружено из XML: Физ. высота шаблона = {self.template_physical_height_meters_from_xml} м, Пикс. высота шаблона = {self.template_height_pixels_from_xml}")
            max_x = -1; max_y = -1
            for x, y in parser_model.vertices:
                if x > max_x: max_x = x
                if y > max_y: max_y = y
            template_actual_rows = max_y + 1; template_actual_cols = max_x + 1
            if template_actual_rows <= 0 or template_actual_cols <= 0: raise ValueError("Не удалось определить размеры шаблона.")
            outline_model = DrawingModel(template_actual_rows, template_actual_cols)
            outline_model.vertices = parser_model.vertices
            outline_model.update_field()
            self.original_template_pixels = np.array(outline_model.pixel_field, dtype=np.uint8)
            if np.sum(self.original_template_pixels) == 0: print("Предупреждение: Шаблон пуст после отрисовки.")
            self.template_angle_degrees = 0.0
            self._adjust_template_scale_to_image()
            self.reset_results(); self.set_current_pos(0, 0)
            print(f"Шаблон загружен (контур {self.original_template_pixels.shape}), тек. масштаб. фактор {self.template_scale_factor:.3f} -> ({self.template_rows}x{self.template_cols})")
        except Exception as e: self.reset_template_and_results(); raise Exception(f"Ошибка загрузки/обработки шаблона '{filename}': {str(e)}")

    def set_image_physical_parameters(self, meters_per_pixel=None, physical_height_meters=None):
        if self.image_rows <= 0: print("Ошибка: Изображение не загружено."); return False
        if meters_per_pixel is not None and meters_per_pixel > 0 :
            self.image_meters_per_pixel = meters_per_pixel
            self.image_physical_height_meters = self.image_rows * self.image_meters_per_pixel
        elif physical_height_meters is not None and physical_height_meters > 0:
            self.image_physical_height_meters = physical_height_meters
            self.image_meters_per_pixel = self.image_physical_height_meters / self.image_rows
        else: return False
        print(f"Параметры изображения: м/пкс={self.image_meters_per_pixel:.4f}, физ.высота={self.image_physical_height_meters:.2f} м")
        self._adjust_template_scale_to_image()
        self._recalculate_current_score()
        return True

    def _adjust_template_scale_to_image(self):
        if self.original_template_pixels is None or self.image_meters_per_pixel <= 0 or \
           self.template_physical_height_meters_from_xml <= 0 or self.template_height_pixels_from_xml <= 0:
            print("Недостаточно данных для автоподстройки масштаба шаблона. Используется текущий относительный масштаб.")
            return self._apply_template_scale()
        template_xml_m_per_pixel = self.template_physical_height_meters_from_xml / self.template_height_pixels_from_xml
        new_scale_factor = template_xml_m_per_pixel / self.image_meters_per_pixel
        print(f"Автоподстройка: Image м/пкс={self.image_meters_per_pixel:.4f}, "
              f"Tpl XML м/пкс={template_xml_m_per_pixel:.4f}, "
              f"Новый фактор масштаба={new_scale_factor:.3f}")
        self.template_scale_factor = new_scale_factor
        return self._apply_template_scale()

    def set_template_angle(self, angle_degrees):
        if self.original_template_pixels is None: return False
        new_angle = angle_degrees % 360.0 # Убедимся, что это float для сравнения
        if abs(new_angle - self.template_angle_degrees) < 1e-5:
            return False # Угол не изменился существенно
        self.template_angle_degrees = new_angle
        if self._apply_template_scale(): # Перегенерирует self.template_pixels с новым углом
            self.reset_results()
            self.set_current_pos(self.current_pos[0], self.current_pos[1])
            print(f"Угол шаблона изменен на {self.template_angle_degrees:.1f}°. Перегенерирован шаблон.")
            return True
        else:
            print(f"Не удалось применить угол {self.template_angle_degrees:.1f}°.")
            return False

    def _apply_template_scale(self): # Теперь также применяет поворот
        if self.original_template_pixels is None: return False

        # 1. Поворот оригинального шаблона (original_template_pixels)
        src_h, src_w = self.original_template_pixels.shape[:2]
        if src_h == 0 or src_w == 0: return False # Нечего поворачивать/масштабировать

        center_x, center_y = src_w / 2.0, src_h / 2.0 # Используем float для центра
        rotation_matrix = cv2.getRotationMatrix2D((center_x, center_y), self.template_angle_degrees, 1.0)

        cos_abs = np.abs(rotation_matrix[0, 0])
        sin_abs = np.abs(rotation_matrix[0, 1])
        new_w = int(np.ceil((src_h * sin_abs) + (src_w * cos_abs))) # Округляем вверх
        new_h = int(np.ceil((src_h * cos_abs) + (src_w * sin_abs)))

        rotation_matrix[0, 2] += (new_w / 2.0) - center_x
        rotation_matrix[1, 2] += (new_h / 2.0) - center_y

        # Применяем поворот к original_template_pixels
        rotated_template = cv2.warpAffine(self.original_template_pixels, rotation_matrix, (new_w, new_h),
                                          flags=cv2.INTER_NEAREST, borderValue=0) # INTER_NEAREST для бинарных
        rotated_template_binary = (rotated_template > 0.5).astype(np.uint8)

        # 2. Масштабирование повернутого шаблона
        current_scale_factor = self.template_scale_factor
        final_rows = max(1, int(np.round(rotated_template_binary.shape[0] * current_scale_factor)))
        final_cols = max(1, int(np.round(rotated_template_binary.shape[1] * current_scale_factor)))

        if self.image_rows > 0 and self.image_cols > 0:
             if final_rows > self.image_rows or final_cols > self.image_cols:
                 print(f"Предупреждение: Повернутый/масштабированный шаблон ({final_rows}x{final_cols}) больше изображения ({self.image_rows}x{self.image_cols}).")
                 return False
        try:
            if final_rows <=0 or final_cols <=0: return False

            scaled_and_rotated_template = cv2.resize(rotated_template_binary, (final_cols, final_rows), interpolation=cv2.INTER_NEAREST)
            self.template_pixels = (scaled_and_rotated_template > 0.5).astype(np.uint8)
            self.template_rows, self.template_cols = self.template_pixels.shape
            self.template_max_score = np.sum(self.template_pixels)
            return True
        except Exception as e: print(f"Ошибка масштабирования/поворота: {e}"); return False

    def _get_active_edge_image(self):
        if self.image_display_mode == 'sobel' and self.sobel_image is not None: return self.sobel_image
        elif self.image_display_mode == 'kirsch' and self.kirsch_image is not None: return self.kirsch_image
        elif self.image_display_mode == 'roberts' and self.roberts_image is not None: return self.roberts_image
        elif self.image_display_mode == 'prewitt' and self.prewitt_image is not None: return self.prewitt_image
        else: return None

    def find_best_match(self):
        active_edge_image = self._get_active_edge_image()
        if active_edge_image is None: raise ValueError("Фильтр границ не применен.")
        if self.template_pixels is None: raise ValueError("Шаблон не загружен.")
        if self.template_rows > self.image_rows or self.template_cols > self.image_cols: raise ValueError("Шаблон больше изображения.")
        if self.template_max_score <= 0:
            print("Предупреждение: Поиск с пустым шаблоном (max_score=0)."); self.best_score = 0.0; self.best_pos = (0, 0); self.current_pos = (0, 0); self.current_score = 0.0
            return self.best_score, self.best_pos
        try:
            tpl_for_match = self.template_pixels
            img_float = active_edge_image.astype(np.float32)
            tpl_float = tpl_for_match.astype(np.float32)
            result_map_raw = cv2.matchTemplate(img_float, tpl_float, CV2_MATCH_METHOD)
            epsilon = 1e-7
            result_map_normalized = result_map_raw / (self.template_max_score + epsilon)
            minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(result_map_normalized)
            self.best_score = float(maxVal); best_r, best_c = maxLoc[1], maxLoc[0]
            self.best_pos = (best_r, best_c); self.best_score = np.clip(self.best_score, 0.0, 1.0)
            self.current_pos = self.best_pos; self.current_score = self.best_score
            print(f"Лучшее совпадение (Custom Normalized CCORR на {self.image_display_mode}): счет={self.best_score:.4f} в {self.best_pos}, Угол: {self.template_angle_degrees:.1f}°") # Добавил угол
        except cv2.error as e:
             if "template size is larger than image size" in str(e): raise ValueError("Ошибка OpenCV: Шаблон больше изображения.")
             else: print(f"Ошибка cv2.matchTemplate: {e}"); self.reset_results(); raise Exception(f"Ошибка поиска: {str(e)}")
        except Exception as e: print(f"Неизвестная ошибка поиска: {e}"); self.reset_results(); raise Exception(f"Неизвестная ошибка поиска: {str(e)}")
        return self.best_score, self.best_pos

    def get_score_at(self, r, c):
        active_edge_image = self._get_active_edge_image()
        if active_edge_image is None or self.template_pixels is None: return 0.0
        if self.template_max_score <= 0: return 0.0
        if 0 <= r <= self.image_rows - self.template_rows and 0 <= c <= self.image_cols - self.template_cols:
            try:
                img_slice = active_edge_image[r : r + self.template_rows, c : c + self.template_cols]
                img_slice_float = img_slice.astype(np.float32)
                tpl_float = self.template_pixels.astype(np.float32)
                result_raw = cv2.matchTemplate(img_slice_float, tpl_float, CV2_MATCH_METHOD)
                raw_score = result_raw[0, 0]
                epsilon = 1e-7
                normalized_score = raw_score / (self.template_max_score + epsilon)
                score = np.clip(normalized_score, 0.0, 1.0)
                return float(score)
            except (cv2.error, Exception): return 0.0
        else: return 0.0

    def set_current_pos(self, r, c):
        if (self.grayscale_image is None) or self.template_pixels is None: return False
        max_r = self.image_rows - self.template_rows; max_c = self.image_cols - self.template_cols
        max_r = max(-1, max_r); max_c = max(-1, max_c)
        valid_r = max(0, min(r, max_r)) if max_r >= 0 else 0; valid_c = max(0, min(c, max_c)) if max_c >= 0 else 0
        if max_r < 0: valid_r = 0;
        if max_c < 0: valid_c = 0;
        new_pos = (valid_r, valid_c); position_changed = (new_pos != self.current_pos)
        self.current_pos = new_pos; self._recalculate_current_score()
        return position_changed

    def reset_results(self):
        self.best_score = 0.0; self.best_pos = (-1, -1); self.current_pos = (0, 0)
        self._recalculate_current_score()

    def reset_template_and_results(self):
        self.original_template_pixels = None; self.template_pixels = None
        self.template_scale_factor = 1.0; self.template_angle_degrees = 0.0
        self.template_rows = 0; self.template_cols = 0
        self.template_max_score = 0
        self.template_physical_height_meters_from_xml = 0.0
        self.template_height_pixels_from_xml = 0
        self.reset_results()