# model/ComparisonModel.py
import xml.etree.ElementTree as ET
import numpy as np
from .DrawingModel import DrawingModel # Импортируем для загрузки шаблона

class ComparisonModel:
    """
    Модель данных для вкладки сравнения.
    Хранит пиксельные данные изображения и шаблона, результаты сравнения.
    """
    def __init__(self):
        self.image_pixels = None    # numpy array
        self.image_rows = 0
        self.image_cols = 0

        self.template_pixels = None # numpy array
        self.template_rows = 0
        self.template_cols = 0

        self.best_score = -np.inf # Используем -inf для поиска максимума
        self.best_pos = (-1, -1)  # (row, col)

        self.current_pos = (0, 0) # Текущее положение ВЕРХНЕГО ЛЕВОГО угла шаблона
        self.current_score = 0

    def load_image_from_xml(self, filename):
        """ Загружает изображение из специального XML формата """
        try:
            tree = ET.parse(filename)
            root = tree.getroot()
            if root.tag != 'image':
                raise ValueError("Корневой тег должен быть 'image'")

            size_tag = root.find("size")
            if size_tag is None: raise ValueError("Тег 'size' не найден")
            img_rows = int(size_tag.get("rows"))
            img_cols = int(size_tag.get("cols"))
            if img_rows <= 0 or img_cols <= 0:
                 raise ValueError("Размеры изображения должны быть положительными")

            pixels_tag = root.find("pixels")
            if pixels_tag is None: raise ValueError("Тег 'pixels' не найден")

            rows_data = pixels_tag.findall("row")
            if len(rows_data) != img_rows:
                raise ValueError(f"Ожидалось {img_rows} строк (<row>), найдено {len(rows_data)}")

            loaded_image_pixels = np.zeros((img_rows, img_cols), dtype=np.uint8) # uint8 экономичнее
            for i, row_tag in enumerate(rows_data):
                row_text = row_tag.text.strip() if row_tag.text else ""
                if len(row_text) != img_cols:
                    raise ValueError(f"Строка {i+1}: ожидалось {img_cols} символов, найдено {len(row_text)}")
                for j, char in enumerate(row_text):
                    if char == '1':
                        loaded_image_pixels[i, j] = 1
                    elif char != '0':
                         raise ValueError(f"Строка {i+1}, столбец {j+1}: недопустимый символ '{char}', ожидался '0' или '1'")

            # Успешная загрузка - обновляем состояние модели
            self.image_pixels = loaded_image_pixels
            self.image_rows = img_rows
            self.image_cols = img_cols
            # Сбрасываем шаблон и результаты при загрузке нового изображения
            self.reset_template_and_results()
            print(f"Изображение загружено: {self.image_rows}x{self.image_cols}")

        except ET.ParseError as e:
             raise Exception(f"Ошибка парсинга XML изображения '{filename}': {str(e)}")
        except FileNotFoundError:
             raise Exception(f"Файл изображения '{filename}' не найден.")
        except (ValueError, TypeError, AttributeError) as e:
             raise Exception(f"Ошибка в структуре или данных файла изображения '{filename}': {str(e)}")
        except Exception as e:
             raise Exception(f"Неизвестная ошибка при загрузке изображения '{filename}': {str(e)}")

    def load_template_from_xml(self, filename):
        """ Загружает шаблон из XML (формат DrawingModel) и сохраняет пиксельную сетку """
        try:
            # Используем DrawingModel для парсинга XML шаблона
            temp_model = DrawingModel(1, 1) # Временная модель
            temp_model.load_from_xml(filename) # Загружаем размер и вершины, поле обновляется внутри

            # Проверяем, что шаблон не пустой
            if temp_model.rows <= 0 or temp_model.cols <= 0:
                raise ValueError("Шаблон имеет нулевые размеры.")
            if np.sum(temp_model.pixel_field) == 0:
                 print("Предупреждение: Загруженный шаблон не содержит активных пикселей.")


            # Проверяем, что шаблон не больше текущего изображения (если оно загружено)
            if self.image_pixels is not None:
                if temp_model.rows > self.image_rows or temp_model.cols > self.image_cols:
                    raise ValueError(f"Шаблон ({temp_model.rows}x{temp_model.cols}) "
                                     f"больше изображения ({self.image_rows}x{self.image_cols})")

            # Успешная загрузка - обновляем состояние модели
            self.template_rows = temp_model.rows
            self.template_cols = temp_model.cols
            self.template_pixels = np.array(temp_model.pixel_field, dtype=np.uint8)
            # Сбрасываем результаты при загрузке нового шаблона
            self.reset_results()
            print(f"Шаблон загружен: {self.template_rows}x{self.template_cols}")

        except Exception as e:
             # Перехватываем ошибки от load_from_xml и свои
             raise Exception(f"Ошибка при загрузке шаблона '{filename}': {str(e)}")

    def calculate_match_score(self, img_slice, template):
        """
        Вычисляет метрику схожести. Простое совпадение '1' (сумма поэлементного умножения).
        """
        if img_slice.shape != template.shape:
             # Эта проверка важна
             print(f"Ошибка: Размеры среза {img_slice.shape} и шаблона {template.shape} не совпадают!")
             return -np.inf # Возвращаем худший возможный счет
        # Подсчет совпадающих '1'
        score = np.sum(img_slice * template)
        return score

    def find_best_match(self):
        """ Ищет наилучшее положение шаблона на изображении """
        if self.image_pixels is None or self.template_pixels is None:
            raise ValueError("Изображение или шаблон не загружены для поиска.")
        if self.template_rows > self.image_rows or self.template_cols > self.image_cols:
             # Эта проверка дублируется из load_template, но полезна на случай прямого изменения
             raise ValueError("Шаблон больше изображения.")

        # Сбрасываем предыдущий лучший результат
        self.best_score = -np.inf
        self.best_pos = (-1, -1)
        found_match = False

        # Итерация по всем возможным верхним левым позициям шаблона
        for r in range(self.image_rows - self.template_rows + 1):
            for c in range(self.image_cols - self.template_cols + 1):
                # Вырезаем кусок изображения размером с шаблон
                img_slice = self.image_pixels[r : r + self.template_rows, c : c + self.template_cols]
                # Считаем совпадение
                score = self.calculate_match_score(img_slice, self.template_pixels)

                # Обновляем лучший результат
                if score > self.best_score:
                    self.best_score = score
                    self.best_pos = (r, c)
                    found_match = True

        if found_match:
             print(f"Лучшее совпадение: счет={self.best_score} в позиции (row={self.best_pos[0]}, col={self.best_pos[1]})")
             # Устанавливаем текущую позицию на лучшую
             self.current_pos = self.best_pos
             self.current_score = self.best_score
        else:
             # Это может произойти, если все срезы дали -inf или если шаблон/изображение пустые
             print("Совпадений не найдено или счет всегда был минимальным.")
             self.best_score = 0 # Или другое значение по умолчанию
             self.best_pos = (-1, -1)
             self.current_pos = (0, 0) # Сброс текущей позиции
             self.current_score = self.get_score_at(0, 0) if self.template_pixels is not None else 0


        return self.best_score, self.best_pos

    def get_score_at(self, r, c):
        """ Вычисляет счет для текущей позиции (r, c) верхнего левого угла шаблона """
        if self.image_pixels is None or self.template_pixels is None:
            return 0 # Нет данных для расчета

        # Проверка, помещается ли шаблон в данной позиции
        if 0 <= r <= self.image_rows - self.template_rows and \
           0 <= c <= self.image_cols - self.template_cols:
            img_slice = self.image_pixels[r : r + self.template_rows, c : c + self.template_cols]
            score = self.calculate_match_score(img_slice, self.template_pixels)
            return score
        else:
            # Позиция некорректна
            return 0 # Или можно вернуть -np.inf, если это имеет смысл для логики

    def set_current_pos(self, r, c):
        """ Устанавливает текущую позицию шаблона с проверкой границ """
        if self.image_pixels is None or self.template_pixels is None:
            return False # Некуда ставить шаблон

        # Проверяем и корректируем границы
        max_r = self.image_rows - self.template_rows
        max_c = self.image_cols - self.template_cols
        valid_r = max(0, min(r, max_r))
        valid_c = max(0, min(c, max_c))

        if (valid_r, valid_c) != self.current_pos:
            self.current_pos = (valid_r, valid_c)
            self.current_score = self.get_score_at(valid_r, valid_c)
            return True # Позиция изменилась
        return False # Позиция не изменилась

    def reset_results(self):
        """ Сбрасывает только результаты поиска и текущую позицию """
        self.best_score = -np.inf
        self.best_pos = (-1, -1)
        self.current_pos = (0, 0) # Сброс в начало координат
        self.current_score = self.get_score_at(0, 0) if self.template_pixels is not None else 0

    def reset_template_and_results(self):
        """ Сбрасывает данные шаблона и результаты """
        self.template_pixels = None
        self.template_rows = 0
        self.template_cols = 0
        self.reset_results()