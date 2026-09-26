"""Tropic Marin ICP Water Analysis parser for Reef ICP."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
from typing import Any

from pypdf import PdfReader

from .parser_core import IcpParseError, MissingAnalysisDateError

PROVIDER_TROPIC_MARIN = "tropic_marin"
PROVIDER_TROPIC_MARIN_NAME = "Tropic Marin"

REPORT_TYPE_TROPIC_MARIN = "icp_water_analysis"
REPORT_TYPE_TROPIC_MARIN_PLUS = "icp_water_analysis_plus"

_NUMBER = r"-?\d+(?:[.,]\d+)?"
_VALUE = rf"(?:n\.n\.|n\.g\.|[<>]\s*{_NUMBER}|{_NUMBER})"
_TARGET = rf"(?:n\.n\.|n\.g\.|none|colorless|{_NUMBER}\s*-\s*{_NUMBER}|{_NUMBER})"
_RECOMMENDATION = r"(?:ideal|Ideal|increase|lower|-)"

# Canonical tuple:
# aliases, source symbol, canonical key, display name, category,
# normalized unit, source-unit fallback, scale.
_TM_ANALYTES: tuple[dict[str, Any], ...] = (
    # Basic physical / chemical values
    {
        "aliases": ("Electrical conductivity (mS/cm 25°C)", "Electrical conductivity"),
        "symbol": None,
        "key": "leitfaehigkeit",
        "name": "Leitfähigkeit",
        "category": "basic",
        "unit": "mS/cm",
        "source_unit": "mS/cm",
        "scale": 1.0,
    },
    {
        "aliases": ("Density (kg/liter, calculated 25°C)", "Density"),
        "symbol": None,
        "key": "dichte",
        "name": "Dichte",
        "category": "basic",
        "unit": "kg/l",
        "source_unit": "kg/l",
        "scale": 1.0,
    },
    {
        "aliases": ("Relative density (calculated 25°C)", "Relative density"),
        "symbol": None,
        "key": "relative_dichte",
        "name": "Relative Dichte",
        "category": "basic",
        "unit": None,
        "source_unit": None,
        "scale": 1.0,
    },
    {
        "aliases": ("Salinity (psu, calculated)", "Salinity"),
        "symbol": None,
        "key": "salinitaet",
        "name": "Salinität",
        "category": "basic",
        "unit": "psu",
        "source_unit": "psu",
        "scale": 1.0,
    },
    {
        "aliases": ("pH value",),
        "symbol": None,
        "key": "ph",
        "name": "pH",
        "category": "basic",
        "unit": None,
        "source_unit": None,
        "scale": 1.0,
    },
    {
        "aliases": ("Alkalinity (°dKH)", "Alkalinity"),
        "symbol": None,
        "key": "alkalinitaet",
        "name": "Alkalinität",
        "category": "basic",
        "unit": "dKH",
        "source_unit": "dKH",
        "scale": 1.0,
    },
    {
        "aliases": ("CO2-Content (mg/l)", "CO₂-Content (mg/l)", "CO2-Content"),
        "symbol": None,
        "key": "co2",
        "name": "CO₂",
        "category": "basic",
        "unit": "mg/l",
        "source_unit": "mg/l",
        "scale": 1.0,
    },
    {
        "aliases": ("Acid binding capacity pH 4.3 (mmol/L)", "Acid binding capacity pH 4.3"),
        "symbol": None,
        "key": "saeurebindungsvermoegen",
        "name": "Säurebindungsvermögen pH 4,3",
        "category": "basic",
        "unit": "mmol/l",
        "source_unit": "mmol/l",
        "scale": 1.0,
    },
    {
        "aliases": ("Odor",),
        "symbol": None,
        "key": "geruch",
        "name": "Geruch",
        "category": "basic",
        "unit": None,
        "source_unit": None,
        "scale": 1.0,
        "qualitative": True,
    },
    {
        "aliases": ("Coloring", "Colouring"),
        "symbol": None,
        "key": "faerbung",
        "name": "Färbung",
        "category": "basic",
        "unit": None,
        "source_unit": None,
        "scale": 1.0,
        "qualitative": True,
    },

    # Major elements / halogens
    {"aliases": ("Chloride",), "symbol": "Cl-", "key": "chlorid", "name": "Chlorid", "category": "major_elements", "unit": "mg/l", "source_unit": "mg/l", "scale": 1.0, "rel35": True},
    {"aliases": ("Sodium", "Natrium"), "symbol": "Na", "key": "natrium", "name": "Natrium", "category": "major_elements", "unit": "mg/l", "source_unit": "mg/l", "scale": 1.0, "rel35": True},
    {"aliases": ("Sulfur", "Sulphur"), "symbol": "S", "key": "schwefel", "name": "Schwefel", "category": "major_elements", "unit": "mg/l", "source_unit": "mg/l", "scale": 1.0, "rel35": True},
    {"aliases": ("Sulphate", "Sulfate"), "symbol": "SO42-", "key": "sulfat", "name": "Sulfat", "category": "major_elements", "unit": "mg/l", "source_unit": "mg/l", "scale": 1.0, "rel35": True},
    {"aliases": ("Potassium",), "symbol": "K", "key": "kalium", "name": "Kalium", "category": "major_elements", "unit": "mg/l", "source_unit": "mg/l", "scale": 1.0, "rel35": True},
    {"aliases": ("Boron",), "symbol": "B", "key": "bor", "name": "Bor", "category": "major_elements", "unit": "mg/l", "source_unit": "mg/l", "scale": 1.0, "rel35": True},
    {"aliases": ("Magnesium",), "symbol": "Mg", "key": "magnesium", "name": "Magnesium", "category": "major_elements", "unit": "mg/l", "source_unit": "mg/l", "scale": 1.0, "rel35": True},
    {"aliases": ("Calcium",), "symbol": "Ca", "key": "calcium", "name": "Calcium", "category": "major_elements", "unit": "mg/l", "source_unit": "mg/l", "scale": 1.0, "rel35": True},
    {"aliases": ("Strontium",), "symbol": "Sr", "key": "strontium", "name": "Strontium", "category": "major_elements", "unit": "mg/l", "source_unit": "mg/l", "scale": 1.0, "rel35": True},
    {"aliases": ("Bromine", "Bromide"), "symbol": "Br", "key": "bromid", "name": "Bromid", "category": "major_elements", "unit": "mg/l", "source_unit": "mg/l", "scale": 1.0, "rel35": True},
    {"aliases": ("Fluoride",), "symbol": "F-", "key": "fluorid", "name": "Fluorid", "category": "trace_elements", "unit": "mg/l", "source_unit": "mg/l", "scale": 1.0, "rel35": True},
    # Tropic Marin prints iodine in mg/l. Reef ICP's shared iodine unit is µg/l.
    {"aliases": ("Iodine (total iodine, ICP-OES) (mg/l)", "Iodine (total iodine, ICP-OES)", "Iodine"), "symbol": "I", "key": "iod", "name": "Iod", "category": "trace_elements", "unit": "µg/l", "source_unit": "mg/l", "scale": 1000.0, "rel35": True},

    # Nutrients / calculated nutrient values
    {"aliases": ("Nitrate",), "symbol": "NO3-", "key": "nitrat", "name": "Nitrat", "category": "nutrients", "unit": "mg/l", "source_unit": "mg/l", "scale": 1.0},
    {"aliases": ("Nitrite",), "symbol": "NO2-", "key": "nitrit", "name": "Nitrit", "category": "nutrients", "unit": "mg/l", "source_unit": "mg/l", "scale": 1.0},
    {"aliases": ("Phosphorus (ICP-OES)", "Phosphorus"), "symbol": "P", "key": "gesamtphosphor_icp", "name": "Gesamtphosphor (ICP)", "category": "nutrients", "unit": "µg/l", "source_unit": "mg/l", "scale": 1000.0},
    {"aliases": ("Total phosphate (calculated)",), "symbol": "PO43-tot", "key": "phosphat", "name": "Gesamtphosphat", "category": "nutrients", "unit": "mg/l", "source_unit": "mg/l", "scale": 1.0},
    {"aliases": ("Orthophosphate (photometric)",), "symbol": "PO43-", "key": "phosphat_photometrisch", "name": "Phosphat (photometrisch)", "category": "nutrients", "unit": "mg/l", "source_unit": "mg/l", "scale": 1.0},
    {"aliases": ("Silicon",), "symbol": "Si", "key": "silicium", "name": "Silicium", "category": "nutrients", "unit": "µg/l", "source_unit": "mg/l", "scale": 1000.0},
    {"aliases": ("Silicate (calculated)",), "symbol": "SiO2", "key": "silikat", "name": "Silikat (berechnet)", "category": "nutrients", "unit": "mg/l", "source_unit": "mg/l", "scale": 1.0},

    # Trace elements / potential pollutants
    {"aliases": ("Zinc",), "symbol": "Zn", "key": "zink", "name": "Zink", "category": "trace_elements", "unit": "µg/l", "source_unit": "µg/l", "scale": 1.0},
    {"aliases": ("Vanadium",), "symbol": "V", "key": "vanadium", "name": "Vanadium", "category": "trace_elements", "unit": "µg/l", "source_unit": "µg/l", "scale": 1.0},
    {"aliases": ("Copper",), "symbol": "Cu", "key": "kupfer", "name": "Kupfer", "category": "trace_elements", "unit": "µg/l", "source_unit": "µg/l", "scale": 1.0},
    {"aliases": ("Nickel",), "symbol": "Ni", "key": "nickel", "name": "Nickel", "category": "trace_elements", "unit": "µg/l", "source_unit": "µg/l", "scale": 1.0},
    {"aliases": ("Manganese",), "symbol": "Mn", "key": "mangan", "name": "Mangan", "category": "trace_elements", "unit": "µg/l", "source_unit": "µg/l", "scale": 1.0},
    {"aliases": ("Molybdenum",), "symbol": "Mo", "key": "molybdaen", "name": "Molybdän", "category": "trace_elements", "unit": "µg/l", "source_unit": "µg/l", "scale": 1.0},
    {"aliases": ("Iron",), "symbol": "Fe", "key": "eisen", "name": "Eisen", "category": "trace_elements", "unit": "µg/l", "source_unit": "µg/l", "scale": 1.0},
    {"aliases": ("Chrome", "Chromium"), "symbol": "Cr", "key": "chrom", "name": "Chrom", "category": "trace_elements", "unit": "µg/l", "source_unit": "µg/l", "scale": 1.0},
    {"aliases": ("Cobalt",), "symbol": "Co", "key": "cobalt", "name": "Cobalt", "category": "trace_elements", "unit": "µg/l", "source_unit": "µg/l", "scale": 1.0},
    {"aliases": ("Lithium",), "symbol": "Li", "key": "lithium", "name": "Lithium", "category": "trace_elements", "unit": "µg/l", "source_unit": "µg/l", "scale": 1.0},
    {"aliases": ("Barium",), "symbol": "Ba", "key": "barium", "name": "Barium", "category": "trace_elements", "unit": "µg/l", "source_unit": "µg/l", "scale": 1.0},
    {"aliases": ("Aluminium", "Aluminum"), "symbol": "Al", "key": "aluminium", "name": "Aluminium", "category": "pollutants", "unit": "µg/l", "source_unit": "µg/l", "scale": 1.0},
    {"aliases": ("Antimony",), "symbol": "Sb", "key": "antimon", "name": "Antimon", "category": "pollutants", "unit": "µg/l", "source_unit": "µg/l", "scale": 1.0},
    {"aliases": ("Tin",), "symbol": "Sn", "key": "zinn", "name": "Zinn", "category": "trace_elements", "unit": "µg/l", "source_unit": "µg/l", "scale": 1.0},
    {"aliases": ("Beryllium",), "symbol": "Be", "key": "beryllium", "name": "Beryllium", "category": "pollutants", "unit": "µg/l", "source_unit": "µg/l", "scale": 1.0},
    {"aliases": ("Selenium",), "symbol": "Se", "key": "selen", "name": "Selen", "category": "trace_elements", "unit": "µg/l", "source_unit": "µg/l", "scale": 1.0},
    {"aliases": ("Silber", "Silver"), "symbol": "Ag", "key": "silber", "name": "Silber", "category": "pollutants", "unit": "µg/l", "source_unit": "µg/l", "scale": 1.0},
    {"aliases": ("Tungsten",), "symbol": "W", "key": "wolfram", "name": "Wolfram", "category": "pollutants", "unit": "µg/l", "source_unit": "µg/l", "scale": 1.0},
    {"aliases": ("Lanthanum",), "symbol": "La", "key": "lanthan", "name": "Lanthan", "category": "pollutants", "unit": "µg/l", "source_unit": "µg/l", "scale": 1.0},
    {"aliases": ("Titanium",), "symbol": "Ti", "key": "titan", "name": "Titan", "category": "pollutants", "unit": "µg/l", "source_unit": "µg/l", "scale": 1.0},
    {"aliases": ("Zirconium",), "symbol": "Zr", "key": "zirkonium", "name": "Zirkonium", "category": "pollutants", "unit": "µg/l", "source_unit": "µg/l", "scale": 1.0},
    {"aliases": ("Arsenic",), "symbol": "As", "key": "arsen", "name": "Arsen", "category": "pollutants", "unit": "µg/l", "source_unit": "µg/l", "scale": 1.0},
    {"aliases": ("Cadmium",), "symbol": "Cd", "key": "cadmium", "name": "Cadmium", "category": "pollutants", "unit": "µg/l", "source_unit": "µg/l", "scale": 1.0},
    {"aliases": ("Mercury",), "symbol": "Hg", "key": "quecksilber", "name": "Quecksilber", "category": "pollutants", "unit": "µg/l", "source_unit": "µg/l", "scale": 1.0},
    {"aliases": ("Lead",), "symbol": "Pb", "key": "blei", "name": "Blei", "category": "pollutants", "unit": "µg/l", "source_unit": "µg/l", "scale": 1.0},
)

_RELATIVE_ALIASES: tuple[tuple[str, str], ...] = (
    ("Salinity meas. value : target value", "salinity_target_ratio"),
    ("KH measured value : target value", "kh_target_ratio"),
    ("Magnesium : Salinity", "magnesium_salinity_ratio"),
    ("Calcium : Salinity", "calcium_salinity_ratio"),
    ("Strontium: Salinity", "strontium_salinity_ratio"),
    ("Potassium : Salinity", "potassium_salinity_ratio"),
    ("Boron : Salinity", "boron_salinity_ratio"),
    ("Chloride : Salinity", "chloride_salinity_ratio"),
    ("Sulphate : Salinity", "sulphate_salinity_ratio"),
    ("Chloride : Sulphate", "chloride_sulphate_ratio"),
    ("Magnesium : Calcium", "magnesium_calcium_ratio"),
    ("Calcium : Strontium", "calcium_strontium_ratio"),
    ("Bromide : Fluoride", "bromide_fluoride_ratio"),
    ("Fluoride : Iodine", "fluoride_iodine_ratio"),
    ("Total phosphate : Nitrate", "total_phosphate_nitrate_ratio"),
    ("Total phosphate : Ortho-phosphate", "total_phosphate_orthophosphate_ratio"),
    ("Total phosphate : Iodine", "total_phosphate_iodine_ratio"),
)


def _decimal(value: str) -> float:
    return float(value.strip().replace(",", "."))


def _number_text(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.9f}".rstrip("0").rstrip(".")


def _normalize_line(value: str) -> str:
    return " ".join(value.replace("μ", "µ").split()).strip()


def _parse_us_date(value: str) -> str:
    return datetime.strptime(value.strip(), "%m-%d-%Y").date().isoformat()


def _date_at_noon_us(value: str) -> str:
    parsed = datetime.strptime(value.strip(), "%m-%d-%Y")
    return parsed.replace(hour=12).isoformat()


def _validated_iso_date(value: str) -> str:
    return datetime.strptime(value.strip(), "%Y-%m-%d").date().isoformat()


def _target(raw: str, scale: float = 1.0) -> dict[str, Any]:
    value = _normalize_line(raw)
    low = value.casefold()
    if low == "n.n.":
        return {"type": "not_detectable"}
    if low == "n.g.":
        return {"type": "not_determined"}
    if low in {"none", "colorless", "colourless"}:
        return {"type": "text", "value": value}
    match = re.fullmatch(rf"(?P<min>{_NUMBER})\s*-\s*(?P<max>{_NUMBER})", value)
    if match:
        return {
            "type": "range",
            "min": _decimal(match.group("min")) * scale,
            "max": _decimal(match.group("max")) * scale,
        }
    if re.fullmatch(_NUMBER, value):
        return {"type": "exact", "value": _decimal(value) * scale}
    return {"type": "unknown", "raw": value}


def _status_from_recommendation(raw: str | None) -> dict[str, str | None]:
    value = (raw or "").strip().casefold()
    if value == "ideal":
        return {"severity": "ok", "direction": None}
    if value == "increase":
        return {"severity": "warning", "direction": "low"}
    if value == "lower":
        return {"severity": "warning", "direction": "high"}
    return {"severity": "unknown", "direction": None}


def _status_from_target(
    state: dict[str, Any],
    target: dict[str, Any],
) -> dict[str, str | None]:
    """Conservatively evaluate rows that do not carry a lab recommendation."""
    value = state.get("value")
    raw_value = str(state.get("raw_value") or "").casefold()
    target_type = target.get("type")

    if value is None:
        if raw_value == "n.n." and target_type == "not_detectable":
            return {"severity": "ok", "direction": None}
        if raw_value == "n.n." and target_type in {"range", "lower_limit", "exact"}:
            return {"severity": "warning", "direction": "low"}
        return {"severity": "unknown", "direction": None}

    numeric = float(value)
    if target_type == "not_detectable":
        return {"severity": "warning", "direction": "high"}
    if target_type == "range":
        minimum = target.get("min")
        maximum = target.get("max")
        if isinstance(minimum, (int, float)) and numeric < float(minimum):
            return {"severity": "warning", "direction": "low"}
        if isinstance(maximum, (int, float)) and numeric > float(maximum):
            return {"severity": "warning", "direction": "high"}
        return {"severity": "ok", "direction": None}
    if target_type == "exact":
        expected = target.get("value")
        if isinstance(expected, (int, float)):
            epsilon = max(abs(float(expected)), 1.0) * 1e-9
            if numeric < float(expected) - epsilon:
                return {"severity": "warning", "direction": "low"}
            if numeric > float(expected) + epsilon:
                return {"severity": "warning", "direction": "high"}
            return {"severity": "ok", "direction": None}
    return {"severity": "unknown", "direction": None}


def _value_state(raw: str, scale: float) -> dict[str, Any]:
    value = raw.strip()
    low = value.casefold()
    if low == "n.n.":
        return {
            "raw_value": "n.n.",
            "value": None,
            "detected": False,
            "determined": True,
        }
    if low == "n.g.":
        return {
            "raw_value": "n.g.",
            "value": None,
            "detected": None,
            "determined": False,
        }
    bound = re.fullmatch(rf"(?P<op>[<>])\s*(?P<number>{_NUMBER})", value)
    if bound:
        number = _decimal(bound.group("number")) * scale
        operator = bound.group("op")
        return {
            "raw_value": f"{operator}{_number_text(number)}",
            "value": number,
            "detected": True,
            "determined": True,
            "value_qualifier": "greater_than" if operator == ">" else "less_than",
            "value_bound": number,
        }
    if re.fullmatch(_NUMBER, value):
        number = _decimal(value) * scale
        return {
            "raw_value": _number_text(number),
            "value": number,
            "detected": True,
            "determined": True,
        }
    return {
        "raw_value": value,
        "value": None,
        "detected": None,
        "determined": True,
    }


def _extract_page_text(page: Any) -> str:
    """Prefer pypdf's layout mode because Tropic Marin reports are table-heavy."""
    try:
        layout = page.extract_text(extraction_mode="layout") or ""
        if layout.strip():
            return layout
    except Exception:  # noqa: BLE001
        pass
    try:
        return page.extract_text() or ""
    except Exception:  # noqa: BLE001
        return ""


