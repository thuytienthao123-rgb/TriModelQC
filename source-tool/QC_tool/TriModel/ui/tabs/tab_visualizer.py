from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
import streamlit as st
import streamlit.components.v1 as components
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from PIL import Image

from qc.models import QCReport, QCError, FrameData, BBox2D, Polygon2D, LabeledObject
from ui.constants import RULE_SUGGESTIONS
from ui.io_utils import find_matching_image, load_image
from ui.ai_assistant import detect_missed_objects
from ui.i18n import get_current_lang
from ui.manual_editor import render_manual_editor_panel


def _predict_salient_contour(
    img_pil: Image.Image,
    bx: BBox2D,
) -> Optional[List[Tuple[float, float]]]:
    """Dùng OpenCV trích xuất đường viền thực tế bên trong BBox để hỗ trợ sinh Polygon chuẩn."""
    try:
        import cv2

        x1 = max(0, int(bx.x1))
        y1 = max(0, int(bx.y1))
        x2 = min(img_pil.width, int(bx.x2))
        y2 = min(img_pil.height, int(bx.y2))
        if (x2 - x1) < 8 or (y2 - y1) < 8:
            return None

        np_img = np.array(img_pil.crop((x1, y1, x2, y2)))
        if np_img.ndim != 3:
            return None

        gray = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 40, 140)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None

        largest_c = max(contours, key=cv2.contourArea)
        if len(largest_c) < 3:
            return None

        # Làm mượt đa giác (Douglas-Peucker)
        epsilon = 0.02 * cv2.arcLength(largest_c, True)
        approx = cv2.approxPolyDP(largest_c, epsilon, True)
        if len(approx) < 3:
            approx = largest_c

        vertices: List[Tuple[float, float]] = []
        for pt in approx:
            px, py = pt[0]
            vertices.append((float(x1 + px), float(y1 + py)))

        return vertices
    except Exception:
        return None


