"""
数据处理模块单元测试
测试DataProcessor类的数据清洗、异常检测和OEE计算功能
"""

import pytest
from datetime import datetime
from decimal import Decimal
from data_processor import DataProcessor


class TestDataProcessorCleanData:
    """测试数据清洗功能"""
    
    def setup_method(self):
        """每个测试方法前执行"""
        self.processor = DataProcessor()
    
    def test_clean_valid_data(self):
        """测试清洗有效数据"""
        raw_data = {
            'device_id': 'conveyor',
            'device_name': 'Conveyor Belt',
            'power_kw': 2.5,
            'energy_kwh': 15.3,
            'status': 'running',
            'timestamp': '2025-12-01 10:30:00'
        }
        
        result = self.processor.clean_data(raw_data)
        
        assert result is not None
        assert result['device_id'] == 'conveyor'
        assert result['device_name'] == 'Conveyor Belt'
        assert result['power_kw'] == Decimal('2.5')
        assert result['energy_kwh'] == Decimal('15.3')
        assert result['status'] == 'running'
        assert isinstance(result['timestamp'], datetime)
    
    def test_clean_data_with_missing_device_id(self):
        """测试缺少device_id的数据"""
        raw_data = {
            'power_kw': 2.5,
            'energy_kwh': 15.3
        }
        
        result = self.processor.clean_data(raw_data)
        
        assert result is None
    
    def test_clean_data_with_invalid_device_id(self):
        """测试无效device_id的数据"""
        raw_data = {
            'device_id': '',
            'power_kw': 2.5
        }
        
        result = self.processor.clean_data(raw_data)
        
        assert result is None
    
    def test_clean_data_with_none_input(self):
        """测试None输入"""
        result = self.processor.clean_data(None)
        assert result is None
    
    def test_clean_data_with_empty_dict(self):
        """测试空字典输入"""
        result = self.processor.clean_data({})
        assert result is None
    
    def test_clean_data_power_out_of_range(self):
        """测试功率超出范围"""
        raw_data = {
            'device_id': 'conveyor',
            'power_kw': 150.0  # 超过默认最大值100
        }
        
        result = self.processor.clean_data(raw_data)
        
        # 数据应该被清洗，但power_kw字段应该被过滤掉
        assert result is None or 'power_kw' not in result
    
    def test_clean_data_negative_power(self):
        """测试负功率值"""
        raw_data = {
            'device_id': 'conveyor',
            'power_kw': -5.0
        }
        
        result = self.processor.clean_data(raw_data)
        
        assert result is None or 'power_kw' not in result
    
    def test_clean_data_with_string_numbers(self):
        """测试字符串格式的数字"""
        raw_data = {
            'device_id': 'station1',
            'power_kw': '3.5',
            'energy_kwh': '20.0'
        }
        
        result = self.processor.clean_data(raw_data)
        
        assert result is not None
        assert result['power_kw'] == Decimal('3.5')
        assert result['energy_kwh'] == Decimal('20.0')
    
    def test_clean_data_with_invalid_number_format(self):
        """测试无效数字格式"""
        raw_data = {
            'device_id': 'station1',
            'power_kw': 'invalid',
            'energy_kwh': 20.0
        }
        
        result = self.processor.clean_data(raw_data)
        
        # power_kw应该被过滤，但energy_kwh应该保留
        assert result is not None
        assert 'power_kw' not in result
        assert result['energy_kwh'] == Decimal('20.0')
    
    def test_clean_data_with_production_fields(self):
        """测试包含生产数据的清洗"""
        raw_data = {
            'device_id': 'production_line',
            'product_count': 100,
            'reject_count': 5,
            'runtime_seconds': 3600,
            'downtime_seconds': 300
        }
        
        result = self.processor.clean_data(raw_data)
        
        assert result is not None
        assert result['product_count'] == 100
        assert result['reject_count'] == 5
        assert result['runtime_seconds'] == 3600
        assert result['downtime_seconds'] == 300
    
    def test_clean_data_with_negative_production_count(self):
        """测试负数生产计数"""
        raw_data = {
            'device_id': 'production_line',
            'product_count': -10
        }
        
        result = self.processor.clean_data(raw_data)
        
        assert result is None or 'product_count' not in result
    
    def test_clean_data_timestamp_formats(self):
        """测试不同时间戳格式"""
        # ISO格式
        raw_data1 = {
            'device_id': 'test',
            'power_kw': 1.0,
            'timestamp': '2025-12-01T10:30:00Z'
        }
        result1 = self.processor.clean_data(raw_data1)
        assert result1 is not None
        assert isinstance(result1['timestamp'], datetime)
        
        # Unix时间戳
        raw_data2 = {
            'device_id': 'test',
            'power_kw': 1.0,
            'timestamp': 1733053800
        }
        result2 = self.processor.clean_data(raw_data2)
        assert result2 is not None
        assert isinstance(result2['timestamp'], datetime)
        
        # datetime对象
        raw_data3 = {
            'device_id': 'test',
            'power_kw': 1.0,
            'timestamp': datetime(2025, 12, 1, 10, 30, 0)
        }
        result3 = self.processor.clean_data(raw_data3)
        assert result3 is not None
        assert result3['timestamp'] == datetime(2025, 12, 1, 10, 30, 0)


