"""Config flow for Reef ICP."""

from __future__ import annotations

from pathlib import Path
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
    CONF_REPORTS,
    CONF_SUPPLY_SYSTEM,
    DOMAIN,
    MAX_STORED_REPORTS,
    PROVIDER_OCEAMO,
    SUPPLY_SYSTEM_ATI_ESSENTIALS_PRO,
    SUPPLY_SYSTEM_FAUNA_MARIN_BALLING_LIGHT,
    SUPPLY_SYSTEM_NONE,
    SUPPLY_SYSTEM_OCEAMO_DUO,
    SUPPLY_SYSTEM_TRITON_METHOD,
)
from .parser import (
    IcpParseError,
    MissingAnalysisDateError,
    PROVIDER_NAMES,
    UnsupportedIcpProviderError,
    detect_icp_provider,
    parse_icp_pdf,
)
from .statistics import async_request_statistics_rebuild

CONF_ANALYSIS_DATE = "analysis_date"
CONF_PDF_FILE = "pdf_file"


class PendingAnalysisDateError(Exception):
    """Carry a preserved upload into the manual date-selection step."""

    def __init__(self, pending_pdf_path: str, provider: str) -> None:
        super().__init__("The ICP report needs a manually selected analysis date.")
        self.pending_pdf_path = pending_pdf_path
        self.provider = provider


def _cleanup_pending_pdf(pending_pdf_path: str | None) -> None:
    """Remove a preserved temporary PDF and its private temp directory."""
    if not pending_pdf_path:
        return
    shutil.rmtree(Path(pending_pdf_path).parent, ignore_errors=True)


def _copy_uploaded_pdf(
    hass: HomeAssistant,
    uploaded_file_id: str,
) -> Path:
    """Preserve an uploaded PDF after Home Assistant removes the upload temp dir."""
    temp_dir = Path(tempfile.mkdtemp(prefix="reef_icp_"))
    try:
        with process_uploaded_file(hass, uploaded_file_id) as file_path:
            source_path = Path(file_path)
            filename = source_path.name or "icp-report.pdf"
            preserved_path = temp_dir / filename
            shutil.copy2(source_path, preserved_path)
        return preserved_path
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise


def _parse_uploaded_pdf(
    hass: HomeAssistant,
    uploaded_file_id: str,
) -> dict[str, Any]:
    """Parse an uploaded ICP PDF and preserve it only when a date is missing."""
    preserved_path = _copy_uploaded_pdf(hass, uploaded_file_id)

    try:
        provider = detect_icp_provider(preserved_path)
        report = parse_icp_pdf(preserved_path)
    except MissingAnalysisDateError as err:
        raise PendingAnalysisDateError(str(preserved_path), provider) from err
    except UnsupportedIcpProviderError:
        _cleanup_pending_pdf(str(preserved_path))
        raise
    except IcpParseError:
        _cleanup_pending_pdf(str(preserved_path))
        raise
    except Exception:
        _cleanup_pending_pdf(str(preserved_path))
        raise

    _cleanup_pending_pdf(str(preserved_path))
    return report


def _normalize_selected_date(value: Any) -> str:
    """Return a Home Assistant date-selector value as YYYY-MM-DD."""
    if hasattr(value, "isoformat"):
        value = value.isoformat()
    date_value = str(value).strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_value):
        raise ValueError("Invalid analysis date.")
    return date_value


def _normalize_aquarium_volume(value: Any) -> float:
    """Return a positive aquarium net volume in liters."""
    volume = float(value)
    if volume <= 0:
        raise ValueError("Aquarium volume must be greater than zero.")
    return volume


def _normalize_supply_system(value: Any) -> str:
    """Return a non-empty supply-system identifier or custom name."""
    system = str(value).strip()
    if not system:
        raise ValueError("Supply system must not be empty.")
    return system


def _supply_system_options(hass: HomeAssistant) -> list[SelectOptionDict]:
    """Return localized preset labels while still allowing custom systems."""
    is_german = str(hass.config.language or "").lower().startswith("de")
    no_system = (
        "Kein Versorgungssystem / nur Analyse"
        if is_german
        else "No dosing system / analysis only"
    )
    return [
        SelectOptionDict(value=SUPPLY_SYSTEM_NONE, label=no_system),
        SelectOptionDict(
            value=SUPPLY_SYSTEM_FAUNA_MARIN_BALLING_LIGHT,
            label="Fauna Marin Balling Light",
        ),
        SelectOptionDict(
            value=SUPPLY_SYSTEM_ATI_ESSENTIALS_PRO,
            label="ATI Essentials pro",
        ),
        SelectOptionDict(
            value=SUPPLY_SYSTEM_TRITON_METHOD,
            label="TRITON Method",
        ),
        SelectOptionDict(
            value=SUPPLY_SYSTEM_OCEAMO_DUO,
            label="Oceamo DUO",
        ),
    ]


