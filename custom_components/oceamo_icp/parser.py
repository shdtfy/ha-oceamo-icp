"""PDF parsers for Reef ICP providers."""

from __future__ import annotations

from datetime import datetime
import hashlib
from pathlib import Path
import re
from typing import Any
import unicodedata

from pypdf import PdfReader
from pypdf.generic import ContentStream

PROVIDER_OCEAMO = "oceamo"
PROVIDER_FAUNA_MARIN = "fauna_marin"

PROVIDER_NAMES = {
    PROVIDER_OCEAMO: "Oceamo",
    PROVIDER_FAUNA_MARIN: "Fauna Marin",
}


class IcpParseError(ValueError):
    """Raised when an ICP report cannot be parsed."""


class UnsupportedIcpProviderError(IcpParseError):
    """Raised when Reef ICP cannot identify a supported provider."""


# Backward-compatible exception name for existing imports/tests.
OceamoParseError = IcpParseError


OCEAMO_CATEGORY_HEADINGS = {
    "Grundparameter": "basic",
    "Mengenelemente": "major_elements",
    "Spurenelemente": "trace_elements",
    "Schadstoffe": "pollutants",
    "Nährstoffe": "nutrients",
    "Osmose-Check": "osmosis",
}

# MD5 hashes of the decoded 15x15 status artwork embedded in the tested
# classic Oceamo PDF format. Unknown artwork is deliberately not guessed.
_OCEAMO_STATUS_IMAGE_HASHES: dict[str, dict[str, str | None]] = {
    "3346ccd496a836a16d810b48ef46ffb9": {
        "severity": "ok",
        "direction": None,
    },
    "82766212f5f1f90277061b6ade0004c7": {
        "severity": "critical",
        "direction": "high",
    },
    "4dd707d862ed26bdee6a3119fcbaf1f1": {
        "severity": "critical",
        "direction": "low",
    },
    "c890e5b25e13d2fbe08b73348bf632fe": {
        "severity": "warning",
        "direction": "high",
    },
    "7816fa4e75cd34b2df783e0253d4edb6": {
        "severity": "warning",
        "direction": "low",
    },
}

_UNIT_PATTERN = r"(?:psu|dKH|mg/l|µg/l|μg/l|ng/l|mmol/l|µmol/l|μmol/l)"

_OCEAMO_ROW_RE = re.compile(
    rf"^(?P<name>.+?)\s+"
    rf"(?P<value>n\.n\.|n\.b\.|-?\d+(?:[.,]\d+)?)\s+"
    rf"(?:(?P<unit>{_UNIT_PATTERN})\s+)?"
    rf"(?P<target>"
    rf"n\.n\.|n\.b\.|"
    rf"<\s*-?\d+(?:[.,]\d+)?|"
    rf">\s*-?\d+(?:[.,]\d+)?|"
    rf"-?\d+(?:[.,]\d+)?(?:\s*-\s*-?\d+(?:[.,]\d+)?)?"
    rf")"
    rf"(?:\s+(?P<target_unit>{_UNIT_PATTERN}))?\s*$"
)

_FAUNA_ROW_RE = re.compile(
    r"^\s*"
    r"(?P<name>[A-Za-zÄÖÜäöüß]+(?:\s+\([^)]*\))?)\s+"
    r"(?P<symbol>[A-Z][a-z]?)\s+"
    r"(?P<value>n\.n\.|n\.g\.|[<>]?\s*-?\d+(?:[.,]\d+)?)\s+"
    r"(?P<rest>.+?)\s*$"
)

_NUMBER = r"-?\d+(?:[.,]\d+)?"
_FAUNA_TARGET_PREFIX_RE = re.compile(
    rf"^\s*(?P<target>"
    rf"<\s*{_NUMBER}|"
    rf">\s*{_NUMBER}|"
    rf"{_NUMBER}\s*-\s*{_NUMBER}(?:\s*-\s*{_NUMBER})?|"
    rf"{_NUMBER}"
    rf")(?P<tail>.*)$"
)

_FAUNA_TOTAL_PHOSPHATE_RE = re.compile(
    rf"^\s*Gesamtphosphat\s+\(errechnet\).*?"
    rf"PO\s+3-\s+(?P<value>{_NUMBER})\s+"
    rf"(?P<min>{_NUMBER})\s*-\s*(?P<max>{_NUMBER})\s*$"
)

