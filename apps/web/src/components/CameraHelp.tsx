// apps/web/src/components/CameraHelp.tsx - Huong dan camera trong hop thoai native co quan ly focus.
import { useRef } from 'react';
import { vi } from '../content/vi';

export function CameraHelp() {
  const dialog = useRef<HTMLDialogElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  return <>
    <button ref={trigger} className="quiet-button" onClick={() => dialog.current?.showModal()}>Hướng dẫn</button>
    <dialog ref={dialog} className="help-dialog" aria-labelledby="help-title" onClose={() => trigger.current?.focus()}>
      <div className="dialog-heading"><h2 id="help-title">Quay một ký hiệu rõ ràng</h2>
        <button className="quiet-button" onClick={() => dialog.current?.close()} aria-label="Đóng hướng dẫn">Đóng</button></div>
      <ol className="help-steps">
        <li><strong>Chuẩn bị khung hình</strong><p>Chọn nơi đủ sáng. Để khuôn mặt, phần thân trên và hai tay trong khung.</p></li>
        <li><strong>Bật camera khi sẵn sàng</strong><p>Cho phép camera trong trình duyệt. Bật camera chỉ mở hình xem trước.</p></li>
        <li><strong>Quay một ký hiệu</strong><p>Chọn Quay ký hiệu, thực hiện động tác rồi chọn Kết thúc. Đoạn quay tự dừng sau 5 giây.</p></li>
        <li><strong>Gửi khi sẵn sàng</strong><p>Chọn Gửi nhận diện để gửi đoạn quay tới dịch vụ. Nếu không muốn gửi, bạn có thể hủy đoạn quay.</p></li>
        <li><strong>Chủ động hủy hoặc tắt</strong><p>Hủy đoạn quay để bỏ clip và tiếp tục xem trước. Tắt camera để giải phóng thiết bị.</p></li>
      </ol>
      <p className="privacy-note">{vi.privacy}</p><p className="disclaimer">{vi.disclaimer}</p>
    </dialog>
  </>;
}
