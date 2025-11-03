# Estructura de Archivos v2.0

## Resumen de Cambios

La versión 2.0 introduce una reorganización completa de la estructura de archivos para mejorar la claridad, el mantenimiento y la escalabilidad del proyecto.

### Cambios Principales

| Aspecto | v1.x (Anterior) | v2.0 (Actual) |
|---------|----------------|---------------|
| **PDFs pendientes** | `facturas/` (raíz) | `documentos/por_procesar/` |
| **PDFs procesados** | `facturas/procesadas/` | `documentos/procesados/facturas/` |
| **Índices** | `facturas/procesadas/indices/` | `documentos/procesados/indices/` |
| **Duplicados** | `facturas/duplicados/` | `documentos/procesados/duplicados/` |
| **Errores** | `facturas/errores/` | `documentos/procesados/errores/` |
| **Reportes Excel** | `resultados/` (timestamps) | `documentos/reportes/YYYY/XT/` |
| **Plantillas** | `plantillas/` | `plantillas/` (sin cambios) |

---

## Estructura Completa v2.0

```
extract-pdf-data/
├── documentos/                          # 🆕 Directorio principal de documentos
│   ├── por_procesar/                    # 🆕 PDFs pendientes de procesar
│   │   └── *.pdf                        # Coloca aquí tus facturas PDF
│   │
│   ├── procesados/                      # 🆕 Resultados del procesamiento
│   │   ├── facturas/                    # PDFs organizados por año/mes/proveedor
│   │   │   └── YYYY/MM/Proveedor/       # Ej: 2025/12/Telefonica/factura.pdf
│   │   │
│   │   ├── indices/                     # 🆕 Índices por trimestre REAL
│   │   │   └── indice_YYYY_XT.json      # Ej: indice_2025_4T.json
│   │   │
│   │   ├── duplicados/                  # Facturas duplicadas
│   │   │   └── YYYY/XT/                 # Organizados por trimestre
│   │   │
│   │   └── errores/                     # PDFs con errores de procesamiento
│   │       └── YYYY/XT/                 # Organizados por trimestre
│   │
│   └── reportes/                        # 🆕 Reportes Excel organizados
│       └── YYYY/XT/                     # Ej: 2025/4T/
│           ├── FACTURAS_2025_4T.xlsx          # Excel principal (9 columnas)
│           ├── FACTURAS_DEBUG_2025_4T.xlsx    # Excel debug (todos los campos)
│           └── ERRORES_2025_4T.xlsx           # Errores de procesamiento
│
├── plantillas/                          # Plantillas JSON (sin cambios)
│   └── *.json                           # Configuraciones por proveedor
│
└── src/                                 # Código fuente (sin cambios)
```

---

## Descripción de Directorios

### 📁 `documentos/`
**Nuevo en v2.0**

Directorio raíz que contiene TODOS los documentos del sistema (PDFs, índices y reportes).

**Motivación**:
- Separar claramente documentos de código fuente
- Agrupar todo el contenido relacionado con facturas
- Facilitar backups (solo copiar `documentos/`)

---

### 📥 `documentos/por_procesar/`
**Nuevo en v2.0** (anteriormente `facturas/` en raíz)

Directorio de entrada para PDFs pendientes de procesar.

**Uso**:
```bash
# Copiar facturas para procesar
cp /descargas/*.pdf documentos/por_procesar/

# Ejecutar procesamiento
python main.py procesar
```

**Comportamiento**:
- Los PDFs se procesan y **se mueven** (no se copian) a su destino final
- Después del procesamiento, este directorio debe quedar vacío
- Si queda algún PDF, significa que no se pudo procesar

---

### ✅ `documentos/procesados/facturas/`
**Nuevo en v2.0** (anteriormente `facturas/procesadas/`)

Facturas procesadas exitosamente, organizadas jerárquicamente.

**Estructura**:
```
procesados/facturas/
└── 2025/                    # Año (del trimestre REAL de la factura)
    └── 12/                  # Mes (del trimestre REAL de la factura)
        └── Telefonica/      # Nombre del proveedor
            └── factura_diciembre.pdf
```

**Importante**:
- La organización se basa en el **trimestre REAL** de la fecha de factura
- NO se basa en el trimestre que el usuario seleccionó al procesar
- Una factura de 15/12/2025 SIEMPRE irá a `2025/12/`, incluso si se procesó con "1T 2026"

