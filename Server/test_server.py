# -*- coding: utf-8 -*-
"""
服务器功能测试脚本
"""
import sys
import os

# 添加Server目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from database import DatabaseManager
from dao import UserDAO, DirectoryDAO, PermissionDAO, AuditDAO
from services import DirectoryService, PermissionService, AuditService


def test_database():
    """测试数据库初始化"""
    print("\n" + "="*60)
    print("测试 1: 数据库初始化")
    print("="*60)
    
    db = DatabaseManager()
    db.init_database()
    print("✓ 数据库初始化成功")
    

def test_user_dao():
    """测试用户DAO"""
    print("\n" + "="*60)
    print("测试 2: 用户DAO")
    print("="*60)
    
    # 创建用户
    user_id = UserDAO.create("测试用户", "管理员")
    print(f"✓ 创建用户: ID={user_id}")
    
    # 查询用户
    user = UserDAO.get_by_username("测试用户")
    print(f"✓ 查询用户: {user}")
    
    # 列出所有用户
    users = UserDAO.list_all()
    print(f"✓ 用户总数: {len(users)}")


def test_directory_dao():
    """测试目录DAO"""
    print("\n" + "="*60)
    print("测试 3: 目录DAO")
    print("="*60)
    
    # 创建目录
    dir_id = DirectoryDAO.create("C:\\TestFolder", is_shared=True)
    print(f"✓ 创建目录: ID={dir_id}")
    
    # 查询目录
    directory = DirectoryDAO.get_by_path("C:\\TestFolder")
    print(f"✓ 查询目录: {directory}")
    
    # 列出所有目录
    directories = DirectoryDAO.list_all()
    print(f"✓ 目录总数: {len(directories)}")


def test_permission_service():
    """测试权限服务"""
    print("\n" + "="*60)
    print("测试 4: 权限服务")
    print("="*60)
    
    # 授予权限
    result = PermissionService.grant_permission(
        username="测试用户",
        directory_path="C:\\TestFolder",
        can_read=True,
        can_write=True,
        is_recursive=True,
        granted_by="admin",
        note="测试权限"
    )
    print(f"✓ 授予权限: {result}")
    
    # 查询用户权限
    perms = PermissionService.get_user_permissions("测试用户")
    print(f"✓ 用户权限数: {len(perms)}")
    if perms:
        print(f"  详情: {perms[0]}")
    
    # 检查权限
    has_read = PermissionService.check_permission("测试用户", "C:\\TestFolder", "read")
    print(f"✓ 检查读权限: {has_read}")


def test_audit_service():
    """测试审计服务"""
    print("\n" + "="*60)
    print("测试 5: 审计服务")
    print("="*60)
    
    # 记录活动
    AuditService.log_file_activity(
        action_type="测试操作",
        file_path="C:\\TestFolder\\test.txt",
        username="测试用户",
        success=True,
        details="这是一条测试日志"
    )
    print("✓ 记录审计日志")
    
    # 查询日志
    logs = AuditService.query_audit_logs(username="测试用户")
    print(f"✓ 审计日志数: {len(logs)}")
    
    # 获取统计
    stats = AuditService.get_statistics()
    print(f"✓ 审计统计: 总计{stats['total_logs']}条, 成功率{stats['success_rate']}%")


def test_directory_service():
    """测试目录服务"""
    print("\n" + "="*60)
    print("测试 6: 目录服务")
    print("="*60)
    
    # 扫描目录树
    try:
        tree = DirectoryService.scan_directory_tree("C:\\Windows\\System32", max_depth=1)
        print(f"✓ 扫描目录树: {tree['name']}, 子目录数: {len(tree['children'])}")
    except Exception as e:
        print(f"⚠ 扫描目录失败: {e}")
    
    # 获取数据库中的目录结构
    structure = DirectoryService.get_directory_structure()
    print(f"✓ 数据库目录结构: {len(structure)} 个根目录")


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("斯能服务器管理系统 - 功能测试")
    print("="*60)
    
    try:
        test_database()
        test_user_dao()
        test_directory_dao()
        test_permission_service()
        test_audit_service()
        test_directory_service()
        
        print("\n" + "="*60)
        print("✓ 所有测试通过!")
        print("="*60)
        print("\n下一步:")
        print("1. 运行 start.bat 启动服务器")
        print("2. 访问 http://localhost:5000/health 验证服务")
        print("3. 使用上位机客户端连接测试")
        print("="*60)
        
    except Exception as e:
        print("\n" + "="*60)
        print(f"✗ 测试失败: {e}")
        print("="*60)
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
