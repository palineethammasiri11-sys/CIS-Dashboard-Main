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

=== CHANGELOG (v7 — ปรับดีไซน์ KPI/AI SIGNAL ใหม่ตาม mockup ทีมออกแบบ) ===
- แทนที่การ์ด KPI แบบเดิม (ตัวหนังสือ label ภาษาอังกฤษ ไม่มีไอคอน) ด้วย _stat_card ใหม่:
  มีไอคอนวงกลมสี + label ภาษาไทย ตามภาพ mockup ที่ได้รับ (ราคาปัจจุบัน / ทิศทาง / โอกาส.../ คำแนะนำ)
- เปลี่ยน gauge ความน่าจะเป็นจาก SVG semi-circle เดิม เป็นวงแหวนเต็มวง (conic-gradient) ตรงกลางมีตัวเลข
  พร้อมแถบ slider แนวนอน "ขาลง ... ขาขึ้น" ประกอบ ตามภาพ
- เปลี่ยนหัวข้อ section จาก "📈 PREDICTION" เป็น "🧠 AI SIGNAL" พร้อม subtitle "สัญญาณจากโมเดล AI"
- การ์ด "คำแนะนำ" (RECOMMENDATION): เมื่อ reliability_low = True จะโชว์ "CAUTION" สีแดงแทนสัญญาณจริง
  (แทนการต่อท้าย "⚠" แบบเดิม) เพื่อไม่ให้ผู้ใช้เห็นคำแนะนำ BUY/SELL ที่โมเดลไม่มั่นใจปนอยู่ด้วยกัน
- ตัด _kpi_card / _kpi_sub / _metric_cell เดิมที่ไม่ได้ใช้แล้วออก (ถูกแทนที่ด้วย _stat_card ทั้งหมด)
- ส่วน FORECAST และ MODEL EXPLANATION ด้านล่างไม่ถูกแก้ไข (ไม่มีอยู่ในภาพ mockup ที่ได้รับ) — โครง/ตรรกะ
  เดิมทั้งหมดยังเหมือน v6 ทุกประการ

