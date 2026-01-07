# -*- coding: utf-8 -*-
"""
服务层 (Service) - 业务逻辑封装
"""
import os
import win32security
import win32api
import win32con
import win32net
import win32netcon
import ntsecuritycon
from typing import List, Dict, Any, Optional
from datetime import datetime
from dao import UserDAO, DirectoryDAO, PermissionDAO, AuditDAO


class DirectoryService:
    """目录服务 - 处理目录扫描和同步"""
    
    @staticmethod
    def scan_directory_tree(root_path: str, max_depth: int = 5) -> Dict[str, Any]:
        """
        扫描目录树结构
        返回: {
            "path": "...",
            "name": "...",
            "is_directory": True,
            "children": [...]
        }
        """
        if not os.path.exists(root_path):
            raise ValueError(f"路径不存在: {root_path}")
        
        def _scan_recursive(path: str, depth: int = 0) -> Dict[str, Any]:
            if depth > max_depth:
                return None
            
            node = {
                "path": path,
                "name": os.path.basename(path) or path,
                "is_directory": os.path.isdir(path),
                "children": []
            }
            
            if node["is_directory"]:
                try:
                    entries = os.listdir(path)
                    for entry in sorted(entries):
                        child_path = os.path.join(path, entry)
                        if os.path.isdir(child_path):
                            child_node = _scan_recursive(child_path, depth + 1)
                            if child_node:
                                node["children"].append(child_node)
                except PermissionError:
                    node["error"] = "访问被拒绝"
                except Exception as e:
                    node["error"] = str(e)
            
            return node
        
        return _scan_recursive(root_path)
    
    @staticmethod
    def sync_directory_to_database(root_path: str, is_shared: bool = False) -> int:
        """
        同步目录到数据库
        返回同步的目录数量
        """
        count = 0
        
        def _sync_recursive(path: str, parent_id: Optional[int] = None):
            nonlocal count
            
            # 检查目录是否已存在
            existing = DirectoryDAO.get_by_path(path)
            if existing:
                dir_id = existing['directory_id']
                DirectoryDAO.update_scan_time(dir_id)
            else:
                dir_id = DirectoryDAO.create(path, parent_id, is_shared)
                count += 1
            
            # 递归处理子目录
            if os.path.isdir(path):
                try:
                    for entry in os.listdir(path):
                        child_path = os.path.join(path, entry)
                        if os.path.isdir(child_path):
                            _sync_recursive(child_path, dir_id)
                except PermissionError:
                    pass
                except Exception:
                    pass
        
        _sync_recursive(root_path)
        return count
    
    @staticmethod
    def get_directory_structure() -> List[Dict[str, Any]]:
        """获取数据库中的目录结构"""
        all_dirs = DirectoryDAO.list_all()
        
        # 构建树形结构
        dir_map = {d['directory_id']: {**d, 'children': []} for d in all_dirs}
        root_nodes = []
        
        for dir_data in all_dirs:
            dir_id = dir_data['directory_id']
            parent_id = dir_data['parent_id']
            
            if parent_id is None:
                root_nodes.append(dir_map[dir_id])
            elif parent_id in dir_map:
                dir_map[parent_id]['children'].append(dir_map[dir_id])
        
        return root_nodes


