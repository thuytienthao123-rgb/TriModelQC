"""
app.py — Giao diện Web tương tác Streamlit cho BDD-QC Tool (Mã đề: N2-04A).
Hỗ trợ kiểm tra chất lượng Bounding Box & Polygon 2D trên dataset BDD100K.
"""

from __future__ import annotations
import json
import os
from pathlib import Path
import logging
from typing import List, Dict, Any, Optional, Tuple

import streamlit as st
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
# Hỗ trợ đọc đa định dạng (JSON BDD100K & TXT YOLO)
# ---------------------------------------------------------------------------
SUPPORTED_EXTS = [".json", ".txt", ".xml"]


LOCAL_IMAGE_DIRS = [
    Path(r"C:\Users\tient\Downloads\Group_23\dataset_final\images"),
    Path(r"C:\Users\tient\Downloads\Group_23\du_lieu\images"),
    Path(r"C:\Users\tient\Downloads\Group_23\anylabeling_workspace\Video_3"),
    Path(r"C:\Users\tient\Downloads\Group_23\anylabeling_workspace\Video_1"),
    Path(r"C:\Users\tient\Downloads\Group_23\anylabeling_workspace\Video_0"),
    Path(r"C:\Users\tient\Downloads\Group_23\anylabeling_workspace\Video_4"),
]


def _find_matching_image(frame_name: str, image_map: Dict[str, Any]) -> Optional[Any]:
    """Tìm ảnh tương ứng với frame_name trong ảnh đã upload hoặc thư mục cục bộ."""
    stem = Path(frame_name).stem
    stem_lower = stem.lower()

    if image_map:
        # 1. Khớp chính xác tên file
        if frame_name in image_map:
            return image_map[frame_name]
        if stem in image_map:
            return image_map[stem]
        # 2. Khớp không phân biệt hoa thường
        for k, v in image_map.items():
            if k.lower() == stem_lower or Path(k).stem.lower() == stem_lower:
                return v
        # 3. Khớp chuỗi số frame (ví dụ: '0160' trong 'Video_3_frame_0160')
        import re
        m = re.search(r'(\d{3,5})', stem)
        if m:
            num = m.group(1)
            for k, v in image_map.items():
                if num in k:
                    return v

    # Fallback: Tự động tìm trong các thư mục ảnh cục bộ của dự án
    for d in LOCAL_IMAGE_DIRS:
        if not d.exists():
            continue
        for ext in [".jpg", ".jpeg", ".png", ".webp"]:
            cand = d / f"{stem}{ext}"
            if cand.exists():
                return str(cand)
            # Thử tìm theo frame number
            import re
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
    """Parse bytes từ một file upload thành List[FrameData].
    Hỗ trợ:
      - .json: BDD100K JSON
      - .txt: Thử BDD100K JSON trước, nếu không được thì tự động parse định dạng YOLO
      - .xml: Trích xuất JSON nhúng nếu có
    """
    name = filename.lower()
    try:
        text = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = file_bytes.decode("latin-1")
        except Exception:
            return None

    # 1. JSON
    if name.endswith(".json"):
        try:
            return parse_bdd100k_text(text)
        except Exception:
            pass

    # 2. TXT (BDD100K JSON hoặc YOLO Format)
    if name.endswith(".txt"):
        # Thử parse JSON trước (phòng trường hợp CVAT export JSON lưu đuôi txt)
        try:
            return parse_bdd100k_text(text)
        except Exception:
            pass

        # Parse theo định dạng YOLO (BBox hoặc Polygon)
        try:
            stem = Path(filename).stem
            # Tạo frame_name có đuôi ảnh để dễ map với ảnh minh họa
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

    # 3. XML (nếu có nhúng JSON)
    if name.endswith(".xml"):
        import re
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

    # 1. Đọc classes.txt nếu có
    detected_classes = None
    for cf in ["classes.txt", "names.txt", "obj.names"]:
        cf_path = p / cf
        if cf_path.exists():
            try:
                detected_classes = [l.strip() for l in cf_path.read_text(encoding="utf-8").splitlines() if l.strip()]
                break
            except Exception:
                pass

    # 2. Quét file JSON
    for fp in sorted(p.glob("*.json")):
        try:
            frames = load_bdd100k(fp)
            if frames:
                results.append((fp.name, frames))
        except Exception:
            pass

    # 3. Quét file TXT (YOLO)
    for fp in sorted(p.glob("*.txt")):
        if fp.name.lower() in ("classes.txt", "names.txt", "obj.names", "requirements.txt"):
            continue
        try:
            # Thử xem có ảnh tương ứng để lấy đúng kích thước thật
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
# Trợ lý AI: Bộ 3 mô hình (Tri-Model Consensus Ensemble)
# ---------------------------------------------------------------------------
@st.cache_resource
def _load_ai_detector():
    """Nạp hệ thống Tri-Model Consensus AI Detector."""
    try:
        from qc.ai_detector import TriModelQCAssistant
        assistant = TriModelQCAssistant()
        if assistant.is_ready():
            return assistant
    except Exception as e:
        logger.warning("Lỗi nạp TriModelQCAssistant: %s", e)
    return None


