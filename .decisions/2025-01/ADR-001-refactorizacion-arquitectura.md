# ADR-001: Refactorización Arquitectónica - Fase 2

**Fecha:** 2025-10-25
**Estado:** Propuesta
**Decisores:** Equipo del proyecto + Claude Code
**Relacionado con:** Issue #7

---

## Contexto y Problema

El proyecto extract-pdf-data ha alcanzado **79% de coverage** con **154 tests pasando**. La Fase 1 (Testing y Calidad) está completada exitosamente.

Sin embargo, al analizar la arquitectura actual, identificamos oportunidades de mejora:

### Problemas Identificados:
1. **Logging inexistente**: Todo usa `print()`, sin estructura ni niveles
2. **Lógica de negocio dispersa**: main.py tiene validación + orquestación + UI
3. **Duplicación de código**: Limpieza de datos, filtrado de columnas, inicialización de errores
4. **Acoplamiento interno**: PDFExtractor mezcla I/O + extracción + limpieza + estadísticas
5. **Testabilidad**: Tests requieren muchos mocks debido a responsabilidades mezcladas

### Estado Actual:
- ✅ Código funcional (79% coverage)
- ✅ Separación básica de módulos
- ✅ Tests bien estructurados
- ❌ Sin logging estructurado
- ❌ Responsabilidades no claramente separadas
- ❌ Difícil de extender con nuevas funcionalidades

---

## Factores de Decisión

1. **Impacto vs Esfuerzo**: Priorizar cambios de alto impacto y bajo/medio esfuerzo
2. **Riesgo**: Minimizar riesgo de introducir bugs (tests deben seguir pasando)
3. **Mantenibilidad**: Facilitar futuras extensiones y mantenimiento
4. **Pragmatismo**: No sobre-ingenierizar - el proyecto es funcional
5. **ROI**: Balance entre inversión de tiempo y beneficio obtenido

---

## Opciones Consideradas

### Opción 1: Mantener Arquitectura Actual (Status Quo)

**Descripción:**
No hacer cambios arquitectónicos. Solo añadir features según se necesiten.

**Pros:**
- ✅ Cero riesgo de romper funcionalidad existente
- ✅ No requiere inversión de tiempo
- ✅ Código ya funciona bien (79% coverage)

**Cons:**
- ❌ Problemas de mantenibilidad crecerán con el tiempo
- ❌ Sin logging, debugging en producción es difícil
- ❌ Duplicación de código seguirá aumentando
- ❌ Difícil añadir nuevas funcionalidades complejas
- ❌ Tests seguirán requiriendo mocks complejos

**Veredicto:** ❌ NO recomendado. El proyecto crecerá y los problemas se amplificarán.

---

### Opción 2: Refactorización Completa (Clean Architecture)

**Descripción:**
Implementar Clean Architecture completa con capas estrictas:
- Presentation Layer (UI)
- Application Layer (Use Cases)
- Domain Layer (Business Logic + Entities)
- Infrastructure Layer (Repositories, External Services)

**Pros:**
- ✅ Arquitectura profesional y escalable
- ✅ Separación de concerns perfecta
- ✅ Máxima testabilidad
- ✅ Preparado para cualquier extensión futura

**Cons:**
- ❌ Esfuerzo muy alto (2-3 semanas)
- ❌ Alto riesgo de introducir bugs durante refactor
- ❌ Over-engineering para un proyecto de este tamaño
- ❌ Learning curve para colaboradores
- ❌ Complejidad innecesaria

**Veredicto:** ❌ NO recomendado. Demasiado para las necesidades actuales.

---

### Opción 3: Refactorización Pragmática Incremental (RECOMENDADA)

**Descripción:**
Implementar mejoras arquitectónicas en 3 fases incrementales, priorizando impacto:

**FASE A (Corto Plazo - 2-3 horas):**
1. Agregar logging estructurado (reemplazar `print()`)
2. Extraer limpiadores de datos a módulo separado
3. Eliminar duplicaciones menores

**FASE B (Mediano Plazo - 4-6 horas):**
4. Crear Repository básico para plantillas
5. Crear Service Layer para lógica de extracción
6. Refactorizar main.py para usar servicios

**FASE C (Largo Plazo - opcional):**
7. Agregar dataclasses para modelos
8. Aplicar Strategy pattern en exportadores
9. Dependency injection simple

**Pros:**
- ✅ Bajo riesgo (cambios incrementales y testeados)
- ✅ Esfuerzo razonable (10-12 horas total)
- ✅ ROI alto - cada fase aporta valor inmediato
- ✅ Permite validar cada mejora antes de continuar
- ✅ Tests siguen pasando en cada etapa
- ✅ Balance perfecto entre mejora y pragmatismo

**Cons:**
- ❌ No es "arquitectura perfecta" (pero no la necesitamos)
- ❌ Requiere 3 iteraciones (pero permite validación)

**Veredicto:** ✅ RECOMENDADO. Máximo valor con mínimo riesgo.

---

## Decisión

**Opción elegida:** **Opción 3 - Refactorización Pragmática Incremental**

**Justificación:**

