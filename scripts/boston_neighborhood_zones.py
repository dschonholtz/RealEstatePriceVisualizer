#!/usr/bin/env python3
"""
Greater Boston Metro Property Value Visualization Script

This script loads Greater Boston metro area parcel and assessment data from the MassGIS geodatabase
and creates property value visualizations. Choose which type to generate:

1. Parcel Choropleth: Colors actual property boundaries (most accurate, large file, SLOWER)
2. Quartile Heat Map: Neighborhood overview with quartile zones (lightweight, FAST)
3. Multi-Tier Heat Map: Layered neighborhood tiers (great for luxury vs affordable, FAST)
4. Grid-Based Zones: Quarter-mile-by-quarter-mile grid with median values using deciles (no interpolation, FAST)
5. Grid + Transit Overlay: Property grid PLUS MBTA transit stops and accessibility zones (FAST)

Usage: python boston_neighborhood_zones.py [1|2|3|4|5]
Or run without arguments for interactive selection.
"""

import logging
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from real_estate_visualizer import NeighborhoodValueVisualizer

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_boston_data():
    """
    Load Greater Boston metro area parcel and assessment data from the MassGIS Level 3 Parcels dataset.

    Returns:
        gpd.GeoDataFrame: Combined parcel and assessment data
    """
    logger.info("Loading Greater Boston metro area parcel and assessment data...")

    # Path to the new MassGIS geodatabase
    gdb_path = (
        Path(__file__).parent.parent
        / "data"
        / "MassGIS_L3_Parcels_gdb"
        / "MassGIS_L3_Parcels.gdb"
    )

    if not gdb_path.exists():
        raise FileNotFoundError(f"Geodatabase not found at {gdb_path}")

    try:
        # Load assessment data first to filter by city
        logger.info("Loading assessment data from L3_ASSESS layer...")
        assessment_gdf = gpd.read_file(str(gdb_path), layer="L3_ASSESS")
        assessment_df = pd.DataFrame(assessment_gdf)
        logger.info(f"Loaded {len(assessment_df):,} assessment records")

        # Filter to Greater Boston metro area cities only
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
            logger.info(
                f"Filtered to {len(metro_assessment):,} Greater Boston metro assessment records"
            )
        else:
            logger.warning("No CITY column found, using all data")
            metro_assessment = assessment_df.copy()

        # Load parcel geometries from L3_TAXPAR_POLY layer
        logger.info("Loading parcel geometries from L3_TAXPAR_POLY layer...")
        parcels_gdf = gpd.read_file(str(gdb_path), layer="L3_TAXPAR_POLY")
        logger.info(f"Loaded {len(parcels_gdf):,} parcels")

        # Join the data on LOC_ID (only for the filtered cities)
        logger.info("Joining parcel and assessment data...")
        combined_gdf = parcels_gdf.merge(metro_assessment, on="LOC_ID", how="inner")
        logger.info(
            f"Successfully joined data. Result has {len(combined_gdf):,} records"
        )

        # Ensure we're in WGS84 for web mapping
        if combined_gdf.crs != "EPSG:4326":
            logger.info(f"Converting from {combined_gdf.crs} to EPSG:4326")
            combined_gdf = combined_gdf.to_crs("EPSG:4326")

        # Use TOTAL_VAL as the primary value column
        value_col = "TOTAL_VAL"
        logger.info(f"Using value column: {value_col}")

        # Filter to valid data
        valid_mask = (
            combined_gdf.geometry.notna()
            & combined_gdf[value_col].notna()
            & (combined_gdf[value_col] > 0)
        )
        combined_gdf = combined_gdf[valid_mask].copy()
        logger.info(f"After filtering: {len(combined_gdf)} valid records")

        # Add standardized TOTAL_VALUE column for the visualizer
        combined_gdf["TOTAL_VALUE"] = combined_gdf[value_col]

        return combined_gdf

    except Exception as e:
        logger.error(f"Error loading data: {e}")
        raise


