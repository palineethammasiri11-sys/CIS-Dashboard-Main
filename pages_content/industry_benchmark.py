"""
pages_content/industry_benchmark.py
-------------------------------
หน้า "Industry Benchmark" ของ CIS Dashboard

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
    n_sector = len(ctx.sector_peers)
    sector_rank = int(ctx.stock_info.get('sector_rank', 1))
    overall_rank = int(ctx.stock_info.get('overall_rank', 1))
    n_all = len(ctx.scores_df)
    pct_in_sector = round((sector_rank / max(n_sector, 1)) * 100)

    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:15px; border-bottom:1px solid #1E293B; padding-bottom:10px;">
        <div><div style="font-size:14.5px; color:#64748B; margin-bottom:2px;">Home / Module 6 / Industry Benchmark</div>
        <div style="display:flex; align-items:baseline; gap:10px;"><h2 style="margin:0; color:#F8FAFC; font-size:23px;">INDUSTRY BENCHMARK</h2>
        <span style="font-size:18.5px; color:#A855F7; font-weight:bold;">{ctx.selected_ticker} ⭐</span>
        <span style="font-size:15px; color:#64748B;">{ctx.stock_info.get('sector','-')}</span></div></div>
        <div style="text-align:right; display:flex; gap:20px;">
        <div><span style="font-size:13.5px; color:#64748B;">Current Price</span><br><b style="color:{ctx.change_color}; font-size:16.5px;">{ctx.current_price:.2f} THB</b> <span style="color:{ctx.change_color}; font-size:13.5px;">({ctx.change_sign}{ctx.change_pct:.2f}%) {ctx.arrow_sign}</span></div>
        <div><span style="font-size:13.5px; color:#64748B;">Sector</span><br><b style="color:#CBD5E1; font-size:15px;">{ctx.stock_info.get('sector','-')}</b></div>
        <div><span style="font-size:13.5px; color:#64748B;">Universe</span><br><b style="color:#CBD5E1; font-size:15px;">{n_all} หุ้นที่ติดตาม (2023-2025)</b></div>
        </div>
    </div>""", unsafe_allow_html=True)

    r1_c1, r1_c2, r1_c3 = st.columns([1.1, 0.8, 2.1])

    with r1_c1:
        single_member_sector = n_sector < 2
        if single_member_sector:
            position_label = "INDUSTRY LEADER" if overall_rank == 1 else ("STRONG COMPETITOR" if overall_rank <= max(2, n_all // 2) else "LAGGING PEER")
            pos_stars = 5 if overall_rank == 1 else (4 if overall_rank <= max(2, n_all // 2) else 2)
        else:
            position_label = "INDUSTRY LEADER" if sector_rank == 1 else ("STRONG COMPETITOR" if sector_rank <= max(2, n_sector // 2) else "LAGGING PEER")
            pos_stars = 5 if sector_rank == 1 else (4 if sector_rank <= max(2, n_sector // 2) else 2)
        st.markdown(f"""<div style="background-color:#151E2F; border:1px solid #1E293B; border-radius:8px; padding:14px; height:360px; display:flex; flex-direction:column; justify-content:space-between;">
    <div style="font-size:14.5px; color:#94A3B8; font-weight:bold; margin-bottom:8px;">STRATEGIC INVESTMENT POSITION</div>
    <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; gap:14px; flex-grow:1;">
    <div style="background:rgba(168,85,247,0.15); border:2px solid #A855F7; border-radius:50%; width:100px; height:100px; display:flex; align-items:center; justify-content:center; font-size:44px;">🏆</div>
    <div style="text-align:center;">
    <div style="color:#C084FC; font-size:26px; font-weight:bold;">{position_label}</div>
    <div style="color:#A855F7; font-size:22px; letter-spacing:4px; margin-top:6px;">{'★'*pos_stars}{'☆'*(5-pos_stars)}</div>
    </div>
    </div>
    <p style="color:#94A3B8; font-size:13.5px; line-height:1.4; margin:0;">อันดับที่ {sector_rank} จาก {n_sector} บริษัทในกลุ่ม {ctx.stock_info.get('sector','-')} จาก Overall Score = {safe(ctx.stock_info.get('overall_score')):.1f}/100</p>
    </div>""", unsafe_allow_html=True)
        
    with r1_c2:
        pct_overall = round((overall_rank / max(n_all, 1)) * 100)
        sector_block = f"""<span style="display:inline-block; margin-top:6px; background-color:rgba(100,116,139,0.15); color:#94A3B8; font-size:14px; font-weight:bold; padding:3px 14px; border-radius:8px;">กลุ่มมีเพียง 1 หุ้น</span>""" if single_member_sector else f"""<span style="display:inline-block; margin-top:6px; background-color:rgba(245,158,11,0.15); color:#F59E0B; font-size:14px; font-weight:bold; padding:3px 14px; border-radius:8px;">Top {pct_in_sector}%</span>"""

        st.markdown(f"""<div style="background-color:#151E2F; border:1px solid #1E293B; border-radius:8px; padding:14px; height:360px; text-align:center; display:flex; flex-direction:column; justify-content:space-between;">
    <div style="font-size:14.5px; color:#94A3B8; font-weight:bold;">RANKING</div>
    <div style="border-bottom:1px solid #1E293B; padding-bottom:10px; flex-grow:1; display:flex; flex-direction:column; justify-content:center;">
    <div style="font-size:14px; color:#64748B;">ในกลุ่ม</div>
    <div style="font-size:13px; color:#94A3B8; margin-bottom:4px;">{ctx.stock_info.get('sector','-')}</div>
    <div><span style="font-size:32px; color:#F8FAFC; font-weight:bold;">{sector_rank}</span> <span style="font-size:14px; color:#64748B;">/ {n_sector} หุ้น</span></div>
    {sector_block}
    </div>
    <div style="flex-grow:1; display:flex; flex-direction:column; justify-content:center;">
    <div style="font-size:14px; color:#64748B;">ทั้งตลาด</div>
    <div style="font-size:13px; color:#94A3B8; margin-bottom:4px;">{n_all} หุ้นที่ติดตาม</div>
    <div><span style="font-size:32px; color:#F8FAFC; font-weight:bold;">{overall_rank}</span> <span style="font-size:14px; color:#64748B;">/ {n_all} หุ้น</span></div>
    <span style="display:inline-block; margin-top:6px; background-color:rgba(56,189,248,0.15); color:#38BDF8; font-size:14px; font-weight:bold; padding:3px 14px; border-radius:8px;">Top {pct_overall}%</span>
    </div>
    </div>""", unsafe_allow_html=True)
        
    with r1_c3:
        def calc_pct(df, col):
            s = df[col].rank(pct=True)
            match = df['ticker'] == ctx.selected_ticker
            if not match.any():
                return 50
            return int(round(100 - s[match].values[0] * 100))

        dims_cols = [
            ("Profitability", 'health_score', "#10B981"),
            ("Growth", 'revenue_growth_yoy', "#3B82F6"),
            ("Valuation", 'valuation_score', "#F59E0B"),
            ("Entry Timing", 'timing_score', "#10B981"),
            ("Risk (safer)", 'risk_score', "#F59E0B"),
            ("AI Prediction", 'ai_score', "#A855F7"),
        ]

        def build_dims(df):
            result = []
            for label, col, color in dims_cols:
                if col == 'revenue_growth_yoy' and ctx.stock_info.get('revenue_growth_yoy') is None:
                    pct = 50
                else:
                    pct = calc_pct(df, col)
                result.append((label, pct, color))
            return result

        dims_market = build_dims(ctx.scores_df)

        def dim_pct_card(label, pct, color):
            tier = "Excellent" if pct <= 20 else ("Good" if pct <= 45 else ("Fair" if pct <= 70 else "Weak"))
            return f"""<div style="background:#0F172A; padding:6px 2px; border-radius:6px; border:1px solid #1E293B;">
    <div style="color:#94A3B8; font-size:12px;">{label}</div><div style="color:{color}; font-size:15px; font-weight:bold; margin:2px 0;">Top {max(pct,1)}%</div>
    <div style="color:{color}; font-size:12px;">{tier}</div></div>"""

        if single_member_sector:
            sector_section = f"""<div style="background:rgba(100,116,139,0.08); border:1px dashed #334155; border-radius:8px; padding:14px; text-align:center; margin-bottom:16px;">
    <div style="color:#94A3B8; font-size:13px; line-height:1.4;">กลุ่ม <b>{ctx.stock_info.get('sector','-')}</b> มีเพียง 1 หุ้น จึงไม่สามารถเปรียบเทียบ percentile ภายในกลุ่มได้อย่างมีความหมาย</div>
    </div>"""
        else:
            dims_sector = build_dims(ctx.sector_peers)
            sector_section = f"""<div style="font-size:12.5px; color:#CBD5E1; margin-bottom:6px;">เปรียบเทียบกับกลุ่มอุตสาหกรรม {ctx.stock_info.get('sector','-')} ({n_sector} หุ้น)</div>
    <div style="display:grid; grid-template-columns: repeat(6, 1fr); gap:6px; text-align:center; margin-bottom:16px;">
    {''.join([dim_pct_card(l, p, c) for l, p, c in dims_sector])}
    </div>"""

        st.markdown(f"""<div style="background-color:#151E2F; border:1px solid #1E293B; border-radius:8px; padding:14px; height:360px; display:flex; flex-direction:column; justify-content:space-between;">
    <div>
    <div style="font-size:14.5px; color:#94A3B8; font-weight:bold; margin-bottom:10px;">DIMENSION PERCENTILE RANK</div>
    {sector_section}
    </div>
    <div style="border-top:1px dashed #334155; margin-bottom:12px;"></div>
    <div>
    <div style="font-size:12.5px; color:#CBD5E1; margin-bottom:6px;">เปรียบเทียบกับหุ้นทั้ง {n_all} ตัว</div>
    <div style="display:grid; grid-template-columns: repeat(6, 1fr); gap:6px; text-align:center;">
    {''.join([dim_pct_card(l, p, c) for l, p, c in dims_market])}
    </div>
    </div>
    </div>""", unsafe_allow_html=True)
        
    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
    r2_c1, r2_c2, r2_c3 = st.columns([2.0, 1.0, 1.1])

    with r2_c1:
        peers_sorted = ctx.sector_peers.sort_values('overall_score', ascending=False)

        def badge(val, thresholds, labels, colors):
            for th, lab, col in zip(thresholds, labels, colors):
                if val >= th:
                    return f'<span style="color:{col}; font-weight:bold;">{lab}</span>'
            return f'<span style="color:{colors[-1]};">{labels[-1]}</span>'

        rows_html = ""
        for _, p in peers_sorted.iterrows():
            is_sel = p['ticker'] == ctx.selected_ticker
            row_bg = "background:rgba(168,85,247,0.08);" if is_sel else ""
            star_n = min(5, max(1, round(safe(p['overall_score']) / 20)))
            health_b = badge(p['health_score'], [70, 45, 0], ["Excellent", "Good", "Weak"], ["#10B981", "#3B82F6", "#EF4444"])
            val_b = "Undervalued" if p['margin_of_safety'] > 10 else ("Overvalued" if p['margin_of_safety'] < -10 else "Fair Value")
            val_c = "#10B981" if p['margin_of_safety'] > 10 else ("#EF4444" if p['margin_of_safety'] < -10 else "#94A3B8")
            timing_b = badge(p['timing_score'], [65, 45, 0], ["Good Entry", "Neutral", "Bad Entry"], ["#10B981", "#F59E0B", "#EF4444"])
            ai_b = badge(p['ai_score'], [65, 45, 0], ["Bullish", "Neutral", "Bearish"], ["#10B981", "#94A3B8", "#EF4444"])
            risk_b = "Low" if p['risk_score'] >= 65 else ("Medium" if p['risk_score'] >= 40 else "High")
            risk_c = "#10B981" if p['risk_score'] >= 65 else ("#F59E0B" if p['risk_score'] >= 40 else "#EF4444")
            name_disp = f"⭐ {p['ticker']}" if is_sel else p['ticker']
            name_c = "#C084FC" if is_sel else "#F8FAFC"
            rows_html += f"""<tr style="border-bottom:1px solid #1E293B; {row_bg}">
    <td style="text-align:left; padding:6px 0; color:{name_c}; font-weight:bold;">{name_disp}</td>
    <td>{health_b}</td><td><span style="color:{val_c};">{val_b}</span></td><td>{timing_b}</td><td>{ai_b}</td>
    <td><span style="color:{risk_c};">{risk_b}</span></td><td style="color:#A855F7; letter-spacing:1px;">{'★'*star_n}{'☆'*(5-star_n)}</td></tr>"""

        st.markdown(f"""<div style="background-color:#151E2F; border:1px solid #1E293B; border-radius:8px; padding:14px; height:350px;">
    <div style="font-size:14.5px; color:#94A3B8; font-weight:bold; margin-bottom:6px;">PEER COMPARISON — {ctx.stock_info.get('sector','-')} ({n_sector} หุ้น)</div>
    <table style="width:100%; text-align:center; font-size:14px; color:#CBD5E1; border-collapse:collapse;">
    <tr style="border-bottom:1px solid #1E293B; color:#64748B; font-size:13px;"><th style="text-align:left; padding:5px 0;">Company</th><th>Health</th><th>Fair Value</th><th>Entry Timing</th><th>AI Prediction</th><th>Risk</th><th>Overall</th></tr>
    {rows_html}
    </table>
    <div style="font-size:12.5px; color:#64748B; margin-top:6px;">*จัดอันดับจาก Overall Score ที่คำนวณจริงจากข้อมูลใน cis_summary_scores</div>
    </div>""", unsafe_allow_html=True)
            
    with r2_c2:
        cats = ['Health', 'Valuation', 'Timing', 'AI Pred.', 'Risk', 'Industry']
        stock_vals = [safe(ctx.stock_info.get('health_score')), safe(ctx.stock_info.get('valuation_score')), safe(ctx.stock_info.get('timing_score')),
                      safe(ctx.stock_info.get('ai_score')), safe(ctx.stock_info.get('risk_score')), safe(ctx.stock_info.get('industry_score'))]
        sector_avg_vals = [ctx.sector_peers['health_score'].mean(), ctx.sector_peers['valuation_score'].mean(), ctx.sector_peers['timing_score'].mean(),
                            ctx.sector_peers['ai_score'].mean(), ctx.sector_peers['risk_score'].mean(), ctx.sector_peers['industry_score'].mean()]
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(r=stock_vals, theta=cats, fill='toself', fillcolor='rgba(168,85,247,0.3)', line=dict(color='#A855F7', width=2), name=ctx.selected_ticker))
        fig_radar.add_trace(go.Scatterpolar(r=sector_avg_vals, theta=cats, line=dict(color='#64748B', width=1.5, dash='dash'), name='Sector Avg'))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100], showticklabels=False, linecolor="#1E293B", gridcolor="#1E293B"),
                       angularaxis=dict(linecolor="#1E293B", gridcolor="#1E293B", tickfont=dict(size=11.5, color="#94A3B8"))),
            paper_bgcolor="#151E2F", plot_bgcolor="#151E2F", height=310, margin=dict(l=25, r=25, t=30, b=15),
            title=dict(text="RADAR: STOCK vs SECTOR AVG", font=dict(size=13.5, color="#94A3B8"), x=0.05, y=0.98),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11.5, color="#CBD5E1"))
        )
        show_chart(fig_radar, key="industry_radar", expand_height=650)

    with r2_c3:
        matrix_df = ctx.scores_df[['ticker', 'health_score', 'overall_score']].copy()
        matrix_df.columns = ['Company', 'Business_Quality', 'Investment_Attract']
        color_map = {t: ('#C084FC' if t == ctx.selected_ticker else '#38BDF8') for t in matrix_df['Company']}
        fig_matrix = px.scatter(matrix_df, x='Business_Quality', y='Investment_Attract', text='Company', color='Company', color_discrete_map=color_map)
        fig_matrix.update_traces(textposition='top center', marker=dict(size=13, line=dict(width=1, color='white')))
        fig_matrix.add_hline(y=50, line_width=1, line_dash="dash", line_color="#334155")
        fig_matrix.add_vline(x=50, line_width=1, line_dash="dash", line_color="#334155")
        fig_matrix.add_annotation(x=25, y=95, text="💎 Hidden Gem", showarrow=False, font=dict(size=11.5, color="#34D399"))
        fig_matrix.add_annotation(x=80, y=95, text="🏆 Market Leader", showarrow=False, font=dict(size=11.5, color="#C084FC"))
        fig_matrix.add_annotation(x=25, y=10, text="⚠️ Value Trap", showarrow=False, font=dict(size=11.5, color="#F87171"))
        fig_matrix.add_annotation(x=80, y=10, text="⭐ Competitive", showarrow=False, font=dict(size=11, color="#FBBF24"))
        fig_matrix.update_layout(
            paper_bgcolor="#151E2F", plot_bgcolor="#0F172A", height=310, margin=dict(l=15, r=15, t=30, b=15),
            title=dict(text="STRATEGIC MATRIX (All 8 Stocks)", font=dict(size=13.5, color="#94A3B8"), x=0.05, y=0.98),
            xaxis=dict(title=dict(text="Business Quality (Health Score) →", font=dict(size=11.5, color="#64748B")), range=[0, 100], showgrid=False, showticklabels=False),
            yaxis=dict(title=dict(text="Investment Attractiveness (Overall) →", font=dict(size=11.5, color="#64748B")), range=[0, 100], showgrid=False, showticklabels=False),
            showlegend=False
        )
        show_chart(fig_matrix, key="industry_matrix", expand_height=650)

    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
    r3_c1, r3_c2, r3_c3 = st.columns([1.3, 1.5, 1.2])

    with r3_c1:
        compare_df = ctx.scores_df if single_member_sector else ctx.sector_peers
        strengths_ib, weaknesses_ib = [], []
        if ctx.stock_info['health_score'] > compare_df['health_score'].mean(): strengths_ib.append("Health Score สูงกว่าค่าเฉลี่ย")
        if ctx.stock_info['ai_score'] > compare_df['ai_score'].mean(): strengths_ib.append("AI Prediction Score สูงกว่าค่าเฉลี่ย")
        if safe(ctx.stock_info.get('revenue_growth_yoy')) > 0: strengths_ib.append(f"รายได้เติบโต {safe(ctx.stock_info.get('revenue_growth_yoy')):.1f}% YoY")
        if not strengths_ib: strengths_ib.append("ผลประกอบการยังอยู่ระหว่างพัฒนาเทียบกลุ่ม")
        if ctx.stock_info['valuation_score'] < compare_df['valuation_score'].mean(): weaknesses_ib.append("Valuation แพงกว่าค่าเฉลี่ย")
        if ctx.stock_info['risk_score'] < compare_df['risk_score'].mean(): weaknesses_ib.append("ความเสี่ยงสูงกว่าค่าเฉลี่ย")
        if ctx.stock_info['health_score'] < compare_df['health_score'].mean(): weaknesses_ib.append("Health Score ต่ำกว่าค่าเฉลี่ย")
        if ctx.stock_info['ai_score'] < compare_df['ai_score'].mean(): weaknesses_ib.append("AI Prediction Score ต่ำกว่าค่าเฉลี่ย")
        if not weaknesses_ib: weaknesses_ib.append("ไม่พบจุดอ่อนเชิงเปรียบเทียบที่ชัดเจน")
        st.markdown(f"""<div style="background-color:#151E2F; border:1px solid #1E293B; border-radius:8px; padding:14px; height:275px;">
    <div style="font-size:14.5px; color:#94A3B8; font-weight:bold; margin-bottom:6px;">COMPETITIVE ADVANTAGE</div>
    <div style="font-size:13px; color:#10B981; font-weight:bold; margin-bottom:2px;">STRENGTHS</div>
    <ul style="color:#CBD5E1; font-size:13.5px; line-height:1.4; padding-left:14px; margin:0 0 6px 0;">{''.join([f'<li>{s}</li>' for s in strengths_ib])}</ul>
    <div style="font-size:13px; color:#EF4444; font-weight:bold; margin-bottom:2px;">WEAKNESSES / RISKS</div>
    <ul style="color:#CBD5E1; font-size:13.5px; line-height:1.4; padding-left:14px; margin:0;">{''.join([f'<li>{w}</li>' for w in weaknesses_ib])}</ul>
    </div>""", unsafe_allow_html=True)

    with r3_c2:
        compare_desc = f"เทียบกับทั้ง {n_all} หุ้นที่ติดตาม (กลุ่มมีตัวเดียว)" if single_member_sector else "เทียบกับบริษัทในกลุ่มเดียวกัน"
        avg_label = "Overall avg" if single_member_sector else "Sector avg"
        st.markdown(f"""<div style="background-color:#151E2F; border:1px solid #1E293B; border-radius:8px; padding:14px; height:275px;">
    <div style="font-size:14.5px; color:#94A3B8; font-weight:bold; margin-bottom:6px;">EXPLAINABLE AI SUMMARY</div>
    <p style="color:#CBD5E1; font-size:14px; line-height:1.4; margin:0 0 8px 0;">
    <b>{ctx.selected_ticker}</b> อยู่อันดับที่ <b>{sector_rank}</b> จาก {n_sector} บริษัทในกลุ่ม {ctx.stock_info.get('sector','-')} (Overall Score {safe(ctx.stock_info.get('overall_score')):.1f}/100) {compare_desc}:</p>
    <div style="color:#CBD5E1; font-size:13.5px; line-height:1.5;">
    <div><span style="color:#10B981;">✔</span> Health Score: {safe(ctx.stock_info.get('health_score')):.1f} ({avg_label} {compare_df['health_score'].mean():.1f})</div>
    <div><span style="color:#10B981;">✔</span> Valuation Score: {safe(ctx.stock_info.get('valuation_score')):.1f} ({avg_label} {compare_df['valuation_score'].mean():.1f})</div>
    <div><span style="color:#10B981;">✔</span> AI Prediction Score: {safe(ctx.stock_info.get('ai_score')):.1f} ({avg_label} {compare_df['ai_score'].mean():.1f})</div>
    <div><span style="color:#10B981;">✔</span> Risk Score: {safe(ctx.stock_info.get('risk_score')):.1f} ({avg_label} {compare_df['risk_score'].mean():.1f})</div>
    </div></div>""", unsafe_allow_html=True)

    with r3_c3:
        rec = ctx.stock_info.get('recommendation', 'ACCUMULATE')
        rec_color2 = {"STRONG BUY": "#10B981", "BUY": "#10B981", "ACCUMULATE": "#84CC16", "REDUCE / SELL": "#EF4444"}.get(rec, "#F59E0B")
        conf_lvl = "High" if abs(safe(ctx.stock_info.get('margin_of_safety'))) > 15 else "Medium"
        st.markdown(f"""<div style="background-color:#151E2F; border:1px solid #1E293B; border-radius:8px; padding:14px; height:275px; text-align:center;">
    <div style="font-size:14.5px; color:#94A3B8; font-weight:bold; margin-bottom:4px; text-align:left;">FINAL RECOMMENDATION</div>
    <div style="display:flex; justify-content:center; align-items:center; gap:8px; margin:4px 0;">
    <div><h1 style="color:{rec_color2}; margin:0; font-size:24px; line-height:1.1;">{rec}</h1></div></div>
    <div style="text-align:left; font-size:13.5px; margin-top:8px; border-top:1px dashed #334155; padding-top:6px;">
    <div style="display:flex; justify-content:space-between; margin-bottom:3px;"><span style="color:#94A3B8;">Confidence Level</span><span style="color:{rec_color2}; font-weight:bold;">{conf_lvl}</span></div>
    <div style="display:flex; justify-content:space-between; margin-bottom:3px;"><span style="color:#94A3B8;">Overall Score</span><span style="color:#F59E0B; font-weight:bold;">{safe(ctx.stock_info.get('overall_score')):.1f}/100</span></div>
    <div style="display:flex; justify-content:space-between; margin-bottom:3px;"><span style="color:#94A3B8;">Sector Rank</span><span style="color:#F59E0B; font-weight:bold;">{sector_rank} / {n_sector}</span></div>
    </div></div>""", unsafe_allow_html=True)

    import base64
    csv_text = ctx.scores_df[ctx.scores_df['ticker'] == ctx.selected_ticker].to_csv(index=False)
    b64_csv = base64.b64encode(csv_text.encode('utf-8-sig')).decode()
    download_link = f'data:file/csv;base64,{b64_csv}'

    st.markdown(f"""<div style="display:flex; justify-content:space-between; align-items:center; background-color:#151E2F; border:1px solid #1E293B; border-radius:8px; padding:10px 14px; margin-top:12px;">
    <div style="font-size:14px; color:#CBD5E1;"><b>EXPORT & INDUSTRY DATA</b><br><span style="color:#94A3B8; font-size:13px;">ดาวน์โหลดคะแนนวิเคราะห์ทั้งหมดของ {ctx.selected_ticker} (ข้อมูลจริงจาก cis_summary_scores)</span></div>
    <a href="{download_link}" download="{ctx.selected_ticker}_CIS_Analysis.csv" style="background:#3B82F6; color:white; border:none; padding:6px 14px; border-radius:6px; font-size:13px; text-decoration:none; display:inline-block; font-weight:bold; cursor:pointer;">📥 Export Data (CSV)</a>
    </div>""", unsafe_allow_html=True)

    render_nav_footer("m6", prev_page=" 🛡️ Risk Analysis", next_page=None)
