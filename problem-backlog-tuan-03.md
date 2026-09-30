# Problem Backlog — Tuần 03 · 28/09 – 04/10/2026

**Task:** Gán nhãn 3D Cuboid trên point cloud nuScenes (41 frames, 4 jobs: `#4051 - #4054`) — [Task #1504 (W3-CUBOID-G5-T1)](https://cvat.note.transformerlabs.ai/tasks/1504)  
**Lead:** Đào Ngọc Hiếu (`2A202602081`)

---

## Danh sách vấn đề Tuần 03

| Mã | Tóm tắt | Loại | Mục guideline | Trạng thái | Kết quả |
|---|---|---|---|---|---|
| [P-001](#p-001) | Thấy người, xe hoặc vật thể trên camera 2D nhưng ở 3D point cloud không thể gán vì không đủ căn cứ | Guideline chưa nói tới | §1, §4.4, §6 | ✅ Đã chốt | [QĐ-003](so-quyet-dinh.md#qđ-003) |
| [P-002](#p-002) | Thanh chắn giao thông dựng trải dọc hình gấp khúc, không thẳng hàng thì vẽ mấy box | Guideline chưa nói tới | §4.2, §4.3, §6 | ✅ Đã chốt | [QĐ-004](so-quyet-dinh.md#qđ-004) |

**Loại:** Guideline chưa nói tới · Guideline mơ hồ · Guideline mâu thuẫn · Pain point công cụ  
**Trạng thái:** 🔴 Mở · 🗣️ Đang bàn · ↗️ Hỏi BTC · ✅ Đã chốt (trỏ sang QĐ) · 🛠️ Làm tool · ⚪ Bỏ

---

## P-001

**Thấy người, xe hoặc vật thể trên camera 2D nhưng ở 3D không thể gán vì không đủ căn cứ**

- **Loại:** Guideline chưa nói tới
- **Mục guideline:** §1, §4.4, §6
- **Người phát hiện:** Đoàn Văn Thắng (`2A202602327`) & Hoàng Công Chứ (`2A202602187`) · 29/09/2026
- **Link CVAT:**
  - https://cvat.note.transformerlabs.ai/tasks/1504/jobs/4051?frame=3 — người đi bộ xa trên vỉa hè, thấy trên `CAM_FRONT_RIGHT` nhưng point cloud chỉ có 1–2 điểm nhiễu rời rạc
  - https://cvat.note.transformerlabs.ai/tasks/1504/jobs/4053?frame=26 — xe ô tô con ở góc xa trên `CAM_FRONT_LEFT`, point cloud hoàn toàn không có điểm phản xạ (0 điểm)
- **Mô tả:** Trên 6 ảnh camera 2D quan sát thấy người đi bộ, xe ô tô hoặc vật thể giao thông ở xa / bị che khuất, nhưng trên dữ liệu 3D LiDAR point cloud thì đối tượng ở quá xa, laser không quét tới hoặc phản xạ laser kém (chỉ có 0 điểm hoặc 1–2 điểm nhiễu rời rạc), không thể xác định được tâm thể tích, kích thước ba chiều và hướng xoay (yaw). Annotator phân vân không biết có vẽ cuboid dựa theo ảnh camera hay bỏ qua.
- **Các cách hiểu:**
  1. Chỉ dựa trên ảnh 2D camera để phỏng đoán và vẽ 3D cuboid mò ở vị trí ước lượng.
  2. Bỏ qua hoàn toàn nếu không thấy rõ toàn bộ hình khối 3D.
  3. Tuân thủ triệt để §1 & §4.4 của Guideline: Tuyệt đối không tạo box nếu không có cơ sở 3D hợp lý trong point cloud (0 điểm hoặc chỉ 1–2 điểm nhiễu). Nếu có cụm điểm tối thiểu (≥ 3–5 điểm) khớp góc nhìn camera thì căn theo ground plane và áp kích thước chuẩn (prior) của đối tượng để ôm cụm điểm.
- **Xử lý tạm trong lúc chờ:** Gắn tag `can_xem_lai` và ghi lại số frame để đối chiếu temporal context giữa các frame liên tiếp.
- **Kết quả:** ✅ [QĐ-003](so-quyet-dinh.md#qđ-003)

---

## P-002

**Thanh chắn giao thông dựng trải dọc hình gấp khúc, không thẳng hàng thì vẽ mấy box**

- **Loại:** Guideline chưa nói tới
- **Mục guideline:** §4.2, §4.3, §6
- **Người phát hiện:** Nguyễn Thanh Đức (`2A202602279`) · 29/09/2026
- **Link CVAT:**
  - https://cvat.note.transformerlabs.ai/tasks/1504/jobs/4052?frame=14 — dải rào chắn thi công gấp khúc hình chữ L quanh góc cua ngã ba
- **Mô tả:** Hàng rào chắn (`barrier`) trải dài nhưng đổi hướng gấp khúc (chữ L, zíc-zắc). 3D cuboid là hình hộp chữ nhật thẳng chỉ có một góc xoay yaw. Nếu vẽ 1 box bao cả cụm sẽ làm box phình cực to, chứa đầy khoảng trống mặt đường (lỗi §4.2) và sai hoàn toàn trục yaw (lỗi §4.3 & §7).
- **Các cách hiểu:**
  1. Vẽ 1 box duy nhất bao trùm cả đường gấp khúc.
  2. Chia thành nhiều box tương ứng với từng đoạn thẳng thẳng hàng của rào chắn.
- **Xử lý tạm trong lúc chờ:** Tạm hoãn gán dải barrier tại frame 14 để họp đội chốt quy tắc.
- **Kết quả:** ✅ [QĐ-004](so-quyet-dinh.md#qđ-004)
