from __future__ import annotations
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image

from qc.models import FrameData
from qc.parser import parse_bdd100k_text, load_bdd100k, parse_yolo_text
from ui.constants import LOCAL_IMAGE_DIRS

logger = logging.getLogger("QC_IO")


def find_matching_image(frame_name: str, image_map: Dict[str, Any]) -> Optional[Any]:
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


def load_image(img_ref: Any) -> Optional[Image.Image]:
    """Mở ảnh an toàn từ PIL.Image, chuỗi đường dẫn, Path, hoặc UploadedFile Streamlit."""
    if img_ref is None:
        return None
    if isinstance(img_ref, Image.Image):
        return img_ref
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


def read_file_bytes(
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
        try:
            from qc.parser import parse_cvat_xml_text
            frames = parse_cvat_xml_text(text)
            if frames:
                return frames
        except Exception:
            pass
        m = re.search(r'\[.*\]', text, re.DOTALL)
        if m:
            try:
                return parse_bdd100k_text(m.group(0))
            except Exception:
                pass
        return None

    return None


def scan_folder(
    folder_path: str,
    default_w: int = 1920,
    default_h: int = 1080,
) -> Tuple[List[Tuple[str, List[FrameData]]], Optional[List[str]]]:
    """Quét folder, tự động nhận diện classes.txt, file JSON, XML và TXT YOLO."""
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

    for fp in sorted(p.glob("*.xml")):
        try:
            raw_bytes = fp.read_bytes()
            frames = read_file_bytes(raw_bytes, fp.name, width=default_w, height=default_h)
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
            frames = read_file_bytes(raw_bytes, fp.name, width=w, height=h, class_names=detected_classes)
            if frames:
                results.append((fp.name, frames))
        except Exception:
            pass

    return results, detected_classes
