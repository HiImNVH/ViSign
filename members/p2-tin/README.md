# P2 Tín - Backend/Cloud/Security

- Current: AI–backend integration contract v0.0.1 đã xác nhận; chờ representative-clip schema review.
- Blocker: T099 chờ lead gửi quy ước API FE-BE.
- Ownership: `services/inference-api/`, `infra/gcp/`, `tests/security/`.
- Commit scopes: `api`, `backend`, `security`, `cloud`.

| Task | Planned files | Gate/result | Commit | Handoff |
|---|---|---|---|---|
| CP0 review | `docs/evidence/checkpoints/CP0/T085-T086-p1-huy-smoke.md` | VERIFIED: 5/5 gate PASS trên `22226b2`; 2 MEDIUM, 2 LOW, 1 INFO không chặn | Chưa commit | Huy cập nhật implementation-status, xử lý ghi chú |
| CP1 | API skeleton/toolchain | Chưa chạy | Chưa commit | Huy review |
| CP2 | API v1 contract, validation và T099 | Chưa chạy | Chưa commit | Hiển/Huy review |
| CP3/CP4 | Predictor, status/error, cleanup và security | Chưa chạy | Chưa commit | Cường/Hiển review |
| CP6 | Admin API boundary | Chưa chạy | Chưa commit | Huy review |
| CP7 | Cloud Run, HTTPS, secrets, rollback | Chưa chạy | Chưa commit | Huy review |
