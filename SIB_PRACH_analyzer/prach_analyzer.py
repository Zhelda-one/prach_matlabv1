"""
PRACH 분석 메인 엔진
모든 모듈을 통합하여 완전한 분석 파이프라인을 제공합니다.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any
import pandas as pd
import json
from datetime import datetime

from sib1_parser import SIB1Parser
from prach_calculator import PRACHCalculator, SubcarrierSpacing
from data_analyzer import PRACHDataAnalyzer
from visualizer import PRACHVisualizer


class PRACHAnalyzer:
    """PRACH 분석 통합 클래스"""
    
    def __init__(self, sib1_file: str, output_dir: str = 'analysis_results'):
        """
        분석기 초기화
        
        Args:
            sib1_file: SIB1 로그 파일 경로
            output_dir: 출력 디렉토리
        """
        self.sib1_file = sib1_file
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.parser = None
        self.prach_config = None
        self.calculator = None
        self.df = None
        self.analyzer = None
        self.visualizer = None
        
    def step1_parse_sib1(self) -> Dict[str, Any]:
        """Step 1: SIB1 파일 파싱"""
        print("\n" + "="*60)
        print("STEP 1: Parsing SIB1 File")
        print("="*60)
        
        self.parser = SIB1Parser(self.sib1_file)
        data = self.parser.parse()
        
        print(f"✓ SIB1 파일 파싱 완료: {self.sib1_file}")
        print(f"  - RRC Release: {data['basic_info'].get('rrc_release', 'N/A')}")
        print(f"  - Physical Cell ID: {data['cell_info'].get('physical_cell_id', 'N/A')}")
        print(f"  - Timing: Frame={data['timing_info'].get('sfn')}, Slot={data['timing_info'].get('slot_n')}, SubFrame={data['timing_info'].get('sub_fn')}")
        
        self.prach_config = data['prach_config']
        
        # PRACH 설정 출력
        print(f"\n[PRACH Configuration]")
        print(f"  - PRACH Config Index: {self.prach_config.get('prach_configuration_index')}")
        print(f"  - msg1 FDM: {self.prach_config.get('msg1_fdm')} ({self.prach_config.get('msg1_fdm_value')} multiplexing)")
        print(f"  - msg1 Frequency Start: {self.prach_config.get('msg1_frequency_start')} RB")
        print(f"  - Zero Correlation Zone: {self.prach_config.get('zero_correlation_zone_config')}")
        print(f"  - Preamble Transmission Max: {self.prach_config.get('preamble_trans_max')} ({self.prach_config.get('preamble_trans_max_value')} retries)")
        print(f"  - RA Response Window: {self.prach_config.get('ra_response_window')} ({self.prach_config.get('ra_response_window_slots')} slots)")
        print(f"  - Power Ramping Step: {self.prach_config.get('power_ramping_step')} ({self.prach_config.get('power_ramping_step_db')} dB)")
        print(f"  - Preamble Target Power: {self.prach_config.get('preamble_received_target_power')} dBm")
        
        return data
    
    def step2_calculate_prach_occasions(self, num_frames: int = 1000) -> pd.DataFrame:
        """Step 2: PRACH Occasion 계산"""
        print("\n" + "="*60)
        print(f"STEP 2: Calculating PRACH Occasions ({num_frames} frames)")
        print("="*60)
        
        self.calculator = PRACHCalculator(
            prach_config_index=self.prach_config['prach_configuration_index'],
            msg1_fdm=self.prach_config['msg1_fdm_value'],
            msg1_frequency_start=self.prach_config['msg1_frequency_start'],
            scs=SubcarrierSpacing.KHZ_15,
            zero_correlation_zone_config=self.prach_config['zero_correlation_zone_config'],
        )
        
        self.df = self.calculator.calculate_prach_timing(num_frames=num_frames)
        
        print(f"✓ PRACH Occasion 계산 완료")
        print(f"  - Total Occasions: {len(self.df):,}")
        print(f"  - Frame Range: {self.df['frame'].min():.0f} - {self.df['frame'].max():.0f}")
        print(f"  - Occasions per Frame: {len(self.df) / (self.df['frame'].max() - self.df['frame'].min() + 1):.2f}")
        
        return self.df
    
    def step3_analyze_data(self) -> Dict[str, Any]:
        """Step 3: 데이터 분석"""
        print("\n" + "="*60)
        print("STEP 3: Analyzing PRACH Data")
        print("="*60)
        
        self.analyzer = PRACHDataAnalyzer(self.df)
        report = self.analyzer.generate_full_report()
        
        print("✓ 데이터 분석 완료")
        print(f"\n[Frame Analysis]")
        print(f"  - Total Frames: {report['frame_analysis']['total_frames']}")
        print(f"  - Occasions/Frame Mean: {report['frame_analysis']['occasions_per_frame_mean']:.2f}")
        print(f"  - Occasions/Frame Std: {report['frame_analysis']['occasions_per_frame_std']:.2f}")
        
        print(f"\n[Slot Analysis]")
        print(f"  - Total Slots: {report['slot_analysis']['total_slots']}")
        print(f"  - Most Common Slot: {report['slot_analysis']['most_common_slot']} ({report['slot_analysis']['most_common_slot_count']} occasions)")
        
        print(f"\n[Symbol Analysis]")
        print(f"  - Total Symbols: {report['symbol_analysis']['total_symbols']}")
        print(f"  - Most Common Symbol: {report['symbol_analysis']['most_common_symbol']} ({report['symbol_analysis']['most_common_symbol_count']} occasions)")
        
        print(f"\n[Collision Analysis]")
        print(f"  - Total Collision Patterns: {report['collision_analysis']['total_collision_patterns']}")
        print(f"  - Max Collision Count: {report['collision_analysis']['max_collision_count']}")
        
        print(f"\n[Gap Analysis]")
        print(f"  - Total Gaps: {report['gap_analysis']['total_gaps']}")
        print(f"  - Gap Mean: {report['gap_analysis']['gap_statistics']['mean']:.2f} symbols")
        print(f"  - Gap Std: {report['gap_analysis']['gap_statistics']['std']:.2f} symbols")
        
        return report
    
    def step4_visualize_results(self) -> None:
        """Step 4: 결과 시각화"""
        print("\n" + "="*60)
        print("STEP 4: Visualizing Results")
        print("="*60)
        
        self.visualizer = PRACHVisualizer(self.df)
        
        # 종합 대시보드 저장
        dashboard_path = self.output_dir / "comprehensive_dashboard.png"
        self.visualizer.plot_comprehensive_dashboard(output_path=str(dashboard_path))
        print(f"✓ 종합 대시보드 저장: {dashboard_path}")
        
        # 개별 플롯 저장
        plots_dir = self.output_dir / "individual_plots"
        self.visualizer.export_all_plots(str(plots_dir))
        print(f"✓ 개별 플롯 저장: {plots_dir}")
    
    def step5_export_results(self, report: Dict[str, Any]) -> None:
        """Step 5: 결과 내보내기"""
        print("\n" + "="*60)
        print("STEP 5: Exporting Results")
        print("="*60)
        
        # CSV 내보내기
        csv_path = self.output_dir / "prach_occasions.csv"
        self.analyzer.export_to_csv(str(csv_path))
        print(f"✓ CSV 내보내기: {csv_path}")
        
        # JSON 내보내기
        json_path = self.output_dir / "prach_occasions.json"
        self.analyzer.export_to_json(str(json_path))
        print(f"✓ JSON 내보내기: {json_path}")
        
        # 분석 리포트 내보내기
        report_path = self.output_dir / "analysis_report.json"
        self.analyzer.export_analysis_report(str(report_path))
        print(f"✓ 분석 리포트 내보내기: {report_path}")
        
        # 요약 통계 내보내기
        summary_path = self.output_dir / "summary_statistics.txt"
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(self._generate_summary_text(report))
        print(f"✓ 요약 통계 내보내기: {summary_path}")
        
        # HTML 리포트 생성
        html_path = self.output_dir / "analysis_report.html"
        self._generate_html_report(report, str(html_path))
        print(f"✓ HTML 리포트 생성: {html_path}")
    
    def _generate_summary_text(self, report: Dict[str, Any]) -> str:
        """요약 텍스트 생성"""
        text = f"""
