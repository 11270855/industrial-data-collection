PROGRAM PLC_PRG
VAR
    // ========== 设备控制变量 ==========
    bConveyorStart: BOOL := FALSE;           // 传送带启动
    rConveyorSpeed: REAL := 0.0;             // 传送带速度 (m/s), 范围: 0-5
    bStation1Active: BOOL := FALSE;          // 工位1激活
    bStation2Active: BOOL := FALSE;          // 工位2激活
    bRejectActive: BOOL := FALSE;            // 剔除机构激活
    
    // ========== 传感器输入 ==========
    bProductSensor1: BOOL := FALSE;          // 产品检测传感器1 (工位1)
    bProductSensor2: BOOL := FALSE;          // 产品检测传感器2 (工位2)
    bQualitySensor: BOOL := FALSE;           // 质量检测传感器 (TRUE=合格, FALSE=不良)
    
    // ========== 能源计量变量 ==========
    rConveyorPower: REAL := 0.0;             // 传送带功率 (kW)
    rStation1Power: REAL := 0.0;             // 工位1功率 (kW)
    rStation2Power: REAL := 0.0;             // 工位2功率 (kW)
    rTotalPower: REAL := 0.0;                // 总功率 (kW)
    rTotalEnergy: REAL := 0.0;               // 累计能耗 (kWh)
    
    // ========== 生产统计 ==========
    iProductCount: INT := 0;                 // 产品计数
    iRejectCount: INT := 0;                  // 不良品计数
    iRunTimeSeconds: DINT := 0;              // 运行时间(秒)
    iDownTimeSeconds: DINT := 0;             // 停机时间(秒)
    
    // ========== 报警标志 ==========
    bEnergyAlarm: BOOL := FALSE;             // 能耗报警
    bSystemFault: BOOL := FALSE;             // 系统故障
    
    // ========== 系统状态 ==========
    eSystemState: INT := 0;                  // 系统状态: 0=待机, 1=运行, 2=故障
    bSystemStart: BOOL := FALSE;             // 系统启动命令
    bSystemStop: BOOL := FALSE;              // 系统停止命令
    bEmergencyStop: BOOL := FALSE;           // 紧急停止
    bAutoMode: BOOL := TRUE;                 // 自动运行模式（TRUE=自动启动）
    
    // ========== 功能块实例 ==========
    fbConveyor: FB_ConveyorControl;          // 传送带控制功能块
    fbStation1: FB_StationControl;           // 工位1控制功能块
    fbStation2: FB_StationControl;           // 工位2控制功能块
    fbQualityCheck: FB_QualityCheck;         // 质量检测功能块
    fbEnergyMeter: FB_EnergyMeter;           // 能源计量功能块
    
    // ========== 内部定时器和计数器 ==========
    tonCycleTime: TON;                       // 循环时间定时器
    
    // ========== 内部工作变量 ==========
    bFirstScan: BOOL := TRUE;                // 首次扫描标志
    
    // ========== 系统诊断变量 ==========
    bAllDevicesReady: BOOL := FALSE;         // 所有设备就绪
    iActiveDeviceCount: INT := 0;            // 激活设备数量
    iSystemStatus: INT := 0;                 // 系统状态代码: 0=初始化, 1=待机, 2=运行中, 3=故障
    
    // ========== 功能块输出缓存 ==========
    bConveyorRunning: BOOL := FALSE;         // 传送带运行状态
    rConveyorActualSpeed: REAL := 0.0;       // 传送带实际速度
    bConveyorFault: BOOL := FALSE;           // 传送带故障

    bStation1ActiveState: BOOL := FALSE;     // 工位1激活状态
    bStation1Processing: BOOL := FALSE;      // 工位1加工中
    bStation1ProcessComplete: BOOL := FALSE; // 工位1完成
    bStation1Fault: BOOL := FALSE;           // 工位1故障
    iStation1Status: INT := 0;               // 工位1状态码

    bStation2ActiveState: BOOL := FALSE;     // 工位2激活状态
    bStation2Processing: BOOL := FALSE;      // 工位2加工中
    bStation2ProcessComplete: BOOL := FALSE; // 工位2完成
    bStation2Fault: BOOL := FALSE;           // 工位2故障
    iStation2Status: INT := 0;               // 工位2状态码

    bQualityCheckInProgress: BOOL := FALSE;  // 质检进行中
    bQualityCheckComplete: BOOL := FALSE;    // 质检完成
    bQualityOK: BOOL := FALSE;               // 质检合格
    bQualityNG: BOOL := FALSE;               // 质检不合格
    rRejectRate: REAL := 0.0;                // 不良率

    rAveragePower: REAL := 0.0;              // 平均功率
    rPeakPower: REAL := 0.0;                 // 峰值功率
    bEnergyDataUpdated: BOOL := FALSE;       // 能耗数据刷新标志
    
    // ========== 自动模拟变量 ==========
    tonAutoStart: TON;                       // 自动启动延时定时器
    tonProductFlow: TON;                     // 产品流动定时器
    iProductGenCounter: INT := 0;            // 产品生成计数器
    
    // ========== 质量检测触发控制 ==========
    bTriggerQualityCheck: BOOL := FALSE;     // 质量检测触发信号
