"""
API路由模块
提供RESTful API端点用于数据查询和操作
"""

from flask import Blueprint, jsonify, request, current_app
from .auth import login_required, admin_required

# 创建API蓝图
api_bp = Blueprint('api', __name__)


@api_bp.route('/devices', methods=['GET'])
@login_required
def get_devices():
    """
    获取设备列表
    返回所有设备的基本信息
    """
    try:
        current_app.logger.info("API: 获取设备列表")
        
        # 定义系统中的设备列表
        devices = [
            {
                'id': 'conveyor',
                'name': '传送带',
                'type': 'conveyor',
                'description': '上料传送带，负责产品输送'
            },
            {
                'id': 'station1',
                'name': '加工工位1',
                'type': 'station',
                'description': '第一个加工工位'
            },
            {
                'id': 'station2',
                'name': '加工工位2',
                'type': 'station',
                'description': '第二个加工工位'
            }
        ]
        
        return jsonify({
            'success': True,
            'devices': devices,
            'total': len(devices)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"获取设备列表失败: {e}")
        return jsonify({
            'success': False,
            'error': '获取设备列表失败',
            'message': str(e)
        }), 500


@api_bp.route('/devices/<device_id>/current', methods=['GET'])
@login_required
def get_device_current(device_id):
    """
    获取设备当前数据
    返回指定设备的实时状态和能耗数据
    """
    try:
        current_app.logger.info(f"API: 获取设备当前数据 - {device_id}")
        
        db_manager = current_app.db_manager
        
        # 查询该设备最新的能源数据
        from datetime import datetime, timedelta
        
        with db_manager.get_session() as session:
            from models import EnergyData
            
            # 获取最近1分钟内的最新数据
            time_threshold = datetime.utcnow() - timedelta(minutes=1)
            latest_data = session.query(EnergyData).filter(
                EnergyData.device_id == device_id,
                EnergyData.timestamp >= time_threshold
            ).order_by(EnergyData.timestamp.desc()).first()
            
            if not latest_data:
                # 如果没有最近的数据，返回空数据
                return jsonify({
                    'success': True,
                    'device_id': device_id,
                    'data': None,
                    'message': '暂无最新数据'
                }), 200
            
            # 转换为字典并返回
            data = latest_data.to_dict()
            
            return jsonify({
                'success': True,
                'device_id': device_id,
                'data': data
            }), 200
            
    except Exception as e:
        current_app.logger.error(f"获取设备当前数据失败: {e}")
        return jsonify({
            'success': False,
            'error': '获取设备当前数据失败',
            'message': str(e)
        }), 500


@api_bp.route('/devices/<device_id>/history', methods=['GET'])
@login_required
def get_device_history(device_id):
    """
    获取设备历史数据
    支持时间范围查询和分页
    
    查询参数:
        - start_time: 开始时间 (ISO格式，可选)
        - end_time: 结束时间 (ISO格式，可选)
        - page: 页码 (默认1)
        - page_size: 每页记录数 (默认100)
    """
    try:
        current_app.logger.info(f"API: 获取设备历史数据 - {device_id}")
        
        # 获取查询参数
        start_time_str = request.args.get('start_time')
        end_time_str = request.args.get('end_time')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 100))
        
        # 验证分页参数
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 1000:
            page_size = 100
        
        # 解析时间参数
        from datetime import datetime
        start_time = None
        end_time = None
        
        if start_time_str:
            try:
                start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': '无效的开始时间格式',
                    'message': '请使用ISO格式，例如: 2025-12-01T10:00:00'
                }), 400
        
        if end_time_str:
            try:
                end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': '无效的结束时间格式',
                    'message': '请使用ISO格式，例如: 2025-12-01T10:00:00'
                }), 400
        
        # 使用DatabaseManager的query_history方法查询数据
        db_manager = current_app.db_manager
        result = db_manager.query_history(
            table_name='energy_data',
            start_time=start_time,
            end_time=end_time,
            device_id=device_id,
            page=page,
            page_size=page_size
        )
        
        if result is None:
            return jsonify({
                'success': False,
                'error': '查询历史数据失败'
            }), 500
        
        return jsonify({
            'success': True,
            'device_id': device_id,
            'data': result['data'],
            'pagination': {
                'page': result['page'],
                'page_size': result['page_size'],
                'total': result['total'],
                'total_pages': result['total_pages']
            }
        }), 200
        
    except ValueError as e:
        current_app.logger.error(f"参数错误: {e}")
        return jsonify({
            'success': False,
            'error': '参数错误',
            'message': str(e)
        }), 400
    except Exception as e:
        current_app.logger.error(f"获取设备历史数据失败: {e}")
        return jsonify({
            'success': False,
            'error': '获取设备历史数据失败',
            'message': str(e)
        }), 500