**Ejemplo de organización**:
```bash
# Factura: fecha=15/12/2025, procesada con trimestre=1T 2026
# Destino: procesados/facturas/2025/12/Proveedor/factura.pdf
#          ↑ año REAL    ↑ mes REAL
```

---

### 📇 `documentos/procesados/indices/`
**Nuevo en v2.0** (anteriormente `facturas/procesadas/indices/`)

**🎯 CAMBIO IMPORTANTE**: Los índices ahora están **FUERA** del directorio de facturas.

Índices JSON que registran todas las facturas procesadas por trimestre REAL.

**Estructura**:
```
procesados/indices/
├── indice_2025_1T.json      # Enero-Marzo 2025
├── indice_2025_2T.json      # Abril-Junio 2025
├── indice_2025_3T.json      # Julio-Septiembre 2025
└── indice_2025_4T.json      # Octubre-Diciembre 2025
```

**Contenido del índice**:
```json
{
  "trimestre": "4T",
  "año": 2025,
  "facturas": [
    {
      "cif_proveedor": "B12345678",
      "num_factura": "F-DIC-001",
      "fecha_factura": "2025-12-15",
      "nombre_archivo": "factura_diciembre.pdf",
      "ruta_completa": "/path/to/2025/12/Proveedor/factura_diciembre.pdf",
      "fecha_procesamiento": "2025-12-20T10:30:00",
      "hash_md5": "a1b2c3d4e5f6..."
    }
  ]
}
```

**Uso**:
- **Detección de duplicados**: Antes de procesar, se busca en el índice del trimestre REAL
- **Auditoría**: Registro completo de todas las facturas procesadas
- **Trazabilidad**: Fecha de procesamiento + hash MD5 para verificación

**Ventaja de estar fuera de `facturas/`**:
- Los índices son metadata, no documentos
- Facilita consultas sin navegar por la estructura de carpetas de facturas
- Simplifica backups selectivos

---

### 🔁 `documentos/procesados/duplicados/`
**Nuevo en v2.0** (anteriormente `facturas/duplicados/`)

Facturas detectadas como duplicadas, organizadas por trimestre.

**Estructura**:
```
procesados/duplicados/
└── 2025/                    # Año del trimestre REAL
    └── 4T/                  # Trimestre REAL de la factura
        └── factura_duplicada.pdf
```

**Detección de duplicados**:
1. Se calcula el trimestre REAL de la factura (por fecha)
2. Se busca en el índice de ese trimestre
3. Se compara CIF + Número de factura
4. Si existe → se mueve a `duplicados/YYYY/XT/`

**Ejemplo**:
```bash
# Primera ejecución con 4T 2025
# Factura: CIF=B12345678, Num=F-001, Fecha=15/12/2025
# → Procesada y guardada en procesados/facturas/2025/12/

# Segunda ejecución con 1T 2026 (mismo PDF)
# → Sistema busca en índice 2025_4T (trimestre REAL)
# → Detecta duplicado por CIF + Num
# → Mueve a procesados/duplicados/2025/4T/
```

---

### ⚠️ `documentos/procesados/errores/`
**Nuevo en v2.0** (anteriormente `facturas/errores/`)

PDFs que no se pudieron procesar correctamente.

**Estructura**:
```
procesados/errores/
└── 2025/                    # Año del trimestre de procesamiento
    └── 4T/                  # Trimestre de procesamiento
        └── factura_con_error.pdf
```

**Tipos de errores comunes**:
- Proveedor no identificado (sin plantilla)
- Campos obligatorios vacíos (NumFactura, FechaFactura)
- Formato de fecha inválido
- PDF corrupto o ilegible
- CIF inválido

**Registro de errores**:
Los errores se exportan también en `documentos/reportes/YYYY/XT/ERRORES_YYYY_XT.xlsx`

---

### 📊 `documentos/reportes/`
**Nuevo en v2.0** (anteriormente `resultados/` con timestamps)

**🎯 CAMBIO IMPORTANTE**: Reportes Excel ahora organizados por **año y trimestre** con nombres estandarizados.

**Estructura antigua (v1.x)**:
```
resultados/
├── facturas_formateadas_20250115_143022.xlsx
├── facturas_completas_20250115_143022.xlsx
├── facturas_20250114_090045.xlsx
└── facturas_basicas_20250115_143022.xlsx
```
❌ Difícil de encontrar reportes por trimestre

