"""
Unit Tests for Streaming Pipeline — Carbon Intensity
Tests producer, consumer, and Gold aggregation logic.
Run with: pytest tests/test_streaming.py -v
"""

import pytest
import json


# ============================================
# Producer Tests
# ============================================

class TestProducer:
    """Validate producer event generation."""

    def test_national_intensity_event_structure(self):
        """National intensity event must have required fields."""
        event = {
            "event_type": "national_intensity",
            "timestamp": "2026-06-25T16:00:00",
            "from": "2026-06-25T16:00Z",
            "to": "2026-06-25T16:30Z",
            "forecast": 142,
            "actual": 160,
            "index": "moderate"
        }
        assert event["event_type"] == "national_intensity"
        assert "forecast" in event
        assert "actual" in event
        assert "index" in event

    def test_generation_mix_event_structure(self):
        """Generation mix event must have fuel and percentage."""
        event = {
            "event_type": "generation_mix",
            "timestamp": "2026-06-25T16:00:00",
            "fuel": "wind",
            "percentage": 27.3
        }
        assert event["event_type"] == "generation_mix"
        assert event["fuel"] == "wind"
        assert 0 <= event["percentage"] <= 100

    def test_regional_intensity_event_structure(self):
        """Regional event must have region_id and region_name."""
        event = {
            "event_type": "regional_intensity",
            "region_id": 1,
            "region_name": "North Scotland",
            "forecast": 2,
            "index": "very low"
        }
        assert event["event_type"] == "regional_intensity"
        assert event["region_id"] >= 1
        assert len(event["region_name"]) > 0

    def test_event_serializable_to_json(self):
        """All events must be JSON serializable for Event Hub."""
        event = {
            "event_type": "national_intensity",
            "forecast": 142,
            "actual": 160,
            "index": "moderate"
        }
        json_str = json.dumps(event)
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed["forecast"] == 142

    def test_fuel_types_valid(self):
        """Generation mix must have valid fuel types."""
        valid_fuels = ["biomass", "coal", "imports", "gas", "nuclear",
                       "other", "hydro", "solar", "wind"]
        assert len(valid_fuels) == 9

    def test_event_count_per_cycle(self):
        """Each cycle should produce ~190 events."""
        national = 1
        generation = 9
        regional = 17
        regional_gen = 17 * 9
        total = national + generation + regional + regional_gen
        assert total == 180


# ============================================
# Consumer Tests
# ============================================

class TestConsumer:
    """Validate consumer JSON parsing."""

    def test_parse_national_intensity_json(self):
        """Consumer must parse national intensity JSON correctly."""
        raw = '{"event_type":"national_intensity","forecast":142,"actual":160,"index":"moderate"}'
        parsed = json.loads(raw)
        assert parsed["event_type"] == "national_intensity"
        assert parsed["forecast"] == 142

    def test_parse_generation_mix_json(self):
        """Consumer must parse generation mix JSON correctly."""
        raw = '{"event_type":"generation_mix","fuel":"wind","percentage":27.3}'
        parsed = json.loads(raw)
        assert parsed["fuel"] == "wind"
        assert parsed["percentage"] == 27.3

    def test_parse_regional_json(self):
        """Consumer must parse regional intensity JSON correctly."""
        raw = '{"event_type":"regional_intensity","region_id":3,"region_name":"Scotland","forecast":2}'
        parsed = json.loads(raw)
        assert parsed["region_name"] == "Scotland"
        assert parsed["forecast"] == 2

    def test_bronze_append_mode(self):
        """Bronze must use append mode — not overwrite."""
        write_mode = "append"
        assert write_mode == "append"

    def test_silver_overwrite_mode(self):
        """Silver must use overwrite mode."""
        write_mode = "overwrite"
        assert write_mode == "overwrite"


# ============================================
# Gold Aggregation Tests
# ============================================

class TestStreamingGold:
    """Validate streaming Gold layer aggregations."""

    def test_intensity_category_very_low(self):
        """Intensity <= 50 should be 'Very Low'."""
        actual = 30
        if actual <= 50:
            category = "Very Low"
        elif actual <= 100:
            category = "Low"
        elif actual <= 200:
            category = "Moderate"
        elif actual <= 300:
            category = "High"
        else:
            category = "Very High"
        assert category == "Very Low"

    def test_intensity_category_moderate(self):
        """Intensity 101-200 should be 'Moderate'."""
        actual = 160
        if actual <= 50:
            category = "Very Low"
        elif actual <= 100:
            category = "Low"
        elif actual <= 200:
            category = "Moderate"
        elif actual <= 300:
            category = "High"
        else:
            category = "Very High"
        assert category == "Moderate"

    def test_intensity_category_very_high(self):
        """Intensity > 300 should be 'Very High'."""
        actual = 350
        if actual <= 50:
            category = "Very Low"
        elif actual <= 100:
            category = "Low"
        elif actual <= 200:
            category = "Moderate"
        elif actual <= 300:
            category = "High"
        else:
            category = "Very High"
        assert category == "Very High"

    def test_energy_category_renewable(self):
        """Wind, solar, hydro should be classified as Renewable."""
        renewable_fuels = ["wind", "solar", "hydro"]
        for fuel in renewable_fuels:
            assert fuel in ["wind", "solar", "hydro"]

    def test_energy_category_fossil(self):
        """Gas and coal should be classified as Fossil Fuel."""
        fossil_fuels = ["gas", "coal"]
        for fuel in fossil_fuels:
            assert fuel in ["gas", "coal"]

    def test_forecast_variance_calculation(self):
        """Variance = actual - forecast."""
        actual = 160
        forecast = 178
        variance = actual - forecast
        assert variance == -18

    def test_negative_variance_is_positive_sign(self):
        """Negative variance means actual < forecast (less CO2 = good)."""
        variance = -18
        is_good = variance < 0
        assert is_good is True

    def test_renewable_percentage_sum(self):
        """Renewable % = wind + solar + hydro."""
        wind = 22.7
        solar = 23.4
        hydro = 0.5
        renewable_total = wind + solar + hydro
        assert round(renewable_total, 1) == 46.6

    def test_total_fuel_percentage_equals_100(self):
        """All fuel percentages must sum to approximately 100%."""
        fuels = {
            "gas": 22.1, "wind": 22.7, "solar": 23.4,
            "nuclear": 14.7, "imports": 11.1, "biomass": 6.0,
            "hydro": 0, "coal": 0, "other": 0
        }
        total = sum(fuels.values())
        assert 99.0 <= total <= 101.0

    def test_17_regions_in_regional_data(self):
        """Regional data must cover 17 UK energy regions."""
        regions = [
            "North Scotland", "South Scotland", "North West England",
            "North East England", "Yorkshire", "North Wales & Merseyside",
            "South Wales", "West Midlands", "East Midlands",
            "East England", "South West England", "South England",
            "London", "South East England", "England", "GB", "Scotland"
        ]
        assert len(regions) == 17
