# 📋 Plan de Acción - Extractor de Facturas PDF

**Fecha:** Enero 2025
**Estado:** En Planificación

---

## 🎯 Objetivos del Proyecto

Desarrollar un sistema robusto, mantenible y profesional para extraer datos de facturas PDF y exportarlos a múltiples formatos.

---

## 📅 Fases del Proyecto

### **FASE 1: Testing y Calidad** 🧪
**Prioridad:** Alta
**Timeline:** Inmediato

Implementar tests para asegurar la estabilidad del sistema antes de continuar con nuevas features.

**Issues a crear:**
- [ ] #1: Configurar framework de testing (pytest)
- [ ] #2: Tests unitarios para pdf_extractor.py
- [ ] #3: Tests unitarios para excel_exporter.py
- [ ] #4: Tests de integración para flujo completo
- [ ] #5: Tests para edge cases en plantillas
- [ ] #6: Configurar CI/CD básico (GitHub Actions)

---

### **FASE 2: Arquitectura y Code Quality** 🏗️
**Prioridad:** Media-Alta
**Timeline:** Después de FASE 1

Evaluar y mejorar la arquitectura según sea necesario.

**Issues a crear:**
- [ ] #7: **DEBATE:** Evaluar arquitectura actual vs necesidades
- [ ] #8: Refactorizar código según conclusiones
- [ ] #9: Documentar patrones de diseño utilizados
- [ ] #10: Implementar logging estructurado
- [ ] #11: Manejo de errores robusto

**Preguntas a responder:**
- ¿Vale la pena implementar patrones como Repository, Service Layer?
- ¿El código actual es suficientemente mantenible?
- ¿Necesitamos separación de capas más estricta?

---

### **FASE 3: Corner Cases y Plantillas** 🔧
**Prioridad:** Alta
**Timeline:** Paralelo a FASE 2

Pulir casos especiales y peculiaridades de diferentes plantillas.

**Issues a crear:**
- [ ] #12: **DEBATE:** Identificar corner cases conocidos
- [ ] #13: Manejo de facturas con múltiples páginas
- [ ] #14: Manejo de campos opcionales/condicionales
- [ ] #15: Plantillas con layouts variables
- [ ] #16: Validación de datos extraídos
- [ ] #17: Mejora en detección de proveedor

**Corner cases a considerar:**
- Facturas con tablas dinámicas
- Campos que pueden estar en diferentes posiciones
- Múltiples monedas
- Descuentos y recargos variables

---

### **FASE 4: Organización de Archivos** 📂
**Prioridad:** Media
**Timeline:** Después de FASE 3

Implementar organización por años y trimestres.

**Issues a crear:**
- [ ] #18: **DEBATE:** Estructura de carpetas (facturas/resultados)
- [ ] #19: Organizar facturas por año/trimestre
- [ ] #20: Organizar resultados por año/trimestre
- [ ] #21: Script de migración de archivos existentes
- [ ] #22: Actualizar paths en código

**Estructura propuesta a debatir:**
```
facturas/
├── 2024/
│   ├── Q1/
│   ├── Q2/
│   ├── Q3/
│   └── Q4/
└── 2025/
    └── Q1/

resultados/
├── 2024/
│   ├── Q1/
│   ├── Q2/
│   ├── Q3/
│   └── Q4/
└── 2025/
    └── Q1/
```

---

### **FASE 5: Exportación y Campos** 📊
**Prioridad:** Media-Alta
**Timeline:** Próxima semana (debate)

Definir campos exactos, nombres y orden de exportación.

**Issues a crear:**
- [ ] #23: **DEBATE:** Definir campos obligatorios vs opcionales
- [ ] #24: **DEBATE:** Nombres estándar de columnas
- [ ] #25: **DEBATE:** Orden de columnas en Excel/CSV
- [ ] #26: Implementar esquema de validación de campos
- [ ] #27: Mejorar formato de Excel (estilos, anchos)
- [ ] #28: Agregar metadatos a exportaciones

**Temas a discutir:**
- ¿Qué campos son obligatorios?
- ¿Nomenclatura en español o inglés?
- ¿Cómo manejar campos personalizados por proveedor?

---

### **FASE 6: Mejoras de Distribución** 🚀
**Prioridad:** Baja
**Timeline:** Después de todas las fases anteriores

**Issues a crear:**
- [ ] #29: **DEBATE:** Aplicación de escritorio vs Docker vs Web
- [ ] #30: **DEBATE:** Electron vs PyQt vs Tkinter (si escritorio)
- [ ] #31: **DEBATE:** Docker compose para deployment
- [ ] #32: Evaluar necesidad de base de datos
- [ ] #33: Implementar según decisión tomada

**Opciones a considerar:**
1. **Aplicación de Escritorio** (Electron, PyQt, Tkinter)
2. **Dockerización** (fácil deployment)
3. **Web App** (Flask/FastAPI + React)
4. **Mantener CLI** con mejoras

---

### **FASE 7: UI/UX** 🎨
**Prioridad:** Baja
**Timeline:** Final del proyecto

**Issues a crear:**
- [ ] #34: Mejorar UI del editor de plantillas
- [ ] #35: Agregar preview en tiempo real
- [ ] #36: Mejorar mensajes de error/éxito
- [ ] #37: Agregar progress bars
- [ ] #38: Mejorar experiencia de usuario general

---

## 🏷️ Labels Sugeridas para GitHub

```
Priority:
- priority:critical
- priority:high
- priority:medium
- priority:low

Type:
- type:bug
- type:feature
- type:refactor
- type:documentation
- type:testing
- type:debate

Status:
- status:planning
- status:in-progress
- status:review
- status:blocked
- status:done

Phase:
- phase:1-testing
- phase:2-architecture
- phase:3-corner-cases
- phase:4-organization
- phase:5-export
- phase:6-distribution
- phase:7-ui
```

---

## 📊 GitHub Project Board - Columnas

```
📋 Backlog
🤔 Debate Needed
📝 To Do
🏗️ In Progress
👀 Review
✅ Done
🚫 Blocked
```

---

## 🎯 Próximos Pasos Inmediatos

1. **Crear GitHub Issues** usando este documento como base
2. **Configurar GitHub Project** con las columnas propuestas
3. **Empezar FASE 1** (Testing) inmediatamente
4. **Programar debates** para issues marcados como DEBATE

---

## 📝 Notas

- Las decisiones importantes se documentarán en `.decisions/2025-01/`
- Cada debate generará un documento de decisión (ADR - Architecture Decision Record)
- El roadmap se actualizará semanalmente
- Prioridades pueden cambiar según necesidades del negocio

---

**Última actualización:** 23 Enero 2025
