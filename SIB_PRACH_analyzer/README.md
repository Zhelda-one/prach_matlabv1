# PRACH Analyzer - Advanced 5G NR PRACH Occasion Analysis Tool

> **통합 안내 (2026-04):** 상위 폴더에서 **`streamlit run app.py`** 한 번으로 MATLAB PRACH 생성과 SIB1 occasion 분석을 함께 쓸 수 있습니다. Python 모듈은 `../sib_prach/` 패키지로 이전되었습니다. 이 폴더의 `web_dashboard.py`(Flask)는 더 이상 단일 진입점이 아닙니다.

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 개요

PRACH Analyzer는 5G NR 시스템 정보 블록(SIB1) 로그를 분석하여 **PRACH(Physical Random Access Channel)** 프리앰블이 발생하는 Frame, Subframe, Slot, Symbol을 자동으로 계산하고 시각화하는 고급 분석 도구입니다.

### 주요 기능

✅ **SIB1 파일 자동 파싱**
- 텍스트 형식의 SIB1 로그 파일 자동 인식
- PRACH 설정 파라미터 자동 추출
- 타이밍 정보 자동 추출

✅ **PRACH Occasion 계산**
- 3GPP TS 38.104 표준 기반 계산
- Fr1 (Sub 6GHz) 대역 지원
- 1000+ 프레임 범위 분석 가능

✅ **상세 데이터 분석**
- Frame/Subframe/Slot/Symbol 분포 분석
- 프리앰블 인덱스 분포 분석
- 충돌 패턴 감지
- 갭 분석
- 주파수 오프셋 분석

✅ **다양한 시각화**
- 프레임별 분포도
- 슬롯별 분포도
- 심볼별 분포도
- Slot-Symbol 히트맵
- 시간 영역 누적 분포
- 프리앰블 분포도
- 갭 분석 히스토그램

✅ **다중 출력 형식**
- CSV 형식 데이터 내보내기
- JSON 형식 상세 리포트
- 이미지 시각화 (PNG)
- HTML 웹 리포트

✅ **웹 대시보드**
- 실시간 분석 인터페이스
- 대화형 차트
- 파일 업로드 및 분석
- 결과 다운로드

## 설치

### 요구사항
- Python 3.8 이상
- pip

### 설치 단계

```bash
# 1. 저장소 클론 또는 파일 다운로드
cd SIB_PRACH_analyzer

# 2. 가상환경 생성 (권장)
python -m venv .venv
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 3. 의존성 설치
pip install -r requirements.txt
```

## 사용법

### 1. CLI 명령어 분석 (가장 간단)

```bash
python prach_analyzer.py
```

**또는** Python 코드에서:

```python
from prach_analyzer import PRACHAnalyzer

# 분석기 생성
analyzer = PRACHAnalyzer('SIB1.txt', output_dir='analysis_results')

# 전체 분석 실행 (1000 프레임)
analyzer.run_full_analysis(num_frames=1000)
```

### 2. 웹 대시보드 실행

```bash
python web_dashboard.py
```

브라우저에서 `http://127.0.0.1:5000` 접속

### 3. MATLAB 예제 스타일 실행

`NewRadioPRACHConfigurationExample.m` 흐름과 유사하게,
지원 SCS 조합 표 -> 포맷 기반 설정 인덱스 선택 -> 활성 슬롯 판별 ->
리소스 그리드 매핑 -> 파형 타이밍 정보(근사) 순서로 실행합니다.

```bash
python prach_matlab_style_example.py
```

결과는 `matlab_style_results/` 폴더에 저장됩니다.

### 4. 단계별 분석

```python
from prach_analyzer import PRACHAnalyzer

analyzer = PRACHAnalyzer('SIB1.txt', output_dir='analysis_results')

# Step 1: SIB1 파싱
analyzer.step1_parse_sib1()

# Step 2: PRACH Occasion 계산
df = analyzer.step2_calculate_prach_occasions(num_frames=1000)

# Step 3: 데이터 분석
report = analyzer.step3_analyze_data()

# Step 4: 시각화
analyzer.step4_visualize_results()

# Step 5: 결과 내보내기
analyzer.step5_export_results(report)
```

### 5. 고급 API 사용

