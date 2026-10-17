from __future__ import annotations
from typing import List, Dict, Any, Tuple
import streamlit as st

from qc.models import QCReport, FrameData
from ui.i18n import t, get_current_lang


def render_header(total_rules_active: int, ai_model: Any, enable_ai_check: bool):
    """Hiển thị Header thu nhỏ, khoảng cách dòng gọn gàng, hỗ trợ Tiếng Việt & English."""
    lang = get_current_lang()
    badge_ver = "Phiên bản 2.6" if lang == "vi" else "v2.6 PRO"

    ai_status_tag = (
        f'<span class="qc-tag qc-tag-online">{t("tag_ai_active")}</span>'
        if (ai_model and enable_ai_check)
        else f'<span class="qc-tag" style="background: rgba(148,163,184,0.12); color: var(--text-muted); border: 1px solid var(--border-c);">{t("tag_ai_offline")}</span>'
    )

    st.markdown(f"""
    <div class="qc-header-box">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
            <div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.64rem; color: var(--val-cyan); font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 1px; line-height: 1.2;">
                    {t("header_pre")}
                </div>
                <h1 class="qc-header-title" style="font-size: 1.15rem; line-height: 1.22; margin: 0; padding: 0;">
                    BDD100K <span style="color: var(--val-cyan); font-weight: 600;">{t("header_title")}</span>
                    <span style="font-size: 0.70rem; background: rgba(0, 229, 255, 0.12); color: var(--val-cyan); border: 1px solid rgba(0, 229, 255, 0.35); padding: 1px 6px; border-radius: 4px; font-weight: 600; vertical-align: middle;">{badge_ver}</span>
                </h1>
                <p class="qc-header-sub" style="font-size: 0.74rem; line-height: 1.2; margin: 2px 0 0 0;">{t("header_sub")}</p>
            </div>
            <div class="qc-tag-row" style="gap: 6px;">
                <div class="qc-tag qc-tag-online" style="padding: 2.5px 8px; font-size: 0.68rem;">
                    <span class="pulse-dot"></span>
                    <span>{t("tag_online")}</span>
                </div>
                <span class="qc-tag qc-tag-cyan" style="padding: 2.5px 8px; font-size: 0.68rem;">{t("tag_spec")}</span>
                <span class="qc-tag qc-tag-purple" style="padding: 2.5px 8px; font-size: 0.68rem;">{t("tag_rules", count=total_rules_active)}</span>
                {ai_status_tag}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_welcome_screen(
    all_sources: List[Tuple[str, List[FrameData]]],
    uploaded_image_map: Dict[str, Any],
    total_rules_active: int,
):
    """Trang chờ và giới thiệu khi người dùng chưa bấm Checking hoặc chưa nạp dữ liệu."""
    lang = get_current_lang()
    n_files = len(all_sources)
    n_frames = sum(len(frs) for _, frs in all_sources)
    n_imgs = len(uploaded_image_map) // 2 if uploaded_image_map else 0

    if not all_sources:
        title_txt = "👈 " + ("Hệ thống sẵn sàng đón nhận dữ liệu kiểm định" if lang == "vi" else "System Ready for Dataset Ingestion")
        desc_txt = (
            "Vui lòng tải lên các tệp nhãn (`.json`, `.txt` YOLO) hoặc chọn dữ liệu mẫu ở bảng điều khiển bên trái để bắt đầu kiểm tra tự động qua 15 bộ luật và đối soát AI."
            if lang == "vi"
            else "Please upload label files (.json, .txt YOLO) or choose sample dataset on the left sidebar to begin automated quality inspection across 15 rules."
        )
    else:
        title_txt = t("welcome_title")
        desc_txt = t("welcome_desc")

    st.markdown(f"""
    <div class="welcome-banner">
        <h3 style="margin-top:0; font-size: 1.2rem; display: flex; align-items: center; gap: 8px;">{title_txt}</h3>
        <p style="font-size: 0.88rem; line-height: 1.5; margin-bottom: 0;">{desc_txt}</p>
    </div>
    """, unsafe_allow_html=True)

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("📄 " + ("Tệp nhãn đã nạp" if lang == "vi" else "Loaded Label Files"), f"{n_files}")
    r2.metric("🎬 " + ("Khung hình phát hiện" if lang == "vi" else "Frames Detected"), f"{n_frames}")
    r3.metric("🖼️ " + ("Ảnh minh họa gốc" if lang == "vi" else "Source Images"), f"{n_imgs}")
    r4.metric("⚙️ " + ("Quy tắc kích hoạt" if lang == "vi" else "Active Rules"), f"{total_rules_active} / 15")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 🌟 " + ("4 Trụ Cột Kiểm Soát Chất Lượng Dữ Liệu:" if lang == "vi" else "4 Core Quality Pillars:"))
    fcol1, fcol2, fcol3, fcol4 = st.columns(4)
    with fcol1:
        st.markdown(f"""
        <div class="feature-card">
            <div class="feature-title">📐 {"Hình Học Hộp Bao Giới Hạn (B01 - B05)" if lang == "vi" else "BBox Geometry (B01 - B05)"}</div>
            <div class="feature-desc">{"Phát hiện hộp tràn khung hình (B01), tọa độ âm (B02), hộp siêu nhỏ (B03), tỉ lệ dị thường (B04) và chiếm toàn màn hình (B05)." if lang == "vi" else "Detect boundary overflow (B01), inverted coords (B02), tiny box (B03), extreme aspect ratio (B04), and fullscreen box (B05)."}</div>
        </div>
        """, unsafe_allow_html=True)
    with fcol2:
        st.markdown(f"""
        <div class="feature-card">
            <div class="feature-title">📉 {"Đa Giác Phân Đoạn (P01 - P04)" if lang == "vi" else "Polygon Topology (P01 - P04)"}</div>
            <div class="feature-desc">{"Kiểm tra số đỉnh dưới 3 (P01), viền tự cắt xoắn nơ (P02), lệch khung bao (P03) và đỉnh trùng / gấp khúc (P04)." if lang == "vi" else "Audit insufficient vertices (P01), self-intersection (P02), BBox mismatch (P03), and duplicate vertices (P04)."}</div>
        </div>
        """, unsafe_allow_html=True)
    with fcol3:
        st.markdown(f"""
        <div class="feature-card">
            <div class="feature-title">👥 {"Phân Loại & Thuộc Tính (A01 - C01)" if lang == "vi" else "Attributes & Classes (A01 - C01)"}</div>
            <div class="feature-desc">{"Soi lỗi vẽ đè trùng lặp (A01), thiếu thuộc tính che khuất (A02), màu đèn tín hiệu (A03) và sai tên lớp (C01)." if lang == "vi" else "Scan duplicate boxes (A01), missing attributes (A02), traffic light color (A03), and invalid classes (C01)."}</div>
        </div>
        """, unsafe_allow_html=True)
    with fcol4:
        st.markdown(f"""
        <div class="feature-card">
            <div class="feature-title">🎬 {"Theo Dõi Chuỗi Khung Hình & AI (T01 - AI01)" if lang == "vi" else "Video Sequence & AI (T01 - AI01)"}</div>
            <div class="feature-desc">{"Đánh giá mất dấu ngắt quãng (T01), nhảy giật vị trí (T02) và trợ lý AI soi vật thể bị bỏ sót (AI01)." if lang == "vi" else "Inspect tracking loss (T01), trajectory jumps (T02), and AI assistant for missed objects (AI01)."}</div>
        </div>
        """, unsafe_allow_html=True)


def render_kpi_dashboard(report: QCReport, all_sources: List[Tuple[str, List[FrameData]]]):
    """Hiển thị 5 thẻ KPI thống kê chính xác và thanh nguồn dữ liệu theo ngôn ngữ chuẩn."""
    lang = get_current_lang()
    total_issues = len(report.errors)
    pass_rate = 100.0 if report.total_objects == 0 else max(0.0, 100.0 - (total_issues / report.total_objects * 100))

    tcol_info, tcol_reload = st.columns([8, 2])
    with tcol_info:
        if len(all_sources) > 1:
            msg = (
                f"📦 Đang phân tích **{len(all_sources)} tệp** | "
                if lang == "vi"
                else f"📦 Analyzing **{len(all_sources)} files** | "
            )
            st.caption(
                msg
                + " · ".join(f"`{n}`" for n, _ in all_sources[:5])
                + (f" ... và {len(all_sources)-5} tệp khác" if len(all_sources) > 5 else "")
            )
        else:
            st.caption("📦 " + ("Hoàn tất kiểm tra chất lượng nhãn dữ liệu" if lang == "vi" else "Dataset quality inspection completed"))
    with tcol_reload:
        if st.button(t("btn_reload_sidebar"), use_container_width=True, help="Reset & re-audit", key="btn_kpi_reload"):
            st.session_state["qc_report"] = None
            st.session_state["qc_ai_missed_cache"] = {}
            st.rerun()

    kcol1, kcol2, kcol3, kcol4, kcol5 = st.columns(5)
    with kcol1:
        st.markdown(f"""
        <div class="qc-kpi-card qc-kpi-cyan">
            <div class="qc-kpi-label">🖼️ {t("kpi_frames")}</div>
            <div class="qc-kpi-val val-cyan">{report.total_frames:,}</div>
            <div class="qc-kpi-sub">{t("kpi_frames_sub")}</div>
        </div>
        """, unsafe_allow_html=True)
    with kcol2:
        st.markdown(f"""
        <div class="qc-kpi-card qc-kpi-indigo">
            <div class="qc-kpi-label">🎯 {t("kpi_objects")}</div>
            <div class="qc-kpi-val val-indigo">{report.total_objects:,}</div>
            <div class="qc-kpi-sub">{t("kpi_objects_sub")}</div>
        </div>
        """, unsafe_allow_html=True)
    with kcol3:
        sub_err = "Bắt buộc sửa chữa" if (lang == "vi" and report.error_count() > 0) else ("Hoàn toàn sạch lỗi" if lang == "vi" else ("Must fix" if report.error_count() > 0 else "Zero errors"))
        st.markdown(f"""
        <div class="qc-kpi-card qc-kpi-rose">
            <div class="qc-kpi-label">🔴 {t("kpi_errors")}</div>
            <div class="qc-kpi-val val-rose">{report.error_count():,}</div>
            <div class="qc-kpi-sub">{sub_err}</div>
        </div>
        """, unsafe_allow_html=True)
    with kcol4:
        st.markdown(f"""
        <div class="qc-kpi-card qc-kpi-amber">
            <div class="qc-kpi-label">🟡 {t("kpi_warnings")}</div>
            <div class="qc-kpi-val val-amber">{report.warning_count():,}</div>
            <div class="qc-kpi-sub">{t("kpi_warnings_sub")}</div>
        </div>
        """, unsafe_allow_html=True)
    with kcol5:
        score_class = "val-emerald" if pass_rate >= 90 else ("val-amber" if pass_rate >= 75 else "val-rose")
        fill_color = "#10b981" if pass_rate >= 90 else ("#f59e0b" if pass_rate >= 75 else "#f43f5e")
        border_class = "qc-kpi-emerald" if pass_rate >= 90 else ("qc-kpi-amber" if pass_rate >= 75 else "qc-kpi-rose")
        sub_health = "🎉 Đạt chuẩn (≥90%)" if (lang == "vi" and pass_rate >= 90) else ("⚠️ Chưa đạt (<90%)" if lang == "vi" else ("🎉 Compliant (≥90%)" if pass_rate >= 90 else "⚠️ Non-compliant (<90%)"))
        st.markdown(f"""
        <div class="qc-kpi-card {border_class}">
            <div class="qc-kpi-label">🛡️ {t("kpi_health")}</div>
            <div class="qc-kpi-val {score_class}">{pass_rate:.1f}%</div>
            <div class="qc-progress-track">
                <div class="qc-progress-fill" style="width: {min(100.0, max(0.0, pass_rate))}%; background: {fill_color};"></div>
            </div>
            <div class="qc-kpi-sub">{sub_health}</div>
        </div>
        """, unsafe_allow_html=True)

    return pass_rate


def render_verdict_card(report: QCReport, pass_rate: float):
    """Hiển thị thẻ Quyết Định Nghiệm Thu với ngôn ngữ đồng bộ 100%."""
    lang = get_current_lang()
    err_n = report.error_count()
    warn_n = report.warning_count()

    if err_n > 0:
        if lang == "vi":
            verdict_badge = "🔴 TỪ CHỐI NGHIỆM THU (KHÔNG ĐẠT)"
            verdict_desc = f"Phát hiện <strong>{err_n} lỗi kỹ thuật nghiêm trọng</strong>. Bộ nhãn không đủ tiêu chuẩn để huấn luyện mô hình. Bắt buộc người gán nhãn phải khắc phục các lỗi này."
            stamp_text = "TỪ CHỐI"
            compliance_tag = '<span class="qc-tag" style="background: rgba(239,68,68,0.15); border: 1px solid rgba(239,68,68,0.4); color: #fca5a5;">CHƯA ĐẠT CHUẨN</span>'
        else:
            verdict_badge = "🔴 REJECTED — DEFECT REMEDIATION REQUIRED"
            verdict_desc = f"Detected <strong>{err_n} critical errors</strong>. The dataset does not meet quality requirements for model training. Annotators must resolve all blocking defects."
            stamp_text = "REJECTED"
            compliance_tag = '<span class="qc-tag" style="background: rgba(239,68,68,0.15); border: 1px solid rgba(239,68,68,0.4); color: #fca5a5;">TRAINING UNSAFE</span>'
        verdict_color = "#ef4444"
        verdict_border = "rgba(239, 68, 68, 0.5)"
    elif warn_n > 0:
        if lang == "vi":
            verdict_badge = "🟡 NGHIỆM THU CÓ ĐIỀU KIỆN"
            verdict_desc = f"Không có lỗi nghiêm trọng, nhưng phát hiện <strong>{warn_n} cảnh báo</strong> cần được Reviewer xác nhận ngoại lệ trước khi xuất dữ liệu."
            stamp_text = "CÓ ĐIỀU KIỆN"
            compliance_tag = '<span class="qc-tag" style="background: rgba(245,158,11,0.15); border: 1px solid rgba(245,158,11,0.4); color: #fde68a;">CẦN RÀ SOÁT</span>'
        else:
            verdict_badge = "🟡 CONDITIONAL PASS"
            verdict_desc = f"Zero critical errors, but <strong>{warn_n} warnings</strong> require reviewer confirmation before proceeding to production."
            stamp_text = "CONDITIONAL"
            compliance_tag = '<span class="qc-tag" style="background: rgba(245,158,11,0.15); border: 1px solid rgba(245,158,11,0.4); color: #fde68a;">REVIEW REQUIRED</span>'
        verdict_color = "#f59e0b"
        verdict_border = "rgba(245, 158, 11, 0.5)"
    else:
        if lang == "vi":
            verdict_badge = "🟢 PHÊ DUYỆT NGHIỆM THU (ĐẠT CHUẨN)"
            verdict_desc = "Tất cả các nhãn kiểm tra đều thỏa mãn <strong>100% quy chuẩn kỹ thuật</strong> (0 lỗi, 0 cảnh báo). Bộ dữ liệu hoàn hảo, sẵn sàng cho công đoạn huấn luyện mô hình."
            stamp_text = "ĐẠT CHUẨN"
            compliance_tag = '<span class="qc-tag" style="background: rgba(16,185,129,0.15); border: 1px solid rgba(16,185,129,0.4); color: #a7f3d0;">SẴN SÀNG HUẤN LUYỆN</span>'
        else:
            verdict_badge = "🟢 PASSED & APPROVED FOR TRAINING"
            verdict_desc = "All annotations strictly satisfy <strong>100% technical specifications</strong> (0 Error, 0 Warning). Dataset verified and ready for deep learning training pipeline."
            stamp_text = "APPROVED"
            compliance_tag = '<span class="qc-tag" style="background: rgba(16,185,129,0.15); border: 1px solid rgba(16,185,129,0.4); color: #a7f3d0;">TRAINING READY</span>'
        verdict_color = "#10b981"
        verdict_border = "rgba(16, 185, 129, 0.5)"

    st.markdown(f"""
    <div style="background: var(--bg-card); border: 1.5px solid {verdict_border}; border-radius: 12px; padding: 18px 24px; margin: 14px 0 20px 0; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 14px; box-shadow: var(--box-shadow); position: relative; overflow: hidden;">
        <div style="position: absolute; top: -10px; left: -10px; width: 6px; height: 120%; background: {verdict_color};"></div>
        <div class="qc-verdict-stamp" style="color: {verdict_color}; border-color: {verdict_color};">
            {stamp_text}
        </div>
        <div style="z-index: 1;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 3px;">
                <span style="font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--text-sub); font-weight: 700; font-family: 'JetBrains Mono', monospace;">{"KẾT QUẢ NGHIỆM THU CHÍNH THỨC" if lang == "vi" else "OFFICIAL QUALITY VERDICT"}</span>
                {compliance_tag}
            </div>
            <div style="font-size: 1.22rem; font-weight: 800; color: {verdict_color}; letter-spacing: -0.01em;">{verdict_badge}</div>
            <div style="color: var(--text-main); font-size: 0.88rem; margin-top: 4px; line-height: 1.5; max-width: 820px;">{verdict_desc}</div>
        </div>
        <div style="text-align: right; font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; color: var(--text-muted); background: var(--bg-card-sub); padding: 10px 16px; border-radius: 8px; border: 1px solid var(--border-c); box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15); z-index: 1;">
            <div style="font-size: 0.72rem; color: var(--text-sub); text-transform: uppercase;">{"Tiêu chuẩn:" if lang == "vi" else "Spec:"} <strong style="color: var(--text-main);">BDD100K / N2-04A</strong></div>
            <div style="margin-top: 4px;">{"Tỷ lệ đạt:" if lang == "vi" else "Pass rate:"} <strong style="color: {verdict_color}; font-size: 1.25rem;">{pass_rate:.1f}%</strong></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
