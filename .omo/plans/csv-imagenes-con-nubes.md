# Plan: Nuevo CSV Individual con Validación de Nubes

## TL;DR

> **Quick Summary**: Reemplazar la exportación de imágenes individuales perdida con una nueva que incluya TODAS las imágenes Sentinel-2 (incluso las nubladas) agregue columnas de validación de nubes y deje celdas vacías donde no haya datos válidos.
>
> **Deliverables**:
> - Bloque nuevo de código en `codigo_gee.js` (~60 líneas)
> - Export opcional: se puede habilitar/deshabilitar la vieja exportación
>
> **Estimated Effort**: Short (un bloque de código en un archivo)
> **Parallel Execution**: NO (tarea secuencial)
> **Critical Path**: Análisis → implementación → verificación

---

## Context

### Original Request
El usuario quiere que el CSV de imágenes individuales:
1. Incluya TODAS las imágenes, incluso las nubladas (no solo las que pasan el filtro)
2. Si una parcela está completamente nublada, deje las celdas de métricas VACÍAS (null), no elimine la fila
3. Agregue columnas que expliquen el estado de nubosidad (claro, parcial, nublado, porcentajes)

### Current State
`codigo_gee.js` actualmente tiene:
- `s2Vinculada` (línea 30-32): colección RAW con CS+ vinculada, SIN filtro de nubes
- `enmascararNubesDobleFiltro()` (línea 34-42): aplica CS+ >= 0.9 + SCL (4,5)
- `calcularMetricas()` (línea 48-89): calcula NDRE, NDVI, S2REP, LAI, Cab, MSAVI2, Kc
- `coleccionProcesada` (línea 91-93): imágenes filtradas + métricas
- **No hay exportación de imágenes individuales** en este momento (fue revertida)

### Metis Review
N/A — Plan pequeño y directo

---

## Work Objectives

### Core Objective
Agregar un nuevo bloque de exportación CSV que procese `s2Vinculada` (todas las imágenes, sin filtrar), aplique el filtro de nubes solo para las métricas (dejando null donde haya nubes) pero calcule estadísticas de nubosidad sobre los datos originales (sin máscara) para las columnas de validación.

### Concrete Deliverables
- Bloque nuevo de código agregado a `codigo_gee.js` (después de la sección 7, antes del print final)

### Must Have
- Una fila por parcela por imagen, INCLUSO si la imagen está completamente nublada
- Valores de métricas (NDRE, NDVI, S2REP, LAI, Cab, MSAVI2, Kc) null cuando la parcela está nublada
- Columnas de validación:
  - `Pixeles_Claros`: cantidad de píxeles no enmascarados (NDRE_count)
  - `Pixeles_Totales`: cantidad total de píxeles en la parcela
  - `Pixeles_Nublados`: Pixeles_Totales - Pixeles_Claros
  - `Porcentaje_Claros`: (Claros / Totales) × 100
  - `Estado_Nubosidad`: "Despejado" (≥70%), "Parcialmente Nublado" (30-70%), "Muy Nublado" (<30%)
  - `Cloud_Score_Medio`: promedio de cs_cdf en la parcela (0=nube, 1=despejado)

### Must NOT Have
- NO modificar el CSV semanal existente (`Dataset_Fenologico_Mandarina_Estandarizado`)
- NO modificar la lógica de procesamiento existente (flag interpolación, S-G, etc.)
- NO eliminar filas por nubosidad (mantener todo)
- NO usar la app_visualizador_ndre.js

---

## Verification Strategy
> Verificación manual en GEE Code Editor

- Correr el script, verificar que aparece la nueva tarea de exportación
- Exportar el CSV y verificar:
  - Columnas correctas
  - Filas con nubes tienen métricas null pero columnas de nubosidad llenas
  - Filas despejadas tienen métricas con valores
  - Sin errores de sintaxis

---

## Execution Strategy

Wave único: tarea única secuencial

```
Wave 1:
├── Task 1: Agregar nuevo bloque de export CSV a codigo_gee.js
```

---

## TODOs

