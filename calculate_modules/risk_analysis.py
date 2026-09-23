"""
calculate_modules/risk_analysis.py
--------------------------------------
สูตรคำนวณโมดูล "Risk Analysis" (🛡️) — คู่กับ pages_content/risk_analysis.py

=== DATA CONTRACT (ห้ามลบ/เปลี่ยนชื่อ key เดิม) ===
คืนค่า dict ที่มี key เดิมครบ:
    risk_score, volatility, volatility_calc, max_drawdown, var_95, beta, sharpe_ratio, sortino_ratio
และ key เสริม:
    cvar_95, psr, recovery_days, risk_free_rate_annual,
    risk_dim_tail, risk_dim_drawdown, risk_dim_volatility, risk_dim_market, risk_dim_quality,
    beta_verified, beta_note
"""

import math
import numpy as np
import pandas as pd
from calculate_modules.common import clean_float

# อัตราดอกเบี้ยปลอดความเสี่ยงรายปี (BOT Policy Rate ประมาณการ 2023-2025)
RISK_FREE_RATE_ANNUAL = 0.02

# น้ำหนักถ่วงคะแนนความเสี่ยง (ห้ามเปลี่ยนโดยไม่ได้รับอนุมัติ)
RISK_WEIGHT_TAIL = 0.30
RISK_WEIGHT_DRAWDOWN = 0.25
RISK_WEIGHT_VOLATILITY = 0.20
RISK_WEIGHT_MARKET = 0.15
RISK_WEIGHT_QUALITY = 0.10

BETA_VERIFIED = False
BETA_UNVERIFIED_NOTE = "⚠️ ยังไม่ยืนยันแหล่งที่มา"


def _clean_price_series(df, price_col='close'):
    """ตัดแถวที่ราคาปิดเป็น NaN/ว่างทิ้ง ป้องกันราคา 0 บาท (F-7a)"""
    out = df.copy()
    out[price_col] = pd.to_numeric(out[price_col], errors='coerce')
    out = out.dropna(subset=[price_col]).reset_index(drop=True)
    return out


def _compute_cvar(returns, confidence=0.95):
    """CVaR / Expected Shortfall 95% (Historical Simulation)"""
    r = returns.dropna()
    if len(r) < 20:
        return None
    cutoff = np.percentile(r, (1 - confidence) * 100)
    tail = r[r <= cutoff]
    if tail.empty:
        return None
    return round(float(abs(tail.mean()) * 100), 2)


def _compute_var_historical(returns, confidence=0.95):
    """VaR 95% (Historical Simulation) ให้ใช้วิธีเดียวกับ CVaR (แก้ F-6)"""
    r = returns.dropna()
    if len(r) < 20:
        return None
    cutoff = np.percentile(r, (1 - confidence) * 100)
    return round(float(abs(cutoff) * 100), 2)


def _compute_psr(returns, sr_benchmark=0.0):
    """Probabilistic Sharpe Ratio (%)"""
    r = returns.dropna()
    n = len(r)
    if n < 30 or r.std() == 0:
        return None

    sr_hat = r.mean() / r.std()
    skew = r.skew()
    kurt = r.kurtosis() + 3  # ปรับเป็น Pearson kurtosis

    denom_sq = 1 - skew * sr_hat + ((kurt - 1) / 4) * (sr_hat ** 2)
    if denom_sq <= 0:
        return None
    denom = math.sqrt(denom_sq)

    z = (sr_hat - sr_benchmark) * math.sqrt(n - 1) / denom
    psr = 0.5 * (1 + math.erf(z / math.sqrt(2)))
    return round(float(psr) * 100, 1)


def _compute_recovery_days(df):
    """จำนวนวันปฏิทินที่ใช้ในการฟื้นตัวกลับสู่ยอดเดิมจากจุดต่ำสุดของ Max Drawdown"""
    if len(df) < 2:
        return None
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
    """บทลงโทษหากยังไม่ฟื้นตัวหรือใช้เวลาฟื้นตัวนาน (Heuristic ของทีม)"""
    if recovery_days is None:
        return 10.0
    if recovery_days > 365:
        return 7.0
    if recovery_days > 180:
        return 3.0
    return 0.0


