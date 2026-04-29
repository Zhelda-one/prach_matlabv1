# 파일명: app.py
import sys

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import io
import json

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="5G NR PRACH Suite (FDD·15 kHz)", layout="wide")

MODES = (
    "MATLAB PRACH (FDD·15 kHz)",
    "SIB1 occasion 분석 (FDD·15 kHz)",
)

# MATLAB 경로에서만 사용 (지연 로드)
@st.cache_resource
def matlab_engine():
    import matlab.engine

    return matlab.engine.start_matlab()


def fig_prach_time_domain_structure(
    tcp_np: np.ndarray,
    tseq_np: np.ndarray,
    gp_np: np.ndarray,
    sym_loc: float,
    prach_dur: float,
) -> go.Figure:
    """
    MATLAB 문서의 PRACH time-domain structure(hPRACHPreamblePlot)와 같이,
    PRACH 슬롯 그리드의 각 OFDM 심볼 행에서 CP / TSEQ / GP 구간을 색으로 표시한다.
    진한 색: 현재 TimeIndex occasion (SymbolLocation ~ SymbolLocation+PRACHDuration-1).
    옅은 색: 같은 슬롯의 다른 PRACH time occasion 구간.
    """
    tcp_np = np.asarray(tcp_np, dtype=float).flatten()
    tseq_np = np.asarray(tseq_np, dtype=float).flatten()
    gp_np = np.asarray(gp_np, dtype=float).flatten()
    n = min(len(tcp_np), len(tseq_np), len(gp_np))
    if n == 0:
        fig = go.Figure()
        fig.update_layout(title="TCP/TSEQ/GP 길이 없음", height=200)
        return fig

    tcp_np = tcp_np[:n]
    tseq_np = tseq_np[:n]
    gp_np = gp_np[:n]

    sym0 = int(sym_loc)
    dur = max(0, int(prach_dur))

    starts = np.zeros(n)
    for i in range(1, n):
        starts[i] = starts[i - 1] + tcp_np[i - 1] + tseq_np[i - 1] + gp_np[i - 1]

    cp_hi, seq_hi, gp_hi = "#C0392B", "#2471A3", "#1E8449"
    cp_lo, seq_lo, gp_lo = "rgba(236, 176, 170, 0.55)", "rgba(174, 214, 241, 0.55)", "rgba(186, 230, 201, 0.55)"

    fig = go.Figure()

    for s in range(n):
        base = starts[s]
        a, b, c = float(tcp_np[s]), float(tseq_np[s]), float(gp_np[s])
        if a + b + c <= 0:
            continue
        in_curr = sym0 <= s < sym0 + dur
        c_cp, c_seq, c_gp = (cp_hi, seq_hi, gp_hi) if in_curr else (cp_lo, seq_lo, gp_lo)

        x0 = base
        fig.add_shape(
            type="rect",
            x0=x0,
            x1=x0 + a,
            y0=s - 0.42,
            y1=s + 0.42,
            fillcolor=c_cp,
            line=dict(width=0),
            layer="below",
        )
        x0 += a
        fig.add_shape(
            type="rect",
            x0=x0,
            x1=x0 + b,
            y0=s - 0.42,
            y1=s + 0.42,
            fillcolor=c_seq,
            line=dict(width=0),
            layer="below",
        )
        x0 += b
        fig.add_shape(
            type="rect",
            x0=x0,
            x1=x0 + c,
            y0=s - 0.42,
            y1=s + 0.42,
            fillcolor=c_gp,
            line=dict(width=0),
            layer="below",
        )

    x_end = float(starts[-1] + tcp_np[-1] + tseq_np[-1] + gp_np[-1])

    fig.update_layout(
        title="PRACH time-domain structure (심볼별 CP · Preamble · GP)",
        xaxis_title="시간 축 — PRACH 슬롯 시작부터의 샘플 인덱스",
        yaxis_title="PRACH 슬롯 그리드 OFDM symbol 인덱스",
        height=max(320, min(720, 80 + n * 28)),
        margin=dict(l=60, r=20, t=50, b=48),
        xaxis=dict(range=[0, x_end * 1.02], zeroline=False),
        yaxis=dict(
            range=[-0.6, (n - 1) + 0.6],
            tickmode="linear",
            tick0=0,
            dtick=1,
            zeroline=False,
        ),
    )

    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(size=11, color=cp_hi),
            name="CP",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(size=11, color=seq_hi),
            name="Preamble (TSEQ)",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(size=11, color=gp_hi),
            name="GP",
        )
    )
    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )

    return fig


