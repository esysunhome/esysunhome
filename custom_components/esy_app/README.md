# ESY App Home Assistant custom integration

Phase 1 features:

- View device statuses
- Switch run mode from a Home Assistant select entity
- View battery SOC
- View basic energy flow values

## Java backend endpoints used

- `POST /login?grant_type=app` or `POST /admin/login`
- `GET /api/smart/home/device?sn=<device_sn>`
- `GET /api/lsydevice/info?id=<device_id>`
- `GET /api/lsypattern/page`
- `POST /api/lsypattern/switch`

## Install

Copy `custom_components/esy_app` into your Home Assistant config directory:

`/config/custom_components/esy_app`

Restart Home Assistant, then add **ESY App** from **Settings > Devices & services > Add integration**.

## Required values

- API base URL, for example `https://api.example.com`
- Username and password. The integration logs in, stores the returned bearer token, and sends it with API requests.
- Choose a bound device SN after login. The integration fetches the list from `/api/lsydevice/page`.

The selected device should include both SN and device id from `/api/lsydevice/page`; device id is required for details, available modes, mode switching, and daily power charts.
## Daily power chart card

This integration includes a Lovelace custom card for `/api/lsydevicepowerdata/list`.

Add this resource in Home Assistant:

`/esy_app_static/esy-power-chart-card.js`

Resource type: JavaScript module.

Example card YAML:

```yaml
type: custom:esy-power-chart-card
title: ESY Daily Power
device_id: "2018602632859529217"
# entry_id is optional if you only have one ESY App config entry.
# entry_id: "your_config_entry_id"
```

The card lets you select a date, fetches that day of power data, and plots PV, load, battery, feed-to-grid, buy-from-grid, and SOC. Hover the chart to see values for a specific time.





