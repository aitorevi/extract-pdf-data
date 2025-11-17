# 📄 Extractor de Datos de Facturas PDF

Aplicación local para extraer datos de facturas en PDF y exportarlos a Excel/CSV/JSON.

## ⚡ Inicio Rápido

### Opción 1: Usando archivos .bat (doble clic)
1. Doble clic en `verificar.bat`
2. Doble clic en `editor.bat` (crear plantilla)
3. Colocar PDFs en carpeta `documentos/por_procesar/`
4. Doble clic en `extraer.bat`

### Opción 2: Usando Python
```bash
# 1. Verificar instalación
python scripts/verificar.py

# 2. Crear plantilla (primera vez)
python scripts/editor.py

# 3. Colocar PDFs en la carpeta documentos/por_procesar/

# 4. Extraer datos
python scripts/extraer.py
```

## 📦 Instalación

```bash
pip install -r .docs/requirements.txt
```

Poppler ya está incluido en el proyecto (carpeta `poppler/`).

## 📁 Estructura del Proyecto (v2.0)

```
extract-pdf-data/
├── src/                      # Código principal
├── utils/                    # Herramientas auxiliares
├── scripts/                  # Scripts de acceso rápido (.py)
├── documentos/               # 🆕 Directorio de documentos
│   ├── por_procesar/         #     PDFs pendientes (input)
│   ├── procesados/           #     PDFs organizados
│   │   ├── facturas/         #     Exitosos (por año/mes/proveedor)
│   │   ├── indices/          #     Índices JSON por trimestre
│   │   ├── duplicados/       #     Facturas duplicadas
│   │   └── errores/          #     PDFs con errores
│   └── reportes/             #     Excel por año/trimestre (output)
├── plantillas/               # Plantillas JSON
├── editor.bat                # ⚡ Doble clic: Editor
├── extraer.bat               # ⚡ Doble clic: Extraer
└── verificar.bat             # ⚡ Doble clic: Verificar
```

## 📚 Documentación

### Documentación General

Toda la documentación está en la carpeta `.docs/`:

- **[ESTRUCTURA_V2.md](.docs/ESTRUCTURA_V2.md)** - 🆕 Nueva estructura v2.0 (completa)
- **[LOGICA_TRIMESTRES.md](.docs/LOGICA_TRIMESTRES.md)** - 🆕 Cálculo de trimestres
- **[COBERTURA_TESTS.md](.docs/COBERTURA_TESTS.md)** - 🆕 Tests y cobertura
- **[COMANDOS.txt](.docs/COMANDOS.txt)** - Cheat sheet de comandos rápidos
- **[INSTRUCCIONES.txt](.docs/INSTRUCCIONES.txt)** - Guía completa de uso
- **[ESTRUCTURA.md](.docs/ESTRUCTURA.md)** - Estructura detallada (v1.x)
- **[MANUAL_USUARIO.md](.docs/MANUAL_USUARIO.md)** - Manual de usuario completo
- **[GUIA_TECNICA.md](.docs/GUIA_TECNICA.md)** - Documentación técnica
- **[RESUMEN_REORGANIZACION.md](.docs/RESUMEN_REORGANIZACION.md)** - Cambios recientes

### Guías de Plantillas

- **[GUIA_ATRIBUTO_PAGINA.md](GUIA_ATRIBUTO_PAGINA.md)** - 🆕 Cuándo usar el atributo "pagina" en templates
- **[COMO_USAR_ATRIBUTO_PAGINA_EN_EDITOR.md](COMO_USAR_ATRIBUTO_PAGINA_EN_EDITOR.md)** - 🆕 Uso del editor con páginas múltiples
- **[README_SISTEMA_HIBRIDO.md](README_SISTEMA_HIBRIDO.md)** - Sistema híbrido Templates + LLM

## 🚀 Uso

### Comandos Principales

**Opción A - Archivos .bat (más fácil):**
- Doble clic en `verificar.bat`
- Doble clic en `editor.bat`
- Doble clic en `extraer.bat`

**Opción B - Python:**
```bash
python scripts/verificar.py    # Verificar que todo está listo
python scripts/editor.py       # Crear/editar plantillas
python scripts/extraer.py      # Procesar facturas
```

