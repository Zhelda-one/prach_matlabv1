"""
PRACH 분석 메인 엔진
모든 모듈을 통합하여 완전한 분석 파이프라인을 제공합니다.
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from .sib1_parser import SIB1Parser
from .prach_calculator import PRACHCalculator, SubcarrierSpacing
from .data_analyzer import PRACHDataAnalyzer


class PRACHAnalyzer:
    """PRACH 분석 통합 클래스"""

    def __init__(self, sib1_file: Optional[str] = None, *, text: Optional[str] = None, output_dir: str = "analysis_results"):
        if not sib1_file and text is None:
            raise TypeError("sib1_file 또는 text= 중 하나는 필수입니다.")
        self.sib1_file = sib1_file or "(in-memory SIB1)"
        self._sib_text = text
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.parser: Optional[SIB1Parser] = None
        self.prach_config: Optional[Dict[str, Any]] = None
        self.calculator: Optional[PRACHCalculator] = None
        self.df: Optional[pd.DataFrame] = None
        self.analyzer: Optional[PRACHDataAnalyzer] = None
        self.visualizer: Optional[Any] = None  # PRACHVisualizer — step4에서만 로드 (matplotlib 선택)

    def step1_parse_sib1(self) -> Dict[str, Any]:
        if self._sib_text is not None:
            self.parser = SIB1Parser(text=self._sib_text)
        else:
            self.parser = SIB1Parser(self.sib1_file)
        data = self.parser.parse()
        self.prach_config = data["prach_config"]
        return data

    def step2_calculate_prach_occasions(self, num_frames: int = 1000) -> pd.DataFrame:
        if self.prach_config is None:
            raise RuntimeError("step1_parse_sib1 을 먼저 실행하세요.")
        pci = self.prach_config["prach_configuration_index"]
        if pci is None:
            raise ValueError("prach_ConfigurationIndex 가 없습니다.")
        self.calculator = PRACHCalculator(
            prach_config_index=int(pci),
            msg1_fdm=int(self.prach_config["msg1_fdm_value"] or 1),
            msg1_frequency_start=int(self.prach_config["msg1_frequency_start"] or 0),
            scs=SubcarrierSpacing.KHZ_15,
            zero_correlation_zone_config=int(self.prach_config["zero_correlation_zone_config"] or 0),
        )

        self.df = self.calculator.calculate_prach_timing(num_frames=num_frames)
        return self.df

    def step3_analyze_data(self) -> Dict[str, Any]:
        if self.df is None:
            raise RuntimeError("step2_calculate_prach_occasions 를 먼저 실행하세요.")
        self.analyzer = PRACHDataAnalyzer(self.df)
        return self.analyzer.generate_full_report()

    def step4_visualize_results(self) -> None:
        if self.df is None:
            raise RuntimeError("step2_calculate_prach_occasions 를 먼저 실행하세요.")
        from .visualizer import PRACHVisualizer  # matplotlib 필요 — step4 전용

        self.visualizer = PRACHVisualizer(self.df)
        dashboard_path = self.output_dir / "comprehensive_dashboard.png"
        self.visualizer.plot_comprehensive_dashboard(output_path=str(dashboard_path))
        plots_dir = self.output_dir / "individual_plots"
        self.visualizer.export_all_plots(str(plots_dir))

    def step5_export_results(self, report: Dict[str, Any]) -> None:
        if self.analyzer is None:
            raise RuntimeError("step3_analyze_data 를 먼저 실행하세요.")
        csv_path = self.output_dir / "prach_occasions.csv"
        self.analyzer.export_to_csv(str(csv_path))
        json_path = self.output_dir / "prach_occasions.json"
        self.analyzer.export_to_json(str(json_path))
        report_path = self.output_dir / "analysis_report.json"
        self.analyzer.export_analysis_report(str(report_path))
        summary_path = self.output_dir / "summary_statistics.txt"
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(self._generate_summary_text(report))
        html_path = self.output_dir / "analysis_report.html"
        self._generate_html_report(report, str(html_path))

    def _generate_summary_text(self, report: Dict[str, Any]) -> str:
        assert self.prach_config is not None
        return f"""