@api_bp.route('/energy/summary', methods=['GET'])
@login_required
def get_energy_summary():
    """
    获取能耗汇总统计
    返回按设备、按时间段的能耗聚合数据
    
    查询参数:
        - start_time: 开始时间 (ISO格式，可选)
        - end_time: 结束时间 (ISO格式，可选)
        - device_id: 设备ID (可选，不指定则返回所有设备)
        - aggregate: 聚合类型 (avg, sum, max, min，默认sum)
        - interval: 聚合时间间隔 (hour, day, week，可选)
    """
    try:
        current_app.logger.info("API: 获取能耗汇总")
        
        # 获取查询参数
        start_time_str = request.args.get('start_time')
        end_time_str = request.args.get('end_time')
        device_id = request.args.get('device_id')
        aggregate = request.args.get('aggregate', 'sum')
        interval = request.args.get('interval')
        
        # 验证聚合类型
        valid_aggregates = ['avg', 'sum', 'max', 'min', 'count']
        if aggregate not in valid_aggregates:
            return jsonify({
                'success': False,
                'error': '无效的聚合类型',
                'message': f'聚合类型必须是以下之一: {", ".join(valid_aggregates)}'
            }), 400
        
        # 验证时间间隔
        if interval and interval not in ['hour', 'day', 'week']:
            return jsonify({
                'success': False,
                'error': '无效的时间间隔',
                'message': '时间间隔必须是: hour, day, week'
            }), 400
        
        # 解析时间参数
        from datetime import datetime, timedelta
        start_time = None
        end_time = None
        
        if start_time_str:
            try:
                start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': '无效的开始时间格式'
                }), 400
        
        if end_time_str:
            try:
                end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': '无效的结束时间格式'
                }), 400
        
        # 如果没有指定时间范围，默认查询最近24小时
        if not start_time and not end_time:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=24)
        
        db_manager = current_app.db_manager
        
        # 如果指定了时间间隔，使用聚合查询
        if interval:
            result = db_manager.query_history(
                table_name='energy_data',
                start_time=start_time,
                end_time=end_time,
                device_id=device_id,
                aggregate=aggregate,
                aggregate_interval=interval
            )
            
            if result is None:
                return jsonify({
                    'success': False,
                    'error': '查询能耗数据失败'
                }), 500
            
            return jsonify({
                'success': True,
                'summary': {
                    'aggregate': result['aggregate'],
                    'interval': result['aggregate_interval'],
                    'data': result['data'],
                    'total_records': result['total']
                }
            }), 200
        
        # 否则，查询原始数据并计算汇总
        with db_manager.get_session() as session:
            from models import EnergyData
            from sqlalchemy import func
            
            # 构建查询
            query = session.query(
                EnergyData.device_id,
                func.sum(EnergyData.energy_kwh).label('total_energy'),
                func.avg(EnergyData.power_kw).label('avg_power'),
                func.max(EnergyData.power_kw).label('max_power'),
                func.min(EnergyData.power_kw).label('min_power'),
                func.count(EnergyData.id).label('record_count')
            )
            
            # 时间范围过滤
            if start_time:
                query = query.filter(EnergyData.timestamp >= start_time)
            if end_time:
                query = query.filter(EnergyData.timestamp <= end_time)
            
            # 设备过滤
            if device_id:
                query = query.filter(EnergyData.device_id == device_id)
            
            # 按设备分组
            query = query.group_by(EnergyData.device_id)
            
            # 执行查询
            results = query.all()
            
            # 转换为字典列表
            summary_data = []
            total_energy = 0
            
            for row in results:
                device_summary = {
                    'device_id': row.device_id,
                    'total_energy_kwh': float(row.total_energy) if row.total_energy else 0,
                    'avg_power_kw': float(row.avg_power) if row.avg_power else 0,
                    'max_power_kw': float(row.max_power) if row.max_power else 0,
                    'min_power_kw': float(row.min_power) if row.min_power else 0,
                    'record_count': row.record_count
                }
                summary_data.append(device_summary)
                total_energy += device_summary['total_energy_kwh']
            
            # 计算能耗趋势（同比、环比）
            trends = {}
            if start_time and end_time:
                time_diff = end_time - start_time
                
                # 计算环比（上一个相同时间段）
                prev_start = start_time - time_diff
                prev_end = start_time
                
                prev_query = session.query(
                    func.sum(EnergyData.energy_kwh).label('prev_total_energy')
                ).filter(
                    EnergyData.timestamp >= prev_start,
                    EnergyData.timestamp < prev_end
                )
                
                if device_id:
                    prev_query = prev_query.filter(EnergyData.device_id == device_id)
                
                prev_result = prev_query.first()
                prev_total = float(prev_result.prev_total_energy) if prev_result.prev_total_energy else 0
                
                if prev_total > 0:
                    change_percentage = ((total_energy - prev_total) / prev_total) * 100
                    trends['period_over_period'] = {
                        'current': total_energy,
                        'previous': prev_total,
                        'change_percentage': round(change_percentage, 2)
                    }
            
            # 查询趋势数据（用于图表显示）
            trend_data = []
            if start_time and end_time:
                # 查询所有设备的时序数据
                trend_query = session.query(EnergyData).filter(
                    EnergyData.timestamp >= start_time,
                    EnergyData.timestamp <= end_time
                ).order_by(EnergyData.timestamp)
                
                if device_id:
                    trend_query = trend_query.filter(EnergyData.device_id == device_id)
                
                trend_records = trend_query.all()
                
                # 按时间戳分组数据
                from collections import defaultdict
                time_grouped = defaultdict(dict)
                
                for record in trend_records:
                    timestamp_key = record.timestamp.isoformat()
                    time_grouped[timestamp_key][record.device_id] = record.power_kw
                
                # 转换为趋势数据格式
                for timestamp_key, devices in sorted(time_grouped.items()):
                    trend_point = {
                        'timestamp': timestamp_key,
                        'conveyor': devices.get('conveyor', 0),
                        'station1': devices.get('station1', 0),
                        'station2': devices.get('station2', 0)
                    }
                    trend_data.append(trend_point)
            
            return jsonify({
                'success': True,
                'summary': {
                    'time_range': {
                        'start': start_time.isoformat() if start_time else None,
                        'end': end_time.isoformat() if end_time else None
                    },
                    'total_energy_kwh': round(total_energy, 3),
                    'devices': summary_data,
                    'trends': trends
                },
                'trend': trend_data
            }), 200
            
    except Exception as e:
        current_app.logger.error(f"获取能耗汇总失败: {e}")
        return jsonify({
            'success': False,
            'error': '获取能耗汇总失败',
            'message': str(e)
        }), 500


