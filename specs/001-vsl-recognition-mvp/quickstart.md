# Quickstart Validation: ViSign VSL Recognition MVP

## Prerequisites

- Windows 11 with a working camera and Chromium-based browser.
- Python 3.12 provisioned through `uv`.
- Node.js 22.12+ and npm.
- A local raw-material directory not tracked by Git.
- No raw data is required for fixture-only integration.
- An approved manifest with at most 3 meanings is sufficient for pilot smoke training.
- A reviewed manifest with exactly 10 frozen P0 meanings is required for full training/release.

## Expected project commands

These commands become runnable after implementation tasks create the project files.

```powershell
uv sync --project services/inference-api
uv sync --project ai
npm ci --prefix apps/web
```

## Scenario 0: Gate WebM decoder and extractor on the demo laptop

Use a versioned fixture set containing clips recorded by the supported Chrome and Edge versions.

Expected:

- Every supported WebM fixture passes container/codec probe and decodes to at least one frame.
- Frame timestamps from PTS are strictly increasing and measured duration stays within the published
  tolerance.
- Corrupt WebM returns `CLIP_DECODE_FAILED`; unsupported containers return
  `UNSUPPORTED_MEDIA_TYPE`.
- MediaPipe version, extractor model hash and `extractorVersion` are recorded before bulk extraction.

## Scenario 1: Validate the dataset manifest

```powershell
uv run --project ai python -m visign_ai.dataset.validate_manifest `
  --manifest data/manifests/p0.csv
```

Expected:

- Exactly 10 active P0 meanings.
- No duplicate `sampleId` or `classLabel + region + variantName` identity.
- Dataset-level source and usage basis are recorded in the dataset card.
- No source-video (`recordingSessionId`) leakage between train, validation and test for full quality-gate data.
- Reports label the split `video-held-out` and make no unseen-signer claims unless `signerId` exists.
- A coverage report lists sample and source-video counts per class.

## Scenario 2: Extract landmarks deterministically

```powershell
uv run --project ai python -m visign_ai.landmarks.extract_manifest `
  --manifest data/manifests/p0.csv `
  --output data/processed/p0
```

Expected:

- Every accepted video produces a versioned landmark sequence or a stable rejection code.
- Re-running with the same extractor version produces the same schema and sample mapping.
- Golden clip→tensor output matches between extraction/training and API integration within tolerance.
- No raw video is copied into the repository.

## Scenario 3: Train and evaluate the GRU baseline

```powershell
uv run --project ai python -m visign_ai.training.train --config ai/configs/p0-gru.yaml
uv run --project ai python -m visign_ai.evaluation.evaluate `
  --config ai/configs/p0-gru.yaml `
  --split test
