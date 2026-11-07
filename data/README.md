# ViSign data workspace

Thư mục `data/` trong Git chỉ chứa manifest, schema và tài liệu có thể công khai. Raw video,
landmark/tensor đã sinh và model binary phải nằm ngoài repository hoặc trong đường dẫn đã được
`.gitignore` loại trừ.

## Raw material không đưa thẳng vào model

Pipeline chính thức:

```text
raw video
  -> audit nguồn/quyền sử dụng/nhãn
  -> decoder
  -> MediaPipe landmark extractor
  -> shared normalization + resampling + mask
  -> versioned tensor
  -> video-held-out split (theo video gốc)
  -> GRU training/evaluation
```

GRU không nhận pixel video trực tiếp. Training CLI và inference API phải dùng cùng extractor,
feature schema, thứ tự đặc trưng và preprocessing để tránh training-serving skew.

## Vị trí lưu local đề xuất

Ưu tiên một thư mục ngoài repository, ví dụ:

```text
D:\ViSign-Dataset\
├── incoming\       # Bản gốc bất biến, chưa kiểm duyệt
├── reviewed\       # Clip đã có quyết định audit
├── processed\      # Landmark/tensor sinh lại được
└── reports\        # Báo cáo local trước khi chọn phần được commit
```

Nếu dùng `data/raw/` hoặc `data/processed/` trong clone để thử cục bộ, các thư mục này đã bị ignore.
Luôn chạy `git status --short` và quét file stage trước commit.

Không đổi tên/bulk-normalize toàn bộ video trước khi T098 đóng băng quy ước tên file, normalization
và version. Giữ tên gốc cùng checksum trong inventory để truy nguồn.

### Tiếp nhận một nguồn dữ liệu mới

1. Giữ bản ZIP hoặc video nhận được ngoài repository, trong `incoming/`; không chỉnh sửa bản gốc.
2. Lập inventory riêng tư gồm tên gốc, SHA-256 đầy đủ, nguồn, ngày tiếp nhận, số clip và nhãn ứng viên.
   Có thể lấy checksum bằng `Get-FileHash -LiteralPath '<đường dẫn file>' -Algorithm SHA256`.
   Hash của ZIP dùng để nhận dạng bản bàn giao; ID từng clip phải dựa trên hash file clip theo T098.
3. Ghi lại căn cứ sử dụng cấp dataset theo quyết định lead bên dưới; với nguồn mới, lưu bằng chứng quyền sử dụng và quyết định audit. Tên thư mục, tên ZIP hoặc việc tải được
   video không chứng minh nhãn đúng, quyền huấn luyện hay consent của người xuất hiện.
4. Chỉ sao chép clip sang `reviewed/` khi có quyết định audit; giữ byte-identical với bản gốc.
   Chưa đóng T098 thì chưa bulk rename; đường dẫn chuẩn trong lead handoff là đích bàn giao sau
   khi quy ước được xác nhận, không yêu cầu sửa tên file gốc ngay khi tiếp nhận.
   Mẫu bị loại hoặc chờ bổ sung metadata được ghi trong báo cáo, không đưa vào training release.
5. Trước bàn giao, kiểm tra metadata, coverage, split và phiên bản schema. Việc có đủ 10 tên nhóm
   trong ZIP không chứng minh đã đủ dữ liệu full model.

Inventory, giấy consent, bảng nối mã người ký với người thật và bằng chứng chứa thông tin riêng tư
phải lưu ngoài Git với quyền truy cập giới hạn cho người phụ trách. Báo cáo công khai chỉ giữ mã ẩn
danh, nguồn công khai an toàn và kết quả audit tổng hợp.

## Metadata tối thiểu cho mỗi mẫu

Manifest dùng `rawPath` tương đối từ dataset root, dùng `/`; `sourceUri` là URL nguồn hoặc ID dataset.
Bộ P0 hiện tại có thể để trống `sourceUri` theo khai báo cấp dataset của lead. Không ghi token,
signed URL hoặc tên thật của người thực hiện vào bản công khai.

| Field | Yêu cầu |
|---|---|
| `sampleId` | Duy nhất, không chứa tên thật |
| `classLabel` | Tham chiếu lớp ký hiệu hợp lệ |
| `meaningId` | Một trong các ý nghĩa đã duyệt |
| `signerId` | Không bắt buộc; mã ẩn danh nếu xác định được người ký |
| `recordingSessionId` | Một video gốc; đơn vị chia train/validation/test |
| `sourceUri` | Nguồn hoặc ID dataset, không chứa credential |
| `licenseStatus` | `approved`, `restricted` hoặc `unknown` |
| `verificationStatus` | `verified`, `unverified` hoặc `rejected` |
| `rejectionReason` | Bắt buộc khi `verificationStatus=rejected` |
| `rawPath` | Path tương đối từ dataset root, dùng `/` |
| `landmarkPath` | Tùy chọn; path artifact sau trích xuất |
| `durationMs`, `frameCount` | Số nguyên dương đo từ decoder, không điền giả khi chưa đo |
| `split` | Rỗng trước audit/split; `train`, `validation`, `test` do T018 gán |

