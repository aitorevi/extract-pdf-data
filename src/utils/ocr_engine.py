"""
Motor OCR para extraer texto de PDFs escaneados usando Tesseract.
"""

import os
from typing import Optional, Tuple, List, Dict
from pathlib import Path
import pytesseract
from pdf2image import convert_from_path
from PIL import Image


class OCREngine:
    """Motor OCR para extraer texto de PDFs escaneados."""

    def __init__(self, idioma: str = 'spa', tesseract_path: Optional[str] = None):
        """
        Inicializa el motor OCR.

        Args:
            idioma: Código de idioma para Tesseract (ej: 'spa' para español, 'eng' para inglés)
            tesseract_path: Ruta al ejecutable de Tesseract (opcional)
        """
        self.idioma = idioma
        self.tesseract_cmd = tesseract_path or self._detectar_tesseract_path()

        if self.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd

    def _detectar_tesseract_path(self) -> Optional[str]:
        """
        Intenta detectar automáticamente la ruta de Tesseract.

        Returns:
            Ruta al ejecutable de Tesseract o None si no se encuentra
        """
        # Rutas comunes en Windows
        rutas_windows = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            r'C:\Tesseract-OCR\tesseract.exe',
        ]

        for ruta in rutas_windows:
            if os.path.exists(ruta):
                return ruta

        # En Linux/Mac, tesseract suele estar en PATH
        return None

    def _detectar_poppler_path(self) -> Optional[str]:
        """
        Intenta detectar automáticamente la ruta de poppler.

        Returns:
            Ruta al directorio bin de poppler o None si no se encuentra
        """
        # Primero buscar en el proyecto
        proyecto_poppler = os.path.join(os.getcwd(), 'poppler', 'Library', 'bin')
        if os.path.exists(proyecto_poppler):
            return proyecto_poppler

        # Rutas comunes en Windows
        rutas_windows = [
            r'C:\Program Files\poppler\Library\bin',
            r'C:\poppler\Library\bin',
        ]

        for ruta in rutas_windows:
            if os.path.exists(ruta):
                return ruta

        # En Linux/Mac, poppler suele estar en PATH
        return None

    def is_available(self) -> bool:
        """
        Verifica si Tesseract está disponible.

        Returns:
            True si Tesseract está instalado y funcional
        """
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def pdf_a_imagen(self, pdf_path: str, pagina_num: int = 1, dpi: int = 300) -> Image.Image:
        """
        Convierte una página PDF a imagen.

        Args:
            pdf_path: Ruta al archivo PDF
            pagina_num: Número de página (1-indexed)
            dpi: Resolución de la imagen (mayor = mejor calidad pero más lento)

        Returns:
            Objeto Image de PIL
        """
        # Detectar ruta de poppler en el proyecto
        poppler_path = self._detectar_poppler_path()

        imagenes = convert_from_path(
            pdf_path,
            dpi=dpi,
            first_page=pagina_num,
            last_page=pagina_num,
            poppler_path=poppler_path
        )
        return imagenes[0] if imagenes else None

    def extraer_texto_completo(self, pdf_path: str, pagina_num: int = 1) -> str:
        """
        Extrae todo el texto de una página PDF usando OCR.

        Args:
            pdf_path: Ruta al archivo PDF
            pagina_num: Número de página (1-indexed)

        Returns:
            Texto extraído
        """
        try:
            imagen = self.pdf_a_imagen(pdf_path, pagina_num)
            if imagen is None:
                return ""

            texto = pytesseract.image_to_string(imagen, lang=self.idioma)
            return texto.strip()

        except Exception as e:
            print(f"Error en OCR: {e}")
            return ""

    def extraer_texto_con_coordenadas(self, pdf_path: str, pagina_num: int = 1) -> List[Dict]:
        """
        Extrae texto con información de coordenadas (bounding boxes).

        Args:
            pdf_path: Ruta al archivo PDF
            pagina_num: Número de página (1-indexed)

        Returns:
            Lista de diccionarios con {'text': str, 'x0': float, 'top': float, 'x1': float, 'bottom': float}
        """
        try:
            imagen = self.pdf_a_imagen(pdf_path, pagina_num)
            if imagen is None:
                return []

            # Obtener datos con coordenadas
            data = pytesseract.image_to_data(imagen, lang=self.idioma, output_type=pytesseract.Output.DICT)

            palabras = []
            n_boxes = len(data['text'])

            for i in range(n_boxes):
                texto = data['text'][i].strip()
                if texto:  # Solo palabras no vacías
                    # Convertir coordenadas de imagen a coordenadas PDF (aproximado)
                    # Tesseract devuelve: left, top, width, height
                    x0 = data['left'][i]
                    y0 = data['top'][i]
                    x1 = x0 + data['width'][i]
                    y1 = y0 + data['height'][i]

                    palabras.append({
                        'text': texto,
                        'x0': float(x0),
                        'top': float(y0),
                        'x1': float(x1),
                        'bottom': float(y1),
                        'conf': data['conf'][i]  # Confianza del OCR (0-100)
                    })

            return palabras

        except Exception as e:
            print(f"Error extrayendo texto con coordenadas: {e}")
            return []

    def extraer_texto_area(self, pdf_path: str, bbox: Tuple[float, float, float, float],
                          pagina_num: int = 1, dpi: int = 300) -> str:
        """
        Extrae texto de un área específica del PDF usando OCR.

        Args:
            pdf_path: Ruta al archivo PDF
            bbox: Tupla (x0, top, x1, bottom) con coordenadas del área en puntos PDF (72 DPI)
            pagina_num: Número de página (1-indexed)
            dpi: DPI usado para generar la imagen (default: 300)

        Returns:
            Texto extraído del área
        """
        try:
            # Convertir PDF a imagen
            imagen = self.pdf_a_imagen(pdf_path, pagina_num, dpi=dpi)
            if imagen is None:
                return ""

            # Escalar coordenadas de PDF (72 DPI) a imagen (dpi)
            # Factor de escala: dpi_imagen / 72
            escala = dpi / 72.0
            x0, top, x1, bottom = bbox
            x0_img = int(x0 * escala)
            top_img = int(top * escala)
            x1_img = int(x1 * escala)
            bottom_img = int(bottom * escala)

            # Recortar área (PIL usa: left, top, right, bottom)
            area_recortada = imagen.crop((x0_img, top_img, x1_img, bottom_img))

            # Aplicar OCR solo al área
            texto = pytesseract.image_to_string(area_recortada, lang=self.idioma)
            return texto.strip()

        except Exception as e:
            print(f"Error extrayendo texto de área: {e}")
            return ""

    def preprocessing_imagen(self, imagen: Image.Image, escala_grises: bool = True,
                            binarizacion: bool = False) -> Image.Image:
        """
        Preprocesa una imagen para mejorar el OCR.

        Args:
            imagen: Imagen PIL
            escala_grises: Convertir a escala de grises
            binarizacion: Aplicar binarización (blanco y negro)

        Returns:
            Imagen procesada
        """
        img_procesada = imagen

        if escala_grises:
            img_procesada = img_procesada.convert('L')

        if binarizacion:
            # Umbral simple para binarizar
            img_procesada = img_procesada.point(lambda x: 0 if x < 128 else 255, '1')

        return img_procesada


