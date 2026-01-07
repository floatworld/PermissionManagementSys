# -*- coding: utf-8 -*-
"""
数据库模型层 - SQLite 数据库表结构定义
"""
import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any


class DatabaseManager:
    """数据库管理器 - 单例模式"""
    _instance = None
    _db_path = "server_data.db"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row  # 支持字典式访问
        return conn
    
    def init_database(self):
        """初始化数据库表结构"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                role TEXT DEFAULT 'user',
                created_at TEXT NOT NULL,
                last_login TEXT,
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        # 目录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS directories (
                directory_id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE NOT NULL,
                parent_id INTEGER,
                is_shared INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                last_scanned TEXT,
                FOREIGN KEY (parent_id) REFERENCES directories(directory_id)
            )
        ''')
        
        # 权限表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS permissions (
                permission_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                directory_id INTEGER NOT NULL,
                can_read INTEGER DEFAULT 0,
                can_write INTEGER DEFAULT 0,
                can_delete INTEGER DEFAULT 0,
                can_execute INTEGER DEFAULT 0,
                is_recursive INTEGER DEFAULT 0,
                granted_at TEXT NOT NULL,
                granted_by TEXT,
                note TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (directory_id) REFERENCES directories(directory_id),
                UNIQUE(user_id, directory_id)
            )
        ''')
        
        # 审计日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                directory_id INTEGER,
                action_type TEXT NOT NULL,
                file_path TEXT,
                timestamp TEXT NOT NULL,
                ip_address TEXT,
                success INTEGER DEFAULT 1,
                details TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (directory_id) REFERENCES directories(directory_id)
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_permissions_user ON permissions(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_directories_path ON directories(path)')
        
        conn.commit()
        conn.close()
        
        print("数据库初始化完成")
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """执行查询并返回结果"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """执行更新/插入/删除操作"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id


# 全局数据库实例
db = DatabaseManager()


if __name__ == '__main__':
    # 测试数据库初始化
    db = DatabaseManager()
    print("数据库表创建成功")
