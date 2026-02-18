# MySQL 数据库配置指南

> **快速解决登录问题**：如遇"登录失败：用户不存在"或"未授权访问"，请直接跳至[快速修复（3步）](#快速修复3步)。

## 目录

1. [快速修复（3步）](#快速修复3步)
2. [完整设置步骤](#完整设置步骤)
3. [配置说明](#配置说明)
4. [常见问题排查](#常见问题排查)
5. [生产环境建议](#生产环境建议)

---

## 快速修复（3步）

适用于已安装 MySQL 但遇到登录或连接错误的情况。

### 步骤1：启动 MySQL 服务

```cmd
net start MySQL80
```

> 注意：服务名可能是 `MySQL`、`MySQL80` 或 `MySQL57`，取决于安装版本

### 步骤2：创建数据库

```cmd
mysql -u root -p < create_mysql_database.sql
```

### 步骤3：初始化数据库和用户

```cmd
setup_mysql.bat
```

初始化完成后，使用以下账户登录系统：
- **用户名**: `root`
- **密码**: `root`

⚠️ **请在首次登录后立即修改默认密码！**

---

## 完整设置步骤

### 方法一：自动化脚本（推荐）

#### 步骤 1：启动 MySQL 服务

```cmd
net start MySQL80
```

#### 步骤 2：创建数据库

```cmd
mysql -u root -p < create_mysql_database.sql
```

#### 步骤 3：配置 .env 文件

编辑项目根目录的 `.env` 文件：

```properties
# 数据库配置
DB_TYPE=mysql
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=你的MySQL密码
DB_NAME=energy_management
```

**重要**: 将 `DB_PASSWORD` 改为你的实际 MySQL root 密码

#### 步骤 4：安装 Python 依赖

```cmd
.venv\Scripts\activate
pip install pymysql sqlalchemy bcrypt python-dotenv
```

#### 步骤 5：初始化数据库

```cmd
cd python_client
python setup_database.py
cd ..
```

这将创建所有必要的表并添加默认用户。

### 方法二：手动设置（仅创建数据库部分）

```sql
CREATE DATABASE energy_management 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;
```

其余步骤同方法一的步骤3~5。

---

## 配置说明

编辑项目根目录的 `.env` 文件：

```properties
# 数据库配置
DB_TYPE=mysql
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=你的MySQL密码    # ⚠️ 修改为实际密码
DB_NAME=energy_management
```

运行诊断脚本可一键检查环境配置、连接、表结构与用户数据：

```cmd
python diagnose_mysql.py
```

---

## 常见问题排查

### 问题1："登录失败：用户不存在"

**原因**: 数据库未初始化或用户表为空

**解决方案**:
```cmd
cd python_client
python seed_data.py
cd ..
```

### 问题2："无法连接到数据库"

**可能原因**:
1. MySQL 服务未启动
2. 密码错误
3. 数据库不存在

**解决方案**:

1. 检查 MySQL 服务状态：
   ```cmd
   net start MySQL80
   ```

2. 验证密码：
   ```cmd
   mysql -u root -p
   ```

3. 检查数据库是否存在：
   ```sql
   SHOW DATABASES LIKE 'energy_management';
   ```

### 问题3："Access denied for user 'root'@'localhost'"

**原因**: MySQL 密码认证问题

**解决方案**:

1. 使用 MySQL 命令行修改密码：
   ```sql
   ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '你的新密码';
   FLUSH PRIVILEGES;
   ```

2. 或运行提供的修复脚本：
   ```cmd
   mysql -u root -p < fix_mysql_auth.sql
   ```

### 问题4："未授权访问"

**原因**: 尝试访问需要登录的页面但未登录

**解决方案**:
1. 确保数据库已初始化（运行 `setup_mysql.bat`）
2. 使用默认账户登录：用户名 `root`，密码 `root`
3. 清除浏览器缓存和 Cookie

## 验证安装

> 也可使用 `python diagnose_mysql.py` 进行全面诊断。

运行以下命令验证数据库设置：

```cmd
cd python_client
python -c "from database import DatabaseManager; from config import config; db = DatabaseManager(config.DATABASE_URI); print('连接成功!' if db.connect() else '连接失败'); db.disconnect()"
cd ..
```

## 数据库表结构

初始化后会创建以下表：

1. **users** - 用户账户表
2. **energy_data** - 能源数据表
3. **production_data** - 生产数据表
4. **alarms** - 报警记录表
5. **thresholds** - 阈值配置表

## 切换回 SQLite

如果需要切换回 SQLite，修改 `.env` 文件：

```properties
# 使用SQLite数据库
DB_TYPE=sqlite
SQLITE_DB_PATH=energy_management.db
```

然后重新初始化：

```cmd
cd python_client
python setup_database.py
cd ..
```

## 数据迁移

如果需要从 SQLite 迁移数据到 MySQL：

1. 导出 SQLite 数据
2. 使用数据库迁移工具（如 SQLAlchemy-Utils）
3. 或手动编写迁移脚本

## 生产环境建议

1. **修改默认密码**: 首次登录后立即修改
2. **创建专用数据库用户**: 不要使用 root 账户
   ```sql
   CREATE USER 'energy_user'@'localhost' IDENTIFIED BY '强密码';
   GRANT ALL PRIVILEGES ON energy_management.* TO 'energy_user'@'localhost';
   FLUSH PRIVILEGES;
   ```
3. **启用 SSL 连接**: 配置 MySQL SSL
4. **定期备份**: 设置自动备份计划
5. **监控性能**: 使用 MySQL 性能监控工具

## 支持

如遇到其他问题，请查看：
- [python_client/DATABASE_SETUP.md](../python_client/DATABASE_SETUP.md)
- [docs/USER_MANUAL.md](USER_MANUAL.md)
- 项目根目录 [README.md](../README.md)
- 项目 README.md
