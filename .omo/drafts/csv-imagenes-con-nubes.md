# Draft: CSV Imágenes Individuales con Validación de Nubes

## Requirements (confirmed)
- Usar TODAS las imágenes de Sentinel-2, NO solo las que pasan el filtro de nubes
- Si no hay datos válidos para una parcela (por nubes), dejar la celda VACÍA en el CSV, no eliminar la fila
- Agregar columnas de validación de nubes: estado de nubosidad, porcentaje, etc.

## Current Analysis
El codigo_gee.js actualmente usa `coleccionProcesada` que solo contiene imágenes 
que pasaron el doble filtro (CS+ >= 0.9 + SCL 4/5). El nuevo CSV debe usar 
`s2Vinculada` que es la colección RAW antes del filtro.

`s2Vinculada` tiene:
- Todas las imágenes Sentinel-2 L2A sin filtrar
- La banda extra `cs_cdf` de Cloud Score+ (para validar calidad)
- La banda `SCL` (Scene Classification Layer)

## Technical Challenges
1. `calcularMetricas()` actualmente usa bandas ópticas (B4-B8) pero NO necesita CS+ ni SCL
2. Para el conteo de píxeles claros/nublados, necesitamos aplicar la máscara CS+ al reducir
3. `CLOUDY_PIXEL_PERCENTAGE` está en propiedades de la imagen original
4. Hay que preservar system:time_start para la fecha

## New Columns to Add
- `Pixeles_Claros`: conteo de píxeles con cs_cdf >= 0.90 en la parcela
- `Pixeles_Nublados`: conteo de píxeles con cs_cdf < 0.90 en la parcela
- `Porcentaje_Claros`: Pixeles_Claros / (Pixeles_Claros + Pixeles_Nublados) * 100
- `Estado_Nubosidad`: "Despejado" (>=70%), "Parcialmente Nublado" (30-70%), "Muy Nublado" (<30%)
- `Cloud_Cover_Property`: CLOUDY_PIXEL_PERCENTAGE de la propiedad de la imagen
- `Flag_Dato_Valido`: 1 si NDRE no es nulo, 0 si está nulo/completamente nublado

## Scope
- IN: Nuevo bloque de Export en codigo_gee.js, ~50-60 líneas
- IN: Reemplaza la individual images CSV que se perdió
- OUT: No modificar el CSV semanal existente
- OUT: No modificar la app_visualizador_ndre.js
