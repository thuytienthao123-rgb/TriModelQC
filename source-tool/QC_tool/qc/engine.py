"""
engine.py — QC Engine: tích hợp tất cả rule và chạy trên danh sách frame.
Phụ trách chính: Đào Ngọc Hiếu (2A202602081)
"""

from __future__ import annotations
from typing import List, Optional

from qc.models import FrameData, QCReport
from qc.rules.base import BaseRule
from qc.rules.bbox_rules import ALL_BBOX_RULES
from qc.rules.polygon_rules import ALL_POLYGON_RULES
from qc.rules.attribute_rules import ALL_ATTRIBUTE_RULES

# Tập hợp tất cả rules theo thứ tự chạy
DEFAULT_RULES: List[BaseRule] = (
    ALL_BBOX_RULES +
    ALL_POLYGON_RULES +
    ALL_ATTRIBUTE_RULES
)


def run_qc(
    frames: List[FrameData],
    rules: Optional[List[BaseRule]] = None,
) -> QCReport:
    """
    Chạy toàn bộ QC pipeline trên danh sách frame.

    Args:
        frames: Danh sách FrameData đã parse từ file nhãn.
        rules:  Danh sách Rule tùy chỉnh. Mặc định dùng tất cả 10 rules.

    Returns:
        QCReport tổng hợp toàn bộ lỗi và cảnh báo.
    """
    if rules is None:
        rules = DEFAULT_RULES

    report = QCReport()
    report.total_frames = len(frames)
    report.total_objects = sum(len(f.objects) for f in frames)

    for frame in frames:
        for rule in rules:
            errors = rule.check(frame)
            for err in errors:
                report.add(err)

    return report
