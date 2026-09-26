"""Reef / nutrient-method guidance for Reef ICP.

Supply systems and reef/nutrient methods are intentionally independent.
Only manufacturer-published quantities are calculated. RO/osmosis values never
participate in aquarium dosing guidance.
"""

from __future__ import annotations

from typing import Any

from .const import (
    REEF_METHOD_AQUAFOREST_PROBIOTIC,
    REEF_METHOD_AQUAFOREST_ZEO_MIX,
    REEF_METHOD_BRIGHTWELL_NEOZEO,
    REEF_METHOD_FAUNA_MARIN_ZEO_LIGHT,
    REEF_METHOD_KORALLEN_ZUCHT_ZEOVIT,
    REEF_METHOD_NAMES,
    REEF_METHOD_NONE,
    REEF_METHOD_RED_SEA_NOPOX,
    REEF_METHOD_SANGOKAI_BASIS,
    STOCKING_PROFILE_FISH_ONLY,
    STOCKING_PROFILE_LPS_DOMINANT,
    STOCKING_PROFILE_MIXED_REEF,
    STOCKING_PROFILE_SOFT_CORAL_DOMINANT,
    STOCKING_PROFILE_SPS_DOMINANT,
)

_KZ_ZEOVIT_URL = "https://www.korallen-zucht.de/Meerwasseraquarium-Pflege/ZEOvit-Grundwasserpflege/ZEOvit-1-L.html"
_FAUNA_ZEO_LIGHT_URL = "https://static.faunamarin.de/Werbung/HTUs/FM_HTU_Zeo_Light_System_web.pdf"
_AF_ZEO_MIX_URL = "https://aquaforest.eu/de/produkte/seawater/wasseraufbereitung/zeo-mix/"
_AF_PRO_BIO_S_URL = "https://aquaforest.eu/de/produkte/seawater/probiotische-methode/pro-bio-s/"
_AF_NP_PRO_URL = "https://aquaforest.eu/de/produkte/seawater/probiotische-methode/np-pro/"
_BRIGHTWELL_NEOZEO_URL = "https://www.brightwellaquatics.com/products/neozeot.php"
_SANGOKAI_BASIS_URL = "https://sangokai.org/?page_id=5443"
_RED_SEA_NOPOX_URL = "https://g1.redseafish.com/de/reef-care-program/no3po4-x/"


def _volume(value: Any) -> float:
    try:
        volume_l = float(value)
    except (TypeError, ValueError):
        return 0.0
    return volume_l if volume_l > 0 else 0.0


def _scale(amount: float, volume_l: float, reference_l: float = 100.0) -> float:
    return round(float(amount) * volume_l / float(reference_l), 3)


def _base_result(method: str, volume_l: float, source_url: str) -> dict[str, Any]:
    return {
        "method": method,
        "method_name": REEF_METHOD_NAMES.get(method, method),
        "supported": True,
        "volume_l": volume_l,
        "mode": "calculated_guidance",
        "source_url": source_url,
        "items": [],
    }


