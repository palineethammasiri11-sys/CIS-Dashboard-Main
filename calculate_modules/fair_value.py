"""
calculate_modules/fair_value.py
----------------------------------
สูตรคำนวณโมดูล "Fair Value" (⚖️) — คู่กับ pages_content/fair_value.py

=== DATA CONTRACT (ห้ามลบ/เปลี่ยนชื่อ key โดยไม่แจ้งทีม — เพิ่ม key ใหม่ได้อิสระ) ===

calculate_valuation_module(df_fin_ticker, current_price, ticker) รับ:
    df_fin_ticker  : pd.DataFrame งบการเงินหุ้น 1 ตัว (คอลัมน์ต้องมี: year, net_income, eps,
                     free_cash_flow, total_liabilities, cash_and_equivalents, total_equity)
    current_price  : float ราคาล่าสุดของหุ้นตัวนั้น (มาจาก stock_daily_prices)
    ticker         : str   รหัสหุ้น (ใช้เลือก target P/E ตามกลุ่มอุตสาหกรรมจาก SECTOR_MAP)

คืนค่าเป็น dict ที่ต้องมี key:
    valuation_score, fair_value, dcf_fair_value, pe_fair_value,
    margin_of_safety, pe_ratio, pb_ratio, market_cap_mb, eps

build_fair_value_yearly(df_fin_ticker, df_price_ticker, ticker) คืน pd.DataFrame
    คอลัมน์ [year, price, fair_value] ใช้วาดกราฟ "Historical Fair Value vs Price"

ที่มาของสูตร: ดูละเอียดใน DATA_FORMULA_AUDIT.md หัวข้อ 2 (Module: Fair Value)
สรุปสั้น: DCF (Gordon Growth Model) และ P/E Relative Valuation เป็นแนวคิดมาตรฐาน
แต่ WACC=8.2%, Terminal Growth=2%, Target P/E (18x/22x) เป็นค่าคงที่ที่กำหนดเอง
และมีการ "หนีบ" (clip) ค่า DCF/PE Fair ให้อยู่ในช่วง 0.65x-1.85x ของราคาตลาดเสมอ — ดูรายละเอียดในไฟล์นี้บรรทัด DCF Model

⚠️ ตัวแปร SHARES_OUTSTANDING เป็นค่าคงที่ที่กรอกด้วยมือ ไม่ได้ดึงจาก Dataset
ถ้ามีข้อมูลจำนวนหุ้นจดทะเบียนจริงที่อัปเดตกว่านี้ ควรแก้ตรงนี้
"""

import numpy as np

from calculate_modules.common import clean_float, SECTOR_MAP

# จำนวนหุ้นจดทะเบียนจริงในตลาดหลักทรัพย์ (หน่วย: หุ้น) - ใช้คำนวณ Market Cap / มูลค่าต่อหุ้น
# ⚠️ ค่าคงที่กรอกด้วยมือ ควรตรวจสอบกับข้อมูลตลาดจริงเป็นระยะ
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


def calculate_valuation_module(df_fin_ticker, current_price, ticker):
    """Module 2: Fair Value (DCF + Relative PE, ใช้งบปีล่าสุดที่มีจริง)"""
    row_latest = df_fin_ticker.sort_values(by='year').iloc[[-1]]
    r = row_latest.iloc[0]

    shares = SHARES_OUTSTANDING.get(ticker, 1000000000)
    net_inc = clean_float(r.get('net_income'), default=1000.0)
    eps = clean_float(r.get('eps'), default=0.5)

    fcf = clean_float(r.get('free_cash_flow'), default=net_inc * 0.75)
    total_debt = clean_float(r.get('total_liabilities'), default=0.0)
    cash = clean_float(r.get('cash_and_equivalents'), default=0.0)
    net_debt = total_debt - cash

    # DCF Model (Gordon Growth Model / Perpetuity DCF)
    wacc, g = 0.082, 0.02
    dcf_equity = ((fcf * 1.05) / (wacc - g)) - net_debt
    dcf_fair = (dcf_equity / shares) if (dcf_equity > 0 and shares > 0) else current_price * 0.90

    # PE Relative Model
    target_pe = 22.0 if 'Technology' in SECTOR_MAP.get(ticker, '') else 18.0
    pe_fair = (eps * target_pe) if eps > 0 else current_price * 0.85

    # ⚠️ หนีบค่าไม่ให้ห่างจากราคาตลาดเกิน 65%-185% เสมอ (กันตัวเลขหลุดกรอบเวลา FCF/EPS ผิดปกติ)
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
