# Changelog

## 0.11.4 - Development

### Added

- Added **Fauna Marin Elementals Trace Se** to the Balling Light recommendation rules.
- The calculation uses Fauna Marin's published strength of **1 ml per 100 l for +0.5 µg/l selenium**.
- Added Fauna Marin's published maximum daily increase of **+1 µg/l selenium**.

### Fixed

- Selenium can now appear in provider-independent recommendations when the aquarium uses **Fauna Marin Balling Light** and the current ICP contains a low numeric selenium result.

### Tested

- For the supplied Oceamo Reef ICP-MS report `MSR234022`, a selenium value of **0.097 µg/l** with a target lower bound of **0.2 µg/l** and an aquarium net volume of **54 l** produces a correction dose of approximately **0.111 ml Fauna Marin Elementals Trace Se**.

## 0.11.3 - Development

### Fixed

- Fixed current Oceamo Reef ICP-MS reports showing valid measurements as `unknown` when the PDF used newer 27x27 / 40x40 rating artwork instead of the older 15x15 classic icons.
- Oceamo rating artwork is now recognized by its green / yellow / red status color and arrow direction instead of relying only on a fixed image size and previously known hashes.
- Kept the existing known classic Oceamo icon hashes as an exact compatibility path.

### Tested

- `MSR229115`: 70 measurements, **57 OK, 6 warning, 7 critical, 0 unknown**.
- `MSR234022`: 70 measurements, **57 OK, 8 warning, 5 critical, 0 unknown**.
- `OC186791` classic regression test: 47 measurements, **35 OK, 8 warning, 4 critical, 0 unknown**.

## 0.11.2 - Development

### Added

- Added **Oceamo Single Elements Selen** correction support.
- Oceamo Selen uses the published strength of 1 ml per 100 l for +0.05 µg/l and the published maximum daily increase of +0.05 µg/l.
- Selen correction is calculated only when the current report is an Oceamo Reef ICP-MS report (`reef_icp_ms`).

### Safety

- Oceamo states that selenium should only be dosed from an ICP-MS analysis because the recommended range lies below the reliable ICP-OES detection limit.
- A low selenium result from a non-ICP-MS report therefore produces an informational `requires_icp_ms` recommendation instead of a calculated supplement dose.
- Elevated selenium can still produce the existing reduce/pause guidance because that action does not calculate an addition dose.

### Changed

- The recommendation engine now receives the current report type so product rules can require a specific analytical method.
- Updated the integration and bundled dashboard card version to `0.11.2`.

## 0.11.1 - Development

### Added

- Added a provider-confirmation step after uploading an ICP PDF during both initial setup and later imports.
- The confirmation view shows the automatically detected laboratory and, when already available, the report type, analysis ID and analysis date.
- Users can override the detected laboratory with any supported provider before the report is stored.
- Added explicit provider parsing so the manually selected parser validates the PDF instead of silently trusting the override.

### Changed

- Uploaded PDFs remain temporarily preserved until provider confirmation and any required manual analysis-date step are complete.
- A selected provider is retained through the manual analysis-date fallback, so an override is not lost when the report needs a date.
- Updated the integration version to `0.11.1`.

## 0.11.0 - Development

### Changed

- Completed the project-wide rename to **Reef ICP**.
- Changed the Home Assistant integration domain to `reef_icp`.
- Renamed the custom integration directory to `custom_components/reef_icp`.
- Renamed the bundled dashboard card to `reef-icp-card.js`.
- Changed the Lovelace card type to `custom:reef-icp-card`.
- Changed the bundled frontend resource path to `/reef_icp/reef-icp-card.js`.
- Changed Reef ICP external statistic IDs to use the `reef_icp:` prefix.
- Updated repository, documentation and issue-tracker references to `shdtfy/ha-reef-icp`.
- Updated the integration and bundled dashboard card version to `0.11.0`.

### Breaking

- Existing test installations using the previous internal namespace should be removed and installed again.

