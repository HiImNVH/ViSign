# CP4 T049 smoke evidence — kiểm clip tại ranh giới API

| Trường | Giá trị |
|---|---|
| Checkpoint/task | `CP4 / T049` — clip validation: MIME, byte limit, chữ ký WebM, probe giải mã, thời lượng PTS, người/landmark |
| Owner | `P2 Tín` |
| Reviewer | `P3 Cường` (quy tắc người/landmark, thời lượng PTS); `P1 Huy`; `P5 Hiển` (mã lỗi phía FE) |
| Candidate commit | `CP4 T049(api): validate clip type, signature, size and landmarks` |
| Commit | `PENDING` |
| Ngày/giờ | `2026-11-07T21:01+07:00` |
| Status | `PASS` local; đi cùng commit T037 adapter GRU (đóng lỗ hổng clip không người) |

## Phạm vi

| File | Nội dung |
|---|---|
| `inference/clip_validator.py` | Hàm kiểm thuần, mỗi lỗi dùng mã sẵn có trong catalog (không thêm mã mới, đúng D3) |
| `api/clip_upload_route.py` | `ClipUploadRoute` cho `/predictions`: kiểm `Content-Length` trước khi FastAPI parse multipart; `BoundedBodyReceive` đếm byte thực nhận để chặn request chunked; gỡ lỗi miền khỏi `HTTPException` 400 mà FastAPI bọc khi đọc form |
| `api/predictions.py` | Kiểm MIME → đọc có giới hạn → kiểm chữ ký, đều **trước** khi giữ slot và ghi clip tạm |
| `inference/feature_extraction.py` | Thêm `ptsSpanMs` (khoảng PTS đầu–cuối đã giải mã; số vô hướng, không phải landmark) |
| `inference/gru_predictor.py`, `main.py` | Adapter GRU kiểm clip sau trích đặc trưng, trước GRU; `GruRuntime.from_settings` lấy `VISIGN_MODEL_DIR` và `MIN/MAX_DURATION_MS` |

| Kiểm tra | Quy tắc | Mã |
|---|---|---|
| MIME | Chuẩn hóa (bỏ khoảng trắng, dấu nháy, chữ hoa) rồi so `ALLOWED_MIME_TYPES`; trước đây cấu hình này chưa có hiệu lực | 415 `UNSUPPORTED_MEDIA_TYPE` |
| Chữ ký WebM | EBML ở byte 0 và DocType `webm` trong 4096 byte đầu, cùng quy tắc `VideoDecoder` | 415 |
| Body | `Content-Length` > `MAX_CLIP_BYTES` + 64 KiB (phần bao multipart) → từ chối trước khi đọc body; chunked bị cắt khi vượt; clip > `MAX_CLIP_BYTES` → 413 như T038 | 413 `CLIP_TOO_LARGE`; header hỏng → 400 |
| Probe giải mã | `VideoDecoder` dùng chung: có stream video, VP8/VP9, PTS tăng, ≤ 900 frame, ≤ 4K | 415/422/400 qua bảng ánh xạ T037 |
| Thời lượng | Decoder chặn cứng 300–6000 ms; API thêm cửa sổ `MIN/MAX_DURATION_MS` trên PTS đã giải mã (trước đây cấu hình chưa có hiệu lực) | 422 `CLIP_TOO_SHORT`/`CLIP_TOO_LONG` |
| Người/landmark | `inputStatus = HAS_USABLE_FRAMES` (cùng quy tắc CLI T017) mới phân lớp; không có điểm tay/mặt/pose nào hợp lệ trong `point_valid` trước chuẩn hóa → không có người; có điểm nhưng không đủ vai + tay → thiếu landmark; trạng thái lạ coi là không dùng được (quy tắc P3, xem mục Đồng bộ) | 422 `NO_PERSON_DETECTED`/`INSUFFICIENT_LANDMARKS` |

Fixture không giải mã video nên chỉ chịu các kiểm tra trước slot (MIME, byte, chữ ký). Không thuộc phạm vi: body
multipart hỏng đang trả `{"detail": ...}` thay vì `ErrorEnvelope` (T050, commit kế tiếp); 404/405 (T072/T073).

