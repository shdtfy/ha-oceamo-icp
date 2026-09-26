"""Regression tests for reef/nutrient methods introduced in 0.15.0."""

from __future__ import annotations

import pytest

from custom_components.reef_icp.const import (
    REEF_METHOD_AQUAFOREST_PROBIOTIC,
    REEF_METHOD_AQUAFOREST_ZEO_MIX,
    REEF_METHOD_BRIGHTWELL_NEOZEO,
    REEF_METHOD_FAUNA_MARIN_ZEO_LIGHT,
    REEF_METHOD_KORALLEN_ZUCHT_ZEOVIT,
    REEF_METHOD_RED_SEA_NOPOX,
    REEF_METHOD_SANGOKAI_BASIS,
    STOCKING_PROFILE_FISH_ONLY,
    STOCKING_PROFILE_MIXED_REEF,
    STOCKING_PROFILE_SPS_DOMINANT,
)
from custom_components.reef_icp.reef_methods import build_reef_method_guidance


def phosphate(value: float, *, category: str = "nutrients") -> dict:
    return {"key": "phosphat", "name": "Phosphat", "category": category, "value": value, "raw_value": str(value), "unit": "mg/l"}


def test_zeovit_long_term_scales_media_and_flow() -> None:
    result = build_reef_method_guidance(REEF_METHOD_KORALLEN_ZUCHT_ZEOVIT, 800)
    items = {item["key"]: item for item in result["items"]}
    assert items["zeovit_media"]["amount"] == pytest.approx(2.0)
    assert items["reactor_flow"]["minimum"] == pytest.approx(400.0)
    assert items["reactor_flow"]["maximum"] == pytest.approx(800.0)
    assert items["media_change"]["minimum"] == 6
    assert items["media_change"]["maximum"] == 8


def test_fauna_zeo_light_scales_published_media() -> None:
    result = build_reef_method_guidance(REEF_METHOD_FAUNA_MARIN_ZEO_LIGHT, 500)
    items = {item["key"]: item for item in result["items"]}
    assert items["zeolite"]["amount"] == pytest.approx(0.5)
    assert items["color_elements"]["amount"] == pytest.approx(10.0)
    assert items["color_elements"]["maximum_amount"] == pytest.approx(15.0)


def test_aquaforest_zeo_mix_has_media_flow_and_six_week_change() -> None:
    result = build_reef_method_guidance(REEF_METHOD_AQUAFOREST_ZEO_MIX, 250)
    items = {item["key"]: item for item in result["items"]}
    assert items["zeo_mix"]["amount"] == pytest.approx(250.0)
    assert items["zeo_mix"]["replace_every_weeks"] == 6
    assert items["flow"]["minimum"] == pytest.approx(300.0)
    assert items["flow"]["maximum"] == pytest.approx(500.0)


def test_aquaforest_probiotic_scales_both_daily_products() -> None:
    result = build_reef_method_guidance(REEF_METHOD_AQUAFOREST_PROBIOTIC, 300)
    items = {item["key"]: item for item in result["items"]}
    assert items["pro_bio_s"]["amount"] == pytest.approx(3.0)
    assert items["np_pro"]["amount"] == pytest.approx(3.0)


def test_brightwell_neozeo_preserves_staged_setup() -> None:
    result = build_reef_method_guidance(REEF_METHOD_BRIGHTWELL_NEOZEO, 378.5)
    items = {item["key"]: item for item in result["items"]}
    assert items["weeks_1_2"]["neozeo_add_g_per_week"] == pytest.approx(200.0)
    assert items["weeks_1_2"]["reactor_flow_l_h"] == pytest.approx(94.6)
    assert items["weeks_3_4"]["microbacter7_ml_daily"] == pytest.approx(2.5)
    assert items["maintenance"]["media_change_fraction"] == pytest.approx(0.25)
    assert items["maintenance"]["media_change_every_weeks"] == 6


@pytest.mark.parametrize(("po4", "expected_per_100"), [(0.01, 0.25), (0.02, 0.5), (0.08, 0.5)])
def test_sangokai_basis_maintenance_uses_phosphate_branch(po4: float, expected_per_100: float) -> None:
    result = build_reef_method_guidance(REEF_METHOD_SANGOKAI_BASIS, 200, [phosphate(po4)])
    assert result["phosphate_mg_l"] == pytest.approx(po4)
    for item in result["items"]:
        assert item["maintenance_ml_per_100_l"] == pytest.approx(expected_per_100)
        assert item["amount"] == pytest.approx(expected_per_100 * 2)


def test_sangokai_basis_never_uses_osmosis_phosphate() -> None:
    result = build_reef_method_guidance(REEF_METHOD_SANGOKAI_BASIS, 100, [phosphate(0.5, category="osmosis")])
    assert result["phosphate_mg_l"] is None
    assert all(item["amount"] is None for item in result["items"])


def test_red_sea_nopox_scales_profile_guidance() -> None:
    mixed = build_reef_method_guidance(REEF_METHOD_RED_SEA_NOPOX, 250, stocking_profile=STOCKING_PROFILE_MIXED_REEF)
    sps = build_reef_method_guidance(REEF_METHOD_RED_SEA_NOPOX, 250, stocking_profile=STOCKING_PROFILE_SPS_DOMINANT)
    fish = build_reef_method_guidance(REEF_METHOD_RED_SEA_NOPOX, 250, stocking_profile=STOCKING_PROFILE_FISH_ONLY)
    assert mixed["items"][0]["amount"] == pytest.approx(5.0)
    assert sps["items"][0]["minimum"] == pytest.approx(2.5)
    assert sps["items"][0]["maximum"] == pytest.approx(5.0)
    assert fish["items"][0]["amount"] == pytest.approx(7.5)
