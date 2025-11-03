"""
Tests para el cálculo de trimestre REAL (sin lógica de negocio) usado para índices.

Esta funcionalidad calcula el trimestre cronológico basándose únicamente en la fecha
de la factura, sin aplicar ninguna regla de negocio. Se usa para:
- Generar índices de facturas por trimestre
- Detectar duplicados
- Organizar archivos por trimestre real
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from src.file_organizer import PDFOrganizer


class TestCalculoTrimestreRealParaIndices:
    """Tests para calcular_trimestre_real_para_indices."""

    def setup_method(self):
        """Setup: Crear directorio temporal para tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.organizador = PDFOrganizer(directorio_base=self.temp_dir)

    def teardown_method(self):
        """Cleanup: Eliminar directorio temporal después de tests."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_fecha_enero_es_t1(self):
        """Enero debe ser 1T."""
        trimestre, año = self.organizador.calcular_trimestre_real_para_indices("15/01/2025")
        assert trimestre == "1T"
        assert año == "2025"

    def test_fecha_febrero_es_t1(self):
        """Febrero debe ser 1T."""
        trimestre, año = self.organizador.calcular_trimestre_real_para_indices("28/02/2025")
        assert trimestre == "1T"
        assert año == "2025"

    def test_fecha_marzo_es_t1(self):
        """Marzo debe ser 1T."""
        trimestre, año = self.organizador.calcular_trimestre_real_para_indices("31/03/2025")
        assert trimestre == "1T"
        assert año == "2025"

    def test_fecha_abril_es_t2(self):
        """Abril debe ser 2T."""
        trimestre, año = self.organizador.calcular_trimestre_real_para_indices("01/04/2025")
        assert trimestre == "2T"
        assert año == "2025"

    def test_fecha_mayo_es_t2(self):
        """Mayo debe ser 2T."""
        trimestre, año = self.organizador.calcular_trimestre_real_para_indices("15/05/2025")
        assert trimestre == "2T"
        assert año == "2025"

    def test_fecha_junio_es_t2(self):
        """Junio debe ser 2T."""
        trimestre, año = self.organizador.calcular_trimestre_real_para_indices("30/06/2025")
        assert trimestre == "2T"
        assert año == "2025"

    def test_fecha_julio_es_t3(self):
        """Julio debe ser 3T."""
        trimestre, año = self.organizador.calcular_trimestre_real_para_indices("01/07/2025")
        assert trimestre == "3T"
        assert año == "2025"

    def test_fecha_agosto_es_t3(self):
        """Agosto debe ser 3T."""
        trimestre, año = self.organizador.calcular_trimestre_real_para_indices("15/08/2025")
        assert trimestre == "3T"
        assert año == "2025"

    def test_fecha_septiembre_es_t3(self):
        """Septiembre debe ser 3T."""
        trimestre, año = self.organizador.calcular_trimestre_real_para_indices("30/09/2025")
        assert trimestre == "3T"
        assert año == "2025"

    def test_fecha_octubre_es_t4(self):
        """Octubre debe ser 4T."""
        trimestre, año = self.organizador.calcular_trimestre_real_para_indices("01/10/2025")
        assert trimestre == "4T"
        assert año == "2025"

    def test_fecha_noviembre_es_t4(self):
        """Noviembre debe ser 4T."""
        trimestre, año = self.organizador.calcular_trimestre_real_para_indices("15/11/2025")
        assert trimestre == "4T"
        assert año == "2025"

    def test_fecha_diciembre_es_t4(self):
        """Diciembre debe ser 4T."""
        trimestre, año = self.organizador.calcular_trimestre_real_para_indices("31/12/2025")
        assert trimestre == "4T"
        assert año == "2025"

    def test_formato_yyyy_mm_dd(self):
        """Debe soportar formato YYYY-MM-DD."""
        trimestre, año = self.organizador.calcular_trimestre_real_para_indices("2025-12-15")
        assert trimestre == "4T"
        assert año == "2025"

    def test_formato_dd_mm_yyyy(self):
        """Debe soportar formato DD/MM/YYYY."""
        trimestre, año = self.organizador.calcular_trimestre_real_para_indices("15/12/2025")
        assert trimestre == "4T"
        assert año == "2025"

    def test_fecha_vacia_retorna_vacios(self):
        """Fecha vacía debe retornar strings vacíos."""
        trimestre, año = self.organizador.calcular_trimestre_real_para_indices("")
        assert trimestre == ""
        assert año == ""

    def test_fecha_invalida_retorna_vacios(self):
        """Fecha inválida debe retornar strings vacíos."""
        trimestre, año = self.organizador.calcular_trimestre_real_para_indices("fecha-invalida")
        assert trimestre == ""
        assert año == ""

    def test_diferentes_años(self):
        """Debe funcionar correctamente con diferentes años."""
        trimestre_2024, año_2024 = self.organizador.calcular_trimestre_real_para_indices("15/12/2024")
        trimestre_2025, año_2025 = self.organizador.calcular_trimestre_real_para_indices("15/03/2025")
        trimestre_2026, año_2026 = self.organizador.calcular_trimestre_real_para_indices("15/06/2026")

        assert (trimestre_2024, año_2024) == ("4T", "2024")
        assert (trimestre_2025, año_2025) == ("1T", "2025")
        assert (trimestre_2026, año_2026) == ("2T", "2026")

    def test_limite_trimestres(self):
        """Tests de límites entre trimestres."""
        # Último día de T1
        t1, y1 = self.organizador.calcular_trimestre_real_para_indices("31/03/2025")
        assert t1 == "1T"

        # Primer día de T2
        t2, y2 = self.organizador.calcular_trimestre_real_para_indices("01/04/2025")
        assert t2 == "2T"

        # Último día de T2
        t2_fin, y2_fin = self.organizador.calcular_trimestre_real_para_indices("30/06/2025")
        assert t2_fin == "2T"

        # Primer día de T3
        t3, y3 = self.organizador.calcular_trimestre_real_para_indices("01/07/2025")
        assert t3 == "3T"

        # Último día de T3
        t3_fin, y3_fin = self.organizador.calcular_trimestre_real_para_indices("30/09/2025")
        assert t3_fin == "3T"

        # Primer día de T4
        t4, y4 = self.organizador.calcular_trimestre_real_para_indices("01/10/2025")
        assert t4 == "4T"


class TestIndependenciaLogicaNegocio:
    """
    Tests para verificar que el cálculo de trimestre para índices
    NO aplica ninguna lógica de negocio (a diferencia del Excel).
    """

    def setup_method(self):
        """Setup: Crear directorio temporal para tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.organizador = PDFOrganizer(directorio_base=self.temp_dir)

    def teardown_method(self):
        """Cleanup: Eliminar directorio temporal después de tests."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_diciembre_2024_siempre_es_4t_2024_no_1t_2025(self):
        """
        Una factura de diciembre 2024 debe ser 4T 2024 en los índices,
        INCLUSO si el usuario procesó con 1T 2026 (que en Excel sería 1T 2026).

        Este test verifica que NO se aplica la regla de negocio del caso especial T1.
        """
        trimestre, año = self.organizador.calcular_trimestre_real_para_indices("15/12/2024")

        # Para índices, diciembre 2024 SIEMPRE es 4T 2024
        assert trimestre == "4T"
        assert año == "2024"

        # NO debe ser 1T 2025 (esa es la lógica de negocio para Excel)

    def test_factura_de_cualquier_trimestre_mantiene_su_trimestre_real(self):
        """
        Todas las facturas deben mantener su trimestre cronológico real,
        independientemente del trimestre que el usuario haya seleccionado.
        """
        # Simular diferentes fechas
        fechas_esperadas = [
            ("15/01/2025", "1T", "2025"),
            ("15/04/2025", "2T", "2025"),
            ("15/07/2025", "3T", "2025"),
            ("15/10/2025", "4T", "2025"),
            ("15/12/2024", "4T", "2024"),
            ("15/03/2026", "1T", "2026"),
        ]

        for fecha, trimestre_esperado, año_esperado in fechas_esperadas:
            trimestre, año = self.organizador.calcular_trimestre_real_para_indices(fecha)
            assert trimestre == trimestre_esperado, f"Fecha {fecha} debería ser {trimestre_esperado}, pero es {trimestre}"
            assert año == año_esperado, f"Fecha {fecha} debería ser año {año_esperado}, pero es {año}"
