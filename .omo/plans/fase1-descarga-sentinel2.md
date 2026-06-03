# Fase 1 — Descarga Sentinel-2 Mandarina Murcott (Abril 2025 + 2026)

## TL;DR

> **Quick Summary**: Crear un notebook de Google Colab (Python + STAC) que descargue imágenes Sentinel-2 L2A en color natural (B2, B3, B4) para los meses de abril 2025 y abril 2026, usando un shapefile como ROI. El notebook contará imágenes por fecha, identificará cobertura de nubes, visualizará los resultados en RGB y exportará a PNG + GeoTIFF.
>
> **Deliverables**:
> - `Fase1_Descarga_Mandarina.ipynb` — Notebook Colab completo
> - Reporte TXT con conteo de imágenes por fecha
> - PNGs visuales por cada fecha disponible
> - GeoTIFFs con datos crudos por cada fecha
>
> **Estimated Effort**: Medium (~3-4 horas de ejecución)
> **Parallel Execution**: NO — las tareas son secuenciales (un solo notebook, celdas ordenadas)

---

## Context

### Original Request
El usuario necesita la **Fase 1** de un análisis de imágenes satelitales para cultivo de mandarina Murcott. La metodología general tiene 3 fases (según transcripción de reunión):
- **Fase 1** (esta): Descargar imágenes, contar por fecha, visualizar en bruto, exportar
- **Fase 2**: Aplicar filtro de nubes (Cloud Score+ / SCL) e interpolación
- **Fase 3**: Comparar resultados con/sin filtro

### Interview Summary
**Key Discussions**:
- Se usará el enfoque STAC (Python, no GEE) — copiando estructura de `Ejemplo_AedesAegyptis.ipynb`
- ROI: shapefile subido a Google Drive por el usuario
- Bandas: solo **B2 (Blue), B3 (Green), B4 (Red)** — color natural RGB
- Mes: **abril 2025 y abril 2026**
- Formato de salida: **PNG** (visual) + **GeoTIFF** (datos)
- Filtro de nubes e interpolación van en Fase 2 (excluidos aquí)

**Research Findings**:
- `Ejemplo_AedesAegyptis.ipynb`: usa `pystac-client` + `stackstac` + `odc-stac` con catálogo Earth Search AWS
- El ejemplo usa bbox manual; para shapefile se usará `geopandas.read_file()` desde Drive montado
- `Codigo.md`: usa GEE JavaScript (enfoque diferente, no se usará aquí)

---

## Work Objectives

### Core Objective
Crear un notebook Colab funcional que descargue, visualice y exporte imágenes Sentinel-2 en color natural para el área de estudio durante los abriles de 2025 y 2026.

### Concrete Deliverables
- [ ] `Fase1_Descarga_Mandarina.ipynb` — Notebook Python listo para ejecutar en Colab
- [ ] Reporte TXT de imágenes disponibles por fecha
- [ ] PNGs por fecha (color natural)
- [ ] GeoTIFFs por fecha (3 bandas: R, G, B)

### Must Have
- El notebook debe poder ejecutarse completo sin errores en Google Colab
- Debe montar Google Drive y leer el shapefile como ROI
- Debe buscar imágenes en el catálogo Earth Search (sentinel-2-l2a)
- Debe contar y reportar imágenes por fecha
- Debe mostrar visualmente (matplotlib) cada imagen RGB disponible
- Debe exportar a PNG y GeoTIFF
- Debe filtrar por abril 2025 y abril 2026

### Must NOT Have (Guardrails)
- NO incluir filtro de nubes (Cloud Score+, SCL) — es Fase 2
- NO incluir interpolación temporal — es Fase 2
- NO calcular índices espectrales (NDVI, NDRE, etc.) — es Fase 2
- NO usar GEE JavaScript ni ee.* — todo en Python STAC
- NO hardcodear rutas del shapefile — debe cargarse desde Drive

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed.

### Test Decision
- **Infrastructure exists**: Sí (Python/Colab)
- **Automated tests**: None (el test es ejecutar el notebook completo)
- **Agent QA**: Cada tarea tendrá escenarios de verificación específicos

### QA Policy
- Ejecutar el notebook en Colab (o simular) y verificar:
  - 1️⃣ No errores en celdas de instalación/import
  - 2️⃣ Shapefile se carga correctamente
  - 3️⃣ Consulta STAC devuelve imágenes
  - 4️⃣ Conteo de imágenes por fecha es correcto
  - 5️⃣ Visualización RGB genera figuras
  - 6️⃣ Archivos PNG/GeoTIFF se exportan correctamente

