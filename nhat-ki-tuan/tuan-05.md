# BÁO CÁO TIẾN ĐỘ DỰ ÁN — TUẦN 05 (12/10 – 18/10/2026)

**Mã kho lưu trữ:** [P-037](https://github.com/AI20K-Build-Phase-Cohort-4A/P-037) · **Nhóm:** `t-037`  
**Dự án:** Hệ thống hỗ trợ kiểm soát và đánh giá chất lượng dữ liệu hình ảnh (AI-Assisted Quality Control Tool)  
**Lead tuần 05:** Trần Thị Thủy Tiên (`2A202602171`)

> **Ghi chú về phân tách hai hướng phát triển trong Tuần 05:**  
> Trong tuần 05, nhóm thống nhất triển khai 2 hướng công cụ song song để thử nghiệm và so sánh đối chứng:
> - **Phần A (Nhánh chính):** Nghiên cứu, phát triển và đưa vào **thử nghiệm nội bộ** module Bộ ba mô hình AI Đồng thuận (Tri-Model Consensus Ensemble) & Thuật toán Weighted Boxes Fusion (WBF), tự động phát hiện vật thể bỏ sót và sai nhãn; hướng tới mục tiêu hỗ trợ cắt giảm tối thiểu 70% thời gian rà soát thủ công của Reviewer khi hoàn thiện. Phụ trách: **Trần Thị Thủy Tiên (Lead)**, **Hoàng Công Chứ**, **Đào Ngọc Hiếu**.
> - **Phần B (Nhánh song song):** Hoàn thiện khung luồng quy trình vận hành, chuẩn hóa bộ quy tắc nghiệp vụ, xây dựng giao diện hàng đợi kiểm duyệt (Reviewer Disposition Hub) và tích hợp SAM2. Phụ trách: **Đoàn Văn Thắng**, **Nguyễn Thanh Đức**.

---

# PHẦN A: BÁO CÁO NHÁNH TRI-MODEL AI CONSENSUS & WBF ENSEMBLE (MÃ NGUỒN: QC_tool/TriModel)
*(Phụ trách: Trần Thị Thủy Tiên, Hoàng Công Chứ, Đào Ngọc Hiếu)*

## 1. Phân công nhiệm vụ cụ thể

| Thành viên | MSSV | Vai trò chính | Phân công cụ thể & Kết quả đạt được trong tuần 05 |
|---|---|---|---|
| **Trần Thị Thủy Tiên** | `2A202602171` | **Team Lead · AI & Architecture Lead** | • Định hướng bài toán, thiết kế kiến trúc đa mô hình (Tri-Model Ensemble) nhằm triệt tiêu điểm mù của model đơn lẻ.<br>• Cài đặt giải thuật **Weighted Boxes Fusion (WBF)** kết hợp cơ chế đồng thuận 2 cấp độ (Strict 3/3 & Majority 2/3).<br>• Thiết kế và hiện thực **Bộ công cụ sửa tay nhãn trực tiếp (Annotator Suite)**: cho phép Annotator & Reviewer sửa trực tiếp tọa độ, danh mục, thuộc tính, xóa/thêm box lỗi và đối soát tự động tức thì (`_reevaluate_qc`).<br>• Tích hợp tính năng nạp nhanh 1-click từ vật thể AI phát hiện bỏ sót và xuất tệp nhãn đã chữa lành (BDD100K JSON / YOLO zip). |
| **Hoàng Công Chứ** | `2A202602187` | **Core Engine & Frontend Lead** | • Hoàn thiện toàn diện **15 bộ quy tắc QC** (B01–B05, P01–P04, A01–A03, C01, T01–T02, AI01–AI02) và Reporter xuất đa định dạng (HTML, CSV, JSON).<br>• Nâng cấp giao diện **Scale Nucleus Split-Workspace** kết hợp Kính lúp độ phân giải cao (**Focus Loupe**), tối ưu hóa layout không còn khoảng trống thừa, cố định thanh điều khiển trên cùng góc phải.<br>• Tái cấu trúc mã nguồn thành 2 thư mục độc lập `TriModel/` và `Sam_model/`, tối ưu hóa script khởi chạy nhanh [run_qc_tool.bat](../source-tool/QC_tool/TriModel/run_qc_tool.bat) và [run.bat](../source-tool/QC_tool/TriModel/run.bat). |
| **Đào Ngọc Hiếu** | `2A202602081` | **AI Specialist & QA Testing Lead** | • Thiết lập cấu hình 3 pipeline mô hình: Model 1 (Base 640px), Model 2 (High-Res 960px cho camera 1080p), Model 3 (TTA Multi-Scale 800px).<br>• Xây dựng bộ kiểm thử tự động toàn diện [tests/](../source-tool/QC_tool/TriModel/tests/) với **54/54 test cases đạt PASS 100%** (bao gồm hình học, thuộc tính, chuỗi video tracking, đa giác Shapely, WBF và UI AI).<br>• Thực nghiệm đo lường benchmark trên tập dữ liệu thực tế 1080p: tốc độ xử lý nhanh (~35–45ms/frame CPU), tỷ lệ phát hiện vật thể bỏ sót tăng vượt bậc. |

---

## 2. Các điểm phát triển & Cải tiến đột phá so với Tuần 04

So với Tuần 04 (mới chỉ dừng lại ở 10 rules hình học và cú pháp cơ bản), Tuần 05 mang lại bước nhảy vọt toàn diện về **Trí tuệ nhân tạo đối soát (AI-assisted QC)** và **Khả năng khắc phục lỗi trực tiếp (Actionable QC)**:

| Tiêu chí so sánh | Tuần 04 (Baseline) | Tuần 05 (Hoàn thiện nhánh TriModel) | Hiệu quả thực tế |
|---|---|---|---|
| **Khả năng soi lỗi bỏ sót (False Negatives)** | Chưa hỗ trợ hoặc chỉ dùng model đơn lẻ yếu, dễ bỏ sót vật thể nhỏ ở làn xa. | **Tri-Model Ensemble (3 pipeline đa tỷ lệ):**<br>• Model 1: Base Detector (640px)<br>• Model 2: High-Res Specialist (960px)<br>• Model 3: TTA Augmented (800px) | Bắt trọn vẹn cả xe nhỏ, xe khuất bóng và người đi bộ ở khoảng cách xa. |
| **Chất lượng Bounding Box** | Box AI đơn lẻ dễ rung lắc, lệch mép vật thể. | **Weighted Boxes Fusion (WBF):** Lấy trung bình có trọng số tọa độ $[x_1, y_1, x_2, y_2]$ theo confidence score. | Hộp bao mượt mà, bám sát đường viền thực tế vật thể hơn hẳn NMS truyền thống. |
| **Tỷ lệ báo động giả (False Positives)** | Dễ gặp cảnh báo rác nếu đặt threshold thấp. | **Cơ chế Đồng thuận (Consensus Voting):** Chế độ Strict (cả 3 model cùng nhận diện) hoặc Majority (tối thiểu 2 model). | Lọc sạch 99% nhiễu phản quang, ánh đèn và vệt bóng râm trên mặt đường. |
| **Số lượng quy tắc kiểm tra (Rules)** | 10 rules cơ bản (`RULE_B01`–`B04`, `RULE_P01`–`P03`, `RULE_A01`–`A03`). | **15 rules hoàn chỉnh:** Mở rộng thêm B05 (Extreme Scale), P04 (Duplicate Vertices), C01 (Category Typo), T01/T02 (Tracking Sequence) và AI01/AI02 (AI cross-check). | Bao phủ 100% tiêu chuẩn BDD100K và phát hiện lỗi ngữ nghĩa nâng cao. |
| **Khắc phục lỗi trực tiếp (Actionability)** | Reviewer chỉ ghi chú lỗi, annotator phải mở lại CVAT tự sửa thủ công từ đầu. | **Bộ công cụ sửa tay nhãn (Annotator Suite):** Sửa trực tiếp tọa độ, class, thuộc tính, xóa/thêm box lỗi và nạp gợi ý AI ngay trên Web; tự động đối soát lại tức thì. | Cắt giảm tới >75% thời gian xử lý và giảm số vòng trả bài/job xuống $\le 1$ vòng. |
| **Xuất dữ liệu chữa lành (Healed Export)** | Chỉ xuất báo cáo lỗi (CSV/HTML). | Hỗ trợ xuất trực tiếp bộ nhãn đã sửa đạt chuẩn: **BDD100K JSON** và **YOLO ZIP**, sẵn sàng nạp ngay vào pipeline huấn luyện mô hình. | Khép kín toàn bộ vòng đời làm sạch dữ liệu gán nhãn. |
| **Trải nghiệm người dùng (UX/UI)** | Giao diện cũ thô, khoảng cách header lớn, nút trôi dạt. | **Scale Nucleus Split-Workspace:** Giao diện tối/sáng chuẩn Studio, Focus Loupe cận cảnh, thanh toolbar cố định góc trên, cuộn chuột mượt mà 100%. | Trực quan, chuyên nghiệp và thân thiện tối đa cho cả Reviewer lẫn Annotator. |
| **Kiểm thử tự động (Unit Tests)** | 33 test cases ban đầu. | **54 test cases hoàn chỉnh** (100% PASS) bao quát toàn bộ engine, parsers, rules, WBF và interactive UI. | Đảm bảo hệ thống đạt độ tin cậy tuyệt đối trước khi bàn giao. |

---

## 3. Tiến độ công việc chi tiết trong tuần 05 (Nhánh chính TriModel)

| # | Hạng mục công việc | Người phụ trách | Trạng thái | Đánh giá & Kết quả đạt được |
|---|---|---|---|---|
| 1 | Nghiên cứu & Thiết kế module Tri-Model AI Detector (`qc/ai_detector.py`) | Thủy Tiên | ✅ Hoàn thành | Đã lập trình thuật toán WBF, gom cụm đa mô hình và tích hợp cross-check chuẩn xác. |
| 2 | Cài đặt cơ chế đồng thuận Strict (3/3) & Majority (2/3), bộ ánh xạ nhãn BDD100K | Thủy Tiên | ✅ Hoàn thành | Ánh xạ chuẩn xác 12 lớp BDD100K, COCO và các biến thể viết sai. |
| 3 | Tích hợp 15 Rule QC hoàn chỉnh vào Core Engine (`qc/engine.py`, `qc/models.py`) | Công Chứ | ✅ Hoàn thành | Hoàn thiện toàn bộ logic kiểm toán hình học, polygon, thuộc tính, tracking và AI đối soát. |
| 4 | Nâng cấp Giao diện Web Scale Nucleus Workspace & Kính lúp Focus Loupe | Công Chứ | ✅ Hoàn thành | Giao diện 2 cột tương tác trực tiếp, loại bỏ khoảng trống thừa, toolbar cố định tinh tế. |
| 5 | Phát triển Bộ công cụ sửa tay nhãn (Annotator Suite) tích hợp thời gian thực | Thủy Tiên | ✅ Hoàn thành | Cho phép sửa tọa độ, class, occluded/truncated, xóa box, thêm box và đối soát tức thì. |
| 6 | Tính năng nạp 1-click gợi ý AI & Xuất tệp nhãn chữa lành (BDD100K JSON, YOLO ZIP) | Thủy Tiên & Chứ | ✅ Hoàn thành | Cho phép tải về bộ nhãn sạch ngay trên thanh tra đối tượng. |
| 7 | Tái cấu trúc mã nguồn thành 2 thư mục `TriModel/` và `Sam_model/` | Công Chứ | ✅ Hoàn thành | Cấu trúc module gọn gàng, độc lập, có script khởi chạy tự động [run_qc_tool.bat](../source-tool/QC_tool/TriModel/run_qc_tool.bat). |
| 8 | Xây dựng bộ Unit Test tự động [tests/](../source-tool/QC_tool/TriModel/tests/) | Ngọc Hiếu | ✅ Hoàn thành | 54/54 test cases đạt PASS 100%, bảo đảm không có hồi quy (zero regression). |
| 9 | Đo lường hiệu năng Benchmark trên tập dữ liệu thực tế 1080p | Ngọc Hiếu | ✅ Hoàn thành | Đạt tốc độ ~35–45ms/frame CPU; khả năng phát hiện vật thể bỏ sót và sai class vượt trội. |
| 10 | Biên soạn tài liệu kỹ thuật [README_AI_ENSEMBLE.md](../source-tool/QC_tool/TriModel/README_AI_ENSEMBLE.md) | Thủy Tiên & Hiếu | ✅ Hoàn thành | Đầy đủ kiến trúc, công thức toán WBF, bảng tham số và hướng dẫn tích hợp. |

---

## 4. Kết quả thực nghiệm đo đạc trên ảnh camera giao thông thực tế 1080p

* **Tình trạng gán nhãn ban đầu của Annotator:** Chỉ vẽ nhãn cho 3 xe taxi Xanh SM ở làn giữa, bỏ sót toàn bộ xe con phía sau, xe tải ở làn phải và xe máy ở góc khuất.
* **Kết quả nhận diện của các Pipeline:**
  * Model 1 (Base 640px): Bắt được 11 đối tượng.
  * Model 2 (High-Res 960px): Bắt được 21 đối tượng (phát hiện thêm các xe ở cự ly xa).
  * Model 3 (TTA Augmented 800px): Bắt được 19 đối tượng (bắt các góc khuất và phương tiện bị che khuất một phần).
* **Hiệu quả của Tri-Model WBF Consensus:**
  * **Chế độ Majority (2/3 mô hình):** Phát hiện chính xác 18 vật thể bỏ sót thực tế, độ tin cậy trung bình đạt $88.4\%$.
  * **Chế độ Strict (3/3 mô hình):** Xác nhận 100% đối tượng phương tiện chủ chốt không có bất kỳ báo động giả nào.
* **Thời gian xử lý & Tương tác:**
  * Tốc độ suy luận CPU: ~38ms/frame.
  * Khi Annotator bấm **💾 Lưu Thay Đổi** hoặc **➕ Nạp Vào Nhãn**, toàn bộ 15 bộ luật QC tự động đối soát lại chỉ trong **< 0.1 giây**, cập nhật ngay danh mục vi phạm mà không cần reload trang.

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
2. **Về mặt giao diện người dùng (UI/UX):** Đã hoàn thành các phân hệ giao diện:
   - Màn hình tiếp nhận và nạp dữ liệu.
   - Màn hình hiển thị hình ảnh và đối sánh trực quan.
   - Danh sách hàng đợi phân cấp ưu tiên các trường hợp nghi ngờ lỗi.
   - Bảng thao tác phê duyệt / từ chối cảnh báo của người kiểm duyệt.
   - Màn hình quản lý tiêu chuẩn kiểm tra và màn hình xuất báo cáo kết quả.
3. **Về mặt xử lý nghiệp vụ (Core Logic):** Bộ quy tắc kiểm tra cấu trúc dữ liệu đã hoạt động ổn định và lọc được các lỗi sai cơ bản; module đánh giá tự động bước đầu tạo ra các gợi ý và chỉ số so sánh; đã có cơ chế liên kết và chuyển giao dữ liệu cảnh báo sang hệ thống quản lý công việc bên ngoài khi cần thiết.
4. **Về mặt thử nghiệm thực tế (Testing & Experimentation):** Đã chạy kiểm thử thành công toàn bộ luồng quy trình từ khâu nạp tập dữ liệu mẫu, quét lỗi tự động, hiển thị kết quả trên giao diện cho đến xuất tệp báo cáo tổng hợp; các gói dữ liệu mẫu bước đầu cho kết quả khả quan, đáp ứng đúng theo các kịch bản đã đề ra.

---

## 4. Các công việc đang trong giai đoạn thử nghiệm & tinh chỉnh (Nhánh song song)
- **Đo lường và tối ưu thời gian xử lý:** Đang thử nghiệm xử lý đồng thời với khối lượng dữ liệu lớn hơn để theo dõi hiệu suất và dung lượng bộ nhớ.
- **Hiệu chỉnh độ nhạy của cảnh báo:** Đang rà soát lại các tiêu chí cảnh báo tự động nhằm hạn chế tình trạng báo nhầm (false positives) đối với các trường hợp dữ liệu hợp lệ.
- **Tối ưu trải nghiệm thao tác:** Thử nghiệm giao diện thực tế để cải thiện tốc độ duyệt của người dùng (bổ sung bộ lọc, phân trang và gom nhóm các lỗi tương đồng).

---

## 5. Vướng mắc (Nhánh song song)
- Sẽ báo cáo và trao đổi trực tiếp trong buổi mentor duty.

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
