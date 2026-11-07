# CP4 T044/T048 smoke evidence — luật quyết định theo ngưỡng confidence

| Trường | Giá trị |
|---|---|
| Checkpoint/task | `CP4 / T044, T048` (module thuần, cần trước endpoint T038 để không trả kết quả đoán bừa) |
| Owner | `P2 Tín` |
| Reviewer | `P1 Huy`; `P3 Cường` (cách chọn `acceptanceThreshold`) |
| Candidate commit | `CP4 T044,T048(api): add pure confidence decision rule` |
| Commit | `9a64b41343c2de7787c96ccd18b864b100fd4104` — [9a64b41](https://github.com/HiImNVH/ViSign/commit/9a64b41343c2de7787c96ccd18b864b100fd4104); CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42375491322) |
| Ngày/giờ | `2026-11-07T19:58+07:00` |
| Status | `PASS` local và CI; chờ reviewer verify |

## Phạm vi

- `inference/prediction_decision.py`: `decide_prediction(raw_prediction, acceptance_threshold)` chấp nhận khi
  `confidence >= acceptanceThreshold` (ngưỡng bao gồm, như legacy) **và** có chữ hiển thị; ngược lại trả
  `accepted=false`, `classLabel=null`, `text = REJECTED_PREDICTION_TEXT` ("Không nhận diện được") — hiến pháp I, FR-008.
- Ngưỡng lấy từ artifact (`ModelMetadata.acceptanceThreshold`), không đặt cứng trong API.

## Smoke

| Gate | Kết quả |
|---|---|
| Test-first RED | `test_prediction_decision.py` trước khi có module: collection error |
| GREEN | 7 passed (0,70/0,85/1,0 chấp nhận; 0/0,42/0,6999 từ chối; chữ trống luôn từ chối) |
| Bắt hồi quy | Đổi `>=` thành `>` → 1 failed (biên 0,70); khôi phục giống hệt |
| Toàn bộ API + contract | 186 passed, 1 skipped `-W error`; Ruff, format, mypy (40 files) |

## Independent review — P1/Huy

Huy (P1) review endpoint của P2 và kết luận **đạt**; ghi nhận `2026-11-07T21:18:08+07:00` trên `219e10d`. Gate tái chạy: API + contract 211 passed, 1 skipped; CI `quality.yml` xanh.

**Reviewer result**: `P1_VERIFIED` → T044, T048 `[X]`.
