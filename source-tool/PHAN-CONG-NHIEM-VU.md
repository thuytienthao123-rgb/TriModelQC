# BẢNG PHÂN CÔNG NHIỆM VỤ DỰ ÁN BDD-QC TOOL (N2-04A)

> **Mỗi thành viên đọc kỹ phần nhiệm vụ của mình, làm đúng định dạng input/output và tự chạy unit test trước khi tạo Pull Request.**

---

## 👤 THÀNH VIÊN 1: ĐOÀN VĂN THẮNG (`2A202602327`)
**Vai trò:** Data Engineer (Data Ingestion & Models)  
**File phụ trách:** [`qc/models.py`](qc/models.py) và [`qc/parser.py`](qc/parser.py)

### 1. Mục tiêu
Đọc file JSON nhãn của BDD100K (hoặc file export tương thích), chuyển hóa thành cấu trúc dữ liệu chuẩn (`dataclass`) để các thành viên viết Rule có dữ liệu sạch để làm việc.

### 2. Nhiệm vụ cụ thể
1. **Hoàn thiện `qc/models.py`:**
   - Định nghĩa `QCError`: Lưu thông tin 1 lỗi phát hiện (`frame_name`, `object_id`, `category`, `rule_id`, `severity`, `message`).
   - Định nghĩa `BBox2D`: Lưu toạ độ `x1`, `y1`, `x2`, `y2`.
   - Định nghĩa `Polygon2D`: Lưu danh sách các đỉnh `vertices: List[Tuple[float, float]]`.
   - Định nghĩa `LabeledObject`: Lưu thông tin 1 đối tượng (`id`, `category`, `box2d`, `poly2d`, `attributes`).
   - Định nghĩa `FrameData`: Lưu 1 frame gồm `name`, `width` (mặc định 1280), `height` (mặc định 720), danh sách `objects`.

2. **Hoàn thiện `qc/parser.py`:**
   - Viết hàm `load_bdd100k(file_path: str) -> List[FrameData]`:
     - Mở file JSON an toàn, bắt ngoại lệ nếu file rỗng / lỗi cú pháp JSON.
     - Duyệt qua từng frame và trích xuất đúng các trường `box2d`, `poly2d`, `attributes`.
     - Bỏ qua các object rác không có tọa độ hoặc log warning.

### 3. Tiêu chí nghiệm thu (DoD)
- Chạy lệnh thử nghiệm:
  ```python
  from qc.parser import load_bdd100k
  frames = load_bdd100k("data_sample/sample_valid.json")
  assert len(frames) > 0
  assert frames[0].objects[0].box2d is not None
  print("Parser hoạt động chuẩn xác!")
  ```

---

## 👤 THÀNH VIÊN 2: NGUYỄN THANH ĐỨC (`2A202602279`)
**Vai trò:** BBox QC Specialist  
**File phụ trách:** [`qc/rules/bbox_rules.py`](qc/rules/bbox_rules.py)

### 1. Mục tiêu
Kiểm tra toàn diện tất cả các lỗi hình học liên quan đến **Bounding Box 2D**.

### 2. Danh sách Rule cần hiện thực
| Mã Rule | Tên lỗi | Điều kiện kích hoạt | Mức độ |
|---|---|---|---|
| **`RULE_B01`** | Out of Bounds | Box vượt ra ngoài kích thước ảnh: $x_1 < 0$ hoặc $y_1 < 0$ hoặc $x_2 > W$ hoặc $y_2 > H$. | 🔴 ERROR |
| **`RULE_B02`** | Inverted / Zero Box | Tọa độ bị ngược hoặc diện tích bằng 0: $x_2 \le x_1$ hoặc $y_2 \le y_1$. | 🔴 ERROR |
| **`RULE_B03`** | Too Small Box | Diện tích $(x_2 - x_1) \times (y_2 - y_1) < 64\text{px}$ (vật thể nhỏ hơn $8 \times 8$). | 🟡 WARNING |
| **`RULE_B04`** | Abnormal Ratio | Tỉ lệ cạnh dị thường: $(w / h > 25)$ hoặc $(h / w > 25)$ (trừ class `traffic sign` hoặc `barrier`). | 🟡 WARNING |

