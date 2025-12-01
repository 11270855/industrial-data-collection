"""
数据库初始化脚本
自动创建所有表和索引
"""

import sys
import logging
from config import config
from database import DatabaseManager
from models import Base

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def init_database():
    """初始化数据库"""
    try:
        logger.info("=" * 60)
        logger.info("开始初始化数据库")
        logger.info("=" * 60)
        
        # 创建数据库管理器
        db_manager = DatabaseManager(config.DATABASE_URI)
        
        # 连接数据库
        logger.info(f"数据库类型: {config.DB_TYPE}")
        logger.info(f"数据库URI: {config.DATABASE_URI}")
        
        if not db_manager.connect():
            logger.error("无法连接到数据库，初始化失败")
            return False
        
        # 创建所有表
        logger.info("正在创建数据表...")
        if not db_manager.create_tables():
            logger.error("创建数据表失败")
            return False
        
        # 验证表创建
        logger.info("验证数据表...")
        with db_manager.get_session() as session:
            # 检查表是否存在
            from sqlalchemy import inspect
            inspector = inspect(db_manager.engine)
            tables = inspector.get_table_names()
            
            expected_tables = ['energy_data', 'production_data', 'alarms', 'users', 'thresholds']
            logger.info(f"已创建的表: {tables}")
            
            for table in expected_tables:
                if table in tables:
                    logger.info(f"✓ 表 '{table}' 创建成功")
                else:
                    logger.warning(f"✗ 表 '{table}' 未找到")
        
        # 断开连接
        db_manager.disconnect()
        
        logger.info("=" * 60)
        logger.info("数据库初始化完成")
        logger.info("=" * 60)
        return True
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}", exc_info=True)
        return False


def drop_all_tables():
    """删除所有表（谨慎使用）"""
    try:
        logger.warning("=" * 60)
        logger.warning("警告：即将删除所有数据表！")
        logger.warning("=" * 60)
        
        # 创建数据库管理器
        db_manager = DatabaseManager(config.DATABASE_URI)
        
        # 连接数据库
        if not db_manager.connect():
            logger.error("无法连接到数据库")
            return False
        
        # 删除所有表
        if not db_manager.drop_tables():
            logger.error("删除数据表失败")
            return False
        
        # 断开连接
        db_manager.disconnect()
        
        logger.info("所有数据表已删除")
        return True
        
    except Exception as e:
        logger.error(f"删除数据表失败: {e}", exc_info=True)
        return False


if __name__ == '__main__':
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == '--drop':
        # 删除所有表
        response = input("确定要删除所有数据表吗？这将清除所有数据！(yes/no): ")
        if response.lower() == 'yes':
            drop_all_tables()
        else:
            logger.info("操作已取消")
    else:
        # 初始化数据库
        success = init_database()
        sys.exit(0 if success else 1)
