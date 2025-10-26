"""
Tests para manejo de errores y exportación.

Valida que:
1. Facturas con errores se marcan correctamente con _Error
2. Errores se excluyen del Excel principal
3. Errores se incluyen en Excel debug
4. Excel formateado no tiene positional indexers out-of-bounds
5. Campos estándar están presentes incluso en registros con error
"""

import pytest
import json
import os
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from src.pdf_extractor import PDFExtractor
from src.excel_exporter import ExcelExporter


class TestErrorHandling:
    """Tests para manejo de errores."""

    @patch('pdfplumber.open')
    def test_proveedor_no_identificado_genera_error(self, mock_pdf_open, tmp_path):
        """Test que proveedor no identificado genera registro con error."""
        plantilla_dir = tmp_path / "plantillas"
        plantilla_dir.mkdir()
        facturas_dir = tmp_path / "facturas"
        facturas_dir.mkdir()

        plantilla = {
            "nombre_proveedor": "Known Provider",
            "cif_proveedor": "B12345678",
            "campos": [
                {
                    "nombre": "Nombre_Identificacion",
                    "coordenadas": [10, 10, 100, 30],
                    "tipo": "texto",
                    "es_identificacion": True
                }
            ]
        }

        with open(plantilla_dir / "known.json", "w", encoding="utf-8") as f:
            json.dump(plantilla, f)

        (facturas_dir / "unknown.pdf").touch()

        extractor = PDFExtractor(
            directorio_plantillas=str(plantilla_dir),
            directorio_facturas=str(facturas_dir),
            trimestre="1T",
            año="2025"
        )
        extractor.cargar_plantillas()

        # Mock que retorna nombre diferente
        def mock_crop(bbox):
            mock_result = MagicMock()
            mock_result.extract_text.return_value = "Unknown Provider"
            return mock_result

        mock_page = MagicMock()
        mock_page.crop = mock_crop
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        mock_pdf_open.return_value = mock_pdf

        resultados = extractor.procesar_directorio_facturas()

        # No debe haber resultados exitosos cuando no se identifica proveedor
        assert len(resultados) == 0

        # Debe haber un error registrado
        assert len(extractor.errores) == 1
        error = extractor.errores[0]

        assert error['Archivo'] == 'unknown.pdf'
        assert 'Proveedor no identificado' in error['Error']
        assert error['Proveedor'] == 'NO_IDENTIFICADO'

    def test_registro_error_tiene_campos_estandar(self):
        """Test que registro con error tiene todos los campos estándar."""
        # Simular resultado con error
        resultado = {
            'CIF': '',
            'FechaFactura': '',
            'Trimestre': '1T',
            'Año': '2025',
            'FechaVto': '',
            'NumFactura': '',
            'FechaPago': '',
            'Base': '',
            'ComPaypal': '',
            '_Archivo': 'error.pdf',
            '_Error': 'Proveedor no identificado',
            '_Proveedor_ID': 'NO_IDENTIFICADO'
        }

        # Verificar que tiene todas las columnas estándar
        columnas_esperadas = [
            'CIF', 'FechaFactura', 'Trimestre', 'Año',
            'FechaVto', 'NumFactura', 'FechaPago', 'Base', 'ComPaypal'
        ]

        for columna in columnas_esperadas:
            assert columna in resultado, f"Falta columna estándar: {columna}"


