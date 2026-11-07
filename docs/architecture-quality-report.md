# ViSign · Báo cáo chất lượng kiến trúc (T090)

**Trạng thái**: bản đầu 2026-11-08 trên `origin/main` `9916831`, phụ trách P1/Huy (trợ lý soạn theo uỷ quyền),
đồng phụ trách P5/Hiển (phần FE cần P5 xác nhận/bổ sung). Mọi số liệu đo trực tiếp trên repo.

## 1. Cấu trúc module

| Module | Vai trò | Kích thước lớn nhất | Test |
|---|---|---|---|
| `apps/web` | React/TS/Vite: camera, kết quả, lỗi, bản dịch + lịch sử 24 giờ | `useRecognition.ts` 216 dòng | 20 file (Vitest, Playwright, E2E) |
| `services/inference-api` | FastAPI `/api/v1`, registry fixture/pilot/full, kiểm clip, lỗi, bảo mật | `gru_predictor.py` 254 dòng | 25 file |
| `ai` | Decode → MediaPipe → tensor 32×234 → GRU; train/eval/gate/benchmark | `train.py` 278 dòng | 9 file |
| `tests/` | contract, integration, security xuyên module | — | 6 file |

Không file nguồn nào vượt ~280 dòng; trách nhiệm tách theo thư mục `domain/`, `api/`, `inference/`
(backend) và `landmarks/`, `training/`, `evaluation/` (AI).

## 2. Chiều phụ thuộc

```text
apps/web ──HTTP (OpenAPI v1)──▶ services/inference-api ──import (extra "serving")──▶ ai (visign_ai)
```

- `ai` **không** import `visign_api` → AI dùng độc lập cho train/eval.
- API chỉ phụ thuộc `visign_ai` khi cài extra `serving` (6 module trong `inference/` + `config.py`); bản
  fixture chạy không cần torch/MediaPipe → CI nhẹ.
- Web không import code ngoài `apps/web`; hợp đồng FE–BE giữ bằng `openapi.yaml` + type viết tay + drift test.

**Đánh giá**: một chiều, không vòng; đúng nguyên tắc "train và API dùng cùng pipeline" mà không trộn module.

## 3. Quy ước code

| Hạng mục | Hiện trạng |
|---|---|
| Lint/type | Ruff + mypy (Python), ESLint + `tsc` (web) chạy trong CI trên mọi push |
| Format | 96/97 file Python đúng `ruff format`; còn `ai/src/visign_ai/evaluation/metrics.py`. CI **chưa** chạy `ruff format --check` |
| Comment | Python dùng tiếng Việt không dấu (ASCII-safe cho console Windows); docs tiếng Việt có dấu |
| Commit | `CPx Txxx(scope): ...`, evidence theo checkpoint, CI xanh trước khi đánh `[X]` |

## 4. Trùng lặp

| Chỗ trùng | Vị trí | Rủi ro | Đề xuất |
|---|---|---|---|
| Giới hạn clip 10 MiB / 300–6000 ms | `services/inference-api/.../config.py`, `ai/.../video_decoder.py`, `apps/web/.../cameraSession.ts` | Sửa một nơi thì lệch nơi khác | Lấy từ một nguồn (hằng số trong `visign_ai` cho API; test so giá trị web với OpenAPI/config) |
| Kiểm chữ ký WebM (EBML) | `clip_validator.py` (API, kiểm sớm trước decoder) và `video_decoder.py` (AI) | Hai quy tắc có thể lệch | API import hằng số/hàm kiểm từ `visign_ai` hoặc thêm test so khớp hai quy tắc |
| Type TS và schema OpenAPI | `apps/web/src/types/inference-api.ts` | Đã được drift test khoá (T099) | Giữ nguyên trong MVP (D4) |

## 5. Khả năng mở rộng

