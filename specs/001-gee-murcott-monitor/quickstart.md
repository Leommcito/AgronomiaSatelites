# Quickstart: Monitoreo Satelital de Mandarina Murcott

## Prerequisites

1. Google Earth Engine account (https://earthengine.google.com)
2. Access to asset: `projects/proyectoleomespinosa/assets/ParcelasDefinidas`
3. Google Drive with folder `Tesis_Mandarinas` (created automatically on first export)

## How to Run

1. Open GEE Code Editor: https://code.earthengine.google.com
2. Copy the full content of `codigo_gee.js` from this repository
3. Paste into the Code Editor
4. Click **Run**
5. Check the **Console** tab for module validation output:
   - Module 1: Pre-processed images count (before/after filtering)
   - Module 2: NDRE median for Parcela 1
   - Module 3: LAI/Cab/Kc ranges verification
   - Module 4: Interpolated weeks count
   - Module 5: Stress alerts count
6. Go to the **Tasks** tab and click **Run** on each export:
   - `Dataset_Fenologico_Mandarina_Estandarizado` (CSV)
   - `TIF_Hito_1_Reposo_Poda` (GeoTIFF)
   - `TIF_Hito_2_Floracion` (GeoTIFF)
   - `TIF_Hito_3_Cosecha` (GeoTIFF)
   - `Timelapse_NDRE` (MP4 video)
7. Files appear in Google Drive under `Tesis_Mandarinas/`

## Configuration Parameters

Edit these values at the top of the script before running:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `startDate` | `2025-01-01` | Start of monitoring period |
| `endDate` | `2026-06-01` | End of monitoring period |
| `LAI_factor` | `0.15` | S2REP to LAI conversion factor |
| `Cab_factor` | `2` | S2REP to chlorophyll conversion factor |
| `kc_slope` | `1.15` | MSAVI2 to Kc slope |
| `kc_intercept` | `0.1` | MSAVI2 to Kc intercept |
| `sg_window` | `5` | Savitzky-Golay filter window size |
| `sg_degree` | `2` | Savitzky-Golay polynomial degree |

## Output Files

| File | Format | Content |
|------|--------|---------|
| `Dataset_Fenologico_Mandarina_Estandarizado.csv` | CSV | 7 columns, ~312 rows |
| `TIF_Hito_1_Reposo_Poda.tif` | GeoTIFF | NDRE map, Jul-Aug 2025 |
| `TIF_Hito_2_Floracion.tif` | GeoTIFF | NDRE map, Oct-Dec 2025 |
| `TIF_Hito_3_Cosecha.tif` | GeoTIFF | NDRE map, Apr-May 2026 |
| `Timelapse_NDRE.mp4` | MP4 | Weekly NDRE animation, ~78 frames |

## Troubleshooting

- **Asset not found**: Verify access to `projects/proyectoleomespinosa/assets/ParcelasDefinidas`
- **Timeout (>5 min)**: Reduce `maxPixels` in export calls; ensure async exports are used for heavy operations
- **Empty CSV**: Check that date range contains Sentinel-2 imagery; verify cloud filtering is not too aggressive
- **No Google Drive folder**: The `folder` parameter creates the folder on first export; no manual creation needed

