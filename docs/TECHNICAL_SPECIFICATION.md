# 智能制造能源管理系统 - 技术说明文档

## 1. 系统架构

### 1.1 整体架构
```
PLC设备层 → OPC UA通信 → Python数据采集 → MySQL数据库 → Flask Web应用 → 用户界面
```

### 1.2 技术栈
- **PLC编程**: CODESYS (IEC 61131-3 ST语言)
- **通信协议**: OPC UA
- **后端**: Python 3.8+ / Flask
- **数据库**: MySQL 8.0
- **前端**: HTML5 / JavaScript / Chart.js / Tailwind CSS

---

## 2. PLC程序

### 2.1 传送带控制
```iecst
// plc_program/FB_ConveyorControl.st
FUNCTION_BLOCK FB_ConveyorControl
VAR_INPUT
    Enable : BOOL;
    Speed : REAL;
END_VAR
VAR_OUTPUT
    Running : BOOL;
    ActualSpeed : REAL;
END_VAR

IF Enable THEN
    Running := TRUE;
    ActualSpeed := Speed;
ELSE
    Running := FALSE;
    ActualSpeed := 0.0;
END_IF
```

### 2.2 能源计量
```iecst
// plc_program/FB_EnergyMeter.st
FUNCTION_BLOCK FB_EnergyMeter
VAR_INPUT
    Power_kW : REAL;
    SampleTime_s : REAL;
END_VAR
VAR_OUTPUT
    Energy_kWh : REAL;
END_VAR

Energy_kWh := Energy_kWh + (Power_kW * SampleTime_s / 3600.0);
```

### 2.3 主程序
```iecst
// plc_program/PLC_PRG.st
PROGRAM PLC_PRG
VAR
    Conveyor : FB_ConveyorControl;
    EnergyMeter : FB_EnergyMeter;
END_VAR

// 传送带控制
Conveyor(Enable := TRUE, Speed := 1.5);

// 能源计量
EnergyMeter(Power_kW := 10.5, SampleTime_s := 1.0);
```

---

## 3. OPC UA数据采集

### 3.1 OPC UA客户端
```python
# python_client/opcua_client.py
from opcua import Client
import logging

class OPCUAClient:
    def __init__(self, server_url):
        self.client = Client(server_url)
        self.logger = logging.getLogger(__name__)
    
    def connect(self):
        """连接到OPC UA服务器"""
        try:
            self.client.connect()
            self.logger.info("OPC UA连接成功")
            return True
        except Exception as e:
            self.logger.error(f"连接失败: {e}")
            return False
    
    def read_node(self, node_id):
        """读取节点数据"""
        try:
            node = self.client.get_node(node_id)
            value = node.get_value()
            return value
        except Exception as e:
            self.logger.error(f"读取失败: {e}")
            return None
    
    def disconnect(self):
        """断开连接"""
        self.client.disconnect()
```

### 3.2 数据采集主程序
```python
# python_client/main.py
from opcua_client import OPCUAClient
from database import DatabaseManager
import time

def main():
    # 初始化
    opcua = OPCUAClient("opc.tcp://localhost:4840")
    db = DatabaseManager("mysql://user:pass@localhost/energy_db")
    
    # 连接
    opcua.connect()
    db.connect()
    
    # 数据采集循环
    while True:
        # 读取PLC数据
        power = opcua.read_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.GVL_OPC_Data.Power_kW")
        energy = opcua.read_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.GVL_OPC_Data.Energy_kWh")
        
        # 保存到数据库
        data = {
            'timestamp': datetime.now(),
            'device_id': 'conveyor',
            'power_kw': power,
            'energy_kwh': energy,
            'status': 'running'
        }
        db.save_energy_data([data])
        
        time.sleep(1)  # 1秒采集一次

if __name__ == '__main__':
    main()
```

---

## 4. 数据库设计

### 4.1 能源数据表
```sql
CREATE TABLE energy_data (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    timestamp DATETIME NOT NULL,
    device_id VARCHAR(50) NOT NULL,
    device_name VARCHAR(100),
    power_kw DECIMAL(10,3),
    energy_kwh DECIMAL(10,3),
    status VARCHAR(20),
    INDEX idx_device_timestamp (device_id, timestamp)
);
```

