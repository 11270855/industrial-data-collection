"""
测试错误处理和日志系统
"""

import os
import sys
import json
import tempfile
import pytest

# 添加python_client到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python_client'))

from app import create_app


class TestConfig:
    """测试配置"""
    SECRET_KEY = 'test-secret-key'
    DEBUG = False
    TESTING = True
    DB_TYPE = 'sqlite'
    SQLITE_DB_PATH = ':memory:'
    LOG_LEVEL = 'DEBUG'
    LOG_FILE = os.path.join(tempfile.gettempdir(), 'test_web_app.log')
    LOG_MAX_BYTES = 1048576
    LOG_BACKUP_COUNT = 3
    
    @property
    def SQLALCHEMY_DATABASE_URI(self):
        return 'sqlite:///:memory:'


@pytest.fixture
def client():
    """创建测试客户端"""
    app = create_app(TestConfig)
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        yield client


def test_404_error_page(client):
    """测试404错误页面"""
    response = client.get('/nonexistent-page')
    assert response.status_code == 404
    assert b'404' in response.data or b'error' in response.data.lower()


def test_404_error_api(client):
    """测试API 404错误返回JSON"""
    response = client.get('/api/nonexistent-endpoint')
    assert response.status_code == 404
    assert response.content_type == 'application/json'
    
    data = json.loads(response.data)
    assert 'error' in data
    assert data['error'] == 'Not Found'
    assert 'status' in data
    assert data['status'] == 404


def test_405_error_api(client):
    """测试API 405错误（方法不允许）"""
    # 假设/api/devices只支持GET
    response = client.post('/api/devices')
    assert response.status_code in [404, 405]  # 可能是404或405


def test_logging_configuration():
    """测试日志配置"""
    app = create_app(TestConfig)
    
    # 验证日志器已配置
    assert len(app.logger.handlers) > 0
    
    # 验证日志级别
    assert app.logger.level <= 20  # DEBUG=10, INFO=20
    
    # 测试日志记录
    app.logger.debug("测试DEBUG日志")
    app.logger.info("测试INFO日志")
    app.logger.warning("测试WARNING日志")
    app.logger.error("测试ERROR日志")


def test_error_handler_with_exception(client):
    """测试异常处理"""
    # 这个测试需要一个会抛出异常的路由
    # 由于我们没有这样的路由，这个测试主要验证错误处理器存在
    app = client.application
    
    # 验证错误处理器已注册
    assert 404 in app.error_handler_spec[None]
    assert 500 in app.error_handler_spec[None]
    assert 403 in app.error_handler_spec[None]
    assert 401 in app.error_handler_spec[None]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
