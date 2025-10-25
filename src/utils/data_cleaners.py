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
    def clean_date(texto: str) -> str:
        """
        Limpia y normaliza campos de fecha al formato DD/MM/YYYY.

        Soporta múltiples formatos de entrada:
        - DD/MM/YYYY, DD-MM-YYYY
        - YYYY/MM/DD, YYYY-MM-DD
        - DD/MM/YY, DD-MM-YY
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
        """
        # Primero limpiar el texto
        texto = DataCleaner.clean_text(texto)

        if not texto:
            return ""

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
