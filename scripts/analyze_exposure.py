from pathlib import Path
from shapely.geometry import box
import geopandas as gpd
import numpy as np
import json


# Find the project root based on this script's location
PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"


def load_datasets():
    """Load the original floodplain and street datasets."""

    flood_path = RAW_DIR / "fema_floodplain_2023.geojson"
    streets_path = RAW_DIR / "philadelphia_streets.geojson"

    if not flood_path.exists():
        raise FileNotFoundError(flood_path)

    if not streets_path.exists():
        raise FileNotFoundError(streets_path)

    flood = gpd.read_file(flood_path)
    streets = gpd.read_file(streets_path)

    return flood, streets


def prepare_geographic_data(flood, streets):
    """
    Clip both datasets to the study area
    and project coordinates into meters.
    """

    # Study area: Schuylkill River corridor
    west, east = -75.26, -75.17
    south, north = 39.99, 40.05

    study_boundary = box(west, south, east, north)

    # Clip to the study area
    flood_clipped = gpd.clip(flood, study_boundary)
    streets_clipped = gpd.clip(streets, study_boundary)

    # Reproject into a meter-based CRS
    target_crs = "EPSG:26918"

    flood_projected = flood_clipped.to_crs(target_crs)
    streets_projected = streets_clipped.to_crs(target_crs)

    return flood_projected, streets_projected


