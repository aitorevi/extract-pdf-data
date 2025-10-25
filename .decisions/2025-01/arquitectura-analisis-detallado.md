# 🏗️ Análisis Arquitectónico Detallado - extract-pdf-data

**Fecha:** 2025-10-25
**Autor:** Claude Code + Equipo
**Estado:** Completado
**Relacionado con:** ADR-001, Issue #7

---

## 📋 Resumen Ejecutivo

### Estado Actual: **Bueno (7/10)**

**Fortalezas:**
- ✅ Código funcional con 79% coverage
- ✅ 154 tests pasando (2 skipped)
- ✅ Separación básica de responsabilidades
- ✅ Tests bien estructurados con fixtures compartidas

**Debilidades:**
- ❌ Sin logging estructurado (solo `print()`)
- ❌ Lógica de negocio en main.py
- ❌ Duplicación menor de código
- ❌ Responsabilidades mezcladas en módulos

**Recomendación:** Refactorización pragmática incremental (10-12 horas de inversión)

---

## 1. ESTRUCTURA ACTUAL

### Módulos en `src/`

```
src/
├── main.py              (212 statements, 91% coverage)
├── pdf_extractor.py     (294 statements, 91% coverage)
├── excel_exporter.py    (241 statements, 81% coverage)
└── editor_plantillas.py (332 statements, 58% coverage)
```

### Responsabilidades por Módulo

#### **main.py - FacturaExtractorApp**
**Líneas:** 320 | **Coverage:** 91%

**Responsabilidades (mezcladas):**
- ✅ Orquestación del flujo (CLI + Interactivo)
- ⚠️ Validación de entrada (debería ser en validator)
- ⚠️ Verificación de estructura del proyecto
- ✅ Coordinación entre PDFExtractor y ExcelExporter
- ✅ Mostrar estadísticas y banners

**Problemas:**
- Hace demasiadas cosas (validación + orquestación + UI)
- Difícil testear lógica de validación por separado
- No hay separación clara entre CLI y lógica

---

#### **pdf_extractor.py - PDFExtractor**
**Líneas:** 631 | **Coverage:** 91%

**Responsabilidades (mezcladas):**
- ✅ Carga y validación de plantillas JSON
- ✅ Identificación automática de proveedores
- ⚠️ Extracción de texto de PDFs (I/O + procesamiento)
- ⚠️ Limpieza de datos (debería ser utils separado)
- ✅ Detección de duplicados
- ⚠️ Generación de estadísticas (debería ser en service)

**Funciones Largas:**
- `procesar_directorio_facturas()`: ~94 líneas (ALTA complejidad)
- `extraer_datos_factura()`: ~89 líneas (MEDIA complejidad)
- `limpiar_fecha()`: ~51 líneas (MEDIA complejidad, pero bien documentada)

**Problemas:**
- Mezcla I/O (cargar plantillas) con lógica de negocio
- Limpieza de datos debería estar en utils
- Estadísticas deberían ser en service separado

---

#### **excel_exporter.py - ExcelExporter**
**Líneas:** 528 | **Coverage:** 81%

**Responsabilidades (mezcladas):**
- ✅ Exportación a Excel (3 variantes: básico, completo, formateado)
- ✅ Exportación a CSV y JSON
- ⚠️ Formateo de hojas con estilos (debería ser formatter)
- ⚠️ Filtrado de columnas (duplicado en múltiples métodos)
- ⚠️ Estadísticas por proveedor y por campo (debería ser service)

**Funciones Largas:**
- `exportar_excel_formateado()`: ~46 líneas (MEDIA-ALTA)
- `_crear_hoja_resumen()`: ~67 líneas (MEDIA-ALTA)

**Duplicación Significativa:**
```python
# Se repite en 5 lugares diferentes:
datos_estandar = self._filtrar_columnas_estandar(...)
```

**Problemas:**
- Mezcla exportación + formateo + estadísticas
- Duplicación de filtrado de columnas
- Pattern Strategy incipiente pero sin interfaz común

