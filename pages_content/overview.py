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
        "ACCUMULATE": "#84CC16",
        "REDUCE / SELL": "#EF4444"
    }.get(rec, "#F59E0B")

    stars = min(5, max(1, round(overall / 20)))
    arc_frac = min(1.0, overall / 100)
    dash_len = round(119.38 * arc_frac, 2)
    label = "ATTRACTIVE" if overall >= 65 else "FAIR" if overall >= 45 else "CAUTION"
    top_strength = "financial health" if m1_s == max(m1_s, m2_s, m3_s, m4_s, m5_s, m6_s) else "fair value"

    st.markdown("""
    <style>
    @media (max-width: 768px) {
        .ai-summary-grid {
            grid-template-columns:1fr !important;
            width:100% !important;
            max-width:100% !important;
            min-width:0 !important;
            box-sizing:border-box !important;
            gap:16px !important;
        }
        .ai-summary-grid > div {
            width:100% !important;
            max-width:100% !important;
            min-width:0 !important;
            box-sizing:border-box !important;
        }
        .ai-summary-grid * {
            max-width:100%;
            box-sizing:border-box;
        }
        .ai-summary-grid div[style*="display:flex"] {
            min-width:0 !important;
            max-width:100% !important;
            flex-wrap:wrap !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    st.html(f"""
    <div style="background-color:#FFFFFF;border:2px solid {rec_color};border-radius:12px;
                padding:16px;margin-bottom:16px;width:100%;max-width:100%;min-width:0;box-sizing:border-box;">
        <div style="font-size:14.5px;font-weight:bold;color:#64748B;letter-spacing:0.5px;margin-bottom:12px;">
            AI INVESTMENT SUMMARY
        </div>

        <div class="ai-summary-grid" style="display:grid;grid-template-columns:minmax(0,180px) minmax(0,1fr) minmax(0,1.3fr);
                    gap:24px;align-items:center;width:100%;min-width:0;max-width:100%;box-sizing:border-box;">

            <div style="text-align:center;">
                <div style="margin:0 auto;width:140px;">
                    <svg viewBox="0 0 100 58" style="width:130px;height:83px;display:block;margin:0 auto;">
                        <path d="M 12 50 A 38 38 0 0 1 88 50" fill="none" stroke="#E2E8F0"
                              stroke-width="10" stroke-linecap="round"/>
                        <path d="M 12 50 A 38 38 0 0 1 88 50" fill="none" stroke="{rec_color}"
                              stroke-width="10" stroke-linecap="round" stroke-dasharray="{dash_len} 119.38"/>
                        <text x="50" y="38" text-anchor="middle" font-size="21" font-weight="bold"
                              fill="#0F172A">{overall:.0f}</text>
                        <text x="50" y="49" text-anchor="middle" font-size="11.5"
                              fill="#64748B">100</text>
                    </svg>
                </div>
                <div style="font-size:13px;font-weight:bold;color:#64748B;">OVERALL SCORE</div>
                <div style="color:#F59E0B;font-size:14.5px;letter-spacing:2px;margin:2px 0;">
                    {'★' * stars}{'☆' * (5-stars)}
                </div>
                <div style="color:{rec_color};font-size:16px;font-weight:bold;">{label}</div>
            </div>

            <div style="text-align:center;">
                <div style="font-size:14px;color:#475569;line-height:1.6;">
                    <b style="color:#0F172A;">{ctx.selected_ticker}</b>
                    ได้คะแนนภาพรวม <b>{overall:.1f}/100</b><br>
                    จุดเด่นหลักอยู่ที่ <b>{top_strength}</b><br>
                    อันดับ <b>{int(ctx.stock_info.get('sector_rank',1))} / {n_sector}</b>
                    จากบริษัทในกลุ่ม <b>{ctx.stock_info.get('sector','-')}</b>
                </div>
            </div>

            <div style="background-color:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;
                        padding:12px 14px;text-align:left;">
                <div style="font-size:12.5px;color:#64748B;font-weight:bold;margin-bottom:4px;">
                    RECOMMENDATION
                </div>
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div style="display:flex;align-items:center;gap:8px;">
                        <span style="color:{rec_color};font-size:18px;">📈</span>
                        <div>
                            <b style="color:{rec_color};font-size:16px;">{rec}</b>
                            <div style="color:#64748B;font-size:11.5px;">Based on Overall Score</div>
                        </div>
                    </div>
                    <div style="text-align:right;">
                        <div style="color:#64748B;font-size:11.5px;">Sector Rank:</div>
                        <b style="color:{rec_color};font-size:13px;">
                            {int(ctx.stock_info.get('sector_rank',1))} / {n_sector}
                        </b>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """)

    # ============================================================
    # TOP SECTION
    # ============================================================

    col_left, col_center = st.columns([1.1, 2.3])

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
            <div style="background-color:#FFFFFF;border:1px solid #E2E8F0;border-radius:10px;
                        padding:16px 14px;text-align:center;position:relative;
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
        @media (max-width: 768px) {
            .overview-module-grid {
                grid-template-columns:1fr !important;
                width:100% !important;
                max-width:100% !important;
            }
            .overview-module-grid > div {
                width:100% !important;
                max-width:100% !important;
                min-width:0 !important;
                box-sizing:border-box !important;
            }
        }
        </style>
        """, unsafe_allow_html=True)

        st.html(f"""
        <div style="background-color:#FFFFFF;border:1px solid #E2E8F0;
                    border-radius:12px;padding:16px;">
            <div style="font-size:15px;font-weight:bold;color:#0F172A;
                        letter-spacing:0.5px;margin-bottom:12px;">
                INVESTMENT DECISION OVERVIEW ({ctx.selected_ticker})
            </div>
            <div class="overview-module-grid"
                 style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));
                        gap:12px;width:100%;min-width:0;">
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

    <div style="font-size:12.5px;color:#475569;text-align:center;margin-top:10px;">
        Disclaimer: This dashboard is for informational purposes only and not intended as
        investment advice. Please conduct your own research before making investment decisions.
    </div>
    """)

    render_nav_footer("m1", next_page=" Company Health")
