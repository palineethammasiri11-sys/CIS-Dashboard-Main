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

=== CHANGELOG (v4 — Font & Prediction box redesign) ===
- ขยายฟอนต์ทั้งหน้า: KPI (label 14 / ค่า 36 / คำอธิบายย่อย 15), Model Performance (ค่า 26 / label 14.5),
  Explainable AI Summary (17), คำอธิบายใน Prediction (18), ตัวเลข/legend ของกราฟทุกอัน (12.5-13)
  และปรับสีข้อความรอง (muted) จาก #64748B เป็น #94A3B8 ให้อ่านชัดขึ้นบนพื้นเข้ม
- ช่อง Prediction แยกเป็น 2 กล่อง: ซ้าย = gauge % ใหญ่ (ตัดข้อความ "Probability of ..." ออกจากในวงกลม)
  ขวา = กล่องคำอธิบายสีอ่อนกว่า มีหัวข้อ "PROBABILITY OF UP" (อังกฤษล้วน) และแยกคำอธิบายเป็น 2 บรรทัด
- เปลี่ยน 🔮 เป็น 📈 ที่หัวข้อ Prediction / เอา 🧠 ออกจากหัวข้อ Model Explanation
- ประโยคอธิบายใช้ความน่าจะเป็นของ "ทิศทางที่ทำนาย" (dir_prob) เพื่อให้ตรงเมื่อ prob_up < 50
  (เดิมจะโชว์ "มีโอกาสขาลง 40%" ทั้งที่ 40% คือโอกาสขึ้น)
- ย้ายโครง KPI card ไปใช้ helper _kpi_card() แทนการเขียน HTML ซ้ำ 5 ก้อน

=== CHANGELOG (v3 — Layout/UX redesign) ===
- รวมสถานะทำนายเป็นแหล่งความจริงเดียว: ใช้เกณฑ์จาก prob_up (>=70 / >=50 / อื่นๆ) กำหนด status_color
  เดียวกันทั้งหน้า (Direction, Probability, Score, Recommendation, กราฟ Forecast)
- ลบการ์ด "MODEL & DATA SUMMARY" ออกจากหน้าแรก ย้ายรายละเอียดไปไว้ใน expander ท้ายส่วน Model Performance
- เพิ่มแถบ KPI ใหญ่ด้านบนสุด (Price, Direction, Probability, Score, Recommendation)
- จัดลำดับส่วนใหม่: Overview -> Prediction -> Forecast -> Model Explanation -> Model Performance
- กราฟ Forecast: แยก Actual / Model Forecast / Prediction Range ให้ต่างกันชัดเจน
- ลดจำนวนสีที่ใช้: สถานะ 3 สี (เขียว/เหลือง/แดง) + ฟ้า 1 สีสำหรับข้อมูลราคาจริง/กราฟทั่วไป
- Explainable AI Summary ตัดบรรทัดที่ซ้ำกับ Model Performance ออก
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from common import fmt_mb, fmt_ratio, safe, show_chart, render_nav_footer, COMPANY_NAMES, SECTOR_MAP

GREEN = "#10B981"
AMBER = "#F59E0B"
RED = "#EF4444"
BLUE = "#38BDF8"
MUTED = "#94A3B8"  # สีข้อความรอง (เดิม #64748B จางเกินไปบนพื้นเข้ม)


def _hex_to_rgba(hex_color, alpha):
    hex_color = hex_color.lstrip('#')
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _section_title(text):
    return f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px 12px 0 0; padding:14px 18px 2px 18px;">
