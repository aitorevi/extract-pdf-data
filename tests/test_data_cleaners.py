"""
Tests para el módulo utils/data_cleaners.py - Limpieza de datos extraídos.

Este módulo prueba las funciones estáticas de limpieza y normalización
de datos extraídos de facturas PDF.
"""

import pytest
from src.utils.data_cleaners import DataCleaner


@pytest.mark.unit
class TestCleanText:
    """Tests para limpieza de texto."""

    def test_clean_text_espacios_multiples(self):
        """Test que limpia espacios múltiples."""
        assert DataCleaner.clean_text("  texto   con   espacios  ") == "texto con espacios"

    def test_clean_text_vacio(self):
        """Test con string vacío."""
        assert DataCleaner.clean_text("") == ""

    def test_clean_text_caracteres_especiales(self):
        """Test que elimina caracteres de control."""
        texto_con_ctrl = "texto\x00con\x1fcaracteres\x7fcontrol"
        # Los caracteres de control se convierten en espacios primero, luego se normalizan
        assert DataCleaner.clean_text(texto_con_ctrl) == "textocon caracterescontrol"

    def test_clean_text_saltos_de_linea(self):
        """Test que normaliza saltos de línea a espacios."""
        assert DataCleaner.clean_text("linea1\n\nlinea2\tlinea3") == "linea1 linea2 linea3"


@pytest.mark.unit
class TestCleanDate:
    """Tests para limpieza y normalización de fechas."""

    def test_clean_date_formato_dd_mm_yyyy(self):
        """Test fecha ya en formato DD/MM/YYYY."""
        assert DataCleaner.clean_date("15/01/2024") == "15/01/2024"

    def test_clean_date_formato_yyyy_mm_dd(self):
        """Test fecha en formato YYYY-MM-DD."""
        assert DataCleaner.clean_date("2024-01-15") == "15/01/2024"

    def test_clean_date_formato_dd_mm_yy(self):
        """Test fecha con año de 2 dígitos."""
        assert DataCleaner.clean_date("15/01/24") == "15/01/2024"

    def test_clean_date_formato_dd_guion_mm_guion_yyyy(self):
        """Test fecha con guiones."""
        assert DataCleaner.clean_date("15-01-2024") == "15/01/2024"

    def test_clean_date_con_texto_adicional(self):
        """Test extracción de fecha de texto."""
        assert DataCleaner.clean_date("Fecha: 15/01/2024 (vencimiento)") == "15/01/2024"

    def test_clean_date_sin_patron_reconocible(self):
        """Test con texto sin fecha válida."""
        resultado = DataCleaner.clean_date("No hay fecha aquí")
        assert resultado == "No hay fecha aquí"

    def test_clean_date_con_espacios(self):
        """Test fecha con espacios extra."""
        assert DataCleaner.clean_date("  15/01/2024  ") == "15/01/2024"

    def test_clean_date_formato_mes_abreviado(self):
        """Test fecha con mes abreviado: 31 jul 2025."""
        assert DataCleaner.clean_date("31 jul 2025") == "31/07/2025"

    def test_clean_date_formato_mes_abreviado_mayusculas(self):
        """Test fecha con mes abreviado en mayúsculas."""
        assert DataCleaner.clean_date("31 JUL 2025") == "31/07/2025"
        assert DataCleaner.clean_date("31 Jul 2025") == "31/07/2025"

    def test_clean_date_todos_meses_abreviados(self):
        """Test todos los meses abreviados."""
        assert DataCleaner.clean_date("1 ene 2025") == "01/01/2025"
        assert DataCleaner.clean_date("15 feb 2025") == "15/02/2025"
        assert DataCleaner.clean_date("10 mar 2025") == "10/03/2025"
        assert DataCleaner.clean_date("20 abr 2025") == "20/04/2025"
        assert DataCleaner.clean_date("5 may 2025") == "05/05/2025"
        assert DataCleaner.clean_date("30 jun 2025") == "30/06/2025"
        assert DataCleaner.clean_date("31 jul 2025") == "31/07/2025"
        assert DataCleaner.clean_date("15 ago 2025") == "15/08/2025"
        assert DataCleaner.clean_date("1 sep 2025") == "01/09/2025"
        assert DataCleaner.clean_date("15 oct 2024") == "15/10/2024"
        assert DataCleaner.clean_date("20 nov 2024") == "20/11/2024"
        assert DataCleaner.clean_date("25 dic 2024") == "25/12/2024"

    def test_clean_date_formato_mes_completo(self):
        """Test fecha con mes completo."""
        assert DataCleaner.clean_date("31 julio 2025") == "31/07/2025"
        assert DataCleaner.clean_date("15 octubre 2024") == "15/10/2024"

    def test_clean_date_formato_textual_largo(self):
        """Test formato textual largo: 1 de octubre de 2025."""
        assert DataCleaner.clean_date("1 de octubre de 2025") == "01/10/2025"
        assert DataCleaner.clean_date("15 de enero de 2024") == "15/01/2024"

    def test_clean_date_formato_puntos_yyyy(self):
        """Test fecha con puntos en formato DD.MM.YYYY."""
        assert DataCleaner.clean_date("15.01.2024") == "15/01/2024"
        assert DataCleaner.clean_date("31.12.2025") == "31/12/2025"

    def test_clean_date_formato_puntos_yy(self):
        """Test fecha con puntos en formato DD.MM.YY (caso Dolz)."""
        assert DataCleaner.clean_date("17.11.25") == "17/11/2025"
        assert DataCleaner.clean_date("01.01.24") == "01/01/2024"

    def test_clean_date_formato_puntos_con_espacios(self):
        """Test fecha con puntos y espacios: 17 . 11 . 25."""
        assert DataCleaner.clean_date("17 . 11 . 25") == "17/11/2025"
        assert DataCleaner.clean_date("1 . 1 . 2024") == "01/01/2024"

    def test_clean_date_formato_mes_abreviado_con_punto(self):
        """Test fecha con mes abreviado seguido de punto: 17 dic. 2025."""
        assert DataCleaner.clean_date("17 dic. 2025") == "17/12/2025"
        assert DataCleaner.clean_date("1 ene. 2024") == "01/01/2024"
        assert DataCleaner.clean_date("31 jul. 2025") == "31/07/2025"
        assert DataCleaner.clean_date("15 oct. 2024") == "15/10/2024"

    def test_clean_date_formato_mes_abreviado_con_punto_mayusculas(self):
        """Test fecha con mes abreviado con punto en mayúsculas."""
        assert DataCleaner.clean_date("17 DIC. 2025") == "17/12/2025"
        assert DataCleaner.clean_date("17 Dic. 2025") == "17/12/2025"


