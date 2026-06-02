# Plan: Agregar NDRE, MSAVI2, S2REP y NDVI al CSV

## TL;DR

> **Quick Summary**: Agregar 4 columnas adicionales (NDRE, MSAVI2, S2REP, NDVI) al CSV de exportación para que el agrónomo/investigador tenga acceso a los índices espectrales crudos sin reprocesar imágenes satelitales.
>
> **Deliverables**:
> - Constitución actualizada (v1.1.0 — MINOR bump)
> - Contrato CSV actualizado (v1.1.0 — 7→11 columnas)
> - `codigo_gee.js` modificado (select(), constant image, feature props, CSV selectors)
>
> **Estimated Effort**: Quick (1 sesión, ~5 cambios)
> **Parallel Execution**: NO — todos los cambios son en el mismo archivo
> **Critical Path**: Constitución → Contrato → Código

---

## Context

### Solicitud Original
Agregar al CSV las bandas espectrales que se calculan en el código pero no se exportan: NDRE (índice de visualización y validación cruzada), MSAVI2 (base del Kc), S2REP (variable independiente de LAI y Cab), y NDVI (índice tradicional para referencia comparativa).

### Por qué son útiles
- **NDRE**: Permite al agrónomo cotejar visualmente los mapas con los valores numéricos
- **MSAVI2**: Permite validar la función de transferencia Kc y recalibrar sin reprocesar
- **S2REP**: Permite recalcular LAI y Cab con coeficientes calibrados futuros
- **NDVI**: Referencia comparativa contra la literatura tradicional (aunque no se use para estimación biofísica)

---

## Work Objectives

### Core Objective
Agregar 4 columnas (NDRE, MSAVI2, S2REP, NDVI) al CSV exportado, manteniendo las 7 columnas existentes en sus posiciones originales para backward compatibility.

### Concrete Deliverables
- Constitución `.specify/memory/constitution.md` → v1.1.0
- Contrato `specs/001-gee-murcott-monitor/contracts/csv-schema.md` → v1.1.0
- Código `codigo_gee.js` → 4 nuevas columnas en CSV export

### Must Have
- Columnas nuevas al FINAL del CSV (posiciones 8-11) para no romper consumidores existentes
- NDRE, MSAVI2, S2REP, NDVI con sus valores correctos
- Documentación actualizada en constitución y contrato

### Must NOT Have
- No cambiar el orden de las 7 columnas existentes
- No eliminar ni renombrar columnas existentes
- No modificar la lógica de cálculo de los índices
- No romper el timelapse ni los GeoTIFF (usan NDRE de la colección)

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: NO (GEE no tiene tests unitarios)
- **Automated tests**: None (validación manual en GEE Console)
- **Agent-Executed QA**: Verificación visual del CSV descargado

### QA Policy
Ejecutar el script en GEE Code Editor, descargar el CSV resultante, verificar que tiene 11 columnas con nombres correctos y valores plausibles.

---

## Execution Strategy

### Sequential (single file, sin paralelismo)

```
Paso 1: Actualizar constitución (.specify/memory/constitution.md)
Paso 2: Actualizar contrato CSV (contracts/csv-schema.md)
Paso 3: Modificar codigo_gee.js (5 cambios en un archivo)
Paso 4: Commit + verificar CSV en GEE
```

---

## TODOs

- [ ] 1. Actualizar Constitución — Principio VIII (v1.0.0 → v1.1.0)

  **What to do**:
  - Agregar 4 columnas opcionales al final de la tabla de columnas en la constitución
  - Actualizar la versión a 1.1.0 y Last Amended a 2026-06-02
  - Justificar como MINOR bump (nuevas columnas opcionales, sin romper existentes)
  
  **Must NOT do**:
  - No eliminar ni modificar las 7 columnas existentes
  
  **References**:
  - `.specify/memory/constitution.md` — Sección VIII y tabla de columnas

  **Acceptance Criteria**:
  - Tabla de columnas muestra 11 columnas (7 obligatorias + 4 opcionales)
  - Version = 1.1.0

- [ ] 2. Actualizar Contrato CSV (v1.0.0 → v1.1.0)

  **What to do**:
  - Agregar 4 nuevas filas a la tabla de especificación de columnas
  - Actualizar versión a 1.1.0
  - Documentar que las columnas 8-11 son opcionales para consumidores
  
  **Must NOT do**:
  - No cambiar el orden de las primeras 7 columnas
  - No cambiar tipos ni nombres de columnas existentes
  
  **References**:
  - `specs/001-gee-murcott-monitor/contracts/csv-schema.md`

  **Acceptance Criteria**:
  - Tabla muestra 11 columnas en orden correcto
  - Columnas 8-11 marcadas como opcionales
  - Version = 1.1.0

