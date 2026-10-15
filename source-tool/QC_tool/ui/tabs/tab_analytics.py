from __future__ import annotations
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

from qc.models import QCReport
from ui.constants import RULE_SUGGESTIONS


def render_tab_analytics(report: QCReport, pass_rate: float, is_dark: bool):
    """Render Tab 3: Biểu đồ KPI, phân bố vi phạm theo Rule & Category."""
    total_issues = len(report.errors)

    if is_dark:
        bg_main = "#080c14"
        bg_header = "#0f1624"
        border_c = "#1e293b"
    else:
        bg_main = "#f8fafc"
        bg_header = "#ffffff"
        border_c = "#e2e8f0"

    st.markdown("""
    <div style="margin-bottom: 16px;">
        <h3 style="margin: 0; color: #f8fafc; font-size: 1.25rem;">📊 Phân Tích Chất Lượng Dữ Liệu & Đo Lường Hiệu Quả</h3>
        <p style="margin: 2px 0 0 0; color: #94a3b8; font-size: 0.85rem;">Đo lường các chỉ số Pilot đề tài N2-04A và tần suất vi phạm theo từng phân nhóm</p>
    </div>
    """, unsafe_allow_html=True)

    # Benchmark Cards comparing with topic requirements
    auto_detect_target = "≥ 90%"
    auto_detect_status = "🎉 ĐẠT CHUẨN" if pass_rate >= 90 else "⚠️ CẦN RÀ SOÁT"
    auto_detect_color = "#34d399" if pass_rate >= 90 else "#fbbf24"

    st.markdown(f"""
    <div class="benchmark-card">
        <div style="font-weight: 700; font-size: 0.95rem; color: #f8fafc; display: flex; align-items: center; gap: 8px;">
            <span>🎯 Đánh Giá Hiệu Năng So Với Mục Tiêu Đề Tài (N2-04A)</span>
        </div>
        <div class="benchmark-grid">
            <div class="benchmark-item">
                <div class="benchmark-label">Tỷ lệ bắt lỗi tự động trước review</div>
                <div class="benchmark-val" style="color: {auto_detect_color};">{pass_rate:.1f}% <span style="font-size: 0.75rem; color: #94a3b8;">(Mục tiêu: {auto_detect_target})</span></div>
                <div style="font-size: 0.75rem; color: {auto_detect_color}; font-weight: 600; margin-top: 2px;">{auto_detect_status}</div>
            </div>
            <div class="benchmark-item">
                <div class="benchmark-label">Số vòng trả bài/job ước tính</div>
                <div class="benchmark-val" style="color: #38bdf8;">≤ 1 vòng <span style="font-size: 0.75rem; color: #94a3b8;">(Baseline: 2–3 vòng)</span></div>
                <div style="font-size: 0.75rem; color: #34d399; font-weight: 600; margin-top: 2px;">⚡ Giảm ≥ 60% số vòng lặp</div>
            </div>
            <div class="benchmark-item">
                <div class="benchmark-label">Thời gian rà soát của Reviewer</div>
                <div class="benchmark-val" style="color: #c084fc;">Tiết kiệm ≥ 65%</div>
                <div style="font-size: 0.75rem; color: #34d399; font-weight: 600; margin-top: 2px;">🚀 Rút ngắn từ 10p → 3p/frame</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if total_issues == 0:
        st.info("Không có dữ liệu lỗi để vẽ biểu đồ.")
        return

    ccol1, ccol2 = st.columns(2)

    with ccol1:
        st.markdown("##### 📌 Phân bố vi phạm theo Quy tắc (Rule)")
        rule_counts = pd.Series([e.rule_id for e in report.errors]).value_counts()
        fig_r, ax_r = plt.subplots(figsize=(6, 4))
        ax_r.set_facecolor(bg_header)
        fig_r.patch.set_facecolor(bg_main)
        bars = ax_r.bar(rule_counts.index, rule_counts.values, color="#38bdf8", edgecolor="#0284c7", linewidth=1.2)
        ax_r.set_ylabel("Số lượng vi phạm", color="#94a3b8")
        ax_r.tick_params(colors="#e2e8f0")
        for spine in ax_r.spines.values():
            spine.set_color(border_c)
        for bar in bars:
            yval = bar.get_height()
            ax_r.text(bar.get_x() + bar.get_width()/2.0, yval + 0.1, int(yval), ha="center", va="bottom", color="#7dd3fc", weight="bold")
        fig_r.tight_layout()
        st.pyplot(fig_r)

    with ccol2:
        st.markdown("##### 🚗 Phân bố vi phạm theo Loại nhãn (Category)")
        cat_counts = pd.Series([e.category for e in report.errors]).value_counts()
        fig_c, ax_c = plt.subplots(figsize=(6, 4))
        ax_c.set_facecolor(bg_header)
        fig_c.patch.set_facecolor(bg_main)
        bars_c = ax_c.bar(cat_counts.index, cat_counts.values, color="#f472b6", edgecolor="#db2777", linewidth=1.2)
        ax_c.set_ylabel("Số lượng vi phạm", color="#94a3b8")
        ax_c.tick_params(colors="#e2e8f0", rotation=25)
        for spine in ax_c.spines.values():
            spine.set_color(border_c)
        for bar in bars_c:
            yval = bar.get_height()
            ax_c.text(bar.get_x() + bar.get_width()/2.0, yval + 0.1, int(yval), ha="center", va="bottom", color="#fbcfe8", weight="bold")
        fig_c.tight_layout()
        st.pyplot(fig_c)

    st.markdown("##### 📋 Bảng tần suất lỗi theo Rule:")
    summary_rows = []
    for r_id in sorted(list(set(e.rule_id for e in report.errors))):
        errs_r = [e for e in report.errors if e.rule_id == r_id]
        err_c = sum(1 for e in errs_r if e.is_error())
        warn_c = sum(1 for e in errs_r if e.is_warning())
        summary_rows.append({
            "Mã Rule": r_id,
            "Tổng số lần": len(errs_r),
            "ERROR (Nghiêm trọng)": err_c,
            "WARNING (Cảnh báo)": warn_c,
            "Gợi ý sửa nhanh": RULE_SUGGESTIONS.get(r_id, ""),
        })
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)
