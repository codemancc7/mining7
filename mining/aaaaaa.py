import cv2
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk

class TruckAnimator:
    def __init__(self, root, image_path, png_paths, new_sizes):
        self.root = root
        self.image_path = image_path
        self.png_paths = png_paths
        self.new_sizes = new_sizes

        # Crear el marco de menú más grande
        self.menu_frame = tk.Frame(root, width=200, bg='gray', padx=10, pady=10)
        self.menu_frame.pack(side=tk.LEFT, fill=tk.Y, expand=False)

        # Crear el marco de canvas
        self.canvas_frame = tk.Frame(root)
        self.canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Crear el marco de la tabla y colocar más arriba
        self.table_frame = tk.Frame(root)
        self.table_frame.pack(side=tk.TOP, fill=tk.X)

        # Cargar imagen de fondo
        self.background_image = Image.open(image_path)
        self.tk_background_image = ImageTk.PhotoImage(self.background_image)
        self.canvas = tk.Canvas(self.canvas_frame, width=self.background_image.width, height=self.background_image.height)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_background_image)

        # Cargar y redimensionar imágenes PNG
        self.images = {color: self.load_resized_image(path, size)
                       for color, (path, size) in zip(png_paths.keys(), zip(png_paths.values(), new_sizes.values()))}
        self.image_ids = {color: self.canvas.create_image(0, 0, anchor=tk.NW, image=image) 
                          for color, image in self.images.items()}

        # Leer coordenadas
        self.coordinates = {}
        for color in ['rojo', 'verde', 'amarillo']:
            try:
                with open(f'coordenadas_{color}.txt', 'r') as f:
                    self.coordinates[color] = [tuple(map(int, line.strip().split(','))) for line in f]
            except FileNotFoundError:
                print(f"Archivo de coordenadas para {color} no encontrado.")

        self.indices = {color: 0 for color in ['rojo', 'verde', 'amarillo']}
        self.speed = 120
        self.animating = False

        # Crear menú
        self.create_menu()
        
        # Crear tabla
        self.create_table()

    def load_resized_image(self, path, size):
        try:
            image = Image.open(path).resize(size)
            return ImageTk.PhotoImage(image)
        except IOError:
            print(f"Error al cargar la imagen {path}")
            return None

    def validate_coordinates(self, coords):
        width, height = self.background_image.width, self.background_image.height
        return [(x, y) for x, y in coords if 0 <= x <= width and 0 <= y <= height]

    def start_animation(self):
        self.animating = True
        self.animate()

    def stop_animation(self):
        self.animating = False

    def reset_animation(self):
        self.stop_animation()
        self.indices = {color: 0 for color in ['rojo', 'verde', 'amarillo']}
        for color in ['rojo', 'verde', 'amarillo']:
            if self.coordinates[color]:
                self.canvas.coords(self.image_ids[color], *self.coordinates[color][0])

    def move_along_path(self, image_id, coords, index):
        if coords:
            x, y = coords[index]
            self.canvas.coords(image_id, x, y)
            index = (index + 1) % len(coords)
        return index

    def animate(self):
        if self.animating:
            for color in self.indices:
                self.indices[color] = self.move_along_path(self.image_ids[color], self.coordinates[color], self.indices[color])
            self.root.after(self.speed, self.animate)

    def create_menu(self):
        # Botones más grandes
        button_config = {
            'padx': 8,
            'pady': 3,
            'font': ('Helvetica', 12),
            'width': 8
        }
        
        start_button = tk.Button(self.menu_frame, text="Start", command=self.start_animation, **button_config)
        start_button.pack(pady=10, padx=10, fill=tk.X)

        stop_button = tk.Button(self.menu_frame, text="Stop", command=self.stop_animation, **button_config)
        stop_button.pack(pady=10, padx=10, fill=tk.X)

        reset_button = tk.Button(self.menu_frame, text="Reset", command=self.reset_animation, **button_config)
        reset_button.pack(pady=10, padx=10, fill=tk.X)

    def create_table(self):
        # Encabezados de la tabla
        headers = ['Imagen', 'Datos']
        for col, header in enumerate(headers):
            header_label = tk.Label(self.table_frame, text=header, bg='lightgray', padx=10, pady=5)
            header_label.grid(row=0, column=col, sticky='nsew')

        # Contenido de la tabla
        labels = ['Cat 797', 'AD30', 'Toyota 4x4']
        for i, (color, image) in enumerate(self.images.items()):
            # Ajustar tamaño de las imágenes en la tabla
            img_size = (50, 50)  # Nuevo tamaño deseado para las imágenes en la tabla
            resized_image = self.load_resized_image(self.png_paths[color], img_size)
            
            # Colocar imagen
            img_label = tk.Label(self.table_frame, image=resized_image, padx=10, pady=5)
            img_label.image = resized_image  # Mantener referencia a la imagen
            img_label.grid(row=i + 1, column=0, padx=5, pady=5, sticky='nsew')

            # Colocar datos
            data_label = tk.Label(self.table_frame, text=labels[i], padx=10, pady=5)
            data_label.grid(row=i + 1, column=1, padx=5, pady=5, sticky='nsew')

        # Configurar la expansión de las columnas y filas
        for col in range(2):
            self.table_frame.columnconfigure(col, weight=1)
        for row in range(4):
            self.table_frame.rowconfigure(row, weight=1)

def detect_lines(image_path):
    try:
        image = cv2.imread(image_path)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        color_ranges = {
            'rojo': [(np.array([0, 100, 100]), np.array([10, 255, 255])),
                     (np.array([160, 100, 100]), np.array([180, 255, 255]))],
            'verde': [(np.array([35, 100, 100]), np.array([85, 255, 255]))],
            'amarillo': [(np.array([20, 100, 100]), np.array([30, 255, 255]))]
        }

        masks = {}
        for color, ranges in color_ranges.items():
            mask = np.zeros_like(hsv[:, :, 0])
            for lower, upper in ranges:
                mask += cv2.inRange(hsv, lower, upper)
            mask = cv2.medianBlur(mask, 5)
            masks[color] = mask

        contours = {color: cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
                    for color, mask in masks.items()}

        for color, contours_list in contours.items():
            coordinates = [tuple(point[0]) for contour in contours_list for point in contour]
            with open(f'coordenadas_{color}.txt', 'w') as f:
                f.writelines(f"{x},{y}\n" for x, y in coordinates)

    except Exception as e:
        print(f"Error al procesar la imagen: {e}")

# Ejecutar funciones
image_path = 'pw.png'
png_paths = {
    'rojo': 'camion.png',
    'verde': 'camion2.png',
    'amarillo': '4x4.png'
}
new_sizes = {
    'rojo': (40, 30),
    'verde': (30, 30),
    'amarillo': (30, 20)
}

detect_lines(image_path)

root = tk.Tk()
root.title("Camiones 2D")
animator = TruckAnimator(root, image_path, png_paths, new_sizes)
root.mainloop()
