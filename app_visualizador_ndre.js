// =============================================================================
// VISUALIZADOR NDRE - IMÁGENES CRUDAS SIN FILTRO DE NUBES
// =============================================================================
// App interactiva de Google Earth Engine para visualizar imágenes NDRE de
// Sentinel-2 (2025-2026) en las 4 parcelas de mandarina Murcott.
//
// CARACTERÍSTICAS:
//   • Mapa con NDRE y parcelas superpuestas
//   • Slider para navegar entre fechas de pasada del satélite
//   • Botón ▶ Play / ⏸ Pause para animación automática
//   • Fecha visible de la imagen actual
//
// DIFERENCIA con codigo_gee.js:
//   Este visualizador NO filtra nubes. Muestra TODAS las imágenes tal cual
//   las capturó el satélite, con nubes y todo. Sirve para que la agrónoma
//   vea la materia prima antes de cualquier procesamiento.
//
// CÓMO PUBLICAR LA APP:
//   1. Abrir https://code.earthengine.google.com/
//   2. Pegar este script y hacer clic en "Run"
//   3. Verificar que el mapa y el slider funcionan
//   4. Botón "Apps" (arriba a la derecha) → "New App"
//   5. Seleccionar este script y publicar
//   6. Compartir el link generado
// =============================================================================

// ---------------------------------------------------------------------------
// 1. PARÁMETROS
// ---------------------------------------------------------------------------
var startDate = '2025-01-01';
var endDate = '2026-06-01';
var paletaVigor = ['#d73027', '#fc8d59', '#fee08b', '#d9ef8b', '#91cf60', '#1a9850'];
var visParams = {min: 0.1, max: 0.6, palette: paletaVigor};

// ---------------------------------------------------------------------------
// 2. CARGAR PARCELAS (mismo asset que codigo_gee.js)
// ---------------------------------------------------------------------------
var parcelas = ee.FeatureCollection(
  'projects/proyectoleomespinosa/assets/ParcelasDefinidas'
);

// ---------------------------------------------------------------------------
// 3. CARGAR SENTINEL-2 L2A CRUDO (SIN FILTRO DE NUBES)
// ---------------------------------------------------------------------------
// Importante: NO se aplica CS+, SCL, ni ningún enmascaramiento.
// Se usa reflectancia de superficie (L2A) para NDRE correcto, pero sin
// descartar píxeles nublados.
var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(parcelas)
  .filterDate(startDate, endDate);

// ---------------------------------------------------------------------------
// 4. CALCULAR NDRE (bandas B5 y B8 escaladas /10000)
// ---------------------------------------------------------------------------
function calcularNDRE(image) {
  var b8 = image.select('B8').divide(10000);
  var b5 = image.select('B5').divide(10000);
  // NDRE = (NIR - RedEdge) / (NIR + RedEdge)
  var ndre = b8.subtract(b5).divide(b8.add(b5)).rename('NDRE');
  return image.addBands(ndre).copyProperties(image, ['system:time_start']);
}

// Colección solo con banda NDRE, clip a parcelas para rendimiento
var ndreCol = s2.map(calcularNDRE).select('NDRE').map(function(img) {
  return img.clip(parcelas);
});

// ---------------------------------------------------------------------------
// 5. PREPARAR DATOS PARA EL SLIDER
// ---------------------------------------------------------------------------
var ndreList = ndreCol.toList(ndreCol.size());
var timestamps = ndreCol.aggregate_array('system:time_start');

// Array client-side de fechas (evita llamadas al servidor en cada cambio)
var fechas = [];
var numImagenes = 0;

timestamps.evaluate(function(ts) {
  fechas = ts.map(function(t) {
    var d = new Date(t);
    var yyyy = d.getFullYear();
    var mm = String(d.getMonth() + 1).padStart(2, '0');
    var dd = String(d.getDate()).padStart(2, '0');
    return yyyy + '-' + mm + '-' + dd;
  });
  numImagenes = fechas.length;
  if (numImagenes > 0) {
    // Configurar slider con el rango real
    slider.setMax(numImagenes - 1);
    // Actualizar etiqueta con la primera fecha
    lblFecha.setValue('Fecha: ' + fechas[0]);
  }
});

// ---------------------------------------------------------------------------
// 6. CONSTRUIR INTERFAZ DE USUARIO
// ---------------------------------------------------------------------------

// 6a. Mapa
var mapa = ui.Map();
mapa.setOptions('SATELLITE');
mapa.centerObject(parcelas, 14);

// Capa NDRE inicial (primera imagen)
mapa.addLayer(ee.Image(ndreList.get(0)), visParams, 'NDRE');
// Capa de parcelas (siempre visible)
mapa.addLayer(parcelas, {color: 'red'}, 'Parcelas');

// 6b. Slider de fechas (max se actualiza cuando llegue el conteo real)
var slider = ui.Slider(0, 100, 0, 1);

// 6c. Etiqueta de fecha
var lblFecha = ui.Label('Fecha: cargando...');

// 6d. Botón Play / Pause
var reproduciendo = false;
var intervaloId = null;
var btnPlay = ui.Button('▶ Play');

function actualizarMapa(indice) {
  var i = Math.round(Number(indice));
  // Clamp a rango válido
  if (i < 0) i = 0;
  if (i >= fechas.length) i = fechas.length - 1;

  var img = ee.Image(ndreList.get(i));
  mapa.layers().get(0).setEeObject(img, visParams);

  if (fechas.length > i) {
    lblFecha.setValue('Fecha: ' + fechas[i]);
  }
}

slider.onChange(actualizarMapa);

function togglePlay() {
  reproduciendo = !reproduciendo;
  if (reproduciendo) {
    btnPlay.setLabel('⏸ Pause');
    intervaloId = ui.util.setInterval(function() {
      var val = slider.getValue();
      var maxVal = numImagenes - 1;
      if (maxVal <= 0) return;
      if (val >= maxVal) {
        slider.setValue(0);
      } else {
        slider.setValue(val + 1);
      }
    }, 600); // 600 ms entre imágenes
  } else {
    btnPlay.setLabel('▶ Play');
    if (intervaloId !== null) {
      ui.util.clearInterval(intervaloId);
      intervaloId = null;
    }
  }
}

btnPlay.onClick(togglePlay);

// 6e. Panel de control
var panelControl = ui.Panel({
  widgets: [
    ui.Panel({
      widgets: [btnPlay, lblFecha],
      layout: ui.Panel.Layout.flow('horizontal'),
      style: {margin: '4px 0px'}
    }),
    slider
  ],
  layout: ui.Panel.Layout.flow('vertical'),
  style: {
    position: 'bottom-center',
    padding: '10px',
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    width: '80%',
    border: '1px solid #ccc',
    borderRadius: '8px'
  }
});

mapa.add(panelControl);

// ---------------------------------------------------------------------------
// 7. INFORMACIÓN EN CONSOLA
// ---------------------------------------------------------------------------
print('✅ Visualizador NDRE - Imágenes crudas sin filtrar');
print('📅 Rango: ' + startDate + ' a ' + endDate);
ndreCol.size().evaluate(function(n) {
  print('🛰️ Imágenes disponibles: ' + n);
});
print('');
print('📖 Cómo usar:');
print('  1. Slider → navegar entre fechas');
print('  2. Play ▶ → animación automática');
print('  3. Zoom/pan en el mapa');
print('');
print('📖 Cómo publicar la App:');
print('  1. Botón "Apps" (arriba derecha) → "New App"');
print('  2. Seleccionar este script');
print('  3. Hacer clic en "Publish"');
print('  4. Copiar el link y compartirlo');
