# 数据库操作模块文档

## 概述

数据库操作模块提供了完整的数据持久化功能，包括能源数据存储、生产数据存储、报警数据存储和历史数据查询。该模块基于SQLAlchemy ORM实现，支持连接池管理、自动重连、批量插入优化和数据去重。

## 核心功能

### 1. 数据库管理类（DatabaseManager）

`DatabaseManager`类是数据库操作的核心，提供以下功能：

- 数据库连接管理（连接池、自动重连）
- 会话管理和事务处理
- 能源数据存储
- 生产数据存储
- 报警数据存储
- 历史数据查询（支持分页和聚合）

### 2. 主要方法

#### 2.1 连接管理

```python
# 连接数据库
db_manager = DatabaseManager(database_uri)
db_manager.connect(max_retries=3, retry_delay=5)

# 检查连接状态
if db_manager.is_connected():
    print("数据库已连接")

# 重新连接
db_manager.reconnect()

# 断开连接
db_manager.disconnect()
```

#### 2.2 能源数据存储

```python
# 保存单条能源数据
energy_data = [{
    'timestamp': datetime.utcnow(),
    'device_id': 'conveyor',
    'device_name': '传送带',
    'power_kw': 2.5,
    'energy_kwh': 15.3,
    'status': 'running'
}]

count = db_manager.save_energy_data(energy_data)
print(f"保存了 {count} 条记录")

# 批量保存能源数据（自动去重）
batch_data = [
    {'device_id': 'station1', 'power_kw': 3.0, ...},
    {'device_id': 'station2', 'power_kw': 4.5, ...},
]
count = db_manager.save_energy_data(batch_data)
```

**特性：**
- 支持批量插入优化
- 自动去重：10秒内相同设备的重复数据会被过滤
- 自动重试机制

#### 2.3 生产数据存储

```python
# 保存生产数据（包含OEE）
production_data = {
    'timestamp': datetime.utcnow(),
    'product_count': 100,
    'reject_count': 5,
    'runtime_seconds': 3600,
    'downtime_seconds': 300,
    'oee_percentage': 85.5,
    'availability': 92.3,
    'performance': 95.0,
    'quality': 95.0
}

success = db_manager.save_production_data(production_data)
```

#### 2.4 报警数据存储

```python
# 保存报警数据（自动去重）
alarm_data = {
    'timestamp': datetime.utcnow(),
    'device_id': 'station1',
    'alarm_type': 'power_exceeded',
    'alarm_level': 'warning',  # warning, critical, emergency
    'message': '工位1功率超过阈值',
    'threshold_value': 5.0,
    'actual_value': 5.8
}

success = db_manager.save_alarm(alarm_data)
```

**特性：**
- 报警去重：相同设备相同类型的报警在5分钟内只记录一次
- 只检查未确认的报警

#### 2.5 历史数据查询

```python
# 基础查询（支持分页）
result = db_manager.query_history(
    table_name='energy_data',
    start_time=datetime.utcnow() - timedelta(hours=1),
    end_time=datetime.utcnow(),
    device_id='conveyor',
    page=1,
    page_size=100
)

print(f"总记录数: {result['total']}")
print(f"当前页: {result['page']}/{result['total_pages']}")
print(f"数据: {result['data']}")

# 查询生产数据
result = db_manager.query_history(
    table_name='production_data',
    start_time=start_time,
    end_time=end_time
)

# 查询报警数据
result = db_manager.query_history(
    table_name='alarms',
    device_id='station1',
    page=1,
    page_size=50
)
```

**支持的表：**
- `energy_data` - 能源数据
- `production_data` - 生产数据
- `alarms` - 报警数据

#### 2.6 聚合查询

```python
# 按小时聚合能源数据（平均功率）
result = db_manager.query_history(
    table_name='energy_data',
    start_time=datetime.utcnow() - timedelta(days=7),
    end_time=datetime.utcnow(),
    device_id='conveyor',
    aggregate='avg',
    aggregate_interval='hour'
)

# 按天聚合生产数据（平均OEE）
result = db_manager.query_history(
    table_name='production_data',
    start_time=start_time,
    end_time=end_time,
    aggregate='avg',
    aggregate_interval='day'
)

# 按周统计报警数量
result = db_manager.query_history(
    table_name='alarms',
    start_time=start_time,
    end_time=end_time,
    aggregate='count',
    aggregate_interval='week'
)
```

**聚合类型：**
- `avg` - 平均值
- `sum` - 总和
- `max` - 最大值
- `min` - 最小值
- `count` - 计数

**聚合间隔：**
- `hour` - 按小时
- `day` - 按天
- `week` - 按周

## 数据模型

### EnergyData（能源数据）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigInteger | 主键 |
| timestamp | DateTime | 时间戳 |
| device_id | String(50) | 设备ID |
| device_name | String(100) | 设备名称 |
| power_kw | Decimal(10,3) | 功率(kW) |
| energy_kwh | Decimal(10,3) | 能耗(kWh) |
| status | String(20) | 状态 |

### ProductionData（生产数据）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigInteger | 主键 |
| timestamp | DateTime | 时间戳 |
| product_count | Integer | 产品计数 |
| reject_count | Integer | 不良品计数 |
| runtime_seconds | Integer | 运行时间（秒） |
| downtime_seconds | Integer | 停机时间（秒） |
| oee_percentage | Decimal(5,2) | OEE百分比 |
| availability | Decimal(5,2) | 可用率 |
| performance | Decimal(5,2) | 性能率 |
| quality | Decimal(5,2) | 质量率 |

