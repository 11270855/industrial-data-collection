"""
仪表盘路由模块
提供仪表盘页面和相关功能
"""

from flask import Blueprint, render_template, current_app
from .auth import login_required

# 创建仪表盘蓝图
dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    """
    仪表盘主页
    显示实时设备状态、能耗数据和报警信息
    """
    current_app.logger.info("访问仪表盘主页")
    return render_template('dashboard.html')


@dashboard_bp.route('/history')
@login_required
def history():
    """
    历史数据查询页面
    """
    current_app.logger.info("访问历史数据页面")
    # TODO: 在任务11中实现历史数据页面
    return render_template('history.html')


@dashboard_bp.route('/alarms')
@login_required
def alarms():
    """
    报警管理页面
    """
    current_app.logger.info("访问报警管理页面")
    # TODO: 在任务11中实现报警管理页面
    return render_template('alarms.html')


@dashboard_bp.route('/settings')
@login_required
def settings():
    """
    系统设置页面
    """
    current_app.logger.info("访问系统设置页面")
    # TODO: 在任务11中实现设置页面
    return render_template('settings.html')
