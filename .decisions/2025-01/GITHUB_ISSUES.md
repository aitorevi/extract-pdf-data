# 🎫 GitHub Issues - Plantillas

Copia y pega estas issues directamente en GitHub.

---

## FASE 1: Testing y Calidad 🧪

### Issue #1: Configurar framework de testing (pytest)
```markdown
## Descripción
Configurar pytest y estructura básica de testing para el proyecto.

## Tareas
- [ ] Instalar pytest y dependencias de testing
- [ ] Crear carpeta `tests/` con estructura
- [ ] Configurar `pytest.ini` o `pyproject.toml`
- [ ] Crear fixtures básicas
- [ ] Documentar cómo ejecutar tests en README

## Archivos a crear
- `tests/__init__.py`
- `tests/conftest.py`
- `tests/test_pdf_extractor.py`
- `tests/test_excel_exporter.py`
- `pytest.ini`

## Labels
`priority:high`, `type:testing`, `phase:1-testing`
```

### Issue #2: Tests unitarios para pdf_extractor.py
```markdown
## Descripción
Crear tests unitarios completos para `src/pdf_extractor.py`

## Funciones a testear
- [ ] `cargar_plantillas()`
- [ ] `identificar_proveedor()`
- [ ] `extraer_datos_factura()`
- [ ] `procesar_directorio_facturas()`
- [ ] `validar_plantilla()`
- [ ] Manejo de errores

## Cobertura objetivo
- Mínimo 80% coverage

## Labels
`priority:high`, `type:testing`, `phase:1-testing`
```

### Issue #3: Tests unitarios para excel_exporter.py
```markdown
## Descripción
Crear tests unitarios completos para `src/excel_exporter.py`

## Funciones a testear
- [ ] `exportar_a_excel()`
- [ ] `exportar_a_csv()`
- [ ] `exportar_a_json()`
- [ ] Formateo de celdas
- [ ] Manejo de datos vacíos/inválidos

## Cobertura objetivo
- Mínimo 80% coverage

## Labels
`priority:high`, `type:testing`, `phase:1-testing`
```

### Issue #4: Tests de integración para flujo completo
```markdown
## Descripción
Tests end-to-end del flujo completo de extracción y exportación.

## Escenarios a testear
- [ ] Procesar factura válida → Excel correcto
- [ ] Procesar múltiples facturas → Consolidado correcto
- [ ] Factura sin plantilla → Error manejado
- [ ] Plantilla inválida → Error manejado
- [ ] Carpeta vacía → Comportamiento correcto

## Labels
`priority:high`, `type:testing`, `phase:1-testing`
```

### Issue #5: Tests para edge cases en plantillas
```markdown
## Descripción
Tests específicos para casos límite y peculiaridades de plantillas.

## Casos a testear
- [ ] Campos vacíos/opcionales
- [ ] Coordenadas fuera de rango
- [ ] Múltiples proveedores con mismo formato
- [ ] Campos con caracteres especiales
- [ ] Números con diferentes formatos (1.000,00 vs 1,000.00)

## Labels
`priority:medium`, `type:testing`, `phase:1-testing`
```

### Issue #6: Configurar CI/CD básico (GitHub Actions)
```markdown
## Descripción
Configurar GitHub Actions para ejecutar tests automáticamente.

## Tareas
- [ ] Crear `.github/workflows/tests.yml`
- [ ] Configurar ejecución de tests en push/PR
- [ ] Agregar badge de status en README
- [ ] Configurar coverage reporting

## Labels
`priority:medium`, `type:feature`, `phase:1-testing`
```

---

## FASE 2: Arquitectura y Code Quality 🏗️

### Issue #7: 🤔 DEBATE: Evaluar arquitectura actual vs necesidades
```markdown
## Descripción
Debate sobre si la arquitectura actual es suficiente o necesita mejoras.

## Preguntas a responder
1. ¿La arquitectura actual es mantenible a largo plazo?
2. ¿Necesitamos separación en capas (Repository, Service)?
3. ¿Vale la pena implementar dependency injection?
4. ¿El acoplamiento actual es problemático?
5. ¿Cómo escalaría si añadimos más features?

## Opciones
- **A:** Mantener arquitectura simple actual
- **B:** Implementar capas (Repository, Service, Controller)
- **C:** Enfoque híbrido (mejorar sin complicar)

## Documentar en
`.decisions/2025-01/ADR-001-arquitectura.md`

## Labels
`priority:high`, `type:debate`, `phase:2-architecture`
```

