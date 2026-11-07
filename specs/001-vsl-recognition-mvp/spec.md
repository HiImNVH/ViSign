# Feature Specification: ViSign VSL Recognition MVP

**Feature Branch**: `001-vsl-recognition-mvp`

**Created**: 2026-10-19

**Status**: Ready for planning

**Release Version**: `0.0.1`

**API Version**: `v1` — mọi public endpoint nằm dưới `/api/v1`; release version không đổi namespace API.

**Input**: User description: "Xây dựng ViSign, một ứng dụng web thử nghiệm nhận diện Ngôn ngữ Ký hiệu Việt Nam và chuyển từng ký hiệu riêng lẻ thành chữ tiếng Việt, ưu tiên biến thể TP.HCM, có độ tin cậy và trạng thái không nhận diện được."

## Clarifications

### Session 2026-10-19

- Q: Bản MVP đầu tiên phải nhận diện ổn định bao nhiêu ý nghĩa tiếng Việt? → A: 10 từ P0; 20 từ còn lại mở rộng sau. Danh sách 10 từ được chốt sau khi thành viên phụ trách hoàn tất lọc và bổ sung raw material.
- Q: MVP đầu tiên phải nhận ký hiệu từ nguồn đầu vào nào? → A: Video được dùng cho huấn luyện và đánh giá; sản phẩm nhận hình ảnh trực tiếp từ camera để kiểm tra đầu ra. Không có luồng người dùng tải video lên để dự đoán trong MVP đầu tiên.
- Q: Mô hình 10 từ phải đạt mức chất lượng tối thiểu nào trên tập kiểm thử gồm những người không xuất hiện trong tập huấn luyện? → A: Macro-F1 tối thiểu 80% và recall của từng từ tối thiểu 65%.

### Session 2026-10-22

- Q: Quang đã chọn những ý nghĩa nào cho phạm vi P0? → A: Giấy tờ (giấy), Đau bụng, Thuốc, Sốt, Nhận, Bạn (Ngôi thứ 2), Xin chào, Cảm ơn, Chờ (đợi), Sao chép.

### Session 2026-11-08

- Q: Có kiểm thử usability với ≥ 10 người thuộc nhóm mục tiêu (T071) không? → A: **Không.** Lead bỏ T071 vì
  sản phẩm là bản trình chiếu chấm điểm, chưa có người dùng thật. Mọi tài liệu MUST NOT nêu kết quả usability;
  bằng chứng trải nghiệm chỉ gồm audit accessibility (T063), audit FE/UX (T088) và kiểm webcam thật của nhóm.

### Session 2026-11-07

- Q: Raw material P0 không có danh tính người ký và nguồn là video giáo dục trực tuyến công khai; quality
  gate chia tập thế nào? → A: Chia theo video gốc. Mỗi video gốc là một `recordingSessionId`; mọi clip
  cắt từ cùng video nằm cùng một tập. Báo cáo gắn nhãn `video-held-out` và không tuyên bố unseen-signer.
  Nếu sau này xác định được `signerId`, split theo signer được ưu tiên.
- Q: Nguồn và quyền sử dụng ghi ở mức nào? → A: Ghi một lần ở mức bộ dữ liệu: video giáo dục trực tuyến
  công khai, lead duyệt dùng cho học tập/nghiên cứu; dataset card ghi tên website nguồn. Không bắt buộc
  ghi nguồn, giấy phép và người ký cho từng video.
- Q: Danh sách 10 ý nghĩa P0 sau khi Quang lọc lại raw material? → A: Vẫn đúng 10 ý nghĩa, thay thế danh
  sách 2026-10-22: Giấy tờ (giấy), Đau bụng, Sốt, Nhận, Bạn, Cảm ơn, Giúp đỡ, Xin lỗi, Đau đầu, Không.
  Thuốc, Xin chào, Chờ (đợi), Sao chép chuyển sang giai đoạn mở rộng. File raw đặt tên
  `<VÙNG>_<NGHĨA>_<số thứ tự video>.mp4`.
- Q: Pilot dùng cặp nghĩa nào khi "Chờ" đã ra khỏi P0? → A: **Sốt + Cảm ơn** (`SOT`, `CAM_ON`): khác nhóm
  y tế/giao tiếp nên dễ tách động tác, có trong fixture và trong bộ PTIT CC-BY-4.0 nếu cần bổ sung mẫu.
  **Cập nhật 2026-11-08 (lead):** pilot đổi sang **Giấy tờ + Nhận** (`GIAY_TO`, `NHAN`) vì đây là bộ đã có
  dữ liệu đã duyệt (15 clip, 4 lớp vùng); kết quả chỉ là bằng chứng pipeline smoke, không claim chất lượng.
  Nguồn dữ liệu gồm cả video giáo dục công khai lẫn video nhóm tự quay: `sourceUri` MUST ghi đúng nguồn từng clip.
  Các nghĩa P0 có số nguồn ngang nhau nên chọn theo độ tách biệt.

