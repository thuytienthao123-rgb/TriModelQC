"""
bbox_rules.py — Bộ luật kiểm tra Bounding Box 2D.
Phụ trách chính: Hoàng Công Chứ (2A202602187) & Đào Ngọc Hiếu (2A202602081)

Rules:
  RULE_B01  Out of Bounds       — Tọa độ vượt ra ngoài kích thước ảnh
  RULE_B02  Inverted/Zero Box   — Tọa độ ngược hoặc diện tích rỗng
  RULE_B03  Too Small           — Diện tích < ngưỡng (mặc định 64 px²)
  RULE_B04  Abnormal Ratio      — Tỉ lệ w/h hoặc h/w > 25
"""

from __future__ import annotations
from typing import List

from qc.models import ERROR, WARNING, FrameData, LabeledObject, QCError
from qc.rules.base import BaseRule

# Các class có tỉ lệ dạng dài/mỏng — không áp dụng RULE_B04
_THIN_CLASSES = {"barrier", "traffic sign", "lane", "drivable area"}

# Ngưỡng diện tích tối thiểu (px²)
MIN_AREA_PX = 64  # 8 × 8 pixel

# Ngưỡng tỉ lệ cạnh tối đa
MAX_RATIO = 25.0


class RuleB01OutOfBounds(BaseRule):
    rule_id = "RULE_B01"
    description = "Box vượt ra ngoài khung hình ảnh"

    def check(self, frame: FrameData) -> List[QCError]:
        errors: List[QCError] = []
        for obj in frame.objects:
            b = obj.box2d
            if b is None:
                continue
            out_x1 = b.x1 < 0
            out_y1 = b.y1 < 0
            out_x2 = b.x2 > frame.width
            out_y2 = b.y2 > frame.height
            if any([out_x1, out_y1, out_x2, out_y2]):
                detail = []
                if out_x1: detail.append(f"x1={b.x1:.1f}<0")
                if out_y1: detail.append(f"y1={b.y1:.1f}<0")
                if out_x2: detail.append(f"x2={b.x2:.1f}>{frame.width}")
                if out_y2: detail.append(f"y2={b.y2:.1f}>{frame.height}")
                errors.append(QCError(
                    frame_name=frame.name,
                    object_id=obj.id,
                    category=obj.category,
                    rule_id=self.rule_id,
                    severity=ERROR,
                    message=f"Box vượt ngoài khung {frame.width}×{frame.height}px ({', '.join(detail)})",
                ))
        return errors


class RuleB02InvertedOrZero(BaseRule):
    rule_id = "RULE_B02"
    description = "Tọa độ box bị đảo ngược hoặc rỗng"

    def check(self, frame: FrameData) -> List[QCError]:
        errors: List[QCError] = []
        for obj in frame.objects:
            b = obj.box2d
            if b is None:
                continue
            if b.width <= 0 or b.height <= 0:
                errors.append(QCError(
                    frame_name=frame.name,
                    object_id=obj.id,
                    category=obj.category,
                    rule_id=self.rule_id,
                    severity=ERROR,
                    message=(
                        f"Tọa độ đảo ngược hoặc rỗng "
                        f"(w={b.width:.1f}, h={b.height:.1f}). "
                        f"Yêu cầu x2 > x1 và y2 > y1."
                    ),
                ))
        return errors


class RuleB03TooSmall(BaseRule):
    rule_id = "RULE_B03"
    description = f"Box có diện tích < {MIN_AREA_PX}px² (nghi ngờ nhiễu)"

    def check(self, frame: FrameData) -> List[QCError]:
        errors: List[QCError] = []
        for obj in frame.objects:
            b = obj.box2d
            if b is None:
                continue
            if b.width > 0 and b.height > 0 and b.area < MIN_AREA_PX:
                errors.append(QCError(
                    frame_name=frame.name,
                    object_id=obj.id,
                    category=obj.category,
                    rule_id=self.rule_id,
                    severity=WARNING,
                    message=(
                        f"Box quá nhỏ (diện tích={b.area:.1f}px² < {MIN_AREA_PX}px²). "
                        f"Kích thước: {b.width:.1f}×{b.height:.1f}px. "
                        f"Kiểm tra xem có phải vật thể thật không."
                    ),
                ))
        return errors


class RuleB04AbnormalRatio(BaseRule):
    rule_id = "RULE_B04"
    description = f"Tỉ lệ cạnh bất thường (> {MAX_RATIO}:1)"

    def check(self, frame: FrameData) -> List[QCError]:
        errors: List[QCError] = []
        for obj in frame.objects:
            if obj.category.lower() in _THIN_CLASSES:
                continue
            b = obj.box2d
            if b is None or b.width <= 0 or b.height <= 0:
                continue
            ratio = max(b.width / b.height, b.height / b.width)
            if ratio > MAX_RATIO:
                errors.append(QCError(
                    frame_name=frame.name,
                    object_id=obj.id,
                    category=obj.category,
                    rule_id=self.rule_id,
                    severity=WARNING,
                    message=(
                        f"Tỉ lệ khung hình dị thường ({ratio:.1f}:1 > {MAX_RATIO}:1). "
                        f"Kích thước: {b.width:.1f}×{b.height:.1f}px."
                    ),
                ))
        return errors


class RuleB05ExtremeScale(BaseRule):
    rule_id = "RULE_B05"
    description = "Box chiếm gần trọn khung hình (> 96% diện tích) nghi ngờ kéo nhầm"

    def check(self, frame: FrameData) -> List[QCError]:
        errors: List[QCError] = []
        frame_area = float(frame.width * frame.height)
        if frame_area <= 0:
            return errors

        for obj in frame.objects:
            if obj.category.lower() in _THIN_CLASSES or obj.category.lower() in {"background", "scene"}:
                continue
            b = obj.box2d
            if b is None or b.width <= 0 or b.height <= 0:
                continue

            area_pct = b.area / frame_area
            if area_pct > 0.96:
                errors.append(QCError(
                    frame_name=frame.name,
                    object_id=obj.id,
                    category=obj.category,
                    rule_id=self.rule_id,
                    severity=WARNING,
                    message=(
                        f"Box chiếm {area_pct:.1%} diện tích khung hình ({b.width:.0f}×{b.height:.0f}px). "
                        f"Nghi ngờ annotator lỡ tay kéo toàn cảnh thay vì bao vật thể thật."
                    ),
                ))
        return errors


# Danh sách tất cả bbox rules, dùng trong engine
ALL_BBOX_RULES: List[BaseRule] = [
    RuleB01OutOfBounds(),
    RuleB02InvertedOrZero(),
    RuleB03TooSmall(),
    RuleB04AbnormalRatio(),
    RuleB05ExtremeScale(),
]