# Canonical analyte mapping. Keys and categories deliberately match the
# classic Oceamo parser where the same analyte is comparable so historic
# points from different providers share one Home Assistant statistic.
#
# Tuple: (key, display name, category, normalized unit, value scale)
_FAUNA_ANALYTES: dict[str, tuple[str, str, str, str, float]] = {
    "Na": ("natrium", "Natrium", "major_elements", "mg/l", 1.0),
    "S": ("schwefel", "Schwefel", "major_elements", "mg/l", 1.0),
    "K": ("kalium", "Kalium", "major_elements", "mg/l", 1.0),
    "B": ("bor", "Bor", "major_elements", "mg/l", 1.0),
    "Mg": ("magnesium", "Magnesium", "major_elements", "mg/l", 1.0),
    "Ca": ("calcium", "Calcium", "major_elements", "mg/l", 1.0),
    "Sr": ("strontium", "Strontium", "major_elements", "mg/l", 1.0),
    # Fauna Marin reports iodine in mg/l; Oceamo uses µg/l.
    "I": ("iod", "Iod", "trace_elements", "µg/l", 1000.0),
    # Fauna Marin labels this as Brom; the comparable Oceamo analyte is Bromid.
    "Br": ("bromid", "Bromid", "major_elements", "mg/l", 1.0),
    # Fauna Marin reports ICP phosphorus in mg/l; Oceamo total phosphorus uses µg/l.
    "P": (
        "gesamtphosphor_icp",
        "Gesamtphosphor (ICP)",
        "nutrients",
        "µg/l",
        1000.0,
    ),
    # Fauna Marin reports silicon in mg/l; Oceamo uses µg/l.
    "Si": ("silicium", "Silicium", "nutrients", "µg/l", 1000.0),
    "Zn": ("zink", "Zink", "trace_elements", "µg/l", 1.0),
    "V": ("vanadium", "Vanadium", "trace_elements", "µg/l", 1.0),
    "Cu": ("kupfer", "Kupfer", "trace_elements", "µg/l", 1.0),
    "Ni": ("nickel", "Nickel", "trace_elements", "µg/l", 1.0),
    "Mn": ("mangan", "Mangan", "trace_elements", "µg/l", 1.0),
    "Mo": ("molybdaen", "Molybdän", "trace_elements", "µg/l", 1.0),
    "Fe": ("eisen", "Eisen", "trace_elements", "µg/l", 1.0),
    "Cr": ("chrom", "Chrom", "trace_elements", "µg/l", 1.0),
    "Co": ("cobalt", "Cobalt", "trace_elements", "µg/l", 1.0),
    "Li": ("lithium", "Lithium", "trace_elements", "µg/l", 1.0),
    "Ba": ("barium", "Barium", "trace_elements", "µg/l", 1.0),
    "Al": ("aluminium", "Aluminium", "pollutants", "µg/l", 1.0),
    "Sb": ("antimon", "Antimon", "pollutants", "µg/l", 1.0),
    "Sn": ("zinn", "Zinn", "trace_elements", "µg/l", 1.0),
    "Be": ("beryllium", "Beryllium", "pollutants", "µg/l", 1.0),
    "Se": ("selen", "Selen", "trace_elements", "µg/l", 1.0),
    "Ag": ("silber", "Silber", "pollutants", "µg/l", 1.0),
    "W": ("wolfram", "Wolfram", "pollutants", "µg/l", 1.0),
    "La": ("lanthan", "Lanthan", "pollutants", "µg/l", 1.0),
    "Ti": ("titan", "Titan", "pollutants", "µg/l", 1.0),
    "Zr": ("zirkonium", "Zirkonium", "pollutants", "µg/l", 1.0),
    "As": ("arsen", "Arsen", "pollutants", "µg/l", 1.0),
    "Cd": ("cadmium", "Cadmium", "pollutants", "µg/l", 1.0),
    "Hg": ("quecksilber", "Quecksilber", "pollutants", "µg/l", 1.0),
    "Pb": ("blei", "Blei", "pollutants", "µg/l", 1.0),
}


def _decimal(value: str) -> float:
    """Convert a German/English decimal string to float."""
    return float(value.replace(",", "."))


def _normalized_number(value: float) -> str:
    """Return a compact decimal representation for normalized source values."""
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.9f}".rstrip("0").rstrip(".")


