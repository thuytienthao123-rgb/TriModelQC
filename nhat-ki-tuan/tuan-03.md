# Nhật ký tuần 03 · 28/09 – 04/10/2026

<!-- Copy file này thành tuan-NN.md mỗi đầu tuần. -->

**Lead tuần này:** Đào Ngọc Hiếu (`2A202602081`)  
**Dữ liệu / task CVAT:** Gán nhãn 3D Cuboid trên point cloud nuScenes (41 frames) chia ra làm 4 job (`#4051 - #4054`) — [Task #1504 (W3-CUBOID-G5-T1)](https://cvat.note.transformerlabs.ai/tasks/1504)

## Thành viên và phân công

| Thành viên | MSSV | Vị trí | Phân công tuần này |
|---|---|---|---|
| **Đào Ngọc Hiếu** | `2A202602081` | **Lead · Reviewer** | Lead task W3-CUBOID-G5-T1; Reviewer lần 1 cho toàn bộ 4 Job #4051–#4054; điều phối tiến độ, rà soát và tổng hợp các ca khó, gửi câu hỏi xin ý kiến mentor, tổng hợp báo cáo và theo dõi nghiệm thu toàn nhóm |
| **Đoàn Văn Thắng** | `2A202602327` | **Annotator** | Annotator Job #4051 (11 frames: Frame 0–10) |
| **Nguyễn Thanh Đức** | `2A202602279` | **Annotator** | Annotator Job #4052 (11 frames: Frame 11–21) |
| **Hoàng Công Chứ** | `2A202602187` | **Annotator** | Annotator Job #4053 (11 frames: Frame 22–32) |
| **Trần Thị Thủy Tiên** | `2A202602171` | **Annotator** | Annotator Job #4054 (8 frames: Frame 33–40) |

## Công việc

| # | Nội dung công việc | Annotator | Reviewer lần 1 | Reviewer lần 2 | Hoàn thành | Ghi chú |
|---|---|---|---|---|---|---|
| 1 | **Job #4051** — 11 frames (Frame 0–10), gán 3D cuboid nuScenes | `2A202602327` (Văn Thắng) | `2A202602081` (Ngọc Hiếu) | — | 🟡 80% hoàn thành | Đã gán 11/11 frames; review xong lần 1; còn thiếu label rào chắn ([P-002](../problem-backlog-tuan-03.md#p-002)), đã tổng hợp chờ buổi mentor lần 1 |
| 2 | **Job #4052** — 11 frames (Frame 11–21), gán 3D cuboid nuScenes | `2A202602279` (Thanh Đức) | `2A202602081` (Ngọc Hiếu) | — | 🟡 90% hoàn thành | Đã gán 11/11 frames; review xong lần 1 |
| 3 | **Job #4053** — 11 frames (Frame 22–32), gán 3D cuboid nuScenes | `2A202602187` (Công Chứ) | `2A202602081` (Ngọc Hiếu) | — | 🟡 90% hoàn thành | Đã gán 11/11 frames; review xong lần 1; phát hiện xe ở xa chỉ thấy trên 2D camera không có điểm 3D ([P-001](../problem-backlog-tuan-03.md#p-001)), đã tổng hợp chờ buổi mentor lần 1 |
| 4 | **Job #4054** — 8 frames (Frame 33–40), gán 3D cuboid nuScenes | `2A202602171` (Thủy Tiên) | `2A202602081` (Ngọc Hiếu) | — | 🟡 80% hoàn thành | Đã gán 8/8 frames; review xong lần 1; phát hiện ca người ở xa thưa điểm 3D ([P-001](../problem-backlog-tuan-03.md#p-001)), đã gắn tag `can_xem_lai` chờ buổi mentor lần 1 |


Mức hoàn thành: ✅ xong **và đã qua review** · 🟡 đang làm / đang chờ · ⛔ bị chặn (ghi lý do) · ⬜ chưa bắt đầu

## Tổng kết

- Đã gán sơ bộ: **41 / 41 frames (100%)** trên 4 jobs (Job #4051: 11/11, Job #4052: 11/11, Job #4053: 11/11, Job #4054: 8/8).
- Tiến độ hoàn thiện sau review lần 1:
  - **Job #4051:** 🟡 90% hoàn thành (11/11 frames; review xong lần 1; còn thiếu label rào chắn do vướng [P-002](../problem-backlog-tuan-03.md#p-002)).
  - **Job #4052:** 🟡 100% hoàn thành (11/11 frames; review xong lần 1).
  - **Job #4053:** 🟡 100% hoàn thành (11/11 frames; review xong lần 1; phát hiện ca xe ở xa không có điểm 3D [P-001](../problem-backlog-tuan-03.md#p-001), chờ mentor lần 1).
  - **Job #4054:** 🟡 90% hoàn thành (8/8 frames; review xong lần 1; phát hiện ca người ở xa thưa điểm 3D [P-001](../problem-backlog-tuan-03.md#p-001), đã gắn tag `can_xem_lai`).
- Qua review lần 1: **4 / 4 jobs (100%)** (Lead Đào Ngọc Hiếu đã rà soát sơ bộ 100% các frames, tổng hợp các ca khó).
- Review lần 2: **Chưa có** (dự kiến thực hiện sau khi chốt hướng dẫn từ mentor và annotator hoàn thiện).
- Vướng mắc kỹ thuật: **2 vấn đề chính ([P-001](../problem-backlog-tuan-03.md#p-001), [P-002](../problem-backlog-tuan-03.md#p-002)) / 0 đã chốt** (Trạng thái: **↗️ Chờ buổi mentor lần 1**).

## Vướng mắc

| Mã / Vấn đề | Chi tiết & Link | Hướng xử lý / Trạng thái |
|---|---|---|
| **[P-001](../problem-backlog-tuan-03.md#p-001)** — Thấy người, xe hoặc vật thể trên camera 2D nhưng ở 3D point cloud không thể gán vì không đủ căn cứ | Tương ứng với **Job #4053** và **Job #4054**:<br>- [https://cvat.note.transformerlabs.ai/tasks/1504/jobs/4053?frame=26](https://cvat.note.transformerlabs.ai/tasks/1504/jobs/4053?frame=26) (**Job #4053**, frame 26 - Công Chứ): Xe ô tô đỗ ở góc xa trên `CAM_FRONT_LEFT` nhưng dữ liệu LiDAR không có điểm phản xạ (0 điểm)<br>- [https://cvat.note.transformerlabs.ai/tasks/1504/jobs/4054?frame=35](https://cvat.note.transformerlabs.ai/tasks/1504/jobs/4054?frame=35) (**Job #4054**, frame 35 - Thủy Tiên): Người ở xa trên vỉa hè (`CAM_FRONT_RIGHT`) thưa điểm 3D (chỉ 1–2 điểm nhiễu rời rạc), đã gắn tag `can_xem_lai` (Job đạt 90%) | **↗️ Chờ buổi mentor lần 1**<br>Nhóm đã chuẩn bị phương án đề xuất dựa theo §4.4: Nếu 0 điểm hoặc 1–2 điểm nhiễu thì không gán cuboid; nếu có cụm điểm (≥ 3–5 điểm) thì căn ground plane và áp kích thước prior. Đã gắn tag `can_xem_lai` tại các frame liên quan (như Job #4054), chờ trao đổi tại buổi mentor lần 1 để chốt quyết định. |
| **[P-002](../problem-backlog-tuan-03.md#p-002)** — Rào chắn giao thông dựng trải dọc theo hình gấp khúc, không thẳng hàng thì vẽ mấy box / thiếu label rào chắn | Tương ứng với **Job #4051**:<br>- [https://cvat.note.transformerlabs.ai/tasks/1504/jobs/4051](https://cvat.note.transformerlabs.ai/tasks/1504/jobs/4051) (**Job #4051**, frame 0–10 - Văn Thắng): Dải rào chắn (`barrier`) thi công kéo dài/gấp khúc dọc mép đường chưa rõ quy cách phân tách box rào chắn nên còn thiếu label rào chắn (Job đạt 90%) | **↗️ Chờ buổi mentor lần 1**<br>Nhóm đã chuẩn bị phương án đề xuất chia nhỏ thành nhiều box (N khúc gấp = N box) ôm sát từng đoạn thẳng để tránh lỗi box quá lớn (§4.2) và sai yaw (§4.3). Tạm thời hoãn gán label rào chắn tại Job #4051, chờ trao đổi tại buổi mentor lần 1 để chốt quyết định. |

## Kế hoạch trước hạn kế tiếp

- Giải quyết vướng mắc, ban hành quyết định kỹ thuật chính thức vào `so-quyet-dinh.md` ngay sau buổi mentor lần 1.
- 4 annotator cập nhật chỉnh sửa các frame có vướng mắc tương ứng theo quyết định đã chốt.
- Lead Đào Ngọc Hiếu tiến hành kiểm tra nghiệm thu chính thức toàn bộ 4 jobs (Job #4051–#4054) trước hạn chót.
