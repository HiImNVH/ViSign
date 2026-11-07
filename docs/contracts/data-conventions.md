# T098 — Quy ước dữ liệu để review

Ngày đối chiếu: **2026-11-08**. **IMPLEMENTED_PENDING_REVIEW**, chưa FROZEN.
Nguồn yêu cầu: [lead handoff](../team/data-convention.md),
[data model](../../specs/001-vsl-recognition-mvp/data-model.md),
[spec](../../specs/001-vsl-recognition-mvp/spec.md).
Đây là bản contract ở repo chính; không giả định worktree T098 đã được merge hoặc được reviewer duyệt.

| Mục | Quy ước được code kiểm tra |
|---|---|
| D1 / meaning | Upper snake case, đúng 10 P0 trong registry; không đổi ID khi relabel sample |
| D1 / class | `{meaningId}_{HCM|HN|HP|OTHER|UNKNOWN}_{variant}`; variant ≥1, không đệm 0 |
| D2 / source | lowercase kebab; mã nguồn không tự chứng minh tác giả hay license |
| D2 / sample | `{sourceId}_{sha256(raw)[:12]}`; hash khớp file; không có raw trùng byte |
| D3 / video | Giữ nguyên byte nguồn, không resize/crop/flip/re-encode trước extractor; mọi derivation cần lineage và ID mới |
| D4 / signer | `S###`, ẩn danh, chỉ cấp theo bằng chứng cùng người; tùy chọn ở full gate |
| Session | `sampleId` của video gốc hoặc `S###-R##` theo repo VSign; sourceId-R## không còn được nhận |
| Version | `{manifest}-v{N}`, N ≥1, không ghi đè bản đã bàn giao; thay manifest phải cấp version mới bởi owner |
| Paths | Tương đối từ dataset root, `/`, không traversal/absolute/symlink escape; không ghi video vào Git |
| CSV | UTF-8 không BOM, LF, newline cuối, NFC, trim; header đúng thứ tự `MANIFEST_COLUMNS` |
| Metadata | duration 300–6000 ms, frameCount >0; giá trị đo thật, không tạo số giả |
| Trạng thái | License approved/restricted/unknown; verification verified/unverified/rejected; rejected cần reason |
| Nguồn bàn giao | Từng clip khai URL/tên nguồn công khai hoặc dataset:self-recorded; không để trống trong manifest bàn giao này |

Không gán variant bằng hậu tố thứ tự filename. Mọi đoạn cắt cùng video nguồn phải giữ chung
group, kể cả khác meaning. Các session độc lập cùng signer có thể ở khác split; không suy ra unseen-signer.
Hash/session ID khác nhau không chứng minh signer khác nhau.

## Điểm đã đối chiếu và cần người review xác nhận

- Đối chiếu repo VSign ngày 2026-11-08: recordingSessionId nhận hash sample ID gốc
  hoặc S###-R##. Đã bỏ mở rộng sourceId-R## của snapshot cũ; inventory/manifest dùng chung regex.
- D1–D4, cách giữ session hash và tính tương thích extractor cần Cường/Huy review
  trước khi ghi FROZEN. Chưa có biên bản xác nhận của hai người trong gói hiện tại.
- `rejectionReason` hiện là text không rỗng; spec chưa ban hành enum cụ thể.
- Manifest v4 vẫn `unverified`, catalog 19 lớp `verified=false,active=false`.
  Giá trị license approved kế thừa tuyên bố người giao, chưa chứng minh chứng cứ bên thứ ba.

## Cổng dữ liệu

T012 metadata không phê duyệt training. Pilot tối đa 3 nghĩa, lớp đã verified, mẫu verified hoặc unverified,
lớp active, nguồn/quyền phù hợp, mỗi lớp có ba split. Full yêu cầu đúng 10 nghĩa,
200 video, 12/5/3 trên từng meaning, recordingSessionId không leakage, signerId tùy chọn.
T018 chỉ viết manifest mới khi nghiệm khả thi qua post-validation T012; không đổi
nguồn/nhãn/trạng thái/ID. T056 kiểm thử giữ nhóm xuyên meaning, class coverage,
quota chính xác, dataset root/hash và session-only không được claim unseen-signer.

## Bằng chứng

[Báo cáo bàn giao Quang](../reviews/t076-t083-data-handoff.md),
[manifest v5 nháp](../../data/manifests/p0-source-v5.DRAFT.csv),
[class catalog nháp](../../data/manifests/sign-classes-review.DRAFT.csv).
Các test ở `ai/tests/dataset/`; code ở `ai/src/visign_ai/dataset/`.
Không có consent chứa danh tính, video, landmark bulk hoặc model binary trong gói review.

## Quyết định Huy áp dụng cho T013/T018/T056/T098 (2026-11-08)

- Full và pilot giữ tất cả clip cùng `recordingSessionId` (video gốc) trong một split,
  kể cả xuyên meaning; `signerId` tùy chọn. Evidence là `video-held-out`, không phải
  bằng chứng unseen-signer generalization.
- Mẫu `verified` và `unverified` đều được nhận khi `licenseStatus=approved`;
  loại `rejected`. Không tự nâng unverified thành verified. Lớp vẫn cần được duyệt.
- Parser giữ tương thích metadata legacy theo main. Riêng bản bàn giao hiện hành
  khai nguồn từng clip, không để trống `sourceUri`; URL trang chủ là nguồn do người
  cung cấp xác nhận, không được coi là exact clip URL hoặc bằng chứng quyền mới.
- `sample-review.csv` có `decision=pending`; reviewer, quyết định nhãn/quyền và
  bằng chứng con người để trống tới khi có review thật. Không coi test pass là ký duyệt.
- Full target giữ 10 nghĩa, mỗi nghĩa 12 train / 5 validation / 3 test; quota và
  cách ly video gốc không được bù bằng nhân bản video. Model quality gate kiểm riêng.

## Bàn giao v2 đối chiếu VSign (2026-11-08)

Nguồn đối chiếu D:/Hojc/Hackathon/VSign chỉ đọc. FR-015 ưu tiên signer khi biết:
solver thử gộp các video cùng signer, nếu không đạt quota/class coverage hoặc hết
ngân sách tìm kiếm thì quay về chia theo video gốc. Báo signerPreference và trạng
thái lần thử; video gốc luôn không leakage, splitEvidence vẫn video-held-out.
Manifest mới p0-source-v5.DRAFT.csv có nguồn từng clip: tự quay dùng
`dataset:self-recorded`, công khai dùng URL clip hoặc tên/URL nguồn theo xác nhận.
Không để trống nguồn trong bản bàn giao này; bốn nguồn chưa có URL clip chính xác
được ghi URL website theo xác nhận trước của người dùng, chưa đối chiếu độc lập.
Ngoại lệ cho phép sourceUri trống ở schema không có nghĩa là phải bỏ metadata đã biết.
Không đưa training_inputs.py, landmarks, video, .task, model.pt vào gói tích hợp.
