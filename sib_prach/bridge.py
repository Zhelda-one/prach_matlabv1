"""SIB1 prach_config dict → Streamlit MATLAB 사이드바용 기본값."""

from __future__ import annotations

from typing import Any, Dict, Optional


def restricted_rrc_to_matlab(rrc: Optional[str]) -> str:
    """RRC restrictedSetConfig 문자열을 nrPRACHConfig.RestrictedSet 형태로."""
    if not rrc:
        return "UnrestrictedSet"
    key = rrc.strip().lower()
    mapping = {
        "unrestrictedset": "UnrestrictedSet",
        "restrictedsettypea": "RestrictedSetTypeA",
        "restrictedsettypeb": "RestrictedSetTypeB",
    }
    return mapping.get(key, "UnrestrictedSet")


def matlab_prefill_from_prach_config(prach: Dict[str, Any]) -> Dict[str, Any]:
    """
    app.py 세션에 넣을 MATLAB 관련 기본값.
    FDD·15 kHz는 앱에서 고정; 여기서는 RACH 공통 필드만 채운다.
    """
    cfg_idx = prach.get("prach_configuration_index")
    if cfg_idx is None:
        raise ValueError("prach_ConfigurationIndex 가 SIB1에서 찾을 수 없습니다.")

    rsi = prach.get("prach_root_sequence_index")
    if rsi is None:
        rsi = 0

    zcz = prach.get("zero_correlation_zone_config")
    if zcz is None:
        zcz = 0

    freq_start = prach.get("msg1_frequency_start")
    if freq_start is None:
        freq_start = 0

    # msg1-FDM=1 일 때 등 MATLAB은 FrequencyIndex>0 과 ActivePRACHSlot 조합을 거부하는 경우가 있음.
    # SIB에서 per-occasion 주파수 인덱스를 주지 않으므로 보수적으로 0.
    freq_index = 0

    return {
        "use_manual_ci": True,
        "manual_ci": int(cfg_idx),
        "freq_start": int(freq_start),
        "freq_index": int(freq_index),
        "rb_offset": 0,
        "zero_corr": int(zcz),
        "sequence_index": int(rsi),
        "restricted_set": restricted_rrc_to_matlab(prach.get("restricted_set_config")),
    }
