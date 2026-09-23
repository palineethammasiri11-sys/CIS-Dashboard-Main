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

=== CHANGELOG (v6 — ลดหน้าจอเหลือ Probability เป็นหลัก, ย้าย Accuracy ไปใช้แค่ในรายงาน) ===
- ตัดการ์ด KPI "SCORE" ออก (เหลือ 4 การ์ด: Price, Direction, Probability, Recommendation)
- เพิ่มจุดสีเล็กๆ (●) ข้างตัวเลข Probability สะท้อนความน่าเชื่อถือของโมเดล (มาจาก reliability_low เดิม)
  โดยไม่แสดงตัวเลข accuracy/baseline บนหน้าจอเลย — ใช้แค่สีเป็นสัญญาณ
- ตัดตัวเลข accuracy/baseline ออกจากประโยคอธิบายในกล่อง PREDICTION
- ตัดส่วน "MODEL PERFORMANCE" (Accuracy/Precision/ROC-AUC/F1 + Historical Backtest chart) ออกทั้งหมด
- ตัด expander "Model & Data Detail" ออก (เก็บไว้ใส่รายงาน/สไลด์แยกต่างหาก ไม่ใส่ในตัว Dashboard)
- calculate_modules/ai_prediction.py ไม่มีการแก้ไขใดๆ — ยังคำนวณและเก็บ accuracy, precision, recall,
  baseline_accuracy ไว้ครบใน DB เหมือนเดิมทุกประการ เพื่อให้ดึงไปสรุปทำรายงานได้ภายหลัง
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


def _hex_to_rgba(hex_color, alpha):
    hex_color = hex_color.lstrip('#')
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _section_title(text):
    return f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px 12px 0 0; padding:12px 16px 0 16px;">
<div><span style="font-size:15.5px; font-weight:bold; color:#94A3B8; letter-spacing:0.5px;">{text}</span></div></div>"""


def render(ctx):
    st.markdown(f"""<div style="margin-bottom:14px;">
<div style="font-size:14.5px; color:#64748B; margin-bottom:2px;">Home / Module 4 / AI Prediction</div>
<h2 style="margin:0; font-size:23px; font-weight:bold; color:#F8FAFC; letter-spacing:0.5px;">AI PREDICTION</h2>
</div>""", unsafe_allow_html=True)

    # ============================================================
    # ถ้าเป็นค่า fallback (ข้อมูลไม่พอเทรนโมเดลจริง) ห้ามแสดง KPI/กราฟเหมือนเป็นผลจริง
    # ============================================================
    if ctx.stock_info.get('is_fallback', False):
        st.markdown(f"""<div style="background:rgba(239,68,68,0.1); border:1px solid {RED}; border-radius:12px; padding:28px; text-align:center;">
<div style="font-size:21px; font-weight:bold; color:{RED}; margin-bottom:10px;">⚠ ข้อมูลไม่เพียงพอสำหรับ {ctx.selected_ticker}</div>
<p style="font-size:15px; color:#CBD5E1; line-height:1.65; margin:0; max-width:640px; margin:0 auto;">
หุ้นตัวนี้มีข้อมูลราคาย้อนหลังไม่พอสำหรับเทรนโมเดล Random Forest จริง (ต้องการอย่างน้อย Train 50 แถว และ Test 20 แถว)
ตัวเลขที่เคยแสดงในหน้านี้เป็นเพียง<b>ค่าตั้งต้นสำรอง (placeholder)</b> ไม่ใช่ผลจากการเทรนโมเดลจริงแต่อย่างใด
จึง<b style="color:{RED};">ไม่ควรใช้ประกอบการตัดสินใจลงทุน</b></p>
</div>""", unsafe_allow_html=True)
        render_nav_footer("m4", prev_page=" ⏱️ Entry Timing", next_page=" 🛡️ Risk Analysis")
        return

    # ============================================================
    # แหล่งความจริงเดียวของสถานะทำนาย + ความน่าเชื่อถือ
    # หมายเหตุ: acc_val, baseline_val, prec_val, rec_val ใช้ "คำนวณสี/สัญลักษณ์เตือน" เท่านั้น
    # จะไม่ถูกพิมพ์เป็นตัวเลขที่ใดในหน้านี้เลย (เก็บไว้ในฐานข้อมูลเพื่อใช้ทำรายงานแยกต่างหาก)
    # ============================================================
    prob_up = safe(ctx.stock_info.get('prob_up'), 50)
    down_prob = round(100 - prob_up, 1)
    acc_val = safe(ctx.stock_info.get('accuracy'), 50)
    baseline_val = safe(ctx.stock_info.get('baseline_accuracy'), acc_val)
    prec_val = safe(ctx.stock_info.get('precision'), 1)
    rec_val = safe(ctx.stock_info.get('recall'), 1)
    signal = ctx.stock_info.get('ai_signal', '-')

    reliability_low = (acc_val <= baseline_val) or (prec_val == 0) or (rec_val == 0)

    if prob_up >= 70:
        status_color = GREEN
    elif prob_up >= 50:
        status_color = AMBER
    else:
        status_color = RED

    if reliability_low and status_color == GREEN:
        status_color = AMBER

    direction_th = "ขาขึ้น" if prob_up >= 50 else "ขาลง"
    signal_display = f"{signal} ⚠" if reliability_low else signal

    # ============================================================
    # 1) OVERVIEW — แถบ KPI (เหลือ 4 ช่อง ตัด SCORE ออก)
    # ============================================================
    k1, k2, k3, k4 = st.columns(4)

    with k1:
        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px; padding:16px 12px; text-align:center; min-height:122px;">
<div style="font-size:12.5px; font-weight:bold; color:#64748B; letter-spacing:1px;">PRICE</div>
<div style="font-size:34px; font-weight:bold; color:#F8FAFC; line-height:1.15; margin-top:4px;">{ctx.current_price:,.2f}</div>
<div style="font-size:13px; font-weight:bold; color:{ctx.change_color};">{ctx.change_val:+.2f} ({ctx.change_pct:+.2f}%) {ctx.arrow_sign}</div>
</div>""", unsafe_allow_html=True)

    with k2:
        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px; padding:16px 12px; text-align:center; min-height:122px;">
