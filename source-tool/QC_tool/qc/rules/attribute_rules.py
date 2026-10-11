"""
attribute_rules.py — Bộ luật kiểm tra Trùng lặp & Thuộc tính.
Phụ trách chính: Trần Thị Thủy Tiên (2A202602171)

Rules:
  RULE_A01  Duplicate Object          — Hai box cùng class IoU > 0.85
  RULE_A02  Missing Attributes        — Thiếu occluded hoặc truncated
  RULE_A03  Traffic Light Color       — Đèn giao thông thiếu/sai màu
"""

from __future__ import annotations
from typing import List, Set

from qc.models import ERROR, WARNING, FrameData, QCError
from qc.rules.base import BaseRule

# Ngưỡng IoU để coi là trùng lặp
DUPLICATE_IOU_THRESHOLD = 0.85

# Giá trị màu đèn giao thông hợp lệ
VALID_TRAFFIC_LIGHT_COLORS: Set[str] = {"red", "yellow", "green", "none"}

# Thuộc tính bắt buộc cho mọi loại đối tượng
MANDATORY_ATTRIBUTES = {"occluded", "truncated"}

# Các class không bắt buộc truncated
_NO_TRUNCATED_CHECK = {"lane", "drivable area", "sky"}


class RuleA01DuplicateObject(BaseRule):
    rule_id = "RULE_A01"
    description = f"Hai box cùng class chồng lấn IoU > {DUPLICATE_IOU_THRESHOLD}"

    def check(self, frame: FrameData) -> List[QCError]:
        errors: List[QCError] = []
        objs = [o for o in frame.objects if o.box2d is not None]
        n = len(objs)

        reported: set = set()  # tránh báo cáo một cặp nhiều lần

        for i in range(n):
            for j in range(i + 1, n):
                a, b = objs[i], objs[j]
                if a.category.lower() != b.category.lower():
                    continue  # chỉ kiểm tra cùng class
                pair_key = (min(a.id, b.id), max(a.id, b.id))
                if pair_key in reported:
                    continue

                iou = a.box2d.iou(b.box2d)
                if iou > DUPLICATE_IOU_THRESHOLD:
                    reported.add(pair_key)
                    errors.append(QCError(
                        frame_name=frame.name,
                        object_id=f"{a.id} & {b.id}",
                        category=a.category,
                        rule_id=self.rule_id,
                        severity=ERROR,
                        message=(
                            f"Nghi ngờ vẽ trùng lặp: object '{a.id}' và '{b.id}' "
                            f"cùng class '{a.category}' chồng lấn nhau (IoU={iou:.2f} > {DUPLICATE_IOU_THRESHOLD})."
                        ),
                    ))
        return errors


class RuleA02MissingAttributes(BaseRule):
    rule_id = "RULE_A02"
    description = "Thiếu thuộc tính bắt buộc (occluded, truncated)"

    def check(self, frame: FrameData) -> List[QCError]:
        errors: List[QCError] = []
        for obj in frame.objects:
            missing = []
            attrs = obj.attributes or {}

            # Kiểm tra occluded
            if "occluded" not in attrs:
                missing.append("occluded")

            # Kiểm tra truncated (trừ một số class đặc biệt)
            if obj.category.lower() not in _NO_TRUNCATED_CHECK:
                if "truncated" not in attrs:
                    missing.append("truncated")

            if missing:
                errors.append(QCError(
                    frame_name=frame.name,
                    object_id=obj.id,
                    category=obj.category,
                    rule_id=self.rule_id,
                    severity=WARNING,
                    message=(
                        f"Thiếu thuộc tính bắt buộc: {missing}. "
                        f"Vui lòng điền đầy đủ trước khi nộp bài."
                    ),
                ))
        return errors


class RuleA03TrafficLightColor(BaseRule):
    rule_id = "RULE_A03"
    description = "Đèn giao thông thiếu hoặc sai giá trị màu"

    def check(self, frame: FrameData) -> List[QCError]:
        errors: List[QCError] = []
        for obj in frame.objects:
            if obj.category.lower() != "traffic light":
                continue
            attrs = obj.attributes or {}
            color = attrs.get("trafficLightColor")
            if color is None:
                errors.append(QCError(
                    frame_name=frame.name,
                    object_id=obj.id,
                    category=obj.category,
                    rule_id=self.rule_id,
                    severity=ERROR,
                    message=(
                        f"Đèn giao thông thiếu thuộc tính 'trafficLightColor'. "
                        f"Giá trị hợp lệ: {sorted(VALID_TRAFFIC_LIGHT_COLORS)}."
                    ),
                ))
            elif str(color).lower() not in VALID_TRAFFIC_LIGHT_COLORS:
                errors.append(QCError(
                    frame_name=frame.name,
                    object_id=obj.id,
                    category=obj.category,
                    rule_id=self.rule_id,
                    severity=ERROR,
                    message=(
                        f"Màu đèn không hợp lệ: '{color}'. "
                        f"Giá trị hợp lệ: {sorted(VALID_TRAFFIC_LIGHT_COLORS)}."
                    ),
                ))
        return errors


ALL_ATTRIBUTE_RULES: List[BaseRule] = [
    RuleA01DuplicateObject(),
    RuleA02MissingAttributes(),
    RuleA03TrafficLightColor(),
]
