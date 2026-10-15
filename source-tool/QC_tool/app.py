"""
app.py — Giao diện Web tương tác Streamlit cho BDD-QC Tool (Mã đề: N2-04A).
Hỗ trợ kiểm tra chất lượng Bounding Box & Polygon 2D trên dataset BDD100K & YOLO.
Phiên bản giao diện nâng cấp: Dark Glassmorphism, Bộ lọc Layer linh hoạt, Điều hướng Next/Prev Error Frame.
"""

from __future__ import annotations
import json
import os
import re
import time
from pathlib import Path
import logging
from typing import List, Dict, Any, Optional, Tuple

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image

from qc.models import (
    ERROR,
    WARNING,
    FrameData,
    QCError,
    QCReport,
    BBox2D,
    Polygon2D,
    LabeledObject,
)
from qc.parser import parse_bdd100k_text, load_bdd100k, parse_yolo_text
from qc.engine import run_qc, DEFAULT_RULES
from qc.rules.bbox_rules import ALL_BBOX_RULES
from qc.rules.polygon_rules import ALL_POLYGON_RULES
from qc.rules.attribute_rules import ALL_ATTRIBUTE_RULES
from qc.rules.sequence_rules import ALL_SEQUENCE_RULES
from qc.reporter import generate_csv_str, generate_html_str

logger = logging.getLogger("QC_App")

# ---------------------------------------------------------------------------
# Hướng dẫn khắc phục chi tiết theo từng mã Rule
# ---------------------------------------------------------------------------
RULE_SUGGESTIONS: Dict[str, str] = {
    "RULE_B01": "Thu nhỏ hoặc kéo BBox về trong phạm vi khung hình (x ≥ 0, y ≥ 0, x ≤ W, y ≤ H).",
    "RULE_B02": "Đảo lại tọa độ sao cho x2 > x1 và y2 > y1; kiểm tra kích thước không được bằng 0.",
    "RULE_B03": "Box quá nhỏ (< 64px²). Nếu là vật thể thật hãy giữ lại; nếu là chấm nhầm/nhiễu hãy xóa bỏ.",
    "RULE_B04": "Tỉ lệ khung hình dị thường (> 25:1). Kiểm tra xem có bị kéo dẹt bất thường không.",
    "RULE_P01": "Polygon cần ít nhất 3 đỉnh để tạo thành mặt phẳng khép kín. Hãy bổ sung thêm đỉnh.",
    "RULE_P02": "Đa giác bị xoắn nơ (tự cắt chính nó). Hãy xóa và vẽ lại đa giác đơn không bắt chéo viền.",
    "RULE_P03": "Khung bao polygon lệch quá nhiều so với BBox (IoU < 0.70). Căn chỉnh lại BBox cho khít với mask.",
    "RULE_A01": "Phát hiện 2 box cùng class vẽ đè lên nhau (> 85% IoU). Hãy xóa bớt 1 box bị vẽ trùng.",
    "RULE_A02": "Thiếu thuộc tính bắt buộc (occluded, truncated). Mở panel thuộc tính và đánh dấu giá trị thật.",
    "RULE_A03": "Đèn giao thông bắt buộc khai báo màu sắc (red, yellow, green, none).",
    "RULE_T01": "Vật thể xuất hiện ở frame trước & sau nhưng mất dấu ở frame này. Bổ sung nhãn liên tục.",
    "RULE_T02": "Vị trí box bị nhảy giật bất thường giữa 2 frame liên tiếp (> 35%). Căn chỉnh lại vị trí nội suy.",
    "RULE_AI01": "AI nghi ngờ có xe/người trong ảnh nhưng chưa được gán nhãn. Kiểm tra lại ảnh gốc để bổ sung.",
}

# ---------------------------------------------------------------------------
# Hỗ trợ đọc đa định dạng (JSON BDD100K & TXT YOLO)
# ---------------------------------------------------------------------------
SUPPORTED_EXTS = [".json", ".txt", ".xml"]

LOCAL_IMAGE_DIRS = [
    Path(__file__).parent / "data_sample" / "images",
    Path(__file__).parent / "images",
    Path(__file__).parent / "data",
    Path("images"),
    Path("data"),
]


def _find_matching_image(frame_name: str, image_map: Dict[str, Any]) -> Optional[Any]:
    """Tìm ảnh tương ứng với frame_name trong ảnh đã upload hoặc thư mục cục bộ."""
    stem = Path(frame_name).stem
    stem_lower = stem.lower()

    if image_map:
        if frame_name in image_map:
            return image_map[frame_name]
        if stem in image_map:
            return image_map[stem]
        for k, v in image_map.items():
            if k.lower() == stem_lower or Path(k).stem.lower() == stem_lower:
                return v
        m = re.search(r'(\d{3,5})', stem)
        if m:
            num = m.group(1)
            for k, v in image_map.items():
                if num in k:
                    return v

    for d in LOCAL_IMAGE_DIRS:
        if not d.exists():
            continue
        for ext in [".jpg", ".jpeg", ".png", ".webp"]:
            cand = d / f"{stem}{ext}"
            if cand.exists():
                return str(cand)
            m = re.search(r'(\d{3,5})', stem)
            if m:
                pattern = f"*{m.group(1)}*{ext}"
                matches = list(d.glob(pattern))
                if matches:
                    return str(matches[0])

    return None


def _load_image(img_ref: Any) -> Optional[Image.Image]:
    """Mở ảnh an toàn từ chuỗi đường dẫn, Path, hoặc UploadedFile Streamlit."""
    if img_ref is None:
        return None
    try:
        if isinstance(img_ref, (str, Path)):
            p = Path(img_ref)
            if p.exists():
                return Image.open(p).convert("RGB")
        elif hasattr(img_ref, "seek"):
            img_ref.seek(0)
            img = Image.open(img_ref).convert("RGB")
            img_ref.seek(0)
            return img
    except Exception as ex:
        logger.warning("Không thể load ảnh: %s", ex)
    return None


def _read_file_bytes(
    file_bytes: bytes,
    filename: str,
    width: int = 1920,
    height: int = 1080,
    class_names: Optional[List[str]] = None,
) -> Optional[List[FrameData]]:
    """Parse bytes từ một file upload thành List[FrameData]."""
    name = filename.lower()
    try:
        text = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = file_bytes.decode("latin-1")
        except Exception:
            return None

    if name.endswith(".json"):
        try:
            return parse_bdd100k_text(text)
        except Exception:
            pass

    if name.endswith(".txt"):
        try:
            return parse_bdd100k_text(text)
        except Exception:
            pass

        try:
            stem = Path(filename).stem
            frame_name = stem if stem.lower().endswith((".jpg", ".png", ".jpeg")) else f"{stem}.jpg"
            frame_data = parse_yolo_text(
                text=text,
                frame_name=frame_name,
                width=width,
                height=height,
                class_names=class_names,
            )
            return [frame_data]
        except Exception:
            return None

    if name.endswith(".xml"):
        m = re.search(r'\[.*\]', text, re.DOTALL)
        if m:
            try:
                return parse_bdd100k_text(m.group(0))
            except Exception:
                pass
        return None

    return None


def _scan_folder(
    folder_path: str,
    default_w: int = 1920,
    default_h: int = 1080,
) -> Tuple[List[Tuple[str, List[FrameData]]], Optional[List[str]]]:
    """Quét folder, tự động nhận diện classes.txt, file JSON và file TXT YOLO."""
    results: List[Tuple[str, List[FrameData]]] = []
    p = Path(folder_path)
    if not p.is_dir():
        return results, None

    detected_classes = None
    for cf in ["classes.txt", "names.txt", "obj.names"]:
        cf_path = p / cf
        if cf_path.exists():
            try:
                detected_classes = [l.strip() for l in cf_path.read_text(encoding="utf-8").splitlines() if l.strip()]
                break
            except Exception:
                pass

    for fp in sorted(p.glob("*.json")):
        try:
            frames = load_bdd100k(fp)
            if frames:
                results.append((fp.name, frames))
        except Exception:
            pass

    for fp in sorted(p.glob("*.txt")):
        if fp.name.lower() in ("classes.txt", "names.txt", "obj.names", "requirements.txt"):
            continue
        try:
            w, h = default_w, default_h
            for img_ext in [".jpg", ".jpeg", ".png", ".webp"]:
                cand = fp.with_suffix(img_ext)
                if cand.exists():
                    try:
                        with Image.open(cand) as img_obj:
                            w, h = img_obj.size
                        break
                    except Exception:
                        pass
            raw_bytes = fp.read_bytes()
            frames = _read_file_bytes(raw_bytes, fp.name, width=w, height=h, class_names=detected_classes)
            if frames:
                results.append((fp.name, frames))
        except Exception:
            pass

    return results, detected_classes


# ---------------------------------------------------------------------------
# Trợ lý AI: Tự động soi vật thể BỎ SÓT (False Negative) trong ảnh
# ---------------------------------------------------------------------------
@st.cache_resource
def _load_ai_detector():
    """Nạp model YOLOv8 cục bộ để phát hiện vật thể bị bỏ sót trong ảnh."""
    candidates = [
        Path(__file__).parent / "yolov8n.pt",
        Path("yolov8n.pt"),
    ]
    for p in candidates:
        if p.exists():
            try:
                from ultralytics import YOLO
                m = YOLO(str(p))
                return m
            except Exception as e:
                logger.warning("Lỗi nạp YOLO từ %s: %s", p, e)
    return None


def _detect_missed_objects(
    img_pil: Image.Image,
    user_objects: List[LabeledObject],
    model,
    conf_thresh: float = 0.25,
) -> List[Dict[str, Any]]:
    """Dùng AI quét ảnh và tìm các vật thể xe/người chưa được gán nhãn."""
    if model is None or img_pil is None:
        return []
    TARGET_CLASSES = {"car", "truck", "bus", "motorcycle", "person", "bicycle"}
    try:
        res = model(img_pil, conf=conf_thresh, verbose=False)
        if not res or len(res[0].boxes) == 0:
            return []
        boxes = res[0].boxes
        missed = []
        for b in boxes:
            cls_id = int(b.cls[0])
            cls_name = model.names[cls_id]
            if cls_name.lower() not in TARGET_CLASSES:
                continue
            x1, y1, x2, y2 = b.xyxy[0].tolist()
            conf = float(b.conf[0])
            ai_box = BBox2D(x1, y1, x2, y2)

            has_match = False
            for uobj in user_objects:
                if uobj.box2d is not None and ai_box.iou(uobj.box2d) > 0.15:
                    has_match = True
                    break
            if not has_match:
                missed.append({
                    "category": cls_name,
                    "confidence": conf,
                    "box2d": ai_box,
                })
        return missed
    except Exception as ex:
        logger.warning("Lỗi AI cross-check: %s", ex)
        return []


