# Báo cáo audit bảo mật và độ tin cậy — ViSign Inference API (T092)

| Trường | Giá trị |
|---|---|
| Phạm vi | `services/inference-api` (API v1), dependency API/AI/web, secret trong repo, cấu hình CORS/header/docs |
| Yêu cầu | FR-027: bảo vệ video/secret, kiểm lỗ hổng dependency và cấu hình, health check, timeout, giới hạn tần suất/tài nguyên, log an toàn, rollback |
| Owner / reviewer | `P2 Tín` / `P1 Huy` |
| Ngày chạy | 2026-11-08, Windows 11; API chạy CPython 3.12.15; production AWS chưa triển khai (T095/T096) |

## 1. Cách chạy audit (một lệnh)

```powershell
python scripts/security_audit.py
```

Chạy từ gốc repo bằng Python có `uv` (trên PATH hoặc module `uv`) và `npm`. Cần mạng: pip-audit và npm audit tra cơ sở
dữ liệu lỗ hổng công khai (chỉ gửi tên và phiên bản package). Công cụ được ghim phiên bản (`pip-audit==2.10.1`,
`detect-secrets==1.5.0`) để kết quả tái lập được. Bước test chạy với extra `serving` như bản production (uv tự cài nếu
thiếu), nên test GRU không bị bỏ qua. Lệnh in bảng PASS/FAIL theo FR-027; exit code `0` nghĩa là đạt mọi kiểm tra. Kết
quả lần chạy này:

| Kiểm tra | Yêu cầu FR-027 | Kết quả | Chi tiết |
|---|---|---|---|
| Test bảo mật, privacy, lỗi, phục hồi | video/secret, log an toàn, timeout, giới hạn, rollback | PASS | 417 passed, 3 skipped (3 test cần clip đại diện qua biến môi trường) |
| pip-audit API (gồm extra `serving`) | lỗ hổng dependency | PASS | 0 lỗ hổng chưa đánh giá; 3 advisory đã chấp nhận (mục 3) |
| pip-audit AI | lỗ hổng dependency | PASS | Như trên |
| npm audit web production | lỗ hổng dependency | PASS | 0 lỗ hổng |
| Quét secret theo baseline | không có secret trong repo | PASS | Không có phát hiện mới so với `.secrets.baseline` |

pip-audit in `4 ignored` vì liệt kê `PYSEC-2026-3447` hai lần; thực tế là 3 advisory.

## 2. Đối chiếu FR-027

| Yêu cầu | Cơ chế | Bằng chứng |
|---|---|---|
| Bảo vệ video | Clip chỉ nằm trong file tạm tên ngẫu nhiên, ghi khi đã giữ slot, xóa trên mọi đường kể cả lỗi và hủy request; dọn clip sót khi khởi động; không lưu video | `test_temporary_clip.py`, `test_prediction_cleanup.py`, `tests/integration/test_prediction_privacy.py`, `tests/security/test_upload_burst.py` |
| Bảo vệ secret | 0 secret trong file đang track và lịch sử git; log không chứa token, cookie, tên file, chữ dịch | Mục 4; `test_prediction_privacy.py` |
| Lỗ hổng dependency | pip-audit (API, AI), npm audit (web) | Mục 3 |
| Cấu hình | CORS liệt kê origin, cấm `*` và credential (app từ chối khởi động); tắt docs mặc định; security header | Mục 6; `tests/security/test_api_security.py` |
| Health check | `GET /api/v1/health` (`no-store`); artifact hỏng → `degraded`, không lùi về fixture | `test_model_info_contract.py`, `tests/integration/test_prediction_pipeline.py` |
| Timeout | Chờ slot tối đa 3 s → 503 `SERVICE_BUSY` + `Retry-After: 3`; FE timeout 15 s cho dự đoán, 5 s cho health/model-info (D2); request bị hủy vẫn giữ slot tới khi worker xong | `test_predictions_contract.py`, `test_worker_thread.py`, `test_upload_burst.py` |
| Giới hạn tài nguyên | Mục 5 | Mục 5 |
| Log an toàn | JSON allowlist (`requestId`, `modelVersion`, timings, `accepted`, `errorCode`, method/path/status) | `test_observability.py`, `test_prediction_privacy.py` |
| Rollback | Khởi động lại với `MODEL_ARTIFACT_PATH` trước; candidate lỗi trong tiến trình giữ predictor cũ | `test_prediction_pipeline.py`, `test_predictor_registry.py`, `test_gru_artifact_loading.py` |

## 3. Lỗ hổng dependency

