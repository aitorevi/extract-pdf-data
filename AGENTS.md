# 🤖 Flujo de Trabajo con Claude Code - AGENTS.md

Este documento describe el flujo de trabajo estándar que usamos para desarrollar features en este proyecto usando Claude Code (AI Agent).

## 📋 Metodología: TDD (Test-Driven Development)

**Usamos TDD para desarrollar todas las features nuevas.** Esto significa:

1. **Primero escribimos los tests** que describen el comportamiento esperado
2. **Luego escribimos el código** para hacer que los tests pasen
3. **Refactorizamos** si es necesario, manteniendo los tests en verde

### Ventajas de TDD
- ✅ Código mejor diseñado desde el inicio
- ✅ Menos bugs en producción
- ✅ Documentación viva del comportamiento esperado
- ✅ Confianza para refactorizar
- ✅ Coverage alto de forma natural

## 🔄 Flujo de Trabajo Estándar (12 Pasos)

### 1. Crear Issue en GitHub
```bash
gh issue create --title "Título descriptivo" --body "Descripción detallada" --assignee @me
```

**Contenido del Issue:**
- Descripción clara del problema/feature
- Lista de tareas a realizar
- Archivos que se modificarán
- Criterios de aceptación
- Labels sugeridos (si existen)

### 2. Crear Feature Branch
```bash
git checkout -b feature/nombre-descriptivo
```

**Convención de nombres:**
- `feature/` - Nueva funcionalidad
- `fix/` - Corrección de bugs
- `refactor/` - Refactorización de código
- `test/` - Añadir/mejorar tests
- `docs/` - Documentación

### 3. Escribir Tests PRIMERO (TDD)

**Antes de escribir código de producción:**
```bash
# Crear archivo de test
tests/test_nombre_feature.py
```

**Los tests deben:**
- Describir el comportamiento esperado
- Cubrir casos normales y edge cases
- Ser claros y autoexplicativos
- Fallar inicialmente (Red)

### 4. Implementar la Funcionalidad

**Escribir el código mínimo para que los tests pasen:**
- Seguir el principio KISS (Keep It Simple, Stupid)
- Código limpio y legible
- Documentar funciones y clases
- Usar type hints cuando sea posible

### 5. Ejecutar Tests

```bash
# Ejecutar tests específicos
python -m pytest tests/test_nombre_feature.py -v

# Ejecutar todos los tests
python -m pytest -v

# Con coverage
python -m pytest --cov=src --cov-report=html
```

**Los tests deben:**
- ✅ Todos pasar (100%)
- ⚠️ Si alguno falla, arreglarlo antes de continuar

### 6. Refactorizar (si es necesario)

- Mejorar el código manteniendo los tests en verde
- Eliminar duplicación
- Mejorar nombres de variables/funciones
- Optimizar si es necesario

### 7. Commit con Mensaje Descriptivo

```bash
git add archivos_modificados
git commit -m "Título del commit - Issue #N

Descripción detallada de los cambios:
- Cambio 1
- Cambio 2
- Cambio 3

Tests: X/X passed ✅

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
"
```

**Convenciones de commits:**
- Primera línea: Título conciso (50 caracteres)
- Cuerpo: Descripción detallada
- Mencionar número de issue
- Incluir estado de tests
- Co-authored con Claude

### 8. Push a Remote

```bash
git push -u origin feature/nombre-descriptivo
```

### 9. Crear Pull Request

```bash
gh pr create --title "Título descriptivo - Issue #N" --body "Descripción" --base main
```

**Contenido del PR:**
- Resumen de cambios
- Lista de cambios detallados por archivo
- Comportamiento esperado
- Testing realizado
- Referencia al issue: `Closes #N`

### 10. Comentar en el Issue

```bash
gh issue comment N --body "✅ Solución implementada en PR #M"
```

**Incluir:**
- Resumen de la solución
- Link al PR
- Próximos pasos

### 11. Actualizar PROGRESS.md

**Añadir el progreso del issue completado:**

```markdown
### Issue #N: Título del Issue ✅
- [x] Branch creado
- [x] Tests implementados
- [x] Código implementado
- [x] PR creado y en revisión

**Tests**: X/X passed ✅

**Archivos modificados**:
- archivo1.py - Descripción
- archivo2.py - Descripción

**Commits**:
- `hash` - Descripción commit
```

**Actualizar secciones:**
- `Estado Actual` - Última actualización, rama actual, próximo paso
- `Completado` - Añadir el nuevo issue con detalles
- `En Progreso` - Actualizar con PR en revisión
- `Próximos Pasos` - Actualizar siguiente tarea

### 12. Review y Merge

- Revisar el PR (el usuario o colaboradores)
- Aprobar cambios
- Merge a `main`
- Cerrar el issue automáticamente

## 📁 Estructura de Archivos

```
extract-pdf-data/
├── src/                          # Código de producción
│   ├── pdf_extractor.py
│   ├── excel_exporter.py
│   └── main.py
├── tests/                        # Tests
│   ├── conftest.py              # Fixtures compartidas
│   ├── test_pdf_extractor.py
│   └── test_excel_exporter.py
├── plantillas/                   # Plantillas JSON
├── facturas/                     # PDFs de entrada
├── resultados/                   # Archivos de salida
├── .decisions/                   # Documentación de decisiones
│   ├── ADR_TEMPLATE.md
│   └── 2025-01/
│       ├── PLAN_DE_ACCION.md
│       ├── GITHUB_ISSUES.md
│       └── FASE1_ISSUES.md
├── .docs/                        # Documentación técnica
├── PROGRESS.md                   # Estado actual del proyecto
├── AGENTS.md                     # Este archivo
└── README.md                     # Documentación principal
```

