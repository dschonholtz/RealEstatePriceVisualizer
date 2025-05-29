"""
Neighborhood value visualization for discrete property value zones.
Creates distinct color zones showing clear differences between neighborhood value ranges.
Uses actual property boundaries and nearest neighbor interpolation instead of heat maps.
"""

import logging
from pathlib import Path
from typing import Optional, Union, Dict, Any, Tuple

import folium
from folium.plugins import HeatMap
import geopandas as gpd
import pandas as pd
import numpy as np
from scipy.spatial import cKDTree
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from shapely.geometry import box

logger = logging.getLogger(__name__)


class NeighborhoodValueVisualizer:
    """Creates property value visualizations that preserve actual property values without interpolating to zero."""

    def __init__(self):
        """Initialize the neighborhood value visualizer."""
        pass

    def create_parcel_choropleth_map(
        self,
        gdf: gpd.GeoDataFrame,
        value_column: str = "TOTAL_VALUE",
        center: Optional[tuple] = None,
        zoom_start: int = 12,
        max_zoom: int = 18,
    ) -> folium.Map:
        """
        Create a choropleth map using actual parcel boundaries.

        This colors each property polygon based on its quartile,
        preserving exact property boundaries without any interpolation.

        Args:
            gdf: GeoDataFrame with geometries and values
            value_column: Column containing property values
            center: Map center as (lat, lon). If None, uses data centroid
            zoom_start: Initial zoom level
            max_zoom: Maximum zoom level

        Returns:
            Folium Map object with property boundaries colored by value quartiles
        """
        if gdf.empty:
            raise ValueError("Cannot create choropleth from empty GeoDataFrame")

        # Ensure we're in WGS84
        if gdf.crs != "EPSG:4326":
            gdf = gdf.to_crs("EPSG:4326")

        # Filter to valid values
        valid_data = gdf[(gdf[value_column].notna()) & (gdf[value_column] > 0)].copy()

        if valid_data.empty:
            raise ValueError(f"No valid data for choropleth in column {value_column}")

        # Calculate center if not provided
        if center is None:
            bounds = valid_data.total_bounds
            center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]

        # Create base map
        m = folium.Map(
            location=center,
            zoom_start=zoom_start,
            tiles="CartoDB positron",
        )

        # Calculate quartiles
        values = valid_data[value_column]
        q25, q50, q75 = values.quantile([0.25, 0.5, 0.75])

        # Define quartile colors
        def get_quartile_color(val):
            if val <= q25:
                return "#2166ac"  # Deep blue (Q1 - Affordable)
            elif val <= q50:
                return "#4393c3"  # Medium blue (Q2 - Moderate)
            elif val <= q75:
                return "#f4a582"  # Light orange (Q3 - High)
            else:
                return "#b2182b"  # Deep red (Q4 - Expensive)

        # Add each parcel as a polygon
        for idx, row in valid_data.iterrows():
            value = row[value_column]
            color = get_quartile_color(value)

            # Create popup with property info
            popup_text = f"""
            <b>Property Value: ${value:,.0f}</b><br>
            Quartile: {'Q1 (Affordable)' if value <= q25 else 'Q2 (Moderate)' if value <= q50 else 'Q3 (High)' if value <= q75 else 'Q4 (Expensive)'}<br>
            LOC_ID: {row.get('LOC_ID', 'N/A')}
            """

            folium.GeoJson(
                row["geometry"].__geo_interface__,
                style_function=lambda x, color=color: {
                    "fillColor": color,
                    "color": color,
                    "weight": 0.5,
                    "fillOpacity": 0.7,
                    "opacity": 0.8,
                },
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=f"${value:,.0f}",
            ).add_to(m)

        # Add legend
        self._add_choropleth_legend(m, pd.Series(values), q25, q50, q75)

        return m

    def create_quartile_based_heat_map(
        self,
        gdf: gpd.GeoDataFrame,
        value_column: str = "TOTAL_VALUE",
        center: Optional[tuple] = None,
        zoom_start: int = 12,
        radius: int = 30,
        blur: int = 25,
        max_zoom: int = 18,
    ) -> folium.Map:
        """
        Create a heat map with quartile-based intensity mapping.

        Shows neighborhood value patterns at a glance with discrete quartile zones.
        Much lighter file size than choropleth, better for overview visualization.

        Args:
            gdf: GeoDataFrame with geometries and values
            value_column: Column containing values for heat intensity
            center: Map center as (lat, lon). If None, uses data centroid
            zoom_start: Initial zoom level
            radius: Heat map radius for each point
            blur: Heat map blur radius
            max_zoom: Maximum zoom level for heat map

        Returns:
            Folium Map object with quartile-based heat map
        """
        if gdf.empty:
            raise ValueError("Cannot create heat map from empty GeoDataFrame")

        # Ensure we're in WGS84
        if gdf.crs != "EPSG:4326":
            gdf = gdf.to_crs("EPSG:4326")

        # Filter to valid values
        valid_data = gdf[(gdf[value_column].notna()) & (gdf[value_column] > 0)].copy()

        if valid_data.empty:
            raise ValueError(f"No valid data for heat map in column {value_column}")

        # Calculate center if not provided
        if center is None:
            bounds = valid_data.total_bounds
            center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]

        # Create base map with clean styling
        m = folium.Map(location=center, zoom_start=zoom_start, tiles="CartoDB positron")

        # Get centroids and values
        # Convert to projected CRS for accurate centroid calculation
        projected_data = valid_data.to_crs("EPSG:3857")  # Web Mercator
        centroids_proj = projected_data.geometry.centroid
        centroids_wgs84 = centroids_proj.to_crs("EPSG:4326")
        values = valid_data[value_column]

        # QUARTILE-BASED INTENSITY MAPPING
        q25, q50, q75 = values.quantile([0.25, 0.5, 0.75])

        # Assign intensity based on quartiles for clear neighborhood patterns
        def quartile_intensity(val):
            if val <= q25:
                return 0.25  # Q1: Low intensity (affordable neighborhoods)
            elif val <= q50:
                return 0.5  # Q2: Medium-low intensity
            elif val <= q75:
                return 0.75  # Q3: Medium-high intensity
            else:
                return 1.0  # Q4: High intensity (expensive neighborhoods)

        # Create heat map data with quartile-based intensity
        heat_data = []
        for idx in valid_data.index:
            pt = centroids_wgs84.loc[idx]
            lat, lon = pt.y, pt.x
            val = values.loc[idx]
            intensity = quartile_intensity(val)

            if not (pd.isna(lat) or pd.isna(lon) or pd.isna(intensity)):
                heat_data.append([lat, lon, intensity])

        # Add heat map with improved neighborhood-focused gradient
        HeatMap(
            heat_data,
            radius=radius,
            blur=blur,
            max_zoom=max_zoom,
            gradient={
                0.0: "#2c7bb6",  # Deep blue (Q1 - Affordable neighborhoods)
                0.25: "#7fcdbb",  # Teal (Q1-Q2 transition)
                0.5: "#ffffcc",  # Light yellow (Q2-Q3 transition)
                0.75: "#fd8d3c",  # Orange (Q3-Q4 transition)
                1.0: "#d7301f",  # Deep red (Q4 - Expensive neighborhoods)
            },
        ).add_to(m)

        # Add improved legend
        self._add_quartile_heat_map_legend(m, values, q25, q50, q75)

        return m

    def create_multi_tier_heat_map(
        self,
        gdf: gpd.GeoDataFrame,
        value_column: str = "TOTAL_VALUE",
        center: Optional[tuple] = None,
        zoom_start: int = 12,
    ) -> folium.Map:
        """
        Create a multi-tier heat map with different layers for different value ranges.

        Shows distinct neighborhood tiers with layered visualization.
        Great for identifying luxury vs affordable areas at different zoom levels.

        Args:
            gdf: GeoDataFrame with geometries and values
            value_column: Column containing values for heat intensity
            center: Map center as (lat, lon). If None, uses data centroid
            zoom_start: Initial zoom level

        Returns:
            Folium Map object with multi-tier heat map layers
        """
        if gdf.empty:
            raise ValueError("Cannot create heat map from empty GeoDataFrame")

        # Ensure we're in WGS84
        if gdf.crs != "EPSG:4326":
            gdf = gdf.to_crs("EPSG:4326")

        # Filter to valid values
        valid_data = gdf[(gdf[value_column].notna()) & (gdf[value_column] > 0)].copy()

        if valid_data.empty:
            raise ValueError(f"No valid data for heat map in column {value_column}")

        # Calculate center if not provided
        if center is None:
            bounds = valid_data.total_bounds
            center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]

        # Create base map with clean styling
        m = folium.Map(location=center, zoom_start=zoom_start, tiles="CartoDB positron")

        # Get centroids and values
        projected_data = valid_data.to_crs("EPSG:3857")  # Web Mercator
        centroids_proj = projected_data.geometry.centroid
        centroids_wgs84 = centroids_proj.to_crs("EPSG:4326")
        values = valid_data[value_column]

        # Define neighborhood tiers with clearer breakpoints
        q33, q67, q90 = values.quantile([0.33, 0.67, 0.90])

        # APPLY LAYERS IN REVERSE ORDER: Luxury first, then most expensive to cheapest
        # This prevents luxury from dominating the visual since affordable areas will be on top

        # Tier 4: Luxury Neighborhoods (top 10%) - APPLIED FIRST
        tier4_data = valid_data[values > q90]
        if not tier4_data.empty:
            heat_data_4 = []
            for idx in tier4_data.index:
                pt = centroids_wgs84.loc[idx]
                lat, lon = pt.y, pt.x
                if not (pd.isna(lat) or pd.isna(lon)):
                    heat_data_4.append([lat, lon, 1.0])  # Maximum intensity

            HeatMap(
                heat_data_4,
                radius=25,
                blur=20,
                max_zoom=18,
                gradient={0.0: "#de2d26", 1.0: "#a50f15"},  # Red tones
            ).add_to(m)

        # Tier 3: High-Value Neighborhoods (67%-90%)
        tier3_data = valid_data[(values > q67) & (values <= q90)]
        if not tier3_data.empty:
            heat_data_3 = []
            for idx in tier3_data.index:
                pt = centroids_wgs84.loc[idx]
                lat, lon = pt.y, pt.x
                if not (pd.isna(lat) or pd.isna(lon)):
                    heat_data_3.append([lat, lon, 0.8])  # Higher intensity

            HeatMap(
                heat_data_3,
                radius=25,
                blur=20,
                max_zoom=18,
                gradient={0.0: "#feb24c", 1.0: "#fd8d3c"},  # Orange tones
            ).add_to(m)

        # Tier 2: Moderate Neighborhoods (33%-67%)
        tier2_data = valid_data[(values > q33) & (values <= q67)]
        if not tier2_data.empty:
            heat_data_2 = []
            for idx in tier2_data.index:
                pt = centroids_wgs84.loc[idx]
                lat, lon = pt.y, pt.x
                if not (pd.isna(lat) or pd.isna(lon)):
                    heat_data_2.append([lat, lon, 0.7])  # Slightly higher intensity

            HeatMap(
                heat_data_2,
                radius=25,
                blur=20,
                max_zoom=18,
                gradient={0.0: "#41b6c4", 1.0: "#7fcdbb"},  # Teal tones
            ).add_to(m)

        # Tier 1: Affordable Neighborhoods (bottom 33%) - APPLIED LAST (most visible)
        tier1_data = valid_data[values <= q33]
        if not tier1_data.empty:
            heat_data_1 = []
            for idx in tier1_data.index:
                pt = centroids_wgs84.loc[idx]
                lat, lon = pt.y, pt.x
                if not (pd.isna(lat) or pd.isna(lon)):
                    heat_data_1.append([lat, lon, 0.6])  # Consistent intensity

            HeatMap(
                heat_data_1,
                radius=25,
                blur=20,
                max_zoom=18,
                gradient={0.0: "#2166ac", 1.0: "#5395ba"},  # Blue tones
            ).add_to(m)

        # Add improved multi-tier legend
        self._add_multi_tier_legend(m, values, q33, q67, q90)

        return m

    def create_nearest_neighbor_zones_map(
        self,
        gdf: gpd.GeoDataFrame,
        value_column: str = "TOTAL_VALUE",
        center: Optional[tuple] = None,
        zoom_start: int = 12,
        grid_resolution: int = 1000,  # Number of grid points per dimension
        max_zoom: int = 18,
    ) -> folium.Map:
        """
        Create zones using nearest neighbor interpolation.

        This creates a smooth color surface where each point takes the value
        of the nearest property, ensuring no interpolation to zero.

        Args:
            gdf: GeoDataFrame with geometries and values
            value_column: Column containing property values
            center: Map center as (lat, lon). If None, uses data centroid
            zoom_start: Initial zoom level
            grid_resolution: Grid resolution for interpolation
            max_zoom: Maximum zoom level

        Returns:
            Folium Map object with nearest neighbor value zones
        """
        if gdf.empty:
            raise ValueError("Cannot create zones from empty GeoDataFrame")

        # Ensure we're in WGS84
        if gdf.crs != "EPSG:4326":
            gdf = gdf.to_crs("EPSG:4326")

        # Filter to valid values and get centroids
        valid_data = gdf[(gdf[value_column].notna()) & (gdf[value_column] > 0)].copy()

        if valid_data.empty:
            raise ValueError(f"No valid data for zones in column {value_column}")

        # Calculate center if not provided
        if center is None:
            bounds = valid_data.total_bounds
            center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]

        # Create base map
        m = folium.Map(
            location=center,
            zoom_start=zoom_start,
            tiles="CartoDB positron",
        )

        # Get property centroids and values
        # Convert to projected CRS for accurate centroid calculation
        projected_data = valid_data.to_crs("EPSG:3857")  # Web Mercator
        centroids_proj = projected_data.geometry.centroid
        centroids_wgs84 = centroids_proj.to_crs("EPSG:4326")

        # Extract coordinates and values
        coords = np.array([[pt.x, pt.y] for pt in centroids_wgs84])
        values = valid_data[value_column].values

        # Create grid for interpolation
        bounds = valid_data.total_bounds
        lon_min, lat_min, lon_max, lat_max = bounds

        # Add padding to ensure coverage
        lon_padding = (lon_max - lon_min) * 0.1
        lat_padding = (lat_max - lat_min) * 0.1

        lon_grid = np.linspace(
            lon_min - lon_padding, lon_max + lon_padding, grid_resolution
        )
        lat_grid = np.linspace(
            lat_min - lat_padding, lat_max + lat_padding, grid_resolution
        )

        lon_mesh, lat_mesh = np.meshgrid(lon_grid, lat_grid)
        grid_points = np.column_stack([lon_mesh.ravel(), lat_mesh.ravel()])

        # Build KDTree for nearest neighbor lookup
        tree = cKDTree(coords)

        # Find nearest neighbor for each grid point
        _, nearest_indices = tree.query(grid_points)
        grid_values = values[nearest_indices]

        # Calculate quartiles for color mapping
        q25, q50, q75 = np.percentile(values, [25, 50, 75])

        # Create contour-like zones using folium
        # We'll create a series of polygons for each quartile zone
        self._add_nearest_neighbor_overlay(
            m, lon_mesh, lat_mesh, grid_values.reshape(lon_mesh.shape), q25, q50, q75
        )

        # Add legend
        self._add_choropleth_legend(pd.Series(values), q25, q50, q75)

        return m

    def _add_nearest_neighbor_overlay(
        self, map_obj, lon_mesh, lat_mesh, values_mesh, q25, q50, q75
    ):
        """Add nearest neighbor interpolated overlay to map."""
        # Create contour levels for quartiles
        levels = [values_mesh.min(), q25, q50, q75, values_mesh.max()]
        colors = ["#2166ac", "#4393c3", "#f4a582", "#b2182b"]

        # For simplicity, we'll create a heatmap-style overlay but with discrete zones
        # This is a simplified approach - for production, you might want to use matplotlib
        # to generate contour polygons and add them as GeoJson layers

        # Sample approach: create representative points for each quartile
        for i, (lower, upper, color) in enumerate(zip(levels[:-1], levels[1:], colors)):
            mask = (values_mesh >= lower) & (values_mesh < upper)
            if i == len(colors) - 1:  # Include upper bound for last quartile
                mask = (values_mesh >= lower) & (values_mesh <= upper)

            if np.any(mask):
                # Get sample points for this quartile
                lat_points = lat_mesh[mask]
                lon_points = lon_mesh[mask]

                # Sample every nth point to avoid too many markers
                step = max(1, len(lat_points) // 100)
                sample_lats = lat_points[::step]
                sample_lons = lon_points[::step]

                for lat, lon in zip(sample_lats, sample_lons):
                    folium.CircleMarker(
                        location=[lat, lon],
                        radius=8,
                        popup=f"Q{i+1}: ${lower:,.0f} - ${upper:,.0f}",
                        color=color,
                        fillColor=color,
                        fillOpacity=0.6,
                        weight=0,
                    ).add_to(map_obj)

    def _add_choropleth_legend(self, map_obj, values, q25, q50, q75):
        """Add legend to the map."""
        legend_html = f"""
        <div style="position: fixed; 
                    top: 10px; left: 50px; width: 320px; height: 160px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px; border-radius: 5px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h4 style="margin-top:0; color: #333;"><b>Boston Property Values</b></h4>
        <p style="margin: 5px 0; color: #666;"><b>Actual Property Boundaries</b></p>
        <p style="margin: 3px 0; font-size: 12px;">
            <span style="color: #2166ac;">■</span> Q1 (Affordable): ${values.min():,.0f} - ${q25:,.0f}
        </p>
        <p style="margin: 3px 0; font-size: 12px;">
            <span style="color: #4393c3;">■</span> Q2 (Moderate): ${q25:,.0f} - ${q50:,.0f}
        </p>
        <p style="margin: 3px 0; font-size: 12px;">
            <span style="color: #f4a582;">■</span> Q3 (High): ${q50:,.0f} - ${q75:,.0f}
        </p>
        <p style="margin: 3px 0; font-size: 12px;">
            <span style="color: #b2182b;">■</span> Q4 (Expensive): ${q75:,.0f} - ${values.max():,.0f}
        </p>
        <p style="margin: 3px 0; font-size: 11px; color: #888;">
            Properties: {len(values):,} | Median: ${values.median():,.0f}
        </p>
        </div>
        """
        map_obj.get_root().html.add_child(folium.Element(legend_html))

    def _add_quartile_heat_map_legend(self, map_obj, values, q25, q50, q75):
        """Add legend for quartile heat map."""
        legend_html = f"""
        <div style="position: fixed; 
                    top: 10px; left: 50px; width: 320px; height: 160px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px; border-radius: 5px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h4 style="margin-top:0; color: #333;"><b>Boston Neighborhood Values</b></h4>
        <p style="margin: 5px 0; color: #666;"><b>Quartile-Based Heat Map</b></p>
        <p style="margin: 3px 0; font-size: 12px;">
            <span style="color: #2c7bb6;">●</span> Q1 (Affordable): ${values.min():,.0f} - ${q25:,.0f}
        </p>
        <p style="margin: 3px 0; font-size: 12px;">
            <span style="color: #7fcdbb;">●</span> Q2 (Moderate): ${q25:,.0f} - ${q50:,.0f}
        </p>
        <p style="margin: 3px 0; font-size: 12px;">
            <span style="color: #fd8d3c;">●</span> Q3 (High): ${q50:,.0f} - ${q75:,.0f}
        </p>
        <p style="margin: 3px 0; font-size: 12px;">
            <span style="color: #d7301f;">●</span> Q4 (Expensive): ${q75:,.0f} - ${values.max():,.0f}
        </p>
        <p style="margin: 3px 0; font-size: 11px; color: #888;">
            Great for neighborhood overview | Properties: {len(values):,}
        </p>
        </div>
        """
        map_obj.get_root().html.add_child(folium.Element(legend_html))

    def _add_multi_tier_legend(self, map_obj, values, q33, q67, q90):
        """Add legend for multi-tier heat map."""
        legend_html = f"""
        <div style="position: fixed; 
                    top: 10px; left: 50px; width: 320px; height: 180px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px; border-radius: 5px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h4 style="margin-top:0; color: #333;"><b>Boston Neighborhood Tiers</b></h4>
        <p style="margin: 5px 0; color: #666;"><b>Balanced Multi-Tier Heat Map</b></p>
        <p style="margin: 3px 0; font-size: 12px;">
            <span style="color: #2166ac;"><b>●</b></span> <b>Affordable (0-33%): ${values.min():,.0f} - ${q33:,.0f}</b>
        </p>
        <p style="margin: 3px 0; font-size: 12px;">
            <span style="color: #41b6c4;">●</span> Moderate (33-67%): ${q33:,.0f} - ${q67:,.0f}
        </p>
        <p style="margin: 3px 0; font-size: 12px;">
            <span style="color: #feb24c;">●</span> High-Value (67-90%): ${q67:,.0f} - ${q90:,.0f}
        </p>
        <p style="margin: 3px 0; font-size: 12px;">
            <span style="color: #de2d26;">●</span> Luxury (90-100%): ${q90:,.0f} - ${values.max():,.0f}
        </p>
        <p style="margin: 3px 0; font-size: 11px; color: #888;">
            Affordable areas most visible | Layers: Luxury→High→Moderate→Affordable
        </p>
        <p style="margin: 3px 0; font-size: 11px; color: #888;">
            Properties: {len(values):,}
        </p>
        </div>
        """
        map_obj.get_root().html.add_child(folium.Element(legend_html))

    def _add_grid_based_legend(
        self, map_obj, values, q25, q50, q75, grid_count, grid_size_meters
    ):
        """Add legend for grid-based visualization."""
        grid_size_miles = grid_size_meters / 1609  # Convert to miles for display
        legend_html = f"""
        <div style="position: fixed; 
                    top: 10px; left: 50px; width: 320px; height: 180px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px; border-radius: 5px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h4 style="margin-top:0; color: #333;"><b>Boston Grid-Based Property Values</b></h4>
        <p style="margin: 5px 0; color: #666;"><b>Median Values per {grid_size_miles:.1f} Mile Grid Square</b></p>
        <p style="margin: 3px 0; font-size: 12px;">
            <span style="color: #2166ac;">■</span> Q1 (Affordable): ${values.min():,.0f} - ${q25:,.0f}
        </p>
        <p style="margin: 3px 0; font-size: 12px;">
            <span style="color: #4393c3;">■</span> Q2 (Moderate): ${q25:,.0f} - ${q50:,.0f}
        </p>
        <p style="margin: 3px 0; font-size: 12px;">
            <span style="color: #f4a582;">■</span> Q3 (High): ${q50:,.0f} - ${q75:,.0f}
        </p>
        <p style="margin: 3px 0; font-size: 12px;">
            <span style="color: #b2182b;">■</span> Q4 (Expensive): ${q75:,.0f} - ${values.max():,.0f}
        </p>
        <p style="margin: 3px 0; font-size: 11px; color: #888;">
            Grid squares with data: {grid_count} | Total properties: {len(values):,}
        </p>
        <p style="margin: 3px 0; font-size: 11px; color: #888;">
            ✅ No interpolation • Click squares for details • Median values only
        </p>
        </div>
        """
        map_obj.get_root().html.add_child(folium.Element(legend_html))

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
        logger.info(f"Property value map saved to {output_path}")

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

        This avoids heat map interpolation-to-zero by using actual median values
        from properties within each quarter-mile-by-quarter-mile grid square. Uses spatial indexing
        for performance and transparent colors to show the underlying map.

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
