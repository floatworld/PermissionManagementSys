# 斯能服务器管理系统 - 服务器端部署文档

## 📋 系统概述

本系统为斯能服务器管理系统的服务器端（下位机），提供目录权限管理、用户管理、审计日志等核心功能。

- **系统名称**: 斯能服务器管理系统 (Server)
- **版本**: 2.0.0
- **部署目标**: 192.168.110.77
- **端口**: 5000
- **协议**: HTTP/JSON

## 🏗️ 系统架构

```
┌─────────────────────────────────────────┐
│         上位机 (PyQt5 Client)           │
│    UIManagement/permission_manager.py   │
└─────────────────┬───────────────────────┘
                  │ HTTP/JSON
                  │ 192.168.110.77:5000
┌─────────────────▼───────────────────────┐
│         下位机 (Flask Server)           │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │  API Layer (api.py)                │ │
│  │  - 目录管理 /api/directory/*       │ │
│  │  - 权限管理 /api/permissions/*     │ │
│  │  - 审计日志 /api/audit/*           │ │
│  └────────────┬───────────────────────┘ │
│               │                          │
│  ┌────────────▼───────────────────────┐ │
│  │  Service Layer (services.py)       │ │
│  │  - DirectoryService                │ │
│  │  - PermissionService               │ │
│  │  - AuditService                    │ │
│  └────────────┬───────────────────────┘ │
│               │                          │
│  ┌────────────▼───────────────────────┐ │
│  │  DAO Layer (dao.py)                │ │
│  │  - UserDAO                         │ │
│  │  - DirectoryDAO                    │ │
│  │  - PermissionDAO                   │ │
│  │  - AuditDAO                        │ │
│  └────────────┬───────────────────────┘ │
│               │                          │
│  ┌────────────▼───────────────────────┐ │
│  │  Database Layer (database.py)      │ │
│  │  - SQLite: server_data.db          │ │
│  │  - 4 Tables + Indexes              │ │
│  └────────────────────────────────────┘ │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │  File Monitor (file_monitor.py)    │ │
│  │  - Watchdog 实时文件监控           │ │
│  └────────────────────────────────────┘ │
└──────────────────────────────────────────┘
```

## 📦 文件结构

```
Server/
├── database.py         # 数据库层 - SQLite管理
├── dao.py             # 数据访问层 - CRUD操作
├── services.py        # 服务层 - 业务逻辑
├── api.py             # API路由层 - Flask接口
├── file_monitor.py    # 文件监控 - Watchdog
├── start_server.py    # 启动脚本
├── start.bat          # Windows启动批处理
├── requirements.txt   # Python依赖
├── README.md          # 部署文档
└── server_data.db     # SQLite数据库（自动创建）
```

## 🔧 环境要求

### Python版本
- Python 3.8+

### 依赖包
```
flask>=2.3.0
flask-cors>=4.0.0
pywin32>=305
watchdog>=3.0.0
```

### 操作系统
- Windows Server 2016+
- Windows 10+

## 🚀 部署步骤

### 1. 拷贝文件到目标机器

将整个 `Server/` 目录拷贝到 **192.168.110.77** 的任意位置，例如：
```
D:\Applications\PermissionManagementSys\Server\
```

### 2. 安装Python依赖

在目标机器上打开命令提示符，进入Server目录：

```powershell
cd D:\Applications\PermissionManagementSys\Server
pip install -r requirements.txt
```

或者使用国内镜像加速：

```powershell
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. 启动服务器

#### 方法1: 使用批处理文件（推荐）
双击 `start.bat` 即可启动

#### 方法2: 命令行启动
```powershell
python start_server.py
```

### 4. 验证服务

服务启动后，访问以下地址验证：

- **健康检查**: http://192.168.110.77:5000/health
- **系统信息**: http://192.168.110.77:5000/api/info
- **权限列表**: http://192.168.110.77:5000/api/permissions

预期返回：
```json
{
  "status": "ok",
  "timestamp": "2024-10-22T15:30:00.123456",
  "service": "斯能服务器管理系统"
}
```

## 📡 API接口文档

### 目录管理

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/directory/structure` | GET | 获取目录树结构 |
| `/api/directory/scan` | POST | 扫描并同步目录 |
| `/api/directory/tree` | POST | 扫描目录树（不写数据库） |

**示例 - 扫描目录:**
```json
POST /api/directory/scan
{
  "path": "C:\\SharedFolders",
  "is_shared": true
}
```

### 权限管理

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/permissions` | GET | 获取所有权限 |
| `/api/permissions/user/<username>` | GET | 获取用户权限 |
| `/api/permissions/directory` | POST | 获取目录权限 |
| `/api/permissions/grant` | POST | 授予权限 |
| `/api/permissions/revoke` | POST | 撤销权限 |
| `/api/permissions/check` | POST | 检查权限 |

**示例 - 授予权限:**
```json
POST /api/permissions/grant
{
  "username": "zhangsan",
  "directory_path": "C:\\SharedFolders\\Project",
  "can_read": true,
  "can_write": true,
  "can_delete": false,
  "is_recursive": true,
  "granted_by": "admin",
  "note": "项目组成员"
}
```

### 用户管理

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/users` | GET | 获取所有用户 |
| `/api/users/<username>` | GET | 获取用户信息 |
| `/api/users` | POST | 创建用户 |

