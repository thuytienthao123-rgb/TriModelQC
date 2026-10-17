from __future__ import annotations
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

from qc.models import QCReport
from ui.constants import RULE_SUGGESTIONS
from ui.i18n import get_current_lang


def render_tab_analytics(report: QCReport, pass_rate: float, is_dark: bool):
    """Render Tab 3: Biểu đồ KPI, phân bố vi phạm theo Rule & Category."""
    lang = get_current_lang()
    total_issues = len(report.errors)

    if is_dark:
        bg_main = "#080c14"
        bg_header = "#0f1624"
        border_c = "#1e293b"
    else:
        bg_main = "#f8fafc"
        bg_header = "#ffffff"
        border_c = "#e2e8f0"

    if lang == "vi":
        header_title = "📊 Phân Tích Chất Lượng Dữ Liệu & Đo Lường Hiệu Quả"
        header_sub = "Đo lường các chỉ số Pilot đề tài N2-04A và tần suất vi phạm theo từng phân nhóm"
        benchmark_title = "🎯 Đánh Giá Hiệu Năng So Với Mục Tiêu Đề Tài (N2-04A)"
        lbl_auto = "Tỷ lệ bắt lỗi tự động trước review"
        lbl_auto_target = "(Mục tiêu: ≥ 90%)"
        status_auto = "🎉 ĐẠT CHUẨN" if pass_rate >= 90 else "⚠️ CẦN RÀ SOÁT"
        lbl_rework = "Số vòng trả bài/job ước tính"
        val_rework = "≤ 1 vòng"
        sub_rework_base = "(Baseline: 2–3 vòng)"
        sub_rework_eff = "⚡ Giảm ≥ 60% số vòng lặp"
        lbl_time = "Thời gian rà soát của Reviewer"
        val_time = "Tiết kiệm ≥ 65%"
        sub_time_eff = "🚀 Rút ngắn từ 10p → 3p/frame"
        no_data_msg = "Không có dữ liệu lỗi để vẽ biểu đồ."
        chart1_title = "##### 📌 Phân bố vi phạm theo Quy tắc (Rule)"
        chart1_ylabel = "Số lượng vi phạm"
        chart2_title = "##### 🚗 Phân bố vi phạm theo Loại nhãn (Category)"
        chart2_ylabel = "Số lượng vi phạm"
        table_title = "##### 📋 Bảng tần suất lỗi theo Quy tắc:"
        col_rule = "Mã Rule"
        col_total = "Tổng số lần"
        col_err = "Lỗi nghiêm trọng"
        col_warn = "Cảnh báo"
        col_sugg = "Gợi ý sửa nhanh"
    else:
        header_title = "📊 Quality Analytics & Performance Telemetry"
        header_sub = "Evaluation against Project N2-04A benchmarks and violation distributions"
        benchmark_title = "🎯 Performance Benchmarking vs. Project Target (N2-04A)"
        lbl_auto = "Automated Defect Catch Rate"
        lbl_auto_target = "(Target: ≥ 90%)"
        status_auto = "🎉 COMPLIANT" if pass_rate >= 90 else "⚠️ REVIEW REQUIRED"
        lbl_rework = "Estimated Review Rework Cycles"
        val_rework = "≤ 1 cycle"
        sub_rework_base = "(Baseline: 2–3 cycles)"
        sub_rework_eff = "⚡ ≥ 60% cycle reduction"
        lbl_time = "Reviewer Audit Turnaround Time"
        val_time = "Saved ≥ 65%"
        sub_time_eff = "🚀 Reduced from 10m → 3m/frame"
        no_data_msg = "No defect data available to plot charts."
        chart1_title = "##### 📌 Defect Distribution by Rule"
        chart1_ylabel = "Violation Count"
        chart2_title = "##### 🚗 Defect Distribution by Category"
        chart2_ylabel = "Violation Count"
        table_title = "##### 📋 Violation Frequency Table by Rule:"
        col_rule = "Rule ID"
        col_total = "Total Count"
        col_err = "Critical Errors"
        col_warn = "Warnings"
        col_sugg = "Suggested Remedy"

    st.markdown(f"""
    <div style="margin-bottom: 16px;">
        <h3 style="margin: 0; color: #f8fafc; font-size: 1.25rem;">{header_title}</h3>
        <p style="margin: 2px 0 0 0; color: #94a3b8; font-size: 0.85rem;">{header_sub}</p>
    </div>
    """, unsafe_allow_html=True)

    auto_detect_color = "#34d399" if pass_rate >= 90 else "#fbbf24"

    st.markdown(f"""
    <div class="benchmark-card">
        <div style="font-weight: 700; font-size: 0.95rem; color: #f8fafc; display: flex; align-items: center; gap: 8px;">
            <span>{benchmark_title}</span>
        </div>
        <div class="benchmark-grid">
            <div class="benchmark-item">
                <div class="benchmark-label">{lbl_auto}</div>
                <div class="benchmark-val" style="color: {auto_detect_color};">{pass_rate:.1f}% <span style="font-size: 0.75rem; color: #94a3b8;">{lbl_auto_target}</span></div>
                <div style="font-size: 0.75rem; color: {auto_detect_color}; font-weight: 600; margin-top: 2px;">{status_auto}</div>
            </div>
            <div class="benchmark-item">
                <div class="benchmark-label">{lbl_rework}</div>
                <div class="benchmark-val" style="color: #38bdf8;">{val_rework} <span style="font-size: 0.75rem; color: #94a3b8;">{sub_rework_base}</span></div>
                <div style="font-size: 0.75rem; color: #34d399; font-weight: 600; margin-top: 2px;">{sub_rework_eff}</div>
            </div>
            <div class="benchmark-item">
                <div class="benchmark-label">{lbl_time}</div>
                <div class="benchmark-val" style="color: #c084fc;">{val_time}</div>
                <div style="font-size: 0.75rem; color: #34d399; font-weight: 600; margin-top: 2px;">{sub_time_eff}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if total_issues == 0:
        st.info(no_data_msg)
        return

    ccol1, ccol2 = st.columns(2)

    with ccol1:
        st.markdown(chart1_title)
        rule_counts = pd.Series([e.rule_id for e in report.errors]).value_counts()
        fig_r, ax_r = plt.subplots(figsize=(6, 4))
        ax_r.set_facecolor(bg_header)
        fig_r.patch.set_facecolor(bg_main)
        bars = ax_r.bar(rule_counts.index, rule_counts.values, color="#38bdf8", edgecolor="#0284c7", linewidth=1.2)
        ax_r.set_ylabel(chart1_ylabel, color="#94a3b8")
        ax_r.tick_params(colors="#e2e8f0")
        for spine in ax_r.spines.values():
            spine.set_color(border_c)
        for bar in bars:
            yval = bar.get_height()
            ax_r.text(bar.get_x() + bar.get_width()/2.0, yval + 0.1, int(yval), ha="center", va="bottom", color="#7dd3fc", weight="bold")
        fig_r.tight_layout()
        st.pyplot(fig_r)

    with ccol2:
        st.markdown(chart2_title)
        cat_counts = pd.Series([e.category for e in report.errors]).value_counts()
        fig_c, ax_c = plt.subplots(figsize=(6, 4))
        ax_c.set_facecolor(bg_header)
        fig_c.patch.set_facecolor(bg_main)
        bars_c = ax_c.bar(cat_counts.index, cat_counts.values, color="#f472b6", edgecolor="#db2777", linewidth=1.2)
        ax_c.set_ylabel(chart2_ylabel, color="#94a3b8")
        ax_c.tick_params(colors="#e2e8f0", rotation=25)
        for spine in ax_c.spines.values():
            spine.set_color(border_c)
        for bar in bars_c:
            yval = bar.get_height()
            ax_c.text(bar.get_x() + bar.get_width()/2.0, yval + 0.1, int(yval), ha="center", va="bottom", color="#fbcfe8", weight="bold")
        fig_c.tight_layout()
        st.pyplot(fig_c)

    st.markdown(table_title)
    summary_rows = []
    for r_id in sorted(list(set(e.rule_id for e in report.errors))):
        errs_r = [e for e in report.errors if e.rule_id == r_id]
        err_c = sum(1 for e in errs_r if e.is_error())
        warn_c = sum(1 for e in errs_r if e.is_warning())
        default_sugg = "Kiểm tra và sửa theo quy chuẩn BDD100K." if lang == "vi" else "Inspect and fix according to BDD100K standard."
        summary_rows.append({
            col_rule: r_id,
            col_total: len(errs_r),
            col_err: err_c,
            col_warn: warn_c,
            col_sugg: RULE_SUGGESTIONS.get(r_id, default_sugg),
        })
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)
