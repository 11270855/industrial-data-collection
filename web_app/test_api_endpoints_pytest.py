"""
API端点测试 - 使用pytest
测试所有API端点、认证和权限控制

需求覆盖:
- 8.1: 用户认证测试
- 8.2: 权限控制测试  
- 8.3: 角色验证测试

注意: 本测试需要实际的数据库连接。请确保数据库已初始化并包含测试用户。
运行前请执行: python python_client/init_database.py
"""

import pytest
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 测试配置
TEST_ADMIN_USER = {'username': 'admin', 'password': 'admin123'}
TEST_NORMAL_USER = {'username': 'user', 'password': 'user123'}


def test_import_app():
    """测试应用模块可以正常导入"""
    try:
        from app import app
        assert app is not None
        print("✓ Flask应用导入成功")
    except Exception as e:
        pytest.fail(f"应用导入失败: {e}")


def test_import_routes():
    """测试路由模块可以正常导入"""
    try:
        from routes.auth import auth_bp, login_required, admin_required
        from routes.api import api_bp
        assert auth_bp is not None
        assert api_bp is not None
        assert login_required is not None
        assert admin_required is not None
        print("✓ 路由模块导入成功")
    except Exception as e:
        pytest.fail(f"路由模块导入失败: {e}")


class TestAuthenticationEndpoints:
    """认证端点测试 (需求 8.1)"""
    
    def test_login_endpoint_exists(self):
        """测试登录端点存在"""
        from app import app
        with app.test_client() as client:
            response = client.get('/auth/login')
            # 应该返回登录页面或重定向，不应该是404
            assert response.status_code != 404
            print("✓ 登录端点存在")
    
    def test_login_with_valid_credentials(self):
        """测试使用有效凭证登录"""
        from app import app
        with app.test_client() as client:
            response = client.post('/auth/login', json=TEST_ADMIN_USER)
            # 应该返回200或302（重定向）
            assert response.status_code in [200, 302]
            if response.status_code == 200:
                data = response.get_json()
                if data:
                    assert 'success' in data or 'user' in data
            print("✓ 有效凭证登录测试通过")
    
    def test_login_with_invalid_credentials(self):
        """测试使用无效凭证登录"""
        from app import app
        with app.test_client() as client:
            response = client.post('/auth/login', json={
                'username': 'admin',
                'password': 'wrongpassword'
            })
            # 应该返回401（未授权）
            assert response.status_code == 401
            print("✓ 无效凭证登录测试通过")
    
    def test_logout_endpoint(self):
        """测试登出端点"""
        from app import app
        with app.test_client() as client:
            # 先登录
            client.post('/auth/login', json=TEST_ADMIN_USER)
            # 然后登出
            response = client.post('/auth/logout')
            # 应该返回200或302
            assert response.status_code in [200, 302]
            print("✓ 登出端点测试通过")


class TestAuthorizationEndpoints:
    """权限控制测试 (需求 8.2, 8.3)"""
    
    def test_api_requires_authentication(self):
        """测试API端点需要认证"""
        from app import app
        with app.test_client() as client:
            # 未登录访问API
            response = client.get('/api/devices')
            # 应该返回401（未授权）
            assert response.status_code == 401
            print("✓ API需要认证测试通过")
    
    def test_authenticated_user_can_access_api(self):
        """测试已认证用户可以访问API"""
        from app import app
        with app.test_client() as client:
            # 登录
            client.post('/auth/login', json=TEST_ADMIN_USER)
            # 访问API
            response = client.get('/api/devices')
            # 应该返回200
            assert response.status_code == 200
            print("✓ 已认证用户访问API测试通过")
    
    def test_normal_user_cannot_update_thresholds(self):
        """测试普通用户无法更新阈值 (需求 8.3)"""
        from app import app
        with app.test_client() as client:
            # 使用普通用户登录
            client.post('/auth/login', json=TEST_NORMAL_USER)
            # 尝试更新阈值
            response = client.put('/api/thresholds/1', json={
                'threshold_value': 5.0
            })
            # 应该返回403（禁止访问）
            assert response.status_code == 403
            print("✓ 普通用户权限限制测试通过")
    
    def test_admin_can_update_thresholds(self):
        """测试管理员可以更新阈值 (需求 8.4)"""
        from app import app
        with app.test_client() as client:
            # 使用管理员登录
            client.post('/auth/login', json=TEST_ADMIN_USER)
            # 尝试更新阈值
            response = client.put('/api/thresholds/1', json={
                'threshold_value': 5.0
            })
            # 应该不是403（可能是200、404或400，但不应该是权限错误）
            assert response.status_code != 403
            print("✓ 管理员权限测试通过")


class TestDeviceAPIEndpoints:
    """设备API端点测试"""
    
    def test_get_devices(self):
        """测试获取设备列表"""
        from app import app
        with app.test_client() as client:
            client.post('/auth/login', json=TEST_ADMIN_USER)
            response = client.get('/api/devices')
            assert response.status_code == 200
            data = response.get_json()
            assert 'devices' in data or 'success' in data
            print("✓ 获取设备列表测试通过")
    
    def test_get_device_current(self):
        """测试获取设备当前数据"""
        from app import app
        with app.test_client() as client:
            client.post('/auth/login', json=TEST_ADMIN_USER)
            response = client.get('/api/devices/conveyor/current')
            assert response.status_code == 200
            print("✓ 获取设备当前数据测试通过")
    
    def test_get_device_history(self):
        """测试获取设备历史数据"""
        from app import app
        with app.test_client() as client:
            client.post('/auth/login', json=TEST_ADMIN_USER)
            response = client.get('/api/devices/conveyor/history')
            assert response.status_code == 200
            print("✓ 获取设备历史数据测试通过")


