# Feature Specification: Multi-Índices STAC Abril 2026

**Feature Branch**: `002-multi-index-stac`

**Created**: 2026-06-04

**Status**: Draft

**Input**: Pipeline Python/STAC para descarga y procesamiento de imágenes Sentinel-2 L2A
de abril 2026, calculando 5 índices espectrales (MSAVI2, S2REP, LAI_RedEdge,
Cab_RedEdge, Kc_Actual) con exportación por índice a carpetas separadas con
mapas de color específicos y estadísticas parcelarias.

---

## User Scenarios & Testing

### User Story 1 - Cálculo y Exportación de Múltiples Índices STAC (Priority: P1)

El ingeniero agrónomo necesita obtener mapas de MSAVI2, S2REP, LAI, Cab y Kc
para sus 4 parcelas de mandarina Murcott durante abril 2026, en formato ráster
(GeoTIFF) con visualización PNG y estadísticas parcelarias, todo organizado
por índice en carpetas separadas.

**Why this priority**: Sin esta funcionalidad, el ingeniero no tiene acceso a
los índices de Borde Rojo y variables biofísicas fuera del pipeline GEE. Este
script permite descarga local para validación cruzada con datos de campo
(visita técnica de abril 2026).

**Independent Test**: Ejecutar el script y verificar que se generan 5 carpetas
de índice con archivos PNG, TIF y CSV en cada una. Verificar que los valores
de cada índice están dentro de rangos fisiológicos conocidos.

**Acceptance Scenarios**:

1. **Given** el período abril 2026 y el shapefile de 4 parcelas, **When** se
   ejecuta el script de procesamiento, **Then** se generan 5 carpetas
   (MSAVI2, S2REP, LAI_RedEdge, Cab_RedEdge, Kc_Actual) dentro de
   `output/Imagenes/`, cada una con subcarpetas PNG/ y TIF/ conteniendo
   archivos por escena procesada.

2. **Given** una escena satelital con cobertura parcial de nubes, **When** se
   procesa, **Then** los píxeles clasificados como nubes (SCL ≠ 4,5) son
   enmascarados (NaN) y no contribuyen a las estadísticas parcelarias,
   mientras que los píxeles válidos sí se incluyen.

3. **Given** el script ya se ejecutó una vez, **When** se ejecuta nuevamente,
   **Then** no se sobrescriben archivos existentes (detección de duplicados
   por verificación de existencia de TIF).

---

### User Story 2 - Visualización por Índice con Colormap Específico (Priority: P2)

El ingeniero necesita poder visualizar cada índice espectral con su propia
paleta de colores y rango, ya que cada uno representa una variable agronómica
distinta (vigor vegetal, clorofila, área foliar, coeficiente de cultivo).

**Why this priority**: Usar la misma paleta para todos los índices produce
mapas engañosos. S2REP (longitud de onda en nm) requiere un mapa de calor,
mientras que LAI (índice de área foliar) requiere verde graduado.

**Independent Test**: Verificar que los archivos PNG generados para cada
índice utilizan el colormap y rango especificado en la configuración.

**Acceptance Scenarios**:

1. **Given** un archivo PNG de S2REP, **When** se inspecciona visualmente,
   **Then** usa una paleta de tipo mapa de calor (turbo/inferno) con rango
   705-740 nm.

2. **Given** un archivo PNG de LAI_RedEdge, **When** se inspecciona,
   **Then** usa una paleta de verdes (Greens) con rango 0.1-6.0.

3. **Given** un archivo PNG de MSAVI2, **When** se inspecciona,
   **Then** usa una paleta rojo-amarillo-verde (RdYlGn) con rango 0.2-0.8.

4. **Given** un archivo PNG de Cab_RedEdge, **When** se inspecciona,
   **Then** usa una paleta amarillo-verde (YlGn) con rango 0-100 μg/cm².

5. **Given** un archivo PNG de Kc_Actual, **When** se inspecciona,
   **Then** usa una paleta marrón-verde-azul (BrBG) con rango 0.2-1.3.

---

### User Story 3 - Estadísticas Parcelarias por Índice (Priority: P3)

El ingeniero necesita, para cada escena procesada, un archivo CSV con
estadísticas descriptivas (media, desviación estándar, cantidad de píxeles
válidos) de cada índice, calculadas dentro de los límites de cada parcela.