---

#### **editor_plantillas.py - EditorPlantillas**
**Líneas:** 619 | **Coverage:** 58%

**Responsabilidades (adecuadas para GUI):**
- ✅ GUI Tkinter para capturar coordenadas
- ✅ Carga/edición de plantillas existentes
- ✅ Persistencia JSON
- ✅ Visualización con Pillow

**Problemas:**
- Coverage bajo (58%) pero ESPERADO para GUI
- Difícil testear eventos de UI (mouse, drag, etc.)
- Lógica de negocio bien separada y testeada

**Nota:** Este módulo está bien para ser GUI. No requiere cambios mayores.

---

## 2. PATRONES DE DISEÑO ACTUALES

### Patrones Identificables

| Patrón | Ubicación | Evaluación | Acción |
|--------|-----------|-----------|--------|
| **Singleton implícito** | FacturaExtractorApp | ✅ Bien usado | Mantener |
| **Repository-like** | PDFExtractor.cargar_plantillas() | ⚠️ Parcial | Mejorar |
| **Template Method** | ExcelExporter (3 exportadores) | ❌ Débil - duplicación | Refactorizar |
| **Strategy** | Exporters (excel, csv, json) | ⚠️ Incipiente | Formalizar |
| **Builder** | EditorPlantillas | ✅ Implícito | Mantener |

### Acoplamiento Actual

```
┌─────────────────────────────────────────┐
│             main.py                      │
│        (Orquestador)                     │
└──────────┬──────────────┬────────────────┘
           │              │
    ┌──────▼─────┐   ┌───▼────────────┐
    │PDFExtractor│   │ ExcelExporter  │
    └──────┬─────┘   └───┬────────────┘
           │             │
    ┌──────▼─────────────▼──────┐
    │   Librerías externas      │
    │ pdfplumber, pandas, etc.  │
    └───────────────────────────┘
```

**Evaluación:** Acoplamiento entre módulos principales es **bajo** (bueno), pero acoplamiento interno es **medio-alto** (mejorable).

---

## 3. ANÁLISIS DE CALIDAD

### 3.1 Funciones Complejas

| Función | Módulo | Líneas | Complejidad | Acción Sugerida |
|---------|--------|--------|-------------|----------------|
| `procesar_directorio_facturas()` | pdf_extractor.py | 94 | ALTA | Dividir en métodos |
| `exportar_excel_formateado()` | excel_exporter.py | 46 | MEDIA-ALTA | Extraer formatters |
| `_crear_hoja_resumen()` | excel_exporter.py | 67 | MEDIA-ALTA | Extraer calculadores |
| `extraer_datos_factura()` | pdf_extractor.py | 89 | MEDIA | Dividir responsabilidades |
| `limpiar_fecha()` | pdf_extractor.py | 51 | MEDIA | Mover a utils |

**Nota:** Ninguna función es crítica, pero hay espacio para mejoras.

---

### 3.2 Duplicación de Código

#### **Duplicación Alta:**

**1. Filtrado de columnas** (5 ubicaciones)
```python
# excel_exporter.py - líneas 32, 79, 139, 403, 432
datos_estandar = self._filtrar_columnas_estandar(datos, excluir_duplicados, excluir_errores)
```

**Impacto:** Cambios en filtrado requieren modificar 5 lugares.

**Solución:**
```python
def _export_generic(self, data, format, exclude_dups=True, exclude_errors=True):
    filtered = self._filtrar_columnas_estandar(data, exclude_dups, exclude_errors)
    # Export según format
```

---

**2. Inicialización de datos con errores** (2 ubicaciones)
```python
# pdf_extractor.py - líneas 513, 534
datos_error = {
    'CIF': '',
    'FechaFactura': '',
    'Trimestre': self.trimestre,
    'Año': self.anio,
    # ... 6 campos más
}
```

