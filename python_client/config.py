"""
配置文件模板
用于定义OPC UA服务器地址、数据库连接等参数
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """系统配置类"""
    
    # OPC UA服务器配置
    OPC_UA_SERVER_URL = os.getenv('OPC_UA_SERVER_URL', 'opc.tcp://localhost:4840')
    OPC_UA_TIMEOUT = int(os.getenv('OPC_UA_TIMEOUT', '3'))  # 连接超时（秒）
    OPC_UA_RETRY_MAX = int(os.getenv('OPC_UA_RETRY_MAX', '5'))  # 最大重试次数
    OPC_UA_RETRY_DELAY = int(os.getenv('OPC_UA_RETRY_DELAY', '5'))  # 重试延迟（秒）
    
    # 数据库配置
    DB_TYPE = os.getenv('DB_TYPE', 'mysql')  # 数据库类型: mysql 或 sqlite
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', '3306'))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'root')
    DB_NAME = os.getenv('DB_NAME', 'energy_management')
    
    # SQLite配置（开发环境）
    SQLITE_DB_PATH = os.getenv('SQLITE_DB_PATH', 'energy_management.db')
    
    @property
    def DATABASE_URI(self):
        """生成数据库连接URI"""
        if self.DB_TYPE == 'sqlite':
            return f'sqlite:///{self.SQLITE_DB_PATH}'
        else:
            return f'mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'
    
    # 数据采集配置
    DATA_COLLECTION_INTERVAL = int(os.getenv('DATA_COLLECTION_INTERVAL', '1'))  # 数据采集间隔（秒）
    BATCH_WRITE_INTERVAL = int(os.getenv('BATCH_WRITE_INTERVAL', '10'))  # 批量写入间隔（秒）
    
    # 报警配置
    ALARM_CHECK_INTERVAL = int(os.getenv('ALARM_CHECK_INTERVAL', '5'))  # 报警检查间隔（秒）
    ALARM_DUPLICATE_WINDOW = int(os.getenv('ALARM_DUPLICATE_WINDOW', '300'))  # 报警去重时间窗口（秒）
    ALARM_CONSECUTIVE_COUNT = int(os.getenv('ALARM_CONSECUTIVE_COUNT', '3'))  # 连续异常次数触发报警
    
    # 邮件通知配置（可选）
    EMAIL_ENABLED = os.getenv('EMAIL_ENABLED', 'False').lower() == 'true'
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USER = os.getenv('SMTP_USER', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    ALERT_EMAIL_TO = os.getenv('ALERT_EMAIL_TO', '').split(',')
    
    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/data_collector.log')
    LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', '10485760'))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))
    
    # OPC UA节点配置
    OPC_UA_NODES = {
        'conveyor': {
            'start': 'ns=2;s=ProductionLine_PLC.DeviceControl.ConveyorStart',
            'speed': 'ns=2;s=ProductionLine_PLC.DeviceControl.ConveyorSpeed',
            'power': 'ns=2;s=ProductionLine_PLC.EnergyData.ConveyorPower',
        },
        'station1': {
            'active': 'ns=2;s=ProductionLine_PLC.DeviceControl.Station1Active',
            'power': 'ns=2;s=ProductionLine_PLC.EnergyData.Station1Power',
        },
        'station2': {
            'active': 'ns=2;s=ProductionLine_PLC.DeviceControl.Station2Active',
            'power': 'ns=2;s=ProductionLine_PLC.EnergyData.Station2Power',
        },
        'energy': {
            'total_energy': 'ns=2;s=ProductionLine_PLC.EnergyData.TotalEnergy',
            'alarm': 'ns=2;s=ProductionLine_PLC.EnergyData.EnergyAlarm',
        },
        'production': {
            'product_count': 'ns=2;s=ProductionLine_PLC.Production.ProductCount',
            'reject_count': 'ns=2;s=ProductionLine_PLC.Production.RejectCount',
            'runtime': 'ns=2;s=ProductionLine_PLC.Production.RunTime',
            'downtime': 'ns=2;s=ProductionLine_PLC.Production.DownTime',
        }
    }
    
    # 数据有效性范围
    DATA_VALIDATION = {
        'power_min': 0.0,
        'power_max': 100.0,  # kW
        'energy_min': 0.0,
        'energy_max': 10000.0,  # kWh
        'speed_min': 0.0,
        'speed_max': 5.0,  # m/s
    }


# 创建全局配置实例
config = Config()
