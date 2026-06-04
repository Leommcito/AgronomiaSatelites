# Guía de Interpretación — Índices Espectrales Sentinel-2

## Mandarina Murcott — Jujuy, Argentina

---

## Estructura de salida

```
output/Imagenes/
├── MSAVI2/Abril2026/{PNG/, TIF/, estadisticas.csv}
├── S2REP/Abril2026/{PNG/, TIF/, estadisticas.csv}
├── LAI_RedEdge/Abril2026/{PNG/, TIF/, estadisticas.csv}
├── Cab_RedEdge/Abril2026/{PNG/, TIF/, estadisticas.csv}
└── Kc_Actual/Abril2026/{PNG/, TIF/, estadisticas.csv}
```

Cada carpeta contiene:
- **PNG/** — imágenes a color listas para visualizar
- **TIF/** — GeoTIFFs para usar en SIG
- **estadisticas.csv** — valores numéricos por parcela

---

## 1. MSAVI2 — Mapa de vigor vegetal

**Propósito**: Evalúa la cantidad y condición de la vegetación, minimizando el ruido del suelo entre las hileras.

| Detalle | Valor |
|---|---|
| Colormap | RdYlGn (Rojo ↔ Amarillo ↔ Verde) |
| Rango visual | 0.2 – 0.8 |
| Rango fisiológico | 0 – 1 |
| Fórmula | `(2×NIR+1 − √((2×NIR+1)² − 8×(NIR−RED))) / 2` |

### Paleta de colores

```
0.2 (rojo)  ──  0.4 (amarillo)  ──  0.6 (verde claro)  ──  0.8 (verde oscuro)
  suelo          vegetación         vegetación            vegetación
  desnudo        muy rala           moderada              muy densa
```

### Interpretación agronómica

| Rango | Color | Significado |
|---|---|---|
| < 0.3 | Rojo | Suelo desnudo, sin vegetación |
| 0.3 – 0.5 | Amarillo | Vegetación rala. En huertos jóvenes (3-4 años) con marco de 5.5m × 3.5m es esperable en las calles |
| 0.5 – 0.7 | Verde | Vegetación activa. Árbol con buena estructura foliar |
| > 0.7 | Verde oscuro | Vegetación muy densa. Poco común en mandarina joven |

### Qué monitorear

- 📉 **Caídas entre fechas**: posible estrés hídrico, plaga o deficiencia nutricional
- 📈 **Subidas**: recuperación o crecimiento
- 🟡 **Diferencias entre parcelas**: identificar lotes con menor vigor para priorizar recorridas a campo

---

## 2. NDRE — Índice de Borde Rojo (vigor + clorofila)

**Propósito**: Índice de vegetación del borde rojo. Similar al NDVI pero usando la banda RedEdge1 (B5) en vez de la Roja (B4). Es más sensible que el NDVI en doseles densos y no se satura tan rápido en cultivos con alto LAI.

| Detalle | Valor |
|---|---|
| Colormap | Personalizado GEE (rojo ↔ amarillo ↔ verde) |
| Rango visual | 0.1 – 0.6 |
| Rango fisiológico | −1 – 1 |
| Fórmula | `(NIR − RedEdge1) / (NIR + RedEdge1)` = `(B8 − B5) / (B8 + B5)` |

### Paleta de colores

```
0.1 (rojo)  ──  0.2 (naranja)  ──  0.35 (amarillo)  ──  0.5 (verde claro)  ──  0.6 (verde oscuro)
  baja              baja-media        moderada             alta                  muy alta
  clorofila         clorofila         clorofila            clorofila             clorofila
```

### Interpretación agronómica

| Rango | Color | Significado |
|---|---|---|
| < 0.15 | Rojo/Naranja | Vegetación estresada o muy rala. Suelo expuesto |
| 0.15 – 0.30 | Naranja/Amarillo | Vegetación con baja actividad fotosintética. Posible deficiencia o estrés temprano |
| 0.30 – 0.45 | Amarillo/Verde claro | Vegetación activa. Rango normal para mandarina en crecimiento |
| 0.45 – 0.60 | Verde | Buena salud. Alta concentración de clorofila. Cobertura foliar densa |

### Qué monitorear

- Es el índice utilizado como **referencia visual principal** en el time-lapse semanal de GEE
- Responde rápido a cambios en nitrógeno y clorofila
- Al ser un índice de borde rojo, es más sensible que el MSAVI2 a cambios **fisiológicos** (nutrición, estrés) y menos sensible a cambios **estructurales** (cantidad de hojas)
- Si el NDRE baja pero el MSAVI2 se mantiene → el problema es nutricional, no de biomasa
- Si ambos bajan → pérdida de vigor general

### NDRE vs MSAVI2

| Situación | NDRE | MSAVI2 |
|---|---|---|
| Planta bien nutrida | Alto | Alto |
| Deficiencia de N | **Bajo** | Medio (todavía tiene hojas) |
| Defoliación por plaga | Bajo | **Bajo** |
| Malezas en callejón | Medio | **Falso alto** (MSAVI2 corrige esto) |

---

## 3. S2REP — Posición del Borde Rojo (clorofila)

**Propósito**: Detecta el punto de inflexión del espectro entre el rojo y el infrarrojo. Es un indicador directo del **contenido de clorofila** y, por lo tanto, del **estado nutricional (nitrógeno)** del cultivo.

| Detalle | Valor |
|---|---|
| Colormap | turbo (azul ↔ verde ↔ amarillo ↔ rojo) |
| Rango visual | 705 – 740 nm |
| Rango fisiológico | 705 – 740 nm |
| Fórmula | `705 + 35 × (((B4+B7)/2 − B5) / (B6 − B5))` |

### Paleta de colores

```
705 (azul)  ──  715 (verde)  ──  725 (amarillo)  ──  740 (rojo)
  baja               clorofila            clorofila           alta
  clorofila          moderada             alta                clorofila
```

### Interpretación agronómica

| Rango | Color | Significado |
|---|---|---|
| < 715 | Azul/verde | Baja clorofila. Posible deficiencia de nitrógeno |
| 715 – 725 | Verde/amarillo | Clorofila moderada. Estado nutricional normal |
| 725 – 740 | Naranja/rojo | Alta clorofila. Buena nutrición nitrogenada |

### Qué monitorear

- Es el índice **más sensible a la fertilización nitrogenada**
- Si se aplicó urea (ej. en noviembre), debería verse un desplazamiento del S2REP hacia valores más altos en las semanas posteriores
- Una caída repentina sin cambio en MSAVI2 sugiere **deficiencia nutricional temprana** (antes de que se note en el vigor)
- El potasio (aplicado oct-feb) también influye indirectamente en la salud foliar

---

## 4. LAI_RedEdge — Índice de Área Foliar

**Propósito**: Estima cuánta superficie de hoja hay por unidad de superficie de suelo. Es una variable estructural crítica para modelos de requerimiento hídrico.

| Detalle | Valor |
|---|---|
| Colormap | Greens (blanco ↔ verde claro ↔ verde oscuro) |
| Rango visual | 0.1 – 6.0 |
| Rango fisiológico | 0.1 – 6.0 |
| Cálculo | `(S2REP − 700) × 0.15` |

> ⚠️ **Importante**: El factor `0.15` es un valor de literatura no calibrado para tus parcelas. Las **tendencias** son confiables; los valores absolutos son orientativos.

### Paleta de colores

```
0.1 (blanco)  ──  2.0 (verde claro)  ──  4.0+ (verde oscuro)
  sin               cultivo               dosel
  hojas             joven                 cerrado
```

### Interpretación agronómica

| Rango | Color | Significado |
|---|---|---|
| < 1.0 | Blanco | Sin vegetación o muy poca |
| 1.0 – 2.5 | Verde claro | Rango esperable para mandarina joven (3-4 años) con calles abiertas |
| 2.5 – 4.0 | Verde | Dosel más denso. Posible en árboles bien desarrollados |
| > 4.0 | Verde oscuro | Dosel cerrado. Poco probable en este huerto |

### Nota para este cultivo

- Tus árboles tienen ~2m de altura y 1.5m de extensión lateral
- Marco de plantación: 5.5m entre hileras, 3.5m entre plantas
- Con esta arquitectura, **los valores esperables de LAI están entre 1.0 y 2.5**
- El suelo entre hileras (con cobertura vegetal controlada) va a mezclarse en el píxel de 10m

---

## 5. Cab_RedEdge — Contenido de Clorofila foliar

**Propósito**: Mide la concentración de clorofila por unidad de área foliar. Complementa al S2REP.

| Detalle | Valor |
|---|---|
| Colormap | YlGn (amarillo ↔ verde ↔ verde oscuro) |
| Rango visual | 0 – 100 μg/cm² |
| Rango fisiológico | 0 – 100 μg/cm² |
| Cálculo | `(S2REP − 700) × 2` |

> ⚠️ **Importante**: Misma advertencia que LAI. El factor `2` es de literatura. Las tendencias son lo confiable.

### Paleta de colores

```
0 (amarillo)  ──  50 (verde)  ──  100 (verde oscuro)
  baja                moderada            alta
  clorofila           clorofila           clorofila
```

### Interpretación agronómica

| Rango | Color | Significado |
|---|---|---|
| < 30 | Amarillo | Baja concentración de clorofila |
| 30 – 60 | Verde | Rango normal |
| > 60 | Verde oscuro | Alta concentración de clorofila |

### Diferencia con S2REP

- **S2REP + Cab altos, LAI estable** → la planta tiene buena nutrición pero no está creciendo más hojas (etapa de maduración de fruta, ej. abril)
- **S2REP + Cab bajos, LAI estable** → posible deficiencia nutricional sin pérdida de biomasa
- **Todos bajos** → problema estructural severo

---

## 6. Kc_Actual — Demanda de Agua (Riego)

**Propósito**: Estima cuánta agua está consumiendo el cultivo en relación a la evapotranspiración de referencia (ETo). Sirve para calcular el riego: `ETc = ETo × Kc`.

| Detalle | Valor |
|---|---|
| Colormap | BrBG (marrón ↔ blanco ↔ verde-azul) |
| Rango visual | 0.2 – 1.3 |
| Rango fisiológico | 0.2 – 1.3 |
| Cálculo | `MSAVI2 × 1.15 + 0.1` |

> ⚠️ Pendientes `1.15` y `0.1` del paper de Ippolito et al. (2023) para cítricos. No calibrados para Jujuy.

### Paleta de colores

```
0.2 (marrón)  ──  0.7 (blanco)  ──  1.3 (verde-azul)
  suelo              cultivo             cultivo
  desnudo            moderado            muy activo
```

### Interpretación agronómica

| Rango | Color | Significado | Recomendación de riego |
|---|---|---|---|
| < 0.4 | Marrón | Poca vegetación o estresado | Reducir riego |
| 0.4 – 0.6 | Marrón claro | Baja actividad | Riego moderado |
| 0.6 – 0.9 | Blanco/verde claro | Actividad normal. Es el rango esperable para mandarina en abril | Riego normal |
| 0.9 – 1.1 | Verde | Alta transpiración | Aumentar riego |
| > 1.1 | Verde-azul | Muy activo (poco común en este cultivo) | Verificar |

### En el contexto de abril (maduración de fruta)

- Es la etapa donde la fruta demanda mucha energía y humedad
- Un Kc entre **0.6 y 0.9** es esperable
- Si una parcela tiene Kc mucho más bajo que las otras → revisar riego o problemas de raíz

---

## Guía rápida de interpretación

### Para el día a día

| Si ves... | Interpretá... |
|---|---|---|
| 🟢 MSAVI2 subiendo | El vigor aumenta. Crecimiento normal |
| 🔴 MSAVI2 bajando | Posible estrés. Revisar riego/plagas |
| 🔴 NDRE baja, MSAVI2 estable | Deficiencia de nitrógeno (las hojas están pero pierden clorofila) |
| 🟡 NDRE alto después de fertilizar | La fertilización nitrogenada está funcionando |
| 🔵 S2REP bajo | Revisar plan de fertilización nitrogenada |
| 🟡 S2REP alto después de urea | La fertilización funcionó |
| Parcela A mucho peor que B | Priorizar recorrida en A |
| Cab cae, MSAVI2 se mantiene | Deficiencia nutricional temprana (antes de pérdida de vigor) |
| LAI + Cab caen juntos | Problema estructural (plaga, raíz, agua) |
| Kc < 0.4 | Casi sin vegetación en esa parcela |

### Regla de oro

> **Las comparaciones importan más que los valores absolutos.**
>
> - Parcela 1 vs Parcela 2 en la misma fecha
> - Fecha actual vs fecha anterior en la misma parcela
> - Abril 2026 vs Abril 2025 (cuando tengas datos)

---

## Limitaciones importantes

| Limitación | Impacto |
|---|---|
| **Sin calibración de campo** | LAI, Cab y Kc son tendencias, no valores absolutos. Los factores (0.15, 2, 1.15, 0.1) son de literatura, no de tus parcelas |
| **Sin Cloud Score+** | El filtro CS+ (>90% certeza) no está disponible en STAC. Solo se usa SCL. Pueden pasar algunos píxeles con nubes remanentes |
| **Resolución mixta** | Las bandas de 20m (B5, B6, B7) se upsampean a ~10m. Los bordes de parcela pueden tener mezcla con el exterior |
| **Píxeles mixtos** | Cada píxel de 10m contiene árbol + suelo interhilar + maleza. MSAVI2 mitiga esto parcialmente |
| **Una temporada** | Estos datos son solo abril 2026. Para análisis de tendencias anuales se necesita procesar más meses |

---

## Glosario

| Término | Significado |
|---|---|
| **Despejada** | La escena satelital tiene <10% de cobertura de nubes |
| **Nublada** | La escena tiene ≥10% de nubes (aunque tus parcelas podrían estar despejadas) |
| **SinDatos** | Después del filtro SCL + recorte a parcelas, no quedaron píxeles válidos |
| **SCL** | Capa de clasificación de escena de Sentinel-2. Clasifica cada píxel en 12 categorías |
| **ETo** | Evapotranspiración de referencia (dato meteorológico) |
| **ETc** | Evapotranspiración del cultivo = ETo × Kc |
| **STAC** | Catálogo estándar de activos espacio-temporales. Es la API que usamos para buscar y descargar imágenes |
| **S2REP** | Posición del borde rojo de Sentinel-2. Medido en nanómetros (nm) |

---

*Documento generado automáticamente por el pipeline multi_indices_abril2026*
*Cultivo: Mandarina Murcott — Jujuy, Argentina*
