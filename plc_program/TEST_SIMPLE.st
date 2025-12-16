// 简化测试程序 - 用于验证基本编译
PROGRAM TEST_SIMPLE
VAR
    // 基本变量
    bStart: BOOL := FALSE;
    iCount: INT := 0;
    rValue: REAL := 0.0;
    sStatus: STRING(50) := 'Ready';
    tTimer: TIME := T#1s;
    
    // 定时器
    tonTest: TON;
END_VAR

// 简单逻辑
IF bStart THEN
    iCount := iCount + 1;
    rValue := rValue + 1.0;
    sStatus := 'Running';
ELSE
    sStatus := 'Stopped';
END_IF

// 定时器测试
tonTest(IN := bStart, PT := tTimer);

IF tonTest.Q THEN
    bStart := FALSE;
END_IF

END_PROGRAM
