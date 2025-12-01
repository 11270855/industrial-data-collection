"""
OPC UA客户端使用示例
演示如何使用OPCUAClient类连接、订阅和读取数据
"""

import logging
import time
from opcua_client import OPCUAClient
from config import config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def data_change_callback(node_id: str, value, data):
    """
    数据变化回调函数
    
    Args:
        node_id: 节点ID
        value: 新值
        data: 数据变化信息
    """
    logger.info(f"数据变化通知: {node_id} = {value}")


def example_basic_connection():
    """示例1: 基本连接和断开"""
    logger.info("=== 示例1: 基本连接 ===")
    
    client = OPCUAClient(
        server_url=config.OPC_UA_SERVER_URL,
        timeout=config.OPC_UA_TIMEOUT,
        max_retries=config.OPC_UA_RETRY_MAX,
        retry_delay=config.OPC_UA_RETRY_DELAY
    )
    
    # 连接到服务器
    if client.connect():
        logger.info("连接成功！")
        
        # 检查连接状态
        if client.check_connection():
            logger.info("连接状态正常")
        
        # 断开连接
        client.disconnect()
        logger.info("已断开连接")
    else:
        logger.error("连接失败")


def example_context_manager():
    """示例2: 使用上下文管理器"""
    logger.info("=== 示例2: 使用上下文管理器 ===")
    
    with OPCUAClient(config.OPC_UA_SERVER_URL) as client:
        if client.is_connected:
            logger.info("通过上下文管理器连接成功")
        # 自动断开连接


def example_read_single_node():
    """示例3: 读取单个节点"""
    logger.info("=== 示例3: 读取单个节点 ===")
    
    client = OPCUAClient(config.OPC_UA_SERVER_URL)
    
    if client.connect():
        # 读取传送带速度
        node_id = config.OPC_UA_NODES['conveyor']['speed']
        value = client.read_node(node_id)
        
        if value is not None:
            logger.info(f"传送带速度: {value} m/s")
        else:
            logger.error("读取节点失败")
        
        client.disconnect()


def example_read_multiple_nodes():
    """示例4: 批量读取多个节点"""
    logger.info("=== 示例4: 批量读取多个节点 ===")
    
    client = OPCUAClient(config.OPC_UA_SERVER_URL)
    
    if client.connect():
        # 准备要读取的节点列表
        node_ids = [
            config.OPC_UA_NODES['conveyor']['power'],
            config.OPC_UA_NODES['station1']['power'],
            config.OPC_UA_NODES['station2']['power'],
            config.OPC_UA_NODES['energy']['total_energy']
        ]
        
        # 批量读取
        results = client.read_nodes(node_ids)
        
        logger.info("读取结果:")
        for node_id, value in results.items():
            logger.info(f"  {node_id}: {value}")
        
        client.disconnect()


def example_subscribe_nodes():
    """示例5: 订阅节点数据变化"""
    logger.info("=== 示例5: 订阅节点数据变化 ===")
    
    client = OPCUAClient(config.OPC_UA_SERVER_URL)
    
    if client.connect():
        # 准备要订阅的节点列表
        node_ids = [
            config.OPC_UA_NODES['conveyor']['power'],
            config.OPC_UA_NODES['station1']['power'],
            config.OPC_UA_NODES['energy']['total_energy']
        ]
        
        # 订阅节点
        if client.subscribe_nodes(node_ids, data_change_callback, publishing_interval=1000):
            logger.info("订阅成功，监听数据变化...")
            
            # 运行30秒，接收数据变化通知
            try:
                time.sleep(30)
            except KeyboardInterrupt:
                logger.info("用户中断")
        
        client.disconnect()


def example_get_node_info():
    """示例6: 获取节点详细信息"""
    logger.info("=== 示例6: 获取节点详细信息 ===")
    
    client = OPCUAClient(config.OPC_UA_SERVER_URL)
    
    if client.connect():
        node_id = config.OPC_UA_NODES['conveyor']['power']
        info = client.get_node_info(node_id)
        
        if info:
            logger.info("节点信息:")
            for key, value in info.items():
                logger.info(f"  {key}: {value}")
        
        client.disconnect()


def example_all_devices_monitoring():
    """示例7: 监控所有设备数据"""
    logger.info("=== 示例7: 监控所有设备数据 ===")
    
    client = OPCUAClient(config.OPC_UA_SERVER_URL)
    
    if client.connect():
        # 收集所有节点ID
        all_node_ids = []
        for device, nodes in config.OPC_UA_NODES.items():
            for param, node_id in nodes.items():
                all_node_ids.append(node_id)
        
        logger.info(f"准备读取 {len(all_node_ids)} 个节点")
        
        # 批量读取所有节点
        results = client.read_nodes(all_node_ids)
        
        # 按设备组织输出
        logger.info("\n当前设备状态:")
        for device, nodes in config.OPC_UA_NODES.items():
            logger.info(f"\n{device.upper()}:")
            for param, node_id in nodes.items():
                value = results.get(node_id, "N/A")
                logger.info(f"  {param}: {value}")
        
        client.disconnect()


if __name__ == "__main__":
    # 运行示例
    # 注意: 需要KepServer正在运行并配置好OPC UA服务器
    
    try:
        # 选择要运行的示例
        logger.info("OPC UA客户端使用示例\n")
        
        # 示例1: 基本连接
        example_basic_connection()
        print("\n" + "="*60 + "\n")
        
        # 示例2: 上下文管理器
        # example_context_manager()
        # print("\n" + "="*60 + "\n")
        
        # 示例3: 读取单个节点
        # example_read_single_node()
        # print("\n" + "="*60 + "\n")
        
        # 示例4: 批量读取
        # example_read_multiple_nodes()
        # print("\n" + "="*60 + "\n")
        
        # 示例5: 订阅数据变化
        # example_subscribe_nodes()
        # print("\n" + "="*60 + "\n")
        
        # 示例6: 获取节点信息
        # example_get_node_info()
        # print("\n" + "="*60 + "\n")
        
        # 示例7: 监控所有设备
        # example_all_devices_monitoring()
        
    except Exception as e:
        logger.error(f"运行示例时出错: {e}", exc_info=True)
