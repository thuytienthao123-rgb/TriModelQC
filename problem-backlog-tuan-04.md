# Problem Backlog — Tuần 04 · 05/10 – 11/10/2026

**Task:** Nghiên cứu & Xây dựng công cụ QC tự động cho dữ liệu BBox & Segmentation 2D BDD100K (Mã đề tài: **N2-04A**)  
**Lead:** Trần Thị Thủy Tiên (`2A202602171`)

---

## Danh sách vấn đề Tuần 04

| Mã | Tóm tắt | Loại | Mục guideline | Trạng thái | Kết quả |
|---|---|---|---|---|---|
| [P-001](#p-001) | Lỗi gán nhãn kỹ thuật lặp lại (box tràn khung, box rỗng, polygon tự cắt viền, trùng lặp, thiếu attribute) làm tăng số vòng review/job | Pain point công cụ | §2, §3, §4 | ✅ Đã làm tool | [`source-tool/QC_tool/`](source-tool/QC_tool/) |
| [P-002](#p-002) | Thiếu giao diện trực quan hóa (Visualizer) để annotator định vị ngay đối tượng bị lỗi trên ảnh thay vì tra tọa độ thủ công | Pain point công cụ | — | ✅ Đã làm tool | [`source-tool/QC_tool/app.py`](source-tool/QC_tool/app.py) |

**Loại:** Guideline chưa nói tới · Guideline mơ hồ · Guideline mâu thuẫn · Pain point công cụ  
**Trạng thái:** 🔴 Mở · 🗣️ Đang bàn · ↗️ Chờ mentor · ✅ Đã chốt (trỏ sang QĐ) · 🛠️ Làm tool · ⚪ Bỏ

---

## P-001

**Lỗi gán nhãn kỹ thuật lặp lại (box tràn khung, box rỗng, polygon tự cắt viền, trùng lặp, thiếu attribute) làm tăng số vòng review/job**

- **Loại:** Pain point công cụ
- **Mục guideline:** §2 (BBox), §3 (Polygon Segmentation), §4 (Attributes)
- **Người phát hiện:** Đào Ngọc Hiếu (`2A202602081`) & Nhóm Annotator/Reviewer · 05/10/2026
- **Link kiểm chứng:** [data_sample/sample_with_errors.json](source-tool/QC_tool/data_sample/sample_with_errors.json)
- **Mô tả:**
  - Trong quá trình gán nhãn hàng loạt trên CVAT, annotator thường xuyên gặp phải các lỗi thao tác kỹ thuật lặp đi lặp lại:
    1. Kéo chuột vô tình vượt ra ngoài khung hình ảnh ($x < 0, y < 0, x > 1280, y > 720$).
    2. Click nhầm tạo ra bounding box có diện tích bằng 0 ($w=0, h=0$) hoặc tọa độ bị đảo ngược ($x_2 \le x_1$).
    3. Vẽ viền polygon phân đoạn bị xoắn nơ, chéo viền (tự cắt chính nó - self-intersection), làm thuật toán trích xuất mask nhị phân bị lỗi.
    4. Vẽ trùng lặp 2 box cho cùng một vật thể ($\text{IoU} > 0.85$).
    5. Quên không điền các thuộc tính bắt buộc như `occluded`, `truncated`, hoặc quên chọn màu cho `traffic light`.
  - Trên nền tảng CVAT hiện tại, không có cơ chế linter hoặc pre-commit validation tự động cảnh báo các lỗi cơ bản này trước khi chuyển giao đoạn (*stage: validation*). Reviewer phải soi từng ảnh bằng mắt rất mất thời gian (15–20 phút/job) và phải trả bài qua 2–3 vòng review chéo.
- **Đánh giá 4 điều kiện làm tool:**
  1. *Đã ghi trong backlog:* Thuộc loại Pain point công cụ.
  2. *Lặp lại nhiều lần:* Xuất hiện liên tục qua các job gán nhãn 2D của tất cả thành viên.
  3. *Ước lượng lợi ích:*
     - Tự động bắt $\ge 90\%$ lỗi kỹ thuật trước khi nộp bài.
     - Giảm số vòng trả bài/job từ 2–3 vòng xuống còn $\le 1$ vòng.
     - Giảm $\ge 60\%$ thời gian rà soát của Reviewer.
  4. *CVAT chưa có sẵn:* CVAT không có sẵn rule validation tự động cho cấu trúc BDD100K.
- **Hướng xử lý:**
  - Xây dựng công cụ kiểm tra chất lượng tự động **BDD-QC Tool** (Mã đề tài `N2-04A`) với 10 Core Rules (BBox B01–B04, Polygon P01–P03, Attribute A01–A03), xuất báo cáo đa định dạng CLI terminal, HTML dashboard dark-mode và CSV.
- **Kết quả:**
  - ✅ **Hoàn thành v1.0:** Toàn bộ mã nguồn, bộ parser, engine, reporter và 33 unit tests tự động đã hoàn thiện tại [`source-tool/QC_tool/`](source-tool/QC_tool/).

---

## P-002

**Thiếu giao diện trực quan hóa (Visualizer) để annotator định vị ngay đối tượng bị lỗi trên ảnh thay vì tra tọa độ thủ công**

- **Loại:** Pain point công cụ
- **Người phát hiện:** Trần Thị Thủy Tiên (`2A202602171`) & Nguyễn Thanh Đức (`2A202602279`) · 07/10/2026
- **Mô tả:**
  - Sau khi tool phát hiện lỗi, nếu chỉ xuất kết quả ra bảng tọa độ (ví dụ: `x1=100, y1=150, x2=300, y2=280`), annotator phải mất công mở CVAT, tìm ID và dò tọa độ trên màn hình để biết vật thể nào bị sai.
  - Reviewer cũng cần một giao diện trực quan để nhìn thấy ngay khung viền lỗi được đánh dấu màu nổi bật (Đỏ/Vàng) đè lên canvas hình ảnh để nghiệm thu nhanh.
- **Hướng xử lý:**
  - Phát triển ứng dụng Web tương tác bằng **Streamlit** ([`app.py`](source-tool/QC_tool/app.py)):
    - Kéo - thả file JSON nhãn hoặc nạp file mẫu sẵn có với 1 click.
    - Canvas Visualizer tự động vẽ viền đỏ nổi bật cho vật thể có lỗi (ERROR), viền vàng cho cảnh báo (WARN) và viền xanh cho vật thể chuẩn (OK).
    - Bộ lọc tìm kiếm tương tác theo frame, class, rule ID, và nút xuất báo cáo 1-click.
- **Kết quả:**
  - ✅ **Hoàn thành:** Ứng dụng Web đã chạy thành công tại `http://localhost:8501` và được tích hợp vào dự án.
