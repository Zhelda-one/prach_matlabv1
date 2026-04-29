"""PRACH occasion DataFrame → Plotly (Streamlit용, matplotlib 불필요)."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def fig_frame_distribution(df: pd.DataFrame) -> go.Figure:
    fc = df["frame"].value_counts().sort_index()
    fig = go.Figure(
        data=go.Bar(x=fc.index, y=fc.values, marker_color="#2E86AB", opacity=0.85),
    )
    fig.update_layout(
        title="프레임별 PRACH occasion 수",
        xaxis_title="Frame",
        yaxis_title="Occasions",
        height=360,
        margin=dict(t=50, b=40),
    )
    return fig


def fig_slot_distribution(df: pd.DataFrame) -> go.Figure:
    sc = df["slot"].value_counts().sort_index()
    fig = go.Figure(
        data=go.Bar(x=sc.index, y=sc.values, marker_color="#A23B72", opacity=0.85),
    )
    fig.update_layout(
        title="슬롯별 PRACH occasion 수",
        xaxis_title="Slot",
        yaxis_title="Occasions",
        height=360,
    )
    return fig


def fig_symbol_distribution(df: pd.DataFrame) -> go.Figure:
    sym = df["symbol"].value_counts().sort_index()
    fig = go.Figure(
        data=go.Bar(x=sym.index, y=sym.values, marker_color="#C73E1D", opacity=0.85),
    )
    fig.update_layout(
        title="심볼별 PRACH occasion 수",
        xaxis_title="OFDM symbol",
        yaxis_title="Occasions",
        height=360,
    )
    return fig


def fig_slot_symbol_heatmap(df: pd.DataFrame) -> go.Figure:
    heat = pd.crosstab(df["slot"], df["symbol"])
    fig = go.Figure(
        data=go.Heatmap(
            z=heat.values,
            x=heat.columns.astype(int),
            y=heat.index.astype(int),
            colorscale="YlOrRd",
            colorbar=dict(title="개수"),
        )
    )
    fig.update_layout(
        title="Slot × Symbol occasion 히트맵",
        xaxis_title="Slot",
        yaxis_title="Symbol",
        height=420,
    )
    return fig


def fig_cumulative_occasions(df: pd.DataFrame) -> go.Figure:
    cc = df.groupby("frame").size().cumsum()
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=cc.index,
            y=cc.values,
            mode="lines+markers",
            line=dict(color="#2E86AB", width=2),
            marker=dict(size=4),
            fill="tozeroy",
            fillcolor="rgba(46, 134, 171, 0.25)",
        )
    )
    fig.update_layout(
        title="누적 PRACH occasion 수 (프레임 기준)",
        xaxis_title="Frame",
        yaxis_title="Cumulative count",
        height=360,
    )
    return fig


def fig_gap_histogram(df: pd.DataFrame) -> go.Figure:
    d = df.sort_values("absolute_symbol").reset_index(drop=True)
    gaps = d["absolute_symbol"].diff().dropna()
    if gaps.empty:
        return go.Figure(layout_title_text="갭 데이터 없음")
    fig = go.Figure(
        data=go.Histogram(x=gaps, nbinsx=min(50, max(10, int(gaps.nunique()))), marker_color="#F18F01", opacity=0.8),
    )
    gm, gd = float(gaps.mean()), float(gaps.median())
    fig.add_vline(x=gm, line_dash="dash", line_color="red", annotation_text=f"mean {gm:.2f}")
    fig.add_vline(x=gd, line_dash="dash", line_color="green", annotation_text=f"median {gd:.2f}")
    fig.update_layout(
        title="연속 occasion 간 absolute_symbol 갭",
        xaxis_title="Gap (symbols)",
        yaxis_title="빈도",
        height=360,
    )
    return fig


def fig_preamble_top(df: pd.DataFrame, top_n: int = 20) -> go.Figure:
    pc = df["preamble_index"].value_counts().head(top_n).sort_values()
    fig = go.Figure(
        data=go.Bar(
            x=pc.values,
            y=[f"preamble {i}" for i in pc.index],
            orientation="h",
            marker_color="#764ba2",
            opacity=0.85,
        )
    )
    fig.update_layout(
        title=f"상위 {top_n} preamble_index (occasion 수)",
        xaxis_title="Occasions",
        height=max(280, 24 * len(pc) + 80),
        margin=dict(l=120),
    )
    return fig
