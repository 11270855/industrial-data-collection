# 生产环境安全加固指南

## 目录
1. [修改默认密码](#1-修改默认密码)
2. [启用HTTPS](#2-启用https)
3. [OPC UA加密与证书认证](#3-opc-ua加密与证书认证)
4. [配置防火墙](#4-配置防火墙)
5. [定期备份数据](#5-定期备份数据)
6. [更新密钥](#6-更新密钥)
7. [禁用调试模式](#7-禁用调试模式)

---

## 1. 修改默认密码

### 原理
默认密码是系统最大的安全隐患。必须在部署前修改所有默认密码，包括：
- 数据库root密码
- Web应用管理员密码
- OPC UA服务器密码

### 实施步骤

#### 1.1 修改MySQL密码

**方法1：使用SQL命令**
```sql
-- 连接到MySQL
mysql -u root -p

-- 修改root密码
ALTER USER 'root'@'localhost' IDENTIFIED BY 'YourStrongPassword123!@#';

-- 修改应用用户密码
ALTER USER 'energy_user'@'localhost' IDENTIFIED BY 'AnotherStrongPassword456!@#';

-- 刷新权限
FLUSH PRIVILEGES;
```

**方法2：使用Python脚本**


```python
# security/change_passwords.py
python security/change_passwords.py
```

#### 1.2 密码强度要求
- 最小长度：12位
- 必须包含：大写字母、小写字母、数字、特殊字符
- 不能包含：用户名、常见词汇、连续字符

---

## 2. 启用HTTPS

### 原理
HTTPS通过SSL/TLS加密HTTP通信，防止中间人攻击和数据窃听。

### 实施步骤

#### 2.1 生成SSL证书

**开发/测试环境（自签名证书）：**
```bash
python security/setup_https.py
# 选择选项1：生成自签名证书
```

**生产环境（Let's Encrypt）：**
```bash
# 安装certbot
sudo apt-get install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

#### 2.2 配置Flask使用HTTPS

```python
# web_app/app.py
from flask import Flask
from config_https import ProductionConfig

app = Flask(__name__)
app.config.from_object(ProductionConfig)

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=443,
        ssl_context=(
            ProductionConfig.SSL_CERT,
            ProductionConfig.SSL_KEY
        )
    )
```

#### 2.3 配置Nginx反向代理

```nginx
# /etc/nginx/sites-available/energy-management
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 3. OPC UA加密与证书认证

### 原理
OPC UA支持多种安全策略和模式：
- **安全策略**：None, Basic128Rsa15, Basic256, Basic256Sha256
- **安全模式**：None, Sign, SignAndEncrypt

生产环境推荐：**Basic256Sha256 + SignAndEncrypt**

### 实施步骤

#### 3.1 生成OPC UA证书

```bash
python security/setup_opcua_security.py
```

#### 3.2 配置客户端使用证书

```python
# python_client/opcua_client.py
from opcua import Client, ua
from opcua_security_config import OPCUASecurityConfig

client = Client("opc.tcp://localhost:4840")

# 设置安全策略
client.set_security_string(
    f"Basic256Sha256,SignAndEncrypt,"
    f"{OPCUASecurityConfig.CLIENT_CERTIFICATE},"
    f"{OPCUASecurityConfig.CLIENT_PRIVATE_KEY}"
)

# 设置用户认证
client.set_user(OPCUASecurityConfig.USERNAME)
client.set_password(OPCUASecurityConfig.PASSWORD)

client.connect()
```

#### 3.3 服务器端配置

**CODESYS配置：**
1. 打开CODESYS项目
2. 工具 → OPC UA Server → 安全设置
3. 启用安全策略：Basic256Sha256
4. 启用安全模式：SignAndEncrypt
5. 导入客户端证书到信任列表
6. 配置用户认证

**KEPServerEX配置：**
1. 打开KEPServerEX配置
2. OPC UA Configuration → Security Policies
3. 启用Basic256Sha256
4. 导入客户端证书
5. 配置用户管理器

---

## 4. 配置防火墙

### 原理
防火墙限制网络访问，只允许必要的端口和IP地址通信。

### 实施步骤

#### 4.1 Windows防火墙

```batch
REM 以管理员身份运行
security\setup_firewall.bat
```

#### 4.2 Linux防火墙（UFW）

```bash
# 启用UFW
sudo ufw enable

# 允许HTTPS
sudo ufw allow 443/tcp

# 允许HTTP（重定向用）
sudo ufw allow 80/tcp

# 允许OPC UA
sudo ufw allow 4840/tcp

# MySQL仅本地访问
sudo ufw deny 3306/tcp

# 查看规则
sudo ufw status
```

#### 4.3 高级规则

```bash
# 限制SSH访问（仅特定IP）
sudo ufw allow from 192.168.1.100 to any port 22

# 限制连接速率（防DDoS）
sudo ufw limit 443/tcp

# 记录被拒绝的连接
sudo ufw logging on
```

---

## 5. 定期备份数据

### 原理
定期备份确保数据安全，在系统故障或数据损坏时可以快速恢复。

### 实施步骤

#### 5.1 手动备份

```bash
# 备份数据库
python security/backup_database.py --action backup --password YOUR_PASSWORD

# 恢复数据库
python security/backup_database.py --action restore --file backups/database/energy_management_20250116_020000.sql.gz --password YOUR_PASSWORD
```

#### 5.2 自动备份

```bash
# 启动自动备份服务（每天凌晨2点）
python security/backup_database.py --action schedule --password YOUR_PASSWORD
```

#### 5.3 Windows计划任务

```batch
REM 创建计划任务
schtasks /create /tn "Database Backup" /tr "python E:\path\to\security\backup_database.py --action backup --password YOUR_PASSWORD" /sc daily /st 02:00
```

#### 5.4 Linux Cron任务

```bash
# 编辑crontab
crontab -e

# 添加每天凌晨2点备份
0 2 * * * /usr/bin/python3 /path/to/security/backup_database.py --action backup --password YOUR_PASSWORD
```

#### 5.5 备份策略

- **每日备份**：保留7天
- **每周备份**：保留4周
- **每月备份**：保留12个月
- **异地备份**：上传到云存储（AWS S3、阿里云OSS等）

---

## 6. 更新密钥

### 原理
定期轮换密钥可以降低密钥泄露的风险，即使密钥被窃取，也会在短时间内失效。

### 实施步骤

#### 6.1 密钥轮换

```bash
python security/rotate_keys.py
```

#### 6.2 轮换周期建议

- **SECRET_KEY**：每3个月
- **JWT密钥**：每6个月
- **数据库密码**：每6个月
- **SSL证书**：每12个月（Let's Encrypt自动续期）
- **OPC UA证书**：每12个月

#### 6.3 密钥管理最佳实践

1. **使用环境变量**
```python
# 不要硬编码密钥
SECRET_KEY = os.getenv('SECRET_KEY')
DB_PASSWORD = os.getenv('DB_PASSWORD')
```

2. **使用密钥管理服务**
- AWS Secrets Manager
- Azure Key Vault
- HashiCorp Vault

3. **密钥存储**
- 加密存储
- 限制访问权限
- 定期审计

---

## 7. 禁用调试模式

### 原理
调试模式会暴露敏感信息（堆栈跟踪、SQL查询、配置信息），必须在生产环境禁用。

### 实施步骤

#### 7.1 运行加固工具

```bash
python security/disable_debug_mode.py
```

#### 7.2 手动检查配置

```python
# web_app/config.py
class ProductionConfig:
    DEBUG = False  # 必须为False
    TESTING = False
    SQLALCHEMY_ECHO = False  # 禁用SQL日志
    LOG_LEVEL = 'WARNING'  # 或'ERROR'
```

#### 7.3 环境变量控制

```python
# web_app/config.py
import os

class Config:
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    SQLALCHEMY_ECHO = os.getenv('SQL_ECHO', 'False').lower() == 'true'
```

```bash
# 生产环境
export FLASK_DEBUG=False
export SQL_ECHO=False
```

#### 7.4 安全HTTP头

```python
# web_app/app.py
@app.after_request
def set_security_headers(response):
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    response.headers['Strict-Transport-Security'] = 'max-age=31536000'
    return response
```

---

## 8. 完整部署流程

### 8.1 部署前检查

```bash
# 1. 修改所有默认密码
python security/change_passwords.py

# 2. 配置HTTPS
python security/setup_https.py

# 3. 配置OPC UA安全
python security/setup_opcua_security.py

# 4. 配置防火墙
security\setup_firewall.bat  # Windows
# 或
sudo bash security/setup_firewall.sh  # Linux

# 5. 禁用调试模式
python security/disable_debug_mode.py

# 6. 设置自动备份
python security/backup_database.py --action schedule --password YOUR_PASSWORD
```

### 8.2 部署后验证

```bash
# 检查HTTPS
curl -I https://your-domain.com

# 检查安全头
curl -I https://your-domain.com | grep -E "X-Frame-Options|X-Content-Type-Options|Strict-Transport-Security"

# 检查防火墙
netstat -an | findstr "LISTENING"  # Windows
# 或
sudo netstat -tulpn  # Linux

# 检查备份
ls -lh backups/database/
```

### 8.3 安全检查清单

参考：`security/PRODUCTION_CHECKLIST.md`

---

## 9. 应急响应

### 9.1 密钥泄露

1. 立即轮换所有密钥
2. 强制所有用户重新登录
3. 检查访问日志
4. 通知相关人员

### 9.2 数据泄露

1. 隔离受影响系统
2. 从备份恢复数据
3. 分析泄露原因
4. 修复安全漏洞
5. 通知用户

### 9.3 服务中断

1. 检查系统日志
2. 从备份恢复
3. 切换到备用系统
4. 修复问题
5. 恢复服务

---

## 10. 安全监控

### 10.1 日志监控

```python
# 监控登录失败
grep "Failed login" logs/web_app.log

# 监控异常访问
grep "401\|403\|404" logs/web_app.log

# 监控数据库错误
grep "ERROR" logs/web_app.log
```

### 10.2 性能监控

- CPU使用率
- 内存使用率
- 磁盘空间
- 网络流量
- 数据库连接数

### 10.3 告警配置

- 登录失败超过5次
- 磁盘空间低于10%
- 数据库连接失败
- 备份失败
- 证书即将过期

---

## 12. 技术实现参考

安全功能的代码实现细节（密码加密、HTTPS配置、OPC UA证书生成、防火墙脚本、备份脚本、密钥轮换等）已整合在 [SECURITY_TECHNICAL_SPEC.md](SECURITY_TECHNICAL_SPEC.md) 中，可结合本指南使用。

---

## 11. 参考资源

### 安全标准
- OWASP Top 10
- CIS Benchmarks
- NIST Cybersecurity Framework

### 工具
- SSL Labs（SSL测试）
- OWASP ZAP（安全扫描）
- Nmap（端口扫描）
- Wireshark（网络分析）

### 文档
- [Flask Security](https://flask.palletsprojects.com/en/2.3.x/security/)
- [OPC UA Security](https://opcfoundation.org/about/opc-technologies/opc-ua/security/)
- [MySQL Security](https://dev.mysql.com/doc/refman/8.0/en/security.html)

---

**文档版本**: v1.0  
**最后更新**: 2025-12-16  
**维护者**: 系统管理员
