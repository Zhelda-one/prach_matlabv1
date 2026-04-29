"""
PRACH 시각화 모듈
Matplotlib을 사용한 다양한 차트 및 그래프 생성
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from typing import Tuple, Optional, List, Dict, Any
from pathlib import Path


class PRACHVisualizer:
    """PRACH 데이터 시각화 클래스"""
    
    def __init__(self, dataframe: pd.DataFrame, figsize: Tuple[int, int] = (16, 12)):
        """
        시각화기 초기화
        
        Args:
            dataframe: PRACH occasion DataFrame
            figsize: 기본 그림 크기
        """
        self.df = dataframe
        self.figsize = figsize
        self.colors = {
            'primary': '#2E86AB',
            'secondary': '#A23B72',
            'accent': '#F18F01',
            'success': '#C73E1D',
            'warning': '#F6AE2D',
        }
    
    def plot_frame_distribution(self, ax: Optional[plt.Axes] = None) -> plt.Axes:
        """프레임별 PRACH occasion 분포"""
        if ax is None:
            fig, ax = plt.subplots(figsize=(14, 4))
        
        frame_counts = self.df['frame'].value_counts().sort_index()
        ax.bar(frame_counts.index, frame_counts.values, color=self.colors['primary'], alpha=0.7, edgecolor='black')
        
        ax.set_xlabel('Frame Number', fontsize=11, fontweight='bold')
        ax.set_ylabel('Number of PRACH Occasions', fontsize=11, fontweight='bold')
        ax.set_title('PRACH Occasion Distribution by Frame', fontsize=12, fontweight='bold')
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        return ax
    
    def plot_slot_distribution(self, ax: Optional[plt.Axes] = None) -> plt.Axes:
        """슬롯별 PRACH occasion 분포"""
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 4))
        
        slot_counts = self.df['slot'].value_counts().sort_index()
        bars = ax.bar(slot_counts.index, slot_counts.values, color=self.colors['secondary'], alpha=0.7, edgecolor='black')
        
        # 최대값 표시
        max_idx = slot_counts.values.argmax()
        bars[max_idx].set_color(self.colors['accent'])
        
        ax.set_xlabel('Slot Number', fontsize=11, fontweight='bold')
        ax.set_ylabel('Number of PRACH Occasions', fontsize=11, fontweight='bold')
        ax.set_title('PRACH Occasion Distribution by Slot', fontsize=12, fontweight='bold')
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.set_xticks(range(int(slot_counts.index.min()), int(slot_counts.index.max()) + 1))
        
        return ax
    
    def plot_symbol_distribution(self, ax: Optional[plt.Axes] = None) -> plt.Axes:
        """심볼별 PRACH occasion 분포"""
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 4))
        
        symbol_counts = self.df['symbol'].value_counts().sort_index()
        bars = ax.bar(symbol_counts.index, symbol_counts.values, color=self.colors['success'], alpha=0.7, edgecolor='black')
        
        # 최대값 표시
        max_idx = symbol_counts.values.argmax()
        bars[max_idx].set_color(self.colors['accent'])
        
        ax.set_xlabel('Symbol Number', fontsize=11, fontweight='bold')
        ax.set_ylabel('Number of PRACH Occasions', fontsize=11, fontweight='bold')
        ax.set_title('PRACH Occasion Distribution by Symbol', fontsize=12, fontweight='bold')
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        return ax
    
    def plot_slot_symbol_heatmap(self, ax: Optional[plt.Axes] = None) -> plt.Axes:
        """Slot-Symbol 히트맵 (2D 분포)"""
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 6))
        
        # Pivot table 생성
        heatmap_data = pd.crosstab(self.df['slot'], self.df['symbol'])
        
        im = ax.imshow(heatmap_data.T, cmap='YlOrRd', aspect='auto', origin='lower')
        
        ax.set_xlabel('Slot Number', fontsize=11, fontweight='bold')
        ax.set_ylabel('Symbol Number', fontsize=11, fontweight='bold')
        ax.set_title('PRACH Occasion Distribution Heatmap (Slot x Symbol)', fontsize=12, fontweight='bold')
        
        # Colorbar 추가
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Occasion Count', fontsize=10)
        
        # 축 설정
        ax.set_xticks(range(len(heatmap_data.columns)))
        ax.set_xticklabels(heatmap_data.columns)
        ax.set_yticks(range(len(heatmap_data.index)))
        ax.set_yticklabels(heatmap_data.index)
        
        return ax
    
    def plot_temporal_distribution(self, ax: Optional[plt.Axes] = None) -> plt.Axes:
        """시간 영역 분포 (Frame 별 누적)"""
        if ax is None:
            fig, ax = plt.subplots(figsize=(14, 4))
        
        cumulative_counts = self.df.groupby('frame').size().cumsum()
        
        ax.plot(cumulative_counts.index, cumulative_counts.values, 
                color=self.colors['primary'], linewidth=2, marker='o', markersize=3)
        ax.fill_between(cumulative_counts.index, cumulative_counts.values, alpha=0.3, color=self.colors['primary'])
        
        ax.set_xlabel('Frame Number', fontsize=11, fontweight='bold')
        ax.set_ylabel('Cumulative PRACH Occasions', fontsize=11, fontweight='bold')
        ax.set_title('Cumulative PRACH Occasions Over Time', fontsize=12, fontweight='bold')
        ax.grid(alpha=0.3, linestyle='--')
        
        return ax
    
    def plot_preamble_distribution(self, ax: Optional[plt.Axes] = None, top_n: int = 20) -> plt.Axes:
        """상위 N개 프리앰블 인덱스 분포"""
        if ax is None:
            fig, ax = plt.subplots(figsize=(12, 4))
        
        preamble_counts = self.df['preamble_index'].value_counts().head(top_n)
        
        bars = ax.barh(range(len(preamble_counts)), preamble_counts.values, 
                       color=self.colors['secondary'], alpha=0.7, edgecolor='black')
        
        ax.set_yticks(range(len(preamble_counts)))
        ax.set_yticklabels([f"Preamble {i}" for i in preamble_counts.index])
        ax.set_xlabel('Number of Occasions', fontsize=11, fontweight='bold')
        ax.set_title(f'Top {top_n} Preamble Indices by Occasion Count', fontsize=12, fontweight='bold')
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        
        return ax
    
    def plot_gap_analysis(self, ax: Optional[plt.Axes] = None) -> plt.Axes:
        """PRACH occasion 간 갭 분석"""
        if ax is None:
            fig, ax = plt.subplots(figsize=(12, 4))
        
        df_sorted = self.df.sort_values('absolute_symbol').reset_index(drop=True)
        gaps = df_sorted['absolute_symbol'].diff().dropna()
        
        ax.hist(gaps, bins=50, color=self.colors['accent'], alpha=0.7, edgecolor='black')
        
        ax.set_xlabel('Gap (Symbols)', fontsize=11, fontweight='bold')
        ax.set_ylabel('Frequency', fontsize=11, fontweight='bold')
        ax.set_title('PRACH Occasion Gap Distribution', fontsize=12, fontweight='bold')
        ax.axvline(gaps.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {gaps.mean():.2f}')
        ax.axvline(gaps.median(), color='green', linestyle='--', linewidth=2, label=f'Median: {gaps.median():.2f}')
        ax.legend()
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        return ax
    
    def plot_frequency_distribution(self, ax: Optional[plt.Axes] = None) -> plt.Axes:
        """주파수 오프셋 분포"""
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 4))
        
        freq_counts = self.df['frequency_offset_rb'].value_counts().sort_index()
        bars = ax.bar(freq_counts.index, freq_counts.values, color=self.colors['warning'], alpha=0.7, edgecolor='black')
        
        ax.set_xlabel('Frequency Offset (RB)', fontsize=11, fontweight='bold')
        ax.set_ylabel('Number of Occasions', fontsize=11, fontweight='bold')
        ax.set_title('PRACH Occasion Distribution by Frequency Offset', fontsize=12, fontweight='bold')
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        return ax
    
    def plot_comprehensive_dashboard(self, output_path: Optional[str] = None) -> plt.Figure:
        """종합 대시보드"""
        fig = plt.figure(figsize=(20, 16))
        gs = GridSpec(4, 3, figure=fig, hspace=0.35, wspace=0.3)
        
        # 1. Frame Distribution
        ax1 = fig.add_subplot(gs[0, :2])
        self.plot_frame_distribution(ax=ax1)
        
        # 2. Summary Stats
        ax2 = fig.add_subplot(gs[0, 2])
        self._plot_summary_stats(ax=ax2)
        
        # 3. Slot Distribution
        ax3 = fig.add_subplot(gs[1, 0])
        self.plot_slot_distribution(ax=ax3)
        
        # 4. Symbol Distribution
        ax4 = fig.add_subplot(gs[1, 1])
        self.plot_symbol_distribution(ax=ax4)
        
        # 5. Frequency Distribution
        ax5 = fig.add_subplot(gs[1, 2])
        self.plot_frequency_distribution(ax=ax5)
        
        # 6. Slot-Symbol Heatmap
        ax6 = fig.add_subplot(gs[2, :2])
        self.plot_slot_symbol_heatmap(ax=ax6)
        
        # 7. Preamble Distribution
        ax7 = fig.add_subplot(gs[2, 2])
        self.plot_preamble_distribution(ax=ax7, top_n=10)
        
        # 8. Temporal Distribution
        ax8 = fig.add_subplot(gs[3, :2])
        self.plot_temporal_distribution(ax=ax8)
        
        # 9. Gap Analysis
        ax9 = fig.add_subplot(gs[3, 2])
        self.plot_gap_analysis(ax=ax9)
        
        # 메인 제목
        fig.suptitle('PRACH Occasion Comprehensive Analysis Dashboard', 
                     fontsize=16, fontweight='bold', y=0.995)
        
        if output_path:
            fig.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"Dashboard saved to {output_path}")
        
        return fig
    
    def _plot_summary_stats(self, ax: Optional[plt.Axes] = None) -> plt.Axes:
        """요약 통계 박스"""
        if ax is None:
            fig, ax = plt.subplots(figsize=(6, 4))
        
        ax.axis('off')
        
        stats_text = f"""
        SUMMARY STATISTICS
        {'='*35}
        Total Occasions: {len(self.df):,}
        Frame Range: {self.df['frame'].min():.0f} - {self.df['frame'].max():.0f}
        Unique Slots: {self.df['slot'].nunique()}
        Unique Symbols: {self.df['symbol'].nunique()}
        Occasions/Frame: {len(self.df) / (self.df['frame'].max() - self.df['frame'].min() + 1):.2f}
        
        Most Common Slot: {self.df['slot'].mode()[0]:.0f}
        Most Common Symbol: {self.df['symbol'].mode()[0]:.0f}
        Most Common Preamble: {self.df['preamble_index'].mode()[0]:.0f}
        """
        
        ax.text(0.1, 0.95, stats_text, transform=ax.transAxes, fontsize=9,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        return ax
    
    def export_all_plots(self, output_dir: str) -> None:
        """모든 플롯을 개별 파일로 내보내기"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        plots = [
            ('frame_distribution', self.plot_frame_distribution),
            ('slot_distribution', self.plot_slot_distribution),
            ('symbol_distribution', self.plot_symbol_distribution),
            ('slot_symbol_heatmap', self.plot_slot_symbol_heatmap),
            ('temporal_distribution', self.plot_temporal_distribution),
            ('preamble_distribution', self.plot_preamble_distribution),
            ('gap_analysis', self.plot_gap_analysis),
            ('frequency_distribution', self.plot_frequency_distribution),
        ]
        
        for plot_name, plot_func in plots:
            fig, ax = plt.subplots(figsize=(12, 6))
            plot_func(ax=ax)
            
            output_file = output_path / f"{plot_name}.png"
            fig.savefig(output_file, dpi=150, bbox_inches='tight')
            print(f"Saved {plot_name} to {output_file}")
            plt.close(fig)
        
        # 종합 대시보드
        output_file = output_path / "comprehensive_dashboard.png"
        self.plot_comprehensive_dashboard(output_path=str(output_file))


if __name__ == '__main__':
    # 테스트를 위해 더미 데이터 생성
    np.random.seed(42)
    dummy_data = {
        'occasion_id': range(500),
        'frame': np.repeat(range(50), 10),
        'subframe': np.tile(range(10), 50),
        'slot': np.tile(np.repeat(range(5), 2), 50),
        'symbol': np.tile([0, 1], 250),
        'preamble_index': np.random.randint(0, 64, 500),
        'prach_config_index': [14] * 500,
        'frequency_offset_rb': [7] * 500,
        'duration_symbols': [1] * 500,
        'absolute_slot': range(500),
        'absolute_symbol': np.arange(500) * 2,
        'frequency_khz': [7 * 12 * 15 / 1000] * 500,
    }
    
    df = pd.DataFrame(dummy_data)
    visualizer = PRACHVisualizer(df)
    
    # 종합 대시보드 생성
    fig = visualizer.plot_comprehensive_dashboard()
    plt.show()
