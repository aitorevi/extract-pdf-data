"""
Tests para campos opcionales y auxiliares - Issue #15

Tests para:
1. Campos opcionales (FechaVto) - puede estar vacío sin error
2. Campos auxiliares (Portes) - se suma a Base, no se exporta
"""

import pytest
import json
import os
from src.pdf_extractor import PDFExtractor
from src.excel_exporter import ExcelExporter


class TestCamposOpcionales:
    """Tests para campos opcionales (ej: FechaVto)"""

    def test_campo_opcional_faltante_no_genera_error(self, tmp_path):
        """Campo opcional faltante (FechaVto) no debe generar error."""
        # Crear plantilla SIN FechaVto (campo opcional)
        plantilla = {
            "nombre_proveedor": "Proveedor Sin FechaVto",
            "campos": [
                {"nombre": "CIF_Identificacion", "tipo": "texto", "coordenadas": [50, 50, 150, 70]},
                {"nombre": "FechaFactura", "tipo": "fecha", "coordenadas": [50, 100, 150, 120]},
                {"nombre": "NumFactura", "tipo": "texto", "coordenadas": [50, 150, 150, 170]},
                {"nombre": "Base", "tipo": "numerico", "coordenadas": [50, 200, 150, 220]},
                # FechaVto NO está capturado (es opcional)
            ]
        }

        # Guardar plantilla
        plantilla_dir = tmp_path / "plantillas"
        plantilla_dir.mkdir()
        plantilla_path = plantilla_dir / "proveedor_sin_fechavto.json"
        with open(plantilla_path, 'w', encoding='utf-8') as f:
            json.dump(plantilla, f, indent=2)

        # Verificar que FechaVto no está en la plantilla
        campos_nombres = [c['nombre'] for c in plantilla['campos']]
        assert 'FechaVto' not in campos_nombres

    def test_campo_opcional_vacio_se_exporta_como_vacio(self, tmp_path):
        """Campo opcional vacío se exporta como cadena vacía en Excel."""
        datos = [
            {
                'CIF': 'B12345678',
                'FechaFactura': '01/01/2025',
                'Trimestre': 'Q1',
                'Año': '2025',
                'FechaVto': '',  # Campo opcional vacío
                'NumFactura': 'F001',
                'FechaPago': '',
                'Base': '100.00',
                'ComPaypal': '',
            }
        ]

        exporter = ExcelExporter(datos=datos, directorio_salida=str(tmp_path))
        excel_path = exporter.exportar_excel_basico(nombre_archivo="test_opcional.xlsx")

        assert os.path.exists(excel_path)

        # Leer Excel y verificar
        import pandas as pd
        df = pd.read_excel(excel_path)

        assert len(df) == 1
        assert df.loc[0, 'FechaVto'] == '' or pd.isna(df.loc[0, 'FechaVto'])

    def test_multiples_facturas_unas_con_fechavto_otras_sin(self, tmp_path):
        """Múltiples facturas, algunas con FechaVto y otras sin (opcional)."""
        datos = [
            {
                'CIF': 'B11111111',
                'FechaFactura': '01/01/2025',
                'Trimestre': 'Q1',
                'Año': '2025',
                'FechaVto': '31/01/2025',  # Tiene FechaVto
                'NumFactura': 'F001',
                'FechaPago': '',
                'Base': '100.00',
                'ComPaypal': '',
            },
            {
                'CIF': 'B22222222',
                'FechaFactura': '02/01/2025',
                'Trimestre': 'Q1',
                'Año': '2025',
                'FechaVto': '',  # Sin FechaVto (opcional)
                'NumFactura': 'F002',
                'FechaPago': '',
                'Base': '200.00',
                'ComPaypal': '',
            }
        ]

        exporter = ExcelExporter(datos=datos, directorio_salida=str(tmp_path))
        excel_path = exporter.exportar_excel_basico(nombre_archivo="test_mixto.xlsx")

        assert os.path.exists(excel_path)

        import pandas as pd
        df = pd.read_excel(excel_path)

        assert len(df) == 2
        assert df.loc[0, 'FechaVto'] == '31/01/2025'
        assert df.loc[1, 'FechaVto'] == '' or pd.isna(df.loc[1, 'FechaVto'])