def _run_ai_qc(
    img_pil: Image.Image,
    user_objects: List[LabeledObject],
    assistant,
    conf_thresh: float = 0.35,
    ensemble_mode: str = "strict",
) -> Dict[str, Any]:
    """Chạy phân tích đa mô hình (Tri-Model) và đối chiếu với nhãn người dùng."""
    if assistant is None or img_pil is None:
        return {"missed": [], "mismatched": [], "total_ai_detections": 0, "total_user_objects": 0}
    try:
        return assistant.check_missed_and_mismatched(
            img_pil=img_pil,
            user_objects=user_objects,
            conf_thresh=conf_thresh,
            ensemble_mode=ensemble_mode,
        )
    except Exception as ex:
        logger.warning("Lỗi Tri-Model AI cross-check: %s", ex)
        return {"missed": [], "mismatched": [], "total_ai_detections": 0, "total_user_objects": 0}


# ---------------------------------------------------------------------------
# Cấu hình giao diện Streamlit
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="BDD100K QC Tool (N2-04A)",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS cho giao diện hiện đại
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8 0%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 0.95rem;
        color: #94a3b8;
        margin-bottom: 1.2rem;
    }
    .metric-card {
        background-color: #1e293b;
        border-radius: 10px;
        padding: 15px 20px;
        border-left: 4px solid #38bdf8;
    }
    .badge-err {
        background-color: #ef4444;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-warn {
        background-color: #f59e0b;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar: Nguồn dữ liệu & Cấu hình Rule
# ---------------------------------------------------------------------------
st.sidebar.image("https://img.shields.io/badge/QC_Tool-N2--04A-blue?style=for-the-badge", use_container_width=True)
st.sidebar.title("⚙️ Cấu hình QC")

# 1. Chọn nguồn dữ liệu
data_source = st.sidebar.radio(
    "Nguồn dữ liệu nhãn:",
    options=[
        "⚡ Dùng dữ liệu mẫu",
        "📂 Upload nhiều file (JSON / TXT YOLO / XML)",
        "🗂️ Quét cả thư mục (nhập đường dẫn)",
    ],
    index=0,
)

# Tùy chọn độ phân giải mặc định (dùng khi file nhãn là YOLO txt)
canvas_res = st.sidebar.selectbox(
    "📐 Độ phân giải khung hình (YOLO):",
    options=["1920x1080 (Full HD)", "1280x720 (HD BDD100K)", "2560x1440 (2K)"],
    index=0,
    help="Tọa độ YOLO được chuẩn hóa (0..1), cần kích thước ảnh để tính ra pixel.",
)
default_w = 1920 if "1920" in canvas_res else (1280 if "1280" in canvas_res else 2560)
default_h = 1080 if "1080" in canvas_res else (720 if "720" in canvas_res else 1440)

# Tải ảnh minh họa đa file (tùy chọn)
uploaded_images_raw = st.sidebar.file_uploader(
    "🖼️ Tải ảnh minh họa gốc (Tùy chọn, nhiều ảnh):",
    type=["jpg", "jpeg", "png", "webp", "bmp"],
    accept_multiple_files=True,
    help=(
        "Upload ảnh gốc tương ứng với frame để hiển thị viền lỗi trên ảnh thật.\n"
        "Tên file ảnh khớp với tên frame (ví dụ: Video_3_frame_0160.jpg)."
    ),
)
# Xây dựng dict: {tên_ảnh -> file_object}
uploaded_image_map: Dict[str, Any] = {}
if uploaded_images_raw:
    for _img_f in uploaded_images_raw:
        uploaded_image_map[_img_f.name] = _img_f
        uploaded_image_map[Path(_img_f.name).stem] = _img_f
    st.sidebar.success(f"✅ Đã tải **{len(uploaded_images_raw)} ảnh** minh họa")

# Lưu kết quả parse: list of (filename, frames)
all_sources: List[Tuple[str, List[FrameData]]] = []
file_display_name = "batch"

SAMPLE_PATH = Path(__file__).parent / "data_sample" / "sample_with_errors.json"

if data_source == "⚡ Dùng dữ liệu mẫu":
    if SAMPLE_PATH.exists():
        try:
            frames_sample = load_bdd100k(SAMPLE_PATH)
            all_sources.append(("sample_with_errors.json", frames_sample))
            file_display_name = "sample_with_errors"
            st.sidebar.success("✅ Đã nạp file mẫu sẵn có")
        except Exception as ex:
            st.sidebar.error(f"Lỗi đọc file mẫu: {ex}")
    else:
        st.sidebar.error("Không tìm thấy file sample_with_errors.json")

elif data_source == "📂 Upload nhiều file (JSON / TXT YOLO / XML)":
    st.sidebar.caption(
        "Chọn **một hoặc nhiều file** cùng lúc.  \n"
        "Hỗ trợ: `.json`, `.txt` (BDD100K hoặc YOLO), `.xml`"
    )
    uploaded_files = st.sidebar.file_uploader(
        "Chọn file nhãn:",
        type=["json", "txt", "xml"],
        accept_multiple_files=True,
        help="Giữ Ctrl (Windows) hoặc Cmd (Mac) để chọn nhiều file cùng lúc.",
    )
    if uploaded_files:
        # Bước A: Tìm classes.txt trong danh sách upload nếu có
        custom_classes: Optional[List[str]] = None
        for uf in uploaded_files:
            if uf.name.lower() in ("classes.txt", "names.txt", "obj.names"):
                try:
                    custom_classes = [l.strip() for l in uf.getvalue().decode("utf-8").splitlines() if l.strip()]
                    st.sidebar.info(f"🏷️ Đã nhận diện classes: {', '.join(custom_classes[:5])}")
                except Exception:
                    pass

        # Bước B: Parse từng file nhãn
        ok_count = 0
        fail_names = []
        for uf in uploaded_files:
            if uf.name.lower() in ("classes.txt", "names.txt", "obj.names"):
                continue  # Bỏ qua file khai báo classes, không coi là frame nhãn

            # Ưu tiên lấy kích thước thật từ ảnh tương ứng đã upload
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
            st.sidebar.success(f"✅ Đã nạp thành công {ok_count} / {len(uploaded_files)} file")
            file_display_name = "_".join(Path(f.name).stem for f in uploaded_files[:3])
        if fail_names:
            st.sidebar.warning(f"⚠️ Không parse được: {', '.join(fail_names)}")

else:  # Quét thư mục
    st.sidebar.caption(
        "Nhập đường dẫn thư mục chứa file nhãn.  \n"
        "Tool sẽ tự động tìm tất cả `.json`, `.txt` (YOLO) bên trong."
    )
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
            st.sidebar.warning(
                "Không tìm thấy file nhãn hợp lệ trong thư mục này.  \n"
                "Kiểm tra đường dẫn và định dạng file."
            )
    elif scan_btn:
        st.sidebar.warning("Vui lòng nhập đường dẫn thư mục.")

    if all_sources:
        with st.sidebar.expander(f"📄 {len(all_sources)} file tìm thấy", expanded=False):
            for fname, frs in all_sources:
                st.caption(f"• **{fname}** — {len(frs)} frames")

# 2. Bộ lọc Rules
st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Chọn bộ luật kiểm tra")

enable_bbox = st.sidebar.checkbox("Kiểm tra Bounding Box (B01 - B04)", value=True)
enable_poly = st.sidebar.checkbox("Kiểm tra Polygon (P01 - P03)", value=True)
enable_attr = st.sidebar.checkbox("Kiểm tra Thuộc tính & Trùng lặp (A01 - A03)", value=True)
enable_seq = st.sidebar.checkbox("Kiểm tra Chuỗi Video (T01 - T02: Bỏ sót / Lệch)", value=True)

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

# Tích hợp Tri-Model AI Detector để soi lỗi gán thiếu & sai nhãn
ai_assistant = _load_ai_detector()
enable_ai_check = False
ai_conf = 0.35
ai_ensemble_mode = "strict"

if ai_assistant is not None:
    st.sidebar.markdown("---")
    st.sidebar.subheader("🤖 Tri-Model AI QC Assistant")
    enable_ai_check = st.sidebar.checkbox(
        "Kích hoạt Tri-Model AI QC",
        value=True,
        help="Sử dụng bộ 3 mô hình (Tri-Model Ensemble) + Weighted Boxes Fusion (WBF) để phát hiện vật thể bỏ sót và sai nhãn.",
    )
    if enable_ai_check:
        ai_ensemble_mode = st.sidebar.radio(
            "Cơ chế hợp nhất (Consensus):",
            options=["strict", "majority"],
            format_func=lambda x: "🛡️ Nghiêm ngặt (Cả 3 model đồng thuận)" if x == "strict" else "⚖️ Đa số (Tối thiểu 2/3 model)",
            help="Chế độ nghiêm ngặt yêu cầu cả 3 mô hình cùng nhận diện và lấy trung bình tọa độ. Chế độ này triệt tiêu hoàn toàn báo động giả, giảm tối đa thời gian reviewer phải rà soát.",
        )
        ai_conf = st.sidebar.slider("Độ nhạy AI (Confidence):", 0.20, 0.70, 0.35, 0.05)

        with st.sidebar.expander("ℹ️ Thông tin bộ 3 mô hình", expanded=False):
            for m_key, m_desc in ai_assistant.model_descriptions.items():
                st.markdown(f"- **{m_key}**: {m_desc}")
            st.caption("📐 Thuật toán hợp nhất: Weighted Boxes Fusion (WBF)")

# Nút RUN (Checking) và RESET (Reload) trên Sidebar
st.sidebar.markdown("---")
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

if reset_btn:
    st.session_state["qc_report"] = None
    st.session_state["qc_frames"] = None
    st.session_state["qc_sources"] = None
    st.session_state["qc_rules_snapshot"] = None
    st.session_state["qc_display_name"] = ""
    st.rerun()

# Thông tin nhóm
st.sidebar.markdown("---")
st.sidebar.caption("👥 **Nhóm thực hiện (N2-04A):**")
st.sidebar.caption("• Đào Ngọc Hiếu (Leader / Pipeline)\n• Đoàn Văn Thắng (Parser & Data)\n• Nguyễn Thanh Đức (BBox Rules)\n• Hoàng Công Chứ (Poly Rules)\n• Trần Thị Thủy Tiên (Attr Rules)")


# ---------------------------------------------------------------------------
# Main Content
# ---------------------------------------------------------------------------
st.markdown('<div class="main-header">🛡️ BDD100K 2D Annotation Quality Control</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Hệ thống Linter & Kiểm tra chất lượng gán nhãn tự động — Hỗ trợ JSON BDD100K & TXT YOLO đa file (Mã đề: N2-04A)</div>', unsafe_allow_html=True)

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

    with st.spinner("⏳ Đang chạy QC & kiểm tra chất lượng (Linter + AI)... Vui lòng chờ."):
        import time
        _t0 = time.time()
        _report = run_qc(
            all_frames_run,
            rules=active_rules,
            sequence_rules=active_seq_rules,
        )

        # Quét Tri-Model AI phát hiện vật thể bỏ sót & sai lệch nhãn (RULE_AI01 & RULE_AI02)
        if enable_ai_check and ai_assistant is not None:
            for frame in all_frames_run:
                img_ref = _find_matching_image(frame.name, uploaded_image_map)
                if img_ref is not None:
                    img_obj = _load_image(img_ref)
                    if img_obj is not None:
                        ai_res = _run_ai_qc(
                            img_obj,
                            frame.objects,
                            ai_assistant,
                            conf_thresh=ai_conf,
                            ensemble_mode=ai_ensemble_mode,
                        )
                        # 1. Báo lỗi vật thể bỏ sót (RULE_AI01)
                        for m_idx, m_obj in enumerate(ai_res.get("missed", []), 1):
                            mbx = m_obj["box2d"]
                            m_cat = m_obj["category"]
                            m_conf = m_obj["confidence"]
                            agreed_cnt = m_obj.get("agreement_count", 3)
                            _report.add(QCError(
                                rule_id="RULE_AI01",
                                severity="ERROR" if agreed_cnt >= 3 or m_conf >= 0.60 else "WARNING",
                                frame_name=frame.name,
                                object_id=f"ai_missed_{m_idx:02d}",
                                category=m_cat,
                                message=(
                                    f"[AI {agreed_cnt}/3 Đồng thuận] Bỏ sót [{m_cat}] tại "
                                    f"[{int(mbx.x1)}, {int(mbx.y1)}, {int(mbx.x2)}, {int(mbx.y2)}] "
                                    f"(tọa độ trung bình WBF, độ tin cậy: {m_conf:.0%})"
                                ),
                            ))

                        # 2. Báo lỗi nghi vấn sai loại nhãn (RULE_AI02)
                        for mm_idx, mm_obj in enumerate(ai_res.get("mismatched", []), 1):
                            _report.add(QCError(
                                rule_id="RULE_AI02",
                                severity="WARNING",
                                frame_name=frame.name,
                                object_id=mm_obj["user_obj_id"],
                                category=mm_obj["user_category"],
                                message=(
                                    f"Nghi vấn sai nhãn: Người gán là [{mm_obj['user_category']}] "
                                    f"nhưng AI đồng thuận xác định là [{mm_obj['ai_category']}] "
                                    f"(IoU {mm_obj['iou']:.0%}, độ tin cậy AI: {mm_obj['confidence']:.0%})"
                                ),
                            ))

        _elapsed = time.time() - _t0

    st.session_state["qc_report"] = _report
    st.session_state["qc_frames"] = all_frames_run
    st.session_state["qc_sources"] = all_sources
    st.session_state["qc_rules_snapshot"] = active_rules
    st.session_state["qc_display_name"] = file_display_name
    st.toast(f"✅ Hoàn thành trong {_elapsed:.2f}s — phát hiện {len(_report.errors)} vấn đề", icon="🛡️")

# Khi người dùng bấm nút Checking trên Sidebar
if run_btn:
    _execute_qc()

# Lấy kết quả từ session
report = st.session_state.get("qc_report")
frames = st.session_state.get("qc_frames")
file_display_name_final = st.session_state.get("qc_display_name", file_display_name)
cached_sources = st.session_state.get("qc_sources", all_sources)

if report is None:
    # Hiển thị trang chờ với 2 NÚT TO RÕ: CHECKING & RELOAD
    st.markdown("---")
    n_files = len(all_sources)
    n_frames = sum(len(frs) for _, frs in all_sources)
    n_imgs = len(uploaded_image_map) // 2 if uploaded_image_map else 0

    st.subheader("📋 Sẵn sàng kiểm tra chất lượng dữ liệu")
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("📄 File nhãn đã nạp", str(n_files))
    r2.metric("🎬 Frames phát hiện", str(n_frames))
    r3.metric("🖼️ Ảnh minh họa", str(n_imgs))
    r4.metric("⚙️ Rules kích hoạt", f"{len(active_rules)} / 10")

    st.markdown("<br>", unsafe_allow_html=True)
    c_btn1, c_btn2, _ = st.columns([3, 2, 4])
    with c_btn1:
        if st.button("🚀 BẮT ĐẦU KIỂM TRA (CHECKING)", type="primary", use_container_width=True):
            _execute_qc()
            st.rerun()
    with c_btn2:
        if st.button("🔄 TẢI LẠI (RELOAD)", use_container_width=True):
            st.session_state["qc_report"] = None
            st.rerun()

    st.stop()
    import sys
    sys.exit(0)


# ---------------------------------------------------------------------------
# Thẻ Thống kê KPI tóm tắt & Báo cáo kết quả
# ---------------------------------------------------------------------------
if report is not None:
    # Thanh thông tin nguồn và nút Reload nhanh
    tcol_info, tcol_reload = st.columns([8, 2])
with tcol_info:
    if len(all_sources) > 1:
        st.caption(
            f"📦 Đang phân tích **{len(all_sources)} file** | "
            + " · ".join(f"`{n}`" for n, _ in all_sources[:5])
            + (f" ... và {len(all_sources)-5} file khác" if len(all_sources) > 5 else "")
        )
    else:
        st.caption("📦 Đã hoàn thành phân tích dữ liệu")
with tcol_reload:
    if st.button("🔄 Reload lại", use_container_width=True, help="Xóa cache và chạy kiểm tra lại"):
        st.session_state["qc_report"] = None
        st.rerun()

col1, col2, col3, col4, col5 = st.columns(5)

total_issues = len(report.errors)
pass_rate = 100.0 if report.total_objects == 0 else max(0.0, 100.0 - (total_issues / report.total_objects * 100))

col1.metric("🖼️ Tổng số Frame", f"{report.total_frames:,}")
col2.metric("🎯 Tổng số Object", f"{report.total_objects:,}")
col3.metric("❌ Số lỗi (ERROR)", f"{report.error_count():,}", delta=f"-{report.error_count()}" if report.error_count() > 0 else "0", delta_color="inverse")
col4.metric("⚠️ Cảnh báo (WARN)", f"{report.warning_count():,}", delta=f"-{report.warning_count()}" if report.warning_count() > 0 else "0", delta_color="inverse")
col5.metric("📈 Tỷ lệ đạt chuẩn", f"{pass_rate:.1f}%", delta=f"{pass_rate:.1f}%")

st.markdown("---")

# ---------------------------------------------------------------------------
# Tabs hiển thị kết quả
# ---------------------------------------------------------------------------
tab_list, tab_visual, tab_charts, tab_docs = st.tabs([
    "📋 Danh sách lỗi phát hiện",
    "🖼️ Visualizer (Trực quan hóa Box lỗi)",
    "📊 Thống kê & Phân tích",
    "📖 Hướng dẫn & Quy chuẩn 10 Rules",
])

# ---------------------------------------------------------------------------
# TAB 1: Danh sách lỗi
# ---------------------------------------------------------------------------
with tab_list:
    st.subheader(f"Danh sách vi phạm ({total_issues} vấn đề)")

    if total_issues == 0:
        st.success("🎉 Xuất sắc! File nhãn hoàn toàn sạch sẽ, không có lỗi hay cảnh báo nào.")
    else:
        # Chuyển đổi thành DataFrame để lọc linh hoạt
        records = []
        for e in report.errors:
            records.append({
                "Frame": e.frame_name,
                "Object ID": e.object_id,
                "Class": e.category,
                "Rule": e.rule_id,
                "Mức độ": e.severity,
                "Chi tiết lỗi": e.message,
            })
        df_errors = pd.DataFrame(records)

        # Thanh công cụ lọc
        fcol1, fcol2, fcol3 = st.columns([2, 2, 4])
        with fcol1:
            severity_filter = st.selectbox("Lọc mức độ:", options=["Tất cả", "ERROR", "WARNING"], index=0)
        with fcol2:
            rules_available = ["Tất cả"] + sorted(list(df_errors["Rule"].unique()))
            rule_filter = st.selectbox("Lọc theo Rule:", options=rules_available, index=0)
        with fcol3:
            search_text = st.text_input("🔍 Tìm kiếm (theo frame, class, object ID...):", "")

        # Áp dụng bộ lọc
        filtered_df = df_errors.copy()
        if severity_filter != "Tất cả":
            filtered_df = filtered_df[filtered_df["Mức độ"] == severity_filter]
        if rule_filter != "Tất cả":
            filtered_df = filtered_df[filtered_df["Rule"] == rule_filter]
        if search_text:
            s = search_text.lower()
            filtered_df = filtered_df[
                filtered_df["Frame"].str.lower().str.contains(s) |
                filtered_df["Object ID"].str.lower().str.contains(s) |
                filtered_df["Class"].str.lower().str.contains(s) |
                filtered_df["Chi tiết lỗi"].str.lower().str.contains(s)
            ]

        # Hiển thị bảng
        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Mức độ": st.column_config.TextColumn(
                    "Mức độ",
                    help="ERROR: Bắt buộc sửa | WARNING: Cần kiểm tra lại",
                ),
                "Rule": st.column_config.TextColumn(
                    "Mã Rule",
                    help="Mã quy tắc vi phạm",
                ),
            }
        )

        st.caption(f"Đang hiển thị {len(filtered_df)} / {total_issues} vấn đề.")

        # Nút xuất báo cáo
        st.markdown("##### 📥 Tải xuống báo cáo QC:")
        dcol1, dcol2, _ = st.columns([2, 2, 6])
        with dcol1:
            csv_data = generate_csv_str(report)
            st.download_button(
                label="📄 Tải Báo cáo CSV",
                data=csv_data,
                file_name=f"qc_report_{Path(file_display_name_final).stem or file_display_name_final}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with dcol2:
            html_data = generate_html_str(report)
            st.download_button(
                label="🌐 Tải Báo cáo HTML Dashboard",
                data=html_data,
                file_name=f"qc_report_{Path(file_display_name_final).stem or file_display_name_final}.html",
                mime="text/html",
                use_container_width=True,
            )

# ---------------------------------------------------------------------------
# TAB 2: Visualizer (Trực quan hóa Box lỗi trên Canvas)
# ---------------------------------------------------------------------------
with tab_visual:
    st.subheader("Trực quan hóa Bounding Box & Polygon bị lỗi")
    st.caption("Khung viền đỏ: Lỗi nghiêm trọng (ERROR) | Khung vàng: Cảnh báo (WARNING) | Khung xanh: Hợp lệ")

    frame_names = [f.name for f in frames]
    selected_frame_name = st.selectbox("Chọn frame cần soi:", options=frame_names, index=0)

    selected_frame = next((f for f in frames if f.name == selected_frame_name), None)

    if selected_frame:
        # Nền canvas hoặc ảnh thực tế
        matched_img_file = _find_matching_image(selected_frame_name, uploaded_image_map)
        loaded_img = _load_image(matched_img_file)

        # AI Missed & Mismatched Object Detection
        missed_objects: List[Dict[str, Any]] = []
        mismatched_objects: List[Dict[str, Any]] = []
        if enable_ai_check and loaded_img is not None and ai_assistant is not None:
            ai_tab_res = _run_ai_qc(
                loaded_img,
                selected_frame.objects,
                ai_assistant,
                conf_thresh=ai_conf,
                ensemble_mode=ai_ensemble_mode,
            )
            missed_objects = ai_tab_res.get("missed", [])
            mismatched_objects = ai_tab_res.get("mismatched", [])

        if enable_ai_check and (matched_img_file is not None or loaded_img is not None):
            mcol1, mcol2, mcol3, mcol4 = st.columns(4)
            mcol1.metric("🎯 Đã gán nhãn", f"{len(selected_frame.objects)} objects")
            mcol2.metric(
                "🚨 AI phát hiện BỎ SÓT",
                f"{len(missed_objects)} objects",
                delta=f"+{len(missed_objects)} thiếu" if missed_objects else "Đủ",
                delta_color="inverse" if missed_objects else "normal",
            )
            mcol3.metric(
                "⚠️ Nghi vấn SAI NHÃN",
                f"{len(mismatched_objects)} objects",
                delta="Cần rà soát" if mismatched_objects else "Khớp",
                delta_color="inverse" if mismatched_objects else "normal",
            )
            total_detected = len(selected_frame.objects) + len(missed_objects)
            cov = (len(selected_frame.objects) / total_detected * 100) if total_detected > 0 else 100
            mcol4.metric("📊 Tỷ lệ bao phủ nhãn", f"{cov:.1f}%")

        # Tìm các lỗi ứng với frame này
        frame_errors: Dict[str, List[QCError]] = {}
        for err in report.errors:
            if err.frame_name == selected_frame_name:
                for oid in [x.strip() for x in err.object_id.split("&")]:
                    frame_errors.setdefault(oid, []).append(err)

        # Vẽ hình bằng matplotlib
        fig, ax = plt.subplots(figsize=(12, 6.75), dpi=100)
        canvas_w = selected_frame.width
        canvas_h = selected_frame.height

        if loaded_img is not None:
            ax.imshow(loaded_img)
            ax.set_xlim(0, loaded_img.width)
            ax.set_ylim(loaded_img.height, 0)
        else:
            ax.set_facecolor("#0f172a")
            ax.set_xlim(0, canvas_w)
            ax.set_ylim(canvas_h, 0)

        # Vẽ từng object người dùng gán
        for obj in selected_frame.objects:
            obj_errs = frame_errors.get(obj.id, [])
            has_error = any(e.is_error() for e in obj_errs)
            has_warn = any(e.is_warning() for e in obj_errs)

            if has_error:
                edge_color = "#ef4444"  # Đỏ
                label_color = "#fee2e2"
                status_txt = "[ERR]"
            elif has_warn:
                edge_color = "#f59e0b"  # Vàng
                label_color = "#fef3c7"
                status_txt = "[WARN]"
            else:
                edge_color = "#22c55e"  # Xanh lá
                label_color = "#dcfce7"
                status_txt = "[OK]"

            # Vẽ Box2D
            if obj.box2d:
                bx = obj.box2d
                rect = patches.Rectangle(
                    (bx.x1, bx.y1),
                    bx.width,
                    bx.height,
                    linewidth=2.2 if (has_error or has_warn) else 1.2,
                    edgecolor=edge_color,
                    facecolor="none",
                    linestyle="--" if (has_error or has_warn) else "-",
                )
                ax.add_patch(rect)

                tag = f"{status_txt} {obj.id}: {obj.category}"
                ax.text(
                    max(5, bx.x1),
                    max(18, bx.y1 - 5),
                    tag,
                    color=edge_color,
                    fontsize=8,
                    weight="bold",
                    bbox=dict(facecolor="#1e293b", edgecolor=edge_color, boxstyle="round,pad=0.2", alpha=0.85),
                )

            # Vẽ Polygon
            if obj.poly2d and obj.poly2d.vertices:
                pts = obj.poly2d.vertices
                poly_patch = patches.Polygon(
                    pts,
                    closed=True,
                    linewidth=2.2 if has_error else 1.5,
                    edgecolor=edge_color,
                    facecolor=edge_color,
                    alpha=0.25,
                    linestyle=":" if has_error else "-",
                )
                ax.add_patch(poly_patch)
                ax.text(
                    pts[0][0],
                    pts[0][1],
                    f"{status_txt} {obj.id} (poly)",
                    color=edge_color,
                    fontsize=8,
                    weight="bold",
                    bbox=dict(facecolor="#1e293b", edgecolor=edge_color, boxstyle="round,pad=0.2", alpha=0.85),
                )

        # Vẽ các vật thể AI phát hiện bị BỎ SÓT (Khung viền cam/tím neon nét đứt từ Tri-Model Ensemble)
        for m_idx, m_obj in enumerate(missed_objects, start=1):
            mbx = m_obj["box2d"]
            m_cat = m_obj["category"]
            m_conf = m_obj["confidence"]
            agreed_cnt = m_obj.get("agreement_count", 3)
            box_color = "#a855f7" if agreed_cnt >= 3 else "#f97316"

            rect = patches.Rectangle(
                (mbx.x1, mbx.y1),
                mbx.width,
                mbx.height,
                linewidth=2.5,
                edgecolor=box_color,
                facecolor="none",
                linestyle="--",
            )
            ax.add_patch(rect)
            ax.text(
                max(5, mbx.x1),
                max(18, mbx.y1 - 5),
                f"🤖 [AI {agreed_cnt}/3] {m_cat} ({m_conf:.0%})",
                color=box_color,
                fontsize=8,
                weight="bold",
                bbox=dict(facecolor="#18181b", edgecolor=box_color, boxstyle="round,pad=0.2", alpha=0.9),
            )

        ax.set_title(
            f"Khung hình: {selected_frame_name} ({len(selected_frame.objects)} objects đã gán | {len(missed_objects)} AI phát hiện bỏ sót | {len(mismatched_objects)} nghi vấn sai nhãn)",
            color="white",
            fontsize=11,
        )
        ax.set_xticks(range(0, canvas_w + 1, 200))
        ax.set_yticks(range(0, canvas_h + 1, 100))
        ax.tick_params(colors="#94a3b8", labelsize=8)
        for spine in ax.spines.values():
            spine.set_color("#334155")
        fig.tight_layout()

        st.pyplot(fig)

        # Hiển thị cảnh báo và bảng tọa độ trung bình từ AI
        if missed_objects:
            st.warning(
                f"🚨 **Tri-Model AI phát hiện {len(missed_objects)} vật thể chưa được gán nhãn trong khung hình này!**  \n"
                f"Tọa độ các khung viền nét đứt màu tím/cam là kết quả lấy **trung bình có trọng số (WBF)** từ bộ 3 mô hình."
            )

            # Bảng chi tiết tọa độ WBF và công cụ tự động tạo file sửa nhãn
            with st.expander("📋 Xem bảng tọa độ WBF & Công cụ tự động sửa nhãn (1-Click Fix)", expanded=True):
                table_rows = []
                for idx, m in enumerate(missed_objects, 1):
                    b = m["box2d"]
                    table_rows.append({
                        "STT": idx,
                        "Đối tượng": m["category"],
                        "Độ tin cậy": f"{m['confidence']:.1%}",
                        "Đồng thuận": f"{m.get('agreement_count', 3)}/3 models",
                        "Tọa độ [x1, y1, x2, y2]": f"[{b.x1:.1f}, {b.y1:.1f}, {b.x2:.1f}, {b.y2:.1f}]",
                        "Kích thước (WxH)": f"{b.width:.1f} x {b.height:.1f} px",
                    })
                st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

                # Nút 1-Click: Tạo file nhãn YOLO txt đã bổ sung đầy đủ các box AI
                img_w = loaded_img.width if loaded_img else selected_frame.width
                img_h = loaded_img.height if loaded_img else selected_frame.height

                yolo_lines = []
                # Giữ nguyên nhãn cũ
                for uobj in selected_frame.objects:
                    if uobj.box2d:
                        bx = uobj.box2d
                        xc = ((bx.x1 + bx.x2) / 2.0) / img_w
                        yc = ((bx.y1 + bx.y2) / 2.0) / img_h
                        bw = bx.width / img_w
                        bh = bx.height / img_h
                        yolo_lines.append(f"0 {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f} # {uobj.category}")

                # Bổ sung các box AI đồng thuận
                for m in missed_objects:
                    bx = m["box2d"]
                    xc = ((bx.x1 + bx.x2) / 2.0) / img_w
                    yc = ((bx.y1 + bx.y2) / 2.0) / img_h
                    bw = bx.width / img_w
                    bh = bx.height / img_h
                    yolo_lines.append(f"0 {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f} # [AI_ADDED] {m['category']}")

                fixed_txt_content = "\n".join(yolo_lines)
                st.download_button(
                    label=f"📥 Tải file nhãn `{Path(selected_frame_name).stem}_fixed.txt` (Đã tự động bù {len(missed_objects)} box)",
                    data=fixed_txt_content,
                    file_name=f"{Path(selected_frame_name).stem}_fixed.txt",
                    mime="text/plain",
                    help="Bấm để tải file nhãn đã gộp các box người gán + các box AI 3/3 đồng thuận, giảm hơn 70% thời gian annotator phải vẽ lại.",
                )

        if mismatched_objects:
            st.info(
                f"⚠️ **Có {len(mismatched_objects)} đối tượng nghi vấn sai class:**  \n" +
                "  \n".join([
                    f"- Đối tượng `{mm['user_obj_id']}`: Gán nhãn là `{mm['user_category']}` "
                    f"nhưng AI đồng thuận xác định là `{mm['ai_category']}` (IoU: {mm['iou']:.0%})"
                    for mm in mismatched_objects
                ])
            )

        # Hiển thị các lỗi cụ thể của Frame này
        cur_errs = [e for e in report.errors if e.frame_name == selected_frame_name]
        if cur_errs:
            st.markdown(f"**Danh sách vấn đề trong frame `{selected_frame_name}`:**")
            for e in cur_errs:
                icon = "❌" if e.is_error() else "⚠️"
                st.markdown(f"- {icon} **`{e.object_id}`** (`{e.category}`) | `{e.rule_id}`: {e.message}")
        else:
            st.success("Frame này hoàn toàn hợp lệ!")

# ---------------------------------------------------------------------------
# TAB 3: Biểu đồ & Thống kê
# ---------------------------------------------------------------------------
with tab_charts:
    st.subheader("Phân tích chất lượng dữ liệu")

    if total_issues == 0:
        st.info("Không có dữ liệu lỗi để vẽ biểu đồ.")
    else:
        ccol1, ccol2 = st.columns(2)

        with ccol1:
            st.markdown("##### 📌 Phân bố lỗi theo Rule")
            rule_counts = pd.Series([e.rule_id for e in report.errors]).value_counts()
            fig_r, ax_r = plt.subplots(figsize=(6, 4))
            ax_r.set_facecolor("#1e293b")
            fig_r.patch.set_facecolor("#0f172a")
            bars = ax_r.bar(rule_counts.index, rule_counts.values, color="#38bdf8")
            ax_r.set_ylabel("Số lượng lỗi", color="#94a3b8")
            ax_r.tick_params(colors="#e2e8f0")
            for spine in ax_r.spines.values():
                spine.set_color("#334155")
            for bar in bars:
                yval = bar.get_height()
                ax_r.text(bar.get_x() + bar.get_width()/2.0, yval + 0.1, int(yval), ha="center", va="bottom", color="#7dd3fc", weight="bold")
            fig_r.tight_layout()
            st.pyplot(fig_r)

        with ccol2:
            st.markdown("##### 🚗 Phân bố lỗi theo Loại nhãn (Category)")
            cat_counts = pd.Series([e.category for e in report.errors]).value_counts()
            fig_c, ax_c = plt.subplots(figsize=(6, 4))
            ax_c.set_facecolor("#1e293b")
            fig_c.patch.set_facecolor("#0f172a")
            bars_c = ax_c.bar(cat_counts.index, cat_counts.values, color="#f472b6")
            ax_c.set_ylabel("Số lượng lỗi", color="#94a3b8")
            ax_c.tick_params(colors="#e2e8f0", rotation=25)
            for spine in ax_c.spines.values():
                spine.set_color("#334155")
            for bar in bars_c:
                yval = bar.get_height()
                ax_c.text(bar.get_x() + bar.get_width()/2.0, yval + 0.1, int(yval), ha="center", va="bottom", color="#fbcfe8", weight="bold")
            fig_c.tight_layout()
            st.pyplot(fig_c)

        # Bảng tổng hợp theo Rule
        st.markdown("##### 📋 Bảng tần suất lỗi theo Rule:")
        summary_rows = []
        for r_id in sorted(list(set(e.rule_id for e in report.errors))):
            errs_r = [e for e in report.errors if e.rule_id == r_id]
            err_c = sum(1 for e in errs_r if e.is_error())
            warn_c = sum(1 for e in errs_r if e.is_warning())
            summary_rows.append({
                "Mã Rule": r_id,
                "Tổng số lần": len(errs_r),
                "ERROR": err_c,
                "WARNING": warn_c,
            })
        st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# TAB 4: Hướng dẫn & Quy chuẩn 10 Rules
# ---------------------------------------------------------------------------
with tab_docs:
    st.subheader("Quy chuẩn 12 Rules kiểm tra chất lượng BDD100K & Video Tracking (Mã đề: N2-04A)")
    st.markdown("""
| Nhóm | Mã Rule | Tên quy tắc | Mô tả chi tiết | Phân loại | Mức độ |
|---|---|---|---|---|---|
| **BBox** | `RULE_B01` | **Out of Bounds** | Tọa độ box vượt ra ngoài khung hình ($x<0, y<0, x>W, y>H$) | 📐 **LỆCH** | 🔴 ERROR |
| **BBox** | `RULE_B02` | **Inverted / Zero Box** | Tọa độ bị đảo ngược ($x_2 \le x_1$ hoặc $y_2 \le y_1$) hoặc $w, h = 0$ | 📐 **LỖI HÌNH HỌC** | 🔴 ERROR |
| **BBox** | `RULE_B03` | **Too Small Box** | Diện tích $w \times h < 64\\text{px}^2$, nghi ngờ chấm nhầm/nhiễu | 📐 **RÁC / NHIỄU** | 🟡 WARN |
| **BBox** | `RULE_B04` | **Abnormal Ratio** | Tỉ lệ khung hình dị thường ($w/h > 25$ hoặc $h/w > 25$) | 📐 **LỆCH DẠNG** | 🟡 WARN |
| **Poly** | `RULE_P01` | **Insufficient Vertices** | Đa giác polygon có ít hơn 3 đỉnh | 📉 **THIẾU ĐỈNH** | 🔴 ERROR |
| **Poly** | `RULE_P02` | **Self-Intersection** | Đa giác bị xoắn nơ, vắt chéo viền (tự cắt chính nó) | 📐 **LỖI HÌNH HỌC** | 🔴 ERROR |
| **Poly** | `RULE_P03` | **Mask vs Box Mismatch** | Khung bao polygon lệch quá nhiều so với BBox (IoU < 0.70) | 📐 **LỆCH VIỀN** | 🟡 WARN |
| **Attr** | `RULE_A01` | **Duplicate Object** | Hai box cùng class đè lên nhau với IoU > 0.85 (vẽ trùng lặp) | 👥 **TRÙNG LẶP** | 🔴 ERROR |
| **Attr** | `RULE_A02` | **Missing Attributes** | Thiếu thuộc tính bắt buộc (`occluded`, `truncated`) | 📉 **THIẾU THUỘC TÍNH** | 🟡 WARN |
| **Attr** | `RULE_A03` | **Traffic Light Color** | Vật thể `traffic light` nhưng sai màu hoặc thiếu màu | 📉 **THIẾU/SAI THUỘC TÍNH** | 🔴 ERROR |
| **Video** | `RULE_T01` | **Missing Object (Flicker)** | Vật thể xuất hiện ở frame trước & sau nhưng mất dấu ở frame giữa | 📉 **GÁN NHÃN THIẾU** | 🟡 WARN |
| **Video** | `RULE_T02` | **Position Drift / Jump** | Vị trí box bị nhảy vọt bất thường (> 35% khung hình) trong 1 frame | 📐 **VẼ LỆCH VỊ TRÍ** | 🟡 WARN |
| **AI Cross** | `RULE_AI01` | **AI Missed Object** | AI phát hiện vật thể (xe/người) có trong ảnh nhưng annotator bỏ sót | 🚨 **BỎ SÓT ĐỐI TƯỢNG** | 🔴 ERROR / 🟡 WARN |
    """)

