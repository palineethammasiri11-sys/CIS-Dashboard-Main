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

=== MERGE NOTE (รวม Branch main x Copy-ทีมออกแบบ) ===
- ธีม/เลย์เอาต์ทั้งหมดยึดตามทีมออกแบบ (การ์ดพื้นขาว, สีไดนามิกตามจำนวนดาว/คะแนน)
- Logic การเช็คข้อมูลไม่พอ (no_data / single_member_sector / rank_txt) ยึดตาม main ทั้งหมด
  เพื่อไม่ให้หน้าจอพังหรือแสดงผลผิดเวลาข้อมูลจัดอันดับไม่ครบ

=== PATCH NOTE ===
- การ์ด RANKING: เพิ่มการไฮไลต์เฉพาะบล็อก "ทั้งตลาด" (whole market) ให้เด่นกว่าบล็อก "ในกลุ่ม"
  ด้วยกรอบ/พื้นหลังสีฟ้าอ่อน ตัวเลขอันดับขยายใหญ่ขึ้น และป้าย Top % เปลี่ยนเป็นพื้นทึบสีฟ้า
  (ไม่กระทบ logic การคำนวณ pct_overall / rank_txt เดิม)

=== PATCH NOTE 2 (layout reshuffle) ===
- ย้าย STRATEGIC MATRIX จาก r2_c3 (เดิมอยู่แถวกลาง คู่กับ Peer Comparison / Radar)
  ขึ้นมาไว้ที่ r1_c3 แทน DIMENSION PERCENTILE RANK เดิม และขยายให้ใหญ่ขึ้น
  (เพิ่มความสูงกราฟและขนาดฟอนต์ของ title/annotation) เพราะเป็นกราฟที่ควรเด่นที่สุด
  ของหน้านี้ ตาม feedback ทีมออกแบบ
- ลบการ์ด FINAL RECOMMENDATION (r3_c3 เดิม) ออกทั้งหมด รวมตัวแปรที่ใช้เฉพาะ
  การ์ดนี้ (rec, rec_bg, conf_lvl, sector_rank_display) เพราะไม่ได้ใช้ที่ไหนอีก
- แถว 2 (Peer Comparison / Radar) เหลือ 2 คอลัมน์ เพราะ Strategic Matrix
  ที่เคยอยู่ตำแหน่งที่ 3 ย้ายขึ้นไปแล้ว
- STRATEGIC MATRIX ปรับความสูงกราฟกลับลงมาที่ 360px (จาก 480px) ให้เท่ากับ
  การ์ด STRATEGIC INVESTMENT POSITION / RANKING ที่อยู่แถวเดียวกัน ไม่ให้สูง
  เกินเพื่อนบ้านสองใบซ้ายมือ

=== PATCH NOTE 3 (Dimension Percentile Rank เต็มความกว้าง) ===
- DIMENSION PERCENTILE RANK ย้ายออกจาก r3_c3 มาวางเต็มความกว้างของหน้า
  (เป็นบล็อกของตัวเอง ไม่อยู่ใน st.columns) ตรงพื้นที่ว่างใต้แถว Peer Comparison /
  Radar พอดี เพราะพื้นที่ตรงนั้นกว้างกว่าคอลัมน์แคบ ๆ ของ r3_c3 เดิม จึงคง grid
  มิติไว้ที่ 6 คอลัมน์/แถวตามดีไซน์ดั้งเดิม (ไม่ต้องบีบเหลือ 3 คอลัมน์แล้ว)
- แถว 3 (Competitive Advantage / Explainable AI Summary) กลับมาเหลือ 2
  คอลัมน์ เพราะ Dimension Percentile Rank ย้ายออกไปเป็นบล็อกเต็มความกว้างแล้ว

=== PATCH NOTE 4 (Dimension Percentile Rank ฟิกความสูงเท่า Radar) ===
- การ์ด DIMENSION PERCENTILE RANK (r2_c1) เปลี่ยนจาก height:430px + overflow-y:auto
  (เลื่อนได้) เป็น height:310px + overflow:hidden (ฟิกความสูง ไม่เลื่อน) ให้เท่ากับ
  กรอบกราฟ RADAR: STOCK vs SECTOR AVG (r2_c2) ที่อยู่แถวเดียวกัน
- เพื่อให้เนื้อหา 2 ชุด (เทียบทั้งตลาด + เทียบในกลุ่ม) ยังพอดีในกรอบที่เตี้ยลง
  ได้บีบ padding การ์ดนอก/การ์ดมิติย่อย และลดฟอนต์ label/ตัวเลข/tier ลงเล็กน้อย
  (ไม่กระทบ logic การคำนวณ percentile เดิม)

=== PATCH NOTE 5 (แก้กลับด้าน: ขยาย RADAR ให้เท่า Dimension แทน) ===
- พบว่า 310px ยังไม่พอกับเนื้อหาจริงของ DIMENSION PERCENTILE RANK (6 การ์ดมิติ
  เทียบตลาด + 3-6 การ์ดมิติเทียบกลุ่ม + header/divider) ทำให้ content ส่วนล่าง
  โดนตัดหายเวลาใช้ overflow:hidden
