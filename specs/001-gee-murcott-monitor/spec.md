# Feature Specification: Monitoreo Satelital de Mandarina Murcott

**Feature Branch**: `001-gee-murcott-monitor`

**Created**: 2026-06-01

**Status**: Draft

**Input**: Script unificado de Google Earth Engine para monitoreo satelital de 4 parcelas de
mandarina Murcott en Jujuy, Argentina (2025-2026), aplicando metodologia de teledeteccion
con Sentinel-2 L2A, indices de Borde Rojo, y reconstruccion temporal.



## Clarifications

### Session 2026-06-01

- Q: Cual formula S2REP usar: la del documento metodologico vs. la estandar de literatura? → A: Formula estandar de Ali et al. (2022): 705 + 35 * (((B4+B7)/2 - B5) / (B6 - B5)). Descartada la formula alternativa del documento por ser probable artefacto de formato.
- Q: Que algoritmo de gap-filling usar dado que Whittaker no es nativo de GEE? → A: Savitzky-Golay (filtro de ventana movil con ajuste polinomico). Similar comportamiento a Whittaker, compatible con GEE via reduceNeighborhood.
- Q: Que coeficientes usar para modelos LAI/Cab/Kc dado que no estan validados para Murcott? → A: Coeficientes configurables como parametros al inicio del script, con valores actuales como defaults (LAI: 0.15, Cab: 2, Kc: 1.15 y 0.1). Facilita calibracion futura sin modificar codigo.
- Q: Implementar analisis Wavelet en v1 o diferirlo dado que Savitzky-Golay ya cubre el suavizado? → A: Diferir Wavelet a version futura. Savitzky-Golay cubre el objetivo funcional de supresion de ruido. Wavelet se documenta como mejora planificada para validacion con datos de campo.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Pre-procesamiento y Filtrado de Calidad (Priority: P1)

El ingeniero agronomo necesita imagenes satelitales libres de nubes y con correccion
atmosferica para las 4 parcelas de estudio, de modo que los analisis posteriores no esten
contaminados por artefactos atmosfericos ni pixeles no confiables.

**Why this priority**: Sin datos limpios, todo analisis posterior es invalido. Es el primer
eslabon de la cadena de procesamiento. Si el filtrado falla, las metricas de salud del
cultivo (LAI, clorofila, estres) seran incorrectas.

**Independent Test**: Ejecutar el filtrado sobre el periodo 2025-2026 y verificar que
(a) todas las imagenes retenidas tienen reflectancia de superficie corregida (L2A),
(b) ningun pixel clasificado como nube, sombra de nube, agua, nieve o defectuoso pasa el
filtro, y (c) se reporta la proporcion de imagenes descartadas vs. retenidas para
trazabilidad del proceso.

**Acceptance Scenarios**:

1. **Given** el periodo 2025-01-01 a 2026-06-01 y las 4 parcelas definidas, **When** se
   aplica el doble filtro de calidad optica, **Then** solo pixeles con probabilidad de
   limpieza superior al 90% Y clasificados como Vegetacion (clase 4) o Suelo desnudo
   (clase 5) son retenidos para calculos posteriores.
2. **Given** una imagen satelital con nubes densas sobre las parcelas, **When** se
   procesa, **Then** los pixeles nubosos son completamente enmascarados (valor nulo) y no
   contribuyen a promedios, medianas ni calculos de indices.

---

### User Story 2 - Calculo de Indices Espectrales de Borde Rojo (Priority: P1)

El agronomo necesita indices espectrales que reflejen el vigor y la salud del cultivo sin
saturarse en doseles densos de citricos, para tomar decisiones informadas de fertilizacion
nitrogenada y riego.

**Why this priority**: Los indices son la base matematica para estimar LAI, clorofila y
coeficiente de cultivo (Kc). El NDVI tradicional se satura en mandarinos jovenes-adultos
(LAI > 2.5), volviendose inservible para monitoreo. Los indices de Borde Rojo (NDRE,
S2REP, MSAVI2) son el reemplazo metodologicamente validado.

