# -*- coding: utf-8 -*-
"""
数据访问层 (DAO) - 封装所有数据库操作
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from database import db


class UserDAO:
    """用户数据访问对象"""
    
    @staticmethod
    def create(username: str, role: str = 'user') -> int:
        """创建用户"""
        query = '''
            INSERT INTO users (username, role, created_at, is_active)
            VALUES (?, ?, ?, 1)
        '''
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return db.execute_update(query, (username, role, now))
    
    @staticmethod
    def get_by_id(user_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取用户"""
        query = 'SELECT * FROM users WHERE user_id = ?'
        results = db.execute_query(query, (user_id,))
        return results[0] if results else None
    
    @staticmethod
    def get_by_username(username: str) -> Optional[Dict[str, Any]]:
        """根据用户名获取用户"""
        query = 'SELECT * FROM users WHERE username = ?'
        results = db.execute_query(query, (username,))
        return results[0] if results else None
    
    @staticmethod
    def list_all(is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
        """列出所有用户"""
        if is_active is None:
            query = 'SELECT * FROM users ORDER BY username'
            return db.execute_query(query)
        else:
            query = 'SELECT * FROM users WHERE is_active = ? ORDER BY username'
            return db.execute_query(query, (1 if is_active else 0,))
    
    @staticmethod
    def update_last_login(user_id: int):
        """更新最后登录时间"""
        query = 'UPDATE users SET last_login = ? WHERE user_id = ?'
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db.execute_update(query, (now, user_id))
    
    @staticmethod
    def delete(user_id: int) -> bool:
        """删除用户（软删除）"""
        query = 'UPDATE users SET is_active = 0 WHERE user_id = ?'
        db.execute_update(query, (user_id,))
        return True


class DirectoryDAO:
    """目录数据访问对象"""
    
    @staticmethod
    def create(path: str, parent_id: Optional[int] = None, is_shared: bool = False) -> int:
        """创建目录记录"""
        query = '''
            INSERT INTO directories (path, parent_id, is_shared, created_at, last_scanned)
            VALUES (?, ?, ?, ?, ?)
        '''
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return db.execute_update(query, (path, parent_id, 1 if is_shared else 0, now, now))
    
    @staticmethod
    def get_by_id(directory_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取目录"""
        query = 'SELECT * FROM directories WHERE directory_id = ?'
        results = db.execute_query(query, (directory_id,))
        return results[0] if results else None
    
    @staticmethod
    def get_by_path(path: str) -> Optional[Dict[str, Any]]:
        """根据路径获取目录"""
        query = 'SELECT * FROM directories WHERE path = ?'
        results = db.execute_query(query, (path,))
        return results[0] if results else None
    
    @staticmethod
    def list_all() -> List[Dict[str, Any]]:
        """列出所有目录"""
        query = 'SELECT * FROM directories ORDER BY path'
        return db.execute_query(query)
    
    @staticmethod
    def list_children(parent_id: int) -> List[Dict[str, Any]]:
        """列出子目录"""
        query = 'SELECT * FROM directories WHERE parent_id = ? ORDER BY path'
        return db.execute_query(query, (parent_id,))
    
    @staticmethod
    def list_shared() -> List[Dict[str, Any]]:
        """列出所有共享目录"""
        query = 'SELECT * FROM directories WHERE is_shared = 1 ORDER BY path'
        return db.execute_query(query)
    
    @staticmethod
    def update_scan_time(directory_id: int):
        """更新扫描时间"""
        query = 'UPDATE directories SET last_scanned = ? WHERE directory_id = ?'
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db.execute_update(query, (now, directory_id))
    
    @staticmethod
    def delete(directory_id: int) -> bool:
        """删除目录记录"""
        query = 'DELETE FROM directories WHERE directory_id = ?'
        db.execute_update(query, (directory_id,))
        return True


class PermissionDAO:
    """权限数据访问对象"""
    
    @staticmethod
    def create(user_id: int, directory_id: int, can_read: bool = False, 
               can_write: bool = False, can_delete: bool = False, can_execute: bool = False,
               is_recursive: bool = False, granted_by: str = 'system', note: str = '') -> int:
        """创建权限记录"""
        query = '''
            INSERT INTO permissions 
            (user_id, directory_id, can_read, can_write, can_delete, can_execute, 
             is_recursive, granted_at, granted_by, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return db.execute_update(query, (
            user_id, directory_id, 
            1 if can_read else 0, 
            1 if can_write else 0, 
            1 if can_delete else 0,
            1 if can_execute else 0,
            1 if is_recursive else 0,
            now, granted_by, note
        ))
    
    @staticmethod
    def get_by_id(permission_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取权限"""
        query = '''
            SELECT p.*, u.username, d.path 
            FROM permissions p
            JOIN users u ON p.user_id = u.user_id
            JOIN directories d ON p.directory_id = d.directory_id
            WHERE p.permission_id = ?
        '''
        results = db.execute_query(query, (permission_id,))
        return results[0] if results else None
    
    @staticmethod
    def get_by_user_and_directory(user_id: int, directory_id: int) -> Optional[Dict[str, Any]]:
        """获取特定用户和目录的权限"""
        query = '''
            SELECT p.*, u.username, d.path 
            FROM permissions p
            JOIN users u ON p.user_id = u.user_id
            JOIN directories d ON p.directory_id = d.directory_id
            WHERE p.user_id = ? AND p.directory_id = ?
        '''
        results = db.execute_query(query, (user_id, directory_id))
        return results[0] if results else None
    
    @staticmethod
    def list_by_user(user_id: int) -> List[Dict[str, Any]]:
        """列出用户的所有权限"""
        query = '''
            SELECT p.*, u.username, d.path 
            FROM permissions p
            JOIN users u ON p.user_id = u.user_id
            JOIN directories d ON p.directory_id = d.directory_id
            WHERE p.user_id = ?
            ORDER BY d.path
        '''
        return db.execute_query(query, (user_id,))
    
    @staticmethod
    def list_by_directory(directory_id: int) -> List[Dict[str, Any]]:
        """列出目录的所有权限"""
        query = '''
            SELECT p.*, u.username, d.path 
            FROM permissions p
            JOIN users u ON p.user_id = u.user_id
            JOIN directories d ON p.directory_id = d.directory_id
            WHERE p.directory_id = ?
            ORDER BY u.username
        '''
        return db.execute_query(query, (directory_id,))
    
    @staticmethod
    def list_all() -> List[Dict[str, Any]]:
        """列出所有权限"""
        query = '''
            SELECT p.*, u.username, d.path 
            FROM permissions p
            JOIN users u ON p.user_id = u.user_id
            JOIN directories d ON p.directory_id = d.directory_id
            ORDER BY u.username, d.path
        '''
        return db.execute_query(query)
    
    @staticmethod
    def update(permission_id: int, can_read: bool = None, can_write: bool = None,
               can_delete: bool = None, can_execute: bool = None, 
               is_recursive: bool = None, note: str = None) -> bool:
        """更新权限"""
        updates = []
        params = []
        
        if can_read is not None:
            updates.append('can_read = ?')
            params.append(1 if can_read else 0)
        if can_write is not None:
            updates.append('can_write = ?')
            params.append(1 if can_write else 0)
        if can_delete is not None:
            updates.append('can_delete = ?')
            params.append(1 if can_delete else 0)
        if can_execute is not None:
            updates.append('can_execute = ?')
            params.append(1 if can_execute else 0)
        if is_recursive is not None:
            updates.append('is_recursive = ?')
            params.append(1 if is_recursive else 0)
        if note is not None:
            updates.append('note = ?')
            params.append(note)
        
        if not updates:
            return False
        
        params.append(permission_id)
        query = f'UPDATE permissions SET {", ".join(updates)} WHERE permission_id = ?'
        db.execute_update(query, tuple(params))
        return True
    
    @staticmethod
    def delete(permission_id: int) -> bool:
        """删除权限"""
        query = 'DELETE FROM permissions WHERE permission_id = ?'
        db.execute_update(query, (permission_id,))
        return True


class AuditDAO:
    """审计日志数据访问对象"""
    
    @staticmethod
    def create(action_type: str, file_path: str = '', user_id: int = None, 
               username: str = '', directory_id: int = None, ip_address: str = '',
               success: bool = True, details: str = '') -> int:
        """创建审计日志"""
        query = '''
            INSERT INTO audit_log 
            (user_id, username, directory_id, action_type, file_path, 
             timestamp, ip_address, success, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return db.execute_update(query, (
            user_id, username, directory_id, action_type, file_path,
            now, ip_address, 1 if success else 0, details
        ))
    
    @staticmethod
    def list_all(limit: int = 1000, offset: int = 0) -> List[Dict[str, Any]]:
        """列出所有审计日志"""
        query = '''
            SELECT * FROM audit_log 
            ORDER BY timestamp DESC 
            LIMIT ? OFFSET ?
        '''
        return db.execute_query(query, (limit, offset))
    
    @staticmethod
    def list_by_user(user_id: int, limit: int = 1000) -> List[Dict[str, Any]]:
        """列出用户的审计日志"""
        query = '''
            SELECT * FROM audit_log 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        '''
        return db.execute_query(query, (user_id, limit))
    
    @staticmethod
    def list_by_action(action_type: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """列出特定操作类型的日志"""
        query = '''
            SELECT * FROM audit_log 
            WHERE action_type = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        '''
        return db.execute_query(query, (action_type, limit))
    
    @staticmethod
    def list_by_timerange(start_time: str, end_time: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """列出时间范围内的日志"""
        query = '''
            SELECT * FROM audit_log 
            WHERE timestamp BETWEEN ? AND ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        '''
        return db.execute_query(query, (start_time, end_time, limit))
    
    @staticmethod
    def search(username: str = None, action_type: str = None, 
               file_path: str = None, limit: int = 1000) -> List[Dict[str, Any]]:
        """搜索审计日志"""
        conditions = []
        params = []
        
        if username:
            conditions.append('username LIKE ?')
            params.append(f'%{username}%')
        if action_type:
            conditions.append('action_type = ?')
            params.append(action_type)
        if file_path:
            conditions.append('file_path LIKE ?')
            params.append(f'%{file_path}%')
        
        where_clause = ' AND '.join(conditions) if conditions else '1=1'
        query = f'''
            SELECT * FROM audit_log 
            WHERE {where_clause}
            ORDER BY timestamp DESC 
            LIMIT ?
        '''
        params.append(limit)
        return db.execute_query(query, tuple(params))


if __name__ == '__main__':
    # 测试DAO
    print("DAO模块测试")
    
    # 创建测试用户
    try:
        user_id = UserDAO.create('test_user', 'admin')
        print(f"创建用户成功: {user_id}")
        
        user = UserDAO.get_by_username('test_user')
        print(f"查询用户: {user}")
    except Exception as e:
        print(f"用户操作错误: {e}")
