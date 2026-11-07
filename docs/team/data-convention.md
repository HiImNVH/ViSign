# Quy ước tên, chuẩn hoá và version dữ liệu (lead handoff cho T098)

**Trạng thái**: Lead P1/Huy bàn giao ngày 2026-11-07; cập nhật cùng ngày theo quyết định nguồn/giấy
phép/người ký và ánh xạ tên file của Quang (mục 8). Quang (owner T098) và Cường (consumer) xác nhận
rồi đóng băng tại `docs/contracts/data-conventions.md`, `ai/src/visign_ai/dataset/manifest_schema.py`
và `ai/tests/dataset/test_manifest_validation.py`.

**Nguồn**: `specs/001-vsl-recognition-mvp/data-model.md`, [data/README.md](../../data/README.md),
[ai-backend-contract.md](ai-backend-contract.md) và mẫu nhãn của fixture legacy
(`XIN_CHAO_HCM_1`). Mục 7 là các quyết định lead bổ sung.

## 1. Định danh

| ID | Mẫu | Regex | Ví dụ |
|---|---|---|---|
| `meaningId` | Chữ hiển thị bỏ dấu, `Đ→D`, UPPER_SNAKE | `^[A-Z][A-Z0-9]*(_[A-Z0-9]+)*$` | `CAM_ON`, `DAU_DAU` |
| `classLabel` | `{meaningId}_{region}_{variant}`; variant là số nguyên ≥1, không đệm 0 | `^[A-Z][A-Z0-9]*(_[A-Z0-9]+)*_(HCM\|HN\|HP\|OTHER\|UNKNOWN)_[1-9][0-9]*$` | `CAM_ON_HN_1` |
| `sourceId` | Mã nguồn ngắn, lowercase kebab; bộ video giáo dục hiện tại dùng một mã chung | `^[a-z0-9]+(-[a-z0-9]+)*$` | `vsl-edu`, `self-rec` |
| `sampleId` | `{sourceId}_{12 hex đầu SHA-256 của file raw}` | `^[a-z0-9]+(-[a-z0-9]+)*_[0-9a-f]{12}$` | `vsl-edu_3fa2c19b0d7e` |
| `signerId` | Không bắt buộc. Khi xác định được: `S` + 3 chữ số, không suy ra từ tên | `^S[0-9]{3}$` | `S007` |
| `recordingSessionId` | Video gốc: bằng `sampleId` của video gốc; mọi clip cắt từ video đó dùng chung giá trị. Tự quay có signer: `{signerId}-R##` | `^([a-z0-9]+(-[a-z0-9]+)*_[0-9a-f]{12}\|S[0-9]{3}-R[0-9]{2})$` | `vsl-edu_3fa2c19b0d7e` |

- `sampleId` không chứa nhãn, nên sửa nhãn không đổi ID; trùng hash nghĩa là trùng file và phải loại.
- Bảng tra `signerId` ↔ người thật (nếu có) chỉ nằm ngoài repo, cùng giấy consent.
- `meaningId` đã đóng băng trong `data/manifests/p0-meanings.csv` không đổi tên. Muốn đổi phải qua
  registry change được review trước khi train.

## 2. File và thư mục ngoài repo

```text
<DATASET_ROOT>/
├── incoming/<sourceId>/<tên gốc>          # bất biến, không đổi tên
├── reviewed/<sourceId>/<sampleId>.<ext>   # bản sao byte-identical sau audit
├── processed/<featureSchemaVersion>/<sampleId>.npz
└── reports/
```

- `ext` viết thường, giữ đúng container gốc (`mp4`, `webm`, `mov`); không đổi đuôi để "giả" định dạng.
- Inventory ghi `originalFilename`, `sha256` đầy đủ và `sampleId` để truy ngược từ `incoming/`.
- `rawPath` trong manifest là path tương đối từ `<DATASET_ROOT>`, dùng `/`, ví dụ
  `reviewed/self-rec/self-rec_3fa2c19b0d7e.mp4`.

## 3. Chuẩn hoá

- **Video**: không resize, đổi fps, crop, flip hay re-encode trước extractor. Mọi chuẩn hoá hình học
  (tâm vai, scale, resample 32 bước) nằm trong pipeline schema dùng chung train/API.
- Ngoại lệ transcode chỉ khi decoder không đọc được file gốc: bản transcode là sample mới với
  `sampleId` từ hash bản transcode, ghi `derivedFrom=<sampleId gốc>` trong inventory.
- **CSV manifest**: UTF-8 không BOM, xuống dòng LF, phân cách `,`, có header, mỗi dòng một sample.
- Text tiếng Việt chuẩn hoá Unicode NFC, trim khoảng trắng; boolean `true`/`false`; ô rỗng nghĩa là null.
- `durationMs`, `frameCount` là số nguyên đo bằng decoder; thời gian theo ISO 8601 UTC.
- Cột `split` chỉ do công cụ split (T018) gán, không gán tay.

## 4. Manifest

| File | Nội dung | Điều kiện |
|---|---|---|
| `data/manifests/p0-meanings.csv` | Registry 10 meaning P0 | Đã đóng băng |
| `data/manifests/pilot.csv` | Tối đa 3 meaning đã audit | Sau audit nguồn/quyền |
| `data/manifests/p0.csv` | Đúng 10 meaning P0; split theo video gốc (FR-015) | Sau coverage + split audit |

