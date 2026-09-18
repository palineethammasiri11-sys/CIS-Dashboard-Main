"""
calculate_modules/risk_analysis.py
--------------------------------------
สูตรคำนวณโมดูล "Risk Analysis" (🛡️) — คู่กับ pages_content/risk_analysis.py

=== DATA CONTRACT (ห้ามลบ/เปลี่ยนชื่อ key เดิมโดยไม่แจ้งทีม — เพิ่ม key ใหม่ได้อิสระ) ===

calculate_risk_module(df_price_ticker, risk_static_row) รับ:
    df_price_ticker  : pd.DataFrame ราคาหุ้น 1 ตัว เรียงตามวันที่ (ต้องมีคอลัมน์ date, close)
    risk_static_row  : pd.DataFrame แถวเดียว (หรือ None) จากตาราง stock_risk_static

คืนค่าเป็น dict ที่ต้องมี key เดิมครบ:
    risk_score, volatility, volatility_calc, max_drawdown, var_95, beta, sharpe_ratio, sortino_ratio

--- key ใหม่ ---
    cvar_95        : float หรือ None — Conditional VaR / Expected Shortfall 95% (Historical Simulation)
    psr            : float หรือ None — Probabilistic Sharpe Ratio (%)
    recovery_days  : int หรือ None   — จำนวนวันฟื้นตัวจากจุดต่ำสุดของ Max Drawdown กลับสู่จุดสูงสุดเดิม
    risk_free_rate_annual : float    — อัตราดอกเบี้ยปลอดความเสี่ยงที่ใช้
    risk_score_breakdown  : dict     — คะแนนย่อยแต่ละมิติ (0-100, ยิ่งสูง=ยิ่งเสี่ยง) ก่อนถ่วงน้ำหนักรวม
                             {'tail', 'drawdown', 'volatility', 'market', 'quality'} — ใช้ debug/แสดงผลเพิ่มเติมได้

=== CHANGELOG ===

รอบที่ 1 (แก้บั๊ก):
1. แก้ CVaR ที่เคยแสดงค่าเท่ากับ VaR เป๊ะ (ผิดตามนิยาม) → เปลี่ยนเป็น Historical Expected Shortfall จริง
   อ้างอิง: Jorion (2007), "Value at Risk"
2. แก้ Sharpe/Sortino ให้หัก Risk-free Rate จริง (RISK_FREE_RATE_ANNUAL = 2.0%, อิงอัตราดอกเบี้ยนโยบาย
   ธปท. เฉลี่ยช่วง 2023-2025 — ดูที่มาด้านล่าง) และเปลี่ยน Sortino ให้ใช้ MAR = Risk-free Rate แทนเลข 0
   อ้างอิง: Sortino, "Mean-Semivariance Behavior"
3. เพิ่ม Probabilistic Sharpe Ratio (PSR) — อ้างอิง Bailey & López de Prado (2012)
4. เพิ่ม Recovery Duration — อ้างอิง arXiv:1403.8125 (2014)

รอบที่ 2 (จัดน้ำหนักคะแนน risk_score ใหม่ + ตัด Stress Test ที่ไม่มีข้อมูลรองรับออก):

5. **ปรับ risk_score ให้ถ่วงน้ำหนักตาม "น้ำหนักของหลักฐาน" ในงานวิจัยที่แนบมาทั้งชุด** แทนตัวเลข
   45%/35%/20% เดิมที่ไม่มีที่มา (เป็น custom heuristic ล้วนๆ) ตรรกะ:
     - งานวิจัย 6 ใน 9 เล่มที่แนบมาสรุปตรงกันว่า "ความเสี่ยงขาลง/tail risk" สำคัญกว่า
       "ความผันผวนแบบสมมาตรธรรมดา" ในการสะท้อนความเสี่ยงที่นักลงทุนเผชิญจริง
     - จึงเพิ่มน้ำหนักให้ Tail Risk (CVaR, Jorion 2007) และ Drawdown+Recovery (arXiv 2014)
       รวมกัน 55% และลดน้ำหนัก Volatility แบบสมมาตรเหลือ 20% (จากเดิม 45%)
     - เพิ่ม Market Risk (Beta) 15% เข้ามาในสูตรเป็นครั้งแรก (เดิมไม่เคยรวมอยู่ใน risk_score เลย
       ทั้งที่ Beta ถูกใช้แสดงผลแยกอยู่แล้วในหน้า UI) — ให้น้ำหนักปานกลางเพราะงานวิจัย Fama-French
       5-Factor (2015) และ Downside Beta (2006) ชี้ว่า Beta ตัวเดียวไม่พอจะอธิบายความเสี่ยงทั้งหมด
     - เพิ่ม Return Quality (PSR) 10% เป็นตัวเช็คเสริมความน่าเชื่อถือของผลตอบแทนที่ปรับความเสี่ยงแล้ว
   ⚠️ **สิ่งที่ต้องเข้าใจให้ชัด:** นี่คือการจัด "ลำดับความสำคัญเชิงคุณภาพ" ตามน้ำหนักหลักฐานในวรรณกรรม
   ไม่ใช่ตัวเลขที่งานวิจัยพิสูจน์ทางสถิติว่าถูกต้องที่สุด ตัวเลข 30/25/20/15/10% ยังเป็นการคาลิเบรต
   ของผู้พัฒนาอยู่ดี (เพียงแต่ตอนนี้มีเหตุผลรองรับทุกตัวเลขแล้ว ต่างจากเดิมที่ไม่มีที่มาเลย) ถ้าต้องการ
   ความเข้มงวดทางสถิติจริง ต้อง backtest เทียบผลตอบแทน/ความเสี่ยงจริงย้อนหลังถึงจะยืนยันได้
   ตัวคูณแปลงหน่วย (×40 สำหรับ Beta, ×1.3 สำหรับ Volatility, ×1.5 สำหรับ Max Drawdown) **ไม่ได้เปลี่ยน**
   เพราะหน้าที่ของมันคือแปลงหน่วยดิบให้อยู่ในสเกล 0-100 เท่ากันเท่านั้น ไม่ใช่ตัวแทนน้ำหนักความสำคัญ
   งานวิจัยที่แนบมาไม่ได้พูดถึงตัวคูณเหล่านี้เลย จึงไม่มีอะไรให้ปรับอ้างอิงเพิ่ม

6. **ตัด Stress Test (rate_impact, recession_impact) ออกจากระบบทั้งหมดตามคำขอของทีม** เพราะทีมไม่ต้องการ
   ดึงข้อมูลมหภาค (CPI/อัตราดอกเบี้ย) เพิ่มเข้าระบบ ส่วนที่เหลืออยู่คือ "Market Crash Impact" (Beta-implied)
   ซึ่งมีทฤษฎี CAPM รองรับโดยตรง (Beta × market shock) ยังคงมีอยู่ในหน้า UI ตามเดิม — ดู UI PATCH

=== สิ่งที่ "ทำไม่ได้" ในเวอร์ชันนี้ (เหมือนเดิม ยังไม่เปลี่ยนแปลง) ===

- Downside Beta (β⁻) และ Fama-French 5-Factor Model ยังทำไม่ได้ เพราะไม่มีข้อมูลดัชนีตลาดอ้างอิง
  (SET Index) หรือ factor data (Size/Value/Profitability/Investment) ในระบบปัจจุบัน
"""

