# -*- coding: utf-8 -*-
"""
主窗口 - 整合 DirectoryTab, PermissionTab, AuditTab 三个标签页
"""
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTabWidget, QLabel, QPushButton, QStatusBar,
                             QMessageBox, QApplication)
from PyQt5.QtCore import Qt, QTimer, QDateTime
from PyQt5.QtGui import QIcon
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config_manager import config
from UIManagement.api_client import api_client

# 客户端配置常量
CLIENT_VERSION = "2.0.0"
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
HEARTBEAT_INTERVAL = 30  # 心跳间隔(秒)
from UIManagement.directory_tab import DirectoryTab
from UIManagement.permission_tab import PermissionTab
from UIManagement.audit_tab import AuditTab


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.connected = False
        self.init_ui()
        self.init_timer()
        self.check_connection()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle(f"{config.system_name} v{CLIENT_VERSION}")
        self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)
        
        # 设置窗口图标
        icon_path = os.path.join(os.path.dirname(__file__), 'resources', 'app_icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 顶部状态栏
        top_bar = self._create_top_bar()
        layout.addWidget(top_bar)
        
        # 标签页
        self.tab_widget = self._create_tab_widget()
        layout.addWidget(self.tab_widget, 1)
        
        # 底部状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("就绪")
        
        # 应用航空主题
        self._apply_aviation_theme()
    
    def _create_top_bar(self) -> QWidget:
        """创建顶部状态栏 - 航空风格"""
        top_bar = QWidget()
        top_bar.setObjectName("topStatusBar")
        top_bar.setFixedHeight(70)
        
        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(20, 10, 20, 10)
        
        # 系统名称
        title_label = QLabel(f"🛫 {config.system_name}")
        title_label.setObjectName("systemTitle")
        layout.addWidget(title_label)
        
        # 版本号
        version_label = QLabel(f"v{CLIENT_VERSION}")
        version_label.setStyleSheet("color: #6a8db3; font-size: 9pt;")
        layout.addWidget(version_label)
        
        layout.addStretch()
        
        # 系统时间
        self.time_label = QLabel()
        self.time_label.setObjectName("sysTime")
        layout.addWidget(self.time_label)
        
        # 服务器地址
        self.server_label = QLabel(f"📡 {config.server_url}")
        self.server_label.setStyleSheet("color: #a0cfff; font-size: 9pt; padding: 0 15px;")
        layout.addWidget(self.server_label)
        
        # 连接状态LED
        self.status_led = QLabel("●")
        self.status_led.setStyleSheet("color: #757575; font-size: 24px;")
        layout.addWidget(self.status_led)
        
        self.status_label = QLabel("未连接")
        self.status_label.setObjectName("connStatus")
        layout.addWidget(self.status_label)
        
        # 刷新连接按钮
        self.connect_btn = QPushButton("🔄 检查连接")
        self.connect_btn.setFixedSize(80, 35)
        self.connect_btn.clicked.connect(self.check_connection)
        layout.addWidget(self.connect_btn)
        
        # 系统时间
        self.time_label = QLabel()
        self.time_label.setStyleSheet("color: #4a9eff; font-size: 11pt; font-weight: bold;")
        self.update_time()
        layout.addWidget(self.time_label)
        
        return top_bar
    
    def _create_tab_widget(self) -> QTabWidget:
        """创建标签页"""
        tab_widget = QTabWidget()
        tab_widget.setTabPosition(QTabWidget.North)
        
        # 三个核心标签页
        self.directory_tab = DirectoryTab()
        self.permission_tab = PermissionTab()
        self.audit_tab = AuditTab()
        
        # 建立标签页之间的连接
        self.directory_tab.permission_tab = self.permission_tab
        self.permission_tab.directory_tab = self.directory_tab  # 反向引用
        
        tab_widget.addTab(self.directory_tab, "📁 目录管理")
        tab_widget.addTab(self.permission_tab, "🔐 权限管理")
        tab_widget.addTab(self.audit_tab, "📋 审计日志")
        
        return tab_widget
    
    def _apply_aviation_theme(self):
        """应用航空专业深色主题"""
        self.setStyleSheet("""
            QMainWindow { background-color: #1a1d23; }
            QWidget {
                background-color: #1a1d23;
                color: #e0e0e0;
                font-family: "Microsoft YaHei", "Consolas", monospace;
                font-size: 10pt;
            }
            #topStatusBar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2a3f5f, stop:1 #1a2332);
                border-bottom: 2px solid #4a9eff;
            }
            #systemTitle {
                font-size: 16pt;
                font-weight: bold;
                color: #4a9eff;
            }
            #sysTime {
                color: #a0cfff;
                font-size: 9pt;
                padding: 0 10px;
            }
            #connStatus {
                color: #ffa726;
                font-weight: bold;
                font-size: 10pt;
            }
            QTabWidget::pane {
                border: 1px solid #3a3f47;
                background-color: #1e2229;
                border-radius: 4px;
            }
            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2a3340, stop:1 #1a2330);
                color: #a0a0a0;
                padding: 12px 30px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: bold;
                font-size: 10pt;
                border: 1px solid #3a3f47;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3a4d66, stop:1 #2a3d56);
                color: #4a9eff;
                border-bottom: 3px solid #4a9eff;
            }
            QTabBar::tab:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3a4552, stop:1 #2a3542);
                color: #e0e0e0;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3a4d66, stop:1 #2a3d56);
                border: 1px solid #4a5d76;
                border-radius: 4px;
                color: #e0e0e0;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a6d96, stop:1 #3a5d86);
                border: 1px solid #5a7d9f;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2a3d56, stop:1 #3a4d66);
            }
            QPushButton:disabled {
                background-color: #1a1d23;
                color: #505050;
                border: 1px solid #2a2d33;
            }
            QStatusBar {
                background-color: #1a1d23;
                color: #808080;
                border-top: 1px solid #2a2d33;
                font-size: 9pt;
            }
        """)
    
    def init_timer(self):
        """初始化定时器"""
        # 时间更新定时器
        self.time_timer = QTimer(self)
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)  # 每秒更新
        
        # 心跳检查定时器
        self.heartbeat_timer = QTimer(self)
        self.heartbeat_timer.timeout.connect(self.check_connection)
        self.heartbeat_timer.start(HEARTBEAT_INTERVAL * 1000)  # 默认30秒
    
    def update_time(self):
        """更新系统时间"""
        current_time = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        self.time_label.setText(f"⏰ {current_time}")
    
    def check_connection(self):
        """检查服务器连接"""
        self.connect_btn.setEnabled(False)
        self.connect_btn.setText("检查中...")
        
        # 更新服务器地址显示（从配置文件重新读取）
        self.server_label.setText(f"📡 {config.server_url}")
        
        # 确保API客户端使用最新的服务器地址
        api_client.update_server_url()
        
        result = api_client.health_check()
        
        if result.get('success', False) or result.get('status') == 'ok':
            self.set_connected(True)
            service_name = result.get('service', config.system_name)
            timestamp = result.get('timestamp', '')
            self.statusBar.showMessage(f"✓ 已连接到: {service_name} | 服务器时间: {timestamp[:19] if timestamp else 'N/A'}")
        else:
            self.set_connected(False)
            error = result.get('error', '未知错误')
            self.statusBar.showMessage(f"✗ 连接失败: {error}")
        
        self.connect_btn.setEnabled(True)
        self.connect_btn.setText("🔄 检查连接")
    
    def set_connected(self, connected: bool):
        """设置连接状态"""
        self.connected = connected
        
        if connected:
            self.status_led.setStyleSheet("color: #66bb6a; font-size: 24px;")  # 绿色
            self.status_label.setText("已连接")
            self.status_label.setStyleSheet("color: #66bb6a; font-weight: bold;")
        else:
            self.status_led.setStyleSheet("color: #ef5350; font-size: 24px;")  # 红色
            self.status_label.setText("断开连接")
            self.status_label.setStyleSheet("color: #ef5350; font-weight: bold;")
    
    def closeEvent(self, event):
        """关闭事件"""
        reply = QMessageBox.question(
            self, '确认退出',
            '确定要退出系统吗?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 停止定时器
            if hasattr(self, 'heartbeat_timer'):
                self.heartbeat_timer.stop()
            if hasattr(self, 'time_timer'):
                self.time_timer.stop()
            
            # 清理子Tab的线程
            for i in range(self.tab_widget.count()):
                tab = self.tab_widget.widget(i)
                if hasattr(tab, 'closeEvent'):
                    from PyQt5.QtGui import QCloseEvent
                    close_evt = QCloseEvent()
                    tab.closeEvent(close_evt)
            
            event.accept()
        else:
            event.ignore()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用信息
    app.setApplicationName(config.system_name)
    app.setApplicationVersion(CLIENT_VERSION)
    app.setOrganizationName("斯能科技")
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
