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
PROVIDER_ATI = "ati"
PROVIDER_TRITON = "triton"

PROVIDER_NAMES = {
    PROVIDER_OCEAMO: "Oceamo",
    PROVIDER_FAUNA_MARIN: "Fauna Marin",
    PROVIDER_ATI: "ATI",
    PROVIDER_TRITON: "TRITON",
}


class IcpParseError(ValueError):
    """Raised when an ICP report cannot be parsed."""


class UnsupportedIcpProviderError(IcpParseError):
    """Raised when Reef ICP cannot identify a supported provider."""


class MissingAnalysisDateError(IcpParseError):
    """Raised when a supported report has no trustworthy analysis date."""


# Backward-compatible exception name for existing imports/tests.
OceamoParseError = IcpParseError


OCEAMO_CATEGORY_HEADINGS = {
    # Classic German reports
    "Grundparameter": "basic",
    "Mengenelemente": "major_elements",
    "Spurenelemente": "trace_elements",
    "Schadstoffe": "pollutants",
    "Nährstoffe": "nutrients",
    "Osmose-Check": "osmosis",
    # Current ICP-MS reports are also distributed in English.
    "Main Parameters": "basic",
    "Basic Parameters": "basic",
    "Main Elements": "major_elements",
    "Major Elements": "major_elements",
    "Trace Elements": "trace_elements",
    "Pollutants": "pollutants",
    "Nutrients": "nutrients",
    "Osmosis-Check": "osmosis",
    "Osmosis Check": "osmosis",
    "Osmosis Water": "osmosis",
    "RO Water": "osmosis",
    "RO/DI Water": "osmosis",
    "RO/DI Check": "osmosis",
}

_OCEAMO_CATEGORY_LOOKUP = {
    heading.casefold(): category
    for heading, category in OCEAMO_CATEGORY_HEADINGS.items()
}

# MD5 hashes of the decoded 15x15 status artwork embedded in the tested
# classic Oceamo PDF format. Unknown artwork is deliberately not guessed.
_OCEAMO_STATUS_IMAGE_HASHES: dict[str, dict[str, str | None]] = {
    # Additional classic Oceamo icon artwork found in report OC186791.
    # The symbols are visually identical to the already supported classic
    # artwork but are encoded with different image data in this PDF.
    "cfb66b1710334a248808b253e6b14042": {
        "severity": "ok",
        "direction": None,
    },
    "e802549f897c6078c97136fbb0a4e89b": {
        "severity": "warning",
        "direction": "high",
    },
    "bbdd419dc49cf34b80e3870a744d0664": {
        "severity": "warning",
        "direction": "low",
    },
    "75e34c979b0e3c9b6e0998368f97b763": {
        "severity": "warning",
        "direction": "low",
    },
    "9acf4dc1999b18fb93117d505ba6bf77": {
        "severity": "critical",
        "direction": "high",
    },
    "4c41d03b9aa6117374e57ddbaef76f67": {
        "severity": "critical",
        "direction": "low",
    },
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

_UNIT_PATTERN = r"(?:psu|dKH|mg/[lL]|µg/[lL]|μg/[lL]|ng/[lL]|mmol/[lL]|µmol/[lL]|μmol/[lL]|m-1|m\^-1|m⁻¹|1/m)"

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
    rf"(?:\s+(?P<target_unit>{_UNIT_PATTERN}))?\s*$",
    re.IGNORECASE,
)

# Canonical Oceamo names make the English ICP-MS layout share entity and
# statistic IDs with the older German classic reports wherever the analyte is
# genuinely the same measurement. Unknown future analytes still fall back to a
# stable slug, so adding a new laboratory parameter does not break the parser.
# Mapping: normalized source-name slug -> (canonical key, display name)
_OCEAMO_CANONICAL_NAMES: dict[str, tuple[str, str]] = {
    "salinitaet": ("salinitaet", "Salinität"),
    "salinity": ("salinitaet", "Salinität"),
    "alkalinitaet": ("alkalinitaet", "Alkalinität"),
    "alkalinitaet_kh": ("alkalinitaet", "Alkalinität"),
    "alkalinity": ("alkalinitaet", "Alkalinität"),
    "alkalinity_kh": ("alkalinitaet", "Alkalinität"),
    "sak254": ("sak254", "SAK254"),
    "sac254": ("sak254", "SAK254"),
    "calcium": ("calcium", "Calcium"),
    "bor": ("bor", "Bor"),
    "boron": ("bor", "Bor"),
    "bromid": ("bromid", "Bromid"),
    "bromide": ("bromid", "Bromid"),
    "chlorid": ("chlorid", "Chlorid"),
    "chloride": ("chlorid", "Chlorid"),
    "kalium": ("kalium", "Kalium"),
    "potassium": ("kalium", "Kalium"),
    "magnesium": ("magnesium", "Magnesium"),
    "natrium": ("natrium", "Natrium"),
    "sodium": ("natrium", "Natrium"),
    "strontium": ("strontium", "Strontium"),
    "sulfat": ("sulfat", "Sulfat"),
    "sulfate": ("sulfat", "Sulfat"),
    "sulphate": ("sulfat", "Sulfat"),
    "barium": ("barium", "Barium"),
    "chrom": ("chrom", "Chrom"),
    "chromium": ("chrom", "Chrom"),
    "cobalt": ("cobalt", "Cobalt"),
    "caesium": ("caesium", "Cäsium"),
    "cesium": ("caesium", "Cäsium"),
    "eisen": ("eisen", "Eisen"),
    "iron": ("eisen", "Eisen"),
    "fluorid": ("fluorid", "Fluorid"),
    "fluoride": ("fluorid", "Fluorid"),
    "iod": ("iod", "Iod"),
    "iodine": ("iod", "Iod"),
    "iodid": ("iod", "Iod"),
    "iodide": ("iod", "Iod"),
    "kupfer": ("kupfer", "Kupfer"),
    "copper": ("kupfer", "Kupfer"),
    "lithium": ("lithium", "Lithium"),
    "mangan": ("mangan", "Mangan"),
    "manganese": ("mangan", "Mangan"),
    "molybdaen": ("molybdaen", "Molybdän"),
    "molybdenum": ("molybdaen", "Molybdän"),
    "nickel": ("nickel", "Nickel"),
    "rubidium": ("rubidium", "Rubidium"),
    "selen": ("selen", "Selen"),
    "selenium": ("selen", "Selen"),
    "vanadium": ("vanadium", "Vanadium"),
    "zink": ("zink", "Zink"),
    "zinc": ("zink", "Zink"),
    "zinn": ("zinn", "Zinn"),
    "tin": ("zinn", "Zinn"),
    "aluminium": ("aluminium", "Aluminium"),
    "aluminum": ("aluminium", "Aluminium"),
    "antimon": ("antimon", "Antimon"),
    "antimony": ("antimon", "Antimon"),
    "arsen": ("arsen", "Arsen"),
    "arsenic": ("arsen", "Arsen"),
    "beryllium": ("beryllium", "Beryllium"),
    "bismuth": ("bismuth", "Bismuth"),
    "blei": ("blei", "Blei"),
    "lead": ("blei", "Blei"),
    "cadmium": ("cadmium", "Cadmium"),
    "cer": ("cer", "Cer"),
    "cerium": ("cer", "Cer"),
    "gallium": ("gallium", "Gallium"),
    "lanthan": ("lanthan", "Lanthan"),
    "lanthanum": ("lanthan", "Lanthan"),
    "quecksilber": ("quecksilber", "Quecksilber"),
    "mercury": ("quecksilber", "Quecksilber"),
    "neodym": ("neodym", "Neodym"),
    "neodymium": ("neodym", "Neodym"),
    "thallium": ("thallium", "Thallium"),
    "tellur": ("tellur", "Tellur"),
    "tellurium": ("tellur", "Tellur"),
    "titan": ("titan", "Titan"),
    "titanium": ("titan", "Titan"),
    "ruthenium": ("ruthenium", "Ruthenium"),
    "thorium": ("thorium", "Thorium"),
    "wolfram": ("wolfram", "Wolfram"),
    "tungsten": ("wolfram", "Wolfram"),
    "uran": ("uran", "Uran"),
    "uranium": ("uran", "Uran"),
    "hafnium": ("hafnium", "Hafnium"),
    "nitrat": ("nitrat", "Nitrat"),
    "nitrate": ("nitrat", "Nitrat"),
    "nitrit": ("nitrit", "Nitrit"),
    "nitrite": ("nitrit", "Nitrit"),
    "phosphat_photometrisch": ("phosphat_photometrisch", "Phosphat (photometrisch)"),
    "phosphate_photometric": ("phosphat_photometrisch", "Phosphat (photometrisch)"),
    "gesamtphosphor_icp": ("gesamtphosphor_icp", "Gesamtphosphor (ICP)"),
    "total_phosphorus_icp": ("gesamtphosphor_icp", "Gesamtphosphor (ICP)"),
    "silicium": ("silicium", "Silicium"),
    "silicon": ("silicium", "Silicium"),
}

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



