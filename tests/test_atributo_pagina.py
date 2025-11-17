"""
Tests para verificar el comportamiento del atributo 'pagina' en templates.

Este módulo prueba que:
1. Campos SIN 'pagina' extraen de la última página
2. Campos CON 'pagina' extraen de la página especificada
3. Templates mixtos funcionan correctamente (ej: Iberdrola)
"""

import pytest
from unittest.mock import MagicMock, patch
from src.pdf_extractor import PDFExtractor


class TestAtributoPagina:
    """Tests para el atributo 'pagina' en templates."""

    @patch('pdfplumber.open')
    def test_sin_pagina_extrae_de_ultima(self, mock_pdfplumber):
        """Campo SIN 'pagina' debe extraer de la última página."""
        extractor = PDFExtractor()

        # Template sin 'pagina'
        plantilla = {
            'nombre_proveedor': 'Test',
            'cif_proveedor': 'B12345678',
            'campos': [
                {'nombre': 'NumFactura', 'coordenadas': [100, 50, 200, 70], 'tipo': 'texto'},
                {'nombre': 'Base', 'coordenadas': [100, 100, 200, 120], 'tipo': 'numerico'}
            ]
        }
        extractor.plantillas_cargadas['test'] = plantilla

        # Mock 3 páginas
        mock_pages = []
        for i, base in enumerate(['100.00', '200.00', '300.00']):
            page = MagicMock()
            page.extract_words.return_value = [{'text': 'word'}] * 10

            def make_crop(b):
                def crop(bbox):
                    c = MagicMock()
                    if bbox == (100, 50, 200, 70):
                        c.extract_text.return_value = 'FAC-001'
                    elif bbox == (100, 100, 200, 120):
                        c.extract_text.return_value = b
                    return c
                return crop

            page.crop.side_effect = make_crop(base)
            mock_pages.append(page)

        mock_pdf = MagicMock()
        mock_pdf.pages = mock_pages
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf

        # Extraer
        resultados = extractor.extraer_datos_factura_multipagina('test.pdf', 'test')

        # Verificar: debe extraer de última página (300.00)
        assert len(resultados) == 1
        assert resultados[0]['Base'] == '300.00', \
            f"Esperaba 300.00 (última página), obtuvo {resultados[0]['Base']}"


    @patch('pdfplumber.open')
    def test_con_pagina_extrae_de_especifica(self, mock_pdfplumber):
        """Campo CON 'pagina' debe extraer de esa página específica."""
        extractor = PDFExtractor()

        # Template CON 'pagina'
        plantilla = {
            'nombre_proveedor': 'Test',
            'cif_proveedor': 'B12345678',
            'campos': [
                {'nombre': 'NumFactura', 'coordenadas': [100, 50, 200, 70], 'tipo': 'texto', 'pagina': 1},
                {'nombre': 'Base', 'coordenadas': [100, 100, 200, 120], 'tipo': 'numerico', 'pagina': 2}
            ]
        }
        extractor.plantillas_cargadas['test'] = plantilla

        # Mock 3 páginas
        mock_pages = []
        for i, base in enumerate(['100.00', '200.00', '300.00']):
            page = MagicMock()
            page.extract_words.return_value = [{'text': 'word'}] * 10

            def make_crop(b):
                def crop(bbox):
                    c = MagicMock()
                    if bbox == (100, 50, 200, 70):
                        c.extract_text.return_value = 'FAC-001'
                    elif bbox == (100, 100, 200, 120):
                        c.extract_text.return_value = b
                    return c
                return crop

            page.crop.side_effect = make_crop(base)
            mock_pages.append(page)

        mock_pdf = MagicMock()
        mock_pdf.pages = mock_pages
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf

        # Extraer
        resultados = extractor.extraer_datos_factura_multipagina('test.pdf', 'test')

        # Verificar: debe extraer de página 2 (200.00), no de la última
        assert len(resultados) == 1
        assert resultados[0]['Base'] == '200.00', \
            f"Esperaba 200.00 (página 2), obtuvo {resultados[0]['Base']}"


    @patch('pdfplumber.open')
    def test_template_mixto_iberdrola(self, mock_pdfplumber):
        """Template con campos en diferentes páginas (Iberdrola)."""
        extractor = PDFExtractor()

        # Template estilo Iberdrola
        plantilla = {
            'nombre_proveedor': 'Iberdrola',
            'cif_proveedor': 'A95758389',
            'campos': [
                {'nombre': 'NumFactura', 'coordenadas': [161, 376, 235, 386], 'tipo': 'texto', 'pagina': 1},
                {'nombre': 'Base', 'coordenadas': [527, 430, 555, 437], 'tipo': 'numerico', 'pagina': 2}
            ]
        }
        extractor.plantillas_cargadas['test'] = plantilla

        # Mock 4 páginas
        mock_pages = []
        for i in range(4):
            page = MagicMock()
            page.extract_words.return_value = [{'text': 'word'}] * 10

            def make_crop(pag):
                def crop(bbox):
                    c = MagicMock()
                    if pag == 0 and bbox == (161, 376, 235, 386):
                        c.extract_text.return_value = '21251006010107325'
                    elif pag == 1 and bbox == (527, 430, 555, 437):
                        c.extract_text.return_value = '90,32'
                    return c
                return crop

            page.crop.side_effect = make_crop(i)
            mock_pages.append(page)

        mock_pdf = MagicMock()
        mock_pdf.pages = mock_pages
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf

        # Extraer
        resultados = extractor.extraer_datos_factura_multipagina('test.pdf', 'test')

        # Verificar
        assert len(resultados) == 1
        assert resultados[0]['NumFactura'] == '21251006010107325'
        assert resultados[0]['Base'] == '90.32', \
            f"Esperaba 90.32 (página 2), obtuvo {resultados[0]['Base']}"


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
