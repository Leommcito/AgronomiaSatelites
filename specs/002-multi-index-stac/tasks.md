# Tasks: Multi-Índices STAC Abril 2026

**Input**: Design documents from `specs/002-multi-index-stac/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, quickstart.md

**Tests**: Not requested in spec. Validation via post-execution verification scripts.

**Organization**: Single script `multi_indices_abril2026.py` — tasks build it incrementally.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different sections, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US3)
- All file paths reference sections within `multi_indices_abril2026.py`

---

## Phase 1: Setup (Script Initialization)

**Purpose**: Script bootstrap — auto-detección de entorno, imports, estructura base.

- [ ] T001 Create script file with metadata comment block, auto-detección Colab/local, and all imports in `multi_indices_abril2026.py`

- [ ] T002 [P] Add configurable parameters section at script top: SHAPEFILE_PATH, BASE_DIR, PERIODO_INICIO, PERIODO_FIN, LAI_factor, Cab_factor, kc_slope, kc_intercept, UMBRAL_NUBES, BATCH_SIZE in `multi_indices_abril2026.py`

**Checkpoint**: Script skeleton ready — environment detection works, all imports available, parameters configurable.

---

## Phase 2: Foundational (Shared Infrastructure)

**Purpose**: Core functions used by ALL user stories. MUST complete before any user story.

- [ ] T003 [P] Implement shapefile loading function: load shapefile via geopandas, calculate bbox, ensure EPSG:4326 CRS in `multi_indices_abril2026.py`

- [ ] T004 [P] Implement STAC catalog connection and search function: connect to Earth Search, search by bbox and datetime range in `multi_indices_abril2026.py`

- [ ] T005 [P] Implement helper functions:
  - `aplicar_mascara_scl(scl)` — SCL mask for classes 4,5
  - `aplicar_mascara_geometrica(da, gdf)` — geometry mask using rasterio
  - `exportar_tif(da, path)` — GeoTIFF export with fallback
  - `exportar_png(data, path, cmap_name, vmin, vmax)` — PNG export
  in `multi_indices_abril2026.py`

- [ ] T006 [P] Implement index calculation functions:
  - `calcular_msavi2(nir, red)` — with discriminant guard
  - `calcular_s2rep(b4, b5, b6, b7)` — with division-by-zero guard
  - `calcular_lai(s2rep)` — clip to [0.1, 6.0]
  - `calcular_cab(s2rep)` — clip to [0, 100]
  - `calcular_kc(msavi2)` — clip to [0.2, 1.3]
  in `multi_indices_abril2026.py`

**Checkpoint**: Foundation ready — shapefile loads, STAC connects, all 5 index formulas and helper functions implemented.

---

## Phase 3: User Story 1 — Cálculo y Exportación de Índices (Priority: P1)

**Goal**: Process April 2026 scenes, calculate 5 indices, export GeoTIFFs.

**Independent Test**: Run script, verify `output/Imagenes/MSAVI2/Abril2026/TIF/` contains TIF files with CRS and 1 band.

- [ ] T007 [US1] Implement STAC search for April 2026: connect catalog, search with bbox and datetime, list items with metadata (eo:cloud_cover), print scene summary in `multi_indices_abril2026.py`

- [ ] T008 [US1] Implement scene processing loop:
  For each scene in April 2026:
  1. Load bands=[red, rededge1, rededge2, rededge3, nir, scl] at resolution=0.0001
  2. Scale optical bands /10000
  3. Apply SCL mask + geometric mask
  4. Calculate all 5 indices
  5. For each index: determine suffix (Despejada/Nublada/SinDatos), build filename, check duplicate, export TIF
  in `multi_indices_abril2026.py`

- [ ] T009 [US1] Add duplicate detection: before exporting TIF, check if file already exists. If exists, skip scene entirely with print message in `multi_indices_abril2026.py`

**Checkpoint**: US1 complete — TIFs exported for all 5 indices in separate folders.

---

## Phase 4: User Story 2 — Visualización con Colormaps (Priority: P2)

**Goal**: Each index exported as PNG with its specific colormap.

**Independent Test**: Verify 5 PNG generators produce images with correct colormap by checking output folder structure.

- [ ] T010 [US2] Add PNG export to scene processing loop: after TIF export, export PNG for the same index using its specific colormap. Colormap mapping:
  - MSAVI2: RdYlGn [0.2, 0.8]
  - S2REP: turbo [705, 740]
  - LAI_RedEdge: Greens [0.1, 6.0]
  - Cab_RedEdge: YlGn [0, 100]
  - Kc_Actual: BrBG [0.2, 1.3]
  in `multi_indices_abril2026.py`

**Checkpoint**: US2 complete — PNGs with correct colormaps exported alongside TIFs.

---

## Phase 5: User Story 3 — Estadísticas Parcelarias (Priority: P3)

**Goal**: Per-index CSV with statistics for each parcel.

**Independent Test**: Verify `estadisticas.csv` exists in each index folder with correct columns and values in physiological ranges.

- [ ] T011 [US3] Implement `calcular_estadisticas_parcela(da, gdf, nombre_indice)` function: for each parcel, compute mean, std, pixel_count of the index within parcel boundaries in `multi_indices_abril2026.py`

- [ ] T012 [US3] Integrate statistics into processing loop: after TIF+PNG export for each index, compute per-parcel statistics and collect for CSV export in `multi_indices_abril2026.py`

- [ ] T013 [US3] Implement per-index CSV export: after processing all scenes, save one `estadisticas.csv` per index folder with columns: fecha, hora, id_escena, nubes_porciento, estado_nubosidad, {indice}_mean, {indice}_std, pixeles_validos, ruta_tif, ruta_png in `multi_indices_abril2026.py`

**Checkpoint**: US3 complete — per-index CSV files with parcel statistics.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final report, validation prints, error handling, cleanup.

- [ ] T014 Add final report section: print summary of processed scenes, exported files by index, and detected duplicates. Include per-index file counts and total statistics in `multi_indices_abril2026.py`

- [ ] T015 Add edge case handling: graceful error recovery per scene (try/except per scene, continue on error), print warning messages for missing bands or empty scenes, timeout handling for STAC connection in `multi_indices_abril2026.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup (T001-T002) — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational (T003-T006)
- **US2 (Phase 4)**: Depends on US1 (T007-T009) — needs TIF export logic
- **US3 (Phase 5)**: Depends on US2 (T010) — needs PNG paths for CSV
- **Polish (Phase 6)**: Depends on all user stories