PRACH ANALYSIS SUMMARY REPORT
{'='*60}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
SIB1 File: {self.sib1_file}

[PRACH Configuration]
{'-'*60}
PRACH Config Index: {self.prach_config.get('prach_configuration_index')}
msg1 FDM: {self.prach_config.get('msg1_fdm')} ({self.prach_config.get('msg1_fdm_value')} multiplexing)
msg1 Frequency Start: {self.prach_config.get('msg1_frequency_start')} RB
Zero Correlation Zone: {self.prach_config.get('zero_correlation_zone_config')}
Preamble Transmission Max: {self.prach_config.get('preamble_trans_max')} ({self.prach_config.get('preamble_trans_max_value')} retries)
RA Response Window: {self.prach_config.get('ra_response_window')} ({self.prach_config.get('ra_response_window_slots')} slots)
Power Ramping Step: {self.prach_config.get('power_ramping_step')} ({self.prach_config.get('power_ramping_step_db')} dB)
Preamble Target Power: {self.prach_config.get('preamble_received_target_power')} dBm

[Overview]
{'-'*60}
Total PRACH Occasions: {report['overview']['total_occasions']:,}
Frame Range: {report['overview']['frame_range'][0]} - {report['overview']['frame_range'][1]}
Total Frames: {report['overview']['total_frames']}

