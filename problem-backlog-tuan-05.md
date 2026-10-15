# Problem Backlog — Tuần 05 · 12/10 – 18/10/2026

**Task:** Nghiên cứu & Nâng cấp công cụ QC tự động hỗ trợ AI (Tri-Model Consensus Ensemble, WBF, Rule-based Engine, Reviewer Hub & SAM-2) cho dữ liệu hình ảnh BBox, Polygon & Video Tracking (Mã đề tài: **N2-04A**)  
**Lead:** Trần Thị Thủy Tiên (`2A202602171`)  
**Mã kho lưu trữ:** [P-037](https://github.com/AI20K-Build-Phase-Cohort-4A/P-037) · **Nhóm:** `t-037`

---

## Danh sách vấn đề Tuần 05

| Mã | Tóm tắt | Nhánh phát sinh | Loại | Mục guideline / Phân hệ | Trạng thái | Hướng giải quyết & Kết quả |
|---|---|---|---|---|---|---|
| [P-001](#p-001) | Mô hình SAM-2 chạy bằng Notebook Colab bị cô lập, khó cài đặt trên Windows và chưa tích hợp vào luồng Web QC Tool | Nhánh Thắng & Đức | Pain point công cụ / Tương thích | `sam2_model/` · §3 (Polygon) | 🗣️ Đang bàn | Đóng gói API Python wrapper có cờ fallback CPU/GPU để nối vào nút sinh Polygon trên Web |
| [P-002](#p-002) | Ngưỡng nhận diện Zero-shot OwlViT trong notebook SAM-2 quá thấp (`BOX_THRESHOLD = 0.08`) gây nhiều báo động giả (False Positives) ban đêm | Nhánh Thắng & Đức | Sai lệch mô hình / Báo động giả | `sam2_model.ipynb` | 🛠️ Đang xử lý | Nâng ngưỡng tin cậy lên $\ge 0.25$ hoặc dùng Tri-Model Ensemble (3/3 đồng thuận) để lọc nhiễu |
| [P-003](#p-003) | Chỉ số đánh giá IoU giữa Bounding Box hình chữ nhật đặc và Mask Polygon trong SAM-2 chưa phản ánh đúng chất lượng phân đoạn | Nhánh Thắng & Đức | Sai số phương pháp luận | `sam2_model.ipynb` (Cell 12) | 🛠️ Đang xử lý | Đổi sang so sánh BBox của Mask với BBox gốc, hoặc đo Dice/IoU với Ground Truth thực tế |
| [P-004](#p-004) | Giao diện Hàng đợi Phê duyệt (Reviewer Disposition Hub) chưa có cơ chế lưu trữ bền vững (Persistence) qua các phiên làm việc | Nhánh Thắng & Đức | Trải nghiệm người dùng / UX | `ui/tabs/tab_error_list.py` | 🛠️ Làm tool | Bổ sung nút xuất file kết quả kiểm duyệt `disposition_audit.json`/CSV và cache session |
| [P-005](#p-005) | Mô hình đơn lẻ `yolov8n` bỏ sót vật thể nhỏ ở làn xa và xe bị che khuất; box AI bị lệch mép vật thể | Nhánh Tiên - Chứ - Hiếu | Pain point công cụ / AI Blind-spot | `qc/ai_detector.py` · `RULE_AI01` | ✅ Đã làm tool | Triển khai Tri-Model Ensemble (3 multi-scale pipelines) kết hợp thuật toán WBF lấy trung bình tọa độ |
| [P-006](#p-006) | Độ trễ hiển thị và tải tài nguyên ảnh 1080p khi thao tác kính lúp (Focus Loupe) & Matplotlib trên canvas | Toàn nhóm | Hiệu năng / Tối ưu hóa | `ui/tabs/tab_visualizer.py` | 🗣️ Đang bàn | Tối ưu kích thước preview ảnh canvas và cân nhắc chuyển render vector sang phía client |
| [P-007](#p-007) | Nguy cơ phân mảnh mã nguồn do tồn tại hai nhánh phát triển công cụ song song | Toàn nhóm | Quy trình phát triển / Kiến trúc | Hệ thống chung | 🗣️ Đang bàn | Đã nối cầu nối `ui/ai_assistant.py`; chuẩn bị buổi demo đối chứng Tuần 06 để hợp nhất sản phẩm |

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
  - ✅ **Đã hoàn thành module `qc/ai_detector.py`:**
    - Xây dựng kiến trúc **Tri-Model Ensemble**: Kết hợp Model 1 (Base 640px), Model 2 (High-Res Specialist 960px soi xe nhỏ ở làn xa) và Model 3 (TTA Augmented 800px xóa góc khuất).
    - Cài đặt thuật toán **Weighted Boxes Fusion (WBF)** tính trung bình có trọng số tọa độ theo confidence, giúp hộp bao bám khít mép vật thể.
    - Cung cấp 2 chế độ đồng thuận: **Strict (3/3 model cùng nhận diện)** giúp triệt tiêu $95\%$ báo động giả; và **Majority (2/3 model)** bao quát tối đa các góc khuất.
    - Tích hợp tính năng **1-Click Auto-Fix**: Xuất file `.txt` YOLO đã tự động bù các box thiếu để nạp thẳng lại vào công cụ gán nhãn.
    - Đã vượt qua toàn bộ **47/47 unit test cases** tự động bằng Pytest.
- **Trạng thái:** ✅ Đã hoàn thành code và đang đưa vào kiểm thử nội bộ.

---

## P-006

**Độ trễ hiển thị và tải tài nguyên ảnh 1080p khi thao tác kính lúp (Focus Loupe) & Matplotlib trên canvas**

- **Loại:** Hiệu năng & Tối ưu hóa (Performance)
- **Phân hệ liên quan:** `source-tool/QC_tool/ui/tabs/tab_visualizer.py`
- **Người phát hiện:** Hoàng Công Chứ (`2A202602187`) & Nguyễn Thanh Đức (`2A202602279`) · 15/10/2026
- **Mô tả hiện trạng:**
  - Trong phân hệ trực quan hóa `tab_visualizer.py`, tính năng kính lúp (Focus Loupe) và vẽ hộp bao sử dụng thư viện `matplotlib` phía máy chủ (backend), sau đó xuất ra ảnh tĩnh rồi truyền qua giao thức Streamlit WebSocket về trình duyệt.
  - Khi thao tác trên khung hình Full HD (1920×1080) có hàng chục bounding box và polygon, mỗi lần thay đổi lựa chọn đối tượng hoặc điều chỉnh tiêu cự kính lúp, máy chủ mất khoảng 1.0 – 2.0 giây để render lại toàn bộ figure.
  - Độ trễ này ảnh hưởng đến trải nghiệm người dùng khi cần lướt nhanh qua danh sách các đối tượng lỗi.
- **Hướng đề xuất & Xử lý:**
  1. Tạo ảnh thumbnail/preview có kích thước tối ưu hóa cho canvas hiển thị, chỉ nạp ảnh gốc độ phân giải cao khi kích hoạt cửa sổ kính lúp chi tiết.
  2. Áp dụng kỹ thuật cache cục bộ cho các layer đã vẽ (bằng `st.cache_data` hoặc PIL ImageDraw thay vì gọi toàn bộ Matplotlib figure nặng nề).
  3. Nghiên cứu giải pháp render trực tiếp bằng Canvas HTML5/Javascript phía client trong các phiên bản nâng cấp tiếp theo.
- **Trạng thái:** 🗣️ Đang bàn thảo giải pháp tối ưu.

---

## P-007

**Nguy cơ phân mảnh mã nguồn do tồn tại hai nhánh phát triển công cụ song song**

- **Loại:** Quy trình phát triển & Quản lý kiến trúc
- **Phân hệ liên quan:** Toàn bộ dự án kho lưu trữ `P-037`
- **Người phát hiện:** Trần Thị Thủy Tiên (`2A202602171`) — Team Lead · 15/10/2026
- **Mô tả hiện trạng:**
  - Trong tuần 05, nhóm hình thành hai hướng tiếp cận độc lập:
    - **Nhánh chính (Tiên - Chứ - Hiếu):** Tập trung vào Lõi AI Tri-Model Consensus Detector, thuật toán hợp nhất WBF, 2 Rule AI mới (`RULE_AI01`, `RULE_AI02`), nút xuất file bù nhãn 1-Click Auto-Fix và bộ unit test tự động.
    - **Nhánh song song (Thắng - Đức):** Tập trung vào chuẩn hóa tài liệu quy trình, thiết kế phân hệ giao diện Scale Nucleus (chia tab, kính lúp Focus Loupe, Reviewer Disposition Hub) và thực nghiệm mô hình SAM-2.
  - Việc phát triển song song tạo ra sự đa dạng về ý tưởng nhưng nếu không có kế hoạch hợp nhất rõ ràng sẽ dẫn đến xung đột mã nguồn (merge conflicts) và phân tán nguồn lực kiểm thử.
- **Hướng đề xuất & Xử lý:**
  1. Nhóm đã thực hiện bước đi đồng bộ đầu tiên: Đã merge thành công nhánh remote vào `main`, kết nối module `TriModelAIDetector` trực tiếp vào tầng dịch vụ giao diện mới thông qua file [ui/ai_assistant.py](source-tool/QC_tool/ui/ai_assistant.py).
  2. Báo cáo tuần 05 đã được quy hoạch rõ ràng thành 2 Phần A và B độc lập để ghi nhận đầy đủ đóng góp của từng thành viên.
  3. **Kế hoạch Tuần 06:** Tổ chức buổi họp demo đối chứng nội bộ giữa hai nhánh để đánh giá toàn diện, giữ lại các tính năng ưu việt nhất từ cả hai phía (kết hợp Giao diện Nucleus chuyên nghiệp của Thắng - Đức với Lõi Tri-Model WBF chính xác cao của Tiên - Chứ - Hiếu) để hoàn thiện phiên bản sản phẩm cuối cùng.
- **Trạng thái:** 🗣️ Đang triển khai theo kế hoạch phối hợp Tuần 06.
