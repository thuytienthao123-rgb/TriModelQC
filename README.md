# BDD100K 2D Annotation QC Tool (Mã đề: N2-04A)

> **Công cụ tự động kiểm tra chất lượng (Linter / Quality Control) cho Bounding Box và Segmentation 2D trên dataset BDD100K.**  
> Giải quyết triệt để vấn đề lỗi gán nhãn lặp lại, giảm số vòng trả bài giữa Reviewer và Annotator.

---

## 1. Thông tin đề tài

- **Mã đề tài:** `N2-04A` (Nhóm 2 – Giữ chất lượng)
- **Tên đề tài:** QC tự động cho bbox và segmentation 2D
- **Dataset mục tiêu:** BDD100K (hỗ trợ cả định dạng JSON BDD100K và export CVAT)
- **Chỉ số đo lường (Baseline → Pilot):**
  - **Tỷ lệ lỗi bắt được tự động:** $\ge 90\%$ trước vòng review chéo.
  - **Số vòng trả lại bài/job:** Giảm từ trung bình 2–3 vòng xuống còn $\le 1$ vòng.
  - **Thời gian rà soát của Reviewer:** Giảm $\ge 60\%$.

---

## 2. Các nhóm lỗi Tool phát hiện (Core Rules)

| Nhóm | Mã Rule | Tên lỗi | Mô tả chi tiết | Mức độ |
|---|---|---|---|---|
| **BBox** | `RULE_B01` | **Out of Bounds** | Tọa độ box vượt ra ngoài khung hình ($x < 0, y < 0, x > W, y > H$) | 🔴 ERROR |
| **BBox** | `RULE_B02` | **Inverted / Zero Box** | Tọa độ bị đảo ngược hoặc diện tích bằng 0 ($x_2 \le x_1$ hoặc $y_2 \le y_1$) | 🔴 ERROR |
| **BBox** | `RULE_B03` | **Too Small Box** | Box quá nhỏ ($w \times h < 64\text{px}$), nghi ngờ chấm nhầm/nhiễu | 🟡 WARNING |
| **BBox** | `RULE_B04` | **Abnormal Ratio** | Tỉ lệ khung hình dị thường ($w/h > 25$ hoặc $h/w > 25$) | 🟡 WARNING |
| **Poly** | `RULE_P01` | **Insufficient Vertices** | Đa giác polygon có ít hơn 3 đỉnh | 🔴 ERROR |
| **Poly** | `RULE_P02` | **Self-Intersection** | Đa giác bị xoắn, vắt chéo viền (tự cắt chính nó) | 🔴 ERROR |
| **Poly** | `RULE_P03` | **Mask vs Box Mismatch** | Khung bao của polygon lệch quá nhiều so với BBox được khai báo ($\text{IoU} < 0.7$) | 🟡 WARNING |
| **Attr** | `RULE_A01` | **Duplicate Object** | Hai box cùng class đè lên nhau với $\text{IoU} > 0.85$ (vẽ trùng) | 🔴 ERROR |
| **Attr** | `RULE_A02` | **Missing Attributes** | Thiếu thuộc tính bắt buộc (`occluded`, `truncated`) | 🟡 WARNING |
| **Attr** | `RULE_A03` | **Traffic Light Color** | Vật thể là `traffic light` nhưng thiếu thuộc tính màu đèn | 🔴 ERROR |

---

## 3. Phân công đội ngũ (5 Thành viên)

| Thành viên | MSSV | Vai trò trong dự án | File phụ trách chính |
|---|---|---|---|
| **Đào Ngọc Hiếu** | `2A202602081` | **Team Lead & Core Integration** | `main.py`, `qc/reporter.py`, Benchmark |
| **Đoàn Văn Thắng** | `2A202602327` | **Data Engineer** | `qc/models.py`, `qc/parser.py` |
| **Nguyễn Thanh Đức** | `2A202602279` | **BBox QC Specialist** | `qc/rules/bbox_rules.py` |
| **Hoàng Công Chứ** | `2A202602187` | **Segmentation QC Specialist** | `qc/rules/polygon_rules.py` |
| **Trần Thị Thủy Tiên** | `2A202602171` | **Consistency & Attribute Specialist** | `qc/rules/attribute_rules.py` |

👉 Chi tiết nhiệm vụ và code mẫu của từng thành viên xem tại: [PHAN-CONG-NHIEM-VU.md](PHAN-CONG-NHIEM-VU.md)

