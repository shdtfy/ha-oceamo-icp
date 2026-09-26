"""Config flow for Reef ICP."""

from __future__ import annotations

from pathlib import Path
import copy
import re
import shutil
import tempfile
from typing import Any, override

import probatio

from homeassistant.components.file_upload import process_uploaded_file
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.selector import (
    DateSelector,
    DateSelectorConfig,
    FileSelector,
    FileSelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_AQUARIUM_NAME,
    CONF_AQUARIUM_VOLUME_L,
    CONF_CUSTOM_TARGETS,
    CONF_REEF_METHOD,
    CONF_REPORTS,
    CONF_STOCKING_PROFILE,
    CONF_SUPPLY_SYSTEM,
    DOMAIN,
    MAX_STORED_REPORTS,
    PROVIDER_OCEAMO,
    REEF_METHOD_NAMES,
    REEF_METHOD_NONE,
    STOCKING_PROFILE_FISH_ONLY,
    STOCKING_PROFILE_LPS_DOMINANT,
    STOCKING_PROFILE_MIXED_REEF,
    STOCKING_PROFILE_NAMES,
    STOCKING_PROFILE_OTHER,
    STOCKING_PROFILE_SOFT_CORAL_DOMINANT,
    STOCKING_PROFILE_SPS_DOMINANT,
    SUPPLY_SYSTEM_NAMES,
    SUPPLY_SYSTEM_NONE,
)
from .parser import (
    IcpParseError,
    MissingAnalysisDateError,
    PROVIDER_NAMES,
    UnsupportedIcpProviderError,
    detect_icp_provider,
    parse_icp_pdf_for_provider,
)
from .statistics import async_request_statistics_rebuild

CONF_ANALYSIS_DATE = "analysis_date"
CONF_PDF_FILE = "pdf_file"
CONF_PROVIDER = "provider"
CONF_BATCH_ACTION = "batch_action"
CONF_TARGET_MODE = "target_mode"
CONF_CUSTOM_SUPPLY_SYSTEM = "custom_supply_system"

TARGET_MODE_LABORATORY = "laboratory"
TARGET_MODE_CUSTOM = "custom"
SUPPLY_SYSTEM_CUSTOM = "__custom__"

CONF_TARGET_SALINITY_MIN = "target_salinity_min"
CONF_TARGET_SALINITY_MAX = "target_salinity_max"
CONF_TARGET_ALKALINITY_MIN = "target_alkalinity_min"
CONF_TARGET_ALKALINITY_MAX = "target_alkalinity_max"
CONF_TARGET_CALCIUM_MIN = "target_calcium_min"
CONF_TARGET_CALCIUM_MAX = "target_calcium_max"
CONF_TARGET_MAGNESIUM_MIN = "target_magnesium_min"
CONF_TARGET_MAGNESIUM_MAX = "target_magnesium_max"

BATCH_ACTION_ADD = "add_another"
BATCH_ACTION_FINISH = "finish"

_CUSTOM_TARGET_FIELDS: dict[str, tuple[str, str]] = {
    "salinitaet": (CONF_TARGET_SALINITY_MIN, CONF_TARGET_SALINITY_MAX),
    "alkalinitaet": (CONF_TARGET_ALKALINITY_MIN, CONF_TARGET_ALKALINITY_MAX),
    "calcium": (CONF_TARGET_CALCIUM_MIN, CONF_TARGET_CALCIUM_MAX),
    "magnesium": (CONF_TARGET_MAGNESIUM_MIN, CONF_TARGET_MAGNESIUM_MAX),
}


def _cleanup_pending_pdf(pending_pdf_path: str | None) -> None:
    """Remove a preserved temporary PDF and its private temp directory."""
    if pending_pdf_path:
        shutil.rmtree(Path(pending_pdf_path).parent, ignore_errors=True)


def _copy_uploaded_pdf(hass: HomeAssistant, uploaded_file_id: str) -> Path:
    """Preserve an uploaded PDF after Home Assistant removes the upload temp dir."""
    temp_dir = Path(tempfile.mkdtemp(prefix="reef_icp_"))
    try:
        with process_uploaded_file(hass, uploaded_file_id) as file_path:
            source_path = Path(file_path)
            preserved_path = temp_dir / (source_path.name or "icp-report.pdf")
            shutil.copy2(source_path, preserved_path)
        return preserved_path
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise


def _prepare_uploaded_pdf(
    hass: HomeAssistant,
    uploaded_file_id: str,
) -> tuple[str, str, dict[str, Any] | None]:
    """Preserve an upload, detect its provider and build a best-effort preview."""
    preserved_path = _copy_uploaded_pdf(hass, uploaded_file_id)
    try:
        provider = detect_icp_provider(preserved_path)
    except Exception:
        _cleanup_pending_pdf(str(preserved_path))
        raise

    try:
        report = parse_icp_pdf_for_provider(preserved_path, provider)
    except (MissingAnalysisDateError, IcpParseError):
        report = None
    except Exception:
        _cleanup_pending_pdf(str(preserved_path))
        raise
    return str(preserved_path), provider, report


def _normalize_selected_date(value: Any) -> str:
    """Return a Home Assistant date-selector value as YYYY-MM-DD."""
    if hasattr(value, "isoformat"):
        value = value.isoformat()
    date_value = str(value).strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_value):
        raise ValueError("Invalid analysis date.")
    return date_value


def _normalize_aquarium_volume(value: Any) -> float:
    volume = float(value)
    if volume <= 0:
        raise ValueError("Aquarium volume must be greater than zero.")
    return volume


