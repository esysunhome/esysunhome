class EsyPowerChartCard extends HTMLElement {
  static getConfigElement() {
    return document.createElement("esy-power-chart-card-editor");
  }

  static getStubConfig() {
    return {
      type: "custom:esy-power-chart-card",
      title: "ESY Daily Power",
      sn: "",
    };
  }

  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = null;
    this._rows = [];
    this._loading = false;
    this._error = "";
    this._date = this._today();
    this._hoverIndex = -1;
    this._resizeObserver = null;
  }

  setConfig(config) {
    if (!config.sn && !config.device_id) {
      throw new Error("sn is required");
    }
    this._config = config;
    this._date = config.date || this._date;
    this._render();
  }

  set hass(hass) {
    const firstSet = !this._hass;
    this._hass = hass;
    if (firstSet && (this._config.sn || this._config.device_id)) {
      this._loadData();
    }
  }

  connectedCallback() {
    this._render();
    this._resizeObserver = new ResizeObserver(() => this._drawChart());
    const wrap = this.shadowRoot.querySelector(".chart-wrap");
    if (wrap) this._resizeObserver.observe(wrap);
  }

  disconnectedCallback() {
    if (this._resizeObserver) this._resizeObserver.disconnect();
  }

  getCardSize() {
    return 5;
  }

  _today() {
    const date = new Date();
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  }

  async _loadData() {
    if (!this._hass || (!this._config.sn && !this._config.device_id)) return;
    this._loading = true;
    this._error = "";
    this._renderStatus();
    try {
      const result = await this._hass.callWS({
        type: "esy_app/power_data",
        entry_id: this._config.entry_id,
        sn: this._config.sn ? String(this._config.sn) : undefined,
        device_id: this._config.device_id ? String(this._config.device_id) : undefined,
        date: this._date,
      });
      this._rows = Array.isArray(result.rows) ? result.rows : [];
      this._hoverIndex = -1;
    } catch (err) {
      this._error = err?.message || String(err);
      this._rows = [];
    } finally {
      this._loading = false;
      this._renderStatus();
      this._drawChart();
    }
  }

  _render() {
    this.shadowRoot.innerHTML = `
      <style>
        :host { display: block; }
        ha-card { overflow: hidden; }
        .header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          padding: 16px 16px 8px;
        }
        .title {
          font-size: 18px;
          font-weight: 600;
          line-height: 1.2;
        }
        .controls {
          display: flex;
          align-items: center;
          gap: 8px;
          flex-wrap: wrap;
          justify-content: flex-end;
        }
        input[type="date"] {
          height: 36px;
          box-sizing: border-box;
          border: 1px solid var(--divider-color, #d4d7dc);
          border-radius: 6px;
          padding: 0 10px;
          background: var(--card-background-color, #fff);
          color: var(--primary-text-color, #111);
          font: inherit;
        }
        button {
          height: 36px;
          border: 0;
          border-radius: 6px;
          padding: 0 12px;
          cursor: pointer;
          color: var(--text-primary-color, #fff);
          background: var(--primary-color, #03a9f4);
          font: inherit;
        }
        button:disabled { opacity: 0.55; cursor: default; }
        .status {
          min-height: 20px;
          padding: 0 16px 8px;
          color: var(--secondary-text-color, #6b7280);
          font-size: 13px;
        }
        .status.error { color: var(--error-color, #db4437); }
        .legend {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
          gap: 8px 12px;
          padding: 0 16px 10px;
          font-size: 12px;
        }
        .legend-item {
          display: flex;
          align-items: center;
          gap: 7px;
          min-width: 0;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        .swatch {
          width: 18px;
          height: 3px;
          border-radius: 2px;
          flex: 0 0 auto;
        }
        .chart-wrap {
          position: relative;
          height: 340px;
          padding: 0 8px 12px;
        }
        canvas {
          width: 100%;
          height: 100%;
          display: block;
        }
        .tooltip {
          position: absolute;
          pointer-events: none;
          max-width: min(280px, calc(100% - 24px));
          padding: 9px 10px;
          border-radius: 6px;
          background: var(--card-background-color, #fff);
          color: var(--primary-text-color, #111);
          box-shadow: 0 6px 18px rgba(0, 0, 0, 0.22);
          border: 1px solid var(--divider-color, #d4d7dc);
          font-size: 12px;
          line-height: 1.45;
          z-index: 2;
          display: none;
        }
        .tooltip .time {
          font-weight: 600;
          margin-bottom: 4px;
        }
        .tip-row {
          display: flex;
          justify-content: space-between;
          gap: 12px;
        }
        @media (max-width: 560px) {
          .header { align-items: flex-start; flex-direction: column; }
          .controls { justify-content: flex-start; width: 100%; }
          input[type="date"] { flex: 1 1 160px; min-width: 0; }
          .chart-wrap { height: 300px; }
        }
      </style>
      <ha-card>
        <div class="header">
          <div class="title">${this._escape(this._config.title || "ESY Daily Power")}</div>
          <div class="controls">
            <input class="date" type="date" value="${this._date}">
            <button class="refresh">Refresh</button>
          </div>
        </div>
        <div class="status"></div>
        <div class="legend"></div>
        <div class="chart-wrap">
          <canvas></canvas>
          <div class="tooltip"></div>
        </div>
      </ha-card>
    `;

    this.shadowRoot.querySelector(".date").addEventListener("change", (event) => {
      this._date = event.target.value || this._today();
      this._loadData();
    });
    this.shadowRoot.querySelector(".refresh").addEventListener("click", () => this._loadData());
    const canvas = this.shadowRoot.querySelector("canvas");
    canvas.addEventListener("mousemove", (event) => this._handleHover(event));
    canvas.addEventListener("mouseleave", () => {
      this._hoverIndex = -1;
      this._hideTooltip();
      this._drawChart();
    });
    this._renderLegend();
    this._renderStatus();
    this._drawChart();
  }

  _series() {
    return [
      { key: "pvElec", label: "PV", color: "#f2a900", unit: "W", axis: "power" },
      { key: "loadElec", label: "Load", color: "#3366cc", unit: "W", axis: "power" },
      { key: "battery", label: "Battery", color: "#109618", unit: "W", axis: "power" },
      { key: "feedNetwork", label: "Feed Grid", color: "#dc3912", unit: "W", axis: "power" },
      { key: "buyElec", label: "Buy Grid", color: "#990099", unit: "W", axis: "power" },
      { key: "batteryTotalSoc", label: "SOC", color: "#0099c6", unit: "%", axis: "soc" },
    ];
  }

  _renderLegend() {
    const legend = this.shadowRoot.querySelector(".legend");
    if (!legend) return;
    legend.innerHTML = this._series().map((item) => `
      <div class="legend-item" title="${item.label}">
        <span class="swatch" style="background:${item.color}"></span>
        <span>${item.label}</span>
      </div>
    `).join("");
  }

  _renderStatus() {
    const status = this.shadowRoot.querySelector(".status");
    const button = this.shadowRoot.querySelector(".refresh");
    if (!status) return;
    if (button) button.disabled = this._loading;
    status.classList.toggle("error", Boolean(this._error));
    if (this._loading) {
      status.textContent = "Loading daily power data...";
    } else if (this._error) {
      status.textContent = this._error;
    } else if (!this._rows.length) {
      status.textContent = "No data for this date.";
    } else {
      status.textContent = `${this._rows.length} samples loaded for ${this._date}.`;
    }
  }

  _drawChart() {
    const canvas = this.shadowRoot.querySelector("canvas");
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const ratio = window.devicePixelRatio || 1;
    canvas.width = Math.max(1, Math.floor(rect.width * ratio));
    canvas.height = Math.max(1, Math.floor(rect.height * ratio));
    const ctx = canvas.getContext("2d");
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    ctx.clearRect(0, 0, rect.width, rect.height);

    const padding = { top: 14, right: 48, bottom: 34, left: 52 };
    const plot = {
      x: padding.left,
      y: padding.top,
      w: Math.max(1, rect.width - padding.left - padding.right),
      h: Math.max(1, rect.height - padding.top - padding.bottom),
    };

    this._drawGrid(ctx, plot);
    if (!this._rows.length) return;

    const powerMax = this._powerMax();
    const xFor = (index) => plot.x + (this._rows.length <= 1 ? 0 : index / (this._rows.length - 1)) * plot.w;
    const yPower = (value) => plot.y + plot.h - (Number(value || 0) / powerMax) * plot.h;
    const ySoc = (value) => plot.y + plot.h - (Math.max(0, Math.min(100, Number(value || 0))) / 100) * plot.h;

    for (const item of this._series()) {
      ctx.beginPath();
      ctx.lineWidth = item.axis === "soc" ? 1.6 : 2;
      ctx.strokeStyle = item.color;
      ctx.setLineDash(item.axis === "soc" ? [5, 4] : []);
      this._rows.forEach((row, index) => {
        const x = xFor(index);
        const y = item.axis === "soc" ? ySoc(row[item.key]) : yPower(row[item.key]);
        if (index === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.stroke();
      ctx.setLineDash([]);
    }

    this._drawAxes(ctx, plot, powerMax);
    if (this._hoverIndex >= 0) {
      const x = xFor(this._hoverIndex);
      ctx.strokeStyle = "rgba(80, 80, 80, 0.5)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(x, plot.y);
      ctx.lineTo(x, plot.y + plot.h);
      ctx.stroke();
    }
  }

  _drawGrid(ctx, plot) {
    ctx.strokeStyle = "rgba(120, 120, 120, 0.22)";
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i += 1) {
      const y = plot.y + (plot.h * i) / 4;
      ctx.beginPath();
      ctx.moveTo(plot.x, y);
      ctx.lineTo(plot.x + plot.w, y);
      ctx.stroke();
    }
  }

  _drawAxes(ctx, plot, powerMax) {
    const style = getComputedStyle(this);
    ctx.fillStyle = style.getPropertyValue("--secondary-text-color") || "#6b7280";
    ctx.font = "11px sans-serif";
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    for (let i = 0; i <= 4; i += 1) {
      const value = Math.round(powerMax - (powerMax * i) / 4);
      const y = plot.y + (plot.h * i) / 4;
      ctx.fillText(`${value}W`, plot.x - 8, y);
      ctx.textAlign = "left";
      ctx.fillText(`${100 - i * 25}%`, plot.x + plot.w + 8, y);
      ctx.textAlign = "right";
    }

    ctx.textBaseline = "top";
    const first = this._rows[0]?.time || "";
    const mid = this._rows[Math.floor(this._rows.length / 2)]?.time || "";
    const last = this._rows[this._rows.length - 1]?.time || "";
    ctx.textAlign = "left";
    ctx.fillText(first, plot.x, plot.y + plot.h + 10);
    ctx.textAlign = "center";
    ctx.fillText(mid, plot.x + plot.w / 2, plot.y + plot.h + 10);
    ctx.textAlign = "right";
    ctx.fillText(last, plot.x + plot.w, plot.y + plot.h + 10);
  }

  _powerMax() {
    let max = 1;
    for (const row of this._rows) {
      for (const item of this._series().filter((series) => series.axis === "power")) {
        max = Math.max(max, Math.abs(Number(row[item.key] || 0)));
      }
    }
    const magnitude = 10 ** Math.floor(Math.log10(max));
    return Math.ceil(max / magnitude) * magnitude;
  }

  _handleHover(event) {
    if (!this._rows.length) return;
    const canvas = this.shadowRoot.querySelector("canvas");
    const rect = canvas.getBoundingClientRect();
    const paddingLeft = 52;
    const paddingRight = 48;
    const plotWidth = Math.max(1, rect.width - paddingLeft - paddingRight);
    const x = Math.max(0, Math.min(plotWidth, event.clientX - rect.left - paddingLeft));
    this._hoverIndex = Math.round((x / plotWidth) * (this._rows.length - 1));
    this._showTooltip(event);
    this._drawChart();
  }

  _showTooltip(event) {
    const tooltip = this.shadowRoot.querySelector(".tooltip");
    const wrap = this.shadowRoot.querySelector(".chart-wrap");
    const row = this._rows[this._hoverIndex];
    if (!tooltip || !wrap || !row) return;
    tooltip.innerHTML = `
      <div class="time">${this._escape(row.time || "")}</div>
      ${this._series().map((item) => `
        <div class="tip-row">
          <span>${item.label}</span>
          <strong>${this._format(row[item.key])}${item.unit}</strong>
        </div>
      `).join("")}
    `;
    tooltip.style.display = "block";
    const wrapRect = wrap.getBoundingClientRect();
    const tipRect = tooltip.getBoundingClientRect();
    let left = event.clientX - wrapRect.left + 12;
    let top = event.clientY - wrapRect.top + 12;
    if (left + tipRect.width > wrapRect.width) left = event.clientX - wrapRect.left - tipRect.width - 12;
    if (top + tipRect.height > wrapRect.height) top = event.clientY - wrapRect.top - tipRect.height - 12;
    tooltip.style.left = `${Math.max(8, left)}px`;
    tooltip.style.top = `${Math.max(8, top)}px`;
  }

  _hideTooltip() {
    const tooltip = this.shadowRoot.querySelector(".tooltip");
    if (tooltip) tooltip.style.display = "none";
  }

  _format(value) {
    const number = Number(value || 0);
    return Number.isInteger(number) ? String(number) : number.toFixed(1);
  }

  _escape(value) {
    return String(value).replace(/[&<>"]/g, (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
    }[char]));
  }
}

customElements.define("esy-power-chart-card", EsyPowerChartCard);
window.customCards = window.customCards || [];
window.customCards.push({
  type: "esy-power-chart-card",
  name: "ESY Daily Power Chart",
  description: "Daily ESY power curve with date picker and hover details.",
});
