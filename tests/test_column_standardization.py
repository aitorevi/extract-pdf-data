"""
Tests para la estandarización de nombres de columnas - Issue #3

Valida que:
1. Los nombres de columnas estándar se aplican correctamente
2. El mapeo de campos de plantillas funciona
3. Los campos no presentes quedan en blanco
4. Los metadatos (campos con _) no se exportan
5. Trimestre y año se asignan correctamente
"""

import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock
from src.pdf_extractor import PDFExtractor
from src.excel_exporter import ExcelExporter


class TestColumnStandardization:
    """Tests para la estandarización de nombres de columnas."""

    def test_mapeo_campos_existe(self):
        """Verifica que el mapeo de campos está definido."""
        assert hasattr(PDFExtractor, 'MAPEO_CAMPOS')
        assert isinstance(PDFExtractor.MAPEO_CAMPOS, dict)
        assert len(PDFExtractor.MAPEO_CAMPOS) > 0

    def test_mapeo_campos_contiene_campos_esperados(self):
        """Verifica que el mapeo contiene los campos esperados."""
        mapeo = PDFExtractor.MAPEO_CAMPOS

        # Verificar que los campos comunes están mapeados
        assert 'num-factura' in mapeo
        assert 'fecha-factura' in mapeo
        assert 'base' in mapeo

        # Verificar que mapean a nombres estándar
        assert mapeo['num-factura'] == 'NumFactura'
        assert mapeo['fecha-factura'] == 'FechaFactura'
        assert mapeo['base'] == 'Base'

    def test_pdf_extractor_acepta_trimestre_y_año(self):
        """Verifica que PDFExtractor acepta parámetros trimestre y año."""
        extractor = PDFExtractor(trimestre="Q1", año="2025")

        assert extractor.trimestre == "Q1"
        assert extractor.año == "2025"

    def test_pdf_extractor_valores_por_defecto(self):
        """Verifica valores por defecto cuando no se pasan trimestre y año."""
        extractor = PDFExtractor()

        assert extractor.trimestre == ""
        assert extractor.año == ""

    def test_columnas_estandar_en_datos_extraidos(self, tmp_path):
        """Verifica que los datos extraídos contienen las columnas estándar."""
        # Crear plantilla de prueba
        plantilla_dir = tmp_path / "plantillas"
        plantilla_dir.mkdir()

        plantilla = {
            "proveedor_id": "B12345678",
            "cif_proveedor": "B12345678",  # Necesario para que el CIF aparezca en datos extraídos
            "nombre_proveedor": "Test Provider",
            "campos": [
                {
                    "nombre": "num-factura",
                    "coordenadas": [100, 100, 200, 120],
                    "tipo": "texto"
                },
                {
                    "nombre": "base",
                    "coordenadas": [100, 150, 200, 170],
                    "tipo": "numerico"
                }
            ]
        }

        with open(plantilla_dir / "test.json", "w", encoding="utf-8") as f:
            json.dump(plantilla, f)

        # Crear PDFExtractor
        extractor = PDFExtractor(
            directorio_plantillas=str(plantilla_dir),
            trimestre="Q1",
            año="2025"
        )
        extractor.cargar_plantillas()

        # Mock de pdfplumber
        with patch('src.pdf_extractor.pdfplumber.open') as mock_pdf:
            mock_page = MagicMock()
            mock_page.crop.return_value.extract_text.return_value = "TEST123"
            mock_pdf.return_value.__enter__.return_value.pages = [mock_page]

            # Extraer datos - usar nombre del archivo JSON como key (sin .json)
            datos = extractor.extraer_datos_factura("test.pdf", "test")

            # Verificar que tiene todas las columnas estándar
            columnas_esperadas = [
                'CIF', 'FechaFactura', 'Trimestre', 'Año',
                'FechaVto', 'NumFactura', 'FechaPago', 'Base', 'ComPaypal'
            ]

            for columna in columnas_esperadas:
                assert columna in datos, f"Falta columna estándar: {columna}"

            # Verificar valores
            assert datos['CIF'] == "B12345678"
            assert datos['Trimestre'] == "Q1"
            assert datos['Año'] == "2025"

    def test_campos_no_en_plantilla_quedan_vacios(self, tmp_path):
        """Verifica que los campos no presentes en la plantilla quedan vacíos."""
        # Crear plantilla con solo 2 campos
        plantilla_dir = tmp_path / "plantillas"
        plantilla_dir.mkdir()

        plantilla = {
            "proveedor_id": "B12345678",
            "cif_proveedor": "B12345678",  # Necesario para que el CIF aparezca en datos extraídos
            "nombre_proveedor": "Test Provider",
            "campos": [
                {
                    "nombre": "num-factura",
                    "coordenadas": [100, 100, 200, 120],
                    "tipo": "texto"
                }
            ]
        }

        with open(plantilla_dir / "test.json", "w", encoding="utf-8") as f:
            json.dump(plantilla, f)

        extractor = PDFExtractor(
            directorio_plantillas=str(plantilla_dir),
            trimestre="Q2",
            año="2025"
        )
        extractor.cargar_plantillas()

        with patch('src.pdf_extractor.pdfplumber.open') as mock_pdf:
            mock_page = MagicMock()
            mock_page.crop.return_value.extract_text.return_value = "FAC-001"
            mock_pdf.return_value.__enter__.return_value.pages = [mock_page]

            # La key ahora es el nombre del archivo JSON (sin .json)
            datos = extractor.extraer_datos_factura("test.pdf", "test")

            # Campos que no están en la plantilla deben estar vacíos
            assert datos['FechaVto'] == ''
            assert datos['FechaPago'] == ''
            assert datos['ComPaypal'] == ''
            assert datos['Base'] == ''
            assert datos['FechaFactura'] == ''

            # Campo que sí está debe tener valor
            assert datos['NumFactura'] == "FAC-001"

    def test_metadatos_tienen_prefijo_underscore(self, tmp_path):
        """Verifica que los metadatos internos tienen prefijo _."""
        plantilla_dir = tmp_path / "plantillas"
        plantilla_dir.mkdir()

        plantilla = {
            "proveedor_id": "B12345678",
            "cif_proveedor": "B12345678",  # Necesario para que el CIF aparezca en datos extraídos
            "nombre_proveedor": "Test Provider",
            "campos": []
        }

        with open(plantilla_dir / "test.json", "w", encoding="utf-8") as f:
            json.dump(plantilla, f)

        extractor = PDFExtractor(directorio_plantillas=str(plantilla_dir))
        extractor.cargar_plantillas()

        with patch('src.pdf_extractor.pdfplumber.open') as mock_pdf:
            mock_page = MagicMock()
            mock_pdf.return_value.__enter__.return_value.pages = [mock_page]

            # La key ahora es el nombre del archivo JSON (sin .json)
            datos = extractor.extraer_datos_factura("test.pdf", "test")

            # Verificar que los metadatos tienen prefijo _
            assert '_Archivo' in datos
            assert '_Proveedor_Nombre' in datos
            assert '_Fecha_Procesamiento' in datos

    def test_filtrar_columnas_estandar(self):
        """Verifica que _filtrar_columnas_estandar excluye campos con _ y errores."""
        datos = [
            {
                'CIF': 'B12345678',
                'NumFactura': 'FAC-001',
                'Base': '100.00',
                '_Archivo': 'test.pdf',
                '_Proveedor_Nombre': 'Test',
                '_Fecha_Procesamiento': '2025-01-23'
            },
            {
                'CIF': 'B87654321',
                'NumFactura': 'FAC-002',
                'Base': '200.00',
                '_Archivo': 'test2.pdf',
                '_Error': 'Some error'  # Este registro será excluido por defecto
            }
        ]

        exporter = ExcelExporter(datos)
        datos_filtrados = exporter._filtrar_columnas_estandar(datos)

        # Por defecto excluye registros con _Error, así que solo debe haber 1 registro
        assert len(datos_filtrados) == 1

        # Verificar que no hay campos con _
        for registro in datos_filtrados:
            for campo in registro.keys():
                assert not campo.startswith('_'), f"Campo {campo} no debería estar en datos filtrados"

        # Verificar que el primer registro tiene los campos estándar
        assert datos_filtrados[0]['CIF'] == 'B12345678'
        assert datos_filtrados[0]['NumFactura'] == 'FAC-001'
        assert datos_filtrados[0]['Base'] == '100.00'

    def test_exportacion_excel_solo_columnas_estandar(self, tmp_path):
        """Verifica que la exportación Excel solo incluye columnas estándar."""
        datos = [
            {
                'CIF': 'B12345678',
                'FechaFactura': '01/01/2025',
                'Trimestre': 'Q1',
                'Año': '2025',
                'FechaVto': '',
                'NumFactura': 'FAC-001',
                'FechaPago': '',
                'Base': '100.00',
                'ComPaypal': '',
                '_Archivo': 'test.pdf',
                '_Proveedor_Nombre': 'Test Provider'
            }
        ]

        output_dir = tmp_path / "resultados"
        output_dir.mkdir()

        exporter = ExcelExporter(datos, directorio_salida=str(output_dir))
        archivo = exporter.exportar_excel_basico("test_columnas.xlsx")

        # Verificar que el archivo se creó
        assert os.path.exists(archivo)

        # Leer el Excel y verificar columnas
        import pandas as pd
        df = pd.read_excel(archivo)

        # Verificar que no hay columnas con _
        for columna in df.columns:
            assert not columna.startswith('_'), f"Columna {columna} no debería estar en Excel"

        # Verificar que las columnas estándar están
        columnas_esperadas = [
            'CIF', 'FechaFactura', 'Trimestre', 'Año',
            'FechaVto', 'NumFactura', 'FechaPago', 'Base', 'ComPaypal'
        ]

        for columna in columnas_esperadas:
            assert columna in df.columns, f"Falta columna: {columna}"

    def test_exportacion_csv_solo_columnas_estandar(self, tmp_path):
        """Verifica que la exportación CSV solo incluye columnas estándar."""
        datos = [
            {
                'CIF': 'B12345678',
                'NumFactura': 'FAC-001',
                'Base': '100.00',
                '_Archivo': 'test.pdf'
            }
        ]

        output_dir = tmp_path / "resultados"
        output_dir.mkdir()

        exporter = ExcelExporter(datos, directorio_salida=str(output_dir))
        archivo = exporter.exportar_csv("test_columnas.csv")

        assert os.path.exists(archivo)

        # Leer CSV
        import pandas as pd
        df = pd.read_csv(archivo, sep=';')

        # Verificar que no hay columnas con _
        for columna in df.columns:
            assert not columna.startswith('_')

    def test_exportacion_json_solo_columnas_estandar(self, tmp_path):
        """Verifica que la exportación JSON solo incluye columnas estándar."""
        datos = [
            {
                'CIF': 'B12345678',
                'NumFactura': 'FAC-001',
                '_Archivo': 'test.pdf',
                '_Proveedor_Nombre': 'Test'
            }
        ]

        output_dir = tmp_path / "resultados"
        output_dir.mkdir()

        exporter = ExcelExporter(datos, directorio_salida=str(output_dir))
        archivo = exporter.exportar_json("test_columnas.json")

        assert os.path.exists(archivo)

        # Leer JSON
        with open(archivo, 'r', encoding='utf-8') as f:
            contenido = json.load(f)

        # Verificar que no hay campos con _ en las facturas
        for factura in contenido['facturas']:
            for campo in factura.keys():
                assert not campo.startswith('_'), f"Campo {campo} no debería estar en JSON"

    def test_formato_fecha_dd_mm_yyyy(self):
        """Verifica que las fechas se normalizan al formato DD/MM/YYYY."""
        extractor = PDFExtractor()

        # Probar diferentes formatos de entrada
        formatos_entrada = [
            ('15/01/2025', '15/01/2025'),      # Ya en formato correcto
            ('15-01-2025', '15/01/2025'),      # Con guiones
            ('2025/01/15', '15/01/2025'),      # Formato YYYY/MM/DD
            ('2025-01-15', '15/01/2025'),      # Formato YYYY-MM-DD con guiones
            ('01/03/2025', '01/03/2025'),      # Con día de un dígito
            ('9/3/2025', '09/03/2025'),        # Sin ceros a la izquierda
        ]

        for entrada, esperado in formatos_entrada:
            resultado = extractor.limpiar_fecha(entrada)
            assert resultado == esperado, f"Entrada '{entrada}' debería producir '{esperado}', pero produjo '{resultado}'"

    def test_orden_columnas_correcto(self, tmp_path):
        """Verifica que el orden de las columnas es el correcto."""
        datos = [
            {
                'CIF': 'B12345678',
                'FechaFactura': '01/01/2025',
                'Trimestre': 'Q1',
                'Año': '2025',
                'FechaVto': '31/01/2025',
                'NumFactura': 'FAC-001',
                'FechaPago': '15/01/2025',
                'Base': '100.00',
                'ComPaypal': '2.50'
            }
        ]

        output_dir = tmp_path / "resultados"
        output_dir.mkdir()

        exporter = ExcelExporter(datos, directorio_salida=str(output_dir))
        archivo = exporter.exportar_excel_basico("test_orden.xlsx")

        import pandas as pd
        df = pd.read_excel(archivo)

        # Verificar orden esperado
        orden_esperado = [
            'CIF', 'FechaFactura', 'Trimestre', 'Año',
            'FechaVto', 'NumFactura', 'FechaPago', 'Base', 'ComPaypal'
        ]

        columnas_actuales = list(df.columns)
        assert columnas_actuales == orden_esperado, f"Orden incorrecto: {columnas_actuales}"


