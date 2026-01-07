# -*- coding: utf-8 -*-
"""
配置文件管理模块
"""
import json
import os
from typing import Dict, Any

class ConfigManager:
    """配置管理器"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
        except FileNotFoundError:
            # 如果配置文件不存在，使用默认配置
            self._config = self._get_default_config()
            self.save_config()
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            self._config = self._get_default_config()
    
    def save_config(self):
        """保存配置文件"""
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "system_name": "斯能服务器管理系统",
            "server": {
                "host": "127.0.0.1",
                "port": 5000
            },
            "default_directory": "D:\\存放资料",
            "user_mapping": {
                "lijing": "李静",
                "zhanggongan": "张公安",
                "yanghaitao": "杨海涛",
                "lirunhui": "李润辉",
                "huanghui": "黄卉",
                "maosongjie": "毛宋杰",
                "yuanxiaofang": "袁晓芳",
                "yuguolong": "余国龙",
                "yehao": "叶浩",
                "tumeng": "图勐",
                "pengzhilong": "彭治龙",
                "liwenting": "李文婷",
                "chenglei": "程雷"
            }
        }
    
    def get(self, key: str, default=None) -> Any:
        """获取配置项"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """设置配置项"""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self.save_config()
    
    @property
    def system_name(self) -> str:
        """系统名称"""
        return self.get('system_name', '斯能服务器管理系统')
    
    @property
    def server_url(self) -> str:
        """服务器URL"""
        host = self.get('server.host', '127.0.0.1')
        port = self.get('server.port', 5000)
        return f"http://{host}:{port}"
    
    @property
    def default_directory(self) -> str:
        """默认目录路径"""
        return self.get('default_directory', 'D:\\存放资料')
    
    @property
    def user_mapping(self) -> Dict[str, str]:
        """用户名映射"""
        return self.get('user_mapping', {})


# 全局配置管理器实例
config = ConfigManager()


if __name__ == '__main__':
    # 测试配置管理器
    print("=" * 60)
    print("配置管理器测试")
    print("=" * 60)
    
    print(f"\n系统名称: {config.system_name}")
    print(f"服务器URL: {config.server_url}")
    print(f"默认目录: {config.default_directory}")
    
    print(f"\n用户映射 ({len(config.user_mapping)} 个):")
    for username, display_name in config.user_mapping.items():
        print(f"  {username:20s} -> {display_name}")
    
    print("\n" + "=" * 60)
