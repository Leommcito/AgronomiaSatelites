// =============================================================================
// CSV INDIVIDUAL - TODAS LAS IMÁGENES CON VALIDACIÓN DE NUBES (2025-2026)
// =============================================================================
// Script independiente. Genera un CSV con TODAS las imágenes Sentinel-2
// (incluso nubladas). Las métricas son null donde hay nubes.
// Las columnas de nubosidad explican el estado.
//
// EXPORTA: Dataset_Imagenes_Individuales_Con_Nubes
//
// Este script es una versión autónoma del módulo de nubes de codigo_gee.js
// =============================================================================

// ---------------------------------------------------------------------------
// 1. PARÁMETROS
// ---------------------------------------------------------------------------
var startDate = '2025-01-01';
var endDate = '2026-06-01';
var LAI_factor = 0.15;
var Cab_factor = 2;
var kc_slope = 1.15;
var kc_intercept = 0.1;

// ---------------------------------------------------------------------------
// 2. CARGAR PARCELAS Y SENTINEL-2 CON CLOUD SCORE+
// ---------------------------------------------------------------------------
var parcelas = ee.FeatureCollection(
  'projects/proyectoleomespinosa/assets/ParcelasDefinidas'
);

var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED');
var csPlus = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED');

var s2Vinculada = s2.filterBounds(parcelas)
                    .filterDate(startDate, endDate)
                    .linkCollection(csPlus, ['cs_cdf']);

// ---------------------------------------------------------------------------
// 3. GENERAR CSV CON MÉTRICAS + VALIDACIÓN DE NUBES
// ---------------------------------------------------------------------------
// Procesa TODAS las imágenes de s2Vinculada. Calcula métricas sobre la imagen
// cruda y luego aplica la máscara de nubes (null donde hay nubes).
// Las columnas cs_cdf_raw NO están enmascaradas para poder contar píxeles.
var csvCompleto = ee.FeatureCollection(
  s2Vinculada.map(function(img) {
    var fecha = ee.Date(img.get('system:time_start'));

    // Calcular métricas directamente sobre B4-B8 escaladas
    var b4 = img.select('B4').divide(10000);
    var b5 = img.select('B5').divide(10000);
    var b6 = img.select('B6').divide(10000);
    var b7 = img.select('B7').divide(10000);
    var b8 = img.select('B8').divide(10000);

    var ndvi = b8.subtract(b4).divide(b8.add(b4)).rename('NDVI_Mask');
    var ndre = b8.subtract(b5).divide(b8.add(b5)).rename('NDRE');
    var denom = b6.subtract(b5);
    var s2repExpr = b4.add(b7).divide(2).subtract(b5).divide(b6.subtract(b5));
    var s2repValid = s2repExpr.multiply(35).add(705).rename('S2REP')
      .updateMask(denom.abs().gt(0.0001));
    var cab = s2repValid.subtract(700).multiply(Cab_factor).rename('Cab_RedEdge');
    var lai = s2repValid.subtract(700).multiply(LAI_factor).rename('LAI_RedEdge');
    var msavi2Expr = b8.multiply(2).add(1).subtract(
      b8.multiply(2).add(1).pow(2).subtract(b8.subtract(b4).multiply(8)).sqrt()
    ).divide(2);
    var msavi2 = msavi2Expr.rename('MSAVI2');
    var kc = msavi2.multiply(kc_slope).add(kc_intercept).rename('Kc_Actual');

    var imgConMetricas = ee.Image(
      img.addBands([ndvi, ndre, s2repValid, cab, lai, msavi2, kc])
    ).copyProperties(img, ['system:time_start']);

    // Aplicar máscara de nubes (1 banda) - null donde hay nubes
    var mascara = img.select('cs_cdf').gte(0.90).and(
      img.select('SCL').eq(4).or(img.select('SCL').eq(5))
    );
    imgConMetricas = ee.Image(imgConMetricas).updateMask(mascara);

    // Agregar cs_cdf sin máscara para estadísticas de nubosidad
    imgConMetricas = imgConMetricas.addBands(
      img.select('cs_cdf').rename('cs_cdf_raw')
    );

    // Reducción por parcela: mean + count
    var stats = imgConMetricas.reduceRegions({
      collection: parcelas,
      reducer: ee.Reducer.mean().combine({
        reducer2: ee.Reducer.count(),
        sharedInputs: true
      }),
      scale: 10
    });

    return stats.map(function(f) {
      var pixClaros = ee.Number(f.get('NDRE_count'));
      var pixTotales = ee.Number(f.get('cs_cdf_raw_count'));
      var pixNublados = pixTotales.subtract(pixClaros);
      var porcClaros = ee.Number(ee.Algorithms.If(
        pixTotales.gt(0),
        pixClaros.divide(pixTotales).multiply(100),
        0
      ));

      var estado = ee.Algorithms.If(
        porcClaros.gte(70), 'Despejado',
        ee.Algorithms.If(porcClaros.gte(30), 'Parcialmente Nublado', 'Muy Nublado')
      );

      return ee.Feature(null, {
        'Fecha': fecha.format('YYYY-MM-dd'),
        'ID_Parcela': f.get('name'),
        'NDVI': f.get('NDVI_Mask_mean'),
        'NDRE': f.get('NDRE_mean'),
        'S2REP': f.get('S2REP_mean'),
        'LAI_RedEdge': f.get('LAI_RedEdge_mean'),
        'Cab_RedEdge': f.get('Cab_RedEdge_mean'),
        'MSAVI2': f.get('MSAVI2_mean'),
        'Kc_Actual': f.get('Kc_Actual_mean'),
        'Pixeles_Claros': pixClaros,
        'Pixeles_Totales': pixTotales,
        'Pixeles_Nublados': pixNublados,
        'Porcentaje_Claros': porcClaros,
        'Estado_Nubosidad': estado,
        'Cloud_Score_Medio': f.get('cs_cdf_raw_mean')
      });
    });
  })
).flatten();

// ---------------------------------------------------------------------------
// 4. EXPORTACIÓN CSV
// ---------------------------------------------------------------------------
Export.table.toDrive({
  collection: csvCompleto,
  description: 'Dataset_Imagenes_Individuales_Con_Nubes',
  folder: 'Tesis_Mandarinas',
  fileFormat: 'CSV',
  selectors: [
    'Fecha', 'ID_Parcela',
    'NDVI', 'NDRE', 'S2REP', 'LAI_RedEdge', 'Cab_RedEdge', 'MSAVI2', 'Kc_Actual',
    'Pixeles_Claros', 'Pixeles_Totales', 'Pixeles_Nublados', 'Porcentaje_Claros',
    'Estado_Nubosidad', 'Cloud_Score_Medio'
  ]
});

print('CSV individual con nubes listo. Revisa la pesta\u00f1a Tasks.');
print('Script independiente de csv_semanal.js y codigo_gee.js');
