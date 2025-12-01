"""
OPC UA客户端核心模块
实现与KepServer的连接、数据订阅和读取功能
"""

import time
import logging
from typing import List, Dict, Callable, Optional, Any
from opcua import Client, ua
from opcua.common.subscription import SubHandler


# 配置日志
logger = logging.getLogger(__name__)


class DataChangeHandler(SubHandler):
    """数据变化处理器"""
    
    def __init__(self, callback: Callable):
        """
        初始化数据变化处理器
        
        Args:
            callback: 数据变化时的回调函数
        """
        self.callback = callback
    
    def datachange_notification(self, node, val, data):
        """
        数据变化通知处理
        
        Args:
            node: 节点对象
            val: 新值
            data: 数据变化信息
        """
        try:
            node_id = node.nodeid.to_string()
            logger.debug(f"数据变化: {node_id} = {val}")
            
            # 调用回调函数
            if self.callback:
                self.callback(node_id, val, data)
        except Exception as e:
            logger.error(f"处理数据变化通知时出错: {e}")


class OPCUAClient:
    """OPC UA客户端管理类"""
    
    def __init__(self, server_url: str, timeout: int = 3, 
                 max_retries: int = 5, retry_delay: int = 5):
        """
        初始化OPC UA客户端
        
        Args:
            server_url: OPC UA服务器地址
            timeout: 连接超时时间（秒）
            max_retries: 最大重试次数
            retry_delay: 重试延迟基础时间（秒）
        """
        self.server_url = server_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        self.client: Optional[Client] = None
        self.subscription = None
        self.is_connected = False
        self.subscribed_nodes: Dict[str, Any] = {}
        
        logger.info(f"初始化OPC UA客户端: {server_url}")
    
    def connect(self) -> bool:
        """
        连接到OPC UA服务器
        使用指数退避策略进行重试
        
        Returns:
            bool: 连接是否成功
        """
        retry_count = 0
        
        while retry_count < self.max_retries:
            try:
                logger.info(f"尝试连接到OPC UA服务器: {self.server_url} (尝试 {retry_count + 1}/{self.max_retries})")
                
                # 创建客户端实例
                self.client = Client(self.server_url, timeout=self.timeout)
                
                # 设置安全策略（开发环境使用None）
                self.client.set_security_string("None")
                
                # 连接到服务器
                self.client.connect()
                
                # 验证连接
                root = self.client.get_root_node()
                logger.info(f"成功连接到OPC UA服务器，根节点: {root}")
                
                self.is_connected = True
                return True
                
            except Exception as e:
                retry_count += 1
                logger.error(f"连接失败 (尝试 {retry_count}/{self.max_retries}): {e}")
                
                if retry_count < self.max_retries:
                    # 指数退避策略
                    wait_time = self.retry_delay * (2 ** (retry_count - 1))
                    logger.info(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"达到最大重试次数 ({self.max_retries})，连接失败")
                    self.is_connected = False
                    return False
        
        return False
    
    def disconnect(self):
        """
        断开与OPC UA服务器的连接
        清理所有资源
        """
        try:
            if self.subscription:
                logger.info("删除订阅...")
                self.subscription.delete()
                self.subscription = None
            
            if self.client and self.is_connected:
                logger.info("断开OPC UA连接...")
                self.client.disconnect()
                self.is_connected = False
                logger.info("已成功断开连接")
            
            # 清理订阅节点记录
            self.subscribed_nodes.clear()
            
        except Exception as e:
            logger.error(f"断开连接时出错: {e}")
    
    def check_connection(self) -> bool:
        """
        检查连接状态
        
        Returns:
            bool: 连接是否正常
        """
        if not self.is_connected or not self.client:
            return False
        
        try:
            # 尝试读取根节点来验证连接
            self.client.get_root_node()
            return True
        except Exception as e:
            logger.warning(f"连接检查失败: {e}")
            self.is_connected = False
            return False
    
    def reconnect(self) -> bool:
        """
        重新连接到服务器
        
        Returns:
            bool: 重连是否成功
        """
        logger.info("尝试重新连接...")
        self.disconnect()
        return self.connect()
    
    def subscribe_nodes(self, node_ids: List[str], callback: Callable,
                       publishing_interval: int = 1000) -> bool:
        """
        订阅OPC UA节点
        
        Args:
            node_ids: 要订阅的节点ID列表
            callback: 数据变化时的回调函数，签名为 callback(node_id, value, data)
            publishing_interval: 发布间隔（毫秒）
        
        Returns:
            bool: 订阅是否成功
        """
        if not self.is_connected or not self.client:
            logger.error("未连接到服务器，无法订阅节点")
            return False
        
        try:
            # 创建订阅（如果不存在）
            if not self.subscription:
                logger.info(f"创建订阅，发布间隔: {publishing_interval}ms")
                handler = DataChangeHandler(callback)
                self.subscription = self.client.create_subscription(
                    publishing_interval, 
                    handler
                )
            
            # 批量订阅节点
            nodes_to_subscribe = []
            for node_id in node_ids:
                if node_id not in self.subscribed_nodes:
                    try:
                        node = self.client.get_node(node_id)
                        nodes_to_subscribe.append(node)
                    except Exception as e:
                        logger.error(f"获取节点失败 {node_id}: {e}")
            
            if nodes_to_subscribe:
                # 批量订阅
                handles = self.subscription.subscribe_data_change(nodes_to_subscribe)
                
                # 记录订阅的节点
                for i, node_id in enumerate([n.nodeid.to_string() for n in nodes_to_subscribe]):
                    self.subscribed_nodes[node_id] = handles[i] if isinstance(handles, list) else handles
                
                logger.info(f"成功订阅 {len(nodes_to_subscribe)} 个节点")
            
            return True
            
        except Exception as e:
            logger.error(f"订阅节点时出错: {e}")
            return False
    
    def unsubscribe_nodes(self, node_ids: List[str]) -> bool:
        """
        取消订阅指定节点
        
        Args:
            node_ids: 要取消订阅的节点ID列表
        
        Returns:
            bool: 操作是否成功
        """
        if not self.subscription:
            logger.warning("没有活动的订阅")
            return False
        
        try:
            for node_id in node_ids:
                if node_id in self.subscribed_nodes:
                    handle = self.subscribed_nodes[node_id]
                    self.subscription.unsubscribe(handle)
                    del self.subscribed_nodes[node_id]
                    logger.info(f"已取消订阅节点: {node_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"取消订阅时出错: {e}")
            return False
    
    def read_node(self, node_id: str, retry: bool = True) -> Optional[Any]:
        """
        读取单个节点的值
        
        Args:
            node_id: 节点ID
            retry: 读取失败时是否重试
        
        Returns:
            节点值，失败返回None
        """
        if not self.is_connected or not self.client:
            logger.error("未连接到服务器，无法读取节点")
            return None
        
        max_attempts = 2 if retry else 1
        attempt = 0
        
        while attempt < max_attempts:
            try:
                node = self.client.get_node(node_id)
                value = node.get_value()
                
                # 数据类型转换
                converted_value = self._convert_value(value)
                
                logger.debug(f"读取节点 {node_id}: {converted_value}")
                return converted_value
                
            except Exception as e:
                attempt += 1
                logger.error(f"读取节点失败 {node_id} (尝试 {attempt}/{max_attempts}): {e}")
                
                if attempt < max_attempts:
                    # 检查连接状态，必要时重连
                    if not self.check_connection():
                        logger.info("连接已断开，尝试重连...")
                        if not self.reconnect():
                            return None
                    time.sleep(0.5)
        
        return None
    
    def read_nodes(self, node_ids: List[str], retry: bool = True) -> Dict[str, Any]:
        """
        批量读取多个节点的值
        
        Args:
            node_ids: 节点ID列表
            retry: 读取失败时是否重试
        
        Returns:
            字典，键为节点ID，值为节点值
        """
        if not self.is_connected or not self.client:
            logger.error("未连接到服务器，无法读取节点")
            return {}
        
        results = {}
        max_attempts = 2 if retry else 1
        attempt = 0
        
        while attempt < max_attempts:
            try:
                # 获取节点对象列表
                nodes = []
                valid_node_ids = []
                
                for node_id in node_ids:
                    try:
                        node = self.client.get_node(node_id)
                        nodes.append(node)
                        valid_node_ids.append(node_id)
                    except Exception as e:
                        logger.error(f"获取节点对象失败 {node_id}: {e}")
                        results[node_id] = None
                
                if not nodes:
                    return results
                
                # 批量读取
                values = self.client.get_values(nodes)
                
                # 处理结果
                for i, node_id in enumerate(valid_node_ids):
                    value = values[i] if isinstance(values, list) else values
                    converted_value = self._convert_value(value)
                    results[node_id] = converted_value
                    logger.debug(f"读取节点 {node_id}: {converted_value}")
                
                return results
                
            except Exception as e:
                attempt += 1
                logger.error(f"批量读取节点失败 (尝试 {attempt}/{max_attempts}): {e}")
                
                if attempt < max_attempts:
                    # 检查连接状态，必要时重连
                    if not self.check_connection():
                        logger.info("连接已断开，尝试重连...")
                        if not self.reconnect():
                            break
                    time.sleep(0.5)
        
        # 如果所有尝试都失败，返回None值
        for node_id in node_ids:
            if node_id not in results:
                results[node_id] = None
        
        return results
    
    def _convert_value(self, value: Any) -> Any:
        """
        转换OPC UA数据类型为Python原生类型
        
        Args:
            value: OPC UA值
        
        Returns:
            转换后的Python值
        """
        try:
            # 处理DataValue对象
            if hasattr(value, 'Value'):
                value = value.Value
            
            # 处理Variant对象
            if isinstance(value, ua.Variant):
                value = value.Value
            
            # 类型转换
            if isinstance(value, (int, float, bool, str)):
                return value
            elif value is None:
                return None
            else:
                # 尝试转换为字符串
                return str(value)
                
        except Exception as e:
            logger.warning(f"数据类型转换失败: {e}, 原始值: {value}")
            return value
    
    def get_node_info(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        获取节点详细信息
        
        Args:
            node_id: 节点ID
        
        Returns:
            节点信息字典
        """
        if not self.is_connected or not self.client:
            logger.error("未连接到服务器")
            return None
        
        try:
            node = self.client.get_node(node_id)
            
            info = {
                'node_id': node_id,
                'browse_name': node.get_browse_name().to_string(),
                'display_name': node.get_display_name().to_string(),
                'node_class': node.get_node_class().name,
                'value': self._convert_value(node.get_value()),
                'data_type': node.get_data_type_as_variant_type().name if hasattr(node, 'get_data_type_as_variant_type') else 'Unknown'
            }
            
            return info
            
        except Exception as e:
            logger.error(f"获取节点信息失败 {node_id}: {e}")
            return None
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.disconnect()
