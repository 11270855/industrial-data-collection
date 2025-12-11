# OPC UA客户端模块使用指南

## 概述

OPC UA客户端模块提供了与KepServer OPC UA服务器通信的完整功能，包括连接管理、数据订阅和数据读取。

## 功能特性

### 1. 连接管理
- ✅ 自动连接到OPC UA服务器
- ✅ 指数退避重试策略（最多5次）
- ✅ 连接超时控制（默认3秒）
- ✅ 连接状态检查
- ✅ 自动重连机制
- ✅ 优雅断开连接和资源清理

### 2. 数据订阅
- ✅ 订阅单个或多个OPC UA节点
- ✅ 数据变化实时回调通知
- ✅ 批量节点订阅优化
- ✅ 订阅管理（创建、删除、更新）
- ✅ 可配置的发布间隔

### 3. 数据读取
- ✅ 读取单个节点值
- ✅ 批量读取多个节点
- ✅ 自动数据类型转换
- ✅ 读取失败自动重试
- ✅ 错误处理和日志记录

## 安装依赖

```bash
pip install opcua==0.98.13
```

## 快速开始

### 基本连接示例

```python
from opcua_client import OPCUAClient
from config import config

# 创建客户端实例
client = OPCUAClient(
    server_url=config.OPC_UA_SERVER_URL,
    timeout=3,
    max_retries=5,
    retry_delay=5
)

# 连接到服务器
if client.connect():
    print("连接成功！")
    
    # 执行操作...
    
    # 断开连接
    client.disconnect()
```

### 使用上下文管理器

```python
with OPCUAClient(config.OPC_UA_SERVER_URL) as client:
    if client.is_connected:
        # 执行操作...
        pass
    # 自动断开连接
```

### 读取单个节点

```python
client = OPCUAClient(config.OPC_UA_SERVER_URL)

if client.connect():
    # 读取传送带速度
    node_id = 'ns=2;s=ProductionLine_PLC.DeviceControl.ConveyorSpeed'
    value = client.read_node(node_id)
    
    if value is not None:
        print(f"传送带速度: {value} m/s")
    
    client.disconnect()
```

### 批量读取多个节点

```python
client = OPCUAClient(config.OPC_UA_SERVER_URL)

if client.connect():
    # 准备节点列表
    node_ids = [
        'ns=2;s=ProductionLine_PLC.EnergyData.ConveyorPower',
        'ns=2;s=ProductionLine_PLC.EnergyData.Station1Power',
        'ns=2;s=ProductionLine_PLC.EnergyData.Station2Power'
    ]
    
    # 批量读取
    results = client.read_nodes(node_ids)
    
    for node_id, value in results.items():
        print(f"{node_id}: {value}")
    
    client.disconnect()
```

### 订阅数据变化

```python
def data_change_callback(node_id, value, data):
    """数据变化时的回调函数"""
    print(f"数据变化: {node_id} = {value}")

client = OPCUAClient(config.OPC_UA_SERVER_URL)

if client.connect():
    # 订阅节点
    node_ids = [
        'ns=2;s=ProductionLine_PLC.EnergyData.ConveyorPower',
        'ns=2;s=ProductionLine_PLC.EnergyData.TotalEnergy'
    ]
    
    client.subscribe_nodes(
        node_ids, 
        data_change_callback,
        publishing_interval=1000  # 1秒
    )
    
    # 保持运行以接收通知
    import time
    time.sleep(60)
    
    client.disconnect()
```

## API参考

### OPCUAClient类

#### 构造函数

```python
OPCUAClient(server_url, timeout=3, max_retries=5, retry_delay=5)
```

**参数:**
- `server_url` (str): OPC UA服务器地址，例如 'opc.tcp://localhost:4840'
- `timeout` (int): 连接超时时间（秒），默认3秒
- `max_retries` (int): 最大重试次数，默认5次
- `retry_delay` (int): 重试延迟基础时间（秒），使用指数退避，默认5秒

#### 方法

##### connect()

连接到OPC UA服务器，使用指数退避策略进行重试。

**返回:** `bool` - 连接是否成功

```python
if client.connect():
    print("连接成功")
```

##### disconnect()

断开连接并清理所有资源（包括订阅）。

```python
client.disconnect()
```

##### check_connection()

检查当前连接状态是否正常。

**返回:** `bool` - 连接是否正常

```python
if client.check_connection():
    print("连接正常")
```

##### reconnect()

重新连接到服务器。

**返回:** `bool` - 重连是否成功

```python
if client.reconnect():
    print("重连成功")
```

##### read_node(node_id, retry=True)

读取单个节点的值。

**参数:**
- `node_id` (str): 节点ID
- `retry` (bool): 失败时是否重试，默认True

