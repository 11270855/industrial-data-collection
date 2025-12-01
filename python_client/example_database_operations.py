"""
数据库操作模块使用示例
演示如何使用DatabaseManager类的各种方法
"""

import logging
from datetime import datetime, timedelta
from database import DatabaseManager
from config import config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def example_save_energy_data(db_manager):
    """示例：保存能源数据"""
    logger.info("=== 示例：保存能源数据 ===")
    
    # 单条数据
    single_data = [{
        'timestamp': datetime.utcnow(),
        'device_id': 'conveyor',
        'device_name': '传送带',
        'power_kw': 2.5,
        'energy_kwh': 15.3,
        'status': 'running'
    }]
    
    count = db_manager.save_energy_data(single_data)
    logger.info(f"保存了 {count} 条能源数据")
    
    # 批量数据
    batch_data = []
    for i in range(5):
        batch_data.append({
            'timestamp': datetime.utcnow() - timedelta(seconds=i*10),
            'device_id': f'station{i%2 + 1}',
            'device_name': f'工位{i%2 + 1}',
            'power_kw': 3.0 + i * 0.5,
            'energy_kwh': 20.0 + i * 2,
            'status': 'running'
        })
    
    count = db_manager.save_energy_data(batch_data)
    logger.info(f"批量保存了 {count} 条能源数据")


def example_save_production_data(db_manager):
    """示例：保存生产数据"""
    logger.info("=== 示例：保存生产数据 ===")
    
    production_data = {
        'timestamp': datetime.utcnow(),
        'product_count': 100,
        'reject_count': 5,
        'runtime_seconds': 3600,
        'downtime_seconds': 300,
        'oee_percentage': 85.5,
        'availability': 92.3,
        'performance': 95.0,
        'quality': 95.0
    }
    
    success = db_manager.save_production_data(production_data)
    logger.info(f"保存生产数据: {'成功' if success else '失败'}")


def example_save_alarm(db_manager):
    """示例：保存报警数据"""
    logger.info("=== 示例：保存报警数据 ===")
    
    alarm_data = {
        'timestamp': datetime.utcnow(),
        'device_id': 'station1',
        'alarm_type': 'power_exceeded',
        'alarm_level': 'warning',
        'message': '工位1功率超过阈值',
        'threshold_value': 5.0,
        'actual_value': 5.8
    }
    
    success = db_manager.save_alarm(alarm_data)
    logger.info(f"保存报警数据: {'成功' if success else '失败（可能是重复报警）'}")
    
    # 尝试保存重复报警（应该被去重）
    success = db_manager.save_alarm(alarm_data)
    logger.info(f"保存重复报警: {'成功' if success else '失败（已去重）'}")


def example_query_history(db_manager):
    """示例：查询历史数据"""
    logger.info("=== 示例：查询历史数据 ===")
    
    # 查询能源数据（分页）
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=1)
    
    result = db_manager.query_history(
        table_name='energy_data',
        start_time=start_time,
        end_time=end_time,
        device_id='conveyor',
        page=1,
        page_size=10
    )
    
    if result:
        logger.info(f"查询到 {result['total']} 条能源数据记录")
        logger.info(f"当前页: {result['page']}/{result['total_pages']}")
        logger.info(f"返回 {len(result['data'])} 条记录")
    
    # 查询生产数据
    result = db_manager.query_history(
        table_name='production_data',
        start_time=start_time,
        end_time=end_time,
        page=1,
        page_size=10
    )
    
    if result:
        logger.info(f"查询到 {result['total']} 条生产数据记录")
    
    # 查询报警数据
    result = db_manager.query_history(
        table_name='alarms',
        start_time=start_time,
        end_time=end_time,
        page=1,
        page_size=10
    )
    
    if result:
        logger.info(f"查询到 {result['total']} 条报警记录")


def example_aggregate_query(db_manager):
    """示例：聚合查询"""
    logger.info("=== 示例：聚合查询 ===")
    
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=7)
    
    # 按小时聚合能源数据（平均功率）
    result = db_manager.query_history(
        table_name='energy_data',
        start_time=start_time,
        end_time=end_time,
        aggregate='avg',
        aggregate_interval='hour'
    )
    
    if result:
        logger.info(f"按小时聚合查询: {result['aggregate']} - {result['aggregate_interval']}")
        logger.info(f"返回 {result['total']} 条聚合记录")
    
    # 按天聚合生产数据（平均OEE）
    result = db_manager.query_history(
        table_name='production_data',
        start_time=start_time,
        end_time=end_time,
        aggregate='avg',
        aggregate_interval='day'
    )
    
    if result:
        logger.info(f"按天聚合查询: {result['aggregate']} - {result['aggregate_interval']}")
        logger.info(f"返回 {result['total']} 条聚合记录")


def main():
    """主函数"""
    logger.info("开始数据库操作示例")
    
    # 创建数据库管理器
    db_manager = DatabaseManager(config.DATABASE_URI)
    
    # 连接数据库
    if not db_manager.connect():
        logger.error("数据库连接失败")
        return
    
    try:
        # 创建表（如果不存在）
        db_manager.create_tables()
        
        # 示例1：保存能源数据
        example_save_energy_data(db_manager)
        
        # 示例2：保存生产数据
        example_save_production_data(db_manager)
        
        # 示例3：保存报警数据
        example_save_alarm(db_manager)
        
        # 示例4：查询历史数据
        example_query_history(db_manager)
        
        # 示例5：聚合查询
        example_aggregate_query(db_manager)
        
        # 查看连接池状态
        pool_status = db_manager.get_pool_status()
        logger.info(f"连接池状态: {pool_status}")
        
    except Exception as e:
        logger.error(f"执行示例时出错: {e}", exc_info=True)
    
    finally:
        # 断开连接
        db_manager.disconnect()
        logger.info("数据库操作示例完成")


if __name__ == '__main__':
    main()