@api_bp.route('/oee', methods=['GET'])
@login_required
def get_oee():
    """
    获取OEE数据
    返回设备综合效率计算结果
    
    查询参数:
        - start_time: 开始时间 (ISO格式，可选)
        - end_time: 结束时间 (ISO格式，可选)
        - dimension: 统计维度 (day, week, month，默认day)
        - page: 页码 (默认1)
        - page_size: 每页记录数 (默认100)
    """
    try:
        current_app.logger.info("API: 获取OEE数据")
        
        # 获取查询参数
        start_time_str = request.args.get('start_time')
        end_time_str = request.args.get('end_time')
        dimension = request.args.get('dimension', 'day')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 100))
        
        # 验证维度参数
        if dimension not in ['day', 'week', 'month']:
            return jsonify({
                'success': False,
                'error': '无效的统计维度',
                'message': '统计维度必须是: day, week, month'
            }), 400
        
        # 验证分页参数
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 1000:
            page_size = 100
        
        # 解析时间参数
        from datetime import datetime, timedelta
        start_time = None
        end_time = None
        
        if start_time_str:
            try:
                start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': '无效的开始时间格式'
                }), 400
        
        if end_time_str:
            try:
                end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': '无效的结束时间格式'
                }), 400
        
        # 如果没有指定时间范围，默认查询最近7天
        if not start_time and not end_time:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=7)
        
        db_manager = current_app.db_manager
        
        with db_manager.get_session() as session:
            from models import ProductionData
            from sqlalchemy import func
            
            # 构建基础查询
            query = session.query(ProductionData)
            
            # 时间范围过滤
            if start_time:
                query = query.filter(ProductionData.timestamp >= start_time)
            if end_time:
                query = query.filter(ProductionData.timestamp <= end_time)
            
            # 根据维度进行聚合
            if dimension == 'day':
                time_group = func.date_format(ProductionData.timestamp, '%Y-%m-%d')
            elif dimension == 'week':
                time_group = func.date_format(ProductionData.timestamp, '%Y-%u')
            elif dimension == 'month':
                time_group = func.date_format(ProductionData.timestamp, '%Y-%m')
            
            # 聚合查询
            agg_query = session.query(
                time_group.label('period'),
                func.avg(ProductionData.oee_percentage).label('avg_oee'),
                func.avg(ProductionData.availability).label('avg_availability'),
                func.avg(ProductionData.performance).label('avg_performance'),
                func.avg(ProductionData.quality).label('avg_quality'),
                func.sum(ProductionData.product_count).label('total_products'),
                func.sum(ProductionData.reject_count).label('total_rejects'),
                func.sum(ProductionData.runtime_seconds).label('total_runtime'),
                func.sum(ProductionData.downtime_seconds).label('total_downtime')
            )
            
            # 应用时间过滤
            if start_time:
                agg_query = agg_query.filter(ProductionData.timestamp >= start_time)
            if end_time:
                agg_query = agg_query.filter(ProductionData.timestamp <= end_time)
            
            # 分组和排序
            agg_query = agg_query.group_by(time_group).order_by(time_group.desc())
            
            # 获取总记录数
            total = agg_query.count()
            
            # 分页
            offset = (page - 1) * page_size
            agg_query = agg_query.limit(page_size).offset(offset)
            
            # 执行查询
            results = agg_query.all()
            
            # 转换为字典列表
            oee_data = []
            for row in results:
                oee_record = {
                    'period': row.period,
                    'oee_percentage': round(float(row.avg_oee), 2) if row.avg_oee else 0,
                    'availability': round(float(row.avg_availability), 2) if row.avg_availability else 0,
                    'performance': round(float(row.avg_performance), 2) if row.avg_performance else 0,
                    'quality': round(float(row.avg_quality), 2) if row.avg_quality else 0,
                    'total_products': row.total_products or 0,
                    'total_rejects': row.total_rejects or 0,
                    'total_runtime_hours': round((row.total_runtime or 0) / 3600, 2),
                    'total_downtime_hours': round((row.total_downtime or 0) / 3600, 2)
                }
                oee_data.append(oee_record)
            
            # 计算总体统计
            overall_query = session.query(
                func.avg(ProductionData.oee_percentage).label('overall_oee'),
                func.avg(ProductionData.availability).label('overall_availability'),
                func.avg(ProductionData.performance).label('overall_performance'),
                func.avg(ProductionData.quality).label('overall_quality')
            )
            
            if start_time:
                overall_query = overall_query.filter(ProductionData.timestamp >= start_time)
            if end_time:
                overall_query = overall_query.filter(ProductionData.timestamp <= end_time)
            
            overall = overall_query.first()
            
            overall_stats = {
                'oee_percentage': round(float(overall.overall_oee), 2) if overall.overall_oee else 0,
                'availability': round(float(overall.overall_availability), 2) if overall.overall_availability else 0,
                'performance': round(float(overall.overall_performance), 2) if overall.overall_performance else 0,
                'quality': round(float(overall.overall_quality), 2) if overall.overall_quality else 0
            }
            
            # 计算总页数
            total_pages = (total + page_size - 1) // page_size
            
            return jsonify({
                'success': True,
                'oee': {
                    'dimension': dimension,
                    'time_range': {
                        'start': start_time.isoformat() if start_time else None,
                        'end': end_time.isoformat() if end_time else None
                    },
                    'overall': overall_stats,
                    'data': oee_data,
                    'pagination': {
                        'page': page,
                        'page_size': page_size,
                        'total': total,
                        'total_pages': total_pages
                    }
                }
            }), 200
            
    except Exception as e:
        current_app.logger.error(f"获取OEE数据失败: {e}")
        return jsonify({
            'success': False,
            'error': '获取OEE数据失败',
            'message': str(e)
        }), 500


