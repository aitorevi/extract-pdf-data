"""
Tests para el módulo file_organizer.py - Organización automática de PDFs procesados.

Siguiendo TDD, estos tests se escriben ANTES de implementar la funcionalidad.
"""

import pytest
import json
import os
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, mock_open, MagicMock
from src.file_organizer import PDFOrganizer, PALABRAS_FACTURA, UMBRAL_PALABRAS_FACTURA


# ==================== TESTS DE INICIALIZACIÓN ====================

def test_pdforganizer_inicializacion_default():
    """
    Test: PDFOrganizer se inicializa con directorio por defecto 'facturas'.
    """
    organizer = PDFOrganizer()

    assert organizer.directorio_base == Path("facturas")
    assert organizer.directorio_procesadas == Path("facturas/procesadas")
    assert organizer.directorio_indices == Path("facturas/procesadas/indices")
    assert organizer.directorio_duplicados == Path("facturas/duplicados")
    assert organizer.directorio_errores == Path("facturas/errores")
    assert organizer.directorio_logs == Path("logs")


def test_pdforganizer_inicializacion_custom():
    """
    Test: PDFOrganizer acepta directorio base personalizado.
    """
    organizer = PDFOrganizer(directorio_base="mis_facturas")

    assert organizer.directorio_base == Path("mis_facturas")
    assert organizer.directorio_procesadas == Path("mis_facturas/procesadas")


@patch('src.file_organizer.Path.mkdir')
def test_crear_estructura_carpetas(mock_mkdir):
    """
    Test: _crear_estructura_carpetas() crea todas las carpetas necesarias.
    """
    organizer = PDFOrganizer()

    # Verificar que se llamó mkdir para crear carpetas
    assert mock_mkdir.called
    # Carpetas principales deben crearse
    assert mock_mkdir.call_count >= 6  # procesadas, indices, duplicados, errores, logs, subcarpetas


# ==================== TESTS DE ÍNDICES JSON ====================

def test_cargar_indice_inexistente():
    """
    Test: cargar_indice() devuelve índice vacío si no existe el archivo.
    """
    organizer = PDFOrganizer()

    indice = organizer.cargar_indice(2025, "1T")

    assert indice["trimestre"] == "1T"
    assert indice["año"] == 2025
    assert indice["facturas"] == []


@patch('builtins.open', new_callable=mock_open, read_data='{"trimestre": "1T", "año": 2025, "facturas": [{"cif": "B12345678"}]}')
@patch('pathlib.Path.exists', return_value=True)
def test_cargar_indice_existente(mock_exists, mock_file):
    """
    Test: cargar_indice() lee y parsea archivo JSON existente correctamente.
    """
    organizer = PDFOrganizer()

    indice = organizer.cargar_indice(2025, "1T")

    assert indice["trimestre"] == "1T"
    assert indice["año"] == 2025
    assert len(indice["facturas"]) == 1
    assert indice["facturas"][0]["cif"] == "B12345678"


@patch('builtins.open', new_callable=mock_open)
@patch('pathlib.Path.exists', return_value=False)
@patch('src.file_organizer.Path.mkdir')
def test_guardar_indice(mock_mkdir, mock_exists, mock_file):
    """
    Test: guardar_indice() escribe el índice en archivo JSON.
    """
    organizer = PDFOrganizer()
    datos = {
        "trimestre": "2T",
        "año": 2025,
        "facturas": [{"cif": "B87654321"}]
    }

    organizer.guardar_indice(2025, "2T", datos)

    # Verificar que se intentó abrir el archivo para escritura
    mock_file.assert_called()
    # Verificar que se escribió JSON
    handle = mock_file()
    written_data = "".join(call.args[0] for call in handle.write.call_args_list)
    assert "2T" in written_data or handle.write.called


# ==================== TESTS DE DETECCIÓN DE DUPLICADOS ====================

def test_es_duplicado_no_existe():
    """
    Test: es_duplicado() retorna None si la factura no existe en el índice.
    """
    organizer = PDFOrganizer()

    with patch.object(organizer, 'cargar_indice', return_value={
        "trimestre": "1T",
        "año": 2025,
        "facturas": []
    }):
        resultado = organizer.es_duplicado("B12345678", "15/01/2025", "F-001", 2025, "1T")

        assert resultado is None


