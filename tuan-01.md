# Nhật ký tuần 01 · 14/09 – 20/09/2026

**Lead tuần này:** Trần Thị Thủy Tiên (@2A202602171)  
**Dữ liệu / task CVAT:** Dữ liệu video / camera hành trình xe tự hành (Giao thông đô thị) — Task 4 splits (Jobs #1690 – #1693) & Job độc lập (#1474)

---

## Thành viên và phân công

| Thành viên | MSSV / Mã | Vị trí | Phân công tuần này |
|---|---|---|---|
| **Trần Thị Thủy Tiên** | `2A202602171` | **Lead · Annotator** | Quản lý tiến độ, điều phối job, tổng hợp báo cáo; gán nhãn Job #1474; nghiệm thu QC toàn nhóm |
| **Hoàng Công Chứ** | `2A202602187` | **QC Lead · Annotator** | Gán nhãn Job #1690; kiểm tra chéo (Review) Job #1691 và #1692 |
| **Đoàn Văn Thắng** | `2A202602327` | **Annotator** | Gán nhãn Job #1691 |
| **Nguyễn Thanh Đức** | `2A202602279` | **Annotator** | Gán nhãn Job #1692 |
| **Đào Ngọc Hiếu** | `2A202602081` | **Annotator** | Gán nhãn Job #1693 |

> *Ghi chú phân công Review:* Hoàng Công Chứ có chuyên môn sâu về *Annotation QC* và *Video Annotation*, chịu trách nhiệm chính kiểm tra chất lượng (Reviewer) cho các thành viên. Job của Hoàng Công Chứ (#1690) và của Leader (#1474) sẽ do chính Lead nghiệm thu đối chiếu chéo.

---

## Công việc

| # | Nội dung công việc | Annotator | Reviewer | Hoàn thành | Ghi chú & Trạng thái |
|---|---|---|---|---|---|
| 1 | **Job #1474** — 25 frames, gán nhãn phương tiện/vật thể camera hành trình | @2A202602171 (Thủy Tiên) | @2A202602187 (Công Chứ) | 🟡 80% | *Stage: annotation, state: in progress*. Đang tiến hành, đảm bảo đúng tiến độ. |
| 2 | **Job #1690** — 25 frames (Frame 0–24), task video giao thông | @2A202602187 (Công Chứ) | @2A202602171 (Thủy Tiên) | 🟡 40% | *Stage: annotation, state: in progress*. Cập nhật gần nhất lúc 11:33 ngày 17/09. |
| 3 | **Job #1691** — 25 frames (Frame 25–49), task video giao thông | @2A202602327 (Văn Thắng) | @2A202602187 (Công Chứ) | 🟡 1% | *Stage: annotation, state: in progress*. Cập nhật lúc 23:40 ngày 16/09. |
| 4 | **Job #1692** — 25 frames (Frame 50–74), task video giao thông | @2A202602279 (Thanh Đức) | @2A202602187 (Công Chứ) | 🟡 4% | *Stage: annotation, state: in progress*. Cập nhật lúc 11:03 ngày 16/09. |
| 5 | **Job #1693** — 25 frames (Frame 75–99), task video giao thông | @2A202602081 (Ngọc Hiếu) | @2A202602187 (Công Chứ) | 🟡 80% | *Stage: annotation, state: in progress*. Cập nhật lúc 11:13 ngày 17/09).|

---

## Đánh giá của Leader & Kế hoạch xử lý tiếp theo

1. **Tiến độ chung:**
   - Đã tạo job từ ngày **14/09/2026**, thời hạn thiết lập trên CVAT là **3 days** (tương đương hạn chót hoàn thành giai đoạn gán là 17/09/2026).
   - Toàn bộ thành viên (5/5) đã mở job và đang tích cực thực hiện (`in progress`).
   
2. **Cảnh báo rủi ro & Hành động:**
   - Khi các thành viên chuyển trạng thái job sang hoàn tất (`validation` hoặc `completed`), Reviewer (*Hoàng Công Chứ*) sẽ tiến hành kiểm định chất lượng (IoU, nhãn lớp, thuộc tính occluded/truncated) và trả phản hồi sửa lỗi trước cuối tuần.
