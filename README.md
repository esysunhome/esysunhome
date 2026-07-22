# ESY App

Home Assistant custom integration for ESY devices through an ESY Java backend API.

## Features

- Login with ESY account username and password.
- Select a bound device SN after login.
- View device status, battery SOC, power, voltage, current, and energy sensors.
- Switch operating mode using `/api/lsypattern/page` and `/api/lsypattern/switch`.
- Enable or disable API polling from the Home Assistant device controls.
- Optional Lovelace daily power chart card for `/api/lsydevicepowerdata/list`.

## Installation

Copy this folder into your Home Assistant config directory:

```text
custom_components/esy_app
```

Then restart Home Assistant and add **ESY App** from:

```text
Settings > Devices & services > Add integration
```

## Configuration

During setup, enter:

- API base URL, for example `http://120.79.138.205:7073`
- ESY account username
- ESY account password

After login, the integration loads devices from:

```text
GET /api/lsydevice/page
```

Choose the device SN you want to add.

## Daily Power Chart Card

The integration includes a Lovelace custom card:

```text
/esy_app_static/esy-power-chart-card.js
```

Add it as a JavaScript module resource in Home Assistant, then use:

```yaml
type: custom:esy-power-chart-card
title: ESY Daily Power
device_id: "2018602632859529217"
```

The card lets you select a date and charts:

- PV power
- Load power
- Battery power
- Feed to grid
- Buy from grid
- Battery SOC

## Backend Endpoints

This integration currently uses:

```text
POST /login?grant_type=app
POST /admin/login
GET  /api/lsydevice/page
GET  /api/smart/home/device
GET  /api/lsydevice/info
GET  /api/lsypattern/page
POST /api/lsypattern/switch
GET  /api/lsydevicepowerdata/list
```

## Development Notes

Local test scripts and reference code are intentionally not part of the published integration.

