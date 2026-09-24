# Changelog

## 0.1.0 - Development

### Added

- Initial HACS-compatible Home Assistant integration structure.
- PDF upload through the Home Assistant config flow.
- Parser for classic Oceamo ICP PDF reports.
- Parsing of metadata, measurement groups, target values and non-detects.
- Extraction of Oceamo green/yellow/red status icons from the tested classic report format.
- Sensor entities for ICP parameters.
- A report/status sensor intended as the data source for the future custom dashboard card.
- Import of additional PDFs through the integration options flow.

### Reviewed against current Home Assistant APIs

- Uses the current `FileSelector` and `file_upload` flow.
- Processes uploaded files on the executor thread as required by Home Assistant.
- Declares `file_upload` as a dependency.
- Uses the current `OptionsFlow.config_entry` property instead of the removed legacy constructor pattern.
- Stores mutable imported reports in config-entry options and uses `OptionsFlowWithReload`.
