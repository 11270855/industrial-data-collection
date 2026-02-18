# CodeSys 完整配置指南

## 📋 目录

1. [系统要求](#系统要求)
2. [安装 CodeSys](#安装-codesys)
3. [创建项目](#创建项目)
4. [导入程序](#导入程序)
5. [配置网络](#配置网络)
6. [编译和运行](#编译和运行)
7. [自动运行模式](#自动运行模式)
8. [测试验证](#测试验证)
9. [故障排查](#故障排查)

---

## 系统要求

### 软件要求

| 软件 | 版本 | 说明 |
|------|------|------|
| CodeSys Development System | V3.5 SP19 或更高 | PLC 编程环境 |
| CODESYS Control Win V3 | 与 CodeSys 版本匹配 | SoftPLC 运行时 |
| Windows | 10/11 | 操作系统 |

### 硬件要求

- CPU: Intel i5 或更高
- 内存: 4GB 或更高
- 硬盘: 2GB 可用空间

---

## 安装 CodeSys

### 步骤 1: 下载 CodeSys

1. 访问 CODESYS Store: https://store.codesys.com/
2. 注册账户（免费）
3. 下载以下组件：
   - **CODESYS Development System V3.5**
   - **CODESYS Control Win V3** (SoftPLC)

### 步骤 2: 安装 Development System

1. 运行 `CODESYS_V3.5.x.x_Setup.exe`
2. 选择安装类型：`Complete`（完整安装）
3. 接受许可协议
4. 选择安装路径（默认即可）
5. 等待安装完成
6. 重启计算机（如果提示）

### 步骤 3: 安装 SoftPLC Runtime

1. 运行 `CODESYS Control Win V3.5.x.x.exe`
2. 选择安装类型：`Complete`
3. 接受许可协议
4. 完成安装
5. 重启计算机

### 步骤 4: 验证安装

1. 打开 CodeSys Development System
2. 菜单：`Tools` → `Device Repository`
3. 应该能看到 `CODESYS Control Win V3`

---

## 创建项目

### 方法 1: 从头创建（推荐学习）

#### 1. 新建项目

1. 启动 CodeSys
2. `File` → `New Project`
3. 配置项目：
   - **Templates**: `Standard Project`
   - **Device**: `CODESYS Control Win V3 (CODESYS)`
   - **Language**: `Structured Text (ST)`
   - **Project Name**: `EnergyManagementSystem`
   - **Location**: 选择保存位置
4. 点击 `OK`

#### 2. 项目结构

创建后会看到：
```
EnergyManagementSystem
├── Application
│   └── PLC_PRG (PRG)
└── Device (CODESYS Control Win V3)
```

### 方法 2: 导入现有项目（快速）

如果有完整的 `.project` 文件：

1. `File` → `Open`
2. 选择 `.project` 文件
3. 点击 `Open`

---

## 导入程序

### 步骤 1: 添加全局变量列表

1. 右键 `Application` → `Add Object` → `Global Variable List`
2. 名称：`GVL_Config`
3. 点击 `Open`
4. 复制 `plc_program/GVL_Config.st` 的内容
5. 粘贴到编辑器
6. 保存（Ctrl+S）

**GVL_Config.st 内容预览**：
```iecst
VAR_GLOBAL CONSTANT
    // 系统配置
    CONVEYOR_SPEED_MAX : REAL := 5.0;        // 传送带最大速度 m/s
    CONVEYOR_POWER_MAX : REAL := 3.0;        // 传送带最大功率 kW
    
    // 工位配置
    STATION_POWER_MAX : REAL := 5.0;         // 工位最大功率 kW
    STATION_CYCLE_TIME : TIME := T#5S;       // 工位加工周期
    
    // 能源阈值
    ENERGY_ALARM_THRESHOLD : REAL := 100.0;  // 能耗报警阈值 kWh
    POWER_ALARM_THRESHOLD : REAL := 15.0;    // 功率报警阈值 kW
END_VAR
```

### 步骤 2: 添加功能块

依次创建以下功能块：

#### FB_ConveyorControl（传送带控制）

1. 右键 `Application` → `Add Object` → `Function Block`
2. 名称：`FB_ConveyorControl`
3. 语言：`Structured Text (ST)`
4. 点击 `Open`
5. 复制 `plc_program/FB_ConveyorControl.st` 的内容
6. 保存

#### FB_StationControl（工位控制）

1. 右键 `Application` → `Add Object` → `Function Block`
2. 名称：`FB_StationControl`
3. 语言：`Structured Text (ST)`
4. 复制 `plc_program/FB_StationControl.st` 的内容
5. 保存

#### FB_QualityCheck（质量检测）

1. 右键 `Application` → `Add Object` → `Function Block`
2. 名称：`FB_QualityCheck`
3. 语言：`Structured Text (ST)`
4. 复制 `plc_program/FB_QualityCheck.st` 的内容
5. 保存

#### FB_EnergyMeter（能源计量）

1. 右键 `Application` → `Add Object` → `Function Block`
2. 名称：`FB_EnergyMeter`
3. 语言：`Structured Text (ST)`
4. 复制 `plc_program/FB_EnergyMeter.st` 的内容
5. 保存

### 步骤 3: 更新主程序

1. 双击 `PLC_PRG (PRG)` 打开
2. 删除默认内容
3. 复制 `plc_program/PLC_PRG.st` 的全部内容
4. 粘贴到编辑器
5. 保存

**PLC_PRG.st 结构预览**：
```iecst
PROGRAM PLC_PRG
VAR
    // 功能块实例
    fbConveyor : FB_ConveyorControl;
    fbStation1 : FB_StationControl;
    fbStation2 : FB_StationControl;
    fbQuality : FB_QualityCheck;
    fbEnergy : FB_EnergyMeter;
    
    // 系统状态
    eSystemState : INT := 0;  // 0=停止, 1=运行, 2=故障
    
    // 输入信号
    bSystemStart : BOOL;
    bSystemStop : BOOL;
    bProductSensor1 : BOOL;
    bProductSensor2 : BOOL;
    bQualitySensor : BOOL;
    
    // 输出数据
    rTotalPower : REAL;
    rTotalEnergy : REAL;
    iProductCount : INT;
    iRejectCount : INT;
END_VAR
```

### 步骤 4: 验证导入

1. 在项目树中应该看到：
   ```
   Application
   ├── GVL_Config (GVL)
   ├── FB_ConveyorControl (FB)
   ├── FB_StationControl (FB)
   ├── FB_QualityCheck (FB)
   ├── FB_EnergyMeter (FB)
   └── PLC_PRG (PRG)
   ```

2. 所有文件应该没有红色错误标记

---

## 配置网络

### 步骤 1: 配置虚拟 PLC 网络

CodeSys 使用 **CODESYS Control Win V3** 作为虚拟 PLC（仿真软件），在本地计算机上模拟真实 PLC。

1. 双击项目树中的 `Device (CODESYS Control Win V3)`
2. 切换到 `Communication Settings` 标签
3. 配置网络参数：
   - **Network**: 选择 `Local (127.0.0.1)` 或本地网卡
   - **IP Address**: `127.0.0.1`（本地回环地址）
   - **Port**: `1217`（CodeSys 默认通信端口）
   - **Gateway**: 保持默认

**重要说明**：
- 虚拟 PLC 运行在本地计算机上
- 使用 `127.0.0.1` 作为 IP 地址
- KepServer 也需要配置为连接 `127.0.0.1:1217`

### 步骤 2: 配置扫描任务

1. 在项目树中展开 `Device`
2. 双击 `Task Configuration`
3. 右键 `MainTask` → `Properties`
4. 配置任务参数：
   - **Type**: `Cyclic`
   - **Priority**: `1`
   - **Interval**: `T#10ms`（10毫秒扫描周期）
   - **Watchdog**: `Enabled`
   - **Watchdog Time**: `T#500ms`

### 步骤 3: 分配程序到任务

1. 确保 `PLC_PRG` 已分配到 `MainTask`
2. 如果没有，右键 `MainTask` → `Add Call`
3. 选择 `PLC_PRG`

---

## 编译和运行

### 步骤 1: 编译项目

1. 菜单：`Build` → `Build` 或按 `F11`
2. 检查输出窗口：
   - ✅ `Build completed successfully` - 编译成功
   - ❌ 如果有错误，双击错误信息定位问题

### 步骤 2: 启动虚拟 PLC Runtime

虚拟 PLC 通过 Windows 服务运行，模拟真实 PLC 的行为。

1. 打开 Windows 服务管理器：
   ```
   Win+R → services.msc → 回车
   ```

2. 找到 `CODESYS Control Win V3 Service`
3. 右键 → `Start`（如果未运行）
4. 右键 → `Properties` → 启动类型设为 `Automatic`（自动启动）

**验证虚拟 PLC 运行**：
- 服务状态应显示为 `Running`
- 如果无法启动，以管理员身份运行 CodeSys

### 步骤 3: 登录到 PLC

1. 菜单：`Online` → `Login` 或按 `Alt+F8`
2. 如果提示选择设备，选择 `CODESYS Control Win V3`
3. 如果提示下载程序，点击 `Yes`
4. 等待下载完成

### 步骤 4: 启动程序

1. 菜单：`Debug` → `Start` 或按 `F5`
2. 状态栏应显示 `RUN`
3. 变量值开始更新

---

## 自动运行模式

导入程序并成功运行后，可通过自动模式快速演示完整流程，无需手动设置传感器变量。

### 功能说明

系统支持 **自动运行模式**（`bAutoMode`），启用后自动：
1. 3秒延时后启动生产线
2. 每10秒生成一个模拟产品
3. 模拟产品在工位间流动（每工位加工5秒）
4. 模拟质量检测（90%合格 / 10%不良）

### 控制变量

```iecst
PLC_PRG.bAutoMode := TRUE  // 启用自动模式（默认）
PLC_PRG.bAutoMode := FALSE // 切换到手动模式
```

### 运行时序

```
0s   → 系统上电，待机
3s   → 自动启动
13s  → 第1个产品到达工位1
18s  → 工位1完成，延时2s移动
20s  → 产品到达工位2
25s  → 工位2完成，质量检测
30s  → 第2个产品到达工位1
...  → 循环继续
```

### 相关变量说明

| 变量 | 类型 | 说明 |
|------|------|------|
| `bAutoMode` | BOOL | 自动/手动模式开关 |
| `tonAutoStart` | TON | 自动启动延时（3秒）|
| `tonProductGen1` | TON | 产品生成间隔（10秒）|
| `iProductGenCounter` | INT | 产品计数（用于质量模拟）|

### 使用场景

| 场景 | `bAutoMode` | 说明 |
|------|-------------|------|
| 演示/测试 | TRUE | 系统自动运行，无需手动操作 |
| 开发/调试 | FALSE | 手动控制每个步骤 |
| OPC UA集成测试 | TRUE | 持续生成数据供上位机采集 |

### 注意事项

- 自动模式优先级高于手动设置，`bAutoMode=TRUE` 时手动传感器值会被覆盖
- 停止系统：设置 `bSystemStop := TRUE`，自动模式会在3秒后重新启动
- 若需禁用故障检测（调试用）：注释 `PLC_PRG` 中的故障检测代码块，系统将持续运行忽略所有故障

### 调试时监视的关键变量

```
fbConveyor.bFault / fbConveyor.eState
fbStation1.bFault / fbStation1.eState
fbStation2.bFault / fbStation2.eState
```

---

## 测试验证

### 方法 1: 使用监控窗口

#### 1. 添加监控窗口

1. 右键 `Application` → `Add Object` → `Watch and Receipt Manager`
2. 名称：`Watch1`

#### 2. 添加监控变量

在监控窗口中添加以下变量：

| 变量名 | 说明 | 预期值 |
|--------|------|--------|
| `PLC_PRG.eSystemState` | 系统状态 | 0=停止, 1=运行 |
| `PLC_PRG.bSystemStart` | 启动命令 | TRUE/FALSE |
| `PLC_PRG.rTotalPower` | 总功率 | 0.0 ~ 15.0 kW |
| `PLC_PRG.rTotalEnergy` | 总能耗 | 持续增加 |
| `PLC_PRG.iProductCount` | 产品计数 | 递增 |
| `PLC_PRG.iRejectCount` | 不良品计数 | 递增 |
| `PLC_PRG.bEnergyAlarm` | 能耗报警 | TRUE/FALSE |

#### 3. 测试系统启动

1. 在监控窗口中，双击 `PLC_PRG.bSystemStart`
2. 修改值为 `TRUE`
3. 按 `Enter` 确认
4. 观察 `PLC_PRG.eSystemState` 应变为 `1`（运行）

#### 4. 模拟产品流程

```
// 步骤 1: 启动系统
PLC_PRG.bSystemStart := TRUE;

// 步骤 2: 模拟产品到达传感器1
PLC_PRG.bProductSensor1 := TRUE;
等待 2 秒
PLC_PRG.bProductSensor1 := FALSE;

// 步骤 3: 模拟产品到达传感器2
PLC_PRG.bProductSensor2 := TRUE;
等待 2 秒
PLC_PRG.bProductSensor2 := FALSE;

// 步骤 4: 模拟质量检测
PLC_PRG.bQualitySensor := TRUE;  // 合格品
// 或
PLC_PRG.bQualitySensor := FALSE; // 不良品
```

#### 5. 验证结果

- ✅ `iProductCount` 应该增加（合格品）
- ✅ `iRejectCount` 应该增加（不良品）
- ✅ `rTotalPower` 显示当前功率
- ✅ `rTotalEnergy` 持续累加

### 方法 2: 使用在线视图

1. 双击 `PLC_PRG` 打开程序
2. 菜单：`Online` → `Toggle Breakpoint` 或按 `F9`
3. 在代码旁边可以看到变量的实时值
4. 蓝色背景表示变量值为 TRUE
5. 白色背景表示变量值为 FALSE

---

## 故障排查

### 问题 1: 无法编译

**错误**: `Unknown identifier 'FB_ConveyorControl'`

**原因**: 功能块未创建或名称不匹配

**解决**:
1. 检查所有功能块是否已创建
2. 确认名称拼写正确（区分大小写）
3. 重新编译（F11）

### 问题 2: 无法登录

**错误**: `No device found` 或 `Connection timeout`

**原因**: SoftPLC 未运行或网络配置错误

**解决**:
1. 检查 SoftPLC 服务是否运行：
   ```
   services.msc → CODESYS Control Win V3 Service
   ```
2. 以管理员身份运行 CodeSys
3. 检查防火墙设置
4. 确认 IP 地址和端口配置正确

### 问题 3: 程序不运行

**错误**: 状态显示 `STOP` 而不是 `RUN`

**原因**: 程序未启动或有运行时错误

**解决**:
1. 按 `F5` 启动程序
2. 检查 `Error List` 窗口是否有错误
3. 查看 `Logger` 窗口的日志信息
4. 检查 Watchdog 是否触发

### 问题 4: 变量值不更新

**错误**: 监控窗口中的值不变化

**原因**: 程序逻辑问题或扫描周期过长

**解决**:
1. 确认程序状态为 `RUN`
2. 检查变量是否在程序中被赋值
3. 减小扫描周期（如改为 T#10ms）
4. 检查是否有死循环

### 问题 5: KepServer 无法连接

**错误**: KepServer 显示设备连接失败

**原因**: PLC 网络配置或 KepServer 配置错误

**解决**:
1. 确认 PLC 程序正在运行（RUN 状态）
2. 检查 IP 地址：
   - PLC: `127.0.0.1`（本地）
   - KepServer: 使用相同 IP
3. 检查端口：`1217`（默认）
4. 在 CodeSys 中测试连接：
   ```
   Online → Communication Parameters → Scan Network
   ```

---

## 高级配置

### 配置符号文件（用于 KepServer）

1. 菜单：`Project` → `Project Settings`
2. 选择 `Symbol Configuration`
3. 配置：
   - ✅ `Support symbolic access`
   - ✅ `Export symbol file`
   - 文件路径：选择导出位置
4. 重新编译并下载

### 配置在线变化

允许在运行时修改代码：

1. `Device` → `Properties`
2. `Online Settings` 标签
3. ✅ `Allow online change`
4. ✅ `Allow force`

### 配置数据保持

保持变量值在重启后不丢失：

1. 在变量声明中添加 `RETAIN` 关键字：
   ```iecst
   VAR RETAIN
       iProductCount : INT;
       rTotalEnergy : REAL;
   END_VAR
   ```

---

## 性能优化

### 优化扫描周期

- 控制逻辑：`T#10ms`
- 数据采集：`T#100ms`
- 统计计算：`T#1s`

### 优化内存使用

- 使用合适的数据类型
- 避免大数组
- 及时释放不用的变量

---

## 下一步

完成 CodeSys 配置后：

1. ✅ 配置 KepServer（参考 [docs/KEPSERVER_SETUP.md](KEPSERVER_SETUP.md)）
2. ✅ 启动数据采集（`python python_client/main.py`）
3. ✅ 启动 Web 应用（`python web_app/app.py`）
4. ✅ 访问监控界面（http://localhost:5000）

---

## 参考资料

- **CodeSys 官方文档**: https://help.codesys.com/
- **项目文件位置**: `plc_program/`
- **快速开始**: `plc_program/QUICK_START.md`
- **实现指南**: `plc_program/IMPLEMENTATION_GUIDE.md`

---

## 附录：完整变量列表

### 输入变量（可通过 KepServer 写入）

| 变量名 | 类型 | 说明 |
|--------|------|------|
| `bSystemStart` | BOOL | 系统启动命令 |
| `bSystemStop` | BOOL | 系统停止命令 |
| `bEmergencyStop` | BOOL | 紧急停止 |
| `bConveyorStart` | BOOL | 传送带启动 |
| `rConveyorSpeed` | REAL | 传送带速度设定 |
| `bStation1Active` | BOOL | 工位1激活 |
| `bStation2Active` | BOOL | 工位2激活 |
| `bProductSensor1` | BOOL | 产品传感器1 |
| `bProductSensor2` | BOOL | 产品传感器2 |
| `bQualitySensor` | BOOL | 质量传感器 |

### 输出变量（可通过 KepServer 读取）

| 变量名 | 类型 | 说明 |
|--------|------|------|
| `eSystemState` | INT | 系统状态 |
| `bSystemFault` | BOOL | 系统故障 |
| `rConveyorPower` | REAL | 传送带功率 (kW) |
| `rStation1Power` | REAL | 工位1功率 (kW) |
| `rStation2Power` | REAL | 工位2功率 (kW) |
| `rTotalPower` | REAL | 总功率 (kW) |
| `rTotalEnergy` | REAL | 总能耗 (kWh) |
| `bEnergyAlarm` | BOOL | 能耗报警 |
| `iProductCount` | INT | 产品计数 |
| `iRejectCount` | INT | 不良品计数 |
| `iRunTimeSeconds` | DINT | 运行时间 (秒) |
| `iDownTimeSeconds` | DINT | 停机时间 (秒) |

---

文档版本：1.0  
最后更新：2025-12-15
