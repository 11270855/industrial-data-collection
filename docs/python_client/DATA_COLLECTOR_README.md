# 数据采集主程序使用指南

## 概述

`main.py` 是能源管理系统的核心数据采集程序，负责：
- 从OPC UA服务器（KepServer）采集设备数据
- 数据清洗和验证
- 批量存储到数据库
- 实时报警检测和处理
- OEE（设备综合效率）计算

## 功能特性

### 1. 模块集成
- **OPC UA客户端**：连接KepServer，订阅和读取设备数据
- **数据处理器**：数据清洗、异常检测、OEE计算
- **数据库管理器**：批量写入、连接池管理、自动重连
- **报警处理器**：阈值检查、报警触发、邮件通知

### 2. 数据采集
- 实时订阅OPC UA节点变化
- 定期轮询设备状态（1秒间隔）
- 批量写入数据库（10秒间隔）
- 生产数据和OEE计算（30秒间隔）

### 3. 可靠性保障
- 自动重连机制（OPC UA和数据库）
- 数据缓存和批量提交
- 优雅关闭，保存未提交数据
- 完整的日志记录和错误处理

## 安装依赖

```bash
cd python_client
pip install -r requirements.txt
```

## 配置

### 环境变量配置

创建 `.env` 文件或修改 `.env.example`：

```env
# OPC UA服务器配置
OPC_UA_SERVER_URL=opc.tcp://localhost:4840
OPC_UA_TIMEOUT=3
OPC_UA_RETRY_MAX=5
OPC_UA_RETRY_DELAY=5

# 数据库配置
DB_TYPE=mysql
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=energy_management

# 或使用SQLite（开发环境）
# DB_TYPE=sqlite
# SQLITE_DB_PATH=energy_management.db

# 数据采集配置
DATA_COLLECTION_INTERVAL=1
BATCH_WRITE_INTERVAL=10

# 报警配置
ALARM_CHECK_INTERVAL=5
ALARM_DUPLICATE_WINDOW=300
ALARM_CONSECUTIVE_COUNT=3

# 邮件通知配置（可选）
EMAIL_ENABLED=False
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
ALERT_EMAIL_TO=admin@example.com,operator@example.com

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/data_collector.log
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=5
```

## 使用方法

### 基本运行

```bash
python main.py
```

### 使用自定义配置文件

```bash
python main.py --config production.env
```

### 设置日志级别

```bash
python main.py --log-level DEBUG
```

### 测试连接

在正式运行前，可以测试OPC UA和数据库连接：

```bash
python main.py --test-connection
```

### 命令行参数

```
usage: main.py [-h] [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
               [--config CONFIG] [--test-connection]

能源管理系统数据采集程序

optional arguments:
  -h, --help            显示帮助信息
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        日志级别（覆盖配置文件中的设置）
  --config CONFIG       配置文件路径（.env文件）
  --test-connection     测试OPC UA和数据库连接后退出

示例:
  python main.py                    # 使用默认配置运行
  python main.py --log-level DEBUG  # 使用DEBUG日志级别
  python main.py --config custom.env # 使用自定义配置文件
```

## 运行流程

### 1. 启动阶段
1. 解析命令行参数
2. 加载配置文件
3. 配置日志系统
4. 初始化各模块：
   - 数据库管理器
   - 数据处理器
   - 报警处理器
   - OPC UA客户端
5. 加载阈值配置
6. 订阅OPC UA节点

### 2. 运行阶段（主循环）
1. **数据采集**（每1秒）：
   - 读取所有设备节点数据
   - 数据清洗和验证
   - 添加到缓存

2. **批量写入**（每10秒）：
   - 将缓存的能源数据批量写入数据库
   - 清空缓存

3. **生产数据采集**（每30秒）：
   - 读取生产统计数据
   - 计算OEE
   - 保存到数据库

4. **报警检测**（实时）：
   - 检查数据是否超过阈值
   - 连续异常判定（3次）
   - 触发报警并记录
   - 发送邮件通知（如果配置）

5. **连接监控**：
   - 检查OPC UA连接状态
   - 检查数据库连接状态
   - 自动重连

