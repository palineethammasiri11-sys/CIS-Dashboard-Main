"""
pages_content/fair_value.py
-----------------------
หน้า "Fair Value" ของ CIS Dashboard

วิธีทดสอบหน้านี้แบบเดี่ยว (ไม่ต้องรอทีมคนอื่น):
    streamlit run preview_my_page.py
    (แล้วเลือกโมดูลนี้จาก dropdown ในไฟล์ preview_my_page.py)

ข้อมูลที่ใช้ได้ใน ctx (ดูนิยามเต็มใน common.py -> class PageContext):
    ctx.selected_ticker, ctx.stock_info, ctx.stock_daily, ctx.fin_stock, ctx.sector_peers,
    ctx.scores_df, ctx.fin_df, ctx.feat_imp_df, ctx.backtest_df, ctx.risk_hist_df,
    ctx.health_yearly_df, ctx.fair_value_yearly_df,
    ctx.current_price, ctx.change_pct, ctx.change_val, ctx.change_color, ctx.change_sign, ctx.arrow_sign

ห้ามแก้ CSS ส่วนกลางหรือ helper function ใน common.py จากไฟล์นี้ — ถ้าจำเป็นต้องแก้ ให้แจ้ง Layout Lead ก่อน
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from common import fmt_mb, fmt_ratio, safe, show_chart, render_nav_footer, COMPANY_NAMES, SECTOR_MAP


def render(ctx):
    val_cur_price = ctx.current_price
    val_fair_value = safe(ctx.stock_info.get('fair_value'), val_cur_price * 1.1)
    val_mos = safe(ctx.stock_info.get('margin_of_safety'), 10.0)
    val_score = int(round(safe(ctx.stock_info.get('valuation_score'), 75)))
    val_status = "UNDERVALUED" if val_mos > 10 else ("OVERVALUED" if val_mos < -10 else "FAIR VALUE")
    val_color = "#10B981" if val_mos > 10 else ("#EF4444" if val_mos < -10 else "#F59E0B")
    val_rec_label = "ATTRACTIVE" if val_mos > 10 else ("FAIR" if val_mos >= -5 else "CAUTION")

    val_bear = safe(ctx.stock_info.get('dcf_fair_value'), val_fair_value * 0.9)
    val_base = val_fair_value
    val_bull = safe(ctx.stock_info.get('pe_fair_value'), val_fair_value * 1.1)

    # เรียงให้ bear <= base <= bull เสมอเพื่อความสวยงามของภาพ
    lo, hi = min(val_bear, val_bull), max(val_bear, val_bull)
    val_bear, val_bull = lo, hi

    # ============================================================
    # HEADER
    # ============================================================
    st.markdown(
        """<div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:18px;">
        <div>
            <div style="display:flex; align-items:center; gap:8px;">
                <h2 style="margin:0; font-size:23px; font-weight:bold; color:#0F172A; letter-spacing:0.5px;">
                    FAIR VALUE
                </h2>
            </div>
            <div style="font-size:16px; color:#64748B; margin-top:4px;">
                ประเมินมูลค่าที่เหมาะสมของหุ้นโดยใช้แบบจำลอง DCF ผสาน P/E Relative
            </div>
        </div>
        </div>""",
        unsafe_allow_html=True
    )

    # ============================================================
    # TOP ROW
    # รูปแบบ: Estimated Fair Value / Current Price /
    # Margin of Safety / Recommendation
    # ============================================================
    r1_c1, r1_c2, r1_c3, r1_c4 = st.columns([1.5, 1.0, 1.0, 1.0])

    val_stars = min(5, max(1, round(val_score / 20)))

    # ------------------------------------------------------------
    # ESTIMATED FAIR VALUE
    # ------------------------------------------------------------
    with r1_c1:
        st.markdown(
            f"""<div style="
                background:linear-gradient(135deg, #FFFFFF 0%, #F0FDFA 100%);
                border:2px solid {val_color};
                border-radius:12px;
                padding:14px 16px;
                min-height:145px;
                box-sizing:border-box;
                display:flex;
                flex-direction:column;
                justify-content:space-between;
            ">
                <div style="font-size:14px; font-weight:bold; color:#64748B; letter-spacing:0.5px;">
                    ESTIMATED FAIR VALUE
                </div>

                <div style="display:flex; align-items:baseline; gap:8px; margin-top:2px;">
                    <span style="
                        font-size:38px;
                        font-weight:800;
                        color:#0F172A;
                        line-height:1;
                        letter-spacing:-0.5px;
                    ">{val_base:.2f}</span>
                    <span style="font-size:17px; color:#64748B; font-weight:500;">THB</span>
                </div>

                <div style="font-size:13px; color:#64748B; margin-top:4px;">
                    (Blended: 55% DCF + 45% P/E)
                </div>
            </div>""",
            unsafe_allow_html=True
        )

    # ------------------------------------------------------------
    # CURRENT PRICE
    # ------------------------------------------------------------
    with r1_c2:
        st.markdown(
            f"""<div style="
                background-color:#FFFFFF;
                border:1px solid #E2E8F0;
                border-radius:12px;
                padding:14px;
                min-height:145px;
                box-sizing:border-box;
                display:flex;
                flex-direction:column;
                justify-content:space-between;
            ">
                <div style="font-size:14px; font-weight:bold; color:#64748B; letter-spacing:0.4px;">
                    CURRENT PRICE
                </div>

                <div>
                    <div style="
                        font-size:28px;
                        font-weight:800;
                        color:#0F172A;
                        line-height:1;
                    ">
                        {val_cur_price:.2f}
                        <span style="font-size:15px; color:#64748B; font-weight:500;">THB</span>
                    </div>

                    <div style="font-size:13px; color:#64748B; margin-top:6px;">
                        ({ctx.stock_info.get('latest_date','-')})
                    </div>
                </div>
            </div>""",
            unsafe_allow_html=True
        )

    # ------------------------------------------------------------
    # MARGIN OF SAFETY
    # ------------------------------------------------------------
    with r1_c3:
        mos_arrow = "▲" if val_mos >= 0 else "▼"

        st.markdown(
            f"""<div style="
                background-color:#FFFFFF;
                border:1px solid #E2E8F0;
                border-radius:12px;
                padding:14px;
                min-height:145px;
                box-sizing:border-box;
                display:flex;
                flex-direction:column;
                justify-content:space-between;
            ">
                <div style="font-size:14px; font-weight:bold; color:#64748B; letter-spacing:0.4px;">
                    MARGIN OF SAFETY
                </div>

                <div>
                    <div style="
                        font-size:30px;
                        font-weight:800;
                        color:{val_color};
                        line-height:1;
                    ">
                        {val_mos:.1f}%
                        <span style="font-size:15px; vertical-align:middle;">{mos_arrow}</span>
                    </div>

                    <div style="font-size:13px; color:#64748B; margin-top:7px;">
                        (vs. fair value)
                    </div>
                </div>
            </div>""",
            unsafe_allow_html=True
        )

    # ------------------------------------------------------------
    # RECOMMENDATION
    # ------------------------------------------------------------
    with r1_c4:
        st.markdown(
            f"""<div style="
                background-color:#FFFFFF;
                border:1px solid #E2E8F0;
                border-radius:12px;
                padding:14px;
                min-height:145px;
                box-sizing:border-box;
                display:flex;
                flex-direction:column;
                justify-content:space-between;
            ">
                <div style="font-size:14px; font-weight:bold; color:#64748B; letter-spacing:0.4px;">
                    RECOMMENDATION
                </div>

                <div style="text-align:center; margin-top:4px;">
                    <div style="
                        display:inline-block;
                        background:{val_color};
                        color:#FFFFFF;
                        border-radius:18px;
                        padding:7px 30px;
                        min-width:95px;
                        font-size:18px;
                        font-weight:800;
                        line-height:1;
                        box-sizing:border-box;
                    ">
                        {val_rec_label}
                    </div>

                    <div style="
                        font-size:13px;
                        color:#64748B;
                        margin-top:8px;
                    ">
                        ราคาเหมาะสม
                    </div>
                </div>
            </div>""",
            unsafe_allow_html=True
        )

    # ============================================================
    # SECOND ROW
    # Fair Value Range / Confidence / Summary Score
    # ============================================================
    st.markdown("<div style='margin-top:14px;'></div>", unsafe_allow_html=True)

    r2_c1, r2_c2, r2_c3 = st.columns([2.4, 0.8, 0.8])

    # ------------------------------------------------------------
    # FAIR VALUE RANGE
    # ------------------------------------------------------------
    with r2_c1:
        range_min = min(val_bear, val_cur_price, val_base, val_bull)
        range_max = max(val_bear, val_cur_price, val_base, val_bull)

        range_padding = max((range_max - range_min) * 0.08, 1)
        display_min = range_min - range_padding
        display_max = range_max + range_padding

        range_span = max(display_max - display_min, 1)

        current_pct = ((val_cur_price - display_min) / range_span) * 100
        fair_pct = ((val_base - display_min) / range_span) * 100

        current_pct = max(4, min(96, current_pct))
        fair_pct = max(4, min(96, fair_pct))

        st.markdown(
            f"""<div style="
                background-color:#FFFFFF;
                border:1px solid #E2E8F0;
                border-radius:12px;
                padding:14px 16px;
                min-height:165px;
                box-sizing:border-box;
                position:relative;
            ">

                <div style="
                    font-size:14px;
                    font-weight:bold;
                    color:#64748B;
                    letter-spacing:0.5px;
                    margin-bottom:10px;
                ">
                    ▣ &nbsp; FAIR VALUE RANGE — DCF vs P/E RELATIVE
                </div>

                <!-- labels above line -->
                <div style="
                    position:relative;
                    height:42px;
                    margin:0 4px;
                ">

                    <div style="
                        position:absolute;
                        left:{current_pct}%;
                        transform:translateX(-50%);
                        top:0;
                        background:#F8FAFC;
                        border:1px solid #3B82F6;
                        border-radius:7px;
                        padding:4px 9px;
                        text-align:center;
                        white-space:nowrap;
                    ">
                        <div style="font-size:11px; color:#3B82F6; line-height:1.1;">
                            Current Price
                        </div>
                        <div style="font-size:14px; color:#2563EB; font-weight:bold; line-height:1.2;">
                            {val_cur_price:.2f} <span style="font-size:10px;">THB</span>
                        </div>
                    </div>

                    <div style="
                        position:absolute;
                        left:{fair_pct}%;
                        transform:translateX(-50%);
                        top:0;
                        background:#FFFBEB;
                        border:1px solid #F59E0B;
                        border-radius:7px;
                        padding:4px 9px;
                        text-align:center;
                        white-space:nowrap;
                    ">
                        <div style="font-size:11px; color:#D97706; line-height:1.1;">
                            Blended Fair Value
                        </div>
                        <div style="font-size:14px; color:#D97706; font-weight:bold; line-height:1.2;">
                            {val_base:.2f} <span style="font-size:10px;">THB</span>
                        </div>
                    </div>

                </div>

                <!-- range line -->
                <div style="
                    position:relative;
                    height:12px;
                    margin:0 6px;
                ">

                    <div style="
                        position:absolute;
                        left:0;
                        right:0;
                        top:2px;
                        height:9px;
                        border-radius:6px;
                        background:linear-gradient(
                            90deg,
                            #34D399 0%,
                            #38BDF8 28%,
                            #F59E0B 60%,
                            #A855F7 100%
                        );
                    "></div>

                    <!-- Current price marker -->
                    <div style="
                        position:absolute;
                        left:{current_pct}%;
                        top:-4px;
                        transform:translateX(-50%);
                        width:14px;
                        height:14px;
                        border-radius:50%;
                        background:#3B82F6;
                        border:2px solid #FFFFFF;
                        box-shadow:0 0 0 1px #3B82F6;
                        box-sizing:border-box;
                    "></div>

                    <!-- Fair value marker -->
                    <div style="
                        position:absolute;
                        left:{fair_pct}%;
                        top:-4px;
                        transform:translateX(-50%);
                        width:14px;
                        height:14px;
                        border-radius:50%;
                        background:#F59E0B;
                        border:2px solid #FFFFFF;
                        box-shadow:0 0 0 1px #F59E0B;
                        box-sizing:border-box;
                    "></div>

                </div>

                <!-- min max -->
                <div style="
                    display:flex;
                    justify-content:space-between;
                    align-items:flex-start;
                    margin:8px 2px 0 2px;
                ">
                    <div>
                        <div style="font-size:11px; color:#64748B;">Min</div>
                        <div style="font-size:15px; color:#334155; font-weight:bold;">
                            {val_bear:.2f}
                        </div>
                        <div style="font-size:10px; color:#64748B;">THB</div>
                    </div>

                    <div style="text-align:right;">
                        <div style="font-size:11px; color:#64748B;">Max</div>
                        <div style="font-size:15px; color:#334155; font-weight:bold;">
                            {val_bull:.2f}
                        </div>
                        <div style="font-size:10px; color:#64748B;">THB</div>
                    </div>
                </div>

            </div>""",
            unsafe_allow_html=True
        )

    # ------------------------------------------------------------
    # CONFIDENCE LEVEL
    # ------------------------------------------------------------
    with r2_c2:
        conf = "High" if abs(val_mos) > 15 else ("Medium" if abs(val_mos) > 5 else "Low")

        conf_score = (
            80 if conf == "High"
            else 60 if conf == "Medium"
            else 35
        )

        conf_color = (
            "#10B981" if conf == "High"
            else "#F59E0B" if conf == "Medium"
            else "#EF4444"
        )

        st.markdown(
            f"""<div style="
                background-color:#FFFFFF;
                border:1px solid #E2E8F0;
                border-radius:12px;
                padding:14px;
                min-height:165px;
                box-sizing:border-box;
                text-align:center;
            ">

                <div style="
                    font-size:14px;
                    font-weight:bold;
                    color:#64748B;
                    letter-spacing:0.4px;
                    text-align:left;
                ">
                    CONFIDENCE LEVEL
                </div>

                <div style="
                    width:92px;
                    height:52px;
                    margin:20px auto 0;
                    border-radius:92px 92px 0 0;
                    border:8px solid #E2E8F0;
                    border-bottom:0;
                    position:relative;
                    box-sizing:border-box;
                ">
                    <div style="
                        position:absolute;
                        left:-8px;
                        top:-8px;
                        width:92px;
                        height:52px;
                        border-radius:92px 92px 0 0;
                        border:8px solid transparent;
                        border-top-color:{conf_color};
                        border-left-color:{conf_color};
                        transform:rotate({-25 + conf_score * 1.35}deg);
                        box-sizing:border-box;
                    "></div>
                </div>

                <div style="
                    color:{conf_color};
                    font-size:17px;
                    font-weight:bold;
                    margin-top:-3px;
                ">
                    {conf.upper()}
                </div>

                <div style="
                    color:#64748B;
                    font-size:12px;
                    margin-top:3px;
                ">
                    ({conf_score}/100)
                </div>

            </div>""",
            unsafe_allow_html=True
        )

    # ------------------------------------------------------------
    # FAIR VALUE SUMMARY SCORE
    # ------------------------------------------------------------
    with r2_c3:
        score_color = val_color

        st.markdown(
            f"""<div style="
                background-color:#FFFFFF;
                border:1px solid #E2E8F0;
                border-radius:12px;
                padding:14px;
                min-height:165px;
                box-sizing:border-box;
                text-align:center;
            ">

                <div style="
                    font-size:13px;
                    font-weight:bold;
                    color:#64748B;
                    letter-spacing:0.35px;
                    text-align:left;
                    line-height:1.2;
                ">
                    ★ &nbsp; FAIR VALUE<br>
                    <span style="padding-left:19px;">SUMMARY SCORE</span>
                </div>

                <div style="
                    width:70px;
                    height:70px;
                    margin:10px auto 4px;
                    border-radius:50%;
                    background:conic-gradient(
                        {score_color} 0% {val_score}%,
                        #E2E8F0 {val_score}% 100%
                    );
                    display:flex;
                    align-items:center;
                    justify-content:center;
                ">
                    <div style="
                        width:54px;
                        height:54px;
                        border-radius:50%;
                        background:#FFFFFF;
                        display:flex;
                        flex-direction:column;
                        align-items:center;
                        justify-content:center;
                    ">
                        <div style="
                            font-size:19px;
                            font-weight:bold;
                            color:#0F172A;
                            line-height:1;
                        ">
                            {val_score}
                        </div>
                        <div style="
                            font-size:10px;
                            color:#64748B;
                            margin-top:2px;
                        ">
                            /100
                        </div>
                    </div>
                </div>

                <div style="
                    color:{score_color};
                    font-size:12px;
                    font-weight:bold;
                ">
                    {val_status.title()}
                </div>

            </div>""",
            unsafe_allow_html=True
        )

    # ============================================================
    # EXISTING DETAIL SECTION
    # ============================================================
    st.markdown("<div style='margin-top:22px;'></div>", unsafe_allow_html=True)

    r3_c1, r3_c2, r3_c3 = st.columns([1.3, 1.3, 1.4])

    # ------------------------------------------------------------
    # FAIR VALUE RANGE DETAIL
    # ------------------------------------------------------------
    with r3_c1:
        st.markdown(
            f"""<div style="
                background-color:#FFFFFF;
                border:1px solid #E2E8F0;
                border-radius:12px;
                padding:14px;
                min-height:315px;
                display:flex;
                flex-direction:column;
                justify-content:space-between;
            ">
                <div style="
                    font-size:15px;
                    font-weight:bold;
                    color:#64748B;
                    letter-spacing:0.5px;
                ">
                    FAIR VALUE RANGE — DCF vs P/E RELATIVE
                </div>

                <div style="
                    display:grid;
                    grid-template-columns:1fr 1.1fr 1fr;
                    gap:6px;
                    margin-top:6px;
                ">

                    <div style="
                        background:#F8FAFC;
                        border:1px solid #E2E8F0;
                        border-radius:8px;
                        padding:8px 4px;
                        text-align:center;
                    ">
                        <div style="color:#EF4444; font-size:14px; font-weight:bold;">
                            Lower Estimate
                        </div>
                        <div style="color:#64748B; font-size:13px;">
                            Min(DCF, P/E)
                        </div>
                        <div style="color:#0F172A; font-size:17px; font-weight:bold; margin-top:4px;">
                            {val_bear:.2f}
                            <span style="font-size:13px; color:#64748B;">THB</span>
                        </div>
                    </div>

                    <div style="
                        background:#FFFBEB;
                        border:1.5px solid #F59E0B;
                        border-radius:8px;
                        padding:8px 4px;
                        text-align:center;
                    ">
                        <div style="color:#F59E0B; font-size:14px; font-weight:bold;">
                            Blended Fair Value
                        </div>
                        <div style="color:#64748B; font-size:13px;">
                            55% DCF + 45% P/E
                        </div>
                        <div style="color:#0F172A; font-size:17.5px; font-weight:bold; margin-top:4px;">
                            {val_base:.2f}
                            <span style="font-size:13px; color:#64748B;">THB</span>
                        </div>
                    </div>

                    <div style="
                        background:#F8FAFC;
                        border:1px solid #E2E8F0;
                        border-radius:8px;
                        padding:8px 4px;
                        text-align:center;
                    ">
                        <div style="color:#10B981; font-size:14px; font-weight:bold;">
                            Upper Estimate
                        </div>
                        <div style="color:#64748B; font-size:13px;">
                            Max(DCF, P/E)
                        </div>
                        <div style="color:#0F172A; font-size:17px; font-weight:bold; margin-top:4px;">
                            {val_bull:.2f}
                            <span style="font-size:13px; color:#64748B;">THB</span>
                        </div>
                    </div>

                </div>

                <div style="
                    background:rgba(16,185,129,0.08);
                    border-radius:6px;
                    padding:6px 8px;
                    display:flex;
                    align-items:flex-start;
                    gap:6px;
                    margin-top:10px;
                ">
                    <span style="color:#10B981; font-size:15px;">✔</span>

                    <div style="
                        font-size:13px;
                        color:#475569;
                        line-height:1.3;
                    ">
                        <b>
                            DCF Fair Value: {safe(ctx.stock_info.get('dcf_fair_value')):.2f} THB
                            &nbsp;|&nbsp;
                            P/E Fair Value: {safe(ctx.stock_info.get('pe_fair_value')):.2f} THB
                        </b>
                        <br>

                        <span style="color:#64748B;">
                            คำนวณจากงบการเงินปีล่าสุด
                            (FY{int(ctx.fin_stock['year'].max()) if not ctx.fin_stock.empty else '-'})
                            เทียบราคาตลาดปัจจุบัน {val_cur_price:.2f} THB
                        </span>
                    </div>
                </div>
            </div>""",
            unsafe_allow_html=True
        )

    # ------------------------------------------------------------
    # VALUATION DRIVERS
    # ------------------------------------------------------------
    with r3_c2:
        st.markdown(
            f"""<div style="
                background-color:#FFFFFF;
                border:1px solid #E2E8F0;
                border-radius:12px;
                padding:14px;
                min-height:315px;
                display:flex;
                flex-direction:column;
                justify-content:space-between;
            ">

                <div style="
                    font-size:15px;
                    font-weight:bold;
                    color:#64748B;
                    letter-spacing:0.5px;
                ">
                    VALUATION DRIVERS ({ctx.selected_ticker})
                </div>

                <div style="
                    font-size:14px;
                    color:#475569;
                    line-height:1.45;
                    display:flex;
                    flex-direction:column;
                    gap:6px;
                    margin:auto 0;
                ">

                    <div style="display:flex; gap:6px;">
                        <span style="color:#10B981;">✔</span>
                        <div>
                            <b>Fair Value (Blended): {val_base:.2f} THB</b>
                            <br>
                            <span style="color:#64748B; font-size:13px;">
                                ประเมินแบบผสมผสาน DCF + Relative P/E
                            </span>
                        </div>
                    </div>

                    <div style="display:flex; gap:6px;">
                        <span style="color:#10B981;">✔</span>
                        <div>
                            <b>Margin of Safety: {val_mos:.1f}%</b>
                            <br>
                            <span style="color:#64748B; font-size:13px;">
                                ส่วนต่างความปลอดภัยจากราคาตลาดปัจจุบัน
                            </span>
                        </div>
                    </div>

                    <div style="display:flex; gap:6px;">
                        <span style="color:#10B981;">✔</span>
                        <div>
                            <b>
                                P/E Ratio ปัจจุบัน:
                                {fmt_ratio(ctx.stock_info.get('pe_ratio'), suffix='')} เท่า
                            </b>
                            <br>
                            <span style="color:#64748B; font-size:13px;">
                                เทียบ EPS ล่าสุด {ctx.stock_info.get('eps','-')} บาท/หุ้น
                            </span>
                        </div>
                    </div>

                    <div style="display:flex; gap:6px;">
                        <span style="color:#10B981;">✔</span>
                        <div>
                            <b>สถานะมูลค่า: {val_status}</b>
                            <br>
                            <span style="color:#64748B; font-size:13px;">
                                ระดับความน่าดึงดูดเชิงมูลค่าพื้นฐาน
                            </span>
                        </div>
                    </div>

                </div>
            </div>""",
            unsafe_allow_html=True
        )

    # ------------------------------------------------------------
    # SCORE BY DIMENSION
    # ------------------------------------------------------------
    with r3_c3:
        safety_score = int(min(100, max(20, int(val_mos + 50))))

        st.markdown(
            f"""<div style="
                background-color:#FFFFFF;
                border:1px solid #E2E8F0;
                border-radius:12px;
                padding:14px;
                min-height:315px;
                display:flex;
                flex-direction:column;
                justify-content:space-between;
            ">

                <div style="
                    font-size:15px;
                    font-weight:bold;
                    color:#64748B;
                    letter-spacing:0.5px;
                ">
                    FAIR VALUE SCORE BY DIMENSION
                </div>

                <div style="
                    display:flex;
                    flex-direction:column;
                    gap:10px;
                    margin:auto 0;
                ">

                    <div>
                        <div style="
                            display:flex;
                            justify-content:space-between;
                            font-size:14px;
                            color:#475569;
                            margin-bottom:3px;
                        ">
                            <span>📊 Relative Valuation (P/E)</span>
                            <span style="font-weight:bold; color:#0F172A;">
                                {val_score}
                                <span style="font-size:13px; color:#64748B;">/100</span>
                            </span>
                        </div>

                        <div style="
                            background:#E2E8F0;
                            height:9px;
                            border-radius:4px;
                            overflow:hidden;
                        ">
                            <div style="
                                background:{val_color};
                                width:{val_score}%;
                                height:100%;
                            "></div>
                        </div>
                    </div>

                    <div>
                        <div style="
                            display:flex;
                            justify-content:space-between;
                            font-size:14px;
                            color:#475569;
                            margin-bottom:3px;
                        ">
                            <span>🎯 Intrinsic Valuation (DCF)</span>
                            <span style="font-weight:bold; color:#0F172A;">
                                {val_score}
                                <span style="font-size:13px; color:#64748B;">/100</span>
                            </span>
                        </div>

                        <div style="
                            background:#E2E8F0;
                            height:9px;
                            border-radius:4px;
                            overflow:hidden;
                        ">
                            <div style="
                                background:{val_color};
                                width:{val_score}%;
                                height:100%;
                            "></div>
                        </div>
                    </div>

                    <div>
                        <div style="
                            display:flex;
                            justify-content:space-between;
                            font-size:14px;
                            color:#475569;
                            margin-bottom:3px;
                        ">
                            <span>🛡️ Margin of Safety</span>
                            <span style="font-weight:bold; color:#0F172A;">
                                {safety_score}
                                <span style="font-size:13px; color:#64748B;">/100</span>
                            </span>
                        </div>

                        <div style="
                            background:#E2E8F0;
                            height:9px;
                            border-radius:4px;
                            overflow:hidden;
                        ">
                            <div style="
                                background:{val_color};
                                width:{safety_score}%;
                                height:100%;
                            "></div>
                        </div>
                    </div>

                </div>

                <div style="
                    display:flex;
                    justify-content:space-between;
                    align-items:center;
                    border-top:1px solid #E2E8F0;
                    padding-top:8px;
                ">
                    <span style="
                        font-size:14px;
                        font-weight:bold;
                        color:#475569;
                    ">
                        OVERALL FAIR VALUE SCORE
                    </span>

                    <span style="
                        font-size:19px;
                        font-weight:bold;
                        color:{val_color};
                    ">
                        {val_score}
                        <span style="font-size:14px; color:#64748B;">/100</span>
                    </span>
                </div>

            </div>""",
            unsafe_allow_html=True
        )

    # ============================================================
    # DETAIL BREAKDOWN
    # ============================================================
    st.markdown("<div style='margin-top:22px;'></div>", unsafe_allow_html=True)

    st.markdown(
        """<div style="
            font-size:15px;
            font-weight:bold;
            color:#64748B;
            letter-spacing:0.5px;
            margin-bottom:8px;
        ">
            DETAIL BREAKDOWN
        </div>""",
        unsafe_allow_html=True
    )

    d_c1, d_c2, d_c3, d_c4 = st.columns(4)

    # ------------------------------------------------------------
    # RELATIVE VALUATION
    # ------------------------------------------------------------
    with d_c1:
        st.markdown(
            f"""<div style="
                background-color:#FFFFFF;
                border:1px solid #E2E8F0;
                border-radius:10px;
                padding:12px;
                min-height:190px;
                display:flex;
                flex-direction:column;
                justify-content:space-between;
            ">
                <div>
                    <div style="
                        font-size:14px;
                        font-weight:bold;
                        color:#475569;
                    ">
                        RELATIVE VALUATION (P/E)
                    </div>

                    <table style="
                        width:100%;
                        font-size:14px;
                        color:#475569;
                        border-collapse:collapse;
                        margin-top:6px;
                    ">
                        <tr style="
                            border-bottom:1px solid #E2E8F0;
                            color:#64748B;
                            font-size:13px;
                        ">
                            <th style="text-align:left; padding:2px 0;">Metric</th>
                            <th>Value</th>
                        </tr>

                        <tr style="border-bottom:1px solid #E2E8F0;">
                            <td style="padding:3px 0;">P/E Ratio ปัจจุบัน</td>
                            <td>{fmt_ratio(ctx.stock_info.get('pe_ratio'))}</td>
                        </tr>

                        <tr>
                            <td style="padding:3px 0;">P/E Fair Value</td>
                            <td>{safe(ctx.stock_info.get('pe_fair_value')):.2f} THB</td>
                        </tr>
                    </table>
                </div>
            </div>""",
            unsafe_allow_html=True
        )

    # ------------------------------------------------------------
    # DCF
    # ------------------------------------------------------------
    with d_c2:
        st.markdown(
            f"""<div style="
                background-color:#FFFFFF;
                border:1px solid #E2E8F0;
                border-radius:10px;
                padding:12px;
                min-height:190px;
                display:flex;
                flex-direction:column;
                justify-content:space-between;
            ">
                <div>
                    <div style="
                        font-size:14px;
                        font-weight:bold;
                        color:#475569;
                    ">
                        INTRINSIC VALUATION (DCF)
                    </div>

                    <table style="
                        width:100%;
                        font-size:14px;
                        color:#475569;
                        border-collapse:collapse;
                        margin-top:6px;
                    ">
                        <tr style="
                            border-bottom:1px solid #E2E8F0;
                            color:#64748B;
                            font-size:13px;
                        ">
                            <th style="text-align:left; padding:2px 0;">Metric</th>
                            <th>Value</th>
                        </tr>

                        <tr style="border-bottom:1px solid #E2E8F0;">
                            <td style="padding:3px 0;">WACC</td>
                            <td>
                                {fmt_ratio(
                                    ctx.stock_info.get('wacc_used'),
                                    suffix="%",
                                    decimals=1
                                )}
                            </td>
                        </tr>

                        <tr>
                            <td style="padding:3px 0;">DCF Fair Value</td>
                            <td>{safe(ctx.stock_info.get('dcf_fair_value')):.2f} THB</td>
                        </tr>
                    </table>
                </div>
            </div>""",
            unsafe_allow_html=True
        )

    # ------------------------------------------------------------
    # PRICE COMPARISON
    # ------------------------------------------------------------
    with d_c3:
        st.markdown(
            f"""<div style="
                background-color:#FFFFFF;
                border:1px solid #E2E8F0;
                border-radius:10px;
                padding:12px;
                min-height:190px;
                display:flex;
                flex-direction:column;
                justify-content:space-between;
            ">
                <div>
                    <div style="
                        font-size:14px;
                        font-weight:bold;
                        color:#475569;
                    ">
                        PRICE COMPARISON
                    </div>

                    <table style="
                        width:100%;
                        font-size:14px;
                        color:#475569;
                        border-collapse:collapse;
                        margin-top:6px;
                    ">
                        <tr style="border-bottom:1px solid #E2E8F0;">
                            <td style="padding:3px 0;">Current</td>
                            <td>{val_cur_price:.2f}</td>
                        </tr>

                        <tr style="border-bottom:1px solid #E2E8F0;">
                            <td style="padding:3px 0;">Fair Value</td>
                            <td>{val_base:.2f}</td>
                        </tr>

                        <tr>
                            <td style="padding:3px 0;">Difference</td>
                            <td>{(val_base - val_cur_price):+.2f}</td>
                        </tr>
                    </table>
                </div>
            </div>""",
            unsafe_allow_html=True
        )

    # ------------------------------------------------------------
    # MARGIN OF SAFETY
    # ------------------------------------------------------------
    with d_c4:
        st.markdown(
            f"""<div style="
                background-color:#FFFFFF;
                border:1px solid #E2E8F0;
                border-radius:10px;
                padding:12px;
                min-height:190px;
                display:flex;
                flex-direction:column;
                justify-content:space-between;
            ">
                <div>
                    <div style="
                        font-size:14px;
                        font-weight:bold;
                        color:#475569;
                    ">
                        MARGIN OF SAFETY
                    </div>

                    <table style="
                        width:100%;
                        font-size:14px;
                        color:#475569;
                        border-collapse:collapse;
                        margin-top:6px;
                    ">
                        <tr>
                            <td style="padding:3px 0;">Margin of Safety</td>
                            <td style="
                                color:{val_color};
                                font-weight:bold;
                            ">
                                {val_mos:.1f}%
                            </td>
                        </tr>
                    </table>
                </div>
            </div>""",
            unsafe_allow_html=True
        )

    # ============================================================
    # DCF ASSUMPTIONS + HISTORICAL
    # ============================================================
    st.markdown("<div style='margin-top:22px;'></div>", unsafe_allow_html=True)

    r4_c1, r4_c2 = st.columns([1.3, 1.7])

    # ------------------------------------------------------------
    # DCF ASSUMPTIONS
    # ------------------------------------------------------------
    with r4_c1:
        wacc_disp = fmt_ratio(
            ctx.stock_info.get('wacc_used'),
            suffix="%",
            decimals=1
        )

        g_disp = fmt_ratio(
            ctx.stock_info.get('terminal_growth_used'),
            suffix="%",
            decimals=1
        )

        fcf_g_disp = fmt_ratio(
            ctx.stock_info.get('fcf_growth_assumed'),
            suffix="%",
            decimals=1
        )

        st.markdown(
            f"""<div style="
                background-color:#FFFFFF;
                border:1px solid #E2E8F0;
                border-radius:12px;
                padding:14px;
                min-height:220px;
                display:flex;
                flex-direction:column;
                justify-content:space-between;
            ">
                <div style="
                    font-size:14px;
                    font-weight:bold;
                    color:#64748B;
                    letter-spacing:0.5px;
                ">
                    DCF ASSUMPTIONS

                    <span style="
                        font-size:12px;
                        color:#64748B;
                        font-weight:normal;
                    ">
                        ({ctx.stock_info.get('sector','-')})
                    </span>
                </div>

                <div style="
                    display:grid;
                    grid-template-columns:1fr 1fr;
                    gap:6px;
                    font-size:14px;
                    color:#475569;
                    margin:auto 0;
                ">
                    <div>
                        <span style="color:#64748B;">WACC</span><br>
                        <b style="color:#0F172A;">{wacc_disp}</b>
                    </div>

                    <div>
                        <span style="color:#64748B;">Terminal Growth</span><br>
                        <b style="color:#0F172A;">{g_disp}</b>
                    </div>

                    <div>
                        <span style="color:#64748B;">FCF Growth (Yr 1)</span><br>
                        <b style="color:#0F172A;">{fcf_g_disp}</b>
                    </div>

                    <div>
                        <span style="color:#64748B;">Target P/E</span><br>
                        <b style="color:#0F172A;">18-22x (by sector)</b>
                    </div>

                    <div>
                        <span style="color:#64748B;">DCF Weight</span><br>
                        <b style="color:#0F172A;">55%</b>
                    </div>

                    <div>
                        <span style="color:#64748B;">P/E Weight</span><br>
                        <b style="color:#0F172A;">45%</b>
                    </div>
                </div>

                <div style="
                    font-size:12px;
                    color:#64748B;
                    border-top:1px solid #E2E8F0;
                    padding-top:6px;
                    margin-top:4px;
                ">
                    WACC/Growth ปรับตามกลุ่มอุตสาหกรรม
                    (ไม่ใช่ค่าคงที่เดียวทุกหุ้นแล้ว)
                    &bull; FCF ฐานใช้ค่าเฉลี่ย 2 ปีล่าสุด
                </div>
            </div>""",
            unsafe_allow_html=True
        )

    # ------------------------------------------------------------
    # HISTORICAL FAIR VALUE VS PRICE
    # ------------------------------------------------------------
    with r4_c2:
        st.markdown(
            """<div style="
                background-color:#FFFFFF;
                border:1px solid #E2E8F0;
                border-radius:12px 12px 0 0;
                padding:12px 16px 0 16px;
            ">
                <div style="
                    font-size:14px;
                    font-weight:bold;
                    color:#64748B;
                    letter-spacing:0.5px;
                ">
                    HISTORICAL FAIR VALUE VS PRICE
                    (Actual, year-end 2023-2025)
                </div>
            </div>""",
            unsafe_allow_html=True
        )

        fv_hist = (
            ctx.fair_value_yearly_df[
                ctx.fair_value_yearly_df['ticker'] == ctx.selected_ticker
            ].sort_values('year')
            if not ctx.fair_value_yearly_df.empty
            else pd.DataFrame()
        )

        if not fv_hist.empty:
            fig_hist_val = go.Figure()

            fig_hist_val.add_trace(
                go.Scatter(
                    x=fv_hist['year'].astype(str),
                    y=fv_hist['fair_value'],
                    mode='lines+markers',
                    name='Fair Value',
                    line=dict(
                        color='#A855F7',
                        width=1.8,
                        dash='dash'
                    )
                )
            )

            fig_hist_val.add_trace(
                go.Scatter(
                    x=fv_hist['year'].astype(str),
                    y=fv_hist['price'],
                    mode='lines+markers',
                    name='Actual Price',
                    line=dict(
                        color='#38BDF8',
                        width=2
                    ),
                    marker=dict(
                        size=9,
                        color='#38BDF8'
                    )
                )
            )

            fig_hist_val.update_layout(
                height=150,
                margin=dict(
                    l=25,
                    r=15,
                    t=10,
                    b=20
                ),
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#FFFFFF",

                yaxis=dict(
                    tickfont=dict(
                        size=12,
                        color="#64748B"
                    ),
                    gridcolor="#E2E8F0",
                    zeroline=False
                ),

                xaxis=dict(
                    tickfont=dict(
                        size=12,
                        color="#64748B"
                    ),
                    gridcolor="#E2E8F0"
                ),

                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.35,
                    xanchor="center",
                    x=0.5,
                    font=dict(
                        size=12,
                        color="#64748B"
                    )
                )
            )

            show_chart(
                fig_hist_val,
                key="fair_value_hist",
                expand_height=650
            )

        else:
            st.info("ไม่มีข้อมูลย้อนหลังเพียงพอ")

    # ============================================================
    # NAVIGATION
    # ============================================================
    render_nav_footer(
        "m2",
        prev_page=" Company Health",
        next_page=" Entry Timing"
    )
