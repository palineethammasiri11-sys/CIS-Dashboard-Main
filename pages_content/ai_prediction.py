"""
pages_content/ai_prediction.py
--------------------------
หน้า "AI Prediction" ของ CIS Dashboard

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
    ai_score = int(round(safe(ctx.stock_info.get('ai_score'), 50)))
    ai_status = "BULLISH" if ai_score >= 70 else ("NEUTRAL" if ai_score >= 45 else "BEARISH")
    ai_color = "#10B981" if ai_score >= 70 else ("#F59E0B" if ai_score >= 45 else "#EF4444")
    prob_up = safe(ctx.stock_info.get('prob_up'), 50)
    down_prob = round(100 - prob_up, 1)
    acc_val = safe(ctx.stock_info.get('accuracy'), 50)                    # <-- เพิ่มบรรทัดนี้
    baseline_val = safe(ctx.stock_info.get('baseline_accuracy'), acc_val) # <-- เพิ่มบรรทัดนี้
    reliability_low = acc_val < 50 

    st.markdown(f"""<div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:15px;">
    <div><div style="font-size:14.5px; color:#64748B; margin-bottom:2px;">Home / Module 4 / AI Prediction</div>
    <div style="display:flex; align-items:baseline; gap:8px;"><h2 style="margin:0; font-size:23px; font-weight:bold; color:#F8FAFC; letter-spacing:0.5px;">AI PREDICTION</h2></div></div>
    <div style="text-align:right; display:flex; align-items:center; gap:16px;">
    <div><span style="font-size:13px; color:#64748B;">Data as of</span><br><b style="color:#CBD5E1; font-size:15px;">{ctx.stock_info.get('latest_date','-')}</b></div>
    <div><span style="font-size:13px; color:#64748B;">Model</span><br><b style="color:#38BDF8; font-size:15px;">Random Forest (n=200, depth=4)</b></div>
    <div><span style="font-size:13px; color:#64748B;">Target</span><br><b style="color:#CBD5E1; font-size:15px;">10-Day Forward Direction</b></div>
    </div></div>""", unsafe_allow_html=True)

    r1_c1, r1_c2, r1_c3 = st.columns([1.1, 1.25, 1.65])

    with r1_c1:
        ai_stars = min(5, max(1, round(ai_score / 20)))
        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px; padding:16px; min-height:260px; display:flex; flex-direction:column; justify-content:space-between;">
    <div style="font-size:14.5px; font-weight:bold; color:#94A3B8; letter-spacing:0.5px;">AI PREDICTION SUMMARY</div>
    <div style="display:flex; align-items:center; justify-content:space-between; margin:auto 0;">
    <div style="text-align:center;"><div style="background:rgba(16,185,129,0.12); border:1px solid {ai_color}; border-radius:50%; width:78px; height:78px; display:flex; align-items:center; justify-content:center; font-size:28px; margin:0 auto 6px auto;">🔮</div>
    <div style="color:{ai_color}; font-size:16px; font-weight:bold;">{ai_status}</div><div style="color:#64748B; font-size:12.5px; letter-spacing:0.5px;">PREDICTION</div>
    <div style="color:{ai_color}; font-size:13px; letter-spacing:1px; margin-top:2px;">{'★'*ai_stars}{'☆'*(5-ai_stars)}</div></div>
    <div style="text-align:right;"><div style="font-size:13px; color:#64748B;">Prediction Score</div><div style="font-size:28px; font-weight:bold; color:{ai_color}; line-height:1.1;">{ai_score}<span style="font-size:15px; color:#64748B;">/100</span></div>
    <div style="font-size:13px; color:#64748B;">Test Accuracy</div><div style="font-size:16.5px; font-weight:bold; color:#10B981;">{safe(ctx.stock_info.get('accuracy')):.1f}%</div></div></div>
    <p style="font-size:13px; color:#CBD5E1; line-height:1.35; margin:0;">โมเดล Random Forest คาดการณ์ทิศทางราคาหุ้น <b>{ctx.selected_ticker}</b> ใน 10 วันทำการถัดไป จาก technical indicators จริง (Train: 2023-2024 / Test: 2025)</p>
    </div>""", unsafe_allow_html=True)

    with r1_c2:
        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px; padding:16px; min-height:260px; display:flex; flex-direction:column; justify-content:space-between; text-align:center;">
    <div style="font-size:14.5px; font-weight:bold; color:#94A3B8; letter-spacing:0.5px; text-align:left;">PREDICTION PROBABILITY</div>
    <div style="margin:auto 0;"><svg viewBox="0 0 100 55" style="width:150px; height:95px; display:block; margin:0 auto;">
    <path d="M 10 50 A 40 40 0 0 1 90 50" fill="none" stroke="#1E293B" stroke-width="9" stroke-linecap="round" />
    <path d="M 10 50 A 40 40 0 0 1 {10 + 80*min(1,prob_up/100):.1f} {50 - (40*np.sin(np.pi*min(1,prob_up/100))):.1f}" fill="none" stroke="{ai_color}" stroke-width="9" stroke-linecap="round" />
    <text x="50" y="38" text-anchor="middle" font-size="20" font-weight="bold" fill="#FFFFFF">{prob_up:.0f}%</text>
    <text x="50" y="47" text-anchor="middle" font-size="9.5" fill="#94A3B8">Probability of</text>
    <text x="50" y="54" text-anchor="middle" font-size="10.5" font-weight="bold" fill="{ai_color}">{ai_status}</text></svg></div>
    <div style="display:flex; justify-content:space-between; align-items:center; border-top:1px solid #1E293B; padding-top:8px;">
    <div style="text-align:left;"><div style="font-size:12.5px; color:#64748B;">UPTREND</div><div style="font-size:16.5px; font-weight:bold; color:#10B981;">{prob_up:.0f}%</div></div>
    <div style="text-align:right;"><div style="font-size:12.5px; color:#64748B;">DOWNTREND</div><div style="font-size:16.5px; font-weight:bold; color:#EF4444;">{down_prob:.0f}%</div></div>
    </div></div>""", unsafe_allow_html=True)

    with r1_c3:
        n_train = len(ctx.stock_daily[ctx.stock_daily['date'] < '2025-01-01'])
        n_test = len(ctx.stock_daily[ctx.stock_daily['date'] >= '2025-01-01'])
        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px; padding:16px; min-height:260px; display:flex; flex-direction:column; justify-content:space-between;">
    <div style="font-size:14.5px; font-weight:bold; color:#94A3B8; letter-spacing:0.5px;">MODEL & DATA SUMMARY</div>
    <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:8px; margin-top:8px;">
    <div style="background:#151E2F; border:1px solid #1E293B; border-radius:8px; padding:10px 8px; text-align:center;"><div style="font-size:12.5px; color:#64748B;">Train Samples</div><div style="font-size:19px; font-weight:bold; color:#FFFFFF; margin:3px 0;">{n_train}</div><div style="font-size:12px; color:#64748B;">2023-2024</div></div>
    <div style="background:#151E2F; border:1.5px solid #2563EB; border-radius:8px; padding:10px 8px; text-align:center;"><div style="font-size:12.5px; color:#64748B;">Test Samples</div><div style="font-size:19px; font-weight:bold; color:#FFFFFF; margin:3px 0;">{n_test}</div><div style="font-size:12px; color:#64748B;">2025</div></div>
    <div style="background:#151E2F; border:1px solid #1E293B; border-radius:8px; padding:10px 8px; text-align:center;"><div style="font-size:12.5px; color:#64748B;">Features</div><div style="font-size:19px; font-weight:bold; color:#FFFFFF; margin:3px 0;">6</div><div style="font-size:12px; color:#64748B;">Technical</div></div>
    </div>
    <p style="font-size:12.5px; color:#94A3B8; line-height:1.4; margin-top:10px;">โมเดลถูกฝึกแยกเป็นรายหุ้น โดยใช้ close, EMA20, EMA50, RSI14, MACD, ADX เป็น input และ label เป้าหมายคือราคาปิดใน 10 วันถัดไปสูงกว่าปัจจุบันหรือไม่</p>
    </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:22px;'></div>", unsafe_allow_html=True)
    r2_c1, r2_c2 = st.columns([1.55, 1.25])

    with r2_c1:
        st.markdown("""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px 12px 0 0; padding:12px 16px 0 16px;">
    <div><span style="font-size:14.5px; font-weight:bold; color:#94A3B8; letter-spacing:0.5px;">PRICE HISTORY + MODEL-IMPLIED FORWARD RANGE</span></div></div>""", unsafe_allow_html=True)

        hist_tail = ctx.stock_daily.tail(150)
        vol_annual = safe(ctx.stock_info.get('volatility'), 25.0) / 100
        daily_vol = vol_annual / np.sqrt(252)
        horizon_days = 10
        future_dates = pd.bdate_range(start=hist_tail['date'].iloc[-1], periods=horizon_days + 1)[1:]
        drift = (prob_up - 50) / 50 * daily_vol * horizon_days  # ทิศทางอิงจาก prob_up จริงของโมเดล
        t = np.arange(1, horizon_days + 1)
        median_path = ctx.current_price * (1 + drift * (t / horizon_days))
        band = ctx.current_price * daily_vol * np.sqrt(t) * 1.28  # ~80% band จาก volatility จริง
        upper_path = median_path + band
        lower_path = median_path - band

        fig_forecast = go.Figure()
        fig_forecast.add_trace(go.Scatter(x=hist_tail['date'], y=hist_tail['close'], mode='lines', line=dict(color='#38BDF8', width=2), name='Actual Price'))
        fig_forecast.add_trace(go.Scatter(x=future_dates, y=lower_path, mode='lines', line=dict(color='#EF4444', width=1.6, dash='dash'), name='Lower Bound (80%)'))
        fig_forecast.add_trace(go.Scatter(x=future_dates, y=median_path, mode='lines', line=dict(color='#10B981', width=2.0, dash='dash'), name='Model-Implied Median'))
        fig_forecast.add_trace(go.Scatter(x=future_dates, y=upper_path, mode='lines', line=dict(color='#2DD4BF', width=1.6, dash='dash'), name='Upper Bound (80%)'))

        fig_forecast.update_layout(
            height=310, margin=dict(l=35, r=45, t=10, b=25), paper_bgcolor="#0F172A", plot_bgcolor="#0F172A",
            xaxis=dict(gridcolor="#1E293B", tickfont=dict(size=11.5, color="#64748B"), zeroline=False),
            yaxis=dict(title=dict(text="Price (THB)", font=dict(size=12, color="#64748B")), gridcolor="#1E293B", tickfont=dict(size=11.5, color="#64748B"), zeroline=False),
            legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0, font=dict(size=11.5, color="#CBD5E1"))
        )
        show_chart(fig_forecast, key="ai_forecast", expand_height=700)
        st.markdown(f"""<div style="font-size:12px; color:#64748B; padding:0 16px 10px 16px; background:#0F172A; border:1px solid #1E293B; border-top:none; border-radius:0 0 12px 12px;">
    * ช่วงคาดการณ์คำนวณจาก Annualized Volatility จริง ({safe(ctx.stock_info.get('volatility')):.1f}%) และความน่าจะเป็นขาขึ้นจากโมเดล ({prob_up:.0f}%) ไม่ใช่การรับประกันผลตอบแทน</div>""", unsafe_allow_html=True)

    with r2_c2:
        st.markdown("""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px 12px 0 0; padding:12px 16px 0 16px;">
    <div><span style="font-size:14.5px; font-weight:bold; color:#94A3B8; letter-spacing:0.5px;">FEATURE IMPORTANCE (Random Forest, actual)</span></div></div>""", unsafe_allow_html=True)

        fi = ctx.feat_imp_df[ctx.feat_imp_df['ticker'] == ctx.selected_ticker].sort_values('importance')
        if not fi.empty:
            fig_shap = go.Figure(go.Bar(
                x=fi['importance'], y=fi['feature'], orientation='h', marker=dict(color='#8B5CF6'),
                text=[f"{v:.3f}" for v in fi['importance']], textposition='outside', textfont=dict(size=11.5, color='#CBD5E1')
            ))
            fig_shap.update_layout(
                height=322, margin=dict(l=10, r=35, t=10, b=25), paper_bgcolor="#0F172A", plot_bgcolor="#0F172A",
                xaxis=dict(gridcolor="#1E293B", tickfont=dict(size=11.5, color="#64748B"), zeroline=False),
                yaxis=dict(tickfont=dict(size=11.5, color="#CBD5E1"), gridcolor="#1E293B", zeroline=False), showlegend=False
            )
            show_chart(fig_shap, key="ai_feature_importance", expand_height=650)
        else:
            st.info("ไม่มีข้อมูล Feature Importance")

    st.markdown("<div style='margin-top:22px;'></div>", unsafe_allow_html=True)
    r3_c1, r3_c2, r3_c3, r3_c4 = st.columns([1.1, 1.25, 1.35, 1.1])

    with r3_c1:
        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px; padding:14px; min-height:290px; display:flex; flex-direction:column; justify-content:space-between;">
    <div><div style="font-size:13.5px; font-weight:bold; color:#94A3B8; letter-spacing:0.5px;">MODEL PERFORMANCE (TEST SET 2025, actual)</div>
    <div style="display:grid; grid-template-columns: repeat(2, 1fr); gap:6px; margin-top:10px; text-align:center;">
    <div style="background:#151E2F; border:1px solid #1E293B; border-radius:6px; padding:6px 2px;"><div style="font-size:12px; color:#64748B;">Accuracy</div><div style="font-size:16px; font-weight:bold; color:#F8FAFC;">{safe(ctx.stock_info.get('accuracy')):.1f}%</div></div>
    <div style="background:#151E2F; border:1px solid #1E293B; border-radius:6px; padding:6px 2px;"><div style="font-size:12px; color:#64748B;">Precision</div><div style="font-size:16px; font-weight:bold; color:#F8FAFC;">{safe(ctx.stock_info.get('precision')):.1f}%</div></div>
    <div style="background:#151E2F; border:1px solid #1E293B; border-radius:6px; padding:6px 2px;"><div style="font-size:12px; color:#64748B;">ROC-AUC</div><div style="font-size:16px; font-weight:bold; color:#F8FAFC;">{safe(ctx.stock_info.get('roc_auc')):.2f}</div></div>
    <div style="background:#151E2F; border:1px solid #1E293B; border-radius:6px; padding:6px 2px;"><div style="font-size:12px; color:#64748B;">F1-Score</div><div style="font-size:16px; font-weight:bold; color:#F8FAFC;">{safe(ctx.stock_info.get('f1_score')):.1f}%</div></div>
    </div></div>
    <div style="font-size:11.5px; color:{'#EF4444' if acc_val < safe(ctx.stock_info.get('baseline_accuracy'), acc_val) else '#10B981'}; border-top:1px dashed #1E293B; padding-top:5px; margin-top:4px;">
    vs. Baseline (naive majority-class): {safe(ctx.stock_info.get('baseline_accuracy')):.1f}%
    </div>
    </div></div><div style="font-size:11.5px; color:#64748B; border-top:1px solid #1E293B; padding-top:6px;">Validation: Out-of-time (Train 2023-24 / Test 2025)</div>
    </div>""", unsafe_allow_html=True)

    with r3_c2:
        st.markdown("""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px 12px 0 0; padding:12px 14px 0 14px;">
    <div style="font-size:13.5px; font-weight:bold; color:#94A3B8; letter-spacing:0.5px;">HISTORICAL PREDICTION PERFORMANCE (Test Set, actual)</div></div>""", unsafe_allow_html=True)
        bt = ctx.backtest_df[ctx.backtest_df['ticker'] == ctx.selected_ticker].sort_values('date') if not ctx.backtest_df.empty else pd.DataFrame()
        if not bt.empty:
            bt_q = bt.set_index('date').resample('W').mean(numeric_only=True).dropna().reset_index()
            fig_bt = go.Figure()
            fig_bt.add_trace(go.Scatter(x=bt_q['date'], y=bt_q['actual_close'], mode='lines', name='Actual Close', line=dict(color='#38BDF8', width=1.5), yaxis='y1'))
            fig_bt.add_trace(go.Scatter(x=bt_q['date'], y=bt_q['predicted_up_prob'] * 100, mode='lines', name='Predicted Up Prob (%)', line=dict(color='#10B981', width=1.5, dash='dash'), yaxis='y2'))
            fig_bt.update_layout(
                height=120, margin=dict(l=25, r=25, t=5, b=15), paper_bgcolor="#0F172A", plot_bgcolor="#0F172A",
                xaxis=dict(tickfont=dict(size=10.5, color="#64748B"), gridcolor="#1E293B"),
                yaxis=dict(tickfont=dict(size=10.5, color="#64748B"), gridcolor="#1E293B", zeroline=False),
                yaxis2=dict(overlaying='y', side='right', showgrid=False, tickfont=dict(size=10.5, color="#64748B")),
                showlegend=False
            )
            show_chart(fig_bt, key="ai_backtest", expand_height=550)
            hit_rate = ((bt['predicted_up_prob'] > 0.5).astype(int) == (bt['actual_close'].diff().shift(-1) > 0).astype(int)).mean() * 100
            st.markdown(f"""<div style="background:#0F172A; border:1px solid #1E293B; border-top:none; border-radius:0 0 12px 12px; padding:0 12px 10px 12px; font-size:11.5px; color:#64748B;">* Test-set Accuracy: {safe(ctx.stock_info.get('accuracy')):.1f}%</div>""", unsafe_allow_html=True)
        else:
            st.info("ไม่มีข้อมูล Backtest")

    with r3_c3:
        top_feat = fi.sort_values('importance', ascending=False).iloc[0]['feature'] if not fi.empty else "N/A"
        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px; padding:14px; min-height:290px; display:flex; flex-direction:column; justify-content:space-between;">
    <div><div style="font-size:13.5px; font-weight:bold; color:#94A3B8; letter-spacing:0.5px; margin-bottom:6px;">EXPLAINABLE AI SUMMARY ({ctx.selected_ticker})</div>
    <p style="font-size:13px; color:#CBD5E1; line-height:1.45; margin:0 0 8px 0;">โมเดลประเมินความน่าจะเป็นขาขึ้นสำหรับ <b>{ctx.selected_ticker}</b> อยู่ที่ <b>{prob_up:.0f}%</b> โดย feature ที่มีอิทธิพลสูงสุดคือ <b>{top_feat}</b>:</p>
    <div style="font-size:12.5px; color:#CBD5E1; line-height:1.5; display:flex; flex-direction:column; gap:4px;">
    <div style="display:flex; gap:6px;"><span style="color:#10B981;">✔</span><span>Test Accuracy บนข้อมูลปี 2025 อยู่ที่ {safe(ctx.stock_info.get('accuracy')):.1f}%</span></div>
    <div style="display:flex; gap:6px;"><span style="color:#10B981;">✔</span><span>ROC-AUC = {safe(ctx.stock_info.get('roc_auc')):.2f} (ยิ่งใกล้ 1 ยิ่งแยกแยะได้ดี)</span></div>
    <div style="display:flex; gap:6px;"><span style="color:#10B981;">✔</span><span>Signal ปัจจุบัน: {ctx.stock_info.get('ai_signal','-')}</span></div>
    </div></div></div>""", unsafe_allow_html=True)

    with r3_c4:
    acc_val = safe(ctx.stock_info.get('accuracy'), 50)
    reliability_badge = (
        '<div style="display:inline-block; background:rgba(239,68,68,0.15); border:1px solid #EF4444; '
        'color:#EF4444; font-size:10.5px; font-weight:bold; padding:2px 7px; border-radius:6px; margin-bottom:5px;">'
        '⚠ LOW RELIABILITY</div>'
    ) if acc_val < 50 else ""
        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px; padding:14px; min-height:290px; display:flex; flex-direction:column; justify-content:space-between;">
    <div><div style="font-size:13.5px; font-weight:bold; color:#94A3B8; letter-spacing:0.5px;">AI RECOMMENDATION</div>
    <div style="display:flex; align-items:center; gap:8px; margin:8px 0 4px 0;"><div>
    <div style="font-size:23px; font-weight:bold; color:{ai_color}; line-height:1;">{ctx.stock_info.get('ai_signal','-')}</div>
    <div style="font-size:12.5px; font-weight:bold; color:{ai_color};">Prob. Up: {prob_up:.0f}%</div></div></div>
    <div style="font-size:12.5px; color:#CBD5E1; border-top:1px dashed #1E293B; padding-top:6px; margin-top:4px;">
    <div style="display:flex; justify-content:space-between; margin-bottom:3px;"><span style="color:#64748B;">Target Period</span><b style="color:#F8FAFC;">10 Trading Days</b></div>
    <div style="display:flex; justify-content:space-between;"><span style="color:#64748B;">Model Accuracy</span><b style="color:#F59E0B;">{safe(ctx.stock_info.get('accuracy')):.1f}%</b></div>
    </div></div><div style="font-size:11.5px; color:#64748B; text-align:center;">โปรดใช้ประกอบการตัดสินใจลงทุน ไม่ใช่คำแนะนำโดยตรง</div>
    </div>""", unsafe_allow_html=True)

    render_nav_footer("m4", prev_page=" ⏱️ Entry Timing", next_page=" 🛡️ Risk Analysis")

