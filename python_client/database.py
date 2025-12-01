"""
数据库连接管理类
实现连接池、自动重连和会话管理
"""

import logging
import time
from contextlib import contextmanager
from sqlalchemy import create_engine, event, exc
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理类"""
    
    def __init__(self, database_uri, pool_size=10, max_overflow=20, pool_timeout=30, pool_recycle=3600):
        """
        初始化数据库管理器
        
        Args:
            database_uri: 数据库连接URI
            pool_size: 连接池大小
            max_overflow: 连接池最大溢出数
            pool_timeout: 连接超时时间（秒）
            pool_recycle: 连接回收时间（秒）
        """
        self.database_uri = database_uri
        self.engine = None
        self.session_factory = None
        self.Session = None
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self._is_connected = False
    
    def connect(self, max_retries=3, retry_delay=5):
        """
        连接到数据库
        
        Args:
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
        
        Returns:
            bool: 连接是否成功
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"正在连接数据库... (尝试 {attempt + 1}/{max_retries})")
                
                # 创建引擎，配置连接池
                self.engine = create_engine(
                    self.database_uri,
                    poolclass=QueuePool,
                    pool_size=self.pool_size,
                    max_overflow=self.max_overflow,
                    pool_timeout=self.pool_timeout,
                    pool_recycle=self.pool_recycle,
                    pool_pre_ping=True,  # 启用连接健康检查
                    echo=False
                )
                
                # 添加连接事件监听器
                self._setup_event_listeners()
                
                # 测试连接
                with self.engine.connect() as conn:
                    conn.execute("SELECT 1")
                
                # 创建会话工厂
                self.session_factory = sessionmaker(bind=self.engine)
                self.Session = scoped_session(self.session_factory)
                
                self._is_connected = True
                logger.info("数据库连接成功")
                return True
                
            except Exception as e:
                logger.error(f"数据库连接失败: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"等待 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                else:
                    logger.error("数据库连接失败，已达到最大重试次数")
                    return False
        
        return False
    
    def _setup_event_listeners(self):
        """设置数据库事件监听器"""
        
        @event.listens_for(self.engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """连接建立时的回调"""
            logger.debug("数据库连接已建立")
        
        @event.listens_for(self.engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            """从连接池获取连接时的回调"""
            logger.debug("从连接池获取连接")
        
        @event.listens_for(self.engine, "checkin")
        def receive_checkin(dbapi_conn, connection_record):
            """连接返回连接池时的回调"""
            logger.debug("连接返回连接池")
    
    def disconnect(self):
        """断开数据库连接"""
        try:
            if self.Session:
                self.Session.remove()
            if self.engine:
                self.engine.dispose()
            self._is_connected = False
            logger.info("数据库连接已断开")
        except Exception as e:
            logger.error(f"断开数据库连接时出错: {e}")
    
    def is_connected(self):
        """检查数据库连接状态"""
        if not self._is_connected or not self.engine:
            return False
        
        try:
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception:
            self._is_connected = False
            return False
    
    def reconnect(self, max_retries=3, retry_delay=5):
        """
        重新连接数据库
        
        Args:
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
        
        Returns:
            bool: 重连是否成功
        """
        logger.info("尝试重新连接数据库...")
        self.disconnect()
        return self.connect(max_retries, retry_delay)
    
    @contextmanager
    def get_session(self):
        """
        获取数据库会话（上下文管理器）
        
        使用示例:
            with db_manager.get_session() as session:
                session.query(User).all()
        """
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库会话错误: {e}")
            raise
        finally:
            session.close()
    
    def create_tables(self):
        """创建所有数据表"""
        try:
            logger.info("正在创建数据表...")
            Base.metadata.create_all(self.engine)
            logger.info("数据表创建成功")
            return True
        except Exception as e:
            logger.error(f"创建数据表失败: {e}")
            return False
    
    def drop_tables(self):
        """删除所有数据表（谨慎使用）"""
        try:
            logger.warning("正在删除所有数据表...")
            Base.metadata.drop_all(self.engine)
            logger.info("数据表删除成功")
            return True
        except Exception as e:
            logger.error(f"删除数据表失败: {e}")
            return False
    
    def execute_with_retry(self, func, max_retries=3, retry_delay=1):
        """
        执行数据库操作，失败时自动重试
        
        Args:
            func: 要执行的函数
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
        
        Returns:
            函数执行结果
        """
        for attempt in range(max_retries):
            try:
                return func()
            except exc.OperationalError as e:
                logger.warning(f"数据库操作失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    # 检查连接状态，必要时重连
                    if not self.is_connected():
                        logger.info("检测到连接断开，尝试重新连接...")
                        self.reconnect()
                    time.sleep(retry_delay)
                else:
                    logger.error("数据库操作失败，已达到最大重试次数")
                    raise
            except Exception as e:
                logger.error(f"数据库操作出错: {e}")
                raise
    
    def get_pool_status(self):
        """获取连接池状态信息"""
        if not self.engine:
            return None
        
        pool = self.engine.pool
        return {
            'pool_size': pool.size(),
            'checked_in': pool.checkedin(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow(),
            'total_connections': pool.size() + pool.overflow()
        }
    
    def save_energy_data(self, data_list):
        """
        保存能源数据到energy_data表
        支持批量插入优化和数据去重
        
        Args:
            data_list: 能源数据列表，每个元素为字典，包含以下字段：
                - timestamp: 时间戳
                - device_id: 设备ID
                - device_name: 设备名称
                - power_kw: 功率(kW)
                - energy_kwh: 能耗(kWh)
                - status: 状态
        
        Returns:
            int: 成功插入的记录数
        """
        from models import EnergyData
        from datetime import datetime, timedelta
        
        if not data_list:
            return 0
        
        def _save():
            with self.get_session() as session:
                inserted_count = 0
                
                # 批量插入优化
                if len(data_list) > 1:
                    # 数据去重：检查最近10秒内是否有相同设备的记录
                    for data in data_list:
                        timestamp = data.get('timestamp', datetime.utcnow())
                        device_id = data['device_id']
                        
                        # 查询最近10秒内的记录
                        time_threshold = timestamp - timedelta(seconds=10)
                        existing = session.query(EnergyData).filter(
                            EnergyData.device_id == device_id,
                            EnergyData.timestamp >= time_threshold,
                            EnergyData.timestamp <= timestamp
                        ).first()
                        
                        # 如果不存在重复记录，则插入
                        if not existing:
                            energy_record = EnergyData(
                                timestamp=timestamp,
                                device_id=device_id,
                                device_name=data.get('device_name'),
                                power_kw=data.get('power_kw'),
                                energy_kwh=data.get('energy_kwh'),
                                status=data.get('status')
                            )
                            session.add(energy_record)
                            inserted_count += 1
                    
                    session.flush()
                else:
                    # 单条记录插入
                    data = data_list[0]
                    timestamp = data.get('timestamp', datetime.utcnow())
                    device_id = data['device_id']
                    
                    # 数据去重检查
                    time_threshold = timestamp - timedelta(seconds=10)
                    existing = session.query(EnergyData).filter(
                        EnergyData.device_id == device_id,
                        EnergyData.timestamp >= time_threshold,
                        EnergyData.timestamp <= timestamp
                    ).first()
                    
                    if not existing:
                        energy_record = EnergyData(
                            timestamp=timestamp,
                            device_id=device_id,
                            device_name=data.get('device_name'),
                            power_kw=data.get('power_kw'),
                            energy_kwh=data.get('energy_kwh'),
                            status=data.get('status')
                        )
                        session.add(energy_record)
                        inserted_count = 1
                
                logger.info(f"成功保存 {inserted_count} 条能源数据记录")
                return inserted_count
        
        return self.execute_with_retry(_save)
    
    def save_production_data(self, data):
        """
        保存生产统计数据到production_data表
        包含OEE数据存储
        
        Args:
            data: 生产数据字典，包含以下字段：
                - timestamp: 时间戳
                - product_count: 产品计数
                - reject_count: 不良品计数
                - runtime_seconds: 运行时间（秒）
                - downtime_seconds: 停机时间（秒）
                - oee_percentage: OEE百分比
                - availability: 可用率
                - performance: 性能率
                - quality: 质量率
        
        Returns:
            bool: 是否保存成功
        """
        from models import ProductionData
        from datetime import datetime
        
        if not data:
            return False
        
        def _save():
            with self.get_session() as session:
                production_record = ProductionData(
                    timestamp=data.get('timestamp', datetime.utcnow()),
                    product_count=data.get('product_count'),
                    reject_count=data.get('reject_count'),
                    runtime_seconds=data.get('runtime_seconds'),
                    downtime_seconds=data.get('downtime_seconds'),
                    oee_percentage=data.get('oee_percentage'),
                    availability=data.get('availability'),
                    performance=data.get('performance'),
                    quality=data.get('quality')
                )
                session.add(production_record)
                logger.info(f"成功保存生产数据记录，OEE: {data.get('oee_percentage')}%")
                return True
        
        return self.execute_with_retry(_save)
    
    def save_alarm(self, alarm_data):
        """
        保存报警记录到alarms表
        实现报警去重：相同设备相同类型的报警在5分钟内只记录一次
        
        Args:
            alarm_data: 报警数据字典，包含以下字段：
                - timestamp: 时间戳
                - device_id: 设备ID
                - alarm_type: 报警类型
                - alarm_level: 报警级别 (warning, critical, emergency)
                - message: 报警消息
                - threshold_value: 阈值
                - actual_value: 实际值
        
        Returns:
            bool: 是否保存成功（如果是重复报警则返回False）
        """
        from models import Alarm
        from datetime import datetime, timedelta
        
        if not alarm_data:
            return False
        
        def _save():
            with self.get_session() as session:
                timestamp = alarm_data.get('timestamp', datetime.utcnow())
                device_id = alarm_data['device_id']
                alarm_type = alarm_data.get('alarm_type')
                
                # 报警去重：检查5分钟内是否有相同设备相同类型的报警
                time_threshold = timestamp - timedelta(minutes=5)
                existing_alarm = session.query(Alarm).filter(
                    Alarm.device_id == device_id,
                    Alarm.alarm_type == alarm_type,
                    Alarm.timestamp >= time_threshold,
                    Alarm.acknowledged == False  # 只检查未确认的报警
                ).first()
                
                if existing_alarm:
                    logger.debug(f"报警去重：设备 {device_id} 的 {alarm_type} 报警在5分钟内已存在")
                    return False
                
                # 创建新的报警记录
                alarm_record = Alarm(
                    timestamp=timestamp,
                    device_id=device_id,
                    alarm_type=alarm_type,
                    alarm_level=alarm_data.get('alarm_level', 'warning'),
                    message=alarm_data.get('message'),
                    threshold_value=alarm_data.get('threshold_value'),
                    actual_value=alarm_data.get('actual_value'),
                    acknowledged=False
                )
                session.add(alarm_record)
                logger.warning(f"保存报警记录：设备 {device_id}，级别 {alarm_data.get('alarm_level')}，消息：{alarm_data.get('message')}")
                return True
        
        return self.execute_with_retry(_save)
    
    def query_history(self, table_name, start_time=None, end_time=None, 
                     device_id=None, page=1, page_size=100, 
                     aggregate=None, aggregate_interval=None):
        """
        查询历史数据
        支持时间范围过滤、设备过滤、分页查询和数据聚合
        
        Args:
            table_name: 表名 ('energy_data', 'production_data', 'alarms')
            start_time: 开始时间
            end_time: 结束时间
            device_id: 设备ID（仅适用于energy_data和alarms表）
            page: 页码（从1开始）
            page_size: 每页记录数
            aggregate: 聚合类型 ('avg', 'sum', 'max', 'min', 'count')
            aggregate_interval: 聚合时间间隔 ('hour', 'day', 'week')
        
        Returns:
            dict: 包含数据列表和分页信息的字典
                {
                    'data': [...],
                    'total': 总记录数,
                    'page': 当前页码,
                    'page_size': 每页记录数,
                    'total_pages': 总页数
                }
        """
        from models import EnergyData, ProductionData, Alarm
        from sqlalchemy import func, and_
        from datetime import datetime
        
        # 选择对应的模型
        model_map = {
            'energy_data': EnergyData,
            'production_data': ProductionData,
            'alarms': Alarm
        }
        
        if table_name not in model_map:
            logger.error(f"不支持的表名: {table_name}")
            return None
        
        model = model_map[table_name]
        
        def _query():
            with self.get_session() as session:
                # 构建基础查询
                query = session.query(model)
                
                # 时间范围过滤
                if start_time:
                    query = query.filter(model.timestamp >= start_time)
                if end_time:
                    query = query.filter(model.timestamp <= end_time)
                
                # 设备过滤（仅适用于energy_data和alarms）
                if device_id and hasattr(model, 'device_id'):
                    query = query.filter(model.device_id == device_id)
                
                # 数据聚合查询
                if aggregate and aggregate_interval:
                    return self._aggregate_query(session, model, query, aggregate, 
                                                aggregate_interval, start_time, end_time)
                
                # 获取总记录数
                total = query.count()
                
                # 分页
                offset = (page - 1) * page_size
                query = query.order_by(model.timestamp.desc())
                query = query.limit(page_size).offset(offset)
                
                # 执行查询
                results = query.all()
                
                # 转换为字典列表
                data = [record.to_dict() for record in results]
                
                # 计算总页数
                total_pages = (total + page_size - 1) // page_size
                
                logger.info(f"查询 {table_name} 历史数据：共 {total} 条记录，返回第 {page} 页")
                
                return {
                    'data': data,
                    'total': total,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': total_pages
                }
        
        return self.execute_with_retry(_query)
    
    def _aggregate_query(self, session, model, base_query, aggregate, 
                        aggregate_interval, start_time, end_time):
        """
        执行聚合查询
        
        Args:
            session: 数据库会话
            model: 数据模型
            base_query: 基础查询
            aggregate: 聚合类型
            aggregate_interval: 聚合时间间隔
            start_time: 开始时间
            end_time: 结束时间
        
        Returns:
            dict: 聚合结果
        """
        from sqlalchemy import func, case
        
        # 根据聚合间隔选择时间分组函数
        if aggregate_interval == 'hour':
            time_group = func.date_format(model.timestamp, '%Y-%m-%d %H:00:00')
        elif aggregate_interval == 'day':
            time_group = func.date_format(model.timestamp, '%Y-%m-%d')
        elif aggregate_interval == 'week':
            time_group = func.date_format(model.timestamp, '%Y-%u')
        else:
            logger.error(f"不支持的聚合间隔: {aggregate_interval}")
            return None
        
        # 构建聚合查询
        if model.__tablename__ == 'energy_data':
            # 能源数据聚合
            if aggregate == 'avg':
                agg_func = func.avg(model.power_kw)
            elif aggregate == 'sum':
                agg_func = func.sum(model.energy_kwh)
            elif aggregate == 'max':
                agg_func = func.max(model.power_kw)
            elif aggregate == 'min':
                agg_func = func.min(model.power_kw)
            elif aggregate == 'count':
                agg_func = func.count(model.id)
            else:
                logger.error(f"不支持的聚合类型: {aggregate}")
                return None
            
            query = session.query(
                time_group.label('time_period'),
                model.device_id,
                agg_func.label('value')
            ).filter(
                base_query.whereclause
            ).group_by(
                time_group, model.device_id
            ).order_by(
                time_group.desc()
            )
        
        elif model.__tablename__ == 'production_data':
            # 生产数据聚合
            if aggregate == 'avg':
                agg_func = func.avg(model.oee_percentage)
            elif aggregate == 'sum':
                agg_func = func.sum(model.product_count)
            elif aggregate == 'max':
                agg_func = func.max(model.oee_percentage)
            elif aggregate == 'min':
                agg_func = func.min(model.oee_percentage)
            elif aggregate == 'count':
                agg_func = func.count(model.id)
            else:
                logger.error(f"不支持的聚合类型: {aggregate}")
                return None
            
            query = session.query(
                time_group.label('time_period'),
                agg_func.label('value')
            ).filter(
                base_query.whereclause
            ).group_by(
                time_group
            ).order_by(
                time_group.desc()
            )
        
        elif model.__tablename__ == 'alarms':
            # 报警数据聚合（通常只统计数量）
            query = session.query(
                time_group.label('time_period'),
                model.device_id,
                model.alarm_level,
                func.count(model.id).label('count')
            ).filter(
                base_query.whereclause
            ).group_by(
                time_group, model.device_id, model.alarm_level
            ).order_by(
                time_group.desc()
            )
        
        # 执行查询
        results = query.all()
        
        # 转换为字典列表
        data = []
        for row in results:
            if model.__tablename__ == 'alarms':
                data.append({
                    'time_period': row.time_period,
                    'device_id': row.device_id,
                    'alarm_level': row.alarm_level,
                    'count': row.count
                })
            elif model.__tablename__ == 'production_data':
                data.append({
                    'time_period': row.time_period,
                    'value': float(row.value) if row.value else None
                })
            else:
                data.append({
                    'time_period': row.time_period,
                    'device_id': row.device_id,
                    'value': float(row.value) if row.value else None
                })
        
        logger.info(f"聚合查询完成：{aggregate_interval} 间隔，{aggregate} 聚合，共 {len(data)} 条记录")
        
        return {
            'data': data,
            'aggregate': aggregate,
            'aggregate_interval': aggregate_interval,
            'total': len(data)
        }