@pytest.mark.integration
class TestIntegrationColumnStandardization:
    """Tests de integración para la estandarización de columnas."""

    def test_flujo_completo_con_columnas_estandar(self, tmp_path):
        """Test de integración del flujo completo con columnas estándar."""
        # Crear estructura de directorios
        plantilla_dir = tmp_path / "plantillas"
        plantilla_dir.mkdir()
        output_dir = tmp_path / "resultados"
        output_dir.mkdir()

        # Crear plantilla
        plantilla = {
            "proveedor_id": "B12345678",
            "cif_proveedor": "B12345678",  # Campo necesario para el CIF en datos extraídos
            "nombre_proveedor": "Test Provider S.L.",
            "campos": [
                {
                    "nombre": "CIF_Cliente",
                    "coordenadas": [100, 90, 200, 95],
                    "tipo": "texto",
                    "es_identificacion": True
                },
                {
                    "nombre": "num-factura",
                    "coordenadas": [100, 100, 200, 120],
                    "tipo": "texto"
                },
                {
                    "nombre": "fecha-factura",
                    "coordenadas": [100, 130, 200, 150],
                    "tipo": "fecha"
                },
                {
                    "nombre": "base",
                    "coordenadas": [100, 160, 200, 180],
                    "tipo": "numerico"
                }
            ]
        }

        with open(plantilla_dir / "test_provider.json", "w", encoding="utf-8") as f:
            json.dump(plantilla, f)

        # Crear extractor
        extractor = PDFExtractor(
            directorio_plantillas=str(plantilla_dir),
            trimestre="Q1",
            año="2025"
        )
        extractor.cargar_plantillas()

        # Mock de PDF
        with patch('src.pdf_extractor.pdfplumber.open') as mock_pdf:
            mock_page = MagicMock()

            # Simular diferentes valores para diferentes campos
            def mock_extract(bbox):
                mock_result = MagicMock()
                if bbox[1] < 96:  # CIF_Cliente
                    mock_result.extract_text.return_value = "E98530876"
                elif bbox[1] < 125:  # num-factura
                    mock_result.extract_text.return_value = "FAC-2025-001"
                elif bbox[1] < 155:  # fecha-factura
                    mock_result.extract_text.return_value = "15/01/2025"
                else:  # base
                    mock_result.extract_text.return_value = "1.234,56"
                return mock_result

            mock_page.crop = mock_extract
            mock_pdf.return_value.__enter__.return_value.pages = [mock_page]

            # Extraer datos - el nombre del archivo es test_provider.json, así que key es "test_provider"
            datos = extractor.extraer_datos_factura("test.pdf", "test_provider")

            # Crear exportador
            exporter = ExcelExporter([datos], directorio_salida=str(output_dir))

            # Exportar
            archivo_excel = exporter.exportar_excel_basico("integracion_test.xlsx")

            # Verificar archivo
            import pandas as pd
            df = pd.read_excel(archivo_excel)

            # Verificar que tiene exactamente 1 fila
            assert len(df) == 1

            # Verificar columnas estándar
            assert 'CIF' in df.columns
            assert 'Trimestre' in df.columns
            assert 'Año' in df.columns

            # Verificar valores
            assert df.iloc[0]['CIF'] == 'B12345678'
            assert df.iloc[0]['Trimestre'] == 'Q1'
            assert str(df.iloc[0]['Año']) == '2025'  # Pandas puede convertir a int
            assert df.iloc[0]['NumFactura'] == 'FAC-2025-001'

            # Verificar que no hay metadatos
            assert '_Archivo' not in df.columns
            assert '_Proveedor_Nombre' not in df.columns