- [ ] 1. Agregar nuevo bloque de exportación CSV con validación de nubes

  **What to do**:
  - Agregar un nuevo bloque de código ANTES del print final de `codigo_gee.js` (sección 8, validación)
  - Crear una función (o bloque inline) que procese `s2Vinculada` imagen por imagen:
    1. Para cada imagen en `s2Vinculada`, tomar la imagen original (con banda `cs_cdf`)
    2. Calcular métricas USANDO el filtro de nubes (imagen enmascarada) → métricas null donde hay nubes
    3. Mantener la banda `cs_cdf` original (sin enmascarar) para estadísticas de nubosidad
    4. Usar `reduceRegions` con `ee.Reducer.mean().combine(ee.Reducer.count())` para obtener:
       - Mean de cada métrica (null si todo enmascarado)
       - Count de píxeles usados para cada métrica
       - Mean y count de `cs_cdf` (siempre válidos, porque cs_cdf no está enmascarado)
    5. Para cada feature, calcular:
       - `Pixeles_Claros` = NDRE_count
       - `Pixeles_Totales` = cs_cdf_count (de la banda sin máscara)
       - `Pixeles_Nublados` = total - claros
       - `Porcentaje_Claros` = (claros / totales) × 100
       - `Estado_Nubosidad`: "Despejado", "Parcialmente Nublado", o "Muy Nublado"
       - `Cloud_Score_Medio` = cs_cdf_mean
    6. Exportar como CSV con `Export.table.toDrive`

  **Columnas del CSV**:
  ```
  Fecha, ID_Parcela, NDVI, NDRE, S2REP, LAI_RedEdge, Cab_RedEdge, MSAVI2, Kc_Actual,
  Pixeles_Claros, Pixeles_Totales, Pixeles_Nublados, Porcentaje_Claros, Estado_Nubosidad, Cloud_Score_Medio
  ```

  **Código base**:
  ```javascript
  // ==============================================================================
  // 8. EXPORTACIÓN CSV: TODAS LAS IMÁGENES CON VALIDACIÓN DE NUBES
  // ==============================================================================
  // Incluye TODAS las imágenes (incluso nubladas). Las métricas son null
  // donde hay nubes. Las columnas de nubosidad explican el estado.
  var csvCompleto = ee.FeatureCollection(
    s2Vinculada.map(function(img) {
      var fecha = ee.Date(img.get('system:time_start'));
      var cloudCover = ee.Number(img.get('CLOUDY_PIXEL_PERCENTAGE'));
      
      // Aplicar máscara de nubes para métricas
      var imgMasked = enmascararNubesDobleFiltro(img);
      
      // Calcular métricas sobre la imagen enmascarada (null donde hay nubes)
      var imgConMetricas = calcularMetricas(imgMasked);
      
      // Agregar cs_cdf original (sin máscara) para estadísticas de nubosidad
      imgConMetricas = imgConMetricas.addBands(
        img.select('cs_cdf').rename('cs_cdf_raw')
      );
      
      // Reducción por parcela: mean + count
      var stats = imgConMetricas.reduceRegions({
        collection: parcelas,
        reducer: ee.Reducer.mean().combine({
          reducer2: ee.Reducer.count(),
          sharedInputs: true
        }),
        scale: 10
      });
      
      return stats.map(function(f) {
        var pixClaros = ee.Number(f.get('NDRE_count'));
        var pixTotales = ee.Number(f.get('cs_cdf_raw_count'));
        var pixNublados = pixTotales.subtract(pixClaros);
        var porcClaros = pixTotales.gt(0).multiply(
          pixClaros.divide(pixTotales).multiply(100)
        );
        
        var estado = ee.Algorithms.If(
          porcClaros.gte(70), 'Despejado',
          ee.Algorithms.If(porcClaros.gte(30), 'Parcialmente Nublado', 'Muy Nublado')
        );
        
        return ee.Feature(null, {
          'Fecha': fecha.format('YYYY-MM-dd'),
          'ID_Parcela': f.get('name'),
          'NDVI': f.get('NDVI_Mask_mean'),
          'NDRE': f.get('NDRE_mean'),
          'S2REP': f.get('S2REP_mean'),
          'LAI_RedEdge': f.get('LAI_RedEdge_mean'),
          'Cab_RedEdge': f.get('Cab_RedEdge_mean'),
          'MSAVI2': f.get('MSAVI2_mean'),
          'Kc_Actual': f.get('Kc_Actual_mean'),
          'Pixeles_Claros': pixClaros,
          'Pixeles_Totales': pixTotales,
          'Pixeles_Nublados': pixNublados,
          'Porcentaje_Claros': porcClaros,
          'Estado_Nubosidad': estado,
          'Cloud_Score_Medio': f.get('cs_cdf_raw_mean')
        });
      });
    })
  ).flatten();
  
  Export.table.toDrive({
    collection: csvCompleto,
    description: 'Dataset_Imagenes_Individuales_Con_Nubes',
    folder: 'Tesis_Mandarinas',
    fileFormat: 'CSV',
    selectors: [
      'Fecha', 'ID_Parcela',
      'NDVI', 'NDRE', 'S2REP', 'LAI_RedEdge', 'Cab_RedEdge', 'MSAVI2', 'Kc_Actual',
      'Pixeles_Claros', 'Pixeles_Totales', 'Pixeles_Nublados', 'Porcentaje_Claros',
      'Estado_Nubosidad', 'Cloud_Score_Medio'
    ]
  });
  ```

  **AVISO**: El código base usa `sharedInputs: true` en el combiner de reducers.
  Esto es importante porque permite que mean y count compartan la misma entrada
  (imagen). Sin esto, GEE puede dar error de incompatibilidad de reducers.

  **Posible problema con `calcularMetricas`**: Esta función selecciona bandas
  B4-B8. Si la imagen está enmascarada (updateMask), las bandas seleccionadas
  conservan la máscara. PERO `calcularMetricas` también puede recibir imágenes
  sin enmascarar. Si queremos métricas solo sobre píxeles claros, debemos pasarle
  la imagen enmascarada. Si queremos métricas raw (sin filtrar), pasar la raw.
  En este plan, se pasa la enmascarada para que métricas = null en nubes.

  **Edge case**: Si `s2Vinculada` no tiene la banda `cs_cdf` por algún error de
  `linkCollection`, la reducción fallará. Agregar guard condicional o confiar en
  que linkCollection ya está validado en el script principal.

  **Must NOT do**:
  - NO eliminar la fila si todos los valores son null (el CSV debe mantenerla)
  - NO modificar las funciones existentes `enmascararNubesDobleFiltro`, `calcularMetricas`
  - NO tocar el CSV semanal existente ni el video ni los hitos fenológicos
  - NO modificar `parcelas`, `startDate`, `endDate`

  **Acceptance Criteria**:

  ```
  Scenario: CSV exportación con nubes
    Preconditions: Script corre sin errores
    Steps:
      1. Verificar que aparece la tarea "Dataset_Imagenes_Individuales_Con_Nubes"
      2. Exportar el CSV
      3. Abrir el CSV
    Expected:
      - Columnas: Fecha, ID_Parcela, NDVI, NDRE, S2REP, LAI_RedEdge, Cab_RedEdge,
        MSAVI2, Kc_Actual, Pixeles_Claros, Pixeles_Totales, Pixeles_Nublados,
        Porcentaje_Claros, Estado_Nubosidad, Cloud_Score_Medio
      - Filas con nubes: NDRE vacío/null, pero Pixeles_Nublados > 0 y
        Estado_Nubosidad = "Muy Nublado" o "Parcialmente Nublado"
      - Filas despejadas: NDRE con valor numérico, Pixeles_Claros > 0,
        Estado_Nubosidad = "Despejado"
      - Todas las imágenes de s2Vinculada están representadas (una fila por parcela
        por imagen, no hay imágenes faltantes)
  ```

  **Commit**: YES
  - Message: `feat(csv): nuevo CSV individual con validación de nubes (todas las imágenes)`
  - Files: `codigo_gee.js`
  - Pre-commit: verificar sintaxis con python o GEE

---

## Final Verification Wave

- [ ] F1. **Plan Compliance** — Verificar que el nuevo bloque existe en codigo_gee.js y que NO modifica nada existente
- [ ] F2. **Code Review** — Revisar: ¿usa `sharedInputs: true`? ¿el combiner es correcto? ¿las columnas de salida son las correctas?
- [ ] F3. **QA** — Correr el script en GEE Code Editor, verificar tarea, exportar CSV parcial y revisar columnas

---

## Commit Strategy

- **Commit único**: `feat(csv): nuevo CSV individual con validación de nubes (todas las imágenes)`
