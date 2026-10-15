from __future__ import annotations
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image
import streamlit as st

from qc.models import BBox2D, LabeledObject

logger = logging.getLogger("QC_AI")


@st.cache_resource
def load_ai_detector():
    """Nạp model YOLOv8 cục bộ để phát hiện vật thể bị bỏ sót trong ảnh."""
    base_dir = Path(__file__).parent.parent
    candidates = [
        base_dir / "yolov8n.pt",
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


def detect_missed_objects(
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