---

## Execution Strategy

Este es un notebook único con celdas secuenciales. Las tareas son la **construcción del notebook** por secciones.

```
Wave 1 (Secuencial — construcción del notebook):
├── Task 1: Celda de instalación + imports + funciones auxiliares
├── Task 2: Celda de carga de shapefile + definición ROI
├── Task 3: Celda de búsqueda STAC + conteo de imágenes
├── Task 4: Celda de carga Data Cube + visualización RGB
├── Task 5: Celda de exportación PNG + GeoTIFF + reporte
├── Task 6: Celda de reporte TXT con resumen

Wave FINAL:
├── F1: Revisión de consistencia del notebook
└── F2: Verificación de ejecución sin errores
```

### Dependency Matrix
- **1**: - → 2, 3 (funciones base)
- **2**: 1 → 3 (necesita shapefile para search)
- **3**: 1, 2 → 4 (necesita items del search)
- **4**: 3 → 5 (necesita data cube)
- **5**: 4 → 6 (necesita rutas de exportación)
- **6**: 5 → F1, F2

---

## TODOs

- [ ] 1. Crear celdas de instalación, imports y funciones auxiliares

  **What to do**:
  - Crear celda 1: `!pip install pystac-client stackstac rioxarray geopandas rasterio odc-stac`
  - Crear celda 2: imports completos (os, geopandas, pystac_client, stackstac, pandas, rioxarray, numpy, odc.stac, xarray, glob, rasterio, matplotlib, google.colab.drive)
  - Crear celda 3: montar Google Drive (`drive.mount('/content/drive')`)
  - Copiar la función `tif_to_png_batch()` desde `Ejemplo_AedesAegyptis.ipynb` (conversión TIF → PNG con matplotlib)
  - Agregar función `rgb_to_png()` que tome un array (bands, h, w) y genere PNG en color natural

  **Must NOT do**:
  - No incluir imports de librerías GEE

  **References**:
  - `Ejemplo_AedesAegyptis.ipynb:lines 20-55` — Patrón de imports y montaje Drive
  - `Ejemplo_AedesAegyptis.ipynb:lines 78-108` — Función tif_to_png_batch

  **Acceptance Criteria**:
  - [ ] Celdas creadas en el notebook con código funcional
  - [ ] imports no tienen errores de sintaxis
  - [ ] La estructura JSON del .ipynb es válida

  **QA Scenarios**:
  ```
  Scenario: Verificar estructura del notebook
    Tool: Bash (python -c "import json; json.load(open('...'))")
    Steps:
      1. Validar que el archivo .ipynb es JSON válido
      2. Contar que tiene al menos 5 celdas
      3. Verificar que las celdas contienen los imports requeridos
    Expected Result: Notebook válido, imports presentes

  Scenario: Verificar sintaxis de imports
    Tool: Bash (python -c "compile(open('cell_source.txt').read(), '<test>', 'exec')")
    Steps:
      1. Extraer el source de cada celda
      2. Compilar con Python para verificar sintaxis
    Expected Result: Sin errores de sintaxis
  ```

  **Evidence to Capture**:
  - [ ] `task-1-notebook-valid.json` — output de validación JSON
  - [ ] `task-1-syntax-check.txt` — resultado de verificación sintáctica

  **Commit**: YES
  - Message: `feat(colab): crear notebook Fase1 con imports y funciones auxiliares`
  - Files: `Fase1_Descarga_Mandarina.ipynb`

---

- [ ] 2. Crear celda de carga de shapefile y definición del ROI

  **What to do**:
  - Crear celda que cargue el shapefile desde Drive usando geopandas
  - Ruta esperada: `/content/drive/MyDrive/{ruta_del_usuario}/` (dejar como variable)
  - Convertir el shapefile a bounding box `[minx, miny, maxx, maxy]` para la consulta STAC
  - Definir fechas: `datetime="2025-04-01/2025-04-30"` y `"2026-04-01/2026-04-30"`
  - Mostrar información del shapefile cargado (columnas, CRS, cantidad de features)
  - Imprimir el bbox resultante para confirmación visual

  **Must NOT do**:
  - No hardcodear rutas absolutas del shapefile
  - No modificar el shapefile original

  **References**:
  - `Ejemplo_AedesAegyptis.ipynb:lines 119-120` — Patrón de bbox manual
  - Documentación geopandas: `read_file()`

  **Acceptance Criteria**:
  - [ ] Celda carga shapefile correctamente
  - [ ] Extrae bbox del shapefile
  - [ ] Muestra información del shapefile en output

  **QA Scenarios**:
  ```
  Scenario: Verificar lógica de carga de shapefile
    Tool: Bash (python -c "import geopandas; ...")
    Preconditions: Shapefile de prueba disponible
    Steps:
      1. Ejecutar código de carga de shapefile
      2. Verificar que gdf no está vacío
      3. Verificar que bbox tiene 4 coordenadas
    Expected Result: Shapefile cargado, bbox calculado
  ```

  **Evidence to Capture**:
  - [ ] `task-2-shapefile-info.txt`

  **Commit**: YES (groups with 1)
  - Message: `feat(colab): agregar carga de shapefile y cálculo de bbox`
  - Files: `Fase1_Descarga_Mandarina.ipynb`

