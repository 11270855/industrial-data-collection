"""
路由模块初始化
"""

from .auth import auth_bp
from .dashboard import dashboard_bp
from .api import api_bp

# 导出所有蓝图，供app.py注册使用
__all__ = ['auth_bp', 'dashboard_bp', 'api_bp']
