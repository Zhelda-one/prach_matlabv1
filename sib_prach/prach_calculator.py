"""
PRACH Occasion 계산 모듈
3GPP TS 38.104 표준 기반으로 PRACH 프리앰블이 발생하는 Frame/Subframe/Slot/Symbol을 계산합니다.
"""

from typing import List, Dict, Any, Tuple
from enum import Enum
import pandas as pd


class SubcarrierSpacing(Enum):
    """부반송파 간격 (kHz)"""
    KHZ_15 = 15
    KHZ_30 = 30
    KHZ_60 = 60
    KHZ_120 = 120
    KHZ_240 = 240


class PRACHCalculator:
    """PRACH Occasion 계산 클래스"""
    
    # 3GPP 38.104 Table 6.3.2-3: PRACH Configuration Indices for FR1 (Unpaired spectrum)
    # Format: (periodicity_slots, slot_offset, symbol, duration)
    PRACH_CONFIG_TABLE_FR1_15KHZ = {
        0: [(14, 0, 0, 1), (14, 7, 0, 1)],
        1: [(14, 0, 0, 1)],
        2: [(14, 0, 0, 1)],
        3: [(14, 0, 0, 1), (14, 7, 0, 1)],
        4: [(14, 0, 0, 1)],
        5: [(14, 0, 0, 1)],
        6: [(14, 0, 0, 1), (14, 7, 0, 1)],
        7: [(14, 0, 0, 1), (14, 7, 0, 1)],
        8: [(14, 0, 0, 1)],
        9: [(14, 0, 0, 1)],
        10: [(14, 0, 0, 1)],
        11: [(14, 0, 0, 1)],
        12: [(14, 0, 0, 1), (14, 7, 0, 1)],
        13: [(14, 0, 0, 1)],
        14: [(14, 0, 0, 1)],
        15: [(14, 0, 0, 1)],
        16: [(14, 0, 0, 1), (14, 7, 0, 1)],
        17: [(14, 0, 0, 1), (14, 7, 0, 1)],
        18: [(14, 0, 0, 1)],
        19: [(14, 0, 0, 1)],
        20: [(14, 0, 0, 1)],
        21: [(14, 0, 0, 1), (14, 7, 0, 1)],
        22: [(14, 0, 0, 1), (14, 7, 0, 1)],
        23: [(14, 0, 0, 1)],
        24: [(14, 0, 0, 1)],
        25: [(14, 0, 0, 1)],
        26: [(14, 0, 0, 1), (14, 7, 0, 1)],
        27: [(14, 0, 0, 1), (14, 7, 0, 1)],
        28: [(14, 0, 0, 1)],
        29: [(14, 0, 0, 1)],
        30: [(14, 0, 0, 1)],
        31: [(14, 0, 0, 1), (14, 7, 0, 1)],
        32: [(14, 0, 0, 1), (14, 7, 0, 1)],
        33: [(14, 0, 0, 1)],
        34: [(14, 0, 0, 1)],
        35: [(14, 0, 0, 1)],
        36: [(14, 0, 0, 1), (14, 7, 0, 1)],
        37: [(14, 0, 0, 1), (14, 7, 0, 1)],
        38: [(14, 0, 0, 1)],
        39: [(14, 0, 0, 1)],
        40: [(14, 0, 0, 1)],
        41: [(14, 0, 0, 1), (14, 7, 0, 1)],
        42: [(14, 0, 0, 1), (14, 7, 0, 1)],
        43: [(14, 0, 0, 1)],
        44: [(14, 0, 0, 1)],
        45: [(14, 0, 0, 1)],
        46: [(14, 0, 0, 1), (14, 7, 0, 1)],
        47: [(14, 0, 0, 1), (14, 7, 0, 1)],
        48: [(14, 0, 0, 1)],
        49: [(14, 0, 0, 1)],
        50: [(14, 0, 0, 1)],
        51: [(14, 0, 0, 1), (14, 7, 0, 1)],
        52: [(14, 0, 0, 1), (14, 7, 0, 1)],
        53: [(14, 0, 0, 1)],
        54: [(14, 0, 0, 1)],
        55: [(14, 0, 0, 1)],
        56: [(14, 0, 0, 1), (14, 7, 0, 1)],
        57: [(14, 0, 0, 1), (14, 7, 0, 1)],
        58: [(14, 0, 0, 1)],
        59: [(14, 0, 0, 1)],
        60: [(14, 0, 0, 1)],
        61: [(14, 0, 0, 1), (14, 7, 0, 1)],
        62: [(14, 0, 0, 1), (14, 7, 0, 1)],
        63: [(14, 0, 0, 1)],
    }
    
    def __init__(self, 
                 prach_config_index: int,
                 msg1_fdm: int,
                 msg1_frequency_start: int,
                 scs: SubcarrierSpacing = SubcarrierSpacing.KHZ_15,
                 zero_correlation_zone_config: int = 0):
        """
        PRACH 계산기 초기화
        
        Args:
            prach_config_index: PRACH Configuration Index (0-63)
            msg1_fdm: msg1 FDM (1, 2, 4, or 8)
            msg1_frequency_start: msg1 Frequency Start (RB 단위)
            scs: 부반송파 간격 (기본: 15 kHz)
            zero_correlation_zone_config: Zero Correlation Zone Config (0-15)
        """
        self.prach_config_index = prach_config_index
        self.msg1_fdm = msg1_fdm
        self.msg1_frequency_start = msg1_frequency_start
        self.scs = scs
        self.zero_correlation_zone_config = zero_correlation_zone_config
        
        # PRACH 프리앰블 시퀀스 길이 (샘플)
        self.prach_preamble_length = 839  # Long sequence (L839)
        
        # 슬롯/심볼 설정 (15kHz SCS 기준: 10 slots/frame, 14 symbols/slot)
        self.slots_per_frame = 10
        self.symbols_per_slot = 14
        
    def get_prach_occasions_fr1(self, 
                                 num_frames: int = 1000,
                                 start_frame: int = 0) -> List[Dict[str, Any]]:
        """
        FR1 (Sub 6GHz)에서 PRACH Occasion 계산
        
        Args:
            num_frames: 계산할 프레임 수 (기본: 1000)
            start_frame: 시작 프레임 (기본: 0)
            
        Returns:
            PRACH occasion 정보 리스트
        """
        occasions = []
        occasion_id = 0
        
        if self.prach_config_index not in self.PRACH_CONFIG_TABLE_FR1_15KHZ:
            raise ValueError(f"Invalid PRACH Configuration Index: {self.prach_config_index}")
        
        config_entries = self.PRACH_CONFIG_TABLE_FR1_15KHZ[self.prach_config_index]
        
        for frame_idx in range(num_frames):
            frame = start_frame + frame_idx

            for periodicity_slots, slot_offset, symbol, duration in config_entries:
                for slot_in_frame in range(self.slots_per_frame):
                    absolute_slot = frame * self.slots_per_frame + slot_in_frame
                    if (absolute_slot - slot_offset) % periodicity_slots != 0:
                        continue

                    slot = slot_in_frame
                    subframe = slot_in_frame

                    for preamble_idx in range(64):  # 64개의 프리앰블
                        occasion = {
                            'occasion_id': occasion_id,
                            'frame': frame,
                            'subframe': subframe,
                            'slot': slot,
                            'symbol': symbol,
                            'preamble_index': preamble_idx,
                            'prach_config_index': self.prach_config_index,
                            'frequency_offset_rb': self.msg1_frequency_start,
                            'duration_symbols': duration,
                        }
                        occasions.append(occasion)
                        occasion_id += 1
        
        return occasions
    
    def calculate_prach_timing(self, num_frames: int = 1000) -> pd.DataFrame:
        """
        PRACH 타이밍 정보를 DataFrame으로 반환
        
        Args:
            num_frames: 계산할 프레임 수
            
        Returns:
            PRACH 타이밍 정보 DataFrame
        """
        occasions = self.get_prach_occasions_fr1(num_frames=num_frames)
        df = pd.DataFrame(occasions)
        
        # 추가 정보 계산
        df['absolute_slot'] = df['frame'] * self.slots_per_frame + df['slot']
        df['absolute_symbol'] = df['absolute_slot'] * self.symbols_per_slot + df['symbol']
        df['frequency_khz'] = (df['frequency_offset_rb'] * 12 * self.scs.value) / 1000
        
        return df
    
    def get_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """PRACH 통계 정보 계산"""
        return {
            'total_occasions': len(df),
            'occasions_per_frame': len(df) / (df['frame'].max() + 1),
            'unique_frames': df['frame'].nunique(),
            'unique_slots': df['slot'].nunique(),
            'unique_symbols': df['symbol'].nunique(),
            'frame_range': (df['frame'].min(), df['frame'].max()),
            'slot_distribution': df['slot'].value_counts().to_dict(),
            'symbol_distribution': df['symbol'].value_counts().to_dict(),
        }


if __name__ == '__main__':
    # 테스트
    calculator = PRACHCalculator(
        prach_config_index=14,
        msg1_fdm=1,
        msg1_frequency_start=7,
        zero_correlation_zone_config=9
    )
    
    df = calculator.calculate_prach_timing(num_frames=100)
    stats = calculator.get_statistics(df)
    
    print("=" * 60)
    print("PRACH Occasion Statistics")
    print("=" * 60)
    for key, value in stats.items():
        print(f"{key:30s}: {value}")
    
    print("\n" + "=" * 60)
    print("First 10 PRACH Occasions")
    print("=" * 60)
    print(df.head(10).to_string(index=False))
