# -*- coding: utf-8 -*-
"""
测试目录权限显示功能
"""
import sys
import os

# 添加路径
sys.path.append(os.path.dirname(__file__))

from UIManagement.api_client import api_client
from config_manager import config

def test_directory_permissions():
    """测试目录权限功能"""
    
    # 测试路径
    test_paths = [
        r"D:\存放资料",
        r"D:\存放资料\个人资料",
        r"D:\存放资料\产品资料",
    ]
    
    for test_path in test_paths:
        print("="*80)
        test_single_path(test_path)
        print()

def test_single_path(test_path):
    """测试单个路径"""
    
    print(f"测试路径: {test_path}")
    print(f"路径是否存在: {os.path.exists(test_path)}")
    print()
    
    # 测试配置文件读取
    print("配置文件中的用户映射:")
    user_mapping = config.user_mapping
    print(f"用户数量: {len(user_mapping)}")
    for username, chinese_name in user_mapping.items():
        print(f"  {username} -> {chinese_name}")
    print()
    
    # 测试 API 调用
    print("调用 API 获取权限...")
    result = api_client.get_file_permissions(test_path)
    
    print(f"API 返回结果:")
    print(f"  success: {result.get('success')}")
    
    if result.get('success'):
        permissions = result.get('permissions', [])
        print(f"  权限数量: {len(permissions)}")
        print()
        
        print("所有权限列表:")
        for i, perm in enumerate(permissions[:20]):  # 显示前20个
            username = perm.get('username', 'N/A')
            domain = perm.get('domain', 'N/A')
            perms = perm.get('permissions', 'N/A')
            print(f"  {i+1}. {domain}\\{username} - {perms}")
        
        if len(permissions) > 20:
            print(f"  ... 还有 {len(permissions) - 20} 个权限")
        print()
        
        # 测试过滤逻辑
        print("过滤配置文件中的用户:")
        filtered_permissions = []
        for perm in permissions:
            username = perm.get('username', '').lower()
            print(f"  检查用户: {username}", end="")
            
            # 检查用户名是否在配置文件中（不区分大小写）
            if username in user_mapping:
                chinese_name = user_mapping[username]
                perm['chinese_name'] = chinese_name
                filtered_permissions.append(perm)
                print(f" ✓ 匹配 -> {chinese_name}")
            else:
                print(" ✗ 未匹配")
        
        print()
        print(f"过滤后的用户数量: {len(filtered_permissions)}")
        
        if filtered_permissions:
            print("\n配置文件中的用户权限:")
            for perm in filtered_permissions:
                username = perm.get('username', 'N/A')
                chinese_name = perm.get('chinese_name', 'N/A')
                perms = perm.get('permissions', 'N/A')
                print(f"  {username} ({chinese_name}) - {perms}")
        else:
            print("\n⚠️ 没有找到配置文件中的用户")
    else:
        print(f"  error: {result.get('error', result.get('message', '未知错误'))}")

if __name__ == '__main__':
    test_directory_permissions()
