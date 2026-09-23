"""
pages_content/overview.py
-------------------------
หน้า "Overview" ของ CIS Dashboard
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from common import (
    fmt_mb, fmt_ratio, safe, show_chart, render_nav_footer,
    COMPANY_NAMES, SECTOR_MAP
)


def render(ctx):

    st.html("""
    <div style="margin-bottom:20px;">
        <div style="font-size:23px;font-weight:700;color:#0F172A;letter-spacing:0.3px;">
            OVERVIEW DASHBOARD
        </div>
        <div style="font-size:15px;color:#64748B;margin-top:4px;">
            ภาพรวมข้อมูลและการวิเคราะห์เพื่อสนับสนุนการตัดสินใจลงทุน
        </div>
    </div>
    """)

    m1_s = int(round(safe(ctx.stock_info.get('health_score'), 50)))
    m2_s = int(round(safe(ctx.stock_info.get('valuation_score'), 50)))
    m3_s = int(round(safe(ctx.stock_info.get('timing_score'), 50)))
    m4_s = int(round(safe(ctx.stock_info.get('ai_score'), 50)))
    m5_s = int(round(safe(ctx.stock_info.get('risk_score'), 50)))
    m6_s = int(round(safe(ctx.stock_info.get('industry_score'), 50)))
    n_sector = len(ctx.sector_peers)

    if m1_s >= 70:
        m1_badge, m1_desc = "EXCELLENT", "ฐานะการเงินแข็งแกร่งและมีคุณภาพทางธุรกิจที่ดี"
    elif m1_s >= 45:
        m1_badge, m1_desc = "MODERATE", "ฐานะการเงินมั่นคงและมีสภาพคล่องอยู่ในระดับเหมาะสม"
    else:
        m1_badge, m1_desc = "WEAK", "มีความเสี่ยงจากภาระหนี้หรือแรงกดดันด้านอัตรากำไร"

    if m2_s >= 70:
        m2_badge, m2_desc = "UNDERVALUED", "ราคาหุ้นน่าสนใจเมื่อเทียบกับมูลค่าพื้นฐาน"
    elif m2_s >= 45:
        m2_badge, m2_desc = "FAIR VALUE", "ราคาซื้อขายอยู่ใกล้เคียงกับมูลค่าพื้นฐาน"
    else:
        m2_badge, m2_desc = "OVERVALUED", "ราคาหุ้นสูงกว่ามูลค่าพื้นฐานที่ประเมินได้"

    if m3_s >= 67:
        m3_badge, m3_desc = "BULLISH", "แนวโน้มราคาเป็นขาขึ้นและมีโมเมนตัมแข็งแกร่ง"
    elif m3_s >= 34:
        m3_badge, m3_desc = "NEUTRAL", "ราคากำลังแกว่งตัวใกล้แนวรับสำคัญ"
    else:
        m3_badge, m3_desc = "BEARISH", "แนวโน้มเป็นขาลงและมีความเสี่ยงต่อการปรับตัวลดลง"

    if m4_s >= 70:
        m4_badge, m4_desc = "POSITIVE", "โมเดล AI ประเมินโอกาสปรับตัวขึ้นในระดับที่ดี"
    elif m4_s >= 50:
        m4_badge, m4_desc = "NEUTRAL", "โมเดล AI คาดว่าราคามีแนวโน้มเคลื่อนไหวในกรอบ"
    else:
        m4_badge, m4_desc = "CAUTION", "โมเดล AI ประเมินโอกาสปรับตัวขึ้นในระดับต่ำ"

    if m5_s >= 65:
        m5_badge, m5_desc = "LOW RISK", "มีความสามารถในการรับมือความผันผวนและความเสี่ยงได้ดี"
    elif m5_s >= 45:
        m5_badge, m5_desc = "MODERATE", "มีระดับความเสี่ยงโดยรวมอยู่ในระดับสมดุล"
    else:
        m5_badge, m5_desc = "HIGH RISK", "มีความผันผวนสูงและความเสี่ยงจากการปรับตัวลงแรง"

    if m6_s >= 70:
        m6_badge, m6_desc = "OUTPERFORM", "มีผลการดำเนินงานโดดเด่นเมื่อเทียบกับบริษัทในกลุ่ม"
    elif m6_s >= 45:
        m6_badge, m6_desc = "PARITY", "มีผลการดำเนินงานใกล้เคียงกับค่ากลางของกลุ่ม"
    else:
        m6_badge, m6_desc = "LAGGING", "มีผลการดำเนินงานต่ำกว่าบริษัทอื่นในกลุ่ม"
    def score_color(score, green_at, yellow_at):
        if score >= green_at: return "#10B981"
        elif score >= yellow_at: return "#F59E0B"
        return "#EF4444"

    def score_bg(score, green_at, yellow_at):
        if score >= green_at: return "rgba(16,185,129,0.20)"
        elif score >= yellow_at: return "rgba(245,158,11,0.20)"
        return "rgba(239,68,68,0.20)"

    overall = safe(ctx.stock_info.get('overall_score'), 50)
    rec = ctx.stock_info.get('recommendation', 'ACCUMULATE')

    rec_color = {
        "STRONG BUY": "#10B981",
        "BUY": "#10B981",
        "ACCUMULATE": "#10B981",
        "REDUCE / SELL": "#EF4444"
    }.get(rec, "#F59E0B")

    rec_bg = {
        "STRONG BUY": "rgba(16,185,129,0.12)",
        "BUY": "rgba(16,185,129,0.12)",
        "ACCUMULATE": "rgba(16,185,129,0.12)",
        "REDUCE / SELL": "rgba(239,68,68,0.12)"
    }.get(rec, "rgba(245,158,11,0.12)")
    
    ai_bg = {
        "STRONG BUY": "#ECFDF5",
        "BUY": "#ECFDF5",
        "ACCUMULATE": "#ECFDF5",
        "REDUCE / SELL": "#FEF2F2"
    }.get(rec, "#FFFBEB")


    stars = min(5, max(1, round(overall / 20)))
    arc_frac = min(1.0, overall / 100)
    dash_len = round(119.38 * arc_frac, 2)
    label = "ATTRACTIVE" if overall >= 65 else "FAIR" if overall >= 45 else "CAUTION"
    top_strength = "financial health" if m1_s == max(m1_s, m2_s, m3_s, m4_s, m5_s, m6_s) else "fair value"

    st.markdown("""
    <style>

    .ai-summary-card {
        width:100% !important;
        max-width:100% !important;
        min-width:0 !important;
        box-sizing:border-box !important;
    }

    .ai-summary-grid {
        width:100% !important;
        max-width:100% !important;
        min-width:0 !important;
        box-sizing:border-box !important;
    }

    .ai-summary-section {
        min-width:0 !important;
        box-sizing:border-box !important;
    }

    .ai-score-section {
        border-right:1px solid #E2E8F0;
        padding-right:20px;
    }

    .ai-insight-section {
        padding:0 10px;
    }

    .ai-recommendation-section {
        min-width:0 !important;
    }

    @media (max-width: 768px) {

        .ai-summary-card {
            padding:16px !important;
        }

        .ai-summary-grid {
            grid-template-columns:1fr !important;
            gap:16px !important;
        }

        .ai-score-section {
            border-right:none !important;
            border-bottom:1px solid #E2E8F0 !important;
            padding-right:0 !important;
            padding-bottom:16px !important;
        }

        .ai-insight-section {
            padding:0 !important;
            padding-bottom:16px !important;
            border-bottom:1px solid #E2E8F0 !important;
        }

        .ai-recommendation-section {
            width:100% !important;
        }

        .ai-summary-card * {
            max-width:100%;
            box-sizing:border-box;
        }

        .ai-recommendation-inner {
            flex-wrap:wrap !important;
            gap:12px !important;
        }

    }

    </style>
    """, unsafe_allow_html=True)

    st.html(f"""
    <div class="ai-summary-card"
         style="
            background:linear-gradient(135deg,{ai_bg} 0%,#FFFFFF 72%);
            border:2px solid {rec_color};
            border-radius:16px;
            padding:20px 22px;
            margin-bottom:20px;
            width:100%;
            max-width:100%;
            min-width:0;
            box-sizing:border-box;
            box-shadow:0 3px 12px rgba(15,23,42,0.06);
         ">

        <!-- HEADER -->
        <div style="
            display:flex;
            justify-content:space-between;
            align-items:center;
            margin-bottom:18px;
            padding-bottom:12px;
            border-bottom:1px solid #E2E8F0;
        ">
            <div>
                <div style="
                    font-size:16px;
                    font-weight:800;
                    color:#0F172A;
                    letter-spacing:0.6px;
                ">
                    AI INVESTMENT SUMMARY
                </div>

                <div style="
                    font-size:11.5px;
                    color:#64748B;
                    margin-top:3px;
                ">
                    AI-powered overview of investment signals
                </div>
            </div>

            <div style="
                background:{rec_bg};
                color:{rec_color};
                border:1px solid {rec_color};
                border-radius:20px;
                padding:5px 11px;
                font-size:11px;
                font-weight:700;
                white-space:nowrap;
            ">
                {rec}
            </div>
        </div>


        <!-- MAIN CONTENT -->
        <div class="ai-summary-grid"
             style="
                display:grid;
                grid-template-columns:minmax(190px,0.9fr)
                                 minmax(240px,1.25fr)
                                 minmax(280px,1.35fr);
                gap:20px;
                align-items:stretch;
                width:100%;
                min-width:0;
                max-width:100%;
                box-sizing:border-box;
             ">


            <!-- OVERALL SCORE -->
            <div class="ai-summary-section ai-score-section"
                 style="text-align:center;">

                <div style="
                    font-size:12px;
                    font-weight:700;
                    color:#64748B;
                    letter-spacing:0.7px;
                    margin-bottom:4px;
                ">
                    OVERALL SCORE
                </div>

                <div style="
                    margin:0 auto;
                    width:180px;
                    max-width:100%;
                ">
                    <svg viewBox="0 0 100 58"
                         style="
                            width:175px;
                            height:105px;
                            display:block;
                            margin:0 auto;
                         ">

                        <path
                            d="M 12 50 A 38 38 0 0 1 88 50"
                            fill="none"
                            stroke="#E2E8F0"
                            stroke-width="10"
                            stroke-linecap="round"
                        />

                        <path
                            d="M 12 50 A 38 38 0 0 1 88 50"
                            fill="none"
                            stroke="{rec_color}"
                            stroke-width="10"
                            stroke-linecap="round"
                            stroke-dasharray="{dash_len} 119.38"
                        />

                        <text
                            x="50"
                            y="38"
                            text-anchor="middle"
                            font-size="24"
                            font-weight="bold"
                            fill="#0F172A"
                        >
                            {overall:.0f}
                        </text>

                        <text
                            x="50"
                            y="49"
                            text-anchor="middle"
                            font-size="11.5"
                            fill="#64748B"
                        >
                            / 100
                        </text>

                    </svg>
                </div>

                <div style="
                    color:#F59E0B;
                    font-size:15px;
                    letter-spacing:3px;
                    margin-top:-2px;
                ">
                    {'★' * stars}{'☆' * (5-stars)}
                </div>

                <div style="
                    color:{rec_color};
                    font-size:17px;
                    font-weight:800;
                    margin-top:3px;
                ">
                    {label}
                </div>

            </div>


            <!-- AI INSIGHT -->
            <div class="ai-summary-section ai-insight-section"
                 style="
                    display:flex;
                    flex-direction:column;
                    justify-content:center;
                    text-align:center;
                 ">

                <div style="
                    font-size:12px;
                    font-weight:700;
                    color:#64748B;
                    letter-spacing:0.6px;
                    margin-bottom:10px;
                ">
                    INVESTMENT INSIGHT
                </div>

                <div style="
                    font-size:16px;
                    color:#475569;
                    line-height:1.7;
                ">

                    <div style="margin-bottom:4px;">
                        <b style="
                            color:#0F172A;
                            font-size:21px;
                        ">
                            {ctx.selected_ticker}
                        </b>
                    </div>

                    <div>
                        ได้คะแนนภาพรวม
                        <b style="
                            color:#0F172A;
                            font-size:18px;
                        ">
                            {overall:.1f}/100
                        </b>
                    </div>

                    <div style="margin-top:4px;">
                        จุดเด่นหลักอยู่ที่
                        <b style="color:{rec_color};">
                            {top_strength}
                        </b>
                    </div>

                    <div style="
                        margin-top:4px;
                        font-size:14px;
                        color:#64748B;
                    ">
                        อันดับ
                        <b style="color:#0F172A;">
                            {int(ctx.stock_info.get('sector_rank',1))} / {n_sector}
                        </b>
                        จากบริษัทในกลุ่ม
                        <b style="color:#0F172A;">
                            {ctx.stock_info.get('sector','-')}
                        </b>
                    </div>

                </div>

            </div>


            <!-- RECOMMENDATION -->
            <div class="ai-summary-section ai-recommendation-section"
                 style="
                    background:{rec_bg};
                    border:1px solid #D1FAE5;
                    border-radius:12px;
                    padding:16px 18px;
                    display:flex;
                    flex-direction:column;
                    justify-content:center;
                    box-sizing:border-box;
                 ">

                <div style="
                    font-size:12px;
                    color:#64748B;
                    font-weight:700;
                    letter-spacing:0.6px;
                    margin-bottom:10px;
                ">
                    RECOMMENDATION
                </div>

                <div class="ai-recommendation-inner"
                     style="
                        display:flex;
                        justify-content:space-between;
                        align-items:center;
                        gap:16px;
                     ">

                    <div style="
                        display:flex;
                        align-items:center;
                        gap:11px;
                        min-width:0;
                     ">

                        <div style="
                            width:42px;
                            height:42px;
                            border-radius:10px;
                            background:#FFFFFF;
                            display:flex;
                            align-items:center;
                            justify-content:center;
                            font-size:20px;
                            flex-shrink:0;
                        ">
                            📈
                        </div>

                        <div style="min-width:0;">

                            <div style="
                                color:{rec_color};
                                font-size:21px;
                                font-weight:800;
                                line-height:1.2;
                            ">
                                {rec}
                            </div>

                            <div style="
                                color:#64748B;
                                font-size:11.5px;
                                margin-top:3px;
                            ">
                                Based on Overall Score
                            </div>

                        </div>
                    </div>


                    <div style="
                        text-align:right;
                        flex-shrink:0;
                    ">

                        <div style="
                            color:#64748B;
                            font-size:11.5px;
                        ">
                            Sector Rank
                        </div>

                        <div style="
                            color:{rec_color};
                            font-size:18px;
                            font-weight:800;
                            margin-top:2px;
                        ">
                            {int(ctx.stock_info.get('sector_rank',1))}
                            <span style="
                                font-size:12px;
                                font-weight:600;
                            ">
                                / {n_sector}
                            </span>
                        </div>

                    </div>

                </div>

            </div>

        </div>
    </div>
    """)

    # ============================================================
    # TOP SECTION
    # ============================================================

    col_left, col_center = st.columns(
        [1.1, 2.3],
        vertical_alignment="top"
    )

    with col_left:

        st.html(f"""
        <div style="background-color:#FFFFFF;border:1px solid #E2E8F0;
                    border-radius:12px 12px 0 0;padding:16px 16px 8px 16px;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="font-size:23px;font-weight:bold;color:#0F172A;">{ctx.selected_ticker}</span>
                <span style="color:#64748B;font-size:18.5px;">☆</span>
            </div>
            <div style="font-size:14.5px;color:#64748B;margin-top:2px;">
                {COMPANY_NAMES.get(ctx.selected_ticker,'-')}
            </div>
            <div style="display:flex;align-items:baseline;gap:8px;margin-top:10px;">
                <span style="font-size:28px;font-weight:bold;color:#0F172A;line-height:1;">
                    {ctx.current_price:.2f}
                </span>
                <span style="font-size:14.5px;color:#64748B;">THB</span>
            </div>
            <div style="font-size:15px;font-weight:bold;color:{ctx.change_color};margin-top:4px;">
                {ctx.change_sign}{ctx.change_val:.2f} ({ctx.change_sign}{ctx.change_pct:.2f}%) {ctx.arrow_sign}
            </div>
            <div style="font-size:13px;color:#64748B;margin-top:4px;">
                Dataset close &bull; {ctx.stock_info.get('latest_date','-')}
            </div>
        </div>
        """)

        spark = ctx.stock_daily.tail(90)
        fig_mini = go.Figure()
        fig_mini.add_trace(go.Scatter(
            x=spark['date'], y=spark['close'], mode='lines',
            line=dict(color='#10B981', width=1.5),
            fill='tozeroy', fillcolor='rgba(16,185,129,0.08)', hoverinfo='skip'
        ))
        fig_mini.update_layout(
            height=125,
            margin=dict(l=8, r=8, t=0, b=0),
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            xaxis=dict(
                showgrid=False, showticklabels=True,
                tickfont=dict(size=11, color="#64748B"),
                nticks=4, linecolor="#E2E8F0"
            ),
            yaxis=dict(showgrid=False, showticklabels=False)
        )
        st.plotly_chart(fig_mini, use_container_width=True, config={'displayModeBar': False})

        market_cap = safe(ctx.stock_info.get('market_cap_mb'))
        fcf_latest = safe(ctx.stock_info.get('free_cash_flow_latest'))
        fcf_yield = fcf_latest / (market_cap * 1e6) * 100 if market_cap > 0 else 0

        st.html(f"""
        <div style="background-color:#FFFFFF;border:1px solid #E2E8F0;
                    border-top:none;border-radius:0 0 12px 12px;padding:8px 16px 16px 16px;">
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;
                        border-top:1px solid #E2E8F0;padding-top:10px;">

                <div>
                    <div style="font-size:13px;color:#64748B;">Market Cap</div>
                    <div style="font-size:15px;font-weight:bold;color:#0F172A;margin-top:2px;">
                        {fmt_mb(safe(ctx.stock_info.get('market_cap_mb')) * 1e6)}
                    </div>
                </div>

                <div>
                    <div style="font-size:13px;color:#64748B;">P/E (TTM)</div>
                    <div style="font-size:15px;font-weight:bold;color:#0F172A;margin-top:2px;">
                        {fmt_ratio(ctx.stock_info.get('pe_ratio'))}
                    </div>
                </div>

                <div>
                    <div style="font-size:13px;color:#64748B;">Sector</div>
                    <div style="font-size:15px;font-weight:bold;color:#0F172A;margin-top:2px;">
                        {ctx.stock_info.get('sector','-').split(' ')[0]}
                    </div>
                </div>

                <div>
                    <div style="font-size:13px;color:#64748B;">P/B (TTM)</div>
                    <div style="font-size:15px;font-weight:bold;color:#0F172A;margin-top:2px;">
                        {fmt_ratio(ctx.stock_info.get('pb_ratio'))}
                    </div>
                </div>

                <div>
                    <div style="font-size:13px;color:#64748B;">Industry</div>
                    <div style="font-size:14.5px;font-weight:bold;color:#0F172A;margin-top:2px;
                                white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                        {ctx.stock_info.get('sector','-')}
                    </div>
                </div>

                <div>
                    <div style="font-size:13px;color:#64748B;">FCF Yield</div>
                    <div style="font-size:15px;font-weight:bold;color:#10B981;margin-top:2px;">
                        {fcf_yield:.2f}%
                    </div>
                </div>

            </div>
        </div>
        """)

    with col_center:

        def module_card(num, label, score, badge, desc, green_at, yellow_at):
            color = score_color(score, green_at, yellow_at)
            badge_bg = score_bg(score, green_at, yellow_at)
            return f"""
            <div class="overview-module-card"
                 style="background-color:#FFFFFF;border:1px solid #E2E8F0;border-radius:10px;
                        padding:12px 12px;text-align:center;position:relative;
                        width:100%;min-width:0;max-width:100%;box-sizing:border-box;">
                <div style="position:absolute;top:10px;left:10px;background:{badge_bg};color:{color};
                            font-size:14px;font-weight:bold;padding:3px 7px;border-radius:5px;">
                    {num}
                </div>
                <div style="display:flex;justify-content:center;align-items:center;margin-bottom:10px;">
                    <span style="font-size:15px;font-weight:bold;color:#0F172A;">{label}</span>
                </div>
                <div style="margin:0 auto 10px auto;width:88px;height:88px;border-radius:50%;
                            background:conic-gradient({color} 0% {score}%,#E2E8F0 {score}% 100%);
                            display:flex;align-items:center;justify-content:center;">
                    <div style="width:72px;height:72px;border-radius:50%;background-color:#FFFFFF;
                                display:flex;flex-direction:column;align-items:center;justify-content:center;">
                        <span style="font-size:20px;font-weight:bold;color:#0F172A;line-height:1;">
                            {score}
                        </span>
                        <span style="font-size:13.5px;color:#64748B;">100</span>
                    </div>
                </div>
                <div style="color:{color};font-size:15.5px;font-weight:bold;margin-bottom:5px;">
                    {badge}
                </div>
                <div style="font-size:14.5px;color:#475569;line-height:1.4;">{desc}</div>
            </div>
            """

        cards_html = "".join([
            module_card("01", "COMPANY HEALTH", m1_s, m1_badge, m1_desc, 70, 45),
            module_card("02", "FAIR VALUE", m2_s, m2_badge, m2_desc, 67, 34),
            module_card("03", "ENTRY TIMING", m3_s, m3_badge, m3_desc, 67, 34),
            module_card("04", "AI PREDICTION", m4_s, m4_badge, m4_desc, 70, 50),
            module_card("05", "RISK ANALYSIS", m5_s, m5_badge, m5_desc, 65, 45),
            module_card("06", "INDUSTRY BENCHMARK", m6_s, m6_badge, m6_desc, 70, 45)
        ])

        st.markdown("""
        <style>

        .overview-decision-card {
            width:100% !important;
            max-width:100% !important;
            min-width:0 !important;
            box-sizing:border-box !important;
        }

        .overview-module-grid {
            width:100% !important;
            max-width:100% !important;
            min-width:0 !important;
            box-sizing:border-box !important;

            height:calc(100% - 32px) !important;
            grid-template-rows:repeat(2, minmax(0, 1fr)) !important;
        }

        .overview-module-card {
            width:100% !important;
            max-width:100% !important;
            min-width:0 !important;
            min-height:0 !important;
            height:100% !important;
            box-sizing:border-box !important;
            overflow:hidden !important;
        }

        @media (max-width: 768px) {

            .overview-decision-card {
                height:auto !important;
                margin-top:0 !important;
            }

            .overview-module-grid {
                height:auto !important;
                grid-template-columns:1fr !important;
                grid-template-rows:none !important;
            }

            .overview-module-card {
                height:auto !important;
                min-height:0 !important;
                overflow:visible !important;
            }

        }

        </style>
        """, unsafe_allow_html=True)

        st.html(f"""
            <div class="overview-decision-card"
                 style="background-color:#FFFFFF;border:1px solid #E2E8F0;
                        border-radius:12px;padding:16px;
                        height:532px;box-sizing:border-box;
                        margin-top:-16px;">
                <div style="font-size:15px;font-weight:bold;color:#0F172A;
                            letter-spacing:0.5px;margin-bottom:12px;">
                    INVESTMENT DECISION OVERVIEW ({ctx.selected_ticker})
                </div>

                <div class="overview-module-grid"
                     style="display:grid;
                            grid-template-columns:repeat(3,minmax(0,1fr));
                            grid-template-rows:repeat(2,minmax(0,1fr));
                            gap:12px;
                            width:100%;
                            min-width:0;
                            height:calc(100% - 32px);
                            box-sizing:border-box;">
                    {cards_html}
                </div>
            </div>
        """)

    rev_g = ctx.stock_info.get('revenue_growth_yoy')
    ni_g = ctx.stock_info.get('net_income_growth_yoy')
    fcf_val = ctx.stock_info.get('free_cash_flow_latest')
    de_val = safe(ctx.stock_info.get('de_ratio'))
    roe_val = safe(ctx.stock_info.get('roe'))
    industry_rank_txt = f"{int(ctx.stock_info.get('sector_rank',1))} / {n_sector}"

    def hl_card(icon, bg, label, value, sub, val_color="#0F172A"):
        return f"""
        <div style="background-color:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;
                    padding:10px 12px;display:flex;align-items:center;gap:10px;
                    width:100%;min-width:0;max-width:100%;box-sizing:border-box;">
            <div style="background:{bg};width:40px;height:40px;border-radius:8px;
                        display:flex;align-items:center;justify-content:center;font-size:17.5px;">
                {icon}
            </div>
            <div>
                <div style="font-size:13px;color:#64748B;">{label}</div>
                <div style="font-size:16px;font-weight:bold;color:{val_color};margin-top:1px;">
                    {value}
                </div>
                <div style="font-size:12px;color:#64748B;">{sub}</div>
            </div>
        </div>
        """

    hl_html = "".join([
        hl_card(
            "📊", "rgba(16,185,129,0.15)", "Revenue Growth",
            f"{'+' if (rev_g or 0) >= 0 else ''}{rev_g if rev_g is not None else 0:.1f}%",
            "YoY (latest FY)", "#10B981" if (rev_g or 0) >= 0 else "#EF4444"
        ),
        hl_card(
            "💰", "rgba(245,158,11,0.15)", "Net Profit Growth",
            f"{'+' if (ni_g or 0) >= 0 else ''}{ni_g if ni_g is not None else 0:.1f}%",
            "YoY (latest FY)", "#10B981" if (ni_g or 0) >= 0 else "#EF4444"
        ),
        hl_card(
            "⏱️", "rgba(56,189,248,0.15)", "ROE (TTM)",
            f"{roe_val:.1f}%", "Return on Equity", "#38BDF8"
        ),
        hl_card(
            "💵", "rgba(168,85,247,0.15)", "Free Cash Flow",
            fmt_mb(safe(fcf_val)), "Latest FY", "#0F172A"
        ),
        hl_card(
            "🛡️", "rgba(249,115,22,0.15)", "Debt to Equity",
            f"{de_val:.2f}", "Lower is safer", "#FB923C"
        ),
        hl_card(
            "🏆", "rgba(20,184,166,0.15)", "Sector Rank",
            industry_rank_txt, f"In {ctx.stock_info.get('sector','-')}", "#2DD4BF"
        )
    ])

    st.markdown("""
    <style>
    @media (max-width: 768px) {

        .key-highlights-grid {
            grid-template-columns:1fr !important;
            width:100% !important;
            max-width:100% !important;
        }    

        .key-highlights-grid > div {
            width:100% !important;
            max-width:100% !important;
            min-width:0 !important;
            box-sizing:border-box !important;
        }

        .overview-decision-card {
            height:auto !important;
        }

    }
    </style>
    """, unsafe_allow_html=True)

    st.html(f"""
    <div style="background-color:#FFFFFF;border:1px solid #E2E8F0;
                border-radius:12px;padding:14px 16px;">
        <div style="font-size:14.5px;font-weight:bold;color:#64748B;
                    margin-bottom:10px;letter-spacing:0.5px;">
            KEY HIGHLIGHTS
        </div>
        <div class="key-highlights-grid"
             style="display:grid;grid-template-columns:repeat(6,minmax(0,1fr));
                    gap:10px;width:100%;min-width:0;">
            {hl_html}
        </div>
    </div>
    """)

    col1, col2, col3 = st.columns([2.7, 1.3, 0.5])

    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)

    st.markdown(
        """
        <div style="
            border-top:1px solid #E2E8F0;
            padding-top:16px;
            margin-bottom:6px;
        "></div>
        """,
        unsafe_allow_html=True
    )

    col_space1, col_space2, col_next, col_disc = st.columns(
        [1.3, 1.3, 1.3, 3.3]
    )

    with col_next:
        if st.button(
            "หน้าถัดไป ➡",
            key="overview_next_company_health",
            use_container_width=True
        ):
            st.session_state["pending_nav"] = " Company Health"
            st.rerun()

    with col_disc:
        st.markdown(
            """
            <div style="
                font-size:15.5px;
                color:#64748B;
                text-align:right;
                padding-top:11px;
                line-height:1.5;
            ">
                หมายเหตุ: การประเมินนี้ไม่ใช่คำแนะนำในการลงทุน
                ผู้ลงทุนควรศึกษาข้อมูลเพิ่มเติม
            </div>
            """,
            unsafe_allow_html=True
        )