- Q: Người dùng cần xem bản dịch trực tiếp và xem lại bản dịch đã có trong ít nhất bao lâu? → A: Lead
  2026-11-07 đưa vào MVP: (1) **bản dịch trực tiếp** ghép các kết quả `accepted` liên tiếp thành một dòng
  văn bản trong phiên (chỉ ghép từ, không suy diễn ngữ pháp, không nhận diện câu liên tục); (2) **lịch sử
  bản dịch** lưu **chỉ trên trình duyệt** ít nhất 24 giờ rồi tự xoá, gồm chữ hiển thị, thời điểm, độ tin
  cậy và `modelVersion`; không lưu video, frame, landmark và không lưu trên server.

### Session 2026-10-24

- Q: Bảng `user` trong database cần đại diện cho đối tượng nào? → A: Chỉ thành viên nội bộ; MVP không có tài khoản người dùng cuối, lịch sử nhận diện hoặc database runtime. Sau khi đánh giá, phạm vi database được bỏ và chỉ cập nhật API contract.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Nhận diện một ký hiệu (Priority: P1)

Một người dùng thực hiện một ký hiệu riêng lẻ trước camera. ViSign phân tích lần thực hiện và hiển thị
ý nghĩa bằng tiếng Việt cùng mức độ tin cậy.

**Why this priority**: Đây là giá trị cốt lõi và là luồng tối thiểu để ViSign có thể được trình diễn.

**Independent Test**: Chọn một ký hiệu thuộc phạm vi MVP, thực hiện một lần và xác nhận hệ thống trả
đúng chữ tiếng Việt, độ tin cậy và trạng thái chấp nhận.

**Acceptance Scenarios**:

1. **Given** người dùng đã cho phép sử dụng nguồn hình ảnh và chọn bắt đầu, **When** người dùng thực
   hiện một ký hiệu hợp lệ rồi kết thúc, **Then** hệ thống hiển thị ý nghĩa tiếng Việt, độ tin cậy và
   trạng thái đã nhận diện.
2. **Given** hai biến thể vùng miền khác nhau cùng mang một ý nghĩa, **When** mỗi biến thể được nhận
   diện, **Then** cả hai lần đều hiển thị cùng một nội dung tiếng Việt.
3. **Given** người dùng từ chối quyền camera hoặc nguồn hình ảnh không thể đọc, **When** bắt đầu nhận
   diện, **Then** hệ thống giải thích lỗi và hướng dẫn cách thử lại mà không bị treo.

---

### User Story 2 - Từ chối kết quả không chắc chắn (Priority: P1)

Một người dùng thực hiện động tác không thuộc phạm vi, không rõ ràng hoặc không có người trong khung
hình. ViSign không đoán bắt buộc mà trả về “Không nhận diện được”.

**Why this priority**: Một dự đoán sai nhưng được trình bày như chắc chắn có thể gây hiểu nhầm, đặc
biệt trong bối cảnh y tế hoặc hành chính.

**Independent Test**: Gửi một đoạn không có ký hiệu hợp lệ và xác nhận hệ thống không trả về một từ
thuộc từ điển như thể đó là kết quả chắc chắn.

**Acceptance Scenarios**:

1. **Given** độ tin cậy thấp hơn ngưỡng chấp nhận, **When** hệ thống hoàn thành phân tích, **Then** kết
   quả là “Không nhận diện được” và trạng thái không được chấp nhận.
2. **Given** đoạn ghi hình quá ngắn, quá dài, không có người hoặc tay ra khỏi khung, **When** người dùng
   gửi yêu cầu, **Then** hệ thống trả thông báo cụ thể và cho phép thử lại.
3. **Given** hệ thống nhận diện không sẵn sàng, **When** người dùng gửi một lần nhận diện, **Then** giao
   diện thông báo dịch vụ chưa sẵn sàng và không hiển thị dự đoán giả.
4. **Given** frontend gọi sai đường dẫn hoặc sai phương thức API, **When** backend trả lỗi định tuyến,
   **Then** giao diện hiển thị thông báo tiếng Việt ổn định, không lộ thông báo framework và không tự
   gửi lại video; đường dẫn chỉ khác dấu gạch chéo được chuẩn hóa mà không đổi phương thức request.