def _slug(value: str) -> str:
    """Create a stable ASCII key."""
    value = (
        value.replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("Ä", "Ae")
        .replace("Ö", "Oe")
        .replace("Ü", "Ue")
        .replace("ß", "ss")
    )
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_").lower()


def _parse_date(value: str) -> str:
    """Convert DD.MM.YYYY to ISO date."""
    return datetime.strptime(value, "%d.%m.%Y").date().isoformat()


def _parse_sample_datetime(value: str) -> str:
    """Convert Oceamo sample timestamp to an ISO local datetime string."""
    normalized = re.sub(r"\s+", " ", value.strip())
    return datetime.strptime(normalized, "%d.%m.%Y - %H:%M").isoformat()


def _date_at_noon(value: str) -> str:
    """Convert a date-only sample timestamp to a stable local noon datetime."""
    parsed = datetime.strptime(value, "%d.%m.%Y")
    return parsed.replace(hour=12).isoformat()


def _parse_target(raw: str) -> dict[str, Any]:
    """Parse Oceamo's ideal/target value representation."""
    normalized = raw.replace(" ", "")

    if normalized == "n.n.":
        return {"type": "not_detectable"}
    if normalized == "n.b.":
        return {"type": "not_determined"}
    if normalized.startswith("<"):
        return {"type": "upper_limit", "max": _decimal(normalized[1:])}
    if normalized.startswith(">"):
        return {"type": "lower_limit", "min": _decimal(normalized[1:])}

    range_match = re.fullmatch(
        r"(-?\d+(?:[.,]\d+)?)\s*-\s*(-?\d+(?:[.,]\d+)?)", raw
    )
    if range_match:
        return {
            "type": "range",
            "min": _decimal(range_match.group(1)),
            "max": _decimal(range_match.group(2)),
        }

    return {"type": "exact", "value": _decimal(normalized)}


def _parse_fauna_target(raw: str, scale: float = 1.0) -> dict[str, Any]:
    """Parse a Fauna Marin reference range, including its optional ideal value."""
    normalized = " ".join(raw.split())

    if normalized.startswith("<"):
        return {
            "type": "upper_limit",
            "max": _decimal(normalized[1:].strip()) * scale,
        }
    if normalized.startswith(">"):
        return {
            "type": "lower_limit",
            "min": _decimal(normalized[1:].strip()) * scale,
        }

    values = [_decimal(value) * scale for value in re.findall(_NUMBER, normalized)]
    if len(values) == 3:
        return {
            "type": "range",
            "min": values[0],
            "ideal": values[1],
            "max": values[2],
        }
    if len(values) == 2:
        return {
            "type": "range",
            "min": values[0],
            "max": values[1],
        }
    if len(values) == 1:
        return {"type": "exact", "value": values[0]}

    return {"type": "unknown", "raw": normalized}


def _status_from_reference(
    value: float | None,
    raw_value: str,
    target: dict[str, Any],
) -> dict[str, str | None]:
    """Derive a conservative status from Fauna Marin's published reference range.

    Fauna Marin does not provide Oceamo-style critical/warning artwork in this
    report format. Values outside the supplied reference range are therefore
    mapped to warning, never to critical.
    """
    target_type = target.get("type")

    if value is None:
        if raw_value == "n.g.":
            return {"severity": "unknown", "direction": None}
        if raw_value == "n.n." and target_type in {
            "upper_limit",
            "not_detectable",
        }:
            return {"severity": "ok", "direction": None}
        if raw_value == "n.n." and target_type in {
            "range",
            "lower_limit",
            "exact",
        }:
            return {"severity": "warning", "direction": "low"}
        return {"severity": "unknown", "direction": None}

    if target_type == "range":
        minimum = target.get("min")
        maximum = target.get("max")
        if isinstance(minimum, (int, float)) and value < minimum:
            return {"severity": "warning", "direction": "low"}
        if isinstance(maximum, (int, float)) and value > maximum:
            return {"severity": "warning", "direction": "high"}
        return {"severity": "ok", "direction": None}

    if target_type == "upper_limit":
        maximum = target.get("max")
        if isinstance(maximum, (int, float)) and value > maximum:
            return {"severity": "warning", "direction": "high"}
        return {"severity": "ok", "direction": None}

    if target_type == "lower_limit":
        minimum = target.get("min")
        if isinstance(minimum, (int, float)) and value < minimum:
            return {"severity": "warning", "direction": "low"}
        return {"severity": "ok", "direction": None}

    if target_type == "exact":
        # An exact value without a provider tolerance cannot safely be turned
        # into a warning threshold.
        return {"severity": "unknown", "direction": None}

    return {"severity": "unknown", "direction": None}