**Impacto:** Añadir un campo requiere 2 cambios.

**Solución:**
```python
def _create_empty_invoice_data(self) -> dict:
    return {
        'CIF': '',
        'FechaFactura': '',
        # ...
    }
```

---

**3. Formateo de bordes en Excel** (múltiple)
```python
# excel_exporter.py - líneas 254-259, 264-269
cell.border = Border(
    left=Side(style='thin'),
    right=Side(style='thin'),
    top=Side(style='thin'),
    bottom=Side(style='thin')
)
```

**Solución:**
```python
def _apply_thin_border(self, cell):
    cell.border = self.THIN_BORDER  # Constante
```

---

### 3.3 Manejo de Errores

#### Fortalezas:
- ✅ Try-except en puntos críticos
- ✅ Errores registrados en metadatos (`_Error`)
- ✅ Validación de entrada de usuario

#### Debilidades:
```python
# Problema 1: Excepciones genéricas
try:
    # ... código
except Exception as e:  # ❌ Demasiado amplio
    print(f"Error: {e}")

# Problema 2: Manejo inconsistente
try:
    # ... 40+ líneas
except Exception as e:
    print(f"Error: {e}")  # ❌ No hay recovery
    datos['_Error'] = str(e)

# Problema 3: Errores silenciosos en Excel
try:
    # ... formateo
except:  # ❌ Bare except
    pass  # ❌ Error silencioso
```

**Soluciones:**
1. Excepciones específicas (`FileNotFoundError`, `ValueError`, etc.)
2. Logging estructurado en lugar de `print()`
3. Recovery strategies donde sea posible
4. No usar bare `except`

---

### 3.4 Logging Actual

**Estado:** ❌ No existe logging formal

```python
# Actual (en todo el código):
print(f"OK Plantilla cargada: {archivo}")
print(f"WARN Plantilla invalida: {archivo}")
print(f"Error cargando plantilla {archivo}: {e}")
```

**Problemas:**
- ❌ No se puede capturar o redirigir logs
- ❌ Sin timestamps
- ❌ Sin niveles (DEBUG, INFO, WARNING, ERROR)
- ❌ Mezclado con output de usuario
- ❌ Imposible debuggear en producción

**Solución:**
```python
import logging

logger = logging.getLogger(__name__)

logger.info("Plantilla cargada: %s", archivo)
logger.warning("Plantilla inválida: %s", archivo)
logger.error("Error cargando plantilla %s: %s", archivo, e)
```

---

## 4. OPORTUNIDADES DE MEJORA

### 4.1 Logging Estructurado

**Esfuerzo:** Bajo (1-2 horas)
**Impacto:** Alto
**Prioridad:** ⭐⭐⭐ CRÍTICA

**Implementación:**
```python
# src/utils/logger.py
import logging
import sys

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Configura logger estructurado."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Handler para consola
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

# Uso en cada módulo:
from utils.logger import setup_logger
logger = setup_logger(__name__)

logger.info("Procesando %d facturas", len(facturas))
logger.error("Error procesando %s: %s", archivo, e)
```

**Beneficios:**
- Debuggeo en producción
- Logs redirigibles a archivo
- Niveles configurables (DEBUG en dev, INFO en prod)
- Timestamps automáticos

---

### 4.2 Extraer Limpiadores de Datos

**Esfuerzo:** Bajo (1-2 horas)
**Impacto:** Medio
**Prioridad:** ⭐⭐⭐ ALTA

