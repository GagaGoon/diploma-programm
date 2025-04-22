# model/ComparisonModel.py
import xml.etree.ElementTree as ET
import numpy as np
import cv2
from .DrawingModel import DrawingModel

# Метод сравнения для OpenCV (базовая кросс-корреляция)
CV2_MATCH_METHOD = cv2.TM_CCORR

class ComparisonModel:
    """
    Модель данных для вкладки сравнения.
    ИЗМЕНЕНО: Используется кастомная нормализация TM_CCORR.
             Результат - доля совпавших активных пикселей [0, 1].
    """
    def __init__(self):
        # Изображение
        self.original_image = None; self.grayscale_image = None; self.sobel_image = None
        self.image_rows = 0; self.image_cols = 0; self.image_display_mode = 'original'
        # Шаблон
        self.original_template_pixels = None; self.template_pixels = None
        self.template_scale = 1.0; self.template_rows = 0; self.template_cols = 0
        # --- НОВОЕ: Максимально возможный счет для текущего шаблона ---
        self.template_max_score = 0
        # --- Результаты (счет будет от 0 до 1) ---
        self.best_score = 0.0
        self.best_pos = (-1, -1)
        self.current_pos = (0, 0); self.current_score = 0.0

    # --- Методы загрузки и обработки изображения (без изменений) ---
    def load_image(self, filename):
        try:
            img = cv2.imread(filename, cv2.IMREAD_GRAYSCALE)
            if img is None: raise ValueError(f"Не удалось загрузить изображение.")
            self.original_image = img; self.grayscale_image = img
            self.image_rows, self.image_cols = img.shape[:2]
            self.sobel_image = None; self.image_display_mode = 'original'
            self.reset_template_and_results()
            print(f"Изображение загружено: {self.image_rows}x{self.image_cols}")
        except FileNotFoundError: raise Exception(f"Файл '{filename}' не найден.")
        except Exception as e: self.__init__(); raise Exception(f"Ошибка при загрузке '{filename}': {str(e)}")

    def apply_sobel(self, ksize=3, threshold_value=30):
        """
        Применяет фильтр Собеля к grayscale_image и бинаризует результат.
        БЕЗ морфологических операций.
        """
        if self.grayscale_image is None: raise ValueError("Изображение не загружено...")
        try:
            # 1. Применяем Собель
            sobelx = cv2.Sobel(self.grayscale_image, cv2.CV_64F, 1, 0, ksize=ksize)
            sobely = cv2.Sobel(self.grayscale_image, cv2.CV_64F, 0, 1, ksize=ksize)
            magnitude = np.sqrt(sobelx ** 2 + sobely ** 2)
            if np.max(magnitude) > 0: magnitude = (magnitude / np.max(magnitude) * 255)
            magnitude = magnitude.astype(np.uint8)

            # 2. Бинаризация по порогу
            _, binary_sobel = cv2.threshold(magnitude, threshold_value, 255, cv2.THRESH_BINARY)

            # 3. Конвертация в 0/1 (uint8)
            binary_01 = (binary_sobel // 255).astype(np.uint8)

            # --- Морфологическое открытие УБРАНО ---

            # 4. Сохраняем результат СРАЗУ ПОСЛЕ бинаризации
            self.sobel_image = binary_01
            # -----------------------------------------

            self.image_display_mode = 'sobel';
            self.reset_results()
            if self.template_pixels is not None:
                self.current_score = self.get_score_at(self.current_pos[0], self.current_pos[1])
            else:
                self.current_score = 0.0
            print(f"Фильтр Собеля (threshold={threshold_value}) применен (без морфологии).")
        except Exception as e:
            raise Exception(f"Ошибка при применении Собеля: {str(e)}")

    def get_display_image(self):
        if self.image_display_mode == 'sobel' and self.sobel_image is not None: return (self.sobel_image * 255).astype(np.uint8)
        elif self.grayscale_image is not None: return self.grayscale_image
        else: return None

    # --- Метод загрузки шаблона (генерирует контур, без изменений) ---
    def load_template_from_xml(self, filename):
        try:
            parser_model = DrawingModel(1, 1)
            parser_model.load_from_xml(filename)
            if not parser_model.vertices: raise ValueError("В файле не найдено корректных вершин.")
            max_x = -1; max_y = -1
            for x, y in parser_model.vertices:
                if x > max_x: max_x = x
                if y > max_y: max_y = y
            template_actual_rows = max_y + 1; template_actual_cols = max_x + 1
            if template_actual_rows <= 0 or template_actual_cols <= 0: raise ValueError("Не удалось определить размеры шаблона.")
            outline_model = DrawingModel(template_actual_rows, template_actual_cols)
            outline_model.vertices = parser_model.vertices
            outline_model.update_field() # Генерируем контур
            self.original_template_pixels = np.array(outline_model.pixel_field, dtype=np.uint8)
            if np.sum(self.original_template_pixels) == 0: print("Предупреждение: Шаблон пуст после отрисовки.")
            self.template_scale = 1.0
            scale_applied = self._apply_template_scale() # Создаст self.template_pixels и self.template_max_score
            if not scale_applied: self.reset_template_and_results(); raise ValueError("Не удалось применить масштаб.")
            self.reset_results(); self.set_current_pos(0, 0) # Пересчитает current_score
            print(f"Шаблон загружен (контур {self.original_template_pixels.shape}), масштаб {self.template_scale:.2f} -> ({self.template_rows}x{self.template_cols})")
        except Exception as e: self.reset_template_and_results(); raise Exception(f"Ошибка загрузки/обработки шаблона '{filename}': {str(e)}")

    # --- Методы масштабирования ---
    def set_template_scale(self, scale):
        if self.original_template_pixels is None: return False
        if scale <= 0: return False
        if abs(scale - self.template_scale) < 1e-5: return False
        old_scale = self.template_scale; self.template_scale = scale
        scale_applied = self._apply_template_scale() # Пересоздаст self.template_pixels и self.template_max_score
        if scale_applied:
            self.reset_results(); self.set_current_pos(0, 0) # Пересчитает current_score
            print(f"Масштаб изменен на {self.template_scale:.2f} -> ({self.template_rows}x{self.template_cols})")
            return True
        else:
            print(f"Не удалось применить масштаб {scale:.2f}. Возврат к {old_scale:.2f}.")
            self.template_scale = old_scale; self._apply_template_scale() # Восстанавливаем
            return False

    def _apply_template_scale(self):
        """ Применяет масштаб и пересчитывает template_max_score """
        if self.original_template_pixels is None: return False
        original_rows, original_cols = self.original_template_pixels.shape
        new_rows = max(1, int(np.round(original_rows * self.template_scale)))
        new_cols = max(1, int(np.round(original_cols * self.template_scale)))
        if self.grayscale_image is not None:
             if new_rows > self.image_rows or new_cols > self.image_cols: return False
        try:
            resized_template = cv2.resize(self.original_template_pixels, (new_cols, new_rows), interpolation=cv2.INTER_NEAREST)
            self.template_pixels = (resized_template > 0.5).astype(np.uint8)
            self.template_rows, self.template_cols = self.template_pixels.shape
            # --- ПЕРЕСЧЕТ MAX SCORE ---
            self.template_max_score = np.sum(self.template_pixels)
            # --- КОНЕЦ ПЕРЕСЧЕТА ---
            return True
        except Exception as e: print(f"Ошибка масштабирования: {e}"); return False

    # --- ИЗМЕНЕННЫЕ МЕТОДЫ РАСЧЕТА СОВПАДЕНИЯ ---
    def find_best_match(self):
        """ Ищет наилучшее положение по TM_CCORR и нормализует результат """
        if self.sobel_image is None: raise ValueError("Фильтр Собеля не применен.")
        if self.template_pixels is None: raise ValueError("Шаблон не загружен.")
        if self.template_rows > self.image_rows or self.template_cols > self.image_cols: raise ValueError("Шаблон больше изображения.")
        # Проверяем max_score перед делением
        if self.template_max_score <= 0:
            print("Предупреждение: Поиск с пустым шаблоном (max_score=0).")
            self.best_score = 0.0; self.best_pos = (0, 0); self.current_pos = (0, 0); self.current_score = 0.0
            return self.best_score, self.best_pos
        try:
            img_for_match = self.sobel_image
            tpl_for_match = self.template_pixels

            # Используем float32 для matchTemplate
            img_float = img_for_match.astype(np.float32)
            tpl_float = tpl_for_match.astype(np.float32)

            # 1. Вычисляем базовую кросс-корреляцию
            result_map_raw = cv2.matchTemplate(img_float, tpl_float, CV2_MATCH_METHOD)

            # 2. Нормализуем результат вручную
            # Делим на количество единиц в шаблоне
            # Добавляем малое число epsilon, чтобы избежать деления на ноль, если max_score вдруг 0 (хотя мы проверили)
            epsilon = 1e-7
            result_map_normalized = result_map_raw / (self.template_max_score + epsilon)

            # 3. Находим максимум в НОРМАЛИЗОВАННОЙ карте
            minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(result_map_normalized)

            # TM_CCORR максимизируется
            self.best_score = float(maxVal)
            best_r, best_c = maxLoc[1], maxLoc[0]
            self.best_pos = (best_r, best_c)

            # Ограничиваем счет диапазоном [0, 1] на всякий случай
            self.best_score = np.clip(self.best_score, 0.0, 1.0)

            self.current_pos = self.best_pos
            self.current_score = self.best_score # Используем найденный нормализованный счет

            print(f"Лучшее совпадение (Custom Normalized CCORR): счет={self.best_score:.4f} в {self.best_pos}")

        except cv2.error as e:
             if "template size is larger than image size" in str(e): raise ValueError("Ошибка OpenCV: Шаблон больше изображения.")
             else: print(f"Ошибка cv2.matchTemplate: {e}"); self.reset_results(); raise Exception(f"Ошибка поиска: {str(e)}")
        except Exception as e: print(f"Неизвестная ошибка поиска: {e}"); self.reset_results(); raise Exception(f"Неизвестная ошибка поиска: {str(e)}")
        return self.best_score, self.best_pos

    def get_score_at(self, r, c):
        """ Вычисляет счет по TM_CCORR и нормализует для текущей позиции (r, c) """
        if self.sobel_image is None or self.template_pixels is None: return 0.0
        # Проверяем max_score
        if self.template_max_score <= 0: return 0.0

        if 0 <= r <= self.image_rows - self.template_rows and 0 <= c <= self.image_cols - self.template_cols:
            try:
                img_slice = self.sobel_image[r : r + self.template_rows, c : c + self.template_cols]

                img_slice_float = img_slice.astype(np.float32)
                tpl_float = self.template_pixels.astype(np.float32)

                # 1. Вычисляем базовую кросс-корреляцию
                result_raw = cv2.matchTemplate(img_slice_float, tpl_float, CV2_MATCH_METHOD)
                raw_score = result_raw[0, 0]

                # 2. Нормализуем вручную
                epsilon = 1e-7
                normalized_score = raw_score / (self.template_max_score + epsilon)

                # 3. Ограничиваем результат [0, 1]
                score = np.clip(normalized_score, 0.0, 1.0)

                return float(score)
            except (cv2.error, Exception): return 0.0
        else: return 0.0

    # --- Методы управления состоянием (без изменений) ---
    def set_current_pos(self, r, c):
        if (self.grayscale_image is None and self.sobel_image is None) or self.template_pixels is None: return False
        max_r = self.image_rows - self.template_rows; max_c = self.image_cols - self.template_cols
        max_r = max(-1, max_r); max_c = max(-1, max_c)
        valid_r = max(0, min(r, max_r)) if max_r >= 0 else 0; valid_c = max(0, min(c, max_c)) if max_c >= 0 else 0
        if max_r < 0: valid_r = 0;
        if max_c < 0: valid_c = 0;
        new_pos = (valid_r, valid_c); position_changed = (new_pos != self.current_pos)
        self.current_pos = new_pos; new_score = self.get_score_at(self.current_pos[0], self.current_pos[1]) # Пересчитываем нормализованный счет
        self.current_score = new_score; return position_changed

    def reset_results(self):
        self.best_score = 0.0; self.best_pos = (-1, -1); self.current_pos = (0, 0)
        if self.template_pixels is not None: self.current_score = self.get_score_at(0, 0)
        else: self.current_score = 0.0

    def reset_template_and_results(self):
        self.original_template_pixels = None; self.template_pixels = None
        self.template_scale = 1.0; self.template_rows = 0; self.template_cols = 0
        self.template_max_score = 0 # Сбрасываем max_score
        self.reset_results()