def create_output_directory():
    """Create output directory for the property value maps."""
    output_dir = Path(__file__).parent / "boston_neighborhood_zones_output"
    output_dir.mkdir(exist_ok=True)
    return output_dir


def get_visualization_choice():
    """Get user's choice of which visualization to generate."""

    # Check if command line argument provided
    if len(sys.argv) > 1:
        try:
            choice = int(sys.argv[1])
            if choice in [1, 2, 3, 4, 5]:
                return choice
            else:
                print("Invalid argument. Use 1, 2, 3, 4, or 5.")
                sys.exit(1)
        except ValueError:
            print("Invalid argument. Use 1, 2, 3, 4, or 5.")
            sys.exit(1)

    # Interactive selection
    print("\n" + "=" * 70)
    print("GREATER BOSTON METRO PROPERTY VALUE VISUALIZATION - SELECT TYPE")
    print("=" * 70)
    print("1. 📊 Parcel Choropleth")
    print("   ✅ Most accurate - actual property boundaries")
    print("   ❌ SLOWER generation, larger file")
    print("   🎯 Best for: Detailed property analysis")

    print("\n2. 🎯 Quartile Heat Map")
    print("   ✅ FAST generation (~30 seconds), small file")
    print("   ✅ Perfect metro area overview")
    print("   🎯 Best for: Quick identification of expensive vs affordable areas")

    print("\n3. 🏆 Multi-Tier Heat Map")
    print("   ✅ FAST generation (~30 seconds), small file")
    print("   ✅ Shows distinct metro area tiers (Affordable/Moderate/High/Luxury)")
    print("   🎯 Best for: Luxury vs affordable area analysis")

    print("\n4. 📋 Grid-Based Zones")
    print("   ✅ FAST generation (~30 seconds), small file")
    print("   ✅ Quarter-mile-by-quarter-mile grid with median values using deciles")
    print("   🎯 Best for: Quick overview of median property values")

    print("\n5. 🚇 Grid + Transit Overlay")
    print("   ✅ FAST generation (~45 seconds), medium file")
    print("   ✅ Property grid PLUS MBTA transit stops and accessibility zones")
    print("   🎯 Best for: Understanding transit impact on property values")

    print("\n" + "=" * 70)

    while True:
        try:
            choice = int(input("Enter your choice (1, 2, 3, 4, or 5): "))
            if choice in [1, 2, 3, 4, 5]:
                return choice
            else:
                print("Please enter 1, 2, 3, 4, or 5.")
        except ValueError:
            print("Please enter a valid number (1, 2, 3, 4, or 5).")
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)


