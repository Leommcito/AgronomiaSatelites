<!--
  Sync Impact Report
  ==================
  Version change: [TEMPLATE] â†’ 1.0.0
  Bump rationale: MAJOR â€” First real constitution replacing placeholder template.
                    Defines 8 core principles, platform constraints, and governance
                    Added sections:
    - 4 optional CSV columns (NDRE, MSAVI2, S2REP, NDVI) appended to Principle VIII

  Removed sections: None
  Modified principles: N/A (all new â€” template had only placeholders)
  Added sections:
    - 8 Core Principles (I-VIII)
    - Platform & Technology Constraints
    - Development Workflow & Validation Protocol
    - Governance
  Removed sections: None (template placeholders replaced)
  Templates requiring updates:
    - .specify/templates/plan-template.md     âœ… No changes needed
    - .specify/templates/spec-template.md     âœ… No changes needed
    - .specify/templates/tasks-template.md    âœ… No changes needed
  Follow-up TODOs: None â€” all placeholders resolved.
-->

# ConstituciÃ³n del Proyecto: Monitoreo Satelital de Mandarina Murcott

## PropÃ³sito

Este proyecto implementa un script unificado en **Google Earth Engine (GEE)** para el
monitoreo satelital de plantaciones de mandarina Murcott (*Citrus reticulata*) en la
Provincia de Jujuy, Argentina, durante el perÃ­odo 2025â€“2026. El script aplica la
metodologÃ­a de teledetecciÃ³n descrita en `Informacion.md` â€”basada en productos
Sentinel-2 L2A, Ã­ndices de Borde Rojo, reconstrucciÃ³n temporal Whittaker/Wavelet,
detecciÃ³n de estrÃ©s, y estimaciÃ³n del coeficiente de cultivo (Kc)â€” produciendo como
entregable un archivo CSV estandarizado y exportaciones espaciales restringidas a hitos
fenolÃ³gicos.

El script cubre **4 parcelas experimentales de 0.5 ha cada una** (2 ha totales),
delimitadas mediante planimetrÃ­a vectorial georreferenciada.

---

## Principios Fundamentales (Core Principles)

### I. Script Ãšnico y Autocontenido (NON-NEGOTIABLE)

**Toda la metodologÃ­a debe ejecutarse desde UN solo script de Google Earth Engine.**

- El script (`Codigo.md` / `codigo_gee.js`) es la Ãºnica fuente de verdad ejecutable.
- No se permite dividir la lÃ³gica en mÃºltiples scripts, mÃ³dulos externos ni dependencias
  fuera del ecosistema nativo de GEE (JavaScript API).
- Cualquier importaciÃ³n debe limitarse a mÃ³dulos pÃºblicos del catÃ¡logo de GEE
  (ej. `users/gena/packages:text` para anotaciones visuales).
- El script debe poder copiarse, pegarse en el Editor de CÃ³digo de GEE, y ejecutarse
  sin configuraciÃ³n adicional mÃ¡s allÃ¡ del `asset` de parcelas y la carpeta Drive de
  destino.

**Racional**: La plataforma GEE favorece scripts monolÃ­ticos autocontenidos. Dividir
el cÃ³digo en mÃºltiples archivos introduce riesgos de desincronizaciÃ³n, errores de
importaciÃ³n, y dificulta la reproducibilidad por parte de terceros (agrÃ³nomos,
revisores de tesis).

---

### II. Fidelidad y Trazabilidad MetodolÃ³gica

**Cada elemento de la metodologÃ­a descrita en `Informacion.md` debe tener una
contraparte trazable en el cÃ³digo.**

- Toda secciÃ³n del documento metodolÃ³gico (1.1 a 4.3) debe estar implementada o
  explÃ­citamente marcada como `TODO` con justificaciÃ³n documentada.
- Las decisiones de simplificaciÃ³n (ej. modelos de regresiÃ³n lineal para LAI/Cab en
  lugar de modelos de transferencia radiomÃ©trica completos) deben:
  - Estar documentadas como comentario en el cÃ³digo.
  - Incluir la referencia bibliogrÃ¡fica que respalda la simplificaciÃ³n.
  - Tener un plan de reemplazo cuando se disponga de coeficientes validados para
    Murcott en Jujuy.
