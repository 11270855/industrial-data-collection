"""
数据采集主程序集成测试
验证各模块是否正确集成
"""

import sys
import logging
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

# 配置基本日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_imports():
    """测试所有模块导入"""
    logger.info("测试模块导入...")
    
    try:
        from main import DataCollector, setup_logging, parse_arguments
        from config import config
        from opcua_client import OPCUAClient
        from database import DatabaseManager
        from data_processor import DataProcessor
        from alarm_handler import AlarmHandler
        
        logger.info("✓ 所有模块导入成功")
        return True
    except ImportError as e:
        logger.error(f"✗ 模块导入失败: {e}")
        return False


def test_data_collector_initialization():
    """测试DataCollector初始化"""
    logger.info("测试DataCollector初始化...")
    
    try:
        from main import DataCollector
        from config import config
        
        collector = DataCollector(config)
        
        assert collector.config is not None
        assert collector.is_running == False
        assert collector.shutdown_requested == False
        assert isinstance(collector.energy_data_buffer, list)
        assert len(collector.energy_data_buffer) == 0
        
        logger.info("✓ DataCollector初始化成功")
        return True
    except Exception as e:
        logger.error(f"✗ DataCollector初始化失败: {e}")
        return False


def test_data_collection_flow():
    """测试数据采集流程（使用Mock）"""
    logger.info("测试数据采集流程...")
    
    try:
        from main import DataCollector
        from config import config
        
        collector = DataCollector(config)
        
        # Mock各模块
        collector.opcua_client = Mock()
        collector.db_manager = Mock()
        collector.data_processor = Mock()
        collector.alarm_handler = Mock()
        
        # 模拟设备数据
        mock_device_data = {
            'device_id': 'conveyor',
            'device_name': '传送带',
            'power': 2.5,
            'speed': 1.5,
            'start': True,
            'timestamp': datetime.utcnow()
        }
        
        # 模拟清洗后的数据
        mock_cleaned_data = {
            'device_id': 'conveyor',
            'device_name': '传送带',
            'power_kw': 2.5,
            'timestamp': datetime.utcnow()
        }
        
        collector.data_processor.clean_data.return_value = mock_cleaned_data
        collector.alarm_handler.check_thresholds.return_value = []
        
        # 测试数据处理和存储
        collector.process_and_store_data(mock_device_data)
        
        # 验证调用
        assert collector.data_processor.clean_data.called
        assert len(collector.energy_data_buffer) > 0
        
        logger.info("✓ 数据采集流程测试通过")
        return True
    except Exception as e:
        logger.error(f"✗ 数据采集流程测试失败: {e}")
        return False


def test_batch_write():
    """测试批量写入功能"""
    logger.info("测试批量写入功能...")
    
    try:
        from main import DataCollector
        from config import config
        
        collector = DataCollector(config)
        
        # Mock数据库管理器
        collector.db_manager = Mock()
        collector.db_manager.save_energy_data.return_value = 3
        
        # 添加测试数据到缓存
        collector.energy_data_buffer = [
            {'device_id': 'conveyor', 'power_kw': 2.5},
            {'device_id': 'station1', 'power_kw': 3.0},
            {'device_id': 'station2', 'power_kw': 2.8}
        ]
        
        # 执行批量写入
        collector.batch_write_energy_data()
        
        # 验证
        assert collector.db_manager.save_energy_data.called
        assert len(collector.energy_data_buffer) == 0
        
        logger.info("✓ 批量写入功能测试通过")
        return True
    except Exception as e:
        logger.error(f"✗ 批量写入功能测试失败: {e}")
        return False


