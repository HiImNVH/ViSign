# ViSign · Báo cáo deploy AWS (T095)

**Cập nhật**: 2026-11-08 · **Thực hiện**: P1/Huy (Tín bàn giao phần Docker/AWS) · **Trạng thái**: `PARTIAL` —
origin EC2 chạy được, HTTPS tạm qua Cloudflare Quick Tunnel; CloudFront chờ AWS xác minh tài khoản.

## Tài khoản và chi phí

| Mục | Giá trị |
|---|---|
| Gói | AWS Free Plan, credit 100 USD, hết hạn 2027-05-07 |
| Region | `ap-southeast-2` (Sydney) |
| Budget | `visign-monthly-credit-guard`: 50 USD/tháng, tính **trước** khi trừ credit; email ở 10% / 40% / 100% thực tế và 100% dự báo |
| Ước tính | EC2 t3.small + EBS 30 GB + Elastic IP ≈ 0,9 USD/ngày (~27 USD/tháng nếu chạy liên tục); tắt EC2 khi không demo |

## Hạ tầng (CloudFormation)

| Stack | Template | Tài nguyên | Trạng thái |
|---|---|---|---|
| `visign-storage` | [visign-storage.yml](../infra/aws/cloudformation/visign-storage.yml) | ECR `visign/inference-api`, `visign/web` (tag bất biến, scan on push, giữ 5 image); S3 `visign-artifacts-706101429579-ap-southeast-2` (private, versioning, SSE-S3, chỉ HTTPS) | `CREATE_COMPLETE` |
| `visign-origin` | [visign-app.yml](../infra/aws/cloudformation/visign-app.yml) với `EnableCloudFront=false` | EC2 t3.small AL2023 (IMDSv2, EBS mã hoá, swap 2 GB), IAM role chỉ kéo `visign/*` + đọc S3 `artifacts/`, `deploy/` + SSM; Security Group không SSH, cổng 80 chỉ cho một IP vận hành; Elastic IP | `CREATE_COMPLETE` |
| `visign-app` | cùng template, `EnableCloudFront=true` | thêm CloudFront (default cache theo header nginx; `/api/*` CachingDisabled + AllViewerExceptHostHeader, đủ method) | `ROLLBACK_COMPLETE` — rỗng, chờ xoá |
| `visign-github-oidc` | bootstrap-github-oidc.yml | — | `ROLLBACK_COMPLETE` — SCP chặn OIDC, rỗng, chờ xoá |

Lỗi CloudFront: `Your account must be verified before you can add new CloudFront resources` (403). Cần mở case
**Account and billing** (miễn phí) trên AWS Support để xác minh tài khoản.

## Bản phát hành đang chạy

| Mục | Giá trị |
|---|---|
| Commit / image tag | `3b29d4a2cec1` |
| Digest API | `sha256:44995ac1f8e4c02ec72d2c0b69d16427b0a9661bd0f95bb7f171bd09619e9c3c` (~665 MB nén) |
| Digest web | `sha256:2499c493f7080e98a2e59185236ef9396d582228558180b7af337dd87b5ab1fc` (~26 MB nén) |
| Artifact | `s3://…/artifacts/vsl-fixture-v0.0.1/` (fixture, `demoReady=false`) |
| EC2 / Elastic IP | `i-0bf663404c3a0d8f9` / `52.65.207.133` |

## Smoke qua origin (`http://52.65.207.133`, từ máy vận hành ở Việt Nam)

| Kiểm | Kết quả |
|---|---|
| `/healthz`, `/api/v1/health` | 200; `modelReady=true`, `vsl-fixture-v0.0.1` |
| Header | Web: CSP `default-src 'self'`, `Permissions-Policy camera=(self)`; API: CSP `default-src 'none'`, `no-store`, echo `X-Request-ID`; `Server: nginx` không lộ phiên bản/uvicorn |
| Lỗi | `/api/v1/x` 404 và `POST /api/v1/health` 405 đúng envelope; 10,5 MiB → 413 `CLIP_TOO_LARGE`; 12 MiB → 413 nginx |
| Dự đoán | Clip WebM → 200; round-trip 1,65–2,07 s dù fixture chỉ xử lý 1 ms → **chi phí mạng VN ↔ Sydney + upload ~1,6–2 s** |
| Trên máy (SSM) | 2 container `healthy`; API uid 10001, root chỉ đọc, `CapDrop=[ALL]`; RAM API 58 MiB, web 4,8 MiB lúc nghỉ; máy còn 1,29 GB khả dụng; đĩa 21% |

