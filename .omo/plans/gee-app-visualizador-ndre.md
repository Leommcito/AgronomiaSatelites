# GEE App: Visualizador NDRE Sin Filtrar (2025-2026)

## TL;DR

> **Quick Summary**: Crear una GEE App publicable con mapa interactivo que muestra imágenes NDRE crudas (sin filtro de nubes) de Sentinel-2 para las 4 parcelas de mandarina Murcott, navegables por fecha con slider. La app reusa `parcelas` y `paletaVigor` de `codigo_gee.js` pero NO aplica enmascaramiento de nubes — se muestra todo tal cual lo capturó el satélite.
> 
> **Deliverables**:
> - `app_visualizador_ndre.js` — script independiente de GEE App
> 
> **Estimated Effort**: Short (1 archivo, ~80 líneas)
> **Parallel Execution**: NO — un solo archivo, tarea secuencial simple
> **Critical Path**: T1 → T2 (construcción → publicación)

---

## Context

### Original Request
El usuario necesita una App de GEE para que la agrónoma pueda visualizar imágenes NDRE de las 4 parcelas desde 2025 hasta 2026, **sin quitar imágenes nubladas** — mostrar todo "tal y como es". La interfaz debe ser fluida e intuitiva (slider de fechas, mapa interactivo).

### Interview Summary
**Key Discussions**:
- **Sin filtro de nubes**: A diferencia de `codigo_gee.js` que aplica CS+ ≥ 0.9 + SCL (4,5), esta app usa imágenes Sentinel-2 L2A CRUDAS sin máscara. Los píxeles nublados aparecen con sus valores reales (aunque NDRE en nubes no tiene sentido agronómico, la agrónoma quiere verlo).
- **Reutilización**: Las geometrías de parcelas (`parcelas`) y la paleta de colores (`paletaVigor`) se importan del asset existente, igual que en `codigo_gee.js`.
- **Archivo separado**: La app va en un archivo nuevo, sin modificar `codigo_gee.js`.
- **Interfaz**: Mapa grande + slider de fechas + play/pause. Click en parcela opcional para ver info.

**Research Findings**:
- `codigo_gee.js` línea 18: `parcelas = ee.FeatureCollection('projects/proyectoleomespinosa/assets/ParcelasDefinidas')` — asset reutilizable.
- `codigo_gee.js` línea 262: `paletaVigor = ['#d73027', '#fc8d59', '#fee08b', '#d9ef8b', '#91cf60', '#1a9850']` — paleta reutilizable.
- `codigo_gee.js` línea 306: visualización NDRE con `{min: 0.1, max: 0.6, palette: paletaVigor}` — parámetros a reutilizar.
- GEE Apps se publican desde el Code Editor (botón "Apps") y generan un link público. No requiere instalación del usuario final.
- Para NDRE sin filtrar, las bandas B5 y B8 de L2A deben dividirse por 10000 (escalado de reflectancia de superficie).

---

## Work Objectives

### Core Objective
Crear un script de GEE App autocontenido que cargue imágenes Sentinel-2 crudas, calcule NDRE sin enmascarar nubes, y las muestre en un mapa interactivo con slider temporal para navegación intuitiva por fecha.

### Concrete Deliverables
- `app_visualizador_ndre.js` — script completo listo para copiar al GEE Code Editor y publicar

### Definition of Done
- [ ] El script carga en GEE Code Editor sin errores
- [ ] El mapa muestra NDRE con la paleta `paletaVigor` y las 4 parcelas superpuestas
- [ ] El slider permite navegar entre fechas de imágenes
- [ ] El botón Play/Pause anima la secuencia temporal
- [ ] La fecha actual se muestra visiblemente en la UI
- [ ] La app se puede publicar desde el botón "Apps" del Code Editor

### Must Have
- Imágenes sin filtro de nubes (raw Sentinel-2 L2A)
- NDRE calculado con bandas B5 y B8 escaladas (/10000)
- Mapa interactivo (zoom, pan)
- Slider de navegación por fechas
- Parcelas superpuestas como capa vectorial
- Fecha visible en la interfaz
- Botón Play/Pause para animación automática

