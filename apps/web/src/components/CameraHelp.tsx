// apps/web/src/components/CameraHelp.tsx - Huong dan camera trong hop thoai native co quan ly focus.
import { useRef } from 'react';
import { vi } from '../content/vi';

export function CameraHelp() {
  const dialog = useRef<HTMLDialogElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  return <>
    <button ref={trigger} className="quiet-button" onClick={() => dialog.current?.showModal()}>Hướng dẫn</button>
    <dialog ref={dialog} className="app-dialog" aria-labelledby="help-title" onClose={() => trigger.current?.focus()}
      onKeyDown={event => {
        // The dialog has a single interactive control. Keep keyboard Tab focus inside it.
        if (event.key === 'Tab') {
          event.preventDefault();
          dialog.current?.querySelector<HTMLButtonElement>('button')?.focus();
        }
      }}>
      <div className="dialog-heading"><h2 id="help-title">Dịch ký hiệu trực tiếp</h2>
        <button className="quiet-button" onClick={() => dialog.current?.close()} aria-label="Đóng hướng dẫn">Đóng</button></div>
      <ol className="help-steps">
        <li><strong>Bật camera</strong><p>Nhấn “Bật camera” và cho phép trình duyệt sử dụng camera.</p></li>
        <li><strong>Vào khung hình</strong><p>Chọn nơi đủ sáng. Đưa khuôn mặt, thân trên và hai tay vào khung hình.</p></li>
        <li><strong>Thực hiện ký hiệu</strong><p>Đợi trạng thái “Sẵn sàng”, thực hiện từng ký hiệu rồi dừng tay một nhịp.</p></li>
        <li><strong>Xem kết quả</strong><p>Xem từ vừa dịch trên camera và các bản dịch trước ở mục lịch sử.</p></li>
        <li><strong>Tạm dừng hoặc tắt</strong><p>Nhấn biểu tượng tạm dừng để nghỉ, hoặc biểu tượng camera gạch chéo để tắt.</p></li>
      </ol>
      <p className="disclaimer">{vi.disclaimer}</p>
    </dialog>
  </>;
}
