"""
Pipeline RGB True Color - Exporta compositos RGB a output/rgb/4ParcelasDefinidas/
Misma logica que NDRE: sin filtro de nubes, sufijo Despejada/Nublada/SinDatos.
Cada mes se procesa independientemente.
"""
import os, sys, glob, calendar, json, traceback
import numpy as np
import pandas as pd, geopandas as gpd
import xarray as xr, rioxarray, rasterio
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pystac_client import Client
from odc.stac import load
from rasterio.features import geometry_mask

# ============================================================
# CONFIG
# ============================================================
SCRIPT_DIR = os.getcwd()
SHAPEFILE_PATH = os.path.join(SCRIPT_DIR, '4ParcelasDefinidas.zip')
BASE_DIR = os.path.join(SCRIPT_DIR, 'output', 'rgb', '4ParcelasDefinidas')

PERIODO_INICIO = "2025-01-01"
PERIODO_FIN = "2026-06-03"

os.makedirs(BASE_DIR, exist_ok=True)

MES_NOMBRE = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
               'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

def generar_fechas_por_mes(inicio_str, fin_str):
    inicio = datetime.strptime(inicio_str, '%Y-%m-%d')
    fin = datetime.strptime(fin_str, '%Y-%m-%d')
    fechas = []
    corriente = inicio.replace(day=1)
    while corriente <= fin:
        a, m = corriente.year, corriente.month
        ultimo = calendar.monthrange(a, m)[1]
        fechas.append((
            corriente.strftime('%Y-%m-%d'),
            min(datetime.strptime(f'{a}-{m:02d}-{ultimo}', '%Y-%m-%d'), fin).strftime('%Y-%m-%d'),
            f'{m:02d} - {MES_NOMBRE[m]} {a}'
        ))
        corriente = datetime(a + (1 if m == 12 else 0), 1 if m == 12 else m + 1, 1)
    return fechas

FECHAS = generar_fechas_por_mes(PERIODO_INICIO, PERIODO_FIN)
TOTAL_MESES = len(FECHAS)
print(f"Meses RGB a procesar: {TOTAL_MESES}")
print(f"Periodo: {PERIODO_INICIO} a {PERIODO_FIN}")
print(f"Exportar a: {BASE_DIR}\n")

# ============================================================
# FUNCIONES
# ============================================================
def aplicar_mascara_scl(scl, clases_validas=[4,5]):
    mask = xr.zeros_like(scl, dtype=bool)
    for c in clases_validas:
        mask = mask | (scl == c)
    return mask

def generar_csv_metadatos(registros, path):
    df = pd.DataFrame(registros)
    columnas = ['fecha', 'hora', 'id_escena', 'nubes_porciento', 'estado_nubosidad', 'ruta_png', 'mes_label']
    df = df[[c for c in columnas if c in df.columns]]
    df.to_csv(path, index=False, encoding='utf-8')
    return df

# ============================================================
# CARGAR SHAPEFILE
# ============================================================
print("Cargando shapefile...")
gdf = gpd.read_file(SHAPEFILE_PATH)
gdf_geo = gdf if (gdf.crs and gdf.crs.is_geographic) else gdf.to_crs('EPSG:4326')
bbox = gdf_geo.total_bounds
print(f"Parcelas: {list(gdf['name'])} | BBox: {bbox}\n")

catalog = Client.open('https://earth-search.aws.element84.com/v1')

LOG_PATH = os.path.join(BASE_DIR, '_progreso.json')
progreso = {}
if os.path.exists(LOG_PATH):
    with open(LOG_PATH) as f:
        progreso = json.load(f)

resultados_globales = {}

