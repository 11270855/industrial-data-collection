"""
Flask Web应用入口
能源管理系统Web应用服务器
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, jsonify
from flask_cors import CORS

# 导入本地配置（在添加python_client到路径之前）
import config as web_config

# 添加python_client到路径，以便导入DatabaseManager
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python_client'))
from database import DatabaseManager


def create_app(config_object=None):
    """
    应用工厂函数
    
    Args:
        config_object: 配置类或对象，默认使用config.py中的WebConfig类
    
    Returns:
        Flask应用实例
    """
    # 加载配置
    if config_object is None:
        config_object = web_config.Config()
    elif isinstance(config_object, type):
        # 如果传入的是类，实例化它
        config_object = config_object()
    
    app = Flask(__name__,
                static_folder='static',
                template_folder='templates')
    
    # 手动加载配置（避免from_object对property的处理问题）
    for key in dir(config_object):
        if key.isupper():
            try:
                app.config[key] = getattr(config_object, key)
            except Exception as e:
                print(f"Warning: Could not set config key {key}: {e}")
    
    # 配置CORS
    cors_origins = app.config.get('CORS_ORIGINS', '*')
    CORS(app, origins=cors_origins)
    
    # 配置日志
    setup_logging(app)
    
    # 初始化数据库管理器
    app.logger.info("开始初始化数据库连接...")
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
    if not db_uri:
        app.logger.error("SQLALCHEMY_DATABASE_URI not found in config")
        app.logger.error(f"Available config keys: {list(app.config.keys())}")
        raise ValueError("Database URI not configured")
    
    app.logger.debug(f"数据库URI: {db_uri.split('@')[-1] if '@' in db_uri else db_uri}")  # 隐藏密码
    db_manager = DatabaseManager(db_uri)
    if not db_manager.connect():
        app.logger.error("数据库连接失败，请检查数据库配置和服务状态")
    else:
        app.logger.info("数据库连接成功")
    
    # 将数据库管理器存储到app上下文
    app.db_manager = db_manager
    
    # 注册蓝图
    app.logger.info("注册应用蓝图...")
    register_blueprints(app)
    
    # 注册错误处理器
    app.logger.info("注册错误处理器...")
    register_error_handlers(app)
    
    # 注册应用关闭处理
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        """应用上下文结束时清理资源"""
        if exception:
            app.logger.error(f"应用上下文异常: {exception}")
        if hasattr(app, 'db_manager'):
            # 注意：不要在这里断开连接，因为连接池会管理连接
            app.logger.debug("应用上下文清理完成")
    
    app.logger.info("=" * 60)
    app.logger.info("Flask应用初始化完成")
    app.logger.info(f"调试模式: {app.config['DEBUG']}")
    app.logger.info(f"数据库类型: {app.config.get('DB_TYPE', 'unknown')}")
    app.logger.info("=" * 60)
    
    return app


def setup_logging(app):
    """
    配置日志系统
    - 配置Web应用日志输出到文件和控制台
    - 使用RotatingFileHandler实现日志轮转
    - 配置不同级别的日志（DEBUG, INFO, WARNING, ERROR）
    - 确保logs目录存在
    
    Args:
        app: Flask应用实例
    """
    # 从app.config获取配置
    log_file = app.config.get('LOG_FILE', 'logs/web_app.log')
    log_level_str = app.config.get('LOG_LEVEL', 'INFO')
    log_max_bytes = app.config.get('LOG_MAX_BYTES', 10485760)  # 10MB
    log_backup_count = app.config.get('LOG_BACKUP_COUNT', 5)
    
    # 确保日志目录存在
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
        print(f"创建日志目录: {log_dir}")
    
    # 配置日志级别
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    
    # 清除现有的处理器（避免重复添加）
    app.logger.handlers.clear()
    
    # 配置文件日志处理器（带轮转）
    # 日志文件达到maxBytes时自动轮转，保留backupCount个备份
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=log_max_bytes,
        backupCount=log_backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    
    # 文件日志使用详细格式
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - [%(levelname)s] - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # 配置控制台日志处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # 控制台日志使用简洁格式
    console_formatter = logging.Formatter(
        '%(asctime)s - [%(levelname)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    
    # 添加处理器到应用日志器
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(log_level)
    
    # 配置其他相关日志器
    # Werkzeug日志（Flask开发服务器）
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.WARNING)
    werkzeug_logger.addHandler(file_handler)
    
    # SQLAlchemy日志
    sqlalchemy_logger = logging.getLogger('sqlalchemy.engine')
    if app.config.get('SQLALCHEMY_ECHO', False):
        sqlalchemy_logger.setLevel(logging.INFO)
    else:
        sqlalchemy_logger.setLevel(logging.WARNING)
    sqlalchemy_logger.addHandler(file_handler)
    
    # 记录日志系统初始化信息
    app.logger.info("=" * 60)
    app.logger.info("日志系统初始化完成")
    app.logger.info(f"日志级别: {log_level_str}")
    app.logger.info(f"日志文件: {log_file}")
    app.logger.info(f"日志轮转: {log_max_bytes / 1024 / 1024:.1f}MB, 保留{log_backup_count}个备份")
    app.logger.info("=" * 60)


def register_blueprints(app):
    """
    注册所有蓝图
    
    Args:
        app: Flask应用实例
    """
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.api import api_bp
    
    # 注册认证蓝图
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.logger.info("已注册认证蓝图: /auth")
    
    # 注册仪表盘蓝图
    app.register_blueprint(dashboard_bp, url_prefix='/')
    app.logger.info("已注册仪表盘蓝图: /")
    
    # 注册API蓝图
    app.register_blueprint(api_bp, url_prefix='/api')
    app.logger.info("已注册API蓝图: /api")


def register_error_handlers(app):
    """
    注册全局错误处理器
    
    Args:
        app: Flask应用实例
    """
    from flask import request
    
    def is_api_request():
        """判断是否为API请求"""
        return request.path.startswith('/api/')
    
    @app.errorhandler(400)
    def bad_request_error(error):
        """处理400错误 - 错误的请求"""
        app.logger.warning(f"错误的请求: {error}")
        if is_api_request():
            return jsonify({
                'error': 'Bad Request',
                'message': '请求参数错误',
                'status': 400
            }), 400
        return render_template('error.html', 
                             error_code=400, 
                             error_message='请求参数错误'), 400
    
    @app.errorhandler(401)
    def unauthorized_error(error):
        """处理401错误 - 未授权"""
        app.logger.warning(f"未授权访问: {error}")
        if is_api_request():
            return jsonify({
                'error': 'Unauthorized',
                'message': '未授权，请先登录',
                'status': 401
            }), 401
        return render_template('error.html', 
                             error_code=401, 
                             error_message='未授权，请先登录'), 401
    
    @app.errorhandler(403)
    def forbidden_error(error):
        """处理403错误 - 禁止访问"""
        app.logger.warning(f"禁止访问: {error}")
        if is_api_request():
            return jsonify({
                'error': 'Forbidden',
                'message': '没有权限访问此资源',
                'status': 403
            }), 403
        return render_template('error.html', 
                             error_code=403, 
                             error_message='没有权限访问'), 403
    
    @app.errorhandler(404)
    def not_found_error(error):
        """处理404错误 - 资源未找到"""
        app.logger.warning(f"资源未找到: {request.path}")
        if is_api_request():
            return jsonify({
                'error': 'Not Found',
                'message': '请求的资源不存在',
                'status': 404
            }), 404
        return render_template('error.html', 
                             error_code=404, 
                             error_message='页面未找到'), 404
    
    @app.errorhandler(405)
    def method_not_allowed_error(error):
        """处理405错误 - 方法不允许"""
        app.logger.warning(f"方法不允许: {request.method} {request.path}")
        if is_api_request():
            return jsonify({
                'error': 'Method Not Allowed',
                'message': '不支持的请求方法',
                'status': 405
            }), 405
        return render_template('error.html', 
                             error_code=405, 
                             error_message='不支持的请求方法'), 405
    
    @app.errorhandler(500)
    def internal_error(error):
        """处理500错误 - 服务器内部错误"""
        app.logger.error(f"服务器内部错误: {error}", exc_info=True)
        if is_api_request():
            return jsonify({
                'error': 'Internal Server Error',
                'message': '服务器内部错误，请稍后重试',
                'status': 500
            }), 500
        return render_template('error.html', 
                             error_code=500, 
                             error_message='服务器内部错误'), 500
    
    @app.errorhandler(503)
    def service_unavailable_error(error):
        """处理503错误 - 服务不可用"""
        app.logger.error(f"服务不可用: {error}")
        if is_api_request():
            return jsonify({
                'error': 'Service Unavailable',
                'message': '服务暂时不可用，请稍后重试',
                'status': 503
            }), 503
        return render_template('error.html', 
                             error_code=503, 
                             error_message='服务暂时不可用'), 503
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """处理所有未捕获的异常"""
        app.logger.error(f"未捕获的异常: {error}", exc_info=True)
        if is_api_request():
            return jsonify({
                'error': 'Internal Server Error',
                'message': '服务器发生错误',
                'status': 500
            }), 500
        return render_template('error.html', 
                             error_code=500, 
                             error_message='服务器发生错误'), 500


# 创建应用实例
app = create_app()


if __name__ == '__main__':
    # 开发环境运行
    host = '0.0.0.0'
    port = 5000
    debug = app.config['DEBUG']
    
    app.logger.info("=" * 60)
    app.logger.info("启动Flask开发服务器")
    app.logger.info(f"监听地址: {host}:{port}")
    app.logger.info(f"调试模式: {debug}")
    app.logger.info(f"访问地址: http://localhost:{port}")
    app.logger.info("=" * 60)
    
    try:
        app.run(
            host=host,
            port=port,
            debug=debug
        )
    except Exception as e:
        app.logger.error(f"服务器启动失败: {e}", exc_info=True)
        raise