import math

import numpy as np
import pandas as pd

from calculate_modules.common import clean_float

# อัตราดอกเบี้ยปลอดความเสี่ยง (Risk-free Rate) รายปี
# ที่มา: อัตราดอกเบี้ยนโยบาย ธนาคารแห่งประเทศไทย (BOT Policy Rate) ช่วง 2023-2025
#   - ปรับขึ้นแตะ 2.50% ช่วง ก.ย. 2023 - ก.ย. 2024 (สิ้นสุดวงจรขึ้นดอกเบี้ยหลังโควิด)
#   - ทยอยลดลงระหว่างปี 2025 เหลือประมาณ 1.00-1.50% ช่วงปลายปี
#   - ค่าเฉลี่ยโดยประมาณตลอดช่วง 2023-2025 ≈ 2.0% (ใช้ค่านี้เป็นตัวแทน)
# ⚠️ เป็นค่าประมาณจากข้อมูลสาธารณะ ไม่ใช่ค่าเฉลี่ยแบบถ่วงน้ำหนักรายวันที่คำนวณจริง
RISK_FREE_RATE_ANNUAL = 0.02

# น้ำหนักถ่วงของแต่ละมิติความเสี่ยงใน risk_score (ดูที่มา/เหตุผลใน CHANGELOG รอบที่ 2 ด้านบน)
RISK_WEIGHT_TAIL = 0.30        # CVaR 95% (Jorion, 2007)
RISK_WEIGHT_DRAWDOWN = 0.25    # Max Drawdown + Recovery Duration (arXiv:1403.8125)
RISK_WEIGHT_VOLATILITY = 0.20  # Annualized Volatility (สมมาตร — ลดน้ำหนักตามที่วรรณกรรมวิจารณ์)
RISK_WEIGHT_MARKET = 0.15      # Beta / Market Systematic Risk (CAPM, จำกัดตาม 5-Factor literature)
RISK_WEIGHT_QUALITY = 0.10     # Return Quality จาก PSR (Bailey & López de Prado, 2012)


