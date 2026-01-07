# -*- coding: utf-8 -*-
"""
服务器启动脚本
"""
import sys
import os
import ctypes

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config_manager import config
from api import app
from database import DatabaseManager

def is_admin():
    """检查是否以管理员权限运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """请求管理员权限重新运行"""
    try:
        if sys.platform == 'win32':
            # 获取当前脚本路径
            script = sys.argv[0]
            params = ' '.join(sys.argv[1:])
            
            # 请求管理员权限
            ctypes.windll.shell32.ShellExecuteW(
                None, 
                "runas", 
                sys.executable,
                f'"{script}" {params}',
                None,
                1  # SW_SHOWNORMAL
            )
            sys.exit(0)
    except Exception as e:
        print(f"✗ 无法获取管理员权限: {e}")
        sys.exit(1)

if __name__ == '__main__':
    # 检查管理员权限
    if not is_admin():
        print("=" * 60)
        print("需要管理员权限来设置文件ACL权限")
        print("正在请求管理员权限...")
        print("=" * 60)
        run_as_admin()
    # 检查管理员权限
    if not is_admin():
        print("=" * 60)
        print("需要管理员权限来设置文件ACL权限")
        print("正在请求管理员权限...")
        print("=" * 60)
        run_as_admin()
    
    # 显示管理员权限状态
    print("=" * 60)
    print("✓ 已获取管理员权限")
    print("=" * 60)
    
    # 初始化数据库
    print("正在初始化数据库...")
    db = DatabaseManager()
    db.init_database()
    print("✓ 数据库初始化完成")
    
    # 启动Flask服务
    print("\n" + "=" * 60)
    print(f"{config.system_name} - 服务器端")
    print("=" * 60)
    print(f"服务地址: http://0.0.0.0:5000")
    print(f"健康检查: http://0.0.0.0:5000/health")
    print(f"系统信息: http://0.0.0.0:5000/api/info")
    print("=" * 60)
    print("按 Ctrl+C 停止服务")
    print("=" * 60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
