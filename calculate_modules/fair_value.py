"""
calculate_modules/fair_value.py
----------------------------------
สูตรคำนวณโมดูล "Fair Value" (⚖️) — คู่กับ pages_content/fair_value.py

=== DATA CONTRACT (ห้ามลบ/เปลี่ยนชื่อ key โดยไม่แจ้งทีม — เพิ่ม key ใหม่ได้อิสระ) ===

calculate_valuation_module(df_fin_ticker, current_price, ticker) รับ:
    df_fin_ticker  : pd.DataFrame งบการเงินหุ้น 1 ตัว (คอลัมน์ต้องมี: year, net_income, eps,
                     free_cash_flow, total_liabilities, cash_and_equivalents, total_equity)
    current_price  : float ราคาล่าสุดของหุ้นตัวนั้น (มาจาก stock_daily_prices)
    ticker         : str   รหัสหุ้น (ใช้เลือก target P/E และสมมติฐาน WACC/Growth ตามกลุ่มอุตสาหกรรมจาก SECTOR_MAP)

คืนค่าเป็น dict ที่ต้องมี key (เดิม — ไม่มีการลบ/เปลี่ยนชื่อ):
    valuation_score, fair_value, dcf_fair_value, pe_fair_value,
    margin_of_safety, pe_ratio, pb_ratio, market_cap_mb, eps

Key ใหม่ที่เพิ่มเข้ามา (v2 — สำหรับความโปร่งใส ใช้แสดงผลใน UI เท่านั้น ไม่กระทบ contract เดิม):
    wacc_used            : float % WACC ที่ใช้จริงสำหรับหุ้นตัวนี้ (ตอนนี้แยกตามกลุ่มอุตสาหกรรม)
    terminal_growth_used : float % Terminal Growth ที่ใช้จริง (แยกตามกลุ่มอุตสาหกรรม)
    fcf_growth_assumed   : float % อัตราเติบโต FCF ปีถัดไปที่สมมติ (ผูกกับ terminal growth ของกลุ่ม)
    fcf_base_used        : float FCF ฐานที่ใช้คำนวณ (ค่าเฉลี่ย FCF ย้อนหลังสูงสุด 2 ปี ไม่ใช่ปีล่าสุดปีเดียว)

build_fair_value_yearly(df_fin_ticker, df_price_ticker, ticker) คืน pd.DataFrame
    คอลัมน์ [year, price, fair_value] ใช้วาดกราฟ "Historical Fair Value vs Price"

=== v2 CHANGELOG (แก้ไขโดย Fair Value Owner — ดูสรุปเหตุผลเต็มในเอกสาร Word ที่แนบมาคู่กับ PR นี้) ===
1. WACC และ Terminal Growth เปลี่ยนจาก "ค่าคงที่เดียวทั้ง 8 หุ้น" เป็น "แยกตามกลุ่มอุตสาหกรรม" (SECTOR_MAP)
   - Technology & Telecomm (ADVANC, TRUE, THCOM): WACC 7.8% / g 2.0%  (ธุรกิจมั่นคง กระแสเงินสดสม่ำเสมอกว่า)
   - Electronic Components (DELTA, HANA, KCE, CCET): WACC 8.8% / g 1.5%  (วัฏจักรส่งออก/อัตราแลกเปลี่ยนผันผวนกว่า)
   - Commerce & Technology (JMART): WACC 9.2% / g 2.5%  (ธุรกิจเติบโตสูง ความเสี่ยงสูงกว่า)
   ยังเป็น 🟡 custom heuristic เหมือนเดิม (ไม่ได้คำนวณจาก CAPM+Beta จริง เพราะฟังก์ชันนี้ไม่ได้รับ Beta
   เป็น input ตาม Data Contract) แต่แยกตามกลุ่มแทนค่าเดียวทั้งหมด สมเหตุสมผลกว่าเดิม
2. FCF ฐานที่ใช้ใน DCF เปลี่ยนจาก "FCF ปีล่าสุดปีเดียว" เป็น "ค่าเฉลี่ย FCF ย้อนหลัง 2 ปีล่าสุด"
   เพื่อลดผลกระทบจากปีที่ FCF ผันผวนผิดปกติ (one-off) — เป็นวิธี normalize ที่ใช้กันทั่วไปในงาน DCF จริง
3. อัตราเติบโต FCF ปีถัดไป เปลี่ยนจาก "+5% คงที่ทุกหุ้น" เป็น "Terminal Growth ของกลุ่ม + 1.5%"
   ผูกสมมติฐานระยะสั้นกับระยะยาวให้สอดคล้องกันแทนที่จะเป็นตัวเลขลอยๆ ไม่มีที่มา
4. คงค่าตัวคูณ P/E เป้าหมาย (18x/22x), น้ำหนักผสม 55/45, การหนีบ (clip) ช่วง 0.65x-1.85x ของราคาตลาด,
   และ SHARES_OUTSTANDING ไว้เหมือนเดิมทั้งหมด — ไม่ได้อยู่ในขอบเขตงานรอบนี้ (ยังคง 🟡/⚠️ ตามที่ระบุใน
   DATA_FORMULA_AUDIT.md เดิม)

⚠️ ตัวแปร SHARES_OUTSTANDING เป็นค่าคงที่ที่กรอกด้วยมือ ไม่ได้ดึงจาก Dataset
ถ้ามีข้อมูลจำนวนหุ้นจดทะเบียนจริงที่อัปเดตกว่านี้ ควรแก้ตรงนี้
"""

