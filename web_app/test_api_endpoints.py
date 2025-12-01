"""
API端点测试脚本
验证所有API端点是否正确注册和可访问
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_api_routes():
    """测试API路由是否正确注册"""
    from app import app
    
    print("=" * 60)
    print("API端点测试")
    print("=" * 60)
    
    # 获取所有注册的路由
    routes = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint.startswith('api.'):
            routes.append({
                'endpoint': rule.endpoint,
                'methods': ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'})),
                'path': str(rule)
            })
    
    # 按路径排序
    routes.sort(key=lambda x: x['path'])
    
    print(f"\n找到 {len(routes)} 个API端点:\n")
    
    for route in routes:
        print(f"  {route['methods']:10s} {route['path']:40s} -> {route['endpoint']}")
    
    print("\n" + "=" * 60)
    
    # 验证预期的端点
    expected_endpoints = [
        'api.get_devices',
        'api.get_device_current',
        'api.get_device_history',
        'api.get_energy_summary',
        'api.get_oee',
        'api.get_alarms',
        'api.acknowledge_alarm',
        'api.get_thresholds',
        'api.update_threshold',
        'api.create_threshold'
    ]
    
    registered_endpoints = [r['endpoint'] for r in routes]
    
    print("\n端点验证:")
    all_found = True
    for endpoint in expected_endpoints:
        if endpoint in registered_endpoints:
            print(f"  ✓ {endpoint}")
        else:
            print(f"  ✗ {endpoint} (未找到)")
            all_found = False
    
    print("\n" + "=" * 60)
    
    if all_found:
        print("\n✓ 所有预期的API端点都已正确注册!")
        return True
    else:
        print("\n✗ 部分API端点未注册")
        return False


if __name__ == '__main__':
    try:
        success = test_api_routes()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
