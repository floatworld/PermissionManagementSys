# -*- coding: utf-8 -*-
"""
文件监控模块 - 使用Watchdog实时监控文件系统事件
"""
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from services import AuditService
from datetime import datetime


class FileActivityLogger(FileSystemEventHandler):
    """文件活动记录器"""
    
    def __init__(self, username='系统'):
        super().__init__()
        self.username = username
        self.audit_service = AuditService()
    
    def on_created(self, event):
        """文件/目录创建"""
        if not event.is_directory:
            self._log_event('创建文件', event.src_path)
        else:
            self._log_event('创建目录', event.src_path)
    
    def on_deleted(self, event):
        """文件/目录删除"""
        if not event.is_directory:
            self._log_event('删除文件', event.src_path)
        else:
            self._log_event('删除目录', event.src_path)
    
    def on_modified(self, event):
        """文件修改"""
        if not event.is_directory:
            self._log_event('修改文件', event.src_path)
    
    def on_moved(self, event):
        """文件/目录移动或重命名"""
        action = '移动目录' if event.is_directory else '移动文件'
        details = f"从 {event.src_path} 到 {event.dest_path}"
        self._log_event(action, event.dest_path, details)
    
    def _log_event(self, action_type, file_path, details=''):
        """记录事件到审计日志"""
        try:
            AuditService.log_file_activity(
                action_type=action_type,
                file_path=file_path,
                username=self.username,
                success=True,
                details=details
            )
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {action_type}: {file_path}")
        except Exception as e:
            print(f"审计日志记录失败: {e}")


class FileMonitorService:
    """文件监控服务"""
    
    def __init__(self):
        self.observers = {}  # {path: Observer}
    
    def start_monitoring(self, path, username='系统', recursive=True):
        """
        启动监控指定路径
        path: 要监控的目录路径
        username: 操作用户
        recursive: 是否递归监控子目录
        """
        if not os.path.exists(path):
            raise ValueError(f"路径不存在: {path}")
        
        if not os.path.isdir(path):
            raise ValueError(f"必须是目录: {path}")
        
        if path in self.observers:
            print(f"路径已在监控中: {path}")
            return
        
        # 创建事件处理器
        event_handler = FileActivityLogger(username)
        
        # 创建观察者
        observer = Observer()
        observer.schedule(event_handler, path, recursive=recursive)
        observer.start()
        
        self.observers[path] = observer
        print(f"开始监控: {path} (递归={recursive})")
    
    def stop_monitoring(self, path):
        """停止监控指定路径"""
        if path not in self.observers:
            print(f"路径未在监控中: {path}")
            return
        
        observer = self.observers[path]
        observer.stop()
        observer.join()
        
        del self.observers[path]
        print(f"停止监控: {path}")
    
    def stop_all(self):
        """停止所有监控"""
        for path in list(self.observers.keys()):
            self.stop_monitoring(path)
    
    def get_monitoring_paths(self):
        """获取所有正在监控的路径"""
        return list(self.observers.keys())
    
    def is_monitoring(self, path):
        """检查路径是否正在监控"""
        return path in self.observers


# 全局监控服务实例
monitor_service = FileMonitorService()


if __name__ == '__main__':
    # 测试文件监控
    print("=" * 60)
    print("文件监控模块测试")
    print("=" * 60)
    
    # 监控测试目录
    test_path = "E:\\Project\\PermissionManagementSys\\test_files"
    
    if not os.path.exists(test_path):
        os.makedirs(test_path)
    
    print(f"\n开始监控: {test_path}")
    monitor_service.start_monitoring(test_path, username='测试用户')
    
    print("\n请在监控目录中进行文件操作...")
    print("按 Ctrl+C 停止监控\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n停止监控...")
        monitor_service.stop_all()
        print("监控已停止")
