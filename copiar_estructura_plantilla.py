"""
Herramienta para copiar la estructura de una plantilla existente a un nuevo PDF.
Mantiene los nombres y tipos de campos, solo cambias las coordenadas.
"""

import pdfplumber
import json
import os
from pdf2image import convert_from_path
from PIL import Image, ImageDraw, ImageFont
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
from PIL import ImageTk


class CopiadorEstructuraPlantilla:
    def __init__(self, pdf_path, plantilla_base):
        self.pdf_path = pdf_path
        self.plantilla_base = plantilla_base
        self.imagen = None
        self.imagen_original = None
        self.campos_capturados = []
        self.campo_actual_index = 0
        self.seleccion_actual = None
        self.punto_inicio = None

        # Obtener dimensiones del PDF
        with pdfplumber.open(pdf_path) as pdf:
            self.pdf_width = pdf.pages[0].width
            self.pdf_height = pdf.pages[0].height

        # Crear ventana
        self.root = tk.Tk()
        self.root.title(f"Copiar Estructura - Campo {self.campo_actual_index + 1}/{len(self.plantilla_base['campos'])}")

        # Configurar geometría de ventana
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

        tk.Label(frame_botones, text="COPIAR ESTRUCTURA", font=("Arial", 12, "bold"),
                bg="gray90", pady=10).pack(side=tk.TOP)

        # Información del campo actual
        self.label_campo_actual = tk.Label(frame_botones,
                                          text="",
                                          font=("Arial", 14, "bold"),
                                          bg="lightyellow",
                                          fg="darkblue",
                                          wraplength=200,
                                          pady=10)
        self.label_campo_actual.pack(side=tk.TOP, fill=tk.X, pady=10)

        # Progreso
        self.label_progreso = tk.Label(frame_botones,
                                      text="",
                                      font=("Arial", 11),
                                      bg="lightgreen",
                                      pady=5)
        self.label_progreso.pack(side=tk.TOP, fill=tk.X, pady=5)

        # Botones
        tk.Button(frame_botones, text="↶ DESHACER\nÚLTIMO", command=self.deshacer_ultimo,
                 bg="orange", fg="white", font=("Arial", 11, "bold"),
                 width=15, height=2).pack(side=tk.TOP, pady=10)

        tk.Button(frame_botones, text="✓ GUARDAR\nPLANTILLA", command=self.guardar_plantilla,
                 bg="green", fg="white", font=("Arial", 12, "bold"),
                 width=15, height=3).pack(side=tk.TOP, pady=10)

        tk.Button(frame_botones, text="✕ CANCELAR", command=self.root.quit,
                 bg="red", fg="white", font=("Arial", 11, "bold"),
                 width=15, height=2).pack(side=tk.TOP, pady=10)

        # Lista de campos
        tk.Label(frame_botones, text="CAMPOS A CAPTURAR:", font=("Arial", 10, "bold"),
                bg="gray90", pady=5).pack(side=tk.TOP)

        self.lista_campos = tk.Text(frame_botones, width=25, height=20,
                                    font=("Arial", 9), wrap=tk.WORD)
        self.lista_campos.pack(side=tk.TOP, pady=5)

        # Mostrar lista de campos
        self.actualizar_lista_campos()

        # Frame para canvas
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

        # Actualizar label del campo actual
        self.actualizar_campo_actual()

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

        self.mostrar_imagen()

    def mostrar_imagen(self):
        """Muestra la imagen en el canvas."""
        self.photo = ImageTk.PhotoImage(self.imagen)
        self.canvas.config(width=self.imagen.width, height=self.imagen.height,
                          scrollregion=(0, 0, self.imagen.width, self.imagen.height))
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

    def actualizar_campo_actual(self):
        """Actualiza la información del campo actual."""
        if self.campo_actual_index < len(self.plantilla_base['campos']):
            campo = self.plantilla_base['campos'][self.campo_actual_index]
            self.label_campo_actual.config(
                text=f"Selecciona:\n\n{campo['nombre']}\n\n({campo['tipo']})"
            )
            self.root.title(f"Copiar Estructura - Campo {self.campo_actual_index + 1}/{len(self.plantilla_base['campos'])}")
        else:
            self.label_campo_actual.config(
                text="✓ TODOS LOS\nCAMPOS\nCAPTURADOS"
            )
            self.label_campo_actual.config(bg="lightgreen")
            self.root.title("Copiar Estructura - ¡COMPLETADO!")

        # Actualizar progreso
        self.label_progreso.config(
            text=f"Progreso: {len(self.campos_capturados)}/{len(self.plantilla_base['campos'])}"
        )

    def actualizar_lista_campos(self):
        """Actualiza la lista de campos en el panel."""
        self.lista_campos.delete(1.0, tk.END)

        for i, campo_base in enumerate(self.plantilla_base['campos']):
            if i < len(self.campos_capturados):
                # Campo ya capturado
                self.lista_campos.insert(tk.END, f"✓ {i+1}. {campo_base['nombre']}\n", "completado")
                self.lista_campos.insert(tk.END, f"   ({campo_base['tipo']})\n\n")
            elif i == self.campo_actual_index:
                # Campo actual
                self.lista_campos.insert(tk.END, f"→ {i+1}. {campo_base['nombre']}\n", "actual")
                self.lista_campos.insert(tk.END, f"   ({campo_base['tipo']})\n\n")
            else:
                # Campo pendiente
                self.lista_campos.insert(tk.END, f"  {i+1}. {campo_base['nombre']}\n")
                self.lista_campos.insert(tk.END, f"   ({campo_base['tipo']})\n\n")

        # Configurar tags de color
        self.lista_campos.tag_config("completado", foreground="green", font=("Arial", 9, "bold"))
        self.lista_campos.tag_config("actual", foreground="blue", font=("Arial", 9, "bold"))

    def al_presionar(self, event):
        """Cuando se presiona el mouse."""
        if self.campo_actual_index >= len(self.plantilla_base['campos']):
            messagebox.showinfo("Completado", "Ya capturaste todos los campos.\nHaz clic en 'Guardar Plantilla'")
            return

        self.punto_inicio = (event.x, event.y)
        if self.seleccion_actual:
            self.canvas.delete(self.seleccion_actual)

    def al_arrastrar(self, event):
        """Cuando se arrastra el mouse."""
        if self.punto_inicio:
            if self.seleccion_actual:
                self.canvas.delete(self.seleccion_actual)
            self.seleccion_actual = self.canvas.create_rectangle(
                self.punto_inicio[0], self.punto_inicio[1],
                event.x, event.y,
                outline="red", width=3
            )

    def al_soltar(self, event):
        """Cuando se suelta el mouse."""
        if not self.punto_inicio or self.campo_actual_index >= len(self.plantilla_base['campos']):
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

        # Obtener campo base
        campo_base = self.plantilla_base['campos'][self.campo_actual_index]

        # Crear nuevo campo con coordenadas actualizadas
        nuevo_campo = {
            "nombre": campo_base['nombre'],
            "coordenadas": [pdf_x0, pdf_top, pdf_x1, pdf_bottom],
            "tipo": campo_base['tipo']
        }

        self.campos_capturados.append(nuevo_campo)

        # Redibujar
        self.redibujar_campos()

        # Avanzar al siguiente campo
        self.campo_actual_index += 1
        self.actualizar_campo_actual()
        self.actualizar_lista_campos()

        print(f"✓ Campo capturado: {nuevo_campo['nombre']} -> {nuevo_campo['coordenadas']}")

        self.seleccion_actual = None
        self.punto_inicio = None

    def redibujar_campos(self):
        """Redibuja todos los campos capturados."""
        self.imagen = self.imagen_original.copy()
        draw = ImageDraw.Draw(self.imagen)

        for i, campo in enumerate(self.campos_capturados, 1):
            # Convertir coordenadas PDF a imagen
            ix0 = int(campo["coordenadas"][0] * self.escala_x)
            iy0 = int(campo["coordenadas"][1] * self.escala_y)
            ix1 = int(campo["coordenadas"][2] * self.escala_x)
            iy1 = int(campo["coordenadas"][3] * self.escala_y)

            # Dibujar rectángulo
            draw.rectangle([ix0, iy0, ix1, iy1], outline="green", width=3)

            # Dibujar etiqueta
            draw.text((ix0 + 5, iy0 + 5), f"{i}. {campo['nombre']}", fill="green")

        self.mostrar_imagen()

    def deshacer_ultimo(self):
        """Deshace la última captura."""
        if not self.campos_capturados:
            messagebox.showwarning("Sin cambios", "No hay campos para deshacer")
            return

        campo_eliminado = self.campos_capturados.pop()
        self.campo_actual_index -= 1

        self.redibujar_campos()
        self.actualizar_campo_actual()
        self.actualizar_lista_campos()

        print(f"↶ Deshecho: {campo_eliminado['nombre']}")

    def guardar_plantilla(self):
        """Guarda la nueva plantilla."""
        if len(self.campos_capturados) < len(self.plantilla_base['campos']):
            if not messagebox.askyesno("Incompleto",
                                      f"Solo has capturado {len(self.campos_capturados)} de {len(self.plantilla_base['campos'])} campos.\n\n"
                                      "¿Guardar de todos modos?"):
                return

        # Pedir información
        nombre_plantilla = simpledialog.askstring("Nombre de Plantilla",
                                                  "Nombre del archivo (sin .json):",
                                                  parent=self.root)
        if not nombre_plantilla:
            return

        proveedor_id = simpledialog.askstring("ID Proveedor",
                                             "ID del proveedor:",
                                             parent=self.root)

        nombre_proveedor = simpledialog.askstring("Nombre Proveedor",
                                                  "Nombre del proveedor:",
                                                  parent=self.root)

        # Crear plantilla
        plantilla = {
            "proveedor_id": proveedor_id or "PROV_001",
            "nombre_proveedor": nombre_proveedor or "Proveedor",
            "pdf_referencia": self.pdf_path,
            "campos": self.campos_capturados
        }

        # Guardar
        os.makedirs("plantillas", exist_ok=True)
        ruta = f"plantillas/{nombre_plantilla}.json"

        with open(ruta, 'w', encoding='utf-8') as f:
            json.dump(plantilla, f, ensure_ascii=False, indent=4)

        messagebox.showinfo("Guardado",
                          f"✓ Plantilla guardada en:\n{ruta}\n\n"
                          f"Campos: {len(self.campos_capturados)}")
        print(f"\n✓ Plantilla guardada: {ruta}")
        print(f"✓ Total campos: {len(self.campos_capturados)}")

    def ejecutar(self):
        """Ejecuta la aplicación."""
        self.cargar_imagen_pdf()
        self.root.mainloop()


