"""
Pipeline NDRE - Procesa cada mes de forma independiente (Feb 2025 a Jun 2026)
Si un mes falla, los siguientes continuan.
"""
import os, sys, glob, calendar, json, traceback
import numpy as np
import pandas as pd, geopandas as gpd
import xarray as xr, rioxarray, rasterio
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from pystac_client import Client
from odc.stac import load
from rasterio.features import geometry_mask

# ============================================================
# CONFIG GLOBAL
# ============================================================
SCRIPT_DIR = os.getcwd()
SHAPEFILE_PATH = os.path.join(SCRIPT_DIR, '4ParcelasDefinidas.zip')
BASE_DIR = os.path.join(SCRIPT_DIR, 'output', 'ndre', '4ParcelasDefinidas')

PERIODO_INICIO = "2025-02-01"
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
        anio = corriente.year
        mes = corriente.month
        ultimo_dia = calendar.monthrange(anio, mes)[1]
        desde = corriente.strftime('%Y-%m-%d')
        hasta_fin_mes = f'{anio}-{mes:02d}-{ultimo_dia}'
        fecha_hasta_dt = datetime.strptime(hasta_fin_mes, '%Y-%m-%d')
        fecha_hasta = min(fecha_hasta_dt, fin).strftime('%Y-%m-%d')
        label = f'{mes:02d} - {MES_NOMBRE[mes]} {anio}'
        fechas.append((desde, fecha_hasta, label))
        if mes == 12:
            corriente = corriente.replace(year=anio+1, month=1)
        else:
            corriente = corriente.replace(month=mes+1)
    return fechas

FECHAS = generar_fechas_por_mes(PERIODO_INICIO, PERIODO_FIN)
TOTAL_MESES = len(FECHAS)
print(f"Meses a procesar: {TOTAL_MESES}")
print(f"Periodo: {PERIODO_INICIO} a {PERIODO_FIN}\n")

# ============================================================
# FUNCIONES AUXILIARES
# ============================================================
def calcular_ndre(nir, rededge1):
    ndre = (nir - rededge1) / (nir + rededge1)
    ndre = xr.where((nir + rededge1) == 0, np.nan, ndre)
    return ndre

def aplicar_mascara_scl(scl, clases_validas=[4,5]):
    mask = xr.zeros_like(scl, dtype=bool)
    for c in clases_validas:
        mask = mask | (scl == c)
    return mask

def exportar_tif(da, path, crs='EPSG:4326', nodata=-9999):
    try:
        da2 = da.copy()
        x_name = next((n for n in ['x', 'lon', 'longitude'] if n in da2.coords), None)
        y_name = next((n for n in ['y', 'lat', 'latitude'] if n in da2.coords), None)
        if x_name and y_name:
            da2 = da2.rename({x_name: 'x', y_name: 'y'})
        da2.rio.set_spatial_dims('x', 'y', inplace=True)
        if not da2.rio.crs:
            da2 = da2.rio.write_crs(crs)
        da2.rio.to_raster(path, dtype='float32', compress='lzw', nodata=nodata)
    except Exception:
        data = da.values.astype('float32') if hasattr(da, 'values') else da
        ny, nx = data.shape
        with rasterio.open(path, 'w', driver='GTiff', height=ny, width=nx,
            count=1, dtype='float32', crs=rasterio.crs.CRS.from_string(crs),
            compress='lzw', nodata=nodata) as dst:
            dst.write(data, 1)

def exportar_png(data, path, vmin=0.1, vmax=0.6, dpi=200):
    colores = ['#d73027', '#fc8d59', '#fee08b', '#d9ef8b', '#91cf60', '#1a9850']
    cmap = LinearSegmentedColormap.from_list('vigor', colores, N=256)
    cmap.set_bad(color='white', alpha=0)
    plt.figure(figsize=(10,10))
    plt.imshow(np.where(np.isnan(data), np.nan, data), cmap=cmap, vmin=vmin, vmax=vmax)
    plt.axis('off')
    plt.savefig(path, bbox_inches='tight', pad_inches=0, dpi=dpi)
    plt.close()

def generar_csv_metadatos(registros, path):
    df = pd.DataFrame(registros)
    columnas = ['fecha', 'hora', 'id_escena', 'nubes_porciento', 'estado_nubosidad', 'ruta_tif', 'ruta_png', 'mes_label']
    df = df[[c for c in columnas if c in df.columns]]
    df.to_csv(path, index=False, encoding='utf-8')
    return df