def _normalize_supply_system(value: Any) -> str:
    system = str(value).strip()
    if not system:
        raise ValueError("Supply system must not be empty.")
    return system


def _normalize_reef_method(value: Any) -> str:
    method = str(value).strip()
    if method not in REEF_METHOD_NAMES:
        raise ValueError("Unsupported reef method.")
    return method


def _normalize_stocking_profile(value: Any) -> str:
    profile = str(value).strip()
    if profile not in STOCKING_PROFILE_NAMES:
        raise ValueError("Unsupported stocking profile.")
    return profile


def _normalize_target_mode(value: Any) -> str:
    mode = str(value).strip()
    if mode not in {TARGET_MODE_LABORATORY, TARGET_MODE_CUSTOM}:
        raise ValueError("Unsupported target mode.")
    return mode


def _optional_number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _normalize_custom_targets(user_input: dict[str, Any]) -> dict[str, dict[str, float]]:
    """Validate optional personal target ranges for the four core parameters."""
    targets: dict[str, dict[str, float]] = {}
    for key, (minimum_field, maximum_field) in _CUSTOM_TARGET_FIELDS.items():
        minimum = _optional_number(user_input.get(minimum_field))
        maximum = _optional_number(user_input.get(maximum_field))
        if minimum is None and maximum is None:
            continue
        if minimum is None or maximum is None:
            raise ValueError("Both limits are required for a custom target.")
        if minimum > maximum:
            raise ValueError("The minimum target must not exceed the maximum.")
        targets[key] = {"min": float(minimum), "max": float(maximum)}
    return targets


def _custom_target_suggestions(targets: dict[str, Any] | None) -> dict[str, float]:
    suggestions: dict[str, float] = {}
    for key, (minimum_field, maximum_field) in _CUSTOM_TARGET_FIELDS.items():
        target = (targets or {}).get(key)
        if not isinstance(target, dict):
            continue
        minimum = target.get("min")
        maximum = target.get("max")
        if isinstance(minimum, (int, float)) and isinstance(maximum, (int, float)):
            suggestions[minimum_field] = float(minimum)
            suggestions[maximum_field] = float(maximum)
    return suggestions


def _apply_custom_targets_to_report(
    report: dict[str, Any],
    custom_targets: dict[str, dict[str, float]],
) -> dict[str, Any]:
    """Apply personal targets while preserving the laboratory target and status."""
    updated = copy.deepcopy(report)
    for measurement in updated.get("measurements", []):
        if not isinstance(measurement, dict):
            continue
        key = str(measurement.get("key") or "")
        target = custom_targets.get(key)
        has_laboratory_target = "laboratory_target" in measurement

        if measurement.get("category") == "osmosis" or target is None:
            if has_laboratory_target:
                measurement["target"] = copy.deepcopy(measurement.get("laboratory_target"))
            measurement.pop("custom_target", None)
            measurement.pop("custom_target_source", None)
            measurement.pop("target_source", None)
            continue

        if not has_laboratory_target:
            measurement["laboratory_target"] = copy.deepcopy(measurement.get("target"))
        personal_target = {
            "type": "range",
            "min": float(target["min"]),
            "max": float(target["max"]),
        }
        measurement["custom_target"] = copy.deepcopy(personal_target)
        measurement["custom_target_source"] = "aquarium"
        measurement["target"] = personal_target
        measurement["target_source"] = "aquarium_custom"
    return updated


def _apply_custom_targets_to_reports(
    reports: list[dict[str, Any]],
    custom_targets: dict[str, dict[str, float]],
) -> list[dict[str, Any]]:
    return [_apply_custom_targets_to_report(report, custom_targets) for report in reports]


def _supply_system_options(
    hass: HomeAssistant,
    current_value: str | None = None,
) -> list[SelectOptionDict]:
    """Return all built-in systems plus an explicit custom-system choice."""
    is_german = str(hass.config.language or "").lower().startswith("de")
    options: list[SelectOptionDict] = []
    for value, label in SUPPLY_SYSTEM_NAMES.items():
        if value == SUPPLY_SYSTEM_NONE:
            label = (
                "Kein Versorgungssystem / nur Analyse"
                if is_german
                else "No dosing system / analysis only"
            )
        options.append(SelectOptionDict(value=value, label=label))

    preset_values = {str(option["value"]) for option in options}
    if current_value and current_value not in preset_values and current_value != SUPPLY_SYSTEM_CUSTOM:
        options.append(SelectOptionDict(value=current_value, label=current_value))

    options.append(
        SelectOptionDict(
            value=SUPPLY_SYSTEM_CUSTOM,
            label=("Sonstiges / benutzerdefiniert" if is_german else "Other / custom"),
        )
    )
    return options


def _reef_method_options(hass: HomeAssistant) -> list[SelectOptionDict]:
    """Return the independent reef/nutrient-method choices."""
    is_german = str(hass.config.language or "").lower().startswith("de")
    options: list[SelectOptionDict] = []
    for value, label in REEF_METHOD_NAMES.items():
        if value == REEF_METHOD_NONE:
            label = "Keine / Standard-Riff" if is_german else "None / standard reef"
        options.append(SelectOptionDict(value=value, label=label))
    return options


