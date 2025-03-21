import tkinter as tk
from tkinter import messagebox
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

# Для лучшего вывода на экран
def print_matrix(matrix):
    for row in matrix:
        print(' '.join(['#' if cell == 1 else '.' for cell in row]))

# Формула полной свертки
def convolution(image, mask):
    index_of_max_convolution = []
    max_convolution = 0

    for i in range(len(image) - len(mask) + 1):
        for j in range(len(image[0]) - len(mask[0]) + 1):
            image_submatrix = matrix_copy(image, mask, i, j)
            convolution = matrix_convolution(image_submatrix, mask)
            if (convolution > max_convolution):
                max_convolution = convolution
                index_of_max_convolution = [i, j]

    print('Максимальный результат свертки:', max_convolution)
    print('Индекс:', index_of_max_convolution)

def matrix_convolution(matrix1, matrix2):
    result = 0
    for i in range(len(matrix1)):
        for j in range(len(matrix1[0])):
            result += matrix1[i][j] * matrix2[i][j]
    return result

def matrix_copy(matrix1, matrix2, i, j):
    rows = len(matrix2)
    cols = len(matrix2[0]) if rows > 0 else 0
    result = [[0 for _ in range(cols)] for _ in range(rows)]
    for row in range(rows):
        for col in range(cols):
            if i + row < len(matrix1) and j + col < len(matrix1[0]):
                result[row][col] = matrix1[i + row][j + col]
            else:
                result[row][col] = 0
    return result

# Алгоритм "построения" ядра свёртки из полигональной фигуры
def from_polygon_to_mask(polygon):
    # Находим минимальные и максимальные координаты
    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    min_x = min(xs)
    max_x = max(xs)
    min_y = min(ys)
    max_y = max(ys)

    # Определяем размер матрицы
    rows = max_y - min_y + 1
    columns = max_x - min_x + 1
    mask = [[0 for _ in range(columns)] for _ in range(rows)]

    # Вспомогательная функция для рисования линии (алгоритм Брезенхэма)
    def draw_line(mask, x0, y0, x1, y1):
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            if 0 <= y0 < len(mask) and 0 <= x0 < len(mask[0]):
                mask[y0][x0] = 1
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    # Проходим по всем рёбрам полигона
    n = len(polygon)
    for i in range(n):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % n]
        x1_idx = x1 - min_x
        y1_idx = y1 - min_y
        x2_idx = x2 - min_x
        y2_idx = y2 - min_y
        draw_line(mask, x1_idx, y1_idx, x2_idx, y2_idx)

    return mask, min_x, min_y

class PolygonApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Построение полигона")

        # Список для хранения полей ввода координат
        self.points_entries = []

        # Создаём фрейм для полей ввода
        self.input_frame = tk.Frame(self.root)
        self.input_frame.pack(pady=10)

        # Первая точка (x, y)
        self.add_point_fields()

        # Кнопка для добавления новой точки
        self.add_button = tk.Button(self.root, text="+", command=self.add_point_fields)
        self.add_button.pack(pady=5)

        # Кнопка для построения фигуры
        self.build_button = tk.Button(self.root, text="Построить фигуру", command=self.build_polygon)
        self.build_button.pack(pady=5)

    def add_point_fields(self):
        point_frame = tk.Frame(self.input_frame)
        point_frame.pack(fill=tk.X, pady=2)

        tk.Label(point_frame, text="x:").pack(side=tk.LEFT)
        x_entry = tk.Entry(point_frame, width=10)
        x_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(point_frame, text="y:").pack(side=tk.LEFT)
        y_entry = tk.Entry(point_frame, width=10)
        y_entry.pack(side=tk.LEFT, padx=5)

        self.points_entries.append((x_entry, y_entry))

    def build_polygon(self):
        points = []
        for x_entry, y_entry in self.points_entries:
            try:
                x = int(x_entry.get())
                y = int(y_entry.get())
                points.append([x, y])
            except ValueError:
                messagebox.showerror("Ошибка", "Пожалуйста, введите целые числовые значения для координат!")
                return

        if len(points) < 3:
            messagebox.showerror("Ошибка", "Для построения полигона нужно минимум 3 точки!")
            return

        # Создаём матрицу с помощью from_polygon_to_mask
        mask, min_x, min_y = from_polygon_to_mask(points)

        # Создаём пользовательскую цветовую палитру: 0 — серый, 1 — синий
        colors = ['gray', 'blue']
        cmap = ListedColormap(colors)

        # Создаём график
        plt.figure(figsize=(6, 6))
        plt.imshow(mask, cmap=cmap, origin='lower')
        plt.grid(True)
        plt.xlabel('X')
        plt.ylabel('Y')
        plt.title('Построенный полигон')

        # Инвертируем ось Y, чтобы она была направлена вниз
        plt.gca().invert_yaxis()

        plt.show()

# Запуск приложения
if __name__ == "__main__":
    root = tk.Tk()
    app = PolygonApp(root)
    root.mainloop()