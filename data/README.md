# Datasets de PIN Platform

La carpeta `data/` contiene los insumos operativos usados por ETL, mapas y dashboards.

## Archivos versionados

Los siguientes tipos de archivo pueden publicarse directamente en el repositorio:

- `.csv`
- `.xlsx`
- `.geojson`

## Archivos grandes

Los archivos de gran tamano se gestionan con Git LFS para evitar romper los limites normales de GitHub:

- `Company_Census_File_20260604.csv`
- `NTAD_National_Highway_System_-2908344783259962276.geojson`

## Uso

- El ETL principal lee estos archivos desde `data/`.
- Si agregas nuevos datasets muy grandes, conviene evaluarlos antes de subirlos directamente al repositorio.
