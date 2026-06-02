# Research: Monitoreo Satelital de Mandarina Murcott (GEE)

**Phase 0 — Technical Decisions & Trade-offs**

## Decision 1: S2REP Formula

**Decision**: Standard literature formula from Ali et al. (2022):
705 + 35 * (((B4+B7)/2 - B5) / (B6 - B5))

**Rationale**: The alternative formula in Informacion.md (705 + 35 * (B4 + 2*B7 - B5) / (B6 + B7))
appears to be a transcription artifact from the document formatting. The standard formula
is the one validated by Ali et al. (2022) in their citrus remote sensing study and is
widely replicated in Sentinel-2 literature. Using the standard ensures comparability with
published results and correct S2REP values in the 705-740 nm range.

**Alternatives considered**: 
- Formula from document → rejected due to lack of independent validation
- Both formulas + comparison → rejected as unnecessary complexity for v1

---

## Decision 2: Gap-Filling Algorithm (Savitzky-Golay instead of Whittaker)

**Decision**: Savitzky-Golay filter (window=5 points, polynomial degree=2) for both
gap-filling and noise suppression.

**Rationale**: The methodology prescribes Whittaker filter (Rouault et al., 2025), but
Whittaker is not natively available in GEE. Implementing it requires custom ee.Array
linear algebra operations that risk hitting GEE memory limits and the 5-minute timeout.
Savitzky-Golay is mathematically similar (both penalize curve roughness while preserving
fidelity to observations), can be implemented via educeNeighborhood() with kernel
convolution, and is already used in published GEE workflows for Sentinel-2 time series
smoothing. The 5-point window is appropriate for the ~5-day Sentinel-2 revisit: it
covers a ±10-day neighborhood, matching the expected gap window of 10-20 days.

**Alternatives considered**:
- Whittaker (custom ee.Array) → rejected for GEE compatibility risk
- LOESS + linear interpolation → rejected as less precise for long gaps
- Median window ±15 days (current code) → rejected as insufficient for trajectory preservation
- Wavelet → deferred to v2; S-G handles noise suppression adequately

**GEE Implementation**: imageCollection.reduceNeighborhood() with a Savitzky-Golay
kernel or iterative ee.Reducer.linearFit() over the temporal dimension.

---

## Decision 3: Model Coefficients (Configurable Parameters)

**Decision**: LAI/Cab/Kc coefficients exposed as script-level constants with current
experimental values as defaults.

**Defaults**:
- LAI_factor = 0.15 → LAI = (S2REP - 700) * LAI_factor
- Cab_factor = 2 → Cab = (S2REP - 700) * Cab_factor  
- kc_slope = 1.15, kc_intercept = 0.1 → Kc = MSAVI2 * kc_slope + kc_intercept

**Rationale**: No published coefficients exist specifically for Murcott mandarin in
Jujuy. Hardcoding values would produce unvalidated results and require code changes for
calibration. Parameterizing them at the script top enables future calibration (LICOR,
SPAD, lysimeter) without touching the processing logic. The default values are
experimental starting points derived from the initial code attempt.

**Alternatives considered**:
- Published citrus coefficients → rejected (none found for Murcott + Jujuy conditions)
- Remove models entirely → rejected (core deliverable)
- Machine learning → rejected (requires training data unavailable at project start)

---

## Decision 4: Wavelet Analysis (Deferred)

**Decision**: Wavelet analysis deferred to future version. v1 relies on Savitzky-Golay
alone for noise suppression.

**Rationale**: The methodology (Ramirez-Juidias et al., 2023) positions Wavelet as
parallel validation for noise suppression. With S-G handling smoothing, the incremental
value of Wavelet in v1 does not justify the implementation complexity (no GEE-native
Wavelet transform). Deferring to v2 allows v1 to deliver functional results while
Wavelet is implemented when field data becomes available for cross-validation.

**Alternatives considered**:
- Full Wavelet in v1 → rejected for GEE compatibility and timeline risk
- Simplified 1-level Wavelet → rejected as insufficient for meaningful validation

---

## Decision 5: NDVI Role (Binary Vegetation Mask)

**Decision**: NDVI calculated but used ONLY as binary mask (NDVI > 0.3 → vegetation).
Not used in any biophysical estimation.

**Rationale**: As documented in Ali et al. (2022), NDVI saturates in citrus canopies
when LAI exceeds 2.5-3.0. Young Murcott trees (planted 2022-2023) are approaching this
threshold. Using NDVI for LAI/Cab estimation would produce flat, uninformative curves.
The binary mask role ensures non-vegetated pixels (roads, bare soil after desmalezado)
are excluded from parcel-level statistics.

---

## Decision 6: Phenological Hit Export Strategy

**Decision**: Export median composites for each phenological period, filtered to clear-sky
dates only (cloud cover < 10% per scene).

**Rationale**: The spec requires "fechas comprobadas de cielo despejado". Since GEE
cannot predict clear-sky dates in advance, the approach is: (a) collect all images in the
phenological window, (b) filter to those where parcel-level cloud cover is < 10%,
(c) compute median composite of the remaining images. This ensures the exported map
represents the best available clear-sky conditions during each milestone period.

**Hitos**:
- Hito 1 (Reposo/Poda): 2025-07-01 to 2025-08-15
- Hito 2 (Floracion/Cuaje): 2025-10-01 to 2025-11-30
- Hito 3 (Cosecha): 2026-04-01 to 2026-05-31