1. **Balance óptimo**: Mejora significativa sin over-engineering
2. **Riesgo controlado**: Cambios incrementales permiten validar en cada paso
3. **ROI excelente**: 10-12 horas de inversión para beneficios a largo plazo
4. **Pragmatismo**: Resuelve problemas reales sin complejidad innecesaria
5. **Alineado con TDD**: Cada cambio seguirá metodología de tests primero

### Priorización de Cambios:

```
┌─────────────────────────────────────────────────┐
│  ESFUERZO BAJO          ESFUERZO ALTO          │
├─────────────────────────────────────────────────┤
│  VALOR ALTO:                                   │
│  1. Logging ✅          4. Repository ✅        │
│  2. DataCleaner ✅      5. Service Layer ✅     │
├─────────────────────────────────────────────────┤
│  VALOR MEDIO:                                  │
│  3. Eliminar dups ✅    6. Dataclasses         │
├─────────────────────────────────────────────────┤
│  VALOR BAJO:                                   │
│                         7. DI Container         │
└─────────────────────────────────────────────────┘
```

---

## Consecuencias

### Positivas

1. **Debugging mejorado**: Logging estructurado permite rastrear problemas en producción
2. **Código más limpio**: Responsabilidades claramente separadas
3. **Testabilidad**: Menos mocks, tests más simples
4. **Extensibilidad**: Fácil añadir nuevos proveedores, formatos de exportación, etc.
5. **Mantenibilidad**: Futuras modificaciones serán más sencillas
6. **Documentación**: Arquitectura más clara y autoexplicativa
7. **Confidence**: Coverage se mantendrá alto (objetivo: 80%+)

### Negativas (y Mitigación)

1. **Inversión de tiempo (10-12 horas)**
   - Mitigación: Hacerlo en 3 fases, validando cada una
   - Beneficio a largo plazo compensa la inversión

2. **Riesgo de romper tests existentes**
   - Mitigación: Ejecutar tests después de cada cambio
   - Usar TDD: escribir tests para nuevo código primero
   - Coverage debe mantenerse >= 79%

3. **Curva de aprendizaje para colaboradores**
   - Mitigación: Documentar patrones en ADR y código
   - Nomenclatura clara y estándares definidos

4. **Posible bajada temporal de coverage**
   - Mitigación: Añadir tests para nuevo código inmediatamente
   - Target: mantener 79%+ en todo momento

---

## Implementación

### FASE A: Mejoras Rápidas (2-3 horas)

**Issues relacionados:**
- #8: Implementar logging estructurado
- #9: Extraer limpiadores de datos
- #10: Eliminar duplicaciones menores

**Tareas:**
- [x] Análisis arquitectónico completado
- [ ] Crear `src/utils/logger.py` con logging configurado
- [ ] Reemplazar `print()` con `logger.info/warning/error()`
- [ ] Crear `src/utils/data_cleaners.py`
- [ ] Mover funciones de limpieza desde pdf_extractor.py
- [ ] Consolidar duplicaciones (datos_error, filtrado)
- [ ] Tests: verificar que todo sigue funcionando

**Timeline:** 1-2 días

---

### FASE B: Repository + Service Layer (4-6 horas)

**Issues relacionados:**
- #11: Crear TemplateRepository
- #12: Crear InvoiceExtractionService
- #13: Refactorizar main.py para usar servicios

**Tareas:**
- [ ] Crear `src/repositories/template_repository.py`
- [ ] Mover lógica de carga de plantillas
- [ ] Crear `src/services/invoice_extraction_service.py`
- [ ] Mover lógica de extracción desde PDFExtractor
- [ ] Refactorizar main.py para usar servicios
- [ ] Refactorizar tests para usar nuevas abstracciones
- [ ] Verificar coverage >= 79%

**Timeline:** 2-3 días

---

### FASE C: Mejoras Opcionales (4-6 horas)

**Issues relacionados:**
- #14: Agregar dataclasses para modelos
- #15: Refactorizar ExcelExporter con Strategy pattern

**Tareas:**
- [ ] Crear `src/models/invoice.py` con dataclass
- [ ] Crear `src/models/template.py` con dataclass
- [ ] Refactorizar ExcelExporter con Strategy
- [ ] Tests para nuevos modelos
- [ ] Documentar patrones

**Timeline:** 2-3 días (opcional)

---

## Notas

### Principios de Implementación:

1. **TDD Estricto**: Tests primero, código después
2. **Commits pequeños**: Un cambio lógico por commit
3. **Tests siempre en verde**: No avanzar si algo falla
4. **Coverage monitorizado**: Mantener >= 79%
5. **Documentación inline**: Docstrings claros
6. **PRs pequeños**: Un issue/feature por PR

### Criterios de Éxito:

- ✅ Todos los tests pasando (154+)
- ✅ Coverage >= 79% (preferiblemente 80%+)
- ✅ Logging implementado en todos los módulos
- ✅ Responsabilidades claramente separadas
- ✅ Código más mantenible y extensible
- ✅ Sin regresiones en funcionalidad

---

## Referencias

- [Clean Architecture - Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)
- [Service Layer Pattern](https://martinfowler.com/eaaCatalog/serviceLayer.html)
- [Python Logging Best Practices](https://docs.python.org/3/howto/logging.html)
- Análisis arquitectónico completo: `.decisions/2025-01/arquitectura-analisis-detallado.md`

---

**Próximo paso:** Crear Issue #7 en GitHub para iniciar debate y obtener aprobación.
