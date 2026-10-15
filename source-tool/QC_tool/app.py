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
    run_btn = cfg["run_btn"]
    reset_btn = cfg["reset_btn"]

    # 4. Áp dụng CSS giao diện tùy biến (Scale Dark vs Studio Light)
    apply_custom_css(is_dark=is_dark)

    # 5. Khởi tạo Session State
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

    # 6. Render Header chính
    render_header(
        total_rules_active=total_rules_active,
        ai_model=ai_model,
        enable_ai_check=enable_ai_check,
    )

    # Kiểm tra nguồn dữ liệu
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

    # Hàm thực thi QC
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
                    img_ref = find_matching_image(frame.name, uploaded_image_map)
                    if img_ref is not None:
                        img_obj = load_image(img_ref)
                        if img_obj is not None:
                            missed_list = detect_missed_objects(
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

    # 7. Trang Chờ (Khi chưa bấm Checking)
    if report is None:
        render_welcome_screen(
            all_sources=all_sources,
            uploaded_image_map=uploaded_image_map,
            total_rules_active=total_rules_active,
        )
        c_btn1, c_btn2, _ = st.columns([3.5, 2, 4.5])
        with c_btn1:
            if st.button("🚀 BẮT ĐẦU KIỂM TRA (CHECKING)", type="primary", use_container_width=True, key="btn_welcome_check"):
                _execute_qc()
                st.rerun()
        with c_btn2:
            if st.button("🔄 TẢI LẠI (RELOAD)", use_container_width=True, key="btn_welcome_reload"):
                st.session_state["qc_report"] = None
                st.rerun()
        st.stop()

    # 8. Dashboard Kết quả: Thống kê KPI & Quyết Định Nghiệm Thu
    pass_rate = render_kpi_dashboard(report=report, all_sources=all_sources)
    render_verdict_card(report=report, pass_rate=pass_rate)

    # 9. Tabs hiển thị chi tiết kết quả
    total_issues = len(report.errors)
    tab_list, tab_visual, tab_charts, tab_docs = st.tabs([
        f"📋 Defect Catalog ({total_issues})",
        "🖼️ Nucleus Split-Workspace",
        "📊 Quality Telemetry & KPI",
        "📖 Rule Specification",
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
