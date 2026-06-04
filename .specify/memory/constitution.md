<!--
  Sync Impact Report
  ==================
  Version change: 1.1.0 → 1.2.0
  Bump rationale: MINOR — New platform scope (Python/STAC) added alongside existing GEE pipeline.
                    New Principle IX (Exportación por Índice). Expanded Platform Constraints.

  Modified principles:
    - I: "Script Único y Autocontenido" → "Implementaciones Autocontenidas por Plataforma"
         Ahora cubre tanto GEE como Python/STAC como implementaciones válidas.
    - VIII: Salida Tabular Estandarizada (CSV) — agregado formato per-índice como opcional.

  Added sections:
    - Principle IX: Exportación por Índice (Per-Index Exports)
    - Python/STAC Platform Constraints en Restricciones de Plataforma

  Removed sections: None
  Templates requiring updates:
    - .specify/templates/plan-template.md     ✅ No changes needed
    - .specify/templates/spec-template.md     ✅ No changes needed
    - .specify/templates/tasks-template.md    ✅ No changes needed
  Follow-up TODOs: None — all placeholders resolved.
-->

# Constitución del Proyecto: Monitoreo Satelital de Mandarina Murcott

## Propósito

Este proyecto implementa metodologías de teledetección para el monitoreo satelital
de plantaciones de mandarina Murcott (*Citrus reticulata*) en la Provincia de Jujuy,
Argentina, durante el período 2025–2026. El proyecto cuenta con dos pipelines
complementarios:

1. **Pipeline GEE (Google Earth Engine)**: Script unificado en `codigo_gee.js` que
   produce series temporales semanales continuas con gap-filling, alertas de estrés
   y exportaciones agendadas a Google Drive. Basado en la metodología de
   `Informacion.md` — productos Sentinel-2 L2A, índices de Borde Rojo,
   reconstrucción temporal Savitzky-Golay y detección de estrés por z-score.

2. **Pipeline Python STAC**: Scripts y notebooks Python (vía `pystac-client` y
   `odc.stac`) para descarga y procesamiento local de imágenes Sentinel-2,
   incluyendo exportación de índices espectrales en formato ráster (GeoTIFF + PNG)
   con estadísticas parcelarias por escena individual.

Ambos pipelines cubren **4 parcelas experimentales de 0.5 ha cada una** (2 ha totales),
delimitadas mediante planimetría vectorial georreferenciada
(`4ParcelasDefinidas.zip` / asset `projects/proyectoleomespinosa/assets/ParcelasDefinidas`).

---

## Principios Fundamentales (Core Principles)

### I. Implementaciones Autocontenidas por Plataforma (NON-NEGOTIABLE)

**Cada pipeline debe ser autocontenido dentro de su plataforma objetivo.**

- **Pipeline GEE**: El script (`codigo_gee.js`) debe poder copiarse, pegarse en el
  Editor de Código de GEE y ejecutarse sin configuración adicional más allá del asset
  de parcelas y la carpeta Drive de destino. No se permite dividir la lógica en
  múltiples scripts GEE ni dependencias fuera del ecosistema nativo de GEE.
- **Pipeline Python/STAC**: Cada script o notebook Python debe ser autocontenido:
  auto-detectar entorno (Colab vs local), instalar dependencias faltantes, y ejecutarse
  sin intervención manual más allá de la ruta del shapefile.
- Ambos pipelines comparten el mismo shapefile/asset de parcelas como fuente única
  de verdad para la geometría de las unidades experimentales.

**Racional**: La plataforma GEE favorece scripts monolíticos; la plataforma Python/STAC
favorece scripts autocontenidos con detección de entorno. Cada implementación debe ser
reproducible por terceros (agrónomos, revisores de tesis) sin configuraciones externas.

---

### II. Fidelidad y Trazabilidad Metodológica

**Cada elemento de la metodología descrita en `Informacion.md` debe tener una
contraparte trazable en el código.**

- Toda sección del documento metodológico (1.1 a 4.3) debe estar implementada o
  explícitamente marcada con justificación documentada.
- Las decisiones de simplificación deben:
  - Estar documentadas como comentario en el código.
  - Incluir la referencia bibliográfica que respalda la simplificación.
  - Tener un plan de reemplazo cuando se disponga de coeficientes validados.