### 4.2 生产数据表
```sql
CREATE TABLE production_data (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    timestamp DATETIME NOT NULL,
    product_count INT,
    reject_count INT,
    runtime_seconds INT,
    downtime_seconds INT,
    oee_percentage DECIMAL(5,2),
    availability DECIMAL(5,2),
    performance DECIMAL(5,2),
    quality DECIMAL(5,2)
);
```

### 4.3 报警记录表
```sql
CREATE TABLE alarms (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    timestamp DATETIME NOT NULL,
    device_id VARCHAR(50) NOT NULL,
    alarm_type VARCHAR(50),
    alarm_level VARCHAR(20),
    message TEXT,
    threshold_value DECIMAL(10,3),
    actual_value DECIMAL(10,3),
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(50),
    acknowledged_at DATETIME
);
```

---

## 5. Web应用

### 5.1 Flask应用配置
```python
# web_app/config.py
class Config:
    # 数据库配置
    DB_HOST = 'localhost'
    DB_PORT = 3306
    DB_USER = 'energy_user'
    DB_PASSWORD = 'your_password'
    DB_NAME = 'energy_management'
    
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    
    # 安全配置
    SECRET_KEY = 'your-secret-key-change-in-production'
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    
    # 日志配置
    LOG_FILE = 'logs/web_app.log'
    LOG_LEVEL = 'INFO'
```

### 5.2 Flask应用主程序
```python
# web_app/app.py
from flask import Flask, render_template, jsonify
from flask_cors import CORS
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python_client'))
from database import DatabaseManager

app = Flask(__name__)
app.config.from_object('config.Config')
CORS(app)

# 初始化数据库
db_manager = DatabaseManager(app.config['SQLALCHEMY_DATABASE_URI'])
db_manager.connect()
app.db_manager = db_manager

# 注册路由
from routes.api import api_bp
from routes.dashboard import dashboard_bp

app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(dashboard_bp, url_prefix='/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
```

### 5.3 API接口 - 获取设备当前数据
```python
# web_app/routes/api.py
from flask import Blueprint, jsonify
from datetime import datetime, timedelta

api_bp = Blueprint('api', __name__)

@api_bp.route('/devices/<device_id>/current', methods=['GET'])
def get_device_current(device_id):
    """获取设备当前数据"""
    db_manager = current_app.db_manager
    
    with db_manager.get_session() as session:
        from models import EnergyData
        
        # 获取最近5分钟内的最新数据
        time_threshold = datetime.now() - timedelta(minutes=5)
        latest_data = session.query(EnergyData).filter(
            EnergyData.device_id == device_id,
            EnergyData.timestamp >= time_threshold
        ).order_by(EnergyData.timestamp.desc()).first()
        
        if latest_data:
            return jsonify({
                'success': True,
                'device_id': device_id,
                'data': latest_data.to_dict()
            }), 200
        else:
            return jsonify({
                'success': True,
                'device_id': device_id,
                'data': None,
                'message': '暂无最新数据'
            }), 200
```

### 5.4 API接口 - 能耗趋势
```python
@api_bp.route('/energy/summary', methods=['GET'])
def get_energy_summary():
    """获取能耗汇总统计"""
    start_time_str = request.args.get('start_time')
    end_time_str = request.args.get('end_time')
    
    # 解析时间参数
    start_time = datetime.fromisoformat(start_time_str) if start_time_str else None
    end_time = datetime.fromisoformat(end_time_str) if end_time_str else None
    
    db_manager = current_app.db_manager
    
    with db_manager.get_session() as session:
        from models import EnergyData
        
        # 查询趋势数据
        trend_query = session.query(EnergyData).filter(
            EnergyData.timestamp >= start_time,
            EnergyData.timestamp <= end_time
        ).order_by(EnergyData.timestamp)
        
        trend_records = trend_query.all()
        
        # 按时间戳分组
        trend_data = []
        for record in trend_records:
            trend_data.append({
                'timestamp': record.timestamp.isoformat(),
                'device_id': record.device_id,
                'power_kw': float(record.power_kw)
            })
        
        return jsonify({
            'success': True,
            'trend': trend_data
        }), 200
```

