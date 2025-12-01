FUNCTION_BLOCK FB_StationControl
VAR_INPUT
    bActivate: BOOL;                 // 工位激活命令
    bProductPresent: BOOL;           // 产品到位传感器
    bEmergencyStop: BOOL;            // 紧急停止
    tProcessTime: TIME := T#5s;      // 工艺加工时间
END_VAR

VAR_OUTPUT
    bActive: BOOL;                   // 工位激活状态
    bProcessing: BOOL;               // 正在加工
    bProcessComplete: BOOL;          // 加工完成
    rPower: REAL;                    // 功率消耗 (kW)
    bFault: BOOL;                    // 故障标志
    sStatus: STRING := 'Standby';    // 状态文本
END_VAR

VAR
    // 内部状态变量
    eState: INT := 0;                // 状态: 0=待机, 1=等待产品, 2=加工中, 3=完成, 4=故障
    
    // 功率参数
    rActivePower: REAL := 5.0;       // 运行功率 (kW)
    rStandbyPower: REAL := 0.2;      // 待机功率 (kW)
    
    // 定时器
    tonProcessTimer: TON;            // 加工时间定时器
    tonWaitTimeout: TON;             // 等待超时定时器
    tonCompleteDelay: TON;           // 完成延时定时器
    
    // 超时设置
    tWaitTimeout: TIME := T#30s;     // 等待产品超时时间
    tCompleteDelay: TIME := T#1s;    // 完成信号保持时间
    
    // 内部标志
    bProductDetected: BOOL := FALSE; // 产品检测标志
    bProcessStarted: BOOL := FALSE;  // 加工开始标志
    
    // 边沿检测
    bProductPresentOld: BOOL := FALSE;
    bProductArrived: BOOL := FALSE;  // 产品到达上升沿
END_VAR

// ========== 主控制逻辑 ==========

// 紧急停止处理
IF bEmergencyStop THEN
    eState := 4; // 进入故障状态
    bProcessing := FALSE;
    bProcessComplete := FALSE;
    bFault := TRUE;
    sStatus := 'Emergency Stop';
    tonProcessTimer(IN := FALSE);
    tonWaitTimeout(IN := FALSE);
    RETURN;
END_IF

// 产品到达边沿检测
bProductArrived := bProductPresent AND NOT bProductPresentOld;
bProductPresentOld := bProductPresent;

// 状态机
CASE eState OF
    0: // 待机状态
        bActive := FALSE;
        bProcessing := FALSE;
        bProcessComplete := FALSE;
        bFault := FALSE;
        sStatus := 'Standby';
        bProcessStarted := FALSE;
        
        // 复位定时器
        tonProcessTimer(IN := FALSE);
        tonWaitTimeout(IN := FALSE);
        tonCompleteDelay(IN := FALSE);
        
        IF bActivate AND NOT bEmergencyStop THEN
            eState := 1; // 进入等待产品状态
        END_IF
    
    1: // 等待产品状态
        bActive := TRUE;
        bProcessing := FALSE;
        bProcessComplete := FALSE;
        sStatus := 'Waiting for Product';
        
        // 启动等待超时定时器
        tonWaitTimeout(IN := TRUE, PT := tWaitTimeout);
        
        // 检测产品到达
        IF bProductArrived OR (bProductPresent AND NOT bProductDetected) THEN
            bProductDetected := TRUE;
            eState := 2; // 进入加工状态
            tonWaitTimeout(IN := FALSE);
        END_IF
        
        // 等待超时
        IF tonWaitTimeout.Q THEN
            eState := 4; // 进入故障状态
            bFault := TRUE;
            sStatus := 'Wait Timeout';
        END_IF
        
        // 取消激活
        IF NOT bActivate THEN
            eState := 0; // 返回待机状态
        END_IF
    
    2: // 加工中状态
        bActive := TRUE;
        bProcessing := TRUE;
        bProcessComplete := FALSE;
        sStatus := 'Processing';
        
        // 启动加工定时器
        IF NOT bProcessStarted THEN
            tonProcessTimer(IN := FALSE); // 复位
            bProcessStarted := TRUE;
        END_IF
        tonProcessTimer(IN := TRUE, PT := tProcessTime);
        
        // 加工完成
        IF tonProcessTimer.Q THEN
            eState := 3; // 进入完成状态
            tonProcessTimer(IN := FALSE);
        END_IF
        
        // 产品移走检测（异常情况）
        IF NOT bProductPresent THEN
            eState := 4; // 进入故障状态
            bFault := TRUE;
            sStatus := 'Product Lost';
        END_IF
        
        // 紧急取消
        IF NOT bActivate THEN
            eState := 0; // 返回待机状态
        END_IF
    
    3: // 完成状态
        bActive := TRUE;
        bProcessing := FALSE;
        bProcessComplete := TRUE;
        sStatus := 'Complete';
        
        // 完成信号保持
        tonCompleteDelay(IN := TRUE, PT := tCompleteDelay);
        
        // 等待产品移走或保持时间结束
        IF NOT bProductPresent OR tonCompleteDelay.Q THEN
            bProductDetected := FALSE;
            tonCompleteDelay(IN := FALSE);
            
            // 如果仍然激活，返回等待状态；否则返回待机
            IF bActivate THEN
                eState := 1; // 返回等待产品状态
            ELSE
                eState := 0; // 返回待机状态
            END_IF
        END_IF
    
    4: // 故障状态
        bActive := FALSE;
        bProcessing := FALSE;
        bProcessComplete := FALSE;
        bFault := TRUE;
        
        // 复位定时器
        tonProcessTimer(IN := FALSE);
        tonWaitTimeout(IN := FALSE);
        tonCompleteDelay(IN := FALSE);
        
        // 故障复位：取消激活且无紧急停止
        IF NOT bActivate AND NOT bEmergencyStop THEN
            eState := 0; // 返回待机状态
            bProductDetected := FALSE;
        END_IF
        
END_CASE

// ========== 功率计算 ==========
// 运行时满功率，待机时低功率
IF bProcessing THEN
    rPower := rActivePower;
ELSIF bActive THEN
    rPower := rStandbyPower;
ELSE
    rPower := 0.0;
END_IF

END_FUNCTION_BLOCK
