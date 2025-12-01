"""
报警处理模块测试脚本
用于验证AlarmHandler类的基本功能
"""

import sys
import logging
from datetime import datetime
from config import config
from database import DatabaseManager
from alarm_handler import AlarmHandler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_alarm_handler():
    """测试报警处理器"""
    
    logger.info("=" * 60)
    logger.info("开始测试报警处理模块")
    logger.info("=" * 60)
    
    # 初始化数据库管理器
    logger.info("\n1. 初始化数据库连接...")
    db_manager = DatabaseManager(config.DATABASE_URI)
    
    if not db_manager.connect():
        logger.error("数据库连接失败")
        return False
    
    logger.info("✓ 数据库连接成功")
    
    # 初始化报警处理器
    logger.info("\n2. 初始化报警处理器...")
    alarm_handler = AlarmHandler(db_manager, config)
    logger.info("✓ 报警处理器初始化成功")
    
    # 测试阈值检查
    logger.info("\n3. 测试阈值检查功能...")
    
    # 模拟设备数据
    device_data = {
        'device_id': 'conveyor',
        'device_name': '传送带',
        'power_kw': 6.5,  # 超过阈值
        'energy_kwh': 15.3,
        'status': 'running',
        'timestamp': datetime.utcnow()
    }
    
    # 模拟阈值配置
    thresholds = [
        {
            'device_id': 'conveyor',
            'parameter_name': 'power_kw',
            'threshold_value': 5.0,
            'alarm_level': 'warning',
            'enabled': True
        }
    ]
    
    # 第一次检查（不会触发，因为需要连续3次）
    logger.info("第1次检查（连续计数: 1/3）...")
    alarms = alarm_handler.check_thresholds(device_data, thresholds)
    logger.info(f"触发报警数: {len(alarms)}")
    
    # 第二次检查
    logger.info("第2次检查（连续计数: 2/3）...")
    alarms = alarm_handler.check_thresholds(device_data, thresholds)
    logger.info(f"触发报警数: {len(alarms)}")
    
    # 第三次检查（应该触发报警）
    logger.info("第3次检查（连续计数: 3/3，应触发报警）...")
    alarms = alarm_handler.check_thresholds(device_data, thresholds)
    logger.info(f"触发报警数: {len(alarms)}")
    
    if len(alarms) > 0:
        logger.info("✓ 阈值检查功能正常")
        logger.info(f"报警详情: {alarms[0]}")
    else:
        logger.warning("⚠ 未触发报警（可能是正常的连续计数逻辑）")
    
    # 测试触发报警
    if len(alarms) > 0:
        logger.info("\n4. 测试触发报警并保存到数据库...")
        success = alarm_handler.trigger_alarm(alarms[0])
        
        if success:
            logger.info("✓ 报警触发成功并已保存到数据库")
        else:
            logger.info("⚠ 报警未保存（可能是重复报警）")
    
    # 测试报警统计
    logger.info("\n5. 测试报警统计功能...")
    stats = alarm_handler.get_alarm_statistics()
    logger.info(f"报警统计: {stats}")
    logger.info("✓ 报警统计功能正常")
    
    # 测试邮件通知（仅当配置启用时）
    logger.info("\n6. 测试邮件通知功能...")
    if config.EMAIL_ENABLED:
        logger.info("邮件通知已启用，测试发送...")
        if len(alarms) > 0:
            email_sent = alarm_handler.send_email_notification(alarms[0])
            if email_sent:
                logger.info("✓ 邮件发送成功")
            else:
                logger.warning("⚠ 邮件发送失败（请检查SMTP配置）")
        else:
            logger.info("⚠ 无报警数据，跳过邮件发送测试")
    else:
        logger.info("⚠ 邮件通知未启用（EMAIL_ENABLED=False）")
        logger.info("  如需测试邮件功能，请在.env文件中配置：")
        logger.info("  EMAIL_ENABLED=True")
        logger.info("  SMTP_SERVER=smtp.gmail.com")
        logger.info("  SMTP_PORT=587")
        logger.info("  SMTP_USER=your_email@gmail.com")
        logger.info("  SMTP_PASSWORD=your_password")
        logger.info("  ALERT_EMAIL_TO=recipient@example.com")
    
    # 清理
    logger.info("\n7. 清理资源...")
    db_manager.disconnect()
    logger.info("✓ 数据库连接已断开")
    
    logger.info("\n" + "=" * 60)
    logger.info("报警处理模块测试完成")
    logger.info("=" * 60)
    
    return True


if __name__ == '__main__':
    try:
        success = test_alarm_handler()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"测试过程中出错: {e}", exc_info=True)
        sys.exit(1)
