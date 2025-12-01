"""
数据库模型定义
使用SQLAlchemy ORM定义所有数据表模型
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, BigInteger, String, DateTime, 
    Boolean, Text, Index, create_engine
)
from sqlalchemy.types import Numeric as Decimal
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import bcrypt

# 创建基类
Base = declarative_base()


class EnergyData(Base):
    """能源数据表模型"""
    __tablename__ = 'energy_data'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    device_id = Column(String(50), nullable=False, index=True)
    device_name = Column(String(100))
    power_kw = Column(Decimal(10, 3))
    energy_kwh = Column(Decimal(10, 3))
    status = Column(String(20))
    
    # 创建复合索引
    __table_args__ = (
        Index('idx_device_timestamp', 'device_id', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<EnergyData(device_id='{self.device_id}', timestamp='{self.timestamp}', power={self.power_kw})>"
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'device_id': self.device_id,
            'device_name': self.device_name,
            'power_kw': float(self.power_kw) if self.power_kw else None,
            'energy_kwh': float(self.energy_kwh) if self.energy_kwh else None,
            'status': self.status
        }


class ProductionData(Base):
    """生产数据表模型"""
    __tablename__ = 'production_data'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    product_count = Column(Integer)
    reject_count = Column(Integer)
    runtime_seconds = Column(Integer)
    downtime_seconds = Column(Integer)
    oee_percentage = Column(Decimal(5, 2))
    availability = Column(Decimal(5, 2))
    performance = Column(Decimal(5, 2))
    quality = Column(Decimal(5, 2))
    
    def __repr__(self):
        return f"<ProductionData(timestamp='{self.timestamp}', oee={self.oee_percentage}%)>"
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'product_count': self.product_count,
            'reject_count': self.reject_count,
            'runtime_seconds': self.runtime_seconds,
            'downtime_seconds': self.downtime_seconds,
            'oee_percentage': float(self.oee_percentage) if self.oee_percentage else None,
            'availability': float(self.availability) if self.availability else None,
            'performance': float(self.performance) if self.performance else None,
            'quality': float(self.quality) if self.quality else None
        }


class Alarm(Base):
    """报警记录表模型"""
    __tablename__ = 'alarms'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    device_id = Column(String(50), nullable=False, index=True)
    alarm_type = Column(String(50))
    alarm_level = Column(String(20))  # warning, critical, emergency
    message = Column(Text)
    threshold_value = Column(Decimal(10, 3))
    actual_value = Column(Decimal(10, 3))
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(50))
    acknowledged_at = Column(DateTime)
    
    # 创建复合索引
    __table_args__ = (
        Index('idx_alarm_device_timestamp', 'device_id', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<Alarm(device_id='{self.device_id}', level='{self.alarm_level}', timestamp='{self.timestamp}')>"
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'device_id': self.device_id,
            'alarm_type': self.alarm_type,
            'alarm_level': self.alarm_level,
            'message': self.message,
            'threshold_value': float(self.threshold_value) if self.threshold_value else None,
            'actual_value': float(self.actual_value) if self.actual_value else None,
            'acknowledged': self.acknowledged,
            'acknowledged_by': self.acknowledged_by,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None
        }


class User(Base):
    """用户表模型"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # admin, user
    email = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    
    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role}')>"
    
    def set_password(self, password):
        """设置密码（使用bcrypt哈希）"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        """验证密码"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def is_locked(self):
        """检查账户是否被锁定"""
        if self.locked_until and datetime.utcnow() < self.locked_until:
            return True
        return False
    
    def to_dict(self):
        """转换为字典格式（不包含密码）"""
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


class Threshold(Base):
    """阈值配置表模型"""
    __tablename__ = 'thresholds'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String(50), nullable=False)
    parameter_name = Column(String(50), nullable=False)
    threshold_value = Column(Decimal(10, 3), nullable=False)
    alarm_level = Column(String(20))  # warning, critical, emergency
    enabled = Column(Boolean, default=True)
    updated_by = Column(String(50))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 创建唯一约束
    __table_args__ = (
        Index('uk_device_param', 'device_id', 'parameter_name', unique=True),
    )
    
    def __repr__(self):
        return f"<Threshold(device_id='{self.device_id}', parameter='{self.parameter_name}', value={self.threshold_value})>"
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'parameter_name': self.parameter_name,
            'threshold_value': float(self.threshold_value) if self.threshold_value else None,
            'alarm_level': self.alarm_level,
            'enabled': self.enabled,
            'updated_by': self.updated_by,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