import numpy as np

from calculate_modules.common import clean_float, SECTOR_MAP

# จำนวนหุ้นจดทะเบียนจริงในตลาดหลักทรัพย์ (หน่วย: หุ้น) - ใช้คำนวณ Market Cap / มูลค่าต่อหุ้น
# ⚠️ ค่าคงที่กรอกด้วยมือ ควรตรวจสอบกับข้อมูลตลาดจริงเป็นระยะ (ไม่ได้แก้ในรอบนี้ — นอกขอบเขตงาน)
SHARES_OUTSTANDING = {
    'ADVANC': 2974000000,
    'CCET':   10400000000,
    'DELTA':  12473000000,
    'HANA':   885000000,
    'JMART':  1450000000,
    'KCE':    1182000000,
    'THCOM':  1096000000,
    'TRUE':   34500000000
}

# WACC และ Terminal Growth แยกตามกลุ่มอุตสาหกรรม (v2 — เดิมเป็นค่าคงที่เดียว 8.2%/2.0% ทั้ง 8 หุ้น)
# ที่มา/เหตุผลของแต่ละค่า: ดูเอกสารสรุปการแก้ไข (Word) ที่แนบมาพร้อมกัน
SECTOR_WACC = {
    'Technology & Telecomm': 0.078,
    'Electronic Components': 0.088,
    'Commerce & Technology': 0.092,
}
SECTOR_TERMINAL_G = {
    'Technology & Telecomm': 0.020,
    'Electronic Components': 0.015,
    'Commerce & Technology': 0.025,
}
DEFAULT_WACC = 0.082          # fallback ถ้าเจอ sector ที่ไม่อยู่ใน SECTOR_MAP (กันโค้ดพังกรณีเพิ่มหุ้นใหม่)
DEFAULT_TERMINAL_G = 0.02
NEAR_TERM_GROWTH_PREMIUM = 0.015  # อัตราเติบโต FCF ปีถัดไป = terminal growth ของกลุ่ม + ค่านี้


