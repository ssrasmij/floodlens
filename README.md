# FloodLens

**Explainable Flood Exposure Intelligence for Urban Infrastructure**

FloodLens is an open-source WebGIS portfolio project that explores how officially mapped flood-hazard zones intersect urban infrastructure.

## Project Objective

Analyze street-level flood exposure in Philadelphia using public geospatial data and communicate the results through an interactive web application.

## Planned Features

- Interactive flood-hazard map
- Street-level flood exposure analysis
- Explainable spatial intersection results
- Exposure classification and filtering
- Data provenance and analysis limitations

## Technology Stack

- Python
- GeoPandas and Shapely
- React
- MapLibre GL JS
- GeoJSON
- GitHub Pages

## Data Sources

- Philadelphia FEMA Floodplain 2023
- Philadelphia Street Centerlines

## Project Structure

- `data/raw/`: Original downloaded datasets
- `data/processed/`: Analysis outputs
- `scripts/`: Python geospatial processing
- `frontend/`: React and MapLibre application
- `docs/`: Technical documentation

## Project Status

Under active development.

## Limitations

FloodLens analyzes intersections with published flood-hazard areas. It does not predict real-time flooding, road closures, flood depths, or structural damage.
