# ViSign · Nghiệm thu ranh giới user/admin, secret, retention và release claim (T084)

**Ngày**: 2026-11-08 · **Người review**: P1/Huy · **Kết luận**: `PARTIAL` — ranh giới public đạt trên bản đang chạy;
nghiệm thu admin chờ backend T078–T080 (P2).

## 1. Ranh giới user/admin

| Tiêu chí | Bằng chứng | Kết quả |
|---|---|---|
| API công khai chỉ gồm `health`, `model-info`, `predictions` | `services/inference-api/src/visign_api/api/router.py`; contract `specs/001-vsl-recognition-mvp/contracts/openapi.yaml` | Đạt |
| Admin API tắt mặc định, không lộ khi chưa cấu hình | Chưa có route `/api/admin/*` trong mã API (T078–T080 chưa làm); production trả **404** cho `/api/admin/pilot` | Đạt cho bản hiện tại |
| Trang admin không làm lộ quyền | `/admin/train-model` (T082) chỉ là UI; token nhập tay, giữ trong state React, gửi `Authorization: Bearer`, `credentials: 'omit'`, 401 xoá token; không ghi storage/URL (review T081/T082) | Đạt phần FE |
| Tài liệu API tắt ở production | `API_DOCS_ENABLED=false` trong `compose.production.yml`; `/api/docs` → 404 | Đạt |
| Admin không dùng chung tài nguyên với luồng public khi chạy | Chưa có backend admin để kiểm (single active job, cleanup, giới hạn byte của inspect) | **Chờ T078–T080** |

## 2. Secret

| Tiêu chí | Bằng chứng | Kết quả |
|---|---|---|
| Không commit secret/khóa/model/video | Job `hygiene` chặn `.env`, `.pem`, `.key`, credentials JSON, media và model binary; quét secret trong T092 | Đạt |
| Không có khóa dài hạn trên máy chủ | EC2 dùng IAM role (chỉ kéo `visign/*`, đọc S3 `artifacts/`, `deploy/`, SSM); không SSH, không access key | Đạt |
| Không có secret trong môi trường container | `docker exec … env` trên EC2: không biến admin/token/secret (`GPG_KEY` là ID khóa ký Python công khai của image gốc) | Đạt |
| Token admin (khi có) | Phải đọc từ biến môi trường `VISIGN_ADMIN_TOKEN`, không log, không trả về; so sánh hằng thời gian | **Kiểm khi P2 bàn giao** |
| CI deploy không dùng khóa tĩnh | GitHub OIDC bị SCP của AWS Free Plan chặn; deploy hiện chạy thủ công bằng `aws login` (phiên tạm) + SSM | Ghi nhận giới hạn |

## 3. Retention

| Tiêu chí | Bằng chứng | Kết quả |
|---|---|---|
| FR-011: không lưu video sau khi trả kết quả | `inference/temporary_clip.py` (`mkstemp` + `unlink` trong `finally`); `/tmp` là tmpfs; kiểm trên EC2 sau nhiều request: **0** file clip trong `/tmp` | Đạt |
| Artifact model chỉ đọc | Bind `/models/artifact` `rw=false`; root filesystem chỉ đọc | Đạt |
| FR-034–036: lịch sử chỉ trên trình duyệt, ≥ 24 giờ, có nút xoá | `translationHistory.ts`, T100–T104 `VERIFIED`; lỗi FE-T090-01 (cleanup ghi lỗi làm mất mục đã đọc) chờ P5 sửa | Đạt, có 1 lỗi đã biết |
| Log không chứa video/nội dung nhạy cảm | Log JSON chỉ có `requestId`, mã lỗi, thời gian, status | Đạt |

## 4. Checklist release claim

Trước khi trình bày hoặc chia sẻ URL, kiểm đủ các mục sau:

- [ ] `model-info` đúng artifact đang chạy (`artifactKind`, `modelVersion`, `datasetVersion`) và UI hiện cảnh báo tương ứng.
- [ ] Chỉ nói "nhận diện 10 nghĩa" khi artifact `full` có `demoReady=true` từ release gate (FR-016: Macro-F1 ≥ 80%,
  recall mỗi nghĩa ≥ 65% trên split `video-held-out`). Hiện tại: pilot Giấy tờ/Nhận, Macro-F1 0,33,
  **`demoReady=false`** → chỉ được gọi là bản pilot.
- [ ] Gọi đúng loại split `video-held-out`; không nói "người ký chưa thấy" (FR-015).
- [ ] Nêu độ trễ thật kèm môi trường đo (EC2 t3.small: 5,5–6,3 s/clip với pilot; chưa đạt SC-002 ≤ 3 s).
- [ ] Không nêu kết quả usability (T071 đã bỏ); bằng chứng trải nghiệm chỉ gồm T063, T088 và kiểm webcam của nhóm.
- [ ] Nguồn dữ liệu: ghi rõ gồm video giáo dục công khai và video nhóm tự quay; `sourceUri` theo từng clip (P4 đang sửa).
- [ ] Disclaimer "không thay thế phiên dịch viên" hiển thị cùng mọi kết quả (đã có trong UI).
- [ ] URL demo đang dùng HTTPS tạm (Cloudflare Quick Tunnel) — nói rõ là môi trường thử nghiệm, chưa có rate limit.

## 5. Quyết định

- Ranh giới public, secret và retention của bản đang chạy: **chấp nhận**.
- Phần admin: **chưa nghiệm thu** — mở lại khi P2 bàn giao T078–T080 (kiểm 404 khi tắt, 401 sai token, 409 job đồng
  thời, giới hạn byte/thời gian của inspect, dọn file tạm ở mọi nhánh) và P5 chạy T082 với backend thật.
- T084 giữ `[ ]` cho tới khi hoàn tất phần admin.