- [ ] 3. Agregar S2REP y MSAVI2 al select() de coleccionProcesada

  **What to do**:
  - Línea 93 de codigo_gee.js: cambiar `.select(['NDVI_Mask', 'NDRE', 'LAI_RedEdge', 'Cab_RedEdge', 'Kc_Actual'])` 
  - a `.select(['NDVI_Mask', 'NDRE', 'S2REP', 'LAI_RedEdge', 'Cab_RedEdge', 'MSAVI2', 'Kc_Actual'])`
  - Agrega `'S2REP'` y `'MSAVI2'` (NDVI_Mask y NDRE ya están)
  
  **Must NOT do**:
  - No cambiar el orden de las bandas existentes
  
  **References**:
  - `codigo_gee.js:L93` — select() de coleccionProcesada
  - `codigo_gee.js:L48-89` — calcularMetricas() produce estas bandas

  **Acceptance Criteria**:
  - coleccionProcesada tiene 7 bandas (5 originales + S2REP + MSAVI2)
  - NDVI_Mask y NDRE preservados en posiciones originales

- [ ] 4. Actualizar imagen constante de semanas sin datos (7 bandas)

  **What to do**:
  - Línea 120: cambiar `ee.Image.constant([0, 0, 0, 0, 0])` (5 ceros)
  - a `ee.Image.constant([0, 0, 0, 0, 0, 0, 0])` (7 ceros)
  - Cambiar rename a `['NDVI_Mask', 'NDRE', 'S2REP', 'LAI_RedEdge', 'Cab_RedEdge', 'MSAVI2', 'Kc_Actual']`
  
  **Must NOT do**:
  - No cambiar la lógica de máscara (updateMask(0) se mantiene)
  
  **References**:
  - `codigo_gee.js:L120` — imagen constante para semanas sin datos

  **Acceptance Criteria**:
  - 7 ceros en el array, 7 nombres en rename()
  - Sin errores de "number of names must match number of bands"

- [ ] 5. Agregar 4 nuevas propiedades al Feature en reduceRegions

  **What to do**:
  - En el `estadisticas.map(function(f))` (líneas 184-219), agregar al `ee.Feature(null, {...})`:
    ```javascript
    'NDRE': f.get('NDRE'),
    'MSAVI2': f.get('MSAVI2'),
    'S2REP': f.get('S2REP'),
    'NDVI': f.get('NDVI_Mask'),
    ```
  - Insertarlas antes de cerrar el objeto `}`
  
  **Must NOT do**:
  - No duplicar propiedades existentes
  - No romper el cálculo de estrés (variables existentes no se modifican)
  
  **References**:
  - `codigo_gee.js:L184-219` — Feature construction

  **Acceptance Criteria**:
  - 4 nuevas propiedades disponibles en cada Feature
  - Propiedades existentes (Fecha_Semanal, ID_Parcela, etc.) intactas

- [ ] 6. Agregar 4 nuevos selectores al CSV export

  **What to do**:
  - Línea 230-231: cambiar el array `selectors` de 7 a 11 elementos
  - Agregar al final: `'NDRE', 'MSAVI2', 'S2REP', 'NDVI'`
  - Array final: `['Fecha_Semanal', 'ID_Parcela', 'LAI_RedEdge', 'Cab_RedEdge', 'Kc_Actual', 'Flag_Interpolacion', 'Alerta_Estres', 'NDRE', 'MSAVI2', 'S2REP', 'NDVI']`
  
  **Must NOT do**:
  - No cambiar el orden de los primeros 7 selectores
  - No escribir mal los nombres de las columnas nuevas
  
  **References**:
  - `codigo_gee.js:L230-231` — selectors del Export.table.toDrive()

  **Acceptance Criteria**:
  - CSV exportado tiene 11 columnas
  - Columnas 1-7 en orden original
  - Columnas 8-11: NDRE, MSAVI2, S2REP, NDVI

---

## Final Verification

- [ ] F1. Ejecutar script en GEE Code Editor, verificar que Console muestra validación sin errores
- [ ] F2. Ejecutar export Tasks, descargar CSV de Google Drive
- [ ] F3. Abrir CSV: verificar 11 columnas, nombres correctos, valores en rangos esperados
- [ ] F4. Commit + push

---

## Commit Strategy

- **1-2**: `docs(constitution): bump to v1.1.0 — add 4 optional CSV columns (NDRE, MSAVI2, S2REP, NDVI)` — constitution.md, csv-schema.md
- **3-6**: `feat(csv): add NDRE, MSAVI2, S2REP, NDVI columns to export` — codigo_gee.js

---

## Success Criteria

### Verification Commands
```javascript
// En GEE Console, después de ejecutar:
print('CSV columns:', serieLimpia.first().propertyNames());
// Expected: 11 property names incluyendo NDRE, MSAVI2, S2REP, NDVI
```

### Final Checklist
- [ ] 11 columnas en CSV descargado
- [ ] NDRE valores ∈ [0.1, 0.6]
- [ ] MSAVI2 valores ∈ [0.2, 0.8]
- [ ] S2REP valores ∈ [705, 740]
- [ ] NDVI valores ∈ [-1, 1]
- [ ] Las 7 columnas originales mantienen sus valores
- [ ] Constitución v1.1.0
- [ ] Contrato CSV v1.1.0
