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

    st.markdown("""<div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:15px;">
    <div><div style="display:flex; align-items:center; gap:8px;"><h2 style="margin:0; font-size:23px; font-weight:bold; color:#F8FAFC; letter-spacing:0.5px;">FAIR VALUE ASSESSMENT</h2></div>
    <div style="font-size:15px; color:#94A3B8; margin-top:2px;">ประเมินมูลค่าที่เหมาะสมของหุ้นโดยใช้แบบจำลอง DCF ผสาน P/E Relative</div></div>
    </div>""", unsafe_allow_html=True)

    r1_c1, r1_c2, r1_c3, r1_c4, r1_c5, r1_c6 = st.columns([1.5, 0.9, 0.9, 0.9, 0.9, 1.1])
    val_stars = min(5, max(1, round(val_score / 20)))

    with r1_c1:
        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px; padding:14px; min-height:170px; display:flex; flex-direction:column; justify-content:space-between;">
    <div style="font-size:13.5px; font-weight:bold; color:#94A3B8; letter-spacing:0.5px;">FAIR VALUE SUMMARY</div>
    <div style="display:flex; align-items:center; gap:12px;">
    <div style="width:76px; height:76px; border-radius:50%; background:conic-gradient({val_color} 0% {val_score}%, #1E293B {val_score}% 100%); display:flex; align-items:center; justify-content:center; flex-shrink:0;">
    <div style="width:62px; height:62px; border-radius:50%; background-color:#0F172A; display:flex; flex-direction:column; align-items:center; justify-content:center;">
    <span style="font-size:19px; font-weight:bold; color:#FFFFFF; line-height:1;">{val_score}</span><span style="font-size:12px; color:#64748B;">/100</span></div></div>
    <div><div style="color:{val_color}; font-size:16.5px; font-weight:bold; line-height:1.2;">{val_status}</div>
    <div style="font-size:13px; color:#CBD5E1; line-height:1.35; margin-top:3px;">Margin of Safety อยู่ที่ {val_mos:.1f}% เมื่อเทียบกับมูลค่าพื้นฐานที่แท้จริง</div>
    <div style="color:{val_color}; font-size:14.5px; letter-spacing:1px; margin-top:4px;">{'★'*val_stars}{'☆'*(5-val_stars)}</div></div>
    </div></div>""", unsafe_allow_html=True)

    with r1_c2:
        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px; padding:12px; min-height:170px; display:flex; flex-direction:column; justify-content:space-between;">
    <div style="font-size:13px; font-weight:bold; color:#94A3B8;">CURRENT PRICE</div>
    <div><div style="font-size:21px; font-weight:bold; color:#FFFFFF; line-height:1;">{val_cur_price:.2f} <span style="font-size:13.5px; color:#94A3B8;">THB</span></div>
    <div style="font-size:12px; color:#64748B; margin-top:2px;">({ctx.stock_info.get('latest_date','-')})</div></div>
    </div>""", unsafe_allow_html=True)

    with r1_c3:
        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px; padding:12px; min-height:170px; display:flex; flex-direction:column; justify-content:space-between;">
    <div style="font-size:13px; font-weight:bold; color:#94A3B8;">ESTIMATED FAIR VALUE<br><span style="font-size:12px; color:#64748B;">(BLENDED: 55% DCF + 45% P/E)</span></div>
    <div><div style="font-size:21px; font-weight:bold; color:#FFFFFF; line-height:1;">{val_base:.2f} <span style="font-size:13.5px; color:#94A3B8;">THB</span></div></div>
    </div>""", unsafe_allow_html=True)

    with r1_c4:
        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px; padding:12px; min-height:170px; display:flex; flex-direction:column; justify-content:space-between; text-align:center;">
    <div style="font-size:13px; font-weight:bold; color:#94A3B8; text-align:left;">MARGIN OF SAFETY</div>
    <div><div style="font-size:21px; font-weight:bold; color:{val_color}; line-height:1;">{val_mos:.1f}%</div></div>
    <div style="margin-top:auto; display:flex; justify-content:center;"><div style="background:rgba(16,185,129,0.15); border:1px solid #10B981; border-radius:50%; width:36px; height:36px; display:flex; align-items:center; justify-content:center; font-size:15px; color:#10B981;">🛡️</div></div>
    </div>""", unsafe_allow_html=True)

    with r1_c5:
        conf = "High" if abs(val_mos) > 15 else ("Medium" if abs(val_mos) > 5 else "Low")
        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px; padding:12px; min-height:170px; display:flex; flex-direction:column; justify-content:space-between; text-align:center;">
    <div style="font-size:13px; font-weight:bold; color:#94A3B8; text-align:left;">CONFIDENCE LEVEL</div>
    <div><div style="font-size:18.5px; font-weight:bold; color:#10B981; line-height:1;">{conf.upper()}</div></div>
    </div>""", unsafe_allow_html=True)

    with r1_c6:
        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px; padding:12px; min-height:170px; display:flex; flex-direction:column; justify-content:space-between; text-align:center;">
    <div style="font-size:13px; font-weight:bold; color:#94A3B8; text-align:left;">RECOMMENDATION</div>
    <div><div style="font-size:17.5px; font-weight:bold; color:{val_color}; line-height:1.1;">{val_rec_label}</div></div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:22px;'></div>", unsafe_allow_html=True)
    r2_c1, r2_c2, r2_c3 = st.columns([1.3, 1.3, 1.4])

    with r2_c1:
        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px; padding:14px; min-height:315px; display:flex; flex-direction:column; justify-content:space-between;">
    <div style="font-size:14px; font-weight:bold; color:#94A3B8; letter-spacing:0.5px;">FAIR VALUE RANGE — DCF vs P/E RELATIVE</div>
    <div style="display:grid; grid-template-columns: 1fr 1.1fr 1fr; gap:6px; margin-top:6px;">
    <div style="background:#151E2F; border:1px solid #1E293B; border-radius:8px; padding:8px 4px; text-align:center;">
    <div style="color:#38BDF8; font-size:13.5px; font-weight:bold;">Lower Estimate</div><div style="color:#64748B; font-size:12px;">Min(DCF, P/E)</div>
    <div style="color:#F8FAFC; font-size:16px; font-weight:bold; margin-top:4px;">{val_bear:.2f} <span style="font-size:12px; color:#64748B;">THB</span></div></div>
    <div style="background:#151E2F; border:1.5px solid #8B5CF6; border-radius:8px; padding:8px 4px; text-align:center;">
    <div style="color:#C084FC; font-size:13.5px; font-weight:bold;">Blended Fair Value</div><div style="color:#94A3B8; font-size:12px;">55% DCF + 45% P/E</div>
    <div style="color:#FFFFFF; font-size:16.5px; font-weight:bold; margin-top:4px;">{val_base:.2f} <span style="font-size:12px; color:#94A3B8;">THB</span></div></div>
    <div style="background:#151E2F; border:1px solid #1E293B; border-radius:8px; padding:8px 4px; text-align:center;">
    <div style="color:#10B981; font-size:13.5px; font-weight:bold;">Upper Estimate</div><div style="color:#64748B; font-size:12px;">Max(DCF, P/E)</div>
    <div style="color:#F8FAFC; font-size:16px; font-weight:bold; margin-top:4px;">{val_bull:.2f} <span style="font-size:12px; color:#64748B;">THB</span></div></div>
    </div>
    <div style="background:rgba(16,185,129,0.08); border-radius:6px; padding:6px 8px; display:flex; align-items:flex-start; gap:6px; margin-top:10px;">
    <span style="color:#10B981; font-size:14.5px;">✔</span><div style="font-size:12.5px; color:#CBD5E1; line-height:1.3;">
    <b>DCF Fair Value: {safe(ctx.stock_info.get('dcf_fair_value')):.2f} THB &nbsp;|&nbsp; P/E Fair Value: {safe(ctx.stock_info.get('pe_fair_value')):.2f} THB</b><br>
    <span style="color:#94A3B8;">คำนวณจากงบการเงินปีล่าสุด (FY{int(ctx.fin_stock['year'].max()) if not ctx.fin_stock.empty else '-'}) เทียบราคาตลาดปัจจุบัน {val_cur_price:.2f} THB</span></div></div>
    </div>""", unsafe_allow_html=True)

    with r2_c2:
        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px; padding:14px; min-height:315px; display:flex; flex-direction:column; justify-content:space-between;">
    <div style="font-size:14px; font-weight:bold; color:#94A3B8; letter-spacing:0.5px;">VALUATION DRIVERS ({ctx.selected_ticker})</div>
    <div style="font-size:13px; color:#CBD5E1; line-height:1.45; display:flex; flex-direction:column; gap:6px; margin:auto 0;">
    <div style="display:flex; gap:6px;"><span style="color:#10B981;">✔</span><div><b>Fair Value (Blended): {val_base:.2f} THB</b><br><span style="color:#64748B; font-size:12.5px;">ประเมินแบบผสมผสาน DCF + Relative P/E</span></div></div>
    <div style="display:flex; gap:6px;"><span style="color:#10B981;">✔</span><div><b>Margin of Safety: {val_mos:.1f}%</b><br><span style="color:#64748B; font-size:12.5px;">ส่วนต่างความปลอดภัยจากราคาตลาดปัจจุบัน</span></div></div>
    <div style="display:flex; gap:6px;"><span style="color:#10B981;">✔</span><div><b>P/E Ratio ปัจจุบัน: {fmt_ratio(ctx.stock_info.get('pe_ratio'), suffix='')} เท่า</b><br><span style="color:#64748B; font-size:12.5px;">เทียบ EPS ล่าสุด {ctx.stock_info.get('eps','-')} บาท/หุ้น</span></div></div>
    <div style="display:flex; gap:6px;"><span style="color:#10B981;">✔</span><div><b>สถานะมูลค่า: {val_status}</b><br><span style="color:#64748B; font-size:12.5px;">ระดับความน่าดึงดูดเชิงมูลค่าพื้นฐาน</span></div></div>
    </div></div>""", unsafe_allow_html=True)

    with r2_c3:
        safety_score = int(min(100, max(20, int(val_mos + 50))))
        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px; padding:14px; min-height:315px; display:flex; flex-direction:column; justify-content:space-between;">
    <div style="font-size:14px; font-weight:bold; color:#94A3B8; letter-spacing:0.5px;">FAIR VALUE SCORE BY DIMENSION</div>
    <div style="display:flex; flex-direction:column; gap:10px; margin:auto 0;">
    <div><div style="display:flex; justify-content:space-between; font-size:13px; color:#CBD5E1; margin-bottom:3px;"><span>📊 Relative Valuation (P/E)</span><span style="font-weight:bold; color:#F8FAFC;">{val_score} <span style="font-size:12px; color:#64748B;">/100</span></span></div>
    <div style="background:#1E293B; height:9px; border-radius:4px; overflow:hidden;"><div style="background:#10B981; width:{val_score}%; height:100%;"></div></div></div>
    <div><div style="display:flex; justify-content:space-between; font-size:13px; color:#CBD5E1; margin-bottom:3px;"><span>🎯 Intrinsic Valuation (DCF)</span><span style="font-weight:bold; color:#F8FAFC;">{val_score} <span style="font-size:12px; color:#64748B;">/100</span></span></div>
    <div style="background:#1E293B; height:9px; border-radius:4px; overflow:hidden;"><div style="background:#10B981; width:{val_score}%; height:100%;"></div></div></div>
    <div><div style="display:flex; justify-content:space-between; font-size:13px; color:#CBD5E1; margin-bottom:3px;"><span>🛡️ Margin of Safety</span><span style="font-weight:bold; color:#F8FAFC;">{safety_score} <span style="font-size:12px; color:#64748B;">/100</span></span></div>
    <div style="background:#1E293B; height:9px; border-radius:4px; overflow:hidden;"><div style="background:#10B981; width:{safety_score}%; height:100%;"></div></div></div>
    </div>
    <div style="display:flex; justify-content:space-between; align-items:center; border-top:1px solid #1E293B; padding-top:8px;">
    <span style="font-size:13.5px; font-weight:bold; color:#CBD5E1;">OVERALL FAIR VALUE SCORE</span><span style="font-size:18.5px; font-weight:bold; color:{val_color};">{val_score} <span style="font-size:13px; color:#64748B;">/100</span></span>
    </div></div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:22px;'></div>", unsafe_allow_html=True)
    st.markdown("""<div style="font-size:14.5px; font-weight:bold; color:#94A3B8; letter-spacing:0.5px; margin-bottom:8px;">DETAIL BREAKDOWN</div>""", unsafe_allow_html=True)
    d_c1, d_c2, d_c3, d_c4 = st.columns(4)

    with d_c1:
        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:10px; padding:12px; min-height:190px; display:flex; flex-direction:column; justify-content:space-between;">
    <div><div style="font-size:13px; font-weight:bold; color:#CBD5E1;">RELATIVE VALUATION (P/E)</div>
    <table style="width:100%; font-size:13px; color:#CBD5E1; border-collapse:collapse; margin-top:6px;">
    <tr style="border-bottom:1px solid #1E293B; color:#64748B; font-size:12.5px;"><th style="text-align:left; padding:2px 0;">Metric</th><th>Value</th></tr>
    <tr style="border-bottom:1px solid #1E293B;"><td style="padding:3px 0;">P/E Ratio ปัจจุบัน</td><td>{fmt_ratio(ctx.stock_info.get('pe_ratio'))}</td></tr>
    <tr><td style="padding:3px 0;">P/E Fair Value</td><td>{safe(ctx.stock_info.get('pe_fair_value')):.2f} THB</td></tr>
    </table></div></div>""", unsafe_allow_html=True)

    with d_c2:
        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:10px; padding:12px; min-height:190px; display:flex; flex-direction:column; justify-content:space-between;">
    <div><div style="font-size:13px; font-weight:bold; color:#CBD5E1;">INTRINSIC VALUATION (DCF)</div>
    <table style="width:100%; font-size:13px; color:#CBD5E1; border-collapse:collapse; margin-top:6px;">
    <tr style="border-bottom:1px solid #1E293B; color:#64748B; font-size:12.5px;"><th style="text-align:left; padding:2px 0;">Metric</th><th>Value</th></tr>
    <tr style="border-bottom:1px solid #1E293B;"><td style="padding:3px 0;">WACC</td><td>8.2%</td></tr>
    <tr><td style="padding:3px 0;">DCF Fair Value</td><td>{safe(ctx.stock_info.get('dcf_fair_value')):.2f} THB</td></tr>
    </table></div></div>""", unsafe_allow_html=True)

    with d_c3:
        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:10px; padding:12px; min-height:190px; display:flex; flex-direction:column; justify-content:space-between;">
    <div><div style="font-size:13px; font-weight:bold; color:#CBD5E1;">PRICE COMPARISON</div>
    <table style="width:100%; font-size:13px; color:#CBD5E1; border-collapse:collapse; margin-top:6px;">
    <tr style="border-bottom:1px solid #1E293B;"><td style="padding:3px 0;">Current</td><td>{val_cur_price:.2f}</td></tr>
    <tr style="border-bottom:1px solid #1E293B;"><td style="padding:3px 0;">Fair Value</td><td>{val_base:.2f}</td></tr>
    <tr><td style="padding:3px 0;">Difference</td><td>{(val_base - val_cur_price):+.2f}</td></tr>
    </table></div></div>""", unsafe_allow_html=True)

    with d_c4:
        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:10px; padding:12px; min-height:190px; display:flex; flex-direction:column; justify-content:space-between;">
    <div><div style="font-size:13px; font-weight:bold; color:#CBD5E1;">MARGIN OF SAFETY</div>
    <table style="width:100%; font-size:13px; color:#CBD5E1; border-collapse:collapse; margin-top:6px;">
    <tr><td style="padding:3px 0;">Margin of Safety</td><td style="color:{val_color}; font-weight:bold;">{val_mos:.1f}%</td></tr>
    </table></div></div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:22px;'></div>", unsafe_allow_html=True)
    r4_c1, r4_c2 = st.columns([1.3, 1.7])

    with r4_c1:
        st.markdown("""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px; padding:14px; min-height:220px; display:flex; flex-direction:column; justify-content:space-between;">
    <div style="font-size:13.5px; font-weight:bold; color:#94A3B8; letter-spacing:0.5px;">DCF ASSUMPTIONS</div>
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:6px; font-size:13px; color:#CBD5E1; margin:auto 0;">
    <div><span style="color:#64748B;">WACC</span><br><b style="color:#F8FAFC;">8.2%</b></div>
    <div><span style="color:#64748B;">Terminal Growth</span><br><b style="color:#F8FAFC;">2.0%</b></div>
    <div><span style="color:#64748B;">Forecast Period</span><br><b style="color:#F8FAFC;">1 Year FCF x1.05</b></div>
    <div><span style="color:#64748B;">Target P/E</span><br><b style="color:#F8FAFC;">18-22x (by sector)</b></div>
    <div><span style="color:#64748B;">DCF Weight</span><br><b style="color:#F8FAFC;">55%</b></div>
    <div><span style="color:#64748B;">P/E Weight</span><br><b style="color:#F8FAFC;">45%</b></div>
    </div></div>""", unsafe_allow_html=True)

    with r4_c2:
        st.markdown("""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px 12px 0 0; padding:12px 16px 0 16px;">
    <div style="font-size:13.5px; font-weight:bold; color:#94A3B8; letter-spacing:0.5px;">HISTORICAL FAIR VALUE VS PRICE (Actual, year-end 2023-2025)</div></div>""", unsafe_allow_html=True)

        fv_hist = ctx.fair_value_yearly_df[ctx.fair_value_yearly_df['ticker'] == ctx.selected_ticker].sort_values('year') if not ctx.fair_value_yearly_df.empty else pd.DataFrame()
        if not fv_hist.empty:
            fig_hist_val = go.Figure()
            fig_hist_val.add_trace(go.Scatter(x=fv_hist['year'].astype(str), y=fv_hist['fair_value'], mode='lines+markers', name='Fair Value', line=dict(color='#A855F7', width=1.8, dash='dash')))
            fig_hist_val.add_trace(go.Scatter(x=fv_hist['year'].astype(str), y=fv_hist['price'], mode='lines+markers', name='Actual Price', line=dict(color='#38BDF8', width=2), marker=dict(size=9, color='#38BDF8')))
            fig_hist_val.update_layout(
                height=150, margin=dict(l=25, r=15, t=10, b=20), paper_bgcolor="#0F172A", plot_bgcolor="#0F172A",
                yaxis=dict(tickfont=dict(size=11.5, color="#64748B"), gridcolor="#1E293B", zeroline=False),
                xaxis=dict(tickfont=dict(size=11, color="#94A3B8"), gridcolor="#1E293B"),
                legend=dict(orientation="h", yanchor="bottom", y=-0.35, xanchor="center", x=0.5, font=dict(size=11.5, color="#94A3B8"))
            )
            show_chart(fig_hist_val, key="fair_value_hist", expand_height=650)
        else:
            st.info("ไม่มีข้อมูลย้อนหลังเพียงพอ")

    render_nav_footer("m2", prev_page=" 💚 Company Health", next_page=" ⏱️ Entry Timing")

