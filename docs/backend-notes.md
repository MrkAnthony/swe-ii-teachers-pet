# Crowd reports API

| Method | URL | Login | Notes |
|---|---|---|---|
| GET | `/api/health/` | no | checks postgres + redis |
| POST | `/api/crowd-reports/` | yes | `{"location": "<id>", "level": "empty" / "moderate" / "packed"}` |
| GET | `/api/crowd-reports/status/<location_id>/` | no | current crowd level for a location |

- Reports count for 45 minutes.
- One report per student per location every 10 minutes (429 if they try again).
- Status is cached in redis for 60 seconds and cleared when someone reports.
- Status returns `"level": null` and `"No recent reports"` when there's nothing recent.
