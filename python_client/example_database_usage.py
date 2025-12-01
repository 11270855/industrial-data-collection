"""
数据库使用示例
演示如何使用DatabaseManager和各种模型
"""

import logging
from datetime import datetime, timedelta
from config import config
from database import DatabaseManager
from models import EnergyData, ProductionData, Alarm, User, Threshold

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_save_energy_data(db_manager):
    """示例：保存能源数据"""
    logger.info("\n=== 示例 1: 保存能源数据 ===")
    
    with db_manager.get_session() as session:
        # 创建能源数据记录
        energy_record = EnergyData(
            timestamp=datetime.utcnow(),
            device_id='conveyor',
            device_name='传送带',
            power_kw=2.5,
            energy_kwh=15.3,
            status='running'
        )
        session.add(energy_record)
        logger.info(f"保存能源数据: {energy_record}")


def example_batch_save_energy_data(db_manager):
    """示例：批量保存能源数据"""
    logger.info("\n=== 示例 2: 批量保存能源数据 ===")
    
    with db_manager.get_session() as session:
        # 批量创建数据
        records = []
        devices = ['conveyor', 'station1', 'station2']
        base_time = datetime.utcnow()
        
        for i in range(10):
            for device in devices:
                record = EnergyData(
                    timestamp=base_time - timedelta(seconds=i*10),
                    device_id=device,
                    device_name=f'设备_{device}',
                    power_kw=2.0 + i * 0.1,
                    energy_kwh=10.0 + i,
                    status='running'
                )
                records.append(record)
        
        session.bulk_save_objects(records)
        logger.info(f"批量保存 {len(records)} 条能源数据")


def example_query_energy_data(db_manager):
    """示例：查询能源数据"""
    logger.info("\n=== 示例 3: 查询能源数据 ===")
    
    with db_manager.get_session() as session:
        # 查询最近的10条记录
        recent_data = session.query(EnergyData)\
            .order_by(EnergyData.timestamp.desc())\
            .limit(10)\
            .all()
        
        logger.info(f"查询到 {len(recent_data)} 条最近的能源数据")
        for data in recent_data[:3]:  # 显示前3条
            logger.info(f"  - {data.device_id}: {data.power_kw} kW @ {data.timestamp}")
        
        # 按设备查询
        conveyor_data = session.query(EnergyData)\
            .filter_by(device_id='conveyor')\
            .count()
        logger.info(f"传送带数据记录数: {conveyor_data}")


def example_query_with_time_range(db_manager):
    """示例：按时间范围查询"""
    logger.info("\n=== 示例 4: 按时间范围查询 ===")
    
    with db_manager.get_session() as session:
        # 查询最近1小时的数据
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        recent_data = session.query(EnergyData)\
            .filter(EnergyData.timestamp >= one_hour_ago)\
            .order_by(EnergyData.timestamp.desc())\
            .all()
        
        logger.info(f"最近1小时内的数据: {len(recent_data)} 条")


def example_save_production_data(db_manager):
    """示例：保存生产数据"""
    logger.info("\n=== 示例 5: 保存生产数据 ===")
    
    with db_manager.get_session() as session:
        production_record = ProductionData(
            timestamp=datetime.utcnow(),
            product_count=100,
            reject_count=5,
            runtime_seconds=3600,
            downtime_seconds=300,
            oee_percentage=85.5,
            availability=92.0,
            performance=95.0,
            quality=98.0
        )
        session.add(production_record)
        logger.info(f"保存生产数据: OEE={production_record.oee_percentage}%")


def example_create_alarm(db_manager):
    """示例：创建报警记录"""
    logger.info("\n=== 示例 6: 创建报警记录 ===")
    
    with db_manager.get_session() as session:
        alarm = Alarm(
            timestamp=datetime.utcnow(),
            device_id='station1',
            alarm_type='power_exceeded',
            alarm_level='warning',
            message='工位1功率超过阈值',
            threshold_value=5.0,
            actual_value=5.8,
            acknowledged=False
        )
        session.add(alarm)
        logger.info(f"创建报警: {alarm.message}")


def example_acknowledge_alarm(db_manager):
    """示例：确认报警"""
    logger.info("\n=== 示例 7: 确认报警 ===")
    
    with db_manager.get_session() as session:
        # 查找未确认的报警
        unacknowledged_alarms = session.query(Alarm)\
            .filter_by(acknowledged=False)\
            .all()
        
        logger.info(f"未确认的报警数: {len(unacknowledged_alarms)}")
        
        # 确认第一个报警
        if unacknowledged_alarms:
            alarm = unacknowledged_alarms[0]
            alarm.acknowledged = True
            alarm.acknowledged_by = 'admin'
            alarm.acknowledged_at = datetime.utcnow()
            logger.info(f"已确认报警 ID: {alarm.id}")


