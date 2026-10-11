# HƯỚNG DẪN KỸ THUẬT & QUY TRÌNH LÀM VIỆC NHÓM

> **Tài liệu chuẩn hóa quy trình Git, môi trường lập trình và kiểm thử cho dự án BDD-QC Tool.**

---

## 1. Chuẩn bị môi trường (Setup Environment)

Tất cả thành viên cần cài đặt môi trường ảo Python 3.9+ để đảm bảo tính đồng nhất:

```bash
# 1. Di chuyển vào thư mục dự án
cd source-tool/bdd-qc-tool

# 2. Khởi tạo môi trường ảo Python
python -m venv venv

# 3. Kích hoạt môi trường ảo:
# Trên Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Trên Linux/macOS:
source venv/bin/activate

# 4. Cài đặt các thư viện phụ thuộc
pip install -r requirements.txt
```

---

## 2. Quy trình làm việc trên Git (Tránh xung đột Merge Conflict)

Để 5 thành viên làm việc song song mượt mà, nhóm áp dụng **Feature Branch Workflow**:

```
main (nhánh chính, chỉ merge khi đã review và chạy pass)
 ├── feature/parser-models       (Thành viên 1: Văn Thắng)
 ├── feature/bbox-rules          (Thành viên 2: Thanh Đức)
 ├── feature/polygon-rules       (Thành viên 3: Công Chứ)
 ├── feature/attribute-rules     (Thành viên 4: Thủy Tiên)
 └── feature/cli-reporter        (Thành viên 5: Ngọc Hiếu)
```

### Các bước đẩy code của từng thành viên:
1. **Lấy code mới nhất về:**
   ```bash
   git checkout main
   git pull origin main
   ```
2. **Tạo nhánh tính năng của riêng mình:**
   ```bash
   git checkout -b feature/bbox-rules  # thay bằng tên nhánh của bạn
   ```
3. **Commit code với thông điệp rõ ràng:**
   ```bash
   git add .
   git commit -m "feat(bbox): implement rule B01 out of bounds and B02 zero size"
   ```
4. **Push nhánh lên GitHub và tạo Pull Request (PR):**
   ```bash
   git push origin feature/bbox-rules
   ```
5. **Review:** Lead Đào Ngọc Hiếu hoặc 1 thành viên khác duyệt PR trước khi merge vào `main`.

---

## 3. Quy chuẩn viết code (Coding Standards)

1. **Kiểu dữ liệu (Type Hinting):**
   Mọi hàm bắt buộc khai báo type rõ ràng:
   ```python
   def check_something(frame: FrameData) -> List[QCError]:
       ...
   ```
2. **Không ném ngoại lệ (Exception) bừa bãi trong Rule:**
   Khi phát hiện lỗi dữ liệu, **không dùng `raise ValueError()`** làm chết chương trình, mà hãy tạo object `QCError` và append vào danh sách trả về.
3. **Mã lỗi chuẩn hóa:**
   - BBox rules: `RULE_B01`, `RULE_B02`, `RULE_B03`, `RULE_B04`
   - Polygon rules: `RULE_P01`, `RULE_P02`, `RULE_P03`
   - Attribute rules: `RULE_A01`, `RULE_A02`, `RULE_A03`
4. **Severity:** Chỉ dùng đúng 2 mức:
   - `"ERROR"`: Sai nghiêm trọng, không thể dùng để train model hoặc nộp bài.
   - `"WARNING"`: Nghi vấn, cần người kiểm tra lại.

---

## 4. Hướng dẫn tự viết Unit Test kiểm tra module của mình

Mỗi bạn sau khi viết xong rule của mình có thể tạo một file test nhanh trong thư mục `tests/` để xác nhận:

Ví dụ test module BBox:
```python
# tests/test_bbox.py
from qc.models import FrameData, LabeledObject, BBox2D
from qc.rules.bbox_rules import check_bbox_rules

def test_out_of_bounds():
    # Giả lập 1 box vượt khung hình 1280x720
    bad_obj = LabeledObject(
        id="test_01",
        category="car",
        box2d=BBox2D(x1=-10, y1=20, x2=1300, y2=500)
    )
    frame = FrameData(name="test_frame.jpg", width=1280, height=720, objects=[bad_obj])
    
    errors = check_bbox_rules(frame)
    assert len(errors) == 1
    assert errors[0].rule_id == "RULE_B01"
    print("✅ Test B01 passed!")

if __name__ == "__main__":
    test_out_of_bounds()
```

---

## 5. Kế hoạch nghiệm thu & Demo trước Mentor

| Hạng mục | Nội dung chuẩn bị | Người phụ trách |
|---|---|---|
| **Demo trực tiếp (Live CLI)** | Chạy lệnh quét file test, hiển thị bảng lỗi màu sinh động trên Terminal và mở file HTML report trên trình duyệt. | Đào Ngọc Hiếu |
| **Giải thích Rule BBox & Data Model** | Thuyết trình cấu trúc dữ liệu và cách bắt các lỗi box âm, box nhỏ, tràn viền. | Đoàn Văn Thắng & Nguyễn Thanh Đức |
| **Giải thích Rule Polygon & Attributes** | Thuyết trình cách dùng Shapely bắt lỗi polygon tự cắt và thuật toán tính IoU bắt box trùng. | Hoàng Công Chứ & Trần Thị Thủy Tiên |
| **Báo cáo chỉ số cải tiến** | Trình bày biểu đồ so sánh: Thời gian review giảm $60\%$, tỷ lệ bắt lỗi đạt $>90\%$. | Cả nhóm |