def main():
    """Main function to generate selected property value visualization."""
    logger.info(
        "Starting Greater Boston Metro Property Value Visualization generation..."
    )

    try:
        # Get user's visualization choice
        choice = get_visualization_choice()

        # Load the data
        gdf = load_boston_data()

        # Create output directory
        output_dir = create_output_directory()

        # Initialize the visualizer
        visualizer = NeighborhoodValueVisualizer()

        # Get data summary for logging
        values = gdf["TOTAL_VALUE"]
        q25, q50, q75 = values.quantile([0.25, 0.5, 0.75])

        logger.info(f"Value statistics:")
        logger.info(f"  Count: {len(values):,}")
        logger.info(f"  Min: ${values.min():,.0f}")
        logger.info(f"  Q1 (25%): ${q25:,.0f}")
        logger.info(f"  Median (50%): ${q50:,.0f}")
        logger.info(f"  Q3 (75%): ${q75:,.0f}")
        logger.info(f"  Max: ${values.max():,.0f}")

        # Generate selected visualization
        if choice == 1:
            # Parcel Choropleth (SLOW but most accurate)
            print(f"\n🔄 Generating Parcel Choropleth... (This will take 2-3 minutes)")
            logger.info(
                "Creating parcel choropleth map with actual property boundaries..."
            )
            map_obj = visualizer.create_parcel_choropleth_map(gdf)
            output_path = output_dir / "boston_parcel_choropleth.html"
            map_name = "Parcel Choropleth"

        elif choice == 2:
            # Quartile Heat Map (FAST neighborhood overview)
            print(f"\n🔄 Generating Quartile Heat Map... (This will take ~30 seconds)")
            logger.info("Creating quartile-based heat map for neighborhood overview...")
            map_obj = visualizer.create_quartile_based_heat_map(gdf)
            output_path = output_dir / "boston_quartile_heat_map.html"
            map_name = "Quartile Heat Map"

        elif choice == 3:
            # Multi-Tier Heat Map (FAST neighborhood tiers)
            print(
                f"\n🔄 Generating Multi-Tier Heat Map... (This will take ~30 seconds)"
            )
            logger.info("Creating multi-tier heat map with neighborhood layers...")
            map_obj = visualizer.create_multi_tier_heat_map(gdf)
            output_path = output_dir / "boston_multi_tier_heat_map.html"
            map_name = "Multi-Tier Heat Map"

        elif choice == 4:
            # Grid-Based Zones (FAST overview of median values)
            print(f"\n🔄 Generating Grid-Based Zones... (This will take ~30 seconds)")
            logger.info("Creating grid-based zones map with median property values...")
            map_obj = visualizer.create_grid_based_value_map(gdf)
            output_path = output_dir / "boston_grid_based_zones.html"
            map_name = "Grid-Based Zones"

        elif choice == 5:
            # Grid + Transit Overlay (FAST combined property grid + transit overlay)
            print(
                f"\n🔄 Generating Grid + Transit Overlay... (This will take ~45 seconds)"
            )
            logger.info(
                "Creating grid + transit overlay map with property values and transit stops..."
            )
            map_obj = visualizer.create_grid_with_transit_overlay(gdf)
            output_path = output_dir / "boston_grid_plus_transit_overlay.html"
            map_name = "Grid + Transit Overlay"

        # Save the map
        visualizer.save_map(map_obj, output_path)
        logger.info(f"{map_name} generated successfully!")

        # Print success summary
        print("\n" + "=" * 70)
        print(f"✅ {map_name.upper()} - GENERATION COMPLETE")
        print("=" * 70)
        print(f"Data processed: {len(gdf):,} properties")
        print(f"Generated file: {output_path}")
        print(f"File size: {output_path.stat().st_size / (1024*1024):.1f} MB")

        print(f"\nValue Distribution:")
        print(f"  Q1 (Affordable): ${values.min():,.0f} - ${q25:,.0f}")
        print(f"  Q2 (Moderate):   ${q25:,.0f} - ${q50:,.0f}")
        print(f"  Q3 (High):       ${q50:,.0f} - ${q75:,.0f}")
        print(f"  Q4 (Expensive):  ${q75:,.0f} - ${values.max():,.0f}")

        print("\n🌟 NEXT STEPS:")
        print(f"• Open {output_path.name} in your web browser")
        print(f"• Explore Boston's {map_name.lower()} visualization")

        if choice == 1:
            print("• Zoom in to see individual property boundaries")
            print("• Click properties for detailed value information")
        elif choice == 2:
            print("• Great for seeing neighborhood patterns at a glance")
            print("• Note: Heat maps still interpolate to zero when zooming in")
        elif choice == 3:
            print("• Great for seeing neighborhood patterns at a glance")
            print("• Note: Heat maps still interpolate to zero when zooming in")
        elif choice == 4:
            print("• Click grid squares to see median values and property counts")
            print("• Each square represents 0.25 mile × 0.25 mile area")
            print("• ✅ No interpolation to zero - shows actual median values only")
            print("• ✅ Uses decile classification (10 groups) for finer granularity")
        elif choice == 5:
            print("• Click grid squares to see property values and transit stops")
            print("• Each square represents 0.25 mile × 0.25 mile area")
            print("• ✅ No interpolation to zero - shows actual property values only")
            print("• ✅ Uses decile classification (10 groups) for finer granularity")

        print(f"\n💡 To generate a different visualization, run the script again!")

    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise


if __name__ == "__main__":
    main()