**Estructura nueva (v2.0)**:
```
documentos/reportes/
├── 2025/
│   ├── 1T/
│   │   ├── FACTURAS_2025_1T.xlsx
│   │   ├── FACTURAS_DEBUG_2025_1T.xlsx
│   │   └── ERRORES_2025_1T.xlsx
│   ├── 2T/
│   ├── 3T/
│   └── 4T/
│       ├── FACTURAS_2025_4T.xlsx
│       ├── FACTURAS_DEBUG_2025_4T.xlsx
│       └── ERRORES_2025_4T.xlsx
└── 2026/
    └── 1T/
```
✅ Organización clara por período fiscal

**Tipos de reportes**:

#### 1. `FACTURAS_YYYY_XT.xlsx` - Excel Principal
**Propósito**: Reporte fiscal limpio con las 9 columnas requeridas

Columnas:
1. CIF_Cliente
2. Nombre_Proveedor
3. CIF_Proveedor
4. NumFactura
5. FechaFactura
6. Base
7. Cuota
8. Trimestre (según lógica de negocio)
9. Año (según lógica de negocio)

**Uso**: Entregar a gestoría/asesor fiscal

#### 2. `FACTURAS_DEBUG_YYYY_XT.xlsx` - Excel Completo
**Propósito**: Debugging y auditoría con TODOS los campos extraídos

Columnas adicionales:
- Todos los campos auxiliares
- Metadata (_NombreArchivo, _RutaArchivo, etc.)
- Información de procesamiento

**Uso**: Debugging, auditoría interna, verificación de plantillas

#### 3. `ERRORES_YYYY_XT.xlsx` - Registro de Errores
**Propósito**: Documentar facturas que no se pudieron procesar

Columnas:
- NombreArchivo
- _TipoError
- _MensajeError
- Datos parciales extraídos (si existen)

**Uso**: Identificar y corregir problemas de procesamiento

---

## Flujo de Procesamiento v2.0

### 1. Preparación
```bash
# Colocar PDFs en la carpeta de entrada
cp ~/Descargas/*.pdf documentos/por_procesar/
```

### 2. Procesamiento
```bash
python main.py procesar

# El sistema solicita:
# - Trimestre (1, 2, 3 o 4)
# - Año (ej: 2025)
```

### 3. Resultados

Para cada factura procesada:

1. **Extracción de datos** → Se leen todos los campos según la plantilla
2. **Cálculo de trimestre REAL** → Basado SOLO en la fecha de factura
3. **Detección de duplicados** → Búsqueda en índice del trimestre REAL
4. **Organización del PDF**:
   - ✅ **Exitoso** → `procesados/facturas/YYYY/MM/Proveedor/`
   - 🔁 **Duplicado** → `procesados/duplicados/YYYY/XT/`
   - ⚠️ **Error** → `procesados/errores/YYYY/XT/`
5. **Actualización de índice** → Se registra en `indices/indice_YYYY_XT.json`
6. **Exportación de reportes** → Se generan en `reportes/YYYY/XT/`

### 4. Verificación

```bash
# Verificar que no quedan PDFs pendientes
ls documentos/por_procesar/
# (debe estar vacío)

# Revisar reportes generados
ls documentos/reportes/2025/4T/
# FACTURAS_2025_4T.xlsx
# FACTURAS_DEBUG_2025_4T.xlsx
# ERRORES_2025_4T.xlsx (si hubo errores)

# Verificar índices
ls documentos/procesados/indices/
# indice_2025_4T.json
```

---

## Diferencias Clave: v1.x vs v2.0

### 1. Nombres de Directorios

| v1.x | v2.0 | Razón del cambio |
|------|------|------------------|
| `facturas/` (raíz) | `documentos/por_procesar/` | "facturas" era ambiguo (¿pendientes o procesadas?) |
| `facturas/procesadas/` | `documentos/procesados/facturas/` | Mejor jerarquía |
| `facturas/procesadas/indices/` | `documentos/procesados/indices/` | Índices fuera de facturas (son metadata) |
| `resultados/` | `documentos/reportes/YYYY/XT/` | Organización por período fiscal |

### 2. Organización de Reportes

**v1.x**:
```
resultados/facturas_formateadas_20250115_143022.xlsx
resultados/facturas_completas_20250115_143022.xlsx
```
- Basado en timestamps
- Difícil encontrar reportes de un trimestre específico
- Nombres inconsistentes