class TestDataProcessorAnomalyDetection:
    """测试异常检测功能"""
    
    def setup_method(self):
        """每个测试方法前执行"""
        self.processor = DataProcessor()
    
    def test_detect_single_anomaly_no_alarm(self):
        """测试单次异常不触发报警"""
        result = self.processor.detect_anomaly(
            device_id='conveyor',
            parameter='power_kw',
            value=6.0,
            threshold=5.0,
            comparison='greater'
        )
        
        assert result is False
    
    def test_detect_consecutive_anomalies_trigger_alarm(self):
        """测试连续3次异常触发报警"""
        device_id = 'conveyor'
        parameter = 'power_kw'
        threshold = 5.0
        
        # 第一次异常
        result1 = self.processor.detect_anomaly(
            device_id=device_id,
            parameter=parameter,
            value=6.0,
            threshold=threshold,
            comparison='greater'
        )
        assert result1 is False
        
        # 第二次异常
        result2 = self.processor.detect_anomaly(
            device_id=device_id,
            parameter=parameter,
            value=6.5,
            threshold=threshold,
            comparison='greater'
        )
        assert result2 is False
        
        # 第三次异常，应该触发报警
        result3 = self.processor.detect_anomaly(
            device_id=device_id,
            parameter=parameter,
            value=7.0,
            threshold=threshold,
            comparison='greater'
        )
        assert result3 is True
    
    def test_detect_anomaly_interrupted_sequence(self):
        """测试异常序列被中断"""
        device_id = 'station1'
        parameter = 'power_kw'
        threshold = 5.0
        
        # 第一次异常
        self.processor.detect_anomaly(device_id, parameter, 6.0, threshold, 'greater')
        
        # 第二次正常
        result2 = self.processor.detect_anomaly(device_id, parameter, 4.0, threshold, 'greater')
        assert result2 is False
        
        # 第三次异常，但序列已被中断
        result3 = self.processor.detect_anomaly(device_id, parameter, 6.0, threshold, 'greater')
        assert result3 is False
    
    def test_detect_anomaly_less_than_comparison(self):
        """测试小于阈值的异常检测"""
        device_id = 'conveyor'
        parameter = 'speed'
        threshold = 1.0
        
        # 连续3次低于阈值
        self.processor.detect_anomaly(device_id, parameter, 0.5, threshold, 'less')
        self.processor.detect_anomaly(device_id, parameter, 0.3, threshold, 'less')
        result = self.processor.detect_anomaly(device_id, parameter, 0.2, threshold, 'less')
        
        assert result is True
    
    def test_detect_anomaly_multiple_devices(self):
        """测试多设备异常检测独立性"""
        threshold = 5.0
        
        # 设备1连续异常
        self.processor.detect_anomaly('device1', 'power', 6.0, threshold, 'greater')
        self.processor.detect_anomaly('device1', 'power', 6.0, threshold, 'greater')
        result1 = self.processor.detect_anomaly('device1', 'power', 6.0, threshold, 'greater')
        
        # 设备2只有一次异常
        result2 = self.processor.detect_anomaly('device2', 'power', 6.0, threshold, 'greater')
        
        assert result1 is True
        assert result2 is False
    
    def test_detect_anomaly_multiple_parameters(self):
        """测试同一设备多参数异常检测独立性"""
        device_id = 'conveyor'
        
        # power参数连续异常
        self.processor.detect_anomaly(device_id, 'power', 6.0, 5.0, 'greater')
        self.processor.detect_anomaly(device_id, 'power', 6.0, 5.0, 'greater')
        result_power = self.processor.detect_anomaly(device_id, 'power', 6.0, 5.0, 'greater')
        
        # speed参数只有一次异常
        result_speed = self.processor.detect_anomaly(device_id, 'speed', 6.0, 5.0, 'greater')
        
        assert result_power is True
        assert result_speed is False
    
    def test_reset_anomaly_history_all(self):
        """测试重置所有异常历史"""
        # 创建一些异常历史
        self.processor.detect_anomaly('device1', 'power', 6.0, 5.0, 'greater')
        self.processor.detect_anomaly('device2', 'power', 6.0, 5.0, 'greater')
        
        # 重置所有
        self.processor.reset_anomaly_history()
        
        assert len(self.processor.anomaly_history) == 0
    
    def test_reset_anomaly_history_device(self):
        """测试重置指定设备的异常历史"""
        # 创建异常历史
        self.processor.detect_anomaly('device1', 'power', 6.0, 5.0, 'greater')
        self.processor.detect_anomaly('device1', 'speed', 6.0, 5.0, 'greater')
        self.processor.detect_anomaly('device2', 'power', 6.0, 5.0, 'greater')
        
        # 重置device1
        self.processor.reset_anomaly_history('device1')
        
        assert 'device1' in self.processor.anomaly_history
        assert len(self.processor.anomaly_history['device1']) == 0
        assert 'device2' in self.processor.anomaly_history
    
    def test_reset_anomaly_history_parameter(self):
        """测试重置指定参数的异常历史"""
        device_id = 'device1'
        
        # 创建异常历史
        self.processor.detect_anomaly(device_id, 'power', 6.0, 5.0, 'greater')
        self.processor.detect_anomaly(device_id, 'speed', 6.0, 5.0, 'greater')
        
        # 重置power参数
        self.processor.reset_anomaly_history(device_id, 'power')
        
        assert 'power' in self.processor.anomaly_history[device_id]
        assert len(self.processor.anomaly_history[device_id]['power']) == 0
        assert 'speed' in self.processor.anomaly_history[device_id]