<div><span style="font-size:16.5px; font-weight:bold; color:{MUTED}; letter-spacing:0.5px;">{text}</span></div></div>"""


def _kpi_card(label, value_html, sub_html="", value_color="#F8FAFC", value_size=36, border="#1E293B"):
    """การ์ด KPI ใบเดียว (HTML บรรทัดเดียว ห้ามมีบรรทัดว่าง/เยื้องหน้า ไม่งั้น markdown จะตีเป็น code block)"""
    return (
        f'<div style="background-color:#0F172A; border:1px solid {border}; border-radius:12px; padding:18px 10px; '
        f'text-align:center; min-height:140px; display:flex; flex-direction:column; justify-content:center;">'
        f'<div style="font-size:14px; font-weight:bold; color:{MUTED}; letter-spacing:1px;">{label}</div>'
        f'<div style="font-size:{value_size}px; font-weight:bold; color:{value_color}; line-height:1.2; margin-top:4px;">{value_html}</div>'
        f'{sub_html}'
        f'</div>'
    )


def _kpi_sub(text, color=MUTED, bold=False):
    weight = "bold" if bold else "normal"
    return f'<div style="font-size:15px; font-weight:{weight}; color:{color}; margin-top:2px;">{text}</div>'


def _metric_cell(label, value):
    return (
        f'<div style="background:#151E2F; border:1px solid #1E293B; border-radius:8px; padding:14px 6px; text-align:center;">'
        f'<div style="font-size:14.5px; color:{MUTED};">{label}</div>'
        f'<div style="font-size:26px; font-weight:bold; color:#F8FAFC; line-height:1.35;">{value}</div></div>'
    )


def render(ctx):
    # ============================================================
    # แหล่งความจริงเดียวของสถานะทำนาย — ใช้ทุกจุดในหน้า ไม่คำนวณซ้ำแยกชุด
    # ============================================================
    prob_up = safe(ctx.stock_info.get('prob_up'), 50)
    down_prob = round(100 - prob_up, 1)
    ai_score = int(round(safe(ctx.stock_info.get('ai_score'), 50)))
    acc_val = safe(ctx.stock_info.get('accuracy'), 50)
    baseline_val = safe(ctx.stock_info.get('baseline_accuracy'), acc_val)
    signal = ctx.stock_info.get('ai_signal', '-')

    if prob_up >= 70:
        status_color = GREEN
    elif prob_up >= 50:
        status_color = AMBER
    else:
        status_color = RED

    direction_th = "ขาขึ้น" if prob_up >= 50 else "ขาลง"
    dir_prob = prob_up if prob_up >= 50 else down_prob  # ความน่าจะเป็นของ "ทิศทางที่ทำนาย" ใช้ในประโยคอธิบาย
    reliability_low = acc_val < baseline_val
    baseline_note = "สูงกว่า" if not reliability_low else "ต่ำกว่า"

    st.markdown(f"""<div style="margin-bottom:16px;">
