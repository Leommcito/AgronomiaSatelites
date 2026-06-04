# =============================================================================
# MULTI-ÍNDICES STAC — ABRIL 2026
# Procesa imágenes Sentinel-2 L2A de abril 2026 calculando 5 índices
# (MSAVI2, S2REP, LAI_RedEdge, Cab_RedEdge, Kc_Actual) con máscara SCL
# y exportación por índice a carpetas separadas (PNG + TIF + CSV).
#
# Referencias:
#   - codigo_gee.js (GEE): fórmulas MSAVI2, S2REP, LAI, Cab, Kc
#   - Fase1_NDRE_2025_2026.ipynb: patrón STAC + SCL + exportación
#
# Ejecución:
#   python multi_indices_abril2026.py
#   (auto-detecta Colab vs local)
# =============================================================================

# ---------------------------------------------------------------------------
# CELDA 1: AUTO-DETECCIÓN DE ENTORNO + VERIFICACIÓN DE LIBRERÍAS
# ---------------------------------------------------------------------------
import sys
import subprocess
import os
import importlib

EN_COLAB = "google.colab" in sys.modules

LIBRERIAS = [
    "pystac_client", "geopandas", "rioxarray", "rasterio",
    "odc", "stackstac", "xarray", "matplotlib"
]

# Verificar librerías faltantes
LIBRERIAS_FALTANTES = [
    l for l in LIBRERIAS
    if not importlib.util.find_spec(l.split('.')[0])
]

if EN_COLAB:
    print("Entorno: GOOGLE COLAB")
    if LIBRERIAS_FALTANTES:
        get_ipython().system(  # noqa: F821
            "pip install pystac-client stackstac rioxarray "
            "geopandas rasterio odc-stac -q"
        )
else:
    print("Entorno: PC LOCAL")
    if LIBRERIAS_FALTANTES:
        print(f"Librerías faltantes: {LIBRERIAS_FALTANTES}")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install"]
            + LIBRERIAS_FALTANTES + ["-q"]
        )
    else:
        print("Todas las librerías ya instaladas.")

print("Entorno listo.\n")


# ---------------------------------------------------------------------------
# CELDA 2: IMPORTACIONES
# ---------------------------------------------------------------------------
import glob
import numpy as np
import pandas as pd
import geopandas as gpd
import xarray as xr
import rioxarray
import rasterio
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
from pystac_client import Client
from odc.stac import load
from rasterio.features import geometry_mask

if EN_COLAB:
    from google.colab import drive

print("Importaciones completadas.\n")


# ---------------------------------------------------------------------------
# CELDA 3: CONFIGURACIÓN UNIFICADA
# ---------------------------------------------------------------------------

if EN_COLAB:
    drive.mount('/content/drive')
    SHAPEFILE_PATH = (
        "/content/drive/MyDrive/Tesis/GEE Murcott/ROI/"
        "Parcelas+Definidas.zip"
    )
    BASE_DIR = os.path.join(
        os.path.dirname(SHAPEFILE_PATH), "output", "Imagenes"
    )
else:
    SCRIPT_DIR = os.getcwd()
    SHAPEFILE_PATH = os.path.join(SCRIPT_DIR, "4ParcelasDefinidas.zip")
    if not os.path.exists(SHAPEFILE_PATH):
        SHAPEFILE_PATH = "./4ParcelasDefinidas.zip"
    if not os.path.exists(SHAPEFILE_PATH):
        SHAPEFILE_PATH = input("Ruta del shapefile: ").strip()
    BASE_DIR = os.path.join(SCRIPT_DIR, "output", "Imagenes")

# ═══════ PARÁMETROS CONFIGURABLES ═══════
PERIODO_INICIO = "2026-04-01"
PERIODO_FIN = "2026-04-30"

# Coeficientes de modelos biofísicos (mismos que codigo_gee.js)
LAI_factor = 0.15
Cab_factor = 2
kc_slope = 1.15
kc_intercept = 0.1

# Umbral de nubes para etiquetado en nombre de archivo (NO filtra)
UMBRAL_NUBES = 10

# Tamaño de lote para carga de datos (evitar saturación RAM)
BATCH_SIZE = 5

