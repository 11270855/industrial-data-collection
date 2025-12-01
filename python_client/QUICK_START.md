# 快速开始指南

## 1. 安装依赖

```bash
cd python_client
pip install -r requirements.txt
```

## 2. 配置环境变量

创建 `.env` 文件（或复制 `.env.example`）：

```env
# 数据库配置（SQLite - 开发环境）
DB_TYPE=sqlite
SQLITE_DB_PATH=energy_management.db

# 或使用MySQL（生产环境）
# DB_TYPE=mysql
# DB_HOST=localhost
# DB_PORT=3306
# DB_USER=root
# DB_PASSWORD=your_password
# DB_NAME=energy_management

# OPC UA配置
OPC_UA_SERVER_URL=opc.tcp://localhost:4840
```

## 3. 初始化数据库

一键设置（推荐）：

```bash
python setup_database.py
```

这将创建所有表并填充初始数据。

## 4. 验证设置

运行测试脚本：

```bash
python test_database_setup.py
```

## 5. 查看示例

学习如何使用数据库：

```bash
python example_database_usage.py
```

## 默认登录信息

- **管理员**: admin / admin123
- **普通用户**: user / user123

⚠️ 请在生产环境中修改默认密码！

## 文件说明

| 文件 | 说明 |
|------|------|
| `models.py` | 数据模型定义 |
| `database.py` | 数据库管理类 |
| `config.py` | 配置管理 |
| `setup_database.py` | 一键设置脚本 |
| `init_database.py` | 初始化数据表 |
| `seed_data.py` | 填充初始数据 |
| `test_database_setup.py` | 测试脚本 |
| `example_database_usage.py` | 使用示例 |

## 下一步

数据库设置完成后，可以继续：

1. 配置KepServer（参考任务13）
2. 实现OPC UA客户端（任务4）
3. 开发数据采集程序（任务5-8）

详细文档请参考 `DATABASE_SETUP.md`
