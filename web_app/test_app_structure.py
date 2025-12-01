"""
Flask应用结构测试脚本
验证应用能够正确初始化和导入所有模块
"""

import sys
import os

# 设置输出编码为UTF-8
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def test_imports():
    """测试所有模块能否正确导入"""
    print("测试模块导入...")
    
    try:
        import config
        print("✓ 配置模块导入成功")
    except Exception as e:
        print(f"✗ 配置模块导入失败: {e}")
        return False
    
    try:
        from routes.auth import auth_bp, login_required, admin_required
        print("✓ 认证路由模块导入成功")
    except Exception as e:
        print(f"✗ 认证路由模块导入失败: {e}")
        return False
    
    try:
        from routes.dashboard import dashboard_bp
        print("✓ 仪表盘路由模块导入成功")
    except Exception as e:
        print(f"✗ 仪表盘路由模块导入失败: {e}")
        return False
    
    try:
        from routes.api import api_bp
        print("✓ API路由模块导入成功")
    except Exception as e:
        print(f"✗ API路由模块导入失败: {e}")
        return False
    
    return True


def test_app_creation():
    """测试Flask应用能否正确创建"""
    print("\n测试Flask应用创建...")
    
    try:
        from app import create_app
        app = create_app()
        print("✓ Flask应用创建成功")
        
        # 检查蓝图注册
        blueprints = list(app.blueprints.keys())
        print(f"  已注册的蓝图: {', '.join(blueprints)}")
        
        expected_blueprints = ['auth', 'dashboard', 'api']
        for bp in expected_blueprints:
            if bp in blueprints:
                print(f"  ✓ 蓝图 '{bp}' 已注册")
            else:
                print(f"  ✗ 蓝图 '{bp}' 未注册")
                return False
        
        # 检查路由
        print("\n  已注册的路由:")
        for rule in app.url_map.iter_rules():
            print(f"    {rule.endpoint}: {rule.rule} [{', '.join(rule.methods - {'HEAD', 'OPTIONS'})}]")
        
        return True
        
    except Exception as e:
        print(f"✗ Flask应用创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_decorators():
    """测试装饰器功能"""
    print("\n测试装饰器...")
    
    try:
        from routes.auth import login_required, admin_required, role_required
        print("✓ 装饰器导入成功")
        
        # 测试装饰器可以应用到函数
        @login_required
        def test_func1():
            return "test"
        
        @admin_required
        def test_func2():
            return "test"
        
        @role_required('manager')
        def test_func3():
            return "test"
        
        print("✓ 装饰器可以正常应用")
        return True
        
    except Exception as e:
        print(f"✗ 装饰器测试失败: {e}")
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("Flask Web应用基础框架测试")
    print("=" * 60)
    
    all_passed = True
    
    # 运行测试
    if not test_imports():
        all_passed = False
    
    if not test_app_creation():
        all_passed = False
    
    if not test_decorators():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ 所有测试通过！")
        print("Flask Web应用基础框架已成功实现")
    else:
        print("✗ 部分测试失败")
    print("=" * 60)