**Implementación:**
```python
# src/utils/data_cleaners.py
import re
from datetime import datetime
from typing import Optional

class DataCleaner:
    """Limpieza y normalización de datos extraídos."""

    @staticmethod
    def clean_text(text: str) -> str:
        """Limpia espacios y caracteres especiales."""
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text).strip()

    @staticmethod
    def clean_date(text: str) -> str:
        """
        Normaliza fechas a formato DD/MM/YYYY.

        Soporta:
        - DD/MM/YYYY
        - YYYY-MM-DD
        - DD-MM-YYYY
        - Texto: "15 de enero de 2024"
        """
        # ... lógica actual de limpiar_fecha()
        pass

    @staticmethod
    def clean_numeric(text: str) -> str:
        """Limpia y normaliza números."""
        # ... lógica actual de limpiar_numerico()
        pass

# Uso en pdf_extractor.py:
from utils.data_cleaners import DataCleaner

texto_limpio = DataCleaner.clean_text(texto_crudo)
fecha_limpia = DataCleaner.clean_date(fecha_cruda)
numero_limpio = DataCleaner.clean_numeric(numero_crudo)
```

**Beneficios:**
- Reutilización en otros módulos
- Testeable independientemente
- Más fácil de mantener
- Reduce complejidad de PDFExtractor

---

### 4.3 Repository Pattern

**Esfuerzo:** Medio (2-3 horas)
**Impacto:** Alto
**Prioridad:** ⭐⭐ MEDIA-ALTA

**Implementación:**
```python
# src/repositories/template_repository.py
from typing import Dict, List, Optional
import json
from pathlib import Path

class TemplateRepository:
    """Repositorio para cargar y gestionar plantillas JSON."""

    def __init__(self, templates_dir: str = "plantillas"):
        self.templates_dir = Path(templates_dir)

    def load_all(self) -> Dict[str, dict]:
        """Carga todas las plantillas del directorio."""
        templates = {}
        for file in self.templates_dir.glob("*.json"):
            template = self.load_one(file.stem)
            if template:
                templates[file.stem] = template
        return templates

    def load_one(self, name: str) -> Optional[dict]:
        """Carga una plantilla específica."""
        path = self.templates_dir / f"{name}.json"
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error("Error cargando plantilla %s: %s", name, e)
            return None

    def validate(self, template: dict) -> bool:
        """Valida estructura de plantilla."""
        # ... lógica de validar_plantilla()
        pass

    def save(self, name: str, template: dict) -> bool:
        """Guarda plantilla a disco."""
        path = self.templates_dir / f"{name}.json"
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error("Error guardando plantilla %s: %s", name, e)
            return False

# Uso en PDFExtractor:
def __init__(self, template_repo: TemplateRepository = None):
    self.template_repo = template_repo or TemplateRepository()
    self.plantillas_cargadas = self.template_repo.load_all()
```

**Beneficios:**
- Separación clara entre I/O y lógica
- Fácil mockear en tests
- Preparado para migrar a DB en el futuro
- Single Responsibility Principle

---

### 4.4 Service Layer

**Esfuerzo:** Alto (3-4 horas)
**Impacto:** Muy Alto
**Prioridad:** ⭐⭐ MEDIA-ALTA