### 3. Khung code mẫu
```python
# qc/rules/bbox_rules.py
from typing import List
from qc.models import FrameData, QCError

def check_bbox_rules(frame: FrameData) -> List[QCError]:
    errors = []
    for obj in frame.objects:
        if not obj.box2d:
            continue
        x1, y1, x2, y2 = obj.box2d.x1, obj.box2d.y1, obj.box2d.x2, obj.box2d.y2
        w, h = x2 - x1, y2 - y1

        # B01: Out of bounds
        if x1 < 0 or y1 < 0 or x2 > frame.width or y2 > frame.height:
            errors.append(QCError(
                frame_name=frame.name, object_id=obj.id, category=obj.category,
                rule_id="RULE_B01", severity="ERROR",
                message=f"Box vượt ngoài khung hình (x1={x1}, y1={y1}, x2={x2}, y2={y2}) trên ảnh {frame.width}x{frame.height}"
            ))

        # B02: Inverted or zero size
        if w <= 0 or h <= 0:
            errors.append(QCError(
                frame_name=frame.name, object_id=obj.id, category=obj.category,
                rule_id="RULE_B02", severity="ERROR",
                message=f"Tọa độ box bị âm hoặc rỗng (w={w}, h={h})"
            ))
        elif w * h < 64: # B03: Quá nhỏ
            errors.append(QCError(
                frame_name=frame.name, object_id=obj.id, category=obj.category,
                rule_id="RULE_B03", severity="WARNING",
                message=f"Box quá nhỏ ({w*h:.1f}px < 64px), nghi ngờ nhiễu hoặc chấm nhầm"
            ))

        # B04: Tỉ lệ bất thường
        if w > 0 and h > 0 and obj.category not in ["barrier"]:
            ratio = max(w / h, h / w)
            if ratio > 25:
                errors.append(QCError(
                    frame_name=frame.name, object_id=obj.id, category=obj.category,
                    rule_id="RULE_B04", severity="WARNING",
                    message=f"Tỉ lệ khung hình dị thường (ratio={ratio:.1f}:1)"
                ))
    return errors
```

---

## 👤 THÀNH VIÊN 3: HOÀNG CÔNG CHỨ (`2A202602187`)
**Vai trò:** Segmentation QC Specialist  
**File phụ trách:** [`qc/rules/polygon_rules.py`](qc/rules/polygon_rules.py)

### 1. Mục tiêu
Kiểm tra tính hợp lệ hình học của các nhãn phân đoạn (**Polygon / Segmentation**) bằng thư viện `shapely`.

### 2. Danh sách Rule cần hiện thực
| Mã Rule | Tên lỗi | Điều kiện kích hoạt | Mức độ |
|---|---|---|---|
| **`RULE_P01`** | Insufficient Vertices | Polygon có ít hơn 3 đỉnh (không tạo thành đa giác). | 🔴 ERROR |
| **`RULE_P02`** | Self-Intersection | Đa giác bị xoắn, vắt chéo nét vẽ (tự cắt chính nó). | 🔴 ERROR |
| **`RULE_P03`** | Mask vs Box Mismatch | Khung bao của polygon lệch quá nhiều so với BBox được gán ($\text{IoU} < 0.7$). | 🟡 WARNING |

### 3. Khung code mẫu
```python
# qc/rules/polygon_rules.py
from typing import List
from shapely.geometry import Polygon as ShapelyPolygon, box as shapely_box
from qc.models import FrameData, QCError

def check_polygon_rules(frame: FrameData) -> List[QCError]:
    errors = []
    for obj in frame.objects:
        if not obj.poly2d:
            continue
        vertices = obj.poly2d.vertices

        # P01: Không đủ 3 đỉnh
        if len(vertices) < 3:
            errors.append(QCError(
                frame_name=frame.name, object_id=obj.id, category=obj.category,
                rule_id="RULE_P01", severity="ERROR",
                message=f"Polygon chỉ có {len(vertices)} đỉnh, yêu cầu tối thiểu 3 đỉnh"
            ))
            continue

        # P02: Tự cắt chính nó (Dùng Shapely)
        poly = ShapelyPolygon(vertices)
        if not poly.is_valid or not poly.is_simple:
            errors.append(QCError(
                frame_name=frame.name, object_id=obj.id, category=obj.category,
                rule_id="RULE_P02", severity="ERROR",
                message="Polygon bị lỗi tự cắt viền (self-intersection) hoặc không hợp lệ"
            ))

        # P03: Mask lệch BBox
        if obj.box2d and poly.is_valid:
            poly_minx, poly_miny, poly_maxx, poly_maxy = poly.bounds
            poly_bbox = shapely_box(poly_minx, poly_miny, poly_maxx, poly_maxy)
            real_bbox = shapely_box(obj.box2d.x1, obj.box2d.y1, obj.box2d.x2, obj.box2d.y2)

            intersection = poly_bbox.intersection(real_bbox).area
            union = poly_bbox.union(real_bbox).area
            iou = intersection / union if union > 0 else 0

            if iou < 0.70:
                errors.append(QCError(
                    frame_name=frame.name, object_id=obj.id, category=obj.category,
                    rule_id="RULE_P03", severity="WARNING",
                    message=f"Khung bao của polygon lệch nhiều so với box2d (IoU={iou:.2f} < 0.70)"
                ))
    return errors
```

---

## 👤 THÀNH VIÊN 4: TRẦN THỊ THỦY TIÊN (`2A202602171`)
**Vai trò:** Consistency & Attribute Specialist  
**File phụ trách:** [`qc/rules/attribute_rules.py`](qc/rules/attribute_rules.py)

### 1. Mục tiêu
Kiểm tra các lỗi vẽ trùng lặp đối tượng (Duplicate) và thiếu sót thuộc tính bắt buộc (Attributes).