def _compute_cvar(returns, confidence=0.95):
    """CVaR / Expected Shortfall (Historical Simulation) — Jorion (2007)"""
    r = returns.dropna()
    if len(r) < 20:
        return None
    cutoff = np.percentile(r, (1 - confidence) * 100)
    tail = r[r <= cutoff]
    if tail.empty:
        return None
    return round(float(abs(tail.mean()) * 100), 2)


def _compute_psr(returns, sr_benchmark=0.0):
    """Probabilistic Sharpe Ratio — Bailey & López de Prado (2012)"""
    r = returns.dropna()
    n = len(r)
    if n < 30 or r.std() == 0:
        return None

    sr_hat = r.mean() / r.std()
    skew = r.skew()
    kurt = r.kurtosis() + 3  # ปรับ excess kurtosis (pandas) กลับเป็น kurtosis ปกติ (Normal = 3)

    denom_sq = 1 - skew * sr_hat + ((kurt - 1) / 4) * sr_hat ** 2
    if denom_sq <= 0:
        return None
    denom = math.sqrt(denom_sq)

    z = (sr_hat - sr_benchmark) * math.sqrt(n - 1) / denom
    psr = 0.5 * (1 + math.erf(z / math.sqrt(2)))
    return round(float(psr) * 100, 1)


def _compute_recovery_days(df):
    """Recovery Duration — arXiv:1403.8125. คืน None ถ้ายังไม่ฟื้นตัว ณ วันที่ข้อมูลล่าสุด"""
    cum_max = df['close'].cummax()
    drawdown = (df['close'] - cum_max) / cum_max
    if drawdown.isna().all():
        return None

    trough_idx = drawdown.idxmin()
    peak_value = cum_max.loc[trough_idx]
    trough_date = df.loc[trough_idx, 'date']

    after_trough = df[df['date'] > trough_date]
    recovered = after_trough[after_trough['close'] >= peak_value]
    if recovered.empty:
        return None
    recovery_date = recovered.iloc[0]['date']
    return int((recovery_date - trough_date).days)


def _recovery_penalty(recovery_days):
    """แปลง Recovery Duration เป็นคะแนนโทษเพิ่มให้มิติ Drawdown (ยิ่งฟื้นตัวช้า/ยังไม่ฟื้น ยิ่งเสี่ยงเชิงโครงสร้างมากกว่า Max DD บอกเพียงลำพัง)"""
    if recovery_days is None:
        return 10.0  # ยังไม่ฟื้นตัวเลย ณ วันที่ข้อมูลล่าสุด — ความเสี่ยงเชิงโครงสร้างสูงสุด
    if recovery_days > 365:
        return 7.0
    if recovery_days > 180:
        return 3.0
    return 0.0