**Implementación:**
```python
# src/services/invoice_extraction_service.py
from typing import List, Dict, Optional
from repositories.template_repository import TemplateRepository
from utils.data_cleaners import DataCleaner
from utils.logger import setup_logger

logger = setup_logger(__name__)

class InvoiceExtractionService:
    """Servicio de extracción de facturas (lógica de negocio)."""

    def __init__(self,
                 template_repo: TemplateRepository,
                 trimestre: str = "Q1",
                 anio: str = "2025"):
        self.template_repo = template_repo
        self.trimestre = trimestre
        self.anio = anio
        self.cleaner = DataCleaner()

    def process_directory(self, directory: str) -> List[Dict]:
        """
        Procesa todos los PDFs de un directorio.

        Returns:
            Lista de diccionarios con datos extraídos.
        """
        logger.info("Procesando directorio: %s", directory)

        # 1. Listar PDFs
        pdfs = self._list_pdfs(directory)
        logger.info("Encontrados %d PDFs", len(pdfs))

        # 2. Procesar cada PDF
        results = []
        for pdf_path in pdfs:
            result = self.extract_invoice(pdf_path)
            results.append(result)

        # 3. Detectar duplicados
        results = self._mark_duplicates(results)

        return results

    def extract_invoice(self, pdf_path: str) -> Dict:
        """Extrae datos de una factura."""
        # 1. Identificar proveedor
        provider_id = self._identify_provider(pdf_path)

        if not provider_id:
            return self._create_error_invoice(pdf_path, "Proveedor no identificado")

        # 2. Extraer campos
        template = self.template_repo.load_one(provider_id)
        data = self._extract_fields(pdf_path, template)

        # 3. Limpiar datos
        data = self._clean_data(data)

        return data

    def _identify_provider(self, pdf_path: str) -> Optional[str]:
        """Identifica proveedor basándose en CIF/Nombre."""
        # ... lógica actual de identificar_proveedor()
        pass

    def _extract_fields(self, pdf_path: str, template: dict) -> Dict:
        """Extrae campos según plantilla."""
        # ... lógica actual de extraer_datos_factura()
        pass

    def _clean_data(self, data: Dict) -> Dict:
        """Limpia todos los campos."""
        for field, value in data.items():
            if 'Fecha' in field:
                data[field] = self.cleaner.clean_date(value)
            elif field in ['Base', 'ComPaypal']:
                data[field] = self.cleaner.clean_numeric(value)
            else:
                data[field] = self.cleaner.clean_text(value)
        return data

# Uso en main.py:
extraction_service = InvoiceExtractionService(
    template_repo=TemplateRepository(),
    trimestre=trimestre,
    anio=anio
)

resultados = extraction_service.process_directory("facturas/")
```

**Beneficios:**
- main.py mucho más simple (de 320 a ~100 líneas)
- Lógica de negocio centralizada y testeada
- Fácil extender funcionalidades
- Dependency injection natural
- Tests más simples (mockear servicios, no clases grandes)

---

### 4.5 Refactorizar ExcelExporter

**Esfuerzo:** Medio (2-3 horas)
**Impacto:** Medio
**Prioridad:** ⭐ BAJA-MEDIA

**Implementación Strategy Pattern:**
```python
# src/exporters/base_exporter.py
from abc import ABC, abstractmethod
from typing import List, Dict

class BaseExporter(ABC):
    """Interfaz común para exportadores."""

    @abstractmethod
    def export(self, data: List[Dict], output_path: str) -> str:
        """Exporta datos a formato específico."""
        pass

# src/exporters/excel_exporter.py
from .base_exporter import BaseExporter

class ExcelExporter(BaseExporter):
    def export(self, data: List[Dict], output_path: str) -> str:
        # ... lógica Excel
        pass

# src/exporters/csv_exporter.py
class CSVExporter(BaseExporter):
    def export(self, data: List[Dict], output_path: str) -> str:
        # ... lógica CSV
        pass

# src/exporters/json_exporter.py
class JSONExporter(BaseExporter):
    def export(self, data: List[Dict], output_path: str) -> str:
        # ... lógica JSON
        pass

# src/services/export_service.py
class ExportService:
    """Servicio de exportación."""

    def __init__(self):
        self.exporters = {
            'excel': ExcelExporter(),
            'csv': CSVExporter(),
            'json': JSONExporter()
        }

    def export(self, data: List[Dict], format: str, output_dir: str) -> str:
        """Exporta a formato especificado."""
        exporter = self.exporters.get(format)
        if not exporter:
            raise ValueError(f"Formato no soportado: {format}")

        return exporter.export(data, output_dir)
```

**Beneficios:**
- Fácil añadir nuevos formatos (XML, Parquet, etc.)
- Código más limpio y modular
- Strategy pattern bien implementado
- Tests independientes por exporter

---

## 5. HOJA DE RUTA RECOMENDADA

### Fase A: Mejoras Rápidas (2-3 horas) - HACER AHORA

