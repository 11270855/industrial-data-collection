"""
用户认证路由模块
实现登录、登出、会话管理和权限控制
"""

import sys
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template, current_app

# 添加python_client到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'python_client'))
from models import User

# 创建认证蓝图
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    用户登录路由
    GET: 显示登录页面
    POST: 处理登录请求，验证用户名和密码
    """
    if request.method == 'GET':
        # 如果已登录，重定向到仪表盘
        if 'user_id' in session:
            return redirect(url_for('dashboard.index'))
        return render_template('login.html')
    
    # POST请求：处理登录
    try:
        data = request.get_json() if request.is_json else request.form
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        # 验证输入
        if not username or not password:
            return jsonify({
                'success': False,
                'message': '用户名和密码不能为空'
            }), 400
        
        # 查询用户
        db_manager = current_app.db_manager
        with db_manager.get_session() as db_session:
            user = db_session.query(User).filter(User.username == username).first()
            
            if not user:
                current_app.logger.warning(f"登录失败：用户不存在 - {username}")
                return jsonify({
                    'success': False,
                    'message': '用户名或密码错误'
                }), 401
            
            # 检查账户是否被锁定
            if user.is_locked():
                locked_until = user.locked_until.strftime('%Y-%m-%d %H:%M:%S')
                current_app.logger.warning(f"登录失败：账户已锁定 - {username}，锁定至 {locked_until}")
                return jsonify({
                    'success': False,
                    'message': f'账户已被锁定，请在 {locked_until} 后重试'
                }), 403
            
            # 验证密码
            if not user.check_password(password):
                # 增加失败计数
                user.failed_login_attempts += 1
                
                # 检查是否需要锁定账户
                max_attempts = current_app.config.get('MAX_LOGIN_ATTEMPTS', 3)
                if user.failed_login_attempts >= max_attempts:
                    lock_duration = current_app.config.get('ACCOUNT_LOCK_DURATION', 600)
                    user.locked_until = datetime.utcnow() + timedelta(seconds=lock_duration)
                    db_session.commit()
                    
                    current_app.logger.warning(
                        f"账户已锁定：{username}，失败次数：{user.failed_login_attempts}"
                    )
                    return jsonify({
                        'success': False,
                        'message': f'登录失败次数过多，账户已被锁定 {lock_duration // 60} 分钟'
                    }), 403
                
                db_session.commit()
                remaining_attempts = max_attempts - user.failed_login_attempts
                current_app.logger.warning(
                    f"登录失败：密码错误 - {username}，剩余尝试次数：{remaining_attempts}"
                )
                return jsonify({
                    'success': False,
                    'message': f'用户名或密码错误，剩余尝试次数：{remaining_attempts}'
                }), 401
            
            # 登录成功
            # 重置失败计数和锁定状态
            user.failed_login_attempts = 0
            user.locked_until = None
            user.last_login = datetime.utcnow()
            db_session.commit()
            
            # 设置会话
            session.clear()
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['login_time'] = datetime.utcnow().isoformat()
            session.permanent = True  # 使用PERMANENT_SESSION_LIFETIME配置
            
            current_app.logger.info(f"用户登录成功：{username}，角色：{user.role}")
            
            return jsonify({
                'success': True,
                'message': '登录成功',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'role': user.role
                },
                'redirect': url_for('dashboard.index')
            }), 200
    
    except Exception as e:
        current_app.logger.error(f"登录处理错误: {e}")
        return jsonify({
            'success': False,
            'message': '登录处理失败，请稍后重试'
        }), 500


@auth_bp.route('/logout', methods=['POST', 'GET'])
def logout():
    """
    用户登出路由
    清除会话并重定向到登录页面
    """
    username = session.get('username', 'Unknown')
    session.clear()
    current_app.logger.info(f"用户登出：{username}")
    
    if request.is_json:
        return jsonify({
            'success': True,
            'message': '登出成功',
            'redirect': url_for('auth.login')
        }), 200
    else:
        return redirect(url_for('auth.login'))


@auth_bp.route('/check', methods=['GET'])
def check_session():
    """
    检查会话状态
    用于前端验证用户是否已登录
    """
    if 'user_id' not in session:
        return jsonify({
            'authenticated': False,
            'message': '未登录'
        }), 401
    
    # 检查会话超时（30分钟无操作）
    login_time_str = session.get('login_time')
    if login_time_str:
        login_time = datetime.fromisoformat(login_time_str)
        session_lifetime = current_app.config.get('PERMANENT_SESSION_LIFETIME', 1800)
        if (datetime.utcnow() - login_time).total_seconds() > session_lifetime:
            session.clear()
            return jsonify({
                'authenticated': False,
                'message': '会话已超时，请重新登录'
            }), 401
    
    return jsonify({
        'authenticated': True,
        'user': {
            'id': session.get('user_id'),
            'username': session.get('username'),
            'role': session.get('role')
        }
    }), 200


@auth_bp.before_app_request
def update_session_activity():
    """
    在每次请求前更新会话活动时间
    实现30分钟无操作自动登出
    """
    if 'user_id' in session:
        # 更新最后活动时间
        session['last_activity'] = datetime.utcnow().isoformat()


def login_required(f):
    """
    登录验证装饰器
    要求用户必须登录才能访问被装饰的路由
    
    使用示例:
        @app.route('/protected')
        @login_required
        def protected_route():
            return "This is protected"
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            current_app.logger.warning(f"未授权访问: {request.path}")
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({
                    'error': 'Unauthorized',
                    'message': '未授权，请先登录'
                }), 401
            return redirect(url_for('auth.login'))
        
        # 检查会话超时
        last_activity_str = session.get('last_activity')
        if last_activity_str:
            last_activity = datetime.fromisoformat(last_activity_str)
            session_lifetime = current_app.config.get('PERMANENT_SESSION_LIFETIME', 1800)
            if (datetime.utcnow() - last_activity).total_seconds() > session_lifetime:
                session.clear()
                current_app.logger.info(f"会话超时，用户已登出")
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({
                        'error': 'Session Timeout',
                        'message': '会话已超时，请重新登录'
                    }), 401
                return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    
    return decorated_function


