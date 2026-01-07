# -*- coding: utf-8 -*-
"""
目录管理标签页 - DirectoryTab
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTreeWidget, QTreeWidgetItem, QLabel, QLineEdit,
                             QMessageBox, QSplitter, QTextEdit, QGroupBox,
                             QFileDialog, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMenu, QAction, QDialog, QDialogButtonBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint
from PyQt5.QtGui import QIcon, QColor, QCursor
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from UIManagement.api_client import api_client
from UIManagement.data_models import DirectoryNode
from config_manager import config


class DirectoryLoadWorker(QThread):
    """目录加载工作线程"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, path=None):
        super().__init__()
        self.path = path
    
    def run(self):
        try:
            if self.path:
                # 扫描指定路径
                result = api_client.scan_directory_tree(self.path, max_depth=3)
            else:
                # 获取数据库中的目录结构
                result = api_client.get_directory_structure()
            
            if result.get('success'):
                self.finished.emit(result)
            else:
                self.error.emit(result.get('error', '未知错误'))
        except Exception as e:
            self.error.emit(str(e))


class DirectoryTab(QWidget):
    """目录管理标签页"""
    
    # 默认目录路径
    DEFAULT_DIRECTORY = r"D:\存放资料"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.permission_tab = None  # 权限管理标签页引用
        self.init_ui()
        self.worker = None
        # 设置默认路径
        self.path_input.setText(self.DEFAULT_DIRECTORY)
    
    def closeEvent(self, event):
        """窗口关闭事件 - 清理线程"""
        if self.worker and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait(1000)  # 等待最多1秒
        event.accept()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 顶部工具栏
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)
        
        # 分割器 - 左侧目录树,右侧详情
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧 - 目录树
        tree_widget = self._create_tree_widget()
        splitter.addWidget(tree_widget)
        
        # 右侧 - 目录详情
        detail_widget = self._create_detail_widget()
        splitter.addWidget(detail_widget)
        
        splitter.setSizes([800, 400])
        layout.addWidget(splitter, 1)
        
        # 应用深色主题样式
        self._apply_dark_theme()
    
    def _create_toolbar(self) -> QWidget:
        """创建工具栏"""
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 路径输入框（只读）
        layout.addWidget(QLabel("目录路径:"))
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("目录路径已锁定")
        self.path_input.setMinimumWidth(400)
        self.path_input.setReadOnly(True)  # 设置为只读
        self.path_input.setStyleSheet("""
            QLineEdit {
                background-color: #2a2f38;
                color: #888888;
            }
        """)
        layout.addWidget(self.path_input)
        
        # 扫描按钮
        self.scan_btn = QPushButton("🔍 扫描目录")
        self.scan_btn.clicked.connect(self.scan_directory)
        layout.addWidget(self.scan_btn)
        
        # 刷新按钮
        self.refresh_btn = QPushButton("🔄 刷新")
        self.refresh_btn.clicked.connect(self.refresh_directory_tree)
        layout.addWidget(self.refresh_btn)
        
        # 同步到数据库按钮
        self.sync_btn = QPushButton("💾 同步到数据库")
        self.sync_btn.clicked.connect(self.sync_to_database)
        layout.addWidget(self.sync_btn)
        
        layout.addStretch()
        
        return toolbar
    
    def _create_tree_widget(self) -> QWidget:
        """创建目录树组件"""
        group = QGroupBox("目录树")
        layout = QVBoxLayout(group)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["目录名称", "路径", "共享"])
        self.tree.setColumnWidth(0, 300)
        self.tree.setColumnWidth(1, 400)
        self.tree.itemClicked.connect(self.on_tree_item_clicked)
        
        layout.addWidget(self.tree)
        return group
    
    def _create_detail_widget(self) -> QWidget:
        """创建详情组件"""
        group = QGroupBox("目录详情")
        layout = QVBoxLayout(group)
        
        # 基本信息显示区
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setMaximumHeight(200)
        layout.addWidget(self.detail_text)
        
        # 用户权限部分
        perm_header = QHBoxLayout()
        perm_label = QLabel("用户访问权限")
        perm_label.setStyleSheet("font-size: 11pt; font-weight: bold; color: #4a9eff;")
        perm_header.addWidget(perm_label)
        perm_header.addStretch()
        
        # 添加用户按钮
        self.add_user_btn = QPushButton("➕ 添加用户")
        self.add_user_btn.setEnabled(False)
        self.add_user_btn.clicked.connect(self.add_users_to_directory)
        self.add_user_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2e7d32, stop:1 #1b5e20);
                border: 1px solid #43a047;
                border-radius: 4px;
                padding: 6px 12px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #43a047, stop:1 #2e7d32);
            }
            QPushButton:disabled {
                background: #3d4450;
                color: #888;
            }
        """)
        perm_header.addWidget(self.add_user_btn)
        layout.addLayout(perm_header)
        
        # 权限表格
        self.perm_table = QTableWidget()
        self.perm_table.setColumnCount(3)
        self.perm_table.setHorizontalHeaderLabels(["用户名", "中文名", "访问权限"])
        self.perm_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.perm_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.perm_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.perm_table.verticalHeader().setVisible(False)
        self.perm_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.perm_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.perm_table.customContextMenuRequested.connect(self.show_permission_context_menu)
        layout.addWidget(self.perm_table)
        
        # 保存当前选中的目录路径
        self.current_selected_path = None
        
        return group
    
    def _apply_dark_theme(self):
        """应用深色主题"""
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1d23;
                color: #e0e0e0;
                font-family: "Microsoft YaHei UI", "微软雅黑";
                font-size: 10pt;
            }
            QGroupBox {
                border: 1px solid #3d4450;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #4a9eff;
            }
            QTreeWidget {
                background-color: #1e2228;
                border: 1px solid #3d4450;
                border-radius: 4px;
                alternate-background-color: #252930;
                color: #ffffff;
                font-size: 10pt;
            }
            QTreeWidget::item {
                padding: 6px;
                color: #ffffff;
                border-bottom: 1px solid #2a2f38;
            }
            QTreeWidget::item:selected {
                background-color: #4a9eff;
                color: #ffffff;
            }
            QTreeWidget::item:hover {
                background-color: #3d4450;
            }
            QTreeWidget::branch {
                background-color: #1e2228;
            }
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {
                border-image: none;
                image: none;
            }
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {
                border-image: none;
                image: none;
            }
            QHeaderView::section {
                background-color: #2a2f38;
                color: #ffffff;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #4a9eff;
                font-weight: bold;
                font-size: 11pt;
            }
            QLineEdit {
                background-color: #252930;
                border: 1px solid #3d4450;
                border-radius: 4px;
                padding: 6px;
                color: #ffffff;
            }
            QLineEdit:focus {
                border: 1px solid #4a9eff;
            }
            QPushButton {
                background-color: #3d4450;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                color: #ffffff;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4a9eff;
            }
            QPushButton:pressed {
                background-color: #3a8eee;
            }
            QTextEdit {
                background-color: #252930;
                border: 1px solid #3d4450;
                border-radius: 4px;
                color: #ffffff;
                line-height: 1.5;
            }
        """)
    
    def scan_directory(self):
        """扫描目录"""
        path = self.path_input.text().strip()
        if not path:
            QMessageBox.warning(self, "警告", "请输入目录路径")
            return
        
        self.scan_btn.setEnabled(False)
        self.scan_btn.setText("扫描中...")
        
        self.worker = DirectoryLoadWorker(path)
        self.worker.finished.connect(self.on_scan_finished)
        self.worker.error.connect(self.on_scan_error)
        self.worker.start()
    
    def refresh_directory_tree(self):
        """刷新目录树"""
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("加载中...")
        
        self.worker = DirectoryLoadWorker()
        self.worker.finished.connect(self.on_refresh_finished)
        self.worker.error.connect(self.on_scan_error)
        self.worker.start()
    
    def sync_to_database(self):
        """同步目录到数据库"""
        path = self.path_input.text().strip()
        if not path:
            QMessageBox.warning(self, "警告", "请输入要同步的目录路径")
            return
        
        reply = QMessageBox.question(
            self, '确认',
            f'确定要将目录 {path} 同步到数据库吗?\n这可能需要一些时间。',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.sync_btn.setEnabled(False)
            self.sync_btn.setText("同步中...")
            
            result = api_client.scan_directory(path, is_shared=True)
            
            self.sync_btn.setEnabled(True)
            self.sync_btn.setText("💾 同步到数据库")
            
            if result.get('success'):
                QMessageBox.information(self, "成功", result.get('message', '同步完成'))
                self.refresh_directory_tree()
            else:
                QMessageBox.critical(self, "错误", result.get('error', '同步失败'))
    
    def on_scan_finished(self, result):
        """扫描完成"""
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("🔍 扫描目录")
        
        data = result.get('data', {})
        if isinstance(data, dict):
            self.tree.clear()
            self._add_tree_items(None, [data])
            self.tree.expandToDepth(1)
        else:
            QMessageBox.warning(self, "警告", "返回数据格式错误")
    
    def on_refresh_finished(self, result):
        """刷新完成"""
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("🔄 刷新")
        
        data = result.get('data', [])
        self.tree.clear()
        self._add_tree_items(None, data)
        self.tree.expandToDepth(1)
    
    def on_scan_error(self, error):
        """扫描错误"""
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("🔍 扫描目录")
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("🔄 刷新")
        
        QMessageBox.critical(self, "错误", f"操作失败: {error}")
    
    def _add_tree_items(self, parent_item, nodes):
        """递归添加树节点"""
        for node_data in nodes:
            # 创建树项
            if isinstance(node_data, dict):
                name = node_data.get('name', '')
                path = node_data.get('path', '')
                is_shared = '是' if node_data.get('is_shared', False) else '否'
                children = node_data.get('children', [])
            else:
                continue
            
            item = QTreeWidgetItem([name, path, is_shared])
            item.setData(0, Qt.UserRole, node_data)
            
            if parent_item:
                parent_item.addChild(item)
            else:
                self.tree.addTopLevelItem(item)
            
            # 递归添加子节点
            if children:
                self._add_tree_items(item, children)
    
    def on_tree_item_clicked(self, item, column):
        """树节点点击事件"""
        node_data = item.data(0, Qt.UserRole)
        
        if node_data:
            path = node_data.get('path', '')
            self.current_selected_path = path  # 保存当前路径
            
            # 更新权限管理标签页的当前目录
            if self.permission_tab and path:
                self.permission_tab.set_current_directory(path)
            
            # 显示基本信息
            details = f"""
<h3>目录信息</h3>
<table style="width:100%">
<tr><td style="color:#4a9eff;font-weight:bold">名称:</td><td>{node_data.get('name', '')}</td></tr>
<tr><td style="color:#4a9eff;font-weight:bold">路径:</td><td>{path}</td></tr>
<tr><td style="color:#4a9eff;font-weight:bold">共享:</td><td>{'是' if node_data.get('is_shared') else '否'}</td></tr>
<tr><td style="color:#4a9eff;font-weight:bold">创建时间:</td><td>{node_data.get('created_at', 'N/A')}</td></tr>
<tr><td style="color:#4a9eff;font-weight:bold">最后扫描:</td><td>{node_data.get('last_scanned', 'N/A')}</td></tr>
<tr><td style="color:#4a9eff;font-weight:bold">子目录数:</td><td>{len(node_data.get('children', []))}</td></tr>
</table>
            """
            self.detail_text.setHtml(details)
            
            # 获取访问权限信息并显示在表格中
            if path:
                self.add_user_btn.setEnabled(True)  # 启用添加用户按钮
                self.perm_table.setRowCount(0)  # 清空表格
                
                # 获取权限信息
                try:
                    # 调用服务器API获取系统权限
                    result = api_client.get_directory_system_permissions(path)
                    
                    if result.get('success'):
                        # 服务器已经过滤好的权限列表（只包含配置文件中的用户）
                        filtered_permissions = result.get('permissions', [])
                        total_permissions = result.get('total_permissions', len(filtered_permissions))
                        
                        if filtered_permissions:
                            self.perm_table.setRowCount(len(filtered_permissions))
                            
                            for row, perm in enumerate(filtered_permissions):
                                username = perm.get('username', 'N/A')
                                chinese_name = perm.get('chinese_name', 'N/A')
                                perms = perm.get('permissions', 'N/A')
                                
                                # 用户名
                                username_item = QTableWidgetItem(username)
                                username_item.setData(Qt.UserRole, perm)  # 存储完整权限信息
                                self.perm_table.setItem(row, 0, username_item)
                                
                                # 中文名
                                chinese_item = QTableWidgetItem(chinese_name)
                                self.perm_table.setItem(row, 1, chinese_item)
                                
                                # 权限
                                perm_item = QTableWidgetItem(perms)
                                # 根据权限类型设置颜色
                                if '完全控制' in perms:
                                    perm_item.setForeground(QColor('#ff6b6b'))  # 红色
                                elif '写' in perms or '删除' in perms:
                                    perm_item.setForeground(QColor('#ffd93d'))  # 黄色
                                elif '读' in perms:
                                    perm_item.setForeground(QColor('#5fb878'))  # 绿色
                                else:
                                    perm_item.setForeground(QColor('#888'))     # 灰色
                                self.perm_table.setItem(row, 2, perm_item)
                        else:
                            # 没有配置文件中的用户有权限
                            self.perm_table.setRowCount(1)
                            msg_item = QTableWidgetItem("配置文件中的用户没有访问此目录的权限")
                            msg_item.setForeground(QColor('#ffa500'))
                            self.perm_table.setItem(0, 0, msg_item)
                            self.perm_table.setSpan(0, 0, 1, 3)
                    else:
                        self.perm_table.setRowCount(1)
                        error_msg = result.get('error', result.get('message', '未知错误'))
                        error_item = QTableWidgetItem(f"加载失败: {error_msg}")
                        error_item.setForeground(QColor('#ff6b6b'))
                        self.perm_table.setItem(0, 0, error_item)
                        self.perm_table.setSpan(0, 0, 1, 3)
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    self.perm_table.setRowCount(1)
                    error_item = QTableWidgetItem(f"异常: {str(e)}")
                    error_item.setForeground(QColor('#ff6b6b'))
                    self.perm_table.setItem(0, 0, error_item)
                    self.perm_table.setSpan(0, 0, 1, 3)
            else:
                self.add_user_btn.setEnabled(False)
    
    def show_permission_context_menu(self, pos: QPoint):
        """显示权限表格的右键菜单"""
        item = self.perm_table.itemAt(pos)
        if not item or item.row() < 0:
            return
        
        # 获取用户名和权限信息
        row = item.row()
        username_item = self.perm_table.item(row, 0)
        if not username_item:
            return
        
        perm_data = username_item.data(Qt.UserRole)
        if not perm_data:
            return
        
        username = perm_data.get('username', '')
        chinese_name = perm_data.get('chinese_name', '')
        
        # 创建右键菜单
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2a2f38;
                border: 1px solid #3d4450;
                color: #e0e0e0;
            }
            QMenu::item {
                padding: 8px 20px;
            }
            QMenu::item:selected {
                background-color: #4a9eff;
            }
        """)
        
        edit_action = QAction(f"✏️ 修改 {chinese_name}({username}) 的访问权限", self)
        edit_action.triggered.connect(lambda: self.edit_user_permission(username, chinese_name))
        menu.addAction(edit_action)
        
        menu.addSeparator()
        
        delete_action = QAction(f"🗑️ 删除 {chinese_name}({username}) 对此目录的所有权限", self)
        delete_action.triggered.connect(lambda: self.remove_user_permission(username, chinese_name))
        menu.addAction(delete_action)
        
        # 显示菜单
        menu.exec_(QCursor.pos())
    
    def edit_user_permission(self, username: str, chinese_name: str):
        """修改用户的访问权限"""
        if not self.current_selected_path:
            QMessageBox.warning(self, "警告", "未选择目录")
            return
        
        if not self.permission_tab:
            QMessageBox.warning(self, "警告", "无法访问权限管理功能")
            return
        
        # 调用权限管理标签页的授予权限功能，预填充用户和路径
        self.permission_tab.grant_permission_for_user(self.current_selected_path, username, chinese_name)
    
    def remove_user_permission(self, username: str, chinese_name: str):
        """删除用户对当前目录的所有访问权限"""
        if not self.current_selected_path:
            QMessageBox.warning(self, "警告", "未选择目录")
            return
        
        if not self.permission_tab:
            QMessageBox.warning(self, "警告", "无法访问权限管理功能")
            return
        
        # 确认删除
        reply = QMessageBox.question(
            self, 
            '确认删除',
            f'确定要删除用户 {chinese_name}({username}) 对以下目录的所有访问权限吗？\n\n'
            f'目录: {self.current_selected_path}\n\n'
            f'⚠️ 此操作将移除该用户在Windows ACL中的所有权限设置！',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 调用权限管理标签页的删除权限功能
            self.permission_tab.remove_user_acl_permission(self.current_selected_path, username, chinese_name)
    
    def add_users_to_directory(self):
        """为当前目录添加用户访问权限"""
        if not self.current_selected_path:
            QMessageBox.warning(self, "警告", "未选择目录")
            return
        
        if not self.permission_tab:
            QMessageBox.warning(self, "警告", "无法访问权限管理功能")
            return
        
        # 调用权限管理标签页的授予权限功能，预填充路径
        self.permission_tab.grant_permission_for_directory(self.current_selected_path)