def _parse_oceamo_measurement_line(
    line: str, category: str
) -> dict[str, Any] | None:
    """Parse one Oceamo table row."""
    normalized = " ".join(line.split())
    match = _OCEAMO_ROW_RE.match(normalized)
    if not match:
        return None

    raw_value = match.group("value")
    unit = match.group("unit") or match.group("target_unit")
    if unit is not None:
        unit = unit.replace("μ", "µ")

    measurement: dict[str, Any] = {
        "key": _slug(match.group("name")),
        "name": match.group("name"),
        "category": category,
        "raw_value": raw_value,
        "unit": unit,
        "target": _parse_target(match.group("target")),
        "provider": PROVIDER_OCEAMO,
        "provider_name": PROVIDER_NAMES[PROVIDER_OCEAMO],
    }

    if raw_value == "n.n.":
        measurement.update(
            {
                "value": None,
                "detected": False,
                "determined": True,
            }
        )
    elif raw_value == "n.b.":
        measurement.update(
            {
                "value": None,
                "detected": None,
                "determined": False,
            }
        )
    else:
        measurement.update(
            {
                "value": _decimal(raw_value),
                "detected": True,
                "determined": True,
            }
        )

    return measurement


def _extract_oceamo_status_sequence(
    page: Any, reader: PdfReader
) -> list[dict[str, Any]]:
    """Extract known Oceamo status icons in drawing order."""
    resources = page.get("/Resources")
    if resources is None:
        return []

    xobjects_ref = resources.get("/XObject")
    if xobjects_ref is None:
        return []

    xobjects = xobjects_ref.get_object()
    statuses_by_name: dict[str, dict[str, Any]] = {}

    for name, reference in xobjects.items():
        obj = reference.get_object()
        if (
            obj.get("/Subtype") != "/Image"
            or obj.get("/Width") != 15
            or obj.get("/Height") != 15
        ):
            continue

        try:
            digest = hashlib.md5(obj.get_data()).hexdigest()  # noqa: S324
        except Exception:  # noqa: BLE001
            continue

        if status := _OCEAMO_STATUS_IMAGE_HASHES.get(digest):
            statuses_by_name[str(name)] = status

    if not statuses_by_name:
        return []

    try:
        content = ContentStream(page.get_contents(), reader)
    except Exception:  # noqa: BLE001
        return []

    result: list[dict[str, Any]] = []
    for operands, operator in content.operations:
        if operator != b"Do" or not operands:
            continue
        status = statuses_by_name.get(str(operands[0]))
        if status is not None:
            result.append(dict(status))

    return result


def _extract_oceamo_metadata(text: str) -> dict[str, Any]:
    """Extract Oceamo report metadata while omitting customer details."""
    metadata: dict[str, Any] = {
        "provider": PROVIDER_OCEAMO,
        "provider_name": PROVIDER_NAMES[PROVIDER_OCEAMO],
    }

    if match := re.search(r"Analysedatum:\s*(\d{2}\.\d{2}\.\d{4})", text):
        metadata["analysis_date"] = _parse_date(match.group(1))
    if match := re.search(r"Analysenummer:\s*([A-Za-z]{2}\d+)", text):
        metadata["analysis_number"] = match.group(1)
        metadata["provider_report_id"] = match.group(1)
    if match := re.search(
        r"Probennahme:\s*(\d{2}\.\d{2}\.\d{4}\s*-\s*\d{2}:\d{2})",
        text,
    ):
        metadata["sample_taken"] = _parse_sample_datetime(match.group(1))
    if match := re.search(r"Beckentyp:\s*(.+?)(?:\n|$)", text):
        metadata["tank_type"] = match.group(1).strip()

    return metadata


def _extract_oceamo_interpretation(text: str) -> str | None:
    """Extract Oceamo's interpretation section."""
    match = re.search(
        r"Interpretation\s+(.*?)\s+Produktempfehlungen",
        text,
        flags=re.DOTALL,
    )
    if not match:
        return None
    return " ".join(match.group(1).split())


