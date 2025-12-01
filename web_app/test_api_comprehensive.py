"""
API端点综合测试
使用pytest和Flask测试客户端测试所有API端点、认证和权限控制

需求覆盖:
- 8.1: 用户认证测试
- 8.2: 权限控制测试
- 8.3: 角色验证测试

注意: 由于Python 3.14与SQLAlchemy的兼容性问题，本测试使用模拟数据库
"""

import pytest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from contextlib import contextmanager

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'python_client'))


# 模拟数据库模型
class MockUser:
    def __init__(self, id, username, role, email):
        self.id = id
        self.username = username
        self.role = role
        self.email = email
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login = None
        self._password_hash = None
    
    def set_password(self, password):
        # 简单的密码存储（测试用）
        self._password_hash = f"hashed_{password}"
    
    def check_password(self, password):
        return self._password_hash == f"hashed_{password}"
    
    def is_locked(self):
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False


class MockEnergyData:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 1)
        self.timestamp = kwargs.get('timestamp', datetime.utcnow())
        self.device_id = kwargs.get('device_id', 'conveyor')
        self.device_name = kwargs.get('device_name', '传送带')
        self.power_kw = kwargs.get('power_kw', 2.5)
        self.energy_kwh = kwargs.get('energy_kwh', 15.3)
        self.status = kwargs.get('status', 'running')
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'device_id': self.device_id,
            'device_name': self.device_name,
            'power_kw': self.power_kw,
            'energy_kwh': self.energy_kwh,
            'status': self.status
        }


class MockAlarm:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 1)
        self.timestamp = kwargs.get('timestamp', datetime.utcnow())
        self.device_id = kwargs.get('device_id', 'station1')
        self.alarm_type = kwargs.get('alarm_type', 'energy_high')
        self.alarm_level = kwargs.get('alarm_level', 'warning')
        self.message = kwargs.get('message', '功率超过阈值')
        self.threshold_value = kwargs.get('threshold_value', 5.0)
        self.actual_value = kwargs.get('actual_value', 5.8)
        self.acknowledged = kwargs.get('acknowledged', False)
        self.acknowledged_by = kwargs.get('acknowledged_by', None)
        self.acknowledged_at = kwargs.get('acknowledged_at', None)
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'device_id': self.device_id,
            'alarm_type': self.alarm_type,
            'alarm_level': self.alarm_level,
            'message': self.message,
            'threshold_value': self.threshold_value,
            'actual_value': self.actual_value,
            'acknowledged': self.acknowledged,
            'acknowledged_by': self.acknowledged_by,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None
        }


class MockThreshold:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 1)
        self.device_id = kwargs.get('device_id', 'conveyor')
        self.parameter_name = kwargs.get('parameter_name', 'power')
        self.threshold_value = kwargs.get('threshold_value', 3.0)
        self.alarm_level = kwargs.get('alarm_level', 'warning')
        self.enabled = kwargs.get('enabled', True)
        self.updated_by = kwargs.get('updated_by', 'admin')
        self.updated_at = kwargs.get('updated_at', datetime.utcnow())
    
    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'parameter_name': self.parameter_name,
            'threshold_value': self.threshold_value,
            'alarm_level': self.alarm_level,
            'enabled': self.enabled,
            'updated_by': self.updated_by,
            'updated_at': self.updated_at.isoformat()
        }


# 模拟数据库会话
class MockSession:
    def __init__(self):
        self.users = {
            'admin': MockUser(1, 'admin', 'admin', 'admin@test.com'),
            'user': MockUser(2, 'user', 'user', 'user@test.com')
        }
        self.users['admin'].set_password('admin123')
        self.users['user'].set_password('user123')
        
        self.energy_data = [MockEnergyData(id=i) for i in range(1, 6)]
        self.alarms = [MockAlarm(id=1)]
        self.thresholds = [MockThreshold(id=1)]
    
    def query(self, model):
        return MockQuery(self, model)
    
    def add(self, obj):
        pass
    
    def commit(self):
        pass
    
    def rollback(self):
        pass


class MockQuery:
    def __init__(self, session, model):
        self.session = session
        self.model = model
        self.filters = []
        self._limit = None
        self._offset = None
        self._order_by = None
    
    def filter(self, *args):
        self.filters.append(args)
        return self
    
    def order_by(self, *args):
        self._order_by = args
        return self
    
    def limit(self, n):
        self._limit = n
        return self
    
    def offset(self, n):
        self._offset = n
        return self
    
    def first(self):
        results = self.all()
        return results[0] if results else None
    
    def all(self):
        # 简化的查询逻辑
        if 'User' in str(self.model):
            return list(self.session.users.values())
        elif 'EnergyData' in str(self.model):
            return self.session.energy_data
        elif 'Alarm' in str(self.model):
            return self.session.alarms
        elif 'Threshold' in str(self.model):
            return self.session.thresholds
        return []
    
    def count(self):
        return len(self.all())
    
    def group_by(self, *args):
        return self