```
Semana 1 (2-3 días)
├── Issue #8: Logging estructurado (1h)
│   ├── Crear src/utils/logger.py
│   ├── Reemplazar print() en todos los módulos
│   └── Tests: verificar que sigue funcionando
│
├── Issue #9: Extraer data cleaners (1h)
│   ├── Crear src/utils/data_cleaners.py
│   ├── Mover funciones de limpieza
│   ├── Refactorizar PDFExtractor para usar utils
│   └── Tests: añadir tests unitarios para cleaners
│
└── Issue #10: Eliminar duplicaciones (1h)
    ├── Consolidar inicialización datos_error
    ├── Consolidar filtrado de columnas
    └── Tests: verificar coverage >= 79%
```

**ROI:** 🟢 Muy Alto - Bajo esfuerzo, alto beneficio inmediato

---

### Fase B: Repository + Service (4-6 horas) - HACER PRÓXIMAMENTE

```
Semana 2-3 (4-5 días)
├── Issue #11: TemplateRepository (2h)
│   ├── Crear src/repositories/template_repository.py
│   ├── Mover lógica carga plantillas desde PDFExtractor
│   ├── Tests: añadir tests para repository
│   └── Refactorizar PDFExtractor para usar repo
│
├── Issue #12: InvoiceExtractionService (3h)
│   ├── Crear src/services/invoice_extraction_service.py
│   ├── Mover lógica extracción desde PDFExtractor
│   ├── Tests: añadir tests para service
│   └── Verificar coverage >= 79%
│
└── Issue #13: Refactorizar main.py (1h)
    ├── Usar InvoiceExtractionService
    ├── Simplificar lógica CLI
    └── Tests: actualizar mocks si es necesario
```

**ROI:** 🟢 Alto - Arquitectura profesional, mantenibilidad

---

### Fase C: Mejoras Opcionales (4-6 horas) - CONSIDERAR DESPUÉS

```
Semana 4+ (opcional)
├── Issue #14: Dataclasses (2h)
│   ├── Crear src/models/invoice.py
│   ├── Crear src/models/template.py
│   └── Refactorizar para usar modelos
│
└── Issue #15: Strategy en Exporters (3h)
    ├── Crear src/exporters/base_exporter.py
    ├── Separar ExcelExporter, CSVExporter, JSONExporter
    ├── Crear ExportService
    └── Tests: verificar todos los formatos
```

**ROI:** 🟡 Medio - Extensibilidad, no urgente

---

## 6. MATRIZ DE DECISIÓN

### Cuadrante de Esfuerzo vs Impacto

```
                IMPACTO
                  ↑
        ALTO      │   1. Logging ✅     │  4. Repository ✅
                  │   2. DataCleaner ✅ │  5. Service Layer ✅
                  │                    │
       ──────────────────────────────────────→ ESFUERZO
                  │                    │
        MEDIO     │   3. Elim. Dups ✅  │  6. Dataclasses
                  │                    │
        BAJO      │   (ya todo cubierto)│  7. DI Container
                  │                    │
              BAJO                    ALTO
```

### Recomendación de Orden:

1. **Logging** (AHORA) - 1 hora
2. **DataCleaner** (AHORA) - 1 hora
3. **Eliminar duplicaciones** (AHORA) - 1 hora
4. **Repository** (PRONTO) - 2 horas
5. **Service Layer** (PRONTO) - 3 horas
6. **Dataclasses** (DESPUÉS) - 2 horas
7. **Strategy Exporters** (DESPUÉS) - 3 horas

**Total Fase A+B:** 8 horas (inversión recomendada)
**Total Fase A+B+C:** 13 horas (si tiempo permite)

---

## 7. CRITERIOS DE ÉXITO

### Métricas Objetivo Post-Refactorización:

| Métrica | Actual | Objetivo | Status |
|---------|--------|----------|--------|
| **Coverage Total** | 79% | >= 79% (preferible 80%+) | 🎯 |
| **Tests Passing** | 154/156 | >= 154/156 | ✅ |
| **Logging Coverage** | 0% (print) | 100% (logger) | 📊 |
| **Duplicación** | Media | Baja | 📉 |
| **Complejidad main.py** | Alta | Baja | 🎯 |
| **Separación de Concerns** | Media | Alta | 🎯 |

