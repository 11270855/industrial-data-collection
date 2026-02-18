# 虚拟 PLC 与 KepServer 连接配置指南

## 📋 系统架构

本系统使用 **CodeSys 虚拟 PLC** 进行仿真，而不是真实的硬件 PLC。

```
┌─────────────────────────────────────────────────────────┐
│                    本地计算机                            │
│                                                          │
│  ┌──────────────┐      ┌──────────────┐                │
│  │  CodeSys     │      │  KepServer   │                │
│  │  Development │      │  EX          │                │
│  │  System      │      │              │                │
│  └──────┬───────┘      └──────┬───────┘                │
│         │                     │                         │
│         │ 编程/监控            │ OPC UA                  │
│         │                     │ (端口 4840)             │
│         ↓                     ↓                         │
│  ┌─────────────────────────────────────┐               │
│  │  CODESYS Control Win V3             │               │
│  │  (虚拟 PLC / 仿真软件)               │               │
│  │  IP: 127.0.0.1                      │               │
│  │  Port: 1217                         │               │
│  └─────────────────────────────────────┘               │
│                     ↑                                   │
│                     │ TCP/IP                            │
│                     │ (本地回环)                         │
└─────────────────────┼───────────────────────────────────┘
                      │
              ┌───────┴────────┐
              │  Python 客户端  │
              │  数据采集程序   │
              └────────────────┘
```

## 🎯 关键概念

### 虚拟 PLC（CODESYS Control Win V3）

- **作用**：在 Windows 上模拟真实 PLC 的运行环境
- **优点**：
  - 无需购买硬件 PLC
  - 开发和测试更方便
  - 完全模拟真实 PLC 行为
- **运行方式**：作为 Windows 服务在后台运行
- **通信地址**：`127.0.0.1:1217`（本地回环）

### KepServer 的角色

- **作用**：作为 OPC UA 服务器，连接虚拟 PLC 并提供标准化数据接口
- **连接方式**：通过 CodeSys Ethernet 驱动连接到虚拟 PLC
- **提供服务**：OPC UA 端点 `opc.tcp://localhost:4840`

---

## 🔧 配置步骤

### 第一步：配置 CodeSys 虚拟 PLC

#### 1. 确认虚拟 PLC 已安装

检查是否安装了 **CODESYS Control Win V3**：

```
开始菜单 → 搜索 "CODESYS Control Win"
```

如果没有，需要从 CODESYS Store 下载安装。

#### 2. 启动虚拟 PLC 服务

```
Win+R → services.msc → 回车
找到：CODESYS Control Win V3 Service
右键 → 启动
```

#### 3. 配置项目网络设置

在 CodeSys Development System 中：

1. 打开项目
2. 双击 `Device (CODESYS Control Win V3)`
3. 在 `Communication Settings` 中：
   ```
   IP Address: 127.0.0.1
   Port: 1217
   ```

#### 4. 编译并下载程序

```
F11 - 编译
Alt+F8 - 登录
F5 - 启动
```

#### 5. 验证虚拟 PLC 运行

在 CodeSys 中应该看到：
- 状态栏显示 `RUN`
- 变量值在更新
- 无连接错误

---

### 第二步：配置 KepServer 连接虚拟 PLC

#### 1. 创建通道

1. 打开 KepServer Configuration
2. 右键 `Connectivity` → `New Channel`
3. 选择驱动：`CodeSys Ethernet`
4. 通道名称：`Virtual_PLC_Channel`
5. 保持默认设置

#### 2. 添加设备

1. 右键 `Virtual_PLC_Channel` → `New Device`
2. 配置设备：
   ```
   Model: CodeSys V3.x
   Name: VirtualPLC
   IP Address: 127.0.0.1  ← 重要！使用本地回环地址
   Port: 1217             ← CodeSys 默认端口
   ```

#### 3. 测试连接

1. 右键设备 `VirtualPLC` → `Properties`
2. 点击 `Communications` → `Test Connection`
3. 应该显示：`Connection Successful`