---

### User Story 3 - Đánh giá chất lượng bản MVP (Priority: P2)

Thành viên nhóm hoặc người đánh giá có thể xác định bản ViSign đang dùng tập từ nào, phiên bản mô hình
nào và chất lượng đã được kiểm thử ra sao trước khi chấp nhận bản demo.

**Why this priority**: Demo chỉ đáng tin cậy khi kết quả có thể truy về phạm vi dữ liệu và bằng chứng
đánh giá, thay vì dựa trên một vài ví dụ thuận lợi.

**Independent Test**: Kiểm tra một bản phát hành và xác nhận có danh sách ý nghĩa hỗ trợ, phiên bản dữ
liệu, phiên bản mô hình, chỉ số đánh giá và ngày đánh giá.

**Acceptance Scenarios**:

1. **Given** một bản mô hình được đề xuất cho MVP, **When** người đánh giá xem thông tin bản phát hành,
   **Then** họ thấy phạm vi từ vựng, phiên bản dữ liệu, cách chia tập và các chỉ số bắt buộc.
2. **Given** dữ liệu kiểm thử có người thực hiện mới, **When** chạy đánh giá, **Then** báo cáo tách riêng
   kết quả này và không trộn mẫu cùng phiên quay giữa huấn luyện và kiểm thử.
3. **Given** model đầy đủ 10 ý nghĩa chưa huấn luyện xong, **When** frontend và backend cần tích hợp,
   **Then** hệ thống có thể dùng fixture hoặc pilot model qua cùng contract, công bố đúng tập ý nghĩa
   đang hỗ trợ và luôn giữ `demoReady=false` cho đến khi full model vượt qua mọi quality gate.

### User Story 4 - Kiểm tra dữ liệu và chạy pilot nội bộ (Priority: P2)

Thành viên nhóm có quyền có thể kiểm tra clip/landmark, kiểm tra bản bàn giao dữ liệu, chạy một job
pilot GRU và xem lại lịch sử hoặc liên kết W&B mà không đưa công cụ này vào luồng người dùng.

**Why this priority**: Công cụ đã có trên nhánh tích hợp và giúp lặp nhanh pipeline dữ liệu-model,
nhưng không được trở thành đường tắt bỏ qua audit dữ liệu hoặc quality gate của bản full.

**Independent Test**: Bật công cụ bằng mã admin cục bộ, kiểm tra một clip, chạy preflight rồi train
pilot trên bộ Giấy tờ–Nhận; xác nhận chỉ một job hoạt động, có trạng thái/báo cáo, và kết quả vẫn
`demoReady=false`.

**Acceptance Scenarios**:

1. **Given** công cụ admin chưa được bật hoặc mã truy cập sai, **When** gọi API nội bộ, **Then** hệ
   thống từ chối mà không lộ token, đường dẫn nhạy cảm hoặc stack trace.
2. **Given** bản bàn giao pilot hợp lệ, **When** nhóm chạy preflight, **Then** hệ thống kiểm tra hash,
   manifest, schema, tensor và coverage trước khi cho phép train.
3. **Given** một job đang chuẩn bị, train hoặc đánh giá, **When** yêu cầu tạo job khác, **Then** hệ
   thống từ chối; job hiện tại tiếp tục và trạng thái có thể đọc lại.
4. **Given** pilot hoàn tất, **When** xem lịch sử, **Then** nhóm thấy dataset/run ID, số mẫu, epoch,
   metrics và W&B online/offline evidence; pilot không được trình bày là model phát hành.

---

### User Story 5 - Nghiệm thu theo tiêu chí hội đồng (Priority: P1)

Ban giám khảo có thể truy từ từng tiêu chí chấm điểm đến bằng chứng chạy được của sản phẩm, dữ liệu,
mô hình, kiến trúc, cloud, chi phí và đóng góp của từng thành viên.

**Why this priority**: Sản phẩm chỉ được đánh giá đầy đủ khi giá trị, tính khả thi và chất lượng kỹ
thuật được chứng minh bằng artifact tái lập thay vì chỉ trình bày bằng lời.

**Independent Test**: Một người đánh giá không tham gia phát triển dùng ma trận tiêu chí để mở đúng
báo cáo, chạy smoke test trên URL production và xác minh mỗi nhóm điểm có bằng chứng tương ứng.

**Acceptance Scenarios**:

1. **Given** bảng điểm 100 điểm, **When** người đánh giá mở hồ sơ nghiệm thu, **Then** mọi tiêu chí đều
   có owner, task, artifact và trạng thái `TODO|PARTIAL|READY` rõ ràng.
