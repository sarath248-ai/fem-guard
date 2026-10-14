# Her TechArmor / FEM Guard
## Complete idea and technical documentation

Version 0.1 · October 2026 · Consolidated from five supplied project documents

## 1. Abstract

Her TechArmor is a proposed multimodal monitoring system that helps a control room review candidate distress in public or campus environments. FEM Guard is the operator application. The complete idea combines camera observations, temporal help gestures, acoustic distress, manual SOS and contextual information. It creates reviewable incidents and supports an authorized response. It does not determine that a crime occurred or guarantee personal safety.

This release implements the software foundation: accounts, responsive UI, camera registry, observation API, explainable priority, incident lifecycle, audit and metadata exports. A simulation lab exercises distress scenarios with synthetic scores. An optional local OpenCV worker provides actual person counts. Trained recognition, police dispatch, live web video and media evidence storage require further work.

## 2. Problem and objectives

Many CCTV systems depend on people continuously watching multiple screens or examining recordings after an event. Limited attention, ambiguous behavior, low visibility and background noise complicate review. An assistant should surface candidate events with context and uncertainty, while a manual SOS remains available when automatic inference misses an event.

The supplied SIH files identify problem SIH1605, Women Safety Analytics – Protecting Women from Safety Threats. This report follows their contents without claiming official certification or competition compliance.

Objectives are to build a usable review console, combine independent distress candidates, preserve a direct SOS path, reduce repeated alerts, record operator decisions, and establish interfaces for future models. Research should test whether fusion improves precision over single modalities and whether operators can triage accurately with this UI. No detection performance claim has been established.

## 3. Stakeholders and boundaries

Administrators maintain monitoring zones and accounts. Operators review incidents and coordinate responses. Device maintainers configure capture workers. People in monitored areas are affected stakeholders who need appropriate notice and an accessible reporting route. Responders should receive operator-approved context through future authorized integrations.

The delivered policy accepts distress/SOS inputs for any person. It does not infer gender, facial emotion or identity. Operators can review and export all local incidents; administrators additionally manage cameras. The MVP is single-organization and has no per-zone tenancy controls.

## 4. Existing versus proposed system

| Aspect | Conventional camera review | Full proposed idea | Delivered release |
|---|---|---|---|
| Inputs | Video | Camera, audio, physical SOS | Synthetic scores + optional counts |
| Attention | Manual viewing | Candidate prioritization | Deterministic review policy |
| Decision | Operator | Explainable cues + operator | Reasons, review notes, lifecycle |
| Evidence | Recorder-dependent | Authorized event clips | Metadata JSON only |
| Response | Manual coordination | Approved responder integration | Internal queue only |
| Evaluation | Site-specific | Detection and workflow metrics | Software tests/UI QA |

Benefits such as faster intervention and reduced crime remain hypotheses for controlled evaluation. The console alone cannot establish them.

## 5. Functional requirements

FR-01: Authenticate admin/operator accounts with password hashes.
FR-02: Display zones, latest counts and observation freshness.
FR-03: Restrict registry changes to administrators.
FR-04: Accept bounded candidate scores and manual SOS from the lab/device endpoint.
FR-05: Explain low/moderate/high priority.
FR-06: Create incidents only for moderate/high results; low updates health.
FR-07: Coalesce repeated automatic alerts for 60 seconds; never coalesce manual SOS.
FR-08: Require acknowledgement before resolution and a note at each step.
FR-09: Log account, camera, incident and export actions.
FR-10: Export reproducible metadata checksums behind authentication.
FR-11: Label simulated inputs and missing media/dispatch features clearly.
FR-12: Support an optional local person-count adapter.

## 6. Nonfunctional requirements

The UI should work on desktop/mobile, keep protected data behind login, reject malformed scores, and persist state across restarts. Browser mutations need CSRF tokens. Device ingestion requires a separate bearer credential. Requests are limited to 64 KiB. The UI does not accept arbitrary remote capture URLs or camera credentials.

Define latency, availability, load, recovery and retention targets with the deployment partner. None is claimed achieved by this local MVP. SQLite and synchronous requests suit small demonstrations, while a large camera fleet needs queued inference and a database designed for concurrent writes.

## 7. Architecture

Browser templates and JavaScript use a same-origin Flask server. The browser polls state every five seconds and submits protected mutations. Flask validates observations, runs the policy, manages lifecycle transitions and writes SQLite. The optional worker runs in another process and posts authenticated counts. CSS and JS need no CDN or paid API.

