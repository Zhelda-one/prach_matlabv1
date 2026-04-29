% 파일명: test_prach.m
function [configIndex, msg] = test_prach(formatType, scs)
    % 파이썬에서 넘겨준 변수가 MATLAB 쪽에 잘 도착했는지 콘솔에 출력
    disp(['[MATLAB 실행중] 전달받은 포맷: ', formatType]);
    disp(['[MATLAB 실행중] 전달받은 SCS: ', num2str(scs)]);
    
    % 임시 로직 (나중에 여기에 진짜 5G Toolbox 코드가 들어갑니다)
    if strcmp(formatType, 'B2')
        configIndex = 119;
    else
        configIndex = 10;
    end
    
    % 파이썬으로 돌려보낼 메시지
    msg = '파이썬과 MATLAB 연결이 완벽하게 성공했습니다!';
end