"""
Tests unitarios para src/pdf_extractor.py
"""
import pytest
import os
import json
import copy
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, mock_open, MagicMock
from src.pdf_extractor import PDFExtractor


@pytest.mark.unit
class TestPDFExtractorInit:
    """Tests para el constructor de PDFExtractor."""

    def test_init_default_directories(self):
        """Test inicialización con directorios por defecto."""
        extractor = PDFExtractor()
        assert extractor.directorio_facturas == "facturas"
        assert extractor.directorio_plantillas == "plantillas"
        assert extractor.plantillas_cargadas == {}
        assert extractor.resultados == []

    def test_init_custom_directories(self):
        """Test inicialización con directorios personalizados."""
        extractor = PDFExtractor(
            directorio_facturas="custom/facturas",
            directorio_plantillas="custom/plantillas"
        )
        assert extractor.directorio_facturas == "custom/facturas"
        assert extractor.directorio_plantillas == "custom/plantillas"


@pytest.mark.unit
class TestValidarPlantilla:
    """Tests para el método validar_plantilla."""

    def test_validar_plantilla_valida(self, plantilla_valida):
        """Test validación de plantilla válida."""
        extractor = PDFExtractor()
        assert extractor.validar_plantilla(plantilla_valida) is True

    def test_validar_plantilla_falta_proveedor_id(self, plantilla_valida):
        """Test validación cuando falta proveedor_id."""
        extractor = PDFExtractor()
        plantilla_invalida = copy.deepcopy(plantilla_valida)
        del plantilla_invalida['proveedor_id']
        assert extractor.validar_plantilla(plantilla_invalida) is False

    def test_validar_plantilla_falta_nombre_proveedor(self, plantilla_valida):
        """Test validación cuando falta nombre_proveedor."""
        extractor = PDFExtractor()
        plantilla_invalida = copy.deepcopy(plantilla_valida)
        del plantilla_invalida['nombre_proveedor']
        assert extractor.validar_plantilla(plantilla_invalida) is False

    def test_validar_plantilla_falta_campos(self, plantilla_valida):
        """Test validación cuando falta campos."""
        extractor = PDFExtractor()
        plantilla_invalida = copy.deepcopy(plantilla_valida)
        del plantilla_invalida['campos']
        assert extractor.validar_plantilla(plantilla_invalida) is False

    def test_validar_plantilla_campos_no_lista(self, plantilla_valida):
        """Test validación cuando campos no es una lista."""
        extractor = PDFExtractor()
        plantilla_invalida = copy.deepcopy(plantilla_valida)
        plantilla_invalida['campos'] = "no es una lista"
        assert extractor.validar_plantilla(plantilla_invalida) is False

    def test_validar_plantilla_campo_no_dict(self, plantilla_valida):
        """Test validación cuando un campo no es diccionario."""
        extractor = PDFExtractor()
        plantilla_invalida = copy.deepcopy(plantilla_valida)
        plantilla_invalida['campos'] = ["no es dict", {}]
        assert extractor.validar_plantilla(plantilla_invalida) is False

    def test_validar_plantilla_campo_falta_nombre(self, plantilla_valida):
        """Test validación cuando falta nombre en campo."""
        extractor = PDFExtractor()
        plantilla_invalida = copy.deepcopy(plantilla_valida)
        plantilla_invalida['campos'] = [{'coordenadas': [0, 0, 100, 100], 'tipo': 'texto'}]
        assert extractor.validar_plantilla(plantilla_invalida) is False

    def test_validar_plantilla_campo_falta_coordenadas(self, plantilla_valida):
        """Test validación cuando faltan coordenadas en campo."""
        extractor = PDFExtractor()
        plantilla_invalida = copy.deepcopy(plantilla_valida)
        plantilla_invalida['campos'] = [{'nombre': 'test', 'tipo': 'texto'}]
        assert extractor.validar_plantilla(plantilla_invalida) is False

    def test_validar_plantilla_campo_coordenadas_invalidas(self, plantilla_valida):
        """Test validación cuando coordenadas son inválidas."""
        extractor = PDFExtractor()
        plantilla_invalida = copy.deepcopy(plantilla_valida)
        plantilla_invalida['campos'] = [
            {'nombre': 'test', 'coordenadas': [0, 0, 100], 'tipo': 'texto'}  # Solo 3 valores
        ]
        assert extractor.validar_plantilla(plantilla_invalida) is False