PRACH ANALYSIS SUMMARY REPORT
{'=' * 60}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
SIB1 File: {self.sib1_file}

[PRACH Configuration]
{'-' * 60}
PRACH Config Index: {self.prach_config.get('prach_configuration_index')}
msg1 FDM: {self.prach_config.get('msg1_fdm')} ({self.prach_config.get('msg1_fdm_value')} multiplexing)
msg1 Frequency Start: {self.prach_config.get('msg1_frequency_start')} RB
Zero Correlation Zone: {self.prach_config.get('zero_correlation_zone_config')}
Preamble Transmission Max: {self.prach_config.get('preamble_trans_max')} ({self.prach_config.get('preamble_trans_max_value')} retries)
RA Response Window: {self.prach_config.get('ra_response_window')} ({self.prach_config.get('ra_response_window_slots')} slots)
Power Ramping Step: {self.prach_config.get('power_ramping_step')} ({self.prach_config.get('power_ramping_step_db')} dB)
Preamble Target Power: {self.prach_config.get('preamble_received_target_power')} dBm

[Overview]
{'-' * 60}
Total PRACH Occasions: {report['overview']['total_occasions']:,}
Frame Range: {report['overview']['frame_range'][0]} - {report['overview']['frame_range'][1]}
Total Frames: {report['overview']['total_frames']}

[Frame Analysis]
{'-' * 60}
Occasions per Frame (Mean): {report['frame_analysis']['occasions_per_frame_mean']:.2f}
Occasions per Frame (Std): {report['frame_analysis']['occasions_per_frame_std']:.2f}
Occasions per Frame (Min): {report['frame_analysis']['occasions_per_frame_min']:.0f}
Occasions per Frame (Max): {report['frame_analysis']['occasions_per_frame_max']:.0f}

[Slot Analysis]
{'-' * 60}
Total Unique Slots: {report['slot_analysis']['total_slots']}
Most Common Slot: {report['slot_analysis']['most_common_slot']}
Most Common Slot Count: {report['slot_analysis']['most_common_slot_count']}

[Symbol Analysis]
{'-' * 60}
Total Unique Symbols: {report['symbol_analysis']['total_symbols']}
Most Common Symbol: {report['symbol_analysis']['most_common_symbol']}
Most Common Symbol Count: {report['symbol_analysis']['most_common_symbol_count']}

[Collision Analysis]
{'-' * 60}
Total Collision Patterns: {report['collision_analysis']['total_collision_patterns']}
Max Collision Count: {report['collision_analysis']['max_collision_count']}

[Gap Analysis]
{'-' * 60}
Total Gaps: {report['gap_analysis']['total_gaps']}
Gap Mean: {report['gap_analysis']['gap_statistics']['mean']:.2f} symbols
Gap Std: {report['gap_analysis']['gap_statistics']['std']:.2f} symbols
Gap Min: {report['gap_analysis']['gap_statistics']['min']:.0f} symbols
Gap Max: {report['gap_analysis']['gap_statistics']['max']:.0f} symbols
Gap Median: {report['gap_analysis']['gap_statistics']['median']:.0f} symbols
"""

    def _generate_html_report(self, report: Dict[str, Any], output_path: str) -> None:
        assert self.prach_config is not None
        html_content = f"""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <title>PRACH Analysis Report</title>
        </head>
        <body>
            <h1>PRACH Analysis Report</h1>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>SIB1: {self.sib1_file}</p>
            <h2>Overview</h2>
            <p>Total occasions: {report['overview']['total_occasions']:,}</p>
        </body>
        </html>
        """
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

    def run_full_analysis(self, num_frames: int = 1000) -> None:
        self.step1_parse_sib1()
        self.step2_calculate_prach_occasions(num_frames=num_frames)
        report = self.step3_analyze_data()
        self.step4_visualize_results()
        self.step5_export_results(report)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "SIB1.txt"
    analyzer = PRACHAnalyzer(path, output_dir="analysis_results")
    analyzer.run_full_analysis(num_frames=1000)
