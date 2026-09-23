"""
pages_content/risk_analysis.py
--------------------------
หน้า "Risk Analysis" ของ CIS Dashboard

วิธีทดสอบหน้านี้แบบเดี่ยว (ไม่ต้องรอทีมคนอื่น):
    streamlit run preview_my_page.py
    (แล้วเลือกโมดูลนี้จาก dropdown ในไฟล์ preview_my_page.py)
"""
import streamlit as st
import pandas as pd
import numpy as np
import math
import plotly.graph_objects as go
from common import safe, show_chart, render_nav_footer


def _fmt_or_na(val, spec="{:.2f}", na="N/A"):
    if _is_missing(val):
        return na
    return spec.format(val)


def _is_missing(val):
    if val is None:
        return True
    try:
        return bool(pd.isna(val))
    except (TypeError, ValueError):
        return False


def _fallback_cvar_95(stock_daily, confidence=0.95):
    try:
        closes = stock_daily['close'].astype(float)
        returns = closes.pct_change().dropna()
        if len(returns) < 20:
            return None
        cutoff = np.percentile(returns, (1 - confidence) * 100)
        tail = returns[returns <= cutoff]
        if tail.empty:
            return None
        return round(float(abs(tail.mean()) * 100), 2)
    except Exception:
        return None


def _fallback_psr(stock_daily, sr_benchmark=0.0):
    try:
        closes = stock_daily['close'].astype(float)
        r = closes.pct_change().dropna()
        n = len(r)
        if n < 30 or r.std() == 0:
            return None
        sr_hat = r.mean() / r.std()
        skew = r.skew()
        kurt = r.kurtosis() + 3
        denom_sq = 1 - skew * sr_hat + ((kurt - 1) / 4) * sr_hat ** 2
        if denom_sq <= 0:
            return None
        denom = math.sqrt(denom_sq)
        z = (sr_hat - sr_benchmark) * math.sqrt(n - 1) / denom
        psr = 0.5 * (1 + math.erf(z / math.sqrt(2)))
        return round(float(psr) * 100, 1)
    except Exception:
        return None


