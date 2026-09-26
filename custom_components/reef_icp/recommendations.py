"""Provider-independent supply recommendations plus newer manufacturer systems.

Established Fauna Marin, ATI, Oceamo and TRITON rules remain in
``recommendations_core``. This wrapper adds Tropic Marin, SANGOKAI and
manufacturer-guided systems, applies personal targets, and excludes RO/osmosis
values from aquarium dosing calculations.
"""

from __future__ import annotations

import copy
from typing import Any

from .const import (
    SUPPLY_SYSTEM_AQUAFOREST_COMPONENT_123,
    SUPPLY_SYSTEM_KORALLEN_ZUCHT_CORAL_SYSTEM,
    SUPPLY_SYSTEM_NAMES,
    SUPPLY_SYSTEM_RED_SEA_REEF_CARE_4_PART,
    SUPPLY_SYSTEM_RED_SEA_REEF_CARE_7_PART,
    SUPPLY_SYSTEM_REEF_MOONSHINERS,
    SUPPLY_SYSTEM_REEF_ZLEMENTS,
    SUPPLY_SYSTEM_SANGOKAI_BALANCE,
    SUPPLY_SYSTEM_TROPIC_MARIN_ALL_FOR_REEF,
    SUPPLY_SYSTEM_TROPIC_MARIN_ORIGINAL_BALLING,
)
from .recommendations_core import *  # noqa: F403
from .recommendations_core import (
    _generic_correction,
    _measurement_needs_action,
    _target_relation,
    build_supply_recommendations as _build_supply_recommendations_core,
)

_TM_BALLING_URL = "https://www.tropic-marin-smartinfo.com/original-balling-components"
_TM_AFR_URL = "https://www.tropic-marin-smartinfo.com/"
_TM_POTASSIUM_URL = "https://www.tropic-marin-smartinfo.com/potassium"
_TM_MAGNESIUM_URL = "https://www.tropic-marin-smartinfo.com/bio-magnesium"
_TM_IODINE_URL = "https://www.tropic-marin-smartinfo.com/iodine"
_TM_BROMINE_URL = "https://www.tropic-marin-smartinfo.com/bromine"
_TM_IRON_URL = "https://www.tropic-marin-smartinfo.com/iron"
_TM_K_URL = "https://www.tropic-marin-smartinfo.com/k-elements"
_TM_A_URL = "https://www.tropic-marin-smartinfo.com/a-elements"
_AF_123_URL = "https://aquaforest.eu/de/produkte/seawater/wasseraufbereitung/component-123/"
_RED_SEA_URL = "https://redseafish.com/reef-care-program/"
_SANGOKAI_BALANCE_URL = "https://sangokai.org/?page_id=4492"
_SANGOKAI_INDIVIDUAL_URL = "https://sangokai.org/?page_id=10575"
_KZ_CORAL_SYSTEM_URL = "https://www.korallen-zucht.de/out/pictures/wysiwigpro/korallenzucht_guide_easy_reefing.pdf"
_ZLEMENTS_URL = "https://icp.reef-zlements.com/"
_MOONSHINERS_URL = "https://reefmoonshiners.com/pages/handbook-tools"

