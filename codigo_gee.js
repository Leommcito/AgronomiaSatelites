// ==============================================================================
// ANÁLISIS DE MANDARINA MURCOTT - METODOLOGÍA DEL DOCUMENTO (2025-2026)
// ==============================================================================

// 0. PARÁMETROS CONFIGURABLES
var LAI_factor = 0.15;
var Cab_factor = 2;
var kc_slope = 1.15;
var kc_intercept = 0.1;
var sg_window = 5;
var sg_degree = 2;

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

  // NDVI binary mask para filtrado de vegetación únicamente (NO estimación biofísica)
  var ndviMask = imgScaled.normalizedDifference(['B8', 'B4']).rename('NDVI_Mask');

  // Índice NDRE para seguimiento visual y validación cruzada
  var ndre = imgScaled.normalizedDifference(['B8', 'B5']).rename('NDRE');

  // Posición del Borde Rojo (S2REP) - Fórmula ESTÁNDAR de interpolación lineal
  var denom = b6.subtract(b5);
  var s2rep = imgScaled.expression(
    '705 + 35 * (((B4+B7)/2 - B5) / (B6 - B5))',
    {'B4': b4, 'B5': b5, 'B6': b6, 'B7': b7}
  ).rename('S2REP');
  
  // Edge case: null S2REP skip pixel (evitar división por cero)
  var s2repValid = s2rep.updateMask(denom.abs().gt(0.0001));

  // Modelado de Clorofila (Cab) y LAI basado en la sensibilidad del S2REP (parámetros configurables)
  var cab = s2repValid.subtract(700).multiply(Cab_factor).rename('Cab_RedEdge');
  var laiRedEdge = s2repValid.subtract(700).multiply(LAI_factor).rename('LAI_RedEdge');

  // MSAVI2 (Mitigación de ruido de fondo / maleza)
  var msavi2 = imgScaled.expression(
    '(2 * NIR + 1 - sqrt(pow((2 * NIR + 1), 2) - 8 * (NIR - RED))) / 2', 
    {'NIR': b8, 'RED': b4}
  ).rename('MSAVI2');

  // Kc Actual (Coeficiente de Cultivo basado en el MSAVI2 purificado, parámetros configurables)
  var kc = msavi2.multiply(kc_slope).add(kc_intercept).rename('Kc_Actual');

  return image.addBands([ndviMask, ndre, s2repValid, cab, laiRedEdge, msavi2, kc])
              .copyProperties(image, ['system:time_start']);
}

var coleccionProcesada = s2Vinculada.map(enmascararNubesDobleFiltro)
                                    .map(calcularMetricas)
                                    .select(['NDVI_Mask', 'NDRE', 'LAI_RedEdge', 'Cab_RedEdge', 'Kc_Actual']);

// ==============================================================================
// 4. RECONSTRUCCIÓN TEMPORAL SEMANAL Y ALERTA DE ESTRÉS (GAP-FILLING SAVITZKY-GOLAY)
// ==============================================================================
// Calcular la media y desviación estándar histórica para LAI y Cab (Alerta Temprana Fitosanitaria)
var imgPromedioCab = coleccionProcesada.select('Cab_RedEdge').mean().rename('Cab_Mean');
var imgStdDevCab = coleccionProcesada.select('Cab_RedEdge').reduce(ee.Reducer.stdDev()).rename('Cab_Std');
var imgPromedioLai = coleccionProcesada.select('LAI_RedEdge').mean().rename('LAI_Mean');
var imgStdDevLai = coleccionProcesada.select('LAI_RedEdge').reduce(ee.Reducer.stdDev()).rename('LAI_Std');

var diasTotal = ee.Date(endDate).difference(ee.Date(startDate), 'day');
var semanasTotal = ee.Number(diasTotal).divide(7).int();
var listaSemanas = ee.List.sequence(0, semanasTotal);

// Crear composites semanales regulares
var weeklyComposites = ee.ImageCollection.fromImages(
  listaSemanas.map(function(w) {
    var inicioSemana = ee.Date(startDate).advance(w, 'week');
    var finSemana = inicioSemana.advance(1, 'week');
    var colSemana = coleccionProcesada.filterDate(inicioSemana, finSemana);
    var hasData = colSemana.size().gt(0);
    
    // Edge case: zero-size weeks flagged as interpolated
    var composite = ee.Image(ee.Algorithms.If(
      hasData,
      colSemana.median(),
      ee.Image.constant(0).rename(['NDVI_Mask', 'NDRE', 'LAI_RedEdge', 'Cab_RedEdge', 'Kc_Actual']).updateMask(0)
    )).set('system:time_start', inicioSemana.millis())
      .set('week', w)
      .set('has_data', hasData)
      .set('interpolated', hasData.not());
    
    return composite;
  })
);

// Savitzky-Golay 5-point quadratic smoothing coefficients: [-3,12,17,12,-3]/35
// (sg_window=5, sg_degree=2)
var sgCoeffs = ee.List([-3, 12, 17, 12, -3]).map(function(c) {
  return ee.Number(c).divide(35);
});

// Temporal join for ±2 weeks (5-point window)
var sgTimeFilter = ee.Filter.maxDifference({
  difference: 2 * 7 * 24 * 60 * 60 * 1000, // 2 weeks in milliseconds
  leftField: 'system:time_start',
  rightField: 'system:time_start'
});

var sgJoin = ee.Join.saveAll({
  matchesKey: 'neighbors',
  ordering: 'system:time_start',
  ascending: true
});