## 0.10.2 - Development

### Added

- Added ATI ICP Element correction support for **Barium**, **Selen** and **Vanadium**.
- Barium uses ATI's published strength of 1 ml per 100 l for +1 µg/l.
- Selen uses ATI's published strength of 1 ml per 100 l for +0.5 µg/l.
- Vanadium uses ATI's published strength of 1 ml per 100 l for +5 µg/l.

### Changed

- Cross-checked all implemented ATI ICP Element product strengths against ATI's current ICP Elements documentation.
- ATI corrections continue to use total correction amounts only; no automatic multi-day split limit is implemented for ATI.
- Updated the integration version to `0.10.2`.

## 0.10.1 - Development

### Changed

- Moved the expandable supply recommendations below the measurement categories and the laboratory interpretation to the bottom of the card.
- Show the calculated daily concentration increase alongside split correction doses.
- Show a precise measuring reminder for correction doses below 1 ml per day.
- Updated the dashboard card cache version to `0.10.1`.

## 0.10.0 - Development

### Added

- Expanded the provider-independent recommendation engine beyond Fauna Marin Balling Light.
- Added **ATI Essentials pro** correction support using published **ATI ICP Elements** product strengths.
- Added **Oceamo DUO** KH correction plus supported **Oceamo Single Elements** corrections.
- Added **TRITON Method / Core7 Flex** recommendation guidance using TRITON's official single-element and Core7 calculators instead of inventing unpublished concentration factors.
- Added individual element correction calculations for supported trace/minor elements such as **Iod, Fluorid, Molybdän, Mangan, Lithium, Kalium, Bor and Strontium**.
- Added manufacturer source links to each generated recommendation.
- Added automatic multi-day splitting when the manufacturer publishes a maximum daily concentration increase.
- Added generic dose-unit support so recommendations can represent both liquid `ml` and solid `g` products.

### Changed

- The recommendation card now distinguishes **Grundversorgung** and **Einzelelement** corrections.
- Daily maintenance guidance is now specific to the selected supply system.
- If a manufacturer strength is known but no official daily maximum is implemented, Reef ICP shows the total correction with a warning instead of inventing a daily schedule.
- Updated the bundled dashboard card cache and integration version to `0.10.0`.

### Safety / scope

- Calculated values are correction doses derived from normalized ICP values, aquarium net volume and published manufacturer product strengths.
- Reef ICP does not treat these correction values as permanent daily maintenance doses.
- TRITON numeric single-element dosing remains delegated to TRITON's official calculator because the public calculator exposes the result rather than a static concentration table.


## 0.9.2 - Development

### Fixed

- Added the alternate classic Oceamo status-icon artwork used by real report `OC186791`.
- Reef ICP can now read the green, yellow and red Oceamo rating icons from this older classic PDF instead of falling back to `unknown` for exact-target values.
- This fixes the report showing 15 unnecessary `Unklar` measurements even though Oceamo printed a rating icon for every row.

### Tested

- Regression-tested the supplied real Oceamo report `OC186791` from 22.01.2022.
- Verified all **47 measurements** receive a provider rating: **35 OK, 8 warning, 4 critical, 0 unknown**.
- Verified high/low direction for Bromid, Magnesium, Barium, Fluorid, Lithium, Molybdän, Aluminium, Phosphat, Gesamtphosphor, Nitrit and Silicium against the printed Oceamo artwork.


## 0.9.1 - Development

### Added

- Added the first provider-independent supply-system recommendation engine.
- **Fauna Marin Balling Light** now calculates correction amounts for calcium, magnesium and alkalinity from the aquarium's stored net volume plus normalized ICP current/target values.
- The calculation works independently of the laboratory that produced the ICP report.
- Added `supply_recommendations` to the `ICP Status` sensor attributes.
- Added a separate collapsible **Recommendations for your supply system** panel to the bundled card.

### Changed