def _extract_oceamo_product_recommendations(text: str) -> str | None:
    """Extract the Oceamo product recommendation block as source text."""
    match = re.search(
        r"Produktempfehlungen\s+(.*?)(?:Advanced Reef Chemistry|$)",
        text,
        flags=re.DOTALL,
    )
    if not match:
        return None
    value = " ".join(match.group(1).split())
    return value or None


def parse_oceamo_pdf(path: str | Path) -> dict[str, Any]:
    """Parse a classic Oceamo PDF report into normalized data."""
    try:
        reader = PdfReader(str(path))
    except Exception as err:  # noqa: BLE001
        raise IcpParseError("The uploaded file is not a readable PDF.") from err

    page_texts = [(page.extract_text() or "") for page in reader.pages]
    full_text = "\n".join(page_texts)

    if "Oceamo" not in full_text or "Analysebericht" not in full_text:
        raise IcpParseError("The PDF does not look like an Oceamo analysis report.")

    metadata = _extract_oceamo_metadata(full_text)
    measurements: list[dict[str, Any]] = []
    current_category: str | None = None

    for page, page_text in zip(reader.pages, page_texts, strict=True):
        page_measurements: list[dict[str, Any]] = []

        for raw_line in page_text.splitlines():
            line = " ".join(raw_line.split())
            if not line:
                continue

            if line == "Interpretation":
                break

            if line in OCEAMO_CATEGORY_HEADINGS:
                current_category = OCEAMO_CATEGORY_HEADINGS[line]
                continue

            if current_category is None:
                continue

            if measurement := _parse_oceamo_measurement_line(line, current_category):
                page_measurements.append(measurement)

        # The classic report draws one status icon per table row. Legend icons
        # are drawn after the data rows, so only consume as many as we parsed.
        page_statuses = _extract_oceamo_status_sequence(page, reader)
        for index, measurement in enumerate(page_measurements):
            if index < len(page_statuses):
                measurement["status"] = page_statuses[index]
            else:
                measurement["status"] = {
                    "severity": "unknown",
                    "direction": None,
                }

        measurements.extend(page_measurements)

    if not measurements:
        raise IcpParseError("No ICP measurements were found in the report.")

    if "analysis_number" not in metadata:
        raise IcpParseError("The analysis number could not be found.")
    if "analysis_date" not in metadata:
        raise IcpParseError("The analysis date could not be found.")

    return {
        "schema_version": 2,
        "provider": PROVIDER_OCEAMO,
        "provider_name": PROVIDER_NAMES[PROVIDER_OCEAMO],
        "metadata": metadata,
        "measurements": measurements,
        "interpretation": _extract_oceamo_interpretation(full_text),
        "product_recommendations": _extract_oceamo_product_recommendations(full_text),
    }


def _extract_fauna_metadata(layout_text: str) -> dict[str, Any]:
    """Extract Fauna Marin metadata from the one-page Reef ICP report."""
    metadata: dict[str, Any] = {
        "provider": PROVIDER_FAUNA_MARIN,
        "provider_name": PROVIDER_NAMES[PROVIDER_FAUNA_MARIN],
    }

    if match := re.search(r"Proben-ID:\s*([A-Za-z0-9-]+)", layout_text):
        metadata["analysis_number"] = match.group(1)
        metadata["provider_report_id"] = match.group(1)

    if match := re.search(r"Probenart:\s*(\S+)", layout_text):
        metadata["tank_type"] = match.group(1).strip()

    if match := re.search(
        r"Volumen Aquarium in Liter:\s*(\d+(?:[.,]\d+)?)",
        layout_text,
    ):
        metadata["aquarium_volume_l"] = _decimal(match.group(1))

    if match := re.search(
        r"Entnahmestelle:\s*(.+?)(?:\s{8,}|\n)",
        layout_text,
    ):
        metadata["sample_location"] = " ".join(match.group(1).split())

    if match := re.search(r"Entnahmedatum:\s*(\d{2}\.\d{2}\.\d{4})", layout_text):
        metadata["sample_taken"] = _date_at_noon(match.group(1))

    if match := re.search(r"Probeneingang:\s*(\d{2}\.\d{2}\.\d{4})", layout_text):
        metadata["analysis_date"] = _parse_date(match.group(1))
        metadata["received_date"] = metadata["analysis_date"]

    return metadata


