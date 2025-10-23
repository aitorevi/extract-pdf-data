# 🚀 Crear Pull Request - Issue #1

## Opción 1: Desde GitHub Web (Recomendado)

### Paso 1: Ir a la URL del PR
```
https://github.com/aitorevi/extract-pdf-data/pull/new/feature/setup-pytest
```

### Paso 2: Llenar el formulario

**Título:**
```
Setup pytest - Issue #1
```

**Descripción:** (Copiar todo lo de abajo)

---

# Setup pytest - Issue #1

## 📋 Descripción

Configuración completa de pytest y estructura básica de testing para el proyecto.

## ✅ Cambios Realizados

### Archivos Creados
- ✅ `tests/__init__.py` - Package marker
- ✅ `tests/conftest.py` - 13 fixtures compartidas
- ✅ `tests/test_sample.py` - 8 tests de ejemplo
- ✅ `pytest.ini` - Configuración completa de pytest
- ✅ `.gitignore` - Ignorar archivos de test y cache

### Archivos Modificados
- ✅ `README.md` - Añadida sección de Testing con instrucciones

## 🧪 Tests

**8 tests creados, todos pasando:**
```
✅ test_pytest_works()
✅ test_fixtures_work()
✅ test_plantilla_valida_fixture()
✅ test_datos_factura_ejemplo_fixture()
✅ test_temp_directories()
✅ test_parametrize_example[2-2]
✅ test_parametrize_example[6-6]
✅ test_parametrize_example[5-5]
```

**Resultado:** `8 passed in 0.35s` ⚡

## 🛠️ Fixtures Creadas

- `project_root` - Ruta raíz del proyecto
- `facturas_dir`, `plantillas_dir`, `resultados_dir` - Directorios del proyecto
- `temp_facturas_dir`, `temp_plantillas_dir`, `temp_resultados_dir` - Directorios temporales
- `plantilla_valida` - Plantilla de ejemplo válida
- `plantilla_invalida` - Plantilla inválida para tests de error
- `datos_factura_ejemplo` - Datos de ejemplo para exportación
- `sample_plantilla_file` - Archivo de plantilla temporal

## 🏷️ Markers Configurados

```python
@pytest.mark.unit          # Tests unitarios
@pytest.mark.integration   # Tests de integración
@pytest.mark.slow         # Tests lentos
@pytest.mark.smoke        # Tests rápidos y críticos
```

## 🚀 Cómo Probar

```bash
# Ejecutar todos los tests
pytest

# Con coverage
pytest --cov=src --cov-report=html

# Solo smoke tests
pytest -m smoke
```

## 📝 Checklist

- [x] Tests creados y pasando
- [x] Fixtures configuradas
- [x] pytest.ini configurado
- [x] .gitignore actualizado
- [x] README actualizado
- [x] Markers configurados
- [x] Coverage funcionando

## 🎯 Issue Relacionado

Closes #1

---

**Ready for review! 🚀**

---

### Paso 3: Labels (si están disponibles)
- `priority:high`
- `type:testing`
- `phase:1-testing`

### Paso 4: Create Pull Request

### Paso 5: Merge
Una vez creado:
1. Revisar los cambios (si quieres)
2. Click en "Merge pull request"
3. Confirmar merge
4. Eliminar branch (opcional)

---

## Opción 2: Merge Local (Alternativa rápida)

Si prefieres hacer merge local sin PR:

```bash
# Volver a main
git checkout main

# Merge del branch
git merge feature/setup-pytest

# Push a remote
git push

# Opcional: Eliminar branch
git branch -d feature/setup-pytest
git push origin --delete feature/setup-pytest
```

---

## ¿Cuál prefieres?

- **Opción 1 (GitHub):** Más profesional, historial visible, code review
- **Opción 2 (Local):** Más rápido, menos overhead

---

**Recomendación:** Opción 1 para este proyecto, ya que estamos construyendo profesionalmente.