### Indicadores de Calidad:

- ✅ Todos los tests pasando
- ✅ Sin regresiones en funcionalidad
- ✅ Logging en todos los módulos
- ✅ Responsabilidades claramente separadas
- ✅ Código más legible y mantenible
- ✅ Fácil añadir nuevas funcionalidades
- ✅ Tests más simples (menos mocks)

---

## 8. RIESGOS Y MITIGACIÓN

### Riesgo 1: Romper tests existentes

**Probabilidad:** Media
**Impacto:** Alto

**Mitigación:**
- Ejecutar tests después de CADA cambio
- Commits pequeños y atómicos
- Revertir inmediatamente si tests fallan
- TDD estricto: tests primero, código después

---

### Riesgo 2: Bajada de coverage

**Probabilidad:** Baja
**Impacto:** Medio

**Mitigación:**
- Monitorear coverage en cada commit
- Añadir tests para nuevo código inmediatamente
- Target: >= 79% en todo momento

---

### Riesgo 3: Over-engineering

**Probabilidad:** Media
**Impacto:** Medio

**Mitigación:**
- Seguir principio YAGNI (You Aren't Gonna Need It)
- Solo implementar Fase A + Fase B inicialmente
- Validar Fase C antes de implementar
- Mantener pragmatismo sobre purismo

---

### Riesgo 4: Tiempo de implementación mayor al estimado

**Probabilidad:** Media
**Impacto:** Bajo

**Mitigación:**
- Fase A es independiente (2-3h garantizadas)
- Fase B puede pausarse si es necesario
- Fase C es completamente opcional
- Beneficio incremental en cada fase

---

## 9. PREGUNTAS FRECUENTES

### ¿Por qué no Clean Architecture completa?

**Respuesta:** Over-engineering. El proyecto es funcional y relativamente pequeño (4 módulos, 1079 statements). Clean Architecture completa añadiría complejidad innecesaria. La propuesta incremental da 80% del beneficio con 30% del esfuerzo.

---

### ¿Por qué no usar un framework de DI (Dependency Injection)?

**Respuesta:** Dependency injection manual es suficiente. Frameworks como `dependency-injector` añaden learning curve y dependencias externas. Para este proyecto, inyección manual en constructores es más que suficiente.

---

### ¿Cuándo implementar Fase C?

**Respuesta:** Fase C es opcional. Implementar solo si:
1. Fase A + B están completas y estables
2. Hay necesidad real de añadir muchos formatos de exportación
3. El proyecto sigue creciendo en complejidad

---

### ¿Qué pasa si coverage baja durante refactor?

**Respuesta:**
1. **Stop immediato** - No continuar
2. Añadir tests para código nuevo
3. Si persiste < 79%, revertir cambio
4. Coverage debe mantenerse >= 79%

---

### ¿Cómo testear servicios y repositorios?

**Respuesta:**
```python
# Ejemplo: test repository
def test_template_repository_loads_all(tmp_path):
    # Arrange
    template_dir = tmp_path / "plantillas"
    template_dir.mkdir()
    (template_dir / "test.json").write_text('{"nombre": "test"}')

    repo = TemplateRepository(template_dir)

    # Act
    templates = repo.load_all()

    # Assert
    assert len(templates) == 1
    assert 'test' in templates

# Ejemplo: test service con mock
def test_extraction_service_process_directory(mocker):
    # Arrange
    mock_repo = mocker.Mock()
    service = InvoiceExtractionService(template_repo=mock_repo)

    # Act
    results = service.process_directory("test/")

    # Assert
    assert len(results) > 0
```

---

## 10. CONCLUSIÓN

### Veredicto Final: **REFACTORIZAR INCREMENTALMENTE ✅**

**Razones:**
1. **ROI excelente**: 8-10 horas → beneficio a largo plazo
2. **Riesgo controlado**: Cambios incrementales y testeados
3. **Pragmatismo**: No over-engineering, solo lo necesario
4. **Valor inmediato**: Cada fase aporta beneficio tangible
5. **Alineado con TDD**: Metodología ya establecida

### Próximos Pasos:

1. ✅ **Completado**: Análisis arquitectónico
2. ✅ **Completado**: Crear ADR-001
3. 🔄 **En progreso**: Crear Issue #7 en GitHub
4. ⏳ **Pendiente**: Obtener aprobación para Fase A
5. ⏳ **Pendiente**: Implementar Fase A (logging, cleaners, dups)

---

**Fecha de análisis:** 2025-10-25
**Próxima revisión:** Después de Fase A (estimado: 3 días)
**Contacto:** Ver Issue #7 en GitHub

---

## APÉNDICE A: Gráfico de Dependencias Actual

```
┌──────────────────────────────────────────────────┐
│                  main.py                          │
│           (FacturaExtractorApp)                   │
│  - CLI parsing                                    │
│  - Validación de inputs                           │
│  - Orquestación del flujo                         │
│  - Mostrar estadísticas                           │
└───────────┬──────────────────┬────────────────────┘
            │                  │
            │                  │
    ┌───────▼─────────┐  ┌────▼───────────────┐
    │ PDFExtractor    │  │  ExcelExporter     │
    ├─────────────────┤  ├────────────────────┤
    │ - Cargar JSON   │  │ - Excel básico     │
    │ - Validar       │  │ - Excel completo   │
    │ - Identificar   │  │ - Excel formateado │
    │ - Extraer       │  │ - CSV              │
    │ - Limpiar       │  │ - JSON             │
    │ - Duplicados    │  │ - Filtrar cols     │
    │ - Stats         │  │ - Stats            │
    └───────┬─────────┘  └────┬───────────────┘
            │                  │
            │                  │
    ┌───────▼──────────────────▼───────┐
    │      Librerías Externas          │
    │  - pdfplumber (PDF parsing)      │
    │  - pandas (data manipulation)    │
    │  - openpyxl (Excel writing)      │
    │  - PIL (imagen en GUI)           │
    │  - tkinter (GUI plantillas)      │
    └──────────────────────────────────┘
```

## APÉNDICE B: Gráfico de Dependencias Objetivo (Post-Refactor)

```
┌──────────────────────────────────────────────────┐
│                  main.py                          │
│           (FacturaExtractorApp)                   │
│  - CLI parsing                                    │
│  - Orquestación simple                            │
└───────────┬──────────────────┬────────────────────┘
            │                  │
            │                  │
    ┌───────▼─────────────┐  ┌─▼──────────────────┐
    │ InvoiceExtraction   │  │  ExportService     │
    │ Service             │  │                    │
    │ (Lógica de negocio) │  │ (Exportación)      │
    └────┬────────────────┘  └─┬──────────────────┘
         │                      │
         │  ┌───────────────────┴──────┬──────────┐
         │  │                          │          │
    ┌────▼──▼────────┐   ┌─────────────▼──┐  ┌───▼─────┐
    │ Template       │   │ Excel          │  │ CSV     │
    │ Repository     │   │ Exporter       │  │ Exporter│
    │ (I/O)          │   └────────────────┘  └─────────┘
    └────────────────┘
         │
    ┌────▼────────────────────┐
    │ utils/                  │
    │  - logger.py            │
    │  - data_cleaners.py     │
    │  - validators.py        │
    └─────────────────────────┘
```

**Mejoras visibles:**
- ✅ main.py mucho más simple
- ✅ Servicios con responsabilidades claras
- ✅ Repository para I/O separado
- ✅ Utils reutilizables
- ✅ Exporters modulares (Strategy)

---

**FIN DEL ANÁLISIS**
