# Tasks: Monitoreo Satelital de Mandarina Murcott (GEE)

**Input**: Design documents from `specs/001-gee-murcott-monitor/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Not requested in spec. Validation via GEE Console `print()` statements per module.

**Organization**: Tasks grouped by user story for independent implementation. Single file: `codigo_gee.js`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different sections, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US6)
- All file paths reference sections within `codigo_gee.js` (single GEE script)

---

## Phase 1: Setup (Script Initialization)

**Purpose**: Script bootstrap — configurable parameters, asset import, date range definition.

- [x] T001 Create script header with metadata comment block, configurable parameter constants (startDate, endDate, LAI_factor, Cab_factor, kc_slope, kc_intercept, sg_window, sg_degree) at top of `codigo_gee.js`
- [x] T002 Import parcel FeatureCollection from asset `projects/proyectoleomespinosa/assets/ParcelasDefinidas` and center map view in `codigo_gee.js`

---

## Phase 2: Foundational (Shared Infrastructure)

**Purpose**: Core functions used by ALL user stories. MUST complete before any user story.

- [x] T003 Link Sentinel-2 L2A collection (`COPERNICUS/S2_SR_HARMONIZED`) with Cloud Score+ (`GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED`) via `linkCollection` in `codigo_gee.js`
- [x] T004 Implement `enmascararNubesDobleFiltro()` function: CS+ mask (`cs_cdf >= 0.90`) AND SCL mask (classes 4,5 only) via `updateMask()` in `codigo_gee.js`

**Checkpoint**: Foundation ready — image collection loaded, double filter applied. User stories can begin.

---

## Phase 3: User Story 1 - Pre-procesamiento y Filtrado de Calidad (Priority: P1)

**Goal**: Clean, cloud-free L2A images for all 4 parcels with traceability report.

**Independent Test**: `print('Imagenes antes:', totalCrudas, 'despues:', totalFiltradas)`. Verify filtered count < original count. Verify SCL classes retained are only 4 and 5.

### Implementation for US1

- [x] T005 [US1] Apply double filter to linked collection via `.map(enmascararNubesDobleFiltro)` and store as `coleccionFiltrada` in `codigo_gee.js`
- [x] T006 [US1] Implement `calcularMetricas()` function: scale optical bands (B4,B5,B6,B7,B8) dividing by 10000, extract scaled band variables (b4,b5,b6,b7,b8) in `codigo_gee.js`
- [x] T007 [US1] Add console report: original image count vs post-filter count with `print()` for quality traceability per FR-003 in `codigo_gee.js`

**Checkpoint**: US1 complete — filtered collection ready, band scaling applied. Verify with `print()` in GEE Console.

---

## Phase 4: User Story 2 - Calculo de Indices Espectrales (Priority: P1)

**Goal**: NDRE, S2REP, MSAVI2 indices calculated. NDVI relegated to binary vegetation mask.

**Independent Test**: `print('NDRE mediana P1:', ndreP1)`. Verify NDRE ∈ [0.1, 0.6], S2REP ∈ [705, 740], MSAVI2 ∈ [0.2, 0.8]. Verify NDVI mask excludes non-vegetation pixels.

### Implementation for US2

- [x] T008 [US2] Calculate NDVI as binary mask: `(B8-B4)/(B8+B4) > 0.3` renamed as `NDVI_Mask` — only for vegetation masking, NOT biophysical estimation in `codigo_gee.js`
- [x] T009 [US2] Calculate NDRE using `normalizedDifference(['B8','B5'])` renamed as `NDRE` for visualization and cross-validation in `codigo_gee.js`
- [x] T010 [US2] Calculate S2REP using standard formula: `705 + 35 * (((B4+B7)/2 - B5) / (B6 - B5))` with `expression()`, renamed as `S2REP` per FR-006 in `codigo_gee.js`
- [x] T011 [US2] Calculate MSAVI2 using expression: `(2*NIR + 1 - sqrt(pow((2*NIR+1),2) - 8*(NIR-RED))) / 2`, renamed as `MSAVI2` in `codigo_gee.js`

**Checkpoint**: US2 complete — all 4 indices calculated. Verify ranges in Console.

---

## Phase 5: User Story 3 - Estimacion de Variables Biofisicas (Priority: P2)

**Goal**: LAI, Cab, Kc weekly values with configurable coefficients.

**Independent Test**: `print('LAI rango:', laiMin, laiMax, 'Cab rango:', cabMin, cabMax, 'Kc rango:', kcMin, kcMax)`. Verify LAI ∈ [0.1, 6.0], Cab ∈ [0, 100], Kc ∈ [0.2, 1.3].

### Implementation for US3

- [x] T012 [US3] Calculate LAI_RedEdge using configurable formula: `(S2REP - 700) * LAI_factor`, renamed as `LAI_RedEdge`. Factor default: 0.15 per FR-006 in `codigo_gee.js`
- [x] T013 [US3] Calculate Cab_RedEdge using configurable formula: `(S2REP - 700) * Cab_factor`, renamed as `Cab_RedEdge`. Factor default: 2 per FR-006 in `codigo_gee.js`
- [x] T014 [US3] Calculate Kc_Actual using configurable formula: `MSAVI2 * kc_slope + kc_intercept`, renamed as `Kc_Actual`. Defaults: slope=1.15, intercept=0.1 per FR-007 in `codigo_gee.js`
- [x] T015 [US3] Chain all index and biophysical calculations in `calcularMetricas()`, add bands to image, copy `system:time_start` property in `codigo_gee.js`

**Checkpoint**: US3 complete — biophysical variables calculated. Configurable at script top.

---

## Phase 6: User Story 4 - Reconstruccion Temporal Continua (Priority: P2)

**Goal**: Weekly regularized series with Savitzky-Golay gap-filling, Flag_Interpolacion.

**Independent Test**: `print('Semanas totales:', semanasTotal, 'Semanas interpoladas:', semanasInterpoladas)`. Verify no missing weeks. Verify Flag_Interpolacion=0 for real data weeks.

### Implementation for US4

- [x] T016 [US4] Build weekly sequence: calculate total weeks from startDate to endDate, generate `listaSemanas` via `ee.List.sequence()` in `codigo_gee.js`
- [x] T017 [US4] Implement weekly aggregation: for each week, filter collection, compute `median()` as representative pixel value per parcel using `reduceRegions()` with `ee.Reducer.mean()` at scale 10 in `codigo_gee.js`
- [x] T018 [US4] Implement Savitzky-Golay filter for gap-filling: apply temporal smoothing with window=5, degree=2 over the weekly series via `ee.Reducer` or iterative linear fit per research.md decision 2 in `codigo_gee.js`
- [x] T019 [US4] Set `Flag_Interpolacion`: 0 when `colSemana.size().gt(0)` (real observation), 1 otherwise (gap-filled). Add as property per FR-011 in `codigo_gee.js`

**Checkpoint**: US4 complete — continuous weekly series with interpolation flags.

---

## Phase 7: User Story 5 - Deteccion Temprana de Estres (Priority: P3)

**Goal**: 3-level stress alerts (Normal/Precaucion/Alerta Critica) using dynamic baseline.

**Independent Test**: `print('Alertas emitidas:', conteoAlertas)`. Simulate LAI drop and verify Alerta Critica triggers.

### Implementation for US5

- [x] T020 [US5] Build dynamic baseline: compute smoothed mean and stdDev from the Savitzky-Golay filtered LAI and Cab series per parcel, stored as `imgPromedio` and `imgStdDev` per FR-012 in `codigo_gee.js`
- [x] T021 [US5] Calculate z-score deviation: `(valorActual - mediaBase) / stdBase` for both LAI_RedEdge and Cab_RedEdge per FR-013 in `codigo_gee.js`
- [x] T022 [US5] Implement 3-level stress classification function: Normal (|z| < 1), Precaución (1 <= |z| < 2), Alerta Critica (|z| >= 2). Apply to each weekly record per FR-014 in `codigo_gee.js`
- [x] T023 [US5] Attach `Alerta_Estres` property to each Feature in the weekly series, using the maximum alert level from LAI and Cab checks per FR-014 in `codigo_gee.js`

**Checkpoint**: US5 complete — stress alerts generated for every parcel every week.

---

## Phase 8: User Story 6 - Exportacion de Resultados (Priority: P3)

**Goal**: CSV download + 3 GeoTIFFs at phenological milestones + NDRE timelapse.

**Independent Test**: Verify CSV in Drive has 7 columns and ~312 rows. Verify GeoTIFFs open in QGIS covering 4 parcels. Verify timelapse plays with date visible.

### Implementation for US6

- [x] T024 [US6] Flatten weekly FeatureCollection, filter nulls (`ee.Filter.notNull(['Cab_RedEdge'])`), prepare `serieLimpia` for CSV export per FR-015 in `codigo_gee.js`
- [x] T025 [US6] Export CSV via `Export.table.toDrive()` with 7 selectors: Fecha_Semanal, ID_Parcela, LAI_RedEdge, Cab_RedEdge, Kc_Actual, Flag_Interpolacion, Alerta_Estres. Folder: `Tesis_Mandarinas` per FR-015 + csv-schema contract in `codigo_gee.js`
- [x] T026 [US6] Implement `exportarHitoFenologico()` function: filter to cloud-free dates (<10% cloud cover) within phenological window, compute median composite, export NDRE GeoTIFF via `Export.image.toDrive()` at 10m scale per FR-016 in `codigo_gee.js`
- [x] T027 [US6] Call `exportarHitoFenologico()` for all 3 milestones: Hito 1 (2025-07-01 to 2025-08-15), Hito 2 (2025-10-01 to 2025-11-30), Hito 3 (2026-04-01 to 2026-05-31) in `codigo_gee.js`
- [x] T028 [US6] Generate NDRE timelapse: for each week, create NDRE visualization frame with date text overlay (`users/gena/packages:text`), duplicate to 2 frames, collect as ImageCollection, export via `Export.video.toDrive()` at 1 FPS, 720p per FR-017 + quickstart.md in `codigo_gee.js`

**Checkpoint**: US6 complete — all exports configured in Tasks tab.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Console validation reports, edge case handling, final script cleanup.

- [x] T029 Add module-by-module console validation: print image counts (M1), NDRE median parcel 1 (M2), LAI/Cab/Kc ranges (M3), interpolated weeks count (M4), alert counts by level (M5), export confirmation with task names (M6) in `codigo_gee.js`
- [x] T030 Handle edge cases: boundary weeks with insufficient data (use wider temporal window fallback), null S2REP values (skip pixel), zero-size collection weeks (flag as interpolated) in `codigo_gee.js`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup (T001-T002) — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational (T003-T004)
- **US2 (Phase 4)**: Depends on US1 (T005-T007) — needs filtered collection
- **US3 (Phase 5)**: Depends on US2 (T008-T011) — needs spectral indices
- **US4 (Phase 6)**: Depends on US3 (T012-T015) — needs biophysical bands
- **US5 (Phase 7)**: Depends on US4 (T016-T019) — needs smoothed series
- **US6 (Phase 8)**: Depends on US5 (T020-T023) — needs alert classification
- **Polish (Phase 9)**: Depends on US6 — needs all exports configured

### Within Each Phase

- T001 → T002 (any order, same phase)
- T003 → T004 (sequence matters: link before filter)
- T005 → T006 → T007 (sequential: filter, calculate, report)
- T008, T009, T010, T011 [P] (parallel — independent indices)
- T012, T013, T014 [P] (parallel — independent variables), then T015 (consolidation)
- T016 → T017 → T018 → T019 (sequential pipeline)
- T020 → T021 → T022 → T023 (sequential pipeline)
- T024 → T025, T026 [P], T028 [P] (parallel exports), then T027 (depends on T026)
- T029, T030 [P] (parallel polish)

### Critical Path

T001 → T003 → T005 → T008 → T012 → T016 → T020 → T024 → T029

---

## Parallel Example: Phase 4 (US2)

```bash
# Launch all 4 index calculations in parallel:
Task T008: "NDVI binary mask"
Task T009: "NDRE calculation"  
Task T010: "S2REP calculation"
Task T011: "MSAVI2 calculation"
```

## Parallel Example: Phase 8 (US6)

```bash
# Launch exports in parallel after T024 (data preparation):
Task T025: "CSV export to Drive"
Task T026: "Hito export function"
Task T028: "Timelapse generation"
```

---

## Implementation Strategy

### MVP First (US1 + US2 only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational (T003-T004)
3. Complete Phase 3: US1 (T005-T007)
4. Complete Phase 4: US2 (T008-T011)
5. **VALIDATE**: Console shows filtered counts, NDRE ∈ [0.1,0.6]
6. Deploy/demo: Map visualization in GEE with NDRE layer

### Incremental Delivery

1. Setup + Foundational → collection ready
2. Add US1 + US2 → indices visible on map (MVP!)
3. Add US3 → biophysical values in console
4. Add US4 + US5 → continuous series + alerts
5. Add US6 → CSV + GeoTIFF + timelapse downloadable
6. Polish → complete validation reports

---

## Notes

- All tasks implement sections within single file `codigo_gee.js`
- [P] tasks = different sections, no shared mutable state
- [Story] label maps task to specific user story for traceability
- Each checkpoint allows independent validation via GEE Console
- Configurable parameters at script top (T001) control model behavior
- Final script must execute in <5 min; heavy ops use async exports (Tasks)