# CodeSys项目设置指南

## 项目创建步骤

### 1. 创建新项目
1. 打开CodeSys V3.5
2. 选择 `File` -> `New Project`
3. 项目模板选择: `Standard Project`
4. 设备选择: `CODESYS Control Win V3 (CODESYS)` (SoftPLC运行时)
5. 项目名称: `EnergyManagementSystem`
6. 编程语言: `Structured Text (ST)`

### 2. 配置SoftPLC运行时
1. 在设备树中右键点击 `Device (CODESYS Control Win V3)`
2. 选择 `Add Device` -> `Ethernet Adapter`
3. 配置IP地址: `127.0.0.1`
4. 端口: `1217` (默认CodeSys端口)

### 3. 导入程序文件

#### 3.1 添加全局变量列表
1. 在项目树中右键点击 `Application`
2. 选择 `Add Object` -> `Global Variable List`
3. 命名为: `GVL_Config`
4. 复制 `GVL_Config.st` 文件内容到编辑器

#### 3.2 添加主程序
1. 双击 `PLC_PRG (PRG)` 打开主程序
2. 复制 `PLC_PRG.st` 文件内容到编辑器

#### 3.3 添加功能块
按以下顺序添加功能块:
1. 右键点击 `Application` -> `Add Object` -> `Function Block`
2. 依次创建以下功能块:
   - `FB_ConveyorControl` - 复制 `FB_ConveyorControl.st` 内容
   - `FB_StationControl` - 复制 `FB_StationControl.st` 内容
   - `FB_QualityCheck` - 复制 `FB_QualityCheck.st` 内容
   - `FB_EnergyMeter` - 复制 `FB_EnergyMeter.st` 内容

### 4. 编译项目
1. 选择 `Build` -> `Build` (F11)
2. 检查错误窗口，确保没有编译错误
3. 如有警告，可以忽略未使用变量的警告

### 5. 配置符号配置
1. 在设备树中双击 `Device (CODESYS Control Win V3)`
2. 选择 `Symbol Configuration` 标签
3. 勾选 `Support OPC UA features`
4. 勾选 `Support symbolic access`

### 6. 下载到SoftPLC
1. 选择 `Online` -> `Login` (Alt+F8)
2. 如果提示创建启动应用程序，选择 `Yes`
3. 选择 `Debug` -> `Start` (F5)

## 变量初始值说明

所有变量已在声明时设置初始值:
- 布尔变量: `FALSE`
- 实数变量: `0.0`
- 整数变量: `0`
- 时间变量: `T#0s`
- 系统状态: `0` (待机状态)

## 数据类型说明

- `BOOL`: 布尔型 (TRUE/FALSE)
- `INT`: 16位整数 (-32768 to 32767)
- `DINT`: 32位整数 (-2147483648 to 2147483647)
- `REAL`: 32位浮点数
- `TIME`: 时间类型 (例如: T#5s, T#100ms)

## 下一步

完成项目设置后，继续实现各个功能块:
1. FB_ConveyorControl - 传送带控制
2. FB_StationControl - 工位控制
3. FB_QualityCheck - 质量检测
4. FB_EnergyMeter - 能源计量
5. 主程序集成逻辑

## 注意事项

- 确保CodeSys版本为V3.5或更高
- SoftPLC需要管理员权限运行
- 首次运行时Windows防火墙可能会提示，需要允许访问
- 保存项目文件到 `plc_program` 目录
