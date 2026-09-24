"""Config flow for Reef ICP."""

from __future__ import annotations

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
    FileSelector,
    FileSelectorConfig,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_AQUARIUM_NAME,
    CONF_REPORTS,
    DOMAIN,
    MAX_STORED_REPORTS,
    PROVIDER_OCEAMO,
)
from .parser import (
    IcpParseError,
    UnsupportedIcpProviderError,
    parse_icp_pdf,
)

CONF_PDF_FILE = "pdf_file"


def _parse_uploaded_pdf(
    hass: HomeAssistant,
    uploaded_file_id: str,
) -> dict[str, Any]:
    """Parse a Home Assistant uploaded ICP PDF with provider auto-detection.

    This wrapper is intentionally synchronous because Home Assistant requires
    process_uploaded_file() and its teardown to run in the executor thread.
    """
    with process_uploaded_file(hass, uploaded_file_id) as file_path:
        return parse_icp_pdf(file_path)


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


class ReefIcpConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a Reef ICP config flow."""

    VERSION = 1

    @staticmethod
    @callback
    @override
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlowWithReload:
        """Return the multi-provider import flow."""
        return ReefIcpOptionsFlow()

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Create an aquarium and import its first ICP report."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                report = await self.hass.async_add_executor_job(
                    _parse_uploaded_pdf,
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
                aquarium_name = user_input[CONF_AQUARIUM_NAME].strip()
                return self.async_create_entry(
                    title=aquarium_name,
                    data={CONF_AQUARIUM_NAME: aquarium_name},
                    options={CONF_REPORTS: [report]},
                )

        schema = probatio.Schema(
            {
                probatio.Required(CONF_AQUARIUM_NAME): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.TEXT)
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


class ReefIcpOptionsFlow(OptionsFlowWithReload):
    """Import additional ICP reports from supported providers."""

    @override
    async def async_step_init(
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
            except UnsupportedIcpProviderError:
                errors["base"] = "unsupported_provider"
            except IcpParseError:
                errors["base"] = "invalid_icp_pdf"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                reports = _upsert_report(
                    list(self.config_entry.options.get(CONF_REPORTS, [])),
                    report,
                )
                return self.async_create_entry(
                    title="",
                    data={CONF_REPORTS: reports},
                )

        schema = probatio.Schema(
            {
                probatio.Required(CONF_PDF_FILE): FileSelector(
                    FileSelectorConfig(accept=".pdf,application/pdf")
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(schema, user_input),
            errors=errors,
        )
