% 파일명: prach_backend.m
% Streamlit 앱에서 nrPRACHConfig / nrCarrierConfig 를 사용자 입력에 맞추고,
% 리소스 그리드·파형·OFDM 정보를 반환합니다 (MathWorks PRACH 예제 흐름과 동일).
function [configIdx, wave_real, wave_imag, err_msg, nfft, win_len, tcp, tseq, gp, ...
    gridMag, prachFormat, numTimeOcc, prachDuration, symbolLocation, nprachSlot, activePrachSlot, sampleRateHz] = prach_backend( ...
    formatType, carrierSCS, nSizeGrid, duplexMode, sequenceIndex, preambleIndex, ...
    restrictedSetStr, zeroCorrZone, rbOffset, freqStart, freqIndex, ...
    useManualCfgIdx, manualCfgIdx, timeIdxOverride)

    err_msg = '';
    prachFormat = '';
    numTimeOcc = 0;
    prachDuration = 0;
    symbolLocation = 0;
    nprachSlot = 0;
    activePrachSlot = 0;
    sampleRateHz = nan;
    gridMag = zeros(2, 2);

    try
        carrier = nrCarrierConfig;
        carrier.SubcarrierSpacing = double(carrierSCS);
        carrier.NSizeGrid = double(nSizeGrid);

        prach = nrPRACHConfig;
        prach.FrequencyRange = 'FR1';
        prach.DuplexMode = char(duplexMode);
        prach.SequenceIndex = double(sequenceIndex);
        prach.PreambleIndex = double(preambleIndex);
        prach.RestrictedSet = char(restrictedSetStr);
        prach.ZeroCorrelationZone = double(zeroCorrZone);
        prach.RBOffset = double(rbOffset);
        prach.FrequencyStart = double(freqStart);
        prach.FrequencyIndex = double(freqIndex);

        % TS 38.211 표 선택 (예: NewRadioPRACHConfigurationExample 와 동일 분기)
        if strcmpi(prach.DuplexMode, 'TDD')
            configTable = prach.Tables.ConfigurationsFR1Unpaired;
        else
            configTable = prach.Tables.ConfigurationsFR1PairedSUL;
        end

        % 수동 ConfigurationIndex: 표가 정한 Format 과 일치하도록 PRACH SCS 설정
        % (사이드바 Preamble Format 과 무관 — Format 0/1/2 는 1.25 kHz, 3 은 5 kHz)
        if useManualCfgIdx ~= 0
            prach.ConfigurationIndex = double(manualCfgIdx);
            fmtResolved = char(prach.Format);
            if any(strcmpi(fmtResolved, {'0','1','2'}))
                prach.SubcarrierSpacing = 1.25;
            elseif strcmpi(fmtResolved, '3')
                prach.SubcarrierSpacing = 5;
            else
                prach.SubcarrierSpacing = double(carrierSCS);
            end
        else
            if any(strcmpi(formatType, {'0','1','2'}))
                prach.SubcarrierSpacing = 1.25;
            elseif strcmpi(formatType, '3')
                prach.SubcarrierSpacing = 5;
            else
                prach.SubcarrierSpacing = double(carrierSCS);
            end
            if any(strcmpi(formatType,{'A1','A2','A3','B1','B4','C0','C2'}))
                configIdx = find(strcmpi(configTable.PreambleFormat,formatType),1,'last') - 2;
            else
                if ~any(strcmpi(formatType,{'B2','B3'}))
                    configIdx = find(strcmpi(configTable.PreambleFormat,formatType),1,'last') - 1;
                else
                    configIdx = find(endsWith(configTable.PreambleFormat,formatType),1,'last') - 1;
                end
            end
            prach.ConfigurationIndex = configIdx;
        end

        % Long preamble (0–3): 단일 RO 대역이라 FrequencyIndex>0 이 흔히 무효·ActivePRACHSlot 오류 유발
        if useManualCfgIdx ~= 0
            fmtLong = char(prach.Format);
            if any(strcmpi(fmtLong, {'0','1','2','3'}))
                prach.FrequencyIndex = 0;
            end
        end

        % TimeIndex: timeIdxOverride>=0 이면 사용자 값, 아니면 B2/B3 은 마지막 occasion
        if timeIdxOverride >= 0
            prach.TimeIndex = double(timeIdxOverride);
        elseif useManualCfgIdx ~= 0
            ft = char(prach.Format);
            if endsWith(ft, 'B2', 'IgnoreCase', true) || endsWith(ft, 'B3', 'IgnoreCase', true)
                prach.TimeIndex = prach.NumTimeOccasions - 1;
            end
        elseif useManualCfgIdx == 0 && any(strcmpi(formatType,{'B2','B3'}))
            prach.TimeIndex = prach.NumTimeOccasions - 1;
        end

        % nrPRACH 만으로는 (slot, ActivePRACHSlot) 이 유효해 보여도,
        % nrPRACHOFDMModulate 에서 "ActivePRACHSlot must be 0" 등으로 실패할 수 있음 → 동일 파이프라인으로 선별.
        activeFound = false;
        grid = [];
        waveform = [];
        prachInfo = struct();
        maxSlot = 20;
        maxAPS = 8;
        for slot = 0:maxSlot
            for aps = 0:maxAPS
                try
                    prach.NPRACHSlot = slot;
                    prach.ActivePRACHSlot = aps;
                    symbols = nrPRACH(carrier, prach);
                    if ~isempty(symbols)
                        grid = nrPRACHGrid(carrier, prach);
                        indices = nrPRACHIndices(carrier, prach);
                        grid(indices) = symbols;
                        [waveform, prachInfo] = nrPRACHOFDMModulate(carrier, prach, grid);
                        activeFound = true;
                        break;
                    end
                catch
                end
            end
            if activeFound
                break;
            end
        end

        if ~activeFound
            error('선택한 PRACH 설정에서 유효한 전송 슬롯을 찾지 못했습니다. SCS·Duplex·ConfigurationIndex·슬롯 조합을 확인하세요.');
        end

        nfft = double(prachInfo.Nfft);
        win_len = double(prachInfo.Windowing);
        tcp = double(prachInfo.CyclicPrefixLengths);
        tseq = double(prachInfo.SymbolLengths);
        if isfield(prachInfo, 'GuardPeriodLengths')
            gp = double(prachInfo.GuardPeriodLengths);
        else
            gp = zeros(size(tseq));
        end

        if isfield(prachInfo, 'SampleRate')
            sampleRateHz = double(prachInfo.SampleRate);
        end

        gridMag = abs(grid);
        prachFormat = char(prach.Format);
        numTimeOcc = double(prach.NumTimeOccasions);
        prachDuration = double(prach.PRACHDuration);
        symbolLocation = double(prach.SymbolLocation);
        nprachSlot = double(prach.NPRACHSlot);
        activePrachSlot = double(prach.ActivePRACHSlot);

        configIdx = double(prach.ConfigurationIndex);

        wave_real = real(waveform);
        wave_imag = imag(waveform);

    catch ME
        err_msg = ME.message;
        configIdx = -1;
        wave_real = zeros(10,1);
        wave_imag = zeros(10,1);
        nfft = 0;
        win_len = 0;
        tcp = 0;
        tseq = 0;
        gp = 0;
        gridMag = zeros(2,2);
        prachFormat = '';
        numTimeOcc = 0;
        prachDuration = 0;
        symbolLocation = 0;
        nprachSlot = 0;
        activePrachSlot = 0;
        sampleRateHz = nan;
    end
end