def main():
    print("="*60)
    print("  COPIAR ESTRUCTURA DE PLANTILLA")
    print("="*60)

    # Seleccionar plantilla base
    print("\n1. Selecciona la plantilla BASE (con los campos que quieres copiar)")
    archivo_plantilla = filedialog.askopenfilename(
        title="Seleccionar plantilla base",
        initialdir="plantillas",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
    )

    if not archivo_plantilla:
        print("Cancelado")
        return

    try:
        with open(archivo_plantilla, 'r', encoding='utf-8') as f:
            plantilla_base = json.load(f)

        if 'campos' not in plantilla_base or not plantilla_base['campos']:
            print("Error: La plantilla no tiene campos")
            return

        print(f"\n✓ Plantilla base cargada: {os.path.basename(archivo_plantilla)}")
        print(f"✓ Campos a capturar: {len(plantilla_base['campos'])}")
        for i, campo in enumerate(plantilla_base['campos'], 1):
            print(f"   {i}. {campo['nombre']} ({campo['tipo']})")

    except Exception as e:
        print(f"Error cargando plantilla: {e}")
        return

    # Seleccionar PDF nuevo
    print("\n2. Ahora ingresa la ruta del PDF NUEVO")
    pdf_path = input("Ruta del PDF: ").strip()

    if not os.path.exists(pdf_path):
        print(f"Error: No se encontró {pdf_path}")
        return

    try:
        app = CopiadorEstructuraPlantilla(pdf_path, plantilla_base)
        app.ejecutar()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
