"""
pages_content/entry_timing.py
--------------------------------------------------------------------
Institutional Grade UI - Bloomberg / TradingView Inspired

IKB v3.2 (Audit Response Build) — merged with main's readability polish

ยึดตรรกะ/การแก้บั๊กทั้งหมดจาก v3.2 (Audit Response Build) เป็นหลัก เพราะ
main ที่ branch นี้ conflict ด้วยยังเป็น v3.1 (เก่ากว่า) การเปลี่ยนแปลงคือ
การรองรับสถานะใหม่จาก backend v2.0 เท่านั้น

Changelog vs v3.1:
- ISSUE 01: เพิ่มเส้นทางเรนเดอร์ "ข้อมูลไม่เพียงพอ" (`_render_insufficient`)
  เมื่อ backend ส่ง data_status = 'INSUFFICIENT_DATA' หรือ timing_score = None
  ฟังก์ชัน render() จะ return ออกตั้งแต่ต้น องค์ประกอบที่ต้องการตัวเลข
  (เกจครึ่งวงกลม, แถบ %, f-string) จึงไม่ถูกเรียกเลย ไม่เกิด TypeError
  ใช้สีเทา #64748B ที่ไม่ซ้ำกับสถานะใดในระบบ และไม่ใช้ค่า default 50.0 อีก
- ISSUE 02: `pillar_pts_label()` หารด้วยจำนวนเกณฑ์ "คงที่"
  (trend_criteria_count / mom_criteria_count จาก backend) ไม่ใช่จำนวนที่มีข้อมูล
  เกณฑ์ที่ไม่มีข้อมูลแสดง badge = N/A แต่แต้มแสดง 0.0 pts ให้ตรงกับคะแนนจริง
- ISSUE 03: แถว Risk/Reward และการ์ด RISK / REWARD แยกแสดง 2 กรณี
  rr_status = 'NOT_COMPUTABLE' -> N/A พร้อมเหตุผล
  rr_status = 'COMPUTED'       -> แสดงอัตราส่วนจริงแม้จะต่ำ เช่น 0.19 : 1
  Risk/Reward จึงไม่ถูกนับรวมใน SIGNAL CHECKLIST (ที่เป็นสัญญาณ ผ่าน/ไม่ผ่าน
  ล้วนๆ) แต่แยกไปแสดงเป็นการ์ดของตัวเอง เพื่อไม่ให้สถานะ "คำนวณไม่ได้"
  ถูกตีความปนไปกับ "สัญญาณลบ"
- ถอดข้อความ narrative ที่ hardcode ในการ์ด RISK / REWARD
  ("Potential upside is significantly higher...") มาสร้างจากค่าที่คำนวณจริง
- แก้ระดับการย่อหน้าของบล็อก `with right:` ให้เป็นคอลัมน์พี่น้องของ
  `with center:` ตามที่ตั้งใจไว้ (ผลลัพธ์บนหน้าจอเหมือนเดิมทุกประการ)

=== MERGE NOTE (รวม Branch ทีมเจ้าของโมดูล/entry_timing x main) ===
- Logic/การแก้บั๊กทั้งหมด (ISSUE 01-03 ด้านบน) ยึดจากทีมเจ้าของโมดูล (v3.2)
  เพราะ main (v3.1) ยังมีบั๊กที่ v3.2 แก้ไปแล้ว เช่น การหารคะแนนด้วยจำนวน
  เกณฑ์ที่มีข้อมูล (ทำให้หุ้นข้อมูลแหว่งได้เปรียบ), การคำนวณแนวรับ-แนวต้าน
  ก่อนเช็คว่าราคาปัจจุบันมีค่าหรือไม่ (เสี่ยง TypeError เมื่อข้อมูลไม่พอ),
  และข้อความ Risk/Reward ที่ hardcode ไว้ตายตัว
- เพิ่ม page title header ("ENTRY TIMING" + คำอธิบาย) ที่ main เพิ่มมา
  เพื่อให้หน้าตาสอดคล้องกับหน้าอื่นๆ ในแดชบอร์ด (Company Health, Risk
  Analysis, AI Prediction, Industry Benchmark ก็มี header แบบนี้เหมือนกัน)
- ปรับขนาดฟอนต์ในการ์ด PRICE SETUP, RISK/REWARD, SYSTEM SCORING
  METHODOLOGY และ CONFIDENCE ให้ใหญ่ขึ้นตามที่ main ปรับไว้ (อ่านง่ายขึ้น
  และสอดคล้องกับฟอนต์ส่วนอื่นของหน้าที่ใช้ ~13-14px อยู่แล้ว) โดยเนื้อหา/
  ตัวเลขยังคง null-safe ตามตรรกะของ v3.2 ทั้งหมด
- เพิ่ม Risk/Reward กลับเข้ามาเป็นการ์ดที่ 4 ใน "WHY WAIT? / WHY NOW?"
  (main มี 4 การ์ด, v3.2 มี 3) แต่ทำให้ null-safe รองรับสถานะ NOT_COMPUTABLE
  ด้วยไอคอน/สีเทาเหมือนรายการอื่นในกลุ่มเดียวกัน แทนที่จะ crash หรือแสดง
  ค่าเท็จเมื่อคำนวณไม่ได้
- ปุ่มเปลี่ยนหน้าด้านล่างใช้ label แบบไม่มี emoji ให้ตรงกับหน้าอื่นทั้งหมด

=== PATCH NOTE (theme + typography) ===
- NEUTRAL: เปลี่ยนสีธีมจากสีฟ้า (ACCENT เดิมที่ backend ส่งมาใน sig["status_color"])
  เป็นสีเหลือง (AMBER) เพื่อไม่ให้ปนกับสีฟ้าที่ใช้เป็น accent สี highlight ทั่วทั้งหน้า
  ทำเป็น UI-only override หลังอ่านค่าจาก classify_signal() แล้ว (ไม่แตะ label /
  readiness / action ที่ยังต้องยึดจาก backend เป็น single source of truth ตามเดิม)
- ปรับขนาดฟอนต์จุดที่เล็กกว่ามาตรฐานของหน้าอื่น (10-11.5px) ให้อยู่ในช่วง
  12-13px ให้สอดคล้องกับสเกลฟอนต์ของหน้า Company Health (บรรทัดข้อมูล header
  bar, ป้ายชื่อ missing_fields, กล่องเหตุผลในหน้า "ข้อมูลไม่เพียงพอ", และ
  หมายเหตุใน SYSTEM SCORING METHODOLOGY)
"""
import html
import json
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
GRAY = "#64748B"          # ISSUE 01: สีเฉพาะของสถานะ "ยังไม่ได้ประเมิน"


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


