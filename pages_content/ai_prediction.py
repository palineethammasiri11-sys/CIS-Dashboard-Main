"""
pages_content/ai_prediction.py
------------------------------
หน้า AI Prediction ของ CIS Dashboard

ธีม: Light Clean
หมายเหตุ:
- ใช้ PageContext จาก common.py
- ไม่แก้ CSS ส่วนกลาง
- ไม่เปลี่ยน logic/data ของระบบ
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from common import (
    fmt_mb,
    fmt_ratio,
    safe,
    show_chart,
    render_nav_footer,
    COMPANY_NAMES,
    SECTOR_MAP,
)


# ============================================================================
# COLOR TOKENS — LIGHT THEME
# ============================================================================

GREEN = "#10B981"
AMBER = "#F59E0B"
RED = "#EF4444"
BLUE = "#38BDF8"
PURPLE = "#8B5CF6"

TEXT = "#0F172A"
TEXT_SECONDARY = "#334155"
TEXT_LIGHT = "#475569"
MUTED = "#64748B"

BG_PAGE = "#F8FAFC"
BG_CARD = "#FFFFFF"
BG_CARD_2 = "#F8FAFC"
BG_DARKER = "#F1F5F9"

BORDER = "#E2E8F0"
BORDER_DARK = "#CBD5E1"
GRID = "#E2E8F0"


# ============================================================================
# HELPERS
# ============================================================================

def _hex_to_rgba(hex_color, alpha=1.0):
    """
    แปลงสี HEX เช่น #10B981 เป็น rgba(...)
    ป้องกัน error จากการเรียก _hex_to_rgba ในส่วน gauge/chart
    """
    try:
        hex_color = str(hex_color).strip().lstrip("#")

        if len(hex_color) == 3:
            hex_color = "".join(c * 2 for c in hex_color)

        if len(hex_color) != 6:
            return f"rgba(100,116,139,{alpha})"

        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        return f"rgba({r},{g},{b},{alpha})"

    except Exception:
        return f"rgba(100,116,139,{alpha})"


def _section_title(title, subtitle=None, accent=PURPLE):
    """
    หัวข้อ section แบบ light card
    """
    subtitle_html = ""

    if subtitle:
        subtitle_html = f"""
        <div style="
            font-size:14px;
            color:{MUTED};
            margin-top:3px;
        ">
            {subtitle}
        </div>
        """

    st.markdown(
        f"""
        <div style="
            background:{BG_CARD};
            border:1px solid {BORDER};
            border-radius:12px 12px 0 0;
            padding:15px 18px;
            margin-top:18px;
            margin-bottom:0;
        ">
            <div style="
                display:flex;
                align-items:center;
                gap:9px;
            ">
                <div style="
                    width:4px;
                    height:22px;
                    border-radius:3px;
                    background:{accent};
                "></div>

                <div style="
                    font-size:17px;
                    font-weight:700;
                    color:{TEXT};
                    letter-spacing:0.2px;
                ">
                    {title}
                </div>
            </div>

            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _kpi_card(label, value, subtext="", value_color=TEXT, accent=None):
    """
    KPI card
    """
    accent_html = ""

    if accent:
        accent_html = f"""
        <div style="
            position:absolute;
            left:0;
            top:0;
            bottom:0;
            width:4px;
            background:{accent};
            border-radius:12px 0 0 12px;
        "></div>
        """

    st.markdown(
        f"""
        <div style="
            position:relative;
            background:{BG_CARD};
            border:1px solid {BORDER};
            border-radius:12px;
            padding:15px 16px;
            min-height:105px;
            overflow:hidden;
        ">
            {accent_html}

            <div style="
                font-size:13px;
                color:{MUTED};
                font-weight:600;
                margin-bottom:6px;
            ">
                {label}
            </div>

            <div style="
                font-size:24px;
                font-weight:700;
                color:{value_color};
                line-height:1.15;
            ">
                {value}
            </div>

            <div style="
                font-size:12px;
                color:{MUTED};
                margin-top:5px;
            ">
                {subtext}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _metric_cell(label, value, color=TEXT):
    return f"""
    <div style="
        background:{BG_CARD_2};
        border:1px solid {BORDER};
        border-radius:9px;
        padding:12px 14px;
    ">
        <div style="
            font-size:12px;
            color:{MUTED};
            margin-bottom:4px;
        ">
            {label}
        </div>

        <div style="
            font-size:17px;
            font-weight:700;
            color:{color};
        ">
            {value}
        </div>
    </div>
    """


def _safe_percent(value, decimals=1):
    try:
        return f"{float(value):.{decimals}f}%"
    except Exception:
        return "-"


def _get_first_existing_column(df, candidates):
    if df is None or df.empty:
        return None

    for col in candidates:
        if col in df.columns:
            return col

    return None


def _style_plot(fig, height=None):
    """
    ปรับ Plotly ให้เข้ากับ Light Theme
    """
    layout_kwargs = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            color=TEXT_SECONDARY,
            size=12,
        ),
        margin=dict(
            l=45,
            r=20,
            t=25,
            b=45,
        ),
        hoverlabel=dict(
            bgcolor=BG_CARD,
            bordercolor=BORDER,
            font=dict(color=TEXT),
        ),
    )

    if height is not None:
        layout_kwargs["height"] = height

    fig.update_layout(**layout_kwargs)

    fig.update_xaxes(
        showgrid=True,
        gridcolor=GRID,
        zeroline=False,
        linecolor=BORDER,
        tickfont=dict(color=MUTED),
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor=GRID,
        zeroline=False,
        linecolor=BORDER,
        tickfont=dict(color=MUTED),
    )

    return fig


# ============================================================================
# MAIN RENDER
# ============================================================================

def render(ctx):

    # ========================================================================
    # BASIC VALUES
    # ========================================================================

    prob_up = safe(
        ctx.stock_info.get("ai_probability_up"),
        safe(ctx.stock_info.get("prob_up"), 50),
    )

    down_prob = max(0.0, 100.0 - prob_up)

    ai_score = safe(
        ctx.stock_info.get("ai_score"),
        50,
    )

    acc_val = safe(
        ctx.stock_info.get("ai_accuracy"),
        safe(ctx.stock_info.get("accuracy"), 0),
    )

    baseline_val = safe(
        ctx.stock_info.get("ai_baseline"),
        safe(ctx.stock_info.get("baseline_accuracy"), 0),
    )

    signal = ctx.stock_info.get(
        "ai_signal",
        ctx.stock_info.get("signal", "-"),
    )

    # Direction
    direction_th = "ขาขึ้น" if prob_up >= 50 else "ขาลง"
    dir_prob = prob_up if prob_up >= 50 else down_prob

    # Status color
    if prob_up >= 70:
        status_color = GREEN
    elif prob_up >= 50:
        status_color = AMBER
    else:
        status_color = RED

    # Reliability
    reliability_low = acc_val < baseline_val
    baseline_note = "สูงกว่า" if not reliability_low else "ต่ำกว่า"

    # ========================================================================
    # PAGE HEADER
    # ========================================================================

    st.markdown(
        f"""
        <div style="
            margin-bottom:18px;
        ">
            <div style="
                font-size:23px;
                font-weight:700;
                color:{TEXT};
                letter-spacing:0.3px;
            ">
                AI PREDICTION
            </div>

            <div style="
                font-size:15px;
                color:{MUTED};
                margin-top:4px;
            ">
                ประเมินทิศทางราคาหุ้นในอีก 10 วันทำการด้วยโมเดล Random Forest
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


    # ========================================================================
    # 1. OVERVIEW
    # ========================================================================

    _section_title(
        "AI PREDICTION OVERVIEW",
        "สรุปผลการคาดการณ์จากโมเดล AI",
        PURPLE,
    )

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        _kpi_card(
            "CURRENT PRICE",
            f"{safe(ctx.current_price):.2f}",
            "THB",
            TEXT,
            PURPLE,
        )

    with col2:
        _kpi_card(
            "DIRECTION",
            direction_th,
            f"Probability {dir_prob:.1f}%",
            status_color,
            status_color,
        )

    with col3:
        _kpi_card(
            "UP PROBABILITY",
            f"{prob_up:.1f}%",
            "Probability of upward movement",
            status_color,
            status_color,
        )

    with col4:
        _kpi_card(
            "AI SCORE",
            f"{ai_score:.1f}",
            "Model-derived score",
            PURPLE,
            PURPLE,
        )

    with col5:
        _kpi_card(
            "SIGNAL",
            str(signal),
            "Model output",
            status_color,
            status_color,
        )


    # ========================================================================
    # 2. PREDICTION
    # ========================================================================

    _section_title(
        "PREDICTION",
        "ความน่าจะเป็นของทิศทางราคาในอีก 10 วันทำการ",
        BLUE,
    )

    st.markdown(
        f"""
        <div style="
            background:{BG_CARD};
            border:1px solid {BORDER};
            border-top:none;
            border-radius:0 0 12px 12px;
            padding:20px;
        ">

            <div style="
                display:flex;
                gap:16px;
                flex-wrap:wrap;
                align-items:stretch;
            ">

                <!-- GAUGE -->
                <div style="
                    flex:0 0 320px;
                    max-width:100%;
                    background:{BG_CARD_2};
                    border:1px solid {BORDER};
                    border-radius:12px;
                    padding:22px 14px;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    min-height:220px;
                ">

                    <div style="
                        width:240px;
                        max-width:100%;
                        text-align:center;
                    ">

                        <svg
                            viewBox="0 0 240 150"
                            style="
                                width:100%;
                                height:auto;
                                display:block;
                            "
                        >

                            <path
                                d="M 30 125 A 90 90 0 0 1 210 125"
                                fill="none"
                                stroke="{BORDER}"
                                stroke-width="18"
                                stroke-linecap="round"
                            />

                            <path
                                d="M 30 125 A 90 90 0 0 1 210 125"
                                fill="none"
                                stroke="{status_color}"
                                stroke-width="18"
                                stroke-linecap="round"
                                pathLength="100"
                                stroke-dasharray="{prob_up} 100"
                            />

                            <text
                                x="120"
                                y="100"
                                text-anchor="middle"
                                font-size="32"
                                font-weight="700"
                                fill="{TEXT}"
                            >
                                {prob_up:.1f}%
                            </text>

                            <text
                                x="120"
                                y="122"
                                text-anchor="middle"
                                font-size="12"
                                fill="{MUTED}"
                            >
                                UP PROBABILITY
                            </text>

                        </svg>

                    </div>
                </div>


                <!-- EXPLANATION -->
                <div style="
                    flex:1 1 420px;
                    background:{BG_CARD};
                    border:1px solid {BORDER};
                    border-radius:12px;
                    padding:18px;
                ">

                    <div style="
                        font-size:13px;
                        font-weight:700;
                        color:{MUTED};
                        letter-spacing:0.4px;
                        margin-bottom:8px;
                    ">
                        MODEL INTERPRETATION
                    </div>

                    <div style="
                        font-size:22px;
                        font-weight:700;
                        color:{status_color};
                        margin-bottom:8px;
                    ">
                        {direction_th}
                    </div>

                    <div style="
                        font-size:14px;
                        color:{TEXT_SECONDARY};
                        line-height:1.6;
                    ">
                        โมเดล Random Forest ประเมินโอกาสที่ราคาจะเคลื่อนไหวในทิศทาง
                        <b>{direction_th}</b>
                        ที่ระดับความน่าจะเป็น
                        <b style="color:{status_color};">
                            {dir_prob:.1f}%
                        </b>
                    </div>

                    <div style="
                        margin-top:16px;
                        display:grid;
                        grid-template-columns:1fr 1fr;
                        gap:10px;
                    ">
                        {_metric_cell("Upside Probability", f"{prob_up:.1f}%", GREEN)}
                        {_metric_cell("Downside Probability", f"{down_prob:.1f}%", RED)}
                    </div>

                </div>

            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


    # ========================================================================
    # 3. FORECAST
    # ========================================================================

    _section_title(
        "FORECAST — PRICE HISTORY + MODEL-IMPLIED RANGE",
        "เปรียบเทียบราคาจริงย้อนหลังกับช่วงราคาที่โมเดลประเมิน",
        GREEN,
    )

    # ------------------------------------------------------------------------
    # Prepare historical data
    # ------------------------------------------------------------------------

    daily = getattr(ctx, "stock_daily", pd.DataFrame())

    if daily is None:
        daily = pd.DataFrame()

    if not daily.empty:

        daily_plot = daily.copy()

        if "date" in daily_plot.columns:
            daily_plot["date"] = pd.to_datetime(
                daily_plot["date"],
                errors="coerce",
            )

        daily_plot = daily_plot.sort_values("date")

    else:
        daily_plot = pd.DataFrame()


    # ------------------------------------------------------------------------
    # Determine forecast-related values
    # ------------------------------------------------------------------------

    current_price = safe(ctx.current_price)

    predicted_price = safe(
        ctx.stock_info.get("ai_predicted_price"),
        safe(
            ctx.stock_info.get("predicted_price"),
            current_price,
        ),
    )

    prediction_low = safe(
        ctx.stock_info.get("ai_prediction_low"),
        safe(
            ctx.stock_info.get("prediction_low"),
            current_price * 0.95 if current_price else 0,
        ),
    )

    prediction_high = safe(
        ctx.stock_info.get("ai_prediction_high"),
        safe(
            ctx.stock_info.get("prediction_high"),
            current_price * 1.05 if current_price else 0,
        ),
    )


    # ------------------------------------------------------------------------
    # Price history chart
    # ------------------------------------------------------------------------

    fig_forecast = go.Figure()

    if (
        not daily_plot.empty
        and "date" in daily_plot.columns
        and "close" in daily_plot.columns
    ):

        history = daily_plot.tail(120)

        fig_forecast.add_trace(
            go.Scatter(
                x=history["date"],
                y=history["close"],
                mode="lines",
                name="Actual Price",
                line=dict(
                    color=BLUE,
                    width=2,
                ),
            )
        )

        # Model implied range around latest period
        if len(history) > 0:

            last_date = history["date"].iloc[-1]

            if pd.notna(last_date):

                try:
                    future_dates = pd.date_range(
                        start=last_date,
                        periods=11,
                        freq="B",
                    )

                    forecast_values = np.linspace(
                        current_price,
                        predicted_price,
                        11,
                    )

                    low_values = np.linspace(
                        current_price,
                        prediction_low,
                        11,
                    )

                    high_values = np.linspace(
                        current_price,
                        prediction_high,
                        11,
                    )

                    fig_forecast.add_trace(
                        go.Scatter(
                            x=future_dates,
                            y=high_values,
                            mode="lines",
                            line=dict(
                                color=_hex_to_rgba(GREEN, 0.0),
                                width=0,
                            ),
                            showlegend=False,
                            hoverinfo="skip",
                        )
                    )

                    fig_forecast.add_trace(
                        go.Scatter(
                            x=future_dates,
                            y=low_values,
                            mode="lines",
                            fill="tonexty",
                            fillcolor=_hex_to_rgba(GREEN, 0.10),
                            line=dict(
                                color=_hex_to_rgba(GREEN, 0.0),
                                width=0,
                            ),
                            name="Prediction Range",
                        )
                    )

                    fig_forecast.add_trace(
                        go.Scatter(
                            x=future_dates,
                            y=forecast_values,
                            mode="lines",
                            name="Model Forecast",
                            line=dict(
                                color=GREEN,
                                width=2.5,
                                dash="dash",
                            ),
                        )
                    )

                except Exception:
                    pass


    _style_plot(fig_forecast, 430)

    fig_forecast.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            font=dict(color=MUTED),
        ),
    )

    st.markdown(
        f"""
        <div style="
            background:{BG_CARD};
            border:1px solid {BORDER};
            border-top:none;
            border-radius:0 0 12px 12px;
            padding:16px;
        ">
        """,
        unsafe_allow_html=True,
    )

    if not fig_forecast.data:

        st.info("ไม่พบข้อมูลราคาสำหรับสร้างกราฟ Forecast")

    else:

        show_chart(
            fig_forecast,
            "ai_prediction_forecast",
            expand_height=650,
        )

    st.markdown("</div>", unsafe_allow_html=True)


    # Forecast metrics

    f1, f2, f3 = st.columns(3)

    with f1:
        _kpi_card(
            "CURRENT PRICE",
            f"{current_price:.2f}",
            "THB",
            TEXT,
            BLUE,
        )

    with f2:
        _kpi_card(
            "MODEL FORECAST",
            f"{predicted_price:.2f}",
            "THB",
            GREEN if predicted_price >= current_price else RED,
            GREEN if predicted_price >= current_price else RED,
        )

    with f3:

        range_text = (
            f"{prediction_low:.2f} – {prediction_high:.2f}"
        )

        _kpi_card(
            "PREDICTION RANGE",
            range_text,
            "THB",
            TEXT,
            AMBER,
        )


    # ========================================================================
    # 4. MODEL EXPLANATION
    # ========================================================================

    _section_title(
        "MODEL EXPLANATION",
        "ปัจจัยที่มีผลต่อการคาดการณ์ของโมเดล",
        PURPLE,
    )

    feat_df = getattr(
        ctx,
        "feat_imp_df",
        pd.DataFrame(),
    )

    if feat_df is None:
        feat_df = pd.DataFrame()

    if not feat_df.empty:

        feature_col = _get_first_existing_column(
            feat_df,
            [
                "feature",
                "feature_name",
                "name",
                "variable",
            ],
        )

        importance_col = _get_first_existing_column(
            feat_df,
            [
                "importance",
                "feature_importance",
                "importance_value",
                "value",
            ],
        )

        if feature_col and importance_col:

            feature_plot = feat_df.copy()

            feature_plot[importance_col] = pd.to_numeric(
                feature_plot[importance_col],
                errors="coerce",
            )

            feature_plot = feature_plot.dropna(
                subset=[importance_col]
            )

            feature_plot = feature_plot.sort_values(
                importance_col,
                ascending=True,
            ).tail(10)

            fig_feature = go.Figure()

            fig_feature.add_trace(
                go.Bar(
                    x=feature_plot[importance_col],
                    y=feature_plot[feature_col],
                    orientation="h",
                    marker=dict(
                        color=PURPLE,
                    ),
                    hovertemplate=(
                        "%{y}<br>"
                        "Importance: %{x:.3f}"
                        "<extra></extra>"
                    ),
                )
            )

            _style_plot(
                fig_feature,
                max(320, 45 * len(feature_plot)),
            )

            fig_feature.update_layout(
                xaxis_title="Importance",
                yaxis_title="",
            )

            c1, c2 = st.columns([1.35, 1])

            with c1:

                st.markdown(
                    f"""
                    <div style="
                        background:{BG_CARD};
                        border:1px solid {BORDER};
                        border-top:none;
                        border-radius:0 0 12px 12px;
                        padding:16px;
                    ">
                    """,
                    unsafe_allow_html=True,
                )

                show_chart(
                    fig_feature,
                    "ai_feature_importance",
                    expand_height=650,
                )

                st.markdown(
                    "</div>",
                    unsafe_allow_html=True,
                )

            with c2:

                st.markdown(
                    f"""
                    <div style="
                        background:{BG_CARD};
                        border:1px solid {BORDER};
                        border-top:none;
                        border-radius:0 0 12px 12px;
                        padding:18px;
                        min-height:300px;
                    ">

                        <div style="
                            font-size:15px;
                            font-weight:700;
                            color:{TEXT};
                            margin-bottom:12px;
                        ">
                            EXPLAINABLE AI SUMMARY
                        </div>

                        <div style="
                            font-size:14px;
                            color:{TEXT_SECONDARY};
                            line-height:1.65;
                        ">
                            โมเดล Random Forest ใช้หลายปัจจัยร่วมกัน
                            เพื่อประเมินทิศทางราคาหุ้นในอนาคต
                            โดย Feature Importance แสดงน้ำหนักสัมพัทธ์
                            ของแต่ละตัวแปรที่ใช้ในการสร้างผลการพยากรณ์
                        </div>

                        <div style="
                            margin-top:18px;
                            background:{BG_CARD_2};
                            border:1px solid {BORDER};
                            border-radius:9px;
                            padding:12px;
                        ">
                            <div style="
                                font-size:12px;
                                color:{MUTED};
                                margin-bottom:4px;
                            ">
                                MODEL
                            </div>

                            <div style="
                                font-size:16px;
                                font-weight:700;
                                color:{PURPLE};
                            ">
                                Random Forest
                            </div>
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        else:

            st.markdown(
                f"""
                <div style="
                    background:{BG_CARD};
                    border:1px solid {BORDER};
                    border-top:none;
                    border-radius:0 0 12px 12px;
                    padding:20px;
                    color:{MUTED};
                ">
                    ไม่พบข้อมูล Feature Importance ที่สามารถแสดงผลได้
                </div>
                """,
                unsafe_allow_html=True,
            )

    else:

        st.markdown(
            f"""
            <div style="
                background:{BG_CARD};
                border:1px solid {BORDER};
                border-top:none;
                border-radius:0 0 12px 12px;
                padding:20px;
                color:{MUTED};
            ">
                ไม่พบข้อมูล Feature Importance
            </div>
            """,
            unsafe_allow_html=True,
        )


    # ========================================================================
    # 5. MODEL PERFORMANCE
    # ========================================================================

    _section_title(
        "MODEL PERFORMANCE",
        "ประสิทธิภาพของโมเดลและผลการทดสอบย้อนหลัง",
        AMBER,
    )

    p1, p2, p3, p4 = st.columns(4)

    accuracy_display = (
        f"{acc_val:.1f}%"
        if acc_val > 0
        else "-"
    )

    baseline_display = (
        f"{baseline_val:.1f}%"
        if baseline_val > 0
        else "-"
    )

    difference_val = acc_val - baseline_val

    difference_display = (
        f"{difference_val:+.1f}%"
        if acc_val > 0 and baseline_val > 0
        else "-"
    )

    with p1:
        _kpi_card(
            "MODEL ACCURACY",
            accuracy_display,
            "Historical backtest",
            GREEN if not reliability_low else AMBER,
            GREEN if not reliability_low else AMBER,
        )

    with p2:
        _kpi_card(
            "BASELINE",
            baseline_display,
            "Reference accuracy",
            TEXT,
            BLUE,
        )

    with p3:
        _kpi_card(
            "VS BASELINE",
            difference_display,
            baseline_note + " baseline",
            GREEN if difference_val >= 0 else RED,
            GREEN if difference_val >= 0 else RED,
        )

    with p4:
        _kpi_card(
            "MODEL",
            "Random Forest",
            "Prediction algorithm",
            PURPLE,
            PURPLE,
        )


    # ------------------------------------------------------------------------
    # Backtest chart
    # ------------------------------------------------------------------------

    backtest_df = getattr(
        ctx,
        "backtest_df",
        pd.DataFrame(),
    )

    if backtest_df is None:
        backtest_df = pd.DataFrame()

    if not backtest_df.empty:

        backtest_plot = backtest_df.copy()

        date_col = _get_first_existing_column(
            backtest_plot,
            [
                "date",
                "timestamp",
                "period",
            ],
        )

        actual_col = _get_first_existing_column(
            backtest_plot,
            [
                "actual",
                "actual_price",
                "actual_value",
                "close",
            ],
        )

        predicted_col = _get_first_existing_column(
            backtest_plot,
            [
                "predicted",
                "predicted_price",
                "prediction",
                "forecast",
            ],
        )

        if date_col and (
            actual_col or predicted_col
        ):

            backtest_plot[date_col] = pd.to_datetime(
                backtest_plot[date_col],
                errors="coerce",
            )

            fig_backtest = go.Figure()

            if actual_col:

                fig_backtest.add_trace(
                    go.Scatter(
                        x=backtest_plot[date_col],
                        y=pd.to_numeric(
                            backtest_plot[actual_col],
                            errors="coerce",
                        ),
                        mode="lines",
                        name="Actual",
                        line=dict(
                            color=BLUE,
                            width=2,
                        ),
                    )
                )

            if predicted_col:

                fig_backtest.add_trace(
                    go.Scatter(
                        x=backtest_plot[date_col],
                        y=pd.to_numeric(
                            backtest_plot[predicted_col],
                            errors="coerce",
                        ),
                        mode="lines",
                        name="Predicted",
                        line=dict(
                            color=PURPLE,
                            width=2,
                            dash="dash",
                        ),
                    )
                )

            _style_plot(
                fig_backtest,
                400,
            )

            fig_backtest.update_layout(
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="left",
                    x=0,
                ),
            )

            st.markdown(
                f"""
                <div style="
                    background:{BG_CARD};
                    border:1px solid {BORDER};
                    border-top:none;
                    border-radius:0 0 12px 12px;
                    padding:16px;
                ">
                """,
                unsafe_allow_html=True,
            )

            show_chart(
                fig_backtest,
                "ai_backtest_history",
                expand_height=620,
            )

            st.markdown(
                "</div>",
                unsafe_allow_html=True,
            )

        else:

            st.markdown(
                f"""
                <div style="
                    background:{BG_CARD};
                    border:1px solid {BORDER};
                    border-top:none;
                    border-radius:0 0 12px 12px;
                    padding:20px;
                    color:{MUTED};
                ">
                    ไม่พบ column ที่เหมาะสมสำหรับแสดง Backtest History
                </div>
                """,
                unsafe_allow_html=True,
            )

    else:

        st.markdown(
            f"""
            <div style="
                background:{BG_CARD};
                border:1px solid {BORDER};
                border-top:none;
                border-radius:0 0 12px 12px;
                padding:20px;
                color:{MUTED};
            ">
                ไม่พบข้อมูล Historical Backtest
            </div>
            """,
            unsafe_allow_html=True,
        )


    # ========================================================================
    # MODEL & DATA DETAIL
    # ========================================================================

    with st.expander("Model & Data Detail"):

        st.markdown(
            f"""
            <div style="
                background:{BG_CARD};
                border:1px solid {BORDER};
                border-radius:10px;
                padding:16px;
            ">

                <div style="
                    display:grid;
                    grid-template-columns:repeat(3, 1fr);
                    gap:10px;
                ">

                    {_metric_cell(
                        "Model",
                        "Random Forest",
                        PURPLE
                    )}

                    {_metric_cell(
                        "Forecast Horizon",
                        "10 Trading Days",
                        BLUE
                    )}

                    {_metric_cell(
                        "Direction",
                        direction_th,
                        status_color
                    )}

                    {_metric_cell(
                        "Up Probability",
                        f"{prob_up:.1f}%",
                        GREEN
                    )}

                    {_metric_cell(
                        "Down Probability",
                        f"{down_prob:.1f}%",
                        RED
                    )}

                    {_metric_cell(
                        "AI Score",
                        f"{ai_score:.1f}/100",
                        PURPLE
                    )}

                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


    # ========================================================================
    # FOOTER
    # ========================================================================

    render_nav_footer(
        "m4",
        prev_page=" Entry Timing",
        next_page=" Risk Analysis",
    )