@pytest.mark.unit
class TestCleanNumeric:
    """Tests para limpieza y normalización de números."""

    def test_clean_numeric_entero(self):
        """Test número entero simple."""
        assert DataCleaner.clean_numeric("1234") == "1234"

    def test_clean_numeric_decimal_punto(self):
        """Test número con punto decimal."""
        assert DataCleaner.clean_numeric("1234.56") == "1234.56"

    def test_clean_numeric_formato_europeo(self):
        """Test formato europeo: 1.234,56"""
        assert DataCleaner.clean_numeric("1.234,56") == "1234.56"

    def test_clean_numeric_formato_americano(self):
        """Test formato americano: 1,234.56"""
        assert DataCleaner.clean_numeric("1,234.56") == "1234.56"

    def test_clean_numeric_solo_coma_decimal(self):
        """Test número con coma como decimal: 123,45"""
        assert DataCleaner.clean_numeric("123,45") == "123.45"

    def test_clean_numeric_solo_coma_miles(self):
        """Test número con coma como separador de miles: 1,234"""
        assert DataCleaner.clean_numeric("1,234") == "1234"

    def test_clean_numeric_con_simbolos(self):
        """Test número con símbolos de moneda."""
        assert DataCleaner.clean_numeric("€ 1.234,56") == "1234.56"
        assert DataCleaner.clean_numeric("$ 1,234.56") == "1234.56"
        assert DataCleaner.clean_numeric("1.234,56 €") == "1234.56"

    def test_clean_numeric_negativo(self):
        """Test número negativo."""
        assert DataCleaner.clean_numeric("-123.45") == "-123.45"

    def test_clean_numeric_invalido(self):
        """Test con texto que no es número."""
        resultado = DataCleaner.clean_numeric("No es un número")
        assert resultado == "No es un número"

    def test_clean_numeric_vacio(self):
        """Test con string vacío."""
        resultado = DataCleaner.clean_numeric("")
        assert resultado.strip() == ""


@pytest.mark.integration
class TestDataCleanerIntegration:
    """Tests de integración para flujos completos."""

    def test_limpiar_datos_completos(self):
        """Test limpieza de un conjunto completo de datos."""
        datos_crudos = {
            'nombre': '  Juan   Pérez  ',
            'fecha': '2024-01-15',
            'importe': '1.234,56 €',
            'descripcion': 'Factura\n\npor\tservicios'
        }

        # Limpiar todos los campos
        datos_limpios = {
            'nombre': DataCleaner.clean_text(datos_crudos['nombre']),
            'fecha': DataCleaner.clean_date(datos_crudos['fecha']),
            'importe': DataCleaner.clean_numeric(datos_crudos['importe']),
            'descripcion': DataCleaner.clean_text(datos_crudos['descripcion'])
        }

        assert datos_limpios['nombre'] == "Juan Pérez"
        assert datos_limpios['fecha'] == "15/01/2024"
        assert datos_limpios['importe'] == "1234.56"
        assert datos_limpios['descripcion'] == "Factura por servicios"