### Must NOT Have (Guardrails)
- **NO** enmascarar nubes (ni CS+, ni SCL, ni filtro alguno)
- **NO** modificar `codigo_gee.js`
- **NO** exportar CSVs ni GeoTIFFs (solo visualización interactiva)
- **NO** interpolación ni S-G (datos crudos)
- **NO** UI excesivamente compleja (sin gráficos de serie temporal, sin tooltips avanzados — mantener simpleza)
- **NO** depender de scripts externos (archivo autocontenido)

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** — el ejecutor verifica en GEE Code Editor y con Playwright.

### Test Decision
- **Infrastructure exists**: NO (GEE Code Editor es entorno visual, no hay test framework)
- **Automated tests**: NO (GEE no soporta unit testing de UI)
- **Agent-Executed QA**: SÍ — el ejecutor abrirá el Code Editor, pegará el script, ejecutará, verificará visualmente, y publicará.

### QA Policy
Verificación manual por el ejecutor en GEE Code Editor:
- **Carga**: Script sin errores de sintaxis
- **Mapa**: NDRE visible con paleta correcta, parcelas superpuestas
- **Slider**: Navegación fluida entre fechas
- **Play**: Animación automática funciona
- **Publicación**: App publicable desde el menú "Apps"

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately - app completa):
├── Task 1: Crear app_visualizador_ndre.js [visual-engineering]
└── Task 2: Verificar en GEE Code Editor y publicar [visual-engineering]

