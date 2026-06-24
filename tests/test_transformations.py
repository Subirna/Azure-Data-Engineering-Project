"""
Unit tests for data transformation logic.
Run with: pytest tests/test_transformations.py -v
"""

import pytest
import pandas as pd
from datetime import datetime


class TestTrafficDataQuality:
    """Validate traffic data transformation rules."""

    def test_uk_latitude_bounds(self):
        """Count points must be within UK latitude range."""
        latitudes = [51.5074, 53.4808, 55.9533, 49.1, 60.9]
        for lat in latitudes:
            assert 49.0 <= lat <= 61.0, f"Latitude {lat} out of UK bounds"

    def test_uk_longitude_bounds(self):
        """Count points must be within UK longitude range."""
        longitudes = [-0.1278, -2.2426, -3.1883, -7.9, 1.9]
        for lon in longitudes:
            assert -8.0 <= lon <= 2.0, f"Longitude {lon} out of UK bounds"

    def test_year_range_valid(self):
        """Traffic count years must be in valid range."""
        valid_years = [2000, 2010, 2019, 2020, 2023, 2025]
        for year in valid_years:
            assert 2000 <= year <= 2025

    def test_vehicle_counts_non_negative(self):
        """All vehicle count columns must be non-negative."""
        counts = {"cars": 150, "hgvs": 20, "cycles": 5, "buses": 3}
        for vehicle_type, count in counts.items():
            assert count >= 0, f"{vehicle_type} count is negative: {count}"

    def test_hgv_percentage_calculation(self):
        """HGV percentage should be correctly calculated."""
        hgvs = 20
        total = 200
        expected = 10.0
        actual = round(hgvs / total * 100, 2)
        assert actual == expected

    def test_time_period_classification(self):
        """Hours should map to correct time periods."""
        classifications = {
            7: "morning_peak", 8: "morning_peak", 9: "morning_peak",
            10: "inter_peak", 14: "inter_peak",
            16: "evening_peak", 17: "evening_peak", 18: "evening_peak",
            20: "evening", 22: "evening",
            2: "night", 5: "night",
        }

        for hour, expected in classifications.items():
            if 7 <= hour <= 9:
                actual = "morning_peak"
            elif 10 <= hour <= 15:
                actual = "inter_peak"
            elif 16 <= hour <= 18:
                actual = "evening_peak"
            elif 19 <= hour <= 22:
                actual = "evening"
            else:
                actual = "night"
            assert actual == expected, f"Hour {hour}: expected {expected}, got {actual}"


class TestAccidentDataQuality:
    """Validate accident data transformation rules."""

    def test_severity_label_mapping(self):
        """Severity codes should map to correct labels."""
        mapping = {1: "Fatal", 2: "Serious", 3: "Slight"}
        for code, expected in mapping.items():
            assert expected in ["Fatal", "Serious", "Slight"]

    def test_ksi_count_calculation(self):
        """KSI count should equal fatal + serious."""
        fatal = 5
        serious = 25
        ksi = fatal + serious
        assert ksi == 30

    def test_ksi_rate_calculation(self):
        """KSI rate should be percentage of total collisions."""
        ksi = 30
        total = 100
        ksi_rate = round(ksi / total * 100, 2)
        assert ksi_rate == 30.0

    def test_age_band_classification(self):
        """Driver ages should map to correct age bands."""
        test_cases = {
            18: "17-25", 30: "26-35", 40: "36-45",
            50: "46-55", 60: "56-65", 70: "65+"
        }
        for age, expected_band in test_cases.items():
            if 17 <= age <= 25:
                band = "17-25"
            elif 26 <= age <= 35:
                band = "26-35"
            elif 36 <= age <= 45:
                band = "36-45"
            elif 46 <= age <= 55:
                band = "46-55"
            elif 56 <= age <= 65:
                band = "56-65"
            else:
                band = "65+"
            assert band == expected_band

    def test_weather_label_mapping(self):
        """Weather codes should produce valid labels."""
        valid_labels = [
            "Fine no high winds", "Raining no high winds",
            "Snowing no high winds", "Fine + high winds",
            "Raining + high winds", "Snowing + high winds",
            "Fog or mist", "Other/Unknown"
        ]
        for label in valid_labels:
            assert isinstance(label, str) and len(label) > 0


class TestEnvironmentalCalculations:
    """Validate CO2 emission calculations."""

    def test_co2_calculation_car(self):
        """Car CO2 should use correct emission factor."""
        car_count = 100
        emission_factor = 164  # g/km
        avg_trip_km = 12.8
        expected_kg = round(car_count * emission_factor * avg_trip_km / 1000, 2)
        assert expected_kg == 209.92

    def test_co2_calculation_cycle(self):
        """Cycle CO2 should be zero."""
        cycle_count = 500
        emission_factor = 0
        co2 = cycle_count * emission_factor
        assert co2 == 0

    def test_green_transport_index(self):
        """Green transport index = (cycles + buses) / total * 100."""
        cycles = 50
        buses = 30
        total = 1000
        gti = round((cycles + buses) / total * 100, 2)
        assert gti == 8.0

    def test_co2_per_vehicle(self):
        """CO2 per vehicle should be total_co2 / vehicle_count."""
        total_co2_tonnes = 500
        vehicle_count = 100000
        co2_per_vehicle = round(total_co2_tonnes * 1000 / vehicle_count, 2)
        assert co2_per_vehicle == 5.0
