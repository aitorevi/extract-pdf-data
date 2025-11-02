"""
Tests para detección de duplicados cuando se procesa el mismo PDF
en diferentes ejecuciones con distintos trimestres.

Caso específico reportado:
- Usuario procesa facturas con 4T 2025
- Facturas se guardan en índice de 4T 2025
- Facturas se archivan en carpetas de 2025
- Usuario vuelve a procesar las MISMAS facturas con 1T 2026
- BUG: Se crean duplicados en índice 1T 2026 y carpetas 2026

El comportamiento correcto debería ser:
- Detectar que ya existen en 4T 2025
- Marcarlas como duplicadas
- Moverlas a carpeta de duplicados
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime
from src.file_organizer import PDFOrganizer


class TestDeteccionDuplicadosCrossTrimestre:
    """
    Tests para verificar que la detección de duplicados funciona correctamente
    cuando se procesan facturas en diferentes ejecuciones con distintos trimestres.
    """

    def setup_method(self):
        """Setup: Crear directorio temporal y organizador."""
        self.temp_dir = tempfile.mkdtemp()
        self.organizador = PDFOrganizer(directorio_base=self.temp_dir)

    def teardown_method(self):
        """Cleanup: Eliminar directorio temporal después de tests."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_factura_ya_en_indice_4t_2025_se_detecta_como_duplicada(self):
        """
        Si una factura ya existe en el índice de 4T 2025,
        debe detectarse como duplicada al procesar de nuevo.
        """
        # Setup: Agregar una factura al índice de 4T 2025
        info_factura = {
            "cif_proveedor": "B12345678",
            "fecha_factura": "2025-12-15",
            "num_factura": "F-001",
            "nombre_archivo": "factura_test.pdf",
            "ruta_completa": "/path/to/factura.pdf",
            "fecha_procesamiento": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "hash_md5": "abc123def456"
        }
        self.organizador.agregar_al_indice(2025, "4T", info_factura)

        # Verificar que se agregó correctamente
        duplicado = self.organizador.es_duplicado(
            cif_proveedor="B12345678",
            fecha_factura="15/12/2025",
            num_factura="F-001",
            año=2025,
            trimestre="4T"
        )

        assert duplicado is not None, "La factura debería detectarse como duplicada"
        assert duplicado["cif_proveedor"] == "B12345678"
        assert duplicado["num_factura"] == "F-001"

    def test_factura_diferente_cif_no_se_detecta_como_duplicada(self):
        """
        Facturas con diferente CIF no deben detectarse como duplicadas,
        incluso si tienen la misma fecha y número.
        """
        # Setup: Agregar una factura al índice
        info_factura = {
            "cif_proveedor": "B12345678",
            "fecha_factura": "2025-12-15",
            "num_factura": "F-001",
            "nombre_archivo": "factura1.pdf",
            "ruta_completa": "/path/to/factura1.pdf",
            "fecha_procesamiento": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "hash_md5": "abc123"
        }
        self.organizador.agregar_al_indice(2025, "4T", info_factura)

        # Buscar con CIF diferente
        duplicado = self.organizador.es_duplicado(
            cif_proveedor="B99999999",  # CIF diferente
            fecha_factura="15/12/2025",
            num_factura="F-001",
            año=2025,
            trimestre="4T"
        )

        assert duplicado is None, "No debería detectarse como duplicada (CIF diferente)"

    def test_factura_diferente_numero_no_se_detecta_como_duplicada(self):
        """
        Facturas con diferente número no deben detectarse como duplicadas,
        incluso si tienen el mismo CIF y fecha.
        """
        # Setup: Agregar una factura al índice
        info_factura = {
            "cif_proveedor": "B12345678",
            "fecha_factura": "2025-12-15",
            "num_factura": "F-001",
            "nombre_archivo": "factura1.pdf",
            "ruta_completa": "/path/to/factura1.pdf",
            "fecha_procesamiento": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "hash_md5": "abc123"
        }
        self.organizador.agregar_al_indice(2025, "4T", info_factura)

        # Buscar con número diferente
        duplicado = self.organizador.es_duplicado(
            cif_proveedor="B12345678",
            fecha_factura="15/12/2025",
            num_factura="F-002",  # Número diferente
            año=2025,
            trimestre="4T"
        )

        assert duplicado is None, "No debería detectarse como duplicada (número diferente)"

    def test_factura_diferente_fecha_no_se_detecta_como_duplicada(self):
        """
        Facturas con diferente fecha no deben detectarse como duplicadas,
        incluso si tienen el mismo CIF y número.
        """
        # Setup: Agregar una factura al índice
        info_factura = {
            "cif_proveedor": "B12345678",
            "fecha_factura": "2025-12-15",
            "num_factura": "F-001",
            "nombre_archivo": "factura1.pdf",
            "ruta_completa": "/path/to/factura1.pdf",
            "fecha_procesamiento": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "hash_md5": "abc123"
        }
        self.organizador.agregar_al_indice(2025, "4T", info_factura)

        # Buscar con fecha diferente
        duplicado = self.organizador.es_duplicado(
            cif_proveedor="B12345678",
            fecha_factura="20/12/2025",  # Fecha diferente
            num_factura="F-001",
            año=2025,
            trimestre="4T"
        )

        assert duplicado is None, "No debería detectarse como duplicada (fecha diferente)"

    def test_normalizacion_fechas_diferentes_formatos(self):
        """
        La detección de duplicados debe funcionar independientemente
        del formato de fecha usado (DD/MM/YYYY vs YYYY-MM-DD).
        """
        # Setup: Agregar factura con formato YYYY-MM-DD
        info_factura = {
            "cif_proveedor": "B12345678",
            "fecha_factura": "2025-12-15",  # Formato YYYY-MM-DD
            "num_factura": "F-001",
            "nombre_archivo": "factura1.pdf",
            "ruta_completa": "/path/to/factura1.pdf",
            "fecha_procesamiento": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "hash_md5": "abc123"
        }
        self.organizador.agregar_al_indice(2025, "4T", info_factura)

        # Buscar con formato DD/MM/YYYY
        duplicado = self.organizador.es_duplicado(
            cif_proveedor="B12345678",
            fecha_factura="15/12/2025",  # Formato DD/MM/YYYY
            num_factura="F-001",
            año=2025,
            trimestre="4T"
        )

        assert duplicado is not None, "Debería detectar duplicado independientemente del formato de fecha"


