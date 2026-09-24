const CARD_VERSION = "0.3.3";
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
      </ha-card>
    `;

    this._wireCategoryToggles();
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
                ? `<span class="target-value">${escapeHtml(
                    t.target
                  )}: ${escapeHtml(target)}</span>`
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
        max-width: 135px;
        color: var(--primary-text-color);
        font-size: 0.91rem;
        font-weight: 750;
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
          max-width: 112px;
          font-size: 0.85rem;
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
