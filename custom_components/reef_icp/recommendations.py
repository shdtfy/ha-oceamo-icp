"""Provider-independent supply-system recommendations for Reef ICP.

All numeric product strengths below are based on published manufacturer
instructions. Reef ICP only calculates a correction when the latest normalized
ICP result is numeric and the laboratory/provider status is warning or critical.

A calculated correction is not a permanent daily maintenance dose.
"""

from __future__ import annotations

from math import ceil
from typing import Any

from .const import (
    SUPPLY_SYSTEM_ATI_ESSENTIALS_PRO,
    SUPPLY_SYSTEM_FAUNA_MARIN_BALLING_LIGHT,
    SUPPLY_SYSTEM_NAMES,
    SUPPLY_SYSTEM_OCEAMO_DUO,
    SUPPLY_SYSTEM_TRITON_METHOD,
)


def _rule(
    *,
    name: str,
    product: str,
    kind: str,
    dose_amount: float,
    dose_unit: str,
    increase: float,
    unit: str,
    source_name: str,
    source_url: str,
    max_daily_increase: float | None = None,
    solution: str | None = None,
    requires_report_type: str | None = None,
) -> dict[str, Any]:
    """Return one manufacturer dosing rule."""
    return {
        "name": name,
        "product": product,
        "kind": kind,
        "dose_amount": dose_amount,
        "dose_unit": dose_unit,
        "increase": increase,
        "unit": unit,
        "max_daily_increase": max_daily_increase,
        "solution": solution,
        "requires_report_type": requires_report_type,
        "source_name": source_name,
        "source_url": source_url,
    }


# ---------------------------------------------------------------------------
# Fauna Marin Balling Light + Elementals
# ---------------------------------------------------------------------------

_FAUNA_BALLING_LIGHT_RULES: dict[str, dict[str, Any]] = {
    # Standard Balling Light working solutions.
    "calcium": _rule(
        name="Calcium",
        product="Fauna Marin Balling Light Calcium Mix",
        kind="core",
        dose_amount=10.0,
        dose_unit="ml",
        increase=11.0,
        unit="mg/l",
        solution="Kanister 1",
        source_name="Fauna Marin Balling Light",
        source_url="https://www.faunamarin.de/category/produkte/wasseraufbereitung-de/balling-light-system-de/",
    ),
    "magnesium": _rule(
        name="Magnesium",
        product="Fauna Marin Balling Light Magnesium Mix",
        kind="core",
        dose_amount=10.0,
        dose_unit="ml",
        increase=5.0,
        unit="mg/l",
        solution="Kanister 2",
        source_name="Fauna Marin Balling Light",
        source_url="https://www.faunamarin.de/category/produkte/wasseraufbereitung-de/balling-light-system-de/",
    ),
    "alkalinitaet": _rule(
        name="Alkalinität",
        product="Fauna Marin Balling Light Carbonate Mix",
        kind="core",
        dose_amount=10.0,
        dose_unit="ml",
        increase=0.5,
        unit="dKH",
        solution="Kanister 3",
        source_name="Fauna Marin Balling Light",
        source_url="https://www.faunamarin.de/category/produkte/wasseraufbereitung-de/balling-light-system-de/",
    ),
}

