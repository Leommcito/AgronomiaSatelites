<!--
  Sync Impact Report
  ==================
  Version change: [TEMPLATE] → 1.0.0
  Bump rationale: MAJOR — First real constitution replacing placeholder template.
                    Defines 8 core principles, platform constraints, and governance
                    specifically for the Murcott Mandarin satellite monitoring project.
  Modified principles: N/A (all new — template had only placeholders)
  Added sections:
    - 8 Core Principles (I-VIII)
    - Platform & Technology Constraints
    - Development Workflow & Validation Protocol
    - Governance
  Removed sections: None (template placeholders replaced)
  Templates requiring updates:
    - .specify/templates/plan-template.md     ✅ No changes needed
    - .specify/templates/spec-template.md     ✅ No changes needed
    - .specify/templates/tasks-template.md    ✅ No changes needed
  Follow-up TODOs: None — all placeholders resolved.
-->

# Constitución del Proyecto: Monitoreo Satelital de Mandarina Murcott

## Propósito

Este proyecto implementa un script unificado en **Google Earth Engine (GEE)** para el
monitoreo satelital de plantaciones de mandarina Murcott (*Citrus reticulata*) en la
Provincia de Jujuy, Argentina, durante el período 2025–2026. El script aplica la
metodología de teledetección descrita en `Informacion.md` —basada en productos
Sentinel-2 L2A, índices de Borde Rojo, reconstrucción temporal Whittaker/Wavelet,
detección de estrés, y estimación del coeficiente de cultivo (Kc)— produciendo como
entregable un archivo CSV estandarizado y exportaciones espaciales restringidas a hitos
fenológicos.

El script cubre **4 parcelas experimentales de 0.5 ha cada una** (2 ha totales),
delimitadas mediante planimetría vectorial georreferenciada.

---

## Principios Fundamentales (Core Principles)

### I. Script Único y Autocontenido (NON-NEGOTIABLE)

**Toda la metodología debe ejecutarse desde UN solo script de Google Earth Engine.**

- El script (`Codigo.md` / `codigo_gee.js`) es la única fuente de verdad ejecutable.
- No se permite dividir la lógica en múltiples scripts, módulos externos ni dependencias
  fuera del ecosistema nativo de GEE (JavaScript API).
- Cualquier importación debe limitarse a módulos públicos del catálogo de GEE
  (ej. `users/gena/packages:text` para anotaciones visuales).
- El script debe poder copiarse, pegarse en el Editor de Código de GEE, y ejecutarse
  sin configuración adicional más allá del `asset` de parcelas y la carpeta Drive de
  destino.

**Racional**: La plataforma GEE favorece scripts monolíticos autocontenidos. Dividir
el código en múltiples archivos introduce riesgos de desincronización, errores de
importación, y dificulta la reproducibilidad por parte de terceros (agrónomos,
revisores de tesis).

---

### II. Fidelidad y Trazabilidad Metodológica

**Cada elemento de la metodología descrita en `Informacion.md` debe tener una
contraparte trazable en el código.**

- Toda sección del documento metodológico (1.1 a 4.3) debe estar implementada o
  explícitamente marcada como `TODO` con justificación documentada.
- Las decisiones de simplificación (ej. modelos de regresión lineal para LAI/Cab en
  lugar de modelos de transferencia radiométrica completos) deben:
  - Estar documentadas como comentario en el código.
  - Incluir la referencia bibliográfica que respalda la simplificación.
  - Tener un plan de reemplazo cuando se disponga de coeficientes validados para
    Murcott en Jujuy.
- El código debe referenciar las fuentes académicas citadas en la metodología:
  Ali et al. (2022), Ippolito et al. (2023), Della Bellver et al. (2024),
  Rouault et al. (2025), Ramírez-Juidias et al. (2023).

**Racional**: El proyecto es una tesis académica. La trazabilidad entre metodología e
implementación es requisito para la defensa y publicación de resultados.

---

### III. Doble Filtrado de Calidad Óptica (GATE OBLIGATORIO)

**Ningún píxel sin filtrar puede participar en los cálculos de índices.**

- **Filtro 1 — Cloud Score+ (CS+)**: `cs_cdf >= 0.90`. Solo píxeles con probabilidad
  de limpieza superior al 90% según el modelo de Deep Learning de Google.
