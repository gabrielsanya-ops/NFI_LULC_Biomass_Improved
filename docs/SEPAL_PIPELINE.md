# KSA NFI LULC - SEPAL pipeline (point-based, no segmentation)

Use FAO **SEPAL** ([https://sepal.io](https://sepal.io)) to map land cover from Sentinel mosaics, trained on your validated NFI points (`final_lulc` / New LCU). No image segmentation is required.

**Official docs:** [SEPAL Cookbook](https://docs.sepal.io/en/latest/cookbook/) · [Classification recipe](https://docs.sepal.io/en/latest/cookbook/classification.html)

---

## Overview

```
Field + Excel (Final LULC)
        │
        ▼
Prepare SEPAL training CSV (lon, lat, class_code)
        │
        ▼
SEPAL account + link Google Earth Engine
        │
        ├─► Optical mosaic (Sentinel-2, dry season)
        │
        └─► Classification recipe
                │
                ├ IMG  → mosaic / EE asset
                ├ LEG  → LUCS / LCML-aligned legend
                ├ TRN  → upload CSV (+ optional CEO)
                ├ AUX  → optional DEM / other
                └ CLS  → Random Forest
                        │
                        ▼
                Export class + probability → GEE / SEPAL
                        │
                        ▼
                Accuracy vs held-out Final LULC points
```

**Reference label:** `final_lulc` (same as New LCU; forest-reserve override already applied).

**Reference geometry:** office plot coordinates (`lon`, `lat` / `office_lon`, `office_lat`).

---

## Phase 0 - Accounts and resources

1. Create / log in to [SEPAL](https://sepal.io).
2. Link your **Google Earth Engine** account in SEPAL (Process → settings / GEE connection).
3. Request computing resources if prompted (CPU/RAM for exports and notebooks).
4. Confirm you can see GEE assets under your project (e.g. `ee-gabrielsanya2`).

---

## Phase 1 - Prepare training data (local)

**Input:** `lucs_office_validated_esa_esri_ndvi.csv` (or the matching `.xlsx`).

**Label column:** `final_lulc`  
**Coordinates:** `lon`, `lat` (EPSG:4326 office DB points)

Run:

```bash
python prepare_sepal_training.py
```

This writes:

| File | Purpose |
|---|---|
| `sepal_training/sepal_train.csv` | 70% of points for SEPAL TRN |
| `sepal_training/sepal_test.csv` | 30% held out for independent accuracy |
| `sepal_training/legend_codes.csv` | Class name ↔ integer code |
| `sepal_training/class_counts.csv` | Sample counts per class |

SEPAL CSV import needs at least:

- geographic coordinates (`longitude`, `latitude`)
- class value (integer code preferred)

Rare classes (e.g. 1-3 points) are kept but flagged; consider merging them into Level-1 groups before national mapping (see Phase 1b).

### Phase 1b - Optional class merge (recommended for mapping)

Imbalanced Final LULC counts make RF unstable for tiny classes. For a first national map, merge rare classes:

| Keep as map class | Merge into |
|---|---|
| Barren Land | - |
| Natural | - |
| Natural Grassland | - |
| Built up area | - |
| Wooded grassland | - |
| Annual Crop | Cultivated |
| Cultivated | Cultivated |
| Perennial crop | Cultivated |
| Forest | Forest |
| Natural regenerated forest | Forest |
| Other woodedland | Other woodedland |
| Wooded grassland | (keep) |
| Inland water, Lake, Pond | Inland water |
| Raffia/Palms - | Other woodedland (or drop) |

Re-run the prep script with `--merge-level1` after you enable that option in the script defaults.

---

## Phase 2 - Area of interest (AOI)

1. In SEPAL **Process**, create or upload an AOI for Saudi Arabia (or NFI regions of interest).
2. Options:
   - Draw / select country boundary in SEPAL
   - Upload a national/admin GeoJSON or shapefile
   - Use an existing GEE FeatureCollection asset
3. Name it clearly, e.g. `KSA_NFI_AOI`.

Start with one province or ecoregion if national mosaics time out; then scale up.

---

## Phase 3 - Optical mosaic (IMG input)

1. Process → green **+** → **Optical mosaic**.
2. Suggested settings for KSA dry-season LULC (align with your August NDVI logic):

| Parameter | Suggested value |
|---|---|
| Sensor | Sentinel-2 |
| Date | 2024-07-01 → 2024-09-30 (adjust if clouds) |
| Composite | Median |
| Cloud masking | Enabled (SCL / cloud probability) |
| AOI | `KSA_NFI_AOI` |
| Recipe name | `KSA_S2_Dry_2024` |

3. Select useful bands (examples):
   - Native: `blue`, `green`, `red`, `nir`, `swir1`, `swir2`
   - Derived: **NDVI** (nir-red), optionally NDWI / NBR
4. Save the recipe.
5. **Optional but recommended:** export the mosaic to a **GEE asset** so Classification runs faster than recomputing the recipe each time.

Radar (Sentinel-1) mosaic is optional; add later if barren vs built-up confusion remains high.

---

## Phase 4 - Classification recipe

1. Process → **+** → **Classification**.
2. Rename tab, e.g. `KSA_LULC_FinalLULC_RF_2024`.

### 4.1 IMG - Image to classify

1. Open **IMG** → **Add**.
2. Select:
   - Saved recipe `KSA_S2_Dry_2024`, **or**
   - Exported GEE mosaic asset (preferred for speed).
3. Add bands (same as mosaic + derived NDVI).
4. Apply → Next.

### 4.2 LEG - Legend

1. Open **LEG**.
2. Build classes from `sepal_training/legend_codes.csv` (name, code, color).
3. Align names with LUCS / LCML documentation when you formalize the legend in LCHS later.
4. Apply → Next.

### 4.3 TRN - Training data

1. Open **TRN** → **Add** → **CSV file**.
2. Upload `sepal_training/sepal_train.csv`.
3. Map columns:
   - Longitude → `longitude`
   - Latitude → `latitude`
   - Class → `class_code`
4. Confirm the class count summary matches expectations.
5. Optional: add a few **on-the-fly** points for rare classes (Forest, water) using imagery in SEPAL.
6. Optional later: add **Collect Earth Online** samples for QC of doubtful plots.

Do **not** upload `sepal_test.csv` into TRN - keep it for independent accuracy.

### 4.4 AUX - Auxiliary data (optional)

Enable if useful for KSA:

- Elevation / slope (SRTM)
- Other global layers available in the AUX tab

Skip on the first run if you want a simple baseline.

### 4.5 CLS - Classifier

| Setting | Suggested |
|---|---|
| Algorithm | **Random Forest** |
| Trees | 100-200 |
| Other | leave defaults first; tune after accuracy review |

Run / render the classification. Inspect class patterns visually against known areas (reserves, cities, irrigated rings).

---

## Phase 5 - Export

1. In the Classification recipe, export:
   - **class** band (map)
   - **probability / confidence** (if available)
2. Destination:
   - Google Earth Engine asset (recommended), and/or
   - SEPAL workspace download (GeoTIFF for QGIS)
3. Naming example: `KSA_LULC_2024_from_FinalLULC_RF`

---

## Phase 6 - Accuracy assessment (outside or in SEPAL/GEE)

Use held-out points (`sepal_test.csv`):

1. Sample the exported classification at test coordinates (GEE `reduceRegions` or QGIS).
2. Build confusion matrix: **Final LULC (reference)** vs **SEPAL map class**.
3. Report overall accuracy, user’s / producer’s accuracy, and per-class F1.
4. Compare also to ESA WorldCover / ESRI (you already have those columns in the enriched CSV).

Minimum success criteria (adjust to project needs):

- Overall accuracy ≥ field-ESA/ESRI agreement context (~55-66% was correspondence, not map OA)
- Forest and Built-up producer’s accuracy reviewed carefully (rare but policy-relevant)

---

## Phase 7 - Optional FAO extensions

| Tool | When to use |
|---|---|
| **LCHS** | Formalize legend in LCML (ISO 19144-2) after map classes stabilize |
| **Collect Earth Online** | Visual reinterpretation of misclassified test points |
| **Class change** recipe | If you later map a second year and need transitions |
| **SEPAL notebooks** | Custom post-processing, area stats, stratified sampling |

Still **no segmentation** required for this pipeline.

---

## Checklist

- [ ] SEPAL + GEE linked  
- [ ] `prepare_sepal_training.py` run; train/test CSVs ready  
- [ ] AOI defined  
- [ ] Dry-season S2 mosaic created (and optionally exported to GEE)  
- [ ] Legend codes match CSV `class_code`  
- [ ] Training CSV imported (train only)  
- [ ] Random Forest classification run  
- [ ] Class + probability exported  
- [ ] Accuracy vs `sepal_test.csv` documented  
- [ ] (Optional) LCML legend in LCHS  

---

## Inputs already in this folder

| Asset | Role |
|---|---|
| `lucs_office_validated_esa_esri_ndvi.csv` | Validated points + Final LULC |
| `level2_catalog_from_field_manual.json` | Class descriptions |
| `prepare_sepal_training.py` | Build SEPAL CSV + legend |
| `PROCESS_AND_VALIDATION.md` | How Final LULC was derived |

---

## Notes and limits

- SEPAL Classification is **pixel-based supervised ML**, not LCML execution and not OBIA segmentation.
- Very rare classes (1-15 points) will not map reliably until merged or supplemented (CEO / on-map clicks).
- National mosaics can hit GEE timeout; prefer **exported mosaic asset** and/or regional tiles.
- Office DB coordinates were used in validation (not field GPS); keep that consistency in SEPAL.