def select_hazard_zones(flood_projected):
    """
    Select high- and moderate-hazard polygons
    for FloodLens exposure analysis.
    """

    flood_clean = flood_projected.copy()

    # Normalize text attributes
    for column in ["fld_zone", "zone_subty", "sfha_tf"]:
        flood_clean[column] = (
            flood_clean[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    # Special Flood Hazard Areas
    high_hazard = flood_clean[
        flood_clean["sfha_tf"] == "T"
    ].copy()

    # 0.2% annual-chance flood hazard
    moderate_hazard = flood_clean[
        (flood_clean["fld_zone"] == "X") &
        (
            flood_clean["zone_subty"] ==
            "0.2 PCT ANNUAL CHANCE FLOOD HAZARD"
        )
    ].copy()

    return high_hazard, moderate_hazard


def calculate_exposure(streets_projected, high_hazard, moderate_hazard):
    """
    Calculate how much of each street centerline overlaps
    high- and moderate-hazard polygons.
    """

    # 1. Merge polygons within each hazard category
    high_union = high_hazard.geometry.union_all()
    moderate_union = moderate_hazard.geometry.union_all()

    # 2. Avoid counting high-hazard areas twice
    moderate_only = moderate_union.difference(high_union)

    # 3. Prepare street attributes
    roads = streets_projected[
        ["seg_id", "streetlabe", "geometry"]
    ].copy()

    # 4. Calculate each segment's full length
    roads["total_length_m"] = roads.geometry.length

    # 5. Calculate high-hazard intersection lengths
    roads["high_overlap_m"] = (
        roads.geometry.intersection(high_union).length
    )

    # 6. Calculate moderate-hazard intersection lengths
    roads["moderate_overlap_m"] = (
        roads.geometry.intersection(moderate_only).length
    )

    # 7. Calculate combined exposure
    roads["total_overlap_m"] = (
        roads["high_overlap_m"] +
        roads["moderate_overlap_m"]
    )

    return roads, high_union, moderate_only


def classify_exposure(roads):
    """Assign an exposure classification to each segment."""

    roads = roads.copy()

    high = roads["high_overlap_m"] > 0.01
    moderate = roads["moderate_overlap_m"] > 0.01

    roads["exposure_class"] = np.select(
        [
            high & moderate,
            high & ~moderate,
            ~high & moderate
        ],
        [
            "Both",
            "High only",
            "Moderate only"
        ],
        default="No mapped exposure"
    )

    return roads


def explain_exposure(row):
    """Generate an evidence-based exposure explanation."""

    name = row["streetlabe"]
    category = row["exposure_class"]

    high_m = row["high_overlap_m"]
    moderate_m = row["moderate_overlap_m"]
    total_m = row["total_length_m"]

    high_pct = (high_m / total_m * 100) if total_m > 0 else 0
    moderate_pct = (moderate_m / total_m * 100) if total_m > 0 else 0

    if category == "Both":
        return (
            f"{name} intersects both mapped flood-hazard categories. "
            f"Approximately {high_m:.1f} meters ({high_pct:.1f}%) "
            f"overlap a Special Flood Hazard Area, and "
            f"{moderate_m:.1f} meters ({moderate_pct:.1f}%) "
            f"overlap the moderate-hazard area."
        )

    elif category == "High only":
        return (
            f"{name} intersects a mapped Special Flood Hazard Area "
            f"for approximately {high_m:.1f} meters "
            f"({high_pct:.1f}% of the segment)."
        )

    elif category == "Moderate only":
        return (
            f"{name} intersects a mapped 0.2% annual-chance "
            f"flood-hazard area for approximately {moderate_m:.1f} "
            f"meters ({moderate_pct:.1f}% of the segment)."
        )

    else:
        return (
            f"{name} has no measurable centerline overlap with "
            f"the selected high- or moderate-hazard polygons. "
            f"This does not establish that the location is flood-safe."
        )


def export_street_exposure(roads_analysis):
    """
    Export analyzed street segments to GeoJSON
    for use in the FloodLens WebGIS application.
    """

    # Ensure the output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Select fields required by the frontend
    columns = [
        "seg_id",
        "streetlabe",
        "total_length_m",
        "high_overlap_m",
        "moderate_overlap_m",
        "total_overlap_m",
        "exposure_class",
        "explanation",
        "geometry"
    ]

    export_roads = roads_analysis[columns].copy()

    # Convert geometry to longitude and latitude
    export_roads = export_roads.to_crs("EPSG:4326")

    # Write the GeoJSON file
    output_file = OUTPUT_DIR / "roads_exposure.geojson"

    export_roads.to_file(output_file, driver="GeoJSON")

    return output_file


def export_flood_hazards(high_union, moderate_only):
    """Export the hazard geometries used in our analysis."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    hazards = gpd.GeoDataFrame(
        {
            "hazard_category": ["High", "Moderate"],
            "description": [
                "Special Flood Hazard Area",
                "0.2% annual-chance flood-hazard area"
            ],
            "geometry": [high_union, moderate_only]
        },
        crs="EPSG:26918"
    )

    # Convert to latitude/longitude for web mapping
    hazards = hazards.to_crs("EPSG:4326")

    output_file = OUTPUT_DIR / "flood_hazards.geojson"

    hazards.to_file(output_file, driver="GeoJSON")

    return output_file


def export_summary(roads):
    """Generate dashboard statistics from analyzed segments."""

    tolerance = 0.01

    high = roads["high_overlap_m"] > tolerance
    moderate = roads["moderate_overlap_m"] > tolerance

    summary = {
        "project": "FloodLens",
        "study_area": "Philadelphia Schuylkill River corridor",
        "data_year": 2023,

        "total_segments": int(len(roads)),
        "exposed_segments": int((high | moderate).sum()),

        "high_hazard_segments": int(high.sum()),
        "moderate_hazard_segments": int(moderate.sum()),

        "high_only_segments": int((high & ~moderate).sum()),
        "moderate_only_segments": int((~high & moderate).sum()),
        "both_segments": int((high & moderate).sum()),

        "high_overlap_km": round(
            float(roads["high_overlap_m"].sum()) / 1000, 2
        ),
        "moderate_overlap_km": round(
            float(roads["moderate_overlap_m"].sum()) / 1000, 2
        ),
        "total_overlap_km": round(
            float(roads["total_overlap_m"].sum()) / 1000, 2
        ),

        "methodology": "Street centerline and flood-hazard polygon intersection",
        "disclaimer": (
            "Mapped exposure does not predict actual flooding, "
            "road closures, or infrastructure damage."
        )
    }

    output_file = OUTPUT_DIR / "summary.json"

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)

    return output_file


def main():
    print("=== FLOODLENS GIS PIPELINE ===")

    # Step 1: Load original datasets
    flood, streets = load_datasets()

    print("\n=== ORIGINAL DATA ===")
    print("Floodplain features:", len(flood))
    print("Street features:", len(streets))

    # Step 2: Prepare geographic data
    flood_projected, streets_projected = (
        prepare_geographic_data(flood, streets)
    )

    print("\n=== CLIPPED AND PROJECTED DATA ===")
    print("Floodplain features:", len(flood_projected))
    print("Street features:", len(streets_projected))

    print("Flood CRS:", flood_projected.crs)
    print("Street CRS:", streets_projected.crs)

    # Basic validation
    assert flood_projected.crs.to_epsg() == 26918
    assert streets_projected.crs.to_epsg() == 26918

    assert flood_projected.geometry.is_valid.all()
    assert streets_projected.geometry.is_valid.all()

        # Step 3: Select hazard categories
    high_hazard, moderate_hazard = select_hazard_zones(
        flood_projected
    )

    print("\n=== SELECTED FLOOD HAZARDS ===")
    print("High-hazard features:", len(high_hazard))
    print("Moderate-hazard features:", len(moderate_hazard))

    print("\n=== HIGH-HAZARD SUBTYPES ===")
    print(high_hazard["zone_subty"].value_counts(dropna=False))

    # Compare against validated notebook results
    assert len(high_hazard) == 31
    assert len(moderate_hazard) == 54

    assert high_hazard.geometry.is_valid.all()
    assert moderate_hazard.geometry.is_valid.all()

    assert high_hazard.crs == streets_projected.crs
    assert moderate_hazard.crs == streets_projected.crs

        # Step 4: Calculate exposure
    roads_analysis, high_union, moderate_only = (
        calculate_exposure(
            streets_projected,
            high_hazard,
            moderate_hazard
        )
    )

    tolerance = 0.01

    high = roads_analysis["high_overlap_m"] > tolerance
    moderate = roads_analysis["moderate_overlap_m"] > tolerance

    print("\n=== STREET EXPOSURE RESULTS ===")
    print("Total segments:", len(roads_analysis))
    print("High-hazard segments:", high.sum())
    print("Moderate-hazard segments:", moderate.sum())
    print("Unique exposed segments:", (high | moderate).sum())

    print(
        "High-hazard overlap (km):",
        round(roads_analysis["high_overlap_m"].sum() / 1000, 2)
    )

    print(
        "Moderate-hazard overlap (km):",
        round(roads_analysis["moderate_overlap_m"].sum() / 1000, 2)
    )

    print(
        "Combined overlap (km):",
        round(roads_analysis["total_overlap_m"].sum() / 1000, 2)
    )

    # Verify against our Jupyter analysis
    assert len(roads_analysis) == 3097
    assert high.sum() == 127
    assert moderate.sum() == 129
    assert (high | moderate).sum() == 167

    # Validate measurement quality
    assert (roads_analysis["total_overlap_m"] >= 0).all()
    assert (
        roads_analysis["total_overlap_m"]
        <= roads_analysis["total_length_m"] + tolerance
    ).all()

        # Step 5: Classify segments
    roads_analysis = classify_exposure(roads_analysis)

    # Generate human-readable explanations
    roads_analysis["explanation"] = roads_analysis.apply(
        explain_exposure,
        axis=1
    )

    print("\n=== EXPOSURE CLASSIFICATIONS ===")
    print(roads_analysis["exposure_class"].value_counts())

    print("\n=== EXPLANATION VALIDATION ===")
    print("Explanations generated:", len(roads_analysis))

    # Validate results against our notebook
    expected = {
        "No mapped exposure": 2930,
        "Both": 89,
        "Moderate only": 40,
        "High only": 38
    }

    assert (
        roads_analysis["exposure_class"].value_counts().to_dict()
        == expected
    )

    assert roads_analysis["explanation"].notna().all()
    assert roads_analysis["explanation"].str.len().gt(0).all()

    print("\n=== SAMPLE EXPLANATION ===")

    sample = roads_analysis[
        roads_analysis["seg_id"] == 522438
    ].iloc[0]

    print("Street:", sample["streetlabe"])
    print("Classification:", sample["exposure_class"])
    print("Explanation:", sample["explanation"])

        # Step 6: Export street exposure GeoJSON
    output_file = export_street_exposure(roads_analysis)

    print("\n=== STREET GEOJSON EXPORT ===")
    print("Saved to:", output_file)
    print("File exists:", output_file.exists())

    print(
        "File size (MB):",
        round(output_file.stat().st_size / 1024**2, 2)
    )

    # Read the exported data back for validation
    verified = gpd.read_file(output_file)

    assert len(verified) == 3097
    assert verified.crs.to_epsg() == 4326
    assert verified["seg_id"].is_unique
    assert verified["explanation"].notna().all()
    assert verified.geometry.is_valid.all()

    print("Exported features:", len(verified))
    

        # Export flood-hazard polygons
    hazards_file = export_flood_hazards(
        high_union,
        moderate_only
    )

    # Export dashboard statistics
    summary_file = export_summary(roads_analysis)

    print("\n=== ADDITIONAL DATA EXPORTS ===")
    print("Hazard GeoJSON:", hazards_file)
    print("Summary JSON:", summary_file)

    # Verify the generated files
    hazards = gpd.read_file(hazards_file)

    with open(summary_file, encoding="utf-8") as file:
        summary = json.load(file)

    assert len(hazards) == 2
    assert hazards.crs.to_epsg() == 4326
    assert hazards.geometry.is_valid.all()

    assert summary["total_segments"] == 3097
    assert summary["exposed_segments"] == 167
    assert summary["both_segments"] == 89

    print("Hazard features:", len(hazards))
    print("Total segments:", summary["total_segments"])
    print("Exposed segments:", summary["exposed_segments"])
    print("Both categories:", summary["both_segments"])
    print("Combined overlap (km):", summary["total_overlap_km"])

    print("\nStage 3.7.6B passed!")


if __name__ == "__main__":
    main()