# FloodLens

**Explainable Flood Exposure Intelligence for Urban Infrastructure**

FloodLens is an independent, open-source-oriented WebGIS portfolio project that analyzes how officially mapped flood-hazard zones intersect urban infrastructure.

The project uses Python, GeoPandas, and Shapely for spatial analysis and is being developed into an interactive application using React and MapLibre GL JS.

**Study Area:** Philadelphia, Pennsylvania, with an initial focus on the Schuylkill River corridor.

**Project Status:** GIS analysis pipeline completed. Interactive WebGIS application under development.

## 1. Project Overview

Flood hazard maps show where flooding is statistically more likely, but understanding which infrastructure assets intersect these areas requires additional spatial analysis.

FloodLens addresses this problem by:

- Analyzing street and trail centerlines against FEMA flood-hazard polygons.
- Measuring the length of each segment intersecting mapped hazard areas.
- Classifying segments by their mapped exposure.
- Generating transparent, human-readable explanations.
- Preparing spatial datasets for interactive WebGIS visualization.

The goal is to make geographic exposure information easier to explore and understand.

## 2. Initial Analysis Results

The first analysis covers a selected area of Philadelphia near the Schuylkill River.

| Metric | Result |
|---|---:|
| Street/trail segments analyzed | 3,097 |
| Segments intersecting selected hazard areas | 167 |
| Special Flood Hazard Area segments | 127 |
| Moderate-hazard segments | 129 |
| High-hazard centerline overlap | 22.09 km |
| Moderate-hazard centerline overlap | 5.73 km |
| Total mapped centerline overlap | 27.81 km |

### Exposure Classification

| Classification | Segments |
|---|---:|
| High only | 38 |
| Moderate only | 40 |
| Both categories | 89 |
| No mapped exposure | 2,930 |

The classifications are based on spatial intersections between mapped flood-hazard polygons and street/trail centerlines. The categories are mutually exclusive, and high-hazard areas are excluded from moderate-hazard overlap calculations to prevent double-counting.

### Example: Explainable Exposure

**Street:** N Schuylkill River Trl

**Segment ID:** 522438

**Classification:** High only

**Explanation:**

N SCHUYLKILL RIVER TRL intersects a mapped Special Flood Hazard Area for approximately 360.4 meters (100.0% of the analyzed segment).

Explanations are generated deterministically from spatial measurements rather than by a generative AI model.

## 3. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Geospatial data processing |
| GeoPandas | Spatial analysis and geographic datasets |
| Shapely | Geometry operations |
| Pyogrio | Geographic file input/output |
| Jupyter Notebook | Data exploration and experimentation |
| GeoJSON | Spatial data exchange |
| React | Planned interactive frontend |
| MapLibre GL JS | Planned browser-based map visualization |
| GitHub Pages | Planned public deployment |

## 4. Data Sources

FloodLens uses publicly accessible geographic datasets.

**FEMA Flood Plain 2023, Philadelphia**

https://opendataphilly.org/datasets/fema-flood-plain/

**Philadelphia Street Centerlines**

https://opendataphilly.org/datasets/street-centerlines/

Original datasets are not included in this repository. Review the source metadata, usage terms, and available versions before reproducing the analysis.

## 5. Project Structure

```text
FloodLens/
├── data/
│   ├── raw/
│   └── processed/
│       ├── roads_exposure.geojson
│       ├── flood_hazards.geojson
│       └── summary.json
├── notebooks/
│   └── 01_explore_flood_data.ipynb
├── scripts/
│   └── analyze_exposure.py
├── frontend/
├── docs/
├── requirements.txt
├── .gitignore
└── README.md
```

## 6. Spatial Analysis Methodology

The GIS pipeline follows these steps:

1. Load original FEMA floodplain and Philadelphia street-centerline datasets.
2. Clip both datasets to the selected study area.
3. Reproject geometries from EPSG:4326 to EPSG:26918 for meter-based length calculations.
4. Identify Special Flood Hazard Areas and moderate-hazard polygons.
5. Dissolve hazard geometries and remove overlaps between analytical categories.
6. Calculate intersecting street-centerline lengths.
7. Classify each street segment.
8. Generate deterministic exposure explanations.
9. Export results to GeoJSON and JSON.
10. Validate output geometry, identifiers, classifications, and summary statistics.

## 7. Running the GIS Pipeline Locally

### Requirements

- Python 3.13
- Git
- Dependencies listed in `requirements.txt`

### Setup

Clone the repository:

```bash
git clone https://github.com/ssrasmij/floodlens.git
cd floodlens
```

Create a Python virtual environment:

```bash
python -m venv .venv
```

On Windows PowerShell, install dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Download the two original datasets from the sources above, and save them as:

```text
data/raw/fema_floodplain_2023.geojson
data/raw/philadelphia_streets.geojson
```

Run the processing pipeline:

```powershell
.\.venv\Scripts\python.exe scripts\analyze_exposure.py
```

The script generates the processed datasets inside `data/processed/`.

## 8. Validation

The initial pipeline passed automated checks covering:

- 3,097 unique street segment identifiers.
- No missing or invalid exported geometries.
- No negative measured overlap lengths.
- No combined overlap lengths exceeding segment length beyond numerical tolerance.
- Consistent exposure classification counts.
- Successful GeoJSON round-trip validation.
- Consistent summary statistics across output files.

Additional independent geographic spot-checks and user-interface testing are planned.

## 9. Limitations

FloodLens measures overlap between published flood-hazard polygons and street/trail centerlines.

It does not:

- Predict real-time flooding.
- Estimate water depth or structural damage.
- Establish whether a road is passable or closed.
- Account for all possible flood hazards.
- Guarantee that areas without mapped exposure are flood-safe.

The initial analysis includes both streets and recreational trails. A reported overlap percentage applies to the analyzed centerline segment, not necessarily an entire road or its full surface.

## 10. Development Roadmap

- [x] Acquire and inspect GIS datasets
- [x] Analyze FEMA hazard classifications
- [x] Perform spatial intersections
- [x] Calculate street-level exposure measurements
- [x] Generate exposure classifications and explanations
- [x] Build a reproducible Python analysis pipeline
- [x] Export and validate GeoJSON/JSON datasets
- [ ] Build React and MapLibre frontend
- [ ] Add interactive feature selection and filters
- [ ] Display exposure explanations on the map
- [ ] Complete frontend and geographic QA
- [ ] Deploy live WebGIS application

## 11. Future Enhancements

Potential future developments include infrastructure-type filtering, additional asset datasets, spatial APIs, database integration, and AI-assisted geographic exploration.

## Project Context

FloodLens is an independent geospatial engineering portfolio project developed to explore transparent spatial analysis, modern WebGIS technologies, and practical infrastructure exposure mapping.

It is not affiliated with FEMA, the City of Philadelphia, or the developers of other projects with the same name.