### Issue #8: Refactorizar código según conclusiones
```markdown
## Descripción
Implementar mejoras de arquitectura según decisión del Issue #7.

## Bloqueado por
- #7

## Labels
`priority:medium`, `type:refactor`, `phase:2-architecture`, `status:blocked`
```

### Issue #9: Documentar patrones de diseño utilizados
```markdown
## Descripción
Documentar los patrones de diseño que usamos en el proyecto.

## Tareas
- [ ] Documentar patrón Factory (si aplica)
- [ ] Documentar patrón Strategy (formatos export)
- [ ] Documentar dependency management
- [ ] Crear diagrama de arquitectura

## Labels
`priority:low`, `type:documentation`, `phase:2-architecture`
```

### Issue #10: Implementar logging estructurado
```markdown
## Descripción
Añadir logging profesional en todo el sistema.

## Tareas
- [ ] Configurar `logging` module
- [ ] Añadir logs en puntos clave
- [ ] Diferentes niveles (DEBUG, INFO, WARNING, ERROR)
- [ ] Logs a archivo rotativo
- [ ] Documentar en README

## Labels
`priority:medium`, `type:feature`, `phase:2-architecture`
```

### Issue #11: Manejo de errores robusto
```markdown
## Descripción
Mejorar el manejo de errores y excepciones.

## Tareas
- [ ] Crear excepciones custom
- [ ] Try-except en lugares críticos
- [ ] Mensajes de error informativos
- [ ] Recovery strategies
- [ ] Documentar errores comunes

## Labels
`priority:high`, `type:feature`, `phase:2-architecture`
```

---

## FASE 3: Corner Cases y Plantillas 🔧

### Issue #12: 🤔 DEBATE: Identificar corner cases conocidos
```markdown
## Descripción
Sesión de brainstorming para identificar todos los casos especiales.

## Corner cases conocidos
- Facturas multi-página
- Campos opcionales
- Layouts variables
- Múltiples monedas
- Descuentos dinámicos
- Tablas con filas variables

## Documentar en
`.decisions/2025-01/CORNER_CASES.md`

## Labels
`priority:high`, `type:debate`, `phase:3-corner-cases`
```

### Issue #13: Manejo de facturas con múltiples páginas
```markdown
## Descripción
Soporte para facturas que ocupan varias páginas.

## Casos de uso
- Factura en páginas 1-3
- Datos en diferentes páginas
- Tablas que continúan en siguiente página

## Labels
`priority:medium`, `type:feature`, `phase:3-corner-cases`
```

### Issue #14: Manejo de campos opcionales/condicionales
```markdown
## Descripción
Campos que pueden existir o no según el tipo de factura.

## Ejemplos
- Descuentos (opcional)
- Recargos (opcional)
- Retenciones (condicional)
- Notas (opcional)

## Labels
`priority:high`, `type:feature`, `phase:3-corner-cases`
```

### Issue #15: Plantillas con layouts variables
```markdown
## Descripción
Manejar proveedores que cambian el layout de sus facturas.

## Estrategias
- Múltiples plantillas por proveedor
- Coordenadas con tolerancia
- Detección automática de layout

## Labels
`priority:medium`, `type:feature`, `phase:3-corner-cases`
```

### Issue #16: Validación de datos extraídos
```markdown
## Descripción
Validar que los datos extraídos sean coherentes.

## Validaciones
- [ ] Fechas válidas
- [ ] Números positivos donde aplique
- [ ] Total = Base + IVA
- [ ] Formatos de NIF/CIF
- [ ] Rangos razonables

## Labels
`priority:high`, `type:feature`, `phase:3-corner-cases`
```

### Issue #17: Mejora en detección de proveedor
```markdown
## Descripción
Hacer más robusta la identificación de proveedor.

## Mejoras
- [ ] Fuzzy matching para nombres
- [ ] Múltiples identificadores (NIF, nombre, logo)
- [ ] Fallback strategies
- [ ] Logging cuando no se identifica

## Labels
`priority:medium`, `type:feature`, `phase:3-corner-cases`
```

---

## FASE 4: Organización de Archivos 📂

### Issue #18: 🤔 DEBATE: Estructura de carpetas (facturas/resultados)
```markdown
## Descripción
Decidir estructura de organización por año/trimestre.

## Propuesta
```
facturas/
├── 2024/
│   ├── Q1/ Q2/ Q3/ Q4/
└── 2025/
    └── Q1/
