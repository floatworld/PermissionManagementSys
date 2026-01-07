# -*- coding: utf-8 -*-
"""
API客户端测试脚本
"""
import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_health():
    """测试健康检查"""
    print("\n测试1: 健康检查")
    print("-" * 40)
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return True
    except Exception as e:
        print(f"错误: {e}")
        return False

def test_system_info():
    """测试系统信息"""
    print("\n测试2: 系统信息")
    print("-" * 40)
    try:
        response = requests.get(f"{BASE_URL}/api/info", timeout=5)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return True
    except Exception as e:
        print(f"错误: {e}")
        return False

def test_create_user():
    """测试创建用户"""
    print("\n测试3: 创建用户")
    print("-" * 40)
    try:
        data = {
            "username": "张三",
            "role": "普通用户"
        }
        response = requests.post(f"{BASE_URL}/api/users", json=data, timeout=5)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return True
    except Exception as e:
        print(f"错误: {e}")
        return False

def test_get_users():
    """测试获取用户列表"""
    print("\n测试4: 获取用户列表")
    print("-" * 40)
    try:
        response = requests.get(f"{BASE_URL}/api/users", timeout=5)
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"用户数量: {data['count']}")
        if data['data']:
            print(f"第一个用户: {json.dumps(data['data'][0], ensure_ascii=False, indent=2)}")
        return True
    except Exception as e:
        print(f"错误: {e}")
        return False

def test_scan_directory():
    """测试扫描目录"""
    print("\n测试5: 扫描目录")
    print("-" * 40)
    try:
        data = {
            "path": "C:\\Windows\\System32",
            "max_depth": 1
        }
        response = requests.post(f"{BASE_URL}/api/directory/tree", json=data, timeout=10)
        print(f"状态码: {response.status_code}")
        result = response.json()
        if result['success']:
            print(f"目录名称: {result['data']['name']}")
            print(f"子目录数: {len(result['data']['children'])}")
        else:
            print(f"错误: {result.get('error')}")
        return True
    except Exception as e:
        print(f"错误: {e}")
        return False

def test_grant_permission():
    """测试授予权限"""
    print("\n测试6: 授予权限")
    print("-" * 40)
    try:
        data = {
            "username": "张三",
            "directory_path": "C:\\SharedFolders",
            "can_read": True,
            "can_write": True,
            "is_recursive": True,
            "granted_by": "admin",
            "note": "测试权限"
        }
        response = requests.post(f"{BASE_URL}/api/permissions/grant", json=data, timeout=5)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return True
    except Exception as e:
        print(f"错误: {e}")
        return False

def test_get_permissions():
    """测试获取权限列表"""
    print("\n测试7: 获取权限列表")
    print("-" * 40)
    try:
        response = requests.get(f"{BASE_URL}/api/permissions", timeout=5)
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"权限数量: {data['count']}")
        if data['data']:
            print(f"第一条权限: {json.dumps(data['data'][0], ensure_ascii=False, indent=2)}")
        return True
    except Exception as e:
        print(f"错误: {e}")
        return False

def test_get_audit_logs():
    """测试获取审计日志"""
    print("\n测试8: 获取审计日志")
    print("-" * 40)
    try:
        response = requests.get(f"{BASE_URL}/api/audit/logs?limit=10", timeout=5)
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"日志数量: {data['count']}")
        if data['data']:
            print(f"最新日志: {json.dumps(data['data'][0], ensure_ascii=False, indent=2)}")
        return True
    except Exception as e:
        print(f"错误: {e}")
        return False

def main():
    """运行所有测试"""
    print("=" * 60)
    print("斯能服务器管理系统 - API接口测试")
    print("=" * 60)
    
    tests = [
        test_health,
        test_system_info,
        test_create_user,
        test_get_users,
        test_scan_directory,
        test_grant_permission,
        test_get_permissions,
        test_get_audit_logs,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"测试异常: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"测试完成: 通过 {passed}/{len(tests)}, 失败 {failed}/{len(tests)}")
    print("=" * 60)

if __name__ == '__main__':
    main()