2. **Given** một model được trình diễn, **When** xem hồ sơ model, **Then** người đánh giá thấy lý do lựa
   chọn, phương pháp thực nghiệm tái lập, chỉ số, giới hạn, thiên lệch, kiểm thử trường hợp biên và cơ
   chế từ chối dự đoán không chắc chắn.
3. **Given** bản production được đề xuất, **When** truy cập URL công khai, **Then** hệ thống dùng HTTPS,
   giữ secret ngoài mã nguồn, có health check, log/monitoring và vượt qua smoke test ổn định.
4. **Given** phần thuyết trình và phản biện, **When** hỏi về giá trị, dữ liệu, mô hình, chi phí, giới hạn
   hoặc khả năng mở rộng, **Then** nhóm trả lời bằng số liệu và bằng chứng đã lưu trong repository.

### User Story 6 - Bản dịch trực tiếp và lịch sử 24 giờ (Priority: P2)

Người dùng thấy các ý nghĩa vừa được chấp nhận nối thành một dòng văn bản đang hiển thị, và có thể xem
lại các bản dịch đã có trên cùng thiết bị trong ít nhất 24 giờ mà không cần tài khoản.

**Why this priority**: Giúp người nghe theo dõi chuỗi ý nghĩa trong một lượt giao tiếp và xem lại sau đó,
nhưng không thay đổi luồng nhận diện từng ký hiệu của US1/US2.

**Independent Test**: Với fixture predictor, nhận diện hai ký hiệu `accepted` và một lần `rejected`, kiểm
tra dòng bản dịch chỉ chứa hai chữ đã chấp nhận; tải lại trang thấy lịch sử còn; giả lập đồng hồ +24 giờ
thì mục cũ bị xoá.

**Acceptance Scenarios**:

1. **Given** hai lần nhận diện được chấp nhận liên tiếp, **When** kết quả trả về, **Then** dòng bản dịch
   trực tiếp hiển thị hai chữ theo đúng thứ tự, kết quả bị từ chối không được nối vào.
2. **Given** đã có bản dịch, **When** người dùng tải lại trang trong vòng 24 giờ, **Then** lịch sử vẫn
   hiển thị chữ, thời điểm, độ tin cậy và phiên bản model.
3. **Given** một mục lịch sử đã quá 24 giờ, **When** ứng dụng mở hoặc cập nhật lịch sử, **Then** mục đó bị
   xoá khỏi bộ nhớ trình duyệt.
4. **Given** người dùng chọn "Xoá lịch sử", **When** xác nhận, **Then** toàn bộ lịch sử và dòng bản dịch
   trong phiên bị xoá ngay.
5. **Given** trình duyệt chặn bộ nhớ cục bộ, **When** nhận diện, **Then** bản dịch trực tiếp vẫn hoạt động
   và ứng dụng thông báo lịch sử không khả dụng thay vì lỗi.

### Edge Cases

- Camera bị từ chối quyền, bị thiết bị khác chiếm dụng hoặc mất kết nối giữa lần ghi.
- Đoạn ghi hình không có người, có nhiều người, tay rời khung hoặc khuôn mặt/cơ thể bị che khuất.
- Đoạn ghi hình quá ngắn, quá dài, sai định dạng hoặc hỏng.
- Người dùng thực hiện ký hiệu không thuộc phạm vi MVP hoặc chuyển tiếp giữa hai ký hiệu.
- Hai lớp vùng miền có cùng ý nghĩa nhưng độ tin cậy gần nhau.
- Dịch vụ nhận diện hoặc bản mô hình chưa sẵn sàng.
- Mạng chậm hoặc yêu cầu bị gián đoạn trước khi có kết quả.
- Nguồn dữ liệu bị phát hiện sai nhãn, không phải VSL hoặc không rõ quyền sử dụng.
- Model phản hồi không ổn định với signer/ánh sáng/góc quay chưa gặp hoặc nhóm dữ liệu kém đại diện.
- Cloud deploy lỗi cấu hình, secret bị thiếu, chi phí vượt ngân sách hoặc URL production không ổn định.
- Hai thành viên cùng push checkpoint làm lệch `main` hoặc bằng chứng không khớp commit đã trình diễn.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống MUST xử lý một ký hiệu riêng lẻ trong mỗi lần nhận diện; hội thoại liên tục nằm
  ngoài phạm vi MVP này.
