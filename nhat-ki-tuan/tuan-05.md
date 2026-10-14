# Nhật ký tuần 05 · 12/10 – 18/10/2026

**Lead tuần này:** Trần Thị Thủy Tiên (`2A202602171`)  
**Nhiệm vụ trọng tâm:** Phát triển và đưa vào **thử nghiệm nội bộ** Bộ ba mô hình (Tri-Model Consensus Ensemble) & Thuật toán Weighted Boxes Fusion (WBF), tự động phát hiện vật thể bỏ sót và sai nhãn; hướng tới mục tiêu hỗ trợ cắt giảm tối thiểu 70% thời gian rà soát thủ công của Reviewer khi hoàn thiện.  
**Mã kho lưu trữ:** [P-037](https://github.com/AI20K-Build-Phase-Cohort-4A/P-037) · **Nhóm:** `t-037`

> **Ghi chú phân tách nhân sự Tuần 05:**  
> Thành viên Đoàn Văn Thắng và Nguyễn Thanh Đức quyết định xây dựng một hướng công cụ QC song song để thử nghiệm độc lập. Phần báo cáo chi tiết của hai thành viên này sẽ được cập nhật riêng sau. Báo cáo tuần 05 này tập trung vào các nội dung phát triển, nâng cấp so với Tuần 04 do nhánh chính thực hiện, gồm **Trần Thị Thủy Tiên (Lead)**, **Đào Ngọc Hiếu** và **Hoàng Công Chứ**.

---

## 1. Thành viên và phân công nhiệm vụ

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

## 3. Tiến độ công việc chi tiết trong tuần 05

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

## 5. Kế hoạch tuần kế tiếp (Tuần 06)

1. **Trực tiếp kiểm thử toàn diện giao diện Web & Quy trình QC:**
   - Các thành viên (Tiên, Chứ, Hiếu) trực tiếp dùng thử giao diện web Streamlit, kiểm tra độ mượt mà, tính tiện dụng của các nút bấm và tính đúng đắn của file nhãn bù tự động (Auto-Fix).
   - Rà soát các trường hợp lỗi giao diện, tối ưu hóa trải nghiệm người dùng (UX) và khắc phục các vấn đề phát sinh trong quá trình thử nghiệm.
2. **Họp đối chứng và so sánh với nhánh công cụ song song của Thắng & Đức:**
   - Tổ chức buổi demo nội bộ đánh giá ưu/nhược điểm giữa nhánh Tri-Model AI WBF và nhánh công cụ của Thắng - Đức.
   - Thống nhất giải pháp tối ưu để hoàn thiện phiên bản công cụ chung của nhóm.
3. **Thử nghiệm trên tập dữ liệu gán nhãn thực tế quy mô lớn hơn:**
   - Chạy thử nghiệm trên nhiều khung hình và video giao thông khác nhau để đánh giá chính xác độ tin cậy và tỷ lệ cắt giảm thời gian thực tế của Reviewer.