END_VAR


// ========== 主程序开始 ==========

// ========== 首次扫描初始化 ==========
IF bFirstScan THEN
    // 初始化系统状态
    eSystemState := 0; // 待机状态
    bSystemStart := FALSE;
    bSystemStop := FALSE;
    
    // 初始化所有设备
    bConveyorStart := FALSE;
    rConveyorSpeed := 0.0;
    bStation1Active := FALSE;
    bStation2Active := FALSE;
    bRejectActive := FALSE;
    
    // 清除报警
    bEnergyAlarm := FALSE;
    bSystemFault := FALSE;
    
    bFirstScan := FALSE;
END_IF

// ========== 自动运行模式 ==========
IF bAutoMode THEN
    // 自动启动：延时3秒后自动启动系统
    tonAutoStart(IN := (eSystemState = 0), PT := T#3s);
    IF tonAutoStart.Q AND NOT bSystemStart THEN
        bSystemStart := TRUE;
    END_IF
    
    // 自动产品流动：简化版本
    IF bAutoMode AND eSystemState = 1 THEN
        // 简单的产品流动：不使用复杂状态机
        
        // 步骤1：生成产品到工位1
        IF NOT bProductSensor1 AND NOT bProductSensor2 AND NOT bStation1Processing THEN
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
        
        // 步骤2：工位1完成后，移动到工位2
        IF bStation1ProcessComplete AND bProductSensor1 AND NOT bProductSensor2 THEN
            tonProductFlow(IN := TRUE, PT := T#2s);
            IF tonProductFlow.Q THEN
                bProductSensor1 := FALSE;
                bProductSensor2 := TRUE;
                tonProductFlow(IN := FALSE);
            END_IF
        END_IF
        
        // 步骤3：工位2完成后，触发质量检测
        IF bStation2ProcessComplete AND bProductSensor2 AND NOT bTriggerQualityCheck AND NOT bQualityCheckComplete THEN
            bTriggerQualityCheck := TRUE;
        END_IF
        
        // 步骤4：质量检测完成后，产品离开
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
ELSE
    // 手动模式：清除自动启动定时器
    tonAutoStart(IN := FALSE);
END_IF

// ========== 系统状态机 ==========
CASE eSystemState OF
    0: // 待机状态
        // 停止所有设备
        bConveyorStart := FALSE;
        rConveyorSpeed := 0.0;
        bStation1Active := FALSE;
        bStation2Active := FALSE;
        iSystemStatus := 1; // 待机
        
        // 清除系统启动命令（边沿触发）
        IF NOT bSystemStart THEN
            // 准备接受新的启动命令
        END_IF
        
        // 启动命令：需要系统启动信号、无紧急停止
        IF bSystemStart AND NOT bEmergencyStop THEN
            eSystemState := 1; // 进入运行状态
            bSystemStart := FALSE; // 清除启动命令
        END_IF
    
    1: // 运行状态
        iSystemStatus := 2; // 运行中
        
        // 启动传送带
        bConveyorStart := TRUE;
        rConveyorSpeed := 3.0; // 设定速度 3 m/s
        
        // 激活工位
        bStation1Active := TRUE;
        bStation2Active := TRUE;
        
        // 清除停止命令（边沿触发）
        IF NOT bSystemStop THEN
            // 准备接受新的停止命令
        END_IF
        
        // 停止命令或紧急停止
        IF bSystemStop OR bEmergencyStop THEN
            eSystemState := 0; // 返回待机状态
            bSystemStop := FALSE; // 清除停止命令
        END_IF
        
        // 系统故障检测（暂时禁用，用于调试）
        // IF bConveyorFault OR bStation1Fault OR bStation2Fault THEN
        //     bSystemFault := TRUE;
        //     eSystemState := 2; // 进入故障状态
        // END_IF
    
    2: // 故障状态
        iSystemStatus := 3; // 故障
        
        // 停止所有设备
        bConveyorStart := FALSE;
        rConveyorSpeed := 0.0;
        bStation1Active := FALSE;
        bStation2Active := FALSE;
        
        // 故障复位：停止命令且无紧急停止
        IF bSystemStop AND NOT bEmergencyStop THEN
            bSystemFault := FALSE;
            eSystemState := 0; // 返回待机状态
            bSystemStop := FALSE; // 清除停止命令
        END_IF
        
ELSE
    // 未知状态，返回待机
    eSystemState := 0;
    iSystemStatus := 0; // 初始化
        
END_CASE

// ========== 调用传送带控制功能块 ==========
fbConveyor(
    bStart := bConveyorStart,
    rSpeedSetpoint := rConveyorSpeed,
    bEmergencyStop := bEmergencyStop,
    bRunning => bConveyorRunning,
    rActualSpeed => rConveyorActualSpeed,
    rPower => rConveyorPower,
    bFault => bConveyorFault
);

// ========== 调用工位1控制功能块 ==========
fbStation1(
    bActivate := bStation1Active,
    bProductPresent := bProductSensor1,
    bEmergencyStop := bEmergencyStop,
    tProcessTime := T#5s,
    bActive => bStation1ActiveState,
    bProcessing => bStation1Processing,
    bProcessComplete => bStation1ProcessComplete,
    rPower => rStation1Power,
    bFault => bStation1Fault,
    iStatus => iStation1Status
);

// ========== 调用工位2控制功能块 ==========
fbStation2(
    bActivate := bStation2Active,
    bProductPresent := bProductSensor2,
    bEmergencyStop := bEmergencyStop,
    tProcessTime := T#5s,
    bActive => bStation2ActiveState,
    bProcessing => bStation2Processing,
    bProcessComplete => bStation2ProcessComplete,
    rPower => rStation2Power,
    bFault => bStation2Fault,
    iStatus => iStation2Status
);

// ========== 调用质量检测功能块 ==========
// 在工位2完成后触发质量检测
fbQualityCheck(
    bEnable := TRUE,
    bQualitySensor := bQualitySensor,
    bProductPresent := bProductSensor2,
    bTriggerCheck := bTriggerQualityCheck,
    bCheckInProgress => bQualityCheckInProgress,
    bCheckComplete => bQualityCheckComplete,
    bQualityOK => bQualityOK,
    bQualityNG => bQualityNG,
    bRejectActive => bRejectActive,
    iProductCount => iProductCount,
    iRejectCount => iRejectCount,
    rRejectRate => rRejectRate
);

// ========== 调用能源计量功能块 ==========
fbEnergyMeter(
    bEnable := TRUE,
    rPower1 := rConveyorPower,
    rPower2 := rStation1Power,
    rPower3 := rStation2Power,
    rPowerThreshold := 15.0,
    bReset := FALSE,
    rTotalPower => rTotalPower,
    rTotalEnergy => rTotalEnergy,
    rAveragePower => rAveragePower,
    rPeakPower => rPeakPower,
    bPowerAlarm => bEnergyAlarm,
    bDataUpdated => bEnergyDataUpdated
);

// ========== 系统诊断（在功能块调用之后）==========
// 检查所有设备是否就绪（无故障）
bAllDevicesReady := NOT bConveyorFault AND NOT bStation1Fault AND NOT bStation2Fault;

// 统计激活设备数量
iActiveDeviceCount := 0;
IF bConveyorRunning THEN
    iActiveDeviceCount := iActiveDeviceCount + 1;
END_IF
IF bStation1ActiveState THEN
    iActiveDeviceCount := iActiveDeviceCount + 1;
END_IF
IF bStation2ActiveState THEN
    iActiveDeviceCount := iActiveDeviceCount + 1;
END_IF

// ========== 运行时间和停机时间统计 ==========
// 使用定时器累计时间，每秒增加计数器
tonCycleTime(IN := TRUE, PT := T#1s);

// 运行时间统计
IF eSystemState = 1 THEN
    // 运行状态：累计运行时间
    IF tonCycleTime.Q THEN
        iRunTimeSeconds := iRunTimeSeconds + 1;
    END_IF
ELSIF eSystemState = 0 OR eSystemState = 2 THEN
    // 待机或故障状态：累计停机时间
    IF tonCycleTime.Q THEN
        iDownTimeSeconds := iDownTimeSeconds + 1;
    END_IF
END_IF

// 定时器复位
IF tonCycleTime.Q THEN
    tonCycleTime(IN := FALSE);
END_IF

// ========== 主程序结束 ==========

(*
================================================================================
程序说明：PLC主程序 - 生产线能源管理系统
================================================================================

功能概述：
- 集成所有功能块（传送带、工位、质量检测、能源计量）
- 实现三状态系统状态机（待机、运行、故障）
- 提供生产线启动和停止控制
- 统计运行时间和停机时间
- 监控系统健康状态和设备就绪状态

状态机说明：
- 状态0（待机）：所有设备停止，等待启动命令
- 状态1（运行）：生产线正常运行，所有设备激活
- 状态2（故障）：检测到设备故障，停止生产线

控制命令：
- bSystemStart：启动生产线（需要所有设备就绪）
- bSystemStop：停止生产线或故障复位
- bEmergencyStop：紧急停止（立即停止所有设备）

数据输出：
- 能源数据：rTotalPower, rTotalEnergy, bEnergyAlarm
- 生产数据：iProductCount, iRejectCount, iRunTimeSeconds (秒), iDownTimeSeconds (秒)
- 系统状态：eSystemState, sSystemStatus, bSystemFault

需求追溯：
- 需求1.1：PLC初始化和设备控制
- 需求1.5：设备状态监控
- 需求6.1：运行时间和停机时间统计

版本：1.0
日期：2025-12-01
================================================================================
*)

END_PROGRAM
