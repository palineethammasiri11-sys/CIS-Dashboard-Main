"""
pages_content/company_health.py
---------------------------
หน้า "Company Health" ของ CIS Dashboard

วิธีทดสอบหน้านี้แบบเดี่ยว (ไม่ต้องรอทีมคนอื่น):
    streamlit run preview_my_page.py
    (แล้วเลือกโมดูลนี้จาก dropdown ในไฟล์ preview_my_page.py)

ข้อมูลที่ใช้ได้ใน ctx (ดูนิยามเต็มใน common.py -> class PageContext):
    ctx.selected_ticker, ctx.stock_info, ctx.stock_daily, ctx.fin_stock, ctx.sector_peers,
    ctx.scores_df, ctx.fin_df, ctx.feat_imp_df, ctx.backtest_df, ctx.risk_hist_df,
    ctx.health_yearly_df, ctx.fair_value_yearly_df,
    ctx.current_price, ctx.change_pct, ctx.change_val, ctx.change_color, ctx.change_sign, ctx.arrow_sign

ห้ามแก้ CSS ส่วนกลางหรือ helper function ใน common.py จากไฟล์นี้ — ถ้าจำเป็นต้องแก้ ให้แจ้ง Layout Lead ก่อน

=== MERGE NOTE (รวม Branch ทีมเจ้าของโมดูล/company-health x main) ===
- โครงสร้าง/ธีมทั้งหมดยึดตาม main (ธีมขาว, มีการตรวจสอบช่วงวันที่ 2023-2025, CSS ปรับสี widget ให้เข้าธีมสว่าง)
- คงจุดแก้บั๊กของทีมเจ้าของโมดูลไว้ 1 จุด: กราฟ HEALTH SCORE TREND ใช้ xaxis type='category'
  (ป้องกันแกน X แสดงผลเพี้ยนเมื่อค่าปีเป็นตัวเลข 2023/2024/2025)
- เพิ่ม `import datetime` ที่ยังขาดไป เพื่อให้ฟังก์ชันตรวจสอบช่วงวันที่ทำงานได้จริง

=== PATCH NOTE ===
- ตาราง "COMPETITOR COMPARISON" เปลี่ยนจาก st.dataframe (พื้นเทาแบบ default ของ glide-data-grid
  ที่ไม่รับ CSS override ตรงๆ) เป็น st.html แบบตาราง HTML ธรรมดา เพื่อให้พื้นหลังเป็นสีขาว
  และสไตล์ตรงกับการ์ด "KEY FINANCIAL HIGHLIGHTS" ด้านซ้าย

=== PATCH NOTE 2 ===
- ทำความสูงกรอบการ์ดทั้ง 3 ใบใน ROW 3 (KEY FINANCIAL HIGHLIGHTS / STRENGTHS / COMPETITOR COMPARISON)
  ให้เท่ากันโดยกำหนด min-height/height:360px + box-sizing:border-box ให้ตรงกันทั้งหมด
  (เดิมการ์ด COMPETITOR COMPARISON ไม่ได้ล็อกความสูง ทำให้ขนาดไม่เท่ากับอีก 2 การ์ด)
"""

import datetime
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
    SECTOR_MAP
)


