# Model development plan

Recognition is future work except the optional HOG person-count baseline. No dataset or weights were supplied. Do not confuse the synthetic signal lab with AI inference.

## Temporal help gestures

Define an explicit gesture sequence. Capture consented participants across angles/lighting, annotate start/end and quality, and include waves, stretching and partly hidden hands as negatives. Compare hand/pose landmarks plus temporal LSTM/TCN classification. An isolated raised hand is insufficient. Split participants, sessions and sites rather than adjacent frames.

Proposed annotation: clip_id, participant_group, session_id, site_id, start_s, end_s, label, visibility, restricted consent reference. Do not commit consent identities or personal recordings.

## Acoustic candidates

Use licensed/consented clips and fixed-window log-mel features. Compare a small CNN with an appropriate pretrained audio model after checking licensing. Include cheering, alarms, laughter, traffic, music and non-distress screams. A scream is not an emotion diagnosis or proof of assault. Audio candidates cannot automatically identify a particular visible person.

## Fusion and deployment

Extend observations with device_id, event_id, capture timestamps/window, model version, calibration version and quality flags. Join matching zone/time windows; reject stale/replayed data. Evaluate gesture-only, audio-only, rule fusion and calibrated learned fusion on the same held-out episodes. Tune false alerts per camera-hour and recall using validation, then freeze thresholds for final test evaluation.

## Metrics and artifacts

Report precision, recall, F1, PR-AUC, calibration, episode recall, false alerts per camera-hour and alert delay by lighting, occlusion, angle and noise. Document prevalence and annotation agreement. A model release needs weights, label/preprocessing configs, calibration, license, dataset summary, model card, independent report and reproducible inference. No achieved accuracy is claimed.

## Readiness gates

1. Reviewed consent/annotation protocol.
2. Independently evaluated modality baselines.
3. Fusion tested on unseen sessions.
4. Failure behavior and operator overrides tested.
5. Controlled drill with responsible reviewers.
6. Approved supervised pilot with independent emergency reporting routes.

Face emotion/gender inference is unnecessary for the delivered policy. Physical proximity requires calibration. Dangerous objects and hotspot forecasts are independent optional research modules, not present capabilities.
