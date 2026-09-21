"""
pages_content/entry_timing.py
--------------------------------------------------------------------
Institutional Grade UI - Bloomberg / TradingView Inspired
IKB v3.1 (Single-source-of-truth signal classification)

Changelog vs v3.0:
- FIX: reads 'trend_available_count' / 'mom_available_count'
- FIX: status_label / status_color / action_th / readiness come
  from calculate_modules.entry_timing.classify_signal(total_score)
- FIX: Risk/Reward is now a 7th item in the SIGNAL CHECKLIST
- FIX: "TOTAL SCORE" row renamed to "CHECKS PASSED"
- Cleanup: dropped redundant unsafe_allow_html=True kwargs on
  calls to _render_html
"""

import html
import re
import textwrap

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from common import safe, render_nav_footer
from calculate_modules.entry_timing import classify_signal


# --------------------------------------------------------------------
# Design tokens - LIGHT THEME
# --------------------------------------------------------------------
BG_PAGE = "#F8FAFC"
BG_CARD = "#FFFFFF"
BG_CARD_2 = "#F8FAFC"
BG_CHIP = "#F1F5F9"

BORDER = "#E2E8F0"
BORDER_SOFT = "#E2E8F0"

TEXT_MUTED = "#64748B"
TEXT = "#334155"
TEXT_WHITE = "#0F172A"

ACCENT = "#38BDF8"
GREEN = "#10B981"
RED = "#EF4444"
AMBER = "#F59E0B"


def _badge(ok, available):
    if not available:
        return "N/A", TEXT_MUTED, "100,116,139"
    if ok:
        return "PASS", GREEN, "16,185,129"
    return "FAIL", RED, "239,68,68"


def _card_style(extra=""):
    return (
        f"background:{BG_CARD};"
        f"border:1px solid {BORDER};"
        "border-radius:10px;"
        "padding:16px;"
        f"{extra}"
    )


def _render_html(markup):
    clean = textwrap.dedent(markup)
    clean = re.sub(r"\s*\n\s*", " ", clean).strip()
    st.markdown(clean, unsafe_allow_html=True)


def _metric_card(
    label,
    value,
    sub="",
    value_color=TEXT_WHITE,
    is_summary=False,
    card_bg=BG_CARD,
):
    content_style = (
        f"font-size:11px;font-weight:700;color:{value_color};margin-top:4px;"
        "overflow:hidden;text-overflow:ellipsis;display:-webkit-box;"
        "-webkit-line-clamp:2;-webkit-box-orient:vertical;line-height:1.35;"
        if is_summary
        else
        f"font-size:17px;font-weight:900;color:{value_color};margin-top:4px;"
        "white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"
    )

    return f"""
    <div style="{_card_style(
        f'height:100%;box-sizing:border-box;background:{card_bg};'
    )}">
        <div style="font-size:10px;font-weight:800;color:{'#FFFFFF' if card_bg != BG_CARD else TEXT_MUTED};letter-spacing:.5px;">
            {label}
        </div>
        <div style="{content_style}">
            {value}
        </div>
        <div style="font-size:10px;color:{'#FFFFFF' if card_bg != BG_CARD else TEXT_MUTED};margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
            {sub}
        </div>
    </div>
    """


