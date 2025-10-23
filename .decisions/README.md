# 📁 Decisiones del Proyecto

Esta carpeta contiene todas las decisiones importantes tomadas durante el desarrollo del proyecto.

---

## 📋 Estructura

```
.decisions/
├── README.md                    # Este archivo
├── ADR_TEMPLATE.md             # Plantilla para ADRs
│
└── 2025-01/                    # Decisiones de Enero 2025
    ├── PLAN_DE_ACCION.md       # Plan maestro del proyecto
    ├── ROADMAP.md              # Timeline y milestones
    ├── GITHUB_ISSUES.md        # Plantillas de issues
    │
    ├── ADR-001-arquitectura.md         # (Pendiente - Debate #7)
    ├── ADR-002-organizacion-archivos.md # (Pendiente - Debate #18)
    ├── ADR-003-campos-exportacion.md    # (Pendiente - Debates #23-25)
    └── ADR-004-distribucion.md          # (Pendiente - Debate #29)
```

---

## 🎯 ¿Qué son los ADRs?

**ADR = Architecture Decision Record**

Son documentos que registran:
- **Qué** decisión se tomó
- **Por qué** se tomó (contexto, opciones, justificación)
- **Cuándo** se tomó
- **Consecuencias** de la decisión

---

## ✍️ Cómo Crear un ADR

1. Copia `ADR_TEMPLATE.md`
2. Nómbralo `ADR-XXX-titulo-descriptivo.md`
3. Llena todas las secciones
4. Discute con el equipo
5. Marca como "Aceptada" o "Rechazada"
6. Referencia el ADR en issues relacionados

---

## 📚 Documentos Principales

### Plan de Acción
- **Archivo:** `2025-01/PLAN_DE_ACCION.md`
- **Propósito:** Plan maestro del proyecto
- **Contiene:** Todas las fases, issues, y organización

### Roadmap
- **Archivo:** `2025-01/ROADMAP.md`
- **Propósito:** Timeline visual del proyecto
- **Contiene:** Fechas estimadas, milestones, métricas

### GitHub Issues
- **Archivo:** `2025-01/GITHUB_ISSUES.md`
- **Propósito:** Plantillas de todas las issues
- **Contiene:** 38 issues listas para copiar a GitHub

---

## 🔍 ADRs Pendientes

### ADR-001: Arquitectura
- **Issue:** #7
- **Pregunta:** ¿Mantenemos arquitectura simple o implementamos capas?
- **Status:** 🟡 Pendiente debate

### ADR-002: Organización de Archivos
- **Issue:** #18
- **Pregunta:** ¿Cómo organizamos facturas/resultados por fecha?
- **Status:** 🟡 Pendiente debate

### ADR-003: Campos de Exportación
- **Issues:** #23, #24, #25
- **Pregunta:** ¿Qué campos, nombres y orden usar?
- **Status:** 🟡 Pendiente debate (próxima semana)

### ADR-004: Distribución
- **Issue:** #29
- **Pregunta:** ¿Desktop, Docker, Web, o CLI?
- **Status:** 🔵 Futuro (final del proyecto)

---

## 🗂️ Organización por Mes

Cada mes tiene su carpeta con:
- Decisiones tomadas ese mes
- Updates del plan de acción
- Cambios en el roadmap

Ejemplo:
```
2025-01/  # Enero
2025-02/  # Febrero
2025-03/  # Marzo
...
```

---

## 🔗 Referencias

- [Plan de Acción](.decisions/2025-01/PLAN_DE_ACCION.md)
- [Roadmap](.decisions/2025-01/ROADMAP.md)
- [GitHub Issues](.decisions/2025-01/GITHUB_ISSUES.md)
- [ADR Template](ADR_TEMPLATE.md)

---

## 💡 Tips

1. **Lee los ADRs** antes de hacer cambios grandes
2. **Actualiza** cuando cambien decisiones
3. **Referencia** ADRs en commits y PRs
4. **Debate** antes de tomar decisiones importantes
5. **Documenta** el "por qué", no solo el "qué"

---

**Este es un documento vivo que crece con el proyecto.**