## HTTPS tạm qua Cloudflare Quick Tunnel (2026-11-08, Huy duyệt)

Trong lúc chờ AWS xác minh CloudFront, container `cloudflare/cloudflared:2026.10.7`
(digest `sha256:4955524aeaa379e154023d5a027c250f7b35041a2e7e950cf13f144bc9b9c5ba`) chạy trên EC2, nối nội bộ tới
`web:8080`; không mở thêm cổng AWS. Container chỉ đọc, `cap_drop ALL`, giới hạn 128 MiB, tự khởi động lại.

| Kiểm qua `https://<tên-ngẫu-nhiên>.trycloudflare.com` | Kết quả |
|---|---|
| `/` qua HTTPS | 200, chứng chỉ hợp lệ; giữ CSP và `Permissions-Policy camera=(self)` của nginx |
| `/api/v1/health` | `modelReady=true`, `vsl-fixture-v0.0.1` |
| `/admin/train-model` | 200 (SPA); admin API vẫn tắt |
| Dự đoán clip WebM | 200, round-trip **0,42–0,63 s** (nhanh hơn origin trực tiếp 1,7–2 s nhờ edge Cloudflare + kết nối giữ sẵn) |
| RAM trên EC2 | tunnel 16,9 MiB, web 4,8 MiB, API 60 MiB; máy còn 1,27 GB khả dụng |
| Webcam thật (Huy, laptop, trình duyệt desktop) | Bật camera → quay → gửi qua HTTPS → hiển thị "Cảm ơn" 95%, cảnh báo fixture `demoReady=false`, bản dịch trực tiếp cập nhật — **luồng end-to-end trên AWS đạt** |

Giới hạn: URL **đổi mỗi khi container/EC2 khởi động lại** (xem bằng `docker logs visign-tunnel` qua SSM); quick tunnel
không có cam kết uptime; công khai, chưa có rate limit. Tắt: `docker rm -f visign-tunnel`. Thay bằng CloudFront khi AWS
duyệt.

## Đổi sang artifact pilot Giấy tờ / Nhận (2026-11-08)

Artifact `t083-pilot-v2-approved` (weights `sha256:0c9a991b…c252`, khớp pilot report) tải lên
`s3://…/artifacts/t083-pilot-v2-approved/`; trên EC2 đổi `ARTIFACT_VERSION` trong `/opt/visign/release.env` rồi chạy
`/opt/visign/deploy.sh` qua SSM (tham số stack `ArtifactVersion` vẫn ghi fixture vì user data chỉ chạy lần đầu).
Tunnel giữ nguyên URL.

| Clip test (chuyển WebM 640×480) | Kết quả trên AWS | Round-trip / processing |
|---|---|---|
| GIAY_TO_HCM_1 | chấp nhận `GIAY_TO_HN_2` (đúng nghĩa), 0,609 | 6,31 s / 4,73 s |
| GIAY_TO_HN_2 | từ chối, 0,412 | 5,88 s / 4,05 s |
| NHAN_HCM_1 | chấp nhận `NHAN_HCM_1`, 0,658 | 5,56 s / 3,99 s |
| NHAN_HN_2 | từ chối, 0,361 | 5,51 s / 4,07 s |
| Clip không có người | 422 `NO_PERSON_DETECTED` | 4,14 s |

