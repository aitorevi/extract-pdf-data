# Directorio de Documentos

Esta carpeta contiene todos los documentos relacionados con el procesamiento de facturas PDF.

## Estructura

```
documentos/
├── por_procesar/              ← Coloca aquí tus PDFs pendientes
├── procesados/
│   ├── facturas/              ← PDFs organizados exitosamente
│   ├── indices/               ← Índices JSON por trimestre
│   ├── duplicados/            ← Facturas duplicadas
│   └── errores/               ← PDFs con errores de procesamiento
└── reportes/                  ← Reportes Excel por año/trimestre
```

## Uso Rápido

### 1. Colocar facturas para procesar
```bash
cp ~/Descargas/*.pdf documentos/por_procesar/
```

### 2. Ejecutar procesamiento
```bash
python main.py procesar
```

### 3. Verificar resultados
- **Facturas procesadas**: `documentos/procesados/facturas/YYYY/MM/Proveedor/`
- **Reportes Excel**: `documentos/reportes/YYYY/XT/`
- **Índices**: `documentos/procesados/indices/indice_YYYY_XT.json`

## Descripción de Subcarpetas

### `por_procesar/`
Directorio de entrada. Coloca aquí todos los PDFs de facturas que quieres procesar.

**Importante**: Los PDFs se MUEVEN (no se copian) después de procesarse. Esta carpeta debe quedar vacía después del procesamiento.

### `procesados/facturas/`
Facturas procesadas exitosamente, organizadas por:
- Año (del trimestre REAL de la factura)
- Mes (del trimestre REAL de la factura)
- Proveedor

Ejemplo: `2025/12/Telefonica/factura_diciembre.pdf`

### `procesados/indices/`
Índices JSON que registran todas las facturas procesadas por trimestre REAL.

Ejemplo: `indice_2025_4T.json` contiene todas las facturas de octubre-diciembre 2025.

**Uso**: Detección de duplicados y auditoría.

### `procesados/duplicados/`
Facturas detectadas como duplicadas (mismo CIF + Número de factura).

Organizadas por año y trimestre: `YYYY/XT/`

### `procesados/errores/`
PDFs que no se pudieron procesar por algún problema:
- Proveedor no identificado
- Campos obligatorios vacíos
- Formato inválido
- PDF corrupto

Los errores también se exportan en el archivo Excel de errores.

### `reportes/`
Reportes Excel organizados por año y trimestre: `YYYY/XT/`

Archivos generados:
- `FACTURAS_YYYY_XT.xlsx` - Excel principal (9 columnas para gestoría)
- `FACTURAS_DEBUG_YYYY_XT.xlsx` - Excel completo (todos los campos para debugging)
- `ERRORES_YYYY_XT.xlsx` - Registro de errores de procesamiento

## Más Información

Para documentación completa, consulta `.docs/ESTRUCTURA_V2.md` en el directorio raíz del proyecto.