**v2.0**:
```
documentos/reportes/2025/4T/FACTURAS_2025_4T.xlsx
documentos/reportes/2025/4T/FACTURAS_DEBUG_2025_4T.xlsx
```
- Organizado por año/trimestre
- Nombres estandarizados
- Fácil navegación

### 3. Ubicación de Índices

**v1.x**: `facturas/procesadas/indices/indice_2025_4T.json`
**v2.0**: `documentos/procesados/indices/indice_2025_4T.json`

**Ventaja**: Los índices son metadata, no documentos. Sacarlos de la carpeta de facturas los hace más accesibles.

---

## Migración de v1.x a v2.0

### Opción 1: Migración Manual

```bash
# 1. Crear nueva estructura
mkdir -p documentos/por_procesar
mkdir -p documentos/procesados/{facturas,indices,duplicados,errores}
mkdir -p documentos/reportes

# 2. Mover PDFs pendientes
mv facturas/*.pdf documentos/por_procesar/

# 3. Mover facturas procesadas
mv facturas/procesadas/* documentos/procesados/facturas/

# 4. Mover índices
mv facturas/procesadas/indices/* documentos/procesados/indices/

# 5. Mover duplicados y errores
mv facturas/duplicados/* documentos/procesados/duplicados/
mv facturas/errores/* documentos/procesados/errores/

# 6. Reorganizar reportes (opcional pero recomendado)
# Los reportes antiguos pueden quedarse en resultados/
# Los nuevos se generarán en documentos/reportes/

# 7. Limpiar estructura antigua
rm -rf facturas/
rm -rf resultados/  # Opcional: hacer backup primero
```

### Opción 2: Empezar de Cero

Si tienes pocos datos o quieres empezar limpio:

```bash
# 1. Hacer backup de estructura antigua
mv facturas facturas_backup_v1
mv resultados resultados_backup_v1

# 2. Ejecutar el programa con la nueva estructura
python main.py verificar
# (creará automáticamente los directorios necesarios)

# 3. Procesar nuevas facturas
cp facturas_backup_v1/*.pdf documentos/por_procesar/
python main.py procesar
```

---

## Beneficios de v2.0

### ✅ Claridad
- Nombres descriptivos (`por_procesar` vs `facturas`)
- Jerarquía lógica (todo bajo `documentos/`)
- Separación clara entre tipos de contenido

### ✅ Organización
- Reportes por año/trimestre (vs timestamps)
- Índices accesibles fuera de la estructura de facturas
- Nombres de archivo estandarizados

### ✅ Escalabilidad
- Fácil añadir más años sin contaminar el directorio raíz
- Estructura preparada para múltiples empresas (futuro)
- Metadata separada de documentos

### ✅ Mantenimiento
- Backups más fáciles (`cp -r documentos/ backup/`)
- Navegación intuitiva en el sistema de archivos
- Limpieza periódica simplificada

### ✅ Compatibilidad con Herramientas
- Estructura estándar reconocible
- Fácil integración con scripts de automatización
- Compatible con sistemas de gestión documental

---

## Preguntas Frecuentes

### ¿Qué pasa con mis datos antiguos?

Los datos antiguos NO se migran automáticamente. Puedes:
1. Migrarlos manualmente (ver sección de migración)
2. Mantener ambas estructuras temporalmente
3. Empezar de cero con v2.0

### ¿Los índices de v1.x son compatibles?

Sí, el formato JSON del índice no ha cambiado. Solo cambió su ubicación.

### ¿Puedo cambiar el directorio base?

Sí, al instanciar las clases:

```python
extractor = PDFExtractor(directorio_facturas="mi_carpeta/pendientes")
organizador = PDFOrganizer(directorio_base="mi_carpeta")
```

### ¿Por qué los reportes usan el trimestre seleccionado por el usuario?

Los reportes Excel están diseñados para uso fiscal. El trimestre que selecciona el usuario representa el período fiscal al que quiere asignar las facturas, según las reglas de negocio (ver `.docs/LOGICA_TRIMESTRES.md`).

Los índices, en cambio, usan el trimestre REAL para garantizar la detección correcta de duplicados.

---

## Referencias

- **Lógica de Trimestres**: Ver `.docs/LOGICA_TRIMESTRES.md`
- **Cobertura de Tests**: Ver `.docs/COBERTURA_TESTS.md`
- **Guía de Uso**: `python main.py ayuda`

---

**Versión del documento**: 2.0
**Última actualización**: 2025-01-20
**Compatibilidad**: extract-pdf-data v2.0+
