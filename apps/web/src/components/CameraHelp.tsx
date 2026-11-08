// apps/web/src/components/CameraHelp.tsx - Huong dan camera trong hop thoai native co quan ly focus.
import { useRef } from 'react';
import { vi } from '../content/vi';
import { captureLimits } from '../features/recognition/cameraSession';

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
        <li><strong>Chuẩn bị khung hình</strong><p>Chọn nơi đủ sáng. Để khuôn mặt, phần thân trên và hai tay trong khung.</p></li>
        <li><strong>Bật camera</strong><p>Cho phép camera trong trình duyệt. Khi thấy đủ người, mặt và tay, trạng thái chuyển sang Sẵn sàng.</p></li>
        <li><strong>Ký hiệu tự nhiên</strong><p>ViSign tự ghi khi tay bắt đầu chuyển động và tự dừng khi tay đứng yên khoảng một giây. Mỗi ký hiệu tối đa {captureLimits.maximumCaptureMs / 1000} giây.</p></li>
        <li><strong>Đọc bản dịch</strong><p>Kết quả được nối vào bản dịch trực tiếp. Dừng một nhịp giữa các ký hiệu để ViSign tách đúng.</p></li>
        <li><strong>Tạm dừng hoặc tắt</strong><p>Tạm dừng để ngừng ghi mà vẫn giữ camera; Tắt camera để giải phóng thiết bị.</p></li>
      </ol>
      <p className="privacy-note">{vi.privacy}</p><p className="disclaimer">{vi.disclaimer}</p>
    </dialog>
  </>;
}