Logical flow is input adapter → schema validation → enabled-camera check → policy → heartbeat → incident create/coalesce → operator review → export. Do not run camera decoding and deep learning inside web request handlers. Future inference services should feed a queue, with synchronized event windows, clip storage, notification outbox and monitoring.

## 8. Identity and access module

CLI-created accounts use Werkzeug salted password hashes. Sessions last eight hours. Cookies are HTTP-only and SameSite Strict. Secure cookie transport is configurable for HTTPS. CSRF checks cover browser mutations, including login/logout. Role checks read the persisted account. Five failed attempts block an account for five minutes.

This basic account limiter can itself cause temporary account denial. Gateway/IP controls, recovery, MFA and centralized identity are later deployment work. There is no public registration or password-reset UI. No default credentials are included.

## 9. Camera and observation modules

Each zone stores ID, name, location text, enabled flag, last_seen and people. Enabled zones are online if an observation arrived within 30 seconds. This is heartbeat freshness, not proof of a functioning CCTV stream. Disabled zones reject observations. The web UI explicitly labels missing video feeds.

The lab sends source `simulation`; the bearer-authenticated endpoint sends source `device`. These endpoints receive metadata scores, not raw audio/video. The optional HOG worker sends camera ID and people count every three seconds. Future envelopes need capture timestamps, model version, quality flags, device identity, replay checks and event IDs.

## 10. Fusion policy

Manual SOS creates high priority with index 100 independently of all other signals. Gesture ≥0.80 plus scream ≥0.80 creates high priority. Otherwise any gesture, scream or aggression value ≥0.70 creates moderate priority. Remaining observations are low priority and do not create incidents.

Policy index = round(100 × (0.40 × gesture + 0.35 × scream + 0.25 × aggression)). Priority depends on corroboration, not only that index. A high event may therefore have an index below 80. These are demonstration thresholds, not learned/calibrated risk probabilities. Aggression has a score interface but no trained detector.

People counts never determine priority. Solitude or inferred gender composition does not establish danger. Physical proximity in meters requires scene calibration. Sound cannot automatically be linked to a specific visible person without localization/context. The system must retain these uncertainties.

## 11. Incident lifecycle

An incident includes camera, priority, index, source, original candidate values, reasons, creation/update timestamps, status and latest note. It begins open; an operator acknowledges then resolves it with mandatory 3–1000 character notes. Direct open-to-resolved changes and reopening are blocked.

The incident row holds the latest note. Earlier decisions remain in audit rows. Same-camera/source/priority open automatic alerts within 60 seconds return an existing ID and update heartbeat. They do not overwrite the initial incident signals or create a complete observation history. Manual SOS always creates a distinct incident. Retry idempotency for physical gateways is future work.

## 12. Evidence and audit

Exports contain metadata plus SHA-256 over canonical JSON. The export clearly states that no CCTV/audio is included. A checksum verifies consistency against a trusted unchanged reference. It does not make a mutable database immutable or establish legal evidentiary authenticity. Administrators with database access can change records and recompute hashes.

Actual evidence needs event clip buffers, source identity, clock synchronization, protected storage, access logs and reviewed retention/legal-hold rules. The source idea's permanent recording claim is not implemented. This release has no automatic deletion job. Retention and minimization must be explicitly designed before a real pilot.

## 13. Optional actual vision baseline

The optional script uses OpenCV's pretrained HOG/SVM people detector, a webcam/local video, local bounding-box preview and authenticated count updates. It does not infer identity, gender, emotion, gestures or screams and cannot create danger alerts from counts alone. HOG is a limited CPU baseline affected by occlusion, distance, lighting, angle and crowding. Measure it on labelled consented footage before making accuracy claims.

## 14. Database

| Table | Fields | Purpose |
|---|---|---|
| users | id, username, password hash, role | Account principal |
| cameras | id, name, location, enabled, last_seen, people | Zone registry/current state |
| incidents | id, camera_id, level, score, source, status, signals, reasons, timestamps, note | Review record |
| audit | id, actor, action, detail, created_at | Application action history |
| login_limits | username, failures, blocked_until | Basic account throttle |

Camera-to-incident foreign keys are enabled. SQL values are parameterized. Signal/reason arrays use JSON text. Schema setup is idempotent but no migration system exists. Introduce migrations before changing a live schema. Raw video/audio, face embeddings, identity and gender labels are not stored.

## 15. UI design

The light UI uses neutral backgrounds, purple actions and text-labelled status badges. Desktop navigation exposes Overview, Incident queue, Camera registry, Signal lab and Activity log. Mobile navigation becomes a horizontal bar. Cards stack, forms resize and tables allow horizontal scrolling. Labels, keyboard focus and live status messages aid usability, but full accessibility compliance is not audited.

