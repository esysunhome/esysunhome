import "./esy-power-chart-card.js";

class EsyPowerPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
    this._panel = null;
    this._entries = [];
    this._selected = "";
    this._loading = false;
    this._error = "";
  }

  set hass(hass) {
    const firstSet = !this._hass;
    this._hass = hass;
    if (firstSet) {
      this._loadDevices();
    } else {
      this._syncCardHass();
    }
  }

  set panel(panel) {
    this._panel = panel;
    this._render();
  }

  connectedCallback() {
    this._render();
    if (this._hass && !this._entries.length && !this._loading) {
      this._loadDevices();
    }
  }

  async _loadDevices() {
    if (!this._hass) return;
    this._loading = true;
    this._error = "";
    this._render();
    try {
      const result = await this._hass.callWS({ type: "esy_app/devices" });
      this._entries = Array.isArray(result.entries) ? result.entries : [];
      const devices = this._devices();
      if (!this._selected && devices.length) {
        this._selected = devices[0].key;
      }
    } catch (err) {
      this._error = err?.message || String(err);
      this._entries = [];
    } finally {
      this._loading = false;
      this._render();
    }
  }

  _devices() {
    const devices = [];
    for (const entry of this._entries) {
      for (const device of entry.devices || []) {
        if (!device.device_id) continue;
        devices.push({
          key: `${entry.entry_id}:${device.device_id}`,
          entry_id: entry.entry_id,
          device_id: String(device.device_id),
          sn: device.sn || "",
          name: device.name || device.sn || String(device.device_id),
          entry_title: entry.title || "ESY App",
        });
      }
    }
    return devices;
  }

  _selectedDevice() {
    const devices = this._devices();
    return devices.find((device) => device.key === this._selected) || devices[0] || null;
  }

  _render() {
    if (!this.shadowRoot) return;
    const devices = this._devices();
    const selected = this._selectedDevice();
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          min-height: 100%;
          background: var(--primary-background-color, #f7f8fa);
          color: var(--primary-text-color, #111);
        }
        .page {
          max-width: 1180px;
          margin: 0 auto;
          padding: 24px 20px 40px;
        }
        .header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 16px;
          margin-bottom: 18px;
        }
        h1 {
          margin: 0;
          font-size: 26px;
          line-height: 1.2;
          font-weight: 650;
        }
        .subtitle {
          margin-top: 6px;
          color: var(--secondary-text-color, #6b7280);
          font-size: 14px;
        }
        .tools {
          display: flex;
          gap: 8px;
          align-items: center;
          flex-wrap: wrap;
          justify-content: flex-end;
        }
        select, button {
          height: 38px;
          border-radius: 6px;
          border: 1px solid var(--divider-color, #d4d7dc);
          background: var(--card-background-color, #fff);
          color: var(--primary-text-color, #111);
          font: inherit;
        }
        select {
          min-width: 240px;
          padding: 0 10px;
        }
        button {
          padding: 0 12px;
          cursor: pointer;
        }
        .grid {
          display: grid;
          grid-template-columns: minmax(0, 1fr);
          gap: 16px;
        }
        .message {
          padding: 18px;
          border-radius: 8px;
          background: var(--card-background-color, #fff);
          border: 1px solid var(--divider-color, #d4d7dc);
          color: var(--secondary-text-color, #6b7280);
        }
        .message.error { color: var(--error-color, #db4437); }
        esy-power-chart-card { display: block; }
        @media (max-width: 720px) {
          .page { padding: 16px 12px 28px; }
          .header { flex-direction: column; align-items: stretch; }
          .tools { justify-content: flex-start; }
          select { width: 100%; min-width: 0; }
        }
      </style>
      <div class="page">
        <div class="header">
          <div>
            <h1>${this._escape(this._panel?.config?.title || "ESY Power")}</h1>
            <div class="subtitle">Daily power curve and ESY device data.</div>
          </div>
          <div class="tools">
            ${devices.length > 1 ? `
              <select class="device">
                ${devices.map((device) => `
                  <option value="${this._escape(device.key)}" ${device.key === selected?.key ? "selected" : ""}>
                    ${this._escape(device.name)}${device.sn && device.name !== device.sn ? ` (${this._escape(device.sn)})` : ""}
                  </option>
                `).join("")}
              </select>
            ` : ""}
            <button class="refresh" ?disabled=${this._loading}>Refresh Devices</button>
          </div>
        </div>
        <div class="grid">
          ${this._bodyTemplate(selected)}
        </div>
      </div>
    `;

    const refresh = this.shadowRoot.querySelector(".refresh");
    if (refresh) refresh.addEventListener("click", () => this._loadDevices());

    const select = this.shadowRoot.querySelector(".device");
    if (select) {
      select.addEventListener("change", (event) => {
        this._selected = event.target.value;
        this._render();
      });
    }

    this._syncCardHass();
  }

  _bodyTemplate(selected) {
    if (this._loading) return `<div class="message">Loading ESY devices...</div>`;
    if (this._error) return `<div class="message error">${this._escape(this._error)}</div>`;
    if (!selected) return `<div class="message">No ESY device with a device id is configured.</div>`;
    return `<esy-power-chart-card></esy-power-chart-card>`;
  }

  _syncCardHass() {
    const card = this.shadowRoot?.querySelector("esy-power-chart-card");
    const selected = this._selectedDevice();
    if (!card || !selected) return;
    card.setConfig({
      title: `${selected.name} Daily Power`,
      entry_id: selected.entry_id,
      device_id: selected.device_id,
    });
    if (this._hass) card.hass = this._hass;
  }

  _escape(value) {
    return String(value ?? "").replace(/[&<>"]/g, (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
    }[char]));
  }
}

customElements.define("esy-power-panel", EsyPowerPanel);
