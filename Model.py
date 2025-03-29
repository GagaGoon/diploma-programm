import xml.etree.ElementTree as ET

class Model:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.vertices = []
        self.pixel_field = [[0 for _ in range(cols)] for _ in range(rows)]

    def add_vertex(self, x, y):
        if 0 <= x < self.cols and 0 <= y < self.rows and self.pixel_field[y][x] == 0:
            self.vertices.append((x, y))
            self.update_field()

    def update_field(self):
        self.pixel_field = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        for vx, vy in self.vertices:
            self.pixel_field[vy][vx] = 1
        if len(self.vertices) >= 2:
            for i in range(len(self.vertices) - 1):
                self.draw_line(self.vertices[i], self.vertices[i + 1])
            if len(self.vertices) >= 3:
                self.draw_line(self.vertices[-1], self.vertices[0])

    def draw_line(self, p1, p2):
        x1, y1 = p1
        x2, y2 = p2
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        while True:
            if 0 <= y1 < self.rows and 0 <= x1 < self.cols:
                self.pixel_field[y1][x1] = 1
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy

    def clear(self):
        self.vertices = []
        self.pixel_field = [[0 for _ in range(self.cols)] for _ in range(self.rows)]

    def resize(self, new_rows, new_cols):
        self.rows = new_rows
        self.cols = new_cols
        self.vertices = []
        self.pixel_field = [[0 for _ in range(new_cols)] for _ in range(new_rows)]

    def get_vertices_string(self):
        return "    ".join(f"x: {x}, y: {y}" for x, y in self.vertices)

    def save_to_xml(self, filename="template.xml"):
        root = ET.Element("template")
        size = ET.SubElement(root, "size")
        size.set("rows", str(self.rows))
        size.set("cols", str(self.cols))
        vertices = ET.SubElement(root, "vertices")
        for x, y in self.vertices:
            vertex = ET.SubElement(vertices, "vertex")
            vertex.set("x", str(x))
            vertex.set("y", str(y))
        tree = ET.ElementTree(root)
        tree.write(filename, encoding="utf-8", xml_declaration=True)

    def load_from_xml(self, filename):
        try:
            tree = ET.parse(filename)
            root = tree.getroot()
            # Загружаем размер поля
            size = root.find("size")
            new_rows = int(size.get("rows"))
            new_cols = int(size.get("cols"))
            self.resize(new_rows, new_cols)
            # Загружаем вершины
            self.vertices = []
            vertices = root.find("vertices")
            for vertex in vertices.findall("vertex"):
                x = int(vertex.get("x"))
                y = int(vertex.get("y"))
                self.vertices.append((x, y))
            self.update_field()
        except Exception as e:
            raise Exception(f"Ошибка при загрузке файла: {str(e)}")