### Alarm（报警记录）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigInteger | 主键 |
| timestamp | DateTime | 时间戳 |
| device_id | String(50) | 设备ID |
| alarm_type | String(50) | 报警类型 |
| alarm_level | String(20) | 报警级别 |
| message | Text | 报警消息 |
| threshold_value | Decimal(10,3) | 阈值 |
| actual_value | Decimal(10,3) | 实际值 |
| acknowledged | Boolean | 是否已确认 |
| acknowledged_by | String(50) | 确认人 |
| acknowledged_at | DateTime | 确认时间 |

## 性能优化

### 1. 连接池配置

```python
db_manager = DatabaseManager(
    database_uri,
    pool_size=10,        # 连接池大小
    max_overflow=20,     # 最大溢出连接数
    pool_timeout=30,     # 连接超时（秒）
    pool_recycle=3600    # 连接回收时间（秒）
)
```

### 2. 批量插入

能源数据支持批量插入，建议每10秒批量提交一次：

```python
# 收集10秒内的数据
data_buffer = []
for data in collected_data:
    data_buffer.append(data)

# 批量提交
if len(data_buffer) >= 10:
    db_manager.save_energy_data(data_buffer)
    data_buffer.clear()
```

### 3. 数据去重

- 能源数据：10秒内相同设备的重复数据自动过滤
- 报警数据：5分钟内相同设备相同类型的报警自动去重

### 4. 索引优化

数据表已创建以下索引：
- `energy_data`: `idx_timestamp`, `idx_device`, `idx_device_timestamp`
- `production_data`: `idx_timestamp`
- `alarms`: `idx_timestamp`, `idx_device`, `idx_alarm_device_timestamp`

## 错误处理

### 自动重试机制

所有数据库操作都支持自动重试：

```python
# 默认重试3次，每次延迟1秒
result = db_manager.execute_with_retry(
    func=lambda: some_database_operation(),
    max_retries=3,
    retry_delay=1
)
```

### 连接断开处理

当检测到连接断开时，系统会自动尝试重新连接：

```python
if not db_manager.is_connected():
    db_manager.reconnect(max_retries=5, retry_delay=5)
```

## 使用示例

完整的使用示例请参考 `example_database_operations.py` 文件。

### 快速开始

```python
from database import DatabaseManager
from config import config
from datetime import datetime

# 1. 创建数据库管理器
db_manager = DatabaseManager(config.DATABASE_URI)

# 2. 连接数据库
if db_manager.connect():
    # 3. 创建表
    db_manager.create_tables()
    
    # 4. 保存数据
    energy_data = [{
        'timestamp': datetime.utcnow(),
        'device_id': 'conveyor',
        'power_kw': 2.5,
        'energy_kwh': 15.3,
        'status': 'running'
    }]
    db_manager.save_energy_data(energy_data)
    
    # 5. 查询数据
    result = db_manager.query_history(
        table_name='energy_data',
        page=1,
        page_size=10
    )
    print(f"查询到 {result['total']} 条记录")
    
    # 6. 断开连接
    db_manager.disconnect()
```

## 配置说明

数据库配置在 `config.py` 中定义：

```python
# MySQL配置
DB_TYPE = 'mysql'
DB_HOST = 'localhost'
DB_PORT = 3306
DB_USER = 'root'
DB_PASSWORD = 'password'
DB_NAME = 'energy_management'

# SQLite配置（开发环境）
DB_TYPE = 'sqlite'
SQLITE_DB_PATH = 'energy_management.db'
```

## 日志记录

所有数据库操作都会记录日志：

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

日志级别：
- `INFO` - 正常操作信息
- `WARNING` - 报警和重试信息
- `ERROR` - 错误信息
- `DEBUG` - 调试信息（连接池事件等）

## 注意事项

1. **数据去重**：能源数据和报警数据都有自动去重机制，避免重复记录
2. **批量提交**：建议使用批量插入来提高性能
3. **连接池**：合理配置连接池大小，避免连接耗尽
4. **事务管理**：使用 `get_session()` 上下文管理器自动处理事务
5. **时间戳**：建议使用UTC时间，避免时区问题

## 故障排查

### 连接失败

```python
# 检查连接状态
if not db_manager.is_connected():
    # 查看连接池状态
    status = db_manager.get_pool_status()
    print(f"连接池状态: {status}")
    
    # 尝试重新连接
    db_manager.reconnect()
```

### 查询性能问题

1. 使用时间范围过滤减少查询数据量
2. 使用分页避免一次性加载大量数据
3. 使用聚合查询获取统计数据
4. 检查索引是否正确创建

### 数据重复

如果发现数据重复，检查：
1. 去重时间窗口是否合适
2. 时间戳是否准确
3. 设备ID是否一致

## 相关文件

- `database.py` - 数据库管理类实现
- `models.py` - 数据模型定义
- `config.py` - 配置文件
- `example_database_operations.py` - 使用示例
- `init_database.py` - 数据库初始化脚本
- `seed_data.py` - 测试数据生成脚本
