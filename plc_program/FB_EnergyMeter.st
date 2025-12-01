FUNCTION_BLOCK FB_EnergyMeter
VAR_INPUT
    bEnable: BOOL;                   // 计量使能
    rPower1: REAL;                   // 设备1功率 (kW)
    rPower2: REAL;                   // 设备2功率 (kW)
    rPower3: REAL;                   // 设备3功率 (kW)
    rPowerThreshold: REAL := 15.0;   // 功率报警阈值 (kW)
    bReset: BOOL;                    // 复位累计能耗
END_VAR

VAR_OUTPUT
    rTotalPower: REAL;               // 总功率 (kW)
    rTotalEnergy: REAL;              // 累计能耗 (kWh)
    rAveragePower: REAL;             // 平均功率 (kW)
    rPeakPower: REAL;                // 峰值功率 (kW)
    bPowerAlarm: BOOL;               // 功率报警
    bDataUpdated: BOOL;              // 数据更新标志
END_VAR

VAR
    // 内部计量变量
    rAccumulatedEnergy: REAL := 0.0; // 累计能耗内部值
    rPowerSum: REAL := 0.0;          // 功率累加和
    iPowerSamples: DINT := 0;        // 功率采样次数
    rPeakPowerInternal: REAL := 0.0; // 峰值功率内部值
    
    // 定时器
    tonUpdateCycle: TON;             // 更新周期定时器
    tUpdateCycle: TIME := T#1s;      // 更新周期（1秒）
    
    // 时间计算
    tLastUpdate: TIME;               // 上次更新时间
    tCurrentTime: TIME;              // 当前时间
    tElapsedTime: TIME;              // 经过时间
    rElapsedHours: REAL;             // 经过时间（小时）
    
    // 扫描时间
    tScanTime: TIME := T#100ms;      // 系统扫描时间
    rScanTimeHours: REAL := 0.0000277778; // 扫描时间（小时）= 100ms / 3600000ms
    
    // 内部标志
    bFirstScan: BOOL := TRUE;        // 首次扫描标志
    bResetOld: BOOL := FALSE;        // 复位信号旧值
    bResetRising: BOOL := FALSE;     // 复位上升沿
    
    // 报警相关
    iAlarmCounter: INT := 0;         // 报警计数器
    iAlarmThreshold: INT := 3;       // 连续超阈值次数才报警
    
    // 数据更新标志
    bUpdateFlag: BOOL := FALSE;      // 内部更新标志
END_VAR

// ========== 主控制逻辑 ==========

// 复位边沿检测
bResetRising := bReset AND NOT bResetOld;
bResetOld := bReset;

// 复位处理
IF bResetRising THEN
    rAccumulatedEnergy := 0.0;
    rPowerSum := 0.0;
    iPowerSamples := 0;
    rPeakPowerInternal := 0.0;
    bPowerAlarm := FALSE;
    iAlarmCounter := 0;
    bFirstScan := TRUE;
END_IF

// 如果未使能，清零输出
IF NOT bEnable THEN
    rTotalPower := 0.0;
    rTotalEnergy := 0.0;
    rAveragePower := 0.0;
    rPeakPower := 0.0;
    bPowerAlarm := FALSE;
    bDataUpdated := FALSE;
    bFirstScan := TRUE;
    RETURN;
END_IF

// ========== 实时功率计算 ==========
// 累加所有设备功率
rTotalPower := rPower1 + rPower2 + rPower3;

// 确保功率为非负值
IF rTotalPower < 0.0 THEN
    rTotalPower := 0.0;
END_IF

// ========== 能耗累计计算 ==========
// 能耗 += 功率 * 时间间隔
// 使用扫描时间作为时间间隔
IF NOT bFirstScan THEN
    // 能耗累计：kWh = kW * hours
    rAccumulatedEnergy := rAccumulatedEnergy + (rTotalPower * rScanTimeHours);
END_IF

// ========== 统计数据计算 ==========
// 功率累加（用于平均值计算）
rPowerSum := rPowerSum + rTotalPower;
iPowerSamples := iPowerSamples + 1;

// 平均功率计算
IF iPowerSamples > 0 THEN
    rAveragePower := rPowerSum / DINT_TO_REAL(iPowerSamples);
ELSE
    rAveragePower := 0.0;
END_IF

// 峰值功率更新
IF rTotalPower > rPeakPowerInternal THEN
    rPeakPowerInternal := rTotalPower;
END_IF

// ========== 异常用电检测 ==========
// 功率超过阈值时设置报警标志
// 使用连续超阈值判定，避免瞬时波动误报
IF rTotalPower > rPowerThreshold THEN
    iAlarmCounter := iAlarmCounter + 1;
    IF iAlarmCounter >= iAlarmThreshold THEN
        bPowerAlarm := TRUE;
    END_IF
ELSE
    iAlarmCounter := 0;
    // 功率恢复正常后，报警需要手动复位或自动清除
    IF rTotalPower < (rPowerThreshold * 0.9) THEN
        bPowerAlarm := FALSE;
    END_IF
END_IF

// ========== 数据更新周期控制 ==========
// 每1秒更新一次数据标志
tonUpdateCycle(IN := TRUE, PT := tUpdateCycle);

IF tonUpdateCycle.Q THEN
    tonUpdateCycle(IN := FALSE); // 复位定时器
    bUpdateFlag := TRUE;
ELSE
    bUpdateFlag := FALSE;
END_IF

// ========== 输出更新 ==========
rTotalEnergy := rAccumulatedEnergy;
rPeakPower := rPeakPowerInternal;
bDataUpdated := bUpdateFlag;

// 清除首次扫描标志
IF bFirstScan THEN
    bFirstScan := FALSE;
END_IF

END_FUNCTION_BLOCK
