Obtención de Imágenes Satélites
Sentinel-2 y Metodología para
Plantaciones de Mandarina Murcott
Introducción
El presente documento describe la metodología y los pasos para la obtención y procesamiento
de imágenes satelitales, utilizando la plataforma Sentinel-2, con el fin de obtener información de
plantaciones de mandarina Murcott ( Citrus reticulata ). El enfoque se centra en el intervalo
2025-2026.

Objetivos
● Implementar un protocolo de pre-procesamiento (Corrección L2A y doble filtrado de
nubes)
● Cuantificar variables (LAI, Clorofila, 𝐾𝑐) mediante la aplicación de índices espectrales.
● Reconstruir una serie temporal semanal continua mediante técnicas de interpolación y
suavizado (Whittaker y Wavelet).
● Generar series temporales de datos agronómicos (LAI, Clorofila, Kc) de alta
frecuencia y restringir la exportación de imágenes espaciales (Mapas de Calor/RGB) a
los hitos fenológicos del cultivo.
1.1 Definición del Área de Estudio y Caracterización de Unidades
Experimentales.
El área de estudio se circunscribe a un sector productivo de mandarina Murcott ( Citrus
reticulata ) ubicado estratégicamente en la región agrícola de la Provincia de Jujuy, Argentina.
Para el desarrollo del protocolo de monitoreo, se han delimitado cuatro (4) parcelas de estudio,
siendo estas las unidades experimentales para la extracción de series temporales espectrales.
Cada parcela posee una superficie definida de 0,5 hectáreas, totalizando un área de muestreo
de 2,0 hectáreas. La delimitación precisa de la geometría de estas unidades se realizó
previamente mediante planimetría vectorial georreferenciada. Es importante considerar la
escala espacial: una superficie de 0,5 hectáreas equivale a un aproximado de 50 píxeles
nativos de Sentinel-2 (10x10 m).

A continuación se muestra una imagen enumerando las parcelas de muestra.

1.2 Metodología: Preprocesamiento de Datos
Centinela-
La misión Sentinel-2 de la Agencia Espacial Europea (ESA), a través de su constelación de
satélites gemelos (S2A y S2B), ha sido seleccionada como la fuente de datos.

Resolución Temporal y Requerimiento Semanal:

Sentinel-2 ofrece un tiempo de revisión teórica de 5 días en el ecuador (y menor en latitudes
medias).

Resolución Espacial y Espectral:

El sensor MultiSpectral Instrument (MSI) de Sentinel-2 proporciona una resolución espacial de
10 metros para las bandas visibles (RGB) y el Infrarrojo Cercano (NIR), y de 20 metros para las
bandas del Borde Rojo ( Red-Edge ) y el Infrarrojo de Onda Corta (SWIR).

Corrección Atmosférica (Nivel 2A):

Se utilizan productos de Nivel 2A (L2A), los cuales representan la Reflectancia de Superficie.
Estos productos han sido sometidos al procesador Sen2Cor , el cual corrige los efectos de
absorción y dispersión atmosférica causados ​​por aerosoles y vapor de agua.

1.3. Algoritmos de Filtrado de Nubes y Calidad Óptica
Extrema
Para evitar "falsos positivos" se adopta un protocolo de enmascaramiento doble, sustentado en
la literatura para el manejo de plagas y fisiología en cítricos (Della Bellver et al., 2024; Rouault et
al., 2025):

Capa de clasificación de escena (SCL): El primer filtro consiste en utilizar la banda de
clasificación de escena (SCL) generada algorítmicamente por el satélite. A través de este
proceso, se obligó al sistema a retener únicamente los píxeles clasificados explícitamente
como "Vegetación" (Clase 4) o "Suelos desnudos" (Clase 5), descartando nubes de alta y
baja probabilidad, sombras de nubes, agua y píxeles defectuosos.
Red Neuronal Cloud Score+ (CS+): Como medida de seguridad adicional se incorpora la
colección Cloud Score+ (CS+) de Google. CS+ es un modelo de aprendizaje profundo
( Deep Learning ) entrenado para predecir la probabilidad de que un píxel esté limpio. Se aplica una máscara estricta que exige un nivel de certeza superior al 90% (es decir, el valor del índice de limpieza cs_cdf > 0.90).