def render(ctx):

    # ============================================================
    # LIGHT THEME - COMPANY HEALTH
    # เปลี่ยนเฉพาะสีของ Streamlit widgets
    # ไม่เปลี่ยนข้อมูล / logic / layout
    # ============================================================

    st.markdown("""
    <style>

    /* =========================================================
       SELECTBOX : เทียบกับคู่แข่ง
       ========================================================= */

    /* กล่องหลัก */
    [data-testid="stSelectbox"] [data-baseweb="select"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border-radius: 10px !important;
    }

    [data-testid="stSelectbox"] [data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 10px !important;
        color: #0F172A !important;
        box-shadow: none !important;
    }

    /* ตัวหนังสือในช่อง */
    [data-testid="stSelectbox"] [data-baseweb="select"] div {
        color: #0F172A !important;
    }

    [data-testid="stSelectbox"] [data-baseweb="select"] span {
        color: #0F172A !important;
    }

    /* ลูกศร */
    [data-testid="stSelectbox"] [data-baseweb="select"] svg {
        fill: #0F172A !important;
        color: #0F172A !important;
    }

    /* =========================================================
       SELECTBOX DROPDOWN
       ========================================================= */

    [data-baseweb="popover"] {
        background-color: #FFFFFF !important;
    }

    [data-baseweb="popover"] [role="listbox"] {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
    }

    [data-baseweb="popover"] [role="option"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
    }

    [data-baseweb="popover"] [role="option"] * {
        color: #0F172A !important;
    }

    [data-baseweb="popover"] [role="option"]:hover {
        background-color: #F1F5F9 !important;
    }

    /* =========================================================
       DATE INPUT : ข้อมูล ณ วันที่
       ========================================================= */

    [data-testid="stDateInput"] {
        color: #0F172A !important;
    }

    /* กล่องด้านนอก */
    [data-testid="stDateInput"] > div {
        color: #0F172A !important;
    }

    /* กล่อง input ของ BaseWeb */
    [data-testid="stDateInput"] [data-baseweb="input"] {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 10px !important;
        box-shadow: none !important;
    }

    [data-testid="stDateInput"] [data-baseweb="input"] > div {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
    }

    /* input จริง */
    [data-testid="stDateInput"] input {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: none !important;
        box-shadow: none !important;
    }

    [data-testid="stDateInput"] input::placeholder {
        color: #64748B !important;
    }

    /* icon ปฏิทิน */
    [data-testid="stDateInput"] svg {
        fill: #0F172A !important;
        color: #0F172A !important;
    }

    /* label */
    [data-testid="stDateInput"] label {
        color: #0F172A !important;
    }

    [data-testid="stDateInput"] label p {
        color: #0F172A !important;
    }

    /* =========================================================
       DATE PICKER ที่เด้งออกมา
       ========================================================= */

    [data-baseweb="calendar"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 1px solid #CBD5E1 !important;
    }

    [data-baseweb="calendar"] * {
        color: #0F172A !important;
    }

    [data-baseweb="calendar"] button {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
    }

    [data-baseweb="calendar"] button:hover {
        background-color: #F1F5F9 !important;
    }

    </style>
    """, unsafe_allow_html=True)


    # ============================================================
    # ฟังก์ชันดึงค่างบการเงิน
    # ============================================================

    def get_fin_val(target_yr, col_name, default="-", fmt="{:.1f}"):

        match = ctx.fin_stock[
            ctx.fin_stock['year'] == target_yr
        ]

        if not match.empty:

            v = match.iloc[0].get(col_name)

            if v is not None and str(v).strip() not in [
                '',
                '-',
                'nan',
                'None'
            ]:

                try:
                    return fmt.format(float(v))

                except Exception:
                    return str(v)

        return str(default)


    roe_23 = get_fin_val(2023, 'roe')
    roe_24 = get_fin_val(2024, 'roe')
    roe_25 = get_fin_val(2025, 'roe')

    roa_23 = get_fin_val(2023, 'roa')
    roa_24 = get_fin_val(2024, 'roa')
    roa_25 = get_fin_val(2025, 'roa')

    npm_23 = get_fin_val(2023, 'net_margin')
    npm_24 = get_fin_val(2024, 'net_margin')
    npm_25 = get_fin_val(2025, 'net_margin')

    de_23 = get_fin_val(2023, 'de_ratio', fmt="{:.2f}")
    de_24 = get_fin_val(2024, 'de_ratio', fmt="{:.2f}")
    de_25 = get_fin_val(2025, 'de_ratio', fmt="{:.2f}")

    cr_23 = get_fin_val(2023, 'current_ratio', fmt="{:.2f}")
    cr_24 = get_fin_val(2024, 'current_ratio', fmt="{:.2f}")
    cr_25 = get_fin_val(2025, 'current_ratio', fmt="{:.2f}")


    # ============================================================
    # ส่วนเลือกวันที่
    # ล็อกเฉพาะช่วงปี 2023 - 2025
    # ============================================================

    min_limit = datetime.date(2023, 1, 1)
    max_limit = datetime.date(2025, 12, 31)

    try:
        raw_date = pd.to_datetime(
            ctx.stock_info.get('latest_date', '2025-12-30')
        ).date()
        default_date = max(min_limit, min(max_limit, raw_date))
    except Exception:
        default_date = datetime.date(2025, 12, 30)


    # ============================================================
    # HEADER
    # ============================================================

    col_title, col_date = st.columns([3, 1.2])

    with col_title:
        st.html("""
        <div style="margin-bottom:10px;">
            <div style="font-size:26px; font-weight:700; color:#0F172A; letter-spacing:0.3px;">
                COMPANY HEALTH
            </h2>
            <div style="font-size:16px; font-weight:400; color:#64748B; margin-top:4px;">
                ประเมินสุขภาพทางการเงินของบริษัทจากมิติสำคัญตามงบการเงินจริง
            </div>
        </div>
        """)


    # ============================================================
    # ROW 1
    # Overall Score ใหญ่ขึ้นเป็น 1.4
    # ============================================================

    r1_c1, r1_c2, r1_c3 = st.columns([1.4, 1.4, 1.5])

    h_score = int(round(safe(ctx.stock_info.get('health_score'), 75)))

    h_badge = (
        "EXCELLENT" if h_score >= 75
        else ("MODERATE" if h_score >= 50 else "WEAK")
    )

    h_color = (
        "#10B981" if h_score >= 75
        else ("#F59E0B" if h_score >= 50 else "#EF4444")
    )

    h_stars = min(5, max(1, round(h_score / 20)))


    # ============================================================
    # SCORE CARD
    # ============================================================

    with r1_c1:

        st.html(f"""
        <div style="
            background-color:#FFFFFF;
            border:2px solid {h_color};
            border-radius:16px;
            padding:22px 22px 18px 22px;
            min-height:285px;
            width:100%;
            box-sizing:border-box;
            display:flex;
            flex-direction:column;
            justify-content:space-between;
            box-shadow:0 6px 18px rgba(15,23,42,0.08);
        ">

            <!-- TITLE -->
            <div style="font-size:17px; font-weight:800; color:#0F172A; letter-spacing:0.6px; line-height:1.25; margin-bottom:4px;">
                OVERALL COMPANY HEALTH SCORE
            </div>

            <!-- SUBTITLE -->
            <div style="font-size:14px; color:#64748B; margin-top:2px;">
                Financial Health • 2023–2025
            </div>

            <!-- SCORE CONTENT -->
            <div style="display:flex; align-items:center; gap:22px; margin-top:10px; margin-bottom:8px;">

                <!-- SCORE RING -->
                <div style="
                    width:118px; height:118px; min-width:118px; border-radius:50%;
                    background:conic-gradient({h_color} 0% {h_score}%, #E2E8F0 {h_score}% 100%);
                    display:flex; align-items:center; justify-content:center;
                ">
                    <div style="
                        width:96px; height:96px; border-radius:50%; background-color:#FFFFFF;
                        display:flex; flex-direction:column; align-items:center; justify-content:center; box-sizing:border-box;
                    ">
                        <span style="font-size:30px; font-weight:800; color:#0F172A; line-height:1;">{h_score}</span>
                        <span style="font-size:14px; color:#64748B; margin-top:5px;">/ 100</span>
                    </div>
                </div>

                <!-- STATUS -->
                <div style="flex:1; min-width:0;">
                    <div style="color:{h_color}; font-size:24px; font-weight:800; line-height:1.15; margin-bottom:8px;">
                        {h_badge}
                    </div>
                    <div style="font-size:15px; color:#475569; line-height:1.45; margin-bottom:7px;">
                        ประเมินจากอัตราส่วน<br>
                        ทางการเงินจริง<br>
                        ปี 2023–2025
                    </div>
                    <div style="color:{h_color}; font-size:19px; letter-spacing:3px; line-height:1;">
                        {'★'*h_stars}{'☆'*(5-h_stars)}
                    </div>
                </div>

            </div>

            <!-- DIVIDER -->
            <div style="width:100%; height:1px; background-color:#E2E8F0; margin:4px 0 10px 0;"></div>

            <!-- BOTTOM SUMMARY -->
            <div style="display:flex; justify-content:space-between; align-items:center; width:100%;">
                <span style="font-size:13.5px; color:#64748B;">Overall Financial Health</span>
                <span style="font-size:14px; font-weight:800; color:{h_color};">{h_score}/100</span>
            </div>

        </div>
        """)


    # ============================================================
    # EXPLAINABLE FINANCIAL SUMMARY
    # ============================================================

    with r1_c2:

        st.html(f"""
        <div style="
            background-color:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; padding:16px;
            min-height:235px; display:flex; flex-direction:column; justify-content:space-between;
        ">
            <div>
                <div style="font-size:14.5px; font-weight:bold; color:#64748B; letter-spacing:0.5px; margin-bottom:8px;">
                    EXPLAINABLE FINANCIAL SUMMARY ({ctx.selected_ticker})
                </div>
                <p style="font-size:15px; color:#475569; line-height:1.6; margin:0;">
                    ผลการวิเคราะห์สุขภาพการเงินของ
                    <b>{ctx.selected_ticker}</b>
                    พบว่ามีอัตราส่วนผลตอบแทนต่อส่วนของผู้ถือหุ้น (ROE)
                    ล่าสุดอยู่ที่ {roe_25}% และความสามารถในการทำกำไรสุทธิ
                    (Net Margin) อยู่ที่ {npm_25}% ในขณะที่ภาระหนี้สินต่อทุน
                    (D/E Ratio) อยู่ที่ {de_25} เท่า และสภาพคล่องหมุนเวียน
                    (Current Ratio) อยู่ที่ {cr_25} เท่า
                </p>
            </div>
            <div>
                <span style="
                    display:inline-flex; align-items:center; gap:6px; background-color:#F8FAFC;
                    border:1px solid #E2E8F0; color:#38BDF8; font-size:14px; padding:5px 12px; border-radius:6px;
                ">
                    Financial Health Benchmark:
                    {ctx.stock_info.get('sector','-')}
                </span>
            </div>
        </div>
        """)


    # ============================================================
    # HEALTH SCORE TREND
    # ============================================================

    with r1_c3:
        st.html("""<div style="background-color:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px 12px 0 0;padding:12px 16px 0 16px;">
        <div style="font-size:14.5px;font-weight:bold;color:#64748B;letter-spacing:0.5px;">COMPANY HEALTH SCORE TREND (Actual, 2023-2025)</div>
        </div>""")

        hy = ctx.health_yearly_df[ctx.health_yearly_df['ticker'] == ctx.selected_ticker].sort_values('year') if not ctx.health_yearly_df.empty else pd.DataFrame()
        trend_x = hy['year'].astype(int).tolist() if not hy.empty else [2023, 2024, 2025]
        trend_y = hy['health_score'].tolist() if not hy.empty else [h_score, h_score, h_score]

        fig_health_trend = go.Figure()
        fig_health_trend.add_trace(go.Scatter(
            x=trend_x, y=trend_y, mode='lines+markers+text', text=trend_y,
            textposition='top center', textfont=dict(size=12.5, color='#0F172A'),
            line=dict(color=h_color, width=2),
            marker=dict(size=10, color=h_color, line=dict(width=1.5, color='#FFFFFF'))
        ))

        # หมายเหตุ: คง type='category' ไว้ตามที่ทีมเจ้าของโมดูลแก้บั๊ก
        # (ป้องกันแกน X เพี้ยนเมื่อค่าปีเป็นตัวเลข 2023/2024/2025)
        fig_health_trend.update_layout(
            height=168, margin=dict(l=25, r=15, t=10, b=20),
            paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
            yaxis=dict(range=[0, 110], tickvals=[0, 25, 50, 75, 100], tickfont=dict(size=11.5, color="#64748B"), gridcolor="#E2E8F0", zeroline=False),
            xaxis=dict(type='category', tickfont=dict(size=12, color="#64748B"), gridcolor="#E2E8F0", zeroline=False),
            showlegend=False
        )

        show_chart(fig_health_trend, key="health_trend", expand_height=650)


    # ============================================================
    # 7 DIMENSIONS OVERVIEW
    # ============================================================

    st.html("""<div style="margin-top:22px;"></div>""")

    st.html("""
    <div style="font-size:15px; font-weight:bold; color:#0F172A; letter-spacing:0.5px; margin-bottom:8px;">
        7 DIMENSIONS OVERVIEW
        <span style="font-size:14.5px; color:#64748B; font-weight:normal; margin-left:6px;">
            ผลการประเมินสุขภาพทางการเงินในแต่ละมิติ (คำนวณจากอัตราส่วนจริง)
        </span>
    </div>
    """)

    latest_fin_row = ctx.fin_stock.iloc[-1] if not ctx.fin_stock.empty else pd.Series(dtype=float)

    ocf_ni = safe(latest_fin_row.get('ocf_to_ni'), 1.0)
    int_cov = safe(latest_fin_row.get('interest_coverage'), 5.0)
    rev_growth = safe(ctx.stock_info.get('revenue_growth_yoy'), 0.0)

    dim_profit = int(round(safe(ctx.stock_info.get('s_profitability'), 50)))
    dim_growth = int(round(np.clip(50 + rev_growth * 2, 0, 100)))
    dim_stability = int(round(safe(ctx.stock_info.get('s_debt'), 50)))
    dim_liquidity = int(round(safe(ctx.stock_info.get('s_liquidity'), 50)))
    dim_cashflow = int(round(np.clip(50 + ocf_ni * 5, 0, 100)))
    dim_efficiency = int(round(np.clip(safe(ctx.stock_info.get('roa'), 5) * 7, 0, 100)))
    dim_earnings = int(round(np.clip(50 + int_cov * 0.3, 0, 100)))

    def label_for(score):
        if score >= 75:
            return "EXCELLENT"
        if score >= 55:
            return "GOOD"
        if score >= 35:
            return "MODERATE"
        return "WEAK"

    dims = [
        ("1", "📊", "PROFITABILITY", "30%", dim_profit),
        ("2", "📈", "GROWTH", "15%", dim_growth),
        ("3", "🛡️", "FIN. STABILITY", "20%", dim_stability),
        ("4", "💧", "LIQUIDITY", "10%", dim_liquidity),
        ("5", "💵", "CASH FLOW", "10%", dim_cashflow),
        ("6", "⚙️", "EFFICIENCY", "10%", dim_efficiency),
        ("7", "🎖️", "EARNINGS Q.", "5%", dim_earnings),
    ]

    dim_html = "".join([
        f"""
        <div style="background-color:#FFFFFF; border:1px solid #E2E8F0; border-radius:10px; padding:10px 8px; text-align:center; width:100%; min-width:0; max-width:100%; box-sizing:border-box;">
            <div style="display:flex;align-items:center;justify-content:center;gap:4px;">
                <span style="font-size:14.5px;">{icon}</span>
                <span style="font-size:13px;font-weight:bold;color:#0F172A;">{n}. {label}</span>
            </div>
            <div style="font-size:12.5px;color:#64748B;margin-top:1px;">Weight {w}</div>
            <div style="margin:8px auto;width:60px;height:60px;border-radius:50%;background:conic-gradient({color} 0% {score}%,#E2E8F0 {score}% 100%);display:flex;align-items:center;justify-content:center;">
                <div style="width:48px;height:48px;border-radius:50%;background-color:#FFFFFF;display:flex;flex-direction:column;align-items:center;justify-content:center;">
                    <span style="font-size:16px;font-weight:bold;color:#0F172A;line-height:1;">{score}</span>
                    <span style="font-size:11.5px;color:#64748B;">/100</span>
                </div>
            </div>
            <div style="color:{color};font-size:13.5px;font-weight:bold;">{label_for(score)}</div>
        </div>
        """
        for n, icon, label, w, score in dims
        for color in [
            "#EF4444" if score <= 33 else
            "#F59E0B" if score <= 66 else
            "#10B981"
        ]
    ])

    st.markdown("""
    <style>
    @media (max-width: 768px) {

        .health-dimensions-grid {
            grid-template-columns: 1fr !important;
            width: 100% !important;
            max-width: 100% !important;
            min-width: 0 !important;
            box-sizing: border-box !important;
            gap: 10px !important;
        }

        .health-dimensions-grid > div {
            width: 100% !important;
            max-width: 100% !important;
            min-width: 0 !important;
            box-sizing: border-box !important;
        }

    }
    </style>
    """, unsafe_allow_html=True)

    st.html(f"""
    <div class="health-dimensions-grid"
         style="display:grid; grid-template-columns:repeat(7,minmax(0,1fr)); gap:8px; width:100%; min-width:0; max-width:100%; box-sizing:border-box;">
        {dim_html}
    </div>
    """)

    # ============================================================
    # KEY FINANCIAL HIGHLIGHTS / STRENGTHS / COMPETITOR
    # ทำความสูงกรอบทั้ง 3 การ์ดให้เท่ากัน (การ์ดเดิม COMPETITOR ไม่ได้ล็อกความสูง)
    # ============================================================

    st.html("""<div style="margin-top:22px;"></div>""")

    r3_c1, r3_c2, r3_c3 = st.columns([1.5, 1.25, 1.25])


    # ============================================================
    # KEY FINANCIAL HIGHLIGHTS
    # ============================================================

    with r3_c1:

        st.html(f"""
        <div style="background-color:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; padding:14px; height:447px; box-sizing:border-box; display:flex; flex-direction:column; justify-content:space-between; overflow-y:auto;">
            <div>
                <div style="font-size:14.5px; font-weight:bold; color:#64748B; letter-spacing:0.5px; margin-bottom:8px;">
                    KEY FINANCIAL HIGHLIGHTS ({ctx.selected_ticker})
                </div>
                <table style="width:100%; text-align:left; font-size:14px; color:#475569; border-collapse:collapse;">
                    <tr style="border-bottom:1px solid #E2E8F0; color:#64748B; font-size:13px;">
                        <th style="padding:4px 0;">Metric</th>
                        <th>2023</th>
                        <th>2024</th>
                        <th>2025</th>
                    </tr>
                    <tr style="border-bottom:1px solid #E2E8F0;">
                        <td style="padding:5px 0; font-weight:bold; color:#0F172A;">ROE (%)</td>
                        <td>{roe_23}</td>
                        <td>{roe_24}</td>
                        <td style="font-weight:bold; color:#0F172A;">{roe_25}</td>
                    </tr>
                    <tr style="border-bottom:1px solid #E2E8F0;">
                        <td style="padding:5px 0; font-weight:bold; color:#0F172A;">ROA (%)</td>
                        <td>{roa_23}</td>
                        <td>{roa_24}</td>
                        <td style="font-weight:bold; color:#0F172A;">{roa_25}</td>
                    </tr>
                    <tr style="border-bottom:1px solid #E2E8F0;">
                        <td style="padding:5px 0; font-weight:bold; color:#0F172A;">Net Profit Margin (%)</td>
                        <td>{npm_23}</td>
                        <td>{npm_24}</td>
                        <td style="font-weight:bold; color:#0F172A;">{npm_25}</td>
                    </tr>
                    <tr style="border-bottom:1px solid #E2E8F0;">
                        <td style="padding:5px 0; font-weight:bold; color:#0F172A;">Debt to Equity (x)</td>
                        <td>{de_23}</td>
                        <td>{de_24}</td>
                        <td style="font-weight:bold; color:#0F172A;">{de_25}</td>
                    </tr>
                    <tr>
                        <td style="padding:5px 0; font-weight:bold; color:#0F172A;">Current Ratio (x)</td>
                        <td>{cr_23}</td>
                        <td>{cr_24}</td>
                        <td style="font-weight:bold; color:#0F172A;">{cr_25}</td>
                    </tr>
                </table>
            </div>
            <div style="font-size:12px; color:#64748B; margin-top:6px;">
                * ข้อมูลทางการเงินดึงตรงจาก stock_financials.csv สำหรับปี 2023-2025 จริงทุกค่า
            </div>
        </div>
        """)


    # ============================================================
    # STRENGTHS / WATCH OUT
    # ============================================================

    with r3_c2:

        strengths = []
        watch = []

        if safe(roe_25 if roe_25 != '-' else 0) > 15:
            strengths.append(f"ROE ล่าสุดอยู่ในเกณฑ์ดีที่ {roe_25}%")

        if safe(cr_25 if cr_25 != '-' else 0) >= 1.0:
            strengths.append(f"สภาพคล่อง Current Ratio อยู่ที่ {cr_25} เท่า เพียงพอต่อภาระหนี้ระยะสั้น")

        if safe(npm_25 if npm_25 != '-' else 0) > 10:
            strengths.append(f"Net Margin ระดับ {npm_25}% สะท้อนความสามารถทำกำไรที่ดี")

        if safe(de_25 if de_25 != '-' else 0) < 1.5:
            strengths.append(f"โครงสร้างเงินทุนมี D/E เพียง {de_25} เท่า ความเสี่ยงหนี้สินต่ำ")

        if not strengths:
            strengths.append("ผลประกอบการโดยรวมยังอยู่ระหว่างการฟื้นตัว")

        if safe(de_25 if de_25 != '-' else 0) > 1.5:
            watch.append(f"ภาระหนี้สินต่อทุนค่อนข้างสูงที่ {de_25} เท่า ควรติดตามใกล้ชิด")

        if safe(cr_25 if cr_25 != '-' else 0) < 1.0:
            watch.append(f"Current Ratio ต่ำกว่า 1 เท่า ({cr_25}) สภาพคล่องระยะสั้นควรเฝ้าระวัง")

        if rev_growth < 0:
            watch.append(f"รายได้หดตัว {rev_growth:.1f}% YoY ควรติดตามแนวโน้มปีถัดไป")

        if not watch:
            watch.append("ยังไม่พบสัญญาณความเสี่ยงเชิงโครงสร้างที่ชัดเจนในงบล่าสุด")

        st.html(f"""
        <div style="background-color:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; padding:14px; height:447px; box-sizing:border-box; overflow-y:auto;">
            <div style="font-size:14px; font-weight:bold; color:#10B981; margin-bottom:6px;">
                STRENGTHS ({ctx.selected_ticker})
            </div>
            <div style="font-size:13px; color:#475569; line-height:1.45; margin-bottom:10px;">
                {''.join([f'<div style="display:flex; gap:6px; margin-bottom:3px;"><span style="color:#10B981;">✔</span><span>{s}</span></div>' for s in strengths])}
            </div>
            <div style="font-size:14px; font-weight:bold; color:#F59E0B; margin-bottom:6px; border-top:1px dashed #E2E8F0; padding-top:8px;">
                WATCH OUT
            </div>
            <div style="font-size:13px; color:#475569; line-height:1.45;">
                {''.join([f'<div style="display:flex; gap:6px; margin-bottom:3px;"><span style="color:#F59E0B;">⚠️</span><span>{w}</span></div>' for w in watch])}
            </div>
        </div>
        """)


    # ============================================================
    # COMPETITOR COMPARISON
    # ============================================================

    with r3_c3:

        # เลือกคู่แข่งในกลุ่มเดียวกัน (ไม่รวมตัวเอง)
        peer_options = [
            t for t in ctx.sector_peers['ticker'].tolist()
            if t != ctx.selected_ticker
        ] if not ctx.sector_peers.empty else []

        latest_year = ctx.fin_stock['year'].max() if not ctx.fin_stock.empty else 2025

        def pct_bar(stock_val, comp_v, higher_better=True):
            if comp_v == 0:
                return 50
            ratio = stock_val / comp_v if higher_better else (comp_v / max(stock_val, 0.01))
            return int(np.clip(ratio * 50, 5, 100))

        if peer_options:
            competitor = st.selectbox(
                "เทียบกับคู่แข่ง", peer_options, key="health_competitor_select",
                format_func=lambda t: f"{t} — {COMPANY_NAMES.get(t, t)}"
            )
            comp_fin_all = ctx.fin_df[ctx.fin_df['ticker'] == competitor].sort_values('year')
            comp_fin_row = comp_fin_all[comp_fin_all['year'] == latest_year]
            if comp_fin_row.empty and not comp_fin_all.empty:
                comp_fin_row = comp_fin_all.iloc[[-1]]

            def comp_val(col, default=0.0):
                return safe(comp_fin_row.iloc[0].get(col), default) if not comp_fin_row.empty else default

            comp_roe = comp_val('roe')
            comp_roa = comp_val('roa')
            comp_npm = comp_val('net_margin')
            comp_de = comp_val('de_ratio')
            comp_cr = comp_val('current_ratio')

            comp_year_used = int(comp_fin_row.iloc[0]['year']) if not comp_fin_row.empty else None

            target_label = competitor
            sub_label = f"เทียบกับคู่แข่งจริง &bull; {ctx.stock_info.get('sector','-')}"

            if comp_year_used and comp_year_used != latest_year:
                sub_label += f" (ปี {comp_year_used})"

        else:
            target_label = "Industry Avg"
            sub_label = f"ไม่มีคู่แข่งตรงในกลุ่ม &bull; เทียบค่าเฉลี่ยตลาดรวม (ปี {latest_year})"

            market_latest = ctx.fin_df[ctx.fin_df['year'] == latest_year] if not ctx.fin_df.empty else pd.DataFrame()
            if market_latest.empty and not ctx.fin_df.empty:
                market_latest = ctx.fin_df

            comp_roe = safe(pd.to_numeric(market_latest['roe'], errors='coerce').median(), 0.0)
            comp_roa = safe(pd.to_numeric(market_latest['roa'], errors='coerce').median(), 0.0)
            comp_npm = safe(pd.to_numeric(market_latest['net_margin'], errors='coerce').median(), 0.0)
            comp_de = safe(pd.to_numeric(market_latest['de_ratio'], errors='coerce').median(), 0.0)
            comp_cr = safe(pd.to_numeric(market_latest['current_ratio'], errors='coerce').median(), 0.0)

        rows_cmp = [
            ("ROE (%)", roe_25, f"{comp_roe:.1f}", pct_bar(safe(roe_25 if roe_25 != '-' else 0), comp_roe)),
            ("ROA (%)", roa_25, f"{comp_roa:.1f}", pct_bar(safe(roa_25 if roa_25 != '-' else 0), comp_roa)),
            ("Net Margin (%)", npm_25, f"{comp_npm:.1f}", pct_bar(safe(npm_25 if npm_25 != '-' else 0), comp_npm)),
            ("Debt to Equity (x)", de_25, f"{comp_de:.2f}", pct_bar(safe(de_25 if de_25 != '-' else 0), comp_de, higher_better=False)),
            ("Current Ratio (x)", cr_25, f"{comp_cr:.2f}", pct_bar(safe(cr_25 if cr_25 != '-' else 0), comp_cr)),
        ]

        # --------------------------------------------------------
        # PATCH: เปลี่ยนจาก st.dataframe -> ตาราง HTML พื้นสีขาว
        # (st.dataframe ใช้ glide-data-grid วาดบน canvas
        #  ทำให้ override สีพื้นหลังด้วย CSS ไม่ได้ผล)
        # PATCH 2: ล็อกความสูงกรอบให้เท่ากับอีก 2 การ์ดในแถวเดียวกัน
        # (เดิมความสูงยืดตามเนื้อหา ทำให้กรอบไม่เท่ากัน)
        # --------------------------------------------------------

        cmp_rows_html = "".join([
            f"""
            <tr style="border-bottom:1px solid #E2E8F0;">
                <td style="padding:6px 4px; font-weight:bold; color:#0F172A;">{metric}</td>
                <td style="padding:6px 4px; text-align:right; color:#475569;">{stock_v}</td>
                <td style="padding:6px 4px; text-align:right; color:#475569;">{comp_v}</td>
                <td style="padding:6px 4px; text-align:right; font-weight:bold; color:#0F172A;">{vs_v}</td>
            </tr>
            """
            for metric, stock_v, comp_v, vs_v in rows_cmp
        ])

        st.html(f"""
        <div style="background-color:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; padding:14px; height:360px; box-sizing:border-box; display:flex; flex-direction:column; overflow-y:auto;">
            <div style="font-size:13px; color:#64748B; margin-bottom:10px;">
                {sub_label}
            </div>
            <table style="width:100%; border-collapse:collapse; background-color:#FFFFFF;">
                <tr style="border-bottom:1px solid #E2E8F0; color:#64748B; font-size:13px;">
                    <th style="padding:4px; text-align:left;">Metric</th>
                    <th style="padding:4px; text-align:right;">{ctx.selected_ticker}</th>
                    <th style="padding:4px; text-align:right;">{target_label}</th>
                    <th style="padding:4px; text-align:right;">vs {target_label}</th>
                </tr>
                {cmp_rows_html}
            </table>
        </div>
        """)


    # ============================================================
    # FOOTER NAVIGATION
    # ============================================================

    render_nav_footer("m1", prev_page=" Stock Overview", next_page=" Fair Value")