def calculate_risk_module(df_price_ticker, risk_static_row):
    """คำนวณตัวชี้วัดความเสี่ยง 5 มิติของหุ้น 1 ตัว"""
    df = df_price_ticker.sort_values(by='date').reset_index(drop=True)
    df = _clean_price_series(df, 'close')

    # F-7b: ถ้าข้อมูลน้อยเกินไป คืนค่า None ไม่คืน 45 หรือ NaN ปลอม
    if len(df) < 2:
        return {
            'risk_score': None, 'volatility': None, 'volatility_calc': None,
            'max_drawdown': None, 'var_95': None, 'beta': 1.0,
            'sharpe_ratio': None, 'sortino_ratio': None, 'cvar_95': None,
            'psr': None, 'recovery_days': None,
            'risk_free_rate_annual': RISK_FREE_RATE_ANNUAL,
            'risk_dim_tail': None, 'risk_dim_drawdown': None,
            'risk_dim_volatility': None, 'risk_dim_market': None,
            'risk_dim_quality': None, 'beta_verified': BETA_VERIFIED,
            'beta_note': BETA_UNVERIFIED_NOTE,
        }

    df['returns'] = df['close'].pct_change()
    daily_vol = df['returns'].std()
    annual_vol_calc = daily_vol * np.sqrt(252) * 100

    cum_max = df['close'].cummax()
    drawdown = (df['close'] - cum_max) / cum_max
    max_dd_calc = abs(drawdown.min()) * 100

    if risk_static_row is not None and not risk_static_row.empty:
        beta = clean_float(risk_static_row.iloc[0].get('beta'), default=1.0)
        annual_vol = clean_float(risk_static_row.iloc[0].get('volatility_pct'), default=annual_vol_calc)
        # แก้ F-3: บังคับใช้ค่า Drawdown จริงจากราคา แทนค่า -29.36% ที่ซ้ำกันในไฟล์
        max_dd = max_dd_calc
    else:
        beta = 1.0
        annual_vol = annual_vol_calc
        max_dd = max_dd_calc

    # F-6: VaR และ CVaR ใช้ Historical Simulation ร่วมกัน
    var_95 = _compute_var_historical(df['returns'], confidence=0.95)
    cvar_95 = _compute_cvar(df['returns'], confidence=0.95)

    # Sharpe และ Sortino Ratio หัก Risk-free Rate จริง
    rf_daily = RISK_FREE_RATE_ANNUAL / 252
    excess_returns = df['returns'] - rf_daily

    if pd.isna(daily_vol) or len(df['returns'].dropna()) < 2:
        sharpe = None
    elif daily_vol > 0:
        sharpe = round(float((excess_returns.mean() * 252) / (daily_vol * np.sqrt(252))), 2)
    else:
        sharpe = 0.0

    # F-8ก: Downside Deviation ตามสูตรสากล
    downside_diff = np.minimum(0, df['returns'] - rf_daily).dropna()
    if len(downside_diff) > 1:
        downside_deviation = np.sqrt(np.mean(downside_diff ** 2))
    else:
        downside_deviation = daily_vol

    if pd.isna(downside_deviation) or len(downside_diff) < 2:
        sortino = None
    elif downside_deviation > 0:
        sortino = round(float((excess_returns.mean() * 252) / (downside_deviation * np.sqrt(252))), 2)
    else:
        sortino = 0.0

    psr = _compute_psr(df['returns'], sr_benchmark=0.0)
    recovery_days = _compute_recovery_days(df)

    # รวมคะแนน 5 มิติ
    tail_input = cvar_95 if cvar_95 is not None else (var_95 if pd.notna(var_95) else None)
    tail_dim = float(np.clip(tail_input * 10, 5, 95)) if tail_input is not None else None
    drawdown_dim = (float(np.clip(max_dd * 1.5 + _recovery_penalty(recovery_days), 5, 95))
                    if pd.notna(max_dd) else None)
    volatility_dim = float(np.clip(annual_vol * 1.3, 5, 95)) if pd.notna(annual_vol) else None
    market_dim = float(np.clip(beta * 40, 5, 95)) if pd.notna(beta) else None
    quality_dim = float(np.clip(100 - psr, 5, 95)) if psr is not None else 50.0

    dims = {
        'tail': (tail_dim, RISK_WEIGHT_TAIL),
        'drawdown': (drawdown_dim, RISK_WEIGHT_DRAWDOWN),
        'volatility': (volatility_dim, RISK_WEIGHT_VOLATILITY),
        'market': (market_dim, RISK_WEIGHT_MARKET),
        'quality': (quality_dim, RISK_WEIGHT_QUALITY),
    }

    if any(value is None for value, _ in dims.values()):
        risk_score = None
    else:
        risk_index = sum(value * weight for value, weight in dims.values())
        risk_score = round(float(np.clip(100 - risk_index, 25, 92)), 1)

    return {
        # คีย์เดิมตาม Data Contract
        'risk_score': risk_score,
        'volatility': round(float(annual_vol), 1) if pd.notna(annual_vol) else None,
        'volatility_calc': round(float(annual_vol_calc), 1) if pd.notna(annual_vol_calc) else None,
        'max_drawdown': round(float(max_dd), 1) if pd.notna(max_dd) else None,
        'var_95': round(float(var_95), 2) if pd.notna(var_95) else None,
        'beta': round(float(beta), 2),
        'sharpe_ratio': sharpe,
        'sortino_ratio': sortino,
        # คีย์เสริมแบบสเกลาร์ (แก้ F-1 บันทึก SQLite ผ่าน)
        'cvar_95': cvar_95,
        'psr': psr,
        'recovery_days': recovery_days,
        'risk_free_rate_annual': RISK_FREE_RATE_ANNUAL,
        'risk_dim_tail': round(tail_dim, 1) if tail_dim is not None else None,
        'risk_dim_drawdown': round(drawdown_dim, 1) if drawdown_dim is not None else None,
        'risk_dim_volatility': round(volatility_dim, 1) if volatility_dim is not None else None,
        'risk_dim_market': round(market_dim, 1) if market_dim is not None else None,
        'risk_dim_quality': round(quality_dim, 1) if quality_dim is not None else None,
        'beta_verified': BETA_VERIFIED,
        'beta_note': BETA_UNVERIFIED_NOTE if not BETA_VERIFIED else None,
    }


def build_risk_rolling_history(df_price_ticker):
    """คำนวณ rolling 30 วันของ Volatility และ Drawdown"""
    df = df_price_ticker.sort_values(by='date').reset_index(drop=True)
    df = _clean_price_series(df, 'close')
    if len(df) < 30:
        return pd.DataFrame(columns=['date', 'rolling_vol_30d', 'drawdown_pct'])

    df['returns'] = df['close'].pct_change()
    df['rolling_vol_30d'] = df['returns'].rolling(30).std() * np.sqrt(252) * 100
    cum_max = df['close'].cummax()
    df['drawdown_pct'] = (df['close'] - cum_max) / cum_max * 100

    out = df[['date', 'rolling_vol_30d', 'drawdown_pct']].dropna(subset=['rolling_vol_30d']).copy()
    out = out.set_index('date').resample('W').last().dropna().reset_index()
    return out