**Independent Test**: Verificar que los valores de NDRE estan en rango [0.1, 0.6],
MSAVI2 en [0.2, 0.8], y S2REP en [700, 740] nm para citricos. Verificar que NDVI
permanece constante (asintotico) en parcelas con alta densidad foliar mientras NDRE
muestra variabilidad.

**Acceptance Scenarios**:

1. **Given** imagenes filtradas por calidad, **When** se calculan los indices
   espectrales, **Then** NDRE, S2REP, y MSAVI2 se generan para cada pixel de cada
   parcela en cada fecha con datos validos.
2. **Given** una parcela con cobertura vegetal densa (dosel cerrado), **When** se
   comparan las series temporales de NDVI vs NDRE, **Then** NDRE muestra variabilidad
   estacional mientras NDVI permanece asintotico (plano), confirmando la saturacion
   documentada en la literatura.
3. **Given** el indice MSAVI2, **When** se evalua en parcelas con suelo expuesto o
   malezas en callejones, **Then** el indice minimiza la contribucion espectral del
   suelo, aislando la senal del cultivo principal.

---

### User Story 3 - Estimacion de Variables Biofisicas (Priority: P2)

El agronomo necesita valores cuantitativos semanales de Indice de Area Foliar (LAI),
contenido de Clorofila foliar (Cab) y Coeficiente de Cultivo real (Kc) para parametrizar
modelos de requerimiento hidrico y evaluar el estado nutricional del cultivo.

**Why this priority**: Estas variables alimentan directamente los modelos agronomicos de
riego (FAO-56, SIMETAW). Sin ellas, el ingeniero agronomo no puede calcular la
evapotranspiracion real del cultivo (ETc) ni detectar deficiencias nutricionales
tempranas.

**Independent Test**: Verificar que LAI ∈ [0.1, 6.0], Cab ∈ [0, 100] μg/cm2, y
Kc ∈ [0.2, 1.3] para mandarinos jovenes-adultos. Realizar prueba de sensibilidad:
aplicar un incremento conocido en S2REP y verificar que LAI y Cab aumentan
proporcionalmente.

**Acceptance Scenarios**:

1. **Given** los indices espectrales NDRE y S2REP calculados, **When** se aplican los
   modelos de estimacion biofisica, **Then** se obtienen valores semanales de LAI
   (adimensional), Cab (μg/cm2), y Kc (adimensional) para cada una de las 4 parcelas.
2. **Given** una parcela tras un evento de fertilizacion nitrogenada (noviembre, segun
   calendario fenologico), **When** se analiza la serie temporal de Cab, **Then** se
   detecta un incremento en el contenido de clorofila en las semanas posteriores a la
   aplicacion.
3. **Given** el Kc derivado de MSAVI2, **When** se compara con valores tabulados FAO-56
   para citricos, **Then** el Kc satelital refleja variabilidad estacional (mayor en
   verano, menor en invierno) que los valores tabulados estaticos no capturan.

---


### User Story 4 - Reconstruccion de Serie Temporal Continua (Priority: P2)

El agronomo necesita una serie de datos semanales ininterrumpida para cada parcela, incluso en semanas donde la cobertura nubosa impide observaciones satelitales directas. Sin esta continuidad, los modelos de riego y las curvas fenologicas presentan vacios que dificultan la toma de decisiones.

**Why this priority**: En la region de Jujuy, es esperable tener ventanas de 10 a 20 dias sin observaciones validas tras el filtrado de nubes. La interpolacion inteligente que respeta la trayectoria biologica del cultivo es esencial para mantener la utilidad agronomica de la serie temporal.

