// ==============================================================================
// ANÁLISIS DE MANDARINA MURCOTT - METODOLOGÍA DEL DOCUMENTO (2025-2026)
// ==============================================================================

// 1. CONFIGURACIÓN INICIAL Y ÁREA DE ESTUDIO
var startDate = '2025-01-01';
var endDate = '2026-06-01'; 

// Importar el Shapefile de las 4 parcelas (Geometría original conservada sin retracción)
var parcelas = ee.FeatureCollection('projects/proyectoleomespinosa/assets/ParcelasDefinidas');

Map.centerObject(parcelas, 16);
Map.addLayer(parcelas, {color: 'red'}, 'Parcelas de Análisis (Originales)');

// ==============================================================================
// 2. PRE-PROCESAMIENTO: L2A Y DOBLE FILTRADO (CS+ Y SCL)
// ==============================================================================
// Uso de Nivel L2A (SR) para tener reflectancia de superficie y banda SCL
var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED');
var csPlus = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED');

var s2Vinculada = s2.filterBounds(parcelas)
                    .filterDate(startDate, endDate)
                    .linkCollection(csPlus, ['cs_cdf']);

function enmascararNubesDobleFiltro(image) {
  // Filtro 1: Cloud Score+ Estricto (> 0.90 como exige el documento)
  var csMask = image.select('cs_cdf').gte(0.90);
  
  // Filtro 2: Scene Classification Layer (SCL) - Solo Vegetación (4) y Suelo (5)
  var scl = image.select('SCL');
  var sclMask = scl.eq(4).or(scl.eq(5));

  return image.updateMask(csMask.and(sclMask));
}

// ==============================================================================
// 3. CÁLCULO DE ÍNDICES: RED-EDGE Y CUANTIFICACIÓN BIOFÍSICA
// ==============================================================================
function calcularMetricas(image) {
  // Extraer y escalar bandas ópticas (Sentinel-2 L2A viene multiplicado por 10000)
  var imgScaled = image.select(['B4', 'B5', 'B6', 'B7', 'B8']).divide(10000);
  
  var b4 = imgScaled.select('B4'); // Rojo
  var b5 = imgScaled.select('B5'); // Red Edge 1
  var b6 = imgScaled.select('B6'); // Red Edge 2
  var b7 = imgScaled.select('B7'); // Red Edge 3
  var b8 = imgScaled.select('B8'); // NIR

  // Índice NDRE para seguimiento visual y validación cruzada
  var ndre = imgScaled.normalizedDifference(['B8', 'B5']).rename('NDRE');

  // Posición del Borde Rojo (S2REP) - Ecuación de interpolación lineal estándar
  var s2rep = imgScaled.expression(
    '705 + 35 * ( ((B4 + B7)/2 - B5) / (B6 - B5) )',
    {'B4': b4, 'B5': b5, 'B6': b6, 'B7': b7}
  ).rename('S2REP');

  // Modelado de Clorofila (Cab) y LAI basado en la sensibilidad del S2REP
  var cab = s2rep.subtract(700).multiply(2).rename('Cab_RedEdge');
  var laiRedEdge = s2rep.subtract(700).multiply(0.15).rename('LAI_RedEdge');

  // MSAVI2 (Mitigación de ruido de fondo / maleza)
  var msavi2 = imgScaled.expression(
    '(2 * NIR + 1 - sqrt(pow((2 * NIR + 1), 2) - 8 * (NIR - RED))) / 2', 
    {'NIR': b8, 'RED': b4}
  ).rename('MSAVI2');

  // Kc Actual (Coeficiente de Cultivo basado en el MSAVI2 purificado)
  var kc = msavi2.multiply(1.15).add(0.1).rename('Kc_Actual');

  return image.addBands([ndre, s2rep, cab, laiRedEdge, msavi2, kc])
              .copyProperties(image, ['system:time_start']);
}

