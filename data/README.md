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

## Metadata tối thiểu cho mỗi mẫu

Manifest được commit có thể tham chiếu path tương đối hoặc ID kho dữ liệu, nhưng không chứa token,
signed URL hoặc tên thật của người thực hiện.

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
| `rawPath` | Path local tương đối hoặc storage object ID |
| `durationMs`, `frameCount` | Giá trị đo từ decoder, không chỉ tin metadata client |

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
Không random split theo video vì sẽ gây leakage đặc điểm người và phiên quay.

## Trình tự bàn giao Data -> AI

1. Quang lập inventory và audit nguồn/quyền/nhãn, chưa bulk rename khi T098 còn blocked.
2. Chọn một nhóm clip đại diện để Cường review decoder, handedness, normalization và schema v0.3.
3. Sau khi schema được APPROVED, chạy validator và shared extractor trên manifest đã duyệt.
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