_FAUNA_ELEMENTALS_RULES: dict[str, dict[str, Any]] = {
    "bor": _rule(
        name="Bor",
        product="Fauna Marin Elementals B",
        kind="single_element",
        dose_amount=15.0,
        dose_unit="ml",
        increase=1.0,
        unit="mg/l",
        max_daily_increase=2.0,
        source_name="Fauna Marin Elementals",
        source_url="https://www.faunamarin.de/elementals-b/",
    ),
    "kalium": _rule(
        name="Kalium",
        product="Fauna Marin Elementals K",
        kind="single_element",
        dose_amount=10.0,
        dose_unit="ml",
        increase=10.0,
        unit="mg/l",
        max_daily_increase=50.0,
        source_name="Fauna Marin Elementals",
        source_url="https://www.faunamarin.de/wissensdatenbank/kalium/",
    ),
    "strontium": _rule(
        name="Strontium",
        product="Fauna Marin Elementals Sr",
        kind="single_element",
        dose_amount=10.0,
        dose_unit="ml",
        increase=2.0,
        unit="mg/l",
        max_daily_increase=2.0,
        source_name="Fauna Marin Elementals",
        source_url="https://www.faunamarin.de/wp-content/uploads/2021/04/FM_HTU_ELEMENTALS_DE_NEU_291121.pdf",
    ),
    "fluorid": _rule(
        name="Fluorid",
        product="Fauna Marin Elementals Trace F",
        kind="single_element",
        dose_amount=10.0,
        dose_unit="ml",
        increase=0.2,
        unit="mg/l",
        max_daily_increase=0.5,
        source_name="Fauna Marin Elementals Trace",
        source_url="https://www.faunamarin.de/wp-content/uploads/2021/04/FM_HTU_ELEMENTALS_TRACE_DE_NEU_291121.pdf",
    ),
    "barium": _rule(
        name="Barium",
        product="Fauna Marin Elementals Trace Ba",
        kind="single_element",
        dose_amount=10.0,
        dose_unit="ml",
        increase=5.0,
        unit="µg/l",
        max_daily_increase=5.0,
        source_name="Fauna Marin Elementals Trace",
        source_url="https://www.faunamarin.de/wp-content/uploads/2021/04/FM_HTU_ELEMENTALS_TRACE_DE_NEU_291121.pdf",
    ),
    "cobalt": _rule(
        name="Cobalt",
        product="Fauna Marin Elementals Trace Co",
        kind="single_element",
        dose_amount=1.0,
        dose_unit="ml",
        increase=4.0,
        unit="µg/l",
        max_daily_increase=1.0,
        source_name="Fauna Marin Elementals Trace",
        source_url="https://www.faunamarin.de/wp-content/uploads/2021/04/FM_HTU_ELEMENTALS_TRACE_DE_NEU_291121.pdf",
    ),
    "chrom": _rule(
        name="Chrom",
        product="Fauna Marin Elementals Trace Cr",
        kind="single_element",
        dose_amount=1.0,
        dose_unit="ml",
        increase=0.5,
        unit="µg/l",
        max_daily_increase=0.5,
        source_name="Fauna Marin Elementals Trace",
        source_url="https://www.faunamarin.de/wp-content/uploads/2021/04/FM_HTU_ELEMENTALS_TRACE_DE_NEU_291121.pdf",
    ),
    "eisen": _rule(
        name="Eisen",
        product="Fauna Marin Elementals Trace Fe",
        kind="single_element",
        dose_amount=1.0,
        dose_unit="ml",
        increase=4.0,
        unit="µg/l",
        max_daily_increase=1.0,
        source_name="Fauna Marin Elementals Trace",
        source_url="https://www.faunamarin.de/wp-content/uploads/2021/04/FM_HTU_ELEMENTALS_TRACE_DE_NEU_291121.pdf",
    ),
    "iod": _rule(
        name="Iod",
        product="Fauna Marin Elementals Trace I",
        kind="single_element",
        dose_amount=1.0,
        dose_unit="ml",
        increase=10.0,
        unit="µg/l",
        max_daily_increase=30.0,
        source_name="Fauna Marin Elementals Trace",
        source_url="https://www.faunamarin.de/elementals-trace-i/",
    ),
    "lithium": _rule(
        name="Lithium",
        product="Fauna Marin Elementals Trace Li",
        kind="single_element",
        dose_amount=1.0,
        dose_unit="ml",
        increase=15.0,
        unit="µg/l",
        max_daily_increase=30.0,
        source_name="Fauna Marin Elementals Trace",
        source_url="https://www.faunamarin.de/elementals-trace-li/",
    ),
    "mangan": _rule(
        name="Mangan",
        product="Fauna Marin Elementals Trace Mn",
        kind="single_element",
        dose_amount=1.0,
        dose_unit="ml",
        increase=4.0,
        unit="µg/l",
        max_daily_increase=1.0,
        source_name="Fauna Marin Elementals Trace",
        source_url="https://www.faunamarin.de/wp-content/uploads/2021/04/FM_HTU_ELEMENTALS_TRACE_DE_NEU_291121.pdf",
    ),
    "molybdaen": _rule(
        name="Molybdän",
        product="Fauna Marin Elementals Trace Mo",
        kind="single_element",
        dose_amount=1.0,
        dose_unit="ml",
        increase=6.0,
        unit="µg/l",
        max_daily_increase=6.0,
        source_name="Fauna Marin Elementals Trace",
        source_url="https://www.faunamarin.de/wp-content/uploads/2021/04/FM_HTU_ELEMENTALS_TRACE_DE_NEU_291121.pdf",
    ),
    "nickel": _rule(
        name="Nickel",
        product="Fauna Marin Elementals Trace Ni",
        kind="single_element",
        dose_amount=1.0,
        dose_unit="ml",
        increase=4.0,
        unit="µg/l",
        max_daily_increase=4.0,
        source_name="Fauna Marin Elementals Trace",
        source_url="https://www.faunamarin.de/wp-content/uploads/2021/04/FM_HTU_ELEMENTALS_TRACE_DE_NEU_291121.pdf",
    ),
    "vanadium": _rule(
        name="Vanadium",
        product="Fauna Marin Elementals Trace V",
        kind="single_element",
        dose_amount=1.0,
        dose_unit="ml",
        increase=5.0,
        unit="µg/l",
        max_daily_increase=2.0,
        source_name="Fauna Marin Elementals Trace",
        source_url="https://www.faunamarin.de/elementals-trace-v/",
    ),
    "zink": _rule(
        name="Zink",
        product="Fauna Marin Elementals Trace Zn",
        kind="single_element",
        dose_amount=1.0,
        dose_unit="ml",
        increase=10.0,
        unit="µg/l",
        max_daily_increase=3.0,
        source_name="Fauna Marin Elementals Trace",
        source_url="https://www.faunamarin.de/elementals-trace-zn/",
    ),
    "rubidium": _rule(
        name="Rubidium",
        product="Fauna Marin Elementals Trace Rb",
        kind="single_element",
        dose_amount=1.0,
        dose_unit="ml",
        increase=5.0,
        unit="µg/l",
        max_daily_increase=25.0,
        source_name="Fauna Marin Elementals Trace",
        source_url="https://www.faunamarin.de/elementals-trace-rb/",
    ),
}