def example_query_thresholds(db_manager):
    """示例：查询阈值配置"""
    logger.info("\n=== 示例 8: 查询阈值配置 ===")
    
    with db_manager.get_session() as session:
        # 查询所有启用的阈值
        active_thresholds = session.query(Threshold)\
            .filter_by(enabled=True)\
            .all()
        
        logger.info(f"启用的阈值配置: {len(active_thresholds)}")
        for threshold in active_thresholds[:5]:  # 显示前5个
            logger.info(f"  - {threshold.device_id}.{threshold.parameter_name}: "
                       f"{threshold.threshold_value} ({threshold.alarm_level})")


def example_update_threshold(db_manager):
    """示例：更新阈值配置"""
    logger.info("\n=== 示例 9: 更新阈值配置 ===")
    
    with db_manager.get_session() as session:
        # 查找并更新阈值
        threshold = session.query(Threshold)\
            .filter_by(device_id='conveyor', parameter_name='power')\
            .first()
        
        if threshold:
            old_value = threshold.threshold_value
            threshold.threshold_value = 3.5
            threshold.updated_by = 'admin'
            threshold.updated_at = datetime.utcnow()
            logger.info(f"更新阈值: {old_value} -> {threshold.threshold_value}")


def example_user_authentication(db_manager):
    """示例：用户认证"""
    logger.info("\n=== 示例 10: 用户认证 ===")
    
    with db_manager.get_session() as session:
        # 查找用户
        user = session.query(User).filter_by(username='admin').first()
        
        if user:
            # 测试正确密码
            if user.check_password('admin123'):
                logger.info("✓ 密码验证成功")
                user.last_login = datetime.utcnow()
                user.failed_login_attempts = 0
            else:
                logger.info("✗ 密码验证失败")
                user.failed_login_attempts += 1
            
            # 检查账户锁定
            if user.is_locked():
                logger.info("⚠ 账户已被锁定")
            else:
                logger.info("✓ 账户状态正常")


def example_aggregation_query(db_manager):
    """示例：聚合查询"""
    logger.info("\n=== 示例 11: 聚合查询 ===")
    
    from sqlalchemy import func
    
    with db_manager.get_session() as session:
        # 按设备统计平均功率
        avg_power = session.query(
            EnergyData.device_id,
            func.avg(EnergyData.power_kw).label('avg_power'),
            func.max(EnergyData.power_kw).label('max_power'),
            func.count(EnergyData.id).label('record_count')
        ).group_by(EnergyData.device_id).all()
        
        logger.info("设备功率统计:")
        for device_id, avg, max_val, count in avg_power:
            logger.info(f"  - {device_id}: 平均={avg:.2f}kW, 最大={max_val:.2f}kW, 记录数={count}")


def example_with_retry(db_manager):
    """示例：使用重试机制执行操作"""
    logger.info("\n=== 示例 12: 使用重试机制 ===")
    
    def risky_operation():
        with db_manager.get_session() as session:
            # 执行可能失败的操作
            result = session.query(EnergyData).count()
            return result
    
    try:
        count = db_manager.execute_with_retry(risky_operation)
        logger.info(f"操作成功，能源数据记录数: {count}")
    except Exception as e:
        logger.error(f"操作失败: {e}")


def run_all_examples():
    """运行所有示例"""
    logger.info("=" * 60)
    logger.info("数据库使用示例")
    logger.info("=" * 60)
    
    # 创建数据库管理器
    db_manager = DatabaseManager(config.DATABASE_URI)
    
    # 连接数据库
    if not db_manager.connect():
        logger.error("无法连接到数据库")
        return
    
    try:
        # 运行所有示例
        example_save_energy_data(db_manager)
        example_batch_save_energy_data(db_manager)
        example_query_energy_data(db_manager)
        example_query_with_time_range(db_manager)
        example_save_production_data(db_manager)
        example_create_alarm(db_manager)
        example_acknowledge_alarm(db_manager)
        example_query_thresholds(db_manager)
        example_update_threshold(db_manager)
        example_user_authentication(db_manager)
        example_aggregation_query(db_manager)
        example_with_retry(db_manager)
        
        logger.info("\n" + "=" * 60)
        logger.info("所有示例执行完成")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"示例执行出错: {e}", exc_info=True)
    finally:
        # 断开连接
        db_manager.disconnect()


if __name__ == '__main__':
    run_all_examples()
