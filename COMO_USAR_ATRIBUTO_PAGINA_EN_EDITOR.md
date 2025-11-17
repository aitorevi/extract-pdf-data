# Cómo Usar el Atributo "pagina" en el Editor de Plantillas

## 📝 Resumen Rápido

El editor **automáticamente decide** si usar páginas fijas o dinámicas según tus campos:

- **Campos en 1 sola página** → Te pregunta qué prefieres
- **Campos en múltiples páginas** → Usa páginas fijas automáticamente

---

## 🎯 Flujo de Trabajo

### Paso 1: Captura tus Campos Normalmente

1. Abre el editor: `python src/editor_plantillas.py`
2. Carga tu PDF
3. Navega entre páginas con `◀` y `▶`
4. Captura campos en cualquier página que necesites

**No te preocupes por la página aún**, solo captura los campos.

---

### Paso 2: Al Guardar - El Editor Decide

Cuando haces clic en "Guardar Plantilla", el editor analiza tus campos:

#### **Caso A: Todos los campos en UNA sola página**

El editor te muestra este diálogo:

```
┌──────────────────────────────────────────────────┐
│     Configuración de Páginas                     │
├──────────────────────────────────────────────────┤
│ Todos los campos están en página 1.             │
│                                                  │
│ ¿Cómo quieres configurar la extracción?         │
│                                                  │
│ • SÍ → Páginas FIJAS (siempre página 1)         │
│   Usar si las facturas SIEMPRE tienen           │
│   el mismo número de páginas                    │
│                                                  │
│ • NO → DINÁMICA (última página) ✓ Recomendado   │
│   Usar si las facturas pueden tener             │
│   diferente número de páginas                   │
│                                                  │
│ • Cancelar → Volver atrás                       │
└──────────────────────────────────────────────────┘
      [Sí]        [No]        [Cancelar]
```

**¿Qué elegir?**

- **Haz clic en "NO"** (recomendado) → Extracción DINÁMICA
  - ✅ Para facturas de 1 página
  - ✅ Para facturas que pueden tener 1, 2 o 3 páginas según contenido
  - ✅ Template SIN atributo `"pagina"`

- **Haz clic en "SÍ"** → Páginas FIJAS
  - Solo si las facturas SIEMPRE tienen 1 página
  - Template CON atributo `"pagina": 1`

#### **Caso B: Campos en MÚLTIPLES páginas**

El editor detecta automáticamente y guarda con páginas fijas:

```
Console:
Campos en múltiples páginas detectados: [1, 2]
Se guardarán con atributo 'pagina' (necesario para extracción correcta)
```

**No te pregunta nada**, simplemente guarda cada campo con su `"pagina"` correspondiente.

---

## 📚 Ejemplos Prácticos

### Ejemplo 1: Factura Simple (1 página)

**PDF:** `factura_proveedor_x.pdf` (1 página)

**Campos capturados:**
- NumFactura (página 1)
- FechaFactura (página 1)
- Base (página 1)

**Al guardar:** El editor pregunta → Eliges **"NO" (DINÁMICA)**

**Template generado:**
```json
{
  "nombre": "Base",
  "coordenadas": [100, 200, 300, 400],
  "tipo": "numerico"
  // SIN atributo "pagina"
}
```

**Resultado:** Funciona para facturas de 1, 2, 3+ páginas automáticamente.

---

### Ejemplo 2: Factura Variable (1-3 páginas)

**PDF:** `factura_gonzalo_ferri.pdf` (puede tener 1, 2 o 3 páginas)

**Campos capturados:**
- NumFactura (página 1)
- FechaFactura (página 1)
- Base (página 1 en este PDF, pero podría estar en pág 2 o 3 en otros)

**Al guardar:** El editor pregunta → Eliges **"NO" (DINÁMICA)**

**Template generado:**
```json
{
  "nombre": "Base",
  "coordenadas": [100, 200, 300, 400],
  "tipo": "numerico"
  // SIN "pagina" → extraerá de última página siempre
}
```

**Resultado:**
- Factura de 1 pág → Extrae Base de pág 1 (última)
- Factura de 2 pág → Extrae Base de pág 2 (última)
- Factura de 3 pág → Extrae Base de pág 3 (última)

---

### Ejemplo 3: Iberdrola (4 páginas fijas, campos en pág 1 y 2)

**PDF:** `iberdrola.pdf` (siempre 4 páginas)

**Campos capturados:**
- NumFactura (página 1)
- FechaFactura (página 1)
- Base (página 2) ← NO está en la última página
- CIF_Cliente (página 2)

**Al guardar:** El editor **NO pregunta**, detecta múltiples páginas automáticamente

**Template generado:**
```json
{
  "nombre": "NumFactura",
  "coordenadas": [161, 376, 235, 386],
  "tipo": "texto",
  "pagina": 1
},
{
  "nombre": "Base",
  "coordenadas": [527, 430, 555, 437],
  "tipo": "numerico",
  "pagina": 2  // ← Necesario (NO es última página)
}
```

**Resultado:** Extrae correctamente de páginas específicas.

---

## 🔄 Cambiar de Páginas Fijas a Dinámicas

Si ya tienes un template con `"pagina"` y quieres cambiarlo:

### Opción 1: Editar Manualmente el JSON

```json
// ANTES (páginas fijas)
{
  "nombre": "Base",
  "coordenadas": [100, 200, 300, 400],
  "tipo": "numerico",
  "pagina": 1  // ← Eliminar esta línea
}

// DESPUÉS (dinámica)
{
  "nombre": "Base",
  "coordenadas": [100, 200, 300, 400],
  "tipo": "numerico"
  // Sin "pagina"
}
```

### Opción 2: Usar el Script de Conversión

```bash
python scripts/convertir_a_paginas_dinamicas.py plantillas/proveedor.json
```

---

## ❓ Preguntas Frecuentes

### ¿Qué pasa si me equivoco?

No hay problema, siempre puedes:
1. Editar el JSON manualmente
2. Volver a abrir el template en el editor
3. Guardar de nuevo con la opción correcta

### ¿Puedo mezclar fijas y dinámicas?

**No**. Un template usa:
- **TODAS páginas fijas** (todos los campos tienen `"pagina"`)
- **TODAS dinámicas** (ningún campo tiene `"pagina"`)

La única excepción es cuando tienes campos en diferentes páginas (como Iberdrola).

### ¿Cómo sé cuál elegir si no estoy seguro?

**Regla simple:** Si tienes duda, elige **DINÁMICA** (NO).

Es más flexible y funciona en la mayoría de casos.

---

## 📖 Recursos Adicionales

- **Guía completa:** `GUIA_ATRIBUTO_PAGINA.md`
- **Ejemplos de templates:** `plantillas/`
- **Tests:** `tests/test_multipagina_pdf.py`

---

**Fecha:** 2025-11-08
**Versión:** 2.0