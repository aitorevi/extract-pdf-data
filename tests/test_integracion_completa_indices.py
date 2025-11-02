"""
Tests de integración end-to-end para el flujo completo:
1. Extracción de factura
2. Generación de índice por trimestre REAL
3. Organización de archivos
4. Detección de duplicados
5. Movimiento a carpeta correcta
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch
from src.pdf_extractor import PDFExtractor
from src.file_organizer import PDFOrganizer


class TestIntegracionCompletaIndicesYOrganizacion:
    """
    Tests end-to-end que verifican el flujo completo desde extracción
    hasta organización de archivos e índices.
    """

    def setup_method(self):
        """Setup: Crear directorios temporales."""
        self.temp_dir = tempfile.mkdtemp()
        self.facturas_dir = Path(self.temp_dir) / "facturas"
        self.plantillas_dir = Path(self.temp_dir) / "plantillas"
        self.facturas_dir.mkdir()
        self.plantillas_dir.mkdir()

    def teardown_method(self):
        """Cleanup: Eliminar directorios temporales."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def crear_plantilla_test(self, cif_proveedor="B12345678", nombre_proveedor="Test Provider"):
        """Helper: Crear plantilla de prueba."""
        plantilla = {
            "nombre_proveedor": nombre_proveedor,
            "cif_proveedor": cif_proveedor,
            "campos": [
                {
                    "nombre": "Nombre_Identificacion",
                    "coordenadas": [10, 10, 100, 30],
                    "tipo": "texto",
                    "es_identificacion": True
                },
                {
                    "nombre": "CIF_Identificacion",
                    "coordenadas": [10, 35, 100, 55],
                    "tipo": "texto",
                    "es_identificacion": True
                },
                {
                    "nombre": "NumFactura",
                    "coordenadas": [10, 60, 100, 80],
                    "tipo": "texto"
                },
                {
                    "nombre": "FechaFactura",
                    "coordenadas": [10, 85, 100, 105],
                    "tipo": "fecha"
                },
                {
                    "nombre": "Base",
                    "coordenadas": [10, 110, 100, 130],
                    "tipo": "numerico"
                }
            ]
        }

        plantilla_path = self.plantillas_dir / "test_provider.json"
        with open(plantilla_path, "w", encoding="utf-8") as f:
            json.dump(plantilla, f)

        return plantilla_path

    def crear_pdf_mock(self, nombre_archivo="factura_test.pdf"):
        """Helper: Crear PDF de prueba."""
        pdf_path = self.facturas_dir / nombre_archivo
        pdf_path.touch()
        return pdf_path

    def configurar_mock_extraccion(self, nombre_proveedor="Test Provider",
                                   cif="B12345678", num_factura="F-001",
                                   fecha_factura="15/12/2025", base="100.00"):
        """Helper: Configurar mock de pdfplumber para simular extracción."""
        def mock_crop(bbox):
            mock_result = MagicMock()
            y_coord = bbox[1]

            if y_coord < 32:  # Nombre_Identificacion
                mock_result.extract_text.return_value = nombre_proveedor
            elif y_coord < 57:  # CIF_Identificacion
                mock_result.extract_text.return_value = cif
            elif y_coord < 82:  # NumFactura
                mock_result.extract_text.return_value = num_factura
            elif y_coord < 107:  # FechaFactura
                mock_result.extract_text.return_value = fecha_factura
            else:  # Base
                mock_result.extract_text.return_value = base

            return mock_result

        mock_page = MagicMock()
        mock_page.crop = mock_crop
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)

        return mock_pdf

    @patch('pdfplumber.open')
    def test_flujo_completo_procesar_factura_generar_indice_organizar(self, mock_pdf_open):
        """
        Test end-to-end: Procesar factura, generar índice y organizar archivos.

        Flujo:
        1. Crear plantilla y PDF
        2. Procesar con PDFExtractor (trimestre usuario: 1T 2026)
        3. Verificar que se genera índice en trimestre REAL (4T 2025)
        4. Verificar que archivo se organiza en carpeta correcta
        5. Verificar contenido del índice
        """
        # Setup: Crear plantilla y PDF
        self.crear_plantilla_test()
        pdf_path = self.crear_pdf_mock("factura_diciembre_2025.pdf")

        # Setup: Configurar mock para simular extracción
        # Factura de diciembre 2025 → trimestre REAL es 4T 2025
        mock_pdf = self.configurar_mock_extraccion(
            fecha_factura="15/12/2025",
            num_factura="F-DIC-001",
            base="250.00"
        )
        mock_pdf_open.return_value = mock_pdf

        # Paso 1: Procesar con PDFExtractor (usuario selecciona 1T 2026)
        extractor = PDFExtractor(
            directorio_facturas=str(self.facturas_dir),
            directorio_plantillas=str(self.plantillas_dir),
            trimestre="1T",
            año="2026",
            organizar_archivos=True
        )
        extractor.cargar_plantillas()
        resultados = extractor.procesar_directorio_facturas()

        # Verificaciones básicas de extracción
        assert len(resultados) == 1, "Debe haber procesado 1 factura"
        factura = resultados[0]
        assert factura['NumFactura'] == "F-DIC-001"
        assert factura['FechaFactura'] == "15/12/2025"
        assert factura['Trimestre'] == "1T", "En Excel debe ser 1T 2026 (lógica negocio)"
        assert factura['Año'] == "2026", "En Excel debe ser año 2026 (lógica negocio)"

        # Paso 2: Verificar que se generó índice en trimestre REAL (4T 2025, NO 1T 2026)
        indice_4t_2025_path = Path(self.temp_dir) / "procesados" / "indices" / "indice_2025_4T.json"
        indice_1t_2026_path = Path(self.temp_dir) / "procesados" / "indices" / "indice_2026_1T.json"

        assert indice_4t_2025_path.exists(), "Debe existir índice de 4T 2025 (trimestre REAL)"
        assert not indice_1t_2026_path.exists(), "NO debe existir índice de 1T 2026"

        # Paso 3: Verificar contenido del índice 4T 2025
        with open(indice_4t_2025_path, 'r', encoding='utf-8') as f:
            indice = json.load(f)

        assert indice['trimestre'] == "4T"
        assert indice['año'] == 2025
        assert len(indice['facturas']) == 1

        factura_indice = indice['facturas'][0]
        assert factura_indice['cif_proveedor'] == "B12345678"
        assert factura_indice['num_factura'] == "F-DIC-001"
        assert factura_indice['fecha_factura'] == "2025-12-15"

        # Paso 4: Verificar que archivo se organizó en carpeta correcta
        # Debe estar en procesados/facturas/2025/12/Test_Provider (año y mes del trimestre REAL)
        archivo_organizado = Path(self.temp_dir) / "procesados" / "facturas" / "2025" / "12" / "Test_Provider" / "factura_diciembre_2025.pdf"
        assert archivo_organizado.exists(), f"Archivo debe estar en {archivo_organizado}"

    @patch('pdfplumber.open')
    def test_flujo_completo_detectar_duplicado_segunda_ejecucion(self, mock_pdf_open):
        """
        Test end-to-end: Reprocesar misma factura debe detectar duplicado.

        Flujo:
        1. Primera ejecución: Procesar con 4T 2025 → genera índice 4T 2025
        2. Segunda ejecución: Reprocesar con 1T 2026 → debe detectar duplicado
        3. Verificar que NO se crea nuevo índice 1T 2026
        4. Verificar que archivo se mueve a carpeta duplicados
        """
        # Setup
        self.crear_plantilla_test()
        pdf_path = self.crear_pdf_mock("factura_diciembre.pdf")

        mock_pdf = self.configurar_mock_extraccion(
            fecha_factura="15/12/2025",
            num_factura="F-DIC-999",
            base="500.00"
        )
        mock_pdf_open.return_value = mock_pdf

        # === PRIMERA EJECUCIÓN: Procesar con 4T 2025 ===
        extractor_1 = PDFExtractor(
            directorio_facturas=str(self.facturas_dir),
            directorio_plantillas=str(self.plantillas_dir),
            trimestre="4T",
            año="2025",
            organizar_archivos=True
        )
        extractor_1.cargar_plantillas()
        resultados_1 = extractor_1.procesar_directorio_facturas()

        assert len(resultados_1) == 1
        assert '_Error' not in resultados_1[0], "Primera ejecución no debe tener errores"

        # Verificar que se creó índice 4T 2025
        indice_4t_2025_path = Path(self.temp_dir) / "procesados" / "indices" / "indice_2025_4T.json"
        assert indice_4t_2025_path.exists()

        # Verificar que archivo se organizó correctamente
        archivo_primera_ejecucion = Path(self.temp_dir) / "procesados" / "facturas" / "2025" / "12" / "Test_Provider" / "factura_diciembre.pdf"
        assert archivo_primera_ejecucion.exists()

        # === SEGUNDA EJECUCIÓN: Reprocesar con 1T 2026 ===
        # Volver a crear PDF en directorio facturas (simular reprocesamiento)
        pdf_path_2 = self.crear_pdf_mock("factura_diciembre_duplicada.pdf")

        extractor_2 = PDFExtractor(
            directorio_facturas=str(self.facturas_dir),
            directorio_plantillas=str(self.plantillas_dir),
            trimestre="1T",
            año="2026",
            organizar_archivos=True
        )
        extractor_2.cargar_plantillas()
        resultados_2 = extractor_2.procesar_directorio_facturas()

        # En la segunda ejecución, puede que no se agregue a resultados si se detecta como duplicado
        # antes de llegar a la etapa de extracción completa

        # Verificaciones críticas:
        # 1. NO debe existir índice de 1T 2026
        indice_1t_2026_path = Path(self.temp_dir) / "procesados" / "indices" / "indice_2026_1T.json"
        assert not indice_1t_2026_path.exists(), "NO debe crear índice de 1T 2026"

        # 2. Índice de 4T 2025 debe seguir teniendo solo 1 factura
        with open(indice_4t_2025_path, 'r', encoding='utf-8') as f:
            indice_final = json.load(f)
        assert len(indice_final['facturas']) == 1, "Índice 4T 2025 debe tener solo 1 factura (no duplicados)"

        # 3. Archivo duplicado debe estar en carpeta duplicados/2025/4T/
        carpeta_duplicados = Path(self.temp_dir) / "procesados" / "duplicados" / "2025" / "4T"
        assert carpeta_duplicados.exists(), "Debe existir carpeta de duplicados"

    @patch('pdfplumber.open')
    def test_flujo_multiples_facturas_diferentes_trimestres(self, mock_pdf_open):
        """
        Test end-to-end: Procesar tres facturas de trimestres diferentes.

        Verifica que cada factura se indexa en su trimestre REAL correcto.
        """
        # Setup
        self.crear_plantilla_test()

        # Crear PDFs con fechas específicas
        self.crear_pdf_mock("factura_A_enero.pdf")
        self.crear_pdf_mock("factura_B_julio.pdf")
        self.crear_pdf_mock("factura_C_octubre.pdf")

        # Configurar mock basado en nombre de archivo
        def mock_pdf_factory(pdf_path):
            path_str = str(pdf_path)

            if "enero" in path_str:
                return self.configurar_mock_extraccion(
                    fecha_factura="15/01/2025",
                    num_factura="F-ENE-001",
                    base="100.00"
                )
            elif "julio" in path_str:
                return self.configurar_mock_extraccion(
                    fecha_factura="15/07/2025",
                    num_factura="F-JUL-001",
                    base="200.00"
                )
            elif "octubre" in path_str:
                return self.configurar_mock_extraccion(
                    fecha_factura="15/10/2025",
                    num_factura="F-OCT-001",
                    base="300.00"
                )

            # Default
            return self.configurar_mock_extraccion()

        mock_pdf_open.side_effect = lambda path: mock_pdf_factory(path)

        # Procesar con trimestre usuario arbitrario (2T 2025)
        extractor = PDFExtractor(
            directorio_facturas=str(self.facturas_dir),
            directorio_plantillas=str(self.plantillas_dir),
            trimestre="2T",
            año="2025",
            organizar_archivos=True
        )
        extractor.cargar_plantillas()
        resultados = extractor.procesar_directorio_facturas()

        # Verificar que se procesaron las facturas
        assert len(resultados) == 3, "Debe haber procesado 3 facturas"

        # Verificar índices por trimestre REAL
        indices_dir = Path(self.temp_dir) / "procesados" / "indices"

        # Debe existir índice para 1T, 3T y 4T
        indice_1t = indices_dir / "indice_2025_1T.json"
        indice_3t = indices_dir / "indice_2025_3T.json"
        indice_4t = indices_dir / "indice_2025_4T.json"

        assert indice_1t.exists(), "Debe existir índice 1T 2025"
        assert indice_3t.exists(), "Debe existir índice 3T 2025"
        assert indice_4t.exists(), "Debe existir índice 4T 2025"

        # Verificar contenido de cada índice
        with open(indice_1t, 'r', encoding='utf-8') as f:
            idx_1t = json.load(f)
        assert len(idx_1t['facturas']) == 1, "1T debe tener 1 factura"
        assert idx_1t['facturas'][0]['num_factura'] == "F-ENE-001"

        with open(indice_3t, 'r', encoding='utf-8') as f:
            idx_3t = json.load(f)
        assert len(idx_3t['facturas']) == 1, "3T debe tener 1 factura"
        assert idx_3t['facturas'][0]['num_factura'] == "F-JUL-001"

        with open(indice_4t, 'r', encoding='utf-8') as f:
            idx_4t = json.load(f)
        assert len(idx_4t['facturas']) == 1, "4T debe tener 1 factura"
        assert idx_4t['facturas'][0]['num_factura'] == "F-OCT-001"

    @patch('pdfplumber.open')
    def test_verificar_estructura_indice_completa(self, mock_pdf_open):
        """
        Test end-to-end: Verificar que el índice contiene todos los campos necesarios.
        """
        # Setup
        self.crear_plantilla_test()
        pdf_path = self.crear_pdf_mock("factura_completa.pdf")

        mock_pdf = self.configurar_mock_extraccion(
            fecha_factura="20/03/2025",
            num_factura="F-MAR-123",
            base="999.99"
        )
        mock_pdf_open.return_value = mock_pdf

        # Procesar
        extractor = PDFExtractor(
            directorio_facturas=str(self.facturas_dir),
            directorio_plantillas=str(self.plantillas_dir),
            trimestre="1T",
            año="2025",
            organizar_archivos=True
        )
        extractor.cargar_plantillas()
        extractor.procesar_directorio_facturas()

        # Verificar índice
        indice_path = Path(self.temp_dir) / "procesados" / "indices" / "indice_2025_1T.json"
        assert indice_path.exists()

        with open(indice_path, 'r', encoding='utf-8') as f:
            indice = json.load(f)

        # Verificar estructura del índice
        assert 'trimestre' in indice
        assert 'año' in indice
        assert 'facturas' in indice
        assert indice['trimestre'] == "1T"
        assert indice['año'] == 2025
        assert len(indice['facturas']) == 1

        # Verificar estructura de factura en índice
        factura_idx = indice['facturas'][0]
        campos_requeridos = [
            'cif_proveedor',
            'fecha_factura',
            'num_factura',
            'nombre_archivo',
            'ruta_completa',
            'fecha_procesamiento',
            'hash_md5'
        ]

        for campo in campos_requeridos:
            assert campo in factura_idx, f"Falta campo '{campo}' en índice"
            assert factura_idx[campo], f"Campo '{campo}' está vacío"

        # Verificar valores específicos
        assert factura_idx['cif_proveedor'] == "B12345678"
        assert factura_idx['num_factura'] == "F-MAR-123"
        assert factura_idx['fecha_factura'] == "2025-03-20"
        assert "factura_completa.pdf" in factura_idx['nombre_archivo']
        assert len(factura_idx['hash_md5']) == 32, "Hash MD5 debe tener 32 caracteres"
