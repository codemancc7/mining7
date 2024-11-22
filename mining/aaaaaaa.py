import cv2
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from tkinter import ttk        
import random
class TruckAnimator:
    def __init__(self, root, image_path, png_paths, new_sizes, logo_path):
        self.root = root
        self.image_path = image_path
        self.png_paths = png_paths
        self.new_sizes = new_sizes
        self.logo_path = logo_path
        # Inicializar el tamaño del logo (ajustar aquí)sss
        self.logo_size = (200, 200)  # Tamaño del logo en píxeles

        # Crear el notebook y las pestañas
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        # Crear las pestañas
        self.tab1 = ttk.Frame(self.notebook)
        self.tab2 = ttk.Frame(self.notebook)  # Puedes agregar más pestañas según sea necesario

        self.notebook.add(self.tab1, text='Camiones')
        self.notebook.add(self.tab2, text='Otra Pestaña')  # Título para la pestaña adicional

        # Crear los marcos en la primera pestaña
        self.menu_frame = tk.Frame(self.tab1, width=200, bg='gray', padx=10, pady=10)
        self.menu_frame.pack(side=tk.LEFT, fill=tk.Y, expand=False)

        self.canvas_frame = tk.Frame(self.tab1)
        self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.table_frame = tk.Frame(self.tab1)
        self.table_frame.pack(side=tk.TOP, fill=tk.X)

        self.graph_frame = tk.Frame(self.tab1)
        self.graph_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        self.data_table_frame = tk.Frame(self.tab1)
        self.data_table_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        self.table_below_canvas_frame = tk.Frame(self.canvas_frame)
        self.table_below_canvas_frame.grid(row=1, column=0, sticky='nsew')

        # Cargar imagen de fondo
        self.background_image = Image.open(image_path)
        self.tk_background_image = ImageTk.PhotoImage(self.background_image)
        self.canvas = tk.Canvas(self.canvas_frame, width=self.background_image.width, height=self.background_image.height)
        self.canvas.grid(row=0, column=0, sticky='nsew')
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_background_image)

        # Cargar y redimensionar imágenes PNG
        self.images = {color: self.load_resized_image(path, size)
                       for color, (path, size) in zip(png_paths.keys(), zip(png_paths.values(), new_sizes.values()))}
        self.image_ids = {color: self.canvas.create_image(0, 0, anchor=tk.NW, image=image) 
                          for color, image in self.images.items()}
        self.truck_data = {'camion.png': [], 'camion2.png': []}
        self.create_truck_comparison_graph()
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

        # Datos del gráfico
        self.hours = []
        self.minerals = []
        self.time_counter = 0
        self.graph_update_id = None

        # Crear menú
        self.create_menu()
        
        # Crear tabla
        self.create_table()
        
        # Crear gráfica
        self.create_graph()
        
        # Crear tabla de datos
        self.create_data_table()

        # Crear tabla debajo del canvas
        self.create_table_below_canvas()

    def load_resized_image(self, path, size):
        try:
            image = Image.open(path).resize(size)
            return ImageTk.PhotoImage(image)
        except IOError:
            print(f"Error al cargar la imagen {path}")
            return ImageTk.PhotoImage(Image.new('RGBA', size))  # Imagen vacía por defecto

    def validate_coordinates(self, coords):
        width, height = self.background_image.width, self.background_image.height
        return [(x, y) for x, y in coords if 0 <= x < width and 0 <= y < height]

    def start_animation(self):
        self.animating = True
        self.animate()
        self.start_graph_update()

    def stop_animation(self):
        self.animating = False
        self.stop_graph_update()

    def reset_animation(self):
        self.stop_animation()
        self.indices = {color: 0 for color in ['rojo', 'verde', 'amarillo']}
        for color in ['rojo', 'verde', 'amarillo']:
            if self.coordinates[color]:
                self.canvas.coords(self.image_ids[color], *self.coordinates[color][0])
        self.reset_graph()
        self.time_counter = 0  # Reiniciar el contador de tiempo
        self.update_data_table()  # Actualizar tabla de datos al reiniciar

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
        # Cargar y mostrar el logo con tamaño ajustado
        try:
            logo_image = Image.open(self.logo_path).resize(self.logo_size)  # Ajustar tamaño según sea necesario
            self.logo_photo = ImageTk.PhotoImage(logo_image)
            logo_label = tk.Label(self.menu_frame, image=self.logo_photo, bg='gray')
            logo_label.pack(pady=10)

        except IOError:
            print(f"Error al cargar el logo {self.logo_path}")

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
            header_label = tk.Label(self.table_frame, text=header, bg='lightgray', padx=10, pady=5, font=('Helvetica', 18))
            header_label.grid(row=0, column=col, sticky='nsew')

        # Contenido de la tabla
        labels = ['Cat 797', 'AD30', 'Toyota 4x4']
        for i, (color, image) in enumerate(self.images.items()):
            # Ajustar tamaño de las imágenes en la tabla
            img_size = (75, 70)  # Nuevo tamaño deseado para las imágenes en la tabla
            resized_image = self.load_resized_image(self.png_paths[color], img_size)
            
            # Colocar imagen
            img_label = tk.Label(self.table_frame, image=resized_image, padx=10, pady=5)
            img_label.image = resized_image  # Mantener referencia a la imagen
            img_label.grid(row=i + 1, column=0, padx=5, pady=5, sticky='nsew')

            # Colocar datos
            data_label = tk.Label(self.table_frame, text=labels[i], padx=10, pady=5, font=('Helvetica', 15))
            data_label.grid(row=i + 1, column=1, padx=5, pady=5, sticky='nsew')

        # Configurar la expansión de las columnas y filas
        for col in range(2):
            self.table_frame.columnconfigure(col, weight=1)
        for row in range(4):
            self.table_frame.rowconfigure(row, weight=1)

    def create_table_below_canvas(self):
        # Crear tabla de datos debajo del canvas usando ttk.Treeview
        self.table_below_canvas = ttk.Treeview(self.table_below_canvas_frame, columns=('Item', 'Cantidad'), show='headings')
        self.table_below_canvas.heading('Item', text='Item')
        self.table_below_canvas.heading('Cantidad', text='Cantidad')
        self.table_below_canvas.pack(fill=tk.BOTH, expand=True)

    def create_graph(self):
        self.fig, self.ax = plt.subplots(figsize=(8, 4), dpi=100)
        self.ax.set_title('Acarreo de Mineral por Tiempo')
        self.ax.set_xlabel('Horas')
        self.ax.set_ylabel('Minerales (toneladas)')
        self.ax.set_xlim(0, 24)  # Ajustar según sea necesario
        self.ax.set_ylim(7500, 8300)  # Ajustar según sea necesario

        self.line, = self.ax.plot([], [], 'o-', label='Mineral Acarreado')
        self.ax.legend()

        self.canvas_graph = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas_graph.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def update_graph(self):
        self.hours.append(self.time_counter)
        self.minerals.append(np.random.randint(7500, 8300))  # Generar valor aleatorio entre 400 y 500
        self.line.set_data(self.hours, self.minerals)
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas_graph.draw()
        self.update_data_table()  # Actualizar tabla de datos después de actualizar el gráfico

    def start_graph_update(self):
        self.time_counter += 1
        self.update_graph()
        self.graph_update_id = self.root.after(7000, self.start_graph_update)  # Actualizar cada 4 segundos

    def stop_graph_update(self):
        if self.graph_update_id:
            self.root.after_cancel(self.graph_update_id)
            self.graph_update_id = None

    def reset_graph(self):
        self.hours = []
        self.minerals = []
        self.line.set_data([], [])
        self.ax.set_xlim(0, 24)  # Asegúrate de ajustar los límites según sea necesario
        self.ax.set_ylim(7500, 8300)  # Asegúrate de ajustar los límites según sea necesario
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas_graph.draw()

    def create_data_table(self):

        style = ttk.Style()
        style.configure('Treeview', font=('Helvetica', 14))
        style.configure('Treeview.Heading', font=('Helvetica', 16)) #tamaño de fuente -----

        # Crear tabla de datos usando ttk.Treeview
        self.data_table = ttk.Treeview(self.data_table_frame, columns=('Horas', 'Minerales'), show='headings')
        self.data_table.heading('Horas', text='Horas')
        self.data_table.heading('Minerales', text='Minerales (toneladas)')
        self.data_table.pack(fill=tk.BOTH, expand=True)

        # Crear una fila para mostrar el total
        self.total_label = tk.Label(self.data_table_frame, text="Total Acarreo (toneladas):", font=('Helvetica', 15))
        self.total_label.pack(side=tk.LEFT, padx=10, pady=5)
        self.total_value = tk.Label(self.data_table_frame, text="0", font=('Helvetica', 15))
        self.total_value.pack(side=tk.LEFT, padx=10, pady=5)

    def update_data_table(self):
        # Limpiar la tabla antes de agregar nuevos datos
        for row in self.data_table.get_children():
            self.data_table.delete(row)

        # Insertar los datos en la tabla
        for hour, mineral in zip(self.hours, self.minerals):
            self.data_table.insert('', tk.END, values=(hour, mineral))

        # Calcular y mostrar el total
        total_acarreo = sum(self.minerals)
        self.total_value.config(text=str(total_acarreo))
        self.update_table_below_canvas(total_acarreo)  # Actualizar tabla debajo del canvas

    def update_table_below_canvas(self, total_acarreo):
        # Limpiar la tabla antes de agregar nuevos datos
        for row in self.table_below_canvas.get_children():
            self.table_below_canvas.delete(row)

        # Calcular valores
        oro = total_acarreo * 0.02
        cobre = total_acarreo * 0.08     
        plata = total_acarreo * 0.05
        Zinc = total_acarreo * 0.07
        Molibdenita = total_acarreo * 0.4
        desmonte = total_acarreo * 0.74


        # Insertar datos en la tabla
        self.table_below_canvas.insert('', tk.END, values=('oro_Au', f"{oro:.2f} toneladas"))
        self.table_below_canvas.insert('', tk.END, values=('cobre_Cu', f"{cobre:.2f} toneladas"))
        self.table_below_canvas.insert('', tk.END, values=('plata_Ag', f"{plata:.2f} toneladas"))
        self.table_below_canvas.insert('', tk.END, values=('Zinc_Zn', f"{Zinc:.2f} toneladas"))
        self.table_below_canvas.insert('', tk.END, values=('Molibdenita_MoS2', f"{Molibdenita:.2f} toneladas"))
        self.table_below_canvas.insert('', tk.END, values=('desmonte', f"{desmonte:.2f} toneladas"))

    def create_truck_comparison_graph(self):
        self.truck_fig, self.truck_ax = plt.subplots(figsize=(8, 4), dpi=100)
        self.truck_ax.set_title('Comparación de Camiones por Hora')
        self.truck_ax.set_xlabel('Horas')
        self.truck_ax.set_ylabel('Toneladas de Mineral')
        
        self.truck_lines = {}
        for truck in self.truck_data.keys():
            line, = self.truck_ax.plot([], [], 'o-', label=truck)
            self.truck_lines[truck] = line
        
        self.truck_ax.legend()
        self.truck_ax.set_xlim(0, 24)  # Set x-axis limit to 24 hours
        self.truck_ax.set_ylim(0, 8300)  # Set y-axis limit based on your data range

        self.truck_canvas = FigureCanvasTkAgg(self.truck_fig, master=self.tab2)
        self.truck_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def update_truck_comparison_graph(self):
        if not self.minerals:
            return

        total_mineral = self.minerals[-1]
        
        # Generate a random split ratio between 0.3 and 0.7
        split_ratio = random.uniform(0.3, 0.7)
        
        truck1_mineral = int(total_mineral * split_ratio)
        truck2_mineral = total_mineral - truck1_mineral

        self.truck_data['camion.png'].append(truck1_mineral)
        self.truck_data['camion2.png'].append(truck2_mineral)

        for truck, line in self.truck_lines.items():
            line.set_data(self.hours, self.truck_data[truck])

        self.truck_ax.relim()
        self.truck_ax.autoscale_view()
        self.truck_canvas.draw()

    def start_animation(self):
        self.animating = True
        self.animate()
        self.start_graph_update()

    def stop_animation(self):
        self.animating = False
        self.stop_graph_update()

    def reset_animation(self):
        self.stop_animation()
        self.indices = {color: 0 for color in ['rojo', 'verde', 'amarillo']}
        for color in ['rojo', 'verde', 'amarillo']:
            if self.coordinates[color]:
                self.canvas.coords(self.image_ids[color], *self.coordinates[color][0])
        self.reset_graph()
        self.time_counter = 0
        self.update_data_table()
        self.reset_truck_comparison_graph()

    def reset_truck_comparison_graph(self):
        for truck in self.truck_data:
            self.truck_data[truck] = []
        for line in self.truck_lines.values():
            line.set_data([], [])
        self.truck_ax.relim()
        self.truck_ax.autoscale_view()
        self.truck_canvas.draw()

    def start_graph_update(self):
        self.time_counter += 1
        self.update_graph()
        self.update_truck_comparison_graph()
        self.graph_update_id = self.root.after(7000, self.start_graph_update)
        
if __name__ == '__main__':
    root = tk.Tk()
    root.title("Animador de Camiones")

    image_path = "pw.png"
    png_paths = {
        'rojo': 'camion.png',
        'verde': 'camion2.png',
        'amarillo': '4x4.png'
    }
    new_sizes = {
        'rojo': (50, 50),
        'verde': (50, 50),
        'amarillo': (50, 50)
    }
    logo_path = 'logo1.png'

    app = TruckAnimator(root, image_path, png_paths, new_sizes, logo_path)
    root.mainloop()
