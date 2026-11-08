# Tasks: ViSign VSL Recognition MVP

**Input**: Design documents from `specs/001-vsl-recognition-mvp/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/openapi.yaml](contracts/openapi.yaml),
[contracts/admin-tools.md](contracts/admin-tools.md)

**Tests**: Bắt buộc theo hiến pháp. Trong mỗi story, viết test và xác nhận test thất bại trước khi
thực hiện phần code tương ứng.

**Organization**: Task được nhóm theo user story để từng phần có thể kiểm thử độc lập.

**Integration tracking**: [docs/team/implementation-status.md](../../docs/team/implementation-status.md)
ghi checkpoint đã có trên `origin/main`; code legacy chỉ là reference cho đến khi được đưa sang theo task.

**Baseline repository mới 2026-11-07**: `HiImNVH/ViSign` bắt đầu trống. Spec Kit được chuẩn bị làm
CP0; application code chỉ được đưa sang từ legacy theo checkpoint nhỏ, test được và push tuần tự trên
`main`. Không dùng nhánh vai trò, không force-push và không full-code dump. Xem
[docs/team/git-checkpoints.md](../../docs/team/git-checkpoints.md).

## Phân công dự kiến

| Mã người | Thành viên hiện tại | Vai trò chính | Task chịu trách nhiệm chính |
|---|---|---|---|
| **P1** | **Huy** | Quản lý dự án, checkpoint, CI, nghiệm thu và trình bày | T032, T047, T067–T070, ~~T071~~ (bỏ), T084–T087, T090–T091, T093, T097 |
| **P2** | **Tín** | Backend, API, security, cloud, tích hợp predictor và CP1 toolchain | T001–T007, T019–T026, T030, T037–T038, T044–T045, T048–T050, T055, T060, T064, T066, T072–T073, T078–T080, T092, T095–T096, T099 |
| **P3** | **Cường** | MediaPipe pipeline, training, evaluation và cost benchmark | T014–T017, T029, T033–T036, T054, T057–T059, T062, T065, T083, T089, T094 |
| **P4** | **Quang** | Data crawler, data analysis, manifest và split | T008–T013, T018, T056, T061, T076–T077, T098 |
| **P5** | **Hiển** | UX/UI, frontend và frontend quality evidence | T027–T028, T031, T039–T043, T046, T051–T053, T063, T074–T075, T081–T082, T088, T090, T100–T104 |

**Quy ước ownership**:

- Người chịu trách nhiệm chính cập nhật trạng thái task và bằng chứng kiểm thử; Huy theo dõi tiến độ,
  dependency và quyết định chuyển checkpoint.
- Task phối hợp vẫn có đúng một người chịu trách nhiệm chính. Người phối hợp được ghi trong mô tả hoặc
  khi cập nhật task, không tạo hai owner ngang nhau.
- Mỗi người có `members/pN-name/README.md` để ghi task đang làm, gate, evidence, blocker và handoff;
  thư mục này không chứa bản sao source code.
- Quang bàn giao manifest, quyền sử dụng, coverage và split; Cường là consumer và không tự thay đổi
  nhãn/split đã duyệt khi training.
- Cường chịu trách nhiệm toàn bộ chuỗi MediaPipe → GRU training → metrics → release metadata. Tín
  review khả năng load artifact và giữ predictor/API contract ổn định.
- Tín chịu trách nhiệm backend/API ở cả ba artifact kind; Hiển chỉ phụ thuộc OpenAPI/model-info, không
  phụ thuộc trực tiếp vào file model.
- Huy quyết định chuyển checkpoint. Fixture/pilot luôn `demoReady=false`; chỉ full model đủ 10 ý
  nghĩa và đạt gate mới được Huy duyệt làm model demo chính thức.
- P1–P5 là mã vị trí thành viên (`Person 1`–`Person 5`), không biểu thị độ ưu tiên và không liên quan
  đến `[P]` (parallel marker) hoặc priority của User Story.
- Hồ sơ tiến độ theo vai trò nằm trong `docs/team/`; `tasks.md` là nguồn sự thật cho checkbox hoàn
  thành, còn member file ghi trạng thái hằng ngày, blocker, bằng chứng và lịch sử bàn giao.
- Mỗi checkpoint có một integration window do Huy mở. Owner pull/rebase, test, commit, pull/rebase
  lần cuối, rerun gate rồi push thường; thành viên khác chờ window kế tiếp và không force-push.

**Từ điển mã dùng trong task/plan**:

| Mã | Ý nghĩa |
|---|---|
| `Person P1`–`Person P5` | Mã người/vị trí thành viên; bảng phân công phía trên là nguồn chuẩn |
| `M0` | Hardening bắt buộc trước pilot; đã nhập vào task `T*` bên dưới |
| `M1` | Candidate cải thiện trước full/demo, chỉ mở khi trigger được Huy duyệt |
| `M2` | Candidate sau MVP; không thuộc backlog cam kết hiện tại |
| `US Priority P1/P2` | Độ ưu tiên User Story trong `spec.md` |
| `Vocabulary P0` | 10 ý nghĩa thuộc phạm vi MVP |
| `[P]` | Marker task có thể chạy song song |

Không dùng mã `VS-*` từ phản hồi senior làm backlog thứ hai. `tasks.md` vẫn là nguồn sự thật duy nhất.

**M0 coverage trong backlog hiện tại**:

| Lỗ hổng M0 | Task đã cập nhật | Owner / reviewer |
|---|---|---|
| WebM decode + timestamp | T014–T015, T049 | Person P3/Cường; Person P2/Tín review API boundary |
| Extractor/schema lock + train/serve parity | T014–T017, T037 | Person P3/Cường; Person P2/Tín review serving |
| Video-held-out full quality gate (FR-015) | T018, T056–T058 | Person P4/Quang; Person P3/Cường consumer |
| Decode/busy stable errors | T021–T022, T026, T045, T049–T050 | Person P2/Tín |
| Fake-camera E2E | T032, T047 | Person P1/Huy; Person P5/Hiển review UX |
| Request correlation + optional diagnostics | T020, T023, T026–T027, T030, T038, T040, T045 | Person P2/Tín; Person P5/Hiển consumer |

**Milestone dữ liệu đã được tách lại**:

1. Quang đã đóng băng danh mục 10 Meaning tại `data/manifests/p0-meanings.csv`.
2. T013 chỉ quản lý vocabulary registry; không còn gộp sample manifest vào cùng một checkbox.
3. T076 audit bản phát triển/pilot (pilot Giấy tờ–Nhận theo quyết định lead 2026-11-08; số clip theo audit thực tế).
4. T077 hoàn thiện sample manifest full 10 nghĩa, coverage và video-held-out split.
5. Huy xác nhận checkpoint T077 trước khi Cường chạy full training; T076 chỉ mở pilot fallback.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Có thể làm song song vì sửa file khác và không phụ thuộc task chưa hoàn thành.
- **[Story]**: Ánh xạ đến User Story trong `spec.md`.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Tạo cấu trúc monorepo và toolchain tối thiểu.

- [X] T001 Tạo các thư mục nguồn theo `plan.md` gồm `apps/web/`, `services/inference-api/`, `ai/`, `data/`, `tests/`, `docs/`, `members/`, `.github/workflows/` và `infra/aws/`
- [X] T002 [P] Khởi tạo Python 3.12 project và dependency groups cho API trong `services/inference-api/pyproject.toml`
- [X] T003 [P] Khởi tạo Python 3.12 project và dependency groups cho AI trong `ai/pyproject.toml`
- [X] T004 [P] Khởi tạo React TypeScript Vite app và test scripts trong `apps/web/package.json`
- [X] T005 [P] Cấu hình Ruff, mypy và pytest dùng chung cho Python trong `pyproject.toml`
- [X] T006 [P] Cấu hình ESLint, TypeScript type-check, Vitest và Playwright trong `apps/web/eslint.config.js`, `apps/web/tsconfig.json`, `apps/web/vite.config.ts` và `apps/web/playwright.config.ts`
- [X] T007 Cập nhật `.gitignore` để loại raw video, processed artifacts, model binaries, file tạm và secret nhưng giữ manifest/metadata trong `.gitignore`
- [X] T008 [P] Viết hướng dẫn đặt raw material ngoài repository và quy tắc quyền sử dụng trong `data/README.md`

**Checkpoint**: Cả ba project cài dependency, lint và chạy test rỗng thành công.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Contract dữ liệu, preprocessing và ranh giới API dùng chung cho mọi story, đồng thời mở
đường tích hợp bằng fixture mà không chờ full model.

**CRITICAL**: Full-model track không bắt đầu trước khi data foundation hoàn thành. Fixture integration
track MAY bắt đầu khi T019–T028 ổn định và không được trình bày là model demo-ready.

- [X] T009 [P] Định nghĩa `Meaning`, `SignClass` và enum metadata theo các constraint trong `data-model.md` tại `ai/src/visign_ai/dataset/entities.py`
- [X] T010 [P] Định nghĩa schema hàng manifest gồm `sampleId` duy nhất, `recordingSessionId` bắt buộc, `licenseStatus`, `verificationStatus` và split tại `ai/src/visign_ai/dataset/manifest_schema.py`
- [X] T011 [P] Viết unit tests cho duplicate ID, license không approved, rejected sample và signer/session leakage tại `ai/tests/dataset/test_manifest_validation.py`
- [X] T012 Cài manifest validator và báo cáo coverage theo class/video gốc tại `ai/src/visign_ai/dataset/validate_manifest.py`
- [X] T013 Duy trì danh mục đúng 10 Meaning P0, display text/category/priority và invariant không trùng tại `data/manifests/p0-meanings.csv`
- [X] T014 [P] Viết decoder/extractor tests cho WebM VP8/VP9 Chrome/Edge, giữ orientation camera, PTS tăng dần, corrupt clip, representative clips, tensor/mask `32×234` và golden offline→API parity tại `ai/tests/landmarks/test_video_pipeline.py`
- [X] T015 Cài `VideoDecoder` PyAV cho WebM VP8/VP9 0.3–6 giây tối đa 10 MiB, giữ nguyên orientation, và MediaPipe video adapter với pinned `extractorVersion` tại `ai/src/visign_ai/landmarks/video_decoder.py` và `ai/src/visign_ai/landmarks/holistic_extractor.py`
- [X] T016 Cài draft feature schema v0.3 tensor `32×234`, chuẩn hóa tọa độ, resampling và missing-landmark mask dùng chung train/API; chỉ chuyển APPROVED sau representative-clip review tại `ai/src/visign_ai/landmarks/sequence_transform.py` và `ai/configs/feature_schema.json`
- [X] T017 Cài CLI trích xuất toàn manifest, ghi extractor/schema version và stable decode/extraction rejection code tại `ai/src/visign_ai/landmarks/extract_manifest.py`
- [X] T018 Cài video-held-out split theo `recordingSessionId` cho full gate (ưu tiên signer khi có `signerId`), gắn nhãn split và cấm unseen-signer claim tại `ai/src/visign_ai/dataset/create_splits.py`
- [X] T019 [P] Định nghĩa model metadata cho `fixture|pilot|full`, extractor/feature schema version, nullable fixture accuracy/precision/recall/Macro-F1 và gate `full && 10 meanings && macroF1 >= 0.80 && mọi perMeaningRecall >= 0.65` tại `services/inference-api/src/visign_api/domain/model_version.py`
- [X] T020 [P] Định nghĩa prediction request/accepted/rejected/error states không thể kết hợp sai; success response giữ `processingTimeMs` và optional `timingsMs {decode,extract,infer}` plus `qualityHints {handsDetectedRatio,frameCount}` không chứa landmark tại `services/inference-api/src/visign_api/domain/prediction.py`
- [X] T021 [P] Cài error catalog ổn định gồm `CLIP_DECODE_FAILED` và `SERVICE_BUSY` đúng `contracts/openapi.yaml` tại `services/inference-api/src/visign_api/domain/errors.py`
- [X] T022 Cài cấu hình model path, MIME allowlist, byte/duration limit, inference wait timeout và CORS tại `services/inference-api/src/visign_api/config.py`
- [X] T023 Cài structured logging không persist payload gồm request ID, model version, total/per-stage duration, accepted và error code tại `services/inference-api/src/visign_api/observability.py`
- [X] T024 Cài temporary-clip boundary luôn xóa file trong success/failure tại `services/inference-api/src/visign_api/inference/temporary_clip.py`
- [X] T025 [P] Viết unit tests chứng minh temporary clip bị xóa ở mọi đường đi tại `services/inference-api/tests/unit/test_temporary_clip.py`
- [X] T026 Cài FastAPI app release `0.0.1`, public router `/api/v1`, `X-Request-ID` receive/generate/echo middleware, bounded single-inference coordinator và exception mapping tại `services/inference-api/src/visign_api/main.py` và `services/inference-api/src/visign_api/api/router.py`
- [X] T027 [P] Định nghĩa TypeScript API types tối thiểu bám `contracts/openapi.yaml`, giữ `X-Request-ID`, optional prediction diagnostics, `artifactKind`, `extractorVersion`, `featureSchemaVersion`, actual meanings và nullable fixture metrics tại `apps/web/src/types/inference-api.ts`; tự động sinh type bằng `openapi-typescript` thuộc M1
- [X] T028 [P] Tạo Vietnamese UI copy, disclaimer và accessible labels tại `apps/web/src/content/vi.ts`
- [ ] T098 Sau khi lead bàn giao quy ước, đóng băng naming/normalization/version cho file dữ liệu, cập nhật validator và ví dụ hợp lệ/không hợp lệ tại `docs/contracts/data-conventions.md`, `ai/src/visign_ai/dataset/manifest_schema.py` và `ai/tests/dataset/test_manifest_validation.py`
- [X] T099 Sau khi lead bàn giao quy ước, đóng băng API v1 naming/status/error/versioning cho FE-BE và cập nhật contract/types/drift tests tại `docs/contracts/api-conventions.md`, `specs/001-vsl-recognition-mvp/contracts/openapi.yaml`, `apps/web/src/types/inference-api.ts` và `tests/contract/`

**Checkpoint**: Manifest có thể audit; cùng feature schema được dùng cho training và serving; API app
khởi động nhưng chưa cần model thật. T098–T099 là ID thêm sau để giữ lịch sử backlog nhưng bắt buộc
thực hiện trước khi đóng Phase 2; không renumber T001–T097.

---

## Phase 3: User Story 1 - Nhận diện một ký hiệu (Priority: P1) — MVP

**Goal**: Camera → đoạn ký hiệu → API → model → chữ tiếng Việt và độ tin cậy.

**Independent Test**: Dùng model fixture có một ký hiệu hợp lệ, ghi/gửi clip camera và nhận response
đúng contract với `accepted=true`, chữ tiếng Việt và model version trong không quá 3 giây.

### Tests for User Story 1

- [X] T029 [P] [US1] Viết model shape, packed-sequence, deterministic forward và class-subset tests dùng chung cho pilot/full tại `ai/tests/training/test_gru_classifier.py`
- [X] T030 [P] [US1] Tạo deterministic fixture artifact và viết contract tests cho release `0.0.1`/API `v1`, chứng minh fixture/pilot/full dùng cùng accepted response schema, echo/generated `X-Request-ID`, non-negative optional timings và bounded quality hints tại `services/inference-api/tests/fixtures/model-artifacts/fixture/` và `services/inference-api/tests/contract/test_predictions_contract.py`
- [X] T031 [P] [US1] Viết component tests cho permission, recording và accepted result tại `apps/web/tests/recognition/recognition-flow.test.tsx`
- [ ] T032 [P] [US1] Viết E2E happy path bằng Chromium fake-camera Y4M và fixture predictor, không thay camera flow bằng HTTP-only mock, tại `apps/web/tests/e2e/recognition-happy-path.spec.ts`

### Implementation for User Story 1

- [X] T033 [US1] Cài GRU classifier nhận padded landmark sequence tại `ai/src/visign_ai/training/gru_classifier.py`
- [X] T034 [US1] Cài dataset loader và batching giữ label order ổn định tại `ai/src/visign_ai/training/sequence_dataset.py`
- [X] T035 [US1] Tạo cấu hình seed tái lập cho pilot tối đa 3 từ và full 10 từ tại `ai/configs/pilot-gru.yaml` và `ai/configs/p0-gru.yaml`
- [X] T036 [US1] Cài training CLI nhận class subset và lưu artifact metadata bất biến gồm `artifactKind`, dataset/feature schema/class map tại `ai/src/visign_ai/training/train.py`
- [X] T037 [US1] Cài predictor interface với deterministic fixture và pilot/full adapter qua `MODEL_ARTIFACT_PATH`; nạp nguyên gói weights/schema/model metadata/evaluation, giữ class order, dùng artifact confidence threshold, kiểm extractor/schema và fail closed để rollback tại `services/inference-api/src/visign_api/inference/predictor.py`
- [X] T038 [US1] Cài `POST /api/v1/predictions` cho accepted result với total/per-stage timings và quality hints không chứa frame/landmark tại `services/inference-api/src/visign_api/api/predictions.py`
- [X] T039 [P] [US1] Cài camera permission, preview và start/stop/cancel recording tại `apps/web/src/features/recognition/CameraRecorder.tsx`
- [X] T040 [P] [US1] Cài typed API client gửi camera blob, truyền/đọc `X-Request-ID`, đọc model-info và bỏ qua an toàn optional diagnostics khi không có tại `apps/web/src/services/inferenceApi.ts`
- [X] T041 [US1] Cài recognition state machine cho idle/permission/recording/submitting/result và loaded artifact kind tại `apps/web/src/features/recognition/useRecognition.ts`
- [X] T042 [US1] Cài accepted result view gồm tiếng Việt, confidence, disclaimer và cảnh báo integration/pilot khi `demoReady=false` tại `apps/web/src/features/recognition/RecognitionResult.tsx`
- [X] T043 [US1] Ghép luồng camera, model-info và prediction vào trang chính mà không rẽ nhánh endpoint theo artifact tại `apps/web/src/App.tsx`

**Checkpoint**: US1 chạy độc lập với model fixture và có thể demo happy path.

---

## Phase 4: User Story 2 - Từ chối kết quả không chắc chắn (Priority: P1)

**Goal**: Không đoán bắt buộc; xử lý low confidence, clip lỗi, camera lỗi và service lỗi an toàn.

**Independent Test**: Gửi fixture low-confidence, no-person, clip sai và từ chối camera; mỗi trường hợp
hiển thị đúng rejected/error state, không hiển thị một từ như kết quả chắc chắn và cho phép thử lại.

### Tests for User Story 2

- [X] T044 [P] [US2] Viết unit tests cho threshold boundary và accepted/rejected decision tại `services/inference-api/tests/unit/test_prediction_decision.py`
- [X] T045 [P] [US2] Mở rộng contract tests cho 400, 413, 415, `CLIP_DECODE_FAILED`, `SERVICE_BUSY` với optional `Retry-After`, model-not-ready 503, `PREDICTION_FAILED` 500 không lộ exception, low-confidence HTTP 200 và `X-Request-ID` trên mọi response tại `services/inference-api/tests/contract/test_predictions_contract.py`
- [X] T046 [P] [US2] Viết web tests cho denied permission, cancel, retry, rejected và service unavailable tại `apps/web/tests/recognition/recognition-errors.test.tsx`
- [ ] T047 [P] [US2] Viết E2E permission-denied, corrupt clip, service-busy, low-confidence và retry flows bằng fake-camera/control fixture tại `apps/web/tests/e2e/recognition-negative-paths.spec.ts`

### Implementation for User Story 2

- [X] T048 [US2] Cài pure confidence decision trả accepted hoặc “Không nhận diện được” tại `services/inference-api/src/visign_api/inference/prediction_decision.py`
- [X] T049 [US2] Cài clip validation cho MIME, byte limit, WebM magic bytes, decoder probe, PTS duration, person và landmark sufficiency tại `services/inference-api/src/visign_api/inference/clip_validator.py`
- [X] T050 [US2] Hoàn thiện error mapping và cleanup cho prediction endpoint tại `services/inference-api/src/visign_api/api/predictions.py`
- [X] T051 [US2] Cài rejected result và retry action tại `apps/web/src/features/recognition/RecognitionResult.tsx`
- [X] T052 [US2] Cài camera/API error presentation với thông báo tiếng Việt ổn định tại `apps/web/src/features/recognition/RecognitionError.tsx`
- [X] T053 [US2] Cài timeout, cancel request và reset state tại `apps/web/src/features/recognition/useRecognition.ts`

**Checkpoint**: US1 và US2 đều chạy; mọi low-confidence/invalid input fail closed.

---

## Phase 5: User Story 3 - Đánh giá chất lượng bản MVP (Priority: P2)

**Goal**: Model release có thể truy về dữ liệu, split và metrics; evaluator xác minh được demo gate.

**Independent Test**: Chạy evaluation trên test split rồi kiểm tra report/model-info chứa dataset version,
10 meanings, accuracy, precision/recall từng meaning, Macro-F1, confusion matrix, latency, split FR-015
provenance và `demoReady` đúng gate.

### Tests for User Story 3

- [X] T054 [P] [US3] Viết evaluation metric tests và chứng minh fixture/pilot không thể qua full demo gate tại `ai/tests/evaluation/test_model_gate.py`
- [X] T055 [P] [US3] Viết `GET /health` và `GET /model-info` contract tests cho fixture/pilot/full, `extractorVersion`, `featureSchemaVersion`, actual meanings và nullable metrics tại `services/inference-api/tests/contract/test_model_info_contract.py`
- [X] T056 [P] [US3] Viết split regression tests chứng minh full test không trùng video gốc và split không có `signerId` không thể mang nhãn unseen-signer tại `ai/tests/dataset/test_split_audit.py`

### Implementation for User Story 3

- [X] T057 [US3] Cài accuracy, Macro-F1, per-meaning precision/recall, confusion matrix, signer/sample counts và latency evaluation tại `ai/src/visign_ai/evaluation/metrics.py`
- [X] T058 [US3] Cài evaluation CLI sinh JSON metrics, confusion-matrix image và split provenance (`video-held-out`/signer) tại `ai/src/visign_ai/evaluation/evaluate.py`
- [X] T059 [US3] Cài metadata writer cho mọi artifact và release gate chỉ chấp nhận full 10-meaning model đạt gate trên split FR-015 tại `ai/src/visign_ai/evaluation/release_gate.py`
- [X] T060 [US3] Cài `GET /api/v1/health` và `GET /api/v1/model-info` công bố artifact kind, extractor/feature schema version, actual meanings và readiness tại `services/inference-api/src/visign_api/api/system.py`
- [ ] T061 [P] [US3] Viết dataset card công bố nguồn, tính hợp pháp, chất lượng, độ đại diện, phương thức thu thập/xử lý, coverage và bias gaps từ manifest audit tại `docs/dataset-card.md`
- [ ] T062 [P] [US3] Viết model card gồm lý do chọn GRU, protocol tái lập, artifact kind, supported meanings, accuracy, per-meaning precision/recall, Macro-F1, confusion matrix, latency, split FR-015/OOD result, bias, explainability limits, fallback status và safety disclaimer tại `docs/model-card.md`

**Checkpoint**: Chỉ model đạt đủ gate mới được API tải làm model demo.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Kiểm chứng toàn hệ thống và chuẩn bị demo.

- [X] T064 [P] Thêm integration test cùng representative clip tạo tensor/mask khớp offline↔API, rồi nạp artifact, prediction, temporary-video cleanup và artifact swap cho fixture/pilot/full tại `tests/integration/test_prediction_pipeline.py`
- [ ] T065 Chạy performance benchmark và ghi p50/p95 per-stage/total, throughput, CPU/RAM peak trên local và production tại `ai/src/visign_ai/evaluation/benchmark_inference.py` và `docs/performance-report.md`
- [X] T066 Audit privacy để chứng minh không có video/frame/PII trong log hoặc artifact tại `tests/integration/test_prediction_privacy.py`
- [X] T063 [P] Chạy accessibility audit cho keyboard, focus, status announcements và camera labels tại `apps/web/tests/accessibility/recognition-accessibility.spec.ts`, lưu kết quả trong `docs/verification-report.md`
- [ ] T067 Chạy toàn bộ quickstart gồm local, CI, cloud smoke, fallback/swap/rollback và lưu commit/revision/results vào `docs/verification-report.md`
- [ ] T068 [P] Viết demo script theo rubric, gồm bài toán thực tế, điểm khác biệt, full/pilot disclosure, dữ liệu, model, cloud, chi phí, giới hạn và Q&A tại `docs/demo-script.md`
- [ ] T069 [P] Viết hướng dẫn cài đặt, cấu trúc module, checkpoint Git, chạy local/cloud, artifact switching/rollback và giới hạn MVP tại `README.md`
- [ ] T070 Tổng duyệt demo trên URL production và local fallback, ghi camera/browser/model/cloud revision, artifact kind và demoReady tại `docs/demo-rehearsal.md`
- [-] ~~T071 Kiểm thử khả thi/usability với ít nhất 10 người thuộc nhóm mục tiêu, ghi task completion, lỗi, phản hồi và thay đổi ưu tiên tại `docs/usability-report.md`~~ — **BỎ KHỎI PHẠM VI** (lead 2026-11-08: sản phẩm là bản trình chiếu chấm điểm, chưa có người dùng thật; không claim kết quả usability)

---

## Phase 7: User Story 2 HTTP Routing Follow-up

**Goal**: Chuẩn hóa lỗi route/method và trailing-slash redirect để frontend không hiển thị raw
framework message hoặc gửi lại video ngoài ý muốn.

**Independent Test**: Gọi unknown route, sai method và canonical route có trailing slash với redirect
disabled; xác nhận status/error envelope/header đúng, sau đó mô phỏng các response đó ở frontend và
kiểm tra stable Vietnamese copy, không auto-resubmit và không lộ raw server text.

- [X] T072 [P] [US2] Viết backend contract tests cho `404 ROUTE_NOT_FOUND`, `405 METHOD_NOT_ALLOWED`, `307` giữ method/body/`Location`, `X-Request-ID`, cùng hành vi chưa bật `403`/`304` tại `services/inference-api/tests/contract/test_http_routing_contract.py`
- [X] T073 [US2] Cài stable error catalog và exception handlers cho 404/405, giữ `Allow`/`Location`/`X-Request-ID`, document 404/405/307 và giữ health `Cache-Control: no-store` tại `services/inference-api/src/visign_api/domain/errors.py`, `services/inference-api/src/visign_api/main.py` và `contracts/openapi.yaml`
- [X] T074 [P] [US2] Viết frontend transport/component tests cho 404/405, canonical URL, không auto-resubmit và không render raw server text tại `apps/web/tests/services/inferenceApi.test.ts` và `apps/web/tests/recognition/recognition-errors.test.tsx`
- [X] T075 [US2] Thêm typed API compatibility errors và stable Vietnamese placeholders; reserve 403/304 nhưng không trình bày là trạng thái MVP đang hoạt động tại `apps/web/src/services/inferenceApi.ts`, `apps/web/src/content/vi.ts` và `apps/web/src/features/recognition/RecognitionError.tsx`

**Checkpoint**: Backend và frontend cùng tuân theo `docs/team/backend-http-status-contract.md` và
`docs/team/frontend-http-status-placeholders.md`; US1 prediction success flow không thay đổi.

---

## Phase 8: User Story 3 Data Completion Follow-up

**Goal**: Tách bằng chứng pilot khỏi manifest full để không dùng clip phát triển hoặc clip pilot
Giấy tờ–Nhận như bằng chứng phát hành 10 nghĩa.

**Independent Test**: Chạy manifest validator và split audit; pilot report chỉ công bố phạm vi pilot,
còn full manifest có đúng 10 nghĩa, nguồn/quyền mức bộ dữ liệu, coverage theo video gốc và không leakage.

- [ ] T076 [P] [US3] Audit bản bàn giao phát triển/pilot, ghi hash/session/split và accepted/rejected coverage vào `data/manifests/pilot.csv` và `docs/dataset-card.md`
- [ ] T077 [US3] Hoàn thiện manifest full đúng 10 nghĩa, coverage meaning×video gốc và video-held-out split không leakage tại `data/manifests/p0.csv` và `docs/dataset-card.md`

**Checkpoint**: T076 chỉ mở pilot; full training/release gate chỉ mở sau T077 và T056.

---

## Phase 9: User Story 4 - Công cụ Admin/train-model nội bộ (Priority: P2)

**Goal**: Hợp nhất công cụ đã có trên `admin/train-model` thành luồng nội bộ opt-in, có contract,
test bảo mật/cleanup/concurrency và không ảnh hưởng public `/api/v1`.

**Independent Test**: Bật/tắt token, inspect clip, chạy preflight→train pilot, thử tạo job song song,
đọc history/W&B evidence và xác nhận pilot vẫn `demoReady=false`.

- [X] T078 [P] [US4] Viết backend tests cho disabled 404, invalid-token 401, inspect byte/concurrency limit, cleanup và single-active-pilot-job tại `services/inference-api/tests/contract/test_admin_tools_contract.py`
- [X] T079 [US4] Chuẩn hóa opt-in admin config, sanitized errors, temporary inspect lifecycle và worker/job locking tại `services/inference-api/src/visign_api/api/admin.py`, `services/inference-api/src/visign_api/api/pilot.py` và `services/inference-api/src/visign_api/config.py`
- [X] T080 [US4] Đồng bộ response models và endpoint behavior với `specs/001-vsl-recognition-mvp/contracts/admin-tools.md` tại `services/inference-api/src/visign_api/api/admin.py` và `services/inference-api/src/visign_api/api/pilot.py`
- [X] T081 [P] [US4] Viết frontend tests cho token form, inspect, preflight, train, active-job conflict, history và W&B online/offline tại `apps/web/tests/admin/admin-training.test.tsx`
- [ ] T082 [US4] Tích hợp route `/admin/train-model`, typed admin client và stable Vietnamese states tại `apps/web/src/features/admin/AdminTraining.tsx`, `apps/web/src/features/admin/PilotPanel.tsx` và `apps/web/src/services/adminApi.ts`
- [ ] T083 [US4] Chạy pilot Giấy tờ–Nhận (`GIAY_TO`, `NHAN`; lead đổi từ Sốt–Cảm ơn ngày 2026-11-08) từ bản bàn giao đã audit và ghi dataset/run ID, sample counts, metrics, W&B evidence cùng `demoReady=false` tại `docs/pilot-report.md`
- [ ] T084 [US4] Review ranh giới user/admin, secret handling, retention và release-claim checklist; ghi quyết định nghiệm thu tại `docs/admin-acceptance.md`

**Checkpoint**: Công cụ admin có thể tích hợp ở checkpoint riêng; không chặn user MVP và không được dùng để bỏ qua
T077/full release gate.

---

## Phase 10: User Story 5 - Nghiệm thu theo tiêu chí hội đồng (Priority: P1)

**Goal**: Tạo bằng chứng kiểm chứng được cho toàn bộ bảng điểm 100 điểm, CI/CD và AWS
production, đồng thời giữ lịch sử đóng góp/checkpoint rõ ràng của 5 thành viên.

**Independent Test**: Một reviewer ngoài nhóm dùng ma trận rubric để mở từng artifact, chạy quality
workflow và production smoke/rollback mà không cần hỏi người viết code.

- [ ] T085 [P] [US5] Duy trì ma trận 8 nhóm/100 điểm với owner, task, artifact, gate và trạng thái tại `docs/team/judging-criteria-mapping.md`
- [X] T086 [P] [US5] Thiết lập quy tắc direct-main tuần tự, integration queue, commit format/scope theo từng thành viên, pre-push gates, mẫu smoke evidence có SHA/Actions/report/cloud link và 5 workspace logs tại `docs/team/git-checkpoints.md`, `docs/team/checkpoint-evidence-template.md`, `docs/team/member-template.md`, `members/README.md` và `members/p1-huy/README.md` đến `members/p5-hien/README.md`
- [ ] T087 [P] [US5] Viết hồ sơ sáng tạo và tính khả thi gồm đối tượng sử dụng, pain point, điểm khác biệt, comparison, phạm vi áp dụng và bằng chứng user validation tại `docs/innovation-feasibility.md`
- [X] T088 [P] [US5] Audit FE/UI/UX theo responsive, accessibility, camera usability, module/component boundaries và visual consistency; lưu screenshot/test evidence tại `docs/frontend-quality-report.md`
- [ ] T089 [P] [US5] Viết tests/report cho OOD, signer/lighting/angle edge cases, false accept, class imbalance/bias, stability và giải thích decision rule tại `ai/tests/evaluation/test_safety_robustness.py` và `docs/ai-safety-report.md`
- [X] T090 [P] [US5] Review cấu trúc module, dependency direction, coding conventions, duplication và khả năng mở rộng FE/BE/AI; ghi action/evidence tại `docs/architecture-quality-report.md`
- [ ] T091 [US5] Cài GitHub Actions quality/deploy gates cho lint, typecheck, unit, contract, integration, web build và AWS deploy-after-pass bằng OIDC tại `.github/workflows/quality.yml` và `.github/workflows/deploy-aws.yml`
- [X] T092 [P] [US5] Chạy security/reliability audit gồm dependency/secret scan, upload abuse, CORS, headers, rate/resource boundaries, timeout, log privacy và recovery tại `tests/security/` và `docs/security-report.md`
- [ ] T093 [P] [US5] Viết báo cáo tác động cộng đồng, nhóm hưởng lợi, accessibility/usability result, rủi ro gây hiểu nhầm và roadmap mở rộng có điều kiện tại `docs/community-impact.md`
- [ ] T094 [P] [US5] Đo CPU/RAM/storage/network/cloud cost, so sánh ít nhất một phương án tối ưu và chốt budget/quality/latency trade-off tại `docs/cost-report.md`
- [ ] T095 [US5] Đóng gói web/API thành image ECR theo commit SHA, deploy hai container lên một EC2 host có Elastic IP, nạp model version/hash từ private S3 và công bố CloudFront HTTPS URL bằng CloudFormation/Compose tái lập tại `infra/aws/`; cấu hình default static behavior và `/api/*` behavior cho đủ methods, `CachingDisabled`, body/query/contract headers cùng nguyên trạng status/`X-Request-ID`; ghi image digest, S3 version, SSM result, Elastic IP và URL tại `docs/deployment-report.md`
- [ ] T096 [US5] Cấu hình GitHub OIDC + least-privilege IAM/EC2 role, no-SSH security group chỉ nhận CloudFront origin-facing traffic, SSM `SecureString`, admin-disabled, CloudWatch log/metric không chứa video/landmark/secret, AWS Budget/Free-Plan alerts tính cả public IPv4/Elastic IP, stop-start origin-stability và no-cache API smoke, external backup cùng rollback ECR digest + S3 version tại `infra/aws/` và `docs/deployment-report.md`
- [ ] T097 [US5] Tổng hợp contribution evidence của 5 thành viên, checkpoint commits, slide/demo flow và bộ Q&A về giá trị, dữ liệu, model, chi phí, giới hạn, cloud và mở rộng tại `docs/team-contributions.md` và `docs/presentation-qa.md`
**Checkpoint**: CP7 chỉ đóng khi CI/security/cost/cloud pass; CP8 chỉ đóng khi rubric matrix không còn
tiêu chí thiếu owner/artifact và demo production + local rollback rehearsal đều đạt. CP2 không được
đóng trước T098–T099; hai task này chờ input quy ước chính thức từ lead.

---

## Phase 11: User Story 6 - Bản dịch trực tiếp và lịch sử 24 giờ (Priority: P2)

**Goal**: Nối các kết quả `accepted` thành dòng bản dịch trực tiếp và lưu lịch sử bản dịch trên trình
duyệt ít nhất 24 giờ (FR-034–FR-036, SC-016). Lead duyệt 2026-11-07. Không đổi API, không lưu server.

**Independent Test**: Fixture predictor: 2 `accepted` + 1 `rejected` → dòng bản dịch có đúng 2 chữ; tải lại
trang vẫn còn lịch sử; giả lập +24 giờ thì mục cũ bị xoá; bộ nhớ trình duyệt bị chặn vẫn nhận diện được.

- [X] T100 [P] [US6] Viết unit tests cho translation history store: lưu đúng 5 field, TTL 24 giờ bằng đồng hồ giả lập, bỏ dữ liệu sai schema, chống trùng `requestId`, `localStorage` ném lỗi/đầy, xoá toàn bộ tại `apps/web/tests/recognition/translationHistory.test.ts`
- [X] T101 [US6] Cài translation history store chỉ dùng `localStorage`, khoá có `schemaVersion`, tự xoá mục quá hạn khi đọc/ghi và không bao giờ lưu frame/landmark/video tại `apps/web/src/features/recognition/translationHistory.ts`
- [X] T102 [P] [US6] Viết component tests: dòng bản dịch chỉ nối kết quả `accepted` theo thứ tự, rejected/error không nối, nút xoá, thông báo lưu cục bộ và trạng thái lịch sử không khả dụng tại `apps/web/tests/recognition/transcript-history.test.tsx`
- [X] T103 [US6] Cài dòng bản dịch trực tiếp và panel lịch sử 24 giờ (thời điểm, độ tin cậy, `modelVersion`, nút xoá, `aria-live`, câu chữ trong `apps/web/src/content/vi.ts`) và nối vào `apps/web/src/App.tsx` tại `apps/web/src/features/recognition/TranscriptPanel.tsx` và `apps/web/src/features/recognition/HistoryPanel.tsx`
- [X] T104 [US6] Viết E2E fake-camera: 2 accepted + 1 rejected, reload giữ lịch sử, giả lập +24 giờ xoá mục cũ, xác nhận network không gửi lịch sử và storage không chứa video/landmark tại `apps/web/tests/browser/transcript-history.spec.ts`

**Checkpoint**: US6 chạy độc lập với fixture; không thay đổi API contract, không ảnh hưởng `demoReady`.
Reviewer: P1/Huy (spec, E2E) và P2/Tín (privacy: không có lịch sử gửi lên server).

### Dịch trực tiếp liên tục (lead quyết định 2026-11-08, FR-004 sửa)

**Owner**: P1/Huy (tiếp quản một phần việc của P3) · **Reviewer**: P5/Hiển (FE), P2/Tín (CSP/privacy)

- [ ] T105 [US6] Phát hiện người/mặt/tay trên trình duyệt bằng `@mediapipe/tasks-vision` 1.1.1 (hand + pose lite, WASM và model phục vụ cùng origin, SHA-256 cố định) và bộ cắt đoạn tự động theo chuyển động tay tại `apps/web/src/features/live/presenceDetector.ts`, `liveSegmenter.ts`, `apps/web/scripts/prepare-mediapipe.mjs`; CSP thêm `'wasm-unsafe-eval'`
- [ ] T106 [US6] Luồng dịch trực tiếp: tự ghi, tự gửi `/api/v1/predictions`, nối bản dịch, 11 trạng thái, Tạm dừng/Tiếp tục/Tắt camera, tự tạm dừng khi ẩn tab, giữ kết quả cuối đến ký hiệu kế tiếp tại `apps/web/src/features/live/useLiveRecognition.ts`, `LiveCamera.tsx`; bỏ giao diện quay thủ công
- [ ] T107 [P] [US6] Kiểm thử: unit bộ cắt đoạn, component luồng live (MediaRecorder/API/detector giả), Playwright camera giả với stub phát hiện (WebM thật, 3 viewport, axe), test MediaPipe thật nạp được, E2E 3 backend FastAPI thật tại `apps/web/tests/live/`, `tests/browser/`, `tests/accessibility/`, `tests/e2e/`
- [ ] T108 [US6] Smoke dịch trực tiếp trên bản deploy (HTTPS, webcam thật, CSP thật), đo thời gian từ khi tay dừng tới khi hiện chữ và ghi vào `docs/deployment-report.md`

---

## M1 Candidates — Không thuộc MVP commitment

Các mục dưới đây chỉ được mở khi Huy ghi trigger, owner và acceptance evidence. Chúng không chặn
`demoReady`, không nằm trên critical path và không được tính vào số task MVP còn lại.

- **M1-API-01 [P]**: Tự động sinh và kiểm tra drift TypeScript API types bằng `openapi-typescript` từ
  `specs/001-vsl-recognition-mvp/contracts/openapi.yaml`. **Trigger**: contract thay đổi thường xuyên,
  có client thứ hai hoặc lỗi drift thủ công xuất hiện. T027 vẫn cung cấp type tối thiểu cho MVP.

## M2 Candidates — Không thuộc backlog hiện tại

Không có task `T*` hiện tại cần chuyển sang M2. Endpoint landmark JSON, client-side extraction,
ONNX, DVC/MLflow và mở rộng vocabulary tiếp tục chỉ là decision backlog trong `plan.md`. Cloud/CI
đã được nâng thành commitment T091, T095–T096 do tiêu chí chấm điểm bắt buộc.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1**: Bắt đầu ngay.
- **Phase 2 / Integration track**: T019–T028 có thể hoàn thành với fixture contract, không phụ thuộc
  T013 hoặc full training.
- **Phase 2 / Contract freeze**: T009–T018 và T027/T040/T072–T075 không được đóng trước T098 data
  convention và T099 FE-BE API convention; AI–backend contract đã được Cường/Tín xác nhận.
- **Phase 2 / Data-model track**: T076 mở pilot; full track chờ T077 `p0.csv` đúng 10 meanings và
  T018/T056 split audit.
- **M0 gate**: Pilot dùng model thật chỉ mở sau khi T014–T017 chứng minh decoder/extractor/schema parity;
  fixture integration vẫn được phép chạy song song.
- **US1 / Fixture**: Bắt đầu sau integration foundation và model fixture; tạo luồng giá trị đầu tiên.
- **US1 / Pilot-Full**: Cường cần T013 pilot/full manifest, T014–T018 preprocessing/split và giữ cùng
  artifact contract đã dùng cho fixture.
- **US2**: Phụ thuộc prediction states/API shell của Phase 2; có thể bắt đầu song song phần lớn với US1.
- **US3**: Phụ thuộc manifest/split/model metadata của Phase 2; evaluation có thể song song với UI US1.
- **Phase 6**: Phụ thuộc các story được chọn cho demo; T070 phụ thuộc toàn bộ cổng bắt buộc.
- **Phase 8**: T076 có thể chạy từ bản bàn giao pilot; T077 phụ thuộc inventory/label audit.
- **Phase 9 / US4**: Có thể review/hợp nhất song song sau foundation; T083 phụ thuộc T076 và T078–T082.
- **Phase 10 / US5**: T085–T090/T093 có thể chuẩn bị song song; T091 chặn deploy, T095 chặn T096,
  và CP8/T097 phụ thuộc toàn bộ quality/cloud/evidence gates.

### User Story Dependencies

```text
Setup -> Foundation -> US1 -> Integration/Polish
                    \-> US2 -/
                    \-> US3 -/
                    \-> US4 (internal, non-release)
                    \-> US5 (rubric/cloud/evidence)
```

- **US1** không phụ thuộc data/full training để chạy happy path với fixture.
- **US2** dùng endpoint và state model chung nhưng kiểm thử được độc lập bằng low-confidence fixture.
- **US3** dùng model artifact chung nhưng kiểm thử được độc lập bằng metrics fixture.
- **US4** dùng AI/data pipeline nhưng có contract/auth riêng; không phụ thuộc để user MVP chạy.
- **US5** kiểm chứng toàn hệ thống; không thay thế US1–US4 mà thu evidence từ các story đó.
- Fixture/pilot/full dùng cùng contract; nâng cấp hoặc rollback artifact không tạo một user story hay
  frontend code path riêng.

### Parallel Opportunities

- T001–T007 do Tín chịu trách nhiệm chính; Cường review T003, Hiển review T004/T006. T002–T006 và
  T008 vẫn sửa file độc lập nên có thể làm song song.
- T009–T011, T014, T019–T021, T025, T027–T028 sửa các vùng độc lập.
- Sau integration foundation, Tín làm T030/T037–T038, Hiển làm T031/T039–T043 và Huy làm T032 bằng
  fixture; không chờ Quang hoặc Cường hoàn thành full track.
- Quang làm T013/T018/T056/T061/T076–T077 trong khi Cường làm T014–T017 rồi T029/T033–T036/T054/T057–T059.
- Trong US2, Tín làm T044–T045/T048–T050, Hiển làm T046/T051–T053 và Huy làm T047.
- US2 tests T044–T047 và US3 tests T054–T056 có thể chạy song song.
- T061–T063 và T068–T069 là các kiểm tra/tài liệu độc lập sau khi contract ổn định.
- Tín làm T078–T080, Hiển làm T081–T082; Cường/Quang cung cấp input cho T083 và Huy review T084.
- T085–T090/T093–T094 có thể làm local song song trên file riêng, nhưng mọi push `main` vẫn tuần tự
  theo `docs/team/git-checkpoints.md`; T095–T096 chỉ bắt đầu sau T091 quality gate.

## Parallel Example: User Story 1

```text
Cường/AI: T029 -> T033 -> T034 -> T035 -> T036
Tín/API:  T030 -> T037 -> T038
Hiển:     T031 -> T039 + T040 -> T041 -> T042 -> T043
Huy:      T032, sau đó điều phối kiểm tra luồng tích hợp
Quang:    T013 pilot subset -> T018, tiếp tục hoàn thiện full manifest
```

## Implementation Strategy

### MVP First

1. Lead duyệt CP0; nhóm chỉ sau đó mới commit/push Spec Kit baseline lên repo mới.
2. Hoàn thành CP1 toolchain, rồi đóng T098–T099 để mở CP2 foundation.
3. Dùng fixture cho CP3 camera → API v1 → UI và CP4 fail-closed/error/privacy paths.
4. Review representative clips, APPROVE schema v0.3, chạy offline↔API tensor/mask parity.
5. Quang hoàn thành T076; Cường train/evaluate pilot; Tín nạp gói qua `MODEL_ARTIFACT_PATH`.
6. Quang hoàn thành T077 video-held-out full manifest; Cường train/evaluate full và release metadata.
7. Hoàn thành CI/security/cost/community/cloud CP7; chỉ deploy commit đã qua quality gate.
8. Huy duyệt full `demoReady=true` và CP8 khi rubric, production smoke, rollback và presentation đạt.

### Team 5 người

- **P1 / Huy — Project/Task Manager**: quản lý scope, backlog, dependency, fallback trigger, checkpoint,
  integration queue, CI coordination, nghiệm thu, E2E và demo; không sở hữu implementation FE/BE/model.
- **P2 / Tín — Backend/API**: sở hữu domain/API, predictor integration, artifact configuration, cleanup,
  contract/integration tests, privacy, security, AWS và rollback vận hành.
- **P3 / Cường — Training Models**: sở hữu MediaPipe extraction/preprocessing, GRU pilot/full training,
  evaluation, release metadata, model card và performance benchmark.
- **P4 / Quang — Data Crawler/Data Analyst**: sở hữu nguồn/quyền sử dụng, lọc nhãn, pilot/full manifest,
  coverage, split leakage audit và dataset card.
- **P5 / Hiển — UX/UI/Frontend**: thiết kế trải nghiệm camera, trạng thái nhận diện, lỗi, accessibility và
  triển khai React frontend, gồm notice cho fixture/pilot dựa trên model-info.

## Notes

- Danh mục P0 đã chốt; T013 vẫn phụ thuộc việc lọc, bổ sung raw material và audit nguồn/quyền sử dụng
  trước khi tạo sample manifest cho pilot/full.
- Fixture mở khóa FE/BE/E2E nhưng không phải bằng chứng chất lượng model; pilot chỉ là smoke model và
  không được đổi thành `demoReady=true`.
- Chuyển artifact phải giữ nguyên API contract, kiểm tra feature schema và có đường rollback về
  artifact smoke-tested gần nhất.
- Không commit raw video, model binary hoặc dữ liệu không rõ quyền sử dụng.
- Không mở rộng lên 30 từ trước khi 10 từ P0 đạt cổng chất lượng.
- M1/M2 trong `plan.md` là decision backlog, không phải checkbox cam kết; chỉ `T*` trong file này là task.
- T063 được giữ mã lịch sử nhưng chuyển thành kiểm tra accessibility trong Phase 6 vì branch đã có
  test và yêu cầu frontend hiện trạng coi đây là phần cần nghiệm thu.
- Local work có thể song song nhưng push lên `main` phải tuần tự; không branch vai trò và không force-push.
- Release `0.0.1`, API namespace `v1`; feature schema v0.3 là version độc lập.
