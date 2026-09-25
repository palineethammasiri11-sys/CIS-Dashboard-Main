"""
calculate_modules/fair_value.py — v3 (Full Audit Fixes & Sector Baseline)
========================================================================
สูตรคำนวณโมดูล "Fair Value" (⚖️) — เข้ากันได้ 100% กับ pages_content/fair_value.py เดิม

=== DATA CONTRACT ===
calculate_valuation_module(df_fin_ticker, current_price, ticker, beta=None, **kwargs)
คืนค่า dict ที่มีคีย์ครอบคลุมทุกเวอร์ชัน (wacc, terminal, target_pe, fcf_growth):
    valuation_score, fair_value, dcf_fair_value, pe_fair_value,
    margin_of_safety, pe_ratio, pb_ratio, market_cap_mb, eps,
    wacc, wacc_used, wacc_str, terminal, terminal_growth, terminal_growth_used, terminal_str,
    target, target_pe, target_pe_used, target_pe_str, target_pb,
    fcf_growth, fcf_growth_assumed, fcf_growth_yr1, fcf_base, fcf_base_used,
    raw_dcf_fair_value, raw_pe_fair_value, dcf_is_clipped, pe_is_clipped, is_clipped,
    pe_score, dcf_score, intrinsic_score, relative_score, safety_score,
    dcf_is_estimate, pe_is_estimate, book_value_per_share, shares_outstanding,
    valuation_status, confidence_level, valuation_methodology_note, warning_message
"""

import numpy as np
import pandas as pd
from calculate_modules.common import clean_float, SECTOR_MAP

# 1. จำนวนหุ้นจดทะเบียนจริงในตลาดหลักทรัพย์แห่งประเทศไทย (SET)
SHARES_OUTSTANDING = {
    'ADVANC': 2974209736,
    'CCET':   10400000000,
    'DELTA':  12473816149,
    'HANA':   885366460,
    'JMART':  1458518485,
    'KCE':    1182429485,
    'THCOM':  1096000000,
    'TRUE':   34552100801
}

# 2. การกำหนดสมมติฐานตาม 3 กลุ่มอุตสาหกรรม (Sector Baseline Benchmark)
STOCK_VALUATION_PARAMS = {
    # 📊 กลุ่มที่ 1: Technology & Telecommunication
    # ตลาดผู้ขายเท่าน้อยราย (Oligopoly), กระแสเงินสดสม่ำเสมอ, ขยายโครงข่ายดิจิทัลต่อเนื่อง
    'ADVANC': {'target_pe': 22.0, 'wacc': 0.078, 'terminal_g': 0.020, 'group': 'Technology & Telecommunication'},
    'TRUE':   {'target_pe': 22.0, 'wacc': 0.078, 'terminal_g': 0.020, 'group': 'Technology & Telecommunication'},
    'THCOM':  {'target_pe': 22.0, 'wacc': 0.078, 'terminal_g': 0.020, 'group': 'Technology & Telecommunication'},

    # 📊 กลุ่มที่ 2: Electronic Components
    # รายได้หลักจากการส่งออก ผันผวนตาม Global Tech Cycle และอัตราแลกเปลี่ยน
    'DELTA':  {'target_pe': 18.0, 'wacc': 0.088, 'terminal_g': 0.015, 'group': 'Electronic Components'},
    'HANA':   {'target_pe': 18.0, 'wacc': 0.088, 'terminal_g': 0.015, 'group': 'Electronic Components'},
    'KCE':    {'target_pe': 18.0, 'wacc': 0.088, 'terminal_g': 0.015, 'group': 'Electronic Components'},
    'CCET':   {'target_pe': 18.0, 'wacc': 0.088, 'terminal_g': 0.015, 'group': 'Electronic Components'},

    # 📊 กลุ่มที่ 3: Commerce & Technology
    # Retail & Holding ผสมผสานการเงินและเทคโนโลยี ศักยภาพเติบโตสูงแต่ผันผวนตามการบริโภค
    'JMART':  {'target_pe': 22.0, 'wacc': 0.092, 'terminal_g': 0.025, 'group': 'Commerce & Technology'},
}

