# Data Model: Monitoreo Satelital de Mandarina Murcott

## Entities

### 1. Parcela

Experimental unit for spectral time series extraction.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| ID_Parcela | string | Unique parcel identifier | Values: "1", "2", "3", "4" |
| geometry | Polygon | Georeferenced vector boundary | Area = 0.5 ha, EPSG:4326 |
| cultivo | string | Crop type | Fixed: "Mandarina Murcott" |
| nio_implantacion | integer | Year planted | Range: 2022-2023 |
| marco_plantacion | string | Planting frame | "5.5m x 3.5m" |

**Source**: projects/proyectoleomespinosa/assets/ParcelasDefinidas (GEE FeatureCollection)

---

### 2. Registro Semanal

Output row in the standardized CSV. One record per parcel per week.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| Fecha_Semanal | date (YYYY-MM-DD) | Regularized weekly date | Fixed weekday, spaced 7 days |
| ID_Parcela | string | Parcel reference | FK → Parcela.ID_Parcela |
| LAI_RedEdge | float | Leaf Area Index from S2REP | Range: [0.1, 6.0] |
| Cab_RedEdge | float | Chlorophyll content proxy (μg/cm2) | Range: [0, 100] |
| Kc_Actual | float | Real crop coefficient from MSAVI2 | Range: [0.2, 1.3] |
| Flag_Interpolacion | integer (0/1) | Data origin indicator | 0 = satellite observation, 1 = gap-filled |
| Alerta_Estres | string (enum) | Stress classification | "Normal", "Precaucion", "Alerta Critica" |

**Primary Key**: (Fecha_Semanal, ID_Parcela)
**Expected Volume**: 4 parcels × ~78 weeks = ~312 rows total

**State Transitions**:

`
Flag_Interpolacion:  0 (observation)  → stays 0 forever
                     1 (gap-filled)   → stays 1 forever (historical record)

Alerta_Estres:       Normal           → Precaución        when |z-score| ∈ [1, 2]
                     Normal           → Alerta Critica    when |z-score| > 2
                     Precaución       → Normal            when |z-score| < 1
                     Precaución       → Alerta Critica    when |z-score| > 2
                     Alerta Critica   → Normal            when |z-score| < 1
                     Alerta Critica   → Precaución        when |z-score| ∈ [1, 2]
`

---

### 3. Hito Fenologico

Agricultural calendar period triggering spatial map export.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| 
ombre | string | Milestone name | "Reposo_Poda", "Floracion_Cuaje", "Cosecha" |
| echa_inicio | date | Period start | ISO 8601 |
| echa_fin | date | Period end | ISO 8601 |
| indice_visualizacion | string | Visualization index | Fixed: "NDRE" |

**Instances**:

| nombre | fecha_inicio | fecha_fin |
|--------|-------------|-----------|
| Reposo_Poda | 2025-07-01 | 2025-08-15 |
| Floracion_Cuaje | 2025-10-01 | 2025-11-30 |
| Cosecha | 2026-04-01 | 2026-05-31 |

---

### 4. Linea Base Dinamica

Smoothed historical trend used as reference for anomaly detection.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| parcela_id | string | Parcel reference | FK → Parcela.ID_Parcela |
| ariable | string | Monitored variable | "LAI_RedEdge" or "Cab_RedEdge" |
| media_movil | float | Smoothed expected value | Derived from S-G filter output |
| std_movil | float | Smoothed standard deviation | Derived from S-G residual analysis |

**Lifecycle**: Recalculated weekly as new observations are added. The S-G filter
provides the smoothed trend; the residual standard deviation of actual vs. smoothed
defines the confidence band.

---

## Variable Calculation Pipeline

`	ext
Sentinel-2 L2A Image
  → [Double Filter: CS+ > 0.90 AND SCL ∈ {4,5}]
  → [Scale bands: ÷10000]
  → NDVI = (B8 - B4) / (B8 + B4)                    → Binary mask (NDVI > 0.3)
  → NDRE = (B8 - B5) / (B8 + B5)                    → Visualization + cross-validation
  → S2REP = 705 + 35*(((B4+B7)/2 - B5)/(B6 - B5))   → Independent variable
  → LAI_RedEdge = (S2REP - 700) * LAI_factor         → (configurable: default 0.15)
  → Cab_RedEdge = (S2REP - 700) * Cab_factor         → (configurable: default 2)
  → MSAVI2 = (2*B8+1 - sqrt((2*B8+1)^2 - 8*(B8-B4))) / 2
  → Kc_Actual = MSAVI2 * kc_slope + kc_intercept     → (configurable: 1.15, 0.1)
  → [Savitzky-Golay: gap-filling + smoothing]
  → [Stress Detection: z-score vs dynamic baseline]
  → CSV Export
`