- **FR-002**: Phạm vi phát hành đầu tiên MUST hỗ trợ đúng 10 ý nghĩa P0 đã đóng băng trong
  `data/manifests/p0-meanings.csv`: Giấy tờ (giấy), Đau bụng, Sốt, Nhận, Bạn, Cảm ơn, Giúp đỡ,
  Xin lỗi, Đau đầu và Không (chốt lại 2026-11-07). Hai mươi ý nghĩa còn lại thuộc giai đoạn mở rộng sau khi
  pipeline 10 từ đạt cổng chất lượng.
- **FR-003**: Sản phẩm MVP MUST nhận đầu vào dự đoán trực tiếp từ camera. Video có sẵn MUST chỉ đi
  qua pipeline dữ liệu để huấn luyện và đánh giá; giao diện người dùng tải video lên để dự đoán nằm
  ngoài phạm vi phát hành đầu tiên.
- **FR-004**: Người dùng MUST có thể chủ động bắt đầu, kết thúc, gửi hoặc hủy một lần nhận diện.
- **FR-005**: Hệ thống MUST ánh xạ mọi lớp ký hiệu được hỗ trợ về đúng nội dung tiếng Việt; mã lớp và
  vùng miền không được hiển thị như kết quả chính cho người dùng.
- **FR-006**: Hệ thống MUST ưu tiên biến thể TP.HCM và MAY hỗ trợ biến thể vùng khác khi động tác khác
  và nguồn dữ liệu phù hợp.
- **FR-007**: Hệ thống MUST trả về nội dung tiếng Việt, độ tin cậy và trạng thái chấp nhận cho mỗi lần
  phân tích thành công.
- **FR-008**: Hệ thống MUST trả “Không nhận diện được” khi quyết định chấp nhận không đạt tiêu chí đã
  công bố hoặc đầu vào không đủ điều kiện; hệ thống MUST NOT buộc chọn một từ.
- **FR-009**: Hệ thống MUST phân biệt lỗi request, định dạng không hỗ trợ, clip không giải mã được,
  dịch vụ đang bận, quyền thiết bị, model chưa sẵn sàng và kết quả không chắc chắn bằng mã lỗi ổn định
  cùng thông báo dễ hiểu.
- **FR-010**: Giao diện MUST hiển thị cảnh báo rằng ViSign là sản phẩm thử nghiệm, kết quả có thể không
  chính xác và không thay thế phiên dịch viên chuyên nghiệp trong tình huống quan trọng.
- **FR-011**: Hệ thống MUST NOT lưu video nhận diện của người dùng sau khi trả kết quả nếu chưa có sự
  đồng ý rõ ràng.
- **FR-012**: Mỗi mẫu huấn luyện được chấp nhận MUST có ý nghĩa, nhãn lớp, vùng miền, video gốc
  (`recordingSessionId`) và trạng thái xác minh. Nguồn và điều kiện sử dụng MAY được khai một lần ở mức
  bộ dữ liệu khi toàn bộ nguồn cùng loại (xem Clarifications 2026-11-07).
- **FR-013**: Hệ thống MUST loại khỏi dữ liệu được phê duyệt các mẫu sai nhãn, không phải VSL hoặc
  không rõ quyền sử dụng.
- **FR-014**: Mỗi bản mô hình được chấp nhận MUST gắn với phiên bản dữ liệu, extractor/feature schema,
  danh sách lớp, cách chia tập, ngày đánh giá và báo cáo gồm accuracy, precision, recall, Macro-F1,
  confusion matrix, latency cùng loại split đã dùng (`video-held-out` hoặc signer-held-out).
- **FR-015**: Quality gate chính thức MUST dùng tập kiểm thử tách theo video gốc (`recordingSessionId`):
  mọi clip cắt từ cùng một video MUST nằm cùng một tập train, validation hoặc test. Khi có `signerId`,
  split theo signer được ưu tiên. Kết quả `video-held-out` MUST được gắn nhãn đúng loại split và MUST NOT
  được trình bày là bằng chứng unseen-signer.
- **FR-016**: Bản MVP MUST đạt Macro-F1 tối thiểu 80% và recall của từng ý nghĩa tối thiểu 65% trên
  tập kiểm thử tách theo FR-015 để được chấp nhận cho demo.
- **FR-017**: Đăng nhập, lịch sử nhận diện **lưu trên server** hoặc đồng bộ giữa thiết bị, chuyển văn bản
  thành giọng nói, chuyển văn bản thành ký hiệu và nhận diện chuỗi câu MUST nằm ngoài phạm vi MVP này.
  Bản dịch trực tiếp và lịch sử cục bộ 24 giờ theo FR-034–FR-036 là ngoại lệ đã được lead duyệt.
