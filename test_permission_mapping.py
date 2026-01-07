# -*- coding: utf-8 -*-
"""
测试权限管理中的用户名映射功能
需要先在数据库中有对应的权限记录
"""
import requests
import json

SERVER_URL = "http://127.0.0.1:5000"

print("=" * 70)
print("测试权限管理 - 用户名映射功能")
print("=" * 70)

# 1. 检查服务器状态
print("\n[1] 检查服务器状态...")
try:
    response = requests.get(f"{SERVER_URL}/health", timeout=5)
    result = response.json()
    print(f"✓ 服务器运行正常: {result.get('service')}")
except Exception as e:
    print(f"✗ 服务器未运行: {e}")
    print("请先启动服务器: cd Server && python start_server.py")
    exit(1)

# 2. 创建测试用户（如果不存在）
print("\n[2] 创建测试用户...")
test_users = [
    {"username": "lisi", "password": "Test@12345", "fullname": "李四测试", "comment": "测试用户"},
    {"username": "zhangsan", "password": "Test@12345", "fullname": "张三测试", "comment": "测试用户"}
]

for user_data in test_users:
    try:
        response = requests.post(
            f"{SERVER_URL}/api/system/create-user",
            json=user_data,
            timeout=10
        )
        result = response.json()
        if result.get('success'):
            print(f"✓ 创建用户: {user_data['username']} -> {user_data['fullname']}")
        else:
            msg = result.get('message', '')
            if '已存在' in msg:
                print(f"- 用户已存在: {user_data['username']}")
            else:
                print(f"✗ 创建失败: {msg}")
    except Exception as e:
        print(f"✗ 请求异常: {e}")

# 3. 授予测试权限
print("\n[3] 授予测试权限...")
test_permissions = [
    {
        "username": "lisi",
        "directory_path": "C:\\TestACL",
        "can_read": True,
        "can_write": True,
        "can_delete": False,
        "can_execute": False,
        "is_recursive": False,
        "granted_by": "admin",
        "note": "测试李四的权限"
    },
    {
        "username": "zhangsan",
        "directory_path": "C:\\TestACL",
        "can_read": True,
        "can_write": False,
        "can_delete": False,
        "can_execute": False,
        "is_recursive": False,
        "granted_by": "admin",
        "note": "测试张三的权限"
    }
]

for perm in test_permissions:
    try:
        response = requests.post(
            f"{SERVER_URL}/api/permissions/grant",
            json=perm,
            timeout=10
        )
        result = response.json()
        if result.get('success'):
            print(f"✓ 授予权限: {perm['username']} -> {perm['directory_path']}")
        else:
            print(f"✗ 授予失败: {result.get('error', '未知错误')}")
    except Exception as e:
        print(f"✗ 请求异常: {e}")

# 4. 查询所有权限
print("\n[4] 查询所有权限...")
try:
    response = requests.get(f"{SERVER_URL}/api/permissions", timeout=10)
    result = response.json()
    
    if result.get('success'):
        permissions = result.get('data', [])
        print(f"✓ 找到 {len(permissions)} 条权限记录\n")
        
        # 用户名映射
        USERNAME_MAP = {
            'lisi': '李四',
            'zhangsan': '张三'
        }
        
        # 显示包含测试用户的权限
        print("权限记录（应用映射后）:")
        print("-" * 70)
        print(f"{'显示名':12s} {'实际用户名':12s} {'目录路径':30s} {'权限':15s}")
        print("-" * 70)
        
        test_user_perms = [p for p in permissions if p.get('username') in ['lisi', 'zhangsan', 'admin']]
        
        for perm in test_user_perms[:10]:  # 最多显示10条
            username = perm.get('username', 'N/A')
            display_name = USERNAME_MAP.get(username, username)
            directory = perm.get('directory_path', 'N/A')
            
            # 构建权限字符串
            perms_list = []
            if perm.get('can_read'): perms_list.append('读')
            if perm.get('can_write'): perms_list.append('写')
            if perm.get('can_delete'): perms_list.append('删')
            if perm.get('can_execute'): perms_list.append('执行')
            perms_str = ', '.join(perms_list) if perms_list else '无'
            
            print(f"{display_name:12s} {username:12s} {directory:30s} {perms_str:15s}")
        
        print("\n说明:")
        print("- '显示名' 列显示的是映射后的中文名（如：李四、张三）")
        print("- '实际用户名' 列是数据库中存储的原始用户名（如：lisi、zhangsan）")
        print("- 在UI界面的权限管理表格中，只会显示映射后的中文名")
        
    else:
        print(f"✗ 查询失败: {result.get('error')}")
except Exception as e:
    print(f"✗ 请求异常: {e}")

print("\n" + "=" * 70)
print("测试完成")
print("=" * 70)
print("\n现在可以打开客户端UI查看效果:")
print("  python UIManagement/main_window.py")
print("  -> 进入 '权限管理' 标签页")
print("  -> 查看表格中 lisi 显示为 '李四'，zhangsan 显示为 '张三'")
print("=" * 70)
