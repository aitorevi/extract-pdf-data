"""
Editor unificado de plantillas - Crear y Editar en una sola herramienta.
Campos predefinidos: solo cambias coordenadas.
"""

import pdfplumber
import json
import os
import platform
from pdf2image import convert_from_path
from PIL import Image, ImageDraw
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
from PIL import ImageTk


# CAMPOS DE IDENTIFICACIÓN - Para identificar la plantilla correcta (no se exportan)
CAMPOS_IDENTIFICACION = [
    {"nombre": "CIF_Identificacion", "tipo": "texto", "descripcion": "CIF del proveedor para identificación"},
    {"nombre": "Nombre_Identificacion", "tipo": "texto", "descripcion": "Nombre completo del proveedor para identificación"},
]

# CAMPOS DE DATOS - Campos a capturar y exportar al Excel
CAMPOS_PREDEFINIDOS = [
    {"nombre": "FechaFactura", "tipo": "fecha", "opcional": False},
    {"nombre": "FechaVto", "tipo": "fecha", "opcional": True},  # Campo opcional
    {"nombre": "NumFactura", "tipo": "texto", "opcional": False},
    {"nombre": "Base", "tipo": "numerico", "opcional": False},
]

# CAMPOS AUXILIARES - Se capturan para cálculos, NO se exportan
CAMPOS_AUXILIARES = [
    {"nombre": "Portes", "tipo": "numerico", "opcional": True,
     "descripcion": "Portes (se suma automáticamente a Base)"},
]