def test_alarm_processing():
    """测试报警处理"""
    logger.info("测试报警处理...")
    
    try:
        from main import DataCollector
        from config import config
        
        collector = DataCollector(config)
        
        # Mock模块
        collector.data_processor = Mock()
        collector.alarm_handler = Mock()
        
        # 模拟清洗后的数据
        mock_cleaned_data = {
            'device_id': 'conveyor',
            'device_name': '传送带',
            'power_kw': 8.5,  # 超过阈值
            'timestamp': datetime.utcnow()
        }
        
        # 模拟触发的报警
        mock_alarms = [
            {
                'device_id': 'conveyor',
                'alarm_type': 'power_kw_threshold',
                'alarm_level': 'warning',
                'message': '功率超过阈值'
            }
        ]
        
        collector.data_processor.clean_data.return_value = mock_cleaned_data
        collector.alarm_handler.check_thresholds.return_value = mock_alarms
        collector.alarm_handler.process_alarms.return_value = 1
        
        # 设置阈值缓存
        collector.thresholds_cache = [
            {
                'device_id': 'conveyor',
                'parameter_name': 'power_kw',
                'threshold_value': 5.0,
                'alarm_level': 'warning',
                'enabled': True
            }
        ]
        
        # 处理数据
        collector.process_and_store_data({'device_id': 'conveyor', 'power_kw': 8.5})
        
        # 验证报警处理被调用
        assert collector.alarm_handler.check_thresholds.called
        assert collector.alarm_handler.process_alarms.called
        
        logger.info("✓ 报警处理测试通过")
        return True
    except Exception as e:
        logger.error(f"✗ 报警处理测试失败: {e}")
        return False


def test_graceful_shutdown():
    """测试优雅关闭"""
    logger.info("测试优雅关闭...")
    
    try:
        from main import DataCollector
        from config import config
        
        collector = DataCollector(config)
        collector.is_running = True
        
        # Mock模块
        collector.opcua_client = Mock()
        collector.db_manager = Mock()
        
        # 添加未提交的数据
        collector.energy_data_buffer = [
            {'device_id': 'conveyor', 'power_kw': 2.5}
        ]
        
        collector.db_manager.save_energy_data.return_value = 1
        
        # 执行关闭
        collector.shutdown()
        
        # 验证
        assert collector.is_running == False
        assert collector.db_manager.save_energy_data.called
        assert collector.opcua_client.disconnect.called
        assert collector.db_manager.disconnect.called
        
        logger.info("✓ 优雅关闭测试通过")
        return True
    except Exception as e:
        logger.error(f"✗ 优雅关闭测试失败: {e}")
        return False


def test_command_line_arguments():
    """测试命令行参数解析"""
    logger.info("测试命令行参数解析...")
    
    try:
        from main import parse_arguments
        
        # 测试默认参数
        with patch('sys.argv', ['main.py']):
            args = parse_arguments()
            assert args.log_level is None
            assert args.config is None
            assert args.test_connection == False
        
        # 测试自定义参数
        with patch('sys.argv', ['main.py', '--log-level', 'DEBUG', '--test-connection']):
            args = parse_arguments()
            assert args.log_level == 'DEBUG'
            assert args.test_connection == True
        
        logger.info("✓ 命令行参数解析测试通过")
        return True
    except Exception as e:
        logger.error(f"✗ 命令行参数解析测试失败: {e}")
        return False


def run_all_tests():
    """运行所有测试"""
    logger.info("=" * 60)
    logger.info("开始运行集成测试")
    logger.info("=" * 60)
    
    tests = [
        ("模块导入", test_imports),
        ("DataCollector初始化", test_data_collector_initialization),
        ("数据采集流程", test_data_collection_flow),
        ("批量写入", test_batch_write),
        ("报警处理", test_alarm_processing),
        ("优雅关闭", test_graceful_shutdown),
        ("命令行参数", test_command_line_arguments)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"测试 {test_name} 执行异常: {e}")
            results.append((test_name, False))
        
        logger.info("")
    
    # 输出测试结果
    logger.info("=" * 60)
    logger.info("测试结果汇总")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        logger.info(f"{test_name}: {status}")
    
    logger.info("=" * 60)
    logger.info(f"总计: {passed}/{total} 测试通过")
    logger.info("=" * 60)
    
    return passed == total


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