def auto_correct_frames(frames: List[FrameData]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Tự động sửa các lỗi hình học & thuộc tính cơ bản và xuất ra định dạng BDD100K."""
    fixed_data = []
    changelog = []

    for frame in frames:
        fixed_objs = []
        seen_boxes: List[Tuple[str, BBox2D]] = []

        for obj in frame.objects:
            obj_copy_id = obj.id
            obj_copy_cat = obj.category
            obj_attrs = dict(obj.attributes) if obj.attributes else {}
            fixed_box = None
            fixed_poly = obj.poly2d

            # Fix RULE_A02: Missing attributes
            if "occluded" not in obj_attrs:
                obj_attrs["occluded"] = False
                changelog.append(f"[{frame.name}] {obj.id}: Bổ sung thuộc tính occluded=False")
            if "truncated" not in obj_attrs:
                obj_attrs["truncated"] = False
                changelog.append(f"[{frame.name}] {obj.id}: Bổ sung thuộc tính truncated=False")

            # Fix RULE_A03: Invalid traffic light color
            if obj_copy_cat == "traffic light":
                tl_color = obj_attrs.get("trafficLightColor", "")
                if tl_color not in ["red", "yellow", "green", "none"]:
                    obj_attrs["trafficLightColor"] = "none"
                    changelog.append(f"[{frame.name}] {obj.id}: Đổi màu đèn '{tl_color}' thành 'none'")

            # Fix Box2D
            if obj.box2d:
                bx1, by1, bx2, by2 = obj.box2d.x1, obj.box2d.y1, obj.box2d.x2, obj.box2d.y2

                # Fix RULE_B02: Inverted coordinates
                if bx2 < bx1:
                    bx1, bx2 = bx2, bx1
                    changelog.append(f"[{frame.name}] {obj.id}: Đảo lại x1={bx1:.1f}, x2={bx2:.1f}")
                if by2 < by1:
                    by1, by2 = by2, by1
                    changelog.append(f"[{frame.name}] {obj.id}: Đảo lại y1={by1:.1f}, y2={by2:.1f}")

                # Skip zero-size box (w=0 and h=0)
                if (bx2 - bx1) <= 0 and (by2 - by1) <= 0:
                    changelog.append(f"[{frame.name}] {obj.id}: Đã xóa box rỗng (w=0, h=0)")
                    continue

                # Fix RULE_B01: Out of bounds clamp
                clamped_x1 = max(0.0, min(float(frame.width), bx1))
                clamped_y1 = max(0.0, min(float(frame.height), by1))
                clamped_x2 = max(0.0, min(float(frame.width), bx2))
                clamped_y2 = max(0.0, min(float(frame.height), by2))
                if (clamped_x1 != bx1 or clamped_y1 != by1 or clamped_x2 != bx2 or clamped_y2 != by2):
                    changelog.append(f"[{frame.name}] {obj.id}: Kéo box về khung [{clamped_x1:.1f}, {clamped_y1:.1f}, {clamped_x2:.1f}, {clamped_y2:.1f}]")
                    bx1, by1, bx2, by2 = clamped_x1, clamped_y1, clamped_x2, clamped_y2

                cand_box = BBox2D(bx1, by1, bx2, by2)

                # Fix RULE_A01: Duplicate box
                is_dup = False
                for seen_cat, seen_b in seen_boxes:
                    if seen_cat == obj_copy_cat and cand_box.iou(seen_b) > 0.85:
                        is_dup = True
                        changelog.append(f"[{frame.name}] {obj.id}: Xóa box trùng lặp với object khác (IoU > 0.85)")
                        break
                if is_dup:
                    continue

                seen_boxes.append((obj_copy_cat, cand_box))
                fixed_box = cand_box

            lbl_dict: Dict[str, Any] = {
                "id": obj_copy_id,
                "category": obj_copy_cat,
                "attributes": obj_attrs,
            }
            if fixed_box:
                lbl_dict["box2d"] = {
                    "x1": round(fixed_box.x1, 1),
                    "y1": round(fixed_box.y1, 1),
                    "x2": round(fixed_box.x2, 1),
                    "y2": round(fixed_box.y2, 1),
                }
            if fixed_poly and fixed_poly.vertices:
                lbl_dict["poly2d"] = [{
                    "vertices": [[round(v[0], 1), round(v[1], 1)] for v in fixed_poly.vertices],
                    "types": "cc",
                    "closed": True,
                }]
            fixed_objs.append(lbl_dict)

        fixed_data.append({
            "name": frame.name,
            "width": frame.width,
            "height": frame.height,
            "labels": fixed_objs,
        })

    return fixed_data, changelog


# ---------------------------------------------------------------------------
# Cấu hình giao diện Streamlit & Custom Styling (Dark Glassmorphism Theme)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Scale Nucleus // QA Audit Workspace (N2-04A)",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Chuyển đổi Theme: Scale Nucleus Dark vs Studio Clean Light
# ---------------------------------------------------------------------------
theme_choice = st.sidebar.radio(
    "🎨 Chế độ hiển thị (Theme):",
    options=["🌑 Scale Dark (Tối)", "☀️ Studio Light (Sáng)"],
    index=0,
    horizontal=True,
    help="Chuyển đổi giao diện Sáng / Tối theo nhu cầu làm việc"
)
is_dark = ("Dark" in theme_choice or "Tối" in theme_choice)

# Palette definitions
if is_dark:
    bg_main = "#080c14"
    bg_sidebar = "#0c121e"
    bg_header = "#0f1624"
    bg_card = "#111827"
    bg_card_sub = "#131b2e"
    border_c = "#1e293b"
    border_header = "#00e5ff"
    text_main = "#f8fafc"
    text_sub = "#94a3b8"
    text_muted = "#cbd5e1"
    badge_bg = "#0f1624"
    val_cyan = "#00e5ff"
    val_indigo = "#818cf8"
    val_rose = "#f43f5e"
    val_amber = "#fbbf24"
    val_emerald = "#10b981"
    box_shadow = "0 4px 20px rgba(0, 0, 0, 0.4)"
    badge_err_bg = "rgba(239, 68, 68, 0.2)"
    badge_err_txt = "#fca5a5"
    badge_warn_bg = "rgba(245, 158, 11, 0.2)"
    badge_warn_txt = "#fde68a"
    badge_ok_bg = "rgba(16, 185, 129, 0.2)"
    badge_ok_txt = "#a7f3d0"
    tag_bg = "#0f1624"
else:
    bg_main = "#f8fafc"
    bg_sidebar = "#ffffff"
    bg_header = "#ffffff"
    bg_card = "#ffffff"
    bg_card_sub = "#f1f5f9"
    border_c = "#e2e8f0"
    border_header = "#0284c7"
    text_main = "#0f172a"
    text_sub = "#64748b"
    text_muted = "#334155"
    badge_bg = "#f1f5f9"
    val_cyan = "#0284c7"
    val_indigo = "#4f46e5"
    val_rose = "#dc2626"
    val_amber = "#d97706"
    val_emerald = "#059669"
    box_shadow = "0 2px 10px rgba(0, 0, 0, 0.05)"
    badge_err_bg = "rgba(220, 38, 38, 0.12)"
    badge_err_txt = "#b91c1c"
    badge_warn_bg = "rgba(217, 119, 6, 0.12)"
    badge_warn_txt = "#b45309"
    badge_ok_bg = "rgba(5, 150, 105, 0.12)"
    badge_ok_txt = "#047857"
    tag_bg = "#f1f5f9"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* Dynamic App & Sidebar Background */
.stApp {{
    background-color: {bg_main} !important;
    color: {text_main} !important;
}}
[data-testid="stSidebar"] {{
    background-color: {bg_sidebar} !important;
    border-right: 1px solid {border_c} !important;
}}

body, .stMarkdown, .stText, p, span, label {{
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}}
code, kbd, samp, pre {{
    font-family: 'JetBrains Mono', 'Courier New', monospace !important;
}}

/* Custom Scrollbar */
::-webkit-scrollbar {{ width: 7px; height: 7px; }}
::-webkit-scrollbar-track {{ background: {bg_main}; }}
::-webkit-scrollbar-thumb {{ background: {border_c}; border-radius: 4px; }}

/* Main Header Container */
.qc-header-box {{
    background: {bg_header};
    border: 1px solid {border_c};
    border-radius: 14px;
    padding: 20px 24px;
    margin-bottom: 20px;
    box-shadow: {box_shadow};
    border-left: 4px solid {border_header};
}}
.qc-header-title {{
    font-size: 1.85rem;
    font-weight: 800;
    color: {text_main};
    margin: 0;
    letter-spacing: -0.02em;
    display: flex;
    align-items: center;
    gap: 10px;
}}
.qc-header-sub {{
    font-size: 0.88rem;
    color: {text_muted};
    margin: 6px 0 0 0;
    line-height: 1.5;
}}
.qc-tag-row {{
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
    margin-top: 12px;
}}
.qc-tag {{
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    display: inline-flex;
    align-items: center;
    gap: 6px;
}}
.qc-tag-online {{
    background: rgba(16, 185, 129, 0.15);
    color: {val_emerald};
    border: 1px solid rgba(16, 185, 129, 0.4);
}}
.qc-tag-cyan {{
    background: rgba(0, 229, 255, 0.12);
    color: {val_cyan};
    border: 1px solid rgba(0, 229, 255, 0.35);
}}
.qc-tag-purple {{
    background: rgba(168, 85, 247, 0.15);
    color: {val_indigo};
    border: 1px solid rgba(168, 85, 247, 0.4);
}}

/* Live Status Dot */
.pulse-dot {{
    width: 8px;
    height: 8px;
    background-color: {val_emerald};
    border-radius: 50%;
    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
    animation: pulse-green 2s infinite;
}}
@keyframes pulse-green {{
    0% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }}
    70% {{ transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }}
    100% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }}
}}

/* KPI Card Styles */
.qc-kpi-card {{
    background: {bg_card};
    border: 1px solid {border_c};
    border-radius: 12px;
    padding: 16px 18px;
    box-sizing: border-box;
    width: 100%;
    min-height: 110px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    box-shadow: {box_shadow};
    border-top: 3px solid {border_c};
    transition: transform 0.2s, border-color 0.2s;
}}
.qc-kpi-card:hover {{
    transform: translateY(-2px);
}}
.qc-kpi-cyan {{ border-top-color: {val_cyan}; }}
.qc-kpi-indigo {{ border-top-color: {val_indigo}; }}
.qc-kpi-rose {{ border-top-color: {val_rose}; }}
.qc-kpi-amber {{ border-top-color: {val_amber}; }}
.qc-kpi-emerald {{ border-top-color: {val_emerald}; }}

.qc-kpi-label {{
    font-size: 0.74rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: {text_sub};
    margin-bottom: 4px;
}}
.qc-kpi-val {{
    font-size: 1.85rem;
    font-weight: 800;
    line-height: 1.1;
    margin-bottom: 4px;
}}
.val-cyan {{ color: {val_cyan}; }}
.val-indigo {{ color: {val_indigo}; }}
.val-rose {{ color: {val_rose}; }}
.val-amber {{ color: {val_amber}; }}
.val-emerald {{ color: {val_emerald}; }}

.qc-kpi-sub {{
    font-size: 0.76rem;
    color: {text_sub};
    font-weight: 500;
}}

/* Badges */
.badge-err {{
    background: {badge_err_bg};
    color: {badge_err_txt};
    border: 1px solid rgba(239, 68, 68, 0.4);
    padding: 3px 8px;
    border-radius: 5px;
    font-weight: 700;
    font-size: 0.74rem;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}}
.badge-warn {{
    background: {badge_warn_bg};
    color: {badge_warn_txt};
    border: 1px solid rgba(245, 158, 11, 0.4);
    padding: 3px 8px;
    border-radius: 5px;
    font-weight: 700;
    font-size: 0.74rem;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}}
.badge-ok {{
    background: {badge_ok_bg};
    color: {badge_ok_txt};
    border: 1px solid rgba(16, 185, 129, 0.4);
    padding: 3px 8px;
    border-radius: 5px;
    font-weight: 700;
    font-size: 0.74rem;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}}

/* Sidebar Custom Card */
.sidebar-brand-card {{
    background: {bg_card};
    border: 1px solid {border_c};
    border-radius: 10px;
    padding: 12px 14px;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 10px;
}}
.sidebar-brand-title {{
    font-weight: 800;
    font-size: 1.05rem;
    color: {text_main};
    margin: 0;
}}
.sidebar-brand-sub {{
    font-size: 0.75rem;
    color: {text_sub};
    margin: 0;
}}

/* Team Card in Sidebar */
.team-card {{
    background: {bg_card};
    border: 1px solid {border_c};
    border-radius: 10px;
    padding: 12px 14px;
    margin-top: 14px;
}}
.team-member-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 4px 0;
    font-size: 0.8rem;
    border-bottom: 1px solid {border_c};
}}
.team-member-row:last-child {{
    border-bottom: none;
}}
.team-member-name {{
    color: {text_main};
    font-weight: 600;
}}
.team-member-role {{
    font-size: 0.72rem;
    color: {val_cyan};
    background: rgba(0, 229, 255, 0.1);
    padding: 1px 6px;
    border-radius: 4px;
    font-family: 'JetBrains Mono', monospace;
}}

/* Feature highlight cards on welcome screen */
.feature-card {{
    background: {bg_card};
    border: 1px solid {border_c};
    border-radius: 12px;
    padding: 16px 18px;
    height: 100%;
    box-shadow: {box_shadow};
}}
.feature-title {{
    font-weight: 700;
    font-size: 0.98rem;
    color: {text_main};
    margin-bottom: 6px;
}}
.feature-desc {{
    color: {text_muted};
    font-size: 0.82rem;
    line-height: 1.5;
}}

/* Benchmark Comparison Card */
.benchmark-card {{
    background: {bg_card};
    border: 1px solid {border_c};
    border-radius: 14px;
    padding: 18px 22px;
    margin: 16px 0;
    box-shadow: {box_shadow};
}}
.benchmark-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 14px;
    margin-top: 12px;
}}
.benchmark-item {{
    background: {bg_card_sub};
    border: 1px solid {border_c};
    border-radius: 10px;
    padding: 12px 14px;
}}
.benchmark-label {{
    font-size: 0.75rem;
    color: {text_sub};
    margin-bottom: 4px;
}}
.benchmark-val {{
    font-size: 1.15rem;
    font-weight: 700;
    color: {val_cyan};
}}

/* Interactive Object Inspector Card */
.inspector-card {{
    background: {bg_card};
    border: 1px solid {border_c};
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 12px;
}}
.inspector-metrics-row {{
    display: flex;
    gap: 8px;
    margin-top: 8px;
    flex-wrap: wrap;
}}
.metric-pill {{
    background: {bg_card_sub};
    border: 1px solid {border_c};
    padding: 3px 8px;
    border-radius: 5px;
    font-size: 0.75rem;
    color: {text_muted};
    font-family: 'JetBrains Mono', monospace;
}}
.metric-pill strong {{ color: {text_main}; }}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar: Nguồn dữ liệu & Cấu hình Rule
# ---------------------------------------------------------------------------
st.sidebar.markdown("""
<div class="sidebar-brand-card">
    <div class="sidebar-brand-icon">🛡️</div>
    <div>
        <h3 class="sidebar-brand-title">BDD-QC Suite</h3>
        <p class="sidebar-brand-sub">2D Annotation Quality Control</p>
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.subheader("📂 1. Nguồn Dữ Liệu")

data_source = st.sidebar.radio(
    "Chọn phương thức nạp dữ liệu:",
    options=[
        "⚡ Dùng dữ liệu mẫu (Sample)",
        "📂 Upload nhiều file (JSON / TXT / XML)",
        "🗂️ Quét cả thư mục cục bộ",
    ],
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.subheader("📐 2. Canvas & Ảnh Gốc")

canvas_res = st.sidebar.selectbox(
    "Độ phân giải khung hình (YOLO):",
    options=["1920x1080 (Full HD)", "1280x720 (HD BDD100K)", "2560x1440 (2K)"],
    index=0,
    help="Tọa độ YOLO được chuẩn hóa (0..1), cần kích thước ảnh để tính ra pixel.",
)
default_w = 1920 if "1920" in canvas_res else (1280 if "1280" in canvas_res else 2560)
default_h = 1080 if "1080" in canvas_res else (720 if "720" in canvas_res else 1440)

uploaded_images_raw = st.sidebar.file_uploader(
    "Tải ảnh minh họa gốc (Tùy chọn):",
    type=["jpg", "jpeg", "png", "webp", "bmp"],
    accept_multiple_files=True,
    help="Upload ảnh gốc tương ứng với frame để hiển thị viền lỗi trên ảnh thật.",
)
uploaded_image_map: Dict[str, Any] = {}
if uploaded_images_raw:
    for _img_f in uploaded_images_raw:
        uploaded_image_map[_img_f.name] = _img_f
        uploaded_image_map[Path(_img_f.name).stem] = _img_f
    st.sidebar.success(f"✅ Đã nạp **{len(uploaded_images_raw)} ảnh** minh họa")

all_sources: List[Tuple[str, List[FrameData]]] = []
file_display_name = "batch"

if data_source == "⚡ Dùng dữ liệu mẫu (Sample)":
    sample_choice = st.sidebar.selectbox(
        "Chọn tệp dữ liệu mẫu:",
        options=[
            "🔴 sample_with_errors.json (7 vi phạm kỹ thuật)",
            "🟢 sample_valid.json (Bộ nhãn 100% chuẩn quy cách)",
        ],
        index=0,
    )
    sel_file = "sample_valid.json" if "sample_valid" in sample_choice else "sample_with_errors.json"
    sample_file_path = Path(__file__).parent / "data_sample" / sel_file

    if sample_file_path.exists():
        try:
            frames_sample = load_bdd100k(sample_file_path)
            all_sources.append((sel_file, frames_sample))
            file_display_name = sample_file_path.stem
            st.sidebar.success(f"✅ Đã nạp `{sel_file}` ({len(frames_sample)} frames)")
        except Exception as ex:
            st.sidebar.error(f"Lỗi đọc file mẫu: {ex}")
    else:
        st.sidebar.error(f"Không tìm thấy file mẫu: {sel_file}")

elif data_source == "📂 Upload nhiều file (JSON / TXT / XML)":
    st.sidebar.caption("Hỗ trợ chọn nhiều file cùng lúc: `.json`, `.txt` (BDD100K hoặc YOLO), `.xml`")
    uploaded_files = st.sidebar.file_uploader(
        "Chọn file nhãn:",
        type=["json", "txt", "xml"],
        accept_multiple_files=True,
        help="Giữ Ctrl hoặc Cmd để chọn nhiều file cùng lúc.",
    )
    if uploaded_files:
        custom_classes: Optional[List[str]] = None
        for uf in uploaded_files:
            if uf.name.lower() in ("classes.txt", "names.txt", "obj.names"):
                try:
                    custom_classes = [l.strip() for l in uf.getvalue().decode("utf-8").splitlines() if l.strip()]
                    st.sidebar.info(f"🏷️ Nhận diện classes: {', '.join(custom_classes[:5])}")
                except Exception:
                    pass

        ok_count = 0
        fail_names = []
        for uf in uploaded_files:
            if uf.name.lower() in ("classes.txt", "names.txt", "obj.names"):
                continue

            cur_w, cur_h = default_w, default_h
            matched_img = _find_matching_image(uf.name, uploaded_image_map)
            if matched_img:
                try:
                    with Image.open(matched_img) as _tmp_img:
                        cur_w, cur_h = _tmp_img.size
                except Exception:
                    pass

            frames_parsed = _read_file_bytes(
                uf.getvalue(),
                uf.name,
                width=cur_w,
                height=cur_h,
                class_names=custom_classes,
            )
            if frames_parsed:
                all_sources.append((uf.name, frames_parsed))
                ok_count += 1
            else:
                fail_names.append(uf.name)

        if ok_count:
            st.sidebar.success(f"✅ Đã nạp thành công **{ok_count}/{len(uploaded_files)} file**")
            file_display_name = "_".join(Path(f.name).stem for f in uploaded_files[:3])
        if fail_names:
            st.sidebar.warning(f"⚠️ Không đọc được: {', '.join(fail_names)}")

else:  # Quét thư mục
    st.sidebar.caption("Nhập đường dẫn thư mục chứa file nhãn.")
    folder_input = st.sidebar.text_input(
        "Đường dẫn thư mục:",
        placeholder=r"Ví dụ: C:\Users\...\Video_3",
    )
    scan_btn = st.sidebar.button("🔍 Quét thư mục", use_container_width=True)
    if scan_btn and folder_input:
        with st.sidebar:
            with st.spinner("Đang quét..."):
                folder_sources, folder_classes = _scan_folder(
                    folder_input.strip(),
                    default_w=default_w,
                    default_h=default_h,
                )
        if folder_sources:
            all_sources = folder_sources
            file_display_name = Path(folder_input.strip()).name
            total_frames_found = sum(len(frs) for _, frs in folder_sources)
            st.sidebar.success(
                f"✅ Tìm thấy **{len(folder_sources)} file** · "
                f"**{total_frames_found} frames** trong `{Path(folder_input.strip()).name}/`"
            )
            if folder_classes:
                st.sidebar.info(f"🏷️ Classes: {', '.join(folder_classes[:5])}")
        else:
            st.sidebar.warning("Không tìm thấy file nhãn hợp lệ trong thư mục này.")
    elif scan_btn:
        st.sidebar.warning("Vui lòng nhập đường dẫn thư mục.")

    if all_sources:
        with st.sidebar.expander(f"📄 {len(all_sources)} file tìm thấy", expanded=False):
            for fname, frs in all_sources:
                st.caption(f"• **{fname}** — {len(frs)} frames")

# 2. Bộ lọc Rules
st.sidebar.markdown("---")
st.sidebar.subheader("🎯 3. Bộ Luật Kiểm Tra")

enable_bbox = st.sidebar.checkbox("Kiểm tra Bounding Box (B01 - B04)", value=True)
enable_poly = st.sidebar.checkbox("Kiểm tra Polygon (P01 - P03)", value=True)
enable_attr = st.sidebar.checkbox("Kiểm tra Thuộc tính & Trùng (A01 - A03)", value=True)
enable_seq = st.sidebar.checkbox("Kiểm tra Chuỗi Video (T01 - T02)", value=True)

active_rules = []
if enable_bbox:
    active_rules.extend(ALL_BBOX_RULES)
if enable_poly:
    active_rules.extend(ALL_POLYGON_RULES)
if enable_attr:
    active_rules.extend(ALL_ATTRIBUTE_RULES)

active_seq_rules = ALL_SEQUENCE_RULES if enable_seq else []
total_rules_active = len(active_rules) + len(active_seq_rules)

st.sidebar.info(f"Đang kích hoạt: **{total_rules_active} / 12 rules**")

# Tích hợp AI Detector
ai_model = _load_ai_detector()
enable_ai_check = False
ai_conf = 0.35

if ai_model is not None:
    st.sidebar.markdown("---")
    st.sidebar.subheader("🤖 4. Trợ Lý AI Soi Bỏ Sót")
    enable_ai_check = st.sidebar.checkbox(
        "Bật AI soi xe/người BỎ SÓT",
        value=True,
        help="Dùng YOLOv8 quét ảnh và khoanh vùng các vật thể bạn chưa gán nhãn.",
    )
    if enable_ai_check:
        ai_conf = st.sidebar.slider("Độ nhạy AI (Confidence):", 0.20, 0.70, 0.35, 0.05)

# Nút RUN và RESET trên Sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("🚀 5. Điều Khiển QC")
btn_col1, btn_col2 = st.sidebar.columns([3, 2])
run_btn = btn_col1.button(
    "🚀 Checking",
    use_container_width=True,
    type="primary",
    disabled=not all_sources,
    help="Bắt đầu chạy kiểm tra QC trên các file đã nạp",
)
reset_btn = btn_col2.button(
    "🔄 Reload",
    use_container_width=True,
    help="Tải lại / Xóa cache kết quả kiểm tra",
)

# Quản lý Session State
if "qc_report" not in st.session_state:
    st.session_state["qc_report"] = None
    st.session_state["qc_frames"] = None
    st.session_state["qc_sources"] = None
    st.session_state["qc_rules_snapshot"] = None
    st.session_state["qc_display_name"] = ""
    st.session_state["active_frame_name"] = ""

if reset_btn:
    st.session_state["qc_report"] = None
    st.session_state["qc_frames"] = None
    st.session_state["qc_sources"] = None
    st.session_state["qc_rules_snapshot"] = None
    st.session_state["qc_display_name"] = ""
    st.session_state["active_frame_name"] = ""
    st.rerun()

st.sidebar.markdown("""
<div class="team-card">
    <div style="font-size: 0.76rem; color: #94a3b8; font-weight: 700; text-transform: uppercase; margin-bottom: 6px;">👥 Đội Ngũ Thực Hiện (N2-04A)</div>
    <div class="team-member-row"><span class="team-member-name">Đào Ngọc Hiếu</span><span class="team-member-role">Leader</span></div>
    <div class="team-member-row"><span class="team-member-name">Đoàn Văn Thắng</span><span class="team-member-role">Data Eng</span></div>
    <div class="team-member-row"><span class="team-member-name">Nguyễn Thanh Đức</span><span class="team-member-role">BBox QC</span></div>
    <div class="team-member-row"><span class="team-member-name">Hoàng Công Chứ</span><span class="team-member-role">Poly QC</span></div>
    <div class="team-member-row"><span class="team-member-name">Trần Thị Thủy Tiên</span><span class="team-member-role">Attr QC</span></div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main Content: Header with Live Status & Tags
# ---------------------------------------------------------------------------
ai_status_tag = '<span class="qc-tag qc-tag-online">🤖 AI YOLOv8 Sẵn Sàng</span>' if (ai_model and enable_ai_check) else '<span class="qc-tag" style="background: rgba(148,163,184,0.15); color: #cbd5e1; border: 1px solid #334155;">🤖 AI Offline</span>'

ai_status_tag = '<span class="qc-tag qc-tag-online">● YOLOv8 AI ACTIVE</span>' if (ai_model and enable_ai_check) else '<span class="qc-tag" style="background: rgba(148,163,184,0.12); color: #cbd5e1; border: 1px solid #334155;">○ AI OFFLINE</span>'

st.markdown(f"""
<div class="qc-header-box">
    <div style="display: flex; align-items: flex-start; justify-content: space-between; flex-wrap: wrap; gap: 14px;">
        <div>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #00e5ff; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 3px;">
                SCALE NUCLEUS // QA AUDIT SUITE
            </div>
            <h1 class="qc-header-title">
                BDD100K <span style="color: #00e5ff; font-weight: 400;">QUALITY CONTROL WORKSPACE</span>
                <span style="font-size: 0.8rem; background: rgba(0, 229, 255, 0.12); color: #00e5ff; border: 1px solid rgba(0, 229, 255, 0.35); padding: 2px 8px; border-radius: 4px; font-weight: 600; vertical-align: middle;">v2.6 PRO</span>
            </h1>
            <p class="qc-header-sub">Automated Spatial Linter, Polygon Topology Audit & Defect Remediation Engine · Project N2-04A</p>
        </div>
        <div class="qc-tag-row">
            <div class="qc-tag qc-tag-online">
                <span class="pulse-dot"></span>
                <span>AUDIT RUNTIME ONLINE</span>
            </div>
            <span class="qc-tag qc-tag-cyan">SPEC: BDD100K / N2-04A</span>
            <span class="qc-tag qc-tag-purple">{total_rules_active} RULES LOADED</span>
            {ai_status_tag}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

if not all_sources:
    st.info(
        "👈 Vui lòng chọn nguồn dữ liệu ở thanh bên trái để bắt đầu kiểm tra.\n\n"
        "**Tính năng hỗ trợ:**\n"
        "- **Upload nhiều file cùng lúc:** Giữ `Ctrl` hoặc `Cmd` để chọn nhiều file `.json` hoặc `.txt` (YOLO).\n"
        "- **Đa định dạng:** Tự động phát hiện JSON BDD100K và text YOLO (`class xc yc w h`).\n"
        "- **Kèm file nhãn:** Tải kèm `classes.txt` để tự động ánh xạ class name thật.\n"
        "- **Ảnh minh họa:** Tải kèm các ảnh `.jpg` / `.png` để soi lỗi trực quan trên canvas."
    )
    st.stop()


# Helper thực thi QC
def _execute_qc():
    all_frames_run: List[FrameData] = []
    for _src_name, _src_frames in all_sources:
        all_frames_run.extend(_src_frames)

    with st.spinner("⏳ Đang quét linter 12 rules và đối soát AI YOLOv8... Vui lòng chờ giây lát."):
        _t0 = time.time()
        _report = run_qc(
            all_frames_run,
            rules=active_rules,
            sequence_rules=active_seq_rules,
        )

        # Quét AI phát hiện vật thể bỏ sót (RULE_AI01)
        if enable_ai_check and ai_model is not None:
            for frame in all_frames_run:
                img_ref = _find_matching_image(frame.name, uploaded_image_map)
                if img_ref is not None:
                    img_obj = _load_image(img_ref)
                    if img_obj is not None:
                        missed_list = _detect_missed_objects(
                            img_obj,
                            frame.objects,
                            ai_model,
                            conf_thresh=ai_conf,
                        )
                        for m_idx, m_obj in enumerate(missed_list, 1):
                            mbx = m_obj["box2d"]
                            m_cat = m_obj["category"]
                            m_conf = m_obj["confidence"]
                            _report.add(QCError(
                                rule_id="RULE_AI01",
                                severity="ERROR" if m_conf >= 0.60 else "WARNING",
                                frame_name=frame.name,
                                object_id=f"ai_missed_{m_idx:02d}",
                                category=m_cat,
                                message=f"AI phát hiện [{m_cat}] bị bỏ sót tại [{int(mbx.x1)}, {int(mbx.y1)}, {int(mbx.x2)}, {int(mbx.y2)}] (độ tin cậy: {m_conf:.0%})",
                            ))

        _elapsed = time.time() - _t0

    st.session_state["qc_report"] = _report
    st.session_state["qc_frames"] = all_frames_run
    st.session_state["qc_sources"] = all_sources
    st.session_state["qc_rules_snapshot"] = active_rules
    st.session_state["qc_display_name"] = file_display_name
    st.toast(f"✅ Hoàn thành quét QC trong {_elapsed:.2f}s — phát hiện {len(_report.errors)} vấn đề", icon="🛡️")


if run_btn:
    _execute_qc()

# Lấy kết quả từ session
report = st.session_state.get("qc_report")
frames = st.session_state.get("qc_frames")
file_display_name_final = st.session_state.get("qc_display_name", file_display_name)
cached_sources = st.session_state.get("qc_sources", all_sources)

# ---------------------------------------------------------------------------
# Trang Chờ (Khi chưa bấm Checking)
# ---------------------------------------------------------------------------
if report is None:
    n_files = len(all_sources)
    n_frames = sum(len(frs) for _, frs in all_sources)
    n_imgs = len(uploaded_image_map) // 2 if uploaded_image_map else 0

    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.5) 0%, rgba(15, 23, 42, 0.7) 100%); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; padding: 26px; margin-bottom: 24px; box-shadow: 0 10px 30px -10px rgba(0,0,0,0.5);">
        <h3 style="margin-top:0; color: #f8fafc; font-size: 1.35rem; display: flex; align-items: center; gap: 10px;">📋 Sẵn sàng kiểm tra chất lượng dữ liệu nhãn</h3>
        <p style="color: #94a3b8; font-size: 0.92rem; line-height: 1.6;">Hệ thống đã nhận diện cấu trúc file thành công. Nhấn nút <strong>BẮT ĐẦU KIỂM TRA</strong> để chạy quét tự động qua 12 rules toán học và đối soát AI YOLOv8.</p>
    </div>
    """, unsafe_allow_html=True)

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("📄 File nhãn đã nạp", f"{n_files} file")
    r2.metric("🎬 Frames phát hiện", f"{n_frames} frame")
    r3.metric("🖼️ Ảnh minh họa gốc", f"{n_imgs} ảnh")
    r4.metric("⚙️ Rules kích hoạt", f"{total_rules_active} / 12")

    st.markdown("<br>", unsafe_allow_html=True)
    c_btn1, c_btn2, _ = st.columns([3.5, 2, 4.5])
    with c_btn1:
        if st.button("🚀 BẮT ĐẦU KIỂM TRA (CHECKING)", type="primary", use_container_width=True):
            _execute_qc()
            st.rerun()
    with c_btn2:
        if st.button("🔄 TẢI LẠI (RELOAD)", use_container_width=True):
            st.session_state["qc_report"] = None
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 🌟 4 Trụ Cột Kiểm Soát Chất Lượng (Quality Pillars):")
    fcol1, fcol2, fcol3, fcol4 = st.columns(4)
    with fcol1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-title">📐 BBox Hình Học</div>
            <div class="feature-desc">Phát hiện box tràn khung hình (B01), box rỗng/diện tích 0 (B02), box quá bé &lt;64px (B03) và tỉ lệ khung hình dị thường &gt;25:1 (B04).</div>
        </div>
        """, unsafe_allow_html=True)
    with fcol2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-title">📉 Polygon Topology</div>
            <div class="feature-desc">Bắt lỗi đa giác ít hơn 3 đỉnh (P01), viền tự cắt chính nó xoắn nơ (P02) và độ lệch Mask vs BBox IoU &lt; 0.70 (P03).</div>
        </div>
        """, unsafe_allow_html=True)
    with fcol3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-title">👥 Thuộc Tính & Trùng</div>
            <div class="feature-desc">Quét box cùng class đè lên nhau IoU &gt; 0.85 (A01), thiếu thuộc tính che khuất/cắt xén (A02) và thiếu màu đèn giao thông (A03).</div>
        </div>
        """, unsafe_allow_html=True)
    with fcol4:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-title">🎬 Video & Trợ Lý AI</div>
            <div class="feature-desc">Kiểm tra tính liên tục chuỗi frame (mất dấu flicker T01, nhảy vị trí giật T02) và AI YOLOv8 đối soát xe/người bị bỏ sót (AI01).</div>
        </div>
        """, unsafe_allow_html=True)

    st.stop()
    raise SystemExit(0)


# ---------------------------------------------------------------------------
# Dashboard Kết quả: Thống kê KPI & Quyết Định Nghiệm Thu
# ---------------------------------------------------------------------------
total_issues = len(report.errors)
pass_rate = 100.0 if report.total_objects == 0 else max(0.0, 100.0 - (total_issues / report.total_objects * 100))

# Thanh thông tin nguồn & nút reload
tcol_info, tcol_reload = st.columns([8, 2])
with tcol_info:
    if len(all_sources) > 1:
        st.caption(
            f"📦 Đang phân tích **{len(all_sources)} file** | "
            + " · ".join(f"`{n}`" for n, _ in all_sources[:5])
            + (f" ... và {len(all_sources)-5} file khác" if len(all_sources) > 5 else "")
        )
    else:
        st.caption("📦 Hoàn tất kiểm tra chất lượng nhãn dữ liệu")
with tcol_reload:
    if st.button("🔄 Reload lại", use_container_width=True, help="Xóa cache và chạy kiểm tra lại"):
        st.session_state["qc_report"] = None
        st.rerun()

# 5 Thẻ KPI Thống Kê Chuẩn Responsive
kcol1, kcol2, kcol3, kcol4, kcol5 = st.columns(5)
with kcol1:
    st.markdown(f"""
    <div class="qc-kpi-card qc-kpi-cyan">
        <div class="qc-kpi-label">🖼️ TOTAL FRAMES</div>
        <div class="qc-kpi-val val-cyan">{report.total_frames:,}</div>
        <div class="qc-kpi-sub">Khung hình phân tích</div>
    </div>
    """, unsafe_allow_html=True)
with kcol2:
    st.markdown(f"""
    <div class="qc-kpi-card qc-kpi-indigo">
        <div class="qc-kpi-label">🎯 GROUND TRUTH OBJECTS</div>
        <div class="qc-kpi-val val-indigo">{report.total_objects:,}</div>
        <div class="qc-kpi-sub">BBox & Polygon mask</div>
    </div>
    """, unsafe_allow_html=True)
with kcol3:
    st.markdown(f"""
    <div class="qc-kpi-card qc-kpi-rose">
        <div class="qc-kpi-label">🔴 BLOCKING DEFECTS</div>
        <div class="qc-kpi-val val-rose">{report.error_count():,}</div>
        <div class="qc-kpi-sub">{'Bắt buộc sửa (Reject)' if report.error_count() > 0 else 'Hoàn toàn sạch lỗi'}</div>
    </div>
    """, unsafe_allow_html=True)
with kcol4:
    st.markdown(f"""
    <div class="qc-kpi-card qc-kpi-amber">
        <div class="qc-kpi-label">🟡 AUDIT WARNINGS</div>
        <div class="qc-kpi-val val-amber">{report.warning_count():,}</div>
        <div class="qc-kpi-sub">Cần annotator rà soát</div>
    </div>
    """, unsafe_allow_html=True)
with kcol5:
    st.markdown(f"""
    <div class="qc-kpi-card qc-kpi-emerald">
        <div class="qc-kpi-label">🛡️ HEALTH SCORE</div>
        <div class="qc-kpi-val val-emerald">{pass_rate:.1f}%</div>
        <div class="qc-kpi-sub">{'🎉 Đạt chuẩn (≥90%)' if pass_rate >= 90 else '⚠️ Chưa đạt (<90%)'}</div>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Thẻ Quyết Định Nghiệm Thu Chính Thức (Official QC Review Verdict)
