"""
Data quality validation tests using Great Expectations patterns.
Run with: pytest tests/test_data_quality.py -v
"""

import pytest
import pandas as pd
import numpy as np


def make_sample_traffic_df():
    """Create a sample traffic DataFrame for testing."""
    return pd.DataFrame({
        "count_point_id": [1, 2, 3, 4, 5],
        "year": [2023, 2023, 2022, 2023, 2021],
        "count_date": pd.to_datetime(["2023-06-15", "2023-07-20", "2022-03-10", "2023-11-01", "2021-09-05"]),
        "latitude": [51.5074, 53.4808, 55.9533, 52.4862, 51.4545],
        "longitude": [-0.1278, -2.2426, -3.1883, -1.8904, -2.5879],
        "cars_and_taxis": [150, 200, 100, 180, 120],
        "all_hgvs": [20, 35, 15, 25, 10],
        "pedal_cycles": [30, 10, 5, 40, 15],
        "total_vehicles": [220, 270, 140, 270, 160],
        "region_name": ["London", "North West", "Scotland", "West Midlands", "South West"],
    })


def make_sample_accident_df():
    """Create a sample accident DataFrame for testing."""
    return pd.DataFrame({
        "collision_id": ["2023010001", "2023010002", "2023010003", "2023010004"],
        "collision_date": pd.to_datetime(["2023-01-15", "2023-02-20", "2023-03-10", "2023-04-01"]),
        "latitude": [51.5, 53.4, 52.9, 55.8],
        "longitude": [-0.1, -2.2, -1.5, -3.1],
        "severity_label": ["Fatal", "Serious", "Slight", "Serious"],
        "number_of_casualties": [1, 3, 1, 2],
        "speed_limit": [30, 60, 30, 40],
        "is_urban": [True, False, True, False],
    })


class TestTrafficDataQualityChecks:

    @pytest.fixture
    def traffic_df(self):
        return make_sample_traffic_df()

    def test_no_null_count_point_ids(self, traffic_df):
        assert traffic_df["count_point_id"].notna().all()

    def test_no_null_coordinates(self, traffic_df):
        assert traffic_df["latitude"].notna().all()
        assert traffic_df["longitude"].notna().all()

    def test_coordinates_within_uk(self, traffic_df):
        assert (traffic_df["latitude"].between(49.0, 61.0)).all()
        assert (traffic_df["longitude"].between(-8.0, 2.0)).all()

    def test_year_in_valid_range(self, traffic_df):
        assert (traffic_df["year"].between(2000, 2025)).all()

    def test_vehicle_counts_non_negative(self, traffic_df):
        for col in ["cars_and_taxis", "all_hgvs", "pedal_cycles", "total_vehicles"]:
            assert (traffic_df[col] >= 0).all(), f"{col} has negative values"

    def test_total_vehicles_gte_components(self, traffic_df):
        component_sum = traffic_df["cars_and_taxis"] + traffic_df["all_hgvs"] + traffic_df["pedal_cycles"]
        assert (traffic_df["total_vehicles"] >= component_sum).all()

    def test_no_duplicate_records(self, traffic_df):
        dupes = traffic_df.duplicated(subset=["count_point_id", "year", "count_date"])
        assert not dupes.any()

    def test_region_names_not_empty(self, traffic_df):
        assert (traffic_df["region_name"].str.strip() != "").all()


class TestAccidentDataQualityChecks:

    @pytest.fixture
    def accident_df(self):
        return make_sample_accident_df()

    def test_no_null_collision_ids(self, accident_df):
        assert accident_df["collision_id"].notna().all()

    def test_unique_collision_ids(self, accident_df):
        assert accident_df["collision_id"].is_unique

    def test_severity_values_valid(self, accident_df):
        valid = {"Fatal", "Serious", "Slight"}
        assert set(accident_df["severity_label"].unique()).issubset(valid)

    def test_casualties_positive(self, accident_df):
        assert (accident_df["number_of_casualties"] > 0).all()

    def test_speed_limits_valid(self, accident_df):
        valid_limits = {20, 30, 40, 50, 60, 70}
        assert set(accident_df["speed_limit"].unique()).issubset(valid_limits)

    def test_coordinates_within_uk(self, accident_df):
        assert (accident_df["latitude"].between(49.0, 61.0)).all()
        assert (accident_df["longitude"].between(-8.0, 2.0)).all()

    def test_dates_not_future(self, accident_df):
        assert (accident_df["collision_date"] <= pd.Timestamp.now()).all()