class MockDatabaseManager:
    def __init__(self, uri):
        self.uri = uri
        self.session = MockSession()
    
    def connect(self):
        return True
    
    @contextmanager
    def get_session(self):
        yield self.session
    
    def query_history(self, **kwargs):
        return {
            'data': [],
            'page': kwargs.get('page', 1),
            'page_size': kwargs.get('page_size', 100),
            'total': 0,
            'total_pages': 0
        }


@pytest.fixture
def app():
    """创建测试应用实例"""
    # 模拟models模块
    sys.modules['models'] = MagicMock()
    sys.modules['models'].User = MockUser
    sys.modules['models'].EnergyData = MockEnergyData
    sys.modules['models'].Alarm = MockAlarm
    sys.modules['models'].Threshold = MockThreshold
    
    # 使用测试配置
    class TestConfig:
        TESTING = True
        SECRET_KEY = 'test-secret-key'
        DB_TYPE = 'sqlite'
        DB_NAME = ':memory:'
        SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
        DEBUG = False
        MAX_LOGIN_ATTEMPTS = 3
        ACCOUNT_LOCK_DURATION = 600
        PERMANENT_SESSION_LIFETIME = 1800
        LOG_LEVEL = 'ERROR'
        LOG_FILE = 'logs/test_web_app.log'
        CORS_ORIGINS = '*'
    
    # 模拟DatabaseManager
    with patch('app.DatabaseManager', MockDatabaseManager):
        from app import create_app
        app = create_app(TestConfig)
        app.db_manager = MockDatabaseManager('sqlite:///:memory:')
    
    yield app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def admin_session(client):
    """创建管理员会话"""
    response = client.post('/auth/login', json={
        'username': 'admin',
        'password': 'admin123'
    })
    assert response.status_code == 200
    return client


@pytest.fixture
def user_session(client):
    """创建普通用户会话"""
    response = client.post('/auth/login', json={
        'username': 'user',
        'password': 'user123'
    })
    assert response.status_code == 200
    return client


# ==================== 认证测试 (需求 8.1) ====================

