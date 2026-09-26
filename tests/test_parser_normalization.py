"""Regression tests for provider-independent report normalization."""

from __future__ import annotations

from custom_components.reef_icp.parser import _normalize_osmosis_display_names


def test_osmosis_suffix_is_added_once_without_changing_identity() -> None:
    report = {
        "measurements": [
            {"category": "osmosis", "key": "calcium", "name": "Calcium"},
            {"category": "osmosis", "key": "kupfer", "name": "Kupfer (Osmose)"},
            {"category": "major_elements", "key": "calcium", "name": "Calcium"},
        ]
    }

    normalized = _normalize_osmosis_display_names(report)
    measurements = normalized["measurements"]

    assert measurements[0]["name"] == "Calcium (Osmose)"
    assert measurements[0]["key"] == "calcium"
    assert measurements[0]["category"] == "osmosis"
    assert measurements[1]["name"] == "Kupfer (Osmose)"
    assert measurements[2]["name"] == "Calcium"