@pytest.mark.unit
class TestCargarPlantillas:
    """Tests para el método cargar_plantillas."""

    def test_cargar_plantillas_directorio_no_existe(self, tmp_path):
        """Test cuando el directorio de plantillas no existe."""
        extractor = PDFExtractor(directorio_plantillas=str(tmp_path / "no_existe"))
        resultado = extractor.cargar_plantillas()
        assert resultado is False
        assert len(extractor.plantillas_cargadas) == 0

    def test_cargar_plantillas_directorio_vacio(self, tmp_path):
        """Test cuando el directorio está vacío."""
        extractor = PDFExtractor(directorio_plantillas=str(tmp_path))
        resultado = extractor.cargar_plantillas()
        assert resultado is False
        assert len(extractor.plantillas_cargadas) == 0

    def test_cargar_plantillas_validas(self, temp_plantillas_dir, plantilla_valida):
        """Test carga de plantillas válidas."""
        # Crear archivo de plantilla válida
        plantilla_path = temp_plantillas_dir / "test_proveedor.json"
        with open(plantilla_path, 'w', encoding='utf-8') as f:
            json.dump(plantilla_valida, f)

        extractor = PDFExtractor(directorio_plantillas=str(temp_plantillas_dir))
        resultado = extractor.cargar_plantillas()

        assert resultado is True
        assert len(extractor.plantillas_cargadas) == 1
        assert plantilla_valida['proveedor_id'] in extractor.plantillas_cargadas

    def test_cargar_plantillas_invalidas(self, temp_plantillas_dir, plantilla_invalida):
        """Test carga de plantillas inválidas."""
        # Crear archivo de plantilla inválida
        plantilla_path = temp_plantillas_dir / "invalid.json"
        with open(plantilla_path, 'w', encoding='utf-8') as f:
            json.dump(plantilla_invalida, f)

        extractor = PDFExtractor(directorio_plantillas=str(temp_plantillas_dir))
        resultado = extractor.cargar_plantillas()

        assert resultado is False
        assert len(extractor.plantillas_cargadas) == 0

    def test_cargar_plantillas_json_corrupto(self, temp_plantillas_dir):
        """Test cuando el archivo JSON está corrupto."""
        # Crear archivo JSON corrupto
        plantilla_path = temp_plantillas_dir / "corrupto.json"
        with open(plantilla_path, 'w', encoding='utf-8') as f:
            f.write("{ esto no es json válido }")

        extractor = PDFExtractor(directorio_plantillas=str(temp_plantillas_dir))
        resultado = extractor.cargar_plantillas()

        assert resultado is False
        assert len(extractor.plantillas_cargadas) == 0

    def test_cargar_plantillas_mixtas(self, temp_plantillas_dir, plantilla_valida, plantilla_invalida):
        """Test carga de mix de plantillas válidas e inválidas."""
        # Crear plantilla válida
        valida_path = temp_plantillas_dir / "valida.json"
        with open(valida_path, 'w', encoding='utf-8') as f:
            json.dump(plantilla_valida, f)

        # Crear plantilla inválida
        invalida_path = temp_plantillas_dir / "invalida.json"
        with open(invalida_path, 'w', encoding='utf-8') as f:
            json.dump(plantilla_invalida, f)

        extractor = PDFExtractor(directorio_plantillas=str(temp_plantillas_dir))
        resultado = extractor.cargar_plantillas()

        # Debe cargar solo la válida
        assert resultado is True
        assert len(extractor.plantillas_cargadas) == 1
        assert plantilla_valida['proveedor_id'] in extractor.plantillas_cargadas