# Índices a procesar con sus colormaps y rangos de visualización
INDICES_CONFIG = {
    "MSAVI2":      {"cmap": "RdYlGn", "vmin": 0.2, "vmax": 0.8},
    "S2REP":       {"cmap": "turbo",  "vmin": 705, "vmax": 740},
    "LAI_RedEdge": {"cmap": "Greens", "vmin": 0.1, "vmax": 6.0},
    "Cab_RedEdge": {"cmap": "YlGn",   "vmin": 0,   "vmax": 100},
    "Kc_Actual":   {"cmap": "BrBG",   "vmin": 0.2, "vmax": 1.3},
}
LISTA_INDICES = list(INDICES_CONFIG.keys())

os.makedirs(BASE_DIR, exist_ok=True)

print("Configuración cargada.")
print(f"  Shapefile: {SHAPEFILE_PATH}")
print(f"  Período: {PERIODO_INICIO} a {PERIODO_FIN}")
print(f"  Índices: {', '.join(LISTA_INDICES)}")
print(f"  Exportar a: {BASE_DIR}\n")


# ===========================================================================
# FUNCIONES AUXILIARES — T003 a T006
# ===========================================================================


# ---------------------------------------------------------------------------
# T003: CARGA DE SHAPEFILE
# ---------------------------------------------------------------------------
def cargar_shapefile(ruta):
    """Carga shapefile y retorna (gdf_geo, bbox)."""
    print("Cargando shapefile...")
    gdf = gpd.read_file(ruta)
    print(f"  Features: {len(gdf)}")
    if gdf.crs and gdf.crs.is_geographic:
        gdf_geo = gdf
    else:
        gdf_geo = gdf.to_crs("EPSG:4326")
    bbox = gdf_geo.total_bounds
    print(f"  BBox: {bbox}")
    return gdf_geo, bbox


# ---------------------------------------------------------------------------
# T004: CONEXIÓN STAC
# ---------------------------------------------------------------------------
def conectar_stac():
    """Conecta al catálogo Earth Search y retorna el cliente."""
    print("Conectando a Earth Search (AWS)...")
    catalog = Client.open("https://earth-search.aws.element84.com/v1")
    print("  Conexión exitosa.")
    return catalog


# ---------------------------------------------------------------------------
# T005: FUNCIONES AUXILIARES (máscaras + exportación)
# ---------------------------------------------------------------------------
def aplicar_mascara_scl(scl, clases_validas=None):
    """Máscara SCL: True donde la clase está en clases_validas."""
    if clases_validas is None:
        clases_validas = [4, 5]
    mask = xr.zeros_like(scl, dtype=bool)
    for c in clases_validas:
        mask = mask | (scl == c)
    return mask


def aplicar_mascara_geometrica(da, gdf):
    """Máscara geométrica: solo píxeles DENTRO de las geometrías."""
    x_name = next(
        (n for n in ["x", "lon", "longitude"] if n in da.coords), None
    )
    y_name = next(
        (n for n in ["y", "lat", "latitude"] if n in da.coords), None
    )
    if not x_name or not y_name:
        print("    AVISO: No se encontraron coordenadas, "
              "saltando máscara geométrica")
        return da
    transform = da.rio.transform()
    ny = da.sizes[y_name]
    nx = da.sizes[x_name]
    # geometry_mask retorna True FUERA de la geometría → invertir con ~
    mascara = ~geometry_mask(
        gdf.geometry.values, transform=transform, out_shape=(ny, nx)
    )
    mascara_da = xr.DataArray(
        mascara, dims=(y_name, x_name),
        coords={y_name: da[y_name], x_name: da[x_name]}
    )
    return da.where(mascara_da)


def exportar_tif(da, path, crs="EPSG:4326", nodata=-9999):
    """Exporta DataArray a GeoTIFF con rioxarray (fallback rasterio)."""
    try:
        da2 = da.copy()
        x_name = next(
            (n for n in ["x", "lon", "longitude"] if n in da2.coords), None
        )
        y_name = next(
            (n for n in ["y", "lat", "latitude"] if n in da2.coords), None
        )
        if x_name and y_name:
            da2 = da2.rename({x_name: "x", y_name: "y"})
        da2.rio.set_spatial_dims("x", "y", inplace=True)
        if not da2.rio.crs:
            da2 = da2.rio.write_crs(crs)
        da2.rio.to_raster(path, dtype="float32", compress="lzw", nodata=nodata)
    except Exception:
        # Fallback: exportar sin georreferencia
        data_arr = da.values.astype("float32") if hasattr(da, "values") else da
        ny, nx = data_arr.shape
        with rasterio.open(
            path, "w", driver="GTiff", height=ny, width=nx,
            count=1, dtype="float32",
            crs=rasterio.crs.CRS.from_string(crs),
            compress="lzw", nodata=nodata
        ) as dst:
            dst.write(data_arr, 1)


