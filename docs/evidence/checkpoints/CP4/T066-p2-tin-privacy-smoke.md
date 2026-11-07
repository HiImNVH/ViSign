# CP4 T066 smoke evidence — audit quyền riêng tư của đường dự đoán

| Trường | Giá trị |
|---|---|
| Checkpoint/task | `CP4 / T066` — chứng minh không có video/frame/PII trong log hay file do API để lại (FR-011, FR-019) |
| Owner | `P2 Tín` |
| Reviewer | `P1 Huy`; `P3 Cường` (artifact model) |
| Candidate commit | `CP4 T066(security): audit prediction privacy and sweep stale clips` |
| Commit | `961f59d7ef1465ac3146a8c5d481ffe2da496183` — [961f59d](https://github.com/HiImNVH/ViSign/commit/961f59d7ef1465ac3146a8c5d481ffe2da496183); CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42388018420) |
| Ngày/giờ | `2026-11-07T22:43+07:00` |
| Status | `PASS` local và CI |

## Phạm vi

| File | Nội dung |
|---|---|
| `tests/integration/test_prediction_privacy.py` | Audit chạy 10 kịch bản (200 accepted/rejected, model-info, 400, 404, 405, 413, 415, 422, 500) với clip chứa chuỗi đánh dấu, tên file chứa họ tên/số điện thoại giả, header `Authorization` và cookie; thư mục tạm riêng để đếm mọi file API ghi |
| `inference/temporary_clip.py` | `sweep_stale_clips`: xóa `visign_clip_*.webm` cũ hơn 15 phút (tiến trình bị giết cứng không chạy `finally`); giữ clip mới của request đang chạy; log chỉ ghi số lượng |
| `main.py` | Gọi dọn clip cũ khi khởi động, trước khi nhận request |
| `tests/unit/test_temporary_clip.py` | 4 test: xóa clip quá hạn, giữ clip mới, bỏ qua file không đúng tên, log không có đường dẫn |

| Khẳng định | Kết quả |
|---|---|
| Log chỉ dùng field allowlist | Mọi dòng JSON chỉ có `timestamp/level/logger/message/exception` và field trong `ALLOWED_CONTEXT_KEYS` |
| Log không chứa dữ liệu riêng tư | Không có nội dung clip, tên file upload, họ tên, số điện thoại, token, cookie, đường dẫn clip tạm, chữ dịch (`Cảm ơn`, `Sốt`, cả dạng `\uXXXX`) hay nhãn lớp |
| Không để lại file | Sau 10 kịch bản, thư mục tạm của API trống: clip tạm và file spool multipart đều bị xóa, kể cả khi lỗi |
| Clip của tiến trình chết | Clip cũ hơn ngưỡng bị xóa khi khởi động; clip mới được giữ |
| Response | Không có landmark/frame (chẩn đoán chỉ là số), không lặp lại nội dung clip hay tên file; model-info không lộ đường dẫn artifact |

Giới hạn: traceback của lỗi bất ngờ vẫn được log (field `exception`) để vận hành; nội dung do code tự đặt, không chứa clip
hay landmark. Audit artifact model (provenance, sampleId) thuộc T058/T059 của P3. `tests/integration/` mới, job API của CI
chưa chạy thư mục này: đề xuất P1 thêm `tests/integration` vào lệnh pytest của job `api` trong `quality.yml`.

## Pre-commit synchronization

- `origin/main...HEAD` = `0 0` tại `cf44cd6` trước khi sửa (cùng đợt với T072/T073, chưa commit).
- Trước commit: pull T051/T052 của P5, T083 và review T052/T065 của P1, T065 của P3 (không trùng file); gate chạy lại: API + contract + integration 372 passed, 2 skipped; web lint, typecheck, Vitest 122/122.
- `origin/main...HEAD` = `0 0` tại `cfa9f04`.

## Smoke

| Gate | Kết quả |
|---|---|
| Test-first RED | 2 lỗi import (`STALE_CLIP_AGE_SECONDS`, `sweep_stale_clips` chưa có) |
| GREEN | 17 test audit + 11 test `temporary_clip` |
| Bắt hồi quy | 6/6 mutation rò rỉ bị bắt: log chữ dịch, log tên file upload, log header `Authorization`, không xóa clip tạm, không gọi dọn khi khởi động, dọn cả clip mới |
| Toàn bộ | API + contract + integration (như CI): 372 passed, 2 skipped. Ruff, format, mypy 57 files (gồm `tests/integration`) |
| Live uvicorn (fixture) | Clip giả 20 phút trong thư mục tạm hệ thống bị xóa khi khởi động, clip 5 giây được giữ; log "Da don 1 clip tam con sot tu tien trinh truoc" không có đường dẫn; 200/415/404; log thật không chứa chuỗi đánh dấu, tên file, số điện thoại, token, `visign_clip_` hay chữ dịch; 0 file `visign_clip_*` còn lại |

**Reviewer result**: `PENDING`

## Independent review — P1/Huy

Review `2026-11-07T23:12:53+07:00` trên `28de816` (theo uỷ quyền của Huy). Gate: API + contract + integration 372 passed, 2 skipped; web lint, typecheck, Vitest 129/129; CI `quality.yml` xanh.

`test_prediction_privacy.py` (10 kịch bản) nằm trong bộ 372 test đạt. `sweep_stale_clips` chạy một lần khi
khởi động, chỉ khớp `visign_clip_*.webm` và chỉ xoá file cũ hơn 15 phút → không đụng clip của request
đang chạy; lỗi stat khi file vừa bị xoá được bỏ qua.

**Reviewer result**: `P1_VERIFIED` → T066 `[X]`.