Overview shows online zones, unresolved high/moderate totals, resolved count in the latest 200 incidents, zones and recent incidents. The queue filters status/high priority. The dialog exposes reasons, signal values, source, review fields and export. Registry cards cannot be mistaken for live feeds. Admin-only creation controls are hidden for operators, with server-side enforcement too.

Unresolved totals cover the database, incident lists/resolved-card counts cover the latest 200 events, and activity log shows 100 latest entries. Pagination, full-history search and aggregate analytics are future work.

## 16. Model and data plan

Collect only consented or appropriately licensed data with a clearly defined annotation protocol. Label temporal help gesture sequences, acoustic scream candidates, ambiguous cases and quality indicators. Include negative examples: cheering, applause, laughter, waves, stretching, routine crowd movement, traffic and low-light artifacts.

Keep participants, sessions and sites separated across train/validation/test. Tune thresholds using validation only; freeze them before test evaluation. Evaluate modalities independently before fusion. Gesture models need sequences, audio needs fixed windows/sample-rate handling, and physical proximity needs camera calibration. Dataset consent/provenance, annotation disagreement, licensing and sensor coverage belong in a reproducible model card. No model weights or training data were supplied. MODEL_PLAN.md expands the next steps.

## 17. Evaluation and acceptance

Software acceptance checks fresh setup, role restrictions, invalid inputs, manual SOS, duplicate handling, lifecycle transitions, hashes, device authentication, heartbeat and disabled cameras. UI QA should cover desktop/mobile, filters, modal review, form errors and keyboard access.

Model metrics should include precision, recall, F1, PR-AUC and calibration per modality. System metrics should include false alerts per camera-hour, missed episodes, time-to-alert and results by low light, occlusion, camera angle and audio noise. Compare fusion against single-signal baselines on held-out sessions. No accuracy number is invented here.

Workflow evaluation should measure operator triage time, reviewer agreement and wrong closures on consented staged scenarios. A controlled drill should precede a supervised pilot. Maintain independent reporting channels and explicit responsibility for review; unvalidated detection must not become the only emergency channel.

## 18. Deployment and operational security

Stage 1 is a laptop demo with simulated scores. Stage 2 adds the optional person-count baseline. Stage 3 adds validated gesture/audio models, per-device authorization and quality/timestamp contracts. Stage 4 adds bounded event clips and operator-approved notification delivery. Stage 5 is a limited authorized pilot with monitoring, backups, retention and recovery tests.

Docker runs as a non-root user and Compose binds localhost. Waitress is available for local WSGI serving. Public TLS/reverse proxy deployment is not preconfigured. Database contents are not encrypted by the app. Use appropriate encrypted storage/access controls in deployments. The shared device token needs replacement with revocable credentials, replay protection, input limits and key rotation. Audit/evidence storage requires independent protection.

## 19. Academic schedule and resources

Weeks 1–2: requirements, source review, policy/UI acceptance. Weeks 3–4: consented collection, annotation and count baseline. Weeks 5–7: gesture/audio models and validation. Weeks 8–9: fusion tuning and negative-case testing. Weeks 10–11: clip/notification sandbox and recovery tests. Week 12: controlled pilot/report/presentation.

For a two/three-person team, divide model/data work, backend/integration and UI/evaluation while reviewing interfaces together. A laptop with webcam/microphone is sufficient initially. No paid API is required for this delivery. Future budgets depend on camera coverage, compute, network, storage retention, installation, maintenance and operator time. Do not buy Coral/Orange Pi/GPU devices until model compatibility and latency are benchmarked. No current hardware price is claimed.

## 20. Limitations and next work

This is a working application-layer prototype, not a trained end-to-end threat detector. The lab is synthetic, and only optional people counting performs real inference. There are no police calls, remote alerts, web video, media evidence, immutable retention, hotspot models or facial emotion/gender classifiers.

Next priorities are calibrated temporal models, synchronized provenance/quality, controlled notification delivery, clip retention, per-device identities, migrations, paginated history and observability. Dangerous-object recognition and historical hotspot analytics need independent evaluation and attention to reporting bias. They must not infer criminal intent about individuals.

## 21. Deliverables and references

The package includes source, responsive UI, local setup, Docker/CI, tests, source comparison, API/model plans, security/contribution guides and screenshots. It has not been pushed to GitHub. Original attachments remain separate.

Primary technical references: Flask security https://flask.palletsprojects.com/en/stable/web-security/ and OpenCV HOG https://docs.opencv.org/4.x/d5/d33/structcv_1_1HOGDescriptor.html . Original slide research links require bibliographic verification before formal citation.
