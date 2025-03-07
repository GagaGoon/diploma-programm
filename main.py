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

index_of_max_convolution = []
max_convolution = 0

for i in range(len(image) - len(square) + 1):
    for j in range(len(image[0]) - len(square[0]) + 1):
        image_submatrix = matrix_copy(image, square, i, j)
        convolution = matrix_convolution(image_submatrix, square)
        if (convolution > max_convolution):
            max_convolution = convolution
            index_of_max_convolution = [i, j]

print('Максимальный результат свертки:', max_convolution)
print('Индекс:', index_of_max_convolution)
