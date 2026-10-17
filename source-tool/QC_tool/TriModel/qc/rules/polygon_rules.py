"""
polygon_rules.py — Bộ luật kiểm tra Polygon / Segmentation 2D.
Phụ trách chính: Hoàng Công Chứ (2A202602187)

Rules:
  RULE_P01  Insufficient Vertices  — Polygon có < 3 đỉnh
  RULE_P02  Self-Intersection      — Đa giác tự cắt viền (dùng shapely)
  RULE_P03  Mask vs Box Mismatch   — Khung bao polygon lệch BBox khai báo (IoU < 0.7)
"""

from __future__ import annotations
from typing import List

from qc.models import ERROR, WARNING, FrameData, QCError
from qc.rules.base import BaseRule

# Ngưỡng IoU tối thiểu giữa polygon bounding box và box2d được khai báo
MIN_MASK_BOX_IOU = 0.70

try:
    from shapely.geometry import Polygon as ShapelyPolygon, box as shapely_box
    _SHAPELY_AVAILABLE = True
except ImportError:
    _SHAPELY_AVAILABLE = False


class RuleP01InsufficientVertices(BaseRule):
    rule_id = "RULE_P01"
    description = "Polygon có ít hơn 3 đỉnh"

    def check(self, frame: FrameData) -> List[QCError]:
        errors: List[QCError] = []
        for obj in frame.objects:
            if obj.poly2d is None:
                continue
            n = len(obj.poly2d.vertices)
            if n < 3:
                errors.append(QCError(
                    frame_name=frame.name,
                    object_id=obj.id,
                    category=obj.category,
                    rule_id=self.rule_id,
                    severity=ERROR,
                    message=(
                        f"Polygon chỉ có {n} đỉnh — cần tối thiểu 3 đỉnh để tạo thành đa giác hợp lệ."
                    ),
                ))
        return errors


class RuleP02SelfIntersection(BaseRule):
    rule_id = "RULE_P02"
    description = "Polygon tự cắt chính nó (self-intersection)"

    def check(self, frame: FrameData) -> List[QCError]:
        errors: List[QCError] = []

        if not _SHAPELY_AVAILABLE:
            # Fallback thủ công nếu shapely chưa cài
            return self._manual_check(frame)

        for obj in frame.objects:
            if obj.poly2d is None or len(obj.poly2d.vertices) < 3:
                continue
            try:
                poly = ShapelyPolygon(obj.poly2d.vertices)
                if not poly.is_valid or not poly.is_simple:
                    reason = "Polygon bị xoắn/thắt nút (không đơn giản)" if not poly.is_simple else "Shapely: is_valid=False"
                    errors.append(QCError(
                        frame_name=frame.name,
                        object_id=obj.id,
                        category=obj.category,
                        rule_id=self.rule_id,
                        severity=ERROR,
                        message=f"Polygon tự cắt viền — {reason}. Vui lòng vẽ lại.",
                    ))
            except Exception as exc:
                errors.append(QCError(
                    frame_name=frame.name,
                    object_id=obj.id,
                    category=obj.category,
                    rule_id=self.rule_id,
                    severity=ERROR,
                    message=f"Lỗi khi kiểm tra polygon geometry: {exc}",
                ))
        return errors

    def _manual_check(self, frame: FrameData) -> List[QCError]:
        """
        Kiểm tra tự cắt thủ công (dùng khi shapely chưa cài).
        Phát hiện self-intersection bằng cách kiểm tra từng cặp cạnh không kề nhau.
        """
        errors: List[QCError] = []
        for obj in frame.objects:
            if obj.poly2d is None or len(obj.poly2d.vertices) < 4:
                continue
            verts = obj.poly2d.vertices
            n = len(verts)
            edges = [(verts[i], verts[(i + 1) % n]) for i in range(n)]

            def segments_intersect(p1, p2, p3, p4) -> bool:
                """Kiểm tra hai đoạn thẳng p1-p2 và p3-p4 có cắt nhau không."""
                def cross(o, a, b):
                    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
                d1 = cross(p3, p4, p1)
                d2 = cross(p3, p4, p2)
                d3 = cross(p1, p2, p3)
                d4 = cross(p1, p2, p4)
                if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and \
                   ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)):
                    return True
                return False

            found = False
            for i in range(n):
                for j in range(i + 2, n):
                    if i == 0 and j == n - 1:
                        continue  # cạnh kề nhau
                    if segments_intersect(edges[i][0], edges[i][1],
                                          edges[j][0], edges[j][1]):
                        found = True
                        break
                if found:
                    break

            if found:
                errors.append(QCError(
                    frame_name=frame.name,
                    object_id=obj.id,
                    category=obj.category,
                    rule_id=self.rule_id,
                    severity=ERROR,
                    message="Polygon tự cắt viền (phát hiện bằng kiểm tra đoạn thẳng thủ công).",
                ))
        return errors


