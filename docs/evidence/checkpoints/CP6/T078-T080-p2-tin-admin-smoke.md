# CP6 T078–T080 evidence — API công cụ admin nội bộ (inspect, pilot job)

| Trường | Giá trị |
|---|---|
| Checkpoint/task | `CP6 / T078–T080` — test backend admin, cấu hình opt-in, lỗi đã làm sạch, vòng đời inspect tạm, khóa job; đồng bộ `contracts/admin-tools.md` |
| Owner | `P2 Tín` |
| Reviewer | `P1 Huy`; `P5 Hiển` (smoke T082 với backend thật); `P3 Cường` (giao diện runner pilot) |
| Candidate commit | `CP6 T078-T080(api): add opt-in admin inspect and single-job pilot API` |
| Commit | `PENDING` |
| Ngày/giờ | `2026-11-08T04:52+07:00` |
| Status | `PASS` local; chờ CI |

## Phạm vi

| File | Nội dung |
|---|---|
| `config.py` | `VISIGN_ADMIN_TOKEN` (`SecretStr`, ít nhất 16 ký tự, rỗng là tắt, lỗi cấu hình không in giá trị), `VISIGN_ADMIN_WORKSPACE`, `ADMIN_INSPECT_TIMEOUT_SECONDS` (60) |
| `api/admin.py` | Router `/api/admin` chỉ được gắn khi có token; Bearer so sánh hằng thời gian; `POST /inspect` nhận multipart `video`, dùng chung giới hạn body 10 MiB với `/predictions` |
| `api/pilot.py` | `GET /pilot`, `GET /pilot/history`, `POST /pilot/prepare` và `/pilot/train` trả 202 kèm `TrainingRun` |
| `admin/errors.py` | Envelope `{code, message, requestId}` với mã riêng `ADMIN_*` (401/409/503/504), không thêm vào catalog `/api/v1` nên contract FE–BE công khai không đổi; 401 kèm `WWW-Authenticate: Bearer` |
| `admin/inspection.py` | Một lượt inspect; nhận diện MP4/WebM theo byte đầu; clip trong thư mục tạm riêng, xóa ở mọi nhánh kể cả sau timeout (worker chạy nốt rồi xóa); ZIP gồm `report.json` (`sourceName` chung) và `landmarks.npz`; dọn thư mục sót khi khởi động |
| `admin/pilot_jobs.py` | Một job ở `preparing/training/evaluating`; `TrainingRun` lưu theo `runId`; lỗi chỉ trả câu cố định; job dở khi tiến trình dừng hoặc bị giết thành `failed`; worker là thread daemon, sau khi đóng không ghi đè trạng thái |
| `admin/dependencies.py`, `main.py` | Lấy pipeline `visign_ai` và runner `visign_ai.pilot` nếu có, thiếu thì 503; gắn vào lifespan |
| `contracts/admin-tools.md` | Bổ sung trường `video`, body 202 là `TrainingRun`, giới hạn, nội dung ZIP, bảng mã lỗi, giao diện runner cho P3 |
| `tests/contract/test_admin_tools_contract.py` | 30 test (T078) |

## Pre-commit synchronization

- `origin/main...HEAD` = `0 0` tại `6d9a958` ngay trước commit; nhánh mới `quang/t076-t083` không ảnh hưởng `main`.

## Smoke

| Gate | Kết quả |
|---|---|
| Test-first RED | (1) Lỗi import vì chưa có `visign_api.admin`. (2) Thêm sau: runner trả metric ngoài `[0, 1]` thì thread chết và run kẹt ở `training` (test hết giờ); đã chuyển phần kiểm kết quả vào khối bắt lỗi |
| GREEN | 30 test; 5 lần chạy liên tiếp đều 30/30 |
| Bắt hồi quy | 15/15 mutation: bỏ so sánh token, bỏ `WWW-Authenticate`, luôn gắn router, nhận token ngắn, không xóa thư mục tạm, chờ slot thay vì 409, bỏ timeout, lộ `sourceName`, không nhận MP4, bỏ dọn khi khởi động, cho job thứ hai, train khi chưa `ready`, lộ chi tiết lỗi, bỏ khôi phục sau crash, worker cũ ghi đè sau khi đóng. Lần đầu "lộ `sourceName`" sống vì pipeline giả chỉ ghi tên file; đã cho pipeline giả ghi cả đường dẫn |
| Live uvicorn, pipeline `visign_ai` thật | Tắt → 404 `ROUTE_NOT_FOUND`; sai token → 401; inspect WebM VP8 → 200 ZIP (`report.json`, `landmarks.npz` 10 mảng, `sourceName=clip.webm`), 2,2 s; inspect MP4 → 200, 1,2 s; pilot `idle`, lịch sử rỗng; `prepare` → 503 `ADMIN_UNAVAILABLE` (chưa có runner P3); thư mục tạm trống sau cùng |
| Như CI (`uv sync --locked`, không `serving`) | Ruff; format 74 file; mypy 69 file; API + contract 401 passed, 3 skipped; security + integration 44 passed, 2 skipped |
| Có `serving` | API + contract + integration + security 465 passed, 4 skipped |

Clip dùng trong smoke là clip tổng hợp không có người; không dùng video người thật.

## Bàn giao

- **P3/Cường:** `prepare`/`train` sẽ chạy khi `visign_ai.pilot` có `build_pilot_runner()` đúng giao diện trong
  `contracts/admin-tools.md` (kiểm handoff, trích đặc trưng, train/evaluate vào thư mục run). Chưa có module này
  thì hai endpoint trả 503 đúng contract.
- **P5/Hiển:** có thể smoke T082 với backend thật (inspect, pilot, 401/404/409/503). FE đang cho phép clip tới
  100 MiB (`MAX_ADMIN_CLIP_BYTES`), backend giới hạn 10 MiB như pipeline nên trả 413; đề xuất đổi FE về 10 MiB để báo
  lỗi sớm.
- **P1/Huy:** phần admin của T084 có thể nghiệm thu (404 khi tắt, 401, 409, giới hạn byte/thời gian, dọn file tạm).

**Reviewer result**: `PENDING`
