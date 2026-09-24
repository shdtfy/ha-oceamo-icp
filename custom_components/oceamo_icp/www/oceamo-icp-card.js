const CARD_VERSION = "0.6.1";
const CARD_TAG = "oceamo-icp-card";
const HISTORY_CARD_TAG = "oceamo-icp-history-card";

const CATEGORY_ORDER = [
  "basic",
  "major_elements",
  "trace_elements",
  "pollutants",
  "nutrients",
  "osmosis",
];

const CATEGORY_ICONS = {
  basic: "mdi:test-tube",
  major_elements: "mdi:atom",
  trace_elements: "mdi:molecule",
  pollutants: "mdi:alert-decagram-outline",
  nutrients: "mdi:sprout-outline",
  osmosis: "mdi:water-check-outline",
};

const TEXT = {
  de: {
    cardName: "Reef ICP",
    noEntity: "Bitte einen ICP-Status-Sensor auswählen.",
    entityMissing: "Die konfigurierte Entität ist nicht verfügbar.",
    invalidEntity: "Diese Entität enthält keine unterstützten ICP-Messwerte.",
    previous: "Vorher",
    target: "Soll",
    notDetectable: "Nicht nachweisbar",
    notDetermined: "Nicht bestimmt",
    unknown: "Unbekannt",
    ok: "Kein Handlungsbedarf",
    warning: "Beobachten",
    critical: "Handlungsbedarf",
    statusUnknown: "Status unbekannt",
    okShort: "OK",
    warningShort: "Warnung",
    criticalShort: "Kritisch",
    unknownShort: "Unklar",
    showPrevious: "Vorherige ICP anzeigen",
    entity: "ICP-Status-Entität",
    title: "Titel (optional)",
    improved: "Näher am Sollwert",
    worsened: "Weiter vom Sollwert entfernt",
    unchanged: "Abstand zum Sollwert unverändert",
    measurement: "Messwert",
    measurements: "Messwerte",
    history: "Verlauf",
    current: "Aktuell",
    change: "Veränderung",
    analyses: "Analysen",
    loadingHistory: "Verlauf wird geladen …",
    noHistory: "Für diesen Messwert sind noch keine numerischen Verlaufsdaten vorhanden.",
    historyError: "Die Verlaufsdaten konnten nicht geladen werden.",
    close: "Schließen",
    selectPoint: "Messpunkt auswählen",
    categories: {
      basic: "Grundparameter",
      major_elements: "Mengenelemente",
      trace_elements: "Spurenelemente",
      pollutants: "Schadstoffe",
      nutrients: "Nährstoffe",
      osmosis: "Osmose-Check",
      unknown: "Weitere Werte",
    },
  },
  en: {
    cardName: "Reef ICP",
    noEntity: "Please select an ICP status sensor.",
    entityMissing: "The configured entity is not available.",
    invalidEntity: "This entity does not contain supported ICP measurements.",
    previous: "Previous",
    target: "Target",
    notDetectable: "Not detectable",
    notDetermined: "Not determined",
    unknown: "Unknown",
    ok: "No action required",
    warning: "Observe",
    critical: "Action required",
    statusUnknown: "Status unknown",
    okShort: "OK",
    warningShort: "Warning",
    criticalShort: "Critical",
    unknownShort: "Unknown",
    showPrevious: "Show previous ICP",
    entity: "ICP status entity",
    title: "Title (optional)",
    improved: "Closer to target",
    worsened: "Further from target",
    unchanged: "Target distance unchanged",
    measurement: "measurement",
    measurements: "measurements",
    history: "History",
    current: "Current",
    change: "Change",
    analyses: "analyses",
    loadingHistory: "Loading history …",
    noHistory: "No numeric history is available for this measurement yet.",
    historyError: "The history data could not be loaded.",
    close: "Close",
    selectPoint: "Select data point",
    categories: {
      basic: "Basic parameters",
      major_elements: "Major elements",
      trace_elements: "Trace elements",
      pollutants: "Pollutants",
      nutrients: "Nutrients",
      osmosis: "RO/DI check",
      unknown: "Other values",
    },
  },
};

