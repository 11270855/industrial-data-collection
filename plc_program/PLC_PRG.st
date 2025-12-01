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
    tRunTime: TIME := T#0s;                  // 运行时间
    tDownTime: TIME := T#0s;                 // 停机时间
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
    
    // ========== 功能块实例 ==========
    fbConveyor: FB_ConveyorControl;          // 传送带控制功能块
    fbStation1: FB_StationControl;           // 工位1控制功能块
    fbStation2: FB_StationControl;           // 工位2控制功能块
    fbQualityCheck: FB_QualityCheck;         // 质量检测功能块
    fbEnergyMeter: FB_EnergyMeter;           // 能源计量功能块
    
    // ========== 内部定时器和计数器 ==========
    tonRunTime: TON;                         // 运行时间定时器
    tonDownTime: TON;                        // 停机时间定时器
    tonCycleTime: TON;                       // 循环时间定时器
    
    // ========== 内部工作变量 ==========
    bFirstScan: BOOL := TRUE;                // 首次扫描标志
    tCycleTime: TIME := T#100ms;             // 循环时间
    tLastCycle: TIME;                        // 上次循环时间
    
    // ========== 系统诊断变量 ==========
    bAllDevicesReady: BOOL := FALSE;         // 所有设备就绪
    iActiveDeviceCount: INT := 0;            // 激活设备数量
    sSystemStatus: STRING := 'Initializing'; // 系统状态文本
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

// ========== 系统诊断 ==========
// 检查所有设备是否就绪（无故障）
bAllDevicesReady := NOT fbConveyor.bFault AND NOT fbStation1.bFault AND NOT fbStation2.bFault;

// 统计激活设备数量
iActiveDeviceCount := 0;
IF fbConveyor.bRunning THEN
    iActiveDeviceCount := iActiveDeviceCount + 1;
END_IF
IF fbStation1.bActive THEN
    iActiveDeviceCount := iActiveDeviceCount + 1;
END_IF
IF fbStation2.bActive THEN
    iActiveDeviceCount := iActiveDeviceCount + 1;
END_IF

// ========== 系统状态机 ==========
CASE eSystemState OF
    0: // 待机状态
        // 停止所有设备
        bConveyorStart := FALSE;
        rConveyorSpeed := 0.0;
        bStation1Active := FALSE;
        bStation2Active := FALSE;
        sSystemStatus := 'Standby';
        
        // 清除系统启动命令（边沿触发）
        IF NOT bSystemStart THEN
            // 准备接受新的启动命令
        END_IF
        
        // 启动命令：需要系统启动信号、无紧急停止、所有设备就绪
        IF bSystemStart AND NOT bEmergencyStop AND bAllDevicesReady THEN
            eSystemState := 1; // 进入运行状态
            bSystemStart := FALSE; // 清除启动命令
        END_IF
    
    1: // 运行状态
        sSystemStatus := 'Running';
        
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
        
        // 系统故障检测
        IF fbConveyor.bFault OR fbStation1.bFault OR fbStation2.bFault THEN
            bSystemFault := TRUE;
            eSystemState := 2; // 进入故障状态
        END_IF
    
    2: // 故障状态
        sSystemStatus := 'Fault';
        
        // 停止所有设备
        bConveyorStart := FALSE;
        rConveyorSpeed := 0.0;
        bStation1Active := FALSE;
        bStation2Active := FALSE;
        
        // 故障复位：停止命令且无紧急停止且所有设备无故障
        IF bSystemStop AND NOT bEmergencyStop THEN
            IF bAllDevicesReady THEN
                bSystemFault := FALSE;
                eSystemState := 0; // 返回待机状态
                bSystemStop := FALSE; // 清除停止命令
            END_IF
        END_IF
        
ELSE
    // 未知状态，返回待机
    eSystemState := 0;
    sSystemStatus := 'Unknown State';
        
END_CASE

// ========== 调用传送带控制功能块 ==========
fbConveyor(
    bStart := bConveyorStart,
    rSpeedSetpoint := rConveyorSpeed,
    bEmergencyStop := bEmergencyStop,
    bRunning => ,
    rActualSpeed => ,
    rPower => rConveyorPower,
    bFault =>
);

// ========== 调用工位1控制功能块 ==========
fbStation1(
    bActivate := bStation1Active,
    bProductPresent := bProductSensor1,
    bEmergencyStop := bEmergencyStop,
    tProcessTime := T#5s,
    bActive => ,
    bProcessing => ,
    bProcessComplete => ,
    rPower => rStation1Power,
    bFault => ,
    sStatus =>
);

// ========== 调用工位2控制功能块 ==========
fbStation2(
    bActivate := bStation2Active,
    bProductPresent := bProductSensor2,
    bEmergencyStop := bEmergencyStop,
    tProcessTime := T#5s,
    bActive => ,
    bProcessing => ,
    bProcessComplete => ,
    rPower => rStation2Power,
    bFault => ,
    sStatus =>
);

// ========== 调用质量检测功能块 ==========
// 在工位2完成后触发质量检测
fbQualityCheck(
    bEnable := TRUE,
    bQualitySensor := bQualitySensor,
    bProductPresent := bProductSensor2,
    bTriggerCheck := fbStation2.bProcessComplete,
    bCheckInProgress => ,
    bCheckComplete => ,
    bQualityOK => ,
    bQualityNG => ,
    bRejectActive => bRejectActive,
    iProductCount => iProductCount,
    iRejectCount => iRejectCount,
    rRejectRate =>
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
    rAveragePower => ,
    rPeakPower => ,
    bPowerAlarm => bEnergyAlarm,
    bDataUpdated =>
);

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

// 更新TIME类型变量（用于显示）
tRunTime := DINT_TO_TIME(iRunTimeSeconds * 1000); // 转换为毫秒
tDownTime := DINT_TO_TIME(iDownTimeSeconds * 1000);

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
- 生产数据：iProductCount, iRejectCount, iRunTimeSeconds, iDownTimeSeconds
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
