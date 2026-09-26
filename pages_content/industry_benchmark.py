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
    overall_rank_raw
