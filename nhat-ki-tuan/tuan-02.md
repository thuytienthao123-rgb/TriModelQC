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
| 1 | **Job #2670** — 5 frames, human-body-keypoints | `2A202602187` (Công Chứ) | `2A202602327` (Văn Thắng) | ✅ 100% gán nhãn | Review xong lần 1 |
| 2 | **Job #2671** — 5 frames, human-body-keypoints | `2A202602171` (Thủy Tiên) | `2A202602327` (Văn Thắng) | ✅ 100% gán nhãn | Review xong lần 1 |
| 3 | **Job #2672** — 5 frames, human-body-keypoints | `2A202602279` (Thanh Đức) | `2A202602327` (Văn Thắng) | ✅ 100% gán nhãn | Review xong lần 1 |
| 4 | **Job #2673** — 5 frames, human-body-keypoints | `2A202602081` (Ngọc Hiếu) | `2A202602327` (Văn Thắng) | ✅ 100% gán nhãn | Review xong lần 1 |
| 5 | **Job #2674** — 10 frames, human-body-keypoints pre-label | `2A202602187` (Công Chứ) | `2A202602327` (Văn Thắng) | 🟡 100% gán nhãn | Review xong lần 1, chờ sửa lỗi |
| 6 | **Job #2675** — 10 frames, human-body-keypoints pre-label | `2A202602171` (Thủy Tiên) | `2A202602327` (Văn Thắng) | ✅ 100% gán nhãn | Review xong lần 1 |
| 7 | **Job #2676** — 10 frames, human-body-keypoints pre-label | `2A202602279` (Thanh Đức) | `2A202602327` (Văn Thắng) | 🟡 100% gán nhãn | Review xong lần 1; phát hiện edge case [P-002](../problem-backlog-tuan-02.md#p-002) |
| 8 | **Job #2677** — 10 frames, human-body-keypoints pre-label | `2A202602081` (Ngọc Hiếu) | `2A202602327` (Văn Thắng) | 🟡 100% gán nhãn | Review xong lần 1; phát hiện edge case [P-001](../problem-backlog-tuan-02.md#p-001) |
| 9 | **Job #2678** — 5 frames (Frame 0–4), Face Landmark `human-face` | `2A202602327` (Văn Thắng) | `2A202602279` (Thanh Đức) | 🟡 100% | Review xong nhưng chờ giải quyết edge case [P-003] |
| 10 | **Job #2679** — 5 frames (Frame 5–9), Face Landmark `human-face` | `2A202602187` (Công Chứ) | `2A202602279` (Thanh Đức) | ✅ 100% |  Đã review xong ngày 23/09 và chuyển sang nghiệm thu. |
| 11 | **Job #2680** — 5 frames (Frame 10–14), Face Landmark `human-face` | `2A202602171` (Thủy Tiên) | `2A202602279` (Thanh Đức) | ✅ 100% |  Đã review xong ngày 23/09 và chuyển sang nghiệm thu. |
| 12 | **Job #2681** — 5 frames (Frame 15-19), Face Landmark `human-face` | `2A202602081` (Ngọc Hiếu) | `2A202602279` (Thanh Đức) | ✅ 100% |  Đã review xong ngày 23/09 và chuyển sang nghiệm thu. |
| 13 | **Job #2682** — 13 frames (Frame 0–12), Face Landmark `human-face-prelabel` | `2A202602327` (Văn Thắng) | `2A202602279` (Thanh Đức) | ✅ 100% | Đã review xong ngày 23/09 và chuyển sang nghiệm thu. |
| 14 | **Job #2683** — 13 frames (Frame 13-25), Face Landmark `human-face-prelabel` | `2A202602187` (Công Chứ) | `2A202602279` (Thanh Đức) | ✅ 100% | Đã review xong ngày 23/09 và chuyển sang nghiệm thu. |
| 15 | **Job #2684** — 13 frames (Frame 26-38), Face Landmark `human-face-prelabel` | `2A202602171` (Thủy Tiên) | `2A202602279` (Thanh Đức) | ✅ 100% | Đã review xong ngày 23/09 và chuyển sang nghiệm thu. | 
| 16 | **Job #2685** — 11 frames (Frame 39-49), Face Landmark `human-face-prelabel` | `2A202602081` (Ngọc Hiếu) | `2A202602279` (Thanh Đức) | ✅ 100% | Đã review xong ngày 23/09 và chuyển sang nghiệm thu. |

Mức hoàn thành: ✅ xong **và đã qua review** · 🟡 đang làm (ghi %) · ⛔ bị chặn (ghi lý do) · ⬜ chưa bắt đầu

## Tổng kết

- Đã gán: **130 / 130 frames (100%)** trên 16 jobs
- Qua review lần đầu: **12 / 16 jobs**
- Edge case mới / đã chốt: **3 edge cases mới**

## Vướng mắc

| Mã / Vấn đề | Chi tiết & Link | Hướng xử lý / Trạng thái |
|---|---|---|
| **[P-001](../problem-backlog-tuan-02.md#p-001)** — Point 6 khó xác định khớp vai | Link CVAT: [https://cvat.note.transformerlabs.ai/tasks/459/jobs/2677?frame=35](https://cvat.note.transformerlabs.ai/tasks/459/jobs/2677?frame=35) (Job #2677, frame 35)<br>File ảnh: `w2/human-body-keypoints-prelabel/G05/000420_vp4_run2_2018-05-22-14-25-04.kinect_color_f013920.jpg` | Tạm thời ước lượng theo tương quan cổ – cánh tay; chờ họp nhóm chốt quy chuẩn |
| **[P-002](../problem-backlog-tuan-02.md#p-002)** — Point 8 bị che khuất | Link CVAT: [https://cvat.note.transformerlabs.ai/tasks/459/jobs/2676?frame=25](https://cvat.note.transformerlabs.ai/tasks/459/jobs/2676?frame=25) (Job #2676, frame 25) | Ước lượng theo hướng xương chi và gắn nhãn `occluded`; chờ họp nhóm chốt tiêu chuẩn |
| **[P-003](../problem-backlog-tuan-02.md#p-003)** — Khoảng cách 43-44-45 và 47-48-49 hợp frame nhưng lệch tỉ lệ | Link CVAT: [https://cvat.note.transformerlabs.ai/tasks/460/jobs/2678?frame=1](https://cvat.note.transformerlabs.ai/tasks/460/jobs/2678?frame=1) (Job #2678, frame 1) | Ước lượng theo hình ảnh; chờ họp nhóm chốt tiêu chuẩn |

## Kế hoạch trước hạn kế tiếp

- Review lại những vấn đề còn vướng mắc
- Chuyển sang những người khác review lại lần 2