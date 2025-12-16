PROGRAM PLC_PRG_MINIMAL
VAR
    // 最小化测试变量
    bTest: BOOL := FALSE;
    iTest: INT := 0;
    rTest: REAL := 0.0;
END_VAR

// 最简单的逻辑
IF bTest THEN
    iTest := iTest + 1;
    rTest := rTest + 1.0;
END_IF

END_PROGRAM