- El código debe referenciar las fuentes académicas: Ali et al. (2022),
  Ippolito et al. (2023), Della Bellver et al. (2024), Rouault et al. (2025),
  Ramírez-Juidias et al. (2023).

**Racional**: El proyecto es una tesis académica. La trazabilidad es requisito
para la defensa y publicación de resultados.

---

### III. Filtrado de Calidad Óptica (GATE OBLIGATORIO)

**Ningún píxel sin filtrar puede participar en los cálculos de índices.**

- **Pipeline GEE**: Doble filtro — Cloud Score+ (`cs_cdf >= 0.90`) Y SCL (clases 4,5).
  Aplicado via `updateMask()` antes de cualquier cálculo.
- **Pipeline Python/STAC**: Filtro SCL (clases 4,5) aplicado via máscara booleana
  post-descarga. Cloud Score+ NO está disponible en STAC.
- Ambos pipelines deben reportar (vía `print()`) la cantidad de escenas/píxeles que
  sobreviven al filtrado.
- NO se debe usar `eo:cloud_cover` como filtro de búsqueda en STAC para parcelas
  pequeñas (< 10 ha). Solo se usa para etiquetar el sufijo del nombre del archivo.

**Racional**: La región de Jujuy tiene cobertura nubosa significativa. Sin filtrado,
los falsos positivos contaminan las series temporales y las alertas de estrés.
`eo:cloud_cover` mide nubes a nivel de tile (100 km × 100 km) — no correlaciona
con parcelas de 0.5 ha.

---

### IV. Primacía Espectral del Borde Rojo sobre NDVI

**El NDVI queda relegado a enmascarador secundario. La cuantificación biofísica usa
exclusivamente índices de Borde Rojo.**

- **NDVI**: Solo como máscara binaria de vegetación (NDVI > 0.3 → vegetación presente).
  No se usa para estimar LAI, Clorofila ni Kc.
- **NDRE**: `(B8 - B5) / (B8 + B5)`. Índice primario para visualización.
- **S2REP**: `705 + 35 * (((B4 + B7) / 2 - B5) / (B6 - B5))`. Variable independiente
  para estimar LAI y Cab. Incluir guardia de división por cero: `|B6 - B5| < 0.0001`.
- **MSAVI2**: `(2*NIR + 1 - sqrt((2*NIR + 1)² - 8*(NIR - RED))) / 2`. Mitiga ruido
  de suelo/maleza. Base para derivar Kc. Incluir guardia de discriminante negativo.
- **LAI_RedEdge**: `(S2REP - 700) × LAI_factor` (default 0.15). Clip a [0.1, 6.0].
- **Cab_RedEdge**: `(S2REP - 700) × Cab_factor` (default 2). Clip a [0, 100] μg/cm².
- **Kc_Actual**: `MSAVI2 × kc_slope + kc_intercept` (defaults 1.15, 0.1).
  Clip a [0.2, 1.3].

**Racional**: En cítricos jóvenes-adultos (3-4 años), el NDVI se satura cuando el LAI
supera 2.5–3.0. Las bandas de Borde Rojo (B5, B6, B7) penetran más profundamente
en el dosel (Ali et al., 2022).

---

### V. Reconstrucción Temporal con Whittaker/Savitzky-Golay (Gap-Filling)

**El relleno de vacíos por nubosidad debe usar un filtro que respete la trayectoria
biológica del cultivo.**

- **Pipeline GEE**: Savitzky-Golay (window=5, degree=2) como gap-filling principal.
  Whittaker Wavelet queda diferido a versión futura por limitaciones de GEE.
- **Flag_Interpolacion**: Cada registro semanal incluye indicador binario:
  - `0` = dato basado en observación satelital real (píxeles válidos > 0).
  - `1` = dato interpolado matemáticamente (gap-filling).
- El flag debe basarse en conteo de píxeles válidos sobre las parcelas
  (`reduceRegion(ee.Reducer.count())`), no en cantidad de imágenes en la colección.
- **Pipeline Python/STAC**: No aplica gap-filling. Exporta escenas individuales
  con datos crudos. El suavizado temporal es potestad del pipeline GEE.

**Racional**: Sin gap-filling, las series temporales tienen vacíos de 10-20 días
en temporada de lluvias. Savitzky-Golay es la alternativa implementable en GEE.

---

### VI. Detección de Estrés por Desviación de Línea Base Dinámica

