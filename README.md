# 11.NFI_LULC_Biomass_Improved (V5)

Improvement of the **LULC Validation** national workflow, extended with the official
**NFI Trees and Shrubs calculation document**.

## Built upon

`F:\1.KSA\1.Forest\10.NFI\10.LULC_Validation`

- Office-point ESA WorldCover / ESRI / dry NDVI validation
- Final LULC / New LCU decision rules and forest-reserve override
- National plot frame (~18k office points)

## Added (calculation document)

`data/docs/NFI_ KSA Calculation_Trees&shrubs.docx`

- Joins: LUCS + Plot + Trees / Shrubs
- Land-use proportion by SU (n plots / 5)
- Tree BA → volume → AGB → BGB → carbon → CO2eq
- Shrub allometric AGB
- Anti-clip SU tree density (CF = 10)

## Colab

Notebook: `NFI_LULC_Biomass_Improved_Colab.ipynb`

Cell 0 clones https://github.com/gabrielsanya-ops/NFI_LULC_Biomass_Improved if Drive is empty.

## Policy

- Carbon labeled **provisional**
- National stock totals **BLOCKED** without design weights / SU area
- Field heights authoritative