<div style="font-size:12.5px; font-weight:bold; color:#64748B; letter-spacing:1px;">DIRECTION (10D)</div>
<div style="font-size:34px; font-weight:bold; color:{status_color}; line-height:1.15; margin-top:4px;">{direction_th}</div>
<div style="font-size:13px; color:#64748B;">10 Trading Days</div>
</div>""", unsafe_allow_html=True)

    with k3:
        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px; padding:16px 12px; text-align:center; min-height:122px;">
<div style="font-size:12.5px; font-weight:bold; color:#64748B; letter-spacing:1px;">PROBABILITY</div>
<div style="font-size:34px; font-weight:bold; color:{status_color}; line-height:1.15; margin-top:4px; display:flex; align-items:center; justify-content:center; gap:8px;">
<span>{prob_up:.0f}%</span><span style="display:inline-block; width:11px; height:11px; border-radius:50%; background:{status_color};"></span>
</div>
<div style="font-size:13px; color:#64748B;">Down: {down_prob:.0f}%</div>
</div>""", unsafe_allow_html=True)

    with k4:
        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid {status_color}; border-radius:12px; padding:16px 12px; text-align:center; min-height:122px;">
<div style="font-size:12.5px; font-weight:bold; color:#64748B; letter-spacing:1px;">RECOMMENDATION</div>
<div style="font-size:22px; font-weight:bold; color:{status_color}; line-height:1.3; margin-top:6px;">{signal_display}</div>
</div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:22px;'></div>", unsafe_allow_html=True)

    # ============================================================
    # 2) PREDICTION — gauge + ประโยคอธิบาย (ไม่มีตัวเลข accuracy/baseline)
    # ============================================================
    st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px; padding:10px 16px; margin-bottom:10px;">