**Las alertas se disparan por desviación significativa respecto a la curva fenológica
esperada, no por umbrales fijos.**

- **Línea base**: La "memoria matemática" de la curva suavizada para cada variable
  (LAI, Cab).
- **Tres niveles de alerta**: `Normal` (±1σ), `Precaución` (1–2σ),
  `Alerta Crítica` (>2σ).
- **Variables monitoreadas**: LAI_RedEdge y Cab_RedEdge. Cualquier caída anómala
  dispara la alerta.
- **Pipeline Python/STAC**: No incluye detección de estrés (es competencia del
  pipeline GEE con series temporales completas).

---

### VII. Exportación Espacial Restringida a Hitos Fenológicos

**Pipeline GEE**:
- Solo se exportan GeoTIFFs en hitos fenológicos agronómicamente relevantes:
  Hito 1 (Reposo/Poda: Jul–Ago), Hito 2 (Floración: Oct–Dic),
  Hito 3 (Cosecha: Abr–Jun).
- Se genera timelapse NDRE semanal animado (MP4).
- Exportación a Google Drive (`folder: 'Tesis_Mandarinas'`).

**Pipeline Python/STAC**:
- Exporta escenas individuales (GeoTIFF + PNG) para todos los índices calculados.
- Sin restricción de hitos fenológicos — el usuario decide qué fechas descargar.
- Exportación a sistema de archivos local.

---

### VIII. Salida Tabular Estandarizada (CSV)

**Pipeline GEE**:
Columnas obligatorias (en este orden):

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `Fecha_Semanal` | `YYYY-MM-DD` | Fecha regularizada (día fijo de la semana) |
| `ID_Parcela` | `string` | Identificador de parcela (1-4) |
| `LAI_RedEdge` | `float` | Índice de Área Foliar estimado |
| `Cab_RedEdge` | `float` | Contenido de Clorofila (μg/cm²) |
| `Kc_Actual` | `float` | Coeficiente de cultivo derivado |
| `Flag_Interpolacion` | `0` o `1` | Origen del dato |
| `Alerta_Estres` | `string` | Normal / Precaución / Alerta Crítica |
| `NDRE` | `float` | Índice NDRE (opcional) |
| `MSAVI2` | `float` | Índice MSAVI2 (opcional) |
| `S2REP` | `float` | Posición del borde rojo (opcional) |
| `NDVI` | `float` | Índice NDVI (opcional) |

- Exportación semanal a Google Drive. ~312 filas (4 parcelas × ~78 semanas).

**Pipeline Python/STAC**:
- Por cada índice, un CSV `estadisticas.csv` con estadísticas parcelarias por escena.
- Columnas: `fecha, hora, id_escena, nubes_porciento, estado_nubosidad,
  {indice}_mean, {indice}_std, pixeles_validos, ruta_tif, ruta_png`
- El CSV es por índice (no global) y por mes de procesamiento.

---

### IX. Exportación por Índice (Per-Index Exports)

**Cada índice espectral procesado debe exportarse en su propia carpeta, con su propio
colormap de visualización y sus propias estadísticas.**

- Estructura de directorios: `output/Imagenes/{Indice}/Abril2026/{PNG,TIF,estadisticas.csv}`
- Cada índice usa un colormap específico para su visualización PNG:

| Índice | Colormap | vmin | vmax |
|--------|----------|------|------|
| MSAVI2 | RdYlGn | 0.2 | 0.8 |
| S2REP | turbo (heatmap) | 705 | 740 |
| LAI_RedEdge | Greens | 0.1 | 6.0 |
| Cab_RedEdge | YlGn | 0 | 100 |
| Kc_Actual | BrBG | 0.2 | 1.3 |

- Nomenclatura de archivos: `{INDICE}_{Mes}_{contador:03d}_{YYYYMMDD}_{HHMMSS}_{Despejada/Nublada/SinDatos}`
- Resolución espacial: 10m para todos los índices (bandas 20m upsampeadas vía
  `odc.stac.load` con `resolution=0.0001`).
- El sufijo de nubosidad se determina por escena (NO filtra, solo etiqueta):
  - `Despejada` si `eo:cloud_cover < 10%`
  - `Nublada` si `eo:cloud_cover ≥ 10%`
  - `SinDatos` si todos los píxeles del índice son NaN
- Detección de duplicados: verificar existencia del TIF antes de procesar.