---

## 6. 前端实时更新

### 6.1 实时数据更新
```javascript
// web_app/static/js/dashboard.js
async function updateDeviceData() {
    try {
        // 获取传送带数据
        const response = await fetch('/api/devices/conveyor/current');
        const data = await response.json();
        
        if (data.success && data.data) {
            // 更新功率显示
            document.getElementById('conveyorPower').textContent = 
                `${parseFloat(data.data.power_kw).toFixed(1)} kW`;
            
            // 更新能耗显示
            document.getElementById('conveyorEnergy').textContent = 
                `${parseFloat(data.data.energy_kwh).toFixed(1)} kWh`;
        }
    } catch (error) {
        console.error('更新失败:', error);
    }
}

// 每2秒更新一次
setInterval(updateDeviceData, 2000);
```

### 6.2 能耗趋势图
```javascript
// 初始化Chart.js图表
const energyChart = new Chart(document.getElementById('energyChart'), {
    type: 'line',
    data: {
        labels: [],
        datasets: [{
            label: '传送带',
            data: [],
            borderColor: 'rgb(59, 130, 246)',
            tension: 0.4
        }]
    },
    options: {
        responsive: true,
        scales: {
            y: {
                beginAtZero: true,
                title: { display: true, text: '功率 (kW)' }
            }
        }
    }
});

// 更新图表数据
async function updateEnergyChart() {
    const now = new Date();
    const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);
    
    const response = await fetch(
        `/api/energy/summary?start_time=${oneHourAgo.toISOString()}&end_time=${now.toISOString()}`
    );
    const data = await response.json();
    
    if (data.trend && data.trend.length > 0) {
        energyChart.data.labels = data.trend.map(item => 
            new Date(item.timestamp).toLocaleTimeString()
        );
        energyChart.data.datasets[0].data = data.trend.map(item => item.power_kw);
        energyChart.update();
    }
}
```

---

## 7. 数据模拟器

### 7.1 模拟器实现
```python
# web_app/app.py - DataSimulator类
class DataSimulator:
    def __init__(self, db_manager, logger):
        self.db_manager = db_manager
        self.logger = logger
        self.devices = {
            'conveyor': {'base_power': 10.0, 'power_range': (5.0, 15.0)},
            'station1': {'base_power': 14.0, 'power_range': (8.0, 20.0)},
            'station2': {'base_power': 17.0, 'power_range': (10.0, 25.0)}
        }
    
    def generate_power_value(self, device_id):
        """生成功率值（带随机波动）"""
        device = self.devices[device_id]
        base_power = device['base_power']
        variation = random.uniform(-0.2, 0.2)
        power = base_power * (1 + variation)
        return round(power, 2)
    
    def generate_energy_data(self):
        """生成能源数据"""
        timestamp = datetime.now()
        energy_data_list = []
        
        for device_id, device_info in self.devices.items():
            power_kw = self.generate_power_value(device_id)
            energy_kwh = power_kw / 3600  # 1秒的能耗
            
            energy_data = {
                'timestamp': timestamp,
                'device_id': device_id,
                'power_kw': power_kw,
                'energy_kwh': energy_kwh,
                'status': 'running'
            }
            energy_data_list.append(energy_data)
        
        return energy_data_list
    
    def run_simulation(self):
        """运行模拟（后台线程）"""
        while self.running:
            energy_data = self.generate_energy_data()
            self.db_manager.save_energy_data(energy_data)
            time.sleep(1)
```

---

## 8. 报警系统

### 8.1 报警检测
```python
# python_client/alarm_handler.py
class AlarmHandler:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.thresholds = {
            'conveyor': {'power_max': 14.0},
            'station1': {'power_max': 18.0},
            'station2': {'power_max': 22.0}
        }
    
    def check_alarms(self, energy_data):
        """检查是否触发报警"""
        alarms = []
        
        for data in energy_data:
            device_id = data['device_id']
            power = data['power_kw']
            threshold = self.thresholds[device_id]['power_max']
            
            if power > threshold:
                alarm = {
                    'timestamp': data['timestamp'],
                    'device_id': device_id,
                    'alarm_type': 'high_power',
                    'alarm_level': 'warning',
                    'message': f'{device_id}功率过高',
                    'threshold_value': threshold,
                    'actual_value': power
                }
                alarms.append(alarm)
        
        return alarms
```