class TestAuthentication:
    """用户认证测试"""
    
    def test_login_success(self, client):
        """测试成功登录"""
        response = client.post('/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['user']['username'] == 'admin'
        assert data['user']['role'] == 'admin'
    
    def test_login_invalid_credentials(self, client):
        """测试无效凭证登录"""
        response = client.post('/auth/login', json={
            'username': 'admin',
            'password': 'wrongpassword'
        })
        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False
    
    def test_login_nonexistent_user(self, client):
        """测试不存在的用户登录"""
        response = client.post('/auth/login', json={
            'username': 'nonexistent',
            'password': 'password'
        })
        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False
    
    def test_login_empty_credentials(self, client):
        """测试空凭证登录"""
        response = client.post('/auth/login', json={
            'username': '',
            'password': ''
        })
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
    
    def test_login_account_lockout(self, client):
        """测试账户锁定机制 (需求 8.5)"""
        # 连续3次失败登录
        for i in range(3):
            response = client.post('/auth/login', json={
                'username': 'admin',
                'password': 'wrongpassword'
            })
            if i < 2:
                assert response.status_code == 401
            else:
                # 第3次失败应该锁定账户
                assert response.status_code == 403
                data = response.get_json()
                assert '锁定' in data['message']
    
    def test_logout(self, admin_session):
        """测试登出"""
        response = admin_session.post('/auth/logout')
        assert response.status_code == 200
        
        # 验证登出后无法访问受保护资源
        response = admin_session.get('/api/devices')
        assert response.status_code == 401
    
    def test_check_session_authenticated(self, admin_session):
        """测试会话检查 - 已认证"""
        response = admin_session.get('/auth/check')
        assert response.status_code == 200
        data = response.get_json()
        assert data['authenticated'] is True
    
    def test_check_session_unauthenticated(self, client):
        """测试会话检查 - 未认证"""
        response = client.get('/auth/check')
        assert response.status_code == 401
        data = response.get_json()
        assert data['authenticated'] is False


# ==================== 权限控制测试 (需求 8.2, 8.3) ====================

class TestAuthorization:
    """权限控制测试"""
    
    def test_api_requires_login(self, client):
        """测试API需要登录"""
        endpoints = [
            '/api/devices',
            '/api/devices/conveyor/current',
            '/api/energy/summary',
            '/api/oee',
            '/api/alarms',
            '/api/thresholds'
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401, f"Endpoint {endpoint} should require login"
    
    def test_admin_only_endpoints(self, user_session):
        """测试管理员专用端点 (需求 8.4)"""
        # 普通用户尝试访问管理员端点
        response = user_session.put('/api/thresholds/1', json={
            'threshold_value': 5.0
        })
        assert response.status_code == 403
        data = response.get_json()
        assert '权限' in data['message']
        
        response = user_session.post('/api/thresholds', json={
            'device_id': 'test',
            'parameter_name': 'power',
            'threshold_value': 5.0
        })
        assert response.status_code == 403
    
    def test_admin_can_access_admin_endpoints(self, admin_session):
        """测试管理员可以访问管理员端点"""
        # 管理员可以访问阈值更新端点
        response = admin_session.put('/api/thresholds/1', json={
            'threshold_value': 5.0
        })
        # 可能返回200或404（如果阈值不存在），但不应该是403
        assert response.status_code != 403
    
    def test_normal_user_can_view_data(self, user_session):
        """测试普通用户可以查看数据 (需求 8.3)"""
        endpoints = [
            '/api/devices',
            '/api/devices/conveyor/current',
            '/api/energy/summary',
            '/api/oee',
            '/api/alarms',
            '/api/thresholds'
        ]
        
        for endpoint in endpoints:
            response = user_session.get(endpoint)
            assert response.status_code == 200, f"User should be able to view {endpoint}"


# ==================== 设备API测试 ====================

class TestDeviceAPI:
    """设备API端点测试"""
    
    def test_get_devices(self, admin_session):
        """测试获取设备列表"""
        response = admin_session.get('/api/devices')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'devices' in data
        assert len(data['devices']) > 0
        assert data['total'] > 0
    
    def test_get_device_current(self, admin_session):
        """测试获取设备当前数据"""
        response = admin_session.get('/api/devices/conveyor/current')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['device_id'] == 'conveyor'
    
    def test_get_device_history(self, admin_session):
        """测试获取设备历史数据"""
        response = admin_session.get('/api/devices/conveyor/history')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'data' in data
        assert 'pagination' in data
    
    def test_get_device_history_with_time_range(self, admin_session):
        """测试带时间范围的历史数据查询"""
        start_time = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        end_time = datetime.utcnow().isoformat()
        
        response = admin_session.get(
            f'/api/devices/conveyor/history?start_time={start_time}&end_time={end_time}'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
    
    def test_get_device_history_invalid_time_format(self, admin_session):
        """测试无效时间格式"""
        response = admin_session.get('/api/devices/conveyor/history?start_time=invalid')
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False


# ==================== 能耗API测试 ====================

class TestEnergyAPI:
    """能耗API端点测试"""
    
    def test_get_energy_summary(self, admin_session):
        """测试获取能耗汇总"""
        response = admin_session.get('/api/energy/summary')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'summary' in data
    
    def test_get_energy_summary_with_device_filter(self, admin_session):
        """测试按设备过滤能耗数据"""
        response = admin_session.get('/api/energy/summary?device_id=conveyor')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
    
    def test_get_energy_summary_with_aggregate(self, admin_session):
        """测试能耗聚合查询"""
        response = admin_session.get('/api/energy/summary?aggregate=avg')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
    
    def test_get_energy_summary_invalid_aggregate(self, admin_session):
        """测试无效的聚合类型"""
        response = admin_session.get('/api/energy/summary?aggregate=invalid')
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False


# ==================== OEE API测试 ====================

class TestOEEAPI:
    """OEE API端点测试"""
    
    def test_get_oee(self, admin_session):
        """测试获取OEE数据"""
        response = admin_session.get('/api/oee')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'oee' in data
    
    def test_get_oee_with_dimension(self, admin_session):
        """测试按维度查询OEE"""
        for dimension in ['day', 'week', 'month']:
            response = admin_session.get(f'/api/oee?dimension={dimension}')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['oee']['dimension'] == dimension
    
    def test_get_oee_invalid_dimension(self, admin_session):
        """测试无效的统计维度"""
        response = admin_session.get('/api/oee?dimension=invalid')
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False


# ==================== 报警API测试 ====================

class TestAlarmAPI:
    """报警API端点测试"""
    
    def test_get_alarms(self, admin_session):
        """测试获取报警列表"""
        response = admin_session.get('/api/alarms')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'alarms' in data
        assert 'pagination' in data
        assert 'statistics' in data
    
    def test_get_alarms_with_filters(self, admin_session):
        """测试带过滤条件的报警查询"""
        response = admin_session.get('/api/alarms?device_id=station1&alarm_level=warning')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
    
    def test_get_alarms_acknowledged_filter(self, admin_session):
        """测试按确认状态过滤报警"""
        response = admin_session.get('/api/alarms?acknowledged=false')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
    
    def test_get_alarms_invalid_level(self, admin_session):
        """测试无效的报警级别"""
        response = admin_session.get('/api/alarms?alarm_level=invalid')
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
    
    def test_acknowledge_alarm(self, admin_session):
        """测试确认报警"""
        # 先获取一个未确认的报警
        response = admin_session.get('/api/alarms?acknowledged=false')
        data = response.get_json()
        
        if data['alarms']:
            alarm_id = data['alarms'][0]['id']
            
            # 确认报警
            response = admin_session.post(f'/api/alarms/{alarm_id}/acknowledge')
            assert response.status_code == 200
            ack_data = response.get_json()
            assert ack_data['success'] is True
    
    def test_acknowledge_nonexistent_alarm(self, admin_session):
        """测试确认不存在的报警"""
        response = admin_session.post('/api/alarms/99999/acknowledge')
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False


# ==================== 阈值API测试 ====================

class TestThresholdAPI:
    """阈值API端点测试"""
    
    def test_get_thresholds(self, admin_session):
        """测试获取阈值配置"""
        response = admin_session.get('/api/thresholds')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'thresholds' in data
    
    def test_get_thresholds_with_device_filter(self, admin_session):
        """测试按设备过滤阈值"""
        response = admin_session.get('/api/thresholds?device_id=conveyor')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
    
    def test_update_threshold_as_admin(self, admin_session):
        """测试管理员更新阈值"""
        # 先获取一个阈值
        response = admin_session.get('/api/thresholds')
        data = response.get_json()
        
        if data['thresholds']:
            threshold_id = data['thresholds'][0]['id']
            
            # 更新阈值
            response = admin_session.put(f'/api/thresholds/{threshold_id}', json={
                'threshold_value': 4.5,
                'alarm_level': 'critical'
            })
            assert response.status_code == 200
            update_data = response.get_json()
            assert update_data['success'] is True
    
    def test_update_threshold_as_user(self, user_session):
        """测试普通用户无法更新阈值 (需求 8.3)"""
        response = user_session.put('/api/thresholds/1', json={
            'threshold_value': 4.5
        })
        assert response.status_code == 403
        data = response.get_json()
        assert '权限' in data['message']
    
    def test_update_threshold_invalid_value(self, admin_session):
        """测试无效的阈值"""
        response = admin_session.put('/api/thresholds/1', json={
            'threshold_value': -1.0
        })
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
    
    def test_update_threshold_missing_value(self, admin_session):
        """测试缺少必需字段"""
        response = admin_session.put('/api/thresholds/1', json={})
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
    
    def test_create_threshold_as_admin(self, admin_session):
        """测试管理员创建阈值"""
        response = admin_session.post('/api/thresholds', json={
            'device_id': 'station2',
            'parameter_name': 'temperature',
            'threshold_value': 80.0,
            'alarm_level': 'warning',
            'enabled': True
        })
        # 可能返回201（创建成功）或409（已存在）
        assert response.status_code in [201, 409]
    
    def test_create_threshold_as_user(self, user_session):
        """测试普通用户无法创建阈值 (需求 8.4)"""
        response = user_session.post('/api/thresholds', json={
            'device_id': 'test',
            'parameter_name': 'power',
            'threshold_value': 5.0
        })
        assert response.status_code == 403
    
    def test_create_threshold_missing_fields(self, admin_session):
        """测试创建阈值缺少必需字段"""
        response = admin_session.post('/api/thresholds', json={
            'device_id': 'test'
        })
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
    
    def test_create_threshold_invalid_level(self, admin_session):
        """测试创建阈值使用无效的报警级别"""
        response = admin_session.post('/api/thresholds', json={
            'device_id': 'test',
            'parameter_name': 'power',
            'threshold_value': 5.0,
            'alarm_level': 'invalid'
        })
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False


# ==================== 运行测试 ====================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