def render_tab_visualizer(
    report: QCReport,
    frames: List[FrameData],
    uploaded_image_map: Dict[str, Any],
    ai_model: Any,
    enable_ai_check: bool,
    ai_conf: float,
    is_dark: bool,
    ensemble_mode: str = "majority",
):
    """Render Tab 2: Scale Nucleus Split-Workspace (Canvas + Kính Lúp Focus Loupe + Real-time Inspector)."""
    lang = get_current_lang()

    # Palette colors for matplotlib styling based on theme
    if is_dark:
        bg_main = "#080c14"
        bg_header = "#0f1624"
        border_c = "#1e293b"
        text_sub = "#94a3b8"
    else:
        bg_main = "#f8fafc"
        bg_header = "#ffffff"
        border_c = "#e2e8f0"
        text_sub = "#475569"

    # Header Tab 2 & Hotkey Badge
    if lang == "vi":
        header_pre = "HỆ THỐNG KIỂM TOÁN KHÔNG GIAN // SCALE NUCLEUS"
        header_title = "Soi Chi Tiết Lỗi Hình Học & Kính Lúp Độ Phân Giải Cao"
        hotkey_prev = "[A / ←] Trước"
        hotkey_next = "[D / →] Tiếp"
        hotkey_zoom = "[Z] Thu phóng"
        btn_prev_lbl = "◀ Lỗi trước (A)"
        btn_next_lbl = "Lỗi tiếp ▶ (D)"
        help_prev = "Phím tắt: A hoặc Phím Mũi tên Trái"
        help_next = "Phím tắt: D hoặc Phím Mũi tên Phải"
        lbl_instances = "VẬT THỂ"
        lbl_defects = "LỖI"
        lbl_warn = "CẢNH BÁO"
        lbl_ai_missed = "AI BỎ SÓT"
        lbl_loupe_toggle = "🔍 Kính Lúp Cận Cảnh"
        help_loupe = "Tự động căn góc nhìn và phóng to trực diện vào vật thể / lỗi vi phạm đang chọn"
        lbl_zoom_slider = "Độ phóng đại viền:"
        zoom_opts = ["1.5x (Rộng)", "2.5x (Chuẩn)", "4.0x (Cực đại)"]
        cap_overview = "🌐 Đang hiển thị toàn cảnh khung hình. Bật Kính Lúp để soi chi tiết từng pixel viền."
    else:
        header_pre = "SCALE NUCLEUS // SPATIAL AUDIT WORKSPACE"
        header_title = "Spatial Defect Inspection & High-Precision Loupe"
        hotkey_prev = "[A / ←] Prev"
        hotkey_next = "[D / →] Next"
        hotkey_zoom = "[Z] Zoom"
        btn_prev_lbl = "◀ Prev Defect (A)"
        btn_next_lbl = "Next Defect ▶ (D)"
        help_prev = "Hotkey: A or Left Arrow"
        help_next = "Hotkey: D or Right Arrow"
        lbl_instances = "INSTANCES"
        lbl_defects = "DEFECTS"
        lbl_warn = "WARN"
        lbl_ai_missed = "MISSED"
        lbl_loupe_toggle = "🔍 High-Precision Focus Loupe"
        help_loupe = "Automatically frames and zooms directly into selected defect instance"
        lbl_zoom_slider = "Loupe Zoom Factor:"
        zoom_opts = ["1.5x (Wide)", "2.5x (Standard)", "4.0x (Extreme)"]
        cap_overview = "🌐 Full overview mode. Enable Focus Loupe to inspect contour pixel boundaries."

    # Khởi tạo mặc định các lớp hiển thị và kính lúp nếu chưa có trong session_state
    if "scale_show_err" not in st.session_state:
        st.session_state["scale_show_err"] = True
    if "scale_show_warn" not in st.session_state:
        st.session_state["scale_show_warn"] = True
    if "scale_show_valid" not in st.session_state:
        st.session_state["scale_show_valid"] = True
    if "scale_show_labels" not in st.session_state:
        st.session_state["scale_show_labels"] = True
    if "scale_show_grid" not in st.session_state:
        st.session_state["scale_show_grid"] = False
    if "scale_focus_zoom" not in st.session_state:
        st.session_state["scale_focus_zoom"] = False
    if "scale_zoom_factor" not in st.session_state or st.session_state["scale_zoom_factor"] not in zoom_opts:
        cur_z = st.session_state.get("scale_zoom_factor", "")
        matched = next((opt for opt in zoom_opts if opt[:4] in cur_z), zoom_opts[0])
        st.session_state["scale_zoom_factor"] = matched

    st.markdown(f"""
    <div style="margin-bottom: 12px; display: flex; justify-content: space-between; align-items: flex-end; flex-wrap: wrap; gap: 10px;">
        <div>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #00e5ff; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;">{header_pre}</div>
            <h3 style="margin: 2px 0 0 0; color: #f8fafc; font-size: 1.25rem;">{header_title}</h3>
        </div>
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.74rem; color: #cbd5e1; background: #0f1624; padding: 4px 10px; border-radius: 6px; border: 1px solid #1e293b; display: flex; gap: 8px;">
            <span>⌨️ Hotkeys:</span>
            <span style="color: #00e5ff; font-weight: 700;">{hotkey_prev}</span>
            <span style="color: #818cf8; font-weight: 700;">{hotkey_next}</span>
            <span style="color: #fbbf24; font-weight: 700;">{hotkey_zoom}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Injected Javascript keyboard listener for fast reviewer hotkeys
    components.html("""
    <script>
    if (!window.qcHotkeysBound) {
        window.qcHotkeysBound = true;
        window.parent.document.addEventListener('keydown', function(e) {
            if (e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA')) {
                return;
            }
            if (e.key === 'a' || e.key === 'A' || e.key === 'ArrowLeft') {
                const btns = window.parent.document.querySelectorAll('button');
                for (let b of btns) {
                    if (b.innerText && (b.innerText.includes('Prev') || b.innerText.includes('trước')) && !b.disabled) {
                        b.click();
                        break;
                    }
                }
            } else if (e.key === 'd' || e.key === 'D' || e.key === 'ArrowRight') {
                const btns = window.parent.document.querySelectorAll('button');
                for (let b of btns) {
                    if (b.innerText && (b.innerText.includes('Next') || b.innerText.includes('tiếp')) && !b.disabled) {
                        b.click();
                        break;
                    }
                }
            }
        });
    }
    </script>
    """, height=0, width=0)

    frame_names_all = [f.name for f in frames]
    frame_error_map: Dict[str, List[QCError]] = {}
    for err in report.errors:
        frame_error_map.setdefault(err.frame_name, []).append(err)

    error_frame_names = [f.name for f in frames if f.name in frame_error_map and len(frame_error_map[f.name]) > 0]

    if "active_frame_name" not in st.session_state or st.session_state["active_frame_name"] not in frame_names_all:
        st.session_state["active_frame_name"] = error_frame_names[0] if error_frame_names else frame_names_all[0]

    # Split workspace: Left 68% for Canvas + Toolbar, Right 32% for Scale Nucleus Inspector
    st.markdown("""
    <style>
    /* Cố định khung ảnh visualizer ở vị trí tự nhiên khi cuộn trang */
    div[data-testid="column"]:nth-of-type(1) {
        position: sticky;
        top: 3rem;
        align-self: flex-start;
    }
    /* Thanh cuộn chuyên dụng cho inspector sidebar */
    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        overflow-y: auto !important;
        scrollbar-width: thin;
    </style>
    """, unsafe_allow_html=True)

    loaded_img = None
    col_workspace, col_inspector = st.columns([6.8, 3.2])

    with col_workspace:
        # Navigation Bar above Canvas
        nav_col1, nav_col2, nav_col3 = st.columns([2.5, 5, 2.5])
        with nav_col1:
            prev_disabled = len(error_frame_names) == 0
            if st.button(btn_prev_lbl, use_container_width=True, disabled=prev_disabled, help=help_prev):
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
            if st.button(btn_next_lbl, use_container_width=True, disabled=next_disabled, help=help_next):
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
                    lbl_err_tag = "LỖI" if lang == "vi" else "ERR"
                    lbl_warn_tag = "CẢNH BÁO" if lang == "vi" else "WARN"
                    return f"🚨 {fname} (🔴 {n_err} {lbl_err_tag} | 🟡 {n_warn} {lbl_warn_tag})"
                elif n_err > 0:
                    lbl_err_tag = "LỖI" if lang == "vi" else "ERR"
                    return f"🚨 {fname} (🔴 {n_err} {lbl_err_tag})"
                elif n_warn > 0:
                    lbl_warn_tag = "CẢNH BÁO" if lang == "vi" else "WARN"
                    return f"⚠️ {fname} (🟡 {n_warn} {lbl_warn_tag})"
                else:
                    lbl_ok_tag = "ĐẠT CHUẨN" if lang == "vi" else "VERIFIED"
                    return f"🟢 {fname} ({lbl_ok_tag})"

            curr_f = st.session_state.get("active_frame_name", frame_names_all[0])
            curr_idx = frame_names_all.index(curr_f) if curr_f in frame_names_all else 0
            frame_sel_label = "Chọn khung hình:" if lang == "vi" else "Select Frame:"
            selected_frame_name = st.selectbox(
                frame_sel_label,
                options=frame_names_all,
                index=curr_idx,
                format_func=format_frame_label,
                key="active_frame_selector_scale",
                label_visibility="collapsed",
            )
            st.session_state["active_frame_name"] = selected_frame_name

        selected_frame = next((f for f in frames if f.name == selected_frame_name), None)

        if selected_frame:
            matched_img_file = find_matching_image(selected_frame_name, uploaded_image_map)
            loaded_img = load_image(matched_img_file)

            missed_objects: List[Dict[str, Any]] = []
            if enable_ai_check and loaded_img is not None and ai_model is not None:
                ai_cache = st.session_state.setdefault("qc_ai_missed_cache", {})
                if selected_frame_name in ai_cache:
                    missed_objects = ai_cache[selected_frame_name]
                else:
                    missed_objects = detect_missed_objects(
                        loaded_img,
                        selected_frame.objects,
                        ai_model,
                        conf_thresh=ai_conf,
                        ensemble_mode=ensemble_mode,
                    )
                    ai_cache[selected_frame_name] = missed_objects

                # Tự động đồng bộ lỗi MISSED của frame này vào báo cáo QC
                cur_rep = st.session_state.get("qc_report")
                if cur_rep is not None and missed_objects:
                    cur_rep.errors = [e for e in cur_rep.errors if not (e.rule_id == "RULE_AI01" and e.frame_name == selected_frame_name)]
                    for m_idx, m_obj in enumerate(missed_objects, start=1):
                        mbx = m_obj["box2d"]
                        m_cat = m_obj["category"]
                        m_conf = m_obj.get("confidence", 0.8)
                        err_msg = (
                            f"MISSED: Phát hiện [{m_cat}] bị bỏ sót tại [{int(mbx.x1)}, {int(mbx.y1)}, {int(mbx.x2)}, {int(mbx.y2)}] (độ tin cậy: {m_conf:.0%})"
                            if lang == "vi"
                            else f"MISSED: Unlabeled [{m_cat}] detected at [{int(mbx.x1)}, {int(mbx.y1)}, {int(mbx.x2)}, {int(mbx.y2)}] (confidence: {m_conf:.0%})"
                        )
                        cur_rep.add(QCError(
                            rule_id="RULE_AI01",
                            severity="ERROR" if m_conf >= 0.60 else "WARNING",
                            frame_name=selected_frame_name,
                            object_id=f"missed_{m_idx:02d}",
                            category=m_cat,
                            message=err_msg,
                        ))

            cur_frame_errs = frame_error_map.get(selected_frame_name, [])
            n_f_err = sum(1 for e in cur_frame_errs if e.is_error())
            n_f_warn = sum(1 for e in cur_frame_errs if e.is_warning())

            # Scale Nucleus Frame Status Header & Zoom Controls Toolbar
            ai_pill = f'<span style="background: rgba(236,72,153,0.15); color: #ec4899; border: 1px solid rgba(236,72,153,0.3); padding: 2px 8px; border-radius: 4px; font-weight: 700; font-size: 0.72rem;">🤖 {len(missed_objects)} {lbl_ai_missed}</span>' if (enable_ai_check and missed_objects) else ''
            st.markdown(f"""
            <div style="background: #0f1624; border: 1px solid #1e293b; border-radius: 8px; padding: 8px 14px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; color: #f8fafc;">
                    FRAME: <strong style="color: #00e5ff;">{selected_frame_name}</strong>
                    <span style="color: #64748b; margin-left: 8px;">({selected_frame.width}×{selected_frame.height}px)</span>
                </div>
                <div style="display: flex; gap: 6px; align-items: center; flex-wrap: wrap;">
                    <span style="background: rgba(0,229,255,0.12); color: #00e5ff; border: 1px solid rgba(0,229,255,0.3); padding: 2px 8px; border-radius: 4px; font-weight: 700; font-size: 0.72rem;">📦 {len(selected_frame.objects)} {lbl_instances}</span>
                    <span style="background: rgba(244,63,94,0.12); color: #f43f5e; border: 1px solid rgba(244,63,94,0.3); padding: 2px 8px; border-radius: 4px; font-weight: 700; font-size: 0.72rem;">🔴 {n_f_err} {lbl_defects}</span>
                    <span style="background: rgba(245,158,11,0.12); color: #fbbf24; border: 1px solid rgba(245,158,11,0.3); padding: 2px 8px; border-radius: 4px; font-weight: 700; font-size: 0.72rem;">🟡 {n_f_warn} {lbl_warn}</span>
                    {ai_pill}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Interactive Viewport Toolbar (Overview vs Focus Loupe Zoom)
            v_col1, v_col2 = st.columns([4.2, 5.8])
            with v_col1:
                is_focus_zoom = st.toggle(
                    lbl_loupe_toggle,
                    key="scale_focus_zoom",
                    help=help_loupe,
                )

            with v_col2:
                if is_focus_zoom:
                    zoom_factor = st.select_slider(
                        lbl_zoom_slider,
                        options=zoom_opts,
                        key="scale_zoom_factor",
                    )
                else:
                    st.caption(cap_overview)

            # Matplotlib Canvas styled for Scale Nucleus
            fig, ax = plt.subplots(figsize=(10.5, 6.2), dpi=105)
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
            sel_inspect_str = st.session_state.get("scale_inspector_obj_select", "")
            if sel_inspect_str and not sel_inspect_str.startswith("🔍"):
                focus_id = sel_inspect_str.split()[0]
            ai_predicted_poly = st.session_state.get("scale_ai_predicted_poly", None)

            focused_obj_target: Optional[LabeledObject] = None

            for obj in selected_frame.objects:
                obj_errs = obj_err_map.get(obj.id, [])
                has_error = any(e.is_error() for e in obj_errs)
                has_warn = any(e.is_warning() for e in obj_errs)
                is_focused = (focus_id is not None and obj.id == focus_id)

                if is_focused:
                    focused_obj_target = obj
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
                        ax.axvline(cx, color="#00e5ff", linestyle=":", linewidth=1.2, alpha=0.85)
                        ax.axhline(cy, color="#00e5ff", linestyle=":", linewidth=1.2, alpha=0.85)

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

            # Render AI Predicted Polygon if generated
            if ai_predicted_poly and focus_id:
                ai_patch = patches.Polygon(
                    ai_predicted_poly,
                    closed=True,
                    linewidth=2.2,
                    edgecolor="#00e5ff",
                    facecolor="rgba(0, 229, 255, 0.3)",
                    linestyle="-.",
                )
                ax.add_patch(ai_patch)
                ax.text(
                    ai_predicted_poly[0][0],
                    ai_predicted_poly[0][1] - 8,
                    "🪄 AI SAM2 CONTOUR",
                    color="#080c14",
                    fontsize=8.5,
                    weight="bold",
                    bbox=dict(facecolor="#00e5ff", edgecolor="#00e5ff", boxstyle="round,pad=0.22", alpha=0.95),
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
                            f"MISSED: {m_cat} ({m_conf:.0%})",
                            color="#ec4899",
                            fontsize=8.0,
                            weight="bold",
                            bbox=dict(facecolor="#080c14", edgecolor="#ec4899", boxstyle="round,pad=0.22", alpha=0.95),
                        )

            # Handle Auto-Focus Zoom Viewport
            if is_focus_zoom:
                zoom_str = str(st.session_state.get("scale_zoom_factor", ""))
                if "4.0x" in zoom_str:
                    zoom_val = 4.0
                elif "2.5x" in zoom_str:
                    zoom_val = 2.5
                else:
                    zoom_val = 1.5

                # 1. Xác định tâm phóng đại (Focus Center)
                hud_target_name = ""
                if focused_obj_target is not None:
                    if focused_obj_target.box2d is not None:
                        bx_t = focused_obj_target.box2d
                        cx = (bx_t.x1 + bx_t.x2) / 2.0
                        cy = (bx_t.y1 + bx_t.y2) / 2.0
                    elif focused_obj_target.poly2d is not None and getattr(focused_obj_target.poly2d, "vertices", None):
                        xs = [v[0] for v in focused_obj_target.poly2d.vertices]
                        ys = [v[1] for v in focused_obj_target.poly2d.vertices]
                        cx = (min(xs) + max(xs)) / 2.0
                        cy = (min(ys) + max(ys)) / 2.0
                    else:
                        cx = canvas_w / 2.0
                        cy = canvas_h / 2.0
                    hud_target_name = f"Object: {focused_obj_target.id} ({focused_obj_target.category})"
                elif cur_frame_errs:
                    first_err = cur_frame_errs[0]
                    first_oid = first_err.object_id.split("&")[0].strip()
                    err_obj = next((o for o in selected_frame.objects if o.id == first_oid), None)
                    if err_obj is not None and err_obj.box2d is not None:
                        cx = (err_obj.box2d.x1 + err_obj.box2d.x2) / 2.0
                        cy = (err_obj.box2d.y1 + err_obj.box2d.y2) / 2.0
                        hud_target_name = f"Defect: {err_obj.id} ({first_err.rule_id})"
                    else:
                        cx = canvas_w / 2.0
                        cy = canvas_h / 2.0
                        hud_target_name = "TÂM KHUNG HÌNH" if lang == "vi" else "FRAME CENTER"
                elif missed_objects:
                    mbx = missed_objects[0]["box2d"]
                    cx = (mbx.x1 + mbx.x2) / 2.0
                    cy = (mbx.y1 + mbx.y2) / 2.0
                    hud_target_name = f"MISSED: {missed_objects[0]['category']}"
                else:
                    cx = canvas_w / 2.0
                    cy = canvas_h / 2.0
                    hud_target_name = "TÂM KHUNG HÌNH" if lang == "vi" else "FRAME CENTER"

                # 2. Tính toán biên cửa sổ phóng đại theo đúng tỉ lệ quang học (Optical Zoom)
                half_w = (canvas_w / zoom_val) / 2.0
                half_h = (canvas_h / zoom_val) / 2.0

                x_min = cx - half_w
                x_max = cx + half_w
                if x_min < 0:
                    x_max = min(float(canvas_w), x_max + (0.0 - x_min))
                    x_min = 0.0
                if x_max > canvas_w:
                    x_min = max(0.0, x_min - (x_max - canvas_w))
                    x_max = float(canvas_w)

                y_min = cy - half_h
                y_max = cy + half_h
                if y_min < 0:
                    y_max = min(float(canvas_h), y_max + (0.0 - y_min))
                    y_min = 0.0
                if y_max > canvas_h:
                    y_min = max(0.0, y_min - (y_max - canvas_h))
                    y_max = float(canvas_h)

                # Invert Y để trục tọa độ phù hợp với hệ pixel ảnh (0 ở trên, canvas_h ở dưới)
                ax.set_xlim(x_min, x_max)
                ax.set_ylim(y_max, y_min)

                # Zoom HUD Chip hiển thị thông số phóng đại trên canvas
                hud_x = x_min + (x_max - x_min) * 0.02
                hud_y = y_min + (y_max - y_min) * 0.06
                ax.text(
                    hud_x,
                    hud_y,
                    f"🔍 FOCUS LOUPE {zoom_val:.1f}x · {hud_target_name}",
                    color="#00e5ff",
                    fontsize=8.5,
                    fontfamily="monospace",
                    weight="bold",
                    bbox=dict(facecolor="#080c14", edgecolor="#00e5ff", boxstyle="round,pad=0.3", alpha=0.95),
                )

            # Lưới tọa độ: chỉ hiển thị khi người dùng tick chọn 'Lưới tọa độ' (độc lập hoàn toàn với kính lúp)
            if show_grid_ly:
                ax.grid(True, linestyle=":", alpha=0.35, color=border_c)
                ax.tick_params(colors=text_sub, labelsize=7.5)
            else:
                ax.grid(False)
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
        with st.container(height=840, border=True):
            inspector_title = "🎯 BẢNG SOI ĐỐI TƯỢNG & KÍNH LÚP" if lang == "vi" else "🎯 NUCLEUS INSPECTOR & LOUPE"
            st.markdown(f"""
            <div style="background: #0f1624; border: 1px solid #1e293b; border-radius: 10px; padding: 12px 16px; margin-bottom: 12px; border-top: 3px solid #00e5ff;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; font-weight: 800; color: #00e5ff; letter-spacing: 0.05em;">
                        {inspector_title}
                    </div>
                    <span style="font-size: 0.7rem; color: #00e5ff; font-family: 'JetBrains Mono', monospace; background: rgba(0,229,255,0.15); padding: 2px 6px; border-radius: 4px; border: 1px solid rgba(0,229,255,0.3);">SIDEBAR SCROLL</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if selected_frame:
                obj_lookup = {o.id: o for o in selected_frame.objects}
                cur_frame_errs = frame_error_map.get(selected_frame_name, [])

                # Filter Mode for Inspector
                f_col1, f_col2 = st.columns([4, 6])
                with f_col1:
                    filter_opts = (
                        ["Tất cả", "🚨 Chỉ lỗi vi phạm", "📉 Chỉ Polygon"]
                        if lang == "vi"
                        else ["All", "🚨 Defects Only", "📉 Polygons Only"]
                    )
                    inst_filter_mode = st.selectbox(
                        "Bộ lọc:" if lang == "vi" else "Filter:",
                        options=filter_opts,
                        index=0,
                        key="scale_inspector_filter_mode",
                    )

                filtered_objs = selected_frame.objects
                if "lỗi" in inst_filter_mode.lower() or "defect" in inst_filter_mode.lower():
                    defect_ids = set()
                    for e in cur_frame_errs:
                        for s in e.object_id.split("&"):
                            defect_ids.add(s.strip())
                    filtered_objs = [o for o in selected_frame.objects if o.id in defect_ids]
                elif "polygon" in inst_filter_mode.lower():
                    filtered_objs = [o for o in selected_frame.objects if o.poly2d is not None]

                # Object Selector
                all_inst_str = "🔍 TẤT CẢ VẬT THỂ" if lang == "vi" else "🔍 ALL INSTANCES"
                obj_choices = [all_inst_str] + [f"{o.id} ({o.category})" for o in filtered_objs]
                with f_col2:
                    sel_obj_str = st.selectbox(
                        "Chọn đối tượng soi:" if lang == "vi" else "Select Instance:",
                        options=obj_choices,
                        index=0,
                        key="scale_inspector_obj_select",
                        help="Chọn một đối tượng để kiểm tra chi tiết tọa độ, hình học và thuộc tính" if lang == "vi" else "Inspect detailed coordinates, geometry, and attributes",
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
                        status_badge = '<span class="badge-err">🔴 PHÁT HIỆN LỖI</span>' if lang == "vi" else '<span class="badge-err">🔴 DEFECT DETECTED</span>'
                    elif has_w:
                        status_badge = '<span class="badge-warn">🟡 CẢNH BÁO KIỂM TRA</span>' if lang == "vi" else '<span class="badge-warn">🟡 AUDIT WARNING</span>'
                    else:
                        status_badge = '<span class="badge-ok">🟢 ĐẠT CHUẨN</span>' if lang == "vi" else '<span class="badge-ok">🟢 PASS SPEC</span>'

                    st.markdown(f"""
                    <div style="background: #131b2e; border: 1px solid #1e293b; border-radius: 8px; padding: 12px; margin-bottom: 10px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                            <div>
                                <strong style="color: #f8fafc; font-size: 0.95rem;">{target_obj.id}</strong>
                                <span style="color: #00e5ff; font-size: 0.8rem; margin-left: 6px; font-family: 'JetBrains Mono', monospace;">[{target_obj.category}]</span>
                            </div>
                            {status_badge}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Defect Loupe Mini Crop Preview (Kính lúp điểm ảnh trong inspector)
                    if loaded_img is not None and target_obj.box2d:
                        bx = target_obj.box2d
                        crop_x1 = max(0, int(bx.x1) - 15)
                        crop_y1 = max(0, int(bx.y1) - 15)
                        crop_x2 = min(loaded_img.width, int(bx.x2) + 15)
                        crop_y2 = min(loaded_img.height, int(bx.y2) + 15)
                        if (crop_x2 > crop_x1) and (crop_y2 > crop_y1):
                            cropped_patch = loaded_img.crop((crop_x1, crop_y1, crop_x2, crop_y2))
                            loupe_crop_title = "🔎 Kính Lúp Điểm Ảnh Cận Cảnh" if lang == "vi" else "🔎 High-Res Pixel Loupe"
                            with st.expander(loupe_crop_title, expanded=True):
                                caption_crop = (
                                    f"Vùng ảnh thực tế: [{crop_x1}, {crop_y1}, {crop_x2}, {crop_y2}] ({cropped_patch.width}×{cropped_patch.height}px)"
                                    if lang == "vi"
                                    else f"Crop region: [{crop_x1}, {crop_y1}, {crop_x2}, {crop_y2}] ({cropped_patch.width}×{cropped_patch.height}px)"
                                )
                                st.image(
                                    cropped_patch,
                                    caption=caption_crop,
                                    use_container_width=True,
                                )

                    # Geometry Telemetry
                    if target_obj.box2d:
                        bx = target_obj.box2d
                        geo_title = "📐 Tọa Độ & Hình Học Không Gian" if lang == "vi" else "📐 Spatial Geometry"
                        st.markdown(f"""
                        <div style="background: #0f1624; border: 1px solid #1e293b; border-radius: 8px; padding: 10px 12px; margin-bottom: 10px;">
                            <div style="font-size: 0.72rem; color: #94a3b8; font-weight: 700; text-transform: uppercase; margin-bottom: 6px;">{geo_title}</div>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; font-size: 0.78rem; font-family: 'JetBrains Mono', monospace;">
                                <div>x1, y1: <strong style="color: #f1f5f9;">{bx.x1:.1f}, {bx.y1:.1f}</strong></div>
                                <div>x2, y2: <strong style="color: #f1f5f9;">{bx.x2:.1f}, {bx.y2:.1f}</strong></div>
                                <div>Dimension: <strong style="color: #f1f5f9;">{bx.width:.1f}×{bx.height:.1f}</strong></div>
                                <div>Aspect W/H: <strong style="color: #00e5ff;">{bx.aspect_ratio:.2f}</strong></div>
                                <div>Area: <strong style="color: #f1f5f9;">{bx.area:.0f} px²</strong></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    # SAM2 / AI Contour Auto-Predictor
                    if loaded_img is not None and target_obj.box2d:
                        ai_c1, ai_c2 = st.columns([6, 4])
                        with ai_c1:
                            btn_sam_lbl = "🪄 Sinh Đa Giác Tự Động (SAM2)" if lang == "vi" else "🪄 Generate SAM2 Contour"
                            help_sam = "Tự động dò tìm đường viền vật thể thực tế trong ảnh để so sánh mặt nạ" if lang == "vi" else "Auto-extract salient contour boundary to compare mask"
                            if st.button(btn_sam_lbl, use_container_width=True, help=help_sam):
                                predicted_pts = _predict_salient_contour(loaded_img, target_obj.box2d)
                                if predicted_pts:
                                    st.session_state["scale_ai_predicted_poly"] = predicted_pts
                                    toast_sam = f"✅ Đã tạo mặt nạ gợi ý ({len(predicted_pts)} đỉnh) cho {target_obj.id}" if lang == "vi" else f"✅ Generated SAM2 contour ({len(predicted_pts)} vertices) for {target_obj.id}"
                                    st.toast(toast_sam, icon="🪄")
                                    st.rerun()
                                else:
                                    warn_sam = "Không thể trích xuất đường viền từ vùng ảnh này." if lang == "vi" else "Could not extract contour from this region."
                                    st.warning(warn_sam)
                        with ai_c2:
                            if st.session_state.get("scale_ai_predicted_poly"):
                                btn_clear_sam = "❌ Xóa gợi ý" if lang == "vi" else "❌ Clear Suggestion"
                                if st.button(btn_clear_sam, use_container_width=True):
                                    st.session_state["scale_ai_predicted_poly"] = None
                                    st.rerun()

                    # Attributes Telemetry
                    attrs = target_obj.attributes or {}
                    attr_header = "🏷️ Thuộc Tính Đối Tượng" if lang == "vi" else "🏷️ Attributes Metadata"
                    missing_str = "THIẾU" if lang == "vi" else "MISSING"
                    st.markdown(f"""
                    <div style="background: #0f1624; border: 1px solid #1e293b; border-radius: 8px; padding: 10px 12px; margin-bottom: 10px;">
                        <div style="font-size: 0.72rem; color: #94a3b8; font-weight: 700; text-transform: uppercase; margin-bottom: 6px;">{attr_header}</div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; font-size: 0.78rem; font-family: 'JetBrains Mono', monospace;">
                            <div>occluded: <strong style="color: {'#fbbf24' if attrs.get('occluded') else '#94a3b8'};">{attrs.get('occluded', missing_str)}</strong></div>
                            <div>truncated: <strong style="color: {'#fbbf24' if attrs.get('truncated') else '#94a3b8'};">{attrs.get('truncated', missing_str)}</strong></div>
                            <div>lightColor: <strong style="color: #00e5ff;">{attrs.get('trafficLightColor', 'none')}</strong></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Active Violations for this Object
                    if obj_errs:
                        vio_title = "🚨 CÁC VI PHẠM ĐANG CÓ:" if lang == "vi" else "🚨 ACTIVE VIOLATIONS:"
                        st.markdown(f"<div style='font-size: 0.75rem; color: #f43f5e; font-weight: 700; margin: 8px 0 4px 0;'>{vio_title}</div>", unsafe_allow_html=True)
                        for e in obj_errs:
                            default_rule_sugg = "Kiểm tra theo quy chuẩn BDD100K." if lang == "vi" else "Check BDD100K specification."
                            sugg = RULE_SUGGESTIONS.get(e.rule_id, default_rule_sugg)
                            lbl_fix_tag = "Cách sửa:" if lang == "vi" else "Fix:"
                            st.markdown(f"""
                            <div style="background: rgba(244,63,94,0.08); border: 1px solid rgba(244,63,94,0.3); border-radius: 6px; padding: 8px 10px; margin-bottom: 6px; font-size: 0.78rem;">
                                <div style="font-weight: 700; color: #f87171; font-family: 'JetBrains Mono', monospace;">{e.rule_id} · {e.severity}</div>
                                <div style="color: #e2e8f0; margin-top: 2px;">{e.message}</div>
                                <div style="color: #00e5ff; margin-top: 4px; font-size: 0.72rem;">💡 <strong>{lbl_fix_tag}</strong> {sugg}</div>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        success_obj_msg = "✅ Đối tượng đạt chuẩn toàn diện 15 bộ quy tắc." if lang == "vi" else "✅ Instance meets all 15 QA validation rules."
                        st.success(success_obj_msg)

                # Case 2: All Instances Summary
                else:
                    summary_hdr = "TỔNG HỢP KHUNG HÌNH" if lang == "vi" else "FRAME TELEMETRY SUMMARY"
                    summary_val = f"{len(selected_frame.objects)} Vật thể · {len(cur_frame_errs)} Lỗi phát hiện" if lang == "vi" else f"{len(selected_frame.objects)} Instances · {len(cur_frame_errs)} Defect Events"
                    st.markdown(f"""
                    <div style="background: #131b2e; border: 1px solid #1e293b; border-radius: 8px; padding: 12px; margin-bottom: 10px;">
                        <div style="font-size: 0.74rem; color: #94a3b8; font-weight: 700; text-transform: uppercase;">{summary_hdr}</div>
                        <div style="font-size: 1.1rem; font-weight: 800; color: #f8fafc; margin-top: 4px;">
                            {summary_val}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if cur_frame_errs:
                        frame_v_hdr = "VI PHẠM TRONG KHUNG HÌNH:" if lang == "vi" else "DEFECTS IN THIS FRAME:"
                        st.markdown(f"<div style='font-size: 0.75rem; color: #f43f5e; font-weight: 700; margin: 8px 0 4px 0;'>{frame_v_hdr}</div>", unsafe_allow_html=True)
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
                        st.success("🎉 Khung hình sạch 100%, không phát hiện lỗi nào." if lang == "vi" else "🎉 Clean frame. Zero defects detected.")

                # Bộ công cụ sửa tay nhãn trực tiếp dành cho Annotator & Reviewer
                img_w = loaded_img.width if loaded_img is not None else 1920
                img_h = loaded_img.height if loaded_img is not None else 1080
                cur_target = obj_lookup.get(chosen_id) if chosen_id else None
                render_manual_editor_panel(
                    target_obj=cur_target,
                    selected_frame=selected_frame,
                    frames=frames,
                    canvas_w=img_w,
                    canvas_h=img_h,
                    lang=lang,
                    loaded_img=loaded_img,
                )

                # Layer Visibility Toggles at the bottom of Inspector
                st.markdown("---")
                layers_title = "🎛️ Bật Tắt Lớp Hiển Thị" if lang == "vi" else "🎛️ Layer Visibility Controls"
                st.markdown(f"<div style='font-size: 0.72rem; color: #94a3b8; font-weight: 700; text-transform: uppercase; margin-bottom: 6px;'>{layers_title}</div>", unsafe_allow_html=True)
                t_col1, t_col2 = st.columns(2)
                with t_col1:
                    st.checkbox("🔴 " + ("Lỗi nghiêm trọng" if lang == "vi" else "Defects"), key="scale_show_err")
                    st.checkbox("🟡 " + ("Cảnh báo" if lang == "vi" else "Warnings"), key="scale_show_warn")
                    st.checkbox("🟢 " + ("Hộp hợp lệ" if lang == "vi" else "Valid BBox"), key="scale_show_valid")
                with t_col2:
                    st.checkbox("🏷️ " + ("Nhãn & ID" if lang == "vi" else "Labels & IDs"), key="scale_show_labels")
                    st.checkbox("📐 " + ("Lưới tọa độ" if lang == "vi" else "Pixel Grid"), key="scale_show_grid")
