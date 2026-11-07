# ViSign · Báo cáo deploy AWS (T095)

**Cập nhật**: 2026-11-08 · **Thực hiện**: P1/Huy (Tín bàn giao phần Docker/AWS) · **Trạng thái**: `PARTIAL` —
origin EC2 chạy được; CloudFront HTTPS bị chặn chờ AWS xác minh tài khoản.

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

## Rủi ro và việc tiếp theo

1. **Camera cần HTTPS**: trình duyệt chỉ cho `getUserMedia` trên HTTPS hoặc localhost, nên người dùng chưa thử được
   qua origin HTTP. Chờ CloudFront (sau khi AWS xác minh) rồi cập nhật `visign-origin` sang `EnableCloudFront=true`
   (bỏ `DirectAccessCidr`).
2. **SC-002 (≤ 3 s)**: riêng mạng tới Sydney đã ~1,7 s; với model thật (extract ~1 s trên Docker local) tổng sẽ sát
   hoặc vượt 3 s. Cân nhắc region `ap-southeast-1` (Singapore) gần Việt Nam hơn; đo lại khi có CloudFront.
3. Đổi phiên bản: tải artifact lên `s3://…/artifacts/<version>/`, push image tag mới, cập nhật stack
   (`ImageTag`/`ArtifactVersion`), rồi chạy `/opt/visign/deploy.sh` qua SSM (user data chỉ chạy lần đầu).
4. T096 (CloudWatch, HSTS, kiểm IAM) và deploy-after-pass qua CI vẫn mở; OIDC bị SCP Free Plan chặn.
