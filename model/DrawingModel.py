# model/DrawingModel.py
import xml.etree.ElementTree as ET
import numpy as np # Понадобится для проверки пиксельного поля

class DrawingModel:
    """
    Модель данных для редактора шаблонов.
    Хранит информацию о размере поля, вершинах и состоянии пиксельного поля.
    Отвечает за логику добавления вершин, отрисовки линий и сохранения/загрузки.
    """
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.vertices = []
        self.pixel_field = [[0 for _ in range(self.cols)] for _ in range(self.rows)]

    # ... (методы add_vertex, update_field, _draw_line, clear, resize, get_vertices_string без изменений) ...
    def add_vertex(self, x, y):
        """
        Добавляет новую вершину, если координаты корректны и такой вершины еще нет.
        Возвращает True, если вершина добавлена, иначе False.
        """
        if 0 <= x < self.cols and 0 <= y < self.rows and (x, y) not in self.vertices:
            self.vertices.append((x, y))
            self.update_field() # Перерисовываем поле после добавления
            return True
        return False

    def update_field(self):
        """
        Пересчитывает и обновляет `pixel_field` на основе текущего списка вершин.
        Сначала очищает поле, затем ставит точки вершин и рисует линии между ними.
        """
        # Сброс поля
        self.pixel_field = [[0 for _ in range(self.cols)] for _ in range(self.rows)]

        # Отмечаем вершины
        for vx, vy in self.vertices:
            # Доп. проверка на случай изменения размера перед отрисовкой
            if 0 <= vy < self.rows and 0 <= vx < self.cols:
                 self.pixel_field[vy][vx] = 1

        # Рисуем линии между последовательными вершинами
        if len(self.vertices) >= 2:
            for i in range(len(self.vertices) - 1):
                self._draw_line(self.vertices[i], self.vertices[i + 1])
            # Замыкаем полигон, если вершин 3 или больше
            if len(self.vertices) >= 3:
                self._draw_line(self.vertices[-1], self.vertices[0])

    def _draw_line(self, p1, p2):
        """
        Рисует линию между точками p1 и p2 на `pixel_field`, используя алгоритм Брезенхэма.
        (Сделал приватным, т.к. вызывается только из update_field)
        """
        x1, y1 = p1
        x2, y2 = p2
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        # Проверяем начальные и конечные точки на выход за границы перед циклом
        # (можно добавить более сложную логику отсечения линии)
        # if not (0 <= y1 < self.rows and 0 <= x1 < self.cols and \
        #         0 <= y2 < self.rows and 0 <= x2 < self.cols):
        #      pass # Пока просто пропускаем, если точки вне поля

        x_curr, y_curr = x1, y1 # Используем временные переменные для итерации

        while True:
            # Закрашиваем пиксель, если он в пределах поля
            if 0 <= y_curr < self.rows and 0 <= x_curr < self.cols:
                self.pixel_field[y_curr][x_curr] = 1

            # Условие выхода: достигли конечной точки
            if x_curr == x2 and y_curr == y2:
                break

            e2 = 2 * err
            # Движение по X
            if e2 > -dy:
                err -= dy
                x_curr += sx
            # Движение по Y
            if e2 < dx:
                err += dx
                y_curr += sy

    def clear(self):
        """
        Очищает список вершин и пиксельное поле.
        """
        self.vertices = []
        self.pixel_field = [[0 for _ in range(self.cols)] for _ in range(self.rows)]

    def resize(self, new_rows, new_cols):
        """
        Изменяет размер поля, сбрасывая вершины и пиксельное поле.
        """
        if new_rows > 0 and new_cols > 0:
            self.rows = new_rows
            self.cols = new_cols
            self.clear() # Используем clear для сброса
            return True
        return False

    def get_vertices_string(self):
        """
        Возвращает строковое представление списка вершин для отображения.
        """
        if not self.vertices:
            return "(пусто)"
        return " -> ".join(f"({x},{y})" for x, y in self.vertices)


    def save_to_xml(self, filename):
        """
        Сохраняет текущее состояние (размер, ВЕРШИНЫ) в XML-файл ШАБЛОНА (<template>).
        """
        root = ET.Element("template")
        size = ET.SubElement(root, "size")
        size.set("rows", str(self.rows))
        size.set("cols", str(self.cols))
        vertices_element = ET.SubElement(root, "vertices")
        for x, y in self.vertices:
            vertex = ET.SubElement(vertices_element, "vertex")
            vertex.set("x", str(x))
            vertex.set("y", str(y))
        tree = ET.ElementTree(root)
        try:
            ET.indent(tree, space="\t", level=0)
            tree.write(filename, encoding="utf-8", xml_declaration=True)
        except Exception as e:
            raise Exception(f"Ошибка при записи XML файла шаблона '{filename}': {str(e)}")

    # --- ДОБАВЛЕНО: Метод сохранения как изображение ---
    def save_as_image_xml(self, filename):
        """
        Сохраняет текущее состояние (размер, ПИКСЕЛИ) в XML-файл ИЗОБРАЖЕНИЯ (<image>).
        """
        # Убедимся, что pixel_field актуален (хотя он должен обновляться при добавлении вершин)
        # self.update_field() # Можно раскомментировать для гарантии, но может быть избыточно

        if not self.pixel_field or self.rows <= 0 or self.cols <= 0:
            raise ValueError("Нет данных для сохранения (поле пустое или имеет нулевые размеры).")

        root = ET.Element("image")
        # Сохраняем размер
        size = ET.SubElement(root, "size")
        size.set("rows", str(self.rows))
        size.set("cols", str(self.cols))
        # Сохраняем пиксели
        pixels_element = ET.SubElement(root, "pixels")
        for r in range(self.rows):
            row_element = ET.SubElement(pixels_element, "row")
            # Преобразуем строку пикселей (список int) в строку символов '0' и '1'
            row_element.text = "".join(map(str, self.pixel_field[r]))

        # Записываем дерево в файл
        tree = ET.ElementTree(root)
        try:
            ET.indent(tree, space="\t", level=0)
            tree.write(filename, encoding="utf-8", xml_declaration=True)
        except Exception as e:
            raise Exception(f"Ошибка при записи XML файла изображения '{filename}': {str(e)}")
    # --- Конец добавления ---

    def load_from_xml(self, filename):
        """
        Загружает состояние (размер, вершины) из XML-файла ШАБЛОНА (<template>).
        Обновляет модель и вызывает update_field().
        """
        try:
            tree = ET.parse(filename)
            root = tree.getroot()
            # --- ПРОВЕРКА: Убеждаемся, что загружаем именно шаблон ---
            if root.tag != 'template':
                 raise ValueError("Неверный формат файла: ожидался шаблон (<template>), получен '<{}>'".format(root.tag))
            # --- Конец проверки ---

            size = root.find("size")
            if size is None: raise ValueError("Тег 'size' не найден в XML")
            new_rows = int(size.get("rows"))
            new_cols = int(size.get("cols"))

            if not self.resize(new_rows, new_cols):
                 raise ValueError("Некорректные размеры поля в XML (должны быть > 0)")

            loaded_vertices = []
            vertices_element = root.find("vertices")
            if vertices_element is not None:
                for vertex in vertices_element.findall("vertex"):
                    x = int(vertex.get("x"))
                    y = int(vertex.get("y"))
                    if 0 <= x < self.cols and 0 <= y < self.rows:
                         if (x, y) not in loaded_vertices:
                             loaded_vertices.append((x, y))
                    else:
                        print(f"Предупреждение: Вершина ({x},{y}) вне границ поля ({self.rows}x{self.cols}), пропущена.")

            self.vertices = loaded_vertices
            self.update_field()

        except ET.ParseError as e:
             raise Exception(f"Ошибка парсинга XML файла '{filename}': {str(e)}")
        except FileNotFoundError:
             raise Exception(f"Файл '{filename}' не найден.")
        except (ValueError, TypeError, AttributeError) as e:
             raise Exception(f"Ошибка в структуре или данных файла '{filename}': {str(e)}")
        except Exception as e:
            raise Exception(f"Неизвестная ошибка при загрузке файла '{filename}': {str(e)}")