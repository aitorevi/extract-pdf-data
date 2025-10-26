# Tests - Extractor de Datos de Facturas PDF

Suite de tests automatizados para verificar la funcionalidad del sistema de extracción de facturas PDF.

## Estructura de Tests

### 1. `test_multipagina_extraccion.py`
Tests para verificar la extracción correcta de PDFs con múltiples páginas.

**Tests incluidos:**
- ✅ **test_extraccion_1_factura_1_pagina**: Verifica extracción básica de 1 factura en 1 página
- ✅ **test_extraccion_1_factura_3_paginas**: Verifica que extrae de la última página cuando una factura tiene 3 páginas
- ✅ **test_extraccion_3_facturas_1_pagina**: Verifica que extrae 3 facturas independientes de un PDF con 3 páginas
- ✅ **test_extraccion_base_acumulada**: Verifica que extrae el total correcto de la última página cuando hay base acumulada

### 2. `test_manejo_errores.py`
Tests para verificar el correcto manejo de errores.

**Tests incluidos:**
- ✅ **test_validacion_numfactura_texto_basura**: Verifica que rechaza texto basura como número de factura
- ✅ **test_pagina_sin_numfactura**: Verifica que páginas sin NumFactura se registran como error
- ✅ **test_proveedor_no_identificado**: Verifica que PDFs sin proveedor identificado se registran como error
- ✅ **test_exportacion_errores**: Verifica que se puede exportar el log de errores a Excel

## Ejecutar Tests

### Opción 1: Ejecutable macOS (Doble clic)
```bash
./ejecutar_tests.command
```

### Opción 2: Desde terminal
```bash
# Activar virtualenv
source .venv/bin/activate

# Ejecutar todos los tests
python tests/test_multipagina_extraccion.py
python tests/test_manejo_errores.py
```

### Opción 3: Ejecutar test individual
```bash
source .venv/bin/activate
python tests/test_multipagina_extraccion.py
```

## PDFs de Prueba Requeridos

Los tests requieren los siguientes PDFs en la carpeta `facturas/`:

- `test_1factura_1pagina.pdf` - 1 factura en 1 página
- `test_1factura_3paginas.pdf` - 1 factura en 3 páginas (FAC-002)
- `test_3facturas_1pagina.pdf` - 3 facturas en 1 PDF
- `test_base_acumulada.pdf` - Factura con base acumulada en 3 páginas
- `test_error_sin_numfactura.pdf` - PDF con página sin NumFactura
- `HBS.pdf` - PDF sin proveedor identificado (para test de errores)

## Resultados Esperados

Todos los tests deben pasar:
```
============================================================
  RESUMEN FINAL
============================================================
Total tests: 8
✅ Exitosos: 8
❌ Fallidos: 0

🎉 TODOS LOS TESTS PASARON
```

## Reglas de Negocio Verificadas

### Extracción Multipágina
1. **Una factura en múltiples páginas**: Se extrae de la última página
2. **Múltiples facturas en un PDF**: Se extrae cada una de su última página
3. **Base acumulada**: Se captura el total de la última página, no parciales

### Manejo de Errores
1. **Páginas sin NumFactura**: Se registran en el log de errores, NO en resultados
2. **Texto basura en NumFactura**: Se valida y rechaza ("Esta página", "continuación", etc.)
3. **Proveedor no identificado**: Se registra en el log de errores
4. **Excel de errores**: Se genera automáticamente con todos los errores detectados

## Añadir Nuevos Tests

Para añadir un nuevo test:

1. Crear función con prefijo `test_`:
```python
def test_mi_nuevo_caso():
    """Descripción del test."""
    print("\n=== TEST: Mi Nuevo Caso ===")

    # Tu código de test aquí
    assert condicion, "Mensaje de error"

    print("✅ PASS: Descripción del éxito")
    return True
```

2. Añadir a la lista de tests en `run_all_tests()`:
```python
tests = [
    test_existente_1,
    test_existente_2,
    test_mi_nuevo_caso,  # <-- Añadir aquí
]
```

3. Ejecutar para verificar:
```bash
python tests/test_multipagina_extraccion.py
```

## Notas

- Los tests son **independientes** y pueden ejecutarse en cualquier orden
- Cada test **limpia** sus propios errores antes de ejecutarse
- Los archivos temporales generados se **eliminan automáticamente**
- Los tests **NO modifican** los PDFs de prueba originales
