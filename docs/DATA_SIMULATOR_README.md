# 数据模拟器使用说明

## 概述

当没有真实 PLC 连接时，数据模拟器可为系统提供模拟的能源和生产数据。支持两种运行方式：

| 方式 | 说明 | 适用场景 |
|------|------|---------|
| **集成模式**（推荐） | 集成在 `web_app/app.py` 中，随 Web 应用自动启动 | 演示、无真实PLC开发环境 |
| **独立模式** | 运行 `simulate_data.py` 独立脚本 | 需要单独控制数据生成 |

> ⚠️ 两种模式**不应同时运行**，避免数据重复写入。

## 功能特性

### 1. 能源数据模拟
- **设备**: 传送带、工作站1、工作站2
- **功率范围**:
  - 传送带: 5.0 - 15.0 kW (基准值: 10.0 kW)
  - 工作站1: 8.0 - 20.0 kW (基准值: 14.0 kW)
  - 工作站2: 10.0 - 25.0 kW (基准值: 17.0 kW)
- **波动**: ±20% 随机波动，模拟真实设备运行状态
- **采集频率**: 每秒采集一次

### 2. 生产数据模拟
- **产品计数**: 自动累加
- **不良品率**: 约5%
- **OEE指标**:
  - 可用率: 92% - 98%
  - 性能率: 85% - 95%
  - 质量率: 根据实际不良品率计算
  - OEE: 可用率 × 性能率 × 质量率
- **更新频率**: 每10秒更新一次

### 3. 报警模拟
- **触发条件**: 设备功率超过最大值的90%
- **报警级别**: warning (警告)
- **报警类型**: high_power (功率过高)
- **触发概率**: 5% (低概率，避免过多报警)

## 使用方法

### 集成模式（推荐）

直接启动 Web 应用，数据模拟器作为后台守护线程自动运行：

```batch
start_system.bat
```

数据模拟器随 Web 应用启停，日志输出至 `logs/web_app.log`。

**技术实现**：
- 使用 Python `threading` 模块，设置为守护线程（daemon=True）
- 与 Web 应用共享同一数据库连接池
- 完全后台静默运行，不创建额外窗口

**修改集成模式参数**：编辑 `web_app/app.py` 中的 `DataSimulator` 类。

---

### 独立模式

分别启动数据模拟器和 Web 应用（两个独立进程）：

#### 自动启动（推荐）

```batch
start_system.bat
```

启动后会看到：
- `Data Simulator - Energy Management`：数据模拟器窗口
- `Web App - Energy Management`：Web 应用窗口

#### 手动启动

```batch
call .venv\Scripts\activate.bat
python simulate_data.py
```

#### 停止

```batch
stop_system.bat
```

或直接关闭 "Data Simulator" 窗口。

独立模式日志保存在 `logs/simulate_data.log`。

**修改独立模式参数**：编辑 `simulate_data.py` 中的设备配置字典。

### 停止运行

使用系统停止脚本：

```batch
stop_system.bat
```

或者直接关闭 "Data Simulator - Energy Management" 窗口。

## 数据范围说明

所有模拟数据都在正常范围内，符合实际工业场景：

| 参数 | 范围 | 说明 |
|------|------|------|
| 传送带功率 | 5.0 - 15.0 kW | 带±20%波动 |
| 工作站1功率 | 8.0 - 20.0 kW | 带±20%波动 |
| 工作站2功率 | 10.0 - 25.0 kW | 带±20%波动 |
| 产品计数 | 累加 | 每10秒约10%概率+1 |
| 不良品率 | ~5% | 符合工业标准 |
| OEE | 75% - 90% | 优秀水平 |
| 可用率 | 92% - 98% | 高可用性 |
| 性能率 | 85% - 95% | 良好性能 |

## 日志文件

数据模拟器的运行日志保存在：

```
logs/simulate_data.log
```

日志包含：
- 数据生成记录
- 数据库保存状态
- 报警生成信息
- 错误和异常信息

## 数据库表

模拟器会向以下数据库表写入数据：

1. **energy_data**: 能源数据
   - timestamp: 时间戳
   - device_id: 设备ID
   - device_name: 设备名称
   - power_kw: 功率(kW)
   - energy_kwh: 累计能耗(kWh)
   - status: 运行状态

2. **production_data**: 生产数据
   - timestamp: 时间戳
   - product_count: 产品计数
   - reject_count: 不良品计数
   - runtime_seconds: 运行时间
   - oee_percentage: OEE百分比
   - availability: 可用率
   - performance: 性能率
   - quality: 质量率

3. **alarms**: 报警记录
   - timestamp: 时间戳
   - device_id: 设备ID
   - alarm_type: 报警类型
   - alarm_level: 报警级别
   - message: 报警消息
   - threshold_value: 阈值
   - actual_value: 实际值

## 与真实 PLC 的关系

- 模拟器和真实 PLC 客户端（`python_client/main.py`）**不应同时运行**
- 如需切换到真实 PLC：停止数据模拟器，启动 `python_client/main.py`
- 如需切换回模拟：停止 PLC 客户端，重启 Web 应用（集成模式）或启动 `simulate_data.py`

## 故障排除

### 问题1: 数据库连接失败
**解决方案**: 
- 检查 `.env` 文件中的数据库配置
- 确保MySQL服务正在运行
- 运行 `setup_mysql.bat` 初始化数据库

### 问题2: Web应用无数据显示
**解决方案**:
- 检查数据模拟器窗口是否正在运行
- 查看 `logs/simulate_data.log` 确认数据是否正常生成
- 刷新Web页面

### 问题3: 模拟器启动失败
**解决方案**:
- 确保虚拟环境已激活
- 检查依赖是否已安装: `pip install -r python_client\requirements.txt`
- 查看错误日志: `logs/simulate_data.log`

## 开发说明

如需修改模拟数据的范围或行为，可以编辑 `simulate_data.py` 中的以下部分：

```python
# 设备配置
self.devices = {
    'conveyor': {
        'name': '传送带',
        'power_range': (5.0, 15.0),  # 修改功率范围
        'base_power': 10.0,           # 修改基准功率
        'status': 'running'
    },
    # ...
}
```

修改后重启数据模拟器即可生效。