class PermissionService:
    """权限服务 - 处理权限管理和验证"""
    
    # 权限映射表
    PERMISSION_MAP = {
        "读取": win32con.GENERIC_READ,
        "写入": win32con.GENERIC_WRITE,
        "修改": win32con.GENERIC_READ | win32con.GENERIC_WRITE,
        "完全控制": win32con.GENERIC_ALL
    }
    
    @staticmethod
    def grant_permission(username: str, directory_path: str, 
                        can_read: bool = False, can_write: bool = False,
                        can_delete: bool = False, can_execute: bool = False,
                        is_recursive: bool = False, granted_by: str = 'admin',
                        note: str = '') -> Dict[str, Any]:
        """
        授予权限
        1. 检查用户和目录是否存在
        2. 更新数据库权限记录
        3. 应用文件系统权限（Windows NTFS ACL）
        """
        # 获取或创建用户
        user = UserDAO.get_by_username(username)
        if not user:
            user_id = UserDAO.create(username)
            user = UserDAO.get_by_id(user_id)
        else:
            user_id = user['user_id']
        
        # 获取或创建目录
        directory = DirectoryDAO.get_by_path(directory_path)
        if not directory:
            directory_id = DirectoryDAO.create(directory_path)
        else:
            directory_id = directory['directory_id']
        
        # 检查权限是否已存在
        existing_perm = PermissionDAO.get_by_user_and_directory(user_id, directory_id)
        
        if existing_perm:
            # 更新现有权限
            PermissionDAO.update(
                existing_perm['permission_id'],
                can_read=can_read,
                can_write=can_write,
                can_delete=can_delete,
                can_execute=can_execute,
                is_recursive=is_recursive,
                note=note
            )
            permission_id = existing_perm['permission_id']
        else:
            # 创建新权限
            permission_id = PermissionDAO.create(
                user_id, directory_id,
                can_read, can_write, can_delete, can_execute,
                is_recursive, granted_by, note
            )
        
        # 应用文件系统权限
        try:
            PermissionService._apply_ntfs_permission(
                directory_path, username, 
                can_read, can_write, can_delete
            )
            success = True
            error = None
        except Exception as e:
            success = False
            error = str(e)
        
        # 记录审计日志
        AuditDAO.create(
            action_type='授予权限',
            file_path=directory_path,
            username=username,
            user_id=user_id,
            directory_id=directory_id,
            success=success,
            details=f"权限设置: 读={can_read}, 写={can_write}, 删={can_delete}, 递归={is_recursive}"
        )
        
        return {
            "success": success,
            "permission_id": permission_id,
            "error": error
        }
    
    @staticmethod
    def revoke_permission(username: str, directory_path: str) -> Dict[str, Any]:
        """撤销权限"""
        user = UserDAO.get_by_username(username)
        if not user:
            return {"success": False, "error": "用户不存在"}
        
        directory = DirectoryDAO.get_by_path(directory_path)
        if not directory:
            return {"success": False, "error": "目录不存在"}
        
        perm = PermissionDAO.get_by_user_and_directory(user['user_id'], directory['directory_id'])
        if not perm:
            return {"success": False, "error": "权限记录不存在"}
        
        # 删除数据库记录
        PermissionDAO.delete(perm['permission_id'])
        
        # 记录审计日志
        AuditDAO.create(
            action_type='撤销权限',
            file_path=directory_path,
            username=username,
            user_id=user['user_id'],
            directory_id=directory['directory_id'],
            success=True,
            details=f"撤销用户 {username} 对 {directory_path} 的权限"
        )
        
        return {"success": True}
    
    @staticmethod
    def get_folder_permissions(directory_path: str) -> List[Dict[str, Any]]:
        """获取文件夹的所有权限"""
        directory = DirectoryDAO.get_by_path(directory_path)
        if not directory:
            return []
        
        return PermissionDAO.list_by_directory(directory['directory_id'])
    
    @staticmethod
    def get_user_permissions(username: str) -> List[Dict[str, Any]]:
        """获取用户的所有权限"""
        user = UserDAO.get_by_username(username)
        if not user:
            return []
        
        return PermissionDAO.list_by_user(user['user_id'])
    
    @staticmethod
    def check_permission(username: str, directory_path: str, 
                        action: str = 'read') -> bool:
        """
        检查用户对目录是否有特定权限
        action: 'read', 'write', 'delete', 'execute'
        """
        user = UserDAO.get_by_username(username)
        if not user:
            return False
        
        directory = DirectoryDAO.get_by_path(directory_path)
        if not directory:
            return False
        
        perm = PermissionDAO.get_by_user_and_directory(user['user_id'], directory['directory_id'])
        if not perm:
            return False
        
        action_map = {
            'read': 'can_read',
            'write': 'can_write',
            'delete': 'can_delete',
            'execute': 'can_execute'
        }
        
        field = action_map.get(action.lower())
        if not field:
            return False
        
        return bool(perm.get(field, 0))
    
    @staticmethod
    def _apply_ntfs_permission(file_path: str, username: str, 
                               can_read: bool, can_write: bool, can_delete: bool):
        """应用NTFS权限（Windows）"""
        try:
            # 获取文件的安全描述符
            sd = win32security.GetFileSecurity(
                file_path, win32security.DACL_SECURITY_INFORMATION
            )
            
            # 获取当前的 DACL
            dacl = sd.GetSecurityDescriptorDacl()
            if dacl is None:
                dacl = win32security.ACL()
            
            # 获取用户的 SID
            try:
                user_sid, domain, type = win32security.LookupAccountName("", username)
            except:
                raise ValueError(f"用户 {username} 不存在")
            
            # 清除该用户的现有权限
            for i in range(dacl.GetAceCount() - 1, -1, -1):
                ace = dacl.GetAce(i)
                if ace[2] == user_sid:
                    dacl.DeleteAce(i)
            
            # 构建新的权限掩码
            mask = 0
            if can_read:
                mask |= win32con.GENERIC_READ
            if can_write:
                mask |= win32con.GENERIC_WRITE
            if can_delete:
                mask |= win32con.DELETE
            
            # 添加新的权限
            if mask > 0:
                dacl.AddAccessAllowedAce(
                    win32security.ACL_REVISION,
                    mask,
                    user_sid
                )
            
            # 设置新的 DACL
            sd.SetSecurityDescriptorDacl(1, dacl, 0)
            win32security.SetFileSecurity(
                file_path,
                win32security.DACL_SECURITY_INFORMATION,
                sd
            )
            
            return True
        except Exception as e:
            raise Exception(f"设置NTFS权限失败: {str(e)}")