def _volume_selector() -> NumberSelector:
    """Return the aquarium net-volume selector."""
    return NumberSelector(
        NumberSelectorConfig(
            min=1,
            max=100000,
            step=1,
            unit_of_measurement="L",
            mode=NumberSelectorMode.BOX,
        )
    )


def _supply_system_selector(hass: HomeAssistant) -> SelectSelector:
    """Return the persistent supply-system selector."""
    return SelectSelector(
        SelectSelectorConfig(
            options=_supply_system_options(hass),
            mode=SelectSelectorMode.DROPDOWN,
            custom_value=True,
        )
    )


def _parse_pending_pdf_with_date(
    pending_pdf_path: str,
    selected_date: Any,
) -> dict[str, Any]:
    """Reparse a preserved supported report with the user-selected date."""
    source_path = Path(pending_pdf_path)
    if not source_path.exists():
        raise IcpParseError("The preserved uploaded PDF is no longer available.")

    date_value = _normalize_selected_date(selected_date)
    return parse_icp_pdf(
        source_path,
        analysis_date_override=date_value,
    )


def _report_provider(report: dict[str, Any]) -> str:
    """Return provider, treating legacy stored reports as Oceamo."""
    return str(
        report.get("provider")
        or report.get("metadata", {}).get("provider")
        or PROVIDER_OCEAMO
    )


def _report_identity(report: dict[str, Any]) -> tuple[str, str]:
    """Return a stable provider-specific report identity."""
    metadata = report.get("metadata", {})
    analysis_number = str(
        metadata.get("provider_report_id")
        or metadata.get("analysis_number")
        or ""
    )
    return (_report_provider(report), analysis_number)


def _report_sort_key(report: dict[str, Any]) -> str:
    """Sort reports by sample time, falling back to report date."""
    metadata = report.get("metadata", {})
    return str(
        metadata.get("sample_taken")
        or metadata.get("analysis_date")
        or ""
    )


def _upsert_report(
    reports: list[dict[str, Any]], report: dict[str, Any]
) -> list[dict[str, Any]]:
    """Add or replace a provider report and keep chronological order."""
    identity = _report_identity(report)
    merged = [
        existing
        for existing in reports
        if _report_identity(existing) != identity
    ]
    merged.append(report)
    merged.sort(key=_report_sort_key)
    return merged[-MAX_STORED_REPORTS:]


def _updated_options_with_reports(
    entry: ConfigEntry,
    reports: list[dict[str, Any]],
) -> dict[str, Any]:
    """Preserve aquarium profile settings while updating stored reports."""
    options = dict(entry.options)
    options[CONF_REPORTS] = reports
    return options


class ReefIcpConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a Reef ICP config flow."""

    VERSION = 1

    _pending_pdf_path: str | None = None
    _pending_provider: str | None = None
    _pending_aquarium_name: str | None = None
    _pending_aquarium_volume_l: float | None = None
    _pending_supply_system: str | None = None

    @staticmethod
    @callback
    @override
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlowWithReload:
        """Return the multi-provider import and aquarium-settings flow."""
        return ReefIcpOptionsFlow()

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Create an aquarium profile and import its first ICP report."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                aquarium_name = str(user_input[CONF_AQUARIUM_NAME]).strip()
                aquarium_volume_l = _normalize_aquarium_volume(
                    user_input[CONF_AQUARIUM_VOLUME_L]
                )
                supply_system = _normalize_supply_system(
                    user_input[CONF_SUPPLY_SYSTEM]
                )
                if not aquarium_name:
                    raise ValueError("Aquarium name must not be empty.")
            except (TypeError, ValueError):
                errors["base"] = "invalid_aquarium_profile"
            else:
                try:
                    report = await self.hass.async_add_executor_job(
                        _parse_uploaded_pdf,
                        self.hass,
                        user_input[CONF_PDF_FILE],
                    )
                except PendingAnalysisDateError as err:
                    self._pending_pdf_path = err.pending_pdf_path
                    self._pending_provider = err.provider
                    self._pending_aquarium_name = aquarium_name
                    self._pending_aquarium_volume_l = aquarium_volume_l
                    self._pending_supply_system = supply_system
                    return await self.async_step_analysis_date()
                except UnsupportedIcpProviderError:
                    errors["base"] = "unsupported_provider"
                except IcpParseError:
                    errors["base"] = "invalid_icp_pdf"
                except Exception:  # noqa: BLE001
                    errors["base"] = "unknown"
                else:
                    return self.async_create_entry(
                        title=aquarium_name,
                        data={CONF_AQUARIUM_NAME: aquarium_name},
                        options={
                            CONF_REPORTS: [report],
                            CONF_AQUARIUM_VOLUME_L: aquarium_volume_l,
                            CONF_SUPPLY_SYSTEM: supply_system,
                        },
                    )

        schema = probatio.Schema(
            {
                probatio.Required(CONF_AQUARIUM_NAME): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.TEXT)
                ),
                probatio.Required(CONF_AQUARIUM_VOLUME_L): _volume_selector(),
                probatio.Required(CONF_SUPPLY_SYSTEM): _supply_system_selector(
                    self.hass
                ),
                probatio.Required(CONF_PDF_FILE): FileSelector(
                    FileSelectorConfig(accept=".pdf,application/pdf")
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(schema, user_input),
            errors=errors,
        )

    async def async_step_analysis_date(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the analysis date when the uploaded first report has none."""
        errors: dict[str, str] = {}

        if (
            self._pending_pdf_path is None
            or self._pending_aquarium_name is None
            or self._pending_aquarium_volume_l is None
            or self._pending_supply_system is None
        ):
            return await self.async_step_user()

        if user_input is not None:
            try:
                report = await self.hass.async_add_executor_job(
                    _parse_pending_pdf_with_date,
                    self._pending_pdf_path,
                    user_input[CONF_ANALYSIS_DATE],
                )
            except IcpParseError:
                errors["base"] = "invalid_icp_pdf"
            except (TypeError, ValueError):
                errors["base"] = "invalid_analysis_date"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                await self.hass.async_add_executor_job(
                    _cleanup_pending_pdf,
                    self._pending_pdf_path,
                )
                aquarium_name = self._pending_aquarium_name
                aquarium_volume_l = self._pending_aquarium_volume_l
                supply_system = self._pending_supply_system

                self._pending_pdf_path = None
                self._pending_provider = None
                self._pending_aquarium_name = None
                self._pending_aquarium_volume_l = None
                self._pending_supply_system = None

                return self.async_create_entry(
                    title=aquarium_name,
                    data={CONF_AQUARIUM_NAME: aquarium_name},
                    options={
                        CONF_REPORTS: [report],
                        CONF_AQUARIUM_VOLUME_L: aquarium_volume_l,
                        CONF_SUPPLY_SYSTEM: supply_system,
                    },
                )

        schema = probatio.Schema(
            {
                probatio.Required(CONF_ANALYSIS_DATE): DateSelector(
                    DateSelectorConfig()
                ),
            }
        )
        provider_name = PROVIDER_NAMES.get(
            self._pending_provider or "",
            self._pending_provider or "ICP",
        )
        return self.async_show_form(
            step_id="analysis_date",
            data_schema=self.add_suggested_values_to_schema(schema, user_input),
            description_placeholders={"provider": provider_name},
            errors=errors,
        )


