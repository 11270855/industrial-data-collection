# PLC程序实现指南

## 概述

本文档描述了能源管理系统PLC控制程序的完整实现。程序使用IEC 61131-3 Structured Text (ST)语言编写，可导入到CodeSys V3.5或更高版本。

## 文件结构

```
plc_program/
├── README.md                    # 目录说明
├── PROJECT_SETUP.md             # CodeSys项目设置指南
├── IMPLEMENTATION_GUIDE.md      # 本文件 - 实现指南
├── GVL_Config.st                # 全局变量列表 - 配置参数
├── PLC_PRG.st                   # 主程序
├── FB_ConveyorControl.st        # 传送带控制功能块
├── FB_StationControl.st         # 工位控制功能块
├── FB_QualityCheck.st           # 质量检测功能块
└── FB_EnergyMeter.st            # 能源计量功能块
```

## 功能块说明

### 1. FB_ConveyorControl - 传送带控制

**功能：**
- 传送带启停控制
- 速度调节（0-5 m/s）
- 加减速控制
- 功率计算（基础功率 + 速度系数 × 速度）

**输入：**
- `bStart`: 启动命令
- `rSpeedSetpoint`: 速度设定值
- `bEmergencyStop`: 紧急停止

**输出：**
- `bRunning`: 运行状态
- `rActualSpeed`: 实际速度
- `rPower`: 功率消耗
- `bFault`: 故障标志

**状态机：**
- 0: 停止
- 1: 启动中
- 2: 运行
- 3: 停止中

### 2. FB_StationControl - 工位控制

**功能：**
- 工位激活和工艺流程控制
- 产品到位检测
- 加工时序控制
- 功率计算（运行时满功率，待机时低功率）

**输入：**
- `bActivate`: 工位激活命令
- `bProductPresent`: 产品到位传感器
- `bEmergencyStop`: 紧急停止
- `tProcessTime`: 工艺加工时间

**输出：**
- `bActive`: 工位激活状态
- `bProcessing`: 正在加工
- `bProcessComplete`: 加工完成
- `rPower`: 功率消耗
- `bFault`: 故障标志
- `sStatus`: 状态文本

**状态机：**
- 0: 待机
- 1: 等待产品
- 2: 加工中
- 3: 完成
- 4: 故障

### 3. FB_QualityCheck - 质量检测

**功能：**
- 质量传感器信号读取
- 合格/不良品判定（多次采样判定）
- 剔除机构控制
- 产品计数和不良品计数

**输入：**
- `bEnable`: 质检使能
- `bQualitySensor`: 质量传感器信号
- `bProductPresent`: 产品到位传感器
- `bTriggerCheck`: 触发检测命令

**输出：**
- `bCheckInProgress`: 检测进行中
- `bCheckComplete`: 检测完成
- `bQualityOK`: 质量合格
- `bQualityNG`: 质量不良
- `bRejectActive`: 剔除机构激活
- `iProductCount`: 产品总数
- `iRejectCount`: 不良品数量
- `rRejectRate`: 不良率

**状态机：**
- 0: 待机
- 1: 检测中
- 2: 合格
- 3: 不良
- 4: 剔除中

### 4. FB_EnergyMeter - 能源计量

**功能：**
- 实时功率累加计算
- 能耗累计（能耗 += 功率 × 时间间隔）
- 异常用电检测（连续超阈值报警）
- 数据更新周期控制（1秒）

**输入：**
- `bEnable`: 计量使能
- `rPower1`, `rPower2`, `rPower3`: 各设备功率
- `rPowerThreshold`: 功率报警阈值
- `bReset`: 复位累计能耗

**输出：**
- `rTotalPower`: 总功率
- `rTotalEnergy`: 累计能耗
- `rAveragePower`: 平均功率
- `rPeakPower`: 峰值功率
- `bPowerAlarm`: 功率报警
- `bDataUpdated`: 数据更新标志

## 主程序逻辑

### 系统状态机

**状态定义：**
- 0: 待机状态 - 所有设备停止，停机时间计时
- 1: 运行状态 - 设备运行，运行时间计时
- 2: 故障状态 - 设备停止，等待故障复位

### 控制流程

1. **系统启动：**
   - 操作员设置 `bSystemStart = TRUE`
   - 系统从待机进入运行状态
   - 传送带启动，速度设定为3 m/s
   - 工位1和工位2激活

2. **生产流程：**
   - 产品到达工位1，传感器检测到产品
   - 工位1开始加工（5秒）
   - 加工完成后，产品移动到工位2
   - 工位2开始加工（5秒）
   - 工位2完成后，触发质量检测
   - 质量检测判定合格/不良
   - 不良品触发剔除机构

3. **能源监控：**
   - 实时计算各设备功率
   - 累计总能耗
   - 监控功率是否超过阈值
   - 连续3次超阈值触发报警

4. **系统停止：**
   - 操作员设置 `bSystemStop = TRUE`
   - 系统返回待机状态
   - 所有设备停止

## 变量映射（用于OPC UA）