SECTOR_WACC = {
    'Technology & Telecomm': 0.078,
    'Technology & Telecommunication': 0.078,
    'Electronic Components': 0.088,
    'Commerce & Technology': 0.092,
}

SECTOR_TERMINAL_G = {
    'Technology & Telecomm': 0.020,
    'Technology & Telecommunication': 0.020,
    'Electronic Components': 0.015,
    'Commerce & Technology': 0.025,
}

SECTOR_TARGET_PE = {
    'Technology & Telecomm': 22.0,
    'Technology & Telecommunication': 22.0,
    'Electronic Components': 18.0,
    'Commerce & Technology': 22.0,
}

DEFAULT_WACC = 0.082
DEFAULT_TERMINAL_G = 0.020
DEFAULT_TARGET_PE = 20.0
NEAR_TERM_GROWTH_PREMIUM = 0.015

VALUATION_METHODOLOGY_NOTE = (
    "WACC และ Target P/E อ้างอิงตาม Sector Baseline Benchmark 3 กลุ่มอุตสาหกรรมใน SET: "
    "กลุ่ม Tech & Telecom (WACC 7.8%, Target P/E 22.0x, g 2.0%), "
    "กลุ่ม Electronic Components (WACC 8.8%, Target P/E 18.0x, g 1.5%), "
    "และกลุ่ม Commerce & Tech (WACC 9.2%, Target P/E 22.0x, g 2.5%) "
    "แผนงานเฟสถัดไปจะปรับระบบให้รองรับ Dynamic P/E Band ย้อนหลัง 5 ปี และ Beta รายบริษัทตาม CAPM"
)

_EMPTY_KEYS = [
    'valuation_score', 'fair_value', 'dcf_fair_value', 'pe_fair_value', 'margin_of_safety',
    'pe_ratio', 'pb_ratio', 'market_cap_mb', 'eps',
    'wacc', 'wacc_used', 'wacc_str', 'terminal', 'terminal_growth', 'terminal_growth_used', 'terminal_str',
    'target', 'target_pe', 'target_pe_used', 'target_pe_str', 'target_pb',
    'fcf_growth', 'fcf_growth_assumed', 'fcf_growth_yr1', 'fcf_base', 'fcf_base_used',
    'raw_dcf_fair_value', 'raw_pe_fair_value', 'dcf_fair_value_raw', 'pe_fair_value_raw',
    'dcf_is_clipped', 'pe_is_clipped', 'is_clipped',
    'pe_score', 'dcf_score', 'intrinsic_score', 'relative_score', 'safety_score',
    'dcf_is_estimate', 'pe_is_estimate', 'book_value_per_share', 'shares_outstanding',
]


def calc_sub_score(raw_fair_value, current_price):
    """
    [ISSUE 01 & ISSUE 03]
    คำนวณคะแนนย่อย 0-100 สำหรับแต่ละมิติ (DCF หรือ P/E)
    - ใช้ np.clip (0.65x - 1.85x) เฉพาะตอนแปลงเป็นคะแนน เพื่อรักษาเสถียรภาพระบบคะแนน
    - ส่งคืน is_clipped = True หากค่าประเมินดิบชนหรือทะลุกรอบขอบเขต
    - หาก raw_fair_value เป็น None (เช่น ผลประกอบการขาดทุน) ส่งคืนคะแนน 0.0 ตาม ISSUE 02
    """
    if raw_fair_value is None or current_price is None or current_price <= 0:
        return 0.0, False
    
    lower_bound = current_price * 0.65
    upper_bound = current_price * 1.85
    fair_for_score = float(np.clip(raw_fair_value, lower_bound, upper_bound))
    is_clipped = bool(raw_fair_value < lower_bound - 1e-4 or raw_fair_value > upper_bound + 1e-4)

    margin = (fair_for_score - current_price) / fair_for_score * 100 if fair_for_score > 0 else 0.0
    score = round(float(np.clip((margin + 20) * 1.4, 25.0, 95.0)), 1)
    return score, is_clipped


