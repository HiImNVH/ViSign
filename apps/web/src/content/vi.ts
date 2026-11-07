// apps/web/src/content/vi.ts - Noi dung camera va thong bao loi tieng Viet.
export const cameraErrors = {
  denied: ['Chưa có quyền sử dụng camera', 'Cho phép camera trong cài đặt của trang trên trình duyệt rồi thử lại.'],
  unavailable: ['Không tìm thấy camera được hỗ trợ', 'Kết nối camera và mở ứng dụng bằng Chrome hoặc Edge.'],
  insecure: ['Không thể bật camera tại địa chỉ này', 'Mở ứng dụng qua localhost hoặc địa chỉ HTTPS.'],
  disconnected: ['Camera đã mất kết nối', 'Kiểm tra thiết bị rồi bật lại camera. Đoạn đang quay đã được hủy.'],
  busy: ['Không mở được camera', 'Đóng ứng dụng khác đang dùng camera, kiểm tra thiết bị rồi thử lại.'],
  recordingUnsupported: ['Trình duyệt chưa hỗ trợ ghi hình WebM', 'Mở ứng dụng bằng Chrome hoặc Edge rồi thử lại.'],
  recordingFailed: ['Không hoàn tất được đoạn quay', 'Bật lại camera và quay một ký hiệu mới.'],
  tooShort: ['Đoạn quay quá ngắn', 'Thực hiện trọn một ký hiệu trước khi nhấn Kết thúc.'],
  tooLong: ['Đoạn quay vượt thời lượng cho phép', 'Quay lại một ký hiệu ngắn hơn.'],
  tooLarge: ['Đoạn quay vượt giới hạn dung lượng', 'Quay lại một ký hiệu ngắn hơn.'],
  unknown: ['Không mở được camera', 'Kiểm tra quyền camera và thiết bị rồi thử lại.'],
} as const;

export type CameraError = keyof typeof cameraErrors;

// Client-owned, stable guidance. Never render an API error's raw message or code.
export const predictionErrors = {
  apiRouteNotFound: 'Không tìm thấy chức năng API. Vui lòng kiểm tra phiên bản dịch vụ.',
  apiMethodNotAllowed: 'Ứng dụng và dịch vụ chưa tương thích. Vui lòng tải lại trang.',
  apiForbidden: 'Bạn không có quyền thực hiện thao tác này.', // Reserved for a future contract.
  network: 'Chưa kết nối được dịch vụ nhận diện. Kiểm tra kết nối rồi thử gửi lại.',
  timeout: 'Dịch vụ phản hồi quá lâu. Thử gửi lại hoặc quay một ký hiệu mới.',
  invalidResponse: 'Chưa nhận được kết quả nhận diện hợp lệ. Vui lòng thử lại.',
  codes: {
    INVALID_REQUEST: 'Yêu cầu nhận diện chưa hợp lệ. Hãy quay ký hiệu mới rồi gửi lại.',
    UNSUPPORTED_MEDIA_TYPE: 'Định dạng đoạn quay chưa được hỗ trợ. Hãy quay lại bằng Chrome hoặc Edge.',
    CLIP_TOO_LARGE: 'Đoạn quay vượt giới hạn dung lượng. Quay lại một ký hiệu ngắn hơn.',
    CLIP_TOO_SHORT: 'Đoạn quay quá ngắn. Hãy quay trọn một ký hiệu rồi gửi lại.',
    CLIP_TOO_LONG: 'Đoạn quay quá dài. Hãy quay lại một ký hiệu ngắn hơn.',
    NO_PERSON_DETECTED: 'Chưa phát hiện người trong khung hình. Đưa khuôn mặt và hai tay vào khung hình rồi quay lại.',
    INSUFFICIENT_LANDMARKS: 'Chưa thấy rõ tay và cơ thể. Điều chỉnh ánh sáng, giữ hai tay trong khung hình rồi quay lại.',
    CLIP_DECODE_FAILED: 'Không đọc được đoạn quay. Hãy quay một ký hiệu mới rồi gửi lại.',
    SERVICE_BUSY: 'Dịch vụ đang bận. Vui lòng chờ một lát rồi thử gửi lại.',
    MODEL_NOT_READY: 'Dịch vụ nhận diện chưa sẵn sàng. Vui lòng thử lại sau.',
    PREDICTION_FAILED: 'Dịch vụ chưa xử lý được đoạn quay. Thử gửi lại hoặc quay ký hiệu mới.',
  },
} as const;

export const vi = {
  title: 'Ngôn ngữ ký hiệu Việt Nam',
  preview: 'Hình ảnh xem trước từ camera',
  privacy: 'Không ghi âm. Chỉ quay khi bạn chủ động chọn. Đoạn quay chỉ được gửi đến dịch vụ nhận diện khi bạn bấm Gửi nhận diện.',
  disclaimer: 'ViSign là công cụ hỗ trợ thử nghiệm. Kết quả có thể không chính xác và không thay thế phiên dịch viên chuyên nghiệp trong tình huống quan trọng.',
  transcript: {
    title: 'Bản dịch trực tiếp',
    description: 'Các ý nghĩa được ghép theo thứ tự nhận diện; chưa phải câu dịch có ngữ pháp.',
  },
  history: {
    open: 'Lịch sử', title: 'Lịch sử bản dịch', close: 'Đóng lịch sử',
    disclosure: 'Chỉ lưu trên thiết bị này trong 24 giờ. Không gửi lịch sử lên máy chủ.',
    empty: 'Chưa có bản dịch được lưu.',
    unavailable: 'Bộ nhớ trình duyệt không khả dụng. Bạn vẫn có thể nhận diện và xem bản dịch trực tiếp.',
    clear: 'Xoá toàn bộ lịch sử',
    confirm: 'Xoá tất cả lịch sử và bản dịch trực tiếp của phiên này?',
    confirmYes: 'Xác nhận xoá', cancel: 'Giữ lại',
    clearFailed: 'Không xoá được lịch sử trên thiết bị. Vui lòng kiểm tra quyền lưu trữ rồi thử lại.',
    confidence: 'Độ tin cậy', model: 'Model',
  },
  recognition: {
    send: 'Gửi nhận diện',
    sending: 'Đang nhận diện…',
    modelLoading: 'Đang tải thông tin model để gửi nhận diện…',
    modelUnavailable: 'Chưa kết nối được dịch vụ nhận diện. Bạn vẫn có thể quay ký hiệu.',
    reloadModel: 'Thử kết nối lại',
    submitError: 'Không thể nhận diện đoạn quay này. Thử gửi lại hoặc quay ký hiệu mới.',
    rejected: 'Chưa nhận diện được ký hiệu. Hãy quay một ký hiệu mới.',
    confidence: 'Độ tin cậy',
    shortDisclaimer: 'Kết quả thử nghiệm, có thể không chính xác.',
    modelNotReady: {
      fixture: 'Tích hợp nội bộ (fixture), chưa sẵn sàng demo.',
      pilot: 'Thí điểm giới hạn (pilot), chưa sẵn sàng demo.',
      full: 'Model hiện tại chưa đạt điều kiện demo chính thức.',
    },
    meanings: 'Ý nghĩa hỗ trợ',
    noMeanings: 'Chưa công bố ý nghĩa hỗ trợ.',
  },
  states: {
    idle: 'Camera chưa bật', permission: 'Đang chờ quyền camera', preview: 'Camera sẵn sàng',
    recording: 'Đang quay ký hiệu', stopping: 'Đang hoàn tất đoạn quay', captured: 'Đã quay xong', error: 'Camera gặp lỗi',
  },
} as const;