# ---------------------------------------------------------------------------
# ATI Essentials pro + ATI ICP Elements
# ---------------------------------------------------------------------------

_ATI_ICP_ELEMENT_RULES: dict[str, dict[str, Any]] = {
    "barium": _rule(
        name="Barium",
        product="ATI ICP Element Barium",
        kind="single_element",
        dose_amount=1.0,
        dose_unit="ml",
        increase=1.0,
        unit="µg/l",
        source_name="ATI ICP Elements",
        source_url="https://atiaquaristik.com/de/reeflab/icp-elements/",
    ),
    "bor": _rule(
        name="Bor",
        product="ATI ICP Element Bor",
        kind="single_element",
        dose_amount=100.0,
        dose_unit="ml",
        increase=0.5,
        unit="mg/l",
        source_name="ATI ICP Elements",
        source_url="https://atiaquaristik.com/de/reeflab/icp-elements/",
    ),
    "bromid": _rule(
        name="Bromid",
        product="ATI ICP Element Brom",
        kind="single_element",
        dose_amount=1.0,
        dose_unit="ml",
        increase=1.0,
        unit="mg/l",
        source_name="ATI ICP Elements",
        source_url="https://atiaquaristik.com/de/reeflab/icp-elements/",
    ),
    "calcium": _rule(
        name="Calcium",
        product="ATI ICP Element Calcium",
        kind="core_correction",
        dose_amount=1.0,
        dose_unit="ml",
        increase=2.0,
        unit="mg/l",
        source_name="ATI ICP Elements",
        source_url="https://atiaquaristik.com/de/reeflab/icp-elements/",
    ),
    "fluorid": _rule(
        name="Fluorid",
        product="ATI ICP Element Fluor",
        kind="single_element",
        dose_amount=10.0,
        dose_unit="ml",
        increase=0.2,
        unit="mg/l",
        source_name="ATI ICP Elements",
        source_url="https://atiaquaristik.com/de/reeflab/icp-elements/",
    ),
    "iod": _rule(
        name="Iod",
        product="ATI ICP Element Jod",
        kind="single_element",
        dose_amount=1.0,
        dose_unit="ml",
        increase=10.0,
        unit="µg/l",
        source_name="ATI ICP Elements",
        source_url="https://atiaquaristik.com/de/reeflab/icp-elements/",
    ),
    "kalium": _rule(
        name="Kalium",
        product="ATI ICP Element Kalium",
        kind="single_element",
        dose_amount=1.0,
        dose_unit="ml",
        increase=1.0,
        unit="mg/l",
        source_name="ATI ICP Elements",
        source_url="https://atiaquaristik.com/de/reeflab/icp-elements/",
    ),
    "alkalinitaet": _rule(
        name="Alkalinität",
        product="ATI ICP Element Karbonathärte",
        kind="core_correction",
        dose_amount=1.0,
        dose_unit="ml",
        increase=0.1,
        unit="dKH",
        source_name="ATI ICP Elements",
        source_url="https://atiaquaristik.com/de/reeflab/icp-elements/",
    ),
    "kupfer": _rule(
        name="Kupfer",
        product="ATI ICP Element Kupfer",
        kind="single_element",
        dose_amount=1.0,
        dose_unit="ml",
        increase=1.0,
        unit="µg/l",
        source_name="ATI ICP Elements",
        source_url="https://atiaquaristik.com/de/reeflab/icp-elements/",
    ),
    "lithium": _rule(
        name="Lithium",
        product="ATI ICP Element Lithium",
        kind="single_element",
        dose_amount=1.0,
        dose_unit="ml",
        increase=15.0,
        unit="µg/l",
        source_name="ATI ICP Elements",
        source_url="https://atiaquaristik.com/de/reeflab/icp-elements/",
    ),
    "magnesium": _rule(
        name="Magnesium",
        product="ATI ICP Element Magnesium",
        kind="core_correction",
        dose_amount=1.0,
        dose_unit="ml",
        increase=1.0,
        unit="mg/l",
        source_name="ATI ICP Elements",
        source_url="https://atiaquaristik.com/de/reeflab/icp-elements/",
    ),
    "mangan": _rule(
        name="Mangan",
        product="ATI ICP Element Mangan",
        kind="single_element",
        dose_amount=1.0,
        dose_unit="ml",
        increase=4.0,
        unit="µg/l",
        source_name="ATI ICP Elements",
        source_url="https://atiaquaristik.com/de/reeflab/icp-elements/",
    ),
    "molybdaen": _rule(
        name="Molybdän",
        product="ATI ICP Element Molybdän",
        kind="single_element",
        dose_amount=1.0,
        dose_unit="ml",
        increase=6.0,
        unit="µg/l",
        source_name="ATI ICP Elements",
        source_url="https://atiaquaristik.com/de/reeflab/icp-elements/",
    ),
    "nickel": _rule(
        name="Nickel",
        product="ATI ICP Element Nickel",
        kind="single_element",
        dose_amount=1.0,
        dose_unit="ml",
        increase=3.0,
        unit="µg/l",
        source_name="ATI ICP Elements",
        source_url="https://atiaquaristik.com/de/reeflab/icp-elements/",
    ),
    "rubidium": _rule(
        name="Rubidium",
        product="ATI ICP Element Rubidium",
        kind="single_element",
        dose_amount=1.0,
        dose_unit="ml",
        increase=5.0,
        unit="µg/l",
        source_name="ATI ICP Elements",
        source_url="https://atiaquaristik.com/de/reeflab/icp-elements/",
    ),
    "schwefel": _rule(
        name="Schwefel",
        product="ATI ICP Element Schwefel",
        kind="single_element",
        dose_amount=1.0,
        dose_unit="g",
        increase=2.25,
        unit="mg/l",
        source_name="ATI ICP Elements",
        source_url="https://atiaquaristik.com/de/reeflab/icp-elements/",
    ),
    "selen": _rule(
        name="Selen",
        product="ATI ICP Element Selen",
        kind="single_element",
        dose_amount=1.0,
        dose_unit="ml",
        increase=0.5,
        unit="µg/l",
        source_name="ATI ICP Elements",
        source_url="https://atiaquaristik.com/de/reeflab/icp-elements/",
    ),
    "strontium": _rule(
        name="Strontium",
        product="ATI ICP Element Strontium",
        kind="single_element",
        dose_amount=1.0,
        dose_unit="ml",
        increase=0.2,
        unit="mg/l",
        source_name="ATI ICP Elements",
        source_url="https://atiaquaristik.com/de/reeflab/icp-elements/",
    ),
    "vanadium": _rule(
        name="Vanadium",
        product="ATI ICP Element Vanadium",
        kind="single_element",
        dose_amount=1.0,
        dose_unit="ml",
        increase=5.0,
        unit="µg/l",
        source_name="ATI ICP Elements",
        source_url="https://atiaquaristik.com/de/reeflab/icp-elements/",
    ),
    "zink": _rule(
        name="Zink",
        product="ATI ICP Element Zink",
        kind="single_element",
        dose_amount=1.0,
        dose_unit="ml",
        increase=10.0,
        unit="µg/l",
        source_name="ATI ICP Elements",
        source_url="https://atiaquaristik.com/de/reeflab/icp-elements/",
    ),
    "chrom": _rule(
        name="Chrom",
        product="ATI ICP Element Chrom",
        kind="single_element",
        dose_amount=1.0,
        dose_unit="ml",
        increase=1.0,
        unit="µg/l",
        source_name="ATI ICP Elements",
        source_url="https://atiaquaristik.com/de/reeflab/icp-elements/",
    ),
    "cobalt": _rule(
        name="Cobalt",
        product="ATI ICP Element Cobalt",
        kind="single_element",
        dose_amount=1.0,
        dose_unit="ml",
        increase=4.0,
        unit="µg/l",
        source_name="ATI ICP Elements",
        source_url="https://atiaquaristik.com/de/reeflab/icp-elements/",
    ),
    "eisen": _rule(
        name="Eisen",
        product="ATI ICP Element Eisen",
        kind="single_element",
        dose_amount=1.0,
        dose_unit="ml",
        increase=4.0,
        unit="µg/l",
        source_name="ATI ICP Elements",
        source_url="https://atiaquaristik.com/de/reeflab/icp-elements/",
    ),
}


