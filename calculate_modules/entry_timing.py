"""
calculate_modules/entry_timing.py
--------------------------------------------------------------------
Institutional Quantitative Framework (IKB v1.3) - Extended Data Contract

Changelog vs v1.2:
- FIX: k17 now compares price to an actual MA200 (rolling 200-bar SMA,
  or a precomputed 'MA200' column if present) instead of a 1-year-ago
  price lookback. The label shown in the UI ("ราคายืนเหนือเส้น MA200")
  now matches what is actually computed.
- FIX: pivot_point now uses the prior bar's High/Low + current price
  (classic pivot definition) instead of the 60-day rolling high/low
  (r1/s1), which was not a standard pivot point.
- FIX: RR reward target upgrades to r2 when price has already broken
  above r1, instead of collapsing to rr_score=0 on breakouts.
- Output dict keys are unchanged except: added 'ma200' /
  'ma200_available'. 'trend_available_count' / 'mom_available_count'
  are kept as-is; the UI has been fixed to read these exact names.
"""

import numpy as np
import pandas as pd

from calculate_modules.common import clean_float

MIN_BARS_FOR_1Y_TREND = 200


def _empty_result():
    return {
        'timing_score': 50.0, 'rsi': 50.0, 'macd': 0.0, 'adx': 20.0,
        'ema20': 0.0, 'ema50': 0.0, 'ma200': 0.0, 'trend_signal': 'NEUTRAL',
        'resistance_60d': 0.0, 'support_60d': 0.0, 'pivot_point': 0.0,
        'resistance_2': 0.0, 'support_2': 0.0, 'overall_signal': 'Neutral',
        'status_label': 'NEUTRAL', 'status_color': '#38BDF8',
        'action_th': 'แกว่งตัว รอดูสัญญาณยืนยัน', 'rr_ratio': 1.0,
        'trend_score': 0.0, 'mom_score': 0.0, 'rr_score': 0.0,
        'upside_pct': 0.0, 'downside_pct': 0.0, 'readiness': 'WAIT',
        'summary_text': 'ข้อมูลไม่เพียงพอสำหรับการประเมินเชิงลึก',
        'k15_ok': False, 'k16_ok': False, 'k17_ok': False,
        'k18_ok': False, 'k19_ok': False, 'k20_ok': False, 'k_rr_ok': False,
        'k15_available': False, 'k16_available': False, 'k17_available': False,
        'k18_available': False, 'k19_available': False, 'k20_available': False,
        'trend_available_count': 0, 'mom_available_count': 0,
        'data_completeness': 0.0,
    }


def classify_signal(total_score):
    if total_score >= 70:
        return dict(
            signal_legacy="BULLISH", overall_signal="BULLISH (Strong Buy)",
            status_label="STRONG BUY", status_color="#10B981",
            action_th="จังหวะซื้อได้เปรียบสูง", readiness="READY",
            summary_text="ราคายืนในโซนสะสมและโครงสร้างขาขึ้นแข็งแกร่ง พร้อมทยอยสะสม",
        )
    elif total_score >= 40:
        return dict(
            signal_legacy="NEUTRAL", overall_signal="NEUTRAL",
            status_label="NEUTRAL", status_color="#38BDF8",
            action_th="แกว่งตัว รอดูสัญญาณยืนยัน", readiness="WAIT",
            summary_text="แม้ราคาจะอยู่ในโซนที่น่าสนใจ แต่สัญญาณทางเทคนิคยังไม่ยืนยันการกลับตัว "
                         "ควรรอการยืนยันจากปริมาณซื้อขายและแนวโน้มราคา",
        )
    else:
        return dict(
            signal_legacy="BEARISH", overall_signal="BEARISH (Avoid)",
            status_label="BEARISH", status_color="#EF4444",
            action_th="ขาลง ควรหลีกเลี่ยง", readiness="WAIT",
            summary_text="แนวโน้มหลักยังเป็นขาลงและโมเมนตัมอ่อนแอ "
                         "หลีกเลี่ยงการเข้าลงทุนจนกว่าจะเกิดสัญญาณกลับตัวชัดเจน",
        )


