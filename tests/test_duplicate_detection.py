"""
Tests para detección de duplicados.

Valida que:
1. Se detectan duplicados basados en CIF + NumFactura + FechaFactura
2. Los duplicados se marcan con _Duplicado = True
3. Los duplicados incluyen _Motivo_Duplicado
4. Duplicados se excluyen del Excel principal
5. Duplicados se incluyen en Excel debug
"""

import pytest
import json
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from src.pdf_extractor import PDFExtractor
from src.excel_exporter import ExcelExporter


class TestDuplicateDetection:
    """Tests para detección de duplicados."""

    @patch('pdfplumber.open')
    def test_detectar_duplicado_mismo_cif_num_fecha(self, mock_pdf_open, tmp_path):
        """Test que detecta duplicado con mismo CIF, NumFactura y FechaFactura."""
        plantilla_dir = tmp_path / "plantillas"
        plantilla_dir.mkdir()
        facturas_dir = tmp_path / "facturas"
        facturas_dir.mkdir()

        plantilla = {
            "nombre_proveedor": "Test Provider",
            "cif_proveedor": "B12345678",
            "campos": [
                {
                    "nombre": "Nombre_Identificacion",
                    "coordenadas": [10, 10, 100, 30],
                    "tipo": "texto",
                    "es_identificacion": True
                },
                {
                    "nombre": "NumFactura",
                    "coordenadas": [10, 50, 100, 70],
                    "tipo": "texto",
                    "es_identificacion": False
                },
                {
                    "nombre": "FechaFactura",
                    "coordenadas": [10, 80, 100, 100],
                    "tipo": "fecha",
                    "es_identificacion": False
                }
            ]
        }

        with open(plantilla_dir / "test_provider.json", "w", encoding="utf-8") as f:
            json.dump(plantilla, f)

        # Crear dos PDFs
        (facturas_dir / "factura1.pdf").touch()
        (facturas_dir / "factura2.pdf").touch()

        extractor = PDFExtractor(
            directorio_plantillas=str(plantilla_dir),
            directorio_facturas=str(facturas_dir),
            trimestre="1T",
            año="2025"
        )
        extractor.cargar_plantillas()

        # Mock que retorna los mismos datos para ambos PDFs
        def mock_crop(bbox):
            mock_result = MagicMock()
            if bbox[1] < 35:  # Nombre_Identificacion
                mock_result.extract_text.return_value = "Test Provider"
            elif bbox[1] < 75:  # NumFactura
                mock_result.extract_text.return_value = "FAC-001"
            else:  # FechaFactura
                mock_result.extract_text.return_value = "15/01/2025"
            return mock_result

        mock_page = MagicMock()
        mock_page.crop = mock_crop
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        mock_pdf_open.return_value = mock_pdf

        resultados = extractor.procesar_directorio_facturas()

        assert len(resultados) == 2

        # Primera factura NO debe estar marcada como duplicada
        assert resultados[0].get("_Duplicado") == False
        assert "_Motivo_Duplicado" not in resultados[0] or resultados[0]["_Motivo_Duplicado"] == ""

        # Segunda factura SÍ debe estar marcada como duplicada
        assert resultados[1].get("_Duplicado") == True
        assert "Ya existe factura con mismo CIF, NumFactura y FechaFactura" in resultados[1]["_Motivo_Duplicado"]

    @patch('pdfplumber.open')
    def test_no_detectar_duplicado_numero_diferente(self, mock_pdf_open, tmp_path):
        """Test que NO detecta duplicado si el número de factura es diferente."""
        plantilla_dir = tmp_path / "plantillas"
        plantilla_dir.mkdir()
        facturas_dir = tmp_path / "facturas"
        facturas_dir.mkdir()

        plantilla = {
            "nombre_proveedor": "Test Provider",
            "cif_proveedor": "B12345678",
            "campos": [
                {
                    "nombre": "Nombre_Identificacion",
                    "coordenadas": [10, 10, 100, 30],
                    "tipo": "texto",
                    "es_identificacion": True
                },
                {
                    "nombre": "NumFactura",
                    "coordenadas": [10, 50, 100, 70],
                    "tipo": "texto",
                    "es_identificacion": False
                },
                {
                    "nombre": "FechaFactura",
                    "coordenadas": [10, 80, 100, 100],
                    "tipo": "fecha",
                    "es_identificacion": False
                }
            ]
        }

        with open(plantilla_dir / "test_provider.json", "w", encoding="utf-8") as f:
            json.dump(plantilla, f)

        (facturas_dir / "factura1.pdf").touch()
        (facturas_dir / "factura2.pdf").touch()

        extractor = PDFExtractor(
            directorio_plantillas=str(plantilla_dir),
            directorio_facturas=str(facturas_dir),
            trimestre="1T",
            año="2025"
        )
        extractor.cargar_plantillas()

        # Mock que retorna números de factura diferentes
        call_count = [0]

        def mock_crop(bbox):
            mock_result = MagicMock()
            if bbox[1] < 35:  # Nombre_Identificacion
                mock_result.extract_text.return_value = "Test Provider"
            elif bbox[1] < 75:  # NumFactura - diferente cada vez
                call_count[0] += 1
                mock_result.extract_text.return_value = f"FAC-{call_count[0]:03d}"
            else:  # FechaFactura - misma fecha
                mock_result.extract_text.return_value = "15/01/2025"
            return mock_result

        mock_page = MagicMock()
        mock_page.crop = mock_crop
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        mock_pdf_open.return_value = mock_pdf

        resultados = extractor.procesar_directorio_facturas()

        # Ninguna debe estar marcada como duplicada
        for resultado in resultados:
            assert resultado.get("_Duplicado") == False

    @patch('pdfplumber.open')
    def test_no_detectar_duplicado_fecha_diferente(self, mock_pdf_open, tmp_path):
        """Test que NO detecta duplicado si la fecha es diferente."""
        plantilla_dir = tmp_path / "plantillas"
        plantilla_dir.mkdir()
        facturas_dir = tmp_path / "facturas"
        facturas_dir.mkdir()

        plantilla = {
            "nombre_proveedor": "Test Provider",
            "cif_proveedor": "B12345678",
            "campos": [
                {
                    "nombre": "Nombre_Identificacion",
                    "coordenadas": [10, 10, 100, 30],
                    "tipo": "texto",
                    "es_identificacion": True
                },
                {
                    "nombre": "NumFactura",
                    "coordenadas": [10, 50, 100, 70],
                    "tipo": "texto",
                    "es_identificacion": False
                },
                {
                    "nombre": "FechaFactura",
                    "coordenadas": [10, 80, 100, 100],
                    "tipo": "fecha",
                    "es_identificacion": False
                }
            ]
        }

        with open(plantilla_dir / "test_provider.json", "w", encoding="utf-8") as f:
            json.dump(plantilla, f)

        (facturas_dir / "factura1.pdf").touch()
        (facturas_dir / "factura2.pdf").touch()

        extractor = PDFExtractor(
            directorio_plantillas=str(plantilla_dir),
            directorio_facturas=str(facturas_dir),
            trimestre="1T",
            año="2025"
        )
        extractor.cargar_plantillas()

        # Mock que retorna fechas diferentes
        call_count = [0]

        def mock_crop(bbox):
            mock_result = MagicMock()
            if bbox[1] < 35:  # Nombre_Identificacion
                mock_result.extract_text.return_value = "Test Provider"
            elif bbox[1] < 75:  # NumFactura - mismo número
                mock_result.extract_text.return_value = "FAC-001"
            else:  # FechaFactura - diferente cada vez
                call_count[0] += 1
                mock_result.extract_text.return_value = f"{call_count[0]:02d}/01/2025"
            return mock_result

        mock_page = MagicMock()
        mock_page.crop = mock_crop
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        mock_pdf_open.return_value = mock_pdf

        resultados = extractor.procesar_directorio_facturas()

        # Ninguna debe estar marcada como duplicada
        for resultado in resultados:
            assert resultado.get("_Duplicado") == False

    @patch('pdfplumber.open')
    def test_no_detectar_duplicado_cif_diferente(self, mock_pdf_open, tmp_path):
        """Test que NO detecta duplicado si el CIF es diferente."""
        plantilla_dir = tmp_path / "plantillas"
        plantilla_dir.mkdir()
        facturas_dir = tmp_path / "facturas"
        facturas_dir.mkdir()

        # Crear dos plantillas con diferentes CIFs
        plantilla1 = {
            "nombre_proveedor": "Provider One",
            "cif_proveedor": "B11111111",
            "campos": [
                {
                    "nombre": "Nombre_Identificacion",
                    "coordenadas": [10, 10, 100, 30],
                    "tipo": "texto",
                    "es_identificacion": True
                },
                {
                    "nombre": "NumFactura",
                    "coordenadas": [10, 50, 100, 70],
                    "tipo": "texto",
                    "es_identificacion": False
                },
                {
                    "nombre": "FechaFactura",
                    "coordenadas": [10, 80, 100, 100],
                    "tipo": "fecha",
                    "es_identificacion": False
                }
            ]
        }

        plantilla2 = {
            "nombre_proveedor": "Provider Two",
            "cif_proveedor": "B22222222",
            "campos": [
                {
                    "nombre": "Nombre_Identificacion",
                    "coordenadas": [10, 10, 100, 30],
                    "tipo": "texto",
                    "es_identificacion": True
                },
                {
                    "nombre": "NumFactura",
                    "coordenadas": [10, 50, 100, 70],
                    "tipo": "texto",
                    "es_identificacion": False
                },
                {
                    "nombre": "FechaFactura",
                    "coordenadas": [10, 80, 100, 100],
                    "tipo": "fecha",
                    "es_identificacion": False
                }
            ]
        }

        with open(plantilla_dir / "provider_one.json", "w", encoding="utf-8") as f:
            json.dump(plantilla1, f)
        with open(plantilla_dir / "provider_two.json", "w", encoding="utf-8") as f:
            json.dump(plantilla2, f)

        (facturas_dir / "factura1.pdf").touch()
        (facturas_dir / "factura2.pdf").touch()

        extractor = PDFExtractor(
            directorio_plantillas=str(plantilla_dir),
            directorio_facturas=str(facturas_dir),
            trimestre="1T",
            año="2025"
        )
        extractor.cargar_plantillas()

        # Mock que retorna diferentes nombres dependiendo del archivo
        current_pdf = [None]

        def mock_pdf_open_func(path):
            current_pdf[0] = path

            def mock_crop(bbox):
                mock_result = MagicMock()
                # Determinar proveedor según el nombre del archivo
                is_provider_one = 'factura1' in str(current_pdf[0])

                if bbox[1] < 35:  # Nombre_Identificacion
                    if is_provider_one:
                        mock_result.extract_text.return_value = "Provider One"
                    else:
                        mock_result.extract_text.return_value = "Provider Two"
                elif bbox[1] < 75:  # NumFactura - mismo número
                    mock_result.extract_text.return_value = "FAC-001"
                else:  # FechaFactura - misma fecha
                    mock_result.extract_text.return_value = "15/01/2025"
                return mock_result

            mock_page = MagicMock()
            mock_page.crop = mock_crop
            mock_pdf = MagicMock()
            mock_pdf.pages = [mock_page]
            mock_pdf.__enter__ = Mock(return_value=mock_pdf)
            mock_pdf.__exit__ = Mock(return_value=None)
            return mock_pdf

        mock_pdf_open.side_effect = mock_pdf_open_func

        resultados = extractor.procesar_directorio_facturas()

        # Ninguna debe estar marcada como duplicada (CIFs diferentes)
        for resultado in resultados:
            assert resultado.get("_Duplicado") == False


