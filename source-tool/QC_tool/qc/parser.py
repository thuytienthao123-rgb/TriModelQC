"""
parser.py — Đọc file nhãn BDD100K JSON và chuẩn hóa sang FrameData.
Phụ trách chính: Đoàn Văn Thắng (2A202602327)
"""

from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Any, List, Optional

from qc.models import BBox2D, FrameData, LabeledObject, Polygon2D

logger = logging.getLogger(__name__)


def _parse_box2d(raw: Optional[dict]) -> Optional[BBox2D]:
    """Chuyển dict box2d của BDD100K sang BBox2D."""
    if not raw:
        return None
    try:
        return BBox2D(
            x1=float(raw["x1"]),
            y1=float(raw["y1"]),
            x2=float(raw["x2"]),
            y2=float(raw["y2"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        logger.warning("Không thể parse box2d: %s — %s", raw, exc)
        return None


def _parse_poly2d(raw: Optional[list]) -> Optional[Polygon2D]:
    """
    Chuyển mảng poly2d của BDD100K sang Polygon2D.
    BDD100K lưu: [{"vertices": [[x,y], ...], "types": "...", "closed": bool}]
    """
    if not raw:
        return None
    try:
        # Lấy segment đầu tiên
        segment = raw[0]
        vertices_raw = segment.get("vertices", [])
        vertices = [(float(pt[0]), float(pt[1])) for pt in vertices_raw]
        return Polygon2D(vertices=vertices)
    except (IndexError, KeyError, TypeError, ValueError) as exc:
        logger.warning("Không thể parse poly2d: %s — %s", raw, exc)
        return None


def _parse_object(raw: dict, frame_idx: int) -> Optional[LabeledObject]:
    """Chuyển một dict object thô sang LabeledObject."""
    obj_id = str(raw.get("id", f"obj_{frame_idx}_unknown"))
    category = str(raw.get("category", "unknown"))
    box2d = _parse_box2d(raw.get("box2d"))
    poly2d_raw = raw.get("poly2d")
    poly2d = _parse_poly2d(poly2d_raw) if poly2d_raw else None
    attributes = raw.get("attributes", {})
    if attributes is None:
        attributes = {}
    return LabeledObject(
        id=obj_id,
        category=category,
        box2d=box2d,
        poly2d=poly2d,
        attributes=attributes,
    )


def parse_bdd100k_data(raw_data: Any) -> List[FrameData]:
    """Parse parsed JSON object/dict/list sang danh sach FrameData."""
    if isinstance(raw_data, dict):
        frames_raw = raw_data.get("frames", raw_data.get("labels", []))
    elif isinstance(raw_data, list):
        frames_raw = raw_data
    else:
        raise ValueError("Cau truc JSON khong hop le (can list hoac dict).")

    frames: List[FrameData] = []
    for idx, frame_raw in enumerate(frames_raw):
        name = str(frame_raw.get("name", f"frame_{idx:05d}"))
        width = int(frame_raw.get("width", 1280))
        height = int(frame_raw.get("height", 720))

        raw_labels = frame_raw.get("labels", [])
        objects: list = []
        for obj_raw in raw_labels:
            obj = _parse_object(obj_raw, idx)
            if obj is not None:
                objects.append(obj)

        frames.append(FrameData(name=name, width=width, height=height, objects=objects))

    return frames


def parse_bdd100k_text(json_text: str) -> List[FrameData]:
    """Parse chuoi JSON text sang danh sach FrameData."""
    try:
        raw_data = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"File JSON khong hop le: {exc}") from exc
    return parse_bdd100k_data(raw_data)


def load_bdd100k(file_path: str | Path) -> List[FrameData]:
    """
    Đọc file JSON định dạng BDD100K và trả về danh sách FrameData.

    Hỗ trợ hai cấu trúc JSON phổ biến:
      1. Danh sách frame trực tiếp: [{"name": ..., "labels": [...]}]
      2. Dict bọc ngoài:  {"frames": [...]}
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {path}")

    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw_data = json.load(fh)
    except json.JSONDecodeError as exc:
        raise ValueError(f"File JSON không hợp lệ: {path} — {exc}") from exc

    frames = parse_bdd100k_data(raw_data)
    logger.info("Đã load %d frame(s) từ %s", len(frames), path.name)
    return frames

