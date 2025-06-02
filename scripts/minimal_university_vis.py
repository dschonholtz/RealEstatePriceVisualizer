#!/usr/bin/env python3
"""
Minimal university visualization script.
"""

import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    print("Loading modules...")

    from real_estate_visualizer.data_loader import PropertyDataLoader
    from real_estate_visualizer.grid_visualizer import GridBasedVisualizer

    print("Loading property data...")
    loader = PropertyDataLoader()
    gdf = loader.load_merged_data()

    if gdf is None or gdf.empty:
        print("Failed to load property data")
        sys.exit(1)

    print(f"Loaded {len(gdf):,} property records")

    print("Creating visualizer...")
    visualizer = GridBasedVisualizer()

    print("Creating university overlay map...")
    map_obj = visualizer.create_grid_with_university_overlay(
        gdf=gdf, value_column="TOTAL_VALUE", zoom_start=11, include_transit=False
    )

    print("Saving map...")
    output_path = "boston_universities_map.html"
    visualizer.save_map(map_obj, output_path)

    print(f"Successfully created university map: {output_path}")

    # Update index.html
    print("Updating index.html...")
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(content)

    print("Done! University visualization created successfully.")

except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
