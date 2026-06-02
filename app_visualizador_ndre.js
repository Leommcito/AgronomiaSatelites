// =============================================================================
// VISUALIZADOR NDRE - IMÁGENES CRUDAS SIN FILTRO DE NUBES
// =============================================================================
// App interactiva de Google Earth Engine para visualizar imágenes NDRE de
// Sentinel-2 (2025-2026) en las 4 parcelas de mandarina Murcott.
//
// CARACTERÍSTICAS:
//   • Mapa NDRE con parcelas superpuestas
//   • Slider para navegar entre fechas de pasada del satélite
//   • Botón Play/Pause para animación automática
//   • Fecha visible de la imagen actual
//
// DIFERENCIA con codigo_gee.js:
//   Este visualizador NO filtra nubes. Muestra TODAS las imágenes tal cual
//   las capturó el satélite, con nubes y todo.
//
// CÓMO PUBLICAR LA APP:
//   1. Abrir https://code.earthengine.google.com/
//   2. Pegar este script y hacer clic en "Run"
//   3. Botón "Apps" (arriba derecha) → "New App" → "Publish"
//   4. Compartir el link generado
// =============================================================================

// ---------------------------------------------------------------------------
// 1. PARÁMETROS
// ---------------------------------------------------------------------------
var startDate = '2025-01-01';
var endDate = '2026-06-01';
var paletaVigor = ['#d73027', '#fc8d59', '#fee08b', '#d9ef8b', '#91cf60', '#1a9850'];
var visParams = {min: 0.1, max: 0.6, palette: paletaVigor};

// ---------------------------------------------------------------------------
// 2. CARGAR PARCELAS
// ---------------------------------------------------------------------------
var parcelas = ee.FeatureCollection(
  'projects/proyectoleomespinosa/assets/ParcelasDefinidas'
);

// ---------------------------------------------------------------------------
// 3. CONSTRUIR UI
// ---------------------------------------------------------------------------

// 3a. Mapa principal
var mapa = ui.Map();
mapa.setOptions('SATELLITE');
mapa.centerObject(parcelas, 14);

// Capa de parcelas (siempre visible)
mapa.addLayer(parcelas, {color: 'red'}, 'Parcelas');

// 3b. Etiqueta de fecha
var lblFecha = ui.Label('Fecha: cargando...', {fontSize: '14px', fontWeight: 'bold', margin: '0 10px'});

// 3c. Botón Play / Pause
var reproduciendo = false;
var intervaloId = null;
var btnPlay = ui.Button({label: '▶ Play', style: {margin: '0 5px'}});

// 3d. Slider
var slider = ui.Slider(0, 1, 0, 1);
slider.style().set({width: '100%', margin: '5px 0'});

// 3e. Panel de control
var panelControl = ui.Panel({
  widgets: [
    ui.Panel({
      widgets: [btnPlay, lblFecha],
      layout: ui.Panel.Layout.flow('horizontal'),
      style: {margin: '0px 0px 5px 0px'}
    }),
    slider
  ],
  layout: ui.Panel.Layout.flow('vertical'),
  style: {
    position: 'bottom-center',
    padding: '10px 15px',
    backgroundColor: 'rgba(255,255,255,0.9)',
    width: '80%',
    border: '1px solid #ccc'
  }
});

mapa.add(panelControl);

// ---------------------------------------------------------------------------
// 4. CARGAR SENTINEL-2 L2A Y CALCULAR NDRE (SIN FILTRO DE NUBES)
// ---------------------------------------------------------------------------
var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(parcelas)
  .filterDate(startDate, endDate);

// Calcular NDRE sin filtrar nubes
function addNDRE(image) {
  var b8 = image.select('B8').divide(10000);
  var b5 = image.select('B5').divide(10000);
  var ndre = b8.subtract(b5).divide(b8.add(b5)).rename('NDRE');
  return image.addBands(ndre).copyProperties(image, ['system:time_start']);
}

// Colección NDRE cruda, clip a parcelas para rendimiento
var ndreCol = s2.map(addNDRE).select('NDRE').map(function(img) {
  return img.clip(parcelas);
});

// ---------------------------------------------------------------------------
// 5. CONFIGURAR SLIDER CUANDO LLEGUEN LOS DATOS DEL SERVIDOR
// ---------------------------------------------------------------------------
var ndreList = ndreCol.toList(ndreCol.size());
var timestamps = ndreCol.aggregate_array('system:time_start');
var fechas = [];

timestamps.evaluate(function(ts) {
  if (!ts || ts.length === 0) {
    lblFecha.setValue('No hay imágenes en el rango de fechas');
    return;
  }

  // Convertir timestamps a strings de fecha
  fechas = ts.map(function(t) {
    var d = new Date(t);
    return d.getFullYear() + '-' +
      ('0' + (d.getMonth() + 1)).slice(-2) + '-' +
      ('0' + d.getDate()).slice(-2);
  });

  slider.setMax(fechas.length - 1);
  lblFecha.setValue('Fecha: ' + fechas[0]);

  // Mostrar la primera imagen NDRE
  var primeraImg = ee.Image(ndreList.get(0));
  mapa.addLayer(primeraImg, visParams, 'NDRE');

  print('Total imágenes: ' + fechas.length);
});

// ---------------------------------------------------------------------------
// 6. MANEJADORES DE EVENTOS
// ---------------------------------------------------------------------------

// 6a. Slider → actualizar mapa y fecha
slider.onChange(function(valor) {
  var i = Math.round(Number(valor));
  if (i < 0 || i >= fechas.length) return;

  var img = ee.Image(ndreList.get(i));
  // Capa NDRE: índice 1 (parcelas es índice 0, agregada antes)
  mapa.layers().get(1).setEeObject(img, visParams);
  lblFecha.setValue('Fecha: ' + fechas[i]);
});

// 6b. Play / Pause
btnPlay.onClick(function() {
  reproduciendo = !reproduciendo;
  if (reproduciendo) {
    btnPlay.setLabel('⏸ Pause');
    intervaloId = ui.util.setInterval(function() {
      var val = slider.getValue();
      var maxVal = fechas.length - 1;
      if (maxVal <= 0) return;
      slider.setValue(val >= maxVal ? 0 : val + 1);
    }, 600);
  } else {
    btnPlay.setLabel('▶ Play');
    if (intervaloId !== null) {
      ui.util.clearInterval(intervaloId);
      intervaloId = null;
    }
  }
});

// ---------------------------------------------------------------------------
// 7. MOSTRAR LA APP (reemplaza el mapa por defecto)
// ---------------------------------------------------------------------------
ui.root.clear();
ui.root.add(mapa);

// ---------------------------------------------------------------------------
// 8. INFORMACIÓN EN CONSOLA
// ---------------------------------------------------------------------------
print('Visualizador NDRE - Imagenes crudas');
print('Rango: ' + startDate + ' a ' + endDate);
print('Usa el slider para navegar entre fechas.');
print('');
print('Para publicar: Apps > New App > seleccionar script > Publish');