# ---------------------------------------------------------------------------
err_n = report.error_count()
warn_n = report.warning_count()

if err_n > 0:
    verdict_badge = "🔴 TỪ CHỐI NGHIỆM THU (REJECTED)"
    verdict_color = "#ef4444"
    verdict_bg = "rgba(239, 68, 68, 0.12)"
    verdict_border = "rgba(239, 68, 68, 0.5)"
    verdict_desc = f"Phát hiện <strong>{err_n} lỗi kỹ thuật nghiêm trọng</strong> (ERROR). Bộ nhãn không đủ tiêu chuẩn để huấn luyện mô hình. Bắt buộc Annotator phải sửa chữa và nộp lại theo danh sách vi phạm bên dưới."
elif warn_n > 0:
    verdict_badge = "🟡 NGHIỆM THU CÓ ĐIỀU KIỆN (CONDITIONAL PASS)"
    verdict_color = "#f59e0b"
    verdict_bg = "rgba(245, 158, 11, 0.12)"
    verdict_border = "rgba(245, 158, 11, 0.5)"
    verdict_desc = f"Không có lỗi nghiêm trọng (0 Error), nhưng có <strong>{warn_n} cảnh báo</strong> (WARNING) cần Reviewer/Lead xác nhận ngoại lệ trước khi đưa vào pipeline chính thức."
