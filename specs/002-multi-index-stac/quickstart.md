# Quickstart: Multi-Índices STAC Abril 2026

## Prerequisites

1. Python 3.10+ instalado
2. Shapefile `4ParcelasDefinidas.zip` en la raíz del proyecto
3. Conexión a internet (para descargar imágenes del catálogo Earth Search)

## Cómo Ejecutar

### Opción 1: Local (Windows/Linux/Mac)

```bash
python multi_indices_abril2026.py
```

El script:
1. Detecta automáticamente que es entorno local
2. Instala dependencias faltantes
3. Busca imágenes Sentinel-2 para abril 2026
4. Procesa cada escena y exporta índices

### Opción 2: Google Colab

Subir `multi_indices_abril2026.py` a Colab y ejecutar, o copiar el contenido
a una celda. El auto-detectará Colab y montará Google Drive.

## Configuración

Editar estas variables al inicio del script:

| Parámetro | Default | Descripción |
|-----------|---------|-------------|
| `PERIODO_INICIO` | `"2026-04-01"` | Inicio del período |
| `PERIODO_FIN` | `"2026-04-30"` | Fin del período |
| `LAI_factor` | `0.15` | Factor de conversión S2REP→LAI |
| `Cab_factor` | `2` | Factor de conversión S2REP→Cab |
| `kc_slope` | `1.15` | Pendiente MSAVI2→Kc |
| `kc_intercept` | `0.1` | Intercepto MSAVI2→Kc |
| `UMBRAL_NUBES` | `10` | % para etiquetar Despejada/Nublada |

## Archivos de Salida

| Directorio | Contenido |
|------------|-----------|
| `output/Imagenes/MSAVI2/Abril2026/PNG/` | Mapas MSAVI2 |
| `output/Imagenes/MSAVI2/Abril2026/TIF/` | GeoTIFFs MSAVI2 |
| `output/Imagenes/S2REP/Abril2026/PNG/` | Mapas S2REP (heatmap) |
| `output/Imagenes/LAI_RedEdge/Abril2026/PNG/` | Mapas LAI (verdes) |
| `output/Imagenes/Cab_RedEdge/Abril2026/PNG/` | Mapas Cab (amarillo-verde) |
| `output/Imagenes/Kc_Actual/Abril2026/PNG/` | Mapas Kc (marrón-verde-azul) |
| Cada carpeta incluye `TIF/` y `estadisticas.csv` | |

## Verificación Rápida

```bash
# Verificar estructura de carpetas
python -c "
import os
for idx in ['MSAVI2','S2REP','LAI_RedEdge','Cab_RedEdge','Kc_Actual']:
    png = os.path.exists(f'output/Imagenes/{idx}/Abril2026/PNG')
    tif = os.path.exists(f'output/Imagenes/{idx}/Abril2026/TIF')
    csv = os.path.exists(f'output/Imagenes/{idx}/Abril2026/estadisticas.csv')
    print(f'{idx}: PNG={png} TIF={tif} CSV={csv}')
"

# Verificar CSV
python -c "
import pandas as pd
df = pd.read_csv('output/Imagenes/MSAVI2/Abril2026/estadisticas.csv')
print(f'Columnas: {list(df.columns)}')
print(f'Filas: {len(df)}')
"
```

## Troubleshooting

- **Sin imágenes**: Verificar que abril 2026 tiene cobertura Sentinel-2 sobre Jujuy
- **Error de memoria**: Reducir BATCH_SIZE en el script
- **Shapefile no encontrado**: Verificar que `4ParcelasDefinidas.zip` está en la raíz
- **Valores NaN en todo**: Posible nubosidad total — verificar estado_nubosidad en CSV
- **Script lento**: Depende del ancho de banda (~100 MB por escena)
