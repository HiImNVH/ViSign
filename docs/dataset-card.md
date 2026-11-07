# Dataset card — T076 / T083 handoff

Ngày 2026-11-08. Registry có 10 Meaning P0; pilot dùng `GIAY_TO` và `NHAN`.

## Pilot đã bàn giao

15 clip, 4 class, train/validation/test = **7/4/4**. Người dùng trực tiếp xác nhận
trong lượt review nguồn: **“15 file vừa liệt kê là tự quay hết.”** Vì vậy,
`dataset:self-recorded` là nguồn đúng của cả 15 clip trong pilot này; không suy
nguồn cho pilot chỉ từ việc bộ DRAFT lớn hơn chứa cả video website.
Mỗi sample ID/file có dòng provenance và evidence riêng trong
[pilot-source-provenance.csv](evidence/dataset/t076-t083-handoff/pilot-source-provenance.csv).
Đây là khai báo người cung cấp; không báo thành chứng cứ xác minh độc lập mới.

[pilot.csv](../data/manifests/pilot.csv) và `pilot-v1.csv` là manifest raw đã duyệt;
`pilot-v2.csv` giữ nguyên nhãn, nguồn, ID và split, chỉ bổ sung `landmarkPath`.
Hash 15/15 PASS và data gate PASS. Metadata ở
[pilot-handoff.metadata.json](../data/manifests/pilot-handoff.metadata.json).
Raw và feature root do reviewer cung cấp local; không có video, NPZ hoặc model trong Git.

13 nhóm video nguồn theo khai báo, 12 mẫu chưa biết signer. Split là
`video-held-out`, không phải bằng chứng unseen-signer. Các lớp/mẫu verified của
pilot kế thừa hồ sơ duyệt chuyên môn do người dùng nhận trách nhiệm trước đó;
lần sửa nguồn này không tự duyệt nhãn hoặc tạo consent mới.

## DRAFT toàn bộ dữ liệu

[p0-source-v5.DRAFT.csv](../data/manifests/p0-source-v5.DRAFT.csv) có 101 mẫu:
**76 tự quay, 25 nguồn công khai**, không còn ô `sourceUri` trống. Trong các mẫu
công khai, URL clip cụ thể được giữ khi có evidence; các mẫu chỉ được xác nhận
website dùng `https://nnkh.thaiphong.net/`, không tự đoán URL MP4.
Bốn nguồn bổ sung có provenance tại [source-v5-changes.json](evidence/dataset/source-v5-changes.json).
Không dùng nguồn website để suy rằng người cung cấp tự quay hoặc có chứng cứ
quyền mới; `licenseStatus` kế thừa các khai báo/quyết định đã ghi nhận.

Hash 101/101 PASS. **101 mẫu vẫn unverified**, 19 class chưa duyệt/active;
fullTrainingEligible=false. Full target là 200 video, 12/5/3 mỗi meaning;
metadata/quota/class coverage còn chặn. Không xuất approved `p0.csv` và không
coi số lượng video hoặc khả năng decode là bằng chứng chất lượng nhận diện.

## Luật chia và giới hạn

FR-015 trên main giữ mọi clip của cùng `recordingSessionId` trong một tập, kể cả
khác meaning. `signerId` không bắt buộc, kể cả full; solver ưu tiên nhóm signer
khi khả thi và fallback về video gốc với trạng thái ghi rõ. Nhận `verified` và
`unverified`, giữ nguyên trạng thái; chặn `rejected`, license chưa approved,
class chưa duyệt và session leakage. Không nâng nhãn để làm gate xanh.

T083 run `kbj3bpvu` đã được P3 đánh giá lại trên main: accuracy 25%, Macro-F1
0,3333 trên 4 test, `demoReady=false`. Mẫu ít và thiếu signer giới hạn khả năng
đánh giá tổng quát hóa; model chỉ chứng minh pipeline pilot chạy được.
Đây là bản bàn giao dữ liệu để review, không tự đóng T076/T083 hoặc dependency admin.
