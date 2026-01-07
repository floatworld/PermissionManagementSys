# -*- coding: utf-8 -*-
"""
测试ACL权限设置功能
"""
import requests
import os

SERVER_URL = "http://127.0.0.1:5000"

print("=" * 60)
print("测试 Windows ACL 权限设置")
print("=" * 60)

# 创建测试目录
test_folder = r"C:\TestACL"
if not os.path.exists(test_folder):
    try:
        os.makedirs(test_folder)
        print(f"\n✓ 已创建测试目录: {test_folder}")
    except Exception as e:
        print(f"\n✗ 创建目录失败: {e}")
        test_folder = None
else:
    print(f"\n✓ 测试目录已存在: {test_folder}")

if test_folder:
    # 测试1: 设置权限 - 缺少file_path
    print("\n[测试1] 缺少file_path参数...")
    try:
        response = requests.post(
            f"{SERVER_URL}/api/system/set-permission",
            json={
                "username": "test_user1",
                "read": True,
                "write": True
            },
            timeout=10
        )
        result = response.json()
        print(f"  状态码: {response.status_code}")
        print(f"  结果: {result}")
    except Exception as e:
        print(f"  ✗ 异常: {e}")

    # 测试2: 设置权限 - 缺少username
    print("\n[测试2] 缺少username参数...")
    try:
        response = requests.post(
            f"{SERVER_URL}/api/system/set-permission",
            json={
                "file_path": test_folder,
                "read": True,
                "write": True
            },
            timeout=10
        )
        result = response.json()
        print(f"  状态码: {response.status_code}")
        print(f"  结果: {result}")
    except Exception as e:
        print(f"  ✗ 异常: {e}")

    # 测试3: 设置权限 - 未选择任何权限
    print("\n[测试3] 未选择任何权限...")
    try:
        response = requests.post(
            f"{SERVER_URL}/api/system/set-permission",
            json={
                "file_path": test_folder,
                "username": "test_user1",
                "read": False,
                "write": False,
                "modify": False,
                "full_control": False
            },
            timeout=10
        )
        result = response.json()
        print(f"  状态码: {response.status_code}")
        print(f"  结果: {result}")
    except Exception as e:
        print(f"  ✗ 异常: {e}")

    # 测试4: 正确的权限设置
    print("\n[测试4] 正确设置权限...")
    try:
        response = requests.post(
            f"{SERVER_URL}/api/system/set-permission",
            json={
                "file_path": test_folder,
                "username": "test_user1",
                "read": True,
                "write": True,
                "modify": False,
                "full_control": False,
                "recursive": False
            },
            timeout=10
        )
        result = response.json()
        print(f"  状态码: {response.status_code}")
        print(f"  结果: {result}")
        
        if result.get('success'):
            print(f"  ✓ {result.get('message')}")
        else:
            print(f"  ✗ {result.get('message')}")
    except Exception as e:
        print(f"  ✗ 异常: {e}")

    # 测试5: 查看设置后的权限
    print("\n[测试5] 查看当前权限...")
    try:
        response = requests.get(
            f"{SERVER_URL}/api/system/get-permission",
            params={"file_path": test_folder},
            timeout=10
        )
        result = response.json()
        print(f"  状态码: {response.status_code}")
        
        if result.get('success'):
            perms = result.get('permissions', [])
            print(f"  ✓ 找到 {len(perms)} 个权限:")
            for p in perms[:5]:  # 只显示前5个
                username = p.get('username', 'N/A')
                domain = p.get('domain', 'N/A')
                permissions = p.get('permissions', 'N/A')
                print(f"    - {username:20s} ({domain:15s}): {permissions}")
        else:
            print(f"  ✗ 获取失败: {result.get('error', result.get('message', '未知错误'))}")
    except Exception as e:
        print(f"  ✗ 获取权限失败: {e}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