def fig_prach_time_structure_single_strip(
    tcp_np: np.ndarray,
    tseq_np: np.ndarray,
    gp_np: np.ndarray,
    sym_loc: float,
    prach_dur: float,
) -> go.Figure:
    """슬롯 전체를 한 줄 타임라인으로 이어 붙인 뷰 (연속 샘플 축)."""
    tcp_np = np.asarray(tcp_np, dtype=float).flatten()
    tseq_np = np.asarray(tseq_np, dtype=float).flatten()
    gp_np = np.asarray(gp_np, dtype=float).flatten()
    n = min(len(tcp_np), len(tseq_np), len(gp_np))
    if n == 0:
        return go.Figure()

    sym0 = int(sym_loc)
    dur = max(0, int(prach_dur))

    cp_hi, seq_hi, gp_hi = "#C0392B", "#2471A3", "#1E8449"
    cp_lo, seq_lo, gp_lo = "rgba(236, 176, 170, 0.55)", "rgba(174, 214, 241, 0.55)", "rgba(186, 230, 201, 0.55)"

    fig = go.Figure()
    x0 = 0.0
    for s in range(n):
        a, b, c = float(tcp_np[s]), float(tseq_np[s]), float(gp_np[s])
        if a + b + c <= 0:
            continue
        in_curr = sym0 <= s < sym0 + dur
        c_cp, c_seq, c_gp = (cp_hi, seq_hi, gp_hi) if in_curr else (cp_lo, seq_lo, gp_lo)

        fig.add_shape(
            type="rect",
            x0=x0,
            x1=x0 + a,
            y0=-0.45,
            y1=0.45,
            fillcolor=c_cp,
            line=dict(width=0),
            layer="below",
        )
        x0 += a
        fig.add_shape(
            type="rect",
            x0=x0,
            x1=x0 + b,
            y0=-0.45,
            y1=0.45,
            fillcolor=c_seq,
            line=dict(width=0),
            layer="below",
        )
        x0 += b
        fig.add_shape(
            type="rect",
            x0=x0,
            x1=x0 + c,
            y0=-0.45,
            y1=0.45,
            fillcolor=c_gp,
            line=dict(width=0),
            layer="below",
        )
        x0 += c

    fig.update_layout(
        title="PRACH time-domain structure — 연속 타임라인 (슬롯 전체)",
        xaxis_title="샘플 인덱스 (슬롯 시작 기준)",
        yaxis=dict(visible=False, range=[-0.7, 0.7]),
        height=220,
        margin=dict(l=40, r=20, t=50, b=40),
        showlegend=False,
    )
    return fig


def carrier_slot_duration_ms(carrier_scs_khz: float) -> float:
    """NR FR1에서 일반적으로 사용하는 캐리어 슬롯 길이(ms): 1 ms / 2^μ,  Δf=15·2^μ kHz."""
    scs = float(carrier_scs_khz)
    if scs <= 0:
        return 1.0
    mu = int(round(np.log2(scs / 15.0)))
    mu = max(0, mu)
    return 1.0 / (2.0**mu)