- **Filtro 2 — Scene Classification Layer (SCL)**: Solo clases 4 (Vegetación) y 5
  (Suelos desnudos). Quedan excluidos: nubes (alta/baja probabilidad), sombras de
  nubes, agua, nieve/hielo, y píxeles defectuosos.
- Ambos filtros se aplican mediante `updateMask()` como primera operación sobre cada
  imagen, antes de cualquier cálculo de bandas o índices.
- La colección resultante debe reportar (vía `print()`) la cantidad de imágenes que
  sobreviven al filtrado vs. el total original.

**Racional**: La región de Jujuy tiene cobertura nubosa significativa. Sin doble
filtrado, los falsos positivos (nubes interpretadas como vegetación vigorosa)
contaminan irreversiblemente las series temporales y las alertas de estrés.

---

### IV. Primacía Espectral del Borde Rojo sobre NDVI

**El NDVI queda relegado a enmascarador secundario. La cuantificación biofísica usa
exclusivamente índices de Borde Rojo.**

- **NDVI**: Se calcula pero SOLO como máscara binaria de vegetación (NDVI > 0.3 →
  vegetación presente). No se usa para estimar LAI, Clorofila ni Kc.
- **NDRE** (Normalized Difference Red-Edge): `(B8 - B5) / (B8 + B5)`. Índice primario
  para visualización (mapas, timelapse) y validación cruzada.
- **S2REP** (Sentinel-2 Red-Edge Position): `705 + 35 * (((B4 + B7) / 2 - B5) /
  (B6 - B5))`. Variable independiente principal para estimar LAI y Clorofila (Cab).
  - **ATENCIÓN**: La fórmula del documento metodológico difiere de la implementada.
    Se debe verificar cuál es la correcta según Ali et al. (2022) y unificar.
- **MSAVI2** (Modified Soil-Adjusted Vegetation Index 2): `(2*NIR + 1 - sqrt((2*NIR +
  1)² - 8*(NIR - RED))) / 2`. Usado para mitigar ruido de suelo/maleza y como base
  para derivar Kc.

**Racional**: En cítricos jóvenes-adultos (3-4 años), el NDVI se satura cuando el LAI
supera 2.5–3.0, produciendo curvas planas inservibles para monitoreo. Las bandas de
Borde Rojo (B5, B6, B7) penetran más profundamente en el dosel y responden
proporcionalmente a cambios en pigmentos fotosintéticos (Ali et al., 2022).

---

### V. Reconstrucción Temporal con Whittaker (Gap-Filling)

**El relleno de vacíos por nubosidad debe usar el filtro de Whittaker, no interpolación
simple.**

- La serie temporal bruta (tras doble filtrado) es irregular: se esperan ventanas de
  10-20 días sin observaciones válidas en temporada de lluvias.
- **Whittaker Filter**: Equilibra matemáticamente la fidelidad a las observaciones
  originales con una penalización de rugosidad de la curva, respetando la trayectoria
  biológica natural del dosel de los cítricos (Rouault et al., 2025).
- **Wavelet Analysis**: Como validación paralela, descompone la señal en componentes
  tiempo-frecuencia para aislar y suprimir ruido de alta frecuencia (anomalías de
  sensor a corto plazo) (Ramírez-Juidias et al., 2023).
- **Flag_Interpolacion**: Cada registro semanal incluye indicador binario:
  - `0` = dato basado en observación satelital real con cielo despejado.
  - `1` = dato interpolado matemáticamente (gap-filling).
- **IMPLEMENTACIÓN ACTUAL**: El código usa mediana de ventana ±15 días (NO es
  Whittaker). Esto es un `TODO` crítico que debe resolverse.

**Racional**: Sin Whittaker, el gap-filling produce artefactos (saltos abruptos entre
semanas con y sin datos) que distorsionan la detección de estrés y las curvas
fenológicas. Con Whittaker, la curva sigue la inercia biológica real del cultivo.

---

### VI. Detección de Estrés por Desviación de Línea Base Dinámica

**Las alertas se disparan por desviación significativa respecto a la curva fenológica
esperada, no por umbrales fijos.**

- **Línea base**: La "memoria matemática" de la curva Whittaker/Wavelet para cada
  variable (LAI, Cab).
- **Tres niveles de alerta**:
  - `Normal`: valor dentro de ±1 desviación estándar de la línea base.
  - `Precaución`: caída entre 1 y 2 desviaciones estándar.
  - `Alerta Crítica`: caída superior a 2 desviaciones estándar.