def _metric_card(label, value, sub="", value_color=TEXT_WHITE, is_summary=False, card_bg=BG_CARD):
    content_style = (
        f"font-size:15px;font-weight:700;color:{value_color};margin-top:4px;"
        "overflow:hidden;text-overflow:ellipsis;display:-webkit-box;"
        "-webkit-line-clamp:2;-webkit-box-orient:vertical;line-height:1.35;"
        if is_summary
        else
        f"font-size:19px;font-weight:900;color:{value_color};margin-top:4px;"
        "white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"
    )

    return f"""
    <div style="{_card_style(
        f'height:100%;box-sizing:border-box;background:{card_bg};'
    )}">
        <div style="font-size:14px;font-weight:800;color:{'#FFFFFF' if card_bg != BG_CARD else TEXT_MUTED};letter-spacing:.5px;">
            {label}
        </div>
        <div style="{content_style}">
            {value}
        </div>
        <div style="font-size:14px;color:{'#FFFFFF' if card_bg != BG_CARD else TEXT_MUTED};margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
            {sub}
        </div>
    </div>
    """


def _num(value):
    """ISSUE 01: None ต้องคงเป็น None ห้ามถูกกลบเป็น 0.0 / 50.0 โดยอัตโนมัติ"""
    if value is None:
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return None if (np.isnan(out) or np.isinf(out)) else out


def _f(value, spec=".2f", dash="N/A"):
    """ISSUE 01 (hardening): format ตัวเลขโดยไม่ระเบิดเมื่อค่าเป็น None
    ต่างจาก safe(value, default) ของ v3.1 ตรงที่ไม่เคยแทน None ด้วยตัวเลข
    แต่คืนข้อความ "N/A" แทน จึงไม่มีทางเกิด
    TypeError: unsupported format string passed to NoneType.__format__
    ไม่ว่าคีย์ใดจาก backend จะหล่นหายระหว่างทางก็ตาม
    """
    if value is None:
        return dash
    try:
        return format(float(value), spec)
    except (TypeError, ValueError):
        return dash


def _missing_list(raw):
    """backend ส่ง missing_fields มาเป็น JSON string (SQLite compatibility)"""
    if isinstance(raw, (list, tuple)):
        return list(raw)
    try:
        parsed = json.loads(raw) if raw else []
        return parsed if isinstance(parsed, list) else []
    except (TypeError, ValueError):
        return []


def _render_header_bar(ticker_safe, sector_label, c_p, price_chg_pct, pe_ratio, roe_pct, data_as_of):
    chg_color = GREEN if (price_chg_pct or 0.0) >= 0 else RED
    chg_arrow = "▲" if (price_chg_pct or 0.0) >= 0 else "▼"
    price_html = (
        f'<b style="color:{TEXT_WHITE};font-size:14px;">{c_p:.2f} THB</b>'
        if c_p is not None else f'<b style="color:{TEXT_MUTED};font-size:14px;">N/A</b>'
    )
    chg_html = (
        f'<span style="color:{chg_color};font-weight:700;">({price_chg_pct:+.2f}%) {chg_arrow}</span>'
        if price_chg_pct is not None else ""
    )
    pe_html = (
        f'<div><span style="color:{TEXT_MUTED};">P/E:</span> <b style="color:{TEXT_WHITE};">{pe_ratio}x</b></div>'
        if pe_ratio not in (None, "") else ""
    )
    roe_html = (
        f'<div><span style="color:{TEXT_MUTED};">ROE:</span> <b style="color:{TEXT_WHITE};">{roe_pct}%</b></div>'
        if roe_pct not in (None, "") else ""
    )
    _render_html(
        f"""
        <div style="{_card_style('display:flex;justify-content:space-between;align-items:center;padding:12px 20px;margin-bottom:12px;')}">
            <div style="font-size:18px;font-weight:900;color:{TEXT_WHITE};letter-spacing:.5px;">
                {ticker_safe} <span style="font-size:13px;font-weight:500;color:{TEXT_MUTED};">{sector_label}</span>
            </div>
            <div style="display:flex;gap:20px;font-size:13px;align-items:center;">
                <div>
                    <span style="color:{TEXT_MUTED};">Price:</span>
                    {price_html} {chg_html}
                </div>
                {pe_html} {roe_html}
                <div>
                    <span style="color:{TEXT_MUTED};">Data as of:</span>
                    <b style="color:{ACCENT};">{data_as_of}</b>
                </div>
            </div>
        </div>
        """
    )