# ---------------------------------------------------------------------------
# Oceamo DUO + Single Elements
# ---------------------------------------------------------------------------

_OCEAMO_DUO_RULES: dict[str, dict[str, Any]] = {
    "alkalinitaet": _rule(
        name="Alkalinität",
        product="Oceamo DUO KH",
        kind="core",
        dose_amount=10.0,
        dose_unit="ml",
        increase=1.0,
        unit="dKH",
        source_name="Oceamo DUO",
        source_url="https://oceamo.com/duo/",
    ),
}

_OCEAMO_SINGLE_ELEMENT_RULES: dict[str, dict[str, Any]] = {
    "barium": _rule(
        name="Barium",
        product="Oceamo Single Elements Barium",
        kind="single_element",
        dose_amount=1.0,
        dose_unit="ml",
        increase=2.0,
        unit="µg/l",
        max_daily_increase=4.0,
        source_name="Oceamo Single Elements",
        source_url="https://oceamo.com/product-page/single-elements-barium-250-ml/",
    ),
    "bor": _rule(
        name="Bor",
        product="Oceamo Single Elements Bor",
        kind="single_element",
        dose_amount=100.0,
        dose_unit="ml",
        increase=0.5,
        unit="mg/l",
        max_daily_increase=0.5,
        source_name="Oceamo Single Elements",
        source_url="https://oceamo.com/product-page/single-elements-bor/",
    ),
    "fluorid": _rule(
        name="Fluorid",
        product="Oceamo Single Elements Fluorid",
        kind="single_element",
        dose_amount=10.0,
        dose_unit="ml",
        increase=0.1,
        unit="mg/l",
        max_daily_increase=0.1,
        source_name="Oceamo Single Elements",
        source_url="https://oceamo.com/product-page/single-elements-fluorid/",
    ),
    "iod": _rule(
        name="Iod",
        product="Oceamo Single Elements Iod",
        kind="single_element",
        dose_amount=1.0,
        dose_unit="ml",
        increase=50.0,
        unit="µg/l",
        source_name="Oceamo Single Elements",
        source_url="https://oceamo.com/product-page/oceamo-iod-supplement/",
    ),
    "kalium": _rule(
        name="Kalium",
        product="Oceamo Single Elements Kalium",
        kind="single_element",
        dose_amount=1.0,
        dose_unit="ml",
        increase=1.5,
        unit="mg/l",
        max_daily_increase=6.0,
        source_name="Oceamo Single Elements",
        source_url="https://oceamo.com/product-page/single-elements-kalium/",
    ),
    "mangan": _rule(
        name="Mangan",
        product="Oceamo Single Elements Mangan",
        kind="single_element",
        dose_amount=1.0,
        dose_unit="ml",
        increase=2.0,
        unit="µg/l",
        max_daily_increase=1.0,
        source_name="Oceamo Single Elements",
        source_url="https://oceamo.com/product-page/single-elements-mangan/",
    ),
    "molybdaen": _rule(
        name="Molybdän",
        product="Oceamo Single Elements Molybdän",
        kind="single_element",
        dose_amount=1.0,
        dose_unit="ml",
        increase=2.0,
        unit="µg/l",
        max_daily_increase=2.0,
        source_name="Oceamo Single Elements",
        source_url="https://oceamo.com/product-page/single-elements-molybdaen-250-ml/",
    ),
    "rubidium": _rule(
        name="Rubidium",
        product="Oceamo Single Elements Rubidium",
        kind="single_element",
        dose_amount=1.0,
        dose_unit="ml",
        increase=5.0,
        unit="µg/l",
        max_daily_increase=25.0,
        source_name="Oceamo Single Elements",
        source_url="https://oceamo.com/product-page/single-elements-rubidium/",
    ),
    "selen": _rule(
        name="Selen",
        product="Oceamo Single Elements Selen",
        kind="single_element",
        dose_amount=1.0,
        dose_unit="ml",
        increase=0.05,
        unit="µg/l",
        max_daily_increase=0.05,
        requires_report_type="reef_icp_ms",
        source_name="Oceamo Single Elements",
        source_url="https://oceamo.com/product-page/single-elements-selen-1000-ml/",
    ),
    "strontium": _rule(
        name="Strontium",
        product="Oceamo Single Elements Strontium",
        kind="single_element",
        dose_amount=10.0,
        dose_unit="ml",
        increase=1.0,
        unit="mg/l",
        max_daily_increase=1.0,
        source_name="Oceamo Single Elements",
        source_url="https://oceamo.com/product-page/single-elements-strontium/",
    ),
}


