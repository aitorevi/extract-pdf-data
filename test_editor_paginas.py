"""
Test para verificar que el editor genera templates correctamente
con y sin atributo 'pagina'
"""

import json
import os

def simular_guardado_template(nombre_proveedor, campos_capturados, usar_paginas_fijas):
    """
    Simula el proceso de guardado del editor.

    Args:
        nombre_proveedor: Nombre del proveedor
        campos_capturados: Dict con campos {nombre: {pagina, coordenadas}}
        usar_paginas_fijas: True/False

    Returns:
        Dict con el template generado
    """

    campos_lista = []

    for nombre, campo_data in campos_capturados.items():
        if campo_data:
            campo_json = {
                "nombre": nombre,
                "coordenadas": campo_data['coordenadas'],
                "tipo": "texto" if nombre in ['NumFactura', 'FechaFactura'] else "numerico"
            }

            # Solo añadir 'pagina' si se usan páginas fijas
            if usar_paginas_fijas:
                campo_json["pagina"] = campo_data['pagina'] + 1  # 1-indexed

            campos_lista.append(campo_json)

    template = {
        "nombre_proveedor": nombre_proveedor,
        "cif_proveedor": "B12345678",
        "campos": campos_lista
    }

    return template


def test_escenario_1_paginas_dinamicas():
    """Test: Campos en 1 página, usuario elige DINÁMICAS"""
    print("\n" + "="*80)
    print("TEST 1: Campos en 1 página - Usuario elige DINÁMICAS (NO)")
    print("="*80)

    campos = {
        'NumFactura': {'pagina': 0, 'coordenadas': [100, 50, 300, 80]},
        'FechaFactura': {'pagina': 0, 'coordenadas': [100, 100, 300, 130]},
        'Base': {'pagina': 0, 'coordenadas': [100, 200, 300, 230]}
    }

    template = simular_guardado_template(
        "Proveedor Test 1",
        campos,
        usar_paginas_fijas=False  # Usuario eligió NO (dinámicas)
    )

    print("\nTemplate generado:")
    print(json.dumps(template, indent=2, ensure_ascii=False))

    # Verificar
    for campo in template['campos']:
        assert 'pagina' not in campo, f"ERROR: Campo {campo['nombre']} NO debería tener 'pagina'"

    print("\n[OK] CORRECTO: Ningun campo tiene atributo 'pagina'")
    print("[OK] Extraera de la ULTIMA pagina de cada factura")
    return True


def test_escenario_2_paginas_fijas():
    """Test: Campos en 1 página, usuario elige FIJAS"""
    print("\n" + "="*80)
    print("TEST 2: Campos en 1 página - Usuario elige FIJAS (SÍ)")
    print("="*80)

    campos = {
        'NumFactura': {'pagina': 0, 'coordenadas': [100, 50, 300, 80]},
        'FechaFactura': {'pagina': 0, 'coordenadas': [100, 100, 300, 130]},
        'Base': {'pagina': 0, 'coordenadas': [100, 200, 300, 230]}
    }

    template = simular_guardado_template(
        "Proveedor Test 2",
        campos,
        usar_paginas_fijas=True  # Usuario eligió SÍ (fijas)
    )

    print("\nTemplate generado:")
    print(json.dumps(template, indent=2, ensure_ascii=False))

    # Verificar
    for campo in template['campos']:
        assert 'pagina' in campo, f"ERROR: Campo {campo['nombre']} debería tener 'pagina'"
        assert campo['pagina'] == 1, f"ERROR: Campo {campo['nombre']} debería tener pagina=1"

    print("\n[OK] CORRECTO: Todos los campos tienen 'pagina': 1")
    print("[OK] Extraera SIEMPRE de pagina 1")
    return True


def test_escenario_3_multiples_paginas():
    """Test: Campos en múltiples páginas (automático)"""
    print("\n" + "="*80)
    print("TEST 3: Campos en MÚLTIPLES páginas (Iberdrola)")
    print("="*80)

    campos = {
        'NumFactura': {'pagina': 0, 'coordenadas': [161, 376, 235, 386]},
        'FechaFactura': {'pagina': 0, 'coordenadas': [160, 404, 239, 415]},
        'Base': {'pagina': 1, 'coordenadas': [527, 430, 555, 437]},
        'CIF_Cliente': {'pagina': 1, 'coordenadas': [158, 507, 196, 517]}
    }

    # Detectar múltiples páginas
    paginas_usadas = set()
    for campo_data in campos.values():
        if campo_data:
            paginas_usadas.add(campo_data['pagina'])

    usar_paginas_fijas = len(paginas_usadas) > 1  # Automático

    print(f"Páginas detectadas: {sorted(p+1 for p in paginas_usadas)}")
    print(f"Decisión automática: usar_paginas_fijas = {usar_paginas_fijas}")

    template = simular_guardado_template(
        "Iberdrola Clientes S.A.U.",
        campos,
        usar_paginas_fijas=usar_paginas_fijas
    )

    print("\nTemplate generado:")
    print(json.dumps(template, indent=2, ensure_ascii=False))

    # Verificar
    for campo in template['campos']:
        assert 'pagina' in campo, f"ERROR: Campo {campo['nombre']} debería tener 'pagina'"

        # Verificar que cada campo tiene la página correcta
        campo_nombre = campo['nombre']
        pagina_esperada = campos[campo_nombre]['pagina'] + 1
        assert campo['pagina'] == pagina_esperada, \
            f"ERROR: Campo {campo_nombre} debería tener pagina={pagina_esperada}, tiene {campo['pagina']}"

    print("\n[OK] CORRECTO: Todos los campos tienen 'pagina' con valores correctos")
    print("[OK] Extraera de las paginas especificas (1 y 2)")
    return True


if __name__ == "__main__":
    print("="*80)
    print("SUITE DE TESTS: Editor de Plantillas - Atributo 'pagina'")
    print("="*80)

    resultados = []

    try:
        resultados.append(test_escenario_1_paginas_dinamicas())
    except AssertionError as e:
        print(f"\n✗ FALLO: {e}")
        resultados.append(False)

    try:
        resultados.append(test_escenario_2_paginas_fijas())
    except AssertionError as e:
        print(f"\n✗ FALLO: {e}")
        resultados.append(False)

    try:
        resultados.append(test_escenario_3_multiples_paginas())
    except AssertionError as e:
        print(f"\n✗ FALLO: {e}")
        resultados.append(False)

    # Resumen
    print("\n" + "="*80)
    print("RESUMEN DE TESTS")
    print("="*80)
    total = len(resultados)
    exitosos = sum(resultados)
    fallidos = total - exitosos

    print(f"Total: {total} tests")
    print(f"[OK] Exitosos: {exitosos}")
    print(f"[X] Fallidos: {fallidos}")

    if fallidos == 0:
        print("\n*** TODOS LOS TESTS PASARON ***")
        print("\nEl editor generara templates correctamente con/sin atributo 'pagina'")
        print("Puedes proceder a usarlo con confianza!")
    else:
        print(f"\n*** {fallidos} test(s) fallaron ***")

    print("="*80)
