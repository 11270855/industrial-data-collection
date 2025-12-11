"""
数据采集主程序
整合OPC UA客户端、数据处理、数据库存储和报警处理模块
实现完整的数据采集和监控流程
"""

import sys
import signal
import time
import logging
from logging.handlers import RotatingFileHandler
import argparse
from datetime import datetime
from typing import Dict, Any, List
import os

# 导入自定义模块
from config import config
from opcua_client import OPCUAClient
from database import DatabaseManager
from data_processor import DataProcessor
from alarm_handler import AlarmHandler
from models import Threshold


class DataCollector:
    """数据采集主类"""
    
    def __init__(self, config_obj):
        """
        初始化数据采集器
        
        Args:
            config_obj: 配置对象
        """
        self.config = config_obj
        self.logger = logging.getLogger(__name__)
        
        # 初始化各模块（延迟初始化）
        self.opcua_client = None
        self.db_manager = None
        self.data_processor = None
        self.alarm_handler = None
        
        # 运行状态
        self.is_running = False
        self.shutdown_requested = False
        
        # 数据缓存（用于批量写入）
        self.energy_data_buffer = []
        self.last_batch_write_time = time.time()
        
        # 阈值配置缓存
        self.thresholds_cache = []
        self.last_threshold_update = 0
        
        self.logger.info("数据采集器初始化完成")
    
    def setup_modules(self) -> bool:
        """
        初始化所有模块
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            self.logger.info("正在初始化各模块...")
            
            # 1. 初始化数据库管理器
            self.logger.info("初始化数据库管理器...")
            self.db_manager = DatabaseManager(
                database_uri=self.config.DATABASE_URI,
                pool_size=10,
                max_overflow=20
            )
            
            if not self.db_manager.connect():
                self.logger.error("数据库连接失败")
                return False
            
            # 确保数据表存在
            self.db_manager.create_tables()
            
            # 2. 初始化数据处理器
            self.logger.info("初始化数据处理器...")
            self.data_processor = DataProcessor(config=self.config)
            
            # 3. 初始化报警处理器
            self.logger.info("初始化报警处理器...")
            self.alarm_handler = AlarmHandler(
                db_manager=self.db_manager,
                config=self.config
            )
            
            # 4. 初始化OPC UA客户端
            self.logger.info("初始化OPC UA客户端...")
            self.opcua_client = OPCUAClient(
                server_url=self.config.OPC_UA_SERVER_URL,
                timeout=self.config.OPC_UA_TIMEOUT,
                max_retries=self.config.OPC_UA_RETRY_MAX,
                retry_delay=self.config.OPC_UA_RETRY_DELAY
            )
            
            if not self.opcua_client.connect():
                self.logger.error("OPC UA连接失败")
                return False
            
            self.logger.info("所有模块初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"模块初始化失败: {e}", exc_info=True)
            return False
    
    def load_thresholds(self):
        """从数据库加载阈值配置"""
        try:
            with self.db_manager.get_session() as session:
                thresholds = session.query(Threshold).filter(
                    Threshold.enabled == True
                ).all()
                
                self.thresholds_cache = [
                    {
                        'device_id': t.device_id,
                        'parameter_name': t.parameter_name,
                        'threshold_value': float(t.threshold_value),
                        'alarm_level': t.alarm_level,
                        'enabled': t.enabled
                    }
                    for t in thresholds
                ]
                
                self.last_threshold_update = time.time()
                self.logger.info(f"已加载 {len(self.thresholds_cache)} 个阈值配置")
                
        except Exception as e:
            self.logger.error(f"加载阈值配置失败: {e}", exc_info=True)
            self.thresholds_cache = []
    
    def data_change_callback(self, node_id: str, value: Any, data):
        """
        OPC UA数据变化回调函数
        
        Args:
            node_id: 节点ID
            value: 新值
            data: 数据变化信息
        """
        try:
            self.logger.debug(f"数据变化回调: {node_id} = {value}")
            # 数据变化时的处理逻辑在主循环中实现
            
        except Exception as e:
            self.logger.error(f"数据变化回调处理失败: {e}", exc_info=True)
    
    def collect_device_data(self, device_id: str, node_config: Dict[str, str]) -> Dict[str, Any]:
        """
        采集单个设备的数据
        
        Args:
            device_id: 设备ID
            node_config: 节点配置字典
        
        Returns:
            设备数据字典
        """
        try:
            # 批量读取设备的所有节点
            node_ids = list(node_config.values())
            values = self.opcua_client.read_nodes(node_ids)
            
            # 构建设备数据
            device_data = {
                'device_id': device_id,
                'device_name': device_id,
                'timestamp': datetime.utcnow()
            }
            
            # 映射节点值到设备数据
            for key, node_id in node_config.items():
                value = values.get(node_id)
                if value is not None:
                    device_data[key] = value
            
            return device_data
            
        except Exception as e:
            self.logger.error(f"采集设备 {device_id} 数据失败: {e}")
            return None
    
    def process_and_store_data(self, device_data: Dict[str, Any]):
        """
        处理并存储设备数据
        
        Args:
            device_data: 设备数据
        """
        try:
            # 1. 数据清洗
            cleaned_data = self.data_processor.clean_data(device_data)
            
            if not cleaned_data:
                self.logger.warning(f"设备 {device_data.get('device_id')} 数据清洗失败")
                return
            
            # 2. 添加到缓存（用于批量写入）
            energy_record = {
                'timestamp': cleaned_data.get('timestamp'),
                'device_id': cleaned_data.get('device_id'),
                'device_name': cleaned_data.get('device_name'),
                'power_kw': cleaned_data.get('power_kw') or cleaned_data.get('power'),
                'energy_kwh': None,  # 能耗数据需要从PLC的累计值获取
                'status': 'running' if cleaned_data.get('active') or cleaned_data.get('start') else 'idle'
            }
            
            self.energy_data_buffer.append(energy_record)
            
            # 3. 检查报警阈值
            if self.thresholds_cache:
                triggered_alarms = self.alarm_handler.check_thresholds(
                    cleaned_data,
                    self.thresholds_cache
                )
                
                # 处理触发的报警
                if triggered_alarms:
                    self.alarm_handler.process_alarms(triggered_alarms)
            
        except Exception as e:
            self.logger.error(f"处理和存储数据失败: {e}", exc_info=True)
    
    def batch_write_energy_data(self):
        """批量写入能源数据到数据库"""
        if not self.energy_data_buffer:
            return
        
        try:
            # 批量保存到数据库
            inserted_count = self.db_manager.save_energy_data(self.energy_data_buffer)
            
            self.logger.info(f"批量写入能源数据: {inserted_count} 条记录")
            
            # 清空缓存
            self.energy_data_buffer.clear()
            self.last_batch_write_time = time.time()
            
        except Exception as e:
            self.logger.error(f"批量写入能源数据失败: {e}", exc_info=True)
    
    def collect_and_store_production_data(self):
        """采集并存储生产数据和OEE"""
        try:
            # 读取生产统计节点
            production_nodes = self.config.OPC_UA_NODES.get('production', {})
            if not production_nodes:
                return
            
            node_ids = list(production_nodes.values())
            values = self.opcua_client.read_nodes(node_ids)
            
            # 提取生产数据
            product_count = values.get(production_nodes.get('product_count'), 0)
            reject_count = values.get(production_nodes.get('reject_count'), 0)
            runtime = values.get(production_nodes.get('runtime'), 0)
            downtime = values.get(production_nodes.get('downtime'), 0)
            
            # 转换TIME类型为秒（如果需要）
            if isinstance(runtime, str):
                runtime = self._parse_time_to_seconds(runtime)
            if isinstance(downtime, str):
                downtime = self._parse_time_to_seconds(downtime)
            
            # 计算OEE
            oee_result = self.data_processor.calculate_oee(
                runtime_seconds=int(runtime) if runtime else 0,
                downtime_seconds=int(downtime) if downtime else 0,
                product_count=int(product_count) if product_count else 0,
                reject_count=int(reject_count) if reject_count else 0
            )
            
            # 构建生产数据记录
            production_data = {
                'timestamp': datetime.utcnow(),
                'product_count': int(product_count) if product_count else 0,
                'reject_count': int(reject_count) if reject_count else 0,
                'runtime_seconds': int(runtime) if runtime else 0,
                'downtime_seconds': int(downtime) if downtime else 0,
                'oee_percentage': oee_result.get('oee'),
                'availability': oee_result.get('availability'),
                'performance': oee_result.get('performance'),
                'quality': oee_result.get('quality')
            }
            
            # 保存到数据库
            self.db_manager.save_production_data(production_data)
            
            self.logger.info(f"生产数据已保存，OEE: {oee_result.get('oee')}%")
            
        except Exception as e:
            self.logger.error(f"采集和存储生产数据失败: {e}", exc_info=True)
    
    def _parse_time_to_seconds(self, time_str: str) -> int:
        """
        解析PLC TIME类型字符串为秒数
        
        Args:
            time_str: 时间字符串，如 "T#1h30m45s"
        
        Returns:
            秒数
        """
        try:
            # 简单实现，假设格式为数字（毫秒）
            return int(float(time_str) / 1000)
        except:
            return 0
    
    def run(self):
        """运行数据采集主循环"""
        self.logger.info("=" * 60)
        self.logger.info("数据采集程序启动")
        self.logger.info("=" * 60)
        
        # 初始化模块
        if not self.setup_modules():
            self.logger.error("模块初始化失败，程序退出")
            return 1
        
        # 加载阈值配置
        self.load_thresholds()
        
        # 订阅OPC UA节点
        self.logger.info("订阅OPC UA节点...")
        all_node_ids = []
        for device_id, nodes in self.config.OPC_UA_NODES.items():
            all_node_ids.extend(nodes.values())
        
        if not self.opcua_client.subscribe_nodes(all_node_ids, self.data_change_callback):
            self.logger.warning("节点订阅失败，将使用轮询模式")
        
        self.is_running = True
        self.logger.info("数据采集主循环开始运行...")
        
        last_production_collect_time = time.time()
        last_threshold_reload_time = time.time()
        
        # 连接失败计数器
        opcua_reconnect_failures = 0
        db_reconnect_failures = 0
        max_reconnect_failures = 5
        
        try:
            while self.is_running and not self.shutdown_requested:
                loop_start_time = time.time()
                
                try:
                    # 1. 采集所有设备数据
                    for device_id, node_config in self.config.OPC_UA_NODES.items():
                        if device_id == 'production' or device_id == 'energy':
                            continue  # 这些节点单独处理
                        
                        device_data = self.collect_device_data(device_id, node_config)
                        if device_data:
                            self.process_and_store_data(device_data)
                    
                    # 2. 检查是否需要批量写入
                    time_since_last_write = time.time() - self.last_batch_write_time
                    if time_since_last_write >= self.config.BATCH_WRITE_INTERVAL:
                        self.batch_write_energy_data()
                    
                    # 3. 定期采集生产数据（每30秒）
                    time_since_last_production = time.time() - last_production_collect_time
                    if time_since_last_production >= 30:
                        self.collect_and_store_production_data()
                        last_production_collect_time = time.time()
                    
                    # 4. 定期重新加载阈值配置（每5分钟）
                    time_since_threshold_reload = time.time() - last_threshold_reload_time
                    if time_since_threshold_reload >= 300:
                        self.load_thresholds()
                        last_threshold_reload_time = time.time()
                    
                    # 5. 检查OPC UA连接状态
                    if not self.opcua_client.check_connection():
                        self.logger.warning("OPC UA连接断开，尝试重连...")
                        if self.opcua_client.reconnect():
                            # 重新订阅节点
                            self.opcua_client.subscribe_nodes(all_node_ids, self.data_change_callback)
                            opcua_reconnect_failures = 0  # 重置失败计数
                        else:
                            opcua_reconnect_failures += 1
                            self.logger.error(f"OPC UA重连失败 ({opcua_reconnect_failures}/{max_reconnect_failures})")
                            if opcua_reconnect_failures >= max_reconnect_failures:
                                self.logger.error("OPC UA重连失败次数过多，程序将退出")
                                break
                    
                    # 6. 检查数据库连接状态
                    if not self.db_manager.is_connected():
                        self.logger.warning("数据库连接断开，尝试重连...")
                        if self.db_manager.reconnect():
                            db_reconnect_failures = 0  # 重置失败计数
                        else:
                            db_reconnect_failures += 1
                            self.logger.error(f"数据库重连失败 ({db_reconnect_failures}/{max_reconnect_failures})")
                            if db_reconnect_failures >= max_reconnect_failures:
                                self.logger.error("数据库重连失败次数过多，程序将退出")
                                break
                    
                except Exception as loop_error:
                    self.logger.error(f"主循环内部错误: {loop_error}", exc_info=True)
                    # 继续运行，不要因为单次错误而退出
                
                # 7. 控制循环频率
                loop_duration = time.time() - loop_start_time
                sleep_time = max(0, self.config.DATA_COLLECTION_INTERVAL - loop_duration)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            self.logger.info("接收到键盘中断信号")
        except Exception as e:
            self.logger.error(f"主循环异常: {e}", exc_info=True)
        finally:
            self.shutdown()
        
        return 0
    
    def shutdown(self):
        """优雅关闭程序"""
        if not self.is_running:
            return
        
        self.logger.info("=" * 60)
        self.logger.info("正在关闭数据采集程序...")
        self.logger.info("=" * 60)
        
        self.is_running = False
        
        try:
            # 1. 保存未提交的数据
            if self.energy_data_buffer:
                self.logger.info("保存未提交的能源数据...")
                self.batch_write_energy_data()
            
            # 2. 断开OPC UA连接
            if self.opcua_client:
                self.logger.info("断开OPC UA连接...")
                self.opcua_client.disconnect()
            
            # 3. 关闭数据库连接
            if self.db_manager:
                self.logger.info("关闭数据库连接...")
                self.db_manager.disconnect()
            
            self.logger.info("数据采集程序已安全关闭")
            
        except Exception as e:
            self.logger.error(f"关闭程序时出错: {e}", exc_info=True)


def setup_logging(config_obj):
    """
    配置日志系统
    
    Args:
        config_obj: 配置对象
    """
    # 确保日志目录存在
    log_dir = os.path.dirname(config_obj.LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 创建根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config_obj.LOG_LEVEL.upper(), logging.INFO))
    
    # 清除现有的处理器
    root_logger.handlers.clear()
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 1. 文件处理器（使用RotatingFileHandler）
    file_handler = RotatingFileHandler(
        config_obj.LOG_FILE,
        maxBytes=config_obj.LOG_MAX_BYTES,
        backupCount=config_obj.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # 2. 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 设置第三方库的日志级别
    logging.getLogger('opcua').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    
    logging.info("日志系统配置完成")


def parse_arguments():
    """
    解析命令行参数
    
    Returns:
        argparse.Namespace: 解析后的参数
    """
    parser = argparse.ArgumentParser(
        description='能源管理系统数据采集程序',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py                    # 使用默认配置运行
  python main.py --log-level DEBUG  # 使用DEBUG日志级别
  python main.py --config custom.env # 使用自定义配置文件
        """
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='日志级别（覆盖配置文件中的设置）'
    )
    
    parser.add_argument(
        '--config',
        help='配置文件路径（.env文件）'
    )
    
    parser.add_argument(
        '--test-connection',
        action='store_true',
        help='测试OPC UA和数据库连接后退出'
    )
    
    return parser.parse_args()