2. Estrategia Espectral y Cuantificación Biofísica
2.1. El Problema de la Saturación del NDVI en Cítricos
Jóvenes-Adultos
El Índice de Vegetación de Diferencia Normalizada (NDVI) es la métrica más utilizada
globalmente para la teledetección agrícola. Sin embargo, su aplicación como única variable de
monitoreo en huertos de cítricos (como la mandarina Murcott ) de 3 a 4 años de edad
fenológica presenta limitaciones espectrales que deben ser abordadas.

Dinámica del Dosel y Absorción de Luz:

El NDVI se basa en el contraste entre la máxima absorción de la clorofila en la banda Roja y la
máxima reflectancia del mesófilo celular en el Infrarrojo Cercano (NIR).

Según se evidencia en la literatura sobre teledetección en cítricos (Ali et al., 2022), cuando el
Índice de Área Foliar (LAI) de un cultivo de hoja perenne supera el valor umbral de 2.5 a 3.0, la

banda visible Roja se satura. Esto significa que la planta absorbe casi el 100% de la luz roja
incidente; por lo tanto, cualquier aumento posterior en la biomasa foliar o en la concentración
interna de nitrógeno/clorofila no generará cambios apreciables en el valor del NDVI.

Impacto en la Toma de Decisiones Agronómicas:

Si la obtención de datos semanales dependiera exclusivamente del NDVI, el modelo entregaría
una "curva plana" (asintótica) durante la mayor parte del año.

Por lo tanto, se justifica el descarte del NDVI como estimador primario de salud, relegándolo a
un papel secundario como enmascarador general de vegetación. Para el seguimiento
fenológico y nutricional, la metodología debe transicionar hacia regiones del espectro con
menor coeficiente de absorción y mayor penetración en la canopia, específicamente el "Borde
Rojo" ( Red-Edge ).

2.2. Implementación de Índices del Borde Rojo (Red-Edge)
para Cuantificación Biofísica
Para superar la saturación óptica descrita y proporcionar variables fisiológicas procesables,
esta metodología explota la configuración multiespectral del satélite Sentinel-2, el cual cuenta
con tres bandas específicas (B5, B6, B7) ubicadas en la región de transición rápida entre el
Rojo y el Infrarrojo Cercano, conocido como el Borde Rojo ( Red-Edge ).

Sensibilidad del Red-Edge en Doseles Densos:

A diferencia de la banda Roja, la luz en la región del Red-Edge (aprox. 700-740 nm) tiene una
profundidad de penetración mucho mayor en las copas de los cítricos (Ali et al., 2022). Esto
permite que el satélite no solo lea las hojas exteriores, sino la estructura interna del árbol,
reaccionando proporcionalmente a los cambios en la concentración de pigmentos
fotosintéticos.

Se implementan dos índices:

Índice de Diferencia Normalizada del Borde Rojo (NDRE):
𝑁𝐷𝑅𝐸= 𝐵𝐵^88 −+𝐵𝐵^55
El NDRE es altamente sensible a la clorofila de la hoja ya la acumulación de Nitrógeno
(N).
Posición del Borde Rojo de Sentinel-2 (S2REP):
𝑆 2 𝑅𝐸𝑃= 705 + 35
𝐵 04 + 2 𝐵 (^07) −𝐵 05
𝐵 06 +𝐵 07
Según (Ali et al., 2022) se han validado perfiles mediante hiperespectrales que la métrica
S2REP (una interpolación lineal empírica del punto de inflexión del espectro) es el
sustituto para estimar variables agronómicas.
Estimación de LAI y Clorofila (Cab):

El objetivo de este módulo es utilizar modelos de transferencia radiométrica o regresiones
validadas para cítricos, donde el S2REP y el NDRE actúan como variables independientes.
Esto permite generar mapas de:
● Contenido de Clorofila de la Hoja ( 𝐶𝑎𝑏 ): Indicador directo del estado nutricional y
fotosintético.
● Índice de Área Foliar (LAI): Variable estructural crítica para determinar la densidad real
del huerto y parametrizar los modelos de requerimiento hídrico.

Se mantiene el uso del índice NDRE proveniente de la metodología anterior como indicador de
validación cruzada.

2.3. Mitigación de Ruido de Fondo (Suelo y Malezas
Esporádicas)
La resolución espacial de 10 metros de Sentinel-2 implica que un único píxel engloba
fracciones del dosel del mandarino, suelo desnudo interhilar, y vegetación espontánea
(malezas o cultivos de cobertura).

