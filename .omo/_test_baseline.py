"""Test baseline con Roigeneral.zip para enero 2025"""
import os, sys, calendar, numpy as np
import pandas as pd, geopandas as gpd
from datetime import datetime
from pystac_client import Client

SHAPEFILE_PATH = os.path.join(os.getcwd(), 'Roigeneral.zip')
BASE_DIR = os.path.join(os.getcwd(), 'ndre2025_2026')
os.makedirs(BASE_DIR, exist_ok=True)

PERIODO_INICIO = '2025-01-01'
PERIODO_FIN = '2025-01-31'
CLOUD_FILTER = {'eo:cloud_cover': {'lt': 10}}

# CARGAR SHAPEFILE
print('=== BASELINE: Roigeneral.zip ===')
print('Cargando shapefile...')
gdf = gpd.read_file(SHAPEFILE_PATH)
print(f'Features: {len(gdf)}')
print(f'Columnas: {list(gdf.columns)}')
print(f'CRS: {gdf.crs}')
if gdf.crs and gdf.crs.is_geographic:
    gdf_geo = gdf
else:
    gdf_geo = gdf.to_crs('EPSG:4326')
bbox = gdf_geo.total_bounds
print(f'Bounding Box: {bbox}')

# STAC QUERY
print('\nConectando Earth Search...')
catalog = Client.open('https://earth-search.aws.element84.com/v1')
search = catalog.search(
    collections=['sentinel-2-l2a'],
    bbox=list(bbox),
    datetime=f'{PERIODO_INICIO}/{PERIODO_FIN}',
    query=CLOUD_FILTER
)
items = list(search.items())
print(f'Escenas (<10% nubes): {len(items)}')
for item in items:
    cloud = item.properties.get('eo:cloud_cover', -1)
    dt = item.datetime.strftime('%Y-%m-%d %H:%M') if item.datetime else 'N/A'
    print(f'  {dt} | id={item.id} | nubes={cloud}%')

print('\nBaseline completado.')
