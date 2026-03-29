# GrowCopilot Home Assistant Add-on

AI-powered plant health monitoring for indoor growers.

## Installation

1. Open Home Assistant
2. Go to **Settings → Add-ons → Add-on Store**
3. Click the three dots menu → **Repositories**
4. Paste this URL: `https://github.com/growcopilot/ha-addon`
5. Click **Add**
6. Find "GrowCopilot" in the store and click **Install**

## Setup

1. Open the add-on and go to the **GrowCopilot** panel in the sidebar
2. Paste your API token from [app.growcopilot.ai/settings/api-tokens](https://app.growcopilot.ai/settings/api-tokens)
3. Select which cameras and sensors to forward
4. Map entities to grow spaces in the GrowCopilot app

## Features

- Automatic camera snapshot capture at configurable intervals
- Sensor entity discovery (temperature, humidity, light)
- Push-based — no public HA URL required
- Dark-themed ingress UI matching the GrowCopilot design
