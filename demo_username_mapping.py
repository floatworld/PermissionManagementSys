# -*- coding: utf-8 -*-
"""
演示用户名映射功能
"""

print("=" * 70)
print("权限管理 - 用户名映射功能演示")
print("=" * 70)

# 模拟 USERNAME_MAP
USERNAME_MAP = {
    'lisi': '李四',
    'zhangsan': '张三'
}

print("\n配置的用户名映射:")
print("-" * 70)
for key, value in USERNAME_MAP.items():
    print(f"  {key:15s} -> {value}")

# 模拟权限数据
class MockPermission:
    def __init__(self, username, directory_path, can_read, can_write):
        self.username = username
        self.directory_path = directory_path
        self.can_read = can_read
        self.can_write = can_write
        self.can_delete = False
        self.can_execute = False
        self.is_recursive = False
        self.granted_at = "2025-11-21"
        self.granted_by = "admin"
        self.note = ""
    
    def to_permission_string(self):
        perms = []
        if self.can_read: perms.append("读")
        if self.can_write: perms.append("写")
        return ", ".join(perms) if perms else "无"

# 模拟数据库中的权限记录
permissions = [
    MockPermission("lisi", "C:\\SharedFolders\\Project1", True, True),
    MockPermission("zhangsan", "C:\\SharedFolders\\Project2", True, False),
    MockPermission("admin", "C:\\SharedFolders\\Admin", True, True),
    MockPermission("lisi", "C:\\SharedFolders\\Documents", True, False),
]

print("\n" + "=" * 70)
print("权限表格显示效果（应用映射后）")
print("=" * 70)

# 表格头
print(f"{'用户名':15s} {'目录路径':35s} {'权限':10s} {'授予时间':12s}")
print("-" * 70)

# 应用映射显示
def get_display_username(username):
    return USERNAME_MAP.get(username, username)

for perm in permissions:
    display_username = get_display_username(perm.username)
    print(f"{display_username:15s} {perm.directory_path:35s} {perm.to_permission_string():10s} {perm.granted_at:12s}")

print("\n" + "=" * 70)
print("用户筛选下拉框显示效果")
print("=" * 70)

# 获取所有唯一用户
users = set(p.username for p in permissions)
print("\n下拉框选项:")
print("  - 全部用户")
for user in sorted(users):
    display_name = get_display_username(user)
    print(f"  - {display_name} (实际值: {user})")

print("\n" + "=" * 70)
print("功能说明")
print("=" * 70)
print("""
1. 当权限记录中的用户名为 'lisi' 时，表格显示 '李四'
2. 当权限记录中的用户名为 'zhangsan' 时，表格显示 '张三'
3. 其他未映射的用户名保持原样显示（如 'admin'）
4. 筛选下拉框中也会显示映射后的中文名
5. 筛选功能使用实际的用户名进行匹配

如何添加更多映射：
编辑 UIManagement/permission_tab.py 文件
在 PermissionTab 类中的 USERNAME_MAP 字典添加键值对
例如：
    USERNAME_MAP = {
        'lisi': '李四',
        'zhangsan': '张三',
        'wangwu': '王五',
        'zhaoliu': '赵六'
    }
""")

print("=" * 70)
print("演示完成")
print("=" * 70)