---

## 4. Kiến trúc mã nguồn

```text
source-tool/bdd-qc-tool/
├── README.md                  # Tài liệu tổng quan (file này)
├── PHAN-CONG-NHIEM-VU.md      # Bảng việc chi tiết cho 5 thành viên
├── HUONG-DAN-KY-THUAT.md      # Chuẩn code, quy trình Git và hướng dẫn test
├── requirements.txt           # Thư viện phụ thuộc (shapely, rich, tabulate)
├── main.py                    # Điểm khởi chạy CLI tool
├── data_sample/               # Thư mục chứa file dữ liệu kiểm thử
│   ├── sample_valid.json
│   └── sample_with_errors.json
└── qc/
    ├── __init__.py
    ├── models.py              # [Văn Thắng] Data structures chuẩn
    ├── parser.py              # [Văn Thắng] Module đọc file nhãn
    ├── reporter.py            # [Ngọc Hiếu] Xuất báo cáo Console/HTML/CSV
    └── rules/
        ├── __init__.py
        ├── base.py            # Base class cho Rule
        ├── bbox_rules.py      # [Thanh Đức] B01 - B04
        ├── polygon_rules.py   # [Công Chứ] P01 - P03
        └── attribute_rules.py # [Thủy Tiên] A01 - A03
```

---

## 5. Cài đặt và sử dụng

### 5.1 Cài đặt môi trường
Yêu cầu Python 3.9 trở lên:
```bash
cd source-tool/bdd-qc-tool
pip install -r requirements.txt
```

### 5.2 Chạy kiểm tra file nhãn
```bash
# Kiểm tra file nhãn và in báo cáo tóm tắt trên terminal:
python main.py --input data_sample/sample_with_errors.json

# Xuất báo cáo chi tiết ra file HTML:
python main.py --input data_sample/sample_with_errors.json --output report.html

# Xuất báo cáo ra file CSV (dành cho annotator lọc theo ID để sửa):
python main.py --input data_sample/sample_with_errors.json --output report.csv
```

### 5.3 Khởi chạy Giao diện Web Trực quan (Streamlit Pro Dashboard)
Hệ thống cung cấp giao diện Web tương tác cao cấp (Dark Glassmorphism UI) hỗ trợ soi lỗi canvas, lọc lỗi, và tự động sửa nhãn:
```bash
streamlit run app.py
```
👉 Truy cập ngay trên trình duyệt tại: `http://localhost:8501`

**Tính năng nổi bật trên Web:**
- 🛡️ **Đánh giá Nghiệm Thu QC (QC Verdict):** Tự động phân loại `Approved` / `Conditional Pass` / `Rejected`.
- 🖼️ **Visualizer Canvas Tương Tác:** Soi trực quan viền box, đa giác polygon, đổi frame nhanh (`Prev / Next Error Frame`), và **tâm ngắm tiêu điểm (Crosshair Focus Highlight)**.
- 🛠️ **1-Click Auto-Fix Engine:** Tự động sửa 6 nhóm lỗi hình học & thuộc tính phổ biến và tải về tệp BDD100K sạch lỗi.
- 🤖 **AI Assistant (YOLOv8):** Đối soát ảnh thực tế để phát hiện xe/người bị annotator bỏ sót (`RULE_AI01`).
- 📥 **Export Hub:** Xuất báo cáo đa định dạng CSV (cho Annotator sửa theo ID) và HTML tương tác độc lập.

---

## 6. Kế hoạch nghiệm thu & Báo cáo Mentor

1. **Chuẩn bị bộ Benchmark:** Bộ dữ liệu mẫu gồm `sample_with_errors.json` (7 vi phạm kỹ thuật) và `sample_valid.json` (bộ chuẩn 100% đạt nghiệm thu).
2. **Chạy đối chứng (Baseline vs Pilot):**
   - **Cách cũ (Manual):** Reviewer soi từng ảnh bằng mắt, bấm giờ và ghi nhận số lỗi bắt được.
   - **Cách mới (Tool):** Chạy tool quét tự động chỉ trong 0.2s, hiển thị trực quan canvas và xuất danh sách lỗi.
3. **Tổng hợp số liệu:** Độ chính xác 100% trên bộ rule toán học, giảm $\ge 60\%$ thời gian review và giảm số vòng trả bài xuống $\le 1$ vòng.