def calculate_valuation_module(df_fin_ticker, current_price, ticker, beta=None, **kwargs):
    """
    Module 2: Fair Value (DCF + Relative PE) — v3 Full Audit Resolution
    """
    # [ISSUE 05] Guard Clause ดักจับกรณีข้อมูลสูญหาย หรือราคาไม่ถูกต้อง
    if df_fin_ticker is None or (hasattr(df_fin_ticker, 'empty') and df_fin_ticker.empty) or current_price is None or current_price <= 0:
        out = {k: None for k in _EMPTY_KEYS}
        out['valuation_score'] = 0.0
        out['valuation_status'] = 'NO_DATA'
        out['confidence_level'] = 'Low'
        out['valuation_methodology_note'] = VALUATION_METHODOLOGY_NOTE
        out['warning_message'] = 'ไม่มีข้อมูลงบการเงิน หรือราคาหุ้นไม่ถูกต้อง ไม่สามารถประเมินมูลค่าได้'
        return out

    fin_sorted = df_fin_ticker.sort_values(by='year')
    if fin_sorted.empty:
        out = {k: None for k in _EMPTY_KEYS}
        out['valuation_score'] = 0.0
        out['valuation_status'] = 'NO_DATA'
        out['confidence_level'] = 'Low'
        out['valuation_methodology_note'] = VALUATION_METHODOLOGY_NOTE
        out['warning_message'] = 'ไม่มีข้อมูลงบการเงิน ไม่สามารถประเมินมูลค่าได้'
        return out

    r = fin_sorted.iloc[-1]

    # ดึงพารามิเตอร์ตามกลุ่มหุ้น (WACC, Terminal Growth, Target P/E)
    ticker_clean = str(ticker).replace('.BK', '').strip().upper() if ticker else ''
    param = STOCK_VALUATION_PARAMS.get(ticker_clean)
    sector = SECTOR_MAP.get(ticker_clean, '')
    if param:
        wacc = param['wacc']
        g = param['terminal_g']
        target_pe = param['target_pe']
    else:
        wacc = SECTOR_WACC.get(sector, DEFAULT_WACC)
        g = SECTOR_TERMINAL_G.get(sector, DEFAULT_TERMINAL_G)
        target_pe = SECTOR_TARGET_PE.get(sector, DEFAULT_TARGET_PE)

    near_term_growth = g + NEAR_TERM_GROWTH_PREMIUM

    shares = SHARES_OUTSTANDING.get(ticker_clean, 1000000000)
    net_inc = clean_float(r.get('net_income'), default=0.0)
    eps = clean_float(r.get('eps'), default=0.0)

    # Free Cash Flow ประเมินจากค่าเฉลี่ย 2 ปีล่าสุด หรือ Net Income Proxy
    fcf_hist = fin_sorted['free_cash_flow'].apply(clean_float).tail(2)
    fcf_base = float(fcf_hist.mean()) if len(fcf_hist) > 0 else (net_inc * 0.75)

    total_debt = clean_float(r.get('total_liabilities'), default=0.0)
    cash = clean_float(r.get('cash_and_equivalents'), default=0.0)
    net_debt = total_debt - cash

    # [ISSUE 02] หาก FCF <= 0 ไม่สร้างมูลค่าสมมติ แต่ให้ DCF เป็น None
    if fcf_base > 0 and (wacc - g) > 0:
        dcf_equity = ((fcf_base * (1 + near_term_growth)) / (wacc - g)) - net_debt
        raw_dcf_fair_value = (dcf_equity / shares) if (dcf_equity > 0 and shares > 0) else None
    else:
        raw_dcf_fair_value = None

    # [ISSUE 02] หาก EPS <= 0 ไม่สร้างมูลค่าสมมติ แต่ให้ P/E Fair Value เป็น None
    if eps > 0:
        raw_pe_fair_value = eps * target_pe
    else:
        raw_pe_fair_value = None

    # [ISSUE 03] คำนวณคะแนนย่อยแยกตามมิติอย่างแท้จริง
    dcf_score, dcf_is_clipped = calc_sub_score(raw_dcf_fair_value, current_price)
    pe_score, pe_is_clipped = calc_sub_score(raw_pe_fair_value, current_price)
    dcf_is_clipped = bool(dcf_is_clipped)
    pe_is_clipped = bool(pe_is_clipped)
    is_clipped = bool(dcf_is_clipped or pe_is_clipped)

    # คำนวณ Blended Fair Value
    fair_components = [(raw_dcf_fair_value, 0.55), (raw_pe_fair_value, 0.45)]
    valid_fair = [(v, w) for v, w in fair_components if v is not None]

    if not valid_fair:
        blended_fair = None
        mos = None
        valuation_status = 'NOT_RATED'
        val_score = 0.0
    else:
        total_w = sum(w for _, w in valid_fair)
        blended_fair = round(sum(v * w for v, w in valid_fair) / total_w, 2)
        mos = round((blended_fair - current_price) / blended_fair * 100, 1)
        valuation_status = 'OK' if len(valid_fair) == 2 else 'PARTIAL'
        # ถ่วงน้ำหนักคะแนนตามสัดส่วนโมเดลที่มีอยู่
        val_score = round(dcf_score * 0.55 + pe_score * 0.45, 1)

    # [ISSUE 04] ระบบประเมิน Confidence Level แบบ Risk Penalty System
    is_profitable = (eps > 0 and fcf_base > 0)
    if (not is_profitable) or valuation_status in ('NOT_RATED', 'NO_DATA'):
        confidence_level = 'Low'
    elif is_clipped:
        confidence_level = 'Medium'
    elif mos is not None and mos > 15:
        confidence_level = 'High'
    else:
        confidence_level = 'Medium'

    # สร้างข้อความแจ้งเตือน (Warning Message)
    warning_message = None
    if valuation_status == 'NOT_RATED':
        warning_message = 'ไม่สามารถประเมินมูลค่าได้เนื่องจากบริษัทมีผลการดำเนินงานขาดทุน (EPS และ/หรือ FCF ติดลบ)'
    elif valuation_status == 'PARTIAL':
        warning_message = 'ประเมินได้เพียงโมเดลเดียว (อีกโมเดลขาดทุนหรือไม่สามารถคำนวณได้) ควรใช้ความระมัดระวังเป็นพิเศษ'
    elif is_clipped:
        warning_message = 'ราคาประเมินดิบชนหรือทะลุกรอบปกติ (65%-185% ของราคาตลาด) ตัวเลข Fair Value ที่แสดงเป็นค่าดิบแท้จริง'

    pe_ratio_now = round(float(current_price / eps), 2) if eps > 0 else None
    book_value_per_share = clean_float(r.get('total_equity'), 0.0) / shares if shares else 0.0
    pb_ratio_now = round(float(current_price / book_value_per_share), 2) if book_value_per_share > 0 else None
    market_cap = round(current_price * shares / 1e6, 1)
    target_pb = 1.50

    safety_score = round(float(np.clip(50.0 + ((mos if mos is not None else 0.0) * 1.2), 10.0, 98.0)), 1) if mos is not None else 0.0

    wacc_pct = round(wacc * 100, 1)
    g_pct = round(g * 100, 1)
    fcf_g_pct = round(near_term_growth * 100, 1)

    return {
        # Core Valuation Metrics
        'valuation_score': val_score,
        'fair_value': blended_fair,
        'dcf_fair_value': round(raw_dcf_fair_value, 2) if raw_dcf_fair_value is not None else None,
        'pe_fair_value': round(raw_pe_fair_value, 2) if raw_pe_fair_value is not None else None,
        'raw_dcf_fair_value': round(raw_dcf_fair_value, 2) if raw_dcf_fair_value is not None else None,
        'raw_pe_fair_value': round(raw_pe_fair_value, 2) if raw_pe_fair_value is not None else None,
        'dcf_fair_value_raw': round(raw_dcf_fair_value, 2) if raw_dcf_fair_value is not None else None,
        'pe_fair_value_raw': round(raw_pe_fair_value, 2) if raw_pe_fair_value is not None else None,
        'margin_of_safety': mos,
        'pe_ratio': pe_ratio_now,
        'pb_ratio': pb_ratio_now,
        'market_cap_mb': market_cap,
        'eps': round(eps, 2),

        # WACC — ส่งครบทั้งชื่อคีย์ wacc, wacc_used และสตริง wacc_str
        'wacc': wacc_pct,
        'wacc_used': round(wacc * 100, 2),
        'wacc_pct': wacc_pct,
        'wacc_rate': wacc,
        'wacc_str': f"{wacc_pct:.1f}%",

        # Terminal Growth — ส่งครบทั้ง terminal, terminal_growth, terminal_growth_used
        'terminal': g_pct,
        'terminal_growth': g_pct,
        'terminal_growth_used': round(g * 100, 2),
        'terminal_g': g_pct,
        'terminal_g_used': round(g * 100, 2),
        'terminal_growth_rate': g,
        'g': g_pct,
        'g_used': round(g * 100, 2),
        'terminal_str': f"{g_pct:.1f}%",
        'terminal_growth_str': f"{g_pct:.1f}%",

        # Target P/E — ส่งครบทั้ง target, target_pe, target_pe_used
        'target': target_pe,
        'target_pe': target_pe,
        'target_pe_used': target_pe,
        'pe_target': target_pe,
        'pe_target_used': target_pe,
        'target_p_e': target_pe,
        'target_pe_ratio': target_pe,
        'target_pe_str': f"{target_pe:.1f}x",
        'target_pb': target_pb,

        # FCF Growth (Yr 1) — ส่งครบทั้ง fcf_growth, fcf_growth_assumed, fcf_growth_yr1
        'fcf_growth': fcf_g_pct,
        'fcf_growth_assumed': round(near_term_growth * 100, 2),
        'fcf_growth_yr1': fcf_g_pct,
        'fcf_growth_y1': fcf_g_pct,
        'fcf_growth_1': fcf_g_pct,
        'near_term_growth': fcf_g_pct,
        'fcf_growth_str': f"{fcf_g_pct:.1f}%",
        'fcf_base': round(fcf_base, 1),
        'fcf_base_used': round(fcf_base, 1),

        # Flags & Sub-scores (ISSUE 01 & 03)
        'dcf_is_clipped': dcf_is_clipped,
        'pe_is_clipped': pe_is_clipped,
        'is_clipped': is_clipped,
        'pe_score': pe_score,
        'dcf_score': dcf_score,
        'intrinsic_score': dcf_score,
        'relative_score': pe_score,
        'safety_score': safety_score,

        # Fallback / Estimate Flags
        'dcf_is_estimate': (fcf_base <= 0),
        'pe_is_estimate': (eps <= 0),
        'valuation_status': valuation_status,
        'confidence_level': confidence_level,
        'valuation_methodology_note': VALUATION_METHODOLOGY_NOTE,
        'warning_message': warning_message,
        'book_value_per_share': round(book_value_per_share, 2),
        'shares_outstanding': shares
    }