- แก้ทิศทางใหม่: กลับไปใช้ FIXED HEIGHT ที่คำนวณให้พอดีเนื้อหาจริงของ Dimension
  Card (440px, overflow:hidden) แล้วขยายความสูงกราฟ RADAR (r2_c2) ขึ้นมาให้เท่ากับ
  440px แทน เพื่อให้สองการ์ดในแถวเดียวกันสูงเท่ากันเหมือนเดิม
- PEER COMPARISON: แก้สี badge "Neutral" ของ AI Prediction จากเทา (#64748B)
  เป็นเหลือง (#F59E0B) ให้ตรงกับความหมายกลาง ๆ เหมือนคอลัมน์อื่น (ไม่กระทบ logic
  การคำนวณ threshold เดิม)

=== PATCH NOTE 6 (bugfix: 440px ยังไม่พอ -> เลิก fix height, ใช้ auto) ===
- 440px ยังไม่พอกับเนื้อหาจริงในบางเคส (ฟอนต์/line-height จริงกินพื้นที่มากกว่า
  ที่คำนวณ) ทำให้เนื้อหาแถวสุดท้ายโดน overflow:hidden ตัดอีกครั้ง
- แก้แบบถาวร: การ์ด DIMENSION PERCENTILE RANK เปลี่ยนเป็น height:auto +
  overflow:visible เท่ากับให้การ์ดสูงเท่าที่เนื้อหาต้องการจริง ไม่มีการตัดอีก
  ไม่ว่าจำนวนดาว/กลุ่มจะสั้นหรือยาวแค่ไหน
- ผลข้างเคียงที่ยอมรับ: การ์ดนี้กับ RADAR (r2_c2) จะไม่สูงเท่ากันเป๊ะ 100% ในทุก
  กรณีอีกต่อไป (เช่น กรณีกลุ่มมีหุ้นเดียว เนื้อหาสั้นกว่า การ์ดจะเตี้ยกว่า Radar
  เล็กน้อย) แต่แลกกับการไม่มีเนื้อหาถูกตัด/ตกขอบอีกเลย ซึ่งสำคัญกว่า
- RADAR (r2_c2) คงความสูงไว้ที่ 440px ตามเดิม เป็นค่าความสูงอ้างอิงกลาง ๆ ที่ดู
  สมส่วนกับความสูงเฉลี่ยของการ์ด Dimension ในเคสส่วนใหญ่ (ไม่กระทบ logic การ
  คำนวณ percentile / ai_score เดิม)

=== PATCH NOTE 7 (ลบ EXPORT & INDUSTRY DATA ออก) ===
- ลบบล็อกดาวน์โหลด CSV ("EXPORT & INDUSTRY DATA") ที่อยู่ท้ายหน้าออกทั้งหมด
  ตามคำขอ ไม่กระทบ logic หรือการ์ดอื่นใดในหน้านี้
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from common import fmt_mb, fmt_ratio, safe, render_nav_footer, COMPANY_NAMES, SECTOR_MAP


def render(ctx):
    n_sector = len(ctx.sector_peers)

    def _rank(v):
        return None if pd.isna(v) else int(v)

    sector_rank_raw = _rank(ctx.stock_info.get('sector_rank', 1))
    overall_rank_raw = _rank(ctx.stock_info.get('overall_rank', 1))
    no_data = sector_rank_raw is None or overall_rank_raw is None
    sector_rank = sector_rank_raw or 0
    overall_rank = overall_rank_raw or 0
    n_all = len(ctx.scores_df)
    pct_in_sector = round((sector_rank / max(n_sector, 1)) * 100)
    rank_txt = lambda v: '-' if not v else v

    st.markdown("""
    <div style="margin-bottom:20px;">
        <div style="font-size:26px; font-weight:700; color:#0F172A; letter-spacing:0.3px;">
            INDUSTRY BENCHMARK
        </div>
        <div style="font-size:16px; color:#64748B; margin-top:4px;">
            เปรียบเทียบศักยภาพของหุ้นกับบริษัทในกลุ่มอุตสาหกรรมและหุ้นที่ติดตาม
        </div>
    </div>
    """, unsafe_allow_html=True)

    r1_c1, r1_c2, r1_c3 = st.columns([1.1, 0.8, 2.1])

    single_member_sector = n_sector < 2

    # ดาว/label อ้างอิงตาม percentile ของอันดับ "ทั้งตลาด" (overall_rank เทียบ n_all)
    # เพื่อให้จำนวนดาวสอดคล้องกับ Top % ที่แสดงในการ์ด RANKING เสมอ
    # (ไม่ใช้ sector_rank ตัดสินดาวอีกต่อไป เพราะกลุ่มเล็กทำให้ตัวเลขบิดเบือนได้)
    if no_data:
        position_label, pos_stars = "INSUFFICIENT DATA", 0
    else:
        market_score = 100 - (overall_rank - 1) / max(n_all - 1, 1) * 100
        if overall_rank == 1:
            position_label, pos_stars = "INDUSTRY LEADER", 5
        elif market_score >= 60:
            position_label, pos_stars = "STRONG COMPETITOR", 4
        elif market_score >= 40:
            position_label, pos_stars = "AVERAGE PERFORMER", 3
        elif market_score >= 20:
            position_label, pos_stars = "BELOW AVERAGE", 2
        else:
            position_label, pos_stars = "LAGGING PEER", 1

    # ---------------- STRATEGIC INVESTMENT POSITION ----------------
    with r1_c1:
        if no_data:
            position_caption = "ข้อมูลคะแนนของหุ้นตัวนี้ไม่เพียงพอสำหรับการจัดอันดับ"
        elif single_member_sector:
            position_caption = (f"กลุ่ม {ctx.stock_info.get('sector','-')} มีเพียง 1 หุ้น จึงจัดอันดับเทียบทั้ง {n_all} หุ้น: "
                                f"อันดับที่ {overall_rank} จาก Overall Score = {safe(ctx.stock_info.get('overall_score')):.1f}/100")
        else:
            position_caption = (f"อันดับที่ {sector_rank} จาก {n_sector} บริษัทในกลุ่ม {ctx.stock_info.get('sector','-')} "
                                f"จาก Overall Score = {safe(ctx.stock_info.get('overall_score')):.1f}/100")

        star_color = "#64748B" if no_data else ("#10B981" if pos_stars == 5 else ("#F59E0B" if pos_stars >= 4 else "#EF4444"))
        cup_bg = "rgba(100,116,139,0.12)" if no_data else ("rgba(16,185,129,0.12)" if pos_stars == 5 else ("rgba(245,158,11,0.12)" if pos_stars >= 4 else "rgba(239,68,68,0.12)"))

        st.markdown(f"""<div style="background:#FFFFFF; border:2px solid {star_color}; border-radius:10px; padding:14px; height:360px; box-sizing:border-box; display:flex; flex-direction:column; justify-content:space-between;">
    <div style="font-size:16px; color:#64748B; font-weight:bold; margin-bottom:8px;">STRATEGIC INVESTMENT POSITION</div>
    <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; gap:14px; flex-grow:1;">
    <div style="background:{cup_bg}; border:2px solid {star_color}; border-radius:50%; width:100px; height:100px; display:flex; align-items:center; justify-content:center; font-size:46px;">🏆</div>
    <div style="text-align:center;">
    <div style="color:{star_color}; font-size:28px; font-weight:bold;">{position_label}</div>
    <div style="color:{star_color}; font-size:24px; letter-spacing:4px; margin-top:6px;">{'★'*pos_stars}{'☆'*(5-pos_stars)}</div>
    </div>
    </div>
    </div>""", unsafe_allow_html=True)

    # ---------------- RANKING ----------------
    with r1_c2:
        pct_overall = round((overall_rank / max(n_all, 1)) * 100)
        if no_data:
            pct_overall = 0

        sector_block = (
            f"""<span style="display:inline-block; margin-top:6px; background-color:rgba(100,116,139,0.10); color:#64748B; font-size:15px; font-weight:bold; padding:3px 14px; border-radius:8px;">กลุ่มมีเพียง 1 หุ้น</span>"""
            if single_member_sector else
            ""
        )

        st.markdown(f"""<div style="background-color:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:14px; height:360px; text-align:center; display:flex; flex-direction:column; overflow:hidden; box-sizing:border-box;">
    <div style="font-size:16px; color:#64748B; font-weight:bold; margin-bottom:8px;">RANKING</div>
    <div style="background-color:{cup_bg}; border:1.5px solid {star_color}; border-radius:12px; padding:8px 8px 10px 8px; margin-bottom:10px; flex:1; display:flex; flex-direction:column; justify-content:center;">
    <span style="display:inline-block; margin:0 auto 6px auto; background-color:{star_color}; color:#FFFFFF; font-size:13px; font-weight:bold; padding:3px 16px; border-radius:14px;">ทั้งตลาด</span>
    <div style="font-size:13px; color:#64748B; margin-bottom:2px;">{n_all} หุ้นที่ติดตาม</div>
    <div><span style="font-size:32px; color:#0F172A; font-weight:800;">{rank_txt(overall_rank)}</span> <span style="font-size:14px; color:#64748B;">/ {n_all} หุ้น</span></div>
    </div>
    <div style="border-top:1px solid #E2E8F0; padding-top:10px; flex:1; display:flex; flex-direction:column; justify-content:center;">
    <span style="display:inline-block; margin:0 auto 6px auto; background-color:rgba(16,185,129,0.08); color:{star_color}; border:1.5px solid {star_color}; font-size:13px; font-weight:bold; padding:2px 16px; border-radius:14px;">ในกลุ่ม</span>
    <div style="font-size:13px; color:#64748B; margin-bottom:2px;">{ctx.stock_info.get('sector','-')}</div>
    <div><span style="font-size:32px; color:#0F172A; font-weight:800;">{rank_txt(sector_rank)}</span> <span style="font-size:14px; color:#64748B;">/ {n_sector} หุ้น</span></div>{sector_block}
    </div>
    </div>""", unsafe_allow_html=True)
    # ---------------- STRATEGIC MATRIX (ย้ายมาจาก r2_c3 เดิม + ขยายใหญ่ขึ้น) ----------------
    with r1_c3:
        matrix_df = ctx.scores_df[['ticker', 'health_score', 'overall_score']].dropna().copy()
        matrix_df.columns = ['Company', 'Business_Quality', 'Investment_Attract']

        matrix_star_color = {5: "#10B981", 4: "#F59E0B", 3: "#F59E0B", 2: "#EF4444", 1: "#EF4444"}.get(pos_stars, "#64748B")

        color_map = {t: (matrix_star_color if t == ctx.selected_ticker else "#CBD5E1") for t in matrix_df['Company']}

        fig_matrix = px.scatter(
            matrix_df, x='Business_Quality', y='Investment_Attract',
            text='Company', color='Company', color_discrete_map=color_map
        )

        fig_matrix.update_traces(textposition='top center', marker=dict(size=16, line=dict(width=1.5, color='#FFFFFF')))
        fig_matrix.add_hline(y=50, line_width=1, line_dash="dash", line_color="#CBD5E1")
        fig_matrix.add_vline(x=50, line_width=1, line_dash="dash", line_color="#CBD5E1")

        fig_matrix.add_annotation(x=25, y=95, text="💎 Hidden Gem", showarrow=False, font=dict(size=16, color="#10B981"))
        fig_matrix.add_annotation(x=80, y=95, text="🏆 Market Leader", showarrow=False, font=dict(size=16, color="#A855F7"))
        fig_matrix.add_annotation(x=25, y=10, text="⚠️ Value Trap", showarrow=False, font=dict(size=16, color="#EF4444"))
        fig_matrix.add_annotation(x=80, y=10, text="⭐ Competitive", showarrow=False, font=dict(size=15, color="#F59E0B"))

        fig_matrix.update_layout(
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#F8FAFC",
            height=360,
            margin=dict(l=20, r=20, t=35, b=20),
            title=dict(text="STRATEGIC MATRIX (All 8 Stocks)", font=dict(size=17, color="#64748B"), x=0.03, y=0.99),
            xaxis=dict(title=dict(text="Business Quality (Health Score) →", font=dict(size=13, color="#64748B")), range=[0, 100], showgrid=False, showticklabels=False),
            yaxis=dict(title=dict(text="Investment Attractiveness (Overall) →", font=dict(size=13, color="#64748B")), range=[0, 100], showgrid=False, showticklabels=False),
            showlegend=False
        )

        # ความสูงเท่ากับการ์ด STRATEGIC INVESTMENT POSITION / RANKING (360px)
        # ที่อยู่แถวเดียวกัน ป้องกันไม่ให้การ์ดนี้สูงเกินเพื่อนบ้านสองใบซ้ายมือ
        # ใช้ st.plotly_chart ตรง ๆ แทน show_chart() เพื่อไม่ให้มีปุ่ม "ขยายกราฟ"
        # โผล่ใต้กราฟ (show_chart ของ common.py แถมปุ่มนี้มาโดยอัตโนมัติ)
        st.plotly_chart(
            fig_matrix,
            use_container_width=True,
            config={"displayModeBar": True, "displaylogo": False},
        )

    st.markdown("""
    <style>

    /* Peer Comparison - Desktop */
    .peer-comparison-table {
        width: 100% !important;
        max-width: 100% !important;
        min-width: 0 !important;
        table-layout: auto !important;
        border-collapse: collapse !important;
        box-sizing: border-box !important;
    }

    .peer-comparison-table th,
    .peer-comparison-table td {
        vertical-align: middle !important;
        box-sizing: border-box !important;
        white-space: normal !important;
        word-break: normal !important;
        overflow-wrap: normal !important;
    }

    .peer-comparison-table th {
        padding: 6px 4px !important;
        line-height: 1.2 !important;
    }

    .peer-comparison-table td {
        padding: 7px 4px !important;
        line-height: 1.25 !important;
    }

    .peer-comparison-table td span {
        display: inline-block !important;
        max-width: 100% !important;
        line-height: 1.2 !important;
        white-space: normal !important;
    }


    /* Mobile */
    @media (max-width: 768px) {

        /* Peer Comparison */
        .peer-comparison-card {
            width: 100% !important;
            max-width: 100% !important;
            min-width: 0 !important;
            height: auto !important;
            min-height: 0 !important;
            box-sizing: border-box !important;
            overflow: visible !important;
        }

        .peer-comparison-table {
            width: 100% !important;
            max-width: 100% !important;
            min-width: 0 !important;
            table-layout: fixed !important;
            font-size: 10px !important;
            box-sizing: border-box !important;
        }

        .peer-comparison-table th,
        .peer-comparison-table td {
            min-width: 0 !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
            white-space: normal !important;
            word-break: normal !important;
            overflow-wrap: break-word !important;
        }

        .peer-comparison-table th {
            font-size: 9.5px !important;
            line-height: 1.15 !important;
            padding: 5px 2px !important;
        }

        .peer-comparison-table td {
            font-size: 10px !important;
            line-height: 1.2 !important;
            padding: 6px 2px !important;
        }

        .peer-comparison-table td span {
            display: inline-block !important;
            max-width: 100% !important;
            white-space: normal !important;
            word-break: normal !important;
            overflow-wrap: break-word !important;
            line-height: 1.2 !important;
        }


        /* Dimension Percentile */
        .dimension-percentile-card {
            width: 100% !important;
            max-width: 100% !important;
            min-width: 0 !important;
            height: auto !important;
            min-height: 0 !important;
            box-sizing: border-box !important;
            overflow: visible !important;
        }

        .industry-dimension-grid {
            grid-template-columns: 1fr !important;
            width: 100% !important;
            max-width: 100% !important;
            min-width: 0 !important;
            box-sizing: border-box !important;
            gap: 8px !important;
        }

        .industry-dimension-grid > div {
            width: 100% !important;
            max-width: 100% !important;
            min-width: 0 !important;
            box-sizing: border-box !important;
        }

    }

    </style>
    """, unsafe_allow_html=True)

    # แถว 2 เหลือ 2 คอลัมน์ (Strategic Matrix ที่เคยอยู่ตำแหน่งที่ 3 ย้ายขึ้นไป r1_c3 แล้ว)
    r2_c1, r2_c2 = st.columns([2.0, 1.3])

    # ---------------- DIMENSION PERCENTILE RANK ----------------
    with r2_c1:
        def calc_pct(df, col):
            s = df[col].rank(pct=True)
            match = df['ticker'] == ctx.selected_ticker
            if not match.any() or pd.isna(s[match].values[0]):
                return None
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
                if col == 'revenue_growth_yoy' and pd.isna(ctx.stock_info.get('revenue_growth_yoy')):
                    pct = None
                else:
                    pct = calc_pct(df, col)
                result.append((label, pct, color))
            return result

        dims_market = build_dims(ctx.scores_df)

        def dim_pct_card(label, pct, color):
            if pct is None:
                return f"""<div style="background:#0F172A; padding:6px 4px; border-radius:6px; border:1px solid #1E293B;">
    <div style="color:#94A3B8; font-size:12px;">{label}</div><div style="color:#64748B; font-size:15px; font-weight:bold; margin:2px 0;">N/A</div>
    <div style="color:#64748B; font-size:12px;">No data</div></div>"""
            tier = "Excellent" if pct <= 20 else ("Good" if pct <= 45 else ("Fair" if pct <= 70 else "Weak"))
            return f"""<div style="background:#F8FAFC; padding:6px 4px; border-radius:6px; border:1px solid #E2E8F0;">
    <div style="color:#64748B; font-size:12px;">{label}</div><div style="color:{color}; font-size:16px; font-weight:bold; margin:2px 0;">Top {max(pct,1)}%</div>
    <div style="color:{color}; font-size:12px;">{tier}</div></div>"""

        if single_member_sector:
            sector_section = f"""<div style="background:rgba(100,116,139,0.06); border:1px dashed #CBD5E1; border-radius:8px; padding:10px; text-align:center; margin-bottom:6px;">
    <div style="color:#64748B; font-size:12px; line-height:1.3;">กลุ่ม <b>{ctx.stock_info.get('sector','-')}</b> มีเพียง 1 หุ้น จึงไม่สามารถเปรียบเทียบ percentile ภายในกลุ่มได้อย่างมีความหมาย</div>
    </div>"""
        else:
            dims_sector = build_dims(ctx.sector_peers)
            sector_section = f"""<div style="font-size:12px; color:#475569; margin-bottom:6px;">เปรียบเทียบกับกลุ่มอุตสาหกรรม {ctx.stock_info.get('sector','-')} ({n_sector} หุ้น)</div>
    <div class="industry-dimension-grid" style="display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:6px; text-align:center; margin-bottom:6px; width:100%; min-width:0; max-width:100%; box-sizing:border-box;">
    {''.join([dim_pct_card(l, p, c) for l, p, c in dims_sector])}
    </div>"""

        market_section = f"""<div style="font-size:12px; color:#475569; margin-bottom:6px;">เปรียบเทียบกับหุ้นทั้ง {n_all} ตัว</div>
    <div class="industry-dimension-grid" style="display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:6px; text-align:center; margin-bottom:6px; width:100%; min-width:0; max-width:100%; box-sizing:border-box;">
    {''.join([dim_pct_card(l, p, c) for l, p, c in dims_market])}
    </div>"""

        # PATCH NOTE 6: เลิก fix height ที่การ์ดนี้ (440px ยังไม่พอในบางเคส ตัดเนื้อหา
        # อีกครั้ง) เปลี่ยนเป็น height:auto + overflow:visible ให้การ์ดสูงตามเนื้อหา
        # จริงเสมอ ไม่มีการตัดอีกต่อไป ไม่ว่าจำนวนดาว/ความยาว sector_section จะเป็นเท่าไหร่
        st.markdown(f"""<div class="dimension-percentile-card" style="background-color:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:14px; height:auto; overflow:visible; display:flex; flex-direction:column; justify-content:flex-start; box-sizing:border-box;">
    <div>
    <div style="font-size:15px; color:#64748B; font-weight:bold; margin-bottom:8px;">DIMENSION PERCENTILE RANK</div>
    {market_section}
    </div>
    <div style="border-top:1px dashed #CBD5E1; margin-bottom:8px;"></div>
    <div>
    {sector_section}
    </div>
    </div>""", unsafe_allow_html=True)

    # ---------------- RADAR: STOCK vs SECTOR AVG ----------------
    with r2_c2:
        cats = ['Health', 'Valuation', 'Timing', 'AI Pred.', 'Risk', 'Industry']

        stock_vals = [
            safe(ctx.stock_info.get('health_score')),
            safe(ctx.stock_info.get('valuation_score')),
            safe(ctx.stock_info.get('timing_score')),
            safe(ctx.stock_info.get('ai_score')),
            safe(ctx.stock_info.get('risk_score')),
            safe(ctx.stock_info.get('industry_score'))
        ]

        sector_avg_vals = [
            ctx.sector_peers['health_score'].mean(),
            ctx.sector_peers['valuation_score'].mean(),
            ctx.sector_peers['timing_score'].mean(),
            ctx.sector_peers['ai_score'].mean(),
            ctx.sector_peers['risk_score'].mean(),
            ctx.sector_peers['industry_score'].mean()
        ]

        radar_color = {5: "#10B981", 4: "#F59E0B", 3: "#F59E0B", 2: "#EF4444", 1: "#EF4444"}.get(pos_stars, "#64748B")
        fill_color = {
            5: "rgba(16,185,129,0.25)", 4: "rgba(245,158,11,0.25)", 3: "rgba(245,158,11,0.25)",
            2: "rgba(239,68,68,0.25)", 1: "rgba(239,68,68,0.25)"
        }.get(pos_stars, "rgba(100,116,139,0.20)")

        fig_radar = go.Figure()

        fig_radar.add_trace(go.Scatterpolar(
            r=stock_vals, theta=cats, fill='toself',
            fillcolor=fill_color, line=dict(color=radar_color, width=2), name=ctx.selected_ticker
        ))
        fig_radar.add_trace(go.Scatterpolar(
            r=sector_avg_vals, theta=cats, line=dict(color='#94A3B8', width=1.5, dash='dash'), name='Sector Avg'
        ))

        # PATCH NOTE 8 (bugfix): PATCH NOTE 7 หด polar.domain มากไป ทำให้ตัวกราฟ
        # วงกลมดูเล็กเกินไป เหลือพื้นที่ว่างเยอะรอบขอบ (โดยเฉพาะช่วงบนใต้ title)
        # แก้โดยขยาย domain ให้กราฟใหญ่ขึ้นอีกครั้ง แต่ยังเว้นระยะพอให้ label ไม่ชน
        # ขอบกรอบเหมือนที่แก้ใน PATCH NOTE 7 (กรอบนอก 470px เท่าเดิม)
        fig_radar.update_layout(
            polar=dict(
                domain=dict(x=[0.08, 0.92], y=[0.04, 0.96]),
                radialaxis=dict(visible=True, range=[0, 100], showticklabels=False, linecolor="#CBD5E1", gridcolor="#E2E8F0"),
                angularaxis=dict(linecolor="#CBD5E1", gridcolor="#E2E8F0", tickfont=dict(size=12, color="#64748B"))
            ),
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            height=470,
            margin=dict(l=45, r=45, t=40, b=25),
            title=dict(text="RADAR: STOCK vs SECTOR AVG", font=dict(size=15, color="#64748B"), x=0.05, y=0.99),
            legend=dict(orientation="h", yanchor="bottom", y=1.04, xanchor="right", x=1, font=dict(size=13, color="#475569"))
        )

        # ใช้ st.plotly_chart ตรง ๆ แทน show_chart() เพื่อไม่ให้มีปุ่ม "ขยายกราฟ" โผล่ใต้กราฟ
        st.plotly_chart(
            fig_radar,
            use_container_width=True,
            config={"displayModeBar": True, "displaylogo": False},
        )

    # ---------------- PEER COMPARISON (เต็มความกว้าง แทนที่ตำแหน่ง Dimension Percentile Rank เดิม) ----------------
    peers_sorted = ctx.sector_peers.sort_values('overall_score', ascending=False)

    def badge(val, thresholds, labels, colors):
        for th, lab, col in zip(thresholds, labels, colors):
            if val >= th:
                return f'<span style="color:{col}; font-weight:bold;">{lab}</span>'
        return f'<span style="color:{colors[-1]};">{labels[-1]}</span>'

    rows_html = ""

    for _, p in peers_sorted.iterrows():
        is_sel = p['ticker'] == ctx.selected_ticker

        star_n = pos_stars if is_sel else min(5, max(1, round(safe(p['overall_score']) / 20)))

        row_star_color = (
            "#10B981" if star_n == 5
            else "#F59E0B" if star_n >= 4
            else "#EF4444"
        )

        row_bg = (
            "background:rgba(16,185,129,0.10);" if is_sel and star_n == 5
            else "background:rgba(245,158,11,0.10);" if is_sel and star_n >= 4
            else "background:rgba(239,68,68,0.10);" if is_sel
            else ""
        )

        health_b = badge(
            p['health_score'], [70, 45, 0],
            ["Excellent", "Good", "Weak"], ["#10B981", "#3B82F6", "#EF4444"]
        )

        val_b = "N/A" if pd.isna(p['margin_of_safety']) else (
            "Undervalued" if p['margin_of_safety'] > 10 else
            ("Overvalued" if p['margin_of_safety'] < -10 else "Fair Value")
        )
        val_c = (
            "#10B981" if not pd.isna(p['margin_of_safety']) and p['margin_of_safety'] > 10
            else "#EF4444" if not pd.isna(p['margin_of_safety']) and p['margin_of_safety'] < -10
            else "#64748B"
        )

        timing_b = badge(
            p['timing_score'], [65, 45, 0],
            ["Good Entry", "Neutral", "Bad Entry"], ["#10B981", "#F59E0B", "#EF4444"]
        )

        # FIX: Neutral เดิมเป็นสีเทา (#64748B) เปลี่ยนเป็นเหลือง (#F59E0B) ให้เห็นชัดว่าอยู่โซนกลาง
        ai_b = badge(
            p['ai_score'], [65, 45, 0],
            ["Bullish", "Neutral", "Bearish"], ["#10B981", "#F59E0B", "#EF4444"]
        )

        risk_b = "Low" if p['risk_score'] >= 65 else ("Medium" if p['risk_score'] >= 40 else "High")
        risk_c = (
            "#10B981" if p['risk_score'] >= 65
            else "#F59E0B" if p['risk_score'] >= 40
            else "#EF4444"
        )

        name_disp = f"⭐ {p['ticker']}" if is_sel else p['ticker']

        # ใช้การจัด Style แบบ Light Theme ตามทีม Layout เป็นหลัก
        name_c = row_star_color if is_sel else "#0F172A"

        rows_html += f"""<tr style="border-bottom:1px solid #E2E8F0; {row_bg}">
    <td style="text-align:left; padding:6px 0; color:{name_c}; font-weight:bold; min-width:0; overflow-wrap:anywhere; word-break:break-word;">{name_disp}</td>
    <td style="padding:7px 4px;">{health_b}</td>
    <td style="padding:7px 4px;"><span style="color:{val_c};">{val_b}</span></td>
    <td style="padding:7px 4px;">{timing_b}</td>
    <td style="padding:7px 4px;">{ai_b}</td>
    <td style="padding:7px 4px;"><span style="color:{risk_c};">{risk_b}</span></td>
    <td style="color:{row_star_color}; letter-spacing:0.5px; font-size:15px; white-space:nowrap; overflow:hidden; text-overflow:clip;">{'★'*star_n}{'☆'*(5-star_n)}</td>
    </tr>"""

    peer_html = f"""
<div class="peer-comparison-card" style="background-color:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:14px; height:auto; width:100%; max-width:100%; min-width:0; box-sizing:border-box;">
    <div style="font-size:16px; color:#64748B; font-weight:bold; margin-bottom:6px;">
        PEER COMPARISON — {ctx.stock_info.get('sector','-')} ({n_sector} หุ้น)
    </div>

    <table class="peer-comparison-table" style="width:100%; max-width:100%; min-width:0; text-align:center; font-size:15px; color:#475569; border-collapse:collapse; box-sizing:border-box;">
        <tr style="border-bottom:1px solid #E2E8F0; color:#64748B; font-size:14px;">
            <th style="text-align:left; padding:5px 0;">Company</th>
            <th>Health</th>
            <th>Fair Value</th>
            <th>Entry Timing</th>
            <th>AI Prediction</th>
            <th>Risk</th>
            <th>Overall</th>
        </tr>

        {rows_html}

    </table>

    <div style="font-size:12px; color:#64748B; margin-top:8px; line-height:1.3;">
        *จัดอันดับจาก Overall Score ที่คำนวณจริงจากข้อมูลใน cis_summary_scores
    </div>
</div>
"""

    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
    st.html(peer_html)

    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
    r3_c1, r3_c2 = st.columns([1.3, 1.3])

    # ---------------- COMPETITIVE ADVANTAGE ----------------
    with r3_c1:
        compare_df = ctx.scores_df if single_member_sector else ctx.sector_peers
        strengths_ib, weaknesses_ib = [], []

        if ctx.stock_info['health_score'] > compare_df['health_score'].mean():
            strengths_ib.append("Health Score สูงกว่าค่าเฉลี่ย")

        if ctx.stock_info['ai_score'] > compare_df['ai_score'].mean():
            strengths_ib.append("AI Prediction Score สูงกว่าค่าเฉลี่ย")

        if safe(ctx.stock_info.get('revenue_growth_yoy')) > 0:
            strengths_ib.append(f"รายได้เติบโต {safe(ctx.stock_info.get('revenue_growth_yoy')):.1f}% YoY")

        if not strengths_ib:
            strengths_ib.append("ผลประกอบการยังอยู่ระหว่างพัฒนาเทียบกลุ่ม")

        if ctx.stock_info['valuation_score'] < compare_df['valuation_score'].mean():
            weaknesses_ib.append("Valuation แพงกว่าค่าเฉลี่ย")

        if ctx.stock_info['risk_score'] < compare_df['risk_score'].mean():
            weaknesses_ib.append("ความเสี่ยงสูงกว่าค่าเฉลี่ย")

        if ctx.stock_info['health_score'] < compare_df['health_score'].mean():
            weaknesses_ib.append("Health Score ต่ำกว่าค่าเฉลี่ย")

        if ctx.stock_info['ai_score'] < compare_df['ai_score'].mean():
            weaknesses_ib.append("AI Prediction Score ต่ำกว่าค่าเฉลี่ย")

        if not weaknesses_ib:
            weaknesses_ib.append("ไม่พบจุดอ่อนเชิงเปรียบเทียบที่ชัดเจน")

        st.markdown(f"""<div style="background-color:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:14px; height:220px;">
    <div style="font-size:16px; color:#64748B; font-weight:bold; margin-bottom:6px;">COMPETITIVE ADVANTAGE</div>
    <div style="font-size:15px; color:#10B981; font-weight:bold; margin-bottom:2px;">STRENGTHS</div>
    <ul style="color:#475569; font-size:15px; line-height:1.4; padding-left:14px; margin:0 0 6px 0;">{''.join([f'<li>{s}</li>' for s in strengths_ib])}</ul>
    <div style="font-size:15px; color:#EF4444; font-weight:bold; margin-bottom:2px;">WEAKNESSES / RISKS</div>
    <ul style="color:#475569; font-size:15px; line-height:1.4; padding-left:14px; margin:0;">{''.join([f'<li>{w}</li>' for w in weaknesses_ib])}</ul>
    </div>""", unsafe_allow_html=True)

    # ---------------- EXPLAINABLE AI SUMMARY ----------------
    with r3_c2:
        compare_desc = (
            f"เทียบกับทั้ง {n_all} หุ้นที่ติดตาม (กลุ่มมีตัวเดียว)"
            if single_member_sector
            else "เทียบกับบริษัทในกลุ่มเดียวกัน"
        )
        avg_label = "Overall avg" if single_member_sector else "Sector avg"

        def _metric_row(label, col):
            v = ctx.stock_info.get(col)
            avg = compare_df[col].mean()
            if pd.isna(v):
                return f'<div><span style="color:#64748B;">–</span> {label}: N/A</div>'
            ok = v >= avg
            icon = '<span style="color:#10B981;">✔</span>' if ok else '<span style="color:#EF4444;">✘</span>'
            return f'<div>{icon} {label}: {v:.1f} ({avg_label} {avg:.1f})</div>'

        metric_rows = "".join(_metric_row(l, c) for l, c in [
            ("Health Score", 'health_score'), ("Valuation Score", 'valuation_score'),
            ("AI Prediction Score", 'ai_score'), ("Risk Score", 'risk_score')])

        if no_data:
            rank_sentence = "มีข้อมูลไม่เพียงพอสำหรับการจัดอันดับ"
        elif single_member_sector:
            rank_sentence = f"อยู่อันดับที่ <b>{overall_rank}</b> จาก {n_all} หุ้นที่ติดตาม (กลุ่ม {ctx.stock_info.get('sector','-')} มีหุ้นตัวเดียว)"
        else:
            rank_sentence = f"อยู่อันดับที่ <b>{sector_rank}</b> จาก {n_sector} บริษัทในกลุ่ม {ctx.stock_info.get('sector','-')}"

        st.markdown(f"""<div style="background-color:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:14px; height:220px;">
    <div style="font-size:16px; color:#64748B; font-weight:bold; margin-bottom:6px;">EXPLAINABLE AI SUMMARY</div>
    <p style="color:#475569; font-size:15px; line-height:1.4; margin:0 0 8px 0;">
    <b>{ctx.selected_ticker}</b> {rank_sentence} (Overall Score {safe(ctx.stock_info.get('overall_score')):.1f}/100) {compare_desc}:</p>
    <div style="color:#475569; font-size:15px; line-height:1.5;">
    {metric_rows}
    </div></div>""", unsafe_allow_html=True)

    render_nav_footer("m7", prev_page=None, next_page=" Stock Overview", show_home=False)
