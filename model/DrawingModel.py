# model/DrawingModel.py
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image, ImageTk

# Добавим небольшой отступ при расчете размера сетки по точкам
GRID_MARGIN = 5

class DrawingModel:
    """
    Модель данных для редактора шаблонов.
    ИЗМЕНЕНО: Загрузка/сохранение только в формате <polygon>.
             load_from_xml определяет размер сетки по точкам.
    """
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.vertices = [] # Список кортежей (int, int)
        self.pixel_field = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        self.undo_stack = []
        self.redo_stack = []
        self.overlay_image_pil = None
        self.overlay_offset_x = 0
        self.overlay_offset_y = 0
        self.overlay_scale = 1.0

    # --- Методы добавления/отмены вершин (без изменений) ---
    def add_vertex(self, x, y):
        try: x_int = int(round(x)); y_int = int(round(y))
        except (ValueError, TypeError): return False
        if 0 <= x_int < self.cols and 0 <= y_int < self.rows and (x_int, y_int) not in self.vertices:
            new_vertex = (x_int, y_int)
            self.vertices.append(new_vertex); self.update_field()
            self.undo_stack.append(new_vertex); self.redo_stack.clear()
            return True
        return False

    def undo_vertex(self):
        if not self.undo_stack: return False
        last_vertex = self.undo_stack.pop(); self.redo_stack.append(last_vertex)
        if last_vertex in self.vertices: self.vertices.remove(last_vertex)
        else: self.redo_stack.pop(); self.undo_stack.append(last_vertex); return False
        self.update_field(); return True

    def redo_vertex(self):
        if not self.redo_stack: return False
        vertex_to_redo = self.redo_stack.pop(); self.undo_stack.append(vertex_to_redo)
        if vertex_to_redo not in self.vertices: self.vertices.append(vertex_to_redo)
        else: self.undo_stack.pop(); self.redo_stack.append(vertex_to_redo); return False
        self.update_field(); return True

    # --- Методы обновления поля и рисования (без изменений) ---
    def update_field(self):
        self.pixel_field = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        for vertex in self.vertices:
            try:
                vx = int(vertex[0]); vy = int(vertex[1])
                if 0 <= vy < self.rows and 0 <= vx < self.cols: self.pixel_field[vy][vx] = 1
            except (TypeError, IndexError, ValueError) as e: print(f"Ошибка в update_field: {e}"); continue
        if len(self.vertices) >= 2:
            for i in range(len(self.vertices) - 1): self._draw_line(self.vertices[i], self.vertices[i + 1])
            if len(self.vertices) >= 3: self._draw_line(self.vertices[-1], self.vertices[0])

    def _draw_line(self, p1, p2):
        try: x1, y1 = int(p1[0]), int(p1[1]); x2, y2 = int(p2[0]), int(p2[1])
        except (TypeError, IndexError, ValueError) as e: print(f"Ошибка в _draw_line: {e}"); return
        dx = abs(x2 - x1); dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1; sy = 1 if y1 < y2 else -1
        err = dx - dy; x_curr, y_curr = x1, y1
        while True:
            if 0 <= y_curr < self.rows and 0 <= x_curr < self.cols:
                try: self.pixel_field[y_curr][x_curr] = 1
                except IndexError: print(f"Ошибка индекса в _draw_line"); break
            if x_curr == x2 and y_curr == y2: break
            e2 = 2 * err
            if e2 > -dy: err -= dy; x_curr += sx
            if e2 < dx: err += dx; y_curr += sy

    # --- Методы управления состоянием (без изменений) ---
    def clear(self):
        self.vertices = []; self.pixel_field = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        self.undo_stack.clear(); self.redo_stack.clear()

    def resize(self, new_rows, new_cols):
        if new_rows > 0 and new_cols > 0:
            self.rows = new_rows; self.cols = new_cols
            self.clear(); return True # Clear очистит вершины и историю
        return False

    def get_vertices_string(self):
        if not self.vertices: return "(пусто)"
        return " -> ".join(f"({int(v[0])},{int(v[1])})" for v in self.vertices)

    # --- ИЗМЕНЕННЫЕ МЕТОДЫ СОХРАНЕНИЯ/ЗАГРУЗКИ XML ---

    def save_to_xml(self, filename):
        """
        Сохраняет текущее состояние (размер сетки, ВЕРШИНЫ) в XML-файл
        в формате <polygon> с <point X="..." Y="..."/>.
        """
        root = ET.Element("polygon")
        root.set("grid_rows", str(self.rows)) # Сохраняем размер сетки
        root.set("grid_cols", str(self.cols))
        for x, y in self.vertices:
            point = ET.SubElement(root, "point")
            point.set("X", str(int(x)))
            point.set("Y", str(int(y)))
        tree = ET.ElementTree(root)
        try:
            ET.indent(tree, space="\t", level=0)
            tree.write(filename, encoding="utf-8", xml_declaration=True)
        except Exception as e:
            raise Exception(f"Ошибка при записи XML файла '{filename}': {str(e)}")

    def load_from_xml(self, filename):
        """
        Загружает вершины из XML-файла формата <polygon>.
        Определяет размер сетки по максимальным координатам вершин.
        Обновляет модель и сбрасывает историю.
        """
        try:
            tree = ET.parse(filename)
            root = tree.getroot()

            if root.tag != 'polygon':
                 raise ValueError(f"Неверный формат файла: ожидался <polygon>, получен '<{root.tag}>'")

            # 1. Сначала читаем ВСЕ точки в временный список
            temp_vertices = []
            max_x = -1
            max_y = -1
            for point in root.findall("point"):
                x_str = point.get("X"); y_str = point.get("Y")
                if x_str is None or y_str is None: continue
                try:
                    x = int(x_str); y = int(y_str)
                    if x < 0 or y < 0: # Координаты не могут быть отрицательными
                        print(f"Предупреждение: Пропущен <point> с отрицательными координатами ({x},{y}).")
                        continue
                    temp_vertices.append((x, y))
                    # Обновляем максимальные координаты
                    if x > max_x: max_x = x
                    if y > max_y: max_y = y
                except ValueError:
                    print(f"Предупреждение: Пропущен <point> с нечисловыми координатами X='{x_str}', Y='{y_str}'.")
                    continue

            if not temp_vertices:
                raise ValueError("В файле не найдено корректных вершин <point>.")

            # 2. Определяем необходимый размер сетки по максимальным координатам + отступ
            # Нумерация с 0, поэтому размер = max_coord + 1 + margin
            required_rows = max_y + 1 + GRID_MARGIN
            required_cols = max_x + 1 + GRID_MARGIN

            # 3. Изменяем размер сетки (это очистит self.vertices и историю)
            if not self.resize(required_rows, required_cols):
                 raise ValueError(f"Не удалось установить расчетный размер сетки ({required_rows}x{required_cols})")

            # 4. Теперь добавляем вершины из временного списка в основной
            # Проверка границ не нужна, т.к. мы установили достаточный размер
            # Проверка дубликатов остается
            final_vertices = []
            for x, y in temp_vertices:
                if (x, y) not in final_vertices:
                    final_vertices.append((x, y))
            self.vertices = final_vertices

            # 5. Обновляем pixel_field
            self.update_field()

        except ET.ParseError as e: raise Exception(f"Ошибка парсинга XML '{filename}': {str(e)}")
        except FileNotFoundError: raise Exception(f"Файл '{filename}' не найден.")
        except (ValueError, TypeError, AttributeError, KeyError) as e: raise Exception(f"Ошибка в структуре/данных '{filename}': {str(e)}")
        except Exception as e: raise Exception(f"Неизвестная ошибка при загрузке '{filename}': {str(e)}")


    # --- Методы для оверлея (без изменений) ---
    def load_overlay_image(self, filename):
        try:
            self.overlay_image_pil = Image.open(filename)
            self.overlay_offset_x = 0; self.overlay_offset_y = 0; self.overlay_scale = 1.0
            return True
        except FileNotFoundError: raise Exception(f"Файл изображения '{filename}' не найден.")
        except Exception as e: self.overlay_image_pil = None; raise Exception(f"Не удалось загрузить изображение '{filename}': {str(e)}")

    def move_overlay(self, dx, dy):
        if self.overlay_image_pil: self.overlay_offset_x += dx; self.overlay_offset_y += dy; return True
        return False

    def scale_overlay(self, factor):
        if self.overlay_image_pil:
            new_scale = self.overlay_scale * factor
            if new_scale < 0.01: new_scale = 0.01
            self.overlay_scale = new_scale; return True
        return False

    def get_overlay_data(self):
        return self.overlay_image_pil, self.overlay_offset_x, self.overlay_offset_y, self.overlay_scale