| Advisory | Package | Bản sửa | Đánh giá trong ViSign | Hành động |
|---|---|---|---|---|
| `PYSEC-2025-194` (CVE-2025-3000) | torch 2.11.0 | 2.13.0 | Hỏng bộ nhớ trong `torch.jit.script`, tấn công cục bộ. API không dùng TorchScript; chỉ `torch.load(weights_only=True)` + forward | Chấp nhận; nâng torch ở lần cập nhật lock AI (P3), API theo |
| `PYSEC-2026-3447` (CVE-2026-59890) | setuptools 81.0.0 | 83.0.0 | Đóng gói sdist trên macOS, không chạy lúc runtime | Chấp nhận; nâng khi cập nhật lock |
| `GHSA-xmj3-9gf7-h52w` | setuptools 81.0.0 | 84.1.0 | Cài wheel kiểu egg trên Windows, không chạy lúc runtime | Chấp nhận; nâng khi cập nhật lock |

Các advisory chấp nhận được khai báo kèm lý do trong `ACCEPTED_VULNERABILITIES` của `scripts/security_audit.py`; advisory
mới làm audit FAIL.

npm: gói production 0 lỗ hổng. Tính cả gói dev có 10 mức *moderate*, cùng bắt nguồn từ `minimatch` (DoS khi so khớp
glob) trong ESLint/typescript-eslint, chỉ chạy lúc lint và không vào bản build. Không có bản sửa giữ nguyên major (npm đề
xuất đổi major `eslint`/`typescript-eslint`), nên không chạy `npm audit fix --force`.

## 4. Quét secret

- Lệnh audit quét file đã track và file mới chưa add (bỏ qua file trong `.gitignore`), nên chạy trước commit sẽ thấy
  đúng những gì sắp được commit.
- `detect-secrets` trên file đang track: 28 phát hiện ở 6 file, đều đã duyệt là báo nhầm (SHA-256 kiểm toàn vẹn trong
  manifest Spec Kit và manifest model MediaPipe; hằng `INTERNAL_SECRET` là đường dẫn giả trong test chống lộ thông tin).
  Đã ghi vào `.secrets.baseline` (chỉ lưu hash), nên lần quét sau chỉ báo phát hiện mới. Báo nhầm trên một dòng
  có thể đánh dấu `# pragma: allowlist secret`; hiện chỉ dùng cho hằng `DETECT_SECRETS_TOOL` (tên công cụ, không phải
  secret).
- Lịch sử git (148 commit trên mọi ref): 0 mẫu AWS key, private key, token GitHub/Slack/Google/OpenAI/Anthropic.
- Kiểm chứng hook: file thử ngoài repo chứa AWS key giả sinh ngẫu nhiên → hook trả exit `1`, baseline không đổi.
- Hook trả exit `3` kèm "The baseline file was updated" khi số dòng của phát hiện cũ thay đổi: commit `.secrets.baseline`
  mới rồi chạy lại. Khi thêm chuỗi entropy cao hợp lệ (checksum mới), chạy
  `detect-secrets scan --baseline .secrets.baseline` rồi duyệt.

## 5. Lạm dụng upload và giới hạn tài nguyên

| Tấn công / giới hạn | Hành vi | Test |
|---|---|---|
| Khai `Content-Length` 10 GiB | 413 `CLIP_TOO_LARGE` trước khi đọc body; trên uvicorn thật trung vị 2,9 ms, tối đa 38,8 ms (5 lần) | `test_predictions_contract.py` |
| Body chunked vượt giới hạn | Dừng parse giữa chừng, 413 | `test_predictions_contract.py` |
| Clip > 10 MiB | 413 trước khi suy luận | `test_predictions_contract.py` |
| MIME lạ; byte MP4 gắn nhãn `video/webm` | 415 `UNSUPPORTED_MEDIA_TYPE` | `test_clip_validator.py`, `test_predictions_contract.py` |
| Multipart hỏng, thiếu boundary | 400 `INVALID_REQUEST` (envelope) | `test_predictions_contract.py` |
| Hơn 1000 field form | 400 `INVALID_REQUEST` | `tests/security/test_api_security.py` |
| Tên file `../`, đường dẫn tuyệt đối, NUL | Bị bỏ qua; API tự đặt tên tạm, không ghi ra ngoài thư mục tạm | `tests/security/test_api_security.py` |
| 12 upload 1,5 MiB cùng lúc | 1 lượt suy luận, 11 × 503 `SERVICE_BUSY`; suốt đợt tải đĩa chỉ có đúng 1 clip; xong thì thư mục tạm trống, kể cả file spool multipart | `tests/security/test_upload_burst.py` |
| Clip 0,3–6 s theo PTS, ≤ 900 frame, ≤ 4K | 422/400 theo catalog | `test_clip_validator.py`, decoder dùng chung |
| Không người / thiếu landmark | 422 trước khi gọi GRU | `test_clip_validator.py`, `test_gru_artifact_loading.py` |
| Lỗi bất ngờ | 500 `PREDICTION_FAILED`, không lộ traceback/đường dẫn | `test_predictions_contract.py` |

