# Reef ICP for Home Assistant

A custom Home Assistant integration for importing reef-aquarium ICP analysis reports from multiple laboratory providers.

> **Status:** Early development / beta testing.

## Supported providers

### Oceamo

- Classic Oceamo ICP PDF format
- Report metadata and sample timestamp
- Measurements and target values
- Oceamo green / yellow / red status artwork
- `n.n.` and `n.b.`
- Interpretation and product recommendation text

### Fauna Marin

- Tested Fauna Marin Reef ICP one-page PDF format
- Sample ID, sample date, received date, aquarium volume and sample location
- Macro elements, nutrients, trace elements and potential pollutants
- Reference ranges
- `n.n.` and `n.g.`
- Per-parameter Elementals dosage recommendations
- Water-change recommendations
- Unit normalization for comparable cross-provider history

The Fauna Marin parser has been tested against four real reports from 2022.

### ATI

- Current ATI laboratory PDF layout
- Automatic recognition using ATI-specific PDF fingerprints
- Analysis ID, barcode, aquarium name, volume, reason and laboratory dates
- Basis values, major elements, trace elements, nutrients and pollutants
- ATI ideal values and textual laboratory assessments
- ATI `---` non-detect values are preserved as non-numeric results
- ATI `TOP`, `WENIG`, `ERHÖHT`, `ZU HOCH`, `Achtung` and `Kritisch` assessments are normalized to Reef ICP status levels
- Comparable concentrations are normalized to the shared cross-provider units
- Recommended-action and dosing text is preserved for later card display

The ATI parser has been developed against a real public current-format ATI report from 2026 (analysis ID **372482**). Older ATI layouts and the newer Pro / Ultimate-MS variants remain separate compatibility targets until representative PDFs are available.

## Provider and report type

Reef ICP stores the laboratory provider separately from a report-type hint. This prepares the integration for different analysis products from the same laboratory, for example classic Oceamo ICP versus **Oceamo Reef ICP-MS**, without treating them as different providers.

Current report-type hints include `classic_icp`, `reef_icp` and `ati_icp`. Future parsers can add dedicated types such as Oceamo ICP-MS or ATI Ultimate-MS while keeping the same provider-neutral history model.

## Multi-provider history

Reports from different providers can be stored in the same aquarium.

Comparable analytes are normalized to the same internal key, category and unit. This allows a history such as:

```text
Fauna Marin → Fauna Marin → Oceamo → Oceamo
```

to appear in one Home Assistant long-term statistic and in the bundled history chart.

Examples of normalization:

- Fauna Marin iodine: `mg/l` → `µg/l`
- Fauna Marin ICP phosphorus: `mg/l` → `µg/l`
- Fauna Marin silicon: `mg/l` → `µg/l`
- Fauna Marin `Brom` is normalized to the shared `Bromid` analyte

Measurements that are not directly comparable remain separate. For example, Fauna Marin elemental sulfur is not merged with Oceamo sulfate.

## Importing another ICP

Open **Settings → Devices & services → Reef ICP → Configure** and upload the ICP PDF.

**Reef ICP detects the laboratory automatically.** The detector checks several provider-specific fingerprints in the PDF and then routes the file to the matching parser. The parser validates the detected format again before anything is stored.

Currently detected automatically:

- Oceamo
- Fauna Marin
- ATI

If no supported provider can be identified, the import stops instead of guessing. A report is replaced only when both its provider and provider report ID match an already stored report.

## What it currently does

- Install as a HACS custom repository
- Add **Reef ICP** under **Settings → Devices & services**
- Import ICP PDFs directly in Home Assistant
- Store up to 100 reports per aquarium
- Keep reports in chronological sample order
- Keep the newest report as the current sensor state
- Create one sensor per parameter in the newest report
- Create `ICP Status`, `Analysis date` and `Analysis number` sensors
- Preserve non-numeric laboratory states instead of converting them to zero
- Import historic numeric values as Home Assistant external long-term statistics
- Compare the newest ICP with the immediately previous stored ICP
- Combine comparable values from different providers in the same history
- Bundle and automatically load the **Reef ICP Card**
- Open an interactive history chart by tapping a measurement
- Show the provider for the current report, previous report and selected history points

## Current entities

For each aquarium, the integration creates:

- `ICP Status`
- `Analysis date`
- `Analysis number`
- one sensor for every measurement in the latest report