- El cÃ³digo debe referenciar las fuentes acadÃ©micas citadas en la metodologÃ­a:
  Ali et al. (2022), Ippolito et al. (2023), Della Bellver et al. (2024),
  Rouault et al. (2025), RamÃ­rez-Juidias et al. (2023).

**Racional**: El proyecto es una tesis acadÃ©mica. La trazabilidad entre metodologÃ­a e
implementaciÃ³n es requisito para la defensa y publicaciÃ³n de resultados.

---

### III. Doble Filtrado de Calidad Ã“ptica (GATE OBLIGATORIO)

**NingÃºn pÃ­xel sin filtrar puede participar en los cÃ¡lculos de Ã­ndices.**

- **Filtro 1 â€” Cloud Score+ (CS+)**: `cs_cdf >= 0.90`. Solo pÃ­xeles con probabilidad
  de limpieza superior al 90% segÃºn el modelo de Deep Learning de Google.
- **Filtro 2 â€” Scene Classification Layer (SCL)**: Solo clases 4 (VegetaciÃ³n) y 5
  (Suelos desnudos). Quedan excluidos: nubes (alta/baja probabilidad), sombras de
  nubes, agua, nieve/hielo, y pÃ­xeles defectuosos.
- Ambos filtros se aplican mediante `updateMask()` como primera operaciÃ³n sobre cada
  imagen, antes de cualquier cÃ¡lculo de bandas o Ã­ndices.
- La colecciÃ³n resultante debe reportar (vÃ­a `print()`) la cantidad de imÃ¡genes que
  sobreviven al filtrado vs. el total original.

**Racional**: La regiÃ³n de Jujuy tiene cobertura nubosa significativa. Sin doble
filtrado, los falsos positivos (nubes interpretadas como vegetaciÃ³n vigorosa)
contaminan irreversiblemente las series temporales y las alertas de estrÃ©s.

---

### IV. PrimacÃ­a Espectral del Borde Rojo sobre NDVI

**El NDVI queda relegado a enmascarador secundario. La cuantificaciÃ³n biofÃ­sica usa
exclusivamente Ã­ndices de Borde Rojo.**

- **NDVI**: Se calcula pero SOLO como mÃ¡scara binaria de vegetaciÃ³n (NDVI > 0.3 â†’
  vegetaciÃ³n presente). No se usa para estimar LAI, Clorofila ni Kc.
- **NDRE** (Normalized Difference Red-Edge): `(B8 - B5) / (B8 + B5)`. Ãndice primario
  para visualizaciÃ³n (mapas, timelapse) y validaciÃ³n cruzada.
- **S2REP** (Sentinel-2 Red-Edge Position): `705 + 35 * (((B4 + B7) / 2 - B5) /
  (B6 - B5))`. Variable independiente principal para estimar LAI y Clorofila (Cab).
  - **ATENCIÃ“N**: La fÃ³rmula del documento metodolÃ³gico difiere de la implementada.
    Se debe verificar cuÃ¡l es la correcta segÃºn Ali et al. (2022) y unificar.
- **MSAVI2** (Modified Soil-Adjusted Vegetation Index 2): `(2*NIR + 1 - sqrt((2*NIR +
  1)Â² - 8*(NIR - RED))) / 2`. Usado para mitigar ruido de suelo/maleza y como base
  para derivar Kc.

**Racional**: En cÃ­tricos jÃ³venes-adultos (3-4 aÃ±os), el NDVI se satura cuando el LAI
supera 2.5â€“3.0, produciendo curvas planas inservibles para monitoreo. Las bandas de
Borde Rojo (B5, B6, B7) penetran mÃ¡s profundamente en el dosel y responden
proporcionalmente a cambios en pigmentos fotosintÃ©ticos (Ali et al., 2022).

---

### V. ReconstrucciÃ³n Temporal con Whittaker (Gap-Filling)

**El relleno de vacÃ­os por nubosidad debe usar el filtro de Whittaker, no interpolaciÃ³n
simple.**

- La serie temporal bruta (tras doble filtrado) es irregular: se esperan ventanas de
  10-20 dÃ­as sin observaciones vÃ¡lidas en temporada de lluvias.