### 2. Danh sách Rule cần hiện thực
| Mã Rule | Tên lỗi | Điều kiện kích hoạt | Mức độ |
|---|---|---|---|
| **`RULE_A01`** | Duplicate Object | Hai box cùng class trong 1 frame đè lên nhau với $\text{IoU} > 0.85$. | 🔴 ERROR |
| **`RULE_A02`** | Missing Attributes | Thiếu thuộc tính bắt buộc `occluded` hoặc `truncated`. | 🟡 WARNING |
| **`RULE_A03`** | Traffic Light Color | Category là `traffic light` nhưng thuộc tính `trafficLightColor` để trống hoặc sai giá trị. | 🔴 ERROR |

### 3. Khung code mẫu
```python
# qc/rules/attribute_rules.py
from typing import List
from qc.models import FrameData, QCError

def calculate_iou(b1, b2):
    ix1, iy1 = max(b1.x1, b2.x1), max(b1.y1, b2.y1)
    ix2, iy2 = min(b1.x2, b2.x2), min(b1.y2, b2.y2)
    iw, ih = max(0, ix2 - ix1), max(0, iy2 - iy1)
    inter = iw * ih
    a1 = (b1.x2 - b1.x1) * (b1.y2 - b1.y1)
    a2 = (b2.x2 - b2.x1) * (b2.y2 - b2.y1)
    union = a1 + a2 - inter
    return inter / union if union > 0 else 0

def check_attribute_rules(frame: FrameData) -> List[QCError]:
    errors = []
    objects = frame.objects
    n = len(objects)

    # A01: Kiểm tra vẽ trùng lặp (Duplicate Detection)
    for i in range(n):
        for j in range(i + 1, n):
            obj_a, obj_b = objects[i], objects[j]
            if obj_a.category == obj_b.category and obj_a.box2d and obj_b.box2d:
                iou = calculate_iou(obj_a.box2d, obj_b.box2d)
                if iou > 0.85:
                    errors.append(QCError(
                        frame_name=frame.name, object_id=f"{obj_a.id}&{obj_b.id}", category=obj_a.category,
                        rule_id="RULE_A01", severity="ERROR",
                        message=f"Phát hiện vẽ trùng lặp giữa ID {obj_a.id} và ID {obj_b.id} (IoU={iou:.2f})"
                    ))

    # A02 & A03: Kiểm tra thuộc tính
    for obj in objects:
        attrs = obj.attributes
        # A02: Thiếu occluded hoặc truncated
        if "occluded" not in attrs or "truncated" not in attrs:
            errors.append(QCError(
                frame_name=frame.name, object_id=obj.id, category=obj.category,
                rule_id="RULE_A02", severity="WARNING",
                message="Thiếu thuộc tính bắt buộc (occluded hoặc truncated)"
            ))

        # A03: Màu đèn giao thông
        if obj.category == "traffic light":
            color = attrs.get("trafficLightColor")
            valid_colors = ["red", "yellow", "green", "none"]
            if not color or color not in valid_colors:
                errors.append(QCError(
                    frame_name=frame.name, object_id=obj.id, category=obj.category,
                    rule_id="RULE_A03", severity="ERROR",
                    message=f"Đèn giao thông có màu không hợp lệ: '{color}'. Bắt buộc: {valid_colors}"
                ))

    return errors
```

---

## 👤 THÀNH VIÊN 5: ĐÀO NGỌC HIẾU (`2A202602081`) (LEAD)
**Vai trò:** Team Lead & Core Integration  
**File phụ trách:** [`main.py`](main.py), [`qc/reporter.py`](qc/reporter.py), Slide Báo cáo & Benchmark

### 1. Mục tiêu
- Ghép nối engine: nhận dữ liệu từ TV1, chuyển qua rules của TV2, TV3, TV4.
- Xây dựng giao diện báo cáo đẹp mắt (Terminal, HTML, CSV).
- Chuẩn bị dữ liệu kiểm thử và đo đạc số liệu để báo cáo nghiệm thu với Mentor.

### 2. Nhiệm vụ cụ thể
1. **Hoàn thiện `qc/reporter.py`:**
   - Dùng thư viện `rich` để in bảng màu tóm tắt trên terminal.
   - Xuất file HTML report trực quan (có thanh tiến độ, bộ lọc theo ERROR/WARNING).
   - Xuất file CSV báo cáo lỗi kèm `frame`, `id`, `message` để annotator mở ra sửa bài.
2. **Hoàn thiện `main.py`:**
   - Xây dựng CLI bằng `argparse` hỗ trợ các tham số: `--input`, `--output`, `--severity`.
3. **Thực nghiệm đo lường chỉ số:**
   - Tạo bộ test 50 frame (có sẵn 30 lỗi giả lập).
   - Đo thời gian chạy tool (mục tiêu < 5 giây).
   - Tính toán tỷ lệ phát hiện lỗi (Recall) và tỷ lệ báo sai (Precision).
   - Điền số liệu vào slide thuyết trình nghiệm thu.