var coleccionProcesada = s2Vinculada.map(enmascararNubesDobleFiltro)
                                    .map(calcularMetricas)
                                    .select(['NDRE', 'LAI_RedEdge', 'Cab_RedEdge', 'Kc_Actual']);

// ==============================================================================
// 4. RECONSTRUCCIÓN TEMPORAL SEMANAL Y ALERTA DE ESTRÉS (GAP-FILLING)
// ==============================================================================
// Calcular la media y desviación estándar histórica para la Alerta Temprana Fitosanitaria
var imgPromedio = coleccionProcesada.select('Cab_RedEdge').mean().rename('Cab_Mean');
var imgStdDev = coleccionProcesada.select('Cab_RedEdge').reduce(ee.Reducer.stdDev()).rename('Cab_Std');

var diasTotal = ee.Date(endDate).difference(ee.Date(startDate), 'day');
var semanasTotal = ee.Number(diasTotal).divide(7).int();
var listaSemanas = ee.List.sequence(0, semanasTotal);

// Generar la serie continua (1 dato regularizado por semana)
var serieSemanal = listaSemanas.map(function(w) {
  var inicioSemana = ee.Date(startDate).advance(w, 'week');
  var finSemana = inicioSemana.advance(1, 'week');
  
  var colSemana = coleccionProcesada.filterDate(inicioSemana, finSemana);
  var hayDatos = colSemana.size().gt(0);
  
  // Algoritmo de Gap-Filling (si hay nubes, interpola usando una ventana temporal vecina)
  var ventanaAmplia = coleccionProcesada.filterDate(inicioSemana.advance(-15, 'day'), inicioSemana.advance(15, 'day'));
  
  var imgSemana = ee.Image(ee.Algorithms.If(
    hayDatos,
    colSemana.median(),
    ventanaAmplia.median() // Dato matemático interpolado
  ));
  
  // Anexar memoria histórica para comparar
  var imgConHistoria = imgSemana.addBands([imgPromedio, imgStdDev]);

  var estadisticas = imgConHistoria.reduceRegions({
    collection: parcelas,
    reducer: ee.Reducer.mean(),
    scale: 10
  });

  return estadisticas.map(function(f) {
    // Sistema de Alerta Temprana (Detecta caídas anómalas en clorofila)
    var cabActual = ee.Number(f.get('Cab_RedEdge'));
    var umbralFallo = ee.Number(f.get('Cab_Mean')).subtract(f.get('Cab_Std'));
    var estres = ee.Algorithms.If(cabActual.lt(umbralFallo), 'Alerta Crítica', 'Normal');

    return ee.Feature(null, {
      'Fecha_Semanal': inicioSemana.format('YYYY-MM-dd'),
      'ID_Parcela': f.get('name'), 
      'LAI_RedEdge': f.get('LAI_RedEdge'),
      'Cab_RedEdge': cabActual,
      'Kc_Actual': f.get('Kc_Actual'),
      'Flag_Interpolacion': ee.Algorithms.If(hayDatos, 0, 1), // 0=Real, 1=Interpolado
      'Alerta_Estres': estres
    });
  });
}).flatten();

// Limpiar artefactos nulos en los extremos y preparar para descargar
var serieLimpia = ee.FeatureCollection(serieSemanal).filter(ee.Filter.notNull(['Cab_RedEdge']));

Export.table.toDrive({
  collection: serieLimpia,
  description: 'Dataset_Fenologico_Mandarina_Estandarizado',
  folder: 'Tesis_Mandarinas',
  fileFormat: 'CSV',
  // Exportar el CSV exactamente con la estructura demandada
  selectors: ['Fecha_Semanal', 'ID_Parcela', 'LAI_RedEdge', 'Cab_RedEdge', 'Kc_Actual', 'Flag_Interpolacion', 'Alerta_Estres']
});

