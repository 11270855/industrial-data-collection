FUNCTION_BLOCK FB_QualityCheck
VAR_INPUT
    bEnable: BOOL;                   // 质检使能
    bQualitySensor: BOOL;            // 质量传感器信号 (TRUE=合格, FALSE=不良)
    bProductPresent: BOOL;           // 产品到位传感器
    bTriggerCheck: BOOL;             // 触发检测命令
END_VAR

VAR_OUTPUT
    bCheckInProgress: BOOL;          // 检测进行中
    bCheckComplete: BOOL;            // 检测完成
    bQualityOK: BOOL;                // 质量合格
    bQualityNG: BOOL;                // 质量不良
    bRejectActive: BOOL;             // 剔除机构激活
    iProductCount: INT;              // 产品总数
    iRejectCount: INT;               // 不良品数量
    rRejectRate: REAL;               // 不良率 (%)
END_VAR

VAR
    // 内部状态变量
    eState: INT := 0;                // 状态: 0=待机, 1=检测中, 2=合格, 3=不良, 4=剔除中
    
    // 定时器
    tonCheckTimer: TON;              // 检测时间定时器
    tonRejectTimer: TON;             // 剔除动作定时器
    
    // 时间参数
    tCheckTime: TIME := T#1s;        // 质量检测时间
    tRejectTime: TIME := T#2s;       // 剔除机构动作时间
    
    // 内部计数
    iInternalProductCount: INT := 0; // 内部产品计数
    iInternalRejectCount: INT := 0;  // 内部不良品计数
    
    // 边沿检测
    bTriggerCheckOld: BOOL := FALSE;
    bTriggerCheckRising: BOOL := FALSE;
    
    // 检测结果
    bLastCheckResult: BOOL := FALSE; // 上次检测结果
    iQualitySampleCount: INT := 0;   // 质量采样计数
    iQualityOKSamples: INT := 0;     // 合格采样数
    
    // 采样参数
    iSamplesRequired: INT := 5;      // 需要的采样次数
    iSampleInterval: INT := 0;       // 采样间隔计数器
    iSampleIntervalMax: INT := 10;   // 采样间隔最大值（扫描周期数）
END_VAR

// ========== 主控制逻辑 ==========

// 触发检测边沿检测
bTriggerCheckRising := bTriggerCheck AND NOT bTriggerCheckOld;
bTriggerCheckOld := bTriggerCheck;

// 状态机
CASE eState OF
    0: // 待机状态
        bCheckInProgress := FALSE;
        bCheckComplete := FALSE;
        bQualityOK := FALSE;
        bQualityNG := FALSE;
        bRejectActive := FALSE;
        
        // 复位定时器和采样计数
        tonCheckTimer(IN := FALSE);
        tonRejectTimer(IN := FALSE);
        iQualitySampleCount := 0;
        iQualityOKSamples := 0;
        iSampleInterval := 0;
        
        // 触发检测
        IF bEnable AND bTriggerCheckRising AND bProductPresent THEN
            eState := 1; // 进入检测状态
        END_IF
    
    1: // 检测中状态
        bCheckInProgress := TRUE;
        bCheckComplete := FALSE;
        
        // 启动检测定时器
        tonCheckTimer(IN := TRUE, PT := tCheckTime);
        
        // 采样质量传感器信号
        iSampleInterval := iSampleInterval + 1;
        IF iSampleInterval >= iSampleIntervalMax THEN
            iSampleInterval := 0;
            
            // 记录采样
            IF iQualitySampleCount < iSamplesRequired THEN
                iQualitySampleCount := iQualitySampleCount + 1;
                IF bQualitySensor THEN
                    iQualityOKSamples := iQualityOKSamples + 1;
                END_IF
            END_IF
        END_IF
        
        // 检测时间到
        IF tonCheckTimer.Q THEN
            tonCheckTimer(IN := FALSE);
            
            // 判定结果：多数采样为合格则判定为合格
            IF iQualityOKSamples > (iSamplesRequired / 2) THEN
                bLastCheckResult := TRUE;
                eState := 2; // 进入合格状态
            ELSE
                bLastCheckResult := FALSE;
                eState := 3; // 进入不良状态
            END_IF
        END_IF
        
        // 产品移走（异常情况）
        IF NOT bProductPresent THEN
            eState := 0; // 返回待机状态
        END_IF
    
    2: // 合格状态
        bCheckInProgress := FALSE;
        bCheckComplete := TRUE;
        bQualityOK := TRUE;
        bQualityNG := FALSE;
        bRejectActive := FALSE;
        
        // 更新产品计数
        iInternalProductCount := iInternalProductCount + 1;
        
        // 等待产品移走或触发复位
        IF NOT bProductPresent OR NOT bTriggerCheck THEN
            eState := 0; // 返回待机状态
        END_IF
    
    3: // 不良状态
        bCheckInProgress := FALSE;
        bCheckComplete := TRUE;
        bQualityOK := FALSE;
        bQualityNG := TRUE;
        
        // 更新计数
        iInternalProductCount := iInternalProductCount + 1;
        iInternalRejectCount := iInternalRejectCount + 1;
        
        // 进入剔除状态
        eState := 4;
    
    4: // 剔除中状态
        bCheckInProgress := FALSE;
        bCheckComplete := TRUE;
        bQualityOK := FALSE;
        bQualityNG := TRUE;
        bRejectActive := TRUE;
        
        // 启动剔除定时器
        tonRejectTimer(IN := TRUE, PT := tRejectTime);
        
        // 剔除动作完成
        IF tonRejectTimer.Q THEN
            tonRejectTimer(IN := FALSE);
            bRejectActive := FALSE;
            
            // 等待产品移走
            IF NOT bProductPresent THEN
                eState := 0; // 返回待机状态
            END_IF
        END_IF
        
END_CASE

// ========== 输出更新 ==========
iProductCount := iInternalProductCount;
iRejectCount := iInternalRejectCount;

// 计算不良率
IF iInternalProductCount > 0 THEN
    rRejectRate := (INT_TO_REAL(iInternalRejectCount) / INT_TO_REAL(iInternalProductCount)) * 100.0;
ELSE
    rRejectRate := 0.0;
END_IF

END_FUNCTION_BLOCK