def _stocking_profile_options(hass: HomeAssistant) -> list[SelectOptionDict]:
    is_german = str(hass.config.language or "").lower().startswith("de")
    labels = (
        {
            STOCKING_PROFILE_MIXED_REEF: "Mixed Reef",
            STOCKING_PROFILE_SPS_DOMINANT: "SPS-dominant",
            STOCKING_PROFILE_LPS_DOMINANT: "LPS-dominant",
            STOCKING_PROFILE_SOFT_CORAL_DOMINANT: "Weichkorallen-dominant",
            STOCKING_PROFILE_FISH_ONLY: "Fish Only / Fischbesatz ohne Korallen",
            STOCKING_PROFILE_OTHER: "Sonstiges / benutzerdefiniert",
        }
        if is_german
        else {
            STOCKING_PROFILE_MIXED_REEF: "Mixed Reef",
            STOCKING_PROFILE_SPS_DOMINANT: "SPS-dominant",
            STOCKING_PROFILE_LPS_DOMINANT: "LPS-dominant",
            STOCKING_PROFILE_SOFT_CORAL_DOMINANT: "Soft-coral dominant",
            STOCKING_PROFILE_FISH_ONLY: "Fish Only",
            STOCKING_PROFILE_OTHER: "Other / custom",
        }
    )
    return [SelectOptionDict(value=value, label=labels[value]) for value in labels]


def _stocking_profile_selector(hass: HomeAssistant) -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(options=_stocking_profile_options(hass), mode=SelectSelectorMode.DROPDOWN)
    )


def _supply_system_selector(hass: HomeAssistant, current_value: str | None = None) -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(options=_supply_system_options(hass, current_value), mode=SelectSelectorMode.DROPDOWN)
    )


def _reef_method_selector(hass: HomeAssistant) -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(options=_reef_method_options(hass), mode=SelectSelectorMode.DROPDOWN)
    )


def _volume_selector() -> NumberSelector:
    return NumberSelector(
        NumberSelectorConfig(min=1, max=100000, step=1, unit_of_measurement="L", mode=NumberSelectorMode.BOX)
    )


def _target_mode_selector(hass: HomeAssistant) -> SelectSelector:
    is_german = str(hass.config.language or "").lower().startswith("de")
    return SelectSelector(
        SelectSelectorConfig(
            options=[
                SelectOptionDict(
                    value=TARGET_MODE_LABORATORY,
                    label=(
                        "Sollbereiche aus der jeweiligen ICP verwenden"
                        if is_german
                        else "Use target ranges from each ICP report"
                    ),
                ),
                SelectOptionDict(
                    value=TARGET_MODE_CUSTOM,
                    label=("Eigene Zielbereiche verwenden" if is_german else "Use personal aquarium target ranges"),
                ),
            ],
            mode=SelectSelectorMode.DROPDOWN,
        )
    )


def _target_number_selector(*, minimum: float, maximum: float, step: float, unit: str) -> NumberSelector:
    return NumberSelector(
        NumberSelectorConfig(min=minimum, max=maximum, step=step, unit_of_measurement=unit, mode=NumberSelectorMode.BOX)
    )


def _custom_targets_schema() -> probatio.Schema:
    return probatio.Schema(
        {
            probatio.Optional(CONF_TARGET_SALINITY_MIN): _target_number_selector(minimum=0, maximum=50, step=0.01, unit="psu"),
            probatio.Optional(CONF_TARGET_SALINITY_MAX): _target_number_selector(minimum=0, maximum=50, step=0.01, unit="psu"),
            probatio.Optional(CONF_TARGET_ALKALINITY_MIN): _target_number_selector(minimum=0, maximum=30, step=0.1, unit="dKH"),
            probatio.Optional(CONF_TARGET_ALKALINITY_MAX): _target_number_selector(minimum=0, maximum=30, step=0.1, unit="dKH"),
            probatio.Optional(CONF_TARGET_CALCIUM_MIN): _target_number_selector(minimum=0, maximum=1000, step=1, unit="mg/l"),
            probatio.Optional(CONF_TARGET_CALCIUM_MAX): _target_number_selector(minimum=0, maximum=1000, step=1, unit="mg/l"),
            probatio.Optional(CONF_TARGET_MAGNESIUM_MIN): _target_number_selector(minimum=0, maximum=3000, step=1, unit="mg/l"),
            probatio.Optional(CONF_TARGET_MAGNESIUM_MAX): _target_number_selector(minimum=0, maximum=3000, step=1, unit="mg/l"),
        }
    )


def _custom_supply_system_schema() -> probatio.Schema:
    return probatio.Schema(
        {probatio.Required(CONF_CUSTOM_SUPPLY_SYSTEM): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT))}
    )


def _provider_selector() -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(
            options=[SelectOptionDict(value=provider, label=name) for provider, name in PROVIDER_NAMES.items()],
            mode=SelectSelectorMode.DROPDOWN,
        )
    )


def _batch_action_selector(hass: HomeAssistant) -> SelectSelector:
    is_german = str(hass.config.language or "").lower().startswith("de")
    return SelectSelector(
        SelectSelectorConfig(
            options=[
                SelectOptionDict(value=BATCH_ACTION_ADD, label="Weitere ICP hinzufügen" if is_german else "Add another ICP"),
                SelectOptionDict(value=BATCH_ACTION_FINISH, label="Import abschließen" if is_german else "Finish import"),
            ],
            mode=SelectSelectorMode.DROPDOWN,
        )
    )