=== CHANGELOG (v8 — ยืนยันตาม mockup ที่ทีมส่งมา (ก่อน/หลัง) — เปลี่ยน label กลับเป็นสลับตามทิศทาง ===
- v7 เคยเปลี่ยน label การ์ดโอกาส + label ใต้ gauge วงกลม ให้ "คงที่" (โอกาสที่ราคาจะปรับขึ้นเสมอ)
  เพราะสังเกตว่า label สลับทิศทางจะดูขัดกับตัวเลข prob_up เวลาโมเดลทำนายขาลง
- ทีมยืนยันด้วยภาพ before/after ว่าต้องการ label แบบ "สลับตามทิศทางที่ทำนาย" ตรงตาม mockup เป๊ะๆ
  (การ์ด 3: "โอกาสที่ราคาจะปรับขึ้น" / "โอกาสที่ราคาจะปรับลดลง" ตาม prob_up, และ label ใต้ gauge
  วงกลมใน AI SIGNAL: "โอกาส" + direction_th) จึงเปลี่ยนกลับเป็นแบบสลับใน v8 นี้
- ค่าตัวเลขที่โชว์ (prob_up) และตัวแปรอื่นทั้งหมดยังไม่ถูกแก้ไข เหมือน v6/v7 ทุกประการ — เปลี่ยนแค่
  ข้อความ label ให้ตรงกับ mockup เท่านั้น

=== MERGE NOTE (รวม Branch main x Copy-ทีมออกแบบ) ===
- ธีม/เลย์เอาต์ทั้งหมดยึดตามทีมออกแบบ (การ์ดพื้นขาว) ปรับตาม mockup ใหม่ใน v7 ด้านบน
- Logic การซ่อนตัวเลข accuracy/baseline และการเตือนความน่าเชื่อถือของโมเดล (reliability_low,
  จุดสัญญาณ, กล่องเตือนสีแดง) ยึดตาม main ทั้งหมด ไม่มีการเปลี่ยนแปลง
- ตัดส่วน "MODEL PERFORMANCE" และ expander "Model & Data Detail" ออกตามมติ main (ไม่โชว์ตัวเลขดิบ)
- ปุ่มเปลี่ยนหน้าด้านล่างใช้ label แบบไม่มี emoji ตามทีมออกแบบ
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
TEAL = "#0EA5A6"
MUTED = "#64748B"


def _hex_to_rgba(hex_color, alpha):
    hex_color = hex_color.lstrip('#')
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _section_title(text):
    return f"""<div style="background-color:#FFFFFF; border:1px solid #D9E2EC; border-radius:12px 12px 0 0; padding:14px 18px 2px 18px;">
<div><span style="font-size:13px; font-weight:bold; color:{MUTED}; letter-spacing:0.5px;">{text}</span></div></div>"""


# ============================================================
# SVG ICONS (inline, สีปรับได้ผ่านพารามิเตอร์ — ไม่พึ่งพา external library
# เพราะไฟล์นี้ inject เป็น HTML string ผ่าน st.markdown ไม่ใช่ React)
# ============================================================
def _icon_bar_chart(color):
    return (
        f'<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{color}" '
        f'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">'
        f'<line x1="4" y1="20" x2="4" y2="12"></line>'
        f'<line x1="12" y1="20" x2="12" y2="6"></line>'
        f'<line x1="20" y1="20" x2="20" y2="15"></line></svg>'
    )


def _icon_arrow(direction, color="#FFFFFF"):
    if direction == "down":
        path = '<line x1="12" y1="5" x2="12" y2="19"></line><polyline points="19 12 12 19 5 12"></polyline>'
    else:
        path = '<line x1="12" y1="19" x2="12" y2="5"></line><polyline points="5 12 12 5 19 12"></polyline>'
    return (
        f'<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="{color}" '
        f'stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">{path}</svg>'
    )


def _icon_pie(color):
    return (
        f'<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="{color}" '
        f'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
        f'<path d="M21.21 15.89A10 10 0 1 1 8 2.83"></path>'
        f'<path d="M22 12A10 10 0 0 0 12 2v10z"></path></svg>'
    )


def _icon_shield(color="#FFFFFF"):
    return (
        f'<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="{color}" '
        f'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
        f'<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>'
    )


def _icon_bulb(color):
    return (
        f'<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="{color}" '
        f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        f'<path d="M9 18h6"></path><path d="M10 22h4"></path>'
        f'<path d="M12 2a7 7 0 0 0-4 12.7V17h8v-2.3A7 7 0 0 0 12 2z"></path></svg>'
    )


def _sparkline(color):
    return (
        f'<svg width="82" height="30" viewBox="0 0 82 30" style="opacity:.28;">'
        f'<path d="M0 10 Q 10 2, 20 12 T 40 15 T 58 6 T 82 20" fill="none" stroke="{color}" stroke-width="2"/></svg>'
    )


def _stat_card(icon_html, icon_bg, label, value_html, value_color="#0F172A", sub_html="", decorative_html=""):
    """การ์ด KPI ใบเดียว แบบใหม่ (ไอคอนวงกลม + label ไทย + ตัวเลขใหญ่ + sub บรรทัดล่าง)"""
    return f"""
    <div style="background:#FFFFFF; border:1px solid #D9E2EC; border-radius:12px; padding:16px 18px;
                height:122px; box-sizing:border-box; position:relative; overflow:hidden;
                display:flex; flex-direction:column; justify-content:center;">
        {f'<div style="position:absolute; right:8px; top:50%; transform:translateY(-50%);">{decorative_html}</div>' if decorative_html else ''}
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px; position:relative; z-index:1;">
            <div style="width:30px; height:30px; border-radius:50%; background:{icon_bg}; display:flex;
                        align-items:center; justify-content:center; flex-shrink:0;">
                {icon_html}
            </div>
            <span style="font-size:12.5px; font-weight:700; color:{MUTED};">{label}</span>
        </div>
        <div style="font-size:25px; font-weight:800; color:{value_color}; line-height:1.15; position:relative; z-index:1;">
            {value_html}
        </div>
        {f'<div style="margin-top:6px; position:relative; z-index:1;">{sub_html}</div>' if sub_html else ''}
    </div>
    """


def render(ctx):
    st.markdown(f"""<div style="margin-bottom:20px;">
<div style="font-size:26px; font-weight:700; color:#0F172A; letter-spacing:0.3px;">AI PREDICTION</div>
<div style="font-size:16px; color:#64748B; margin-top:4px;">ประเมินทิศทางราคาหุ้นในอีก 10 วันทำการด้วยโมเดล Random Forest</div>
</div>""", unsafe_allow_html=True)

    # ============================================================
    # ถ้าเป็นค่า fallback (ข้อมูลไม่พอเทรนโมเดลจริง) ห้ามแสดง KPI/กราฟเหมือนเป็นผลจริง
    # ============================================================
    if ctx.stock_info.get('is_fallback', False):
        st.markdown(f"""<div style="background:rgba(239,68,68,0.1); border:1px solid {RED}; border-radius:12px; padding:28px; text-align:center;">
<div style="font-size:21px; font-weight:bold; color:{RED}; margin-bottom:10px;">⚠ ข้อมูลไม่เพียงพอสำหรับ {ctx.selected_ticker}</div>
<p style="font-size:15px; color:#334155; line-height:1.65; margin:0; max-width:640px; margin:0 auto;">
หุ้นตัวนี้มีข้อมูลราคาย้อนหลังไม่พอสำหรับเทรนโมเดล Random Forest จริง (ต้องการอย่างน้อย Train 50 แถว และ Test 20 แถว)
ตัวเลขที่เคยแสดงในหน้านี้เป็นเพียง<b>ค่าตั้งต้นสำรอง (placeholder)</b> ไม่ใช่ผลจากการเทรนโมเดลจริงแต่อย่างใด
จึง<b style="color:{RED};">ไม่ควรใช้ประกอบการตัดสินใจลงทุน</b></p>
</div>""", unsafe_allow_html=True)
        render_nav_footer("m4", prev_page=" Entry Timing", next_page=" Risk Analysis")
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

    # การ์ด/badge คำแนะนำ: ถ้าความน่าเชื่อถือต่ำ ให้โชว์ "CAUTION" สีแดงแทนสัญญาณจริง
    # (ไม่ปนคำแนะนำ BUY/SELL ที่โมเดลเองก็ไม่มั่นใจเข้ากับสัญญาณที่น่าเชื่อถือ)
    if reliability_low:
        signal_display = "CAUTION"
        signal_color = RED
    else:
        signal_display = signal
        signal_color = status_color

    # ============================================================
    # 1) OVERVIEW — แถบ KPI ใหม่ (ไอคอน + label ไทย ตาม mockup)
    # ============================================================

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        st.markdown(
            _stat_card(
                icon_html=_icon_bar_chart(TEAL),
                icon_bg=_hex_to_rgba(TEAL, 0.14),
                label="ราคาปัจจุบัน (บาท)",
                value_html=f"{ctx.current_price:,.2f}",
                sub_html=(
                    f'<span style="color:{ctx.change_color}; font-weight:700; font-size:12.5px;">'
                    f'{ctx.arrow_sign} {ctx.change_val:+.2f} ({ctx.change_pct:+.2f}%)</span>'
                    f'<div style="color:{MUTED}; font-size:11.5px; margin-top:1px;">(vs. previous day)</div>'
                ),
            ),
            unsafe_allow_html=True
        )

    with k2:
        st.markdown(
            _stat_card(
                icon_html=_icon_arrow("down" if prob_up < 50 else "up"),
                icon_bg=status_color,
                label="ทิศทาง (10D)",
                value_html=f'<span style="color:{status_color};">{direction_th}</span>',
                sub_html=f'<span style="color:{MUTED}; font-size:12px;">10 Trading Days</span>',
                decorative_html=_sparkline(status_color),
            ),
            unsafe_allow_html=True
        )

    with k3:
        prob_card_label = "โอกาสที่ราคาจะปรับขึ้น" if prob_up >= 50 else "โอกาสที่ราคาจะปรับลดลง"
        st.markdown(
            _stat_card(
                icon_html=_icon_pie(BLUE),
                icon_bg=_hex_to_rgba(BLUE, 0.14),
                label=prob_card_label,
                value_html=f"{prob_up:.0f}%",
                sub_html=(
                    f'<div style="font-size:11.5px; color:{MUTED}; margin-bottom:3px;">Down: {down_prob:.0f}%</div>'
                    f'<div style="background:#E2E8F0; height:6px; border-radius:3px; overflow:hidden;">'
                    f'<div style="background:{status_color}; width:{prob_up:.0f}%; height:100%;"></div></div>'
                ),
            ),
            unsafe_allow_html=True
        )

    with k4:
        st.markdown(
            _stat_card(
                icon_html=_icon_shield(),
                icon_bg=signal_color,
                label="คำแนะนำ",
                value_html=signal_display,
                value_color=signal_color,
            ),
            unsafe_allow_html=True
        )

    st.markdown("<div style='margin-top:22px;'></div>", unsafe_allow_html=True)

    # ============================================================
    # 2) AI SIGNAL — gauge วงแหวนเต็มวง + slider + กล่องอธิบาย (ไม่มีตัวเลข accuracy/baseline)
    # ============================================================

    st.markdown(
        f"""<div style="background:#FFFFFF; border:1px solid #D9E2EC; border-radius:12px 12px 0 0; padding:16px 20px 6px 20px;">
<div style="display:flex; align-items:center; gap:8px;">
<span style="font-size:19px;">🧠</span>
<span style="font-size:15px; font-weight:800; color:#0F172A;">AI SIGNAL</span>
</div>
<div style="font-size:12.5px; color:{MUTED}; margin-top:2px; margin-left:27px;">สัญญาณจากโมเดล AI</div>
</div>""",
        unsafe_allow_html=True
    )

    gauge_pct = min(100, max(0, prob_up))

    warn_line = ""
    if reliability_low:
        warn_line = (
            f'<div style="font-size:12px; color:{RED}; background:rgba(239,68,68,0.1); border:1px solid {RED}; '
            f'border-radius:8px; padding:9px 13px; margin-top:12px; line-height:1.55; margin-left:30px;">'
            f'⚠ ความแม่นยำของโมเดลสำหรับหุ้นตัวนี้อยู่ในเกณฑ์ที่ควรใช้ด้วยความระมัดระวังเป็นพิเศษ</div>'
        )

    status_badge = (
        f'<span style="background:{_hex_to_rgba(signal_color, 0.12)}; color:{signal_color}; font-size:11.5px; '
        f'font-weight:800; padding:3px 10px; border-radius:20px; white-space:nowrap; flex-shrink:0;">{signal_display}</span>'
    )

    st.markdown(
        f"""<div style="background:#FFFFFF; border:1px solid #D9E2EC; border-top:none; border-radius:0 0 12px 12px; padding:20px;">
<div style="display:flex; gap:20px; flex-wrap:wrap; align-items:stretch;">

<div style="flex:1 1 320px; min-width:280px; background:#F8FAFC; border:1px solid #D9E2EC; border-radius:12px; padding:22px;
            display:flex; align-items:center; gap:22px; flex-wrap:wrap; justify-content:center;">

<div style="position:relative; width:150px; height:150px; flex-shrink:0;">
<div style="width:150px; height:150px; border-radius:50%;
            background:conic-gradient({status_color} 0% {gauge_pct:.0f}%, #E2E8F0 {gauge_pct:.0f}% 100%);
            display:flex; align-items:center; justify-content:center;">
<div style="width:110px; height:110px; border-radius:50%; background:#F8FAFC; display:flex; flex-direction:column;
            align-items:center; justify-content:center;">
<span style="font-size:26px; font-weight:800; color:#0F172A;">{prob_up:.0f}%</span>
<span style="font-size:11px; color:{MUTED}; margin-top:2px; text-align:center;">โอกาส{direction_th}</span>
</div>
</div>
</div>

<div style="flex:1 1 160px; min-width:160px;">
<div style="display:flex; justify-content:space-between; font-size:12.5px; font-weight:700; color:{MUTED}; margin-bottom:5px;">
<span>ขาลง</span><span>ขาขึ้น</span>
</div>
<div style="background:#E2E8F0; height:8px; border-radius:4px; overflow:hidden;">
<div style="background:{status_color}; width:{prob_up:.0f}%; height:100%;"></div>
</div>
<div style="display:flex; justify-content:space-between; font-size:11px; color:{MUTED}; margin-top:4px;">
<span>0%</span><span>100%</span>
</div>
</div>

</div>

<div style="flex:1 1 320px; min-width:280px; background:#F3F7FB; border:1px solid #C7D5E3; border-left:4px solid {status_color};
            border-radius:12px; padding:20px 24px; display:flex; flex-direction:column; justify-content:center;">
<div style="display:flex; align-items:flex-start; justify-content:space-between; gap:10px;">
<div style="display:flex; align-items:flex-start; gap:10px;">
<div style="flex-shrink:0; margin-top:2px;">{_icon_bulb(BLUE)}</div>
<div style="font-size:14px; color:#334155; line-height:1.7;">
โมเดล Random Forest ประเมินว่า <b>{ctx.selected_ticker}</b> มีโอกาส
<b style="color:{status_color};">{direction_th}</b>
<b>{prob_up:.0f}%</b> ในอีก 10 วันทำการ
</div>
</div>
{status_badge}
</div>
<div style="font-size:12px; color:{MUTED}; line-height:1.6; margin-top:10px; margin-left:30px;">
โดยมีปัจจัยหลักจากความผันผวนของราคาและตัวชี้วัดทางเทคนิคบางตัว ที่ส่งผลต่อทิศทางราคาในระยะสั้น
</div>
<div style="display:flex; gap:8px; margin-top:14px; flex-wrap:wrap; margin-left:30px;">
<div style="background:#FFFFFF; border:1px solid #D9E2EC; border-radius:8px; padding:5px 11px; font-size:12px; color:#334155;">
🌲 Model: Random Forest
</div>
<div style="background:#FFFFFF; border:1px solid #D9E2EC; border-radius:8px; padding:5px 11px; font-size:12px; color:#334155;">
📅 Horizon: 10 Trading Days
</div>
</div>
<div style="font-size:11px; color:{MUTED}; line-height:1.6; margin-top:12px; margin-left:30px;">
โปรดใช้ประกอบการตัดสินใจลงทุน ควรพิจารณาร่วมกับ Fair Value และ Company Health ก่อนตัดสินใจ ไม่ใช่คำแนะนำโดยตรง
</div>
{warn_line}
</div>

</div>
</div>""",
        unsafe_allow_html=True
    )

    st.markdown("<div style='margin-top:22px;'></div>", unsafe_allow_html=True)

    # ============================================================
    # 3) FORECAST — ราคาจะไปทางไหนในอนาคต (ไม่มีอยู่ในภาพ mockup ที่ได้รับ — คงไว้เหมือน v6 เดิมทุกประการ)
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

    vol_annual = safe(ctx.stock_info.get('volatility'), 25.0) / 100
    daily_vol = vol_annual / np.sqrt(252)
    horizon_days = 10

    future_dates = pd.bdate_range(
        start=hist_tail['date'].iloc[-1],
        periods=horizon_days + 1
    )[1:]

    drift = (prob_up - 50) / 50 * daily_vol * horizon_days
    t_arr = np.arange(1, horizon_days + 1)

    median_path = ctx.current_price * (1 + drift * (t_arr / horizon_days))
    band = ctx.current_price * daily_vol * np.sqrt(t_arr) * 1.28

    upper_path = median_path + band
    lower_path = median_path - band

    fig_forecast = go.Figure()

    fig_forecast.add_trace(
        go.Scatter(
            x=future_dates, y=lower_path, mode='lines',
            line=dict(width=0), showlegend=False, hoverinfo='skip'
        )
    )
    fig_forecast.add_trace(
        go.Scatter(
            x=future_dates, y=upper_path, mode='lines',
            line=dict(width=0), fill='tonexty',
            fillcolor=_hex_to_rgba(status_color, 0.18),
            name='Prediction Range', hoverinfo='skip'
        )
    )
    fig_forecast.add_trace(
        go.Scatter(
            x=future_dates, y=median_path, mode='lines',
            line=dict(color=status_color, width=2.2, dash='dash'),
            name='Model Forecast (Median)'
        )
    )
    fig_forecast.add_trace(
        go.Scatter(
            x=hist_tail['date'], y=hist_tail['close'], mode='lines',
            line=dict(color=BLUE, width=2.2), name='Actual Price'
        )
    )

    fig_forecast.update_layout(
        height=350,
        margin=dict(l=45, r=25, t=10, b=30),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        xaxis=dict(gridcolor="#D9E2EC", tickfont=dict(size=11, color=MUTED), zeroline=False),
        yaxis=dict(
            title=dict(text="Price (THB)", font=dict(size=11.5, color=MUTED)),
            gridcolor="#D9E2EC", tickfont=dict(size=11, color=MUTED), zeroline=False
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0, font=dict(size=11, color="#334155"))
    )

    show_chart(fig_forecast, key="ai_forecast", expand_height=700)

    st.markdown("<div style='margin-top:22px;'></div>", unsafe_allow_html=True)

    # ============================================================
    # 4) MODEL EXPLANATION — โมเดลตัดสินใจจากอะไร (ไม่มีอยู่ในภาพ mockup ที่ได้รับ — คงไว้เหมือน v6 เดิมทุกประการ)
    # ============================================================

    st.markdown(_section_title("MODEL EXPLANATION"), unsafe_allow_html=True)

    exp_c1, exp_c2 = st.columns([1.4, 1])

    fi = ctx.feat_imp_df[ctx.feat_imp_df['ticker'] == ctx.selected_ticker].sort_values('importance')

    with exp_c1:
        if not fi.empty:
            fig_shap = go.Figure(
                go.Bar(
                    x=fi['importance'], y=fi['feature'], orientation='h',
                    marker=dict(color=BLUE),
                    text=[f"{v:.3f}" for v in fi['importance']],
                    textposition='outside',
                    textfont=dict(size=11, color='#334155')
                )
            )
            fig_shap.update_layout(
                height=310,
                margin=dict(l=10, r=50, t=15, b=15),
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#FFFFFF",
                xaxis=dict(gridcolor="#D9E2EC", tickfont=dict(size=11, color=MUTED), zeroline=False),
                yaxis=dict(tickfont=dict(size=11.5, color="#334155"), gridcolor="#D9E2EC", zeroline=False),
                showlegend=False
            )
            show_chart(fig_shap, key="ai_feature_importance", expand_height=650)
        else:
            st.info("ไม่มีข้อมูล Feature Importance")

    with exp_c2:
        top_feat = fi.sort_values('importance', ascending=False).iloc[0]['feature'] if not fi.empty else "N/A"
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

    render_nav_footer("m4", prev_page=" Entry Timing", next_page=" Risk Analysis")
