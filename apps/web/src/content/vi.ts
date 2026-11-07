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

export const vi = {
  title: 'Ngôn ngữ ký hiệu Việt Nam',
  preview: 'Hình ảnh xem trước từ camera',
  privacy: 'Không ghi âm. Chỉ quay khi bạn chủ động chọn. Đoạn quay chỉ được gửi đến dịch vụ nhận diện khi bạn bấm Gửi nhận diện.',
  disclaimer: 'ViSign là công cụ hỗ trợ thử nghiệm. Kết quả có thể không chính xác và không thay thế phiên dịch viên chuyên nghiệp trong tình huống quan trọng.',
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
