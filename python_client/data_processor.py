"""
数据处理模块
实现数据清洗、异常检测和OEE计算功能
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from decimal import Decimal, InvalidOperation
from collections import deque

logger = logging.getLogger(__name__)


class DataProcessor:
    """数据处理类"""
    
    def __init__(self, config=None):
        """
        初始化数据处理器
        
        Args:
            config: 配置对象，包含数据验证范围等参数
        """
        self.config = config
        
        # 数据验证范围（从配置读取或使用默认值）
        if config and hasattr(config, 'DATA_VALIDATION'):
            self.power_min = config.DATA_VALIDATION.get('power_min', 0.0)
            self.power_max = config.DATA_VALIDATION.get('power_max', 100.0)
            self.energy_min = config.DATA_VALIDATION.get('energy_min', 0.0)
            self.energy_max = config.DATA_VALIDATION.get('energy_max', 10000.0)
            self.speed_min = config.DATA_VALIDATION.get('speed_min', 0.0)
            self.speed_max = config.DATA_VALIDATION.get('speed_max', 5.0)
        else:
            self.power_min = 0.0
            self.power_max = 100.0
            self.energy_min = 0.0
            self.energy_max = 10000.0
            self.speed_min = 0.0
            self.speed_max = 5.0
        
        # 异常检测历史记录（用于连续异常判定）
        # 格式: {device_id: {parameter: deque([value1, value2, ...])}}
        self.anomaly_history = {}
        
        # 连续异常次数阈值
        self.consecutive_anomaly_threshold = 3
        if config and hasattr(config, 'ALARM_CONSECUTIVE_COUNT'):
            self.consecutive_anomaly_threshold = config.ALARM_CONSECUTIVE_COUNT
    
    def clean_data(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        数据清洗方法
        
        功能：
        - 过滤无效和空值
        - 数据类型验证和转换
        - 数值范围检查
        - 时间戳标准化处理
        
        Args:
            raw_data: 原始数据字典
        
        Returns:
            清洗后的数据字典，如果数据无效则返回None
        """
        if not raw_data or not isinstance(raw_data, dict):
            logger.warning("数据清洗失败: 输入数据为空或格式不正确")
            return None
        
        cleaned_data = {}
        
        try:
            # 1. 处理时间戳
            timestamp = raw_data.get('timestamp')
            if timestamp:
                cleaned_data['timestamp'] = self._normalize_timestamp(timestamp)
            else:
                # 如果没有时间戳，使用当前时间
                cleaned_data['timestamp'] = datetime.utcnow()
            
            # 2. 处理设备ID（必需字段）
            device_id = raw_data.get('device_id')
            if not device_id or not isinstance(device_id, str):
                logger.warning("数据清洗失败: 缺少有效的device_id")
                return None
            cleaned_data['device_id'] = device_id.strip()
            
            # 3. 处理设备名称（可选字段）
            device_name = raw_data.get('device_name')
            if device_name:
                cleaned_data['device_name'] = str(device_name).strip()
            
            # 4. 处理功率数据
            power_kw = raw_data.get('power_kw') or raw_data.get('power')
            if power_kw is not None:
                cleaned_power = self._validate_and_convert_number(
                    power_kw, 
                    self.power_min, 
                    self.power_max,
                    'power_kw'
                )
                if cleaned_power is not None:
                    cleaned_data['power_kw'] = cleaned_power
            
            # 5. 处理能耗数据
            energy_kwh = raw_data.get('energy_kwh') or raw_data.get('energy')
            if energy_kwh is not None:
                cleaned_energy = self._validate_and_convert_number(
                    energy_kwh,
                    self.energy_min,
                    self.energy_max,
                    'energy_kwh'
                )
                if cleaned_energy is not None:
                    cleaned_data['energy_kwh'] = cleaned_energy
            
            # 6. 处理速度数据（如果存在）
            speed = raw_data.get('speed')
            if speed is not None:
                cleaned_speed = self._validate_and_convert_number(
                    speed,
                    self.speed_min,
                    self.speed_max,
                    'speed'
                )
                if cleaned_speed is not None:
                    cleaned_data['speed'] = cleaned_speed
            
            # 7. 处理状态字段
            status = raw_data.get('status')
            if status:
                cleaned_data['status'] = str(status).strip().lower()
            
            # 8. 处理生产数据（如果存在）
            for field in ['product_count', 'reject_count', 'runtime_seconds', 'downtime_seconds']:
                value = raw_data.get(field)
                if value is not None:
                    cleaned_value = self._validate_and_convert_integer(value, field)
                    if cleaned_value is not None:
                        cleaned_data[field] = cleaned_value
            
            # 检查清洗后的数据是否有有效内容
            if len(cleaned_data) <= 2:  # 只有timestamp和device_id
                logger.warning(f"数据清洗后无有效数据: {raw_data}")
                return None
            
            logger.debug(f"数据清洗成功: {device_id}")
            return cleaned_data
            
        except Exception as e:
            logger.error(f"数据清洗过程出错: {e}")
            return None
    
    def _normalize_timestamp(self, timestamp: Any) -> datetime:
        """
        标准化时间戳
        
        Args:
            timestamp: 时间戳（可以是datetime对象、字符串或数字）
        
        Returns:
            标准化的datetime对象
        """
        if isinstance(timestamp, datetime):
            return timestamp
        
        if isinstance(timestamp, str):
            # 尝试解析ISO格式时间字符串
            try:
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except ValueError:
                pass
            
            # 尝试其他常见格式
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M:%S.%f',
                '%Y/%m/%d %H:%M:%S',
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(timestamp, fmt)
                except ValueError:
                    continue
        
        if isinstance(timestamp, (int, float)):
            # 假设是Unix时间戳
            try:
                return datetime.fromtimestamp(timestamp)
            except (ValueError, OSError):
                pass
        
        # 如果无法解析，返回当前时间
        logger.warning(f"无法解析时间戳: {timestamp}，使用当前时间")
        return datetime.utcnow()
    
    def _validate_and_convert_number(
        self, 
        value: Any, 
        min_value: float, 
        max_value: float,
        field_name: str
    ) -> Optional[Decimal]:
        """
        验证并转换数值
        
        Args:
            value: 要验证的值
            min_value: 最小值
            max_value: 最大值
            field_name: 字段名称（用于日志）
        
        Returns:
            转换后的Decimal值，如果无效则返回None
        """
        try:
            # 转换为float进行范围检查
            num_value = float(value)
            
            # 检查是否为有效数字
            if not isinstance(num_value, (int, float)) or num_value != num_value:  # NaN检查
                logger.warning(f"字段 {field_name} 包含无效数值: {value}")
                return None
            
            # 范围检查
            if num_value < min_value or num_value > max_value:
                logger.warning(
                    f"字段 {field_name} 超出有效范围 [{min_value}, {max_value}]: {num_value}"
                )
                return None
            
            # 转换为Decimal（保持精度）
            return Decimal(str(num_value))
            
        except (ValueError, TypeError, InvalidOperation) as e:
            logger.warning(f"字段 {field_name} 数值转换失败: {value}, 错误: {e}")
            return None
    
    def _validate_and_convert_integer(self, value: Any, field_name: str) -> Optional[int]:
        """
        验证并转换整数
        
        Args:
            value: 要验证的值
            field_name: 字段名称（用于日志）
        
        Returns:
            转换后的整数值，如果无效则返回None
        """
        try:
            int_value = int(value)
            
            # 检查是否为非负整数
            if int_value < 0:
                logger.warning(f"字段 {field_name} 不能为负数: {int_value}")
                return None
            
            return int_value
            
        except (ValueError, TypeError) as e:
            logger.warning(f"字段 {field_name} 整数转换失败: {value}, 错误: {e}")
            return None

    def detect_anomaly(
        self, 
        device_id: str,
        parameter: str,
        value: float, 
        threshold: float,
        comparison: str = 'greater'
    ) -> bool:
        """
        异常检测方法
        
        功能：
        - 使用阈值比较检测异常
        - 连续异常判定（连续3次超阈值才报警）
        
        Args:
            device_id: 设备ID
            parameter: 参数名称（如'power_kw'）
            value: 当前值
            threshold: 阈值
            comparison: 比较方式 ('greater' 或 'less')
        
        Returns:
            是否触发报警（连续异常达到阈值）
        """
        try:
            # 初始化设备的异常历史记录
            if device_id not in self.anomaly_history:
                self.anomaly_history[device_id] = {}
            
            if parameter not in self.anomaly_history[device_id]:
                self.anomaly_history[device_id][parameter] = deque(
                    maxlen=self.consecutive_anomaly_threshold
                )
            
            # 判断当前值是否异常
            is_anomaly = False
            if comparison == 'greater':
                is_anomaly = value > threshold
            elif comparison == 'less':
                is_anomaly = value < threshold
            else:
                logger.warning(f"未知的比较方式: {comparison}")
                return False
            
            # 记录异常状态
            history = self.anomaly_history[device_id][parameter]
            history.append(is_anomaly)
            
            # 检查是否连续异常
            if len(history) >= self.consecutive_anomaly_threshold:
                consecutive_anomalies = all(history)
                
                if consecutive_anomalies:
                    logger.warning(
                        f"检测到连续异常: 设备={device_id}, 参数={parameter}, "
                        f"当前值={value}, 阈值={threshold}, 连续次数={len(history)}"
                    )
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"异常检测过程出错: {e}")
            return False
    
    def reset_anomaly_history(self, device_id: str = None, parameter: str = None):
        """
        重置异常历史记录
        
        Args:
            device_id: 设备ID（如果为None，重置所有设备）
            parameter: 参数名称（如果为None，重置该设备的所有参数）
        """
        try:
            if device_id is None:
                # 重置所有设备
                self.anomaly_history.clear()
                logger.info("已重置所有设备的异常历史记录")
            elif parameter is None:
                # 重置指定设备的所有参数
                if device_id in self.anomaly_history:
                    self.anomaly_history[device_id].clear()
                    logger.info(f"已重置设备 {device_id} 的异常历史记录")
            else:
                # 重置指定设备的指定参数
                if device_id in self.anomaly_history and parameter in self.anomaly_history[device_id]:
                    self.anomaly_history[device_id][parameter].clear()
                    logger.info(f"已重置设备 {device_id} 参数 {parameter} 的异常历史记录")
        except Exception as e:
            logger.error(f"重置异常历史记录时出错: {e}")
    
    def calculate_oee(
        self,
        runtime_seconds: int,
        downtime_seconds: int,
        product_count: int,
        reject_count: int,
        ideal_cycle_time: float = 10.0,
        planned_production_time: Optional[int] = None
    ) -> Dict[str, float]:
        """
        计算设备综合效率（OEE）
        
        OEE = 可用率 × 性能率 × 质量率
        
        Args:
            runtime_seconds: 运行时间（秒）
            downtime_seconds: 停机时间（秒）
            product_count: 总产量
            reject_count: 不良品数量
            ideal_cycle_time: 理想节拍时间（秒/件），默认10秒
            planned_production_time: 计划生产时间（秒），如果为None则使用runtime+downtime
        
        Returns:
            包含OEE及其组成部分的字典:
            {
                'availability': 可用率 (0-100),
                'performance': 性能率 (0-100),
                'quality': 质量率 (0-100),
                'oee': 总OEE (0-100)
            }
        """
        try:
            # 输入验证
            if runtime_seconds < 0 or downtime_seconds < 0:
                logger.error("运行时间和停机时间不能为负数")
                return self._get_zero_oee()
            
            if product_count < 0 or reject_count < 0:
                logger.error("产量和不良品数量不能为负数")
                return self._get_zero_oee()
            
            if reject_count > product_count:
                logger.error("不良品数量不能大于总产量")
                return self._get_zero_oee()
            
            if ideal_cycle_time <= 0:
                logger.error("理想节拍时间必须大于0")
                return self._get_zero_oee()
            
            # 1. 计算可用率 (Availability)
            # 可用率 = 运行时间 / 计划生产时间
            if planned_production_time is None:
                planned_production_time = runtime_seconds + downtime_seconds
            
            if planned_production_time == 0:
                logger.warning("计划生产时间为0，无法计算OEE")
                return self._get_zero_oee()
            
            availability = (runtime_seconds / planned_production_time) * 100
            
            # 2. 计算性能率 (Performance)
            # 性能率 = (实际产量 × 理想节拍时间) / 运行时间
            if runtime_seconds == 0:
                performance = 0.0
            else:
                ideal_production_time = product_count * ideal_cycle_time
                performance = (ideal_production_time / runtime_seconds) * 100
                
                # 性能率不应超过100%（如果超过，说明实际效率高于理想值）
                if performance > 100:
                    logger.debug(f"性能率超过100%: {performance:.2f}%，限制为100%")
                    performance = 100.0
            
            # 3. 计算质量率 (Quality)
            # 质量率 = 合格品数量 / 总产量
            if product_count == 0:
                quality = 100.0  # 没有生产时，质量率视为100%
            else:
                good_count = product_count - reject_count
                quality = (good_count / product_count) * 100
            
            # 4. 计算总OEE
            # OEE = 可用率 × 性能率 × 质量率
            oee = (availability * performance * quality) / 10000  # 除以10000因为三个百分比相乘
            
            result = {
                'availability': round(availability, 2),
                'performance': round(performance, 2),
                'quality': round(quality, 2),
                'oee': round(oee, 2)
            }
            
            logger.debug(
                f"OEE计算结果: 可用率={result['availability']}%, "
                f"性能率={result['performance']}%, "
                f"质量率={result['quality']}%, "
                f"OEE={result['oee']}%"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"OEE计算过程出错: {e}")
            return self._get_zero_oee()
    
    def _get_zero_oee(self) -> Dict[str, float]:
        """返回零值OEE结果"""
        return {
            'availability': 0.0,
            'performance': 0.0,
            'quality': 0.0,
            'oee': 0.0
        }
    
    def batch_clean_data(self, raw_data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量清洗数据
        
        Args:
            raw_data_list: 原始数据列表
        
        Returns:
            清洗后的数据列表（过滤掉无效数据）
        """
        cleaned_list = []
        
        for raw_data in raw_data_list:
            cleaned = self.clean_data(raw_data)
            if cleaned:
                cleaned_list.append(cleaned)
        
        logger.info(f"批量清洗完成: 输入{len(raw_data_list)}条，输出{len(cleaned_list)}条有效数据")
        return cleaned_list
    
    def get_anomaly_statistics(self) -> Dict[str, Any]:
        """
        获取异常检测统计信息
        
        Returns:
            统计信息字典
        """
        stats = {
            'total_devices': len(self.anomaly_history),
            'devices': {}
        }
        
        for device_id, parameters in self.anomaly_history.items():
            device_stats = {
                'total_parameters': len(parameters),
                'parameters': {}
            }
            
            for parameter, history in parameters.items():
                anomaly_count = sum(1 for x in history if x)
                device_stats['parameters'][parameter] = {
                    'history_length': len(history),
                    'anomaly_count': anomaly_count,
                    'current_consecutive': anomaly_count if all(history) else 0
                }
            
            stats['devices'][device_id] = device_stats
        
        return stats
