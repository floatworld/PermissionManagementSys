# 斯能服务器管理系统 - 客户端

## 📋 概述

这是斯能服务器管理系统的上位机客户端,使用PyQt5开发,提供专业的航空风格界面。

## 🎯 主要功能

### 1. 目录管理 (DirectoryTab)
- 📁 扫描目录树结构
- 🔄 同步目录到数据库
- 📊 查看目录详情
- 🌳 树形结构展示

### 2. 权限管理 (PermissionTab)
- ✅ 查看所有权限记录
- ➕ 授予用户权限
- 🗑 撤销用户权限
- ✏ 编辑权限设置
- 🔍 按用户筛选权限

### 3. 审计日志 (AuditTab)
- 📋 查询审计日志
- 🔍 多条件筛选(用户/操作/路径/时间)
- 📊 统计分析
- 📥 导出CSV
- 📈 可视化展示

## 📦 文件结构

```
UIManagement/
├── main_window.py       # 主窗口 - 整合三个标签页
├── directory_tab.py     # 目录管理标签页
├── permission_tab.py    # 权限管理标签页
├── audit_tab.py         # 审计日志标签页
├── api_client.py        # API客户端 - 封装HTTP通信
├── data_models.py       # 数据模型 - DirectoryNode, UserPermission, AuditRecord
└── logs/                # 客户端日志目录
```

## 🛠️ 技术栈

- **UI框架**: PyQt5 5.15+
- **HTTP客户端**: requests 2.28+
- **通信协议**: HTTP/JSON
- **Python版本**: 3.8+

## 🚀 快速开始

### 1. 安装依赖

```powershell
pip install PyQt5 requests
```

或使用requirements.txt:

```powershell
pip install -r requirements.txt
```

### 2. 配置服务器地址

编辑 `config.py`:

```python
# 开发环境
SERVER_URL = "http://127.0.0.1:5000"

# 生产环境
SERVER_URL = "http://192.168.110.77:5000"
```

### 3. 启动客户端

**方法1**: 使用批处理文件(推荐)
```
双击 start_client.bat
```

**方法2**: 命令行启动
```powershell
python UIManagement\main_window.py
```

## 🎨 界面展示

### 主窗口布局

```
┌──────────────────────────────────────────────────────────┐
│  ✈ 斯能服务器管理系统      服务器: ... [●] 已连接 🔄  时间 │
├──────────────────────────────────────────────────────────┤
│  [📁 目录管理] [🔐 权限管理] [📋 审计日志]               │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                                                      │ │
│  │                   标签页内容区域                     │ │
│  │                                                      │ │
│  │                                                      │ │
│  └─────────────────────────────────────────────────────┘ │
│  就绪                                                     │
└──────────────────────────────────────────────────────────┘
```

### 颜色主题

- **背景色**: #1a1d23 (深色)
- **强调色**: #4a9eff (蓝色)
- **边框色**: #3d4450 (中灰)
- **文字色**: #e0e0e0 (浅灰)

## 📡 API客户端使用

### 基本用法

```python
from UIManagement.api_client import api_client

# 健康检查
result = api_client.health_check()

# 获取目录结构
result = api_client.get_directory_structure()

# 授予权限
result = api_client.grant_permission(
    username="张三",
    directory_path="C:\\SharedFolders",
    can_read=True,
    can_write=True
)

# 查询审计日志
result = api_client.get_audit_logs(
    username="张三",
    limit=100
)
```

### 错误处理

所有API调用返回统一格式:

```python
{
    "success": True/False,
    "data": {...},      # 成功时的数据
    "error": "..."      # 失败时的错误信息
}
```

## 🔧 配置说明

### config.py 配置项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| SERVER_URL | 服务器地址 | http://127.0.0.1:5000 |
| CLIENT_VERSION | 客户端版本 | 2.0.0 |
| SYSTEM_NAME | 系统名称 | 斯能服务器管理系统 |
| HEARTBEAT_INTERVAL | 心跳间隔(秒) | 30 |
| REQUEST_TIMEOUT | 请求超时(秒) | 10 |
| WINDOW_WIDTH | 窗口宽度 | 1400 |
| WINDOW_HEIGHT | 窗口高度 | 900 |

## 🐛 故障排查

### 1. 无法连接服务器

**现象**: 连接状态显示"断开连接"

**解决**:
- 检查服务器是否启动
- 检查 config.py 中的 SERVER_URL 配置
- 检查网络连接
- 检查防火墙设置

### 2. PyQt5 导入错误

**现象**: `ModuleNotFoundError: No module named 'PyQt5'`

**解决**:
```powershell
pip install PyQt5
```

### 3. 请求超时

**现象**: 操作一直显示"加载中..."

**解决**:
- 增加 REQUEST_TIMEOUT 值
- 检查服务器性能
- 检查网络延迟

## 📝 开发指南

### 添加新功能

1. **创建新的标签页**:
   - 在 UIManagement/ 下创建新的 .py 文件
   - 继承 QWidget 类
   - 实现 init_ui() 方法

2. **添加API接口**:
   - 在 api_client.py 中添加新方法
   - 遵循统一的错误处理模式

3. **定义数据模型**:
   - 在 data_models.py 中添加 @dataclass
   - 实现 from_dict() 类方法

### 代码风格

- 使用中文注释
- 遵循PEP 8规范
- 方法名使用snake_case
- 类名使用PascalCase

## 🔒 安全注意事项

1. **敏感信息**: 不要在代码中硬编码密码
2. **输入验证**: 所有用户输入都经过验证
3. **错误处理**: 不显示敏感的系统错误信息
4. **日志记录**: 不记录密码等敏感信息

## 📞 技术支持

- **版本**: 2.0.0
- **开发日期**: 2024年10月
- **联系方式**: 技术支持团队

## 📄 更新日志

### v2.0.0 (2024-10-22)
- ✨ 重新设计架构 - 三标签页模式
- ✨ API客户端封装 - 统一错误处理
- ✨ 数据模型抽象 - DirectoryNode, UserPermission, AuditRecord
- ✨ 航空风格深色主题
- ✨ 实时连接状态监控
- ✨ 审计日志统计和导出
- 🐛 修复原有的连接错误
- 📝 完整的代码注释和文档

---

**开发完成,可以开始联调测试!** 🎉