def exportar_png(data, path, cmap_name="RdYlGn", vmin=0, vmax=1, dpi=200):
    """Exporta array 2D a PNG con colormap y rango específicos."""
    cmap = plt.get_cmap(cmap_name)
    cmap.set_bad(color="white", alpha=0)
    plt.figure(figsize=(10, 10))
    plt.imshow(
        np.where(np.isnan(np.asarray(data)), np.nan, np.asarray(data)),
        cmap=cmap, vmin=vmin, vmax=vmax
    )
    plt.axis("off")
    plt.savefig(path, bbox_inches="tight", pad_inches=0, dpi=dpi)
    plt.close()


# ---------------------------------------------------------------------------
# T006: CÁLCULO DE ÍNDICES ESPECTRALES
# ---------------------------------------------------------------------------
def calcular_msavi2(nir, red):
    """
    MSAVI2 = (2*NIR+1 - sqrt((2*NIR+1)^2 - 8*(NIR-RED))) / 2
    Guardia: discriminante negativo → NaN
    """
    nir_a = np.asarray(nir)
    red_a = np.asarray(red)
    disc = (2 * nir_a + 1) ** 2 - 8 * (nir_a - red_a)
    disc = np.where(disc < 0, np.nan, disc)
    msavi2 = (2 * nir_a + 1 - np.sqrt(disc)) / 2
    msavi2 = xr.where((nir + red) == 0, np.nan, msavi2)
    return msavi2.clip(0, 1)


def calcular_s2rep(b4, b5, b6, b7):
    """
    S2REP = 705 + 35 * (((B4+B7)/2 - B5) / (B6 - B5))
    Guardia: |B6-B5| < 0.0001 → NaN (división por cero)
    Clip a [700, 750] nm
    """
    denom = b6 - b5
    s2rep = xr.where(
        np.abs(denom) < 0.0001, np.nan,
        705 + 35 * (((b4 + b7) / 2 - b5) / denom)
    )
    return s2rep.where((s2rep >= 705) & (s2rep <= 740))


def calcular_lai(s2rep):
    """LAI_RedEdge = (S2REP - 700) * LAI_factor. Clip a [0.1, 6.0]."""
    return xr.clip((s2rep - 700) * LAI_factor, 0.1, 6.0)


def calcular_cab(s2rep):
    """Cab_RedEdge = (S2REP - 700) * Cab_factor. Clip a [0, 100]."""
    return xr.clip((s2rep - 700) * Cab_factor, 0, 100)


def calcular_kc(msavi2):
    """Kc_Actual = MSAVI2 * kc_slope + kc_intercept. Clip a [0.2, 1.3]."""
    return xr.clip(msavi2 * kc_slope + kc_intercept, 0.2, 1.3)


def calcular_estadisticas_parcela(da, gdf, nombre_indice):
    """Calcula mean, std y pixeles_validos por parcela para un índice."""
    stats = []
    col_parcela = "name" if "name" in gdf.columns else gdf.columns[0]
    for i2, row in gdf.iterrows():
        mascara_parcela = aplicar_mascara_geometrica(da, gdf.iloc[[i2]])
        valores = mascara_parcela.values.flatten()
        valores = valores[~np.isnan(valores)]
        stats.append({
            "ID_Parcela": row.get(col_parcela, str(i2)),
            f"{nombre_indice}_mean": float(np.mean(valores)) if len(valores) > 0 else "",
            f"{nombre_indice}_std": float(np.std(valores)) if len(valores) > 0 else "",
            "pixeles_validos": int(len(valores)),
        })
    return stats


print("Funciones auxiliares cargadas.\n")


# ===========================================================================
# EJECUCIÓN PRINCIPAL
# ===========================================================================


