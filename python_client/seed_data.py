"""
数据库种子数据脚本
创建初始用户数据（管理员账户）和默认阈值配置
"""

import sys
import logging
from datetime import datetime
from config import config
from database import DatabaseManager
from models import User, Threshold

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def seed_users(session):
    """创建初始用户数据"""
    logger.info("正在创建初始用户...")
    
    # 检查是否已存在root用户
    existing_root = session.query(User).filter_by(username='root').first()
    if existing_root:
        logger.info("root用户已存在，更新密码...")
        existing_root.set_password('root')
        session.commit()
        logger.info("✓ root用户密码已更新")
        return
    
    # 创建root管理员账户
    root_user = User(
        username='root',
        role='admin',
        email='root@example.com',
        created_at=datetime.utcnow()
    )
    root_user.set_password('root')
    session.add(root_user)
    logger.info("✓ root管理员用户创建成功 (用户名: root, 密码: root)")
    
    session.commit()


def seed_thresholds(session):
    """创建默认阈值配置"""
    logger.info("正在创建默认阈值配置...")
    
    # 定义默认阈值
    default_thresholds = [
        # 传送带阈值
        {
            'device_id': 'conveyor',
            'parameter_name': 'power',
            'threshold_value': 3.0,
            'alarm_level': 'warning',
            'enabled': True
        },
        {
            'device_id': 'conveyor',
            'parameter_name': 'power_critical',
            'threshold_value': 4.0,
            'alarm_level': 'critical',
            'enabled': True
        },
        # 工位1阈值
        {
            'device_id': 'station1',
            'parameter_name': 'power',
            'threshold_value': 5.0,
            'alarm_level': 'warning',
            'enabled': True
        },
        {
            'device_id': 'station1',
            'parameter_name': 'power_critical',
            'threshold_value': 6.0,
            'alarm_level': 'critical',
            'enabled': True
        },
        # 工位2阈值
        {
            'device_id': 'station2',
            'parameter_name': 'power',
            'threshold_value': 5.0,
            'alarm_level': 'warning',
            'enabled': True
        },
        {
            'device_id': 'station2',
            'parameter_name': 'power_critical',
            'threshold_value': 6.0,
            'alarm_level': 'critical',
            'enabled': True
        },
        # 总能耗阈值
        {
            'device_id': 'total',
            'parameter_name': 'energy',
            'threshold_value': 100.0,
            'alarm_level': 'warning',
            'enabled': True
        },
        {
            'device_id': 'total',
            'parameter_name': 'energy_critical',
            'threshold_value': 150.0,
            'alarm_level': 'critical',
            'enabled': True
        },
    ]
    
    # 创建阈值记录
    created_count = 0
    for threshold_data in default_thresholds:
        # 检查是否已存在
        existing = session.query(Threshold).filter_by(
            device_id=threshold_data['device_id'],
            parameter_name=threshold_data['parameter_name']
        ).first()
        
        if not existing:
            threshold = Threshold(
                device_id=threshold_data['device_id'],
                parameter_name=threshold_data['parameter_name'],
                threshold_value=threshold_data['threshold_value'],
                alarm_level=threshold_data['alarm_level'],
                enabled=threshold_data['enabled'],
                updated_by='system',
                updated_at=datetime.utcnow()
            )
            session.add(threshold)
            created_count += 1
            logger.info(f"✓ 创建阈值: {threshold_data['device_id']}.{threshold_data['parameter_name']} = {threshold_data['threshold_value']}")
    
    if created_count > 0:
        session.commit()
        logger.info(f"成功创建 {created_count} 个阈值配置")
    else:
        logger.info("所有阈值配置已存在，跳过创建")


def seed_database():
    """执行数据库种子数据填充"""
    try:
        logger.info("=" * 60)
        logger.info("开始填充种子数据")
        logger.info("=" * 60)
        
        # 创建数据库管理器
        db_manager = DatabaseManager(config.DATABASE_URI)
        
        # 连接数据库
        if not db_manager.connect():
            logger.error("无法连接到数据库")
            return False
        
        # 填充数据
        with db_manager.get_session() as session:
            # 创建用户
            seed_users(session)
            
            # 创建阈值配置
            seed_thresholds(session)
        
        # 断开连接
        db_manager.disconnect()
        
        logger.info("=" * 60)
        logger.info("种子数据填充完成")
        logger.info("=" * 60)
        logger.info("")
        logger.info("默认登录信息:")
        logger.info("  管理员 - 用户名: root, 密码: root")
        logger.info("")
        logger.info("⚠️  请在生产环境中修改默认密码！")
        logger.info("")
        
        return True
        
    except Exception as e:
        logger.error(f"填充种子数据失败: {e}", exc_info=True)
        return False


if __name__ == '__main__':
    success = seed_database()
    sys.exit(0 if success else 1)
