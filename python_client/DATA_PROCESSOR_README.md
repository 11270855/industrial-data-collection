# 数据处理模块 (DataProcessor)

## 概述

数据处理模块提供了完整的工业数据处理功能，包括数据清洗、异常检测和OEE（设备综合效率）计算。该模块是能源管理系统的核心组件之一，确保数据质量和准确性。

## 功能特性

### 1. 数据清洗 (Data Cleaning)

- **过滤无效和空值**：自动识别并过滤掉空值、None值和无效数据
- **数据类型验证和转换**：确保数据类型正确，自动转换为合适的类型
- **数值范围检查**：验证功率、能耗等数值是否在合理范围内
- **时间戳标准化**：支持多种时间格式，统一转换为标准datetime对象

### 2. 异常检测 (Anomaly Detection)

- **阈值比较**：支持大于/小于阈值的比较
- **连续异常判定**：只有连续N次（默认3次）超过阈值才触发报警，避免误报
- **历史记录管理**：维护每个设备每个参数的异常历史
- **统计信息**：提供异常检测的统计数据

### 3. OEE计算 (Overall Equipment Effectiveness)

- **可用率计算**：运行时间 / 计划生产时间
- **性能率计算**：(实际产量 × 理想节拍时间) / 运行时间
- **质量率计算**：合格品数量 / 总产量
- **总OEE计算**：可用率 × 性能率 × 质量率

## 安装和配置

### 依赖项

```bash
# 已包含在 requirements.txt 中
pip install python-dotenv
```

### 配置参数

在 `config.py` 中配置数据验证范围：

```python
DATA_VALIDATION = {
    'power_min': 0.0,
    'power_max': 100.0,      # kW
    'energy_min': 0.0,
    'energy_max': 10000.0,   # kWh
    'speed_min': 0.0,
    'speed_max': 5.0,        # m/s
}

# 连续异常次数阈值
ALARM_CONSECUTIVE_COUNT = 3
```

## 使用方法

### 基本使用

```python
from data_processor import DataProcessor
from config import config

# 创建数据处理器实例
processor = DataProcessor(config)
```

### 1. 数据清洗

```python
# 原始数据
raw_data = {
    'timestamp': '2025-12-01 10:30:00',
    'device_id': 'conveyor',
    'device_name': '传送带',
    'power_kw': 2.5,
    'energy_kwh': 15.3,
    'status': 'running'
}

# 清洗数据
cleaned_data = processor.clean_data(raw_data)

if cleaned_data:
    print(f"清洗成功: {cleaned_data}")
else:
    print("数据无效")
```

**清洗规则：**
- 必需字段：`device_id`
- 自动添加时间戳（如果缺失）
- 数值范围验证
- 字符串去空格和标准化

### 2. 异常检测

```python
# 检测功率异常
is_alarm = processor.detect_anomaly(
    device_id='conveyor',
    parameter='power_kw',
    value=6.5,              # 当前功率值
    threshold=5.0,          # 阈值
    comparison='greater'    # 比较方式：'greater' 或 'less'
)

if is_alarm:
    print("触发报警！连续异常超过阈值")
else:
    print("正常或未达到连续异常阈值")
```

**异常判定逻辑：**
- 只有连续N次（默认3次）超过阈值才返回True
- 支持两种比较方式：大于阈值（greater）和小于阈值（less）
- 自动维护每个设备每个参数的历史记录

### 3. OEE计算

```python
# 计算OEE
oee_result = processor.calculate_oee(
    runtime_seconds=7200,      # 运行时间（秒）
    downtime_seconds=800,      # 停机时间（秒）
    product_count=600,         # 总产量
    reject_count=12,           # 不良品数量
    ideal_cycle_time=10.0      # 理想节拍时间（秒/件）
)

print(f"可用率: {oee_result['availability']}%")
print(f"性能率: {oee_result['performance']}%")
print(f"质量率: {oee_result['quality']}%")
print(f"总OEE: {oee_result['oee']}%")
```

**OEE计算公式：**
```
可用率 = 运行时间 / (运行时间 + 停机时间) × 100%
性能率 = (实际产量 × 理想节拍时间) / 运行时间 × 100%
质量率 = (总产量 - 不良品) / 总产量 × 100%
OEE = 可用率 × 性能率 × 质量率 / 100
```

### 4. 批量处理

```python
# 批量清洗数据
raw_data_list = [
    {'device_id': 'conveyor', 'power_kw': 2.5},
    {'device_id': 'station1', 'power_kw': 4.2},
    {'device_id': 'station2', 'power_kw': 150.0},  # 超范围，会被过滤
]

cleaned_list = processor.batch_clean_data(raw_data_list)
print(f"有效数据: {len(cleaned_list)}条")
```

### 5. 管理异常历史