**如果连接失败**：
- 检查虚拟 PLC 服务是否运行
- 检查 CodeSys 程序是否在 RUN 状态
- 检查防火墙设置

#### 4. 配置标签

创建标签映射 PLC 变量，例如：

| 标签名 | PLC 地址 | 数据类型 |
|--------|----------|----------|
| `EnergyData.TotalPower` | `PLC_PRG.rTotalPower` | Float |
| `EnergyData.TotalEnergy` | `PLC_PRG.rTotalEnergy` | Float |
| `Production.ProductCount` | `PLC_PRG.iProductCount` | Word |

详细标签配置参考 `docs/KEPSERVER_SETUP.md`

#### 5. 启用 OPC UA 服务器

1. 菜单：`Settings` → `OPC UA Configuration`
2. 配置：
   ```
   ✅ Enable OPC UA Server
   ✅ Allow Anonymous Login
   Endpoint: opc.tcp://localhost:4840
   Security Policy: None
   ```

---

### 第三步：验证完整连接

#### 1. 使用 KepServer Quick Client 测试

```
Tools → Quick Client
Server URL: opc.tcp://localhost:4840
Connect → 应该能看到 VirtualPLC 设备和所有标签
```

#### 2. 使用 Python 客户端测试

```bash
cd python_client
python main.py --test-connection
```

应该看到：
```
✓ 数据库连接成功
✓ OPC UA连接成功
```

---

## 🔍 连接验证清单

完成配置后，按顺序检查：

### 1. 虚拟 PLC 层

- [ ] CODESYS Control Win V3 服务正在运行
- [ ] CodeSys 项目已编译无错误
- [ ] 程序已下载到虚拟 PLC
- [ ] 程序状态为 RUN
- [ ] 变量值在 CodeSys 中正常更新

### 2. KepServer 层

- [ ] KepServer 正在运行
- [ ] 创建了 CodeSys Ethernet 通道
- [ ] 设备 IP 配置为 127.0.0.1
- [ ] 设备端口配置为 1217
- [ ] 设备连接测试成功（绿色图标）
- [ ] 标签已配置并显示正常值

### 3. OPC UA 层

- [ ] OPC UA 服务器已启用
- [ ] 端点为 opc.tcp://localhost:4840
- [ ] Quick Client 可以连接
- [ ] 可以读取标签值

### 4. Python 客户端层

- [ ] .env 配置正确（OPC_UA_SERVER_URL=opc.tcp://localhost:4840）
- [ ] Python 测试连接成功
- [ ] 可以读取 OPC UA 数据

---

## ❌ 常见问题

### 问题 1：KepServer 无法连接到虚拟 PLC

**错误**：设备图标显示红色，状态 `Failed`

**原因**：虚拟 PLC 未运行或网络配置错误

**解决方案**：

1. **检查虚拟 PLC 服务**：
   ```
   services.msc → CODESYS Control Win V3 Service → 确认 Running
   ```

2. **检查 CodeSys 程序状态**：
   - 打开 CodeSys
   - 确认程序状态为 `RUN`（不是 STOP）
   - 如果是 STOP，按 F5 启动

3. **检查 IP 和端口**：
   - KepServer 设备 IP：`127.0.0.1`
   - KepServer 设备端口：`1217`
   - 不要使用其他 IP 地址

4. **检查防火墙**：
   ```
   临时关闭 Windows 防火墙测试
   如果可以连接，添加例外规则
   ```

### 问题 2：Python 客户端连接超时

**错误**：`[WinError 10061] 由于目标计算机积极拒绝，无法连接`

**原因**：OPC UA 服务器未启用或端口错误

**解决方案**：

1. **检查 KepServer OPC UA 服务器**：
   ```
   Settings → OPC UA Configuration
   确认 "Enable OPC UA Server" 已勾选
   ```

