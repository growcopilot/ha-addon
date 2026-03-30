# Changelog

## 1.2.1

- Token persistence across add-on updates — token saved to separate file that HA won't overwrite
- Entity selection grouped by type (Cameras, Sensors, Switches & Plugs, Lights, Fans) with card layout
- Search filter for entities
- Collapsible entity groups with "Show all" for large lists

## 1.2.0

- Sensor data push — reads mapped sensor entities every 5 min and pushes temperature, humidity, illuminance, moisture values to GrowCopilot
- Immediate sync on startup — heartbeat, discovery, and entity push run immediately when token is present (no more waiting for loop intervals after restart)
- Discover controllable entities — switch, light, and fan entities are now discoverable and selectable
- HA service call support — foundation for remote device control (turn on/off switches, lights, fans)
- Config sync extended to manage both camera and sensor targets

## 1.1.0

- Live status page showing active cameras, capture intervals, last/next capture times, and selected sensors
- Add-on icon and logo for HA add-on store display
- Link to GrowCopilot app from status page
- Cleaned up debug logging for production readiness
- Fixed SUPERVISOR_TOKEN resolution from s6 container environment

## 1.0.0

- Initial release
- Camera entity discovery via HA Supervisor API
- Sensor entity discovery (mapped for future use)
- Ingress web UI for setup and entity selection
- Scheduled camera snapshot capture and upload
- Device heartbeat and config sync
- Push-based architecture — no public HA URL required