@pytest.mark.unit
class TestLimpiarTexto:
    """Tests para el método limpiar_texto."""

    def test_limpiar_texto_basico(self):
        """Test limpieza básica de texto."""
        extractor = PDFExtractor()
        texto = "  Texto  con   espacios   "
        resultado = extractor.limpiar_texto(texto)
        assert resultado == "Texto con espacios"

    def test_limpiar_texto_caracteres_especiales(self):
        """Test limpieza de caracteres especiales."""
        extractor = PDFExtractor()
        texto = "Texto\x00con\x1fcaracteres\x7fespeciales"
        resultado = extractor.limpiar_texto(texto)
        assert "\x00" not in resultado
        assert "\x1f" not in resultado
        assert "\x7f" not in resultado

    def test_limpiar_texto_vacio(self):
        """Test limpieza de texto vacío."""
        extractor = PDFExtractor()
        assert extractor.limpiar_texto("") == ""
        assert extractor.limpiar_texto("   ") == ""


@pytest.mark.unit
class TestLimpiarFecha:
    """Tests para el método limpiar_fecha."""

    def test_limpiar_fecha_formato_dd_mm_yyyy(self):
        """Test limpieza de fecha DD/MM/YYYY."""
        extractor = PDFExtractor()
        assert "15/03/2024" in extractor.limpiar_fecha("Fecha: 15/03/2024 Extra")

    def test_limpiar_fecha_formato_yyyy_mm_dd(self):
        """Test limpieza de fecha YYYY-MM-DD."""
        extractor = PDFExtractor()
        assert "2024-03-15" in extractor.limpiar_fecha("Fecha: 2024-03-15 Extra")

    def test_limpiar_fecha_formato_texto(self):
        """Test limpieza de fecha en formato texto."""
        extractor = PDFExtractor()
        resultado = extractor.limpiar_fecha("15 de marzo de 2024")
        assert "15 de marzo de 2024" in resultado

    def test_limpiar_fecha_sin_patron(self):
        """Test cuando no se encuentra patrón de fecha."""
        extractor = PDFExtractor()
        texto = "No hay fecha aquí"
        resultado = extractor.limpiar_fecha(texto)
        assert resultado == "No hay fecha aquí"


@pytest.mark.unit
class TestLimpiarNumerico:
    """Tests para el método limpiar_numerico."""

    def test_limpiar_numerico_entero(self):
        """Test limpieza de número entero."""
        extractor = PDFExtractor()
        assert extractor.limpiar_numerico("1234") == "1234"

    def test_limpiar_numerico_decimal_punto(self):
        """Test limpieza de número decimal con punto."""
        extractor = PDFExtractor()
        assert extractor.limpiar_numerico("123.45") == "123.45"

    def test_limpiar_numerico_formato_europeo(self):
        """Test limpieza de formato europeo (1.234,56)."""
        extractor = PDFExtractor()
        resultado = extractor.limpiar_numerico("1.234,56")
        # Debe convertir a formato estándar: 1234.56
        assert resultado == "1234.56"

    def test_limpiar_numerico_formato_americano(self):
        """Test limpieza de formato americano (1,234.56)."""
        extractor = PDFExtractor()
        resultado = extractor.limpiar_numerico("1,234.56")
        # Debe remover separador de miles: 1234.56
        assert resultado == "1234.56"

    def test_limpiar_numerico_solo_coma_decimal(self):
        """Test número con coma decimal (123,45)."""
        extractor = PDFExtractor()
        resultado = extractor.limpiar_numerico("123,45")
        assert resultado == "123.45"

    def test_limpiar_numerico_solo_coma_miles(self):
        """Test número con coma de miles (1,234)."""
        extractor = PDFExtractor()
        resultado = extractor.limpiar_numerico("1,234")
        # Tiene 3 dígitos después de la coma, es separador de miles
        assert resultado == "1234"

    def test_limpiar_numerico_con_simbolos(self):
        """Test limpieza de número con símbolos."""
        extractor = PDFExtractor()
        resultado = extractor.limpiar_numerico("$ 1,234.56 USD")
        assert resultado == "1234.56"

    def test_limpiar_numerico_negativo(self):
        """Test limpieza de número negativo."""
        extractor = PDFExtractor()
        resultado = extractor.limpiar_numerico("-123.45")
        assert resultado == "-123.45"

    def test_limpiar_numerico_invalido(self):
        """Test cuando no es un número válido."""
        extractor = PDFExtractor()
        resultado = extractor.limpiar_numerico("abc")
        assert resultado == "abc"  # Devuelve original


