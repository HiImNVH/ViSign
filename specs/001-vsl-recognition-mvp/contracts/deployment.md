# Production Deployment Contract

## Topology

- `web`: Cloud Run service phục vụ frontend production.
- `inference-api`: Cloud Run service phục vụ `/api/v1/*`; admin routes bị tắt.
- Model artifact: Google Cloud Storage object có version/hash, chỉ service account API được đọc.
- Secrets: Google Secret Manager; không bake vào image, source hoặc log.

## Required production behavior

| Check | Acceptance |
|---|---|
| Public access | Web URL HTTPS công khai và ổn định |
| Health | `/api/v1/health` trả trạng thái/model readiness đúng contract |
| Prediction | Camera WebM hợp lệ chạy qua public web→API flow |
| Errors | Invalid clip, model-not-ready và route lỗi giữ stable envelope/correlation ID |
| Security | Least-privilege service account, admin disabled, allowed origins explicit, secret scan sạch |
| Resources | CPU/RAM/concurrency/timeout/max instances được khai báo và có lý do |
| Observability | Request ID, status, latency và error code có log; không log video/landmark/secret |
| Cost | Budget/alert và cost estimate cho demo load được ghi nhận |
| Rollback | Có thể redeploy image/artifact smoke-tested trước và xác minh health/prediction |

## CI/CD gate

Quality workflow phải pass trước deploy: Python lint/type/test, web lint/type/test/build, contract và
fixture integration. Deploy workflow chỉ nhận commit/tag đã qua quality gate và lưu URL/revision làm
evidence. Production deploy không tự bật `demoReady`; readiness vẫn do artifact metadata/release gate.
