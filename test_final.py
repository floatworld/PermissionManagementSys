import sys
sys.path.insert(0, 'Server')
from services import SystemService

print("测试获取权限功能...")
result = SystemService.get_file_permissions('C:\\TestACL')

if result.get('success'):
    print(f"✓ 成功! 找到 {len(result.get('permissions', []))} 个权限条目")
    print("\n权限详情:")
    for p in result.get('permissions', []):
        username = p['username']
        perms = p['permissions']
        print(f"  - {username}: {perms}")
else:
    print(f"✗ 失败: {result.get('error')}")
