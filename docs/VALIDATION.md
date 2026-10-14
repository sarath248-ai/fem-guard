# Validation · 14 October 2026

- Python 3.12: `python -m pytest -q` → 9 tests passed.
- `python -m ruff check .` → all configured checks passed (critical syntax/name checks, not a full style audit).
- Headless Chromium: login → synthetic high incident → acknowledge → resolve completed successfully.
- Browser desktop 1440px and mobile 390px: no JavaScript page errors or document-level horizontal overflow; screenshots inspected.
- OpenCV 4.12 HOG model initialized and processed a 640×480 blank frame with zero detections. This is a smoke check, not recognition accuracy evaluation or hardware webcam testing.
- Docker recipe/CI configuration supplied but not executed in this environment. Windows instructions are provided but execution was on Linux.
- No trained gesture/audio/aggression models were tested because none are present. No police or external notification service was contacted.

Screenshots contain a local review-only account and staged simulation, not real personal surveillance data. The temporary account/database are excluded from the distributable archive. A fresh install requires init-db, create-user and optional seed-demo.