- **Whittaker Filter**: Equilibra matemÃ¡ticamente la fidelidad a las observaciones
  originales con una penalizaciÃ³n de rugosidad de la curva, respetando la trayectoria
  biolÃ³gica natural del dosel de los cÃ­tricos (Rouault et al., 2025).
- **Wavelet Analysis**: Como validaciÃ³n paralela, descompone la seÃ±al en componentes
  tiempo-frecuencia para aislar y suprimir ruido de alta frecuencia (anomalÃ­as de
  sensor a corto plazo) (RamÃ­rez-Juidias et al., 2023).
- **Flag_Interpolacion**: Cada registro semanal incluye indicador binario:
  - `0` = dato basado en observaciÃ³n satelital real con cielo despejado.
  - `1` = dato interpolado matemÃ¡ticamente (gap-filling).
- **IMPLEMENTACIÃ“N ACTUAL**: El cÃ³digo usa mediana de ventana Â±15 dÃ­as (NO es
  Whittaker). Esto es un `TODO` crÃ­tico que debe resolverse.

**Racional**: Sin Whittaker, el gap-filling produce artefactos (saltos abruptos entre
semanas con y sin datos) que distorsionan la detecciÃ³n de estrÃ©s y las curvas
fenolÃ³gicas. Con Whittaker, la curva sigue la inercia biolÃ³gica real del cultivo.

---

### VI. DetecciÃ³n de EstrÃ©s por DesviaciÃ³n de LÃ­nea Base DinÃ¡mica

**Las alertas se disparan por desviaciÃ³n significativa respecto a la curva fenolÃ³gica
esperada, no por umbrales fijos.**

- **LÃ­nea base**: La "memoria matemÃ¡tica" de la curva Whittaker/Wavelet para cada
  variable (LAI, Cab).
- **Tres niveles de alerta**:
  - `Normal`: valor dentro de Â±1 desviaciÃ³n estÃ¡ndar de la lÃ­nea base.
  - `PrecauciÃ³n`: caÃ­da entre 1 y 2 desviaciones estÃ¡ndar.
  - `Alerta CrÃ­tica`: caÃ­da superior a 2 desviaciones estÃ¡ndar.
- **Variables monitoreadas**: Tanto LAI_RedEdge como Cab_RedEdge. Una caÃ­da anÃ³mala en
  cualquiera de las dos dispara la alerta.
- **Filtros previos garantizan**: nubes ya eliminadas (CS+ > 0.90), malezas aisladas
  (MSAVI2). Una caÃ­da real es atribuible a estrÃ©s fisiolÃ³gico real (plaga, dÃ©ficit
  hÃ­drico, deficiencia nutricional).

**Racional**: La metodologÃ­a cita a Della Bellver et al. (2024), quienes demostraron
que caÃ­das en firmas espectrales del Borde Rojo y LAI actÃºan como indicadores
tempranos de infestaciÃ³n (ej. cochinilla *Delottococcus aberiae*). Un umbral fijo
ignora la fenologÃ­a natural del cultivo.

---

### VII. ExportaciÃ³n Espacial Restringida a Hitos FenolÃ³gicos

**Solo se exportan mapas espaciales (GeoTIFF) en fechas comprobadas de cielo despejado
que coinciden con hitos fenolÃ³gicos agronÃ³micamente relevantes.**

- **Hito 1 â€” Reposo y Poda**: Julioâ€“Agosto.
- **Hito 2 â€” FloraciÃ³n plena y Cuaje**: Octubreâ€“Diciembre.
- **Hito 3 â€” Proximidad de Cosecha**: Abrilâ€“Junio.
- Cada exportaciÃ³n debe usar imÃ¡genes de fechas especÃ­ficas con verificaciÃ³n de
  cobertura nubosa < 10% (no composiciones medianas de perÃ­odos largos).
- **VisualizaciÃ³n semanal**: Se genera timelapse/video usando NDRE para todas las
  semanas del perÃ­odo. Los frames sin datos (nubosidad total) aparecen en negro.
- Las imÃ¡genes semanales individuales como GeoTIFF son opcionales pero recomendadas.

