# Deuda Técnica

Documento de registro de deuda técnica del proyecto Extract PDF Data.

---

## 🟡 MEDIA PRIORIDAD: Soporte para campos en páginas específicas cuando NumFactura no está en todas las páginas

**Fecha:** 2025-10-28
**Estado:** Pendiente (No bloqueante)
**Impacto:** Bajo - No afecta casos de uso actuales
**Esfuerzo estimado:** Medio (4-6 horas)

### Descripción del Problema

**Situación actual:**
El extractor (`pdf_extractor.py`) asume que el campo `NumFactura` está en **todas las páginas** de una factura multipágina, usando las mismas coordenadas. El flujo es:

1. Lee `NumFactura` de cada página usando las coordenadas de la plantilla
2. Agrupa páginas por número de factura encontrado
3. Extrae todos los campos de la **última página** de cada grupo

**Caso NO soportado actualmente:**
Factura de 3 páginas donde:
- `NumFactura` solo aparece en **página 1** en coordenadas `[100,50,200,70]`
- `Base` solo aparece en **página 3** en coordenadas `[100,200,300,250]`
- Páginas 2 y 3 no tienen `NumFactura` en esas coordenadas

**Comportamiento actual con este caso:**
- Página 1: encuentra `NumFactura = "FAC-001"` ✓
- Página 2: busca `NumFactura` en `[100,50,200,70]` → no encuentra → marca como `ERROR_SIN_NUMFACTURA` ✗
- Página 3: busca `NumFactura` en `[100,50,200,70]` → no encuentra → marca como `ERROR_SIN_NUMFACTURA` ✗

**Resultado:** Las páginas 2 y 3 se consideran errores en lugar de parte de la factura.

### Por qué no es urgente

**Análisis de casos reales:**
- Las facturas multipágina en producción tienen el número de factura repetido en todas las páginas
- Esto es una práctica común en facturación para trazabilidad
- No se ha identificado ningún proveedor que use el patrón problemático

### Solución propuesta (cuando sea necesario)

#### Opción 1: Usar campo `'pagina'` en plantillas (Recomendado)

**Cambios en el extractor:**

```python
def extraer_datos_factura_multipagina_v2(self, ruta_pdf: str, proveedor_id: str):
    """Versión mejorada que soporta campos en páginas específicas."""

    plantilla = self.plantillas_cargadas[proveedor_id]

    with pdfplumber.open(ruta_pdf) as pdf:
        # 1. Buscar NumFactura en la página especificada en la plantilla
        campo_numfactura = next(
            (c for c in plantilla['campos'] if c['nombre'] == 'NumFactura'),
            None
        )

        if not campo_numfactura:
            raise ValueError("Plantilla sin campo NumFactura")

        pagina_numfactura = campo_numfactura.get('pagina', 1) - 1  # 0-indexed
        coords_numfactura = campo_numfactura['coordenadas']

        # Extraer NumFactura de la página específica
        pagina = pdf.pages[pagina_numfactura]
        bbox = tuple(coords_numfactura)
        num_factura = pagina.crop(bbox).extract_text()

        # 2. Extraer cada campo de su página específica
        datos_factura = {'NumFactura': num_factura}

        for campo in plantilla['campos']:
            if campo['nombre'] == 'NumFactura':
                continue  # Ya extraído

            nombre = campo['nombre']
            coords = campo['coordenadas']
            pagina_campo = campo.get('pagina', 1) - 1  # Default página 1
            tipo = campo.get('tipo', 'texto')

            # Extraer de la página específica
            try:
                pagina = pdf.pages[pagina_campo]
                bbox = tuple(coords)
                texto = pagina.crop(bbox).extract_text()
                valor = self.procesar_campo(texto, tipo)

                # Mapear a nombre columna
                nombre_col = self.MAPEO_CAMPOS.get(nombre, nombre)
                datos_factura[nombre_col] = valor

            except IndexError:
                print(f"WARN: Página {pagina_campo + 1} no existe para campo {nombre}")
                datos_factura[nombre_col] = ''

        return [datos_factura]
```

**Cambios necesarios:**
1. Modificar `extraer_datos_factura_multipagina()` en `src/pdf_extractor.py`
2. Añadir validación de campo `'pagina'` en plantillas
3. Actualizar documentación del formato de plantillas

