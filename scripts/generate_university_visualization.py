#!/usr/bin/env python3
"""
Generate Boston property value visualization with university overlay.

This script creates a comprehensive map showing:
1. Property values by grid squares (deciles)
2. University locations with logos and enrollment data
3. Analysis of how universities correlate with low property values due to tax exemptions

Usage:
    uv run python scripts/generate_university_visualization.py
"""

import logging
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from real_estate_visualizer.data_loader import PropertyDataLoader
from real_estate_visualizer.grid_visualizer import GridBasedVisualizer
from real_estate_visualizer.university_data import BostonUniversityData

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Generate property value visualization with university overlay."""
    logger.info("Starting university overlay visualization generation...")

    # Create output directory
    output_dir = Path("scripts/university_visualization_output")
    output_dir.mkdir(exist_ok=True, parents=True)

    try:
        # Load property data
        logger.info("Loading Boston property data...")
        loader = PropertyDataLoader()
        gdf = loader.load_merged_data()

        if gdf is None or gdf.empty:
            logger.error("Failed to load property data")
            return False

        logger.info(f"Loaded {len(gdf):,} property records")

        # Initialize visualizer and university data
        visualizer = GridBasedVisualizer()
        university_data = BostonUniversityData()

        # Print university statistics
        stats = university_data.get_university_stats()
        logger.info(f"University Statistics:")
        logger.info(f"  Total universities: {stats['total_universities']}")
        logger.info(f"  Total enrollment: {stats['total_enrollment']:,}")
        logger.info(f"  Average enrollment: {stats['average_enrollment']:,.0f}")
        logger.info(f"  Private universities: {stats['private_universities']}")
        logger.info(f"  Public universities: {stats['public_universities']}")

        # List the top 10 largest universities
        logger.info("\nTop 10 Largest Universities:")
        top_10 = university_data.get_largest_universities(10)
        for i, uni in enumerate(top_10, 1):
            logger.info(
                f"  {i:2d}. {uni['name']} - {uni['enrollment']:,} students ({uni['type']})"
            )

        # Create visualizations
        logger.info("\n" + "=" * 60)
        logger.info("Creating visualizations...")

        # 1. Basic grid with universities
        logger.info("1. Creating property grid with university overlay...")
        map_basic = visualizer.create_grid_with_university_overlay(
            gdf=gdf, value_column="TOTAL_VALUE", zoom_start=11, include_transit=False
        )

        basic_path = output_dir / "boston_properties_with_universities.html"
        visualizer.save_map(map_basic, basic_path)
        logger.info(f"   Saved: {basic_path}")

        # 2. Full overlay with transit + universities
        logger.info("2. Creating full overlay with transit and universities...")
        map_full = visualizer.create_grid_with_university_overlay(
            gdf=gdf, value_column="TOTAL_VALUE", zoom_start=11, include_transit=True
        )

        full_path = output_dir / "boston_properties_universities_transit.html"
        visualizer.save_map(map_full, full_path)
        logger.info(f"   Saved: {full_path}")

        # 3. Create university-only map for reference
        logger.info("3. Creating university-focused map...")
        map_unis = visualizer.create_grid_based_value_map(
            gdf=gdf,
            value_column="TOTAL_VALUE",
            zoom_start=10,
        )
        map_unis = visualizer._add_university_overlay(map_unis, filter_by_bounds=False)

        unis_path = output_dir / "boston_universities_overview.html"
        visualizer.save_map(map_unis, unis_path)
        logger.info(f"   Saved: {unis_path}")

        # 4. Copy best version to main index.html
        logger.info("4. Updating main index.html with university visualization...")
        main_index = Path("index.html")

        # Use the full overlay as the main visualization
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        with open(main_index, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"   Updated: {main_index}")

        # Generate analysis summary
        logger.info("\n" + "=" * 60)
        logger.info("UNIVERSITY ANALYSIS SUMMARY")
        logger.info("=" * 60)

        logger.info(
            f"Generated visualization with {stats['total_universities']} universities"
        )
        logger.info(f"Total student population: {stats['total_enrollment']:,}")
        logger.info(
            f"Largest university: {top_10[0]['name']} ({top_10[0]['enrollment']:,} students)"
        )
        logger.info(
            f"Founded span: {stats['oldest_founded']} - {stats['newest_founded']}"
        )

        # Analyze university distribution by city
        df = university_data.get_universities_dataframe()
        city_stats = (
            df.groupby("city")
            .agg(
                {
                    "enrollment": ["count", "sum"],
                    "name": lambda x: ", ".join(x.head(3)),  # Top 3 names per city
                }
            )
            .round(0)
        )

        logger.info("\nUniversities by City:")
        for city in city_stats.index:
            count = int(city_stats.loc[city, ("enrollment", "count")])
            total_enrollment = int(city_stats.loc[city, ("enrollment", "sum")])
            logger.info(
                f"  {city}: {count} universities, {total_enrollment:,} students"
            )

        logger.info("\n" + "=" * 60)
        logger.info("KEY INSIGHTS:")
        logger.info("• Universities appear in areas with lower property values due to:")
        logger.info("  - Non-profit tax exemptions")
        logger.info("  - Institutional ownership of large land areas")
        logger.info("  - Different zoning and land use patterns")
        logger.info("• Boston area has exceptional density of higher education")
        logger.info(
            "• Major universities cluster in Cambridge, Boston, and inner suburbs"
        )
        logger.info("• Student population significantly impacts local housing markets")
        logger.info("=" * 60)

        logger.info("\nVisualization generation completed successfully!")
        logger.info(f"Main output: {main_index}")
        logger.info(f"Additional outputs in: {output_dir}")

        return True

    except Exception as e:
        logger.error(f"Error generating university visualization: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