else:
    verdict_badge = "🟢 PHÊ DUYỆT NGHIỆM THU (PASSED & APPROVED)"
    verdict_color = "#10b981"
    verdict_bg = "rgba(16, 185, 129, 0.12)"
    verdict_border = "rgba(16, 185, 129, 0.5)"
    verdict_desc = "Tất cả các nhãn kiểm tra đều thỏa mãn <strong>100% tiêu chuẩn kỹ thuật</strong> (0 Error, 0 Warning). Bộ dữ liệu hoàn hảo, sẵn sàng cho công đoạn huấn luyện mô hình Autonomous Driving."

st.markdown(f"""
<div style="background: {verdict_bg}; border: 1.5px solid {verdict_border}; border-radius: 12px; padding: 18px 24px; margin: 18px 0 24px 0; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 14px;">
    <div>
        <div style="font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.08em; color: #94a3b8; font-weight: 700; margin-bottom: 4px;">SCALE NUCLEUS // OFFICIAL QUALITY VERDICT</div>
        <div style="font-size: 1.3rem; font-weight: 800; color: {verdict_color};">{verdict_badge}</div>
        <div style="color: #f1f5f9; font-size: 0.9rem; margin-top: 6px; line-height: 1.5;">{verdict_desc}</div>
    </div>
    <div style="text-align: right; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: #cbd5e1; background: #0b0f19; padding: 10px 16px; border-radius: 8px; border: 1px solid #1f2937;">
        <div>Quy chuẩn: <strong style="color: #f8fafc;">N2-04A / BDD100K</strong></div>
        <div style="margin-top: 4px;">Tỷ lệ đạt: <strong style="color: {verdict_color}; font-size: 1.1rem;">{pass_rate:.1f}%</strong></div>
    </div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Tabs hiển thị kết quả
# ---------------------------------------------------------------------------
tab_list, tab_visual, tab_charts, tab_docs = st.tabs([
    f"📋 Defect Catalog ({total_issues})",
    "🖼️ Nucleus Split-Workspace",
    "📊 Quality Telemetry & KPI",
    "📖 Rule Specification",
])


# ---------------------------------------------------------------------------
# TAB 1: Danh sách lỗi phát hiện & Báo cáo
# ---------------------------------------------------------------------------
with tab_list:
    st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; flex-wrap: wrap; gap: 10px;">
        <div>
            <h3 style="margin: 0; color: #f8fafc; font-size: 1.25rem;">Danh Sách Vi Phạm Phát Hiện</h3>
            <p style="margin: 2px 0 0 0; color: #94a3b8; font-size: 0.85rem;">Chi tiết từng đối tượng lỗi kèm hướng dẫn khắc phục cụ thể cho Annotator</p>
        </div>
        <div style="display: flex; gap: 8px;">
            <span class="badge-err">🔴 {report.error_count()} ERRORs</span>
            <span class="badge-warn">🟡 {report.warning_count()} WARNINGs</span>
            <span class="badge-ok">📦 {total_issues} Tổng số</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if total_issues == 0:
        st.success("🎉 Xuất sắc! Dữ liệu nhãn hoàn toàn sạch sẽ, không có lỗi hay cảnh báo nào.")
    else:
        records = []
        for e in report.errors:
            records.append({
                "Frame": e.frame_name,
                "Object ID": e.object_id,
                "Class": e.category,
                "Rule": e.rule_id,
                "Mức độ": e.severity,
                "Chi tiết lỗi": e.message,
                "💡 Gợi ý khắc phục": RULE_SUGGESTIONS.get(e.rule_id, "Kiểm tra và sửa theo quy chuẩn BDD100K."),
            })
        df_errors = pd.DataFrame(records)

        # Bộ lọc tương tác (Mức độ, Rule, Class, Tìm kiếm)
        fcol1, fcol2, fcol3, fcol4 = st.columns([2, 2.2, 2.2, 3.6])
        with fcol1:
            severity_filter = st.selectbox("Lọc mức độ:", options=["Tất cả", "ERROR", "WARNING"], index=0)
        with fcol2:
            rules_available = ["Tất cả"] + sorted(list(df_errors["Rule"].unique()))
            rule_filter = st.selectbox("Lọc theo Rule:", options=rules_available, index=0)
        with fcol3:
            classes_available = ["Tất cả"] + sorted(list(df_errors["Class"].unique()))
            class_filter = st.selectbox("Lọc theo Class:", options=classes_available, index=0)
        with fcol4:
            search_text = st.text_input("🔍 Tìm kiếm nhanh:", "", placeholder="ID, frame, class, mô tả...")

        filtered_df = df_errors.copy()
        if severity_filter != "Tất cả":
            filtered_df = filtered_df[filtered_df["Mức độ"] == severity_filter]
        if rule_filter != "Tất cả":
            filtered_df = filtered_df[filtered_df["Rule"] == rule_filter]
        if class_filter != "Tất cả":
            filtered_df = filtered_df[filtered_df["Class"] == class_filter]
        if search_text:
            s = search_text.lower()
            filtered_df = filtered_df[
                filtered_df["Frame"].str.lower().str.contains(s) |
                filtered_df["Object ID"].str.lower().str.contains(s) |
                filtered_df["Class"].str.lower().str.contains(s) |
                filtered_df["Chi tiết lỗi"].str.lower().str.contains(s)
            ]

        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Mức độ": st.column_config.TextColumn("Mức độ", help="ERROR: Bắt buộc sửa | WARNING: Cần rà soát"),
                "Rule": st.column_config.TextColumn("Mã Rule"),
                "💡 Gợi ý khắc phục": st.column_config.TextColumn("💡 Hướng dẫn sửa", width="large"),
            }
        )

        st.caption(f"Đang hiển thị **{len(filtered_df)} / {total_issues}** vấn đề vi phạm.")

        # Nút xuất báo cáo
        st.markdown("##### 📥 Xuất Báo Cáo Chất Lượng (Export Hub):")
        dcol1, dcol2, _ = st.columns([3, 3, 4])
        with dcol1:
            csv_data = generate_csv_str(report)
            st.download_button(
                label="📄 Tải Báo Cáo CSV (Cho Annotator)",
                data=csv_data,
                file_name=f"qc_report_{Path(file_display_name_final).stem or file_display_name_final}.csv",
                mime="text/csv",
                use_container_width=True,
                help="File CSV có đủ mã lỗi, Object ID để annotator lọc và sửa nhanh trên CVAT / Labelme",
            )
        with dcol2:
            html_data = generate_html_str(report)
            st.download_button(
                label="🌐 Tải Báo Cáo HTML Dashboard",
                data=html_data,
                file_name=f"qc_report_{Path(file_display_name_final).stem or file_display_name_final}.html",
                mime="text/html",
                use_container_width=True,
                help="Báo cáo HTML Dashboard độc lập có tìm kiếm, bộ lọc và in ấn PDF",
            )

        # Xem trước trực tiếp HTML Dashboard ngay trên app
        with st.expander("🌐 Xem trước Báo cáo HTML Trực quan (Interactive Live Preview)", expanded=False):
            components.html(html_data, height=560, scrolling=True)

        # Bộ Công Cụ Tự Động Sửa Lỗi (1-Click Auto-Fix)
        with st.expander("🛠️ Bộ Công Cụ Tự Động Sửa Lỗi (1-Click Auto-Fix & Xuất BDD100K Đã Sửa)", expanded=False):
            st.markdown("""
            **Thuật toán tự động khắc phục các lỗi vi phạm phổ biến (N2-04A):**
            - 📏 **Clamp BBox (B01):** Tự động kéo bounding box bị tràn viền về đúng kích thước khung ảnh.
            - 🔄 **Invert Coords (B02):** Đảo lại tọa độ bị ngược (x1 > x2 hoặc y1 > y2).
            - 🗑️ **Zero-size Box (B02):** Tự động gỡ bỏ các box rỗng (w=0 và h=0).
            - 👥 **Duplicate Box (A01):** Tự động loại bỏ các box trùng lặp cùng category (IoU > 0.85).
            - 🏷️ **Missing Attributes (A02):** Bổ sung thuộc tính mặc định `occluded=False`, `truncated=False`.
            - 🚦 **Traffic Light Color (A03):** Chuẩn hóa giá trị màu đèn sai lệch về `none`.
            """)

            if st.button("✨ Thực Thi Tự Động Sửa Lỗi (Run Auto-Fix Engine)", type="primary", key="btn_run_autofix", use_container_width=True):
                fixed_dataset, changelog = auto_correct_frames(frames)
                st.session_state["auto_fix_done"] = True
                st.session_state["auto_fix_data"] = fixed_dataset
                st.session_state["auto_fix_log"] = changelog
                st.rerun()

            if st.session_state.get("auto_fix_done", False):
                fixed_data = st.session_state.get("auto_fix_data", [])
                logs = st.session_state.get("auto_fix_log", [])
                st.success(f"🎉 Đã tự động xử lý và khắc phục thành công **{len(logs)} vị trí vi phạm**!")

                with st.expander("📝 Nhật ký chi tiết các mục đã sửa (Changelog):", expanded=True):
                    for log_item in logs[:50]:
                        st.markdown(f"- `{log_item}`")
                    if len(logs) > 50:
                        st.caption(f"... và {len(logs) - 50} mục khác.")

                fixed_json_bytes = json.dumps(fixed_data, indent=2, ensure_ascii=False).encode("utf-8")
                st.download_button(
                    label="💾 Tải Về Tệp BDD100K Đã Sửa Lỗi (Cleaned JSON)",
                    data=fixed_json_bytes,
                    file_name=f"bdd100k_cleaned_{file_display_name_final}.json",
                    mime="application/json",
                    use_container_width=True,
                )


# ---------------------------------------------------------------------------
# TAB 2: Visualizer Soi Lỗi Thông Minh (Canvas + Next/Prev Error Frame)
# ---------------------------------------------------------------------------
with tab_visual:
    st.markdown("""
    <div style="margin-bottom: 14px; display: flex; justify-content: space-between; align-items: flex-end; flex-wrap: wrap; gap: 10px;">
        <div>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #00e5ff; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;">SCALE NUCLEUS // SPATIAL WORKSPACE</div>
            <h3 style="margin: 2px 0 0 0; color: #f8fafc; font-size: 1.25rem;">Spatial Defect Inspection & Real-Time Inspector</h3>
        </div>
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; color: #94a3b8; background: #0f1624; padding: 4px 10px; border-radius: 6px; border: 1px solid #1e293b;">
            SPLIT-VIEW: <span style="color: #00e5ff; font-weight: 700;">CANVAS</span> + <span style="color: #818cf8; font-weight: 700;">INSPECTOR</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    frame_names_all = [f.name for f in frames]
    frame_error_map: Dict[str, List[QCError]] = {}
    for err in report.errors:
        frame_error_map.setdefault(err.frame_name, []).append(err)

    error_frame_names = [f.name for f in frames if f.name in frame_error_map and len(frame_error_map[f.name]) > 0]

    if "active_frame_name" not in st.session_state or st.session_state["active_frame_name"] not in frame_names_all:
        st.session_state["active_frame_name"] = error_frame_names[0] if error_frame_names else frame_names_all[0]

    # Split workspace: Left 68% for Canvas, Right 32% for Scale Nucleus Inspector
    col_workspace, col_inspector = st.columns([6.8, 3.2])

    with col_workspace:
        # Navigation Bar above Canvas
        nav_col1, nav_col2, nav_col3 = st.columns([2.5, 5, 2.5])
        with nav_col1:
            prev_disabled = len(error_frame_names) == 0
            if st.button("◀ Prev Defect", use_container_width=True, disabled=prev_disabled, help="Chuyển đến frame bị lỗi gần nhất phía trước"):
                if error_frame_names:
                    curr_f = st.session_state.get("active_frame_name", frame_names_all[0])
                    if curr_f in error_frame_names:
                        e_idx = error_frame_names.index(curr_f)
                        target_frame = error_frame_names[(e_idx - 1) % len(error_frame_names)]
                    else:
                        target_frame = error_frame_names[-1]
                    st.session_state["active_frame_name"] = target_frame
                    st.rerun()

        with nav_col3:
            next_disabled = len(error_frame_names) == 0
            if st.button("Next Defect ▶", use_container_width=True, disabled=next_disabled, help="Chuyển đến frame bị lỗi kế tiếp"):
                if error_frame_names:
                    curr_f = st.session_state.get("active_frame_name", frame_names_all[0])
                    if curr_f in error_frame_names:
                        e_idx = error_frame_names.index(curr_f)
                        target_frame = error_frame_names[(e_idx + 1) % len(error_frame_names)]
                    else:
                        target_frame = error_frame_names[0]
                    st.session_state["active_frame_name"] = target_frame
                    st.rerun()

        with nav_col2:
            def format_frame_label(fname: str) -> str:
                errs = frame_error_map.get(fname, [])
                n_err = sum(1 for e in errs if e.is_error())
                n_warn = sum(1 for e in errs if e.is_warning())
                if n_err > 0 and n_warn > 0:
                    return f"🚨 {fname} (🔴 {n_err} ERR | 🟡 {n_warn} WARN)"
                elif n_err > 0:
                    return f"🚨 {fname} (🔴 {n_err} ERR)"
                elif n_warn > 0:
                    return f"⚠️ {fname} (🟡 {n_warn} WARN)"
                else:
                    return f"🟢 {fname} (VERIFIED)"

            curr_f = st.session_state.get("active_frame_name", frame_names_all[0])
            curr_idx = frame_names_all.index(curr_f) if curr_f in frame_names_all else 0
            selected_frame_name = st.selectbox(
                "Chọn frame:",
                options=frame_names_all,
                index=curr_idx,
                format_func=format_frame_label,
                key="active_frame_selector_scale",
                label_visibility="collapsed",
            )
            st.session_state["active_frame_name"] = selected_frame_name

        selected_frame = next((f for f in frames if f.name == selected_frame_name), None)

        if selected_frame:
            matched_img_file = _find_matching_image(selected_frame_name, uploaded_image_map)
            loaded_img = _load_image(matched_img_file)

            missed_objects: List[Dict[str, Any]] = []
            if enable_ai_check and loaded_img is not None and ai_model is not None:
                missed_objects = _detect_missed_objects(
                    loaded_img,
                    selected_frame.objects,
                    ai_model,
                    conf_thresh=ai_conf,
                )

            cur_frame_errs = frame_error_map.get(selected_frame_name, [])
            n_f_err = sum(1 for e in cur_frame_errs if e.is_error())
            n_f_warn = sum(1 for e in cur_frame_errs if e.is_warning())

            # Scale Nucleus Frame Status Header
            ai_pill = f'<span style="background: rgba(236,72,153,0.15); color: #ec4899; border: 1px solid rgba(236,72,153,0.3); padding: 2px 8px; border-radius: 4px; font-weight: 700; font-size: 0.72rem;">🤖 {len(missed_objects)} AI MISSED</span>' if (enable_ai_check and missed_objects) else ''
            st.markdown(f"""
            <div style="background: #0f1624; border: 1px solid #1e293b; border-radius: 8px; padding: 8px 14px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; color: #f8fafc;">
                    FRAME: <strong style="color: #00e5ff;">{selected_frame_name}</strong>
                    <span style="color: #64748b; margin-left: 8px;">({selected_frame.width}×{selected_frame.height}px)</span>
                </div>
                <div style="display: flex; gap: 6px; align-items: center; flex-wrap: wrap;">
                    <span style="background: rgba(0,229,255,0.12); color: #00e5ff; border: 1px solid rgba(0,229,255,0.3); padding: 2px 8px; border-radius: 4px; font-weight: 700; font-size: 0.72rem;">📦 {len(selected_frame.objects)} INSTANCES</span>
                    <span style="background: rgba(244,63,94,0.12); color: #f43f5e; border: 1px solid rgba(244,63,94,0.3); padding: 2px 8px; border-radius: 4px; font-weight: 700; font-size: 0.72rem;">🔴 {n_f_err} DEFECTS</span>
                    <span style="background: rgba(245,158,11,0.12); color: #fbbf24; border: 1px solid rgba(245,158,11,0.3); padding: 2px 8px; border-radius: 4px; font-weight: 700; font-size: 0.72rem;">🟡 {n_f_warn} WARN</span>
                    {ai_pill}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Matplotlib Canvas styled for Scale Nucleus
            fig, ax = plt.subplots(figsize=(10.5, 6.0), dpi=105)
            fig.patch.set_facecolor(bg_main)
            ax.set_facecolor(bg_header)
            canvas_w = selected_frame.width
            canvas_h = selected_frame.height

            if loaded_img is not None:
                ax.imshow(loaded_img)
                ax.set_xlim(0, loaded_img.width)
                ax.set_ylim(loaded_img.height, 0)
            else:
                ax.set_xlim(0, canvas_w)
                ax.set_ylim(canvas_h, 0)

            obj_err_map: Dict[str, List[QCError]] = {}
            for err in cur_frame_errs:
                for oid in [x.strip() for x in err.object_id.split("&")]:
                    obj_err_map.setdefault(oid, []).append(err)

            # Layer controls state
            show_err_ly = st.session_state.get("scale_show_err", True)
            show_warn_ly = st.session_state.get("scale_show_warn", True)
            show_valid_ly = st.session_state.get("scale_show_valid", True)
            show_lbl_ly = st.session_state.get("scale_show_labels", True)
            show_grid_ly = st.session_state.get("scale_show_grid", False)
            focus_id = st.session_state.get("scale_focused_obj_id", None)

            for obj in selected_frame.objects:
                obj_errs = obj_err_map.get(obj.id, [])
                has_error = any(e.is_error() for e in obj_errs)
                has_warn = any(e.is_warning() for e in obj_errs)
                is_focused = (focus_id is not None and obj.id == focus_id)

                if is_focused:
                    edge_color = "#00e5ff"
                    status_txt = "🎯 [FOCUS]"
                elif has_error:
                    if not show_err_ly and not is_focused:
                        continue
                    edge_color = "#f43f5e"
                    status_txt = "[ERR]"
                elif has_warn:
                    if not show_warn_ly and not is_focused:
                        continue
                    edge_color = "#fbbf24"
                    status_txt = "[WARN]"
                else:
                    if not show_valid_ly and not is_focused:
                        continue
                    edge_color = "#10b981"
                    status_txt = "[OK]"

                # Render BBox
                if obj.box2d:
                    bx = obj.box2d
                    box_lw = 2.8 if is_focused else (2.0 if (has_error or has_warn) else 1.2)
                    box_ls = "-" if is_focused else ("--" if (has_error or has_warn) else "-")
                    
                    rect = patches.Rectangle(
                        (bx.x1, bx.y1),
                        bx.width,
                        bx.height,
                        linewidth=box_lw,
                        edgecolor=edge_color,
                        facecolor="rgba(0, 229, 255, 0.15)" if is_focused else "none",
                        linestyle=box_ls,
                    )
                    ax.add_patch(rect)

                    if is_focused:
                        cx = (bx.x1 + bx.x2) / 2.0
                        cy = (bx.y1 + bx.y2) / 2.0
                        ax.axvline(cx, color="#00e5ff", linestyle=":", linewidth=1.2, alpha=0.8)
                        ax.axhline(cy, color="#00e5ff", linestyle=":", linewidth=1.2, alpha=0.8)

                    if show_lbl_ly or is_focused:
                        tag = f"{status_txt} {obj.id}: {obj.category}"
                        ax.text(
                            max(5, bx.x1),
                            max(18, bx.y1 - 5),
                            tag,
                            color="#080c14" if is_focused else edge_color,
                            fontsize=9.0 if is_focused else 8.2,
                            weight="bold",
                            bbox=dict(
                                facecolor="#00e5ff" if is_focused else "#080c14",
                                edgecolor=edge_color,
                                boxstyle="round,pad=0.25",
                                alpha=0.92
                            ),
                        )

                # Render Polygon
                if obj.poly2d and obj.poly2d.vertices:
                    pts = obj.poly2d.vertices
                    poly_lw = 2.8 if is_focused else (2.0 if has_error else 1.2)
                    poly_patch = patches.Polygon(
                        pts,
                        closed=True,
                        linewidth=poly_lw,
                        edgecolor=edge_color,
                        facecolor=edge_color,
                        alpha=0.45 if is_focused else 0.22,
                        linestyle="-" if is_focused else (":" if has_error else "-"),
                    )
                    ax.add_patch(poly_patch)

                    if show_lbl_ly or is_focused:
                        ax.text(
                            pts[0][0],
                            pts[0][1],
                            f"{status_txt} {obj.id} (poly)",
                            color="#080c14" if is_focused else edge_color,
                            fontsize=9.0 if is_focused else 8.2,
                            weight="bold",
                            bbox=dict(
                                facecolor="#00e5ff" if is_focused else "#080c14",
                                edgecolor=edge_color,
                                boxstyle="round,pad=0.25",
                                alpha=0.92
                            ),
                        )

            # AI Missed boxes
            if missed_objects:
                for m_idx, m_obj in enumerate(missed_objects, start=1):
                    mbx = m_obj["box2d"]
                    m_cat = m_obj["category"]
                    m_conf = m_obj["confidence"]
                    rect = patches.Rectangle(
                        (mbx.x1, mbx.y1),
                        mbx.width,
                        mbx.height,
                        linewidth=2.2,
                        edgecolor="#ec4899",
                        facecolor="none",
                        linestyle="--",
                    )
                    ax.add_patch(rect)
                    if show_lbl_ly:
                        ax.text(
                            max(5, mbx.x1),
                            max(18, mbx.y1 - 5),
                            f"AI MISSED: {m_cat} ({m_conf:.0%})",
                            color="#ec4899",
                            fontsize=8.0,
                            weight="bold",
                            bbox=dict(facecolor="#080c14", edgecolor="#ec4899", boxstyle="round,pad=0.22", alpha=0.95),
                        )

            if show_grid_ly:
                ax.grid(True, linestyle=":", alpha=0.3, color=border_c)
                ax.set_xticks(range(0, canvas_w + 1, 200))
                ax.set_yticks(range(0, canvas_h + 1, 100))
                ax.tick_params(colors=text_sub, labelsize=7.5)
            else:
                ax.set_xticks([])
                ax.set_yticks([])

            for spine in ax.spines.values():
                spine.set_color(border_c)
            fig.tight_layout()
            st.pyplot(fig)

    # -----------------------------------------------------------------------
    # RIGHT PANE: SCALE NUCLEUS OBJECT INSPECTOR (32% Width)
    # -----------------------------------------------------------------------
    with col_inspector:
        st.markdown("""
        <div style="background: #0f1624; border: 1px solid #1e293b; border-radius: 10px; padding: 14px 16px; margin-bottom: 12px; border-top: 3px solid #00e5ff;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; font-weight: 800; color: #00e5ff; letter-spacing: 0.05em;">
                    🎯 NUCLEUS INSPECTOR
                </div>
                <span style="font-size: 0.7rem; color: #94a3b8; font-family: 'JetBrains Mono', monospace;">REAL-TIME</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if selected_frame:
            obj_lookup = {o.id: o for o in selected_frame.objects}
            cur_frame_errs = frame_error_map.get(selected_frame_name, [])

            # Object Selector
            obj_choices = ["🔍 ALL INSTANCES"] + [f"{o.id} ({o.category})" for o in selected_frame.objects]
            sel_obj_str = st.selectbox(
                "Select Instance to Inspect:",
                options=obj_choices,
                index=0,
                key="scale_inspector_obj_select",
                help="Chọn một đối tượng để kiểm tra chi tiết tọa độ, hình học và thuộc tính",
            )

            chosen_id = sel_obj_str.split()[0] if not sel_obj_str.startswith("🔍") else None
            st.session_state["scale_focused_obj_id"] = chosen_id

            # Case 1: Specific Object Chosen
            if chosen_id and chosen_id in obj_lookup:
                target_obj = obj_lookup[chosen_id]
                obj_errs = [e for e in cur_frame_errs if chosen_id in [x.strip() for x in e.object_id.split("&")]]
                has_e = any(e.is_error() for e in obj_errs)
                has_w = any(e.is_warning() for e in obj_errs)

                if has_e:
                    status_badge = '<span class="badge-err">🔴 DEFECT DETECTED</span>'
                elif has_w:
                    status_badge = '<span class="badge-warn">🟡 AUDIT WARNING</span>'
                else:
                    status_badge = '<span class="badge-ok">🟢 PASS SPEC</span>'

                st.markdown(f"""
                <div style="background: #131b2e; border: 1px solid #1e293b; border-radius: 8px; padding: 12px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <div>
                            <strong style="color: #f8fafc; font-size: 0.95rem;">{target_obj.id}</strong>
                            <span style="color: #00e5ff; font-size: 0.8rem; margin-left: 6px; font-family: 'JetBrains Mono', monospace;">[{target_obj.category}]</span>
                        </div>
                        {status_badge}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Geometry Telemetry
                if target_obj.box2d:
                    bx = target_obj.box2d
                    st.markdown(f"""
                    <div style="background: #0f1624; border: 1px solid #1e293b; border-radius: 8px; padding: 10px 12px; margin-bottom: 10px;">
                        <div style="font-size: 0.72rem; color: #94a3b8; font-weight: 700; text-transform: uppercase; margin-bottom: 6px;">📐 Spatial Geometry</div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; font-size: 0.78rem; font-family: 'JetBrains Mono', monospace;">
                            <div>x1, y1: <strong style="color: #f1f5f9;">{bx.x1:.1f}, {bx.y1:.1f}</strong></div>
                            <div>x2, y2: <strong style="color: #f1f5f9;">{bx.x2:.1f}, {bx.y2:.1f}</strong></div>
                            <div>Dimension: <strong style="color: #f1f5f9;">{bx.width:.1f}×{bx.height:.1f}</strong></div>
                            <div>Aspect W/H: <strong style="color: #00e5ff;">{bx.aspect_ratio:.2f}</strong></div>
                            <div>Area: <strong style="color: #f1f5f9;">{bx.area:.0f} px²</strong></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                # Attributes Telemetry
                attrs = target_obj.attributes or {}
                st.markdown(f"""
                <div style="background: #0f1624; border: 1px solid #1e293b; border-radius: 8px; padding: 10px 12px; margin-bottom: 10px;">
                    <div style="font-size: 0.72rem; color: #94a3b8; font-weight: 700; text-transform: uppercase; margin-bottom: 6px;">🏷️ Attributes Metadata</div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; font-size: 0.78rem; font-family: 'JetBrains Mono', monospace;">
                        <div>occluded: <strong style="color: {'#fbbf24' if attrs.get('occluded') else '#94a3b8'};">{attrs.get('occluded', 'MISSING')}</strong></div>
                        <div>truncated: <strong style="color: {'#fbbf24' if attrs.get('truncated') else '#94a3b8'};">{attrs.get('truncated', 'MISSING')}</strong></div>
                        <div>lightColor: <strong style="color: #00e5ff;">{attrs.get('trafficLightColor', 'none')}</strong></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Active Violations for this Object
                if obj_errs:
                    st.markdown("<div style='font-size: 0.75rem; color: #f43f5e; font-weight: 700; margin: 8px 0 4px 0;'>🚨 ACTIVE VIOLATIONS:</div>", unsafe_allow_html=True)
                    for e in obj_errs:
                        sugg = RULE_SUGGESTIONS.get(e.rule_id, "Check BDD100K specification.")
                        st.markdown(f"""
                        <div style="background: rgba(244,63,94,0.08); border: 1px solid rgba(244,63,94,0.3); border-radius: 6px; padding: 8px 10px; margin-bottom: 6px; font-size: 0.78rem;">
                            <div style="font-weight: 700; color: #f87171; font-family: 'JetBrains Mono', monospace;">{e.rule_id} · {e.severity}</div>
                            <div style="color: #e2e8f0; margin-top: 2px;">{e.message}</div>
                            <div style="color: #00e5ff; margin-top: 4px; font-size: 0.72rem;">💡 <strong>Fix:</strong> {sugg}</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.success("✅ Instance meets all 12 QA validation rules.")

            # Case 2: All Instances Summary
            else:
                st.markdown(f"""
                <div style="background: #131b2e; border: 1px solid #1e293b; border-radius: 8px; padding: 12px; margin-bottom: 10px;">
                    <div style="font-size: 0.74rem; color: #94a3b8; font-weight: 700; text-transform: uppercase;">Frame Telemetry Summary</div>
                    <div style="font-size: 1.1rem; font-weight: 800; color: #f8fafc; margin-top: 4px;">
                        {len(selected_frame.objects)} Instances · {len(cur_frame_errs)} Defect Events
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if cur_frame_errs:
                    st.markdown("<div style='font-size: 0.75rem; color: #f43f5e; font-weight: 700; margin: 8px 0 4px 0;'>DEFECTS IN THIS FRAME:</div>", unsafe_allow_html=True)
                    for e in cur_frame_errs:
                        is_e = e.is_error()
                        badge_c = "#f43f5e" if is_e else "#fbbf24"
                        st.markdown(f"""
                        <div style="background: #0f1624; border-left: 3px solid {badge_c}; border-radius: 0 6px 6px 0; padding: 6px 10px; margin-bottom: 6px; font-size: 0.78rem;">
                            <div style="display: flex; justify-content: space-between;">
                                <strong style="color: #f8fafc;">{e.object_id}</strong>
                                <span style="font-family: 'JetBrains Mono', monospace; color: {badge_c}; font-size: 0.72rem;">{e.rule_id}</span>
                            </div>
                            <div style="color: #94a3b8; font-size: 0.74rem; margin-top: 2px;">{e.message}</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.success("🎉 Khung hình sạch 100%, không phát hiện lỗi nào.")

            # Layer Visibility Toggles at the bottom of Inspector
            st.markdown("---")
            st.markdown("<div style='font-size: 0.72rem; color: #94a3b8; font-weight: 700; text-transform: uppercase; margin-bottom: 6px;'>🎛️ Layer Visibility Controls</div>", unsafe_allow_html=True)
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                st.session_state["scale_show_err"] = st.checkbox("🔴 Defects", value=True)
                st.session_state["scale_show_warn"] = st.checkbox("🟡 Warnings", value=True)
                st.session_state["scale_show_valid"] = st.checkbox("🟢 Valid BBox", value=True)
            with t_col2:
                st.session_state["scale_show_labels"] = st.checkbox("🏷️ Labels & IDs", value=True)
                st.session_state["scale_show_grid"] = st.checkbox("📐 Pixel Grid", value=False)


# ---------------------------------------------------------------------------
with tab_charts:
    st.markdown("""
    <div style="margin-bottom: 16px;">
        <h3 style="margin: 0; color: #f8fafc; font-size: 1.25rem;">📊 Phân Tích Chất Lượng Dữ Liệu & Đo Lường Hiệu Quả</h3>
        <p style="margin: 2px 0 0 0; color: #94a3b8; font-size: 0.85rem;">Đo lường các chỉ số Pilot đề tài N2-04A và tần suất vi phạm theo từng phân nhóm</p>
    </div>
    """, unsafe_allow_html=True)

    # Benchmark Cards comparing with topic requirements
    auto_detect_target = "≥ 90%"
    auto_detect_status = "🎉 ĐẠT CHUẨN" if pass_rate >= 90 else "⚠️ CẦN RÀ SOÁT"
    auto_detect_color = "#34d399" if pass_rate >= 90 else "#fbbf24"

    st.markdown(f"""
    <div class="benchmark-card">
        <div style="font-weight: 700; font-size: 0.95rem; color: #f8fafc; display: flex; align-items: center; gap: 8px;">
            <span>🎯 Đánh Giá Hiệu Năng So Với Mục Tiêu Đề Tài (N2-04A)</span>
        </div>
        <div class="benchmark-grid">
            <div class="benchmark-item">
                <div class="benchmark-label">Tỷ lệ bắt lỗi tự động trước review</div>
                <div class="benchmark-val" style="color: {auto_detect_color};">{pass_rate:.1f}% <span style="font-size: 0.75rem; color: #94a3b8;">(Mục tiêu: {auto_detect_target})</span></div>
                <div style="font-size: 0.75rem; color: {auto_detect_color}; font-weight: 600; margin-top: 2px;">{auto_detect_status}</div>
            </div>
            <div class="benchmark-item">
                <div class="benchmark-label">Số vòng trả bài/job ước tính</div>
                <div class="benchmark-val" style="color: #38bdf8;">≤ 1 vòng <span style="font-size: 0.75rem; color: #94a3b8;">(Baseline: 2–3 vòng)</span></div>
                <div style="font-size: 0.75rem; color: #34d399; font-weight: 600; margin-top: 2px;">⚡ Giảm ≥ 60% số vòng lặp</div>
            </div>
            <div class="benchmark-item">
                <div class="benchmark-label">Thời gian rà soát của Reviewer</div>
                <div class="benchmark-val" style="color: #c084fc;">Tiết kiệm ≥ 65%</div>
                <div style="font-size: 0.75rem; color: #34d399; font-weight: 600; margin-top: 2px;">🚀 Rút ngắn từ 10p → 3p/frame</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if total_issues == 0:
        st.info("Không có dữ liệu lỗi để vẽ biểu đồ.")
    else:
        ccol1, ccol2 = st.columns(2)

        with ccol1:
            st.markdown("##### 📌 Phân bố vi phạm theo Quy tắc (Rule)")
            rule_counts = pd.Series([e.rule_id for e in report.errors]).value_counts()
            fig_r, ax_r = plt.subplots(figsize=(6, 4))
            ax_r.set_facecolor(bg_header)
            fig_r.patch.set_facecolor(bg_main)
            bars = ax_r.bar(rule_counts.index, rule_counts.values, color="#38bdf8", edgecolor="#0284c7", linewidth=1.2)
            ax_r.set_ylabel("Số lượng vi phạm", color="#94a3b8")
            ax_r.tick_params(colors="#e2e8f0")
            for spine in ax_r.spines.values():
                spine.set_color(border_c)
            for bar in bars:
                yval = bar.get_height()
                ax_r.text(bar.get_x() + bar.get_width()/2.0, yval + 0.1, int(yval), ha="center", va="bottom", color="#7dd3fc", weight="bold")
            fig_r.tight_layout()
            st.pyplot(fig_r)

        with ccol2:
            st.markdown("##### 🚗 Phân bố vi phạm theo Loại nhãn (Category)")
            cat_counts = pd.Series([e.category for e in report.errors]).value_counts()
            fig_c, ax_c = plt.subplots(figsize=(6, 4))
            ax_c.set_facecolor(bg_header)
            fig_c.patch.set_facecolor(bg_main)
            bars_c = ax_c.bar(cat_counts.index, cat_counts.values, color="#f472b6", edgecolor="#db2777", linewidth=1.2)
            ax_c.set_ylabel("Số lượng vi phạm", color="#94a3b8")
            ax_c.tick_params(colors="#e2e8f0", rotation=25)
            for spine in ax_c.spines.values():
                spine.set_color(border_c)
            for bar in bars_c:
                yval = bar.get_height()
                ax_c.text(bar.get_x() + bar.get_width()/2.0, yval + 0.1, int(yval), ha="center", va="bottom", color="#fbcfe8", weight="bold")
            fig_c.tight_layout()
            st.pyplot(fig_c)

        st.markdown("##### 📋 Bảng tần suất lỗi theo Rule:")
        summary_rows = []
        for r_id in sorted(list(set(e.rule_id for e in report.errors))):
            errs_r = [e for e in report.errors if e.rule_id == r_id]
            err_c = sum(1 for e in errs_r if e.is_error())
            warn_c = sum(1 for e in errs_r if e.is_warning())
            summary_rows.append({
                "Mã Rule": r_id,
                "Tổng số lần": len(errs_r),
                "ERROR (Nghiêm trọng)": err_c,
                "WARNING (Cảnh báo)": warn_c,
                "Gợi ý sửa nhanh": RULE_SUGGESTIONS.get(r_id, ""),
            })
        st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# TAB 4: Hướng dẫn & Quy chuẩn 12 Rules
# ---------------------------------------------------------------------------
with tab_docs:
    st.markdown("""
    <div style="margin-bottom: 16px;">
        <h3 style="margin: 0; color: #f8fafc; font-size: 1.25rem;">📖 Quy Chuẩn 12 Rules & Hướng Dẫn Sửa Lỗi Cho Annotator</h3>
        <p style="margin: 2px 0 0 0; color: #94a3b8; font-size: 0.85rem;">Quy định chuẩn hóa dữ liệu 2D Bounding Box, Polygon Segmentation và Video Tracking (Đề tài N2-04A)</p>
    </div>
    """, unsafe_allow_html=True)

    r_tab1, r_tab2, r_tab3, r_tab4, r_tab5 = st.tabs([
        "📐 BBox Rules (B01-B04)",
        "📉 Polygon Rules (P01-P03)",
        "👥 Attribute Rules (A01-A03)",
        "🎬 Video Sequence (T01-T02)",
        "🤖 AI Cross-check (AI01)",
    ])

    with r_tab1:
        st.markdown(r"""
        #### 📐 Nhóm Luật Bounding Box (Phụ trách: Nguyễn Thanh Đức)
        - **`RULE_B01` — Out of Bounds (🔴 ERROR):**
          - *Công thức:* Tọa độ vượt ngoài kích thước ảnh ($x_1 < 0, y_1 < 0, x_2 > W, y_2 > H$).
          - *Nguyên nhân:* Vẽ tràn viền ảnh hoặc kéo chuột trượt ra mép canvas.
          - *Cách sửa:* Thu nhỏ box hoặc kéo box nằm trọn trong giới hạn $[0, W] \times [0, H]$.
        - **`RULE_B02` — Inverted / Zero Box (🔴 ERROR):**
          - *Công thức:* $x_2 \le x_1$ hoặc $y_2 \le y_1$ hoặc diện tích bằng 0.
          - *Nguyên nhân:* Bị đảo ngược điểm kéo chuột hoặc click vô tình tạo box rỗng.
          - *Cách sửa:* Xóa box 0px và vẽ lại sao cho $x_2 > x_1$ và $y_2 > y_1$.
        - **`RULE_B03` — Too Small Box (🟡 WARNING):**
          - *Công thức:* Diện tích $w \times h < 64\text{px}^2$.
          - *Nguyên nhân:* Chấm nhầm điểm ảnh rác, nhiễu hoặc vật thể quá xa không thể nhận diện.
          - *Cách sửa:* Nếu là vật thể thật hãy giữ lại; nếu là click nhầm hãy xóa bỏ.
        - **`RULE_B04` — Abnormal Aspect Ratio (🟡 WARNING):**
          - *Công thức:* Tỉ lệ $w/h > 25$ hoặc $h/w > 25$.
          - *Nguyên nhân:* Kéo dẹt box bất thường, box biến dạng thành 1 đường thẳng mảnh.
          - *Cách sửa:* Căn chỉnh lại chiều rộng và chiều cao bao khít vật thể thực tế.
        """)

    with r_tab2:
        st.markdown(r"""
        #### 📉 Nhóm Luật Polygon Topology (Phụ trách: Hoàng Công Chứ)
        - **`RULE_P01` — Insufficient Vertices (🔴 ERROR):**
          - *Công thức:* Số đỉnh polygon $< 3$.
          - *Nguyên nhân:* Bấm enter kết thúc vẽ khi mới chỉ có 1 hoặc 2 điểm.
          - *Cách sửa:* Đa giác khép kín cần ít nhất 3 đỉnh. Hãy vẽ bổ sung thêm điểm.
        - **`RULE_P02` — Self-Intersection (🔴 ERROR):**
          - *Công thức:* Đa giác tự cắt viền (xoắn hình nơ, phức hợp).
          - *Nguyên nhân:* Thứ tự các đỉnh bị đảo lộn chéo nhau khi vẽ tay nhanh.
          - *Cách sửa:* Xóa và vẽ lại polygon đơn giản theo chiều kim đồng hồ, không để các đoạn thẳng viền cắt nhau.
        - **`RULE_P03` — Mask vs Box Mismatch (🟡 WARNING):**
          - *Công thức:* $\text{IoU}(\text{Box}(\text{poly}), \text{box2d}) < 0.70$.
          - *Nguyên nhân:* BBox và Segmentation mask của cùng 1 vật thể không ăn khớp nhau.
          - *Cách sửa:* Điều chỉnh lại BBox sao cho bao khít với ranh giới của polygon.
        """)

    with r_tab3:
        st.markdown(r"""
        #### 👥 Nhóm Luật Thuộc Tính & Trùng Lặp (Phụ trách: Trần Thị Thủy Tiên)
        - **`RULE_A01` — Duplicate Object (🔴 ERROR):**
          - *Công thức:* 2 box cùng class chồng đè lên nhau với $\text{IoU} > 0.85$.
          - *Nguyên nhân:* Annotator vẽ đè 2 lần cho cùng một vật thể mà quên xóa nhãn cũ.
          - *Cách sửa:* Kiểm tra danh sách nhãn và xóa bớt 1 trong 2 box trùng lặp.
        - **`RULE_A02` — Missing Attributes (🟡 WARNING):**
          - *Yêu cầu:* Thiếu 2 thuộc tính bắt buộc là `occluded` (bị che khuất) hoặc `truncated` (bị cắt xén).
          - *Cách sửa:* Mở panel thuộc tính và đánh dấu giá trị True/False chính xác.
        - **`RULE_A03` — Traffic Light Color (🔴 ERROR):**
          - *Yêu cầu:* Vật thể là `traffic light` nhưng thuộc tính `color` không nằm trong `['red', 'yellow', 'green', 'none']`.
          - *Cách sửa:* Khai báo đúng màu sắc trạng thái của đèn giao thông.
        """)

    with r_tab4:
        st.markdown(r"""
        #### 🎬 Nhóm Luật Chuỗi Video Tracking (Phụ trách: Đào Ngọc Hiếu)
        - **`RULE_T01` — Object Flicker / Lost Track (🟡 WARNING):**
          - *Hiện tượng:* Vật thể xuất hiện ở Frame $k-1$ và $k+1$ nhưng biến mất ở Frame $k$.
          - *Nguyên nhân:* Annotator bị sót nhãn ở khung hình giữa chuỗi.
          - *Cách sửa:* Bổ sung nhãn liên tục hoặc dùng tính năng nội suy (interpolation).
        - **`RULE_T02` — Position Drift / Sudden Jump (🟡 WARNING):**
          - *Hiện tượng:* Box bị nhảy vọt vị trí bất thường ($> 35\%$ kích thước khung hình) giữa 2 frame liên tiếp.
          - *Nguyên nhân:* Gán nhầm ID vật thể hoặc nhảy nhầm tọa độ box.
          - *Cách sửa:* Kiểm tra ID liên kết hoặc căn chỉnh lại tọa độ cho mượt mà.
        """)

    with r_tab5:
        st.markdown(r"""
        #### 🤖 Nhóm Trợ Lý AI Cross-check (Tích hợp: YOLOv8)
        - **`RULE_AI01` — AI Missed Object (🔴 ERROR / 🟡 WARNING):**
          - *Hiện tượng:* AI quét ảnh gốc và phát hiện xe, người, xe buýt, xe tải nhưng trong file nhãn chưa có BBox tương ứng.
          - *Độ tin cậy:* Confidence $\ge 60\%$ xếp loại ERROR; $35\% - 60\%$ xếp loại WARNING.
          - *Cách sửa:* Đối chiếu với ảnh gốc xem có phải vật thể thật bị bỏ sót không, nếu có hãy vẽ bổ sung nhãn.
        """)