<div style="font-size:15px; color:{MUTED}; margin-bottom:2px;">Home / Module 4 / AI Prediction</div>
<h2 style="margin:0; font-size:26px; font-weight:bold; color:#F8FAFC; letter-spacing:0.5px;">AI PREDICTION</h2>
</div>""", unsafe_allow_html=True)

    # ============================================================
    # 1) OVERVIEW — แถบ KPI ใหญ่ ตอบคำถาม "สรุปแล้วตัวเลขคืออะไร"
    # ============================================================
    k1, k2, k3, k4, k5 = st.columns(5)

    with k1:
        st.markdown(_kpi_card(
            "PRICE", f"{ctx.current_price:,.2f}",
            _kpi_sub(f"{ctx.change_val:+.2f} ({ctx.change_pct:+.2f}%) {ctx.arrow_sign}", ctx.change_color, bold=True)
        ), unsafe_allow_html=True)

    with k2:
        st.markdown(_kpi_card(
            "DIRECTION (10D)", direction_th, _kpi_sub("10 Trading Days"), value_color=status_color
        ), unsafe_allow_html=True)

    with k3:
        st.markdown(_kpi_card(
            "PROBABILITY", f"{prob_up:.0f}%", _kpi_sub(f"Down: {down_prob:.0f}%"), value_color=status_color
        ), unsafe_allow_html=True)

    with k4:
        st.markdown(_kpi_card(
            "SCORE", f'{ai_score}<span style="font-size:18px; color:{MUTED};">/100</span>',
            _kpi_sub("Prediction Score"), value_color=status_color
        ), unsafe_allow_html=True)

    with k5:
        st.markdown(_kpi_card(
            "RECOMMENDATION", signal, value_color=status_color, value_size=24, border=status_color
        ), unsafe_allow_html=True)

    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)

    # ============================================================
    # 2) PREDICTION — 2 กล่อง: ซ้าย = gauge % ใหญ่ / ขวา = กล่องคำอธิบาย (สีอ่อนกว่า)
    # ============================================================
    st.markdown(_section_title("📈 PREDICTION"), unsafe_allow_html=True)

    _t = min(1, max(0, prob_up / 100))
    _gx = 50 - 40 * np.cos(np.pi * _t)
    _gy = 50 - 40 * np.sin(np.pi * _t)

    warn_line = ""
    if reliability_low:
        warn_line = (
            f'<div style="font-size:15px; color:{RED}; background:rgba(239,68,68,0.1); border:1px solid {RED}; '
            f'border-radius:8px; padding:10px 14px; margin-top:14px; line-height:1.55;">'
            f'⚠ ความแม่นยำของโมเดลต่ำกว่าเกณฑ์เปรียบเทียบ (baseline) สำหรับหุ้นตัวนี้ — ควรใช้ผลทำนายนี้ด้วยความระมัดระวังเป็นพิเศษ</div>'
        )

    st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-top:none; border-radius:0 0 12px 12px; padding:16px;">
<div style="display:flex; gap:16px; flex-wrap:wrap; align-items:stretch;">
<div style="flex:0 0 320px; max-width:100%; background-color:#0B1120; border:1px solid #1E293B; border-radius:12px; padding:22px 14px; display:flex; align-items:center; justify-content:center;">
<svg viewBox="0 0 100 56" style="width:100%; max-width:290px; height:auto;">
<path d="M 10 50 A 40 40 0 0 1 90 50" fill="none" stroke="#1E293B" stroke-width="9" stroke-linecap="round" />
<path d="M 10 50 A 40 40 0 0 1 {_gx:.1f} {_gy:.1f}" fill="none" stroke="{status_color}" stroke-width="9" stroke-linecap="round" />
<text x="50" y="47" text-anchor="middle" font-size="24" font-weight="bold" fill="#FFFFFF">{prob_up:.0f}%</text>
</svg>
</div>
<div style="flex:1; min-width:300px; background-color:#1A2740; border:1px solid #2A3A55; border-left:4px solid {status_color}; border-radius:12px; padding:22px 26px; display:flex; flex-direction:column; justify-content:center;">
<div style="font-size:14px; font-weight:bold; color:{MUTED}; letter-spacing:1px; margin-bottom:10px;">PROBABILITY OF UP</div>
<div style="font-size:18px; color:#E2E8F0; line-height:1.7;">โมเดล Random Forest ประเมินว่า <b>{ctx.selected_ticker}</b> มีโอกาส<b style="color:{status_color};">{direction_th}</b> <b>{dir_prob:.0f}%</b> ในอีก 10 วันทำการ</div>
<div style="font-size:18px; color:#E2E8F0; line-height:1.7;">ด้วยความแม่นยำการทดสอบ <b>{acc_val:.1f}%</b> ({baseline_note}เกณฑ์เปรียบเทียบ {baseline_val:.1f}%) &nbsp;→&nbsp; คำแนะนำ: <b style="color:{status_color};">{signal}</b></div>
<div style="font-size:14.5px; color:{MUTED}; line-height:1.6; margin-top:12px;">โปรดใช้ประกอบการตัดสินใจลงทุน ควรพิจารณาร่วมกับ Fair Value และ Company Health ก่อนตัดสินใจ ไม่ใช่คำแนะนำโดยตรง</div>{warn_line}
</div>
</div>
</div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)

    # ============================================================
    # 3) FORECAST — ตอบคำถาม "ราคาจะไปทางไหนในอนาคต"
    # ============================================================
    st.markdown(_section_title("📈 FORECAST — PRICE HISTORY + MODEL-IMPLIED RANGE"), unsafe_allow_html=True)

    hist_tail = ctx.stock_daily.tail(150)
    vol_annual = safe(ctx.stock_info.get('volatility'), 25.0) / 100
    daily_vol = vol_annual / np.sqrt(252)
    horizon_days = 10
    future_dates = pd.bdate_range(start=hist_tail['date'].iloc[-1], periods=horizon_days + 1)[1:]
    drift = (prob_up - 50) / 50 * daily_vol * horizon_days
    t_arr = np.arange(1, horizon_days + 1)
    median_path = ctx.current_price * (1 + drift * (t_arr / horizon_days))
    band = ctx.current_price * daily_vol * np.sqrt(t_arr) * 1.28
    upper_path = median_path + band
    lower_path = median_path - band

    fig_forecast = go.Figure()
    fig_forecast.add_trace(go.Scatter(x=future_dates, y=lower_path, mode='lines', line=dict(width=0), showlegend=False, hoverinfo='skip'))
    fig_forecast.add_trace(go.Scatter(x=future_dates, y=upper_path, mode='lines', line=dict(width=0), fill='tonexty',
                                       fillcolor=_hex_to_rgba(status_color, 0.18), name='Prediction Range', hoverinfo='skip'))
    fig_forecast.add_trace(go.Scatter(x=future_dates, y=median_path, mode='lines', line=dict(color=status_color, width=2.2, dash='dash'), name='Model Forecast (Median)'))
    fig_forecast.add_trace(go.Scatter(x=hist_tail['date'], y=hist_tail['close'], mode='lines', line=dict(color=BLUE, width=2.2), name='Actual Price'))

    fig_forecast.update_layout(
        height=350, margin=dict(l=45, r=25, t=10, b=30), paper_bgcolor="#0F172A", plot_bgcolor="#0F172A",
        xaxis=dict(gridcolor="#1E293B", tickfont=dict(size=13, color=MUTED), zeroline=False),
        yaxis=dict(title=dict(text="Price (THB)", font=dict(size=13.5, color=MUTED)), gridcolor="#1E293B", tickfont=dict(size=13, color=MUTED), zeroline=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0, font=dict(size=13, color="#CBD5E1"))
    )
    show_chart(fig_forecast, key="ai_forecast", expand_height=700)
    st.markdown(f"""<div style="font-size:14px; color:{MUTED}; line-height:1.6; padding:6px 18px 12px 18px; background:#0F172A; border:1px solid #1E293B; border-top:none; border-radius:0 0 12px 12px;">