@pytest.mark.unit
class TestProcesarCampo:
    """Tests para el método procesar_campo."""

    def test_procesar_campo_texto(self):
        """Test procesamiento de campo tipo texto."""
        extractor = PDFExtractor()
        resultado = extractor.procesar_campo("  Texto   ", "texto")
        assert resultado == "Texto"

    def test_procesar_campo_numerico(self):
        """Test procesamiento de campo tipo numérico."""
        extractor = PDFExtractor()
        resultado = extractor.procesar_campo("1,234.56", "numerico")
        assert resultado == "1234.56"

    def test_procesar_campo_fecha(self):
        """Test procesamiento de campo tipo fecha."""
        extractor = PDFExtractor()
        resultado = extractor.procesar_campo("Fecha: 15/03/2024", "fecha")
        assert "15/03/2024" in resultado

    def test_procesar_campo_vacio(self):
        """Test procesamiento de campo vacío."""
        extractor = PDFExtractor()
        assert extractor.procesar_campo("", "texto") == ""
        assert extractor.procesar_campo(None, "texto") == ""


@pytest.mark.unit
class TestIdentificarProveedor:
    """Tests para el método identificar_proveedor."""

    def test_identificar_proveedor_por_nombre_archivo(self, temp_facturas_dir, plantilla_valida):
        """Test identificación por nombre de archivo."""
        extractor = PDFExtractor()
        extractor.plantillas_cargadas = {plantilla_valida['proveedor_id']: plantilla_valida}

        # Crear archivo con nombre que contiene el proveedor
        pdf_path = temp_facturas_dir / f"{plantilla_valida['nombre_proveedor'].lower()}_factura.pdf"
        pdf_path.touch()

        resultado = extractor.identificar_proveedor(str(pdf_path))
        assert resultado == plantilla_valida['proveedor_id']

    @patch('pdfplumber.open')
    def test_identificar_proveedor_por_contenido(self, mock_pdf_open, plantilla_valida):
        """Test identificación por contenido del PDF."""
        extractor = PDFExtractor()
        extractor.plantillas_cargadas = {plantilla_valida['proveedor_id']: plantilla_valida}

        # Mock del PDF
        mock_page = Mock()
        mock_page.extract_text.return_value = f"Factura de {plantilla_valida['nombre_proveedor']}\nDatos adicionales"

        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)

        mock_pdf_open.return_value = mock_pdf

        resultado = extractor.identificar_proveedor("factura_sin_nombre.pdf")
        assert resultado == plantilla_valida['proveedor_id']

    @patch('pdfplumber.open')
    def test_identificar_proveedor_no_encontrado(self, mock_pdf_open):
        """Test cuando no se puede identificar el proveedor."""
        extractor = PDFExtractor()
        extractor.plantillas_cargadas = {'PROV_001': {'nombre_proveedor': 'XYZ Corp'}}

        # Mock del PDF sin coincidencias
        mock_page = Mock()
        mock_page.extract_text.return_value = "Factura de otra empresa completamente diferente ABC Ltd"

        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)

        mock_pdf_open.return_value = mock_pdf

        resultado = extractor.identificar_proveedor("factura_desconocida.pdf")
        assert resultado is None

    @patch('pdfplumber.open')
    def test_identificar_proveedor_error_leyendo_pdf(self, mock_pdf_open):
        """Test cuando hay error al leer el PDF."""
        extractor = PDFExtractor()
        extractor.plantillas_cargadas = {'PROV_001': {'nombre_proveedor': 'Proveedor Uno'}}

        # Mock que lanza excepción
        mock_pdf_open.side_effect = Exception("Error al abrir PDF")

        resultado = extractor.identificar_proveedor("factura_corrupta.pdf")
        assert resultado is None


