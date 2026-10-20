# BÁO CÁO PHÂN CÔNG NHIỆM VỤ DỰ ÁN TRIMODEL QC STUDIO (N2-04A)

> **Dự án:** TriModel BDD100K 2D Annotation QC Studio  
> **Mã đề tài:** `N2-04A` (Nhóm 2 – Giữ chất lượng gán nhãn 2D/3D)  
> **Cập nhật:** Tháng 10/2026  
> **Ghi chú nhân sự:** Bộ công cụ TriModel do **3 thành viên** trực tiếp nghiên cứu kiến trúc, triển khai giải thuật và hoàn thiện mã nguồn: **Đào Ngọc Hiếu**, **Hoàng Công Chứ**, và **Trần Thị Thủy Tiên**. *(Thành viên Đoàn Văn Thắng và Nguyễn Thanh Đức không tham gia đóng góp phần này).*

---

## 📋 TỔNG QUAN PHÂN CÔNG ĐÓNG GÓP THỰC TẾ

| Thành viên | MSSV | Vai trò chính trong dự án TriModel | Các module & Bộ luật (Rules) phụ trách |
|---|---|---|---|
| **Đào Ngọc Hiếu** | `2A202602081` | **Team Lead, System Architect & AI Ensemble** | `main.py`, `app.py`, `qc/reporter.py`, `RULE_AI01` (YOLOv8 Ensemble), Benchmark Suite (`benchmark.py`, `evaluate_qc_accuracy.py`) |
| **Hoàng Công Chứ** | `2A202602187` | **Geometry & Spatial QC Specialist** | `qc/rules/polygon_rules.py` (`RULE_P01`–`P03`), `qc/rules/bbox_rules.py` (`RULE_B01`–`B04`), Tích hợp kiểm định hình học Shapely |
| **Trần Thị Thủy Tiên** | `2A202602171` | **Data Pipeline & Attribute/Auto-Fix Specialist** | `qc/models.py`, `qc/parser.py`, `qc/rules/attribute_rules.py` (`RULE_A01`–`A03`), `class_rules.py` (`RULE_C01`), `ui/auto_fix.py` |

---

## 👤 1. ĐÀO NGỌC HIẾU (`2A202602081`) — TEAM LEAD & SYSTEM ARCHITECT

### Vai trò & Trách nhiệm
Chịu trách nhiệm thiết kế toàn bộ kiến trúc lõi của hệ thống TriModel, điều phối tích hợp các engine kiểm định, phát triển mô hình AI phát hiện xe bỏ sót (RULE_AI01), xây dựng giao diện Streamlit Pro Studio và bộ công cụ đo lường định lượng độ chính xác (Benchmark Suite).

### Các Module Phụ Trách Chính
1. **Kiến trúc hệ thống & CLI Tool (`main.py`):**
   - Thiết kế luồng pipeline thực thi: Nhận dữ liệu &rarr; Phân tích Rules song song &rarr; Tổng hợp vi phạm &rarr; Xuất báo cáo đa định dạng.
   - Xây dựng CLI chuyên nghiệp bằng `argparse` hỗ trợ `--input`, `--output`, `--format`, `--severity`, `--confidence`.
2. **Hệ thống xuất báo cáo đa nền tảng (`qc/reporter.py`):**
   - Rich Console: In bảng màu sắc nét, highlight chi tiết frame, ID đối tượng, tọa độ vi phạm và khuyến nghị sửa.
   - HTML Dashboard: Trang web báo cáo trực quan kèm biểu đồ, bộ lọc trạng thái (Error, Warning), thanh tìm kiếm nhãn theo thời gian thực.
   - Xuất dữ liệu CSV và JSON phục vụ tích hợp CI/CD và quy trình trả bài cho annotator.
3. **Mô hình AI phát hiện đối tượng bỏ sót (`qc/rules/ai_rules.py` - `RULE_AI01`):**
   - Tích hợp ensemble YOLOv8 (nano, small, medium) với Non-Maximum Suppression (NMS) và IoU cross-matching.
   - So sánh trực tiếp pixel ảnh gốc với nhãn gán sẵn, phát hiện triệt để các trường hợp annotator quên/sót xe ô tô, xe tải, xe buýt trên đường.
