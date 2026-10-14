# Analysis of all five original files

All slides/pages were read and embedded flowcharts inspected. These are proposals, not trained-model or implementation artifacts. No code, dataset, weights, evaluation results, police integration contract or credentials were supplied. Text extracts are retained in SOURCE_EXTRACTS.txt; original files are not redistributed.

| File | Size | Main contribution | Role in consolidated design |
|---|---|---|---|
| HER TECHARMOR FINAL.pdf | 6 pages | FEM Guard, scream-plus-gesture confirmation, streetlight SOS, graded storage | Primary baseline because it is explicitly FINAL |
| SIH WOMEN SAFETY2.pptx | 6 slides | Closely matches final PDF's multimodal solution and feasibility | Companion final proposal |
| SIH HER TECHARMOR2pptx.pptx | 6 slides | Facial emotion, proximity, AI voice prompt, no-response escalation, Coral | Earlier wider proposal |
| HER TECHARMOR2-1.pptx | 6 slides | Similar earlier proposal, Orange Pi edge hardware, benefits | Alternative hardware version |
| WOMEN SAFETY PREDICTION.pptx | 9 slides | Priority levels, dangerous objects, temporal gesture LSTM, audio analysis, hotspot forecasts | Expanded explanatory proposal |

## Consolidated idea

Use existing camera infrastructure plus acoustic and manual inputs to identify candidate distress, combine cues, queue reviewable incidents and assist an authorized control room. Her TechArmor is the project/team identity; FEM Guard is the application name in the final PDF. Camera location and event context support an operator's response. Evidence clips require an independently implemented retention/access workflow.

## Differences and corrections

- Earlier versions infer fear/anger from faces and use an AI voice. The final version focuses on scream/gesture cross-checking. This release follows the final fusion workflow, using synthetic candidate scores until validated models exist.
- The original gender counts/lone-woman/surrounded-by-men triggers do not establish danger. The optional delivered baseline counts people without inferring gender. The policy prioritizes explicit SOS and corroborated distress candidates.
- Coral and Orange Pi are alternative proposals. Benchmark the selected models before buying an edge board.
- Source slides suggest temporary moderate storage and permanent/non-deletable high evidence. The release stores mutable metadata only, without automatic deletion or immutable recordings.
- Automatic police connection is a proposal. No authorized dispatch integration exists in this package. Queue entries do not send external messages.
- Prediction and dangerous-object detection appear as additional scope in the explanatory deck; they need separate models/data and evaluation.
- The final flowchart ties scream verification to gesture/threat detection. Manual SOS must bypass that condition and does in the delivered policy.
- Physical distance in meters requires camera calibration; pixel separation alone is insufficient.
- WOMEN SAFETY PREDICTION's 35% public-space and 60% workplace figures have insufficient provenance in the file. Do not reuse them as verified statistics.
- The named DejaView/North Korea case study is insufficiently sourced in the file; omit it from formal reports until independently verified.
- Reference links in the source slides are reading suggestions, not proof of project performance. The delivered documentation does not invent accuracy or response-time gains.

## Requirements traceability

| Original feature | Delivered | Remaining |
|---|---|---|
| Camera surveillance | Registry/heartbeat + optional local video people count | Web streaming, RTSP reconnect, credentials |
| Gender classification | General people count | Optional reviewed research; not needed for alerts |
| Gesture and scream | Input contract, lab, fusion policy | Capture, trained models, calibration |
| Manual SOS | Lab and device API boolean | Physical gateway, debounce, per-device identity |
| Graded threat | Explainable priority queue | Held-out threshold evaluation |
| Nearest station | Location text for operator | Coordinates, station directory, approved dispatch |
| Evidence | Metadata export and checksum | Event clips, legal hold, retention/access controls |
| Permanent recordings | Not implemented | Protected object store, reviewed retention policy |
| Cloud scale | Docker and local WSGI | Queue, PostgreSQL, workers, monitoring |
| Hotspot/object analytics | Model plan only | Relevant data and independent evaluation |

## Source reference handling

The originals cite ResearchGate, SJSU ScholarWorks, PiscoMed, PeerJ, ESRGroups and ScienceDirect. Bibliographic relevance and research claims have not been independently validated for this deliverable. Verify each reference before using it in an academic literature review.