class TestScenarioRealBugReportado:
    """
    Tests que replican el escenario real del bug reportado por el usuario.

    Escenario:
    1. Usuario procesa facturas con 4T 2025
    2. Facturas se agregan al índice de 4T 2025
    3. Usuario vuelve a procesar con 1T 2026
    4. Las facturas deberían detectarse como duplicadas
    """

    def setup_method(self):
        """Setup: Crear directorio temporal y organizador."""
        self.temp_dir = tempfile.mkdtemp()
        self.organizador = PDFOrganizer(directorio_base=self.temp_dir)

    def teardown_method(self):
        """Cleanup: Eliminar directorio temporal después de tests."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_bug_facturas_diciembre_2025_procesadas_dos_veces(self):
        """
        Reproduce el bug reportado:
        - Factura de diciembre 2025 procesada con 4T 2025
        - Se vuelve a procesar con 1T 2026
        - Debe detectarse como duplicada

        IMPORTANTE: Este test verifica que se use el trimestre REAL (4T 2025)
        para buscar en el índice, NO el trimestre de Excel (1T 2026).
        """
        # Paso 1: Primera ejecución con 4T 2025
        # Factura de diciembre 2025 → pertenece a 4T 2025
        fecha_factura = "15/12/2025"
        cif = "B12345678"
        num_factura = "F-DIC-001"

        # Calcular trimestre REAL para índices
        trimestre_real, año_real = self.organizador.calcular_trimestre_real_para_indices(fecha_factura)
        assert trimestre_real == "4T", "Diciembre debe ser 4T"
        assert año_real == "2025", "Debe ser 2025"

        # Agregar al índice de 4T 2025
        info_factura = {
            "cif_proveedor": cif,
            "fecha_factura": self.organizador._normalizar_fecha(fecha_factura),
            "num_factura": num_factura,
            "nombre_archivo": "factura_diciembre.pdf",
            "ruta_completa": f"{self.temp_dir}/procesadas/2025/12/Proveedor/factura_diciembre.pdf",
            "fecha_procesamiento": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "hash_md5": "abc123def456"
        }
        self.organizador.agregar_al_indice(2025, "4T", info_factura)

        # Verificar que se guardó correctamente
        indice = self.organizador.cargar_indice(2025, "4T")
        assert len(indice["facturas"]) == 1

        # Paso 2: Segunda ejecución con 1T 2026
        # La MISMA factura de diciembre 2025 se vuelve a procesar
        # Debe detectarse como duplicada porque ya está en el índice de 4T 2025

        # Calcular trimestre REAL (no el de Excel)
        trimestre_busqueda, año_busqueda = self.organizador.calcular_trimestre_real_para_indices(fecha_factura)

        # Buscar duplicado en el índice del trimestre REAL
        duplicado = self.organizador.es_duplicado(
            cif_proveedor=cif,
            fecha_factura=fecha_factura,
            num_factura=num_factura,
            año=int(año_busqueda),
            trimestre=trimestre_busqueda
        )

        # VERIFICACIÓN: Debe detectarse como duplicada
        assert duplicado is not None, (
            f"BUG: Factura de {fecha_factura} ya existe en índice 4T 2025 "
            f"pero NO se detectó como duplicada al buscar en {trimestre_busqueda} {año_busqueda}"
        )
        assert duplicado["num_factura"] == num_factura
        assert duplicado["cif_proveedor"] == cif

    def test_no_debe_crear_indice_1t_2026_para_facturas_de_diciembre_2025(self):
        """
        Verifica que NO se cree un índice de 1T 2026 para facturas de diciembre 2025.

        Las facturas de diciembre 2025 deben estar SOLO en el índice de 4T 2025,
        independientemente del trimestre que el usuario haya seleccionado para procesar.
        """
        # Agregar factura de diciembre 2025 al índice de 4T 2025
        fecha_factura = "20/12/2025"
        info_factura = {
            "cif_proveedor": "B98765432",
            "fecha_factura": self.organizador._normalizar_fecha(fecha_factura),
            "num_factura": "F-DIC-999",
            "nombre_archivo": "otra_factura_diciembre.pdf",
            "ruta_completa": f"{self.temp_dir}/procesadas/2025/12/Proveedor/otra_factura.pdf",
            "fecha_procesamiento": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "hash_md5": "xyz789"
        }
        self.organizador.agregar_al_indice(2025, "4T", info_factura)

        # Verificar que existe en 4T 2025
        indice_4t_2025 = self.organizador.cargar_indice(2025, "4T")
        assert len(indice_4t_2025["facturas"]) == 1

        # Verificar que NO existe índice de 1T 2026
        archivo_indice_1t_2026 = Path(self.temp_dir) / "procesadas" / "indices" / "indice_2026_1T.json"
        assert not archivo_indice_1t_2026.exists(), (
            "NO debe existir índice de 1T 2026 para facturas de diciembre 2025"
        )

        # Si se intenta cargar el índice de 1T 2026, debe estar vacío
        indice_1t_2026 = self.organizador.cargar_indice(2026, "1T")
        assert len(indice_1t_2026["facturas"]) == 0, (
            "El índice de 1T 2026 debe estar vacío (o no existir) para facturas de diciembre 2025"
        )

    def test_multiples_facturas_diferentes_trimestres(self):
        """
        Test con múltiples facturas de diferentes trimestres para verificar
        que cada una se registra en su trimestre REAL correcto.
        """
        facturas_test = [
            ("15/01/2025", "B11111111", "F-ENE-001", "1T", "2025"),
            ("15/04/2025", "B22222222", "F-ABR-001", "2T", "2025"),
            ("15/07/2025", "B33333333", "F-JUL-001", "3T", "2025"),
            ("15/10/2025", "B44444444", "F-OCT-001", "4T", "2025"),
            ("15/12/2025", "B55555555", "F-DIC-001", "4T", "2025"),
        ]

        for fecha, cif, num, trimestre_esperado, año_esperado in facturas_test:
            # Calcular trimestre real
            trimestre, año = self.organizador.calcular_trimestre_real_para_indices(fecha)
            assert trimestre == trimestre_esperado, f"Fecha {fecha} debería ser {trimestre_esperado}"
            assert año == año_esperado, f"Fecha {fecha} debería ser {año_esperado}"

            # Agregar al índice del trimestre real
            info = {
                "cif_proveedor": cif,
                "fecha_factura": self.organizador._normalizar_fecha(fecha),
                "num_factura": num,
                "nombre_archivo": f"factura_{num}.pdf",
                "ruta_completa": f"{self.temp_dir}/procesadas/{año}/{trimestre}/factura.pdf",
                "fecha_procesamiento": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "hash_md5": f"hash_{num}"
            }
            self.organizador.agregar_al_indice(int(año), trimestre, info)

        # Verificar que cada factura está en su índice correcto
        indice_1t = self.organizador.cargar_indice(2025, "1T")
        indice_2t = self.organizador.cargar_indice(2025, "2T")
        indice_3t = self.organizador.cargar_indice(2025, "3T")
        indice_4t = self.organizador.cargar_indice(2025, "4T")

        assert len(indice_1t["facturas"]) == 1, "1T debe tener 1 factura"
        assert len(indice_2t["facturas"]) == 1, "2T debe tener 1 factura"
        assert len(indice_3t["facturas"]) == 1, "3T debe tener 1 factura"
        assert len(indice_4t["facturas"]) == 2, "4T debe tener 2 facturas (octubre y diciembre)"