- The laboratory interpretation panel is now collapsed by default and can be expanded on demand.
- Balling Light amounts are explicitly labelled as correction doses rather than permanent daily maintenance dosing.
- Trace-element corrections are not guessed. The card states that Balling Trace / Elementals support still requires product-specific dosing rules and additional stock-solution context.
- Updated the bundled card cache and integration version to `0.9.1`.


## 0.9.0 - Development

### Added

- Added a persistent aquarium profile with **net water volume** and **dosing / supply system**.
- New aquariums now require both profile values before the first ICP is imported.
- Added built-in supply-system presets for **Fauna Marin Balling Light**, **ATI Essentials pro**, **TRITON Method** and **Oceamo DUO**, plus analysis-only mode and support for custom system names.
- Added a new options menu with separate **Import another ICP analysis** and **Aquarium settings** actions.
- Existing aquariums can add or change their volume and supply system without touching stored ICP reports.
- Exposed `aquarium_volume_l`, `supply_system` and `supply_system_name` on the Reef ICP status sensor.
- Added aquarium profile chips to the bundled dashboard card.
- Added the provider-independent **Laboratory interpretation** panel to the card when the current report contains interpretation/evaluation text.

### Changed

- Aquarium profile settings are preserved automatically when new ICP reports are imported or existing reports are replaced.
- Laboratory choice and supply-system choice are now explicitly independent in the data model.
- The bundled card cache/version is now `0.9.0`.
- Updated the integration version to `0.9.0`.

### Foundation for next step

- System-specific recommendations will use the normalized ICP values together with the aquarium's stored net water volume and supply system.
- Original laboratory product recommendations remain stored in report data but are not treated as the aquarium's primary dosing recommendation.


## 0.8.5 - Development

### Fixed

- Replacing an already stored ICP report now also repairs its Home Assistant long-term statistics.
- Previously, changing a report date replaced the report in Reef ICP storage but left the old timestamped recorder point behind because external statistics are keyed by statistic ID plus timestamp.
- Reef ICP now detects provider/report-ID replacements, clears the affected Reef ICP statistic IDs, waits for the recorder clear operation to finish, and rebuilds those statistics exclusively from the currently stored reports.
- This removes stale points such as the legacy TRITON PDF creation-date point while keeping the corrected manually selected analysis date.

### Changed

- Statistics cleanup is requested only when an existing provider/report identity is replaced. Normal new-report imports continue using the lightweight incremental statistics import.
- The rebuild request is transient and is consumed during the automatic config-entry reload triggered by the options flow.
- Updated the integration version to `0.8.5`.


## 0.8.4 - Development

### Fixed

- Fixed the manual analysis-date form failing with an unexpected error after a date was selected.
- `config_flow.py` used `re.fullmatch()` to validate the selected `YYYY-MM-DD` value but was missing the `re` import, causing a `NameError` at submission time.
- Manual date selection can now continue to reparsing and storing the supported ICP report.

### Changed

- Updated the integration version to `0.8.4`.


## 0.8.3 - Development

### Fixed

- Fixed the manual analysis-date fallback not opening after version `0.8.2`.
- The parser correctly raised `MissingAnalysisDateError`, but the upload wrapper accidentally caught the flow-only `PendingAnalysisDateError` instead. The parser error therefore fell through to the generic invalid-PDF handling.
- Supported reports without a trustworthy date now correctly transition to the Home Assistant date-selector step while preserving the uploaded PDF for reparsing.

### Changed

- Updated the integration version to `0.8.3`.



## 0.8.2 - Development

### Added

- Generalized the missing-analysis-date fallback so it applies to **all supported providers**, not only legacy TRITON.
- Added a shared parser-level `MissingAnalysisDateError` and a provider-independent date resolver.
- Added common filename-date recognition for `YYYYMMDD`, `YYYY-MM-DD`, `YYYY_MM_DD`, `DD.MM.YYYY`, `DD-MM-YYYY` and `DD_MM_YYYY`.
- The manual Home Assistant date selector now reparses the original preserved PDF with an explicit date override instead of temporarily renaming the PDF.