def _render_insufficient(sig, reason, missing_fields):
    """ISSUE 01: หน้าจอสถานะ "ยังไม่ได้ประเมิน"
    ใช้โครงการ์ดเดียวกับหน้าปกติ (grid 4 ช่อง + การ์ดใหญ่) เพื่อให้หน้าตาต่อเนื่อง
    แต่ไม่มีการเรนเดอร์เกจ คะแนน หรือแถบเปอร์เซ็นต์ใด ๆ ทั้งสิ้น
    """
    missing_html = (
        "".join(
            f'<span style="background:{BG_CHIP};color:{TEXT_MUTED};font-size:12px;font-weight:700;'
            f'padding:3px 8px;border-radius:4px;margin:0 4px 4px 0;display:inline-block;">{html.escape(str(m))}</span>'
            for m in missing_fields
        )
        or f'<span style="font-size:12.5px;color:{TEXT_MUTED};">ไม่ระบุรายการ</span>'
    )
    _render_html(
        f"""
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1.6fr;gap:10px;margin-bottom:12px;">
            {_metric_card("MARKET TREND", sig["status_label"], sig["action_th"], GRAY)}
            {_metric_card("ENTRY READINESS", "NO DATA", "ยังไม่ได้ประเมิน", GRAY)}
            {_metric_card("CONFIDENCE", "-- / --", "ไม่มีคะแนนความเชื่อมั่น", GRAY)}
            {_metric_card("ℹ️ สรุปสั้น ๆ", html.escape(str(reason)), "สถานะคุณภาพข้อมูลของหลักทรัพย์นี้", TEXT, is_summary=True)}
        </div>
        """
    )
    _render_html(
        f"""
        <div style="{_card_style('border-left:4px solid ' + GRAY + ';')}">
            <div style="font-size:13px;font-weight:900;color:{GRAY};border-bottom:2px solid {BORDER_SOFT};
                        padding-bottom:6px;margin-bottom:10px;">
                ⚠️ ข้อมูลไม่เพียงพอ — ระบบยังไม่ได้ประเมินหลักทรัพย์นี้
            </div>
            <div style="font-size:13px;color:{TEXT};line-height:1.6;">
                {html.escape(str(reason))}
            </div>
            <div style="margin-top:10px;font-size:12px;font-weight:800;color:{TEXT_MUTED};letter-spacing:.5px;">
                ตัวชี้วัดที่ขาด
            </div>
            <div style="margin-top:6px;">{missing_html}</div>
            <div style="margin-top:12px;background:rgba(100,116,139,.10);border-left:3px solid {GRAY};
                        padding:8px 12px;border-radius:0 6px 6px 0;font-size:12.5px;color:{TEXT};">
                <b>หมายเหตุ:</b> ระบบจงใจไม่แสดงคะแนนใด ๆ ในสถานะนี้ —
                <b>ไม่มีข้อมูล ไม่เท่ากับ ปานกลาง</b>
                การแสดงคะแนน 50 / NEUTRAL ให้หลักทรัพย์ที่ข้อมูลแหว่ง
                คือการให้สารสนเทศที่ทำให้เข้าใจผิด
            </div>
        </div>
        """
    )


