# KepServer配置指南

本文档详细说明如何配置KepServerEX以连接CodeSys PLC并启用OPC UA服务器，实现能源管理系统的数据通信。

## 目录

1. [前提条件](#前提条件)
2. [KepServer安装](#kepserver安装)
3. [创建通道](#创建通道)
4. [添加设备](#添加设备)
5. [配置标签](#配置标签)
6. [启用OPC UA服务器](#启用opc-ua服务器)
7. [测试连接](#测试连接)
8. [故障排查](#故障排查)

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

## KepServer安装

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

标签映射PLC中的变量，使其可通过OPC UA访问。

### 标签命名规范

格式：分组.变量名

例如：DeviceControl.ConveyorStart

### 创建标签组

为了组织标签，我们创建以下标签组：

1. DeviceControl - 设备控制变量
2. SensorInput - 传感器输入
3. EnergyData - 能源数据
4. Production - 生产统计
5. SystemStatus - 系统状态

#### 创建标签组步骤

1. 右键点击设备"ProductionLine_PLC"
2. 选择"New Tag"
3. 在"Name"字段输入组名（如DeviceControl）
4. 在"Data Type"选择"Group"
5. 点击"OK"

### 配置标签映射

以下是完整的标签配置表：

#### 1. DeviceControl（设备控制）

| 标签名称 | PLC变量 | 数据类型 | 访问权限 | 扫描率(ms) |
|---------|---------|---------|---------|-----------|
| ConveyorStart | PLC_PRG.bConveyorStart | Boolean | Read/Write | 1000 |
| ConveyorSpeed | PLC_PRG.rConveyorSpeed | Float | Read/Write | 1000 |
| Station1Active | PLC_PRG.bStation1Active | Boolean | Read/Write | 1000 |
| Station2Active | PLC_PRG.bStation2Active | Boolean | Read/Write | 1000 |
| RejectActive | PLC_PRG.bRejectActive | Boolean | Read Only | 1000 |
| SystemStart | PLC_PRG.bSystemStart | Boolean | Read/Write | 1000 |
| SystemStop | PLC_PRG.bSystemStop | Boolean | Read/Write | 1000 |
| EmergencyStop | PLC_PRG.bEmergencyStop | Boolean | Read/Write | 500 |

#### 2. SensorInput（传感器输入）

| 标签名称 | PLC变量 | 数据类型 | 访问权限 | 扫描率(ms) |
|---------|---------|---------|---------|-----------|
| ProductSensor1 | PLC_PRG.bProductSensor1 | Boolean | Read Only | 500 |
| ProductSensor2 | PLC_PRG.bProductSensor2 | Boolean | Read Only | 500 |
| QualitySensor | PLC_PRG.bQualitySensor | Boolean | Read Only | 500 |

#### 3. EnergyData（能源数据）

| 标签名称 | PLC变量 | 数据类型 | 访问权限 | 扫描率(ms) |
|---------|---------|---------|---------|-----------|
| ConveyorPower | PLC_PRG.rConveyorPower | Float | Read Only | 1000 |
| Station1Power | PLC_PRG.rStation1Power | Float | Read Only | 1000 |
| Station2Power | PLC_PRG.rStation2Power | Float | Read Only | 1000 |
| TotalPower | PLC_PRG.rTotalPower | Float | Read Only | 1000 |
| TotalEnergy | PLC_PRG.rTotalEnergy | Float | Read Only | 1000 |
| EnergyAlarm | PLC_PRG.bEnergyAlarm | Boolean | Read Only | 1000 |

#### 4. Production（生产统计）

| 标签名称 | PLC变量 | 数据类型 | 访问权限 | 扫描率(ms) |
|---------|---------|---------|---------|-----------|
| ProductCount | PLC_PRG.iProductCount | Word | Read Only | 1000 |
| RejectCount | PLC_PRG.iRejectCount | Word | Read Only | 1000 |
| RunTime | PLC_PRG.iRunTimeSeconds | DWord | Read Only | 1000 |
| DownTime | PLC_PRG.iDownTimeSeconds | DWord | Read Only | 1000 |

#### 5. SystemStatus（系统状态）

| 标签名称 | PLC变量 | 数据类型 | 访问权限 | 扫描率(ms) |
|---------|---------|---------|---------|-----------|
| SystemState | PLC_PRG.eSystemState | Word | Read Only | 1000 |
| SystemFault | PLC_PRG.bSystemFault | Boolean | Read Only | 500 |
| SystemStatus | PLC_PRG.sSystemStatus | String | Read Only | 2000 |

### 创建单个标签步骤

以DeviceControl.ConveyorStart为例：

1. 创建标签
   - 右键点击"DeviceControl"标签组
   - 选择"New Tag"

2. 配置标签属性
   - Name: ConveyorStart
   - Address: PLC_PRG.bConveyorStart
   - Data Type: Boolean
   - Client Access: Read/Write
   - Scan Rate: 1000 ms

3. 保存标签
   - 点击"OK"

4. 验证标签
   - 标签应显示为绿色
   - 在"Tag"列中应显示当前值

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
   - Allow Anonymous Login: Enabled（允许匿名访问，开发环境）
   - Security Policy: None（无安全策略，开发环境）

生产环境建议：
- 禁用匿名登录
- 启用用户名/密码认证
- 使用安全策略（Basic256Sha256）

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
