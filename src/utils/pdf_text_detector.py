"""
Utilidad para detectar si un PDF tiene texto extraíble.
"""

from typing import Optional
import pdfplumber


def tiene_texto_extraible(pdf_page, umbral_palabras: int = 5) -> bool:
    """
    Detecta si una página PDF tiene texto extraíble.

    Args:
        pdf_page: Página de pdfplumber
        umbral_palabras: Número mínimo de palabras para considerar que tiene texto

    Returns:
        True si la página tiene texto extraíble, False si es imagen escaneada
    """
    try:
        palabras = pdf_page.extract_words()
        return len(palabras) >= umbral_palabras
    except Exception:
        return False


def detectar_paginas_sin_texto(pdf_path: str) -> list:
    """
    Detecta qué páginas de un PDF no tienen texto extraíble.

    Args:
        pdf_path: Ruta al archivo PDF

    Returns:
        Lista de números de página (1-indexed) que no tienen texto
    """
    paginas_sin_texto = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, pagina in enumerate(pdf.pages):
                if not tiene_texto_extraible(pagina):
                    paginas_sin_texto.append(i + 1)  # 1-indexed
    except Exception as e:
        print(f"Error detectando páginas sin texto: {e}")

    return paginas_sin_texto


def diagnosticar_pdf(pdf_path: str) -> dict:
    """
    Diagnóstico completo de un PDF.

    Args:
        pdf_path: Ruta al archivo PDF

    Returns:
        Diccionario con información del PDF:
        - tiene_texto: bool
        - num_paginas: int
        - paginas_con_texto: list
        - paginas_sin_texto: list
        - porcentaje_texto: float
    """
    resultado = {
        'tiene_texto': False,
        'num_paginas': 0,
        'paginas_con_texto': [],
        'paginas_sin_texto': [],
        'porcentaje_texto': 0.0
    }

    try:
        with pdfplumber.open(pdf_path) as pdf:
            resultado['num_paginas'] = len(pdf.pages)

            for i, pagina in enumerate(pdf.pages):
                num_pagina = i + 1
                if tiene_texto_extraible(pagina):
                    resultado['paginas_con_texto'].append(num_pagina)
                else:
                    resultado['paginas_sin_texto'].append(num_pagina)

            resultado['tiene_texto'] = len(resultado['paginas_con_texto']) > 0

            if resultado['num_paginas'] > 0:
                resultado['porcentaje_texto'] = (
                    len(resultado['paginas_con_texto']) / resultado['num_paginas'] * 100
                )

    except Exception as e:
        print(f"Error diagnosticando PDF: {e}")

    return resultado
