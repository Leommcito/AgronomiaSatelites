// ==============================================================================
// CSV SEMANAL - SERIE FENOLÓGICA ESTANDARIZADA (2025-2026)
// ==============================================================================
// Script independiente. Genera el CSV semanal con datos suavizados por
// Savitzky-Golay + alerta de estrés + flag de interpolación.
//
// EXPORTA: Dataset_Fenologico_Mandarina_Estandarizado
//
// Este script es una versión autónoma del módulo semanal de codigo_gee.js
// ==============================================================================

// ---------------------------------------------------------------------------
// 0. PARÁMETROS CONFIGURABLES
// ---------------------------------------------------------------------------
var LAI_factor = 0.15;
var Cab_factor = 2;
var kc_slope = 1.15;
var kc_intercept = 0.1;
var sg_window = 5;
var sg_degree = 2;

// ---------------------------------------------------------------------------
// 1. CONFIGURACIÓN INICIAL Y ÁREA DE ESTUDIO
// ---------------------------------------------------------------------------
var startDate = '2025-01-01';
var endDate = '2026-06-01'; 

var parcelas = ee.FeatureCollection('projects/proyectoleomespinosa/assets/ParcelasDefinidas');

// ---------------------------------------------------------------------------
// 2. PRE-PROCESAMIENTO: L2A Y DOBLE FILTRADO (CS+ Y SCL)
// ---------------------------------------------------------------------------
var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED');
var csPlus = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED');

var s2Vinculada = s2.filterBounds(parcelas)
                    .filterDate(startDate, endDate)
                    .linkCollection(csPlus, ['cs_cdf']);

function enmascararNubesDobleFiltro(image) {
  var csMask = image.select('cs_cdf').gte(0.90);
  var scl = image.select('SCL');
  var sclMask = scl.eq(4).or(scl.eq(5));
  return image.updateMask(csMask.and(sclMask));
}

// ---------------------------------------------------------------------------
// 3. CÁLCULO DE ÍNDICES: RED-EDGE Y CUANTIFICACIÓN BIOFÍSICA
// ---------------------------------------------------------------------------
function calcularMetricas(image) {
  var imgScaled = image.select(['B4', 'B5', 'B6', 'B7', 'B8']).divide(10000);
  
  var b4 = imgScaled.select('B4');
  var b5 = imgScaled.select('B5');
  var b6 = imgScaled.select('B6');
  var b7 = imgScaled.select('B7');
  var b8 = imgScaled.select('B8');

  var ndviMask = imgScaled.normalizedDifference(['B8', 'B4']).rename('NDVI_Mask');
  var ndre = imgScaled.normalizedDifference(['B8', 'B5']).rename('NDRE');

  var denom = b6.subtract(b5);
  var s2rep = imgScaled.expression(
    '705 + 35 * (((B4+B7)/2 - B5) / (B6 - B5))',
    {'B4': b4, 'B5': b5, 'B6': b6, 'B7': b7}
  ).rename('S2REP');
  
  var s2repValid = s2rep.updateMask(denom.abs().gt(0.0001));

  var cab = s2repValid.subtract(700).multiply(Cab_factor).rename('Cab_RedEdge');
  var laiRedEdge = s2repValid.subtract(700).multiply(LAI_factor).rename('LAI_RedEdge');

  var msavi2 = imgScaled.expression(
    '(2 * NIR + 1 - sqrt(pow((2 * NIR + 1), 2) - 8 * (NIR - RED))) / 2', 
    {'NIR': b8, 'RED': b4}
  ).rename('MSAVI2');

  var kc = msavi2.multiply(kc_slope).add(kc_intercept).rename('Kc_Actual');

  return image.addBands([ndviMask, ndre, s2repValid, cab, laiRedEdge, msavi2, kc])
              .copyProperties(image, ['system:time_start']);
}

