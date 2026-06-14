# Notification Overlay Tester

Small standalone project to test top-center non-clickable Windows overlay notifications.

## Run

From repository root:

```powershell
python projects\notification_overlay_tester\main.py
```

Or use:

```powershell
projects\notification_overlay_tester\run.ps1
```

## Behavior

- Shows a minimal top-center overlay.
- Overlay is configured as click-through (non-clickable).
- Rotates demo status messages every ~1.3 seconds.
- Logs are written to repository root `logs/notification_overlay_tester.log`.
