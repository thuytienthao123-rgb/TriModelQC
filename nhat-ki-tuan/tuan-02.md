# Nhật ký tuần 02 · 21/09 – 27/09/2026

<!-- Copy file này thành tuan-NN.md mỗi đầu tuần. -->

**Lead tuần này:** Nguyễn Thanh Đức (`2A202602279`) và Đoàn Văn Thắng (`2A202602327`)
**Dữ liệu / task CVAT:** Ảnh người ngồi trong xe (60 ảnh) và ảnh gương mặt người (70 ảnh) chia ra làm 8 job mỗi loại (`#2670 - #2677` và `#2678 - #2685`)

## Thành viên và phân công

| Thành viên | MSSV | Vị trí | Phân công tuần này |
|---|---|---|---|
| **Nguyễn Thanh Đức** | `2A202602279` | **Lead · Annotator · Reviewer** | Lead nhóm Job #2678–#2685; Annotator Job #2672 và #2676; Reviewer lần 1 Job #2678-#2685; tổng hợp báo cáo và theo dõi nghiệm thu toàn nhóm lần 1 |
| **Đoàn Văn Thắng** | `2A202602327` | **Lead · Annotator · Reviewer** | Lead nhóm Job #2670–#2677; Annotator Job #2678 và #2682; Reviewer lần 1 Job #2670-#2677;tổng hợp báo cáo và theo dõi nghiệm thu toàn nhóm lần 2 |
| **Hoàng Công Chứ** | `2A202602187` |   **Annotator** | Annotator Job #2670, #2674, #2679, #2683,  |
| **Trần Thị Thủy TIên** | `2A202602171` | **Annotator** | Annotator Job #2671, #2675, #2680, #2684, |
| **Đào Ngọc Hiếu** | `2A202602081` | **Annotator** | Annotator Job #2673, #2677, #2681, #2685, |
## Công việc

| # | Nội dung công việc | Annotator | Reviewer | Hoàn thành | Ghi chú |
|---|---|---|---|---|---|
| 1 | **Job #2670** — 5 frames, human-body-keypoints | `2A202602187` (Công Chứ) | `2A202602327` (Văn Thắng) | 🟡 100% gán nhãn | Review xong lần 1 |
| 2 | **Job #2671** — 5 frames, human-body-keypoints | `2A202602171` (Thủy Tiên) | `2A202602327` (Văn Thắng) | 🟡 100% gán nhãn | Review xong lần 1 |
| 3 | **Job #2672** — 5 frames, human-body-keypoints | `2A202602279` (Thanh Đức) | `2A202602327` (Văn Thắng) | 🟡 100% gán nhãn | Review xong lần 1 |
| 4 | **Job #2673** — 5 frames, human-body-keypoints | `2A202602081` (Ngọc Hiếu) | `2A202602327` (Văn Thắng) | 🟡 100% gán nhãn | Review xong lần 1 |
| 5 | **Job #2674** — 10 frames, human-body-keypoints pre-label | `2A202602187` (Công Chứ) | `2A202602327` (Văn Thắng) | 🟡 100% gán nhãn | Review xong lần 1 |
| 6 | **Job #2675** — 10 frames, human-body-keypoints pre-label | `2A202602171` (Thủy Tiên) | `2A202602327` (Văn Thắng) | 🟡 100% gán nhãn | Review xong lần 1 |
| 7 | **Job #2676** — 10 frames, human-body-keypoints pre-label | `2A202602279` (Thanh Đức) | `2A202602327` (Văn Thắng) | 🟡 100% gán nhãn | Review xong lần 1; phát hiện edge case [P-002](../problem-backlog-tuan-02.md#p-002) |
| 8 | **Job #2677** — 10 frames, human-body-keypoints pre-label | `2A202602081` (Ngọc Hiếu) | `2A202602327` (Văn Thắng) | 🟡 100% gán nhãn | Review xong lần 1; phát hiện edge case [P-001](../problem-backlog-tuan-02.md#p-001) |

Mức hoàn thành: ✅ xong **và đã qua review** · 🟡 đang làm (ghi %) · ⛔ bị chặn (ghi lý do) · ⬜ chưa bắt đầu

## Tổng kết

- Đã gán:
- Qua review lần đầu:
- Edge case mới / đã chốt:

## Vướng mắc

| Mã / Vấn đề | Chi tiết & Link | Hướng xử lý / Trạng thái |
|---|---|---|
| **[P-001](../problem-backlog-tuan-02.md#p-001)** — Point 6 khó xác định khớp vai | Link CVAT: [https://cvat.note.transformerlabs.ai/tasks/459/jobs/2677?frame=35](https://cvat.note.transformerlabs.ai/tasks/459/jobs/2677?frame=35) (Job #2677, frame 35)<br>File ảnh: `w2/human-body-keypoints-prelabel/G05/000420_vp4_run2_2018-05-22-14-25-04.kinect_color_f013920.jpg` | Tạm thời ước lượng theo tương quan cổ – cánh tay; chờ họp nhóm chốt quy chuẩn |
| **[P-002](../problem-backlog-tuan-02.md#p-002)** — Point 8 bị che khuất | Link CVAT: [https://cvat.note.transformerlabs.ai/tasks/459/jobs/2676?frame=25](https://cvat.note.transformerlabs.ai/tasks/459/jobs/2676?frame=25) (Job #2676, frame 25) | Ước lượng theo hướng xương chi và gắn nhãn `occluded`; chờ họp nhóm chốt tiêu chuẩn |

## Kế hoạch tuần sau

-