def build_fair_value_yearly(df_fin_ticker, df_price_ticker, ticker):
    """
    คำนวณ Fair Value ย้อนหลังแต่ละปี (2023-2025) อิงงบการเงินจริงของปีนั้น
    เทียบกับราคาปิดสิ้นปีจริง เพื่อนำไปวาดกราฟ Historical Fair Value vs Price
    """
    rows = []
    if df_fin_ticker is None or df_fin_ticker.empty or df_price_ticker is None or df_price_ticker.empty:
        return pd.DataFrame(rows)

    price_df = df_price_ticker.copy()
    price_df['date'] = pd.to_datetime(price_df['date'])
    for yr in sorted(df_fin_ticker['year'].unique()):
        fin_upto = df_fin_ticker[df_fin_ticker['year'] <= yr]
        if fin_upto.empty:
            continue
        year_end_prices = price_df[price_df['date'] <= f'{yr}-12-31']
        if year_end_prices.empty:
            continue
        year_end_price = clean_float(year_end_prices.sort_values('date').iloc[-1]['close'])
        try:
            val = calculate_valuation_module(fin_upto, year_end_price, ticker)
            rows.append({
                'year': int(yr),
                'price': round(year_end_price, 2),
                'fair_value': val.get('fair_value')
            })
        except Exception:
            continue
    return pd.DataFrame(rows)
