# CP4 T045/T050 smoke evidence — contract lỗi và dọn dẹp của endpoint dự đoán

| Trường | Giá trị |
|---|---|
| Checkpoint/task | `CP4 / T045` (mở rộng contract test lỗi); `T050` (hoàn thiện ánh xạ lỗi và dọn dẹp) |
| Owner | `P2 Tín` |
| Reviewer | `P1 Huy`; `P5 Hiển` (FE đọc `ErrorEnvelope`, `X-Request-ID`, `Retry-After` qua CORS) |
| Candidate commit | `CP4 T045,T050(api): extend error contract tests and harden cleanup` |
| Commit | `PENDING` |
| Ngày/giờ | `2026-11-07T21:20+07:00` |
| Status | `PASS` local |

## Phát hiện và sửa (T050)

1. **Body multipart hỏng lộ `{"detail": ...}`**: thiếu boundary làm Starlette ném `HTTPException` 400 và FastAPI trả
   `{"detail": "Missing boundary in multipart."}`, lệch `ErrorEnvelope`. `ClipUploadRoute` nay đổi mọi lỗi parse body
   400 thành `INVALID_REQUEST` (envelope + `requestId`).
2. **Hủy request bỏ rơi worker**: probe cho thấy `run_in_threadpool` chỉ hoãn được hủy kiểu anyio (cancel scope/task
   group), còn hủy thuần `task.cancel()` (ví dụ uvicorn hủy task khi tắt máy quá hạn) làm request rời slot ngay trong khi
   thread vẫn chạy. Hậu quả: slot trả sớm nên có thể có 2 lượt suy luận song song (vượt RAM); clip tạm bị xóa khi worker
   còn đọc (Windows không xóa được → clip nằm lại trên đĩa). `inference/worker_thread.py` (`run_to_completion`) dùng
   `asyncio.shield` và chờ worker trong scope anyio được che chắn: cả hai kiểu hủy chỉ lan truyền sau khi thread xong.
   Lỗi của worker sau khi hủy được đọc ra để asyncio không log "never retrieved".

## Contract test mở rộng (T045)

| Nhóm | Nội dung |
|---|---|
| Catalog | Cả 11 `ErrorCode` khi predictor ném: đúng status, body đúng `{code, message, requestId}` theo catalog, `Content-Type` JSON, `Retry-After` chỉ có ở `SERVICE_BUSY` (3) và `MODEL_NOT_READY` (5), clip tạm luôn bị xóa |
| Body hỏng | Thiếu boundary và part bị cắt cụt → 400 `INVALID_REQUEST` |
| `X-Request-ID` | 9 kịch bản (200 accepted, 200 rejected, 400 thiếu clip, 400 body hỏng, 413, 415, 422, 500, 503): header là UUID và trùng `requestId` trong body; ID hợp lệ của client được echo trên response lỗi, ID sai định dạng được thay bằng UUID mới |
| CORS | Response 415 và 503 cho origin Vite có `access-control-allow-origin` và expose `X-Request-ID`, `Retry-After` |
| Đã có từ T038/T049 | 413 (clip, `Content-Length`, chunked), 415 (MIME, chữ ký), `CLIP_DECODE_FAILED`, `SERVICE_BUSY` đồng thời thật, `MODEL_NOT_READY`, `PREDICTION_FAILED` không lộ exception, low-confidence 200 |

Không thuộc phạm vi: 404/405 vẫn là `{"detail"}` mặc định (T072/T073, cần thống nhất mã với P5 theo D3).

## Pre-commit synchronization

- Trước commit: remote có review T019 (`989533e`) và T037 parity/GRU handoff (`1b14f1e`) của P3, chỉ chạm evidence/README;
  stash → `pull --rebase` (T037 `e91bc2b` → `23ed5b1`, T049 `99d3c64` → `4c9fdb9`) → apply, hash 7 path khớp rồi mới
  drop stash; gate chạy lại đạt.
- `origin/main...HEAD` = `0 2` tại `1b14f1e`.

## Smoke

| Gate | Kết quả |
|---|---|
| Test-first RED | 3 failed đúng lý do: body thiếu boundary trả `{"detail"}`; kịch bản `X-Request-ID` của body hỏng; hủy thuần làm request rời sớm, xóa clip và trả slot khi worker còn chạy. Ma trận catalog và CORS xanh ngay (khóa hồi quy cho hành vi sẵn có) |
| GREEN | 46 contract `predictions` (+25), 5 unit `worker_thread`, 1 unit dọn dẹp endpoint |
| Bắt hồi quy | 6/6 mutation bị bắt: bỏ `asyncio.shield`, bỏ chờ worker sau khi hủy, bỏ scope anyio che chắn (đỏ biến thể hủy kiểu anyio), không đọc lỗi worker, endpoint quay lại `run_in_threadpool`, giữ 400 `{"detail"}` |
| Toàn bộ API + contract | Môi trường như CI: 329 passed, 2 skipped ×3 lần. Extra `serving`: 342 passed, 1 skipped; parity offline ↔ API trên clip VP8/VP9 tổng hợp đạt. Ruff, format, mypy 54 files |
| Live uvicorn (fixture) | Multipart thiếu boundary → 400, body chỉ có `code`, `message`, `requestId` khớp header; clip hợp lệ → 200; `X-Request-ID: khong-phai-uuid` → UUID mới, khớp body; 0 file `visign_clip_*` còn lại |

## Rủi ro còn lại

- Tiến trình bị giết cứng (OOM killer/`SIGKILL`, `TerminateProcess`) giữa lúc suy luận không chạy `finally`, nên clip tạm
  còn trong thư mục tạm. Đề xuất cho T066/T095: dọn `visign_clip_*` cũ khi khởi động và đặt giới hạn bộ nhớ đủ để tránh OOM.

**Reviewer result**: `PENDING`
