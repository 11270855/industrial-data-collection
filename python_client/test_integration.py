"""
集成测试套件
测试OPC UA通信、数据库操作和端到端数据流

需求覆盖:
- 3.4: OPC UA通信集成测试
- 4.1: 数据库操作集成测试
- 9.1: 端到端数据流测试

注意: 
- OPC UA测试需要KepServer运行
- 数据库测试需要数据库已初始化
"""

import sys
import logging
import time
from datetime import datetime, timedelta
from config import config
from opcua_client import OPCUAClient
from database import DatabaseManager
from models import EnergyData, ProductionData, Alarm, Threshold

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestOPCUACommunication:
    """OPC UA通信集成测试 (需求 3.4)"""
    
    def __init__(self):
        self.opcua_client = None
    
    def test_opcua_connection(self):
        """测试OPC UA服务器连接"""
        logger.info("\n测试 1: OPC UA服务器连接")
        try:
            # 临时修改重试次数以加快测试
            original_retry = config.OPC_UA_RETRY_MAX
            config.OPC_UA_RETRY_MAX = 1
            
            self.opcua_client = OPCUAClient(config.OPC_UA_SERVER_URL)
            
            if self.opcua_client.connect():
                logger.info(f"✓ 成功连接到OPC UA服务器: {config.OPC_UA_SERVER_URL}")
                config.OPC_UA_RETRY_MAX = original_retry
                return True
            else:
                logger.error("✗ 无法连接到OPC UA服务器")
                logger.warning("⚠ 请确保KepServer正在运行")
                config.OPC_UA_RETRY_MAX = original_retry
                return False
        except Exception as e:
            logger.error(f"✗ OPC UA连接测试失败: {e}")
            config.OPC_UA_RETRY_MAX = original_retry
            return False
    
    def test_read_single_node(self):
        """测试读取单个节点"""
        logger.info("\n测试 2: 读取单个OPC UA节点")
        try:
            if not self.opcua_client or not self.opcua_client.is_connected():
                logger.warning("⚠ 跳过测试 - OPC UA未连接")
                return False
            
            # 读取传送带启动状态
            node_id = config.OPC_UA_NODES['conveyor']['start']
            value = self.opcua_client.read_node(node_id)
            
            if value is not None:
                logger.info(f"✓ 成功读取节点 {node_id}: {value}")
                return True
            else:
                logger.error(f"✗ 读取节点失败: {node_id}")
                return False
        except Exception as e:
            logger.error(f"✗ 读取节点测试失败: {e}")
            return False
    
    def test_read_multiple_nodes(self):
        """测试批量读取节点"""
        logger.info("\n测试 3: 批量读取OPC UA节点")
        try:
            if not self.opcua_client or not self.opcua_client.is_connected():
                logger.warning("⚠ 跳过测试 - OPC UA未连接")
                return False
            
            # 读取所有传送带相关节点
            node_ids = list(config.OPC_UA_NODES['conveyor'].values())
            values = self.opcua_client.read_nodes(node_ids)
            
            if values:
                logger.info(f"✓ 成功批量读取 {len(values)} 个节点")
                for node_id, value in zip(node_ids, values):
                    logger.info(f"  - {node_id}: {value}")
                return True
            else:
                logger.error("✗ 批量读取节点失败")
                return False
        except Exception as e:
            logger.error(f"✗ 批量读取测试失败: {e}")
            return False
    
    def test_read_all_devices(self):
        """测试读取所有设备数据"""
        logger.info("\n测试 4: 读取所有设备数据")
        try:
            if not self.opcua_client or not self.opcua_client.is_connected():
                logger.warning("⚠ 跳过测试 - OPC UA未连接")
                return False
            
            devices = ['conveyor', 'station1', 'station2']
            success_count = 0
            
            for device in devices:
                node_ids = list(config.OPC_UA_NODES[device].values())
                values = self.opcua_client.read_nodes(node_ids)
                
                if values:
                    logger.info(f"✓ 成功读取设备 {device} 的数据")
                    success_count += 1
                else:
                    logger.error(f"✗ 读取设备 {device} 失败")
            
            return success_count == len(devices)
        except Exception as e:
            logger.error(f"✗ 读取所有设备测试失败: {e}")
            return False
    
    def test_opcua_reconnection(self):
        """测试OPC UA自动重连"""
        logger.info("\n测试 5: OPC UA自动重连")
        try:
            if not self.opcua_client:
                logger.warning("⚠ 跳过测试 - OPC UA客户端未初始化")
                return False
            
            # 断开连接
            self.opcua_client.disconnect()
            logger.info("✓ 已断开OPC UA连接")
            
            # 尝试重连
            if self.opcua_client.reconnect():
                logger.info("✓ OPC UA自动重连成功")
                return True
            else:
                logger.error("✗ OPC UA自动重连失败")
                return False
        except Exception as e:
            logger.error(f"✗ 重连测试失败: {e}")
            return False
    
    def cleanup(self):
        """清理资源"""
        if self.opcua_client:
            self.opcua_client.disconnect()