4. **Bộ kiểm thử định lượng khoa học (`benchmark.py` & `evaluate_qc_accuracy.py`):**
   - Xây dựng công cụ tiêm lỗi nhân tạo (Honeypot Injected Defects) mô phỏng 12 dạng lỗi thực tế.
   - Đo đạc chính xác Confusion Matrix (TP, FP, TN, FN), Precision (100%), Recall, F1-Score và mIoU cải thiện sau khi QC.
   - Xây dựng Jupyter Notebook `benchmark_qc_accuracy_colab.ipynb` phục vụ chạy thực nghiệm và fine-tune trên GPU Google Colab.
5. **Giao diện Web Tương tác cao cấp (`app.py`):**
   - Streamlit Dark Theme, Canvas trực quan hóa hộp bao/đa giác, tích hợp lọc lỗi tức thời và tính năng gửi ngược kết quả sang CVAT Server.

---

## 👤 2. HOÀNG CÔNG CHỨ (`2A202602187`) — GEOMETRY & SPATIAL QC SPECIALIST

### Vai trò & Trách nhiệm
Phụ trách chuyên sâu về toàn bộ các giải thuật kiểm tra tính hợp lệ hình học không gian 2D cho cả **Bounding Box** và **Polygon Segmentation**, ứng dụng thư viện hình học tính toán `shapely`.

### Các Module Phụ Trách Chính
1. **Bộ luật kiểm tra Đa giác phân đoạn (`qc/rules/polygon_rules.py`):**
   - **`RULE_P01` (Insufficient Vertices):** Phát hiện đa giác suy biến có ít hơn 3 đỉnh không thể tạo thành diện tích khép kín.
   - **`RULE_P02` (Self-Intersection / Knot Polygon):** Sử dụng `shapely.geometry.Polygon` để bắt các lỗi nét vẽ vắt chéo, xoắn nút hoặc viền tự cắt chính nó gây lỗi nạp vào mô hình Deep Learning.
   - **`RULE_P03` (Mask vs Box Mismatch):** Tính toán độ tương đồng không gian $\text{IoU}$ giữa khung bao cực đại của polygon và BBox được gán nhãn; cảnh báo khi $\text{IoU} < 0.70$.
2. **Bộ luật kiểm tra Bounding Box hình học (`qc/rules/bbox_rules.py`):**
   - **`RULE_B01` (Out of Bounds):** Bắt các box tràn viền hoặc có tọa độ âm ($x_1 < 0, y_1 < 0, x_2 > W, y_2 > H$).
   - **`RULE_B02` (Inverted / Zero Area):** Bắt các box có tọa độ ngược ($x_2 \le x_1$ hoặc $y_2 \le y_1$) hoặc diện tích bằng 0.
   - **`RULE_B03` (Too Small / Micro Box):** Cảnh báo các box nhiễu với diện tích siêu nhỏ ($w \times h < 64\text{px}^2$).
   - **`RULE_B04` (Abnormal Aspect Ratio):** Nhận diện các box có tỉ lệ dài/rộng bất thường ($w/h > 25$ hoặc ngược lại), loại trừ có chọn lọc các class đặc thù như rào chắn (`barrier`) hay vạch kẻ đường.
3. **Kiểm thử đơn vị hình học (`tests/test_bbox_rules.py`, `tests/test_polygon_rules.py`):**
   - Đảm bảo 100% test cases hình học chạy thông qua mà không gặp ngoại lệ Topology Exception.

---

## 👤 3. TRẦN THỊ THỦY TIÊN (`2A202602171`) — DATA PIPELINE & ATTRIBUTE/AUTO-FIX SPECIALIST

### Vai trò & Trách nhiệm
Phụ trách xây dựng hệ thống dữ liệu chuẩn hóa từ file JSON BDD100K và CVAT Task XML/JSON, hiện thực bộ luật kiểm tra thuộc tính và nhãn phân loại, đồng thời phát triển cơ chế tự động sửa lỗi (Auto-Fix Engine).

### Các Module Phụ Trách Chính
1. **Cấu trúc dữ liệu và Data Pipeline (`qc/models.py`, `qc/parser.py`):**
   - Xây dựng dataclass chuẩn hóa: `BBox2D`, `Polygon2D`, `LabeledObject`, `FrameData`, `QCError`.
   - Viết parser an toàn hỗ trợ cả cấu trúc BDD100K 100k categories và cấu trúc dữ liệu CVAT 1.1 / CVAT For Images.
   - Chuẩn hóa tọa độ tương đối/tuyệt đối giữa các định dạng khác nhau.
2. **Bộ luật kiểm tra Thuộc tính & Trùng lặp (`qc/rules/attribute_rules.py`):**
   - **`RULE_A01` (Duplicate Object Detection):** Thuật toán so sánh từng cặp nhãn trong cùng một frame; phát hiện và gắn cờ đỏ cho hai box cùng class đè lên nhau với $\text{IoU} > 0.85$ (lỗi vẽ trùng/chấm đúp của annotator).
   - **`RULE_A02` (Missing Attributes):** Kiểm tra sự hiện diện của các thuộc tính bắt buộc đối với xe và người tham gia giao thông (`occluded`, `truncated`).
   - **`RULE_A03` (Traffic Light Color Consistency):** Xác thực riêng cho class `traffic light`: bắt buộc phải có thuộc tính màu hợp lệ (`red`, `yellow`, `green`, `none`), phát hiện các trường hợp để trống hoặc điền sai.
3. **Bộ luật kiểm tra Tính nhất quán Danh mục (`qc/rules/class_rules.py` - `RULE_C01`):**
   - Bắt các lỗi gõ sai chính tả (typo) trong danh mục nhãn (ví dụ: `pedestrain` &rarr; `pedestrian`, `motocycle` &rarr; `motorcycle`).
4. **Cơ chế Tự Động Sửa Lỗi Hàng Loạt (`ui/auto_fix.py`):**
   - Phát triển thuật toán tự động nắn chỉnh:
     - Kẹp tọa độ box tràn viền về đúng biên ảnh $[0, W] \times [0, H]$.
     - Đảo lại tọa độ box bị ngược ($x_1 \leftrightarrow x_2$).
     - Xóa bỏ các box trùng lặp có độ tin cậy thấp hơn.
     - Tự động điền thuộc tính mặc định (`occluded: false`, `truncated: false`) khi bị thiếu.

---

## 📊 MA TRẬN PHÂN CÔNG THEO TỪNG QUY TẮC (RULE MATRIX)

| Mã Quy Tắc | Tên Quy Tắc | Thành viên phụ trách | Trạng thái hiện thực |
|---|---|---|:---:|
| `RULE_B01` | Out of Bounds Box | **Hoàng Công Chứ** | ✅ Đạt chuẩn 100% |
| `RULE_B02` | Inverted / Zero Area Box | **Hoàng Công Chứ** | ✅ Đạt chuẩn 100% |
| `RULE_B03` | Too Small Micro Box | **Hoàng Công Chứ** | ✅ Đạt chuẩn 100% |
| `RULE_B04` | Abnormal Aspect Ratio | **Hoàng Công Chứ** | ✅ Đạt chuẩn 100% |
| `RULE_P01` | Insufficient Vertices (<3) | **Hoàng Công Chứ** | ✅ Đạt chuẩn 100% |
| `RULE_P02` | Self-Intersecting Polygon | **Hoàng Công Chứ** | ✅ Đạt chuẩn 100% |
| `RULE_P03` | Mask vs Box IoU Mismatch | **Hoàng Công Chứ** | ✅ Đạt chuẩn 100% |
| `RULE_A01` | Duplicate Object (IoU > 0.85) | **Trần Thị Thủy Tiên** | ✅ Đạt chuẩn 100% |
| `RULE_A02` | Missing occluded / truncated | **Trần Thị Thủy Tiên** | ✅ Đạt chuẩn 100% |
| `RULE_A03` | Traffic Light Color Invalid | **Trần Thị Thủy Tiên** | ✅ Đạt chuẩn 100% |
| `RULE_C01` | Invalid Taxonomy / Class Typo | **Trần Thị Thủy Tiên** | ✅ Đạt chuẩn 100% |
| `RULE_AI01` | AI Missed Vehicle Detection | **Đào Ngọc Hiếu** | ✅ Đạt chuẩn 100% |
| `PIPELINE` | Core Architecture & Reporting | **Đào Ngọc Hiếu** | ✅ Đạt chuẩn 100% |
| `AUTO_FIX` | Automated Quality Healing Engine | **Trần Thị Thủy Tiên** | ✅ Đạt chuẩn 100% |
| `BENCHMARK`| Quantitative Precision / Recall Suite | **Đào Ngọc Hiếu** | ✅ Đạt chuẩn 100% |
