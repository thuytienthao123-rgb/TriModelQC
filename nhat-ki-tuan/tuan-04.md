# Nhật ký tuần 04 · 05/10 – 11/10/2026

**Lead tuần này:** Đào Ngọc Hiếu (`2A202602081`)  
**Nhiệm vụ trọng tâm:** Nghiên cứu & Xây dựng công cụ QC tự động cho dữ liệu BBox & Segmentation 2D BDD100K (Mã đề tài: **N2-04A**)  
**Mã kho lưu trữ:** [P-037](https://github.com/AI20K-Build-Phase-Cohort-4A/P-037) · **Nhóm:** `t-037`

---

## 1. Thành viên và phân công nhiệm vụ

| Thành viên | MSSV | Vai trò chính | Phân công cụ thể trong tuần 04 |
|---|---|---|---|
| **Đào Ngọc Hiếu** | `2A202602081` | **Team Lead · Core Integration** | Thiết kế kiến trúc tổng thể; viết QC Engine (`engine.py`), Reporter xuất HTML/CSV/Console (`reporter.py`), CLI (`main.py`); xây dựng Giao diện Web tương tác Streamlit (`app.py`); thiết lập CI/CD & bộ Unit test tổng hợp; viết tài liệu kỹ thuật. |
| **Đoàn Văn Thắng** | `2A202602327` | **Data Engineer** | Thiết kế cấu trúc dữ liệu chuẩn (`models.py`); xây dựng module đọc và chuẩn hóa dữ liệu nhãn BDD100K JSON / CVAT export (`parser.py`); tạo bộ dữ liệu kiểm thử mẫu (`sample_valid.json`, `sample_with_errors.json`). |
| **Nguyễn Thanh Đức** | `2A202602279` | **BBox QC Specialist** | Nghiên cứu và cài đặt 4 quy tắc kiểm tra Bounding Box 2D (`bbox_rules.py`): `RULE_B01` (Out of Bounds), `RULE_B02` (Inverted/Zero Box), `RULE_B03` (Too Small Box), `RULE_B04` (Abnormal Aspect Ratio). |
| **Hoàng Công Chứ** | `2A202602187` | **Segmentation QC Specialist** | Nghiên cứu và cài đặt 3 quy tắc kiểm tra Polygon/Mask 2D (`polygon_rules.py`): `RULE_P01` (Thiếu đỉnh < 3), `RULE_P02` (Đa giác tự cắt viền - Self-intersection, thuật toán hình học thuần túy không phụ thuộc C-lib), `RULE_P03` (Lệch khung bao Mask vs BBox). |
| **Trần Thị Thủy Tiên** | `2A202602171` | **Attribute & Consistency Specialist** | Nghiên cứu và cài đặt 3 quy tắc kiểm tra thuộc tính & trùng lặp (`attribute_rules.py`): `RULE_A01` (Vẽ trùng lặp đối tượng cùng class, IoU > 0.85), `RULE_A02` (Thiếu thuộc tính bắt buộc `occluded`, `truncated`), `RULE_A03` (Sai/thiếu màu đèn tín hiệu giao thông). |

---

## 2. Tiến độ công việc

| # | Hạng mục công việc | Người phụ trách | Trạng thái | Kết quả nghiệm thu |
|---|---|---|---|---|
| 1 | Khảo sát pain point, thống nhất kịch bản và phân công đề tài N2-04A | Cả nhóm | ✅ 100% | Hoàn thành tài liệu phân công [PHAN-CONG-NHIEM-VU.md](../source-tool/bdd-qc-tool/PHAN-CONG-NHIEM-VU.md) |
| 2 | Xây dựng Data Models (`models.py`) & Parser JSON (`parser.py`) | Văn Thắng | ✅ 100% | Đọc thành công định dạng BDD100K JSON và chuỗi JSON từ upload stream |
| 3 | Xây dựng 4 Rule BBox (`RULE_B01` - `RULE_B04`) | Thanh Đức | ✅ 100% | Vượt qua 14/14 test cases BBox |
| 4 | Xây dựng 3 Rule Polygon (`RULE_P01` - `RULE_P03`) | Công Chứ | ✅ 100% | Hỗ trợ thuật toán giao cắt đoạn thẳng thủ công an toàn khi thiếu thư viện ngoài |
| 5 | Xây dựng 3 Rule Attribute & Duplicate (`RULE_A01` - `RULE_A03`) | Thủy Tiên | ✅ 100% | Bắt chính xác lỗi vẽ trùng lặp và thiếu thuộc tính |
| 6 | Xây dựng QC Engine & Multi-format Reporter (CLI, HTML, CSV) | Ngọc Hiếu | ✅ 100% | Xuất báo cáo console đa màu, HTML dashboard dark-mode và file CSV |
| 7 | Xây dựng Giao diện Web tương tác (Streamlit Web Demo - `app.py`) | Ngọc Hiếu | ✅ 100% | Web app chạy tại `localhost:8501`, hỗ trợ kéo thả file, canvas trực quan hóa lỗi và lọc tương tác |
| 8 | Viết bộ kiểm thử tự động (Unit test với Pytest) | Ngọc Hiếu & Nhóm | ✅ 100% | **33 / 33 test cases PASSED (100%)** |
| 9 | Đồng bộ tài liệu kỹ thuật & Hướng dẫn sử dụng | Cả nhóm | ✅ 100% | Hoàn thành `README.md`, `HUONG-DAN-KY-THUAT.md`, `requirements.txt` |

Mức hoàn thành: ✅ Xong & Đã kiểm thử · 🟡 Đang hoàn thiện · ⛔ Bị chặn

---

## 3. Kết quả đạt được & Đo lường chất lượng

1. **Bộ mã nguồn hoàn chỉnh:**
   - Đã đóng gói thành công mã nguồn tại thư mục [`source-tool/bdd-qc-tool/`](../source-tool/bdd-qc-tool/).
   - Cung cấp 2 phương thức sử dụng:
     - **Giao diện dòng lệnh (CLI):** `python main.py --input data_sample/sample_with_errors.json --output report.html`
     - **Giao diện Web tương tác (Streamlit):** `streamlit run app.py` (hỗ trợ kéo thả file, visualizer highlight box lỗi Đỏ/Vàng/Xanh, tải CSV/HTML chỉ với 1 click).

2. **Chỉ số kiểm thử tự động (Unit Tests):**
   - Đạt **33/33 test cases (100% PASS)** bao phủ đầy đủ 10 rules và luồng tích hợp end-to-end.
   - Thời gian quét: < 0.2 giây cho 1 file chứa hàng chục object.

3. **Độ chính xác và hiệu quả sơ bộ:**
   - **Tỷ lệ bắt lỗi (Detection Rate):** Bắt chính xác 100% (7/7 lỗi) trên tập benchmark nhân tạo [sample_with_errors.json](../source-tool/bdd-qc-tool/data_sample/sample_with_errors.json).
   - **Giảm tải cho Reviewer:** Dự kiến giảm **60% – 70%** thời gian soi lỗi kỹ thuật cơ bản (out-of-bounds, trùng box, polygon lỗi, thiếu thuộc tính), giúp Reviewer chỉ cần tập trung vào đánh giá ngữ cảnh và chất lượng biên viền phức tạp.

---

## 4. Vướng mắc kỹ thuật & Hướng giải quyết

| Vấn đề | Chi tiết | Hướng xử lý của nhóm |
|---|---|---|
| **Thư viện bên ngoài & Môi trường Proxy** | Cài đặt các thư viện C-extension như `shapely` có thể gặp khó khăn trên một số máy có proxy hạn chế mạng. | Nhóm đã cài đặt sẵn thuật toán hình học thuần túy (Pure Python geometry check) để kiểm tra giao cắt polygon (`RULE_P02`) hoạt động độc lập ngay cả khi không có `shapely`. |
| **Tương thích Encoding Windows Terminal** | Ký tự Unicode / Emoji hiển thị trên PowerShell mặc định có thể bị lỗi mã hóa font. | Chuẩn hóa toàn bộ text xuất ra console sang mã ASCII an toàn, đồng thời đưa toàn bộ giao diện trực quan giàu tính năng lên **Streamlit Web Demo** và **HTML Dashboard**. |

---

## 5. Kế hoạch tuần kế tiếp (Tuần 05)

1. **Chạy thử nghiệm Pilot quy mô lớn:**
   - Áp dụng BDD-QC Tool vào tập dữ liệu gán nhãn thực tế quy mô từ 500 – 1.000 frames để đánh giá độ chính xác (Precision & Recall) và tỷ lệ False Positive trên dữ liệu thật.
2. **Tối ưu hóa & Thu thập phản hồi:**
   - Cho toàn bộ thành viên trong nhóm dùng trực tiếp giao diện Web Streamlit trước mỗi lượt nộp bài để đo lường thực tế số vòng trả bài giữa Reviewer và Annotator.
3. **Mở rộng tính năng:**
   - Nghiên cứu tích hợp API đọc trực tiếp từ CVAT (nếu được cấp token API) để tự động hóa hoàn toàn luồng CI/CD cho quá trình gán nhãn.