_SYSTEM_RULES: dict[str, dict[str, dict[str, Any]]] = {
    SUPPLY_SYSTEM_FAUNA_MARIN_BALLING_LIGHT: {
        **_FAUNA_BALLING_LIGHT_RULES,
        **_FAUNA_ELEMENTALS_RULES,
    },
    SUPPLY_SYSTEM_ATI_ESSENTIALS_PRO: _ATI_ICP_ELEMENT_RULES,
    SUPPLY_SYSTEM_OCEAMO_DUO: {
        **_OCEAMO_DUO_RULES,
        **_OCEAMO_SINGLE_ELEMENT_RULES,
    },
}

_SYSTEM_MAINTENANCE_NOTE = {
    SUPPLY_SYSTEM_FAUNA_MARIN_BALLING_LIGHT: "balling_light_consumption",
    SUPPLY_SYSTEM_ATI_ESSENTIALS_PRO: "ati_essentials_consumption",
    SUPPLY_SYSTEM_OCEAMO_DUO: "oceamo_duo_consumption",
    SUPPLY_SYSTEM_TRITON_METHOD: "triton_core7_consumption",
}

_TRITON_CALCULATOR_URL = (
    "https://www.triton.de/toolkit/rechner-fuer-spurenelementergaenzung"
)
_TRITON_CORE7_URL = "https://www.triton.de/toolkit/core7-verbrauchsberechner"


