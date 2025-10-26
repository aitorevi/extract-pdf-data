# Fixtures - PDFs de Prueba

Esta carpeta contiene scripts para generar PDFs de prueba utilizados en la suite de tests.

## Scripts Disponibles

### `crear_pdf_prueba.py`
Crea PDFs de prueba básicos para testing.

**PDFs generados:**
- `test_1factura_1pagina.pdf` - Factura simple de 1 página
- `test_1factura_3paginas.pdf` - Factura con 3 páginas (base acumulada)
- `test_3facturas_1pagina.pdf` - 3 facturas en 1 PDF
- `test_error_sin_numfactura.pdf` - PDF con página sin NumFactura
- `test_mixto.pdf` - PDF mixto con varios casos

**Uso:**
```bash
python tests/fixtures/crear_pdf_prueba.py
```

### `crear_pdf_base_acumulada.py`
Crea un PDF específico para probar la extracción de base acumulada.

**PDF generado:**
- `test_base_acumulada.pdf` - Factura con 3 páginas donde la base se acumula (250 → 650 → 1125.50)

**Estructura:**
- Página 1: Base = 250.00€ (parcial)
- Página 2: Base = 650.00€ (acumulado parcial)
- Página 3: Base = 1125.50€ (TOTAL CORRECTO) ✓

**Uso:**
```bash
python tests/fixtures/crear_pdf_base_acumulada.py
```

### `crear_pdf_mixto_complejo.py`
Crea un PDF complejo con múltiples facturas, algunas de 1 página y otras multipágina.

**PDF generado:**
- `test_mixto_complejo.pdf` - 7 páginas con 4 facturas mixtas

**Estructura:**
- Página 1: FAC-MIX-001 (1 página) - Base: 100.00
- Páginas 2-3: FAC-MIX-002 (2 páginas) - Base: 500.00 (de página 3)
- Página 4: FAC-MIX-003 (1 página) - Base: 150.00
- Páginas 5-7: FAC-MIX-004 (3 páginas) - Base: 900.00 (de página 7)

**Uso:**
```bash
python tests/fixtures/crear_pdf_mixto_complejo.py
```

### `test_extraccion_multipagina.py`
Test antiguo, mantener por compatibilidad.

## Regenerar Todos los PDFs de Prueba

Para regenerar todos los PDFs de prueba:

```bash
cd tests/fixtures
python crear_pdf_prueba.py
python crear_pdf_base_acumulada.py
python crear_pdf_mixto_complejo.py
```

## Notas

- Los PDFs generados se guardan en la carpeta `facturas/`
- Todos los PDFs usan las coordenadas de la plantilla `test-1-fra-1-page.json`
- Los PDFs están configurados para el proveedor "Test Provider S.L." (CIF: B12345678)
- Requiere la librería `reportlab`: `pip install reportlab`

## Dependencias

```bash
pip install reportlab
```

## Archivos Generados

Los scripts generan PDFs en `facturas/`:
- `test_1factura_1pagina.pdf`
- `test_1factura_3paginas.pdf`
- `test_3facturas_1pagina.pdf`
- `test_error_sin_numfactura.pdf`
- `test_mixto.pdf`
- `test_base_acumulada.pdf`
- `test_mixto_complejo.pdf`

Estos PDFs son necesarios para ejecutar la suite de tests (`./ejecutar_tests.command`).