def _aquarium_measurements(measurements: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    return [
        item for item in (measurements or [])
        if isinstance(item, dict) and str(item.get("category") or "") != "osmosis"
    ]


def _phosphate_value(measurements: list[dict[str, Any]] | None) -> float | None:
    preferred = ("phosphat", "phosphat_photometrisch", "gesamtphosphat_errechnet")
    by_key = {str(item.get("key") or ""): item for item in _aquarium_measurements(measurements)}
    for key in preferred:
        item = by_key.get(key)
        if not item:
            continue
        value = item.get("value")
        unit = str(item.get("unit") or "").lower()
        if isinstance(value, (int, float)) and unit in {"mg/l", "mg/l po4", ""}:
            return float(value)
    return None


def _kz_zeovit(volume_l: float) -> dict[str, Any]:
    result = _base_result(REEF_METHOD_KORALLEN_ZUCHT_ZEOVIT, volume_l, _KZ_ZEOVIT_URL)
    media_l = _scale(1.0, volume_l, 400.0)
    result["items"] = [
        {"key": "zeovit_media", "kind": "media", "product": "Korallen-Zucht ZEOvit", "amount": media_l, "unit": "L", "frequency": "continuous"},
        {"key": "reactor_flow", "kind": "flow", "product": "ZEOvit reactor", "minimum": round(media_l * 200.0, 1), "maximum": round(media_l * 400.0, 1), "unit": "L/h"},
        {"key": "media_change", "kind": "interval", "product": "Korallen-Zucht ZEOvit", "minimum": 6, "maximum": 8, "unit": "weeks", "replacement_fraction": 1.0},
        {"key": "cleaning", "kind": "maintenance", "product": "ZEOvit reactor", "frequency": "daily", "note": "Keep the media free of deposits by moving the reactor cleaning rod."},
    ]
    result["caution"] = "Long-term ZEOvit values. Tank conversion and new-tank startup use different published flow regimes."
    return result


def _fauna_zeo_light(volume_l: float) -> dict[str, Any]:
    result = _base_result(REEF_METHOD_FAUNA_MARIN_ZEO_LIGHT, volume_l, _FAUNA_ZEO_LIGHT_URL)
    result["items"] = [
        {"key": "zeolite", "kind": "media", "product": "Fauna Marin zeolite", "amount": _scale(1.0, volume_l, 1000.0), "unit": "L", "frequency": "continuous", "clean_every_days": "2-3", "replace_every_weeks": "4-6", "replacement_fraction": 0.75},
        {"key": "reef_vitality", "kind": "dose", "product": "Fauna Marin Reef Vitality", "amount": _scale(1.0, volume_l, 1000.0), "unit": "capsule", "frequency": "every_4_days"},
        {"key": "carb_l", "kind": "media", "product": "Fauna Marin Carb L", "minimum": _scale(250.0, volume_l, 1000.0), "maximum": _scale(300.0, volume_l, 1000.0), "unit": "g", "max_reactor_flow_l_h": 200.0},
        {"key": "color_elements", "kind": "dose", "product": "Fauna Marin Color Elements", "amount": _scale(2.0, volume_l), "start_amount": _scale(0.5, volume_l), "maximum_amount": _scale(3.0, volume_l), "unit": "ml", "frequency": "every_4_days"},
        {"key": "coral_sprint", "kind": "dose", "product": "Fauna Marin Coral Sprint", "amount": _scale(1.0, volume_l, 500.0), "unit": "measuring_spoon", "reference_spoon_ml": 6.0, "frequency": "every_2_days"},
        {"key": "min_s", "kind": "dose_range", "product": "Fauna Marin Min S", "minimum": _scale(1.0, volume_l, 1000.0), "maximum": _scale(3.0, volume_l, 1000.0), "unit": "drop", "frequency": "every_2_days"},
    ]
    return result


def _aquaforest_zeo_mix(volume_l: float) -> dict[str, Any]:
    result = _base_result(REEF_METHOD_AQUAFOREST_ZEO_MIX, volume_l, _AF_ZEO_MIX_URL)
    result["items"] = [
        {"key": "zeo_mix", "kind": "media", "product": "Aquaforest Zeo Mix", "amount": _scale(100.0, volume_l), "unit": "ml", "frequency": "continuous", "replace_every_weeks": 6, "note": "Rinse with RODI before use; shaking is not required."},
        {"key": "flow", "kind": "flow", "product": "Zeo Mix reactor", "minimum": 300.0, "maximum": 500.0, "unit": "L/h"},
    ]
    return result


def _aquaforest_probiotic(volume_l: float) -> dict[str, Any]:
    result = _base_result(REEF_METHOD_AQUAFOREST_PROBIOTIC, volume_l, _AF_PRO_BIO_S_URL)
    result["secondary_source_url"] = _AF_NP_PRO_URL
    result["items"] = [
        {"key": "pro_bio_s", "kind": "dose", "product": "Aquaforest Pro Bio S", "amount": _scale(1.0, volume_l), "unit": "drop", "frequency": "daily"},
        {"key": "np_pro", "kind": "dose", "product": "Aquaforest -NP Pro", "amount": _scale(1.0, volume_l), "unit": "drop", "frequency": "daily"},
    ]
    return result


def _brightwell_neozeo(volume_l: float) -> dict[str, Any]:
    result = _base_result(REEF_METHOD_BRIGHTWELL_NEOZEO, volume_l, _BRIGHTWELL_NEOZEO_URL)
    ref_l = 378.5
    media = _scale(200.0, volume_l, ref_l)
    result["items"] = [
        {"key": "weeks_1_2", "kind": "stage", "stage": "Weeks 1-2", "neozeo_add_g_per_week": media, "reactor_flow_l_h": _scale(94.6, volume_l, ref_l), "microbacter7_ml_daily": _scale(5.0, volume_l, ref_l), "reef_biofuel_ml_daily": 0.0},
        {"key": "weeks_3_4", "kind": "stage", "stage": "Weeks 3-4", "neozeo_add_g_per_week": media, "reactor_flow_l_h": _scale(189.3, volume_l, ref_l), "microbacter7_ml_daily": _scale(2.5, volume_l, ref_l), "reef_biofuel_ml_daily": _scale(2.5, volume_l, ref_l)},
        {"key": "week_5", "kind": "stage", "stage": "Week 5", "neozeo_add_g_per_week": media, "reactor_flow_l_h": _scale(378.5, volume_l, ref_l), "microbacter7_ml_daily": _scale(2.5, volume_l, ref_l), "reef_biofuel_ml_daily": _scale(2.5, volume_l, ref_l)},
        {"key": "maintenance", "kind": "maintenance", "stage": "After week 5", "media_change_fraction": 0.25, "media_change_every_weeks": 6, "microbacter7_ml_daily_around_change": _scale(2.5, volume_l, ref_l), "reef_biofuel_ml_daily_around_change": _scale(2.5, volume_l, ref_l), "support_dose_duration_days": 7},
    ]
    return result


def _sangokai_basis(volume_l: float, measurements: list[dict[str, Any]] | None) -> dict[str, Any]:
    result = _base_result(REEF_METHOD_SANGOKAI_BASIS, volume_l, _SANGOKAI_BASIS_URL)
    phosphate = _phosphate_value(measurements)
    result["establishment"] = [
        {"week": week, "dose_ml_per_100_l": round(week * 0.1, 1), "dose_ml": _scale(week * 0.1, volume_l)}
        for week in range(1, 6)
    ]
    if phosphate is None:
        maintenance = None
        note = "After week 5: 0.25 ml/100 L/day when PO4 < 0.02 mg/L, otherwise 0.5 ml/100 L/day."
    elif phosphate < 0.02:
        maintenance = 0.25
        note = "PO4 < 0.02 mg/L."
    else:
        maintenance = 0.5
        note = "PO4 >= 0.02 mg/L."
    result["phosphate_mg_l"] = phosphate
    result["items"] = [
        {"key": "basis_1", "kind": "dose", "product": "SANGOKAI BASIS #1", "amount": _scale(maintenance, volume_l) if maintenance is not None else None, "unit": "ml", "frequency": "daily_single_bolus", "maintenance_ml_per_100_l": maintenance},
        {"key": "basis_2", "kind": "dose", "product": "SANGOKAI BASIS #2", "amount": _scale(maintenance, volume_l) if maintenance is not None else None, "unit": "ml", "frequency": "daily_single_bolus", "maintenance_ml_per_100_l": maintenance},
    ]
    result["note"] = note
    return result


def _red_sea_nopox(volume_l: float, stocking_profile: str | None) -> dict[str, Any]:
    result = _base_result(REEF_METHOD_RED_SEA_NOPOX, volume_l, _RED_SEA_NOPOX_URL)
    if stocking_profile == STOCKING_PROFILE_SPS_DOMINANT:
        item = {"key": "nopox", "kind": "dose_range", "product": "Red Sea NO3:PO4-X", "minimum": _scale(1.0, volume_l), "maximum": _scale(2.0, volume_l), "unit": "ml", "frequency": "daily", "reference_profile": "SPS-dominant"}
    elif stocking_profile == STOCKING_PROFILE_FISH_ONLY:
        item = {"key": "nopox", "kind": "dose", "product": "Red Sea NO3:PO4-X", "amount": _scale(3.0, volume_l), "unit": "ml", "frequency": "daily", "reference_profile": "fish-only"}
    elif stocking_profile in {STOCKING_PROFILE_MIXED_REEF, STOCKING_PROFILE_LPS_DOMINANT, STOCKING_PROFILE_SOFT_CORAL_DOMINANT}:
        item = {"key": "nopox", "kind": "dose", "product": "Red Sea NO3:PO4-X", "amount": _scale(2.0, volume_l), "unit": "ml", "frequency": "daily", "reference_profile": "mixed reef"}
    else:
        item = {"key": "nopox", "kind": "guidance", "product": "Red Sea NO3:PO4-X", "amount": None, "unit": "ml", "frequency": "daily", "note": "Select a supported stocking profile for a manufacturer-table dose."}
    result["items"] = [item]
    result["note"] = "Manufacturer average daily program dose by aquarium type, not a one-result ICP correction."
    return result


def build_reef_method_guidance(
    reef_method: str | None,
    aquarium_volume_l: Any,
    measurements: list[dict[str, Any]] | None = None,
    stocking_profile: str | None = None,
) -> dict[str, Any] | None:
    """Build volume-scaled guidance for the selected reef/nutrient method."""
    if not reef_method or reef_method == REEF_METHOD_NONE:
        return None
    volume_l = _volume(aquarium_volume_l)
    if volume_l <= 0:
        return {"method": reef_method, "method_name": REEF_METHOD_NAMES.get(reef_method, reef_method), "supported": False, "reason": "missing_volume", "items": []}
    if reef_method == REEF_METHOD_KORALLEN_ZUCHT_ZEOVIT:
        return _kz_zeovit(volume_l)
    if reef_method == REEF_METHOD_FAUNA_MARIN_ZEO_LIGHT:
        return _fauna_zeo_light(volume_l)
    if reef_method == REEF_METHOD_AQUAFOREST_ZEO_MIX:
        return _aquaforest_zeo_mix(volume_l)
    if reef_method == REEF_METHOD_AQUAFOREST_PROBIOTIC:
        return _aquaforest_probiotic(volume_l)
    if reef_method == REEF_METHOD_BRIGHTWELL_NEOZEO:
        return _brightwell_neozeo(volume_l)
    if reef_method == REEF_METHOD_SANGOKAI_BASIS:
        return _sangokai_basis(volume_l, measurements)
    if reef_method == REEF_METHOD_RED_SEA_NOPOX:
        return _red_sea_nopox(volume_l, stocking_profile)
    return {"method": reef_method, "method_name": REEF_METHOD_NAMES.get(reef_method, reef_method), "supported": False, "reason": "method_not_implemented", "volume_l": volume_l, "items": []}