class TestDatabaseOperations:
    """数据库操作集成测试 (需求 4.1)"""
    
    def __init__(self):
        self.db_manager = None
    
    def test_database_connection(self):
        """测试数据库连接"""
        logger.info("\n测试 6: 数据库连接")
        try:
            self.db_manager = DatabaseManager(config.DATABASE_URI)
            
            if self.db_manager.connect():
                logger.info("✓ 数据库连接成功")
                return True
            else:
                logger.error("✗ 数据库连接失败")
                return False
        except Exception as e:
            logger.error(f"✗ 数据库连接测试失败: {e}")
            return False
    
    def test_save_energy_data(self):
        """测试保存能源数据"""
        logger.info("\n测试 7: 保存能源数据")
        try:
            if not self.db_manager or not self.db_manager.is_connected():
                logger.warning("⚠ 跳过测试 - 数据库未连接")
                return False
            
            # 创建测试数据
            test_data = [
                {
                    'timestamp': datetime.utcnow(),
                    'device_id': 'test_conveyor',
                    'device_name': '测试传送带',
                    'power_kw': 2.5,
                    'energy_kwh': 10.0,
                    'status': 'running'
                },
                {
                    'timestamp': datetime.utcnow(),
                    'device_id': 'test_station1',
                    'device_name': '测试工位1',
                    'power_kw': 3.0,
                    'energy_kwh': 12.0,
                    'status': 'running'
                }
            ]
            
            # 保存数据
            saved_count = self.db_manager.save_energy_data(test_data)
            
            if saved_count == len(test_data):
                logger.info(f"✓ 成功保存 {saved_count} 条能源数据")
                return True
            else:
                logger.error(f"✗ 保存数据失败，预期 {len(test_data)} 条，实际 {saved_count} 条")
                return False
        except Exception as e:
            logger.error(f"✗ 保存能源数据测试失败: {e}")
            return False
    
    def test_query_energy_data(self):
        """测试查询能源数据"""
        logger.info("\n测试 8: 查询能源数据")
        try:
            if not self.db_manager or not self.db_manager.is_connected():
                logger.warning("⚠ 跳过测试 - 数据库未连接")
                return False
            
            # 查询最近的数据
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=1)
            
            data = self.db_manager.get_energy_data(
                device_id='test_conveyor',
                start_time=start_time,
                end_time=end_time
            )
            
            if data is not None:
                logger.info(f"✓ 成功查询到 {len(data)} 条能源数据")
                return True
            else:
                logger.error("✗ 查询能源数据失败")
                return False
        except Exception as e:
            logger.error(f"✗ 查询能源数据测试失败: {e}")
            return False
    
    def test_save_production_data(self):
        """测试保存生产数据"""
        logger.info("\n测试 9: 保存生产数据")
        try:
            if not self.db_manager or not self.db_manager.is_connected():
                logger.warning("⚠ 跳过测试 - 数据库未连接")
                return False
            
            # 创建测试数据
            test_data = {
                'timestamp': datetime.utcnow(),
                'product_count': 100,
                'reject_count': 5,
                'runtime_minutes': 60,
                'downtime_minutes': 5,
                'availability': 0.92,
                'performance': 0.95,
                'quality': 0.95,
                'oee': 0.83
            }
            
            # 保存数据
            if self.db_manager.save_production_data(test_data):
                logger.info("✓ 成功保存生产数据")
                return True
            else:
                logger.error("✗ 保存生产数据失败")
                return False
        except Exception as e:
            logger.error(f"✗ 保存生产数据测试失败: {e}")
            return False
    
    def test_save_alarm(self):
        """测试保存报警"""
        logger.info("\n测试 10: 保存报警")
        try:
            if not self.db_manager or not self.db_manager.is_connected():
                logger.warning("⚠ 跳过测试 - 数据库未连接")
                return False
            
            # 创建测试报警
            test_alarms = [
                {
                    'timestamp': datetime.utcnow(),
                    'device_id': 'test_conveyor',
                    'alarm_type': 'power_threshold',
                    'alarm_level': 'warning',
                    'message': '功率超过阈值',
                    'threshold_value': 5.0,
                    'actual_value': 6.5,
                    'acknowledged': False
                }
            ]
            
            # 保存报警
            saved_count = self.db_manager.save_alarms(test_alarms)
            
            if saved_count == len(test_alarms):
                logger.info(f"✓ 成功保存 {saved_count} 条报警")
                return True
            else:
                logger.error(f"✗ 保存报警失败")
                return False
        except Exception as e:
            logger.error(f"✗ 保存报警测试失败: {e}")
            return False
    
    def test_get_thresholds(self):
        """测试获取阈值配置"""
        logger.info("\n测试 11: 获取阈值配置")
        try:
            if not self.db_manager or not self.db_manager.is_connected():
                logger.warning("⚠ 跳过测试 - 数据库未连接")
                return False
            
            thresholds = self.db_manager.get_thresholds()
            
            if thresholds is not None:
                logger.info(f"✓ 成功获取 {len(thresholds)} 个阈值配置")
                return True
            else:
                logger.error("✗ 获取阈值配置失败")
                return False
        except Exception as e:
            logger.error(f"✗ 获取阈值配置测试失败: {e}")
            return False
    
    def test_batch_operations(self):
        """测试批量操作性能"""
        logger.info("\n测试 12: 批量操作性能")
        try:
            if not self.db_manager or not self.db_manager.is_connected():
                logger.warning("⚠ 跳过测试 - 数据库未连接")
                return False
            
            # 创建100条测试数据
            batch_size = 100
            test_data = []
            for i in range(batch_size):
                test_data.append({
                    'timestamp': datetime.utcnow(),
                    'device_id': f'test_device_{i % 3}',
                    'device_name': f'测试设备{i % 3}',
                    'power_kw': 2.5 + (i % 10) * 0.1,
                    'energy_kwh': 10.0 + i * 0.5,
                    'status': 'running'
                })
            
            # 测试批量保存
            start_time = time.time()
            saved_count = self.db_manager.save_energy_data(test_data)
            elapsed_time = time.time() - start_time
            
            if saved_count == batch_size:
                logger.info(f"✓ 批量保存 {saved_count} 条数据，耗时 {elapsed_time:.3f} 秒")
                logger.info(f"  平均速度: {saved_count / elapsed_time:.1f} 条/秒")
                return True
            else:
                logger.error(f"✗ 批量保存失败，预期 {batch_size} 条，实际 {saved_count} 条")
                return False
        except Exception as e:
            logger.error(f"✗ 批量操作测试失败: {e}")
            return False
    
    def test_database_reconnection(self):
        """测试数据库自动重连"""
        logger.info("\n测试 13: 数据库自动重连")
        try:
            if not self.db_manager:
                logger.warning("⚠ 跳过测试 - 数据库管理器未初始化")
                return False
            
            # 断开连接
            self.db_manager.disconnect()
            logger.info("✓ 已断开数据库连接")
            
            # 尝试重连
            if self.db_manager.reconnect():
                logger.info("✓ 数据库自动重连成功")
                return True
            else:
                logger.error("✗ 数据库自动重连失败")
                return False
        except Exception as e:
            logger.error(f"✗ 重连测试失败: {e}")
            return False
    
    def cleanup(self):
        """清理测试数据"""
        logger.info("\n清理测试数据...")
        try:
            if self.db_manager and self.db_manager.is_connected():
                with self.db_manager.get_session() as session:
                    # 删除测试数据
                    session.query(EnergyData).filter(
                        EnergyData.device_id.like('test_%')
                    ).delete(synchronize_session=False)
                    
                    session.query(Alarm).filter(
                        Alarm.device_id.like('test_%')
                    ).delete(synchronize_session=False)
                    
                    session.commit()
                    logger.info("✓ 测试数据清理完成")
                
                self.db_manager.disconnect()
        except Exception as e:
            logger.error(f"✗ 清理测试数据失败: {e}")


