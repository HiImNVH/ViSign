# CP3 T030/T038 smoke evidence — endpoint dự đoán với fixture

| Trường | Giá trị |
|---|---|
| Checkpoint/task | `CP3 / T038` (endpoint); `T030` (contract test fixture HTTP) — theo P1 "tiếp T038/T060 endpoint để mở E2E" |
| Owner | `P2 Tín` |
| Reviewer | `P1 Huy` (E2E T032); `P5 Hiển` (client T040); `P3 Cường` (đường predictor) |
| Candidate commit | `CP3 T030,T038(api): add prediction endpoint with fixture contract tests` |
| Commit | `bfeee4d1213300f4cf20edc8af63b248e5dbcc45` — [bfeee4d](https://github.com/HiImNVH/ViSign/commit/bfeee4d1213300f4cf20edc8af63b248e5dbcc45); CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42375491322) |
| Ngày/giờ | `2026-11-07T20:06+07:00` |
| Status | `PASS` local và CI; chờ reviewer verify |

## Phạm vi

`api/predictions.py` — `POST /api/v1/predictions` (multipart, đúng một field `clip`):

1. Đọc tối đa `MAX_CLIP_BYTES + 1` byte: vượt → 413 `CLIP_TOO_LARGE` trước khi suy luận; rỗng/thiếu → 400 `INVALID_REQUEST`.
2. Chưa có predictor → 503 `MODEL_NOT_READY` ngay, không chờ slot.
3. Giữ slot `InferenceCoordinator` (hết chờ → 503 `SERVICE_BUSY`, `Retry-After: 3`); trong slot ghi clip tạm và chạy
   `predictor.predict` bằng threadpool (event loop không bị chặn, slot giữ tới khi thread xong); clip tạm luôn bị xóa.
4. Áp `decide_prediction` (T048) với `acceptanceThreshold` của artifact; trả `PredictionResponse` (`processingTimeMs` từ
   lúc nhận request); log một dòng gồm `requestId`, `modelVersion`, `processingTimeMs`, `timingsMs`, `accepted` (không có
   `classLabel`/chữ/clip).

Không thuộc phạm vi: MIME allowlist chuẩn hóa và chặn theo `Content-Length` trước khi parse multipart (T049), quy tắc
`INSUFFICIENT_LANDMARKS` từ `inputStatus` (T049), predictor GRU (T037 + T036 của P3).

## Pre-commit synchronization

- `git fetch`; `origin/main...HEAD` = `0 2` (chỉ hai commit T044/T048, T055/T060 chưa push) trên `15384cc` (T036 của P3).
- Ghi chú quy trình: commit T055/T060 ban đầu được tạo khi remote đã có `15384cc` (`1 1`), trái cổng "không commit khi
  chậm hơn `origin/main`". Đã `git pull --rebase` trước bất kỳ push nào (rebase sạch, không trùng file) và chạy lại gate:
  196 passed; test quét mã lỗi 15 passed; AI 55 passed.

## Smoke

| Gate | Kết quả |
|---|---|
| Test-first RED | 15 failed (endpoint chưa có) sau khi sửa import `httpx` → `httpx2` trong test |
| GREEN | 15 passed: fixture chấp nhận đủ field + diagnostics hợp lệ; `X-Request-ID` echo/tự sinh; low-confidence → 200 `accepted=false`, "Không nhận diện được"; mọi artifact kind cùng schema; diagnostics vắng bị bỏ; thiếu field/clip rỗng/field text → 400; quá giới hạn → 413, không gọi predictor; không model → 503 + `Retry-After: 5`; clip tạm tồn tại trong lúc suy luận với đúng byte và bị xóa sau; lỗi domain giữ 422 và dọn clip; lỗi bất ngờ → 500 không lộ path/traceback; hai request đồng thời thật → 503 `SERVICE_BUSY` + `Retry-After: 3`, request đầu 200 |
| Bắt hồi quy | Bỏ ngưỡng → 1 failed; đọc cả body không giới hạn → 1 failed; gọi `predict` trên event loop → test busy failed (request thứ hai bị chặn ~20 s); khôi phục giống hệt |
| Toàn bộ API + contract | 211 passed, 1 skipped ×3 `-W error`; Ruff, format, mypy (45 files) |
| Live uvicorn | Fixture: 200 `Cảm ơn`, `x-request-id` echo, `access-control-allow-origin: http://127.0.0.1:5173`, `access-control-expose-headers: X-Request-ID, Retry-After`; low-confidence 200 rejected; thiếu clip 400; `MAX_CLIP_BYTES=8` → 413; không model → 503 + `retry-after: 5`; 0 file `visign_clip_*` còn lại trong thư mục tạm |

Ghi chú: lần smoke đầu dùng curl Windows với đường dẫn `/tmp` của Git Bash nên curl không đọc được file (lỗi 26) và
trả rỗng/`000`; chạy lại với đường dẫn Windows trong scratchpad thì đạt như bảng trên.

Chạy local cho FE/E2E:

```bash
MODEL_ARTIFACT_PATH=services/inference-api/tests/fixtures/model-artifacts/fixture \
  uv run --project services/inference-api uvicorn visign_api.main:app --host 127.0.0.1 --port 8000
```

**Reviewer result**: `PENDING`
