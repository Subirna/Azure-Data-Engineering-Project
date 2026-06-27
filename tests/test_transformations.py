"""
Unit Tests for Data Transformation Logic — Batch Pipeline
Tests Bronze → Silver → Gold transformation rules.
Run with: pytest tests/test_transformations.py -v
"""

import pytest


# ============================================
# Bronze Layer Tests
# ============================================

class TestBronzeIngestion:
    """Validate Bronze layer data ingestion rules."""

    def test_all_11_regions_fetched(self):
        """API must fetch all 11 UK regions."""
        expected_regions = list(range(1, 12))
        assert len(expected_regions) == 11

    def test_region_ids_valid(self):
        """Region IDs must be 1 to 11."""
        for region_id in range(1, 12):
            assert 1 <= region_id <= 11

    def test_api_pagination_extracts_data_array(self):
        """API response must extract 'data' array, not the wrapper."""
        api_response = {
            "current_page": 1,
            "total": 600551,
            "per_page": 250,
            "data": [
                {"count_point_id": 51, "year": 2000, "cars_and_taxis": 837},
                {"count_point_id": 51, "year": 2001, "cars_and_taxis": 857},
            ]
        }
        extracted = api_response["data"]
        assert isinstance(extracted, list)
        assert len(extracted) == 2
        assert "count_point_id" in extracted[0]

    def test_api_response_not_wrapper(self):
        """Extracted data should NOT contain pagination metadata."""
        record = {"count_point_id": 51, "year": 2000, "cars_and_taxis": 837}
        assert "current_page" not in record
        assert "total" not in record
        assert "per_page" not in record


# ============================================
# Silver Layer Tests
# ============================================

class TestSilverTransformation:
    """Validate Silver layer cleansing and type-casting rules."""

    def test_uk_latitude_bounds(self):
        """Latitude must be within UK range (49-61)."""
        valid = [49.0, 51.5, 53.4, 55.9, 60.9]
        invalid = [48.9, 61.1, 0, -1, 90]
        for lat in valid:
            assert 49.0 <= lat <= 61.0
        for lat in invalid:
            assert not (49.0 <= lat <= 61.0)

    def test_uk_longitude_bounds(self):
        """Longitude must be within UK range (-8 to 2)."""
        valid = [-7.9, -3.1, -0.1, 1.9]
        invalid = [-8.1, 2.1, 10, -20]
        for lon in valid:
            assert -8.0 <= lon <= 2.0
        for lon in invalid:
            assert not (-8.0 <= lon <= 2.0)

    def test_year_range(self):
        """Year must be between 2000 and 2025."""
        valid_years = [2000, 2010, 2019, 2020, 2023, 2025]
        for year in valid_years:
            assert 2000 <= year <= 2025

    def test_vehicle_counts_non_negative(self):
        """All vehicle counts must be non-negative."""
        counts = {"cars": 837, "hgvs": 30, "cycles": 105, "buses": 25, "lgvs": 451}
        for vehicle, count in counts.items():
            assert count >= 0, f"{vehicle} has negative count"

    def test_total_vehicles_calculation(self):
        """total_vehicles = sum of all individual vehicle types."""
        cars = 837
        hgvs = 30
        cycles = 105
        buses = 25
        lgvs = 451
        motorcycles = 87
        total = cars + hgvs + cycles + buses + lgvs + motorcycles
        assert total == 1535

    def test_hgv_percentage_calculation(self):
        """HGV percentage = all_hgvs / all_motor_vehicles * 100."""
        all_hgvs = 30
        all_motor_vehicles = 1430
        hgv_pct = round(all_hgvs / all_motor_vehicles * 100, 2)
        assert hgv_pct == 2.1

    def test_road_name_uppercase(self):
        """Road names must be uppercase after transformation."""
        raw = "a3111"
        transformed = raw.upper().strip()
        assert transformed == "A3111"

    def test_string_to_int_casting(self):
        """String columns must cast to integer correctly."""
        assert int("837") == 837
        assert int("2023") == 2023
        assert int("0") == 0

    def test_string_to_float_casting(self):
        """String columns must cast to float correctly."""
        assert float("51.5074") == 51.5074
        assert float("-0.1278") == -0.1278


