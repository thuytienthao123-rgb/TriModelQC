"""
base.py — Base class cho tất cả các Rule của QC Tool.
Phụ trách chính: Đào Ngọc Hiếu (2A202602081)
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List

from qc.models import FrameData, QCError


class BaseRule(ABC):
    """Mọi Rule đều kế thừa class này và implement phương thức check()."""

    rule_id: str = "RULE_UNDEFINED"
    description: str = "No description"

    @abstractmethod
    def check(self, frame: FrameData) -> List[QCError]:
        """
        Chạy kiểm tra trên một frame.
        Trả về danh sách QCError (rỗng nếu không có lỗi).
        """
        ...

    def __repr__(self) -> str:
        return f"<Rule {self.rule_id}: {self.description}>"
