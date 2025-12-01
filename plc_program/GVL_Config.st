// 全局变量列表 - 配置参数
VAR_GLOBAL CONSTANT
    // ========== 传送带配置 ==========
    CONVEYOR_MIN_SPEED: REAL := 0.0;         // 最小速度 (m/s)
    CONVEYOR_MAX_SPEED: REAL := 5.0;         // 最大速度 (m/s)
    CONVEYOR_BASE_POWER: REAL := 0.5;        // 基础功率 (kW)
    CONVEYOR_SPEED_COEFF: REAL := 0.3;       // 速度系数 (kW/(m/s))
    
    // ========== 工位配置 ==========
    STATION_ACTIVE_POWER: REAL := 5.0;       // 工位运行功率 (kW)
    STATION_STANDBY_POWER: REAL := 0.2;      // 工位待机功率 (kW)
    STATION_PROCESS_TIME: TIME := T#5s;      // 工位加工时间
    
    // ========== 质量检测配置 ==========
    QUALITY_CHECK_TIME: TIME := T#1s;        // 质量检测时间
    REJECT_ACTIVATE_TIME: TIME := T#2s;      // 剔除机构动作时间
    
    // ========== 能源计量配置 ==========
    ENERGY_UPDATE_CYCLE: TIME := T#1s;       // 能耗更新周期
    POWER_ALARM_THRESHOLD: REAL := 15.0;     // 功率报警阈值 (kW)
    
    // ========== 系统配置 ==========
    SYSTEM_SCAN_TIME: TIME := T#100ms;       // 系统扫描时间
END_VAR
