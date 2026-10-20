"""
app.py — Giao diện Web tương tác Streamlit cho BDD-QC Tool (Mã đề: N2-04A).
Kiểm tra chất lượng Bounding Box & Polygon 2D trên dataset BDD100K & YOLO.
Kiến trúc mã nguồn chuẩn hóa: Phân tách module UI (ui/styles, ui/sidebar, ui/tabs).
"""

from __future__ import annotations
import time
from typing import List
import streamlit as st

from qc.models import FrameData, QCError
from qc.engine import run_qc

from ui.styles import apply_custom_css
from ui.sidebar import render_sidebar
from ui.header import render_header, render_welcome_screen, render_kpi_dashboard, render_verdict_card
from ui.io_utils import find_matching_image, load_image
from ui.ai_assistant import load_ai_detector, detect_missed_objects
from ui.tabs.tab_error_list import render_tab_error_list
from ui.tabs.tab_visualizer import render_tab_visualizer
from ui.tabs.tab_analytics import render_tab_analytics
from ui.tabs.tab_docs import render_tab_docs


def main():
    # 1. Cấu hình trang Streamlit
    st.set_page_config(
        page_title="Scale Nucleus // QA Audit Workspace (N2-04A)",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # 2. Khởi tạo mô hình AI Detector (cache tài nguyên)
    ai_model = load_ai_detector()

    # 3. Render Sidebar & Lấy cấu hình
    cfg = render_sidebar(ai_model=ai_model)
    is_dark = cfg["is_dark"]
    all_sources = cfg["all_sources"]
    file_display_name = cfg["file_display_name"]
    uploaded_image_map = cfg["uploaded_image_map"]
    active_rules = cfg["active_rules"]
    active_seq_rules = cfg["active_seq_rules"]
    total_rules_active = cfg["total_rules_active"]
    enable_ai_check = cfg["enable_ai_check"]
    ai_conf = cfg["ai_conf"]
    ai_ensemble_mode = cfg.get("ai_ensemble_mode", "majority")
    run_btn = cfg["run_btn"]
    reset_btn = cfg["reset_btn"]

    # 4. Áp dụng CSS giao diện tùy biến (Scale Dark vs Studio Light)
    apply_custom_css(is_dark=is_dark)

    # 5. Khởi tạo Session State
    st.session_state["qc_ai_model"] = ai_model
    st.session_state["qc_uploaded_image_map"] = uploaded_image_map
    st.session_state["qc_enable_ai_check"] = enable_ai_check
    st.session_state["qc_ai_conf"] = ai_conf
    st.session_state["qc_ai_ensemble_mode"] = ai_ensemble_mode

    # Đảm bảo các layer hiển thị không bao giờ bị tắt nhãn mặc định
    for _ly_k in ["scale_show_err", "scale_show_warn", "scale_show_valid", "scale_show_labels"]:
        if _ly_k not in st.session_state:
            st.session_state[_ly_k] = True
    if "scale_show_grid" not in st.session_state:
        st.session_state["scale_show_grid"] = False

    if "qc_report" not in st.session_state:
        st.session_state["qc_report"] = None
        st.session_state["qc_frames"] = None
        st.session_state["qc_sources"] = None
        st.session_state["qc_rules_snapshot"] = None
        st.session_state["qc_display_name"] = ""
        st.session_state["active_frame_name"] = ""
        st.session_state["qc_ai_missed_cache"] = {}

    if reset_btn:
        st.session_state["qc_report"] = None
        st.session_state["qc_frames"] = None
        st.session_state["qc_sources"] = None
        st.session_state["qc_rules_snapshot"] = None
        st.session_state["qc_display_name"] = ""
        st.session_state["active_frame_name"] = ""
        st.session_state["qc_ai_missed_cache"] = {}
        st.session_state["scale_show_err"] = True
        st.session_state["scale_show_warn"] = True
        st.session_state["scale_show_valid"] = True
        st.session_state["scale_show_labels"] = True
        st.session_state["scale_show_grid"] = False
        st.rerun()

    from ui.i18n import t, get_current_lang, set_current_lang
    curr_lang = get_current_lang()

    # 6. Render Header chính
    render_header(
        total_rules_active=total_rules_active,
        ai_model=ai_model,
        enable_ai_check=enable_ai_check,
    )

    # Kiểm tra nguồn dữ liệu
    if not all_sources:
        render_welcome_screen(
            all_sources=[],
            uploaded_image_map=uploaded_image_map,
            total_rules_active=total_rules_active,
        )
        st.stop()


    # Hàm thực thi QC với Progress Bar thời gian thực
    def _execute_qc():
        all_frames_run: List[FrameData] = []
        for _src_name, _src_frames in all_sources:
            all_frames_run.extend(_src_frames)

        st.session_state["qc_ai_missed_cache"] = {}
        _t0 = time.time()

        p_msg1 = "🚀 Đang khởi động quy trình kiểm tra QC..." if curr_lang == "vi" else "🚀 Initializing QC audit runtime..."
        pbar = st.progress(0, text=p_msg1)

        # 1. Quét 12 Linter rules (cực nhanh: ~0.05s)
        p_msg2 = "📐 Đang quét các bộ luật hình học, đa giác & chuỗi video..." if curr_lang == "vi" else "📐 Auditing geometry, topology & temporal tracking rules..."
        pbar.progress(25, text=p_msg2)
        _report = run_qc(
            all_frames_run,
            rules=active_rules,
            sequence_rules=active_seq_rules,
        )

        # 2. Quét AI phát hiện vật thể bỏ sót (RULE_AI01)
        if enable_ai_check and ai_model is not None:
            frames_with_img = []
            for frame in all_frames_run:
                img_ref = find_matching_image(frame.name, uploaded_image_map)
                if img_ref is not None:
                    frames_with_img.append((frame, img_ref))

            total_ai = len(frames_with_img)
            # Quét các frame tiêu biểu trong batch (tối đa 5 frame đầu để phản hồi ngay lập tức trong vài giây)
            max_batch_ai = min(total_ai, 5)

            for ai_idx, (frame, img_ref) in enumerate(frames_with_img[:max_batch_ai], start=1):
                pct = 25 + int(70 * (ai_idx / max_batch_ai))
                ai_scan_text = (
                    f"🤖 Đang đối soát AI [{ai_idx}/{max_batch_ai}]: {frame.name}"
                    if curr_lang == "vi"
                    else f"🤖 Running AI consensus check [{ai_idx}/{max_batch_ai}]: {frame.name}"
                )
                pbar.progress(pct, text=ai_scan_text)

                img_obj = load_image(img_ref)
                if img_obj is not None:
                    missed_list = detect_missed_objects(
                        img_obj,
                        frame.objects,
                        ai_model,
                        conf_thresh=ai_conf,
                        ensemble_mode=ai_ensemble_mode,
                    )
                    st.session_state["qc_ai_missed_cache"][frame.name] = missed_list

                    for m_idx, m_obj in enumerate(missed_list, 1):
                        mbx = m_obj["box2d"]
                        m_cat = m_obj["category"]
                        m_conf = m_obj["confidence"]
                        err_msg = (
                            f"MISSED: Phát hiện [{m_cat}] bị bỏ sót tại [{int(mbx.x1)}, {int(mbx.y1)}, {int(mbx.x2)}, {int(mbx.y2)}] (độ tin cậy: {m_conf:.0%})"
                            if curr_lang == "vi"
                            else f"MISSED: Unlabeled [{m_cat}] detected at [{int(mbx.x1)}, {int(mbx.y1)}, {int(mbx.x2)}, {int(mbx.y2)}] (confidence: {m_conf:.0%})"
                        )
                        _report.add(QCError(
                            rule_id="RULE_AI01",
                            severity="ERROR" if m_conf >= 0.60 else "WARNING",
                            frame_name=frame.name,
                            object_id=f"missed_{m_idx:02d}",
                            category=m_cat,
                            message=err_msg,
                        ))

        p_done = "🎉 Đã hoàn tất kiểm tra QC thành công!" if curr_lang == "vi" else "🎉 QC audit pipeline completed successfully!"
        pbar.progress(100, text=p_done)
        time.sleep(0.3)
        pbar.empty()
        _elapsed = time.time() - _t0

        st.session_state["qc_report"] = _report
        st.session_state["qc_frames"] = all_frames_run
        st.session_state["qc_sources"] = all_sources
        st.session_state["qc_rules_snapshot"] = active_rules
        st.session_state["qc_active_seq_rules"] = active_seq_rules
        st.session_state["qc_display_name"] = file_display_name
        toast_msg = (
            f"✅ Hoàn thành quét QC trong {_elapsed:.2f}s — phát hiện {len(_report.errors)} vấn đề"
            if curr_lang == "vi"
            else f"✅ QC audit finished in {_elapsed:.2f}s — found {len(_report.errors)} issues"
        )
        st.toast(toast_msg, icon="🛡️")

    if run_btn:
        _execute_qc()

    # Lấy kết quả từ session
    report = st.session_state.get("qc_report")
    frames = st.session_state.get("qc_frames")
    file_display_name_final = st.session_state.get("qc_display_name", file_display_name)

    # 7. Trang Chờ (Khi chưa bấm Checking)
    if report is None:
        render_welcome_screen(
            all_sources=all_sources,
            uploaded_image_map=uploaded_image_map,
            total_rules_active=total_rules_active,
        )
        c_btn1, c_btn2, _ = st.columns([3.5, 2, 4.5])
        with c_btn1:
            if st.button(t("btn_start_audit"), type="primary", use_container_width=True, key="btn_welcome_check"):
                _execute_qc()
                st.rerun()
        with c_btn2:
            if st.button(t("btn_reload_welcome"), use_container_width=True, key="btn_welcome_reload"):
                st.session_state["qc_report"] = None
                st.rerun()
        st.stop()

    # 8. Dashboard Kết quả: Thống kê KPI & Quyết Định Nghiệm Thu
    pass_rate = render_kpi_dashboard(report=report, all_sources=all_sources)
    render_verdict_card(report=report, pass_rate=pass_rate)

    # 9. Tabs hiển thị chi tiết kết quả
    total_issues = len(report.errors)
    tab_list, tab_visual, tab_charts, tab_docs = st.tabs([
        t("tab_defects", count=total_issues),
        t("tab_visual"),
        t("tab_analytics"),
        t("tab_docs"),
    ])

    with tab_list:
        render_tab_error_list(
            report=report,
            frames=frames,
            file_display_name=file_display_name_final,
        )

    with tab_visual:
        render_tab_visualizer(
            report=report,
            frames=frames,
            uploaded_image_map=uploaded_image_map,
            ai_model=ai_model,
            enable_ai_check=enable_ai_check,
            ai_conf=ai_conf,
            is_dark=is_dark,
            ensemble_mode=ai_ensemble_mode,
        )

    with tab_charts:
        render_tab_analytics(
            report=report,
            pass_rate=pass_rate,
            is_dark=is_dark,
        )

    with tab_docs:
        render_tab_docs()


if __name__ == "__main__":
    main()