**Racional**: Exportar imÃ¡genes de todas las semanas generarÃ­a cientos de archivos, la
mayorÃ­a con vacÃ­os por nubes. Restringir a hitos fenolÃ³gicos optimiza almacenamiento y
entrega exactamente lo que el agrÃ³nomo necesita para decisiones de campo.

---

### VIII. Salida Tabular Estandarizada (CSV)

**El producto final es un archivo CSV con estructura fija e inmutable.**

Columnas obligatorias (en este orden):

| Columna | Tipo | DescripciÃ³n |
|---------|------|-------------|
| `Fecha_Semanal` | `YYYY-MM-DD` | Fecha regularizada por el algoritmo temporal (dÃ­a fijo de la semana) |
| `ID_Parcela` | `string` | Identificador Ãºnico de la parcela (1-4) |
| `LAI_RedEdge` | `float` | Ãndice de Ãrea Foliar estimado mediante S2REP |
| `Cab_RedEdge` | `float` | Contenido de Clorofila subrogado (Î¼g/cmÂ²) |
| `Kc_Actual` | `float` | Coeficiente de cultivo derivado de MSAVI2 |
| `Flag_Interpolacion` | `0` o `1` | 0 = observaciÃ³n real, 1 = interpolado matemÃ¡ticamente |
| `Alerta_Estres` | `string` | `Normal` / `PrecauciÃ³n` / `Alerta CrÃ­tica` |

- El CSV se exporta a Google Drive (`folder: 'Tesis_Mandarinas'`).
- Una fila por parcela por semana (11 columnas). Con 4 parcelas y ~78 semanas (2025-01 a 2026-06),
  se esperan ~312 filas (antes de filtrar nulos en extremos).
- **Prohibido** agregar, eliminar o renombrar columnas sin actualizar esta
  constituciÃ³n.

**Racional**: La estandarizaciÃ³n del CSV permite que los datos sean consumidos
directamente por dashboards agronÃ³micos, modelos de riego (SIMETAW), y anÃ¡lisis
estadÃ­sticos posteriores sin necesidad de pre-procesamiento manual.

---

## Restricciones de Plataforma y TecnologÃ­a

### Plataforma de EjecuciÃ³n

- **Google Earth Engine (GEE)** â€” JavaScript API (Editor de CÃ³digo).
- El script debe ser ejecutable en el entorno estÃ¡ndar de GEE sin activar funciones
  experimentales ni cuentas especiales.

### Fuentes de Datos

| Dataset | ID GEE | PropÃ³sito |
|---------|--------|-----------|
| Sentinel-2 L2A (Harmonized) | `COPERNICUS/S2_SR_HARMONIZED` | Reflectancia de superficie, bandas espectrales, SCL |
| Cloud Score+ V1 | `GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED` | Probabilidad de pÃ­xel limpio (cs_cdf) |
| Parcelas (vectorial) | `projects/proyectoleomespinosa/assets/ParcelasDefinidas` | GeometrÃ­a de las 4 parcelas de estudio |
| ETâ‚€ (estaciÃ³n meteorolÃ³gica) | `TODO` | Pendiente de integrar â€” evapotranspiraciÃ³n de referencia |

### Limitaciones TÃ©cnicas de GEE a Respetar

- **Timeout de 5 minutos**: El script completo debe ejecutarse en < 5 min. Si se excede,
  dividir en exportaciones asÃ­ncronas (Tasks) pero nunca en mÃºltiples scripts.
- **Memoria**: Usar `tileScale` y `maxPixels` apropiados para no exceder lÃ­mites.
- **CSV**: La exportaciÃ³n de tablas estÃ¡ limitada a ~10â¶ filas. Con ~312 filas
  esperadas, no hay riesgo.
- **Whittaker en GEE**: El filtro Whittaker no es nativo de GEE. La implementaciÃ³n
  debe usar `ee.Reducer` o Ã¡lgebra lineal con `ee.Array`. Verificar viabilidad; si es
  imposible, documentar la alternativa y justificarla en la tesis.

---

## Flujo de Desarrollo y Protocolo de ValidaciÃ³n

### Orden de ImplementaciÃ³n (por prioridad)

