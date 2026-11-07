# T089 · Đánh giá độ bền và từ chối

## Phạm vi đã kiểm

Smoke trên Windows dùng Uvicorn, detector thật và GRU T036 huấn luyện từ tensor
tổng hợp. Hai WebM trống đen/trắng đều trả `422 NO_PERSON_DETECTED`. Sáu clip
review có người đi qua pipeline và đều trả HTTP 200. Chưa có nhãn đã audit cho
lượt này nên không tính sáu clip vào mẫu số false accept hoặc độ chính xác VSL.
[Bằng chứng HTTP](evidence/checkpoints/CP5/T065-p3-cuong-smoke.md)

API kiểm đầu vào và landmark trước GRU. Khi có tensor đủ điều kiện, GRU chọn
lớp có softmax cao nhất. Nếu confidence đạt hoặc bằng ngưỡng của artifact và
lớp có chữ hiển thị, API chấp nhận. Kết quả dưới ngưỡng bị từ chối. Softmax
cần được kiểm nghiệm trên ký hiệu ngoài phạm vi trước khi diễn giải độ tin cậy.
[Luật quyết định](../services/inference-api/src/visign_api/inference/prediction_decision.py)

## Chạy với artifact đã đánh giá

1. Cố định artifact, model version, class map và threshold đã chọn trên validation.
   Giữ video test và probe OOD độc lập với train/validation. Lấy ký hiệu ngoài
   danh mục, cử chỉ không phải VSL và clip không có người. Với mẫu trong danh mục,
   audit nhãn và phủ người ký mới, các mức ánh sáng và góc camera. Giữ biến thể
   của cùng video nguồn trong cùng nhóm khi chia dữ liệu.
2. Chạy qua endpoint thật. Ghi một dòng cho mỗi lượt. Đặt `expectedMeaning` trống
   cho OOD đã xác minh, ghi loại ở `oodKind` và để cột đó trống với mẫu trong
   danh mục. Với response accepted, tra `classLabel` qua class map
   và ghi `predictedMeaning`. Ghi `rejected` cho quyết định từ chối có chủ đích,
   gồm `NO_PERSON_DETECTED` và `INSUFFICIENT_LANDMARKS`. Ghi `error` cho timeout,
   lỗi hạ tầng, response bất nhất và lỗi kỹ thuật khác. Giữ nguyên probe ID và
   điều kiện giữa các lượt lặp cùng input. Dùng nhóm người ký ẩn danh và cột
   metadata theo đúng header bên dưới, tránh lưu tên, clip, landmark hoặc signer ID.
3. Chạy scorer và đọc số mẫu cùng tỷ lệ từng nhóm. False accept là số OOD
   được chấp nhận chia cho số OOD có quyết định. Lỗi được đếm riêng và tỷ lệ là
   `null` nếu chưa có quyết định. Tỷ lệ đúng theo nghĩa tính trên toàn bộ lượt
   có nhãn, kể cả lượt lỗi/từ chối. Lượt lặp có lỗi được ghi `incomplete`.
   Báo coverage theo nghĩa, người ký, ánh sáng và góc. Mẫu ít hoặc mất cân
   bằng giới hạn kết luận về bias và độ ổn định.

```text
probeId,modelVersion,expectedMeaning,predictedMeaning,outcome,oodKind,signerGroup,lighting,angle
```

```powershell
uv run --locked --project ai python -m visign_ai.evaluation.robustness --probes PATH/probes.csv --output PATH/robustness.json
uv run --locked --project ai pytest ai/tests/evaluation/test_safety_robustness.py -q
```

## Còn thiếu để nghiệm thu

T089 đã có smoke với artifact VSL thật. Còn chờ probe đã audit và bằng chứng qua UI cho các nhóm
điều kiện. Cần báo cáo false accept theo loại OOD, số clip và người ký theo
nhóm, tỷ lệ đúng theo nghĩa, lỗi kỹ thuật và độ ổn định qua lặp. Các test scorer
dùng dữ liệu mô phỏng để kiểm công thức và quy tắc xử lý lỗi.


## Smoke trên pilot VSL Giấy tờ / Nhận

P3 chạy trên `2182f85`, API FastAPI cục bộ bằng TestClient, artifact `t083-pilot-v2-approved`, detector MediaPipe thật. Cùng sáu WebM review T014–T016 và hai WebM trống đen/trắng được gửi qua `POST /api/v1/predictions` với `detector_prewarm_enabled` tắt rồi bật.

- Sáu clip có người trả HTTP 200 ở cả hai nhánh. Bốn được chấp nhận theo threshold và hai bị từ chối. Các clip này dùng để đối chiếu hành vi phục vụ.
- Hai clip trống đều trả HTTP 422 `NO_PERSON_DETECTED` ở cả hai nhánh. False accept trên hai probe trống là 0/2 mỗi nhánh.
- 8/8 cặp khớp HTTP status, mã lỗi hoặc nhãn, nội dung, `accepted`, confidence và model version. Sáu lượt HTTP 200 đo 1,715–3,034 s khi tắt và 1,811–2,370 s khi bật. Đây là phép chạy tuần tự trên máy local, chưa phải đối chứng p95 production.

T089 còn mở để đánh giá OOD có người ký, góc máy, ánh sáng và độ ổn định theo người ký trên bộ probe đã audit. [Kết quả đánh giá pilot](pilot-report.md)

## Probe bổ sung trên pilot thật

P3 chạy trên `c73c8b3` với `t083-pilot-v2-approved` qua FastAPI TestClient, detector thật và prewarm bật. Chọn 5 clip ngoài phạm vi theo nhãn inventory T076 và trạng thái nguồn `exact-byte-match` (1 Sốt, 3 Cảm ơn, 1 Xin lỗi). SHA-256 của cả 5 clip khớp inventory. Nhãn ngoài phạm vi dùng theo inventory, chưa qua xác nhận chuyên môn riêng cho bộ probe này.

Chuyển MP4 sang WebM VP8 ở tốc độ frame trung bình của nguồn. Chạy thêm 4 clip test T083, mỗi clip có bản chuyển mã nguyên sáng và bản nhân giá trị RGB với 0,45 trước mã hóa. 13/13 request trả HTTP 200, gồm cả các lượt model từ chối theo ngưỡng.

| Nhóm | Kết quả |
|---|---|
| Ký hiệu ngoài phạm vi | 1/5 nhận nhầm. Một clip Cảm ơn được nhận thành Giấy tờ ở confidence 0,5207 với ngưỡng 0,5. |
| Clip test trong phạm vi, nguyên sáng sau chuyển mã | 2/4 đúng, 2/4 từ chối. |
| Cùng 4 clip, giảm sáng tổng hợp | 3/4 đúng, 1/4 từ chối. Một clip Giấy tờ đổi từ từ chối sang nhận đúng. |

Đây là phép thử thăm dò. Mẫu quá nhỏ để suy ra tác động của ánh sáng hoặc tỷ lệ nhận nhầm ngoài thực tế. Các kết quả WebM qua API là phép đo riêng với đánh giá T083 trên NPZ. T089 vẫn cần mẫu có người nhưng không ký, góc máy, nhóm người ký và chạy lặp qua UI. Scorer T089: 4/4 test đạt.
