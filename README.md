<p align="center">
  <img src="custom_components/oceamo_icp/brand/logo.png"
       alt="Reef ICP for Home Assistant"
       width="900">
</p>

# Reef ICP for Home Assistant

A custom Home Assistant integration for importing reef-aquarium ICP analysis reports from multiple laboratory providers.

> **Status:** Early development / beta testing.

## Screenshots

Reef ICP turns uploaded laboratory reports into a provider-independent Home Assistant view with current values, status information and long-term history.

<p align="center">
  <img src="docs/images/dashboard-overview.jpg"
       alt="Reef ICP dashboard overview in Home Assistant"
       width="420">
</p>

<p align="center">
  <strong>Dashboard overview</strong><br>
  Current report, provider/report type, status counts, previous analysis and measurement categories at a glance.
</p>

<table>
  <tr>
    <td align="center"><strong>Measurements & comparison</strong></td>
    <td align="center"><strong>Cross-provider history</strong></td>
  </tr>
  <tr>
    <td align="center">
      <img src="docs/images/measurement-details.jpg"
           alt="Expanded Reef ICP measurement category"
           width="330">
    </td>
    <td align="center">
      <img src="docs/images/multi-provider-history.jpg"
           alt="Reef ICP cross-provider history chart"
           width="330">
    </td>
  </tr>
  <tr>
    <td align="center">
      Target ranges, previous values, changes and trend indicators.
    </td>
    <td align="center">
      Comparable values from different laboratories share one history. The selected point shown here originates from Fauna Marin.
    </td>
  </tr>
</table>

<table>
  <tr>
    <td align="center"><strong>PDF import</strong></td>
    <td align="center"><strong>Home Assistant integration</strong></td>
  </tr>
  <tr>
    <td align="center">
      <img src="docs/images/pdf-import.jpg"
           alt="Reef ICP PDF import dialog"
           width="330">
    </td>
    <td align="center">
      <img src="docs/images/integration-overview.jpg"
           alt="Reef ICP integration overview in Home Assistant"
           width="330">
    </td>
  </tr>
  <tr>
    <td align="center">
      Upload a report. Reef ICP detects the supported laboratory automatically.
    </td>
    <td align="center">
      Imported analytes are exposed as normal Home Assistant entities and long-term statistics.
    </td>
  </tr>
</table>

> Screenshots show a development installation containing test reports from multiple supported laboratories and report types.

## Supported providers

### Oceamo

- Classic Oceamo ICP PDF format
- Oceamo **Reef ICP-MS** / ICP-MS analysis-report format
- Automatic distinction between classic reports (`classic_icp`) and ICP-MS reports (`reef_icp_ms`)
- German classic and English ICP-MS headings / metadata
- Cross-report normalization of English ICP-MS names such as `Boron`, `Potassium`, `Sodium`, `Iodine`, `Copper` and `Tungsten` to the existing Reef ICP analytes
- ICP-MS-only / extended parameters such as SAK/SAC254, Cäsium, Cer, Gallium, Ruthenium, Thorium, Tellur, Neodym and Hafnium when present in the supplied report
- Report metadata and sample timestamp
- Measurements and target values
- Oceamo rating artwork when the embedded icon is recognized; conservative range/limit fallback for changed artwork
- `n.n.` and `n.b.` without converting them to zero
- Interpretation and product recommendation text when present

The ICP-MS parser is designed around Oceamo's publicly documented current parameter set and public English-format analysis-report examples, including the `MSR...` report family. Public reports **MSR229115** and **MSR234022** were used as format/value references for this development step.

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

### TRITON

- Tested legacy TRITON ICP-OES PDF table format from 2014
- Automatic recognition using the legacy TRITON report fingerprints
- 32 analytes in the available real-world test report
- Set points, deviations and aquarium volume
- Reads the green / yellow / red **Warnampel** directly from the PDF drawing stream
- Preserves TRITON one-time and daily dosing recommendations per analyte
- Normalizes comparable analytes into the shared Reef ICP history
- Uses a stable generated provider report ID because this legacy PDF layout does not print an analysis ID
- Uses a date embedded in the PDF filename when available; otherwise falls back to a document date or PDF creation metadata

The currently supported TRITON format is explicitly treated as `triton_legacy_icp`. It is based on a real two-page German TRITON ICP-OES report from 2014. Current TRITON reports may use a different layout and remain a separate compatibility target until a representative modern result is available.

## Provider and report type

