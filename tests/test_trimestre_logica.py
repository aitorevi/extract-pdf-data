"""
Tests para la lógica de marcado inteligente de trimestres.

Esta funcionalidad determina el trimestre a asignar a cada factura basándose en:
1. La fecha de emisión de la factura
2. El trimestre introducido por el usuario
3. Reglas de negocio específicas
"""

import pytest
from datetime import datetime
from src.pdf_extractor import PDFExtractor


class TestCalculoTrimestreDesdeFecha:
    """Tests para calcular el trimestre a partir de una fecha."""

    def test_fecha_enero_pertenece_a_t1(self):
        """Enero pertenece al trimestre 1."""
        fecha = datetime(2025, 1, 15)
        trimestre = PDFExtractor.calcular_trimestre_desde_fecha(fecha)
        assert trimestre == 1

    def test_fecha_marzo_pertenece_a_t1(self):
        """Marzo pertenece al trimestre 1."""
        fecha = datetime(2025, 3, 31)
        trimestre = PDFExtractor.calcular_trimestre_desde_fecha(fecha)
        assert trimestre == 1

    def test_fecha_abril_pertenece_a_t2(self):
        """Abril pertenece al trimestre 2."""
        fecha = datetime(2025, 4, 1)
        trimestre = PDFExtractor.calcular_trimestre_desde_fecha(fecha)
        assert trimestre == 2

    def test_fecha_junio_pertenece_a_t2(self):
        """Junio pertenece al trimestre 2."""
        fecha = datetime(2025, 6, 30)
        trimestre = PDFExtractor.calcular_trimestre_desde_fecha(fecha)
        assert trimestre == 2

    def test_fecha_julio_pertenece_a_t3(self):
        """Julio pertenece al trimestre 3."""
        fecha = datetime(2025, 7, 1)
        trimestre = PDFExtractor.calcular_trimestre_desde_fecha(fecha)
        assert trimestre == 3

    def test_fecha_septiembre_pertenece_a_t3(self):
        """Septiembre pertenece al trimestre 3."""
        fecha = datetime(2025, 9, 30)
        trimestre = PDFExtractor.calcular_trimestre_desde_fecha(fecha)
        assert trimestre == 3

    def test_fecha_octubre_pertenece_a_t4(self):
        """Octubre pertenece al trimestre 4."""
        fecha = datetime(2025, 10, 1)
        trimestre = PDFExtractor.calcular_trimestre_desde_fecha(fecha)
        assert trimestre == 4

    def test_fecha_diciembre_pertenece_a_t4(self):
        """Diciembre pertenece al trimestre 4."""
        fecha = datetime(2025, 12, 31)
        trimestre = PDFExtractor.calcular_trimestre_desde_fecha(fecha)
        assert trimestre == 4


class TestLogicaMarcadoTrimestres:
    """Tests para la lógica de marcado de trimestres según reglas de negocio."""

    def test_usuario_introduce_t2_factura_t1_se_marca_t2(self):
        """
        Usuario introduce T2, factura es T1 (anterior).
        Resultado: Se marca como T2.
        """
        fecha_factura = datetime(2025, 2, 15)  # T1
        trimestre_usuario = 2
        año_usuario = 2025

        resultado = PDFExtractor.determinar_trimestre_factura(
            fecha_factura, trimestre_usuario, año_usuario
        )

        assert resultado == (2, 2025)  # (trimestre, año)

    def test_usuario_introduce_t2_factura_t2_se_marca_t2(self):
        """
        Usuario introduce T2, factura es T2 (igual).
        Resultado: Se marca como T2.
        """
        fecha_factura = datetime(2025, 5, 15)  # T2
        trimestre_usuario = 2
        año_usuario = 2025

        resultado = PDFExtractor.determinar_trimestre_factura(
            fecha_factura, trimestre_usuario, año_usuario
        )

        assert resultado == (2, 2025)

    def test_usuario_introduce_t2_factura_t3_se_marca_t3(self):
        """
        Usuario introduce T2, factura es T3 (posterior).
        Resultado: Se marca con su propio trimestre T3.
        """
        fecha_factura = datetime(2025, 8, 15)  # T3
        trimestre_usuario = 2
        año_usuario = 2025

        resultado = PDFExtractor.determinar_trimestre_factura(
            fecha_factura, trimestre_usuario, año_usuario
        )

        assert resultado == (3, 2025)

    def test_usuario_introduce_t2_factura_t4_se_marca_t4(self):
        """
        Usuario introduce T2, factura es T4 (posterior).
        Resultado: Se marca con su propio trimestre T4.
        """
        fecha_factura = datetime(2025, 11, 15)  # T4
        trimestre_usuario = 2
        año_usuario = 2025

        resultado = PDFExtractor.determinar_trimestre_factura(
            fecha_factura, trimestre_usuario, año_usuario
        )

        assert resultado == (4, 2025)

    def test_usuario_introduce_t3_factura_t1_se_marca_t3(self):
        """
        Usuario introduce T3, factura es T1 (anterior).
        Resultado: Se marca como T3.
        """
        fecha_factura = datetime(2025, 2, 15)  # T1
        trimestre_usuario = 3
        año_usuario = 2025

        resultado = PDFExtractor.determinar_trimestre_factura(
            fecha_factura, trimestre_usuario, año_usuario
        )

        assert resultado == (3, 2025)

    def test_usuario_introduce_t3_factura_t4_se_marca_t4(self):
        """
        Usuario introduce T3, factura es T4 (posterior).
        Resultado: Se marca con su propio trimestre T4.
        """
        fecha_factura = datetime(2025, 11, 15)  # T4
        trimestre_usuario = 3
        año_usuario = 2025

        resultado = PDFExtractor.determinar_trimestre_factura(
            fecha_factura, trimestre_usuario, año_usuario
        )

        assert resultado == (4, 2025)