var coleccionProcesada = s2Vinculada.map(enmascararNubesDobleFiltro)
                                    .map(calcularMetricas)
                                    .select(['NDVI_Mask', 'NDRE', 'S2REP', 'LAI_RedEdge', 'Cab_RedEdge', 'MSAVI2', 'Kc_Actual']);

// ---------------------------------------------------------------------------
// 4. RECONSTRUCCIÓN TEMPORAL SEMANAL Y ALERTA DE ESTRÉS
// ---------------------------------------------------------------------------
var imgPromedioCab = coleccionProcesada.select('Cab_RedEdge').mean().rename('Cab_Mean');
var imgStdDevCab = coleccionProcesada.select('Cab_RedEdge').reduce(ee.Reducer.stdDev()).rename('Cab_Std');
var imgPromedioLai = coleccionProcesada.select('LAI_RedEdge').mean().rename('LAI_Mean');
var imgStdDevLai = coleccionProcesada.select('LAI_RedEdge').reduce(ee.Reducer.stdDev()).rename('LAI_Std');

var diasTotal = ee.Date(endDate).difference(ee.Date(startDate), 'day');
var semanasTotal = ee.Number(diasTotal).divide(7).int();
var listaSemanas = ee.List.sequence(0, semanasTotal);

// 4a. Composites semanales
var weeklyComposites = ee.ImageCollection.fromImages(
  listaSemanas.map(function(w) {
    var inicioSemana = ee.Date(startDate).advance(w, 'week');
    var finSemana = inicioSemana.advance(1, 'week');
    var colSemana = coleccionProcesada.filterDate(inicioSemana, finSemana);
    var hasData = colSemana.size().gt(0);
    
    var composite = ee.Image(ee.Algorithms.If(
      hasData,
      colSemana.median(),
      ee.Image.constant([0, 0, 0, 0, 0, 0, 0]).rename(['NDVI_Mask', 'NDRE', 'S2REP', 'LAI_RedEdge', 'Cab_RedEdge', 'MSAVI2', 'Kc_Actual']).updateMask(0)
    )).set('system:time_start', inicioSemana.millis())
      .set('week', w)
      .set('has_data', hasData)
      .set('interpolated', hasData.not());

    var pixelCount = composite.select('NDRE').reduceRegion({
      reducer: ee.Reducer.count(),
      geometry: parcelas.geometry(),
      scale: 10,
      maxPixels: 1e5
    });
    var hasRealData = ee.Number(pixelCount.get('NDRE')).gt(0);
    composite = composite.set('has_real_data', hasRealData);
    
    return composite;
  })
);

// 4b. Savitzky-Golay smoothing
var sgSmoothed = ee.ImageCollection.fromImages(
  listaSemanas.map(function(w) {
    var inicioSemana = ee.Date(startDate).advance(w, 'week');
    var weekNum = ee.Number(w);
    var isBoundary = weekNum.lt(2).or(weekNum.gt(semanasTotal.subtract(3)));
    
    var winStart = inicioSemana.advance(-2, 'week');
    var winEnd = inicioSemana.advance(2, 'week');
    var windowCol = weeklyComposites.filterDate(winStart, winEnd);
    var nWin = windowCol.size();
    var semanaImgData = weeklyComposites.filterDate(inicioSemana, inicioSemana.advance(1, 'week')).first();
    var hasData = ee.Number(ee.Image(semanaImgData).get('has_real_data')).gt(0);
    
    var c0 = -3/35, c1 = 12/35, c2 = 17/35, c3 = 12/35, c4 = -3/35;
    var imgList = windowCol.toList(5);
    
    var smoothed = ee.Image(ee.Algorithms.If(
      nWin.gte(5).and(isBoundary.not()),
      ee.Image(imgList.get(0)).multiply(c0).add(
        ee.Image(imgList.get(1)).multiply(c1)).add(
        ee.Image(imgList.get(2)).multiply(c2)).add(
        ee.Image(imgList.get(3)).multiply(c3)).add(
        ee.Image(imgList.get(4)).multiply(c4)),
      windowCol.median()
    ));
    
    return smoothed
      .set('system:time_start', inicioSemana.millis())
      .set('week', w)
      .set('interpolated', hasData.not());
  })
);