_TM_BALLING_RULES: dict[str, dict[str, Any]] = {
    "calcium": {"name": "Calcium", "product": "Tropic Marin Original Balling", "kind": "core", "dose_amount": 50.0, "dose_unit": "ml", "increase": 10.0, "unit": "mg/l", "max_daily_increase": 30.0, "solution": "Part A", "requires_report_type": None, "source_name": "Tropic Marin Original Balling", "source_url": _TM_BALLING_URL},
    "alkalinitaet": {"name": "Alkalinität", "product": "Tropic Marin Original Balling", "kind": "core", "dose_amount": 50.0, "dose_unit": "ml", "increase": 1.4, "unit": "dKH", "max_daily_increase": 4.2, "solution": "Part B", "requires_report_type": None, "source_name": "Tropic Marin Original Balling", "source_url": _TM_BALLING_URL},
    "magnesium": {"name": "Magnesium", "product": "Tropic Marin Bio-Magnesium Liquid", "kind": "core_correction", "dose_amount": 50.0, "dose_unit": "ml", "increase": 25.0, "unit": "mg/l", "max_daily_increase": 25.0, "solution": None, "requires_report_type": None, "source_name": "Tropic Marin Bio-Magnesium", "source_url": _TM_MAGNESIUM_URL},
    "kalium": {"name": "Kalium", "product": "Tropic Marin Potassium", "kind": "single_element", "dose_amount": 10.0, "dose_unit": "ml", "increase": 10.0, "unit": "mg/l", "max_daily_increase": 20.0, "solution": None, "requires_report_type": None, "source_name": "Tropic Marin Potassium", "source_url": _TM_POTASSIUM_URL},
    "iod": {"name": "Iod", "product": "Tropic Marin Iodine", "kind": "single_element", "dose_amount": 1.5, "dose_unit": "ml", "increase": 15.0, "unit": "µg/l", "max_daily_increase": 30.0, "solution": None, "requires_report_type": None, "source_name": "Tropic Marin Iodine", "source_url": _TM_IODINE_URL},
    "bromid": {"name": "Bromid", "product": "Tropic Marin Bromine", "kind": "single_element", "dose_amount": 5.0, "dose_unit": "ml", "increase": 5.0, "unit": "mg/l", "max_daily_increase": 10.0, "solution": None, "requires_report_type": None, "source_name": "Tropic Marin Bromine", "source_url": _TM_BROMINE_URL},
    "eisen": {"name": "Eisen", "product": "Tropic Marin Iron", "kind": "single_element", "dose_amount": 1.0, "dose_unit": "ml", "increase": 1.0, "unit": "µg/l", "max_daily_increase": 4.0, "solution": None, "requires_report_type": None, "source_name": "Tropic Marin Iron", "source_url": _TM_IRON_URL},
}

_TM_TRACE_MAINTENANCE = {
    "k_plus_elements": {"product": "Tropic Marin K+ Elements", "elements": ["barium", "bor", "chrom", "eisen", "cobalt", "kupfer", "mangan", "nickel", "strontium", "zink"], "daily_dose_ml_per_100_l": 1.0, "max_daily_dose_ml_per_100_l": 2.0, "source_url": _TM_K_URL},
    "a_minus_elements": {"product": "Tropic Marin A- Elements", "elements": ["bromid", "fluorid", "iod", "lithium", "molybdaen", "selen", "vanadium"], "daily_dose_ml_per_100_l": 1.0, "max_daily_dose_ml_per_100_l": 2.0, "source_url": _TM_A_URL},
}