def calculate_risk_module(df_price_ticker, risk_static_row):
    """Module 5: Risk Analysis"""
    df = df_price_ticker.sort_values(by='date').reset_index(drop=True).copy()
    df['close'] = df['close'].apply(clean_float)
    df['returns'] = df['close'].pct_change()

    daily_vol = df['returns'].std()
    annual_vol_calc = daily_vol * np.sqrt(252) * 100

    cum_max = df['close'].cummax()
    drawdown = (df['close'] - cum_max) / cum_max
    max_dd_calc = abs(drawdown.min()) * 100

    var_95 = 1.645 * daily_vol * 100
    cvar_95 = _compute_cvar(df['returns'], confidence=0.95)

    if risk_static_row is not None and not risk_static_row.empty:
        beta = clean_float(risk_static_row.iloc[0].get('beta'), default=1.0)
        annual_vol = clean_float(risk_static_row.iloc[0].get('volatility_pct'), default=annual_vol_calc)
        max_dd = abs(clean_float(risk_static_row.iloc[0].get('max_drawdown_pct'), default=max_dd_calc))
    else:
        beta = 1.0
        annual_vol = annual_vol_calc
        max_dd = max_dd_calc

    # Sharpe/Sortino — หัก Risk-free Rate จริง
    rf_daily = RISK_FREE_RATE_ANNUAL / 252
    excess_returns = df['returns'] - rf_daily
    sharpe = round(float((excess_returns.mean() * 252) / (daily_vol * np.sqrt(252))), 2) if daily_vol > 0 else 0.0

    downside_returns = df['returns'][df['returns'] < rf_daily]
    downside_std = downside_returns.std() if len(downside_returns) > 1 else daily_vol
    sortino = round(float((excess_returns.mean() * 252) / (downside_std * np.sqrt(252))), 2) if downside_std > 0 else 0.0

    psr = _compute_psr(df['returns'], sr_benchmark=0.0)
    recovery_days = _compute_recovery_days(df)

    # ---------- risk_score: คะแนนรวมแบบถ่วงน้ำหนักใหม่ (ดู CHANGELOG รอบที่ 2) ----------
    tail_dim = float(np.clip((cvar_95 if cvar_95 is not None else var_95) * 10, 5, 95))
    drawdown_dim = float(np.clip(max_dd * 1.5 + _recovery_penalty(recovery_days), 5, 95))
    volatility_dim = float(np.clip(annual_vol * 1.3, 5, 95))
    market_dim = float(np.clip(beta * 40, 5, 95))
    quality_dim = float(np.clip(100 - psr, 5, 95)) if psr is not None else 50.0

    risk_index = (
        tail_dim * RISK_WEIGHT_TAIL +
        drawdown_dim * RISK_WEIGHT_DRAWDOWN +
        volatility_dim * RISK_WEIGHT_VOLATILITY +
        market_dim * RISK_WEIGHT_MARKET +
        quality_dim * RISK_WEIGHT_QUALITY
    )
    risk_score = round(float(np.clip(100 - risk_index, 25, 92)), 1)

    return {
        # --- key เดิม ---
        'risk_score': risk_score,
        'volatility': round(float(annual_vol), 1),
        'volatility_calc': round(float(annual_vol_calc), 1),
        'max_drawdown': round(float(max_dd), 1),
        'var_95': round(float(var_95), 2),
        'beta': round(float(beta), 2),
        'sharpe_ratio': sharpe,
        'sortino_ratio': sortino,
        # --- key ใหม่ ---
        'cvar_95': cvar_95,
        'psr': psr,
        'recovery_days': recovery_days,
        'risk_free_rate_annual': RISK_FREE_RATE_ANNUAL,
        'risk_score_breakdown': {
            'tail': round(tail_dim, 1),
            'drawdown': round(drawdown_dim, 1),
            'volatility': round(volatility_dim, 1),
            'market': round(market_dim, 1),
            'quality': round(quality_dim, 1),
        },
    }


def build_risk_rolling_history(df_price_ticker):
    """คำนวณ rolling 30 วัน ของ Volatility (annualized) และ Drawdown จากราคาปิดจริง (ไม่เปลี่ยนแปลง)"""
    df = df_price_ticker.sort_values(by='date').copy()
    df['close'] = df['close'].apply(clean_float)
    df['returns'] = df['close'].pct_change()

    df['rolling_vol_30d'] = df['returns'].rolling(30).std() * np.sqrt(252) * 100
    cum_max = df['close'].cummax()
    df['drawdown_pct'] = (df['close'] - cum_max) / cum_max * 100

    out = df[['date', 'rolling_vol_30d', 'drawdown_pct']].dropna(subset=['rolling_vol_30d']).copy()
    out = out.set_index('date').resample('W').last().dropna().reset_index()
    return out
