# Changelog

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
