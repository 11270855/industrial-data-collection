# 报警处理模块说明

## 概述

报警处理模块（`alarm_handler.py`）实现了能源管理系统的报警逻辑管理、阈值检查和邮件通知功能。

## 主要功能

### 1. AlarmHandler 类

报警处理器的核心类，负责管理所有报警相关的逻辑。

#### 初始化

```python
from alarm_handler import AlarmHandler
from database import DatabaseManager
from config import config

db_manager = DatabaseManager(config.DATABASE_URI)
db_manager.connect()

alarm_handler = AlarmHandler(db_manager, config)
```

### 2. 阈值检查 (check_thresholds)

检查设备数据是否超过配置的阈值。

**特性：**
- 支持多参数阈值检查
- 连续异常检测：需要连续N次（默认3次）超过阈值才触发报警
- 自动报警去重：相同设备相同类型的报警在时间窗口内（默认5分钟）只触发一次

**使用示例：**

```python
# 设备数据
device_data = {
    'device_id': 'conveyor',
    'device_name': '传送带',
    'power_kw': 6.5,
    'energy_kwh': 15.3,
    'status': 'running',
    'timestamp': datetime.utcnow()
}

# 阈值配置
thresholds = [
    {
        'device_id': 'conveyor',
        'parameter_name': 'power_kw',
        'threshold_value': 5.0,
        'alarm_level': 'warning',
        'enabled': True
    }
]

# 检查阈值
alarms = alarm_handler.check_thresholds(device_data, thresholds)
```

### 3. 触发报警 (trigger_alarm)

触发报警并记录到数据库。

**特性：**
- 自动判定报警级别（warning/critical/emergency）
- 格式化报警消息
- 保存到数据库
- 可选的邮件通知

**使用示例：**

```python
alarm_data = {
    'timestamp': datetime.utcnow(),
    'device_id': 'conveyor',
    'device_name': '传送带',
    'alarm_type': 'power_kw_threshold',
    'alarm_level': 'warning',
    'parameter_name': 'power_kw',
    'threshold_value': 5.0,
    'actual_value': 6.5,
    'message': '设备传送带的power_kw超过阈值'
}

success = alarm_handler.trigger_alarm(alarm_data)
```

### 4. 报警级别判定

系统根据超出阈值的程度自动判定报警级别：

- **warning（警告）**：超出阈值 < 20%
- **critical（严重）**：超出阈值 20% - 50%
- **emergency（紧急）**：超出阈值 ≥ 50%

### 5. 邮件通知 (send_email_notification)

当配置了邮件通知时，自动发送报警邮件。

**配置要求：**

在 `.env` 文件中配置以下参数：

```env
EMAIL_ENABLED=True
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
ALERT_EMAIL_TO=recipient1@example.com,recipient2@example.com
```

**邮件内容：**
- 支持纯文本和HTML两种格式
- 包含报警时间、设备信息、报警级别、阈值和实际值
- 根据报警级别使用不同的颜色标识

### 6. 批量处理报警 (process_alarms)

批量处理多个报警。

```python
alarms = [alarm1, alarm2, alarm3]
success_count = alarm_handler.process_alarms(alarms)
```

### 7. 报警统计 (get_alarm_statistics)

获取报警统计信息。

```python
from datetime import datetime, timedelta

# 获取最近24小时的报警统计
start_time = datetime.utcnow() - timedelta(hours=24)
stats = alarm_handler.get_alarm_statistics(start_time=start_time)

# 返回结果示例：
# {
#     'total': 15,
#     'by_level': {'warning': 10, 'critical': 4, 'emergency': 1},
#     'by_device': {'conveyor': 8, 'station1': 5, 'station2': 2},
#     'acknowledged_count': 5,
#     'unacknowledged_count': 10
# }
```

## 配置参数

在 `config.py` 中可以配置以下参数：

```python
# 报警配置
ALARM_CHECK_INTERVAL = 5           # 报警检查间隔（秒）
ALARM_DUPLICATE_WINDOW = 300       # 报警去重时间窗口（秒）
ALARM_CONSECUTIVE_COUNT = 3        # 连续异常次数触发报警

# 邮件通知配置
EMAIL_ENABLED = False              # 是否启用邮件通知
SMTP_SERVER = 'smtp.gmail.com'     # SMTP服务器地址
SMTP_PORT = 587                    # SMTP端口
SMTP_USER = ''                     # SMTP用户名
SMTP_PASSWORD = ''                 # SMTP密码
ALERT_EMAIL_TO = []                # 收件人邮箱列表
```

## 测试

运行测试脚本验证功能：

```bash
cd python_client
python test_alarm_handler.py
```

测试脚本会验证：
1. 数据库连接
2. 报警处理器初始化
3. 阈值检查功能（包括连续计数逻辑）
4. 报警触发和数据库保存
5. 报警统计功能
6. 邮件通知功能（如果启用）

## 集成示例

在数据采集主程序中集成报警处理：

```python
from opcua_client import OPCUAClient
from database import DatabaseManager
from alarm_handler import AlarmHandler
from config import config
import time

# 初始化
db_manager = DatabaseManager(config.DATABASE_URI)
db_manager.connect()

alarm_handler = AlarmHandler(db_manager, config)

# 从数据库加载阈值配置
with db_manager.get_session() as session:
    from models import Threshold
    thresholds = session.query(Threshold).filter(Threshold.enabled == True).all()
    threshold_list = [t.to_dict() for t in thresholds]

# 数据采集循环
while True:
    # 采集设备数据
    device_data = {
        'device_id': 'conveyor',
        'device_name': '传送带',
        'power_kw': read_power_from_plc(),
        'timestamp': datetime.utcnow()
    }
    
    # 检查阈值
    alarms = alarm_handler.check_thresholds(device_data, threshold_list)
    
    # 处理报警
    if alarms:
        alarm_handler.process_alarms(alarms)
    
    time.sleep(config.ALARM_CHECK_INTERVAL)
```

## 注意事项

1. **连续异常检测**：为避免误报，系统需要连续N次检测到超过阈值才会触发报警
2. **报警去重**：相同设备相同类型的报警在时间窗口内只会记录一次
3. **邮件配置**：使用Gmail时需要启用"应用专用密码"，不能使用普通密码
4. **数据库依赖**：报警处理器依赖数据库管理器，确保数据库连接正常
5. **线程安全**：当前实现不是线程安全的，多线程环境下需要添加锁机制

## 需求追溯

本模块实现了以下需求：

- **需求 7.1**：允许用户为每个设备设置能耗阈值
- **需求 7.2**：设备能耗超过阈值时在Web界面显示实时报警信息
- **需求 7.3**：触发报警时记录报警事件到数据库
- **需求 7.5**：WHERE 配置了邮件通知功能，向指定邮箱发送报警通知

## 相关文件

- `alarm_handler.py` - 报警处理模块主文件
- `test_alarm_handler.py` - 测试脚本
- `models.py` - 数据模型（Alarm, Threshold）
- `database.py` - 数据库管理器
- `config.py` - 配置文件