class TestCasoEspecialT1ConAñoAnterior:
    """Tests para el caso especial de T1 que incluye T4 del año anterior."""

    def test_usuario_introduce_t1_2025_factura_t4_2024_se_marca_t1_2025(self):
        """
        Usuario introduce T1 de 2025, factura es T4 de 2024.
        Resultado: Se marca como T1 de 2025 (caso especial).
        """
        fecha_factura = datetime(2024, 11, 15)  # T4 de 2024
        trimestre_usuario = 1
        año_usuario = 2025

        resultado = PDFExtractor.determinar_trimestre_factura(
            fecha_factura, trimestre_usuario, año_usuario
        )

        assert resultado == (1, 2025)

    def test_usuario_introduce_t1_2025_factura_t1_2025_se_marca_t1_2025(self):
        """
        Usuario introduce T1 de 2025, factura es T1 de 2025.
        Resultado: Se marca como T1 de 2025.
        """
        fecha_factura = datetime(2025, 2, 15)  # T1 de 2025
        trimestre_usuario = 1
        año_usuario = 2025

        resultado = PDFExtractor.determinar_trimestre_factura(
            fecha_factura, trimestre_usuario, año_usuario
        )

        assert resultado == (1, 2025)

    def test_usuario_introduce_t1_2025_factura_t2_2025_se_marca_t2_2025(self):
        """
        Usuario introduce T1 de 2025, factura es T2 de 2025 (posterior).
        Resultado: Se marca con su propio trimestre T2 de 2025.
        """
        fecha_factura = datetime(2025, 5, 15)  # T2 de 2025
        trimestre_usuario = 1
        año_usuario = 2025

        resultado = PDFExtractor.determinar_trimestre_factura(
            fecha_factura, trimestre_usuario, año_usuario
        )

        assert resultado == (2, 2025)

    def test_usuario_introduce_t1_2025_factura_t3_2024_se_ignora(self):
        """
        Usuario introduce T1 de 2025, factura es T3 de 2024 (no T4).
        Resultado: Se marca como None (se debe excluir).
        """
        fecha_factura = datetime(2024, 8, 15)  # T3 de 2024
        trimestre_usuario = 1
        año_usuario = 2025

        resultado = PDFExtractor.determinar_trimestre_factura(
            fecha_factura, trimestre_usuario, año_usuario
        )

        # Esta factura no debe incluirse (None indica exclusión)
        assert resultado is None

    def test_usuario_introduce_t2_2025_factura_t4_2024_se_ignora(self):
        """
        Usuario introduce T2 de 2025, factura es T4 de 2024.
        Resultado: None (se excluye, solo T1 incluye año anterior).
        """
        fecha_factura = datetime(2024, 11, 15)  # T4 de 2024
        trimestre_usuario = 2
        año_usuario = 2025

        resultado = PDFExtractor.determinar_trimestre_factura(
            fecha_factura, trimestre_usuario, año_usuario
        )

        assert resultado is None


class TestConversionFormatoTrimestre:
    """Tests para conversión entre formatos de trimestre (1, 2, 3, 4) y (1T, 2T, 3T, 4T)."""

    def test_convertir_numero_a_formato_t(self):
        """Convierte número de trimestre a formato con T."""
        assert PDFExtractor.formatear_trimestre(1) == "1T"
        assert PDFExtractor.formatear_trimestre(2) == "2T"
        assert PDFExtractor.formatear_trimestre(3) == "3T"
        assert PDFExtractor.formatear_trimestre(4) == "4T"

    def test_parsear_formato_t_a_numero(self):
        """Parsea formato con T a número de trimestre."""
        assert PDFExtractor.parsear_trimestre("1T") == 1
        assert PDFExtractor.parsear_trimestre("2T") == 2
        assert PDFExtractor.parsear_trimestre("3T") == 3
        assert PDFExtractor.parsear_trimestre("4T") == 4

    def test_parsear_numero_directo(self):
        """Parsea número directo si no tiene T."""
        assert PDFExtractor.parsear_trimestre("1") == 1
        assert PDFExtractor.parsear_trimestre("2") == 2


class TestIntegracionConExtraccionPDF:
    """Tests de integración con el flujo completo de extracción."""

    def test_extractor_aplica_logica_trimestres_correctamente(self, tmp_path):
        """
        Test de integración: verifica que el extractor aplique correctamente
        la lógica de trimestres al extraer datos de un PDF.

        Este test se implementará cuando la funcionalidad esté integrada.
        """
        # Este test requiere un PDF de prueba y una plantilla
        # Se dejará como placeholder por ahora
        pytest.skip("Test de integración pendiente de implementación")

    def test_fechas_sin_año_usan_año_actual(self):
        """
        Si una fecha no tiene año, se asume el año introducido por el usuario.
        """
        # Este comportamiento debe mantenerse
        pytest.skip("Test pendiente de validar comportamiento actual")