# Tested legacy TRITON ICP-OES PDF layouts (2014/2015 generation).
#
# The PDF contains compact tabular rows with:
# element, analysis value, set point, deviation, a coloured warning light,
# aquarium volume, one-time dosage and daily dosage. The warning light itself
# is drawn as a coloured rectangle and therefore does not appear in extracted
# text. Reef ICP reads those rectangles from the PDF content stream and aligns
# them with the parsed rows in drawing order.
#
# Tuple: (key, display name, category, normalized unit)
_TRITON_LEGACY_ANALYTES: dict[str, tuple[str, str, str, str]] = {
    "Hg": ("quecksilber", "Quecksilber", "pollutants", "µg/l"),
    "Se": ("selen", "Selen", "trace_elements", "µg/l"),
    "Cd": ("cadmium", "Cadmium", "pollutants", "µg/l"),
    "Sn": ("zinn", "Zinn", "trace_elements", "µg/l"),
    "Sb": ("antimon", "Antimon", "pollutants", "µg/l"),
    "As": ("arsen", "Arsen", "pollutants", "µg/l"),
    "Al": ("aluminium", "Aluminium", "pollutants", "µg/l"),
    "Pb": ("blei", "Blei", "pollutants", "µg/l"),
    "Ti": ("titan", "Titan", "pollutants", "µg/l"),
    "Cu": ("kupfer", "Kupfer", "trace_elements", "µg/l"),
    "Na": ("natrium", "Natrium", "major_elements", "mg/l"),
    "Ca": ("calcium", "Calcium", "major_elements", "mg/l"),
    "Mg": ("magnesium", "Magnesium", "major_elements", "mg/l"),
    "K": ("kalium", "Kalium", "major_elements", "mg/l"),
    "Br": ("bromid", "Bromid", "major_elements", "mg/l"),
    "B": ("bor", "Bor", "major_elements", "mg/l"),
    "Sr": ("strontium", "Strontium", "major_elements", "mg/l"),
    # TRITON reports elemental sulfur. Keep this separate from Oceamo sulfate,
    # but share it with the existing Fauna Marin / ATI elemental-sulfur key.
    "S": ("schwefel", "Schwefel", "major_elements", "mg/l"),
    "Li": ("lithium", "Lithium", "trace_elements", "µg/l"),
    "Ni": ("nickel", "Nickel", "trace_elements", "µg/l"),
    "Mo": ("molybdaen", "Molybdän", "trace_elements", "µg/l"),
    "V": ("vanadium", "Vanadium", "trace_elements", "µg/l"),
    "Zn": ("zink", "Zink", "trace_elements", "µg/l"),
    "Mn": ("mangan", "Mangan", "trace_elements", "µg/l"),
    "I": ("iod", "Iod", "trace_elements", "µg/l"),
    "Cr": ("chrom", "Chrom", "trace_elements", "µg/l"),
    "Co": ("cobalt", "Cobalt", "trace_elements", "µg/l"),
    "Fe": ("eisen", "Eisen", "trace_elements", "µg/l"),
    "Ba": ("barium", "Barium", "trace_elements", "µg/l"),
    # Present in the tested 2015 layout. Keep the shared Reef ICP category/key
    # used by Fauna Marin and ATI so cross-provider history remains compatible.
    "Be": ("beryllium", "Beryllium", "pollutants", "µg/l"),
    "Si": ("silicium", "Silicium", "nutrients", "µg/l"),
    "P": ("gesamtphosphor_icp", "Gesamtphosphor (ICP)", "nutrients", "µg/l"),
    "PO4": ("phosphat", "Phosphat", "nutrients", "mg/l"),
}

_TRITON_LEGACY_CATEGORY_HEADINGS = {
    "ungewünschte schwermetalle": "pollutants",
    "ungewuenschte schwermetalle": "pollutants",
    "macro-elemente": "major_elements",
    "makro-elemente": "major_elements",
    "li-gruppe": "trace_elements",
    "i-gruppe": "trace_elements",
    "fe-gruppe": "trace_elements",
    "ba-gruppe": "trace_elements",
    "si-gruppe": "nutrients",
    "nährstoff-gruppe": "nutrients",
    "naehrstoff-gruppe": "nutrients",
}

_TRITON_LEGACY_ROW_RE = re.compile(
    r"^(?P<symbol>PO4|[A-Z][a-z]?)\s+"
    r"(?P<value>-?\d+(?:[.,]\d+)?)\s+"
    r"(?P<unit>mg/[lL]|µg/[lL]|μg/[lL]|ug/[lL])\s+"
    r"(?P<target>-?\d+(?:[.,]\d+)?)\s+"
    r"(?P<target_unit>mg/[lL]|µg/[lL]|μg/[lL]|ug/[lL])\s+"
    r"(?P<deviation>-?\d+(?:[.,]\d+)?)\s+"
    r"(?P<volume>\d+(?:[.,]\d+)?)\s+"
    r"(?P<one_time>\d+(?:[.,]\d+)?)(?:\s*mL)?\s+"
    r"(?P<daily>\d+(?:[.,]\d+)?)(?:\s*mL)?$"
)

_TRITON_LEGACY_STATUS_COLORS: tuple[
    tuple[tuple[float, float, float], str], ...
] = (
    ((0.000, 0.769, 0.153), "ok"),
    ((0.890, 0.878, 0.196), "warning"),
    ((0.890, 0.196, 0.196), "critical"),
)


