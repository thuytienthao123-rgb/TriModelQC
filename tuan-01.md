# Nhật ký tuần 01 · 14/09 – 20/09/2026

**Lead tuần này:** Trần Thị Thủy Tiên (`2A202602171`) và Hoàng Công Chứ (`2A202602187`)  
**Dữ liệu / task CVAT:** Video camera hành trình xe tự hành trong môi trường giao thông đô thị — 8 jobs, tổng cộng 200 frames (`#1474`–`#1477`, `#1690`–`#1693`)

## Thành viên và phân công

| Thành viên | MSSV / Mã | Vị trí | Phân công tuần này |
|---|---|---|---|
| **Trần Thị Thủy Tiên** | `2A202602171` | **Lead · Annotator · Reviewer** | Lead nhóm Job #1690–#1693; Annotator Job #1474; Reviewer Job #1476, #1690–#1692 và review lần 2 Job #1477, #1693; tổng hợp báo cáo và theo dõi nghiệm thu toàn nhóm |
| **Hoàng Công Chứ** | `2A202602187` | **Lead · Annotator · Reviewer** | Lead phụ trách phân công nhóm Job #1474–#1477; Annotator Job #1690; Reviewer lần 1 Job #1693 |
| **Đoàn Văn Thắng** | `2A202602327` | **Annotator** | Annotator Job #1475 và #1691; Reviewer lần 1 Job #1477 |
| **Nguyễn Thanh Đức** | `2A202602279` | **Annotator · Reviewer** | Annotator Job #1476 và #1692; Reviewer Job #1474 |
| **Đào Ngọc Hiếu** | `2A202602081` | **Annotator · Reviewer** | Annotator Job #1477 và #1693; Reviewer Job #1475 |

> Hoàng Công Chứ là Lead phụ trách phân công nhóm Job #1474–#1477; Trần Thị Thủy Tiên là Lead phụ trách nhóm Job #1690–#1693. Tên Assignee hiển thị khi job ở stage `validation` là Reviewer, không phải Annotator.

## Công việc

| # | Nội dung công việc | Annotator | Reviewer lần 1 | Reviewer lần 2 | Hoàn thành | Ghi chú |
|---|---|---|---|---|---|---|
| 1 | **Job #1474** — 25 frames (Frame 0–24), BBOX `W1-BBOX-G5-T1` | `2A202602171` (Thủy Tiên) | `2A202602279` (Thanh Đức) | — | 🟡 100% gán nhãn | *Stage: validation; state: new*. Đã phân công Reviewer, chờ bắt đầu validation. |
| 2 | **Job #1475** — 25 frames (Frame 25–49), cùng bộ nhãn BBOX | `2A202602327` (Văn Thắng) | `2A202602081` (Ngọc Hiếu) | — | 🟡 100% gán nhãn | *Stage: validation; state: new*. Đã phân công Reviewer, chờ bắt đầu validation. |
| 3 | **Job #1476** — 25 frames (Frame 50–74), cùng bộ nhãn BBOX | `2A202602279` (Thanh Đức) | `2A202602171` (Thủy Tiên) | — | 🟡 100% gán nhãn | *Stage: validation; state: in progress*. Reviewer đang kiểm tra. |
| 4 | **Job #1477** — 25 frames (Frame 75–99), cùng bộ nhãn BBOX | `2A202602081` (Ngọc Hiếu) | `2A202602171` (Thủy Tiên) | `2A202602171` (Thủy Tiên) | 🟡 100% gán nhãn | Reviewer lần 1 đã mở issue; Job được chuyển cho Reviewer lần 2 lúc 11:26 ngày 20/09. |
| 5 | **Job #1690** — 25 frames (Frame 0–24), segmentation `W1-SEG-G5-T1` | `2A202602187` (Công Chứ) | `2A202602171` (Thủy Tiên) | — | ✅ 100% | Đã review xong lúc 11:13 ngày 20/09 và chuyển sang nghiệm thu. |
| 6 | **Job #1691** — 25 frames (Frame 25–49), cùng bộ nhãn segmentation | `2A202602327` (Văn Thắng) | `2A202602171` (Thủy Tiên) | — | 🟡 100% gán nhãn | *Stage: validation; state: in progress*. Reviewer đã mở issue để Annotator kiểm tra và sửa. |
| 7 | **Job #1692** — 25 frames (Frame 50–74), cùng bộ nhãn segmentation | `2A202602279` (Thanh Đức) | `2A202602171` (Thủy Tiên) | — | ✅ 100% | Đã review xong lúc 11:03 ngày 20/09 và chuyển sang nghiệm thu. |
| 8 | **Job #1693** — 25 frames (Frame 75–99), cùng bộ nhãn segmentation | `2A202602081` (Ngọc Hiếu) | `2A202602187` (Công Chứ) | `2A202602171` (Thủy Tiên) | 🟡 100% gán nhãn | Reviewer lần 1 đã mở issue; Job được chuyển cho Reviewer lần 2 và đang tiếp tục validation. |
| 9 | Nộp báo cáo Mentor Duty ngày 17/09 | `2A202602171` (Thủy Tiên) | — | — | ✅ 100% | Đã nộp lúc 11:16 ngày 17/09. |

Mức hoàn thành chung: 🟡 **Đã gán nhãn 100%; đang hoàn tất review và nghiệm thu.**

Quy ước: ✅ xong **và đã qua review** · 🟡 đã gán xong, đang review/sửa lỗi · ⛔ bị chặn · ⬜ chưa bắt đầu

## Tổng kết

- Đã gán: **200 / 200 frames (100%)** trên 8 jobs.
- Đã chuyển sang validation: **8 / 8 jobs (100%)**.
- Đã review xong và chuyển sang nghiệm thu: **2 / 8 jobs (25%)** — #1690 và #1692, tương ứng 50 frames.
- Validation đang thực hiện: **4 / 8 jobs (50%)** — #1476, #1477, #1691 và #1693.
- Validation đang chờ bắt đầu: **2 / 8 jobs (25%)** — #1474 và #1475.
- Phân công Job #1474–#1477 do Lead Hoàng Công Chứ điều phối; cặp Annotator–Reviewer được ghi theo bảng phân công chính thức của nhóm.
- Edge case mới / đã chốt: **chưa ghi nhận** trong thông tin cập nhật tuần này.

## Vướng mắc

- Bốn job (#1476, #1477, #1691 và #1693) vẫn đang trong quá trình validation.
- Chưa có số liệu tổng hợp về số lỗi, tỷ lệ đạt lần đầu hoặc số frame bị trả lại sau validation của các job đang kiểm tra.

## Kế hoạch tuần 02

Tiếp nhận và phân chia các job tracking video theo vai trò Annotator và Reviewer; theo dõi, phối hợp và đẩy nhanh tiến độ hoàn thành các job hiệu quả hơn so với tuần 1
