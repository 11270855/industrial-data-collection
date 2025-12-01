"""
Web应用配置文件
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """Flask应用配置类"""
    
    # Flask基础配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # 数据库配置
    DB_TYPE = os.getenv('DB_TYPE', 'mysql')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', '3306'))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
    DB_NAME = os.getenv('DB_NAME', 'energy_management')
    
    # SQLite配置（开发环境）
    SQLITE_DB_PATH = os.getenv('SQLITE_DB_PATH', 'energy_management.db')
    
    @property
    def SQLALCHEMY_DATABASE_URI(self):
        """生成SQLAlchemy数据库连接URI"""
        if self.DB_TYPE == 'sqlite':
            return f'sqlite:///{self.SQLITE_DB_PATH}'
        else:
            return f'mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.getenv('SQLALCHEMY_ECHO', 'False').lower() == 'true'
    
    # 会话配置
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = int(os.getenv('SESSION_LIFETIME', '1800'))  # 30分钟
    
    # 用户认证配置
    MAX_LOGIN_ATTEMPTS = int(os.getenv('MAX_LOGIN_ATTEMPTS', '3'))
    ACCOUNT_LOCK_DURATION = int(os.getenv('ACCOUNT_LOCK_DURATION', '600'))  # 10分钟（秒）
    
    # API配置
    API_RATE_LIMIT = os.getenv('API_RATE_LIMIT', '100 per minute')
    
    # 数据刷新配置
    REALTIME_UPDATE_INTERVAL = int(os.getenv('REALTIME_UPDATE_INTERVAL', '2'))  # 前端刷新间隔（秒）
    
    # 分页配置
    ITEMS_PER_PAGE = int(os.getenv('ITEMS_PER_PAGE', '50'))
    
    # 数据保留配置
    DATA_RETENTION_DAYS = int(os.getenv('DATA_RETENTION_DAYS', '30'))
    
    # CORS配置
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/web_app.log')
    LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', '10485760'))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))
    
    # 静态文件配置
    STATIC_FOLDER = 'static'
    TEMPLATE_FOLDER = 'templates'
    
    # 上传配置（如果需要）
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', '16777216'))  # 16MB


# 创建全局配置实例
config = Config()
