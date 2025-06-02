"""
Grid-based property value visualization for discrete property value zones.
Creates quarter-mile-by-quarter-mile grid squares showing median property values using deciles.
No interpolation - shows actual median values only.
"""

import logging
from pathlib import Path
from typing import Optional, Union

import folium
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point, box

logger = logging.getLogger(__name__)


class GridBasedVisualizer:
    """Creates grid-based property value visualizations without interpolation."""

    def __init__(self):
        """Initialize the grid-based visualizer."""
        self.metro_cities = [
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

    def _load_rail_transit_data(self):
        """Load only rail transit data (Heavy Rail, Light Rail, Commuter Rail) - no buses."""
        try:
            logger.info("Loading MBTA rail transit data...")

            # Load stops
            gtfs_path = Path("data/MBTA_GTFS")
            stops_df = pd.read_csv(gtfs_path / "stops.txt")

            # Filter to metro area municipalities
            metro_stops = stops_df[
                stops_df["municipality"].str.upper().isin(self.metro_cities)
            ].copy()

            # Filter to ONLY rail transit (remove buses and ferries)
            # vehicle_type: 0=Light Rail, 1=Heavy Rail, 2=Commuter Rail, 3=Bus, 4=Ferry
            rail_stops = metro_stops[metro_stops["vehicle_type"].isin([0, 1, 2])].copy()

            # Categorize transit types
            rail_stops["transit_type"] = "Rail"
            rail_stops.loc[rail_stops["vehicle_type"] == 0, "transit_type"] = (
                "Green Line"
            )
            rail_stops.loc[rail_stops["vehicle_type"] == 1, "transit_type"] = (
                "Heavy Rail"
            )
            rail_stops.loc[rail_stops["vehicle_type"] == 2, "transit_type"] = (
                "Commuter Rail"
            )

            # Filter out invalid coordinates
            valid_stops = rail_stops.dropna(subset=["stop_lat", "stop_lon"])

            logger.info(f"Loaded {len(valid_stops):,} rail transit stops")
            return valid_stops

        except Exception as e:
            logger.warning(f"Could not load transit data: {e}")
            return None

    def _add_rail_transit_overlay(self, folium_map, stops_df):
        """Add simplified rail transit markers to the map."""
        if stops_df is None or stops_df.empty:
            return folium_map

        logger.info("Adding rail transit markers...")

        # Simple colors for transit types
        colors = {
            "Heavy Rail": "#DA291C",  # Red
            "Green Line": "#00843D",  # Green
            "Commuter Rail": "#80276C",  # Purple
        }

        for _, stop in stops_df.iterrows():
            color = colors.get(stop["transit_type"], "#333333")

            # Minimal circle markers instead of icons
            folium.CircleMarker(
                location=[stop["stop_lat"], stop["stop_lon"]],
                radius=3,  # Small radius
                popup=f"<b>{stop['stop_name']}</b><br>{stop['transit_type']}",
                tooltip=stop["stop_name"],
                color=color,
                fillColor=color,
                fillOpacity=0.8,
                weight=1,
            ).add_to(folium_map)

        # Add simple legend
        self._add_transit_legend(folium_map)

        return folium_map

    def _add_transit_legend(self, folium_map):
        """Add minimal transit legend."""
        legend_html = """
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 160px; height: 90px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:12px; padding: 8px">
        <p style="margin:0 0 5px 0;"><b>MBTA Rail Transit</b></p>
        <p style="margin:2px 0;"><span style="color:#DA291C;">●</span> Heavy Rail (Red/Orange/Blue)</p>
        <p style="margin:2px 0;"><span style="color:#00843D;">●</span> Green Line</p>
        <p style="margin:2px 0;"><span style="color:#80276C;">●</span> Commuter Rail</p>
        </div>
        """
        folium_map.get_root().html.add_child(folium.Element(legend_html))

    def create_grid_based_value_map(
        self,
        gdf: gpd.GeoDataFrame,
        value_column: str = "TOTAL_VALUE",
        grid_size_meters: float = 402.25,  # 0.25 mile = 402.25 meters
        center: Optional[tuple] = None,
        zoom_start: int = 12,
        max_zoom: int = 18,
    ) -> folium.Map:
        """
        Create a grid-based visualization where each square shows median property values.

        This avoids interpolation by using actual median values from properties within
        each quarter-mile-by-quarter-mile grid square. Uses spatial indexing for performance
        and transparent colors to show the underlying map.

        Args:
            gdf: GeoDataFrame with geometries and values
            value_column: Column containing property values
            grid_size_meters: Size of each grid square in meters (default: 0.25 mile)
            center: Map center as (lat, lon). If None, uses data centroid
            zoom_start: Initial zoom level
            max_zoom: Maximum zoom level

        Returns:
            Folium Map object with grid-based median value visualization using deciles
        """
        if gdf.empty:
            raise ValueError("Cannot create grid map from empty GeoDataFrame")

        # Ensure we're in WGS84 first
        if gdf.crs != "EPSG:4326":
            gdf = gdf.to_crs("EPSG:4326")

        # Filter to valid values
        valid_data = gdf[(gdf[value_column].notna()) & (gdf[value_column] > 0)].copy()

        if valid_data.empty:
            raise ValueError(f"No valid data for grid map in column {value_column}")

        # Calculate center if not provided
        if center is None:
            bounds = valid_data.total_bounds
            center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]

        # Create base map with clean styling
        m = folium.Map(
            location=center,
            zoom_start=zoom_start,
            tiles="CartoDB positron",
        )

        # Convert to projected CRS for accurate grid creation (Web Mercator)
        projected_crs = "EPSG:3857"  # Web Mercator
        projected_data = valid_data.to_crs(projected_crs)

        # Get bounds in projected coordinates
        bounds = projected_data.total_bounds
        xmin, ymin, xmax, ymax = bounds

        # Add small padding to ensure coverage
        padding = grid_size_meters * 0.1
        xmin -= padding
        ymin -= padding
        xmax += padding
        ymax += padding

        # Create grid
        logger.info(f"Creating grid with {grid_size_meters}m squares...")

        # Calculate number of grid cells
        x_cells = int(np.ceil((xmax - xmin) / grid_size_meters))
        y_cells = int(np.ceil((ymax - ymin) / grid_size_meters))

        logger.info(
            f"Grid dimensions: {x_cells} x {y_cells} = {x_cells * y_cells} squares"
        )

        # Build spatial index for fast lookups
        logger.info("Building spatial index...")
        spatial_index = projected_data.sindex

        # Calculate global deciles for consistent coloring
        all_values = projected_data[value_column]
        deciles = all_values.quantile([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])
        d10, d20, d30, d40, d50, d60, d70, d80, d90 = deciles

        # Process each grid square
        logger.info("Processing grid squares...")
        grid_squares_with_data = []

        for i in range(x_cells):
            for j in range(y_cells):
                # Calculate grid square bounds
                x_left = xmin + i * grid_size_meters
                x_right = xmin + (i + 1) * grid_size_meters
                y_bottom = ymin + j * grid_size_meters
                y_top = ymin + (j + 1) * grid_size_meters

                # Create grid square geometry
                grid_square = box(x_left, y_bottom, x_right, y_top)

                # Use spatial index to find potential matches
                possible_matches_idx = list(
                    spatial_index.intersection(grid_square.bounds)
                )

                if possible_matches_idx:
                    # Get the actual geometries and check for real intersection
                    possible_matches = projected_data.iloc[possible_matches_idx]
                    intersecting = possible_matches[
                        possible_matches.intersects(grid_square)
                    ]

                    if not intersecting.empty:
                        # Calculate median value for this grid square
                        median_value = intersecting[value_column].median()
                        property_count = len(intersecting)

                        # Convert grid square back to WGS84 for mapping
                        grid_gdf = gpd.GeoDataFrame(
                            [1], geometry=[grid_square], crs=projected_crs
                        )
                        grid_wgs84 = grid_gdf.to_crs("EPSG:4326")

                        grid_squares_with_data.append(
                            {
                                "geometry": grid_wgs84.geometry.iloc[0],
                                "median_value": median_value,
                                "property_count": property_count,
                                "grid_id": f"Grid_{i}_{j}",
                            }
                        )

        logger.info(
            f"Found {len(grid_squares_with_data)} grid squares with property data"
        )

        # Add grid squares to map
        for grid_data in grid_squares_with_data:
            median_val = grid_data["median_value"]
            prop_count = grid_data["property_count"]

            # Determine decile and color
            if median_val <= d10:
                color = "#08306b"  # Very dark blue (D1 - Bottom 10%)
                decile_label = "D1 (Bottom 10%)"
            elif median_val <= d20:
                color = "#08519c"  # Dark blue (D2)
                decile_label = "D2 (10%-20%)"
            elif median_val <= d30:
                color = "#3182bd"  # Medium-dark blue (D3)
                decile_label = "D3 (20%-30%)"
            elif median_val <= d40:
                color = "#6baed6"  # Medium blue (D4)
                decile_label = "D4 (30%-40%)"
            elif median_val <= d50:
                color = "#9ecae1"  # Light blue (D5 - Median)
                decile_label = "D5 (40%-50%)"
            elif median_val <= d60:
                color = "#c6dbef"  # Very light blue (D6)
                decile_label = "D6 (50%-60%)"
            elif median_val <= d70:
                color = "#fcae91"  # Light orange (D7)
                decile_label = "D7 (60%-70%)"
            elif median_val <= d80:
                color = "#fb6a4a"  # Medium orange (D8)
                decile_label = "D8 (70%-80%)"
            elif median_val <= d90:
                color = "#de2d26"  # Dark red (D9)
                decile_label = "D9 (80%-90%)"
            else:
                color = "#a50f15"  # Very dark red (D10 - Top 10%)
                decile_label = "D10 (Top 10%)"

            # Create popup with grid square info
            popup_text = f"""
            <div style="font-family: Arial, sans-serif;">
                <h4 style="margin: 0 0 10px 0; color: #333;">Grid Square Analysis</h4>
                <p style="margin: 3px 0;"><b>Median Value: ${median_val:,.0f}</b></p>
                <p style="margin: 3px 0;"><b>Decile: {decile_label}</b></p>
                <p style="margin: 3px 0;">Properties in grid: {prop_count}</p>
                <p style="margin: 3px 0; font-size: 11px; color: #666;">Grid ID: {grid_data['grid_id']}</p>
                <p style="margin: 3px 0; font-size: 11px; color: #666;">Size: 0.25 mile × 0.25 mile</p>
            </div>
            """

            # Add grid square to map with transparency
            folium.GeoJson(
                grid_data["geometry"].__geo_interface__,
                style_function=lambda x, color=color: {
                    "fillColor": color,
                    "color": color,
                    "weight": 1,
                    "fillOpacity": 0.4,  # Semi-transparent so map shows through
                    "opacity": 0.6,
                },
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=f"Median: ${median_val:,.0f} ({prop_count} properties)",
            ).add_to(m)

        # Add legend for grid-based visualization with deciles
        self._add_grid_based_decile_legend(
            m, all_values, deciles, len(grid_squares_with_data), grid_size_meters
        )

        return m

    def _add_grid_based_decile_legend(
        self, map_obj, values, deciles, grid_count, grid_size_meters
    ):
        """Add legend for decile-based grid visualization."""
        grid_size_miles = grid_size_meters / 1609  # Convert to miles for display
        d10, d20, d30, d40, d50, d60, d70, d80, d90 = deciles

        legend_html = f"""
        <div style="position: fixed; 
                    top: 10px; left: 50px; width: 350px; height: 280px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:13px; padding: 10px; border-radius: 5px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h4 style="margin-top:0; color: #333;"><b>Boston Grid-Based Property Values</b></h4>
        <p style="margin: 5px 0; color: #666;"><b>Median Values per {grid_size_miles:.2f} Mile Grid Square (Deciles)</b></p>
        <p style="margin: 2px 0; font-size: 11px;">
            <span style="color: #08306b;">■</span> D1 (0-10%): ${values.min():,.0f} - ${d10:,.0f}
        </p>
        <p style="margin: 2px 0; font-size: 11px;">
            <span style="color: #08519c;">■</span> D2 (10-20%): ${d10:,.0f} - ${d20:,.0f}
        </p>
        <p style="margin: 2px 0; font-size: 11px;">
            <span style="color: #3182bd;">■</span> D3 (20-30%): ${d20:,.0f} - ${d30:,.0f}
        </p>
        <p style="margin: 2px 0; font-size: 11px;">
            <span style="color: #6baed6;">■</span> D4 (30-40%): ${d30:,.0f} - ${d40:,.0f}
        </p>
        <p style="margin: 2px 0; font-size: 11px;">
            <span style="color: #9ecae1;">■</span> D5 (40-50%): ${d40:,.0f} - ${d50:,.0f}
        </p>
        <p style="margin: 2px 0; font-size: 11px;">
            <span style="color: #c6dbef;">■</span> D6 (50-60%): ${d50:,.0f} - ${d60:,.0f}
        </p>
        <p style="margin: 2px 0; font-size: 11px;">
            <span style="color: #fcae91;">■</span> D7 (60-70%): ${d60:,.0f} - ${d70:,.0f}
        </p>
        <p style="margin: 2px 0; font-size: 11px;">
            <span style="color: #fb6a4a;">■</span> D8 (70-80%): ${d70:,.0f} - ${d80:,.0f}
        </p>
        <p style="margin: 2px 0; font-size: 11px;">
            <span style="color: #de2d26;">■</span> D9 (80-90%): ${d80:,.0f} - ${d90:,.0f}
        </p>
        <p style="margin: 2px 0; font-size: 11px;">
            <span style="color: #a50f15;">■</span> D10 (90-100%): ${d90:,.0f} - ${values.max():,.0f}
        </p>
        <p style="margin: 3px 0; font-size: 10px; color: #888;">
            Grid squares with data: {grid_count} | Total properties: {len(values):,}
        </p>
        <p style="margin: 3px 0; font-size: 10px; color: #888;">
            ✅ No interpolation • Click squares for details • Median values only
        </p>
        </div>
        """
        map_obj.get_root().html.add_child(folium.Element(legend_html))

    def save_map(self, map_obj: folium.Map, output_path: Union[str, Path]):
        """
        Save a Folium map to an HTML file.

        Args:
            map_obj: Folium Map object to save
            output_path: Path where to save the HTML file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        map_obj.save(str(output_path))
        logger.info(f"Grid-based property value map saved to {output_path}")

    def create_grid_with_transit_overlay(
        self,
        gdf: gpd.GeoDataFrame,
        value_column: str = "TOTAL_VALUE",
        grid_size_meters: float = 402.25,  # 0.25 mile = 402.25 meters
        center: Optional[tuple] = None,
        zoom_start: int = 12,
        max_zoom: int = 18,
    ) -> folium.Map:
        """
        Create a combined grid-based property visualization with simplified MBTA rail transit overlay.

        This creates the grid-based property value visualization and overlays
        MBTA rail transit stops (Heavy Rail, Light Rail, Commuter Rail only - no buses).

        Args:
            gdf: GeoDataFrame with geometries and values
            value_column: Column containing property values
            grid_size_meters: Size of each grid square in meters (default: 0.25 mile)
            center: Map center as (lat, lon). If None, uses data centroid
            zoom_start: Initial zoom level
            max_zoom: Maximum zoom level

        Returns:
            Folium Map object with combined property grid and rail transit overlay
        """
        logger.info("Creating combined property grid + rail transit overlay...")

        # First create the base property grid map
        logger.info("Creating property value grid...")
        map_obj = self.create_grid_based_value_map(
            gdf=gdf,
            value_column=value_column,
            grid_size_meters=grid_size_meters,
            center=center,
            zoom_start=zoom_start,
            max_zoom=max_zoom,
        )

        # Load and add rail transit data
        rail_stops = self._load_rail_transit_data()
        if rail_stops is not None and len(rail_stops) > 0:
            map_obj = self._add_rail_transit_overlay(map_obj, rail_stops)
            logger.info(f"Added {len(rail_stops)} rail transit stops to map")
        else:
            logger.info(
                "No rail transit data available - continuing with property grid only"
            )

        return map_obj
