"""
sequence_rules.py — Bộ luật kiểm tra Chuỗi Frame (Temporal / Sequence Consistency).
Phát hiện: Gán nhãn thiếu giữa chừng (Flicker / Missing label) & Vẽ lệch tọa độ đột ngột.
"""

from __future__ import annotations
import math
import re
from typing import List, Optional, Tuple

from qc.models import ERROR, WARNING, FrameData, LabeledObject, QCError
from qc.rules.base import BaseRule


def _extract_frame_number(name: str) -> Optional[int]:
    """Trích xuất số thứ tự frame từ tên file (ví dụ: Video_3_frame_0160.jpg -> 160)."""
    m = re.findall(r"\d+", name)
    if m:
        try:
            return int(m[-1])  # Lấy cụm số cuối cùng
        except ValueError:
            pass
    return None


class RuleT01MissingObjectInSequence(BaseRule):
    """
    RULE_T01 — Phát hiện gán nhãn THIẾU (Missing Object / Flicker) giữa các frame liên tiếp.
    Nếu vật thể xuất hiện ở frame (t-1) và frame (t+1) cùng vị trí, nhưng ở frame (t) lại biến mất,
    chắc chắn là annotator đã bỏ sót (quên gán nhãn) tại frame đó!
    """

    rule_id = "RULE_T01"
    description = "Nghi ngờ gán nhãn thiếu (vật thể bị biến mất 1 frame giữa chừng)"

    def check(self, frame: FrameData) -> List[QCError]:
        # Rule này kiểm tra trên chuỗi, check() đơn lẻ trả về []
        return []

    def check_sequence(self, sorted_frames: List[FrameData]) -> List[QCError]:
        errors: List[QCError] = []
        if len(sorted_frames) < 3:
            return errors

        for i in range(1, len(sorted_frames) - 1):
            prev_f = sorted_frames[i - 1]
            curr_f = sorted_frames[i]
            next_f = sorted_frames[i + 1]

            # Kiểm tra xem khoảng cách frame có phải liên tiếp không (ví dụ chênh <= 2)
            idx_prev = _extract_frame_number(prev_f.name)
            idx_curr = _extract_frame_number(curr_f.name)
            idx_next = _extract_frame_number(next_f.name)

            if idx_prev is not None and idx_curr is not None and idx_next is not None:
                if not (idx_curr - idx_prev <= 2 and idx_next - idx_curr <= 2):
                    continue

            # Kiểm tra từng object ở prev_f
            for obj_prev in prev_f.objects:
                if obj_prev.box2d is None:
                    continue

                # Tìm object tương ứng ở next_f (cùng class và IoU > 0.25 hoặc tâm gần nhau)
                match_next = None
                for obj_next in next_f.objects:
                    if obj_next.box2d is None:
                        continue
                    if obj_next.category.lower() != obj_prev.category.lower():
                        continue
                    iou = obj_prev.box2d.iou(obj_next.box2d)
                    dist = math.hypot(
                        obj_prev.box2d.center[0] - obj_next.box2d.center[0],
                        obj_prev.box2d.center[1] - obj_next.box2d.center[1],
                    )
                    if iou > 0.25 or dist < 80.0:
                        match_next = obj_next
                        break

                if match_next is not None:
                    # Vật thể tồn tại ở cả prev và next!
                    # Kiểm tra xem ở curr_f có object nào khớp không
                    has_match_curr = False
                    for obj_curr in curr_f.objects:
                        if obj_curr.box2d is None:
                            continue
                        if obj_curr.category.lower() != obj_prev.category.lower():
                            continue
                        iou_prev = obj_prev.box2d.iou(obj_curr.box2d)
                        iou_next = match_next.box2d.iou(obj_curr.box2d)
                        if iou_prev > 0.15 or iou_next > 0.15:
                            has_match_curr = True
                            break

                    if not has_match_curr:
                        errors.append(
                            QCError(
                                frame_name=curr_f.name,
                                object_id=f"missed_{obj_prev.category}",
                                category=obj_prev.category,
                                rule_id=self.rule_id,
                                severity=WARNING,
                                message=(
                                    f"Nghi ngờ GÁN NHÃN THIẾU: Vật thể class '{obj_prev.category}' "
                                    f"xuất hiện ở frame trước ({prev_f.name}) và frame sau ({next_f.name}) "
                                    f"nhưng bị mất dấu tại frame này."
                                ),
                            )
                        )

        return errors


class RuleT02DrasticPositionJump(BaseRule):
    """
    RULE_T02 — Phát hiện VẼ LỆCH VỊ TRÍ đột ngột (Position Drift / Sudden Jump).
    Trong video liên tiếp, vị trí box không thể dịch chuyển > 35% chiều rộng ảnh trong 1 frame duy nhất.
    """

    rule_id = "RULE_T02"
    description = "Nghi ngờ vẽ lệch vị trí (box nhảy vọt tọa độ đột ngột giữa 2 frame)"

    def check(self, frame: FrameData) -> List[QCError]:
        return []

    def check_sequence(self, sorted_frames: List[FrameData]) -> List[QCError]:
        errors: List[QCError] = []
        if len(sorted_frames) < 2:
            return errors

        for i in range(len(sorted_frames) - 1):
            curr_f = sorted_frames[i]
            next_f = sorted_frames[i + 1]

            idx_curr = _extract_frame_number(curr_f.name)
            idx_next = _extract_frame_number(next_f.name)
            if idx_curr is not None and idx_next is not None:
                if abs(idx_next - idx_curr) > 2:
                    continue

            max_dist_px = curr_f.width * 0.35  # Ngưỡng dịch chuyển tối đa trong 1 frame (~670px trên FHD)

            # So khớp theo object id nếu cùng id
            for o1 in curr_f.objects:
                if o1.box2d is None:
                    continue
                for o2 in next_f.objects:
                    if o2.box2d is None:
                        continue
                    if o1.id == o2.id and o1.category.lower() == o2.category.lower():
                        c1 = o1.box2d.center
                        c2 = o2.box2d.center
                        dist = math.hypot(c1[0] - c2[0], c1[1] - c2[1])
                        if dist > max_dist_px:
                            errors.append(
                                QCError(
                                    frame_name=next_f.name,
                                    object_id=o2.id,
                                    category=o2.category,
                                    rule_id=self.rule_id,
                                    severity=WARNING,
                                    message=(
                                        f"Nghi ngờ VẼ LỆCH VỊ TRÍ: Object '{o2.id}' ({o2.category}) "
                                        f"dịch chuyển {dist:.1f}px so với frame trước ({curr_f.name}), "
                                        f"vượt ngưỡng bất thường ({max_dist_px:.1f}px)."
                                    ),
                                )
                            )
        return errors


ALL_SEQUENCE_RULES = [
    RuleT01MissingObjectInSequence(),
    RuleT02DrasticPositionJump(),
]
