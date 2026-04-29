"""
PRACH 웹 대시보드 (Flask)
레거시: 단일 진입은 상위 디렉터리 `streamlit run app.py` 를 사용하세요.
"""

from flask import Flask, render_template_string, jsonify, request, send_file
from flask_cors import CORS
import pandas as pd
import json
import io
from pathlib import Path
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

from prach_analyzer import PRACHAnalyzer
from prach_time_frequency_mapper import PRACHTimeFrequencyMapper


app = Flask(__name__)
CORS(app)

# Manual mode format-to-configuration recommendation table.
FORMAT_RECOMMENDED_CONFIG_INDEX = {
    '0': 14,
    '1': 14,
    '2': 14,
    '3': 14,
    'A1': 64,
    'A2': 64,
    'A3': 64,
    'B1': 64,
    'B2': 146,
    'B3': 146,
    'B4': 64,
    'C0': 64,
    'C2': 64,
}


def recommend_config_index(preferred_format: str) -> int:
    fmt = (preferred_format or 'B2').upper()
    return FORMAT_RECOMMENDED_CONFIG_INDEX.get(fmt, 14)


# 전역 변수
analyzer = None
df = None
report = None


@app.route('/')
def dashboard():
    """메인 대시보드"""
    html_template = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PRACH Analyzer Dashboard</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1600px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                overflow: hidden;
            }
            
            .header {
                background: linear-gradient(135deg, #2E86AB 0%, #A23B72 100%);
                color: white;
                padding: 40px 30px;
                text-align: center;
            }
            
            .header h1 {
                font-size: 32px;
                margin-bottom: 10px;
            }
            
            .header p {
                font-size: 14px;
                opacity: 0.9;
            }
            
            .content {
                padding: 30px;
            }
            
            .control-panel {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 30px;
                border: 1px solid #e0e0e0;
            }
            
            .control-row {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 15px;
                margin-bottom: 15px;
            }
            
            .control-group {
                display: flex;
                flex-direction: column;
            }
            
            .control-group label {
                font-weight: bold;
                margin-bottom: 5px;
                color: #333;
                font-size: 13px;
            }
            
            .control-group input,
            .control-group select {
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 13px;
            }
            
            .button-group {
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
            }
            
            button {
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-weight: bold;
                font-size: 13px;
                transition: all 0.3s ease;
            }
            
            .btn-primary {
                background: #2E86AB;
                color: white;
            }
            
            .btn-primary:hover {
                background: #1e5a7a;
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(46, 134, 171, 0.3);
            }
            
            .btn-secondary {
                background: #A23B72;
                color: white;
            }
            
            .btn-secondary:hover {
                background: #7a2a55;
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-bottom: 30px;
            }
            
            .stat-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            
            .stat-card h3 {
                font-size: 12px;
                opacity: 0.9;
                margin-bottom: 10px;
                font-weight: 600;
            }
            
            .stat-card .value {
                font-size: 28px;
                font-weight: bold;
            }
            
            .charts-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }

            .table-container {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
                margin-bottom: 30px;
            }

            .table-wrap {
                max-height: 420px;
                overflow: auto;
                border: 1px solid #d9d9d9;
                border-radius: 6px;
                background: #fff;
            }

            table {
                width: 100%;
                border-collapse: collapse;
                font-size: 12px;
            }

            th, td {
                border: 1px solid #e5e5e5;
                padding: 8px 10px;
                text-align: center;
                white-space: nowrap;
            }

            th {
                position: sticky;
                top: 0;
                background: #2E86AB;
                color: white;
                z-index: 1;
                font-weight: 600;
            }

            tr:nth-child(even) {
                background: #fafafa;
            }
            
            .chart-container {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
                min-height: 400px;
            }
            
            .chart-container h3 {
                margin-bottom: 15px;
                color: #333;
                font-size: 15px;
            }
            
            .loading {
                text-align: center;
                padding: 20px;
                color: #666;
            }
            
            .spinner {
                border: 4px solid #f3f3f3;
                border-top: 4px solid #2E86AB;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto 15px;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .error-message {
                background: #f8d7da;
                color: #721c24;
                padding: 15px;
                border-radius: 4px;
                margin-bottom: 20px;
                border: 1px solid #f5c6cb;
            }
            
            .success-message {
                background: #d4edda;
                color: #155724;
                padding: 15px;
                border-radius: 4px;
                margin-bottom: 20px;
                border: 1px solid #c3e6cb;
            }
            
            .footer {
                background: #f8f9fa;
                padding: 20px 30px;
                text-align: center;
                color: #666;
                font-size: 12px;
                border-top: 1px solid #e0e0e0;
            }
            
            @media (max-width: 768px) {
                .charts-grid {
                    grid-template-columns: 1fr;
                }
                
                .header h1 {
                    font-size: 24px;
                }
                
                .stat-card .value {
                    font-size: 22px;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🛰️ PRACH Analyzer Dashboard</h1>
                <p>Advanced 5G NR PRACH Occasion Analysis Tool</p>
            </div>
            
            <div class="content">
                <!-- Control Panel -->
                <div class="control-panel">
                    <h3 style="margin-bottom: 15px; color: #333;">File Upload & Analysis Settings</h3>
                    <div class="control-row">
                        <div class="control-group">
                            <label>Input Source</label>
                            <select id="inputMode" onchange="toggleInputMode()">
                                <option value="sib1" selected>SIB1 Log Upload</option>
                                <option value="manual">Manual PRACH Settings</option>
                            </select>
                        </div>
                        <div class="control-group">
                            <label>SIB1 Log File</label>
                            <input type="file" id="sibFile" accept=".txt" placeholder="Select SIB1.txt">
                        </div>
                        <div class="control-group">
                            <label>Number of Frames</label>
                            <input type="number" id="numFrames" value="20" min="1" max="20" step="1">
                        </div>
                    </div>

                    <div id="manualSettings" style="display: none;">
                        <div class="control-row">
                            <div class="control-group">
                                <label>PRACH Format</label>
                                <select id="manualPreferredFormat" onchange="applyAutoRecommendation()">
                                    <option value="0">0</option>
                                    <option value="1">1</option>
                                    <option value="2">2</option>
                                    <option value="3">3</option>
                                    <option value="A1">A1</option>
                                    <option value="A2">A2</option>
                                    <option value="A3">A3</option>
                                    <option value="B1">B1</option>
                                    <option value="B2" selected>B2</option>
                                    <option value="B3">B3</option>
                                    <option value="B4">B4</option>
                                    <option value="C0">C0</option>
                                    <option value="C2">C2</option>
                                </select>
                            </div>
                            <div class="control-group">
                                <label>PRACH Configuration Index</label>
                                <input type="number" id="manualPrachConfigIndex" value="14" min="0" max="262" step="1">
                            </div>
                            <div class="control-group">
                                <label>msg1 FDM</label>
                                <select id="manualMsg1Fdm">
                                    <option value="1" selected>1</option>
                                    <option value="2">2</option>
                                    <option value="4">4</option>
                                    <option value="8">8</option>
                                </select>
                            </div>
                            <div class="control-group">
                                <label>msg1 Frequency Start (RB)</label>
                                <input type="number" id="manualMsg1FrequencyStart" value="7" min="0" max="274" step="1">
                            </div>
                            <div class="control-group">
                                <label>Zero Correlation Zone</label>
                                <input type="number" id="manualZeroCorrelationZone" value="9" min="0" max="15" step="1">
                            </div>
                            <div class="control-group">
                                <label>Auto Recommend Config Index</label>
                                <div style="display: flex; align-items: center; gap: 8px; height: 36px;">
                                    <input type="checkbox" id="manualAutoRecommend" checked onchange="applyAutoRecommendation()">
                                    <span style="font-size: 12px; color: #555;">Use format-based recommendation</span>
                                </div>
                                <small id="manualRecommendHint" style="margin-top: 6px; color: #666;">Recommended index: 146</small>
                            </div>
                        </div>
                    </div>
                    <div class="button-group">
                        <button class="btn-primary" onclick="uploadAndAnalyze()">🚀 Start Analysis</button>
                        <button class="btn-secondary" onclick="downloadResults()">📥 Download Results</button>
                    </div>
                </div>
                
                <!-- Messages -->
                <div id="messageContainer"></div>
                
                <!-- Statistics Cards -->
                <div id="statsContainer" class="stats-grid" style="display: none;">
                    <div class="stat-card">
                        <h3>Frames Analyzed</h3>
                        <div class="value" id="framesAnalyzed">-</div>
                    </div>
                    <div class="stat-card">
                        <h3>Time Domain</h3>
                        <div class="value" id="timeDomainInfo" style="font-size: 16px;">-</div>
                    </div>
                    <div class="stat-card">
                        <h3>Frequency Domain</h3>
                        <div class="value" id="frequencyDomainInfo" style="font-size: 16px;">-</div>
                    </div>
                    <div class="stat-card">
                        <h3>Total PRACH Occasions</h3>
                        <div class="value" id="totalOccasions">-</div>
                    </div>
                </div>
                
                <!-- Charts -->
                <div class="charts-grid" id="chartsContainer">
                    <div class="chart-container">
                        <h3>📶 Frequency Domain (RB Allocation)</h3>
                        <div id="frequencyDomainChart"></div>
                    </div>
                </div>

                <div class="table-container" id="tableContainer" style="display: none;">
                    <h3 style="margin-bottom: 12px; color: #333;">📋 Time-Frequency Result Table</h3>

                    <h4 style="margin-bottom: 8px; color: #333;">Summary Table (No Duplicates)</h4>
                    <p id="summaryTableInfo" style="margin-bottom: 12px; color: #666; font-size: 12px;"></p>
                    <div class="table-wrap" style="margin-bottom: 20px;">
                        <table id="summaryResultTable">
                            <thead>
                                <tr>
                                    <th>Frame</th>
                                    <th>Subframe</th>
                                    <th>Slot</th>
                                    <th>Symbol</th>
                                    <th>RB Start</th>
                                    <th>RB End</th>
                                    <th>Subcarrier Start</th>
                                    <th>Subcarrier End</th>
                                    <th>Preamble Count</th>
                                </tr>
                            </thead>
                            <tbody id="summaryTableBody"></tbody>
                        </table>
                    </div>

                    <h4 style="margin-bottom: 8px; color: #333;">Detail Table (Per Preamble)</h4>
                    <p id="detailTableInfo" style="margin-bottom: 12px; color: #666; font-size: 12px;"></p>
                    <div class="table-wrap">
                        <table id="detailResultTable">
                            <thead>
                                <tr>
                                    <th>Occasion ID</th>
                                    <th>Frame</th>
                                    <th>Subframe</th>
                                    <th>Slot</th>
                                    <th>Symbol</th>
                                    <th>Preamble</th>
                                    <th>RB Start</th>
                                    <th>RB End</th>
                                    <th>Subcarrier Start</th>
                                    <th>Subcarrier End</th>
                                </tr>
                            </thead>
                            <tbody id="detailTableBody"></tbody>
                        </table>
                    </div>
                </div>
            </div>
            
            <div class="footer">
                <p>PRACH Analyzer v1.0 | 5G NR PRACH Occasion Analysis Tool | © 2026</p>
            </div>
        </div>
        
        <script>
            function showMessage(message, type = 'info') {
                const container = document.getElementById('messageContainer');
                const className = type === 'error' ? 'error-message' : 'success-message';
                container.innerHTML = `<div class="${className}">${message}</div>`;
                setTimeout(() => {
                    container.innerHTML = '';
                }, 5000);
            }

            function getRecommendedConfigIndex(format) {
                const map = {
                    '0': 14,
                    '1': 14,
                    '2': 14,
                    '3': 14,
                    'A1': 64,
                    'A2': 64,
                    'A3': 64,
                    'B1': 64,
                    'B2': 146,
                    'B3': 146,
                    'B4': 64,
                    'C0': 64,
                    'C2': 64
                };
                return map[format] || 14;
            }

            function applyAutoRecommendation() {
                const format = document.getElementById('manualPreferredFormat').value;
                const autoRecommend = document.getElementById('manualAutoRecommend').checked;
                const indexInput = document.getElementById('manualPrachConfigIndex');
                const hint = document.getElementById('manualRecommendHint');

                const recommended = getRecommendedConfigIndex(format);
                hint.textContent = `Recommended index: ${recommended}`;

                if (autoRecommend) {
                    indexInput.value = recommended;
                }
            }

            function toggleInputMode() {
                const inputMode = document.getElementById('inputMode').value;
                const fileInput = document.getElementById('sibFile');
                const manualPanel = document.getElementById('manualSettings');

                if (inputMode === 'manual') {
                    manualPanel.style.display = 'block';
                    fileInput.disabled = true;
                    applyAutoRecommendation();
                } else {
                    manualPanel.style.display = 'none';
                    fileInput.disabled = false;
                }
            }
            
            function uploadAndAnalyze() {
                const inputMode = document.getElementById('inputMode').value;
                const fileInput = document.getElementById('sibFile');
                const rawFrames = parseInt(document.getElementById('numFrames').value || '20', 10);
                const numFrames = Math.max(1, Math.min(20, rawFrames));
                document.getElementById('numFrames').value = numFrames;
                
                if (inputMode === 'sib1' && !fileInput.files.length) {
                    showMessage('Please select a SIB1 file', 'error');
                    return;
                }
                
                const formData = new FormData();
                formData.append('inputMode', inputMode);
                formData.append('numFrames', numFrames);

                if (inputMode === 'sib1') {
                    formData.append('file', fileInput.files[0]);
                } else {
                    const autoRecommend = document.getElementById('manualAutoRecommend').checked;
                    formData.append('manualPrachConfigIndex', document.getElementById('manualPrachConfigIndex').value || '14');
                    formData.append('manualMsg1Fdm', document.getElementById('manualMsg1Fdm').value || '1');
                    formData.append('manualMsg1FrequencyStart', document.getElementById('manualMsg1FrequencyStart').value || '7');
                    formData.append('manualZeroCorrelationZone', document.getElementById('manualZeroCorrelationZone').value || '9');
                    formData.append('manualPreferredFormat', document.getElementById('manualPreferredFormat').value || 'B2');
                    formData.append('manualAutoRecommend', autoRecommend ? 'true' : 'false');
                }
                
                const container = document.getElementById('messageContainer');
                container.innerHTML = '<div class="loading"><div class="spinner"></div>Analyzing PRACH data...</div>';
                
                fetch('/analyze', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        displayResults(data);
                        showMessage('Analysis completed successfully!', 'success');
                    } else {
                        showMessage(data.error, 'error');
                    }
                })
                .catch(error => {
                    showMessage('Error: ' + error, 'error');
                });
            }
            
            function displayResults(data) {
                // Update stats
                document.getElementById('statsContainer').style.display = 'grid';
                document.getElementById('totalOccasions').textContent = data.stats.total_occasions.toLocaleString();
                document.getElementById('framesAnalyzed').textContent = data.stats.frames_analyzed;
                document.getElementById('timeDomainInfo').textContent = `Frame 0-${data.stats.frame_range[1]}, Slot ${data.stats.slot}, Symbol ${data.stats.symbol}`;
                document.getElementById('frequencyDomainInfo').textContent = `RB ${data.stats.rb_range}, SC ${data.stats.subcarrier_range[0]}-${data.stats.subcarrier_range[1]}`;
                
                // Create charts
                createFrequencyDomainChart(data.frequency_domain_chart);
                renderSummaryTable(data.summary_table_rows, data.summary_total_rows, data.summary_shown_rows);
                renderDetailTable(data.detail_table_rows, data.detail_total_rows, data.detail_shown_rows);
            }
            
            function createFrequencyDomainChart(data) {
                const trace = {
                    x: data.rb_indices,
                    y: data.rb_allocated,
                    type: 'bar',
                    marker: {
                        color: data.rb_allocated.map(v => v > 0 ? '#C73E1D' : '#d9d9d9')
                    },
                    hovertemplate: 'RB %{x}: %{y}<extra></extra>'
                };
                const layout = {
                    title: '',
                    xaxis: { title: 'RB Index' },
                    yaxis: { title: 'Allocated (1=yes, 0=no)' },
                    annotations: [
                        {
                            x: data.rb_start,
                            y: 1.08,
                            text: `Start RB ${data.rb_start}`,
                            showarrow: false,
                            font: { size: 11, color: '#2E86AB' }
                        },
                        {
                            x: data.rb_end,
                            y: 1.08,
                            text: `End RB ${data.rb_end}`,
                            showarrow: false,
                            font: { size: 11, color: '#2E86AB' }
                        },
                        {
                            x: (data.rb_start + data.rb_end) / 2,
                            y: 1.18,
                            text: `Subcarrier ${data.subcarrier_start} -> ${data.subcarrier_end} (repeat every frame)`,
                            showarrow: false,
                            font: { size: 11, color: '#444' }
                        }
                    ],
                    margin: { l: 50, r: 30, t: 30, b: 50 }
                };
                Plotly.newPlot('frequencyDomainChart', [trace], layout, { responsive: true });
            }

            function renderSummaryTable(rows, totalRows, shownRows) {
                const tableContainer = document.getElementById('tableContainer');
                const info = document.getElementById('summaryTableInfo');
                const tbody = document.getElementById('summaryTableBody');

                tableContainer.style.display = 'block';
                info.textContent = `Showing ${shownRows.toLocaleString()} of ${totalRows.toLocaleString()} summary rows`;
                tbody.innerHTML = '';

                rows.forEach(row => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${row.frame}</td>
                        <td>${row.subframe}</td>
                        <td>${row.slot}</td>
                        <td>${row.symbol}</td>
                        <td>${row.rb_start}</td>
                        <td>${row.rb_end}</td>
                        <td>${row.subcarrier_start}</td>
                        <td>${row.subcarrier_end}</td>
                        <td>${row.preamble_count}</td>
                    `;
                    tbody.appendChild(tr);
                });
            }

            function renderDetailTable(rows, totalRows, shownRows) {
                const info = document.getElementById('detailTableInfo');
                const tbody = document.getElementById('detailTableBody');

                info.textContent = `Showing ${shownRows.toLocaleString()} of ${totalRows.toLocaleString()} detail rows`;
                tbody.innerHTML = '';

                rows.forEach(row => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${row.occasion_id}</td>
                        <td>${row.frame}</td>
                        <td>${row.subframe}</td>
                        <td>${row.slot}</td>
                        <td>${row.symbol}</td>
                        <td>${row.preamble_index}</td>
                        <td>${row.rb_start}</td>
                        <td>${row.rb_end}</td>
                        <td>${row.subcarrier_start}</td>
                        <td>${row.subcarrier_end}</td>
                    `;
                    tbody.appendChild(tr);
                });
            }
            
            function downloadResults() {
                showMessage('Feature coming soon...', 'info');
            }
        </script>
    </body>
    </html>
    """
    
    return render_template_string(html_template)


@app.route('/analyze', methods=['POST'])
def analyze():
    """분석 실행"""
    temp_path = None
    try:
        input_mode = (request.form.get('inputMode') or 'sib1').strip().lower()
        num_frames = int(request.form.get('numFrames', 20))
        num_frames = max(1, min(20, num_frames))

        global analyzer, df, report

        if input_mode == 'sib1':
            if 'file' not in request.files:
                return jsonify({'success': False, 'error': 'No file uploaded'})

            file = request.files['file']
            if not file or not file.filename:
                return jsonify({'success': False, 'error': 'SIB1 file is empty'})

            # 임시 파일로 저장
            temp_path = Path('temp_sib1.txt')
            file.save(str(temp_path))

            # 기존 파서로 SIB1 설정 파싱
            analyzer = PRACHAnalyzer(str(temp_path), output_dir='analysis_results')
            analyzer.step1_parse_sib1()
            prach_cfg = analyzer.prach_config
        else:
            # 수동 설정 모드
            preferred_format = (request.form.get('manualPreferredFormat') or 'B2').strip().upper()
            auto_recommend = (request.form.get('manualAutoRecommend') or 'true').strip().lower() == 'true'
            requested_config_index = int(request.form.get('manualPrachConfigIndex', 14))
            used_config_index = recommend_config_index(preferred_format) if auto_recommend else requested_config_index

            manual_cfg = {
                'prach_configuration_index': used_config_index,
                'msg1_fdm_value': int(request.form.get('manualMsg1Fdm', 1)),
                'msg1_frequency_start': int(request.form.get('manualMsg1FrequencyStart', 7)),
                'zero_correlation_zone_config': int(request.form.get('manualZeroCorrelationZone', 9)),
                'preferred_format': preferred_format,
                'auto_recommend': auto_recommend,
                'requested_config_index': requested_config_index,
                'recommended_config_index': recommend_config_index(preferred_format),
            }
            prach_cfg = manual_cfg

            # 기존 output 흐름 호환을 위해 analyzer 인스턴스는 유지
            analyzer = PRACHAnalyzer('SIB1.txt', output_dir='analysis_results')
            analyzer.prach_config = {
                'prach_configuration_index': manual_cfg['prach_configuration_index'],
                'msg1_fdm_value': manual_cfg['msg1_fdm_value'],
                'msg1_frequency_start': manual_cfg['msg1_frequency_start'],
                'zero_correlation_zone_config': manual_cfg['zero_correlation_zone_config'],
            }

        # Time-Frequency 매퍼로 실제 시간/주파수 도메인 데이터 생성
        mapper = PRACHTimeFrequencyMapper(
            prach_config_index=int(prach_cfg.get('prach_configuration_index', 14)),
            msg1_frequency_start=int(prach_cfg.get('msg1_frequency_start', 7)),
            msg1_fdm=int(prach_cfg.get('msg1_fdm_value', 1)),
            num_frames=num_frames,
            scs=15
        )
        df = mapper.calculate_prach_occasions()
        report = mapper.get_time_frequency_summary()
        
        # 결과 준비
        slot_value = int(df['slot'].mode()[0])
        symbol_value = int(df['symbol'].mode()[0])

        rb_axis = list(range(report['frequency_domain']['rb_start'], report['frequency_domain']['rb_end'] + 1))
        total_rbs = 150
        allocated = [0] * total_rbs
        for rb in rb_axis:
            if 0 <= rb < total_rbs:
                allocated[rb] = 1

        frequency_domain_chart = {
            'rb_indices': list(range(total_rbs)),
            'rb_allocated': allocated,
            'rb_start': int(report['frequency_domain']['rb_start']),
            'rb_end': int(report['frequency_domain']['rb_end']),
            'subcarrier_start': int(report['frequency_domain']['subcarrier_start']),
            'subcarrier_end': int(report['frequency_domain']['subcarrier_end'])
        }

        # 요약 테이블: 중복 제거 (frame/slot/symbol/frequency 기준)
        summary_group_cols = [
            'frame', 'subframe', 'slot', 'symbol',
            'rb_start', 'rb_end', 'subcarrier_start', 'subcarrier_end'
        ]
        summary_df = (
            df.groupby(summary_group_cols, as_index=False)
            .agg(preamble_count=('preamble_index', 'nunique'))
            .sort_values(by=['frame', 'slot', 'symbol'])
        )
        max_summary_rows = 200
        summary_df = summary_df.head(max_summary_rows).copy()
        summary_table_rows = [
            {
                'frame': int(r['frame']),
                'subframe': int(r['subframe']),
                'slot': int(r['slot']),
                'symbol': int(r['symbol']),
                'rb_start': int(r['rb_start']),
                'rb_end': int(r['rb_end']),
                'subcarrier_start': int(r['subcarrier_start']),
                'subcarrier_end': int(r['subcarrier_end']),
                'preamble_count': int(r['preamble_count']),
            }
            for _, r in summary_df.iterrows()
        ]

        # 상세 테이블: preamble 단위
        detail_columns = [
            'occasion_id', 'frame', 'subframe', 'slot', 'symbol',
            'preamble_index', 'rb_start', 'rb_end', 'subcarrier_start', 'subcarrier_end'
        ]
        max_detail_rows = 300
        detail_df = df[detail_columns].head(max_detail_rows).copy()
        detail_table_rows = [
            {
                'occasion_id': int(r['occasion_id']),
                'frame': int(r['frame']),
                'subframe': int(r['subframe']),
                'slot': int(r['slot']),
                'symbol': int(r['symbol']),
                'preamble_index': int(r['preamble_index']),
                'rb_start': int(r['rb_start']),
                'rb_end': int(r['rb_end']),
                'subcarrier_start': int(r['subcarrier_start']),
                'subcarrier_end': int(r['subcarrier_end']),
            }
            for _, r in detail_df.iterrows()
        ]
        
        results = {
            'success': True,
            'frequency_domain_chart': frequency_domain_chart,
            'summary_table_rows': summary_table_rows,
            'summary_total_rows': int(df[summary_group_cols].drop_duplicates().shape[0]),
            'summary_shown_rows': int(len(summary_table_rows)),
            'detail_table_rows': detail_table_rows,
            'detail_total_rows': int(len(df)),
            'detail_shown_rows': int(len(detail_table_rows)),
            'stats': {
                'total_occasions': len(df),
                'frame_range': [int(df['frame'].min()), int(df['frame'].max())],
                'frames_analyzed': num_frames,
                'slot': slot_value,
                'symbol': symbol_value,
                'rb_range': f"{report['frequency_domain']['rb_start']}-{report['frequency_domain']['rb_end']}",
                'subcarrier_range': [
                    int(report['frequency_domain']['subcarrier_start']),
                    int(report['frequency_domain']['subcarrier_end'])
                ],
                'config_index_used': int(prach_cfg.get('prach_configuration_index', 14)),
                'input_mode': input_mode,
            }
        }

        if input_mode == 'manual':
            results['manual_settings'] = {
                'preferred_format': str(prach_cfg.get('preferred_format', 'B2')),
                'auto_recommend': bool(prach_cfg.get('auto_recommend', True)),
                'requested_config_index': int(prach_cfg.get('requested_config_index', prach_cfg.get('prach_configuration_index', 14))),
                'recommended_config_index': int(prach_cfg.get('recommended_config_index', prach_cfg.get('prach_configuration_index', 14))),
                'used_config_index': int(prach_cfg.get('prach_configuration_index', 14)),
            }
        
        # 결과 내보내기
        mapper.generate_comprehensive_report(output_dir='time_frequency_analysis')

        if input_mode == 'sib1':
            analyzer.step2_calculate_prach_occasions(num_frames=num_frames)
            legacy_report = analyzer.step3_analyze_data()
            analyzer.step4_visualize_results()
            analyzer.step5_export_results(legacy_report)
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()


@app.route('/download-report')
def download_report():
    """분석 결과 다운로드"""
    try:
        tf_output_dir = Path('time_frequency_analysis')
        tf_csv_path = tf_output_dir / 'time_frequency_mapping.csv'
        legacy_output_dir = Path('analysis_results')
        legacy_csv_path = legacy_output_dir / 'prach_occasions.csv'
        
        if tf_csv_path.exists():
            return send_file(str(tf_csv_path), as_attachment=True, download_name='time_frequency_mapping.csv')
        if legacy_csv_path.exists():
            return send_file(str(legacy_csv_path), as_attachment=True, download_name='prach_occasions.csv')
        else:
            return {'error': 'No results available'}, 404
    except Exception as e:
        return {'error': str(e)}, 500


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
