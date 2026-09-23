# ไฟล์ calculate_modules/entry_timing.py
"""
calculate_modules/entry_timing.py
--------------------------------------------------------------------
Institutional Quantitative Framework (IKB v2.2) - Production Database Compatible Build
Changelog vs v2.1:
- FIX: ปรับรูปแบบคืนค่าทั้งหมดเป็น Primitive/Scalar types (int, float, str)
  เพื่อรองรับ SQLite schema ใน calculate_scores.py โดยไม่ต้องแก้ไขโค้ดฐานข้อมูลกลาง
- MAINTAIN: ตรรกะ Issue 01-05 และ Trend Veto ยังคงทำงานครบถ้วนตามเดิม
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, replace, asdict
from typing import Optional, Sequence, Tuple

import numpy as np
import pandas as pd

try:
    from calculate_modules.common import clean_float
except ImportError:
    def clean_float(value, default=0.0):
        try:
            f = float(value)
            return default if (math.isnan(f) or math.isinf(f)) else f
        except (TypeError, ValueError):
            return default


# =====================================================================
# ISSUE 05: Parameterization layer
# =====================================================================
@dataclass(frozen=True)
class TimingConfig:
    trend_weight: float = 40.0
    momentum_weight: float = 30.0
    rr_weight: float = 30.0

    trend_criteria_count: int = 3
    momentum_criteria_count: int = 3

    adx_trend_threshold: float = 25.0
    macd_bull_threshold: float = 0.0
    volume_ratio_threshold: float = 1.0

    volume_lookback: int = 20
    volume_exclude_current_bar: bool = True
    use_precomputed_volume_avg: bool = False
    volume_avg_column_candidates: Tuple[str, ...] = ("Volume_Avg20", "Volume_Avg_20")

    rr_tiers: Tuple[Tuple[float, float], ...] = ((2.0, 30.0), (1.5, 20.0), (1.0, 10.0))
    min_downside_pct: float = 1.0

    bullish_threshold: float = 70.0
    neutral_threshold: float = 40.0

    min_bars_required: int = 20
    min_data_completeness: float = 0.50
    enable_trend_veto: bool = True

    resistance_window_short: int = 60
    resistance_window_long: int = 120
    ma_long_period: int = 200

    close_columns: Tuple[str, ...] = ("close", "Close")
    high_columns: Tuple[str, ...] = ("high", "High")
    low_columns: Tuple[str, ...] = ("low", "Low")
    volume_columns: Tuple[str, ...] = ("volume", "Volume", "vol", "Vol")
    ema20_columns: Tuple[str, ...] = ("EMA20", "ema20", "EMA_20")
    ema50_columns: Tuple[str, ...] = ("EMA50", "ema50", "EMA_50")
    ma200_columns: Tuple[str, ...] = ("MA200", "ma200", "SMA200", "MA_200")
    rsi_columns: Tuple[str, ...] = ("RSI14", "rsi14", "RSI_14", "RSI")
    macd_columns: Tuple[str, ...] = ("MACD", "macd")
    adx_columns: Tuple[str, ...] = ("ADX", "ADX14", "adx14", "ADX_14", "adx")

    def __post_init__(self):
        total = self.trend_weight + self.momentum_weight + self.rr_weight
        if abs(total - 100.0) > 1e-6:
            raise ValueError(f"น้ำหนักเสารวมต้องเท่ากับ 100 (ได้ {total})")
        if self.trend_criteria_count < 1 or self.momentum_criteria_count < 1:
            raise ValueError("ตัวหารของเสาต้องเป็นจำนวนเต็มบวก")
        if self.bullish_threshold <= self.neutral_threshold:
            raise ValueError("bullish_threshold ต้องมากกว่า neutral_threshold")
        if self.rr_tiers:
            ratios = [t[0] for t in self.rr_tiers]
            if ratios != sorted(ratios, reverse=True):
                raise ValueError("rr_tiers ต้องเรียงอัตราส่วนจากมากไปน้อย")
            if max(t[1] for t in self.rr_tiers) > self.rr_weight + 1e-9:
                raise ValueError("คะแนนสูงสุดใน rr_tiers เกินน้ำหนักเสา RR")
        if self.volume_lookback < 2:
            raise ValueError("volume_lookback ต้อง >= 2")

    @classmethod
    def from_dict(cls, overrides: Optional[dict]) -> "TimingConfig":
        if not overrides:
            return cls()
        valid = {f for f in cls.__dataclass_fields__}
        unknown = set(overrides) - valid
        if unknown:
            raise KeyError(f"พารามิเตอร์ไม่รู้จัก: {sorted(unknown)}")
        clean = {}
        for k, v in overrides.items():
            if k == "rr_tiers" and v is not None:
                v = tuple((float(a), float(b)) for a, b in v)
            elif isinstance(v, list):
                v = tuple(v)
            clean[k] = v
        return cls(**clean)

    @classmethod
    def from_json(cls, path: str) -> "TimingConfig":
        with open(path, "r", encoding="utf-8") as fh:
            return cls.from_dict(json.load(fh))

    @classmethod
    def from_env(cls, prefix: str = "TIMING_") -> "TimingConfig":
        overrides = {}
        for name, f in cls.__dataclass_fields__.items():
            env_key = prefix + name.upper()
            if env_key not in os.environ:
                continue
            raw = os.environ[env_key]
            if f.type in ("float", float):
                overrides[name] = float(raw)
            elif f.type in ("int", int):
                overrides[name] = int(raw)
            elif f.type in ("bool", bool):
                overrides[name] = raw.strip().lower() in ("1", "true", "yes", "y")
            else:
                overrides[name] = json.loads(raw)
        return cls.from_dict(overrides)

    def tuned(self, **kwargs) -> "TimingConfig":
        return replace(self, **kwargs)

    def as_dict(self) -> dict:
        return asdict(self)


DEFAULT_CONFIG = TimingConfig()
MIN_BARS_FOR_1Y_TREND = DEFAULT_CONFIG.ma_long_period


def _to_float(value) -> Optional[float]:
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return f


def _resolve_column(df: pd.DataFrame, candidates: Sequence[str]) -> Optional[str]:
    if df is None:
        return None
    for name in candidates:
        if name in df.columns:
            return name
    return None


def _latest_value(df: pd.DataFrame, candidates: Sequence[str]) -> Tuple[Optional[float], Optional[str]]:
    col = _resolve_column(df, candidates)
    if col is None:
        return None, None
    return _to_float(df[col].iloc[-1]), col


def _round(value: Optional[float], digits: int = 2) -> Optional[float]:
    return None if value is None else round(float(value), digits)


NO_DATA_STATUS = "INSUFFICIENT_DATA"
NO_DATA_COLOR = "#64748B"
NO_DATA_LABEL_TH = "ข้อมูลไม่เพียงพอ"

_NUMERIC_OUTPUT_KEYS = (
    "timing_score", "rsi", "macd", "adx", "ema20", "ema50", "ma200",
    "resistance_60d", "support_60d", "pivot_point", "resistance_2", "support_2",
    "rr_ratio", "trend_score", "mom_score", "rr_score",
    "upside_pct", "downside_pct", "volume_ratio", "volume_avg", "volume_last",
)

_FLAG_OUTPUT_KEYS = (
    "k15_ok", "k16_ok", "k17_ok", "k18_ok", "k19_ok", "k20_ok", "k_rr_ok",
    "k15_available", "k16_available", "k17_available",
    "k18_available", "k19_available", "k20_available", "k_rr_available",
)


def _empty_result(reason: str = "ไม่พบข้อมูลราคาสำหรับหลักทรัพย์นี้",
                  config: Optional[TimingConfig] = None) -> dict:
    result = {key: None for key in _NUMERIC_OUTPUT_KEYS}
    result.update({key: 0 for key in _FLAG_OUTPUT_KEYS})
    result.update({
        "data_status": NO_DATA_STATUS,
        "data_status_th": NO_DATA_LABEL_TH,
        "data_status_reason": reason,
        "is_evaluated": 0,
        "trend_signal": "N/A",
        "overall_signal": "N/A",
        "status_label": NO_DATA_LABEL_TH,
        "status_color": NO_DATA_COLOR,
        "action_th": "ยังประเมินจังหวะเข้าซื้อไม่ได้ เนื่องจากข้อมูลไม่เพียงพอ",
        "readiness": "NO_DATA",
        "summary_text": f"ข้อมูลไม่เพียงพอสำหรับการประเมินเชิงลึก ({reason})",
        "rr_status": "NOT_COMPUTABLE",
        "rr_status_th": "คำนวณไม่ได้",
        "rr_reason": reason,
        "trend_veto_applied": 0,
        "trend_veto_reason": "",
        "trend_available_count": 0,
        "mom_available_count": 0,
        "trend_criteria_count": int((config or DEFAULT_CONFIG).trend_criteria_count),
        "mom_criteria_count": int((config or DEFAULT_CONFIG).momentum_criteria_count),
        "data_completeness": 0.0,
        "missing_fields": "",
        "config_snapshot": "",
    })
    return result


def _check_data_gate(df_price_ticker: Optional[pd.DataFrame],
                     config: TimingConfig) -> Optional[str]:
    if df_price_ticker is None or not isinstance(df_price_ticker, pd.DataFrame):
        return "ไม่ได้รับ DataFrame ราคา"
    if df_price_ticker.empty:
        return "DataFrame ราคาว่างเปล่า"
    if _resolve_column(df_price_ticker, config.close_columns) is None:
        return "ไม่พบคอลัมน์ราคาปิด (close/Close)"
    if len(df_price_ticker) < config.min_bars_required:
        return (f"มีข้อมูลเพียง {len(df_price_ticker)} แท่ง "
                f"(ต้องการอย่างน้อย {config.min_bars_required} แท่ง)")
    price = _to_float(df_price_ticker[_resolve_column(
        df_price_ticker, config.close_columns)].iloc[-1])
    if price is None or price <= 0:
        return "ราคาปิดล่าสุดไม่ถูกต้อง (NaN หรือ <= 0)"
    return None


def classify_signal(total_score: Optional[float],
                    config: Optional[TimingConfig] = None,
                    trend_veto: bool = False) -> dict:
    cfg = config or DEFAULT_CONFIG

    if total_score is None:
        return dict(
            signal_legacy="N/A", overall_signal="N/A",
            status_label=NO_DATA_LABEL_TH, status_color=NO_DATA_COLOR,
            action_th="ยังประเมินจังหวะเข้าซื้อไม่ได้ เนื่องจากข้อมูลไม่เพียงพอ",
            readiness="NO_DATA", trend_veto_applied=False,
            summary_text="ข้อมูลไม่เพียงพอสำหรับการประเมินเชิงลึก",
        )

    if cfg.enable_trend_veto and trend_veto:
        return dict(
            signal_legacy="BEARISH", overall_signal="BEARISH (Avoid)",
            status_label="BEARISH", status_color="#EF4444",
            action_th="เทรนด์หลักเป็นขาลง (ราคาต่ำกว่า MA200) ห้ามรับมีด แม้เสาอื่นจะให้คะแนนดี",
            readiness="WAIT", trend_veto_applied=True,
            summary_text=f"ระบบยกเลิกผลรวม {total_score:.0f} คะแนนตามกฎ KO-21 (Trend Veto): "
                         "เทรนด์หลักยืนยันเป็นขาลง จึงบังคับสถานะเป็น BEARISH (Avoid) "
                         "เพื่อป้องกันสัญญาณ Oversold หลอกลวงจากเสาอื่น",
        )

    if total_score >= cfg.bullish_threshold:
        return dict(
            signal_legacy="BULLISH", overall_signal="BULLISH (Strong Buy)",
            status_label="STRONG BUY", status_color="#10B981",
            action_th="จังหวะซื้อได้เปรียบสูง", readiness="READY",
            summary_text="ราคายืนในโซนสะสมและโครงสร้างขาขึ้นแข็งแกร่ง พร้อมทยอยสะสม",
        )
    elif total_score >= cfg.neutral_threshold:
        return dict(
            signal_legacy="NEUTRAL", overall_signal="NEUTRAL",
            status_label="NEUTRAL", status_color="#38BDF8",
            action_th="แกว่งตัว รอดูสัญญาณยืนยัน", readiness="WAIT",
            trend_veto_applied=False,
            summary_text="แม้ราคาจะอยู่ในโซนที่น่าสนใจ แต่สัญญาณทางเทคนิคยังไม่ยืนยันการกลับตัว "
                         "ควรรอการยืนยันจากปริมาณซื้อขายและแนวโน้มราคา",
        )
    else:
        return dict(
            signal_legacy="BEARISH", overall_signal="BEARISH (Avoid)",
            status_label="BEARISH", status_color="#EF4444",
            action_th="ขาลง ควรหลีกเลี่ยง", readiness="WAIT",
            trend_veto_applied=False,
            summary_text="แนวโน้มหลักยังเป็นขาลงและโมเมนตัมอ่อนแอ "
                         "หลีกเลี่ยงการเข้าลงทุนจนกว่าจะเกิดสัญญาณกลับตัวชัดเจน",
        )


def compute_price_levels(price: Optional[float],
                         df_price_ticker: pd.DataFrame,
                         high_col: Optional[str] = None,
                         low_col: Optional[str] = None,
                         config: Optional[TimingConfig] = None) -> dict:
    cfg = config or DEFAULT_CONFIG
    high_col = high_col or _resolve_column(df_price_ticker, cfg.high_columns)
    low_col = low_col or _resolve_column(df_price_ticker, cfg.low_columns)

    levels = {"r1": None, "r2": None, "s1": None, "s2": None,
              "pivot_point": None, "levels_available": False,
              "levels_reason": ""}

    if price is None or price <= 0:
        levels["levels_reason"] = "ไม่มีราคาอ้างอิง"
        return levels
    if high_col is None or low_col is None:
        levels["levels_reason"] = "ไม่พบคอลัมน์ High/Low"
        return levels

    recent_s = df_price_ticker.tail(cfg.resistance_window_short)
    recent_l = df_price_ticker.tail(cfg.resistance_window_long)

    r1 = _to_float(recent_s[high_col].max())
    r2 = _to_float(recent_l[high_col].max())
    s1 = _to_float(recent_s[low_col].min())
    s2 = _to_float(recent_l[low_col].min())

    if r1 is None or s1 is None:
        levels["levels_reason"] = "High/Low ในกรอบเวลาเป็น NaN ทั้งหมด"
        return levels

    r2 = r1 if r2 is None else max(r2, r1)
    s2 = s1 if s2 is None else min(s2, s1)

    pivot = None
    if len(df_price_ticker) >= 2:
        prev = df_price_ticker.iloc[-2]
        ph, pl = _to_float(prev.get(high_col)), _to_float(prev.get(low_col))
        if ph is not None and pl is not None:
            pivot = round((ph + pl + price) / 3.0, 2)

    levels.update({
        "r1": round(r1, 2), "r2": round(r2, 2),
        "s1": round(s1, 2), "s2": round(s2, 2),
        "pivot_point": pivot, "levels_available": True,
    })
    return levels


def compute_risk_reward(price: Optional[float],
                        r1: Optional[float],
                        r2: Optional[float],
                        s2: Optional[float],
                        config: Optional[TimingConfig] = None) -> dict:
    cfg = config or DEFAULT_CONFIG
    out = {
        "rr_ratio": None, "rr_score": 0.0, "rr_status": "NOT_COMPUTABLE",
        "rr_status_th": "คำนวณไม่ได้", "rr_reason": "",
        "upside_pct": None, "downside_pct": None,
        "reward_target": None, "risk_floor": None,
        "k_rr_ok": False, "k_rr_available": False,
    }

    if price is None or price <= 0:
        out["rr_reason"] = "ไม่มีราคาอ้างอิง"
        return out
    if r1 is None or s2 is None:
        out["rr_reason"] = "หาแนวรับ/แนวต้านอ้างอิงไม่ได้"
        return out

    reward_target = r2 if (price >= r1 and r2 is not None) else r1
    downside_risk = price - s2

    if downside_risk <= 0:
        out["rr_reason"] = "ราคาหลุดแนวรับอ้างอิงแล้ว (ตัวหาร <= 0) จึงนิยามความเสี่ยงไม่ได้"
        return out

    downside_pct = (downside_risk / price) * 100.0
    if cfg.min_downside_pct > 0 and downside_pct < cfg.min_downside_pct:
        out["rr_reason"] = (
            f"ระยะถึงแนวรับเพียง {downside_pct:.2f}% (ต่ำกว่าเกณฑ์ "
            f"{cfg.min_downside_pct:.2f}%) ตัวหารเล็กเกินกว่าจะนิยามความเสี่ยงได้"
        )
        out["downside_pct"] = round(downside_pct, 1)
        return out

    upside_reward = reward_target - price
    rr_ratio = round(max(upside_reward, 0.0) / downside_risk, 2)

    rr_score = 0.0
    for threshold, points in cfg.rr_tiers:
        if rr_ratio >= threshold:
            rr_score = float(points)
            break

    out.update({
        "rr_ratio": rr_ratio,
        "rr_score": rr_score,
        "rr_status": "COMPUTED",
        "rr_status_th": "คำนวณได้",
        "upside_pct": round((upside_reward / price) * 100, 1),
        "downside_pct": round((downside_risk / price) * 100, 1),
        "reward_target": round(reward_target, 2),
        "risk_floor": round(s2, 2),
        "k_rr_ok": rr_score > 0,
        "k_rr_available": True,
    })
    if upside_reward <= 0:
        out["rr_reason"] = "ราคาเลยเป้าหมายอ้างอิงแล้ว อัพไซด์คงเหลือ = 0"
    return out


def compute_volume_context(df_price_ticker: pd.DataFrame,
                           config: Optional[TimingConfig] = None) -> dict:
    cfg = config or DEFAULT_CONFIG
    out = {"volume_last": None, "volume_avg": None, "volume_ratio": None,
           "volume_base_window": "",
           "k20_available": False, "k20_ok": False, "volume_reason": ""}

    vol_col = _resolve_column(df_price_ticker, cfg.volume_columns)
    if vol_col is None:
        out["volume_reason"] = "ไม่พบคอลัมน์ Volume"
        return out

    vol_last = _to_float(df_price_ticker[vol_col].iloc[-1])
    if vol_last is None:
        out["volume_reason"] = "วอลุ่มแท่งล่าสุดเป็น NaN"
        return out
    out["volume_last"] = vol_last

    n = cfg.volume_lookback
    vol_avg = None

    if cfg.use_precomputed_volume_avg:
        avg_col = _resolve_column(df_price_ticker, cfg.volume_avg_column_candidates)
        if avg_col is not None and len(df_price_ticker) >= 2:
            vol_avg = _to_float(df_price_ticker[avg_col].iloc[-2])
            out["volume_base_window"] = f"{avg_col} @ bar -2 (shift 1)"

    if vol_avg is None:
        need = n + 1 if cfg.volume_exclude_current_bar else n
        if len(df_price_ticker) < need:
            out["volume_reason"] = f"ต้องการอย่างน้อย {need} แท่งเพื่อสร้างฐานค่าเฉลี่ย"
            return out
        if cfg.volume_exclude_current_bar:
            base = df_price_ticker[vol_col].iloc[-(n + 1):-1]
            out["volume_base_window"] = f"bars -{n + 1} .. -2"
        else:
            base = df_price_ticker[vol_col].iloc[-n:]
            out["volume_base_window"] = f"bars -{n} .. -1"
        vol_avg = _to_float(base.mean())

    if vol_avg is None or vol_avg <= 0:
        out["volume_reason"] = "ฐานค่าเฉลี่ยวอลุ่มเป็น NaN หรือ <= 0"
        return out

    ratio = vol_last / vol_avg
    out.update({
        "volume_avg": round(vol_avg, 2),
        "volume_ratio": round(ratio, 3),
        "k20_available": True,
        "k20_ok": bool(ratio >= cfg.volume_ratio_threshold),
    })
    return out


def _score_pillar(passes: Sequence[bool],
                  availables: Sequence[bool],
                  weight: float,
                  criteria_count: int) -> float:
    if criteria_count <= 0:
        return 0.0
    if len(passes) != criteria_count:
        raise ValueError(
            f"จำนวนเกณฑ์ ({len(passes)}) ไม่ตรงกับตัวหารที่ตั้งไว้ ({criteria_count})"
        )
    passed = sum(1 for p, a in zip(passes, availables) if bool(p) and bool(a))
    return round(passed * (weight / criteria_count), 1)


def calculate_timing_module(df_price_ticker: Optional[pd.DataFrame],
                            config: Optional[TimingConfig] = None,
                            **overrides) -> dict:
    cfg = config or DEFAULT_CONFIG
    if overrides:
        cfg = cfg.tuned(**overrides)

    gate_reason = _check_data_gate(df_price_ticker, cfg)
    if gate_reason is not None:
        return _empty_result(gate_reason, cfg)

    close_col = _resolve_column(df_price_ticker, cfg.close_columns)
    high_col = _resolve_column(df_price_ticker, cfg.high_columns)
    low_col = _resolve_column(df_price_ticker, cfg.low_columns)
    price = _to_float(df_price_ticker[close_col].iloc[-1])

    ema20, _ = _latest_value(df_price_ticker, cfg.ema20_columns)
    ema50, _ = _latest_value(df_price_ticker, cfg.ema50_columns)
    rsi, _ = _latest_value(df_price_ticker, cfg.rsi_columns)
    macd, _ = _latest_value(df_price_ticker, cfg.macd_columns)
    adx, adx_col = _latest_value(df_price_ticker, cfg.adx_columns)

    ma200, ma200_col = _latest_value(df_price_ticker, cfg.ma200_columns)
    if ma200 is None and len(df_price_ticker) >= cfg.ma_long_period:
        ma200 = _to_float(df_price_ticker[close_col].tail(cfg.ma_long_period).mean())

    k15_available = ema20 is not None
    k16_available = (ema20 is not None) and (ema50 is not None)
    k17_available = ma200 is not None

    k15_ok = bool(price > ema20) if k15_available else False
    k16_ok = bool(ema20 > ema50) if k16_available else False
    k17_ok = bool(price > ma200) if k17_available else False

    trend_pass = [k15_ok, k16_ok, k17_ok]
    trend_avail = [k15_available, k16_available, k17_available]
    trend_score = _score_pillar(trend_pass, trend_avail,
                                cfg.trend_weight, cfg.trend_criteria_count)

    vol_ctx = compute_volume_context(df_price_ticker, cfg)

    k18_available = macd is not None
    k19_available = adx is not None
    k20_available = vol_ctx["k20_available"]

    k18_ok = bool(macd > cfg.macd_bull_threshold) if k18_available else False
    k19_ok = bool(adx >= cfg.adx_trend_threshold) if k19_available else False
    k20_ok = vol_ctx["k20_ok"]

    mom_pass = [k18_ok, k19_ok, k20_ok]
    mom_avail = [k18_available, k19_available, k20_available]
    mom_score = _score_pillar(mom_pass, mom_avail,
                              cfg.momentum_weight, cfg.momentum_criteria_count)

    levels = compute_price_levels(price, df_price_ticker, high_col, low_col, cfg)
    rr = compute_risk_reward(price, levels["r1"], levels["r2"], levels["s2"], cfg)

    available_flags = trend_avail + mom_avail + [rr["k_rr_available"]]
    total_criteria = cfg.trend_criteria_count + cfg.momentum_criteria_count + 1
    available_count = sum(1 for a in available_flags if a)
    data_completeness = round(available_count / float(total_criteria), 2)

    missing_fields = [
        name for name, ok in [
            ("EMA20", k15_available), ("EMA50", k16_available), ("MA200", k17_available),
            ("MACD", k18_available), ("ADX", k19_available),
            ("Volume", k20_available), ("Risk/Reward", rr["k_rr_available"]),
        ] if not ok
    ]
    missing_fields_str = ", ".join(missing_fields) if missing_fields else ""

    if data_completeness < cfg.min_data_completeness:
        result = _empty_result(
            f"ตัวชี้วัดพร้อมใช้เพียง {available_count}/{total_criteria} "
            f"({data_completeness:.0%}) ต่ำกว่าเกณฑ์ขั้นต่ำ {cfg.min_data_completeness:.0%}",
            cfg,
        )
        result["missing_fields"] = missing_fields_str
        result["data_completeness"] = data_completeness
        return result

    total_score = float(np.clip(trend_score + mom_score + rr["rr_score"], 0, 100))
    total_score = round(total_score)

    trend_veto = bool(cfg.enable_trend_veto and k17_available and not k17_ok)
    sig = classify_signal(total_score, cfg, trend_veto=trend_veto)

    config_snapshot_str = json.dumps({
        "adx_trend_threshold": cfg.adx_trend_threshold,
        "rr_tiers": cfg.rr_tiers,
        "bullish_threshold": cfg.bullish_threshold,
        "neutral_threshold": cfg.neutral_threshold,
        "volume_lookback": cfg.volume_lookback,
        "volume_exclude_current_bar": cfg.volume_exclude_current_bar,
        "enable_trend_veto": cfg.enable_trend_veto,
    }, ensure_ascii=False)

    return {
        "data_status": "OK",
        "data_status_th": "ข้อมูลเพียงพอ",
        "data_status_reason": "",
        "is_evaluated": 1,
        "data_completeness": float(data_completeness),
        "missing_fields": str(missing_fields_str),

        "timing_score": float(total_score),
        "trend_score": float(trend_score),
        "mom_score": float(mom_score),
        "rr_score": float(rr["rr_score"]),

        "rsi": _round(rsi, 1),
        "macd": _round(macd, 3),
        "adx": _round(adx, 1),
        "ema20": _round(ema20),
        "ema50": _round(ema50),
        "ma200": _round(ma200),
        "adx_source_column": str(adx_col or ""),
        "ma200_source_column": str(ma200_col or ""),

        "resistance_60d": _round(levels["r1"]),
        "resistance_2": _round(levels["r2"]),
        "support_60d": _round(levels["s1"]),
        "support_2": _round(levels["s2"]),
        "pivot_point": _round(levels["pivot_point"]),
        "levels_available": 1 if levels["levels_available"] else 0,

        "rr_ratio": _round(rr["rr_ratio"]),
        "rr_status": str(rr["rr_status"]),
        "rr_status_th": str(rr["rr_status_th"]),
        "rr_reason": str(rr["rr_reason"] or ""),
        "upside_pct": _round(rr["upside_pct"], 1),
        "downside_pct": _round(rr["downside_pct"], 1),
        "reward_target": _round(rr["reward_target"]),
        "risk_floor": _round(rr["risk_floor"]),

        "volume_last": _round(vol_ctx["volume_last"]),
        "volume_avg": _round(vol_ctx["volume_avg"]),
        "volume_ratio": _round(vol_ctx["volume_ratio"], 3),
        "volume_base_window": str(vol_ctx["volume_base_window"] or ""),

        "trend_signal": str(sig["signal_legacy"]),
        "overall_signal": str(sig["overall_signal"]),
        "status_label": str(sig["status_label"]),
        "status_color": str(sig["status_color"]),
        "action_th": str(sig["action_th"]),
        "readiness": str(sig["readiness"]),
        "summary_text": str(sig["summary_text"]),
        "trend_veto_applied": 1 if sig["trend_veto_applied"] else 0,
        "trend_veto_reason": "ราคาต่ำกว่า MA200 (KO-15 Downtrend) — บังคับ BEARISH ตาม KO-21" if sig["trend_veto_applied"] else "",

        "k15_ok": 1 if k15_ok else 0,
        "k16_ok": 1 if k16_ok else 0,
        "k17_ok": 1 if k17_ok else 0,
        "k18_ok": 1 if k18_ok else 0,
        "k19_ok": 1 if k19_ok else 0,
        "k20_ok": 1 if k20_ok else 0,
        "k_rr_ok": 1 if rr["k_rr_ok"] else 0,
        "k15_available": 1 if k15_available else 0,
        "k16_available": 1 if k16_available else 0,
        "k17_available": 1 if k17_available else 0,
        "k18_available": 1 if k18_available else 0,
        "k19_available": 1 if k19_available else 0,
        "k20_available": 1 if k20_available else 0,
        "k_rr_available": 1 if rr["k_rr_available"] else 0,

        "trend_criteria_count": int(cfg.trend_criteria_count),
        "mom_criteria_count": int(cfg.momentum_criteria_count),
        "trend_weight": float(cfg.trend_weight),
        "mom_weight": float(cfg.momentum_weight),
        "rr_weight": float(cfg.rr_weight),
        "trend_available_count": int(sum(1 for a in trend_avail if a)),
        "mom_available_count": int(sum(1 for a in mom_avail if a)),

        "config_snapshot": str(config_snapshot_str),
    }