class RuleP03MaskBoxMismatch(BaseRule):
    rule_id = "RULE_P03"
    description = "Khung bao của polygon lệch BBox khai báo (IoU < 0.70)"

    def check(self, frame: FrameData) -> List[QCError]:
        errors: List[QCError] = []
        for obj in frame.objects:
            if obj.poly2d is None or obj.box2d is None:
                continue
            poly_bbox = obj.poly2d.bounding_box()
            if poly_bbox is None:
                continue
            iou = poly_bbox.iou(obj.box2d)
            if iou < MIN_MASK_BOX_IOU:
                errors.append(QCError(
                    frame_name=frame.name,
                    object_id=obj.id,
                    category=obj.category,
                    rule_id=self.rule_id,
                    severity=WARNING,
                    message=(
                        f"Khung bao polygon lệch nhiều so với box2d khai báo "
                        f"(IoU={iou:.2f} < {MIN_MASK_BOX_IOU}). "
                        f"Poly bbox: [{poly_bbox.x1:.0f},{poly_bbox.y1:.0f},{poly_bbox.x2:.0f},{poly_bbox.y2:.0f}] | "
                        f"Box2D: [{obj.box2d.x1:.0f},{obj.box2d.y1:.0f},{obj.box2d.x2:.0f},{obj.box2d.y2:.0f}]"
                    ),
                ))
        return errors


class RuleP04SpikeOrDuplicateVertices(BaseRule):
    rule_id = "RULE_P04"
    description = "Polygon có đỉnh trùng lặp liên tiếp hoặc góc gai dị thường (< 3.5°)"

    def check(self, frame: FrameData) -> List[QCError]:
        import math
        errors: List[QCError] = []
        for obj in frame.objects:
            if obj.poly2d is None or len(obj.poly2d.vertices) < 3:
                continue
            verts = obj.poly2d.vertices
            n = len(verts)

            has_dup = False
            for i in range(n):
                p1 = verts[i]
                p2 = verts[(i + 1) % n]
                if math.hypot(p1[0] - p2[0], p1[1] - p2[1]) < 0.8:
                    has_dup = True
                    break

            has_spike = False
            spike_angle_deg = 180.0
            for i in range(n):
                p_prev = verts[(i - 1) % n]
                p_curr = verts[i]
                p_next = verts[(i + 1) % n]

                v1 = (p_prev[0] - p_curr[0], p_prev[1] - p_curr[1])
                v2 = (p_next[0] - p_curr[0], p_next[1] - p_curr[1])
                len1 = math.hypot(v1[0], v1[1])
                len2 = math.hypot(v2[0], v2[1])

                if len1 > 15.0 and len2 > 15.0:
                    dot = v1[0] * v2[0] + v1[1] * v2[1]
                    cos_ang = max(-1.0, min(1.0, dot / (len1 * len2)))
                    ang = math.degrees(math.acos(cos_ang))
                    if ang < 3.5:
                        has_spike = True
                        spike_angle_deg = ang
                        break

            if has_dup or has_spike:
                reasons = []
                if has_dup:
                    reasons.append("đỉnh trùng lặp liên tiếp (khoảng cách < 0.8px)")
                if has_spike:
                    reasons.append(f"gai nhọn dị thường ({spike_angle_deg:.1f}° < 3.5°)")
                errors.append(QCError(
                    frame_name=frame.name,
                    object_id=obj.id,
                    category=obj.category,
                    rule_id=self.rule_id,
                    severity=WARNING,
                    message=f"Đa giác lỗi hình học: {', '.join(reasons)}. Cần làm mượt hoặc xóa đỉnh thừa.",
                ))
        return errors


ALL_POLYGON_RULES: List[BaseRule] = [
    RuleP01InsufficientVertices(),
    RuleP02SelfIntersection(),
    RuleP03MaskBoxMismatch(),
    RuleP04SpikeOrDuplicateVertices(),
]
