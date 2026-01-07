# -*- coding: utf-8 -*-
"""
本地联调测试脚本
"""
import sys
import time
sys.path.insert(0, '.')

print("=" * 60)
print("斯能服务器管理系统 - 本地联调测试")
print("=" * 60)

# 1. 测试配置
print("\n[1] 测试配置文件...")
from config import SERVER_URL, SYSTEM_NAME
print(f"  系统名称: {SYSTEM_NAME}")
print(f"  服务器地址: {SERVER_URL}")

# 2. 测试API客户端
print("\n[2] 测试API客户端...")
from UIManagement.api_client import api_client

# 健康检查
print("  - 健康检查...")
result = api_client.health_check()
if result.get('status') == 'ok' or result.get('success'):
    print(f"    ✓ 服务器连接成功")
    print(f"    响应: {result}")
else:
    print(f"    ✗ 服务器连接失败")
    print(f"    错误: {result.get('error')}")
    sys.exit(1)

# 系统信息
print("\n  - 系统信息...")
result = api_client.get_system_info()
if result.get('success'):
    data = result.get('data', {})
    print(f"    系统: {data.get('system_name')}")
    print(f"    版本: {data.get('version')}")
    print(f"    用户数: {data.get('user_count')}")
    print(f"    目录数: {data.get('directory_count')}")
    print(f"    权限数: {data.get('permission_count')}")
else:
    print(f"    ✗ 获取系统信息失败: {result.get('error')}")

# 3. 测试数据模型
print("\n[3] 测试数据模型...")
from UIManagement.data_models import DirectoryNode, UserPermission, AuditRecord
print("  ✓ DirectoryNode")
print("  ✓ UserPermission")
print("  ✓ AuditRecord")

# 4. 测试用户管理
print("\n[4] 测试用户管理...")
result = api_client.get_all_users()
if result.get('success'):
    users = result.get('data', [])
    print(f"  当前用户数: {len(users)}")
    if users:
        print(f"  第一个用户: {users[0].get('username')}")
else:
    print(f"  获取用户列表失败: {result.get('error')}")

# 5. 测试目录管理
print("\n[5] 测试目录管理...")
result = api_client.get_directory_structure()
if result.get('success'):
    dirs = result.get('data', [])
    print(f"  当前根目录数: {len(dirs)}")
else:
    print(f"  获取目录结构失败: {result.get('error')}")

# 6. 测试权限管理
print("\n[6] 测试权限管理...")
result = api_client.get_all_permissions()
if result.get('success'):
    perms = result.get('data', [])
    print(f"  当前权限数: {len(perms)}")
    if perms:
        p = perms[0]
        print(f"  示例权限: {p.get('username')} -> {p.get('path')}")
else:
    print(f"  获取权限列表失败: {result.get('error')}")

# 7. 测试审计日志
print("\n[7] 测试审计日志...")
result = api_client.get_audit_logs(limit=10)
if result.get('success'):
    logs = result.get('data', [])
    print(f"  当前日志数: {len(logs)}")
    if logs:
        log = logs[0]
        print(f"  最新日志: {log.get('action_type')} - {log.get('username')}")
else:
    print(f"  获取审计日志失败: {result.get('error')}")

print("\n" + "=" * 60)
print("✓ 本地联调测试完成!")
print("=" * 60)
print("\n下一步: 运行客户端UI")
print("  python UIManagement/main_window.py")
print("=" * 60)