class EditorPlantillas:
    def __init__(self, pdf_path, plantilla_existente=None):
        self.pdf_path = pdf_path
        self.imagen = None
        self.imagen_original = None
        self.imagenes_paginas = []  # Lista de todas las imágenes del PDF
        self.pagina_actual = 0  # Página que se está visualizando (0-indexed)
        self.total_paginas = 0  # Total de páginas del PDF
        self.campos = {}  # {nombre_campo: {'coordenadas': [...], 'pagina': N}} o None
        self.seleccion_actual = None
        self.punto_inicio = None
        self.plantilla_cargada = plantilla_existente

        # Inicializar campos de identificación
        for campo_def in CAMPOS_IDENTIFICACION:
            self.campos[campo_def['nombre']] = None

        # Inicializar campos de datos
        for campo_def in CAMPOS_PREDEFINIDOS:
            self.campos[campo_def['nombre']] = None

        # Inicializar campos auxiliares
        for campo_def in CAMPOS_AUXILIARES:
            self.campos[campo_def['nombre']] = None

        # Si hay plantilla cargada, cargar coordenadas existentes
        if plantilla_existente and 'campos' in plantilla_existente:
            for campo in plantilla_existente['campos']:
                if campo['nombre'] in self.campos:
                    # Compatibilidad: si no tiene 'pagina', asumir página 1 (índice 0)
                    pagina = campo.get('pagina', 1) - 1  # Convertir a 0-indexed
                    self.campos[campo['nombre']] = {
                        'coordenadas': campo['coordenadas'],
                        'pagina': pagina
                    }

        # Obtener dimensiones del PDF
        with pdfplumber.open(pdf_path) as pdf:
            self.pdf_width = pdf.pages[0].width
            self.pdf_height = pdf.pages[0].height

        # Crear ventana
        self.root = tk.Tk()
        self.root.title("Editor de Plantillas")

        # Configurar geometría
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.window_width = min(1400, screen_width - 100)
        self.window_height = min(900, screen_height - 100)
        x = (screen_width - self.window_width) // 2
        y = (screen_height - self.window_height) // 2
        self.root.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")

        # Panel derecho
        frame_botones = tk.Frame(self.root, bg="gray90", padx=10)
        frame_botones.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Label(frame_botones, text="EDITOR DE PLANTILLAS", font=("Arial", 12, "bold"),
                bg="gray90", pady=10).pack(side=tk.TOP)

        # Controles de navegación entre páginas
        frame_navegacion = tk.Frame(frame_botones, bg="gray90")
        frame_navegacion.pack(side=tk.TOP, pady=5)

        self.btn_anterior = tk.Button(frame_navegacion, text="◀", command=self.pagina_anterior,
                                      font=("Arial", 10, "bold"), width=3)
        self.btn_anterior.pack(side=tk.LEFT, padx=2)

        self.label_pagina = tk.Label(frame_navegacion, text="Página 1/1",
                                     bg="gray90", font=("Arial", 10))
        self.label_pagina.pack(side=tk.LEFT, padx=5)

        self.btn_siguiente = tk.Button(frame_navegacion, text="▶", command=self.pagina_siguiente,
                                       font=("Arial", 10, "bold"), width=3)
        self.btn_siguiente.pack(side=tk.LEFT, padx=2)

        # Label campo seleccionado
        self.label_seleccionado = tk.Label(frame_botones,
                                          text="Ningún campo seleccionado",
                                          bg="lightyellow", fg="blue",
                                          font=("Arial", 10, "bold"),
                                          wraplength=200, pady=10)
        self.label_seleccionado.pack(side=tk.TOP, fill=tk.X, pady=5)

        # Botones principales
        tk.Button(frame_botones, text="✓ GUARDAR", command=self.guardar_plantilla,
                 bg="black", fg="white", font=("Arial", 14, "bold"),
                 width=15, height=3).pack(side=tk.TOP, pady=10)

        tk.Button(frame_botones, text="📂 CARGAR\nOTRA PLANTILLA", command=self.cargar_plantilla,
                 bg="blue", fg="white", font=("Arial", 11, "bold"),
                 width=15, height=2).pack(side=tk.TOP, pady=5)

        tk.Button(frame_botones, text="🔄 CAMBIAR PDF", command=self.cambiar_pdf,
                 bg="purple", fg="white", font=("Arial", 11, "bold"),
                 width=15, height=2).pack(side=tk.TOP, pady=5)

        tk.Button(frame_botones, text="✕ SALIR", command=self.root.quit,
                 bg="red", fg="white", font=("Arial", 11, "bold"),
                 width=15, height=2).pack(side=tk.TOP, pady=10)

        # Separador
        tk.Label(frame_botones, text="", bg="gray90", height=1).pack(side=tk.TOP)
        tk.Label(frame_botones, text="CAMPOS:", font=("Arial", 11, "bold"),
                bg="gray90").pack(side=tk.TOP)

        # Lista de campos con botones
        self.frame_campos = tk.Frame(frame_botones, bg="white")
        self.frame_campos.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=5)

        # Canvas con scrollbar para campos
        canvas_campos = tk.Canvas(self.frame_campos, bg="white", highlightthickness=0)
        scrollbar = tk.Scrollbar(self.frame_campos, orient="vertical", command=canvas_campos.yview)
        self.scrollable_frame = tk.Frame(canvas_campos, bg="white")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas_campos.configure(scrollregion=canvas_campos.bbox("all"))
        )

        canvas_campos.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas_campos.configure(yscrollcommand=scrollbar.set)

        canvas_campos.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.actualizar_lista_campos()

        # Frame para canvas PDF
        frame_canvas = tk.Frame(self.root)
        frame_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Canvas con scrollbars
        scrollbar_y = tk.Scrollbar(frame_canvas, orient=tk.VERTICAL)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        scrollbar_x = tk.Scrollbar(frame_canvas, orient=tk.HORIZONTAL)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.canvas = tk.Canvas(frame_canvas, cursor="cross",
                               yscrollcommand=scrollbar_y.set,
                               xscrollcommand=scrollbar_x.set,
                               bg="white")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar_y.config(command=self.canvas.yview)
        scrollbar_x.config(command=self.canvas.xview)

        # Eventos del mouse
        self.canvas.bind("<ButtonPress-1>", self.al_presionar)
        self.canvas.bind("<B1-Motion>", self.al_arrastrar)
        self.canvas.bind("<ButtonRelease-1>", self.al_soltar)

        # Campo seleccionado para capturar
        self.campo_seleccionado = None

    def cargar_imagen_pdf(self):
        """Convierte el PDF a imagen."""
        print("Convirtiendo PDF a imagen...")

        # Configurar ruta de Poppler según el sistema operativo
        sistema = platform.system()

        if sistema == "Darwin":  # macOS
            # En macOS, usar poppler instalado con Homebrew
            poppler_path = "/opt/homebrew/bin"
        elif sistema == "Windows":
            # En Windows, usar poppler local del proyecto
            project_root = os.path.dirname(os.path.dirname(__file__))
            poppler_path = os.path.join(project_root, "poppler", "Library", "bin")
        else:
            # Linux u otros: intentar usar poppler del sistema (en PATH)
            poppler_path = None

        imagenes = convert_from_path(self.pdf_path, dpi=150, poppler_path=poppler_path)
        self.total_paginas = len(imagenes)
        print(f"PDF tiene {self.total_paginas} página(s)")

        # Guardar todas las imágenes sin procesar
        self.imagenes_originales = imagenes

        # Cargar la primera página
        self.imagen_original = imagenes[self.pagina_actual]
        self.imagen = self.imagen_original.copy()

        # Calcular escala inicial
        self.escala_x = self.imagen.width / self.pdf_width
        self.escala_y = self.imagen.height / self.pdf_height

        # Calcular espacio disponible (dejando margen para UI)
        # Ancho: toda la ventana menos panel derecho (~350px) y márgenes (~50px)
        espacio_ancho = self.window_width - 400
        # Alto: toda la ventana menos márgenes (~50px)
        espacio_alto = self.window_height - 50

        # Redimensionar para que quepa en el espacio disponible (sin scroll)
        if self.imagen.width > espacio_ancho or self.imagen.height > espacio_alto:
            # Calcular ratio manteniendo proporción
            ratio = min(espacio_ancho / self.imagen.width, espacio_alto / self.imagen.height)
            new_width = int(self.imagen.width * ratio)
            new_height = int(self.imagen.height * ratio)

            print(f"Redimensionando imagen: {self.imagen.width}x{self.imagen.height} → {new_width}x{new_height}")
            print(f"  Espacio disponible: {espacio_ancho}x{espacio_alto}")
            print(f"  Ratio aplicado: {ratio:.3f}")

            self.imagen = self.imagen.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.imagen_original = self.imagen_original.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Actualizar escalas (crítico para mantener coordenadas precisas)
            self.escala_x *= ratio
            self.escala_y *= ratio

            print(f"  Nuevas escalas: X={self.escala_x:.3f}, Y={self.escala_y:.3f}")

        self.actualizar_controles_navegacion()
        self.redibujar_campos()

    def mostrar_imagen(self):
        """Muestra la imagen en el canvas."""
        self.photo = ImageTk.PhotoImage(self.imagen)
        self.canvas.config(width=self.imagen.width, height=self.imagen.height,
                          scrollregion=(0, 0, self.imagen.width, self.imagen.height))
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

    def actualizar_controles_navegacion(self):
        """Actualiza el estado de los botones de navegación."""
        # Actualizar label de página
        self.label_pagina.config(text=f"Página {self.pagina_actual + 1}/{self.total_paginas}")

        # Habilitar/deshabilitar botones
        if self.pagina_actual == 0:
            self.btn_anterior.config(state=tk.DISABLED)
        else:
            self.btn_anterior.config(state=tk.NORMAL)

        if self.pagina_actual >= self.total_paginas - 1:
            self.btn_siguiente.config(state=tk.DISABLED)
        else:
            self.btn_siguiente.config(state=tk.NORMAL)

    def pagina_anterior(self):
        """Navega a la página anterior."""
        if self.pagina_actual > 0:
            self.pagina_actual -= 1
            self.cargar_pagina()

    def pagina_siguiente(self):
        """Navega a la página siguiente."""
        if self.pagina_actual < self.total_paginas - 1:
            self.pagina_actual += 1
            self.cargar_pagina()

    def cargar_pagina(self):
        """Carga y muestra la página actual."""
        print(f"Cargando página {self.pagina_actual + 1}/{self.total_paginas}...")

        # Cargar imagen de la página actual
        self.imagen_original = self.imagenes_originales[self.pagina_actual].copy()
        self.imagen = self.imagen_original.copy()

        # Recalcular escalas
        self.escala_x = self.imagen.width / self.pdf_width
        self.escala_y = self.imagen.height / self.pdf_height

        # Redimensionar si es necesario
        espacio_ancho = self.window_width - 400
        espacio_alto = self.window_height - 50

        if self.imagen.width > espacio_ancho or self.imagen.height > espacio_alto:
            ratio = min(espacio_ancho / self.imagen.width, espacio_alto / self.imagen.height)
            new_width = int(self.imagen.width * ratio)
            new_height = int(self.imagen.height * ratio)

            self.imagen = self.imagen.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.imagen_original = self.imagen_original.resize((new_width, new_height), Image.Resampling.LANCZOS)

            self.escala_x *= ratio
            self.escala_y *= ratio

        # Actualizar controles y redibujar
        self.actualizar_controles_navegacion()
        self.redibujar_campos()

    def actualizar_lista_campos(self):
        """Actualiza la lista de campos con botones."""
        # Limpiar frame
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Sección de campos de identificación
        tk.Label(self.scrollable_frame, text="🔍 CAMPOS DE IDENTIFICACIÓN",
                font=("Arial", 10, "bold"), bg="lightblue", pady=5).pack(fill=tk.X, padx=5, pady=(5,2))

        for i, campo_def in enumerate(CAMPOS_IDENTIFICACION):
            nombre = campo_def['nombre']
            tipo = campo_def['tipo']
            descripcion = campo_def.get('descripcion', '')
            campo_data = self.campos[nombre]
            tiene_coords = campo_data is not None

            frame_campo = tk.Frame(self.scrollable_frame, bg="white", pady=2)
            frame_campo.pack(fill=tk.X, padx=5, pady=2)

            if tiene_coords:
                color_fondo = "#4169E1"  # Azul royal
                color_texto = "white"
                texto_btn = "✓ EDITAR"
                color_btn = "orange"
                pagina_info = f" [Pág.{campo_data['pagina'] + 1}]"
            else:
                color_fondo = "#FF8C00"  # Naranja oscuro
                color_texto = "white"
                texto_btn = "+ CAPTURAR"
                color_btn = "blue"
                pagina_info = ""

            label = tk.Label(frame_campo, text=f"{i+1}. {nombre}{pagina_info}\n({descripcion})",
                           bg=color_fondo, fg=color_texto, font=("Arial", 8, "bold"),
                           width=20, anchor="w", padx=5, wraplength=150)
            label.pack(side=tk.LEFT, fill=tk.X, expand=True)

            btn = tk.Button(frame_campo, text=texto_btn,
                          bg=color_btn, fg="white",
                          font=("Arial", 8, "bold"),
                          command=lambda n=nombre: self.seleccionar_campo_para_captura(n))
            btn.pack(side=tk.RIGHT, padx=2)

        # Separador
        tk.Label(self.scrollable_frame, text="", bg="gray90", height=1).pack(fill=tk.X, pady=2)

        # Sección de campos de datos
        tk.Label(self.scrollable_frame, text="📊 CAMPOS DE DATOS",
                font=("Arial", 10, "bold"), bg="lightgreen", pady=5).pack(fill=tk.X, padx=5, pady=(5,2))

        for i, campo_def in enumerate(CAMPOS_PREDEFINIDOS):
            nombre = campo_def['nombre']
            tipo = campo_def['tipo']
            es_opcional = campo_def.get('opcional', False)
            campo_data = self.campos[nombre]
            tiene_coords = campo_data is not None

            frame_campo = tk.Frame(self.scrollable_frame, bg="white", pady=2)
            frame_campo.pack(fill=tk.X, padx=5, pady=2)

            if tiene_coords:
                color_fondo = "#228B22"  # Verde oscuro
                color_texto = "white"
                texto_btn = "✓ EDITAR"
                color_btn = "orange"
                pagina_info = f" [Pág.{campo_data['pagina'] + 1}]"
            else:
                if es_opcional:
                    color_fondo = "#4682B4"  # Azul acero (opcional)
                    color_texto = "white"
                else:
                    color_fondo = "#DC143C"  # Rojo crimson (obligatorio)
                    color_texto = "white"
                texto_btn = "+ CAPTURAR"
                color_btn = "blue"
                pagina_info = ""

            # Mostrar si es opcional
            texto_opcional = " (opcional)" if es_opcional else ""
            label = tk.Label(frame_campo, text=f"{i+1}. {nombre}{texto_opcional}{pagina_info}\n({tipo})",
                           bg=color_fondo, fg=color_texto, font=("Arial", 9, "bold"),
                           width=20, anchor="w", padx=5)
            label.pack(side=tk.LEFT, fill=tk.X, expand=True)

            btn = tk.Button(frame_campo, text=texto_btn,
                          bg=color_btn, fg="white",
                          font=("Arial", 8, "bold"),
                          command=lambda n=nombre: self.seleccionar_campo_para_captura(n))
            btn.pack(side=tk.RIGHT, padx=2)

        # Separador
        tk.Label(self.scrollable_frame, text="", bg="gray90", height=1).pack(fill=tk.X, pady=2)

        # Sección de campos auxiliares
        tk.Label(self.scrollable_frame, text="🔧 CAMPOS AUXILIARES (para cálculos)",
                font=("Arial", 10, "bold"), bg="lightyellow", pady=5).pack(fill=tk.X, padx=5, pady=(5,2))

        for i, campo_def in enumerate(CAMPOS_AUXILIARES):
            nombre = campo_def['nombre']
            tipo = campo_def['tipo']
            descripcion = campo_def.get('descripcion', '')
            campo_data = self.campos[nombre]
            tiene_coords = campo_data is not None

            frame_campo = tk.Frame(self.scrollable_frame, bg="white", pady=2)
            frame_campo.pack(fill=tk.X, padx=5, pady=2)

            if tiene_coords:
                color_fondo = "#FFA500"  # Naranja
                color_texto = "white"
                texto_btn = "✓ EDITAR"
                color_btn = "orange"
                pagina_info = f" [Pág.{campo_data['pagina'] + 1}]"
            else:
                color_fondo = "#FFD700"  # Dorado
                color_texto = "black"
                texto_btn = "+ CAPTURAR"
                color_btn = "blue"
                pagina_info = ""

            label = tk.Label(frame_campo, text=f"{i+1}. {nombre} (opcional){pagina_info}\n{descripcion}",
                           bg=color_fondo, fg=color_texto, font=("Arial", 8, "bold"),
                           width=20, anchor="w", padx=5, wraplength=150)
            label.pack(side=tk.LEFT, fill=tk.X, expand=True)

            btn = tk.Button(frame_campo, text=texto_btn,
                          bg=color_btn, fg="white",
                          font=("Arial", 8, "bold"),
                          command=lambda n=nombre: self.seleccionar_campo_para_captura(n))
            btn.pack(side=tk.RIGHT, padx=2)

    def seleccionar_campo_para_captura(self, nombre_campo):
        """Selecciona un campo para capturar sus coordenadas."""
        self.campo_seleccionado = nombre_campo
        self.label_seleccionado.config(
            text=f"SELECCIONADO:\n{nombre_campo}\n\nAhora arrastra sobre\nel PDF",
            bg="lightgreen"
        )
        print(f"→ Campo seleccionado: {nombre_campo}")

    def al_presionar(self, event):
        """Cuando se presiona el mouse."""
        if self.campo_seleccionado is None:
            # No mostrar modal, solo actualizar label
            self.label_seleccionado.config(
                text="⚠️ SELECCIONA\nUN CAMPO\nde la lista →",
                bg="orange"
            )
            return

        self.punto_inicio = (event.x, event.y)
        if self.seleccion_actual:
            self.canvas.delete(self.seleccion_actual)

    def al_arrastrar(self, event):
        """Cuando se arrastra el mouse."""
        if self.punto_inicio and self.campo_seleccionado:
            if self.seleccion_actual:
                self.canvas.delete(self.seleccion_actual)
            self.seleccion_actual = self.canvas.create_rectangle(
                self.punto_inicio[0], self.punto_inicio[1],
                event.x, event.y,
                outline="red", width=3
            )

    def al_soltar(self, event):
        """Cuando se suelta el mouse."""
        if not self.punto_inicio or not self.campo_seleccionado:
            return

        x1, y1 = self.punto_inicio
        x2, y2 = event.x, event.y

        # Normalizar coordenadas
        x_min, x_max = min(x1, x2), max(x1, x2)
        y_min, y_max = min(y1, y2), max(y1, y2)

        # Verificar que no sea un clic sin arrastre
        if abs(x_max - x_min) < 5 or abs(y_max - y_min) < 5:
            if self.seleccion_actual:
                self.canvas.delete(self.seleccion_actual)
            self.punto_inicio = None
            return

        # Convertir a coordenadas PDF
        pdf_x0 = x_min / self.escala_x
        pdf_top = y_min / self.escala_y
        pdf_x1 = x_max / self.escala_x
        pdf_bottom = y_max / self.escala_y

        # Guardar coordenadas con número de página
        self.campos[self.campo_seleccionado] = {
            'coordenadas': [pdf_x0, pdf_top, pdf_x1, pdf_bottom],
            'pagina': self.pagina_actual
        }

        print(f"✓ Campo actualizado: {self.campo_seleccionado} -> Página {self.pagina_actual + 1}, coords: {[pdf_x0, pdf_top, pdf_x1, pdf_bottom]}")

        # Redibujar
        self.redibujar_campos()
        self.actualizar_lista_campos()

        # Actualizar label
        self.label_seleccionado.config(
            text=f"✓ Capturado:\n{self.campo_seleccionado}\n\nSelecciona otro\no guarda",
            bg="lightblue"
        )

        # Limpiar selección
        self.campo_seleccionado = None
        self.seleccion_actual = None
        self.punto_inicio = None

    def redibujar_campos(self):
        """Redibuja todos los campos capturados de la página actual."""
        self.imagen = self.imagen_original.copy()
        draw = ImageDraw.Draw(self.imagen)

        # Dibujar campos de identificación en azul (solo de la página actual)
        for i, campo_def in enumerate(CAMPOS_IDENTIFICACION, 1):
            nombre = campo_def['nombre']
            campo_data = self.campos[nombre]

            if campo_data and isinstance(campo_data, dict):
                # Solo dibujar si es de la página actual
                if campo_data['pagina'] == self.pagina_actual:
                    coords = campo_data['coordenadas']
                    ix0 = int(coords[0] * self.escala_x)
                    iy0 = int(coords[1] * self.escala_y)
                    ix1 = int(coords[2] * self.escala_x)
                    iy1 = int(coords[3] * self.escala_y)

                    draw.rectangle([ix0, iy0, ix1, iy1], outline="blue", width=3)
                    draw.text((ix0 + 5, iy0 + 5), f"ID{i}: {nombre}", fill="blue")

        # Dibujar campos de datos en verde (solo de la página actual)
        for i, campo_def in enumerate(CAMPOS_PREDEFINIDOS, 1):
            nombre = campo_def['nombre']
            campo_data = self.campos[nombre]

            if campo_data and isinstance(campo_data, dict):
                # Solo dibujar si es de la página actual
                if campo_data['pagina'] == self.pagina_actual:
                    coords = campo_data['coordenadas']
                    ix0 = int(coords[0] * self.escala_x)
                    iy0 = int(coords[1] * self.escala_y)
                    ix1 = int(coords[2] * self.escala_x)
                    iy1 = int(coords[3] * self.escala_y)

                    draw.rectangle([ix0, iy0, ix1, iy1], outline="green", width=3)
                    draw.text((ix0 + 5, iy0 + 5), f"{i}. {nombre}", fill="green")

        # Dibujar campos auxiliares en naranja (solo de la página actual)
        for i, campo_def in enumerate(CAMPOS_AUXILIARES, 1):
            nombre = campo_def['nombre']
            campo_data = self.campos[nombre]

            if campo_data and isinstance(campo_data, dict):
                # Solo dibujar si es de la página actual
                if campo_data['pagina'] == self.pagina_actual:
                    coords = campo_data['coordenadas']
                    ix0 = int(coords[0] * self.escala_x)
                    iy0 = int(coords[1] * self.escala_y)
                    ix1 = int(coords[2] * self.escala_x)
                    iy1 = int(coords[3] * self.escala_y)

                    draw.rectangle([ix0, iy0, ix1, iy1], outline="orange", width=3)
                    draw.text((ix0 + 5, iy0 + 5), f"AUX{i}: {nombre}", fill="orange")

        self.mostrar_imagen()

    def cargar_plantilla(self):
        """Carga una plantilla existente."""
        archivo = filedialog.askopenfilename(
            title="Seleccionar plantilla",
            initialdir="plantillas",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if not archivo:
            return

        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                plantilla = json.load(f)

            if 'campos' not in plantilla:
                messagebox.showerror("Error", "Plantilla inválida")
                return

            # Cargar coordenadas
            for campo in plantilla['campos']:
                if campo['nombre'] in self.campos:
                    self.campos[campo['nombre']] = campo['coordenadas']

            self.plantilla_cargada = plantilla
            self.redibujar_campos()
            self.actualizar_lista_campos()

            messagebox.showinfo("Cargado", f"Plantilla cargada:\n{os.path.basename(archivo)}")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar:\n{e}")

    def cambiar_pdf(self):
        """Cambia el PDF de referencia."""
        pdf_path = filedialog.askopenfilename(
            title="Seleccionar PDF",
            initialdir="facturas",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )

        if pdf_path:
            self.pdf_path = pdf_path
            self.cargar_imagen_pdf()

    def guardar_plantilla(self):
        """Guarda la plantilla."""
        print("\n=== GUARDANDO PLANTILLA ===")

        # Verificar campos OBLIGATORIOS de DATOS (opcional=False)
        campos_obligatorios = [c['nombre'] for c in CAMPOS_PREDEFINIDOS if not c.get('opcional', False)]
        faltantes_obligatorios = [nombre for nombre in campos_obligatorios
                                 if self.campos.get(nombre) is None]

        if faltantes_obligatorios:
            print(f"Faltan campos obligatorios: {faltantes_obligatorios}")
            if not messagebox.askyesno("Campos obligatorios incompletos",
                                      f"Faltan campos obligatorios:\n" + "\n".join(f"- {c}" for c in faltantes_obligatorios) +
                                      "\n\n¿Guardar de todos modos?"):
                print("Guardado cancelado por usuario")
                return

        # Verificar campos de IDENTIFICACIÓN (son opcionales pero avisar)
        campos_id_nombres = [c['nombre'] for c in CAMPOS_IDENTIFICACION]
        faltantes_id = [nombre for nombre, coords in self.campos.items()
                       if coords is None and nombre in campos_id_nombres]

        if faltantes_id:
            print(f"AVISO: Campos de identificación no capturados: {faltantes_id}")
            messagebox.showwarning("Campos de identificación faltantes",
                                  f"Campos de identificación no capturados:\n" + "\n".join(f"- {c}" for c in faltantes_id) +
                                  "\n\nLa identificación automática puede no funcionar.\n" +
                                  "Se recomienda capturar al menos el CIF o el Nombre del proveedor.",
                                  parent=self.root)

        # Pedir información si es nueva
        if self.plantilla_cargada:
            nombre_proveedor = self.plantilla_cargada.get('nombre_proveedor', '')
            cif_proveedor = self.plantilla_cargada.get('cif_proveedor', '')
            nombre_archivo_inicial = self.plantilla_cargada.get('nombre_proveedor', '').replace(' ', '_').lower()
            print(f"Editando plantilla existente: {nombre_proveedor}")
            nombre_archivo = simpledialog.askstring("Guardar",
                                                 "Nombre del archivo (sin .json):",
                                                 initialvalue=nombre_archivo_inicial,
                                                 parent=self.root)
        else:
            print("Creando plantilla nueva")
            nombre_proveedor = simpledialog.askstring("Nombre Proveedor",
                                                      "Nombre del proveedor:",
                                                      parent=self.root)
            if not nombre_proveedor:
                print("Guardado cancelado - sin nombre de proveedor")
                return

            cif_proveedor = simpledialog.askstring("CIF Proveedor",
                                                   "CIF del proveedor:",
                                                   parent=self.root)

            # Sugerir nombre de archivo basado en el nombre del proveedor
            nombre_archivo_sugerido = nombre_proveedor.replace(' ', '_').lower()
            nombre_archivo = simpledialog.askstring("Nombre de Plantilla",
                                                    "Nombre del archivo (sin .json):",
                                                    initialvalue=nombre_archivo_sugerido,
                                                    parent=self.root)

        if not nombre_archivo:
            print("Guardado cancelado - sin nombre de archivo")
            return

        print(f"Nombre archivo: {nombre_archivo}")
        print(f"Nombre proveedor: {nombre_proveedor}")
        print(f"CIF proveedor: {cif_proveedor}")

        # Crear lista de todos los campos (identificación + datos)
        campos_lista = []

        # Añadir campos de identificación
        for campo_def in CAMPOS_IDENTIFICACION:
            nombre = campo_def['nombre']
            campo_data = self.campos[nombre]
            if campo_data:
                campos_lista.append({
                    "nombre": nombre,
                    "coordenadas": campo_data['coordenadas'],
                    "pagina": campo_data['pagina'] + 1,  # Guardar en formato 1-indexed
                    "tipo": campo_def['tipo'],
                    "es_identificacion": True
                })

        # Añadir campos de datos
        for campo_def in CAMPOS_PREDEFINIDOS:
            nombre = campo_def['nombre']
            campo_data = self.campos[nombre]
            if campo_data:
                campos_lista.append({
                    "nombre": nombre,
                    "coordenadas": campo_data['coordenadas'],
                    "pagina": campo_data['pagina'] + 1,  # Guardar en formato 1-indexed
                    "tipo": campo_def['tipo'],
                    "es_identificacion": False
                })

        # Añadir campos auxiliares
        for campo_def in CAMPOS_AUXILIARES:
            nombre = campo_def['nombre']
            campo_data = self.campos[nombre]
            if campo_data:
                campos_lista.append({
                    "nombre": nombre,
                    "coordenadas": campo_data['coordenadas'],
                    "pagina": campo_data['pagina'] + 1,  # Guardar en formato 1-indexed
                    "tipo": campo_def['tipo'],
                    "es_identificacion": False,
                    "es_auxiliar": True
                })

        print(f"Campos a guardar: {len(campos_lista)}")

        plantilla = {
            "nombre_proveedor": nombre_proveedor or "Proveedor",
            "cif_proveedor": cif_proveedor or "",
            "pdf_referencia": self.pdf_path,
            "campos": campos_lista
        }

        # Guardar
        try:
            os.makedirs("plantillas", exist_ok=True)
            ruta = f"plantillas/{nombre_archivo}.json"

            print(f"Guardando en: {ruta}")

            with open(ruta, 'w', encoding='utf-8') as f:
                json.dump(plantilla, f, ensure_ascii=False, indent=4)

            print(f"✓ Archivo guardado exitosamente")
            messagebox.showinfo("Guardado",
                              f"✓ Plantilla guardada:\n{ruta}\n\nCampos: {len(campos_lista)}",
                              parent=self.root)
            print(f"✓ Plantilla guardada: {ruta}")

        except Exception as e:
            print(f"ERROR al guardar: {e}")
            messagebox.showerror("Error", f"No se pudo guardar:\n{e}", parent=self.root)

    def ejecutar(self):
        """Ejecuta la aplicación."""
        self.cargar_imagen_pdf()
        self.root.mainloop()


def main():
    print("="*60)
    print("  EDITOR UNIFICADO DE PLANTILLAS")
    print("="*60)
    print("\nCampos predefinidos:")
    for i, campo in enumerate(CAMPOS_PREDEFINIDOS, 1):
        print(f"  {i}. {campo['nombre']} ({campo['tipo']})")

    print("\nOpciones:")
    print("1. Crear plantilla nueva")
    print("2. Editar plantilla existente")

    opcion = input("\nSelecciona (1/2): ").strip()

    # Crear ventana raíz temporal para los diálogos (evita ventanas en blanco en algunos PCs)
    root_temp = tk.Tk()
    root_temp.withdraw()  # Ocultar la ventana raíz

    plantilla_existente = None

    if opcion == "2":
        archivo = filedialog.askopenfilename(
            title="Seleccionar plantilla a editar",
            initialdir="plantillas",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if archivo:
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    plantilla_existente = json.load(f)
                print(f"✓ Plantilla cargada: {os.path.basename(archivo)}")
            except Exception as e:
                print(f"Error: {e}")
                root_temp.destroy()
                return

    print("\nSelecciona el PDF de la factura...")
    pdf_path = filedialog.askopenfilename(
        title="Seleccionar PDF de factura",
        initialdir="facturas",
        filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
    )

    if not pdf_path:
        print("No se seleccionó PDF")
        root_temp.destroy()
        return

    print(f"✓ PDF seleccionado: {os.path.basename(pdf_path)}")

    # Destruir la ventana temporal antes de crear la ventana del editor
    root_temp.destroy()

    try:
        app = EditorPlantillas(pdf_path, plantilla_existente)
        app.ejecutar()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