```

## Alternativas
- Por mes en lugar de trimestre
- Año/Mes/Día
- Solo año

## Documentar en
`.decisions/2025-01/ADR-002-organizacion-archivos.md`

## Labels
`priority:medium`, `type:debate`, `phase:4-organization`
```

### Issue #19: Organizar facturas por año/trimestre
```markdown
## Descripción
Implementar organización automática de facturas.

## Tareas
- [ ] Detectar fecha de factura
- [ ] Crear carpetas automáticamente
- [ ] Mover/copiar a carpeta correcta
- [ ] Configuración opcional (activar/desactivar)

## Bloqueado por
- #18

## Labels
`priority:medium`, `type:feature`, `phase:4-organization`, `status:blocked`
```

### Issue #20: Organizar resultados por año/trimestre
```markdown
## Descripción
Guardar resultados en carpetas organizadas.

## Tareas
- [ ] Crear carpetas por año/trimestre
- [ ] Nombrar archivos con fecha
- [ ] Configuración de ruta de salida

## Bloqueado por
- #18

## Labels
`priority:medium`, `type:feature`, `phase:4-organization`, `status:blocked`
```

### Issue #21: Script de migración de archivos existentes
```markdown
## Descripción
Migrar facturas y resultados existentes a nueva estructura.

## Tareas
- [ ] Crear script de migración
- [ ] Backup automático antes de migrar
- [ ] Dry-run mode
- [ ] Documentar proceso

## Labels
`priority:low`, `type:feature`, `phase:4-organization`
```

### Issue #22: Actualizar paths en código
```markdown
## Descripción
Actualizar código para usar nueva estructura de carpetas.

## Archivos a modificar
- `src/pdf_extractor.py`
- `src/excel_exporter.py`
- `src/main.py`
- Scripts de acceso rápido

## Labels
`priority:medium`, `type:refactor`, `phase:4-organization`
```

---

## FASE 5: Exportación y Campos 📊

### Issue #23: 🤔 DEBATE: Definir campos obligatorios vs opcionales
```markdown
## Descripción
Definir qué campos son obligatorios y cuáles opcionales.

## Campos a discutir
- Proveedor (obligatorio?)
- Número factura (obligatorio?)
- Fecha (obligatorio?)
- Base imponible (obligatorio?)
- IVA (obligatorio?)
- Total (obligatorio?)
- Retención (opcional?)
- Descuentos (opcional?)

## Documentar en
`.decisions/2025-01/ADR-003-campos-exportacion.md`

## Labels
`priority:high`, `type:debate`, `phase:5-export`
```

### Issue #24: 🤔 DEBATE: Nombres estándar de columnas
```markdown
## Descripción
Definir nomenclatura estándar para columnas.

## Opciones
- **Español:** "Número Factura", "Fecha", "Base Imponible"
- **Inglés:** "Invoice Number", "Date", "Taxable Base"
- **Códigos:** "num_factura", "fecha", "base_imponible"

## Documentar en
`.decisions/2025-01/ADR-003-campos-exportacion.md`

## Labels
`priority:medium`, `type:debate`, `phase:5-export`
```

### Issue #25: 🤔 DEBATE: Orden de columnas en Excel/CSV
```markdown
## Descripción
Definir orden lógico de columnas en exportaciones.

## Propuesta
1. Proveedor
2. NIF/CIF
3. Número Factura
4. Fecha
5. Base Imponible
6. IVA
7. Total
8. ...

## Documentar en
`.decisions/2025-01/ADR-003-campos-exportacion.md`

## Labels
`priority:low`, `type:debate`, `phase:5-export`
```

### Issue #26: Implementar esquema de validación de campos
```markdown
## Descripción
Crear esquema para validar campos extraídos.

## Opciones
- Pydantic models
- JSON Schema
- Custom validators

## Bloqueado por
- #23

## Labels
`priority:medium`, `type:feature`, `phase:5-export`, `status:blocked`
```

### Issue #27: Mejorar formato de Excel (estilos, anchos)
```markdown
## Descripción
Excel con mejor formato profesional.

## Mejoras
- [ ] Anchos de columna automáticos
- [ ] Formato de números (moneda)
- [ ] Formato de fechas
- [ ] Headers con estilo
- [ ] Totales al final
- [ ] Filtros automáticos

## Labels
`priority:low`, `type:feature`, `phase:5-export`
```

### Issue #28: Agregar metadatos a exportaciones
```markdown
## Descripción
Incluir metadatos útiles en archivos exportados.

## Metadatos
- Fecha de generación
- Versión del software
- Número de facturas procesadas
- Rango de fechas
- Filtros aplicados

## Labels
`priority:low`, `type:feature`, `phase:5-export`
```

