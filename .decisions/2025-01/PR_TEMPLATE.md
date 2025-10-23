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

## 📊 Configuración

### pytest.ini
- Testpaths: `tests/`
- Coverage automático: `--cov=src`
- Reportes: HTML + Terminal
- Markers personalizados
- Coverage threshold: 0% (temporal)

### .gitignore
- Cache de pytest
- Reportes de coverage
- Archivos temporales de tests

## 🚀 Cómo Probar

```bash
# Ejecutar todos los tests
pytest

# Con coverage
pytest --cov=src --cov-report=html

# Solo smoke tests
pytest -m smoke

# Solo tests unitarios
pytest -m unit
```

## 📝 Checklist

- [x] Tests creados y pasando
- [x] Fixtures configuradas
- [x] pytest.ini configurado
- [x] .gitignore actualizado
- [x] README actualizado con instrucciones
- [x] Markers configurados
- [x] Coverage funcionando

## 🎯 Issue Relacionado

Closes #1

## 📚 Documentación

- Ver `.decisions/2025-01/FASE1_ISSUES.md` para más detalles
- Ver `README.md` sección "Testing" para instrucciones de uso

## 🔜 Próximo Paso

Una vez merged, continuar con **Issue #2: Tests unitarios para pdf_extractor.py**

---

**Ready for review! 🚀**
