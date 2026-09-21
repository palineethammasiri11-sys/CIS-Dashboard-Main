"""
pages_content/fair_value.py
---------------------------
หน้า "Fair Value" ของ CIS Dashboard

วิธีทดสอบหน้านี้แบบเดี่ยว:
    streamlit run preview_my_page.py

ข้อมูลที่ใช้ได้ใน ctx:
    ctx.selected_ticker
    ctx.stock_info
    ctx.stock_daily
    ctx.fin_stock
    ctx.sector_peers
    ctx.scores_df
    ctx.fin_df
    ctx.feat_imp_df
    ctx.backtest_df
    ctx.risk_hist_df
    ctx.health_yearly_df
    ctx.fair_value_yearly_df
    ctx.current_price
    ctx.change_pct
    ctx.change_val
    ctx.change_color
    ctx.change_sign
    ctx.arrow_sign

ห้ามแก้ CSS ส่วนกลางหรือ helper function ใน common.py จากไฟล์นี้
"""

import textwrap

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from common import (
    fmt_mb,
    fmt_ratio,
    safe,
    show_chart,
    render_nav_footer,
    COMPANY_NAMES,
    SECTOR_MAP,
)


# ============================================================
# HTML HELPER
# ============================================================
# สำคัญมาก:
# ถ้า HTML ใน st.markdown() มี indentation จาก Python
# Streamlit อาจตีความเป็น code block แล้วแสดง <div> ออกมาเป็นข้อความ
def _html(content: str) -> str:
    return textwrap.dedent(content).strip()