@api_bp.route('/alarms', methods=['GET'])
@login_required
def get_alarms():
    """
    获取报警列表
    支持分页和过滤
    
    查询参数:
        - device_id: 设备ID (可选)
        - alarm_level: 报警级别 (warning, critical, emergency，可选)
        - acknowledged: 是否已确认 (true, false，可选)
        - start_time: 开始时间 (ISO格式，可选)
        - end_time: 结束时间 (ISO格式，可选)
        - page: 页码 (默认1)
        - page_size: 每页记录数 (默认50)
    """
    try:
        current_app.logger.info("API: 获取报警列表")
        
        # 获取查询参数
        device_id = request.args.get('device_id')
        alarm_level = request.args.get('alarm_level')
        acknowledged_str = request.args.get('acknowledged')
        start_time_str = request.args.get('start_time')
        end_time_str = request.args.get('end_time')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 50))
        
        # 验证分页参数
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 500:
            page_size = 50
        
        # 验证报警级别
        if alarm_level and alarm_level not in ['warning', 'critical', 'emergency']:
            return jsonify({
                'success': False,
                'error': '无效的报警级别',
                'message': '报警级别必须是: warning, critical, emergency'
            }), 400
        
        # 解析acknowledged参数
        acknowledged = None
        if acknowledged_str:
            if acknowledged_str.lower() == 'true':
                acknowledged = True
            elif acknowledged_str.lower() == 'false':
                acknowledged = False
        
        # 解析时间参数
        from datetime import datetime
        start_time = None
        end_time = None
        
        if start_time_str:
            try:
                start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': '无效的开始时间格式'
                }), 400
        
        if end_time_str:
            try:
                end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': '无效的结束时间格式'
                }), 400
        
        db_manager = current_app.db_manager
        
        with db_manager.get_session() as session:
            from models import Alarm
            from sqlalchemy import func
            
            # 构建查询
            query = session.query(Alarm)
            
            # 应用过滤条件
            if device_id:
                query = query.filter(Alarm.device_id == device_id)
            if alarm_level:
                query = query.filter(Alarm.alarm_level == alarm_level)
            if acknowledged is not None:
                query = query.filter(Alarm.acknowledged == acknowledged)
            if start_time:
                query = query.filter(Alarm.timestamp >= start_time)
            if end_time:
                query = query.filter(Alarm.timestamp <= end_time)
            
            # 获取总记录数
            total = query.count()
            
            # 排序和分页
            query = query.order_by(Alarm.timestamp.desc())
            offset = (page - 1) * page_size
            query = query.limit(page_size).offset(offset)
            
            # 执行查询
            alarms = query.all()
            
            # 转换为字典列表
            alarm_list = [alarm.to_dict() for alarm in alarms]
            
            # 获取报警统计（按级别）
            stats_query = session.query(
                Alarm.alarm_level,
                func.count(Alarm.id).label('count')
            )
            
            # 应用相同的过滤条件（除了alarm_level）
            if device_id:
                stats_query = stats_query.filter(Alarm.device_id == device_id)
            if acknowledged is not None:
                stats_query = stats_query.filter(Alarm.acknowledged == acknowledged)
            if start_time:
                stats_query = stats_query.filter(Alarm.timestamp >= start_time)
            if end_time:
                stats_query = stats_query.filter(Alarm.timestamp <= end_time)
            
            stats_query = stats_query.group_by(Alarm.alarm_level)
            stats_results = stats_query.all()
            
            # 转换统计结果
            stats_by_level = {row.alarm_level: row.count for row in stats_results}
            
            # 按设备统计
            device_stats_query = session.query(
                Alarm.device_id,
                func.count(Alarm.id).label('count')
            )
            
            if alarm_level:
                device_stats_query = device_stats_query.filter(Alarm.alarm_level == alarm_level)
            if acknowledged is not None:
                device_stats_query = device_stats_query.filter(Alarm.acknowledged == acknowledged)
            if start_time:
                device_stats_query = device_stats_query.filter(Alarm.timestamp >= start_time)
            if end_time:
                device_stats_query = device_stats_query.filter(Alarm.timestamp <= end_time)
            
            device_stats_query = device_stats_query.group_by(Alarm.device_id)
            device_stats_results = device_stats_query.all()
            
            stats_by_device = {row.device_id: row.count for row in device_stats_results}
            
            # 计算总页数
            total_pages = (total + page_size - 1) // page_size
            
            return jsonify({
                'success': True,
                'alarms': alarm_list,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total': total,
                    'total_pages': total_pages
                },
                'statistics': {
                    'by_level': stats_by_level,
                    'by_device': stats_by_device
                }
            }), 200
            
    except Exception as e:
        current_app.logger.error(f"获取报警列表失败: {e}")
        return jsonify({
            'success': False,
            'error': '获取报警列表失败',
            'message': str(e)
        }), 500


