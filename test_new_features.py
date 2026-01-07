# -*- coding: utf-8 -*-
"""
测试新增的系统功能API
"""
import requests

SERVER_URL = "http://127.0.0.1:5000"

print("=" * 60)
print("测试新增功能API")
print("=" * 60)

# 测试1: 获取本地Windows用户
print("\n[1] 测试获取本地Windows用户...")
try:
    response = requests.get(f"{SERVER_URL}/api/system/local-users", timeout=5)
    result = response.json()
    
    if result.get('success'):
        users = result.get('data', [])
        count = result.get('count', 0)
        print(f"  ✓ 成功获取 {count} 个本地用户")
        
        # 显示前5个用户
        for i, user in enumerate(users[:5]):
            username = user.get('username', '')
            full_name = user.get('full_name', '')
            is_disabled = user.get('is_disabled', False)
            status = "[已禁用]" if is_disabled else "[启用]"
            print(f"    {i+1}. {username:20s} {full_name:20s} {status}")
        
        if count > 5:
            print(f"    ... 还有 {count-5} 个用户")
    else:
        print(f"  ✗ 失败: {result.get('error')}")
except Exception as e:
    print(f"  ✗ 异常: {e}")

# 测试2: 设置文件权限 (需要实际路径)
print("\n[2] 测试设置文件权限...")
print("  ⚠ 需要指定实际的测试路径和用户名")
print("  示例代码:")
print("  requests.post(")
print("      f'{SERVER_URL}/api/system/set-permission',")
print("      json={")
print("          'file_path': 'C:\\\\TestFolder',")
print("          'username': 'TestUser',")
print("          'read': True,")
print("          'write': True,")
print("          'modify': False,")
print("          'full_control': False,")
print("          'recursive': False")
print("      }")
print("  )")

# 测试3: 获取文件权限 (需要实际路径)
print("\n[3] 测试获取文件权限...")
print("  ⚠ 需要指定实际的测试路径")
print("  示例代码:")
print("  requests.get(")
print("      f'{SERVER_URL}/api/system/get-permission',")
print("      params={'file_path': 'C:\\\\TestFolder'}")
print("  )")

print("\n" + "=" * 60)
print("✓ API接口测试完成")
print("=" * 60)