@pytest.mark.unit
class TestExtraerDatosFactura:
    """Tests para el método extraer_datos_factura."""

    @patch('pdfplumber.open')
    def test_extraer_datos_factura_exitoso(self, mock_pdf_open, plantilla_valida):
        """Test extracción exitosa de datos."""
        extractor = PDFExtractor()
        extractor.plantillas_cargadas = {plantilla_valida['proveedor_id']: plantilla_valida}

        # Mock del PDF
        mock_cropped = Mock()
        mock_cropped.extract_text.return_value = "12345"

        mock_page = Mock()
        mock_page.crop.return_value = mock_cropped

        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)

        mock_pdf_open.return_value = mock_pdf

        resultado = extractor.extraer_datos_factura("test.pdf", plantilla_valida['proveedor_id'])

        assert resultado['Archivo'] == "test.pdf"
        assert resultado['Proveedor_ID'] == plantilla_valida['proveedor_id']
        assert resultado['Proveedor_Nombre'] == plantilla_valida['nombre_proveedor']
        assert 'Fecha_Procesamiento' in resultado

    def test_extraer_datos_factura_plantilla_no_encontrada(self):
        """Test cuando la plantilla no existe."""
        extractor = PDFExtractor()

        with pytest.raises(ValueError, match="Plantilla no encontrada"):
            extractor.extraer_datos_factura("test.pdf", "PROVEEDOR_INEXISTENTE")

    @patch('pdfplumber.open')
    def test_extraer_datos_factura_pdf_sin_paginas(self, mock_pdf_open, plantilla_valida):
        """Test cuando el PDF no tiene páginas."""
        extractor = PDFExtractor()
        extractor.plantillas_cargadas = {plantilla_valida['proveedor_id']: plantilla_valida}

        # Mock de PDF sin páginas
        mock_pdf = Mock()
        mock_pdf.pages = []
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)

        mock_pdf_open.return_value = mock_pdf

        resultado = extractor.extraer_datos_factura("test.pdf", plantilla_valida['proveedor_id'])

        # Debe devolver datos con ERROR_PDF
        assert resultado['Archivo'] == "test.pdf"
        for campo in plantilla_valida['campos']:
            assert resultado[campo['nombre']] == "ERROR_PDF"

    @patch('pdfplumber.open')
    def test_extraer_datos_factura_error_en_campo(self, mock_pdf_open, plantilla_valida):
        """Test cuando hay error extrayendo un campo específico."""
        extractor = PDFExtractor()
        extractor.plantillas_cargadas = {plantilla_valida['proveedor_id']: plantilla_valida}

        # Mock que lanza excepción al hacer crop
        mock_page = Mock()
        mock_page.crop.side_effect = Exception("Error en crop")

        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)

        mock_pdf_open.return_value = mock_pdf

        resultado = extractor.extraer_datos_factura("test.pdf", plantilla_valida['proveedor_id'])

        # Los campos deben tener "ERROR" cuando falla crop
        # Pero los campos metainformación deben existir
        assert resultado['Archivo'] == "test.pdf"
        assert resultado['Proveedor_ID'] == plantilla_valida['proveedor_id']
        for campo in plantilla_valida['campos']:
            assert resultado[campo['nombre']] == "ERROR"


