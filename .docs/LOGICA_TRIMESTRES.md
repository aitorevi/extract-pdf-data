# Lógica de Cálculo de Trimestres

## Resumen

El sistema utiliza **dos cálculos de trimestre diferentes** para propósitos distintos:

1. **Trimestre REAL** → Usado para índices, detección de duplicados y organización de archivos
2. **Trimestre para Excel** → Usado para la exportación a Excel con reglas de negocio

## 1. Trimestre REAL (para índices)

### Función
`PDFOrganizer.calcular_trimestre_real_para_indices(fecha_factura: str) -> Tuple[str, str]`

### Propósito
Calcula el trimestre cronológico **basándose únicamente en la fecha de factura**, sin aplicar ninguna regla de negocio.

### Usos
- Generar índices JSON de facturas por trimestre (`indice_YYYY_XT.json`)
- Detectar facturas duplicadas
- Organizar archivos en carpetas por trimestre real

### Lógica
```python
# Enero-Marzo → 1T
# Abril-Junio → 2T
# Julio-Septiembre → 3T
# Octubre-Diciembre → 4T

Ejemplos:
- 15/01/2025 → 1T 2025
- 15/06/2025 → 2T 2025
- 15/12/2025 → 4T 2025
- 15/12/2024 → 4T 2024 (NO cambia a 1T 2025 aunque el usuario procese con 1T 2025)
```

### Características importantes
- ✅ **NO** aplica reglas de negocio
- ✅ **NO** depende del trimestre seleccionado por el usuario
- ✅ Una factura de diciembre 2025 **SIEMPRE** será 4T 2025 en los índices
- ✅ Garantiza consistencia en la detección de duplicados

---

## 2. Trimestre para Excel (con lógica de negocio)

### Función
`PDFExtractor.determinar_trimestre_para_exportacion_excel(fecha_factura: datetime, trimestre_usuario: int, año_usuario: int) -> Optional[tuple]`

### Propósito
Calcula el trimestre que debe aparecer en el Excel **según reglas de negocio complejas**.

### Usos
- **ÚNICAMENTE** para la columna "Trimestre" en el archivo Excel exportado

### Lógica de negocio

#### Regla 1: Facturas del mismo año
```python
Si año_factura == año_usuario:
    Si trimestre_factura <= trimestre_usuario:
        → Usar trimestre_usuario
    Si trimestre_factura > trimestre_usuario:
        → Usar trimestre_factura
```

**Ejemplos (usuario selecciona 2T 2025):**
- Factura 15/01/2025 (1T) → **2T 2025** en Excel
- Factura 15/04/2025 (2T) → **2T 2025** en Excel
- Factura 15/07/2025 (3T) → **3T 2025** en Excel (usa su propio trimestre)
- Factura 15/10/2025 (4T) → **4T 2025** en Excel (usa su propio trimestre)

#### Regla 2: Caso especial T1 (incluye 4T del año anterior)
```python
Si trimestre_usuario == 1 AND año_factura == (año_usuario - 1) AND trimestre_factura == 4:
    → Marcar como 1T año_usuario
```

**Ejemplo (usuario selecciona 1T 2026):**
- Factura 15/12/2025 (4T 2025) → **1T 2026** en Excel
- Factura 15/03/2026 (1T 2026) → **1T 2026** en Excel

#### Regla 3: Otras facturas se excluyen
```python
Facturas de años diferentes (que no cumplen regla especial T1):
    → None (se excluyen del Excel)
```

**Ejemplo (usuario selecciona 2T 2025):**
- Factura 15/12/2024 → **Excluida** (no aparece en Excel)
- Factura 15/07/2024 → **Excluida**

---

## Comparación con Ejemplos

### Ejemplo 1: Usuario procesa con 1T 2026

| Fecha Factura | Trimestre REAL<br/>(índices) | Trimestre Excel<br/>(lógica negocio) |
|---------------|------------------------------|--------------------------------------|
| 15/12/2025    | **4T 2025**                  | **1T 2026** (caso especial)          |
| 15/01/2026    | **1T 2026**                  | **1T 2026**                          |
| 15/04/2026    | **2T 2026**                  | **2T 2026** (posterior, usa propio)  |

### Ejemplo 2: Usuario procesa con 3T 2025

| Fecha Factura | Trimestre REAL<br/>(índices) | Trimestre Excel<br/>(lógica negocio) |
|---------------|------------------------------|--------------------------------------|
| 15/01/2025    | **1T 2025**                  | **3T 2025** (anterior, usa usuario)  |
| 15/06/2025    | **2T 2025**                  | **3T 2025** (anterior, usa usuario)  |
| 15/09/2025    | **3T 2025**                  | **3T 2025** (igual, usa usuario)     |
| 15/12/2025    | **4T 2025**                  | **4T 2025** (posterior, usa propio)  |

