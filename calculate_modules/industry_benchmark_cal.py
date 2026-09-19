"""
calculate_modules/industry_benchmark.py
-------------------------------------------
สูตรคำนวณโมดูล "Industry Benchmark" (📊) — คู่กับ pages_content/industry_benchmark.py

ต่างจากโมดูลอื่น: โมดูลนี้ "ไม่ได้" คำนวณจากงบการเงิน/ราคาหุ้นโดยตรง แต่คำนวณจาก
"ผลลัพธ์ที่โมดูลอื่นทั้ง 5 คำนวณมาแล้ว" (เพราะการจัดอันดับ/เทียบกลุ่มต้องรู้คะแนนของทุกหุ้นก่อน)
ดังนั้นฟังก์ชันนี้จะถูกเรียกเป็นลำดับสุดท้ายใน calculate_scores.py หลัง 5 โมดูลอื่นคำนวณครบทุกหุ้นแล้ว

=== DATA CONTRACT (ห้ามลบ/เปลี่ยนชื่อ key โดยไม่แจ้งทีม — เพิ่ม key ใหม่ได้อิสระ) ===

compute_industry_rankings(df_res) รับ:
    df_res : pd.DataFrame ที่มีคะแนนครบทุกหุ้น (แถวละ 1 หุ้น) ต้องมีคอลัมน์ต่อไปนี้อยู่แล้ว
             (มาจาก 5 โมดูลอื่น + ข้อมูลพื้นฐาน): ticker, sector, health_score, valuation_score,
             timing_score, ai_score, risk_score

คืนค่า df_res เดิม "บวกเพิ่ม" คอลัมน์ต่อไปนี้ (ไม่ลบคอลัมน์เดิม):
    industry_score   : float 0-100  (percentile ของ health_score ภายในกลุ่ม sector เดียวกัน)
    overall_score    : float 0-100  (คะแนนรวมถ่วงน้ำหนักทุกโมดูล — ใช้ทำ Recommendation หน้า Overview)
    sector_rank      : int          (อันดับภายในกลุ่ม sector เดียวกัน จากทั้งหมดที่ติดตาม)
    overall_rank     : int          (อันดับเทียบทั้งหมดที่ติดตาม ไม่แบ่งกลุ่ม)
    recommendation   : str          (STRONG BUY / BUY / ACCUMULATE / REDUCE-SELL)

ที่มาของสูตร: ดูละเอียดใน DATA_FORMULA_AUDIT.md หัวข้อ 6-7 (Industry Benchmark + Overall Score)
สรุปสั้น: การจัดอันดับ (rank) และ percentile เป็นวิธีทางสถิติมาตรฐาน (pandas.rank())
แต่น้ำหนักถ่วง Overall Score (25/25/15/10/15/10%) และเกณฑ์ Recommendation (75/65/50)
เป็นค่าที่กำหนดเองทั้งหมด — จุดสำคัญ: ฐานเทียบมีแค่ 8 หุ้นเท่านั้น ไม่ใช่ทั้งตลาด SET จริง
"""


def compute_industry_rankings(df_res):
    """รับ DataFrame ที่มีคะแนนทุกโมดูลของทุกหุ้นแล้ว (แถวละ 1 หุ้น) คำนวณ Industry Benchmark
    + Overall Score + Recommendation แล้วคืน DataFrame เดิมที่เพิ่มคอลัมน์เหล่านี้เข้าไป"""

    # Percentile ของ health_score ภายในกลุ่ม sector เดียวกัน (0-100, ยิ่งสูงยิ่งดีกว่ากลุ่ม)
    df_res['industry_score'] = df_res.groupby('sector')['health_score'].rank(pct=True).apply(lambda x: round(x * 100, 1))

    # คะแนนรวมถ่วงน้ำหนัก — น้ำหนักนี้เป็นค่าที่กำหนดเอง ปรับได้ตามที่ทีมเห็นสมควร
    df_res['overall_score'] = (
        (df_res['health_score'] * 0.25) +
        (df_res['valuation_score'] * 0.25) +
        (df_res['timing_score'] * 0.15) +
        (df_res['ai_score'] * 0.10) +
        (df_res['risk_score'] * 0.15) +
        (df_res['industry_score'] * 0.10)
    ).round(1)

    df_res['sector_rank'] = df_res.groupby('sector')['overall_score'].rank(ascending=False, method='min').astype(int)
    df_res['overall_rank'] = df_res['overall_score'].rank(ascending=False, method='min').astype(int)

    def get_rec(score):
        if score >= 75:
            return "STRONG BUY"
        if score >= 65:
            return "BUY"
        if score >= 50:
            return "ACCUMULATE"
        return "REDUCE / SELL"

    df_res['recommendation'] = df_res['overall_score'].apply(get_rec)
    return df_res
