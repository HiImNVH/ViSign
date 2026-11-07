# Internal Admin Tool Contract

This contract applies only to the opt-in local `/api/admin/*` tool. It is not part of the public
`/api/v1` recognition contract and must not be exposed without an explicit deployment decision.

## Security boundary

- The API is disabled when `VISIGN_ADMIN_TOKEN` is absent or blank: no `/api/admin/*` route is mounted,
  so every path returns `404 ROUTE_NOT_FOUND`.
- `VISIGN_ADMIN_TOKEN` must be at least 16 characters; a shorter value stops the API at startup without
  printing the value.
- Enabled requests require `Authorization: Bearer <token>`. The token is compared in constant time and is
  never logged or returned.
- Tokens, W&B keys, raw clips and stack traces must not be committed or returned.
- Inspect artifacts are temporary and are removed after download or failure.

## Configuration

| Variable | Default | Effect |
|---|---|---|
| `VISIGN_ADMIN_TOKEN` | unset | Enables the tool |
| `VISIGN_ADMIN_WORKSPACE` | unset | Local directory for pilot run state and history (`runs/<runId>.json`, `runs/<runId>/`). Unset: pilot endpoints return 503 |
| `ADMIN_INSPECT_TIMEOUT_SECONDS` | `60` | Inspection deadline before 504 |

## Endpoints

| Method | Path | Purpose | Required behavior |
|---|---|---|---|
| POST | `/api/admin/inspect` | Inspect one MP4/WebM clip and download a ZIP report | Enforce byte limit and single inspection; cleanup in all paths |
| GET | `/api/admin/pilot` | Read current pilot state | Return a `TrainingRun` state |
| GET | `/api/admin/pilot/history` | Read local run history | Return sanitized run summaries, newest first |
| POST | `/api/admin/pilot/prepare` | Validate handoff and extract pilot features | Return 202; reject when a job is active |
| POST | `/api/admin/pilot/train` | Train/evaluate a prepared pilot | Return 202; require `ready`; reject concurrent job |

### `POST /api/admin/inspect`

- Request: `multipart/form-data` with the file in field **`video`**. The format is detected from the
  leading bytes (WebM EBML or MP4 `ftyp`), not from the file name or declared MIME type.
- Limits: the request body is limited to 10 MiB + 64 KiB (the same clip limit as `/api/v1/predictions`;
  the shared pipeline rejects larger clips) and the shared pipeline accepts at most 6 s by PTS. Only one
  inspection runs at a time.
- Response `200 application/zip` with `Content-Disposition: attachment; filename="visign-inspect.zip"`:
  - `report.json`: the shared pipeline report (detection ratios, usable frame ratio, timings, schema and
    extractor versions). `sourceName` is always the generic `clip.webm` or `clip.mp4`.
  - `landmarks.npz`: the extracted arrays (`coords`, `point_valid`, `visibility`, `presence`,
    `hand_scores`, `masks`, `tensor`, `tensor_mask`, `timestamps`, `target`). No video or image is returned.
- The clip is written to a private temporary directory and removed before the response, on error, and
  after a timeout once the worker finishes. Directories left by a killed process are removed at startup.

### Pilot endpoints

`GET /api/admin/pilot` returns the current `TrainingRun` (`phase: "idle"` and `runId: null` before any run).
`GET /api/admin/pilot/history` returns a `TrainingRun[]`, newest first. `POST /api/admin/pilot/prepare`
and `POST /api/admin/pilot/train` take no body and return **202 with the `TrainingRun`** that was started
(`preparing` or `training`). Clients poll `GET /api/admin/pilot` for progress. A run that was active when
the API stopped becomes `failed` on the next start.

`TrainingRun` (see `data-model.md`):

| Field | Type | Notes |
|---|---|---|
| `runId` | string or null | Random, for example `pilot-20261108-031500-a1b2c3` |
| `phase` | enum | `idle`, `preparing`, `ready`, `training`, `evaluating`, `complete`, `failed` |
| `datasetVersion`, `featureSchemaVersion` | string or null | Set after a successful prepare |
| `sampleTotal`, `accepted` | integer | `0 <= accepted <= sampleTotal` |
| `epoch`, `epochs` | integer or null | Training progress |
| `metrics` | object or null | `{accuracy, macroF1}`, each in `[0, 1]` or null; never sets `demoReady` |
| `wandbRunId`, `wandbMode`, `wandbUrl` | string or null | `wandbMode` is `online` or `offline` |
| `updatedAt` | ISO 8601 datetime | |
| `error` | string or null | Fixed Vietnamese message only; details stay in the server log and run directory |

### Pilot runner (P3 integration point)

The API owns locking, state and history; training belongs to the AI package. When the module
`visign_ai.pilot` provides `build_pilot_runner()`, the API uses the returned object:

- `prepare(workspace, progress)` validates the handoff (hash, manifest, schema, coverage), extracts features
  into `workspace` (the run directory) and returns an object with `datasetVersion`,
  `featureSchemaVersion`, `sampleTotal` and `accepted`.
- `train(workspace, progress)` trains and evaluates the prepared pilot and returns an object with `epochs`,
  `accuracy`, `macroF1`, `wandbRunId`, `wandbMode` and `wandbUrl`. It may call `progress.epoch(done, total)`
  and `progress.evaluating()`.
- Any exception, or a returned value outside these ranges, makes the run `failed` with a fixed message.
  Detailed reports belong in the run directory.

Without that module, `prepare` and `train` return 503.

## Stable outcomes

- Disabled tool: 404.
- Invalid token: 401.
- Another inspection or training job is active: 409.
- Invalid handoff/clip: 4xx with a stable Vietnamese message.
- Worker unavailable or environment incomplete: 503.
- Inspection timeout: 504.

Error bodies use the same shape as `/api/v1`: `{code, message, requestId}` with `X-Request-ID`.

| Status | Code | When |
|---|---|---|
| 404 | `ROUTE_NOT_FOUND` | Tool disabled |
| 401 | `ADMIN_UNAUTHORIZED` | Missing, malformed or wrong token; adds `WWW-Authenticate: Bearer` |
| 409 | `ADMIN_JOB_ACTIVE` | Another inspection, or another pilot job in `preparing`/`training`/`evaluating` |
| 409 | `ADMIN_PILOT_NOT_READY` | `train` while the current run is not `ready` |
| 413, 415, 422, 400 | `CLIP_TOO_LARGE`, `UNSUPPORTED_MEDIA_TYPE`, pipeline codes such as `CLIP_TOO_LONG`, `INVALID_REQUEST` | Invalid clip, same codes as `/api/v1` |
| 503 | `ADMIN_UNAVAILABLE` | Serving extra, workspace or pilot runner missing |
| 504 | `ADMIN_TIMEOUT` | Inspection exceeded `ADMIN_INSPECT_TIMEOUT_SECONDS` |
| 500 | `PREDICTION_FAILED` | Unexpected error, without trace or path |

Pilot metrics are integration evidence only. No admin endpoint may set a pilot artifact to
`demoReady=true` or bypass the full 10-meaning release gate on the FR-015 split.
