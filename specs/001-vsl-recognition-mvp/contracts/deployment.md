# Production Deployment Contract

## Topology

- Region: `ap-southeast-2` (Sydney), một region cho MVP; benchmark từ máy demo tại Việt Nam phải đạt SC-002.
- Public entrypoint: một CloudFront distribution với default HTTPS domain ổn định.
- Stable origin: một Elastic IP được gắn vào EC2 và giữ nguyên qua stop/start; CloudFront origin dùng
  DNS name phân giải đến Elastic IP, không dùng public IP tạm thời.
- Compute: một EC2 instance chạy `web` và `inference-api` bằng `compose.production.yml`; `web` reverse
  proxy `/api/*` đến API và phục vụ frontend build, admin routes bị tắt.
- CloudFront behaviors:
  - Default `/*`: chỉ static web `GET/HEAD`, cache bật và SPA fallback không được nuốt `/api/*`.
  - Ordered `/api/*`: allowed methods `GET, HEAD, OPTIONS, PUT, POST, PATCH, DELETE`; cache policy
    `CachingDisabled`; không cache response kể cả health/model-info/error; forward body, query string và
    các header contract gồm `Content-Type`, `Origin`, `X-Request-ID`; không forward cookie.
  - Response của origin, gồm status, error envelope và `X-Request-ID`, phải đi nguyên vẹn đến viewer.
- Images: hai private ECR repositories, deploy theo immutable commit SHA/image digest.
- Model artifact: private versioned S3 object có SHA-256; deployment tải đúng version về volume chỉ đọc.
- Access: EC2 instance role chỉ đọc đúng model prefix và ghi log cần thiết; GitHub Actions assume deploy
  role bằng OIDC rồi gọi Systems Manager, không dùng access key hoặc SSH.
- Current access exception (2026-11-07): AWS Free Plan SCP chặn `iam:CreateOpenIDConnectProvider` và
  bootstrap stack đã rollback sạch. Tín là project team member qua AWS Settings và MAY chạy integration
  thủ công bằng phiên Console/CloudShell của chính mình; MUST NOT tạo static access key. Ngoại lệ này
  không thỏa automated CI/CD acceptance và hết hiệu lực khi OIDC được mở khóa có phê duyệt.
- Secrets/config: SSM Parameter Store `SecureString`; không bake vào image, source, user data hoặc log.
- Network: EC2 origin chỉ nhận HTTP từ CloudFront origin-facing managed prefix list; không mở SSH.

## Required production behavior

| Check | Acceptance |
|---|---|
| Public access | Một CloudFront HTTPS URL công khai và ổn định; web và `/api/v1/*` cùng origin; stop/start EC2 không đổi origin nhờ Elastic IP |
| Health | `/api/v1/health` trả trạng thái/model readiness đúng contract |
| Prediction | Camera WebM hợp lệ chạy qua public web→API flow |
| Errors | Invalid clip, model-not-ready, `404/405/307` và route lỗi đi qua API behavior không cache, giữ status/envelope/correlation ID |
| Security | Least-privilege IAM/OIDC, no SSH/static keys, admin disabled, origin restricted, secret scan sạch |
| Resources | EC2 type/disk, một inference worker, timeout/body limit và container memory được khai báo, benchmark trước khi chốt |
| Observability | Request ID, status, latency và error code có log; không log video/landmark/secret |
| Cost | AWS Budget/alert tính cả public IPv4/Elastic IP, credit/time boundary và lịch start/stop cho demo load được ghi nhận; không tự upgrade Paid Plan |
| Rollback | Có thể redeploy image digest + S3 version smoke-tested trước và xác minh health/prediction |
| Retention | Model/evidence quan trọng có backup ngoài AWS trước khi Free Plan/credit kết thúc |

## CI/CD gate

Quality workflow phải pass trước deploy: Python lint/type/test, web lint/type/test/build, contract và
fixture integration. `deploy-aws.yml` chỉ nhận commit/tag đã qua quality gate, build/push image SHA lên
ECR, assume deploy role bằng OIDC và dùng SSM cập nhật host. Evidence phải lưu commit SHA, image digest,
S3 version ID, CloudFront URL và SSM command result. Production deploy không tự bật `demoReady`;
readiness vẫn do artifact metadata/release gate.

Cho tới khi OIDC được mở khóa, không tạo `deploy-aws.yml` dùng access-key secrets. Manual deployment
phải ghi cùng bộ evidence và giữ T091/T096 mở.

## Trạng thái thực tế 2026-11-08 (tạm thời, chưa thỏa đủ contract)

| Mục contract | Thực tế | Còn thiếu |
|---|---|---|
| CloudFront HTTPS | Bị chặn: tài khoản cần AWS Support xác minh. HTTPS tạm qua Cloudflare Quick Tunnel (`cloudflared` trên EC2, không mở cổng; URL đổi khi khởi động lại) | Bật `EnableCloudFront=true` trên stack `visign-origin` khi được duyệt |
| EC2 + Elastic IP + ECR + S3 + SSM, không SSH | Đạt: CloudFormation `visign-storage`, `visign-origin`; IAM role chỉ kéo `visign/*` và đọc S3 `artifacts/`, `deploy/` | — |
| Image theo commit SHA, artifact theo version | Đạt: tag 12 ký tự SHA, ECR tag bất biến; S3 có versioning | — |
| Deploy qua CI bằng OIDC | Bị chặn bởi SCP Free Plan; deploy thủ công bằng phiên `aws login` tạm thời + SSM | Mở OIDC (cần quyết định billing) |
| Security headers, admin tắt, không lưu video | Đạt trên EC2 (`docs/admin-acceptance.md`) | HSTS khi có CloudFront (T096) |
| CI chặn lỗi image trước deploy | Job `docker`: build 2 image, nạp MediaPipe trong container chỉ đọc, smoke 14/14 | — |