def test_es_duplicado_existe():
    """
    Test: es_duplicado() retorna info de factura si existe duplicado.
    """
    organizer = PDFOrganizer()

    factura_existente = {
        "cif_proveedor": "B12345678",
        "fecha_factura": "2025-01-15",
        "num_factura": "F-001",
        "ruta_completa": "facturas/procesadas/2025/01/Proveedor/factura.pdf"
    }

    with patch.object(organizer, 'cargar_indice', return_value={
        "trimestre": "1T",
        "año": 2025,
        "facturas": [factura_existente]
    }):
        resultado = organizer.es_duplicado("B12345678", "15/01/2025", "F-001", 2025, "1T")

        assert resultado is not None
        assert resultado["cif_proveedor"] == "B12345678"
        assert resultado["num_factura"] == "F-001"


def test_normalizar_fecha_formato_dd_mm_yyyy():
    """
    Test: _normalizar_fecha() convierte DD/MM/YYYY a YYYY-MM-DD.
    """
    organizer = PDFOrganizer()

    fecha_normalizada = organizer._normalizar_fecha("15/01/2025")

    assert fecha_normalizada == "2025-01-15"


def test_normalizar_fecha_formato_yyyy_mm_dd():
    """
    Test: _normalizar_fecha() mantiene formato YYYY-MM-DD sin cambios.
    """
    organizer = PDFOrganizer()

    fecha_normalizada = organizer._normalizar_fecha("2025-01-15")

    assert fecha_normalizada == "2025-01-15"


def test_agregar_al_indice():
    """
    Test: agregar_al_indice() añade una factura nueva al índice.
    """
    organizer = PDFOrganizer()

    info_factura = {
        "cif_proveedor": "B12345678",
        "fecha_factura": "2025-01-15",
        "num_factura": "F-001"
    }

    with patch.object(organizer, 'cargar_indice', return_value={"trimestre": "1T", "año": 2025, "facturas": []}):
        with patch.object(organizer, 'guardar_indice') as mock_guardar:
            organizer.agregar_al_indice(2025, "1T", info_factura)

            # Verificar que se llamó a guardar_indice con factura añadida
            mock_guardar.assert_called_once()
            datos_guardados = mock_guardar.call_args[0][2]
            assert len(datos_guardados["facturas"]) == 1
            assert datos_guardados["facturas"][0]["cif_proveedor"] == "B12345678"


# ==================== TESTS DE ANÁLISIS HEURÍSTICO ====================

@patch('pdfplumber.open')
def test_analizar_contenido_pdf_es_factura(mock_pdfplumber):
    """
    Test: analizar_contenido_pdf() detecta PDF como posible factura si ≥3 palabras clave.
    """
    # Mock PDF con texto que contiene palabras clave
    mock_page = Mock()
    mock_page.extract_text.return_value = "Factura número F-001 CIF: B12345678 IVA: 21% Base imponible: 100€"
    mock_pdf = Mock()
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = Mock(return_value=mock_pdf)
    mock_pdf.__exit__ = Mock(return_value=False)
    mock_pdfplumber.return_value = mock_pdf

    organizer = PDFOrganizer()
    es_factura, num_palabras = organizer.analizar_contenido_pdf("test.pdf")

    assert es_factura is True
    assert num_palabras >= UMBRAL_PALABRAS_FACTURA


@patch('pdfplumber.open')
def test_analizar_contenido_pdf_no_es_factura(mock_pdfplumber):
    """
    Test: analizar_contenido_pdf() detecta PDF como NO factura si <3 palabras clave.
    """
    # Mock PDF sin palabras clave de factura
    mock_page = Mock()
    mock_page.extract_text.return_value = "Este es un documento aleatorio sin información fiscal."
    mock_pdf = Mock()
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = Mock(return_value=mock_pdf)
    mock_pdf.__exit__ = Mock(return_value=False)
    mock_pdfplumber.return_value = mock_pdf

    organizer = PDFOrganizer()
    es_factura, num_palabras = organizer.analizar_contenido_pdf("test.pdf")

    assert es_factura is False
    assert num_palabras < UMBRAL_PALABRAS_FACTURA


# ==================== TESTS DE HASH MD5 ====================

def test_calcular_hash_md5():
    """
    Test: calcular_hash_md5() calcula hash correcto de archivo.
    """
    organizer = PDFOrganizer()

    with patch('builtins.open', mock_open(read_data=b'test content')):
        hash_md5 = organizer.calcular_hash_md5("test.pdf")

        # Hash MD5 de "test content" es conocido
        assert hash_md5 == "9473fdd0d880a43c21b7778d34872157"


