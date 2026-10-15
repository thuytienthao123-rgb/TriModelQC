# BÁO CÁO TIẾN ĐỘ DỰ ÁN — TUẦN 05 (12/10 – 18/10/2026)

**Mã kho lưu trữ:** [P-037](https://github.com/AI20K-Build-Phase-Cohort-4A/P-037) · **Nhóm:** `t-037`  
**Dự án:** Hệ thống hỗ trợ kiểm soát và đánh giá chất lượng dữ liệu hình ảnh (AI-Assisted Quality Control Tool)  
**Lead tuần 05:** Trần Thị Thủy Tiên (`2A202602171`)

> **Ghi chú về phân tách hai hướng phát triển trong Tuần 05:**  
> Trong tuần 05, nhóm thống nhất triển khai 2 hướng công cụ song song để thử nghiệm và so sánh đối chứng:
> - **Phần A (Nhánh chính):** Nghiên cứu, phát triển và đưa vào **thử nghiệm nội bộ** module Bộ ba mô hình AI Đồng thuận (Tri-Model Consensus Ensemble) & Thuật toán Weighted Boxes Fusion (WBF), tự động phát hiện vật thể bỏ sót và sai nhãn; hướng tới mục tiêu hỗ trợ cắt giảm tối thiểu 70% thời gian rà soát thủ công của Reviewer khi hoàn thiện. Phụ trách: **Trần Thị Thủy Tiên (Lead)**, **Hoàng Công Chứ**, **Đào Ngọc Hiếu**.
> - **Phần B (Nhánh song song):** Hoàn thiện khung luồng quy trình vận hành, chuẩn hóa bộ quy tắc nghiệp vụ, xây dựng giao diện hàng đợi kiểm duyệt (Reviewer Disposition Hub) và tích hợp SAM2. Phụ trách: **Đoàn Văn Thắng**, **Nguyễn Thanh Đức**.

---

# PHẦN A: BÁO CÁO NHÁNH TRI-MODEL AI CONSENSUS & WBF ENSEMBLE
*(Phụ trách: Trần Thị Thủy Tiên, Hoàng Công Chứ, Đào Ngọc Hiếu)*

## 1. Phân công nhiệm vụ cụ thể

| Thành viên | MSSV | Vai trò chính | Phân công cụ thể trong tuần 05 |
|---|---|---|---|
| **Trần Thị Thủy Tiên** | `2A202602171` | **Team Lead · AI & Architecture Lead** | • Định hướng bài toán, thiết kế kiến trúc đa mô hình (Tri-Model Ensemble) nhằm giảm thiểu điểm mù của model đơn lẻ `yolov8n`.<br>• Nghiên cứu và cài đặt thuật toán hợp nhất hộp bao **Weighted Boxes Fusion (WBF)** kết hợp cơ chế đồng thuận 2 cấp độ (Strict 3/3 & Majority 2/3).<br>• Thiết kế cơ chế đối chiếu tự động (Cross-check) phát hiện vật thể bỏ sót (`RULE_AI01`) và sai danh mục (`RULE_AI02`).<br>• Thiết kế tính năng **1-Click Auto-Fix** xuất file nhãn bù box tự động, hướng tới mục tiêu giảm tải công việc cho Reviewer. |
| **Hoàng Công Chứ** | `2A202602187` | **Core Engine & Integration Engineer** | • Nâng cấp QC Engine (`qc/engine.py`) và Reporter (`qc/reporter.py`) hỗ trợ 2 Rule AI mới trên các định dạng xuất kết quả (CLI, HTML, CSV).<br>• Nâng cấp giao diện Web Streamlit (`app.py`): tích hợp cụm điều khiển Tri-Model, visualizer trực quan hóa hộp bao AI nét đứt neon tím/cam kèm tỷ lệ đồng thuận, bảng dữ liệu WBF; **hiện đang tiến hành kiểm thử giao diện**.<br>• Xây dựng script tiện ích khởi chạy nhanh trên Windows ([run_qc_tool.bat](../run_qc_tool.bat), [run.bat](../run.bat)) để phục vụ việc test nội bộ thuận tiện hơn. |
| **Đào Ngọc Hiếu** | `2A202602081` | **AI Specialist & Benchmark Lead** | • Khảo sát và thiết lập cấu hình 3 pipeline mô hình: Model 1 (Base 640px), Model 2 (High-Res 960px cho camera 1080p), Model 3 (TTA Multi-Scale 800px).<br>• Xây dựng bộ kiểm thử tự động [test_ai_detector.py](../source-tool/QC_tool/tests/test_ai_detector.py), đã vượt qua 42/42 test cases trong môi trường kiểm thử của nhóm.<br>• Chạy thử nghiệm bước đầu trên ảnh mẫu camera giao thông 1080p để đo đạc sơ bộ tốc độ CPU và khả năng phát hiện vật thể bỏ sót, ghi nhận dữ liệu phục vụ quá trình kiểm thử tiếp theo. |

---

## 2. Các điểm phát triển & Cải tiến so với Tuần 04

So với Tuần 04 (mới chỉ dừng lại ở 10 rules hình học và thuộc tính cơ bản như out-of-bounds, zero-size, trùng box, polygon lỗi), Tuần 05 tập trung vào **nghiên cứu và thử nghiệm Trí tuệ nhân tạo (AI-assisted QC)**:

| Tiêu chí so sánh | Tuần 04 (Baseline) | Tuần 05 (Hướng tiếp cận AI Ensemble) | Mục tiêu & Kỳ vọng |
|---|---|---|---|
| **Khả năng soi lỗi bỏ sót (False Negatives)** | Chưa hỗ trợ hoặc chỉ dùng model đơn lẻ `yolov8n` yếu, dễ bỏ sót hoặc nhận diện sai. | **Tri-Model Ensemble (kết hợp 3 pipeline):**<br>• Model 1: Base Detector (640px)<br>• Model 2: High-Res Specialist (960px)<br>• Model 3: TTA Augmented (800px) | Giảm thiểu điểm mù, hướng tới bắt được cả xe nhỏ, xe khuất và người đi bộ ở làn xa. |
| **Chất lượng Bounding Box** | Box AI đơn lẻ dễ rung lắc, lệch mép vật thể. | **Weighted Boxes Fusion (WBF):** Lấy trung bình có trọng số tọa độ $[x_1, y_1, x_2, y_2]$ theo độ tin cậy. | Hộp bao mượt mà, bám sát mép vật thể hơn so với việc chỉ dùng 1 model. |
| **Tỷ lệ báo động giả (False Positives)** | Dễ gặp cảnh báo rác nếu chỉ dùng 1 model độ nhạy cao. | **Cơ chế Đồng thuận (Consensus Voting):** Chế độ Strict (cả 3 model cùng nhận diện) hoặc Majority (tối thiểu 2 model). | Giảm đáng kể báo động giả, nhãn cảnh báo tin cậy hơn. |
| **Quy tắc kiểm tra (Rules)** | 10 rules cơ bản (`RULE_B01`–`B04`, `RULE_P01`–`P03`, `RULE_A01`–`A03`). | **12 rules** (Bổ sung thử nghiệm `RULE_AI01` — Bỏ sót vật thể và `RULE_AI02` — Nghi vấn sai loại nhãn). | Mở rộng kiểm tra từ lỗi hình học/cú pháp sang lỗi ngữ nghĩa gán nhãn. |
| **Hỗ trợ công việc của Reviewer** | Giảm ~60% thời gian cho lỗi cú pháp cơ bản; vẫn phải soi thủ công từng xe sót. | Đang xây dựng luồng tự động gom cụm lỗi AI và xuất danh sách đối chiếu. | Kỳ vọng giảm >70% công việc rà soát thủ công khi hoàn thiện kiểm thử. |
| **Khả năng khắc phục lỗi (Actionability)** | Reviewer phải ghi chú lỗi, annotator tự mở lại CVAT vẽ lại từ đầu. | Thử nghiệm tính năng **1-Click Auto-Fix**: Xuất file nhãn tự động bù các box AI đồng thuận (YOLO txt format). | Giảm thời gian vẽ bù nhãn thủ công cho đội ngũ gán nhãn. |
| **Khởi chạy và Vận hành** | Gõ lệnh dài dòng trong terminal, dễ nhầm thư mục. | Bổ sung script khởi chạy nhanh [run_qc_tool.bat](../run_qc_tool.bat) / `run.bat` để các thành viên tiện mở và test. | Đang thử nghiệm tính tiện dụng và tương thích trên máy các thành viên. |
| **Kiểm thử tự động** | 33 test cases. | Bổ sung bộ test [test_ai_detector.py](../source-tool/QC_tool/tests/test_ai_detector.py) (42 test cases pass trong môi trường dev). | Đảm bảo tính toán thuật toán WBF, IoU đúng logic; tiếp tục test trên dữ liệu thực. |

---

## 3. Tiến độ công việc chi tiết trong tuần 05 (Nhánh chính)

> *Lưu ý: Các hạng mục mã nguồn và giao diện đã được triển khai nhưng **chưa thể khẳng định là đã hoàn thành 100% hay chạy trơn tru tuyệt đối**, hiện toàn bộ hệ thống đang trong giai đoạn kiểm thử nội bộ và tiếp tục được các thành viên trong nhóm trải nghiệm thực tế.*

| # | Hạng mục công việc | Người phụ trách | Trạng thái | Đánh giá hiện tại |
|---|---|---|---|---|
| 1 | Nghiên cứu & Thiết kế module Tri-Model AI Detector (`qc/ai_detector.py`) | Thủy Tiên | 🟡 Đang kiểm thử | Đã lập trình thuật toán WBF và logic gom cụm; đang kiểm thử tính chính xác. |
| 2 | Cài đặt cơ chế đồng thuận Strict (3/3) & Majority (2/3), bộ ánh xạ nhãn | Thủy Tiên | 🟡 Đang kiểm thử | Đã ánh xạ COCO ↔ BDD100K ↔ `class_0`; cần kiểm tra thêm các tập dữ liệu khác. |
| 3 | Tích hợp 2 Rule AI mới vào Core Engine (`qc/engine.py`, `qc/models.py`) | Công Chứ | 🟡 Đang kiểm thử | Đã nối luồng xuất báo cáo; đang đối soát lỗi trên các ca gán nhãn thực tế. |
| 4 | Nâng cấp Giao diện Web tương tác Streamlit (`source-tool/QC_tool/app.py`) | Công Chứ | 🟡 Đang kiểm thử | Đã code cụm AI Sidebar và visualizer; **đang kiểm thử thao tác, chưa nghiệm thu độ trơn tru**. |
| 5 | Xây dựng tính năng 1-Click Auto-Fix xuất file nhãn bù box AI | Thủy Tiên & Chứ | 🟡 Đang thử nghiệm | Đã tích hợp nút tải file `.txt`; cần thử nghiệm thực tế xem file bù nhãn chuẩn chưa. |
| 6 | Bổ sung cờ `--ai-check` cho CLI (`source-tool/QC_tool/main.py`) | Công Chứ | 🟡 Đang kiểm thử | Đã thêm cờ dòng lệnh; đang chạy thử nghiệm quét hàng loạt thư mục. |
| 7 | Viết script tiện ích khởi chạy nhanh trên Windows ([run_qc_tool.bat](../run_qc_tool.bat), [run.bat](../run.bat)) | Công Chứ | 🟡 Đang thử nghiệm | Đã tạo script mở nhanh; đang kiểm tra tính tương thích trên máy các thành viên. |
| 8 | Xây dựng bộ Unit Test mới [tests/test_ai_detector.py](../source-tool/QC_tool/tests/test_ai_detector.py) | Ngọc Hiếu | 🟡 Đã pass unit tests | 42/42 test cases pass trong dev; cần bổ sung thêm các ca biên (edge cases). |
| 9 | Thử nghiệm bước đầu trên ảnh camera giao thông thực tế 1080p | Ngọc Hiếu | 🟡 Đang thử nghiệm | Đã test trên ảnh mẫu; bắt đầu phát hiện được xe bỏ sót, cần test trên tập mẫu lớn hơn. |
| 10 | Biên soạn tài liệu kỹ thuật [README_AI_ENSEMBLE.md](../source-tool/QC_tool/README_AI_ENSEMBLE.md) | Thủy Tiên & Hiếu | 🟡 Đang hoàn thiện | Đã soạn tài liệu hướng dẫn cơ chế WBF; sẽ cập nhật thêm khi hoàn tất kiểm thử. |

---

## 4. Kết quả thử nghiệm bước đầu trên ảnh mẫu

*Lưu ý: Đây mới chỉ là kết quả thử nghiệm trên frame mẫu kiểm thử ban đầu của nhóm phát triển. Nhóm chưa đưa vào sử dụng chính thức và giao diện web hiện đang được các thành viên tiếp tục trải nghiệm, kiểm thử độ ổn định thực tế.*

* **Tình trạng gán nhãn ban đầu trên frame mẫu:** Annotator mới chỉ vẽ nhãn cho **3 xe taxi điện Xanh SM ở làn giữa**, chưa bao quát các phương tiện xung quanh.
* **Ghi nhận từ các Pipeline:**
  * Model 1 (Base 640px): Bắt được 11 đối tượng.
  * Model 2 (High-Res 960px): Bắt được 21 đối tượng (phát hiện thêm các xe ở làn xa).
  * Model 3 (TTA Augmented 800px): Bắt được 19 đối tượng (bắt các góc khuất và phương tiện nhỏ).
* **Kết quả khi áp dụng WBF và đồng thuận (Thử nghiệm ban đầu):**
  * **Chế độ Strict (cả 3 model cùng đồng thuận):** Bắt được 8–10 đối tượng nghi vấn bỏ sót (xe tải, xe con phía sau, xe máy) với độ tin cậy tương đối cao.
  * **Chế độ Majority (tối thiểu 2 model đồng thuận):** Bắt được khoảng 16 đối tượng trên toàn cảnh.
* **Đánh giá sơ bộ:** Tốc độ suy luận trên CPU đơn máy phát triển đạt khoảng ~40ms/ảnh. Tuy nhiên, tính ổn định của toàn bộ giao diện và độ mượt mà khi người dùng thao tác liên tục vẫn **cần được các thành viên trực tiếp trải nghiệm và kiểm thử kỹ hơn** trong thời gian tới.

---

# PHẦN B: BÁO CÁO NHÁNH QUY TRÌNH HỆ THỐNG & GIAO DIỆN HÀNG ĐỢI KIỂM DUYỆT
*(Phụ trách: Đoàn Văn Thắng, Nguyễn Thanh Đức)*

## 1. Tổng quan mục tiêu
- Hoàn thiện kế hoạch chi tiết và tài liệu hóa toàn bộ luồng quy trình vận hành của hệ thống.
- Xây dựng hoàn chỉnh khung giao diện người dùng và các phân khu chức năng phục vụ thao tác kiểm tra dữ liệu.
- Thiết lập hệ thống quy tắc nghiệp vụ và cơ chế rà soát tự động ban đầu.
- Tiến hành chạy thử nghiệm liên thông từ đầu vào đến đầu ra trên các tập dữ liệu mẫu để đánh giá tính khả thi và độ ổn định của hệ thống.

---

## 2. Phân công và kết quả công việc chi tiết

### 👤 Đoàn Văn Thắng
* **Xây dựng quy hoạch hệ thống và tài liệu luồng quy trình:**
  - Hoàn thành tài liệu phân tích luồng làm việc tổng thể từ khâu tiếp nhận dữ liệu đầu vào, xử lý tự động, kiểm duyệt thủ công đến khâu kết xuất báo cáo nghiệm thu.
  - Xây dựng kế hoạch triển khai từng giai đoạn và xác định các tiêu chí nghiệm thu cho từng phân hệ.
* **Hoàn thiện thiết kế và xây dựng giao diện người dùng:**
  - Triển khai xong toàn bộ giao diện làm việc trực quan cho người kiểm duyệt, bao gồm khu vực tải lên dữ liệu, màn hình trực quan hóa hình ảnh kèm thông tin đối soát, và bảng điều khiển trung tâm.
  - Thiết kế bảng hàng đợi thông minh giúp phân loại và sắp xếp thứ tự ưu tiên các trường hợp cần rà soát dựa trên mức độ cảnh báo.
  - Xây dựng khu vực xem xét chi tiết cho phép người dùng xác nhận, bác bỏ hoặc để lại ghi chú đối với từng cảnh báo nghi vấn.
  - Tích hợp màn hình quản lý, xem trước và chỉnh sửa bộ tiêu chuẩn/hướng dẫn kiểm tra chất lượng.
* **Phối hợp thử nghiệm và kiểm thử tích hợp:**
  - Thực hiện kiểm tra tính liên kết và độ phản hồi giữa các màn hình chức năng.
  - Thử nghiệm chức năng xuất báo cáo tổng hợp sau kiểm tra dưới nhiều định dạng khác nhau.

---

### 👤 Nguyễn Thanh Đức
* **Thiết lập bộ tiêu chuẩn và quy tắc kiểm tra dữ liệu:**
  - Xây dựng và hoàn thiện bộ tiêu chí đánh giá tự động đối với dữ liệu hình ảnh (kiểm tra tính hợp lệ về hình học, cấu trúc đối tượng, các lỗi trùng lặp và phân loại sai danh mục).
  - Chuẩn hóa các kịch bản kiểm tra đối với các định dạng dữ liệu khác nhau để đảm bảo tính tương thích khi nạp vào hệ thống.
* **Phát triển lõi xử lý và cơ chế đánh giá tự động:**
  - Xây dựng logic phân tích dữ liệu tự động, đối chiếu giữa dữ liệu thực tế và bộ quy tắc đã ban hành để tự động phát hiện các điểm bất thường.
  - Thiết lập cơ chế tích hợp với module hỗ trợ rà soát nâng cao nhằm tạo ra các đề xuất khách quan hỗ trợ người kiểm duyệt.
  - Xây dựng cơ chế trích xuất vị trí nghi ngờ lỗi và tính toán các chỉ số tương đồng giúp khoanh vùng vấn đề nhanh chóng.
* **Thử nghiệm trên dữ liệu mẫu và chuẩn bị môi trường chạy:**
  - Chuẩn bị các gói dữ liệu mẫu chuẩn (bao gồm nhiều tình huống dữ liệu từ đơn giản đến phức tạp) để đưa vào kiểm tra thực tế.
  - Thực hiện các đợt chạy thử nghiệm đo lường hiệu năng và độ ổn định của bộ kiểm tra tự động trên các tập dữ liệu mẫu.

---

## 3. Tóm tắt những gì đã đạt được (Tổng kết hiện trạng nhánh song song)

1. **Về mặt quy trình & Kế hoạch (Planning):** Đã thống nhất và hoàn tất toàn bộ tài liệu đặc tả luồng xử lý của hệ thống; xác định rõ vai trò của việc kiểm tra tự động là đưa ra cảnh báo và đề xuất hỗ trợ, quyền quyết định nghiệm thu cuối cùng thuộc về người kiểm duyệt.
2. **Về mặt giao diện người dùng (UI/UX):** Đã hoàn thành các phân hệ giao diện (tiếp nhận nạp dữ liệu, hiển thị hình ảnh đối sánh trực quan, danh sách hàng đợi phân cấp ưu tiên, bảng phê duyệt/từ chối của reviewer, màn hình quản lý tiêu chuẩn và xuất báo cáo).
3. **Về mặt xử lý nghiệp vụ (Core Logic):** Bộ quy tắc kiểm tra cấu trúc dữ liệu đã hoạt động ổn định và lọc được các lỗi sai cơ bản; module đánh giá tự động bước đầu tạo ra các gợi ý và chỉ số so sánh.
4. **Về mặt thử nghiệm thực tế (Testing & Experimentation):** Đã chạy kiểm thử thành công toàn bộ luồng quy trình trên tập dữ liệu mẫu; các gói dữ liệu mẫu bước đầu cho kết quả khả quan.

---

# PHẦN C: KẾ HOẠCH PHỐI HỢP & NHIỆM VỤ TUẦN 06

1. **Trực tiếp kiểm thử toàn diện giao diện Web & Quy trình QC:**
   - Các thành viên (Tiên, Chứ, Hiếu) trực tiếp dùng thử giao diện web Streamlit, kiểm tra độ mượt mà, tính tiện dụng của các nút bấm và tính đúng đắn của file nhãn bù tự động (Auto-Fix).
   - Rà soát các trường hợp lỗi giao diện, tối ưu hóa trải nghiệm người dùng (UX) và khắc phục các vấn đề phát sinh trong quá trình thử nghiệm.
2. **Họp đối chứng và hợp nhất hai nhánh công cụ:**
   - Tổ chức buổi demo nội bộ đánh giá ưu/nhược điểm giữa nhánh Tri-Model AI WBF của Tiên - Chứ - Hiếu và nhánh công cụ của Thắng - Đức.
   - Thống nhất giải pháp tối ưu để tích hợp trọn vẹn thành một sản phẩm QC Tool hoàn chỉnh của cả nhóm.
3. **Thử nghiệm trên tập dữ liệu gán nhãn thực tế quy mô lớn hơn:**
   - Chạy thử nghiệm trên nhiều khung hình và video giao thông khác nhau để đánh giá chính xác độ tin cậy và tỷ lệ cắt giảm thời gian thực tế của Reviewer.
4. **Chuẩn bị tài liệu nghiệm thu đề tài N2-04A:**
   - Tổng hợp các kết quả thực nghiệm, hoàn thiện slide báo cáo và video demo.