def aplicar_mascara_geometrica(da, gdf):
    x_name = next((n for n in ['x', 'lon', 'longitude'] if n in da.coords), None)
    y_name = next((n for n in ['y', 'lat', 'latitude'] if n in da.coords), None)
    if not x_name or not y_name:
        return da
    transform = da.rio.transform()
    ny = da.sizes[y_name]
    nx = da.sizes[x_name]
    mascara = ~geometry_mask(gdf.geometry.values, transform=transform, out_shape=(ny, nx))
    mascara_da = xr.DataArray(mascara, dims=(y_name, x_name),
                               coords={y_name: da[y_name], x_name: da[x_name]})
    return da.where(mascara_da)

# ============================================================
# CARGAR SHAPEFILE (UNA VEZ)
# ============================================================
print("Cargando shapefile...")
gdf = gpd.read_file(SHAPEFILE_PATH)
if gdf.crs and gdf.crs.is_geographic:
    gdf_geo = gdf
else:
    gdf_geo = gdf.to_crs('EPSG:4326')
bbox = gdf_geo.total_bounds
print(f"Shapefile: {len(gdf)} parcelas")
print(f"BBox: {bbox}\n")

# Conectar STAC
catalog = Client.open('https://earth-search.aws.element84.com/v1')

# ============================================================
# PROCESAR CADA MES INDEPENDIENTEMENTE
# ============================================================
LOG_PATH = os.path.join(BASE_DIR, '_progreso.json')

# Cargar progreso anterior si existe
progreso = {}
if os.path.exists(LOG_PATH):
    with open(LOG_PATH, 'r') as f:
        progreso = json.load(f)

resultados_globales = {}

