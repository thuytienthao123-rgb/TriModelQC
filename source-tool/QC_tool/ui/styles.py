from __future__ import annotations
import streamlit as st


def apply_custom_css(is_dark: bool):
    """Áp dụng hệ thống Design System nâng cấp chuẩn Scale Nucleus Pro (Dark Obsidian vs Studio Light)."""
    if is_dark:
        bg_main = "#080c14"
        bg_sidebar = "#0b101b"
        bg_header = "#0f1626"
        bg_card = "#111827"
        bg_card_sub = "#141d30"
        border_c = "#1e293b"
        border_header = "#00e5ff"
        text_main = "#f8fafc"
        text_sub = "#94a3b8"
        text_muted = "#cbd5e1"
        badge_bg = "#0f1624"
        val_cyan = "#00e5ff"
        val_indigo = "#818cf8"
        val_rose = "#f43f5e"
        val_amber = "#fbbf24"
        val_emerald = "#10b981"
        box_shadow = "0 8px 30px rgba(0, 0, 0, 0.5)"
        badge_err_bg = "rgba(244, 63, 94, 0.15)"
        badge_err_txt = "#fca5a5"
        badge_warn_bg = "rgba(245, 158, 11, 0.15)"
        badge_warn_txt = "#fde68a"
        badge_ok_bg = "rgba(16, 185, 129, 0.15)"
        badge_ok_txt = "#a7f3d0"
        tab_active_bg = "rgba(0, 229, 255, 0.08)"
        glow_cyan = "0 0 20px rgba(0, 229, 255, 0.25)"
    else:
        bg_main = "#f8fafc"
        bg_sidebar = "#ffffff"
        bg_header = "#ffffff"
        bg_card = "#ffffff"
        bg_card_sub = "#f1f5f9"
        border_c = "#e2e8f0"
        border_header = "#0284c7"
        text_main = "#0f172a"
        text_sub = "#475569"
        text_muted = "#334155"
        badge_bg = "#f1f5f9"
        val_cyan = "#0284c7"
        val_indigo = "#4f46e5"
        val_rose = "#e11d48"
        val_amber = "#d97706"
        val_emerald = "#059669"
        box_shadow = "0 6px 20px rgba(0, 0, 0, 0.06)"
        badge_err_bg = "#fee2e2"
        badge_err_txt = "#b91c1c"
        badge_warn_bg = "#fef3c7"
        badge_warn_txt = "#b45309"
        badge_ok_bg = "#d1fae5"
        badge_ok_txt = "#047857"
        tab_active_bg = "rgba(2, 132, 199, 0.08)"
        glow_cyan = "0 0 15px rgba(2, 132, 199, 0.18)"

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    .stApp {{
        background-color: {bg_main} !important;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        color: {text_main} !important;
    }}

    [data-testid="stSidebar"] {{
        background-color: {bg_sidebar} !important;
        border-right: 1px solid {border_c} !important;
    }}
    [data-testid="stSidebar"] * {{
        color: {text_main};
    }}
    [data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {{
        color: {text_sub};
    }}

    .stApp p, .stApp span, .stApp label, .stApp div {{
        color: {text_main};
    }}

    /* Streamlit Tab Bar Elevation */
    [data-baseweb="tab-list"] {{
        gap: 8px !important;
        border-bottom: 2px solid {border_c} !important;
        padding-bottom: 4px !important;
        background: transparent !important;
    }}
    [data-baseweb="tab"] {{
        border-radius: 8px 8px 0 0 !important;
        padding: 9px 20px !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        color: {text_sub} !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
        border: 1px solid transparent !important;
        background: transparent !important;
    }}
    [data-baseweb="tab"]:hover {{
        color: {val_cyan} !important;
        background: {tab_active_bg} !important;
        border-color: rgba(0, 229, 255, 0.2) !important;
    }}
    [data-baseweb="tab"][aria-selected="true"] {{
        background: {tab_active_bg} !important;
        border-bottom: 2px solid {val_cyan} !important;
        color: {val_cyan} !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 15px -3px rgba(0, 229, 255, 0.25) !important;
    }}

    /* Buttons Elevation */
    .stButton > button {{
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        padding: 7px 16px !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
        border: 1px solid {border_c} !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05) !important;
    }}
    .stButton > button:hover {{
        transform: translateY(-1.5px) !important;
        border-color: {val_cyan} !important;
        box-shadow: {box_shadow} !important;
    }}
    .stButton > button:active {{
        transform: translateY(0.5px) !important;
    }}

    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, {val_cyan} 0%, #0284c7 100%) !important;
        color: #080c14 !important;
        font-weight: 800 !important;
        border: none !important;
        box-shadow: {glow_cyan} !important;
    }}
    .stButton > button[kind="primary"]:hover {{
        box-shadow: 0 0 25px rgba(0, 229, 255, 0.55) !important;
        transform: translateY(-2px) !important;
    }}

    /* Input & Select Streamlit Customization */
    div[data-baseweb="select"] > div {{
        background-color: {bg_card} !important;
        border-color: {border_c} !important;
        border-radius: 8px !important;
        color: {text_main} !important;
    }}
    div[data-baseweb="select"] * {{
        color: {text_main} !important;
    }}
    .stTextInput > div > div > input {{
        background-color: {bg_card} !important;
        border-color: {border_c} !important;
        color: {text_main} !important;
        border-radius: 8px !important;
    }}
    .stNumberInput > div > div > input {{
        background-color: {bg_card} !important;
        border-color: {border_c} !important;
        color: {text_main} !important;
        border-radius: 8px !important;
    }}

    /* Custom Modern Scrollbars */
    ::-webkit-scrollbar {{
        width: 6px;
        height: 6px;
    }}
    ::-webkit-scrollbar-track {{
        background: transparent;
    }}
    ::-webkit-scrollbar-thumb {{
        background: rgba(148, 163, 184, 0.25);
        border-radius: 4px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: {val_cyan};
    }}

    /* Header Box */
    .qc-header-box {{
        background: {bg_header};
        border-bottom: 2px solid {border_header};
        padding: 20px 28px;
        margin: -1rem -1rem 1.6rem -1rem;
        box-shadow: {box_shadow};
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
    }}

    .qc-header-box::after {{
        content: "";
        position: absolute;
        top: 0;
        right: 0;
        width: 380px;
        height: 100%;
        background: radial-gradient(circle at 85% 20%, rgba(0, 229, 255, 0.12) 0%, transparent 70%);
        pointer-events: none;
    }}

    .qc-header-title {{
        font-size: 1.48rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        color: {text_main} !important;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }}

    .qc-header-sub {{
        font-size: 0.85rem;
        color: {text_sub} !important;
        margin: 4px 0 0 0;
        font-weight: 400;
    }}

    .qc-tag-row {{
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
    }}

    .qc-tag {{
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }}

    .qc-tag-cyan {{
        background: rgba(0, 229, 255, 0.12);
        color: {val_cyan} !important;
        border: 1px solid rgba(0, 229, 255, 0.35);
    }}

    .qc-tag-purple {{
        background: rgba(129, 140, 248, 0.12);
        color: {val_indigo} !important;
        border: 1px solid rgba(129, 140, 248, 0.35);
    }}

    .qc-tag-online {{
        background: rgba(16, 185, 129, 0.12);
        color: {val_emerald} !important;
        border: 1px solid rgba(16, 185, 129, 0.35);
    }}

    .pulse-dot {{
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: {val_emerald};
        box-shadow: 0 0 8px {val_emerald};
        animation: pulse 1.8s infinite;
    }}

    @keyframes pulse {{
        0%, 100% {{ opacity: 1; transform: scale(1); }}
        50% {{ opacity: 0.4; transform: scale(0.85); }}
    }}

    /* KPI Cards */
    .qc-kpi-card {{
        background: {bg_card};
        border: 1px solid {border_c};
        border-radius: 10px;
        padding: 15px 18px;
        transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1);
        position: relative;
        overflow: hidden;
        margin-bottom: 0.5rem;
    }}

    .qc-kpi-card:hover {{
        border-color: {val_cyan};
        transform: translateY(-2.5px);
        box-shadow: {box_shadow};
    }}

    .qc-kpi-cyan {{ border-left: 3.5px solid {val_cyan}; }}
    .qc-kpi-indigo {{ border-left: 3.5px solid {val_indigo}; }}
    .qc-kpi-rose {{ border-left: 3.5px solid {val_rose}; }}
    .qc-kpi-amber {{ border-left: 3.5px solid {val_amber}; }}
    .qc-kpi-emerald {{ border-left: 3.5px solid {val_emerald}; }}

    .qc-kpi-label {{
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: {text_sub} !important;
        margin-bottom: 4px;
        font-family: 'JetBrains Mono', monospace;
    }}

    .qc-kpi-val {{
        font-size: 1.88rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        line-height: 1.1;
        font-family: 'JetBrains Mono', monospace;
    }}

    .val-cyan {{ color: {val_cyan} !important; }}
    .val-indigo {{ color: {val_indigo} !important; }}
    .val-rose {{ color: {val_rose} !important; }}
    .val-amber {{ color: {val_amber} !important; }}
    .val-emerald {{ color: {val_emerald} !important; }}

    .qc-kpi-sub {{
        font-size: 0.74rem;
        color: {text_sub} !important;
        margin-top: 4px;
    }}

    /* Badges */
    .badge-err {{
        background: {badge_err_bg};
        color: {badge_err_txt} !important;
        border: 1px solid rgba(239, 68, 68, 0.4);
        padding: 3px 9px;
        border-radius: 6px;
        font-size: 0.74rem;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        display: inline-block;
    }}

    .badge-warn {{
        background: {badge_warn_bg};
        color: {badge_warn_txt} !important;
        border: 1px solid rgba(245, 158, 11, 0.4);
        padding: 3px 9px;
        border-radius: 6px;
        font-size: 0.74rem;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        display: inline-block;
    }}

    .badge-ok {{
        background: {badge_ok_bg};
        color: {badge_ok_txt} !important;
        border: 1px solid rgba(16, 185, 129, 0.4);
        padding: 3px 9px;
        border-radius: 6px;
        font-size: 0.74rem;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        display: inline-block;
    }}

    .sidebar-brand-card {{
        background: {bg_card_sub};
        border: 1px solid {border_c};
        border-radius: 10px;
        padding: 12px 14px;
        margin-bottom: 14px;
        display: flex;
        align-items: center;
        gap: 12px;
    }}

    .sidebar-brand-icon {{
        font-size: 1.6rem;
        background: {bg_card};
        padding: 6px 10px;
        border-radius: 8px;
        border: 1px solid {border_c};
    }}

    .sidebar-brand-title {{
        margin: 0;
        font-size: 1.05rem;
        font-weight: 800;
        letter-spacing: -0.01em;
        color: {text_main} !important;
    }}

    .sidebar-brand-sub {{
        margin: 0;
        font-size: 0.74rem;
        color: {text_sub} !important;
        font-family: 'JetBrains Mono', monospace;
    }}

    .team-card {{
        background: {bg_card_sub};
        border: 1px solid {border_c};
        border-radius: 8px;
        padding: 10px 12px;
        margin-top: 16px;
    }}

    .team-member-row {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.78rem;
        padding: 3px 0;
        border-bottom: 1px dashed {border_c};
    }}

    .team-member-row:last-child {{
        border-bottom: none;
    }}

    .team-member-name {{
        color: {text_main};
        font-weight: 500;
    }}

    .team-member-role {{
        color: {val_cyan};
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
    }}

    .feature-card {{
        background: {bg_card};
        border: 1px solid {border_c};
        border-radius: 10px;
        padding: 16px 18px;
        height: 100%;
        transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.2s ease;
    }}
    .feature-card:hover {{
        transform: translateY(-2.5px);
        border-color: {val_cyan};
        box-shadow: {box_shadow};
    }}
    .feature-title {{
        font-size: 0.94rem;
        font-weight: 700;
        color: {text_main};
        margin-bottom: 6px;
    }}
    .feature-desc {{
        font-size: 0.8rem;
        color: {text_sub};
        line-height: 1.55;
    }}

    .benchmark-card {{
        background: {bg_card};
        border: 1px solid {border_c};
        border-radius: 10px;
        padding: 18px 20px;
        margin-bottom: 14px;
    }}
    .benchmark-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 12px;
        margin-top: 12px;
    }}
    .benchmark-item {{
        background: {bg_card_sub};
        border: 1px solid {border_c};
        border-radius: 8px;
        padding: 12px 14px;
    }}
    .benchmark-label {{
        font-size: 0.74rem;
        color: {text_sub};
        font-weight: 600;
    }}
    .benchmark-val {{
        font-size: 1.25rem;
        font-weight: 800;
        font-family: 'JetBrains Mono', monospace;
        margin: 4px 0 2px 0;
    }}
    .metric-pill {{
        background: {bg_card_sub};
        border: 1px solid {border_c};
        padding: 3px 8px;
        border-radius: 5px;
        font-size: 0.75rem;
        color: {text_muted};
        font-family: 'JetBrains Mono', monospace;
    }}
    .metric-pill strong {{ color: {text_main}; }}

    /* Streamlit Expander Glow */
    .streamlit-expanderHeader {{
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
    }}

    /* Official Quality Verdict Stamp Watermark */
    .qc-verdict-stamp {{
        position: absolute;
        right: 28px;
        bottom: 12px;
        transform: rotate(-10deg);
        border: 3.5px dashed;
        border-radius: 12px;
        padding: 8px 18px;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 900;
        font-size: 1.15rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        opacity: 0.22;
        pointer-events: none;
        user-select: none;
    }}

    /* Mini Progress Bar in KPI */
    .qc-progress-track {{
        width: 100%;
        height: 5px;
        background: rgba(148, 163, 184, 0.15);
        border-radius: 999px;
        margin-top: 8px;
        overflow: hidden;
    }}
    .qc-progress-fill {{
        height: 100%;
        border-radius: 999px;
        transition: width 0.6s ease;
    }}
    </style>
    """, unsafe_allow_html=True)