| Hướng | Mức sẵn sàng |
|---|---|
| Thêm nghĩa/biến thể | Qua class map + train lại; API/FE không đổi code trong giới hạn **≤ 10 nghĩa** của contract MVP (`inferenceApi.ts` chặn `meanings.length <= 10`); vượt 10 phải đổi contract + guard |
| Đổi artifact fixture/pilot/full | Đổi `MODEL_ARTIFACT_PATH` + khởi động lại; đã test chuỗi đổi và rollback (T064) |
| Thay mô hình (ngoài GRU) | Registry theo `artifactKind`; cần factory mới cho kiến trúc khác |
| Nhiều worker/instance | Hiện một inference slot mỗi tiến trình; mở rộng ngang cần thêm instance (ngoài MVP) |
| Latency | Nút thắt ở MediaPipe (p50 ~4,6 s), không ở kiến trúc API/GRU |

## 6. Hành động đề xuất

| # | Hành động | Owner | Ưu tiên |
|---|---|---|---|
| 1 | Gom giới hạn clip về một nguồn + test đồng bộ web/API/AI | P2 + P3 | Trung bình |
| 2 | API dùng chung quy tắc kiểm WebM với `visign_ai` | P2 | Thấp |
| 3 | Thêm `ruff format --check` vào CI sau khi format `metrics.py` | P1 (T091) + P3 | Thấp |
| 4 | Root mypy đang `follow_imports = "skip"` → kiểu dữ liệu giữa package không được kiểm; cân nhắc bật `normal` cho `visign_api` ↔ `visign_ai` | P1 + P2 | Trung bình |
| 5 | CI chưa có job Playwright/E2E (camera giả + backend thật chạy local bằng `npm run test:e2e`) | P1 (T091) | Trung bình |
| 6 | Giữ detector MediaPipe giữa request để đạt SC-002 | P3 | Cao |

## 7. Phần FE cần P5 bổ sung

### 7.1. Review frontend của P5/Hiển (2026-11-08)

**Phạm vi**: `apps/web/src/` và các test FE hiện có trên `main` tại `a214a3c` (sau khi đồng bộ
origin). Review tĩnh mã nguồn, đối chiếu component đang dùng và test; không thay đổi hành vi ứng dụng.

**Ranh giới và chiều phụ thuộc FE**:

```text
App (composition)
 ├─ useRecognition (camera + model metadata + prediction + transcript/history orchestration)
 │   ├─ useCameraCapture → cameraSession (MediaRecorder, clip lifecycle)
 │   ├─ services/inferenceApi (HTTP + runtime response guards)
 │   └─ translationHistory (localStorage, metadata only, TTL 24 giờ)
 └─ CameraRecorder / HistoryPanel / CameraHelp
      └─ RecognitionResult / RecognitionError / TranscriptPanel (presentation)
```

- **Điểm đạt**: `App.tsx` chỉ ghép UI và hook; transport không nằm trong component; camera được quản lý
  riêng ở `cameraSession.ts` / `useCameraCapture.ts`; `useRecognition.ts` dùng `AbortController`,
  generation và capture identity để chặn phản hồi muộn hoặc không còn khớp clip. Các trạng thái
  accepted/rejected và version được kiểm tra trước khi hiển thị ở `RecognitionResult.tsx`.
  Không cần thêm global state library cho phạm vi MVP hiện tại.
- **State**: `useRecognition.ts` (~216 dòng) còn gộp orchestration camera, metadata, prediction,
  transcript và lưu lịch sử. Điều này chấp nhận được với một màn hình, nhưng cần chia contract
  state/actions trước khi thêm admin UI hoặc nhiều màn hình dùng chung.
- **UI/CSS**: `styles.css` đã có style nút chung và class cho viewport/overlay; nội dung tiếng Việt
  chính nằm trong `content/vi.ts`. Chưa có convention tách component style/variant chặt chẽ;
  `.help-dialog` còn được dùng bởi lịch sử, và `CameraRecorder.tsx` tìm target focus bằng selector CSS.

### 7.2. Phát hiện và hành động FE

