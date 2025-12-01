# 安全配置说明

## 重要提示

**请勿将包含真实密码的 `.env` 文件提交到版本控制系统！**

## 配置步骤

1. 复制 `.env.example` 文件为 `.env`：
   ```bash
   cp .env.example .env
   ```

2. 编辑 `.env` 文件，填入您的实际配置：
   - `SECRET_KEY`: 生成一个强随机密钥
   - `DB_USER`: 您的数据库用户名
   - `DB_PASSWORD`: 您的数据库密码
   - 其他配置根据实际需求修改

3. 确保 `.env` 文件已被 `.gitignore` 忽略

## 生成安全的 SECRET_KEY

使用 Python 生成随机密钥：

```python
import secrets
print(secrets.token_hex(32))
```

## 生产环境建议

1. 使用环境变量而不是 `.env` 文件
2. 启用 HTTPS（设置 `SESSION_COOKIE_SECURE=True`）
3. 使用强密码策略
4. 定期更换密钥和密码
5. 限制数据库用户权限
6. 启用防火墙规则
7. 定期更新依赖包

## 数据库安全

1. 不要使用 root 用户连接数据库
2. 为应用创建专用数据库用户
3. 只授予必要的权限（SELECT, INSERT, UPDATE, DELETE）
4. 使用强密码
5. 限制数据库访问的 IP 地址

## 示例：创建专用数据库用户

```sql
-- 创建数据库
CREATE DATABASE energy_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建专用用户
CREATE USER 'energy_app'@'localhost' IDENTIFIED BY 'strong_password_here';

-- 授予权限
GRANT SELECT, INSERT, UPDATE, DELETE ON energy_management.* TO 'energy_app'@'localhost';

-- 刷新权限
FLUSH PRIVILEGES;
```