class AuditService:
    """审计服务 - 处理审计日志查询和管理"""
    
    @staticmethod
    def log_file_activity(action_type: str, file_path: str, 
                         username: str = '', success: bool = True,
                         details: str = ''):
        """记录文件活动"""
        user = None
        if username:
            user = UserDAO.get_by_username(username)
        
        directory = DirectoryDAO.get_by_path(os.path.dirname(file_path))
        
        AuditDAO.create(
            action_type=action_type,
            file_path=file_path,
            username=username,
            user_id=user['user_id'] if user else None,
            directory_id=directory['directory_id'] if directory else None,
            success=success,
            details=details
        )
    
    @staticmethod
    def query_audit_logs(username: str = None, action_type: str = None,
                        file_path: str = None, start_time: str = None,
                        end_time: str = None, limit: int = 1000) -> List[Dict[str, Any]]:
        """查询审计日志"""
        if start_time and end_time:
            return AuditDAO.list_by_timerange(start_time, end_time, limit)
        elif username or action_type or file_path:
            return AuditDAO.search(username, action_type, file_path, limit)
        else:
            return AuditDAO.list_all(limit)
    
    @staticmethod
    def get_user_activity(username: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """获取用户活动记录"""
        user = UserDAO.get_by_username(username)
        if not user:
            return []
        
        return AuditDAO.list_by_user(user['user_id'], limit)
    
    @staticmethod
    def get_statistics() -> Dict[str, Any]:
        """获取审计统计信息"""
        logs = AuditDAO.list_all(limit=10000)
        
        stats = {
            "total_logs": len(logs),
            "action_counts": {},
            "user_counts": {},
            "success_rate": 0
        }
        
        success_count = 0
        for log in logs:
            # 统计操作类型
            action = log['action_type']
            stats['action_counts'][action] = stats['action_counts'].get(action, 0) + 1
            
            # 统计用户
            username = log['username']
            if username:
                stats['user_counts'][username] = stats['user_counts'].get(username, 0) + 1
            
            # 统计成功率
            if log['success']:
                success_count += 1
        
        if stats['total_logs'] > 0:
            stats['success_rate'] = round(success_count / stats['total_logs'] * 100, 2)
        
        return stats


class SystemService:
    """系统服务 - 处理本地Windows用户和ACL权限"""
    
    @staticmethod
    def create_local_user(username: str, password: str, fullname: str = "", 
                         comment: str = "") -> Dict[str, Any]:
        """
        创建本地Windows用户
        
        参数:
            username: 用户名
            password: 密码
            fullname: 全名（可选）
            comment: 描述（可选）
        
        返回: {"success": True/False, "message": "..."}
        """
        try:
            # 构建用户信息字典
            user_info = {
                'name': username,
                'password': password,
                'priv': win32netcon.USER_PRIV_USER,  # 普通用户权限
                'home_dir': None,
                'comment': comment,
                'flags': win32netcon.UF_SCRIPT | win32netcon.UF_NORMAL_ACCOUNT,
                'script_path': None
            }
            
            # 如果提供了全名，添加到用户信息中
            if fullname:
                user_info['full_name'] = fullname
            
            # 创建用户
            win32net.NetUserAdd(None, 1, user_info)
            
            return {
                "success": True,
                "message": f"成功创建用户: {username}"
            }
            
        except Exception as e:
            error_msg = str(e)
            if "2224" in error_msg:  # 用户已存在
                return {"success": False, "message": f"用户 {username} 已存在"}
            elif "2245" in error_msg:  # 密码不符合要求
                return {"success": False, "message": "密码不符合系统要求（可能太短或太简单）"}
            else:
                return {"success": False, "message": f"创建用户失败: {error_msg}"}
    
    @staticmethod
    def delete_local_user(username: str) -> Dict[str, Any]:
        """
        删除本地Windows用户
        
        参数:
            username: 用户名
        
        返回: {"success": True/False, "message": "..."}
        """
        try:
            # 删除用户
            win32net.NetUserDel(None, username)
            
            return {
                "success": True,
                "message": f"成功删除用户: {username}"
            }
            
        except Exception as e:
            error_msg = str(e)
            if "2221" in error_msg:  # 用户不存在
                return {"success": False, "message": f"用户 {username} 不存在"}
            else:
                return {"success": False, "message": f"删除用户失败: {error_msg}"}
    
    @staticmethod
    def get_local_users() -> List[Dict[str, Any]]:
        """
        获取本地所有Windows用户
        返回: [{"username": "...", "full_name": "...", "comment": "...", "is_disabled": False}, ...]
        """
        users = []
        try:
            # 使用win32net获取本地用户列表
            resume = 0
            while True:
                data, total, resume = win32net.NetUserEnum(
                    None,  # 本地计算机
                    2,     # 详细信息级别
                    win32netcon.FILTER_NORMAL_ACCOUNT,  # 普通用户账户
                    resume,
                    win32netcon.MAX_PREFERRED_LENGTH
                )
                
                for user_info in data:
                    users.append({
                        "username": user_info['name'],
                        "full_name": user_info.get('full_name', ''),
                        "comment": user_info.get('comment', ''),
                        "is_disabled": bool(user_info['flags'] & win32netcon.UF_ACCOUNTDISABLE),
                        "password_age": user_info.get('password_age', 0),
                        "last_logon": user_info.get('last_logon', 0),
                        "num_logons": user_info.get('num_logons', 0)
                    })
                
                if resume == 0:
                    break
        except Exception as e:
            print(f"获取本地用户失败: {e}")
        
        return users
    
    @staticmethod
    def set_file_permission(
        file_path: str,
        username: str,
        read: bool = False,
        write: bool = False,
        modify: bool = False,
        full_control: bool = False,
        recursive: bool = False
    ) -> Dict[str, Any]:
        """
        给指定文件/文件夹添加Windows用户权限
        
        参数:
            file_path: 文件或文件夹路径
            username: Windows用户名
            read: 读取权限
            write: 写入权限
            modify: 修改权限
            full_control: 完全控制权限
            recursive: 是否递归应用到子文件夹
        
        返回: {"success": True/False, "message": "..."}
        """
        try:
            if not os.path.exists(file_path):
                return {"success": False, "message": f"路径不存在: {file_path}"}
            
            # 构建权限掩码
            permissions = 0
            
            if full_control:
                permissions = ntsecuritycon.FILE_ALL_ACCESS
            else:
                if read:
                    permissions |= (
                        ntsecuritycon.FILE_GENERIC_READ |
                        ntsecuritycon.FILE_READ_DATA |
                        ntsecuritycon.FILE_READ_ATTRIBUTES |
                        ntsecuritycon.FILE_READ_EA
                    )
                if write:
                    permissions |= (
                        ntsecuritycon.FILE_GENERIC_WRITE |
                        ntsecuritycon.FILE_WRITE_DATA |
                        ntsecuritycon.FILE_APPEND_DATA |
                        ntsecuritycon.FILE_WRITE_ATTRIBUTES |
                        ntsecuritycon.FILE_WRITE_EA
                    )
                if modify:
                    permissions |= (
                        ntsecuritycon.FILE_GENERIC_READ |
                        ntsecuritycon.FILE_GENERIC_WRITE |
                        ntsecuritycon.FILE_DELETE
                    )
            
            if permissions == 0:
                return {"success": False, "message": "至少需要指定一个权限"}
            
            # 获取用户SID
            try:
                user_sid, domain, type = win32security.LookupAccountName(None, username)
            except Exception as e:
                return {"success": False, "message": f"用户不存在: {username} ({e})"}
            
            # 获取当前安全描述符
            sd = win32security.GetFileSecurity(
                file_path,
                win32security.DACL_SECURITY_INFORMATION
            )
            
            # 获取当前DACL
            dacl = sd.GetSecurityDescriptorDacl()
            if dacl is None:
                dacl = win32security.ACL()
            
            # 添加新的ACE
            dacl.AddAccessAllowedAce(
                win32security.ACL_REVISION,
                permissions,
                user_sid
            )
            
            # 设置新的DACL
            sd.SetSecurityDescriptorDacl(1, dacl, 0)
            win32security.SetFileSecurity(
                file_path,
                win32security.DACL_SECURITY_INFORMATION,
                sd
            )
            
            message = f"成功为用户 {username} 设置权限"
            
            # 递归处理子文件夹
            if recursive and os.path.isdir(file_path):
                count = 0
                for root, dirs, files in os.walk(file_path):
                    for d in dirs:
                        try:
                            sub_path = os.path.join(root, d)
                            SystemService.set_file_permission(
                                sub_path, username, read, write, modify, full_control, False
                            )
                            count += 1
                        except Exception:
                            pass
                    for f in files:
                        try:
                            sub_path = os.path.join(root, f)
                            SystemService.set_file_permission(
                                sub_path, username, read, write, modify, full_control, False
                            )
                            count += 1
                        except Exception:
                            pass
                message += f", 递归处理了 {count} 个子项"
            
            return {"success": True, "message": message}
            
        except Exception as e:
            return {"success": False, "message": f"设置权限失败: {str(e)}"}
    
    @staticmethod
    def remove_file_permission(file_path: str, username: str) -> Dict[str, Any]:
        """
        删除用户对文件/文件夹的所有Windows ACL权限
        
        参数:
            file_path: 文件或文件夹路径
            username: Windows用户名
        
        返回: {"success": True/False, "message": "..."}
        """
        try:
            if not os.path.exists(file_path):
                return {"success": False, "message": f"路径不存在: {file_path}"}
            
            # 获取用户SID
            try:
                user_sid, domain, type = win32security.LookupAccountName(None, username)
            except Exception as e:
                return {"success": False, "message": f"用户不存在: {username} ({e})"}
            
            # 获取当前安全描述符
            sd = win32security.GetFileSecurity(
                file_path,
                win32security.DACL_SECURITY_INFORMATION
            )
            
            # 获取当前DACL
            dacl = sd.GetSecurityDescriptorDacl()
            if dacl is None:
                return {"success": False, "message": "该文件/文件夹没有访问控制列表"}
            
            # 创建新的DACL，移除指定用户的所有ACE
            new_dacl = win32security.ACL()
            ace_count = dacl.GetAceCount()
            removed_count = 0
            
            for i in range(ace_count):
                ace = dacl.GetAce(i)
                # GetAce返回格式: ((ace_type, ace_flags), ace_mask, ace_sid)
                try:
                    ace_header, ace_mask, ace_sid = ace
                    ace_type, ace_flags = ace_header
                    
                    # 如果不是目标用户的ACE，则添加到新DACL中
                    if ace_sid != user_sid:
                        # 只添加允许类型的ACE
                        if ace_type == win32security.ACCESS_ALLOWED_ACE_TYPE:
                            new_dacl.AddAccessAllowedAce(
                                win32security.ACL_REVISION,
                                ace_mask,
                                ace_sid
                            )
                        elif ace_type == win32security.ACCESS_DENIED_ACE_TYPE:
                            new_dacl.AddAccessDeniedAce(
                                win32security.ACL_REVISION,
                                ace_mask,
                                ace_sid
                            )
                    else:
                        removed_count += 1
                        print(f"[ACL删除] 找到并移除用户 {username} 的ACE (类型: {ace_type})")
                except (ValueError, TypeError) as e:
                    print(f"[ACL删除] 处理ACE时出错: {e}, ACE: {ace}")
                    continue
            
            if removed_count == 0:
                return {"success": False, "message": f"未找到用户 {username} 的权限设置"}
            
            # 设置新的DACL
            sd.SetSecurityDescriptorDacl(1, new_dacl, 0)
            win32security.SetFileSecurity(
                file_path,
                win32security.DACL_SECURITY_INFORMATION,
                sd
            )
            
            return {
                "success": True, 
                "message": f"成功删除用户 {username} 的所有权限（共 {removed_count} 条ACE）"
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"删除权限失败: {str(e)}"}
    
    @staticmethod
    def get_file_permissions(file_path: str) -> Dict[str, Any]:
        """
        获取文件/文件夹的当前权限列表
        
        返回: {
            "success": True/False,
            "permissions": [{"username": "...", "permissions": "读、写、修改"}, ...]
        }
        """
        try:
            if not os.path.exists(file_path):
                return {"success": False, "message": f"路径不存在: {file_path}"}
            
            # 获取安全描述符
            try:
                sd = win32security.GetFileSecurity(
                    file_path,
                    win32security.DACL_SECURITY_INFORMATION
                )
            except Exception as e:
                # 权限不足或其他错误
                error_msg = str(e)
                if "拒绝访问" in error_msg or "Access is denied" in error_msg or "5" in error_msg:
                    return {
                        "success": False, 
                        "message": "权限不足：服务器需要管理员权限才能读取此目录的ACL权限",
                        "error_code": "PERMISSION_DENIED"
                    }
                else:
                    return {"success": False, "message": f"获取安全描述符失败: {error_msg}"}
            
            dacl = sd.GetSecurityDescriptorDacl()
            if dacl is None:
                return {"success": True, "permissions": []}
            
            permissions_list = []
            
            # 遍历ACL中的每个ACE
            for i in range(dacl.GetAceCount()):
                ace = dacl.GetAce(i)
                # GetAce返回: ((ace_type, ace_flags), ace_mask, ace_sid)
                try:
                    ace_header, ace_mask, ace_sid = ace
                    ace_type, ace_flags = ace_header
                except (ValueError, TypeError) as e:
                    print(f"[获取权限] 解析ACE失败: {e}, ace={ace}")
                    continue
                
                # 只处理允许类型的ACE
                if ace_type == win32security.ACCESS_ALLOWED_ACE_TYPE:
                    try:
                        username, domain, type = win32security.LookupAccountSid(None, ace_sid)
                        
                        # 解析权限 - 使用win32con中的常量
                        perms = []
                        
                        # 完全控制
                        if ace_mask == ntsecuritycon.FILE_ALL_ACCESS:
                            perms = ["完全控制"]
                        else:
                            # 读取权限
                            if ace_mask & ntsecuritycon.FILE_GENERIC_READ:
                                perms.append("读")
                            # 写入权限  
                            if ace_mask & ntsecuritycon.FILE_GENERIC_WRITE:
                                perms.append("写")
                            # 删除权限 - 使用win32con.DELETE
                            if ace_mask & win32con.DELETE:
                                perms.append("删除")
                            # 执行权限
                            if ace_mask & ntsecuritycon.FILE_GENERIC_EXECUTE:
                                perms.append("执行")
                        
                        permissions_list.append({
                            "username": username,
                            "domain": domain,
                            "permissions": " + ".join(perms) if perms else "其他权限"
                        })
                    except Exception as e:
                        # 忽略无法解析的SID
                        print(f"[获取权限] 解析用户失败: {e}")
            
            return {"success": True, "permissions": permissions_list}
            
        except Exception as e:
            return {"success": False, "message": f"获取权限失败: {str(e)}"}


if __name__ == '__main__':
    # 测试服务层
    print("服务层测试")
    
    # 测试目录扫描
    try:
        test_path = "C:\\Users\\Public"
        tree = DirectoryService.scan_directory_tree(test_path, max_depth=2)
        print(f"目录扫描结果: {tree['name']}, 子目录数: {len(tree['children'])}")
    except Exception as e:
        print(f"目录扫描错误: {e}")
