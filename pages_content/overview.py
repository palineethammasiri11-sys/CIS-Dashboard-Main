"""
pages_content/overview.py
---------------------
หน้า "Overview" ของ CIS Dashboard

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
    st.markdown("""
    <div style="margin-bottom:20px;">
        <div style="font-size:23px; font-weight:700; color:#0F172A; letter-spacing:0.3px;">
            OVERVIEW DASHBOARD
        </div>
        <div style="font-size:15px; color:#64748B; margin-top:4px;">
            ภาพรวมข้อมูลและการวิเคราะห์เพื่อสนับสนุนการตัดสินใจลงทุน
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_left, col_center, col_right = st.columns([1.1, 2.3, 1.2])

    with col_left:
        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px 12px 0 0; padding:16px 16px 8px 16px;">
    <div style="display:flex; justify-content:space-between; align-items:center;">
    <span style="font-size:23px; font-weight:bold; color:#FFFFFF;">{ctx.selected_ticker}</span>
    <span style="color:#64748B; font-size:18.5px;">☆</span>
    </div>
    <div style="font-size:14.5px; color:#94A3B8; margin-top:2px;">{COMPANY_NAMES.get(ctx.selected_ticker,'-')}</div>
    <div style="display:flex; align-items:baseline; gap:8px; margin-top:10px;">
    <span style="font-size:28px; font-weight:bold; color:#FFFFFF; line-height:1;">{ctx.current_price:.2f}</span>
    <span style="font-size:14.5px; color:#94A3B8;">THB</span>
    </div>
    <div style="font-size:15px; font-weight:bold; color:{ctx.change_color}; margin-top:4px;">{ctx.change_sign}{ctx.change_val:.2f} ({ctx.change_sign}{ctx.change_pct:.2f}%) {ctx.arrow_sign}</div>
    <div style="font-size:13px; color:#64748B; margin-top:4px;">Dataset close &bull; {ctx.stock_info.get('latest_date','-')}</div>
    </div>""", unsafe_allow_html=True)

        # Sparkline จากราคาปิดจริงย้อนหลัง 90 วันทำการ
        spark = ctx.stock_daily.tail(90)
        fig_mini = go.Figure()
        fig_mini.add_trace(go.Scatter(
            x=spark['date'], y=spark['close'], mode='lines',
            line=dict(color='#10B981', width=1.5), fill='tozeroy', fillcolor='rgba(16, 185, 129, 0.08)', hoverinfo='skip'
        ))
        fig_mini.update_layout(
            height=125, margin=dict(l=8, r=8, t=0, b=0), paper_bgcolor="#0F172A", plot_bgcolor="#0F172A",
            xaxis=dict(showgrid=False, showticklabels=True, tickfont=dict(size=11, color="#64748B"), nticks=4, linecolor="#1E293B"),
            yaxis=dict(showgrid=False, showticklabels=False)
        )
        st.plotly_chart(fig_mini, use_container_width=True, config={'displayModeBar': False})

        n_sector = len(ctx.sector_peers)
        fcf_yield = (safe(ctx.stock_info.get('free_cash_flow_latest')) / (safe(ctx.stock_info.get('market_cap_mb')) * 1e6) * 100) if safe(ctx.stock_info.get('market_cap_mb')) > 0 else 0
        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-top:none; border-radius:0 0 12px 12px; padding:8px 16px 16px 16px;">
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px; border-top:1px solid #1E293B; padding-top:10px;">
    <div><div style="font-size:13px; color:#64748B;">Market Cap</div><div style="font-size:15px; font-weight:bold; color:#F8FAFC; margin-top:2px;">{fmt_mb(safe(ctx.stock_info.get('market_cap_mb'))*1e6)}</div></div>
    <div><div style="font-size:13px; color:#64748B;">P/E (TTM)</div><div style="font-size:15px; font-weight:bold; color:#F8FAFC; margin-top:2px;">{fmt_ratio(ctx.stock_info.get('pe_ratio'))}</div></div>
    <div><div style="font-size:13px; color:#64748B;">Sector</div><div style="font-size:15px; font-weight:bold; color:#F8FAFC; margin-top:2px;">{ctx.stock_info.get('sector','-').split(' ')[0]}</div></div>
    <div><div style="font-size:13px; color:#64748B;">P/B (TTM)</div><div style="font-size:15px; font-weight:bold; color:#F8FAFC; margin-top:2px;">{fmt_ratio(ctx.stock_info.get('pb_ratio'))}</div></div>
    <div><div style="font-size:13px; color:#64748B;">Industry</div><div style="font-size:14.5px; font-weight:bold; color:#F8FAFC; margin-top:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{ctx.stock_info.get('sector','-')}</div></div>
    <div><div style="font-size:13px; color:#64748B;">FCF Yield</div><div style="font-size:15px; font-weight:bold; color:#10B981; margin-top:2px;">{fcf_yield:.2f}%</div></div>
    </div>
    </div>""", unsafe_allow_html=True)

    with col_center:
        m1_s = int(round(safe(ctx.stock_info.get('health_score'), 50)))
        m2_s = int(round(safe(ctx.stock_info.get('valuation_score'), 50)))
        m3_s = int(round(safe(ctx.stock_info.get('timing_score'), 50)))
        m4_s = int(round(safe(ctx.stock_info.get('ai_score'), 50)))
        m5_s = int(round(safe(ctx.stock_info.get('risk_score'), 50)))
        m6_s = int(round(safe(ctx.stock_info.get('industry_score'), 50)))

        if m1_s >= 70: m1_badge, m1_desc = "EXCELLENT", "Strong balance sheet and sustainable quality"
        elif m1_s >= 45: m1_badge, m1_desc = "MODERATE", "Stable financial position with sound liquidity"
        else: m1_badge, m1_desc = "WEAK", "Elevated debt leverage or margin pressure"

        if m2_s >= 70: m2_badge, m2_desc = "UNDERVALUED", "Attractive valuation with high margin of safety"
        elif m2_s >= 45: m2_badge, m2_desc = "FAIR VALUE", "Trading near assessed fundamental value"
        else: m2_badge, m2_desc = "OVERVALUED", "Price trades at premium to fair valuation"

        if m3_s >= 65: m3_badge, m3_desc = "BULLISH", "Strong upward momentum across moving averages"
        elif m3_s >= 45: m3_badge, m3_desc = "NEUTRAL", "Consolidating near key technical support"
        else: m3_badge, m3_desc = "BEARISH", "Downtrend momentum; elevated pullback risk"

        if m4_s >= 65: m4_badge, m4_desc = "POSITIVE", "AI model forecasts favorable upside probability"
        elif m4_s >= 45: m4_badge, m4_desc = "NEUTRAL", "AI predicts range-bound price consolidation"
        else: m4_badge, m4_desc = "CAUTION", "Low upside probability under current features"

        if m5_s >= 65: m5_badge, m5_desc = "LOW RISK", "High resilience with stable volatility"
        elif m5_s >= 45: m5_badge, m5_desc = "MODERATE", "Balanced market risk profile"
        else: m5_badge, m5_desc = "HIGH RISK", "Higher volatility and deeper drawdown risk"

        if m6_s >= 70: m6_badge, m6_desc = "OUTPERFORM", "Leading peer group across key industry metrics"
        elif m6_s >= 45: m6_badge, m6_desc = "PARITY", "Performing on par with sectoral median"
        else: m6_badge, m6_desc = "LAGGING", "Trailing behind sectoral benchmark"

        def module_card(num, icon, label, score, color, badge, desc, badge_bg):
            return f"""<div style="background-color:#151E2F; border:1px solid #1E293B; border-radius:10px; padding:16px 14px; text-align:center; position:relative;">
    <div style="position:absolute; top:10px; left:10px; background:{badge_bg}; color:{color}; font-size:14px; font-weight:bold; padding:3px 7px; border-radius:5px;">{num}</div>
    <div style="display:flex; justify-content:center; align-items:center; gap:6px; margin-bottom:10px;">
    <span style="font-size:18px;">{icon}</span><span style="font-size:15px; font-weight:bold; color:#F8FAFC;">{label}</span>
    </div>
    <div style="margin:0 auto 10px auto; width:88px; height:88px; border-radius:50%; background:conic-gradient({color} 0% {score}%, #1E293B {score}% 100%); display:flex; align-items:center; justify-content:center;">
    <div style="width:72px; height:72px; border-radius:50%; background-color:#151E2F; display:flex; flex-direction:column; align-items:center; justify-content:center;">
    <span style="font-size:20px; font-weight:bold; color:#FFFFFF; line-height:1;">{score}</span><span style="font-size:13.5px; color:#94A3B8;">100</span>
    </div></div>
    <div style="color:{color}; font-size:15.5px; font-weight:bold; margin-bottom:5px;">{badge}</div>
    <div style="font-size:14.5px; color:#CBD5E1; line-height:1.4;">{desc}</div>
    </div>"""

        cards_html = "".join([
            module_card("01", "💚", "COMPANY HEALTH", m1_s, "#34D399", m1_badge, m1_desc, "rgba(16,185,129,0.2)"),
            module_card("02", "⚖️", "FAIR VALUE", m2_s, "#FBBF24", m2_badge, m2_desc, "rgba(245,158,11,0.2)"),
            module_card("03", "⏱️", "ENTRY TIMING", m3_s, "#38BDF8", m3_badge, m3_desc, "rgba(56,189,248,0.2)"),
            module_card("04", "🔮", "AI PREDICTION", m4_s, "#C084FC", m4_badge, m4_desc, "rgba(168,85,247,0.2)"),
            module_card("05", "🛡️", "RISK ANALYSIS", m5_s, "#FB923C", m5_badge, m5_desc, "rgba(249,115,22,0.2)"),
            module_card("06", "📊", "INDUSTRY BENCHMARK", m6_s, "#2DD4BF", m6_badge, m6_desc, "rgba(20,184,166,0.2)"),
        ])
        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px; padding:16px; min-height:900px;">
    <div style="font-size:15px; font-weight:bold; color:#F1F5F9; letter-spacing:0.5px; margin-bottom:12px;">INVESTMENT DECISION OVERVIEW ({ctx.selected_ticker})</div>
    <div style="display:grid; grid-template-columns: repeat(2, 1fr); gap:12px;">{cards_html}</div>
    </div>""", unsafe_allow_html=True)

    with col_right:
        overall = safe(ctx.stock_info.get('overall_score'), 50)
        rec = ctx.stock_info.get('recommendation', 'ACCUMULATE')
        rec_color = {"STRONG BUY": "#10B981", "BUY": "#10B981", "ACCUMULATE": "#84CC16", "REDUCE / SELL": "#EF4444"}.get(rec, "#F59E0B")
        stars = min(5, max(1, round(overall / 20)))
        arc_frac = min(1.0, overall / 100)
        dash_len = round(119.38 * arc_frac, 2)
        label = "ATTRACTIVE" if overall >= 65 else ("FAIR" if overall >= 45 else "CAUTION")
        top_strength = "financial health" if m1_s == max(m1_s, m2_s, m3_s, m4_s, m5_s, m6_s) else "fair value"
        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px; padding:16px; min-height:900px; display:flex; flex-direction:column; justify-content:space-between; text-align:center;">
    <div>
    <div style="font-size:14.5px; font-weight:bold; color:#94A3B8; letter-spacing:0.5px; text-align:left; margin-bottom:4px;">AI INVESTMENT SUMMARY</div>
    <div style="margin:6px auto 0 auto; width:140px;">
    <svg viewBox="0 0 100 58" style="width:130px; height:83px; display:block; margin:0 auto;">
    <path d="M 12 50 A 38 38 0 0 1 88 50" fill="none" stroke="#1E293B" stroke-width="10" stroke-linecap="round" />
    <path d="M 12 50 A 38 38 0 0 1 88 50" fill="none" stroke="#10B981" stroke-width="10" stroke-linecap="round" stroke-dasharray="{dash_len} 119.38" />
    <text x="50" y="38" text-anchor="middle" font-size="21" font-weight="bold" fill="#FFFFFF">{overall:.0f}</text>
    <text x="50" y="49" text-anchor="middle" font-size="11.5" fill="#64748B">100</text>
    </svg>
    </div>
    <div style="font-size:13px; font-weight:bold; color:#94A3B8; margin-top:2px;">OVERALL SCORE</div>
    <div style="color:#F59E0B; font-size:14.5px; letter-spacing:2px; margin:2px 0;">{'★'*stars}{'☆'*(5-stars)}</div>
    <div style="color:{rec_color}; font-size:16px; font-weight:bold; margin-top:2px;">{label}</div>
    <div style="font-size:12.5px; color:#CBD5E1; line-height:1.35; margin-top:4px; padding:0 2px;">
    <b>{ctx.selected_ticker}</b> ได้คะแนนภาพรวม {overall:.1f}/100 จุดเด่นหลักอยู่ที่ {top_strength} อันดับ {int(ctx.stock_info.get('sector_rank',1))} จาก {n_sector} บริษัทในกลุ่ม {ctx.stock_info.get('sector','-')}
    </div>
    <div style="background-color:#151E2F; border:1px solid #1E293B; border-radius:8px; padding:8px 10px; margin-top:8px; text-align:left;">
    <div style="font-size:12.5px; color:#94A3B8; font-weight:bold; margin-bottom:2px;">RECOMMENDATION</div>
    <div style="display:flex; justify-content:space-between; align-items:center;">
    <div style="display:flex; align-items:center; gap:6px;">
    <span style="color:{rec_color}; font-size:16.5px;">📈</span>
    <div><b style="color:{rec_color}; font-size:16px; line-height:1;">{rec}</b><div style="color:#64748B; font-size:11.5px;">Based on Overall Score</div></div>
    </div>
    <div style="text-align:right;"><div style="color:#64748B; font-size:11.5px;">Sector Rank:</div><b style="color:{rec_color}; font-size:13px;">{int(ctx.stock_info.get('sector_rank',1))} / {n_sector}</b></div>
    </div></div>
    </div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:22px;'></div>", unsafe_allow_html=True)

    rev_g = ctx.stock_info.get('revenue_growth_yoy')
    ni_g = ctx.stock_info.get('net_income_growth_yoy')
    fcf_val = ctx.stock_info.get('free_cash_flow_latest')
    de_val = safe(ctx.stock_info.get('de_ratio'))
    roe_val = safe(ctx.stock_info.get('roe'))
    industry_rank_txt = f"{int(ctx.stock_info.get('sector_rank',1))} / {n_sector}"

    def hl_card(icon, bg, label, value, sub, val_color="#F8FAFC"):
        return f"""<div style="background-color:#151E2F; border:1px solid #1E293B; border-radius:8px; padding:10px 12px; display:flex; align-items:center; gap:10px;">
    <div style="background:{bg}; width:40px; height:40px; border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:17.5px;">{icon}</div>
    <div><div style="font-size:13px; color:#94A3B8;">{label}</div><div style="font-size:16px; font-weight:bold; color:{val_color}; margin-top:1px;">{value}</div><div style="font-size:12px; color:#64748B;">{sub}</div></div>
    </div>"""

    hl_html = "".join([
        hl_card("📊", "rgba(16,185,129,0.15)", "Revenue Growth", f"{'+' if (rev_g or 0)>=0 else ''}{rev_g if rev_g is not None else 0:.1f}%", "YoY (latest FY)", "#10B981" if (rev_g or 0) >= 0 else "#EF4444"),
        hl_card("💰", "rgba(245,158,11,0.15)", "Net Profit Growth", f"{'+' if (ni_g or 0)>=0 else ''}{ni_g if ni_g is not None else 0:.1f}%", "YoY (latest FY)", "#10B981" if (ni_g or 0) >= 0 else "#EF4444"),
        hl_card("⏱️", "rgba(56,189,248,0.15)", "ROE (TTM)", f"{roe_val:.1f}%", "Return on Equity", "#38BDF8"),
        hl_card("💵", "rgba(168,85,247,0.15)", "Free Cash Flow", fmt_mb(safe(fcf_val)), "Latest FY", "#F8FAFC"),
        hl_card("🛡️", "rgba(249,115,22,0.15)", "Debt to Equity", f"{de_val:.2f}", "Lower is safer", "#FB923C"),
        hl_card("🏆", "rgba(20,184,166,0.15)", "Sector Rank", industry_rank_txt, f"In {ctx.stock_info.get('sector','-')}", "#2DD4BF"),
    ])
    st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px; padding:14px 16px;">
    <div style="font-size:14.5px; font-weight:bold; color:#94A3B8; margin-bottom:10px; letter-spacing:0.5px;">KEY HIGHLIGHTS</div>
    <div style="display:grid; grid-template-columns: repeat(6, 1fr); gap:10px;">{hl_html}</div>
    </div>
    <div style="font-size:12.5px; color:#475569; text-align:center; margin-top:10px;">
    Disclaimer: This dashboard is for informational purposes only and not intended as investment advice. Please conduct your own research before making investment decisions.
    </div>""", unsafe_allow_html=True)

