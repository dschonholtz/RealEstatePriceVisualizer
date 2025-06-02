#!/usr/bin/env python3
"""Simple test to verify university visualization works."""

import sys
import os
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_university_data():
    """Test if university data loads correctly."""
    try:
        from real_estate_visualizer.university_data import BostonUniversityData

        uni_data = BostonUniversityData()
        stats = uni_data.get_university_stats()

        print(f"✅ University data loaded successfully")
        print(f"   Universities: {stats['total_universities']}")
        print(f"   Total enrollment: {stats['total_enrollment']:,}")

        return True
    except Exception as e:
        print(f"❌ University data failed: {e}")
        return False


def create_simple_map():
    """Create a simple map with just universities (no property data)."""
    try:
        import folium
        from real_estate_visualizer.university_data import BostonUniversityData

        # Create simple map centered on Boston
        m = folium.Map(location=[42.3601, -71.0589], zoom_start=11)

        # Add universities
        uni_data = BostonUniversityData()
        for uni in uni_data.get_largest_universities(10):
            folium.Marker(
                location=[uni["latitude"], uni["longitude"]],
                popup=f"{uni['name']} - {uni['enrollment']:,} students",
                tooltip=uni["name"],
            ).add_to(m)

        # Save map
        m.save("simple_university_map.html")
        print("✅ Simple university map created: simple_university_map.html")

        return True
    except Exception as e:
        print(f"❌ Simple map creation failed: {e}")
        return False


if __name__ == "__main__":
    print("Testing university functionality...")

    # Test 1: University data
    test1 = test_university_data()

    # Test 2: Simple map creation
    test2 = create_simple_map()

    if test1 and test2:
        print("\n🎉 All tests passed! University functionality is working.")
    else:
        print("\n❌ Some tests failed.")

    sys.exit(0 if (test1 and test2) else 1)
