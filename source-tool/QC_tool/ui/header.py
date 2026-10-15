from __future__ import annotations
from typing import List, Dict, Any, Tuple
import streamlit as st

from qc.models import QCReport, FrameData


def render_header(total_rules_active: int, ai_model: Any, enable_ai_check: bool):
    """Hiển thị Header chuẩn Scale Nucleus với status pill và live audit indicator."""
    ai_status_tag = (
        '<span class="qc-tag qc-tag-online">● YOLOv8 AI ACTIVE</span>'
        if (ai_model and enable_ai_check)
        else '<span class="qc-tag" style="background: rgba(100,116,139,0.12); color: #64748b; border: 1px solid #cbd5e1;">○ AI OFFLINE</span>'
    )

    st.markdown(f"""
    <div class="qc-header-box">
        <div style="display: flex; align-items: flex-start; justify-content: space-between; flex-wrap: wrap; gap: 14px;">
            <div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 3px;" class="val-cyan">
                    SCALE NUCLEUS // QA AUDIT SUITE
                </div>
                <h1 class="qc-header-title">
                    BDD100K <span class="val-cyan" style="font-weight: 500;">QUALITY CONTROL WORKSPACE</span>
                    <span style="font-size: 0.8rem; background: rgba(37, 99, 235, 0.1); color: #2563eb; border: 1px solid rgba(37, 99, 235, 0.3); padding: 2px 8px; border-radius: 4px; font-weight: 600; vertical-align: middle;">v2.6 PRO</span>
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


def render_welcome_screen(
    all_sources: List[Tuple[str, List[FrameData]]],
    uploaded_image_map: Dict[str, Any],
    total_rules_active: int,
) -> Tuple[bool, bool]:
    """Trang chờ và giới thiệu luồng thao tác: (2) Banner -> (3) Metrics -> (4) Action Buttons -> (5) 4 Pillars."""
    n_files = len(all_sources)
    n_frames = sum(len(frs) for _, frs in all_sources)
    n_imgs = len(uploaded_image_map) // 2 if uploaded_image_map else 0

    # (2) Khối Banner thông báo chuẩn WCAG độ tương phản cao
    st.markdown("""
    <div class="qc-welcome-banner">
        <h3 class="qc-welcome-title">📋 Sẵn sàng kiểm tra chất lượng dữ liệu nhãn</h3>
        <p class="qc-welcome-desc">Hệ thống đã nhận diện cấu trúc file thành công. Nhấn nút <strong>BẮT ĐẦU KIỂM TRA</strong> để chạy quét tự động qua 15 rules toán học và đối soát AI YOLOv8.</p>
    </div>
    """, unsafe_allow_html=True)

    # (3) Hàng 4 chỉ số thống kê đóng khung dạng thẻ nhẹ
    r1, r2, r3, r4 = st.columns(4)
    with r1:
        st.markdown(f"""
        <div class="qc-welcome-metric">
            <div class="qc-welcome-metric-label">📄 File nhãn đã nạp</div>
            <div class="qc-welcome-metric-val">{n_files} <span style="font-size: 0.85rem; font-weight: 500; color: #64748b;">file</span></div>
        </div>
        """, unsafe_allow_html=True)
    with r2:
        st.markdown(f"""
        <div class="qc-welcome-metric">
            <div class="qc-welcome-metric-label">🎬 Frames phát hiện</div>
            <div class="qc-welcome-metric-val">{n_frames} <span style="font-size: 0.85rem; font-weight: 500; color: #64748b;">frame</span></div>
        </div>
        """, unsafe_allow_html=True)
    with r3:
        st.markdown(f"""
        <div class="qc-welcome-metric">
            <div class="qc-welcome-metric-label">🖼️ Ảnh minh họa gốc</div>
            <div class="qc-welcome-metric-val">{n_imgs} <span style="font-size: 0.85rem; font-weight: 500; color: #64748b;">ảnh</span></div>
        </div>
        """, unsafe_allow_html=True)
    with r4:
        st.markdown(f"""
        <div class="qc-welcome-metric">
            <div class="qc-welcome-metric-label">⚙️ Rules kích hoạt</div>
            <div class="qc-welcome-metric-val">{total_rules_active} <span style="font-size: 0.85rem; font-weight: 500; color: #64748b;">/ 15</span></div>
        </div>
        """, unsafe_allow_html=True)

    # (4) Cụm 2 nút hành động ("🚀 BẮT ĐẦU KIỂM TRA" và "🔄 LÀM MỚI") nằm ngay dưới metrics
    c_btn1, c_btn2, _ = st.columns([2.8, 1.8, 5.4])
    with c_btn1:
        start_btn = st.button("🚀 BẮT ĐẦU KIỂM TRA", type="primary", use_container_width=True, key="btn_welcome_check")
    with c_btn2:
        reload_btn = st.button("🔄 LÀM MỚI", use_container_width=True, key="btn_welcome_reload")

    st.markdown("<br>", unsafe_allow_html=True)

    # (5) 4 Trụ Cột Kiểm Soát Chất Lượng (Quality Pillars) đưa xuống dưới làm thông tin tham khảo
    st.markdown("#### 🌟 4 Trụ Cột Kiểm Soát Chất Lượng (Quality Pillars):")
    fcol1, fcol2, fcol3, fcol4 = st.columns(4)
    with fcol1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-title">📐 BBox Hình Học (B01-B05)</div>
            <div class="feature-desc">Phát hiện box tràn khung hình (B01), box rỗng (B02), box quá bé (B03), tỉ lệ khung hình bất thường (B04) và scale vượt kích thước ảnh (B05).</div>
        </div>
        """, unsafe_allow_html=True)
    with fcol2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-title">📉 Polygon Topology (P01-P04)</div>
            <div class="feature-desc">Bắt lỗi đa giác dưới 3 đỉnh (P01), viền tự xoắn cắt nơ (P02), lệch Mask vs BBox IoU &lt; 0.70 (P03) và gai nhọn/trùng đỉnh spike (P04).</div>
        </div>
        """, unsafe_allow_html=True)
    with fcol3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-title">👥 Phân Loại & Thuộc Tính (A01-C01)</div>
            <div class="feature-desc">Quét box trùng đè IoU &gt; 0.85 (A01), thiếu occlusion/truncation (A02), thiếu màu đèn (A03) và sai chính tả/ngoài taxonomy BDD100K (C01).</div>
        </div>
        """, unsafe_allow_html=True)
    with fcol4:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-title">🎬 Video Tracking & AI (T01-AI01)</div>
            <div class="feature-desc">Kiểm tra tính liên tục chuỗi frame (mất dấu flicker T01, nhảy tọa độ giật T02) và trợ lý AI YOLOv8 đối soát vật thể bị bỏ sót (AI01).</div>
        </div>
        """, unsafe_allow_html=True)

    return start_btn, reload_btn


def render_kpi_dashboard(report: QCReport, all_sources: List[Tuple[str, List[FrameData]]]):
    """Hiển thị 5 thẻ KPI thống kê chính xác và thanh nguồn dữ liệu."""
    total_issues = len(report.errors)
    pass_rate = 100.0 if report.total_objects == 0 else max(0.0, 100.0 - (total_issues / report.total_objects * 100))

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
        if st.button("🔄 Reload lại", use_container_width=True, help="Xóa cache và chạy kiểm tra lại", key="btn_kpi_reload"):
            st.session_state["qc_report"] = None
            st.rerun()

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
        score_class = "val-emerald" if pass_rate >= 90 else ("val-amber" if pass_rate >= 75 else "val-rose")
        fill_color = "#10b981" if pass_rate >= 90 else ("#f59e0b" if pass_rate >= 75 else "#f43f5e")
        border_class = "qc-kpi-emerald" if pass_rate >= 90 else ("qc-kpi-amber" if pass_rate >= 75 else "qc-kpi-rose")
        st.markdown(f"""
        <div class="qc-kpi-card {border_class}">
            <div class="qc-kpi-label">🛡️ HEALTH SCORE</div>
            <div class="qc-kpi-val {score_class}">{pass_rate:.1f}%</div>
            <div class="qc-progress-track">
                <div class="qc-progress-fill" style="width: {min(100.0, max(0.0, pass_rate))}%; background: {fill_color};"></div>
            </div>
            <div class="qc-kpi-sub">{'🎉 Đạt chuẩn (≥90%)' if pass_rate >= 90 else '⚠️ Chưa đạt (<90%)'}</div>
        </div>
        """, unsafe_allow_html=True)

    return pass_rate


def render_verdict_card(report: QCReport, pass_rate: float):
    """Hiển thị thẻ Quyết Định Nghiệm Thu Chính Thức (Official QC Review Verdict)."""
    err_n = report.error_count()
    warn_n = report.warning_count()

    if err_n > 0:
        verdict_badge = "🔴 TỪ CHỐI NGHIỆM THU (REJECTED)"
        verdict_color = "#ef4444"
        verdict_bg = "rgba(239, 68, 68, 0.12)"
        verdict_border = "rgba(239, 68, 68, 0.5)"
        verdict_desc = f"Phát hiện <strong>{err_n} lỗi kỹ thuật nghiêm trọng</strong> (ERROR). Bộ nhãn không đủ tiêu chuẩn để huấn luyện mô hình. Bắt buộc Annotator phải sửa chữa và nộp lại theo danh sách vi phạm bên dưới."
        stamp_text = "QC REJECTED"
        compliance_tag = '<span class="qc-tag" style="background: rgba(239,68,68,0.15); border: 1px solid rgba(239,68,68,0.4); color: #fca5a5;">TRAINING UNSAFE</span>'
    elif warn_n > 0:
        verdict_badge = "🟡 NGHIỆM THU CÓ ĐIỀU KIỆN (CONDITIONAL PASS)"
        verdict_color = "#f59e0b"
        verdict_bg = "rgba(245, 158, 11, 0.12)"
        verdict_border = "rgba(245, 158, 11, 0.5)"
        verdict_desc = f"Không có lỗi nghiêm trọng (0 Error), nhưng có <strong>{warn_n} cảnh báo</strong> (WARNING) cần Reviewer/Lead xác nhận ngoại lệ trước khi đưa vào pipeline chính thức."
        stamp_text = "CONDITIONAL"
        compliance_tag = '<span class="qc-tag" style="background: rgba(245,158,11,0.15); border: 1px solid rgba(245,158,11,0.4); color: #fde68a;">REVIEW REQUIRED</span>'
    else:
        verdict_badge = "🟢 PHÊ DUYỆT NGHIỆM THU (PASSED & APPROVED)"
        verdict_color = "#10b981"
        verdict_bg = "rgba(16, 185, 129, 0.12)"
        verdict_border = "rgba(16, 185, 129, 0.5)"
        verdict_desc = "Tất cả các nhãn kiểm tra đều thỏa mãn <strong>100% tiêu chuẩn kỹ thuật</strong> (0 Error, 0 Warning). Bộ dữ liệu hoàn hảo, sẵn sàng cho công đoạn huấn luyện mô hình Autonomous Driving."
        stamp_text = "QC APPROVED"
        compliance_tag = '<span class="qc-tag" style="background: rgba(16,185,129,0.15); border: 1px solid rgba(16,185,129,0.4); color: #a7f3d0;">TRAINING READY</span>'

    st.markdown(f"""
    <div style="background: {verdict_bg}; border: 1.5px solid {verdict_border}; border-radius: 12px; padding: 22px 28px; margin: 18px 0 24px 0; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px; box-shadow: 0 8px 30px rgba(0, 0, 0, 0.35); position: relative; overflow: hidden;">
        <div style="position: absolute; top: -10px; left: -10px; width: 6px; height: 120%; background: {verdict_color};"></div>
        <div class="qc-verdict-stamp" style="color: {verdict_color}; border-color: {verdict_color};">
            {stamp_text}
        </div>
        <div style="z-index: 1;">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 4px;">
                <span style="font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em; color: #94a3b8; font-weight: 700; font-family: 'JetBrains Mono', monospace;">SCALE NUCLEUS // QUALITY VERDICT</span>
                <span style="border: 1.5px solid {verdict_color}; color: {verdict_color}; padding: 1px 7px; border-radius: 4px; font-weight: 800; font-size: 0.68rem; font-family: 'JetBrains Mono', monospace;">OFFICIAL AUDIT</span>
                {compliance_tag}
            </div>
            <div style="font-size: 1.35rem; font-weight: 800; color: {verdict_color}; letter-spacing: -0.01em;">{verdict_badge}</div>
            <div style="color: #f1f5f9; font-size: 0.92rem; margin-top: 6px; line-height: 1.55; max-width: 820px;">{verdict_desc}</div>
            <div style="display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap;">
                <span class="qc-tag" style="background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.15); color: #cbd5e1;">ISO-26262 ROAD VEHICLES</span>
                <span class="qc-tag" style="background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.15); color: #cbd5e1;">BDD100K SPEC v2</span>
                <span class="qc-tag" style="background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.15); color: #cbd5e1;">SHAPELY TOPOLOGY AUDITED</span>
            </div>
        </div>
        <div style="text-align: right; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: #cbd5e1; background: #0b0f19; padding: 14px 20px; border-radius: 10px; border: 1px solid #1f2937; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4); z-index: 1;">
            <div style="font-size: 0.75rem; color: #94a3b8; text-transform: uppercase;">Tiêu chuẩn: <strong style="color: #f8fafc;">N2-04A / BDD100K</strong></div>
            <div style="margin-top: 6px;">Tỷ lệ đạt: <strong style="color: {verdict_color}; font-size: 1.3rem;">{pass_rate:.1f}%</strong></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
