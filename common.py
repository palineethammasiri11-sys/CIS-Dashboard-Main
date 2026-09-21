"""
common.py
---------
โค้ดส่วนกลางที่ทุกหน้าของ CIS Dashboard ใช้ร่วมกัน

⚠️ กติกาสำคัญสำหรับทีม (9 คน):
- ไฟล์นี้เป็น "ของกลาง" ที่ทุกโมดูลอิงใช้ ถ้าจะแก้ (CSS, สี, ธีม, helper function,
  โครงสร้าง PageContext) ต้องแจ้ง/ขอความเห็นชอบจาก Layout Lead หรือ QA Lead ก่อนเสมอ
  ไม่งั้นจะกระทบทุกหน้าพร้อมกัน
- ห้าม copy โค้ดจากไฟล์นี้ไปแปะซ้ำในไฟล์หน้าโมดูลของตัวเอง — ให้ import มาใช้แทน
- ถ้ามีจุดที่คิดว่าควรเพิ่ม helper ใหม่ที่ "ทุกหน้า" น่าจะได้ใช้ ให้เพิ่มที่นี่ที่เดียว

โครงสร้างไฟล์:
1. ค่าคงที่
2. CSS/ธีมของทั้งแอป
3. Helper functions
4. การเชื่อมต่อฐานข้อมูล + auto-healing
5. PageContext
6. render_sidebar() / render_header_bar()
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

TARGET_STOCKS = [
    "ADVANC",
    "CCET",
    "DELTA",
    "HANA",
    "JMART",
    "KCE",
    "THCOM",
    "TRUE",
]


SECTOR_MAP = {
    "ADVANC": "Technology & Telecomm",
    "TRUE": "Technology & Telecomm",
    "THCOM": "Technology & Telecomm",
    "DELTA": "Electronic Components",
    "HANA": "Electronic Components",
    "KCE": "Electronic Components",
    "CCET": "Electronic Components",
    "JMART": "Commerce & Technology",
}


COMPANY_NAMES = {
    "ADVANC": "Advanced Info Service PCL",
    "CCET": "Cal-Comp Electronics PCL",
    "DELTA": "Delta Electronics (Thailand) PCL",
    "HANA": "Hana Microelectronics PCL",
    "JMART": "Jaymart Group Holdings PCL",
    "KCE": "KCE Electronics PCL",
    "THCOM": "Thaicom PCL",
    "TRUE": "True Corporation PCL",
}


# ลำดับหน้า + emoji ประจำแต่ละโมดูล
PAGES = [
    " Overview",
    " Company Health",
    " Fair Value",
    " Entry Timing",
    " AI Prediction",
    " Risk Analysis",
    " Industry Benchmark",
]


# ============================================================================
# 2. CSS / ธีม Light Clean ของทั้งแอป
# ============================================================================

def setup_page_and_css():
    """
    เรียกครั้งเดียวตอนเริ่ม app.py เท่านั้น
    ห้ามเรียกซ้ำในไฟล์หน้าโมดูล
    """

    st.set_page_config(
        page_title="CIS - Comprehensive Investment System",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown(
        """
        <style>

        /* =========================================================
           GLOBAL — Clean Financial Platform
           ========================================================= */

        html,
        body,
        [class*="css"] {
            font-size: 16px;
        }

        .stApp {
            background-color: #F8FAFC;
        }

        .main .block-container {
            max-width: 1400px;
            padding-top: 2rem;
            padding-bottom: 3rem;
            padding-left: 3rem;
            padding-right: 3rem;
        }


        /* =========================================================
           CARDS
           ========================================================= */

        .metric-card {
            background: #FFFFFF;
            padding: 20px;
            border-radius: 14px;
            border: 1px solid #E2E8F0;
            text-align: center;
            height: 100%;
            box-shadow: none;
        }

        .hero-card {
            background: #FFFFFF;
            padding: 24px;
            border-radius: 16px;
            border: 1px solid #E2E8F0;
            box-shadow: none;
        }

        .dim-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 16px;
            text-align: center;
            box-shadow: none;
        }


        /* =========================================================
           BUTTONS
           ========================================================= */

        .stButton > button {
            background-color: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            color: #334155 !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            font-size: 14px !important;
            padding: 9px 16px !important;
            transition: all 0.2s ease-in-out !important;
            box-shadow: none !important;
        }

        .stButton > button:hover {
            background-color: #F8FAFC !important;
            border-color: #CBD5E1 !important;
            color: #0F172A !important;
        }

        .stButton > button p {
            font-size: 14px !important;
            font-weight: 600 !important;
        }


        /* =========================================================
           SIDEBAR
           ========================================================= */

        [data-testid="stSidebar"] {
            background-color: #FFFFFF;
            border-right: 1px solid #E2E8F0;
        }

        [data-testid="stSidebar"] * {
            font-size: 15px;
        }


        /* Hide radio circles */

        [data-testid="stSidebar"]
        [data-testid="stRadio"]
        div[role="radiogroup"]
        label > div:first-child,

        [data-testid="stSidebar"]
        [data-testid="stRadio"]
        input[type="radio"],

        [data-testid="stSidebar"]
        [data-testid="stRadio"]
        svg {
            display: none !important;
            width: 0 !important;
            height: 0 !important;
            margin: 0 !important;
        }


        /* Navigation spacing */

        [data-testid="stSidebar"]
        [data-testid="stRadio"]
        div[role="radiogroup"] {
            gap: 4px !important;
        }


        /* Navigation item */

        [data-testid="stSidebar"]
        [data-testid="stRadio"]
        div[role="radiogroup"]
        label {
            background-color: transparent !important;
            border: 1px solid transparent !important;
            border-radius: 8px !important;
            padding: 10px 12px !important;
            margin: 0 !important;
            cursor: pointer !important;
            width: 100% !important;
            display: flex !important;
            align-items: center !important;
            transition: all 0.15s ease-in-out !important;
        }


        /* Hover */

        [data-testid="stSidebar"]
        [data-testid="stRadio"]
        div[role="radiogroup"]
        label:hover {
            background-color: #F8FAFC !important;
            border-color: #F1F5F9 !important;
        }


        /* Navigation text */

        [data-testid="stSidebar"]
        [data-testid="stRadio"]
        div[role="radiogroup"]
        label p {
            font-size: 14px !important;
            color: #475569 !important;
            font-weight: 500 !important;
            margin: 0 !important;
            line-height: 1.4 !important;
        }


        /* Sidebar labels */

        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stCaption,
        [data-testid="stSidebar"]
        [data-testid="stCaptionContainer"] {
            color: #64748B !important;
        }


        [data-testid="stSidebar"]
        [data-testid="stSelectbox"]
        label p {
            color: #64748B !important;
            font-size: 13px !important;
            font-weight: 600 !important;
        }


        /* Selectbox */

        [data-testid="stSidebar"]
        [data-testid="stSelectbox"] > div {
            background-color: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 8px !important;
            box-shadow: none !important;
        }

        [data-testid="stSidebar"]
        [data-testid="stSelectbox"]
        [data-baseweb="select"] > div {
            background-color: #FFFFFF !important;
            border-color: #E2E8F0 !important;
            border-radius: 8px !important;
            color: #0F172A !important;
        }

        [data-testid="stSidebar"]
        [data-testid="stSelectbox"]
        [data-baseweb="select"] span {
            color: #0F172A !important;
        }


        /* =========================================================
           SECTION HEADINGS
           ========================================================= */

        h1,
        h2,
        h3 {
            color: #0F172A !important;
        }

        p {
            color: #475569;
        }


        /* =========================================================
           HEADER
           ========================================================= */

        .cis-header {
            width: 100%;
            box-sizing: border-box;
        }


        /* =========================================================
           RESPONSIVE / MOBILE
           ========================================================= */

        @media (max-width: 768px) {

            .main .block-container {
                padding: 1rem 0.85rem 2rem 0.85rem !important;
                max-width: 100% !important;
            }

            [data-testid="stHorizontalBlock"] {
                flex-wrap: wrap !important;
                gap: 0.75rem !important;
            }

            [data-testid="column"] {
                width: 100% !important;
                flex: 1 1 100% !important;
                min-width: 100% !important;
            }

            .cis-header {
                flex-direction: column !important;
                align-items: flex-start !important;
                gap: 10px !important;
                padding: 14px 16px !important;
            }

            .cis-header-info {
                width: 100% !important;
                display: flex !important;
                flex-wrap: wrap !important;
                gap: 6px 10px !important;
                font-size: 13px !important;
                white-space: normal !important;
                text-align: left !important;
            }

            .cis-header-divider {
                display: none !important;
            }

            .module-title {
                font-size: 21px !important;
                line-height: 1.25 !important;
            }

            .module-subtitle {
                font-size: 14px !important;
                line-height: 1.5 !important;
            }

            [data-testid="stDataFrame"] {
                width: 100% !important;
                overflow-x: auto !important;
            }

            .js-plotly-plot,
            .plot-container {
                width: 100% !important;
                max-width: 100% !important;
            }

            .stButton > button {
                width: 100% !important;
            }
        }


        /* =========================================================
           VERY SMALL MOBILE
           ========================================================= */

        @media (max-width: 480px) {

            .main .block-container {
                padding: 0.75rem 0.65rem 1.5rem 0.65rem !important;
            }

            .module-title {
                font-size: 19px !important;
            }

            .module-subtitle {
                font-size: 13.5px !important;
            }

            [data-testid="stHorizontalBlock"] {
                gap: 0.6rem !important;
            }
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================================
# 3. Helper functions
# ============================================================================

def fmt_mb(x, unit="MB"):
    """
    แปลงตัวเลขบาทดิบให้เป็นหน่วยล้านบาท พร้อม comma
    """
    try:
        return f"{float(x) / 1e6:,.1f} {unit}"
    except Exception:
        return "-"


def fmt_ratio(v, suffix="x", decimals=2):
    """
    แสดงอัตราส่วน (P/E, P/B ฯลฯ) อย่างปลอดภัย

    คืน '-' ถ้าเป็น None/NaN
    """
    try:
        if v is None:
            return "-"

        if pd.isna(v):
            return "-"

        return f"{float(v):.{decimals}f}{suffix}"

    except Exception:
        return "-"


def safe(v, default=0.0):
    """
    แปลงค่าเป็น float อย่างปลอดภัย
    กัน None/NaN/string แปลก ๆ ทำแอปพัง
    """
    try:
        if v is None:
            return default

        if pd.isna(v):
            return default

        return float(v)

    except Exception:
        return default


def create_gauge(score, title, color_hex):
    """
    Plotly Gauge
    """

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,

            number={
                "font": {
                    "size": 38,
                    "color": "white",
                }
            },

            title={
                "text": (
                    f"<br>"
                    f"<span style='font-size:15px;color:#94A3B8'>"
                    f"{title}"
                    f"</span>"
                ),
                "font": {
                    "size": 14,
                },
            },

            gauge={
                "axis": {
                    "range": [None, 100],
                    "visible": False,
                },

                "bar": {
                    "color": color_hex,
                    "thickness": 0.85,
                },

                "bgcolor": "rgba(255,255,255,0.05)",
                "borderwidth": 0,
            },
        )
    )

    fig.update_layout(
        height=170,
        margin=dict(
            l=10,
            r=10,
            t=10,
            b=10,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
    )

    return fig


# ============================================================================
# Plotly expanded dialog
# ============================================================================

@st.dialog("ขยายกราฟ", width="large")
def _open_chart_dialog(fig, expand_height):

    big_fig = go.Figure(fig)

    big_fig.update_layout(
        height=expand_height
    )

    try:
        big_fig.update_xaxes(
            tickfont=dict(size=13)
        )

        big_fig.update_yaxes(
            tickfont=dict(size=13)
        )

    except Exception:
        pass

    st.plotly_chart(
        big_fig,
        use_container_width=True,
        config={
            "displayModeBar": True
        },
        key=f"dlg_{id(fig)}",
    )


def show_chart(fig, key, expand_height=680):
    """
    แสดงกราฟ Plotly พร้อมปุ่มขยายกราฟ
    """

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False
        },
        key=f"{key}_small",
    )

    if st.button(
        "🔍 ขยายกราฟ",
        key=f"{key}_expand_btn",
        use_container_width=True,
    ):
        _open_chart_dialog(
            fig,
            expand_height
        )