Vùng miền/variant nằm ở `SignClass` mà `classLabel` tham chiếu. Ánh xạ tiền tố vùng và số thứ tự
theo mục 8 của [lead handoff](../docs/team/data-convention.md); số thứ tự video không phải variant.
`recordingSessionId` theo video gốc; mọi clip cắt từ cùng video giữ chung ID để tránh leakage.

Chỉ mẫu `licenseStatus=approved` và không bị `rejected` mới được cân nhắc cho training release.
Mẫu chưa được người có chuyên môn xác minh phải giữ `verificationStatus=unverified`.

## Quyền sử dụng và quyền riêng tư

**Quyết định lead 2026-11-07**: raw material P0 hiện là video giáo dục trực tuyến công khai. Nguồn và
căn cứ sử dụng (học tập/nghiên cứu, lead duyệt) được khai **một lần** trong dataset card kèm tên website
nguồn; không bắt buộc ghi nguồn, giấy phép hay người ký cho từng video. Mẫu thuộc bộ này mặc định
`licenseStatus=approved`. Khi nhóm tự quay hoặc thêm nguồn khác, áp dụng đầy đủ danh sách dưới đây.

Với nguồn tự quay hoặc nguồn mới, trước khi đưa clip vào manifest approved, phải lưu được:

- nguồn và chủ sở hữu hoặc điều khoản dataset;
- quyền cho phép tải, xử lý, huấn luyện và trình diễn;
- consent phù hợp nếu nhóm tự quay người tham gia;
- phạm vi chia sẻ và thời hạn lưu nếu có;
- quyết định loại bỏ khi nguồn, nhãn hoặc quyền sử dụng không rõ.

Không commit raw video, ảnh frame, landmark bulk, thông tin nhận dạng cá nhân hoặc giấy tờ consent
có dữ liệu nhạy cảm. Repository chỉ lưu mã ẩn danh và báo cáo tổng hợp.

## Chia dữ liệu

Full quality gate chia theo video gốc (`recordingSessionId`): mọi clip cắt từ cùng một video nằm cùng
một tập. Raw material hiện không có danh tính người ký, nên report ghi `video-held-out` và không được
tuyên bố là unseen-signer test. Có `signerId` thì ưu tiên chia theo signer.
Không random split từng clip cắt độc lập: các clip từ cùng video gốc phải ở cùng tập.
Video-held-out không chứng minh tổng quát hóa sang người ký mới.

## Trình tự bàn giao Data -> AI

1. Quang lập inventory, khai nguồn/căn cứ sử dụng cấp dataset theo lead và audit nhãn; chưa bulk rename khi T098 chưa đóng băng.
2. Chọn nhóm clip đại diện đủ điều kiện xử lý để Cường chạy thử decoder/extractor và review
   handedness, normalization, schema v0.3; đây là evidence review, chưa phải artifact training.
3. Sau khi T098 đóng băng và schema được APPROVED, chạy validator và shared extractor hàng loạt
   trên manifest đã duyệt; đo metadata và review clip nhỏ có thể thực hiện trước đó.
4. Bàn giao manifest version/hash, class/meaning map, coverage, split audit và processed artifact ID.
5. Cường train/evaluate; Tín dùng cùng schema/pipeline để chạy parity và serving smoke.

Pilot có thể dùng tối đa ba ý nghĩa đã audit và luôn `demoReady=false`. Full release phải có đúng 10
ý nghĩa P0, video-held-out evaluation và vượt model quality gate trong spec.

## Những gì được phép commit trong `data/`

```text
data/
├── README.md
└── manifests/
    ├── p0-meanings.csv     # registry ý nghĩa đã duyệt
    ├── pilot.csv           # chỉ khi audit hoàn tất
    └── p0.csv              # chỉ khi full manifest hoàn tất
```

Manifest chưa hoàn thành không được tạo dữ liệu giả để làm task trông như đã xong. Ghi blocker và
coverage thiếu trong member log/dataset card thay vì tự suy đoán metadata.

### Kiểm tra trước khi đề nghị commit

Chạy từ repository root để xem trạng thái, diff và danh sách file đã stage:

```powershell
git status --short --untracked-files=all
git diff --check
git diff --cached --name-only
```

Mở và kiểm tra nội dung từng manifest/report được chọn; không stage hàng loạt thư mục dữ liệu.
ZIP, ảnh frame, giấy consent và CSV chứa thông tin riêng tư có thể không bị `.gitignore` chặn.
`.gitignore` không bảo vệ file đã được track hoặc được thêm bằng `git add -f`.
Không commit/push trước khi người dùng yêu cầu và các gate/checkpoint liên quan đạt.

## Tài liệu tham chiếu

- [SignSample và data model](../specs/001-vsl-recognition-mvp/data-model.md).
- [Quy ước lead bàn giao cho T098](../docs/team/data-convention.md): còn cần xác nhận, không được coi
  hướng dẫn T008 này là quyết định đóng băng D1–D4.
- [Hiến pháp dự án](../.specify/memory/constitution.md).