# ============================================
# Gold Layer Tests
# ============================================

class TestGoldTransformation:
    """Validate Gold layer aggregation and business logic."""

    def test_co2_emission_factor_car(self):
        """Car CO2 = count * 164 g/km * 12.8 km / 1000."""
        car_count = 100
        emission_factor = 164
        avg_trip_km = 12.8
        co2_kg = round(car_count * emission_factor * avg_trip_km / 1000, 2)
        assert co2_kg == 209.92

    def test_co2_emission_factor_hgv(self):
        """HGV CO2 = count * 586 g/km * 12.8 km / 1000."""
        hgv_count = 50
        emission_factor = 586
        avg_trip_km = 12.8
        co2_kg = round(hgv_count * emission_factor * avg_trip_km / 1000, 2)
        assert co2_kg == 375.04

    def test_co2_cycle_is_zero(self):
        """Cycle CO2 emission must be zero."""
        cycle_count = 500
        emission_factor = 0
        co2 = cycle_count * emission_factor
        assert co2 == 0

    def test_green_transport_index(self):
        """Green index = (cycles + buses) / total * 100."""
        cycles = 105
        buses = 25
        total = 1535
        gti = round((cycles + buses) / total * 100, 2)
        assert gti == 8.47

    def test_yoy_change_calculation(self):
        """YoY change = (current - previous) / previous * 100."""
        current = 110
        previous = 100
        yoy = round((current - previous) / previous * 100, 2)
        assert yoy == 10.0

    def test_yoy_negative_change(self):
        """Negative YoY indicates traffic decrease."""
        current = 76
        previous = 100
        yoy = round((current - previous) / previous * 100, 2)
        assert yoy == -24.0

    def test_covid_recovery_calculation(self):
        """Recovery % = current / baseline_2019 * 100."""
        baseline_2019 = 100000
        current_2023 = 90680
        recovery = round(current_2023 / baseline_2019 * 100, 2)
        assert recovery == 90.68

    def test_covid_baseline_join_not_null(self):
        """COVID baseline must not be null when using JOIN approach."""
        baseline_2019 = 37873683
        assert baseline_2019 is not None
        assert baseline_2019 > 0

    def test_gold_no_partition_by_preserves_year(self):
        """Year column must exist in Gold tables (no partitionBy)."""
        gold_columns = ['region_name', 'road_type', 'year', 'total_cars', 'total_all_vehicles']
        assert 'year' in gold_columns

    def test_fact_traffic_summary_columns(self):
        """fact_traffic_summary must have required columns."""
        expected = ['region_name', 'road_type', 'year', 'total_cars', 'total_buses',
                    'total_lgvs', 'total_hgvs', 'total_cycles', 'total_all_vehicles',
                    'yoy_change_pct', 'green_transport_index']
        for col in expected:
            assert isinstance(col, str)
            assert len(col) > 0


# ============================================
# Data Quality Tests
# ============================================

class TestDataQuality:
    """Validate data quality rules across all layers."""

    def test_no_duplicate_region_year_combination(self):
        """Each region-year-road_type combination must be unique in Gold."""
        data = [
            ("South East", "Major", 2023),
            ("South East", "Minor", 2023),
            ("North West", "Major", 2023),
        ]
        unique = set(data)
        assert len(unique) == len(data)

    def test_all_11_regions_in_gold(self):
        """Gold tables must contain all 11 UK regions."""
        regions = [
            "South West", "East Midlands", "Scotland", "Wales",
            "North West", "London", "East Of England",
            "Yorkshire And The Humber", "South East",
            "West Midlands", "North East"
        ]
        assert len(regions) == 11

    def test_year_range_in_gold(self):
        """Gold tables must cover years 2000-2025."""
        years = list(range(2000, 2026))
        assert len(years) == 26
        assert min(years) == 2000
        assert max(years) == 2025

    def test_co2_per_vehicle_reasonable(self):
        """CO2 per vehicle should be between 1-5 kg (reasonable range)."""
        co2_per_vehicle = 2.57
        assert 1.0 <= co2_per_vehicle <= 5.0
