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
from qc.rules.sequence_rules import ALL_SEQUENCE_RULES

# Tập hợp tất cả rules theo thứ tự chạy
DEFAULT_RULES: List[BaseRule] = (
    ALL_BBOX_RULES +
    ALL_POLYGON_RULES +
    ALL_ATTRIBUTE_RULES
)


def run_qc(
    frames: List[FrameData],
    rules: Optional[List[BaseRule]] = None,
    sequence_rules: Optional[List[BaseRule]] = None,
) -> QCReport:
    """
    Chạy toàn bộ QC pipeline trên danh sách frame.

    Args:
        frames: Danh sách FrameData đã parse từ file nhãn.
        rules:  Danh sách Rule đơn frame tùy chỉnh. Mặc định dùng 10 rules cốt lõi.
        sequence_rules: Danh sách Rule kiểm tra chuỗi frame liên tiếp (temporal).

    Returns:
        QCReport tổng hợp toàn bộ lỗi và cảnh báo.
    """
    if rules is None:
        rules = DEFAULT_RULES

    report = QCReport()
    report.total_frames = len(frames)
    report.total_objects = sum(len(f.objects) for f in frames)

    # 1. Chạy các rule đơn lẻ trên từng frame
    for frame in frames:
        for rule in rules:
            errors = rule.check(frame)
            for err in errors:
                report.add(err)

    # 2. Chạy các rule chuỗi liên tiếp (Temporal / Sequence Rules) khi có từ 2 frame trở lên
    if len(frames) >= 2:
        seq_rules = sequence_rules if sequence_rules is not None else ALL_SEQUENCE_RULES
        sorted_frames = sorted(frames, key=lambda f: f.name)
        for srule in seq_rules:
            if hasattr(srule, "check_sequence"):
                seq_errors = srule.check_sequence(sorted_frames)
                for err in seq_errors:
                    report.add(err)

    return report
