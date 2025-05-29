"""
Improved heat map implementations for better price visualization.
Addresses the issue where linear normalization makes most properties appear uniform.
"""

import logging
from pathlib import Path
from typing import Optional, Union, Dict, Any, Tuple

import folium
from folium.plugins import HeatMap
import geopandas as gpd
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class ImprovedHeatMapVisualizer:
    """Enhanced heat map visualizer with better normalization techniques."""

    def __init__(self):
        """Initialize the improved heat map visualizer."""
        pass

    def create_log_normalized_heat_map(
        self,
        gdf: gpd.GeoDataFrame,
        value_column: str = "TOTAL_VALUE",
        center: Optional[tuple] = None,
        zoom_start: int = 12,
        radius: int = 25,  # Increased from 15
        blur: int = 20,  # Increased from 15
        max_zoom: int = 18,
    ) -> folium.Map:
        """
        Create a heat map with log-based normalization for better distribution.

        Args:
            gdf: GeoDataFrame with geometries and values
            value_column: Column containing values for heat intensity
            center: Map center as (lat, lon). If None, uses data centroid
            zoom_start: Initial zoom level
            radius: Heat map radius for each point (increased for better visibility)
            blur: Heat map blur radius (increased for better blending)
            max_zoom: Maximum zoom level for heat map

        Returns:
            Folium Map object with improved heat map overlay
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

        # Create base map
        m = folium.Map(location=center, zoom_start=zoom_start, tiles="OpenStreetMap")

        # Get centroids and values for heat map
        centroids = valid_data.geometry.centroid
        values = valid_data[value_column]

        # LOG-BASED NORMALIZATION (the key improvement!)
        log_values = np.log10(values)

        # Handle case where all values are the same (avoid division by zero)
        log_range = log_values.max() - log_values.min()
        if log_range == 0:
            # All values are the same, use uniform intensity
            normalized_values = pd.Series(0.5, index=log_values.index)
        else:
            normalized_values = (log_values - log_values.min()) / log_range

        # Create heat map data: [lat, lon, intensity]
        heat_data = []
        for idx in valid_data.index:
            lat = centroids.loc[idx].y
            lon = centroids.loc[idx].x
            intensity = normalized_values.loc[idx]

            # Validate that lat, lon, and intensity are not NaN
            if not (pd.isna(lat) or pd.isna(lon) or pd.isna(intensity)):
                heat_data.append([lat, lon, intensity])

        # Enhanced gradient with better color distribution
        HeatMap(
            heat_data,
            radius=radius,
            blur=blur,
            max_zoom=max_zoom,
            gradient={
                0.0: "#000080",  # Dark blue (low values)
                0.2: "#0040FF",  # Blue
                0.4: "#00BFFF",  # Light blue
                0.6: "#40FF40",  # Green
                0.8: "#FFFF00",  # Yellow
                1.0: "#FF0000",  # Red (high values)
            },
        ).add_to(m)

        # Add improved title and legend
        title_html = f"""
        <h3 align="center" style="font-size:16px"><b>Boston Assessment Value Heat Map</b></h3>
        <h4 align="center" style="font-size:14px"><b>Log-Normalized Intensity</b></h4>
        <p align="center">Values: ${values.min():,.0f} - ${values.max():,.0f}</p>
        <p align="center"><small>🔵 Blue = Lower Values | 🔴 Red = Higher Values</small></p>
        <p align="center"><small>Using log-based normalization for better distribution</small></p>
        """

        m.get_root().html.add_child(folium.Element(title_html))

        return m

    def create_quartile_based_heat_map(
        self,
        gdf: gpd.GeoDataFrame,
        value_column: str = "TOTAL_VALUE",
        center: Optional[tuple] = None,
        zoom_start: int = 12,
        radius: int = 30,  # Even larger for quartile-based
        blur: int = 25,
        max_zoom: int = 18,
    ) -> folium.Map:
        """
        Create a heat map with quartile-based intensity mapping.
        Each quartile gets a specific intensity range for better differentiation.

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

        # Create base map
        m = folium.Map(location=center, zoom_start=zoom_start, tiles="OpenStreetMap")

        # Get centroids and values
        centroids = valid_data.geometry.centroid
        values = valid_data[value_column]

        # QUARTILE-BASED INTENSITY MAPPING
        q25, q50, q75 = values.quantile([0.25, 0.5, 0.75])

        # Assign intensity based on quartiles (much better distribution!)
        def quartile_intensity(val):
            if val <= q25:
                return 0.2  # Q1: Low intensity
            elif val <= q50:
                return 0.4  # Q2: Medium-low intensity
            elif val <= q75:
                return 0.7  # Q3: Medium-high intensity
            else:
                return 1.0  # Q4: High intensity

        # Create heat map data with quartile-based intensity
        heat_data = []
        for idx in valid_data.index:
            lat = centroids.loc[idx].y
            lon = centroids.loc[idx].x
            val = values.loc[idx]
            intensity = quartile_intensity(val)
            if not (pd.isna(lat) or pd.isna(lon) or pd.isna(intensity)):
                heat_data.append([lat, lon, intensity])

        # Add heat map with clear quartile gradient
        HeatMap(
            heat_data,
            radius=radius,
            blur=blur,
            max_zoom=max_zoom,
            gradient={
                0.0: "#000080",  # Dark blue (Q1)
                0.25: "#4080FF",  # Blue (Q1-Q2 transition)
                0.5: "#40FF80",  # Green (Q2-Q3 transition)
                0.75: "#FFFF40",  # Yellow (Q3-Q4 transition)
                1.0: "#FF0000",  # Red (Q4)
            },
        ).add_to(m)

        # Add quartile information to title
        title_html = f"""
        <h3 align="center" style="font-size:16px"><b>Boston Assessment Heat Map</b></h3>
        <h4 align="center" style="font-size:14px"><b>Quartile-Based Intensity</b></h4>
        <p align="center">Q1 (🔵): ${values.min():,.0f} - ${q25:,.0f}</p>
        <p align="center">Q2 (🟢): ${q25:,.0f} - ${q50:,.0f}</p>
        <p align="center">Q3 (🟡): ${q50:,.0f} - ${q75:,.0f}</p>
        <p align="center">Q4 (🔴): ${q75:,.0f} - ${values.max():,.0f}</p>
        <p align="center"><small>Each quartile has distinct intensity for better visualization</small></p>
        """

        m.get_root().html.add_child(folium.Element(title_html))

        return m

    def create_multi_tier_heat_map(
        self,
        gdf: gpd.GeoDataFrame,
        value_column: str = "TOTAL_VALUE",
        center: Optional[tuple] = None,
        zoom_start: int = 12,
    ) -> folium.Map:
        """
        Create a multi-tier heat map with different parameters for different value ranges.
        High-value properties get larger blobs, low-value properties get smaller ones.

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

        # Create base map
        m = folium.Map(location=center, zoom_start=zoom_start, tiles="OpenStreetMap")

        # Get centroids and values
        centroids = valid_data.geometry.centroid
        values = valid_data[value_column]

        # Define value tiers with different visualization parameters
        q33, q67, q90 = values.quantile([0.33, 0.67, 0.90])

        # Tier 1: Low values (bottom 33%) - Same size blobs
        tier1_data = valid_data[values <= q33]
        if not tier1_data.empty:
            heat_data_1 = []
            for idx in tier1_data.index:
                lat = centroids.loc[idx].y
                lon = centroids.loc[idx].x
                heat_data_1.append([lat, lon, 0.3])  # Fixed low intensity

            HeatMap(
                heat_data_1,
                radius=25,
                blur=20,
                max_zoom=18,
                gradient={0.0: "#000080", 1.0: "#0080FF"},  # Blue gradient
            ).add_to(m)

        # Tier 2: Medium values (33%-67%) - Same size blobs
        tier2_data = valid_data[(values > q33) & (values <= q67)]
        if not tier2_data.empty:
            heat_data_2 = []
            for idx in tier2_data.index:
                lat = centroids.loc[idx].y
                lon = centroids.loc[idx].x
                heat_data_2.append([lat, lon, 0.6])  # Fixed medium intensity

            HeatMap(
                heat_data_2,
                radius=25,
                blur=20,
                max_zoom=18,
                gradient={0.0: "#008040", 1.0: "#40FF40"},  # Green gradient
            ).add_to(m)

        # Tier 3: High values (67%-90%) - Same size blobs
        tier3_data = valid_data[(values > q67) & (values <= q90)]
        if not tier3_data.empty:
            heat_data_3 = []
            for idx in tier3_data.index:
                lat = centroids.loc[idx].y
                lon = centroids.loc[idx].x
                heat_data_3.append([lat, lon, 0.8])  # Fixed high intensity

            HeatMap(
                heat_data_3,
                radius=25,
                blur=20,
                max_zoom=18,
                gradient={0.0: "#FF8000", 1.0: "#FFFF00"},  # Orange-Yellow gradient
            ).add_to(m)

        # Tier 4: Ultra-high values (top 10%) - Same size blobs
        tier4_data = valid_data[values > q90]
        if not tier4_data.empty:
            heat_data_4 = []
            for idx in tier4_data.index:
                lat = centroids.loc[idx].y
                lon = centroids.loc[idx].x
                heat_data_4.append([lat, lon, 1.0])  # Maximum intensity

            HeatMap(
                heat_data_4,
                radius=25,
                blur=20,
                max_zoom=18,
                gradient={0.0: "#FF4000", 1.0: "#FF0000"},  # Red gradient
            ).add_to(m)

        # Add comprehensive title
        title_html = f"""
        <h3 align="center" style="font-size:16px"><b>Boston Assessment Multi-Tier Heat Map</b></h3>
        <h4 align="center" style="font-size:14px"><b>Uniform Blob Sizes with Color-Coded Value Ranges</b></h4>
        <p align="center">🔵 Tier 1 (0-33%): ${values.min():,.0f} - ${q33:,.0f}</p>
        <p align="center">🟢 Tier 2 (33-67%): ${q33:,.0f} - ${q67:,.0f}</p>
        <p align="center">🟡 Tier 3 (67-90%): ${q67:,.0f} - ${q90:,.0f}</p>
        <p align="center">🔴 Tier 4 (90-100%): ${q90:,.0f} - ${values.max():,.0f}</p>
        <p align="center"><small>All blobs same size - value differences shown through color and intensity</small></p>
        """

        m.get_root().html.add_child(folium.Element(title_html))

        return m

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
        logger.info(f"Map saved to {output_path}")
