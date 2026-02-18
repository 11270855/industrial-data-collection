# KepServer 配置指南

本文档详细说明如何配置 KepServerEX 以连接 CodeSys PLC 并启用 OPC UA 服务器，实现能源管理系统的数据通信。

> **快速参考**：如需 5 分钟内完成基础配置，直接阅读[快速配置步骤](#快速配置步骤)；如遇中文界面身份验证问题，参见[故障排查 · 问题4](#问题4身份验证失败)。

## 目录

1. [前提条件](#前提条件)
2. [快速配置步骤](#快速配置步骤)
3. [KepServer安装](#kepserver安装)
4. [创建通道](#创建通道)
5. [添加设备](#添加设备)
6. [配置标签](#配置标签)
7. [启用OPC UA服务器](#启用opc-ua服务器)
8. [测试连接](#测试连接)
9. [故障排查](#故障排查)

---

## 前提条件

在开始配置之前，请确保：

- 已安装KepServerEX 6.x或更高版本
- CodeSys PLC程序已部署并运行
- PLC与KepServer所在计算机网络连通
- 具有KepServer管理员权限
- 了解PLC的IP地址和通信端口

### 所需信息

| 项目 | 说明 | 示例值 |
|------|------|--------|
| PLC IP地址 | CodeSys PLC的网络地址 | 192.168.1.100 |
| PLC端口 | CodeSys运行时端口 | 1217（默认） |
| 项目名称 | CodeSys项目名称 | ProductionLine_PLC |

---

## 快速配置步骤

完成以下6步即可建立基础连接：

### 1. 安装 KepServer

- 安装 KepServerEX 6.x 或更高版本
- 安装时勾选：✅ OPC UA Server  ✅ CodeSys Ethernet Driver

### 2. 启动 KepServer

```
开始菜单 → KEPServerEX 6 Configuration
```

### 3. 创建通道（Channel）

1. 右键 `Connectivity` → `New Channel`
2. 驱动选择：`CodeSys Ethernet`
3. 通道名称：`CodeSys_Channel`
4. 接受默认设置完成

### 4. 添加设备（Device）

1. 右键 `CodeSys_Channel` → `New Device`
2. 型号：`CodeSys V3.x`
3. 设备名称：`ProductionLine_PLC`
4. IP 地址：`127.0.0.1`（本地虚拟PLC）
5. 端口：`1217`

### 5. 启用 OPC UA 服务器

1. 菜单：`Settings` → `OPC UA Configuration`
2. ✅ 勾选 `Enable OPC UA Server`
3. 点击 `User Manager` → ✅ 勾选 `Allow Anonymous Login`
4. 确认端点 URL：`opc.tcp://localhost:4840`，Security Policy：`None`
5. 点击 `OK`

### 6. 验证配置

#### 方法1：KepServer Quick Client

1. 菜单：`Tools` → `Quick Client`
2. Server URL：`opc.tcp://localhost:4840`，点击 `Connect`
3. 应能看到设备和标签节点

#### 方法2：Python 测试

```bash
cd python_client
python main.py --test-connection
```

应显示：`✓ OPC UA连接成功`

---

### 1. 安装KepServerEX

1. 运行KepServerEX安装程序
2. 选择"Complete"完整安装
3. 确保安装以下组件：
   - OPC UA Server（必需）
   - CodeSys Ethernet Driver（必需）
   - Administration Tools（推荐）

### 2. 启动KepServer

1. 从开始菜单启动"KEPServerEX 6 Configuration"
2. 如果出现防火墙提示，选择"允许访问"
3. 等待KepServer完全启动（状态栏显示"Runtime"）

---

## 创建通道

通道定义了KepServer与PLC之间的通信方式。

### 步骤

1. 打开通道配置
   - 在左侧项目树中，右键点击"Connectivity"
   - 选择"New Channel"

2. 选择驱动程序
   - 在驱动列表中找到并选择："CodeSys Ethernet"
   - 点击"Next"

3. 配置通道名称
   - Name: CodeSys_Channel
   - Description: CodeSys PLC通信通道
   - 点击"Next"

4. 配置通信参数
   - Network Adapter: 选择正确的网卡（与PLC在同一网段）
   - Write Optimizations: Write All Values for All Tags
   - Request Timeout: 3000 ms
   - Retry Attempts: 3
   - 点击"Next"

5. 完成通道创建
   - 检查配置摘要
   - 点击"Finish"

### 验证通道状态

通道图标应显示为绿色，如果显示红色，检查网络连接和驱动程序。

---

## 添加设备

设备代表具体的PLC控制器。

### 步骤

1. 创建新设备
   - 右键点击刚创建的"CodeSys_Channel"
   - 选择"New Device"

2. 选择设备型号
   - Model: 选择"CodeSys V3.x"
   - 点击"Next"

3. 配置设备名称
   - Name: ProductionLine_PLC
   - Description: 生产线PLC设备
   - 点击"Next"

4. 配置设备地址
   - IP Address: 192.168.1.100（PLC的实际IP地址）
   - Port: 1217（CodeSys默认端口）
   - Device ID: 留空或0
   - 点击"Next"

5. 配置扫描参数
   - Scan Mode: Respect Tag-Specified Scan Rate
   - Initial Updates from Cache: Enabled
   - 点击"Next"

6. 配置标签生成
   - 选择"Do not generate tags on creation"（稍后手动创建）
   - 点击"Next"

7. 完成设备创建
   - 检查配置摘要
   - 点击"Finish"

### 验证设备连接

1. 右键点击设备"ProductionLine_PLC"
2. 选择"Properties"
3. 点击"Communications" → "Test Connection"
4. 应显示"Connection Successful"

---

## 配置标签

标签映射PLC中的变量，使其可通过OPC UA访问。本节详细说明如何创建标签组和配置所有必需的标签。

### 标签命名规范

格式：`标签组.变量名`

例如：`DeviceControl.ConveyorStart`

### 标签组结构

为了更好地组织标签，我们创建以下标签组：

1. **DeviceControl** - 设备控制变量（可读写）
2. **SensorInput** - 传感器输入（只读）
3. **EnergyData** - 能源数据（只读）
4. **Production** - 生产统计（只读）
5. **SystemStatus** - 系统状态（只读）
6. **DeviceStatus** - 设备状态详情（只读）
7. **QualityControl** - 质量控制（只读）

### 创建标签组步骤

1. 右键点击设备"ProductionLine_PLC"
2. 选择"New Tag"
3. 在"Name"字段输入组名（如DeviceControl）
4. 在"Data Type"选择"Group"
5. 点击"OK"
6. 重复以上步骤创建所有标签组

### 完整标签配置表

以下是基于PLC程序的完整标签映射配置：

#### 1. DeviceControl（设备控制）

控制命令和设定值，支持读写操作。

| 标签名称 | PLC变量 | 数据类型 | 访问权限 | 扫描率(ms) | 说明 |
|---------|---------|---------|---------|-----------|------|
| ConveyorStart | PLC_PRG.bConveyorStart | Boolean | Read/Write | 1000 | 传送带启动命令 |
| ConveyorSpeed | PLC_PRG.rConveyorSpeed | Float | Read/Write | 1000 | 传送带速度设定 (0-5 m/s) |
| Station1Active | PLC_PRG.bStation1Active | Boolean | Read/Write | 1000 | 工位1激活命令 |
| Station2Active | PLC_PRG.bStation2Active | Boolean | Read/Write | 1000 | 工位2激活命令 |
| SystemStart | PLC_PRG.bSystemStart | Boolean | Read/Write | 1000 | 系统启动命令 |
| SystemStop | PLC_PRG.bSystemStop | Boolean | Read/Write | 1000 | 系统停止命令 |
| EmergencyStop | PLC_PRG.bEmergencyStop | Boolean | Read/Write | 500 | 紧急停止（高优先级） |
| AutoMode | PLC_PRG.bAutoMode | Boolean | Read/Write | 1000 | 自动运行模式开关 |

#### 2. SensorInput（传感器输入）

物理传感器状态，只读。

| 标签名称 | PLC变量 | 数据类型 | 访问权限 | 扫描率(ms) | 说明 |
|---------|---------|---------|---------|-----------|------|
| ProductSensor1 | PLC_PRG.bProductSensor1 | Boolean | Read Only | 500 | 工位1产品检测传感器 |
| ProductSensor2 | PLC_PRG.bProductSensor2 | Boolean | Read Only | 500 | 工位2产品检测传感器 |
| QualitySensor | PLC_PRG.bQualitySensor | Boolean | Read Only | 500 | 质量检测传感器 (TRUE=合格) |

#### 3. EnergyData（能源数据）

能源计量和报警信息，只读。

| 标签名称 | PLC变量 | 数据类型 | 访问权限 | 扫描率(ms) | 说明 |
|---------|---------|---------|---------|-----------|------|
| ConveyorPower | PLC_PRG.rConveyorPower | Float | Read Only | 1000 | 传送带功率 (kW) |
| Station1Power | PLC_PRG.rStation1Power | Float | Read Only | 1000 | 工位1功率 (kW) |
| Station2Power | PLC_PRG.rStation2Power | Float | Read Only | 1000 | 工位2功率 (kW) |
| TotalPower | PLC_PRG.rTotalPower | Float | Read Only | 1000 | 总功率 (kW) |
| TotalEnergy | PLC_PRG.rTotalEnergy | Float | Read Only | 1000 | 累计能耗 (kWh) |
| AveragePower | PLC_PRG.rAveragePower | Float | Read Only | 1000 | 平均功率 (kW) |
| PeakPower | PLC_PRG.rPeakPower | Float | Read Only | 1000 | 峰值功率 (kW) |
| EnergyAlarm | PLC_PRG.bEnergyAlarm | Boolean | Read Only | 500 | 能耗报警标志 |
| EnergyDataUpdated | PLC_PRG.bEnergyDataUpdated | Boolean | Read Only | 1000 | 能耗数据更新标志 |

#### 4. Production（生产统计）

生产计数和时间统计，只读。

| 标签名称 | PLC变量 | 数据类型 | 访问权限 | 扫描率(ms) | 说明 |
|---------|---------|---------|---------|-----------|------|
| ProductCount | PLC_PRG.iProductCount | Word | Read Only | 1000 | 产品总计数 |
| RejectCount | PLC_PRG.iRejectCount | Word | Read Only | 1000 | 不良品计数 |
| RunTimeSeconds | PLC_PRG.iRunTimeSeconds | DWord | Read Only | 1000 | 运行时间（秒） |
| DownTimeSeconds | PLC_PRG.iDownTimeSeconds | DWord | Read Only | 1000 | 停机时间（秒） |

#### 5. SystemStatus（系统状态）

系统整体状态和诊断信息，只读。

| 标签名称 | PLC变量 | 数据类型 | 访问权限 | 扫描率(ms) | 说明 |
|---------|---------|---------|---------|-----------|------|
| SystemState | PLC_PRG.eSystemState | Word | Read Only | 500 | 系统状态 (0=待机, 1=运行, 2=故障) |
| SystemFault | PLC_PRG.bSystemFault | Boolean | Read Only | 500 | 系统故障标志 |
| SystemStatus | PLC_PRG.iSystemStatus | Word | Read Only | 1000 | 系统状态码 (0=初始化, 1=待机, 2=运行, 3=故障) |
| AllDevicesReady | PLC_PRG.bAllDevicesReady | Boolean | Read Only | 1000 | 所有设备就绪标志 |
| ActiveDeviceCount | PLC_PRG.iActiveDeviceCount | Word | Read Only | 1000 | 激活设备数量 |

#### 6. DeviceStatus（设备状态详情）

各设备的详细运行状态，只读。

| 标签名称 | PLC变量 | 数据类型 | 访问权限 | 扫描率(ms) | 说明 |
|---------|---------|---------|---------|-----------|------|
| ConveyorRunning | PLC_PRG.bConveyorRunning | Boolean | Read Only | 1000 | 传送带运行状态 |
| ConveyorActualSpeed | PLC_PRG.rConveyorActualSpeed | Float | Read Only | 1000 | 传送带实际速度 (m/s) |
| ConveyorFault | PLC_PRG.bConveyorFault | Boolean | Read Only | 500 | 传送带故障标志 |
| Station1ActiveState | PLC_PRG.bStation1ActiveState | Boolean | Read Only | 1000 | 工位1激活状态 |
| Station1Processing | PLC_PRG.bStation1Processing | Boolean | Read Only | 1000 | 工位1加工中 |
| Station1ProcessComplete | PLC_PRG.bStation1ProcessComplete | Boolean | Read Only | 1000 | 工位1加工完成 |
| Station1Fault | PLC_PRG.bStation1Fault | Boolean | Read Only | 500 | 工位1故障标志 |
| Station1Status | PLC_PRG.iStation1Status | Word | Read Only | 1000 | 工位1状态码 |
| Station2ActiveState | PLC_PRG.bStation2ActiveState | Boolean | Read Only | 1000 | 工位2激活状态 |
| Station2Processing | PLC_PRG.bStation2Processing | Boolean | Read Only | 1000 | 工位2加工中 |
| Station2ProcessComplete | PLC_PRG.bStation2ProcessComplete | Boolean | Read Only | 1000 | 工位2加工完成 |
| Station2Fault | PLC_PRG.bStation2Fault | Boolean | Read Only | 500 | 工位2故障标志 |
| Station2Status | PLC_PRG.iStation2Status | Word | Read Only | 1000 | 工位2状态码 |

#### 7. QualityControl（质量控制）

质量检测和剔除控制，只读。

| 标签名称 | PLC变量 | 数据类型 | 访问权限 | 扫描率(ms) | 说明 |
|---------|---------|---------|---------|-----------|------|
| RejectActive | PLC_PRG.bRejectActive | Boolean | Read Only | 500 | 剔除机构激活状态 |
| QualityCheckInProgress | PLC_PRG.bQualityCheckInProgress | Boolean | Read Only | 500 | 质检进行中 |
| QualityCheckComplete | PLC_PRG.bQualityCheckComplete | Boolean | Read Only | 500 | 质检完成 |
| QualityOK | PLC_PRG.bQualityOK | Boolean | Read Only | 500 | 质检合格标志 |
| QualityNG | PLC_PRG.bQualityNG | Boolean | Read Only | 500 | 质检不合格标志 |
| RejectRate | PLC_PRG.rRejectRate | Float | Read Only | 1000 | 不良率 (%) |

### 创建单个标签详细步骤

以DeviceControl.ConveyorStart为例：

1. **创建标签**
   - 右键点击"DeviceControl"标签组
   - 选择"New Tag"

2. **配置基本属性**
   - Name: `ConveyorStart`
   - Description: `传送带启动命令`
   - Address: `PLC_PRG.bConveyorStart`
   - Data Type: `Boolean`

3. **配置访问权限**
   - Client Access: `Read/Write`
   - Scan Rate: `1000` ms

4. **高级设置（可选）**
   - Respect Data Type: `Enabled`
   - Scale: `None`

5. **保存标签**
   - 点击"OK"

6. **验证标签**
   - 标签图标应显示为绿色（表示连接正常）
   - 在"Value"列中应显示当前值
   - 如果显示红色或"Bad Quality"，检查地址拼写和PLC连接

### 批量导入标签（推荐）

对于大量标签，可以使用CSV批量导入功能：

1. **准备CSV文件**
   
   创建文件`tags_import.csv`，格式如下：
   ```csv
   Tag Name,Address,Data Type,Client Access,Scan Rate
   DeviceControl.ConveyorStart,PLC_PRG.bConveyorStart,Boolean,Read/Write,1000
   DeviceControl.ConveyorSpeed,PLC_PRG.rConveyorSpeed,Float,Read/Write,1000
   DeviceControl.Station1Active,PLC_PRG.bStation1Active,Boolean,Read/Write,1000
   ...
   ```

2. **导入标签**
   - 右键点击设备"ProductionLine_PLC"
   - 选择"Import Tags from CSV"
   - 选择准备好的CSV文件
   - 点击"Import"

3. **验证导入结果**
   - 检查所有标签是否正确创建
   - 验证标签值是否正常更新

### 标签地址格式说明

KepServer中CodeSys标签地址格式：

- **格式**: `程序名.变量名`
- **示例**: `PLC_PRG.bConveyorStart`
- **注意事项**:
  - 地址区分大小写
  - 必须与PLC程序中的变量名完全一致
  - 功能块实例变量格式：`PLC_PRG.fbConveyor.bRunning`

### 数据类型映射表

| PLC数据类型 | KepServer数据类型 | 说明 |
|------------|------------------|------|
| BOOL | Boolean | 布尔值 |
| INT | Word | 16位整数 |
| DINT | DWord | 32位整数 |
| REAL | Float | 32位浮点数 |
| STRING | String | 字符串 |
| TIME | DWord | 时间（毫秒） |

### 标签质量状态说明

标签显示的质量状态：

- **Good (绿色)**: 标签值正常更新
- **Bad (红色)**: 无法读取标签值
  - 可能原因：地址错误、PLC未运行、网络断开
- **Uncertain (黄色)**: 标签值不确定
  - 可能原因：通信延迟、数据类型不匹配

### 标签验证清单

配置完成后，使用此清单验证每个标签组：

- [ ] DeviceControl组：8个标签，全部可读写
- [ ] SensorInput组：3个标签，全部只读
- [ ] EnergyData组：9个标签，全部只读
- [ ] Production组：4个标签，全部只读
- [ ] SystemStatus组：5个标签，全部只读
- [ ] DeviceStatus组：13个标签，全部只读
- [ ] QualityControl组：6个标签，全部只读
- [ ] 所有标签图标显示为绿色
- [ ] 所有标签值正常更新
- [ ] 可写标签可以成功写入

---

## 启用OPC UA服务器

KepServer内置OPC UA服务器，需要启用才能让Python客户端连接。

### 步骤

1. 打开OPC UA配置
   - 在菜单栏选择"Settings" → "OPC UA Configuration"

2. 启用OPC UA服务器
   - 勾选"Enable OPC UA Server"
   - 点击"Apply"

3. 配置服务器端点
   - Server Endpoint URL: opc.tcp://localhost:4840（默认端点）
   - 点击"Server Endpoints"标签页

4. 配置匿名访问（重要）
   - 点击"User Manager"按钮
   - 确保"Allow Anonymous Login"已勾选
   - 点击"Apply"保存

5. 配置安全策略
   - 在"Server Endpoints"中，确保至少有一个端点的Security Policy为"None"
   - Security Mode: None（开发环境）
   - Message Security Mode: None

**开发环境配置（推荐）：**
- Allow Anonymous Login: ✓ Enabled
- Security Policy: None
- Message Security Mode: None

**生产环境建议：**
- 禁用匿名登录
- 启用用户名/密码认证
- 使用安全策略（Basic256Sha256）
- Message Security Mode: SignAndEncrypt

4. 配置服务器属性
   - Server Name: KepServerEX
   - Application URI: urn:localhost:KepServerEX
   - Product URI: urn:KepServerEX

5. 保存配置
   - 点击"OK"
   - KepServer会自动重启OPC UA服务

### 验证OPC UA服务器

1. 检查服务状态
   - 在KepServer主界面底部状态栏
   - 应显示"OPC UA Server: Running"

2. 查看端点信息
   - 在菜单栏选择"View" → "Event Log"
   - 查找"OPC UA Server started"消息
   - 记录端点URL（如opc.tcp://192.168.1.10:4840）

---

## 测试连接

### 使用KepServer内置工具测试

1. 打开Quick Client
   - 在菜单栏选择"Tools" → "Quick Client"

2. 连接到OPC UA服务器
   - 在"Server URL"输入：opc.tcp://localhost:4840
   - 点击"Connect"

3. 浏览标签
   - 展开"Objects" → "ProductionLine_PLC"
   - 应看到所有配置的标签组和标签

4. 读取标签值
   - 选择任意标签（如EnergyData.TotalPower）
   - 点击"Read"
   - 应显示当前值

5. 写入标签值（可写标签）
   - 选择可写标签（如DeviceControl.ConveyorStart）
   - 在"Value"字段输入新值（如True）
   - 点击"Write"
   - 验证PLC中的值是否改变

### 使用Python客户端测试

1. 配置环境变量
   - 编辑.env文件
   - 设置OPC_UA_SERVER_URL=opc.tcp://localhost:4840

2. 运行测试脚本
   ```
   cd python_client
   python main.py --test-connection
   ```

3. 检查输出
   - 应显示"OPC UA连接成功"
   - 如果失败，检查KepServer状态和防火墙设置

---

## 故障排查

### 问题1：无法连接到PLC

症状：设备图标显示红色，状态为"Failed"

解决方案：
1. 检查网络连接
   - 在命令行执行：ping 192.168.1.100
   - 确保PLC可达

2. 检查PLC运行状态
   - 确认CodeSys PLC程序正在运行
   - 检查PLC的网络配置

3. 检查防火墙
   - 临时关闭Windows防火墙测试
   - 如果可以连接，添加KepServer到防火墙例外

4. 验证IP地址和端口
   - 确认PLC的IP地址正确
   - 确认CodeSys端口为1217（默认）

### 问题2：标签值不更新

症状：标签显示"Bad Quality"或值不变化

解决方案：
1. 检查标签地址
   - 确认PLC变量名称拼写正确
   - 注意大小写敏感

2. 检查数据类型
   - 确保KepServer标签数据类型与PLC变量匹配

3. 检查扫描率
   - 扫描率不要设置太快（建议≥500ms）

4. 检查访问权限
   - 只读变量不能设置为Read/Write

### 问题3：OPC UA客户端无法连接

症状：Python客户端报错"Connection refused"

解决方案：
1. 检查OPC UA服务器状态
   - 在KepServer中确认OPC UA服务器已启用

2. 检查端点URL
   - 确认URL格式正确：opc.tcp://IP:4840

3. 检查防火墙
   - 确保端口4840已开放

4. 检查安全设置
   - 开发环境：启用匿名访问

### 问题4：身份验证失败

症状：Python客户端报错"The user identity token is not valid" (BadIdentityTokenInvalid)

这是最常见的连接问题，通常是因为KepServer的匿名访问未正确配置。

**解决步骤（英文界面）：**

1. **启用匿名登录**
   - 打开KepServer Configuration
   - 菜单栏：Settings → OPC UA Configuration
   - 点击"User Manager"按钮
   - 确保"Allow Anonymous Login"已勾选 ✓
   - 点击"Apply"

2. **检查端点安全策略**
   - 在OPC UA Configuration窗口
   - 切换到"Server Endpoints"标签页
   - 确认至少有一个端点配置为：
     - Security Policy: None
     - Security Mode: None
   - 如果没有，点击"Add"添加一个

3. **重启OPC UA服务**
   - 点击"OK"保存所有更改
   - KepServer会自动重启OPC UA服务
   - 等待状态栏显示"OPC UA Server: Running"

**中文界面额外步骤（配置用户名密码方式）：**

如果需要使用用户名密码，而非匿名登录：

1. **打开设置** → **OPC UA配置** → 点击 **"用户管理器"**
2. 点击 **"添加"**，填写：用户名 `admin`，密码 `admin123456789`，权限：读写
3. 找到 **"端点"** / **"服务器端点"** 标签页，选中 `opc.tcp://localhost:4840` 对应的端点
4. 编辑该端点，找到 **"用户令牌策略"** / **"User Token Policies"** 区域
5. 点击 **"添加"**，令牌类型选 **"用户名"**，策略ID 填 `UserName`，安全策略选 **"无"**
6. 点击 **"确定"** → KepServer 提示重启 OPC UA 服务 → 点击 **"是"**

**常见错误配置：**
- ❌ 匿名登录未启用
- ❌ 所有端点都要求安全策略
- ❌ 客户端代码设置了错误的安全字符串
- ❌ 防火墙阻止了4840端口

**正确配置检查清单：**
- ✓ Allow Anonymous Login: Enabled
- ✓ 至少一个端点Security Policy为None
- ✓ OPC UA Server状态为Running
- ✓ 端口4840未被防火墙阻止
- ✓ Python客户端使用默认匿名连接

---

## 配置检查清单

在完成配置后，使用此清单验证：

- [ ] KepServer已安装并运行
- [ ] 创建了CodeSys Ethernet通道
- [ ] 添加了ProductionLine_PLC设备
- [ ] 设备连接测试成功
- [ ] 创建了所有必需的标签组
- [ ] 配置了所有标签映射
- [ ] 标签值正常更新
- [ ] 启用了OPC UA服务器
- [ ] OPC UA端点可访问
- [ ] Python客户端可以连接
- [ ] 可以读取标签值
- [ ] 可以写入标签值（可写标签）

---

## 下一步

配置完成后，您可以：

1. 启动数据采集程序
   ```
   cd python_client
   python main.py
   ```

2. 启动Web应用
   ```
   cd web_app
   python app.py
   ```

3. 访问监控界面
   - 打开浏览器访问：http://localhost:5000
   - 使用默认账户登录：admin / admin123

---

文档版本：1.0  
最后更新：2025-12-01