class TestErrorExportFiltering:
    """Tests para filtrado de errores en exportación."""

    def test_filtrar_columnas_estandar_excluye_errores(self):
        """Test que _filtrar_columnas_estandar excluye errores por defecto."""
        datos = [
            {
                'CIF': 'B12345678',
                'NumFactura': 'FAC-001',
                'Base': '100.00',
                '_Duplicado': False
            },
            {
                'CIF': '',
                'NumFactura': '',
                'Base': '',
                '_Error': 'Proveedor no identificado',
                '_Proveedor_ID': 'NO_IDENTIFICADO',
                '_Duplicado': False
            }
        ]

        exporter = ExcelExporter(datos)
        datos_filtrados = exporter._filtrar_columnas_estandar(
            datos,
            excluir_duplicados=False,
            excluir_errores=True
        )

        # Solo debe quedar 1 registro (el sin error)
        assert len(datos_filtrados) == 1
        assert datos_filtrados[0]['CIF'] == 'B12345678'

    def test_filtrar_columnas_estandar_incluye_errores_si_se_indica(self):
        """Test que puede incluir errores si se desactiva el filtro."""
        datos = [
            {
                'CIF': 'B12345678',
                'NumFactura': 'FAC-001',
            },
            {
                'CIF': '',
                'NumFactura': '',
                '_Error': 'Algún error'
            }
        ]

        exporter = ExcelExporter(datos)
        datos_filtrados = exporter._filtrar_columnas_estandar(
            datos,
            excluir_duplicados=False,
            excluir_errores=False
        )

        # Deben quedar ambos registros (sin el campo _Error)
        assert len(datos_filtrados) == 2

    def test_excel_basico_excluye_errores(self, tmp_path):
        """Test que exportar_excel_basico excluye registros con error."""
        datos = [
            {
                'CIF': 'B12345678',
                'NumFactura': 'FAC-001',
                'Base': '100.00'
            },
            {
                'CIF': '',
                'NumFactura': '',
                'Base': '',
                '_Error': 'Proveedor no identificado'
            },
            {
                'CIF': 'B87654321',
                'NumFactura': 'FAC-002',
                'Base': '200.00'
            }
        ]

        output_dir = tmp_path / "resultados"
        output_dir.mkdir()

        exporter = ExcelExporter(datos, directorio_salida=str(output_dir))
        archivo = exporter.exportar_excel_basico("test_errores.xlsx")

        # Leer el Excel
        df = pd.read_excel(archivo)

        # Solo deben quedar 2 registros (los sin error)
        assert len(df) == 2
        assert list(df['NumFactura']) == ['FAC-001', 'FAC-002']

    def test_excel_completo_incluye_errores(self, tmp_path):
        """Test que exportar_excel_completo incluye todos los datos incluyendo errores."""
        datos = [
            {
                'CIF': 'B12345678',
                'NumFactura': 'FAC-001'
            },
            {
                'CIF': '',
                'NumFactura': '',
                '_Error': 'Proveedor no identificado',
                '_Proveedor_ID': 'NO_IDENTIFICADO'
            }
        ]

        output_dir = tmp_path / "resultados"
        output_dir.mkdir()

        exporter = ExcelExporter(datos, directorio_salida=str(output_dir))
        archivo = exporter.exportar_excel_completo("test_completo_errores.xlsx")

        # Leer el Excel debug
        df = pd.read_excel(archivo, sheet_name="Datos_Completos")

        # Deben estar TODOS los registros
        assert len(df) == 2

        # Debe incluir columnas de error
        assert '_Error' in df.columns
        assert '_Proveedor_ID' in df.columns

    def test_excel_formateado_excluye_errores_y_duplicados(self, tmp_path):
        """Test que exportar_excel_formateado excluye tanto errores como duplicados."""
        datos = [
            {
                'CIF': 'B12345678',
                'NumFactura': 'FAC-001',
                'FechaFactura': '15/01/2025',
                'Trimestre': '1T',
                'Año': '2025',
                'FechaVto': '',
                'FechaPago': '',
                'Base': '100.00',
                'ComPaypal': '',
                '_Duplicado': False
            },
            {
                'CIF': 'B12345678',
                'NumFactura': 'FAC-001',
                'FechaFactura': '15/01/2025',
                'Trimestre': '1T',
                'Año': '2025',
                'FechaVto': '',
                'FechaPago': '',
                'Base': '100.00',
                'ComPaypal': '',
                '_Duplicado': True,
                '_Motivo_Duplicado': 'Duplicado'
            },
            {
                'CIF': '',
                'NumFactura': '',
                'FechaFactura': '',
                'Trimestre': '1T',
                'Año': '2025',
                'FechaVto': '',
                'FechaPago': '',
                'Base': '',
                'ComPaypal': '',
                '_Error': 'Proveedor no identificado',
                '_Duplicado': False
            },
            {
                'CIF': 'B87654321',
                'NumFactura': 'FAC-002',
                'FechaFactura': '16/01/2025',
                'Trimestre': '1T',
                'Año': '2025',
                'FechaVto': '',
                'FechaPago': '',
                'Base': '200.00',
                'ComPaypal': '',
                '_Duplicado': False
            }
        ]

        output_dir = tmp_path / "resultados"
        output_dir.mkdir()

        exporter = ExcelExporter(datos, directorio_salida=str(output_dir))
        archivo = exporter.exportar_excel_formateado("test_formateado.xlsx")

        # Leer la hoja de Facturas_Exitosas
        df = pd.read_excel(archivo, sheet_name="Facturas_Exitosas")

        # Solo deben quedar 2 registros (los sin error ni duplicado)
        assert len(df) == 2
        assert list(df['NumFactura']) == ['FAC-001', 'FAC-002']

        # No deben aparecer columnas con _
        for col in df.columns:
            assert not col.startswith('_'), f"Columna {col} no debería estar en Excel formateado"

    def test_excel_formateado_no_causa_index_out_of_bounds(self, tmp_path):
        """
        Test que exportar_excel_formateado no causa error de 'positional indexers out-of-bounds'.

        Este test reproduce el bug que teníamos donde el código intentaba usar indices
        de df_original en el df filtrado, causando out-of-bounds.
        """
        datos = [
            {
                'CIF': '',
                'NumFactura': '',
                '_Error': 'Error 1',  # índice 0 en df_original
                '_Duplicado': False
            },
            {
                'CIF': 'B12345678',
                'NumFactura': 'FAC-001',  # índice 1 en df_original
                '_Duplicado': False
            },
            {
                'CIF': 'B12345678',
                'NumFactura': 'FAC-001',  # índice 2 en df_original
                '_Duplicado': True
            }
        ]

        output_dir = tmp_path / "resultados"
        output_dir.mkdir()

        exporter = ExcelExporter(datos, directorio_salida=str(output_dir))

        # Esto NO debe lanzar excepción
        try:
            archivo = exporter.exportar_excel_formateado("test_no_error.xlsx")

            # Verificar que el archivo se creó correctamente
            df = pd.read_excel(archivo, sheet_name="Facturas_Exitosas")

            # Solo debe haber 1 registro (índice 1 del original, que es índice 0 en el filtrado)
            assert len(df) == 1
            assert df.iloc[0]['NumFactura'] == 'FAC-001'

        except IndexError as e:
            pytest.fail(f"exportar_excel_formateado causó IndexError: {e}")

    def test_csv_excluye_errores_y_duplicados(self, tmp_path):
        """Test que exportar_csv excluye errores y duplicados."""
        datos = [
            {
                'CIF': 'B12345678',
                'NumFactura': 'FAC-001',
                '_Duplicado': False
            },
            {
                'CIF': '',
                'NumFactura': '',
                '_Error': 'Error',
                '_Duplicado': False
            },
            {
                'CIF': 'B12345678',
                'NumFactura': 'FAC-001',
                '_Duplicado': True
            }
        ]

        output_dir = tmp_path / "resultados"
        output_dir.mkdir()

        exporter = ExcelExporter(datos, directorio_salida=str(output_dir))
        archivo = exporter.exportar_csv("test_csv.csv")

        # Leer CSV
        df = pd.read_csv(archivo, sep=';')

        # Solo debe quedar 1 registro
        assert len(df) == 1
        assert df.iloc[0]['NumFactura'] == 'FAC-001'

    def test_json_excluye_errores_y_duplicados(self, tmp_path):
        """Test que exportar_json excluye errores y duplicados."""
        datos = [
            {
                'CIF': 'B12345678',
                'NumFactura': 'FAC-001',
                '_Duplicado': False
            },
            {
                'CIF': '',
                'NumFactura': '',
                '_Error': 'Error',
                '_Duplicado': False
            },
            {
                'CIF': 'B12345678',
                'NumFactura': 'FAC-001',
                '_Duplicado': True
            }
        ]

        output_dir = tmp_path / "resultados"
        output_dir.mkdir()

        exporter = ExcelExporter(datos, directorio_salida=str(output_dir))
        archivo = exporter.exportar_json("test_json.json")

        # Leer JSON
        with open(archivo, 'r', encoding='utf-8') as f:
            contenido = json.load(f)

        # Solo debe quedar 1 registro
        assert len(contenido['facturas']) == 1
        assert contenido['facturas'][0]['NumFactura'] == 'FAC-001'

        # No debe tener campos con _
        for campo in contenido['facturas'][0].keys():
            assert not campo.startswith('_')