Reef ICP stores the laboratory provider separately from a report-type hint. This prepares the integration for different analysis products from the same laboratory, for example classic Oceamo ICP versus **Oceamo Reef ICP-MS**, without treating them as different providers.

Current report-type hints include `classic_icp`, `reef_icp_ms`, `reef_icp`, `ati_icp` and `triton_legacy_icp`. Future parsers can add further types such as ATI Ultimate-MS while keeping the same provider-neutral history model.

## Multi-provider history

Reports from different providers can be stored in the same aquarium.

Comparable analytes are normalized to the same internal key, category and unit. This allows a history such as:

```text
Fauna Marin → Fauna Marin → Oceamo → Oceamo ICP-MS
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
- TRITON (tested legacy ICP-OES format)

If no supported provider can be identified, the import stops instead of guessing. A report is replaced only when both its provider and provider report ID match an already stored report.

## What it currently does

- Install as a HACS custom repository
- Add **Reef ICP** under **Settings → Devices & services**
- Import ICP PDFs directly in Home Assistant
- Store up to 100 reports per aquarium
- Keep reports in chronological sample order
- Keep the newest report as the current sensor state
- Keep one stable sensor per analyte seen in any stored report
- Preserve the newest available analyte result when a later provider omits that parameter
- Create `ICP Status`, `Analysis date` and `Analysis number` sensors
- Preserve non-numeric laboratory states instead of converting them to zero
- Import historic numeric values as Home Assistant external long-term statistics
- Compare the newest ICP with the immediately previous stored ICP
- Combine comparable values from different providers in the same history
- Bundle and automatically load the **Reef ICP Card**
- Open an interactive history chart by tapping a measurement
- Show the provider for the current report, previous report and selected history points
- Label Oceamo ICP-MS reports as `Oceamo · ICP-MS` in the dashboard/history source display

## Current entities

For each aquarium, the integration creates:

- `ICP Status`
- `Analysis date`
- `Analysis number`
- one stable sensor for every analyte that has appeared in any stored report

`ICP Status` contains the complete normalized measurement list, provider metadata, previous-analysis comparison, stored-report summary and statistic IDs used by the bundled card.

### Stable measurement entities across providers

Different laboratories do not always test the same parameter set. Starting with version `0.6.1`, individual measurement entities therefore remain stable across provider changes.

If the newest ICP omits an analyte entirely, the sensor keeps the newest available result from the most recent older report that actually contained that analyte. The sensor exposes `included_in_current_report: false` plus `last_measured_*` and `current_*` attributes so the source of the value remains explicit.

This fallback only applies when the parameter is absent from the newest report. If the newest report contains the analyte but reports `n.n.`, `n.b.`, `n.g.` or ATI `---`, that laboratory result remains current and Reef ICP does not substitute an older numeric value.

The `ICP Status` entity and Reef ICP dashboard card continue to show only measurements that are actually present in the newest report. Carried-forward values therefore never appear as fresh measurements in the main ICP card.

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
- provider and report type
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
- provider, report type and report ID for selected history points

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
- [x] Stable measurement entities when providers omit analytes
- [x] Reef ICP project branding
- [x] README screenshots
- [ ] Show Oceamo interpretation / evaluation text inside the card
- [ ] Show laboratory dosing recommendations inside the card
- [ ] Older ATI layouts and ATI Pro / Ultimate-MS variants
- [x] Oceamo Reef ICP-MS / current ICP-MS report layout
- [x] TRITON legacy ICP-OES (2014 report layout)
- [ ] Current TRITON ICP-OES report layout
- [ ] Reef Factory Smart ICP-OES
- [ ] Additional newer Oceamo report variants if the PDF layout changes
- [ ] Additional ICP laboratories
- [ ] Parser regression tests in the repository
- [ ] First tagged HACS release
- [ ] Optional dosing assistant with explicit safeguards and user approval

## Privacy

ICP reports can contain names, customer numbers and other personal information. Reports are processed locally by Home Assistant.

Private test reports are not included in the public repository.

## Disclaimer

Reef ICP is an independent community project and is not affiliated with or endorsed by Oceamo, Fauna Marin, ATI, TRITON or any other ICP laboratory.

Laboratory reference ranges and recommendations are imported from the supplied reports. Reef ICP does not replace professional aquarium husbandry advice.

---

<p align="center">
  Developed by <strong>Filo Mahlich</strong><br>
  Reef ICP is an independent open-source community project for Home Assistant.
</p>
