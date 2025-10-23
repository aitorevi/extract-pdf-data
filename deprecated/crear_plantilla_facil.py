"""
Herramienta FÁCIL para crear plantillas visualmente.
Convierte el PDF a imagen y permite seleccionar zonas con el mouse.
"""

import pdfplumber
import json
import os
from pdf2image import convert_from_path
from PIL import Image, ImageDraw, ImageFont
import tkinter as tk
from tkinter import simpledialog, messagebox
from PIL import ImageTk


class CreadorPlantillaVisual:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.imagen = None
        self.imagen_original = None
        self.campos = []
        self.seleccion_actual = None
        self.punto_inicio = None

        # Obtener dimensiones del PDF
        with pdfplumber.open(pdf_path) as pdf:
            self.pdf_width = pdf.pages[0].width
            self.pdf_height = pdf.pages[0].height

        # Crear ventana
        self.root = tk.Tk()
        self.root.title("Creador de Plantilla - Haz clic y arrastra para seleccionar campos")

        # Configurar geometría de ventana
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = min(1400, screen_width - 100)
        window_height = min(900, screen_height - 100)
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Botones - A LA DERECHA
        frame_botones = tk.Frame(self.root, bg="gray90", padx=10)
        frame_botones.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Label(frame_botones, text="ACCIONES", font=("Arial", 12, "bold"),
                bg="gray90", pady=10).pack(side=tk.TOP)

        tk.Button(frame_botones, text="📂 CARGAR\nPLANTILLA", command=self.cargar_plantilla_existente,
                 bg="blue", fg="white", font=("Arial", 11, "bold"),
                 width=15, height=2).pack(side=tk.TOP, pady=5)

        tk.Button(frame_botones, text="✓ GUARDAR\nPLANTILLA", command=self.guardar_plantilla,
                 bg="green", fg="white", font=("Arial", 12, "bold"),
                 width=15, height=3).pack(side=tk.TOP, pady=10)

        tk.Button(frame_botones, text="🗑️ ELIMINAR\nÚLTIMO CAMPO", command=self.eliminar_ultimo_campo,
                 bg="purple", fg="white", font=("Arial", 11, "bold"),
                 width=15, height=2).pack(side=tk.TOP, pady=5)

        tk.Button(frame_botones, text="🎯 ELIMINAR\nCAMPO #", command=self.eliminar_campo_especifico,
                 bg="darkviolet", fg="white", font=("Arial", 11, "bold"),
                 width=15, height=2).pack(side=tk.TOP, pady=5)

        tk.Button(frame_botones, text="↻ REINICIAR", command=self.reiniciar,
                 bg="orange", fg="white", font=("Arial", 11, "bold"),
                 width=15, height=2).pack(side=tk.TOP, pady=5)

        tk.Button(frame_botones, text="✕ SALIR", command=self.root.quit,
                 bg="red", fg="white", font=("Arial", 11, "bold"),
                 width=15, height=2).pack(side=tk.TOP, pady=5)

        # Separador visual
        tk.Label(frame_botones, text="", bg="gray90", height=2).pack(side=tk.TOP)

        # Lista de campos capturados
        tk.Label(frame_botones, text="CAMPOS:", font=("Arial", 10, "bold"),
                bg="gray90").pack(side=tk.TOP)

        self.lista_campos = tk.Text(frame_botones, width=20, height=20,
                                    font=("Arial", 9), wrap=tk.WORD)
        self.lista_campos.pack(side=tk.TOP, pady=5)

        # Frame para canvas con scroll
        frame_canvas = tk.Frame(self.root)
        frame_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Canvas para la imagen con scrollbars
        scrollbar_y = tk.Scrollbar(frame_canvas, orient=tk.VERTICAL)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        scrollbar_x = tk.Scrollbar(frame_canvas, orient=tk.HORIZONTAL)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.canvas = tk.Canvas(frame_canvas, cursor="cross",
                               yscrollcommand=scrollbar_y.set,
                               xscrollcommand=scrollbar_x.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar_y.config(command=self.canvas.yview)
        scrollbar_x.config(command=self.canvas.xview)

        # Eventos del mouse
        self.canvas.bind("<ButtonPress-1>", self.al_presionar)
        self.canvas.bind("<B1-Motion>", self.al_arrastrar)
        self.canvas.bind("<ButtonRelease-1>", self.al_soltar)

    def cargar_imagen_pdf(self):
        """Convierte el PDF a imagen."""
        print("Convirtiendo PDF a imagen...")
        # Ruta de Poppler instalado localmente
        poppler_path = os.path.join(os.path.dirname(__file__), "poppler", "Library", "bin")
        imagenes = convert_from_path(self.pdf_path, dpi=150, poppler_path=poppler_path)
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
        self.canvas.config(width=self.imagen.width, height=self.imagen.height)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

    def al_presionar(self, event):
        """Cuando se presiona el mouse."""
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
        if not self.punto_inicio:
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

        # Pedir nombre del campo
        nombre = simpledialog.askstring("Nombre del Campo",
                                       "Ingresa el nombre del campo:\n(ej: numero_factura, fecha, total)",
                                       parent=self.root)

        if not nombre:
            if self.seleccion_actual:
                self.canvas.delete(self.seleccion_actual)
            self.punto_inicio = None
            return

        # Pedir tipo
        tipo = simpledialog.askstring("Tipo de Campo",
                                     "Tipo de campo:\n- texto\n- fecha\n- numerico",
                                     initialvalue="texto",
                                     parent=self.root)

        if tipo not in ["texto", "fecha", "numerico"]:
            tipo = "texto"

        # Guardar campo
        campo = {
            "nombre": nombre,
            "coordenadas": [pdf_x0, pdf_top, pdf_x1, pdf_bottom],
            "tipo": tipo
        }
        self.campos.append(campo)

        # Dibujar rectángulo permanente con número
        self.imagen = self.imagen_original.copy()
        draw = ImageDraw.Draw(self.imagen)

        for i, c in enumerate(self.campos, 1):
            # Convertir coordenadas PDF a imagen
            ix0 = int(c["coordenadas"][0] * self.escala_x)
            iy0 = int(c["coordenadas"][1] * self.escala_y)
            ix1 = int(c["coordenadas"][2] * self.escala_x)
            iy1 = int(c["coordenadas"][3] * self.escala_y)

            # Dibujar rectángulo
            draw.rectangle([ix0, iy0, ix1, iy1], outline="green", width=3)

            # Dibujar etiqueta
            draw.text((ix0 + 5, iy0 + 5), f"{i}. {c['nombre']}", fill="green")

        self.mostrar_imagen()

        # Actualizar lista de campos
        self.lista_campos.delete(1.0, tk.END)
        for i, c in enumerate(self.campos, 1):
            self.lista_campos.insert(tk.END, f"{i}. {c['nombre']}\n   ({c['tipo']})\n\n")

        print(f"✓ Campo agregado: {nombre} -> {campo['coordenadas']}")

        self.seleccion_actual = None
        self.punto_inicio = None

    def cargar_plantilla_existente(self):
        """Carga una plantilla JSON existente para editarla."""
        from tkinter import filedialog

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

            # Validar que tenga la estructura correcta
            if 'campos' not in plantilla:
                messagebox.showerror("Error", "Plantilla inválida: no contiene 'campos'")
                return

            # Cargar campos
            self.campos = plantilla['campos']

            # Redibujar imagen con los campos
            self.imagen = self.imagen_original.copy()
            draw = ImageDraw.Draw(self.imagen)

            for i, c in enumerate(self.campos, 1):
                # Convertir coordenadas PDF a imagen
                ix0 = int(c["coordenadas"][0] * self.escala_x)
                iy0 = int(c["coordenadas"][1] * self.escala_y)
                ix1 = int(c["coordenadas"][2] * self.escala_x)
                iy1 = int(c["coordenadas"][3] * self.escala_y)

                # Dibujar rectángulo
                draw.rectangle([ix0, iy0, ix1, iy1], outline="green", width=3)

                # Dibujar etiqueta
                draw.text((ix0 + 5, iy0 + 5), f"{i}. {c['nombre']}", fill="green")

            self.mostrar_imagen()

            # Actualizar lista
            self.lista_campos.delete(1.0, tk.END)
            for i, c in enumerate(self.campos, 1):
                self.lista_campos.insert(tk.END, f"{i}. {c['nombre']}\n   ({c['tipo']})\n\n")

            messagebox.showinfo("Plantilla cargada",
                              f"✓ Plantilla cargada exitosamente\n\n"
                              f"Archivo: {os.path.basename(archivo)}\n"
                              f"Campos: {len(self.campos)}\n\n"
                              f"Puedes agregar más campos o guardar los cambios.")

            print(f"✓ Plantilla cargada: {archivo}")
            print(f"✓ Campos cargados: {len(self.campos)}")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la plantilla:\n{e}")
            print(f"Error cargando plantilla: {e}")

    def redibujar_campos(self):
        """Redibuja todos los campos en la imagen."""
        self.imagen = self.imagen_original.copy()
        draw = ImageDraw.Draw(self.imagen)

        for i, c in enumerate(self.campos, 1):
            # Convertir coordenadas PDF a imagen
            ix0 = int(c["coordenadas"][0] * self.escala_x)
            iy0 = int(c["coordenadas"][1] * self.escala_y)
            ix1 = int(c["coordenadas"][2] * self.escala_x)
            iy1 = int(c["coordenadas"][3] * self.escala_y)

            # Dibujar rectángulo
            draw.rectangle([ix0, iy0, ix1, iy1], outline="green", width=3)

            # Dibujar etiqueta
            draw.text((ix0 + 5, iy0 + 5), f"{i}. {c['nombre']}", fill="green")

        self.mostrar_imagen()

        # Actualizar lista
        self.lista_campos.delete(1.0, tk.END)
        for i, c in enumerate(self.campos, 1):
            self.lista_campos.insert(tk.END, f"{i}. {c['nombre']}\n   ({c['tipo']})\n\n")

    def eliminar_ultimo_campo(self):
        """Elimina el último campo agregado."""
        if not self.campos:
            messagebox.showwarning("Sin campos", "No hay campos para eliminar")
            return

        campo_eliminado = self.campos.pop()
        self.redibujar_campos()

        print(f"✓ Campo eliminado: {campo_eliminado['nombre']}")
        messagebox.showinfo("Campo eliminado", f"Campo '{campo_eliminado['nombre']}' eliminado")

    def eliminar_campo_especifico(self):
        """Elimina un campo específico por número."""
        if not self.campos:
            messagebox.showwarning("Sin campos", "No hay campos para eliminar")
            return

        # Mostrar lista de campos
        lista = "\n".join([f"{i}. {c['nombre']} ({c['tipo']})" for i, c in enumerate(self.campos, 1)])

        numero = simpledialog.askinteger(
            "Eliminar Campo",
            f"Campos disponibles:\n\n{lista}\n\nIngresa el número del campo a eliminar:",
            minvalue=1,
            maxvalue=len(self.campos),
            parent=self.root
        )

        if numero is None:
            return

        # Eliminar campo
        campo_eliminado = self.campos.pop(numero - 1)
        self.redibujar_campos()

        print(f"✓ Campo #{numero} eliminado: {campo_eliminado['nombre']}")
        messagebox.showinfo("Campo eliminado", f"Campo #{numero} '{campo_eliminado['nombre']}' eliminado")

    def reiniciar(self):
        """Reinicia la selección."""
        if messagebox.askyesno("Reiniciar", "¿Borrar todos los campos y empezar de nuevo?"):
            self.campos = []
            self.imagen = self.imagen_original.copy()
            self.mostrar_imagen()
            self.lista_campos.delete(1.0, tk.END)
            print("Campos reiniciados")

    def guardar_plantilla(self):
        """Guarda la plantilla en JSON."""
        if not self.campos:
            messagebox.showwarning("Sin campos", "No has seleccionado ningún campo")
            return

        # Pedir información de la plantilla
        nombre_plantilla = simpledialog.askstring("Nombre de Plantilla",
                                                  "Nombre del archivo (sin .json):",
                                                  parent=self.root)
        if not nombre_plantilla:
            return

        proveedor_id = simpledialog.askstring("ID Proveedor",
                                             "ID del proveedor (ej: B05529656):",
                                             parent=self.root)

        nombre_proveedor = simpledialog.askstring("Nombre Proveedor",
                                                  "Nombre del proveedor:",
                                                  parent=self.root)

        # Crear plantilla
        plantilla = {
            "proveedor_id": proveedor_id or "PROV_001",
            "nombre_proveedor": nombre_proveedor or "Proveedor",
            "pdf_referencia": self.pdf_path,
            "campos": self.campos
        }

        # Guardar
        os.makedirs("plantillas", exist_ok=True)
        ruta = f"plantillas/{nombre_plantilla}.json"

        with open(ruta, 'w', encoding='utf-8') as f:
            json.dump(plantilla, f, ensure_ascii=False, indent=4)

        messagebox.showinfo("Guardado", f"✓ Plantilla guardada en:\n{ruta}\n\n"
                                       f"Campos: {len(self.campos)}")
        print(f"\n✓ Plantilla guardada: {ruta}")
        print(f"✓ Total campos: {len(self.campos)}")

    def ejecutar(self):
        """Ejecuta la aplicación."""
        self.cargar_imagen_pdf()
        self.root.mainloop()


def main():
    print("="*60)
    print("  CREADOR DE PLANTILLAS VISUAL - VERSIÓN FÁCIL")
    print("="*60)

    pdf_path = input("\nRuta del PDF: ").strip()

    if not os.path.exists(pdf_path):
        print(f"Error: No se encontró {pdf_path}")
        return

    try:
        app = CreadorPlantillaVisual(pdf_path)
        app.ejecutar()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
