# Nhật ký tuần 03 · 28/09 – 04/10/2026

<!-- Copy file này thành tuan-NN.md mỗi đầu tuần. -->

**Lead tuần này:** Đào Ngọc Hiếu (`2A202602081`)  
**Dữ liệu / task CVAT:** Gán nhãn 3D Cuboid trên point cloud nuScenes (41 frames) chia ra làm 4 job (`#4051 - #4054`) — [Task #1504 (W3-CUBOID-G5-T1)](https://cvat.note.transformerlabs.ai/tasks/1504)

## Thành viên và phân công

| Thành viên | MSSV | Vị trí | Phân công tuần này |
|---|---|---|---|
| **Đào Ngọc Hiếu** | `2A202602081` | **Lead · Reviewer** | Lead task W3-CUBOID-G5-T1; Reviewer lần 1 cho toàn bộ 4 Job #4051–#4054; điều phối tiến độ, rà soát ca khó và làm việc với mentor, ban hành QĐ-003 & QĐ-004, tổng hợp nghiệm thu task |
| **Đoàn Văn Thắng** | `2A202602327` | **Annotator · Reviewer 2** | Annotator Job #4051 (11 frames: Frame 0–10); Reviewer lần 2 Job #4052 |
| **Nguyễn Thanh Đức** | `2A202602279` | **Annotator · Reviewer 2** | Annotator Job #4052 (11 frames: Frame 11–21); Reviewer lần 2 Job #4051 |
| **Hoàng Công Chứ** | `2A202602187` | **Annotator · Reviewer 2** | Annotator Job #4053 (11 frames: Frame 22–32); Reviewer lần 2 Job #4054 |
| **Trần Thị Thủy Tiên** | `2A202602171` | **Annotator · Reviewer 2** | Annotator Job #4054 (8 frames: Frame 33–40); Reviewer lần 2 Job #4053 |

## Công việc

| # | Nội dung công việc | Annotator | Reviewer lần 1 | Reviewer lần 2 | Hoàn thành | Ghi chú |
|---|---|---|---|---|---|---|
| 1 | **Job #4051** — 11 frames (Frame 0–10), gán 3D cuboid nuScenes | `2A202602327` (Văn Thắng) | `2A202602081` (Ngọc Hiếu) | `2A202602279` (Thanh Đức) | 🟡 90% (Bị trả về sửa) | Đức đã review chéo lần 2 và trả về (*stage: annotation*); lỗi: Thắng vẽ hàng rào (`barrier`) không cố định qua các frame, ở các frame hàng rào vẽ khác nhau, số lượng khung box cũng khác nhau; Thắng đang hoàn thiện cố định lại |
| 2 | **Job #4052** — 11 frames (Frame 11–21), gán 3D cuboid nuScenes | `2A202602279` (Thanh Đức) | `2A202602081` (Ngọc Hiếu) | `2A202602327` (Văn Thắng) | ✅ 100% hoàn thành | Review lần 1 xong; Thắng đã review chéo lần 2 xong (*stage: validation · state: completed*) |
| 3 | **Job #4053** — 11 frames (Frame 22–32), gán 3D cuboid nuScenes | `2A202602187` (Công Chứ) | `2A202602081` (Ngọc Hiếu) | `2A202602171` (Thủy Tiên) | ✅ 100% hoàn thành | Đã xử lý ca xe ở xa theo [QĐ-003](../so-quyet-dinh.md#qđ-003), tháo tag `can_xem_lai`; Tiên đã review chéo lần 2 xong (*stage: validation · state: completed*) |
| 4 | **Job #4054** — 8 frames (Frame 33–40), gán 3D cuboid nuScenes | `2A202602171` (Thủy Tiên) | `2A202602081` (Ngọc Hiếu) | `2A202602187` (Công Chứ) | ✅ 100% hoàn thành | Đã xử lý ca người thưa điểm theo [QĐ-003](../so-quyet-dinh.md#qđ-003), tháo tag `can_xem_lai`; Chứ đã review chéo lần 2 xong (*stage: validation · state: completed*) |


Mức hoàn thành: ✅ xong **và đã qua review** · 🟡 đang làm / đang chờ · ⛔ bị chặn (ghi lý do) · ⬜ chưa bắt đầu

## Tổng kết

- Đã gán sơ bộ: **41 / 41 frames (100%)** trên 4 jobs (Job #4051: 11/11, Job #4052: 11/11, Job #4053: 11/11, Job #4054: 8/8).
- Qua review lần 1: **4 / 4 jobs (100%)** do Lead Đào Ngọc Hiếu rà soát và nghiệm thu kỹ thuật sơ bộ.
- Review chéo lần 2 (*validation*):
  - **3 / 4 jobs đã hoàn thành 100% và nghiệm thu** (*validation: completed*):
    - **Job #4052:** Đức gán, Thắng review chéo -> `completed`
    - **Job #4053:** Chứ gán, Tiên review chéo -> `completed`
    - **Job #4054:** Tiên gán, Chứ review chéo -> `completed`
  - **1 / 4 job đang trả về để hoàn thiện lại** (*stage: annotation*):
    - **Job #4051:** Thắng gán, Đức review chéo lần 2 đã trả về cho Thắng. Lý do: Hàng rào (`barrier`) vẽ không cố định qua các frame, ở các frame khác nhau hàng rào được vẽ khác nhau, số lượng khung box cũng khác nhau (vi phạm tính nhất quán thời gian của vật thể tĩnh).
- Vướng mắc kỹ thuật & Hướng dẫn:
  - 2 vấn đề lớn đã được Mentor giải đáp và ban hành [QĐ-003](../so-quyet-dinh.md#qđ-003) và [QĐ-004](../so-quyet-dinh.md#qđ-004).
  - Vấn đề thực thi tại Job #4051: Thống nhất hướng dẫn Thắng phải cố định số lượng khung box barrier (ví dụ chia cố định N box) và vị trí/kích thước xuyên suốt từ frame 0 đến frame 10 để bảo đảm tính nhất quán của vật thể tĩnh.

## Vướng mắc

| Mã / Vấn đề | Chi tiết & Link | Hướng xử lý / Trạng thái |
|---|---|---|
| **[P-001](../problem-backlog-tuan-03.md#p-001)** — Thấy người, xe hoặc vật thể trên camera 2D nhưng ở 3D point cloud không thể gán vì không đủ căn cứ | Tương ứng với **Job #4053** và **Job #4054**:<br>- [https://cvat.note.transformerlabs.ai/tasks/1504/jobs/4053?frame=26](https://cvat.note.transformerlabs.ai/tasks/1504/jobs/4053?frame=26) (**Job #4053**, frame 26 - Công Chứ): Xe ô tô đỗ ở góc xa trên `CAM_FRONT_LEFT` nhưng dữ liệu LiDAR không có điểm phản xạ (0 điểm)<br>- [https://cvat.note.transformerlabs.ai/tasks/1504/jobs/4054?frame=35](https://cvat.note.transformerlabs.ai/tasks/1504/jobs/4054?frame=35) (**Job #4054**, frame 35 - Thủy Tiên): Người ở xa trên vỉa hè (`CAM_FRONT_RIGHT`) thưa điểm 3D (chỉ 1–2 điểm nhiễu rời rạc) | **✅ Đã giải đáp tại Mentor 1 · Áp dụng [QĐ-003](../so-quyet-dinh.md#qđ-003)**<br>Mentor đồng thuận với đề xuất của nhóm: Tuyệt đối không tạo 3D box nếu 0 điểm hoặc chỉ 1–2 điểm nhiễu rời rạc (§4.4). Annotator đã rà soát lại frame 26 và frame 35, xác nhận bỏ qua, tháo tag `can_xem_lai` và hoàn tất review chéo lần 2. |
| **[P-002](../problem-backlog-tuan-03.md#p-002)** — Rào chắn giao thông dựng trải dọc theo hình gấp khúc, không thẳng hàng thì vẽ mấy box / thiếu label rào chắn | Tương ứng với **Job #4051**:<br>- [https://cvat.note.transformerlabs.ai/tasks/1504/jobs/4051](https://cvat.note.transformerlabs.ai/tasks/1504/jobs/4051) (**Job #4051**, frame 0–10 - Văn Thắng): Dải rào chắn (`barrier`) thi công kéo dài/gấp khúc dọc mép đường | **✅ Đã giải đáp tại Mentor 1 · Áp dụng [QĐ-004](../so-quyet-dinh.md#qđ-004) · Đang sửa lỗi review chéo lần 2**<br>Mentor đồng thuận chia N box theo từng đoạn thẳng. Khi thực hiện, Thắng vẽ hàng rào không cố định qua các frame (ở các frame khác nhau hàng rào vẽ khác nhau, số lượng khung cũng khác nhau). Thanh Đức review lần 2 đã trả về (*annotation*) để Thắng chuẩn hóa cố định số lượng box và vị trí qua toàn bộ 11 frames. |

## Kế hoạch trước hạn kế tiếp

- Đoàn Văn Thắng hoàn thiện chỉnh sửa Job #4051: Khóa cố định số lượng box barrier và kích thước/vị trí đồng nhất qua tất cả các frame (0–10) của vật thể rào chắn tĩnh.
- Nguyễn Thanh Đức kiểm tra lại Job #4051 sau khi Thắng nộp lại và chuyển sang trạng thái `validation: completed`.
- Lead Đào Ngọc Hiếu kiểm tra đối chiếu lần cuối toàn bộ 41 frames trên CVAT.
- Hoàn tất nghiệm thu và đóng task trước hạn nộp 23:00 Chủ nhật 04/10/2026.