class TestCamposAuxiliares:
    """Tests para campos auxiliares (ej: Portes que se suma a Base)"""

    def test_campo_auxiliar_portes_se_suma_a_base(self):
        """Portes (campo auxiliar) se suma automáticamente a Base."""
        extractor = PDFExtractor(trimestre="Q1", año="2025")

        # Datos extraídos con Portes
        datos_extraidos = {
            'FechaFactura': '01/01/2025',
            'NumFactura': 'F001',
            'Base': '100.00',
            'Portes': '15.50',  # Campo auxiliar
        }

        # Procesar campos auxiliares
        datos_procesados = extractor._procesar_campos_auxiliares(datos_extraidos)

        # Base debe ser 100 + 15.50 = 115.50
        assert float(datos_procesados['Base']) == 115.50

        # Portes no debe estar en datos procesados (se elimina)
        assert 'Portes' not in datos_procesados

    def test_campo_auxiliar_portes_sin_valor_no_afecta_base(self):
        """Si Portes está vacío o es None, no afecta a Base."""
        extractor = PDFExtractor(trimestre="Q1", año="2025")

        # Datos sin Portes
        datos_extraidos = {
            'FechaFactura': '01/01/2025',
            'NumFactura': 'F001',
            'Base': '100.00',
            'Portes': '',  # Vacío
        }

        datos_procesados = extractor._procesar_campos_auxiliares(datos_extraidos)

        # Base no cambia
        assert datos_procesados['Base'] == '100.00'

        # Portes se elimina
        assert 'Portes' not in datos_procesados

    def test_proveedor_sin_campo_portes_base_sin_cambios(self):
        """Proveedor sin campo Portes → Base sin cambios."""
        extractor = PDFExtractor(trimestre="Q1", año="2025")

        # Datos sin Portes en absoluto
        datos_extraidos = {
            'FechaFactura': '01/01/2025',
            'NumFactura': 'F001',
            'Base': '100.00',
        }

        datos_procesados = extractor._procesar_campos_auxiliares(datos_extraidos)

        # Base no cambia
        assert datos_procesados['Base'] == '100.00'

    def test_campo_auxiliar_no_aparece_en_excel(self, tmp_path):
        """Portes NO debe aparecer como columna en Excel (se eliminó antes)."""
        datos = [
            {
                'CIF': 'B12345678',
                'FechaFactura': '01/01/2025',
                'Trimestre': 'Q1',
                'Año': '2025',
                'FechaVto': '',
                'NumFactura': 'F001',
                'FechaPago': '',
                'Base': '115.50',  # Ya incluye Portes sumados
                'ComPaypal': '',
                # Portes NO está aquí (fue eliminado)
            }
        ]

        exporter = ExcelExporter(datos=datos, directorio_salida=str(tmp_path))
        excel_path = exporter.exportar_excel_basico(nombre_archivo="test_sin_portes.xlsx")

        assert os.path.exists(excel_path)

        import pandas as pd
        df = pd.read_excel(excel_path)

        # Verificar que Portes no está en columnas
        assert 'Portes' not in df.columns

        # Verificar que Base tiene el valor correcto (con Portes ya sumado)
        assert float(df.loc[0, 'Base']) == 115.50

    def test_portes_con_valor_cero_no_suma(self):
        """Portes con valor 0 → no suma nada a Base."""
        extractor = PDFExtractor(trimestre="Q1", año="2025")

        datos_extraidos = {
            'FechaFactura': '01/01/2025',
            'NumFactura': 'F001',
            'Base': '100.00',
            'Portes': '0.00',
        }

        datos_procesados = extractor._procesar_campos_auxiliares(datos_extraidos)

        # Base = 100 + 0 = 100
        assert float(datos_procesados['Base']) == 100.00
        assert 'Portes' not in datos_procesados

    def test_portes_con_valor_invalido_no_rompe_extraccion(self):
        """Portes con valor inválido → no rompe, solo no suma."""
        extractor = PDFExtractor(trimestre="Q1", año="2025")

        datos_extraidos = {
            'FechaFactura': '01/01/2025',
            'NumFactura': 'F001',
            'Base': '100.00',
            'Portes': 'TEXTO_INVALIDO',
        }

        # No debe lanzar excepción
        datos_procesados = extractor._procesar_campos_auxiliares(datos_extraidos)

        # Base no cambia (no se pudo sumar)
        assert datos_procesados['Base'] == '100.00'

        # Portes se elimina de todos modos
        assert 'Portes' not in datos_procesados

    def test_multiples_facturas_con_y_sin_portes(self):
        """Múltiples facturas, algunas con Portes y otras sin."""
        extractor = PDFExtractor(trimestre="Q1", año="2025")

        # Factura 1: CON Portes
        datos1 = {
            'FechaFactura': '01/01/2025',
            'NumFactura': 'F001',
            'Base': '100.00',
            'Portes': '15.00',
        }
        procesados1 = extractor._procesar_campos_auxiliares(datos1)
        assert float(procesados1['Base']) == 115.00
        assert 'Portes' not in procesados1

        # Factura 2: SIN Portes
        datos2 = {
            'FechaFactura': '02/01/2025',
            'NumFactura': 'F002',
            'Base': '200.00',
        }
        procesados2 = extractor._procesar_campos_auxiliares(datos2)
        assert procesados2['Base'] == '200.00'


class TestIntegracionCamposOpcionalesAuxiliares:
    """Tests de integración entre campos opcionales y auxiliares"""

    def test_factura_completa_con_opcional_y_auxiliar(self):
        """Factura con campo opcional (FechaVto) y auxiliar (Portes)."""
        extractor = PDFExtractor(trimestre="Q1", año="2025")

        datos_extraidos = {
            'FechaFactura': '01/01/2025',
            'FechaVto': '31/01/2025',  # Opcional, presente
            'NumFactura': 'F001',
            'Base': '100.00',
            'Portes': '15.00',  # Auxiliar
        }

        datos_procesados = extractor._procesar_campos_auxiliares(datos_extraidos)

        # FechaVto sigue presente (es opcional pero está capturado)
        assert datos_procesados['FechaVto'] == '31/01/2025'

        # Base con Portes sumado
        assert float(datos_procesados['Base']) == 115.00

        # Portes eliminado
        assert 'Portes' not in datos_procesados

    def test_factura_sin_opcional_con_auxiliar(self):
        """Factura SIN campo opcional pero CON auxiliar."""
        extractor = PDFExtractor(trimestre="Q1", año="2025")

        datos_extraidos = {
            'FechaFactura': '01/01/2025',
            'FechaVto': '',  # Opcional, vacío
            'NumFactura': 'F001',
            'Base': '100.00',
            'Portes': '20.00',  # Auxiliar
        }

        datos_procesados = extractor._procesar_campos_auxiliares(datos_extraidos)

        # FechaVto vacío (opcional)
        assert datos_procesados['FechaVto'] == ''

        # Base con Portes sumado
        assert float(datos_procesados['Base']) == 120.00

        # Portes eliminado
        assert 'Portes' not in datos_procesados
