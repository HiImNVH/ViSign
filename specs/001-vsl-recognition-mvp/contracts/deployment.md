# Production Deployment Contract

## Topology

- Region: `ap-southeast-1` (Singapore), một region cho MVP.
- Public entrypoint: một CloudFront distribution với default HTTPS domain ổn định.
- Compute: một EC2 instance chạy `web` và `inference-api` bằng `compose.production.yml`; `web` reverse
  proxy `/api/*` đến API và phục vụ frontend build, admin routes bị tắt.
- Images: hai private ECR repositories, deploy theo immutable commit SHA/image digest.
- Model artifact: private versioned S3 object có SHA-256; deployment tải đúng version về volume chỉ đọc.
- Access: EC2 instance role chỉ đọc đúng model prefix và ghi log cần thiết; GitHub Actions assume deploy
  role bằng OIDC rồi gọi Systems Manager, không dùng access key hoặc SSH.
- Secrets/config: SSM Parameter Store `SecureString`; không bake vào image, source, user data hoặc log.
- Network: EC2 origin chỉ nhận HTTP từ CloudFront origin-facing managed prefix list; không mở SSH.

## Required production behavior

| Check | Acceptance |
|---|---|
| Public access | Một CloudFront HTTPS URL công khai và ổn định; web và `/api/v1/*` cùng origin |
| Health | `/api/v1/health` trả trạng thái/model readiness đúng contract |
| Prediction | Camera WebM hợp lệ chạy qua public web→API flow |
| Errors | Invalid clip, model-not-ready và route lỗi giữ stable envelope/correlation ID |
| Security | Least-privilege IAM/OIDC, no SSH/static keys, admin disabled, origin restricted, secret scan sạch |
| Resources | EC2 type/disk, một inference worker, timeout/body limit và container memory được khai báo, benchmark trước khi chốt |
| Observability | Request ID, status, latency và error code có log; không log video/landmark/secret |
| Cost | AWS Budget/alert, credit/time boundary và lịch start/stop cho demo load được ghi nhận; không tự upgrade Paid Plan |
| Rollback | Có thể redeploy image digest + S3 version smoke-tested trước và xác minh health/prediction |
| Retention | Model/evidence quan trọng có backup ngoài AWS trước khi Free Plan/credit kết thúc |

## CI/CD gate

Quality workflow phải pass trước deploy: Python lint/type/test, web lint/type/test/build, contract và
fixture integration. `deploy-aws.yml` chỉ nhận commit/tag đã qua quality gate, build/push image SHA lên
ECR, assume deploy role bằng OIDC và dùng SSM cập nhật host. Evidence phải lưu commit SHA, image digest,
S3 version ID, CloudFront URL và SSM command result. Production deploy không tự bật `demoReady`;
readiness vẫn do artifact metadata/release gate.