Huerto Joven (4 Años):

Durante el periodo 2025-2026, los mandarinos, no formarán un dosel continuo que cerrará las
calles por completo. Esta arquitectura de plantación exponen el sustrato inferior al satélite. Como
advierten Ippolito et al. (2023), la presencia esporádica de malezas, especialmente tras eventos
de lluvia o riegos ineficientes, genera pulsos de reflectancia verde que los índices tradicionales
(como el NDVI simple) captan incorrectamente como un aumento en el vigor del cultivo principal.

Ajuste Matemático del Píxel (MSAVI2):

La metodología incorpora el Índice de Vegetación Ajustado al Suelo Modificado (MSAVI2),
diseñado específicamente para maximizar la "señal" de la planta de interés y minimizar el "ruido"
del sustrato subyacente. Su formulación matemática no requiere una línea de suelo empírica
(constante L ), lo que lo hace ideal para procesos automatizados:

𝑀𝑆𝐴𝑉𝐼 2 =^2 +𝑁𝐼𝑅+^1 − (^2 *𝑁𝐼𝑅+^1 )

(^2) − 8 (𝑁𝐼𝑅−𝑅𝐸𝐷)
2

3. Reconstrucción Espacio-Temporal de la Serie
de Dato
3.1. Reconstrucción Temporal (Gap-Filling) y Suavizado
Matemático
El Reto de la Frecuencia Temporal en Teledetección Óptica:

Aunque la constelación Sentinel-2 posee un tiempo de revisión teórica de 5 días, la
disponibilidad real de imágenes útiles está fuertemente condicionada por la cobertura nubosa
de la región. Tras aplicar el enmascaramiento por inteligencia artificial (Cloud Score+ > 90% de
pureza) detallado en la Fase I, la serie temporal bruta resultante se vuelve asimétrica. Es
esperable registrar ventanas de 10 a 20 días sin observaciones válidas.

Solución: Modelado y Suavizado de la Serie Temporal
Para transformar estos datos satelitales irregulares en un dataframe ininterrumpido, la
metodología implementa algoritmos de interpolación y suavizado de series temporales:

Filtro e Interpolación de Whittaker:
Según (Rouault et al., 2025) han validado su uso para la integración de datos Sentinel-2 en
modelos de requerimiento de riego y evapotranspiración. Este algoritmo rellena los vacíos
causados ​​por las nubes (gap-filling) asumiendo la trayectoria biológica natural del dosel
de los cítricos. Funciona logrando un equilibrio matemático entre la fidelidad a las
observaciones satelitales originales y la penalización de la aspereza de la curva.
Análisis Wavelet (Transformada Ondícula):
Como validación paralela, el Análisis Wavelet tiene eficacia para procesar series
temporales agrícolas ruidosas provenientes de Sentinel-2 (Ramírez-Juidias et al., 2023). Al
descomponer la señal espectral en sus componentes de tiempo y frecuencia
simultáneamente, el método permite aislar y suprimir el "ruido de alta frecuencia"
(anomalías del sensor a corto plazo).
Entregable del Módulo (El "Dato Semanal"):

Entregable del Módulo (Datos Continuos vs. Imágenes Discretas): A través de los
algoritmos de suavizado (Whittaker/Wavelet), se remuestrean las matrices de datos, no
las imágenes físicas. El producto resultante es un vector de datos tabulares (LAI, Cab, Kc)
validado y continuo para un día fijo de la semana.

Restricción de Exportación de Imágenes (JPG/GeoTIFF): La exportación de mapas
espaciales se restringirá a fechas comprobadas de cielo despejado que coinciden con
hitos fenológicos agronómicamente relevantes:

Reposo y poda (Julio - Agosto).
Floración plena y cuaje (Octubre - Diciembre).
Proximidad de cosecha (Abril - Junio).
4. Aplicaciones Agronómicas y Entrega de
Resultados
4.1. Estimación del Coeficiente de Cultivo Real (Kc)
El tradicional cálculo de la Evapotranspiración del cultivo (𝐸𝑇𝑐) se realiza multiplicando la
Evapotranspiración de referencia (𝐸𝑇 0 ), obtenida de estaciones meteorológicas) por un
Coeficiente de Cultivo (𝐾𝑐) tabulado (metodología FAO-56). Sin embargo, los valores tabulados
de 𝐾𝑐 son teóricos y no reflejan la realidad dinámica, las podas, o el vigor específico de cada
parcela.

