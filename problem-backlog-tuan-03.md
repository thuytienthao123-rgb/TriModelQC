# Problem Backlog — Tuần 03 · 28/09 – 04/10/2026

**Task:** Gán nhãn 3D Cuboid trên point cloud nuScenes (41 frames, 4 jobs: `#4051 - #4054`) — [Task #1504 (W3-CUBOID-G5-T1)](https://cvat.note.transformerlabs.ai/tasks/1504)  
**Lead:** Đào Ngọc Hiếu (`2A202602081`)

---

## Danh sách vấn đề Tuần 03

| Mã | Tóm tắt | Loại | Mục guideline | Trạng thái | Kết quả |
|---|---|---|---|---|---|
| [P-001](#p-001) | Thấy người, xe hoặc vật thể trên camera 2D nhưng ở 3D point cloud không thể gán vì không đủ căn cứ | Guideline mơ hồ | §4.4 | ↗️ Chờ mentor giải đáp | — |
| [P-002](#p-002) | Rào chắn giao thông dựng trải dọc hình gấp khúc, không thẳng hàng thì vẽ mấy box / thiếu label rào chắn | Guideline mơ hồ | §4.3, §6 | ↗️ Chờ mentor giải đáp | — |

**Loại:** Guideline chưa nói tới · Guideline mơ hồ · Guideline mâu thuẫn · Pain point công cụ  
**Trạng thái:** 🔴 Mở · 🗣️ Đang bàn · ↗️ Chờ mentor 1 · ✅ Đã chốt (trỏ sang QĐ) · 🛠️ Làm tool · ⚪ Bỏ

---

## P-001

**Thấy người, xe hoặc vật thể trên camera 2D nhưng ở 3D không thể gán vì không đủ căn cứ**

- **Loại:** Guideline mơ hồ
- **Mục guideline:** §4.4 — chỉ quy định "không tạo cuboid chỉ dựa trên ảnh 2D nếu không có cơ sở 3D", nhưng chưa nêu ngưỡng điểm tối thiểu và cách xử lý khi thấy rất rõ trên camera 2D mà trên 3D chỉ có 0 điểm hoặc 1–2 điểm nhiễu rời rạc
- **Tương ứng:** **Job #4053** (Hoàng Công Chứ) & **Job #4054** (Trần Thị Thủy Tiên)
- **Người phát hiện:** Hoàng Công Chứ (`2A202602187`) (Job #4053) & Trần Thị Thủy Tiên (`2A202602171`) (Job #4054) · 29/09/2026
- **Link CVAT & Trường hợp cụ thể:**
  - https://cvat.note.transformerlabs.ai/tasks/1504/jobs/4053?frame=26 (Job #4053, frame 26): Xe ô tô đỗ ở góc xa trên `CAM_FRONT_LEFT`, point cloud hoàn toàn không có điểm phản xạ (0 điểm) — Annotator Hoàng Công Chứ phát hiện, ghi nhận chờ mentor lần 1
  - https://cvat.note.transformerlabs.ai/tasks/1504/jobs/4054?frame=35 (Job #4054, frame 35): Người đi bộ ở xa trên vỉa hè (`CAM_FRONT_RIGHT`), point cloud thưa điểm 3D (chỉ có 1–2 điểm nhiễu rời rạc), không đủ căn cứ tạo box — Annotator Trần Thị Thủy Tiên phát hiện, đã gắn tag `can_xem_lai` (Job #4054 đạt 90%)
- **Mô tả:** Trên 6 ảnh camera 2D quan sát thấy rõ người đi bộ, xe ô tô hoặc vật thể giao thông ở xa / bị che khuất, nhưng trên dữ liệu 3D LiDAR point cloud thì đối tượng ở quá xa, laser không quét tới hoặc phản xạ laser kém (chỉ có 0 điểm hoặc 1–2 điểm nhiễu rời rạc), không thể xác định được tâm thể tích, kích thước ba chiều và hướng xoay (yaw). Annotator phân vân không biết có vẽ cuboid dựa theo ảnh camera hay bỏ qua.
- **Các cách hiểu / Hướng đề xuất:**
  1. Chỉ dựa trên ảnh 2D camera để phỏng đoán và vẽ 3D cuboid mò ở vị trí ước lượng.
  2. Bỏ qua hoàn toàn nếu không thấy rõ toàn bộ hình khối 3D.
  3. Tuân thủ triệt để §1 & §4.4 của Guideline: Tuyệt đối không tạo box nếu không có cơ sở 3D hợp lý trong point cloud (0 điểm hoặc chỉ 1–2 điểm nhiễu). Nếu có cụm điểm tối thiểu (≥ 3–5 điểm) khớp góc nhìn camera thì căn theo ground plane và áp kích thước chuẩn (prior) của đối tượng để ôm cụm điểm.
- **Xử lý tạm trong lúc chờ:** Gắn tag `can_xem_lai` tại các frame liên quan (Job #4054 frame 35 và Job #4053 frame 26), ghi nhận vào báo cáo tiến độ tuần và tổng hợp danh sách frame chờ buổi mentor lần 1.
- **Kết quả:** ↗️ Đã tổng hợp danh sách các frame khó, chờ trao đổi trực tiếp tại **buổi mentor lần 1** để thống nhất quy tắc trước khi ban hành quyết định chính thức.

---

## P-002

**Rào chắn giao thông dựng trải dọc hình gấp khúc, không thẳng hàng thì vẽ mấy box / thiếu label rào chắn**

- **Loại:** Guideline mơ hồ
- **Mục guideline:** §4.3, §6 — chỉ hướng dẫn đặt trục dài theo chiều kéo dài của rào chắn thẳng, chưa hướng dẫn cụ thể trường hợp rào chắn thi công gấp khúc hình chữ L quanh góc đường hoặc dải rào chắn kéo dài dọc mép đường
- **Tương ứng:** **Job #4051** (Đoàn Văn Thắng)
- **Người phát hiện:** Đoàn Văn Thắng (`2A202602327`) (Job #4051) · 29/09/2026
- **Link CVAT & Trường hợp cụ thể:**
  - https://cvat.note.transformerlabs.ai/tasks/1504/jobs/4051 (Job #4051, frame 0–10): Dải rào chắn (`barrier`) thi công kéo dài/gấp khúc dọc mép đường, chưa rõ quy cách phân tách box rào chắn nên còn thiếu label rào chắn (Job #4051 đạt 90%) — Annotator Đoàn Văn Thắng và Reviewer Đào Ngọc Hiếu ghi nhận
- **Mô tả:** Hàng rào chắn (`barrier`) trải dài nhưng đổi hướng gấp khúc (chữ L, zíc-zắc) hoặc kéo dài dọc khu vực công trường. 3D cuboid là hình hộp chữ nhật thẳng chỉ có một góc xoay yaw. Nếu vẽ 1 box bao cả cụm sẽ làm box phình cực to, chứa đầy khoảng trống mặt đường (lỗi §4.2) và sai hoàn toàn trục yaw (lỗi §4.3 & §7). Do đó tại Job #4051 annotator tạm thời chưa gán label rào chắn để chờ hướng dẫn từ mentor.
- **Các cách hiểu / Hướng đề xuất:**
  1. Vẽ 1 box duy nhất bao trùm cả đường gấp khúc.
  2. Chia thành nhiều box tương ứng với từng đoạn thẳng thẳng hàng của rào chắn (N khúc gấp = N box) ôm sát từng dải barrier rồi dùng Group (gộp thành 1 nhóm).
- **Xử lý tạm trong lúc chờ:** Tạm hoãn gán dải barrier chưa rõ quy cách tại Job #4051 (Job đạt 90%), đã tổng hợp chờ ý kiến mentor tại buổi mentor lần 1.
- **Kết quả:** ↗️ Đã tổng hợp hình ảnh và tọa độ dải rào chắn Job #4051, chờ trao đổi trực tiếp tại **buổi mentor lần 1** để chốt quy cách phân tách box trước khi ban hành quyết định chính thức.
