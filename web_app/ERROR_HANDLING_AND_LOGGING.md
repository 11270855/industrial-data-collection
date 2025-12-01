# 错误处理和日志系统文档

## 概述

本文档描述了能源管理系统Web应用的错误处理和日志系统实现。

## 错误处理

### 全局错误处理器

系统实现了以下HTTP错误的全局处理器：

#### 1. 400 Bad Request - 错误的请求
- **触发条件**: 请求参数错误或格式不正确
- **API响应**: JSON格式，包含error、message、status字段
- **页面响应**: 渲染error.html模板

#### 2. 401 Unauthorized - 未授权
- **触发条件**: 用户未登录或会话过期
- **API响应**: JSON格式，提示需要登录
- **页面响应**: 渲染error.html模板，提示登录

#### 3. 403 Forbidden - 禁止访问
- **触发条件**: 用户权限不足
- **API响应**: JSON格式，提示权限不足
- **页面响应**: 渲染error.html模板

#### 4. 404 Not Found - 资源未找到
- **触发条件**: 请求的URL不存在
- **API响应**: JSON格式，提示资源不存在
- **页面响应**: 渲染error.html模板

#### 5. 405 Method Not Allowed - 方法不允许
- **触发条件**: 使用了不支持的HTTP方法
- **API响应**: JSON格式，提示方法不支持
- **页面响应**: 渲染error.html模板

#### 6. 500 Internal Server Error - 服务器内部错误
- **触发条件**: 服务器代码异常
- **API响应**: JSON格式，提示服务器错误
- **页面响应**: 渲染error.html模板
- **日志**: 记录完整的异常堆栈信息

#### 7. 503 Service Unavailable - 服务不可用
- **触发条件**: 服务暂时不可用（如数据库连接失败）
- **API响应**: JSON格式，提示服务不可用
- **页面响应**: 渲染error.html模板

#### 8. Exception - 通用异常处理
- **触发条件**: 所有未被捕获的异常
- **处理方式**: 记录完整异常信息，返回500错误

### API错误响应格式

所有API错误响应统一使用以下JSON格式：

```json
{
    "error": "错误类型",
    "message": "错误描述信息",
    "status": 错误状态码
}
```

### 错误检测机制

系统通过检查请求路径是否以`/api/`开头来判断是API请求还是页面请求：
- API请求：返回JSON格式错误
- 页面请求：渲染HTML错误页面

## 日志系统

### 日志配置

#### 日志级别
- **DEBUG**: 详细的调试信息
- **INFO**: 一般信息（默认级别）
- **WARNING**: 警告信息
- **ERROR**: 错误信息

#### 日志输出

系统配置了两个日志处理器：

1. **文件日志处理器 (RotatingFileHandler)**
   - 日志文件: `logs/web_app.log`
   - 最大文件大小: 10MB
   - 备份文件数: 5个
   - 编码: UTF-8
   - 格式: `时间 - 日志器名称 - [级别] - 文件名:行号 - 消息`

2. **控制台日志处理器 (StreamHandler)**
   - 输出到: stdout
   - 格式: `时间 - [级别] - 消息`

### 日志轮转

当日志文件达到10MB时，系统会自动：
1. 将当前日志文件重命名为 `web_app.log.1`
2. 创建新的 `web_app.log` 文件
3. 保留最近5个备份文件
4. 自动删除最旧的备份文件

### 日志记录内容

系统在以下关键操作时记录日志：

#### 应用启动
- 日志系统初始化信息
- 数据库连接状态
- 蓝图注册信息
- 错误处理器注册信息
- 应用配置信息

#### 错误处理
- 所有HTTP错误（400, 401, 403, 404, 405, 500, 503）
- 未捕获的异常（包含完整堆栈信息）

#### 数据库操作
- 连接成功/失败
- SQLAlchemy查询（如果启用SQLALCHEMY_ECHO）

#### 应用关闭
- 上下文清理信息
- 异常信息（如果有）

### 相关日志器

系统还配置了以下相关日志器：

1. **werkzeug**: Flask开发服务器日志（级别: WARNING）
2. **sqlalchemy.engine**: SQLAlchemy数据库引擎日志

### 配置参数

日志系统通过以下环境变量配置（在config.py中定义）：

```python
LOG_LEVEL = 'INFO'              # 日志级别
LOG_FILE = 'logs/web_app.log'  # 日志文件路径
LOG_MAX_BYTES = 10485760        # 最大文件大小（10MB）
LOG_BACKUP_COUNT = 5            # 备份文件数量
```

## 使用示例

### 在代码中记录日志

```python
from flask import current_app

# 记录不同级别的日志
current_app.logger.debug("调试信息")
current_app.logger.info("一般信息")
current_app.logger.warning("警告信息")
current_app.logger.error("错误信息")

# 记录异常信息（包含堆栈）
try:
    # 可能出错的代码
    pass
except Exception as e:
    current_app.logger.error(f"操作失败: {e}", exc_info=True)
```

### 触发错误处理

```python
from flask import abort

# 触发404错误
abort(404)

# 触发403错误
abort(403)

# 触发500错误
abort(500)
```

## 测试

运行测试文件验证错误处理和日志系统：

```bash
python -m pytest web_app/test_error_handling.py -v
```

## 维护建议

1. **定期检查日志文件**: 监控logs目录的磁盘使用情况
2. **调整日志级别**: 生产环境建议使用INFO或WARNING级别
3. **日志归档**: 定期归档或删除旧的日志备份文件
4. **监控错误**: 定期检查ERROR级别的日志，及时发现和解决问题
5. **性能优化**: 如果日志量很大，考虑使用异步日志处理

## 相关文件

- `web_app/app.py`: 错误处理和日志系统实现
- `web_app/config.py`: 日志配置参数
- `web_app/templates/error.html`: 错误页面模板
- `web_app/test_error_handling.py`: 测试文件
- `web_app/logs/`: 日志文件目录