### 设备控制变量
- `PLC_PRG.bConveyorStart` - 传送带启动
- `PLC_PRG.rConveyorSpeed` - 传送带速度
- `PLC_PRG.bStation1Active` - 工位1激活
- `PLC_PRG.bStation2Active` - 工位2激活
- `PLC_PRG.bRejectActive` - 剔除机构激活

### 传感器输入
- `PLC_PRG.bProductSensor1` - 产品传感器1
- `PLC_PRG.bProductSensor2` - 产品传感器2
- `PLC_PRG.bQualitySensor` - 质量传感器

### 能源数据
- `PLC_PRG.rConveyorPower` - 传送带功率
- `PLC_PRG.rStation1Power` - 工位1功率
- `PLC_PRG.rStation2Power` - 工位2功率
- `PLC_PRG.rTotalPower` - 总功率
- `PLC_PRG.rTotalEnergy` - 累计能耗

### 生产统计
- `PLC_PRG.iProductCount` - 产品计数
- `PLC_PRG.iRejectCount` - 不良品计数
- `PLC_PRG.iRunTimeSeconds` - 运行时间（秒）
- `PLC_PRG.iDownTimeSeconds` - 停机时间（秒）

### 报警标志
- `PLC_PRG.bEnergyAlarm` - 能耗报警
- `PLC_PRG.bSystemFault` - 系统故障

### 系统状态
- `PLC_PRG.eSystemState` - 系统状态（0=待机, 1=运行, 2=故障）

## 配置参数

在 `GVL_Config.st` 中定义的常量：

```
传送带配置：
- CONVEYOR_MIN_SPEED: 0.0 m/s
- CONVEYOR_MAX_SPEED: 5.0 m/s
- CONVEYOR_BASE_POWER: 0.5 kW
- CONVEYOR_SPEED_COEFF: 0.3 kW/(m/s)

工位配置：
- STATION_ACTIVE_POWER: 5.0 kW
- STATION_STANDBY_POWER: 0.2 kW
- STATION_PROCESS_TIME: 5s

质量检测配置：
- QUALITY_CHECK_TIME: 1s
- REJECT_ACTIVATE_TIME: 2s

能源计量配置：
- ENERGY_UPDATE_CYCLE: 1s
- POWER_ALARM_THRESHOLD: 15.0 kW
```

## 测试步骤

### 1. 编译测试
1. 在CodeSys中打开项目
2. 按F11编译
3. 检查错误窗口，确保无错误

### 2. 仿真测试
1. 登录到SoftPLC（Alt+F8）
2. 启动程序（F5）
3. 打开监控窗口，观察变量值

### 3. 功能测试

**测试传送带：**
```
1. 设置 bSystemStart = TRUE
2. 观察 fbConveyor.bRunning 变为 TRUE
3. 观察 fbConveyor.rActualSpeed 从0加速到3.0
4. 观察 rConveyorPower 随速度增加
```

**测试工位：**
```
1. 设置 bProductSensor1 = TRUE（模拟产品到达）
2. 观察 fbStation1.bProcessing 变为 TRUE
3. 等待5秒，观察 fbStation1.bProcessComplete 变为 TRUE
4. 观察 rStation1Power 在加工时为5.0 kW
```

**测试质量检测：**
```
1. 设置 bProductSensor2 = TRUE
2. 等待工位2完成
3. 设置 bQualitySensor = FALSE（模拟不良品）
4. 观察 fbQualityCheck.bQualityNG 变为 TRUE
5. 观察 bRejectActive 变为 TRUE
6. 观察 iRejectCount 增加
```

**测试能源计量：**
```
1. 观察 rTotalPower 为各设备功率之和
2. 观察 rTotalEnergy 持续增加
3. 手动增加功率超过15 kW
4. 观察 bEnergyAlarm 变为 TRUE
```

## 故障排除

### 编译错误
- 确保所有功能块文件都已导入
- 检查变量名拼写
- 确保使用正确的数据类型

### 运行时错误
- 检查SoftPLC是否正常运行
- 确认管理员权限
- 检查Windows防火墙设置

### 通信问题
- 确认IP地址和端口配置
- 使用UaExpert测试OPC UA连接
- 检查KepServer配置

## 需求追溯

本实现满足以下需求：

- **需求1.1**: 系统启动时初始化所有工位设备
- **需求1.2**: 控制传送带启停和速度调节
- **需求1.3**: 按预设工艺流程执行多工位加工
- **需求1.4**: 检测不良品并触发剔除机制
- **需求1.5**: 持续记录设备状态变量
- **需求2.1**: 实时计算每个设备的功率消耗
- **需求2.2**: 累计统计每个设备的总能耗
- **需求2.3**: 能耗超过阈值时设置异常标志
- **需求2.5**: 以1秒周期更新能源计量数据
- **需求6.1**: 根据运行时间和停机时间计算OEE
- **需求6.2**: 计算质量率（合格品/总产量）

## 下一步

完成PLC程序实现后，继续以下任务：
1. 配置KepServer连接到SoftPLC
2. 实现Python OPC UA客户端
3. 开发Web可视化界面

## 注意事项

- 本程序为仿真环境设计，实际应用需要根据硬件调整
- 扫描时间设置为100ms，可根据实际需求调整
- 所有时间参数可在功能块中修改
- 建议定期保存项目文件