## Pre-commit synchronization

- `origin/main...HEAD` = `0 1` tại `f1eb7ea` (chỉ commit T037 `e91bc2b` chưa push).

## Smoke

| Gate | Kết quả |
|---|---|
| Test-first RED | 2 collection errors + 7 failed. Test chunked ban đầu đã xanh vì `read_bounded_clip` cũng trả 413 → siết lại: parser multipart phải bị cắt giữa chừng, rồi mới đỏ đúng lý do |
| GREEN | 41 unit `clip_validator`, 16 unit `gru_predictor`, 13 unit `feature_extraction`, 21 contract `predictions` |
| Bắt hồi quy | 19/19 mutation bị bắt: bỏ chuẩn hóa chữ hoa, bỏ kiểm MIME, bỏ DocType, quét cả clip thay vì 4096 byte, giới hạn bao gồm, nhận chữ số Unicode, bỏ phần bao multipart, biên ngắn bao gồm, bỏ kiểm dài, bỏ điểm lẻ, coi trạng thái lạ là dùng được, GRU bỏ kiểm, runtime bỏ settings, không chép `ptsSpanMs`, endpoint bỏ MIME/chữ ký, route bỏ `Content-Length`, bộ đếm không dừng, giữ nguyên 400 bọc ngoài |
| Toàn bộ API + contract | Extra `serving`: 311 passed, 1 skipped. Môi trường như CI: 298 passed, 2 skipped. Ruff, format, mypy 51 files |
| Live uvicorn (artifact pilot T036, `Origin: http://localhost:5173`) | Clip VP8 không người: trước T049 trả "Cảm ơn" `accepted=true`, nay **422 `NO_PERSON_DETECTED`**; MIME `video/mp4` → 415; byte MP4 gắn nhãn `video/webm` → 415; mọi lỗi có `access-control-allow-origin` và `requestId` khớp header. Socket thô khai `Content-Length: 10 GiB`, chỉ gửi header + 5 byte → `413` sau 14 ms, có `x-request-id`. 0 file `visign_clip_*` còn lại |

## Đồng bộ quy tắc P3 (commit tiếp theo)

P3 chốt quy tắc T049 lúc `21:02` trong `CP3/T037-p2-tin-serving-feature-smoke.md`, cùng lúc bản đầu được commit. Bản đầu
suy "không có người" từ `groupMask`/`tensorMask` sau chuẩn hóa, nên người lọt khung mà thiếu vai (không chuẩn hóa được)
có thể bị báo nhầm `NO_PERSON_DETECTED`. Commit `CP4 T049(api): use pre-normalization points for no-person rule`:

- `ExtractedFeatures.detectedAnyLandmark` = `point_valid.any()` của pipeline (chỉ giữ cờ, không giữ mảng điểm).
- Test theo ba ca P3 yêu cầu: clip trống → `NO_PERSON_DETECTED`; có điểm (kể cả chỉ một điểm, thiếu vai/tay) →
  `INSUFFICIENT_LANDMARKS`; đủ landmark → phân lớp. Mask đủ mà cờ `false` vẫn là không có người.
- 4/4 mutation bị bắt (quy tắc mask cũ, `.all()` thay `.any()`, cờ luôn `true`, không bao giờ trả `NO_PERSON_DETECTED`).
- Toàn bộ API + contract (extra `serving`) 345 passed, 1 skipped; live: clip VP8 không người vẫn 422 `NO_PERSON_DETECTED`.

## Handoff

- Cường: xác nhận bản đã áp quy tắc P3 (cờ `point_valid` trước chuẩn hóa) và việc API dùng `ptsSpanMs` của report
  làm thời lượng.
- Hiển: không có mã lỗi mới; FE nhận 415/413/422 theo catalog hiện có.
- Huy: nên đưa clip không người vào kịch bản E2E/T064 làm ca âm tính.

**Reviewer result**: `PENDING`