# ---------------------------------------------------------------------------
# T007: BÚSQUEDA STAC + RESUMEN DE ESCENAS
# ---------------------------------------------------------------------------
print("=" * 60)
print("  BÚSQUEDA STAC — ABRIL 2026")
print("=" * 60)

# Cargar shapefile
gdf_geo, bbox = cargar_shapefile(SHAPEFILE_PATH)

# Conectar catálogo
catalog = conectar_stac()

# Buscar escenas (SIN filtro eo:cloud_cover — solo se etiqueta después)
search = catalog.search(
    collections=["sentinel-2-l2a"],
    bbox=list(bbox),
    datetime=f"{PERIODO_INICIO}/{PERIODO_FIN}",
)
items = list(search.items())

if len(items) == 0:
    print("\n  No se encontraron imágenes para abril 2026.")
    print("  Verificar cobertura de Sentinel-2 sobre Jujuy.")
    sys.exit(0)

print(f"\n  Total escenas encontradas: {len(items)}")
print(f"\n  {'Fecha':15s} {'Hora':10s} {'Nubes %':8s} {'Estado':15s}")
print(f"  {'-'*15} {'-'*10} {'-'*8} {'-'*15}")

resultados_totales = []
for item in items:
    ts = item.datetime
    fecha_str = ts.strftime("%Y-%m-%d") if ts else "N/A"
    hora_str = ts.strftime("%H:%M:%S") if ts else "N/A"
    cloud = item.properties.get("eo:cloud_cover", -1)
    if cloud < 0:
        estado = "Sin dato"
    elif cloud < UMBRAL_NUBES:
        estado = "Despejada"
    else:
        estado = "Nublada"
    print(f"  {fecha_str:15s} {hora_str:10s} {cloud:>6.1f}%  {estado:15s}")
    resultados_totales.append({
        "fecha": fecha_str,
        "hora": hora_str,
        "id": item.id,
        "nubes_porciento": cloud,
        "estado": estado,
    })

df_resultados = pd.DataFrame(resultados_totales)
print(f"\n  Resumen por fecha:")
for fecha, grupo in df_resultados.groupby("fecha"):
    nubes_prom = grupo["nubes_porciento"].mean()
    print(f"    {fecha}: {len(grupo)} img(s) | "
          f"{'Despejada' if nubes_prom < UMBRAL_NUBES else 'Nublada'} "
          f"({nubes_prom:.1f}% nubes)")

print()


# ---------------------------------------------------------------------------
# T008-T013: PROCESAMIENTO POR ESCENA + EXPORTACIÓN + ESTADÍSTICAS
# ---------------------------------------------------------------------------
print("=" * 60)
print("  PROCESAMIENTO DE ESCENAS — ABRIL 2026")
print("=" * 60)

# Verificar que el shapefile tiene columna 'name' para identificar parcelas
col_parcela = "name" if "name" in gdf_geo.columns else gdf_geo.columns[0]

# Inicializar registro de estadísticas por índice
stats_por_indice = {indice: [] for indice in LISTA_INDICES}

# Obtener el label del mes para naming
label_mes = "Abril2026"

contador_global = 0
total_exportados = 0
total_omitidos = 0