function languageFor(hass) {
  const language = hass?.language || hass?.locale?.language || "en";
  return language.toLowerCase().startsWith("de") ? "de" : "en";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function dateLabel(value, language) {
  if (!value) return "";
  const parsed = new Date(`${value}T12:00:00`);
  if (Number.isNaN(parsed.getTime())) return String(value);
  return new Intl.DateTimeFormat(language === "de" ? "de-DE" : "en-GB", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(parsed);
}

function numericLabel(value, language, digits = 6) {
  if (typeof value !== "number" || Number.isNaN(value)) return "";
  return new Intl.NumberFormat(language === "de" ? "de-DE" : "en-GB", {
    maximumFractionDigits: digits,
  }).format(value);
}

function measurementValue(measurement, language, previous = false) {
  const raw = previous
    ? measurement.previous_raw_value
    : measurement.raw_value;
  const numeric = previous
    ? measurement.previous_value
    : measurement.value;

  if (raw === "n.n.") return TEXT[language].notDetectable;
  if (raw === "n.b." || raw === "n.g.") return TEXT[language].notDetermined;

  let display;
  if (raw !== undefined && raw !== null && raw !== "") {
    display = String(raw);
  } else if (typeof numeric === "number") {
    display = numericLabel(numeric, language);
  } else {
    return TEXT[language].unknown;
  }

  return measurement.unit ? `${display} ${measurement.unit}` : display;
}

function targetLabel(measurement, language) {
  const target = measurement.target;
  if (!target || !target.type) return "";

  const unit = measurement.unit ? ` ${measurement.unit}` : "";
  const n = (value) => numericLabel(value, language);

  switch (target.type) {
    case "exact":
      return `${n(target.value)}${unit}`;
    case "range":
      return `${n(target.min)}–${n(target.max)}${unit}`;
    case "upper_limit":
      return `< ${n(target.max)}${unit}`;
    case "lower_limit":
      return `> ${n(target.min)}${unit}`;
    case "not_detectable":
      return TEXT[language].notDetectable;
    case "not_determined":
      return TEXT[language].notDetermined;
    default:
      return "";
  }
}

function trendSymbol(trend) {
  if (trend === "up") return "↑";
  if (trend === "down") return "↓";
  if (trend === "same") return "→";
  return "";
}

function targetDistance(value, target) {
  if (typeof value !== "number" || Number.isNaN(value) || !target?.type) {
    return null;
  }

  switch (target.type) {
    case "exact":
      return typeof target.value === "number"
        ? Math.abs(value - target.value)
        : null;
    case "range":
      if (typeof target.min !== "number" || typeof target.max !== "number") {
        return null;
      }
      if (value < target.min) return target.min - value;
      if (value > target.max) return value - target.max;
      return 0;
    case "upper_limit":
      if (typeof target.max !== "number") return null;
      return value <= target.max ? 0 : value - target.max;
    case "lower_limit":
      if (typeof target.min !== "number") return null;
      return value >= target.min ? 0 : target.min - value;
    default:
      return null;
  }
}

function targetProgress(measurement) {
  const currentDistance = targetDistance(measurement.value, measurement.target);
  const previousDistance = targetDistance(
    measurement.previous_value,
    measurement.target
  );

  if (currentDistance === null || previousDistance === null) return "neutral";

  const epsilon = 1e-9;
  if (currentDistance < previousDistance - epsilon) return "improved";
  if (currentDistance > previousDistance + epsilon) return "worsened";
  return "same";
}


function parseStoredReportDate(report) {
  const value = report?.sample_taken || report?.analysis_date;
  if (!value) return null;
  const normalized = value.includes("T") ? value : `${value}T12:00:00`;
  const parsed = new Date(normalized);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function historyDateLabel(value, language) {
  const parsed = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(parsed.getTime())) return "";
  return new Intl.DateTimeFormat(language === "de" ? "de-DE" : "en-GB", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(parsed);
}


function providerLabel(value) {
  if (!value) return "";
  if (value === "oceamo") return "Oceamo";
  if (value === "fauna_marin") return "Fauna Marin";
  return String(value);
}

class OceamoIcpHistoryCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = undefined;
    this._measurement = undefined;
    this._reports = [];
    this._language = "en";
    this._points = [];
    this._requestId = 0;
  }

  configure({ hass, measurement, reports, language }) {
    this._hass = hass;
    this._measurement = measurement;
    this._reports = Array.isArray(reports) ? reports : [];
    this._language = language || "en";
    this._points = [];
    this._load();
  }

  async _load() {
    const requestId = ++this._requestId;
    const t = TEXT[this._language];
    this._renderMessage("mdi:chart-line", t.loadingHistory, true);

    const statisticId = this._measurement?.historical_statistic_id;
    if (!this._hass?.callWS || !statisticId) {
      this._renderMessage("mdi:chart-line", t.noHistory);
      return;
    }

    const { start, end } = this._historyRange();

    try {
      const result = await this._hass.callWS({
        type: "recorder/statistics_during_period",
        start_time: start.toISOString(),
        end_time: end.toISOString(),
        statistic_ids: [statisticId],
        period: "hour",
        types: ["mean"],
      });

      if (requestId !== this._requestId) return;

      const rawPoints = Array.isArray(result?.[statisticId])
        ? result[statisticId]
        : [];

      this._points = rawPoints
        .filter((point) => typeof point?.mean === "number")
        .map((point) => ({
          start: Number(point.start),
          value: Number(point.mean),
        }))
        .filter(
          (point) =>
            Number.isFinite(point.start) && Number.isFinite(point.value)
        )
        .sort((a, b) => a.start - b.start);

      this._render();
    } catch (error) {
      console.warn("Reef ICP history load failed", error);
      if (requestId !== this._requestId) return;
      this._renderMessage("mdi:alert-circle-outline", t.historyError);
    }
  }

  _historyRange() {
    const reportDates = this._reports
      .map(parseStoredReportDate)
      .filter((value) => value instanceof Date);

    if (!reportDates.length) {
      const end = new Date();
      const start = new Date(end);
      start.setFullYear(start.getFullYear() - 10);
      return { start, end };
    }

    const timestamps = reportDates.map((value) => value.getTime());
    const day = 24 * 60 * 60 * 1000;
    return {
      start: new Date(Math.min(...timestamps) - 2 * day),
      end: new Date(Math.max(...timestamps) + 2 * day),
    };
  }

  _reportForPoint(timestamp) {
    const day = 24 * 60 * 60 * 1000;
    let closest = null;
    let closestDistance = Infinity;

    for (const report of this._reports) {
      const date = parseStoredReportDate(report);
      if (!date) continue;
      const distance = Math.abs(date.getTime() - timestamp);
      if (distance < closestDistance && distance <= 2 * day) {
        closest = report;
        closestDistance = distance;
      }
    }
    return closest;
  }

  _summaryValue(value) {
    if (typeof value !== "number" || Number.isNaN(value)) return "—";
    const formatted = numericLabel(value, this._language);
    return this._measurement?.unit
      ? `${formatted} ${this._measurement.unit}`
      : formatted;
  }

  _changeValue() {
    const delta = this._measurement?.delta;
    if (typeof delta !== "number" || Number.isNaN(delta)) return "—";
    const sign = delta > 0 ? "+" : "";
    const formatted = numericLabel(delta, this._language);
    return this._measurement?.unit
      ? `${sign}${formatted} ${this._measurement.unit}`
      : `${sign}${formatted}`;
  }

  _targetGraphic(y, plotLeft, plotRight) {
    const target = this._measurement?.target;
    if (!target?.type) return "";

    const line = (value) => {
      if (typeof value !== "number") return "";
      const yPos = y(value);
      return `
        <line
          class="target-line"
          x1="${plotLeft}"
          y1="${yPos}"
          x2="${plotRight}"
          y2="${yPos}"
        ></line>
      `;
    };

    if (
      target.type === "range" &&
      typeof target.min === "number" &&
      typeof target.max === "number"
    ) {
      const top = y(target.max);
      const bottom = y(target.min);
      return `
        <rect
          class="target-band"
          x="${plotLeft}"
          y="${Math.min(top, bottom)}"
          width="${plotRight - plotLeft}"
          height="${Math.abs(bottom - top)}"
          rx="4"
        ></rect>
        ${line(target.min)}
        ${line(target.max)}
      `;
    }

    if (target.type === "exact") return line(target.value);
    if (target.type === "upper_limit") return line(target.max);
    if (target.type === "lower_limit") return line(target.min);
    return "";
  }

  _chart() {
    const points = this._points;
    if (!points.length) return "";

    const width = 640;
    const height = 270;
    const plotLeft = 56;
    const plotRight = width - 20;
    const plotTop = 18;
    const plotBottom = height - 46;

    const target = this._measurement?.target || {};
    const yValues = points.map((point) => point.value);
    for (const candidate of [target.value, target.min, target.max]) {
      if (typeof candidate === "number") yValues.push(candidate);
    }

    let yMin = Math.min(...yValues);
    let yMax = Math.max(...yValues);
    if (yMin === yMax) {
      const padding = Math.max(Math.abs(yMin) * 0.08, 1);
      yMin -= padding;
      yMax += padding;
    } else {
      const padding = (yMax - yMin) * 0.1;
      yMin -= padding;
      yMax += padding;
    }

    const xMin = points[0].start;
    const xMax = points[points.length - 1].start;
    const x = (timestamp) =>
      xMin === xMax
        ? (plotLeft + plotRight) / 2
        : plotLeft +
          ((timestamp - xMin) / (xMax - xMin)) * (plotRight - plotLeft);
    const y = (value) =>
      plotBottom -
      ((value - yMin) / (yMax - yMin)) * (plotBottom - plotTop);

    const path =
      points.length > 1
        ? points
            .map(
              (point, index) =>
                `${index === 0 ? "M" : "L"} ${x(point.start).toFixed(
                  2
                )} ${y(point.value).toFixed(2)}`
            )
            .join(" ")
        : "";

    const grid = Array.from({ length: 5 }, (_, index) => {
      const ratio = index / 4;
      const value = yMax - ratio * (yMax - yMin);
      const yPos = plotTop + ratio * (plotBottom - plotTop);
      return `
        <line
          class="grid-line"
          x1="${plotLeft}"
          y1="${yPos}"
          x2="${plotRight}"
          y2="${yPos}"
        ></line>
        <text class="axis-value" x="${plotLeft - 9}" y="${yPos + 4}">
          ${escapeHtml(numericLabel(value, this._language, 4))}
        </text>
      `;
    }).join("");

    const labelIndexes =
      points.length <= 4
        ? points.map((_, index) => index)
        : [0, Math.floor((points.length - 1) / 2), points.length - 1];

    const xLabels = [...new Set(labelIndexes)]
      .map((index) => {
        const point = points[index];
        return `
          <text
            class="axis-date"
            x="${x(point.start)}"
            y="${height - 17}"
            text-anchor="${
              index === 0
                ? "start"
                : index === points.length - 1
                  ? "end"
                  : "middle"
            }"
          >
            ${escapeHtml(historyDateLabel(point.start, this._language))}
          </text>
        `;
      })
      .join("");

    const circles = points
      .map((point, index) => {
        const report = this._reportForPoint(point.start);
        const analysis = report?.analysis_number
          ? ` · ${report.analysis_number}`
          : "";
        const provider = report?.provider_name || providerLabel(report?.provider);
        const source = provider ? ` · ${provider}` : "";
        const title = `${historyDateLabel(
          point.start,
          this._language
        )}${analysis}${source} · ${this._summaryValue(point.value)}`;

        return `
          <circle
            class="chart-point${index === points.length - 1 ? " selected" : ""}"
            data-index="${index}"
            cx="${x(point.start)}"
            cy="${y(point.value)}"
            r="5.5"
            tabindex="0"
            role="button"
            aria-label="${escapeHtml(title)}"
          >
            <title>${escapeHtml(title)}</title>
          </circle>
        `;
      })
      .join("");

    return `
      <div class="chart-wrap">
        <svg
          class="history-chart"
          viewBox="0 0 ${width} ${height}"
          role="img"
          aria-label="${escapeHtml(this._measurement?.name || "")}"
        >
          ${grid}
          ${this._targetGraphic(y, plotLeft, plotRight)}
          ${
            path
              ? `<path class="history-line" d="${path}"></path>`
              : ""
          }
          ${circles}
          ${xLabels}
        </svg>
      </div>
    `;
  }

  _pointDetail(index) {
    const point = this._points[index];
    if (!point) return "";
    const report = this._reportForPoint(point.start);
    const analysis = report?.analysis_number || "";
    const provider = report?.provider_name || providerLabel(report?.provider);
    const sourceLabel = [analysis, provider].filter(Boolean).join(" · ");
    return `
      <span>${escapeHtml(historyDateLabel(point.start, this._language))}</span>
      ${
        sourceLabel
          ? `<strong>${escapeHtml(sourceLabel)}</strong>`
          : ""
      }
      <strong>${escapeHtml(this._summaryValue(point.value))}</strong>
    `;
  }

  _wirePoints() {
    const points = this.shadowRoot?.querySelectorAll(".chart-point") || [];
    const select = (element) => {
      const index = Number(element.dataset.index);
      this.shadowRoot
        ?.querySelectorAll(".chart-point")
        .forEach((point) => point.classList.remove("selected"));
      element.classList.add("selected");
      const detail = this.shadowRoot?.querySelector(".point-detail");
      if (detail) detail.innerHTML = this._pointDetail(index);
    };

    points.forEach((element) => {
      element.addEventListener("click", () => select(element));
      element.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          select(element);
        }
      });
    });
  }

  _renderMessage(icon, message, loading = false) {
    this.shadowRoot.innerHTML = `
      <style>${this._styles()}</style>
      <div class="history-message">
        <ha-icon icon="${escapeHtml(icon)}" class="${loading ? "spin" : ""}"></ha-icon>
        <span>${escapeHtml(message)}</span>
      </div>
    `;
  }

  _render() {
    const t = TEXT[this._language];
    if (!this._points.length) {
      this._renderMessage("mdi:chart-line", t.noHistory);
      return;
    }

    const name = this._measurement?.name || this._measurement?.key || "—";
    const current = measurementValue(this._measurement || {}, this._language);
    const previous = this._measurement?.has_previous
      ? measurementValue(this._measurement, this._language, true)
      : "—";
    const target = targetLabel(this._measurement || {}, this._language);
    const latestPointIndex = this._points.length - 1;

    this.shadowRoot.innerHTML = `
      <style>${this._styles()}</style>
      <div class="history-card">
        <div class="history-heading">
          <div class="history-icon">
            <ha-icon icon="mdi:chart-line"></ha-icon>
          </div>
          <div class="history-heading-text">
            <div class="history-title">${escapeHtml(name)}</div>
            <div class="history-subtitle">
              ${escapeHtml(t.history)}
              · ${escapeHtml(this._points.length)} ${escapeHtml(t.analyses)}
            </div>
          </div>
        </div>

        <div class="history-summary">
          <div class="summary-item">
            <span>${escapeHtml(t.current)}</span>
            <strong>${escapeHtml(current)}</strong>
          </div>
          <div class="summary-item">
            <span>${escapeHtml(t.previous)}</span>
            <strong>${escapeHtml(previous)}</strong>
          </div>
          <div class="summary-item">
            <span>${escapeHtml(t.change)}</span>
            <strong>${escapeHtml(this._changeValue())}</strong>
          </div>
        </div>

        ${
          target
            ? `
              <div class="target-hint">
                <ha-icon icon="mdi:target"></ha-icon>
                <span>${escapeHtml(t.target)}: ${escapeHtml(target)}</span>
              </div>
            `
            : ""
        }

        ${this._chart()}

        <div class="point-detail" aria-live="polite">
          ${this._pointDetail(latestPointIndex)}
        </div>
      </div>
    `;

    this._wirePoints();
  }

  _styles() {
    return `
      :host {
        display: block;
        color: var(--primary-text-color);
      }

      .history-card {
        min-width: 0;
      }

      .history-heading {
        display: flex;
        align-items: center;
        gap: 11px;
        padding-right: 42px;
      }

      .history-icon {
        display: grid;
        place-items: center;
        width: 42px;
        height: 42px;
        flex: 0 0 auto;
        border-radius: 14px;
        color: var(--primary-color);
        background: color-mix(
          in srgb,
          var(--primary-color) 13%,
          transparent
        );
      }

      .history-heading-text {
        min-width: 0;
      }

      .history-title {
        overflow: hidden;
        color: var(--primary-text-color);
        font-size: 1.12rem;
        font-weight: 750;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .history-subtitle {
        margin-top: 3px;
        color: var(--secondary-text-color);
        font-size: 0.76rem;
      }

      .history-summary {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 7px;
        margin-top: 16px;
      }

      .summary-item {
        min-width: 0;
        padding: 9px 10px;
        border-radius: 12px;
        background: var(--secondary-background-color);
      }

      .summary-item span {
        display: block;
        color: var(--secondary-text-color);
        font-size: 0.67rem;
      }

      .summary-item strong {
        display: block;
        margin-top: 4px;
        overflow-wrap: anywhere;
        color: var(--primary-text-color);
        font-size: 0.8rem;
      }

      .target-hint {
        display: flex;
        align-items: center;
        gap: 6px;
        margin-top: 11px;
        color: var(--secondary-text-color);
        font-size: 0.75rem;
      }

      .target-hint ha-icon {
        color: var(--primary-color);
        --mdc-icon-size: 16px;
      }

      .chart-wrap {
        margin-top: 8px;
        overflow: hidden;
        border-radius: 13px;
        background: color-mix(
          in srgb,
          var(--secondary-background-color) 56%,
          transparent
        );
      }

      .history-chart {
        display: block;
        width: 100%;
        height: auto;
        min-height: 210px;
        overflow: visible;
      }

      .grid-line {
        stroke: var(--divider-color);
        stroke-width: 1;
      }

      .axis-value,
      .axis-date {
        fill: var(--secondary-text-color);
        font-family: sans-serif;
        font-size: 10px;
      }

      .history-line {
        fill: none;
        stroke: var(--primary-color);
        stroke-linecap: round;
        stroke-linejoin: round;
        stroke-width: 3;
      }

      .target-band {
        fill: var(--success-color, #43a047);
        opacity: 0.1;
      }

      .target-line {
        stroke: var(--success-color, #43a047);
        stroke-dasharray: 5 5;
        stroke-width: 1.4;
        opacity: 0.75;
      }

      .chart-point {
        cursor: pointer;
        fill: var(--ha-card-background, var(--card-background-color));
        stroke: var(--primary-color);
        stroke-width: 3;
        transition:
          r 120ms ease,
          stroke-width 120ms ease;
      }

      .chart-point.selected {
        r: 7;
        stroke-width: 4;
      }

      .chart-point:focus-visible {
        outline: none;
        stroke: var(--primary-text-color);
      }

      .point-detail {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        justify-content: space-between;
        gap: 5px 12px;
        min-height: 22px;
        margin-top: 8px;
        color: var(--secondary-text-color);
        font-size: 0.74rem;
      }

      .point-detail strong {
        color: var(--primary-text-color);
        font-weight: 650;
      }

      .history-message {
        display: flex;
        min-height: 180px;
        align-items: center;
        justify-content: center;
        gap: 10px;
        color: var(--secondary-text-color);
        text-align: center;
      }

      .history-message ha-icon {
        color: var(--primary-color);
      }

      .spin {
        animation: oceamo-history-spin 1s linear infinite;
      }

      @keyframes oceamo-history-spin {
        to {
          transform: rotate(360deg);
        }
      }

      @media (max-width: 520px) {
        .history-summary {
          gap: 5px;
        }

        .summary-item {
          padding: 8px 7px;
        }

        .summary-item span {
          font-size: 0.62rem;
        }

        .summary-item strong {
          font-size: 0.73rem;
        }

        .history-chart {
          min-height: 190px;
        }
      }

      @media (prefers-reduced-motion: reduce) {
        .spin {
          animation: none;
        }
      }
    `;
  }
}

