FUNCTION_BLOCK FB_ConveyorControl
VAR_INPUT
    bStart: BOOL;                    // 启动命令
    rSpeedSetpoint: REAL;            // 速度设定值 (m/s)
    bEmergencyStop: BOOL;            // 紧急停止
END_VAR

VAR_OUTPUT
    bRunning: BOOL;                  // 运行状态
    rActualSpeed: REAL;              // 实际速度 (m/s)
    rPower: REAL;                    // 功率消耗 (kW)
    bFault: BOOL;                    // 故障标志
END_VAR

VAR
    // 内部状态变量
    eState: INT := 0;                // 状态: 0=停止, 1=启动中, 2=运行, 3=停止中
    rCurrentSpeed: REAL := 0.0;      // 当前速度
    rTargetSpeed: REAL := 0.0;       // 目标速度
    
    // 加减速控制
    rAcceleration: REAL := 0.5;      // 加速度 (m/s²)
    rDeceleration: REAL := 0.8;      // 减速度 (m/s²)
    tScanTime: TIME := T#100ms;      // 扫描时间
    rScanTimeSec: REAL := 0.1;       // 扫描时间(秒)
    
    // 功率计算参数
    rBasePower: REAL := 0.5;         // 基础功率 (kW)
    rSpeedCoeff: REAL := 0.3;        // 速度系数 (kW/(m/s))
    
    // 速度限制
    rMinSpeed: REAL := 0.0;          // 最小速度
    rMaxSpeed: REAL := 5.0;          // 最大速度
    
    // 定时器
    tonStartDelay: TON;              // 启动延时
    tonStopDelay: TON;               // 停止延时
    
    // 故障检测
    bOverspeed: BOOL := FALSE;       // 超速故障
END_VAR

// ========== 主控制逻辑 ==========

// 紧急停止处理
IF bEmergencyStop THEN
    eState := 0;
    rCurrentSpeed := 0.0;
    rTargetSpeed := 0.0;
    bRunning := FALSE;
    bFault := TRUE;
    RETURN;
END_IF

// 速度设定值限制
rTargetSpeed := LIMIT(rMinSpeed, rSpeedSetpoint, rMaxSpeed);

// 状态机
CASE eState OF
    0: // 停止状态
        rCurrentSpeed := 0.0;
        bRunning := FALSE;
        bFault := FALSE;
        
        IF bStart AND NOT bEmergencyStop THEN
            eState := 1; // 进入启动状态
            tonStartDelay(IN := FALSE); // 复位定时器
        END_IF
    
    1: // 启动中
        tonStartDelay(IN := TRUE, PT := T#500ms);
        
        IF tonStartDelay.Q THEN
            eState := 2; // 进入运行状态
            tonStartDelay(IN := FALSE);
        END_IF
        
        IF NOT bStart THEN
            eState := 0; // 返回停止状态
        END_IF
    
    2: // 运行状态
        bRunning := TRUE;
        
        // 速度控制 - 加速
        IF rCurrentSpeed < rTargetSpeed THEN
            rCurrentSpeed := rCurrentSpeed + (rAcceleration * rScanTimeSec);
            IF rCurrentSpeed > rTargetSpeed THEN
                rCurrentSpeed := rTargetSpeed;
            END_IF
        END_IF
        
        // 速度控制 - 减速
        IF rCurrentSpeed > rTargetSpeed THEN
            rCurrentSpeed := rCurrentSpeed - (rDeceleration * rScanTimeSec);
            IF rCurrentSpeed < rTargetSpeed THEN
                rCurrentSpeed := rTargetSpeed;
            END_IF
        END_IF
        
        // 超速检测
        IF rCurrentSpeed > rMaxSpeed THEN
            bOverspeed := TRUE;
            bFault := TRUE;
            eState := 3; // 进入停止状态
        END_IF
        
        // 停止命令
        IF NOT bStart THEN
            eState := 3; // 进入停止中状态
        END_IF
    
    3: // 停止中
        bRunning := FALSE;
        
        // 减速停止
        IF rCurrentSpeed > 0.0 THEN
            rCurrentSpeed := rCurrentSpeed - (rDeceleration * rScanTimeSec);
            IF rCurrentSpeed < 0.0 THEN
                rCurrentSpeed := 0.0;
            END_IF
        ELSE
            eState := 0; // 返回停止状态
            bOverspeed := FALSE;
        END_IF
        
END_CASE

// ========== 功率计算 ==========
// 功率 = 基础功率 + 速度系数 * 速度
IF bRunning AND rCurrentSpeed > 0.0 THEN
    rPower := rBasePower + (rSpeedCoeff * rCurrentSpeed);
ELSE
    rPower := 0.0;
END_IF

// ========== 输出更新 ==========
rActualSpeed := rCurrentSpeed;

END_FUNCTION_BLOCK