for idx_item, item in enumerate(items):
    ts = item.datetime
    fecha_dt = ts if ts else None
    if fecha_dt is None:
        continue

    fecha_str = fecha_dt.strftime("%Y%m%d")
    hora_str = fecha_dt.strftime("%H%M%S")
    cloud_val = item.properties.get("eo:cloud_cover", -1)
    estado = "Despejada" if cloud_val < UMBRAL_NUBES and cloud_val >= 0 \
             else "Nublada"

    print(f"\n[{idx_item+1}/{len(items)}] {fecha_str} {hora_str} "
          f"| {estado} ({cloud_val:.0f}% nubes)")

    # T009: Verificar los 5 TIFs antes de decidir si cargar la escena
    tifs_existentes = 0
    tifs_detalle = {}
    for nom in LISTA_INDICES:
        base = f"{nom}_Abril_{contador_global + 1:03d}_{fecha_str}_{hora_str}_{estado}"
        tif_path = os.path.join(BASE_DIR, nom, label_mes, "TIF", f"{base}.tif")
        existe = os.path.exists(tif_path)
        tifs_detalle[nom] = {"existe": existe, "base": base, "tif_path": tif_path}
        if existe:
            tifs_existentes += 1

    if tifs_existentes == len(LISTA_INDICES):
        print(f"  Todos los {len(LISTA_INDICES)} TIFs ya existen. Saltando.")
        total_omitidos += 1
        continue
    elif tifs_existentes > 0:
        print(f"  {tifs_existentes}/{len(LISTA_INDICES)} TIFs ya existen. "
              f"Procesando solo los faltantes.")

    try:
        # Cargar bands para esta escena individual
        ds = load(
            [item],
            bands=["red", "rededge1", "rededge2", "rededge3", "nir", "scl"],
            bbox=list(bbox),
            crs="EPSG:4326",
            resolution=0.0001,  # ~10m, upsampea bandas 20m
            groupby=None,
        )

        if ds.sizes.get("time", 0) == 0:
            print("  Sin datos en esta escena. Saltando.")
            continue

        escena = ds.isel(time=0)

        # Extraer bandas y escalar
        b4 = escena["red"].astype("float32") / 10000.0
        b5 = escena["rededge1"].astype("float32") / 10000.0
        b6 = escena["rededge2"].astype("float32") / 10000.0
        b7 = escena["rededge3"].astype("float32") / 10000.0
        b8 = escena["nir"].astype("float32") / 10000.0

        # Aplicar máscara SCL (clases 4,5)
        mascara_scl = aplicar_mascara_scl(escena["scl"])
        b4 = b4.where(mascara_scl)
        b5 = b5.where(mascara_scl)
        b6 = b6.where(mascara_scl)
        b7 = b7.where(mascara_scl)
        b8 = b8.where(mascara_scl)

        # Aplicar máscara geométrica (recorte a parcelas)
        b4 = aplicar_mascara_geometrica(b4, gdf_geo)
        b5 = aplicar_mascara_geometrica(b5, gdf_geo)
        b6 = aplicar_mascara_geometrica(b6, gdf_geo)
        b7 = aplicar_mascara_geometrica(b7, gdf_geo)
        b8 = aplicar_mascara_geometrica(b8, gdf_geo)

        # Calcular índices
        msavi2 = calcular_msavi2(b8, b4)
        s2rep = calcular_s2rep(b4, b5, b6, b7)
        lai = calcular_lai(s2rep)
        cab = calcular_cab(s2rep)
        kc = calcular_kc(msavi2)

        indices_calculados = {
            "MSAVI2": msavi2,
            "S2REP": s2rep,
            "LAI_RedEdge": lai,
            "Cab_RedEdge": cab,
            "Kc_Actual": kc,
        }

        # Exportar cada índice (TIF + PNG + estadísticas)
        contador_global += 1

        for nombre_indice, da_indice in indices_calculados.items():
            data_values = da_indice.values if hasattr(da_indice, "values") else da_indice

            # Determinar sufijo (per-index)
            if np.all(np.isnan(np.asarray(data_values))):
                sufijo = "SinDatos"
                estado_label = "SinDatos"
            else:
                sufijo = estado
                estado_label = estado

            nombre_archivo = (
                f"{nombre_indice}_Abril_{contador_global:03d}_"
                f"{fecha_str}_{hora_str}_{sufijo}"
            )

            dir_indice = os.path.join(BASE_DIR, nombre_indice, label_mes)
            dir_tif = os.path.join(dir_indice, "TIF")
            dir_png = os.path.join(dir_indice, "PNG")
            tif_path = os.path.join(dir_tif, f"{nombre_archivo}.tif")
            if os.path.exists(tif_path):
                print(f"  {nombre_indice}: TIF ya existe → saltando")
                continue

            # Crear carpetas del índice
            os.makedirs(dir_tif, exist_ok=True)
            os.makedirs(dir_png, exist_ok=True)

            # T008: Exportar TIF
            exportar_tif(da_indice, tif_path)
            print(f"  {nombre_indice}: TIF exportado → {nombre_archivo}.tif")

            # T010: Exportar PNG con colormap específico
            config = INDICES_CONFIG[nombre_indice]
            png_path = os.path.join(dir_png, f"{nombre_archivo}.png")
            exportar_png(data_values, png_path,
                         cmap_name=config["cmap"],
                         vmin=config["vmin"], vmax=config["vmax"])

            # T011-T012: Calcular estadísticas por parcela
            stats_parcelas = calcular_estadisticas_parcela(
                da_indice, gdf_geo, nombre_indice
            )

            # Acumular registros para CSV
            for stat in stats_parcelas:
                stats_por_indice[nombre_indice].append({
                    "fecha": fecha_str,
                    "hora": hora_str,
                    "id_escena": nombre_archivo,
                    "nubes_porciento": cloud_val,
                    "estado_nubosidad": estado_label,
                    **stat,
                    "ruta_tif": tif_path,
                    "ruta_png": png_path,
                })

            total_exportados += 1

        del ds

    except Exception as e:
        print(f"  ERROR procesando escena {fecha_str}: {e}")
        continue


