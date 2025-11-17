"""
Utilidad para detectar si un PDF tiene texto extraíble.
"""

from typing import Optional
import pdfplumber
import re


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


def tiene_texto_corrupto_cid(texto: str, umbral_porcentaje: float = 10.0) -> bool:
    """
    Detecta si un texto contiene códigos CID (Character ID) que indican
    fuentes embebidas sin mapeo Unicode correcto.

    Los códigos CID aparecen como: (cid:123) o similares y hacen que el texto
    sea ilegible aunque técnicamente sea "extraíble".

    Args:
        texto (str): Texto extraído del PDF
        umbral_porcentaje (float): Porcentaje mínimo de caracteres CID para
                                   considerar el texto como corrupto (default: 10%)

    Returns:
        bool: True si el texto contiene códigos CID significativos, False si es legible

    Ejemplos:
        >>> tiene_texto_corrupto_cid("(cid:24)(cid:1)(cid:23)(cid:1)(cid:21)")
        True
        >>> tiene_texto_corrupto_cid("Factura normal 12345")
        False
        >>> tiene_texto_corrupto_cid("Texto normal con un (cid:1) ocasional")
        False  # Solo 10% es CID, debajo del umbral
    """
    if not texto or len(texto.strip()) == 0:
        return False

    # Detectar patrón de códigos CID: (cid:NNN)
    patron_cid = r'\(cid:\d+\)'
    coincidencias_cid = re.findall(patron_cid, texto)

    if not coincidencias_cid:
        return False

    # Calcular porcentaje de texto que son códigos CID
    # Cada coincidencia representa un carácter corrupto
    num_caracteres_cid = len(coincidencias_cid)

    # Contar caracteres totales (excluyendo espacios)
    texto_sin_espacios = texto.replace(' ', '').replace('\n', '').replace('\t', '')
    num_caracteres_totales = len(texto_sin_espacios)

    if num_caracteres_totales == 0:
        return False

    # Calcular porcentaje
    porcentaje_cid = (num_caracteres_cid / num_caracteres_totales) * 100

    # Si más del umbral% del texto son códigos CID, considerarlo corrupto
    return porcentaje_cid >= umbral_porcentaje


def detectar_texto_corrupto_en_pagina(pdf_page, umbral_cid: float = 10.0) -> bool:
    """
    Detecta si una página PDF tiene texto corrupto (códigos CID).

    Args:
        pdf_page: Página de pdfplumber
        umbral_cid (float): Porcentaje mínimo de CID para considerar corrupto

    Returns:
        bool: True si la página tiene texto corrupto, False si es legible
    """
    try:
        texto = pdf_page.extract_text()
        if not texto:
            return False

        return tiene_texto_corrupto_cid(texto, umbral_cid)
    except Exception:
        return False