@api_bp.route('/alarms/<int:alarm_id>/acknowledge', methods=['POST'])
@login_required
def acknowledge_alarm(alarm_id):
    """
    确认报警
    标记报警为已确认状态
    """
    try:
        current_app.logger.info(f"API: 确认报警 - {alarm_id}")
        
        # 获取当前用户信息
        from flask import session
        username = session.get('username', 'unknown')
        
        db_manager = current_app.db_manager
        
        with db_manager.get_session() as db_session:
            from models import Alarm
            from datetime import datetime
            
            # 查询报警记录
            alarm = db_session.query(Alarm).filter(Alarm.id == alarm_id).first()
            
            if not alarm:
                return jsonify({
                    'success': False,
                    'error': '报警不存在',
                    'message': f'未找到ID为 {alarm_id} 的报警记录'
                }), 404
            
            # 检查是否已确认
            if alarm.acknowledged:
                return jsonify({
                    'success': False,
                    'error': '报警已确认',
                    'message': f'该报警已于 {alarm.acknowledged_at.isoformat()} 被 {alarm.acknowledged_by} 确认'
                }), 400
            
            # 更新报警状态
            alarm.acknowledged = True
            alarm.acknowledged_by = username
            alarm.acknowledged_at = datetime.utcnow()
            
            db_session.commit()
            
            current_app.logger.info(f"报警 {alarm_id} 已被用户 {username} 确认")
            
            return jsonify({
                'success': True,
                'message': '报警已确认',
                'alarm': alarm.to_dict()
            }), 200
            
    except Exception as e:
        current_app.logger.error(f"确认报警失败: {e}")
        return jsonify({
            'success': False,
            'error': '确认报警失败',
            'message': str(e)
        }), 500