2. **检查端点 URL**：
   ```
   KepServer: opc.tcp://localhost:4840
   .env 文件: OPC_UA_SERVER_URL=opc.tcp://localhost:4840
   ```

3. **检查端口占用**：
   ```cmd
   netstat -ano | findstr :4840
   ```
   如果端口被占用，关闭占用程序或更改端口

### 问题 3：标签值不更新

**错误**：KepServer 中标签显示 `Bad Quality`

**原因**：标签地址配置错误或 PLC 变量不存在

**解决方案**：

1. **检查标签地址**：
   - 在 CodeSys 中确认变量名称
   - 注意大小写（区分大小写）
   - 格式：`PLC_PRG.变量名`

2. **检查数据类型匹配**：
   - KepServer 标签类型必须与 PLC 变量类型匹配
   - REAL → Float
   - INT → Word
   - BOOL → Boolean

3. **检查扫描率**：
   - 标签扫描率不要太快
   - 建议：≥ 500ms

### 问题 4：虚拟 PLC 服务无法启动

**错误**：服务启动失败或立即停止

**原因**：权限不足或端口冲突

**解决方案**：

1. **以管理员身份运行**：
   - 右键 CodeSys → 以管理员身份运行
   - 重新下载程序到虚拟 PLC

2. **检查端口占用**：
   ```cmd
   netstat -ano | findstr :1217
   ```
   如果被占用，关闭占用程序

3. **重新安装虚拟 PLC**：
   - 卸载 CODESYS Control Win V3
   - 重新安装
   - 重启计算机

---

## 🚀 快速诊断命令

### 检查虚拟 PLC 服务

```cmd
sc query "CODESYS Control Win V3 Service"
```

应该显示：`STATE: 4 RUNNING`

### 检查端口监听

```cmd
netstat -ano | findstr :1217
netstat -ano | findstr :4840
```

应该看到两个端口都在监听

### 测试本地连接

```cmd
ping 127.0.0.1
```

应该有响应（<1ms）

---

## 📊 网络拓扑

### 本地回环通信

```
应用层:
  Python 客户端 ←→ OPC UA (端口 4840) ←→ KepServer

中间层:
  KepServer ←→ CodeSys Ethernet (端口 1217) ←→ 虚拟 PLC

底层:
  所有通信都在 127.0.0.1 (本地回环) 上进行
```

### 端口使用

| 端口 | 用途 | 协议 |
|------|------|------|
| 1217 | CodeSys 虚拟 PLC 通信 | TCP |
| 4840 | OPC UA 服务器 | TCP |
| 3306 | MySQL 数据库 | TCP |
| 5000 | Flask Web 应用 | HTTP |

---

## 💡 最佳实践

### 开发环境配置

1. **使用本地回环地址**：
   - 所有组件都在同一台机器上
   - 使用 `127.0.0.1` 避免网络问题

2. **禁用安全策略**（开发环境）：
   - OPC UA: `Security Policy = None`
   - OPC UA: `Allow Anonymous Login = True`

3. **合理设置扫描率**：
   - 控制变量：500ms - 1s
   - 能源数据：1s
   - 统计数据：2s - 5s

### 生产环境配置

1. **启用安全策略**：
   - OPC UA: `Security Policy = Basic256Sha256`
   - 配置用户认证

2. **使用实际 IP 地址**：
   - 如果部署到服务器，使用实际 IP

3. **配置防火墙规则**：
   - 只开放必要的端口
   - 限制访问来源

---

## 📖 相关文档

- **CodeSys 配置**：`CODESYS_SETUP_GUIDE.md`
- **KepServer 配置**：`KEPSERVER_QUICK_SETUP.md`
- **完整系统配置**：`README.md`

---

## 🆘 需要帮助？

如果遇到问题：

1. 按照验证清单逐项检查
2. 查看日志文件：
   - KepServer: `View` → `Event Log`
   - Python: `logs/data_collector.log`
3. 参考故障排查部分
4. 检查所有服务是否运行

---

文档版本：1.0  
最后更新：2025-12-15