## 6. Header, CORS và tài liệu API

- Mọi response có `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `X-Frame-Options: DENY`,
  `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'` và `Cache-Control: no-store` (route có thể đặt
  riêng `Cache-Control`).
- `/docs`, `/redoc`, `/openapi.json` tắt mặc định: trả 404 `ROUTE_NOT_FOUND` với đủ header trên. Bật khi dev bằng
  `API_DOCS_ENABLED=true`; khi đó chỉ trang HTML `/docs`, `/redoc`, `/docs/oauth2-redirect` được miễn CSP để tải script,
  còn `/openapi.json` vẫn giữ header chặt. Contract chính thức là `specs/001-vsl-recognition-mvp/contracts/openapi.yaml`.
- CORS: không bao giờ trả `Access-Control-Allow-Credentials`; preflight từ origin lạ → 400 (ngoại lệ đã ghi trong
  `docs/contracts/api-conventions.md` v1.0.1).

## 7. Ghi chú từ các checkpoint trước

| Ghi chú (nguồn) | Quyết định |
|---|---|
| npm audit 10 *moderate* ở toolchain dev (CP1 T001–T007) | Giữ; không có bản sửa cùng major (mục 3). P5 nâng ESLint/typescript-eslint khi có bản tương thích |
| Có đưa `ruff format --check` vào CI không (CP2 T019–T021, CP7 T091) | Nên bật. API (62 file) và `tests/security` đã đúng format; AI còn 1 file (`ai/src/visign_ai/evaluation/metrics.py`) cần P3 format trước, sau đó P1 thêm bước vào job `api` và `ai` |
| Kiểm thư mục tạm sau chạy tải (CP2 T024–T025) | Đã kiểm bằng `tests/security/test_upload_burst.py` (mục 5) |
| Tắt `/docs` trên production (CP2 T026, CP4 T072–T073) | Tắt mặc định (mục 6) |
| torch từ PyPI kéo CUDA vào image (CP7 T091) | Chuyển sang T095: image API dùng torch bản CPU |

## 8. Rủi ro còn mở

| # | Phát hiện | Mức | Đề xuất | Owner |
|---|---|---|---|---|
| 1 | Chưa giới hạn tần suất theo client (`core.md` 8.8 yêu cầu trả 429). Mỗi request chờ slot giữ tối đa 10 MiB trong RAM trong ≤ 3 s và không có giới hạn số kết nối đồng thời | Trung bình | Lead chọn: (a) rule rate-based ở biên (AWS WAF trước CloudFront, có phí), hoặc (b) limiter trong API với mã mới `RATE_LIMITED` (theo D3, FE phải xử lý trước) | P1 quyết định, P2 làm |
| 2 | Không có thời gian tối đa cho một lượt suy luận phía server; lượt bị treo giữ slot tới khi khởi động lại | Trung bình | Theo dõi "slot bận quá lâu" và restart policy trong T095/T096 | P2 |
| 3 | HTTPS/HSTS, không mở SSH, IAM tối thiểu quyền, secret trong SSM, CloudWatch | Cao (khi deploy) | Thuộc T095/T096; OIDC đang bị SCP của AWS Free Plan chặn | P1, P2 |
| 4 | uvicorn trả header `server: uvicorn` (thấy trong smoke uvicorn) | Thấp | Chạy uvicorn với `--no-server-header` trong Compose (T095) | P2 |
| 5 | torch 2.11, setuptools 81 có advisory (mục 3) | Thấp | Nâng ở lần cập nhật lock | P3, P2 |
| 6 | Toolchain lint web có 10 advisory dev | Thấp | Nâng ESLint/typescript-eslint | P5 |
| 7 | CI chưa chạy `tests/integration`, `tests/security`, `ruff format --check` và lệnh audit | Trung bình | Thêm vào job `api`; job audit riêng (cần mạng) | P1 (T091) |
| 8 | Lỗi bất ngờ ghi traceback vào log | Thấp | Nội dung do code đặt, đã kiểm không chứa dữ liệu người dùng (T066) | — |

## 9. Giới hạn của audit

Audit chạy trên máy local; chưa có production để kiểm HTTPS, IAM, mạng và giám sát. Không gồm pentest mạng/DDoS và chưa
fuzz decoder (PyAV/FFmpeg); pip-audit chỉ phát hiện advisory theo phiên bản package. Cần chạy lại lệnh audit trên commit
được demo và trên production sau T095/T096.
