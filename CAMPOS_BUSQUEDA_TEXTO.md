# Campos con Búsqueda por Texto (Regex)

## 🎯 ¿Para qué sirve?

El tipo de campo **`busqueda_texto`** permite extraer datos de PDFs cuando **la posición del campo varía** según el contenido dinámico de la factura.

### Problema que resuelve

Algunos proveedores emiten facturas donde ciertos campos (como "Base imponible") **no están siempre en la misma posición** porque dependen del número de líneas de detalle:

- Factura con 3 líneas → Base aparece en Y=320
- Factura con 8 líneas → Base aparece en Y=400
- Factura con 15 líneas → Base aparece en Y=520

Con coordenadas fijas, esto falla. Con **búsqueda por texto**, el sistema encuentra el campo sin importar su posición.

---

## 📋 Sintaxis en Plantillas JSON

### Estructura básica

```json
{
    "nombre": "Base",
    "tipo": "busqueda_texto",
    "patron_busqueda": "Base\\s*imponible[:\\s]+([\\d.,]+)",
    "area_busqueda": [0, 200, 595, 700],
    "tipo_dato": "numerico",
    "pagina": 1
}
```

### Parámetros

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `nombre` | string | ✅ Sí | Nombre del campo a extraer |
| `tipo` | string | ✅ Sí | Debe ser `"busqueda_texto"` |
| `patron_busqueda` | string | ✅ Sí | Expresión regular para buscar el valor. El primer grupo capturado `(...)` será el valor extraído |
| `area_busqueda` | array[4] | ❌ No | Coordenadas `[x0, top, x1, bottom]` que limitan el área de búsqueda. Si se omite, busca en toda la página |
| `tipo_dato` | string | ❌ No | Tipo de dato para limpieza: `"texto"`, `"numerico"`, `"fecha"`. Default: `"texto"` |
| `pagina` | int | ❌ No | Número de página (1-indexed). Default: `1` |

---

## 🔍 Patrones Regex Comunes

### 1. Buscar valor numérico después de etiqueta

```json
{
    "nombre": "Base",
    "tipo": "busqueda_texto",
    "patron_busqueda": "Base\\s*imponible[:\\s]+([\\d.,]+)",
    "tipo_dato": "numerico"
}
```

**Captura:**
- "Base imponible: 1234.56" → `1234.56`
- "Base imponible 1234.56" → `1234.56`
- "Base    imponible:  1,234.56" → `1,234.56`

### 2. Buscar múltiples variantes de etiqueta

```json
{
    "nombre": "Base",
    "tipo": "busqueda_texto",
    "patron_busqueda": "(?:Base\\s*imponible|Base|TOTAL\\s*BASE)[:\\s]*([\\d.,]+)",
    "tipo_dato": "numerico"
}
```

**Captura:**
- "Base imponible: 1234.56" → `1234.56`
- "Base: 1234.56" → `1234.56`
- "TOTAL BASE 1234.56" → `1234.56`

### 3. Buscar fecha con formato específico

```json
{
    "nombre": "FechaFactura",
    "tipo": "busqueda_texto",
    "patron_busqueda": "Fecha\\s*(?:de\\s*)?[Ff]actura[:\\s]+(\\d{2}[/-]\\d{2}[/-]\\d{4})",
    "tipo_dato": "fecha"
}
```

**Captura:**
- "Fecha Factura: 15/01/2025" → `15/01/2025`
- "Fecha de factura 15-01-2025" → `15-01-2025`

### 4. Buscar número de factura

```json
{
    "nombre": "NumFactura",
    "tipo": "busqueda_texto",
    "patron_busqueda": "N[uúº\\.º]*\\s*(?:Factura|FACTURA)[:\\s#]*([A-Z0-9/-]+)",
    "tipo_dato": "texto"
}
```

**Captura:**
- "Nº Factura: F-2025/001" → `F-2025/001`
- "N. FACTURA #12345" → `12345`
- "Núm. factura: A/2025/123" → `A/2025/123`

### 5. Buscar CIF/NIF

```json
{
    "nombre": "CIF_Identificacion",
    "tipo": "busqueda_texto",
    "patron_busqueda": "(?:CIF|NIF)[:\\s]*([A-Z]\\d{8})",
    "tipo_dato": "texto"
}
```

**Captura:**
- "CIF: B98852643" → `B98852643`
- "NIF B98852643" → `B98852643`

---

## 📐 Área de Búsqueda

El parámetro `area_busqueda` define un rectángulo donde buscar el texto:

```json
"area_busqueda": [x0, top, x1, bottom]
```

### Coordenadas en puntos PDF

- **x0**: Margen izquierdo (0 = borde izquierdo de la página)
- **top**: Margen superior (0 = parte superior de la página)
- **x1**: Margen derecho (595 = borde derecho para A4 vertical)
- **bottom**: Margen inferior (842 = parte inferior para A4 vertical)

### Ejemplos de áreas comunes

```json
// Buscar solo en la columna derecha (datos de factura)
"area_busqueda": [400, 0, 595, 300]

// Buscar en la mitad inferior de la página (zona de totales)
"area_busqueda": [0, 400, 595, 842]

// Buscar en toda la página (área completa)
"area_busqueda": null  // O simplemente omitir el parámetro

// Área específica para Networks Fibra Valencia (columna derecha, zona variable)
"area_busqueda": [500, 200, 595, 750]
```

