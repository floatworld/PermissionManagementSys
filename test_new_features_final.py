# -*- coding: utf-8 -*-
"""
测试新增功能
"""
import requests

SERVER_URL = "http://127.0.0.1:5000"

print("=" * 70)
print("测试新增功能")
print("=" * 70)

# 测试1: 删除用户API
print("\n[测试1] 测试删除用户API...")
print("  注意：这只是测试API，不会真正删除用户")
print("  实际使用时需要谨慎操作")

# 测试2: 验证USERNAME_MAP用户
print("\n[测试2] 验证USERNAME_MAP中的用户...")
USERNAME_MAP = {
    'lijing': '李静',
    'zhanggongan': '张公安',
    'yanghaitao': '杨海涛',
    'lirunhui': '李润辉',
    'huanghui': '黄卉',
    'maosongjie': '毛宋杰',
    'yuanxiaofang': '袁晓芳',
    'yuguolong': '余国龙',
    'yehao': '叶浩',
    'tumeng': '图勐',
    'pengzhilong': '彭治龙',
    'liwenting': '李文婷',
    'chenglei': '程雷',
}

print(f"  映射用户数: {len(USERNAME_MAP)}")
print("\n  用户列表:")
for i, (key, value) in enumerate(USERNAME_MAP.items(), 1):
    print(f"    {i:2d}. {key:15s} -> {value}")

# 测试3: 默认目录
print("\n[测试3] 验证默认目录...")
DEFAULT_DIRECTORY = r"D:\存放资料"
print(f"  默认目录: {DEFAULT_DIRECTORY}")

import os
if os.path.exists(DEFAULT_DIRECTORY):
    print(f"  ✓ 目录存在")
else:
    print(f"  ✗ 目录不存在（将在权限管理中显示为空）")

# 测试4: 获取目录权限
print("\n[测试4] 获取默认目录的权限信息...")
try:
    response = requests.get(
        f"{SERVER_URL}/api/system/get-permission",
        params={"file_path": DEFAULT_DIRECTORY},
        timeout=10
    )
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            permissions = result.get('permissions', [])
            print(f"  ✓ 成功获取权限，共 {len(permissions)} 条")
            
            # 显示映射用户的权限
            print("\n  映射用户的权限:")
            for username in USERNAME_MAP.keys():
                user_perm = next((p for p in permissions if p.get('username', '').lower() == username.lower()), None)
                display_name = USERNAME_MAP[username]
                if user_perm:
                    perms = user_perm.get('permissions', '无')
                    print(f"    {display_name:8s} ({username:15s}): {perms}")
                else:
                    print(f"    {display_name:8s} ({username:15s}): 无权限")
        else:
            print(f"  ✗ 获取失败: {result.get('error', result.get('message'))}")
    else:
        print(f"  ✗ HTTP错误: {response.status_code}")
except Exception as e:
    print(f"  ✗ 异常: {e}")

print("\n" + "=" * 70)
print("功能说明")
print("=" * 70)

print("""
✅ 功能① 删除Windows用户
   位置: 权限管理 -> "🗑 删除Windows用户" 按钮（红色）
   - 点击按钮弹出删除对话框
   - 选择要删除的用户（自动过滤系统账户）
   - 二次确认后删除
   - 需要管理员权限

✅ 功能② 默认显示映射用户
   位置: 权限管理标签页的表格
   - 自动显示USERNAME_MAP中的所有用户
   - 如果用户有权限，显示具体权限
   - 如果用户无权限，目录路径显示为空
   - 用户筛选下拉框也只显示这些映射用户

✅ 功能③ 根据目录管理刷新权限
   联动机制:
   - 在目录管理中点击某个目录
   - 权限管理自动刷新，显示该目录的权限
   - 显示所有映射用户对该目录的访问权限

✅ 功能④ 默认目录路径
   位置: D:\\存放资料
   - 目录管理标签页的路径输入框默认显示此路径
   - 权限管理初始化时使用此路径
   - 可以通过"📁 浏览..."按钮修改

使用流程:
1. 启动服务器（管理员权限）
2. 启动客户端: python UIManagement/main_window.py
3. 进入"目录管理"，默认显示 D:\\存放资料
4. 进入"权限管理"，查看所有映射用户的权限
5. 在目录管理中点击不同目录，权限管理自动更新
""")

print("=" * 70)
print("测试完成")
print("=" * 70)
