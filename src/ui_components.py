from io import BytesIO

import plotly.express as px
import streamlit as st


PLOTLY_TEMPLATE = "plotly_white"


def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    :html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: #F5F7FA; }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] { background: #101828; border-right: 1px solid #1D2939; }
    [data-testid="stSidebar"] * { color: #D0D5DD; }
    [data-testid="stSidebar"] .stRadio > label { display: none; }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
        border-radius: 8px; padding: 7px 10px; margin: 2px 0; gap: 8px;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover { background: #1D2939; }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:has(input:checked) {
        background: #244A68; color: #FFFFFF;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { margin-bottom: 0; }
    .block-container { max-width: 1450px; padding: 1.2rem 2rem 3rem 2rem; }
    h1, h2, h3 { color: #101828 !important; letter-spacing: -0.02em; }
    .topbar {
        display:flex; align-items:center; justify-content:space-between;
        background:#FFFFFF; border:1px solid #EAECF0; border-radius:12px;
        padding:12px 16px; margin:-8px 0 18px 0; box-shadow:0 1px 2px rgba(16,24,40,.04);
    }
    .breadcrumb { color:#667085; font-size:12px; }
    .page-title { color:#101828; font-size:20px; font-weight:700; }
    .brand {
        display:flex; align-items:center; gap:10px; padding:14px 8px 18px 8px;
        border-bottom:1px solid #1D2939; margin-bottom:12px;
    }
    .brand-mark {
        width:34px; height:34px; border-radius:9px; background:#4F8FBA;
        display:grid; place-items:center; color:white; font-weight:700;
    }
    .brand-name { color:white; font-size:17px; font-weight:700; }
    .brand-sub { color:#98A2B3; font-size:10px; text-transform:uppercase; letter-spacing:.08em; }
    .kpi-grid { display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:12px; margin-bottom:12px; }
    .kpi-card {
        background:#FFFFFF; border:1px solid #EAECF0; border-radius:12px;
        padding:16px 18px; min-height:118px; box-shadow:0 1px 3px rgba(16,24,40,.04);
    }
    .kpi-label { color:#667085; font-size:12px; font-weight:600; text-transform:uppercase; letter-spacing:.04em; }
    .kpi-value { color:#101828; font-size:27px; font-weight:700; margin:7px 0 3px 0; }
    .kpi-note { color:#98A2B3; font-size:11px; }
    .panel {
        background:#FFFFFF; border:1px solid #EAECF0; border-radius:12px;
        padding:16px; box-shadow:0 1px 3px rgba(16,24,40,.04);
    }
    .panel-title { color:#344054; font-size:14px; font-weight:700; margin-bottom:12px; }
    .metric-caption { color:#667085; font-size:12px; }
    [data-testid="stMetric"] {
        background:#FFFFFF; border:1px solid #EAECF0; border-radius:12px; padding:14px;
    }
    [data-testid="stDataFrame"] { border:1px solid #EAECF0; border-radius:10px; overflow:hidden; }
    .stButton > button, .stDownloadButton > button {
        border-radius:8px; border:1px solid #D0D5DD; color:#344054; font-weight:600;
    }
    .stButton > button[kind="primary"] { background:#244A68; color:white; border-color:#244A68; }
    .data-status { border-left:3px solid #2E90FA; background:#EFF8FF; padding:10px 12px; border-radius:6px; }
    @media (max-width: 900px) {
        .kpi-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }
        .block-container { padding:1rem; }
    }
    @media (max-width: 600px) {
        .kpi-grid { grid-template-columns:1fr; }
    }
    </style>
    """, unsafe_allow_html=True)


def chart_theme(fig, height=300):
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        height=height,
        margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=12, color="#667085"),
        colorway=["#2E90FA", "#2E7D6E", "#7A5AF8", "#F79009", "#667085"],
        hoverlabel=dict(bgcolor="#101828", font_color="#FFFFFF"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="#EAECF0", zeroline=False)
    return fig


def kpi_card(label, value, note=""):
    return (
        f'<div class="kpi-card"><div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div><div class="kpi-note">{note}</div></div>'
    )
