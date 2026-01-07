# -*- coding: utf-8 -*-
"""
API客户端 - 封装所有与服务器的HTTP通信
"""
import requests
from typing import Dict, List, Any, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config_manager import config

# 从配置文件读取服务器地址
SERVER_URL = config.server_url
REQUEST_TIMEOUT = 10  # 请求超时(秒)


class APIClient:
    """API客户端类 - 统一管理所有API请求"""
    
    def __init__(self, base_url: str = None, timeout: int = 10):
        # 如果没有指定base_url，从配置文件读取
        if base_url is None:
            base_url = config.server_url
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
    
    def update_server_url(self):
        """更新服务器地址（重新从配置文件读取）"""
        self.base_url = config.server_url.rstrip('/')
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        统一的请求封装
        :param method: HTTP方法 (GET, POST, PUT, DELETE)
        :param endpoint: API端点 (如 /api/users)
        :param kwargs: 其他requests参数
        :return: JSON响应
        """
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault('timeout', self.timeout)
        
        try:
            response = self.session.request(method, url, **kwargs)
            
            # 先尝试解析JSON响应
            try:
                json_data = response.json()
            except:
                json_data = None
            
            # 如果状态码不是2xx，但有JSON数据，返回JSON数据（包含错误信息）
            if response.status_code >= 400:
                if json_data:
                    # 服务器返回了结构化的错误信息
                    return json_data
                else:
                    # 没有JSON数据，返回HTTP错误
                    return {"success": False, "error": f"HTTP错误 {response.status_code}: {response.text}"}
            
            # 成功响应
            return json_data if json_data else {"success": True}
            
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "无法连接到服务器"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "请求超时"}
        except Exception as e:
            return {"success": False, "error": f"未知错误: {str(e)}"}
    
    # ==================== 健康检查 ====================
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return self._request('GET', '/health')
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        return self._request('GET', '/api/info')
    
    # ==================== 目录管理 ====================
    
    def get_directory_structure(self) -> Dict[str, Any]:
        """获取目录树结构"""
        return self._request('GET', '/api/directory/structure')
    
    def scan_directory(self, path: str, is_shared: bool = False) -> Dict[str, Any]:
        """
        扫描并同步目录到数据库
        :param path: 目录路径
        :param is_shared: 是否为共享目录
        """
        return self._request('POST', '/api/directory/scan', json={
            'path': path,
            'is_shared': is_shared
        })
    
    def scan_directory_tree(self, path: str, max_depth: int = 3) -> Dict[str, Any]:
        """
        扫描目录树(不存储到数据库)
        :param path: 目录路径
        :param max_depth: 最大深度
        """
        return self._request('POST', '/api/directory/tree', json={
            'path': path,
            'max_depth': max_depth
        })
    
    # ==================== 权限管理 ====================
    
    def get_all_permissions(self) -> Dict[str, Any]:
        """获取所有权限记录"""
        return self._request('GET', '/api/permissions')
    
    def get_user_permissions(self, username: str) -> Dict[str, Any]:
        """获取指定用户的权限列表"""
        return self._request('GET', f'/api/permissions/user/{username}')
    
    def get_directory_permissions(self, directory_path: str) -> Dict[str, Any]:
        """
        获取指定目录的权限列表
        :param directory_path: 目录路径
        """
        return self._request('POST', '/api/permissions/directory', json={
            'path': directory_path
        })
    
    def grant_permission(self, username: str, directory_path: str,
                        can_read: bool = False, can_write: bool = False,
                        can_delete: bool = False, can_execute: bool = False,
                        is_recursive: bool = False, granted_by: str = 'admin',
                        note: str = '') -> Dict[str, Any]:
        """
        授予用户权限
        :param username: 用户名
        :param directory_path: 目录路径
        :param can_read: 读权限
        :param can_write: 写权限
        :param can_delete: 删除权限
        :param can_execute: 执行权限
        :param is_recursive: 是否递归应用
        :param granted_by: 授予人
        :param note: 备注
        """
        return self._request('POST', '/api/permissions/grant', json={
            'username': username,
            'directory_path': directory_path,
            'can_read': can_read,
            'can_write': can_write,
            'can_delete': can_delete,
            'can_execute': can_execute,
            'is_recursive': is_recursive,
            'granted_by': granted_by,
            'note': note
        })
    
    def revoke_permission(self, username: str, directory_path: str) -> Dict[str, Any]:
        """
        撤销用户权限
        :param username: 用户名
        :param directory_path: 目录路径
        """
        return self._request('POST', '/api/permissions/revoke', json={
            'username': username,
            'directory_path': directory_path
        })
    
    def check_permission(self, username: str, directory_path: str, 
                        action: str = 'read') -> Dict[str, Any]:
        """
        检查用户权限
        :param username: 用户名
        :param directory_path: 目录路径
        :param action: 操作类型 (read/write/delete/execute)
        """
        return self._request('POST', '/api/permissions/check', json={
            'username': username,
            'directory_path': directory_path,
            'action': action
        })
    
    # ==================== 用户管理 ====================
    
    def get_all_users(self) -> Dict[str, Any]:
        """获取所有用户"""
        return self._request('GET', '/api/users')
    
    def get_user(self, username: str) -> Dict[str, Any]:
        """获取指定用户信息"""
        return self._request('GET', f'/api/users/{username}')
    
    def create_user(self, username: str, role: str = '普通用户') -> Dict[str, Any]:
        """
        创建用户
        :param username: 用户名
        :param role: 角色
        """
        return self._request('POST', '/api/users', json={
            'username': username,
            'role': role
        })
    
    # ==================== 审计日志 ====================
    
    def get_audit_logs(self, username: str = None, action_type: str = None,
                      file_path: str = None, start_time: str = None,
                      end_time: str = None, limit: int = 1000) -> Dict[str, Any]:
        """
        查询审计日志
        :param username: 用户名过滤
        :param action_type: 操作类型过滤
        :param file_path: 文件路径过滤
        :param start_time: 开始时间
        :param end_time: 结束时间
        :param limit: 返回数量限制
        """
        params = {'limit': limit}
        if username:
            params['username'] = username
        if action_type:
            params['action_type'] = action_type
        if file_path:
            params['file_path'] = file_path
        if start_time:
            params['start_time'] = start_time
        if end_time:
            params['end_time'] = end_time
        
        return self._request('GET', '/api/audit/logs', params=params)
    
    def get_user_audit_logs(self, username: str, limit: int = 1000) -> Dict[str, Any]:
        """获取指定用户的审计日志"""
        return self._request('GET', f'/api/audit/user/{username}', params={'limit': limit})
    
    def get_audit_statistics(self) -> Dict[str, Any]:
        """获取审计统计信息"""
        return self._request('GET', '/api/audit/statistics')
    
    # ==================== 系统管理接口 ====================
    
    def get_local_users(self) -> Dict[str, Any]:
        """
        获取本地所有Windows用户
        :return: {"success": True, "data": [...], "count": n}
        """
        return self._request('GET', '/api/system/local-users')
    
    def set_file_permission(self, file_path: str, username: str,
                           read: bool = False, write: bool = False,
                           modify: bool = False, full_control: bool = False,
                           recursive: bool = False) -> Dict[str, Any]:
        """
        给指定文件/文件夹添加Windows用户权限
        :param file_path: 文件或文件夹路径
        :param username: Windows用户名
        :param read: 读取权限
        :param write: 写入权限
        :param modify: 修改权限
        :param full_control: 完全控制权限
        :param recursive: 是否递归应用到子文件夹
        """
        data = {
            'file_path': file_path,
            'username': username,
            'read': read,
            'write': write,
            'modify': modify,
            'full_control': full_control,
            'recursive': recursive
        }
        return self._request('POST', '/api/system/set-permission', json=data)
    
    def remove_file_permission(self, file_path: str, username: str) -> Dict[str, Any]:
        """
        删除用户对文件/文件夹的所有Windows ACL权限
        :param file_path: 文件或文件夹路径
        :param username: Windows用户名
        """
        data = {
            'file_path': file_path,
            'username': username
        }
        return self._request('POST', '/api/system/remove-permission', json=data)
    
    def get_file_permissions(self, file_path: str) -> Dict[str, Any]:
        """
        获取文件/文件夹的当前权限列表
        :param file_path: 文件或文件夹路径
        """
        return self._request('GET', '/api/system/get-permission', params={'file_path': file_path})
    
    def get_directory_system_permissions(self, directory_path: str) -> Dict[str, Any]:
        """
        获取目录的系统权限（从服务器端读取Windows ACL）
        :param directory_path: 目录路径
        """
        return self._request('GET', '/api/directory/system-permissions', params={'path': directory_path})
    
    def create_local_user(self, username: str, password: str, 
                         fullname: str = "", comment: str = "") -> Dict[str, Any]:
        """
        创建本地Windows用户
        :param username: 用户名
        :param password: 密码
        :param fullname: 全名（可选）
        :param comment: 描述（可选）
        """
        data = {
            'username': username,
            'password': password,
            'fullname': fullname,
            'comment': comment
        }
        return self._request('POST', '/api/system/create-user', json=data)
    
    def delete_local_user(self, username: str) -> Dict[str, Any]:
        """
        删除本地Windows用户
        :param username: 用户名
        """
        data = {'username': username}
        return self._request('POST', '/api/system/delete-user', json=data)


# 单例模式 - 全局API客户端实例
api_client = APIClient()


if __name__ == '__main__':
    # 测试API客户端
    print("测试API客户端连接...")
    
    result = api_client.health_check()
    if result.get('success', False) or result.get('status') == 'ok':
        print("✓ 服务器连接正常")
        print(f"  响应: {result}")
    else:
        print("✗ 服务器连接失败")
        print(f"  错误: {result.get('error')}")