class TestEndToEndDataFlow:
    """端到端数据流测试 (需求 9.1)"""
    
    def __init__(self):
        self.opcua_client = None
        self.db_manager = None
    
    def test_complete_data_flow(self):
        """测试完整数据流: PLC -> KepServer -> Python -> 数据库"""
        logger.info("\n测试 14: 端到端数据流")
        try:
            # 1. 连接OPC UA服务器
            logger.info("步骤 1: 连接OPC UA服务器...")
            self.opcua_client = OPCUAClient(config.OPC_UA_SERVER_URL)
            if not self.opcua_client.connect():
                logger.error("✗ 无法连接OPC UA服务器")
                logger.warning("⚠ 请确保KepServer正在运行")
                return False
            logger.info("✓ OPC UA连接成功")
            
            # 2. 连接数据库
            logger.info("步骤 2: 连接数据库...")
            self.db_manager = DatabaseManager(config.DATABASE_URI)
            if not self.db_manager.connect():
                logger.error("✗ 数据库连接失败")
                return False
            logger.info("✓ 数据库连接成功")
            
            # 3. 从OPC UA读取数据
            logger.info("步骤 3: 从OPC UA读取设备数据...")
            device_data = {}
            
            for device_id in ['conveyor', 'station1', 'station2']:
                node_ids = list(config.OPC_UA_NODES[device_id].values())
                values = self.opcua_client.read_nodes(node_ids)
                
                if values:
                    device_data[device_id] = dict(zip(
                        config.OPC_UA_NODES[device_id].keys(),
                        values
                    ))
                    logger.info(f"✓ 读取设备 {device_id} 数据成功")
                else:
                    logger.error(f"✗ 读取设备 {device_id} 数据失败")
                    return False
            
            # 4. 处理和转换数据
            logger.info("步骤 4: 处理和转换数据...")
            energy_data_list = []
            
            for device_id, data in device_data.items():
                # 提取功率数据
                power_value = data.get('power', 0.0)
                
                energy_record = {
                    'timestamp': datetime.utcnow(),
                    'device_id': device_id,
                    'device_name': f'{device_id}_设备',
                    'power_kw': float(power_value) if power_value is not None else 0.0,
                    'energy_kwh': 0.0,
                    'status': 'running'
                }
                energy_data_list.append(energy_record)
            
            logger.info(f"✓ 处理了 {len(energy_data_list)} 条数据记录")
            
            # 5. 保存到数据库
            logger.info("步骤 5: 保存数据到数据库...")
            saved_count = self.db_manager.save_energy_data(energy_data_list)
            
            if saved_count == len(energy_data_list):
                logger.info(f"✓ 成功保存 {saved_count} 条数据到数据库")
            else:
                logger.error(f"✗ 保存数据失败，预期 {len(energy_data_list)} 条，实际 {saved_count} 条")
                return False
            
            # 6. 验证数据已保存
            logger.info("步骤 6: 验证数据已保存...")
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=1)
            
            for device_id in device_data.keys():
                saved_data = self.db_manager.get_energy_data(
                    device_id=device_id,
                    start_time=start_time,
                    end_time=end_time
                )
                
                if saved_data and len(saved_data) > 0:
                    logger.info(f"✓ 验证设备 {device_id} 数据已保存")
                else:
                    logger.error(f"✗ 验证设备 {device_id} 数据失败")
                    return False
            
            logger.info("✓ 端到端数据流测试通过")
            return True
            
        except Exception as e:
            logger.error(f"✗ 端到端数据流测试失败: {e}")
            return False
    
    def test_data_flow_with_alarms(self):
        """测试带报警的数据流"""
        logger.info("\n测试 15: 带报警的数据流")
        try:
            if not self.opcua_client or not self.opcua_client.is_connected():
                logger.warning("⚠ 跳过测试 - OPC UA未连接")
                return False
            
            if not self.db_manager or not self.db_manager.is_connected():
                logger.warning("⚠ 跳过测试 - 数据库未连接")
                return False
            
            # 1. 获取阈值配置
            logger.info("步骤 1: 获取阈值配置...")
            thresholds = self.db_manager.get_thresholds()
            logger.info(f"✓ 获取到 {len(thresholds)} 个阈值配置")
            
            # 2. 读取设备数据
            logger.info("步骤 2: 读取设备数据...")
            node_ids = list(config.OPC_UA_NODES['conveyor'].values())
            values = self.opcua_client.read_nodes(node_ids)
            
            if not values:
                logger.error("✗ 读取设备数据失败")
                return False
            
            device_data = dict(zip(
                config.OPC_UA_NODES['conveyor'].keys(),
                values
            ))
            logger.info("✓ 读取设备数据成功")
            
            # 3. 检查阈值
            logger.info("步骤 3: 检查阈值...")
            alarms = []
            power_value = float(device_data.get('power', 0.0)) if device_data.get('power') is not None else 0.0
            
            for threshold in thresholds:
                if threshold['device_id'] == 'conveyor' and threshold['parameter_name'] == 'power_kw':
                    if power_value > threshold['threshold_value']:
                        alarm = {
                            'timestamp': datetime.utcnow(),
                            'device_id': 'conveyor',
                            'alarm_type': 'power_threshold',
                            'alarm_level': threshold['alarm_level'],
                            'message': f"功率 {power_value:.2f} kW 超过阈值 {threshold['threshold_value']:.2f} kW",
                            'threshold_value': threshold['threshold_value'],
                            'actual_value': power_value,
                            'acknowledged': False
                        }
                        alarms.append(alarm)
                        logger.info(f"✓ 检测到报警: {alarm['message']}")
            
            # 4. 保存报警
            if alarms:
                logger.info("步骤 4: 保存报警...")
                saved_count = self.db_manager.save_alarms(alarms)
                logger.info(f"✓ 保存了 {saved_count} 条报警")
            else:
                logger.info("步骤 4: 未检测到报警")
            
            logger.info("✓ 带报警的数据流测试通过")
            return True
            
        except Exception as e:
            logger.error(f"✗ 带报警的数据流测试失败: {e}")
            return False
    
    def test_continuous_data_collection(self):
        """测试连续数据采集"""
        logger.info("\n测试 16: 连续数据采集（5个周期）")
        try:
            if not self.opcua_client or not self.opcua_client.is_connected():
                logger.warning("⚠ 跳过测试 - OPC UA未连接")
                return False
            
            if not self.db_manager or not self.db_manager.is_connected():
                logger.warning("⚠ 跳过测试 - 数据库未连接")
                return False
            
            cycles = 5
            interval = 2  # 秒
            success_count = 0
            
            for i in range(cycles):
                logger.info(f"采集周期 {i + 1}/{cycles}...")
                
                # 读取数据
                node_ids = list(config.OPC_UA_NODES['conveyor'].values())
                values = self.opcua_client.read_nodes(node_ids)
                
                if values:
                    # 保存数据
                    energy_record = {
                        'timestamp': datetime.utcnow(),
                        'device_id': 'conveyor',
                        'device_name': '传送带',
                        'power_kw': float(values[2]) if values[2] is not None else 0.0,
                        'energy_kwh': 0.0,
                        'status': 'running'
                    }
                    
                    saved_count = self.db_manager.save_energy_data([energy_record])
                    if saved_count > 0:
                        success_count += 1
                        logger.info(f"✓ 周期 {i + 1} 数据保存成功")
                    else:
                        logger.error(f"✗ 周期 {i + 1} 数据保存失败")
                else:
                    logger.error(f"✗ 周期 {i + 1} 数据读取失败")
                
                if i < cycles - 1:
                    time.sleep(interval)
            
            if success_count == cycles:
                logger.info(f"✓ 连续数据采集测试通过 ({success_count}/{cycles})")
                return True
            else:
                logger.error(f"✗ 连续数据采集测试失败 ({success_count}/{cycles})")
                return False
            
        except Exception as e:
            logger.error(f"✗ 连续数据采集测试失败: {e}")
            return False
    
    def cleanup(self):
        """清理资源"""
        if self.opcua_client:
            self.opcua_client.disconnect()
        if self.db_manager:
            self.db_manager.disconnect()


