# 🧪 FASE 1: Testing y Calidad - Issues para Crear

**Copiar estas 6 issues a GitHub para empezar**

---

## Issue #1: Configurar framework de testing (pytest)

**Labels:** `priority:high`, `type:testing`, `phase:1-testing`

### Descripción
Configurar pytest y estructura básica de testing para el proyecto.

### Tareas
- [ ] Instalar pytest y dependencias de testing (`pytest`, `pytest-cov`, `pytest-mock`)
- [ ] Crear carpeta `tests/` con estructura
- [ ] Configurar `pytest.ini` o `pyproject.toml`
- [ ] Crear fixtures básicas en `conftest.py`
- [ ] Documentar cómo ejecutar tests en README
- [ ] Añadir `tests/` a `.gitignore` (solo `__pycache__`)

### Archivos a crear
```
tests/
├── __init__.py
├── conftest.py              # Fixtures compartidas
├── test_pdf_extractor.py    # Tests para pdf_extractor
├── test_excel_exporter.py   # Tests para excel_exporter
└── test_integration.py      # Tests de integración
```

### Configuración pytest.ini
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --cov=src --cov-report=html --cov-report=term
```

### Criterios de Aceptación
- [ ] `pytest` ejecuta sin errores
- [ ] Estructura de tests creada
- [ ] README actualizado con instrucciones
- [ ] Coverage report funciona

---

## Issue #2: Tests unitarios para pdf_extractor.py

**Labels:** `priority:high`, `type:testing`, `phase:1-testing`

### Descripción
Crear tests unitarios completos para `src/pdf_extractor.py`

### Funciones a testear

#### 1. `cargar_plantillas()`
- [ ] Carga plantillas válidas correctamente
- [ ] Maneja directorio vacío
- [ ] Maneja plantillas inválidas (JSON malformado)
- [ ] Valida esquema de plantilla correctamente

#### 2. `identificar_proveedor()`
- [ ] Identifica proveedor por contenido
- [ ] Retorna None si no encuentra proveedor
- [ ] Funciona con diferentes codificaciones

#### 3. `extraer_datos_factura()`
- [ ] Extrae datos correctamente con plantilla válida
- [ ] Maneja campos faltantes
- [ ] Maneja coordenadas fuera de rango
- [ ] Procesa diferentes tipos de campos (texto, fecha, numérico)

#### 4. `procesar_directorio_facturas()`
- [ ] Procesa múltiples facturas
- [ ] Maneja directorio vacío
- [ ] Continúa si una factura falla
- [ ] Retorna estadísticas correctas

#### 5. `validar_plantilla()`
- [ ] Valida plantilla correcta
- [ ] Rechaza plantilla sin campos obligatorios
- [ ] Rechaza coordenadas inválidas

### Cobertura objetivo
- **Mínimo 80% coverage**

### Fixtures necesarias
```python
@pytest.fixture
def plantilla_valida():
    return {...}

@pytest.fixture
def pdf_factura_test():
    return "tests/fixtures/factura_test.pdf"

@pytest.fixture
def mock_pdf_extractor():
    return PDFExtractor(...)
```

---

## Issue #3: Tests unitarios para excel_exporter.py

**Labels:** `priority:high`, `type:testing`, `phase:1-testing`

### Descripción
Crear tests unitarios completos para `src/excel_exporter.py`

### Funciones a testear

#### 1. `exportar_a_excel()`
- [ ] Crea archivo Excel válido
- [ ] Columnas correctas
- [ ] Formato de celdas correcto
- [ ] Maneja datos vacíos
- [ ] Sobrescribe archivo existente si necesario

#### 2. `exportar_a_csv()`
- [ ] Crea archivo CSV válido
- [ ] Codificación UTF-8 correcta
- [ ] Separador correcto (coma o punto y coma)
- [ ] Maneja caracteres especiales

#### 3. `exportar_a_json()`
- [ ] JSON válido y bien formateado
- [ ] Estructura correcta
- [ ] Encoding UTF-8

#### 4. Formateo de datos
- [ ] Fechas en formato correcto
- [ ] Números con separadores correctos
- [ ] Valores nulos manejados

### Fixtures necesarias
```python
@pytest.fixture
def datos_ejemplo():
    return [
        {"proveedor": "Test", "fecha": "2025-01-01", ...},
        ...
    ]

@pytest.fixture
def temp_output_dir(tmp_path):
    return tmp_path / "resultados"
```

### Cobertura objetivo
- **Mínimo 80% coverage**

---

## Issue #4: Tests de integración para flujo completo

**Labels:** `priority:high`, `type:testing`, `phase:1-testing`

### Descripción
Tests end-to-end del flujo completo de extracción y exportación.

### Escenarios a testear

#### Escenario 1: Happy Path
```python
def test_flujo_completo_exitoso():
    """
    1. Cargar plantilla
    2. Procesar factura válida
    3. Exportar a Excel
    4. Verificar archivo creado y contenido correcto
    """
```

#### Escenario 2: Múltiples facturas
```python
def test_procesar_multiples_facturas():
    """
    Procesar 3+ facturas de diferentes proveedores
    y verificar consolidado correcto
    """
```

#### Escenario 3: Error Handling
```python
def test_factura_sin_plantilla():
    """Factura sin plantilla correspondiente"""

def test_plantilla_invalida():
    """Plantilla con JSON malformado"""

def test_carpeta_vacia():
    """Sin facturas para procesar"""