### Within Each Phase

- T001 → T002 (any order)
- T003, T004, T005, T006 [P] (parallel — independent functions)
- T007 → T008 → T009 (sequential pipeline: search, process, dedup)
- T010 (depends on T008)
- T011 → T012 → T013 (sequential: function, integration, CSV save)
- T014 → T015 (any order)

### Critical Path

T001 → T003/T004/T005/T006 → T007 → T008 → T009 → T010 → T011 → T012 → T013 → T014

### Parallel Opportunities

Phase 2: All 4 foundational tasks [P] can run in parallel (different functions)
Phase 6: T014 and T015 can run in parallel

---

## Implementation Strategy

### MVP First (US1 only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational (T003-T006)
3. Complete Phase 3: US1 (T007-T009)
4. **VALIDATE**: TIFs exist in 5 index folders with correct CRS
5. Deploy/demo

### Incremental Delivery

1. Setup + Foundational → script skeleton
2. Add US1 → TIF export working (MVP!)
3. Add US2 → PNG with colormaps
4. Add US3 → CSV with per-parcel statistics
5. Polish → final validation report + error recovery

---

## Notes

- All tasks implement sections within single file `multi_indices_abril2026.py`
- No tests requested — validation via post-execution verification
- [P] tasks = different sections, no shared mutable state
- [Story] label maps task to specific user story for traceability
- Each checkpoint allows independent validation