### Changed

- Reef ICP now uses the same trusted date priority for every provider: report date → parsed sample date → filename date → manual selection.
- PDF `CreationDate` metadata is deliberately ignored because it can represent PDF export time rather than the laboratory analysis date.
- Updated the integration version to `0.8.2`.
- Updated German and English config-flow text and README documentation for the provider-independent date handling.

### Fixed

- Fixed the tested 2014 TRITON PDF being silently dated `2014-10-18` from its PDF creation metadata even though the actual archived analysis date was `2014-09-25`.
- A supported report without any trustworthy date now reliably reaches the manual date-selection step.


## 0.8.1 - Development

### Added

- Added a manual analysis-date fallback to both the initial setup flow and the **Import another ICP analysis** options flow.
- If Reef ICP recognizes and parses a supported report but cannot determine a reliable analysis date from the PDF, filename or PDF metadata, Home Assistant now opens a native date selector instead of rejecting the report.
- The selected date is stored as the report's `analysis_date` with `analysis_date_source: manual`.
- The uploaded PDF is preserved only for the duration of the fallback step so it can be reparsed after the date is selected; normal successful and failed imports clean up their temporary copy immediately.
- The fallback is provider-neutral at the config-flow level and currently fixes date-less legacy TRITON reports such as the tested 2014 PDF without requiring a renamed file.

### Changed

- Updated the integration version to `0.8.1`.
- Updated German and English config-flow text for the new analysis-date step.
- Updated the README to document the manual date fallback.


## 0.8.0 - Development

### Added

- Added automatic detection and parsing for the tested **legacy TRITON ICP-OES** PDF family (`report_type: triton_legacy_icp`), covering the supplied 2014 and 2015 layouts.
- Added canonical normalization for the 32 analytes in the supplied 2014 report and 33 analytes in the supplied 2015 report so comparable TRITON values share existing Reef ICP entities and long-term statistics.
- Added extraction of TRITON set points, deviations and aquarium volume.
- Added support for the later legacy dosing headers `Korrektur Dosierung` / `Erhaltungs Dosierung` in addition to `Einmalige Dosierung` / `Tägliche Dosierung`.
- Added handling for the 2015 PDF extraction quirk where the `mL` header label is attached to the first analyte row of each table.
- Added Beryllium (`Be`) from the supplied 2015 report and mapped it to the existing shared Reef ICP Beryllium analyte.
- Added printed legacy TRITON report-ID extraction; report `296B` now uses `296B` instead of a generated fallback ID.
- Added direct reading of the legacy TRITON green / yellow / red **Warnampel** rectangles from the PDF drawing stream and mapped them to Reef ICP `ok` / `warning` / `critical` status levels.
- Added per-analyte TRITON one-time and daily dosing recommendations when the report contains non-zero dosing values.
- Added a stable generated provider report ID for legacy TRITON PDFs that do not print a report/analysis ID.
- Added legacy TRITON report-date fallback handling: filename `YYYYMMDD` first, then a date printed in the PDF, then PDF creation metadata.
- Added `TRITON · Legacy ICP-OES` source labels to the bundled dashboard/history card.

### Changed

- Updated the integration and bundled dashboard card to `0.8.0`.
- Updated the README supported-provider list, automatic detection section and roadmap for TRITON legacy support.

### Tested

- Parsed the supplied real two-page TRITON ICP-OES report from 2014 with **32 measurements**.
- Verified extraction of **25 OK, 5 warning and 2 critical** warning-light results from the 2014 report artwork.
- Parsed the supplied real two-page TRITON ICP-OES report `296B` from 2015 with **33 measurements**.
- Verified extraction of **26 OK, 3 warning and 4 critical** warning-light results from the 2015 report artwork.
- Verified the 2015 report ID `296B`, filename-derived date `2015-10-14` and the additional Beryllium measurement.
- Verified TRITON calcium, magnesium, iodine, barium, phosphorus/phosphate and dosing fields against the supplied source reports.
- Regression-tested Oceamo Classic (**47 measurements**), four Fauna Marin reports (**37 each**), ATI current layout (**40**) and the Oceamo ICP-MS fixture (**56**) after broadening the TRITON parser.