```

#### Escenario 4: Diferentes formatos
```python
def test_exportar_todos_formatos():
    """Exportar mismo dataset a Excel, CSV y JSON"""
```

### Fixtures necesarias
```python
@pytest.fixture
def setup_proyecto_test(tmp_path):
    """
    Crea estructura completa:
    - facturas/
    - plantillas/
    - resultados/
    """
    ...
```

---

## Issue #5: Tests para edge cases en plantillas

**Labels:** `priority:medium`, `type:testing`, `phase:1-testing`

### Descripción
Tests específicos para casos límite y peculiaridades de plantillas.

### Casos a testear

#### 1. Campos vacíos/opcionales
```python
def test_campo_opcional_vacio():
    """Campo opcional sin valor en PDF"""

def test_campo_obligatorio_vacio():
    """Campo obligatorio sin valor → debe fallar o alertar"""
```

#### 2. Coordenadas límite
```python
def test_coordenadas_fuera_de_rango():
    """Coordenadas x,y fuera del tamaño del PDF"""

def test_coordenadas_negativas():
    """Coordenadas negativas"""

def test_coordenadas_muy_pequenas():
    """Área de captura de 1x1 pixel"""
```

#### 3. Múltiples proveedores
```python
def test_proveedores_con_mismo_formato():
    """Dos proveedores con layouts similares"""

def test_proveedor_no_identificado():
    """PDF sin identificador de proveedor"""
```

#### 4. Caracteres especiales
```python
def test_caracteres_especiales_en_texto():
    """Tildes, ñ, símbolos €, etc."""

def test_numeros_con_diferentes_formatos():
    """1.000,00 vs 1,000.00 vs 1000.00"""
```

#### 5. Tipos de datos
```python
def test_fecha_formato_incorrecto():
    """Fecha en formato no esperado"""

def test_numero_con_texto():
    """Campo numérico con texto adicional"""
```

---

## Issue #6: Configurar CI/CD básico (GitHub Actions)

**Labels:** `priority:medium`, `type:feature`, `phase:1-testing`

### Descripción
Configurar GitHub Actions para ejecutar tests automáticamente.

### Tareas

#### 1. Crear workflow file
```yaml
# .github/workflows/tests.yml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: windows-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.13'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r .docs/requirements.txt
        pip install pytest pytest-cov

    - name: Run tests
      run: |
        pytest --cov=src --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

#### 2. Agregar badge al README
```markdown
[![Tests](https://github.com/usuario/repo/actions/workflows/tests.yml/badge.svg)](https://github.com/usuario/repo/actions/workflows/tests.yml)
[![Coverage](https://codecov.io/gh/usuario/repo/badge.svg)](https://codecov.io/gh/usuario/repo)
```

#### 3. Configurar Codecov (opcional)
- [ ] Crear cuenta en codecov.io
- [ ] Conectar repositorio
- [ ] Configurar threshold mínimo

### Criterios de Aceptación
- [ ] Tests ejecutan automáticamente en cada push
- [ ] Badge en README muestra estado
- [ ] Workflow falla si tests fallan
- [ ] Coverage report disponible

---

## 📝 Orden de Implementación Sugerido

1. **#1: Configurar pytest** ← EMPEZAR AQUÍ
   - Base para todo lo demás
   - ~2-3 horas

2. **#2: Tests pdf_extractor** ← LUEGO
   - Componente más crítico
   - ~1-2 días

3. **#3: Tests excel_exporter** ← DESPUÉS
   - Exportación es importante
   - ~1 día

4. **#4: Tests integración** ← DESPUÉS
   - Valida todo junto
   - ~1 día

5. **#5: Tests edge cases** ← EN PARALELO con 2-4
   - Puede hacerse paralelamente
   - ~1-2 días

6. **#6: CI/CD** ← ÚLTIMO
   - Cuando todos los tests estén listos
   - ~2-3 horas

---

## ⏱️ Estimación Total FASE 1

**Duración:** 3-4 semanas (part-time) o 1-2 semanas (full-time)

**Breakdown:**
- Configurar pytest: 0.5 días
- Tests unitarios: 4-5 días
- Tests integración: 1-2 días
- Tests edge cases: 1-2 días
- CI/CD: 0.5 días
- Buffer/fixes: 1-2 días

**Total:** ~8-12 días de trabajo efectivo

---

## ✅ Definition of Done (FASE 1)

La FASE 1 está completa cuando:
- [ ] Todas las 6 issues cerradas
- [ ] Coverage >80%
- [ ] CI/CD ejecutando automáticamente
- [ ] 0 tests fallando
- [ ] Documentación actualizada
- [ ] Badge en README verde

---

## 🚀 Cómo Empezar HOY

```bash
# 1. Crear estas 6 issues en GitHub
#    (Copiar y pegar desde este archivo)

# 2. Mover Issue #1 a "In Progress" en el Project Board

# 3. Crear branch
git checkout -b feature/setup-pytest

# 4. Instalar pytest
pip install pytest pytest-cov pytest-mock

# 5. Crear tests/__init__.py
mkdir tests
echo "" > tests/__init__.py

# 6. Crear pytest.ini
# ... (copiar configuración de Issue #1)

# 7. Primer test básico
# tests/test_sample.py
def test_true():
    assert True

# 8. Ejecutar
pytest

# 9. Commit y push
git add .
git commit -m "Setup pytest - Issue #1"
git push

# 10. Crear PR
```

---

**¡Todo listo para empezar la FASE 1! 🎯**