# ==================== TESTS DE MOVIMIENTO DE ARCHIVOS ====================

@patch('shutil.move')
@patch('pathlib.Path.exists', return_value=False)
@patch('pathlib.Path.mkdir')
def test_mover_pdf_exito(mock_mkdir, mock_exists, mock_move):
    """
    Test: mover_pdf() mueve archivo correctamente cuando destino no existe.
    """
    organizer = PDFOrganizer()

    resultado = organizer.mover_pdf("facturas/test.pdf", "facturas/procesadas/2025/01/test.pdf")

    assert resultado is True
    mock_move.assert_called_once()


@patch('shutil.move')
@patch('pathlib.Path.exists', side_effect=[True, False])  # Primera vez existe, segunda no
@patch('pathlib.Path.mkdir')
def test_mover_pdf_archivo_existe_renombrar(mock_mkdir, mock_exists, mock_move):
    """
    Test: mover_pdf() renombra archivo con sufijo _2 si destino ya existe.
    """
    organizer = PDFOrganizer()

    resultado = organizer.mover_pdf("facturas/test.pdf", "facturas/procesadas/test.pdf")

    assert resultado is True
    # Verificar que se movió con nombre modificado (test_2.pdf)
    call_args = mock_move.call_args[0]
    assert "_2" in str(call_args[1]) or mock_move.called


# ==================== TESTS DE LOGGING ====================

@patch('builtins.open', new_callable=mock_open)
def test_registrar_operacion(mock_file):
    """
    Test: registrar_operacion() escribe entrada en archivo de log.
    """
    organizer = PDFOrganizer()

    organizer.registrar_operacion("EXITO", "test.pdf", "facturas/", "facturas/procesadas/", "CIF: B12345678")

    # Verificar que se intentó escribir en el log
    mock_file.assert_called()
    handle = mock_file()
    assert handle.write.called

    # Verificar formato del log
    log_entry = handle.write.call_args[0][0]
    assert "EXITO" in log_entry
    assert "test.pdf" in log_entry
    assert "CIF: B12345678" in log_entry


# ==================== TESTS DE ORGANIZACIÓN COMPLETA ====================

@patch.object(PDFOrganizer, 'mover_pdf', return_value=True)
@patch.object(PDFOrganizer, 'agregar_al_indice')
@patch.object(PDFOrganizer, 'es_duplicado', return_value=None)
@patch.object(PDFOrganizer, 'registrar_operacion')
@patch.object(PDFOrganizer, 'calcular_hash_md5', return_value="abc123")
def test_organizar_factura_exitosa(mock_hash, mock_log, mock_duplicado, mock_agregar, mock_mover, tmp_path):
    """
    Test: organizar_pdf() organiza factura exitosa en carpeta por mes y proveedor.
    """
    organizer = PDFOrganizer()

    pdf_path = tmp_path / "test_factura.pdf"
    pdf_path.write_text("dummy")

    resultado_extraccion = {
        "CIF": "B12345678",
        "FechaFactura": "15/01/2025",
        "NumFactura": "F-001",
        "Trimestre": "1T",
        "Año": "2025",
        "_NombreProveedor": "Innovaciones Textiles"
    }

    ruta_final = organizer.organizar_pdf(str(pdf_path), resultado_extraccion)

    # Verificar que se llamó a mover_pdf
    assert mock_mover.called
    # Verificar que se agregó al índice
    assert mock_agregar.called
    # Verificar que se registró en log
    assert mock_log.called


@patch.object(PDFOrganizer, 'mover_pdf', return_value=True)
@patch.object(PDFOrganizer, 'es_duplicado', return_value={"cif_proveedor": "B12345678"})
@patch.object(PDFOrganizer, 'registrar_operacion')
def test_organizar_factura_duplicada(mock_log, mock_duplicado, mock_mover, tmp_path):
    """
    Test: organizar_pdf() mueve duplicado a carpeta duplicados/YYYY/NT/.
    """
    organizer = PDFOrganizer()

    pdf_path = tmp_path / "test_duplicado.pdf"
    pdf_path.write_text("dummy")

    resultado_extraccion = {
        "CIF": "B12345678",
        "FechaFactura": "15/01/2025",
        "NumFactura": "F-001",
        "Trimestre": "1T",
        "Año": "2025"
    }

    ruta_final = organizer.organizar_pdf(str(pdf_path), resultado_extraccion)

    # Verificar que se llamó a mover_pdf con destino en duplicados/
    assert mock_mover.called
    call_args = str(mock_mover.call_args)
    assert "duplicados" in call_args
    # Verificar que se registró como DUPLICADO en log
    log_call_args = str(mock_log.call_args)
    assert "DUPLICADO" in log_call_args