## 0.7.0 - Development

### Added

- Added **Oceamo Reef ICP-MS** support while keeping Oceamo as the same provider and storing the format as `report_type: reef_icp_ms`.
- Added automatic detection of English Oceamo `Analysis Report` PDFs and `MSR...` analysis IDs in addition to the existing German classic format.
- Added English ICP-MS category headings (`Main Parameters`, `Main Elements`, `Trace Elements`, `Pollutants`, `Nutrients`) and common RO/DI section headings.
- Added canonical name mapping so English ICP-MS analytes share the existing entities and long-term statistics with matching classic Oceamo values.
- Added support for the ICP-MS DOC surrogate `SAK254` / `SAC254` and its `m-1` unit.
- Added mappings for ICP-MS extended / ultra-trace elements including caesium, cerium, gallium, ruthenium, thorium, tellurium, neodymium, tungsten, uranium and hafnium when they occur in a report.
- Added conservative status fallback from published target ranges/limits when a newer Oceamo PDF uses rating artwork that Reef ICP does not recognize yet.
- The dashboard/history source label now distinguishes Oceamo ICP-MS points as **Oceamo · ICP-MS**.

### Changed

- Generalized the Oceamo parser so classic and ICP-MS reports share one provider-neutral code path instead of creating a second Oceamo provider.
- German classic analyte keys remain unchanged for backward compatibility with existing entity IDs and external statistic IDs.
- Updated the integration and bundled dashboard card to `0.7.0`.

### Tested

- Regression-tested parsing of the existing classic Oceamo report `OC188727`.
- Regression-tested all four available Fauna Marin reports and the existing ATI current-layout test report.
- Tested the new ICP-MS parser path with a representative English `MSR...` report fixture covering main parameters, main elements, trace elements, pollutants, nutrients and RO/DI water.
- Development was cross-checked against Oceamo's current published ICP-MS parameter list and public report examples including `MSR229115` and `MSR234022`.

## 0.6.1 - Development

### Fixed

- Measurement entities no longer become unavailable merely because the newest provider does not include that analyte.
- Reef ICP now keeps the newest available result for every analyte that has appeared in any stored report.
- A current non-detect or undetermined result (`n.n.`, `n.b.`, `n.g.` or ATI `---`) still remains the current result and is never replaced by an older numeric value.

### Added

- Added `included_in_current_report` to measurement entities so carried-forward results are explicitly distinguishable from values measured in the newest ICP.
- Added `last_measured_*` attributes with the provider, report ID, date, sample timestamp and report type that supplied the sensor state.
- Added `current_*` report attributes alongside carried-forward results for clear provenance.
- Added the new Reef ICP icon and wide project logo.

### Changed

- Individual measurement entities now use the union of analytes across all stored reports while the `ICP Status` entity and Reef ICP dashboard card remain strict views of the newest report.
- Updated the bundled card cache version and integration version to `0.6.1`.

## 0.6.0 - Development

### Added

- Added automatic detection and parsing for the current ATI laboratory PDF format.
- Added ATI metadata including analysis ID, barcode, aquarium name, net volume, analysis reason and laboratory dates.
- Added ATI basis values, major elements, trace elements, nutrients and pollutants to the shared provider-neutral measurement model.
- Added ATI ideal values and normalization of textual assessments such as `TOP`, `WENIG`, `ERHÖHT`, `ZU HOCH`, `Achtung` and `Kritisch`.
- Added handling for ATI `---` non-detect values without converting them to numeric zero.
- Added safe ATI concentration-unit conversion before cross-provider statistics are merged.
- Added extraction of ATI recommended-action text and ICP Elements / supplement dosing text for future dashboard display.
- Added report-type metadata so future formats such as Oceamo Reef ICP-MS and ATI Ultimate-MS can be distinguished from the laboratory provider itself.