---

## FASE 6: Mejoras de Distribución 🚀

### Issue #29: 🤔 DEBATE: Aplicación de escritorio vs Docker vs Web
```markdown
## Descripción
Decidir cómo distribuir y ejecutar la aplicación.

## Opciones
1. **Aplicación de Escritorio**
   - Electron (web tech)
   - PyQt/PySide (nativo)
   - Tkinter (simple)

2. **Docker**
   - Fácil deployment
   - Consistent environment
   - Portable

3. **Web App**
   - Flask/FastAPI backend
   - React/Vue frontend
   - Acceso remoto

4. **CLI Mejorada**
   - Mantener actual
   - Mejorar UX
   - Añadir features

## Documentar en
`.decisions/2025-01/ADR-004-distribucion.md`

## Labels
`priority:low`, `type:debate`, `phase:6-distribution`
```

### Issue #30: 🤔 DEBATE: Electron vs PyQt vs Tkinter (si escritorio)
```markdown
## Descripción
Si se decide por desktop app, elegir framework.

## Comparación
- **Electron:** Web tech, grande, cross-platform
- **PyQt:** Nativo, profesional, licencia
- **Tkinter:** Simple, incluido, básico

## Bloqueado por
- #29

## Labels
`priority:low`, `type:debate`, `phase:6-distribution`, `status:blocked`
```

### Issue #31: 🤔 DEBATE: Docker compose para deployment
```markdown
## Descripción
Si se usa Docker, definir arquitectura.

## Servicios
- App principal
- Base de datos (si necesaria)
- Almacenamiento de archivos
- Backup automático

## Bloqueado por
- #29

## Labels
`priority:low`, `type:debate`, `phase:6-distribution`, `status:blocked`
```

### Issue #32: Evaluar necesidad de base de datos
```markdown
## Descripción
¿Necesitamos DB o los archivos son suficientes?

## Pros DB
- Búsquedas rápidas
- Histórico
- Reportes complejos

## Cons DB
- Más complejidad
- Backup adicional
- Overhead

## Labels
`priority:low`, `type:debate`, `phase:6-distribution`
```

### Issue #33: Implementar según decisión tomada
```markdown
## Descripción
Implementar la solución de distribución elegida.

## Bloqueado por
- #29, #30, #31, #32

## Labels
`priority:low`, `type:feature`, `phase:6-distribution`, `status:blocked`
```

---

## FASE 7: UI/UX 🎨

### Issue #34: Mejorar UI del editor de plantillas
```markdown
## Descripción
Hacer el editor más intuitivo y visual.

## Mejoras
- [ ] Preview de PDF en alta resolución
- [ ] Zoom in/out
- [ ] Undo/Redo
- [ ] Guías y reglas
- [ ] Snap to grid
- [ ] Colores por tipo de campo

## Labels
`priority:low`, `type:feature`, `phase:7-ui`
```

### Issue #35: Agregar preview en tiempo real
```markdown
## Descripción
Ver el dato extraído mientras defines las coordenadas.

## Features
- Preview del texto capturado
- Validación en tiempo real
- Highlight de campos

## Labels
`priority:low`, `type:feature`, `phase:7-ui`
```

### Issue #36: Mejorar mensajes de error/éxito
```markdown
## Descripción
Mensajes más claros y accionables.

## Ejemplos
- ❌ "Error" → ✅ "No se encontró plantilla para 'Proveedor X'. ¿Desea crear una?"
- ❌ "OK" → ✅ "✓ 15 facturas procesadas exitosamente"

## Labels
`priority:low`, `type:feature`, `phase:7-ui`
```

### Issue #37: Agregar progress bars
```markdown
## Descripción
Indicadores de progreso para operaciones largas.

## Lugares
- Procesamiento masivo de facturas
- Exportación de datos
- Carga de plantillas

## Labels
`priority:low`, `type:feature`, `phase:7-ui`
```

### Issue #38: Mejorar experiencia de usuario general
```markdown
## Descripción
Pulir detalles de UX en toda la aplicación.

## Áreas
- Confirmaciones antes de acciones destructivas
- Shortcuts de teclado
- Tooltips informativos
- Ayuda contextual
- Tutorial integrado

## Labels
`priority:low`, `type:feature`, `phase:7-ui`
```

---

**Total: 38 Issues**
**Debates: 8**
**Features: 20**
**Testing: 6**
**Refactor: 2**
**Documentation: 2**