# ============================================================================
# Navigation footer
# ============================================================================

def render_nav_footer(
    key_prefix,
    prev_page=None,
    next_page=None,
):
    """
    แถบปุ่มนำทางท้ายทุกหน้าโมดูล
    """

    st.markdown(
        "<div style='margin-top:24px;'></div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div
            style="
                border-top:1px solid #E2E8F0;
                padding-top:16px;
                margin-bottom:6px;
            "
        ></div>
        """,
        unsafe_allow_html=True,
    )

    col_prev, col_home, col_next, col_disc = st.columns(
        [1.3, 1.3, 1.3, 3.3]
    )

    with col_prev:

        if prev_page:

            if st.button(
                "⬅ หน้าก่อนหน้า",
                key=f"btn_prev_{key_prefix}",
                use_container_width=True,
            ):

                st.session_state["pending_nav"] = prev_page
                st.rerun()

    with col_home:

        if st.button(
            "🏠 หน้าหลัก",
            key=f"btn_home_{key_prefix}",
            use_container_width=True,
        ):

            st.session_state["pending_nav"] = " Overview"
            st.rerun()

    with col_next:

        if next_page:

            if st.button(
                "หน้าถัดไป ➡",
                key=f"btn_next_{key_prefix}",
                use_container_width=True,
            ):

                st.session_state["pending_nav"] = next_page
                st.rerun()

    with col_disc:

        st.markdown(
            """
            <div
                style="
                    font-size:15.5px;
                    color:#64748B;
                    text-align:right;
                    padding-top:11px;
                    line-height:1.5;
                "
            >
                หมายเหตุ: การประเมินนี้ไม่ใช่คำแนะนำในการลงทุน
                ผู้ลงทุนควรศึกษาข้อมูลเพิ่มเติม
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================================
# 4. เชื่อมต่อฐานข้อมูล SQLite + ระบบซ่อมตัวเอง
# ============================================================================

@st.cache_resource
def get_connection():
    return create_engine(
        "sqlite:///cis_database.db"
    )


def database_is_ready():
    """
    เช็คว่าฐานข้อมูลมีตารางผลลัพธ์พร้อมใช้งานหรือไม่
    """

    try:

        engine = get_connection()

        with engine.connect() as conn:

            conn.execute(
                text(
                    "SELECT ticker "
                    "FROM cis_summary_scores "
                    "LIMIT 1"
                )
            )

        return True

    except Exception:

        return False


def build_database():
    """
    รัน import_data.py + calculate_scores.py อัตโนมัติ
    กรณีฐานข้อมูลหาย/ว่างเปล่า
    """

    import os
    import import_data
    import calculate_scores

    missing = []

    if (
        not import_data.find_file(
            "*master_all_8_stocks_financials*.csv"
        )
        and not import_data.find_all_files(
            "*financials_train*.csv"
        )
    ):
        missing.append(
            "งบการเงิน "
            "(master_all_8_stocks_financials*.csv "
            "หรือ financials_train/test*.csv)"
        )

    if not import_data.find_file(
        "*stock_cleaned*.csv"
    ):
        missing.append(
            "ราคาหุ้นรายวัน "
            "(stock_cleaned_data*.csv)"
        )

    if not import_data.find_file(
        "*stock_risk_metrics*.csv"
    ):
        missing.append(
            "ความเสี่ยง "
            "(stock_risk_metrics*.csv)"
        )

    if missing:

        cwd_listing = (
            "\n".join(
                f"  - {f}"
                for f in sorted(os.listdir("."))
            )
            if os.path.isdir(".")
            else "(อ่านโฟลเดอร์ปัจจุบันไม่ได้)"
        )

        ds_listing = (
            "\n".join(
                f"  - {f}"
                for f in sorted(os.listdir("Dataset"))
            )
            if os.path.isdir("Dataset")
            else "  (ไม่พบโฟลเดอร์ Dataset/ เลย)"
        )

        raise FileNotFoundError(
            "ไม่พบไฟล์ข้อมูลต่อไปนี้ใน repo: "
            + "; ".join(missing)

            + f"""

ไฟล์/โฟลเดอร์ใน working directory ปัจจุบัน:
{cwd_listing}

ไฟล์ใน Dataset/ ที่เจอ:
{ds_listing}

➡️ กรุณาตรวจสอบว่าโฟลเดอร์ Dataset/
พร้อมไฟล์ CSV ทั้ง 5 ไฟล์ถูก push ขึ้น GitHub จริง

เช็คได้จากหน้า repo บน GitHub ว่าเห็น
โฟลเดอร์ Dataset/ และไฟล์ .csv ข้างในหรือไม่

และเช็ค .gitignore ว่าไม่ได้ ignore
*.csv หรือทั้งโฟลเดอร์ Dataset/
"""
        )

    engine = get_connection()

    import_data.import_financial_data(
        engine
    )

    import_data.import_price_data(
        engine
    )

    import_data.import_risk_metrics(
        engine
    )

    calculate_scores.run_full_pipeline()


@st.cache_data(ttl=600)
def load_all_data():
    """
    โหลดทุกตารางจากฐานข้อมูลครั้งเดียว
    cache ไว้ 10 นาที
    """

    engine = get_connection()

    # ---------------------------------------------------------
    # Summary scores
    # ---------------------------------------------------------

    scores_df = pd.read_sql(
        """
        SELECT *
        FROM cis_summary_scores
        ORDER BY ticker
        """,
        engine,
    )

    # ---------------------------------------------------------
    # Daily prices
    # ---------------------------------------------------------

    daily_df = pd.read_sql(
        """
        SELECT *
        FROM stock_daily_prices
        ORDER BY ticker, date
        """,
        engine,
    )

    daily_df["date"] = pd.to_datetime(
        daily_df["date"]
    )

    # ---------------------------------------------------------
    # Financials
    # ---------------------------------------------------------

    fin_df = pd.read_sql(
        """
        SELECT *
        FROM stock_financials
        ORDER BY ticker, year
        """,
        engine,
    )

    # ---------------------------------------------------------
    # AI feature importance
    # ---------------------------------------------------------

    feat_imp_df = pd.read_sql(
        """
        SELECT *
        FROM ai_feature_importance
        """,
        engine,
    )

    # ---------------------------------------------------------
    # AI backtest
    # ---------------------------------------------------------

    try:

        backtest_df = pd.read_sql(
            """
            SELECT *
            FROM ai_backtest_history
            """,
            engine,
        )

        backtest_df["date"] = pd.to_datetime(
            backtest_df["date"]
        )

    except Exception:

        backtest_df = pd.DataFrame()

    # ---------------------------------------------------------
    # Risk rolling history
    # ---------------------------------------------------------

    try:

        risk_hist_df = pd.read_sql(
            """
            SELECT *
            FROM risk_rolling_history
            """,
            engine,
        )

        risk_hist_df["date"] = pd.to_datetime(
            risk_hist_df["date"]
        )

    except Exception:

        risk_hist_df = pd.DataFrame()

    # ---------------------------------------------------------
    # Health yearly
    # ---------------------------------------------------------

    try:

        health_yearly_df = pd.read_sql(
            """
            SELECT *
            FROM health_score_yearly
            """,
            engine,
        )

    except Exception:

        health_yearly_df = pd.DataFrame()

    # ---------------------------------------------------------
    # Fair value yearly
    # ---------------------------------------------------------

    try:

        fair_value_yearly_df = pd.read_sql(
            """
            SELECT *
            FROM fair_value_yearly
            """,
            engine,
        )

    except Exception:

        fair_value_yearly_df = pd.DataFrame()

    # ---------------------------------------------------------
    # Risk static
    # ---------------------------------------------------------

    try:

        risk_static_df = pd.read_sql(
            """
            SELECT *
            FROM stock_risk_static
            """,
            engine,
        )

    except Exception:

        risk_static_df = pd.DataFrame()

    return (
        scores_df,
        daily_df,
        fin_df,
        feat_imp_df,
        backtest_df,
        risk_hist_df,
        health_yearly_df,
        fair_value_yearly_df,
        risk_static_df,
    )


def ensure_database_ready():
    """
    เรียกจาก app.py ครั้งเดียวตอนเริ่มแอป
    """

    if not database_is_ready():

        with st.spinner(
            "⏳ กำลังประมวลผลข้อมูลครั้งแรก "
            "(import + calculate scores)... "
            "อาจใช้เวลาสักครู่"
        ):

            try:

                build_database()

                st.cache_data.clear()

            except Exception as build_err:

                st.error(
                    f"""
⚠️ สร้างฐานข้อมูลอัตโนมัติไม่สำเร็จ:

{build_err}

กรุณาตรวจสอบว่าโฟลเดอร์ Dataset/
ถูกอัปโหลดขึ้น GitHub ครบถ้วน

หรือรัน:

python import_data.py

แล้วตามด้วย:

python calculate_scores.py

ก่อนเปิด Dashboard
"""
                )

                st.stop()

    return True


# ============================================================================
# 5. PageContext
# ============================================================================

@dataclass
class PageContext:
    """
    ข้อมูลทั้งหมดที่หน้าโมดูลแต่ละหน้าอาจต้องใช้
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


def build_context(
    selected_ticker,
    scores_df,
    daily_df,
    fin_df,
    feat_imp_df,
    backtest_df,
    risk_hist_df,
    health_yearly_df,
    fair_value_yearly_df,
):
    """
    ประกอบ PageContext
    """

    selected_rows = scores_df[
        scores_df["ticker"] == selected_ticker
    ]

    if selected_rows.empty:

        raise ValueError(
            f"ไม่พบ ticker '{selected_ticker}' "
            "ใน cis_summary_scores"
        )

    stock_info = (
        selected_rows
        .iloc[0]
        .to_dict()
    )

    stock_daily = (
        daily_df[
            daily_df["ticker"] == selected_ticker
        ]
        .sort_values("date")
        .reset_index(drop=True)
    )

    fin_stock = (
        fin_df[
            fin_df["ticker"] == selected_ticker
        ]
        .sort_values("year")
        .reset_index(drop=True)
    )

    sector_peers = scores_df[
        scores_df["sector"] == stock_info.get("sector")
    ]

    current_price = safe(
        stock_info.get("current_price")
    )

    change_pct = safe(
        stock_info.get("change_pct")
    )

    change_val = safe(
        stock_info.get("change_val")
    )

    change_color = (
        "#10B981"
        if change_pct >= 0
        else "#EF4444"
    )

    change_sign = (
        "+"
        if change_pct >= 0
        else ""
    )

    arrow_sign = (
        "▲"
        if change_pct >= 0
        else "▼"
    )

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
# 6. UI ส่วนกลาง: Sidebar
# ============================================================================

def render_sidebar(scores_df):
    """
    วาด sidebar:
    - Logo
    - Company selector
    - Navigation
    - Data information

    return:
        nav_page
        selected_ticker
    """

    # =========================================================
    # LOGO
    #
    # ใช้ st.html() แทน markdown HTML
    # เพื่อไม่ให้ <div> / <span> ถูกแสดงเป็นข้อความ
    # =========================================================

    st.sidebar.html(
        """
        <div style="
            padding:8px 0 14px 0;
            width:100%;
            box-sizing:border-box;
        ">

            <div style="
                display:flex;
                align-items:flex-start;
                gap:10px;
                min-width:0;
                width:100%;
            ">

                <div style="
                    width:26px;
                    height:26px;
                    min-width:26px;
                    flex-shrink:0;
                    border-radius:7px;
                    background:#0F172A;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                ">
                    <span style="
                        font-size:13px;
                        font-weight:800;
                        color:#FFFFFF;
                    ">
                        CI
                    </span>
                </div>

                <span style="
                    font-size:15px;
                    font-weight:800;
                    color:#0F172A;
                    letter-spacing:-0.1px;
                    line-height:1.3;
                    min-width:0;
                    word-break:break-word;
                    overflow-wrap:break-word;
                ">
                    Comprehensive Investment System
                </span>

            </div>

            <div style="
                font-size:12px;
                color:#94A3B8;
                margin-top:4px;
                padding-left:36px;
                letter-spacing:0.3px;
                font-weight:600;
            ">
                Investment Decision Support
            </div>

        </div>
        """
    )

    st.sidebar.markdown("---")

    # =========================================================
    # NAVIGATION STATE
    # =========================================================

    if "nav_page" not in st.session_state:

        st.session_state["nav_page"] = PAGES[0]

    # ปุ่ม navigation จาก footer
    # ฝากค่ามาที่ pending_nav แล้วมาเปลี่ยนก่อน radio ถูกสร้าง

    if "pending_nav" in st.session_state:

        st.session_state["nav_page"] = (
            st.session_state.pop("pending_nav")
        )

    # =========================================================
    # COMPANY SELECTOR
    # =========================================================

    st.sidebar.markdown(
        """
        <div style="
            font-size:12px;
            font-weight:700;
            color:#64748B;
            margin-bottom:6px;
            letter-spacing:0.5px;
        ">
            COMPANY
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ป้องกัน ticker ซ้ำ
    ticker_options = (
        scores_df["ticker"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    selected_ticker = st.sidebar.selectbox(
        "Choose a company",
        ticker_options,
        label_visibility="collapsed",
    )

    st.sidebar.markdown("---")

    # =========================================================
    # NAVIGATION
    # =========================================================

    selected_page = st.sidebar.radio(
        "Navigation",
        PAGES,
        key="nav_page",
    )

    # =========================================================
    # NAV COLORS
    # =========================================================

    nav_colors = {

        " Overview":
            "#3B82F6",

        " Company Health":
            "#34D399",

        " Fair Value":
            "#FBBF24",

        " Entry Timing":
            "#38BDF8",

        " AI Prediction":
            "#C084FC",

        " Risk Analysis":
            "#FB923C",

        " Industry Benchmark":
            "#2DD4BF",
    }

    active_color = nav_colors.get(
        selected_page,
        "#3B82F6",
    )

    # =========================================================
    # SIDEBAR ACTIVE ITEM + RESPONSIVE CSS
    # =========================================================

    st.markdown(
        f"""
        <style>

        /* =====================================================
           ACTIVE SIDEBAR ITEM
           ===================================================== */

        [data-testid="stSidebar"]
        [data-testid="stRadio"]
        div[role="radiogroup"]
        label:has(input:checked) {{
            background-color:{active_color}12 !important;
            border:1px solid {active_color}30 !important;
            box-shadow:none !important;
        }}

        [data-testid="stSidebar"]
        [data-testid="stRadio"]
        div[role="radiogroup"]
        label:has(input:checked) p {{
            color:{active_color} !important;
            font-weight:700 !important;
        }}


        /* =====================================================
           RESPONSIVE / MOBILE
           ===================================================== */

        @media (max-width:768px) {{

            .main .block-container {{
                padding:1rem 0.85rem 2rem 0.85rem !important;
                max-width:100% !important;
            }}

            [data-testid="stHorizontalBlock"] {{
                flex-wrap:wrap !important;
                gap:0.75rem !important;
            }}

            [data-testid="column"] {{
                width:100% !important;
                flex:1 1 100% !important;
                min-width:100% !important;
            }}

            .cis-header {{
                flex-direction:column !important;
                align-items:flex-start !important;
                gap:10px !important;
                padding:14px 16px !important;
            }}

            .cis-header-info {{
                width:100% !important;
                display:flex !important;
                flex-wrap:wrap !important;
                gap:6px 10px !important;
                font-size:13px !important;
                white-space:normal !important;
                text-align:left !important;
            }}

            .cis-header-divider {{
                display:none !important;
            }}

            .module-title {{
                font-size:21px !important;
                line-height:1.25 !important;
            }}

            .module-subtitle {{
                font-size:14px !important;
                line-height:1.5 !important;
            }}

            [data-testid="stDataFrame"] {{
                width:100% !important;
                overflow-x:auto !important;
            }}

            .js-plotly-plot,
            .plot-container {{
                width:100% !important;
                max-width:100% !important;
            }}

            .stButton > button {{
                width:100% !important;
            }}
        }}


        /* =====================================================
           VERY SMALL MOBILE
           ===================================================== */

        @media (max-width:480px) {{

            .main .block-container {{
                padding:0.75rem 0.65rem 1.5rem 0.65rem !important;
            }}

            .module-title {{
                font-size:19px !important;
            }}

            .module-subtitle {{
                font-size:13.5px !important;
            }}

            [data-testid="stHorizontalBlock"] {{
                gap:0.6rem !important;
            }}
        }}

        </style>
        """,
        unsafe_allow_html=True,
    )

    nav_page = st.session_state["nav_page"]

    # =========================================================
    # DATA INFORMATION
    # =========================================================

    try:

        latest_date = scores_df["latest_date"].max()

    except Exception:

        latest_date = "-"

    st.sidebar.caption(
        f"📅 ข้อมูล ณ วันที่ล่าสุดในชุดข้อมูล: **{latest_date}**\n\n"
        "(ราคาทั้งหมดอ้างอิงจากไฟล์ Dataset ไม่ใช่ราคาตลาดสด)"
    )

    return nav_page, selected_ticker


# ============================================================================
# HEADER BAR
# ============================================================================

def render_header_bar(ctx):
    """
    แถบหัวข้อบนสุดของทุกหน้า

    ticker
    sector
    price
    change
    P/E
    ROE
    data as of

    สำคัญ:
    ใช้ st.html() เพื่อให้ HTML render จริง
    ไม่ให้ <div> / <span> / style="" โผล่บนหน้า
    """

    ticker = str(
        ctx.selected_ticker
    )

    sector = str(
        ctx.stock_info.get(
            "sector",
            "-"
        )
    )

    price = safe(
        ctx.current_price
    )

    change_pct = safe(
        ctx.change_pct
    )

    change_sign = (
        ctx.change_sign
        if ctx.change_sign is not None
        else (
            "+"
            if change_pct >= 0
            else ""
        )
    )

    arrow_sign = (
        ctx.arrow_sign
        if ctx.arrow_sign is not None
        else (
            "▲"
            if change_pct >= 0
            else "▼"
        )
    )

    change_color = (
        ctx.change_color
        if ctx.change_color
        else (
            "#10B981"
            if change_pct >= 0
            else "#EF4444"
        )
    )

    pe = fmt_ratio(
        ctx.stock_info.get(
            "pe_ratio"
        )
    )

    roe = ctx.stock_info.get(
        "roe",
        "-"
    )

    if roe is None or pd.isna(roe):
        roe = "-"

    latest_date = ctx.stock_info.get(
        "latest_date",
        "-"
    )

    if latest_date is None:
        latest_date = "-"

    # =========================================================
    # IMPORTANT
    #
    # ใช้ st.html() แทน st.markdown()
    # เพราะ block นี้เป็น HTML โดยตรง
    # =========================================================

    st.html(
        f"""
        <div
            class="cis-header"
            style="
                display:flex;
                justify-content:space-between;
                align-items:center;
                background:#FFFFFF;
                padding:14px 24px;
                border-radius:12px;
                border:1px solid #E2E8F0;
                margin-bottom:20px;
                width:100%;
                box-sizing:border-box;
            "
        >

            <!-- =================================================
                 LEFT SIDE
                 ================================================= -->

            <div
                style="
                    min-width:0;
                    flex:1;
                "
            >

                <span
                    style="
                        font-size:24px;
                        font-weight:700;
                        color:#0F172A;
                    "
                >
                    {ticker}
                </span>

                <span
                    style="
                        color:#64748B;
                        font-size:15px;
                        margin-left:8px;
                    "
                >
                    {sector} (SET)
                </span>

            </div>


            <!-- =================================================
                 RIGHT SIDE
                 ================================================= -->

            <div
                class="cis-header-info"
                style="
                    font-size:16.5px;
                    color:#64748B;
                    white-space:nowrap;
                    text-align:right;
                "
            >

                Price:

                <b
                    style="
                        color:#0F172A;
                        font-size:19px;
                    "
                >
                    {price:.2f}
                </b>

                THB

                <span
                    style="
                        color:{change_color};
                        font-weight:700;
                        margin-left:6px;
                    "
                >
                    ({change_sign}{change_pct:.2f}%)
                    {arrow_sign}
                </span>


                <span
                    class="cis-header-divider"
                    style="
                        margin:0 12px;
                        color:#CBD5E1;
                    "
                >
                    |
                </span>


                P/E:

                <b
                    style="
                        color:#0F172A;
                    "
                >
                    {pe}
                </b>


                <span
                    class="cis-header-divider"
                    style="
                        margin:0 12px;
                        color:#CBD5E1;
                    "
                >
                    |
                </span>


                ROE:

                <b
                    style="
                        color:#0F172A;
                    "
                >
                    {roe}%
                </b>


                <span
                    class="cis-header-divider"
                    style="
                        margin:0 12px;
                        color:#CBD5E1;
                    "
                >
                    |
                </span>


                Data as of:

                <b
                    style="
                        color:#475569;
                    "
                >
                    {latest_date}
                </b>

            </div>

        </div>
        """
    )