### Changed

- Updated the bundled card and integration version to `0.6.0`.
- Stored-report and status attributes now expose a report-type hint when available.
- Existing Oceamo and Fauna Marin imports remain backward compatible and continue using the same entity and statistic IDs.

### Tested

- Regression-tested the parser against the existing Oceamo test report and all four available Fauna Marin reports.
- Developed and validated the ATI parser against the structure and values of a real public 2026 ATI report (analysis ID `372482`).

## 0.5.0 - Development

### Added

- Renamed the integration and dashboard card to **Reef ICP**.
- Added automatic provider detection to the initial setup and Configure/options import flow.
- Added **Fauna Marin** as the second supported ICP provider.
- Provider detection uses multiple provider-specific PDF fingerprints and each parser validates the detected format again.
- Added parsing for the tested one-page Fauna Marin Reef ICP PDF format.
- Added Fauna Marin sample metadata including sample ID, sample date, received date, aquarium volume and sample location.
- Added parsing of Fauna Marin per-parameter Elementals dosage recommendations and water-change recommendations.
- Added normalized provider metadata to reports, measurements, sensors and stored-report summaries.
- Added provider labels to the dashboard header, previous-analysis row and history-point details.
- Added cross-provider analyte normalization so directly comparable measurements can share the same long-term statistic.
- Added unit normalization for Fauna Marin iodine, ICP phosphorus and silicon.

### Changed

- Reports are now deduplicated by provider plus provider report ID instead of report number alone.
- Reports are sorted by sample timestamp when available, with report date as fallback.
- Fauna Marin reference ranges are conservatively mapped to `ok`, `warning` or `unknown`; the parser does not invent a `critical` level.
- External statistic import now refuses to merge points with incompatible units.
- Updated the bundled card and integration version to `0.5.0`.

### Compatibility

- The Home Assistant domain is `reef_icp`.
- The custom card tag is `custom:reef-icp-card`.
- Existing test installations using the previous namespace should be removed and installed again.

## 0.4.1 - Development

### Fixed

- Fixed a typo in the measurement-map helper that caused the Oceamo sensor platform to fail during setup after updating to version 0.4.0.
- Restored all Oceamo sensor entities and the `ICP Status` dashboard-card data source.
- Updated the bundled dashboard card and integration version to `0.4.1`.

## 0.4.0 - Development

### Added

- Added a dedicated interactive history view for individual ICP measurements.
- Measurement rows in the Oceamo ICP dashboard card are now clickable when long-term statistics are available.
- Clicking a measurement opens a modal history card with all imported numeric ICP values for that parameter.
- The history view shows a time-series line chart, the current value, previous value, absolute change and target value or target range.
- Target ranges are visualized directly in the chart, and individual data points can be selected for their date, analysis number and measured value.
- The `ICP Status` sensor now exposes each measurement's external Home Assistant statistic ID to the dashboard card.

### Changed

- Updated the bundled dashboard card and integration version to `0.4.0`.
- Expanded the dashboard card with a small history indicator on measurements that support the new detail view.

## 0.3.3 - Development

### Added

- Added compact per-category status summaries to the Oceamo ICP dashboard card.
- Category headers now show the number of green, yellow, red and unknown measurements using small status dots and counts.
- Added localized tooltips to category total counters so it is immediately clear that the number represents measurements.

### Changed

- Refined category-header spacing for desktop and mobile layouts.
- Updated the bundled card and integration version to `0.3.3`.

## 0.3.2 - Development

### Added

