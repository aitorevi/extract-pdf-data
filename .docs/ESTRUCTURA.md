# Estructura del Proyecto

## 📁 Organización de Carpetas

```
extract-pdf-data/
│
├── src/                        # Código principal del sistema
│   ├── __init__.py
│   ├── main.py                 # Aplicación principal CLI
│   ├── pdf_extractor.py        # Extractor de datos de PDFs
│   ├── excel_exporter.py       # Exportador a Excel/CSV/JSON
│   └── editor_plantillas.py    # Editor visual de plantillas
│
├── utils/                      # Utilidades y herramientas auxiliares
│   ├── __init__.py
│   ├── ver_todas_palabras.py   # Debug: ver palabras de PDF
│   ├── copiar_estructura_plantilla.py  # Copiar estructura entre plantillas
│   └── instalar_poppler.py     # Instalador de Poppler
│
├── deprecated/                 # Archivos obsoletos (no usar)
│   ├── coordinate_extractor.py
│   ├── coordinate_extractor_visual.py
│   ├── crear_plantilla_facil.py
│   ├── crear_plantilla.py
│   ├── crear_plantilla.bat
│   └── demo.py
│
├── facturas/                   # PDFs a procesar (input)
├── plantillas/                 # Plantillas JSON
├── resultados/                 # Excel/CSV/JSON generados (output)
├── poppler/                    # Poppler instalado localmente
│
├── editor.py                   # ⚡ Script de acceso: Editor
├── extraer.py                  # ⚡ Script de acceso: Extracción
├── verificar.py                # ⚡ Script de acceso: Verificación
│
├── editor.bat                  # Windows: doble clic para editor
├── extraer.bat                 # Windows: doble clic para extraer
├── verificar.bat               # Windows: doble clic para verificar
│
├── COMANDOS.txt               # Cheat sheet de comandos
├── INSTRUCCIONES.txt          # Guía de uso completa
├── ESTRUCTURA.md              # Este archivo
└── requirements.txt           # Dependencias Python
```

## 🎯 Archivos Principales

### **Scripts de Acceso Rápido** (usar estos)
- `editor.py` - Abre el editor de plantillas
- `extraer.py` - Extrae datos de facturas
- `verificar.py` - Verifica estructura del proyecto

### **Módulos Core** (src/)
- `main.py` - CLI principal con todos los comandos
- `pdf_extractor.py` - Lógica de extracción de datos
- `excel_exporter.py` - Exportación a múltiples formatos
- `editor_plantillas.py` - Editor visual interactivo

### **Utilidades** (utils/)
- `ver_todas_palabras.py` - Debug para ver contenido del PDF
- `copiar_estructura_plantilla.py` - Reutilizar estructura de plantillas
- `instalar_poppler.py` - Instalador automático de Poppler

## 🚀 Comandos Rápidos

```bash
# 3 comandos principales:
python verificar.py    # Verificar que todo está listo
python editor.py       # Crear/editar plantillas
python extraer.py      # Procesar facturas

# Comando avanzado (CLI completa):
python src/main.py ayuda
```

## 📝 Flujo de Trabajo

1. **Verificar**: `python verificar.py`
2. **Crear plantilla**: `python editor.py`
3. **Colocar PDFs**: en carpeta `facturas/`
4. **Extraer**: `python extraer.py`
5. **Ver resultados**: en carpeta `resultados/`

## 🗑️ Archivos Deprecados

La carpeta `deprecated/` contiene archivos antiguos que ya no se usan.
**NO los uses** - están ahí solo como respaldo.

Archivos obsoletos reemplazados por `editor_plantillas.py`:
- `coordinate_extractor.py`
- `coordinate_extractor_visual.py`
- `crear_plantilla_facil.py`
- `crear_plantilla.py`

## 🔧 Mantenimiento

### Para desarrolladores:
- **Código principal**: Modificar archivos en `src/`
- **Nuevas utilidades**: Agregar en `utils/`
- **Scripts obsoletos**: Mover a `deprecated/`

### Imports:
- Desde raíz: `from src.main import FacturaExtractorApp`
- Entre módulos en src/: `from src.pdf_extractor import PDFExtractor`

## ❓ Ayuda

- Ver comandos: `cat COMANDOS.txt`
- Ver guía completa: `cat INSTRUCCIONES.txt`
- Ayuda CLI: `python src/main.py ayuda`
