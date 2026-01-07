# -*- coding: utf-8 -*-
"""
数据模型 - 客户端数据结构定义
"""
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class DirectoryNode:
    """目录节点模型"""
    directory_id: int
    path: str
    name: str
    parent_id: Optional[int] = None
    is_shared: bool = False
    created_at: str = ''
    last_scanned: str = ''
    children: List['DirectoryNode'] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DirectoryNode':
        """从字典创建目录节点"""
        children_data = data.get('children', [])
        children = [cls.from_dict(child) for child in children_data]
        
        return cls(
            directory_id=data.get('directory_id', 0),
            path=data.get('path', ''),
            name=data.get('name', ''),
            parent_id=data.get('parent_id'),
            is_shared=data.get('is_shared', False),
            created_at=data.get('created_at', ''),
            last_scanned=data.get('last_scanned', ''),
            children=children
        )


@dataclass
class UserPermission:
    """用户权限模型"""
    permission_id: int
    user_id: int
    username: str
    directory_id: int
    directory_path: str
    can_read: bool
    can_write: bool
    can_delete: bool
    can_execute: bool
    is_recursive: bool
    granted_at: str
    granted_by: str
    note: str = ''
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UserPermission':
        """从字典创建权限对象"""
        return cls(
            permission_id=data.get('permission_id', 0),
            user_id=data.get('user_id', 0),
            username=data.get('username', ''),
            directory_id=data.get('directory_id', 0),
            directory_path=data.get('path', ''),
            can_read=bool(data.get('can_read', 0)),
            can_write=bool(data.get('can_write', 0)),
            can_delete=bool(data.get('can_delete', 0)),
            can_execute=bool(data.get('can_execute', 0)),
            is_recursive=bool(data.get('is_recursive', 0)),
            granted_at=data.get('granted_at', ''),
            granted_by=data.get('granted_by', ''),
            note=data.get('note', '')
        )
    
    def to_permission_string(self) -> str:
        """转换为权限字符串"""
        perms = []
        if self.can_read:
            perms.append('读')
        if self.can_write:
            perms.append('写')
        if self.can_delete:
            perms.append('删')
        if self.can_execute:
            perms.append('执行')
        return '、'.join(perms) if perms else '无权限'


@dataclass
class AuditRecord:
    """审计记录模型"""
    log_id: int
    user_id: Optional[int]
    username: str
    directory_id: Optional[int]
    action_type: str
    file_path: str
    timestamp: str
    ip_address: str
    success: bool
    details: str = ''
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AuditRecord':
        """从字典创建审计记录"""
        return cls(
            log_id=data.get('log_id', 0),
            user_id=data.get('user_id'),
            username=data.get('username', ''),
            directory_id=data.get('directory_id'),
            action_type=data.get('action_type', ''),
            file_path=data.get('file_path', ''),
            timestamp=data.get('timestamp', ''),
            ip_address=data.get('ip_address', ''),
            success=bool(data.get('success', 1)),
            details=data.get('details', '')
        )
    
    def get_formatted_time(self) -> str:
        """获取格式化的时间"""
        try:
            dt = datetime.fromisoformat(self.timestamp)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return self.timestamp
    
    def get_status_text(self) -> str:
        """获取状态文本"""
        return '成功' if self.success else '失败'


@dataclass
class User:
    """用户模型"""
    user_id: int
    username: str
    role: str
    created_at: str
    last_login: Optional[str] = None
    is_active: bool = True
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """从字典创建用户对象"""
        return cls(
            user_id=data.get('user_id', 0),
            username=data.get('username', ''),
            role=data.get('role', '普通用户'),
            created_at=data.get('created_at', ''),
            last_login=data.get('last_login'),
            is_active=bool(data.get('is_active', 1))
        )