Nhãn và confidence **trùng khớp** lần chạy Docker local (parity môi trường). Nhưng processing trên t3.small
**4,0–4,7 s** (local 12 CPU: 1,4–2,3 s) → round-trip 5,5–6,3 s, **trượt SC-002 (≤ 3 s)**. Phần nặng là MediaPipe trên
2 vCPU burst. Hướng xử lý: thử `c7i-flex.large` (cũng dùng credit Free Plan, CPU mới hơn, 4 GB) chỉ trong ngày demo,
hoặc giảm độ phân giải/số frame giải mã (P3).

## Dịch trực tiếp trên AWS (2026-11-08, `d7637107d8be`)

Image web/API `d7637107d8be` (mã nguồn `de14b19`: dịch trực tiếp T105–T107) đẩy lên ECR, đổi `IMAGE_TAG` và chạy
`deploy.sh` qua SSM; artifact vẫn pilot Giấy tờ/Nhận, tunnel giữ URL.

| Kiểm | Kết quả |
|---|---|
| CSP thật qua HTTPS | `script-src 'self' 'wasm-unsafe-eval'`; WASM `application/wasm` 13,5 MB, model tay 7,8 MB + pose lite 5,8 MB phục vụ cùng origin |
| MediaPipe trên trình duyệt (Edge, camera giả không có người) | Nạp xong và báo "Không phát hiện người" sau **6,9 s** lần đầu qua tunnel (0,9 s khi chạy local); không lỗi CSP/console |
| Image web | 150 MB (trước 90,5 MB) do mang WASM + model |

Chưa đo: webcam thật với người ký trên bản deploy và thời gian từ lúc tay dừng tới khi hiện chữ (T108).

## Đổi sang c7i-flex.large cho ngày demo (2026-11-08)

Lead chọn chạy một ngày rồi tắt: cập nhật stack `visign-origin` `InstanceType=c7i-flex.large` (2 vCPU thế hệ mới, 3,8 GB
RAM, vẫn dùng credit Free Plan); instance giữ nguyên ID và Elastic IP, chỉ khởi động lại. URL tunnel mới:
`https://slope-flexibility-preferences-attacks.trycloudflare.com`.

| 4 clip test × 2 lượt | t3.small | c7i-flex.large |
|---|---|---|
| `processingTimeMs` trên server | 4.050–4.733 ms | **2.494–3.391 ms** |
| Round-trip từ Việt Nam qua tunnel | 5,5–6,3 s | **3,9–5,4 s** (một lần 7,0 s do mạng) |
| Nhãn/confidence | — | trùng khớp hoàn toàn |

Phần còn lại chủ yếu là upload clip ~0,5–0,6 MB sang Sydney (1,4–3,6 s). SC-002 (≤ 3 s) vẫn chưa đạt; hướng tiếp theo là
gửi landmark từ trình duyệt thay cho video. Tắt dự án sau demo: dừng EC2 (`aws ec2 stop-instances`) hoặc xoá stack
`visign-origin` để ngừng tính phí EC2/EBS/Elastic IP.

## Rủi ro và việc tiếp theo

1. **Camera cần HTTPS**: trình duyệt chỉ cho `getUserMedia` trên HTTPS hoặc localhost, nên người dùng chưa thử được
   qua origin HTTP. Chờ CloudFront (sau khi AWS xác minh) rồi cập nhật `visign-origin` sang `EnableCloudFront=true`
   (bỏ `DirectAccessCidr`).
2. **SC-002 (≤ 3 s)**: riêng mạng tới Sydney đã ~1,7 s; với model thật (extract ~1 s trên Docker local) tổng sẽ sát
   hoặc vượt 3 s. Cân nhắc region `ap-southeast-1` (Singapore) gần Việt Nam hơn; đo lại khi có CloudFront.
3. Đổi phiên bản: tải artifact lên `s3://…/artifacts/<version>/`, push image tag mới, cập nhật stack
   (`ImageTag`/`ArtifactVersion`), rồi chạy `/opt/visign/deploy.sh` qua SSM (user data chỉ chạy lần đầu).
4. T096 (CloudWatch, HSTS, kiểm IAM) và deploy-after-pass qua CI vẫn mở; OIDC bị SCP Free Plan chặn.
