# Plan: Corregir Flag_Interpolacion (siempre en 0)

## TL;DR

> **Problema**: `Flag_Interpolacion` siempre sale 0 porque el código revisa si hay imágenes en `coleccionProcesada`, pero esa colección SIEMPRE tiene imágenes (aunque los píxeles estén 100% enmascarados por nubes). Hay que contar píxeles válidos sobre las parcelas, no contar imágenes en la colección.
>
> **Solución**: Agregar `reduceRegion(ee.Reducer.count())` en `weeklyComposites` para contar píxeles no enmascarados. Usar ese conteo como flag de datos reales en `sgSmoothed`.
>
> **Archivos**: Solo `codigo_gee.js` — 2 cambios.

---

## Root Cause

La línea 114 del código actual:
```javascript
var hasData = colSemana.size().gt(0);
```

`coleccionProcesada` contiene TODAS las imágenes Sentinel-2 del período 2025-2026. Cada imagen existe, aunque el doble filtro (CS+ ≥ 0.90 + SCL {4,5}) haya enmascarado TODOS sus píxeles por nubosidad. `size()` nunca da 0 para semanas con pasadas del satélite (~1-2 por semana). Por eso todas las semanas se marcan como `hasData = true` → `Flag_Interpolacion = 0`.

---

## Cambio 1: `weeklyComposites` — Agregar conteo de píxeles válidos

**Ubicación**: Línea 124, DENTRO del bloque `set()` de propiedades del composite

**ANTES** (líneas 121-126):
```javascript
    )).set('system:time_start', inicioSemana.millis())
      .set('week', w)
      .set('has_data', hasData)
      .set('interpolated', hasData.not());
    
    return composite;
```

**DESPUÉS**:
```javascript
    )).set('system:time_start', inicioSemana.millis())
      .set('week', w)
      .set('has_data', hasData)
      .set('interpolated', hasData.not());

    // Contar pixeles validos sobre las parcelas para detectar semanas con datos reales
    var pixelCount = composite.select('NDRE').reduceRegion({
      reducer: ee.Reducer.count(),
      geometry: parcelas.geometry(),
      scale: 10,
      maxPixels: 1e5
    });
    var hasRealData = ee.Number(pixelCount.get('NDRE')).gt(0);
    composite = composite.set('has_real_data', hasRealData);
    
    return composite;
```

**Qué hace**: `reduceRegion(ee.Reducer.count())` cuenta cuántos píxeles NO están enmascarados sobre las 4 parcelas. Si el conteo es 0, todos los píxeles están nublados → no hay datos reales. Si es > 0, hay al menos un píxel válido.

**Performance**: `reduceRegion` dentro de un `.map()` es seguro en GEE (construye el árbol de expresión diferido). Con `maxPixels: 1e5` y área de ~2 ha a 10m (~2000 píxeles), es muy liviano.

---

## Cambio 2: `sgSmoothed` — Leer `has_real_data` del composite semanal

**Ubicación**: Líneas 145-147, DENTRO del `listaSemanas.map()` en sgSmoothed

**ANTES**:
```javascript
    // Usar coleccionProcesada ORIGINAL para detectar semanas sin datos reales
    var colSemanaOriginal = coleccionProcesada.filterDate(inicioSemana, inicioSemana.advance(1, 'week'));
    var hasData = colSemanaOriginal.size().gt(0);
```

**DESPUÉS**:
```javascript
    // Leer el flag de datos reales del composite semanal (conteo de pixeles validos)
    var semanaImgData = weeklyComposites.filterDate(inicioSemana, inicioSemana.advance(1, 'week')).first();
    var hasData = ee.Number(ee.Image(semanaImgData).get('has_real_data')).gt(0);
```

**Qué hace**: En lugar de preguntarle a `coleccionProcesada` si tiene imágenes (respuesta: siempre sí), le pregunta al composite semanal de `weeklyComposites` si tiene píxeles válidos (flag `has_real_data` computado en el Cambio 1).

**Nota**: `ee.Image(semanaImgData)` envuelve el elemento server-side en un `ee.Image` para poder llamar `.get()`.

---

## Verificación

Después de aplicar los cambios, ejecutar en GEE Code Editor:

1. **Console** → verificar que `Interpolated weeks count` es > 0
2. **Tasks** → exportar CSV
3. **Google Drive** → abrir `Dataset_Fenologico_Mandarina_Estandarizado.csv`
4. **Columna `Flag_Interpolacion`** → debe tener valores 0 Y 1:
   - `0` = semanas con al menos un píxel válido sobre las parcelas
   - `1` = semanas completamente nubladas (todos los píxeles enmascarados)

---

## Flujo Completo del Fix

```
weeklyComposites (cada semana):
  composite = median() de las imágenes filtradas de la semana
  → reduceRegion(ee.Reducer.count()) sobre NDRE en las parcelas
  → si count > 0 → has_real_data = true
  → si count = 0 → has_real_data = false (todo nublado)
  composite.set('has_real_data', hasRealData)

sgSmoothed (S-G suavizado, cada semana):
  semanaImgData = weeklyComposites.filterDate(semana).first()
  hasData = semanaImgData.get('has_real_data')  ← NUEVO: basado en píxeles
  → si hasData = true → interpolated = false → Flag = 0
  → si hasData = false → interpolated = true → Flag = 1

serieSemanal → CSV:
  Flag_Interpolacion = image.get('interpolated') ? 1 : 0
```