Cột theo `SignSample` trong `data-model.md`, thêm `meaningId` như `data/README.md`. Chỉ
`licenseStatus=approved` và `verificationStatus≠rejected` được vào bản release. Bộ video giáo dục công
khai hiện tại khai nguồn/quyền một lần ở dataset card và để `licenseStatus=approved`; `sourceUri` và
`signerId` được để trống.

## 5. Version

- `datasetVersion` = `{tên manifest}-v{N}` với N nguyên tăng dần, ví dụ `pilot-v1`, `p0-v2`.
- Bất kỳ thay đổi dòng, nhãn, split hay quyền nào trong manifest đã bàn giao đều tăng N.
- Mỗi bản bàn giao ghi SHA-256 của file CSV; `model_info.json` ghi `datasetVersion`, dataset card ghi
  cả version và SHA-256. Không ghi đè một version đã giao cho training.
- Artifact đã xử lý phân theo `featureSchemaVersion`; đổi schema thì trích lại vào thư mục mới.

## 6. Validator khi đóng T098

- Regex mục 1 cho mọi ID; `classLabel` tham chiếu `meaningId` có trong registry.
- `sampleId` duy nhất, khớp hash file khi có quyền đọc dataset root.
- Encoding/NFC/header của CSV; enum `licenseStatus`, `verificationStatus`, `region`, `split`.
- `rejectionReason` bắt buộc khi `rejected`; không có `recordingSessionId` nào xuất hiện ở hai tập split khác nhau.
- Ví dụ hợp lệ và không hợp lệ cho từng luật trong test.

## 7. Quyết định lead bổ sung — cần Quang/Cường xác nhận

| # | Quyết định | Lý do |
|---|---|---|
| D1 | `classLabel` dạng `CAM_ON_HN_1` | Giữ tương thích fixture legacy và `data-model.md` |
| D2 | `sampleId` lấy từ `sourceId` + hash file, không chứa nhãn | Ổn định khi relabel, phát hiện trùng, không lộ danh tính |
| D3 | Không chuẩn hoá video trước extractor | Tránh training-serving skew; API nhận video camera gốc |
| D4 | `signerId` không bắt buộc (dạng `S###` khi có); `datasetVersion` dạng `{manifest}-v{N}` | Raw material không có danh tính người ký; split theo video gốc (FR-015) |

## 8. Ánh xạ tên file raw của Quang (chốt 2026-11-07)

Raw material P0 có 10 thư mục `<số>. <ý nghĩa>`, file đặt tên **`<VÙNG>_<NGHĨA>_<số>.mp4`**, ví dụ
`10. Không/HN_Không_3.mp4`. Tên gốc **giữ nguyên** trong `incoming/` (mục 2); manifest chuyển sang ID
chuẩn như sau.

| Phần trong tên | Ánh xạ | Ví dụ |
|---|---|---|
| `<VÙNG>` = `HCM`, `HN`, `HP` | `region` giữ nguyên | `HN_Không_3` → `HN` |
| `<VÙNG>` = `O` | `region=OTHER` (khác/không rõ vùng) | `O_Sốt_1` → `OTHER` |
| `<NGHĨA>` | `meaningId` theo bảng dưới | `Không` → `KHONG` |
| `<số>` | Số thứ tự video (sample), **không** phải biến thể động tác | `HN_Không_1..3` → 3 sample cùng `KHONG_HN_1` |
| Động tác khác nhau cùng nghĩa, cùng vùng | Variant 2, 3… do Quang đánh dấu trong inventory | `KHONG_HN_2` |

`classLabel` = `{meaningId}_{region}_{variant}`; mặc định `variant=1`. Mỗi video là một
`recordingSessionId` (= `sampleId` của video) nên các clip cắt từ cùng video không thể rơi vào hai tập
split (FR-015).

| Thư mục | Hiển thị | `meaningId` |
|---|---|---|
| 1. Giấy tờ (giấy) | Giấy tờ | `GIAY_TO` |
| 2. Đau bụng | Đau bụng | `DAU_BUNG` |
| 3. Sốt | Sốt | `SOT` |
| 4. Nhận | Nhận | `NHAN` |
| 5. Bạn | Bạn | `BAN` |
| 6. Cảm ơn | Cảm ơn | `CAM_ON` |
| 7. Giúp đỡ | Giúp đỡ | `GIUP_DO` |
| 8. Xin lỗi | Xin lỗi | `XIN_LOI` |
| 9. Đau đầu | Đau đầu | `DAU_DAU` |
| 10. Không | Không | `KHONG` |

Thuốc, Xin chào, Chờ (đợi), Sao chép, Tạm biệt, Tôi nằm ngoài P0; giữ ở `incoming/` cho giai đoạn mở rộng
và không đưa vào `p0.csv`. `data/manifests/p0-meanings.csv` (T013) phải dùng đúng bảng trên.

**Quang cần xác nhận**:

1. `O` nghĩa là khác/không rõ vùng (`OTHER`).
2. Video nào trong cùng thư mục là **động tác khác** (không chỉ quay lại) thì ghi variant trong inventory.