def render(ctx):
    info = ctx.stock_info
    c_p = _num(ctx.current_price)
    ticker_safe = html.escape(str(ctx.selected_ticker))

    st.markdown("""
    <div style="margin-bottom:20px;">
        <div style="font-size:25px; font-weight:700; color:#0F172A; letter-spacing:0.3px;">
            ENTRY TIMING
        </div>
        <div style="font-size:16px; color:#64748B; margin-top:4px;">
            วิเคราะห์จังหวะการเข้าลงทุนจากแนวโน้ม โมเมนตัม และ Risk/Reward
        </div>
    </div>
    """, unsafe_allow_html=True)

    sector_label = str(safe(info.get("sector_label"), ""))
    data_as_of = str(safe(info.get("data_as_of"), "-"))
    price_chg_pct = _num(info.get("price_change_pct"))
    pe_ratio = safe(info.get("pe_ratio"), None)
    roe_pct = safe(info.get("roe_pct"), None)
    total_score = _num(info.get("timing_score"))
    data_status = str(info.get("data_status", "OK"))

    # Single source of truth: classify_signal() lives in the backend module.
    # Do not re-derive status_label/status_color/action_th/readiness here —
    # that duplication is what caused the UI and backend to drift apart before.
    sig = classify_signal(total_score)

    # ---- ISSUE 01: ข้อมูลไม่พอ -> ออกจาก render() ตั้งแต่ต้น ----
    if total_score is None or data_status == "INSUFFICIENT_DATA":
        _render_header_bar(ticker_safe, sector_label, c_p, price_chg_pct, pe_ratio, roe_pct, data_as_of)
        reason = str(info.get("data_status_reason") or info.get("summary_text") or sig["summary_text"])
        _render_insufficient(sig, reason, _missing_list(info.get("missing_fields")))
        render_nav_footer("m3", prev_page=" Fair Value", next_page=" AI Prediction")
        return

    status_label = sig["status_label"]
    status_color = sig["status_color"]
    action_th = sig["action_th"]
    readiness = sig["readiness"]

    # PATCH (theme): NEUTRAL ใช้สีเหลือง (AMBER) แทนสีฟ้าเดิมที่ backend ส่งมา
    # เป็น UI-only override — label / readiness / action ยังคงยึดจาก
    # classify_signal() เหมือนเดิมตาม single-source-of-truth ด้านบน
    # เปลี่ยนเฉพาะสีที่ใช้ "แสดงผล" บนหน้านี้เท่านั้น
    if status_label == "NEUTRAL":
        status_color = AMBER

    adx_val = _num(info.get("adx")) or 0.0
    r1 = _num(info.get("resistance_60d")) or c_p * 1.05
    r2 = _num(info.get("resistance_2")) or r1 * 1.05
    s1 = _num(info.get("support_60d")) or c_p * 0.95
    s2 = _num(info.get("support_2")) or s1 * 0.95
    pp = _num(info.get("pivot_point")) or round((r1 + s1 + c_p) / 3, 2)

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
    k_rr_av = bool(info.get("k_rr_available", False))

    # ISSUE 02: ตัวหารต้องเป็นจำนวนเกณฑ์ "ทั้งหมด" ของเสานั้น (คงที่ 3/3)
    # ไม่ใช่จำนวนเกณฑ์ที่มีข้อมูล มิฉะนั้นหุ้นข้อมูลแหว่งจะได้แต้มต่อหัวสูงกว่า
    trend_criteria_count = int(safe(info.get("trend_criteria_count"), 3)) or 3
    mom_criteria_count = int(safe(info.get("mom_criteria_count"), 3)) or 3

    rr_ratio = _num(info.get("rr_ratio"))
    rr_score = _num(info.get("rr_score")) or 0.0
    rr_status = str(info.get("rr_status", "COMPUTED"))
    rr_status_reason = str(info.get("rr_status_reason", ""))

    # ISSUE 03 (hardening): ห้ามเชื่อธงสถานะเพียงอย่างเดียว เพราะถ้าคีย์ rr_status
    # หล่นหายระหว่างทาง (backend เวอร์ชันเก่า หรือ schema ของ cis_database.db
    # ไม่มีคอลัมน์นี้) ค่า default "COMPUTED" จะพาโค้ดไป format rr_ratio ที่เป็น
    # None แล้วเกิด TypeError ทั้งหน้าจอ — ให้ "ค่าที่จะแสดง" เป็นคนตัดสินแทน
    rr_computable = (rr_status != "NOT_COMPUTABLE") and (rr_ratio is not None)
    if not rr_computable and not rr_status_reason:
        rr_status_reason = (
            "ไม่พบค่าอัตราส่วนจาก backend (ตรวจสอบว่าใช้ entry_timing.py v2.0 "
            "และตาราง cis_database.db มีคอลัมน์ rr_status / rr_status_reason)"
            if rr_status != "NOT_COMPUTABLE"
            else "ไม่สามารถนิยามอัตราส่วนผลตอบแทนต่อความเสี่ยงได้"
        )

    downside_pct = _num(info.get("downside_pct"))
    upside_pct = _num(info.get("upside_pct"))

    # TRADER MODE (v2.3): Stop Loss = 30-Day Low, Target 1/2 = Risk x 2 / x 3.
    # เมื่อ New Low Guardrails สั่งงดเข้าเทรด (rr_computable == False) ต้องไม่โชว์
    # ตัวเลข SL/Target ที่คำนวณมาแบบไม่มีความหมาย (เช่น Risk <= 0) จึงสลับเป็น
    # N/A พร้อมข้อความเตือนแทน
    if rr_computable:
        sl_display = f"&lt; {_f(s2)}"
        target1_display = _f(r1)
        target2_display = _f(r2)
        watch_zone_display = f"{_f(pp)} -- {_f(r1)}"
        setup_warning_html = ""
    else:
        sl_display = "N/A"
        target1_display = "N/A"
        target2_display = "N/A"
        watch_zone_display = f"{_f(pp)} -- N/A"
        setup_warning_html = f"""
        <div style="margin-top:8px;background:rgba(239,68,68,.08);border-left:3px solid {RED};
                    padding:6px 10px;border-radius:0 6px 6px 0;font-size:12px;color:{TEXT_MUTED};">
            <b style="color:{RED};">⚠ งดเข้าเทรด (New Low Guardrail):</b> {rr_status_reason}
        </div>
        """

    vol_series = next(
        (
            ctx.stock_daily[v]
            for v in ["volume", "Volume", "vol", "Vol"]
            if v in ctx.stock_daily.columns
        ),
        None,
    )

    def pillar_pts_label(ok, available, n_criteria, pillar_max):
        # ตัวชี้วัดที่ไม่มีข้อมูลได้ 0 คะแนนจริง ๆ (ISSUE 02) จึงแสดง 0.0 pts
        # ส่วนการบอกว่า "ไม่มีข้อมูล" เป็นหน้าที่ของ badge N/A ไม่ใช่ช่องแต้ม
        if not available or not ok:
            return "0.0 pts"
        share = pillar_max / n_criteria if n_criteria > 0 else 0.0
        return f"+{share:.1f} pts"

    # ISSUE 03: ข้อความของแถว Risk/Reward แยก 2 กรณีชัดเจน (ไม่นับรวมใน
    # SIGNAL CHECKLIST ด้านล่าง เพราะ "คำนวณไม่ได้" ไม่ควรถูกตีความเป็น "ไม่ผ่าน")
    if not rr_computable:
        rr_sub_text = f"คำนวณไม่ได้ — {rr_status_reason}"
    elif k_rr_ok:
        rr_sub_text = f"RR {_f(rr_ratio)} : 1 ผ่านเกณฑ์ขั้นต่ำ"
    else:
        rr_sub_text = f"RR {_f(rr_ratio)} : 1 ต่ำกว่าเกณฑ์ขั้นต่ำ"

    # 6 items: 3 Trend + 3 Momentum ตาม pillar weighting 40/30 ของ backend
    # (Risk/Reward แยกออกไปแสดงเป็นการ์ดของตัวเองด้านล่าง ดูเหตุผลใน ISSUE 03)
    checklist = [
        (k15_ok, k15_av, "Short-Term Trend",
         "ราคายืนเหนือเส้น EMA20" if k15_ok else ("ราคาต่ำกว่าเส้น EMA20" if k15_av else "ไม่มีข้อมูล EMA20"),
         pillar_pts_label(k15_ok, k15_av, trend_criteria_count, 40.0)),
        (k16_ok, k16_av, "Medium-Term Trend",
         "EMA20 อยู่เหนือ EMA50" if k16_ok else ("EMA20 ยังไม่ตัดขึ้นเหนือ EMA50" if k16_av else "ไม่มีข้อมูล EMA50"),
         pillar_pts_label(k16_ok, k16_av, trend_criteria_count, 40.0)),
        (k17_ok, k17_av, "Long-Term Trend",
         "ราคายืนเหนือเส้น MA200" if k17_ok else ("ราคายังอยู่ต่ำกว่า MA200" if k17_av else "ข้อมูลไม่ถึง 200 แท่ง"),
         pillar_pts_label(k17_ok, k17_av, trend_criteria_count, 40.0)),
        (k18_ok, k18_av, "Momentum (MACD)",
         "MACD อยู่ในโซนบวก" if k18_ok else ("MACD อยู่ในโซนลบ" if k18_av else "ไม่มีข้อมูล MACD"),
         pillar_pts_label(k18_ok, k18_av, mom_criteria_count, 30.0)),
        (k19_ok, k19_av, "Trend Strength (ADX)",
         (f"ADX {_f(adx_val, '.1f')} (มีแรงเหวี่ยงดี)" if k19_ok else f"ADX {_f(adx_val, '.1f')} (ต่ำกว่าเกณฑ์)") if k19_av else "ไม่มีข้อมูล ADX",
         pillar_pts_label(k19_ok, k19_av, mom_criteria_count, 30.0)),
        (k20_ok, k20_av, "Volume Confirmation",
         ("วอลุ่มล่าสุดสูงกว่าค่าเฉลี่ย 20 วันก่อนหน้า" if k20_ok else "วอลุ่มเบาบางกว่าค่าเฉลี่ย 20 วันก่อนหน้า") if k20_av else "ไม่มีข้อมูลวอลุ่มเพียงพอ",
         pillar_pts_label(k20_ok, k20_av, mom_criteria_count, 30.0)),
    ]

    bullish_count = sum(1 for ok, av, *_ in checklist if ok and av)
    total_checks = len(checklist)
    failed_items = [name for ok, av, name, _, _ in checklist if not ok and av]
    na_items = [name for ok, av, name, _, _ in checklist if not av]

    if bullish_count >= total_checks - 1:
        summary_text = f"สัญญาณพร้อมสูง ({bullish_count}/{total_checks}) โครงสร้างราคาและโมเมนตัมสนับสนุนการเข้าสะสม"
    elif len(failed_items) + len(na_items) <= 2:
        missing_str = ", ".join(failed_items + [f"{n} (ไม่มีข้อมูล)" for n in na_items])
        summary_text = f"ผ่าน {bullish_count}/{total_checks} เกณฑ์ --- <b>รอการยืนยันจาก: {missing_str}</b>"
    else:
        summary_text = f"ผ่าน {bullish_count}/{total_checks} เกณฑ์ --- <b>สัญญาณยังไม่ครบถ้วน ควรงดเข้าซื้อ</b>"

    # --- TOP HEADER BAR ---
    _render_header_bar(ticker_safe, sector_label, c_p, price_chg_pct, pe_ratio, roe_pct, data_as_of)
    readiness_color = GREEN if readiness == "READY" else AMBER

    confidence_dots = "".join([
        f'<span style="height:7px;width:7px;'
        f'background-color:{"#10B981" if i < bullish_count else "#CBD5E1"};'
        f'border-radius:50%;display:inline-block;margin-right:3px;"></span>'
        for i in range(total_checks)
    ])

    kpi_html = f"""
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1.6fr;gap:10px;margin-bottom:12px;">
        {_metric_card(
            "ENTRY READINESS",
            readiness,
            "รอการยืนยันสัญญาณเพิ่มเติม" if readiness != "READY" else "สัญญาณครบตามเกณฑ์",
            "#FFFFFF",
            card_bg=readiness_color
        )}
        {_metric_card("MARKET TREND", status_label, action_th, status_color)}
        <div style="{_card_style()}">
            <div style="font-size:14px;font-weight:800;color:{TEXT_MUTED};letter-spacing:.5px;">CONFIDENCE</div>
            <div style="font-size:20px;font-weight:900;color:{TEXT_WHITE};margin-top:4px;">{bullish_count} / {total_checks}</div>
            <div style="margin-top:4px;">{confidence_dots}</div>
        </div>
        {_metric_card(
            "ⓘ สรุปสั้น ๆ",
            summary_text,
            "ภาพรวมสถานะการลงทุนเชิงปริมาณ",
            TEXT,
            is_summary=True
        )}
    </div>
    """

    _render_html(kpi_html)

    # ปรับสัดส่วนคอลัมน์ให้สมมาตรและพอดีกับจอภาพแบบ Institutional Grade
    left, center, right = st.columns([1.0, 2.3, 1.15], gap="medium")

    # ==================================================================
    # LEFT COLUMN
    # ==================================================================
    with left:

        total_arc = 125.66
        score_fill = round(total_arc * min(1.0, max(0.0, total_score / 100.0)), 2)

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
                    font-size:16px;
                    font-weight:800;
                    color:{TEXT_WHITE};
                ">
                    ⏱️ ENTRY TIMING ANALYSIS
                </div>

                <div style="text-align:center;margin-top:8px;">

                    <svg viewBox="0 0 100 55" style="width:120px;height:66px;display:block;margin:0 auto;">

                        <path d="M 10 48 A 38 38 0 0 1 90 48" fill="none" stroke="{BORDER_SOFT}" stroke-width="7" stroke-linecap="round" />

                        <path d="M 10 48 A 38 38 0 0 1 90 48" fill="none" stroke="{status_color}" stroke-width="7"
                              stroke-linecap="round" stroke-dasharray="{score_fill} {total_arc}" />

                        <text x="50" y="33" text-anchor="middle" font-size="20" font-weight="900" fill="{TEXT_WHITE}">
                            {total_score:.0f}
                        </text>

                        <text x="50" y="43" text-anchor="middle" font-size="8" font-weight="700" fill="{TEXT_MUTED}">
                            / 100
                        </text>

                    </svg>

                    <div style="font-size:19px;font-weight:900;color:{status_color};margin-top:2px;">
                        {status_label}
                    </div>

                    <div style="font-size:14px;color:{TEXT_MUTED};">
                        {action_th}
                    </div>

                </div>

                <div style="border-top:1px solid {BORDER_SOFT};margin-top:8px;padding-top:5px;
                            display:flex;justify-content:space-between;font-size:13px;font-weight:800;">
                    <span style="color:{TEXT_WHITE};">CONFLUENCE</span>
                    <span style="color:{status_color};">{bullish_count} / {total_checks} ผ่าน</span>
                </div>

            </div>
            """
        )

        checklist_items = []

        for ok, av, label, sub, points in checklist:

            badge_label, badge_color, badge_bg = _badge(ok, av)
            icon = "✓" if ok and av else ("✕" if av else "--")

            checklist_items.append(
                f"""
                <div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;
                            border-bottom:1px solid {BORDER_SOFT};">

                    <div style="display:flex;align-items:center;gap:6px;min-width:0;">

                        <div style="background:rgba({badge_bg},.15);color:{badge_color};width:16px;height:16px;
                                    border-radius:50%;display:flex;align-items:center;justify-content:center;
                                    font-size:15px;font-weight:bold;flex-shrink:0;">
                            {icon}
                        </div>

                        <div style="min-width:0;">
                            <div style="font-size:14px;color:{TEXT_WHITE};font-weight:700;">{label}</div>
                            <div style="font-size:13px;color:{TEXT_MUTED};">{sub}</div>
                        </div>

                    </div>

                    <span style="background:rgba({badge_bg},.15);color:{badge_color};font-size:13px;font-weight:800;
                                 padding:2px 5px;border-radius:4px;white-space:nowrap;margin-left:5px;">
                        {badge_label}
                    </span>

                </div>
                """
            )

        _render_html(
            f"""
            <div style="{_card_style()}">

                <div style="font-size:16px;font-weight:800;color:{TEXT_WHITE};margin-bottom:6px;
                            border-bottom:2px solid {ACCENT};padding-bottom:4px;display:flex;justify-content:space-between;">
                    <span>🛡️ SIGNAL CHECKLIST</span>
                    <span style="color:{status_color};">{bullish_count} / {total_checks} ผ่าน</span>
                </div>

                {''.join(checklist_items)}

                <div style="margin-top:8px;font-size:16px;font-weight:900;color:{status_color};
                            display:flex;justify-content:space-between;">
                    <span>CHECKS PASSED</span>
                    <span>{bullish_count} / {total_checks}</span>
                </div>

            </div>
            """
        )

    # ==================================================================
    # CENTER COLUMN
    # ==================================================================
    with center:

        c_head1, c_head2 = st.columns([1, 1.5])

        with c_head1:
            _render_html(
                f"""
                <div style="font-size:16px;font-weight:800;color:{TEXT_WHITE};padding-top:4px;">
                    PRICE ACTION &amp; VOLUME
                </div>
                """
            )

        with c_head2:
            tf_selected = st.radio(
                "TF", ["1M", "3M", "6M", "1Y", "2Y", "ALL"],
                index=2, horizontal=True, label_visibility="collapsed", key="timing_tf_sel",
            )

        tf_bars = {"1M": 22, "3M": 66, "6M": 132, "1Y": 252, "2Y": 504, "ALL": len(ctx.stock_daily)}
        n_bars = min(tf_bars.get(tf_selected, 132), len(ctx.stock_daily))
        chart_df = ctx.stock_daily.tail(n_bars).copy()

        aliases = {"Close": "close", "Open": "open", "High": "high", "Low": "low", "Date": "date"}
        for source, target in aliases.items():
            if source in chart_df.columns and target not in chart_df.columns:
                chart_df[target] = chart_df[source]

        required = {"close", "open", "high", "low", "date"}
        if not required.issubset(chart_df.columns):
            st.error("ไม่พบข้อมูล OHLC/Date ที่จำเป็นสำหรับกราฟ")
        else:

            fig_main = make_subplots(
                rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.78, 0.22],
            )

            fig_main.add_trace(
                go.Candlestick(
                    x=chart_df["date"], open=chart_df["open"], high=chart_df["high"],
                    low=chart_df["low"], close=chart_df["close"], name="Price",
                    increasing_line_color=GREEN, decreasing_line_color=RED, line=dict(width=1),
                ),
                row=1, col=1,
            )

            if "EMA20" in chart_df.columns:
                fig_main.add_trace(
                    go.Scatter(x=chart_df["date"], y=chart_df["EMA20"], line=dict(color=AMBER, width=1.2), name="EMA 20"),
                    row=1, col=1,
                )

            if "EMA50" in chart_df.columns:
                fig_main.add_trace(
                    go.Scatter(x=chart_df["date"], y=chart_df["EMA50"], line=dict(color=ACCENT, width=1.2), name="EMA 50"),
                    row=1, col=1,
                )

            if "MA200" in chart_df.columns:
                fig_main.add_trace(
                    go.Scatter(x=chart_df["date"], y=chart_df["MA200"], line=dict(color="#A78BFA", width=1.2), name="MA 200"),
                    row=1, col=1,
                )

            bar_colors = [GREEN if c >= o else RED for c, o in zip(chart_df["close"], chart_df["open"])]
            vol_data = vol_series.tail(n_bars) if vol_series is not None else pd.Series(
                np.zeros(len(chart_df)), index=chart_df.index
            )

            fig_main.add_trace(
                go.Bar(x=chart_df["date"], y=vol_data, marker_color=bar_colors, showlegend=False),
                row=2, col=1,
            )

            lines_to_plot = [
                (r2, "dot", "#F87171", 1.0),
                (r1, "dash", RED, 1.2),
                (pp, "dash", "#94A3B8", 1.2),
                (s1, "dash", GREEN, 1.2),
                (s2, "dash", RED, 1.2),
            ]

            for val, dash_type, col_hex, w in lines_to_plot:
                fig_main.add_hline(y=val, line_dash=dash_type, line_color=col_hex, line_width=w)

            # ขยายความสูงของกราฟให้เติมเต็มพื้นที่ฝั่งขวาพอดี (height=525)
            fig_main.update_layout(
                height=525,
                margin=dict(l=8, r=40, t=25, b=5),
                paper_bgcolor=BG_CARD,
                plot_bgcolor=BG_CARD,
                xaxis=dict(gridcolor=BORDER_SOFT, showticklabels=False, linecolor=BORDER),
                xaxis2=dict(gridcolor=BORDER_SOFT, tickfont=dict(size=13, color=TEXT_MUTED), linecolor=BORDER),
                yaxis=dict(gridcolor=BORDER_SOFT, side="right", tickfont=dict(size=13, color=TEXT_MUTED), linecolor=BORDER),
                yaxis2=dict(showticklabels=False, gridcolor=BORDER_SOFT),
                legend=dict(orientation="h", y=1.12, x=0.01, font=dict(size=13, color=TEXT_WHITE), bgcolor="rgba(255,255,255,0)"),
                xaxis_rangeslider_visible=False,
                hovermode="x unified",
            )

            st.plotly_chart(fig_main, use_container_width=True, config={"displayModeBar": True, "displaylogo": False})

    # ==================================================================
    # RIGHT COLUMN
    # ==================================================================
    with right:

        _render_html(
            f"""
            <div style="{_card_style('margin-bottom:12px;')}">
                <div style="border-bottom:2px solid {ACCENT};padding-bottom:5px;display:flex;justify-content:space-between;
                            align-items:center;flex-wrap:wrap;row-gap:4px;">
                    <span style="font-size:14px;font-weight:800;color:{TEXT_WHITE};">PRICE SETUP</span>
                    <span style="background:rgba(56,189,248,.15);color:{ACCENT};font-size:13px;font-weight:800;
                                 padding:2px 6px;border-radius:4px;">Current {_f(c_p)}</span>
                </div>
                <div style="margin-top:8px;">
                    <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid {BORDER_SOFT};font-size:14px;">
                        <span style="color:{TEXT_MUTED};">Current Price</span><b style="color:{TEXT_WHITE};">{_f(c_p)} THB</b>
                    </div>
                    <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid {BORDER_SOFT};font-size:14px;">
                        <span style="color:{GREEN};">Preferred Entry</span><b style="color:{GREEN};">{_f(s1)} -- {_f(pp)}</b>
                    </div>
                    <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid {BORDER_SOFT};font-size:14px;">
                        <span style="color:{AMBER};">Watch Zone</span><b style="color:{AMBER};">{watch_zone_display}</b>
                    </div>
                    <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid {BORDER_SOFT};font-size:14px;">
                        <span style="color:{RED};">Stop Loss (30D Low)</span><b style="color:{RED};">{sl_display}</b>
                    </div>
                    <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid {BORDER_SOFT};font-size:14px;">
                        <span style="color:{TEXT_WHITE};">Target 1 (RR 1:2)</span><b style="color:{TEXT_WHITE};">{target1_display}</b>
                    </div>
                    <div style="display:flex;justify-content:space-between;padding:5px 0;font-size:14px;">
                        <span style="color:{TEXT_WHITE};">Target 2 (RR 1:3)</span><b style="color:{TEXT_WHITE};">{target2_display}</b>
                    </div>
                </div>
                {setup_warning_html}
            </div>
            """
        )

        _render_html(
            f"""
            <div style="{_card_style()}">
                <div style="
                    font-size:16px;
                    font-weight:800;
                    color:{TEXT_WHITE};
                    margin-bottom:6px;
                    border-bottom:2px solid {ACCENT};
                    padding-bottom:4px;
                ">
                    ⓘ SYSTEM SCORING METHODOLOGY
                </div>
                <div style="font-size:14px;color:{TEXT_MUTED};line-height:1.45;">
                    <b style="color:{TEXT_WHITE};">Trend --- 40 pts</b><br>
                    ราคาเทียบ EMA20, EMA50 และ MA200 (หาร {trend_criteria_count} เกณฑ์คงที่)
                    <br><br>
                    <b style="color:{TEXT_WHITE};">Momentum --- 30 pts</b><br>
                    MACD, ADX และ Volume Confirmation (หาร {mom_criteria_count} เกณฑ์คงที่)
                    <br><br>
                    <b style="color:{TEXT_WHITE};">Reward / Risk --- 30 pts</b><br>
                    ประเมินจากผลตอบแทนเทียบกับ downside
                    <br><br>
                    <span style="font-size:14px;">ตัวชี้วัดที่ไม่มีข้อมูลได้ 0 คะแนน ระบบไม่ลดตัวหารให้
                    เพื่อให้ทุกหลักทรัพย์ถูกวัดด้วยมาตรฐานเดียวกัน</span>
                </div>
            </div>
            """
        )

    # ==================================================================
    # BOTTOM SECTION
    # ==================================================================
    st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
    b_c1, b_c2 = st.columns([1.0, 1.5], gap="medium")

    # ------------------------------------------------------------
    # BOTTOM LEFT - RISK / REWARD
    # ------------------------------------------------------------
    with b_c1:

        # ISSUE 03: NOT_COMPUTABLE ต้องไม่ถูกแสดงเป็น "0.00 : 1" ปนกับค่าที่คำนวณได้จริง
        if not rr_computable:
            rr_color = GRAY
            rr_headline = "N/A"
            rr_note = rr_status_reason
        else:
            rr_color = GREEN if rr_ratio >= 2.0 else (AMBER if rr_ratio >= 1.5 else RED)
            rr_headline = f"{_f(rr_ratio)} : 1"
            if rr_ratio >= 2.0:
                rr_note = "อัพไซด์สูงกว่าระยะความเสี่ยงที่นิยามไว้อย่างมีนัยสำคัญ"
            elif rr_ratio >= 1.0:
                rr_note = "อัพไซด์สูงกว่าระยะความเสี่ยง แต่ส่วนต่างยังไม่มาก"
            else:
                rr_note = "อัพไซด์ต่ำกว่าระยะความเสี่ยง ยังไม่คุ้มค่าที่จะเข้า"

        upside_bar = min(100, max(0, (upside_pct or 0.0) * 2))
        downside_bar = min(100, max(0, (downside_pct or 0.0) * 5))

        _render_html(
            f"""
            <div style="{_card_style()}">

                <div style="font-size:16px;font-weight:800;color:{TEXT_WHITE};margin-bottom:8px;
                            border-bottom:2px solid {ACCENT};padding-bottom:4px;">
                    RISK / REWARD
                </div>

                <div style="margin-bottom:6px;">
                    <div style="display:flex;justify-content:space-between;font-size:14px;color:{TEXT_MUTED};">
                        <span>Expected Upside</span>
                        <b style="color:{GREEN};">{('+' + format(upside_pct, '.1f') + '%') if upside_pct is not None else 'N/A'}</b>
                    </div>
                    <div style="background:{BORDER_SOFT};height:5px;border-radius:2.5px;overflow:hidden;margin-top:2px;">
                        <div style="background:{GREEN};width:{upside_bar:.0f}%;height:100%;"></div>
                    </div>
                </div>

                <div style="margin-bottom:10px;">
                    <div style="display:flex;justify-content:space-between;font-size:14px;color:{TEXT_MUTED};">
                        <span>Maximum Risk</span>
                        <b style="color:{RED};">{('-' + format(downside_pct, '.1f') + '%') if downside_pct is not None else 'N/A'}</b>
                    </div>
                    <div style="background:{BORDER_SOFT};height:5px;border-radius:2.5px;overflow:hidden;margin-top:2px;">
                        <div style="background:{RED};width:{downside_bar:.0f}%;height:100%;"></div>
                    </div>
                </div>

                <div style="display:flex;justify-content:space-between;align-items:center;
                            border-top:1px solid {BORDER_SOFT};padding-top:6px;gap:10px;">
                    <span style="font-size:19px;font-weight:900;color:{rr_color};white-space:nowrap;">{rr_headline}</span>
                    <span style="font-size:13px;color:{TEXT_MUTED};text-align:right;line-height:1.35;">{rr_note}</span>
                </div>

            </div>
            """
        )

    # ------------------------------------------------------------
    # BOTTOM RIGHT - WHY WAIT / WHY NOW
    # ------------------------------------------------------------
    with b_c2:

        trend_ok = k15_ok and k16_ok
        trend_av = k15_av and k16_av

        reasons = [
            ("Trend", "✓" if trend_ok else "✕", GREEN if trend_ok else (RED if trend_av else GRAY),
             "โครงสร้างราคาเหนือเส้นเฉลี่ย" if trend_ok else ("ราคาอยู่ใต้ EMA20" if trend_av else "ไม่มีข้อมูลเส้นเฉลี่ย")),
            ("Momentum", "✓" if k18_ok else "✕", GREEN if k18_ok else (RED if k18_av else GRAY),
             "MACD สนับสนุนโมเมนตัม" if k18_ok else ("MACD เป็นขาลง" if k18_av else "ไม่มีข้อมูล MACD")),
            ("Volume", "✓" if k20_ok else "✕", GREEN if k20_ok else (RED if k20_av else GRAY),
             "มี Volume ยืนยัน" if k20_ok else ("วอลุ่มไม่หนุน" if k20_av else "ไม่มีข้อมูลวอลุ่ม")),
            ("Risk / Reward", "✓" if (rr_computable and k_rr_ok) else "✕",
             GREEN if (rr_computable and k_rr_ok) else (RED if rr_computable else GRAY),
             (("อัตราผลตอบแทนคุ้มค่า" if k_rr_ok else "อัตราผลตอบแทนยังไม่คุ้มความเสี่ยง")
              if rr_computable else "คำนวณไม่ได้ (ข้อมูลไม่พอ)")),
        ]

        reason_cards = "".join(
            f"""
            <div style="background:{BG_CHIP};padding:7px;border-radius:6px;text-align:center;">
                <div style="font-size:14px;color:{color};font-weight:bold;">{icon} {name}</div>
                <div style="font-size:13px;color:{TEXT_MUTED};margin-top:2px;">{desc}</div>
            </div>
            """
            for name, icon, color, desc in reasons
        )

        wait_title = "WHY WAIT?" if readiness != "READY" else "WHY NOW?"
        wait_subtitle = "เหตุผลที่ระบบยังรอการยืนยันก่อนเข้าซื้อ" if readiness != "READY" else "เหตุผลที่สัญญาณมีความพร้อมมากขึ้น"

        _render_html(
            f"""
            <div style="{_card_style()}">

                <div style="font-size:16px;font-weight:800;color:{ACCENT};margin-bottom:5px;">
                    💡 {wait_title}
                </div>

                <div style="font-size:14px;color:{TEXT};margin-bottom:8px;">
                    {wait_subtitle}
                </div>

                <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-bottom:6px;">
                    {reason_cards}
                </div>

                <div style="background:rgba(56,189,248,.08);border-left:3px solid {ACCENT};padding:6px 10px;
                            border-radius:0 6px 6px 0;font-size:14px;color:{TEXT};">
                    <b>สรุป:</b> {summary_text}
                </div>

            </div>
            """
        )

    render_nav_footer("m3", prev_page=" Fair Value", next_page=" AI Prediction")
