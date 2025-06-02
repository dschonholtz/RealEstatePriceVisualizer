#!/usr/bin/env python3
"""
Generate comprehensive Boston map with property values + MBTA transit + universities.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    print("Loading data and modules...")

    # Import what we need
    from real_estate_visualizer.grid_visualizer import GridBasedVisualizer
    import geopandas as gpd
    import pandas as pd

    # Load property data directly from geodatabase
    print("Loading property data from geodatabase...")

    gdb_path = (
        Path(__file__).parent.parent
        / "data"
        / "MassGIS_L3_Parcels_gdb"
        / "MassGIS_L3_Parcels.gdb"
    )

    if not gdb_path.exists():
        print(f"Error: Geodatabase not found at {gdb_path}")
        sys.exit(1)

    # Load and filter assessment data
    assessment_gdf = gpd.read_file(str(gdb_path), layer="L3_ASSESS")
    assessment_df = pd.DataFrame(assessment_gdf)

    # Filter to Boston metro cities
    metro_cities = [
        "BOSTON",
        "CAMBRIDGE",
        "SOMERVILLE",
        "BROOKLINE",
        "NEWTON",
        "WATERTOWN",
        "WALTHAM",
        "BELMONT",
        "ARLINGTON",
        "LEXINGTON",
        "WINCHESTER",
        "MEDFORD",
        "MALDEN",
        "EVERETT",
        "REVERE",
        "CHELSEA",
        "WINTHROP",
        "QUINCY",
        "MILTON",
        "DEDHAM",
        "NEEDHAM",
    ]

    if "CITY" in assessment_df.columns:
        metro_assessment = assessment_df[
            assessment_df["CITY"].str.upper().isin(metro_cities)
        ].copy()
    else:
        metro_assessment = assessment_df.copy()

    # Load parcels and join
    parcels_gdf = gpd.read_file(str(gdb_path), layer="L3_TAXPAR_POLY")
    combined_gdf = parcels_gdf.merge(metro_assessment, on="LOC_ID", how="inner")

    # Convert to WGS84
    if combined_gdf.crs != "EPSG:4326":
        combined_gdf = combined_gdf.to_crs("EPSG:4326")

    # Filter valid data
    value_col = "TOTAL_VAL"
    valid_mask = (
        combined_gdf.geometry.notna()
        & combined_gdf[value_col].notna()
        & (combined_gdf[value_col] > 0)
    )
    combined_gdf = combined_gdf[valid_mask].copy()
    combined_gdf["TOTAL_VALUE"] = combined_gdf[value_col]

    print(f"Loaded {len(combined_gdf):,} properties")

    # Create visualizer
    print("Creating comprehensive visualization...")
    visualizer = GridBasedVisualizer()

    # Generate map with both transit and universities
    map_obj = visualizer.create_grid_with_university_overlay(
        combined_gdf, include_transit=True
    )

    # Save the map
    output_path = "boston_comprehensive_map.html"
    visualizer.save_map(map_obj, output_path)

    print(f"✅ Comprehensive map generated: {output_path}")
    print("   Includes: Property values + MBTA transit + 30 universities")
    print("   University colors: 🔵 Blue = Private, 🟠 Orange = Public")

    # Update index.html
    print("Updating index.html...")
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Updated index.html with comprehensive visualization")

except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