---

- [ ] 3. Crear celda de búsqueda STAC y conteo de imágenes

  **What to do**:
  - Crear celda que se conecte al catálogo Earth Search: `Client.open("https://earth-search.aws.element84.com/v1")`
  - Buscar colección `sentinel-2-l2a`
  - Usar el bbox calculado del Task 2
  - Fechas: loop sobre 2025-04 y 2026-04 (o dos searches separados)
  - Filtro: sin filtro de nubes (queremos VER las nubes, no ocultarlas)
  - Contar imágenes por fecha usando `Counter`
  - Mostrar tabla: fecha | cantidad de imágenes | cobertura de nubes promedio
  - Extraer metadato `eo:cloud_cover` de cada item para identificar imágenes nubladas vs claras
  - Clasificar cada imagen: "Despejada" (cloud_cover < 20%), "Parcial" (20-60%), "Nublada" (>60%)
  - Imprimir resumen visual con colores

  **Must NOT do**:
  - No filtrar por cloud_cover (queremos ver todo)
  - No limitar resultados (queremos todas las imágenes disponibles)

  **References**:
  - `Ejemplo_AedesAegyptis.ipynb:lines 122-162` — Patrón de búsqueda STAC y conteo
  - Documentación pystac-client: `catalog.search()`

  **Acceptance Criteria**:
  - [ ] Conexión exitosa al catálogo Earth Search
  - [ ] Resultados devueltos para ambas fechas (2025 y 2026)
  - [ ] Conteo por fecha correctamente calculado
  - [ ] Clasificación de nubes (despejada/parcial/nublada) por imagen

  **QA Scenarios**:
  ```
  Scenario: Verificar búsqueda STAC
    Tool: Bash (python -c "from pystac_client import Client; ...")
    Preconditions: Conexión a internet
    Steps:
      1. Conectar al catálogo
      2. Buscar con bbox y fechas de prueba
      3. Verificar que items no está vacío
    Expected Result: Items encontrados, conteo > 0
  ```

  **Evidence to Capture**:
  - [ ] `task-3-stac-results.txt` — muestra de items encontrados

  **Commit**: YES (groups with 1, 2)
  - Message: `feat(colab): agregar búsqueda STAC y conteo de imágenes`
  - Files: `Fase1_Descarga_Mandarina.ipynb`

---

- [ ] 4. Crear celda de carga Data Cube y visualización RGB

  **What to do**:
  - Usar `odc.stac.load()` para cargar las imágenes como Data Cube
  - Bandas: solo `["blue", "green", "red"]` (B2, B3, B4)
  - CRS: `EPSG:4326`, resolución: `0.0001` (aproximadamente 10m)
  - `groupby="solar_day"` para agrupar por día
  - `chunks={'time': 1, 'x': 512, 'y': 512}` para no saturar RAM
  - Normalizar bandas dividiendo por 10000 (Sentinel-2 L2A viene escalado)
  - Para cada fecha, crear visualización RGB usando matplotlib:
    - Mostrar en una cuadrícula (grid) de imágenes por fecha
    - Título con fecha y clasificación de nubes
    - Usar `imshow()` con los canales R, G, B en orden correcto
  - Manejar casos donde no hay datos para una fecha

  **Must NOT do**:
  - No calcular índices (solo mostrar RGB)
  - No aplicar máscaras de nubes

  **References**:
  - `Ejemplo_AedesAegyptis.ipynb:lines 173-188` — Patrón de load() con odc-stac
  - Documentación odc-stac: `load()` parámetros

  **Acceptance Criteria**:
  - [ ] Data Cube cargado sin errores
  - [ ] Visualización RGB genera figuras por fecha
  - [ ] Las imágenes se ven en color natural (no falsos colores)
  - [ ] La cuadrícula es legible (no más de 6 imágenes por fila)

  **QA Scenarios**:
  ```
  Scenario: Verificar visualización RGB
    Tool: Bash (python -c "import matplotlib.pyplot as plt; ...")
    Steps:
      1. Ejecutar celda de visualización
      2. Verificar que se generan figuras matplotlib
      3. Verificar que el orden de canales es RGB (no BGR)
    Expected Result: Figuras generadas, color natural correcto
  ```

  **Evidence to Capture**:
  - [ ] `task-4-rgb-preview.png` — screenshot de la visualización

  **Commit**: YES (groups with 1, 2, 3)
  - Message: `feat(colab): agregar carga Data Cube y visualización RGB`
  - Files: `Fase1_Descarga_Mandarina.ipynb`