var joinedWeekly = sgJoin.apply(weeklyComposites, weeklyComposites, sgTimeFilter);

var sgSmoothed = joinedWeekly.map(function(image) {
  var neighbors = ee.List(image.get('neighbors'));
  var n = neighbors.size();
  var week = ee.Number(image.get('week'));
  var hasData = ee.Number(image.get('has_data')).eq(1);
  
  // Edge case: boundary weeks use wider window (fallback to median of neighbors)
  var isBoundary = week.lt(2).or(week.gt(semanasTotal.subtract(3)));
  
  var smoothed = ee.Image(ee.Algorithms.If(
    n.gte(5).and(isBoundary.not()).and(hasData),
    // Apply Savitzky-Golay coefficients explicitly (equivalente a reduceNeighborhood temporal)
    (function() {
      var w0 = ee.Number(sgCoeffs.get(0));
      var w1 = ee.Number(sgCoeffs.get(1));
      var w2 = ee.Number(sgCoeffs.get(2));
      var w3 = ee.Number(sgCoeffs.get(3));
      var w4 = ee.Number(sgCoeffs.get(4));
      
      var img0 = ee.Image(neighbors.get(0)).multiply(w0);
      var img1 = ee.Image(neighbors.get(1)).multiply(w1);
      var img2 = ee.Image(neighbors.get(2)).multiply(w2);
      var img3 = ee.Image(neighbors.get(3)).multiply(w3);
      var img4 = ee.Image(neighbors.get(4)).multiply(w4);
      
      return img0.add(img1).add(img2).add(img3).add(img4);
    })(),
    // Fallback: median of available neighbors (wider window for boundaries)
    ee.ImageCollection(neighbors).median()
  ));
  
  return smoothed
    .set('system:time_start', image.get('system:time_start'))
    .set('week', week)
    .set('interpolated', image.get('interpolated'))
    .set('has_data', image.get('has_data'));
});

// Generar la serie continua (1 dato regularizado por semana) con estadísticas históricas
var serieSemanal = sgSmoothed.map(function(image) {
  var inicioSemana = ee.Date(image.get('system:time_start'));
  
  // Anexar memoria histórica para comparar
  var imgConHistoria = image.addBands([imgPromedioCab, imgStdDevCab, imgPromedioLai, imgStdDevLai]);

  var estadisticas = imgConHistoria.reduceRegions({
    collection: parcelas,
    reducer: ee.Reducer.mean(),
    scale: 10
  });

  return estadisticas.map(function(f) {
    // Sistema de Alerta Temprana de 3 niveles (Normal, Precaución, Alerta Crítica)
    // Basado en z-score de LAI_RedEdge Y Cab_RedEdge
    var cabActual = ee.Number(f.get('Cab_RedEdge'));
    var laiActual = ee.Number(f.get('LAI_RedEdge'));
    var cabMean = ee.Number(f.get('Cab_Mean'));
    var cabStd = ee.Number(f.get('Cab_Std'));
    var laiMean = ee.Number(f.get('LAI_Mean'));
    var laiStd = ee.Number(f.get('LAI_Std'));
    
    var zCab = cabActual.subtract(cabMean).divide(cabStd).abs();
    var zLai = laiActual.subtract(laiMean).divide(laiStd).abs();
    var zMax = zCab.max(zLai);
    
    var estres = ee.Algorithms.If(
      zMax.gte(2), 'Alerta Crítica',
      ee.Algorithms.If(zMax.gte(1), 'Precaución', 'Normal')
    );

    return ee.Feature(null, {
      'Fecha_Semanal': inicioSemana.format('YYYY-MM-dd'),
      'ID_Parcela': f.get('name'), 
      'LAI_RedEdge': f.get('LAI_RedEdge'),
      'Cab_RedEdge': cabActual,
      'Kc_Actual': f.get('Kc_Actual'),
      'Flag_Interpolacion': ee.Algorithms.If(image.get('interpolated'), 1, 0), // 0=Real, 1=Interpolado
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
  // Exportar el CSV exactamente con la estructura demandada (7 columnas)
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

// ==============================================================================
// 7. VALIDACIÓN POR CONSOLA (PRINT)
// ==============================================================================
print('Image count before filter:', s2.filterBounds(parcelas).filterDate(startDate, endDate).size());
print('Image count after filter:', coleccionProcesada.size());

// NDRE median for parcel 1
var parcel1 = parcelas.first();
var ndreMedianP1 = coleccionProcesada.select('NDRE').median().reduceRegion({
  reducer: ee.Reducer.median(),
  geometry: parcel1.geometry(),
  scale: 10
});
print('NDRE median Parcel 1:', ndreMedianP1);

// LAI/Cab/Kc ranges
var ranges = coleccionProcesada.select(['LAI_RedEdge', 'Cab_RedEdge', 'Kc_Actual']).reduce(ee.Reducer.minMax());
print('LAI/Cab/Kc ranges:', ranges);

// Interpolated weeks count
var interpolatedCount = serieLimpia.filter(ee.Filter.eq('Flag_Interpolacion', 1)).size();
print('Interpolated weeks count:', interpolatedCount);

// Alert counts by level
var alertCounts = serieLimpia.reduceColumns({
  selectors: ['Alerta_Estres'],
  reducer: ee.Reducer.frequencyHistogram()
});
print('Alert counts by level:', alertCounts);

print('✅ Metodología completa implementada. Revisa la pestaña Tasks.');