class TestDataProcessorOEECalculation:
    """测试OEE计算功能"""
    
    def setup_method(self):
        """每个测试方法前执行"""
        self.processor = DataProcessor()
    
    def test_calculate_oee_normal_case(self):
        """测试正常情况的OEE计算"""
        result = self.processor.calculate_oee(
            runtime_seconds=3600,      # 1小时运行
            downtime_seconds=400,      # 400秒停机
            product_count=300,         # 生产300件
            reject_count=10,           # 10件不良品
            ideal_cycle_time=10.0      # 理想节拍10秒/件
        )
        
        assert result is not None
        assert 'availability' in result
        assert 'performance' in result
        assert 'quality' in result
        assert 'oee' in result
        
        # 可用率 = 3600 / (3600 + 400) = 90%
        assert result['availability'] == 90.0
        
        # 性能率 = (300 * 10) / 3600 = 83.33%
        assert abs(result['performance'] - 83.33) < 0.01
        
        # 质量率 = (300 - 10) / 300 = 96.67%
        assert abs(result['quality'] - 96.67) < 0.01
        
        # OEE = 90 * 83.33 * 96.67 / 10000 ≈ 72.5%
        assert 72.0 <= result['oee'] <= 73.0
    
    def test_calculate_oee_perfect_production(self):
        """测试完美生产的OEE"""
        result = self.processor.calculate_oee(
            runtime_seconds=3600,
            downtime_seconds=0,
            product_count=360,
            reject_count=0,
            ideal_cycle_time=10.0
        )
        
        assert result['availability'] == 100.0
        assert result['performance'] == 100.0
        assert result['quality'] == 100.0
        assert result['oee'] == 100.0
    
    def test_calculate_oee_zero_production(self):
        """测试零产量的OEE"""
        result = self.processor.calculate_oee(
            runtime_seconds=3600,
            downtime_seconds=0,
            product_count=0,
            reject_count=0,
            ideal_cycle_time=10.0
        )
        
        assert result['availability'] == 100.0
        assert result['performance'] == 0.0
        assert result['quality'] == 100.0  # 没有生产时质量率为100%
        assert result['oee'] == 0.0
    
    def test_calculate_oee_all_rejects(self):
        """测试全部不良品的OEE"""
        result = self.processor.calculate_oee(
            runtime_seconds=3600,
            downtime_seconds=0,
            product_count=100,
            reject_count=100,
            ideal_cycle_time=10.0
        )
        
        assert result['quality'] == 0.0
        assert result['oee'] == 0.0
    
    def test_calculate_oee_negative_runtime(self):
        """测试负运行时间"""
        result = self.processor.calculate_oee(
            runtime_seconds=-100,
            downtime_seconds=0,
            product_count=100,
            reject_count=0,
            ideal_cycle_time=10.0
        )
        
        # 应该返回零值OEE
        assert result['oee'] == 0.0
        assert result['availability'] == 0.0
    
    def test_calculate_oee_negative_product_count(self):
        """测试负产量"""
        result = self.processor.calculate_oee(
            runtime_seconds=3600,
            downtime_seconds=0,
            product_count=-100,
            reject_count=0,
            ideal_cycle_time=10.0
        )
        
        assert result['oee'] == 0.0
    
    def test_calculate_oee_reject_exceeds_product(self):
        """测试不良品数量超过总产量"""
        result = self.processor.calculate_oee(
            runtime_seconds=3600,
            downtime_seconds=0,
            product_count=100,
            reject_count=150,
            ideal_cycle_time=10.0
        )
        
        assert result['oee'] == 0.0
    
    def test_calculate_oee_zero_ideal_cycle_time(self):
        """测试零理想节拍时间"""
        result = self.processor.calculate_oee(
            runtime_seconds=3600,
            downtime_seconds=0,
            product_count=100,
            reject_count=0,
            ideal_cycle_time=0.0
        )
        
        assert result['oee'] == 0.0
    
    def test_calculate_oee_zero_planned_time(self):
        """测试零计划生产时间"""
        result = self.processor.calculate_oee(
            runtime_seconds=0,
            downtime_seconds=0,
            product_count=0,
            reject_count=0,
            ideal_cycle_time=10.0
        )
        
        assert result['oee'] == 0.0
    
    def test_calculate_oee_high_performance(self):
        """测试高性能率（超过100%的情况）"""
        result = self.processor.calculate_oee(
            runtime_seconds=3600,
            downtime_seconds=0,
            product_count=500,  # 超过理想产量
            reject_count=0,
            ideal_cycle_time=10.0
        )
        
        # 性能率应该被限制在100%
        assert result['performance'] == 100.0
    
    def test_calculate_oee_with_custom_planned_time(self):
        """测试自定义计划生产时间"""
        result = self.processor.calculate_oee(
            runtime_seconds=3000,
            downtime_seconds=500,
            product_count=300,
            reject_count=0,
            ideal_cycle_time=10.0,
            planned_production_time=4000  # 自定义计划时间
        )
        
        # 可用率 = 3000 / 4000 = 75%
        assert result['availability'] == 75.0