- **Variables monitoreadas**: Tanto LAI_RedEdge como Cab_RedEdge. Una caída anómala en
  cualquiera de las dos dispara la alerta.
- **Filtros previos garantizan**: nubes ya eliminadas (CS+ > 0.90), malezas aisladas
  (MSAVI2). Una caída real es atribuible a estrés fisiológico real (plaga, déficit
  hídrico, deficiencia nutricional).

**Racional**: La metodología cita a Della Bellver et al. (2024), quienes demostraron
que caídas en firmas espectrales del Borde Rojo y LAI actúan como indicadores
tempranos de infestación (ej. cochinilla *Delottococcus aberiae*). Un umbral fijo
ignora la fenología natural del cultivo.

---

### VII. Exportación Espacial Restringida a Hitos Fenológicos

**Solo se exportan mapas espaciales (GeoTIFF) en fechas comprobadas de cielo despejado
que coinciden con hitos fenológicos agronómicamente relevantes.**

- **Hito 1 — Reposo y Poda**: Julio–Agosto.
- **Hito 2 — Floración plena y Cuaje**: Octubre–Diciembre.
- **Hito 3 — Proximidad de Cosecha**: Abril–Junio.
- Cada exportación debe usar imágenes de fechas específicas con verificación de
  cobertura nubosa < 10% (no composiciones medianas de períodos largos).
- **Visualización semanal**: Se genera timelapse/video usando NDRE para todas las
  semanas del período. Los frames sin datos (nubosidad total) aparecen en negro.
- Las imágenes semanales individuales como GeoTIFF son opcionales pero recomendadas.

**Racional**: Exportar imágenes de todas las semanas generaría cientos de archivos, la
mayoría con vacíos por nubes. Restringir a hitos fenológicos optimiza almacenamiento y
entrega exactamente lo que el agrónomo necesita para decisiones de campo.

---

### VIII. Salida Tabular Estandarizada (CSV)

**El producto final es un archivo CSV con estructura fija e inmutable.**

Columnas obligatorias (en este orden):

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `Fecha_Semanal` | `YYYY-MM-DD` | Fecha regularizada por el algoritmo temporal (día fijo de la semana) |
| `ID_Parcela` | `string` | Identificador único de la parcela (1-4) |
| `LAI_RedEdge` | `float` | Índice de Área Foliar estimado mediante S2REP |
| `Cab_RedEdge` | `float` | Contenido de Clorofila subrogado (μg/cm²) |
| `Kc_Actual` | `float` | Coeficiente de cultivo derivado de MSAVI2 |
| `Flag_Interpolacion` | `0` o `1` | 0 = observación real, 1 = interpolado matemáticamente |
| `Alerta_Estres` | `string` | `Normal` / `Precaución` / `Alerta Crítica` |

- El CSV se exporta a Google Drive (`folder: 'Tesis_Mandarinas'`).
- Una fila por parcela por semana. Con 4 parcelas y ~78 semanas (2025-01 a 2026-06),
  se esperan ~312 filas (antes de filtrar nulos en extremos).
- **Prohibido** agregar, eliminar o renombrar columnas sin actualizar esta
  constitución.

**Racional**: La estandarización del CSV permite que los datos sean consumidos
directamente por dashboards agronómicos, modelos de riego (SIMETAW), y análisis
estadísticos posteriores sin necesidad de pre-procesamiento manual.

---

## Restricciones de Plataforma y Tecnología

### Plataforma de Ejecución

- **Google Earth Engine (GEE)** — JavaScript API (Editor de Código).
- El script debe ser ejecutable en el entorno estándar de GEE sin activar funciones
  experimentales ni cuentas especiales.

### Fuentes de Datos

| Dataset | ID GEE | Propósito |
|---------|--------|-----------|
| Sentinel-2 L2A (Harmonized) | `COPERNICUS/S2_SR_HARMONIZED` | Reflectancia de superficie, bandas espectrales, SCL |
| Cloud Score+ V1 | `GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED` | Probabilidad de píxel limpio (cs_cdf) |
| Parcelas (vectorial) | `projects/proyectoleomespinosa/assets/ParcelasDefinidas` | Geometría de las 4 parcelas de estudio |
| ET₀ (estación meteorológica) | `TODO` | Pendiente de integrar — evapotranspiración de referencia |

### Limitaciones Técnicas de GEE a Respetar

- **Timeout de 5 minutos**: El script completo debe ejecutarse en < 5 min. Si se excede,
  dividir en exportaciones asíncronas (Tasks) pero nunca en múltiples scripts.
