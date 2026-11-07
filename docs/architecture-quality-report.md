# ViSign · Báo cáo chất lượng kiến trúc (T090)

**Trạng thái**: bản đầu 2026-11-08 trên `origin/main` `9916831`, phụ trách P1/Huy (trợ lý soạn theo uỷ quyền),
đồng phụ trách P5/Hiển (phần FE cần P5 xác nhận/bổ sung). Mọi số liệu đo trực tiếp trên repo.

## 1. Cấu trúc module

| Module | Vai trò | Kích thước lớn nhất | Test |
|---|---|---|---|
| `apps/web` | React/TS/Vite: camera, kết quả, lỗi, bản dịch + lịch sử 24 giờ | `useRecognition.ts` 216 dòng | 17 file (Vitest, Playwright, E2E) |
| `services/inference-api` | FastAPI `/api/v1`, registry fixture/pilot/full, kiểm clip, lỗi, bảo mật | `gru_predictor.py` 254 dòng | 25 file |
| `ai` | Decode → MediaPipe → tensor 32×234 → GRU; train/eval/gate/benchmark | `train.py` 278 dòng | 9 file |
| `tests/` | contract, integration, security xuyên module | — | 6 file |

Không file nguồn nào vượt ~280 dòng; trách nhiệm tách theo thư mục `domain/`, `api/`, `inference/`
(backend) và `landmarks/`, `training/`, `evaluation/` (AI).

## 2. Chiều phụ thuộc

```text
apps/web ──HTTP (OpenAPI v1)──▶ services/inference-api ──import (extra "serving")──▶ ai (visign_ai)
```

- `ai` **không** import `visign_api` → AI dùng độc lập cho train/eval.
- API chỉ phụ thuộc `visign_ai` khi cài extra `serving` (6 module trong `inference/` + `config.py`); bản
  fixture chạy không cần torch/MediaPipe → CI nhẹ.
- Web không import code ngoài `apps/web`; hợp đồng FE–BE giữ bằng `openapi.yaml` + type viết tay + drift test.

**Đánh giá**: một chiều, không vòng; đúng nguyên tắc "train và API dùng cùng pipeline" mà không trộn module.

## 3. Quy ước code

| Hạng mục | Hiện trạng |
|---|---|
| Lint/type | Ruff + mypy (Python), ESLint + `tsc` (web) chạy trong CI trên mọi push |
| Format | 96/97 file Python đúng `ruff format`; còn `ai/src/visign_ai/evaluation/metrics.py`. CI **chưa** chạy `ruff format --check` |
| Comment | Python dùng tiếng Việt không dấu (ASCII-safe cho console Windows); docs tiếng Việt có dấu |
| Commit | `CPx Txxx(scope): ...`, evidence theo checkpoint, CI xanh trước khi đánh `[X]` |

## 4. Trùng lặp

| Chỗ trùng | Vị trí | Rủi ro | Đề xuất |
|---|---|---|---|
| Giới hạn clip 10 MiB / 300–6000 ms | `services/inference-api/.../config.py`, `ai/.../video_decoder.py`, `apps/web/.../cameraSession.ts` | Sửa một nơi thì lệch nơi khác | Lấy từ một nguồn (hằng số trong `visign_ai` cho API; test so giá trị web với OpenAPI/config) |
| Kiểm chữ ký WebM (EBML) | `clip_validator.py` (API, kiểm sớm trước decoder) và `video_decoder.py` (AI) | Hai quy tắc có thể lệch | API import hằng số/hàm kiểm từ `visign_ai` hoặc thêm test so khớp hai quy tắc |
| Type TS và schema OpenAPI | `apps/web/src/types/inference-api.ts` | Đã được drift test khoá (T099) | Giữ nguyên trong MVP (D4) |

## 5. Khả năng mở rộng

| Hướng | Mức sẵn sàng |
|---|---|
| Thêm nghĩa/biến thể | Qua class map + train lại; API/FE không đổi code (registry đọc `model_info.json`) |
| Đổi artifact fixture/pilot/full | Đổi `MODEL_ARTIFACT_PATH` + khởi động lại; đã test chuỗi đổi và rollback (T064) |
| Thay mô hình (ngoài GRU) | Registry theo `artifactKind`; cần factory mới cho kiến trúc khác |
| Nhiều worker/instance | Hiện một inference slot mỗi tiến trình; mở rộng ngang cần thêm instance (ngoài MVP) |
| Latency | Nút thắt ở MediaPipe (p50 ~4,6 s), không ở kiến trúc API/GRU |

## 6. Hành động đề xuất

| # | Hành động | Owner | Ưu tiên |
|---|---|---|---|
| 1 | Gom giới hạn clip về một nguồn + test đồng bộ web/API/AI | P2 + P3 | Trung bình |
| 2 | API dùng chung quy tắc kiểm WebM với `visign_ai` | P2 | Thấp |
| 3 | Thêm `ruff format --check` vào CI sau khi format `metrics.py` | P1 (T091) + P3 | Thấp |
| 4 | Root mypy đang `follow_imports = "skip"` → kiểu dữ liệu giữa package không được kiểm; cân nhắc bật `normal` cho `visign_api` ↔ `visign_ai` | P1 + P2 | Trung bình |
| 5 | CI chưa có job Playwright/E2E (camera giả + backend thật chạy local bằng `npm run test:e2e`) | P1 (T091) | Trung bình |
| 6 | Giữ detector MediaPipe giữa request để đạt SC-002 | P3 | Cao |

## 7. Phần FE cần P5 bổ sung

Ranh giới component (`features/recognition/*`), quản lý state (`useRecognition.ts`), tái sử dụng UI và quy ước
CSS — P5 xác nhận hoặc bổ sung mục này trước khi T090 được review.