**Racional**: Los índices espectrales tienen diferentes rangos, colormaps y
aplicaciones agronómicas. Mezclarlos en un mismo archivo o carpeta dificulta
la interpretación visual y el análisis por parcela.

---

## Restricciones de Plataforma y Tecnología

### Plataforma GEE

- **Google Earth Engine (GEE)** — JavaScript API (Editor de Código).
- El script debe ejecutarse en el entorno estándar sin funciones experimentales.
- **Timeout**: 5 minutos. Usar exportaciones asíncronas (Tasks) para operaciones pesadas.

### Plataforma Python/STAC

- **Python 3.10+** (local o Google Colab).
- **Dependencias**: `pystac-client`, `stackstac`, `rioxarray`, `geopandas`,
  `rasterio`, `odc-stac`, `xarray`, `matplotlib`, `numpy`, `pandas`.
- **Catálogo**: Earth Search AWS (`https://earth-search.aws.element84.com/v1`).
- **Auto-detección**: El script debe detectar si se ejecuta en Colab o local.
- **Memoria**: Procesar escenas en batches de 5 para evitar saturación de RAM.
- **Formato de exportación**: GeoTIFF (float32, LZW, CRS EPSG:4326) + PNG (200 dpi).

### Fuentes de Datos Compartidas

| Dataset | GEE Asset / STAC Collection | Propósito |
|---------|---------------------------|-----------|
| Sentinel-2 L2A | `COPERNICUS/S2_SR_HARMONIZED` (GEE) / `sentinel-2-l2a` (STAC) | Reflectancia de superficie |
| Cloud Score+ | `GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED` | Solo GEE — no disponible en STAC |
| Parcelas | Asset GEE / `4ParcelasDefinidas.zip` (local) | Geometría de las 4 parcelas |
| SCL | Banda incluida en L2A | Clasificación de escena (ambos pipelines) |

---

## Flujo de Desarrollo y Protocolo de Validación

### Orden de Implementación

1. **Pre-procesamiento**: L2A, filtro SCL, máscara geométrica.
2. **Índices espectrales**: NDRE, S2REP, MSAVI2.
3. **Variables biofísicas**: LAI, Cab, Kc.
4. **Reconstrucción temporal**: Savitzky-Golay (solo GEE).
5. **Detección de estrés**: Línea base dinámica + 3 niveles (solo GEE).
6. **Exportación tabular**: CSV semanal (GEE) / CSV por índice (Python).
7. **Exportación espacial**: GeoTIFFs por hito (GEE) + PNGs por escena (Python).
8. **Visualización**: Timelapse NDRE (GEE) + mapas de índice por escena (Python).

### Protocolo de Validación

- **Pipeline GEE**: Validación por `print()` en Consola (conteo de imágenes, rangos).
- **Pipeline Python/STAC**: Validación post-ejecución (verificar TIFs, CSVs, PNGs).
- Ambos pipelines deben verificar rangos fisiológicos de todos los índices calculados.

### Commits y Versionado

- Commits por módulo completado y validado.
- Prefijo: `feat(gee):` para pipeline GEE, `feat(stac):` para pipeline Python.

---

## Gobernanza

### Jerarquía Documental

1. **Esta Constitución** — Principios innegociables.
2. **`Informacion.md`** — Metodología académica de referencia.
3. **`codigo_gee.js`** — Implementación GEE.
4. **Scripts Python (`multi_indices_*.py`)** — Implementación Python/STAC.
5. **`Informacionsitio.md`** — Contexto agronómico complementario.

### Procedimiento de Enmienda

1. Proponer el cambio con justificación escrita.
2. Evaluar impacto en los principios y en las salidas.
3. Si el cambio elimina un principio: bump MAJOR.
4. Si agrega módulo/plataforma/sección: bump MINOR.
5. Si es corrección o clarificación: bump PATCH.
6. Actualizar `LAST_AMENDED_DATE` y `CONSTITUTION_VERSION`.
7. Sincronizar implementaciones afectadas.

### Compliance Review

- Revisión de cumplimiento constitucional antes de dar por terminado un módulo.
- Violaciones críticas bloquean la entrega; mayores requieren plan de resolución;
  menores se documentan como limitaciones conocidas.

---

**Version**: 1.2.0 | **Ratified**: 2026-06-01 | **Last Amended**: 2026-06-04
