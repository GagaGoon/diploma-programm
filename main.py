import math

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
    # Получаем размеры второй матрицы
    rows = len(matrix2)
    cols = len(matrix2[0]) if rows > 0 else 0

    # Создаем пустую матрицу для результата
    result = [[0 for _ in range(cols)] for _ in range(rows)]

    # Копируем элементы из matrix1 в result
    for row in range(rows):
        for col in range(cols):
            # Проверяем, чтобы не выйти за границы matrix1
            if i + row < len(matrix1) and j + col < len(matrix1[0]):
                result[row][col] = matrix1[i + row][j + col]
            else:
                # Если выходим за границы, заполняем нулями
                result[row][col] = 0
    return result


# алгоритм "построения" ядра свертки из полигональной фигуры
def from_polygon_to_mask(polygon):
    # Находим минимальные и максимальные координаты
    xs = [p[0] for p in polygon]  # Все x-координаты
    ys = [p[1] for p in polygon]  # Все y-координаты
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
            # Устанавливаем пиксель в 1
            if 0 <= y0 < len(mask) and 0 <= x0 < len(mask[0]):
                mask[y0][x0] = 1
            # Если достигли конечной точки, выходим
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
        x2, y2 = polygon[(i + 1) % n]  # Следующая вершина (для последней соединяем с первой)
        # Приводим координаты к индексам матрицы
        x1_idx = x1 - min_x
        y1_idx = y1 - min_y
        x2_idx = x2 - min_x
        y2_idx = y2 - min_y
        draw_line(mask, x1_idx, y1_idx, x2_idx, y2_idx)

    return mask


image = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
         [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
         [0, 1, 1, 1, 1, 1, 0, 0, 0, 0],
         [0, 1, 0, 0, 0, 1, 0, 0, 0, 0],
         [0, 1, 0, 0, 0, 1, 0, 0, 0, 0],
         [0, 1, 1, 1, 1, 1, 0, 0, 0, 0],
         [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
         [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]]

square = [[1, 1, 1, 1, 1],
          [1, 0, 0, 0, 1],
          [1, 0, 0, 0, 1],
          [1, 1, 1, 1, 1]]

polygon1 = [[0,0], [24,0], [12,24]]
polygon2 = [[5,5], [5,19], [19,19], [19,5]]

center = (12, 12)
radius = 10
polygon3 = []
for i in range(16):
    angle = 2 * math.pi * i / 16
    x = int(center[0] + radius * math.cos(angle))
    y = int(center[1] + radius * math.sin(angle))
    polygon3.append([x, y])

center = (12, 12)
outer_radius = 10
inner_radius = 5
polygon4 = []
for i in range(10):
    radius = outer_radius if i % 2 == 0 else inner_radius
    angle = 2 * math.pi * i / 5
    x = int(center[0] + radius * math.cos(angle))
    y = int(center[1] + radius * math.sin(angle))
    polygon4.append([x, y])

polygon5 = [[12,0], [12,24], [12,12], [0,12], [24,12], [12,12]]

matrix = from_polygon_to_mask(polygon1)
print_matrix(matrix)
print()
matrix = from_polygon_to_mask(polygon2)
print_matrix(matrix)
print()
matrix = from_polygon_to_mask(polygon3)
print_matrix(matrix)
print()
matrix = from_polygon_to_mask(polygon4)
print_matrix(matrix)
print()
matrix = from_polygon_to_mask(polygon5)
print_matrix(matrix)