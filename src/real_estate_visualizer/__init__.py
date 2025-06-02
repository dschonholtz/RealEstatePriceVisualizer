"""Real Estate Visualizer package for property value mapping and analysis."""

from .grid_visualizer import GridBasedVisualizer

# Export with both names for backward compatibility
NeighborhoodValueVisualizer = GridBasedVisualizer


def main() -> None:
    print("Hello from real-estate-visualizer!")


__all__ = ["GridBasedVisualizer", "NeighborhoodValueVisualizer"]