def _parse_fauna_recommendation(tail: str) -> dict[str, Any] | None:
    """Parse Fauna Marin's row-level dosage or water-change recommendation."""
    normalized = " ".join(tail.split())
    if not normalized:
        return None

    if "Wasserwechsel" in normalized:
        product_match = re.search(r"(Elementals(?:\s+Trace)?\s+\S+.*)$", normalized)
        result: dict[str, Any] = {"type": "water_change"}
        if product_match:
            result["product"] = product_match.group(1).strip()
        return result

    match = re.match(
        rf"^(?P<amount>{_NUMBER})\s+(?P<days>\d+)\b(?P<rest>.*)$",
        normalized,
    )
    if not match:
        return None

    result = {
        "type": "dose",
        "amount_ml": _decimal(match.group("amount")),
        "days": int(match.group("days")),
    }
    product = match.group("rest").strip()
    if product:
        result["product"] = product
    return result


def _fauna_measurement_from_parts(
    *,
    symbol: str,
    raw_value: str,
    raw_target: str,
    recommendation_tail: str,
) -> dict[str, Any] | None:
    """Normalize one Fauna Marin analyte into the shared report model."""
    analyte = _FAUNA_ANALYTES.get(symbol)
    if analyte is None:
        return None

    key, name, category, unit, scale = analyte
    source_unit = "mg/l" if symbol in {
        "Na", "S", "K", "B", "Mg", "Ca", "Sr", "I", "Br", "P", "Si"
    } else "µg/l"

    raw_value = raw_value.replace(" ", "")
    target = _parse_fauna_target(raw_target, scale)

    value: float | None
    normalized_raw = raw_value
    detected: bool | None
    determined: bool

    if raw_value == "n.n.":
        value = None
        detected = False
        determined = True
    elif raw_value == "n.g.":
        value = None
        detected = None
        determined = False
    elif raw_value.startswith((">", "<")):
        # Fauna Marin documents qualified values such as "> 24" as bounds
        # outside the calibrated range. Keep them non-numeric for history
        # instead of pretending the bound is an exact measurement.
        qualifier = "greater_than" if raw_value.startswith(">") else "less_than"
        source_bound = _decimal(raw_value[1:].strip())
        value = None
        normalized_bound = source_bound * scale
        normalized_raw = f"{raw_value[0]}{_normalized_number(normalized_bound)}"
        detected = True
        determined = False
    else:
        source_value = _decimal(raw_value)
        value = source_value * scale
        normalized_raw = _normalized_number(value)
        detected = True
        determined = True

    measurement: dict[str, Any] = {
        "key": key,
        "name": name,
        "category": category,
        "raw_value": normalized_raw,
        "source_raw_value": raw_value,
        "unit": unit,
        "source_unit": source_unit,
        "target": target,
        "value": value,
        "detected": detected,
        "determined": determined,
        "provider": PROVIDER_FAUNA_MARIN,
        "provider_name": PROVIDER_NAMES[PROVIDER_FAUNA_MARIN],
    }

    if raw_value.startswith((">", "<")):
        measurement["value_qualifier"] = qualifier
        measurement["value_bound"] = normalized_bound

    measurement["status"] = _status_from_reference(value, raw_value, target)

    recommendation = _parse_fauna_recommendation(recommendation_tail)
    if recommendation is not None:
        measurement["recommendation"] = recommendation

    return measurement


def _parse_fauna_total_phosphate(line: str) -> dict[str, Any] | None:
    """Parse Fauna Marin's calculated total-phosphate row."""
    match = _FAUNA_TOTAL_PHOSPHATE_RE.match(line)
    if not match:
        return None

    raw_value = match.group("value")
    value = _decimal(raw_value)
    target = {
        "type": "range",
        "min": _decimal(match.group("min")),
        "max": _decimal(match.group("max")),
    }

    measurement: dict[str, Any] = {
        "key": "gesamtphosphat_errechnet",
        "name": "Gesamtphosphat (errechnet)",
        "category": "nutrients",
        "raw_value": raw_value,
        "source_raw_value": raw_value,
        "unit": "mg/l",
        "source_unit": "mg/l",
        "target": target,
        "value": value,
        "detected": True,
        "determined": True,
        "provider": PROVIDER_FAUNA_MARIN,
        "provider_name": PROVIDER_NAMES[PROVIDER_FAUNA_MARIN],
    }
    measurement["status"] = _status_from_reference(value, raw_value, target)
    return measurement


