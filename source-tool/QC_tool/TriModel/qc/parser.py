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
    box2d = _parse_box2d(raw.get("box2d"))
    poly2d_raw = raw.get("poly2d")
    poly2d = _parse_poly2d(poly2d_raw) if poly2d_raw else None

    # Bỏ qua các object rác không có tọa độ hình học
    if box2d is None and poly2d is None:
        return None

    obj_id = str(raw.get("id", f"obj_{frame_idx}_unknown"))
    category = str(raw.get("category", "unknown"))
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
            poly2d = Polygon2D(vertices=[(v[0], v[1]) for v in vertices])

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


def parse_cvat_xml_text(xml_text: str) -> List[FrameData]:
    """Parse CVAT XML format cho cả ảnh đơn (image tag) và video track (track tag)."""
    import xml.etree.ElementTree as ET

    try:
        root = ET.fromstring(xml_text)
    except Exception as exc:
        logger.warning("Không thể parse CVAT XML: %s", exc)
        return []

    frames: List[FrameData] = []

    # 1. Định dạng Image Annotations: <image ...> <box .../> <polygon .../> </image>
    image_nodes = root.findall(".//image")
    if image_nodes:
        for img_node in image_nodes:
            frame_name = img_node.get("name", "frame.jpg")
            w = int(float(img_node.get("width", 1920)))
            h = int(float(img_node.get("height", 1080)))

            objects: List[LabeledObject] = []

            # Đọc box
            for b_idx, box_node in enumerate(img_node.findall("box")):
                box_id = box_node.get("id", f"box_{b_idx}")
                label = box_node.get("label", "unknown")
                xtl = float(box_node.get("xtl", 0))
                ytl = float(box_node.get("ytl", 0))
                xbr = float(box_node.get("xbr", 0))
                ybr = float(box_node.get("ybr", 0))
                occluded = box_node.get("occluded") in ("1", "true", "True")

                attributes = {"occluded": occluded}
                for attr_node in box_node.findall("attribute"):
                    attr_name = attr_node.get("name", "")
                    attr_val = (attr_node.text or "").strip()
                    if attr_val.lower() == "true":
                        attributes[attr_name] = True
                    elif attr_val.lower() == "false":
                        attributes[attr_name] = False
                    else:
                        attributes[attr_name] = attr_val

                objects.append(
                    LabeledObject(
                        id=box_id,
                        category=label,
                        box2d=BBox2D(x1=xtl, y1=ytl, x2=xbr, y2=ybr),
                        attributes=attributes,
                    )
                )

            # Đọc polygon
            for p_idx, poly_node in enumerate(img_node.findall("polygon")):
                poly_id = poly_node.get("id", f"poly_{p_idx}")
                label = poly_node.get("label", "unknown")
                points_str = poly_node.get("points", "")
                vertices: List[List[float]] = []
                for pt in points_str.split(";"):
                    if "," in pt:
                        px, py = pt.split(",")[:2]
                        vertices.append([float(px.strip()), float(py.strip())])
                xs = [v[0] for v in vertices]
                ys = [v[1] for v in vertices]
                box2d = BBox2D(x1=min(xs), y1=min(ys), x2=max(xs), y2=max(ys)) if xs and ys else None
                poly2d = Polygon2D(vertices=[(v[0], v[1]) for v in vertices])

                objects.append(
                    LabeledObject(
                        id=poly_id,
                        category=label,
                        box2d=box2d,
                        poly2d=poly2d,
                        attributes={"occluded": False, "truncated": False},
                    )
                )

            frames.append(FrameData(name=frame_name, width=w, height=h, objects=objects))
        return frames

    # 2. Định dạng Video Track Annotations: <track ...> <box frame="..." outside="0" .../> </track>
    track_nodes = root.findall(".//track")
    if track_nodes:
        orig_w = 1920
        orig_h = 1080
        orig_size = root.find(".//original_size")
        if orig_size is not None:
            w_node = orig_size.find("width")
            h_node = orig_size.find("height")
            if w_node is not None and w_node.text:
                orig_w = int(float(w_node.text))
            if h_node is not None and h_node.text:
                orig_h = int(float(h_node.text))

        frames_by_index: dict = {}
        for track in track_nodes:
            track_id = track.get("id", "track")
            label = track.get("label", "unknown")

            for box_node in track.findall("box"):
                outside = box_node.get("outside", "0")
                if outside in ("1", "true", "True"):
                    continue

                frame_idx = int(box_node.get("frame", 0))
                xtl = float(box_node.get("xtl", 0))
                ytl = float(box_node.get("ytl", 0))
                xbr = float(box_node.get("xbr", 0))
                ybr = float(box_node.get("ybr", 0))
                occluded = box_node.get("occluded") in ("1", "true", "True")

                attributes = {"occluded": occluded}
                for attr_node in box_node.findall("attribute"):
                    attr_name = attr_node.get("name", "")
                    attr_val = (attr_node.text or "").strip()
                    if attr_val.lower() == "true":
                        attributes[attr_name] = True
                    elif attr_val.lower() == "false":
                        attributes[attr_name] = False
                    else:
                        attributes[attr_name] = attr_val

                obj = LabeledObject(
                    id=f"{track_id}_f{frame_idx}",
                    category=label,
                    box2d=BBox2D(x1=xtl, y1=ytl, x2=xbr, y2=ybr),
                    attributes=attributes,
                )
                frames_by_index.setdefault(frame_idx, []).append(obj)

        for f_idx in sorted(frames_by_index.keys()):
            frames.append(
                FrameData(
                    name=f"frame_{f_idx:06d}.jpg",
                    width=orig_w,
                    height=orig_h,
                    objects=frames_by_index[f_idx],
                )
            )

    return frames


