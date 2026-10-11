"""
models.py — Cấu trúc dữ liệu chuẩn cho BDD-QC Tool.
Phụ trách chính: Đoàn Văn Thắng (2A202602327)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Severity constants
# ---------------------------------------------------------------------------
ERROR = "ERROR"
WARNING = "WARNING"


# ---------------------------------------------------------------------------
# Geometry primitives
# ---------------------------------------------------------------------------

@dataclass
class BBox2D:
    """Hộp bao hình chữ nhật trong không gian 2D."""
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

    def iou(self, other: "BBox2D") -> float:
        """Tính Intersection over Union với box khác."""
        ix1 = max(self.x1, other.x1)
        iy1 = max(self.y1, other.y1)
        ix2 = min(self.x2, other.x2)
        iy2 = min(self.y2, other.y2)
        inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
        union = self.area + other.area - inter
        return inter / union if union > 0 else 0.0


@dataclass
class Polygon2D:
    """Đa giác phân đoạn 2D."""
    vertices: List[Tuple[float, float]]

    def bounding_box(self) -> Optional[BBox2D]:
        """Trả về khung bao ngoại tiếp polygon."""
        if len(self.vertices) < 2:
            return None
        xs = [v[0] for v in self.vertices]
        ys = [v[1] for v in self.vertices]
        return BBox2D(min(xs), min(ys), max(xs), max(ys))


# ---------------------------------------------------------------------------
# Domain objects
# ---------------------------------------------------------------------------

@dataclass
class LabeledObject:
    """Một đối tượng được gán nhãn trong một frame."""
    id: str
    category: str
    box2d: Optional[BBox2D] = None
    poly2d: Optional[Polygon2D] = None
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FrameData:
    """Đại diện cho một ảnh / frame cần kiểm tra QC."""
    name: str
    width: int = 1280
    height: int = 720
    objects: List[LabeledObject] = field(default_factory=list)


# ---------------------------------------------------------------------------
# QC result
# ---------------------------------------------------------------------------

@dataclass
class QCError:
    """Kết quả phát hiện một lỗi hoặc cảnh báo."""
    frame_name: str
    object_id: str
    category: str
    rule_id: str      # Ví dụ: RULE_B01
    severity: str     # ERROR | WARNING
    message: str

    def is_error(self) -> bool:
        return self.severity == ERROR

    def is_warning(self) -> bool:
        return self.severity == WARNING


@dataclass
class QCReport:
    """Tổng hợp toàn bộ kết quả sau khi quét."""
    total_frames: int = 0
    total_objects: int = 0
    errors: List[QCError] = field(default_factory=list)

    def add(self, err: QCError) -> None:
        self.errors.append(err)

    def error_count(self) -> int:
        return sum(1 for e in self.errors if e.is_error())

    def warning_count(self) -> int:
        return sum(1 for e in self.errors if e.is_warning())

    def has_issues(self) -> bool:
        return len(self.errors) > 0