6. **配置更新**（每5分钟）：
   - 重新加载阈值配置

### 3. 关闭阶段
1. 接收关闭信号（Ctrl+C 或 SIGTERM）
2. 保存未提交的数据
3. 断开OPC UA连接
4. 关闭数据库连接
5. 记录关闭日志

## 日志管理

### 日志文件位置
默认：`logs/data_collector.log`

### 日志轮转
- 单个日志文件最大：10MB
- 保留备份数量：5个
- 自动压缩旧日志

### 日志级别
- **DEBUG**：详细的调试信息
- **INFO**：一般信息（默认）
- **WARNING**：警告信息
- **ERROR**：错误信息
- **CRITICAL**：严重错误

### 查看日志

```bash
# 实时查看日志
tail -f logs/data_collector.log

# 查看最近100行
tail -n 100 logs/data_collector.log

# 搜索错误
grep ERROR logs/data_collector.log
```

## 监控和维护

### 进程管理

#### Windows
```batch
# 启动（后台运行）
start /B python main.py > logs/output.log 2>&1

# 查找进程
tasklist | findstr python

# 停止进程
taskkill /F /IM python.exe
```

#### Linux
```bash
# 启动（后台运行）
nohup python main.py > logs/output.log 2>&1 &

# 查看进程
ps aux | grep main.py

# 停止进程
kill -TERM <PID>
```

### 性能监控

程序会在日志中记录：
- 数据采集频率
- 批量写入记录数
- 连接状态
- 报警触发情况

### 常见问题

#### 1. OPC UA连接失败
- 检查KepServer是否运行
- 验证服务器地址和端口
- 检查防火墙设置
- 查看OPC UA服务器日志

#### 2. 数据库连接失败
- 检查数据库服务是否运行
- 验证连接参数（主机、端口、用户名、密码）
- 确认数据库已创建
- 检查网络连接

#### 3. 数据未写入
- 检查数据清洗是否通过
- 查看日志中的错误信息
- 验证数据表是否存在
- 检查数据库权限

#### 4. 报警未触发
- 确认阈值配置已加载
- 检查连续异常次数设置
- 验证报警去重时间窗口
- 查看报警历史记录

#### 5. 邮件通知失败
- 确认EMAIL_ENABLED=True
- 检查SMTP服务器配置
- 验证邮箱账号和密码
- 查看邮件服务器日志

## 性能优化建议

1. **批量写入间隔**：根据数据量调整BATCH_WRITE_INTERVAL
2. **连接池大小**：根据并发需求调整数据库连接池
3. **日志级别**：生产环境使用INFO或WARNING
4. **数据保留**：定期清理历史数据
5. **索引优化**：为常用查询字段添加索引

## 安全建议

1. **配置文件**：不要将.env文件提交到版本控制
2. **密码管理**：使用环境变量或密钥管理服务
3. **网络安全**：使用VPN或防火墙限制访问
4. **日志脱敏**：避免在日志中记录敏感信息
5. **权限控制**：使用最小权限原则配置数据库用户

## 扩展开发

### 添加新设备

1. 在`config.py`的`OPC_UA_NODES`中添加设备配置
2. 更新数据采集逻辑（如需要）
3. 添加对应的阈值配置

### 自定义报警规则

1. 在`alarm_handler.py`中扩展`check_thresholds`方法
2. 添加新的报警级别判定逻辑
3. 自定义邮件模板

### 集成其他数据源

1. 创建新的客户端类（参考`opcua_client.py`）
2. 在`DataCollector`中集成新模块
3. 更新主循环逻辑

## 相关文档

- [OPC UA客户端文档](OPCUA_CLIENT_README.md)
- [数据处理器文档](DATA_PROCESSOR_README.md)
- [数据库操作文档](DATABASE_OPERATIONS_README.md)
- [报警处理器文档](ALARM_HANDLER_README.md)
- [快速开始指南](QUICK_START.md)

## 技术支持

如有问题，请查看：
1. 日志文件：`logs/data_collector.log`
2. 项目文档：`README.md`
3. 配置示例：`.env.example`