---

- [ ] 5. Crear celda de exportación PNG + GeoTIFF

  **What to do**:
  - Para cada fecha con datos:
    - Crear carpeta de salida: `{base_dir}/PNG/` y `{base_dir}/GeoTIFF/`
    - Exportar GeoTIFF: usar `rioxarray` para guardar el Data Cube como GeoTIFF con 3 bandas (R, G, B) y CRS original
    - Exportar PNG: usar `tif_to_png_batch()` O crear una función que convierta el array RGB a PNG con matplotlib
    - Nombrar archivos como: `Mandarina_2025-04-15_RGB.tif` y `Mandarina_2025-04-15_RGB.png`
    - Mostrar progreso: "✅ Exportado: Mandarina_2025-04-15 (PNG + GeoTIFF)"

  **Must NOT do**:
  - No modificar los valores de píxeles (exportar datos crudos)
  - No comprimir GeoTIFF con pérdida

  **References**:
  - `Ejemplo_AedesAegyptis.ipynb:lines 78-108` — Función tif_to_png_batch
  - Documentación rioxarray: `to_raster()`

  **Acceptance Criteria**:
  - [ ] Archivos PNG generados por fecha
  - [ ] Archivos GeoTIFF generados por fecha
  - [ ] GeoTIFF tiene 3 bandas (R, G, B) con CRS correcto
  - [ ] PNG se ve visualmente correcto (color natural)

  **QA Scenarios**:
  ```
  Scenario: Verificar exportación GeoTIFF
    Tool: Bash (python -c "import rasterio; ...")
    Steps:
      1. Abrir GeoTIFF exportado con rasterio
      2. Verificar count=3 bandas
      3. Verificar CRS no es None
      4. Verificar shape coincide con lo esperado
    Expected Result: GeoTIFF válido con 3 bandas y CRS

  Scenario: Verificar exportación PNG
    Tool: Bash (python -c "from PIL import Image; ...")
    Steps:
      1. Abrir PNG exportado
      2. Verificar que es una imagen RGB válida
    Expected Result: PNG válido
  ```

  **Evidence to Capture**:
  - [ ] `task-5-export-results.txt` — lista de archivos exportados
  - [ ] `task-5-sample-geotiff-info.txt` — info de un GeoTIFF

  **Commit**: YES (groups with 1,2,3,4)
  - Message: `feat(colab): agregar exportación PNG y GeoTIFF`
  - Files: `Fase1_Descarga_Mandarina.ipynb`

---

- [ ] 6. Crear celda de reporte TXT

  **What to do**:
  - Generar archivo `Reporte_Fase1_Abril.txt`
  - Estructura del reporte:
    ```
    ============================================
       FASE 1 — REPORTE DE IMÁGENES SENTINEL-2
       Mandarina Murcott — Abril 2025 y 2026
    ============================================

    📅 Abril 2025:
      - 2025-04-02: 1 imagen [Nublada 35%]
      - 2025-04-07: 1 imagen [Parcial 22%]
      - 2025-04-12: 1 imagen [Despejada 5%]
      Total: 5 imágenes

    📅 Abril 2026:
      - 2026-04-01: 1 imagen [Despejada 8%]
      ...
      Total: 4 imágenes

    ============================================
    ARCHIVOS EXPORTADOS:
      PNG:  9 archivos en {ruta}
      GeoTIFF: 9 archivos en {ruta}
    ============================================
    ```
  - Guardar en Drive junto a las imágenes

  **Acceptance Criteria**:
  - [ ] Reporte TXT creado
  - [ ] Contiene conteo por fecha
  - [ ] Contiene clasificación de nubes
  - [ ] Contiene resumen de archivos exportados

  **QA Scenarios**:
  ```
  Scenario: Verificar reporte TXT
    Tool: Bash (Get-Content ...)
    Steps:
      1. Leer el archivo TXT
      2. Verificar que contiene "FASE 1"
      3. Verificar que contiene "Abril 2025" y "Abril 2026"
      4. Verificar que contiene "Total:"
    Expected Result: Reporte completo y formateado
  ```

  **Evidence to Capture**:
  - [ ] `task-6-reporte.txt` — contenido del reporte

  **Commit**: YES (groups with 1,2,3,4,5)
  - Message: `feat(colab): agregar generación de reporte TXT`
  - Files: `Fase1_Descarga_Mandarina.ipynb`

