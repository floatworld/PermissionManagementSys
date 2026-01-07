# -*- coding: utf-8 -*-
"""检查数据库中的权限记录"""
import sys
sys.path.append('Server')
from dao import PermissionDAO

perms = PermissionDAO.list_all()
print(f'数据库中权限总数: {len(perms)}')
print()

if perms:
    print("前10条权限记录:")
    for i, p in enumerate(perms[:10], 1):
        perm_str = []
        if p.can_read: perm_str.append('读')
        if p.can_write: perm_str.append('写')
        if p.can_delete: perm_str.append('删')
        if p.can_execute: perm_str.append('执')
        print(f"{i}. {p.user_name} -> {p.directory_path}")
        print(f"   权限: {' + '.join(perm_str) if perm_str else '无'}")
else:
    print("⚠️ 数据库中没有权限记录")
    print("\n提示：您需要先在【权限管理】标签页中为用户授予目录访问权限")