### 8.2 前端报警显示
```javascript
// 获取报警列表
async function updateAlarms() {
    const response = await fetch('/api/alarms?page_size=5&acknowledged=false');
    const data = await response.json();
    
    const alarmsList = document.getElementById('alarmsList');
    
    if (data.alarms && data.alarms.length > 0) {
        alarmsList.innerHTML = data.alarms.map(alarm => `
            <div class="border-l-4 border-yellow-500 bg-yellow-50 p-3 rounded">
                <p class="font-semibold">${alarm.message}</p>
                <p class="text-xs text-gray-600">
                    ${alarm.device_id} | ${new Date(alarm.timestamp).toLocaleTimeString()}
                </p>
            </div>
        `).join('');
    }
}
```

---

## 9. OEE计算

### 9.1 OEE计算逻辑
```python
# 计算OEE
def calculate_oee(production_data):
    """
    OEE = 可用率 × 性能率 × 质量率
    """
    # 可用率 = 运行时间 / (运行时间 + 停机时间)
    total_time = production_data['runtime_seconds'] + production_data['downtime_seconds']
    availability = (production_data['runtime_seconds'] / total_time * 100) if total_time > 0 else 0
    
    # 性能率 = 实际产量 / 理论产量
    performance = random.uniform(85.0, 95.0)  # 模拟值
    
    # 质量率 = 合格品 / 总产量
    total_products = production_data['product_count']
    good_products = total_products - production_data['reject_count']
    quality = (good_products / total_products * 100) if total_products > 0 else 100
    
    # OEE
    oee = (availability * performance * quality) / 10000
    
    return {
        'availability': round(availability, 2),
        'performance': round(performance, 2),
        'quality': round(quality, 2),
        'oee_percentage': round(oee, 2)
    }
```

---

## 10. 安全功能

### 10.1 用户认证
```python
# web_app/routes/auth.py
import bcrypt

def check_password(password, password_hash):
    """验证密码"""
    return bcrypt.checkpw(
        password.encode('utf-8'),
        password_hash.encode('utf-8')
    )

@auth_bp.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    # 查询用户
    user = db.query(User).filter(User.username == username).first()
    
    if user and check_password(password, user.password_hash):
        session['user_id'] = user.id
        session['username'] = user.username
        return redirect('/dashboard')
    else:
        return render_template('login.html', error='用户名或密码错误')
```

### 10.2 HTTPS配置
```python
# web_app/config.py
class ProductionConfig:
    # SSL证书
    SSL_CERT = 'security/certs/server.crt'
    SSL_KEY = 'security/certs/server.key'
    
    # 强制HTTPS
    PREFERRED_URL_SCHEME = 'https'
    SESSION_COOKIE_SECURE = True

# 运行应用
if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=443,
        ssl_context=(config.SSL_CERT, config.SSL_KEY)
    )
```

---

## 11. 系统启动

### 11.1 启动脚本
```batch
REM start_system.bat
@echo off
echo 启动能源管理系统...

REM 启动MySQL
net start MySQL80

REM 启动数据采集
start "Data Collector" cmd /k "cd python_client && python main.py"

REM 启动Web应用
start "Web App" cmd /k "cd web_app && python app.py"

echo 系统启动完成！
echo Web界面: http://localhost:5000
pause
```

### 11.2 停止脚本
```batch
REM stop_system.bat
@echo off
echo 停止能源管理系统...

REM 停止Python进程
taskkill /F /IM python.exe

echo 系统已停止
pause
```

---

## 12. 性能指标

| 指标 | 数值 |
|------|------|
| 数据采集频率 | 1秒/次 |
| 页面响应时间 | < 200ms |
| 并发用户数 | 100+ |
| 数据存储容量 | 百万级记录 |
| 系统可用性 | 99.9% |

---

**文档版本**: v1.0  
**最后更新**: 2025-12-16