## 🧪 Convenciones de Testing

### Nomenclatura de Tests
```python
def test_descripcion_comportamiento_esperado():
    """Descripción clara de qué se está probando."""
    # Arrange (preparar)
    # Act (ejecutar)
    # Assert (verificar)
```

### Markers de pytest
```python
@pytest.mark.unit          # Tests unitarios
@pytest.mark.integration   # Tests de integración
@pytest.mark.slow          # Tests lentos
@pytest.mark.smoke         # Tests rápidos críticos
```

### Coverage objetivo
- **Mínimo**: 80% por módulo
- **Ideal**: 90%+ en módulos core

## 🎯 Ejemplo Completo: Issue #3

### Paso 1: Crear Issue
```bash
gh issue create --title "Definir nombres de columnas estándar para exportación Excel"
```

### Paso 2: Crear Branch
```bash
git checkout -b feature/standardize-column-names
```

### Paso 3: Escribir Tests
```python
# tests/test_column_standardization.py
def test_columnas_estandar_en_datos_extraidos():
    """Verifica que los datos extraídos contienen las columnas estándar."""
    # Test implementation
```

### Paso 4: Implementar
```python
# src/pdf_extractor.py
MAPEO_CAMPOS = {
    'num-factura': 'NumFactura',
    'fecha-factura': 'FechaFactura',
    # ...
}
```

### Paso 5: Ejecutar Tests
```bash
python -m pytest tests/test_column_standardization.py -v
# 14/14 passed ✅
```

### Paso 6: Commit
```bash
git add tests/ src/
git commit -m "Estandarizar nombres de columnas - Issue #3"
```

### Paso 7: Push
```bash
git push -u origin feature/standardize-column-names
```

### Paso 8: PR
```bash
gh pr create --title "Estandarizar nombres de columnas - Issue #3" --base main
```

### Paso 9: Comentar
```bash
gh issue comment 3 --body "✅ Solución implementada en PR #4"
```

## 🚀 Comandos Útiles

### Git
```bash
# Ver status
git status

# Ver log bonito
git log --oneline --graph --all

# Ver diferencias
git diff

# Crear branch y cambiar
git checkout -b feature/nombre

# Cambiar de branch
git checkout nombre-branch

# Merge desde main
git checkout main
git pull
git checkout feature/nombre
git merge main
```

### GitHub CLI (gh)
```bash
# Ver issues
gh issue list

# Ver PRs
gh pr list

# Ver detalles de issue
gh issue view N

# Ver detalles de PR
gh pr view N

# Checkout de PR localmente
gh pr checkout N
```

### Testing
```bash
# Tests específicos
pytest tests/test_archivo.py::TestClass::test_method -v

# Con coverage
pytest --cov=src --cov-report=term-missing

# Solo smoke tests
pytest -m smoke

# Excluir tests lentos
pytest -m "not slow"

# Modo verbose
pytest -vv

# Mostrar print statements
pytest -s
```

## ✅ Checklist del Desarrollador

Antes de crear un PR, verificar:

- [ ] **Tests escritos y pasando** (TDD)
- [ ] **Código implementado** y funcionando
- [ ] **Coverage aceptable** (>80%)
- [ ] **Commit con mensaje descriptivo**
- [ ] **Branch actualizado** con main
- [ ] **Sin conflictos** con main
- [ ] **Documentación actualizada** (si aplica)
- [ ] **Issue creado** y asignado
- [ ] **PR creado** con descripción detallada
- [ ] **Comentario en issue** con link al PR
- [ ] **PROGRESS.md actualizado** con detalles del issue

## 📚 Recursos

### Documentación del Proyecto
- `README.md` - Guía de inicio
- `PROGRESS.md` - Estado actual
- `.decisions/2025-01/PLAN_DE_ACCION.md` - Plan maestro
- `.decisions/2025-01/GITHUB_ISSUES.md` - Issues planificadas
- `.docs/GUIA_TECNICA.md` - Documentación técnica

### Herramientas
- [pytest](https://docs.pytest.org/) - Framework de testing
- [GitHub CLI](https://cli.github.com/) - CLI de GitHub
- [Claude Code](https://claude.com/claude-code) - AI Coding Assistant

## 🤝 Colaboración con Claude Code

Este proyecto se desarrolla con asistencia de Claude Code (AI Agent). El workflow está optimizado para:

1. **Crear issues** estructurados y claros
2. **Seguir TDD** rigurosamente
3. **Automatizar** tareas repetitivas con gh CLI
4. **Mantener calidad** con tests y reviews
5. **Documentar** decisiones y cambios

Claude Code ayuda a:
- ✅ Escribir tests comprehensivos
- ✅ Implementar código limpio
- ✅ Crear commits descriptivos
- ✅ Generar documentación
- ✅ Seguir mejores prácticas

---

**Última actualización**: 2025-01-24
**Versión**: 1.0
**Autor**: Proyecto extract-pdf-data + Claude Code