**Independent Test**: Verificar que la serie de salida tiene exactamente un registro por parcela por semana para todo el periodo (sin semanas faltantes). Verificar que el campo Flag_Interpolacion marca correctamente con 0 las semanas con datos reales y con 1 las semanas donde el valor fue generado matematicamente.

**Acceptance Scenarios**:

1. **Given** una semana sin ninguna imagen valida por nubosidad persistente, **When** se ejecuta el algoritmo de reconstruccion temporal, **Then** se genera un valor estimado para LAI, Cab y Kc que sigue la tendencia fenologica del cultivo, y Flag_Interpolacion = 1.
2. **Given** la serie temporal completa de 78 semanas, **When** se inspecciona la continuidad, **Then** no existen semanas faltantes para ninguna de las 4 parcelas, y la serie es uniformemente espaciada a intervalos de 7 dias.
3. **Given** una semana con datos reales de alta calidad, **When** se verifica el registro, **Then** Flag_Interpolacion = 0 y los valores provienen directamente de observaciones satelitales.

---

### User Story 5 - Deteccion Temprana de Estres del Cultivo (Priority: P3)

El agronomo necesita alertas automaticas cuando una parcela muestra desviaciones anomalas en su firma espectral respecto a su comportamiento historico, permitiendo intervencion temprana ante plagas (ej. cochinilla, acaros), deficit hidrico, o deficiencias nutricionales.

**Why this priority**: La deteccion temprana de estres reduce perdidas de cosecha y optimiza el uso dirigido de agroquimicos. La metodologia cita a Della Bellver et al. (2024), quienes demostraron que caidas en las firmas espectrales del Borde Rojo actuan como indicadores tempranos de infestacion por cochinilla en citricos.

**Independent Test**: Simular una caida del 40 por ciento en LAI para una semana especifica y verificar que el sistema emite Alerta Critica para esa parcela en esa fecha. Simular una caida del 15 por ciento y verificar que emite Precaución. Verificar que valores dentro de mas-menos 1 desviacion estandar no generan alertas.

**Acceptance Scenarios**:

1. **Given** una parcela con LAI y Cab dentro de mas-menos 1 desviacion estandar de su linea base historica, **When** se evalua el nivel de estres, **Then** la alerta es Normal.
2. **Given** una parcela con caida de Cab entre 1 y 2 desviaciones estandar, **When** se evalua, **Then** la alerta es Precaución.
3. **Given** una parcela con caida de LAI o Cab superior a 2 desviaciones estandar respecto a la linea base, **When** se evalua, **Then** la alerta es Alerta Critica, indicando posible infestacion o estres severo.

---

### User Story 6 - Exportacion de Resultados y Visualizacion (Priority: P3)

El agronomo necesita descargar los resultados en formatos utilizables fuera de la plataforma de procesamiento: un archivo tabular (CSV) con todas las variables semanales para analisis en planillas de calculo o software estadistico, y mapas espaciales (GeoTIFF) en momentos fenologicos clave para inspeccion visual en campo. Tambien necesita una visualizacion animada (timelapse) para comunicar la evolucion del cultivo a tecnicos y directivos.

**Why this priority**: Sin exportacion, los datos quedan inaccesibles para el agronomo en el campo. El CSV permite integrar los datos satelitales con informacion meteorologica (ETo) y planillas de riego. Los mapas en hitos fenologicos permiten validacion visual contra observaciones en terreno.

**Independent Test**: Verificar que el CSV descargado contiene exactamente 7 columnas con los nombres especificados y una fila por parcela por semana. Verificar que los mapas GeoTIFF exportados cubren la extension completa de las 4 parcelas. Verificar que el timelapse se reproduce sin errores y muestra la fecha en cada frame.

**Acceptance Scenarios**:

