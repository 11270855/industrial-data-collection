"""
数据处理模块使用示例
演示DataProcessor类的各种功能
"""

import sys
from datetime import datetime
from data_processor import DataProcessor
from config import config

def example_clean_data():
    """示例：数据清洗"""
    print("\n=== 数据清洗示例 ===")
    
    processor = DataProcessor(config)
    
    # 测试数据1：正常数据
    raw_data1 = {
        'timestamp': '2025-12-01 10:30:00',
        'device_id': 'conveyor',
        'device_name': '传送带',
        'power_kw': 2.5,
        'energy_kwh': 15.3,
        'status': 'running'
    }
    
    cleaned1 = processor.clean_data(raw_data1)
    print(f"原始数据: {raw_data1}")
    print(f"清洗后: {cleaned1}")
    
    # 测试数据2：包含无效值
    raw_data2 = {
        'device_id': 'station1',
        'power_kw': 150.0,  # 超出范围
        'energy_kwh': -5.0,  # 负值
        'status': '  RUNNING  '
    }
    
    cleaned2 = processor.clean_data(raw_data2)
    print(f"\n原始数据: {raw_data2}")
    print(f"清洗后: {cleaned2}")
    
    # 测试数据3：缺少必需字段
    raw_data3 = {
        'power_kw': 3.0,
        'energy_kwh': 10.0
    }
    
    cleaned3 = processor.clean_data(raw_data3)
    print(f"\n原始数据: {raw_data3}")
    print(f"清洗后: {cleaned3}")


def example_detect_anomaly():
    """示例：异常检测"""
    print("\n=== 异常检测示例 ===")
    
    processor = DataProcessor(config)
    
    device_id = 'conveyor'
    parameter = 'power_kw'
    threshold = 5.0
    
    # 模拟连续的功率读数
    power_readings = [4.5, 5.2, 5.8, 6.1, 5.9, 4.8, 3.2]
    
    print(f"设备: {device_id}, 参数: {parameter}, 阈值: {threshold}")
    print(f"连续异常阈值: {processor.consecutive_anomaly_threshold}次\n")
    
    for i, power in enumerate(power_readings, 1):
        is_alarm = processor.detect_anomaly(
            device_id=device_id,
            parameter=parameter,
            value=power,
            threshold=threshold,
            comparison='greater'
        )
        
        status = "🚨 触发报警" if is_alarm else "✓ 正常"
        print(f"读数 {i}: 功率={power} kW - {status}")
    
    # 显示异常统计
    stats = processor.get_anomaly_statistics()
    print(f"\n异常统计: {stats}")


def example_calculate_oee():
    """示例：OEE计算"""
    print("\n=== OEE计算示例 ===")
    
    processor = DataProcessor(config)
    
    # 场景1：正常生产
    print("\n场景1：正常生产")
    oee1 = processor.calculate_oee(
        runtime_seconds=7200,      # 运行2小时
        downtime_seconds=800,      # 停机约13分钟
        product_count=600,         # 生产600件
        reject_count=12,           # 12件不良品
        ideal_cycle_time=10.0      # 理想节拍10秒/件
    )
    print(f"运行时间: 7200秒 (2小时)")
    print(f"停机时间: 800秒 (13.3分钟)")
    print(f"总产量: 600件")
    print(f"不良品: 12件")
    print(f"理想节拍: 10秒/件")
    print(f"\n结果:")
    print(f"  可用率: {oee1['availability']:.2f}%")
    print(f"  性能率: {oee1['performance']:.2f}%")
    print(f"  质量率: {oee1['quality']:.2f}%")
    print(f"  OEE: {oee1['oee']:.2f}%")
    
    # 场景2：低效生产
    print("\n场景2：低效生产（频繁停机）")
    oee2 = processor.calculate_oee(
        runtime_seconds=5400,      # 运行1.5小时
        downtime_seconds=2600,     # 停机约43分钟
        product_count=400,         # 生产400件
        reject_count=50,           # 50件不良品
        ideal_cycle_time=10.0
    )
    print(f"运行时间: 5400秒 (1.5小时)")
    print(f"停机时间: 2600秒 (43.3分钟)")
    print(f"总产量: 400件")
    print(f"不良品: 50件")
    print(f"\n结果:")
    print(f"  可用率: {oee2['availability']:.2f}%")
    print(f"  性能率: {oee2['performance']:.2f}%")
    print(f"  质量率: {oee2['quality']:.2f}%")
    print(f"  OEE: {oee2['oee']:.2f}%")
    
    # 场景3：高效生产
    print("\n场景3：高效生产")
    oee3 = processor.calculate_oee(
        runtime_seconds=7800,      # 运行约2.17小时
        downtime_seconds=200,      # 停机约3分钟
        product_count=720,         # 生产720件
        reject_count=5,            # 5件不良品
        ideal_cycle_time=10.0
    )
    print(f"运行时间: 7800秒 (2.17小时)")
    print(f"停机时间: 200秒 (3.3分钟)")
    print(f"总产量: 720件")
    print(f"不良品: 5件")
    print(f"\n结果:")
    print(f"  可用率: {oee3['availability']:.2f}%")
    print(f"  性能率: {oee3['performance']:.2f}%")
    print(f"  质量率: {oee3['quality']:.2f}%")
    print(f"  OEE: {oee3['oee']:.2f}%")


def example_batch_processing():
    """示例：批量数据处理"""
    print("\n=== 批量数据处理示例 ===")
    
    processor = DataProcessor(config)
    
    # 批量原始数据
    raw_data_list = [
        {'device_id': 'conveyor', 'power_kw': 2.5, 'energy_kwh': 15.3},
        {'device_id': 'station1', 'power_kw': 4.2, 'energy_kwh': 25.1},
        {'device_id': 'station2', 'power_kw': 150.0, 'energy_kwh': 30.5},  # 功率超范围
        {'device_id': 'station3'},  # 缺少数据
        {'device_id': 'conveyor', 'power_kw': 3.1, 'energy_kwh': 18.7},
    ]
    
    print(f"输入数据: {len(raw_data_list)}条")
    cleaned_list = processor.batch_clean_data(raw_data_list)
    print(f"有效数据: {len(cleaned_list)}条")
    
    for i, data in enumerate(cleaned_list, 1):
        print(f"  {i}. {data['device_id']}: 功率={data.get('power_kw')} kW")


def main():
    """主函数"""
    print("=" * 60)
    print("数据处理模块 (DataProcessor) 使用示例")
    print("=" * 60)
    
    try:
        # 运行各个示例
        example_clean_data()
        example_detect_anomaly()
        example_calculate_oee()
        example_batch_processing()
        
        print("\n" + "=" * 60)
        print("所有示例运行完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