@api_bp.route('/thresholds', methods=['GET'])
@login_required
def get_thresholds():
    """
    获取阈值配置
    返回所有设备的阈值设置
    
    查询参数:
        - device_id: 设备ID (可选)
        - enabled: 是否启用 (true, false，可选)
    """
    try:
        current_app.logger.info("API: 获取阈值配置")
        
        # 获取查询参数
        device_id = request.args.get('device_id')
        enabled_str = request.args.get('enabled')
        
        # 解析enabled参数
        enabled = None
        if enabled_str:
            if enabled_str.lower() == 'true':
                enabled = True
            elif enabled_str.lower() == 'false':
                enabled = False
        
        db_manager = current_app.db_manager
        
        with db_manager.get_session() as session:
            from models import Threshold
            
            # 构建查询
            query = session.query(Threshold)
            
            # 应用过滤条件
            if device_id:
                query = query.filter(Threshold.device_id == device_id)
            if enabled is not None:
                query = query.filter(Threshold.enabled == enabled)
            
            # 排序
            query = query.order_by(Threshold.device_id, Threshold.parameter_name)
            
            # 执行查询
            thresholds = query.all()
            
            # 转换为字典列表
            threshold_list = [threshold.to_dict() for threshold in thresholds]
            
            return jsonify({
                'success': True,
                'thresholds': threshold_list,
                'total': len(threshold_list)
            }), 200
            
    except Exception as e:
        current_app.logger.error(f"获取阈值配置失败: {e}")
        return jsonify({
            'success': False,
            'error': '获取阈值配置失败',
            'message': str(e)
        }), 500