def render(ctx):
    raw_risk_score = ctx.stock_info.get('risk_score')
    risk_score_available = not _is_missing(raw_risk_score)
    risk_score = int(round(safe(raw_risk_score, 45))) if risk_score_available else None

    if risk_score_available:
        risk_status = "LOW RISK" if risk_score >= 65 else ("MODERATE RISK" if risk_score >= 40 else "HIGH RISK")
        risk_color = "#10B981" if risk_score >= 65 else ("#F59E0B" if risk_score >= 40 else "#EF4444")
    else:
        risk_status = "N/A"
        risk_color = "#64748B"

    beta_val = safe(ctx.stock_info.get('beta'), 1.0)
    vol_val = safe(ctx.stock_info.get('volatility'), 25.0)

    # คำนวณ Max Drawdown จากราคาปิดจริงสดๆ ทันที
    if not ctx.stock_daily.empty and 'close' in ctx.stock_daily.columns:
        _closes = pd.to_numeric(ctx.stock_daily['close'], errors='coerce').dropna()
        _cum_max = _closes.cummax()
        _dd_series = (_closes - _cum_max) / _cum_max
        dd_val = round(abs(float(_dd_series.min())) * 100, 1)
    else:
        dd_val = safe(ctx.stock_info.get('max_drawdown'), 20.0)

    de_val_r = safe(ctx.stock_info.get('de_ratio'), 1.0)
    cr_val_r = safe(ctx.stock_info.get('current_ratio'), 1.2)

    st.markdown(f"""<div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:15px;">
    <div><div style="font-size:14.5px; color:#64748B; margin-bottom:2px;">Home / Module 5 / Risk Analysis</div>
    <div style="display:flex; align-items:baseline; gap:8px;"><h2 style="margin:0; font-size:23px; font-weight:bold; color:#F8FAFC; letter-spacing:0.5px;">RISK ANALYSIS</h2></div></div>
    <div style="text-align:right; display:flex; align-items:center; gap:16px;">
    <div><span style="font-size:13px; color:#64748B;">Analysis Date</span><br><b style="color:#CBD5E1; font-size:15px;">{ctx.stock_info.get('latest_date','-')}</b></div>
    <div><span style="font-size:13px; color:#64748B;">Data Period</span><br><b style="color:#CBD5E1; font-size:15px;">2023-2025 (3Y)</b></div>
    </div></div>""", unsafe_allow_html=True)

    r1_c1, r1_c2 = st.columns([1.15, 2.85])

    with r1_c1:
        if risk_score_available:
            needle_frac = 1 - min(1.0, risk_score / 100)
            score_display = f"""{risk_score}<span style="font-size:13.5px; color:#64748B;">/100</span>"""
            needle_color = "#F8FAFC"
        else:
            needle_frac = 0.5
            score_display = """N/A"""
            needle_color = "#475569"

        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px; padding:16px; min-height:260px; display:flex; flex-direction:column; justify-content:space-between; text-align:center;">
    <div style="font-size:14.5px; font-weight:bold; color:#94A3B8; letter-spacing:0.5px; text-align:left;">RISK SUMMARY</div>
    <div style="margin:auto 0;"><svg viewBox="0 0 100 55" style="width:140px; height:90px; display:block; margin:0 auto;">
    <path d="M 12 50 A 38 38 0 0 1 35 15" fill="none" stroke="#10B981" stroke-width="8" stroke-linecap="round" />
    <path d="M 35 15 A 38 38 0 0 1 65 15" fill="none" stroke="#F59E0B" stroke-width="8" />
    <path d="M 65 15 A 38 38 0 0 1 88 50" fill="none" stroke="#EF4444" stroke-width="8" stroke-linecap="round" />
    <line x1="50" y1="50" x2="{50 - 30*np.cos(np.pi*needle_frac):.1f}" y2="{50 - 40*np.sin(np.pi*needle_frac):.1f}" stroke="{needle_color}" stroke-width="2.5" stroke-linecap="round"/>
    <circle cx="50" cy="50" r="4" fill="{needle_color}"/></svg></div>
    <div style="color:{risk_color}; font-size:16.5px; font-weight:bold; margin-top:2px;">{risk_status}</div>
    <div style="font-size:12px; color:#64748B; margin-top:1px;">Risk Score (higher = safer)</div>
    <div style="font-size:21px; font-weight:bold; color:#FFFFFF; line-height:1.1;">{score_display}</div></div>
    <div style="font-size:12.5px; color:#94A3B8; line-height:1.35;">{"ระดับความเสี่ยงของ " + ctx.selected_ticker + " ประเมินจากความเสี่ยงขาลง (CVaR) การตกและฟื้นตัว (Drawdown/Recovery) ความผันผวน (Volatility) ความเสี่ยงตลาด (Beta) และคุณภาพผลตอบแทน (PSR) ถ่วงน้ำหนัก 5 มิติ" if risk_score_available else "ข้อมูลราคาย้อนหลังของหุ้นนี้ไม่พอสำหรับคำนวณ Risk Score (ต้องมีอย่างน้อยประมาณ 20-30 วันทำการ)"}</div>
    </div>""", unsafe_allow_html=True)

    with r1_c2:
        market_risk = int(np.clip(beta_val * 40, 5, 95))
        price_risk = int(np.clip(vol_val * 1.3, 5, 95))
        financial_risk = int(np.clip(de_val_r * 25, 5, 95))
        liquidity_risk = int(np.clip((2.0 - cr_val_r) * 40, 5, 95))
        downside_risk = int(np.clip(dd_val * 1.5, 5, 95))
        overall_risk_dim = int(np.clip(100 - risk_score, 5, 95)) if risk_score_available else None

        def risk_dim_card(label, val):
            if val is None:
                return f"""<div style="background:#151E2F; border:1px solid #1E293B; border-radius:10px; padding:10px 4px; text-align:center;">
    <div style="font-size:13px; font-weight:bold; color:#CBD5E1;">{label}</div>
    <div style="margin:8px auto; width:56px; height:56px; border-radius:50%; background:#1E293B; display:flex; align-items:center; justify-content:center;">
    <span style="font-size:13px; color:#64748B;">N/A</span></div>
    <div style="color:#64748B; font-size:12.5px; font-weight:bold;">-</div></div>"""
            c = "#10B981" if val <= 35 else ("#F59E0B" if val <= 60 else "#EF4444")
            lvl = "Low" if val <= 35 else ("Moderate" if val <= 60 else "High")
            return f"""<div style="background:#151E2F; border:1px solid #1E293B; border-radius:10px; padding:10px 4px; text-align:center;">
    <div style="font-size:13px; font-weight:bold; color:#CBD5E1;">{label}</div>
    <div style="margin:8px auto; width:56px; height:56px; border-radius:50%; background:conic-gradient({c} 0% {val}%, #1E293B {val}% 100%); display:flex; align-items:center; justify-content:center;">
    <div style="width:46px; height:46px; border-radius:50%; background-color:#151E2F; display:flex; align-items:center; justify-content:center;"><span style="font-size:15px; color:#FFFFFF;">{val}</span></div></div>
    <div style="color:{c}; font-size:12.5px; font-weight:bold;">{lvl}</div></div>"""

        dims_html = "".join([
            risk_dim_card("Market Risk (Beta)", market_risk),
            risk_dim_card("Price Risk (Vol.)", price_risk),
            risk_dim_card("Financial Risk (D/E)", financial_risk),
            risk_dim_card("Liquidity Risk", liquidity_risk),
            risk_dim_card("Downside Risk (DD)", downside_risk),
            risk_dim_card("Overall Risk", overall_risk_dim),
        ])
        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px; padding:16px; min-height:260px; display:flex; flex-direction:column; justify-content:space-between;">
    <div style="font-size:14.5px; font-weight:bold; color:#94A3B8; letter-spacing:0.5px;">RISK DIMENSION OVERVIEW ({ctx.selected_ticker})</div>
    <div style="display:grid; grid-template-columns: repeat(6, 1fr); gap:8px; margin:auto 0;">{dims_html}</div>
    <div style="font-size:11px; color:#475569; margin-top:6px;">* มุมมองแยกย่อยอย่างง่าย คำนวณคนละสูตรกับ Risk Score หลักด้านซ้าย ไม่ใช่ breakdown ของ Risk Score โดยตรง</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:22px;'></div>", unsafe_allow_html=True)
    r2_c1, r2_c2, r2_c3 = st.columns(3)

    rh = ctx.risk_hist_df[ctx.risk_hist_df['ticker'] == ctx.selected_ticker].sort_values('date') if not ctx.risk_hist_df.empty else pd.DataFrame()

    with r2_c1:
        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px 12px 0 0; padding:12px 14px 0 14px;">
    <div style="font-size:14px; font-weight:bold; color:#94A3B8; letter-spacing:0.5px;">MARKET RISK (BETA) — vs Peers</div>
    <div style="font-size:19px; font-weight:bold; color:#FFFFFF; margin-top:2px;">{beta_val:.2f}</div></div>""", unsafe_allow_html=True)
        beta_cmp = ctx.scores_df[['ticker', 'beta']].sort_values('beta')
        colors_beta = ['#A855F7' if t == ctx.selected_ticker else '#38BDF8' for t in beta_cmp['ticker']]
        fig_beta = go.Figure(go.Bar(x=beta_cmp['beta'], y=beta_cmp['ticker'], orientation='h', marker=dict(color=colors_beta)))
        fig_beta.add_vline(x=1.0, line_width=1, line_dash="dash", line_color="#64748B")
        fig_beta.update_layout(
            height=160, margin=dict(l=40, r=10, t=10, b=20), paper_bgcolor="#0F172A", plot_bgcolor="#0F172A",
            xaxis=dict(tickfont=dict(size=11, color="#64748B"), gridcolor="#1E293B"),
            yaxis=dict(tickfont=dict(size=11, color="#CBD5E1"), gridcolor="#1E293B"), showlegend=False
        )
        show_chart(fig_beta, key="risk_beta", expand_height=550)

    with r2_c2:
        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px 12px 0 0; padding:12px 14px 0 14px;">
    <div style="font-size:14px; font-weight:bold; color:#94A3B8; letter-spacing:0.5px;">PRICE RISK — Rolling 30D Volatility (actual)</div>
    <div style="font-size:19px; font-weight:bold; color:#FFFFFF; margin-top:2px;">{vol_val:.1f}%</div></div>""", unsafe_allow_html=True)
        if not rh.empty:
            fig_vol = go.Figure()
            fig_vol.add_trace(go.Scatter(x=rh['date'], y=rh['rolling_vol_30d'], mode='lines', line=dict(color='#38BDF8', width=1.8)))
            fig_vol.update_layout(
                height=160, margin=dict(l=30, r=10, t=10, b=20), paper_bgcolor="#0F172A", plot_bgcolor="#0F172A",
                xaxis=dict(tickfont=dict(size=11, color="#64748B"), gridcolor="#1E293B"),
                yaxis=dict(tickfont=dict(size=11, color="#64748B"), gridcolor="#1E293B", zeroline=False), showlegend=False
            )
            show_chart(fig_vol, key="risk_volatility", expand_height=550)
        else:
            st.info("ไม่มีข้อมูล")

    with r2_c3:
        recovery_days = ctx.stock_info.get('recovery_days')
        recovery_txt = f"ฟื้นตัวใน {int(recovery_days)} วัน" if not _is_missing(recovery_days) else "ยังไม่ฟื้นตัวกลับสู่จุดสูงสุดเดิม"
        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px 12px 0 0; padding:12px 14px 0 14px;">
    <div style="font-size:14px; font-weight:bold; color:#94A3B8; letter-spacing:0.5px;">DRAWDOWN — Actual (2023-2025)</div>
    <div style="font-size:19px; font-weight:bold; color:#EF4444; margin-top:2px;">-{dd_val:.1f}%</div>
    <div style="font-size:11.5px; color:#94A3B8; margin-top:2px;">Recovery: {recovery_txt}</div></div>""", unsafe_allow_html=True)
        if not rh.empty:
            fig_dd = go.Figure()
            fig_dd.add_trace(go.Scatter(x=rh['date'], y=rh['drawdown_pct'], mode='lines', line=dict(color='#EF4444', width=1.5), fill='tozeroy', fillcolor='rgba(239,68,68,0.2)'))
            fig_dd.update_layout(
                height=160, margin=dict(l=30, r=10, t=10, b=20), paper_bgcolor="#0F172A", plot_bgcolor="#0F172A",
                xaxis=dict(tickfont=dict(size=11, color="#64748B"), gridcolor="#1E293B"),
                yaxis=dict(tickfont=dict(size=11, color="#64748B"), gridcolor="#1E293B", zeroline=False), showlegend=False
            )
            show_chart(fig_dd, key="risk_drawdown", expand_height=550)
        else:
            st.info("ไม่มีข้อมูล")

    st.markdown("<div style='margin-top:22px;'></div>", unsafe_allow_html=True)
    r3_c1, r3_c2 = st.columns(2)

    with r3_c1:
        cvar_val = ctx.stock_info.get('cvar_95')
        if _is_missing(cvar_val):
            cvar_val = _fallback_cvar_95(ctx.stock_daily)

        var_num_txt = _fmt_or_na(ctx.stock_info.get('var_95'))
        var_txt = var_num_txt if var_num_txt == 'N/A' else f'-{var_num_txt}%'
        if cvar_val is not None:
            cvar_txt = _fmt_or_na(cvar_val) + '%'
            downside_metrics_html = f"""<div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; text-align:center; margin:auto 0;">
    <div><div style="font-size:22px; font-weight:bold; color:#EF4444;">{var_txt}</div><div style="font-size:12px; color:#64748B;">VaR 95%</div></div>
    <div><div style="font-size:22px; font-weight:bold; color:#EF4444;">-{cvar_txt}</div><div style="font-size:12px; color:#64748B;">CVaR 95%</div></div>
    </div>
    <div style="font-size:12px; color:#64748B; border-top:1px solid #1E293B; padding-top:6px;">VaR = ระดับขาดทุนรายวันที่ไม่ควรแย่ไปกว่านี้ใน 95% ของวัน (Historical Simulation) | CVaR = ขาดทุนเฉลี่ยจริงของวันที่แย่กว่าเส้น VaR — คำนวณจากข้อมูลจริงทั้งคู่ จึงการันตีว่า CVaR แย่กว่าหรือเท่ากับ VaR เสมอ</div>"""
        else:
            downside_metrics_html = f"""<div style="margin:auto 0;">
    <div style="font-size:24px; font-weight:bold; color:#EF4444;">{var_txt}</div><div style="font-size:12.5px; color:#64748B;">VaR 95% (Historical)</div>
    </div>
    <div style="font-size:12px; color:#64748B; border-top:1px solid #1E293B; padding-top:6px;">VaR = ระดับขาดทุนรายวันที่ไม่ควรแย่ไปกว่านี้ใน 95% ของวัน — CVaR ยังคำนวณไม่ได้เนื่องจากข้อมูลราคาย้อนหลังไม่พอ</div>"""

        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px; padding:14px; min-height:225px; display:flex; flex-direction:column; justify-content:space-between;">
    <div style="font-size:14px; font-weight:bold; color:#94A3B8; letter-spacing:0.5px;">DOWNSIDE RISK (Daily)</div>
    {downside_metrics_html}
    </div>""", unsafe_allow_html=True)

    with r3_c2:
        avg_ret = ctx.stock_daily['close'].pct_change().mean() * 252
        calmar = round(avg_ret * 100 / dd_val, 2) if dd_val > 0 else 0
        rf_pct = safe(ctx.stock_info.get('risk_free_rate_annual'), 0.02) * 100

        psr_val = ctx.stock_info.get('psr')
        if _is_missing(psr_val):
            psr_val = _fallback_psr(ctx.stock_daily)

        base_cells = f"""<div style="background:#151E2F; border:1px solid #1E293B; border-radius:6px; padding:6px 2px;"><div style="font-size:12px; color:#64748B;">Sharpe</div><div style="font-size:15px; font-weight:bold; color:#F8FAFC;">{_fmt_or_na(ctx.stock_info.get('sharpe_ratio'))}</div></div>
    <div style="background:#151E2F; border:1px solid #1E293B; border-radius:6px; padding:6px 2px;"><div style="font-size:12px; color:#64748B;">Sortino</div><div style="font-size:15px; font-weight:bold; color:#F8FAFC;">{_fmt_or_na(ctx.stock_info.get('sortino_ratio'))}</div></div>
    <div style="background:#151E2F; border:1px solid #1E293B; border-radius:6px; padding:6px 2px;"><div style="font-size:12px; color:#64748B;">Calmar</div><div style="font-size:15px; font-weight:bold; color:#F8FAFC;">{calmar:.2f}</div></div>"""

        if psr_val is not None:
            grid_cols = 4
            ratio_cells = base_cells + f"""
    <div style="background:#151E2F; border:1px solid #1E293B; border-radius:6px; padding:6px 2px;"><div style="font-size:12px; color:#64748B;">PSR</div><div style="font-size:15px; font-weight:bold; color:#F8FAFC;">{psr_val:.0f}%</div></div>"""
            footnote = f"""คำนวณหัก Risk-free Rate (~{rf_pct:.1f}%/ปี) แล้ว | PSR = ความน่าจะเป็นที่ Sharpe Ratio จริง &gt; 0 เมื่อพิจารณาความเบ้/โด่งของข้อมูล"""
        else:
            grid_cols = 3
            ratio_cells = base_cells
            footnote = f"""คำนวณหัก Risk-free Rate (~{rf_pct:.1f}%/ปี) แล้ว"""

        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px; padding:14px; min-height:225px; display:flex; flex-direction:column; justify-content:space-between;">
    <div style="font-size:14px; font-weight:bold; color:#94A3B8; letter-spacing:0.5px;">RISK-ADJUSTED RETURN (actual, 2023-2025)</div>
    <div style="display:grid; grid-template-columns: repeat({grid_cols}, 1fr); gap:6px; text-align:center; margin:auto 0;">
    {ratio_cells}
    </div><div style="font-size:11.5px; color:#CBD5E1; border-top:1px solid #1E293B; padding-top:6px;">{footnote}</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:22px;'></div>", unsafe_allow_html=True)
    r4_c1, r4_c2 = st.columns([1.35, 1.65])

    with r4_c1:
        risk_pts = []
        if beta_val < 1: risk_pts.append(("✔", "#10B981", f"Beta {beta_val:.2f} ต่ำกว่าตลาด ความผันผวนสัมพัทธ์ต่ำ"))
        else: risk_pts.append(("●", "#EF4444", f"Beta {beta_val:.2f} สูงกว่าตลาด อ่อนไหวต่อความผันผวนตลาดมาก"))
        if de_val_r < 1: risk_pts.append(("✔", "#10B981", f"ภาระหนี้สินต่ำ D/E = {de_val_r:.2f} เท่า"))
        else: risk_pts.append(("●", "#EF4444", f"ภาระหนี้สินค่อนข้างสูง D/E = {de_val_r:.2f} เท่า"))
        if dd_val < 30: risk_pts.append(("✔", "#10B981", f"Max Drawdown {dd_val:.1f}% อยู่ในเกณฑ์ควบคุมได้"))
        else: risk_pts.append(("●", "#EF4444", f"Max Drawdown {dd_val:.1f}% ค่อนข้างลึก ควรระวังช่วงตลาดผันผวน"))
        risk_pts_html = "".join([f'<div style="display:flex; gap:6px; margin-bottom:3px;"><span style="color:{c};">{icon}</span><span>{txt}</span></div>' for icon, c, txt in risk_pts])
        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px; padding:14px; min-height:210px; display:flex; flex-direction:column; justify-content:space-between;">
    <div style="font-size:14px; font-weight:bold; color:#94A3B8; letter-spacing:0.5px;">RISK FACTORS HIGHLIGHT ({ctx.selected_ticker})</div>
    <div style="font-size:12.5px; color:#CBD5E1; line-height:1.45; margin:auto 0;">{risk_pts_html}</div>
    </div>""", unsafe_allow_html=True)

    with r4_c2:
        risk_score_line = f"<b>{risk_score}/100 ({risk_status})</b>" if risk_score_available else "<b>N/A</b> (ข้อมูลราคาย้อนหลังไม่พอ)"
        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px; padding:14px; min-height:210px; display:flex; flex-direction:column; justify-content:space-between;">
    <div><div style="font-size:14px; font-weight:bold; color:#94A3B8; letter-spacing:0.5px; margin-bottom:6px;">EXPLAINABLE RISK SUMMARY</div>
    <p style="font-size:13px; color:#CBD5E1; line-height:1.5; margin:0;">
    หุ้น <b>{ctx.selected_ticker}</b> มีคะแนนความเสี่ยงรวมอยู่ที่ {risk_score_line} โดย Beta = {beta_val:.2f}, Volatility รายปี = {vol_val:.1f}%, และ Max Drawdown สูงสุด = {dd_val:.1f}% ในช่วง 2023-2025
    </p></div>
    <div style="font-size:12px; color:#F59E0B; background:rgba(245,158,11,0.08); border-left:3px solid #F59E0B; padding:5px 8px; border-radius:4px;">
    <b>ข้อสังเกต:</b> ควรติดตามความผันผวนของตลาดโลกและนโยบายอัตราดอกเบี้ยอย่างต่อเนื่อง</div>
    </div>""", unsafe_allow_html=True)

    render_nav_footer("m5", prev_page=" 🔮 AI Prediction", next_page=" 📊 Industry Benchmark")