[Frame Analysis]
{'-'*60}
Occasions per Frame (Mean): {report['frame_analysis']['occasions_per_frame_mean']:.2f}
Occasions per Frame (Std): {report['frame_analysis']['occasions_per_frame_std']:.2f}
Occasions per Frame (Min): {report['frame_analysis']['occasions_per_frame_min']:.0f}
Occasions per Frame (Max): {report['frame_analysis']['occasions_per_frame_max']:.0f}

[Slot Analysis]
{'-'*60}
Total Unique Slots: {report['slot_analysis']['total_slots']}
Most Common Slot: {report['slot_analysis']['most_common_slot']}
Most Common Slot Count: {report['slot_analysis']['most_common_slot_count']}

[Symbol Analysis]
{'-'*60}
Total Unique Symbols: {report['symbol_analysis']['total_symbols']}
Most Common Symbol: {report['symbol_analysis']['most_common_symbol']}
Most Common Symbol Count: {report['symbol_analysis']['most_common_symbol_count']}

[Collision Analysis]
{'-'*60}
Total Collision Patterns: {report['collision_analysis']['total_collision_patterns']}
Max Collision Count: {report['collision_analysis']['max_collision_count']}

[Gap Analysis]
{'-'*60}
Total Gaps: {report['gap_analysis']['total_gaps']}
Gap Mean: {report['gap_analysis']['gap_statistics']['mean']:.2f} symbols
Gap Std: {report['gap_analysis']['gap_statistics']['std']:.2f} symbols
Gap Min: {report['gap_analysis']['gap_statistics']['min']:.0f} symbols
Gap Max: {report['gap_analysis']['gap_statistics']['max']:.0f} symbols
Gap Median: {report['gap_analysis']['gap_statistics']['median']:.0f} symbols
"""
        
        return text
    
    def _generate_html_report(self, report: Dict[str, Any], output_path: str) -> None:
        """HTML 리포트 생성"""
        html_content = f"""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>PRACH Analysis Report</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #2E86AB;
                    border-bottom: 3px solid #2E86AB;
                    padding-bottom: 10px;
                }}
                h2 {{
                    color: #A23B72;
                    margin-top: 30px;
                }}
                .section {{
                    margin: 20px 0;
                    padding: 15px;
                    background-color: #f9f9f9;
                    border-left: 4px solid #2E86AB;
                }}
                .stat-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 15px;
                }}
                .stat-box {{
                    background-color: white;
                    padding: 15px;
                    border-radius: 5px;
                    border: 1px solid #ddd;
                }}
                .stat-box h3 {{
                    margin: 0 0 10px 0;
                    color: #2E86AB;
                    font-size: 14px;
                }}
                .stat-box .value {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #333;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 15px 0;
                }}
                th, td {{
                    padding: 10px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }}
                th {{
                    background-color: #2E86AB;
                    color: white;
                    font-weight: bold;
                }}
                tr:hover {{
                    background-color: #f5f5f5;
                }}
                .timestamp {{
                    color: #999;
                    font-size: 12px;
                }}
                img {{
                    max-width: 100%;
                    height: auto;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>PRACH Analysis Report</h1>
                <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p class="timestamp">SIB1 File: {self.sib1_file}</p>
                
                <h2>PRACH Configuration</h2>
                <div class="section">
                    <table>
                        <tr>
                            <td><strong>PRACH Config Index:</strong></td>
                            <td>{self.prach_config.get('prach_configuration_index')}</td>
                        </tr>
                        <tr>
                            <td><strong>msg1 FDM:</strong></td>
                            <td>{self.prach_config.get('msg1_fdm')} ({self.prach_config.get('msg1_fdm_value')} multiplexing)</td>
                        </tr>
                        <tr>
                            <td><strong>msg1 Frequency Start:</strong></td>
                            <td>{self.prach_config.get('msg1_frequency_start')} RB</td>
                        </tr>
                        <tr>
                            <td><strong>RA Response Window:</strong></td>
                            <td>{self.prach_config.get('ra_response_window')} ({self.prach_config.get('ra_response_window_slots')} slots)</td>
                        </tr>
                    </table>
                </div>
                
                <h2>Analysis Overview</h2>
                <div class="stat-grid">
                    <div class="stat-box">
                        <h3>Total PRACH Occasions</h3>
                        <div class="value">{report['overview']['total_occasions']:,}</div>
                    </div>
                    <div class="stat-box">
                        <h3>Frame Range</h3>
                        <div class="value">{report['overview']['frame_range'][0]} - {report['overview']['frame_range'][1]}</div>
                    </div>
                    <div class="stat-box">
                        <h3>Occasions per Frame</h3>
                        <div class="value">{report['frame_analysis']['occasions_per_frame_mean']:.2f}</div>
                    </div>
                    <div class="stat-box">
                        <h3>Most Common Slot</h3>
                        <div class="value">{report['slot_analysis']['most_common_slot']}</div>
                    </div>
                </div>
                
                <h2>Results</h2>
                <div class="section">
                    <p>Results have been saved to the following files:</p>
                    <ul>
                        <li>prach_occasions.csv - PRACH occasion 데이터</li>
                        <li>prach_occasions.json - JSON 형식 데이터</li>
                        <li>analysis_report.json - 상세 분석 리포트</li>
                        <li>comprehensive_dashboard.png - 종합 시각화</li>
                        <li>individual_plots/ - 개별 차트</li>
                    </ul>
                </div>
                
                <h2>Visualization</h2>
                <div class="section">
                    <img src="comprehensive_dashboard.png" alt="Comprehensive Dashboard">
                </div>
            </div>
        </body>
        </html>
        """
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def run_full_analysis(self, num_frames: int = 1000) -> None:
        """전체 분석 파이프라인 실행"""
        print("\n")
        print("╔" + "="*58 + "╗")
        print("║" + " "*58 + "║")
        print("║" + "  PRACH ANALYZER - Advanced Analysis Tool".center(58) + "║")
        print("║" + " "*58 + "║")
        print("╚" + "="*58 + "╝")
        
        try:
            # Step 1: Parse SIB1
            self.step1_parse_sib1()
            
            # Step 2: Calculate PRACH Occasions
            self.step2_calculate_prach_occasions(num_frames=num_frames)
            
            # Step 3: Analyze Data
            report = self.step3_analyze_data()
            
            # Step 4: Visualize Results
            self.step4_visualize_results()
            
            # Step 5: Export Results
            self.step5_export_results(report)
            
            print("\n" + "="*60)
            print("✓ 분석 완료!")
            print("="*60)
            print(f"\n결과 저장 위치: {self.output_dir.absolute()}")
            print("\n생성된 파일:")
            print("  1. prach_occasions.csv - PRACH occasion 데이터 (CSV)")
            print("  2. prach_occasions.json - PRACH occasion 데이터 (JSON)")
            print("  3. analysis_report.json - 상세 분석 리포트")
            print("  4. analysis_report.html - 웹 리포트")
            print("  5. summary_statistics.txt - 요약 통계")
            print("  6. comprehensive_dashboard.png - 종합 대시보드 이미지")
            print("  7. individual_plots/ - 개별 차트 이미지들")
            print("\n")
            
        except Exception as e:
            print(f"\n✗ 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == '__main__':
    # 사용 예시
    analyzer = PRACHAnalyzer('SIB1.txt', output_dir='analysis_results')
    analyzer.run_full_analysis(num_frames=1000)