---

## Detección de Duplicados

### Flujo de detección

1. Usuario vuelve a procesar una factura ya procesada anteriormente
2. Sistema calcula **trimestre REAL** de la fecha de factura
3. Busca en el índice del **trimestre REAL**
4. Si encuentra coincidencia (CIF + NumFactura + Fecha) → **DUPLICADO**
5. Mueve a carpeta `duplicados/YYYY/XT/`

### Ejemplo de detección correcta

**Primera ejecución (4T 2025):**
- Factura: 15/12/2025, CIF: B12345678, Num: F-001
- Trimestre real: 4T 2025
- Se guarda en índice: `indice_2025_4T.json`
- Se archiva en: `procesadas/2025/12/Proveedor/`

**Segunda ejecución (1T 2026):**
- MISMA factura: 15/12/2025, CIF: B12345678, Num: F-001
- Trimestre real: 4T 2025
- Busca en índice: `indice_2025_4T.json`
- ✅ **Encuentra duplicado**
- Mueve a: `duplicados/2025/4T/`

---

## Archivos de Índice

Los índices se guardan en: `facturas/procesadas/indices/indice_YYYY_XT.json`

### Estructura de índice
```json
{
  "trimestre": "4T",
  "año": 2025,
  "facturas": [
    {
      "cif_proveedor": "B12345678",
      "fecha_factura": "2025-12-15",
      "num_factura": "F-001",
      "nombre_archivo": "factura.pdf",
      "ruta_completa": "/path/to/procesadas/2025/12/Proveedor/factura.pdf",
      "fecha_procesamiento": "2025-01-20 10:30:00",
      "hash_md5": "abc123def456"
    }
  ]
}
```

### Nombres de archivos
- `indice_2025_1T.json` → Facturas de enero-marzo 2025
- `indice_2025_2T.json` → Facturas de abril-junio 2025
- `indice_2025_3T.json` → Facturas de julio-septiembre 2025
- `indice_2025_4T.json` → Facturas de octubre-diciembre 2025

---

## Funciones Clave

### Para Índices (sin lógica de negocio)
```python
# En file_organizer.py
organizador.calcular_trimestre_real_para_indices(fecha_factura: str) -> Tuple[str, str]
```

### Para Excel (con lógica de negocio)
```python
# En pdf_extractor.py
PDFExtractor.determinar_trimestre_para_exportacion_excel(
    fecha_factura: datetime,
    trimestre_usuario: int,
    año_usuario: int
) -> Optional[tuple]
```

### Otras funciones útiles
```python
# Calcular trimestre desde datetime (1-4)
PDFExtractor.calcular_trimestre_desde_fecha(fecha: datetime) -> int

# Formatear trimestre (1 → "1T")
PDFExtractor.formatear_trimestre(numero: int) -> str

# Parsear trimestre ("1T" → 1)
PDFExtractor.parsear_trimestre(trimestre_str: str) -> int
```

---

## Tests

### Tests para trimestre REAL (índices)
`tests/test_calculo_trimestre_indices.py`
- Verifica que el cálculo sea correcto para todos los meses
- Verifica que NO aplique lógica de negocio
- Verifica independencia del trimestre seleccionado por el usuario

### Tests para trimestre Excel (lógica de negocio)
`tests/test_trimestre_logica.py`
- Verifica todas las reglas de negocio
- Verifica caso especial T1 con año anterior
- Verifica exclusión de facturas fuera de período

### Tests de detección de duplicados
`tests/test_duplicados_cross_trimestre.py`
- Verifica detección de duplicados entre diferentes ejecuciones
- Verifica que no se creen índices duplicados
- Verifica que facturas se muevan a carpeta correcta

---

## Preguntas Frecuentes

### ¿Por qué una factura de diciembre 2025 aparece como 1T 2026 en el Excel?
Porque al procesar con 1T 2026, la regla de negocio incluye facturas del 4T del año anterior como parte del 1T actual. Esto es intencional para el Excel.

### ¿En qué índice se guarda una factura de diciembre 2025?
**SIEMPRE** en `indice_2025_4T.json`, independientemente del trimestre que el usuario haya seleccionado.

### ¿Cómo se detectan duplicados?
Se busca en el índice del **trimestre REAL** (calculado desde la fecha), NO del trimestre del Excel.

### Si reproceso con un trimestre diferente, ¿se duplican las facturas?
No. El sistema detecta duplicados usando el trimestre REAL, por lo que una factura de diciembre 2025 siempre se buscará en el índice de 4T 2025, independientemente del trimestre seleccionado.