Para resolver esto, Ippolito et al. (2023) demostraron en huertos de cítricos que es posible
derivar un Coeficiente de Cultivo actual o real utilizando índices de vegetación extraídos de
Sentinel-2. Asimismo, Rouault et al. (2025) la asimilación de variables suavizadas
temporalmente (como el LAI o FCOVER) en modelos agronómicos (ej. SIMETAW) reducen la
incertidumbre en el cálculo de los requerimientos de riego semanales.

Metodología de Traducción Espectral a 𝐾𝑐 :

Basándonos en Ippolito et al. (2023), el impacto de las malezas esporádicas en los huertos de
cítricos, la metodología utilizará la serie temporal reconstruida del índice purificado MSAVI .

El proceso será el siguiente:

El algoritmo extrae el valor del índice ajustado (sin ruido de suelo/maleza) para la semana
(i).
Mediante una función de transferencia empírica, el valor espectral se convierte en el
Coeficiente de Cultivo real (𝐾𝑐 𝑠𝑎𝑡𝑒𝑙𝑖𝑡𝑎𝑙).
El sistema cruza este dato con la 𝐸𝑇 0 de la estación meteorológica local para calcular:
𝐸𝑇𝑐=𝐸𝑇 0 *𝐾𝑐 𝑠𝑎𝑡𝑒𝑙𝑖𝑡𝑎𝑙
4.2. Detección de Estrés
Della Bellver et al. (2024) , en su estudio sobre la detección de la plaga de la cochinilla
( Delottococcus aberiae ) utilizando Sentinel-2 en el este de España, las caídas en las firmas

espectrales, específicamente en las bandas del Borde Rojo ( Red-Edge ) y en la estimación del
Índice de Área Foliar (LAI), actúan como indicadores tempranos de infestación o estrés.

El sistema funcionará bajo las siguientes reglas:

Línea Base Dinámica: El algoritmo no compara el valor actual con un umbral fijo, sino con
el comportamiento fenológico histórico esperado (la "memoria" matemática de la curva
de Whittaker/Wavelet).
Identificación de la Anomalía: Si en la semana actual (𝑇 0 ), la parcela registra una caída
del LAI o del contenido de Clorofila (𝐶𝑎𝑏) que supera la desviación histórica estándar
permitida, el sistema la marca como "anómala". Como las nubes ya fueron filtradas (Cloud
Score+) y las malezas aisladas (MSAVI2).
4.3. Formato de Entrega
Estructura del Conjunto de Datos (Dataset):

El producto final del script alojado en la nube será un archivo tabular estandarizado (.CSV)
exportado automáticamente a un repositorio compartido (Google Drive / SharePoint) obtenido
a través de un script de GEE. El protocolo de datos incluye las siguientes columnas por cada
registro:

Fecha_Semanal: Fecha regularizada por el algoritmo temporal.
ID_Parcela: Identificador único de las 4 parcelas de estudio.
LAI_RedEdge: Índice de Área Foliar estimado mediante S2REP.
Cab_RedEdge: Contenido de Clorofila subrogado.
Kc_Actual: Coeficiente de cultivo derivado de MSAVI2.
Flag_Interpolacion: Un indicador binario (0/1) que informa al agrícola si el dato de esa
semana es una observación satelital real y despejada, o si fue matemáticamente
interpolado (Whittaker/Wavelet) debido a una cobertura nubosa.
Alerta_Estres: Indicador de anomalía (Normal / Precaución / Alerta Crítica).
Entregable del Módulo (Datos Continuos y Visualización Espacial): A través de los
algoritmos de suavizado (Whittaker/Wavelet), se remuestrean las matrices de datos para
obtener un vector de datos tabulares (LAI, Cab, Kc) validado y continuo.

● Exportación de Imágenes Semanales y Mitigación de Nubes: Para satisfacer los
requerimientos del monitoreo agronómico de campo, se generarán
composiciones espaciales (mosaicos) semanales. Dado el filtrado de calidad
óptica (Cloud Score+ > 90%), es físicamente esperado que en semanas de alta
nubosidad las imágenes presenten vacíos (gaps) o ausencia total de datos.
● Índice de Visualización Óptimo: Se prescinde del NDVI debido a su conocida
saturación en canopias cítricas densas. Toda la representación visual semanal se
se entregará utilizando el Índice de Borde Rojo (NDRE).