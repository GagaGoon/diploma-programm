# controller/main.py
import tkinter as tk
from tkinter import ttk
import sys
import os

# Добавляем корневую директорию проекта в sys.path, чтобы работали импорты
# Это один из способов решения проблемы импортов при такой структуре
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Теперь можно использовать абсолютные импорты от корня проекта
from controller.DrawingController import DrawingController
from controller.ComparisonController import ComparisonController

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Редактор шаблонов и Сравнение")
    # Установим минимальный размер окна, чтобы панели влезали
    root.minsize(width=650, height=500)

    # Стиль для вкладок (опционально)
    style = ttk.Style()
    style.configure('TNotebook.Tab', padding=[10, 5], font=('Helvetica', 10))

    notebook = ttk.Notebook(root, style='TNotebook')

    # --- Вкладка 1: Редактор шаблонов ---
    # Создаем фрейм-контейнер для вкладки
    editor_frame = tk.Frame(notebook)
    editor_frame.pack(fill='both', expand=True) # Заполняем пространство вкладки
    # Добавляем фрейм как вкладку
    notebook.add(editor_frame, text=" Построение шаблона ") # Пробелы для отступов
    # Создаем MVC для редактора, передавая фрейм вкладки
    # Контроллер сам создаст View внутри этого фрейма
    editor_app = DrawingController(editor_frame)

    # --- Вкладка 2: Сравнение с шаблоном ---
    # Создаем фрейм-контейнер для вкладки
    comparison_frame = tk.Frame(notebook)
    comparison_frame.pack(fill='both', expand=True)
    # Добавляем фрейм как вкладку
    notebook.add(comparison_frame, text=" Сравнение с шаблоном ")
    # Создаем MVC для сравнения, передавая фрейм вкладки
    comparison_app = ComparisonController(comparison_frame)

    notebook.pack(expand=True, fill="both", padx=5, pady=5)

    # Запускаем главный цикл Tkinter
    root.mainloop()

# Надо добавить скрол в редакторе, добавить отмену последней точки, добавить наложение изображения поверх поля