def calculate_valuation_module(df_fin_ticker, current_price, ticker):
    """Module 2: Fair Value (DCF + Relative PE, ใช้งบปีล่าสุดที่มีจริง)"""
    fin_sorted = df_fin_ticker.sort_values(by='year')
    row_latest = fin_sorted.iloc[[-1]]
    r = row_latest.iloc[0]

    shares = SHARES_OUTSTANDING.get(ticker, 1000000000)
    net_inc = clean_float(r.get('net_income'), default=1000.0)
    eps = clean_float(r.get('eps'), default=0.5)

    # FCF ฐาน: ค่าเฉลี่ยย้อนหลังสูงสุด 2 ปีล่าสุด (แทนปีล่าสุดปีเดียว) เพื่อลด noise จากปีที่ผิดปกติ
    fcf_hist = fin_sorted['free_cash_flow'].apply(clean_float).tail(2)
    fcf_base = float(fcf_hist.mean()) if len(fcf_hist) > 0 else net_inc * 0.75
    if fcf_base == 0:
        fcf_base = net_inc * 0.75

    total_debt = clean_float(r.get('total_liabilities'), default=0.0)
    cash = clean_float(r.get('cash_and_equivalents'), default=0.0)
    net_debt = total_debt - cash

    # DCF Model (Gordon Growth Model / Perpetuity DCF) — WACC/g แยกตามกลุ่มอุตสาหกรรม
    sector = SECTOR_MAP.get(ticker, '')
    wacc = SECTOR_WACC.get(sector, DEFAULT_WACC)
    g = SECTOR_TERMINAL_G.get(sector, DEFAULT_TERMINAL_G)
    near_term_growth = g + NEAR_TERM_GROWTH_PREMIUM

    dcf_equity = ((fcf_base * (1 + near_term_growth)) / (wacc - g)) - net_debt
    dcf_fair = (dcf_equity / shares) if (dcf_equity > 0 and shares > 0) else current_price * 0.90

    # PE Relative Model (ไม่เปลี่ยนจากเดิม)
    target_pe = 22.0 if 'Technology' in sector else 18.0
    pe_fair = (eps * target_pe) if eps > 0 else current_price * 0.85

    # ⚠️ หนีบค่าไม่ให้ห่างจากราคาตลาดเกิน 65%-185% เสมอ (คงไว้เหมือนเดิม — ไม่ได้แก้ในรอบนี้)
    dcf_fair = np.clip(dcf_fair, current_price * 0.65, current_price * 1.85)
    pe_fair = np.clip(pe_fair, current_price * 0.65, current_price * 1.85)

    blended_fair = round(float((dcf_fair * 0.55) + (pe_fair * 0.45)), 2)
    mos = round(float(((blended_fair - current_price) / blended_fair) * 100), 1) if blended_fair > 0 else 0.0
    val_score = round(float(np.clip((mos + 20) * 1.4, 25, 95)), 1)

    pe_ratio_now = round(float(current_price / eps), 2) if eps > 0 else None
    book_value_per_share = clean_float(r.get('total_equity'), 0.0) / shares if shares else 0.0
    pb_ratio_now = round(float(current_price / book_value_per_share), 2) if book_value_per_share > 0 else None
    market_cap = round(current_price * shares / 1e6, 1)  # หน่วยล้านบาท

    return {
        'valuation_score': val_score,
        'fair_value': blended_fair,
        'dcf_fair_value': round(float(dcf_fair), 2),
        'pe_fair_value': round(float(pe_fair), 2),
        'margin_of_safety': mos,
        'pe_ratio': pe_ratio_now,
        'pb_ratio': pb_ratio_now,
        'market_cap_mb': market_cap,
        'eps': round(eps, 2),
        # --- key ใหม่ (v2) เพื่อความโปร่งใส ใช้แสดงผลใน UI ---
        'wacc_used': round(wacc * 100, 2),
        'terminal_growth_used': round(g * 100, 2),
        'fcf_growth_assumed': round(near_term_growth * 100, 2),
        'fcf_base_used': round(fcf_base, 1),
    }


def build_fair_value_yearly(df_fin_ticker, df_price_ticker, ticker):
    """คำนวณ Fair Value ย้อนหลังแต่ละปี (2023-2025) โดยใช้งบการเงินจริงของปีนั้น ๆ
    เทียบกับราคาปิดสิ้นปีจริง เพื่อวาดกราฟ Historical Fair Value vs Price แบบไม่ mock"""
    import pandas as pd
    rows = []
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
            rows.append({'year': int(yr), 'price': round(year_end_price, 2), 'fair_value': val['fair_value']})
        except Exception:
            continue
    return pd.DataFrame(rows)
