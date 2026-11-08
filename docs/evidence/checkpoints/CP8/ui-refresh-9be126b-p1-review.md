# Review — P5 Hiển `9be126b` "refine live camera and translation history UI"

**Ngày**: 2026-11-08 · **Reviewer**: P1/Huy · **Kết quả**: `CHANGES_REQUESTED`

## Independent review — P1/Huy

**CI đỏ trên `32f5149`**: job Web lỗi ESLint `react-hooks/exhaustive-deps` ở `apps/web/src/App.tsx:30`. P1 sửa tối thiểu
(tách `liveStatus/paused/start/resume/pause/stop` ra trước `useEffect`, không đổi hành vi) để mở lại CI.

**Playwright (Edge, `npm run check`) — 12 test của chính commit này fail trên cả 3 viewport** (CI không chạy Playwright
nên không bắt được):

| Test | Lỗi quan sát |
|---|---|
| `history-sidebar.spec.ts:3` camera and persistent history share desktop space | Bố cục: giá trị đo 14, test yêu cầu < 2 |
| `history-sidebar.spec.ts:37` bounded pagination and clear-confirmation focus | Màu `rgb(22, 132, 71)` thay vì `rgb(36, 120, 212)` |
| `transcript-history.spec.ts:48` T104 two accepted clips… | Nội dung lịch sử khác kỳ vọng |
| `transcript-history.spec.ts:138` FE-T090-05 1200 entries… | Danh sách hiện mục 7xx–9xx, không thấy "Ký hiệu 1199" (thứ tự/phân trang) |

**Lệch spec (cần lead quyết — giữ thiết kế mới thì phải sửa spec, nếu không thì khôi phục):**

| Yêu cầu | Trước commit | Sau commit |
|---|---|---|
| FR-007 + US1 acceptance: hiển thị độ tin cậy | Thẻ kết quả có "Độ tin cậy NN%" | Bỏ; test mới kiểm **không** có |
| FR-010: cảnh báo thử nghiệm / không thay phiên dịch viên | Hiện cùng kết quả | Chỉ còn trong hộp Hướng dẫn |
| plan.md: pilot/fixture phải ghi rõ "chưa sẵn sàng demo" và phạm vi | `role=note` + "Ý nghĩa hỗ trợ" | Bỏ; test mới kiểm không có `note` |
| FR-036: cho biết lịch sử lưu trên thiết bị 24 giờ | Dòng công bố trong lịch sử | Bỏ (`.history-disclosure` count 0) |

P1 đã bỏ 2 test T109 phía FE (dòng "Ý nghĩa hỗ trợ" không còn tồn tại nên không còn lộ mã nghĩa; phần API của T109 giữ).

## Yêu cầu

1. Sửa 12 test Playwright fail (thứ tự lịch sử mới nhất trước, màu, bố cục) hoặc sửa test nếu thiết kế đổi có chủ đích.
2. Chờ lead quyết 4 điểm lệch spec; không gỡ thêm nội dung bắt buộc trước khi có quyết định.
3. Chạy `npm run check` (gồm Playwright) trước khi push.

## Re-review sau `3be0da7` — P1/Huy (2026-11-08)

`npm run check` trên Edge: lint/typecheck/unit/build đạt; Playwright **87 passed, 6 failed** (trước đó 12 failed).
`history-sidebar.spec.ts` đã đạt. Còn `transcript-history.spec.ts` fail trên cả 3 viewport, cùng một nguyên nhân:

- `translationHistory.ts` nay sắp **mới nhất trước** khi lưu (`Date.parse(b.createdAt) - Date.parse(a.createdAt)`), nên
  `localStorage` lưu `["Cảm ơn","Xin chào"]` trong khi T104 kiểm thứ tự thời gian `["Xin chào","Cảm ơn"]`.
- FE-T090-05 (1.200 mục, hiển thị 50 mỗi trang): sidebar không chứa mục mới nhất "Ký hiệu 1199" — thứ tự lưu và cách
  cắt trang đang lệch nhau, người dùng sẽ thấy mục cũ trước.

**Kết quả**: vẫn `CHANGES_REQUESTED` — sửa thứ tự lưu/hiển thị cho nhất quán (hoặc cập nhật T104 nếu cố ý đổi thứ tự lưu,
nhưng trang đầu phải hiện mục mới nhất). 4 điểm lệch spec (FR-007, FR-010, FR-036, công bố pilot) vẫn chờ lead quyết.
