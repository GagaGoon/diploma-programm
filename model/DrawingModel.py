# model/DrawingModel.py
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image, ImageTk

GRID_MARGIN = 5 # Отступ при авто-определении размера сетки из XML

class DrawingModel:
    """
    Модель данных для редактора шаблонов.
    Хранит информацию о размере поля, вершинах, состоянии пиксельного поля,
    физической высоте шаблона, истории для Undo/Redo и данных для оверлея.
    Загрузка/сохранение только в формате <polygon>.
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
        self.template_physical_height_meters = 0.0 # Физическая высота шаблона в метрах

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

    def clear(self):
        self.vertices = []; self.pixel_field = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        self.undo_stack.clear(); self.redo_stack.clear()
        # Физическую высоту НЕ сбрасываем при простой очистке поля,
        # она должна сбрасываться/устанавливаться при загрузке нового шаблона или изменении размера.
        # При изменении размера ее сбрасывать не надо, если пользователь явно ее не меняет.

    def resize(self, new_rows, new_cols):
        if new_rows > 0 and new_cols > 0:
            self.rows = new_rows; self.cols = new_cols
            # Важно: очищаем вершины и историю, т.к. старые вершины могут быть вне новых границ.
            # Физическую высоту шаблона не трогаем, она не зависит от размера сетки.
            self.vertices = []
            self.pixel_field = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
            self.undo_stack.clear()
            self.redo_stack.clear()
            return True
        return False

    def get_vertices_string(self):
        if not self.vertices: return "(пусто)"
        return " -> ".join(f"({int(v[0])},{int(v[1])})" for v in self.vertices)

    def save_to_xml(self, filename):
        root = ET.Element("polygon")
        root.set("grid_rows", str(self.rows))
        root.set("grid_cols", str(self.cols))
        root.set("physical_height_m", f"{self.template_physical_height_meters:.3f}") # Сохраняем с 3 знаками

        for x, y in self.vertices:
            point = ET.SubElement(root, "point")
            point.set("X", str(int(x)))
            point.set("Y", str(int(y)))
        tree = ET.ElementTree(root)
        try:
            ET.indent(tree, space="\t", level=0)
            tree.write(filename, encoding="utf-8", xml_declaration=True)
        except Exception as e:
            raise Exception(f"Ошибка при записи XML '{filename}': {str(e)}")

    def load_from_xml(self, filename):
        try:
            tree = ET.parse(filename); root = tree.getroot()
            if root.tag != 'polygon': raise ValueError(f"Ожидался <polygon>, получен '<{root.tag}>'")

            # Загрузка физической высоты шаблона
            height_str = root.get("physical_height_m")
            if height_str is not None:
                try: self.template_physical_height_meters = float(height_str)
                except ValueError: self.template_physical_height_meters = 0.0; print(f"Предупреждение: некорректный physical_height_m ('{height_str}')")
            else: self.template_physical_height_meters = 0.0; print(f"Предупреждение: physical_height_m не найден")

            # Чтение вершин и определение размеров сетки
            temp_vertices = []; max_x = -1; max_y = -1
            for point in root.findall("point"):
                x_str = point.get("X"); y_str = point.get("Y")
                if x_str is None or y_str is None: continue
                try:
                    x = int(x_str); y = int(y_str)
                    if x < 0 or y < 0: continue
                    temp_vertices.append((x, y))
                    if x > max_x: max_x = x
                    if y > max_y: max_y = y
                except ValueError: continue

            if not temp_vertices: raise ValueError("В файле не найдено корректных вершин <point>.")

            # Определение размера сетки по точкам + отступ
            # Либо используем grid_rows/grid_cols из файла, если они есть (предпочтительнее)
            g_rows_str = root.get("grid_rows")
            g_cols_str = root.get("grid_cols")
            resized_by_grid_attr = False
            if g_rows_str and g_cols_str:
                try:
                    new_r, new_c = int(g_rows_str), int(g_cols_str)
                    if new_r > 0 and new_c > 0:
                        if not self.resize(new_r, new_c): raise ValueError("Не удалось изменить размер по grid_rows/cols")
                        resized_by_grid_attr = True
                except ValueError:
                    print("Предупреждение: некорректные grid_rows/cols, размер будет определен по точкам.")

            if not resized_by_grid_attr: # Если grid_rows/cols не было или они некорректны
                required_rows = max_y + 1 + GRID_MARGIN
                required_cols = max_x + 1 + GRID_MARGIN
                if not self.resize(required_rows, required_cols):
                     raise ValueError(f"Не удалось установить расчетный размер сетки ({required_rows}x{required_cols})")

            # Добавляем вершины, проверяя их на попадание в текущие (возможно, новые) границы сетки
            final_vertices = []
            for x, y in temp_vertices:
                if 0 <= x < self.cols and 0 <= y < self.rows: # Проверка на текущие self.cols, self.rows
                    if (x, y) not in final_vertices:
                        final_vertices.append((x, y))
                else:
                    print(f"Предупреждение: Вершина ({x},{y}) вне установленных границ сетки ({self.rows}x{self.cols}), пропущена.")

            self.vertices = final_vertices
            self.undo_stack.clear() # Очищаем историю после загрузки
            self.redo_stack.clear()
            self.update_field()

        except ET.ParseError as e: raise Exception(f"Ошибка парсинга XML '{filename}': {str(e)}")
        except FileNotFoundError: raise Exception(f"Файл '{filename}' не найден.")
        except (ValueError, TypeError, AttributeError, KeyError) as e: raise Exception(f"Ошибка в структуре/данных '{filename}': {str(e)}")
        except Exception as e: raise Exception(f"Неизвестная ошибка при загрузке '{filename}': {str(e)}")

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