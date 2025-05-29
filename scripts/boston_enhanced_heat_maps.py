#!/usr/bin/env python3
"""
Boston Enhanced Heat Maps Script

This script loads Boston parcel and assessment data from the geodatabase
and creates three types of improved heat maps:
1. Log-normalized heat map
2. Quartile-based heat map
3. Multi-tier heat map

The script addresses the issue where linear normalization makes most properties
appear uniform by using better normalization techniques.
"""

import logging
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from real_estate_visualizer.improved_heat_maps import ImprovedHeatMapVisualizer

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_boston_data():
    """
    Load Boston parcel and assessment data from the geodatabase.

    Returns:
        gpd.GeoDataFrame: Combined parcel and assessment data
    """
    logger.info("Loading Boston parcel and assessment data...")

    # Path to the geodatabase
    gdb_path = Path(__file__).parent.parent / "data" / "M035_parcels_CY22_FY23_sde.gdb"

    if not gdb_path.exists():
        raise FileNotFoundError(f"Geodatabase not found at {gdb_path}")

    try:
        # Load parcel geometries
        logger.info("Loading parcel geometries from M035TaxPar layer...")
        parcels_gdf = gpd.read_file(str(gdb_path), layer="M035TaxPar")
        logger.info(f"Loaded {len(parcels_gdf)} parcels")

        # Load assessment data
        logger.info("Loading assessment data from M035Assess layer...")
        assessment_df = gpd.read_file(str(gdb_path), layer="M035Assess")
        logger.info(f"Loaded {len(assessment_df)} assessment records")

        # Check the columns to understand the data structure
        logger.info(f"Parcel columns: {list(parcels_gdf.columns)}")
        logger.info(f"Assessment columns: {list(assessment_df.columns)}")

        # Find common columns for joining (likely PROP_ID, LOC_ID, or similar)
        parcel_cols = set(parcels_gdf.columns)
        assess_cols = set(assessment_df.columns)
        common_cols = parcel_cols.intersection(assess_cols)
        logger.info(f"Common columns for joining: {common_cols}")

        # Try to join on the most likely key
        join_keys = ["PROP_ID", "LOC_ID", "MAP_PAR_ID", "CAMA_ID"]
        join_key = None

        for key in join_keys:
            if key in common_cols:
                join_key = key
                break

        if join_key is None:
            logger.warning("No obvious join key found. Using first common column.")
            join_key = list(common_cols)[0] if common_cols else None

        if join_key:
            logger.info(f"Joining data on column: {join_key}")
            # Join the data
            combined_gdf = parcels_gdf.merge(assessment_df, on=join_key, how="inner")
            logger.info(
                f"Successfully joined data. Result has {len(combined_gdf)} records"
            )
        else:
            logger.warning("No join key found. Using parcels data only.")
            combined_gdf = parcels_gdf.copy()

        # Ensure we're in WGS84 for web mapping
        if combined_gdf.crs != "EPSG:4326":
            logger.info(f"Converting from {combined_gdf.crs} to EPSG:4326")
            combined_gdf = combined_gdf.to_crs("EPSG:4326")

        # Look for value columns
        value_columns = []
        for col in combined_gdf.columns:
            if any(term in col.upper() for term in ["TOTAL", "VALUE", "VAL", "ASSESS"]):
                if pd.api.types.is_numeric_dtype(combined_gdf[col]):
                    value_columns.append(col)

        logger.info(f"Found potential value columns: {value_columns}")

        # Filter to valid geometries and non-zero values
        if value_columns:
            value_col = value_columns[0]  # Use the first value column found
            logger.info(f"Using value column: {value_col}")

            # Filter to valid data
            valid_mask = (
                combined_gdf.geometry.notna()
                & combined_gdf[value_col].notna()
                & (combined_gdf[value_col] > 0)
            )
            combined_gdf = combined_gdf[valid_mask].copy()
            logger.info(f"After filtering: {len(combined_gdf)} valid records")

            # Add a standardized TOTAL_VALUE column for the heat map class
            combined_gdf["TOTAL_VALUE"] = combined_gdf[value_col]
        else:
            logger.warning("No value columns found. Heat maps may not work properly.")
            combined_gdf["TOTAL_VALUE"] = 1  # Default value

        return combined_gdf

    except Exception as e:
        logger.error(f"Error loading data: {e}")
        raise


def create_output_directory():
    """Create output directory for the heat maps."""
    output_dir = Path(__file__).parent / "boston_enhanced_heat_maps_output"
    output_dir.mkdir(exist_ok=True)
    return output_dir


def main():
    """Main function to generate all improved heat maps."""
    logger.info("Starting Boston Enhanced Heat Maps generation...")

    try:
        # Load the data
        gdf = load_boston_data()

        # Create output directory
        output_dir = create_output_directory()

        # Initialize the visualizer
        visualizer = ImprovedHeatMapVisualizer()

        # Get data summary for logging
        if "TOTAL_VALUE" in gdf.columns:
            values = gdf["TOTAL_VALUE"]
            logger.info(f"Value statistics:")
            logger.info(f"  Count: {len(values):,}")
            logger.info(f"  Min: ${values.min():,.0f}")
            logger.info(f"  Max: ${values.max():,.0f}")
            logger.info(f"  Mean: ${values.mean():,.0f}")
            logger.info(f"  Median: ${values.median():,.0f}")

        # 1. Create log-normalized heat map
        logger.info("Creating log-normalized heat map...")
        log_map = visualizer.create_log_normalized_heat_map(gdf)
        log_output = output_dir / "boston_log_normalized_heat_map.html"
        visualizer.save_map(log_map, log_output)
        logger.info(f"Log-normalized heat map saved to: {log_output}")

        # 2. Create quartile-based heat map
        logger.info("Creating quartile-based heat map...")
        quartile_map = visualizer.create_quartile_based_heat_map(gdf)
        quartile_output = output_dir / "boston_quartile_heat_map.html"
        visualizer.save_map(quartile_map, quartile_output)
        logger.info(f"Quartile-based heat map saved to: {quartile_output}")

        # 3. Create multi-tier heat map
        logger.info("Creating multi-tier heat map...")
        multi_tier_map = visualizer.create_multi_tier_heat_map(gdf)
        multi_tier_output = output_dir / "boston_multi_tier_heat_map.html"
        visualizer.save_map(multi_tier_map, multi_tier_output)
        logger.info(f"Multi-tier heat map saved to: {multi_tier_output}")

        logger.info("All heat maps generated successfully!")
        logger.info(f"Output directory: {output_dir}")

        # Print summary
        print("\n" + "=" * 60)
        print("BOSTON ENHANCED HEAT MAPS - GENERATION COMPLETE")
        print("=" * 60)
        print(f"Data loaded: {len(gdf):,} parcels")
        if "TOTAL_VALUE" in gdf.columns:
            values = gdf["TOTAL_VALUE"]
            print(f"Value range: ${values.min():,.0f} - ${values.max():,.0f}")
        print(f"\nGenerated maps:")
        print(f"  1. Log-normalized: {log_output}")
        print(f"  2. Quartile-based: {quartile_output}")
        print(f"  3. Multi-tier: {multi_tier_output}")
        print("\nOpen these HTML files in your browser to view the interactive maps!")

    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise


if __name__ == "__main__":
    main()