def _raw_page_fingerprint(page: Any) -> str:
    """Return explicit text-like markers that may not survive normal extraction."""
    parts: list[str] = []
    try:
        contents = page.get_contents()
        if contents is not None:
            data = contents.get_data()
            parts.append(data.decode("latin-1", "ignore"))
    except Exception:  # noqa: BLE001
        pass

    # Form XObjects sometimes carry the stylized report title separately.
    try:
        resources = page.get("/Resources")
        if resources is not None:
            xobjects_ref = resources.get("/XObject")
            if xobjects_ref is not None:
                xobjects = xobjects_ref.get_object()
                for name, ref in xobjects.items():
                    parts.append(str(name))
                    obj = ref.get_object()
                    for key in ("/Name", "/Title", "/Alt", "/ActualText", "/TU", "/T"):
                        value = obj.get(key) if hasattr(obj, "get") else None
                        if value is not None:
                            parts.append(str(value))
                    if str(obj.get("/Subtype")) == "/Form":
                        try:
                            parts.append(obj.get_data().decode("latin-1", "ignore"))
                        except Exception:  # noqa: BLE001
                            pass
    except Exception:  # noqa: BLE001
        pass
    return "\n".join(parts)


def _report_type(reader: PdfReader, page_texts: list[str]) -> tuple[str, str]:
    """Read the explicit Water Analysis product name from the PDF.

    The title is the authority. Reef ICP does not classify Plus from page count,
    conductivity, RO-water measurements or any other measured field.
    """
    explicit_parts = list(page_texts[:1])
    try:
        explicit_parts.extend(str(value) for value in (reader.metadata or {}).values())
    except Exception:  # noqa: BLE001
        pass
    explicit_parts.append(_raw_page_fingerprint(reader.pages[0]))
    fingerprint = " ".join(explicit_parts)
    normalized = re.sub(r"\s+", " ", fingerprint).casefold()

    if re.search(r"icp\s*water\s*analysis.{0,80}\bplus\b", normalized):
        return REPORT_TYPE_TROPIC_MARIN_PLUS, "explicit_title"
    if re.search(r"\bplus\b.{0,80}icp\s*water\s*analysis", normalized):
        return REPORT_TYPE_TROPIC_MARIN_PLUS, "explicit_title"
    if re.search(r"icp\s*water\s*analysis", normalized):
        return REPORT_TYPE_TROPIC_MARIN, "explicit_title"

    # The provider is still valid if the stylized title is not text-extractable.
    # Keep the neutral base family instead of guessing Plus from report contents.
    return REPORT_TYPE_TROPIC_MARIN, "title_not_extractable"