def _target_relation(
    measurement: dict[str, Any],
) -> tuple[str | None, float | None]:
    """Return low/high relation and the nearest target boundary."""
    current = measurement.get("value")
    target = measurement.get("target")

    if not isinstance(current, (int, float)) or not isinstance(target, dict):
        return None, None

    target_type = target.get("type")

    if target_type == "exact":
        desired = target.get("value")
        if not isinstance(desired, (int, float)):
            return None, None
        if current < desired:
            return "low", float(desired)
        if current > desired:
            return "high", float(desired)
        return "ok", float(desired)

    if target_type == "range":
        minimum = target.get("min")
        maximum = target.get("max")
        if not isinstance(minimum, (int, float)) or not isinstance(
            maximum, (int, float)
        ):
            return None, None
        if current < minimum:
            return "low", float(minimum)
        if current > maximum:
            return "high", float(maximum)
        return "ok", float(current)

    if target_type == "lower_limit":
        minimum = target.get("min")
        if not isinstance(minimum, (int, float)):
            return None, None
        if current < minimum:
            return "low", float(minimum)
        return "ok", float(current)

    if target_type == "upper_limit":
        maximum = target.get("max")
        if not isinstance(maximum, (int, float)):
            return None, None
        if current > maximum:
            return "high", float(maximum)
        return "ok", float(current)

    return None, None