`ICP Status` contains the complete normalized measurement list, provider metadata, previous-analysis comparison, stored-report summary and statistic IDs used by the bundled card.

## Fauna Marin recommendations

Where present in the PDF, Fauna Marin measurement attributes can contain a structured recommendation.

Example dosage:

```yaml
recommendation:
  type: dose
  amount_ml: 2.7
  days: 2
  product: Elementals Trace I
```

Example water-change recommendation:

```yaml
recommendation:
  type: water_change
  product: Elementals Trace Ba
```

These are imported as laboratory-provided recommendations. Reef ICP does not currently control dosing equipment.

## Status handling

Oceamo status levels come directly from the status artwork embedded in the tested classic PDF.

ATI's current PDF contains textual assessments. Reef ICP maps ATI labels such as `TOP`, `WENIG`, `ERHÖHT`, `ZU HOCH`, `Achtung` and `Kritisch` into the same `ok` / `warning` / `critical` model while preserving the laboratory result itself.

The tested Fauna Marin format does not contain equivalent Oceamo-style severity icons. Reef ICP therefore derives a conservative display status from Fauna Marin's published reference range:

- inside reference range → `ok`
- outside reference range → `warning`
- insufficient information → `unknown`

Fauna Marin values are not automatically labeled `critical`.

## Historical values

Numeric measurements from all stored reports are imported as Home Assistant external long-term statistics.

The original sample timestamp is used when available. Date-only samples are placed at local noon, then rounded to the full hour as required by Home Assistant external statistics.

Provider parsers normalize comparable measurements before statistics are imported. A safety check prevents points with mismatching units from being merged into the same statistic.

`n.n.`, `n.b.`, `n.g.` and ATI `---` non-detect results are never converted to numeric zero.

## Reef ICP dashboard card

The bundled card is still registered internally as:

```yaml
type: custom:oceamo-icp-card
```

The internal tag and integration domain are intentionally kept for backward compatibility with existing installations and dashboards.

In the Home Assistant card picker it appears as **Reef ICP Card**.

The card shows:

- aquarium name
- provider
- latest analysis/report ID and date
- overall status and status counts
- previous analysis and provider
- collapsible categories
- current measurement
- target / reference range
- previous measurement
- change and trend direction
- history availability
- interactive long-term history
- provider and report ID for selected history points

## Backward compatibility

The visible project name is now **Reef ICP**.

The internal Home Assistant domain remains:

```text
oceamo_icp
```

This is deliberate. Changing the domain would break existing config entries, entity unique IDs, external statistic IDs and dashboard resources.

The repository URL also remains unchanged for now:

```text
https://github.com/shdtfy/ha-oceamo-icp
```

## Installation during development

1. Open HACS.
2. Add this repository as a custom **Integration** repository:
   `https://github.com/shdtfy/ha-oceamo-icp`
3. Install **Reef ICP**.
4. Restart Home Assistant.
5. Go to **Settings → Devices & services → Add integration**.
6. Search for **Reef ICP**.
7. Enter an aquarium name and upload the first ICP PDF. Reef ICP detects the provider automatically.

## Roadmap

- [x] Classic Oceamo PDF parser
- [x] Oceamo status artwork extraction
- [x] Fauna Marin Reef ICP PDF parser
- [x] Current ATI laboratory PDF parser
- [x] Automatic provider detection during import
- [x] Cross-provider normalized history
- [x] Long-term statistics
- [x] Previous-ICP comparison
- [x] Bundled dashboard card
- [x] Interactive measurement history
- [ ] Show Oceamo interpretation / evaluation text inside the card
- [ ] Show laboratory dosing recommendations inside the card
- [ ] Older ATI layouts and ATI Pro / Ultimate-MS variants
- [ ] Oceamo Reef ICP-MS and newer Oceamo report formats
- [ ] Additional ICP laboratories
- [ ] Parser regression tests in the repository
- [ ] First tagged HACS release
- [ ] Optional dosing assistant with explicit safeguards and user approval

## Privacy

ICP reports can contain names, customer numbers and other personal information. Reports are processed locally by Home Assistant.

Private test reports are not included in the public repository.

## Disclaimer

Reef ICP is an independent community project and is not affiliated with or endorsed by Oceamo, Fauna Marin or any other ICP laboratory.

Laboratory reference ranges and recommendations are imported from the supplied reports. Reef ICP does not replace professional aquarium husbandry advice.
