# esysunhome

esysunhome is a Home Assistant custom integration for ESY energy devices. It lets you add your ESY device to Home Assistant, view device data, switch supported operating modes, and optionally view a daily power chart.

## Features

- Sign in with your ESY account username and password.
- Select a bound device during setup.
- View battery, solar, grid, load, voltage, current, frequency, status, and energy sensors.
- Switch supported operating modes from Home Assistant.
- Enable or disable polling from the device controls.
- View a daily power chart with date selection.

## Installation With HACS

1. Open Home Assistant.
2. Go to **HACS**.
3. Open the menu in the top-right corner and choose **Custom repositories**.
4. Add this repository URL:

   ```text
   https://github.com/esysunhome/esysunhome
   ```

5. Select **Integration** as the category.
6. Click **Add**.
7. Open **esysunhome** in HACS and click **Download**.
8. Restart Home Assistant.

## Manual Installation

1. Copy this folder into your Home Assistant configuration directory:

   ```text
   custom_components/esy_app
   ```

2. Restart Home Assistant.

The final path in Home Assistant should be:

```text
/config/custom_components/esy_app
```

## Add The Integration

1. In Home Assistant, go to **Settings > Devices & services**.
2. Click **Add integration**.
3. Search for **esysunhome**.
4. Enter the required setup information:
   - **Name**: a display name for this integration.
   - **Username**: your ESY account username.
   - **Password**: your ESY account password.
5. Submit the form.
6. Select the device you want to add.
7. Choose whether to show the ESY Power page if the option is displayed.
8. Submit to finish setup.

## Using The Integration

After setup, Home Assistant creates a device for the selected ESY unit. Open it from **Settings > Devices & services > esysunhome**.

You can use the device page to:

- Check current battery state of charge.
- View solar, grid, load, and battery power values.
- View voltage, current, frequency, and energy totals.
- Enable or disable data polling.
- Change the operating mode from the **Operating Mode** select entity.

Only operating modes supported by the connected ESY device are shown.

## Daily Power Chart

If the ESY Power page is enabled during setup, Home Assistant adds an **ESY Power** item to the sidebar. Open it to view daily power data.

The page lets you:

- Select a date.
- Refresh the chart.
- View PV power, load power, battery power, grid feed, grid purchase, and battery SOC.
- Hover over the chart to inspect values at a specific time.

## Optional Lovelace Card

The integration also includes a custom Lovelace card. This is optional because the ESY Power sidebar page can show the chart automatically.

To add the card manually:

1. Go to **Settings > Dashboards > Resources**.
2. Add this resource:

   ```text
   /esy_app_static/esy-power-chart-card.js
   ```

3. Set the resource type to **JavaScript module**.
4. Add a manual card to your dashboard:

   ```yaml
   type: custom:esy-power-chart-card
   title: ESY Daily Power
   sn: "your_device_sn"
   ```

Use the device SN shown in your esysunhome device list.

## Troubleshooting

- If the integration does not appear after installation, restart Home Assistant.
- If login fails, check your username and password.
- If no device is listed, make sure your ESY account is already bound to a device.
- If mode switching fails, refresh the device page and confirm the device is online.
- If the chart does not load, confirm the selected device supports daily power data.

## Updating

When updating through HACS:

1. Open **HACS**.
2. Open **esysunhome**.
3. Click **Update** or **Redownload**.
4. Restart Home Assistant.