def _measurement_needs_action(measurement: dict[str, Any]) -> bool:
    """Return whether the provider marked this measurement for attention."""
    severity = str((measurement.get("status") or {}).get("severity", "unknown"))
    return severity in {"warning", "critical"}


def _report_type_restriction_notice(
    measurement: dict[str, Any],
    rule: dict[str, Any],
    report_type: str | None,
) -> dict[str, Any] | None:
    """Return an informational item when a low correction needs another method."""
    required_report_type = rule.get("requires_report_type")
    if (
        not required_report_type
        or report_type == required_report_type
        or not _measurement_needs_action(measurement)
    ):
        return None

    relation, target_value = _target_relation(measurement)
    direction = str((measurement.get("status") or {}).get("direction") or "")

    # The restriction only blocks an upward correction. An elevated result can
    # still safely produce the generic "reduce or pause" guidance because no
    # supplement dose is calculated from that measurement.
    if relation != "low" and not (relation is None and direction == "low"):
        return None

    current = measurement.get("value")
    return {
        "key": str(measurement.get("key", "")),
        "name": rule["name"],
        "product": rule["product"],
        "solution": rule.get("solution"),
        "kind": rule["kind"],
        "current": float(current) if isinstance(current, (int, float)) else None,
        "target": float(target_value) if target_value is not None else None,
        "unit": measurement.get("unit") or rule["unit"],
        "severity": str(
            (measurement.get("status") or {}).get("severity", "unknown")
        ),
        "action": "requires_icp_ms",
        "required_report_type": str(required_report_type),
        "source_name": rule["source_name"],
        "source_url": rule["source_url"],
    }


def _generic_correction(
    measurement: dict[str, Any],
    volume_l: float,
    rule: dict[str, Any],
) -> dict[str, Any] | None:
    """Calculate a correction from one published manufacturer strength."""
    if not _measurement_needs_action(measurement):
        return None

    current = measurement.get("value")
    if not isinstance(current, (int, float)):
        return None

    measurement_unit = measurement.get("unit")
    if measurement_unit != rule["unit"]:
        # Cross-provider parsers normalize known comparable analytes. Refuse
        # to calculate if a future parser supplies an incompatible unit.
        return None

    relation, target_value = _target_relation(measurement)
    if relation not in {"low", "high"} or target_value is None:
        return None

    common = {
        "key": str(measurement.get("key", "")),
        "name": rule["name"],
        "product": rule["product"],
        "solution": rule.get("solution"),
        "kind": rule["kind"],
        "current": float(current),
        "target": float(target_value),
        "unit": measurement_unit,
        "severity": str(
            (measurement.get("status") or {}).get("severity", "unknown")
        ),
        "source_name": rule["source_name"],
        "source_url": rule["source_url"],
    }

    if relation == "high":
        return {
            **common,
            "action": "reduce_or_pause",
            "dose_amount": 0.0,
            "dose_unit": rule["dose_unit"],
        }

    delta = float(target_value) - float(current)
    if delta <= 0:
        return None

    total_dose = (
        delta
        / float(rule["increase"])
        * float(rule["dose_amount"])
        * (volume_l / 100.0)
    )

    item: dict[str, Any] = {
        **common,
        "action": "correction_dose",
        "delta": delta,
        "dose_amount": round(total_dose, 3),
        "dose_unit": rule["dose_unit"],
        "manufacturer_increase": float(rule["increase"]),
        "manufacturer_increase_unit": rule["unit"],
        "manufacturer_reference_dose": float(rule["dose_amount"]),
        "manufacturer_reference_volume_l": 100.0,
    }

    max_daily_increase = rule.get("max_daily_increase")
    if isinstance(max_daily_increase, (int, float)) and max_daily_increase > 0:
        days = max(1, ceil(delta / float(max_daily_increase)))
        item.update(
            {
                "max_daily_increase": float(max_daily_increase),
                "split_days": days,
                "daily_dose_amount": round(total_dose / days, 3),
            }
        )
    else:
        item["daily_limit_known"] = False

    return item