def run_all_tests():
    """运行所有集成测试"""
    logger.info("=" * 70)
    logger.info("集成测试套件")
    logger.info("=" * 70)
    logger.info("\n注意:")
    logger.info("- OPC UA测试需要KepServer运行")
    logger.info("- 数据库测试需要数据库已初始化")
    logger.info("- 端到端测试需要完整系统运行\n")
    
    results = []
    
    # 测试1: OPC UA通信
    logger.info("\n" + "=" * 70)
    logger.info("第一部分: OPC UA通信测试")
    logger.info("=" * 70)
    
    opcua_test = TestOPCUACommunication()
    opcua_tests = [
        ("OPC UA连接", opcua_test.test_opcua_connection),
        ("读取单个节点", opcua_test.test_read_single_node),
        ("批量读取节点", opcua_test.test_read_multiple_nodes),
        ("读取所有设备", opcua_test.test_read_all_devices),
        ("OPC UA重连", opcua_test.test_opcua_reconnection),
    ]
    
    for test_name, test_func in opcua_tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"测试 '{test_name}' 执行异常: {e}")
            results.append((test_name, False))
    
    opcua_test.cleanup()
    
    # 测试2: 数据库操作
    logger.info("\n" + "=" * 70)
    logger.info("第二部分: 数据库操作测试")
    logger.info("=" * 70)
    
    db_test = TestDatabaseOperations()
    db_tests = [
        ("数据库连接", db_test.test_database_connection),
        ("保存能源数据", db_test.test_save_energy_data),
        ("查询能源数据", db_test.test_query_energy_data),
        ("保存生产数据", db_test.test_save_production_data),
        ("保存报警", db_test.test_save_alarm),
        ("获取阈值配置", db_test.test_get_thresholds),
        ("批量操作性能", db_test.test_batch_operations),
        ("数据库重连", db_test.test_database_reconnection),
    ]
    
    for test_name, test_func in db_tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"测试 '{test_name}' 执行异常: {e}")
            results.append((test_name, False))
    
    db_test.cleanup()
    
    # 测试3: 端到端数据流
    logger.info("\n" + "=" * 70)
    logger.info("第三部分: 端到端数据流测试")
    logger.info("=" * 70)
    
    e2e_test = TestEndToEndDataFlow()
    e2e_tests = [
        ("完整数据流", e2e_test.test_complete_data_flow),
        ("带报警的数据流", e2e_test.test_data_flow_with_alarms),
        ("连续数据采集", e2e_test.test_continuous_data_collection),
    ]
    
    for test_name, test_func in e2e_tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"测试 '{test_name}' 执行异常: {e}")
            results.append((test_name, False))
    
    e2e_test.cleanup()
    
    # 输出测试结果
    logger.info("\n" + "=" * 70)
    logger.info("测试结果汇总")
    logger.info("=" * 70)
    
    passed = 0
    failed = 0
    skipped = 0
    
    for test_name, result in results:
        if result is None:
            status = "⊘ 跳过"
            skipped += 1
        elif result:
            status = "✓ 通过"
            passed += 1
        else:
            status = "✗ 失败"
            failed += 1
        
        logger.info(f"{test_name}: {status}")
    
    logger.info("=" * 70)
    logger.info(f"总计: {passed} 通过, {failed} 失败, {skipped} 跳过")
    logger.info("=" * 70)
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
