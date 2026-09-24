"""Config flow for Oceamo ICP."""

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
)
from .parser import OceamoParseError, parse_oceamo_pdf

CONF_PDF_FILE = "pdf_file"


def _parse_uploaded_pdf(hass: HomeAssistant, uploaded_file_id: str) -> dict[str, Any]:
    """Parse a Home Assistant uploaded PDF.

    This wrapper is intentionally synchronous because Home Assistant requires
    process_uploaded_file() and its teardown to run in the executor thread.
    """
    with process_uploaded_file(hass, uploaded_file_id) as file_path:
        return parse_oceamo_pdf(file_path)


def _upsert_report(
    reports: list[dict[str, Any]], report: dict[str, Any]
) -> list[dict[str, Any]]:
    """Add or replace a report by analysis number and keep chronological order."""
    analysis_number = report["metadata"]["analysis_number"]
    merged = [
        existing
        for existing in reports
        if existing.get("metadata", {}).get("analysis_number") != analysis_number
    ]
    merged.append(report)
    merged.sort(key=lambda item: item.get("metadata", {}).get("analysis_date", ""))
    return merged[-MAX_STORED_REPORTS:]


class OceamoIcpConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle an Oceamo ICP config flow."""

    VERSION = 1

    @staticmethod
    @callback
    @override
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlowWithReload:
        """Return the options flow."""
        return OceamoIcpOptionsFlow()

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Create an Oceamo ICP aquarium and import its first report."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                report = await self.hass.async_add_executor_job(
                    _parse_uploaded_pdf,
                    self.hass,
                    user_input[CONF_PDF_FILE],
                )
            except OceamoParseError:
                errors["base"] = "invalid_oceamo_pdf"
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


class OceamoIcpOptionsFlow(OptionsFlowWithReload):
    """Import additional Oceamo reports."""

    @override
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Upload an additional Oceamo PDF."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                report = await self.hass.async_add_executor_job(
                    _parse_uploaded_pdf,
                    self.hass,
                    user_input[CONF_PDF_FILE],
                )
            except OceamoParseError:
                errors["base"] = "invalid_oceamo_pdf"
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

        return self.async_show_form(
            step_id="init",
            data_schema=probatio.Schema(
                {
                    probatio.Required(CONF_PDF_FILE): FileSelector(
                        FileSelectorConfig(accept=".pdf,application/pdf")
                    )
                }
            ),
            errors=errors,
        )
