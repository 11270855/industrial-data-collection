"""
报警处理模块
实现报警逻辑管理、阈值检查和邮件通知功能
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class AlarmHandler:
    """报警处理类，管理报警逻辑、阈值检查和通知"""
    
    def __init__(self, db_manager, config):
        """
        初始化报警处理器
        
        Args:
            db_manager: 数据库管理器实例
            config: 配置对象
        """
        self.db_manager = db_manager
        self.config = config
        self.consecutive_violations = {}  # 记录连续违规次数 {device_id: {param: count}}
        self.last_alarm_time = {}  # 记录最后报警时间 {device_id: {alarm_type: timestamp}}
        logger.info("报警处理器初始化完成")
    
    def check_thresholds(self, device_data: Dict[str, Any], thresholds: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        检查所有设备的阈值
        
        Args:
            device_data: 设备数据字典，格式：
                {
                    'device_id': str,
                    'device_name': str,
                    'power_kw': float,
                    'energy_kwh': float,
                    'status': str,
                    'timestamp': datetime
                }
            thresholds: 阈值配置列表，每个元素包含：
                {
                    'device_id': str,
                    'parameter_name': str,
                    'threshold_value': float,
                    'alarm_level': str,
                    'enabled': bool
                }
        
        Returns:
            List[Dict]: 触发的报警列表
        """
        triggered_alarms = []
        
        if not device_data or not thresholds:
            return triggered_alarms
        
        device_id = device_data.get('device_id')
        if not device_id:
            logger.warning("设备数据缺少device_id字段")
            return triggered_alarms
        
        # 初始化设备的连续违规计数器
        if device_id not in self.consecutive_violations:
            self.consecutive_violations[device_id] = {}
        
        # 检查每个阈值
        for threshold in thresholds:
            # 只检查启用的阈值且设备ID匹配
            if not threshold.get('enabled', True):
                continue
            
            if threshold.get('device_id') != device_id:
                continue
            
            parameter_name = threshold.get('parameter_name')
            threshold_value = threshold.get('threshold_value')
            alarm_level = threshold.get('alarm_level', 'warning')
            
            if not parameter_name or threshold_value is None:
                continue
            
            # 获取实际值
            actual_value = device_data.get(parameter_name)
            if actual_value is None:
                continue
            
            # 转换为float进行比较
            try:
                actual_value_float = float(actual_value)
                threshold_value_float = float(threshold_value)
            except (ValueError, TypeError):
                logger.warning(f"无法转换数值进行比较：{parameter_name}={actual_value}, threshold={threshold_value}")
                continue
            
            # 检查是否超过阈值
            if actual_value_float > threshold_value_float:
                # 增加连续违规计数
                if parameter_name not in self.consecutive_violations[device_id]:
                    self.consecutive_violations[device_id][parameter_name] = 0
                
                self.consecutive_violations[device_id][parameter_name] += 1
                
                # 检查是否达到连续异常次数阈值
                consecutive_count = self.consecutive_violations[device_id][parameter_name]
                required_count = self.config.ALARM_CONSECUTIVE_COUNT
                
                if consecutive_count >= required_count:
                    # 触发报警
                    alarm_data = {
                        'timestamp': device_data.get('timestamp', datetime.utcnow()),
                        'device_id': device_id,
                        'device_name': device_data.get('device_name', device_id),
                        'alarm_type': f'{parameter_name}_threshold',
                        'alarm_level': alarm_level,
                        'parameter_name': parameter_name,
                        'threshold_value': threshold_value_float,
                        'actual_value': actual_value_float,
                        'message': f"设备 {device_data.get('device_name', device_id)} 的 {parameter_name} 超过阈值"
                    }
                    
                    # 检查报警去重
                    if self._should_trigger_alarm(device_id, alarm_data['alarm_type']):
                        triggered_alarms.append(alarm_data)
                        # 重置连续违规计数
                        self.consecutive_violations[device_id][parameter_name] = 0
                        logger.warning(
                            f"触发报警：设备={device_id}, 参数={parameter_name}, "
                            f"实际值={actual_value_float:.2f}, 阈值={threshold_value_float:.2f}, "
                            f"级别={alarm_level}"
                        )
            else:
                # 未超过阈值，重置连续违规计数
                if parameter_name in self.consecutive_violations[device_id]:
                    self.consecutive_violations[device_id][parameter_name] = 0
        
        return triggered_alarms
    
    def _should_trigger_alarm(self, device_id: str, alarm_type: str) -> bool:
        """
        检查是否应该触发报警（报警去重）
        
        Args:
            device_id: 设备ID
            alarm_type: 报警类型
        
        Returns:
            bool: 是否应该触发报警
        """
        # 初始化设备的报警时间记录
        if device_id not in self.last_alarm_time:
            self.last_alarm_time[device_id] = {}
        
        # 检查最后一次报警时间
        if alarm_type in self.last_alarm_time[device_id]:
            last_time = self.last_alarm_time[device_id][alarm_type]
            time_diff = (datetime.utcnow() - last_time).total_seconds()
            
            # 如果在去重时间窗口内，不触发报警
            if time_diff < self.config.ALARM_DUPLICATE_WINDOW:
                logger.debug(
                    f"报警去重：设备 {device_id} 的 {alarm_type} 报警在 "
                    f"{self.config.ALARM_DUPLICATE_WINDOW} 秒内已触发"
                )
                return False
        
        # 更新最后报警时间
        self.last_alarm_time[device_id][alarm_type] = datetime.utcnow()
        return True
    
    def trigger_alarm(self, alarm_data: Dict[str, Any]) -> bool:
        """
        触发报警并记录到数据库
        
        Args:
            alarm_data: 报警数据字典，包含：
                - timestamp: 时间戳
                - device_id: 设备ID
                - device_name: 设备名称（可选）
                - alarm_type: 报警类型
                - alarm_level: 报警级别 (warning, critical, emergency)
                - parameter_name: 参数名称（可选）
                - threshold_value: 阈值
                - actual_value: 实际值
                - message: 报警消息
        
        Returns:
            bool: 是否成功触发报警
        """
        try:
            # 确定报警级别
            alarm_level = self._determine_alarm_level(alarm_data)
            alarm_data['alarm_level'] = alarm_level
            
            # 格式化报警消息
            message = self._format_alarm_message(alarm_data)
            alarm_data['message'] = message
            
            # 保存到数据库
            db_alarm_data = {
                'timestamp': alarm_data.get('timestamp', datetime.utcnow()),
                'device_id': alarm_data['device_id'],
                'alarm_type': alarm_data['alarm_type'],
                'alarm_level': alarm_level,
                'message': message,
                'threshold_value': alarm_data.get('threshold_value'),
                'actual_value': alarm_data.get('actual_value')
            }
            
            saved = self.db_manager.save_alarm(db_alarm_data)
            
            if saved:
                logger.warning(f"报警已触发并记录：{message}")
                
                # 发送邮件通知（如果配置了）
                if self.config.EMAIL_ENABLED:
                    self.send_email_notification(alarm_data)
                
                return True
            else:
                logger.debug(f"报警未记录（可能是重复报警）：{message}")
                return False
                
        except Exception as e:
            logger.error(f"触发报警时出错: {e}", exc_info=True)
            return False
    
    def _determine_alarm_level(self, alarm_data: Dict[str, Any]) -> str:
        """
        判定报警级别
        
        Args:
            alarm_data: 报警数据
        
        Returns:
            str: 报警级别 (warning, critical, emergency)
        """
        # 如果已经指定了级别，直接返回
        if 'alarm_level' in alarm_data and alarm_data['alarm_level']:
            return alarm_data['alarm_level']
        
        # 根据超出阈值的程度判定级别
        threshold_value = alarm_data.get('threshold_value')
        actual_value = alarm_data.get('actual_value')
        
        if threshold_value is not None and actual_value is not None:
            try:
                threshold_float = float(threshold_value)
                actual_float = float(actual_value)
                
                if threshold_float > 0:
                    exceed_ratio = (actual_float - threshold_float) / threshold_float
                    
                    # 超出50%以上为紧急
                    if exceed_ratio >= 0.5:
                        return 'emergency'
                    # 超出20%以上为严重
                    elif exceed_ratio >= 0.2:
                        return 'critical'
                    # 其他为警告
                    else:
                        return 'warning'
            except (ValueError, TypeError, ZeroDivisionError):
                pass
        
        # 默认为警告级别
        return 'warning'
    
    def _format_alarm_message(self, alarm_data: Dict[str, Any]) -> str:
        """
        格式化报警消息
        
        Args:
            alarm_data: 报警数据
        
        Returns:
            str: 格式化的报警消息
        """
        device_name = alarm_data.get('device_name', alarm_data.get('device_id'))
        parameter_name = alarm_data.get('parameter_name', '参数')
        threshold_value = alarm_data.get('threshold_value')
        actual_value = alarm_data.get('actual_value')
        alarm_level = alarm_data.get('alarm_level', 'warning')
        
        # 级别中文映射
        level_map = {
            'warning': '警告',
            'critical': '严重',
            'emergency': '紧急'
        }
        level_text = level_map.get(alarm_level, alarm_level)
        
        if threshold_value is not None and actual_value is not None:
            message = (
                f"[{level_text}] 设备 {device_name} 的 {parameter_name} 超过阈值：\n"
                f"实际值: {actual_value:.2f}, 阈值: {threshold_value:.2f}, "
                f"超出: {((actual_value - threshold_value) / threshold_value * 100):.1f}%"
            )
        else:
            message = alarm_data.get('message', f"[{level_text}] 设备 {device_name} 触发报警")
        
        return message
    
    def send_email_notification(self, alarm_data: Dict[str, Any]) -> bool:
        """
        发送报警邮件通知
        WHERE 配置了邮件通知，发送报警邮件
        
        Args:
            alarm_data: 报警数据
        
        Returns:
            bool: 是否发送成功
        """
        # 检查邮件通知是否启用
        if not self.config.EMAIL_ENABLED:
            logger.debug("邮件通知未启用")
            return False
        
        # 检查必要的邮件配置
        if not self.config.SMTP_SERVER or not self.config.SMTP_USER:
            logger.warning("邮件配置不完整，无法发送通知")
            return False
        
        if not self.config.ALERT_EMAIL_TO or len(self.config.ALERT_EMAIL_TO) == 0:
            logger.warning("未配置收件人邮箱，无法发送通知")
            return False
        
        try:
            # 创建邮件内容
            subject = self._format_email_subject(alarm_data)
            body = self._format_email_body(alarm_data)
            
            # 创建邮件对象
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.config.SMTP_USER
            msg['To'] = ', '.join(self.config.ALERT_EMAIL_TO)
            
            # 添加纯文本和HTML版本
            text_part = MIMEText(body, 'plain', 'utf-8')
            html_part = MIMEText(self._format_email_html(alarm_data), 'html', 'utf-8')
            msg.attach(text_part)
            msg.attach(html_part)
            
            # 连接SMTP服务器并发送
            logger.info(f"正在连接SMTP服务器: {self.config.SMTP_SERVER}:{self.config.SMTP_PORT}")
            
            with smtplib.SMTP(self.config.SMTP_SERVER, self.config.SMTP_PORT, timeout=10) as server:
                server.starttls()  # 启用TLS加密
                server.login(self.config.SMTP_USER, self.config.SMTP_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"报警邮件已发送至: {', '.join(self.config.ALERT_EMAIL_TO)}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP认证失败: {e}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP错误: {e}")
            return False
        except Exception as e:
            logger.error(f"发送邮件时出错: {e}", exc_info=True)
            return False
    
    def _format_email_subject(self, alarm_data: Dict[str, Any]) -> str:
        """
        格式化邮件主题
        
        Args:
            alarm_data: 报警数据
        
        Returns:
            str: 邮件主题
        """
        alarm_level = alarm_data.get('alarm_level', 'warning')
        device_name = alarm_data.get('device_name', alarm_data.get('device_id'))
        
        level_map = {
            'warning': '⚠️ 警告',
            'critical': '🔴 严重',
            'emergency': '🚨 紧急'
        }
        level_prefix = level_map.get(alarm_level, '⚠️')
        
        return f"{level_prefix} 能源管理系统报警 - {device_name}"
    
    def _format_email_body(self, alarm_data: Dict[str, Any]) -> str:
        """
        格式化邮件正文（纯文本版本）
        
        Args:
            alarm_data: 报警数据
        
        Returns:
            str: 邮件正文
        """
        timestamp = alarm_data.get('timestamp', datetime.utcnow())
        device_name = alarm_data.get('device_name', alarm_data.get('device_id'))
        alarm_level = alarm_data.get('alarm_level', 'warning')
        message = alarm_data.get('message', '未知报警')
        
        level_map = {
            'warning': '警告',
            'critical': '严重',
            'emergency': '紧急'
        }
        level_text = level_map.get(alarm_level, alarm_level)
        
        body = f"""
能源管理系统报警通知

报警时间: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}
设备名称: {device_name}
设备ID: {alarm_data.get('device_id')}
报警级别: {level_text}
报警类型: {alarm_data.get('alarm_type', '未知')}

报警详情:
{message}
"""
        
        if alarm_data.get('parameter_name'):
            body += f"\n参数名称: {alarm_data.get('parameter_name')}"
        
        if alarm_data.get('threshold_value') is not None:
            body += f"\n阈值: {alarm_data.get('threshold_value'):.2f}"
        
        if alarm_data.get('actual_value') is not None:
            body += f"\n实际值: {alarm_data.get('actual_value'):.2f}"
        
        body += "\n\n请及时处理此报警。\n\n---\n此邮件由能源管理系统自动发送，请勿回复。"
        
        return body
    
    def _format_email_html(self, alarm_data: Dict[str, Any]) -> str:
        """
        格式化邮件正文（HTML版本）
        
        Args:
            alarm_data: 报警数据
        
        Returns:
            str: HTML格式的邮件正文
        """
        timestamp = alarm_data.get('timestamp', datetime.utcnow())
        device_name = alarm_data.get('device_name', alarm_data.get('device_id'))
        alarm_level = alarm_data.get('alarm_level', 'warning')
        message = alarm_data.get('message', '未知报警')
        
        # 级别颜色映射
        level_colors = {
            'warning': '#FFA500',
            'critical': '#FF4500',
            'emergency': '#DC143C'
        }
        level_color = level_colors.get(alarm_level, '#FFA500')
        
        level_map = {
            'warning': '警告',
            'critical': '严重',
            'emergency': '紧急'
        }
        level_text = level_map.get(alarm_level, alarm_level)
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: {level_color}; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
        .content {{ background-color: #f9f9f9; padding: 20px; border: 1px solid #ddd; border-top: none; }}
        .info-row {{ margin: 10px 0; padding: 10px; background-color: white; border-left: 3px solid {level_color}; }}
        .label {{ font-weight: bold; color: #555; }}
        .value {{ color: #333; }}
        .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #888; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>能源管理系统报警通知</h2>
        </div>
        <div class="content">
            <div class="info-row">
                <span class="label">报警时间:</span>
                <span class="value">{timestamp.strftime('%Y-%m-%d %H:%M:%S')}</span>
            </div>
            <div class="info-row">
                <span class="label">设备名称:</span>
                <span class="value">{device_name}</span>
            </div>
            <div class="info-row">
                <span class="label">设备ID:</span>
                <span class="value">{alarm_data.get('device_id')}</span>
            </div>
            <div class="info-row">
                <span class="label">报警级别:</span>
                <span class="value" style="color: {level_color}; font-weight: bold;">{level_text}</span>
            </div>
            <div class="info-row">
                <span class="label">报警类型:</span>
                <span class="value">{alarm_data.get('alarm_type', '未知')}</span>
            </div>
"""
        
        if alarm_data.get('parameter_name'):
            html += f"""
            <div class="info-row">
                <span class="label">参数名称:</span>
                <span class="value">{alarm_data.get('parameter_name')}</span>
            </div>
"""
        
        if alarm_data.get('threshold_value') is not None:
            html += f"""
            <div class="info-row">
                <span class="label">阈值:</span>
                <span class="value">{alarm_data.get('threshold_value'):.2f}</span>
            </div>
"""
        
        if alarm_data.get('actual_value') is not None:
            html += f"""
            <div class="info-row">
                <span class="label">实际值:</span>
                <span class="value" style="color: {level_color}; font-weight: bold;">{alarm_data.get('actual_value'):.2f}</span>
            </div>
"""
        
        html += f"""
            <div class="info-row">
                <span class="label">报警详情:</span>
                <div class="value" style="margin-top: 10px; white-space: pre-line;">{message}</div>
            </div>
            <div style="margin-top: 20px; padding: 15px; background-color: #fff3cd; border-left: 3px solid #ffc107;">
                <strong>⚠️ 请及时处理此报警</strong>
            </div>
        </div>
        <div class="footer">
            <p>此邮件由能源管理系统自动发送，请勿回复。</p>
        </div>
    </div>
</body>
</html>
"""
        
        return html
    
    def process_alarms(self, alarms: List[Dict[str, Any]]) -> int:
        """
        批量处理报警列表
        
        Args:
            alarms: 报警数据列表
        
        Returns:
            int: 成功处理的报警数量
        """
        if not alarms:
            return 0
        
        success_count = 0
        for alarm in alarms:
            if self.trigger_alarm(alarm):
                success_count += 1
        
        logger.info(f"批量处理报警完成：共 {len(alarms)} 条，成功 {success_count} 条")
        return success_count
    
    def get_alarm_statistics(self, start_time: datetime = None, end_time: datetime = None) -> Dict[str, Any]:
        """
        获取报警统计信息
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
        
        Returns:
            Dict: 报警统计信息
        """
        try:
            # 查询报警数据
            result = self.db_manager.query_history(
                table_name='alarms',
                start_time=start_time,
                end_time=end_time,
                page=1,
                page_size=10000  # 获取所有数据用于统计
            )
            
            if not result or 'data' not in result:
                return {
                    'total': 0,
                    'by_level': {},
                    'by_device': {},
                    'acknowledged_count': 0
                }
            
            alarms = result['data']
            
            # 统计各级别报警数量
            by_level = {}
            by_device = {}
            acknowledged_count = 0
            
            for alarm in alarms:
                # 按级别统计
                level = alarm.get('alarm_level', 'unknown')
                by_level[level] = by_level.get(level, 0) + 1
                
                # 按设备统计
                device_id = alarm.get('device_id', 'unknown')
                by_device[device_id] = by_device.get(device_id, 0) + 1
                
                # 统计已确认数量
                if alarm.get('acknowledged'):
                    acknowledged_count += 1
            
            return {
                'total': len(alarms),
                'by_level': by_level,
                'by_device': by_device,
                'acknowledged_count': acknowledged_count,
                'unacknowledged_count': len(alarms) - acknowledged_count
            }
            
        except Exception as e:
            logger.error(f"获取报警统计信息时出错: {e}", exc_info=True)
            return {
                'total': 0,
                'by_level': {},
                'by_device': {},
                'acknowledged_count': 0
            }