---

## 💡 Consejos para Crear Patrones Efectivos

### 1. Usa grupos de captura `(...)`

El valor extraído será **el primer grupo capturado** entre paréntesis:

```regex
Base:\s*([\\d.,]+)
         ^^^^^^^^
         Este es el valor que se captura
```

### 2. Haz el patrón flexible con `\s*`

Permite espacios opcionales o múltiples:

```regex
Base\s*imponible[:\s]+
     ^^          ^^
     Espacios opcionales y variables
```

### 3. Usa alternativas con `|`

Para buscar múltiples variantes:

```regex
(?:Base|TOTAL|Importe)
   ^^^^^^^^^^^^^^^
   Busca cualquiera de estas palabras
```

### 4. Escapa caracteres especiales

En JSON debes escapar la barra invertida `\`:

| Regex | En JSON |
|-------|---------|
| `\s` | `"\\s"` |
| `\d` | `"\\d"` |
| `\.` | `"\\."` |

### 5. Sé específico pero flexible

```regex
// ❌ Demasiado estricto (puede fallar con variaciones)
Base imponible: (\d+\.\d{2})

// ✅ Flexible y robusto
Base\s*imponible[:\s]*([\\d.,]+)
```

### 6. Prueba con regex101.com

Usa [regex101.com](https://regex101.com) para probar tus patrones antes de agregarlos a la plantilla.

---

## 📝 Ejemplo Completo: Networks Fibra Valencia

```json
{
    "nombre_proveedor": "Networks Fibra Valencia S.L.",
    "cif_proveedor": "B98852643",
    "campos": [
        {
            "nombre": "NumFactura",
            "coordenadas": [525, 43, 574, 52],
            "tipo": "texto",
            "pagina": 1
        },
        {
            "nombre": "FechaFactura",
            "coordenadas": [495, 54, 573, 63],
            "tipo": "fecha",
            "pagina": 1
        },
        {
            "nombre": "Base",
            "tipo": "busqueda_texto",
            "patron_busqueda": "(?:Base\\s*imponible|Base|TOTAL\\s*BASE)[:\\s]*([\\d]+[.,]\\d{2})",
            "area_busqueda": [500, 200, 595, 750],
            "tipo_dato": "numerico",
            "pagina": 1,
            "comentario": "Campo con posición variable según líneas de factura"
        }
    ]
}
```

---

## 🔧 Debugging

Si el campo no se extrae correctamente:

1. **Verifica el patrón regex** en regex101.com con texto de ejemplo del PDF
2. **Amplía el área de búsqueda** temporalmente para cubrir toda la página:
   ```json
   "area_busqueda": [0, 0, 595, 842]
   ```
3. **Revisa los logs** durante la extracción:
   ```
   [Búsqueda texto] Encontrado: '1234.56' usando patrón: Base\s*imponible...
   ```
4. **Asegúrate de que el texto existe** en el PDF (no es una imagen escaneada sin OCR)

---

## ⚡ Ventajas vs Coordenadas Fijas

| Aspecto | Coordenadas Fijas | Búsqueda por Texto |
|---------|-------------------|-------------------|
| **Precisión** | 100% (si el formato no cambia) | 95-98% (depende del patrón) |
| **Robustez** | ❌ Falla si cambia la posición | ✅ Funciona independiente de posición |
| **Velocidad** | ⚡ Muy rápida | ⚡ Rápida (milisegundos) |
| **Costo** | $0 | $0 |
| **Complejidad** | ✅ Simple (solo coordenadas) | ⚠️ Requiere regex |
| **Mantenimiento** | ⚠️ Requiere actualizar si cambia layout | ✅ No requiere cambios |

---

## 🎓 Casos de Uso Ideales

### ✅ Cuándo usar búsqueda por texto

- Campos que cambian de posición según contenido dinámico
- Proveedores que modifican layouts frecuentemente
- Facturas con número variable de líneas de detalle
- Cuando necesitas extraer un campo por su etiqueta, no su posición

### ❌ Cuándo NO usar búsqueda por texto

- Si las coordenadas fijas funcionan bien (son más precisas)
- Campos sin etiqueta distintiva (usa coordenadas)
- Cuando hay múltiples valores similares en la página (usa área específica)

---

## 🔗 Ver También

- [README_SISTEMA_HIBRIDO.md](README_SISTEMA_HIBRIDO.md) - Sistema híbrido Templates + LLM
- [src/pdf_extractor.py:456](src/pdf_extractor.py) - Implementación de `_buscar_texto_en_pdf()`
- [plantillas/networks_fibra_valencia.json](plantillas/networks_fibra_valencia.json) - Ejemplo real

---

## 📞 Soporte

Si tienes dudas o problemas:

1. Revisa los logs de extracción para ver qué patrón está intentando
2. Prueba tu regex en [regex101.com](https://regex101.com)
3. Amplía temporalmente el `area_busqueda` para diagnosticar
4. Como último recurso, el sistema caerá automáticamente a LLM fallback si tienes configurada la API key

