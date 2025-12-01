"""
数据库设置测试脚本
验证数据库模型和连接是否正常工作
"""

import logging
from datetime import datetime
from config import config
from database import DatabaseManager
from models import User, EnergyData, ProductionData, Alarm, Threshold

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_database_connection():
    """测试数据库连接"""
    logger.info("测试 1: 数据库连接")
    try:
        db_manager = DatabaseManager(config.DATABASE_URI)
        if db_manager.connect():
            logger.info("✓ 数据库连接成功")
            
            # 测试连接状态
            if db_manager.is_connected():
                logger.info("✓ 连接状态检查通过")
            
            # 获取连接池状态
            pool_status = db_manager.get_pool_status()
            logger.info(f"✓ 连接池状态: {pool_status}")
            
            db_manager.disconnect()
            return True
        else:
            logger.error("✗ 数据库连接失败")
            return False
    except Exception as e:
        logger.error(f"✗ 连接测试失败: {e}")
        return False


def test_user_model():
    """测试用户模型"""
    logger.info("\n测试 2: 用户模型")
    try:
        db_manager = DatabaseManager(config.DATABASE_URI)
        db_manager.connect()
        
        with db_manager.get_session() as session:
            # 查询管理员用户
            admin = session.query(User).filter_by(username='admin').first()
            if admin:
                logger.info(f"✓ 找到管理员用户: {admin.username}")
                
                # 测试密码验证
                if admin.check_password('admin123'):
                    logger.info("✓ 密码验证成功")
                else:
                    logger.error("✗ 密码验证失败")
                
                # 测试to_dict方法
                user_dict = admin.to_dict()
                logger.info(f"✓ 用户数据转换: {user_dict}")
            else:
                logger.warning("⚠ 未找到管理员用户（可能需要运行seed_data.py）")
        
        db_manager.disconnect()
        return True
    except Exception as e:
        logger.error(f"✗ 用户模型测试失败: {e}")
        return False


def test_energy_data_model():
    """测试能源数据模型"""
    logger.info("\n测试 3: 能源数据模型")
    try:
        db_manager = DatabaseManager(config.DATABASE_URI)
        db_manager.connect()
        
        with db_manager.get_session() as session:
            # 创建测试数据
            test_data = EnergyData(
                timestamp=datetime.utcnow(),
                device_id='test_device',
                device_name='测试设备',
                power_kw=2.5,
                energy_kwh=10.0,
                status='running'
            )
            session.add(test_data)
            session.commit()
            logger.info("✓ 能源数据插入成功")
            
            # 查询数据
            data = session.query(EnergyData).filter_by(device_id='test_device').first()
            if data:
                logger.info(f"✓ 能源数据查询成功: {data.to_dict()}")
                
                # 删除测试数据
                session.delete(data)
                session.commit()
                logger.info("✓ 测试数据清理完成")
            
        db_manager.disconnect()
        return True
    except Exception as e:
        logger.error(f"✗ 能源数据模型测试失败: {e}")
        return False


def test_threshold_model():
    """测试阈值模型"""
    logger.info("\n测试 4: 阈值配置模型")
    try:
        db_manager = DatabaseManager(config.DATABASE_URI)
        db_manager.connect()
        
        with db_manager.get_session() as session:
            # 查询阈值配置
            thresholds = session.query(Threshold).all()
            logger.info(f"✓ 找到 {len(thresholds)} 个阈值配置")
            
            if thresholds:
                for threshold in thresholds[:3]:  # 显示前3个
                    logger.info(f"  - {threshold.device_id}.{threshold.parameter_name}: {threshold.threshold_value}")
        
        db_manager.disconnect()
        return True
    except Exception as e:
        logger.error(f"✗ 阈值模型测试失败: {e}")
        return False


def test_reconnection():
    """测试自动重连功能"""
    logger.info("\n测试 5: 自动重连")
    try:
        db_manager = DatabaseManager(config.DATABASE_URI)
        db_manager.connect()
        
        # 断开连接
        db_manager.disconnect()
        logger.info("✓ 连接已断开")
        
        # 测试重连
        if db_manager.reconnect():
            logger.info("✓ 自动重连成功")
            db_manager.disconnect()
            return True
        else:
            logger.error("✗ 自动重连失败")
            return False
    except Exception as e:
        logger.error(f"✗ 重连测试失败: {e}")
        return False


def run_all_tests():
    """运行所有测试"""
    logger.info("=" * 60)
    logger.info("数据库设置测试套件")
    logger.info("=" * 60)
    
    tests = [
        ("数据库连接", test_database_connection),
        ("用户模型", test_user_model),
        ("能源数据模型", test_energy_data_model),
        ("阈值配置模型", test_threshold_model),
        ("自动重连", test_reconnection),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"测试 '{test_name}' 执行异常: {e}")
            results.append((test_name, False))
    
    # 输出测试结果
    logger.info("\n" + "=" * 60)
    logger.info("测试结果汇总")
    logger.info("=" * 60)
    
    passed = 0
    failed = 0
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    logger.info("=" * 60)
    logger.info(f"总计: {passed} 通过, {failed} 失败")
    logger.info("=" * 60)
    
    return failed == 0


if __name__ == '__main__':
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
