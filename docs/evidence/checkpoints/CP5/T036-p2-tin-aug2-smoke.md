# CP5 T036 evidence (P2) — bật augmentation aug2 trong cấu hình train full P0

## 1. Nhận dạng

| Trường | Giá trị |
|---|---|
| Checkpoint | `CP5` |
| Task | `T036` (train, owner P3 Cường) |
| Owner | `P2 Tín`. Thay đổi nằm ngoài scope của P2 (`train` thuộc P3), làm theo quyết định của Tín; cần P3/P1 review |
| Reviewer | `P3 Cường`, `P1 Huy` |
| Commit | `a083c02db74a3a17f15a8a1ce9ce1cea1e3bd6dd` — [a083c02](https://github.com/HiImNVH/ViSign/commit/a083c02db74a3a17f15a8a1ce9ce1cea1e3bd6dd); CI [success](https://github.com/HiImNVH/ViSign/actions/runs/42447292058) |
| Ngày/giờ | `2026-11-08T11:31+07:00` |
| Môi trường | Windows 11, Intel i5-8350U (4 nhân/8 luồng), Python 3.12.15 (`ai/.venv`), torch 2.11.0+cpu, MediaPipe 1.1.1, CPU |
| Status | `PASS` cho tái lập và gate liên quan. Model vẫn trượt cổng phát hành (`demoReady=false`) |

## 2. Phạm vi thay đổi

- Kết quả cần chứng minh: bật tăng cường dữ liệu chỉ cho tập train (`training/augmentation.py`, `fa10302`) với bộ
  aug2 giảm học thuộc so với không tăng cường, trên cùng một split.
- File: `ai/configs/p0-gru.yaml` thêm khối `augmentation` (`noise_std` 0,08; `time_warp` 0,35; `scale` 0,2;
  `rotate_deg` 20). Không đổi code.
- Không thuộc phạm vi: split chính thức T018 và manifest P0 của P4, giấy phép dữ liệu (T061/T076), đưa model lên API.
- Schema/data: feature schema `visign-xy-32-v0.3-draft`, extractor `tasks-hand-pose-face-1.1.1-24d9ff64192c8dc3`,
  dataset local `p0-local-v1`.

### Dữ liệu và split dùng để thử (local, không commit)

- Thư mục raw P0 cục bộ: 10 thư mục `<số>. <nghĩa>`, 486 video. Loại 215 video hiển thị dọc, trong đó 135 video lưu
  khung ngang kèm cờ xoay 270° mà decoder không áp dụng. Còn 271 video ngang.
- `python -m visign_ai.landmarks.extract_manifest`: 271/271 video trích được landmark.
- Nhãn `{meaningId}_{region}_1` theo `docs/team/data-convention.md` mục 8. `BAN_HCM_1` chỉ có 1 video nên bị bỏ,
  còn 270 mẫu, 15 nhãn, đủ 10 nghĩa.
- Split local phân tầng theo `classLabel`, tỉ lệ 10:3:2, seed 42, mỗi video là một `recordingSessionId`:
  179 train / 54 validation / 37 test. Đây không phải `create_splits.py` của T018 (12/5/3 cố định mỗi nghĩa). Dữ liệu
  không có `signerId` nên một người ký có thể xuất hiện ở nhiều tập.
- Manifest local ghi `licenseStatus=approved`, `verificationStatus=unverified` chỉ để qua bước kiểm đầu vào của CLI
  train, không phải duyệt chính thức.

## 3. Smoke test

| # | Mục tiêu | Command hoặc thao tác tái lập | Kết quả mong đợi | Kết quả thực tế/exit code | Trạng thái |
|---|---|---|---|---|---|
| 1 | Static gate | `python -m ruff check ai`; `python -m mypy ai/src ai/tests` | Không lỗi | Ruff không lỗi; mypy 60 file không lỗi; exit 0 | `PASS` |
| 2 | Unit | `python -m pytest ai/tests -q -rs` | Test liên quan đạt | 176 passed, 6 skipped, 35 failed. Cả 35 nằm trong `ai/tests/dataset/`: Windows checkout CRLF (`core.autocrlf=true`) nên validator từ chối `data/manifests/*.csv`. Bỏ thay đổi này ra vẫn đúng 35 failed. Test train/augmentation đạt | `PASS` cho thay đổi; lỗi môi trường có sẵn |
| 3 | Tái lập | Train rồi evaluate bằng `ai/configs/p0-gru.yaml` đã sửa trên `eed694d` | Giống hệt lần aug2 trên `fa10302` | Weights cùng SHA-256 `9db78452…114cb5`; lịch sử loss, ngưỡng 0,5, metric test và confusion matrix giống hệt | `PASS` |
| 4 | Phạm vi augmentation, dữ liệu riêng tư | Đọc `make_loader` và `evaluate.py`; kiểm path đã stage | Validation/test không bị biến đổi; không commit raw/npz/pt/manifest | Chỉ split `train` được bọc `AugmentedDataset`; evaluate dùng `SequenceDataset` gốc; chỉ stage YAML, evidence này và member README | `PASS` |
| 5 | Backend nạp artifact aug2 | Uvicorn local `127.0.0.1:8000` với `MODEL_ARTIFACT_PATH` trỏ tới artifact aug2; gửi 5 clip test (mỗi nghĩa 1 clip, chuyển sang WebM VP8 640×360, 30 fps) tới `/api/v1/predictions`, xoá WebM tạm sau khi gửi | Nạp được `feature_scale`; trả kết quả đúng contract | `/health` `modelReady=true`, `/model-info` `full`, ngưỡng 0,5, `demoReady=false`. 5/5 HTTP 200: Đau đầu, Bạn, Giấy tờ đúng (96%, 67%, 77%); Cảm ơn bị nhận nhầm thành Nhận (77%); Không bị từ chối (38%). Xử lý 3,0–4,0 s/clip trên CPU này | `PASS` |

### Kết quả train trên cùng split (seed 42, hidden 128, 60 epoch)

| Bản | Code | Trọng số nhóm | Augmentation (nhiễu/thời gian/tỉ lệ/xoay) | Epoch tốt nhất | Loss valid | Ngưỡng | Top-1 valid | Top-1 test | Accuracy test | Macro-F1 | Bị từ chối | W&B |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| baseline | `323beb2` | không | không | 46 | 1,561 | 0,7 | 63% | 59% | 40,5% | 0,448 | 18/37 | chưa ghi |
| r3 | `fa10302` | 0,7/0,2/0,1 | không | 25 | 1,570 | 0,6 | 56% | 43% | 27,0% | 0,287 | 25/37 | [9u0sahj9](https://forge.coreweave.com/wandb/hoagtin935-sai-gon-university/ViSign/runs/9u0sahj9) |
| aug1 | `fa10302` | 0,7/0,2/0,1 | 0,02/0,15/0,1/10° | 45 | 1,245 | 0,8 | 61% | 59% | 32,4% | 0,380 | 22/37 | [1gczddpd](https://forge.coreweave.com/wandb/hoagtin935-sai-gon-university/ViSign/runs/1gczddpd) |
| **aug2** | `fa10302` | 0,7/0,2/0,1 | 0,08/0,35/0,2/20° | 45 | **0,968** | 0,5 | **69%** | 57% | **43,2%** | **0,464** | 13/37 | [152s4gcd](https://forge.coreweave.com/wandb/hoagtin935-sai-gon-university/ViSign/runs/152s4gcd) |

Top-1 là tỉ lệ đoán đúng nghĩa trước khi áp ngưỡng. Recall từng nghĩa của aug2 trên test: Bạn 0,75; Cảm ơn 0,25;
Đau bụng 0,5; Đau đầu 0,6; Giấy tờ 0,5; Giúp đỡ 0,5; Không 0,4; Nhận 0,33; Sốt 0; Xin lỗi 0.

Cổng phát hành (macro-F1 ≥ 0,80, recall mỗi nghĩa ≥ 0,65): cả bốn bản đều trượt.

## 4. Link và artifact

| Loại | Link/path bền vững | Ghi chú |
|---|---|---|
| Commit diff | `https://github.com/HiImNVH/ViSign/commit/a083c02db74a3a17f15a8a1ce9ce1cea1e3bd6dd` | |
| GitHub Actions | `https://github.com/HiImNVH/ViSign/actions/runs/42447292058` | `quality` success |
| Report trong repo | `docs/evidence/checkpoints/CP5/T036-p2-tin-aug2-smoke.md` | File này |
| W&B | 3 link trong bảng trên, project `ViSign` | Chỉ có config, metric, hash và ảnh confusion matrix; không có video, landmark, manifest hay model |
| Data/model | `p0-local-v1`; manifest SHA-256 `3cc8ae84df600a5774b37201749965e12c77ebd81ed41cb8d92b38a4a5571ad1`; schema digest `6f1e32eeb8be9e6fbf3e13f7dded063ad9b4ea7ad387593ddfb658c66d92c389`; weights aug2 `9db78452ad82c119fbae540893c837360fe0b83fb818ea5f2245bbd885114cb5` | Artifact nằm ở `ai/artifacts/` (gitignored), không commit |

## 5. Rủi ro, rollback và handoff

- Rủi ro còn lại:
  - Mới chạy một seed, tập test chỉ 37 mẫu; aug2 hơn baseline 1 mẫu đúng trên test.
  - Bộ aug2 khá mạnh (xoay ±20°, tỉ lệ ±20%, thời gian ±35%), có thể làm lẫn ký hiệu phụ thuộc hướng tay.
  - Đổi mặc định cho mọi lần train full; thay đổi nằm ngoài scope P2.
- Rollback: xoá khối `augmentation` trong `ai/configs/p0-gru.yaml` (khoá tuỳ chọn) hoặc revert commit; artifact cũ
  không bị ảnh hưởng.
- Việc người kế tiếp cần làm:
  - P3 Cường/P1 Huy review thay đổi config.
  - Chạy ít nhất 5 seed để so aug2 với không augmentation.
  - Train lại khi có split chính thức T018 của P4 và thêm video cho Sốt, Xin lỗi.
  - Đề xuất P4/P1 thêm `data/manifests/*.csv text eol=lf` vào `.gitattributes` để 35 test dataset đạt trên Windows.
- Blocker: không.

## 6. Xác nhận

- [x] Owner đã chạy lại gate sau lần rebase cuối. Kiểm đồng bộ trước commit ra `1 0` vì remote có `58bcb28` (chỉ
  sửa web), nhưng commit local đã được tạo; đã rebase, kiểm lại config và Ruff, push ở `0 1`.
- [x] Không có secret, raw video, landmark bulk hoặc model binary bị stage.
- [x] Full SHA và link đã được điền sau push.
- [ ] Reviewer tái lập gate quan trọng và ghi kết quả bên dưới.