def test_connections(config_obj):
    """
    测试连接
    
    Args:
        config_obj: 配置对象
    
    Returns:
        bool: 所有连接是否成功
    """
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("测试连接")
    logger.info("=" * 60)
    
    success = True
    
    # 测试数据库连接
    logger.info("测试数据库连接...")
    db_manager = DatabaseManager(config_obj.DATABASE_URI)
    if db_manager.connect():
        logger.info("✓ 数据库连接成功")
        db_manager.disconnect()
    else:
        logger.error("✗ 数据库连接失败")
        success = False
    
    # 测试OPC UA连接
    logger.info("测试OPC UA连接...")
    opcua_client = OPCUAClient(
        server_url=config_obj.OPC_UA_SERVER_URL,
        timeout=config_obj.OPC_UA_TIMEOUT
    )
    if opcua_client.connect():
        logger.info("✓ OPC UA连接成功")
        opcua_client.disconnect()
    else:
        logger.error("✗ OPC UA连接失败")
        success = False
    
    logger.info("=" * 60)
    if success:
        logger.info("所有连接测试通过")
    else:
        logger.error("部分连接测试失败")
    logger.info("=" * 60)
    
    return success


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    # 加载配置文件（如果指定）
    if args.config:
        from dotenv import load_dotenv
        load_dotenv(args.config)
    
    # 覆盖日志级别（如果指定）
    if args.log_level:
        config.LOG_LEVEL = args.log_level
    
    # 配置日志系统
    setup_logging(config)
    
    logger = logging.getLogger(__name__)
    
    # 如果是测试连接模式
    if args.test_connection:
        success = test_connections(config)
        return 0 if success else 1
    
    # 创建数据采集器实例
    collector = DataCollector(config)
    
    # 设置信号处理器（用于优雅关闭）
    def signal_handler(signum, frame):
        logger.info(f"接收到信号 {signum}，准备关闭程序...")
        collector.shutdown_requested = True
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 运行数据采集程序
    return collector.run()


if __name__ == '__main__':
    sys.exit(main())
