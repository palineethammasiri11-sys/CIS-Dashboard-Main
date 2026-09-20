"""
common.py
---------
โค้ดส่วนกลางที่ทุกหน้าของ CIS Dashboard ใช้ร่วมกัน

⚠️ กติกาสำคัญสำหรับทีม (9 คน):
- ไฟล์นี้เป็น "ของกลาง" ที่ทุกโมดูลอิงใช้ ถ้าจะแก้ (CSS, สี, ธีม, helper function, โครงสร้าง PageContext)
  ต้องแจ้ง/ขอความเห็นชอบจาก Layout Lead หรือ QA Lead ก่อนเสมอ ไม่งั้นจะกระทบทุกหน้าพร้อมกัน
- ห้าม copy โค้ดจากไฟล์นี้ไปแปะซ้ำในไฟล์หน้าโมดูลของตัวเอง — ให้ import มาใช้แทน
  (ถ้ามีจุดที่คิดว่าควรเพิ่ม helper ใหม่ที่ "ทุกหน้า" น่าจะได้ใช้ ให้เพิ่มที่นี่ที่เดียว)

โครงสร้างไฟล์:
1. ค่าคงที่ (TARGET_STOCKS, SECTOR_MAP, COMPANY_NAMES, PAGES)
2. CSS/ธีมของทั้งแอป
3. Helper functions ที่ใช้ข้ามหน้า (fmt_mb, safe, show_chart, render_nav_footer, create_gauge)
4. การเชื่อมต่อฐานข้อมูล + auto-healing (database_is_ready, build_database, load_all_data)
5. PageContext — โครงสร้างข้อมูลที่ส่งต่อให้ทุกหน้า
6. render_sidebar() / render_header_bar() — UI ส่วนที่ใช้ร่วมกันทุกหน้า
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
from dataclasses import dataclass


# ============================================================================
# 1. ค่าคงที่ที่ใช้ร่วมกันทั้งแอป
# ============================================================================
TARGET_STOCKS = ['ADVANC', 'CCET', 'DELTA', 'HANA', 'JMART', 'KCE', 'THCOM', 'TRUE']

SECTOR_MAP = {
    'ADVANC': 'Technology & Telecomm', 'TRUE': 'Technology & Telecomm', 'THCOM': 'Technology & Telecomm',
    'DELTA': 'Electronic Components', 'HANA': 'Electronic Components', 'KCE': 'Electronic Components',
    'CCET': 'Electronic Components', 'JMART': 'Commerce & Technology'
}

COMPANY_NAMES = {
    'ADVANC': 'Advanced Info Service PCL', 'CCET': 'Cal-Comp Electronics PCL', 'DELTA': 'Delta Electronics (Thailand) PCL',
    'HANA': 'Hana Microelectronics PCL', 'JMART': 'Jaymart Group Holdings PCL', 'KCE': 'KCE Electronics PCL',
    'THCOM': 'Thaicom PCL', 'TRUE': 'True Corporation PCL'
}

# ลำดับหน้า + emoji ประจำแต่ละโมดูล (ห้ามเปลี่ยน emoji ให้ซ้ำกันข้ามโมดูล — ดูตารางสี/emoji ในเอกสารแบ่งงาน)
PAGES = [
    " 🏠 Overview", " 💚 Company Health", " ⚖️ Fair Value",
    " ⏱️ Entry Timing", " 🔮 AI Prediction", " 🛡️ Risk Analysis", " 📊 Industry Benchmark"
]


# ============================================================================
# 2. CSS / ธีม Dark Navy ของทั้งแอป
# ============================================================================
def setup_page_and_css():
    """เรียกครั้งเดียวตอนเริ่ม app.py เท่านั้น ห้ามเรียกซ้ำในไฟล์หน้าโมดูล"""
    st.set_page_config(
        page_title="CIS - Comprehensive Investment System",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.markdown("""
    <style>
        html, body, [class*="css"] { font-size: 16px; }
        .stApp { background-color: #FFFFFF; }
        .metric-card { background-color: #FFFFFF; padding: 16px; border-radius: 12px; border: 1px solid #E2E8F0; text-align: center; height: 100%; }
        .hero-card { background-color: #FFFFFF; padding: 20px; border-radius: 16px; border: 1px solid #E2E8F0; }
        .dim-card { background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px; text-align: center; }

        /* ปุ่มทั้งหมดในแอป (Previous/Home/Next) ให้เข้ากับธีมมืด อ่านง่าย กดง่าย */
        .stButton > button {
            background-color: #151E2F !important;
            border: 1px solid #2A3A55 !important;
            color: #F1F5F9 !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            font-size: 14.5px !important;
            padding: 10px 18px !important;
            transition: all 0.2s ease-in-out !important;
        }
        .stButton > button:hover {
            border-color: #10B981 !important;
            color: #10B981 !important;
            background-color: rgba(16,185,129,0.10) !important;
        }
        .stButton > button p { font-size: 14.5px !important; font-weight: 600 !important; }

        /* --- Sidebar: พื้นหลังเข้ม ตัวหนังสือต้องสว่างพอให้อ่านออก --- */
        [data-testid="stSidebar"] { background-color: #0F172A; }
        [data-testid="stSidebar"] * { font-size: 15px; }
        [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label > div:first-child,
        [data-testid="stSidebar"] [data-testid="stRadio"] input[type="radio"],
        [data-testid="stSidebar"] [data-testid="stRadio"] svg { display: none !important; width: 0 !important; height: 0 !important; margin: 0 !important; }
        [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] { gap: 7px !important; }
        [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label {
            background-color: #151E2F !important; border: 1px solid #1E293B !important; border-radius: 8px !important;
            padding: 11px 14px !important; margin: 0 !important; cursor: pointer !important; width: 100% !important;
            display: flex !important; align-items: center !important; transition: all 0.2s ease-in-out !important;
        }
        [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label:hover {
            background-color: rgba(45, 212, 191, 0.10) !important; border-color: rgba(45, 212, 191, 0.35) !important;
        }
        [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) {
            background: rgba(16, 185, 129, 0.22) !important; border: 1.5px solid #10B981 !important; box-shadow: 0 0 10px rgba(16, 185, 129, 0.18) !important;
        }
        [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label p {
            font-size: 15px !important; color: #E2E8F0 !important; font-weight: 600 !important; margin: 0 !important; line-height: 1.4 !important;
        }
        [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) p {
            color: #10B981 !important; font-weight: 800 !important;
        }
        [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
            color: #CBD5E1 !important;
        }
        [data-testid="stSidebar"] [data-testid="stSelectbox"] label p { color: #CBD5E1 !important; font-size: 14px !important; font-weight: 600 !important; }
    </style>
    """, unsafe_allow_html=True)


# ============================================================================
# 3. Helper functions ที่ใช้ข้ามหน้า
# ============================================================================
def fmt_mb(x, unit="MB"):
    """แปลงตัวเลขบาทดิบ ให้เป็นหน่วยล้านบาท พร้อม comma"""
    try:
        return f"{float(x)/1e6:,.1f} {unit}"
    except Exception:
        return "-"


def fmt_ratio(v, suffix="x", decimals=2):
    """แสดงอัตราส่วน (P/E, P/B ฯลฯ) อย่างปลอดภัย — คืน '-' ถ้าเป็น None/NaN
    (เช่น หุ้นที่ EPS ติดลบจะไม่มีค่า P/E ที่มีความหมาย — ป้องกันไม่ให้จอโชว์ 'nanx')"""
    try:
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return "-"
        return f"{float(v):.{decimals}f}{suffix}"
    except Exception:
        return "-"


def safe(v, default=0.0):
    """แปลงค่าเป็น float อย่างปลอดภัย กัน None/NaN/string แปลกๆ ทำแอปพัง"""
    try:
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return default
        return float(v)
    except Exception:
        return default


def create_gauge(score, title, color_hex):
    """เผื่อบางโมดูลอยากใช้ gauge แบบ Plotly Indicator (ปัจจุบันทุกหน้าใช้ SVG/HTML gauge เอง แต่มีฟังก์ชันนี้ไว้เผื่อ)"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score,
        number={'font': {'size': 38, 'color': 'white'}},
        title={'text': f"<br><span style='font-size:15px;color:#94A3B8'>{title}</span>", 'font': {'size': 14}},
        gauge={'axis': {'range': [None, 100], 'visible': False}, 'bar': {'color': color_hex, 'thickness': 0.85},
               'bgcolor': "rgba(255,255,255,0.05)", 'borderwidth': 0}
    ))
    fig.update_layout(height=170, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)")
    return fig


@st.dialog("ขยายกราฟ", width="large")
def _open_chart_dialog(fig, expand_height):
    big_fig = go.Figure(fig)
    big_fig.update_layout(height=expand_height)
    try:
        big_fig.update_xaxes(tickfont=dict(size=13))
        big_fig.update_yaxes(tickfont=dict(size=13))
    except Exception:
        pass
    st.plotly_chart(big_fig, use_container_width=True, config={'displayModeBar': True}, key=f"dlg_{id(fig)}")


def show_chart(fig, key, expand_height=680):
    """แสดงกราฟ Plotly พร้อมปุ่ม '🔍 ขยายกราฟ' ที่เปิดกราฟเวอร์ชันใหญ่ในหน้าต่างลอย (dialog)
    ใช้แทน st.plotly_chart ตรงๆ ทุกจุดที่เป็นกราฟหลักของหน้า"""
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key=f"{key}_small")
    if st.button("🔍 ขยายกราฟ", key=f"{key}_expand_btn", use_container_width=True):
        _open_chart_dialog(fig, expand_height)


def render_nav_footer(key_prefix, prev_page=None, next_page=None):
    """แถบปุ่มนำทาง (หน้าก่อนหน้า / หน้าหลัก / หน้าถัดไป) แสดงท้ายทุกหน้าโมดูล (ยกเว้น Overview)
    key_prefix ต้องไม่ซ้ำกันข้ามหน้า (แนะนำ: m1=Health, m2=FairValue, m3=Timing, m4=AI, m5=Risk, m6=Industry)"""
    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
    st.markdown("""<div style="border-top:1px solid #1E293B; padding-top:16px; margin-bottom:6px;"></div>""", unsafe_allow_html=True)
    col_prev, col_home, col_next, col_disc = st.columns([1.3, 1.3, 1.3, 3.3])
    with col_prev:
        if prev_page:
            if st.button("⬅ หน้าก่อนหน้า", key=f"btn_prev_{key_prefix}", use_container_width=True):
                st.session_state["pending_nav"] = prev_page
                st.rerun()
    with col_home:
        if st.button("🏠 หน้าหลัก", key=f"btn_home_{key_prefix}", use_container_width=True):
            st.session_state["pending_nav"] = " 🏠 Overview"
            st.rerun()
    with col_next:
        if next_page:
            if st.button("หน้าถัดไป ➡", key=f"btn_next_{key_prefix}", use_container_width=True):
                st.session_state["pending_nav"] = next_page
                st.rerun()
    with col_disc:
        st.markdown(
            '<div style="font-size:15.5px; color:#94A3B8; text-align:right; padding-top:11px; line-height:1.5;">'
            'หมายเหตุ: การประเมินนี้ไม่ใช่คำแนะนำในการลงทุน ผู้ลงทุนควรศึกษาข้อมูลเพิ่มเติม</div>',
            unsafe_allow_html=True
        )


# ============================================================================
# 4. เชื่อมต่อฐานข้อมูล SQLite + ระบบซ่อมตัวเอง (auto-healing)
# ============================================================================
@st.cache_resource
def get_connection():
    return create_engine("sqlite:///cis_database.db")


def database_is_ready():
    """เช็คว่าฐานข้อมูลมีตารางผลลัพธ์พร้อมใช้งานหรือไม่"""
    try:
        engine = get_connection()
        with engine.connect() as conn:
            conn.execute(text("SELECT ticker FROM cis_summary_scores LIMIT 1"))
        return True
    except Exception:
        return False


def build_database():
    """รัน import_data.py + calculate_scores.py อัตโนมัติ กรณีฐานข้อมูลหาย/ว่างเปล่า
    (เช่น ตอน deploy บน Streamlit Cloud แล้ว .db ไม่ได้ถูกอัปโหลดไปด้วย หรือ container ถูกสร้างใหม่)"""
    import os
    import import_data
    import calculate_scores

    missing = []
    if not import_data.find_file("*master_all_8_stocks_financials*.csv") and not import_data.find_all_files("*financials_train*.csv"):
        missing.append("งบการเงิน (master_all_8_stocks_financials*.csv หรือ financials_train/test*.csv)")
    if not import_data.find_file("*stock_cleaned*.csv"):
        missing.append("ราคาหุ้นรายวัน (stock_cleaned_data*.csv)")
    if not import_data.find_file("*stock_risk_metrics*.csv"):
        missing.append("ความเสี่ยง (stock_risk_metrics*.csv)")

    if missing:
        cwd_listing = "\n".join(f"  - {f}" for f in sorted(os.listdir("."))) if os.path.isdir(".") else "(อ่านโฟลเดอร์ปัจจุบันไม่ได้)"
        ds_listing = "\n".join(f"  - {f}" for f in sorted(os.listdir("Dataset"))) if os.path.isdir("Dataset") else "  (ไม่พบโฟลเดอร์ Dataset/ เลย)"
        raise FileNotFoundError(
            "ไม่พบไฟล์ข้อมูลต่อไปนี้ใน repo: " + "; ".join(missing) +
            f"\n\nไฟล์/โฟลเดอร์ใน working directory ปัจจุบัน:\n{cwd_listing}" +
            f"\n\nไฟล์ใน Dataset/ ที่เจอ:\n{ds_listing}" +
            "\n\n➡️ กรุณาตรวจสอบว่าโฟลเดอร์ Dataset/ (พร้อมไฟล์ CSV ทั้ง 5 ไฟล์) ถูก push ขึ้น GitHub จริง "
            "(เช็คได้จากหน้า repo บน GitHub ว่าเห็นโฟลเดอร์ Dataset/ และไฟล์ .csv ข้างในหรือไม่ "
            "และเช็ค .gitignore ว่าไม่ได้ ignore *.csv หรือทั้งโฟลเดอร์ Dataset/ อยู่)"
        )

    engine = get_connection()
    import_data.import_financial_data(engine)
    import_data.import_price_data(engine)
    import_data.import_risk_metrics(engine)
    calculate_scores.run_full_pipeline()


@st.cache_data(ttl=600)
def load_all_data():
    """โหลดทุกตารางจากฐานข้อมูลครั้งเดียว (cache ไว้ 10 นาที) แชร์ให้ทุกหน้าใช้ร่วมกัน"""
    engine = get_connection()
    scores_df = pd.read_sql("SELECT * FROM cis_summary_scores ORDER BY ticker", engine)
    daily_df = pd.read_sql("SELECT * FROM stock_daily_prices ORDER BY ticker, date", engine)
    daily_df['date'] = pd.to_datetime(daily_df['date'])
    fin_df = pd.read_sql("SELECT * FROM stock_financials ORDER BY ticker, year", engine)
    feat_imp_df = pd.read_sql("SELECT * FROM ai_feature_importance", engine)
    try:
        backtest_df = pd.read_sql("SELECT * FROM ai_backtest_history", engine)
        backtest_df['date'] = pd.to_datetime(backtest_df['date'])
    except Exception:
        backtest_df = pd.DataFrame()
    try:
        risk_hist_df = pd.read_sql("SELECT * FROM risk_rolling_history", engine)
        risk_hist_df['date'] = pd.to_datetime(risk_hist_df['date'])
    except Exception:
        risk_hist_df = pd.DataFrame()
    try:
        health_yearly_df = pd.read_sql("SELECT * FROM health_score_yearly", engine)
    except Exception:
        health_yearly_df = pd.DataFrame()
    try:
        fair_value_yearly_df = pd.read_sql("SELECT * FROM fair_value_yearly", engine)
    except Exception:
        fair_value_yearly_df = pd.DataFrame()
    try:
        risk_static_df = pd.read_sql("SELECT * FROM stock_risk_static", engine)
    except Exception:
        risk_static_df = pd.DataFrame()
    return scores_df, daily_df, fin_df, feat_imp_df, backtest_df, risk_hist_df, health_yearly_df, fair_value_yearly_df, risk_static_df


def ensure_database_ready():
    """เรียกจาก app.py ครั้งเดียวตอนเริ่มแอป — ถ้าฐานข้อมูลไม่พร้อมจะพยายามสร้างให้อัตโนมัติ
    return True ถ้าพร้อมใช้งาน, False ถ้าล้มเหลว (จะ st.stop() ให้เองถ้าล้มเหลว)"""
    if not database_is_ready():
        with st.spinner("⏳ กำลังประมวลผลข้อมูลครั้งแรก (import + calculate scores)... อาจใช้เวลาสักครู่"):
            try:
                build_database()
                st.cache_data.clear()
            except Exception as build_err:
                st.error(f"⚠️ สร้างฐานข้อมูลอัตโนมัติไม่สำเร็จ: {build_err}\n\n"
                         f"กรุณาตรวจสอบว่าโฟลเดอร์ `Dataset/` ถูกอัปโหลดขึ้น GitHub ครบถ้วน "
                         f"หรือรัน `python import_data.py` แล้วตามด้วย `python calculate_scores.py` เองก่อนเปิด Dashboard")
                st.stop()
    return True


# ============================================================================
# 5. PageContext — โครงสร้างข้อมูลที่ส่งให้ทุกหน้าโมดูล
# ============================================================================
@dataclass
class PageContext:
    """ข้อมูลทั้งหมดที่หน้าโมดูลแต่ละหน้าอาจต้องใช้ ถูกสร้างครั้งเดียวใน app.py ต่อ 1 รอบการรัน
    แล้วส่งต่อ (ctx) ให้ฟังก์ชัน render(ctx) ของแต่ละหน้าเรียกใช้

    ⚠️ ถ้าโมดูลของคุณต้องใช้ข้อมูลเพิ่มเติมที่ยังไม่มีใน ctx (เช่น ตารางใหม่ที่คุณเพิ่มใน calculate_scores.py)
    ให้เพิ่ม field ใหม่ตรงนี้ + เพิ่มการโหลดข้อมูลใน load_all_data() ด้านบน แล้วแจ้งทีมว่าเพิ่ม field อะไร
    """
    selected_ticker: str
    stock_info: dict
    stock_daily: pd.DataFrame
    fin_stock: pd.DataFrame
    sector_peers: pd.DataFrame
    scores_df: pd.DataFrame
    fin_df: pd.DataFrame
    feat_imp_df: pd.DataFrame
    backtest_df: pd.DataFrame
    risk_hist_df: pd.DataFrame
    health_yearly_df: pd.DataFrame
    fair_value_yearly_df: pd.DataFrame
    current_price: float
    change_pct: float
    change_val: float
    change_color: str
    change_sign: str
    arrow_sign: str


def build_context(selected_ticker, scores_df, daily_df, fin_df, feat_imp_df,
                   backtest_df, risk_hist_df, health_yearly_df, fair_value_yearly_df):
    """ประกอบ PageContext จากข้อมูลดิบที่โหลดมาจาก load_all_data() + ticker ที่เลือกใน sidebar"""
    stock_info = scores_df[scores_df['ticker'] == selected_ticker].iloc[0].to_dict()
    stock_daily = daily_df[daily_df['ticker'] == selected_ticker].sort_values('date').reset_index(drop=True)
    fin_stock = fin_df[fin_df['ticker'] == selected_ticker].sort_values('year').reset_index(drop=True)
    sector_peers = scores_df[scores_df['sector'] == stock_info['sector']]

    current_price = safe(stock_info.get('current_price'))
    change_pct = safe(stock_info.get('change_pct'))
    change_val = safe(stock_info.get('change_val'))
    change_color = "#10B981" if change_pct >= 0 else "#EF4444"
    change_sign = "+" if change_pct >= 0 else ""
    arrow_sign = "▲" if change_pct >= 0 else "▼"

    return PageContext(
        selected_ticker=selected_ticker,
        stock_info=stock_info,
        stock_daily=stock_daily,
        fin_stock=fin_stock,
        sector_peers=sector_peers,
        scores_df=scores_df,
        fin_df=fin_df,
        feat_imp_df=feat_imp_df,
        backtest_df=backtest_df,
        risk_hist_df=risk_hist_df,
        health_yearly_df=health_yearly_df,
        fair_value_yearly_df=fair_value_yearly_df,
        current_price=current_price,
        change_pct=change_pct,
        change_val=change_val,
        change_color=change_color,
        change_sign=change_sign,
        arrow_sign=arrow_sign,
    )


# ============================================================================
# 6. UI ส่วนกลาง: Sidebar + Header Bar (ใช้เหมือนกันทุกหน้า)
# ============================================================================
def render_sidebar(scores_df):
    """วาด sidebar (โลโก้, เมนู navigation, dropdown เลือกหุ้น) แล้ว return (nav_page, selected_ticker)"""
    st.sidebar.markdown("""
    <div style="padding: 8px 0 14px 0;">
        <div style="display: flex; align-items: flex-start; gap: 10px; min-width: 0;">
            <span style="font-size: 26px; flex-shrink: 0; line-height:1.3;">🧠</span>
            <span style="font-size: 15px; font-weight: 800; color: #0F172A; letter-spacing: -0.1px; line-height: 1.3; min-width: 0; word-break: break-word; overflow-wrap: break-word;">
                Comprehensive Investment System
            </span>
        </div>
        <div style="font-size: 12px; color: #94A3B8; margin-top: 4px; padding-left: 36px; letter-spacing: 0.3px; font-weight: 600;">
            Investment Decision Support
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.sidebar.markdown("---")

    if "nav_page" not in st.session_state:
        st.session_state["nav_page"] = PAGES[0]

    # ปุ่ม "หน้าก่อนหน้า/หน้าหลัก/หน้าถัดไป" (render_nav_footer) จะฝากคำขอเปลี่ยนหน้าไว้ใน pending_nav แล้ว rerun
    # ต้องอัปเดตค่าให้ widget ตรงนี้ (ก่อน radio ถูกสร้าง) เพราะ Streamlit ไม่อนุญาตให้แก้ session_state
    # ของ key ที่ widget ใช้อยู่ หลังจาก widget ถูกสร้างไปแล้วในรอบเดียวกัน
    # *** ห้ามลบ/ย้ายกลไกนี้โดยไม่ปรึกษาทีมก่อน — เคยเป็นบั๊กที่ sidebar ไม่ sync กับปุ่มนำทางมาแล้ว ***
    if "pending_nav" in st.session_state:
    st.session_state["nav_page"] = st.session_state.pop("pending_nav")

st.sidebar.radio("Navigation", PAGES, key="nav_page")
nav_page = st.session_state["nav_page"]

st.sidebar.markdown("---")
selected_ticker = st.sidebar.selectbox("Search Company...", scores_df['ticker'].unique())
st.sidebar.caption(
    f"📅 ข้อมูล ณ วันที่ล่าสุดในชุดข้อมูล: **{scores_df['latest_date'].max()}**\n\n"
    f"(ราคาทั้งหมดอ้างอิงจากไฟล์ Dataset ไม่ใช่ราคาตลาดสด)"
)
return nav_page, selected_ticker
2. ให้แทนที่โค้ดเดิมทั้งหมดด้วยโค้ดนี้
if "pending_nav" in st.session_state:
    st.session_state["nav_page"] = st.session_state.pop("pending_nav")


# =========================
# COMPANY SELECTOR
# =========================

st.sidebar.markdown(
    "<div style='font-size:13px; font-weight:700; color:#64748B; "
    "margin-bottom:6px;'>SELECT COMPANY</div>",
    unsafe_allow_html=True
)

selected_ticker = st.sidebar.selectbox(
    "Choose a company",
    scores_df['ticker'].unique(),
    label_visibility="collapsed"
)

st.sidebar.markdown("---")


# =========================
# NAVIGATION
# =========================

st.sidebar.radio("Navigation", PAGES, key="nav_page")
nav_page = st.session_state["nav_page"]


# =========================
# DATA INFORMATION
# =========================

st.sidebar.caption(
    f"📅 ข้อมูล ณ วันที่ล่าสุดในชุดข้อมูล: **{scores_df['latest_date'].max()}**\n\n"
    f"(ราคาทั้งหมดอ้างอิงจากไฟล์ Dataset ไม่ใช่ราคาตลาดสด)"
)

return nav_page, selected_ticker


def render_header_bar(ctx):
    """แถบหัวข้อบนสุดของทุกหน้า (ticker, ราคา, P/E, ROE, วันที่ข้อมูล) — เหมือนกันทุกหน้า ไม่ต้องเขียนซ้ำ"""
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; background-color:#0F172A; padding:14px 24px; border-radius:12px; border:1px solid #1E293B; margin-bottom:20px;">
        <div>
            <span style="font-size:24px; font-weight:bold; color:white;">{ctx.selected_ticker}</span>
            <span style="color:#64748B; font-size:16px; margin-left:8px;">{ctx.stock_info.get('sector','-')} (SET) ☆</span>
        </div>
        <div style="font-size:16.5px; color:#64748B;">
            Price: <b style="color:white; font-size:19px;">{ctx.current_price:.2f}</b> THB
            <span style="color:{ctx.change_color}; font-weight:bold; margin-left:6px;">({ctx.change_sign}{ctx.change_pct:.2f}%) {ctx.arrow_sign}</span>
            <span style="margin: 0 12px; color:#334155;">|</span>
            P/E: <b style="color:white;">{fmt_ratio(ctx.stock_info.get('pe_ratio'))}</b>
            <span style="margin: 0 12px; color:#334155;">|</span>
            ROE: <b style="color:white;">{ctx.stock_info.get('roe','-')}%</b>
            <span style="margin: 0 12px; color:#334155;">|</span>
            Data as of: <b style="color:#F59E0B;">{ctx.stock_info.get('latest_date','-')}</b>
        </div>
    </div>
    """, unsafe_allow_html=True)