@pytest.mark.unit
class TestProcesarDirectorioFacturas:
    """Tests para el método procesar_directorio_facturas."""

    def test_procesar_directorio_no_existe(self, tmp_path):
        """Test cuando el directorio no existe."""
        extractor = PDFExtractor(directorio_facturas=str(tmp_path / "no_existe"))
        resultado = extractor.procesar_directorio_facturas()
        assert resultado == []

    def test_procesar_directorio_vacio(self, temp_facturas_dir):
        """Test cuando el directorio está vacío."""
        extractor = PDFExtractor(directorio_facturas=str(temp_facturas_dir))
        resultado = extractor.procesar_directorio_facturas()
        assert resultado == []

    def test_procesar_directorio_sin_pdfs(self, temp_facturas_dir):
        """Test cuando no hay archivos PDF."""
        # Crear archivos no-PDF
        (temp_facturas_dir / "test.txt").touch()
        (temp_facturas_dir / "image.jpg").touch()

        extractor = PDFExtractor(directorio_facturas=str(temp_facturas_dir))
        resultado = extractor.procesar_directorio_facturas()
        assert resultado == []

    @patch('src.pdf_extractor.PDFExtractor.identificar_proveedor')
    @patch('src.pdf_extractor.PDFExtractor.extraer_datos_factura')
    def test_procesar_directorio_con_pdfs_exitosos(
        self, mock_extraer, mock_identificar, temp_facturas_dir, plantilla_valida
    ):
        """Test procesamiento exitoso de PDFs."""
        # Crear archivos PDF
        (temp_facturas_dir / "factura1.pdf").touch()
        (temp_facturas_dir / "factura2.pdf").touch()

        extractor = PDFExtractor(directorio_facturas=str(temp_facturas_dir))
        extractor.plantillas_cargadas = {plantilla_valida['proveedor_id']: plantilla_valida}

        # Mocks
        mock_identificar.return_value = plantilla_valida['proveedor_id']
        mock_extraer.return_value = {
            'Archivo': 'factura.pdf',
            'Proveedor_ID': plantilla_valida['proveedor_id'],
            'Numero_Factura': '12345'
        }

        resultado = extractor.procesar_directorio_facturas()

        assert len(resultado) == 2
        assert mock_identificar.call_count == 2
        assert mock_extraer.call_count == 2

    @patch('src.pdf_extractor.PDFExtractor.identificar_proveedor')
    def test_procesar_directorio_proveedor_no_identificado(self, mock_identificar, temp_facturas_dir):
        """Test cuando no se puede identificar el proveedor."""
        # Crear archivo PDF
        (temp_facturas_dir / "factura_desconocida.pdf").touch()

        extractor = PDFExtractor(directorio_facturas=str(temp_facturas_dir))

        # Mock que no identifica proveedor
        mock_identificar.return_value = None

        resultado = extractor.procesar_directorio_facturas()

        assert len(resultado) == 1
        assert resultado[0]['Proveedor_ID'] == 'NO_IDENTIFICADO'
        assert 'Error' in resultado[0]

    @patch('src.pdf_extractor.PDFExtractor.identificar_proveedor')
    @patch('src.pdf_extractor.PDFExtractor.extraer_datos_factura')
    def test_procesar_directorio_error_en_extraccion(
        self, mock_extraer, mock_identificar, temp_facturas_dir, plantilla_valida
    ):
        """Test cuando hay error al extraer datos."""
        # Crear archivo PDF
        (temp_facturas_dir / "factura_error.pdf").touch()

        extractor = PDFExtractor(directorio_facturas=str(temp_facturas_dir))

        # Mocks
        mock_identificar.return_value = plantilla_valida['proveedor_id']
        mock_extraer.side_effect = Exception("Error al extraer")

        resultado = extractor.procesar_directorio_facturas()

        assert len(resultado) == 1
        assert resultado[0]['Proveedor_ID'] == plantilla_valida['proveedor_id']
        assert 'Error' in resultado[0]