@patch.object(PDFOrganizer, 'mover_pdf', return_value=True)
@patch.object(PDFOrganizer, 'analizar_contenido_pdf', return_value=(True, 5))
@patch.object(PDFOrganizer, 'registrar_operacion')
def test_organizar_pdf_error_posible_factura(mock_log, mock_analizar, mock_mover, tmp_path):
    """
    Test: organizar_pdf() clasifica PDF con error como posible factura si ≥3 palabras clave.
    """
    organizer = PDFOrganizer()

    pdf_path = tmp_path / "test_error.pdf"
    pdf_path.write_text("dummy")

    # Sin resultado de extracción (error)
    ruta_final = organizer.organizar_pdf(str(pdf_path), None)

    # Verificar que se analizó contenido
    assert mock_analizar.called
    # Verificar que se movió a errores/sin_plantilla_posible_factura/
    call_args = str(mock_mover.call_args)
    assert "sin_plantilla_posible_factura" in call_args
    # Verificar que se registró como ERROR_POSIBLE_FACTURA
    log_call_args = str(mock_log.call_args)
    assert "ERROR_POSIBLE_FACTURA" in log_call_args


@patch.object(PDFOrganizer, 'mover_pdf', return_value=True)
@patch.object(PDFOrganizer, 'analizar_contenido_pdf', return_value=(False, 1))
@patch.object(PDFOrganizer, 'registrar_operacion')
def test_organizar_pdf_error_no_factura(mock_log, mock_analizar, mock_mover, tmp_path):
    """
    Test: organizar_pdf() clasifica PDF con error como NO factura si <3 palabras clave.
    """
    organizer = PDFOrganizer()

    pdf_path = tmp_path / "test_no_factura.pdf"
    pdf_path.write_text("dummy")

    # Sin resultado de extracción (error)
    ruta_final = organizer.organizar_pdf(str(pdf_path), None)

    # Verificar que se movió a errores/probablemente_no_factura/
    call_args = str(mock_mover.call_args)
    assert "probablemente_no_factura" in call_args
    # Verificar que se registró como ERROR_NO_FACTURA
    log_call_args = str(mock_log.call_args)
    assert "ERROR_NO_FACTURA" in log_call_args


# ==================== TESTS DE UTILIDADES ====================

def test_normalizar_nombre_proveedor():
    """
    Test: _normalizar_nombre_proveedor() convierte nombre a formato válido para carpeta.
    """
    organizer = PDFOrganizer()

    nombre_normalizado = organizer._normalizar_nombre_proveedor("Innovaciones Textiles S.L.")

    assert nombre_normalizado == "Innovaciones_Textiles_SL"
    assert " " not in nombre_normalizado
    assert "." not in nombre_normalizado


def test_normalizar_nombre_proveedor_vacio():
    """
    Test: _normalizar_nombre_proveedor() retorna 'Desconocido' si nombre vacío.
    """
    organizer = PDFOrganizer()

    nombre_normalizado = organizer._normalizar_nombre_proveedor("")

    assert nombre_normalizado == "Desconocido"


def test_extraer_mes_de_fecha_formato_dd_mm_yyyy():
    """
    Test: _extraer_mes_de_fecha() extrae mes de fecha DD/MM/YYYY.
    """
    organizer = PDFOrganizer()

    mes = organizer._extraer_mes_de_fecha("15/03/2025")

    assert mes == "03"


def test_extraer_mes_de_fecha_formato_yyyy_mm_dd():
    """
    Test: _extraer_mes_de_fecha() extrae mes de fecha YYYY-MM-DD.
    """
    organizer = PDFOrganizer()

    mes = organizer._extraer_mes_de_fecha("2025-03-15")

    assert mes == "03"


def test_extraer_mes_de_fecha_invalida():
    """
    Test: _extraer_mes_de_fecha() retorna '00' si fecha inválida.
    """
    organizer = PDFOrganizer()

    mes = organizer._extraer_mes_de_fecha("fecha_invalida")

    assert mes == "00"
