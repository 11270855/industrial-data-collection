# 能源管理系统 - 文档中心

本目录包含能源管理系统的所有文档。

## 📚 文档结构

```
docs/
├── README.md                    # 本文件 - 文档索引
├── KEPSERVER_SETUP.md          # KepServer配置指南
├── USER_MANUAL.md              # 用户操作手册
├── plc_program/                # PLC程序文档
├── python_client/              # Python客户端文档
└── web_app/                    # Web应用文档
```

---

## 🎯 快速导航

### 系统级文档

| 文档 | 说明 | 适用对象 |
|------|------|---------|
| [KepServer配置指南](KEPSERVER_SETUP.md) | 详细的KepServer配置步骤 | 系统管理员、部署人员 |
| [用户操作手册](USER_MANUAL.md) | 系统使用指南 | 所有用户 |

### PLC程序文档

位置：`docs/plc_program/`

| 文档 | 说明 |
|------|------|
| [README.md](plc_program/README.md) | PLC程序总览 |
| [QUICK_START.md](plc_program/QUICK_START.md) | 5分钟快速开始 |
| [PROJECT_SETUP.md](plc_program/PROJECT_SETUP.md) | CodeSys项目设置指南 |
| [IMPLEMENTATION_GUIDE.md](plc_program/IMPLEMENTATION_GUIDE.md) | 实现指南和变量映射 |
| [TASK_COMPLETION_SUMMARY.md](plc_program/TASK_COMPLETION_SUMMARY.md) | 任务完成总结 |

### Python客户端文档

位置：`docs/python_client/`

| 文档 | 说明 |
|------|------|
| [README.md](python_client/README.md) | Python客户端总览 |
| [QUICK_START.md](python_client/QUICK_START.md) | 快速开始指南 |
| [OPCUA_CLIENT_README.md](python_client/OPCUA_CLIENT_README.md) | OPC UA客户端使用说明 |
| [DATA_PROCESSOR_README.md](python_client/DATA_PROCESSOR_README.md) | 数据处理模块说明 |
| [DATA_COLLECTOR_README.md](python_client/DATA_COLLECTOR_README.md) | 数据采集程序说明 |
| [DATABASE_OPERATIONS_README.md](python_client/DATABASE_OPERATIONS_README.md) | 数据库操作说明 |
| [DATABASE_SETUP.md](python_client/DATABASE_SETUP.md) | 数据库设置指南 |
| [ALARM_HANDLER_README.md](python_client/ALARM_HANDLER_README.md) | 报警处理模块说明 |
| [TASK_5_COMPLETION_SUMMARY.md](python_client/TASK_5_COMPLETION_SUMMARY.md) | 任务5完成总结 |
| [TASK_6_COMPLETION_SUMMARY.md](python_client/TASK_6_COMPLETION_SUMMARY.md) | 任务6完成总结 |
| [TASK_8_COMPLETION_SUMMARY.md](python_client/TASK_8_COMPLETION_SUMMARY.md) | 任务8完成总结 |

### Web应用文档

位置：`docs/web_app/`

| 文档 | 说明 |
|------|------|
| [README.md](web_app/README.md) | Web应用总览 |
| [ERROR_HANDLING_AND_LOGGING.md](web_app/ERROR_HANDLING_AND_LOGGING.md) | 错误处理和日志说明 |
| [SECURITY.md](web_app/SECURITY.md) | 安全配置指南 |
| [API_IMPLEMENTATION_SUMMARY.md](web_app/API_IMPLEMENTATION_SUMMARY.md) | API实现总结 |
| [TEST_API_IMPLEMENTATION_SUMMARY.md](web_app/TEST_API_IMPLEMENTATION_SUMMARY.md) | API测试总结 |
| [环境问题解决方案.md](web_app/环境问题解决方案.md) | 环境问题解决方案 |
| [TASK_9_COMPLETION_SUMMARY.md](web_app/TASK_9_COMPLETION_SUMMARY.md) | 任务9完成总结 |
| [TASK_10_COMPLETION_SUMMARY.md](web_app/TASK_10_COMPLETION_SUMMARY.md) | 任务10完成总结 |
| [TASK_11_COMPLETION_SUMMARY.md](web_app/TASK_11_COMPLETION_SUMMARY.md) | 任务11完成总结 |

---

## 📖 按角色查找文档

### 系统管理员

1. [KepServer配置指南](KEPSERVER_SETUP.md) - 配置OPC UA通信
2. [PLC项目设置](plc_program/PROJECT_SETUP.md) - 部署PLC程序
3. [数据库设置](python_client/DATABASE_SETUP.md) - 初始化数据库
4. [安全配置](web_app/SECURITY.md) - 配置系统安全

### 开发人员

1. [PLC实现指南](plc_program/IMPLEMENTATION_GUIDE.md) - PLC开发参考
2. [OPC UA客户端](python_client/OPCUA_CLIENT_README.md) - OPC UA通信开发
3. [数据处理模块](python_client/DATA_PROCESSOR_README.md) - 数据处理开发
4. [API实现总结](web_app/API_IMPLEMENTATION_SUMMARY.md) - Web API开发

### 最终用户

1. [用户操作手册](USER_MANUAL.md) - 系统使用指南
2. [快速开始](python_client/QUICK_START.md) - 快速上手

### 运维人员

1. [数据采集程序](python_client/DATA_COLLECTOR_README.md) - 运行和监控
2. [错误处理和日志](web_app/ERROR_HANDLING_AND_LOGGING.md) - 故障排查
3. [数据库操作](python_client/DATABASE_OPERATIONS_README.md) - 数据库维护

---

## 🚀 快速开始路径

### 首次部署

1. [KepServer配置指南](KEPSERVER_SETUP.md)
2. [PLC快速开始](plc_program/QUICK_START.md)
3. [Python客户端快速开始](python_client/QUICK_START.md)
4. [用户操作手册](USER_MANUAL.md)

### 日常使用

1. [用户操作手册](USER_MANUAL.md)
2. [报警处理](python_client/ALARM_HANDLER_README.md)

### 故障排查

1. [错误处理和日志](web_app/ERROR_HANDLING_AND_LOGGING.md)
2. [环境问题解决方案](web_app/环境问题解决方案.md)
3. [KepServer配置指南 - 故障排查部分](KEPSERVER_SETUP.md#故障排查)

---

## 📝 文档更新记录

| 日期 | 更新内容 | 版本 |
|------|---------|------|
| 2025-12-01 | 创建文档中心，整理所有模块文档 | 1.0 |
| 2025-12-01 | 添加KepServer配置指南和用户手册 | 1.0 |

---

## 💡 文档贡献

如需更新文档，请：

1. 在对应模块目录下修改源文档
2. 将更新后的文档复制到docs目录
3. 更新本README.md的更新记录

---

**文档版本**：1.0  
**最后更新**：2025-12-01
