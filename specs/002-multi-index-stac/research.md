# Research: Multi-Índices STAC Abril 2026

**Phase 0 — Technical Decisions & Trade-offs**

## Decision 1: SCL como Único Filtro de Nubes (sin CS+)

**Decision**: Usar exclusivamente la máscara SCL (clases 4,5) para filtrar nubes.
Cloud Score+ (CS+) no está disponible en el catálogo Earth Search STAC.

**Rationale**: 
- CS+ es un modelo de Google exclusivo de GEE. No existe en STAC.
- Para parcelas de 0.5 ha, el filtro SCL es suficiente: elimina nubes, sombras
  de nubes, agua y píxeles defectuosos.
- No usar `eo:cloud_cover` como filtro de búsqueda porque mide nubes a nivel
  de tile (100km×100km), no correlaciona con parcelas chicas.

**Alternativas considered**:
- CS+ → rechazado por no estar disponible en STAC
- `eo:cloud_cover < 10` → rechazado por no correlacionar con parcelas pequeñas
- Sin filtro → rechazado, datos contaminados por nubes

---

## Decision 2: Resolución Uniforme a 10m

**Decision**: Todas las bandas se cargan a resolución de 10m
(`resolution=0.0001` en EPSG:4326), upsampeando B6 y B7 de 20m a 10m.

**Rationale**:
- Consistencia: todos los índices tienen la misma cuadrícula de píxeles
- Las parcelas de 0.5 ha (~50 píxeles a 10m) tendrían ~12 píxeles a 20m,
  demasiado pocos para estadísticas significativas
- `odc.stac.load()` con `resolution=0.0001` maneja el upsampling automáticamente

**Alternativas considered**:
- Todo a 20m → rechazado, muy pocos píxeles por parcela
- Carpetas separadas por resolución → rechazado por complejidad innecesaria

---

## Decision 3: Guardias de Estabilidad Numérica

**Decision**: Incluir guardias explícitas para evitar NaN/Inf en los cálculos.

**Rationale**:
- S2REP: `np.abs(b6 - b5) < 0.0001` causa división por cero → retornar NaN
- MSAVI2: discriminante negativo cuando `(2*NIR+1)² < 8*(NIR-RED)` → retornar NaN
- Sin estas guardias, escenas con bandas homogéneas (ej. agua, sombra total)
  producirían valores Inf que contaminan estadísticas

**Implementación**: Seguir el patrón de `codigo_gee.js:65-72` y `79-82`.

---

## Decision 4: Etiquetado de Nubes por Escena (sin filtrar)

**Decision**: `eo:cloud_cover` se usa SOLO para etiquetar el sufijo del nombre
del archivo (Despejada/Nublada), NO para filtrar escenas.

**Rationale**:
- La máscara SCL ya maneja la calidad por píxel
- `eo:cloud_cover` es un metadata a nivel de escena, útil para referencia
- Filtrar por `eo:cloud_cover` descartaría escenas con píxeles válidos
  parciales sobre las parcelas

**Alternativas considered**:
- Filtrar por `eo:cloud_cover < 10` → rechazado por descartar datos válidos
- No etiquetar → rechazado, la etiqueta es útil para identificación rápida

---

## Decision 5: Parámetros Configurables al Inicio del Script

**Decision**: Exponer LAI_factor, Cab_factor, kc_slope, kc_intercept como
variables al inicio del script, con los mismos defaults que `codigo_gee.js`.

**Defaults**:
- LAI_factor = 0.15
- Cab_factor = 2
- kc_slope = 1.15
- kc_intercept = 0.1

**Rationale**: Coeficientes no validados específicamente para Murcott en Jujuy.
Tenerlos como constantes al inicio permite recalibrar sin modificar la lógica.

---

## Decision 6: Colormaps Específicos por Índice

**Decision**: Cada índice usa su propio colormap de matplotlib con rango fijo.

| Índice | Colormap | vmin | vmax |
|--------|----------|------|------|
| MSAVI2 | RdYlGn | 0.2 | 0.8 |
| S2REP | turbo | 705 | 740 |
| LAI_RedEdge | Greens | 0.1 | 6.0 |
| Cab_RedEdge | YlGn | 0 | 100 |
| Kc_Actual | BrBG | 0.2 | 1.3 |

**Rationale**: Cada índice representa una variable agronómica distinta con
diferente rango y significado visual. Usar el mismo colormap para todos
produciría mapas engañosos.