- **Memoria**: Usar `tileScale` y `maxPixels` apropiados para no exceder límites.
- **CSV**: La exportación de tablas está limitada a ~10⁶ filas. Con ~312 filas
  esperadas, no hay riesgo.
- **Whittaker en GEE**: El filtro Whittaker no es nativo de GEE. La implementación
  debe usar `ee.Reducer` o álgebra lineal con `ee.Array`. Verificar viabilidad; si es
  imposible, documentar la alternativa y justificarla en la tesis.

---

## Flujo de Desarrollo y Protocolo de Validación

### Orden de Implementación (por prioridad)

1. **Pre-procesamiento**: L2A, doble filtro CS+/SCL, cálculo de bandas escaladas.
2. **Índices espectrales**: NDVI, NDRE, S2REP, MSAVI2 — en ese orden.
3. **Variables biofísicas**: LAI, Cab (basados en S2REP), Kc (basado en MSAVI2).
4. **Reconstrucción temporal**: Whittaker + Wavelet (o alternativa documentada).
5. **Detección de estrés**: Línea base dinámica + 3 niveles de alerta.
6. **Exportación CSV**: Tabla estandarizada a Google Drive.
7. **Exportación espacial**: GeoTIFF por hitos fenológicos + timelapse semanal NDRE.
8. **Integración ET₀**: `TODO` — Pendiente de fuente de datos meteorológicos.

### Protocolo de Validación por Módulo

Cada módulo debe ser verificable independientemente mediante `print()` en Consola GEE:

- **Módulo 1 (Pre-procesamiento)**: `print('Imágenes antes del filtro:', totalCrudas,
  'después:', totalFiltradas)`.
- **Módulo 2 (Índices)**: `print('NDRE mediana parcela 1:', ndreMediana)`.
- **Módulo 3 (Biofísica)**: Verificar que LAI ∈ [0.1, 6.0], Cab ∈ [0, 100].
- **Módulo 4 (Temporal)**: `print('Semanas interpoladas:', semanasInterpoladas)`.
- **Módulo 5 (Estrés)**: `print('Alertas emitidas:', conteoAlertas)`.
- **Módulo 6 (CSV)**: Verificar en Google Drive que el archivo tiene columnas correctas.
- **Módulo 7 (Espacial)**: Verificar GeoTIFF abre en QGIS con valores esperados.

### Commits y Versionado

- **Un commit por módulo completado y validado.**
- Mensaje de commit: `feat(modulo-N): descripción breve`.
- Ejemplo: `feat(modulo-1): doble filtro CS+ (>0.90) + SCL (clases 4,5)`.

---

## Gobernanza

### Jerarquía Documental

1. **Esta Constitución** — Principios innegociables. Solo se modifica con justificación
   escrita y actualización de versión.
2. **`Informacion.md`** — Metodología académica de referencia. La constitución deriva
   sus principios de este documento.
3. **`Codigo.md`** — Implementación. Debe cumplir esta constitución. Si hay conflicto,
   la constitución prevalece.
4. **`Informacionsitio.md`** — Contexto agronómico complementario (no normativo).

### Procedimiento de Enmienda

1. Proponer el cambio con justificación escrita (issue o documento).
2. Evaluar impacto en los 8 principios y en el CSV de salida.
3. Si el cambio afecta el CSV, requiere nueva columna, o elimina un principio: bump
   de versión MAJOR.
4. Si el cambio agrega un módulo, expande una sección: bump MINOR.
5. Si el cambio es corrección de errores, ajuste de constantes, clarificación: bump
   PATCH.
6. Actualizar `LAST_AMENDED_DATE` y `CONSTITUTION_VERSION`.
7. Sincronizar `Codigo.md` para reflejar el cambio.

### Compliance Review

- Antes de considerar el script "terminado", se debe ejecutar una revisión de
  cumplimiento constitucional: verificar cada uno de los 8 principios contra el
  código.
- Las violaciones se clasifican como:
  - **Críticas**: Bloquean la entrega (ej. falta el doble filtro).
  - **Mayores**: Requieren plan de resolución (ej. Whittaker no implementado).
  - **Menores**: Se documentan como limitaciones conocidas (ej. coeficientes LAI
    no validados para Murcott).

---

**Version**: 1.0.0 | **Ratified**: 2026-06-01 | **Last Amended**: 2026-06-01