def fig_prach_preamble_plot_matlab_style(
    tcp_np: np.ndarray,
    tseq_np: np.ndarray,
    gp_np: np.ndarray,
    sym_loc: float,
    prach_dur: float,
    carrier_scs_khz: float,
    nprach_slot: int,
    prach_format: str,
    sample_rate_hz: float,
    nfft: int,
    prach_scs_khz: float,
) -> go.Figure:
    """
    MATLAB `hPRACHPreamblePlot` 도움말 그림과 유사:
    한 캐리어 슬롯(Time [ms]) 안에서 CP / Sequence / GP 띠, current vs other occasion 색 구분.
    """
    tcp_np = np.asarray(tcp_np, dtype=float).flatten()
    tseq_np = np.asarray(tseq_np, dtype=float).flatten()
    gp_np = np.asarray(gp_np, dtype=float).flatten()
    n = min(len(tcp_np), len(tseq_np), len(gp_np))
    if n == 0:
        return go.Figure()

    fs = float(sample_rate_hz)
    if np.isnan(fs) or fs <= 0:
        fs = float(nfft) * float(prach_scs_khz) * 1000.0
    if fs <= 0:
        fs = 1.0

    def sm_to_ms(samp: float) -> float:
        return float(samp) / fs * 1000.0

    sym0 = int(sym_loc)
    dur = max(0, int(prach_dur))

    # MATLAB 범례와 비슷한 색: current = 진하게, other = 연한 핑크/블루/그린
    cp_cur, seq_cur, gp_cur = "#E67E22", "#2980B9", "#27AE60"
    cp_oth, seq_oth = "#F5B7B1", "#AED6F1"
    gp_oth = "rgba(171, 223, 194, 0.75)"

    fig = go.Figure()
    x0_ms = 0.0
    for s in range(n):
        a, b, c = float(tcp_np[s]), float(tseq_np[s]), float(gp_np[s])
        if a + b + c <= 0:
            continue
        in_curr = sym0 <= s < sym0 + dur
        if in_curr:
            c_cp, c_seq, c_gp = cp_cur, seq_cur, gp_cur
        else:
            c_cp, c_seq, c_gp = cp_oth, seq_oth, gp_oth

        w = sm_to_ms(a)
        fig.add_shape(
            type="rect",
            x0=x0_ms,
            x1=x0_ms + w,
            y0=-0.48,
            y1=0.48,
            fillcolor=c_cp,
            line=dict(width=0),
            layer="below",
        )
        x0_ms += w
        w = sm_to_ms(b)
        fig.add_shape(
            type="rect",
            x0=x0_ms,
            x1=x0_ms + w,
            y0=-0.48,
            y1=0.48,
            fillcolor=c_seq,
            line=dict(width=0),
            layer="below",
        )
        x0_ms += w
        w = sm_to_ms(c)
        fig.add_shape(
            type="rect",
            x0=x0_ms,
            x1=x0_ms + w,
            y0=-0.48,
            y1=0.48,
            fillcolor=c_gp,
            line=dict(width=0),
            layer="below",
        )
        x0_ms += w

    slot_ms = carrier_slot_duration_ms(carrier_scs_khz)
    x_max = max(slot_ms, x0_ms * 1.02)

    ttl = (
        f"Time-Domain Structure of PRACH Preamble Format {prach_format} "
        f"within One {carrier_scs_khz:g} kHz Carrier Slot (NPRACHSlot = {int(nprach_slot)})"
    )

    fig.update_layout(
        title=dict(text=ttl, x=0.5, xanchor="center"),
        xaxis_title="Time [ms]",
        yaxis=dict(visible=False, range=[-0.65, 0.65]),
        height=300,
        margin=dict(l=50, r=30, t=80, b=50),
        xaxis=dict(range=[0, x_max], zeroline=False),
    )

    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(size=10, color=cp_cur),
            name="Cyclic Prefix — current",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(size=10, color=seq_cur),
            name="Sequence — current",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(size=10, color=gp_cur),
            name="Guard Period — current",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(size=10, color=cp_oth),
            name="Cyclic Prefix (other)",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(size=10, color=seq_oth),
            name="Sequence (other)",
        )
    )
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=10),
        ),
    )

    return fig


