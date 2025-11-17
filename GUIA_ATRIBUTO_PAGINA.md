# Guía: Cuándo usar el atributo "pagina" en Templates

## Regla Simple

**¿El campo está en la ÚLTIMA página de la factura?**

- ✅ **SÍ** → **NO pongas** `"pagina"` (el sistema extraerá automáticamente de la última página)
- ❌ **NO** → **SÍ pon** `"pagina": N` (especifica de qué página extraer)

---

## Casos de Uso

### Caso 1: Factura SIEMPRE de 1 página

**Ejemplo:** Proveedor X siempre emite facturas de 1 sola página

```json
{
  "nombre": "Base",
  "coordenadas": [100, 200, 300, 400],
  "tipo": "numerico"
  // ← NO poner "pagina"
}
```

**Resultado:** Extraerá de la última página (que es la página 1)

---

### Caso 2: Factura con PÁGINAS VARIABLES (2-5 páginas)

**Ejemplo:** Proveedor Y emite facturas de 2, 3, 4 o 5 páginas según contenido

#### Opción A: Campo en la ÚLTIMA página (Total, Base final)

```json
{
  "nombre": "Base",
  "coordenadas": [100, 200, 300, 400],
  "tipo": "numerico"
  // ← NO poner "pagina" (extraerá de la última, sea pág 2, 3, 4 o 5)
}
```

#### Opción B: Campo en PÁGINA FIJA (Header en pág 1)

```json
{
  "nombre": "NumFactura",
  "coordenadas": [100, 50, 300, 80],
  "tipo": "texto",
  "pagina": 1  // ← SÍ poner "pagina" (siempre en pág 1)
}
```

---

### Caso 3: Factura SIEMPRE con MÚLTIPLES PÁGINAS FIJAS

**Ejemplo:** Iberdrola SIEMPRE tiene 4 páginas

- Página 1: NumFactura, FechaFactura
- Página 2: Base, CIF_Cliente
- Página 3-4: Detalles

```json
{
  "nombre": "NumFactura",
  "coordenadas": [100, 50, 300, 80],
  "tipo": "texto",
  "pagina": 1  // ← Extraer de página 1
},
{
  "nombre": "Base",
  "coordenadas": [400, 500, 500, 530],
  "tipo": "numerico",
  "pagina": 2  // ← Extraer de página 2 (NO es la última)
}
```

---

## Tabla de Decisión Rápida

| Situación | ¿Poner `"pagina"`? | Comportamiento |
|-----------|-------------------|----------------|
| Factura de 1 página | ❌ NO | Extrae de página 1 (última) |
| Campo en última página (páginas variables) | ❌ NO | Extrae de última (2, 3, 4...) |
| Campo en primera página (páginas variables) | ✅ SÍ: `"pagina": 1` | Extrae siempre de página 1 |
| Campo en página específica (no última) | ✅ SÍ: `"pagina": N` | Extrae de página N |

---

## Cómo Determinar la Estrategia

### Paso 1: Analiza varias facturas del proveedor (5-10 mínimo)

```bash
# Ver cuántas páginas tienen las facturas
ls facturas/proveedor_x/*.pdf | xargs -I {} sh -c 'echo "{}:"; pdfinfo {} | grep Pages'
```

### Paso 2: Identifica el patrón

- **¿Siempre el mismo número de páginas?** → Puedes usar `"pagina"` si quieres (opcional)
- **¿Varía el número de páginas?** → Solo usa `"pagina"` para campos que NO estén en la última

### Paso 3: Ubicación del campo

- **Campo en última página** (Total, Base final, Firma)
  → **NO** uses `"pagina"`

- **Campo en primera página** (Header, NumFactura, Fecha)
  → Solo si las facturas tienen más de 1 página, pon `"pagina": 1`

- **Campo en página intermedia** (Ej: tabla de conceptos en pág 2)
  → **SÍ** pon `"pagina": N`

---

## Ejemplos Reales del Proyecto

### ✅ Correcto: Gonzalo Ferri (1 página siempre)

```json
{
  "nombre": "Base",
  "coordenadas": [100, 200, 300, 400],
  "tipo": "numerico"
  // ← SIN "pagina" (extrae de última = pág 1)
}
```

### ✅ Correcto: Iberdrola (4 páginas siempre, Base en pág 2)

```json
{
  "nombre": "Base",
  "coordenadas": [527.53, 430.52, 555.26, 437.12],
  "tipo": "numerico",
  "pagina": 2  // ← CON "pagina" (Base NO está en última pág)
}
```

### ✅ Correcto: Proveedor X (2-4 páginas variables, Base en última)

```json
{
  "nombre": "Base",
  "coordenadas": [100, 200, 300, 400],
  "tipo": "numerico"
  // ← SIN "pagina" (extrae de última página siempre)
}
```

---

## Resumen

### 🎯 Regla de Oro

**Por defecto, NO uses `"pagina"`**

Solo usa `"pagina": N` cuando:

1. El campo NO está en la última página
2. La factura tiene múltiples páginas
3. Necesitas extraer de una página específica que no es la última

---

## Herramientas para Verificar

### Ver plantilla actual

```bash
python -c "import json; t=json.load(open('plantillas/proveedor.json'));
[print(f'{c[\"nombre\"]:20} pag={c.get(\"pagina\", \"ultima\")}') for c in t['campos']]"
```

### Analizar PDFs del proveedor

```bash
python scripts/analizar_paginas_proveedor.py proveedor_nombre
```

---

**Fecha:** 2025-11-08
**Autor:** Sistema de extracción PDF
**Versión:** 2.0