1. **Given** el procesamiento completo de la serie temporal, **When** se exporta el archivo CSV, **Then** contiene las columnas: Fecha_Semanal, ID_Parcela, LAI_RedEdge, Cab_RedEdge, Kc_Actual, Flag_Interpolacion, Alerta_Estres, con tipos de datos consistentes en todas las filas.
2. **Given** los tres hitos fenologicos definidos (Reposo/Poda Jul-Ago, Floracion/Cuaje Oct-Dic, Cosecha Abr-Jun), **When** se exportan los mapas espaciales, **Then** se genera un GeoTIFF NDRE para cada hito, cubriendo las 4 parcelas con resolucion espacial de 10 metros.
3. **Given** el periodo completo 2025-2026, **When** se genera la animacion semanal, **Then** el timelapse contiene al menos 78 frames (uno por semana) con la fecha visible y utiliza NDRE como indice de visualizacion.

---

## Edge Cases

- Que sucede cuando una parcela tiene 0 imagenes validas en todo un mes por nubosidad extrema (ej. enero-febrero, pico de lluvias en Jujuy)?
- Como maneja el sistema valores de S2REP fuera del rango fisiologico esperado (705-740 nm) causados por pixeles mixtos o errores de sensor?
- Que sucede si el archivo vectorial de parcelas no esta disponible en la plataforma o contiene geometrias invalidas (autointersecciones, anillos abiertos)?
- Como se comporta el sistema en las semanas del borde del periodo (enero 2025, junio 2026) donde no hay suficientes datos historicos para construir la linea base o la ventana de interpolacion?
- Que sucede si la coleccion Cloud Score+ no tiene cobertura para una fecha especifica (fallo en la coleccion auxiliar de Google)?
- Como se manejan los cambios de cobertura de suelo (ej. renovacion de parcela, arboles removidos) que producen caidas reales y permanentes en los indices, diferentes al estres temporal?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE trabajar exclusivamente con productos de reflectancia de superficie con correccion atmosferica aplicada (equivalente a Sentinel-2 Nivel 2A procesado con Sen2Cor).
- **FR-002**: El sistema DEBE aplicar un doble filtro de calidad optica sobre cada imagen: (a) enmascarar pixeles con probabilidad de estar limpios inferior al 90 por ciento segun modelo de aprendizaje profundo, y (b) retener exclusivamente pixeles clasificados como Vegetacion o Suelo desnudo en la capa de clasificacion de escena.
- **FR-003**: El sistema DEBE reportar, para trazabilidad, la cantidad de imagenes que ingresan al proceso y la cantidad que sobreviven al doble filtrado.
- **FR-004**: El sistema DEBE calcular los indices espectrales NDVI, NDRE (Normalized Difference Red-Edge), S2REP (Sentinel-2 Red-Edge Position), y MSAVI2 (Modified Soil-Adjusted Vegetation Index 2) para cada pixel valido de cada parcela.
- **FR-005**: El sistema DEBE restringir el NDVI a funcion de enmascarador binario de vegetacion (NDVI mayor que 0.3 implica vegetacion presente), sin usarlo como variable independiente para estimaciones biofisicas.
- **FR-006**: El sistema DEBE usar los indices de Borde Rojo (NDRE y S2REP) como variables independientes principales para la estimacion de Indice de Area Foliar (LAI) y contenido de Clorofila foliar (Cab). La formula S2REP utilizada es la estandar de literatura: 705 + 35 * (((B4+B7)/2 - B5) / (B6 - B5)) (Ali et al., 2022). Los coeficientes del modelo LAI/Cab son parametros configurables al inicio del script (valores default: LAI_factor=0.15, Cab_factor=2), facilitando calibracion futura sin reescribir la logica.
- **FR-007**: El sistema DEBE derivar el Coeficiente de Cultivo real (Kc) a partir del indice MSAVI2 purificado, mediante la funcion de transferencia Kc = MSAVI2 * kc_slope + kc_intercept. Los coeficientes kc_slope (default: 1.15) y kc_intercept (default: 0.1) son parametros configurables al inicio del script, sujetos a calibracion con datos de campo.
- **FR-008**: El sistema DEBE producir exactamente un registro semanal por parcela, generando una serie temporal uniformemente espaciada (intervalos de 7 dias) para todo el periodo de estudio.
- **FR-009**: El sistema DEBE aplicar el filtro Savitzky-Golay como algoritmo de reconstruccion temporal (gap-filling). Este filtro estima valores para semanas sin datos satelitales mediante una ventana movil con ajuste polinomico, respetando la trayectoria fenologica del cultivo. Parametros iniciales: ventana de 5 puntos, polinomio grado 2.
- **FR-010**: El sistema DEBE aplicar el filtro Savitzky-Golay para suavizado de la serie temporal, suprimiendo ruido de alta frecuencia (anomalias de sensor de corto plazo) mientras preserva las tendencias fenologicas de baja frecuencia.
- **FR-011**: El sistema DEBE incluir en cada registro semanal un indicador binario (Flag_Interpolacion) que distinga observaciones satelitales reales (0) de valores generados matematicamente por gap-filling (1).
- **FR-012**: El sistema DEBE construir una linea base dinamica del comportamiento fenologico historico para cada parcela y variable (LAI, Cab), actualizada conforme se acumulan mas observaciones.
- **FR-013**: El sistema DEBE comparar cada valor semanal de LAI y Cab contra su linea base dinamica, calculando la desviacion en unidades de desviacion estandar.
- **FR-014**: El sistema DEBE clasificar el nivel de estres en tres categorias: Normal (dentro de mas-menos 1 desviacion estandar), Precaución (caida entre 1 y 2 desviaciones), y Alerta Critica (caida mayor a 2 desviaciones).
- **FR-015**: El sistema DEBE exportar un archivo tabular estructurado (CSV) con exactamente siete columnas en el siguiente orden: Fecha_Semanal, ID_Parcela, LAI_RedEdge, Cab_RedEdge, Kc_Actual, Flag_Interpolacion, Alerta_Estres.
- **FR-016**: El sistema DEBE exportar imagenes espaciales (mapas de NDRE) exclusivamente en los tres hitos fenologicos definidos: Reposo y Poda (julio-agosto), Floracion plena y Cuaje (octubre-diciembre), y Proximidad de Cosecha (abril-junio).
- **FR-017**: El sistema DEBE generar una secuencia animada (timelapse) con un cuadro por semana utilizando el indice NDRE como variable de visualizacion, con la fecha correspondiente visible en cada cuadro.