**Estructura de plantilla con páginas específicas:**
```json
{
  "nombre_proveedor": "Proveedor Ejemplo",
  "cif_proveedor": "B12345678",
  "campos": [
    {
      "nombre": "NumFactura",
      "coordenadas": [100, 50, 200, 70],
      "pagina": 1,
      "tipo": "texto"
    },
    {
      "nombre": "FechaFactura",
      "coordenadas": [100, 100, 200, 120],
      "pagina": 1,
      "tipo": "fecha"
    },
    {
      "nombre": "Base",
      "coordenadas": [100, 200, 300, 250],
      "pagina": 3,
      "tipo": "numerico"
    }
  ]
}
```

#### Opción 2: Detección inteligente de continuidad

Asumir que páginas consecutivas sin NumFactura son continuación de la factura anterior:

```python
def agrupar_paginas_por_factura_inteligente(self, paginas_data):
    """
    Agrupa páginas asumiendo que páginas sin NumFactura son
    continuación de la factura anterior.
    """
    grupos = {}
    num_factura_actual = None

    for pagina_info in paginas_data:
        num_fac = pagina_info['NumFactura']

        if num_fac:  # Página tiene NumFactura
            num_factura_actual = num_fac
            if num_fac not in grupos:
                grupos[num_fac] = []
            grupos[num_fac].append(pagina_info)
        else:  # Página sin NumFactura
            if num_factura_actual:
                # Asumir que es continuación de la factura anterior
                grupos[num_factura_actual].append(pagina_info)
            else:
                # Primera página sin NumFactura = error
                if 'ERROR_SIN_NUMFACTURA' not in grupos:
                    grupos['ERROR_SIN_NUMFACTURA'] = []
                grupos['ERROR_SIN_NUMFACTURA'].append(pagina_info)

    return grupos
```

**Pros:**
- No requiere modificar plantillas
- Funciona automáticamente

**Contras:**
- Menos explícito
- Puede agrupar incorrectamente si hay páginas en blanco o separadores

### Tests necesarios

Cuando se implemente, añadir estos tests en `tests/test_multipagina_campos_especificos.py`:

```python
def test_extraer_numfactura_solo_en_primera_pagina():
    """
    Test: NumFactura solo en página 1, Base solo en página 3.
    Debe extraer correctamente de ambas páginas.
    """
    plantilla = {
        'campos': [
            {'nombre': 'NumFactura', 'coordenadas': [100,50,200,70], 'pagina': 1},
            {'nombre': 'Base', 'coordenadas': [100,200,300,250], 'pagina': 3}
        ]
    }

    # Mock PDF con 3 páginas
    # Página 1: NumFactura = "FAC-001"
    # Página 2: vacía (continuación)
    # Página 3: Base = "1000.00"

    resultado = extractor.extraer_datos_factura_multipagina('test.pdf', 'test')

    assert len(resultado) == 1
    assert resultado[0]['NumFactura'] == "FAC-001"
    assert resultado[0]['Base'] == "1000.00"

def test_multiples_facturas_con_campos_en_diferentes_paginas():
    """
    Test: Múltiples facturas, cada una con campos en diferentes páginas.
    """
    # FAC-001: NumFactura en pág 1, Base en pág 2
    # FAC-002: NumFactura en pág 3, Base en pág 5

    resultado = extractor.extraer_datos_factura_multipagina('test.pdf', 'test')

    assert len(resultado) == 2
    assert resultado[0]['NumFactura'] == "FAC-001"
    assert resultado[0]['Base'] == "500.00"
    assert resultado[1]['NumFactura'] == "FAC-002"
    assert resultado[1]['Base'] == "750.00"
```

### Referencias

- **Código actual:** `src/pdf_extractor.py:683-850` (método `extraer_datos_factura_multipagina`)
- **Tests existentes:** `tests/test_multipagina_pdf.py`
- **Editor de plantillas:** Ya soporta campo `'pagina'` desde 2025-10-28
- **Discusión:** Conversación con usuario el 2025-10-28

### Criterios de activación

Implementar esta funcionalidad SI:
- [ ] Se identifica un proveedor con facturas donde NumFactura no está en todas las páginas
- [ ] El volumen de facturas de ese proveedor justifica el desarrollo (>50 facturas/mes)
- [ ] No es posible obtener PDFs con NumFactura en todas las páginas

### Notas adicionales

- El editor de plantillas (`src/editor_plantillas.py`) YA soporta el campo `'pagina'`
- Las plantillas generadas desde el 2025-10-28 incluyen el campo `'pagina'`
- Plantillas antiguas sin campo `'pagina'` asumen página 1 por defecto (compatibilidad hacia atrás)
- La implementación sería principalmente en `pdf_extractor.py`

---

## Historial de cambios

- **2025-10-28:** Creación del documento. Registro de caso de campos en páginas específicas.