### 审计日志

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/audit/logs` | GET | 查询审计日志 |
| `/api/audit/user/<username>` | GET | 获取用户活动 |
| `/api/audit/statistics` | GET | 获取统计信息 |

**查询参数:**
- `username`: 用户名
- `action_type`: 操作类型
- `file_path`: 文件路径
- `start_time`: 开始时间 (ISO格式)
- `end_time`: 结束时间
- `limit`: 返回数量（默认1000）

## 🗄️ 数据库结构

### users - 用户表
| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | INTEGER PK | 用户ID |
| username | TEXT UNIQUE | 用户名 |
| role | TEXT | 角色 |
| created_at | TEXT | 创建时间 |
| last_login | TEXT | 最后登录 |
| is_active | INTEGER | 是否激活 |

### directories - 目录表
| 字段 | 类型 | 说明 |
|------|------|------|
| directory_id | INTEGER PK | 目录ID |
| path | TEXT UNIQUE | 目录路径 |
| parent_id | INTEGER FK | 父目录ID |
| is_shared | INTEGER | 是否共享 |
| created_at | TEXT | 创建时间 |
| last_scanned | TEXT | 最后扫描 |

### permissions - 权限表
| 字段 | 类型 | 说明 |
|------|------|------|
| permission_id | INTEGER PK | 权限ID |
| user_id | INTEGER FK | 用户ID |
| directory_id | INTEGER FK | 目录ID |
| can_read | INTEGER | 读权限 |
| can_write | INTEGER | 写权限 |
| can_delete | INTEGER | 删权限 |
| can_execute | INTEGER | 执行权限 |
| is_recursive | INTEGER | 递归应用 |
| granted_at | TEXT | 授予时间 |
| granted_by | TEXT | 授予人 |
| note | TEXT | 备注 |

### audit_log - 审计日志表
| 字段 | 类型 | 说明 |
|------|------|------|
| log_id | INTEGER PK | 日志ID |
| user_id | INTEGER | 用户ID |
| username | TEXT | 用户名 |
| directory_id | INTEGER | 目录ID |
| action_type | TEXT | 操作类型 |
| file_path | TEXT | 文件路径 |
| timestamp | TEXT | 时间戳 |
| ip_address | TEXT | IP地址 |
| success | INTEGER | 是否成功 |
| details | TEXT | 详细信息 |

## 🔒 安全特性

1. **SQL注入防护**: 所有查询使用参数化语句
2. **路径验证**: 防止路径遍历攻击
3. **审计日志**: 记录所有操作
4. **NTFS权限**: 应用Windows文件系统级别权限
5. **CORS配置**: 限制跨域访问

## 🐛 故障排查

### 服务无法启动

**问题**: 端口5000已被占用
```
Address already in use
```

**解决**:
```powershell
# 查找占用进程
netstat -ano | findstr :5000

# 结束进程
taskkill /PID <进程ID> /F
```

### 数据库连接错误

**问题**: 无法创建数据库文件

**解决**: 检查Server目录写权限

```powershell
icacls Server /grant Everyone:F
```

### 权限设置失败

**问题**: 无法设置NTFS权限

**解决**: 
1. 确保以管理员身份运行
2. 检查目标目录的所有权
3. 安装pywin32: `pip install pywin32`

### 文件监控不生效

**问题**: Watchdog未启动

**解决**: 检查watchdog安装
```powershell
pip install watchdog --upgrade
```

## 📊 性能优化

1. **数据库索引**: 已在timestamp、user_id、path字段建立索引
2. **连接池**: DatabaseManager使用单例模式避免连接泄漏
3. **查询限制**: 审计日志查询默认限制1000条
4. **递归深度**: 目录扫描限制最大深度5层

## 🔄 系统维护

### 备份数据库

```powershell
copy server_data.db server_data_backup_%date:~0,4%%date:~5,2%%date:~8,2%.db
```

### 清理审计日志

```python
from dao import AuditDAO
# 删除30天前的日志
# 需要自行实现清理逻辑
```

### 更新系统

1. 停止服务
2. 备份数据库
3. 替换Python文件
4. 重启服务

## 📞 联系支持

- **系统版本**: 2.0.0
- **部署日期**: 2024年10月
- **目标机器**: 192.168.110.77

## 📝 更新日志

### v2.0.0 (2024-10-22)
- ✨ 重新设计架构（分层设计）
- ✨ SQLite数据库替代JSON存储
- ✨ 完整的RESTful API
- ✨ 文件监控功能（Watchdog）
- ✨ 审计日志系统
- ✨ NTFS权限集成
- 🐛 修复原有的连接错误
- 📝 完善部署文档

---

**部署完成后，请在上位机配置文件中设置服务器地址为: `http://192.168.110.77:5000`**