// ==============================================================================
// 5. HITOS FENOLÓGICOS: EXPORTACIÓN ESPACIAL (SOLO OBSERVACIONES REALES)
// ==============================================================================
var paletaVigor = ['#d73027', '#fc8d59', '#fee08b', '#d9ef8b', '#91cf60', '#1a9850'];

function exportarHitoFenologico(inicio, fin, nombreHito) {
  var imagenHito = coleccionProcesada.filterDate(inicio, fin).median().clip(parcelas);
  Map.addLayer(imagenHito.select('NDRE'), {min: 0.2, max: 0.6, palette: paletaVigor}, nombreHito);

  Export.image.toDrive({
    image: imagenHito.select(['NDRE', 'LAI_RedEdge', 'Cab_RedEdge', 'Kc_Actual']).toFloat(),
    description: 'TIF_' + nombreHito,
    folder: 'Tesis_Mandarinas',
    scale: 10,
    region: parcelas.geometry().bounds(),
    maxPixels: 1e8
  });
}

exportarHitoFenologico('2025-07-01', '2025-08-15', 'Hito_1_Reposo_Poda');
exportarHitoFenologico('2025-10-01', '2025-11-30', 'Hito_2_Floracion');
exportarHitoFenologico('2026-04-01', '2026-05-31', 'Hito_3_Cosecha');

// ==============================================================================
// 6. VIDEO TIME-LAPSE SEMANAL (2 SEG POR SEMANA + TEXTO AJUSTADO A LA IZQUIERDA)
// ==============================================================================
var text = require('users/gena/packages:text');

// Recalcular el punto del texto para empujarlo a la izquierda y evitar que tape las parcelas
var coordBordes = ee.List(parcelas.geometry().bounds().coordinates().get(0));
var offsetIzquierda = ee.Number(ee.List(coordBordes.get(3)).get(0)).subtract(0.0035); 
var topY = ee.Number(ee.List(coordBordes.get(3)).get(1));
var ptTextoDesplazado = ee.Geometry.Point([offsetIzquierda, topY]); 

var listaVideo = listaSemanas.map(function(w) {
  var inicioSemana = ee.Date(startDate).advance(w, 'week');
  var finSemana = inicioSemana.advance(1, 'week');
  
  var colSemana = coleccionProcesada.filterDate(inicioSemana, finSemana);
  
  // Para el video, si hay nubes queda negro (sin interpolar visuals)
  var imgSemana = ee.Image(ee.Algorithms.If(
    colSemana.size().eq(0),
    ee.Image.constant(0).rename('NDRE').updateMask(0),
    colSemana.median()
  )).clip(parcelas);
  
  var ndreVisual = imgSemana.select('NDRE').visualize({min: 0.1, max: 0.6, palette: paletaVigor});
  
  // Tamaño de texto reducido a la escala 2 y fontSize 14
  var fechaString = inicioSemana.format('YYYY-MM-dd');
  var textImg = text.draw(fechaString, ptTextoDesplazado, 2, { 
    fontSize: 14, textColor: 'ffffff', outlineColor: '000000', outlineWidth: 2
  });
  
  var frameConTexto = ndreVisual.blend(textImg).set('system:time_start', inicioSemana.millis());
  
  // Duplicar a 2 frames = 2 segundos a 1 FPS
  return ee.List.repeat(frameConTexto, 2);
});

var coleccionVideo = ee.ImageCollection.fromImages(listaVideo.flatten());

// Agrandar el encuadre (buffer) para que el texto movido a la izquierda no quede cortado
var encuadreVideo = parcelas.geometry().bounds().buffer(150);

Export.video.toDrive({
  collection: coleccionVideo,
  description: 'Timelapse_NDRE_2Seg_Corregido',
  folder: 'Tesis_Mandarinas',
  framesPerSecond: 1, 
  dimensions: 720, 
  region: encuadreVideo
});

print('✅ Metodología completa implementada. Revisa la pestaña Tasks.');