_SANGOKAI_RULES: dict[str, dict[str, Any]] = {
    "calcium": {"name": "Calcium", "product": "SANGOKAI BALANCE Ca-1", "kind": "core", "dose_amount": 2.5, "dose_unit": "ml", "increase": 1.0, "unit": "mg/l", "max_daily_increase": None, "solution": "working solution", "requires_report_type": None, "source_name": "SANGOKAI BALANCE", "source_url": "https://sangokai.org/?page_id=5133"},
    "alkalinitaet": {"name": "Alkalinität", "product": "SANGOKAI BALANCE KH", "kind": "core", "dose_amount": 40.0, "dose_unit": "ml", "increase": 1.0, "unit": "dKH", "max_daily_increase": None, "solution": "10x diluted working solution", "requires_report_type": None, "source_name": "SANGOKAI BALANCE", "source_url": "https://sangokai.org/?page_id=5163"},
    "kalium": {"name": "Kalium", "product": "SANGOKAI INDIVIDUAL K", "kind": "single_element", "dose_amount": 10.0, "dose_unit": "ml", "increase": 10.0, "unit": "mg/l", "max_daily_increase": 20.0, "solution": None, "requires_report_type": None, "source_name": "SANGOKAI INDIVIDUAL", "source_url": "https://sangokai.org/?page_id=8771"},
    "strontium": {"name": "Strontium", "product": "SANGOKAI INDIVIDUAL Sr", "kind": "single_element", "dose_amount": 10.0, "dose_unit": "ml", "increase": 1.0, "unit": "mg/l", "max_daily_increase": 4.0, "solution": None, "requires_report_type": None, "source_name": "SANGOKAI INDIVIDUAL", "source_url": "https://sangokai.org/?page_id=9006"},
    "bor": {"name": "Bor", "product": "SANGOKAI INDIVIDUAL B", "kind": "single_element", "dose_amount": 10.0, "dose_unit": "ml", "increase": 0.5, "unit": "mg/l", "max_daily_increase": 4.0, "solution": None, "requires_report_type": None, "source_name": "SANGOKAI INDIVIDUAL", "source_url": "https://sangokai.org/?page_id=8963"},
    "bromid": {"name": "Bromid", "product": "SANGOKAI INDIVIDUAL BrF", "kind": "single_element", "dose_amount": 10.0, "dose_unit": "ml", "increase": 5.0, "unit": "mg/l", "max_daily_increase": 5.0, "solution": None, "requires_report_type": None, "source_name": "SANGOKAI INDIVIDUAL", "source_url": _SANGOKAI_INDIVIDUAL_URL},
    "iod": {"name": "Iod", "product": "SANGOKAI INDIVIDUAL IF", "kind": "single_element", "dose_amount": 1.0, "dose_unit": "ml", "increase": 50.0, "unit": "µg/l", "max_daily_increase": None, "solution": None, "requires_report_type": None, "source_name": "SANGOKAI INDIVIDUAL", "source_url": _SANGOKAI_INDIVIDUAL_URL},
}


def _is_aquarium_measurement(measurement: dict[str, Any]) -> bool:
    return str(measurement.get("category") or "") != "osmosis"


def _volume(value: Any) -> float:
    try:
        volume_l = float(value)
    except (TypeError, ValueError):
        return 0.0
    return volume_l if volume_l > 0 else 0.0


def _scaled(amount_per_100_l: float, volume_l: float) -> float:
    return round(float(amount_per_100_l) * volume_l / 100.0, 3)


def _missing_volume_result(system: str) -> dict[str, Any]:
    return {"system": system, "system_name": SUPPLY_SYSTEM_NAMES.get(system, system), "supported": False, "reason": "missing_volume", "items": []}


def _build_tropic_marin_original_balling(aquarium_volume_l: Any, measurements: list[dict[str, Any]]) -> dict[str, Any]:
    system = SUPPLY_SYSTEM_TROPIC_MARIN_ORIGINAL_BALLING
    volume_l = _volume(aquarium_volume_l)
    if volume_l <= 0:
        return _missing_volume_result(system)
    items: list[dict[str, Any]] = []
    for measurement in measurements:
        rule = _TM_BALLING_RULES.get(str(measurement.get("key") or ""))
        if rule is None:
            continue
        item = _generic_correction(measurement, volume_l, rule)
        if item is not None:
            items.append(item)
    return {
        "system": system,
        "system_name": SUPPLY_SYSTEM_NAMES[system],
        "supported": True,
        "volume_l": volume_l,
        "mode": "calculated",
        "items": items,
        "calculated_keys": sorted(_TM_BALLING_RULES),
        "maintenance_note": "tropic_marin_original_balling_consumption",
        "maintenance_requires_consumption": True,
        "maintenance_source_url": _TM_BALLING_URL,
        "trace_elements_implemented": True,
        "numeric_trace_calculation": True,
        "trace_maintenance": copy.deepcopy(_TM_TRACE_MAINTENANCE),
        "trace_maintenance_note": "K+ Elements and A- Elements remain mixed maintenance supplements; Reef ICP does not invent their individual element concentrations.",
    }