def parse_fauna_marin_pdf(path: str | Path) -> dict[str, Any]:
    """Parse the tested Fauna Marin Reef ICP one-page PDF format."""
    try:
        reader = PdfReader(str(path))
    except Exception as err:  # noqa: BLE001
        raise IcpParseError("The uploaded file is not a readable PDF.") from err

    if not reader.pages:
        raise IcpParseError("The PDF contains no pages.")

    layout_texts = [
        page.extract_text(extraction_mode="layout") or ""
        for page in reader.pages
    ]
    layout_text = "\n".join(layout_texts)

    if (
        "Fauna Marin" not in layout_text
        or "Proben-ID:" not in layout_text
        or "ICP-OES" not in layout_text
    ):
        raise IcpParseError(
            "The PDF does not look like a supported Fauna Marin Reef ICP report."
        )

    metadata = _extract_fauna_metadata(layout_text)
    measurements: list[dict[str, Any]] = []

    for line in layout_text.splitlines():
        if total_phosphate := _parse_fauna_total_phosphate(line):
            measurements.append(total_phosphate)
            continue

        match = _FAUNA_ROW_RE.match(line)
        if not match:
            continue

        symbol = match.group("symbol")
        if symbol not in _FAUNA_ANALYTES:
            continue

        target_match = _FAUNA_TARGET_PREFIX_RE.match(match.group("rest"))
        if not target_match:
            continue

        measurement = _fauna_measurement_from_parts(
            symbol=symbol,
            raw_value=match.group("value"),
            raw_target=target_match.group("target"),
            recommendation_tail=target_match.group("tail"),
        )
        if measurement is not None:
            measurements.append(measurement)

    if not measurements:
        raise IcpParseError("No ICP measurements were found in the report.")
    if "analysis_number" not in metadata:
        raise IcpParseError("The Fauna Marin sample ID could not be found.")
    if "analysis_date" not in metadata:
        raise IcpParseError("The Fauna Marin report date could not be found.")

    return {
        "schema_version": 2,
        "provider": PROVIDER_FAUNA_MARIN,
        "provider_name": PROVIDER_NAMES[PROVIDER_FAUNA_MARIN],
        "metadata": metadata,
        "measurements": measurements,
        "interpretation": None,
        # Fauna Marin recommendations are stored per measurement because the
        # PDF provides amount, duration and product in the corresponding row.
        "product_recommendations": None,
    }


def detect_icp_provider(path: str | Path) -> str:
    """Identify the laboratory from provider-specific PDF fingerprints.

    Detection intentionally uses several independent markers per provider so a
    single incidental word is not enough to route a report to the wrong parser.
    Each provider parser performs its own validation again afterwards.
    """
    try:
        reader = PdfReader(str(path))
    except Exception as err:  # noqa: BLE001
        raise IcpParseError("The uploaded file is not a readable PDF.") from err

    if not reader.pages:
        raise IcpParseError("The PDF contains no pages.")

    full_text = "\n".join((page.extract_text() or "") for page in reader.pages)
    normalized = " ".join(full_text.split()).casefold()

    oceamo_markers = (
        "oceamo",
        "analysebericht",
        "analysenummer:",
    )
    fauna_marin_markers = (
        "proben-id:",
        "volumen aquarium in liter:",
        "dosierempfehlung elementals",
    )

    matches: list[str] = []
    if all(marker in normalized for marker in oceamo_markers):
        matches.append(PROVIDER_OCEAMO)
    if all(marker in normalized for marker in fauna_marin_markers):
        matches.append(PROVIDER_FAUNA_MARIN)

    if len(matches) == 1:
        return matches[0]

    if len(matches) > 1:
        raise UnsupportedIcpProviderError(
            "The ICP provider could not be identified unambiguously."
        )

    raise UnsupportedIcpProviderError(
        "The ICP provider is not supported or could not be detected."
    )


def parse_icp_pdf(path: str | Path) -> dict[str, Any]:
    """Detect the provider and dispatch an uploaded PDF automatically."""
    provider = detect_icp_provider(path)

    if provider == PROVIDER_OCEAMO:
        return parse_oceamo_pdf(path)
    if provider == PROVIDER_FAUNA_MARIN:
        return parse_fauna_marin_pdf(path)

    # Kept as a defensive guard for future detector additions.
    raise UnsupportedIcpProviderError(f"Unsupported ICP provider: {provider}")
