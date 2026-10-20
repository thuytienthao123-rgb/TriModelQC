"""
manual_editor.py — Bộ công cụ sửa tay trực tiếp dành cho Annotator & Reviewer.
Tích hợp trực tiếp vào quy trình QC để người gán nhãn có thể:
1. Chỉnh sửa tọa độ BBox (x1, y1, x2, y2), đổi tên lớp, cập nhật thuộc tính occluded/truncated.
2. Xóa các box lỗi, vẽ thừa, trùng lặp hoặc vi phạm không cứu được.
3. Chấp nhận các đối tượng bị bỏ sót do Trợ lý AI (YOLOv8) phát hiện và nạp thẳng vào tập nhãn.
4. Thêm mới hoàn toàn đối tượng nhãn vào khung hình hiện tại.
5. Tự động chạy lại quy trình đối soát QC thời gian thực và cho phép xuất/tải file nhãn đã sửa.
"""

from __future__ import annotations
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import streamlit as st

from qc.models import FrameData, LabeledObject, BBox2D, Polygon2D, QCReport, QCError
from qc.engine import run_qc
from qc.reporter import (
    export_coco_json,
    export_yolo_zip_bytes,
    export_bdd100k_json,
    export_bdd100k_zip_bytes,
    export_anylabeling_json_single,
    export_anylabeling_zip_bytes,
    export_yolo_txt_single,
    export_cvat_xml_str,
)


STANDARD_BDD_CLASSES = [
    "car",
    "truck",
    "bus",
    "pedestrian",
    "rider",
    "traffic sign",
    "traffic light",
    "motorcycle",
    "bicycle",
    "train",
    "other vehicle",
    "trailer",
]


def _sync_missed_to_report(report: QCReport, lang: str = "vi") -> None:
    """Đồng bộ tất cả các vật thể bị bỏ sót (MISSED) từ cache AI vào QCReport để xuất hiện đầy đủ trong báo cáo."""
    if report is None:
        return
    # Loại bỏ các lỗi RULE_AI01 cũ để tránh trùng lặp
    report.errors = [e for e in report.errors if e.rule_id != "RULE_AI01"]
    ai_cache = st.session_state.get("qc_ai_missed_cache", {})
    for fname, missed_items in ai_cache.items():
        for m_idx, m_obj in enumerate(missed_items, start=1):
            mbx = m_obj["box2d"]
            m_cat = m_obj["category"]
            m_conf = m_obj.get("confidence", 0.8)
            err_msg = (
                f"MISSED: Phát hiện [{m_cat}] bị bỏ sót tại [{int(mbx.x1)}, {int(mbx.y1)}, {int(mbx.x2)}, {int(mbx.y2)}] (độ tin cậy: {m_conf:.0%})"
                if lang == "vi"
                else f"MISSED: Unlabeled [{m_cat}] detected at [{int(mbx.x1)}, {int(mbx.y1)}, {int(mbx.x2)}, {int(mbx.y2)}] (confidence: {m_conf:.0%})"
            )
            report.add(QCError(
                rule_id="RULE_AI01",
                severity="ERROR" if m_conf >= 0.60 else "WARNING",
                frame_name=fname,
                object_id=f"missed_{m_idx:02d}",
                category=m_cat,
                message=err_msg,
            ))


def _reevaluate_qc(frames: List[FrameData], lang: str = "vi"):
    """Chạy lại đối soát QC trên toàn bộ dữ liệu nhãn đã chỉnh sửa và bảo toàn các lỗi MISSED."""
    active_rules = st.session_state.get("qc_rules_snapshot", None)
    active_seq_rules = st.session_state.get("qc_active_seq_rules", None)
    report = run_qc(frames, rules=active_rules, sequence_rules=active_seq_rules)
    _sync_missed_to_report(report, lang=lang)
    st.session_state["qc_report"] = report
    st.session_state["qc_frames"] = frames


