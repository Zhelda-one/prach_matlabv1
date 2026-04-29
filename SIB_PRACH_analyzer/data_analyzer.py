"""
PRACH 데이터 분석 모듈
Pandas를 사용한 상세 분석 및 비교
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import json


class PRACHDataAnalyzer:
    """PRACH 데이터 분석 클래스"""
    
    def __init__(self, dataframe: pd.DataFrame):
        """
        분석기 초기화
        
        Args:
            dataframe: PRACH occasion DataFrame
        """
        self.df = dataframe.copy()
        self.analysis_results = {}
        
    def analyze_frame_distribution(self) -> Dict[str, Any]:
        """프레임 분포 분석"""
        frame_group = self.df.groupby('frame').size()
        
        return {
            'total_frames': len(frame_group),
            'occasions_per_frame_mean': frame_group.mean(),
            'occasions_per_frame_std': frame_group.std(),
            'occasions_per_frame_min': frame_group.min(),
            'occasions_per_frame_max': frame_group.max(),
            'frame_distribution': frame_group.to_dict(),
        }
    
    def analyze_slot_distribution(self) -> Dict[str, Any]:
        """슬롯 분포 분석"""
        slot_group = self.df.groupby('slot').size()
        
        return {
            'total_slots': len(slot_group),
            'occasions_per_slot': slot_group.to_dict(),
            'most_common_slot': slot_group.idxmax(),
            'most_common_slot_count': slot_group.max(),
            'slot_statistics': {
                'mean': slot_group.mean(),
                'std': slot_group.std(),
                'min': slot_group.min(),
                'max': slot_group.max(),
            }
        }
    
    def analyze_symbol_distribution(self) -> Dict[str, Any]:
        """심볼 분포 분석"""
        symbol_group = self.df.groupby('symbol').size()
        
        return {
            'total_symbols': len(symbol_group),
            'occasions_per_symbol': symbol_group.to_dict(),
            'most_common_symbol': symbol_group.idxmax(),
            'most_common_symbol_count': symbol_group.max(),
            'symbol_statistics': {
                'mean': symbol_group.mean(),
                'std': symbol_group.std(),
                'min': symbol_group.min(),
                'max': symbol_group.max(),
            }
        }
    
    def analyze_subframe_distribution(self) -> Dict[str, Any]:
        """서브프레임 분포 분석"""
        subframe_group = self.df.groupby('subframe').size()
        
        return {
            'total_subframes': len(subframe_group),
            'occasions_per_subframe': subframe_group.to_dict(),
            'subframe_statistics': {
                'mean': subframe_group.mean(),
                'std': subframe_group.std(),
                'min': subframe_group.min(),
                'max': subframe_group.max(),
            }
        }
    
    def analyze_preamble_distribution(self) -> Dict[str, Any]:
        """프리앰블 인덱스 분포 분석"""
        preamble_group = self.df.groupby('preamble_index').size()
        
        return {
            'total_preambles': len(preamble_group),
            'occasions_per_preamble': preamble_group.to_dict(),
            'preamble_statistics': {
                'mean': preamble_group.mean(),
                'std': preamble_group.std(),
                'min': preamble_group.min(),
                'max': preamble_group.max(),
            }
        }
    
    def analyze_frequency_distribution(self) -> Dict[str, Any]:
        """주파수 분포 분석"""
        freq_group = self.df.groupby('frequency_offset_rb').size()
        
        return {
            'total_frequency_offsets': len(freq_group),
            'occasions_per_frequency': freq_group.to_dict(),
            'frequency_offsets': sorted(self.df['frequency_offset_rb'].unique().tolist()),
        }
    
    def find_high_density_slots(self, threshold_percentile: int = 75) -> pd.DataFrame:
        """높은 밀도의 PRACH occasion이 있는 슬롯 찾기"""
        slot_counts = self.df.groupby('slot').size()
        threshold = slot_counts.quantile(threshold_percentile / 100)
        
        high_density_slots = slot_counts[slot_counts >= threshold].index.tolist()
        
        return {
            'threshold': float(threshold),
            'high_density_slots': high_density_slots,
            'slot_counts': slot_counts[high_density_slots].to_dict(),
            'total_high_density_occasions': len(self.df[self.df['slot'].isin(high_density_slots)])
        }
    
    def find_collision_patterns(self) -> Dict[str, Any]:
        """충돌 패턴 찾기 (같은 슬롯, 심볼에서 여러 프리앰블)"""
        collision_key = ['slot', 'symbol']
        collision_groups = self.df.groupby(collision_key).size()
        collisions = collision_groups[collision_groups > 1]
        
        collision_details = []
        for (slot, symbol), count in collisions.items():
            collision_details.append({
                'slot': slot,
                'symbol': symbol,
                'preamble_count': count,
                'frames': self.df[(self.df['slot'] == slot) & (self.df['symbol'] == symbol)]['frame'].unique().tolist(),
            })
        
        return {
            'total_collision_patterns': len(collisions),
            'collision_details': collision_details,
            'most_collided_slot_symbol': collision_groups.idxmax() if len(collisions) > 0 else None,
            'max_collision_count': collision_groups.max() if len(collisions) > 0 else 0,
        }
    
    def get_gap_analysis(self) -> Dict[str, Any]:
        """PRACH occasion 간 갭 분석"""
        df_sorted = self.df.sort_values('absolute_symbol').reset_index(drop=True)
        gaps = df_sorted['absolute_symbol'].diff().dropna()
        
        return {
            'total_gaps': len(gaps),
            'gap_statistics': {
                'mean': gaps.mean(),
                'std': gaps.std(),
                'min': gaps.min(),
                'max': gaps.max(),
                'median': gaps.median(),
            },
            'gap_distribution': gaps.value_counts().head(10).to_dict(),
        }
    
    def compare_with_another(self, other_df: pd.DataFrame) -> Dict[str, Any]:
        """다른 PRACH 설정과 비교"""
        diff = {
            'same_occasions_count': len(pd.merge(self.df, other_df, 
                                                   on=['frame', 'subframe', 'slot', 'symbol'],
                                                   how='inner')),
            'unique_to_self': len(pd.merge(self.df, other_df,
                                           on=['frame', 'subframe', 'slot', 'symbol'],
                                           how='left_only')),
            'unique_to_other': len(pd.merge(self.df, other_df,
                                            on=['frame', 'subframe', 'slot', 'symbol'],
                                            how='right_only')),
            'self_total': len(self.df),
            'other_total': len(other_df),
        }
        
        return diff
    
    def generate_full_report(self) -> Dict[str, Any]:
        """전체 분석 리포트 생성"""
        return {
            'overview': {
                'total_occasions': len(self.df),
                'total_frames': self.df['frame'].max() - self.df['frame'].min() + 1,
                'frame_range': (int(self.df['frame'].min()), int(self.df['frame'].max())),
            },
            'frame_analysis': self.analyze_frame_distribution(),
            'slot_analysis': self.analyze_slot_distribution(),
            'symbol_analysis': self.analyze_symbol_distribution(),
            'subframe_analysis': self.analyze_subframe_distribution(),
            'preamble_analysis': self.analyze_preamble_distribution(),
            'frequency_analysis': self.analyze_frequency_distribution(),
            'gap_analysis': self.get_gap_analysis(),
            'collision_analysis': self.find_collision_patterns(),
            'high_density_slots': self.find_high_density_slots(),
        }
    
    def export_to_csv(self, output_path: str) -> None:
        """CSV로 내보내기"""
        self.df.to_csv(output_path, index=False)
        print(f"Exported to {output_path}")
    
    def export_to_json(self, output_path: str) -> None:
        """JSON으로 내보내기"""
        self.df_json = self.df.to_dict(orient='records')
        with open(output_path, 'w') as f:
            json.dump(self.df_json, f, indent=2)
        print(f"Exported to {output_path}")
    
    def export_analysis_report(self, output_path: str) -> None:
        """분석 리포트를 JSON으로 내보내기"""
        report = self.generate_full_report()
        
        # Convert non-serializable objects
        def convert_to_serializable(obj):
            if isinstance(obj, (np.integer, np.floating)):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_to_serializable(item) for item in obj]
            return obj
        
        report = convert_to_serializable(report)
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Analysis report exported to {output_path}")
    
    def get_summary_stats(self) -> pd.DataFrame:
        """요약 통계"""
        summary_data = {
            'Metric': [
                'Total PRACH Occasions',
                'Frame Range',
                'Unique Slots',
                'Unique Symbols',
                'Unique Preambles',
                'Occasions/Frame (avg)',
                'Slot with Max Occasions',
                'Symbol with Max Occasions',
            ],
            'Value': [
                len(self.df),
                f"{self.df['frame'].min()}-{self.df['frame'].max()}",
                self.df['slot'].nunique(),
                self.df['symbol'].nunique(),
                self.df['preamble_index'].nunique(),
                f"{len(self.df) / (self.df['frame'].max() - self.df['frame'].min() + 1):.2f}",
                f"{self.analyze_slot_distribution()['most_common_slot']} ({self.analyze_slot_distribution()['most_common_slot_count']} occasions)",
                f"{self.analyze_symbol_distribution()['most_common_symbol']} ({self.analyze_symbol_distribution()['most_common_symbol_count']} occasions)",
            ]
        }
        
        return pd.DataFrame(summary_data)


if __name__ == '__main__':
    # 테스트를 위해 더미 데이터 생성
    dummy_data = {
        'occasion_id': range(100),
        'frame': [i // 10 for i in range(100)],
        'subframe': [i % 10 for i in range(100)],
        'slot': [i % 10 for i in range(100)],
        'symbol': [0] * 100,
        'preamble_index': [i % 64 for i in range(100)],
        'prach_config_index': [14] * 100,
        'frequency_offset_rb': [7] * 100,
        'duration_symbols': [1] * 100,
        'absolute_slot': [i for i in range(100)],
        'absolute_symbol': [i * 14 for i in range(100)],
        'frequency_khz': [7 * 12 * 15 / 1000] * 100,
    }
    
    df = pd.DataFrame(dummy_data)
    analyzer = PRACHDataAnalyzer(df)
    
    print("Summary Statistics:")
    print(analyzer.get_summary_stats().to_string(index=False))