st.title("5G NR PRACH")
st.caption(
    "단일 앱: **MATLAB** 리소스 그리드·파형 / **SIB1** occasion·통계. "
    "현재 통합 범위는 **FDD·캐리어 15 kHz** 만 지원합니다."
)

# SIB→MATLAB 브리지는 라디오 생성 전에만 prach_suite_mode 를 바꿀 수 있음
if st.session_state.pop("_goto_matlab_next", False):
    st.session_state["prach_suite_mode"] = MODES[0]

mode = st.sidebar.radio("화면", MODES, key="prach_suite_mode")

if mode == MODES[0]:
    for _k, _v in (
        ("sb_use_manual_ci", False),
        ("sb_manual_ci", 146),
        ("sb_format", "B2"),
        ("sb_seq", 0),
        ("sb_preamble", 0),
        ("sb_restricted", "UnrestrictedSet"),
        ("sb_zcz", 0),
        ("sb_rb_offset", 0),
        ("sb_freq_start", 0),
        ("sb_freq_index", 0),
        ("sb_time_idx", -1),
    ):
        st.session_state.setdefault(_k, _v)

    st.sidebar.header("Carrier (고정)")
    st.sidebar.info("DuplexMode: **FDD** · Carrier SCS: **15 kHz**")
    carrier_scs = 15.0
    duplex_mode = "FDD"
    n_size_grid = st.sidebar.number_input("NSizeGrid (RB)", min_value=1, max_value=275, value=52, step=1)

    st.sidebar.header("PRACH preamble")
    format_type = st.sidebar.selectbox(
        "Preamble Format",
        ["0", "1", "2", "3", "A1", "A2", "A3", "B1", "B2", "B3", "B4", "C0", "C2"],
        key="sb_format",
    )
    use_manual_ci = st.sidebar.checkbox("ConfigurationIndex 직접 지정", key="sb_use_manual_ci")
    manual_ci = st.sidebar.number_input(
        "ConfigurationIndex (수동)",
        min_value=0,
        max_value=255,
        step=1,
        disabled=not use_manual_ci,
        key="sb_manual_ci",
    )

    sequence_index = st.sidebar.number_input(
        "SequenceIndex", min_value=0, max_value=1149, step=1, key="sb_seq"
    )
    preamble_index = st.sidebar.number_input("PreambleIndex", min_value=0, max_value=63, step=1, key="sb_preamble")

    restricted_set = st.sidebar.selectbox(
        "RestrictedSet",
        ["UnrestrictedSet", "RestrictedSetTypeA", "RestrictedSetTypeB"],
        key="sb_restricted",
    )
    zero_corr = st.sidebar.number_input(
        "ZeroCorrelationZone",
        min_value=0,
        max_value=15,
        step=1,
        key="sb_zcz",
    )
    rb_offset = st.sidebar.number_input("RBOffset", min_value=0, max_value=274, step=1, key="sb_rb_offset")
    freq_start = st.sidebar.number_input(
        "FrequencyStart",
        min_value=0,
        max_value=274,
        step=1,
        key="sb_freq_start",
    )
    freq_index = st.sidebar.number_input("FrequencyIndex", min_value=0, max_value=7, step=1, key="sb_freq_index")

    st.sidebar.markdown("---")
    st.sidebar.caption("TimeIndex: −1 이면 자동(B2/B3 은 마지막 occasion).")
    time_idx_override = st.sidebar.number_input("TimeIndex (−1 = 자동)", min_value=-1, max_value=6, step=1, key="sb_time_idx")

    st.markdown(
        "### MATLAB 5G Toolbox\n"
        "`nrCarrierConfig`, `nrPRACHConfig` 흐름으로 리소스 그리드와 시간 영역 파형을 생성합니다."
    )

    if st.sidebar.button("생성 — 그리드 & 파형 & 정보", type="primary"):
        use_m = 1.0 if use_manual_ci else 0.0
        t_override = float(time_idx_override)

        try:
            eng = matlab_engine()
        except Exception as e:
            st.error(f"MATLAB 엔진을 시작할 수 없습니다.\n\n{type(e).__name__}: {e}")
            st.stop()

        with st.spinner("MATLAB에서 계산 중..."):
            eng.eval("clear prach_backend", nargout=0)
            outs = eng.prach_backend(
                format_type,
                float(carrier_scs),
                float(n_size_grid),
                duplex_mode,
                float(sequence_index),
                float(preamble_index),
                restricted_set,
                float(zero_corr),
                float(rb_offset),
                float(freq_start),
                float(freq_index),
                float(use_m),
                float(manual_ci),
                float(t_override),
                nargout=17,
            )
            (
                config_idx,
                w_real,
                w_imag,
                err_msg,
                nfft,
                win_len,
                tcp,
                tseq,
                gp,
                grid_mag,
                prach_format,
                num_time_occ,
                prach_dur,
                sym_loc,
                npr_slot,
                ap_slot,
                sample_rate_hz,
            ) = outs

        if config_idx == -1:
            st.error(f"MATLAB 오류:\n\n{err_msg}")
        else:
            st.success(
                f"완료 — ConfigurationIndex **{int(config_idx)}**, "
                f"Format **{prach_format}**, NPRACHSlot **{int(npr_slot)}**, "
                f"ActivePRACHSlot **{int(ap_slot)}**"
            )

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("NumTimeOccasions", f"{float(num_time_occ):.0f}")
            c2.metric("PRACHDuration (symbols)", f"{float(prach_dur):.0f}")
            c3.metric("SymbolLocation", f"{float(sym_loc):.0f}")
            c4.metric("Nfft", f"{int(nfft)}")
    
            tcp_np = np.array(tcp, dtype=float).flatten()
            tseq_np = np.array(tseq, dtype=float).flatten()
            gp_np = np.array(gp, dtype=float).flatten()
    
            if format_type in ["0", "1", "2"]:
                prach_scs = 1.25
            elif format_type == "3":
                prach_scs = 5.0
            else:
                prach_scs = float(carrier_scs)
    
            num_sc = int(n_size_grid) * 12
    
            sr_use = float(sample_rate_hz)
    
            console_text = "Information associated with PRACH:\n"
            console_text += f"   SubcarrierSpacing:         {prach_scs:g} kHz\n"
            console_text += f"   Number of subcarriers:     {num_sc}\n\n"
            console_text += "Information associated with PRACH OFDM modulation:\n"
            console_text += f"   Nfft:                      {int(nfft)}\n"
            console_text += f"   Windowing:                 {int(win_len)}\n"
            console_text += "   Offset:                    0 samples\n\n"
            console_text += "   Symbol    TCP     TSEQ       GP\n"
            console_text += "   ------  ------   ------    -----\n"
            for i in range(len(tcp_np)):
                gpi = int(gp_np[i]) if i < len(gp_np) else 0
                console_text += f"     {i:<4}    {int(tcp_np[i]):<8} {int(tseq_np[i]):<9} {gpi}\n"
    
            st.divider()
            st.subheader("PRACH OFDM modulation 정보")
            st.code(console_text, language="text")
    
            # --- MATLAB hPRACHPreamblePlot 스타일: Time [ms], 한 캐리어 슬롯 ---
            st.divider()
            st.subheader("Time-domain structure (`hPRACHPreamblePlot` 스타일)")
            st.caption(
                "가로축: **Time [ms]** (PRACH OFDM 샘플레이트로 TCP/TSEQ/GP 샘플 길이 환산). "
                "범위는 NR 슬롯 길이(예: 15 kHz → 1 ms) 이상으로 맞춤. "
                f"SampleRate: {sr_use:g} Hz (MATLAB `prachInfo.SampleRate`, 없으면 Nfft×PRACH SCS 추정)."
            )
            fig_mw = fig_prach_preamble_plot_matlab_style(
                tcp_np,
                tseq_np,
                gp_np,
                float(sym_loc),
                float(prach_dur),
                float(carrier_scs),
                int(npr_slot),
                str(prach_format),
                sr_use,
                int(nfft),
                float(prach_scs),
            )
            st.plotly_chart(fig_mw, width="stretch")
    
            # --- MATLAB 문서형: PRACH time-domain structure (CP / preamble / GP) ---
            st.divider()
            st.subheader("PRACH time-domain structure (심볼 행·샘플 축)")
            st.caption(
                "색: CP(적)·Preamble/TSEQ(청)·GP(녹). 진한색 = 현재 TimeIndex 구간 "
                "(SymbolLocation ~ SymbolLocation + PRACHDuration − 1), 옅은색 = 다른 occasion."
            )
            fig_td = fig_prach_time_domain_structure(
                tcp_np, tseq_np, gp_np, float(sym_loc), float(prach_dur)
            )
            st.plotly_chart(fig_td, width="stretch")
    
            with st.expander("연속 타임라인 뷰 — 슬롯 전체를 한 줄로"):
                st.caption("모든 OFDM 심볼 구간을 시간 순으로 이어 붙인 샘플 축입니다.")
                fig_strip = fig_prach_time_structure_single_strip(
                    tcp_np, tseq_np, gp_np, float(sym_loc), float(prach_dur)
                )
                st.plotly_chart(fig_strip, width="stretch")
    
            # --- 리소스 그리드 (문서 예제와 동일하게 magnitude 맵) ---
            st.divider()
            st.subheader("PRACH resource grid — |grid|")
            Z = np.abs(np.array(grid_mag, dtype=float))
            if Z.ndim == 1:
                st.warning("그리드 차원을 알 수 없어 표시를 건너뜁니다.")
            else:
                fig_g = go.Figure(
                    data=go.Heatmap(
                        z=np.flipud(Z),
                        colorscale="Blues",
                        colorbar=dict(title="|값|"),
                    )
                )
                fig_g.update_layout(
                    xaxis_title="OFDM symbol 인덱스 (PRACH 슬롯 그리드)",
                    yaxis_title="부반송파 인덱스 (아래가 저주파)",
                    margin=dict(l=0, r=0, t=40, b=0),
                    height=420,
                )
                st.plotly_chart(fig_g, width="stretch")
    
            # --- 시간 영역: I/Q + 크기 (문서의 time-domain 파형에 대응) ---
            st.divider()
            st.subheader("시간 영역 파형")
            w_real_np = np.array(w_real, dtype=float).flatten()
            w_imag_np = np.array(w_imag, dtype=float).flatten()
            mag = np.sqrt(w_real_np ** 2 + w_imag_np ** 2)
            t_ax = np.arange(len(mag))
    
            fig_w = go.Figure()
            fig_w.add_trace(
                go.Scatter(x=t_ax, y=w_real_np, mode="lines", name="Real", line=dict(color="blue"))
            )
            fig_w.add_trace(
                go.Scatter(
                    x=t_ax,
                    y=w_imag_np,
                    mode="lines",
                    name="Imag",
                    line=dict(color="orange"),
                    opacity=0.75,
                )
            )
            fig_w.add_trace(
                go.Scatter(
                    x=t_ax,
                    y=mag,
                    mode="lines",
                    name="Magnitude",
                    line=dict(color="green", width=1.5),
                )
            )
            fig_w.update_layout(
                xaxis_title="Time sample",
                yaxis_title="Amplitude",
                hovermode="x unified",
                margin=dict(l=0, r=0, t=30, b=0),
                height=400,
            )
            st.plotly_chart(fig_w, width="stretch")
    
            with st.expander("적용된 RRC 관련 필드 요약"):
                st.markdown(
                    f"""
- **DuplexMode:** `{duplex_mode}`
- **Carrier SCS:** {carrier_scs} kHz, **NSizeGrid:** {n_size_grid}
- **SequenceIndex / PreambleIndex:** {sequence_index} / {preamble_index}
- **RestrictedSet:** `{restricted_set}`, **ZeroCorrelationZone:** {zero_corr}
- **RBOffset / FrequencyStart / FrequencyIndex:** {rb_offset} / {freq_start} / {freq_index}
- **TimeIndex override:** {time_idx_override} (−1 = 자동)
"""
                )