- **FR-018**: Hệ thống MUST cho phép thay thế `fixture`, `pilot` và `full` model artifact qua cùng
  predictor/API contract. Fixture và pilot MUST công bố đúng tập ý nghĩa đang hỗ trợ, MUST hiển thị là
  bản tích hợp nội bộ và MUST NOT được đánh dấu `demoReady=true`; chỉ full model đủ 10 ý nghĩa và đạt
  FR-016 mới được phát hành làm model demo.
- **FR-019**: Mọi API response MUST trả `X-Request-ID`; prediction thành công MAY trả phân rã thời gian
  `decode/extract/infer` và chỉ báo chất lượng đầu vào `handsDetectedRatio/frameCount`. Các trường chẩn
  đoán này MUST NOT thay thế trạng thái `accepted`, MUST NOT chứa frame/landmark và MUST NOT được persist.
- **FR-020**: API MUST trả error envelope ổn định có cùng request ID cho route không tồn tại và phương
  thức không được hỗ trợ; redirect chuẩn hóa đường dẫn MUST giữ nguyên phương thức và body. Giao diện
  MUST dùng đường dẫn chuẩn, MUST NOT hiển thị raw framework message và MUST phân biệt lỗi tương thích
  API với camera permission hoặc kết quả nhận diện bị từ chối. `403` chỉ được dùng khi có chính sách
  phân quyền thật; cache validation chỉ được bật sau khi contract invalidation được công bố.
- **FR-021**: Công cụ kiểm tra/train nội bộ MUST nằm ngoài luồng người dùng, chỉ được bật khi có
  `VISIGN_ADMIN_TOKEN`, không commit token, và MUST xóa clip kiểm tra cùng thư mục tạm sau khi trả file
  kết quả hoặc gặp lỗi.
- **FR-022**: Mỗi pilot run MUST kiểm tra bản bàn giao dữ liệu, hash, feature schema và coverage trước
  train; hệ thống MUST chỉ cho một job ở trạng thái active, lưu trạng thái/báo cáo theo run ID và MUST
  giữ `demoReady=false` bất kể metrics pilot.
- **FR-023**: Hồ sơ nghiệm thu MUST ánh xạ đủ 100 điểm chấm sang task, owner, artifact và bằng chứng;
  mọi tuyên bố sáng tạo hoặc khả thi MUST nêu điểm khác biệt, đối tượng sử dụng và giới hạn thực tế.
- **FR-024**: Dataset card MUST công bố nguồn gốc, tính hợp pháp, chất lượng, độ đại diện, phương thức
  thu thập/xử lý và mọi khoảng trống coverage có thể gây thiên lệch.
- **FR-025**: Model card và test report MUST giải thích lý do chọn mô hình, protocol thực nghiệm có thể
  tái lập, độ ổn định trên trường hợp biên/OOD, cơ chế từ chối kết quả, thiên lệch và giới hạn giải thích.
- **FR-026**: Repository MUST có cấu trúc module rõ, kiểm tra code tự động, build/test tự động và một
  pipeline phát hành chỉ chạy khi các quality gate bắt buộc đạt.
- **FR-027**: Bản phát hành MUST bảo vệ video/secret, kiểm tra lỗ hổng dependency và cấu hình, có health
  check, timeout, rate/resource boundary, logging an toàn và kế hoạch rollback.
- **FR-028**: Hồ sơ sản phẩm MUST đánh giá tác động cộng đồng, khả năng tiếp cận, nhóm hưởng lợi, rủi ro
  gây hiểu nhầm và phương án mở rộng sau MVP mà không phóng đại hiệu quả hiện có.
- **FR-029**: Nhóm MUST đo CPU, RAM, thời gian, lưu trữ, network và chi phí cloud của luồng chính; báo
  cáo MUST so sánh ít nhất một phương án tối ưu và giải thích cân bằng chi phí-chất lượng-tốc độ.
- **FR-030**: ViSign MUST có một bản production trên AWS hoặc Google Cloud với URL công khai ổn định,
  HTTPS, biến môi trường/secret an toàn, cấu hình tài nguyên và smoke/rollback runbook.
- **FR-031**: Mỗi thành viên MUST có thư mục làm việc riêng để ghi task, bằng chứng và bàn giao; nhóm
  MUST lưu lịch sử đóng góp và chuẩn bị demo/Q&A về bài toán, giải pháp, AI, dữ liệu, mô hình, chi phí,
  giới hạn và khả năng triển khai.
