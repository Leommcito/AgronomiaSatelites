# Implementation Plan: Multi-Índices STAC Abril 2026

**Branch**: `002-multi-index-stac` | **Date**: 2026-06-04 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-multi-index-stac/spec.md`

## Summary

Crear un script Python STAC autocontenido que descargue imágenes Sentinel-2 L2A
de abril 2026, calcule 5 índices espectrales (MSAVI2, S2REP, LAI_RedEdge,
Cab_RedEdge, Kc_Actual) aplicando máscara SCL + geométrica, y exporte cada
índice a su propia carpeta con PNG (colormap específico), TIF (GeoTIFF) y
CSV de estadísticas parcelarias (mean, std, pixeles válidos).

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**:
- `pystac-client` — Catálogo STAC Earth Search
- `odc-stac` / `stackstac` — Carga de Data Cube desde STAC
- `rioxarray` / `rasterio` — Exportación GeoTIFF
- `geopandas` — Carga de shapefile y máscara geométrica
- `xarray` / `numpy` — Procesamiento de arrays
- `matplotlib` — Exportación PNG

**Storage**: Sistema de archivos local, estructura `output/Imagenes/{Indice}/Abril2026/{PNG,TIF,estadisticas.csv}`

**Testing**: Validación post-ejecución vía scripts de verificación (no unit tests)

**Target Platform**: Windows local / Google Colab (auto-detección)

**Project Type**: Script de procesamiento de datos satelitales (data-processing)

**Performance Goals**: No aplica (1 mes, ~10-20 escenas, proceso secuencial)

**Constraints**: RAM limitada — procesar en batches de 5 escenas; dependiente de conexión a internet

**Scale/Scope**: 1 mes (abril 2026), 4 parcelas, 5 índices, ~10-20 escenas

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Estado | Justificación |
|-----------|--------|---------------|
| I. Implementaciones Autocontenidas | ✅ Pasa | Script Python autocontenido, auto-detecta Colab/local, instala dependencias |
| II. Fidelidad Metodológica | ✅ Pasa | Fórmulas idénticas a codigo_gee.js, coeficientes configurables |
| III. Filtrado Óptico (SCL) | ✅ Pasa | Máscara SCL clases 4,5. CS+ no disponible en STAC — documentado en Assumptions |
| IV. Borde Rojo | ✅ Pasa | MSAVI2, S2REP, LAI, Cab, Kc implementados con guardias numéricas |
| V. Gap-Filling | ✅ No aplica | Script exporta escenas individuales, no series temporales |
| VI. Detección de Estrés | ✅ No aplica | Competencia del pipeline GEE |
| VII. Exportación Espacial | ✅ Pasa | PNG + TIF por índice con colormaps específicos |
| VIII. CSV Estandarizado | ✅ Pasa | CSV por índice con columnas definidas en spec |
| IX. Exportación por Índice | ✅ Pasa | Carpetas separadas por índice, colormaps específicos |

**Veredicto**: GATE PASS — todas las violaciones ausentes o justificadas.

---

## Project Structure

### Documentation (this feature)

```text
specs/002-multi-index-stac/
├── plan.md              # This file
├── research.md          # Phase 0 — technical decisions
├── data-model.md        # Phase 1 — entities and relationships
├── quickstart.md        # Phase 1 — how to run
├── contracts/           # Phase 1 — (empty, no external interfaces)
├── checklists/
│   └── requirements.md  # Specification quality checklist
└── spec.md              # Feature specification
```

### Source Code (repository root)

```text
multi_indices_abril2026.py   # Script principal (Task 1)
output/Imagenes/             # Generated at runtime
├── MSAVI2/Abril2026/{PNG,TIF,estadisticas.csv}
├── S2REP/Abril2026/{PNG,TIF,estadisticas.csv}
├── LAI_RedEdge/Abril2026/{PNG,TIF,estadisticas.csv}
├── Cab_RedEdge/Abril2026/{PNG,TIF,estadisticas.csv}
└── Kc_Actual/Abril2026/{PNG,TIF,estadisticas.csv}
```

**Structure Decision**: Single script at repository root (matching existing pattern
of `Fase1_NDRE_2025_2026.ipynb` and `_run_meses.py`).

---

## Complexity Tracking

> No constitution violations to justify.
