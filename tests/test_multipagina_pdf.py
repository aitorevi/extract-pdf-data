"""
Tests para soporte de facturas en múltiples páginas.

Casos de uso:
1. Una factura en una página (comportamiento actual)
2. Una factura en múltiples páginas → extraer de última página
3. Múltiples facturas en un PDF → extraer cada una de su última página
4. Páginas sin NumFactura → marcar como ERROR
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, mock_open
from src.pdf_extractor import PDFExtractor


class TestMultipaginaPDF:
    """Tests para procesamiento de PDFs con múltiples páginas."""

    # ==================== Tests de Agrupación por NumFactura ====================

    def test_agrupar_paginas_una_factura_una_pagina(self):
        """
        Caso 1: Una factura en una página (comportamiento actual).
        Debe devolver un solo grupo con una página.
        """
        extractor = PDFExtractor()

        # Simular extracción de NumFactura de una página
        paginas_data = [
            {'pagina_num': 0, 'NumFactura': 'FAC-001'}
        ]

        grupos = extractor.agrupar_paginas_por_factura(paginas_data)

        assert len(grupos) == 1
        assert 'FAC-001' in grupos
        assert len(grupos['FAC-001']) == 1
        assert grupos['FAC-001'][0]['pagina_num'] == 0

    def test_agrupar_paginas_una_factura_tres_paginas(self):
        """
        Caso 2: Una factura en tres páginas.
        Debe agrupar las tres páginas bajo el mismo NumFactura.
        """
        extractor = PDFExtractor()

        paginas_data = [
            {'pagina_num': 0, 'NumFactura': 'FAC-001'},
            {'pagina_num': 1, 'NumFactura': 'FAC-001'},
            {'pagina_num': 2, 'NumFactura': 'FAC-001'}
        ]

        grupos = extractor.agrupar_paginas_por_factura(paginas_data)

        assert len(grupos) == 1
        assert 'FAC-001' in grupos
        assert len(grupos['FAC-001']) == 3
        assert grupos['FAC-001'][0]['pagina_num'] == 0
        assert grupos['FAC-001'][1]['pagina_num'] == 1
        assert grupos['FAC-001'][2]['pagina_num'] == 2

    def test_agrupar_paginas_tres_facturas_en_un_pdf(self):
        """
        Caso 3: Tres facturas diferentes en un PDF.
        Debe crear tres grupos independientes.
        """
        extractor = PDFExtractor()

        paginas_data = [
            {'pagina_num': 0, 'NumFactura': 'FAC-001'},
            {'pagina_num': 1, 'NumFactura': 'FAC-002'},
            {'pagina_num': 2, 'NumFactura': 'FAC-003'}
        ]

        grupos = extractor.agrupar_paginas_por_factura(paginas_data)

        assert len(grupos) == 3
        assert 'FAC-001' in grupos
        assert 'FAC-002' in grupos
        assert 'FAC-003' in grupos
        assert len(grupos['FAC-001']) == 1
        assert len(grupos['FAC-002']) == 1
        assert len(grupos['FAC-003']) == 1

    def test_agrupar_paginas_caso_mixto(self):
        """
        Caso mixto: Algunas facturas con múltiples páginas, otras con una sola.
        FAC-001: 2 páginas
        FAC-002: 1 página
        FAC-003: 3 páginas
        """
        extractor = PDFExtractor()

        paginas_data = [
            {'pagina_num': 0, 'NumFactura': 'FAC-001'},
            {'pagina_num': 1, 'NumFactura': 'FAC-001'},
            {'pagina_num': 2, 'NumFactura': 'FAC-002'},
            {'pagina_num': 3, 'NumFactura': 'FAC-003'},
            {'pagina_num': 4, 'NumFactura': 'FAC-003'},
            {'pagina_num': 5, 'NumFactura': 'FAC-003'}
        ]

        grupos = extractor.agrupar_paginas_por_factura(paginas_data)

        assert len(grupos) == 3
        assert len(grupos['FAC-001']) == 2
        assert len(grupos['FAC-002']) == 1
        assert len(grupos['FAC-003']) == 3

    # ==================== Tests de Extracción desde Última Página ====================

    def test_extraer_datos_ultima_pagina_una_factura_una_pagina(self):
        """
        Una factura de una página: extraer datos de esa única página.
        """
        extractor = PDFExtractor()

        # Mock de página
        mock_page = MagicMock()
        mock_page.crop.return_value.extract_text.return_value = "FAC-001"

        grupos = {
            'FAC-001': [
                {'pagina_num': 0, 'NumFactura': 'FAC-001', 'page_obj': mock_page}
            ]
        }

        # La función debe extraer de la última (y única) página
        ultima_pagina = extractor.obtener_ultima_pagina_factura(grupos['FAC-001'])

        assert ultima_pagina['pagina_num'] == 0

    def test_extraer_datos_ultima_pagina_una_factura_tres_paginas(self):
        """
        Una factura de tres páginas: extraer datos de la página 3 (última).
        """
        extractor = PDFExtractor()

        grupos = {
            'FAC-001': [
                {'pagina_num': 0, 'NumFactura': 'FAC-001'},
                {'pagina_num': 1, 'NumFactura': 'FAC-001'},
                {'pagina_num': 2, 'NumFactura': 'FAC-001'}  # Esta es la última
            ]
        }

        ultima_pagina = extractor.obtener_ultima_pagina_factura(grupos['FAC-001'])

        assert ultima_pagina['pagina_num'] == 2

    def test_extraer_todas_facturas_de_sus_ultimas_paginas(self):
        """
        Múltiples facturas: cada una debe extraerse de su última página.
        FAC-001 → página 1 (última de 2)
        FAC-002 → página 2 (única)
        FAC-003 → página 5 (última de 3)
        """
        extractor = PDFExtractor()

        grupos = {
            'FAC-001': [
                {'pagina_num': 0, 'NumFactura': 'FAC-001'},
                {'pagina_num': 1, 'NumFactura': 'FAC-001'}  # última
            ],
            'FAC-002': [
                {'pagina_num': 2, 'NumFactura': 'FAC-002'}  # última (única)
            ],
            'FAC-003': [
                {'pagina_num': 3, 'NumFactura': 'FAC-003'},
                {'pagina_num': 4, 'NumFactura': 'FAC-003'},
                {'pagina_num': 5, 'NumFactura': 'FAC-003'}  # última
            ]
        }

        for factura_num, paginas in grupos.items():
            ultima = extractor.obtener_ultima_pagina_factura(paginas)
            if factura_num == 'FAC-001':
                assert ultima['pagina_num'] == 1
            elif factura_num == 'FAC-002':
                assert ultima['pagina_num'] == 2
            elif factura_num == 'FAC-003':
                assert ultima['pagina_num'] == 5

    # ==================== Tests de Validación: Páginas sin NumFactura ====================

    def test_pagina_sin_num_factura_debe_generar_error(self):
        """
        Si una página no tiene NumFactura, debe marcarse como ERROR.
        """
        extractor = PDFExtractor()

        paginas_data = [
            {'pagina_num': 0, 'NumFactura': None},  # Sin NumFactura
        ]

        grupos = extractor.agrupar_paginas_por_factura(paginas_data)

        # Debe crear un grupo especial para errores
        assert 'ERROR_SIN_NUMFACTURA' in grupos
        assert len(grupos['ERROR_SIN_NUMFACTURA']) == 1

    def test_multiples_paginas_sin_num_factura(self):
        """
        Múltiples páginas sin NumFactura deben agruparse como ERROR.
        """
        extractor = PDFExtractor()

        paginas_data = [
            {'pagina_num': 0, 'NumFactura': 'FAC-001'},
            {'pagina_num': 1, 'NumFactura': None},  # Error
            {'pagina_num': 2, 'NumFactura': None},  # Error
            {'pagina_num': 3, 'NumFactura': 'FAC-002'}
        ]

        grupos = extractor.agrupar_paginas_por_factura(paginas_data)

        assert len(grupos) == 3  # FAC-001, FAC-002, ERROR_SIN_NUMFACTURA
        assert 'FAC-001' in grupos
        assert 'FAC-002' in grupos
        assert 'ERROR_SIN_NUMFACTURA' in grupos
        assert len(grupos['ERROR_SIN_NUMFACTURA']) == 2

    def test_pagina_con_num_factura_vacio_debe_generar_error(self):
        """
        NumFactura vacío ('') también debe considerarse como error.
        """
        extractor = PDFExtractor()

        paginas_data = [
            {'pagina_num': 0, 'NumFactura': ''},  # Vacío
            {'pagina_num': 1, 'NumFactura': 'FAC-001'}
        ]

        grupos = extractor.agrupar_paginas_por_factura(paginas_data)

        assert 'ERROR_SIN_NUMFACTURA' in grupos
        assert len(grupos['ERROR_SIN_NUMFACTURA']) == 1
        assert grupos['ERROR_SIN_NUMFACTURA'][0]['pagina_num'] == 0

    # ==================== Tests de Extracción de NumFactura de Página ====================

    @patch('pdfplumber.open')
    def test_extraer_num_factura_de_pagina(self, mock_pdfplumber):
        """
        Debe extraer el NumFactura de una página según la plantilla.
        """
        extractor = PDFExtractor()

        # Mock plantilla con campo NumFactura
        plantilla = {
            'nombre_proveedor': 'Proveedor Test',
            'cif_proveedor': 'B12345678',
            'campos': [
                {
                    'nombre': 'NumFactura',
                    'coordenadas': [100, 100, 200, 120],
                    'tipo': 'texto'
                }
            ]
        }

        extractor.plantillas_cargadas['test'] = plantilla

        # Mock página que devuelve un número de factura
        mock_page = MagicMock()
        mock_crop = MagicMock()
        mock_crop.extract_text.return_value = "FAC-12345"
        mock_page.crop.return_value = mock_crop

        # Extraer NumFactura de la página
        num_factura = extractor.extraer_num_factura_de_pagina(mock_page, plantilla)

        assert num_factura == "FAC-12345"
        mock_page.crop.assert_called_once_with((100, 100, 200, 120))

    @patch('pdfplumber.open')
    def test_extraer_num_factura_de_pagina_no_encontrado(self, mock_pdfplumber):
        """
        Si no se encuentra NumFactura en la plantilla, debe devolver None.
        """
        extractor = PDFExtractor()

        # Plantilla SIN campo NumFactura
        plantilla = {
            'nombre_proveedor': 'Proveedor Test',
            'campos': [
                {
                    'nombre': 'Base',
                    'coordenadas': [100, 100, 200, 120],
                    'tipo': 'numerico'
                }
            ]
        }

        mock_page = MagicMock()

        num_factura = extractor.extraer_num_factura_de_pagina(mock_page, plantilla)

        assert num_factura is None

    # ==================== Tests de Integración ====================

    @patch('pdfplumber.open')
    def test_integracion_extraer_multiples_facturas_multipagina(self, mock_pdfplumber):
        """
        Test de integración: PDF con múltiples facturas, algunas con múltiples páginas.

        Estructura del PDF:
        - Página 0: FAC-001 (1/2)
        - Página 1: FAC-001 (2/2) ← extraer de aquí
        - Página 2: FAC-002 (1/1) ← extraer de aquí
        - Página 3: FAC-003 (1/3)
        - Página 4: FAC-003 (2/3)
        - Página 5: FAC-003 (3/3) ← extraer de aquí

        Resultado esperado: 3 facturas extraídas (FAC-001, FAC-002, FAC-003)
        """
        extractor = PDFExtractor()

        # Plantilla de prueba
        plantilla = {
            'nombre_proveedor': 'Test Provider',
            'cif_proveedor': 'B12345678',
            'campos': [
                {
                    'nombre': 'NumFactura',
                    'coordenadas': [100, 50, 200, 70],
                    'tipo': 'texto'
                },
                {
                    'nombre': 'Base',
                    'coordenadas': [100, 100, 200, 120],
                    'tipo': 'numerico'
                }
            ]
        }

        extractor.plantillas_cargadas['test'] = plantilla

        # Mock de páginas del PDF
        mock_pages = []
        numeros_factura = ['FAC-001', 'FAC-001', 'FAC-002', 'FAC-003', 'FAC-003', 'FAC-003']
        bases = ['', '', '100.00', '', '', '250.50']  # Solo en últimas páginas

        for i, (num_fac, base) in enumerate(zip(numeros_factura, bases)):
            mock_page = MagicMock()

            def make_crop_side_effect(num_f, b):
                def crop_side_effect(bbox):
                    mock_crop = MagicMock()
                    # Según las coordenadas, devolver NumFactura o Base
                    if bbox == (100, 50, 200, 70):  # NumFactura
                        mock_crop.extract_text.return_value = num_f
                    elif bbox == (100, 100, 200, 120):  # Base
                        mock_crop.extract_text.return_value = b
                    return mock_crop
                return crop_side_effect

            mock_page.crop.side_effect = make_crop_side_effect(num_fac, base)
            mock_pages.append(mock_page)

        # Mock del PDF
        mock_pdf = MagicMock()
        mock_pdf.pages = mock_pages
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf

        # CUANDO: Extraer datos del PDF multipágina
        resultados = extractor.extraer_datos_factura_multipagina('test.pdf', 'test')

        # ENTONCES: Debe devolver 3 facturas
        assert len(resultados) == 3

        # Verificar que se extrajeron de las páginas correctas
        facturas_dict = {r['NumFactura']: r for r in resultados}

        # FAC-001 debe extraerse de página 1 (última de 2)
        assert 'FAC-001' in facturas_dict

        # FAC-002 debe extraerse de página 2 (única)
        assert 'FAC-002' in facturas_dict
        assert facturas_dict['FAC-002']['Base'] == '100.00'

        # FAC-003 debe extraerse de página 5 (última de 3)
        assert 'FAC-003' in facturas_dict
        assert facturas_dict['FAC-003']['Base'] == '250.50'