// 4c. Generar serie semanal con estadísticas
var serieSemanal = sgSmoothed.map(function(image) {
  var inicioSemana = ee.Date(image.get('system:time_start'));
  
  var imgConHistoria = image.addBands([imgPromedioCab, imgStdDevCab, imgPromedioLai, imgStdDevLai]);

  var estadisticas = imgConHistoria.reduceRegions({
    collection: parcelas,
    reducer: ee.Reducer.mean(),
    scale: 10
  });

  return estadisticas.map(function(f) {
    var cabActual = ee.Number(f.get('Cab_RedEdge'));
    var laiActual = ee.Number(f.get('LAI_RedEdge'));
    var cabMean = ee.Number(f.get('Cab_Mean'));
    var cabStd = ee.Number(f.get('Cab_Std'));
    var laiMean = ee.Number(f.get('LAI_Mean'));
    var laiStd = ee.Number(f.get('LAI_Std'));
    
    var estres = ee.Algorithms.If(
      cabActual,
      ee.Algorithms.If(
        cabActual.subtract(cabMean).divide(cabStd).abs().max(
          laiActual.subtract(laiMean).divide(laiStd).abs()
        ).gte(2), 'Alerta Crítica',
        ee.Algorithms.If(
          cabActual.subtract(cabMean).divide(cabStd).abs().max(
            laiActual.subtract(laiMean).divide(laiStd).abs()
          ).gte(1), 'Precaución', 'Normal'
        )
      ),
      'Normal'
    );

    return ee.Feature(null, {
      'Fecha_Semanal': inicioSemana.format('YYYY-MM-dd'),
      'ID_Parcela': f.get('name'), 
      'LAI_RedEdge': f.get('LAI_RedEdge'),
      'Cab_RedEdge': cabActual,
      'Kc_Actual': f.get('Kc_Actual'),
      'Flag_Interpolacion': ee.Algorithms.If(image.get('interpolated'), 1, 0),
      'Alerta_Estres': estres,
      'NDRE': f.get('NDRE'),
      'MSAVI2': f.get('MSAVI2'),
      'S2REP': f.get('S2REP'),
      'NDVI': f.get('NDVI_Mask')
    });
  });
}).flatten();

// Limpiar artefactos nulos
var serieLimpia = ee.FeatureCollection(serieSemanal).filter(ee.Filter.notNull(['Cab_RedEdge']));

// ---------------------------------------------------------------------------
// 5. EXPORTACIÓN CSV SEMANAL
// ---------------------------------------------------------------------------
Export.table.toDrive({
  collection: serieLimpia,
  description: 'Dataset_Fenologico_Mandarina_Estandarizado',
  folder: 'Tesis_Mandarinas',
  fileFormat: 'CSV',
  selectors: ['Fecha_Semanal', 'ID_Parcela', 'LAI_RedEdge', 'Cab_RedEdge', 'Kc_Actual', 'Flag_Interpolacion', 'Alerta_Estres', 'NDRE', 'MSAVI2', 'S2REP', 'NDVI']
});

// ---------------------------------------------------------------------------
// 6. VALIDACIÓN POR CONSOLA
// ---------------------------------------------------------------------------
print('Image count before filter:', s2.filterBounds(parcelas).filterDate(startDate, endDate).size());
print('Image count after filter:', coleccionProcesada.size());
print('Interpolated weeks count:', serieLimpia.filter(ee.Filter.eq('Flag_Interpolacion', 1)).size());

var alertCounts = serieLimpia.reduceColumns({
  selectors: ['Alerta_Estres'],
  reducer: ee.Reducer.frequencyHistogram()
});
print('Alert counts by level:', alertCounts);

print('CSV semanal listo. Revisa la pestaña Tasks.');
