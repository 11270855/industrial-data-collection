# 数据库设置指南

本文档说明如何设置和管理能源管理系统的数据库。

## 前置要求

1. 安装Python依赖：
```bash
pip install -r requirements.txt
```

2. 配置数据库连接：
   - 复制 `.env.example` 到 `.env`
   - 修改数据库配置参数

## 快速开始

### 一键设置（推荐）

运行完整的数据库设置脚本，自动完成初始化和数据填充：

```bash
python setup_database.py
```

这将：
- 创建所有数据表和索引
- 创建默认管理员账户（admin/admin123）
- 创建默认普通用户账户（user/user123）
- 配置默认阈值设置

## 分步设置

### 1. 初始化数据库

仅创建数据表结构：

```bash
python init_database.py
```

### 2. 填充种子数据

创建初始用户和配置：

```bash
python seed_data.py
```

## 数据库模型

系统包含以下数据表：

### energy_data（能源数据表）
- 存储设备实时能源消耗数据
- 包含功率、能耗、设备状态等信息
- 按时间戳和设备ID索引

### production_data（生产数据表）
- 存储生产统计数据
- 包含产量、不良品数、OEE指标等
- 按时间戳索引

### alarms（报警记录表）
- 存储系统报警事件
- 包含报警级别、阈值、确认状态等
- 按时间戳和设备ID索引

### users（用户表）
- 存储用户账户信息
- 支持密码哈希、登录失败锁定等安全功能
- 区分管理员和普通用户角色

### thresholds（阈值配置表）
- 存储设备参数阈值
- 支持启用/禁用、报警级别配置
- 按设备ID和参数名唯一索引

## 数据库管理

### 查看连接池状态

```python
from database import DatabaseManager
from config import config

db_manager = DatabaseManager(config.DATABASE_URI)
db_manager.connect()
status = db_manager.get_pool_status()
print(status)
```

### 使用会话管理器

```python
from database import DatabaseManager
from models import User

db_manager = DatabaseManager(config.DATABASE_URI)
db_manager.connect()

# 使用上下文管理器自动处理提交和回滚
with db_manager.get_session() as session:
    users = session.query(User).all()
    for user in users:
        print(user.username)
```

### 重置数据库

⚠️ **警告：这将删除所有数据！**

```bash
python init_database.py --drop
```

然后重新初始化：

```bash
python setup_database.py
```

## 默认账户

设置完成后，系统将创建以下默认账户：

| 用户名 | 密码 | 角色 | 权限 |
|--------|------|------|------|
| admin | admin123 | 管理员 | 完全访问，可修改配置 |
| user | user123 | 普通用户 | 只读访问 |

⚠️ **重要：请在生产环境中立即修改默认密码！**

## 默认阈值配置

系统预配置了以下设备阈值：

- **传送带 (conveyor)**
  - 功率警告: 3.0 kW
  - 功率严重: 4.0 kW

- **工位1 (station1)**
  - 功率警告: 5.0 kW
  - 功率严重: 6.0 kW

- **工位2 (station2)**
  - 功率警告: 5.0 kW
  - 功率严重: 6.0 kW

- **总能耗 (total)**
  - 能耗警告: 100.0 kWh
  - 能耗严重: 150.0 kWh

## 数据库配置

### MySQL配置示例

在 `.env` 文件中：

```env
DB_TYPE=mysql
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=energy_management
```

### SQLite配置示例（开发环境）

在 `.env` 文件中：

```env
DB_TYPE=sqlite
SQLITE_DB_PATH=energy_management.db
```

## 连接池配置

数据库管理器使用连接池优化性能：

- **pool_size**: 10（基础连接数）
- **max_overflow**: 20（最大溢出连接数）
- **pool_timeout**: 30秒（获取连接超时）
- **pool_recycle**: 3600秒（连接回收时间）
- **pool_pre_ping**: 启用（连接健康检查）

## 故障排除

### 连接失败

1. 检查数据库服务是否运行
2. 验证 `.env` 配置是否正确
3. 确认数据库用户权限
4. 检查防火墙设置

### 表已存在错误

如果表已存在，脚本会跳过创建。如需重建：

```bash
python init_database.py --drop
python setup_database.py
```

### 导入错误

确保所有依赖已安装：

```bash
pip install -r requirements.txt
```

## 维护建议

1. **定期备份**：建议每天备份数据库
2. **数据归档**：超过30天的历史数据应归档
3. **索引优化**：定期检查和优化索引性能
4. **连接监控**：监控连接池使用情况
5. **日志审计**：定期审查操作日志

## 相关文件

- `models.py` - 数据模型定义
- `database.py` - 数据库管理类
- `init_database.py` - 数据库初始化脚本
- `seed_data.py` - 种子数据脚本
- `setup_database.py` - 完整设置脚本
- `config.py` - 配置管理
