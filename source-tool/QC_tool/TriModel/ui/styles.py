from __future__ import annotations
import streamlit as st
import streamlit.components.v1 as components


def apply_custom_css(is_dark: bool = True):
    """
    Áp dụng hệ thống Design System chuẩn Scale Nucleus Pro với khả năng
    tự động thích ứng 100% giữa Sáng (Light) và Tối (Dark) theo cài đặt của Streamlit.
    """
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    /* =========================================================================
       CSS VARIABLES: DARK THEME (DEFAULT)
       ========================================================================= */
    :root, body, .stApp {
        --bg-main: #080c14;
        --bg-sidebar: #0b101b;
        --bg-header: #0f1626;
        --bg-card: #111827;
        --bg-card-sub: #141d30;
        --border-c: #1e293b;
        --border-header: #00e5ff;
        --text-main: #f8fafc;
        --text-sub: #94a3b8;
        --text-muted: #cbd5e1;
        --val-cyan: #00e5ff;
        --val-indigo: #818cf8;
        --val-rose: #f43f5e;
        --val-amber: #fbbf24;
        --val-emerald: #10b981;
        --box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5);
        --badge-err-bg: rgba(244, 63, 94, 0.15);
        --badge-err-txt: #fca5a5;
        --badge-warn-bg: rgba(245, 158, 11, 0.15);
        --badge-warn-txt: #fde68a;
        --badge-ok-bg: rgba(16, 185, 129, 0.15);
        --badge-ok-txt: #a7f3d0;
        --tab-active-bg: rgba(0, 229, 255, 0.08);
        --glow-cyan: 0 0 20px rgba(0, 229, 255, 0.25);
    }

    html.theme-dark,
    body.theme-dark,
    .theme-dark .stApp,
    [data-theme="dark"],
    .stApp[data-theme="dark"],
    .theme-dark {
        --bg-main: #080c14 !important;
        --bg-sidebar: #0b101b !important;
        --bg-header: #0f1626 !important;
        --bg-card: #111827 !important;
        --bg-card-sub: #141d30 !important;
        --border-c: #1e293b !important;
        --border-header: #00e5ff !important;
        --text-main: #f8fafc !important;
        --text-sub: #94a3b8 !important;
        --text-muted: #cbd5e1 !important;
        --val-cyan: #00e5ff !important;
        --val-indigo: #818cf8 !important;
        --val-rose: #f43f5e !important;
        --val-amber: #fbbf24 !important;
        --val-emerald: #10b981 !important;
        --box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5) !important;
        --badge-err-bg: rgba(244, 63, 94, 0.15) !important;
        --badge-err-txt: #fca5a5 !important;
        --badge-warn-bg: rgba(245, 158, 11, 0.15) !important;
        --badge-warn-txt: #fde68a !important;
        --badge-ok-bg: rgba(16, 185, 129, 0.15) !important;
        --badge-ok-txt: #a7f3d0 !important;
        --tab-active-bg: rgba(0, 229, 255, 0.08) !important;
        --glow-cyan: 0 0 20px rgba(0, 229, 255, 0.25) !important;
    }

    /* =========================================================================
       CSS VARIABLES: LIGHT THEME (STUDIO LIGHT)
       ========================================================================= */
    @media (prefers-color-scheme: light) {
        :root, body, .stApp {
            --bg-main: #f8fafc;
            --bg-sidebar: #ffffff;
            --bg-header: #ffffff;
            --bg-card: #ffffff;
            --bg-card-sub: #f1f5f9;
            --border-c: #e2e8f0;
            --border-header: #0284c7;
            --text-main: #0f172a;
            --text-sub: #475569;
            --text-muted: #334155;
            --val-cyan: #0284c7;
            --val-indigo: #4f46e5;
            --val-rose: #e11d48;
            --val-amber: #d97706;
            --val-emerald: #059669;
            --box-shadow: 0 6px 20px rgba(0, 0, 0, 0.06);
            --badge-err-bg: #fee2e2;
            --badge-err-txt: #b91c1c;
            --badge-warn-bg: #fef3c7;
            --badge-warn-txt: #b45309;
            --badge-ok-bg: #d1fae5;
            --badge-ok-txt: #047857;
            --tab-active-bg: rgba(2, 132, 199, 0.08);
            --glow-cyan: 0 0 15px rgba(2, 132, 199, 0.18);
        }
    }

    html.theme-light,
    body.theme-light,
    .theme-light .stApp,
    [data-theme="light"],
    .stApp[data-theme="light"],
    .theme-light {
        --bg-main: #f8fafc !important;
        --bg-sidebar: #ffffff !important;
        --bg-header: #ffffff !important;
        --bg-card: #ffffff !important;
        --bg-card-sub: #f1f5f9 !important;
        --border-c: #e2e8f0 !important;
        --border-header: #0284c7 !important;
        --text-main: #0f172a !important;
        --text-sub: #475569 !important;
        --text-muted: #334155 !important;
        --val-cyan: #0284c7 !important;
        --val-indigo: #4f46e5 !important;
        --val-rose: #e11d48 !important;
        --val-amber: #d97706 !important;
        --val-emerald: #059669 !important;
        --box-shadow: 0 6px 20px rgba(0, 0, 0, 0.06) !important;
        --badge-err-bg: #fee2e2 !important;
        --badge-err-txt: #b91c1c !important;
        --badge-warn-bg: #fef3c7 !important;
        --badge-warn-txt: #b45309 !important;
        --badge-ok-bg: #d1fae5 !important;
        --badge-ok-txt: #047857 !important;
        --tab-active-bg: rgba(2, 132, 199, 0.08) !important;
        --glow-cyan: 0 0 15px rgba(2, 132, 199, 0.18) !important;
    }

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

    /* Đưa iframe ẩn hoàn toàn không chắn sự kiện cuộn chuột */
    iframe[data-testid="stCustomComponentV1"],
    div[data-testid="stCustomComponentV1"],
    div.element-container:has(iframe) {
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

    /* Input & Select Customization */
    div[data-baseweb="select"] > div {
        background-color: var(--bg-card) !important;
        border-color: var(--border-c) !important;
        border-radius: 8px !important;
        color: var(--text-main) !important;
    }
    div[data-baseweb="select"] * {
        color: var(--text-main) !important;
    }
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        background-color: var(--bg-card) !important;
        border-color: var(--border-c) !important;
        color: var(--text-main) !important;
        border-radius: 8px !important;
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

                const isLight = (detected === 'light');

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
            } catch(e) {}
        }

        checkAndApplyTheme();
        setInterval(checkAndApplyTheme, 250);
    })();
    </script>
    """, height=0, width=0)