def _maintenance_result(system: str, aquarium_volume_l: Any, *, source_url: str, guidance: dict[str, Any], mode: str = "maintenance_guidance") -> dict[str, Any]:
    volume_l = _volume(aquarium_volume_l)
    if volume_l <= 0:
        return _missing_volume_result(system)
    return {
        "system": system,
        "system_name": SUPPLY_SYSTEM_NAMES.get(system, system),
        "supported": True,
        "volume_l": volume_l,
        "mode": mode,
        "items": [],
        "maintenance_source_url": source_url,
        "maintenance_guidance": guidance,
        "maintenance_requires_consumption": True,
        "trace_elements_implemented": True,
        "numeric_trace_calculation": False,
    }


def _build_all_for_reef(aquarium_volume_l: Any) -> dict[str, Any]:
    volume_l = _volume(aquarium_volume_l)
    if volume_l <= 0:
        return _missing_volume_result(SUPPLY_SYSTEM_TROPIC_MARIN_ALL_FOR_REEF)
    return _maintenance_result(
        SUPPLY_SYSTEM_TROPIC_MARIN_ALL_FOR_REEF,
        volume_l,
        source_url=_TM_AFR_URL,
        guidance={
            "product": "Tropic Marin All-For-Reef",
            "start_daily_ml": _scaled(5.0, volume_l),
            "weekly_increase_ml": _scaled(2.5, volume_l),
            "max_daily_ml": _scaled(25.0, volume_l),
            "start_ml_per_100_l": 5.0,
            "weekly_increase_ml_per_100_l": 2.5,
            "max_daily_ml_per_100_l": 25.0,
            "regulator": "alkalinity_and_calcium",
            "note": "Balanced maintenance system; establish Ca/KH/Mg first and do not use the maintenance dose as a one-parameter emergency correction.",
        },
    )


def _build_aquaforest_component_123(aquarium_volume_l: Any) -> dict[str, Any]:
    volume_l = _volume(aquarium_volume_l)
    if volume_l <= 0:
        return _missing_volume_result(SUPPLY_SYSTEM_AQUAFOREST_COMPONENT_123)
    return _maintenance_result(
        SUPPLY_SYSTEM_AQUAFOREST_COMPONENT_123,
        volume_l,
        source_url=_AF_123_URL,
        guidance={
            "products": ["Component 1+", "Component 2+", "Component 3+"],
            "typical_daily_ml_each": _scaled(25.0, volume_l),
            "typical_daily_ml_each_per_100_l": 25.0,
            "equal_amounts": True,
            "split_into_small_doses": True,
            "published_reference_increase": {"component_1_calcium_mg_l": 4.5, "component_2_alkalinity_dkh": 0.65, "component_3_magnesium_mg_l": 0.38, "reference_dose_ml_per_100_l": 25.0},
            "note": "Keep 1+2+3+ balanced. Correct individual Ca/Mg/KH deficits with separate supplements rather than unbalancing the three components.",
        },
    )


def _build_red_sea(system: str, aquarium_volume_l: Any) -> dict[str, Any]:
    variant = "4-Part" if system == SUPPLY_SYSTEM_RED_SEA_REEF_CARE_4_PART else "7-Part"
    return _maintenance_result(
        system,
        aquarium_volume_l,
        source_url=_RED_SEA_URL,
        mode="official_guidance",
        guidance={"product": f"Red Sea Reef Care {variant}", "variant": variant, "use_manufacturer_recipe": True, "note": "Red Sea has multiple product generations/concentrations. Reef ICP therefore does not apply one concentration formula across all variants."},
    )


