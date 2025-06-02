"""
University data for Boston area with enrollment information and locations.
Contains information for the 30 largest universities by enrollment.
"""

import logging
from typing import Dict, List, Optional, Tuple
import pandas as pd

logger = logging.getLogger(__name__)


class BostonUniversityData:
    """Manages data for Boston area universities including locations and logos."""

    def __init__(self):
        """Initialize with the 30 largest Boston area universities by enrollment."""
        # Based on 2021-2024 enrollment data from various sources
        self.universities = [
            {
                "name": "Boston University",
                "enrollment": 36624,
                "latitude": 42.3505,
                "longitude": -71.1054,
                "city": "Boston",
                "founded": 1839,
                "type": "Private",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/7/7b/Boston_University_logo.svg",
                "website": "https://www.bu.edu",
            },
            {
                "name": "Northeastern University",
                "enrollment": 33676,
                "latitude": 42.3398,
                "longitude": -71.0892,
                "city": "Boston",
                "founded": 1898,
                "type": "Private",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/d/d0/Northeastern_University_Huskies_Logo.svg",
                "website": "https://www.northeastern.edu",
            },
            {
                "name": "Harvard University",
                "enrollment": 31345,
                "latitude": 42.3744,
                "longitude": -71.1169,
                "city": "Cambridge",
                "founded": 1636,
                "type": "Private",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/2/29/Harvard_shield_wreath.svg",
                "website": "https://www.harvard.edu",
            },
            {
                "name": "University of Massachusetts Lowell",
                "enrollment": 17597,
                "latitude": 42.6569,
                "longitude": -71.3281,
                "city": "Lowell",
                "founded": 1894,
                "type": "Public",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/1/1e/University_of_Massachusetts_Lowell_logo.svg",
                "website": "https://www.uml.edu",
            },
            {
                "name": "University of Massachusetts Boston",
                "enrollment": 15810,
                "latitude": 42.3133,
                "longitude": -71.0380,
                "city": "Boston",
                "founded": 1964,
                "type": "Public",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/4/46/University_of_Massachusetts_Boston_logo.svg",
                "website": "https://www.umb.edu",
            },
            {
                "name": "Boston College",
                "enrollment": 15280,
                "latitude": 42.3355,
                "longitude": -71.1685,
                "city": "Newton",
                "founded": 1863,
                "type": "Private",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/9/9e/Boston_College_Eagles_logo.svg",
                "website": "https://www.bc.edu",
            },
            {
                "name": "Tufts University",
                "enrollment": 13274,
                "latitude": 42.4085,
                "longitude": -71.1183,
                "city": "Medford/Somerville",
                "founded": 1852,
                "type": "Private",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/9/96/Tufts_University_wordmark.svg",
                "website": "https://www.tufts.edu",
            },
            {
                "name": "Massachusetts Institute of Technology",
                "enrollment": 11920,
                "latitude": 42.3601,
                "longitude": -71.0942,
                "city": "Cambridge",
                "founded": 1861,
                "type": "Private",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/4/44/MIT_Seal.svg",
                "website": "https://www.mit.edu",
            },
            {
                "name": "Bridgewater State University",
                "enrollment": 9942,
                "latitude": 41.9901,
                "longitude": -70.9742,
                "city": "Bridgewater",
                "founded": 1840,
                "type": "Public",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/a/a8/Bridgewater_State_University_logo.png",
                "website": "https://www.bridgew.edu",
            },
            {
                "name": "Bunker Hill Community College",
                "enrollment": 8545,
                "latitude": 42.3780,
                "longitude": -71.0699,
                "city": "Boston",
                "founded": 1973,
                "type": "Public",
                "logo_url": "https://www.bhcc.edu/bhccstatic/media/images/logo.png",
                "website": "https://www.bhcc.edu",
            },
            {
                "name": "Berklee College of Music",
                "enrollment": 8448,
                "latitude": 42.3467,
                "longitude": -71.0840,
                "city": "Boston",
                "founded": 1945,
                "type": "Private",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/6/69/Berklee_College_of_Music_logo.png",
                "website": "https://www.berklee.edu",
            },
            {
                "name": "Salem State University",
                "enrollment": 7131,
                "latitude": 42.5141,
                "longitude": -70.8967,
                "city": "Salem",
                "founded": 1854,
                "type": "Public",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/e/e5/Salem_State_University_logo.png",
                "website": "https://www.salemstate.edu",
            },
            {
                "name": "Massachusetts College of Pharmacy and Health Sciences",
                "enrollment": 6321,
                "latitude": 42.3407,
                "longitude": -71.0873,
                "city": "Boston",
                "founded": 1823,
                "type": "Private",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/f/f3/MCPHS_University_logo.png",
                "website": "https://www.mcphs.edu",
            },
            {
                "name": "Suffolk University",
                "enrollment": 6697,
                "latitude": 42.3589,
                "longitude": -71.0622,
                "city": "Boston",
                "founded": 1906,
                "type": "Private",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/8/8b/Suffolk_University_logo.png",
                "website": "https://www.suffolk.edu",
            },
            {
                "name": "Simmons University",
                "enrollment": 5984,
                "latitude": 42.3428,
                "longitude": -71.1002,
                "city": "Boston",
                "founded": 1899,
                "type": "Private",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/7/72/Simmons_University_logo.png",
                "website": "https://www.simmons.edu",
            },
            {
                "name": "Emerson College",
                "enrollment": 5670,
                "latitude": 42.3522,
                "longitude": -71.0679,
                "city": "Boston",
                "founded": 1880,
                "type": "Private",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/c/c9/Emerson_College_logo.png",
                "website": "https://www.emerson.edu",
            },
            {
                "name": "Merrimack College",
                "enrollment": 5452,
                "latitude": 42.7684,
                "longitude": -71.2767,
                "city": "North Andover",
                "founded": 1947,
                "type": "Private",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/7/7b/Merrimack_College_logo.png",
                "website": "https://www.merrimack.edu",
            },
            {
                "name": "Brandeis University",
                "enrollment": 5302,
                "latitude": 42.3664,
                "longitude": -71.2595,
                "city": "Waltham",
                "founded": 1948,
                "type": "Private",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/5/5d/Brandeis_University_logo.svg",
                "website": "https://www.brandeis.edu",
            },
            {
                "name": "Bentley University",
                "enrollment": 5264,
                "latitude": 42.3885,
                "longitude": -71.2304,
                "city": "Waltham",
                "founded": 1917,
                "type": "Private",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/b/b6/Bentley_University_logo.png",
                "website": "https://www.bentley.edu",
            },
            {
                "name": "Framingham State University",
                "enrollment": 4495,
                "latitude": 42.3014,
                "longitude": -71.4370,
                "city": "Framingham",
                "founded": 1839,
                "type": "Public",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/e/e7/Framingham_State_University_logo.png",
                "website": "https://www.framingham.edu",
            },
            {
                "name": "Wentworth Institute of Technology",
                "enrollment": 4018,
                "latitude": 42.3370,
                "longitude": -71.0955,
                "city": "Boston",
                "founded": 1904,
                "type": "Private",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/5/50/Wentworth_Institute_of_Technology_logo.png",
                "website": "https://www.wit.edu",
            },
            {
                "name": "Endicott College",
                "enrollment": 3982,
                "latitude": 42.5762,
                "longitude": -70.8265,
                "city": "Beverly",
                "founded": 1939,
                "type": "Private",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/3/3b/Endicott_College_logo.png",
                "website": "https://www.endicott.edu",
            },
            {
                "name": "Babson College",
                "enrollment": 3684,
                "latitude": 42.2963,
                "longitude": -71.2643,
                "city": "Wellesley",
                "founded": 1919,
                "type": "Private",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/b/b4/Babson_College_logo.png",
                "website": "https://www.babson.edu",
            },
            {
                "name": "Regis College",
                "enrollment": 3599,
                "latitude": 42.2877,
                "longitude": -71.2632,
                "city": "Weston",
                "founded": 1927,
                "type": "Private",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/6/67/Regis_College_logo.png",
                "website": "https://www.regiscollege.edu",
            },
            {
                "name": "Lesley University",
                "enrollment": 3134,
                "latitude": 42.3875,
                "longitude": -71.1304,
                "city": "Cambridge",
                "founded": 1909,
                "type": "Private",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/2/20/Lesley_University_logo.png",
                "website": "https://www.lesley.edu",
            },
            {
                "name": "Quincy College",
                "enrollment": 2603,
                "latitude": 42.2501,
                "longitude": -71.0022,
                "city": "Quincy",
                "founded": 1958,
                "type": "Public",
                "logo_url": "https://www.quincycollege.edu/images/qc-logo.png",
                "website": "https://www.quincycollege.edu",
            },
            {
                "name": "Stonehill College",
                "enrollment": 2479,
                "latitude": 42.1067,
                "longitude": -71.0578,
                "city": "Easton",
                "founded": 1948,
                "type": "Private",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/8/8a/Stonehill_College_logo.png",
                "website": "https://www.stonehill.edu",
            },
            {
                "name": "Wellesley College",
                "enrollment": 2461,
                "latitude": 42.2947,
                "longitude": -71.3055,
                "city": "Wellesley",
                "founded": 1870,
                "type": "Private",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/4/4f/Wellesley_College_logo.png",
                "website": "https://www.wellesley.edu",
            },
            {
                "name": "Cambridge College",
                "enrollment": 2451,
                "latitude": 42.3731,
                "longitude": -71.1097,
                "city": "Cambridge",
                "founded": 1971,
                "type": "Private",
                "logo_url": "https://www.cambridgecollege.edu/images/cc-logo.png",
                "website": "https://www.cambridgecollege.edu",
            },
            {
                "name": "Curry College",
                "enrollment": 2242,
                "latitude": 42.2764,
                "longitude": -71.0631,
                "city": "Milton",
                "founded": 1879,
                "type": "Private",
                "logo_url": "https://upload.wikimedia.org/wikipedia/en/7/71/Curry_College_logo.png",
                "website": "https://www.curry.edu",
            },
        ]

    def get_universities_dataframe(self) -> pd.DataFrame:
        """Get universities data as a pandas DataFrame."""
        return pd.DataFrame(self.universities)

    def get_university_by_name(self, name: str) -> Optional[Dict]:
        """Get a specific university by name."""
        for uni in self.universities:
            if uni["name"].lower() == name.lower():
                return uni
        return None

    def get_universities_by_city(self, city: str) -> List[Dict]:
        """Get all universities in a specific city."""
        return [uni for uni in self.universities if uni["city"].lower() == city.lower()]

    def get_largest_universities(self, count: int = 10) -> List[Dict]:
        """Get the largest universities by enrollment."""
        return sorted(self.universities, key=lambda x: x["enrollment"], reverse=True)[
            :count
        ]

    def get_universities_in_bounds(
        self, min_lat: float, max_lat: float, min_lon: float, max_lon: float
    ) -> List[Dict]:
        """Get universities within specified geographic bounds."""
        return [
            uni
            for uni in self.universities
            if min_lat <= uni["latitude"] <= max_lat
            and min_lon <= uni["longitude"] <= max_lon
        ]

    def get_total_enrollment(self) -> int:
        """Get total enrollment across all universities."""
        return sum(uni["enrollment"] for uni in self.universities)

    def get_university_stats(self) -> Dict:
        """Get summary statistics about the universities."""
        enrollments = [uni["enrollment"] for uni in self.universities]
        public_count = len(
            [uni for uni in self.universities if uni["type"] == "Public"]
        )
        private_count = len(
            [uni for uni in self.universities if uni["type"] == "Private"]
        )

        return {
            "total_universities": len(self.universities),
            "total_enrollment": sum(enrollments),
            "average_enrollment": sum(enrollments) / len(enrollments),
            "largest_enrollment": max(enrollments),
            "smallest_enrollment": min(enrollments),
            "public_universities": public_count,
            "private_universities": private_count,
            "oldest_founded": min(uni["founded"] for uni in self.universities),
            "newest_founded": max(uni["founded"] for uni in self.universities),
        }