```python
from sib1_parser import SIB1Parser
from prach_calculator import PRACHCalculator, SubcarrierSpacing
from data_analyzer import PRACHDataAnalyzer
from visualizer import PRACHVisualizer

# SIB1 파싱
parser = SIB1Parser('SIB1.txt')
data = parser.parse()
prach_config = data['prach_config']

# PRACH 계산
calculator = PRACHCalculator(
    prach_config_index=14,
    msg1_fdm=1,
    msg1_frequency_start=7,
    scs=SubcarrierSpacing.KHZ_15,
    zero_correlation_zone_config=9
)

df = calculator.calculate_prach_timing(num_frames=1000)

# 데이터 분석
analyzer = PRACHDataAnalyzer(df)
report = analyzer.generate_full_report()

# 시각화
visualizer = PRACHVisualizer(df)
fig = visualizer.plot_comprehensive_dashboard(output_path='dashboard.png')
```

## 출력 결과

분석 완료 후 `analysis_results/` 디렉토리에 다음 파일들이 생성됩니다:

```
analysis_results/
├── prach_occasions.csv              # PRACH occasion 데이터 (CSV)
├── prach_occasions.json             # PRACH occasion 데이터 (JSON)
├── analysis_report.json             # 상세 분석 리포트
├── analysis_report.html             # 웹 리포트
├── summary_statistics.txt           # 요약 통계 텍스트
├── comprehensive_dashboard.png      # 종합 시각화 이미지
└── individual_plots/                # 개별 차트 이미지
    ├── frame_distribution.png
    ├── slot_distribution.png
    ├── symbol_distribution.png
    ├── slot_symbol_heatmap.png
    ├── temporal_distribution.png
    ├── preamble_distribution.png
    ├── gap_analysis.png
    └── frequency_distribution.png
```

## 분석 리포트 예시

### CSV 형식 (prach_occasions.csv)
```
occasion_id,frame,subframe,slot,symbol,preamble_index,...
0,0,0,0,0,0,...
1,0,0,0,0,1,...
2,0,0,0,0,2,...
...
```

### 분석 통계 (analysis_report.json)
```json
{
  "overview": {
    "total_occasions": 64000,
    "frame_range": [0, 999],
    "total_frames": 1000
  },
  "frame_analysis": {
    "total_frames": 1000,
    "occasions_per_frame_mean": 64.0,
    "occasions_per_frame_std": 0.0,
    ...
  },
  "collision_analysis": {
    "total_collision_patterns": 0,
    "max_collision_count": 0,
    ...
  },
  ...
}
```

## SIB1 파일 형식

지원하는 SIB1 파일 형식:

```
Chipset timestamp: 2026-04-09 09:07:13.150143, CFN : 254
Dual Mode Index : 0
...
Slot_n : 0x0000(0)
sub_fn : 0x0005(5)
sfn    : 0x01D0(464)
...
rach_ConfigCommon
   setup
      rach_ConfigGeneric
         prach_ConfigurationIndex = 14
         msg1_FDM = one
         msg1_FrequencyStart = 7
         zeroCorrelationZoneConfig = 9
         ...
```

## 지원하는 PRACH 파라미터

| 파라미터 | 범위 | 설명 |
|---------|------|------|
| PRACH Config Index | 0-63 | PRACH 설정 인덱스 (3GPP 38.104) |
| msg1 FDM | 1, 2, 4, 8 | msg1 FDM 멀티플렉싱 팩터 |
| msg1 Frequency Start | 0-274 | RB 단위의 시작 위치 |
| Zero Correlation Zone | 0-15 | PRACH 루트 시퀀스 ZCZ 설정 |
| Preamble Trans Max | 3-200 | 프리앰블 재전송 최대 횟수 |
| RA Response Window | 1-160 slots | RA 응답 대기 윈도우 |
| Power Ramping Step | 2-8 dB | 전력 램핑 단계 |

## 기술 사양

### PRACH Calculation
- **표준**: 3GPP TS 38.104 V17.2.0 (Release 17)
- **대역**: FR1 (Sub 6GHz)
- **부반송파 간격**: 15 kHz (Primary)
- **최대 분석 범위**: 10240 프레임 (≈102.4 초)