* เส้นทึบฟ้า = ราคาจริงที่เกิดขึ้นแล้ว | เส้นประสี = ค่ากลางที่โมเดลคาดการณ์ | แถบทึบแสง = ช่วงคาดการณ์ (~80%) จาก Volatility จริง ({safe(ctx.stock_info.get('volatility')):.1f}%) — ไม่ใช่การรับประกันผลตอบแทน</div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)

    # ============================================================
    # 4) MODEL EXPLANATION — ตอบคำถาม "โมเดลตัดสินใจจากอะไร"
    # ============================================================
    st.markdown(_section_title("MODEL EXPLANATION"), unsafe_allow_html=True)
    exp_c1, exp_c2 = st.columns([1.4, 1])

    fi = ctx.feat_imp_df[ctx.feat_imp_df['ticker'] == ctx.selected_ticker].sort_values('importance')

    with exp_c1:
        if not fi.empty:
            fig_shap = go.Figure(go.Bar(
                x=fi['importance'], y=fi['feature'], orientation='h', marker=dict(color=BLUE),
                text=[f"{v:.3f}" for v in fi['importance']], textposition='outside', textfont=dict(size=13, color='#CBD5E1')
            ))
            fig_shap.update_layout(
                height=310, margin=dict(l=10, r=50, t=15, b=15), paper_bgcolor="#0F172A", plot_bgcolor="#0F172A",
                xaxis=dict(gridcolor="#1E293B", tickfont=dict(size=13, color=MUTED), zeroline=False),
                yaxis=dict(tickfont=dict(size=13.5, color="#CBD5E1"), gridcolor="#1E293B", zeroline=False), showlegend=False
            )
            show_chart(fig_shap, key="ai_feature_importance", expand_height=650)
        else:
            st.info("ไม่มีข้อมูล Feature Importance")

    with exp_c2:
        top_feat = fi.sort_values('importance', ascending=False).iloc[0]['feature'] if not fi.empty else "N/A"
        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px; padding:22px; min-height:310px; display:flex; flex-direction:column; justify-content:center;">
<div style="font-size:15.5px; font-weight:bold; color:{MUTED}; letter-spacing:0.5px; margin-bottom:12px;">EXPLAINABLE AI SUMMARY</div>
<p style="font-size:17px; color:#CBD5E1; line-height:1.7; margin:0;">โมเดลใช้ 6 ตัวชี้วัดเชิงเทคนิคในการทำนาย โดย feature ที่มีอิทธิพลต่อผลทำนายของ <b>{ctx.selected_ticker}</b> สูงสุดคือ
<b style="color:{BLUE};">{top_feat}</b> — ค่านี้มาจากน้ำหนักจริงที่ Random Forest เรียนรู้ได้ ไม่ใช่ค่าคงที่</p>
</div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)

    # ============================================================
    # 5) MODEL PERFORMANCE — ตอบคำถาม "เชื่อโมเดลนี้ได้แค่ไหน"
    # ============================================================
    st.markdown(_section_title("📊 MODEL PERFORMANCE (TEST SET 2025, actual)"), unsafe_allow_html=True)
    perf_c1, perf_c2 = st.columns([1, 1.3])

    with perf_c1:
        cells = "".join([
            _metric_cell("Accuracy", f"{acc_val:.1f}%"),
            _metric_cell("Precision", f"{safe(ctx.stock_info.get('precision')):.1f}%"),
            _metric_cell("ROC-AUC", f"{safe(ctx.stock_info.get('roc_auc')):.2f}"),
            _metric_cell("F1-Score", f"{safe(ctx.stock_info.get('f1_score')):.1f}%"),
        ])
        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-top:none; border-radius:0 0 12px 12px; padding:16px; min-height:350px;">