<span style="font-size:15.5px; font-weight:bold; color:#94A3B8; letter-spacing:0.5px;">📈 PREDICTION</span>
</div>""", unsafe_allow_html=True)

    _t = min(1, max(0, prob_up / 100))
    _gx = 50 - 40 * np.cos(np.pi * _t)
    _gy = 50 - 40 * np.sin(np.pi * _t)

    pred_left, pred_right = st.columns([1, 1.6])

    with pred_left:
        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px; padding:20px; text-align:center; min-height:230px; display:flex; flex-direction:column; justify-content:center; align-items:center;">
<svg viewBox="0 0 100 58" style="width:230px; height:135px;">
<path d="M 10 50 A 40 40 0 0 1 90 50" fill="none" stroke="#1E293B" stroke-width="10" stroke-linecap="round" />
<path d="M 10 50 A 40 40 0 0 1 {_gx:.1f} {_gy:.1f}" fill="none" stroke="{status_color}" stroke-width="10" stroke-linecap="round" />
<text x="50" y="44" text-anchor="middle" font-size="27" font-weight="bold" fill="#FFFFFF">{prob_up:.0f}%</text>
</svg>
</div>""", unsafe_allow_html=True)

    with pred_right:
        st.markdown(f"""<div style="background-color:#141E33; border:1px solid #263248; border-radius:12px; padding:22px; min-height:230px; display:flex; flex-direction:column; justify-content:center;">
<p style="font-size:16.5px; color:#E2E8F0; line-height:1.65; margin:0;">
โมเดล Random Forest ประเมินว่า <b>{ctx.selected_ticker}</b> มีโอกาส<b style="color:{status_color};">{direction_th}</b>
<b>{prob_up:.0f}%</b> ในอีก 10 วันทำการ &nbsp;→&nbsp; คำแนะนำ:
<b style="color:{status_color};">{signal}</b>
</p>
<p style="font-size:14px; color:#94A3B8; margin:12px 0 0 0; line-height:1.5;">โปรดใช้ประกอบการตัดสินใจลงทุน ควรพิจารณาร่วมกับ Fair Value และ Company Health ก่อนตัดสินใจ ไม่ใช่คำแนะนำโดยตรง</p>
</div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:22px;'></div>", unsafe_allow_html=True)

    # ============================================================
    # 3) FORECAST — ราคาจะไปทางไหนในอนาคต
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
        height=330, margin=dict(l=35, r=25, t=10, b=25), paper_bgcolor="#0F172A", plot_bgcolor="#0F172A",
        xaxis=dict(gridcolor="#1E293B", tickfont=dict(size=11.5, color="#64748B"), zeroline=False),
        yaxis=dict(title=dict(text="Price (THB)", font=dict(size=12, color="#64748B")), gridcolor="#1E293B", tickfont=dict(size=11.5, color="#64748B"), zeroline=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0, font=dict(size=11.5, color="#CBD5E1"))
    )
    show_chart(fig_forecast, key="ai_forecast", expand_height=700)
    st.markdown(f"""<div style="font-size:12.5px; color:#64748B; padding:0 16px 10px 16px; background:#0F172A; border:1px solid #1E293B; border-top:none; border-radius:0 0 12px 12px;">
* เส้นทึบฟ้า = ราคาจริงที่เกิดขึ้นแล้ว | เส้นประสี = ค่ากลางที่โมเดลคาดการณ์ | แถบทึบแสง = ช่วงคาดการณ์ (~80%) จาก Volatility จริง ({safe(ctx.stock_info.get('volatility')):.1f}%) — ไม่ใช่การรับประกันผลตอบแทน</div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:22px;'></div>", unsafe_allow_html=True)

    # ============================================================
    # 4) MODEL EXPLANATION — โมเดลตัดสินใจจากอะไร
    # ============================================================
    st.markdown(_section_title("MODEL EXPLANATION"), unsafe_allow_html=True)
    exp_c1, exp_c2 = st.columns([1.4, 1])

    fi = ctx.feat_imp_df[ctx.feat_imp_df['ticker'] == ctx.selected_ticker].sort_values('importance')

    with exp_c1:
        if not fi.empty:
            fig_shap = go.Figure(go.Bar(
                x=fi['importance'], y=fi['feature'], orientation='h', marker=dict(color=BLUE),
                text=[f"{v:.3f}" for v in fi['importance']], textposition='outside', textfont=dict(size=11.5, color='#CBD5E1')
            ))
            fig_shap.update_layout(
                height=280, margin=dict(l=10, r=35, t=15, b=15), paper_bgcolor="#0F172A", plot_bgcolor="#0F172A",
                xaxis=dict(gridcolor="#1E293B", tickfont=dict(size=11.5, color="#64748B"), zeroline=False),
                yaxis=dict(tickfont=dict(size=11.5, color="#CBD5E1"), gridcolor="#1E293B", zeroline=False), showlegend=False
            )
            show_chart(fig_shap, key="ai_feature_importance", expand_height=650)
        else:
            st.info("ไม่มีข้อมูล Feature Importance")

    with exp_c2:
        top_feat = fi.sort_values('importance', ascending=False).iloc[0]['feature'] if not fi.empty else "N/A"
        st.markdown(f"""<div style="background-color:#0F172A; border:1px solid #1E293B; border-radius:12px; padding:16px; min-height:280px; display:flex; flex-direction:column; justify-content:center;">
<div style="font-size:14px; font-weight:bold; color:#94A3B8; letter-spacing:0.5px; margin-bottom:8px;">EXPLAINABLE AI SUMMARY</div>
<p style="font-size:15px; color:#CBD5E1; line-height:1.6; margin:0;">โมเดลใช้ 6 ตัวชี้วัดเชิงเทคนิคในการทำนาย โดย feature ที่มีอิทธิพลต่อผลทำนายของ <b>{ctx.selected_ticker}</b> สูงสุดคือ
<b style="color:{BLUE};">{top_feat}</b> — ค่านี้มาจากน้ำหนักจริงที่ Random Forest เรียนรู้ได้ ไม่ใช่ค่าคงที่</p>
</div>""", unsafe_allow_html=True)

    render_nav_footer("m4", prev_page=" ⏱️ Entry Timing", next_page=" 🛡️ Risk Analysis")
