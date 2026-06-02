# CSV Schema Contract: Dataset_Fenologico_Mandarina_Estandarizado

**Version**: 1.0.0
**Format**: CSV (comma-separated values), UTF-8 encoding, header row present
**Delimiter**: comma (,)
**Line ending**: LF (Unix-style)
**Export path**: Google Drive, folder `Tesis_Mandarinas`

## Column Specification

| Position | Column Name | Type | Expected Range | Nullable |
|----------|-------------|------|---------------|----------|
| 1 | Fecha_Semanal | String (YYYY-MM-DD) | 2025-01-01 to 2026-06-01 | No |
| 2 | ID_Parcela | String | "1","2","3","4" | No |
| 3 | LAI_RedEdge | Float | [0.1, 6.0] | Yes* |
| 4 | Cab_RedEdge | Float | [0, 100] | Yes* |
| 5 | Kc_Actual | Float | [0.2, 1.3] | Yes* |
| 6 | Flag_Interpolacion | Integer | 0 or 1 | No |
| 7 | Alerta_Estres | String | Normal/Precaucion/Alerta Critica | No |

*Nullable only at period boundaries (first/last weeks with insufficient data)

## Row Count

Expected: 4 parcels x ~78 weeks = ~312 rows (before null filtering at boundaries)

## Integrity Rules

1. Fecha_Semanal values spaced exactly 7 days apart for each parcel
2. ID_Parcela values match the 4 input parcel identifiers
3. Flag_Interpolacion=1 rows SHALL have Alerta_Estres="Normal" (gaps are not stress)
4. LAI, Cab, Kc must be within physiological ranges
5. (Fecha_Semanal, ID_Parcela) composite unique key

## Backward Compatibility

Schema v1.0.0 is STABLE. Future changes require:
- Constitution amendment (Principle VIII)
- MAJOR version bump if columns added/removed
- MINOR version bump if new optional columns

## Consumer Guidelines

- Import ready: Excel, R (read.csv), Python (pandas), QGIS
- Filter Flag_Interpolacion=1 for real-observation-only analysis
- Alerta_Estres != "Normal" triggers agronomic review
- Kc_Actual x ETo = ETc (ETo from external weather station)

## GEE Export Reference

```
Export.table.toDrive({
  collection: serieLimpia,
  description: "Dataset_Fenologico_Mandarina_Estandarizado",
  folder: "Tesis_Mandarinas",
  fileFormat: "CSV",
  selectors: ["Fecha_Semanal","ID_Parcela","LAI_RedEdge","Cab_RedEdge","Kc_Actual","Flag_Interpolacion","Alerta_Estres"]
});
```