# ATI's current laboratory PDF format is laid out as small blocks rather than
# conventional rows: symbol, analyte name, measured value, ideal value, then
# the laboratory's textual assessment. The canonical key/category choices
# below intentionally follow Reef ICP's existing cross-provider model. That
# lets directly comparable values share one Home Assistant statistic even when
# ATI places them under a differently named visual section.
#
# Tuple: (key, display name, category, normalized unit)
_ATI_ANALYTES: dict[str, tuple[str, str, str, str]] = {
    "Sal. total": ("salinitaet", "Salinität", "basic", "psu"),
    "KH": ("alkalinitaet", "Alkalinität", "basic", "dKH"),
    "Cl": ("chlorid", "Chlorid", "major_elements", "mg/l"),
    "Na": ("natrium", "Natrium", "major_elements", "mg/l"),
    "Mg": ("magnesium", "Magnesium", "major_elements", "mg/l"),
    "S": ("schwefel", "Schwefel", "major_elements", "mg/l"),
    "Ca": ("calcium", "Calcium", "major_elements", "mg/l"),
    "K": ("kalium", "Kalium", "major_elements", "mg/l"),
    "Br": ("bromid", "Bromid", "major_elements", "mg/l"),
    "Sr": ("strontium", "Strontium", "major_elements", "mg/l"),
    "B": ("bor", "Bor", "major_elements", "mg/l"),
    # Oceamo exposes fluoride in its trace-element section. Keep the canonical
    # category so ATI and Oceamo use the same history statistic.
    "F": ("fluorid", "Fluorid", "trace_elements", "mg/l"),
    "Li": ("lithium", "Lithium", "trace_elements", "µg/l"),
    "Si": ("silicium", "Silicium", "nutrients", "µg/l"),
    "I": ("iod", "Iod", "trace_elements", "µg/l"),
    "Ba": ("barium", "Barium", "trace_elements", "µg/l"),
    "Mo": ("molybdaen", "Molybdän", "trace_elements", "µg/l"),
    "Ni": ("nickel", "Nickel", "trace_elements", "µg/l"),
    "Mn": ("mangan", "Mangan", "trace_elements", "µg/l"),
    "As": ("arsen", "Arsen", "pollutants", "µg/l"),
    "Be": ("beryllium", "Beryllium", "pollutants", "µg/l"),
    "Cr": ("chrom", "Chrom", "trace_elements", "µg/l"),
    "Co": ("cobalt", "Cobalt", "trace_elements", "µg/l"),
    "Fe": ("eisen", "Eisen", "trace_elements", "µg/l"),
    "Cu": ("kupfer", "Kupfer", "trace_elements", "µg/l"),
    "Se": ("selen", "Selen", "trace_elements", "µg/l"),
    "Ag": ("silber", "Silber", "pollutants", "µg/l"),
    "V": ("vanadium", "Vanadium", "trace_elements", "µg/l"),
    "Zn": ("zink", "Zink", "trace_elements", "µg/l"),
    "Sn": ("zinn", "Zinn", "trace_elements", "µg/l"),
    "Rb": ("rubidium", "Rubidium", "trace_elements", "µg/l"),
    "Al": ("aluminium", "Aluminium", "pollutants", "µg/l"),
    "Sb": ("antimon", "Antimon", "pollutants", "µg/l"),
    "Bi": ("bismuth", "Bismuth", "pollutants", "µg/l"),
    "Cd": ("cadmium", "Cadmium", "pollutants", "µg/l"),
    "Ga": ("gallium", "Gallium", "pollutants", "µg/l"),
    "Ge": ("germanium", "Germanium", "pollutants", "µg/l"),
    "La": ("lanthan", "Lanthan", "pollutants", "µg/l"),
    "Pb": ("blei", "Blei", "pollutants", "µg/l"),
    "Hg": ("quecksilber", "Quecksilber", "pollutants", "µg/l"),
    "Nd": ("neodym", "Neodym", "pollutants", "µg/l"),
    "Nb": ("niob", "Niob", "pollutants", "µg/l"),
    "Te": ("tellur", "Tellur", "pollutants", "µg/l"),
    "Tl": ("thallium", "Thallium", "pollutants", "µg/l"),
    "Ti": ("titan", "Titan", "pollutants", "µg/l"),
    "W": ("wolfram", "Wolfram", "pollutants", "µg/l"),
    "Zr": ("zirkonium", "Zirkonium", "pollutants", "µg/l"),
    "P": ("gesamtphosphor_icp", "Gesamtphosphor (ICP)", "nutrients", "µg/l"),
    "PO4": ("phosphat", "Phosphat", "nutrients", "mg/l"),
    "NO3": ("nitrat", "Nitrat", "nutrients", "mg/l"),
    "NO2": ("nitrit", "Nitrit", "nutrients", "mg/l"),
}

_ATI_CATEGORY_HEADINGS = {
    "basiswerte": "basic",
    "base elements": "basic",
    "base values": "basic",
    "mengenelemente": "major_elements",
    "major elements": "major_elements",
    "spurenelemente": "trace_elements",
    "minor elements": "trace_elements",
    "trace elements": "trace_elements",
    "schadstoffe": "pollutants",
    "pollutants": "pollutants",
    "nährstoffe": "nutrients",
    "naehrstoffe": "nutrients",
    "nutrients": "nutrients",
    "osmose": "osmosis",
    "osmosis": "osmosis",
}

_ATI_VALUE_RE = re.compile(
    r"^(?P<value>---|n\.?n\.?|n\.?d\.?|u\.?|<\s*-?\d+(?:[.,]\d+)?|>\s*-?\d+(?:[.,]\d+)?|-?\d+(?:[.,]\d+)?)"
    r"\s*(?P<unit>PSU|psu|°?dKH|mg/l|µg/l|μg/l|ug/l|ng/l|µg/L|mg/L|ng/L)?$",
    re.IGNORECASE,
)

_ATI_IDEAL_RE = re.compile(
    r"^(?:Idealwert|Ideal value)\s*:\s*"
    r"(?P<value>-?\d+(?:[.,]\d+)?)\s*"
    r"(?P<unit>PSU|psu|°?dKH|mg/l|µg/l|μg/l|ug/l|ng/l|µg/L|mg/L|ng/L)?$",
    re.IGNORECASE,
)


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


def _validated_iso_date(value: str) -> str:
    """Validate and normalize an ISO YYYY-MM-DD date."""
    return datetime.strptime(value.strip(), "%Y-%m-%d").date().isoformat()


def _analysis_date_from_filename(path: str | Path) -> str | None:
    """Extract a plausible calendar date from a PDF filename.

    Supported forms include YYYYMMDD, YYYY-MM-DD, YYYY_MM_DD, DD.MM.YYYY,
    DD-MM-YYYY and DD_MM_YYYY. Invalid calendar dates are ignored.
    """
    name = Path(path).name
    patterns: tuple[tuple[str, str], ...] = (
        (r"(?<!\d)((?:19|20)\d{2}\d{2}\d{2})(?!\d)", "%Y%m%d"),
        (r"(?<!\d)((?:19|20)\d{2}[-_.]\d{2}[-_.]\d{2})(?!\d)", None),
        (r"(?<!\d)(\d{2}[.-]\d{2}[.-](?:19|20)\d{2})(?!\d)", None),
        (r"(?<!\d)(\d{2}_\d{2}_(?:19|20)\d{2})(?!\d)", None),
    )

    for pattern, fmt in patterns:
        match = re.search(pattern, name)
        if not match:
            continue
        raw = match.group(1)
        try:
            if fmt == "%Y%m%d":
                parsed = datetime.strptime(raw, fmt).date()
            elif re.match(r"^(?:19|20)\d{2}", raw):
                parsed = datetime.strptime(
                    raw.replace("_", "-").replace(".", "-"),
                    "%Y-%m-%d",
                ).date()
            else:
                parsed = datetime.strptime(
                    raw.replace("_", ".").replace("-", "."),
                    "%d.%m.%Y",
                ).date()
            return parsed.isoformat()
        except ValueError:
            continue
    return None


