# Nhật ký tuần 04 — 05/10 – 11/10/2026

**Lead tuần này:** Trần Thị Thủy Tiên (`2A202602171`)
**Dự án / Task:** BDD-QC Tool (N2-04A) — công cụ QC nhãn Bounding Box và Segmentation 2D cho BDD100K.

> Báo cáo tiến độ dưới đây được đối chiếu với nội dung hiện có trong `source-tool/`. Tài liệu README mô tả kiến trúc/kế hoạch mục tiêu; trạng thái hoàn thành chỉ ghi nhận theo các file mã nguồn và dữ liệu thực tế trong thư mục.

## Thành viên và phân công

| Thành viên | MSSV | Vai trò tuần này | Phân công theo `source-tool/` |
|---|---|---|---|
| **Trần Thị Thủy Tiên** | `2A202602171` | **Lead tuần 4 · Consistency & Attribute Specialist** | Điều phối tiến độ tuần; phụ trách `qc/rules/attribute_rules.py` (RULE_A01–A03) theo bảng phân công dự án |
| **Đào Ngọc Hiếu** | `2A202602081` | **Team Lead kỹ thuật · Core Integration** | Phụ trách `main.py`, `qc/reporter.py` và benchmark theo README dự án |
| **Đoàn Văn Thắng** | `2A202602327` | **Data Engineer** | Phụ trách `qc/models.py`, `qc/parser.py`; hiện thực chuyển đổi dữ liệu BDD100K/CVAT sang cấu trúc chuẩn |
| **Nguyễn Thanh Đức** | `2A202602279` | **BBox QC Specialist** | Phụ trách `qc/rules/bbox_rules.py` (RULE_B01–B04) |
| **Hoàng Công Chứ** | `2A202602187` | **Segmentation QC Specialist** | Phụ trách `qc/rules/polygon_rules.py` (RULE_P01–P03) |

## Công việc và tiến độ đối chiếu mã nguồn

| # | Hạng mục | Người phụ trách | Trạng thái theo `source-tool/` | Ghi nhận |
|---|---|---|---|---|
| 1 | Tài liệu tổng quan, danh sách 10 rule và kiến trúc dự kiến | Cả nhóm | ✅ Có tài liệu | Có trong `README.md`; đây là đặc tả/kế hoạch, không đồng nghĩa các rule đã được hiện thực |
| 2 | Quy trình kỹ thuật, hướng dẫn Git và hướng dẫn viết unit test | Cả nhóm | ✅ Có tài liệu | Có trong `HUONG-DAN-KY-THUAT.md`; thư mục mã nguồn hiện chưa có các file test được hướng dẫn |
| 3 | Khai báo thư viện phụ thuộc | Core Integration | ✅ Có khai báo | `requirements.txt` liệt kê `shapely`, `rich`, `tabulate`, `pytest`; báo cáo này không xác nhận đã cài hoặc chạy chúng |
| 4 | Cấu trúc dữ liệu `QCError`, `BBox2D`, `Polygon2D`, `LabeledObject`, `FrameData` | `2A202602327` (Văn Thắng) | ✅ Có mã nguồn | Đã có `qc/models.py` với 5 dataclass |
| 5 | Dữ liệu mẫu có lỗi | `2A202602327` (Văn Thắng) | ✅ Có file mẫu | `data_sample/sample_with_errors.json` có 1 frame và 9 object, minh họa các trường hợp như box vượt biên/zero-size, object trùng, thiếu attribute, traffic light sai màu và polygon tự cắt |
| 6 | Parser BDD100K/CVAT (`qc/parser.py`) | `2A202602327` (Văn Thắng) | ⬜ Chưa có file trong repo | Chưa thể xác nhận đọc và chuyển đổi JSON đầu-cuối |
| 7 | BBox rules RULE_B01–B04 | `2A202602279` (Thanh Đức) | ⬜ Chưa có file trong repo | Chưa thể xác nhận rule hoặc unit test hoạt động |
| 8 | Polygon rules RULE_P01–P03 | `2A202602187` (Công Chứ) | ⬜ Chưa có file trong repo | Chưa thể xác nhận kiểm tra polygon bằng Shapely |
| 9 | Attribute rules RULE_A01–A03 | `2A202602171` (Thủy Tiên) | ⬜ Chưa có file trong repo | Chưa thể xác nhận kiểm tra trùng lặp/attribute |
| 10 | CLI, pipeline và reporter (HTML/CSV/terminal) | `2A202602081` (Ngọc Hiếu) | ⬜ Chưa có file trong repo | `main.py` và `qc/reporter.py` chưa có trong thư mục hiện tại |
| 11 | Benchmark, Precision/Recall và so sánh thời gian review | `2A202602081` (Ngọc Hiếu), cả nhóm hỗ trợ | ⬜ Chưa có kết quả trong repo | README mô tả benchmark dự kiến 50 ảnh/30 lỗi; chưa có bộ benchmark hay kết quả đo để xác nhận |