```python
# 重置所有设备的异常历史
processor.reset_anomaly_history()

# 重置特定设备的异常历史
processor.reset_anomaly_history(device_id='conveyor')

# 重置特定设备特定参数的异常历史
processor.reset_anomaly_history(device_id='conveyor', parameter='power_kw')

# 获取异常统计信息
stats = processor.get_anomaly_statistics()
print(stats)
```

## API参考

### DataProcessor类

#### `__init__(config=None)`
初始化数据处理器

**参数：**
- `config`: 配置对象（可选）

#### `clean_data(raw_data: Dict) -> Optional[Dict]`
清洗单条数据

**参数：**
- `raw_data`: 原始数据字典

**返回：**
- 清洗后的数据字典，如果无效则返回None

#### `detect_anomaly(device_id, parameter, value, threshold, comparison='greater') -> bool`
检测异常

**参数：**
- `device_id`: 设备ID
- `parameter`: 参数名称
- `value`: 当前值
- `threshold`: 阈值
- `comparison`: 比较方式（'greater' 或 'less'）

**返回：**
- 是否触发报警（连续异常达到阈值）

#### `calculate_oee(runtime_seconds, downtime_seconds, product_count, reject_count, ideal_cycle_time=10.0) -> Dict`
计算OEE

**参数：**
- `runtime_seconds`: 运行时间（秒）
- `downtime_seconds`: 停机时间（秒）
- `product_count`: 总产量
- `reject_count`: 不良品数量
- `ideal_cycle_time`: 理想节拍时间（秒/件），默认10.0

**返回：**
- 包含OEE及其组成部分的字典

#### `batch_clean_data(raw_data_list: List[Dict]) -> List[Dict]`
批量清洗数据

**参数：**
- `raw_data_list`: 原始数据列表

**返回：**
- 清洗后的数据列表

#### `reset_anomaly_history(device_id=None, parameter=None)`
重置异常历史记录

**参数：**
- `device_id`: 设备ID（可选）
- `parameter`: 参数名称（可选）

#### `get_anomaly_statistics() -> Dict`
获取异常检测统计信息

**返回：**
- 统计信息字典

## 数据格式

### 输入数据格式

```python
{
    'timestamp': '2025-12-01 10:30:00',  # 可选，支持多种格式
    'device_id': 'conveyor',              # 必需
    'device_name': '传送带',              # 可选
    'power_kw': 2.5,                      # 可选
    'energy_kwh': 15.3,                   # 可选
    'speed': 3.0,                         # 可选
    'status': 'running',                  # 可选
    'product_count': 100,                 # 可选
    'reject_count': 5,                    # 可选
    'runtime_seconds': 3600,              # 可选
    'downtime_seconds': 300               # 可选
}
```

### 输出数据格式

```python
{
    'timestamp': datetime.datetime(2025, 12, 1, 10, 30),
    'device_id': 'conveyor',
    'device_name': '传送带',
    'power_kw': Decimal('2.5'),
    'energy_kwh': Decimal('15.3'),
    'status': 'running'
}
```

## 示例程序

运行示例程序查看完整功能演示：

```bash
cd python_client
python example_data_processor_usage.py
```

示例程序包含：
1. 数据清洗示例
2. 异常检测示例
3. OEE计算示例
4. 批量数据处理示例

## 日志记录

模块使用Python标准logging库记录日志：

```python
import logging

# 配置日志级别
logging.basicConfig(level=logging.INFO)

# 或使用配置文件中的设置
logger = logging.getLogger(__name__)
```

**日志级别：**
- `DEBUG`: 详细的调试信息
- `INFO`: 一般信息
- `WARNING`: 警告信息（如数据超范围）
- `ERROR`: 错误信息

## 性能考虑

- **批量处理**：使用`batch_clean_data()`处理大量数据更高效
- **内存管理**：异常历史使用`deque`限制长度，避免内存泄漏
- **数值精度**：使用`Decimal`类型保持数值精度

## 错误处理

所有方法都包含异常处理：
- 数据清洗失败返回None
- 异常检测失败返回False
- OEE计算失败返回零值结果

## 最佳实践

1. **始终检查返回值**：`clean_data()`可能返回None
2. **配置合理的阈值**：根据实际设备调整数据验证范围
3. **定期重置历史**：在设备重启或维护后重置异常历史
4. **监控统计信息**：定期检查异常统计，优化阈值设置

## 相关需求

本模块实现了以下需求：
- 需求4.3：数据清洗和异常值过滤
- 需求2.3：异常用电检测
- 需求7.2：能耗超过阈值时显示报警
- 需求6.1：OEE计算
- 需求6.2：可用率、性能率、质量率计算

## 下一步

- 集成到数据采集主程序
- 连接数据库存储模块
- 实现报警处理功能
