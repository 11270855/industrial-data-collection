"""
数据库完整设置脚本
一键完成数据库初始化和种子数据填充
"""

import sys
import logging
from init_database import init_database
from seed_data import seed_database

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_database():
    """完整的数据库设置流程"""
    try:
        logger.info("=" * 60)
        logger.info("能源管理系统 - 数据库设置")
        logger.info("=" * 60)
        logger.info("")
        
        # 步骤1: 初始化数据库
        logger.info("步骤 1/2: 初始化数据库表结构")
        if not init_database():
            logger.error("数据库初始化失败，设置中止")
            return False
        
        logger.info("")
        
        # 步骤2: 填充种子数据
        logger.info("步骤 2/2: 填充初始数据")
        if not seed_database():
            logger.error("种子数据填充失败")
            return False
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("✓ 数据库设置完成！")
        logger.info("=" * 60)
        logger.info("")
        logger.info("系统已准备就绪，可以开始使用。")
        logger.info("")
        
        return True
        
    except Exception as e:
        logger.error(f"数据库设置失败: {e}", exc_info=True)
        return False


if __name__ == '__main__':
    success = setup_database()
    sys.exit(0 if success else 1)