**Why this priority**: Los mapas PNG muestran la distribución espacial, pero
el CSV permite análisis cuantitativo, comparación entre parcelas, y
alimentación de modelos agronómicos externos.

**Independent Test**: Abrir el CSV de estadísticas de cualquier índice y
verificar que contiene las columnas especificadas con valores numéricos
en rangos plausibles.

**Acceptance Scenarios**:

1. **Given** una escena procesada con datos válidos sobre las parcelas,
   **When** se genera el CSV de estadísticas, **Then** contiene columnas:
   fecha, hora, id_escena, nubes_porciento, estado_nubosidad,
   {indice}_mean, {indice}_std, pixeles_validos, ruta_tif, ruta_png.

2. **Given** una escena completamente nublada sobre todas las parcelas,
   **When** se generan las estadísticas, **Then** el CSV refleja
   pixeles_validos = 0 y valores mean/std vacíos para esa escena-parcela.

3. **Given** parcelas con diferente cobertura vegetal, **When** se comparan
   sus estadísticas de MSAVI2, **Then** las parcelas con mayor vigor
   tienen valores mean más altos y std más bajos (mayor uniformidad).

---

### Edge Cases

- ¿Qué sucede cuando una banda necesaria (ej. B6 para S2REP) no está
  disponible en el catálogo STAC para una fecha específica?
- ¿Cómo maneja el sistema la división por cero en la fórmula de S2REP
  cuando B6 ≈ B5?
- ¿Qué sucede con el discriminante negativo en MSAVI2 cuando los valores
  de NIR y Red producen una raíz cuadrada de número negativo?
- ¿Cómo se comporta el script si no hay imágenes disponibles para abril
  2026 (ventana sin cobertura satelital)?
- ¿Qué pasa si el shapefile de parcelas contiene geometrías inválidas o
  no se encuentra en la ruta especificada?
- ¿Cómo afecta la mezcla de resoluciones (10m y 20m) al cálculo de S2REP?
- ¿Qué ocurre si se interrumpe la ejecución a mitad del procesamiento
  (pérdida de conexión, timeout)?

## Requirements

### Functional Requirements

- **FR-001**: El sistema DEBE conectarse al catálogo Earth Search de AWS
  y buscar imágenes Sentinel-2 L2A para abril 2026 dentro del bbox
  delimitado por el shapefile de parcelas.
- **FR-002**: El sistema DEBE cargar las bandas necesarias para el cálculo
  de los 5 índices: red (B4), rededge1 (B5), rededge2 (B6), rededge3 (B7),
  nir (B8), y scl.
- **FR-003**: El sistema DEBE aplicar una máscara SCL que retenga
  exclusivamente píxeles clasificados como Vegetación (clase 4) o
  Suelo desnudo (clase 5), descartando nubes, sombras y otros.
- **FR-004**: El sistema DEBE aplicar una máscara geométrica que recorte
  todas las bandas e índices a los límites de las parcelas definidas en
  el shapefile.
- **FR-005**: El sistema DEBE calcular los siguientes índices para cada
  píxel válido de cada escena:
  - MSAVI2: `(2×NIR + 1 - sqrt((2×NIR+1)² - 8×(NIR-RED))) / 2`
  - S2REP: `705 + 35 × (((B4+B7)/2 - B5) / (B6 - B5))`
  - LAI_RedEdge: `(S2REP - 700) × LAI_factor` (default 0.15)
  - Cab_RedEdge: `(S2REP - 700) × Cab_factor` (default 2)
  - Kc_Actual: `MSAVI2 × kc_slope + kc_intercept` (defaults 1.15, 0.1)
- **FR-006**: El sistema DEBE incluir guardias de estabilidad numérica:
  división por cero en S2REP cuando `|B6-B5| < 0.0001`, y discriminante
  negativo en MSAVI2.
- **FR-007**: El sistema DEBE clipiar cada índice a su rango fisiológico
  antes de exportar: S2REP ∈ [705, 740], MSAVI2 ∈ [0, 1],
  LAI ∈ [0.1, 6.0], Cab ∈ [0, 100], Kc ∈ [0.2, 1.3].
- **FR-008**: El sistema DEBE exportar cada índice a su propia carpeta
  con estructura: `output/Imagenes/{Indice}/Abril2026/{PNG,TIF}`.
