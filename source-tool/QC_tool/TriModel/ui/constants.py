from pathlib import Path
from typing import Dict, List

# ---------------------------------------------------------------------------
# Hướng dẫn khắc phục chi tiết theo từng mã Rule
# ---------------------------------------------------------------------------
RULE_SUGGESTIONS: Dict[str, str] = {
    "RULE_B01": "Thu nhỏ hoặc kéo BBox về trong phạm vi khung hình (x ≥ 0, y ≥ 0, x ≤ W, y ≤ H).",
    "RULE_B02": "Đảo lại tọa độ sao cho x2 > x1 và y2 > y1; kiểm tra kích thước không được bằng 0.",
    "RULE_B03": "Box quá nhỏ (< 64px²). Nếu là vật thể thật hãy giữ lại; nếu là chấm nhầm/nhiễu hãy xóa bỏ.",
    "RULE_B04": "Tỉ lệ khung hình dị thường (> 25:1). Kiểm tra xem có bị kéo dẹt bất thường không.",
    "RULE_P01": "Polygon cần ít nhất 3 đỉnh để tạo thành mặt phẳng khép kín. Hãy bổ sung thêm đỉnh.",
    "RULE_P02": "Đa giác bị xoắn nơ (tự cắt chính nó). Hãy xóa và vẽ lại đa giác đơn không bắt chéo viền.",
    "RULE_P03": "Khung bao polygon lệch quá nhiều so với BBox (IoU < 0.70). Căn chỉnh lại BBox cho khít với mask.",
    "RULE_A01": "Phát hiện 2 box cùng class vẽ đè lên nhau (> 85% IoU). Hãy xóa bớt 1 box bị vẽ trùng.",
    "RULE_A02": "Thiếu thuộc tính bắt buộc (occluded, truncated). Mở panel thuộc tính và đánh dấu giá trị thật.",
    "RULE_A03": "Đèn giao thông bắt buộc khai báo màu sắc (red, yellow, green, none).",
    "RULE_T01": "Vật thể xuất hiện ở frame trước & sau nhưng mất dấu ở frame này. Bổ sung nhãn liên tục.",
    "RULE_T02": "Vị trí box bị nhảy giật bất thường giữa 2 frame liên tiếp (> 35%). Căn chỉnh lại vị trí nội suy.",
    "RULE_B05": "Box chiếm gần hết toàn cảnh (> 96%). Xóa bỏ nếu vô tình kéo chuột toàn màn hình.",
    "RULE_P04": "Làm mượt đa giác, xóa bớt các đỉnh trùng nhau hoặc góc nhọn gấp khúc dị thường.",
    "RULE_C01": "Đổi lại tên phân loại (class) về đúng chuẩn BDD100K (ví dụ: car, truck, pedestrian).",
    "RULE_AI01": "AI nghi ngờ có xe/người trong ảnh nhưng chưa được gán nhãn. Kiểm tra lại ảnh gốc để bổ sung.",
}

# ---------------------------------------------------------------------------
# Hỗ trợ đọc đa định dạng (JSON BDD100K & TXT YOLO)
# ---------------------------------------------------------------------------
SUPPORTED_EXTS: List[str] = [".json", ".txt", ".xml"]

BASE_DIR = Path(__file__).parent.parent
PROJECT_ROOT = BASE_DIR.parent.parent

LOCAL_IMAGE_DIRS: List[Path] = [
    PROJECT_ROOT / "dataset_final" / "images",
    BASE_DIR / "data_sample" / "images",
    BASE_DIR / "images",
    BASE_DIR / "data",
    Path("dataset_final/images"),
    Path("images"),
    Path("data"),
]