Critical Path: Task 1 → Task 2
```

### Agent Dispatch Summary

- **Wave 1**: **2** — T1 → `visual-engineering`, T2 → `visual-engineering`

---

## TODOs

- [ ] 1. Crear `app_visualizador_ndre.js` con mapa interactivo NDRE

  **What to do**:
  - Crear archivo nuevo `app_visualizador_ndre.js` en la raíz del proyecto
  - Cargar el asset de parcelas: `ee.FeatureCollection('projects/proyectoleomespinosa/assets/ParcelasDefinidas')`
  - Cargar colección Sentinel-2 L2A cruda (`COPERNICUS/S2_SR_HARMONIZED`) filtrada por parcelas y por fechas `2025-01-01` a `2026-06-01`
  - Calcular NDRE: `(B8 - B5) / (B8 + B5)` con bandas escaladas `/ 10000`
  - **NO aplicar ninguna máscara de nubes** (ni CS+, ni SCL)
  - Construir UI con `ui.Map` (mapa principal), `ui.Panel` (panel de control abajo), `ui.Slider` (selector de fecha), `ui.Button` (play/pause)
  - El slider debe mapear índice → imagen de la colección → mostrar en mapa
  - Al mover el slider, actualizar la capa NDRE en el mapa
  - Botón Play: avanza automáticamente el slider con `setInterval`
  - Mostrar la fecha actual como texto en el panel
  - Capa de parcelas siempre visible como overlay vectorial (borde rojo)
  - Paleta de colores: `['#d73027', '#fc8d59', '#fee08b', '#d9ef8b', '#91cf60', '#1a9850']`
  - Rango de visualización NDRE: `{min: 0.1, max: 0.6}`
  - Incluir instrucciones en comentarios sobre cómo publicar la app

  **Must NOT do**:
  - NO enmascarar píxeles nublados
  - NO importar ni modificar `codigo_gee.js`
  - NO exportar datos (CSV, GeoTIFF, video)
  - NO agregar gráficos de serie temporal (UI simple, solo mapa + slider)
  - NO usar `ui.Chart` ni `reduceRegions`

  **Recommended Agent Profile**:
  > La app es puramente frontend UI de GEE con JavaScript Earth Engine API.
  - **Category**: `visual-engineering`
    - Reason: Construcción de UI interactiva, mapa, slider, animación — dominio visual/frontend
  - **Skills**: [`playwright`]
    - `playwright`: Para verificar la app publicada abriendo el link y confirmando que el mapa, slider y play funcionan
  - **Skills Evaluated but Omitted**:
    - `frontend-ui-ux`: No aplica (la UI es GEE nativa, no HTML/CSS/React)

  **Parallelization**:
  - **Can Run In Parallel**: NO (tarea única)
  - **Parallel Group**: Wave 1 (única tarea)
  - **Blocks**: Nada (es la base)
  - **Blocked By**: Ninguna (autocontenida)

  **References**:

  **Pattern References** (código existente a seguir):
  - `codigo_gee.js:18` — `parcelas = ee.FeatureCollection('projects/proyectoleomespinosa/assets/ParcelasDefinidas')` — Reutilizar mismo asset ID
  - `codigo_gee.js:262` — `paletaVigor = ['#d73027', '#fc8d59', '#fee08b', '#d9ef8b', '#91cf60', '#1a9850']` — Reutilizar misma paleta
  - `codigo_gee.js:14-15` — `startDate = '2025-01-01'; endDate = '2026-06-01'` — Mismo rango de fechas
  - `codigo_gee.js:306` — `{min: 0.1, max: 0.6, palette: paletaVigor}` — Mismos parámetros de visualización

  **External References** (API de GEE UI):
  - GEE UI Map docs: `https://developers.google.com/earth-engine/guides/ui_widgets#ui.map` — Referencia de `ui.Map`, `ui.Map.Layer`, `ui.Map.addLayer`
  - GEE UI Slider docs: `https://developers.google.com/earth-engine/guides/ui_widgets#ui.slider` — Referencia de `ui.Slider` con eventos `onChange`
  - GEE Apps publishing: `https://developers.google.com/earth-engine/guides/apps` — Cómo publicar la app desde el Code Editor

  **WHY Each Reference Matters**:
  - `codigo_gee.js` line 18: Asset ID exacto que funciona en el proyecto GEE del usuario — no hay que adivinar el path
  - `codigo_gee.js` line 262: Paleta validada visualmente por el usuario para NDRE
  - `ui.Slider` docs: La API de slider en GEE requiere entender el patrón `onChange(callback)` y cómo indexar en una `ee.List` de fechas
  - GEE Apps guide: Publicar requiere pasos específicos (botón "Apps" → "New App" → seleccionar script)

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Happy path — Carga y visualización de NDRE
    Tool: GEE Code Editor (manual) + Playwright para verificación de app publicada
    Preconditions:
      - Script copiado al GEE Code Editor
      - Proyecto GEE con acceso al asset de parcelas
    Steps:
      1. Abrir GEE Code Editor y pegar el script completo
      2. Hacer clic en "Run" — verificar que no hay errores en la consola
      3. Confirmar que el mapa carga centrado en las parcelas
      4. Confirmar que la capa NDRE es visible con la paleta de colores (verde = alto NDRE, rojo = bajo)
      5. Mover el slider a una posición intermedia — verificar que la capa NDRE cambia
      6. Verificar que la fecha en el panel se actualiza al mover el slider
      7. Hacer clic en el botón Play — verificar que el slider avanza automáticamente
      8. Confirmar que las parcelas se ven como polígonos rojos superpuestos
    Expected Result:
      - Mapa muestra NDRE con paletaVigor sin errores de consola
      - Slider cambia entre imágenes y la fecha se actualiza
      - Play/Pause funciona correctamente
      - Parcelas visibles como overlay
    Failure Indicators:
      - Error en consola: "asset not found" → asset ID incorrecto
      - Error en consola: "NDVI is not defined" → banda mal referenciada
      - Slider no cambia imagen → callback onChange mal conectado
      - Mapa en blanco → rango de fechas sin imágenes o filtro mal aplicado
      - Botón Play no responde → setInterval no configurado
    Evidence: .omo/evidence/task-1-ndre-app-loaded.png (screenshot del Code Editor con mapa visible)

  Scenario: Edge case — Imágenes nubladas se muestran sin filtrar
    Tool: GEE Code Editor (manual)
    Preconditions: Script ejecutándose
    Steps:
      1. Navegar con el slider a una fecha donde se sabe que hay nubes (época de lluvias en Jujuy: enero-febrero)
      2. Observar la capa NDRE en el mapa
      3. Verificar que los píxeles nublados NO están enmascarados — aparecen con algún valor de NDRE (aunque no tenga sentido agronómico)
      4. Confirmar que NO se aplicó CS+ ni SCL — si alguna máscara estuviera presente, los píxeles nublados aparecerían como transparentes/negros
    Expected Result:
      - Píxeles nublados visibles (no enmascarados), con valores NDRE derivados de reflectancia de nubes
      - Sin huecos transparentes donde debería haber nubes
    Failure Indicators:
      - Grandes áreas negras/transparentes donde debería haber nubes → se aplicó máscara de nubes por error
      - Error en consola sobre CS+ o SCL → se importó código de filtrado por error
    Evidence: .omo/evidence/task-1-cloudy-visible.png (screenshot mostrando nubes visibles)
  ```

  **Commit**: YES
  - Message: `feat(app): visualizador NDRE sin filtrar con slider de fechas`
  - Files: `app_visualizador_ndre.js`
  - Pre-commit: N/A (archivo nuevo, no hay tests automatizados)

---

## Final Verification Wave (MANDATORY — after ALL implementation tasks)

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Leer el plan end-to-end. Verificar que el archivo `app_visualizador_ndre.js` existe en la raíz del proyecto, que NO modifica `codigo_gee.js`, que NO aplica máscaras de nubes (buscar CS+, SCL, updateMask en el nuevo archivo), y que reutiliza los mismos asset ID y paleta de `codigo_gee.js`.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Revisar sintaxis JavaScript/GEE del script: ¿las bandas B5/B8 están escaladas (/10000)? ¿el slider usa onChange correctamente? ¿el setInterval tiene clearInterval para evitar memory leaks? ¿la UI es autocontenida (sin require() externos salvo los de GEE)? ¿comentarios claros para la agrónoma? Verificar que no hay `ui.Chart`, `reduceRegions`, `Export`, ni `updateMask`.
  Output: `Build [PASS/FAIL] | Lint N/A (GEE) | GEE Syntax [PASS/FAIL] | VERDICT`

- [ ] F3. **Real Manual QA** — `unspecified-high` (+ `playwright` skill)
  Abrir GEE Code Editor, copiar el script, ejecutar. Verificar cada escenario QA definido arriba. Publicar la app y verificar que el link público funciona. Tomar screenshots de cada paso.
  Output: `Scenarios [N/N pass] | Publicación [SUCCESS/FAIL] | VERDICT`

- [ ] F4. **Scope Fidelity Check** — `deep`
  Verificar que el script nuevo NO contiene: enmascaramiento de nubes, modificación de codigo_gee.js, exportación de datos, interpolación, S-G. Verificar que SÍ contiene: carga de parcelas, cálculo de NDRE, mapa, slider, play/pause, fecha visible, paletaVigor.
  Output: `Tasks [1/1 compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

- **Commit único**: `feat(app): visualizador NDRE sin filtrar con slider de fechas`
  - Archivo: `app_visualizador_ndre.js` (nuevo)
  - Mensaje describe el propósito y la característica principal (slider de fechas)

---

## Success Criteria

### Verification Commands
```bash
# Verificar que el archivo existe y tiene contenido
python -c "content = open('app_visualizador_ndre.js', encoding='utf-8').read(); print(f'Lines: {content.count(chr(10))}')"

# Verificar que NO contiene máscaras de nubes
python -c "content = open('app_visualizador_ndre.js', encoding='utf-8').read(); assert 'updateMask' not in content, 'updateMask found!'; assert 'CS+' not in content.upper(), 'CS+ found!'; assert 'SCL' not in content, 'SCL found!'; print('Clean: no cloud masks')"

# Verificar que NO modifica codigo_gee.js (git diff)
git diff --name-only HEAD
```

### Final Checklist
- [ ] `app_visualizador_ndre.js` existe en la raíz
- [ ] Script autocontenido (sin require externos)
- [ ] Carga `parcelas` del mismo asset que `codigo_gee.js`
- [ ] Usa misma `paletaVigor` que `codigo_gee.js`
- [ ] SIN máscaras de nubes (CS+, SCL, updateMask)
- [ ] Slider navega entre fechas
- [ ] Play/Pause anima automáticamente
- [ ] Fecha visible en la UI
- [ ] App publicable desde Code Editor
- [ ] `codigo_gee.js` sin modificaciones