@api_bp.route('/thresholds/<int:threshold_id>', methods=['PUT'])
@login_required
@admin_required
def update_threshold(threshold_id):
    """
    更新阈值配置
    仅管理员可以修改阈值
    
    请求体 (JSON):
        - threshold_value: 阈值 (必需)
        - alarm_level: 报警级别 (warning, critical, emergency，可选)
        - enabled: 是否启用 (true, false，可选)
    """
    try:
        current_app.logger.info(f"API: 更新阈值配置 - {threshold_id}")
        
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '缺少请求数据',
                'message': '请提供JSON格式的请求体'
            }), 400
        
        # 验证必需字段
        threshold_value = data.get('threshold_value')
        if threshold_value is None:
            return jsonify({
                'success': False,
                'error': '缺少必需字段',
                'message': 'threshold_value字段是必需的'
            }), 400
        
        # 验证阈值数值范围
        try:
            threshold_value = float(threshold_value)
            if threshold_value < 0:
                return jsonify({
                    'success': False,
                    'error': '无效的阈值',
                    'message': '阈值必须大于或等于0'
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': '无效的阈值格式',
                'message': '阈值必须是数字'
            }), 400
        
        # 验证报警级别
        alarm_level = data.get('alarm_level')
        if alarm_level and alarm_level not in ['warning', 'critical', 'emergency']:
            return jsonify({
                'success': False,
                'error': '无效的报警级别',
                'message': '报警级别必须是: warning, critical, emergency'
            }), 400
        
        # 获取当前用户信息
        from flask import session
        username = session.get('username', 'unknown')
        
        db_manager = current_app.db_manager
        
        with db_manager.get_session() as db_session:
            from models import Threshold
            from datetime import datetime
            
            # 查询阈值记录
            threshold = db_session.query(Threshold).filter(Threshold.id == threshold_id).first()
            
            if not threshold:
                return jsonify({
                    'success': False,
                    'error': '阈值不存在',
                    'message': f'未找到ID为 {threshold_id} 的阈值配置'
                }), 404
            
            # 更新阈值
            threshold.threshold_value = threshold_value
            if alarm_level:
                threshold.alarm_level = alarm_level
            if 'enabled' in data:
                threshold.enabled = bool(data['enabled'])
            
            threshold.updated_by = username
            threshold.updated_at = datetime.utcnow()
            
            db_session.commit()
            
            current_app.logger.info(
                f"阈值 {threshold_id} 已被用户 {username} 更新: "
                f"设备={threshold.device_id}, 参数={threshold.parameter_name}, 值={threshold_value}"
            )
            
            return jsonify({
                'success': True,
                'message': '阈值已更新',
                'threshold': threshold.to_dict()
            }), 200
            
    except Exception as e:
        current_app.logger.error(f"更新阈值配置失败: {e}")
        return jsonify({
            'success': False,
            'error': '更新阈值配置失败',
            'message': str(e)
        }), 500


