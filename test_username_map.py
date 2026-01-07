# -*- coding: utf-8 -*-
"""
测试用户名映射功能
"""
import sys
import os
sys.path.append('UIManagement')
from permission_tab import PermissionTab

# 测试用户名映射
tab = PermissionTab()

print("=" * 60)
print("测试用户名映射功能")
print("=" * 60)

print("\n用户名映射字典:")
for key, value in tab.USERNAME_MAP.items():
    print(f"  {key} -> {value}")

print("\n测试映射转换:")
test_users = ['lisi', 'zhangsan', 'wangwu', 'admin']
for user in test_users:
    display_name = tab.get_display_username(user)
    print(f"  {user:15s} -> {display_name}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