for mes_idx, (fi, ff, label) in enumerate(FECHAS):
    print(f"\n{'='*60}")
    print(f"  MES {mes_idx+1}/{TOTAL_MESES}: {label} (RGB)")
    print(f"  {fi} -> {ff}")
    print(f"{'='*60}")

    if label in progreso and progreso[label].get('status') == 'ok':
        print(f"  Ya procesado. Saltando.")
        resultados_globales[label] = progreso[label]
        continue

    try:
        # Busqueda STAC (sin filtro de nubes)
        search = catalog.search(
            collections=['sentinel-2-l2a'],
            bbox=list(bbox),
            datetime=f'{fi}/{ff}',
        )
        items_mes = list(search.items())
        print(f"  Escenas: {len(items_mes)}")

        if len(items_mes) == 0:
            print("  Sin escenas.")
            progreso[label] = {'status': 'ok', 'escenas': 0, 'exportadas': 0, 'error': None}
            with open(LOG_PATH, 'w') as f:
                json.dump(progreso, f, indent=2)
            continue

        # Procesar batches
        BATCH_SIZE = 5
        rgb_mes = []

        for bs in range(0, len(items_mes), BATCH_SIZE):
            batch = items_mes[bs:bs+BATCH_SIZE]
            try:
                # Cargar RGB + SCL para mascaras
                ds = load(batch, bands=['red', 'green', 'blue', 'scl'],
                          bbox=list(bbox), crs='EPSG:4326',
                          resolution=0.0001, groupby=None)

                if ds.sizes.get('time', 0) == 0:
                    continue

                for t in range(ds.sizes['time']):
                    try:
                        item_actual = batch[t]
                        escena = ds.isel(time=t)
                        fecha_dt = pd.Timestamp(ds.time.values[t]).to_pydatetime()

                        # Aplicar mascara SCL (clases 4,5) igual que NDRE
                        mascara_scl = np.zeros_like(escena['scl'].values, dtype=bool)
                        for c in [4, 5]:
                            mascara_scl = mascara_scl | (escena['scl'].values == c)

                        # Escalar RGB y enmascarar
                        r = np.where(mascara_scl, escena['red'].values / 10000.0, np.nan)
                        g = np.where(mascara_scl, escena['green'].values / 10000.0, np.nan)
                        b = np.where(mascara_scl, escena['blue'].values / 10000.0, np.nan)

                        # Aplicar mascara geometrica
                        ny, nx = r.shape
                        transform = escena['red'].rio.transform()
                        mask_geo = ~geometry_mask(
                            gdf_geo.geometry.values, transform=transform,
                            out_shape=(ny, nx)
                        )
                        r = np.where(mask_geo, r, np.nan)
                        g = np.where(mask_geo, g, np.nan)
                        b = np.where(mask_geo, b, np.nan)

                        cloud_cover = item_actual.properties.get('eo:cloud_cover', -1)

                        rgb_mes.append({
                            'r': r, 'g': g, 'b': b,
                            'fecha_dt': fecha_dt,
                            'cloud_cover': cloud_cover,
                        })
                    except Exception as e:
                        print(f"    Error escena t={t}: {e}")
                        continue
                del ds
            except Exception as e:
                print(f"    Error batch: {e}")
                continue

        print(f"  RGB calculado: {len(rgb_mes)} imagenes")

        # Exportar
        contador = 0
        registros_mes = []
        mes_carpeta = os.path.join(BASE_DIR, label)
        png_dir = os.path.join(mes_carpeta, 'PNG')
        os.makedirs(png_dir, exist_ok=True)

        for res in rgb_mes:
            try:
                r_arr = res['r']; g_arr = res['g']; b_arr = res['b']
                fecha_dt = res['fecha_dt']
                fecha_str = fecha_dt.strftime('%Y%m%d')
                hora_str = fecha_dt.strftime('%H%M%S')
                contador += 1
                mes_corto = label.split(' - ')[1].split()[0] if ' - ' in label else label
                cv = res.get('cloud_cover', -1)

                pix_validos = np.sum(~np.isnan(r_arr))
                if pix_validos == 0:
                    sufijo = 'SinDatos'
                elif cv < 10:
                    sufijo = 'Despejada'
                else:
                    sufijo = 'Nublada'

                nombre_base = f'RGB_{mes_corto}_{contador:03d}_{fecha_str}_{hora_str}_{sufijo}'
                png_path = os.path.join(png_dir, f'{nombre_base}.png')

                exportar_rgb_png(r_arr, g_arr, b_arr, png_path)

                registros_mes.append({
                    'fecha': fecha_dt.strftime('%Y-%m-%d'),
                    'hora': fecha_dt.strftime('%H:%M:%S'),
                    'id_escena': nombre_base,
                    'nubes_porciento': cv,
                    'estado_nubosidad': sufijo,
                    'ruta_png': png_path,
                    'mes_label': label,
                })
            except Exception as e:
                print(f"    Error exportando {contador}: {e}")
                continue

        if registros_mes:
            csv_path = os.path.join(mes_carpeta, 'metadatos.csv')
            generar_csv_metadatos(registros_mes, csv_path)

        # Estadisticas
        d = sum(1 for r in registros_mes if r['estado_nubosidad'] == 'Despejada')
        n = sum(1 for r in registros_mes if r['estado_nubosidad'] == 'Nublada')
        s = sum(1 for r in registros_mes if r['estado_nubosidad'] == 'SinDatos')
        print(f"  Exportado: {len(registros_mes)} PNGs ({d}D/{n}N/{s}S) a {label}")

        progreso[label] = {
            'status': 'ok', 'escenas': len(items_mes),
            'exportadas': len(registros_mes),
            'despejadas': d, 'nubladas': n, 'sindatos': s, 'error': None
        }
        resultados_globales[label] = progreso[label]
        with open(LOG_PATH, 'w') as f:
            json.dump(progreso, f, indent=2)

        del rgb_mes

    except Exception as e:
        print(f"  ERROR CRITICO {label}: {e}")
        traceback.print_exc()
        progreso[label] = {'status': 'error', 'escenas': 0, 'exportadas': 0, 'error': str(e)}
        with open(LOG_PATH, 'w') as f:
            json.dump(progreso, f, indent=2)
        continue

# ============================================================
# REPORTE FINAL
# ============================================================
print(f"\n\n{'='*60}")
print("   REPORTE FINAL - RGB FEB 2025 A JUN 2026")
print(f"{'='*60}")

total_escenas = 0
total_exp = 0
total_d = 0
total_n = 0
total_s = 0
errores = 0

for label, info in sorted(resultados_globales.items()):
    if info['status'] == 'ok':
        e = info.get('escenas', 0)
        x = info.get('exportadas', 0)
        d = info.get('despejadas', 0)
        n = info.get('nubladas', 0)
        s = info.get('sindatos', 0)
        total_escenas += e
        total_exp += x
        total_d += d
        total_n += n
        total_s += s
        print(f"  {label:25s}: {e:2d} escenas -> {x:2d} PNGs ({d}D/{n}N/{s}S)")
    else:
        errores += 1
        print(f"  {label:25s}: ERROR")

print(f"\n{'='*60}")
print(f"  TOTAL: {total_escenas} escenas | {total_exp} PNGs")
print(f"  Despejadas: {total_d} | Nubladas: {total_n} | SinDatos: {total_s}")
if errores:
    print(f"  ERRORES: {errores} meses")
print(f"  Directorio: {BASE_DIR}")
print(f"{'='*60}")