def auto_generate_polygon_for_object(img: Optional[Any], box: Optional[BBox2D]) -> Optional[Polygon2D]:
    """Tự động sinh viền Polygon từ ảnh và Bounding Box bằng OpenCV GrabCut + Contour approximation."""
    if box is None:
        return None
    try:
        import cv2
        import numpy as np
        from PIL import Image

        if img is not None:
            if isinstance(img, Image.Image):
                img_np = np.array(img.convert("RGB"))
                img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            elif isinstance(img, np.ndarray):
                img_bgr = img if len(img.shape) == 3 and img.shape[2] == 3 else cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            else:
                img_bgr = None
        else:
            img_bgr = None

        x1 = max(0.0, float(box.x1))
        y1 = max(0.0, float(box.y1))
        x2 = max(x1 + 1.0, float(box.x2))
        y2 = max(y1 + 1.0, float(box.y2))
        bw = x2 - x1
        bh = y2 - y1

        if img_bgr is not None and bw >= 8 and bh >= 8:
            h, w = img_bgr.shape[:2]
            ix1, iy1 = max(0, int(x1)), max(0, int(y1))
            ix2, iy2 = min(w, int(x2)), min(h, int(y2))
            crop_w, crop_h = ix2 - ix1, iy2 - iy1

            if crop_w >= 8 and crop_h >= 8:
                crop = img_bgr[iy1:iy2, ix1:ix2]
                mask = np.zeros(crop.shape[:2], np.uint8)
                bgd_model = np.zeros((1, 65), np.float64)
                fgd_model = np.zeros((1, 65), np.float64)
                rect = (max(1, int(crop_w * 0.05)), max(1, int(crop_h * 0.05)), max(2, int(crop_w * 0.90)), max(2, int(crop_h * 0.90)))
                cv2.grabCut(crop, mask, rect, bgd_model, fgd_model, 2, cv2.GC_INIT_WITH_RECT)
                bin_mask = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
                bin_mask = cv2.morphologyEx(bin_mask, cv2.MORPH_CLOSE, kernel)

                contours, _ = cv2.findContours(bin_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if contours:
                    largest = max(contours, key=cv2.contourArea)
                    if cv2.contourArea(largest) > (crop_w * crop_h * 0.08):
                        epsilon = 0.015 * cv2.arcLength(largest, True)
                        approx = cv2.approxPolyDP(largest, epsilon, True)
                        if len(approx) >= 3:
                            vertices = [(float(pt[0][0] + ix1), float(pt[0][1] + iy1)) for pt in approx]
                            return Polygon2D(vertices=vertices)
    except Exception:
        pass

    # Smooth Octagon fallback bám sát Bounding Box
    dx, dy = bw * 0.16, bh * 0.16
    return Polygon2D(vertices=[
        (float(x1 + dx), float(y1)),
        (float(x2 - dx), float(y1)),
        (float(x2), float(y1 + dy)),
        (float(x2), float(y2 - dy)),
        (float(x2 - dx), float(y2)),
        (float(x1 + dx), float(y2)),
        (float(x1), float(y2 - dy)),
        (float(x1), float(y1 + dy)),
    ])


def render_manual_editor_panel(
    target_obj: Optional[LabeledObject],
    selected_frame: FrameData,
    frames: List[FrameData],
    canvas_w: int = 1920,
    canvas_h: int = 1080,
    lang: str = "vi",
    loaded_img: Optional[Any] = None,
    ai_model: Optional[Any] = None,
    uploaded_image_map: Optional[Dict[str, Any]] = None,
    enable_ai_check: bool = True,
    ai_conf: float = 0.50,
    ensemble_mode: str = "nano",
):
    """Giao diện tương tác sửa tay trực tiếp dành cho Annotator trong Inspector."""
    if ai_model is None:
        ai_model = st.session_state.get("qc_ai_model")
    if uploaded_image_map is None:
        uploaded_image_map = st.session_state.get("qc_uploaded_image_map", {})
    if ai_conf is None:
        ai_conf = st.session_state.get("qc_ai_conf", 0.50)
    if ensemble_mode is None:
        ensemble_mode = st.session_state.get("qc_ai_ensemble_mode", "nano")

    st.markdown("---")
    panel_title = "🛠️ BỘ CÔNG CỤ SỬA TAY NHÃN (ANNOTATOR SUITE)" if lang == "vi" else "🛠️ MANUAL ANNOTATION & REMEDIATION SUITE"
    st.markdown(f"""
    <div style="background: var(--bg-card-sub); border: 1px solid var(--val-cyan); border-radius: 8px; padding: 10px 14px; margin-bottom: 12px;">
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; font-weight: 800; color: var(--val-cyan); display: flex; align-items: center; justify-content: space-between;">
            <span>{panel_title}</span>
            <span style="font-size: 0.68rem; background: rgba(0, 229, 255, 0.15); color: var(--val-cyan); padding: 2px 6px; border-radius: 4px;">INTERACTIVE</span>
        </div>
        <p style="font-size: 0.74rem; color: var(--text-sub); margin: 4px 0 0 0;">
            {"Sửa trực tiếp tọa độ, lớp hoặc xóa/thêm box vi phạm và đối soát lại ngay lập tức." if lang == "vi" else "Directly edit coordinates, re-classify, remove defects or add missing boxes in real-time."}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 1. SỬA ĐỐI TƯỢNG ĐANG CHỌN
    # -------------------------------------------------------------------------
    if target_obj is not None:
        edit_box_title = f"✏️ Chỉnh Sửa Đối Tượng: {target_obj.id}" if lang == "vi" else f"✏️ Edit Instance: {target_obj.id}"
        with st.expander(edit_box_title, expanded=True):
            # Chọn Category
            cur_cat = target_obj.category.lower() if target_obj.category else "car"
            cat_options = STANDARD_BDD_CLASSES.copy()
            if cur_cat not in cat_options:
                cat_options.insert(0, cur_cat)
            cat_idx = cat_options.index(cur_cat) if cur_cat in cat_options else 0

            new_cat = st.selectbox(
                "Phân loại đối tượng (Category):" if lang == "vi" else "Object Category:",
                options=cat_options,
                index=cat_idx,
                key=f"medit_cat_{selected_frame.name}_{target_obj.id}",
            )

            # Tọa độ BBox
            cur_bx = target_obj.box2d or BBox2D(x1=0.0, y1=0.0, x2=100.0, y2=100.0)
            c1, c2 = st.columns(2)
            with c1:
                new_x1 = st.number_input(
                    "x1 (Trái):" if lang == "vi" else "x1 (Left):",
                    value=float(round(cur_bx.x1, 1)),
                    step=1.0,
                    min_value=0.0,
                    max_value=float(canvas_w),
                    key=f"medit_x1_{selected_frame.name}_{target_obj.id}",
                )
                new_y1 = st.number_input(
                    "y1 (Trên):" if lang == "vi" else "y1 (Top):",
                    value=float(round(cur_bx.y1, 1)),
                    step=1.0,
                    min_value=0.0,
                    max_value=float(canvas_h),
                    key=f"medit_y1_{selected_frame.name}_{target_obj.id}",
                )
            with c2:
                new_x2 = st.number_input(
                    "x2 (Phải):" if lang == "vi" else "x2 (Right):",
                    value=float(round(cur_bx.x2, 1)),
                    step=1.0,
                    min_value=0.0,
                    max_value=float(canvas_w),
                    key=f"medit_x2_{selected_frame.name}_{target_obj.id}",
                )
                new_y2 = st.number_input(
                    "y2 (Dưới):" if lang == "vi" else "y2 (Bottom):",
                    value=float(round(cur_bx.y2, 1)),
                    step=1.0,
                    min_value=0.0,
                    max_value=float(canvas_h),
                    key=f"medit_y2_{selected_frame.name}_{target_obj.id}",
                )

            # Thuộc tính
            cur_attrs = target_obj.attributes or {}
            a1, a2 = st.columns(2)
            with a1:
                new_occ = st.checkbox(
                    "Bị che khuất (Occluded)" if lang == "vi" else "Occluded",
                    value=bool(cur_attrs.get("occluded", False)),
                    key=f"medit_occ_{selected_frame.name}_{target_obj.id}",
                )
            with a2:
                new_trunc = st.checkbox(
                    "Bị cắt xén (Truncated)" if lang == "vi" else "Truncated",
                    value=bool(cur_attrs.get("truncated", False)),
                    key=f"medit_trunc_{selected_frame.name}_{target_obj.id}",
                )

            # Phân đoạn Polygon (Segmentation)
            st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
            poly_label = "🔷 Viền Đa Giác (Polygon Segmentation):" if lang == "vi" else "🔷 Polygon Segmentation:"
            has_poly = target_obj.poly2d is not None and len(target_obj.poly2d.vertices) >= 3
            poly_desc = (
                f"Đã có viền ({len(target_obj.poly2d.vertices)} đỉnh)" if has_poly else "Chưa có viền đa giác"
            ) if lang == "vi" else (
                f"Active ({len(target_obj.poly2d.vertices)} vertices)" if has_poly else "No polygon contour"
            )
            st.markdown(f"<div style='font-size: 0.74rem; color: #94a3b8; font-weight: 600; margin-bottom: 4px;'>{poly_label} <span style='color: {'#10b981' if has_poly else '#64748b'}; font-weight: 700;'>{poly_desc}</span></div>", unsafe_allow_html=True)

            poly_btn1, poly_btn2 = st.columns(2)
            with poly_btn1:
                btn_auto_poly_lbl = "⚡ Tự Động Sinh Polygon" if lang == "vi" else "⚡ Auto-Gen Polygon"
                if st.button(btn_auto_poly_lbl, use_container_width=True, key=f"btn_poly_gen_{selected_frame.name}_{target_obj.id}", help="Tự động trích xuất viền đối tượng bên trong Bounding Box bằng Computer Vision"):
                    bx = target_obj.box2d or BBox2D(x1=new_x1, y1=new_y1, x2=new_x2, y2=new_y2)
                    new_poly = auto_generate_polygon_for_object(loaded_img, bx)
                    if new_poly:
                        target_obj.poly2d = new_poly
                        _reevaluate_qc(frames, lang=lang)
                        st.toast(f"✨ Đã sinh viền Polygon ({len(new_poly.vertices)} đỉnh) cho {target_obj.id}!", icon="✨")
                        st.rerun()
            with poly_btn2:
                if has_poly:
                    btn_clr_poly = "🗑️ Gỡ Bỏ Polygon" if lang == "vi" else "🗑️ Remove Poly"
                    if st.button(btn_clr_poly, use_container_width=True, key=f"btn_poly_clr_{selected_frame.name}_{target_obj.id}"):
                        target_obj.poly2d = None
                        _reevaluate_qc(frames, lang=lang)
                        st.toast(f"🗑️ Đã xóa viền Polygon của đối tượng {target_obj.id}!", icon="🗑️")
                        st.rerun()

            st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                btn_save_lbl = "💾 Lưu Thay Đổi" if lang == "vi" else "💾 Save Edits"
                if st.button(btn_save_lbl, use_container_width=True, type="primary", key=f"btn_save_{selected_frame.name}_{target_obj.id}"):
                    if new_x2 <= new_x1 or new_y2 <= new_y1:
                        st.error("⚠️ Tọa độ không hợp lệ: x2 phải lớn hơn x1 và y2 phải lớn hơn y1!" if lang == "vi" else "⚠️ Invalid coords: x2 > x1 and y2 > y1 required!")
                    else:
                        target_obj.category = new_cat
                        target_obj.box2d = BBox2D(x1=new_x1, y1=new_y1, x2=new_x2, y2=new_y2)
                        if target_obj.attributes is None:
                            target_obj.attributes = {}
                        target_obj.attributes["occluded"] = new_occ
                        target_obj.attributes["truncated"] = new_trunc
                        _reevaluate_qc(frames, lang=lang)
                        st.toast(f"✅ Đã lưu đối tượng {target_obj.id} và cập nhật đối soát QC!", icon="💾")
                        st.rerun()

            with btn_col2:
                btn_del_lbl = "🗑️ Xóa Box Này" if lang == "vi" else "🗑️ Delete Box"
                if st.button(btn_del_lbl, use_container_width=True, key=f"btn_del_{selected_frame.name}_{target_obj.id}"):
                    selected_frame.objects = [o for o in selected_frame.objects if o.id != target_obj.id]
                    _reevaluate_qc(frames, lang=lang)
                    st.toast(f"🗑️ Đã xóa đối tượng {target_obj.id} khỏi nhãn!", icon="🗑️")
                    st.rerun()

    # -------------------------------------------------------------------------
    # 2. CHẤP NHẬN GỢI Ý VẬT THỂ BỎ SÓT (MISSED -> NẠP THÀNH NHÃN)
    # -------------------------------------------------------------------------
    all_ai_cache = st.session_state.get("qc_ai_missed_cache", {})
    total_all_missed = sum(len(items) for items in all_ai_cache.values())
    ai_missed_cache = all_ai_cache.get(selected_frame.name, [])
    if not ai_missed_cache and Path(selected_frame.name).stem in all_ai_cache:
        ai_missed_cache = all_ai_cache[Path(selected_frame.name).stem]
    if total_all_missed == 0 and ai_missed_cache:
        total_all_missed = len(ai_missed_cache)

    unscanned_frames = sum(
        1 for f in frames
        if f.name not in all_ai_cache and Path(f.name).stem not in all_ai_cache
    )

    if ai_missed_cache or total_all_missed > 0 or (unscanned_frames > 0 and ai_model is not None and enable_ai_check):
        if total_all_missed > 0:
            count_info = (
                f"{len(ai_missed_cache)} Vật Thể Trên Ảnh Này · {total_all_missed} Trên Toàn Bộ Ảnh"
                if lang == "vi"
                else f"{len(ai_missed_cache)} This Frame · {total_all_missed} All Images"
            )
        elif unscanned_frames > 0:
            count_info = (
                f"{len(ai_missed_cache)} Trên Ảnh Này · {unscanned_frames} Ảnh Chưa Quét"
                if lang == "vi"
                else f"{len(ai_missed_cache)} This Frame · {unscanned_frames} Unscanned Frames"
            )
        else:
            count_info = (
                f"{len(ai_missed_cache)} Vật Thể Trên Ảnh Này"
                if lang == "vi"
                else f"{len(ai_missed_cache)} This Frame"
            )

        ai_box_title = f"🤖 Gợi Ý MISSED: {count_info}" if lang == "vi" else f"🤖 MISSED Suggestions: {count_info}"
        with st.expander(ai_box_title, expanded=True):
            st.caption(
                "Trợ lý AI phát hiện các đối tượng bị bỏ sót (MISSED) chưa được gán nhãn. Bạn có thể nạp từng đối tượng, nạp cho ảnh này hoặc nạp trên toàn bộ ảnh:"
                if lang == "vi"
                else "AI consensus detected unlabeled objects (MISSED). Accept individually, for this image, or ingest across all images:"
            )

            # CÁC NÚT NẠP TOÀN BỘ VẬT THỂ BỎ SÓT (ẢNH NÀY & TOÀN BỘ ẢNH)
            col_acc1, col_acc2 = st.columns([1, 1])
            with col_acc1:
                btn_curr_lbl = (
                    f"📥 Nạp Cho Ảnh Này ({len(ai_missed_cache)})"
                    if lang == "vi"
                    else f"📥 For This Image ({len(ai_missed_cache)})"
                )
                if st.button(
                    btn_curr_lbl,
                    type="secondary",
                    use_container_width=True,
                    disabled=(len(ai_missed_cache) == 0),
                    key=f"btn_acc_curr_{selected_frame.name}",
                ):
                    added_count = 0
                    cw = float(selected_frame.width) if selected_frame.width > 0 else 1920.0
                    ch = float(selected_frame.height) if selected_frame.height > 0 else 1080.0
                    for m_idx, m_item in enumerate(ai_missed_cache):
                        mbx: BBox2D = m_item["box2d"]
                        mcat = m_item["category"]
                        new_id = f"missed_{mcat[:3]}_{int(time.time()*100)%10000}_{m_idx+1}"
                        cx1 = max(0.0, min(cw - 2.0, float(mbx.x1)))
                        cy1 = max(0.0, min(ch - 2.0, float(mbx.y1)))
                        cx2 = max(cx1 + 1.0, min(cw, float(mbx.x2)))
                        cy2 = max(cy1 + 1.0, min(ch, float(mbx.y2)))
                        new_obj = LabeledObject(
                            id=new_id,
                            category=mcat,
                            box2d=BBox2D(x1=cx1, y1=cy1, x2=cx2, y2=cy2),
                            attributes={"occluded": False, "truncated": False},
                        )
                        selected_frame.objects.append(new_obj)
                        added_count += 1
                    
                    all_cache = st.session_state.setdefault("qc_ai_missed_cache", {})
                    all_cache[selected_frame.name] = []
                    all_cache[Path(selected_frame.name).stem] = []
                    st.session_state["qc_ai_missed_cache"] = all_cache
                    st.session_state["qc_frames"] = frames

                    # Đảm bảo bật tất cả layer hiển thị để annotator thấy nhãn ngay lập tức
                    st.session_state["scale_show_err"] = True
                    st.session_state["scale_show_warn"] = True
                    st.session_state["scale_show_valid"] = True
                    st.session_state["scale_show_labels"] = True

                    _reevaluate_qc(frames, lang=lang)
                    st.toast(f"✅ Đã nạp thành công {added_count} vật thể bỏ sót vào nhãn ảnh hiện tại!", icon="📥")
                    st.rerun()

            with col_acc2:
                btn_all_text = (
                    f"⚡ Nạp Nhãn Trên Toàn Bộ Ảnh ({total_all_missed})"
                    if total_all_missed > 0
                    else "⚡ Quét & Nạp Nhãn Toàn Bộ Ảnh"
                ) if lang == "vi" else (
                    f"⚡ Ingest On All Images ({total_all_missed})"
                    if total_all_missed > 0
                    else "⚡ Scan & Ingest All Images"
                )
                if st.button(
                    btn_all_text,
                    type="primary",
                    use_container_width=True,
                    key=f"btn_acc_all_frames_{selected_frame.name}",
                ):
                    from ui.ai_assistant import detect_missed_objects
                    from ui.io_utils import find_matching_image, load_image

                    all_cache = st.session_state.setdefault("qc_ai_missed_cache", {})
                    img_map = uploaded_image_map if uploaded_image_map else st.session_state.get("qc_uploaded_image_map", {})
                    active_model = ai_model if ai_model is not None else st.session_state.get("qc_ai_model")

                    total_added = 0
                    frames_affected = 0
                    n_frames = len(frames)
                    pbar = st.progress(0, text="🚀 Đang quét và nạp nhãn bỏ sót trên toàn bộ ảnh..." if lang == "vi" else "🚀 Ingesting missed objects across all images...")

                    for f_idx, f in enumerate(frames):
                        pct = int(100 * (f_idx + 1) / max(1, n_frames))
                        pbar.progress(pct, text=f"🤖 Đang nạp nhãn ({f_idx+1}/{n_frames}): {f.name}" if lang == "vi" else f"🤖 Ingesting frame ({f_idx+1}/{n_frames}): {f.name}")

                        f_missed = []
                        if f.name in all_cache:
                            f_missed = list(all_cache[f.name])
                        elif Path(f.name).stem in all_cache:
                            f_missed = list(all_cache[Path(f.name).stem])
                        elif active_model is not None and img_map:
                            matched_img = find_matching_image(f.name, img_map)
                            img_f = load_image(matched_img)
                            if img_f is not None:
                                try:
                                    f_missed = detect_missed_objects(
                                        img_f,
                                        f.objects,
                                        active_model,
                                        conf_thresh=ai_conf,
                                        ensemble_mode=ensemble_mode,
                                    )
                                except Exception:
                                    f_missed = []

                        if f_missed:
                            cw = float(f.width) if f.width > 0 else 1920.0
                            ch = float(f.height) if f.height > 0 else 1080.0
                            for m_idx, m_item in enumerate(f_missed):
                                mbx: BBox2D = m_item["box2d"]
                                mcat = m_item["category"]
                                new_id = f"missed_{mcat[:3]}_{int(time.time()*100)%10000}_{f_idx+1}_{m_idx+1}"
                                cx1 = max(0.0, min(cw - 2.0, float(mbx.x1)))
                                cy1 = max(0.0, min(ch - 2.0, float(mbx.y1)))
                                cx2 = max(cx1 + 1.0, min(cw, float(mbx.x2)))
                                cy2 = max(cy1 + 1.0, min(ch, float(mbx.y2)))
                                new_obj = LabeledObject(
                                    id=new_id,
                                    category=mcat,
                                    box2d=BBox2D(x1=cx1, y1=cy1, x2=cx2, y2=cy2),
                                    attributes={"occluded": False, "truncated": False},
                                )
                                f.objects.append(new_obj)
                                total_added += 1
                            frames_affected += 1

                        # Đánh dấu frame này đã sạch nhãn bỏ sót và không cần cảnh báo lại
                        all_cache[f.name] = []
                        all_cache[Path(f.name).stem] = []

                    pbar.empty()
                    st.session_state["qc_ai_missed_cache"] = all_cache
                    st.session_state["qc_frames"] = frames
                    _reevaluate_qc(frames, lang=lang)

                    # Đảm bảo bật tất cả layer hiển thị để annotator thấy toàn bộ nhãn ngay
                    st.session_state["scale_show_err"] = True
                    st.session_state["scale_show_warn"] = True
                    st.session_state["scale_show_valid"] = True
                    st.session_state["scale_show_labels"] = True

                    success_msg = (
                        f"🎉 Đã nạp thành công {total_added} vật thể bỏ sót trên {frames_affected} ảnh vào nhãn!"
                        if lang == "vi"
                        else f"🎉 Successfully ingested {total_added} missed objects across {frames_affected} images!"
                    )
                    st.toast(success_msg, icon="⚡")
                    st.success(success_msg)
                    time.sleep(0.4)
                    st.rerun()

            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

            # NẠP TỪNG ĐỐI TƯỢNG RIÊNG LẺ
            for m_i, m_item in enumerate(ai_missed_cache):
                mbx: BBox2D = m_item["box2d"]
                mcat = m_item["category"]
                mconf = m_item.get("confidence", 0.8)
                
                mcol_info, mcol_btn = st.columns([6, 4])
                with mcol_info:
                    st.markdown(
                        f"**{mcat}** · `[{int(mbx.x1)}, {int(mbx.y1)}, {int(mbx.x2)}, {int(mbx.y2)}]` ({mconf:.0%})"
                    )
                with mcol_btn:
                    btn_acc_lbl = "➕ Nạp Vào..." if lang == "vi" else "➕ Add Box"
                    if st.button(btn_acc_lbl, key=f"btn_acc_ai_{selected_frame.name}_{m_i}", use_container_width=True):
                        cw = float(selected_frame.width) if selected_frame.width > 0 else 1920.0
                        ch = float(selected_frame.height) if selected_frame.height > 0 else 1080.0
                        cx1 = max(0.0, min(cw - 2.0, float(mbx.x1)))
                        cy1 = max(0.0, min(ch - 2.0, float(mbx.y1)))
                        cx2 = max(cx1 + 1.0, min(cw, float(mbx.x2)))
                        cy2 = max(cy1 + 1.0, min(ch, float(mbx.y2)))
                        new_id = f"missed_{mcat[:3]}_{int(time.time()*100)%10000}"
                        new_obj = LabeledObject(
                            id=new_id,
                            category=mcat,
                            box2d=BBox2D(x1=cx1, y1=cy1, x2=cx2, y2=cy2),
                            attributes={"occluded": False, "truncated": False},
                        )
                        selected_frame.objects.append(new_obj)
                        # Gỡ khỏi cache AI để không bị cảnh báo trùng
                        ai_missed_cache.pop(m_i)
                        all_cache = st.session_state.setdefault("qc_ai_missed_cache", {})
                        all_cache[selected_frame.name] = ai_missed_cache
                        all_cache[Path(selected_frame.name).stem] = ai_missed_cache
                        st.session_state["qc_ai_missed_cache"] = all_cache
                        st.session_state["qc_frames"] = frames

                        # Đảm bảo hiển thị nhãn
                        st.session_state["scale_show_err"] = True
                        st.session_state["scale_show_warn"] = True
                        st.session_state["scale_show_valid"] = True
                        st.session_state["scale_show_labels"] = True

                        _reevaluate_qc(frames, lang=lang)
                        st.toast(f"✅ Đã nạp đối tượng MISSED [{mcat}] vào danh sách nhãn!", icon="➕")
                        st.rerun()

    # -------------------------------------------------------------------------
    # 3. VẼ TAY TRỰC QUAN / THÊM ĐỐI TƯỢNG MỚI (VISUAL CLICK-AND-DRAG BBOX)
    # -------------------------------------------------------------------------
    add_box_title = "🎨 Vẽ Tay & Thêm Đối Tượng Mới Vào Khung Hình" if lang == "vi" else "🎨 Visual Draw & Add Annotation Box"
    drawn_cache = st.session_state.get(f"drawn_box_{selected_frame.name}")
    with st.expander(add_box_title, expanded=True):
        add_cat = st.selectbox(
            "Lớp đối tượng cần vẽ:" if lang == "vi" else "Target Category:",
            options=STANDARD_BDD_CLASSES,
            index=0,
            key=f"madd_cat_{selected_frame.name}",
        )

        # Kiểm tra xem có ảnh hiển thị để người dùng vẽ tay trực tiếp hay không
        if loaded_img is not None:
            st.markdown(
                """
                <div style="background: rgba(0, 229, 255, 0.08); border-left: 3px solid #00e5ff; padding: 6px 10px; margin-bottom: 8px; border-radius: 4px; font-size: 0.76rem; line-height: 1.45;">
                    🎯 <strong>Thao tác chuột trực tiếp trên ảnh:</strong><br/>
                    • <strong>Vẽ box:</strong> Bấm giữ chuột và kéo quanh vật thể.<br/>
                    • <strong>Co duỗi kích thước:</strong> Bấm giữ 8 điểm neo (góc & cạnh) để kéo dãn / thu nhỏ.<br/>
                    • <strong>Di chuyển:</strong> Rê chuột vào giữa box (con trỏ ✥) và kéo.<br/>
                    • <strong>Zoom:</strong> Lăn con trỏ chuột để phóng to / thu nhỏ góc nhìn.
                </div>
                """
                if lang == "vi"
                else """
                <div style="background: rgba(0, 229, 255, 0.08); border-left: 3px solid #00e5ff; padding: 6px 10px; margin-bottom: 8px; border-radius: 4px; font-size: 0.76rem; line-height: 1.45;">
                    🎯 <strong>Interactive Mouse Controls:</strong><br/>
                    • <strong>Draw:</strong> Click & drag across the object.<br/>
                    • <strong>Resize / Stretch:</strong> Drag 8 anchor handles (corners & edges).<br/>
                    • <strong>Move:</strong> Hover inside box (cursor ✥) and drag.<br/>
                    • <strong>Zoom:</strong> Mouse scroll wheel to zoom in / out.
                </div>
                """,
                unsafe_allow_html=True,
            )

            from ui.visual_drawer import visual_bbox_drawer
            draw_result = visual_bbox_drawer(
                loaded_img,
                label=add_cat,
                orig_w=canvas_w,
                orig_h=canvas_h,
                display_w=390,
                initial_box=drawn_cache,
                key=f"visual_drawer_{selected_frame.name}",
            )

            # Khi người dùng kéo thả chuột vẽ xong trên Canvas
            if draw_result and "x1" in draw_result and "x2" in draw_result:
                st.session_state[f"drawn_box_{selected_frame.name}"] = {
                    "x1": draw_result["x1"],
                    "y1": draw_result["y1"],
                    "x2": draw_result["x2"],
                    "y2": draw_result["y2"],
                    "cat": add_cat,
                }
                drawn_cache = st.session_state[f"drawn_box_{selected_frame.name}"]
            elif draw_result is None and f"drawn_box_{selected_frame.name}" in st.session_state and st.session_state.get(f"_just_cleared_{selected_frame.name}"):
                drawn_cache = None
            if drawn_cache:
                bx1 = drawn_cache["x1"]
                by1 = drawn_cache["y1"]
                bx2 = drawn_cache["x2"]
                by2 = drawn_cache["y2"]
                bw = int(bx2 - bx1)
                bh = int(by2 - by1)

                st.markdown(
                    f"""
                    <div style="background: rgba(16, 185, 129, 0.15); border: 1px solid #10b981; border-radius: 6px; padding: 8px 12px; margin: 8px 0;">
                        <span style="color: #10b981; font-weight: 700; font-size: 0.8rem;">✨ Box Bạn Vừa Vẽ:</span>
                        <div style="font-family: monospace; font-size: 0.82rem; color: #f8fafc; margin-top: 2px;">
                            Lớp: <strong style="color: #00e5ff;">{add_cat}</strong> · [{bx1}, {by1}, {bx2}, {by2}] ({bw}×{bh} px)
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                btn_c1, btn_c2 = st.columns([6, 4])
                with btn_c1:
                    btn_confirm_lbl = "➕ Thêm Box Vừa Vẽ Này" if lang == "vi" else "➕ Add Drawn Box"
                    if st.button(btn_confirm_lbl, type="primary", use_container_width=True, key=f"btn_add_drawn_{selected_frame.name}"):
                        new_id = f"user_{add_cat[:3]}_{len(selected_frame.objects)+1:02d}"
                        new_obj = LabeledObject(
                            id=new_id,
                            category=add_cat,
                            box2d=BBox2D(x1=bx1, y1=by1, x2=bx2, y2=by2),
                            attributes={"occluded": False, "truncated": False},
                        )
                        selected_frame.objects.append(new_obj)
                        st.session_state.pop(f"drawn_box_{selected_frame.name}", None)
                        _reevaluate_qc(frames, lang=lang)
                        st.toast(f"✅ Đã thêm mới đối tượng {new_id} ({add_cat}) từ nét vẽ!", icon="🎉")
                        st.rerun()

                with btn_c2:
                    btn_reset_lbl = "🔄 Vẽ Lại" if lang == "vi" else "🔄 Reset"
                    if st.button(btn_reset_lbl, use_container_width=True, key=f"btn_reset_drawn_{selected_frame.name}"):
                        st.session_state.pop(f"drawn_box_{selected_frame.name}", None)
                        st.rerun()

        # Phần nhập tọa độ số phụ (Dành cho trường hợp không có ảnh hoặc muốn vi chỉnh)
        with st.expander("⚙️ Nhập tọa độ số thủ công (Tùy chọn phụ)" if lang == "vi" else "⚙️ Manual Coordinate Input (Optional)", expanded=(loaded_img is None)):
            col_ax1, col_ax2 = st.columns(2)
            with col_ax1:
                add_x1 = st.number_input("x1:", value=50.0, step=10.0, min_value=0.0, max_value=float(canvas_w), key=f"madd_x1_{selected_frame.name}")
                add_y1 = st.number_input("y1:", value=50.0, step=10.0, min_value=0.0, max_value=float(canvas_h), key=f"madd_y1_{selected_frame.name}")
            with col_ax2:
                add_x2 = st.number_input("x2:", value=250.0, step=10.0, min_value=0.0, max_value=float(canvas_w), key=f"madd_x2_{selected_frame.name}")
                add_y2 = st.number_input("y2:", value=200.0, step=10.0, min_value=0.0, max_value=float(canvas_h), key=f"madd_y2_{selected_frame.name}")

            btn_add_lbl = "➕ Thêm Bằng Tọa Độ Số" if lang == "vi" else "➕ Add Box by Numbers"
            if st.button(btn_add_lbl, use_container_width=True, key=f"btn_add_new_{selected_frame.name}"):
                if add_x2 <= add_x1 or add_y2 <= add_y1:
                    st.error("⚠️ Tọa độ không hợp lệ: x2 > x1 và y2 > y1!" if lang == "vi" else "⚠️ Invalid: x2 > x1 and y2 > y1!")
                else:
                    new_id = f"user_{len(selected_frame.objects)+1:03d}"
                    new_obj = LabeledObject(
                        id=new_id,
                        category=add_cat,
                        box2d=BBox2D(x1=add_x1, y1=add_y1, x2=add_x2, y2=add_y2),
                        attributes={"occluded": False, "truncated": False},
                    )
                    selected_frame.objects.append(new_obj)
                    _reevaluate_qc(frames, lang=lang)
                    st.toast(f"✅ Đã thêm mới đối tượng {new_id} ({add_cat})!", icon="🎉")
                    st.rerun()

    # -------------------------------------------------------------------------
    # 4. TẢI VỀ BỘ NHÃN ĐÃ SỬA HOÀN TẤT (JSON / YOLO / CVAT XML)
    # -------------------------------------------------------------------------
    exp_title = "📥 Xuất Tệp Nhãn Đã Sửa (JSON / YOLO / CVAT XML)" if lang == "vi" else "📥 Export Healed Annotations (JSON / YOLO / CVAT)"
    with st.expander(exp_title, expanded=True):
        st.caption(
            "Tải về ngay bộ dữ liệu đã được chữa lành và kiểm định đạt chuẩn theo định dạng mong muốn:"
            if lang == "vi"
            else "Download the remediated dataset ready for model training in your preferred format:"
        )

        stem = Path(selected_frame.name).stem
        qc_sources = st.session_state.get("qc_sources", [])
        detected_label = "BDD100K JSON (.json)"
        if qc_sources:
            first_src_name = qc_sources[0][0].lower()
            if first_src_name.endswith(".txt"):
                detected_label = "YOLO TXT (.txt / .zip)"
            elif first_src_name.endswith(".xml") or "cvat" in first_src_name:
                detected_label = "CVAT XML (.xml)"
            elif first_src_name.endswith(".json"):
                detected_label = "JSON (BDD100K / COCO .json)"

        # Banner nhận diện định dạng giống Input
        st.markdown(f"""
        <div style="background: rgba(0, 229, 255, 0.08); border-left: 3px solid #00e5ff; padding: 6px 12px; margin-bottom: 10px; border-radius: 4px; font-size: 0.74rem;">
            🎯 <strong>Định dạng phát hiện từ Input:</strong> <span style="color: #00e5ff; font-weight: 700;">{detected_label}</span>
        </div>
        """, unsafe_allow_html=True)

        tab_dl_json, tab_dl_yolo, tab_dl_cvat = st.tabs([
            "📄 Định Dạng JSON" if lang == "vi" else "📄 JSON Formats",
            "⚡ Định Dạng YOLO" if lang == "vi" else "⚡ YOLO Formats",
            "🌐 Định Dạng CVAT XML" if lang == "vi" else "🌐 CVAT XML Format",
        ])

        with tab_dl_json:
            st.markdown(
                """
                <div style='font-size: 0.74rem; color: #94a3b8; margin-bottom: 8px; line-height: 1.4;'>
                    💡 <strong>Hỗ trợ phần mềm gán nhãn ngoài (AnyLabeling, Labelme, BDD100K):</strong><br/>
                    Tải về từng file <code>.json</code> độc lập tương ứng với mỗi frame ảnh hoặc file JSON gộp toàn bộ.
                </div>
                """
                if lang == "vi"
                else """
                <div style='font-size: 0.74rem; color: #94a3b8; margin-bottom: 8px; line-height: 1.4;'>
                    💡 <strong>External Annotation Tools Support (AnyLabeling, Labelme, BDD100K):</strong><br/>
                    Export per-frame <code>.json</code> files or combined datasets.
                </div>
                """,
                unsafe_allow_html=True,
            )

            # 1. AnyLabeling ZIP (Mỗi frame 1 file json riêng)
            try:
                anylabeling_zip = export_anylabeling_zip_bytes(frames)
                st.download_button(
                    "🏷️ " + ("Tải ZIP JSON Từng Frame (Chuẩn AnyLabeling / Labelme)" if lang == "vi" else "Download AnyLabeling JSONs (.zip)"),
                    data=anylabeling_zip,
                    file_name="anylabeling_frames_json.zip",
                    mime="application/zip",
                    use_container_width=True,
                    key=f"dl_anylabeling_zip_{selected_frame.name}",
                    help="Tệp ZIP chứa các file {tên_ảnh}.json riêng lẻ theo chuẩn AnyLabeling. Giải nén vào thư mục ảnh để mở và chỉnh sửa trực tiếp trên AnyLabeling!",
                )
            except Exception:
                pass

            # 2. File JSON AnyLabeling của ảnh này
            try:
                anylabeling_single = export_anylabeling_json_single(selected_frame)
                st.download_button(
                    "📄 " + (f"Tải File JSON AnyLabeling Cho Ảnh Này ({stem}.json)" if lang == "vi" else f"Download AnyLabeling JSON ({stem}.json)"),
                    data=anylabeling_single.encode("utf-8"),
                    file_name=f"{stem}.json",
                    mime="application/json",
                    use_container_width=True,
                    key=f"dl_anylabeling_single_{selected_frame.name}",
                    help=f"Tải trực tiếp file nhãn {stem}.json theo định dạng AnyLabeling cho ảnh này",
                )
            except Exception:
                pass

            # 3. BDD100K ZIP (Mỗi frame 1 file json riêng)
            try:
                bdd_zip = export_bdd100k_zip_bytes(frames)
                st.download_button(
                    "📦 " + ("Tải ZIP Từng Frame (Chuẩn BDD100K - Không dùng cho AnyLabeling)" if lang == "vi" else "Download BDD100K JSONs Per Frame (.zip)"),
                    data=bdd_zip,
                    file_name="bdd100k_frames_json.zip",
                    mime="application/zip",
                    use_container_width=True,
                    key=f"dl_bdd_zip_{selected_frame.name}",
                    help="Tệp ZIP chứa từng file {tên_ảnh}.json riêng theo cấu trúc BDD100K (dạng danh sách [ ]). Chú ý: AnyLabeling không đọc được dạng này, vui lòng dùng nút [Chuẩn AnyLabeling / Labelme] ở trên!",
                )
            except Exception:
                pass

            st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
            j_col1, j_col2 = st.columns(2)
            with j_col1:
                # 4. BDD100K JSON Gộp toàn bộ
                bdd_all_bytes = export_bdd100k_json(frames).encode("utf-8")
                st.download_button(
                    "📄 " + ("BDD100K Toàn Bộ (.json)" if lang == "vi" else "BDD100K All (.json)"),
                    data=bdd_all_bytes,
                    file_name="bdd100k_all_healed.json",
                    mime="application/json",
                    use_container_width=True,
                    key=f"dl_bdd_all_{selected_frame.name}",
                    help="Tải 1 file JSON duy nhất chứa toàn bộ nhãn của tất cả ảnh theo chuẩn BDD100K",
                )
            with j_col2:
                # 5. COCO JSON Gộp toàn bộ
                try:
                    coco_str = export_coco_json(frames)
                    st.download_button(
                        "📦 " + ("COCO Instances (.json)" if lang == "vi" else "COCO Instances (.json)"),
                        data=coco_str.encode("utf-8"),
                        file_name="coco_instances_healed.json",
                        mime="application/json",
                        use_container_width=True,
                        key=f"dl_coco_all_{selected_frame.name}",
                        help="Xuất tập nhãn chuẩn COCO Instances JSON cho Detectron2 / YOLO / PyTorch",
                    )
                except Exception:
                    pass

        with tab_dl_yolo:
            st.markdown(
                "<div style='font-size: 0.73rem; color: #94a3b8; margin-bottom: 6px;'>Tải nhãn định dạng YOLO TXT (tọa độ chuẩn hóa 0..1 kèm classes.txt):</div>"
                if lang == "vi"
                else "<div style='font-size: 0.73rem; color: #94a3b8; margin-bottom: 6px;'>Export annotations in YOLO TXT format (normalized 0..1):</div>",
                unsafe_allow_html=True,
            )
            # 1. YOLO TXT của ảnh hiện tại
            yolo_curr_txt = export_yolo_txt_single(selected_frame)
            st.download_button(
                "⚡ " + (f"Tải YOLO TXT (Chỉ Ảnh Này: {stem}.txt)" if lang == "vi" else f"Download YOLO TXT ({stem}.txt)"),
                data=yolo_curr_txt.encode("utf-8"),
                file_name=f"{stem}.txt",
                mime="text/plain",
                use_container_width=True,
                key=f"dl_yolo_txt_single_{selected_frame.name}",
                help=f"Tải trực tiếp file nhãn {stem}.txt theo định dạng YOLO cho ảnh này",
            )

            # 2. YOLO Zip toàn bộ
            try:
                yolo_bytes = export_yolo_zip_bytes(frames)
                st.download_button(
                    "📦 " + ("Tải Toàn Bộ Nhãn YOLO (.zip)" if lang == "vi" else "Download All YOLO Labels (.zip)"),
                    data=yolo_bytes,
                    file_name="yolo_healed_labels.zip",
                    mime="application/zip",
                    use_container_width=True,
                    key=f"dl_yolo_healed_{selected_frame.name}",
                    help="Tải tệp ZIP chứa classes.txt và tất cả file .txt của các frame",
                )
            except Exception:
                pass

        with tab_dl_cvat:
            st.markdown(
                "<div style='font-size: 0.73rem; color: #94a3b8; margin-bottom: 6px;'>Tải nhãn định dạng CVAT XML 1.1 (tương thích nạp lại trực tiếp vào CVAT Tool):</div>"
                if lang == "vi"
                else "<div style='font-size: 0.73rem; color: #94a3b8; margin-bottom: 6px;'>Export annotations in CVAT XML 1.1 format:</div>",
                unsafe_allow_html=True,
            )
            try:
                cvat_xml_data = export_cvat_xml_str(frames)
                st.download_button(
                    "🌐 " + ("Tải Nhãn CVAT XML (.xml)" if lang == "vi" else "Download CVAT XML (.xml)"),
                    data=cvat_xml_data.encode("utf-8"),
                    file_name="cvat_annotations_healed.xml",
                    mime="application/xml",
                    use_container_width=True,
                    key=f"dl_cvat_xml_all_{selected_frame.name}",
                    help="Tải file XML chuẩn CVAT để nạp vào công cụ CVAT",
                )
            except Exception:
                pass

    # -------------------------------------------------------------------------
    # 5. ĐỒNG BỘ TRỰC TIẾP VỚI CVAT (TWO-WAY SYNC TO CVAT)
    # -------------------------------------------------------------------------
    cvat_meta = st.session_state.get("cvat_meta")
    cvat_bridge = st.session_state.get("cvat_bridge")

    cvat_panel_title = "🌐 Đồng Bộ Ngược Lại CVAT (Two-Way Sync)" if lang == "vi" else "🌐 Push Back to CVAT (Two-Way Sync)"
    with st.expander(cvat_panel_title, expanded=(cvat_meta is not None)):
        if cvat_meta:
            job_id = cvat_meta.get("job_id", 88)
            is_mock = (cvat_meta.get("mode") == "offline_mock")
            status_text = (
                f"Đang liên kết CVAT Job #{job_id} ({'Mô phỏng Local' if is_mock else 'Server Trực Tuyến'})"
                if lang == "vi"
                else f"Linked CVAT Job #{job_id} ({'Offline Mock' if is_mock else 'Online Server'})"
            )
            st.markdown(f"""
            <div style="background: rgba(0, 229, 255, 0.08); border: 1px solid rgba(0, 229, 255, 0.3); border-radius: 6px; padding: 8px 12px; margin-bottom: 8px;">
                <div style="font-size: 0.76rem; font-weight: 700; color: #00e5ff;">🔗 {status_text}</div>
                <div style="font-size: 0.70rem; color: #94a3b8; margin-top: 2px;">
                    {"Bấm nút bên dưới để nạp toàn bộ nhãn đã sửa (bổ sung box thiếu, viền polygon) ngược lại CVAT." if lang == "vi" else "Push all remediated annotations (added boxes, auto polygons) directly to CVAT."}
                </div>
            </div>
            """, unsafe_allow_html=True)

            c_btn1, c_btn2 = st.columns(2)
            with c_btn1:
                btn_push_lbl = "🚀 Nạp Vào CVAT" if lang == "vi" else "🚀 Push to CVAT"
                if st.button(btn_push_lbl, use_container_width=True, type="primary", key=f"btn_cvat_push_{selected_frame.name}"):
                    if is_mock or cvat_bridge is None:
                        # Mô phỏng nạp thành công
                        total_objs = sum(len(f.objects) for f in frames)
                        poly_count = sum(1 for f in frames for o in f.objects if o.poly2d)
                        st.session_state["cvat_meta"]["total_shapes"] = total_objs + poly_count
                        st.toast(f"✅ [Mô phỏng] Đã nạp thành công {total_objs} BBoxes và {poly_count} Polygons sang CVAT Job #{job_id}!", icon="🚀")
                        st.success(f"🎉 Đã nạp sang CVAT Job #{job_id}: {total_objs} BBoxes, {poly_count} Polygons! Mở CVAT bấm F5 để xem nhãn mới." if lang == "vi" else f"🎉 Synced to CVAT Job #{job_id}!")
                    else:
                        with st.spinner("Đang đẩy nhãn lên CVAT..." if lang == "vi" else "Pushing to CVAT..."):
                            ok, res = cvat_bridge.push_healed_annotations_to_job(job_id, frames, cvat_meta.get("label_map"))
                            if ok:
                                st.toast(f"✅ {res.get('message', 'Đã nạp thành công lên CVAT!')}", icon="🚀")
                                st.success(f"🎉 {res.get('message', 'Thành công!')}")
                            else:
                                st.error(f"❌ Lỗi nạp CVAT: {res}")
            with c_btn2:
                btn_issues_lbl = "🚩 Gắn Cờ Issue" if lang == "vi" else "🚩 Flag Issues"
                if st.button(btn_issues_lbl, use_container_width=True, key=f"btn_cvat_issues_{selected_frame.name}", help="Tự động cắm cờ báo lỗi lên từng frame trên CVAT"):
                    qc_rep = st.session_state.get("qc_report")
                    if is_mock or cvat_bridge is None:
                        err_cnt = len(qc_rep.errors) if qc_rep else 0
                        st.toast(f"🚩 [Mô phỏng] Đã cắm {err_cnt} cờ Issue lên CVAT Job #{job_id}!", icon="🚩")
                        st.info(f"🚩 Đã tạo {err_cnt} Issue chỉ điểm lỗi trên CVAT!" if lang == "vi" else f"🚩 Flagged {err_cnt} issues on CVAT!")
                    else:
                        with st.spinner("Đang tạo Issue trên CVAT..."):
                            ok, res = cvat_bridge.push_issues_to_cvat(job_id, qc_rep)
                            if ok:
                                st.toast(f"🚩 {res}", icon="🚩")
                                st.info(res)
                            else:
                                st.error(f"❌ Lỗi: {res}")
        else:
            st.caption(
                "Để kết nối trực tiếp với CVAT, vui lòng chọn nguồn dữ liệu **'🌐 Đồng Bộ Trực Tuyến CVAT'** ở thanh điều khiển bên trái."
                if lang == "vi"
                else "To connect to CVAT, select **'🌐 Online CVAT Sync'** in the left sidebar."
            )