```

Expected demo gate:

- Macro-F1 is at least 0.80.
- Recall for every P0 meaning is at least 0.65.
- Accuracy, per-meaning precision/recall, confusion matrix, source-video/sample counts and latency report are generated.
- Model metadata names the dataset version and test split.
- `demoReady` remains false if any gate fails.

## Scenario 3A: Exercise delayed-training fallbacks

Start integration with the deterministic fixture artifact:

```powershell
$env:MODEL_ARTIFACT_PATH = "services/inference-api/tests/fixtures/model-artifacts/fixture"
uv run --project services/inference-api uvicorn visign_api.main:app --port 8000
```

When Quang has an approved subset of at most three meanings, train the pilot with the same GRU and
feature schema used by the full model:

```powershell
uv run --project ai python -m visign_ai.training.train --config ai/configs/pilot-gru.yaml
```

Switch `MODEL_ARTIFACT_PATH` to the pilot artifact, restart the API, then repeat health, model-info,
prediction contract and camera smoke tests. Repeat the same process for the full artifact after the
10-meaning training and evaluation finish.

Expected:

- Fixture, pilot and full artifacts load through the same predictor interface.
- `/api/v1/model-info` reports `artifactKind`, `extractorVersion`, `featureSchemaVersion`, actual
  supported meanings and `demoReady`.
- Fixture and pilot always report `demoReady=false`; missing evaluation metrics are `null` for fixture.
- The frontend displays a clear integration/pilot notice while `demoReady=false`.
- Moving between artifacts does not change the prediction response schema or frontend code.
- A failed artifact load is rolled back by restoring the previous `MODEL_ARTIFACT_PATH`, restarting
  the API and rerunning health/model-info/prediction smoke tests.

## Scenario 4: Run API contract tests

```powershell
uv run --project services/inference-api pytest services/inference-api/tests
```

Expected:

- Health and model-info return the schemas in `contracts/openapi.yaml`.
- Every endpoint echoes the caller's valid `X-Request-ID`, or generates one when the header is absent;
  response header and body ID match whenever the body includes `requestId`.
- Prediction accepts the supported camera MIME type.
- Prediction keeps `processingTimeMs`; optional `timingsMs` contains non-negative `decode`, `extract`
  and `infer`, while optional `qualityHints` contains only `handsDetectedRatio` and `frameCount`.
- Diagnostics never contain frames/landmarks, never change `accepted`, and are not persisted.
- Invalid, oversized, too-short, no-person and model-not-ready cases return stable error codes.
- Corrupt decodable-type clips return `CLIP_DECODE_FAILED`; a second request beyond the configured
  inference wait returns `SERVICE_BUSY` and can be retried.
- Unexpected inference failures return HTTP 500 with `PREDICTION_FAILED`, a matching `X-Request-ID`
  and no internal exception detail.
- Low confidence returns HTTP 200 with `accepted=false` and “Không nhận diện được”.
- Temporary camera clips are deleted on success and every failure path.

## Scenario 4A: Validate the opt-in admin tool

Set a local token and point the pilot worker at an approved handoff directory. Do not commit either
value or raw video.

```powershell
$env:VISIGN_ADMIN_TOKEN = '<local-token>'
$env:VISIGN_PILOT_DATA = '<approved-handoff-directory>'
```

Expected:

- Without `VISIGN_ADMIN_TOKEN`, admin endpoints behave as disabled; an invalid bearer token is denied.
- Clip inspection enforces its size/concurrency limit and deletes temporary input/output on both
  success and failure after the response lifecycle ends.
- Pilot preflight verifies manifest, clip hashes, schema/tensor compatibility and class coverage.
- A second prepare/train request is rejected while one run is active.
- History exposes run status, metrics and W&B online/offline evidence without exposing tokens.
- A completed pilot remains `demoReady=false`; it does not replace Scenario 3 full-model gates.

## Scenario 5: Run the local product

Terminal 1:

```powershell
uv run --project services/inference-api uvicorn visign_api.main:app --reload --port 8000
```

Terminal 2:

```powershell
npm run dev --prefix apps/web
```

Expected:

- The web app requests camera permission.
- The user can start, stop, cancel and submit one isolated sign.
- A successful result displays Vietnamese text and confidence.
- A rejected result displays “Không nhận diện được”.
- The disclaimer is visible near the result.

## Scenario 6: Run automated verification

```powershell
uv run --project ai pytest ai/tests
uv run --project services/inference-api pytest services/inference-api/tests
npm test --prefix apps/web
npx --prefix apps/web playwright test
```

Expected:

- Unit, contract and integration suites pass.
- E2E covers camera permission accepted, denied, low-confidence result, service unavailable and a
  successful recognition using a Y4M fake-camera fixture rather than an HTTP-only mock.
- The successful E2E result appears within 3 seconds after submission in the documented demo setup.

## Scenario 7: Verify a commit/push checkpoint

Follow `docs/team/git-checkpoints.md` on a clean local clone.

Expected:

- The owner updates only canonical source paths plus `members/<owner>/README.md` evidence.
- `git pull --rebase origin main` succeeds before commit and again immediately before push.
- The checkpoint-specific gate passes after the final rebase.
- The commit message contains the checkpoint and task IDs; no raw video/model/secret is staged.
- The owner creates `docs/evidence/checkpoints/CPx/Txxx-<owner>-smoke.md` from
  `docs/team/checkpoint-evidence-template.md`, recording commands, exit codes, environment and
  pass/fail/blocked/not-run reasons.
- After push, the evidence contains the full commit SHA/link and, when applicable, durable GitHub
  Actions, report, model/data checksum or Cloud Run revision/URL links.
- Another member reproduces the important gate and records `VERIFIED`; an expiring signed URL or a
  local-only path is not accepted as the only evidence.
- Only one member pushes during the assigned integration window; no force-push is used.

## Scenario 8: Verify Google Cloud production

Use the deployed URLs recorded in `docs/deployment-report.md`.

Expected:

- Public web and API use HTTPS; `/api/v1/health` reports the expected artifact/readiness.
- Camera prediction, low-confidence rejection, invalid clip and unknown route work through production.
- Admin routes are disabled; CORS origins and service accounts are restricted to the published design.
- Logs contain request ID/status/latency/error code but no clip bytes, landmark, token or secret.
- CPU/RAM/concurrency/max-instance settings and the demo cost estimate match `docs/cost-report.md`.
- Rolling back to the last smoke-tested image/artifact restores health and prediction successfully.

## Scenario 9: Verify judging evidence

Open `docs/team/judging-criteria-mapping.md` and follow every linked evidence item.

Expected:

- All eight rubric groups (100 points) have an owner, task and artifact.
- Dataset/model reports are reproducible and state limitations/bias rather than hiding failed cases.
- CI, cloud, security, community impact, cost and team contribution evidence points to the exact
  checkpoint commit used for the demo.
