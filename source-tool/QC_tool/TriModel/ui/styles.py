from __future__ import annotations
import streamlit as st
import streamlit.components.v1 as components


def apply_custom_css(is_dark: bool = True):
    """
    Áp dụng hệ thống Design System chuẩn Scale Nucleus Pro với khả năng
    tự động thích ứng 100% giữa Sáng (Light) và Tối (Dark).
    """
    bg_main = "#080c14" if is_dark else "#f8fafc"
    bg_sidebar = "#0b101b" if is_dark else "#ffffff"
    bg_header = "#0f1626" if is_dark else "#ffffff"
    bg_card = "#111827" if is_dark else "#ffffff"
    bg_card_sub = "#141d30" if is_dark else "#f1f5f9"
    border_c = "#1e293b" if is_dark else "#cbd5e1"
    border_header = "#00e5ff" if is_dark else "#0284c7"
    text_main = "#f8fafc" if is_dark else "#0f172a"
    text_sub = "#94a3b8" if is_dark else "#334155"
    text_muted = "#cbd5e1" if is_dark else "#475569"
    val_cyan = "#00e5ff" if is_dark else "#0284c7"
    val_indigo = "#818cf8" if is_dark else "#4f46e5"
    val_rose = "#f43f5e" if is_dark else "#e11d48"
    val_amber = "#fbbf24" if is_dark else "#d97706"
    val_emerald = "#10b981" if is_dark else "#059669"
    box_shadow = "0 8px 30px rgba(0, 0, 0, 0.5)" if is_dark else "0 4px 20px rgba(0, 0, 0, 0.08)"
    badge_err_bg = "rgba(244, 63, 94, 0.15)" if is_dark else "#fee2e2"
    badge_err_txt = "#fca5a5" if is_dark else "#b91c1c"
    badge_warn_bg = "rgba(245, 158, 11, 0.15)" if is_dark else "#fef3c7"
    badge_warn_txt = "#fde68a" if is_dark else "#b45309"
    badge_ok_bg = "rgba(16, 185, 129, 0.15)" if is_dark else "#d1fae5"
    badge_ok_txt = "#a7f3d0" if is_dark else "#047857"
    tab_active_bg = "rgba(0, 229, 255, 0.08)" if is_dark else "rgba(2, 132, 199, 0.08)"
    glow_cyan = "0 0 20px rgba(0, 229, 255, 0.25)" if is_dark else "0 0 15px rgba(2, 132, 199, 0.18)"

    css_content = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    /* =========================================================================
       DYNAMIC ACTIVE THEME VARIABLES
       ========================================================================= */
    :root, html, body, .stApp, [data-theme], [data-testid="stSidebar"], [data-testid="stSidebarContent"], header[data-testid="stHeader"] {{
        --bg-main: {bg_main} !important;
        --bg-sidebar: {bg_sidebar} !important;
        --bg-header: {bg_header} !important;
        --bg-card: {bg_card} !important;
        --bg-card-sub: {bg_card_sub} !important;
        --border-c: {border_c} !important;
        --border-header: {border_header} !important;
        --text-main: {text_main} !important;
        --text-sub: {text_sub} !important;
        --text-muted: {text_muted} !important;
        --val-cyan: {val_cyan} !important;
        --val-indigo: {val_indigo} !important;
        --val-rose: {val_rose} !important;
        --val-amber: {val_amber} !important;
        --val-emerald: {val_emerald} !important;
        --box-shadow: {box_shadow} !important;
        --badge-err-bg: {badge_err_bg} !important;
        --badge-err-txt: {badge_err_txt} !important;
        --badge-warn-bg: {badge_warn_bg} !important;
        --badge-warn-txt: {badge_warn_txt} !important;
        --badge-ok-bg: {badge_ok_bg} !important;
        --badge-ok-txt: {badge_ok_txt} !important;
        --tab-active-bg: {tab_active_bg} !important;
        --glow-cyan: {glow_cyan} !important;
    }}

    .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], section.main, .block-container {{
        background-color: {bg_main} !important;
        color: {text_main} !important;
    }}

    section[data-testid="stSidebar"], [data-testid="stSidebar"], [data-testid="stSidebarContent"], [data-testid="stSidebarNav"] {{
        background-color: {bg_sidebar} !important;
        border-right: 1px solid {border_c} !important;
    }}

    .qc-header-box, .welcome-banner, .feature-card, .benchmark-card, .benchmark-item, .qc-kpi-card, [data-testid="stMetric"], [data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: {bg_card} !important;
        border-color: {border_c} !important;
        color: {text_main} !important;
    }}
    """
    st.markdown(css_content, unsafe_allow_html=True)

    st.markdown("""
    <style>

    /* -------------------------------------------------------------------------
       VẤN ĐỀ 1: THU GỌN THANH HEADER TRÊN CÙNG & DỊCH CHUYỂN DEPLOY LÊN GÓC PHẢI
       Thu hồi khoảng trống lãng phí đầu trang, giữ Deploy & 3-dots gọn ở góc trên phải.
       ------------------------------------------------------------------------- */
    header[data-testid="stHeader"] {
        height: 2.6rem !important;
        min-height: 2.6rem !important;
        background: var(--bg-main) !important;
        border-bottom: 1px solid var(--border-c) !important;
        padding: 0 1rem !important;
        margin: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-end !important;
        z-index: 99999 !important;
        position: relative !important;
    }

    [data-testid="stToolbar"] {
        position: absolute !important;
        top: 4px !important;
        right: 12px !important;
        z-index: 1000000 !important;
        display: flex !important;
        align-items: center !important;
        gap: 6px !important;
    }

    /* Thu gọn toàn bộ padding khoảng trống đầu trang */
    .block-container,
    [data-testid="stMainBlockContainer"],
    .stMain .block-container,
    .main .block-container,
    div[data-testid="stAppViewContainer"] section.main .block-container {
        padding-top: 0.6rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 100% !important;
    }

    /* Đảm bảo cuộn chuột (Mouse Wheel Scroll) mượt mà 100% */
    [data-testid="stAppViewContainer"] {
        overflow-y: auto !important;
        overflow-x: hidden !important;
    }
    .main {
        overflow-y: visible !important;
    }

    /* Chỉ ẩn iframe 0px của script đồng bộ, không ẩn custom components khác */
    iframe[height="0"],
    iframe[width="0"],
    div.element-container:has(> iframe[height="0"]),
    div.element-container:has(> div > iframe[height="0"]) {
        position: fixed !important;
        bottom: -200px !important;
        left: -200px !important;
        width: 1px !important;
        height: 1px !important;
        opacity: 0 !important;
        pointer-events: none !important;
        z-index: -9999 !important;
    }

    .qc-header-box {
        background: var(--bg-card);
        border: 1px solid var(--border-c);
        border-radius: 12px;
        padding: 12px 18px;
        margin-top: 0 !important;
        margin-bottom: 14px;
        box-shadow: var(--box-shadow);
        border-left: 4px solid var(--val-cyan);
    }

    /* -------------------------------------------------------------------------
       VẤN ĐỀ 2: CẤU TRÚC GIAO DIỆN & TỰ ĐỘNG THÍCH ỨNG THEME SÁNG / TỐI
       ------------------------------------------------------------------------- */
    .stApp {
        background-color: var(--bg-main) !important;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        color: var(--text-main) !important;
    }

    [data-testid="stSidebar"] {
        background-color: var(--bg-sidebar) !important;
        border-right: 1px solid var(--border-c) !important;
    }

    [data-testid="stSidebar"] * {
        color: var(--text-main);
    }

    [data-testid="stSidebar"] .stCaption,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label {
        color: var(--text-sub) !important;
    }

    .stApp p, .stApp span, .stApp label {
        color: var(--text-main);
    }

    /* Tab bar */
    [data-baseweb="tab-list"] {
        gap: 8px !important;
        border-bottom: 2px solid var(--border-c) !important;
        padding-bottom: 4px !important;
        background: transparent !important;
    }
    [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0 !important;
        padding: 9px 20px !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        color: var(--text-sub) !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
        border: 1px solid transparent !important;
        background: transparent !important;
    }
    [data-baseweb="tab"]:hover {
        color: var(--val-cyan) !important;
        background: var(--tab-active-bg) !important;
        border-color: rgba(0, 229, 255, 0.2) !important;
    }
    [data-baseweb="tab"][aria-selected="true"] {
        background: var(--tab-active-bg) !important;
        border-bottom: 2px solid var(--val-cyan) !important;
        color: var(--val-cyan) !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 15px -3px rgba(0, 229, 255, 0.25) !important;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        padding: 7px 16px !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
        border: 1px solid var(--border-c) !important;
        background: var(--bg-card) !important;
        color: var(--text-main) !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05) !important;
    }
    .stButton > button:hover {
        transform: translateY(-1.5px) !important;
        border-color: var(--val-cyan) !important;
        color: var(--val-cyan) !important;
        box-shadow: var(--box-shadow) !important;
    }
    .stButton > button:active {
        transform: translateY(0.5px) !important;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--val-cyan) 0%, #0284c7 100%) !important;
        color: #ffffff !important;
        font-weight: 800 !important;
        border: none !important;
        box-shadow: var(--glow-cyan) !important;
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 0 25px rgba(0, 229, 255, 0.55) !important;
        transform: translateY(-2px) !important;
    }

    /* =========================================================================
       SIDEBAR & WIDGET THEME UNIFORMITY (ĐỒNG NHẤT NỀN SIDEBAR SÁNG & TỐI)
       ========================================================================= */
    /* 1. Selectbox & Dropdown Popovers */
    div[data-baseweb="select"],
    div[data-baseweb="select"] > div,
    div[data-baseweb="select"] [role="combobox"],
    div[data-baseweb="select"] input {
        background-color: var(--bg-card-sub) !important;
        border-color: var(--border-c) !important;
        color: var(--text-main) !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] svg {
        color: var(--text-main) !important;
        fill: var(--text-main) !important;
    }
    div[data-baseweb="popover"],
    div[data-baseweb="menu"],
    ul[role="listbox"],
    li[role="option"] {
        background-color: var(--bg-card) !important;
        color: var(--text-main) !important;
        border: 1px solid var(--border-c) !important;
    }
    li[role="option"]:hover,
    li[role="option"][aria-selected="true"] {
        background-color: var(--tab-active-bg) !important;
        color: var(--val-cyan) !important;
    }

    /* 2. File Uploader Dropzone & Uploaded File Items */
    [data-testid="stFileUploader"],
    [data-testid="stFileUploader"] section,
    section[data-testid="stFileUploadDropzone"],
    div[data-baseweb="file-uploader"] {
        background-color: var(--bg-card-sub) !important;
        border: 1.5px dashed var(--border-c) !important;
        border-radius: 10px !important;
        color: var(--text-main) !important;
    }
    section[data-testid="stFileUploadDropzone"]:hover {
        border-color: var(--val-cyan) !important;
    }
    section[data-testid="stFileUploadDropzone"] * {
        color: var(--text-sub) !important;
    }
    section[data-testid="stFileUploadDropzone"] button {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-c) !important;
        color: var(--text-main) !important;
        border-radius: 6px !important;
    }
    section[data-testid="stFileUploadDropzone"] button:hover {
        border-color: var(--val-cyan) !important;
        color: var(--val-cyan) !important;
    }
    /* Uploaded File list chips/cards in dark & light */
    [data-testid="stUploadedFile"],
    div[data-testid="stFileUploaderFile"],
    ul[data-testid="stFileUploaderFile"] li,
    ul[data-testid="stFileUploaderFile"] {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-c) !important;
        border-radius: 8px !important;
        color: var(--text-main) !important;
    }
    [data-testid="stUploadedFile"] *,
    div[data-testid="stFileUploaderFile"] * {
        color: var(--text-main) !important;
    }
    [data-testid="stUploadedFile"] svg,
    div[data-testid="stFileUploaderFile"] svg {
        fill: var(--val-cyan) !important;
    }

    /* 3. Sidebar Buttons (Đổi bộ ảnh, Scan thư mục, Reset) */
    [data-testid="stSidebar"] .stButton > button,
    [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
        background-color: var(--bg-card-sub) !important;
        border: 1px solid var(--border-c) !important;
        color: var(--text-main) !important;
        border-radius: 8px !important;
        box-shadow: none !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover,
    [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover {
        border-color: var(--val-cyan) !important;
        color: var(--val-cyan) !important;
        background-color: var(--bg-card) !important;
    }

    /* 4. Text & Number Inputs in Sidebar & Main */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    [data-testid="stSidebar"] input {
        background-color: var(--bg-card-sub) !important;
        border-color: var(--border-c) !important;
        color: var(--text-main) !important;
        border-radius: 8px !important;
    }
    .stTextInput input:focus,
    .stNumberInput input:focus,
    [data-testid="stSidebar"] input:focus {
        border-color: var(--val-cyan) !important;
        box-shadow: 0 0 0 1px var(--val-cyan) !important;
    }

    /* 5. Radio Buttons & Checkboxes inside Sidebar */
    [data-testid="stSidebar"] div[role="radiogroup"] label,
    [data-testid="stSidebar"] .stCheckbox label,
    [data-testid="stSidebar"] label p,
    [data-testid="stSidebar"] label span {
        color: var(--text-main) !important;
    }

    /* 6. Expanders in Sidebar */
    [data-testid="stSidebar"] [data-testid="stExpander"],
    [data-testid="stSidebar"] details {
        background-color: var(--bg-card-sub) !important;
        border: 1px solid var(--border-c) !important;
        border-radius: 8px !important;
        color: var(--text-main) !important;
    }
    [data-testid="stSidebar"] summary {
        color: var(--text-main) !important;
    }

    /* Header Box - Tinh gọn, đặt sát mép trên */
    .qc-header-box {
        background: var(--bg-header);
        border: 1px solid var(--border-c);
        border-bottom: 2px solid var(--border-header);
        border-radius: 12px;
        padding: 10px 20px;
        margin: 0 0 1rem 0;
        box-shadow: var(--box-shadow);
        position: relative;
        overflow: hidden;
    }

    .qc-header-title {
        font-size: 1.15rem;
        font-weight: 800;
        letter-spacing: -0.015em;
        line-height: 1.25;
        color: var(--text-main) !important;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .qc-header-sub {
        font-size: 0.74rem;
        line-height: 1.2;
        color: var(--text-sub) !important;
        margin: 2px 0 0 0;
        font-weight: 400;
    }

    .qc-tag-row {
        display: flex;
        align-items: center;
        gap: 6px;
        flex-wrap: wrap;
    }

    .qc-tag {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 2.5px 8px;
        border-radius: 5px;
        font-size: 0.68rem;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }

    .qc-tag-cyan {
        background: rgba(0, 229, 255, 0.12);
        color: var(--val-cyan) !important;
        border: 1px solid rgba(0, 229, 255, 0.35);
    }

    .qc-tag-purple {
        background: rgba(129, 140, 248, 0.12);
        color: var(--val-indigo) !important;
        border: 1px solid rgba(129, 140, 248, 0.35);
    }

    .qc-tag-online {
        background: rgba(16, 185, 129, 0.12);
        color: var(--val-emerald) !important;
        border: 1px solid rgba(16, 185, 129, 0.35);
    }

    .pulse-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: var(--val-emerald);
        box-shadow: 0 0 8px var(--val-emerald);
        animation: pulse 1.8s infinite;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.4; transform: scale(0.85); }
    }

    /* KPI Cards */
    .qc-kpi-card {
        background: var(--bg-card);
        border: 1px solid var(--border-c);
        border-radius: 10px;
        padding: 14px 16px;
        transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1);
        position: relative;
        overflow: hidden;
        margin-bottom: 0.5rem;
    }

    .qc-kpi-card:hover {
        border-color: var(--val-cyan);
        transform: translateY(-2.5px);
        box-shadow: var(--box-shadow);
    }

    .qc-kpi-cyan { border-left: 3.5px solid var(--val-cyan); }
    .qc-kpi-indigo { border-left: 3.5px solid var(--val-indigo); }
    .qc-kpi-rose { border-left: 3.5px solid var(--val-rose); }
    .qc-kpi-amber { border-left: 3.5px solid var(--val-amber); }
    .qc-kpi-emerald { border-left: 3.5px solid var(--val-emerald); }

    .qc-kpi-label {
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--text-sub) !important;
        margin-bottom: 4px;
        font-family: 'JetBrains Mono', monospace;
    }

    .qc-kpi-val {
        font-size: 1.88rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        line-height: 1.1;
        font-family: 'JetBrains Mono', monospace;
    }

    .val-cyan { color: var(--val-cyan) !important; }
    .val-indigo { color: var(--val-indigo) !important; }
    .val-rose { color: var(--val-rose) !important; }
    .val-amber { color: var(--val-amber) !important; }
    .val-emerald { color: var(--val-emerald) !important; }

    .qc-kpi-sub {
        font-size: 0.74rem;
        color: var(--text-sub) !important;
        margin-top: 4px;
    }

    /* Badges */
    .badge-err {
        background: var(--badge-err-bg);
        color: var(--badge-err-txt) !important;
        border: 1px solid rgba(239, 68, 68, 0.4);
        padding: 3px 9px;
        border-radius: 6px;
        font-size: 0.74rem;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        display: inline-block;
    }

    .badge-warn {
        background: var(--badge-warn-bg);
        color: var(--badge-warn-txt) !important;
        border: 1px solid rgba(245, 158, 11, 0.4);
        padding: 3px 9px;
        border-radius: 6px;
        font-size: 0.74rem;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        display: inline-block;
    }

    .badge-ok {
        background: var(--badge-ok-bg);
        color: var(--badge-ok-txt) !important;
        border: 1px solid rgba(16, 185, 129, 0.4);
        padding: 3px 9px;
        border-radius: 6px;
        font-size: 0.74rem;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        display: inline-block;
    }

    .feature-card {
        background: var(--bg-card);
        border: 1px solid var(--border-c);
        border-radius: 10px;
        padding: 16px 18px;
        height: 100%;
        transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.2s ease;
    }
    .feature-card:hover {
        transform: translateY(-2.5px);
        border-color: var(--val-cyan);
        box-shadow: var(--box-shadow);
    }
    .feature-title {
        font-size: 0.94rem;
        font-weight: 700;
        color: var(--text-main) !important;
        margin-bottom: 6px;
    }
    .feature-desc {
        font-size: 0.8rem;
        color: var(--text-sub) !important;
        line-height: 1.55;
    }

    .welcome-banner {
        background: var(--bg-card);
        border: 1px solid var(--border-c);
        border-radius: 14px;
        padding: 18px 22px;
        margin-bottom: 18px;
        box-shadow: var(--box-shadow);
    }
    .welcome-banner h3 {
        margin-top: 0;
        color: var(--text-main) !important;
        font-size: 1.18rem;
    }
    .welcome-banner p {
        color: var(--text-sub) !important;
        font-size: 0.86rem;
        line-height: 1.5;
        margin-bottom: 0;
    }

    .benchmark-card {
        background: var(--bg-card);
        border: 1px solid var(--border-c);
        border-radius: 10px;
        padding: 18px 20px;
        margin-bottom: 14px;
    }
    .benchmark-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 12px;
        margin-top: 12px;
    }
    .benchmark-item {
        background: var(--bg-card-sub);
        border: 1px solid var(--border-c);
        border-radius: 8px;
        padding: 12px 14px;
    }
    .benchmark-label {
        font-size: 0.74rem;
        color: var(--text-sub) !important;
        font-weight: 600;
    }
    .benchmark-val {
        font-size: 1.25rem;
        font-weight: 800;
        font-family: 'JetBrains Mono', monospace;
        margin: 4px 0 2px 0;
        color: var(--text-main) !important;
    }

    /* Metric elements in light/dark */
    [data-testid="stMetric"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-c) !important;
        border-radius: 8px !important;
        padding: 10px 14px !important;
    }
    [data-testid="stMetricValue"] * {
        color: var(--text-main) !important;
    }
    [data-testid="stMetricLabel"] * {
        color: var(--text-sub) !important;
    }

    /* Progress bar */
    .qc-progress-track {
        width: 100%;
        height: 5px;
        background: rgba(148, 163, 184, 0.18);
        border-radius: 999px;
        margin-top: 8px;
        overflow: hidden;
    }
    .qc-progress-fill {
        height: 100%;
        border-radius: 999px;
        transition: width 0.6s ease;
    }
    </style>
    """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # CLIENT-SIDE DYNAMIC THEME DETECTOR & SYNCHRONIZER
    # Tự động phát hiện khi người dùng chuyển theme Sáng / Tối trong menu 3 chấm
    # và lập tức đồng bộ toàn bộ giao diện app không bị xung đột màu sắc.
    # -------------------------------------------------------------------------
    components.html("""
    <script>
    (function() {
        function checkAndApplyTheme() {
            try {
                const pWin = window.parent;
                const pDoc = pWin.document;
                let detected = null;

                // 1. Kiểm tra React fiber theme trên .stApp (Nguồn sự thật chính xác nhất của Streamlit)
                const app = pDoc.querySelector('.stApp');
                if (app) {
                    const fk = Object.keys(app).find(k => k.startsWith('__reactFiber'));
                    if (fk && app[fk]) {
                        let cur = app[fk];
                        for (let d = 0; d < 30 && cur; d++) {
                            if (cur.memoizedProps && cur.memoizedProps.theme) {
                                const th = cur.memoizedProps.theme;
                                const base = (th.base || th.name || '').toLowerCase();
                                if (base.includes('light')) { detected = 'light'; break; }
                                if (base.includes('dark')) { detected = 'dark'; break; }
                            }
                            cur = cur.return;
                        }
                    }
                }

                // 2. Kiểm tra Streamlit MainMenu button icon (3 chấm)
                if (!detected) {
                    const menuBtn = pDoc.querySelector('[data-testid="stMainMenu"] svg') || pDoc.querySelector('[data-testid="stToolbar"] svg');
                    if (menuBtn) {
                        const c = pWin.getComputedStyle(menuBtn).fill || pWin.getComputedStyle(menuBtn).color;
                        const m = c.match(/\d+/g);
                        if (m && m.length >= 3) {
                            const lum = (parseInt(m[0])*299 + parseInt(m[1])*587 + parseInt(m[2])*114) / 1000;
                            if (lum < 130) detected = 'light';
                            else if (lum > 180) detected = 'dark';
                        }
                    }
                }

                // 3. Fallback: matchMedia
                if (!detected) {
                    if (pWin.matchMedia && pWin.matchMedia('(prefers-color-scheme: light)').matches) {
                        detected = 'light';
                    } else {
                        detected = 'dark';
                    }
                }

                const isLight = """ + ("false" if is_dark else "true") + """;

                // 4. Áp dụng class theme tương ứng
                if (isLight) {
                    pDoc.documentElement.classList.add('theme-light');
                    pDoc.documentElement.classList.remove('theme-dark');
                    pDoc.body.classList.add('theme-light');
                    pDoc.body.classList.remove('theme-dark');
                    pDoc.documentElement.setAttribute('data-theme', 'light');
                    if (app) {
                        app.classList.add('theme-light');
                        app.classList.remove('theme-dark');
                        app.setAttribute('data-theme', 'light');
                    }
                } else {
                    pDoc.documentElement.classList.add('theme-dark');
                    pDoc.documentElement.classList.remove('theme-light');
                    pDoc.body.classList.add('theme-dark');
                    pDoc.body.classList.remove('theme-light');
                    pDoc.documentElement.setAttribute('data-theme', 'dark');
                    if (app) {
                        app.classList.add('theme-dark');
                        app.classList.remove('theme-light');
                        app.setAttribute('data-theme', 'dark');
                    }
                }
                // Xóa bỏ hoàn toàn floating button nếu còn tồn tại
                const floatBtn = pDoc.getElementById('quick-theme-floating-btn');
                if (floatBtn) {
                    floatBtn.remove();
                }

                // Tự động gắn thanh kéo độ rộng mép phải sidebar
                initSidebarResizer();
            } catch(e) {}
        }

        function initSidebarResizer() {
            try {
                const pWin = window.parent;
                const pDoc = pWin.document;
                const sidebar = pDoc.querySelector('section[data-testid="stSidebar"]');
                if (!sidebar) return;

                let resizer = pDoc.getElementById('sidebar-drag-resizer');
                if (!resizer) {
                    resizer = pDoc.createElement('div');
                    resizer.id = 'sidebar-drag-resizer';
                    resizer.title = 'Kéo mép này để chỉnh độ rộng sidebar (Double click để về mặc định)';
                    resizer.style.position = 'absolute';
                    resizer.style.top = '0';
                    resizer.style.right = '-3px';
                    resizer.style.width = '7px';
                    resizer.style.height = '100%';
                    resizer.style.cursor = 'col-resize';
                    resizer.style.zIndex = '999999';
                    resizer.style.backgroundColor = 'transparent';
                    resizer.style.transition = 'background-color 0.15s ease';

                    resizer.addEventListener('mouseenter', () => {
                        resizer.style.backgroundColor = 'rgba(0, 229, 255, 0.45)';
                    });
                    resizer.addEventListener('mouseleave', () => {
                        if (!resizer.dataset.dragging) {
                            resizer.style.backgroundColor = 'transparent';
                        }
                    });

                    let isDragging = false;
                    let startX = 0;
                    let startWidth = 0;

                    resizer.addEventListener('mousedown', (e) => {
                        isDragging = true;
                        resizer.dataset.dragging = 'true';
                        startX = e.clientX;
                        startWidth = sidebar.getBoundingClientRect().width;
                        resizer.style.backgroundColor = '#00e5ff';
                        pDoc.body.style.cursor = 'col-resize';
                        pDoc.body.style.userSelect = 'none';
                        e.preventDefault();
                    });

                    pDoc.addEventListener('mousemove', (e) => {
                        if (!isDragging) return;
                        const delta = e.clientX - startX;
                        const newWidth = Math.max(220, Math.min(680, startWidth + delta));
                        sidebar.style.width = newWidth + 'px';
                        sidebar.style.minWidth = newWidth + 'px';
                        sidebar.style.maxWidth = newWidth + 'px';
                        try {
                            localStorage.setItem('trimodel_sidebar_w', newWidth);
                        } catch(err) {}
                    });

                    pDoc.addEventListener('mouseup', () => {
                        if (isDragging) {
                            isDragging = false;
                            delete resizer.dataset.dragging;
                            resizer.style.backgroundColor = 'transparent';
                            pDoc.body.style.cursor = '';
                            pDoc.body.style.userSelect = '';
                        }
                    });

                    resizer.addEventListener('dblclick', () => {
                        sidebar.style.width = '';
                        sidebar.style.minWidth = '';
                        sidebar.style.maxWidth = '';
                        try {
                            localStorage.removeItem('trimodel_sidebar_w');
                        } catch(err) {}
                    });

                    sidebar.style.position = 'relative';
                    sidebar.appendChild(resizer);
                }

                // Khôi phục kích thước người dùng đã lưu
                try {
                    const savedW = localStorage.getItem('trimodel_sidebar_w');
                    if (savedW) {
                        const parsed = parseInt(savedW, 10);
                        if (parsed >= 220 && parsed <= 680) {
                            sidebar.style.width = parsed + 'px';
                            sidebar.style.minWidth = parsed + 'px';
                            sidebar.style.maxWidth = parsed + 'px';
                        }
                    }
                } catch(err) {}
            } catch(e) {}
        }

        checkAndApplyTheme();
        setInterval(checkAndApplyTheme, 500);
    })();
    </script>
    """, height=0, width=0)

