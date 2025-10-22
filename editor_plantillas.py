"""
Editor unificado de plantillas - Crear y Editar en una sola herramienta.
Campos predefinidos: solo cambias coordenadas.
"""

import pdfplumber
import json
import os
from pdf2image import convert_from_path
from PIL import Image, ImageDraw
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
from PIL import ImageTk


# CAMPOS PREDEFINIDOS - Modifica esto según tus necesidades
CAMPOS_PREDEFINIDOS = [
    {"nombre": "num-factura", "tipo": "texto"},
    {"nombre": "fecha-factura", "tipo": "fecha"},
    {"nombre": "base", "tipo": "numerico"},
    {"nombre": "iva", "tipo": "numerico"},
    {"nombre": "total", "tipo": "numerico"},
]


class EditorPlantillas:
    def __init__(self, pdf_path, plantilla_existente=None):
        self.pdf_path = pdf_path
        self.imagen = None
        self.imagen_original = None
        self.campos = {}  # {nombre_campo: coordenadas} o None si no está capturado
        self.seleccion_actual = None
        self.punto_inicio = None
        self.plantilla_cargada = plantilla_existente

        # Inicializar campos
        for campo_def in CAMPOS_PREDEFINIDOS:
            self.campos[campo_def['nombre']] = None

        # Si hay plantilla cargada, cargar coordenadas existentes
        if plantilla_existente and 'campos' in plantilla_existente:
            for campo in plantilla_existente['campos']:
                if campo['nombre'] in self.campos:
                    self.campos[campo['nombre']] = campo['coordenadas']

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
        window_width = min(1400, screen_width - 100)
        window_height = min(900, screen_height - 100)
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Panel derecho
        frame_botones = tk.Frame(self.root, bg="gray90", padx=10)
        frame_botones.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Label(frame_botones, text="EDITOR DE PLANTILLAS", font=("Arial", 12, "bold"),
                bg="gray90", pady=10).pack(side=tk.TOP)

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
        imagenes = convert_from_path(self.pdf_path, dpi=150)
        self.imagen_original = imagenes[0]
        self.imagen = self.imagen_original.copy()

        # Calcular escala
        self.escala_x = self.imagen.width / self.pdf_width
        self.escala_y = self.imagen.height / self.pdf_height

        # Redimensionar si es muy grande
        max_width = 1200
        max_height = 900
        if self.imagen.width > max_width or self.imagen.height > max_height:
            ratio = min(max_width / self.imagen.width, max_height / self.imagen.height)
            new_width = int(self.imagen.width * ratio)
            new_height = int(self.imagen.height * ratio)
            self.imagen = self.imagen.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.imagen_original = self.imagen_original.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.escala_x *= ratio
            self.escala_y *= ratio

        self.redibujar_campos()

    def mostrar_imagen(self):
        """Muestra la imagen en el canvas."""
        self.photo = ImageTk.PhotoImage(self.imagen)
        self.canvas.config(width=self.imagen.width, height=self.imagen.height,
                          scrollregion=(0, 0, self.imagen.width, self.imagen.height))
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

    def actualizar_lista_campos(self):
        """Actualiza la lista de campos con botones."""
        # Limpiar frame
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        for i, campo_def in enumerate(CAMPOS_PREDEFINIDOS):
            nombre = campo_def['nombre']
            tipo = campo_def['tipo']
            tiene_coords = self.campos[nombre] is not None

            # Frame para cada campo
            frame_campo = tk.Frame(self.scrollable_frame, bg="white", pady=2)
            frame_campo.pack(fill=tk.X, padx=5, pady=2)

            # Color según estado
            if tiene_coords:
                color_fondo = "#228B22"  # Verde oscuro
                color_texto = "white"
                texto_btn = "✓ EDITAR"
                color_btn = "orange"
            else:
                color_fondo = "#DC143C"  # Rojo crimson
                color_texto = "white"
                texto_btn = "+ CAPTURAR"
                color_btn = "blue"

            # Label del campo
            label = tk.Label(frame_campo, text=f"{i+1}. {nombre}\n({tipo})",
                           bg=color_fondo, fg=color_texto, font=("Arial", 9, "bold"),
                           width=20, anchor="w", padx=5)
            label.pack(side=tk.LEFT, fill=tk.X, expand=True)

            # Botón para capturar/editar
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

        # Guardar coordenadas
        self.campos[self.campo_seleccionado] = [pdf_x0, pdf_top, pdf_x1, pdf_bottom]

        print(f"✓ Campo actualizado: {self.campo_seleccionado} -> {self.campos[self.campo_seleccionado]}")

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
        """Redibuja todos los campos capturados."""
        self.imagen = self.imagen_original.copy()
        draw = ImageDraw.Draw(self.imagen)

        for i, campo_def in enumerate(CAMPOS_PREDEFINIDOS, 1):
            nombre = campo_def['nombre']
            coords = self.campos[nombre]

            if coords:
                # Convertir coordenadas PDF a imagen
                ix0 = int(coords[0] * self.escala_x)
                iy0 = int(coords[1] * self.escala_y)
                ix1 = int(coords[2] * self.escala_x)
                iy1 = int(coords[3] * self.escala_y)

                # Dibujar rectángulo
                draw.rectangle([ix0, iy0, ix1, iy1], outline="green", width=3)

                # Dibujar etiqueta
                draw.text((ix0 + 5, iy0 + 5), f"{i}. {nombre}", fill="green")

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

        # Verificar que todos los campos estén capturados
        faltantes = [nombre for nombre, coords in self.campos.items() if coords is None]

        if faltantes:
            print(f"Faltan campos: {faltantes}")
            if not messagebox.askyesno("Campos incompletos",
                                      f"Faltan campos:\n" + "\n".join(f"- {c}" for c in faltantes) +
                                      "\n\n¿Guardar de todos modos?"):
                print("Guardado cancelado por usuario")
                return

        # Pedir información si es nueva
        if self.plantilla_cargada:
            proveedor_id = self.plantilla_cargada.get('proveedor_id', '')
            nombre_proveedor = self.plantilla_cargada.get('nombre_proveedor', '')
            print(f"Editando plantilla existente: {proveedor_id}")
            nombre_archivo = simpledialog.askstring("Guardar",
                                                 "Nombre del archivo (sin .json):",
                                                 initialvalue=proveedor_id,
                                                 parent=self.root)
        else:
            print("Creando plantilla nueva")
            nombre_archivo = simpledialog.askstring("Nombre de Plantilla",
                                                    "Nombre del archivo (sin .json):",
                                                    parent=self.root)
            if not nombre_archivo:
                print("Guardado cancelado - sin nombre")
                return

            proveedor_id = simpledialog.askstring("ID Proveedor",
                                                 "ID del proveedor:",
                                                 parent=self.root)
            nombre_proveedor = simpledialog.askstring("Nombre Proveedor",
                                                      "Nombre del proveedor:",
                                                      parent=self.root)

        if not nombre_archivo:
            print("Guardado cancelado - sin nombre de archivo")
            return

        print(f"Nombre archivo: {nombre_archivo}")
        print(f"Proveedor ID: {proveedor_id}")
        print(f"Nombre proveedor: {nombre_proveedor}")

        # Crear plantilla
        campos_lista = []
        for campo_def in CAMPOS_PREDEFINIDOS:
            nombre = campo_def['nombre']
            coords = self.campos[nombre]
            if coords:  # Solo incluir campos con coordenadas
                campos_lista.append({
                    "nombre": nombre,
                    "coordenadas": coords,
                    "tipo": campo_def['tipo']
                })

        print(f"Campos a guardar: {len(campos_lista)}")

        plantilla = {
            "proveedor_id": proveedor_id or "PROV_001",
            "nombre_proveedor": nombre_proveedor or "Proveedor",
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
                return

    pdf_path = input("\nRuta del PDF: ").strip()

    if not os.path.exists(pdf_path):
        print(f"Error: No se encontró {pdf_path}")
        return

    try:
        app = EditorPlantillas(pdf_path, plantilla_existente)
        app.ejecutar()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