- **FR-009**: El sistema DEBE generar un archivo PNG por índice por escena
  utilizando el colormap y rango específico para cada índice.
- **FR-010**: El sistema DEBE generar un archivo GeoTIFF (float32, LZW,
  CRS EPSG:4326) por índice por escena.
- **FR-011**: El sistema DEBE generar un archivo CSV por carpeta de índice
  con estadísticas parcelarias: media, desviación estándar y cantidad de
  píxeles válidos por parcela por escena.
- **FR-012**: El sistema DEBE etiquetar cada escena en el nombre del
  archivo como Despejada (eo:cloud_cover < 10%), Nublada (≥ 10%) o
  SinDatos (todos los píxeles NaN), sin filtrar ninguna escena.
- **FR-013**: El sistema DEBE detectar archivos existentes antes de
  exportar y saltar escenas ya procesadas para evitar duplicados.
- **FR-014**: El sistema DEBE incluir parámetros configurables al inicio
  del script: LAI_factor, Cab_factor, kc_slope, kc_intercept,
  ruta del shapefile, fechas de inicio y fin.
- **FR-015**: El sistema DEBE auto-detectar si se ejecuta en Google Colab
  o en entorno local, montando Drive en Colab o usando rutas locales.

### Key Entities

- **Parcela**: Unidad experimental de 0.5 ha delimitada por geometría
  vectorial. Existen 4 parcelas. Cultivo: Mandarina Murcott.
- **Escena**: Imagen satelital individual (tile Sentinel-2 L2A) que
  intersecta el área de estudio en una fecha y hora específicas.
- **Índice Espectral**: Variable derivada de combinaciones de bandas
  espectrales. Incluye MSAVI2, S2REP, LAI_RedEdge, Cab_RedEdge, Kc_Actual.
  Cada índice tiene su propio rango fisiológico y colormap.
- **Registro Estadístico**: Fila en el CSV por índice que contiene:
  media, desviación estándar y conteo de píxeles válidos para una
  parcela en una escena específica.

## Success Criteria

### Measurable Outcomes

- **SC-001**: El script procesa todas las escenas disponibles de abril 2026
  sin errores fatales, generando al menos un archivo TIF y PNG por escena
  e índice donde haya píxeles válidos.
- **SC-002**: El 100% de los archivos GeoTIFF exportados tienen CRS
  definido (EPSG:4326), 1 banda, y tipo de dato float32.
- **SC-003**: El 100% de los valores de S2REP_mean en los CSV están dentro
  del rango [705, 740] nm (rangos fisiológicos para cítricos).
- **SC-004**: El 100% de los valores de MSAVI2_mean en los CSV están dentro
  del rango [0, 1] (rangos fisiológicos con clip aplicado).
- **SC-005**: Ejecutar el script dos veces consecutivas produce exactamente
  la misma cantidad de archivos en todas las carpetas (detección de
  duplicados funcional).
- **SC-006**: Cada CSV de estadísticas contiene exactamente 10 columnas
  con los nombres especificados y sin valores faltantes en las columnas
  de identificación (fecha, hora, id_escena).

## Assumptions

- Las 4 parcelas están correctamente delimitadas en el shapefile y sus
  geometrías son válidas.
- El catálogo Earth Search de AWS tiene cobertura completa para abril 2026
  sobre la región de Jujuy, Argentina.
- Los coeficientes de los modelos de estimación (LAI_factor=0.15,
  Cab_factor=2, kc_slope=1.15, kc_intercept=0.1) son valores empíricos
  iniciales, sujetos a calibración futura con datos de campo.
- La resolución espacial de 10m para todos los índices es aceptable
  (bandas de 20m se upsampean). Esto puede introducir artefactos menores
  en S2REP pero es consistente con la resolución de las bandas ópticas.
- El usuario tiene acceso al shapefile `4ParcelasDefinidas.zip` en la
  raíz del proyecto o en Google Drive.
- No se requiere Cloud Score+ (no disponible en STAC). El filtro SCL
  es suficiente para parcelas pequeñas.
- El ancho de banda de internet es suficiente para descargar las escenas
  de abril 2026 (~10-20 escenas, ~100 MB cada una en formato comprimido).
- Los archivos existentes no se sobrescriben; si se necesita reprocesar,
  se deben eliminar manualmente los archivos previos o modificar la
  ruta de salida.