### Flujo de Trabajo

1. **Verificar**: Doble clic en `verificar.bat`
2. **Crear plantilla**: Doble clic en `editor.bat` (solo primera vez por cada tipo de factura)
3. **Colocar PDFs**: en carpeta `documentos/por_procesar/`
4. **Extraer datos**: Doble clic en `extraer.bat`
5. **Ver resultados**: en carpeta `documentos/reportes/YYYY/XT/`

## 🔧 Comandos Avanzados

```bash
# Usar CLI completa
python src/main.py ayuda

# Procesar solo a Excel
python src/main.py procesar --formato excel

# Procesar solo a CSV
python src/main.py procesar --formato csv
```

## 🛠️ Herramientas Útiles

```bash
# Ver todas las palabras de un PDF (debug)
python utils/ver_todas_palabras.py documentos/por_procesar/mi_factura.pdf

# Copiar estructura de plantilla existente
python utils/copiar_estructura_plantilla.py
```

## 🧪 Testing

El proyecto incluye tests automatizados con pytest.

### Ejecutar todos los tests
```bash
pytest
```

### Ejecutar tests con coverage
```bash
pytest --cov=src --cov-report=html
```

### Ejecutar solo tests unitarios
```bash
pytest -m unit
```

### Ejecutar solo smoke tests (rápidos)
```bash
pytest -m smoke
```

### Ver reporte de coverage
```bash
# Se genera automáticamente en htmlcov/
# Abrir htmlcov/index.html en el navegador
```

### Estructura de tests
```
tests/
├── __init__.py           # Package marker
├── conftest.py          # Fixtures compartidas
├── test_sample.py       # Tests de ejemplo
├── test_pdf_extractor.py    # (próximamente)
├── test_excel_exporter.py   # (próximamente)
└── test_integration.py      # (próximamente)
```

## 📖 Más Información

Para más detalles, consulta la documentación en `.docs/`:

```bash
# Ver comandos rápidos
cat .docs/COMANDOS.txt

# Ver guía completa
cat .docs/INSTRUCCIONES.txt
```

## 🗺️ Roadmap y Planificación

Este proyecto está en desarrollo activo. Consulta la planificación en `.decisions/`:

- **[Plan de Acción](.decisions/2025-01/PLAN_DE_ACCION.md)** - Fases del proyecto y objetivos
- **[Roadmap](.decisions/2025-01/ROADMAP.md)** - Timeline y milestones
- **[GitHub Issues](.decisions/2025-01/GITHUB_ISSUES.md)** - Issues para crear en GitHub

### Fases del Proyecto

1. **FASE 1:** Testing y Calidad 🧪 (En planificación)
2. **FASE 2:** Arquitectura y Code Quality 🏗️
3. **FASE 3:** Corner Cases y Plantillas 🔧
4. **FASE 4:** Organización de Archivos 📂
5. **FASE 5:** Exportación y Campos 📊
6. **FASE 6:** Mejoras de Distribución 🚀
7. **FASE 7:** UI/UX 🎨

Ver [.decisions/2025-01/PLAN_DE_ACCION.md](.decisions/2025-01/PLAN_DE_ACCION.md) para más detalles.

## 🤝 Contribuir

### Para Desarrolladores

1. Revisa el [Plan de Acción](.decisions/2025-01/PLAN_DE_ACCION.md)
2. Consulta las [Issues de GitHub](.decisions/2025-01/GITHUB_ISSUES.md)
3. Lee los ADRs en `.decisions/` antes de hacer cambios grandes
4. Ejecuta los tests antes de hacer commits (cuando estén implementados)

### Reportar Issues

Usa las plantillas en `.decisions/2025-01/GITHUB_ISSUES.md` para crear issues en GitHub.

## 🤝 Soporte

Si encuentras problemas:
1. Revisa `.docs/INSTRUCCIONES.txt` - Solución de problemas
2. Ejecuta `python scripts/verificar.py` para diagnosticar
3. Verifica que Poppler esté instalado (carpeta `poppler/`)
4. Consulta las issues de GitHub

## 📝 Licencia

Este proyecto es de uso privado.
