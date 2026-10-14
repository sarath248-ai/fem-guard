# API contract

Base URL http://127.0.0.1:8080. Server UTC ISO-8601 timestamps. Browser mutations require a logged-in session and X-CSRF-Token from the HTML meta tag. JSON bodies must be objects; maximum request is 64 KiB.

| Endpoint | Permission | Behavior |
|---|---|---|
| GET /health | Public | Liveness, not database/model readiness |
| GET /api/state | Operator/admin | Cameras, 200 incidents, unresolved totals, 100 audit rows |
| POST /api/cameras | Admin + CSRF | Create zone, 201 with id |
| PATCH /api/cameras/{id} | Admin + CSRF | Set enabled boolean |
| POST /api/simulate | Operator/admin + CSRF | Synthetic observation |
| POST /api/observations | Device bearer token | Device observation |
| PATCH /api/incidents/{id} | Operator/admin + CSRF | Acknowledge/resolve with note |
| GET /api/incidents/{id}/export | Operator/admin | Metadata/checksum download |

Observation:

```json
{"camera_id":1,"people":3,"gesture":0.92,"scream":0.89,"aggression":0.75,"manual_sos":false}
```

camera_id must be an enabled registered integer. people is integer 0–10000, default 0. Scores are finite numbers 0–1, default 0; strings/booleans are rejected. manual_sos is boolean, default false. Unknown fields are ignored. Above values produce high priority and index 87. Low returns incident_id null. Repeated automatic alerts may return an existing ID within 60 seconds; manual SOS creates a new incident. No external message/media capture occurs.

Python device example:

```python
import json, os, urllib.request
req = urllib.request.Request(
    "http://127.0.0.1:8080/api/observations",
    data=json.dumps({"camera_id":1,"people":3,"manual_sos":True}).encode(),
    headers={"Content-Type":"application/json",
             "Authorization":"Bearer " + os.environ["DEVICE_TOKEN"]})
with urllib.request.urlopen(req, timeout=5) as response:
    print(response.read().decode())
```

Camera create: `{"name":"South entrance","location":"Campus · Gate B"}`. Toggle: `{"enabled":false}`. Review: `{"status":"acknowledged","note":"Reviewed staged event."}` then `resolved` with another note. Notes must be 3–1000 characters.

Errors use {"error":"description"}: 400 invalid input, 401 no authentication, 403 authorization/CSRF, 404 unknown resource, 409 disabled zone/invalid transition, 413 request too large. Clients also need to handle transport and non-JSON proxy failures.

Export checksum verification:

```python
import hashlib, json
with open("incident-1.json", encoding="utf-8") as f: export=json.load(f)
raw=json.dumps(export["record"], sort_keys=True, separators=(",", ":")).encode()
assert hashlib.sha256(raw).hexdigest() == export["sha256"]
```

This checks internal consistency, not immutable provenance. The MVP uses received time, shared bearer token and no client event IDs; physical gateways need per-device credentials, retry idempotency, debounce and replay controls.