def _build_kz_coral_system(aquarium_volume_l: Any) -> dict[str, Any]:
    volume_l = _volume(aquarium_volume_l)
    if volume_l <= 0:
        return _missing_volume_result(SUPPLY_SYSTEM_KORALLEN_ZUCHT_CORAL_SYSTEM)
    return _maintenance_result(
        SUPPLY_SYSTEM_KORALLEN_ZUCHT_CORAL_SYSTEM,
        volume_l,
        source_url=_KZ_CORAL_SYSTEM_URL,
        guidance={
            "products": ["Korallen-Zucht Coral System 1", "Korallen-Zucht Coral System 2", "Korallen-Zucht Coral System 3", "Korallen-Zucht Coral System 4"],
            "weekly_ml_each": _scaled(5.0, volume_l),
            "weekly_ml_each_per_100_l": 5.0,
            "note": "Coral System 1-4 is trace/mineral maintenance and does not replace separate Ca/KH/Mg supply.",
        },
    )


def _official_calculator_items(measurements: list[dict[str, Any]], *, product: str, source_name: str, source_url: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for measurement in measurements:
        if not _measurement_needs_action(measurement):
            continue
        current = measurement.get("value")
        relation, target_value = _target_relation(measurement)
        if not isinstance(current, (int, float)) or relation not in {"low", "high"} or target_value is None:
            continue
        item = {"key": str(measurement.get("key") or ""), "name": measurement.get("name") or measurement.get("key"), "product": product, "kind": "manufacturer_guided", "current": float(current), "target": float(target_value), "unit": measurement.get("unit"), "severity": str((measurement.get("status") or {}).get("severity", "unknown")), "source_name": source_name, "source_url": source_url}
        if relation == "high":
            item.update({"action": "reduce_or_pause", "dose_amount": 0.0, "dose_unit": "ml"})
        else:
            item["action"] = "official_calculator"
        items.append(item)
    return items


def _build_official_tool_system(system: str, aquarium_volume_l: Any, measurements: list[dict[str, Any]], *, product: str, source_name: str, source_url: str) -> dict[str, Any]:
    volume_l = _volume(aquarium_volume_l)
    if volume_l <= 0:
        return _missing_volume_result(system)
    return {
        "system": system,
        "system_name": SUPPLY_SYSTEM_NAMES.get(system, system),
        "supported": True,
        "volume_l": volume_l,
        "mode": "official_calculator",
        "items": _official_calculator_items(measurements, product=product, source_name=source_name, source_url=source_url),
        "maintenance_source_url": source_url,
        "trace_elements_implemented": True,
        "numeric_trace_calculation": False,
    }


def _build_sangokai(aquarium_volume_l: Any, measurements: list[dict[str, Any]]) -> dict[str, Any]:
    system = SUPPLY_SYSTEM_SANGOKAI_BALANCE
    volume_l = _volume(aquarium_volume_l)
    if volume_l <= 0:
        return _missing_volume_result(system)
    items: list[dict[str, Any]] = []
    for measurement in measurements:
        key = str(measurement.get("key") or "")
        rule = _SANGOKAI_RULES.get(key)
        if rule is None:
            continue
        item = _generic_correction(measurement, volume_l, rule)
        if item is None:
            continue
        if key == "calcium":
            item["companion_product"] = "SANGOKAI BALANCE Ca-2"
            item["companion_dose_equal_to_primary"] = True
            item["companion_note"] = "Use the BALANCE Ca-2 working solution in the corresponding amount for ionic balance according to the BALANCE instructions."
        items.append(item)
    return {
        "system": system,
        "system_name": SUPPLY_SYSTEM_NAMES[system],
        "supported": True,
        "volume_l": volume_l,
        "mode": "calculated",
        "items": items,
        "calculated_keys": sorted(_SANGOKAI_RULES),
        "maintenance_note": "sangokai_balance_consumption",
        "maintenance_requires_consumption": True,
        "maintenance_source_url": _SANGOKAI_BALANCE_URL,
        "individual_source_url": _SANGOKAI_INDIVIDUAL_URL,
        "trace_elements_implemented": True,
        "numeric_trace_calculation": True,
    }


def _measurement_for_personal_target(measurement: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    target = measurement.get("custom_target")
    if not isinstance(target, dict) or target.get("type") != "range":
        return measurement, False
    minimum = target.get("min")
    maximum = target.get("max")
    if not isinstance(minimum, (int, float)) or not isinstance(maximum, (int, float)):
        return measurement, False
    prepared = copy.deepcopy(measurement)
    prepared["target"] = {"type": "range", "min": float(minimum), "max": float(maximum)}
    current = prepared.get("value")
    if not isinstance(current, (int, float)) or isinstance(current, bool):
        prepared["status"] = {"severity": "unknown", "direction": None}
    elif float(current) < float(minimum):
        prepared["status"] = {"severity": "warning", "direction": "low"}
    elif float(current) > float(maximum):
        prepared["status"] = {"severity": "warning", "direction": "high"}
    else:
        prepared["status"] = {"severity": "ok", "direction": None}
    prepared["reef_target_source"] = "aquarium_custom"
    return prepared, True


def build_supply_recommendations(
    supply_system: str | None,
    aquarium_volume_l: Any,
    measurements: list[dict[str, Any]],
    report_type: str | None = None,
) -> dict[str, Any] | None:
    """Build supply recommendations using aquarium-water values only."""
    prepared_measurements: list[dict[str, Any]] = []
    custom_keys: set[str] = set()
    for measurement in measurements:
        if not _is_aquarium_measurement(measurement):
            continue
        prepared, used_custom_target = _measurement_for_personal_target(measurement)
        prepared_measurements.append(prepared)
        if used_custom_target:
            custom_keys.add(str(measurement.get("key") or ""))

    if supply_system == SUPPLY_SYSTEM_TROPIC_MARIN_ORIGINAL_BALLING:
        result = _build_tropic_marin_original_balling(aquarium_volume_l, prepared_measurements)
    elif supply_system == SUPPLY_SYSTEM_TROPIC_MARIN_ALL_FOR_REEF:
        result = _build_all_for_reef(aquarium_volume_l)
    elif supply_system == SUPPLY_SYSTEM_AQUAFOREST_COMPONENT_123:
        result = _build_aquaforest_component_123(aquarium_volume_l)
    elif supply_system in {SUPPLY_SYSTEM_RED_SEA_REEF_CARE_4_PART, SUPPLY_SYSTEM_RED_SEA_REEF_CARE_7_PART}:
        result = _build_red_sea(supply_system, aquarium_volume_l)
    elif supply_system == SUPPLY_SYSTEM_SANGOKAI_BALANCE:
        result = _build_sangokai(aquarium_volume_l, prepared_measurements)
    elif supply_system == SUPPLY_SYSTEM_KORALLEN_ZUCHT_CORAL_SYSTEM:
        result = _build_kz_coral_system(aquarium_volume_l)
    elif supply_system == SUPPLY_SYSTEM_REEF_ZLEMENTS:
        result = _build_official_tool_system(SUPPLY_SYSTEM_REEF_ZLEMENTS, aquarium_volume_l, prepared_measurements, product="Reef Zlements element correction", source_name="Reef Zlements ICP portal", source_url=_ZLEMENTS_URL)
    elif supply_system == SUPPLY_SYSTEM_REEF_MOONSHINERS:
        result = _build_official_tool_system(SUPPLY_SYSTEM_REEF_MOONSHINERS, aquarium_volume_l, prepared_measurements, product="Reef Moonshiner's element correction", source_name="Reef Moonshiner's Assessment & Dosing Tools", source_url=_MOONSHINERS_URL)
    else:
        result = _build_supply_recommendations_core(supply_system, aquarium_volume_l, prepared_measurements, report_type)

    if result is None:
        return None
    result = copy.deepcopy(result)
    result["custom_target_keys"] = sorted(key for key in custom_keys if key)
    for item in result.get("items", []):
        if not isinstance(item, dict):
            continue
        item["target_source"] = "aquarium_custom" if str(item.get("key") or "") in custom_keys else "laboratory"
    return result