def _provider_markers(text: str) -> bool:
    normalized = " ".join(text.split()).casefold()
    markers = (
        "tropic marin block analysis system",
        "sample-id:",
        "lab.tropic-marin.com",
        "date of taking the water sample",
    )
    return sum(marker in normalized for marker in markers) >= 3


def looks_like_tropic_marin_pdf(path: str | Path) -> bool:
    """Return True only for the tested Tropic Marin Water Analysis family."""
    try:
        reader = PdfReader(str(path))
    except Exception:
        return False
    if not reader.pages:
        return False
    text = "\n".join(_extract_page_text(page) for page in reader.pages)
    return _provider_markers(text)


def _extract_metadata(
    text: str,
    source_path: Path,
    report_type: str,
    report_type_source: str,
    analysis_date_override: str | None,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "provider": PROVIDER_TROPIC_MARIN,
        "provider_name": PROVIDER_TROPIC_MARIN_NAME,
        "report_type": report_type,
        "report_type_source": report_type_source,
    }

    patterns = {
        "sample_id": r"Sample-ID:\s*([A-Z0-9-]+)",
        "sample_type": r"Sample type:\s*([^\n]+)",
        "aquarium_name": r"From your aquarium:\s*([^\n]+)",
        "sample_date_raw": r"Date of taking the water sample:\s*(\d{2}-\d{2}-\d{4})",
        "receipt_date_raw": r"Receipt of the sample\s*:?\s*(\d{2}-\d{2}-\d{4})",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            metadata[key] = _normalize_line(match.group(1))

    volume = re.search(
        rf"Aquarium volume in liters:\s*({_NUMBER})",
        text,
        re.IGNORECASE,
    )
    if volume:
        parsed_volume = _decimal(volume.group(1))
        metadata["aquarium_volume_l"] = (
            int(parsed_volume) if parsed_volume.is_integer() else parsed_volume
        )

    report_id = re.search(
        r"lab\.tropic-marin\.com/(?:de|en)/home/analysis/(\d+)",
        text,
        re.IGNORECASE,
    )
    if report_id:
        analysis_number = report_id.group(1)
    elif source_path.stem.isdigit():
        analysis_number = source_path.stem
    else:
        sample_id = str(metadata.get("sample_id") or "").strip()
        analysis_number = sample_id or None

    if analysis_number:
        metadata["analysis_number"] = analysis_number
        metadata["provider_report_id"] = analysis_number
        metadata["analysis_url"] = (
            f"https://lab.tropic-marin.com/de/home/analysis/{analysis_number}"
        )

    sample_date_raw = metadata.pop("sample_date_raw", None)
    if sample_date_raw:
        metadata["sample_date"] = _parse_us_date(str(sample_date_raw))
        metadata["sample_taken"] = _date_at_noon_us(str(sample_date_raw))

    receipt_date_raw = metadata.pop("receipt_date_raw", None)
    if receipt_date_raw:
        metadata["receipt_date"] = _parse_us_date(str(receipt_date_raw))
        # Tropic Marin prints no separate completed-analysis date in the tested
        # PDFs. Preserve receipt as document chronology while sample_taken
        # remains the primary history sort key.
        metadata["analysis_date"] = metadata["receipt_date"]
        metadata["analysis_date_source"] = "document_receipt"

    if not metadata.get("analysis_date"):
        if metadata.get("sample_date"):
            metadata["analysis_date"] = metadata["sample_date"]
            metadata["analysis_date_source"] = "sample_taken"
        elif analysis_date_override is not None:
            try:
                metadata["analysis_date"] = _validated_iso_date(
                    str(analysis_date_override)
                )
            except ValueError as err:
                raise MissingAnalysisDateError(
                    "The selected analysis date is invalid."
                ) from err
            metadata["analysis_date_source"] = "manual"
        else:
            raise MissingAnalysisDateError(
                "Tropic Marin report does not contain a trustworthy analysis date."
            )

    return metadata


def _strip_alias_and_symbol(
    line: str,
    spec: dict[str, Any],
) -> tuple[str, str] | None:
    folded = line.casefold()
    for alias in sorted(spec["aliases"], key=len, reverse=True):
        alias_folded = alias.casefold()
        if not folded.startswith(alias_folded):
            continue
        rest = line[len(alias):].strip()
        symbol = spec.get("symbol")
        if symbol:
            symbol_match = re.match(
                rf"^{re.escape(str(symbol))}(?:\s+|$)",
                rest,
                re.IGNORECASE,
            )
            if symbol_match:
                rest = rest[symbol_match.end():].strip()
            else:
                # PDF extraction occasionally inserts a unit before the symbol
                # in the iodine/block rows. Locate the expected symbol locally.
                located = re.search(
                    rf"(?:^|\s){re.escape(str(symbol))}(?:\s|$)",
                    rest,
                    re.IGNORECASE,
                )
                if located and located.start() < 45:
                    rest = rest[located.end():].strip()
        return alias, rest
    return None


def _parse_row_tail(
    tail: str,
    expect_rel35: bool,
    osmosis_mode: bool = False,
) -> dict[str, str] | None:
    tail = _normalize_line(tail)

    # RO/DI-water tables contain only measured value and target. Parse that
    # shape first so a target range such as ``0 - 10`` is not mistaken for
    # recommendation ``-`` plus a stray product token.
    if osmosis_mode:
        pattern = re.compile(
            rf"^(?P<value>{_VALUE})\s+(?P<target>{_TARGET})$",
            re.IGNORECASE,
        )
        match = pattern.match(tail)
        if match:
            result = {key: (value or "") for key, value in match.groupdict().items()}
            result.update({"recommendation": "", "product": "", "rel": ""})
            return result

        # Some Tropic Marin PDF rows split a chemical formula into several text
        # fragments. The Plus report's osmosis total-phosphate row is one known
        # example (the PO4 formula can remain in front of the two table values).
        # For osmosis rows the measured value and target are the final two
        # columns, so recover that pair from the end without guessing from any
        # earlier numbers that may belong to the chemical formula.
        match = re.search(
            rf"(?P<value>{_VALUE})\s+(?P<target>{_TARGET})\s*$",
            tail,
            re.IGNORECASE,
        )
        if match:
            result = {key: (value or "") for key, value in match.groupdict().items()}
            result.update({"recommendation": "", "product": "", "rel": ""})
            return result

    if expect_rel35:
        pattern = re.compile(
            rf"^(?P<value>{_VALUE})\s+"
            rf"(?P<rel>{_VALUE})\s+"
            rf"(?P<target>{_TARGET})\s+"
            rf"(?P<recommendation>{_RECOMMENDATION})"
            rf"(?:\s+(?P<product>.+))?$",
            re.IGNORECASE,
        )
        match = pattern.match(tail)
        if match:
            return {key: (value or "") for key, value in match.groupdict().items()}

    pattern = re.compile(
        rf"^(?P<value>{_VALUE})\s+"
        rf"(?P<target>{_TARGET})\s+"
        rf"(?P<recommendation>{_RECOMMENDATION})"
        rf"(?:\s+(?P<product>.+))?$",
        re.IGNORECASE,
    )
    match = pattern.match(tail)
    if match:
        result = {key: (value or "") for key, value in match.groupdict().items()}
        result["rel"] = ""
        return result

    # Osmosis-water rows carry measured value and target only.
    pattern = re.compile(
        rf"^(?P<value>{_VALUE})\s+(?P<target>{_TARGET})$",
        re.IGNORECASE,
    )
    match = pattern.match(tail)
    if match:
        result = {key: (value or "") for key, value in match.groupdict().items()}
        result.update({"recommendation": "", "product": "", "rel": ""})
        return result

    return None


def _qualitative_measurement(
    spec: dict[str, Any],
    source_name: str,
    tail: str,
    category: str,
) -> dict[str, Any] | None:
    parts = tail.split()
    if not parts:
        return None
    raw_value = parts[0]
    target_raw = " ".join(parts[1:]) if len(parts) > 1 else ""
    return {
        "key": spec["key"],
        "name": spec["name"],
        "source_name": source_name,
        "category": category,
        "raw_value": raw_value,
        "source_raw_value": raw_value,
        "unit": None,
        "source_unit": None,
        "target": _target(target_raw) if target_raw else {"type": "unknown"},
        "value": None,
        "detected": None,
        "determined": True,
        "status": {"severity": "unknown", "direction": None},
        "provider": PROVIDER_TROPIC_MARIN,
        "provider_name": PROVIDER_TROPIC_MARIN_NAME,
    }


def _measurement_from_line(
    line: str,
    osmosis_mode: bool,
) -> dict[str, Any] | None:
    normalized = _normalize_line(line)

    for spec in _TM_ANALYTES:
        matched = _strip_alias_and_symbol(normalized, spec)
        if matched is None:
            continue
        source_name, tail = matched

        category = "osmosis" if osmosis_mode else str(spec["category"])
        if spec.get("qualitative"):
            return _qualitative_measurement(spec, source_name, tail, category)

        expect_rel35 = bool(spec.get("rel35")) and not osmosis_mode
        parsed = _parse_row_tail(tail, expect_rel35, osmosis_mode)
        if parsed is None and expect_rel35:
            parsed = _parse_row_tail(tail, False, osmosis_mode)
        if parsed is None:
            continue

        scale = float(spec["scale"])
        state = _value_state(parsed["value"], scale)
        recommendation = parsed.get("recommendation") or ""
        product = _normalize_line(parsed.get("product") or "") or None
        parsed_target = _target(parsed["target"], scale)
        status = _status_from_recommendation(recommendation)
        if status["severity"] == "unknown" and not recommendation.strip():
            status = _status_from_target(state, parsed_target)

        display_name = (
            f"{spec['name']} (Osmose)"
            if category == "osmosis"
            else str(spec["name"])
        )

        measurement: dict[str, Any] = {
            "key": spec["key"],
            "name": display_name,
            "source_name": source_name,
            "source_symbol": spec.get("symbol"),
            "category": category,
            "source_raw_value": parsed["value"],
            "source_unit": spec.get("source_unit"),
            "unit": spec.get("unit"),
            "target": parsed_target,
            "status": status,
            "provider": PROVIDER_TROPIC_MARIN,
            "provider_name": PROVIDER_TROPIC_MARIN_NAME,
            "laboratory_assessment": recommendation or None,
            "provider_product_recommendation": product,
            **state,
        }

        if rel_value := parsed.get("rel"):
            rel_state = _value_state(rel_value, scale)
            measurement["relative_35_psu_raw"] = rel_value
            measurement["relative_35_psu"] = rel_state.get("value")

        return measurement

    return None


def _parse_orphan_co2(
    line: str,
    basic_keys: set[str],
) -> dict[str, Any] | None:
    """Recover CO2 when PDF extraction separates the row label from its values."""
    if "alkalinitaet" not in basic_keys or "co2" in basic_keys:
        return None
    match = re.match(
        rf"^(?P<value>{_VALUE})\s+(?P<target>{_TARGET})\s+(?P<rec>{_RECOMMENDATION})$",
        _normalize_line(line),
        re.IGNORECASE,
    )
    if not match:
        return None
    # Avoid assigning unrelated standalone lines by limiting this fallback to a
    # plausible CO2 row immediately after the alkalinity block.
    raw = match.group("value")
    if raw.casefold() not in {"n.g.", "n.n."}:
        try:
            if not (0.0 <= _decimal(raw.lstrip("<> ")) <= 20.0):
                return None
        except ValueError:
            return None
    state = _value_state(raw, 1.0)
    return {
        "key": "co2",
        "name": "CO₂",
        "source_name": "CO2-Content",
        "category": "basic",
        "source_raw_value": raw,
        "raw_value": state["raw_value"],
        "source_unit": "mg/l",
        "unit": "mg/l",
        "target": _target(match.group("target")),
        "status": _status_from_recommendation(match.group("rec")),
        "provider": PROVIDER_TROPIC_MARIN,
        "provider_name": PROVIDER_TROPIC_MARIN_NAME,
        **{k: v for k, v in state.items() if k != "raw_value"},
    }


def _parse_relative_value(line: str) -> dict[str, Any] | None:
    normalized = _normalize_line(line)
    for alias, key in _RELATIVE_ALIASES:
        if not normalized.casefold().startswith(alias.casefold()):
            continue
        rest = normalized[len(alias):].strip()

        # Optional printed short symbol (Sal., KH, Mg, Ca, ...)
        rest = re.sub(r"^(?:Sal\.|KH|Mg/Ca|Ca/Sr|Cl-/SO42-|SO42-|Cl-|Mg|Ca|Sr|K|B|Br-/F-|F-/I)\s+", "", rest)

        match = re.match(
            rf"^(?P<value>{_VALUE})\s+(?P<target>{_TARGET})$",
            rest,
            re.IGNORECASE,
        )
        if not match:
            continue

        state = _value_state(match.group("value"), 1.0)
        return {
            "key": key,
            "source_name": alias,
            "raw_value": state["raw_value"],
            "value": state.get("value"),
            "target": _target(match.group("target")),
        }
    return None


def _parse_measurements(
    text: str,
    *,
    force_osmosis: bool = False,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    lines = [_normalize_line(line) for line in text.splitlines() if _normalize_line(line)]
    measurements: list[dict[str, Any]] = []
    relative_values: list[dict[str, Any]] = []

    osmosis_mode = force_osmosis
    relative_mode = False
    basic_mode = False
    basic_keys: set[str] = set()

    for line in lines:
        folded = line.casefold()

        if "basic physical and chemical values" in folded:
            basic_mode = True
            relative_mode = False
            if not force_osmosis:
                osmosis_mode = False
            continue
        if "relative values" in folded:
            relative_mode = True
            basic_mode = False
            continue
        if "osmosis water in" in folded:
            osmosis_mode = True
            relative_mode = False
            basic_mode = False
            continue
        if any(
            marker in folded
            for marker in (
                "macroelements",
                "makroelements",
                "physiologically relevant trace",
                "other trace elements",
                "macronutrients",
            )
        ):
            relative_mode = False
            basic_mode = False
            # Do not clear osmosis mode on the Plus RO-water page.
            continue

        if relative_mode:
            relative = _parse_relative_value(line)
            if relative is not None:
                relative_values.append(relative)
                continue

        measurement = _measurement_from_line(line, osmosis_mode)
        if measurement is not None:
            # Block Analysis summary rows repeat I/Mo/Ni/Sr/Zn. Keep the later
            # full-table row but preserve any BAS product hint from either copy.
            identity = (measurement["category"], measurement["key"])
            existing_index = next(
                (
                    index
                    for index, item in enumerate(measurements)
                    if (item["category"], item["key"]) == identity
                ),
                None,
            )
            if existing_index is None:
                measurements.append(measurement)
            else:
                old = measurements[existing_index]
                if not measurement.get("provider_product_recommendation"):
                    measurement["provider_product_recommendation"] = old.get(
                        "provider_product_recommendation"
                    )
                measurements[existing_index] = measurement

            if measurement["category"] == "basic":
                basic_keys.add(str(measurement["key"]))
            continue

        if basic_mode:
            orphan = _parse_orphan_co2(line, basic_keys)
            if orphan is not None:
                measurements.append(orphan)
                basic_keys.add("co2")

    return measurements, relative_values


def _product_recommendation_text(measurements: list[dict[str, Any]]) -> str | None:
    lines: list[str] = []
    seen: set[tuple[str, str, str]] = set()
    for measurement in measurements:
        product = str(measurement.get("provider_product_recommendation") or "").strip()
        assessment = str(measurement.get("laboratory_assessment") or "").strip()
        if not product and assessment.casefold() in {"", "ideal", "-"}:
            continue
        identity = (
            str(measurement.get("name") or measurement.get("key") or ""),
            assessment,
            product,
        )
        if identity in seen:
            continue
        seen.add(identity)
        parts = [identity[0]]
        if assessment and assessment != "-":
            parts.append(assessment)
        if product:
            parts.append(product)
        lines.append(" · ".join(parts))
    return "\n".join(lines) if lines else None


def parse_tropic_marin_pdf(
    path: str | Path,
    analysis_date_override: str | None = None,
) -> dict[str, Any]:
    """Parse Tropic Marin ICP Water Analysis / Water Analysis Plus PDFs."""
    source_path = Path(path)
    try:
        reader = PdfReader(str(source_path))
    except Exception as err:  # noqa: BLE001
        raise IcpParseError("The uploaded file is not a readable PDF.") from err

    if not reader.pages:
        raise IcpParseError("The PDF contains no pages.")

    page_texts = [_extract_page_text(page) for page in reader.pages]
    full_text = "\n".join(page_texts)

    if not _provider_markers(full_text):
        raise IcpParseError(
            "The PDF does not look like a supported Tropic Marin ICP Water Analysis report."
        )

    report_type, report_type_source = _report_type(reader, page_texts)
    metadata = _extract_metadata(
        full_text,
        source_path,
        report_type,
        report_type_source,
        analysis_date_override,
    )
    measurements: list[dict[str, Any]] = []
    relative_values: list[dict[str, Any]] = []
    for page_text in page_texts:
        force_osmosis = "osmosis water in" in page_text.casefold()
        page_measurements, page_relative_values = _parse_measurements(
            page_text,
            force_osmosis=force_osmosis,
        )
        for measurement in page_measurements:
            identity = (measurement.get("category"), measurement.get("key"))
            existing_index = next(
                (
                    index
                    for index, item in enumerate(measurements)
                    if (item.get("category"), item.get("key")) == identity
                ),
                None,
            )
            if existing_index is None:
                measurements.append(measurement)
            else:
                old_measurement = measurements[existing_index]
                if not measurement.get("provider_product_recommendation"):
                    measurement["provider_product_recommendation"] = old_measurement.get(
                        "provider_product_recommendation"
                    )
                measurements[existing_index] = measurement
        relative_values.extend(page_relative_values)

    if not measurements:
        raise IcpParseError("No Tropic Marin ICP measurements were found in the report.")
    if not metadata.get("analysis_number"):
        raise IcpParseError("The Tropic Marin analysis number could not be found.")

    if relative_values:
        metadata["relative_values"] = relative_values

    return {
        "schema_version": 2,
        "provider": PROVIDER_TROPIC_MARIN,
        "provider_name": PROVIDER_TROPIC_MARIN_NAME,
        "report_type": report_type,
        "metadata": metadata,
        "measurements": measurements,
        "product_recommendations": _product_recommendation_text(measurements),
    }


# Small text-only hook used by local regression checks without needing to
# redistribute Tropic Marin's public PDFs with the repository.
def _parse_text_fixture(text: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return _parse_measurements(text)