- **FR-032**: Việc tích hợp MUST diễn ra trên `main` theo checkpoint nhỏ, một người push tại một thời
  điểm, pull/rebase trước push, chạy gate tương ứng và không force-push; full code dump một lần không
  được tính là quy trình bàn giao hợp lệ.
- **FR-033**: Trước khi đóng data/API foundation, nhóm MUST tiếp nhận và đóng băng bộ quy ước do lead
  cung cấp cho tên/chuẩn hóa file dữ liệu và FE-BE API; manifest validator, OpenAPI và client types
  MUST cùng tham chiếu một phiên bản quy ước, không tự đặt các biến thể riêng.
- **FR-034**: Giao diện MUST hiển thị bản dịch trực tiếp bằng cách nối chữ hiển thị của các kết quả
  `accepted` trong phiên theo thứ tự thời gian; kết quả `rejected` và lỗi MUST NOT được nối. Đây chỉ là
  ghép từ, MUST NOT trình bày như dịch câu có ngữ pháp.
- **FR-035**: Lịch sử bản dịch MUST chỉ lưu trên trình duyệt của người dùng, giữ mỗi mục **ít nhất 24 giờ**
  rồi tự xoá khi quá hạn, chỉ gồm `text`, thời điểm, `confidence`, `modelVersion` và `requestId`; MUST NOT
  lưu video, frame, landmark hoặc gửi lịch sử lên server.
- **FR-036**: Giao diện MUST cho biết lịch sử được lưu trên thiết bị này trong 24 giờ, cung cấp nút xoá toàn
  bộ lịch sử, và MUST tiếp tục hoạt động khi bộ nhớ trình duyệt bị chặn hoặc đầy.

### Key Entities *(include if feature involves data)*

- **Ý nghĩa tiếng Việt**: Nội dung hiển thị cho người dùng, ví dụ “Cảm ơn” hoặc “Đau bụng”; một ý
  nghĩa có thể liên kết với nhiều lớp ký hiệu.
- **Lớp ký hiệu**: Một động tác ký hiệu khác biệt dùng để nhận diện, gồm mã lớp, ý nghĩa đích, vùng
  miền và trạng thái xác minh.
- **Mẫu ký hiệu**: Một đoạn ghi hình hoặc đặc trưng đã trích xuất, gồm nguồn, người thực hiện ẩn danh,
  phiên quay, quyền sử dụng, nhãn và trạng thái kiểm duyệt.
- **Lần nhận diện**: Một lần người dùng cung cấp đầu vào, gồm trạng thái xử lý, kết quả tiếng Việt,
  độ tin cậy, trạng thái chấp nhận và mã lỗi nếu có; video không được lưu mặc định.
- **Phiên bản mô hình**: Bản nhận diện có định danh, phiên bản dữ liệu, danh sách lớp, ngưỡng chấp
  nhận, chỉ số đánh giá và ngày tạo.
- **Bản dịch đã lưu**: Một kết quả được chấp nhận lưu trên trình duyệt gồm chữ hiển thị, thời điểm,
  độ tin cậy, phiên bản model và request ID; tự hết hạn sau 24 giờ, không chứa video hay landmark.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Ít nhất 90% người thử nghiệm có thể hoàn thành một lần nhận diện hợp lệ mà không cần
  người phát triển hướng dẫn trực tiếp.
- **SC-002**: Sau khi người dùng kết thúc và gửi ký hiệu, 95% lần thử hợp lệ hiển thị kết quả hoặc lỗi
  có thể xử lý trong không quá 3 giây trên môi trường demo đã công bố.
- **SC-003**: 100% lần thử không đạt decision rule đã công bố hiển thị “Không nhận diện được” thay vì
  một từ được khẳng định chắc chắn; báo cáo MUST nêu rõ rule, threshold và tập đánh giá đã dùng.
- **SC-004**: Bản mô hình demo đạt ngưỡng chất lượng được chốt trong FR-016 trên tập kiểm thử tách theo
  FR-015 và có báo cáo theo từng lớp.
- **SC-005**: Bộ dữ liệu dùng cho bản mô hình demo công bố nguồn và căn cứ quyền sử dụng (ở mức bộ dữ
  liệu hoặc từng mẫu); mọi mẫu chưa được chuyên gia xác minh được đánh dấu rõ.
- **SC-006**: Không có video nhận diện của người dùng được lưu sau khi trả kết quả trong luồng mặc định.
- **SC-007**: Luồng demo bắt buộc chạy thành công với ít nhất ba ý nghĩa thuộc các nhóm giao tiếp, y tế
  và hành chính, đồng thời có một lần thử không hợp lệ được từ chối đúng.