| ID | Mức | Bằng chứng cụ thể | Ảnh hưởng / hành động tiếp theo | Owner |
|---|---|---|---|---|
| FE-T090-01 | **Trung bình; xác nhận theo luồng code** | `translationHistory.ts:37-64` bắt lỗi của cả `getItem`, parse và ghi cleanup chung một `try/catch`. Khi dữ liệu đọc được nhưng `setItem`/`removeItem` trong cleanup ném lỗi, kết quả bị thay bằng `entries: []`. `HistoryPanel.tsx:45` chỉ hiện nút xóa khi danh sách có mục. | Tách đọc/parse khỏi cleanup; giữ các entry đã đọc khi ghi thất bại, gắn `available=false`, và bảo đảm người dùng vẫn thử xóa được dữ liệu tồn dư. Viết test quota/cleanup/remove lỗi. | P5 |
| FE-T090-02 | **Trung bình; rủi ro suy ra, chưa tái hiện đa tab** | `translationHistory.ts:69-81` lưu nguyên danh sách theo chu kỳ read–modify–write; `useRecognition.ts:125-135` chỉ refresh sau action cục bộ, không có đồng bộ `storage` giữa tab. | Xác định semantics multi-tab, test append/clear cạnh tranh trước khi chọn đồng bộ; tránh cam kết nhất quán giữa tab khi chưa có giải pháp. | P5 |
| FE-T090-03 | **Trung bình; nợ cấu trúc** | `CameraRecorder.tsx:10-14` và `HistoryPanel.tsx:5` lấy props từ `ReturnType<typeof useRecognition>`; `CameraRecorder` nhận `camera.session` qua controller, có `Partial` để giữ fixture cũ; `useRecognition.ts:112-117` xử lý session bị gọi trực tiếp. | Định nghĩa interface view/actions độc lập từ hook và dồn mutation camera qua controller; giữ regression abort/cancel/reset/focus khi tách. | P5 |
| FE-T090-04 | **Trung bình; trùng logic/test fidelity** | `RecognitionOverlay.tsx:10-17` trùng validation/markup một phần với `RecognitionResult.tsx:13-43`, nhưng không kiểm metadata/model notice; app thực tế dùng `RecognitionResult` ở `CameraRecorder.tsx:73`. Một trường hợp ở `tests/browser/camera.spec.ts` dựng HTML overlay riêng để thử viewport. | Bỏ/cô lập UI cũ sau khi di chuyển test sang response fixture qua API và component production; đảm bảo test xanh có nghĩa luồng thật xanh. | P5 |
| FE-T090-05 | **Trung bình khi session dài; chưa benchmark** | `useRecognition.ts:183` nối transcript không có giới hạn số mục, `TranscriptPanel.tsx:8` ghép và `aria-live` toàn bộ chuỗi, `HistoryPanel.tsx:38` render mọi entry; history ghi lại toàn bộ JSON. | Benchmark với nhiều kết quả, đo DOM/quota/announce trước khi quyết định phân trang hoặc virtualize. **Không tự xóa** dữ liệu còn trong TTL 24 giờ. | P5 |
| FE-T090-06 | **Thấp** | `CameraRecorder.tsx:62,79` tìm focus bằng selector CSS; `HistoryPanel.tsx:30` tái dùng `.help-dialog`; `CameraHelp.tsx:23` hard-code thời gian 5 giây. | Đổi focus target sang ref, làm tên style dialog trung tính và gom copy/giới hạn hiển thị về chỗ có test đồng bộ. | P5 |

**Thứ tự xử lý**: FE-T090-01 (mất khả năng đọc/xóa lịch sử khi cleanup lỗi) →
FE-T090-02 (quy định nhất quán multi-tab) → FE-T090-03/04 (component boundaries và test fidelity)
→ đo FE-T090-05 → sửa FE-T090-06. Mỗi fix là micro-commit FE riêng kèm test/evidence;
T090 ban đầu chỉ ghi review và hành động. Kết quả triển khai tiếp theo ghi tại §7.3.