class TestEnergyAPIEndpoints:
    """能耗API端点测试"""
    
    def test_get_energy_summary(self):
        """测试获取能耗汇总"""
        from app import app
        with app.test_client() as client:
            client.post('/auth/login', json=TEST_ADMIN_USER)
            response = client.get('/api/energy/summary')
            assert response.status_code == 200
            print("✓ 获取能耗汇总测试通过")
    
    def test_get_energy_summary_with_invalid_aggregate(self):
        """测试无效的聚合类型"""
        from app import app
        with app.test_client() as client:
            client.post('/auth/login', json=TEST_ADMIN_USER)
            response = client.get('/api/energy/summary?aggregate=invalid')
            assert response.status_code == 400
            print("✓ 无效聚合类型验证测试通过")


class TestOEEAPIEndpoints:
    """OEE API端点测试"""
    
    def test_get_oee(self):
        """测试获取OEE数据"""
        from app import app
        with app.test_client() as client:
            client.post('/auth/login', json=TEST_ADMIN_USER)
            response = client.get('/api/oee')
            assert response.status_code == 200
            print("✓ 获取OEE数据测试通过")
    
    def test_get_oee_with_dimension(self):
        """测试按维度查询OEE"""
        from app import app
        with app.test_client() as client:
            client.post('/auth/login', json=TEST_ADMIN_USER)
            for dimension in ['day', 'week', 'month']:
                response = client.get(f'/api/oee?dimension={dimension}')
                assert response.status_code == 200
            print("✓ OEE维度查询测试通过")
    
    def test_get_oee_with_invalid_dimension(self):
        """测试无效的统计维度"""
        from app import app
        with app.test_client() as client:
            client.post('/auth/login', json=TEST_ADMIN_USER)
            response = client.get('/api/oee?dimension=invalid')
            assert response.status_code == 400
            print("✓ 无效维度验证测试通过")


class TestAlarmAPIEndpoints:
    """报警API端点测试"""
    
    def test_get_alarms(self):
        """测试获取报警列表"""
        from app import app
        with app.test_client() as client:
            client.post('/auth/login', json=TEST_ADMIN_USER)
            response = client.get('/api/alarms')
            assert response.status_code == 200
            print("✓ 获取报警列表测试通过")
    
    def test_get_alarms_with_filters(self):
        """测试带过滤条件的报警查询"""
        from app import app
        with app.test_client() as client:
            client.post('/auth/login', json=TEST_ADMIN_USER)
            response = client.get('/api/alarms?alarm_level=warning')
            assert response.status_code == 200
            print("✓ 报警过滤查询测试通过")
    
    def test_get_alarms_with_invalid_level(self):
        """测试无效的报警级别"""
        from app import app
        with app.test_client() as client:
            client.post('/auth/login', json=TEST_ADMIN_USER)
            response = client.get('/api/alarms?alarm_level=invalid')
            assert response.status_code == 400
            print("✓ 无效报警级别验证测试通过")
    
    def test_acknowledge_alarm_endpoint(self):
        """测试确认报警端点"""
        from app import app
        with app.test_client() as client:
            client.post('/auth/login', json=TEST_ADMIN_USER)
            # 尝试确认一个报警（可能不存在，但端点应该存在）
            response = client.post('/api/alarms/1/acknowledge')
            # 应该返回200或404，不应该是405（方法不允许）
            assert response.status_code != 405
            print("✓ 确认报警端点测试通过")


class TestThresholdAPIEndpoints:
    """阈值API端点测试"""
    
    def test_get_thresholds(self):
        """测试获取阈值配置"""
        from app import app
        with app.test_client() as client:
            client.post('/auth/login', json=TEST_ADMIN_USER)
            response = client.get('/api/thresholds')
            assert response.status_code == 200
            print("✓ 获取阈值配置测试通过")
    
    def test_update_threshold_missing_value(self):
        """测试更新阈值缺少必需字段"""
        from app import app
        with app.test_client() as client:
            client.post('/auth/login', json=TEST_ADMIN_USER)
            response = client.put('/api/thresholds/1', json={})
            assert response.status_code == 400
            print("✓ 阈值必需字段验证测试通过")
    
    def test_update_threshold_invalid_value(self):
        """测试更新阈值使用无效值"""
        from app import app
        with app.test_client() as client:
            client.post('/auth/login', json=TEST_ADMIN_USER)
            response = client.put('/api/thresholds/1', json={
                'threshold_value': -1.0
            })
            assert response.status_code == 400
            print("✓ 阈值数值验证测试通过")
    
    def test_create_threshold_missing_fields(self):
        """测试创建阈值缺少必需字段"""
        from app import app
        with app.test_client() as client:
            client.post('/auth/login', json=TEST_ADMIN_USER)
            response = client.post('/api/thresholds', json={
                'device_id': 'test'
            })
            assert response.status_code == 400
            print("✓ 创建阈值必需字段验证测试通过")
    
    def test_create_threshold_invalid_level(self):
        """测试创建阈值使用无效的报警级别"""
        from app import app
        with app.test_client() as client:
            client.post('/auth/login', json=TEST_ADMIN_USER)
            response = client.post('/api/thresholds', json={
                'device_id': 'test',
                'parameter_name': 'power',
                'threshold_value': 5.0,
                'alarm_level': 'invalid'
            })
            assert response.status_code == 400
            print("✓ 报警级别验证测试通过")


# 运行所有测试
if __name__ == '__main__':
    print("=" * 70)
    print("API端点综合测试")
    print("=" * 70)
    print("\n注意: 本测试需要实际的数据库连接和测试用户")
    print("请确保已运行: python python_client/init_database.py\n")
    
    pytest.main([__file__, '-v', '--tb=short', '-s'])