if (!customElements.get(HISTORY_CARD_TAG)) {
  customElements.define(HISTORY_CARD_TAG, OceamoIcpHistoryCard);
}

class OceamoIcpCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = undefined;
    this._lastState = undefined;
    this._openCategories = null;
  }

  static getConfigForm() {
    const documentLanguage =
      document.documentElement.lang || navigator.language || "en";
    const language = documentLanguage.toLowerCase().startsWith("de")
      ? "de"
      : "en";
    const t = TEXT[language];

    return {
      schema: [
        {
          name: "entity",
          required: true,
          selector: {
            entity: {
              filter: {
                domain: "sensor",
              },
            },
          },
        },
        {
          name: "title",
          selector: {
            text: {},
          },
        },
        {
          name: "show_previous",
          selector: {
            boolean: {},
          },
        },
      ],
      computeLabel: (schema) => {
        if (schema.name === "entity") return t.entity;
        if (schema.name === "title") return t.title;
        if (schema.name === "show_previous") return t.showPrevious;
        return undefined;
      },
    };
  }

  static getStubConfig(hass) {
    const state = Object.values(hass?.states || {}).find((candidate) => {
      const attrs = candidate?.attributes || {};
      return (
        candidate.entity_id?.startsWith("sensor.") &&
        Array.isArray(attrs.measurements) &&
        "analysis_number" in attrs &&
        "status_counts" in attrs
      );
    });

    return {
      entity: state?.entity_id || "",
      show_previous: true,
    };
  }

  setConfig(config) {
    this._config = {
      show_previous: true,
      ...config,
    };
    this._lastState = undefined;
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    const state = this._config.entity
      ? hass?.states?.[this._config.entity]
      : undefined;

    if (state !== this._lastState) {
      this._lastState = state;
      this._render();
    }
  }

  getCardSize() {
    const measurements =
      this._lastState?.attributes?.measurements?.length || 0;
    return Math.max(4, Math.ceil(measurements / 5) + 3);
  }

  getGridOptions() {
    return {
      columns: 12,
      min_columns: 6,
    };
  }

  _wireCategoryToggles() {
    this.shadowRoot?.querySelectorAll("details.category").forEach((details) => {
      details.addEventListener("toggle", () => {
        if (this._openCategories === null) this._openCategories = new Set();
        if (details.open) {
          this._openCategories.add(details.dataset.category);
        } else {
          this._openCategories.delete(details.dataset.category);
        }
      });
    });
  }

  _isCategoryOpen(category, index, hasBasic) {
    if (this._openCategories !== null) {
      return this._openCategories.has(category);
    }
    return category === "basic" || (index === 0 && !hasBasic);
  }

  _render() {
    if (!this.shadowRoot) return;

    const language = languageFor(this._hass);
    const t = TEXT[language];

    if (!this._config.entity) {
      this.shadowRoot.innerHTML = this._messageCard(t.cardName, t.noEntity);
      return;
    }

    const state = this._hass?.states?.[this._config.entity];
    if (!state) {
      this.shadowRoot.innerHTML = this._messageCard(
        t.cardName,
        t.entityMissing
      );
      return;
    }

    const attrs = state.attributes || {};
    const measurements = Array.isArray(attrs.measurements)
      ? attrs.measurements
      : [];

    if (!measurements.length) {
      this.shadowRoot.innerHTML = this._messageCard(
        t.cardName,
        t.invalidEntity
      );
      return;
    }

    const friendlyName =
      attrs.friendly_name || this._config.entity || t.cardName;
    const inferredTitle = friendlyName.replace(/\s+ICP Status$/i, "");
    const title = this._config.title?.trim() || inferredTitle || t.cardName;
    const analysisNumber = attrs.analysis_number || "—";
    const analysisDate = dateLabel(attrs.analysis_date, language);
    const providerName = attrs.provider_name || providerLabel(attrs.provider);
    const counts = attrs.status_counts || {};
    const overall = state.state || "unknown";
    const previousAnalysis = attrs.previous_analysis_number;
    const previousDate = dateLabel(attrs.previous_analysis_date, language);
    const previousProvider =
      attrs.previous_provider_name || providerLabel(attrs.previous_provider);

    const grouped = new Map();
    for (const measurement of measurements) {
      const category = measurement.category || "unknown";
      if (!grouped.has(category)) grouped.set(category, []);
      grouped.get(category).push(measurement);
    }

    const categories = [
      ...CATEGORY_ORDER.filter((key) => grouped.has(key)),
      ...[...grouped.keys()].filter((key) => !CATEGORY_ORDER.includes(key)),
    ];

    this.shadowRoot.innerHTML = `
      <style>${this._styles()}</style>
      <ha-card>
        <div class="header">
          <div class="title-row">
            <div class="brand-icon">
              <ha-icon icon="mdi:test-tube"></ha-icon>
            </div>
            <div class="title-wrap">
              <div class="title">${escapeHtml(title)}</div>
              <div class="meta">
                ${escapeHtml(analysisNumber)}
                ${analysisDate ? ` · ${escapeHtml(analysisDate)}` : ""}
                ${providerName ? ` · ${escapeHtml(providerName)}` : ""}
              </div>
            </div>
            <div class="overall ${escapeHtml(overall)}">
              ${escapeHtml(this._overallLabel(overall, language))}
            </div>
          </div>

          <div class="status-strip">
            ${this._statusCount("ok", counts.ok || 0, t.okShort)}
            ${this._statusCount(
              "warning",
              counts.warning || 0,
              t.warningShort
            )}
            ${this._statusCount(
              "critical",
              counts.critical || 0,
              t.criticalShort
            )}
            ${
              counts.unknown
                ? this._statusCount(
                    "unknown",
                    counts.unknown || 0,
                    t.unknownShort
                  )
                : ""
            }
          </div>

          ${
            previousAnalysis && this._config.show_previous !== false
              ? `
                <div class="previous-analysis">
                  <ha-icon icon="mdi:history"></ha-icon>
                  <span>${escapeHtml(t.previous)}</span>
                  <strong>${escapeHtml(previousAnalysis)}</strong>
                  ${
                    previousDate
                      ? `<span class="previous-date">· ${escapeHtml(
                          previousDate
                        )}</span>`
                      : ""
                  }
                  ${
                    previousProvider
                      ? `<span class="previous-date">· ${escapeHtml(
                          previousProvider
                        )}</span>`
                      : ""
                  }
                </div>
              `
              : ""
          }
        </div>

        <div class="categories">
          ${categories
            .map((category, index) =>
              this._category(
                category,
                grouped.get(category),
                language,
                this._isCategoryOpen(category, index, grouped.has("basic"))
              )
            )
            .join("")}
        </div>

        <dialog class="history-dialog">
          <div class="history-dialog-inner">
            <button
              class="history-close"
              type="button"
              title="${escapeHtml(t.close)}"
              aria-label="${escapeHtml(t.close)}"
            >
              <ha-icon icon="mdi:close"></ha-icon>
            </button>
            <${HISTORY_CARD_TAG}></${HISTORY_CARD_TAG}>
          </div>
        </dialog>
      </ha-card>
    `;

    this._wireCategoryToggles();
    this._wireHistoryInteractions();
  }

  _wireHistoryInteractions() {
    const dialog = this.shadowRoot?.querySelector(".history-dialog");
    const close = this.shadowRoot?.querySelector(".history-close");

    close?.addEventListener("click", () => dialog?.close());
    dialog?.addEventListener("click", (event) => {
      if (event.target === dialog) dialog.close();
    });

    const open = (row) => {
      const category = row.dataset.category;
      const key = row.dataset.key;
      const state = this._hass?.states?.[this._config.entity];
      const attrs = state?.attributes || {};
      const measurement = (attrs.measurements || []).find(
        (item) => item.category === category && item.key === key
      );

      if (!measurement?.historical_statistic_id || !dialog) return;

      const historyCard = dialog.querySelector(HISTORY_CARD_TAG);
      historyCard?.configure({
        hass: this._hass,
        measurement,
        reports: attrs.stored_reports || [],
        language: languageFor(this._hass),
      });
      dialog.showModal();
    };

    this.shadowRoot
      ?.querySelectorAll(".measurement.history-enabled")
      .forEach((row) => {
        row.addEventListener("click", () => open(row));
        row.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            open(row);
          }
        });
      });
  }

  _messageCard(title, message) {
    return `
      <style>${this._styles()}</style>
      <ha-card>
        <div class="message">
          <ha-icon icon="mdi:test-tube"></ha-icon>
          <div>
            <div class="message-title">${escapeHtml(title)}</div>
            <div class="message-text">${escapeHtml(message)}</div>
          </div>
        </div>
      </ha-card>
    `;
  }

  _overallLabel(status, language) {
    const t = TEXT[language];
    if (status === "ok") return t.ok;
    if (status === "warning") return t.warning;
    if (status === "critical") return t.critical;
    return t.statusUnknown;
  }

  _statusCount(status, count, label) {
    return `
      <div class="status-count ${status}">
        <span class="status-dot"></span>
        <span class="status-label">${escapeHtml(label)}</span>
        <strong>${escapeHtml(count)}</strong>
      </div>
    `;
  }

  _measurementCountLabel(count, language) {
    const t = TEXT[language];
    return `${count} ${count === 1 ? t.measurement : t.measurements}`;
  }

  _categoryStatusCounts(measurements) {
    const counts = {
      ok: 0,
      warning: 0,
      critical: 0,
      unknown: 0,
    };

    for (const measurement of measurements) {
      const severity = measurement?.status?.severity || "unknown";
      if (severity in counts) {
        counts[severity] += 1;
      } else {
        counts.unknown += 1;
      }
    }

    return counts;
  }

  _categoryStatusSummary(counts, language) {
    const t = TEXT[language];
    const items = [
      ["ok", counts.ok, t.okShort],
      ["warning", counts.warning, t.warningShort],
      ["critical", counts.critical, t.criticalShort],
      ["unknown", counts.unknown, t.unknownShort],
    ].filter(([, count]) => count > 0);

    return `
      <span class="category-status" aria-label="${escapeHtml(
        items.map(([, count, label]) => `${label}: ${count}`).join(", ")
      )}">
        ${items
          .map(
            ([status, count, label]) => `
              <span
                class="category-status-item ${escapeHtml(status)}"
                title="${escapeHtml(`${label}: ${count}`)}"
              >
                <span class="status-dot"></span>
                <span class="category-status-count">${escapeHtml(count)}</span>
              </span>
            `
          )
          .join("")}
      </span>
    `;
  }

  _category(category, measurements, language, isOpen) {
    const t = TEXT[language];
    const label = t.categories[category] || t.categories.unknown;
    const icon = CATEGORY_ICONS[category] || "mdi:flask-outline";
    const statusCounts = this._categoryStatusCounts(measurements);
    const countLabel = this._measurementCountLabel(
      measurements.length,
      language
    );

    return `
      <details class="category" data-category="${escapeHtml(category)}" ${
        isOpen ? "open" : ""
      }>
        <summary>
          <span class="category-title">
            <span class="category-icon">
              <ha-icon icon="${escapeHtml(icon)}"></ha-icon>
            </span>
            <span>${escapeHtml(label)}</span>
          </span>
          ${this._categoryStatusSummary(statusCounts, language)}
          <span
            class="category-count"
            title="${escapeHtml(countLabel)}"
            aria-label="${escapeHtml(countLabel)}"
          >${measurements.length}</span>
          <ha-icon class="chevron" icon="mdi:chevron-down"></ha-icon>
        </summary>
        <div class="rows">
          ${measurements
            .map((measurement) =>
              this._measurementRow(measurement, language)
            )
            .join("")}
        </div>
      </details>
    `;
  }

  _measurementRow(measurement, language) {
    const t = TEXT[language];
    const status = measurement.status || {};
    const severity = status.severity || "unknown";
    const direction = status.direction;
    const current = measurementValue(measurement, language);
    const target = targetLabel(measurement, language);
    const previous = measurement.has_previous
      ? measurementValue(measurement, language, true)
      : "";
    const hasNumericDelta = typeof measurement.delta === "number";
    const delta = hasNumericDelta
      ? numericLabel(Math.abs(measurement.delta), language)
      : "";
    const deltaUnit = measurement.unit ? ` ${measurement.unit}` : "";
    const symbol = trendSymbol(measurement.trend);
    const progress = targetProgress(measurement);
    const progressTitle =
      progress === "improved"
        ? t.improved
        : progress === "worsened"
          ? t.worsened
          : progress === "same"
            ? t.unchanged
            : "";

    let comparison = "";
    if (this._config.show_previous !== false && measurement.has_previous) {
      comparison = `
        <span class="previous-value">
          ${escapeHtml(t.previous)}: ${escapeHtml(previous)}
        </span>
        ${
          hasNumericDelta
            ? `
              <span class="delta ${escapeHtml(progress)}" title="${escapeHtml(
                progressTitle
              )}">
                ${escapeHtml(symbol)} ${escapeHtml(delta)}${escapeHtml(
                  deltaUnit
                )}
              </span>
            `
            : ""
        }
      `;
    }

    const historyEnabled = Boolean(measurement.historical_statistic_id);

    return `
      <div
        class="measurement${historyEnabled ? " history-enabled" : ""}"
        data-category="${escapeHtml(measurement.category || "unknown")}"
        data-key="${escapeHtml(measurement.key || "unknown")}"
        ${historyEnabled ? 'role="button" tabindex="0"' : ""}
      >
        <div class="status-icon ${escapeHtml(severity)}">
          <span class="status-dot"></span>
          ${
            direction === "high"
              ? '<span class="direction">↑</span>'
              : direction === "low"
                ? '<span class="direction">↓</span>'
                : ""
          }
        </div>

        <div class="measurement-main">
          <div class="measurement-name">
            ${escapeHtml(measurement.name || measurement.key || "—")}
          </div>
          <div class="measurement-sub">
            ${
              target
                ? `<span class="target-value">${escapeHtml(
                    t.target
                  )}: ${escapeHtml(target)}</span>`
                : ""
            }
            ${comparison}
          </div>
        </div>

        <div class="measurement-value">
          <span>${escapeHtml(current)}</span>
          ${
            historyEnabled
              ? '<ha-icon class="history-indicator" icon="mdi:chart-line"></ha-icon>'
              : ""
          }
        </div>
      </div>
    `;
  }

  _styles() {
    return `
      :host {
        display: block;
      }

      ha-card {
        overflow: hidden;
        border-radius: var(--ha-card-border-radius, 18px);
        background:
          radial-gradient(
            circle at 0% 0%,
            color-mix(in srgb, var(--primary-color) 8%, transparent),
            transparent 34%
          ),
          var(--ha-card-background, var(--card-background-color));
      }

      .header {
        padding: 16px 16px 13px;
        border-bottom: 1px solid var(--divider-color);
      }

      .title-row {
        display: grid;
        grid-template-columns: auto minmax(0, 1fr) auto;
        align-items: center;
        gap: 11px;
      }

      .brand-icon {
        display: grid;
        place-items: center;
        width: 42px;
        height: 42px;
        border-radius: 14px;
        background: color-mix(
          in srgb,
          var(--primary-color) 16%,
          transparent
        );
        color: var(--primary-color);
      }

      .brand-icon ha-icon {
        --mdc-icon-size: 25px;
      }

      .title-wrap {
        min-width: 0;
      }

      .title {
        color: var(--primary-text-color);
        font-size: 1.18rem;
        font-weight: 700;
        line-height: 1.2;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .meta {
        margin-top: 4px;
        color: var(--secondary-text-color);
        font-size: 0.82rem;
      }

      .overall {
        max-width: 132px;
        padding: 6px 9px;
        border-radius: 999px;
        font-size: 0.68rem;
        font-weight: 700;
        line-height: 1.15;
        text-align: center;
        color: var(--primary-text-color);
        background: var(--secondary-background-color);
      }

      .overall.ok {
        color: var(--success-color, #43a047);
        background: color-mix(
          in srgb,
          var(--success-color, #43a047) 13%,
          transparent
        );
      }

      .overall.warning {
        color: var(--warning-color, #f9a825);
        background: color-mix(
          in srgb,
          var(--warning-color, #f9a825) 13%,
          transparent
        );
      }

      .overall.critical {
        color: var(--error-color, #db4437);
        background: color-mix(
          in srgb,
          var(--error-color, #db4437) 13%,
          transparent
        );
      }

      .status-strip {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 7px;
        margin-top: 12px;
      }

      .status-count {
        display: grid;
        grid-template-columns: auto minmax(0, 1fr) auto;
        align-items: center;
        gap: 5px;
        min-width: 0;
        padding: 6px 8px;
        border-radius: 11px;
        background: color-mix(
          in srgb,
          var(--secondary-background-color) 86%,
          transparent
        );
        color: var(--secondary-text-color);
        font-size: 0.71rem;
      }

      .status-count strong {
        color: var(--primary-text-color);
        font-size: 0.82rem;
      }

      .status-label {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .status-count .status-dot,
      .status-icon .status-dot {
        width: 9px;
        height: 9px;
        border-radius: 50%;
        background: var(--disabled-text-color);
      }

      .ok .status-dot {
        background: var(--success-color, #43a047);
      }

      .warning .status-dot {
        background: var(--warning-color, #f9a825);
      }

      .critical .status-dot {
        background: var(--error-color, #db4437);
      }

      .previous-analysis {
        display: flex;
        align-items: center;
        gap: 5px;
        margin-top: 10px;
        color: var(--secondary-text-color);
        font-size: 0.75rem;
      }

      .previous-analysis strong {
        color: var(--primary-text-color);
        font-weight: 600;
      }

      .previous-analysis ha-icon {
        margin-right: 2px;
        --mdc-icon-size: 16px;
      }

      .previous-date {
        opacity: 0.85;
      }

      .categories {
        padding: 8px;
      }

      details.category {
        border-radius: 13px;
        overflow: hidden;
      }

      details.category + details.category {
        margin-top: 4px;
      }

      summary {
        list-style: none;
        cursor: pointer;
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto auto auto;
        align-items: center;
        gap: 8px;
        padding: 10px 9px;
        border-radius: 11px;
        color: var(--primary-text-color);
        user-select: none;
      }

      summary::-webkit-details-marker {
        display: none;
      }

      summary:hover {
        background: var(--secondary-background-color);
      }

      .category-title {
        display: flex;
        align-items: center;
        min-width: 0;
        gap: 8px;
        font-size: 0.9rem;
        font-weight: 700;
      }

      .category-icon {
        display: grid;
        place-items: center;
        width: 28px;
        height: 28px;
        border-radius: 9px;
        color: var(--primary-color);
        background: color-mix(
          in srgb,
          var(--primary-color) 9%,
          transparent
        );
      }

      .category-icon ha-icon {
        --mdc-icon-size: 18px;
      }

      .category-status {
        display: inline-flex;
        align-items: center;
        justify-content: flex-end;
        gap: 7px;
        min-width: 0;
      }

      .category-status-item {
        display: inline-flex;
        align-items: center;
        gap: 3px;
        color: var(--secondary-text-color);
        font-size: 0.64rem;
        font-weight: 700;
        line-height: 1;
        white-space: nowrap;
      }

      .category-status-item .status-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: var(--disabled-text-color);
      }

      .category-status-item.ok .status-dot {
        background: var(--success-color, #43a047);
      }

      .category-status-item.warning .status-dot {
        background: var(--warning-color, #f9a825);
      }

      .category-status-item.critical .status-dot {
        background: var(--error-color, #db4437);
      }

      .category-status-item.unknown .status-dot {
        background: var(--disabled-text-color);
      }

      .category-status-count {
        min-width: 0.65rem;
        text-align: left;
      }

      .category-count {
        min-width: 25px;
        padding: 3px 7px;
        border-radius: 999px;
        text-align: center;
        color: var(--secondary-text-color);
        background: var(--secondary-background-color);
        font-size: 0.7rem;
      }

      .chevron {
        color: var(--secondary-text-color);
        transition: transform 160ms ease;
        --mdc-icon-size: 20px;
      }

      details[open] .chevron {
        transform: rotate(180deg);
      }

      .rows {
        padding: 0 4px 5px;
      }

      .measurement {
        display: grid;
        grid-template-columns: 30px minmax(0, 1fr) auto;
        align-items: center;
        gap: 9px;
        min-height: 56px;
        padding: 7px 8px;
        border-top: 1px solid var(--divider-color);
      }

      .measurement.history-enabled {
        cursor: pointer;
        border-radius: 10px;
        transition: background 120ms ease;
      }

      .measurement.history-enabled:hover {
        background: color-mix(
          in srgb,
          var(--secondary-background-color) 65%,
          transparent
        );
      }

      .measurement.history-enabled:focus-visible {
        outline: 2px solid var(--primary-color);
        outline-offset: -2px;
      }

      .status-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 2px;
        width: 28px;
        height: 28px;
        border-radius: 9px;
        color: var(--secondary-text-color);
        background: var(--secondary-background-color);
      }

      .status-icon .status-dot {
        width: 9px;
        height: 9px;
      }

      .direction {
        font-size: 0.78rem;
        font-weight: 800;
        line-height: 1;
      }

      .status-icon.ok {
        color: var(--success-color, #43a047);
      }

      .status-icon.warning {
        color: var(--warning-color, #f9a825);
      }

      .status-icon.critical {
        color: var(--error-color, #db4437);
      }

      .measurement-main {
        min-width: 0;
      }

      .measurement-name {
        color: var(--primary-text-color);
        font-size: 0.9rem;
        font-weight: 650;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .measurement-sub {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 4px 8px;
        margin-top: 4px;
        color: var(--secondary-text-color);
        font-size: 0.69rem;
      }

      .target-value,
      .previous-value {
        white-space: nowrap;
      }

      .delta {
        display: inline-flex;
        align-items: center;
        min-height: 18px;
        padding: 1px 5px;
        border-radius: 999px;
        font-weight: 700;
        white-space: nowrap;
        background: var(--secondary-background-color);
      }

      .delta.improved {
        color: var(--success-color, #43a047);
        background: color-mix(
          in srgb,
          var(--success-color, #43a047) 10%,
          transparent
        );
      }

      .delta.worsened {
        color: var(--error-color, #db4437);
        background: color-mix(
          in srgb,
          var(--error-color, #db4437) 10%,
          transparent
        );
      }

      .delta.same,
      .delta.neutral {
        color: var(--secondary-text-color);
      }

      .measurement-value {
        display: inline-flex;
        max-width: 150px;
        align-items: center;
        justify-content: flex-end;
        gap: 5px;
        color: var(--primary-text-color);
        font-size: 0.91rem;
        font-weight: 750;
        text-align: right;
        overflow-wrap: anywhere;
      }

      .history-indicator {
        flex: 0 0 auto;
        color: var(--secondary-text-color);
        opacity: 0.7;
        --mdc-icon-size: 15px;
      }

      .history-dialog {
        width: min(92vw, 720px);
        max-width: 720px;
        max-height: min(88vh, 760px);
        margin: auto;
        padding: 0;
        overflow: visible;
        border: 1px solid var(--divider-color);
        border-radius: 20px;
        background:
          radial-gradient(
            circle at 0% 0%,
            color-mix(in srgb, var(--primary-color) 8%, transparent),
            transparent 36%
          ),
          var(--ha-card-background, var(--card-background-color));
        color: var(--primary-text-color);
        box-shadow: 0 18px 60px rgba(0, 0, 0, 0.42);
      }

      .history-dialog::backdrop {
        background: rgba(0, 0, 0, 0.66);
        backdrop-filter: blur(4px);
      }

      .history-dialog-inner {
        position: relative;
        max-height: min(88vh, 760px);
        padding: 18px;
        overflow-y: auto;
        box-sizing: border-box;
      }

      .history-close {
        position: absolute;
        z-index: 2;
        top: 12px;
        right: 12px;
        display: grid;
        width: 38px;
        height: 38px;
        place-items: center;
        padding: 0;
        border: 0;
        border-radius: 12px;
        color: var(--secondary-text-color);
        background: var(--secondary-background-color);
        cursor: pointer;
      }

      .history-close:hover {
        color: var(--primary-text-color);
      }

      .history-close ha-icon {
        --mdc-icon-size: 21px;
      }

      .message {
        display: flex;
        align-items: center;
        gap: 14px;
        padding: 22px;
      }

      .message > ha-icon {
        color: var(--primary-color);
        --mdc-icon-size: 30px;
      }

      .message-title {
        color: var(--primary-text-color);
        font-weight: 650;
      }

      .message-text {
        margin-top: 4px;
        color: var(--secondary-text-color);
        font-size: 0.85rem;
      }

      @media (max-width: 520px) {
        .header {
          padding: 14px 13px 12px;
        }

        .title-row {
          gap: 9px;
        }

        .brand-icon {
          width: 39px;
          height: 39px;
          border-radius: 13px;
        }

        .title {
          font-size: 1.08rem;
        }

        .meta {
          font-size: 0.77rem;
        }

        .overall {
          max-width: 105px;
          padding: 5px 7px;
          font-size: 0.62rem;
        }

        .status-strip {
          gap: 5px;
          margin-top: 10px;
        }

        .status-count {
          grid-template-columns: auto minmax(0, 1fr) auto;
          gap: 4px;
          padding: 5px 6px;
          font-size: 0.64rem;
        }

        .status-count strong {
          font-size: 0.75rem;
        }

        .categories {
          padding: 6px;
        }

        summary {
          gap: 6px;
          padding: 9px 7px;
        }

        .category-status {
          gap: 5px;
        }

        .category-status-item {
          gap: 2px;
          font-size: 0.6rem;
        }

        .category-status-item .status-dot {
          width: 6px;
          height: 6px;
        }

        .measurement {
          grid-template-columns: 28px minmax(0, 1fr) minmax(74px, auto);
          gap: 7px;
          padding-inline: 6px;
        }

        .measurement-value {
          max-width: 126px;
          font-size: 0.85rem;
        }

        .history-dialog {
          width: min(94vw, 720px);
          border-radius: 17px;
        }

        .history-dialog-inner {
          padding: 15px;
        }

        .measurement-sub {
          gap: 3px 6px;
          font-size: 0.65rem;
        }
      }

      @media (max-width: 370px) {
        .status-label {
          display: none;
        }

        .status-count {
          grid-template-columns: auto auto;
          justify-content: center;
        }

        .overall {
          max-width: 92px;
        }
      }
    `;
  }
}

if (!customElements.get(CARD_TAG)) {
  customElements.define(CARD_TAG, OceamoIcpCard);
}

window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === CARD_TAG)) {
  window.customCards.push({
    type: CARD_TAG,
    name: "Reef ICP Card",
    description:
      "Displays multi-provider reef ICP analyses with targets, status, comparison and interactive measurement history.",
    preview: true,
    getEntitySuggestion: (hass, entityId) => {
      const state = hass?.states?.[entityId];
      const attrs = state?.attributes || {};
      if (
        !entityId?.startsWith("sensor.") ||
        !Array.isArray(attrs.measurements) ||
        !("analysis_number" in attrs) ||
        !("status_counts" in attrs)
      ) {
        return null;
      }

      return {
        config: {
          type: "custom:oceamo-icp-card",
          entity: entityId,
          show_previous: true,
        },
      };
    },
  });
}

console.info(
  `%c REEF ICP CARD %c v${CARD_VERSION} `,
  "background:#1686a8;color:white;font-weight:700;padding:2px 6px;border-radius:4px 0 0 4px;",
  "background:#1f2937;color:white;padding:2px 6px;border-radius:0 4px 4px 0;"
);