def diagnosticar_ocr(pdf_path: str, pagina_num: int = 1) -> Dict:
    """
    Diagnóstico de OCR para un PDF.

    Args:
        pdf_path: Ruta al archivo PDF
        pagina_num: Número de página a diagnosticar

    Returns:
        Diccionario con resultados del diagnóstico
    """
    ocr = OCREngine()

    resultado = {
        'tesseract_disponible': ocr.is_available(),
        'tesseract_path': ocr.tesseract_cmd,
        'texto_extraido': '',
        'num_palabras': 0,
        'confianza_promedio': 0.0
    }

    if not resultado['tesseract_disponible']:
        resultado['error'] = 'Tesseract no está instalado o no se encuentra'
        return resultado

    try:
        # Extraer texto completo
        texto = ocr.extraer_texto_completo(pdf_path, pagina_num)
        resultado['texto_extraido'] = texto[:500]  # Primeros 500 caracteres
        resultado['num_palabras'] = len(texto.split())

        # Obtener palabras con confianza
        palabras = ocr.extraer_texto_con_coordenadas(pdf_path, pagina_num)
        if palabras:
            confianzas = [p['conf'] for p in palabras if p['conf'] > 0]
            if confianzas:
                resultado['confianza_promedio'] = sum(confianzas) / len(confianzas)

    except Exception as e:
        resultado['error'] = str(e)

    return resultado
