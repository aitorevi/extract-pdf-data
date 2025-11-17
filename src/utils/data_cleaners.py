"""
Módulo de limpieza y normalización de datos extraídos de PDFs.

Este módulo proporciona funciones estáticas para limpiar y normalizar
diferentes tipos de datos: texto, fechas y números.
"""

import re
from datetime import datetime
from typing import Optional


class DataCleaner:
    """
    Clase con métodos estáticos para limpieza de datos.

    Proporciona funciones para:
    - Limpiar texto (espacios, caracteres especiales)
    - Normalizar fechas a formato DD/MM/YYYY
    - Normalizar números (formato decimal consistente)
    """

    @staticmethod
    def clean_text(texto: str) -> str:
        """
        Limpia campos de texto removiendo caracteres especiales y normalizando espacios.

        Args:
            texto: Texto a limpiar

        Returns:
            Texto limpio con espacios normalizados y sin caracteres de control

        Examples:
            >>> DataCleaner.clean_text("  texto   con   espacios  ")
            "texto con espacios"
            >>> DataCleaner.clean_text("texto\\ncon\\nsaltos")
            "texto con saltos"
        """
        if not texto:
            return ""

        # Primero normalizar espacios (múltiples espacios, tabs, newlines → espacio simple)
        texto = re.sub(r'\s+', ' ', texto)

        # Luego remover caracteres especiales problemáticos (control characters)
        # pero NO \n, \t, etc. que ya fueron convertidos a espacios
        texto = re.sub(r'[\x00-\x08\x0b-\x1f\x7f-\x9f]', '', texto)

        return texto.strip()

    @staticmethod
    def clean_invoice_number(texto: str) -> str:
        """
        Limpia números de factura removiendo todos los espacios y caracteres especiales.

        Args:
            texto: Texto que contiene un número de factura

        Returns:
            Número de factura sin espacios ni caracteres especiales

        Examples:
            >>> DataCleaner.clean_invoice_number("  FAC 123  ")
            "FAC123"
            >>> DataCleaner.clean_invoice_number("A - 2024 / 001")
            "A-2024/001"
            >>> DataCleaner.clean_invoice_number("N ° 1 2 3 4 5")
            "N°12345"
            >>> DataCleaner.clean_invoice_number(": F2025/82150")
            "F2025/82150"
        """
        if not texto:
            return ""

        # Primero limpiar caracteres de control
        texto = re.sub(r'[\x00-\x08\x0b-\x1f\x7f-\x9f]', '', texto)

        # Eliminar TODOS los espacios (antes, después e intermedios)
        texto = re.sub(r'\s+', '', texto)

        # Limpiar dos puntos al inicio (común en algunos PDFs mal formateados)
        texto = texto.lstrip(':')

        return texto.strip()

    @staticmethod
    def clean_date(texto: str) -> str:
        """
        Limpia y normaliza campos de fecha al formato DD/MM/YYYY.

        Soporta múltiples formatos de entrada:
        - DD/MM/YYYY, DD-MM-YYYY
        - YYYY/MM/DD, YYYY-MM-DD
        - DD/MM/YY, DD-MM-YY
        - Formato textual español largo: "1 de octubre de 2025"
        - Formato textual español corto: "31 jul 2025", "15 oct 2024"
        - Meses completos y abreviados (ene, feb, mar, etc.)
        - Extracción de fechas dentro de texto

        Args:
            texto: Texto que contiene una fecha

        Returns:
            Fecha en formato DD/MM/YYYY o texto original si no se reconoce

        Examples:
            >>> DataCleaner.clean_date("2024-01-15")
            "15/01/2024"
            >>> DataCleaner.clean_date("15/01/24")
            "15/01/2024"
            >>> DataCleaner.clean_date("Fecha: 15/01/2024")
            "15/01/2024"
            >>> DataCleaner.clean_date("1 de octubre de 2025")
            "01/10/2025"
            >>> DataCleaner.clean_date("31 jul 2025")
            "31/07/2025"
            >>> DataCleaner.clean_date("15 Oct 2024")
            "15/10/2024"
            >>> DataCleaner.clean_date("..3..1.. j.u.l. .2.0..2.5.....")
            "31/07/2025"
        """
        # Primero limpiar el texto
        texto = DataCleaner.clean_text(texto)

        if not texto:
            return ""

        # Diccionario de meses en español
        meses_es = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12,
            # Abreviaciones
            'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4,
            'may': 5, 'jun': 6, 'jul': 7, 'ago': 8,
            'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12,
            # Variantes comunes
            'ener': 1, 'febr': 2, 'agos': 8, 'sept': 9, 'octu': 10, 'novi': 11, 'dici': 12
        }

        # === PASO 1: Intentar parsear formatos textuales españoles PRIMERO con texto original ===

        # Patrón 1: "día de mes de año" - formato largo
        patron_textual = r'(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})'
        match = re.search(patron_textual, texto.lower())
        if match:
            dia = int(match.group(1))
            mes_texto = match.group(2)
            año = int(match.group(3))

            if mes_texto in meses_es:
                mes = meses_es[mes_texto]
                try:
                    # Validar la fecha
                    fecha_obj = datetime(año, mes, dia)
                    return fecha_obj.strftime('%d/%m/%Y')
                except ValueError:
                    pass  # Fecha inválida, continuar con otros métodos

        # Patrón 2: "día mes año" - formato corto (31 jul 2025, 15 oct 2024, etc.)
        patron_corto = r'(\d{1,2})\s+(\w+)\s+(\d{4})'
        match = re.search(patron_corto, texto.lower())
        if match:
            dia = int(match.group(1))
            mes_texto = match.group(2)
            año = int(match.group(3))

            if mes_texto in meses_es:
                mes = meses_es[mes_texto]
                try:
                    # Validar la fecha
                    fecha_obj = datetime(año, mes, dia)
                    return fecha_obj.strftime('%d/%m/%Y')
                except ValueError:
                    pass  # Fecha inválida, continuar con otros métodos

        # Eliminar espacios alrededor de separadores de fecha (/ y -)
        # Esto maneja casos como "30/ 9/2025" o "30 / 9 / 2025"
        texto = re.sub(r'\s*([/-])\s*', r'\1', texto)

        # Intentar parsear diferentes formatos de fecha
        formatos = [
            '%d/%m/%Y',      # DD/MM/YYYY
            '%d-%m-%Y',      # DD-MM-YYYY
            '%Y/%m/%d',      # YYYY/MM/DD
            '%Y-%m-%d',      # YYYY-MM-DD
            '%d/%m/%y',      # DD/MM/YY
            '%d-%m-%y',      # DD-MM-YY
        ]

        for formato in formatos:
            try:
                fecha_obj = datetime.strptime(texto.strip(), formato)
                # Convertir siempre a DD/MM/YYYY
                return fecha_obj.strftime('%d/%m/%Y')
            except ValueError:
                continue

        # Si no se puede parsear directamente, intentar extraer con regex
        patrones_fecha = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{4}',  # DD/MM/YYYY o DD-MM-YYYY
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',  # YYYY/MM/DD o YYYY-MM-DD
        ]

        for patron in patrones_fecha:
            match = re.search(patron, texto)
            if match:
                fecha_encontrada = match.group()
                # Intentar parsear lo encontrado
                for formato in formatos:
                    try:
                        fecha_obj = datetime.strptime(fecha_encontrada, formato)
                        return fecha_obj.strftime('%d/%m/%Y')
                    except ValueError:
                        continue

        # === PASO 2: Como último recurso, intentar limpieza agresiva de puntos ===
        # Esto es para casos extremos como "..3..1.. j.u.l. .2.0..2.5....."
        if '.' in texto and texto.count('.') > 3:  # Solo si hay muchos puntos
            # Limpiar puntos que aparecen entre caracteres (común en PDFs con fuentes especiales)
            texto_sin_puntos = re.sub(r'\.+', '', texto)  # Eliminar todos los puntos
            texto_sin_puntos = re.sub(r'\s+', '', texto_sin_puntos)  # Eliminar espacios intermedios

            # Agregar espacios entre números y letras para formato "31jul2025" → "31 jul 2025"
            texto_procesado = re.sub(r'(\d+)([a-zA-Z]+)', r'\1 \2', texto_sin_puntos)
            texto_procesado = re.sub(r'([a-zA-Z]+)(\d+)', r'\1 \2', texto_procesado)

            # Intentar parsear formato textual español corto con el texto procesado
            patron_corto = r'(\d{1,2})\s+(\w+)\s+(\d{4})'
            match = re.search(patron_corto, texto_procesado.lower())
            if match:
                dia = int(match.group(1))
                mes_texto = match.group(2)
                año = int(match.group(3))

                if mes_texto in meses_es:
                    mes = meses_es[mes_texto]
                    try:
                        fecha_obj = datetime(año, mes, dia)
                        return fecha_obj.strftime('%d/%m/%Y')
                    except ValueError:
                        pass

        # Devolver original si no se reconoce ningún patrón
        return texto

    @staticmethod
    def clean_numeric(texto: str) -> str:
        """
        Limpia y normaliza campos numéricos.

        Maneja diferentes formatos:
        - Formato europeo: 1.234,56 → 1234.56
        - Formato americano: 1,234.56 → 1234.56
        - Símbolos de moneda: €, $, etc.
        - Números negativos

        Args:
            texto: Texto que contiene un número

        Returns:
            Número limpio como string (punto como decimal) o texto original si inválido

        Examples:
            >>> DataCleaner.clean_numeric("1.234,56 €")
            "1234.56"
            >>> DataCleaner.clean_numeric("$ 1,234.56")
            "1234.56"
            >>> DataCleaner.clean_numeric("-123.45")
            "-123.45"
        """
        if not texto:
            return ""

        # Remover caracteres no numéricos excepto puntos, comas y signos
        texto_limpio = re.sub(r'[^\d.,+-]', '', texto)

        if not texto_limpio:
            return texto.strip()

        # Manejar formato europeo (1.234,56) vs americano (1,234.56)
        if ',' in texto_limpio and '.' in texto_limpio:
            # Si hay ambos, determinar cuál es decimal basándose en posición
            if texto_limpio.rfind(',') > texto_limpio.rfind('.'):
                # Formato europeo: 1.234,56 (coma está después del punto)
                texto_limpio = texto_limpio.replace('.', '').replace(',', '.')
            else:
                # Formato americano: 1,234.56 (punto está después de la coma)
                texto_limpio = texto_limpio.replace(',', '')
        elif ',' in texto_limpio:
            # Solo coma - podría ser decimal europeo o separador de miles
            partes = texto_limpio.split(',')
            if len(partes) == 2 and len(partes[1]) <= 2:
                # Probablemente decimal: 123,45 (2 dígitos después de coma)
                texto_limpio = texto_limpio.replace(',', '.')
            else:
                # Probablemente separador de miles: 1,234
                texto_limpio = texto_limpio.replace(',', '')

        # Validar que es un número válido
        try:
            float(texto_limpio)
            return texto_limpio
        except ValueError:
            # Devolver original si no se puede convertir
            return texto.strip()