# ---------------------------------------------------------------------------
# T013: GUARDAR CSV POR ÍNDICE
# ---------------------------------------------------------------------------
print(f"\n{'='*60}")
print(f"  GUARDANDO ESTADÍSTICAS POR ÍNDICE")
print(f"{'='*60}")

for nombre_indice in LISTA_INDICES:
    registros = stats_por_indice[nombre_indice]
    if not registros:
        print(f"  {nombre_indice}: sin registros")
        continue

    df_stats = pd.DataFrame(registros)
    dir_indice = os.path.join(BASE_DIR, nombre_indice, label_mes)
    csv_path = os.path.join(dir_indice, "estadisticas.csv")
    df_stats.to_csv(csv_path, index=False, encoding="utf-8")
    print(f"  {nombre_indice}: {len(df_stats)} registros → "
          f"estadisticas.csv")


# ---------------------------------------------------------------------------
# T014-T015: REPORTE FINAL + VALIDACIÓN
# ---------------------------------------------------------------------------
print(f"\n{'='*60}")
print(f"  REPORTE FINAL — MULTI-ÍNDICES ABRIL 2026")
print(f"{'='*60}")
print(f"  Período: {PERIODO_INICIO} a {PERIODO_FIN}")
print(f"  Escenas totales: {len(items)}")
print(f"  Exportados: {total_exportados} archivos "
      f"({total_omitidos} omitidos por duplicados)")
print()

total_tifs = 0
total_pngs = 0
for nombre_indice in LISTA_INDICES:
    dir_indice = os.path.join(BASE_DIR, nombre_indice, label_mes)
    dir_tif = os.path.join(dir_indice, "TIF")
    dir_png = os.path.join(dir_indice, "PNG")
    csv_path = os.path.join(dir_indice, "estadisticas.csv")

    n_tif = len(glob.glob(os.path.join(dir_tif, "*.tif"))) if os.path.isdir(dir_tif) else 0
    n_png = len(glob.glob(os.path.join(dir_png, "*.png"))) if os.path.isdir(dir_png) else 0
    tiene_csv = "CSV OK" if os.path.exists(csv_path) else "---"

    total_tifs += n_tif
    total_pngs += n_png

    # Validar rangos desde CSV si existe
    if os.path.exists(csv_path):
        try:
            df_check = pd.read_csv(csv_path)
            col_mean = f"{nombre_indice}_mean"
            if col_mean in df_check.columns:
                vals = df_check[col_mean].dropna()
                if len(vals) > 0:
                    cfg = INDICES_CONFIG[nombre_indice]
                    in_range = vals.between(cfg["vmin"], cfg["vmax"]).all()
                    rango_str = f"Rango {cfg['vmin']}-{cfg['vmax']}: {'OK' if in_range else 'FUERA'}"
                else:
                    rango_str = "Sin datos válidos"
            else:
                rango_str = "CSV sin columna mean"
        except Exception:
            rango_str = "Error leyendo CSV"
    else:
        rango_str = ""

    print(f"  {nombre_indice:15s}: {n_tif:3d} TIFs | {n_png:3d} PNGs "
          f"| {tiene_csv} | {rango_str}")

print()
print(f"  TOTAL: {total_tifs} TIFs + {total_pngs} PNGs exportados")
print(f"  Directorio base: {BASE_DIR}")
print(f"{'='*60}")
print("  Procesamiento completado.")
print(f"{'='*60}")