1. **Pre-procesamiento**: L2A, doble filtro CS+/SCL, cÃ¡lculo de bandas escaladas.
2. **Ãndices espectrales**: NDVI, NDRE, S2REP, MSAVI2 â€” en ese orden.
3. **Variables biofÃ­sicas**: LAI, Cab (basados en S2REP), Kc (basado en MSAVI2).
4. **ReconstrucciÃ³n temporal**: Whittaker + Wavelet (o alternativa documentada).
5. **DetecciÃ³n de estrÃ©s**: LÃ­nea base dinÃ¡mica + 3 niveles de alerta.
6. **ExportaciÃ³n CSV**: Tabla estandarizada a Google Drive.
7. **ExportaciÃ³n espacial**: GeoTIFF por hitos fenolÃ³gicos + timelapse semanal NDRE.
8. **IntegraciÃ³n ETâ‚€**: `TODO` â€” Pendiente de fuente de datos meteorolÃ³gicos.

### Protocolo de ValidaciÃ³n por MÃ³dulo

Cada mÃ³dulo debe ser verificable independientemente mediante `print()` en Consola GEE:

- **MÃ³dulo 1 (Pre-procesamiento)**: `print('ImÃ¡genes antes del filtro:', totalCrudas,
  'despuÃ©s:', totalFiltradas)`.
- **MÃ³dulo 2 (Ãndices)**: `print('NDRE mediana parcela 1:', ndreMediana)`.
- **MÃ³dulo 3 (BiofÃ­sica)**: Verificar que LAI âˆˆ [0.1, 6.0], Cab âˆˆ [0, 100].
- **MÃ³dulo 4 (Temporal)**: `print('Semanas interpoladas:', semanasInterpoladas)`.
- **MÃ³dulo 5 (EstrÃ©s)**: `print('Alertas emitidas:', conteoAlertas)`.
- **MÃ³dulo 6 (CSV)**: Verificar en Google Drive que el archivo tiene columnas correctas.
- **MÃ³dulo 7 (Espacial)**: Verificar GeoTIFF abre en QGIS con valores esperados.

### Commits y Versionado

- **Un commit por mÃ³dulo completado y validado.**
- Mensaje de commit: `feat(modulo-N): descripciÃ³n breve`.
- Ejemplo: `feat(modulo-1): doble filtro CS+ (>0.90) + SCL (clases 4,5)`.

---

## Gobernanza

### JerarquÃ­a Documental

1. **Esta ConstituciÃ³n** â€” Principios innegociables. Solo se modifica con justificaciÃ³n
   escrita y actualizaciÃ³n de versiÃ³n.
2. **`Informacion.md`** â€” MetodologÃ­a acadÃ©mica de referencia. La constituciÃ³n deriva
   sus principios de este documento.
3. **`Codigo.md`** â€” ImplementaciÃ³n. Debe cumplir esta constituciÃ³n. Si hay conflicto,
   la constituciÃ³n prevalece.
4. **`Informacionsitio.md`** â€” Contexto agronÃ³mico complementario (no normativo).

### Procedimiento de Enmienda

1. Proponer el cambio con justificaciÃ³n escrita (issue o documento).
2. Evaluar impacto en los 8 principios y en el CSV de salida.
3. Si el cambio afecta el CSV, requiere nueva columna, o elimina un principio: bump
   de versiÃ³n MAJOR.
4. Si el cambio agrega un mÃ³dulo, expande una secciÃ³n: bump MINOR.
5. Si el cambio es correcciÃ³n de errores, ajuste de constantes, clarificaciÃ³n: bump
   PATCH.
6. Actualizar `LAST_AMENDED_DATE` y `CONSTITUTION_VERSION`.
7. Sincronizar `Codigo.md` para reflejar el cambio.

### Compliance Review

- Antes de considerar el script "terminado", se debe ejecutar una revisiÃ³n de
  cumplimiento constitucional: verificar cada uno de los 8 principios contra el
  cÃ³digo.
- Las violaciones se clasifican como:
  - **CrÃ­ticas**: Bloquean la entrega (ej. falta el doble filtro).
  - **Mayores**: Requieren plan de resoluciÃ³n (ej. Whittaker no implementado).
  - **Menores**: Se documentan como limitaciones conocidas (ej. coeficientes LAI
    no validados para Murcott).

---

****Version**: 1.1.0 | **Ratified**: 2026-06-01 | **Last Amended**: 2026-06-02