**返回:** 节点值，失败返回None

```python
value = client.read_node('ns=2;s=ProductionLine_PLC.EnergyData.ConveyorPower')
```

##### read_nodes(node_ids, retry=True)

批量读取多个节点的值。

**参数:**
- `node_ids` (List[str]): 节点ID列表
- `retry` (bool): 失败时是否重试，默认True

**返回:** `Dict[str, Any]` - 字典，键为节点ID，值为节点值

```python
results = client.read_nodes([node_id1, node_id2, node_id3])
```

##### subscribe_nodes(node_ids, callback, publishing_interval=1000)

订阅OPC UA节点的数据变化。

**参数:**
- `node_ids` (List[str]): 要订阅的节点ID列表
- `callback` (Callable): 回调函数，签名为 `callback(node_id, value, data)`
- `publishing_interval` (int): 发布间隔（毫秒），默认1000ms

**返回:** `bool` - 订阅是否成功

```python
def my_callback(node_id, value, data):
    print(f"{node_id} = {value}")

client.subscribe_nodes([node_id1, node_id2], my_callback)
```

##### unsubscribe_nodes(node_ids)

取消订阅指定节点。

**参数:**
- `node_ids` (List[str]): 要取消订阅的节点ID列表

**返回:** `bool` - 操作是否成功

```python
client.unsubscribe_nodes([node_id1, node_id2])
```

##### get_node_info(node_id)

获取节点的详细信息。

**参数:**
- `node_id` (str): 节点ID

**返回:** `Dict[str, Any]` - 节点信息字典，包含browse_name、display_name、node_class、value、data_type等

```python
info = client.get_node_info('ns=2;s=ProductionLine_PLC.EnergyData.ConveyorPower')
print(info)
```

## 配置说明

在 `config.py` 中配置OPC UA相关参数：

```python
# OPC UA服务器配置
OPC_UA_SERVER_URL = 'opc.tcp://localhost:4840'
OPC_UA_TIMEOUT = 3  # 连接超时（秒）
OPC_UA_RETRY_MAX = 5  # 最大重试次数
OPC_UA_RETRY_DELAY = 5  # 重试延迟（秒）

# OPC UA节点配置
OPC_UA_NODES = {
    'conveyor': {
        'start': 'ns=2;s=ProductionLine_PLC.DeviceControl.ConveyorStart',
        'speed': 'ns=2;s=ProductionLine_PLC.DeviceControl.ConveyorSpeed',
        'power': 'ns=2;s=ProductionLine_PLC.EnergyData.ConveyorPower',
    },
    # ... 更多设备配置
}
```

## 错误处理

客户端内置了完善的错误处理机制：

1. **连接失败**: 自动重试，使用指数退避策略
2. **读取失败**: 可选的自动重试，检查连接状态并尝试重连
3. **订阅失败**: 记录错误日志，返回失败状态
4. **数据类型转换**: 自动处理OPC UA数据类型到Python原生类型的转换

所有错误都会记录到日志中，便于调试和监控。

## 日志配置

建议配置日志以便跟踪客户端操作：

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 性能优化建议

1. **批量读取**: 使用 `read_nodes()` 而不是多次调用 `read_node()`
2. **订阅优先**: 对于需要实时监控的数据，使用订阅而不是轮询
3. **合理的发布间隔**: 根据实际需求设置订阅的发布间隔
4. **连接复用**: 在应用程序生命周期内保持连接，避免频繁连接/断开

## 示例程序

查看 `example_opcua_usage.py` 获取更多使用示例：

```bash
python example_opcua_usage.py
```

## 故障排查

### 连接失败

1. 检查KepServer是否正在运行
2. 验证OPC UA服务器地址和端口是否正确
3. 确认防火墙允许端口4840的通信
4. 检查OPC UA服务器是否启用了匿名访问

### 读取节点失败

1. 使用UaExpert验证节点ID是否正确
2. 检查节点是否存在于服务器中
3. 确认节点ID的命名空间索引（ns）是否正确

### 订阅无数据

1. 确认节点值是否在变化
2. 检查发布间隔设置是否合理
3. 验证回调函数是否正确实现

## 需求追溯

本模块实现了以下需求：

- **需求 3.1**: OPC UA通信 - KepServer连接
- **需求 3.2**: OPC UA通信 - 节点订阅
- **需求 3.4**: OPC UA通信 - 数据响应
- **需求 4.1**: 数据采集 - 客户端连接
- **需求 4.2**: 数据采集 - 数据订阅
- **需求 4.5**: 数据采集 - 错误处理和重连

## 下一步

完成OPC UA客户端后，可以继续实现：

- 数据处理模块 (task 5)
- 数据库操作模块 (task 6)
- 报警处理模块 (task 7)
