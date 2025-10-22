"""
Herramienta para extraer coordenadas de campos en facturas PDF usando OpenCV.
Permite seleccionar áreas interactivamente y convierte coordenadas píxeles a coordenadas PDF.
"""

import cv2
import os
import json
from pdf2image import convert_from_path


class CoordinateExtractor:
    def __init__(self, imagen_path, dpi=300):
        """
        Inicializa el extractor de coordenadas.

        Args:
            imagen_path (str): Ruta a la imagen de la factura
            dpi (int): DPI usado para convertir PDF a imagen (default: 300)
        """
        self.imagen_path = imagen_path
        self.dpi = dpi
        self.coordenadas_seleccionadas = []
        self.campos_extraidos = []
        self.img = None
        self.img_original = None

    def cargar_imagen(self):
        """Carga la imagen de la factura."""
        self.img = cv2.imread(self.imagen_path)
        if self.img is None:
            raise FileNotFoundError(f"No se pudo cargar la imagen: {self.imagen_path}")
        self.img_original = self.img.copy()
        return True

    def convertir_pdf_a_imagen(self, pdf_path, output_path=None, pagina=0):
        """
        Convierte la primera página de un PDF a imagen.

        Args:
            pdf_path (str): Ruta al archivo PDF
            output_path (str): Ruta donde guardar la imagen (opcional)
            pagina (int): Número de página a convertir (default: 0)
        """
        try:
            # Convertir PDF a imagen con DPI especificado
            imagenes = convert_from_path(pdf_path, dpi=self.dpi, first_page=pagina+1, last_page=pagina+1)

            if not imagenes:
                raise Exception("No se pudo convertir el PDF a imagen")

            imagen = imagenes[0]

            # Guardar imagen si se especifica ruta de salida
            if output_path is None:
                nombre_base = os.path.splitext(os.path.basename(pdf_path))[0]
                output_path = f"imagenes_muestra/{nombre_base}_page{pagina}_{self.dpi}dpi.png"

            imagen.save(output_path, 'PNG')
            self.imagen_path = output_path
            print(f"PDF convertido a imagen: {output_path}")
            return output_path

        except Exception as e:
            print(f"Error convirtiendo PDF a imagen: {e}")
            return None

    def obtener_coordenadas_callback(self, event, x, y, flags, param):
        """Función callback para capturar eventos del ratón."""
        if event == cv2.EVENT_LBUTTONDOWN:
            # Inicio del arrastre (esquina superior izquierda)
            self.coordenadas_seleccionadas = [(x, y)]

        elif event == cv2.EVENT_LBUTTONUP:
            # Fin del arrastre (esquina inferior derecha)
            if len(self.coordenadas_seleccionadas) == 1:
                self.coordenadas_seleccionadas.append((x, y))
                self.procesar_seleccion()

    def procesar_seleccion(self):
        """Procesa la selección realizada y muestra las coordenadas."""
        if len(self.coordenadas_seleccionadas) == 2:
            x1, y1 = self.coordenadas_seleccionadas[0]
            x2, y2 = self.coordenadas_seleccionadas[1]

            # Normalizar coordenadas (superior izquierda, inferior derecha)
            x_min, y_min = min(x1, x2), min(y1, y2)
            x_max, y_max = max(x1, x2), max(y1, y2)

            # Dibujar rectángulo verde en la imagen
            cv2.rectangle(self.img, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
            cv2.imshow("Selector de Coordenadas", self.img)

            # Convertir coordenadas píxeles a coordenadas PDF
            coordenadas_pdf = self.convertir_pixeles_a_pdf(x_min, y_min, x_max, y_max)

            print(f"\n--- COORDENADAS EXTRAÍDAS ---")
            print(f"Píxeles (x_min, y_min, x_max, y_max): [{x_min}, {y_min}, {x_max}, {y_max}]")
            print(f"PDF (x1, y1, x2, y2): {coordenadas_pdf}")

            # Solicitar información del campo
            nombre_campo = input("Nombre del campo: ").strip()
            tipo_campo = input("Tipo (texto/fecha/numerico): ").strip().lower()

            if nombre_campo:
                campo = {
                    "nombre": nombre_campo,
                    "coordenadas": coordenadas_pdf,
                    "tipo": tipo_campo if tipo_campo in ["texto", "fecha", "numerico"] else "texto",
                    "coordenadas_pixeles": [x_min, y_min, x_max, y_max]
                }
                self.campos_extraidos.append(campo)
                print(f"Campo '{nombre_campo}' agregado exitosamente.")

            # Limpiar selección para la siguiente
            self.coordenadas_seleccionadas = []

    def convertir_pixeles_a_pdf(self, x_min, y_min, x_max, y_max):
        """
        Convierte coordenadas en píxeles a coordenadas PDF.

        Args:
            x_min, y_min, x_max, y_max: Coordenadas en píxeles

        Returns:
            list: Coordenadas en formato PDF [x1, y1, x2, y2]
        """
        # Factor de escalado de píxeles a puntos PDF
        factor_escala = 72.0 / self.dpi

        # Convertir coordenadas X (igual dirección)
        x1_pdf = x_min * factor_escala
        x2_pdf = x_max * factor_escala

        # Convertir coordenadas Y (invertir origen: píxel top-left vs PDF bottom-left)
        altura_imagen = self.img.shape[0]
        y1_pdf = (altura_imagen - y_max) * factor_escala  # Bottom de la selección
        y2_pdf = (altura_imagen - y_min) * factor_escala  # Top de la selección

        return [round(x1_pdf, 1), round(y1_pdf, 1), round(x2_pdf, 1), round(y2_pdf, 1)]

    def ejecutar_seleccion_interactiva(self):
        """Ejecuta el proceso interactivo de selección de coordenadas."""
        if not self.cargar_imagen():
            return False

        cv2.namedWindow('Selector de Coordenadas', cv2.WINDOW_NORMAL)
        cv2.setMouseCallback('Selector de Coordenadas', self.obtener_coordenadas_callback)

        print("\n=== EXTRACTOR DE COORDENADAS ===")
        print("INSTRUCCIONES:")
        print("1. Clic y arrastra para seleccionar cada campo")
        print("2. Ingresa el nombre y tipo del campo en la consola")
        print("3. Presiona 'q' o ESC para terminar y guardar")
        print("4. Presiona 'r' para reiniciar la imagen")
        print("5. Presiona 's' para guardar plantilla actual")
        print("\nIMPORTANTE: Asegúrate de que la ventana de imagen esté activa (haz clic en ella)")
        print("-" * 40)

        while True:
            cv2.imshow('Selector de Coordenadas', self.img)
            key = cv2.waitKey(100) & 0xFF  # Aumentado de 1 a 100ms para mejor detección

            if key != 255:  # Si se presionó alguna tecla
                print(f"Tecla presionada: {key} ('{chr(key) if 32 <= key <= 126 else '?'}')")

            if key == ord('q') or key == 27:  # 'q' o ESC
                print("Saliendo del modo de selección...")
                break
            elif key == ord('r'):
                # Reiniciar imagen
                self.img = self.img_original.copy()
                cv2.imshow('Selector de Coordenadas', self.img)
                print("Imagen reiniciada.")
            elif key == ord('s'):
                # Guardar plantilla actual
                self.guardar_plantilla_temporal()

        cv2.destroyAllWindows()
        return True

    def guardar_plantilla_temporal(self):
        """Guarda una plantilla temporal con los campos extraídos hasta ahora."""
        if not self.campos_extraidos:
            print("No hay campos para guardar.")
            return

        nombre_archivo = input("Nombre del archivo de plantilla (sin .json): ").strip()
        if nombre_archivo:
            self.generar_plantilla_json(nombre_archivo)

    def generar_plantilla_json(self, nombre_plantilla):
        """
        Genera el archivo JSON de plantilla con los campos extraídos.

        Args:
            nombre_plantilla (str): Nombre del archivo (sin extensión)
        """
        if not self.campos_extraidos:
            print("No hay campos extraídos para generar la plantilla.")
            return None

        proveedor_id = input("ID del proveedor (ej. PROV_001): ").strip()
        nombre_proveedor = input("Nombre del proveedor: ").strip()

        plantilla = {
            "proveedor_id": proveedor_id or "PROV_001",
            "nombre_proveedor": nombre_proveedor or "Proveedor Ejemplo",
            "imagen_referencia": self.imagen_path,
            "dpi_imagen": self.dpi,
            "campos": self.campos_extraidos
        }

        # Guardar en directorio de plantillas
        ruta_plantilla = f"plantillas/{nombre_plantilla}.json"

        try:
            with open(ruta_plantilla, 'w', encoding='utf-8') as f:
                json.dump(plantilla, f, ensure_ascii=False, indent=4)

            print(f"\n✓ Plantilla guardada exitosamente: {ruta_plantilla}")
            print(f"✓ Campos extraídos: {len(self.campos_extraidos)}")

            return ruta_plantilla

        except Exception as e:
            print(f"Error guardando plantilla: {e}")
            return None


def main():
    """Función principal para ejecutar el extractor de coordenadas."""
    print("=== EXTRACTOR DE COORDENADAS PARA FACTURAS PDF ===\n")

    # Opciones de entrada
    print("Opciones:")
    print("1. Trabajar con imagen existente")
    print("2. Convertir PDF a imagen y trabajar con ella")

    opcion = input("Selecciona una opción (1 o 2): ").strip()

    extractor = CoordinateExtractor("", dpi=300)

    if opcion == "1":
        # Trabajar con imagen existente
        ruta_imagen = input("Ruta de la imagen: ").strip()
        if not os.path.exists(ruta_imagen):
            print(f"Error: No se encontró la imagen en {ruta_imagen}")
            return
        extractor.imagen_path = ruta_imagen

    elif opcion == "2":
        # Convertir PDF a imagen
        ruta_pdf = input("Ruta del PDF: ").strip()
        if not os.path.exists(ruta_pdf):
            print(f"Error: No se encontró el PDF en {ruta_pdf}")
            return

        pagina = input("Número de página (0 para primera): ").strip()
        pagina = int(pagina) if pagina.isdigit() else 0

        dpi = input("DPI para conversión (300 recomendado): ").strip()
        extractor.dpi = int(dpi) if dpi.isdigit() else 300

        ruta_imagen = extractor.convertir_pdf_a_imagen(ruta_pdf, pagina=pagina)
        if not ruta_imagen:
            print("Error convirtiendo PDF a imagen.")
            return
    else:
        print("Opción no válida.")
        return

    # Ejecutar selección interactiva
    if extractor.ejecutar_seleccion_interactiva():
        # Generar plantilla final
        if extractor.campos_extraidos:
            nombre_plantilla = input("\nNombre final de la plantilla: ").strip()
            if nombre_plantilla:
                extractor.generar_plantilla_json(nombre_plantilla)
        else:
            print("No se extrajeron campos.")


if __name__ == "__main__":
    main()