class TestDataProcessorBatchOperations:
    """测试批量操作功能"""
    
    def setup_method(self):
        """每个测试方法前执行"""
        self.processor = DataProcessor()
    
    def test_batch_clean_data(self):
        """测试批量数据清洗"""
        raw_data_list = [
            {'device_id': 'device1', 'power_kw': 2.5},
            {'device_id': 'device2', 'power_kw': 3.0},
            {'device_id': 'device3', 'power_kw': 'invalid'},  # 无效数据
            {'power_kw': 4.0},  # 缺少device_id
        ]
        
        result = self.processor.batch_clean_data(raw_data_list)
        
        # 应该只有2条有效数据
        assert len(result) == 2
        assert result[0]['device_id'] == 'device1'
        assert result[1]['device_id'] == 'device2'
    
    def test_batch_clean_empty_list(self):
        """测试空列表批量清洗"""
        result = self.processor.batch_clean_data([])
        assert len(result) == 0
    
    def test_get_anomaly_statistics(self):
        """测试获取异常统计信息"""
        # 创建一些异常历史
        self.processor.detect_anomaly('device1', 'power', 6.0, 5.0, 'greater')
        self.processor.detect_anomaly('device1', 'power', 6.0, 5.0, 'greater')
        self.processor.detect_anomaly('device1', 'speed', 0.5, 1.0, 'less')
        self.processor.detect_anomaly('device2', 'power', 6.0, 5.0, 'greater')
        
        stats = self.processor.get_anomaly_statistics()
        
        assert stats['total_devices'] == 2
        assert 'device1' in stats['devices']
        assert 'device2' in stats['devices']
        assert stats['devices']['device1']['total_parameters'] == 2
        assert 'power' in stats['devices']['device1']['parameters']
        assert 'speed' in stats['devices']['device1']['parameters']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
