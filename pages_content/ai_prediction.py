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


GREEN = "#10B981"
AMBER = "#F59E0B"
RED = "#EF4444"
BLUE = "#0284C7"
MUTED = "#64748B"


def _hex_to_rgba(hex_color, alpha):
    hex_color = hex_color.lstrip('#')
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _section_title(text):
    return f"""<div style="background-color:#FFFFFF; border:1px solid #D9E2EC; border-radius:12px 12px 0 0; padding:14px 18px 2px 18px;">
<div><span style="font-size:13px; font-weight:bold; color:{MUTED}; letter-spacing:0.5px;">{text}</span></div></div>"""


def _kpi_card(
    label,
    value_html,
    sub_html="",
    value_color="#0F172A",
    value_size=28,
    border="#D9E2EC",
    bg_color="#FFFFFF",
    label_color=MUTED
):
    """การ์ด KPI ใบเดียว"""
    return (
        f'<div style="background-color:{bg_color}; border:1px solid {border}; border-radius:12px; padding:14px 16px; text-align:left; height:120px; box-sizing:border-box; display:flex; flex-direction:column; justify-content:center;">'
        f'<div style="font-size:11px; font-weight:bold; color:{label_color}; letter-spacing:1px;">{label}</div>'
        f'<div style="font-size:{value_size}px; font-weight:bold; color:{value_color}; line-height:1.2; margin-top:4px;">{value_html}</div>'
        f'{sub_html}'
        f'</div>'
    )


def _kpi_sub(text, color=MUTED, bold=False):
    weight = "bold" if bold else "normal"
    return f'<div style="font-size:11px; font-weight:{weight}; color:{color}; margin-top:2px;">{text}</div>'


def _metric_cell(label, value):
    return (
        f'<div style="background:#F8FAFC; border:1px solid #D9E2EC; border-radius:8px; padding:14px 6px; text-align:center;">'
        f'<div style="font-size:12px; color:{MUTED};">{label}</div>'
        f'<div style="font-size:21px; font-weight:bold; color:#0F172A; line-height:1.35;">{value}</div></div>'
    )