- Added bundled integration branding under `custom_components/reef_icp/brand/`.
- Added a dedicated `icon.png` for the Home Assistant integration.
- Added a dedicated `logo.png` for the integration and project branding.
- Added the Oceamo ICP logo as the header banner in the repository README.

### Changed

- Polished the bundled Oceamo ICP dashboard card for mobile and desktop layouts.
- Kept the overall analysis status in the title row on narrow screens instead of moving it below the header.
- Added labels to the green, yellow and red status counters.
- Refined category headers, status markers, spacing and typography.
- Added a subtle theme-aware header glow while keeping Home Assistant theme colors.
- Delta badges now indicate whether the current value moved closer to or farther from the target value or target range.
- Category open/closed state is preserved while the card is live.
- Updated the card's internal version to `0.3.2`.

## 0.3.1 - Development

### Fixed

- Fixed the bundled dashboard card not appearing in the Home Assistant card picker.
- The card is now registered as a versioned Lovelace module in storage mode in addition to the frontend module registration.
- The existing Lovelace resource collection is explicitly loaded before it is modified, so resources from HACS and other integrations are preserved.
- Existing Oceamo card resource entries are updated in place instead of duplicated.

## 0.3.0 - Development

### Added

- Added the first bundled `Oceamo ICP Card` for Home Assistant dashboards.
- The integration now serves and automatically loads the card through the Home Assistant frontend.
- No separate HACS frontend repository and no manual Lovelace resource entry are required.
- Added a visual editor for choosing the `ICP Status` entity, an optional title and previous-analysis display.
- Card shows analysis metadata, overall status, status counts, collapsible categories, targets, previous values, deltas and trend direction.
- Added German and English card labels.
- Added mobile-responsive card styling.

### Changed

- Added `frontend` as an integration dependency.
- Updated the README with card installation and usage instructions.

## 0.2.5 - Development

### Added

- Added comparison data between the latest ICP and the immediately previous stored ICP.
- Each current measurement now exposes `has_previous`, `previous_value`, `previous_raw_value`, `previous_display_value`, previous report metadata, `delta` and `trend`.
- The `ICP Status` sensor now exposes the same enriched measurement list for the future dashboard card.
- Added previous analysis metadata to the `ICP Status` sensor.

### Changed

- Updated the README to reflect long-term statistics, the analysis-number entity and historical comparison support.

## 0.2.4 - Development

### Fixed

- Added a one-time entity-registry migration for the `Analysis number` sensor.
- Keeps the existing entity ID and user customizations while moving the sensor
  to a fresh unique ID.
- Removes a stale unavailable state before the migrated entity is re-added.
- This targets installations where the analysis-number sensor was introduced
  after the Oceamo config entry already existed.

## 0.2.3 - Development

### Fixed

- Made all PDF-backed Oceamo sensors explicitly non-polling.
- Simplified the `Analysis number` sensor to publish its string value and attributes directly during entity creation.

## 0.2.2 - Development

### Added

- Added a dedicated `Analysis number` sensor for the newest imported Oceamo report.
- The analysis-number sensor also exposes analysis date, sample timestamp and tank type as attributes.

## 0.2.1 - Development

### Fixed

- Fixed invalid external statistic IDs on Home Assistant installations using uppercase config-entry IDs.
- Statistic IDs are now normalized to lowercase Home Assistant-compatible slugs before import.

## 0.2.0 - Development

### Added

- Historical ICP values as Home Assistant external long-term statistics.
- Statistics use the original sample timestamp from each Oceamo report.
- Sample timestamps are rounded down to the hour because Home Assistant external statistics require hourly timestamps.
- Numeric ICP values are stored with mean/min/max values for graphing.
- `n.n.` and `n.b.` values are never converted to numeric zero.
- `historical_statistic_id` attribute on measurement sensors.
- `display_value` attribute, including `Nicht nachweisbar` and `Nicht bestimmt`.
- Compact `stored_reports` history on the `ICP Status` sensor.

### Changed

- Added `recorder` as a dependency.

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
