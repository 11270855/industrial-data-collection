# 安全功能技术说明

## 1. 密码管理

### 1.1 密码加密存储
```python
# python_client/models.py
import bcrypt

class User(Base):
    password_hash = Column(String(255), nullable=False)
    
    def set_password(self, password):
        """使用bcrypt加密密码"""
        salt = bcrypt.gensalt(rounds=12)
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'), 
            salt
        ).decode('utf-8')
    
    def check_password(self, password):
        """验证密码"""
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )
```



## 2. HTTPS配置

### 2.1 生成SSL证书
```python
# security/setup_https.py
import subprocess

def generate_self_signed_cert():
    # 生成私钥
    subprocess.run([
        "openssl", "genrsa",
        "-out", "security/certs/server.key",
        "2048"
    ])
    
    # 生成证书
    subprocess.run([
        "openssl", "req", "-new", "-x509",
        "-key", "security/certs/server.key",
        "-out", "security/certs/server.crt",
        "-days", "365"
    ])
```

### 2.2 Flask HTTPS配置
```python
# web_app/app.py
if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=443,
        ssl_context=(
            'security/certs/server.crt',
            'security/certs/server.key'
        )
    )
```


## 3. OPC UA安全

### 3.1 生成OPC UA证书
```python
# security/setup_opcua_security.py
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

def generate_opcua_cert():
    # 生成私钥
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    
    # 生成证书
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "OPC UA Client")
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).sign(private_key, hashes.SHA256())
    
    # 保存
    with open("security/opcua_certs/client_key.pem", "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
```

### 3.2 安全连接配置
```python
# python_client/opcua_client.py
from opcua import Client, ua

client = Client("opc.tcp://localhost:4840")

# 设置安全策略
client.set_security_string(
    "Basic256Sha256,SignAndEncrypt,"
    "security/opcua_certs/client_cert.pem,"
    "security/opcua_certs/client_key.pem"
)

# 用户认证
client.set_user("opcua_user")
client.set_password("secure_password")

client.connect()
```

## 4. 防火墙配置

### 4.1 Windows防火墙
```batch
REM security/setup_firewall.bat
@echo off

REM 允许HTTPS
netsh advfirewall firewall add rule name="HTTPS" dir=in action=allow protocol=TCP localport=443

REM 允许OPC UA
netsh advfirewall firewall add rule name="OPC UA" dir=in action=allow protocol=TCP localport=4840

REM MySQL仅本地访问
netsh advfirewall firewall add rule name="MySQL" dir=in action=allow protocol=TCP localport=3306 remoteip=127.0.0.1

REM 启用防火墙
netsh advfirewall set allprofiles state on
```

### 4.2 Linux防火墙
```bash
# 启用UFW
sudo ufw enable

# 允许HTTPS
sudo ufw allow 443/tcp

# 允许OPC UA
sudo ufw allow 4840/tcp

# MySQL仅本地
sudo ufw deny 3306/tcp
```

## 5. 数据备份

### 5.1 备份脚本
```python
# security/backup_database.py
import subprocess
import gzip
from datetime import datetime

def backup_database(db_name, password):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'backups/{db_name}_{timestamp}.sql'
    
    # 使用mysqldump备份
    cmd = [
        'mysqldump',
        f'--user=root',
        f'--password={password}',
        '--single-transaction',
        db_name
    ]
    
    with open(backup_file, 'w') as f:
        subprocess.run(cmd, stdout=f, check=True)
    
    # 压缩
    with open(backup_file, 'rb') as f_in:
        with gzip.open(f'{backup_file}.gz', 'wb') as f_out:
            f_out.writelines(f_in)
    
    os.remove(backup_file)
    print(f"✅ 备份完成: {backup_file}.gz")
```

### 5.2 自动备份任务
```python
import schedule

def schedule_backup():
    # 每天凌晨2点备份
    schedule.every().day.at("02:00").do(
        backup_database, 
        'energy_management', 
        'password'
    )
    
    while True:
        schedule.run_pending()
        time.sleep(60)
```

## 6. 密钥轮换

### 6.1 生成新密钥
```python
# security/rotate_keys.py
import secrets

def generate_secret_key(length=64):
    """生成随机密钥"""
    return secrets.token_urlsafe(length)

def rotate_flask_key():
    new_key = generate_secret_key()
    
    # 更新配置文件
    with open('web_app/config.py', 'r') as f:
        content = f.read()
    
    content = content.replace(
        "SECRET_KEY = 'old_key'",
        f"SECRET_KEY = '{new_key}'"
    )
    
    with open('web_app/config.py', 'w') as f:
        f.write(content)
    
    print("✅ SECRET_KEY已更新")
```

## 7. 禁用调试模式

### 7.1 生产环境配置
```python
# web_app/config.py
class ProductionConfig:
    DEBUG = False
    TESTING = False
    SQLALCHEMY_ECHO = False
    LOG_LEVEL = 'WARNING'
    
    # 安全配置
    SECRET_KEY = os.getenv('SECRET_KEY')
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
```

### 7.2 安全HTTP头
```python
# web_app/app.py
@app.after_request
def set_security_headers(response):
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000'
    return response
```

### 7.3 禁用调试工具
```python
# security/disable_debug_mode.py
import re

def disable_debug():
    with open('web_app/config.py', 'r') as f:
        content = f.read()
    
    # 替换DEBUG=True为False
    content = re.sub(r'DEBUG\s*=\s*True', 'DEBUG = False', content)
    
    with open('web_app/config.py', 'w') as f:
        f.write(content)
    
    print("✅ 调试模式已禁用")
```

---

**文档版本**: v1.0  
**最后更新**: 2025-12-16
