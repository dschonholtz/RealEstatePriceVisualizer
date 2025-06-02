#!/usr/bin/env python3
"""
Test script to verify university data functionality.
"""

import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    from real_estate_visualizer.university_data import BostonUniversityData

    print("Testing university data...")

    # Initialize university data
    uni_data = BostonUniversityData()

    # Get stats
    stats = uni_data.get_university_stats()
    print(f"Total universities: {stats['total_universities']}")
    print(f"Total enrollment: {stats['total_enrollment']:,}")

    # Get top 5 universities
    top_5 = uni_data.get_largest_universities(5)
    print("\nTop 5 Universities:")
    for i, uni in enumerate(top_5, 1):
        print(f"  {i}. {uni['name']} - {uni['enrollment']:,} students")

    print("\nUniversity data test passed!")

except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
