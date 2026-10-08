"""
models.py - Khai báo cấu trúc dữ liệu chuẩn cho QC Tool.
Phụ trách chính: Đoàn Văn Thắng (2A202602327)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class QCError:
    """Đại diện cho một lỗi hoặc cảnh báo được phát hiện."""
    frame_name: str
    object_id: str
    category: str
    rule_id: str       # Ví dụ: RULE_B01, RULE_P02, RULE_A01
    severity: str      # 'ERROR' hoặc 'WARNING'
    message: str       # Chi tiết mô tả lỗi


@dataclass
class BBox2D:
    """Tọa độ hộp bao 2D chuẩn."""
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    @property
    def area(self) -> float:
        return max(0.0, self.width) * max(0.0, self.height)


@dataclass
class Polygon2D:
    """Đa giác phân đoạn 2D."""
    vertices: List[Tuple[float, float]]  # Danh sách các cặp toạ độ (x, y)


@dataclass
class LabeledObject:
    """Đại diện cho một đối tượng được gán nhãn trong frame."""
    id: str
    category: str
    box2d: Optional[BBox2D] = None
    poly2d: Optional[Polygon2D] = None
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FrameData:
    """Đại diện cho một ảnh/frame dữ liệu cần kiểm tra."""
    name: str
    width: int = 1280
    height: int = 720
    objects: List[LabeledObject] = field(default_factory=list)