def render(ctx):

    # ============================================================
    # แหล่งความจริงเดียวของสถานะทำนาย
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
    dir_prob = prob_up if prob_up >= 50 else down_prob

    reliability_low = acc_val < baseline_val
    baseline_note = "สูงกว่า" if not reliability_low else "ต่ำกว่า"

    st.markdown("""
    <div style="margin-bottom:20px;">
        <div style="font-size:19px; font-weight:700; color:#0F172A; letter-spacing:0.3px;">
            AI PREDICTION
        </div>
        <div style="font-size:12px; color:#64748B; margin-top:4px;">
            ประเมินทิศทางราคาหุ้นในอีก 10 วันทำการด้วยโมเดล Random Forest
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ============================================================
    # 1) OVERVIEW
    # ============================================================

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        st.markdown(
            _kpi_card(
                "PRICE",
                f"{ctx.current_price:,.2f}",
                _kpi_sub(
                    f"{ctx.change_val:+.2f} ({ctx.change_pct:+.2f}%) {ctx.arrow_sign}",
                    ctx.change_color,
                    bold=True
                )
            ),
            unsafe_allow_html=True
        )

    with k2:
        st.markdown(
            _kpi_card(
                "DIRECTION (10D)",
                direction_th,
                _kpi_sub("10 Trading Days"),
                value_color=status_color,
                border=status_color,
                bg_color=_hex_to_rgba(status_color, 0.08)
            ),
            unsafe_allow_html=True
        )

    with k3:
        st.markdown(
            _kpi_card(
                "PROBABILITY",
                f"{prob_up:.0f}%",
                _kpi_sub(f"Down: {down_prob:.0f}%"),
                value_color=status_color,
                border=status_color,
                bg_color=_hex_to_rgba(status_color, 0.08)
            ),
            unsafe_allow_html=True
        )

    with k4:
        st.markdown(
            _kpi_card(
                "RECOMMENDATION",
                signal,
                value_color="#0F172A",
                value_size=21,
                border="#D9E2EC",
                bg_color="#FFFFFF",
                label_color=MUTED
            ),
            unsafe_allow_html=True
        )

    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)

    # ============================================================
    # 2) PREDICTION
    # ============================================================

    st.markdown(
        _section_title("📈 PREDICTION"),
        unsafe_allow_html=True
    )

    _t = min(1, max(0, prob_up / 100))
    _gx = 50 - 40 * np.cos(np.pi * _t)
    _gy = 50 - 40 * np.sin(np.pi * _t)

    warn_line = ""

    if reliability_low:
        warn_line = (
            f'<div style="font-size:12px; color:{RED}; background:rgba(239,68,68,0.1); border:1px solid {RED}; '
            f'border-radius:8px; padding:10px 14px; margin-top:14px; line-height:1.55;">'
            f'⚠ ความแม่นยำของโมเดลต่ำกว่าเกณฑ์เปรียบเทียบ (baseline) สำหรับหุ้นตัวนี้ — ควรใช้ผลทำนายนี้ด้วยความระมัดระวังเป็นพิเศษ</div>'
        )

    st.markdown(
        f"""<div style="background-color:#FFFFFF; border:1px solid #D9E2EC; border-top:none; border-radius:0 0 12px 12px; padding:16px;">
<div style="display:flex; gap:16px; flex-wrap:wrap; align-items:stretch;">

<div style="flex:0 0 320px; max-width:100%; background-color:#F8FAFC; border:1px solid #D9E2EC; border-radius:12px; padding:22px 14px; display:flex; align-items:center; justify-content:center;">
<svg viewBox="0 0 100 56" style="width:100%; max-width:180px; height:auto;">
<path d="M 10 50 A 40 40 0 0 1 90 50" fill="none" stroke="#D9E2EC" stroke-width="6" stroke-linecap="round" />
<path d="M 10 50 A 40 40 0 0 1 {_gx:.1f} {_gy:.1f}" fill="none" stroke="{status_color}" stroke-width="6" stroke-linecap="round" />
<text x="50" y="47" text-anchor="middle" font-size="17" font-weight="bold" fill="#0F172A">{prob_up:.0f}%</text>
</svg>
</div>

<div style="flex:1; min-width:300px; background-color:#F3F7FB; border:1px solid #C7D5E3; border-left:4px solid {status_color}; border-radius:12px; padding:22px 26px; display:flex; flex-direction:column; justify-content:center;">

<div style="font-size:12px; font-weight:bold; color:{MUTED}; letter-spacing:1px; margin-bottom:10px;">
PROBABILITY OF UP
</div>

<div style="font-size:15px; color:#334155; line-height:1.7;">
โมเดล Random Forest ประเมินว่า <b>{ctx.selected_ticker}</b> มีโอกาส
<b style="color:{status_color};">{direction_th}</b>
<b>{dir_prob:.0f}%</b> ในอีก 10 วันทำการ
</div>

<div style="font-size:15px; color:#334155; line-height:1.7;">
ด้วยความแม่นยำการทดสอบ <b>{acc_val:.1f}%</b>
({baseline_note}เกณฑ์เปรียบเทียบ {baseline_val:.1f}%)
&nbsp;→&nbsp; คำแนะนำ:
<b style="color:{status_color};">{signal}</b>
</div>

<div style="font-size:12px; color:{MUTED}; line-height:1.6; margin-top:12px;">
โปรดใช้ประกอบการตัดสินใจลงทุน ควรพิจารณาร่วมกับ Fair Value และ Company Health ก่อนตัดสินใจ ไม่ใช่คำแนะนำโดยตรง
</div>

{warn_line}

</div>
</div>
</div>""",
        unsafe_allow_html=True
    )

    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)

    # ============================================================
    # 3) FORECAST
    # ============================================================

    forecast_title, forecast_info = st.columns([0.96, 0.06], gap="small")

    with forecast_title:
        st.markdown(
            """
            <div style="
                background-color:#FFFFFF;
                border:1px solid #D9E2EC;
                border-right:none;
                border-radius:12px 0 0 0;
                padding:14px 18px 10px 18px;
                height:48px;
                box-sizing:border-box;
            ">
                <span style="
                    font-size:13px;
                    font-weight:bold;
                    color:#64748B;
                    letter-spacing:0.5px;
                ">
                    📈 FORECAST — PRICE HISTORY + MODEL-IMPLIED RANGE
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )

    with forecast_info:
        with st.popover("ⓘ", use_container_width=True):
            st.markdown(
                """
                **คำอธิบายกราฟ**

                - เส้นทึบฟ้า = ราคาจริงที่เกิดขึ้นแล้ว
                - เส้นประสี = ค่ากลางที่โมเดลคาดการณ์
                - แถบทึบแสง = ช่วงคาดการณ์ประมาณ 80%
                - คำนวณจาก Volatility จริง
                - ไม่ใช่การรับประกันผลตอบแทน
                """
            )

    hist_tail = ctx.stock_daily.tail(150)

    vol_annual = safe(
        ctx.stock_info.get('volatility'),
        25.0
    ) / 100

    daily_vol = vol_annual / np.sqrt(252)

    horizon_days = 10

    future_dates = pd.bdate_range(
        start=hist_tail['date'].iloc[-1],
        periods=horizon_days + 1
    )[1:]

    drift = (
        (prob_up - 50) / 50
        * daily_vol
        * horizon_days
    )

    t_arr = np.arange(1, horizon_days + 1)

    median_path = (
        ctx.current_price
        * (1 + drift * (t_arr / horizon_days))
    )

    band = (
        ctx.current_price
        * daily_vol
        * np.sqrt(t_arr)
        * 1.28
    )

    upper_path = median_path + band
    lower_path = median_path - band

    fig_forecast = go.Figure()

    fig_forecast.add_trace(
        go.Scatter(
            x=future_dates,
            y=lower_path,
            mode='lines',
            line=dict(width=0),
            showlegend=False,
            hoverinfo='skip'
        )
    )

    fig_forecast.add_trace(
        go.Scatter(
            x=future_dates,
            y=upper_path,
            mode='lines',
            line=dict(width=0),
            fill='tonexty',
            fillcolor=_hex_to_rgba(status_color, 0.18),
            name='Prediction Range',
            hoverinfo='skip'
        )
    )

    fig_forecast.add_trace(
        go.Scatter(
            x=future_dates,
            y=median_path,
            mode='lines',
            line=dict(
                color=status_color,
                width=2.2,
                dash='dash'
            ),
            name='Model Forecast (Median)'
        )
    )

    fig_forecast.add_trace(
        go.Scatter(
            x=hist_tail['date'],
            y=hist_tail['close'],
            mode='lines',
            line=dict(
                color=BLUE,
                width=2.2
            ),
            name='Actual Price'
        )
    )

    fig_forecast.update_layout(
        height=350,
        margin=dict(l=45, r=25, t=10, b=30),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        xaxis=dict(
            gridcolor="#D9E2EC",
            tickfont=dict(
                size=11,
                color=MUTED
            ),
            zeroline=False
        ),
        yaxis=dict(
            title=dict(
                text="Price (THB)",
                font=dict(
                    size=11.5,
                    color=MUTED
                )
            ),
            gridcolor="#D9E2EC",
            tickfont=dict(
                size=11,
                color=MUTED
            ),
            zeroline=False
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="left",
            x=0,
            font=dict(
                size=11,
                color="#334155"
            )
        )
    )

    show_chart(
        fig_forecast,
        key="ai_forecast",
        expand_height=700
    )

    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)

    # ============================================================
    # 4) MODEL EXPLANATION
    # ============================================================

    st.markdown(
        _section_title("MODEL EXPLANATION"),
        unsafe_allow_html=True
    )

    exp_c1, exp_c2 = st.columns([1.4, 1])

    fi = ctx.feat_imp_df[
        ctx.feat_imp_df['ticker'] == ctx.selected_ticker
    ].sort_values('importance')

    with exp_c1:

        if not fi.empty:

            fig_shap = go.Figure(
                go.Bar(
                    x=fi['importance'],
                    y=fi['feature'],
                    orientation='h',
                    marker=dict(color=BLUE),
                    text=[
                        f"{v:.3f}"
                        for v in fi['importance']
                    ],
                    textposition='outside',
                    textfont=dict(
                        size=11,
                        color='#334155'
                    )
                )
            )

            fig_shap.update_layout(
                height=310,
                margin=dict(
                    l=10,
                    r=50,
                    t=15,
                    b=15
                ),
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#FFFFFF",
                xaxis=dict(
                    gridcolor="#D9E2EC",
                    tickfont=dict(
                        size=11,
                        color=MUTED
                    ),
                    zeroline=False
                ),
                yaxis=dict(
                    tickfont=dict(
                        size=11.5,
                        color="#334155"
                    ),
                    gridcolor="#D9E2EC",
                    zeroline=False
                ),
                showlegend=False
            )

            show_chart(
                fig_shap,
                key="ai_feature_importance",
                expand_height=650
            )

        else:
            st.info("ไม่มีข้อมูล Feature Importance")

    with exp_c2:

        top_feat = (
            fi.sort_values(
                'importance',
                ascending=False
            ).iloc[0]['feature']
            if not fi.empty
            else "N/A"
        )

        st.markdown(
            f"""<div style="background-color:#FFFFFF; border:1px solid #D9E2EC; border-radius:12px; padding:22px; min-height:310px; display:flex; flex-direction:column; justify-content:center;">
<div style="font-size:13.5px; font-weight:bold; color:{MUTED}; letter-spacing:0.5px; margin-bottom:12px;">
EXPLAINABLE AI SUMMARY
</div>
<p style="font-size:14px; color:#334155; line-height:1.7; margin:0;">
โมเดลใช้ 6 ตัวชี้วัดเชิงเทคนิคในการทำนาย โดย feature ที่มีอิทธิพลต่อผลทำนายของ
<b>{ctx.selected_ticker}</b> สูงสุดคือ
<b style="color:{BLUE};">{top_feat}</b>
— ค่านี้มาจากน้ำหนักจริงที่ Random Forest เรียนรู้ได้ ไม่ใช่ค่าคงที่
</p>
</div>""",
            unsafe_allow_html=True
        )

    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)

    # ============================================================
    # 5) MODEL PERFORMANCE
    # ============================================================

    st.markdown(
        _section_title(
            "📊 MODEL PERFORMANCE (TEST SET 2025, actual)"
        ),
        unsafe_allow_html=True
    )

    perf_c1, perf_c2 = st.columns([1, 1.3])

    with perf_c1:

        cells = "".join([
            _metric_cell(
                "Accuracy",
                f"{acc_val:.1f}%"
            ),
            _metric_cell(
                "Precision",
                f"{safe(ctx.stock_info.get('precision')):.1f}%"
            ),
            _metric_cell(
                "ROC-AUC",
                f"{safe(ctx.stock_info.get('roc_auc')):.2f}"
            ),
            _metric_cell(
                "F1-Score",
                f"{safe(ctx.stock_info.get('f1_score')):.1f}%"
            ),
        ])

        st.markdown(
            f"""<div style="background-color:#FFFFFF; border:1px solid #D9E2EC; border-top:none; border-radius:0 0 12px 12px; padding:16px; min-height:350px;">
<div style="display:grid; grid-template-columns: repeat(2, 1fr); gap:10px;">{cells}</div>
<div style="font-size:12px; color:{RED if reliability_low else GREEN}; border-top:1px dashed #D9E2EC; padding-top:12px; margin-top:14px; line-height:1.55;">
vs. Baseline (naive majority-class): <b>{baseline_val:.1f}%</b> — {"ต่ำกว่า baseline ⚠" if reliability_low else "สูงกว่า baseline ✓"}
</div>
<div style="font-size:11px; color:{MUTED}; border-top:1px solid #D9E2EC; padding-top:10px; margin-top:10px;">
Validation: Out-of-time (Train 2023-24 / Test 2025)
</div>
</div>""",
            unsafe_allow_html=True
        )

    with perf_c2:

        st.markdown(
            _section_title(
                "HISTORICAL PREDICTION PERFORMANCE (Test Set, actual)"
            ),
            unsafe_allow_html=True
        )

        bt = (
            ctx.backtest_df[
                ctx.backtest_df['ticker'] == ctx.selected_ticker
            ].sort_values('date')
            if not ctx.backtest_df.empty
            else pd.DataFrame()
        )

        if not bt.empty:

            bt_q = (
                bt.set_index('date')
                .resample('W')
                .mean(numeric_only=True)
                .dropna()
                .reset_index()
            )

            fig_bt = go.Figure()

            fig_bt.add_trace(
                go.Scatter(
                    x=bt_q['date'],
                    y=bt_q['actual_close'],
                    mode='lines',
                    name='Actual Close',
                    line=dict(
                        color=BLUE,
                        width=1.8
                    ),
                    yaxis='y1'
                )
            )

            fig_bt.add_trace(
                go.Scatter(
                    x=bt_q['date'],
                    y=bt_q['predicted_up_prob'] * 100,
                    mode='lines',
                    name='Predicted Up Prob (%)',
                    line=dict(
                        color=status_color,
                        width=1.8,
                        dash='dash'
                    ),
                    yaxis='y2'
                )
            )

            fig_bt.update_layout(
                height=235,
                margin=dict(
                    l=30,
                    r=30,
                    t=5,
                    b=18
                ),
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#FFFFFF",
                xaxis=dict(
                    tickfont=dict(
                        size=10.5,
                        color=MUTED
                    ),
                    gridcolor="#D9E2EC"
                ),
                yaxis=dict(
                    tickfont=dict(
                        size=10.5,
                        color=MUTED
                    ),
                    gridcolor="#D9E2EC",
                    zeroline=False
                ),
                yaxis2=dict(
                    overlaying='y',
                    side='right',
                    showgrid=False,
                    tickfont=dict(
                        size=10.5,
                        color=MUTED
                    )
                ),
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.01,
                    xanchor="left",
                    x=0,
                    font=dict(
                        size=10.5,
                        color="#334155"
                    )
                )
            )

            show_chart(
                fig_bt,
                key="ai_backtest",
                expand_height=550
            )

            st.markdown(
                f"""<div style="background:#FFFFFF; border:1px solid #D9E2EC; border-top:none; border-radius:0 0 12px 12px; padding:8px 14px 12px 14px; font-size:11px; color:{MUTED};">
* Test-set Accuracy: {acc_val:.1f}%
</div>""",
                unsafe_allow_html=True
            )

        else:

            st.markdown(
                """<div style="background:#FFFFFF; border:1px solid #D9E2EC; border-top:none; border-radius:0 0 12px 12px; padding:20px;">""",
                unsafe_allow_html=True
            )

            st.info("ไม่มีข้อมูล Backtest")

            st.markdown(
                "</div>",
                unsafe_allow_html=True
            )

    # ============================================================
    # MODEL & DATA DETAIL
    # ============================================================

    with st.expander(
        "📋 รายละเอียดโมเดลและข้อมูล (Model & Data Detail)"
    ):

        n_train = len(
            ctx.stock_daily[
                ctx.stock_daily['date'] < '2025-01-01'
            ]
        )

        n_test = len(
            ctx.stock_daily[
                ctx.stock_daily['date'] >= '2025-01-01'
            ]
        )

        st.markdown(
            f"""<ul style="font-size:13px; line-height:1.9; color:#334155; margin:0; padding-left:22px;">
<li><b>Model</b>: Random Forest (n_estimators=200, max_depth=4)</li>
<li><b>Target</b>: 10-Day Forward Direction (ราคาปิด 10 วันข้างหน้าสูงกว่าปัจจุบันหรือไม่)</li>
<li><b>Train Samples</b>: {n_train} แถว (2023–2024)</li>
<li><b>Test Samples</b>: {n_test} แถว (2025)</li>
<li><b>Features</b>: 6 ตัว (Technical) — close, EMA20, EMA50, RSI14, MACD, ADX</li>
<li><b>Data as of</b>: {ctx.stock_info.get('latest_date','-')}</li>
<li><b>Validation</b>: Out-of-time (แบ่งตามช่วงเวลาจริง ไม่ใช่สุ่มแบ่ง)</li>
</ul>""",
            unsafe_allow_html=True
        )

    render_nav_footer(
        "m4",
        prev_page=" Entry Timing",
        next_page=" Risk Analysis"
    )
