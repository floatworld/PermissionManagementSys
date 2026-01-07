# -*- coding: utf-8 -*-
"""测试系统权限获取功能"""
import sys
sys.path.append('Server')

from services import SystemService
from config_manager import config

def test_get_permissions():
    """测试获取目录权限"""
    
    # 测试多个路径
    test_paths = [
        r"D:\存放资料",
        r"D:\存放资料\个人资料",
        r"C:\Users\Public",
    ]
    
    for test_path in test_paths:
        print("=" * 80)
        print(f"测试路径: {test_path}")
        print("=" * 80)
    for test_path in test_paths:
        print("=" * 80)
        print(f"测试路径: {test_path}")
        print("=" * 80)
        
        # 1. 获取系统权限
        print("调用 SystemService.get_file_permissions()")
        
        result = SystemService.get_file_permissions(test_path)
        print(f"结果: success={result.get('success')}")
        
        if result.get('success'):
            permissions = result.get('permissions', [])
            print(f"权限数量: {len(permissions)}")
            
            if len(permissions) > 0:
                print("\n前5个权限:")
                for i, perm in enumerate(permissions[:5], 1):
                    username = perm.get('username', 'N/A')
                    domain = perm.get('domain', 'N/A')
                    perms = perm.get('permissions', 'N/A')
                    print(f"  {i}. {domain}\\{username} - {perms}")
                
                # 获取配置文件中的用户
                user_mapping = config.user_mapping
                
                # 过滤匹配
                filtered_permissions = []
                for perm in permissions:
                    username = perm.get('username', '').lower()
                    
                    if username in user_mapping:
                        chinese_name = user_mapping[username]
                        perm['chinese_name'] = chinese_name
                        filtered_permissions.append(perm)
                
                print(f"\n配置文件中匹配的用户数: {len(filtered_permissions)}")
                
                if filtered_permissions:
                    print("匹配的用户权限:")
                    for perm in filtered_permissions:
                        username = perm.get('username')
                        chinese_name = perm.get('chinese_name')
                        perms = perm.get('permissions')
                        print(f"  ✓ {username} ({chinese_name}) - {perms}")
                else:
                    print("  ⚠️ 没有找到配置文件中的用户")
        
        print()
    else:
        print(f"错误: {result.get('message', result.get('error', '未知错误'))}")
        print()

if __name__ == '__main__':
    test_get_permissions()