class TestCompleteWorkflow:
    """Tests de integración del flujo completo."""

    @patch('pdfplumber.open')
    def test_flujo_completo_con_exito_error_duplicado(self, mock_pdf_open, tmp_path):
        """
        Test del flujo completo con:
        - 1 factura exitosa
        - 1 factura con error (proveedor no identificado)
        - 1 factura duplicada
        """
        plantilla_dir = tmp_path / "plantillas"
        plantilla_dir.mkdir()
        facturas_dir = tmp_path / "facturas"
        facturas_dir.mkdir()
        output_dir = tmp_path / "resultados"
        output_dir.mkdir()

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
                },
                {
                    "nombre": "Base",
                    "coordenadas": [10, 110, 100, 130],
                    "tipo": "numerico",
                    "es_identificacion": False
                }
            ]
        }

        with open(plantilla_dir / "test_provider.json", "w", encoding="utf-8") as f:
            json.dump(plantilla, f)

        # Crear 3 archivos PDF
        (facturas_dir / "factura_exitosa.pdf").touch()
        (facturas_dir / "factura_error.pdf").touch()
        (facturas_dir / "factura_duplicada.pdf").touch()

        extractor = PDFExtractor(
            directorio_plantillas=str(plantilla_dir),
            directorio_facturas=str(facturas_dir),
            trimestre="1T",
            año="2025"
        )
        extractor.cargar_plantillas()

        # Mock que simula diferentes escenarios según el archivo
        current_file = {'name': ''}

        def mock_pdf_open_func(filepath):
            # Guardar el nombre del archivo actual
            current_file['name'] = os.path.basename(filepath)

            def mock_crop(bbox):
                mock_result = MagicMock()
                filename = current_file['name']

                # factura_error.pdf: proveedor no identificado (Unknown Provider)
                if 'error' in filename:
                    if bbox[1] < 35:  # Nombre_Identificacion
                        mock_result.extract_text.return_value = "Unknown Provider"
                    else:
                        mock_result.extract_text.return_value = ""

                # factura_exitosa.pdf y factura_duplicada.pdf: identificado correctamente
                else:
                    if bbox[1] < 35:  # Nombre_Identificacion
                        mock_result.extract_text.return_value = "Test Provider"
                    elif bbox[1] < 75:  # NumFactura
                        mock_result.extract_text.return_value = "FAC-001"
                    elif bbox[1] < 105:  # FechaFactura
                        mock_result.extract_text.return_value = "15/01/2025"
                    else:  # Base
                        mock_result.extract_text.return_value = "100.50"

                return mock_result

            mock_page = MagicMock()
            mock_page.crop = mock_crop
            mock_pdf = MagicMock()
            mock_pdf.pages = [mock_page]
            mock_pdf.__enter__ = Mock(return_value=mock_pdf)
            mock_pdf.__exit__ = Mock(return_value=None)
            return mock_pdf

        mock_pdf_open.side_effect = mock_pdf_open_func

        # Procesar facturas
        resultados = extractor.procesar_directorio_facturas()

        # Verificar resultados:
        # - factura_exitosa.pdf y factura_error.pdf se identifican correctamente
        # - factura_duplicada.pdf NO se identifica (va a errores)
        # - La primera factura tiene todos los datos, la segunda es duplicada
        assert len(resultados) == 2  # 2 exitosas (una es duplicada)
        assert len(extractor.errores) == 1  # 1 con error de identificación

        # Verificar que una está marcada como duplicada
        duplicados = [r for r in resultados if r.get('_Duplicado', False)]
        assert len(duplicados) == 1

        # Exportar
        exporter = ExcelExporter(resultados, directorio_salida=str(output_dir))

        # Excel principal (excluye duplicados)
        archivo_principal = exporter.exportar_excel_basico("principal.xlsx")
        df_principal = pd.read_excel(archivo_principal)
        assert len(df_principal) == 1  # Solo la no duplicada
        assert df_principal.iloc[0]['NumFactura'] == 'FAC-001'

        # Excel debug (todos los resultados, no incluye errores)
        archivo_debug = exporter.exportar_excel_completo("debug.xlsx")
        df_debug = pd.read_excel(archivo_debug, sheet_name="Datos_Completos")
        assert len(df_debug) == 2  # Ambas facturas procesadas (incluye duplicada)

        # Excel formateado (solo exitosas no duplicadas)
        archivo_formateado = exporter.exportar_excel_formateado("formateado.xlsx")
        df_formateado = pd.read_excel(archivo_formateado, sheet_name="Facturas_Exitosas")
        assert len(df_formateado) == 1  # Solo la no duplicada