for mes_idx, (fecha_inicio, fecha_fin, label) in enumerate(FECHAS):
    print(f"\n{'='*60}")
    print(f"  MES {mes_idx+1}/{TOTAL_MESES}: {label}")
    print(f"  {fecha_inicio} -> {fecha_fin}")
    print(f"{'='*60}")

    # Saltar si ya fue procesado exitosamente
    if label in progreso and progreso[label].get('status') == 'ok':
        print(f"  Ya procesado anteriormente. Saltando.")
        resultados_globales[label] = progreso[label]
        continue

    try:
        # --- Busqueda STAC ---
        search = catalog.search(
            collections=['sentinel-2-l2a'],
            bbox=list(bbox),
            datetime=f'{fecha_inicio}/{fecha_fin}',
        )
        items_mes = list(search.items())
        print(f"  Escenas encontradas: {len(items_mes)}")

        if len(items_mes) == 0:
            print("  Mes sin escenas. Registrando como vacio.")
            progreso[label] = {'status': 'ok', 'escenas': 0, 'exportadas': 0, 'error': None}
            with open(LOG_PATH, 'w') as f:
                json.dump(progreso, f, indent=2)
            continue

        # --- Procesar batches ---
        BATCH_SIZE = 5
        ndre_mes = []
        errores_batch = 0

        for batch_start in range(0, len(items_mes), BATCH_SIZE):
            batch = items_mes[batch_start:batch_start+BATCH_SIZE]
            try:
                ds = load(batch, bands=['nir', 'rededge1', 'scl'],
                          bbox=list(bbox), crs='EPSG:4326',
                          resolution=0.0001, groupby=None)

                if ds.sizes.get('time', 0) == 0:
                    continue

                for t in range(ds.sizes['time']):
                    try:
                        item_actual = batch[t]
                        escena = ds.isel(time=t)
                        nir = escena['nir']
                        rededge1 = escena['rededge1']
                        scl = escena['scl']
                        ndre = calcular_ndre(nir, rededge1)
                        mascara = aplicar_mascara_scl(scl)
                        ndre_masked = ndre.where(mascara)
                        ndre_masked = aplicar_mascara_geometrica(ndre_masked, gdf_geo)
                        ts_val = ds.time.values[t]
                        fecha_dt = pd.Timestamp(ts_val).to_pydatetime()
                        cloud_cover = item_actual.properties.get('eo:cloud_cover', -1)
                        ndre_mes.append({
                            'ndre': ndre_masked,
                            'fecha_dt': fecha_dt,
                            'cloud_cover': cloud_cover,
                        })
                    except Exception as e:
                        errores_batch += 1
                        print(f"    Error en escena t={t}: {e}")
                        continue
                del ds
            except Exception as e:
                errores_batch += 1
                print(f"    Error cargando batch: {e}")
                continue

        print(f"  NDRE calculado: {len(ndre_mes)} imagenes (errores: {errores_batch})")

        # --- Exportar ---
        contador = 0
        registros_mes = []
        mes_carpeta = os.path.join(BASE_DIR, label)
        tif_dir = os.path.join(mes_carpeta, 'TIF')
        png_dir = os.path.join(mes_carpeta, 'PNG')
        os.makedirs(tif_dir, exist_ok=True)
        os.makedirs(png_dir, exist_ok=True)

        for resultado in ndre_mes:
            try:
                ndre_data = resultado['ndre']
                fecha_dt = resultado['fecha_dt']
                data_values = ndre_data.values if hasattr(ndre_data, 'values') else ndre_data

                fecha_str = fecha_dt.strftime('%Y%m%d')
                hora_str = fecha_dt.strftime('%H%M%S')
                contador += 1
                mes_corto = label.split(' - ')[1].split()[0] if ' - ' in label else label
                cloud_val = resultado.get('cloud_cover', -1)

                if np.all(np.isnan(data_values)):
                    sufijo = 'SinDatos'
                else:
                    sufijo = 'Despejada' if cloud_val < 10 else 'Nublada'

                nombre_base = f'NDRE_{mes_corto}_{contador:03d}_{fecha_str}_{hora_str}_{sufijo}'
                tif_path = os.path.join(tif_dir, f'{nombre_base}.tif')
                png_path = os.path.join(png_dir, f'{nombre_base}.png')

                exportar_tif(ndre_data, tif_path)
                exportar_png(data_values, png_path)

                registros_mes.append({
                    'fecha': fecha_dt.strftime('%Y-%m-%d'),
                    'hora': fecha_dt.strftime('%H:%M:%S'),
                    'id_escena': nombre_base,
                    'nubes_porciento': cloud_val,
                    'estado_nubosidad': sufijo,
                    'ruta_tif': tif_path,
                    'ruta_png': png_path,
                    'mes_label': label,
                })
            except Exception as e:
                print(f"    Error exportando escena {contador}: {e}")
                continue

        if registros_mes:
            csv_path = os.path.join(mes_carpeta, 'metadatos.csv')
            generar_csv_metadatos(registros_mes, csv_path)

        print(f"  Exportado: {len(registros_mes)} imagenes a {label}")
        del ndre_mes

        # --- Guardar progreso ---
        despejadas = sum(1 for r in registros_mes if r['estado_nubosidad'] == 'Despejada')
        nubladas = sum(1 for r in registros_mes if r['estado_nubosidad'] == 'Nublada')
        sindatos = sum(1 for r in registros_mes if r['estado_nubosidad'] == 'SinDatos')

        progreso[label] = {
            'status': 'ok',
            'escenas': len(items_mes),
            'exportadas': len(registros_mes),
            'despejadas': despejadas,
            'nubladas': nubladas,
            'sindatos': sindatos,
            'error': None
        }
        resultados_globales[label] = progreso[label]
        with open(LOG_PATH, 'w') as f:
            json.dump(progreso, f, indent=2)

    except Exception as e:
        print(f"  ERROR CRITICO en mes {label}: {e}")
        traceback.print_exc()
        progreso[label] = {'status': 'error', 'escenas': 0, 'exportadas': 0, 'error': str(e)}
        with open(LOG_PATH, 'w') as f:
            json.dump(progreso, f, indent=2)
        # Continuar con el siguiente mes
        continue

# ============================================================
# REPORTE FINAL
# ============================================================
print(f"\n\n{'='*60}")
print("   REPORTE FINAL - NDRE FEB 2025 A JUN 2026")
print(f"{'='*60}")

total_escenas = 0
total_exportadas = 0
total_despejadas = 0
total_nubladas = 0
total_sindatos = 0
errores = 0

for label, info in sorted(resultados_globales.items()):
    if info['status'] == 'ok':
        e = info.get('escenas', 0)
        x = info.get('exportadas', 0)
        d = info.get('despejadas', 0)
        n = info.get('nubladas', 0)
        s = info.get('sindatos', 0)
        total_escenas += e
        total_exportadas += x
        total_despejadas += d
        total_nubladas += n
        total_sindatos += s
        print(f"  {label:25s}: {e:2d} escenas -> {x:2d} exportadas ({d}D/{n}N/{s}S)")
    else:
        errores += 1
        print(f"  {label:25s}: ERROR - {info.get('error', 'desconocido')}")

print(f"\n{'='*60}")
print(f"  TOTAL: {total_escenas} escenas | {total_exportadas} exportadas")
print(f"  Despejadas: {total_despejadas} | Nubladas: {total_nubladas} | SinDatos: {total_sindatos}")
if errores:
    print(f"  ERRORES: {errores} meses")
print(f"  Directorio: {BASE_DIR}")
print(f"{'='*60}")
