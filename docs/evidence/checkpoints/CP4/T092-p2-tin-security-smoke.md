# CP4 T092 smoke evidence — audit bảo mật, độ tin cậy và lệnh audit một lần

| Trường | Giá trị |
|---|---|
| Checkpoint/task | `CP4 / T092` — audit theo FR-027: dependency/secret scan, upload abuse, CORS, header, giới hạn tài nguyên, timeout, log privacy, recovery |
| Owner | `P2 Tín` |
| Reviewer | `P1 Huy` |
| Candidate commit | `CP4 T092(security): add security audit, headers and docs lockdown` |
| Commit | `2561c7d4c5bace5c7c7db00e632382b15d752344` — [2561c7d](https://github.com/HiImNVH/ViSign/commit/2561c7d4c5bace5c7c7db00e632382b15d752344); CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42396068969) |
| Ngày/giờ | `2026-11-08T00:17+07:00` |
| Status | `PASS` local và CI |

## Phạm vi

| File | Nội dung |
|---|---|
| `api/security_headers.py` (mới) | `nosniff`, `no-referrer`, `X-Frame-Options: DENY`, CSP `default-src 'none'; frame-ancestors 'none'`, `Cache-Control: no-store` mặc định; chỉ trang HTML docs mà app đang phục vụ được miễn CSP |
| `api/request_middleware.py` | Gắn security header cạnh `X-Request-ID` cho mọi response, kể cả lỗi |
| `config.py`, `main.py` | `API_DOCS_ENABLED` (mặc định `false`) tắt `/docs`, `/redoc`, `/openapi.json` |
| `tests/security/test_api_security.py` (16 test) | Header trên 200/307/404/405/415; docs tắt mặc định và 404 của docs vẫn đủ header; bật docs khi dev; CORS không credential; tên file độc; flood field form |
| `tests/security/test_upload_burst.py` (1 test) | 12 upload 1,5 MiB đồng thời: 11 × 503 `SERVICE_BUSY`, đúng 1 clip trên đĩa suốt đợt tải, thư mục tạm trống sau đó (ghi chú T024–T025) |
| `tests/security/test_security_audit_script.py` (8 test) | Logic lệnh audit với runner giả: dừng ở lệnh lỗi, bảng PASS/FAIL, advisory chấp nhận có lý do, test và pip-audit gồm extra `serving`, công cụ ghim phiên bản, quét cả file mới chưa add, dòng tóm tắt là kết quả của công cụ |
| `scripts/security_audit.py` | Lệnh `python scripts/security_audit.py`: test bảo mật/privacy/lỗi/phục hồi, pip-audit API + AI, npm audit production, quét secret theo baseline |
| `.secrets.baseline` | 28 báo nhầm đã duyệt (checksum manifest, đường dẫn giả trong test), chỉ lưu hash |
| `docs/security-report.md` | Báo cáo: đối chiếu FR-027, advisory chấp nhận, quyết định cho ghi chú các checkpoint trước, rủi ro còn mở |

## Pre-commit synchronization

- Bắt đầu trên `24a9e21`. Trước khi chốt, pull 5 commit: P1 review T040/T064 (`c875ae5`), P3 T065 (`fd2656f`),
  T089 (`6505caa`), T094 (`d65c38e`), T083 (`5a624b4`); không trùng file với T092. Stash → rebase → apply, digest
  11 path khớp.
- `origin/main...HEAD` = `0 0` tại `5a624b4`; mọi gate dưới đây chạy lại trên cây đã đồng bộ.
- Ngay trước commit: pull `231f8d2` (P5 T074–T075, T100–T104; chỉ `apps/web` và tài liệu P5), digest khớp; quét
  secret toàn repo theo baseline và 25 test bảo mật chạy lại PASS; `origin/main...HEAD` = `0 0` tại `231f8d2`.

## Smoke

| Gate | Kết quả |
|---|---|
| Test-first RED | (1) 11 failed, 4 passed: chưa có header và docs vẫn mở. (2) Sau smoke uvicorn: 4 failed vì 404 của `/docs`, `/redoc`, `/openapi.json` khi docs tắt thiếu CSP/`no-store` và `/openapi.json` được miễn CSP khi bật docs. (3) 1 failed: công cụ audit chưa ghim phiên bản. (4) 1 failed: bước test của audit thiếu extra `serving`, máy chưa cài extra thì test GRU bị skip mà audit vẫn PASS. (5) 1 failed: cột chi tiết lấy dòng "Installed N packages" của uv thay vì kết quả pytest. (6) 1 failed: bước quét secret chỉ xét file đã track nên báo nhầm "Secret Keyword" ở dòng `DETECT_SECRETS_TOOL` (file mới chưa add) lọt qua, và audit sẽ FAIL ngay sau commit; nay quét cả file mới chưa add, dòng đó đánh dấu `# pragma: allowlist secret` |
| GREEN | 25 test `tests/security` |
| Bắt hồi quy | 14/14 mutation bị bắt. Header/docs (10): không gắn header, docs bật mặc định, không miễn CSP cho trang docs, miễn theo danh sách path cố định, miễn cả schema, bỏ điều kiện `openapi_url`, bỏ trang OAuth2 redirect, thiếu CSP, thiếu `Cache-Control`, thiếu `nosniff`. Burst (4): ghi clip trước khi giữ slot, không xóa clip, chờ slot không giới hạn, 2 slot suy luận |
| Lệnh audit (có `serving`) | 5/5 PASS: 417 passed, 3 skipped (cần `VISIGN_CP2_REFERENCE_WEBM`); pip-audit API/AI 0 lỗ hổng chưa đánh giá (3 advisory chấp nhận); npm production 0; secret không có phát hiện mới |
| Như CI (`uv sync --locked`, không `serving`) | Ruff; format 63 file; mypy 58 + 4 file; API + contract 355 passed, 2 skipped; security + integration 44 passed, 2 skipped. Lệnh audit trên máy vừa gỡ `serving` tự cài lại extra và vẫn PASS |
| Live uvicorn (fixture, docs tắt) | Khai `Content-Length` 10 GiB, không gửi body → 413 `CLIP_TOO_LARGE`, trung vị 2,9 ms, tối đa 38,8 ms (5 lần); `/docs`, `/openapi.json` → 404 `ROUTE_NOT_FOUND` có CSP và `no-store`; health 200 đủ header; response có `server: uvicorn` (rủi ro #4 trong báo cáo) |
| Secret | Lịch sử 148 commit trên mọi ref: 0 mẫu key/token; file thử ngoài repo chứa AWS key giả → hook exit `1`, baseline không đổi; các file của commit này không có phát hiện mới |

Giới hạn: chưa có production nên HTTPS/HSTS, IAM, security group và CloudWatch thuộc T095/T096. Chưa có giới hạn tần suất
theo client (429); cần lead chọn giữa rule ở biên (WAF) và limiter trong API với mã lỗi mới (D3, FE xử lý trước).

## Đề xuất cho reviewer

- P1 (T091): thêm `tests/integration`, `tests/security` và `ruff format --check` vào job `api`; cân nhắc job audit riêng
  (cần mạng). AI còn 1 file chưa format (`ai/src/visign_ai/evaluation/metrics.py`).
- P1: chốt hướng rate limit (mục 8 của báo cáo, rủi ro #1).

**Reviewer result**: `PENDING`

## Independent review — P1/Huy

Review `2026-11-08T00:37:34+07:00` trên `dc9e357` (P1 review theo uỷ quyền của Huy).

| Kiểm tra | Kết quả |
|---|---|
| `pytest tests/security` + API + contract + integration | 399 passed, 4 skipped |
| Header trên app thật | `/api/v1/health`, `/docs`, `/openapi.json`, `/redoc`, route lạ: đều có `nosniff`, `X-Frame-Options: DENY`, CSP, `Referrer-Policy: no-referrer`, `no-store` |
| Docs/OpenAPI production | Tắt mặc định → 404 |
| `.secrets.baseline` | Chỉ gồm SHA-256 trong manifest và hai chuỗi giả `INTERNAL_SECRET` dùng để test log không lộ đường dẫn — không có secret thật |
| Advisory chấp nhận | torch `PYSEC-2025-194` (TorchScript, API không dùng), 2 advisory setuptools build-time — có lý do, advisory mới làm audit FAIL |

**Reviewer result**: `P1_VERIFIED` → T092 `[X]`.