_REPORT_TYPE_LABELS = {
    "classic_icp": "Classic ICP",
    "reef_icp_ms": "Reef ICP-MS",
    "reef_icp": "Reef ICP",
    "ati_icp": "ICP",
    "standard": "ICP-OES Standard",
    "pro": "ICP-OES Pro",
    "ultimate_ms": "Ultimate-MS",
    "triton_legacy_icp": "Legacy ICP-OES",
    "icp_water_analysis": "ICP Water Analysis",
    "icp_water_analysis_plus": "ICP Water Analysis Plus",
}


def _confirmation_placeholders(detected_provider: str, report: dict[str, Any] | None) -> dict[str, str]:
    metadata = report.get("metadata", {}) if report else {}
    report_type = (report.get("report_type") or metadata.get("report_type")) if report else None
    return {
        "detected_provider": PROVIDER_NAMES.get(detected_provider, detected_provider),
        "report_type": _REPORT_TYPE_LABELS.get(str(report_type), str(report_type)) if report_type else "—",
        "analysis_number": str(metadata.get("provider_report_id") or metadata.get("analysis_number") or "—"),
        "analysis_date": str(metadata.get("analysis_date") or "—"),
    }


def _parse_pending_pdf_for_provider(pending_pdf_path: str, provider: str) -> dict[str, Any]:
    source_path = Path(pending_pdf_path)
    if not source_path.exists():
        raise IcpParseError("The preserved uploaded PDF is no longer available.")
    return parse_icp_pdf_for_provider(source_path, provider)


def _parse_pending_pdf_with_date(pending_pdf_path: str, provider: str, selected_date: Any) -> dict[str, Any]:
    source_path = Path(pending_pdf_path)
    if not source_path.exists():
        raise IcpParseError("The preserved uploaded PDF is no longer available.")
    return parse_icp_pdf_for_provider(
        source_path,
        provider,
        analysis_date_override=_normalize_selected_date(selected_date),
    )


def _report_provider(report: dict[str, Any]) -> str:
    return str(report.get("provider") or report.get("metadata", {}).get("provider") or PROVIDER_OCEAMO)


def _report_identity(report: dict[str, Any]) -> tuple[str, str]:
    metadata = report.get("metadata", {})
    return (
        _report_provider(report),
        str(metadata.get("provider_report_id") or metadata.get("analysis_number") or ""),
    )


def _report_sort_key(report: dict[str, Any]) -> str:
    metadata = report.get("metadata", {})
    return str(metadata.get("sample_taken") or metadata.get("analysis_date") or "")


def _upsert_report(reports: list[dict[str, Any]], report: dict[str, Any]) -> list[dict[str, Any]]:
    identity = _report_identity(report)
    merged = [existing for existing in reports if _report_identity(existing) != identity]
    merged.append(report)
    merged.sort(key=_report_sort_key)
    return merged[-MAX_STORED_REPORTS:]


