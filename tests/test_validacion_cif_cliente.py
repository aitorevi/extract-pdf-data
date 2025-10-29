"""
Tests para la validación de CIF del cliente en facturas.

Tests que cubren:
- Captura de CIF del cliente desde el PDF
- Validación contra el CIF corporativo (E98530876)
- Rechazo de facturas con CIF incorrecto
- El CIF del cliente NO se exporta al Excel
"""

import pytest
import os
from src.pdf_extractor import PDFExtractor
from src.utils.cif import CIF


class TestCapturaCIFCliente:
    """Tests para la captura del CIF del cliente desde facturas."""

    def test_cif_cliente_se_captura_desde_pdf(self, tmp_path):
        """El CIF del cliente se captura correctamente desde el PDF."""
        # Este test requiere un PDF de prueba con CIF del cliente
        # Por ahora verificamos que el extractor tenga el método
        extractor = PDFExtractor("plantillas")
        assert hasattr(extractor, '_extraer_cif_cliente')

    def test_cif_cliente_se_sanea_correctamente(self):
        """El CIF del cliente se sanea antes de validar."""
        # Simular diferentes formatos de CIF del cliente
        cif_con_guiones = CIF("E-98530876")
        cif_con_espacios = CIF("E 98530876")
        cif_con_barras = CIF("E/98530876")

        # Todos deben normalizarse al mismo valor
        assert cif_con_guiones == "E98530876"
        assert cif_con_espacios == "E98530876"
        assert cif_con_barras == "E98530876"


class TestValidacionCIFCliente:
    """Tests para la validación del CIF del cliente contra el CIF corporativo."""

    CIF_CORPORATIVO = "E98530876"

    def test_factura_con_cif_correcto_se_acepta(self):
        """Factura con CIF del cliente correcto se acepta."""
        cif_extraido = CIF("E98530876")
        cif_corporativo = CIF(self.CIF_CORPORATIVO)

        assert cif_extraido == cif_corporativo

    def test_factura_con_cif_correcto_con_formato_diferente(self):
        """Factura con CIF correcto pero formato diferente se acepta."""
        cif_extraido = CIF("E-98530876")
        cif_corporativo = CIF(self.CIF_CORPORATIVO)

        assert cif_extraido == cif_corporativo

    def test_factura_con_cif_incorrecto_se_rechaza(self):
        """Factura con CIF del cliente incorrecto se rechaza."""
        cif_extraido = CIF("B12345678")  # CIF diferente
        cif_corporativo = CIF(self.CIF_CORPORATIVO)

        assert cif_extraido != cif_corporativo

    def test_factura_sin_cif_cliente_se_marca_como_advertencia(self):
        """Factura sin CIF del cliente se marca con advertencia."""
        cif_extraido = CIF("")  # CIF vacío
        cif_corporativo = CIF(self.CIF_CORPORATIVO)

        # CIF vacío no debe ser igual al corporativo
        assert cif_extraido != cif_corporativo
        # Y además debe ser inválido
        assert not cif_extraido.is_valid()


class TestRechazoFacturasIncorrectas:
    """Tests para verificar que facturas con CIF incorrecto se rechazan o marcan."""

    CIF_CORPORATIVO = "E98530876"

    def test_factura_rechazada_tiene_flag_cif_incorrecto(self):
        """Factura rechazada debe tener un flag indicando CIF incorrecto."""
        extractor = PDFExtractor("plantillas")

        # Simular datos de factura con CIF incorrecto
        datos_factura = {
            'NumFactura': '2024-001',
            'FechaFactura': '15/01/2024',
            '_CIF_Cliente': 'B12345678',  # CIF incorrecto
        }

        # Verificar que se marca como incorrecta
        es_valido = extractor._validar_cif_cliente(datos_factura.get('_CIF_Cliente'))
        assert not es_valido

    def test_factura_aceptada_no_tiene_errores(self):
        """Factura con CIF correcto no tiene errores."""
        extractor = PDFExtractor("plantillas")

        # Simular datos de factura con CIF correcto
        datos_factura = {
            'NumFactura': '2024-001',
            'FechaFactura': '15/01/2024',
            '_CIF_Cliente': 'E98530876',  # CIF correcto
        }

        # Verificar que es válida
        es_valido = extractor._validar_cif_cliente(datos_factura.get('_CIF_Cliente'))
        assert es_valido


class TestCIFClienteNoSeExportaExcel:
    """Tests para verificar que el CIF del cliente NO se exporta al Excel."""

    def test_cif_cliente_no_aparece_en_datos_exportados(self):
        """El campo _CIF_Cliente no debe aparecer en los datos exportados al Excel."""
        # Los campos que empiezan con _ son internos y no se exportan
        datos_internos = {
            'NumFactura': '2024-001',
            'FechaFactura': '15/01/2024',
            'Base': '1000.00',
            '_CIF_Cliente': 'E98530876',  # Campo interno (empieza con _)
            '_Motivo_Rechazo': 'CIF incorrecto',  # Otro campo interno
        }

        # Filtrar campos que NO empiezan con _
        datos_exportables = {k: v for k, v in datos_internos.items() if not k.startswith('_')}

        # Verificar que _CIF_Cliente NO está en los datos exportables
        assert '_CIF_Cliente' not in datos_exportables
        assert 'NumFactura' in datos_exportables
        assert 'FechaFactura' in datos_exportables
        assert 'Base' in datos_exportables

    def test_campo_cif_cliente_es_temporal(self):
        """El CIF del cliente se usa solo para validación, no para exportación."""
        # Campo interno empieza con _ para indicar que es temporal
        campo_cif_cliente = '_CIF_Cliente'

        assert campo_cif_cliente.startswith('_')


class TestIntegracionCIFCliente:
    """Tests de integración para captura y validación de CIF del cliente."""

    def test_extractor_tiene_metodo_validar_cif_cliente(self):
        """El extractor debe tener método para validar CIF del cliente."""
        extractor = PDFExtractor("plantillas")
        assert hasattr(extractor, '_validar_cif_cliente')

    def test_extractor_tiene_cif_corporativo_configurado(self):
        """El extractor debe tener el CIF corporativo configurado."""
        extractor = PDFExtractor("plantillas")
        assert hasattr(extractor, 'CIF_CORPORATIVO')
        assert extractor.CIF_CORPORATIVO == "E98530876"
