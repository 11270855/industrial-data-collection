// 简化版产品流动逻辑 - 直接替换PLC_PRG.st中的产品流动部分

// 自动产品流动：简化版本，不使用复杂状态机
IF bAutoMode AND eSystemState = 1 THEN
    // 简单的产品流动：直接模拟产品在两个工位之间流动
    
    // 工位1：如果没有产品且工位1空闲，生成新产品
    IF NOT bProductSensor1 AND NOT bStation1Processing THEN
        tonProductFlow(IN := TRUE, PT := T#2s);
        IF tonProductFlow.Q THEN
            bProductSensor1 := TRUE;
            iProductGenCounter := iProductGenCounter + 1;
            // 设置质量（90%合格）
            IF iProductGenCounter MOD 10 = 0 THEN
                bQualitySensor := FALSE;
            ELSE
                bQualitySensor := TRUE;
            END_IF
            tonProductFlow(IN := FALSE);
        END_IF
    END_IF
    
    // 工位1完成后，移动到工位2
    IF bStation1ProcessComplete AND bProductSensor1 AND NOT bProductSensor2 THEN
        tonProductFlow(IN := TRUE, PT := T#2s);
        IF tonProductFlow.Q THEN
            bProductSensor1 := FALSE;
            bProductSensor2 := TRUE;
            tonProductFlow(IN := FALSE);
        END_IF
    END_IF
    
    // 工位2完成后，触发质量检测
    IF bStation2ProcessComplete AND bProductSensor2 AND NOT bTriggerQualityCheck THEN
        bTriggerQualityCheck := TRUE;
    END_IF
    
    // 质量检测完成后，产品离开
    IF bQualityCheckComplete AND bProductSensor2 THEN
        tonProductFlow(IN := TRUE, PT := T#2s);
        IF tonProductFlow.Q THEN
            bProductSensor2 := FALSE;
            bTriggerQualityCheck := FALSE;
            tonProductFlow(IN := FALSE);
        END_IF
    END_IF
    
ELSE
    // 系统停止时复位
    bProductSensor1 := FALSE;
    bProductSensor2 := FALSE;
    bTriggerQualityCheck := FALSE;
    tonProductFlow(IN := FALSE);
END_IF
