"""
PRACH Time-Frequency Domain Mapper
Frame/Subframe/Slot/Symbol와 RB/Subcarrier 2차원 매핑
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from typing import List, Dict, Any, Tuple
from pathlib import Path


class PRACHTimeFrequencyMapper:
    """PRACH의 시간-주파수 영역 매핑을 시각화하는 클래스"""
    
    # 3GPP 38.104 Table 6.3.3.2-3: PRACH occasions in a 10ms frame for FR1
    # Format: slot index where PRACH occurs (for PRACH config index 14)
    PRACH_CONFIG_14_SLOTS = [0]  # Config 14는 slot 0에서만 발생 (매 프레임)
    
    def __init__(self, 
                 prach_config_index: int,
                 msg1_frequency_start: int,
                 msg1_fdm: int,
                 num_frames: int = 100,
                 scs: int = 15):  # 15 kHz
        """
        Time-Frequency Mapper 초기화
        
        Args:
            prach_config_index: PRACH Configuration Index
            msg1_frequency_start: msg1 Frequency Start (RB 단위)
            msg1_fdm: msg1 FDM (1, 2, 4, or 8)
            num_frames: 분석할 프레임 수
            scs: 부반송파 간격 (kHz)
        """
        self.prach_config_index = prach_config_index
        self.msg1_frequency_start = msg1_frequency_start
        self.msg1_fdm = msg1_fdm
        self.num_frames = num_frames
        self.scs = scs
        
        # PRACH 파라미터
        self.prach_duration_symbols = 1  # 일반적으로 1 symbol
        self.rbs_per_prach = 6  # 표준 PRACH RB 크기
        self.subcarriers_per_rb = 12  # 부반송파/RB
        self.symbols_per_slot = 14
        self.slots_per_frame = 10  # 15kHz SCS에서
        
        self.data = []
        
    def calculate_prach_occasions(self) -> pd.DataFrame:
        """PRACH Occasion 계산 (Time-Frequency 정보 포함)"""
        self.data = []
        
        occasion_id = 0
        
        for frame in range(self.num_frames):
            # 매 프레임의 slot 0에서 PRACH 발생
            slot_in_frame = 0  # PRACH Config 14는 slot 0
            
            # Subframe 계산
            subframe = frame % 10
            
            # PRACH는 symbol 0부터 시작
            symbol_start = 0
            
            # 주파수 영역: msg1_frequency_start부터 msg1_frequency_start + 6 RB
            rb_start = self.msg1_frequency_start
            rb_end = rb_start + self.rbs_per_prach - 1
            
            # Subcarrier 계산
            subcarrier_start = rb_start * self.subcarriers_per_rb
            subcarrier_end = rb_end * self.subcarriers_per_rb + (self.subcarriers_per_rb - 1)
            
            # 64개 프리앰블 각각에 대해 occasion 생성
            for preamble_idx in range(64):
                occasion = {
                    'occasion_id': occasion_id,
                    'frame': frame,
                    'subframe': subframe,
                    'slot': slot_in_frame,
                    'symbol': symbol_start,
                    'preamble_index': preamble_idx,
                    'rb_start': rb_start,
                    'rb_end': rb_end,
                    'rb_count': self.rbs_per_prach,
                    'subcarrier_start': subcarrier_start,
                    'subcarrier_end': subcarrier_end,
                    'subcarrier_count': (rb_end - rb_start + 1) * self.subcarriers_per_rb,
                    'frequency_khz': (rb_start * self.subcarriers_per_rb + subcarrier_start) * (self.scs / 1000),
                    'duration_symbols': self.prach_duration_symbols,
                }
                
                self.data.append(occasion)
                occasion_id += 1
        
        return pd.DataFrame(self.data)
    
    def get_time_frequency_summary(self) -> Dict[str, Any]:
        """Time-Frequency 요약 정보"""
        df = pd.DataFrame(self.data)
        
        unique_frames = df['frame'].nunique()
        unique_slots = df['slot'].nunique()
        unique_symbols = df['symbol'].nunique()
        unique_rbs = df['rb_start'].nunique()
        
        return {
            'total_occasions': len(df),
            'time_domain': {
                'frames': sorted(df['frame'].unique().tolist()),
                'frame_count': unique_frames,
                'slots': sorted(df['slot'].unique().tolist()),
                'slot_count': unique_slots,
                'symbols': sorted(df['symbol'].unique().tolist()),
                'symbol_count': unique_symbols,
                'occasions_per_frame': len(df) // unique_frames if unique_frames > 0 else 0,
            },
            'frequency_domain': {
                'rb_start': self.msg1_frequency_start,
                'rb_end': self.msg1_frequency_start + self.rbs_per_prach - 1,
                'rb_count': self.rbs_per_prach,
                'subcarrier_start': self.msg1_frequency_start * self.subcarriers_per_rb,
                'subcarrier_end': (self.msg1_frequency_start + self.rbs_per_prach - 1) * self.subcarriers_per_rb + 11,
                'subcarrier_count': self.rbs_per_prach * self.subcarriers_per_rb,
                'center_frequency_khz': (self.msg1_frequency_start * self.subcarriers_per_rb + 
                                        self.rbs_per_prach * self.subcarriers_per_rb / 2) * (self.scs / 1000),
            }
        }
    
    def create_time_frequency_table(self, output_path: str = None) -> pd.DataFrame:
        """Time-Frequency 상세 테이블 생성"""
        df = pd.DataFrame(self.data)
        
        # 주요 열만 선택
        summary_df = df[[
            'occasion_id', 'frame', 'subframe', 'slot', 'symbol',
            'preamble_index', 'rb_start', 'rb_end', 'rb_count',
            'subcarrier_start', 'subcarrier_end'
        ]].copy()
        
        # 라벨 추가
        summary_df['time_index'] = (summary_df['frame'] * self.slots_per_frame * self.symbols_per_slot + 
                                    summary_df['slot'] * self.symbols_per_slot + 
                                    summary_df['symbol'])
        summary_df['frequency_label'] = (summary_df['rb_start'].astype(str) + '-' + 
                                         summary_df['rb_end'].astype(str) + ' RB')
        
        if output_path:
            summary_df.to_csv(output_path, index=False)
            print(f"Time-Frequency table exported to {output_path}")
        
        return summary_df
    
    def plot_time_frequency_grid(self, output_path: str = None, max_frames: int = 50) -> plt.Figure:
        """
        Time-Frequency 2D 그리드 시각화
        X축: Frequency (RB), Y축: Time (Frame/Slot/Symbol)
        """
        df = pd.DataFrame(self.data)
        df = df[df['frame'] < max_frames]  # 처음 max_frames만 표시
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # 각 PRACH occasion을 사각형으로 표시
        unique_frames = sorted(df['frame'].unique())
        
        for idx, row in df.iterrows():
            # Y축: Time domain (Frame/Slot/Symbol)
            y_pos = row['frame'] * (self.slots_per_frame * self.symbols_per_slot) + \
                   row['slot'] * self.symbols_per_slot + \
                   row['symbol']
            
            # X축: Frequency domain (RB)
            x_pos = row['rb_start']
            
            # 색상: preamble index로 결정
            color_value = row['preamble_index'] / 64
            
            rect = Rectangle((x_pos, y_pos), 
                            self.rbs_per_prach, 1,
                            linewidth=0.5, 
                            edgecolor='black',
                            facecolor=plt.cm.viridis(color_value),
                            alpha=0.7)
            ax.add_patch(rect)
        
        # 축 설정
        ax.set_xlim(0, 150)  # RB 범위 (전형적인 FR1)
        ax.set_ylim(0, max_frames * self.slots_per_frame * self.symbols_per_slot)
        
        ax.set_xlabel('Frequency Domain (RB Index)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Time Domain (Frame×Slot×Symbol)', fontsize=12, fontweight='bold')
        ax.set_title(f'PRACH Time-Frequency Mapping (First {max_frames} Frames)\nConfig Index: {self.prach_config_index}', 
                    fontsize=14, fontweight='bold')
        
        # 그리드
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # PRACH RB 범위 강조
        ax.axvline(self.msg1_frequency_start, color='red', linestyle='--', linewidth=2, label='PRACH RB Start')
        ax.axvline(self.msg1_frequency_start + self.rbs_per_prach - 1, 
                  color='red', linestyle='--', linewidth=2, label='PRACH RB End')
        
        ax.legend(loc='upper right')
        
        if output_path:
            fig.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"Time-Frequency grid saved to {output_path}")
        
        return fig
    
    def plot_spectrum_allocation(self, output_path: str = None) -> plt.Figure:
        """주파수 스펙트럼 할당 시각화"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8))
        
        # 상단: 전체 대역폭
        total_rbs = 150  # 예시: 150 RB (20 MHz @ 15kHz SCS)
        rb_allocation = np.zeros(total_rbs)
        
        # PRACH RB 할당
        rb_allocation[self.msg1_frequency_start:self.msg1_frequency_start + self.rbs_per_prach] = 1
        
        ax1.bar(range(total_rbs), rb_allocation, color=['red' if x == 1 else 'lightgray' for x in rb_allocation],
               edgecolor='black', linewidth=0.5)
        ax1.set_ylabel('Allocation', fontsize=11, fontweight='bold')
        ax1.set_title('Frequency Domain: RB Allocation', fontsize=12, fontweight='bold')
        ax1.set_xlim(0, total_rbs)
        ax1.set_ylim(0, 1.2)
        ax1.grid(True, alpha=0.3, axis='y')
        
        # PRACH 범위 강조
        ax1.axvspan(self.msg1_frequency_start, 
                   self.msg1_frequency_start + self.rbs_per_prach,
                   alpha=0.2, color='red', label=f'PRACH RB {self.msg1_frequency_start}-{self.msg1_frequency_start + self.rbs_per_prach - 1}')
        ax1.legend()
        
        # 하단: PRACH RB 내 Subcarrier 할당
        subcarriers_in_prach = self.rbs_per_prach * self.subcarriers_per_rb
        subcarrier_allocation = np.ones(subcarriers_in_prach)
        
        ax2.bar(range(subcarriers_in_prach), subcarrier_allocation, 
               color='red', edgecolor='black', linewidth=0.5, alpha=0.7)
        ax2.set_xlabel('Subcarrier Index', fontsize=11, fontweight='bold')
        ax2.set_ylabel('Allocation', fontsize=11, fontweight='bold')
        ax2.set_title(f'Frequency Domain: Subcarrier Allocation in PRACH ({subcarriers_in_prach} subcarriers)', 
                     fontsize=12, fontweight='bold')
        ax2.set_ylim(0, 1.2)
        ax2.grid(True, alpha=0.3, axis='y')
        
        # RB 경계 표시
        for rb_idx in range(self.rbs_per_prach + 1):
            ax2.axvline(rb_idx * self.subcarriers_per_rb, color='blue', linestyle='--', alpha=0.5, linewidth=1)
        
        plt.tight_layout()
        
        if output_path:
            fig.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"Spectrum allocation saved to {output_path}")
        
        return fig
    
    def plot_time_distribution(self, output_path: str = None) -> plt.Figure:
        """시간 영역 분포 시각화"""
        df = pd.DataFrame(self.data)
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # 1. Frame별 PRACH occasion 수
        frame_counts = df.groupby('frame').size()
        axes[0, 0].bar(frame_counts.index, frame_counts.values, color='steelblue', edgecolor='black')
        axes[0, 0].set_xlabel('Frame Number', fontsize=10, fontweight='bold')
        axes[0, 0].set_ylabel('PRACH Occasions Count', fontsize=10, fontweight='bold')
        axes[0, 0].set_title('PRACH Occasions per Frame', fontsize=11, fontweight='bold')
        axes[0, 0].grid(True, alpha=0.3, axis='y')
        
        # 2. Slot별 분포
        slot_counts = df.groupby('slot').size()
        axes[0, 1].bar(slot_counts.index, slot_counts.values, color='darkgreen', edgecolor='black')
        axes[0, 1].set_xlabel('Slot Number', fontsize=10, fontweight='bold')
        axes[0, 1].set_ylabel('PRACH Occasions Count', fontsize=10, fontweight='bold')
        axes[0, 1].set_title('PRACH Occasions per Slot', fontsize=11, fontweight='bold')
        axes[0, 1].grid(True, alpha=0.3, axis='y')
        
        # 3. Symbol별 분포
        symbol_counts = df.groupby('symbol').size()
        axes[1, 0].bar(symbol_counts.index, symbol_counts.values, color='darkorange', edgecolor='black')
        axes[1, 0].set_xlabel('Symbol Number', fontsize=10, fontweight='bold')
        axes[1, 0].set_ylabel('PRACH Occasions Count', fontsize=10, fontweight='bold')
        axes[1, 0].set_title('PRACH Occasions per Symbol', fontsize=11, fontweight='bold')
        axes[1, 0].grid(True, alpha=0.3, axis='y')
        
        # 4. Preamble 분포
        preamble_counts = df.groupby('preamble_index').size()
        axes[1, 1].bar(preamble_counts.index, preamble_counts.values, color='purple', edgecolor='black', alpha=0.7)
        axes[1, 1].set_xlabel('Preamble Index', fontsize=10, fontweight='bold')
        axes[1, 1].set_ylabel('Occasions Count', fontsize=10, fontweight='bold')
        axes[1, 1].set_title('PRACH Preamble Distribution', fontsize=11, fontweight='bold')
        axes[1, 1].grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        if output_path:
            fig.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"Time distribution saved to {output_path}")
        
        return fig
    
    def generate_comprehensive_report(self, output_dir: str = 'analysis_results') -> None:
        """종합 분석 리포트 생성"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 데이터프레임 생성
        df = self.calculate_prach_occasions()
        
        # 1. CSV 데이터 저장
        csv_path = output_path / "time_frequency_mapping.csv"
        self.create_time_frequency_table(str(csv_path))
        
        # 2. Time-Frequency 그리드
        grid_path = output_path / "time_frequency_grid.png"
        self.plot_time_frequency_grid(str(grid_path), max_frames=50)
        
        # 3. 스펙트럼 할당
        spectrum_path = output_path / "spectrum_allocation.png"
        self.plot_spectrum_allocation(str(spectrum_path))
        
        # 4. 시간 분포
        time_path = output_path / "time_distribution.png"
        self.plot_time_distribution(str(time_path))
        
        # 5. 요약 리포트
        summary = self.get_time_frequency_summary()
        report_path = output_path / "time_frequency_report.txt"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("PRACH TIME-FREQUENCY MAPPING REPORT\n")
            f.write("="*70 + "\n\n")
            
            f.write("[PRACH CONFIGURATION]\n")
            f.write(f"Config Index: {self.prach_config_index}\n")
            f.write(f"msg1 Frequency Start: {self.msg1_frequency_start} RB\n")
            f.write(f"msg1 FDM: {self.msg1_fdm}\n")
            f.write(f"Analysis Period: {self.num_frames} frames\n\n")
            
            f.write("[TIME DOMAIN]\n")
            f.write(f"Total Frames: {summary['time_domain']['frame_count']}\n")
            f.write(f"Frame List: {summary['time_domain']['frames'][:10]}{'...' if len(summary['time_domain']['frames']) > 10 else ''}\n")
            f.write(f"Total Slots: {summary['time_domain']['slot_count']}\n")
            f.write(f"Slot Numbers: {summary['time_domain']['slots']}\n")
            f.write(f"Total Symbols: {summary['time_domain']['symbol_count']}\n")
            f.write(f"Symbol Numbers: {summary['time_domain']['symbols']}\n")
            f.write(f"Occasions per Frame: {summary['time_domain']['occasions_per_frame']}\n\n")
            
            f.write("[FREQUENCY DOMAIN]\n")
            f.write(f"RB Range: {summary['frequency_domain']['rb_start']}-{summary['frequency_domain']['rb_end']}\n")
            f.write(f"RB Count: {summary['frequency_domain']['rb_count']} RBs\n")
            f.write(f"Subcarrier Start: {summary['frequency_domain']['subcarrier_start']}\n")
            f.write(f"Subcarrier End: {summary['frequency_domain']['subcarrier_end']}\n")
            f.write(f"Total Subcarriers: {summary['frequency_domain']['subcarrier_count']}\n")
            f.write(f"Center Frequency: {summary['frequency_domain']['center_frequency_khz']:.2f} kHz\n")
            f.write(f"SCS: {self.scs} kHz\n\n")
            
            f.write("[SUMMARY]\n")
            f.write(f"Total PRACH Occasions: {summary['total_occasions']:,}\n")
            f.write(f"Total Preambles per Occasion: 64\n")
            f.write(f"Frequency Multiplexing: {self.msg1_fdm}×\n\n")
            
            f.write("[TIME-FREQUENCY STRUCTURE]\n")
            f.write(f"Time slots: Frame {summary['time_domain']['frames'][0]} to Frame {summary['time_domain']['frames'][-1]}\n")
            f.write(f"Slot: {summary['time_domain']['slots']}\n")
            f.write(f"Symbol: {summary['time_domain']['symbols']}\n")
            f.write(f"Frequency: RB {summary['frequency_domain']['rb_start']}-{summary['frequency_domain']['rb_end']}\n")
        
        print(f"\n✓ Time-Frequency mapping report generated: {report_path}")
        print(f"✓ Generated files:")
        print(f"  - {csv_path}")
        print(f"  - {grid_path}")
        print(f"  - {spectrum_path}")
        print(f"  - {time_path}")
        print(f"  - {report_path}")


if __name__ == '__main__':
    mapper = PRACHTimeFrequencyMapper(
        prach_config_index=14,
        msg1_frequency_start=7,
        msg1_fdm=1,
        num_frames=100,
        scs=15
    )
    
    # 데이터 계산
    df = mapper.calculate_prach_occasions()
    
    # 요약 정보
    summary = mapper.get_time_frequency_summary()
    print("\n" + "="*70)
    print("PRACH TIME-FREQUENCY SUMMARY")
    print("="*70)
    print(f"\n[TIME DOMAIN]")
    print(f"Frames: {len(summary['time_domain']['frames'])} unique frames")
    print(f"Slots: {summary['time_domain']['slots']}")
    print(f"Symbols: {summary['time_domain']['symbols']}")
    print(f"Occasions per Frame: {summary['time_domain']['occasions_per_frame']}")
    
    print(f"\n[FREQUENCY DOMAIN]")
    print(f"RB Range: {summary['frequency_domain']['rb_start']}-{summary['frequency_domain']['rb_end']} RB")
    print(f"Total RBs: {summary['frequency_domain']['rb_count']}")
    print(f"Subcarrier Range: {summary['frequency_domain']['subcarrier_start']}-{summary['frequency_domain']['subcarrier_end']}")
    print(f"Total Subcarriers: {summary['frequency_domain']['subcarrier_count']}")
    
    print(f"\n[STATISTICS]")
    print(f"Total PRACH Occasions: {summary['total_occasions']:,}")
    
    # 종합 리포트 생성
    mapper.generate_comprehensive_report('time_frequency_analysis')
