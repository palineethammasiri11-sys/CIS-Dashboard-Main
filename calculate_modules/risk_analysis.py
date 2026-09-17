"""
calculate_modules/risk_analysis.py
--------------------------------------
สูตรคำนวณโมดูล "Risk Analysis" (🛡️) — คู่กับ pages_content/risk_analysis.py

=== DATA CONTRACT (ห้ามลบ/เปลี่ยนชื่อ key โดยไม่แจ้งทีม — เพิ่ม key ใหม่ได้อิสระ) ===

calculate_risk_module(df_price_ticker, risk_static_row) รับ:
    df_price_ticker  : pd.DataFrame ราคาหุ้น 1 ตัว เรียงตามวันที่ (ต้องมีคอลัมน์ date, close)
    risk_static_row  : pd.DataFrame แถวเดียว (หรือ None) จากตาราง stock_risk_static
                       (มี Beta/Volatility/Max Drawdown จริงจากไฟล์ stock_risk_metrics.csv)
                       ถ้าไม่มีข้อมูล ให้ส่ง None แล้วฟังก์ชันจะ fallback ไปคำนวณเองจากราคา

คืนค่าเป็น dict ที่ต้องมี key:
    risk_score, volatility, volatility_calc, max_drawdown, var_95, beta, sharpe_ratio, sortino_ratio

build_risk_rolling_history(df_price_ticker) คืน pd.DataFrame
    คอลัมน์ [date, rolling_vol_30d, drawdown_pct] ใช้วาดกราฟ trend หน้า Risk Analysis

ที่มาของสูตร: ดูละเอียดใน DATA_FORMULA_AUDIT.md หัวข้อ 5 (Module: Risk Analysis)
สรุปสั้น: Annualized Volatility, Max Drawdown, VaR (parametric 95%), Sharpe/Sortino Ratio
เป็นสูตรการเงินเชิงปริมาณมาตรฐานทั้งหมด (คำนวณถูกต้องตามนิยาม) แต่:
  - Sharpe/Sortino ไม่ได้หัก Risk-free Rate (ถือว่า = 0) ทำให้ค่าสูงกว่าสูตรเต็มเล็กน้อย
  - risk_score (คะแนนรวม 0-100) เป็นสูตรแปลงที่กำหนดเอง
"""

import numpy as np
import pandas as pd

from calculate_modules.common import clean_float


def calculate_risk_module(df_price_ticker, risk_static_row):
    """Module 5: Risk Analysis (ใช้ Beta/Volatility/Max Drawdown จริงจาก stock_risk_metrics.csv
    ผสมกับความผันผวน/Drawdown ที่คำนวณจากราคาย้อนหลังจริงในช่วง 2023-2025)"""
    df = df_price_ticker.sort_values(by='date').copy()
    df['close'] = df['close'].apply(clean_float)
    df['returns'] = df['close'].pct_change()

    daily_vol = df['returns'].std()
    annual_vol_calc = daily_vol * np.sqrt(252) * 100  # Annualized Volatility (มาตรฐาน: std * sqrt(252 วันเทรด/ปี))

    cum_max = df['close'].cummax()
    drawdown = (df['close'] - cum_max) / cum_max
    max_dd_calc = abs(drawdown.min()) * 100  # Maximum Drawdown (มาตรฐาน)

    var_95 = 1.645 * daily_vol * 100  # Parametric VaR 95% (z-score 1.645 ของ Normal Distribution)

    # ใช้ค่าจริงจากไฟล์ stock_risk_metrics.csv เป็นหลักถ้ามี ไม่งั้น fallback เป็นค่าที่คำนวณเอง
    if risk_static_row is not None and not risk_static_row.empty:
        beta = clean_float(risk_static_row.iloc[0].get('beta'), default=1.0)
        annual_vol = clean_float(risk_static_row.iloc[0].get('volatility_pct'), default=annual_vol_calc)
        max_dd = abs(clean_float(risk_static_row.iloc[0].get('max_drawdown_pct'), default=max_dd_calc))
    else:
        beta = 1.0
        annual_vol = annual_vol_calc
        max_dd = max_dd_calc

    risk_index = (annual_vol * 0.45) + (max_dd * 0.35) + (var_95 * 2.0)
    risk_score = round(float(np.clip(100 - risk_index, 25, 92)), 1)

    # Sharpe/Sortino Ratio (ไม่ได้หัก Risk-free Rate — ถือว่า Rf = 0 เพื่อความง่าย)
    sharpe = round(float((df['returns'].mean() * 252) / (daily_vol * np.sqrt(252))), 2) if daily_vol > 0 else 0.0
    downside_returns = df['returns'][df['returns'] < 0]
    downside_std = downside_returns.std() if len(downside_returns) > 1 else daily_vol
    sortino = round(float((df['returns'].mean() * 252) / (downside_std * np.sqrt(252))), 2) if downside_std > 0 else 0.0

    return {
        'risk_score': risk_score,
        'volatility': round(float(annual_vol), 1),
        'volatility_calc': round(float(annual_vol_calc), 1),
        'max_drawdown': round(float(max_dd), 1),
        'var_95': round(float(var_95), 2),
        'beta': round(float(beta), 2),
        'sharpe_ratio': sharpe,
        'sortino_ratio': sortino,
    }


def build_risk_rolling_history(df_price_ticker):
    """คำนวณ rolling 30 วัน ของ Volatility (annualized) และ Drawdown จากราคาปิดจริง"""
    df = df_price_ticker.sort_values(by='date').copy()
    df['close'] = df['close'].apply(clean_float)
    df['returns'] = df['close'].pct_change()

    df['rolling_vol_30d'] = df['returns'].rolling(30).std() * np.sqrt(252) * 100
    cum_max = df['close'].cummax()
    df['drawdown_pct'] = (df['close'] - cum_max) / cum_max * 100

    out = df[['date', 'rolling_vol_30d', 'drawdown_pct']].dropna(subset=['rolling_vol_30d']).copy()
    # เก็บเฉพาะจุดข้อมูลรายสัปดาห์ (เพื่อไม่ให้ตารางใหญ่เกินไป และกราฟอ่านง่าย)
    out = out.set_index('date').resample('W').last().dropna().reset_index()
    return out