@pytest.mark.unit
class TestObtenerEstadisticas:
    """Tests para el método obtener_estadisticas."""

    def test_obtener_estadisticas_sin_resultados(self):
        """Test estadísticas sin resultados."""
        extractor = PDFExtractor()
        stats = extractor.obtener_estadisticas()
        assert stats == {}

    def test_obtener_estadisticas_con_resultados_exitosos(self):
        """Test estadísticas con resultados exitosos."""
        extractor = PDFExtractor()
        extractor.resultados = [
            {'Archivo': 'f1.pdf', 'Proveedor_ID': 'PROV_001', 'Numero': '123'},
            {'Archivo': 'f2.pdf', 'Proveedor_ID': 'PROV_001', 'Numero': '456'},
            {'Archivo': 'f3.pdf', 'Proveedor_ID': 'PROV_002', 'Numero': '789'},
        ]

        stats = extractor.obtener_estadisticas()

        assert stats['total_facturas'] == 3
        assert stats['facturas_exitosas'] == 3
        assert stats['facturas_con_error'] == 0
        assert stats['tasa_exito'] == 100.0
        assert len(stats['proveedores']) == 2

    def test_obtener_estadisticas_con_errores(self):
        """Test estadísticas con errores."""
        extractor = PDFExtractor()
        extractor.resultados = [
            {'Archivo': 'f1.pdf', 'Proveedor_ID': 'PROV_001', 'Numero': '123'},
            {'Archivo': 'f2.pdf', 'Proveedor_ID': 'PROV_001', 'Error': 'Error al procesar'},
            {'Archivo': 'f3.pdf', 'Proveedor_ID': 'NO_IDENTIFICADO', 'Error': 'No identificado'},
        ]

        stats = extractor.obtener_estadisticas()

        assert stats['total_facturas'] == 3
        assert stats['facturas_exitosas'] == 1
        assert stats['facturas_con_error'] == 2
        assert stats['tasa_exito'] == 33.33

    def test_obtener_estadisticas_por_proveedor(self):
        """Test estadísticas agrupadas por proveedor."""
        extractor = PDFExtractor()
        extractor.resultados = [
            {'Archivo': 'f1.pdf', 'Proveedor_ID': 'PROV_001', 'Numero': '123'},
            {'Archivo': 'f2.pdf', 'Proveedor_ID': 'PROV_001', 'Error': 'Error'},
            {'Archivo': 'f3.pdf', 'Proveedor_ID': 'PROV_002', 'Numero': '789'},
        ]

        stats = extractor.obtener_estadisticas()

        assert stats['proveedores']['PROV_001']['total'] == 2
        assert stats['proveedores']['PROV_001']['exitosos'] == 1
        assert stats['proveedores']['PROV_001']['errores'] == 1

        assert stats['proveedores']['PROV_002']['total'] == 1
        assert stats['proveedores']['PROV_002']['exitosos'] == 1
        assert stats['proveedores']['PROV_002']['errores'] == 0


@pytest.mark.integration
class TestPDFExtractorIntegration:
    """Tests de integración para flujos completos."""

    def test_flujo_completo_carga_y_validacion(self, temp_plantillas_dir, plantilla_valida):
        """Test flujo completo de carga y validación de plantillas."""
        # Crear plantilla
        plantilla_path = temp_plantillas_dir / "proveedor_test.json"
        with open(plantilla_path, 'w', encoding='utf-8') as f:
            json.dump(plantilla_valida, f)

        # Ejecutar flujo
        extractor = PDFExtractor(directorio_plantillas=str(temp_plantillas_dir))
        cargadas = extractor.cargar_plantillas()

        assert cargadas is True
        assert len(extractor.plantillas_cargadas) == 1

        # Verificar que la plantilla cargada es válida
        plantilla_cargada = extractor.plantillas_cargadas[plantilla_valida['proveedor_id']]
        assert extractor.validar_plantilla(plantilla_cargada) is True