---

- [ ] 7. **Fix: soporte para .zip en shapefile**

  **What to do**:
  - El shapefile en realidad es un conjunto de archivos (.shp, .shx, .dbf, .prj) que suelen venir comprimidos en .zip
  - `geopandas.read_file()` puede leer .zip directamente
  - Modificar **Celda 5** (config): actualizar comentario para indicar que acepta .shp o .zip
  - Modificar **Celda 6** (carga): detectar si la ruta termina en .zip → usar `gpd.read_file()` directo (geopandas lo maneja)
  - Si termina en .shp → comportamiento actual
  - Verificar que la función `zipfile` o el lector directo de geopandas funciona sin errores

  **Must NOT do**:
  - No descomprimir archivos temporales (geopandas lee zip inline)
  - No cambiar las rutas de salida

  **References**:
  - Documentación geopandas: soporta .zip nativamente desde v0.8+
  - Shapefile en GEE se exporta como .zip con múltiples archivos internos

  **Acceptance Criteria**:
  - [ ] Celda 5 comentario actualizado: menciona .shp y .zip
  - [ ] Celda 6: `gpd.read_file()` funciona con ruta .zip
  - [ ] Carga del shapefile funciona igual para .shp y .zip

  **QA Scenarios**:
  ```
  Scenario: Probar con .zip simulado
    Tool: Bash
    Steps:
      1. Extraer source de la celda 6
      2. Verificar que la línea `gpd.read_file(SHAPEFILE_PATH)` se ejecuta sin condicionales extra
      3 (geopandas ya maneja .zip nativamente)
    Expected Result: Sin errores, mismo comportamiento para .shp y .zip
  ```

  **Evidence to Capture**:
  - [ ] `task-7-zip-support.txt`

  **Commit**: YES (groups with 1-6)
  - Message: `fix(colab): soporte para shapefile .zip en Celda 5 y 6`
  - Files: `Fase1_Descarga_Mandarina.ipynb`

---

## Final Verification Wave

- [ ] F1. **Consistencia del Notebook** — `unspecified-high`
  Leer el notebook completo. Verificar:
  - El flujo de celdas es lógico (instalación → imports → shapefile → search → carga → visualización → exportación → reporte)
  - Nombres de variables consistentes entre celdas
  - No hay código muerto o comentado
  - Todas las rutas usan variables, no strings hardcodeados
  - Output: `Estructura [OK/ISSUES] | Variables [OK/ISSUES] | VERDICT`

- [ ] F2. **Verificación de ejecución simulada** — `unspecified-high`
  Extraer el source de cada celda. Verificar:
  - `compile()` de Python pasa en todas las celdas
  - No hay `import` duplicados
  - No hay referencias a variables no definidas previamente
  - Output: `Compilación [N/N PASS] | Dependencias [OK/ISSUES] | VERDICT`

---

## Commit Strategy

- **1-6**: `feat(colab): crear notebook Fase1 - descarga Sentinel-2 mandarina` + todos los archivos

---

## Success Criteria

### Verification Commands
```bash
python -c "import json; nb = json.load(open('Fase1_Descarga_Mandarina.ipynb')); print(f'Celdas: {len(nb[\"cells\"])}')"
# Expected: Celdas: >= 6

python -c "
import json
nb = json.load(open('Fase1_Descarga_Mandarina.ipynb'))
sources = [''.join(c['source']) for c in nb['cells'] if c['cell_type'] == 'code']
for i, src in enumerate(sources):
    compile(src, f'cell_{i}', 'exec')
print('Todas las celdas compilan OK')
"
# Expected: Todas las celdas compilan OK
```

### Final Checklist
- [ ] Notebook creado: `Fase1_Descarga_Mandarina.ipynb`
- [ ] 6+ celdas de código funcionales
- [ ] Flujo completo: import → shapefile → STAC → RGB → exportación → reporte
- [ ] Sin errores de sintaxis en ninguna celda
- [ ] Variables consistentes entre celdas
- [ ] Sin hardcodeo de rutas de shapefile
- [ ] Listo para ejecutar en Google Colab