else:
    st.markdown(
        "### SIB1 occasion 분석 (Python)\n"
        "텍스트 SIB1에서 `rach_ConfigGeneric` 필드를 읽고, **TS 38.104 FR1·configuration index 0–63·15 kHz** "
        "표 기반으로 occasion 테이블을 만듭니다. MATLAB IQ 파형은 포함되지 않습니다."
    )
    st.info(
        "Occasion 수 = (조건에 맞는 슬롯/심볼) × 64 preamble 가정이라 통계는 **경향**으로만 보세요. "
        "MATLAB과 숫자가 다를 수 있습니다."
    )

    try:
        from sib_prach import (
            PRACHCalculator,
            PRACHDataAnalyzer,
            SIB1Parser,
            SubcarrierSpacing,
            matlab_prefill_from_prach_config,
        )
        from sib_prach.plotly_viz import (
            fig_cumulative_occasions,
            fig_frame_distribution,
            fig_gap_histogram,
            fig_preamble_top,
            fig_slot_distribution,
            fig_slot_symbol_heatmap,
            fig_symbol_distribution,
        )
    except ImportError as e:
        st.error(f"`sib_prach` 패키지를 불러올 수 없습니다: {e}")
        st.stop()

    up = st.file_uploader("SIB1 로그 (.txt)", type=["txt"], key="sib_upload")
    num_frames = st.number_input("분석 프레임 수", min_value=1, max_value=10240, value=200, step=1, key="sib_nframes")

    if st.button("파싱 및 occasion 계산", type="primary", key="sib_run"):
        if up is None:
            st.warning("먼저 SIB1 텍스트 파일을 업로드하세요.")
        else:
            raw = up.getvalue().decode("utf-8", errors="replace")
            try:
                parser = SIB1Parser(text=raw)
                data = parser.parse()
            except Exception as e:
                st.error(f"SIB1 파싱 실패: {e}")
                st.stop()

            prach = data["prach_config"]
            with st.expander("파싱된 PRACH 필드", expanded=False):
                st.json(prach)

            idx = prach.get("prach_configuration_index")
            if idx is None or idx < 0 or idx > 63:
                st.error(
                    "이 통합 버전의 Python 계산기는 **prach_ConfigurationIndex 0–63** 만 지원합니다. "
                    "다른 인덱스는 MATLAB 탭에서 수동으로 확인하세요."
                )
                st.stop()

            try:
                calc = PRACHCalculator(
                    prach_config_index=int(idx),
                    msg1_fdm=int(prach.get("msg1_fdm_value") or 1),
                    msg1_frequency_start=int(prach.get("msg1_frequency_start") or 0),
                    scs=SubcarrierSpacing.KHZ_15,
                    zero_correlation_zone_config=int(prach.get("zero_correlation_zone_config") or 0),
                )
                df = calc.calculate_prach_timing(num_frames=int(num_frames))
            except Exception as e:
                st.error(f"Occasion 계산 실패: {e}")
                st.stop()

            st.session_state["sib_last_df"] = df
            st.session_state["sib_last_prach"] = prach
            st.success(f"총 **{len(df):,}** 행 (프레임 수 {int(num_frames)})")

    df_sib = st.session_state.get("sib_last_df")
    prach_sib = st.session_state.get("sib_last_prach")
    if df_sib is not None and prach_sib is not None:
        rep = PRACHDataAnalyzer(df_sib).generate_full_report()

        o1, o2, o3, o4 = st.columns(4)
        o1.metric("총 occasion", f"{rep['overview']['total_occasions']:,}")
        o2.metric("프레임 범위", f"{rep['overview']['frame_range'][0]}–{rep['overview']['frame_range'][1]}")
        o3.metric("프레임당 평균", f"{rep['frame_analysis']['occasions_per_frame_mean']:.2f}")
        o4.metric("충돌 패턴 수", f"{rep['collision_analysis']['total_collision_patterns']}")

        st.plotly_chart(fig_frame_distribution(df_sib), width="stretch")
        cA, cB = st.columns(2)
        with cA:
            st.plotly_chart(fig_slot_distribution(df_sib), width="stretch")
        with cB:
            st.plotly_chart(fig_symbol_distribution(df_sib), width="stretch")
        st.plotly_chart(fig_slot_symbol_heatmap(df_sib), width="stretch")
        cC, cD = st.columns(2)
        with cC:
            st.plotly_chart(fig_cumulative_occasions(df_sib), width="stretch")
        with cD:
            st.plotly_chart(fig_gap_histogram(df_sib), width="stretch")
        st.plotly_chart(fig_preamble_top(df_sib), width="stretch")

        st.subheader("데이터 미리보기")
        st.dataframe(df_sib.head(200), height=320)

        csv_buf = io.StringIO()
        df_sib.to_csv(csv_buf, index=False)
        st.download_button(
            "occasions.csv 다운로드",
            data=csv_buf.getvalue().encode("utf-8"),
            file_name="prach_occasions.csv",
            mime="text/csv",
            key="dl_csv",
        )

        def _json_safe(obj):
            if isinstance(obj, (np.integer, np.floating)):
                return float(obj)
            if isinstance(obj, dict):
                return {k: _json_safe(v) for k, v in obj.items()}
            if isinstance(obj, (list, tuple)):
                return [_json_safe(v) for v in obj]
            return obj

        st.download_button(
            "analysis_report.json 다운로드",
            data=json.dumps(_json_safe(rep), indent=2).encode("utf-8"),
            file_name="analysis_report.json",
            mime="application/json",
            key="dl_json",
        )

        st.divider()
        st.subheader("MATLAB 탭으로 값 반영")
        st.caption(
            "Preamble Format은 SIB1에 직접 없으므로 MATLAB 탭에서 그대로 둡니다. "
            "ConfigurationIndex·FrequencyStart·ZCZ·SequenceIndex·RestrictedSet 만 채웁니다."
        )
        if st.button("위 파싱값을 MATLAB 사이드바에 적용", key="sib_bridge"):
            try:
                pre = matlab_prefill_from_prach_config(prach_sib)
            except Exception as e:
                st.error(str(e))
            else:
                st.session_state["sb_use_manual_ci"] = True
                st.session_state["sb_manual_ci"] = int(pre["manual_ci"])
                st.session_state["sb_freq_start"] = int(pre["freq_start"])
                st.session_state["sb_freq_index"] = int(pre["freq_index"])
                st.session_state["sb_rb_offset"] = int(pre["rb_offset"])
                st.session_state["sb_zcz"] = int(pre["zero_corr"])
                st.session_state["sb_seq"] = int(pre["sequence_index"])
                st.session_state["sb_restricted"] = pre["restricted_set"]
                st.session_state["_goto_matlab_next"] = True
                st.success("MATLAB 화면으로 전환합니다. Preamble Format 확인 후 생성을 누르세요.")
                st.rerun()