def _merge_reports(existing_reports: list[dict[str, Any]], imported_reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    reports = list(existing_reports)
    for report in imported_reports:
        reports = _upsert_report(reports, report)
    return reports


def _updated_options_with_reports(entry: ConfigEntry, reports: list[dict[str, Any]]) -> dict[str, Any]:
    options = dict(entry.options)
    options[CONF_REPORTS] = reports
    return options


def _batch_placeholders(reports: list[dict[str, Any]]) -> dict[str, str]:
    lines: list[str] = []
    for report in sorted(reports, key=_report_sort_key):
        metadata = report.get("metadata", {})
        provider = report.get("provider_name") or PROVIDER_NAMES.get(_report_provider(report), _report_provider(report))
        analysis_number = str(metadata.get("provider_report_id") or metadata.get("analysis_number") or "—")
        date_value = str(metadata.get("analysis_date") or metadata.get("sample_taken") or "—")
        if "T" in date_value:
            date_value = date_value.split("T", 1)[0]
        lines.append(f"✓ {date_value} · {provider} · {analysis_number}")
    return {"report_count": str(len(reports)), "report_list": "\n".join(lines) or "—"}


class ReefIcpConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a Reef ICP config flow."""

    VERSION = 1

    _pending_pdf_path: str | None = None
    _pending_detected_provider: str | None = None
    _pending_provider: str | None = None
    _pending_report: dict[str, Any] | None = None
    _pending_reports: list[dict[str, Any]] | None = None
    _pending_aquarium_name: str | None = None
    _pending_aquarium_volume_l: float | None = None
    _pending_stocking_profile: str | None = None
    _pending_supply_system: str | None = None
    _pending_reef_method: str | None = None
    _pending_target_mode: str | None = None
    _pending_custom_targets: dict[str, dict[str, float]] | None = None

    @staticmethod
    @callback
    @override
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlowWithReload:
        return ReefIcpOptionsFlow()

    def _batch_reports(self) -> list[dict[str, Any]]:
        if self._pending_reports is None:
            self._pending_reports = []
        return self._pending_reports

    def _clear_current_pdf(self) -> None:
        self._pending_pdf_path = None
        self._pending_detected_provider = None
        self._pending_provider = None
        self._pending_report = None

    def _clear_pending_setup(self) -> None:
        self._clear_current_pdf()
        self._pending_reports = None
        self._pending_aquarium_name = None
        self._pending_aquarium_volume_l = None
        self._pending_stocking_profile = None
        self._pending_supply_system = None
        self._pending_reef_method = None
        self._pending_target_mode = None
        self._pending_custom_targets = None

    async def _prepare_pdf_from_input(self, uploaded_file_id: str) -> tuple[str, str, dict[str, Any] | None]:
        return await self.hass.async_add_executor_job(_prepare_uploaded_pdf, self.hass, uploaded_file_id)

    async def _accept_report(self, report: dict[str, Any]) -> ConfigFlowResult:
        await self.hass.async_add_executor_job(_cleanup_pending_pdf, self._pending_pdf_path)
        self._pending_reports = _upsert_report(self._batch_reports(), report)
        self._clear_current_pdf()
        return await self.async_step_import_more()

    def _create_aquarium_entry(self) -> ConfigFlowResult:
        if (
            self._pending_aquarium_name is None
            or self._pending_aquarium_volume_l is None
            or self._pending_stocking_profile is None
            or self._pending_supply_system is None
            or self._pending_reef_method is None
        ):
            raise ValueError("Aquarium profile is incomplete.")

        aquarium_name = self._pending_aquarium_name
        options = {
            CONF_REPORTS: [],
            CONF_AQUARIUM_VOLUME_L: self._pending_aquarium_volume_l,
            CONF_STOCKING_PROFILE: self._pending_stocking_profile,
            CONF_SUPPLY_SYSTEM: self._pending_supply_system,
            CONF_REEF_METHOD: self._pending_reef_method,
            CONF_CUSTOM_TARGETS: dict(self._pending_custom_targets or {}),
        }
        self._clear_pending_setup()
        return self.async_create_entry(
            title=aquarium_name,
            data={CONF_AQUARIUM_NAME: aquarium_name},
            options=options,
        )

    @override
    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                aquarium_name = str(user_input[CONF_AQUARIUM_NAME]).strip()
                if not aquarium_name:
                    raise ValueError("Aquarium name must not be empty.")
                aquarium_volume_l = _normalize_aquarium_volume(user_input[CONF_AQUARIUM_VOLUME_L])
                stocking_profile = _normalize_stocking_profile(user_input[CONF_STOCKING_PROFILE])
                supply_system = _normalize_supply_system(user_input[CONF_SUPPLY_SYSTEM])
                reef_method = _normalize_reef_method(user_input[CONF_REEF_METHOD])
                target_mode = _normalize_target_mode(user_input[CONF_TARGET_MODE])
            except (TypeError, ValueError):
                errors["base"] = "invalid_aquarium_profile"
            else:
                self._pending_reports = []
                self._pending_aquarium_name = aquarium_name
                self._pending_aquarium_volume_l = aquarium_volume_l
                self._pending_stocking_profile = stocking_profile
                self._pending_supply_system = supply_system
                self._pending_reef_method = reef_method
                self._pending_target_mode = target_mode
                self._pending_custom_targets = {}
                if supply_system == SUPPLY_SYSTEM_CUSTOM:
                    return await self.async_step_custom_supply_system()
                if target_mode == TARGET_MODE_CUSTOM:
                    return await self.async_step_custom_targets()
                return self._create_aquarium_entry()

        schema = probatio.Schema(
            {
                probatio.Required(CONF_AQUARIUM_NAME): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
                probatio.Required(CONF_AQUARIUM_VOLUME_L): _volume_selector(),
                probatio.Required(CONF_STOCKING_PROFILE): _stocking_profile_selector(self.hass),
                probatio.Required(CONF_SUPPLY_SYSTEM): _supply_system_selector(self.hass),
                probatio.Required(CONF_REEF_METHOD): _reef_method_selector(self.hass),
                probatio.Required(CONF_TARGET_MODE): _target_mode_selector(self.hass),
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                schema,
                user_input or {
                    CONF_REEF_METHOD: REEF_METHOD_NONE,
                    CONF_TARGET_MODE: TARGET_MODE_LABORATORY,
                },
            ),
            errors=errors,
        )

    async def async_step_custom_supply_system(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if self._pending_aquarium_name is None or self._pending_supply_system != SUPPLY_SYSTEM_CUSTOM:
            return await self.async_step_user()
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                supply_system = _normalize_supply_system(user_input[CONF_CUSTOM_SUPPLY_SYSTEM])
                if supply_system == SUPPLY_SYSTEM_CUSTOM:
                    raise ValueError("Reserved supply-system value.")
            except (TypeError, ValueError):
                errors["base"] = "invalid_custom_supply_system"
            else:
                self._pending_supply_system = supply_system
                if self._pending_target_mode == TARGET_MODE_CUSTOM:
                    return await self.async_step_custom_targets()
                return self._create_aquarium_entry()
        return self.async_show_form(
            step_id="custom_supply_system",
            data_schema=self.add_suggested_values_to_schema(_custom_supply_system_schema(), user_input),
            errors=errors,
        )

    async def async_step_custom_targets(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if self._pending_aquarium_name is None or self._pending_target_mode != TARGET_MODE_CUSTOM:
            return await self.async_step_user()
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                self._pending_custom_targets = _normalize_custom_targets(user_input)
            except (TypeError, ValueError):
                errors["base"] = "invalid_custom_targets"
            else:
                return self._create_aquarium_entry()
        suggested = _custom_target_suggestions(self._pending_custom_targets)
        return self.async_show_form(
            step_id="custom_targets",
            data_schema=self.add_suggested_values_to_schema(_custom_targets_schema(), user_input or suggested),
            errors=errors,
        )

    async def async_step_add_icp(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if self._pending_aquarium_name is None or not self._batch_reports():
            return await self.async_step_user()
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                pending_path, provider, preview_report = await self._prepare_pdf_from_input(user_input[CONF_PDF_FILE])
            except UnsupportedIcpProviderError:
                errors["base"] = "unsupported_provider"
            except IcpParseError:
                errors["base"] = "invalid_icp_pdf"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                self._pending_pdf_path = pending_path
                self._pending_detected_provider = provider
                self._pending_provider = provider
                self._pending_report = preview_report
                return await self.async_step_confirm_provider()
        schema = probatio.Schema({probatio.Required(CONF_PDF_FILE): FileSelector(FileSelectorConfig(accept=".pdf,application/pdf"))})
        return self.async_show_form(
            step_id="add_icp",
            data_schema=self.add_suggested_values_to_schema(schema, user_input),
            description_placeholders=_batch_placeholders(self._batch_reports()),
            errors=errors,
        )

    async def async_step_confirm_provider(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if self._pending_pdf_path is None or self._pending_detected_provider is None or self._pending_aquarium_name is None:
            return await (self.async_step_add_icp() if self._batch_reports() else self.async_step_user())
        detected_provider = self._pending_detected_provider
        if user_input is not None:
            selected_provider = str(user_input[CONF_PROVIDER]).strip()
            self._pending_provider = selected_provider
            try:
                if selected_provider == detected_provider and self._pending_report is not None:
                    report = self._pending_report
                else:
                    report = await self.hass.async_add_executor_job(
                        _parse_pending_pdf_for_provider,
                        self._pending_pdf_path,
                        selected_provider,
                    )
            except MissingAnalysisDateError:
                self._pending_report = None
                return await self.async_step_analysis_date()
            except (IcpParseError, UnsupportedIcpProviderError):
                errors["base"] = "provider_mismatch"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                return await self._accept_report(report)
        schema = probatio.Schema({probatio.Required(CONF_PROVIDER): _provider_selector()})
        return self.async_show_form(
            step_id="confirm_provider",
            data_schema=self.add_suggested_values_to_schema(schema, user_input or {CONF_PROVIDER: detected_provider}),
            description_placeholders=_confirmation_placeholders(detected_provider, self._pending_report),
            errors=errors,
        )

    async def async_step_analysis_date(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if self._pending_pdf_path is None or self._pending_provider is None:
            return await (self.async_step_add_icp() if self._batch_reports() else self.async_step_user())
        if user_input is not None:
            try:
                report = await self.hass.async_add_executor_job(
                    _parse_pending_pdf_with_date,
                    self._pending_pdf_path,
                    self._pending_provider,
                    user_input[CONF_ANALYSIS_DATE],
                )
            except IcpParseError:
                errors["base"] = "invalid_icp_pdf"
            except (TypeError, ValueError):
                errors["base"] = "invalid_analysis_date"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                return await self._accept_report(report)
        schema = probatio.Schema({probatio.Required(CONF_ANALYSIS_DATE): DateSelector(DateSelectorConfig())})
        provider_name = PROVIDER_NAMES.get(self._pending_provider or "", self._pending_provider or "ICP")
        return self.async_show_form(
            step_id="analysis_date",
            data_schema=self.add_suggested_values_to_schema(schema, user_input),
            description_placeholders={"provider": provider_name},
            errors=errors,
        )

    async def async_step_import_more(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        reports = self._batch_reports()
        if not reports or self._pending_aquarium_name is None:
            return await self.async_step_user()
        if user_input is not None:
            action = str(user_input[CONF_BATCH_ACTION])
            if action == BATCH_ACTION_ADD:
                return await self.async_step_add_icp()
            if action == BATCH_ACTION_FINISH:
                if self._pending_reef_method is None:
                    self._pending_reef_method = REEF_METHOD_NONE
                aquarium_name = self._pending_aquarium_name
                options = {
                    CONF_REPORTS: _apply_custom_targets_to_reports(list(reports), dict(self._pending_custom_targets or {})),
                    CONF_AQUARIUM_VOLUME_L: self._pending_aquarium_volume_l,
                    CONF_STOCKING_PROFILE: self._pending_stocking_profile,
                    CONF_SUPPLY_SYSTEM: self._pending_supply_system,
                    CONF_REEF_METHOD: self._pending_reef_method,
                    CONF_CUSTOM_TARGETS: dict(self._pending_custom_targets or {}),
                }
                self._clear_pending_setup()
                return self.async_create_entry(title=aquarium_name, data={CONF_AQUARIUM_NAME: aquarium_name}, options=options)
        schema = probatio.Schema({probatio.Required(CONF_BATCH_ACTION): _batch_action_selector(self.hass)})
        return self.async_show_form(
            step_id="import_more",
            data_schema=self.add_suggested_values_to_schema(schema, user_input or {CONF_BATCH_ACTION: BATCH_ACTION_ADD}),
            description_placeholders=_batch_placeholders(reports),
        )


class ReefIcpOptionsFlow(OptionsFlowWithReload):
    """Manage aquarium settings and import additional ICP reports."""

    _pending_pdf_path: str | None = None
    _pending_detected_provider: str | None = None
    _pending_provider: str | None = None
    _pending_report: dict[str, Any] | None = None
    _pending_reports: list[dict[str, Any]] | None = None
    _pending_aquarium_settings: dict[str, Any] | None = None
    _pending_target_mode: str | None = None

    def _batch_reports(self) -> list[dict[str, Any]]:
        if self._pending_reports is None:
            self._pending_reports = []
        return self._pending_reports

    def _clear_current_pdf(self) -> None:
        self._pending_pdf_path = None
        self._pending_detected_provider = None
        self._pending_provider = None
        self._pending_report = None

    def _clear_batch(self) -> None:
        self._clear_current_pdf()
        self._pending_reports = None

    async def _accept_report(self, report: dict[str, Any]) -> ConfigFlowResult:
        await self.hass.async_add_executor_job(_cleanup_pending_pdf, self._pending_pdf_path)
        self._pending_reports = _upsert_report(self._batch_reports(), report)
        self._clear_current_pdf()
        return await self.async_step_import_more()

    def _store_reports(self, imported_reports: list[dict[str, Any]]) -> ConfigFlowResult:
        existing_reports = list(self.config_entry.options.get(CONF_REPORTS, []))
        existing_identities = {_report_identity(report) for report in existing_reports}
        replacing_existing = any(_report_identity(report) in existing_identities for report in imported_reports)
        reports = _merge_reports(existing_reports, imported_reports)
        custom_targets = self.config_entry.options.get(CONF_CUSTOM_TARGETS, {})
        if not isinstance(custom_targets, dict):
            custom_targets = {}
        reports = _apply_custom_targets_to_reports(reports, custom_targets)
        if replacing_existing:
            async_request_statistics_rebuild(self.hass, self.config_entry, [*existing_reports, *imported_reports])
        return self.async_create_entry(title="", data=_updated_options_with_reports(self.config_entry, reports))

    @override
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return self.async_show_menu(step_id="init", menu_options=["import_icp", "aquarium_settings"])

    async def async_step_import_icp(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                pending_path, provider, preview_report = await self.hass.async_add_executor_job(
                    _prepare_uploaded_pdf,
                    self.hass,
                    user_input[CONF_PDF_FILE],
                )
            except UnsupportedIcpProviderError:
                errors["base"] = "unsupported_provider"
            except IcpParseError:
                errors["base"] = "invalid_icp_pdf"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                if self._pending_reports is None:
                    self._pending_reports = []
                self._pending_pdf_path = pending_path
                self._pending_detected_provider = provider
                self._pending_provider = provider
                self._pending_report = preview_report
                return await self.async_step_confirm_provider()
        schema = probatio.Schema({probatio.Required(CONF_PDF_FILE): FileSelector(FileSelectorConfig(accept=".pdf,application/pdf"))})
        return self.async_show_form(
            step_id="import_icp",
            data_schema=self.add_suggested_values_to_schema(schema, user_input),
            description_placeholders=_batch_placeholders(self._batch_reports()),
            errors=errors,
        )

    async def async_step_confirm_provider(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if self._pending_pdf_path is None or self._pending_detected_provider is None:
            return await self.async_step_import_icp()
        detected_provider = self._pending_detected_provider
        if user_input is not None:
            selected_provider = str(user_input[CONF_PROVIDER]).strip()
            self._pending_provider = selected_provider
            try:
                if selected_provider == detected_provider and self._pending_report is not None:
                    report = self._pending_report
                else:
                    report = await self.hass.async_add_executor_job(
                        _parse_pending_pdf_for_provider,
                        self._pending_pdf_path,
                        selected_provider,
                    )
            except MissingAnalysisDateError:
                self._pending_report = None
                return await self.async_step_analysis_date()
            except (IcpParseError, UnsupportedIcpProviderError):
                errors["base"] = "provider_mismatch"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                return await self._accept_report(report)
        schema = probatio.Schema({probatio.Required(CONF_PROVIDER): _provider_selector()})
        return self.async_show_form(
            step_id="confirm_provider",
            data_schema=self.add_suggested_values_to_schema(schema, user_input or {CONF_PROVIDER: detected_provider}),
            description_placeholders=_confirmation_placeholders(detected_provider, self._pending_report),
            errors=errors,
        )

    async def async_step_import_more(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        reports = self._batch_reports()
        if not reports:
            return await self.async_step_import_icp()
        if user_input is not None:
            action = str(user_input[CONF_BATCH_ACTION])
            if action == BATCH_ACTION_ADD:
                return await self.async_step_import_icp()
            if action == BATCH_ACTION_FINISH:
                imported_reports = list(reports)
                self._clear_batch()
                return self._store_reports(imported_reports)
        schema = probatio.Schema({probatio.Required(CONF_BATCH_ACTION): _batch_action_selector(self.hass)})
        return self.async_show_form(
            step_id="import_more",
            data_schema=self.add_suggested_values_to_schema(schema, user_input or {CONF_BATCH_ACTION: BATCH_ACTION_ADD}),
            description_placeholders=_batch_placeholders(reports),
        )

    def _store_aquarium_settings(self, custom_targets: dict[str, dict[str, float]]) -> ConfigFlowResult:
        if self._pending_aquarium_settings is None:
            raise ValueError("Aquarium settings are not prepared.")
        options = dict(self.config_entry.options)
        options.update(self._pending_aquarium_settings)
        options.setdefault(CONF_REEF_METHOD, REEF_METHOD_NONE)
        options[CONF_CUSTOM_TARGETS] = custom_targets
        options[CONF_REPORTS] = _apply_custom_targets_to_reports(list(options.get(CONF_REPORTS, [])), custom_targets)
        self._pending_aquarium_settings = None
        self._pending_target_mode = None
        return self.async_create_entry(title="", data=options)

    async def async_step_custom_supply_system(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if self._pending_aquarium_settings is None:
            return await self.async_step_aquarium_settings()
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                supply_system = _normalize_supply_system(user_input[CONF_CUSTOM_SUPPLY_SYSTEM])
                if supply_system == SUPPLY_SYSTEM_CUSTOM:
                    raise ValueError("Reserved supply-system value.")
            except (TypeError, ValueError):
                errors["base"] = "invalid_custom_supply_system"
            else:
                self._pending_aquarium_settings[CONF_SUPPLY_SYSTEM] = supply_system
                if self._pending_target_mode == TARGET_MODE_CUSTOM:
                    return await self.async_step_custom_targets()
                return self._store_aquarium_settings({})
        return self.async_show_form(
            step_id="custom_supply_system",
            data_schema=self.add_suggested_values_to_schema(_custom_supply_system_schema(), user_input),
            errors=errors,
        )

    async def async_step_aquarium_settings(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                aquarium_volume_l = _normalize_aquarium_volume(user_input[CONF_AQUARIUM_VOLUME_L])
                stocking_profile = _normalize_stocking_profile(user_input[CONF_STOCKING_PROFILE])
                supply_system = _normalize_supply_system(user_input[CONF_SUPPLY_SYSTEM])
                reef_method = _normalize_reef_method(user_input[CONF_REEF_METHOD])
                target_mode = _normalize_target_mode(user_input[CONF_TARGET_MODE])
            except (TypeError, ValueError):
                errors["base"] = "invalid_aquarium_profile"
            else:
                self._pending_target_mode = target_mode
                self._pending_aquarium_settings = {
                    CONF_AQUARIUM_VOLUME_L: aquarium_volume_l,
                    CONF_STOCKING_PROFILE: stocking_profile,
                    CONF_REEF_METHOD: reef_method,
                }
                if supply_system == SUPPLY_SYSTEM_CUSTOM:
                    return await self.async_step_custom_supply_system()
                self._pending_aquarium_settings[CONF_SUPPLY_SYSTEM] = supply_system
                if target_mode == TARGET_MODE_CUSTOM:
                    return await self.async_step_custom_targets()
                return self._store_aquarium_settings({})

        current_targets = self.config_entry.options.get(CONF_CUSTOM_TARGETS, {})
        if not isinstance(current_targets, dict):
            current_targets = {}
        current_supply_system = str(self.config_entry.options.get(CONF_SUPPLY_SYSTEM, SUPPLY_SYSTEM_NONE))
        suggested: dict[str, Any] = {
            CONF_STOCKING_PROFILE: self.config_entry.options.get(CONF_STOCKING_PROFILE, STOCKING_PROFILE_OTHER),
            CONF_SUPPLY_SYSTEM: current_supply_system,
            CONF_REEF_METHOD: self.config_entry.options.get(CONF_REEF_METHOD, REEF_METHOD_NONE),
            CONF_TARGET_MODE: TARGET_MODE_CUSTOM if current_targets else TARGET_MODE_LABORATORY,
        }
        if volume := self.config_entry.options.get(CONF_AQUARIUM_VOLUME_L):
            suggested[CONF_AQUARIUM_VOLUME_L] = volume

        schema = probatio.Schema(
            {
                probatio.Required(CONF_AQUARIUM_VOLUME_L): _volume_selector(),
                probatio.Required(CONF_STOCKING_PROFILE): _stocking_profile_selector(self.hass),
                probatio.Required(CONF_SUPPLY_SYSTEM): _supply_system_selector(self.hass, current_supply_system),
                probatio.Required(CONF_REEF_METHOD): _reef_method_selector(self.hass),
                probatio.Required(CONF_TARGET_MODE): _target_mode_selector(self.hass),
            }
        )
        return self.async_show_form(
            step_id="aquarium_settings",
            data_schema=self.add_suggested_values_to_schema(schema, user_input or suggested),
            errors=errors,
        )

    async def async_step_custom_targets(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if self._pending_aquarium_settings is None:
            return await self.async_step_aquarium_settings()
        errors: dict[str, str] = {}
        current_targets = self.config_entry.options.get(CONF_CUSTOM_TARGETS, {})
        if not isinstance(current_targets, dict):
            current_targets = {}
        if user_input is not None:
            try:
                custom_targets = _normalize_custom_targets(user_input)
            except (TypeError, ValueError):
                errors["base"] = "invalid_custom_targets"
            else:
                return self._store_aquarium_settings(custom_targets)
        suggested = _custom_target_suggestions(current_targets)
        return self.async_show_form(
            step_id="custom_targets",
            data_schema=self.add_suggested_values_to_schema(_custom_targets_schema(), user_input or suggested),
            errors=errors,
        )

    async def async_step_analysis_date(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if self._pending_pdf_path is None or self._pending_provider is None:
            return await self.async_step_import_icp()
        if user_input is not None:
            try:
                report = await self.hass.async_add_executor_job(
                    _parse_pending_pdf_with_date,
                    self._pending_pdf_path,
                    self._pending_provider,
                    user_input[CONF_ANALYSIS_DATE],
                )
            except IcpParseError:
                errors["base"] = "invalid_icp_pdf"
            except (TypeError, ValueError):
                errors["base"] = "invalid_analysis_date"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                return await self._accept_report(report)
        schema = probatio.Schema({probatio.Required(CONF_ANALYSIS_DATE): DateSelector(DateSelectorConfig())})
        provider_name = PROVIDER_NAMES.get(self._pending_provider or "", self._pending_provider or "ICP")
        return self.async_show_form(
            step_id="analysis_date",
            data_schema=self.add_suggested_values_to_schema(schema, user_input),
            description_placeholders={"provider": provider_name},
            errors=errors,
        )