class ReefIcpOptionsFlow(OptionsFlowWithReload):
    """Manage aquarium settings and import additional ICP reports."""

    _pending_pdf_path: str | None = None
    _pending_provider: str | None = None

    @override
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let the user choose between importing ICP data and aquarium settings."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["import_icp", "aquarium_settings"],
        )

    async def async_step_import_icp(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Upload another ICP PDF and detect its provider automatically."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                report = await self.hass.async_add_executor_job(
                    _parse_uploaded_pdf,
                    self.hass,
                    user_input[CONF_PDF_FILE],
                )
            except PendingAnalysisDateError as err:
                self._pending_pdf_path = err.pending_pdf_path
                self._pending_provider = err.provider
                return await self.async_step_analysis_date()
            except UnsupportedIcpProviderError:
                errors["base"] = "unsupported_provider"
            except IcpParseError:
                errors["base"] = "invalid_icp_pdf"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                existing_reports = list(
                    self.config_entry.options.get(CONF_REPORTS, [])
                )
                replacing_existing = any(
                    _report_identity(existing) == _report_identity(report)
                    for existing in existing_reports
                )
                reports = _upsert_report(existing_reports, report)
                if replacing_existing:
                    async_request_statistics_rebuild(
                        self.hass,
                        self.config_entry,
                        [*existing_reports, report],
                    )
                return self.async_create_entry(
                    title="",
                    data=_updated_options_with_reports(
                        self.config_entry,
                        reports,
                    ),
                )

        schema = probatio.Schema(
            {
                probatio.Required(CONF_PDF_FILE): FileSelector(
                    FileSelectorConfig(accept=".pdf,application/pdf")
                ),
            }
        )

        return self.async_show_form(
            step_id="import_icp",
            data_schema=self.add_suggested_values_to_schema(schema, user_input),
            errors=errors,
        )

    async def async_step_aquarium_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Edit net aquarium volume and the persistent supply system."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                aquarium_volume_l = _normalize_aquarium_volume(
                    user_input[CONF_AQUARIUM_VOLUME_L]
                )
                supply_system = _normalize_supply_system(
                    user_input[CONF_SUPPLY_SYSTEM]
                )
            except (TypeError, ValueError):
                errors["base"] = "invalid_aquarium_profile"
            else:
                options = dict(self.config_entry.options)
                options[CONF_AQUARIUM_VOLUME_L] = aquarium_volume_l
                options[CONF_SUPPLY_SYSTEM] = supply_system
                return self.async_create_entry(title="", data=options)

        suggested: dict[str, Any] = {
            CONF_SUPPLY_SYSTEM: self.config_entry.options.get(
                CONF_SUPPLY_SYSTEM,
                SUPPLY_SYSTEM_NONE,
            ),
        }
        if volume := self.config_entry.options.get(CONF_AQUARIUM_VOLUME_L):
            suggested[CONF_AQUARIUM_VOLUME_L] = volume

        schema = probatio.Schema(
            {
                probatio.Required(CONF_AQUARIUM_VOLUME_L): _volume_selector(),
                probatio.Required(CONF_SUPPLY_SYSTEM): _supply_system_selector(
                    self.hass
                ),
            }
        )
        return self.async_show_form(
            step_id="aquarium_settings",
            data_schema=self.add_suggested_values_to_schema(
                schema,
                user_input or suggested,
            ),
            errors=errors,
        )

    async def async_step_analysis_date(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for a missing analysis date before storing an additional report."""
        errors: dict[str, str] = {}

        if self._pending_pdf_path is None:
            return await self.async_step_import_icp()

        if user_input is not None:
            try:
                report = await self.hass.async_add_executor_job(
                    _parse_pending_pdf_with_date,
                    self._pending_pdf_path,
                    user_input[CONF_ANALYSIS_DATE],
                )
            except IcpParseError:
                errors["base"] = "invalid_icp_pdf"
            except (TypeError, ValueError):
                errors["base"] = "invalid_analysis_date"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                await self.hass.async_add_executor_job(
                    _cleanup_pending_pdf,
                    self._pending_pdf_path,
                )
                self._pending_pdf_path = None
                self._pending_provider = None

                existing_reports = list(
                    self.config_entry.options.get(CONF_REPORTS, [])
                )
                replacing_existing = any(
                    _report_identity(existing) == _report_identity(report)
                    for existing in existing_reports
                )
                reports = _upsert_report(existing_reports, report)
                if replacing_existing:
                    async_request_statistics_rebuild(
                        self.hass,
                        self.config_entry,
                        [*existing_reports, report],
                    )
                return self.async_create_entry(
                    title="",
                    data=_updated_options_with_reports(
                        self.config_entry,
                        reports,
                    ),
                )

        schema = probatio.Schema(
            {
                probatio.Required(CONF_ANALYSIS_DATE): DateSelector(
                    DateSelectorConfig()
                ),
            }
        )
        provider_name = PROVIDER_NAMES.get(
            self._pending_provider or "",
            self._pending_provider or "ICP",
        )
        return self.async_show_form(
            step_id="analysis_date",
            data_schema=self.add_suggested_values_to_schema(schema, user_input),
            description_placeholders={"provider": provider_name},
            errors=errors,
        )