### Key Entities

- **Parcela**: Unidad experimental de 0.5 hectareas delimitada por geometria vectorial georreferenciada. Existen 4 parcelas. Cultivo: Mandarina Murcott (Citrus reticulata) implantada entre 2022-2023. Marco de plantacion: 5.5 m entre hileras x 3.5 m entre plantas.
- **Registro Semanal**: Fila en la serie temporal de salida. Contiene: fecha regularizada, identificador de parcela, valor de LAI estimado, valor de clorofila estimado, Kc actual, indicador de origen del dato (real/interpolado), y clasificacion de nivel de estres.
- **Hito Fenologico**: Periodo del calendario agricola con relevancia agronomica para la exportacion de mapas espaciales. Definido por nombre, fecha de inicio y fecha de fin.
- **Linea Base Dinamica**: Comportamiento fenologico esperado para cada variable (LAI, Cab) derivado del suavizado de la serie historica. Sirve como referencia movil para la deteccion de anomalias, actualizandose con cada nueva observacion real.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El sistema retiene al menos el 40 por ciento de las imagenes disponibles tras aplicar el doble filtro de calidad optica, medido sobre el periodo completo 2025-2026 (indicador de que el filtrado no es excesivamente restrictivo).
- **SC-002**: El cien por ciento de las semanas del periodo de estudio (78 semanas) tienen un registro en la serie temporal de salida para cada una de las 4 parcelas, sin excepciones ni semanas faltantes.
- **SC-003**: Los valores de NDRE para parcelas con vegetacion sana y sin estres estan en el rango 0.25 a 0.55, consistente con los valores reportados en la literatura para plantaciones de citricos (Ali et al., 2022). Los coeficientes del modelo LAI/Cab son parametros configurables al inicio del script (valores default: LAI_factor=0.15, Cab_factor=2), facilitando calibracion futura sin reescribir la logica.
- **SC-004**: El sistema clasifica correctamente como Alerta Critica una anomalia simulada consistente en una caida de LAI superior a 2 desviaciones estandar respecto a la linea base, verificable en un caso de prueba controlado.
- **SC-005**: El archivo CSV de salida contiene exactamente 7 columnas con los nombres y tipos de datos especificados en FR-015, verificable mediante inspeccion de schema sin necesidad de abrir el archivo manualmente.
- **SC-006**: Las imagenes espaciales (GeoTIFF) exportadas para cada hito fenologico cubren la extension completa de las 4 parcelas con una resolucion espacial de 10 metros, sin artefactos de borde ni recortes incompletos.
- **SC-007**: La animacion semanal (timelapse) contiene al menos 78 cuadros, uno por cada semana del periodo, con la fecha correspondiente legible en cada cuadro y utilizando el indice NDRE para la representacion cromatica del vigor del cultivo.