@api_bp.route('/thresholds', methods=['POST'])
@login_required
@admin_required
def create_threshold():
    """
    创建新阈值配置
    仅管理员可以创建阈值
    
    请求体 (JSON):
        - device_id: 设备ID (必需)
        - parameter_name: 参数名称 (必需)
        - threshold_value: 阈值 (必需)
        - alarm_level: 报警级别 (warning, critical, emergency，默认warning)
        - enabled: 是否启用 (true, false，默认true)
    """
    try:
        current_app.logger.info("API: 创建阈值配置")
        
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '缺少请求数据',
                'message': '请提供JSON格式的请求体'
            }), 400
        
        # 验证必需字段
        device_id = data.get('device_id')
        parameter_name = data.get('parameter_name')
        threshold_value = data.get('threshold_value')
        
        if not device_id:
            return jsonify({
                'success': False,
                'error': '缺少必需字段',
                'message': 'device_id字段是必需的'
            }), 400
        
        if not parameter_name:
            return jsonify({
                'success': False,
                'error': '缺少必需字段',
                'message': 'parameter_name字段是必需的'
            }), 400
        
        if threshold_value is None:
            return jsonify({
                'success': False,
                'error': '缺少必需字段',
                'message': 'threshold_value字段是必需的'
            }), 400
        
        # 验证阈值数值范围
        try:
            threshold_value = float(threshold_value)
            if threshold_value < 0:
                return jsonify({
                    'success': False,
                    'error': '无效的阈值',
                    'message': '阈值必须大于或等于0'
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': '无效的阈值格式',
                'message': '阈值必须是数字'
            }), 400
        
        # 验证报警级别
        alarm_level = data.get('alarm_level', 'warning')
        if alarm_level not in ['warning', 'critical', 'emergency']:
            return jsonify({
                'success': False,
                'error': '无效的报警级别',
                'message': '报警级别必须是: warning, critical, emergency'
            }), 400
        
        # 获取enabled参数
        enabled = data.get('enabled', True)
        
        # 获取当前用户信息
        from flask import session
        username = session.get('username', 'unknown')
        
        db_manager = current_app.db_manager
        
        with db_manager.get_session() as db_session:
            from models import Threshold
            from datetime import datetime
            from sqlalchemy.exc import IntegrityError
            
            # 检查是否已存在相同的设备和参数组合
            existing = db_session.query(Threshold).filter(
                Threshold.device_id == device_id,
                Threshold.parameter_name == parameter_name
            ).first()
            
            if existing:
                return jsonify({
                    'success': False,
                    'error': '阈值已存在',
                    'message': f'设备 {device_id} 的参数 {parameter_name} 已存在阈值配置'
                }), 409
            
            # 创建新阈值
            new_threshold = Threshold(
                device_id=device_id,
                parameter_name=parameter_name,
                threshold_value=threshold_value,
                alarm_level=alarm_level,
                enabled=enabled,
                updated_by=username,
                updated_at=datetime.utcnow()
            )
            
            db_session.add(new_threshold)
            
            try:
                db_session.commit()
            except IntegrityError:
                db_session.rollback()
                return jsonify({
                    'success': False,
                    'error': '创建阈值失败',
                    'message': '数据库约束冲突，可能已存在相同的阈值配置'
                }), 409
            
            current_app.logger.info(
                f"阈值已被用户 {username} 创建: "
                f"设备={device_id}, 参数={parameter_name}, 值={threshold_value}"
            )
            
            return jsonify({
                'success': True,
                'message': '阈值已创建',
                'threshold': new_threshold.to_dict()
            }), 201
            
    except Exception as e:
        current_app.logger.error(f"创建阈值配置失败: {e}")
        return jsonify({
            'success': False,
            'error': '创建阈值配置失败',
            'message': str(e)
        }), 500
