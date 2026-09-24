const CARD_VERSION = "0.3.0";
const CARD_TAG = "oceamo-icp-card";
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
    cardName: "Oceamo ICP",
    noEntity: "Bitte einen ICP-Status-Sensor auswählen.",
    entityMissing: "Die konfigurierte Entität ist nicht verfügbar.",
    invalidEntity: "Diese Entität enthält keine Oceamo-ICP-Messwerte.",
    analysis: "Analyse",
    previous: "Vorher",
    target: "Soll",
    change: "Änderung",
    noPrevious: "Keine vorherige Analyse",
    notDetectable: "Nicht nachweisbar",
    notDetermined: "Nicht bestimmt",
    unknown: "Unbekannt",
    ok: "Kein Handlungsbedarf",
    warning: "Beobachten",
    critical: "Handlungsbedarf",
    statusUnknown: "Status unbekannt",
    showPrevious: "Vorherige ICP anzeigen",
    entity: "ICP-Status-Entität",
    title: "Titel (optional)",
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
    cardName: "Oceamo ICP",
    noEntity: "Please select an ICP status sensor.",
    entityMissing: "The configured entity is not available.",
    invalidEntity: "This entity does not contain Oceamo ICP measurements.",
    analysis: "Analysis",
    previous: "Previous",
    target: "Target",
    change: "Change",
    noPrevious: "No previous analysis",
    notDetectable: "Not detectable",
    notDetermined: "Not determined",
    unknown: "Unknown",
    ok: "No action required",
    warning: "Observe",
    critical: "Action required",
    statusUnknown: "Status unknown",
    showPrevious: "Show previous ICP",
    entity: "ICP status entity",
    title: "Title (optional)",
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
  if (raw === "n.b.") return TEXT[language].notDetermined;

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

class OceamoIcpCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = undefined;
    this._lastState = undefined;
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

  _rememberOpenSections() {
    const open = new Set();
    this.shadowRoot
      ?.querySelectorAll("details.category[open]")
      .forEach((element) => open.add(element.dataset.category));
    return open;
  }

  _render() {
    if (!this.shadowRoot) return;

    const openSections = this._rememberOpenSections();
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
    const counts = attrs.status_counts || {};
    const overall = state.state || "unknown";
    const previousAnalysis = attrs.previous_analysis_number;
    const previousDate = dateLabel(attrs.previous_analysis_date, language);

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
              </div>
            </div>
            <div class="overall ${escapeHtml(overall)}">
              ${escapeHtml(this._overallLabel(overall, language))}
            </div>
          </div>

          <div class="status-strip">
            ${this._statusCount("ok", counts.ok || 0)}
            ${this._statusCount("warning", counts.warning || 0)}
            ${this._statusCount("critical", counts.critical || 0)}
            ${
              counts.unknown
                ? this._statusCount("unknown", counts.unknown || 0)
                : ""
            }
          </div>

          ${
            previousAnalysis && this._config.show_previous !== false
              ? `
                <div class="previous-analysis">
                  <ha-icon icon="mdi:history"></ha-icon>
                  <span>${escapeHtml(t.previous)}:
                    <strong>${escapeHtml(previousAnalysis)}</strong>
                    ${previousDate ? ` · ${escapeHtml(previousDate)}` : ""}
                  </span>
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
                openSections.size
                  ? openSections.has(category)
                  : category === "basic" || (index === 0 && !grouped.has("basic"))
              )
            )
            .join("")}
        </div>
      </ha-card>
    `;
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

  _statusCount(status, count) {
    return `
      <div class="status-count ${status}">
        <span class="status-dot"></span>
        <strong>${escapeHtml(count)}</strong>
      </div>
    `;
  }

  _category(category, measurements, language, isOpen) {
    const t = TEXT[language];
    const label = t.categories[category] || t.categories.unknown;
    const icon = CATEGORY_ICONS[category] || "mdi:flask-outline";

    return `
      <details class="category" data-category="${escapeHtml(category)}" ${
        isOpen ? "open" : ""
      }>
        <summary>
          <span class="category-title">
            <ha-icon icon="${escapeHtml(icon)}"></ha-icon>
            <span>${escapeHtml(label)}</span>
          </span>
          <span class="category-count">${measurements.length}</span>
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
    const delta =
      typeof measurement.delta === "number"
        ? numericLabel(Math.abs(measurement.delta), language)
        : "";
    const deltaUnit = measurement.unit ? ` ${measurement.unit}` : "";
    const symbol = trendSymbol(measurement.trend);

    let comparison = "";
    if (
      this._config.show_previous !== false &&
      measurement.has_previous
    ) {
      comparison = `
        <span class="previous-value">
          ${escapeHtml(t.previous)}: ${escapeHtml(previous)}
        </span>
        ${
          delta
            ? `
              <span class="delta ${escapeHtml(
                measurement.trend || "same"
              )}">
                ${escapeHtml(symbol)}
                ${escapeHtml(delta)}${escapeHtml(deltaUnit)}
              </span>
            `
            : ""
        }
      `;
    }

    return `
      <div class="measurement">
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
                ? `<span>${escapeHtml(t.target)}: ${escapeHtml(target)}</span>`
                : ""
            }
            ${comparison}
          </div>
        </div>

        <div class="measurement-value">
          ${escapeHtml(current)}
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
      }

      .header {
        padding: 18px 18px 14px;
        border-bottom: 1px solid var(--divider-color);
      }

      .title-row {
        display: grid;
        grid-template-columns: auto minmax(0, 1fr) auto;
        align-items: center;
        gap: 12px;
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
        font-size: 1.2rem;
        font-weight: 650;
        line-height: 1.25;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .meta {
        margin-top: 3px;
        color: var(--secondary-text-color);
        font-size: 0.85rem;
      }

      .overall {
        padding: 6px 9px;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 650;
        white-space: nowrap;
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
        display: flex;
        gap: 10px;
        margin-top: 14px;
      }

      .status-count {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 9px;
        border-radius: 10px;
        background: var(--secondary-background-color);
        color: var(--secondary-text-color);
        font-size: 0.82rem;
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
        gap: 7px;
        margin-top: 12px;
        color: var(--secondary-text-color);
        font-size: 0.78rem;
      }

      .previous-analysis ha-icon {
        --mdc-icon-size: 17px;
      }

      .categories {
        padding: 10px;
      }

      details.category {
        border-radius: 13px;
        overflow: hidden;
      }

      details.category + details.category {
        margin-top: 6px;
      }

      summary {
        list-style: none;
        cursor: pointer;
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto auto;
        align-items: center;
        gap: 9px;
        padding: 12px 10px;
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
        gap: 9px;
        font-size: 0.91rem;
        font-weight: 650;
      }

      .category-title ha-icon {
        color: var(--primary-color);
        --mdc-icon-size: 20px;
      }

      .category-count {
        min-width: 24px;
        padding: 2px 7px;
        border-radius: 999px;
        text-align: center;
        color: var(--secondary-text-color);
        background: var(--secondary-background-color);
        font-size: 0.72rem;
      }

      .chevron {
        color: var(--secondary-text-color);
        transition: transform 160ms ease;
      }

      details[open] .chevron {
        transform: rotate(180deg);
      }

      .rows {
        padding: 0 4px 6px;
      }

      .measurement {
        display: grid;
        grid-template-columns: 28px minmax(0, 1fr) auto;
        align-items: center;
        gap: 9px;
        min-height: 56px;
        padding: 7px 8px;
        border-top: 1px solid var(--divider-color);
      }

      .status-icon {
        position: relative;
        display: flex;
        align-items: center;
        gap: 2px;
        min-width: 25px;
      }

      .status-icon .status-dot {
        width: 10px;
        height: 10px;
      }

      .direction {
        font-size: 0.85rem;
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
        font-size: 0.91rem;
        font-weight: 520;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .measurement-sub {
        display: flex;
        flex-wrap: wrap;
        gap: 4px 10px;
        margin-top: 3px;
        color: var(--secondary-text-color);
        font-size: 0.72rem;
      }

      .delta.up,
      .delta.down {
        color: var(--secondary-text-color);
        font-weight: 600;
      }

      .measurement-value {
        max-width: 145px;
        color: var(--primary-text-color);
        font-size: 0.91rem;
        font-weight: 650;
        text-align: right;
        overflow-wrap: anywhere;
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
          padding: 16px 14px 13px;
        }

        .title-row {
          grid-template-columns: auto minmax(0, 1fr);
        }

        .overall {
          grid-column: 1 / -1;
          justify-self: start;
          margin-left: 54px;
        }

        .categories {
          padding: 7px;
        }

        .measurement {
          grid-template-columns: 24px minmax(0, 1fr) minmax(75px, auto);
          gap: 7px;
          padding-inline: 6px;
        }

        .measurement-value {
          max-width: 118px;
          font-size: 0.86rem;
        }

        .measurement-sub {
          font-size: 0.68rem;
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
    name: "Oceamo ICP Card",
    description:
      "Displays the latest Oceamo ICP analysis with targets, status and previous-analysis comparison.",
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
  `%c OCEAMO ICP CARD %c v${CARD_VERSION} `,
  "background:#1686a8;color:white;font-weight:700;padding:2px 6px;border-radius:4px 0 0 4px;",
  "background:#1f2937;color:white;padding:2px 6px;border-radius:0 4px 4px 0;"
);
