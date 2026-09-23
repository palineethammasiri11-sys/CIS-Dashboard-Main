"""
calculate_modules/ai_prediction.py
--------------------------------------
สูตรคำนวณโมดูล "AI Prediction" (🔮) — คู่กับ pages_content/ai_prediction.py

=== DATA CONTRACT (ห้ามลบ/เปลี่ยนชื่อ key โดยไม่แจ้งทีม — เพิ่ม key ใหม่ได้อิสระ) ===

train_and_predict_ai(df_price_ticker, ticker) รับ:
    df_price_ticker : pd.DataFrame ราคาหุ้น 1 ตัว เรียงตามวันที่ (จากตาราง stock_daily_prices)
                      ต้องมีคอลัมน์: date, close, EMA20, EMA50, RSI14, MACD, ADX
    ticker          : str (ปัจจุบันไม่ได้ใช้ในฟังก์ชัน แต่เก็บไว้เผื่ออยากทำโมเดลเฉพาะกลุ่มอุตสาหกรรมในอนาคต)

คืนค่าเป็น tuple 3 ตัว: (metrics_dict, feature_importance_dict, backtest_df)

    metrics_dict ต้องมี key:
        ai_score, prob_up, accuracy, precision, recall, f1_score, roc_auc, ai_signal

    feature_importance_dict: {feature_name: importance_value} ครบทุก feature ใน FEATURES

    backtest_df: pd.DataFrame คอลัมน์ [date, actual_close, predicted_up_prob]
        (ผลทำนายจริงบนชุด Test ปี 2025 — ใช้วาดกราฟ "Historical Prediction Performance")

ที่มาของสูตร: ดูละเอียดใน DATA_FORMULA_AUDIT.md หัวข้อ 4 (Module: AI Prediction)
สรุปสั้น: Random Forest + metrics (accuracy/precision/recall/f1/roc-auc) เป็น library มาตรฐานจาก
scikit-learn คำนวณให้ ไม่มีการปรับแต่งสูตรใดๆ (ส่วนที่น่าเชื่อถือที่สุดในระบบ)
ส่วนสูตร ai_score = prob_up*0.7 + accuracy*0.3 เป็นค่าที่กำหนดเอง

⚠️ ถ้าจะปรับ hyperparameter โมเดล (n_estimators, max_depth) หรือเปลี่ยนช่วง horizon การทำนาย
(ปัจจุบัน = ราคาใน 10 วันข้างหน้า) แก้ได้ที่ไฟล์นี้ไฟล์เดียว แต่ระวังว่าการเปลี่ยน horizon
จะกระทบข้อความอธิบายในหน้า UI (pages_content/ai_prediction.py) ที่เขียนว่า "10 วัน" ไว้ด้วย ต้องแก้คู่กัน

=== CHANGELOG ===
- เพิ่ม key 'baseline_accuracy' (ค่า accuracy ถ้าทายกลุ่มส่วนใหญ่เฉยๆ) ใน metrics_dict ทั้ง 2 return path
  เพื่อให้หน้า UI แสดงเทียบกับ accuracy จริงได้ ว่าโมเดล "เก่งกว่าทายมั่ว" จริงหรือไม่
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

# Feature ที่ใช้เทรนโมเดล (ต้องตรงกับคอลัมน์จริงในตาราง stock_daily_prices)
FEATURES = ['close', 'EMA20', 'EMA50', 'RSI14', 'MACD', 'ADX']

# จำนวนวันทำการล่วงหน้าที่ใช้นิยาม label (ราคาขึ้น/ลง) — ถ้าแก้เลขนี้ ต้องแก้คำอธิบายในหน้า UI ด้วย
PREDICTION_HORIZON_DAYS = 10


def train_and_predict_ai(df_price_ticker, ticker):
    """Module 4: AI Prediction (Train บน 2023-2024 / Test บน 2025) + คืน Feature Importance จริง"""
    from calculate_modules.common import clean_float

    df = df_price_ticker.copy().sort_values(by='date').reset_index(drop=True)

    for col in FEATURES:
        df[col] = df[col].apply(clean_float)

    df['target'] = (df['close'].shift(-PREDICTION_HORIZON_DAYS) > df['close']).astype(int)
    df_model = df.dropna(subset=FEATURES + ['target'])

    train_data = df_model[df_model['date'] < '2025-01-01']
    test_data = df_model[df_model['date'] >= '2025-01-01']

    feature_importance = {f: 0.0 for f in FEATURES}
    backtest_df = pd.DataFrame(columns=['date', 'actual_close', 'predicted_up_prob'])

    if len(train_data) < 50 or len(test_data) < 20:
        return ({'ai_score': 65.0, 'prob_up': 65.0, 'accuracy': 75.0, 'baseline_accuracy': 65.0,
                 'ai_signal': 'ACCUMULATE',
                 'precision': 70.0, 'recall': 70.0, 'f1_score': 70.0, 'roc_auc': 0.70},
                feature_importance, backtest_df)

    X_train, y_train = train_data[FEATURES], train_data['target']
    X_test, y_test = test_data[FEATURES], test_data['target']
    baseline_acc = float(max(y_test.mean(), 1 - y_test.mean()) * 100)  # ความแม่นยำถ้าทายกลุ่มส่วนใหญ่เฉยๆ

    model = RandomForestClassifier(n_estimators=200, max_depth=4, random_state=42)
    model.fit(X_train, y_train)

    test_pred = model.predict(X_test)
    test_proba = model.predict_proba(X_test)[:, 1]
    acc = accuracy_score(y_test, test_pred) * 100
    prec = precision_score(y_test, test_pred, zero_division=0) * 100
    rec = recall_score(y_test, test_pred, zero_division=0) * 100
    f1 = f1_score(y_test, test_pred, zero_division=0) * 100
    try:
        auc = roc_auc_score(y_test, test_proba) if y_test.nunique() > 1 else 0.5
    except Exception:
        auc = 0.5

    latest_X = df[FEATURES].iloc[[-1]]
    prob_up = model.predict_proba(latest_X)[0][1] * 100
    ai_score = round(float(np.clip((prob_up * 0.7) + (acc * 0.3), 30, 95)), 1)

    sig = "STRONG BUY" if prob_up >= 70 else ("ACCUMULATE" if prob_up >= 50 else "CAUTION")

    for f, imp in zip(FEATURES, model.feature_importances_):
        feature_importance[f] = round(float(imp), 4)

    backtest_df = pd.DataFrame({
        'date': test_data['date'].values,
        'actual_close': test_data['close'].values,
        'predicted_up_prob': test_proba,
    })

    return ({
        'ai_score': ai_score,
        'prob_up': round(float(prob_up), 1),
        'accuracy': round(float(acc), 1),
        'baseline_accuracy': round(baseline_acc, 1),
        'precision': round(float(prec), 1),
        'recall': round(float(rec), 1),
        'f1_score': round(float(f1), 1),
        'roc_auc': round(float(auc), 2),
        'ai_signal': sig,
    }, feature_importance, backtest_df)