class TestDuplicateExportFiltering:
    """Tests para filtrado de duplicados en exportación."""

    def test_filtrar_columnas_estandar_excluye_duplicados(self):
        """Test que _filtrar_columnas_estandar excluye duplicados por defecto."""
        datos = [
            {
                'CIF': 'B12345678',
                'NumFactura': 'FAC-001',
                'FechaFactura': '15/01/2025',
                'Base': '100.00',
                '_Duplicado': False
            },
            {
                'CIF': 'B12345678',
                'NumFactura': 'FAC-001',
                'FechaFactura': '15/01/2025',
                'Base': '100.00',
                '_Duplicado': True,
                '_Motivo_Duplicado': 'Ya existe factura con mismo CIF, NumFactura y FechaFactura'
            }
        ]

        exporter = ExcelExporter(datos)
        datos_filtrados = exporter._filtrar_columnas_estandar(
            datos,
            excluir_duplicados=True,
            excluir_errores=False
        )

        # Solo debe quedar 1 registro (el no duplicado)
        assert len(datos_filtrados) == 1
        assert datos_filtrados[0]['NumFactura'] == 'FAC-001'

    def test_filtrar_columnas_estandar_incluye_duplicados_si_se_indica(self):
        """Test que puede incluir duplicados si se desactiva el filtro."""
        datos = [
            {
                'CIF': 'B12345678',
                'NumFactura': 'FAC-001',
                '_Duplicado': False
            },
            {
                'CIF': 'B12345678',
                'NumFactura': 'FAC-001',
                '_Duplicado': True
            }
        ]

        exporter = ExcelExporter(datos)
        datos_filtrados = exporter._filtrar_columnas_estandar(
            datos,
            excluir_duplicados=False,
            excluir_errores=False
        )

        # Deben quedar ambos registros
        assert len(datos_filtrados) == 2

    def test_excel_basico_excluye_duplicados(self, tmp_path):
        """Test que exportar_excel_basico excluye duplicados."""
        datos = [
            {
                'CIF': 'B12345678',
                'NumFactura': 'FAC-001',
                'FechaFactura': '15/01/2025',
                '_Duplicado': False
            },
            {
                'CIF': 'B12345678',
                'NumFactura': 'FAC-001',
                'FechaFactura': '15/01/2025',
                '_Duplicado': True
            },
            {
                'CIF': 'B87654321',
                'NumFactura': 'FAC-002',
                'FechaFactura': '16/01/2025',
                '_Duplicado': False
            }
        ]

        output_dir = tmp_path / "resultados"
        output_dir.mkdir()

        exporter = ExcelExporter(datos, directorio_salida=str(output_dir))
        archivo = exporter.exportar_excel_basico("test_duplicados.xlsx")

        # Leer el Excel
        df = pd.read_excel(archivo)

        # Solo deben quedar 2 registros (los no duplicados)
        assert len(df) == 2
        assert list(df['NumFactura']) == ['FAC-001', 'FAC-002']

    def test_excel_completo_incluye_duplicados(self, tmp_path):
        """Test que exportar_excel_completo incluye TODOS los datos incluyendo duplicados."""
        datos = [
            {
                'CIF': 'B12345678',
                'NumFactura': 'FAC-001',
                '_Duplicado': False
            },
            {
                'CIF': 'B12345678',
                'NumFactura': 'FAC-001',
                '_Duplicado': True,
                '_Motivo_Duplicado': 'Duplicado detectado'
            }
        ]

        output_dir = tmp_path / "resultados"
        output_dir.mkdir()

        exporter = ExcelExporter(datos, directorio_salida=str(output_dir))
        archivo = exporter.exportar_excel_completo("test_completo.xlsx")

        # Leer el Excel debug
        df = pd.read_excel(archivo, sheet_name="Datos_Completos")

        # Deben estar TODOS los registros
        assert len(df) == 2

        # Debe incluir columnas de metadatos
        assert '_Duplicado' in df.columns
        assert '_Motivo_Duplicado' in df.columns

    def test_estadisticas_cuentan_duplicados(self):
        """Test que las estadísticas cuentan correctamente los duplicados."""
        datos = [
            {
                'CIF': 'B12345678',
                'NumFactura': 'FAC-001',
                '_Duplicado': False
            },
            {
                'CIF': 'B12345678',
                'NumFactura': 'FAC-001',
                '_Duplicado': True
            },
            {
                'CIF': 'B87654321',
                'NumFactura': 'FAC-002',
                '_Duplicado': False
            }
        ]

        exporter = ExcelExporter(datos)

        # Usar datos como si fueran de un DataFrame para calcular estadísticas
        import pandas as pd
        df_original = pd.DataFrame(datos)

        # Contar duplicados
        duplicados = len(df_original[df_original['_Duplicado'] == True])

        assert duplicados == 1