Mức hoàn thành: ✅ có file mã nguồn/tài liệu tương ứng trong repo · 🔄 đang triển khai (cần cập nhật bằng bằng chứng cụ thể) · ⬜ chưa có hiện vật/kết quả trong repo · ⛔ bị chặn (ghi lý do).

## Tổng kết

- Hiện vật mã nguồn Python trong `source-tool/`: **1 file triển khai chính là `qc/models.py`**; các file còn lại hiện có là `__init__.py`.
- Đã có: tài liệu dự án, hướng dẫn kỹ thuật, danh sách phụ thuộc, cấu trúc dataclass và một file JSON mẫu có lỗi.
- Chưa có trong repo: parser, các module rule BBox/Polygon/Attribute, CLI, reporter và unit test tương ứng.
- Tích hợp end-to-end: **chưa xác nhận được** vì chưa có parser, rule modules và `main.py`.
- Benchmark và các chỉ số Precision/Recall/thời gian: **chưa có kết quả lưu trong repo**; các chỉ số mục tiêu trong README là tiêu chí dự kiến, không phải kết quả đã đo.

## Vướng mắc

| Mã / Vấn đề | Chi tiết | Hướng xử lý / Trạng thái |
|---|---|---|
| **P-001 — Thiếu các module triển khai chính** | Thư mục hiện tại chưa có `qc/parser.py`, các file `qc/rules/*_rules.py`, `main.py`, `qc/reporter.py` và thư mục test; do đó chưa thể chạy pipeline như hướng dẫn trong README | ⬜ Cần hoàn thiện các file theo bảng phân công, sau đó chạy unit test và kiểm thử end-to-end |
| **P-002 — Chưa có benchmark và số liệu nghiệm thu** | Chưa thấy bộ 50 frame/30 lỗi, kết quả Precision/Recall, thời gian chạy hoặc số liệu so sánh manual/tool trong `source-tool/` | ⬜ Cần tạo dữ liệu benchmark, lưu cách đo và kết quả để có thể kiểm chứng |
| **P-003 — Thiếu dữ liệu mẫu hợp lệ và kiểm thử parser** | Repo hiện có `sample_with_errors.json`; chưa thấy `sample_valid.json` hoặc test kiểm tra parse dữ liệu hợp lệ/sai định dạng | ⬜ Bổ sung mẫu sạch và các ca kiểm thử parser |

## Kế hoạch tuần kế tiếp

- **Đoàn Văn Thắng:** hoàn thiện parser đọc JSON và bổ sung `sample_valid.json`, kiểm thử dữ liệu hợp lệ và lỗi.
- **Nguyễn Thanh Đức:** hiện thực RULE_B01–B04 và unit test theo tiêu chí trong tài liệu phân công.
- **Hoàng Công Chứ:** hiện thực RULE_P01–P03, gồm xử lý polygon không hợp lệ và kiểm thử.
- **Trần Thị Thủy Tiên:** điều phối tiến độ tuần; hiện thực RULE_A01–A03 và kiểm thử các trường hợp attribute/đối tượng trùng.
- **Đào Ngọc Hiếu:** hiện thực CLI và reporter sau khi parser/rules sẵn sàng; tổ chức benchmark và ghi lại số liệu đo thực tế.
- **Cả nhóm:** tích hợp các module, chạy test, cập nhật trạng thái theo hiện vật đã đưa vào `source-tool/`; chỉ chốt các chỉ số nghiệm thu sau khi đo được.