def _date_from_sample_taken(value: Any) -> str | None:
    """Return the calendar date from an already parsed sample timestamp."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text).date().isoformat()
    except ValueError:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
            try:
                return _validated_iso_date(text)
            except ValueError:
                return None
    return None


def _ensure_analysis_date(
    metadata: dict[str, Any],
    path: str | Path,
    analysis_date_override: str | None = None,
) -> None:
    """Ensure every supported report has a trustworthy analysis date.

    Priority:
    1. A provider-specific date parsed from the report itself.
    2. A parsed sample-taking timestamp when that is the only report date.
    3. A plausible date embedded in the original PDF filename.
    4. A date explicitly selected by the user in Home Assistant.

    PDF CreationDate metadata is deliberately ignored because it only tells us
    when the PDF file was created/exported and can differ from the laboratory
    analysis or sampling date.
    """
    if metadata.get("analysis_date"):
        metadata.setdefault("analysis_date_source", "document")
        return

    if sample_date := _date_from_sample_taken(metadata.get("sample_taken")):
        metadata["analysis_date"] = sample_date
        metadata["analysis_date_source"] = "sample_taken"
        return

    if filename_date := _analysis_date_from_filename(path):
        metadata["analysis_date"] = filename_date
        metadata["analysis_date_source"] = "filename"
        return

    if analysis_date_override is not None:
        try:
            metadata["analysis_date"] = _validated_iso_date(
                str(analysis_date_override)
            )
        except ValueError as err:
            raise MissingAnalysisDateError(
                "The selected analysis date is invalid."
            ) from err
        metadata["analysis_date_source"] = "manual"
        return

    provider_name = str(metadata.get("provider_name") or "ICP")
    raise MissingAnalysisDateError(
        f"{provider_name} report does not contain a trustworthy analysis date."
    )


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

    if target_type == "not_detectable":
        # A numeric result against a laboratory "not detectable" target is a
        # real detection. Mark it as attention-worthy without inventing a
        # critical threshold.
        return {"severity": "warning", "direction": "high"}

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
    """Parse one classic or ICP-MS Oceamo table row."""
    normalized = " ".join(line.split())
    match = _OCEAMO_ROW_RE.match(normalized)
    if not match:
        return None

    source_name = match.group("name").strip()
    canonical = _OCEAMO_CANONICAL_NAMES.get(_slug(source_name))
    if canonical is None:
        key = _slug(source_name)
        display_name = source_name
    else:
        key, display_name = canonical

    raw_value = match.group("value")
    unit = match.group("unit") or match.group("target_unit")
    if unit is not None:
        unit = unit.replace("μ", "µ").replace("/L", "/l")
        if unit in {"m^-1", "m⁻¹", "1/m"}:
            unit = "m-1"

    measurement: dict[str, Any] = {
        "key": key,
        "name": display_name,
        "source_name": source_name,
        "category": category,
        "raw_value": raw_value,
        "source_raw_value": raw_value,
        "unit": unit,
        "source_unit": unit,
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


def _oceamo_report_type(text: str) -> str:
    """Distinguish Oceamo classic ICP from the ICP-MS report family."""
    normalized = " ".join(text.split()).casefold()
    head = normalized[:1800]
    if re.search(r"\bmsr\d{4,}\b", normalized):
        return "reef_icp_ms"
    if "icp-ms" in head or "icp ms" in head:
        return "reef_icp_ms"
    return "classic_icp"


def _extract_oceamo_metadata(text: str, report_type: str) -> dict[str, Any]:
    """Extract German or English Oceamo metadata while omitting customer details."""
    metadata: dict[str, Any] = {
        "provider": PROVIDER_OCEAMO,
        "provider_name": PROVIDER_NAMES[PROVIDER_OCEAMO],
        "report_type": report_type,
    }

    date_patterns = (
        r"Analysedatum:\s*(\d{2}\.\d{2}\.\d{4})",
        r"Date of Analysis\s*:?\s*(\d{2}\.\d{2}\.\d{4})",
    )
    for pattern in date_patterns:
        if match := re.search(pattern, text, flags=re.IGNORECASE):
            metadata["analysis_date"] = _parse_date(match.group(1))
            break

    number_patterns = (
        r"Analysenummer:\s*([A-Za-z]{2,4}\d+)",
        r"Analysis No\.?\s*:?\s*([A-Za-z]{2,4}\d+)",
        r"Analysis Number\s*:?\s*([A-Za-z]{2,4}\d+)",
    )
    for pattern in number_patterns:
        if match := re.search(pattern, text, flags=re.IGNORECASE):
            report_id = match.group(1).upper()
            metadata["analysis_number"] = report_id
            metadata["provider_report_id"] = report_id
            break

    sample_patterns = (
        r"Probennahme:\s*(\d{2}\.\d{2}\.\d{4}\s*-\s*\d{2}:\d{2})",
        r"Date of Sampling\s*:?\s*(\d{2}\.\d{2}\.\d{4}\s*-\s*\d{2}:\d{2})",
    )
    for pattern in sample_patterns:
        if match := re.search(pattern, text, flags=re.IGNORECASE):
            metadata["sample_taken"] = _parse_sample_datetime(match.group(1))
            break

    tank_patterns = (
        r"Beckentyp:\s*(.+?)(?:\n|$)",
        r"Tank\s*:\s*(.+?)(?:\n|$)",
    )
    for pattern in tank_patterns:
        if match := re.search(pattern, text, flags=re.IGNORECASE):
            metadata["tank_type"] = " ".join(match.group(1).split())
            break

    return metadata


def _extract_oceamo_interpretation(text: str) -> str | None:
    """Extract Oceamo's German or English interpretation section."""
    match = re.search(
        r"(?:Interpretation|Evaluation)\s+(.*?)\s+"
        r"(?:Produktempfehlungen|Product Recommendations|Product recommendation)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return None
    return " ".join(match.group(1).split())


def _extract_oceamo_product_recommendations(text: str) -> str | None:
    """Extract Oceamo's German or English product recommendation block."""
    match = re.search(
        r"(?:Produktempfehlungen|Product Recommendations|Product recommendation)\s+"
        r"(.*?)(?:Advanced Reef Chemistry|ICP\s*-?\s*MS\s+by\s+oceamo|$)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return None
    value = " ".join(match.group(1).split())
    return value or None


def parse_oceamo_pdf(
    path: str | Path,
    analysis_date_override: str | None = None,
) -> dict[str, Any]:
    """Parse classic Oceamo and Oceamo Reef ICP-MS PDF reports."""
    source_path = Path(path)
    try:
        reader = PdfReader(str(source_path))
    except Exception as err:  # noqa: BLE001
        raise IcpParseError("The uploaded file is not a readable PDF.") from err

    if not reader.pages:
        raise IcpParseError("The PDF contains no pages.")

    page_texts = [(page.extract_text() or "") for page in reader.pages]
    full_text = "\n".join(page_texts)
    normalized = " ".join(full_text.split()).casefold()

    has_oceamo_brand = "oceamo" in normalized
    has_report_heading = (
        "analysebericht" in normalized
        or "analysis report" in normalized
    )
    has_report_id = (
        "analysenummer" in normalized
        or "analysis no" in normalized
        or "analysis number" in normalized
        or re.search(r"\b(?:oc|msr)\d{4,}\b", normalized) is not None
    )
    if not (has_oceamo_brand and has_report_heading and has_report_id):
        raise IcpParseError("The PDF does not look like a supported Oceamo analysis report.")

    report_type = _oceamo_report_type(full_text)
    metadata = _extract_oceamo_metadata(full_text, report_type)
    measurements: list[dict[str, Any]] = []
    current_category: str | None = None

    for page, page_text in zip(reader.pages, page_texts, strict=True):
        page_measurements: list[dict[str, Any]] = []

        for raw_line in page_text.splitlines():
            line = " ".join(raw_line.split())
            if not line:
                continue

            if line.casefold() in {
                "interpretation",
                "evaluation",
                "produktempfehlungen",
                "product recommendations",
            }:
                break

            category = _OCEAMO_CATEGORY_LOOKUP.get(line.casefold())
            if category is not None:
                current_category = category
                continue

            if current_category is None:
                continue

            if measurement := _parse_oceamo_measurement_line(line, current_category):
                page_measurements.append(measurement)

        # Oceamo draws one rating icon per table row in the tested layouts.
        # Known artwork is authoritative. If newer ICP-MS artwork changes, a
        # conservative range/limit fallback is used instead of inventing a
        # critical threshold for exact ideal values.
        page_statuses = _extract_oceamo_status_sequence(page, reader)
        for index, measurement in enumerate(page_measurements):
            if index < len(page_statuses):
                measurement["status"] = page_statuses[index]
            else:
                measurement["status"] = _status_from_reference(
                    measurement.get("value"),
                    str(measurement.get("raw_value", "")),
                    measurement.get("target", {}),
                )

        measurements.extend(page_measurements)

    # Some PDF generators can repeat a table header/page fragment. Keep the
    # first occurrence of each category/key pair while retaining RO/DI values
    # separately through their distinct category.
    deduplicated: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for measurement in measurements:
        identity = (
            str(measurement.get("category", "unknown")),
            str(measurement.get("key", "unknown")),
        )
        if identity in seen:
            continue
        seen.add(identity)
        deduplicated.append(measurement)
    measurements = deduplicated

    if not measurements:
        raise IcpParseError("No ICP measurements were found in the report.")
    if "analysis_number" not in metadata:
        raise IcpParseError("The analysis number could not be found.")
    _ensure_analysis_date(metadata, source_path, analysis_date_override)

    return {
        "schema_version": 2,
        "provider": PROVIDER_OCEAMO,
        "provider_name": PROVIDER_NAMES[PROVIDER_OCEAMO],
        "report_type": report_type,
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
        "report_type": "reef_icp",
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


def parse_fauna_marin_pdf(
    path: str | Path,
    analysis_date_override: str | None = None,
) -> dict[str, Any]:
    """Parse the tested Fauna Marin Reef ICP one-page PDF format."""
    source_path = Path(path)
    try:
        reader = PdfReader(str(source_path))
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
    _ensure_analysis_date(metadata, source_path, analysis_date_override)

    return {
        "schema_version": 2,
        "provider": PROVIDER_FAUNA_MARIN,
        "provider_name": PROVIDER_NAMES[PROVIDER_FAUNA_MARIN],
        "report_type": "reef_icp",
        "metadata": metadata,
        "measurements": measurements,
        "interpretation": None,
        # Fauna Marin recommendations are stored per measurement because the
        # PDF provides amount, duration and product in the corresponding row.
        "product_recommendations": None,
    }




def _normalize_triton_unit(unit: str) -> str:
    """Normalize legacy TRITON concentration units."""
    value = unit.replace("μ", "µ").replace("ug", "µg").replace("/L", "/l")
    return value


def _triton_unit_factor(source_unit: str, target_unit: str) -> float | None:
    """Return a concentration conversion factor for legacy TRITON rows."""
    if source_unit == target_unit:
        return 1.0
    factors = {
        ("mg/l", "µg/l"): 1000.0,
        ("µg/l", "mg/l"): 0.001,
    }
    return factors.get((source_unit, target_unit))


def _triton_legacy_status_sequence(
    page: Any, reader: PdfReader
) -> list[dict[str, str | None]]:
    """Read legacy TRITON traffic-light rectangles in drawing order."""
    try:
        content = ContentStream(page.get_contents(), reader)
    except Exception:  # noqa: BLE001
        return []

    fill: tuple[float, float, float] | None = None
    statuses: list[dict[str, str | None]] = []

    for operands, operator in content.operations:
        if operator == b"rg" and len(operands) >= 3:
            fill = tuple(float(value) for value in operands[:3])
            continue
        if operator != b"re" or fill is None or len(operands) < 4:
            continue

        _x, _y, width, height = (float(value) for value in operands[:4])

        # In the tested 2014 FPDF layout each warning light is a 17.01 x 8.50
        # point rectangle. Restricting the geometry prevents ordinary table
        # backgrounds from being interpreted as status lights.
        if abs(abs(width) - 17.01) > 0.25 or abs(abs(height) - 8.50) > 0.25:
            continue

        for reference, severity in _TRITON_LEGACY_STATUS_COLORS:
            if all(abs(fill[index] - reference[index]) <= 0.02 for index in range(3)):
                statuses.append({"severity": severity, "direction": None})
                break

    return statuses


def _triton_status_with_direction(
    status: dict[str, str | None] | None,
    deviation: float,
) -> dict[str, str | None]:
    """Add high/low direction to a TRITON warning-light severity."""
    if status is None:
        return {"severity": "unknown", "direction": None}

    severity = status.get("severity") or "unknown"
    if severity == "ok":
        return {"severity": "ok", "direction": None}

    direction: str | None
    if deviation > 0:
        direction = "high"
    elif deviation < 0:
        direction = "low"
    else:
        direction = None

    return {"severity": severity, "direction": direction}


def _extract_triton_legacy_date(
    path: Path, _reader: PdfReader, text: str
) -> tuple[str | None, str | None]:
    """Find a trustworthy date for a legacy TRITON report.

    The tested 2014 PDF does not print a report date in its table. Prefer a
    date embedded in the filename, then a date printed in the document.
    PDF CreationDate metadata is intentionally ignored.
    """
    filename_match = re.search(r"(?<!\d)((?:19|20)\d{6})(?!\d)", path.name)
    if filename_match:
        try:
            return (
                datetime.strptime(filename_match.group(1), "%Y%m%d")
                .date()
                .isoformat(),
                "filename",
            )
        except ValueError:
            pass

    text_match = re.search(
        r"\b(\d{2}[./]\d{2}[./]\d{4}|\d{4}-\d{2}-\d{2})\b",
        text,
    )
    if text_match:
        value = text_match.group(1)
        try:
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                parsed = datetime.strptime(value, "%Y-%m-%d").date()
            else:
                parsed = datetime.strptime(value.replace("/", "."), "%d.%m.%Y").date()
            return parsed.isoformat(), "document"
        except ValueError:
            pass

    return None, None


def _triton_legacy_printed_id(text: str) -> str | None:
    """Return a printed legacy TRITON report ID when the layout provides one."""
    match = re.search(
        r"Auswertung\s*\(ICP-OES\)\s*\((?P<report_id>[A-Za-z0-9-]+)\)",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    return match.group("report_id").strip() or None


def _triton_legacy_report_id(text: str) -> str:
    """Return a provider-local ID, preferring the ID printed in the PDF."""
    if printed_id := _triton_legacy_printed_id(text):
        return printed_id
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    return f"legacy-{digest}"


def _is_triton_legacy_layout(normalized_text: str) -> bool:
    """Recognize the tested 2014/2015 TRITON legacy table variants."""
    common_markers = (
        "auswertung (icp-oes)",
        "warnampel",
        "www.triton-lab.de",
    )
    if not all(marker in normalized_text for marker in common_markers):
        return False

    dosing_header = (
        "einmalige dosierung / ml" in normalized_text
        or "korrektur dosierung / ml" in normalized_text
    )
    return dosing_header


def _parse_triton_legacy_measurement(
    line: str,
    status: dict[str, str | None] | None,
) -> dict[str, Any] | None:
    """Normalize one legacy TRITON table row."""
    match = _TRITON_LEGACY_ROW_RE.match(" ".join(line.split()))
    if not match:
        return None

    symbol = match.group("symbol")
    analyte = _TRITON_LEGACY_ANALYTES.get(symbol)
    if analyte is None:
        return None

    key, name, category, canonical_unit = analyte
    source_unit = _normalize_triton_unit(match.group("unit"))
    target_source_unit = _normalize_triton_unit(match.group("target_unit"))
    factor = _triton_unit_factor(source_unit, canonical_unit)
    target_factor = _triton_unit_factor(target_source_unit, canonical_unit)
    if factor is None or target_factor is None:
        return None

    source_value = _decimal(match.group("value"))
    source_target = _decimal(match.group("target"))
    value = source_value * factor
    target_value = source_target * target_factor
    deviation = _decimal(match.group("deviation")) * factor
    aquarium_volume_l = _decimal(match.group("volume"))
    one_time_ml = _decimal(match.group("one_time"))
    daily_ml = _decimal(match.group("daily"))

    measurement: dict[str, Any] = {
        "key": key,
        "name": name,
        "source_name": symbol,
        "source_symbol": symbol,
        "category": category,
        "raw_value": _normalized_number(value),
        "source_raw_value": match.group("value"),
        "unit": canonical_unit,
        "source_unit": source_unit,
        "target": {"type": "exact", "value": target_value},
        "value": value,
        "detected": True,
        "determined": True,
        "status": _triton_status_with_direction(status, deviation),
        "provider": PROVIDER_TRITON,
        "provider_name": PROVIDER_NAMES[PROVIDER_TRITON],
        "source_deviation": deviation,
        "aquarium_volume_l": aquarium_volume_l,
    }

    if one_time_ml > 0 or daily_ml > 0:
        measurement["recommendation"] = {
            "type": "dose",
            "one_time_ml": one_time_ml,
            "daily_ml": daily_ml,
            "aquarium_volume_l": aquarium_volume_l,
        }

    return measurement


def parse_triton_legacy_pdf(
    path: str | Path,
    analysis_date_override: str | None = None,
) -> dict[str, Any]:
    """Parse the tested legacy TRITON ICP-OES table format."""
    source_path = Path(path)
    try:
        reader = PdfReader(str(source_path))
    except Exception as err:  # noqa: BLE001
        raise IcpParseError("The uploaded file is not a readable PDF.") from err

    if not reader.pages:
        raise IcpParseError("The PDF contains no pages.")

    page_texts = [(page.extract_text() or "") for page in reader.pages]
    full_text = "\n".join(page_texts)
    normalized = " ".join(full_text.split()).casefold()

    if not _is_triton_legacy_layout(normalized):
        raise IcpParseError(
            "The PDF does not look like a supported legacy TRITON ICP-OES report."
        )

    measurements: list[dict[str, Any]] = []
    volumes: list[float] = []

    for page, page_text in zip(reader.pages, page_texts, strict=True):
        statuses = _triton_legacy_status_sequence(page, reader)
        status_index = 0

        for raw_line in page_text.splitlines():
            line = " ".join(raw_line.split())
            if not line:
                continue

            # In the tested 2015 export, the unit label from the dosing header
            # is glued to the first analyte of each table (for example
            # ``mLHg`` or ``mLNa``). Remove only that very specific prefix so
            # the first row is parsed instead of silently dropped.
            line = re.sub(r"^mL(?=(?:PO4|[A-Z][a-z]?)\s)", "", line)

            if line.casefold() in _TRITON_LEGACY_CATEGORY_HEADINGS:
                continue

            row_match = _TRITON_LEGACY_ROW_RE.match(line)
            if row_match is None:
                continue

            status = statuses[status_index] if status_index < len(statuses) else None
            status_index += 1

            measurement = _parse_triton_legacy_measurement(line, status)
            if measurement is not None:
                measurements.append(measurement)
                volumes.append(float(measurement["aquarium_volume_l"]))

    if not measurements:
        raise IcpParseError("No TRITON ICP measurements were found in the report.")

    analysis_date, date_source = _extract_triton_legacy_date(
        source_path, reader, full_text
    )

    printed_id = _triton_legacy_printed_id(full_text)
    provider_report_id = _triton_legacy_report_id(full_text)
    if "korrektur dosierung / ml" in normalized:
        layout_variant = "correction_maintenance"
    else:
        layout_variant = "one_time_daily"

    metadata: dict[str, Any] = {
        "provider": PROVIDER_TRITON,
        "provider_name": PROVIDER_NAMES[PROVIDER_TRITON],
        "report_type": "triton_legacy_icp",
        "provider_report_id": provider_report_id,
        "legacy_layout_variant": layout_variant,
    }
    if analysis_date is not None:
        metadata["analysis_date"] = analysis_date
        metadata["analysis_date_source"] = date_source

    _ensure_analysis_date(metadata, source_path, analysis_date_override)
    compact_date = str(metadata["analysis_date"]).replace("-", "")
    metadata["analysis_number"] = printed_id or f"TRITON-{compact_date}"

    if volumes:
        rounded = {round(value, 6) for value in volumes}
        if len(rounded) == 1:
            metadata["aquarium_volume_l"] = volumes[0]

    return {
        "schema_version": 2,
        "provider": PROVIDER_TRITON,
        "provider_name": PROVIDER_NAMES[PROVIDER_TRITON],
        "report_type": "triton_legacy_icp",
        "metadata": metadata,
        "measurements": measurements,
        "interpretation": None,
        "product_recommendations": None,
    }


def _normalize_ati_unit(unit: str | None, fallback: str) -> str:
    """Normalize ATI unit spellings to Reef ICP's existing unit strings."""
    if not unit:
        return fallback
    value = unit.replace("μ", "µ").replace("ug", "µg")
    value = value.replace("/L", "/l")
    if value.lower() == "psu":
        return "psu"
    if value.lower().endswith("dkh"):
        return "dKH"
    return value


def _ati_report_type(text: str) -> str:
    """Return an ATI report-type hint without relying on it for parsing."""
    normalized = " ".join(text.split()).casefold()
    if "ultimate-ms" in normalized or "ultimate ms" in normalized or "icp-ms" in normalized:
        return "ultimate_ms"
    if "icp-oes pro" in normalized or "laboranalyse pro" in normalized:
        return "pro"
    if "icp-oes standard" in normalized or "laboranalyse standard" in normalized:
        return "standard"
    return "ati_icp"


def _parse_ati_date(value: str) -> str:
    """Parse common German/English date representations used by ATI."""
    value = value.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    if "." in value:
        return datetime.strptime(value, "%d.%m.%Y").date().isoformat()
    if "/" in value:
        first, second, _year = value.split("/", 2)
        # English ATI reports commonly use month/day/year. If the first field
        # cannot be a month, fall back to day/month/year.
        fmt = "%d/%m/%Y" if int(first) > 12 else "%m/%d/%Y"
        return datetime.strptime(value, fmt).date().isoformat()
    raise ValueError(f"Unsupported ATI date: {value}")


def _extract_ati_metadata(text: str) -> dict[str, Any]:
    """Extract ATI metadata from the current lab PDF layout."""
    metadata: dict[str, Any] = {
        "provider": PROVIDER_ATI,
        "provider_name": PROVIDER_NAMES[PROVIDER_ATI],
        "report_type": _ati_report_type(text),
    }

    if match := re.search(r"\(ID:\s*([A-Za-z0-9-]+)\)", text, flags=re.IGNORECASE):
        metadata["analysis_number"] = match.group(1)
        metadata["provider_report_id"] = match.group(1)
    elif match := re.search(r"(?:Barcode|Analysis ID|Analyse-ID)\s*:?\s*([A-Za-z0-9-]{4,})", text, flags=re.IGNORECASE):
        metadata["analysis_number"] = match.group(1)
        metadata["provider_report_id"] = match.group(1)

    flat = " ".join(text.split())

    if match := re.search(
        r"(?:Aquarium|Aquarium name)\s+(.+?)\s+(?:Netto-Volumen|Net volume)",
        flat,
        flags=re.IGNORECASE,
    ):
        metadata["tank_name"] = match.group(1).strip()

    if match := re.search(
        r"(?:Grund der Analyse|Reason for analysis)\s+(.+?)\s+(?:Barcode|Analysis ID|Analyse-ID)",
        flat,
        flags=re.IGNORECASE,
    ):
        metadata["analysis_reason"] = match.group(1).strip()

    if match := re.search(
        r"Barcode\s+([A-Z0-9-]+)\s*\(ID:",
        flat,
        flags=re.IGNORECASE,
    ):
        metadata["barcode"] = match.group(1).strip()

    if match := re.search(r"Netto-Volumen\s+(\d+(?:[.,]\d+)?)\s*Liter", flat, flags=re.IGNORECASE):
        metadata["aquarium_volume_l"] = _decimal(match.group(1))
    elif match := re.search(r"Net volume\s+(\d+(?:[.,]\d+)?)\s*(?:liters?|litres?|l)\b", flat, flags=re.IGNORECASE):
        metadata["aquarium_volume_l"] = _decimal(match.group(1))

    # ATI's PDF places the three labels first and the corresponding three dates
    # directly afterwards. Keep all three when available, but use the evaluated
    # date as the analysis date. Do not invent a sample-taking timestamp.
    header_match = re.search(
        r"(?:Erstellt|Created).*?(?:Im Labor angekommen|Arrived at laboratory).*?"
        r"(?:Ausgewertet|Evaluated)(?P<tail>.*?)(?:Qualitätsbewertung|Quality assessment|Auswertung(?: Basis)? Salzwasser|Saltwater evaluation)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    date_source = header_match.group("tail") if header_match else text[:2500]
    dates = re.findall(
        r"\b(\d{2}[./]\d{2}[./]\d{4}|\d{4}-\d{2}-\d{2})\b",
        date_source,
    )
    if len(dates) >= 3:
        metadata["created_date"] = _parse_ati_date(dates[0])
        metadata["received_date"] = _parse_ati_date(dates[1])
        metadata["evaluated_date"] = _parse_ati_date(dates[2])
        metadata["analysis_date"] = metadata["evaluated_date"]
    elif dates:
        metadata["analysis_date"] = _parse_ati_date(dates[-1])
        metadata["evaluated_date"] = metadata["analysis_date"]

    return metadata


def _ati_status_from_text(lines: list[str]) -> dict[str, str | None]:
    """Map ATI's textual assessment labels to the shared status model."""
    text = " ".join(lines).casefold()

    low_critical = ("zu niedrig", "too low", "critical low")
    high_critical = ("zu hoch", "too high", "critical high")
    low_warning = ("wenig", "niedrig", "low", "decreased")
    high_warning = ("erhöht", "erhoeht", "increased", "high")

    if any(marker in text for marker in low_critical):
        return {"severity": "critical", "direction": "low"}
    if any(marker in text for marker in high_critical):
        return {"severity": "critical", "direction": "high"}
    if "kritisch" in text or "critical" in text:
        direction = "low" if any(marker in text for marker in low_warning) else "high" if any(marker in text for marker in high_warning) else None
        return {"severity": "critical", "direction": direction}
    if any(marker in text for marker in low_warning):
        return {"severity": "warning", "direction": "low"}
    if any(marker in text for marker in high_warning):
        return {"severity": "warning", "direction": "high"}
    if "achtung" in text or "attention" in text:
        return {"severity": "warning", "direction": None}
    if "top" in text or "naturnah" in text or "near nature" in text:
        return {"severity": "ok", "direction": None}
    return {"severity": "unknown", "direction": None}


def _normalize_ati_symbol(symbol: str) -> str:
    """Normalize harmless punctuation used by ATI for some element symbols."""
    normalized = symbol.strip()
    if normalized != "Sal. total":
        normalized = normalized.rstrip(".")
    return normalized


def _ati_value_state(raw_value: str) -> tuple[float | None, bool | None, bool, str | None, float | None]:
    """Convert ATI numeric/non-detect/qualified values without inventing zeroes."""
    normalized = raw_value.strip().casefold().replace(" ", "")
    if normalized in {"---", "n.n.", "n.n", "n.d.", "n.d", "u.", "u"}:
        return None, False, True, None, None
    if normalized.startswith(("<", ">")):
        qualifier = "less_than" if normalized.startswith("<") else "greater_than"
        bound = _decimal(normalized[1:])
        return None, True, False, qualifier, bound
    return _decimal(normalized), True, True, None, None


def _ati_unit_factor(source_unit: str, target_unit: str) -> float | None:
    """Return a safe concentration conversion factor for ATI values."""
    if source_unit == target_unit:
        return 1.0
    factors = {
        ("mg/l", "µg/l"): 1000.0,
        ("µg/l", "mg/l"): 0.001,
        ("µg/l", "ng/l"): 1000.0,
        ("ng/l", "µg/l"): 0.001,
        ("mg/l", "ng/l"): 1_000_000.0,
        ("ng/l", "mg/l"): 0.000001,
    }
    return factors.get((source_unit, target_unit))


def _convert_ati_number(value: float, source_unit: str, target_unit: str) -> float | None:
    """Convert a numeric ATI value into the canonical Reef ICP unit."""
    factor = _ati_unit_factor(source_unit, target_unit)
    if factor is None:
        return None
    return value * factor


def _extract_ati_interpretation(text: str) -> str | None:
    """Extract ATI's human-readable recommended actions section."""
    match = re.search(
        r"Empfohlene Handlungen\s+(.*?)\s+Empfohlene ICP Elements Dosierung",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return None
    value = " ".join(match.group(1).split())
    return value or None


def _extract_ati_product_recommendations(text: str) -> str | None:
    """Extract ATI's ICP Elements / supplement dosing recommendation text."""
    match = re.search(
        r"Empfohlene ICP Elements Dosierung\s+(.*?)(?:\s+Diagramme(?:\s|$)|$)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return None
    value = " ".join(match.group(1).split())
    return value or None


def _parse_ati_measurements(text: str) -> list[dict[str, Any]]:
    """Parse current ATI result blocks into the provider-neutral model."""
    lines = [" ".join(line.split()) for line in text.splitlines()]
    lines = [line for line in lines if line]
    measurements: list[dict[str, Any]] = []
    current_category: str | None = None

    symbol_indices: list[tuple[int, str | None]] = []
    for index, line in enumerate(lines):
        category = _ATI_CATEGORY_HEADINGS.get(line.casefold())
        if category is not None:
            current_category = category
            continue
        if _normalize_ati_symbol(line) in _ATI_ANALYTES:
            symbol_indices.append((index, current_category))

    for position, (index, section_category) in enumerate(symbol_indices):
        source_symbol = lines[index]
        symbol = _normalize_ati_symbol(source_symbol)
        canonical = _ATI_ANALYTES[symbol]
        key, canonical_name, canonical_category, canonical_unit = canonical
        next_index = (
            symbol_indices[position + 1][0]
            if position + 1 < len(symbol_indices)
            else min(len(lines), index + 12)
        )
        block = lines[index:next_index]

        # A valid ATI measurement block has a measured value and a separate
        # Idealwert/Ideal value line. Search locally instead of assuming fixed
        # offsets because PDF text extraction order can vary slightly.
        value_match = None
        value_index = None
        ideal_match = None
        ideal_index = None
        for offset, candidate in enumerate(block[1:8], start=1):
            if value_match is None:
                maybe_value = _ATI_VALUE_RE.match(candidate)
                if maybe_value:
                    value_match = maybe_value
                    value_index = offset
                    continue
            maybe_ideal = _ATI_IDEAL_RE.match(candidate)
            if maybe_ideal:
                ideal_match = maybe_ideal
                ideal_index = offset
                break

        if value_match is None or ideal_match is None or value_index is None or ideal_index is None:
            continue

        source_raw_value = value_match.group("value")
        source_unit = _normalize_ati_unit(value_match.group("unit"), canonical_unit)
        source_ideal_value = _decimal(ideal_match.group("value"))
        ideal_unit = _normalize_ati_unit(ideal_match.group("unit"), source_unit)

        value, detected, determined, qualifier, bound = _ati_value_state(source_raw_value)

        # Normalize ATI concentrations before they reach Home Assistant so a
        # measurement can safely share one statistic with Oceamo/Fauna Marin.
        if value is not None:
            converted = _convert_ati_number(value, source_unit, canonical_unit)
            if converted is None:
                continue
            value = converted
        if bound is not None:
            converted_bound = _convert_ati_number(bound, source_unit, canonical_unit)
            if converted_bound is None:
                continue
            bound = converted_bound

        converted_ideal = _convert_ati_number(
            source_ideal_value, ideal_unit, canonical_unit
        )
        if converted_ideal is None:
            continue
        ideal_value = converted_ideal

        name = canonical_name
        if value_index >= 2:
            candidate_name = block[value_index - 1]
            if (
                _normalize_ati_symbol(candidate_name) not in _ATI_ANALYTES
                and not _ATI_VALUE_RE.match(candidate_name)
            ):
                name = candidate_name

        assessment_lines = block[ideal_index + 1 : ideal_index + 5]
        status = _ati_status_from_text(assessment_lines)

        canonical_raw_value = source_raw_value
        if source_raw_value.strip() == "---":
            # Canonical non-detect marker already understood by sensors/card.
            canonical_raw_value = "n.n."
        elif value is not None:
            canonical_raw_value = _normalized_number(value)
        elif bound is not None and qualifier is not None:
            operator = "<" if qualifier == "less_than" else ">"
            canonical_raw_value = f"{operator}{_normalized_number(bound)}"

        measurement: dict[str, Any] = {
            "key": key,
            "name": canonical_name,
            "source_name": name,
            "source_symbol": source_symbol,
            "category": (
                "osmosis"
                if section_category == "osmosis"
                else canonical_category or section_category or "unknown"
            ),
            "raw_value": canonical_raw_value,
            "source_raw_value": source_raw_value,
            "unit": canonical_unit,
            "source_unit": source_unit,
            "target": {"type": "exact", "value": ideal_value},
            "value": value,
            "detected": detected,
            "determined": determined,
            "status": status,
            "provider": PROVIDER_ATI,
            "provider_name": PROVIDER_NAMES[PROVIDER_ATI],
        }
        if qualifier is not None:
            measurement["value_qualifier"] = qualifier
            measurement["value_bound"] = bound
        measurements.append(measurement)

    # Some ATI PDFs repeat navigation/summary content. Keep the first complete
    # occurrence of each canonical key/category pair.
    deduplicated: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for measurement in measurements:
        identity = (measurement["category"], measurement["key"])
        if identity in seen:
            continue
        seen.add(identity)
        deduplicated.append(measurement)
    return deduplicated


def parse_ati_pdf(
    path: str | Path,
    analysis_date_override: str | None = None,
) -> dict[str, Any]:
    """Parse the current ATI laboratory analysis PDF layout."""
    source_path = Path(path)
    try:
        reader = PdfReader(str(source_path))
    except Exception as err:  # noqa: BLE001
        raise IcpParseError("The uploaded file is not a readable PDF.") from err

    if not reader.pages:
        raise IcpParseError("The PDF contains no pages.")

    page_texts = [(page.extract_text() or "") for page in reader.pages]
    full_text = "\n".join(page_texts)
    normalized = " ".join(full_text.split()).casefold()

    ati_brand = "ati aquaristik" in normalized or "atiaquaristik.com" in normalized
    ati_layout = (
        ("idealwert:" in normalized or "ideal value:" in normalized)
        and ("barcode" in normalized or "(id:" in normalized)
    )
    if not (ati_brand and ati_layout):
        raise IcpParseError("The PDF does not look like a supported ATI analysis report.")

    metadata = _extract_ati_metadata(full_text)
    measurements = _parse_ati_measurements(full_text)

    if not measurements:
        raise IcpParseError("No ATI ICP measurements were found in the report.")
    if "analysis_number" not in metadata:
        raise IcpParseError("The ATI analysis ID could not be found.")
    _ensure_analysis_date(metadata, source_path, analysis_date_override)

    return {
        "schema_version": 2,
        "provider": PROVIDER_ATI,
        "provider_name": PROVIDER_NAMES[PROVIDER_ATI],
        "report_type": metadata.get("report_type", "ati_icp"),
        "metadata": metadata,
        "measurements": measurements,
        "interpretation": _extract_ati_interpretation(full_text),
        "product_recommendations": _extract_ati_product_recommendations(full_text),
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

    oceamo_brand = "oceamo" in normalized
    oceamo_report_marker = (
        "analysebericht" in normalized
        or "analysis report" in normalized
    )
    oceamo_id_marker = (
        "analysenummer" in normalized
        or "analysis no" in normalized
        or "analysis number" in normalized
        or re.search(r"\b(?:oc|msr)\d{4,}\b", normalized) is not None
    )
    fauna_marin_markers = (
        "proben-id:",
        "volumen aquarium in liter:",
        "dosierempfehlung elementals",
    )
    ati_brand_markers = (
        "atiaquaristik.com",
        "idealwert:",
        "barcode",
    )
    ati_english_markers = (
        "atiaquaristik.com",
        "ideal value:",
        "barcode",
    )
    triton_legacy_layout = _is_triton_legacy_layout(normalized)

    matches: list[str] = []
    if oceamo_brand and oceamo_report_marker and oceamo_id_marker:
        matches.append(PROVIDER_OCEAMO)
    if all(marker in normalized for marker in fauna_marin_markers):
        matches.append(PROVIDER_FAUNA_MARIN)
    if all(marker in normalized for marker in ati_brand_markers) or all(
        marker in normalized for marker in ati_english_markers
    ):
        matches.append(PROVIDER_ATI)
    if triton_legacy_layout:
        matches.append(PROVIDER_TRITON)

    if len(matches) == 1:
        return matches[0]

    if len(matches) > 1:
        raise UnsupportedIcpProviderError(
            "The ICP provider could not be identified unambiguously."
        )

    raise UnsupportedIcpProviderError(
        "The ICP provider is not supported or could not be detected."
    )


def parse_icp_pdf(
    path: str | Path,
    analysis_date_override: str | None = None,
) -> dict[str, Any]:
    """Detect the provider and dispatch an uploaded PDF automatically."""
    provider = detect_icp_provider(path)

    if provider == PROVIDER_OCEAMO:
        return parse_oceamo_pdf(path, analysis_date_override)
    if provider == PROVIDER_FAUNA_MARIN:
        return parse_fauna_marin_pdf(path, analysis_date_override)
    if provider == PROVIDER_ATI:
        return parse_ati_pdf(path, analysis_date_override)
    if provider == PROVIDER_TRITON:
        return parse_triton_legacy_pdf(path, analysis_date_override)

    # Kept as a defensive guard for future detector additions.
    raise UnsupportedIcpProviderError(f"Unsupported ICP provider: {provider}")