### 분석 능력
- **총 PRACH Occasion**: 수백만 개 분석 가능
- **처리 시간**: 1000 프레임 기준 < 10초
- **메모리 효율**: 최적화된 메모리 사용

## 예제

### 예제 1: 기본 분석

```python
from prach_analyzer import PRACHAnalyzer

analyzer = PRACHAnalyzer('SIB1.txt')
analyzer.run_full_analysis(num_frames=500)
```

### 예제 2: 커스텀 분석

```python
from sib1_parser import SIB1Parser
from prach_calculator import PRACHCalculator
from data_analyzer import PRACHDataAnalyzer
import pandas as pd

# 파싱
parser = SIB1Parser('SIB1.txt')
prach_config = parser.parse()['prach_config']

# 계산
calc = PRACHCalculator(
    prach_config_index=prach_config['prach_configuration_index'],
    msg1_fdm=prach_config['msg1_fdm_value'],
    msg1_frequency_start=prach_config['msg1_frequency_start']
)
df = calc.calculate_prach_timing(num_frames=1000)

# 분석
analyzer = PRACHDataAnalyzer(df)
stats = analyzer.analyze_slot_distribution()

print(f"Most common slot: {stats['most_common_slot']}")
print(f"Slot distribution: {stats['occasions_per_slot']}")
```

### 예제 3: 비교 분석

```python
# 2개의 SIB1 파일 비교
analyzer1 = PRACHAnalyzer('SIB1_config1.txt')
df1 = analyzer1.step2_calculate_prach_occasions(1000)

analyzer2 = PRACHAnalyzer('SIB1_config2.txt')
df2 = analyzer2.step2_calculate_prach_occasions(1000)

# 비교
data_analyzer = PRACHDataAnalyzer(df1)
comparison = data_analyzer.compare_with_another(df2)

print(f"Common occasions: {comparison['same_occasions_count']}")
print(f"Unique to config1: {comparison['unique_to_self']}")
print(f"Unique to config2: {comparison['unique_to_other']}")
```

## 문제 해결

### 1. SIB1 파일 인식 안 됨
- **원인**: 파일 형식이 지원되지 않는 형식
- **해결**: 표준 텍스트 형식의 SIB1 로그 사용

### 2. PRACH Configuration Index가 없음
- **원인**: SIB1 파일에 RACH 설정이 포함되지 않음
- **해결**: 완전한 SIB1 메시지가 포함된 파일 사용

### 3. 메모리 부족
- **원인**: 너무 많은 프레임 분석 (>10000 프레임)
- **해결**: `num_frames` 파라미터를 줄여서 실행

### 4. 차트가 렌더링 안 됨
- **원인**: matplotlib 백엔드 문제
- **해결**: `MPLBACKEND=Agg python prach_analyzer.py` 사용

## 성능 벤치마크

| 작업 | 1000 프레임 | 5000 프레임 | 10000 프레임 |
|------|-----------|-----------|------------|
| SIB1 파싱 | < 1초 | < 1초 | < 1초 |
| PRACH 계산 | ~2초 | ~10초 | ~20초 |
| 데이터 분석 | ~1초 | ~5초 | ~10초 |
| 시각화 | ~3초 | ~5초 | ~8초 |
| **총 시간** | **~7초** | **~21초** | **~39초** |

## 라이센스

MIT License - 자유롭게 사용, 수정, 배포 가능

## 기여

버그 리포트 및 기능 제안은 환영합니다!

## 참고 자료

- [3GPP TS 38.104 - Physical layer: General description](https://www.3gpp.org/)
- [5G NR PRACH Specifications](https://www.3gpp.org/)
- [Pandas Documentation](https://pandas.pydata.org/)
- [Matplotlib Documentation](https://matplotlib.org/)

## 버전 히스토리

### v1.0.0 (2026-04-20)
- ✅ 초기 릴리스
- ✅ SIB1 파싱
- ✅ PRACH Occasion 계산
- ✅ 데이터 분석
- ✅ 시각화
- ✅ 웹 대시보드

## 연락처

문제 발생 시 또는 피드백이 있으시면 연락주세요.

---

**Happy PRACH Analyzing!** 🚀
