# Data Model: Multi-Índices STAC Abril 2026

## Entities

### 1. Parcela

Experimental unit for spectral time series extraction.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| ID_Parcela | string | Unique parcel identifier | Values: "1","2","3","4" |
| geometry | Polygon | Georeferenced vector boundary | Area = 0.5 ha, EPSG:4326 |
| cultivo | string | Crop type | Fixed: "Mandarina Murcott" |

**Source**: `4ParcelasDefinidas.zip` (local) / `projects/proyectoleomespinosa/assets/ParcelasDefinidas` (GEE)

---

### 2. Escena

Individual satellite image tile that intersects the study area.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | string | STAC item ID | Unique per scene |
| fecha | datetime | Acquisition date | April 2026 |
| hora | datetime | Acquisition time | HH:MM:SS |
| eo:cloud_cover | float | Tile-level cloud cover % | [0, 100] |
| estado_nubosidad | string | Classification label | "Despejada" / "Nublada" / "SinDatos" |

---

### 3. Índice Espectral

Derived variable from spectral band combinations.

| Entity | Formula | Valid Range | Colormap |
|--------|---------|-------------|----------|
| MSAVI2 | (2×NIR+1 - sqrt((2×NIR+1)² - 8×(NIR-RED))) / 2 | [0, 1] | RdYlGn |
| S2REP | 705 + 35 × (((B4+B7)/2 - B5) / (B6 - B5)) | [705, 740] nm | turbo |
| LAI_RedEdge | (S2REP - 700) × LAI_factor (default 0.15) | [0.1, 6.0] | Greens |
| Cab_RedEdge | (S2REP - 700) × Cab_factor (default 2) | [0, 100] μg/cm² | YlGn |
| Kc_Actual | MSAVI2 × kc_slope (1.15) + kc_intercept (0.1) | [0.2, 1.3] | BrBG |

**Dependencies**:
- S2REP → LAI_RedEdge, Cab_RedEdge (derivación directa)
- MSAVI2 → Kc_Actual (derivación directa)

---

### 4. Registro Estadístico

Statistical summary per parcel per scene per index.

| Field | Type | Description |
|-------|------|-------------|
| fecha | string (YYYY-MM-DD) | Acquisition date |
| hora | string (HH:MM:SS) | Acquisition time |
| id_escena | string | Scene identifier (filename base) |
| nubes_porciento | float | Tile-level cloud cover |
| estado_nubosidad | string | "Despejada"/"Nublada"/"SinDatos" |
| {indice}_mean | float | Mean value of index within parcel |
| {indice}_std | float | Standard deviation of index within parcel |
| pixeles_validos | int | Count of non-NaN pixels in parcel |
| ruta_tif | string | Path to exported GeoTIFF |
| ruta_png | string | Path to exported PNG |

---

## Processing Pipeline

```text
STAC Earth Search
  → search(sentinel-2-l2a, bbox, datetime=2026-04)
  → for each scene:
    → load(bands=[red, rededge1, rededge2, rededge3, nir, scl])
    → scale bands (/10000)
    → SCL mask (classes 4,5)
    → geometric mask (parcel boundaries)
    → compute 5 indices
    → for each index:
      → determine suffix (Despejada/Nublada/SinDatos)
      → check if TIF exists (duplicate detection)
      → export GeoTIFF (float32, LZW, EPSG:4326)
      → export PNG (specific colormap)
      → compute per-parcel statistics
    → save per-index CSV
```

## Output Structure

```text
output/Imagenes/
├── MSAVI2/Abril2026/
│   ├── PNG/          ← MSAVI2_Abril_001_20260405_123456_Despejada.png
│   ├── TIF/          ← MSAVI2_Abril_001_20260405_123456_Despejada.tif
│   └── estadisticas.csv
├── S2REP/Abril2026/...
├── LAI_RedEdge/Abril2026/...
├── Cab_RedEdge/Abril2026/...
└── Kc_Actual/Abril2026/...
```