**Giới hạn của kết luận**: chưa đo hiệu năng session dài, chưa tái hiện đồng thời hai tab và chưa
kiểm trên camera/screen reader thật. Các mục được đánh dấu "rủi ro suy ra" không phải lỗi runtime đã
chứng minh. Đã có unit/browser regression cho camera, nhưng không coi test mock là chứng cứ cho
thiết bị thật. Bàn giao P1/P2 review độc lập trước khi đánh T090 `[X]`.

**Đối chiếu bản đầu cần P1 xác nhận**: bản đầu ở mục 1 ghi 17 file test web, trong khi phép đếm
`*.test.*` / `*.spec.*` dưới `apps/web/tests` ngày 2026-11-08 cho **20 file**. Mục 5 về "thêm nghĩa
không đổi FE" chỉ áp dụng trong contract MVP tối đa **10 nghĩa** hiện được chặn tại
`apps/web/src/services/inferenceApi.ts:54`; tăng qua 10 cần thống nhất lại contract và runtime guard.
Chi tiết gate của P5: `docs/evidence/checkpoints/CP7/T090-p5-hien-smoke.md`.

### 7.3. Follow-up FE-T090-01..06 (P5, 2026-11-08)

| ID | Thay đổi đã triển khai | Regression / phạm vi xác nhận |
|---|---|---|
| FE-T090-01 | Tách lỗi đọc localStorage khỏi lỗi cleanup; giữ entry hợp lệ khi dọn dẹp thất bại; lịch sử vẫn cho phép thao tác xoá khi storage không khả dụng, kể cả danh sách hiển thị rỗng. | Vitest quota, remove, dữ liệu không đọc được và thử xoá lại sau khi storage hồi phục. |
| FE-T090-02 | Nghe `storage` event để cập nhật lịch sử đang mở trên các tab; khi tab khác xoá, huỷ request chờ và reset transcript trước khi response muộn có thể ghi lại. | Unit test append/clear khi submit đang chạy; browser 2 tab trên desktop, mobile, landscape. **Giới hạn:** hai append đồng thời vẫn có thể mất cập nhật do ghi đè read–modify–write; localStorage không bảo đảm giao dịch đa tab. |
| FE-T090-03 | Tách `CameraController` / `HistoryController` / `RecognitionController` khỏi hook, component nhận view và actions; `camera.session` nằm trong hook. | Unit regression huỷ, reset, capture identity, response đến muộn; accessibility focus trên 3 viewport. |
| FE-T090-04 | Loại `RecognitionOverlay` không dùng; browser test dựng camera thật qua capture và API fixture, hiển thị `RecognitionResult` production. | Browser kiểm soát trình bày accepted/pilot và viewport 320×180. |
| FE-T090-05 | History hiển thị từng 50 entry và nạp thêm theo yêu cầu; transcript hiển thị 30 mục cuối, `aria-live` chỉ phát mục mới, giữ nguyên toàn bộ metadata trong TTL 24h. | Vitest transcript 100/1.200 phần tử; Playwright seed 1.200 entry, 50→100 DOM row, không mất dữ liệu, payload fixture < 500 KB. Đây là số liệu fixture, chưa phải benchmark thiết bị thật. |
| FE-T090-06 | Focus chuyển qua ref của button còn khả dụng; dialog dùng class trung tính `app-dialog`; copy hướng dẫn dùng `captureLimits.maximumCaptureMs` từ camera session. | Accessibility keyboard, dialog, reconnect và layout trong Playwright. |

Tất cả thay đổi được kiểm qua lint, typecheck, unit, build và browser gate ở
`docs/evidence/checkpoints/CP7/T090-p5-fixes.md`. Không tuyên bố đạt mức an toàn đồng bộ append
tranh chấp hoặc đã kiểm thử camera/screen reader thật. Checkpoint review kiến trúc T090 trước đó
vẫn là tài liệu lịch sử độc lập.