- **SC-008**: 100% kiểm thử route không tồn tại, phương thức không hợp lệ và chuẩn hóa trailing slash
  trả đúng trạng thái, giữ correlation ID cần thiết và hiển thị stable Vietnamese copy thay vì raw
  server/framework text.
- **SC-009**: Luồng admin nội bộ vượt qua kiểm thử disabled/unauthorized, cleanup, preflight,
  single-active-job và history; một run pilot hoàn tất có báo cáo truy vết nhưng không thể tự nâng
  model thành `demoReady=true`.
- **SC-010**: Ma trận nghiệm thu ánh xạ 100% tiêu chí của bảng điểm đến ít nhất một task và một artifact
  kiểm chứng; không còn tiêu chí ở trạng thái không có owner.
- **SC-011**: 100% checkpoint được push chỉ sau khi quality gate tương ứng đạt và hồ sơ thành viên ghi
  commit, lệnh test, kết quả cùng handoff; lịch sử không có force-push hoặc một commit full-code dump.
- **SC-012**: Bản production có URL HTTPS công khai, vượt qua health, prediction smoke, error-path và
  rollback rehearsal; các secret không xuất hiện trong repository hoặc log.
- **SC-013**: Một thành viên khác có thể tái lập dataset audit, model evaluation và báo cáo benchmark
  từ hướng dẫn đã công bố mà không cần sửa mã nguồn thủ công.
- **SC-014**: Báo cáo cuối ghi CPU/RAM/latency/chi phí cho luồng demo, tác động cộng đồng, kết quả
  accessibility/usability và đóng góp có bằng chứng của cả 5 thành viên.
- **SC-015**: Sau khi lead bàn giao quy ước, 100% file dữ liệu audit được kiểm bằng cùng naming/
  normalization rules và 100% FE-BE contract tests/client fields khớp service contract đã đóng băng.
- **SC-016**: 100% kết quả `accepted` trong phiên xuất hiện đúng thứ tự trong bản dịch trực tiếp; lịch sử
  còn sau khi tải lại trang trong 24 giờ, mục quá 24 giờ bị xoá, và kiểm tra bộ nhớ trình duyệt/network
  không tìm thấy video, landmark hoặc lịch sử gửi lên server.
## Assumptions

- MVP nhận diện từng ký hiệu riêng lẻ, không diễn giải ngữ pháp hoặc chuỗi câu.
- Video raw material được dùng để xây dựng tập huấn luyện và đánh giá; camera trực tiếp là nguồn đầu
  vào duy nhất của luồng dự đoán dành cho người dùng trong MVP đầu tiên.
- Người dùng mục tiêu là người sử dụng VSL và người nghe cần hiểu một số ý nghĩa thiết yếu trong bối
  cảnh giao tiếp, y tế và hành chính.
- Biến thể TP.HCM được ưu tiên; biến thể vùng khác vẫn có thể được giữ thành lớp riêng và ánh xạ về
  cùng một nội dung tiếng Việt.
- Một mẫu từ nguồn trực tuyến có thể được dùng ở giai đoạn thử nghiệm nếu quyền sử dụng phù hợp, nhưng
  phải mang trạng thái chưa xác minh cho đến khi được người có chuyên môn đối chiếu.
- Danh sách 10 ý nghĩa P0 được Quang chốt lại ngày 2026-11-07 (thay bản 2026-10-22); việc chốt danh mục không đồng nghĩa các
  video mẫu đã được duyệt. Từng mẫu vẫn phải qua lọc nhãn, kiểm tra quyền sử dụng và phân tích độ phủ.
- Mức 20–30 mẫu mỗi lớp chỉ là planning floor để chạy pilot, không phải bằng chứng dữ liệu đã đủ;
  quyết định full training dựa trên coverage theo meaning × video gốc và split audit. Raw material hiện
  là video giáo dục trực tuyến công khai, không có danh tính người ký.
- Bản cloud là yêu cầu chấm điểm; bản chạy cục bộ và artifact đã smoke-test được giữ làm phương án
  rollback cho buổi trình diễn.
- Nhóm dùng một repository `HiImNVH/ViSign`, không dùng nhánh vai trò dài hạn; mỗi người có clone cục
  bộ và thư mục `members/pN-name/`, còn source chính vẫn nằm trong các module chuẩn của monorepo.
- Lead sẽ gửi sau bộ quy ước đặt tên/chuẩn hóa file dữ liệu và quy ước API FE-BE. Các task T098–T099
  được giữ `blocked` về nội dung cho đến khi nhận tài liệu, nhưng những phần không phụ thuộc vẫn làm được.
