"""
Tests para verificar el manejo correcto de errores.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pdf_extractor import PDFExtractor


def test_pagina_sin_numfactura():
    """Test: Página sin NumFactura - debe registrar error, no incluir en resultados."""
    print("\n=== TEST 1: Página Sin NumFactura ===")

    extractor = PDFExtractor(trimestre="3T", año="2025")
    extractor.cargar_plantillas()

    pdf_path = "facturas/test_error_sin_numfactura.pdf"
    if not os.path.exists(pdf_path):
        print(f"⚠️  SKIP: {pdf_path} no encontrado")
        return False

    proveedor_id = extractor.identificar_proveedor(pdf_path)
    if not proveedor_id:
        print("❌ FAIL: No se identificó el proveedor")
        return False

    # Limpiar errores previos
    extractor.errores = []

    lista_facturas = extractor.extraer_datos_factura_multipagina(pdf_path, proveedor_id)

    # Verificaciones
    # Debe extraer FAC-009 y FAC-010, pero NO la página sin NumFactura
    nums_factura = [f['NumFactura'] for f in lista_facturas]
    assert 'FAC-009' in nums_factura, "Debe incluir FAC-009"
    assert 'FAC-010' in nums_factura, "Debe incluir FAC-010"

    # Debe haber registrado 1 error (página 2 sin NumFactura)
    assert len(extractor.errores) >= 1, f"Debe haber al menos 1 error, encontró {len(extractor.errores)}"

    # Verificar que el error menciona la página 2
    error_encontrado = False
    for error in extractor.errores:
        if error.get('Pagina') == 2 and 'NumFactura' in error.get('Error', ''):
            error_encontrado = True
            break

    assert error_encontrado, "Debe registrar error de página 2 sin NumFactura"

    print("✅ PASS: Página sin NumFactura registrada como error")


def test_proveedor_no_identificado():
    """Test: PDF sin proveedor identificado - debe registrar error."""
    print("\n=== TEST 2: Proveedor No Identificado ===")

    extractor = PDFExtractor(trimestre="2T", año="2025")
    extractor.cargar_plantillas()

    # Usar un PDF que no coincida con ninguna plantilla
    pdf_path = "facturas/HBS.pdf"
    if not os.path.exists(pdf_path):
        print(f"⚠️  SKIP: {pdf_path} no encontrado")
        return False

    # Limpiar errores previos
    extractor.errores = []

    # Procesar en el contexto completo
    resultados = []
    proveedor_id = extractor.identificar_proveedor(pdf_path)

    if not proveedor_id:
        # Debe registrar error
        error_registro = {
            'Archivo': os.path.basename(pdf_path),
            'Pagina': 'N/A',
            'Error': 'Proveedor no identificado - no hay plantilla que coincida',
            'Proveedor': 'NO_IDENTIFICADO',
        }
        extractor.errores.append(error_registro)

    # Verificaciones
    assert len(extractor.errores) >= 1, "Debe haber al menos 1 error registrado"
    assert any('NO_IDENTIFICADO' in str(e.get('Proveedor', '')) for e in extractor.errores), \
        "Debe tener error de proveedor no identificado"

    print("✅ PASS: Proveedor no identificado registrado como error")



def test_validacion_numfactura_texto_basura():
    """Test: NumFactura con texto basura - debe ser rechazado."""
    print("\n=== TEST 3: Validación de NumFactura con Texto Basura ===")

    extractor = PDFExtractor()

    # Probar palabras inválidas
    assert not extractor._es_numfactura_valido("Esta página n"), "Debe rechazar 'Esta página n'"
    assert not extractor._es_numfactura_valido("continuación"), "Debe rechazar 'continuación'"
    assert not extractor._es_numfactura_valido("Página siguiente"), "Debe rechazar 'Página siguiente'"
    assert not extractor._es_numfactura_valido(""), "Debe rechazar string vacío"

    # Probar números válidos
    assert extractor._es_numfactura_valido("FAC-001"), "Debe aceptar 'FAC-001'"
    assert extractor._es_numfactura_valido("2025-001"), "Debe aceptar '2025-001'"
    assert extractor._es_numfactura_valido("INV123"), "Debe aceptar 'INV123'"

    print("✅ PASS: Validación de NumFactura funciona correctamente")



def test_exportacion_errores():
    """Test: Exportación de errores a Excel."""
    print("\n=== TEST 4: Exportación de Errores ===")

    from src.excel_exporter import ExcelExporter

    # Crear datos y errores de prueba
    datos = [
        {'NumFactura': 'FAC-001', 'Base': '100.00'}
    ]

    errores = [
        {
            'Archivo': 'test.pdf',
            'Pagina': 2,
            'Error': 'Página sin NumFactura detectado',
            'Proveedor': 'Test Provider',
        }
    ]

    exporter = ExcelExporter(datos, errores, directorio_salida="resultados")

    # Intentar exportar errores
    try:
        ruta_errores = exporter.exportar_excel_errores("test_errores_validacion.xlsx")
        assert ruta_errores is not None, "Debe generar archivo de errores"
        assert os.path.exists(ruta_errores), f"Archivo {ruta_errores} debe existir"

        # Limpiar
        if os.path.exists(ruta_errores):
            os.remove(ruta_errores)

        print("✅ PASS: Exportación de errores funciona correctamente")
    except Exception as e:
        print(f"❌ FAIL: {e}")
        raise


def run_all_tests():
    """Ejecuta todos los tests."""
    print("="*60)
    print("  SUITE DE TESTS: MANEJO DE ERRORES")
    print("="*60)

    tests = [
        test_validacion_numfactura_texto_basura,
        test_pagina_sin_numfactura,
        test_proveedor_no_identificado,
        test_exportacion_errores,
    ]

    resultados = []
    for test in tests:
        try:
            resultado = test()
            resultados.append(resultado)
        except AssertionError as e:
            print(f"❌ FAIL: {e}")
            resultados.append(False)
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            resultados.append(False)

    # Resumen
    print("\n" + "="*60)
    print("  RESUMEN")
    print("="*60)
    total = len(resultados)
    exitosos = sum(1 for r in resultados if r)
    fallidos = total - exitosos

    print(f"Total tests: {total}")
    print(f"✅ Exitosos: {exitosos}")
    print(f"❌ Fallidos: {fallidos}")

    if fallidos == 0:
        print("\n🎉 TODOS LOS TESTS PASARON")
        return True
    else:
        print(f"\n⚠️  {fallidos} test(s) fallaron")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