def render(ctx):
    info = ctx.stock_info
    c_p = float(ctx.current_price)
    ticker_safe = html.escape(str(ctx.selected_ticker))

    st.markdown("""
    <div style="margin-bottom:20px;">
        <div style="font-size:23px; font-weight:700; color:#0F172A; letter-spacing:0.3px;">
            ENTRY TIMING
        </div>
        <div style="font-size:15px; color:#64748B; margin-top:4px;">
            วิเคราะห์จังหวะการเข้าลงทุนจากแนวโน้ม โมเมนตัม และ Risk/Reward
        </div>
    </div>
    """, unsafe_allow_html=True)

    adx_val = float(safe(info.get("adx"), 0.0))

    r1 = float(safe(info.get("resistance_60d"), c_p * 1.05))
    r2 = float(safe(info.get("resistance_2"), r1 * 1.05))
    s1 = float(safe(info.get("support_60d"), c_p * 0.95))
    s2 = float(safe(info.get("support_2"), s1 * 0.95))
    pp = float(safe(info.get("pivot_point"), round((r1 + s1 + c_p) / 3, 2)))

    total_score = float(safe(info.get("timing_score"), 50.0))

    # Single source of truth
    sig = classify_signal(total_score)

    status_label = sig["status_label"]
    status_color = sig["status_color"]
    action_th = sig["action_th"]
    readiness = sig["readiness"]

    # ---------------------------------------------------------------
    # STATUS COLOR
    # ไม่แก้ข้อความจาก classify_signal
    # เปลี่ยนเฉพาะสีตามสถานะ
    # ---------------------------------------------------------------
    if status_label in ("WAIT", "NEUTRAL", "NATURAL"):
        status_color = AMBER
    elif status_label == "READY":
        status_color = GREEN
    elif status_label == "BEARISH":
        status_color = RED

    price_chg_pct = float(safe(info.get("price_change_pct"), 0.0))
    pe_ratio = safe(info.get("pe_ratio"), None)
    roe_pct = safe(info.get("roe_pct"), None)
    data_as_of = str(safe(info.get("data_as_of"), "-"))
    sector_label = str(safe(info.get("sector_label"), ""))

    k15_ok = bool(info.get("k15_ok", False))
    k16_ok = bool(info.get("k16_ok", False))
    k17_ok = bool(info.get("k17_ok", False))
    k18_ok = bool(info.get("k18_ok", False))
    k19_ok = bool(info.get("k19_ok", False))
    k20_ok = bool(info.get("k20_ok", False))
    k_rr_ok = bool(info.get("k_rr_ok", False))

    k15_av = bool(info.get("k15_available", False))
    k16_av = bool(info.get("k16_available", False))
    k17_av = bool(info.get("k17_available", False))
    k18_av = bool(info.get("k18_available", False))
    k19_av = bool(info.get("k19_available", False))
    k20_av = bool(info.get("k20_available", False))

    trend_avail_count = int(
        safe(info.get("trend_available_count"), 0)
    )
    mom_avail_count = int(
        safe(info.get("mom_available_count"), 0)
    )

    rr_ratio = float(safe(info.get("rr_ratio"), 0.0))
    rr_score = float(safe(info.get("rr_score"), 0.0))
    downside_pct = float(safe(info.get("downside_pct"), 0.0))
    upside_pct = float(safe(info.get("upside_pct"), 0.0))

    vol_series = next(
        (
            ctx.stock_daily[v]
            for v in ["volume", "Volume", "vol", "Vol"]
            if v in ctx.stock_daily.columns
        ),
        None,
    )

    def pillar_pts_label(ok, available, n_available, pillar_max):
        if not available:
            return "N/A"

        share = pillar_max / n_available if n_available > 0 else 0

        return f"+{share:.1f} pts" if ok else "0.0 pts"

    # 7 items total:
    # 3 Trend + 3 Momentum + 1 Risk/Reward
    checklist = [
        (
            k15_ok,
            k15_av,
            "Short-Term Trend",
            "ราคายืนเหนือเส้น EMA20"
            if k15_ok
            else "ราคาต่ำกว่าเส้น EMA20",
            pillar_pts_label(
                k15_ok,
                k15_av,
                trend_avail_count,
                40.0,
            ),
        ),
        (
            k16_ok,
            k16_av,
            "Medium-Term Trend",
            "EMA20 อยู่เหนือ EMA50"
            if k16_ok
            else "EMA20 ยังไม่ตัดขึ้นเหนือ EMA50",
            pillar_pts_label(
                k16_ok,
                k16_av,
                trend_avail_count,
                40.0,
            ),
        ),
        (
            k17_ok,
            k17_av,
            "Long-Term Trend",
            "ราคายืนเหนือเส้น MA200"
            if k17_ok
            else "ราคายังอยู่ต่ำกว่า MA200",
            pillar_pts_label(
                k17_ok,
                k17_av,
                trend_avail_count,
                40.0,
            ),
        ),
        (
            k18_ok,
            k18_av,
            "Momentum (MACD)",
            "MACD อยู่ในโซนบวก"
            if k18_ok
            else "MACD อยู่ในโซนลบ",
            pillar_pts_label(
                k18_ok,
                k18_av,
                mom_avail_count,
                30.0,
            ),
        ),
        (
            k19_ok,
            k19_av,
            "Trend Strength (ADX)",
            f"ADX {adx_val:.1f} (มีแรงเหวี่ยงดี)"
            if k19_ok
            else f"ADX {adx_val:.1f} (ต่ำกว่าเกณฑ์)",
            pillar_pts_label(
                k19_ok,
                k19_av,
                mom_avail_count,
                30.0,
            ),
        ),
        (
            k20_ok,
            k20_av,
            "Volume Confirmation",
            "วอลุ่มล่าสุดสูงกว่าค่าเฉลี่ย"
            if k20_ok
            else "วอลุ่มเบาบางกว่าค่าเฉลี่ย",
            pillar_pts_label(
                k20_ok,
                k20_av,
                mom_avail_count,
                30.0,
            ),
        ),
        (
            k_rr_ok,
            True,
            "Risk / Reward",
            f"RR {rr_ratio:.2f} : 1 ผ่านเกณฑ์ขั้นต่ำ"
            if k_rr_ok
            else f"RR {rr_ratio:.2f} : 1 ต่ำกว่าเกณฑ์ขั้นต่ำ",
            f"+{rr_score:.1f} pts"
            if k_rr_ok
            else "0.0 pts",
        ),
    ]

    bullish_count = sum(
        1
        for ok, av, *_ in checklist
        if ok and av
    )

    total_checks = len(checklist)

    failed_items = [
        name
        for ok, av, name, _, _ in checklist
        if not ok and av
    ]

    if bullish_count >= 6:
        summary_text = (
            f"สัญญาณพร้อมสูง ({bullish_count}/{total_checks}) "
            f"โครงสร้างราคาและโมเมนตัมสนับสนุนการเข้าสะสม"
        )

    elif len(failed_items) <= 2:
        missing_str = ", ".join(failed_items)

        summary_text = (
            f"ผ่าน {bullish_count}/{total_checks} เกณฑ์ --- "
            f"<b>รอการยืนยันจาก: {missing_str}</b>"
        )

    else:
        summary_text = (
            f"ผ่าน {bullish_count}/{total_checks} เกณฑ์ --- "
            f"<b>สัญญาณยังไม่ครบถ้วน ควรงดเข้าซื้อ</b>"
        )

    chg_color = GREEN if price_chg_pct >= 0 else RED
    chg_arrow = "▲" if price_chg_pct >= 0 else "▼"

    pe_html = (
        f'<div><span style="color:{TEXT_MUTED};">P/E:</span> '
        f'<b style="color:{TEXT_WHITE};">{pe_ratio}x</b></div>'
        if pe_ratio not in (None, "")
        else ""
    )

    roe_html = (
        f'<div><span style="color:{TEXT_MUTED};">ROE:</span> '
        f'<b style="color:{TEXT_WHITE};">{roe_pct}%</b></div>'
        if roe_pct not in (None, "")
        else ""
    )

    readiness_color = (
        GREEN
        if readiness == "READY"
        else AMBER
    )

    # ---------------------------------------------------------------
    # CONFIDENCE DOTS
    # ---------------------------------------------------------------
    confidence_dots = "".join([
        f'<span style="height:7px;width:7px;'
        f'background-color:{"#10B981" if i < bullish_count else "#CBD5E1"};'
        f'border-radius:50%;display:inline-block;margin-right:3px;"></span>'
        for i in range(total_checks)
    ])

    # ---------------------------------------------------------------
    # KPI TOP ROW
    # ---------------------------------------------------------------
    kpi_html = f"""
    <div style="
        display:grid;
        grid-template-columns:1fr 1fr 1fr 1.6fr;
        gap:10px;
        margin-bottom:12px;
    ">

        {_metric_card(
            "ENTRY READINESS",
            readiness,
            "รอการยืนยันสัญญาณเพิ่มเติม",
            "#FFFFFF",
            card_bg=readiness_color
        )}

        {_metric_card(
            "MARKET TREND",
            status_label,
            action_th,
            status_color
        )}

        <div style="{_card_style('height:100%;box-sizing:border-box;')}">

            <div style="
                font-size:10px;
                font-weight:800;
                color:{TEXT_MUTED};
                letter-spacing:.5px;
            ">
                CONFIDENCE
            </div>

            <div style="
                font-size:17px;
                font-weight:900;
                color:{TEXT_WHITE};
                margin-top:4px;
            ">
                {bullish_count} / {total_checks}
            </div>

            <div style="margin-top:4px;">
                {confidence_dots}
            </div>

        </div>

        {_metric_card(
            "ℹ️ สรุปสั้น ๆ",
            summary_text,
            "ภาพรวมสถานะการลงทุนเชิงปริมาณ",
            TEXT,
            is_summary=True
        )}

    </div>
    """

    _render_html(kpi_html)

    # ---------------------------------------------------------------
    # MAIN THREE COLUMNS
    # ---------------------------------------------------------------
    left, center, right = st.columns(
        [1.0, 2.3, 1.15],
        gap="medium",
    )

    # ==============================================================
    # LEFT COLUMN
    # ==============================================================

    with left:

        total_arc = 125.66

        score_fill = round(
            total_arc
            * min(
                1.0,
                max(
                    0.0,
                    total_score / 100.0
                )
            ),
            2,
        )

        _render_html(
            f"""
            <div style="
                background:{BG_CARD};
                border:2px solid {status_color};
                border-radius:10px;
                padding:16px;
                margin-bottom:12px;
                box-sizing:border-box;
            ">

                <div style="
                    border-bottom:2px solid {status_color};
                    padding-bottom:5px;
                    font-size:12px;
                    font-weight:800;
                    color:{TEXT_WHITE};
                ">
                    ⏱️ ENTRY TIMING ANALYSIS
                </div>

                <div style="
                    text-align:center;
                    margin-top:8px;
                ">

                    <svg
                        viewBox="0 0 100 55"
                        style="
                            width:120px;
                            height:66px;
                            display:block;
                            margin:0 auto;
                        "
                    >

                        <path
                            d="M 10 48 A 38 38 0 0 1 90 48"
                            fill="none"
                            stroke="{BORDER_SOFT}"
                            stroke-width="7"
                            stroke-linecap="round"
                        />

                        <path
                            d="M 10 48 A 38 38 0 0 1 90 48"
                            fill="none"
                            stroke="{status_color}"
                            stroke-width="7"
                            stroke-linecap="round"
                            stroke-dasharray="{score_fill} {total_arc}"
                        />

                        <text
                            x="50"
                            y="33"
                            text-anchor="middle"
                            font-size="18"
                            font-weight="900"
                            fill="{TEXT_WHITE}"
                        >
                            {total_score:.0f}
                        </text>

                        <text
                            x="50"
                            y="43"
                            text-anchor="middle"
                            font-size="7"
                            font-weight="700"
                            fill="{TEXT_MUTED}"
                        >
                            / 100
                        </text>

                    </svg>

                    <div style="
                        font-size:14px;
                        font-weight:900;
                        color:{status_color};
                        margin-top:2px;
                    ">
                        {status_label}
                    </div>

                    <div style="
                        font-size:9.5px;
                        color:{TEXT_MUTED};
                    ">
                        {action_th}
                    </div>

                </div>

                <div style="
                    border-top:1px solid {BORDER_SOFT};
                    margin-top:8px;
                    padding-top:5px;
                    display:flex;
                    justify-content:space-between;
                    font-size:10px;
                    font-weight:800;
                ">
                    <span style="color:{TEXT_WHITE};">
                        CONFLUENCE
                    </span>

                    <span style="color:{status_color};">
                        {bullish_count} / {total_checks} ผ่าน
                    </span>
                </div>

            </div>
            """
        )

        checklist_items = []

        for ok, av, label, sub, points in checklist:

            badge_label, badge_color, badge_bg = _badge(
                ok,
                av
            )

            icon = (
                "✓"
                if ok and av
                else ("✕" if av else "--")
            )

            checklist_items.append(
                f"""
                <div style="
                    display:flex;
                    justify-content:space-between;
                    align-items:center;
                    padding:5px 0;
                    border-bottom:1px solid {BORDER_SOFT};
                ">

                    <div style="
                        display:flex;
                        align-items:center;
                        gap:6px;
                        min-width:0;
                    ">

                        <div style="
                            background:rgba({badge_bg},.15);
                            color:{badge_color};
                            width:16px;
                            height:16px;
                            border-radius:50%;
                            display:flex;
                            align-items:center;
                            justify-content:center;
                            font-size:9.5px;
                            font-weight:bold;
                            flex-shrink:0;
                        ">
                            {icon}
                        </div>

                        <div style="min-width:0;">

                            <div style="
                                font-size:10px;
                                color:{TEXT_WHITE};
                                font-weight:700;
                            ">
                                {label}
                            </div>

                            <div style="
                                font-size:8.5px;
                                color:{TEXT_MUTED};
                            ">
                                {sub}
                            </div>

                        </div>

                    </div>

                    <span style="
                        background:rgba({badge_bg},.15);
                        color:{badge_color};
                        font-size:9px;
                        font-weight:800;
                        padding:2px 5px;
                        border-radius:4px;
                        white-space:nowrap;
                        margin-left:5px;
                    ">
                        {badge_label}
                    </span>

                </div>
                """
            )

        _render_html(
            f"""
            <div style="{_card_style()}">

                <div style="
                    font-size:11.5px;
                    font-weight:800;
                    color:{TEXT_WHITE};
                    margin-bottom:6px;
                    border-bottom:2px solid {ACCENT};
                    padding-bottom:4px;
                    display:flex;
                    justify-content:space-between;
                ">

                    <span>
                        🛡️ SIGNAL CHECKLIST
                    </span>

                    <span style="color:{status_color};">
                        {bullish_count} / {total_checks} ผ่าน
                    </span>

                </div>

                {''.join(checklist_items)}

                <div style="
                    margin-top:8px;
                    font-size:11.5px;
                    font-weight:900;
                    color:{status_color};
                    display:flex;
                    justify-content:space-between;
                ">

                    <span>
                        CHECKS PASSED
                    </span>

                    <span>
                        {bullish_count} / {total_checks}
                    </span>

                </div>

            </div>
            """
        )

    # ==============================================================
    # CENTER COLUMN
    # ==============================================================

    with center:

        c_head1, c_head2 = st.columns(
            [1, 1.5]
        )

        with c_head1:

            _render_html(
                f"""
                <div style="
                    font-size:12px;
                    font-weight:800;
                    color:{TEXT_WHITE};
                    padding-top:4px;
                ">
                    PRICE ACTION &amp; VOLUME
                </div>
                """
            )

        with c_head2:

            tf_selected = st.radio(
                "TF",
                [
                    "1M",
                    "3M",
                    "6M",
                    "1Y",
                    "2Y",
                    "ALL",
                ],
                index=2,
                horizontal=True,
                label_visibility="collapsed",
                key="timing_tf_sel",
            )

        tf_bars = {
            "1M": 22,
            "3M": 66,
            "6M": 132,
            "1Y": 252,
            "2Y": 504,
            "ALL": len(ctx.stock_daily),
        }

        n_bars = min(
            tf_bars.get(
                tf_selected,
                132
            ),
            len(ctx.stock_daily),
        )

        chart_df = (
            ctx.stock_daily
            .tail(n_bars)
            .copy()
        )

        aliases = {
            "Close": "close",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Date": "date",
        }

        for source, target in aliases.items():

            if (
                source in chart_df.columns
                and target not in chart_df.columns
            ):
                chart_df[target] = chart_df[source]

        required = {
            "close",
            "open",
            "high",
            "low",
            "date",
        }

        if not required.issubset(
            chart_df.columns
        ):

            st.error(
                "ไม่พบข้อมูล OHLC/Date ที่จำเป็นสำหรับกราฟ"
            )

        else:

            fig_main = make_subplots(
                rows=2,
                cols=1,
                shared_xaxes=True,
                vertical_spacing=0.03,
                row_heights=[
                    0.78,
                    0.22,
                ],
            )

            fig_main.add_trace(
                go.Candlestick(
                    x=chart_df["date"],
                    open=chart_df["open"],
                    high=chart_df["high"],
                    low=chart_df["low"],
                    close=chart_df["close"],
                    name="Price",
                    increasing_line_color=GREEN,
                    decreasing_line_color=RED,
                    line=dict(width=1),
                ),
                row=1,
                col=1,
            )

            if "EMA20" in chart_df.columns:

                fig_main.add_trace(
                    go.Scatter(
                        x=chart_df["date"],
                        y=chart_df["EMA20"],
                        line=dict(
                            color=AMBER,
                            width=1.2
                        ),
                        name="EMA 20",
                    ),
                    row=1,
                    col=1,
                )

            if "EMA50" in chart_df.columns:

                fig_main.add_trace(
                    go.Scatter(
                        x=chart_df["date"],
                        y=chart_df["EMA50"],
                        line=dict(
                            color=ACCENT,
                            width=1.2
                        ),
                        name="EMA 50",
                    ),
                    row=1,
                    col=1,
                )

            if "MA200" in chart_df.columns:

                fig_main.add_trace(
                    go.Scatter(
                        x=chart_df["date"],
                        y=chart_df["MA200"],
                        line=dict(
                            color="#A78BFA",
                            width=1.2
                        ),
                        name="MA 200",
                    ),
                    row=1,
                    col=1,
                )

            bar_colors = [
                GREEN if c >= o else RED
                for c, o in zip(
                    chart_df["close"],
                    chart_df["open"],
                )
            ]

            vol_data = (
                vol_series.tail(n_bars)
                if vol_series is not None
                else pd.Series(
                    np.zeros(
                        len(chart_df)
                    ),
                    index=chart_df.index,
                )
            )

            fig_main.add_trace(
                go.Bar(
                    x=chart_df["date"],
                    y=vol_data,
                    marker_color=bar_colors,
                    showlegend=False,
                ),
                row=2,
                col=1,
            )

            lines_to_plot = [
                (
                    r2,
                    "dot",
                    "#F87171",
                    1.0
                ),
                (
                    r1,
                    "dash",
                    RED,
                    1.2
                ),
                (
                    pp,
                    "dash",
                    "#94A3B8",
                    1.2
                ),
                (
                    s1,
                    "dash",
                    GREEN,
                    1.2
                ),
                (
                    s2,
                    "dash",
                    RED,
                    1.2
                ),
            ]

            for (
                val,
                dash_type,
                col_hex,
                w,
            ) in lines_to_plot:

                fig_main.add_hline(
                    y=val,
                    line_dash=dash_type,
                    line_color=col_hex,
                    line_width=w,
                )

            # -------------------------------------------------------
            # LIGHT THEME PLOTLY
            # -------------------------------------------------------

            fig_main.update_layout(
                height=525,

                margin=dict(
                    l=8,
                    r=40,
                    t=25,
                    b=5,
                ),

                paper_bgcolor=BG_CARD,
                plot_bgcolor=BG_CARD,

                xaxis=dict(
                    gridcolor=BORDER_SOFT,
                    showticklabels=False,
                    linecolor=BORDER,
                ),

                xaxis2=dict(
                    gridcolor=BORDER_SOFT,
                    tickfont=dict(
                        size=10,
                        color=TEXT_MUTED,
                    ),
                    linecolor=BORDER,
                ),

                yaxis=dict(
                    gridcolor=BORDER_SOFT,
                    side="right",
                    tickfont=dict(
                        size=10,
                        color=TEXT_MUTED,
                    ),
                    linecolor=BORDER,
                ),

                yaxis2=dict(
                    showticklabels=False,
                    gridcolor=BORDER_SOFT,
                ),

                legend=dict(
                    orientation="h",
                    y=1.12,
                    x=0.01,
                    font=dict(
                        size=10,
                        color=TEXT_WHITE,
                    ),
                    bgcolor="rgba(255,255,255,0)",
                ),

                xaxis_rangeslider_visible=False,

                hovermode="x unified",
            )

            st.plotly_chart(
                fig_main,
                use_container_width=True,
                config={
                    "displayModeBar": True,
                    "displaylogo": False,
                },
            )

    # ==============================================================
    # RIGHT COLUMN
    # ==============================================================

    with right:

        _render_html(
            f"""
            <div style="{_card_style('margin-bottom:12px;')}">

                <div style="
                    border-bottom:2px solid {ACCENT};
                    padding-bottom:5px;
                    display:flex;
                    justify-content:space-between;
                    align-items:center;
                    flex-wrap:wrap;
                    row-gap:4px;
                ">

                    <span style="
                        font-size:12px;
                        font-weight:800;
                        color:{TEXT_WHITE};
                    ">
                        PRICE SETUP
                    </span>

                    <span style="
                        background:rgba(56,189,248,.15);
                        color:{ACCENT};
                        font-size:9.5px;
                        font-weight:800;
                        padding:2px 6px;
                        border-radius:4px;
                    ">
                        Current {c_p:.2f}
                    </span>

                </div>

                <div style="margin-top:8px;">

                    <div style="
                        display:flex;
                        justify-content:space-between;
                        padding:5px 0;
                        border-bottom:1px solid {BORDER_SOFT};
                        font-size:11px;
                    ">

                        <span style="color:{TEXT_MUTED};">
                            Current Price
                        </span>

                        <b style="color:{TEXT_WHITE};">
                            {c_p:.2f} THB
                        </b>

                    </div>

                    <div style="
                        display:flex;
                        justify-content:space-between;
                        padding:5px 0;
                        border-bottom:1px solid {BORDER_SOFT};
                        font-size:11px;
                    ">

                        <span style="color:{GREEN};">
                            Preferred Entry
                        </span>

                        <b style="color:{GREEN};">
                            {s1:.2f} -- {pp:.2f}
                        </b>

                    </div>

                    <div style="
                        display:flex;
                        justify-content:space-between;
                        padding:5px 0;
                        border-bottom:1px solid {BORDER_SOFT};
                        font-size:11px;
                    ">

                        <span style="color:{AMBER};">
                            Watch Zone
                        </span>

                        <b style="color:{AMBER};">
                            {pp:.2f} -- {r1:.2f}
                        </b>

                    </div>

                    <div style="
                        display:flex;
                        justify-content:space-between;
                        padding:5px 0;
                        border-bottom:1px solid {BORDER_SOFT};
                        font-size:11px;
                    ">

                        <span style="color:{RED};">
                            Stop Loss
                        </span>

                        <b style="color:{RED};">
                            &lt; {s2:.2f}
                        </b>

                    </div>

                    <div style="
                        display:flex;
                        justify-content:space-between;
                        padding:5px 0;
                        border-bottom:1px solid {BORDER_SOFT};
                        font-size:11px;
                    ">

                        <span style="color:{TEXT_WHITE};">
                            Target 1
                        </span>

                        <b style="color:{TEXT_WHITE};">
                            {r1:.2f}
                        </b>

                    </div>

                    <div style="
                        display:flex;
                        justify-content:space-between;
                        padding:5px 0;
                        font-size:11px;
                    ">

                        <span style="color:{TEXT_WHITE};">
                            Target 2
                        </span>

                        <b style="color:{TEXT_WHITE};">
                            {r2:.2f}
                        </b>

                    </div>

                </div>

            </div>
            """
        )

        _render_html(
            f"""
            <div style="{_card_style()}">

                <div style="
                    font-size:11.5px;
                    font-weight:800;
                    color:{TEXT_WHITE};
                    margin-bottom:6px;
                    border-bottom:2px solid {ACCENT};
                    padding-bottom:4px;
                ">
                    ℹ️ SYSTEM SCORING METHODOLOGY
                </div>

                <div style="
                    font-size:10.5px;
                    color:{TEXT_MUTED};
                    line-height:1.45;
                ">

                    <b style="color:{TEXT_WHITE};">
                        Trend --- 40 pts
                    </b>

                    <br>

                    ราคาเทียบ EMA20, EMA50 และ MA200

                    <br><br>

                    <b style="color:{TEXT_WHITE};">
                        Momentum --- 30 pts
                    </b>

                    <br>

                    MACD, ADX และ Volume Confirmation

                    <br><br>

                    <b style="color:{TEXT_WHITE};">
                        Reward / Risk --- 30 pts
                    </b>

                    <br>

                    ประเมินจากผลตอบแทนเทียบกับ downside

                </div>

            </div>
            """
        )

    # ==============================================================
    # BOTTOM SECTION
    # ==============================================================

    st.markdown(
        "<div style='margin-top:12px;'></div>",
        unsafe_allow_html=True,
    )

    b_c1, b_c2 = st.columns(
        [1.0, 1.5],
        gap="medium",
    )

    # ==============================================================
    # BOTTOM LEFT - RISK / REWARD
    # ==============================================================

    with b_c1:

        rr_color = (
            GREEN
            if rr_ratio >= 2.0
            else (
                AMBER
                if rr_ratio >= 1.5
                else RED
            )
        )

        upside_bar = min(
            100,
            max(
                0,
                upside_pct * 2
            ),
        )

        downside_bar = min(
            100,
            max(
                0,
                downside_pct * 5
            ),
        )

        _render_html(
            f"""
            <div style="{_card_style()}">

                <div style="
                    font-size:12px;
                    font-weight:800;
                    color:{TEXT_WHITE};
                    margin-bottom:8px;
                    border-bottom:2px solid {ACCENT};
                    padding-bottom:4px;
                ">
                    RISK / REWARD
                </div>

                <div style="margin-bottom:6px;">

                    <div style="
                        display:flex;
                        justify-content:space-between;
                        font-size:10.5px;
                        color:{TEXT_MUTED};
                    ">

                        <span>
                            Expected Upside
                        </span>

                        <b style="color:{GREEN};">
                            +{upside_pct:.1f}%
                        </b>

                    </div>

                    <div style="
                        background:{BORDER_SOFT};
                        height:5px;
                        border-radius:2.5px;
                        overflow:hidden;
                        margin-top:2px;
                    ">

                        <div style="
                            background:{GREEN};
                            width:{upside_bar:.0f}%;
                            height:100%;
                        "></div>

                    </div>

                </div>

                <div style="margin-bottom:10px;">

                    <div style="
                        display:flex;
                        justify-content:space-between;
                        font-size:10.5px;
                        color:{TEXT_MUTED};
                    ">

                        <span>
                            Maximum Risk
                        </span>

                        <b style="color:{RED};">
                            -{downside_pct:.1f}%
                        </b>

                    </div>

                    <div style="
                        background:{BORDER_SOFT};
                        height:5px;
                        border-radius:2.5px;
                        overflow:hidden;
                        margin-top:2px;
                    ">

                        <div style="
                            background:{RED};
                            width:{downside_bar:.0f}%;
                            height:100%;
                        "></div>

                    </div>

                </div>

                <div style="
                    display:flex;
                    justify-content:space-between;
                    align-items:center;
                    border-top:1px solid {BORDER_SOFT};
                    padding-top:6px;
                ">

                    <span style="
                        font-size:15px;
                        font-weight:900;
                        color:{rr_color};
                    ">
                        {rr_ratio:.2f} : 1
                    </span>

                    <span style="
                        font-size:9.5px;
                        color:{TEXT_MUTED};
                        text-align:right;
                    ">
                        Potential upside is significantly<br>
                        higher than defined downside.
                    </span>

                </div>

            </div>
            """
        )

    # ==============================================================
    # BOTTOM RIGHT - WHY WAIT / WHY NOW
    # ==============================================================

    with b_c2:

        reasons = [
            (
                "Trend",
                "✓" if k15_ok and k16_ok else "✕",
                GREEN if k15_ok and k16_ok else RED,
                "โครงสร้างราคาเหนือเส้นเฉลี่ย"
                if k15_ok and k16_ok
                else "ราคาอยู่ใต้ EMA20",
            ),
            (
                "Momentum",
                "✓" if k18_ok else "✕",
                GREEN if k18_ok else RED,
                "MACD สนับสนุนโมเมนตัม"
                if k18_ok
                else "MACD เป็นขาลง",
            ),
            (
                "Volume",
                "✓" if k20_ok else "✕",
                GREEN if k20_ok else RED,
                "มี Volume ยืนยัน"
                if k20_ok
                else "วอลุ่มไม่หนุน",
            ),
            (
                "Risk / Reward",
                "✓" if k_rr_ok else "✕",
                GREEN if k_rr_ok else RED,
                "อัตราผลตอบแทนคุ้มค่า"
                if k_rr_ok
                else "อัตราผลตอบแทนยังไม่คุ้มความเสี่ยง",
            ),
        ]

        reason_cards = "".join(
            f"""
            <div style="
                background:{BG_CHIP};
                padding:7px;
                border-radius:6px;
                text-align:center;
            ">

                <div style="
                    font-size:9.5px;
                    color:{color};
                    font-weight:bold;
                ">
                    {icon} {name}
                </div>

                <div style="
                    font-size:9px;
                    color:{TEXT_MUTED};
                    margin-top:1px;
                ">
                    {desc}
                </div>

            </div>
            """
            for name, icon, color, desc in reasons
        )

        wait_title = (
            "WHY WAIT?"
            if readiness != "READY"
            else "WHY NOW?"
        )

        wait_subtitle = (
            "เหตุผลที่ระบบยังรอการยืนยันก่อนเข้าซื้อ"
            if readiness != "READY"
            else "เหตุผลที่สัญญาณมีความพร้อมมากขึ้น"
        )

        _render_html(
            f"""
            <div style="{_card_style()}">

                <div style="
                    font-size:12px;
                    font-weight:800;
                    color:{ACCENT};
                    margin-bottom:4px;
                ">
                    💡 {wait_title}
                </div>

                <div style="
                    font-size:10.5px;
                    color:{TEXT};
                    margin-bottom:6px;
                ">
                    {wait_subtitle}
                </div>

                <div style="
                    display:grid;
                    grid-template-columns:repeat(4,1fr);
                    gap:6px;
                    margin-bottom:6px;
                ">
                    {reason_cards}
                </div>

                <div style="
                    background:rgba(56,189,248,.08);
                    border-left:3px solid {ACCENT};
                    padding:6px 10px;
                    border-radius:0 6px 6px 0;
                    font-size:10.5px;
                    color:{TEXT};
                ">
                    <b>สรุป:</b> {summary_text}
                </div>

            </div>
            """
        )

    render_nav_footer(
        "m3",
        prev_page=" Fair Value",
        next_page=" AI Prediction",
    )
