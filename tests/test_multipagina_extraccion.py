"""
Tests para verificar la extracción correcta de PDFs multipágina.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pdf_extractor import PDFExtractor


def test_extraccion_1_factura_3_paginas():
    """Test: 1 factura en 3 páginas - debe extraer de la última página."""
    print("\n=== TEST 1: 1 Factura en 3 Páginas ===")

    extractor = PDFExtractor(trimestre="2T", año="2025")
    extractor.cargar_plantillas()

    pdf_path = "facturas/test_1factura_3paginas.pdf"
    if not os.path.exists(pdf_path):
        print(f"⚠️  SKIP: {pdf_path} no encontrado")
        return False

    proveedor_id = extractor.identificar_proveedor(pdf_path)
    if not proveedor_id:
        print("❌ FAIL: No se identificó el proveedor")
        return False

    lista_facturas = extractor.extraer_datos_factura_multipagina(pdf_path, proveedor_id)

    # Verificaciones
    assert len(lista_facturas) == 1, f"Debe extraer 1 factura, obtuvo {len(lista_facturas)}"

    factura = lista_facturas[0]
    assert factura['NumFactura'] == 'FAC-002', f"NumFactura debe ser FAC-002, obtuvo {factura['NumFactura']}"
    assert factura['_Total_Paginas'] == 3, f"Debe tener 3 páginas, obtuvo {factura['_Total_Paginas']}"
    assert factura['_Pagina'] == 3, f"Debe extraer de página 3, obtuvo {factura['_Pagina']}"
    assert factura['Base'] == '1250.75', f"Base debe ser 1250.75, obtuvo {factura['Base']}"

    print("✅ PASS: Extrae correctamente de la última página")



def test_extraccion_3_facturas_1_pagina():
    """Test: 3 facturas en 1 PDF - debe extraer las 3."""
    print("\n=== TEST 2: 3 Facturas en 1 PDF ===")

    extractor = PDFExtractor(trimestre="2T", año="2025")
    extractor.cargar_plantillas()

    pdf_path = "facturas/test_3facturas_1pagina.pdf"
    if not os.path.exists(pdf_path):
        print(f"⚠️  SKIP: {pdf_path} no encontrado")
        return False

    proveedor_id = extractor.identificar_proveedor(pdf_path)
    if not proveedor_id:
        print("❌ FAIL: No se identificó el proveedor")
        return False

    lista_facturas = extractor.extraer_datos_factura_multipagina(pdf_path, proveedor_id)

    # Verificaciones
    assert len(lista_facturas) == 3, f"Debe extraer 3 facturas, obtuvo {len(lista_facturas)}"

    nums_factura = [f['NumFactura'] for f in lista_facturas]
    assert 'FAC-003' in nums_factura, "Debe incluir FAC-003"
    assert 'FAC-004' in nums_factura, "Debe incluir FAC-004"
    assert 'FAC-005' in nums_factura, "Debe incluir FAC-005"

    print("✅ PASS: Extrae correctamente 3 facturas independientes")



def test_extraccion_base_acumulada():
    """Test: Base acumulada - debe extraer el total de la última página."""
    print("\n=== TEST 3: Base Acumulada (3 Páginas) ===")

    extractor = PDFExtractor(trimestre="1T", año="2025")
    extractor.cargar_plantillas()

    pdf_path = "facturas/test_base_acumulada.pdf"
    if not os.path.exists(pdf_path):
        print(f"⚠️  SKIP: {pdf_path} no encontrado")
        return False

    proveedor_id = extractor.identificar_proveedor(pdf_path)
    if not proveedor_id:
        print("❌ FAIL: No se identificó el proveedor")
        return False

    lista_facturas = extractor.extraer_datos_factura_multipagina(pdf_path, proveedor_id)

    # Verificaciones
    assert len(lista_facturas) == 1, f"Debe extraer 1 factura, obtuvo {len(lista_facturas)}"

    factura = lista_facturas[0]
    assert factura['NumFactura'] == 'FAC-BASE-001', f"NumFactura debe ser FAC-BASE-001"
    assert factura['_Total_Paginas'] == 3, f"Debe tener 3 páginas"
    assert factura['_Pagina'] == 3, f"Debe extraer de página 3"
    assert factura['Base'] == '1125.50', f"Base debe ser 1125.50 (total), obtuvo {factura['Base']}"

    print("✅ PASS: Extrae el total correcto de la última página")



def test_extraccion_1_factura_1_pagina():
    """Test: 1 factura en 1 página - caso básico."""
    print("\n=== TEST 4: 1 Factura en 1 Página ===")

    extractor = PDFExtractor(trimestre="2T", año="2025")
    extractor.cargar_plantillas()

    pdf_path = "facturas/test_1factura_1pagina.pdf"
    if not os.path.exists(pdf_path):
        print(f"⚠️  SKIP: {pdf_path} no encontrado")
        return False

    proveedor_id = extractor.identificar_proveedor(pdf_path)
    if not proveedor_id:
        print("❌ FAIL: No se identificó el proveedor")
        return False

    lista_facturas = extractor.extraer_datos_factura_multipagina(pdf_path, proveedor_id)

    # Verificaciones
    assert len(lista_facturas) == 1, f"Debe extraer 1 factura"

    factura = lista_facturas[0]
    assert factura['NumFactura'] == 'FAC-001', f"NumFactura debe ser FAC-001"
    assert factura['_Total_Paginas'] == 1, f"Debe tener 1 página"

    print("✅ PASS: Extrae correctamente factura simple")



def test_extraccion_pdf_mixto_complejo():
    """Test: PDF con facturas mixtas (algunas 1 pág, otras multipágina)."""
    print("\n=== TEST 5: PDF Mixto Complejo ===")

    extractor = PDFExtractor(trimestre="1T", año="2025")
    extractor.cargar_plantillas()

    pdf_path = "facturas/test_mixto_complejo.pdf"
    if not os.path.exists(pdf_path):
        print(f"⚠️  SKIP: {pdf_path} no encontrado")
        return False

    proveedor_id = extractor.identificar_proveedor(pdf_path)
    if not proveedor_id:
        print("❌ FAIL: No se identificó el proveedor")
        return False

    lista_facturas = extractor.extraer_datos_factura_multipagina(pdf_path, proveedor_id)

    # Verificaciones
    assert len(lista_facturas) == 4, f"Debe extraer 4 facturas, obtuvo {len(lista_facturas)}"

    # Crear diccionario por NumFactura para fácil acceso
    facturas_dict = {f['NumFactura']: f for f in lista_facturas}

    # FAC-MIX-001: 1 página
    assert 'FAC-MIX-001' in facturas_dict, "Debe incluir FAC-MIX-001"
    assert facturas_dict['FAC-MIX-001']['_Pagina'] == 1, "FAC-MIX-001 debe estar en página 1"
    assert facturas_dict['FAC-MIX-001']['_Total_Paginas'] == 1, "FAC-MIX-001 debe tener 1 página"
    assert facturas_dict['FAC-MIX-001']['Base'] == '100.00', "FAC-MIX-001 Base debe ser 100.00"

    # FAC-MIX-002: 2 páginas, extrae de la última (página 3)
    assert 'FAC-MIX-002' in facturas_dict, "Debe incluir FAC-MIX-002"
    assert facturas_dict['FAC-MIX-002']['_Pagina'] == 3, "FAC-MIX-002 debe extraer de página 3"
    assert facturas_dict['FAC-MIX-002']['_Total_Paginas'] == 2, "FAC-MIX-002 debe tener 2 páginas"
    assert facturas_dict['FAC-MIX-002']['Base'] == '500.00', "FAC-MIX-002 Base debe ser 500.00 (total, no 200)"

    # FAC-MIX-003: 1 página
    assert 'FAC-MIX-003' in facturas_dict, "Debe incluir FAC-MIX-003"
    assert facturas_dict['FAC-MIX-003']['_Pagina'] == 4, "FAC-MIX-003 debe estar en página 4"
    assert facturas_dict['FAC-MIX-003']['Base'] == '150.00', "FAC-MIX-003 Base debe ser 150.00"

    # FAC-MIX-004: 3 páginas, extrae de la última (página 7)
    assert 'FAC-MIX-004' in facturas_dict, "Debe incluir FAC-MIX-004"
    assert facturas_dict['FAC-MIX-004']['_Pagina'] == 7, "FAC-MIX-004 debe extraer de página 7"
    assert facturas_dict['FAC-MIX-004']['_Total_Paginas'] == 3, "FAC-MIX-004 debe tener 3 páginas"
    assert facturas_dict['FAC-MIX-004']['Base'] == '900.00', "FAC-MIX-004 Base debe ser 900.00 (total)"

    print("✅ PASS: Extrae correctamente PDF mixto (1 pág + multipágina)")



def run_all_tests():
    """Ejecuta todos los tests."""
    print("="*60)
    print("  SUITE DE TESTS: EXTRACCIÓN MULTIPÁGINA")
    print("="*60)

    tests = [
        test_extraccion_1_factura_1_pagina,
        test_extraccion_1_factura_3_paginas,
        test_extraccion_3_facturas_1_pagina,
        test_extraccion_base_acumulada,
        test_extraccion_pdf_mixto_complejo,
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
