"""
Tests para identificación de proveedores usando campos de identificación.

Valida que:
1. Identificación por CIF exacto funciona
2. Identificación por nombre con similitud >= 85% funciona
3. Se puede identificar con CIF O Nombre (no ambos requeridos)
4. La similitud normaliza correctamente (ignora puntuación, espacios)
5. Campos de identificación no se exportan
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from src.pdf_extractor import PDFExtractor


class TestProviderIdentification:
    """Tests para identificación de proveedores."""

    def test_calcular_similitud_identicos(self):
        """Test similitud entre textos idénticos."""
        extractor = PDFExtractor()
        similitud = extractor._calcular_similitud("Homebed Spain S.L.", "Homebed Spain S.L.")
        assert similitud == 100.0

    def test_calcular_similitud_ignora_puntuacion(self):
        """Test que la similitud ignora puntuación."""
        extractor = PDFExtractor()

        # "homebed spain, sl." vs "homebed spain s.l." debería ser 100% tras normalización
        similitud = extractor._calcular_similitud("homebed spain, sl.", "homebed spain s.l.")
        assert similitud == 100.0

    def test_calcular_similitud_ignora_mayusculas(self):
        """Test que la similitud ignora mayúsculas/minúsculas."""
        extractor = PDFExtractor()
        similitud = extractor._calcular_similitud("HOMEBED SPAIN SL", "homebed spain sl")
        assert similitud == 100.0

    def test_calcular_similitud_normaliza_espacios(self):
        """Test que la similitud normaliza espacios múltiples."""
        extractor = PDFExtractor()
        similitud = extractor._calcular_similitud("Homebed  Spain   SL", "Homebed Spain SL")
        assert similitud == 100.0

    def test_calcular_similitud_textos_diferentes(self):
        """Test similitud entre textos completamente diferentes."""
        extractor = PDFExtractor()
        similitud = extractor._calcular_similitud("Homebed Spain", "Empresa Diferente")
        assert similitud < 50.0

    def test_calcular_similitud_parcial(self):
        """Test similitud parcial entre textos."""
        extractor = PDFExtractor()
        # "Homebed Spain" vs "Homebed" debería tener similitud parcial
        similitud = extractor._calcular_similitud("Homebed Spain", "Homebed")
        assert 50.0 < similitud < 100.0

    @patch('pdfplumber.open')
    def test_identificar_proveedor_por_cif_exacto(self, mock_pdf_open, tmp_path):
        """Test identificación por CIF exacto."""
        # Crear plantilla con CIF de identificación
        plantilla_dir = tmp_path / "plantillas"
        plantilla_dir.mkdir()

        plantilla = {
            "nombre_proveedor": "Homebed Spain S.L.",
            "cif_proveedor": "B05529656",
            "campos": [
                {
                    "nombre": "CIF_Identificacion",
                    "coordenadas": [10, 10, 100, 30],
                    "tipo": "texto",
                    "es_identificacion": True
                },
                {
                    "nombre": "NumFactura",
                    "coordenadas": [10, 50, 100, 70],
                    "tipo": "texto",
                    "es_identificacion": False
                }
            ]
        }

        with open(plantilla_dir / "homebed_spain_s.l..json", "w", encoding="utf-8") as f:
            json.dump(plantilla, f)

        extractor = PDFExtractor(directorio_plantillas=str(plantilla_dir))
        extractor.cargar_plantillas()

        # Mock del PDF que retorna el CIF en las coordenadas de identificación
        def mock_crop(bbox):
            mock_result = MagicMock()
            if bbox == (10, 10, 100, 30):  # CIF_Identificacion
                mock_result.extract_text.return_value = "B05529656"
            else:
                mock_result.extract_text.return_value = ""
            return mock_result

        mock_page = MagicMock()
        mock_page.crop = mock_crop
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        mock_pdf_open.return_value = mock_pdf

        # Identificar proveedor
        resultado = extractor.identificar_proveedor("test.pdf")

        assert resultado == "homebed_spain_s.l."

    @patch('pdfplumber.open')
    def test_identificar_proveedor_por_nombre_similitud(self, mock_pdf_open, tmp_path):
        """Test identificación por nombre con similitud >= 85%."""
        plantilla_dir = tmp_path / "plantillas"
        plantilla_dir.mkdir()

        plantilla = {
            "nombre_proveedor": "Homebed Spain S.L.",
            "cif_proveedor": "B05529656",
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
                }
            ]
        }

        with open(plantilla_dir / "homebed_spain_s.l..json", "w", encoding="utf-8") as f:
            json.dump(plantilla, f)

        extractor = PDFExtractor(directorio_plantillas=str(plantilla_dir))
        extractor.cargar_plantillas()

        # Mock del PDF que retorna nombre similar
        def mock_crop(bbox):
            mock_result = MagicMock()
            if bbox == (10, 10, 100, 30):  # Nombre_Identificacion
                # Nombre con ligeras diferencias pero > 85% similitud
                mock_result.extract_text.return_value = "HOMEBED SPAIN, SL."
            else:
                mock_result.extract_text.return_value = ""
            return mock_result

        mock_page = MagicMock()
        mock_page.crop = mock_crop
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        mock_pdf_open.return_value = mock_pdf

        resultado = extractor.identificar_proveedor("test.pdf")

        assert resultado == "homebed_spain_s.l."

    @patch('pdfplumber.open')
    def test_identificar_proveedor_nombre_baja_similitud(self, mock_pdf_open, tmp_path):
        """Test que no identifica con nombre de baja similitud (<85%)."""
        plantilla_dir = tmp_path / "plantillas"
        plantilla_dir.mkdir()

        plantilla = {
            "nombre_proveedor": "Homebed Spain S.L.",
            "cif_proveedor": "B05529656",
            "campos": [
                {
                    "nombre": "Nombre_Identificacion",
                    "coordenadas": [10, 10, 100, 30],
                    "tipo": "texto",
                    "es_identificacion": True
                }
            ]
        }

        with open(plantilla_dir / "homebed_spain_s.l..json", "w", encoding="utf-8") as f:
            json.dump(plantilla, f)

        extractor = PDFExtractor(directorio_plantillas=str(plantilla_dir))
        extractor.cargar_plantillas()

        # Mock del PDF con nombre muy diferente
        def mock_crop(bbox):
            mock_result = MagicMock()
            mock_result.extract_text.return_value = "Otra Empresa Completamente Diferente"
            return mock_result

        mock_page = MagicMock()
        mock_page.crop = mock_crop
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        mock_pdf_open.return_value = mock_pdf

        resultado = extractor.identificar_proveedor("test.pdf")

        assert resultado is None

    @patch('pdfplumber.open')
    def test_identificar_proveedor_sin_campos_identificacion(self, mock_pdf_open, tmp_path):
        """Test cuando la plantilla no tiene campos de identificación."""
        plantilla_dir = tmp_path / "plantillas"
        plantilla_dir.mkdir()

        plantilla = {
            "nombre_proveedor": "Homebed Spain S.L.",
            "cif_proveedor": "B05529656",
            "campos": [
                {
                    "nombre": "NumFactura",
                    "coordenadas": [10, 50, 100, 70],
                    "tipo": "texto",
                    "es_identificacion": False
                }
            ]
        }

        with open(plantilla_dir / "homebed_spain_s.l..json", "w", encoding="utf-8") as f:
            json.dump(plantilla, f)

        extractor = PDFExtractor(directorio_plantillas=str(plantilla_dir))
        extractor.cargar_plantillas()

        mock_page = MagicMock()
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        mock_pdf_open.return_value = mock_pdf

        # Sin campos de identificación, no debería poder identificar
        resultado = extractor.identificar_proveedor("test.pdf")

        assert resultado is None

    @patch('pdfplumber.open')
    def test_identificar_proveedor_cif_o_nombre_suficiente(self, mock_pdf_open, tmp_path):
        """Test que CIF O Nombre es suficiente (no requiere ambos)."""
        plantilla_dir = tmp_path / "plantillas"
        plantilla_dir.mkdir()

        plantilla = {
            "nombre_proveedor": "Homebed Spain S.L.",
            "cif_proveedor": "B05529656",
            "campos": [
                {
                    "nombre": "CIF_Identificacion",
                    "coordenadas": [10, 10, 100, 30],
                    "tipo": "texto",
                    "es_identificacion": True
                },
                {
                    "nombre": "Nombre_Identificacion",
                    "coordenadas": [10, 40, 100, 60],
                    "tipo": "texto",
                    "es_identificacion": True
                }
            ]
        }

        with open(plantilla_dir / "homebed_spain_s.l..json", "w", encoding="utf-8") as f:
            json.dump(plantilla, f)

        extractor = PDFExtractor(directorio_plantillas=str(plantilla_dir))
        extractor.cargar_plantillas()

        # Mock que solo retorna CIF (nombre vacío)
        def mock_crop(bbox):
            mock_result = MagicMock()
            if bbox == (10, 10, 100, 30):  # CIF_Identificacion
                mock_result.extract_text.return_value = "B05529656"
            else:  # Nombre_Identificacion vacío
                mock_result.extract_text.return_value = ""
            return mock_result

        mock_page = MagicMock()
        mock_page.crop = mock_crop
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        mock_pdf_open.return_value = mock_pdf

        resultado = extractor.identificar_proveedor("test.pdf")

        # Debería identificar solo con CIF
        assert resultado == "homebed_spain_s.l."

    @patch('pdfplumber.open')
    def test_campos_identificacion_no_se_exportan(self, mock_pdf_open, tmp_path):
        """Test que campos de identificación no aparecen en datos exportables."""
        plantilla_dir = tmp_path / "plantillas"
        plantilla_dir.mkdir()

        plantilla = {
            "nombre_proveedor": "Test Provider",
            "cif_proveedor": "B12345678",
            "campos": [
                {
                    "nombre": "CIF_Identificacion",
                    "coordenadas": [10, 10, 100, 30],
                    "tipo": "texto",
                    "es_identificacion": True
                },
                {
                    "nombre": "Nombre_Identificacion",
                    "coordenadas": [10, 40, 100, 60],
                    "tipo": "texto",
                    "es_identificacion": True
                },
                {
                    "nombre": "NumFactura",
                    "coordenadas": [10, 70, 100, 90],
                    "tipo": "texto",
                    "es_identificacion": False
                }
            ]
        }

        with open(plantilla_dir / "test_provider.json", "w", encoding="utf-8") as f:
            json.dump(plantilla, f)

        extractor = PDFExtractor(directorio_plantillas=str(plantilla_dir), trimestre="1T", año="2025")
        extractor.cargar_plantillas()

        def mock_crop(bbox):
            mock_result = MagicMock()
            if bbox[1] < 35:  # CIF_Identificacion
                mock_result.extract_text.return_value = "B12345678"
            elif bbox[1] < 65:  # Nombre_Identificacion
                mock_result.extract_text.return_value = "Test Provider"
            else:  # NumFactura
                mock_result.extract_text.return_value = "FAC-001"
            return mock_result

        mock_page = MagicMock()
        mock_page.crop = mock_crop
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        mock_pdf_open.return_value = mock_pdf

        datos = extractor.extraer_datos_factura("test.pdf", "test_provider")

        # Campos de identificación NO deben estar en las columnas estándar
        assert "CIF_Identificacion" not in datos
        assert "Nombre_Identificacion" not in datos

        # Pero sí deben estar como metadatos (con _)
        assert "_CIF_Identificacion" in datos
        assert "_Nombre_Identificacion" in datos

        # Campo normal debe estar
        assert "NumFactura" in datos
        assert datos["NumFactura"] == "FAC-001"

    @patch('pdfplumber.open')
    def test_proveedor_no_identificado_genera_error(self, mock_pdf_open, tmp_path):
        """Test que factura sin proveedor identificado genera registro de error."""
        plantilla_dir = tmp_path / "plantillas"
        plantilla_dir.mkdir()
        facturas_dir = tmp_path / "facturas"
        facturas_dir.mkdir()

        plantilla = {
            "nombre_proveedor": "Proveedor Conocido",
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

        with open(plantilla_dir / "conocido.json", "w", encoding="utf-8") as f:
            json.dump(plantilla, f)

        # Crear archivo PDF
        (facturas_dir / "factura_desconocida.pdf").touch()

        extractor = PDFExtractor(
            directorio_plantillas=str(plantilla_dir),
            directorio_facturas=str(facturas_dir),
            trimestre="1T",
            año="2025"
        )
        extractor.cargar_plantillas()

        # Mock que retorna nombre no coincidente
        def mock_crop(bbox):
            mock_result = MagicMock()
            mock_result.extract_text.return_value = "Proveedor Desconocido"
            return mock_result

        mock_page = MagicMock()
        mock_page.crop = mock_crop
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        mock_pdf_open.return_value = mock_pdf

        resultados = extractor.procesar_directorio_facturas()

        assert len(resultados) == 1
        resultado = resultados[0]

        # Debe tener error
        assert "_Error" in resultado
        assert "Proveedor no identificado" in resultado["_Error"]
        assert resultado.get("_Proveedor_ID") == "NO_IDENTIFICADO"

        # Campos estándar deben estar vacíos
        assert resultado.get("CIF") == ""
        assert resultado.get("NumFactura") == ""
