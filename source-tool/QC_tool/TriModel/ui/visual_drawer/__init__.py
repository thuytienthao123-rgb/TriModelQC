from __future__ import annotations
from pathlib import Path
import base64
from io import BytesIO
from typing import Optional, Dict, Any
from PIL import Image
import streamlit.components.v1 as components

_component_path = Path(__file__).parent.resolve()
_visual_bbox_drawer_func = components.declare_component(
    "visual_bbox_drawer",
    path=str(_component_path),
)


def visual_bbox_drawer(
    image: Image.Image,
    label: str = "car",
    orig_w: int = 1920,
    orig_h: int = 1080,
    display_w: int = 390,
    key: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Component vẽ tay trực quan (Visual Mouse Drag & Drop BBox Drawer).
    Cho phép Annotator dùng chuột kéo vẽ trực tiếp trên ảnh và trả về tọa độ pixel thực tế.
    """
    buf = BytesIO()
    # Resize nhẹ cho preview nếu ảnh quá lớn để tối ưu bộ nhớ và tốc độ truyền
    preview_w = min(image.width, 1280)
    preview_h = int(image.height * (preview_w / image.width))
    if preview_w < image.width:
        thumb = image.resize((preview_w, preview_h), Image.Resampling.BILINEAR)
    else:
        thumb = image
    thumb.convert("RGB").save(buf, format="JPEG", quality=82)
    img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    return _visual_bbox_drawer_func(
        img_b64=img_b64,
        label=label,
        orig_w=orig_w,
        orig_h=orig_h,
        display_w=display_w,
        key=key,
        default=None,
    )