<div style="display:grid; grid-template-columns: repeat(2, 1fr); gap:10px;">{cells}</div>
<div style="font-size:15px; color:{RED if reliability_low else GREEN}; border-top:1px dashed #1E293B; padding-top:12px; margin-top:14px; line-height:1.55;">
vs. Baseline (naive majority-class): <b>{baseline_val:.1f}%</b> — {"ต่ำกว่า baseline ⚠" if reliability_low else "สูงกว่า baseline ✓"}
</div>
<div style="font-size:13.5px; color:{MUTED}; border-top:1px solid #1E293B; padding-top:10px; margin-top:10px;">Validation: Out-of-time (Train 2023-24 / Test 2025)</div>
</div>""", unsafe_allow_html=True)

    with perf_c2:
        st.markdown(_section_title("HISTORICAL PREDICTION PERFORMANCE (Test Set, actual)"), unsafe_allow_html=True)
        bt = ctx.backtest_df[ctx.backtest_df['ticker'] == ctx.selected_ticker].sort_values('date') if not ctx.backtest_df.empty else pd.DataFrame()
        if not bt.empty:
            bt_q = bt.set_index('date').resample('W').mean(numeric_only=True).dropna().reset_index()
            fig_bt = go.Figure()
            fig_bt.add_trace(go.Scatter(x=bt_q['date'], y=bt_q['actual_close'], mode='lines', name='Actual Close', line=dict(color=BLUE, width=1.8), yaxis='y1'))
            fig_bt.add_trace(go.Scatter(x=bt_q['date'], y=bt_q['predicted_up_prob'] * 100, mode='lines', name='Predicted Up Prob (%)', line=dict(color=status_color, width=1.8, dash='dash'), yaxis='y2'))
            fig_bt.update_layout(
                height=235, margin=dict(l=30, r=30, t=5, b=18), paper_bgcolor="#0F172A", plot_bgcolor="#0F172A",
                xaxis=dict(tickfont=dict(size=12.5, color=MUTED), gridcolor="#1E293B"),
                yaxis=dict(tickfont=dict(size=12.5, color=MUTED), gridcolor="#1E293B", zeroline=False),
                yaxis2=dict(overlaying='y', side='right', showgrid=False, tickfont=dict(size=12.5, color=MUTED)),
                showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0, font=dict(size=12.5, color="#CBD5E1"))
            )
            show_chart(fig_bt, key="ai_backtest", expand_height=550)
            st.markdown(f"""<div style="background:#0F172A; border:1px solid #1E293B; border-top:none; border-radius:0 0 12px 12px; padding:8px 14px 12px 14px; font-size:13.5px; color:{MUTED};">* Test-set Accuracy: {acc_val:.1f}%</div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div style="background:#0F172A; border:1px solid #1E293B; border-top:none; border-radius:0 0 12px 12px; padding:20px;">""", unsafe_allow_html=True)
            st.info("ไม่มีข้อมูล Backtest")
            st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("📋 รายละเอียดโมเดลและข้อมูล (Model & Data Detail)"):
        n_train = len(ctx.stock_daily[ctx.stock_daily['date'] < '2025-01-01'])
        n_test = len(ctx.stock_daily[ctx.stock_daily['date'] >= '2025-01-01'])
        st.markdown(f"""<ul style="font-size:16px; line-height:1.9; color:#CBD5E1; margin:0; padding-left:22px;">
<li><b>Model</b>: Random Forest (n_estimators=200, max_depth=4)</li>
<li><b>Target</b>: 10-Day Forward Direction (ราคาปิด 10 วันข้างหน้าสูงกว่าปัจจุบันหรือไม่)</li>
<li><b>Train Samples</b>: {n_train} แถว (2023–2024)</li>
<li><b>Test Samples</b>: {n_test} แถว (2025)</li>
<li><b>Features</b>: 6 ตัว (Technical) — close, EMA20, EMA50, RSI14, MACD, ADX</li>
<li><b>Data as of</b>: {ctx.stock_info.get('latest_date','-')}</li>
<li><b>Validation</b>: Out-of-time (แบ่งตามช่วงเวลาจริง ไม่ใช่สุ่มแบ่ง)</li>
</ul>""", unsafe_allow_html=True)

    render_nav_footer("m4", prev_page=" ⏱️ Entry Timing", next_page=" 🛡️ Risk Analysis")