## Assumptions

- Las 4 parcelas estan correctamente delimitadas en el archivo vectorial de entrada, sus geometrias son validas (sin autointersecciones ni anillos abiertos) y no se solapan entre si.
- La constelacion Sentinel-2 (satelites S2A y S2B) mantiene su frecuencia de revisita nominal de aproximadamente 5 dias durante todo el periodo 2025-2026, sin interrupciones prolongadas del servicio.
- El modelo Cloud Score+ (CS+) de Google tiene cobertura completa y actualizada para la region de la Provincia de Jujuy, Argentina, durante el periodo de estudio.
- Los coeficientes de los modelos de estimacion de LAI y Clorofila (Cab) son aproximaciones lineales iniciales basadas en S2REP, sujetas a calibracion futura con mediciones de campo (LICOR, SPAD) cuando se disponga de datos de verdad-terreno.
- Los coeficientes de la funcion de transferencia MSAVI2 a Kc son valores empiricos iniciales, sujetos a validacion con datos de evapotranspiracion medidos en campo.
- La estacion meteorologica local mas cercana proporciona datos de evapotranspiracion de referencia (ETo), pero su integracion directa en el sistema esta fuera del alcance de esta version. El sistema entrega Kc; el calculo de ETc = ETo x Kc queda como responsabilidad del usuario.
- El usuario final (ingeniero agronomo) tiene acceso a una cuenta de Google Drive para recibir los archivos CSV y GeoTIFF exportados por el sistema.
- El periodo de estudio (enero 2025 a junio 2026) cubre al menos un ciclo fenologico completo: reposo invernal, brotacion, floracion, cuaje, crecimiento de fruto, maduracion y cosecha.
- Las malezas y cultivos de cobertura presentes en los callejones entre hileras son espectralmente mitigados por el indice MSAVI2, no requiriendo un enmascaramiento adicional ni algoritmo de separacion espectral.
- La finca mantiene las practicas de manejo descritas en el contexto agronomico (fertilizacion con urea en noviembre, aplicaciones de potasio entre octubre y febrero, riego por goteo, desmalezado quincenal), garantizando que los cambios espectrales detectados son atribuibles a la fenologia del cultivo y no a cambios abruptos de manejo.
- El analisis Wavelet (validacion paralela de supresion de ruido) queda explicitamente fuera del alcance de la version 1. El filtro Savitzky-Golay asume ambas funciones (gap-filling y supresion de ruido). Wavelet se planifica como mejora futura cuando se disponga de datos de campo para validacion cruzada (Ramirez-Juidias et al., 2023).

