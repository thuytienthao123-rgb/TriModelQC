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


def parse_yolo_text(
    text: str,
    frame_name: str = "frame_0000",
    width: int = 1920,
    height: int = 1080,
    class_names: Optional[List[str]] = None,
) -> FrameData:
    """
    Parse chuỗi text định dạng YOLO (BBox hoặc Polygon Segmentation) sang FrameData.
    Hỗ trợ:
      - YOLO BBox: <class_id> <x_center> <y_center> <width> <height> (chuẩn hóa 0..1)
      - YOLO Polygon: <class_id> <x1> <y1> <x2> <y2> ... (chuẩn hóa 0..1)
    """
    objects: List[LabeledObject] = []
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip() and not ln.strip().startswith("#")]

    for idx, line in enumerate(lines, start=1):
        parts = line.split()
        if len(parts) < 5:
            continue

        try:
            cls_id = int(float(parts[0]))
        except ValueError:
            continue

        if class_names and 0 <= cls_id < len(class_names):
            category = class_names[cls_id]
        else:
            category = f"class_{cls_id}"

        # Trường hợp 1: YOLO Bounding Box (5 giá trị)
        if len(parts) == 5:
            try:
                xc = float(parts[1])
                yc = float(parts[2])
                w = float(parts[3])
                h = float(parts[4])
            except ValueError:
                continue

            x1 = (xc - w / 2.0) * width
            y1 = (yc - h / 2.0) * height
            x2 = (xc + w / 2.0) * width
            y2 = (yc + h / 2.0) * height

            objects.append(
                LabeledObject(
                    id=f"obj_{idx:03d}",
                    category=category,
                    box2d=BBox2D(x1=x1, y1=y1, x2=x2, y2=y2),
                    attributes={"occluded": False, "truncated": False},
                )
            )

        # Trường hợp 2: YOLO Polygon / Segmentation (lẻ, > 5 giá trị)
        elif len(parts) > 5 and len(parts) % 2 == 1:
            try:
                coords = [float(p) for p in parts[1:]]
            except ValueError:
                continue

            vertices = [
                [coords[i] * width, coords[i + 1] * height]
                for i in range(0, len(coords), 2)
            ]
            xs = [v[0] for v in vertices]
            ys = [v[1] for v in vertices]
            box2d = BBox2D(x1=min(xs), y1=min(ys), x2=max(xs), y2=max(ys)) if xs and ys else None
            poly2d = Polygon2D(vertices=vertices, types="cc", closed=True)

            objects.append(
                LabeledObject(
                    id=f"obj_{idx:03d}",
                    category=category,
                    box2d=box2d,
                    poly2d=poly2d,
                    attributes={"occluded": False, "truncated": False},
                )
            )

    return FrameData(
        name=frame_name,
        width=width,
        height=height,
        objects=objects,
    )