def _triton_guidance_items(
    measurements: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return safe TRITON guidance without copying an unpublished formula."""
    supported_single_elements = {
        "vanadium",
        "chrom",
        "eisen",
        "mangan",
        "lithium",
        "cobalt",
        "iod",
        "molybdaen",
        "zink",
        "nickel",
        "fluorid",
        "bromid",
        "bor",
        "strontium",
        "kalium",
        "schwefel",
        "calcium",
        "magnesium",
    }

    items: list[dict[str, Any]] = []
    for measurement in measurements:
        key = str(measurement.get("key", ""))
        if key not in supported_single_elements:
            continue
        if not _measurement_needs_action(measurement):
            continue

        current = measurement.get("value")
        relation, target_value = _target_relation(measurement)
        if not isinstance(current, (int, float)):
            continue
        if relation not in {"low", "high"} or target_value is None:
            continue

        if relation == "high":
            items.append(
                {
                    "key": key,
                    "name": measurement.get("name") or key,
                    "product": "TRITON Core7 / Single Element",
                    "kind": "single_element",
                    "current": float(current),
                    "target": float(target_value),
                    "unit": measurement.get("unit"),
                    "severity": str(
                        (measurement.get("status") or {}).get(
                            "severity", "unknown"
                        )
                    ),
                    "action": "reduce_or_pause",
                    "dose_amount": 0.0,
                    "dose_unit": "ml",
                    "source_name": "TRITON",
                    "source_url": _TRITON_CALCULATOR_URL,
                }
            )
            continue

        items.append(
            {
                "key": key,
                "name": measurement.get("name") or key,
                "product": f"TRITON {measurement.get('name') or key} Single Element",
                "kind": "single_element",
                "current": float(current),
                "target": float(target_value),
                "unit": measurement.get("unit"),
                "severity": str(
                    (measurement.get("status") or {}).get(
                        "severity", "unknown"
                    )
                ),
                "action": "official_calculator",
                "source_name": "TRITON Single Element Calculator",
                "source_url": _TRITON_CALCULATOR_URL,
            }
        )

    return items


def build_supply_recommendations(
    supply_system: str | None,
    aquarium_volume_l: Any,
    measurements: list[dict[str, Any]],
    report_type: str | None = None,
) -> dict[str, Any] | None:
    """Build provider-independent recommendations for the selected system."""
    if not supply_system or supply_system == "none":
        return None

    try:
        volume_l = float(aquarium_volume_l)
    except (TypeError, ValueError):
        return {
            "system": supply_system,
            "system_name": SUPPLY_SYSTEM_NAMES.get(
                supply_system, supply_system
            ),
            "supported": False,
            "reason": "missing_volume",
            "items": [],
        }

    if volume_l <= 0:
        return {
            "system": supply_system,
            "system_name": SUPPLY_SYSTEM_NAMES.get(
                supply_system, supply_system
            ),
            "supported": False,
            "reason": "missing_volume",
            "items": [],
        }

    if supply_system == SUPPLY_SYSTEM_TRITON_METHOD:
        return {
            "system": supply_system,
            "system_name": SUPPLY_SYSTEM_NAMES.get(
                supply_system, supply_system
            ),
            "supported": True,
            "volume_l": volume_l,
            "mode": "official_calculator",
            "items": _triton_guidance_items(measurements),
            "maintenance_note": _SYSTEM_MAINTENANCE_NOTE[supply_system],
            "maintenance_source_url": _TRITON_CORE7_URL,
            "trace_elements_implemented": True,
            "numeric_trace_calculation": False,
        }

    rules = _SYSTEM_RULES.get(supply_system)
    if rules is None:
        return {
            "system": supply_system,
            "system_name": SUPPLY_SYSTEM_NAMES.get(
                supply_system, supply_system
            ),
            "supported": False,
            "reason": "system_not_implemented",
            "volume_l": volume_l,
            "items": [],
        }

    items: list[dict[str, Any]] = []
    for measurement in measurements:
        rule = rules.get(str(measurement.get("key", "")))
        if rule is None:
            continue

        item = _report_type_restriction_notice(
            measurement,
            rule,
            report_type,
        )
        if item is None:
            item = _generic_correction(
                measurement,
                volume_l,
                rule,
            )
        if item is not None:
            items.append(item)

    return {
        "system": supply_system,
        "system_name": SUPPLY_SYSTEM_NAMES.get(
            supply_system, supply_system
        ),
        "supported": True,
        "volume_l": volume_l,
        "mode": "calculated",
        "items": items,
        "calculated_keys": sorted(rules),
        "maintenance_note": _SYSTEM_MAINTENANCE_NOTE.get(supply_system),
        "maintenance_requires_consumption": True,
        "trace_elements_implemented": True,
        "numeric_trace_calculation": True,
    }