def render(ctx):

    # ========================================================
    # BASIC VALUES
    # ========================================================
    val_cur_price = safe(ctx.current_price, 0.0)

    val_fair_value = safe(
        ctx.stock_info.get("fair_value"),
        val_cur_price * 1.1,
    )

    val_mos = safe(
        ctx.stock_info.get("margin_of_safety"),
        10.0,
    )

    val_score = int(
        round(
            safe(
                ctx.stock_info.get("valuation_score"),
                75,
            )
        )
    )

    val_score = max(0, min(100, val_score))

    # ========================================================
    # VALUATION STATUS
    # ========================================================
    if val_mos > 10:
        val_status = "UNDERVALUED"
        val_color = "#10B981"
        val_bg = "rgba(16,185,129,0.08)"
        val_border = "#10B981"
        val_rec_label = "ATTRACTIVE"

    elif val_mos < -10:
        val_status = "OVERVALUED"
        val_color = "#EF4444"
        val_bg = "rgba(239,68,68,0.08)"
        val_border = "#EF4444"
        val_rec_label = "CAUTION"

    else:
        val_status = "FAIR VALUE"
        val_color = "#F59E0B"
        val_bg = "rgba(245,158,11,0.08)"
        val_border = "#F59E0B"
        val_rec_label = "FAIR"

    # ========================================================
    # FAIR VALUE VALUES
    # ========================================================
    val_bear = safe(
        ctx.stock_info.get("dcf_fair_value"),
        val_fair_value * 0.9,
    )

    val_base = val_fair_value

    val_bull = safe(
        ctx.stock_info.get("pe_fair_value"),
        val_fair_value * 1.1,
    )

    # เรียง lower / upper เพื่อให้กราฟและ card ดูถูกต้องเสมอ
    lo = min(val_bear, val_bull)
    hi = max(val_bear, val_bull)

    val_bear = lo
    val_bull = hi

    # ========================================================
    # STARS
    # ========================================================
    val_stars = min(
        5,
        max(
            1,
            round(val_score / 20),
        ),
    )

    # ========================================================
    # PAGE HEADER
    # ========================================================
    st.markdown(
        _html(
            """
            <div
                style="
                    display:flex;
                    justify-content:space-between;
                    align-items:flex-end;
                    margin-bottom:15px;
                "
            >
                <div>
                    <div
                        style="
                            display:flex;
                            align-items:center;
                            gap:8px;
                        "
                    >
                        <h2
                            style="
                                margin:0;
                                font-size:23px;
                                font-weight:bold;
                                color:#0F172A;
                                letter-spacing:0.5px;
                            "
                        >
                            FAIR VALUE
                        </h2>
                    </div>

                    <div
                        style="
                            font-size:15px;
                            color:#64748B;
                            margin-top:2px;
                        "
                    >
                        ประเมินมูลค่าที่เหมาะสมของหุ้นโดยใช้แบบจำลอง DCF ผสาน P/E Relative
                    </div>
                </div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    # ========================================================
    # ROW 1
    # ========================================================
    r1_c1, r1_c2, r1_c3, r1_c4, r1_c5, r1_c6 = st.columns(
        [1.5, 0.9, 0.9, 0.9, 0.9, 1.1]
    )

    # ========================================================
    # FAIR VALUE SUMMARY
    # ========================================================
    with r1_c1:

        st.markdown(
            _html(
                f"""
                <div
                    style="
                        background-color:#FFFFFF;
                        border:2px solid {val_border};
                        border-radius:16px;
                        padding:14px;
                        min-height:170px;
                        display:flex;
                        flex-direction:column;
                        justify-content:space-between;
                        box-shadow:
                            0 4px 14px rgba(15,23,42,0.06);
                    "
                >

                    <div
                        style="
                            font-size:13.5px;
                            font-weight:bold;
                            color:#64748B;
                            letter-spacing:0.5px;
                        "
                    >
                        FAIR VALUE SUMMARY
                    </div>

                    <div
                        style="
                            display:flex;
                            align-items:center;
                            gap:12px;
                            margin-top:10px;
                        "
                    >

                        <!-- SCORE RING -->
                        <div
                            style="
                                width:76px;
                                height:76px;
                                min-width:76px;
                                border-radius:50%;
                                background:
                                    conic-gradient(
                                        {val_color} 0% {val_score}%,
                                        #E2E8F0 {val_score}% 100%
                                    );
                                display:flex;
                                align-items:center;
                                justify-content:center;
                            "
                        >

                            <div
                                style="
                                    width:62px;
                                    height:62px;
                                    border-radius:50%;
                                    background-color:#FFFFFF;
                                    display:flex;
                                    flex-direction:column;
                                    align-items:center;
                                    justify-content:center;
                                "
                            >
                                <span
                                    style="
                                        font-size:19px;
                                        font-weight:bold;
                                        color:#0F172A;
                                        line-height:1;
                                    "
                                >
                                    {val_score}
                                </span>

                                <span
                                    style="
                                        font-size:12px;
                                        color:#64748B;
                                        margin-top:3px;
                                    "
                                >
                                    /100
                                </span>
                            </div>

                        </div>

                        <!-- SUMMARY TEXT -->
                        <div
                            style="
                                min-width:0;
                                flex:1;
                            "
                        >

                            <div
                                style="
                                    color:{val_color};
                                    font-size:16.5px;
                                    font-weight:bold;
                                    line-height:1.2;
                                "
                            >
                                {val_status}
                            </div>

                            <div
                                style="
                                    font-size:13px;
                                    color:#475569;
                                    line-height:1.35;
                                    margin-top:3px;
                                "
                            >
                                Margin of Safety อยู่ที่ {val_mos:.1f}%
                                เมื่อเทียบกับมูลค่าพื้นฐานที่แท้จริง
                            </div>

                            <div
                                style="
                                    color:{val_color};
                                    font-size:14.5px;
                                    letter-spacing:1px;
                                    margin-top:4px;
                                "
                            >
                                {"★" * val_stars}{"☆" * (5 - val_stars)}
                            </div>

                        </div>

                    </div>

                </div>
                """
            ),
            unsafe_allow_html=True,
        )

    # ========================================================
    # CURRENT PRICE
    # ========================================================
    with r1_c2:

        st.markdown(
            _html(
                f"""
                <div
                    style="
                        background-color:#FFFFFF;
                        border:1px solid #E2E8F0;
                        border-radius:12px;
                        padding:12px;
                        min-height:170px;
                        display:flex;
                        flex-direction:column;
                        justify-content:space-between;
                    "
                >

                    <div
                        style="
                            font-size:13px;
                            font-weight:bold;
                            color:#64748B;
                        "
                    >
                        CURRENT PRICE
                    </div>

                    <div>

                        <div
                            style="
                                font-size:21px;
                                font-weight:bold;
                                color:#0F172A;
                                line-height:1;
                            "
                        >
                            {val_cur_price:.2f}
                            <span
                                style="
                                    font-size:13.5px;
                                    color:#64748B;
                                "
                            >
                                THB
                            </span>
                        </div>

                        <div
                            style="
                                font-size:12px;
                                color:#64748B;
                                margin-top:2px;
                            "
                        >
                            ({ctx.stock_info.get("latest_date", "-")})
                        </div>

                    </div>

                </div>
                """
            ),
            unsafe_allow_html=True,
        )

    # ========================================================
    # ESTIMATED FAIR VALUE
    # ========================================================
    with r1_c3:

        st.markdown(
            _html(
                f"""
                <div
                    style="
                        background-color:#FFFFFF;
                        border:1px solid #E2E8F0;
                        border-radius:12px;
                        padding:12px;
                        min-height:170px;
                        display:flex;
                        flex-direction:column;
                        justify-content:space-between;
                    "
                >

                    <div
                        style="
                            font-size:13px;
                            font-weight:bold;
                            color:#64748B;
                            line-height:1.35;
                        "
                    >
                        ESTIMATED FAIR VALUE
                        <br>
                        <span
                            style="
                                font-size:12px;
                                color:#64748B;
                            "
                        >
                            (BLENDED: 55% DCF + 45% P/E)
                        </span>
                    </div>

                    <div>

                        <div
                            style="
                                font-size:21px;
                                font-weight:bold;
                                color:#0F172A;
                                line-height:1;
                            "
                        >
                            {val_base:.2f}
                            <span
                                style="
                                    font-size:13.5px;
                                    color:#64748B;
                                "
                            >
                                THB
                            </span>
                        </div>

                    </div>

                </div>
                """
            ),
            unsafe_allow_html=True,
        )

    # ========================================================
    # MARGIN OF SAFETY
    # ========================================================
    with r1_c4:

        st.markdown(
            _html(
                f"""
                <div
                    style="
                        background-color:#FFFFFF;
                        border:1px solid #E2E8F0;
                        border-radius:12px;
                        padding:12px;
                        min-height:170px;
                        display:flex;
                        flex-direction:column;
                        justify-content:space-between;
                        text-align:center;
                    "
                >

                    <div
                        style="
                            font-size:13px;
                            font-weight:bold;
                            color:#64748B;
                            text-align:left;
                        "
                    >
                        MARGIN OF SAFETY
                    </div>

                    <div>

                        <div
                            style="
                                font-size:21px;
                                font-weight:bold;
                                color:{val_color};
                                line-height:1;
                            "
                        >
                            {val_mos:.1f}%
                        </div>

                    </div>

                    <div
                        style="
                            margin-top:auto;
                            display:flex;
                            justify-content:center;
                        "
                    >
                        <div
                            style="
                                background:{val_bg};
                                border:1px solid {val_color};
                                border-radius:50%;
                                width:36px;
                                height:36px;
                                display:flex;
                                align-items:center;
                                justify-content:center;
                                font-size:15px;
                            "
                        >
                            🛡️
                        </div>
                    </div>

                </div>
                """
            ),
            unsafe_allow_html=True,
        )

    # ========================================================
    # CONFIDENCE
    # ========================================================
    with r1_c5:

        conf = (
            "High"
            if abs(val_mos) > 15
            else ("Medium" if abs(val_mos) > 5 else "Low")
        )

        conf_color = (
            "#10B981"
            if conf == "High"
            else (
                "#F59E0B"
                if conf == "Medium"
                else "#EF4444"
            )
        )

        st.markdown(
            _html(
                f"""
                <div
                    style="
                        background-color:#FFFFFF;
                        border:1px solid #E2E8F0;
                        border-radius:12px;
                        padding:12px;
                        min-height:170px;
                        display:flex;
                        flex-direction:column;
                        justify-content:space-between;
                        text-align:center;
                    "
                >

                    <div
                        style="
                            font-size:13px;
                            font-weight:bold;
                            color:#64748B;
                            text-align:left;
                        "
                    >
                        CONFIDENCE LEVEL
                    </div>

                    <div>

                        <div
                            style="
                                font-size:18.5px;
                                font-weight:bold;
                                color:{conf_color};
                                line-height:1;
                            "
                        >
                            {conf.upper()}
                        </div>

                    </div>

                </div>
                """
            ),
            unsafe_allow_html=True,
        )

    # ========================================================
    # RECOMMENDATION
    # ========================================================
    with r1_c6:

        st.markdown(
            _html(
                f"""
                <div
                    style="
                        background-color:#FFFFFF;
                        border:1px solid #E2E8F0;
                        border-radius:12px;
                        padding:12px;
                        min-height:170px;
                        display:flex;
                        flex-direction:column;
                        justify-content:space-between;
                        text-align:center;
                    "
                >

                    <div
                        style="
                            font-size:13px;
                            font-weight:bold;
                            color:#64748B;
                            text-align:left;
                        "
                    >
                        RECOMMENDATION
                    </div>

                    <div>

                        <div
                            style="
                                font-size:17.5px;
                                font-weight:bold;
                                color:{val_color};
                                line-height:1.1;
                            "
                        >
                            {val_rec_label}
                        </div>

                    </div>

                </div>
                """
            ),
            unsafe_allow_html=True,
        )

    # ========================================================
    # SPACING
    # ========================================================
    st.markdown(
        "<div style='margin-top:22px;'></div>",
        unsafe_allow_html=True,
    )

    # ========================================================
    # ROW 2
    # ========================================================
    r2_c1, r2_c2, r2_c3 = st.columns(
        [1.3, 1.3, 1.4]
    )

    # ========================================================
    # FAIR VALUE RANGE
    # ========================================================
    with r2_c1:

        latest_year = (
            int(ctx.fin_stock["year"].max())
            if (
                not ctx.fin_stock.empty
                and "year" in ctx.fin_stock.columns
            )
            else "-"
        )

        st.markdown(
            _html(
                f"""
                <div
                    style="
                        background-color:#FFFFFF;
                        border:1px solid #E2E8F0;
                        border-radius:12px;
                        padding:14px;
                        min-height:315px;
                        display:flex;
                        flex-direction:column;
                        justify-content:space-between;
                    "
                >

                    <div
                        style="
                            font-size:14px;
                            font-weight:bold;
                            color:#64748B;
                            letter-spacing:0.5px;
                        "
                    >
                        FAIR VALUE RANGE — DCF vs P/E RELATIVE
                    </div>

                    <div
                        style="
                            display:grid;
                            grid-template-columns:1fr 1.1fr 1fr;
                            gap:6px;
                            margin-top:6px;
                        "
                    >

                        <div
                            style="
                                background:#F8FAFC;
                                border:1px solid #E2E8F0;
                                border-radius:8px;
                                padding:8px 4px;
                                text-align:center;
                            "
                        >
                            <div
                                style="
                                    color:#38BDF8;
                                    font-size:13.5px;
                                    font-weight:bold;
                                "
                            >
                                Lower Estimate
                            </div>

                            <div
                                style="
                                    color:#64748B;
                                    font-size:12px;
                                "
                            >
                                Min(DCF, P/E)
                            </div>

                            <div
                                style="
                                    color:#0F172A;
                                    font-size:16px;
                                    font-weight:bold;
                                    margin-top:4px;
                                "
                            >
                                {val_bear:.2f}
                                <span
                                    style="
                                        font-size:12px;
                                        color:#64748B;
                                    "
                                >
                                    THB
                                </span>
                            </div>
                        </div>

                        <div
                            style="
                                background:#F8FAFC;
                                border:1.5px solid #8B5CF6;
                                border-radius:8px;
                                padding:8px 4px;
                                text-align:center;
                            "
                        >
                            <div
                                style="
                                    color:#C084FC;
                                    font-size:13.5px;
                                    font-weight:bold;
                                "
                            >
                                Blended Fair Value
                            </div>

                            <div
                                style="
                                    color:#64748B;
                                    font-size:12px;
                                "
                            >
                                55% DCF + 45% P/E
                            </div>

                            <div
                                style="
                                    color:#0F172A;
                                    font-size:16.5px;
                                    font-weight:bold;
                                    margin-top:4px;
                                "
                            >
                                {val_base:.2f}
                                <span
                                    style="
                                        font-size:12px;
                                        color:#64748B;
                                    "
                                >
                                    THB
                                </span>
                            </div>
                        </div>

                        <div
                            style="
                                background:#F8FAFC;
                                border:1px solid #E2E8F0;
                                border-radius:8px;
                                padding:8px 4px;
                                text-align:center;
                            "
                        >
                            <div
                                style="
                                    color:#10B981;
                                    font-size:13.5px;
                                    font-weight:bold;
                                "
                            >
                                Upper Estimate
                            </div>

                            <div
                                style="
                                    color:#64748B;
                                    font-size:12px;
                                "
                            >
                                Max(DCF, P/E)
                            </div>

                            <div
                                style="
                                    color:#0F172A;
                                    font-size:16px;
                                    font-weight:bold;
                                    margin-top:4px;
                                "
                            >
                                {val_bull:.2f}
                                <span
                                    style="
                                        font-size:12px;
                                        color:#64748B;
                                    "
                                >
                                    THB
                                </span>
                            </div>
                        </div>

                    </div>

                    <div
                        style="
                            background:rgba(16,185,129,0.08);
                            border-radius:6px;
                            padding:6px 8px;
                            display:flex;
                            align-items:flex-start;
                            gap:6px;
                            margin-top:10px;
                        "
                    >

                        <span
                            style="
                                color:#10B981;
                                font-size:14.5px;
                            "
                        >
                            ✔
                        </span>

                        <div
                            style="
                                font-size:12.5px;
                                color:#475569;
                                line-height:1.3;
                            "
                        >

                            <b>
                                DCF Fair Value:
                                {safe(ctx.stock_info.get("dcf_fair_value"), 0):.2f}
                                THB
                                &nbsp;|&nbsp;
                                P/E Fair Value:
                                {safe(ctx.stock_info.get("pe_fair_value"), 0):.2f}
                                THB
                            </b>

                            <br>

                            <span style="color:#64748B;">
                                คำนวณจากงบการเงินปีล่าสุด
                                (FY{latest_year})
                                เทียบราคาตลาดปัจจุบัน
                                {val_cur_price:.2f} THB
                            </span>

                        </div>

                    </div>

                </div>
                """
            ),
            unsafe_allow_html=True,
        )

    # ========================================================
    # VALUATION DRIVERS
    # ========================================================
    with r2_c2:

        pe_ratio_display = fmt_ratio(
            ctx.stock_info.get("pe_ratio"),
            suffix="",
        )

        eps_display = ctx.stock_info.get(
            "eps",
            "-",
        )

        st.markdown(
            _html(
                f"""
                <div
                    style="
                        background-color:#FFFFFF;
                        border:1px solid #E2E8F0;
                        border-radius:12px;
                        padding:14px;
                        min-height:315px;
                        display:flex;
                        flex-direction:column;
                        justify-content:space-between;
                    "
                >

                    <div
                        style="
                            font-size:14px;
                            font-weight:bold;
                            color:#64748B;
                            letter-spacing:0.5px;
                        "
                    >
                        VALUATION DRIVERS ({ctx.selected_ticker})
                    </div>

                    <div
                        style="
                            font-size:13px;
                            color:#475569;
                            line-height:1.45;
                            display:flex;
                            flex-direction:column;
                            gap:6px;
                            margin:auto 0;
                        "
                    >

                        <div
                            style="
                                display:flex;
                                gap:6px;
                            "
                        >
                            <span style="color:#10B981;">
                                ✔
                            </span>

                            <div>
                                <b>
                                    Fair Value (Blended):
                                    {val_base:.2f} THB
                                </b>

                                <br>

                                <span
                                    style="
                                        color:#64748B;
                                        font-size:12.5px;
                                    "
                                >
                                    ประเมินแบบผสมผสาน DCF + Relative P/E
                                </span>
                            </div>
                        </div>

                        <div
                            style="
                                display:flex;
                                gap:6px;
                            "
                        >
                            <span style="color:#10B981;">
                                ✔
                            </span>

                            <div>
                                <b>
                                    Margin of Safety:
                                    {val_mos:.1f}%
                                </b>

                                <br>

                                <span
                                    style="
                                        color:#64748B;
                                        font-size:12.5px;
                                    "
                                >
                                    ส่วนต่างความปลอดภัยจากราคาตลาดปัจจุบัน
                                </span>
                            </div>
                        </div>

                        <div
                            style="
                                display:flex;
                                gap:6px;
                            "
                        >
                            <span style="color:#10B981;">
                                ✔
                            </span>

                            <div>
                                <b>
                                    P/E Ratio ปัจจุบัน:
                                    {pe_ratio_display} เท่า
                                </b>

                                <br>

                                <span
                                    style="
                                        color:#64748B;
                                        font-size:12.5px;
                                    "
                                >
                                    เทียบ EPS ล่าสุด
                                    {eps_display}
                                    บาท/หุ้น
                                </span>
                            </div>
                        </div>

                        <div
                            style="
                                display:flex;
                                gap:6px;
                            "
                        >
                            <span style="color:#10B981;">
                                ✔
                            </span>

                            <div>
                                <b>
                                    สถานะมูลค่า:
                                    {val_status}
                                </b>

                                <br>

                                <span
                                    style="
                                        color:#64748B;
                                        font-size:12.5px;
                                    "
                                >
                                    ระดับความน่าดึงดูดเชิงมูลค่าพื้นฐาน
                                </span>
                            </div>
                        </div>

                    </div>

                </div>
                """
            ),
            unsafe_allow_html=True,
        )

    # ========================================================
    # FAIR VALUE SCORE BY DIMENSION
    # ========================================================
    with r2_c3:

        safety_score = int(
            min(
                100,
                max(
                    20,
                    int(val_mos + 50),
                ),
            )
        )

        st.markdown(
            _html(
                f"""
                <div
                    style="
                        background-color:#FFFFFF;
                        border:1px solid #E2E8F0;
                        border-radius:12px;
                        padding:14px;
                        min-height:315px;
                        display:flex;
                        flex-direction:column;
                        justify-content:space-between;
                    "
                >

                    <div
                        style="
                            font-size:14px;
                            font-weight:bold;
                            color:#64748B;
                            letter-spacing:0.5px;
                        "
                    >
                        FAIR VALUE SCORE BY DIMENSION
                    </div>

                    <div
                        style="
                            display:flex;
                            flex-direction:column;
                            gap:10px;
                            margin:auto 0;
                        "
                    >

                        <!-- P/E -->
                        <div>

                            <div
                                style="
                                    display:flex;
                                    justify-content:space-between;
                                    font-size:13px;
                                    color:#475569;
                                    margin-bottom:3px;
                                "
                            >
                                <span>
                                    📊 Relative Valuation (P/E)
                                </span>

                                <span
                                    style="
                                        font-weight:bold;
                                        color:#0F172A;
                                    "
                                >
                                    {val_score}
                                    <span
                                        style="
                                            font-size:12px;
                                            color:#64748B;
                                        "
                                    >
                                        /100
                                    </span>
                                </span>
                            </div>

                            <div
                                style="
                                    background:#E2E8F0;
                                    height:9px;
                                    border-radius:4px;
                                    overflow:hidden;
                                "
                            >
                                <div
                                    style="
                                        background:#10B981;
                                        width:{val_score}%;
                                        height:100%;
                                    "
                                ></div>
                            </div>

                        </div>

                        <!-- DCF -->
                        <div>

                            <div
                                style="
                                    display:flex;
                                    justify-content:space-between;
                                    font-size:13px;
                                    color:#475569;
                                    margin-bottom:3px;
                                "
                            >
                                <span>
                                    🎯 Intrinsic Valuation (DCF)
                                </span>

                                <span
                                    style="
                                        font-weight:bold;
                                        color:#0F172A;
                                    "
                                >
                                    {val_score}
                                    <span
                                        style="
                                            font-size:12px;
                                            color:#64748B;
                                        "
                                    >
                                        /100
                                    </span>
                                </span>
                            </div>

                            <div
                                style="
                                    background:#E2E8F0;
                                    height:9px;
                                    border-radius:4px;
                                    overflow:hidden;
                                "
                            >
                                <div
                                    style="
                                        background:#10B981;
                                        width:{val_score}%;
                                        height:100%;
                                    "
                                ></div>
                            </div>

                        </div>

                        <!-- MOS -->
                        <div>

                            <div
                                style="
                                    display:flex;
                                    justify-content:space-between;
                                    font-size:13px;
                                    color:#475569;
                                    margin-bottom:3px;
                                "
                            >
                                <span>
                                    🛡️ Margin of Safety
                                </span>

                                <span
                                    style="
                                        font-weight:bold;
                                        color:#0F172A;
                                    "
                                >
                                    {safety_score}
                                    <span
                                        style="
                                            font-size:12px;
                                            color:#64748B;
                                        "
                                    >
                                        /100
                                    </span>
                                </span>
                            </div>

                            <div
                                style="
                                    background:#E2E8F0;
                                    height:9px;
                                    border-radius:4px;
                                    overflow:hidden;
                                "
                            >
                                <div
                                    style="
                                        background:{val_color};
                                        width:{safety_score}%;
                                        height:100%;
                                    "
                                ></div>
                            </div>

                        </div>

                    </div>

                    <div
                        style="
                            display:flex;
                            justify-content:space-between;
                            align-items:center;
                            border-top:1px solid #E2E8F0;
                            padding-top:8px;
                        "
                    >

                        <span
                            style="
                                font-size:13.5px;
                                font-weight:bold;
                                color:#475569;
                            "
                        >
                            OVERALL FAIR VALUE SCORE
                        </span>

                        <span
                            style="
                                font-size:18.5px;
                                font-weight:bold;
                                color:{val_color};
                            "
                        >
                            {val_score}
                            <span
                                style="
                                    font-size:13px;
                                    color:#64748B;
                                "
                            >
                                /100
                            </span>
                        </span>

                    </div>

                </div>
                """
            ),
            unsafe_allow_html=True,
        )

    # ========================================================
    # DETAIL BREAKDOWN
    # ========================================================
    st.markdown(
        "<div style='margin-top:22px;'></div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        _html(
            """
            <div
                style="
                    font-size:14.5px;
                    font-weight:bold;
                    color:#64748B;
                    letter-spacing:0.5px;
                    margin-bottom:8px;
                "
            >
                DETAIL BREAKDOWN
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    d_c1, d_c2, d_c3, d_c4 = st.columns(4)

    # ========================================================
    # RELATIVE VALUATION
    # ========================================================
    with d_c1:

        st.markdown(
            _html(
                f"""
                <div
                    style="
                        background-color:#FFFFFF;
                        border:1px solid #E2E8F0;
                        border-radius:10px;
                        padding:12px;
                        min-height:190px;
                        display:flex;
                        flex-direction:column;
                        justify-content:space-between;
                    "
                >

                    <div>

                        <div
                            style="
                                font-size:13px;
                                font-weight:bold;
                                color:#475569;
                            "
                        >
                            RELATIVE VALUATION (P/E)
                        </div>

                        <table
                            style="
                                width:100%;
                                font-size:13px;
                                color:#475569;
                                border-collapse:collapse;
                                margin-top:6px;
                            "
                        >

                            <tr
                                style="
                                    border-bottom:1px solid #E2E8F0;
                                    color:#64748B;
                                    font-size:12.5px;
                                "
                            >
                                <th
                                    style="
                                        text-align:left;
                                        padding:2px 0;
                                    "
                                >
                                    Metric
                                </th>

                                <th>
                                    Value
                                </th>
                            </tr>

                            <tr
                                style="
                                    border-bottom:1px solid #E2E8F0;
                                "
                            >
                                <td style="padding:3px 0;">
                                    P/E Ratio ปัจจุบัน
                                </td>

                                <td>
                                    {fmt_ratio(ctx.stock_info.get("pe_ratio"))}
                                </td>
                            </tr>

                            <tr>
                                <td style="padding:3px 0;">
                                    P/E Fair Value
                                </td>

                                <td>
                                    {safe(ctx.stock_info.get("pe_fair_value"), 0):.2f}
                                    THB
                                </td>
                            </tr>

                        </table>

                    </div>

                </div>
                """
            ),
            unsafe_allow_html=True,
        )

    # ========================================================
    # DCF
    # ========================================================
    with d_c2:

        st.markdown(
            _html(
                f"""
                <div
                    style="
                        background-color:#FFFFFF;
                        border:1px solid #E2E8F0;
                        border-radius:10px;
                        padding:12px;
                        min-height:190px;
                        display:flex;
                        flex-direction:column;
                        justify-content:space-between;
                    "
                >

                    <div>

                        <div
                            style="
                                font-size:13px;
                                font-weight:bold;
                                color:#475569;
                            "
                        >
                            INTRINSIC VALUATION (DCF)
                        </div>

                        <table
                            style="
                                width:100%;
                                font-size:13px;
                                color:#475569;
                                border-collapse:collapse;
                                margin-top:6px;
                            "
                        >

                            <tr
                                style="
                                    border-bottom:1px solid #E2E8F0;
                                    color:#64748B;
                                    font-size:12.5px;
                                "
                            >
                                <th
                                    style="
                                        text-align:left;
                                        padding:2px 0;
                                    "
                                >
                                    Metric
                                </th>

                                <th>
                                    Value
                                </th>
                            </tr>

                            <tr
                                style="
                                    border-bottom:1px solid #E2E8F0;
                                "
                            >
                                <td style="padding:3px 0;">
                                    WACC
                                </td>

                                <td>
                                    {fmt_ratio(
                                        ctx.stock_info.get("wacc_used"),
                                        suffix="%",
                                        decimals=1,
                                    )}
                                </td>
                            </tr>

                            <tr>
                                <td style="padding:3px 0;">
                                    DCF Fair Value
                                </td>

                                <td>
                                    {safe(
                                        ctx.stock_info.get("dcf_fair_value"),
                                        0,
                                    ):.2f}
                                    THB
                                </td>
                            </tr>

                        </table>

                    </div>

                </div>
                """
            ),
            unsafe_allow_html=True,
        )

    # ========================================================
    # PRICE COMPARISON
    # ========================================================
    with d_c3:

        difference = val_base - val_cur_price

        st.markdown(
            _html(
                f"""
                <div
                    style="
                        background-color:#FFFFFF;
                        border:1px solid #E2E8F0;
                        border-radius:10px;
                        padding:12px;
                        min-height:190px;
                        display:flex;
                        flex-direction:column;
                        justify-content:space-between;
                    "
                >

                    <div>

                        <div
                            style="
                                font-size:13px;
                                font-weight:bold;
                                color:#475569;
                            "
                        >
                            PRICE COMPARISON
                        </div>

                        <table
                            style="
                                width:100%;
                                font-size:13px;
                                color:#475569;
                                border-collapse:collapse;
                                margin-top:6px;
                            "
                        >

                            <tr
                                style="
                                    border-bottom:1px solid #E2E8F0;
                                "
                            >
                                <td style="padding:3px 0;">
                                    Current
                                </td>

                                <td>
                                    {val_cur_price:.2f}
                                </td>
                            </tr>

                            <tr
                                style="
                                    border-bottom:1px solid #E2E8F0;
                                "
                            >
                                <td style="padding:3px 0;">
                                    Fair Value
                                </td>

                                <td>
                                    {val_base:.2f}
                                </td>
                            </tr>

                            <tr>
                                <td style="padding:3px 0;">
                                    Difference
                                </td>

                                <td
                                    style="
                                        color:{val_color};
                                        font-weight:bold;
                                    "
                                >
                                    {difference:+.2f}
                                </td>
                            </tr>

                        </table>

                    </div>

                </div>
                """
            ),
            unsafe_allow_html=True,
        )

    # ========================================================
    # MARGIN OF SAFETY DETAIL
    # ========================================================
    with d_c4:

        st.markdown(
            _html(
                f"""
                <div
                    style="
                        background-color:#FFFFFF;
                        border:1px solid #E2E8F0;
                        border-radius:10px;
                        padding:12px;
                        min-height:190px;
                        display:flex;
                        flex-direction:column;
                        justify-content:space-between;
                    "
                >

                    <div>

                        <div
                            style="
                                font-size:13px;
                                font-weight:bold;
                                color:#475569;
                            "
                        >
                            MARGIN OF SAFETY
                        </div>

                        <table
                            style="
                                width:100%;
                                font-size:13px;
                                color:#475569;
                                border-collapse:collapse;
                                margin-top:6px;
                            "
                        >

                            <tr>
                                <td style="padding:3px 0;">
                                    Margin of Safety
                                </td>

                                <td
                                    style="
                                        color:{val_color};
                                        font-weight:bold;
                                    "
                                >
                                    {val_mos:.1f}%
                                </td>
                            </tr>

                        </table>

                    </div>

                </div>
                """
            ),
            unsafe_allow_html=True,
        )

    # ========================================================
    # ROW 4
    # ========================================================
    st.markdown(
        "<div style='margin-top:22px;'></div>",
        unsafe_allow_html=True,
    )

    r4_c1, r4_c2 = st.columns(
        [1.3, 1.7]
    )

    # ========================================================
    # DCF ASSUMPTIONS
    # ========================================================
    with r4_c1:

        wacc_disp = fmt_ratio(
            ctx.stock_info.get("wacc_used"),
            suffix="%",
            decimals=1,
        )

        g_disp = fmt_ratio(
            ctx.stock_info.get("terminal_growth_used"),
            suffix="%",
            decimals=1,
        )

        fcf_g_disp = fmt_ratio(
            ctx.stock_info.get("fcf_growth_assumed"),
            suffix="%",
            decimals=1,
        )

        sector_name = ctx.stock_info.get(
            "sector",
            "-",
        )

        st.markdown(
            _html(
                f"""
                <div
                    style="
                        background-color:#FFFFFF;
                        border:1px solid #E2E8F0;
                        border-radius:12px;
                        padding:14px;
                        min-height:220px;
                        display:flex;
                        flex-direction:column;
                        justify-content:space-between;
                    "
                >

                    <div
                        style="
                            font-size:13.5px;
                            font-weight:bold;
                            color:#64748B;
                            letter-spacing:0.5px;
                        "
                    >
                        DCF ASSUMPTIONS

                        <span
                            style="
                                font-size:11.5px;
                                color:#64748B;
                                font-weight:normal;
                            "
                        >
                            ({sector_name})
                        </span>
                    </div>

                    <div
                        style="
                            display:grid;
                            grid-template-columns:1fr 1fr;
                            gap:6px;
                            font-size:13px;
                            color:#475569;
                            margin:auto 0;
                        "
                    >

                        <div>
                            <span style="color:#64748B;">
                                WACC
                            </span>

                            <br>

                            <b style="color:#0F172A;">
                                {wacc_disp}
                            </b>
                        </div>

                        <div>
                            <span style="color:#64748B;">
                                Terminal Growth
                            </span>

                            <br>

                            <b style="color:#0F172A;">
                                {g_disp}
                            </b>
                        </div>

                        <div>
                            <span style="color:#64748B;">
                                FCF Growth (Yr 1)
                            </span>

                            <br>

                            <b style="color:#0F172A;">
                                {fcf_g_disp}
                            </b>
                        </div>

                        <div>
                            <span style="color:#64748B;">
                                Target P/E
                            </span>

                            <br>

                            <b style="color:#0F172A;">
                                18-22x (by sector)
                            </b>
                        </div>

                        <div>
                            <span style="color:#64748B;">
                                DCF Weight
                            </span>

                            <br>

                            <b style="color:#0F172A;">
                                55%
                            </b>
                        </div>

                        <div>
                            <span style="color:#64748B;">
                                P/E Weight
                            </span>

                            <br>

                            <b style="color:#0F172A;">
                                45%
                            </b>
                        </div>

                    </div>

                    <div
                        style="
                            font-size:11px;
                            color:#64748B;
                            border-top:1px solid #E2E8F0;
                            padding-top:6px;
                            margin-top:4px;
                        "
                    >
                        WACC/Growth ปรับตามกลุ่มอุตสาหกรรม
                        (ไม่ใช่ค่าคงที่เดียวทุกหุ้นแล้ว)
                        &bull;
                        FCF ฐานใช้ค่าเฉลี่ย 2 ปีล่าสุด
                    </div>

                </div>
                """
            ),
            unsafe_allow_html=True,
        )

    # ========================================================
    # HISTORICAL FAIR VALUE VS PRICE
    # ========================================================
    with r4_c2:

        st.markdown(
            _html(
                """
                <div
                    style="
                        background-color:#FFFFFF;
                        border:1px solid #E2E8F0;
                        border-radius:12px 12px 0 0;
                        padding:12px 16px 0 16px;
                    "
                >

                    <div
                        style="
                            font-size:13.5px;
                            font-weight:bold;
                            color:#64748B;
                            letter-spacing:0.5px;
                        "
                    >
                        HISTORICAL FAIR VALUE VS PRICE
                        (Actual, year-end 2023-2025)
                    </div>

                </div>
                """
            ),
            unsafe_allow_html=True,
        )

        # ====================================================
        # HISTORICAL DATA
        # ====================================================
        if (
            hasattr(ctx, "fair_value_yearly_df")
            and not ctx.fair_value_yearly_df.empty
        ):

            fv_hist = ctx.fair_value_yearly_df[
                ctx.fair_value_yearly_df["ticker"]
                == ctx.selected_ticker
            ].sort_values("year")

        else:
            fv_hist = pd.DataFrame()

        # ====================================================
        # HISTORICAL CHART
        # ====================================================
        if not fv_hist.empty:

            fig_hist_val = go.Figure()

            # FAIR VALUE
            fig_hist_val.add_trace(
                go.Scatter(
                    x=fv_hist["year"].astype(str),
                    y=fv_hist["fair_value"],
                    mode="lines+markers",
                    name="Fair Value",
                    line=dict(
                        color="#A855F7",
                        width=1.8,
                        dash="dash",
                    ),
                    marker=dict(
                        size=8,
                        color="#A855F7",
                    ),
                )
            )

            # ACTUAL PRICE
            fig_hist_val.add_trace(
                go.Scatter(
                    x=fv_hist["year"].astype(str),
                    y=fv_hist["price"],
                    mode="lines+markers",
                    name="Actual Price",
                    line=dict(
                        color="#38BDF8",
                        width=2,
                    ),
                    marker=dict(
                        size=9,
                        color="#38BDF8",
                    ),
                )
            )

            fig_hist_val.update_layout(
                height=150,
                margin=dict(
                    l=25,
                    r=15,
                    t=10,
                    b=20,
                ),
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#FFFFFF",
                yaxis=dict(
                    tickfont=dict(
                        size=11.5,
                        color="#64748B",
                    ),
                    gridcolor="#E2E8F0",
                    zeroline=False,
                ),
                xaxis=dict(
                    tickfont=dict(
                        size=11,
                        color="#64748B",
                    ),
                    gridcolor="#E2E8F0",
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.35,
                    xanchor="center",
                    x=0.5,
                    font=dict(
                        size=11.5,
                        color="#64748B",
                    ),
                ),
            )

            show_chart(
                fig_hist_val,
                key="fair_value_hist",
                expand_height=650,
            )

        else:

            st.info(
                "ไม่มีข้อมูลย้อนหลังเพียงพอ"
            )

    # ========================================================
    # FOOTER NAVIGATION
    # ========================================================
    render_nav_footer(
        "m2",
        prev_page=" Company Health",
        next_page=" Entry Timing",
    )