def admin_required(f):
    """
    管理员权限验证装饰器
    要求用户必须是管理员才能访问被装饰的路由
    
    使用示例:
        @app.route('/admin/settings')
        @login_required
        @admin_required
        def admin_settings():
            return "Admin only"
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            current_app.logger.warning(f"未授权访问: {request.path}")
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({
                    'error': 'Unauthorized',
                    'message': '未授权，请先登录'
                }), 401
            return redirect(url_for('auth.login'))
        
        # 检查用户角色
        user_role = session.get('role')
        if user_role != 'admin':
            current_app.logger.warning(
                f"权限不足: 用户 {session.get('username')} 尝试访问管理员功能 {request.path}"
            )
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({
                    'error': 'Forbidden',
                    'message': '权限不足，需要管理员权限'
                }), 403
            return render_template('error.html', 
                                 error_code=403, 
                                 error_message='权限不足，需要管理员权限'), 403
        
        return f(*args, **kwargs)
    
    return decorated_function


def role_required(required_role):
    """
    角色验证装饰器工厂
    要求用户具有指定角色才能访问被装饰的路由
    
    Args:
        required_role: 所需的角色名称
    
    使用示例:
        @app.route('/manager/dashboard')
        @login_required
        @role_required('manager')
        def manager_dashboard():
            return "Manager only"
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({
                        'error': 'Unauthorized',
                        'message': '未授权，请先登录'
                    }), 401
                return redirect(url_for('auth.login'))
            
            user_role = session.get('role')
            if user_role != required_role:
                current_app.logger.warning(
                    f"权限不足: 用户 {session.get('username')} (角色: {user_role}) "
                    f"尝试访问需要 {required_role} 角色的功能 {request.path}"
                )
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({
                        'error': 'Forbidden',
                        'message': f'权限不足，需要 {required_role} 角色'
                    }), 403
                return render_template('error.html', 
                                     error_code=403, 
                                     error_message=f'权限不足，需要 {required_role} 角色'), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator
