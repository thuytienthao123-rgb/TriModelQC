# Problem Backlog — Tuần 05 · 12/10 – 18/10/2026

**Task:** Nghiên cứu & Nâng cấp công cụ QC tự động hỗ trợ AI (Tri-Model Consensus Ensemble, WBF, Rule-based Engine, Reviewer Hub & SAM-2) cho dữ liệu hình ảnh BBox, Polygon & Video Tracking (Mã đề tài: **N2-04A**)  
**Lead:** Trần Thị Thủy Tiên (`2A202602171`)  
**Mã kho lưu trữ:** [P-037](https://github.com/AI20K-Build-Phase-Cohort-4A/P-037) · **Nhóm:** `t-037`

---

## Danh sách vấn đề Tuần 05

| Mã | Tóm tắt | Nhánh phát sinh | Loại | Mục guideline / Phân hệ | Trạng thái | Hướng giải quyết & Kết quả |
|---|---|---|---|---|---|---|
| [P-001](#p-001) | Mô hình SAM-2 chạy bằng Notebook Colab bị cô lập, khó cài đặt trên Windows và chưa tích hợp vào luồng Web QC Tool | Nhánh Thắng & Đức | Pain point công cụ / Tương thích | `Sam_model/` · §3 (Polygon) | 🗣️ Đang bàn | Đóng gói API Python wrapper có cờ fallback CPU/GPU để nối vào nút sinh Polygon trên Web |
| [P-002](#p-002) | Ngưỡng nhận diện Zero-shot OwlViT trong notebook SAM-2 quá thấp (`BOX_THRESHOLD = 0.08`) gây nhiều báo động giả (False Positives) ban đêm | Nhánh Thắng & Đức | Sai lệch mô hình / Báo động giả | `Sam_model/` (sam2_model.ipynb) | 🛠️ Đang xử lý | Nâng ngưỡng tin cậy lên $\ge 0.25$ hoặc dùng Tri-Model Ensemble (3/3 đồng thuận) để lọc nhiễu |
| [P-003](#p-003) | Chỉ số đánh giá IoU giữa Bounding Box hình chữ nhật đặc và Mask Polygon trong SAM-2 chưa phản ánh đúng chất lượng phân đoạn | Nhánh Thắng & Đức | Sai số phương pháp luận | `Sam_model/` (Cell 12) | 🛠️ Đang xử lý | Đổi sang so sánh BBox của Mask với BBox gốc, hoặc đo Dice/IoU với Ground Truth thực tế |
| [P-004](#p-004) | Giao diện Hàng đợi Phê duyệt (Reviewer Disposition Hub) chưa có cơ chế lưu trữ bền vững (Persistence) qua các phiên làm việc | Nhánh Thắng & Đức | Trải nghiệm người dùng / UX | `TriModel/ui/tabs/tab_error_list.py` | 🛠️ Làm tool | Bổ sung nút xuất file kết quả kiểm duyệt `disposition_audit.json`/CSV và cache session |
| [P-005](#p-005) | Mô hình đơn lẻ `yolov8n` bỏ sót vật thể nhỏ ở làn xa và xe bị che khuất; box AI bị lệch mép vật thể | Nhánh Tiên - Chứ - Hiếu | Pain point công cụ / AI Blind-spot | `TriModel/qc/ai_detector.py` · `RULE_AI01` | ✅ Đã làm tool | Triển khai Tri-Model Ensemble (3 multi-scale pipelines) kết hợp thuật toán WBF; đạt 54/54 unit tests PASS 100% |
| [P-006](#p-006) | Độ trễ hiển thị, lỗi kẹt cuộn chuột và khoảng trống header thừa trên giao diện Web | Nhánh Tiên - Chứ - Hiếu | Trải nghiệm người dùng / Hiệu năng | `TriModel/ui/styles.py`, `tab_visualizer.py` | ✅ Đã làm tool | Tối ưu hóa padding header, cố định toolbar góc trên phải, đưa iframe ẩn ra ngoài viewport, cuộn chuột mượt 100% |
| [P-007](#p-007) | Nguy cơ phân mảnh mã nguồn do tồn tại hai nhánh phát triển công cụ song song | Toàn nhóm | Quy trình phát triển / Kiến trúc | Cấu trúc thư mục kho lưu trữ | ✅ Đã giải quyết | Tái cấu trúc thành 2 phân hệ độc lập `TriModel/` và `Sam_model/`, đẩy nhánh riêng `QC_tool/TriModel` lên GitHub |
| [P-008](#p-008) | Quy trình gán nhãn một chiều khiến Annotator không thể trực tiếp sửa lỗi phát hiện từ QC Tool | Nhánh Tiên - Chứ - Hiếu | Pain point công cụ / Khả năng khắc phục | `TriModel/ui/manual_editor.py` | ✅ Đã làm tool | Tích hợp Bộ công cụ sửa tay nhãn (Annotator Suite): sửa tọa độ, class, occluded/truncated, xóa/thêm box, đối soát lại tức thì |

**Loại:** Guideline chưa nói tới · Guideline mơ hồ · Guideline mâu thuẫn · Pain point công cụ · Tương thích môi trường · Sai số phương pháp luận  
**Trạng thái:** 🔴 Mở · 🗣️ Đang bàn · ↗️ Chờ mentor · ✅ Đã chốt / Đã làm tool · 🛠️ Đang xử lý · ⚪ Bỏ

---

## P-001

**Mô hình SAM-2 chạy bằng Notebook Colab bị cô lập, khó cài đặt trên Windows và chưa tích hợp vào luồng Web QC Tool**

- **Loại:** Pain point công cụ / Tương thích môi trường
- **Phân hệ liên quan:** Phân hệ hỗ trợ gán nhãn & kiểm tra Polygon Segmentation (`source-tool/QC_tool/sam2_model/`)
- **Người phát hiện:** Trần Thị Thủy Tiên (`2A202602171`) & Đào Ngọc Hiếu (`2A202602081`) qua kiểm tra commit `8289c35` của Nguyễn Thanh Đức · 14/10/2026
- **Link kiểm chứng:** [source-tool/QC_tool/sam2_model/sam2_model.ipynb](source-tool/QC_tool/sam2_model/sam2_model.ipynb)
- **Mô tả hiện trạng:**
  - File `sam2_model.ipynb` và tệp dữ liệu `xanh_sm_night.zip` (5.5 MB) được đẩy lên kho lưu trữ dưới dạng một Jupyter Notebook thực nghiệm độc lập (được thiết kế cho môi trường Google Colab trên Linux với câu lệnh `!pip install git+https://github.com/facebookresearch/sam2.git`).
  - Khi thành viên nhóm tải về chạy thử trên môi trường Windows thông thường:
    1. Quá trình biên dịch gói `sam2` bị thất bại vì phụ thuộc vào trình biên dịch C++/CUDA (`_C` extension của PyTorch), yêu cầu phải cài đặt bộ Visual Studio C++ Build Tools phức tạp.
    2. Notebook chạy tách biệt hoàn toàn khỏi luồng ứng dụng chính, chưa có hàm hay API Python để giao diện Web Streamlit (`app.py`) hoặc dòng lệnh CLI (`main.py`) gọi vào phục vụ việc tự động kiểm tra hay sửa lỗi polygon (`RULE_P01`–`RULE_P03`).
    3. Đường dẫn dữ liệu bị gắn cứng (`image_folder = "xanh_sm_night"`), tải checkpoint trực tiếp từ server Meta (`dl.fbaipublicfiles.com`) gây phụ thuộc vào kết nối mạng bên ngoài.
- **Hướng đề xuất & Xử lý:**
  1. Đóng gói mã nguồn gọi SAM-2 thành một class service độc lập (ví dụ `qc/sam2_annotator.py`), cung cấp phương thức `segment_box_to_polygon(image, bbox)` trả về tọa độ polygon chuẩn hóa.
  2. Bổ sung cơ chế fallback linh hoạt: Nếu máy không có GPU CUDA hoặc không cài được thư viện `sam2`, hệ thống tự động chuyển sang giải thuật trích xuất đường viền cục bộ bằng OpenCV Canny/FindContours đã có sẵn trong `tab_visualizer.py` để đảm bảo ứng dụng không bị crash.
  3. Tích hợp nút bấm trực tiếp trên giao diện Web: Cho phép reviewer chọn một BBox có nghi vấn viền polygon và bấm "Tự động sinh Polygon chuẩn" thay vì phải mở Colab chạy thủ công.
- **Trạng thái:** 🗣️ Đang bàn bạc để thống nhất tích hợp trong tuần 06.

---

## P-002

**Ngưỡng nhận diện Zero-shot OwlViT trong notebook SAM-2 quá thấp (`BOX_THRESHOLD = 0.08`) gây nhiều báo động giả (False Positives) ban đêm**

- **Loại:** Sai lệch mô hình / Báo động giả
- **Phân hệ liên quan:** `source-tool/QC_tool/sam2_model/sam2_model.ipynb` (Cell 8)
- **Người phát hiện:** Hoàng Công Chứ (`2A202602187`) & Trần Thị Thủy Tiên (`2A202602171`) · 14/10/2026
- **Mô tả hiện trạng:**
  - Trong Cell 8 của notebook `sam2_model.ipynb`, mô hình phát hiện vật thể zero-shot OwlViT (`google/owlvit-base-patch32`) được thiết lập với ngưỡng phát hiện:
    ```python
    BOX_THRESHOLD = 0.08  # Significantly lower threshold for challenging night-time settings
    ```
  - Mức ngưỡng 0.08 (tức chỉ cần độ tin cậy $8\%$) là quá thấp đối với các bài toán thị giác máy tính. Trong tập dữ liệu ban đêm `xanh_sm_night`, ánh đèn pha, vệt sáng phản chiếu trên mặt đường nhựa ướt và biển hiệu đều bị nhận diện nhầm thành `car` hoặc `vehicle`.
  - Hậu quả: Mô hình sinh ra hàng loạt bounding box rác (False Positives). Khi các box rác này được đưa làm prompt đầu vào cho SAM-2, SAM-2 vẫn cố gắng phân đoạn các mảng bóng râm hoặc vệt sáng thành các đa giác sai lệch, đi ngược lại tiêu chí của công cụ QC (vốn đòi hỏi độ chính xác cao và phải giảm thiểu tối đa báo động giả cho người duyệt).
- **Hướng đề xuất & Xử lý:**
  1. Thiết lập ngưỡng tin cậy hợp lý tối thiểu $\ge 0.25 - 0.35$ đối với mô hình đơn lẻ.
  2. Thay vì dùng mô hình zero-shot đơn lẻ với ngưỡng thấp, áp dụng giải pháp **Tri-Model Consensus Ensemble** của nhánh chính (kết hợp 3 pipeline mô hình với độ phân giải cao và TTA) để phát hiện vật thể; chỉ những đối tượng được tối thiểu 2 hoặc cả 3 mô hình cùng đồng thuận mới chuyển sang SAM-2 để trích xuất viền polygon.
- **Trạng thái:** 🛠️ Đang xử lý, sẽ đưa vào buổi họp kỹ thuật đối chứng giữa hai nhánh.

---

## P-003

**Chỉ số đánh giá IoU giữa Bounding Box hình chữ nhật đặc và Mask Polygon trong SAM-2 chưa phản ánh đúng chất lượng phân đoạn**

- **Loại:** Sai số phương pháp luận đánh giá
- **Phân hệ liên quan:** `source-tool/QC_tool/sam2_model/sam2_model.ipynb` (Cell 12: `calculate_iou`)
- **Người phát hiện:** Đào Ngọc Hiếu (`2A202602081`) · 14/10/2026
- **Mô tả hiện trạng:**
  - Trong Cell 12 của notebook `sam2_model.ipynb`, mã nguồn sử dụng hàm tính toán IoU như sau:
    ```python
    # 1. Create a binary mask representing the solid bounding box area
    box_mask = np.zeros((height, width), dtype=bool)
    box_mask[y0:y1, x0:x1] = True

    # 2. Extract SAM 2 mask
    sam_mask = mask[0] > 0.0

    # 3. Compute IoU
    iou_score = calculate_iou(box_mask, sam_mask)
    ```
  - Cách tính này lấy toàn bộ diện tích hình chữ nhật đặc kín của Bounding Box (`box_mask`) để đo mức độ trùng khớp với Mask của chiếc xe do SAM-2 sinh ra (`sam_mask`).
  - **Vấn đề bản chất:** Một chiếc xe ô tô trong thực tế không bao giờ lấp kín 100% hình chữ nhật bao quanh nó (luôn có khoảng trống ở 4 góc, gầm xe, mui xe vát...). Do đó, ngay cả khi SAM-2 phân đoạn hoàn hảo từng pixel của thân xe, giá trị IoU lý thuyết giữa mask thân xe và hình chữ nhật đặc cũng chỉ dao động quanh mức $0.60 - 0.75$.
  - Việc dùng chỉ số này làm thước đo đánh giá chất lượng phân đoạn (đạt trung bình ~0.65) dễ dẫn đến kết luận sai lầm rằng mô hình SAM-2 cắt viền kém hoặc thuật toán bị lỗi.
- **Hướng đề xuất & Xử lý:**
  1. Đo lường theo đúng bản chất: Trích xuất Bounding Box ngoại tiếp nhỏ nhất của Mask SAM-2 (`mask_to_bbox`), sau đó tính IoU giữa BBox ngoại tiếp này với BBox do Detector đề xuất.
  2. Trong trường hợp đánh giá độ khít của Polygon với BBox, áp dụng chuẩn theo quy tắc `RULE_P03` (Mask vs Box Mismatch) đã được chuẩn hóa trong Core Engine: $\text{IoU}(\text{Box}(\text{poly}), \text{box2d}) \ge 0.70$.
- **Trạng thái:** 🛠️ Đang cập nhật lại công thức đo lường.

---

## P-004

**Giao diện Hàng đợi Phê duyệt (Reviewer Disposition Hub) chưa có cơ chế lưu trữ bền vững (Persistence) qua các phiên làm việc**

- **Loại:** Trải nghiệm người dùng (UX) / Quản lý trạng thái
- **Phân hệ liên quan:** Màn hình kiểm duyệt `ui/tabs/tab_error_list.py`
- **Người phát hiện:** Đoàn Văn Thắng (`2A202602287`) & Hoàng Công Chứ (`2A202602187`) · 14/10/2026
- **Mô tả hiện trạng:**
  - Phân hệ kiểm duyệt mới đã xây dựng các nút thao tác chuyên nghiệp cho Reviewer: Xác nhận lỗi (Confirm Defect), Đánh dấu báo sai (False Alarm) và Ghi chú nguyên nhân (Annotation Feedback Notes).
  - Tuy nhiên, toàn bộ dữ liệu phản hồi này hiện chỉ được lưu tạm trong biến nhớ `st.session_state` của Streamlit.
  - Khi Reviewer vô tình bấm F5 (Reload trang), chuyển qua lại giữa các tập dữ liệu hoặc khi server tự khởi động lại, toàn bộ công sức duyệt hàng chục ca lỗi trước đó sẽ bị xóa sạch, người dùng phải thao tác lại từ đầu.
- **Hướng đề xuất & Xử lý:**
  1. Bổ sung tính năng **Xuất Biên Bản Kiểm Duyệt (Export Disposition Audit)**: Thêm nút tải file `audit_disposition.json` hoặc `.csv` ghi nhận đầy đủ quyết định của reviewer kèm timestamp và ghi chú.
  2. Tự động sao lưu trạng thái kiểm duyệt vào file cache cục bộ dạng `.cache/disposition_<session_id>.json` để khi mở lại dữ liệu, hệ thống tự động khôi phục các quyết định cũ.
- **Trạng thái:** 🛠️ Đang xây dựng tính năng xuất file và lưu cache.

---

## P-005

**Mô hình đơn lẻ `yolov8n` bỏ sót vật thể nhỏ ở làn xa và xe bị che khuất; box AI bị lệch mép vật thể**

- **Loại:** Pain point công cụ / Điểm mù AI
- **Phân hệ liên quan:** `qc/ai_detector.py` · Quy tắc phát hiện vật thể bỏ sót `RULE_AI01`
- **Người phát hiện:** Trần Thị Thủy Tiên (`2A202602171`) & Đào Ngọc Hiếu (`2A202602081`) · 12/10/2026
- **Mô tả hiện trạng:**
  - Ở phiên bản ban đầu, công cụ chỉ tích hợp mô hình đơn lẻ `yolov8n.pt` chạy ở kích thước chuẩn 640px.
  - Khi thử nghiệm trên ảnh camera giao thông độ phân giải cao 1080p:
    1. Các phương tiện ở làn đường xa (chiếm diện tích nhỏ $< 30\text{px}$) bị bỏ sót hoàn toàn.
    2. Các xe tải lớn bị cắt góc ở mép khung hình hoặc người đi bộ bị bóng râm che khuất không được nhận diện.
    3. Hộp bao của model đơn lẻ hay bị rung lắc, lệch mép so với thực tế, gây khó khăn cho việc tự động bù nhãn.
- **Đánh giá 4 điều kiện làm tool:**
  1. *Ghi trong backlog:* Thuộc nhóm Pain point công cụ cấp thiết.
  2. *Lặp lại nhiều lần:* Xuất hiện liên tục trên toàn bộ các frame camera giao thông đông đúc.
  3. *Lợi ích:* Cần giảm $\ge 70\%$ công sức reviewer phải căng mắt soi tìm xe sót trên ảnh 1080p.
  4. *CVAT chưa có sẵn:* CVAT không có cơ chế tự động bù box đồng thuận đa mô hình.
- **Hướng xử lý & Kết quả:**
  - ✅ **Đã hoàn thành module `TriModel/qc/ai_detector.py`:**
    - Xây dựng kiến trúc **Tri-Model Ensemble**: Kết hợp Model 1 (Base 640px), Model 2 (High-Res Specialist 960px soi xe nhỏ ở làn xa) và Model 3 (TTA Augmented 800px xóa góc khuất).
    - Cài đặt thuật toán **Weighted Boxes Fusion (WBF)** tính trung bình có trọng số tọa độ theo confidence, giúp hộp bao bám khít mép vật thể.
    - Cung cấp 2 chế độ đồng thuận: **Strict (3/3 model cùng nhận diện)** giúp triệt tiêu $95\%$ báo động giả; và **Majority (2/3 model)** bao quát tối đa các góc khuất.
    - Tích hợp tính năng **1-Click Auto-Fix**: Xuất file `.txt` YOLO đã tự động bù các box thiếu để nạp thẳng lại vào công cụ gán nhãn.
    - Đã vượt qua toàn bộ **54/54 unit test cases** tự động bằng Pytest (PASS 100%).
- **Trạng thái:** ✅ Đã hoàn thành và kiểm thử thành công 100%.

---

## P-006

**Độ trễ hiển thị, lỗi kẹt cuộn chuột và khoảng trống header thừa trên giao diện Web**

- **Loại:** Trải nghiệm người dùng (UX) & Hiệu năng
- **Phân hệ liên quan:** `source-tool/QC_tool/TriModel/ui/styles.py`, `tab_visualizer.py`
- **Người phát hiện:** Hoàng Công Chứ (`2A202602187`) & Trần Thị Thủy Tiên (`2A202602171`) · 15/10/2026
- **Mô tả hiện trạng:**
  - Phần đầu trang bên phải xuất hiện khoảng trống rỗng màu đen lớn (~150-200px), cụm nút `Deploy` và `⋮` bị rơi xuống giữa trang gây bất hợp lý về mặt thị giác.
  - Vùng nội dung bên phải bị kẹt cuộn chuột (mouse wheel) do thẻ `iframe` của Streamlit Components chiếm dụng sự kiện lăn chuột.
- **Hướng xử lý & Kết quả:**
  - ✅ **Đã tối ưu hóa toàn diện CSS & Layout:**
    1. Giảm `padding-top: 0.6rem !important;` trên `.block-container`, triệt tiêu hoàn toàn khoảng trống đen rỗng.
    2. Cố định cụm `stToolbar` (chứa nút Deploy và menu 3 chấm) tại vị trí góc trên cùng bên phải (`top: 4px; right: 12px; z-index: 1000000;`).
    3. Đưa các thẻ iframe ẩn ra khỏi viewport (`position: fixed; bottom: -200px; pointer-events: none;`) và kích hoạt `overflow-y: auto !important`, giúp cuộn chuột mượt mà 100%.
- **Trạng thái:** ✅ Đã làm tool và kiểm tra trực quan đạt chuẩn.

---

## P-007

**Nguy cơ phân mảnh mã nguồn do tồn tại hai nhánh phát triển công cụ song song**

- **Loại:** Quy trình phát triển & Quản lý kiến trúc
- **Phân hệ liên quan:** Toàn bộ dự án kho lưu trữ `P-037`
- **Người phát hiện:** Trần Thị Thủy Tiên (`2A202602171`) — Team Lead · 15/10/2026
- **Mô tả hiện trạng:**
  - Việc tồn tại 2 nhóm công cụ (nhánh TriModel của Tiên - Chứ - Hiếu và nhánh Sam_model của Thắng - Đức) trong cùng thư mục `QC_tool` gây khó khăn cho việc quản lý mã nguồn, chạy kiểm thử và đóng gói nộp bài.
- **Hướng xử lý & Kết quả:**
  - ✅ **Đã tái cấu trúc thư mục rõ ràng và độc lập:**
    1. Tạo 2 thư mục con riêng biệt bên trong `source-tool/QC_tool`:
       - `TriModel/`: Chứa toàn bộ sản phẩm QC Tool Nâng Cao tích hợp AI Ensemble, 15 bộ luật, Focus Loupe, Annotator Suite và 54 tests.
       - `Sam_model/`: Chứa notebook nghiên cứu SAM-2 và tập dữ liệu ban đêm của Thắng - Đức kèm tài liệu README riêng.
    2. Tạo nhánh Git riêng `QC_tool/TriModel` và đã đẩy toàn bộ mã nguồn cùng tập dữ liệu `dataset_final` lên GitHub an toàn, không ảnh hưởng đến nhánh khác.
- **Trạng thái:** ✅ Đã giải quyết triệt để.

---

## P-008

**Quy trình gán nhãn một chiều khiến Annotator không thể trực tiếp sửa lỗi phát hiện từ QC Tool**

- **Loại:** Pain point công cụ / Khả năng khắc phục lỗi (Actionability)
- **Phân hệ liên quan:** `source-tool/QC_tool/TriModel/ui/manual_editor.py`
- **Người phát hiện:** Trần Thị Thủy Tiên (`2A202602171`) · 16/10/2026
- **Mô tả hiện trạng:**
  - Các công cụ QC truyền thống chỉ dừng lại ở mức "bắt lỗi và xuất danh sách", sau đó Annotator phải mở lại phần mềm CVAT để tìm từng ảnh, vẽ lại từng box rồi nộp lại qua nhiều vòng duyệt tốn kém thời gian.
  - Khi Trợ lý AI phát hiện xe hoặc người đi bộ bị bỏ sót (`RULE_AI01`), người dùng không có cách nào nạp nhanh vào nhãn mà phải tự đo tọa độ thủ công.
- **Hướng xử lý & Kết quả:**
  - ✅ **Đã phát triển Bộ công cụ sửa tay nhãn (Annotator Suite):**
    1. Form sửa tay trực tiếp: Cho phép điều chỉnh tọa độ $[x_1, y_1, x_2, y_2]$, thay đổi Category (danh mục 12 lớp BDD100K) và thuộc tính `occluded`, `truncated`.
    2. Nút **💾 Lưu Thay Đổi** và **🗑️ Xóa Box Này**: Tự động chạy lại quy trình đối soát 15 bộ luật thời gian thực (`_reevaluate_qc`), làm mới điểm số nghiệm thu ngay tức thì.
    3. Nút **➕ Nạp Vào Nhãn**: 1-click đưa vật thể AI phát hiện thiếu vào tập nhãn chính thức.
    4. Nút xuất và tải về trực tiếp tệp nhãn đã chữa lành: **BDD100K JSON** và **YOLO ZIP**, sẵn sàng đưa thẳng vào huấn luyện mô hình.
- **Trạng thái:** ✅ Đã làm tool và tích hợp trực tiếp vào Tab 2.