def compute_price_levels(price, df_price_ticker, high_col, low_col):
    recent60 = df_price_ticker.tail(60)
    recent120 = df_price_ticker.tail(120)

    r1 = float(recent60[high_col].max()) if not recent60.empty else price * 1.05
    r2 = float(recent120[high_col].max()) if not recent120.empty else r1 * 1.05
    s1 = float(recent60[low_col].min()) if not recent60.empty else price * 0.95
    s2 = float(recent120[low_col].min()) if not recent120.empty else s1 * 0.95

    r2 = max(r2, r1)
    s2 = min(s2, s1)

    # Classic pivot point: prior bar's High/Low + current close, NOT the
    # 60-day rolling range. Using the 60-day high/low here previously
    # produced a value that looked like a pivot point but wasn't one.
    if len(df_price_ticker) >= 2:
        prev_bar = df_price_ticker.iloc[-2]
        prev_high = clean_float(prev_bar.get(high_col), default=price)
        prev_low = clean_float(prev_bar.get(low_col), default=price)
    else:
        prev_high = price
        prev_low = price
    pivot_point = round((prev_high + prev_low + price) / 3.0, 2)

    return round(r1, 2), round(r2, 2), round(s1, 2), round(s2, 2), pivot_point


def calculate_timing_module(df_price_ticker):
    if df_price_ticker is None or df_price_ticker.empty:
        return _empty_result()

    latest = df_price_ticker.iloc[-1]
    close_col = 'close' if 'close' in df_price_ticker.columns else 'Close'
    high_col = 'high' if 'high' in df_price_ticker.columns else 'High'
    low_col = 'low' if 'low' in df_price_ticker.columns else 'Low'

    price = clean_float(latest.get(close_col), default=10.0)

    ema20_raw = latest.get('EMA20')
    ema50_raw = latest.get('EMA50')
    rsi_raw = latest.get('RSI14')
    macd_raw = latest.get('MACD')
    adx_raw = latest.get('ADX')

    ema20_available = pd.notna(ema20_raw)
    ema50_available = pd.notna(ema50_raw)
    macd_available = pd.notna(macd_raw)
    adx_available = pd.notna(adx_raw)

    rsi = clean_float(rsi_raw, default=50.0)
    macd = clean_float(macd_raw, default=0.0)
    adx = clean_float(adx_raw, default=20.0)
    ema20 = clean_float(ema20_raw, default=price)
    ema50 = clean_float(ema50_raw, default=price)

    r1, r2, s1, s2, pivot_point = compute_price_levels(price, df_price_ticker, high_col, low_col)

    # --- RR: reward target upgrades to r2 once price has broken above r1,
    # so a breakout no longer collapses rr_score to 0. ---
    reward_target = r2 if price >= r1 else r1
    downside_risk = price - s2
    upside_reward = reward_target - price

    rr_ratio = round(upside_reward / downside_risk, 2) if (downside_risk > 0 and upside_reward > 0) else 0.0
    upside_pct = round((upside_reward / price) * 100, 1) if price > 0 else 0.0
    downside_pct = round((downside_risk / price) * 100, 1) if price > 0 else 0.0

    # --- Trend pillar (40 pts): k15 short-term, k16 medium-term, k17 long-term ---
    k15_ok = bool(price > ema20) if ema20_available else False
    k16_ok = bool(ema20 > ema50) if (ema20_available and ema50_available) else False

    # k17: real MA200 comparison. Prefer a precomputed 'MA200' column if the
    # data pipeline supplies one; otherwise fall back to a rolling 200-bar
    # SMA computed here. This replaces the old "price vs. 1-year-ago price"
    # proxy, which did not match the "ราคายืนเหนือเส้น MA200" label shown in the UI.
    ma200_col = 'MA200' if 'MA200' in df_price_ticker.columns else None
    if ma200_col is not None and pd.notna(latest.get(ma200_col)):
        ma200 = clean_float(latest.get(ma200_col), default=price)
        ma200_available = True
    elif len(df_price_ticker) >= MIN_BARS_FOR_1Y_TREND:
        ma200 = float(df_price_ticker[close_col].tail(MIN_BARS_FOR_1Y_TREND).mean())
        ma200_available = True
    else:
        ma200 = price
        ma200_available = False

    k17_available = ma200_available
    k17_ok = bool(price > ma200) if k17_available else False

    trend_avail = [ema20_available, (ema20_available and ema50_available), k17_available]
    trend_pass = [k15_ok, k16_ok, k17_ok]
    n_trend_available = sum(trend_avail)
    trend_score = round(
        sum(p for p, a in zip(trend_pass, trend_avail) if a) * (40.0 / n_trend_available), 1
    ) if n_trend_available > 0 else 0.0

    # --- Momentum pillar (30 pts): k18 MACD, k19 ADX, k20 Volume ---
    k18_ok = bool(macd > 0) if macd_available else False
    k19_ok = bool(adx >= 25.0) if adx_available else False

    vol_col = next((v for v in ['volume', 'Volume', 'vol', 'Vol'] if v in df_price_ticker.columns), None)
    k20_available = False
    k20_ok = False
    if vol_col is not None and len(df_price_ticker) >= 20:
        vol_avg20 = float(df_price_ticker[vol_col].tail(20).mean())
        vol_last = float(df_price_ticker[vol_col].iloc[-1])
        if pd.notna(vol_avg20) and pd.notna(vol_last):
            k20_available = True
            k20_ok = bool(vol_last >= vol_avg20)

    mom_avail = [macd_available, adx_available, k20_available]
    mom_pass = [k18_ok, k19_ok, k20_ok]
    n_mom_available = sum(mom_avail)
    mom_score = round(
        sum(p for p, a in zip(mom_pass, mom_avail) if a) * (30.0 / n_mom_available), 1
    ) if n_mom_available > 0 else 0.0

    # --- Risk/Reward pillar (30 pts) ---
    if rr_ratio >= 2.0:
        rr_score = 30.0
    elif rr_ratio >= 1.5:
        rr_score = 20.0
    elif rr_ratio >= 1.0:
        rr_score = 10.0
    else:
        rr_score = 0.0
    k_rr_ok = rr_score > 0

    total_score = round(float(np.clip(trend_score + mom_score + rr_score, 0, 100)))
    data_completeness = round((n_trend_available + n_mom_available + 1) / 7.0, 2)

    sig = classify_signal(total_score)

    return {
        'timing_score': float(total_score), 'rsi': round(rsi, 1), 'macd': round(macd, 3),
        'adx': round(adx, 1), 'ema20': round(ema20, 2), 'ema50': round(ema50, 2),
        'ma200': round(ma200, 2),
        'trend_signal': sig['signal_legacy'], 'resistance_60d': r1, 'support_60d': s1,
        'pivot_point': pivot_point, 'resistance_2': r2, 'support_2': s2,
        'overall_signal': sig['overall_signal'], 'status_label': sig['status_label'],
        'status_color': sig['status_color'], 'action_th': sig['action_th'],
        'rr_ratio': rr_ratio, 'trend_score': trend_score, 'mom_score': mom_score, 'rr_score': rr_score,
        'upside_pct': upside_pct, 'downside_pct': downside_pct,
        'readiness': sig['readiness'],
        'summary_text': sig['summary_text'],
        'k15_ok': k15_ok, 'k16_ok': k16_ok, 'k17_ok': k17_ok,
        'k18_ok': k18_ok, 'k19_ok': k19_ok, 'k20_ok': k20_ok, 'k_rr_ok': k_rr_ok,
        'k15_available': ema20_available, 'k16_available': ema20_available and ema50_available,
        'k17_available': k17_available, 'k18_available': macd_available,
        'k19_available': adx_available, 'k20_available': k20_available,
        'trend_available_count': n_trend_available, 'mom_available_count': n_mom_available,
        'data_completeness': data_completeness,
    }