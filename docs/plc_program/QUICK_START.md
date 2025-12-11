# PLC程序快速启动指南

## 5分钟快速开始

### 前提条件
- 已安装CodeSys V3.5或更高版本
- 已安装CODESYS Control Win V3 (SoftPLC运行时)

### 步骤1: 创建CodeSys项目（2分钟）

1. 打开CodeSys
2. `File` → `New Project`
3. 选择 `Standard Project`
4. 设备: `CODESYS Control Win V3`
5. 语言: `Structured Text (ST)`
6. 项目名: `EnergyManagementSystem`

### 步骤2: 导入程序文件（2分钟）

#### 添加全局变量
1. 右键 `Application` → `Add Object` → `Global Variable List`
2. 命名: `GVL_Config`
3. 复制 `GVL_Config.st` 内容

#### 添加功能块
右键 `Application` → `Add Object` → `Function Block`，依次创建：
- `FB_ConveyorControl` - 复制 `FB_ConveyorControl.st`
- `FB_StationControl` - 复制 `FB_StationControl.st`
- `FB_QualityCheck` - 复制 `FB_QualityCheck.st`
- `FB_EnergyMeter` - 复制 `FB_EnergyMeter.st`

#### 更新主程序
1. 双击 `PLC_PRG (PRG)`
2. 复制 `PLC_PRG.st` 全部内容替换

### 步骤3: 编译和运行（1分钟）

1. 按 `F11` 编译
2. 按 `Alt+F8` 登录
3. 按 `F5` 启动

### 快速测试

在监控窗口中设置以下变量：

```
// 启动系统
PLC_PRG.bSystemStart := TRUE;

// 模拟产品到达
PLC_PRG.bProductSensor1 := TRUE;
PLC_PRG.bProductSensor2 := TRUE;

// 模拟质量传感器（TRUE=合格，FALSE=不良）
PLC_PRG.bQualitySensor := TRUE;
```

观察以下输出：
- `PLC_PRG.eSystemState` 应该变为 1（运行）
- `PLC_PRG.rTotalPower` 显示总功率
- `PLC_PRG.rTotalEnergy` 持续增加
- `PLC_PRG.iProductCount` 产品计数增加

## 关键变量监控

添加以下变量到监控窗口：

```
// 系统状态
PLC_PRG.eSystemState
PLC_PRG.bSystemFault

// 能源数据
PLC_PRG.rTotalPower
PLC_PRG.rTotalEnergy
PLC_PRG.bEnergyAlarm

// 生产数据
PLC_PRG.iProductCount
PLC_PRG.iRejectCount

// 设备功率
PLC_PRG.rConveyorPower
PLC_PRG.rStation1Power
PLC_PRG.rStation2Power
```

## 常见问题

**Q: 编译错误 "Unknown type"**
A: 确保所有功能块都已创建并命名正确

**Q: 无法登录到SoftPLC**
A: 以管理员身份运行CodeSys

**Q: 变量值不变化**
A: 确认程序已启动（F5），检查扫描状态

## 下一步

- 详细文档: 查看 `IMPLEMENTATION_GUIDE.md`
- 项目设置: 查看 `PROJECT_SETUP.md`
- KepServer配置: 继续任务13

## 支持

如遇问题，请检查：
1. CodeSys版本是否为V3.5+
2. SoftPLC是否正常运行
3. 所有文件是否正确导入
