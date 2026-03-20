# -*- coding: utf-8 -*-
"""
权限管理标签页 - PermissionTab
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QLabel, QComboBox,
                             QMessageBox, QDialog, QDialogButtonBox, QCheckBox,
                             QLineEdit, QTextEdit, QGroupBox, QHeaderView,
                             QFileDialog, QTreeWidget, QTreeWidgetItem,
                             QListWidget, QListWidgetItem, QInputDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from UIManagement.api_client import api_client
from UIManagement.data_models import UserPermission
from config_manager import config


class PermissionLoadWorker(QThread):
    """权限加载工作线程"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def run(self):
        try:
            result = api_client.get_all_permissions()
            if result.get('success'):
                permissions_data = result.get('data', [])
                permissions = [UserPermission.from_dict(p) for p in permissions_data]
                self.finished.emit(permissions)
            else:
                self.error.emit(result.get('error', '未知错误'))
        except Exception as e:
            self.error.emit(str(e))


class PermissionDialog(QDialog):
    """权限编辑对话框"""
    
    def __init__(self, parent=None, edit_mode=False, permission=None):
        super().__init__(parent)
        self.edit_mode = edit_mode
        self.permission = permission
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("编辑权限" if self.edit_mode else "授予权限")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # 用户名
        user_layout = QHBoxLayout()
        user_layout.addWidget(QLabel("用户名:"))
        self.username_input = QLineEdit()
        if self.permission:
            self.username_input.setText(self.permission.username)
            self.username_input.setReadOnly(self.edit_mode)
        user_layout.addWidget(self.username_input)
        layout.addLayout(user_layout)
        
        # 目录路径
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("目录路径:"))
        self.path_input = QLineEdit()
        if self.permission:
            self.path_input.setText(self.permission.directory_path)
            self.path_input.setReadOnly(self.edit_mode)
        path_layout.addWidget(self.path_input)
        layout.addLayout(path_layout)
        
        # 权限复选框
        perm_group = QGroupBox("权限设置")
        perm_layout = QVBoxLayout(perm_group)
        
        self.read_check = QCheckBox("读取权限 (Read)")
        self.write_check = QCheckBox("写入权限 (Write)")
        self.delete_check = QCheckBox("删除权限 (Delete)")
        self.execute_check = QCheckBox("执行权限 (Execute)")
        self.recursive_check = QCheckBox("递归应用到子目录")
        
        if self.permission:
            self.read_check.setChecked(self.permission.can_read)
            self.write_check.setChecked(self.permission.can_write)
            self.delete_check.setChecked(self.permission.can_delete)
            self.execute_check.setChecked(self.permission.can_execute)
            self.recursive_check.setChecked(self.permission.is_recursive)
        
        perm_layout.addWidget(self.read_check)
        perm_layout.addWidget(self.write_check)
        perm_layout.addWidget(self.delete_check)
        perm_layout.addWidget(self.execute_check)
        perm_layout.addWidget(self.recursive_check)
        
        layout.addWidget(perm_group)
        
        # 备注
        note_layout = QVBoxLayout()
        note_layout.addWidget(QLabel("备注:"))
        self.note_input = QTextEdit()
        self.note_input.setMaximumHeight(80)
        if self.permission:
            self.note_input.setText(self.permission.note)
        note_layout.addWidget(self.note_input)
        layout.addLayout(note_layout)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self._apply_dark_theme()
    
    def _apply_dark_theme(self):
        """应用深色主题"""
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1d23;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
                font-weight: bold;
            }
            QLineEdit, QTextEdit {
                background-color: #252930;
                border: 1px solid #3d4450;
                border-radius: 4px;
                padding: 6px;
                color: #e0e0e0;
            }
            QCheckBox {
                color: #e0e0e0;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QGroupBox {
                border: 1px solid #3d4450;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QPushButton {
                background-color: #3d4450;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                color: #e0e0e0;
            }
            QPushButton:hover {
                background-color: #4a9eff;
            }
        """)
    
    def get_data(self):
        """获取表单数据"""
        return {
            'username': self.username_input.text().strip(),
            'directory_path': self.path_input.text().strip(),
            'can_read': self.read_check.isChecked(),
            'can_write': self.write_check.isChecked(),
            'can_delete': self.delete_check.isChecked(),
            'can_execute': self.execute_check.isChecked(),
            'is_recursive': self.recursive_check.isChecked(),
            'note': self.note_input.toPlainText().strip()
        }


class WindowsACLDialog(QDialog):
    """授予权限对话框（支持多文件夹、多用户）"""
    
    def __init__(self, parent=None, directory_tab=None, preset_path=None, preset_users=None):
        super().__init__(parent)
        self.local_users = []
        self.directory_tab = directory_tab  # 保存目录管理标签页的引用
        # preset_path 可以是字符串或字符串列表
        if isinstance(preset_path, list):
            self.preset_paths = preset_path
        elif preset_path:
            self.preset_paths = [preset_path]
        else:
            self.preset_paths = []
        self.preset_users = preset_users or []  # 预填充用户列表
        self.init_ui()
        self.load_local_users()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("授予权限")
        self.setMinimumWidth(750)
        self.setMinimumHeight(680)
        
        layout = QVBoxLayout(self)
        
        # 文件路径（支持多个文件夹）
        path_group = QGroupBox("目标路径（支持多个文件夹）")
        path_layout = QVBoxLayout(path_group)
        
        # 路径工具栏
        path_toolbar = QHBoxLayout()
        path_toolbar.addWidget(QLabel("已选路径:"))
        path_toolbar.addStretch()
        
        browse_btn = QPushButton("📁 从目录树选择")
        browse_btn.clicked.connect(self.browse_and_add_path)
        path_toolbar.addWidget(browse_btn)
        
        manual_add_btn = QPushButton("✏️ 手动输入")
        manual_add_btn.clicked.connect(self.manual_add_path)
        path_toolbar.addWidget(manual_add_btn)
        
        remove_path_btn = QPushButton("🗑 移除选中")
        remove_path_btn.clicked.connect(self.remove_selected_paths)
        path_toolbar.addWidget(remove_path_btn)
        
        path_layout.addLayout(path_toolbar)
        
        # 路径列表（多选，允许添加多个路径）
        self.path_list = QListWidget()
        self.path_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.path_list.setMinimumHeight(100)
        path_layout.addWidget(self.path_list)
        
        self.path_count_label = QLabel("未选择路径")
        self.path_count_label.setStyleSheet("color: #888; font-size: 9pt;")
        path_layout.addWidget(self.path_count_label)
        
        layout.addWidget(path_group)
        
        # Windows用户选择（多选列表）
        user_group = QGroupBox("Windows本地用户（可多选）")
        user_layout = QVBoxLayout(user_group)
        
        # 工具栏
        user_toolbar = QHBoxLayout()
        user_toolbar.addWidget(QLabel("选择用户:"))
        user_toolbar.addStretch()
        
        refresh_users_btn = QPushButton("🔄 刷新")
        refresh_users_btn.clicked.connect(self.load_local_users)
        user_toolbar.addWidget(refresh_users_btn)
        
        select_all_btn = QPushButton("✓ 全选")
        select_all_btn.clicked.connect(self.select_all_users)
        user_toolbar.addWidget(select_all_btn)
        
        clear_btn = QPushButton("✗ 清空")
        clear_btn.clicked.connect(self.clear_user_selection)
        user_toolbar.addWidget(clear_btn)
        
        user_layout.addLayout(user_toolbar)
        
        # 用户列表（多选）
        self.user_list = QListWidget()
        self.user_list.setSelectionMode(QListWidget.MultiSelection)
        self.user_list.setMinimumHeight(150)
        user_layout.addWidget(self.user_list)
        
        # 用户信息显示
        self.user_info_label = QLabel("正在加载本地用户...")
        self.user_info_label.setStyleSheet("color: #888; font-size: 9pt;")
        user_layout.addWidget(self.user_info_label)
        
        layout.addWidget(user_group)
        
        # 权限设置
        perm_group = QGroupBox("权限配置")
        perm_layout = QVBoxLayout(perm_group)
        
        self.read_check = QCheckBox("🔍 读取权限 (Read)")
        self.write_check = QCheckBox("✏ 写入权限 (Write)")
        self.modify_check = QCheckBox("🔧 修改权限 (Modify)")
        self.full_control_check = QCheckBox("👑 完全控制 (Full Control)")
        self.recursive_check = QCheckBox("🔁 递归应用到子文件夹和文件")
        
        self.full_control_check.stateChanged.connect(self.on_full_control_changed)
        
        perm_layout.addWidget(self.read_check)
        perm_layout.addWidget(self.write_check)
        perm_layout.addWidget(self.modify_check)
        perm_layout.addWidget(self.full_control_check)
        perm_layout.addWidget(self.recursive_check)
        
        layout.addWidget(perm_group)
        
        # 提示信息
        hint_label = QLabel(
            "💡 提示:\n"
            "• 可添加多个文件夹路径，同时对所有选中文件夹设置权限\n"
            "• 可选择多个用户，同时为所有选中用户设置权限\n"
            "• 完全控制包含所有权限；修改权限包含读取、写入和删除\n"
            "• 递归选项将权限应用到所有子项"
        )
        hint_label.setStyleSheet("color: #ffa726; font-size: 9pt; padding: 10px;")
        layout.addWidget(hint_label)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self._apply_dark_theme()
        
        # 预填充路径列表
        for p in self.preset_paths:
            if p:
                self._add_path_to_list(p)
    
    def _apply_dark_theme(self):
        """应用深色主题"""
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1d23;
                color: #e0e0e0;
            }
            QGroupBox {
                border: 1px solid #3a3f47;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 15px;
                font-weight: bold;
                color: #a0cfff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                background-color: #1e2229;
            }
            QLineEdit, QComboBox {
                background-color: #2a2f38;
                border: 1px solid #3a3f47;
                border-radius: 4px;
                padding: 6px 10px;
                color: #e0e0e0;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #4a9eff;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3a4d66, stop:1 #2a3d56);
                border: 1px solid #4a5d76;
                border-radius: 4px;
                color: #e0e0e0;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a6d96, stop:1 #3a5d86);
            }
            QCheckBox {
                color: #e0e0e0;
                spacing: 8px;
            }
        """)
    
    def _add_path_to_list(self, path: str):
        """将路径添加到路径列表（避免重复）"""
        # 检查是否已存在
        for i in range(self.path_list.count()):
            if self.path_list.item(i).text() == path:
                return
        self.path_list.addItem(path)
        self._update_path_count()
    
    def _update_path_count(self):
        """更新路径数量提示"""
        count = self.path_list.count()
        if count == 0:
            self.path_count_label.setText("未选择路径")
        else:
            self.path_count_label.setText(f"✓ 已选择 {count} 个路径")
    
    def browse_and_add_path(self):
        """从目录管理的目录树中选择路径并添加到列表"""
        # 创建目录选择对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("选择服务器目录")
        dialog.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(dialog)
        
        # 提示信息
        hint = QLabel("📁 请从目录管理中的目录树选择目标路径（可多选）")
        hint.setStyleSheet("color: #4a9eff; font-weight: bold; padding: 5px;")
        layout.addWidget(hint)
        
        # 创建目录树（复制目录管理中的结构）
        tree = QTreeWidget()
        tree.setHeaderLabels(["目录名称", "路径", "共享"])
        tree.setColumnWidth(0, 250)
        tree.setColumnWidth(1, 280)
        tree.setSelectionMode(QTreeWidget.ExtendedSelection)
        layout.addWidget(tree)
        
        # 状态标签
        status_label = QLabel("")
        status_label.setStyleSheet("color: #888;")
        layout.addWidget(status_label)
        
        # 如果有目录管理标签页的引用，复制其目录树
        if self.directory_tab and hasattr(self.directory_tab, 'tree'):
            # 复制目录管理中的目录树
            source_tree = self.directory_tab.tree
            root_count = source_tree.topLevelItemCount()
            
            if root_count > 0:
                # 递归复制所有项
                for i in range(root_count):
                    source_item = source_tree.topLevelItem(i)
                    self._copy_tree_item(source_item, tree, None)
                
                status_label.setText(f"✓ 已加载 {root_count} 个目录")
                status_label.setStyleSheet("color: #5fb878;")
                
                # 展开第一层
                tree.expandToDepth(0)
            else:
                status_label.setText("⚠️ 目录管理中没有目录数据，请先在目录管理标签页中加载目录")
                status_label.setStyleSheet("color: #ffa500;")
        else:
            status_label.setText("✗ 无法访问目录管理数据，请先切换到目录管理标签页")
            status_label.setStyleSheet("color: #ff6b6b;")
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # 应用样式
        dialog.setStyleSheet("""
            QDialog {
                background-color: #1a1d23;
                color: #e0e0e0;
            }
            QTreeWidget {
                background-color: #252930;
                border: 1px solid #3d4450;
                border-radius: 4px;
                color: #ffffff;
            }
            QTreeWidget::item:selected {
                background-color: #4a9eff;
            }
            QTreeWidget::item:hover {
                background-color: #3a3f47;
            }
            QHeaderView::section {
                background-color: #2a2f38;
                color: #ffffff;
                padding: 6px;
                border: none;
                border-bottom: 2px solid #4a9eff;
                font-weight: bold;
            }
        """)
        
        # 显示对话框
        if dialog.exec_() == QDialog.Accepted:
            selected_items = tree.selectedItems()
            for selected in selected_items:
                path = selected.text(1)
                if path:
                    self._add_path_to_list(path)
    
    def manual_add_path(self):
        """手动输入路径并添加到列表"""
        path, ok = QInputDialog.getText(
            self, "手动输入路径", "请输入文件夹路径:",
            QLineEdit.Normal, ""
        )
        if ok and path.strip():
            self._add_path_to_list(path.strip())
    
    def remove_selected_paths(self):
        """移除选中的路径"""
        selected_items = self.path_list.selectedItems()
        for item in selected_items:
            row = self.path_list.row(item)
            self.path_list.takeItem(row)
        self._update_path_count()

    def browse_path(self):
        """兼容旧版调用：从目录树选择单个路径（添加到列表）"""
        self.browse_and_add_path()
    
    def _copy_tree_item(self, source_item, tree, parent_item):
        """递归复制目录树项"""
        # 复制当前项的数据
        col_count = source_item.columnCount()
        texts = [source_item.text(i) for i in range(col_count)]
        
        # 创建新项
        new_item = QTreeWidgetItem(texts)
        
        # 复制用户数据
        node_data = source_item.data(0, Qt.UserRole)
        if node_data:
            new_item.setData(0, Qt.UserRole, node_data)
        
        # 添加到树中
        if parent_item:
            parent_item.addChild(new_item)
        else:
            tree.addTopLevelItem(new_item)
        
        # 递归复制子项
        child_count = source_item.childCount()
        for i in range(child_count):
            child_item = source_item.child(i)
            self._copy_tree_item(child_item, tree, new_item)
    
    def load_local_users(self):
        """加载本地Windows用户（只显示配置文件中的用户）"""
        from config_manager import config
        
        self.user_info_label.setText("正在加载本地用户...")
        self.user_list.clear()
        
        result = api_client.get_local_users()
        
        if result.get('success'):
            users = result.get('data', [])
            self.local_users = users
            
            # 获取配置文件中的用户映射
            user_mapping = config.user_mapping
            
            # 只显示配置文件中的用户
            displayed_count = 0
            total_count = len(users)
            
            for user in users:
                username = user.get('username', '')
                is_disabled = user.get('is_disabled', False)
                
                # 检查用户名是否在配置文件中
                if username in user_mapping:
                    # 获取配置文件中的中文名
                    chinese_name = user_mapping[username]
                    
                    # 构建显示文本：用户名 (中文名)
                    display_text = f"{username} ({chinese_name})"
                    if is_disabled:
                        display_text += " [已禁用]"
                    
                    item = QListWidgetItem(display_text)
                    item.setData(Qt.UserRole, username)
                    self.user_list.addItem(item)
                    displayed_count += 1
            
            # 显示统计信息
            if displayed_count > 0:
                self.user_info_label.setText(
                    f"✓ 已加载 {displayed_count} 个配置文件中的用户（共 {total_count} 个系统用户，可按住Ctrl多选）"
                )
            else:
                self.user_info_label.setText(
                    f"⚠️ 未找到配置文件中的用户（系统共 {total_count} 个用户）"
                )
            
            # 预填充用户选择
            if self.preset_users:
                for i in range(self.user_list.count()):
                    item = self.user_list.item(i)
                    username = item.data(Qt.UserRole)
                    if username in self.preset_users:
                        item.setSelected(True)
        else:
            error = result.get('error', '未知错误')
            self.user_info_label.setText(f"✗ 加载失败: {error}")
            QMessageBox.warning(self, "警告", f"获取本地用户失败: {error}")
    
    def select_all_users(self):
        """全选用户"""
        for i in range(self.user_list.count()):
            self.user_list.item(i).setSelected(True)
    
    def clear_user_selection(self):
        """清空用户选择"""
        self.user_list.clearSelection()
    
    def on_full_control_changed(self, state):
        """完全控制选项变化"""
        if state == Qt.Checked:
            self.read_check.setChecked(True)
            self.write_check.setChecked(True)
            self.modify_check.setChecked(True)
            self.read_check.setEnabled(False)
            self.write_check.setEnabled(False)
            self.modify_check.setEnabled(False)
        else:
            self.read_check.setEnabled(True)
            self.write_check.setEnabled(True)
            self.modify_check.setEnabled(True)
    
    def accept(self):
        """验证并接受对话框"""
        # 验证至少有一个路径
        if self.path_list.count() == 0:
            QMessageBox.warning(self, "警告", "请至少添加一个文件夹路径")
            return
        
        # 验证用户选择（检查是否至少选择了一个用户）
        selected_items = self.user_list.selectedItems()
        if not selected_items or len(selected_items) == 0:
            QMessageBox.warning(self, "警告", "请至少选择一个用户")
            self.user_list.setFocus()
            return
        
        # 验证至少选择一个权限
        if not (self.read_check.isChecked() or self.write_check.isChecked() or 
                self.modify_check.isChecked() or self.full_control_check.isChecked()):
            QMessageBox.warning(self, "警告", "请至少选择一个权限")
            return
        
        # 调用父类的accept
        super().accept()
    
    def get_data(self):
        """获取表单数据"""
        # 获取所有路径
        paths = [self.path_list.item(i).text() for i in range(self.path_list.count())]
        
        # 获取所有选中的用户名
        selected_items = self.user_list.selectedItems()
        usernames = [item.data(Qt.UserRole) for item in selected_items]
        
        return {
            'paths': paths,          # 文件夹路径列表（支持多个）
            'usernames': usernames,  # 用户名列表（支持多个）
            'read': self.read_check.isChecked(),
            'write': self.write_check.isChecked(),
            'modify': self.modify_check.isChecked(),
            'full_control': self.full_control_check.isChecked(),
            'recursive': self.recursive_check.isChecked()
        }


class PermissionTab(QWidget):
    """权限管理标签页"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.permissions = []
        self.worker = None  # 保存worker引用以便清理
        self.directory_tab = None  # 目录管理标签页引用
        # 从配置文件读取
        self.current_directory = config.default_directory
        self.USERNAME_MAP = config.user_mapping
        self.init_ui()
    
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
        
        # 权限表格
        self.table = self._create_table()
        layout.addWidget(self.table, 1)
        
        # 应用深色主题
        self._apply_dark_theme()
        
        # 自动加载权限列表
        self.refresh_permissions()
    
    def _create_toolbar(self) -> QWidget:
        """创建工具栏"""
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 刷新按钮
        self.refresh_btn = QPushButton("🔄 刷新")
        self.refresh_btn.clicked.connect(self.refresh_permissions)
        layout.addWidget(self.refresh_btn)
        
        # 授予权限按钮（原Windows ACL设置）
        self.grant_btn = QPushButton("➕ 授予权限")
        self.grant_btn.clicked.connect(self.grant_permission)
        self.grant_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2e7d32, stop:1 #1b5e20);
                border: 1px solid #43a047;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #43a047, stop:1 #2e7d32);
            }
        """)
        layout.addWidget(self.grant_btn)
        
        # 撤销权限按钮
        self.revoke_btn = QPushButton("🗑 撤销权限")
        self.revoke_btn.clicked.connect(self.revoke_permission)
        layout.addWidget(self.revoke_btn)
        
        # 创建Windows用户按钮
        self.create_user_btn = QPushButton("👤 创建Windows用户")
        self.create_user_btn.clicked.connect(self.create_windows_user)
        self.create_user_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1565c0, stop:1 #0d47a1);
                border: 1px solid #1976d2;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1976d2, stop:1 #1565c0);
            }
        """)
        layout.addWidget(self.create_user_btn)
        
        # 删除Windows用户按钮
        self.delete_user_btn = QPushButton("🗑 删除Windows用户")
        self.delete_user_btn.clicked.connect(self.delete_windows_user)
        self.delete_user_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #c62828, stop:1 #8e0000);
                border: 1px solid #d32f2f;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #d32f2f, stop:1 #c62828);
            }
        """)
        layout.addWidget(self.delete_user_btn)
        
        layout.addStretch()
        
        # 筛选
        layout.addWidget(QLabel("用户筛选:"))
        self.user_filter = QComboBox()
        self.user_filter.setMinimumWidth(150)
        self.user_filter.currentTextChanged.connect(self.filter_permissions)
        layout.addWidget(self.user_filter)
        
        return toolbar
    
    def _create_table(self) -> QTableWidget:
        """创建权限表格"""
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            "用户名", "目录路径", "权限", "递归", "授予时间", "授予人", "备注"
        ])
        
        # 隐藏垂直表头（序号列）
        table.verticalHeader().setVisible(False)
        
        # 设置列宽
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.Stretch)
        
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setAlternatingRowColors(True)
        table.doubleClicked.connect(self.edit_permission)
        
        # 设置表格网格线样式
        table.setShowGrid(True)
        
        return table
    
    def _apply_dark_theme(self):
        """应用深色主题"""
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1d23;
                color: #e0e0e0;
                font-family: "Microsoft YaHei UI", "微软雅黑";
                font-size: 10pt;
            }
            QTableWidget {
                background-color: #1e2228;
                border: 1px solid #3d4450;
                border-radius: 4px;
                gridline-color: #3d4450;
                color: #ffffff;
            }
            QTableWidget::item {
                padding: 8px;
                color: #ffffff;
                background-color: #252930;
            }
            QTableWidget::item:alternate {
                background-color: #2a2f38;
            }
            QTableWidget::item:selected {
                background-color: #4a9eff;
                color: #ffffff;
            }
            QTableWidget::item:hover {
                background-color: #3d4450;
            }
            QHeaderView::section {
                background-color: #2a2f38;
                color: #ffffff;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #4a9eff;
                font-weight: bold;
                font-size: 11pt;
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
            QComboBox {
                background-color: #252930;
                border: 1px solid #3d4450;
                border-radius: 4px;
                padding: 6px;
                color: #ffffff;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #252930;
                color: #ffffff;
                selection-background-color: #4a9eff;
            }
        """)
    
    def refresh_permissions(self):
        """刷新权限列表 - 显示所有映射用户对当前目录的权限"""
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("加载中...")
        
        # 获取当前目录的权限信息
        if os.path.exists(self.current_directory):
            result = api_client.get_file_permissions(self.current_directory)
            
            if result.get('success'):
                permissions_data = result.get('permissions', [])
                
                # 创建所有映射用户的权限记录
                all_permissions = []
                for username, display_name in self.USERNAME_MAP.items():
                    # 查找该用户在权限数据中的记录
                    user_perm = next((p for p in permissions_data if p.get('username', '').lower() == username.lower()), None)
                    
                    # 创建权限对象
                    perm_dict = {
                        'username': username,
                        'directory_path': self.current_directory if user_perm else '',
                        'can_read': False,
                        'can_write': False,
                        'can_delete': False,
                        'can_execute': False,
                        'is_recursive': False,
                        'granted_at': '',
                        'granted_by': '',
                        'note': ''
                    }
                    
                    # 如果找到权限信息，解析权限
                    if user_perm:
                        perms_str = user_perm.get('permissions', '')
                        perm_dict['can_read'] = '读' in perms_str
                        perm_dict['can_write'] = '写' in perms_str
                        perm_dict['can_delete'] = '删除' in perms_str or '完全控制' in perms_str
                        perm_dict['can_execute'] = '执行' in perms_str
                        perm_dict['granted_at'] = '当前'
                        perm_dict['granted_by'] = 'system'
                        perm_dict['note'] = perms_str
                    
                    all_permissions.append(UserPermission.from_dict(perm_dict))
                
                self.permissions = all_permissions
                self.update_table(all_permissions)
                self.update_user_filter()
            else:
                # 如果获取失败，仍显示所有映射用户但路径为空
                all_permissions = []
                for username, display_name in self.USERNAME_MAP.items():
                    perm_dict = {
                        'username': username,
                        'directory_path': '',
                        'can_read': False,
                        'can_write': False,
                        'can_delete': False,
                        'can_execute': False,
                        'is_recursive': False,
                        'granted_at': '',
                        'granted_by': '',
                        'note': '无权限'
                    }
                    all_permissions.append(UserPermission.from_dict(perm_dict))
                
                self.permissions = all_permissions
                self.update_table(all_permissions)
                self.update_user_filter()
        else:
            # 目录不存在，显示所有映射用户但路径为空
            all_permissions = []
            for username, display_name in self.USERNAME_MAP.items():
                perm_dict = {
                    'username': username,
                    'directory_path': '',
                    'can_read': False,
                    'can_write': False,
                    'can_delete': False,
                    'can_execute': False,
                    'is_recursive': False,
                    'granted_at': '',
                    'granted_by': '',
                    'note': '目录不存在'
                }
                all_permissions.append(UserPermission.from_dict(perm_dict))
            
            self.permissions = all_permissions
            self.update_table(all_permissions)
            self.update_user_filter()
        
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("🔄 刷新")
    
    def set_current_directory(self, directory: str):
        """设置当前目录并刷新权限"""
        self.current_directory = directory
        self.refresh_permissions()
    
    def on_permissions_loaded(self, permissions):
        """权限加载完成"""
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("🔄 刷新")
        
        self.permissions = permissions
        self.update_table(permissions)
        self.update_user_filter()
    
    def on_load_error(self, error):
        """加载错误"""
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("🔄 刷新")
        QMessageBox.critical(self, "错误", f"加载权限失败: {error}")
    
    def update_table(self, permissions):
        """更新表格"""
        self.table.setRowCount(0)
        
        for perm in permissions:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # 应用用户名映射
            display_username = self.get_display_username(perm.username)
            
            self.table.setItem(row, 0, QTableWidgetItem(display_username))
            self.table.setItem(row, 1, QTableWidgetItem(perm.directory_path))
            self.table.setItem(row, 2, QTableWidgetItem(perm.to_permission_string()))
            self.table.setItem(row, 3, QTableWidgetItem("是" if perm.is_recursive else "否"))
            self.table.setItem(row, 4, QTableWidgetItem(perm.granted_at))
            self.table.setItem(row, 5, QTableWidgetItem(perm.granted_by))
            self.table.setItem(row, 6, QTableWidgetItem(perm.note))
            
            # 存储权限对象
            self.table.item(row, 0).setData(Qt.UserRole, perm)
    
    def get_display_username(self, username):
        """获取显示用户名（如果有映射则显示中文名）"""
        return self.USERNAME_MAP.get(username, username)
    
    def update_user_filter(self):
        """更新用户筛选 - 只显示映射字典中的用户"""
        current_user = self.user_filter.currentText()
        
        self.user_filter.clear()
        self.user_filter.addItem("全部用户")
        
        # 只显示映射字典中的用户
        for username in sorted(self.USERNAME_MAP.keys()):
            display_name = self.get_display_username(username)
            self.user_filter.addItem(display_name, username)  # 显示名，实际值
        
        if current_user and current_user in [self.user_filter.itemText(i) for i in range(self.user_filter.count())]:
            self.user_filter.setCurrentText(current_user)
    
    def filter_permissions(self):
        """筛选权限"""
        filter_display_name = self.user_filter.currentText()
        
        if filter_display_name == "全部用户":
            filtered = self.permissions
        else:
            # 获取当前选中项的实际用户名
            current_index = self.user_filter.currentIndex()
            if current_index > 0:  # 跳过"全部用户"
                actual_username = self.user_filter.itemData(current_index)
                filtered = [p for p in self.permissions if p.username == actual_username]
            else:
                filtered = self.permissions
        
        self.update_table(filtered)
    
    def grant_permission(self):
        """授予权限（调用Windows ACL设置）"""
        self.set_windows_acl()
    
    def grant_permission_for_user(self, path: str, username: str, chinese_name: str):
        """为指定用户修改权限（从目录管理右键菜单调用）"""
        dialog = WindowsACLDialog(self, directory_tab=self.directory_tab, 
                                 preset_path=path, preset_users=[username])
        if dialog.exec_() == QDialog.Accepted:
            self._execute_acl_setting(dialog.get_data())
    
    def grant_permission_for_directory(self, path: str):
        """为目录添加用户（从目录管理"+"按钮调用）"""
        dialog = WindowsACLDialog(self, directory_tab=self.directory_tab, preset_path=path)
        if dialog.exec_() == QDialog.Accepted:
            self._execute_acl_setting(dialog.get_data())
    
    def remove_user_acl_permission(self, path: str, username: str, chinese_name: str):
        """删除用户对目录的Windows ACL权限（从目录管理右键菜单调用）"""
        result = api_client.remove_file_permission(
            file_path=path,
            username=username
        )
        
        if result.get('success'):
            QMessageBox.information(
                self, 
                "成功", 
                f"已删除用户 {chinese_name}({username}) 对目录的所有访问权限\n\n"
                f"路径: {path}"
            )
            # 刷新目录管理中的权限显示
            if self.directory_tab:
                # 触发重新加载当前目录的权限信息
                current_item = self.directory_tab.tree.currentItem()
                if current_item:
                    self.directory_tab.on_tree_item_clicked(current_item, 0)
        else:
            error_msg = result.get('error') or result.get('message', '未知错误')
            QMessageBox.critical(
                self, 
                "失败", 
                f"删除用户权限失败\n\n"
                f"用户: {chinese_name}({username})\n"
                f"路径: {path}\n\n"
                f"错误: {error_msg}"
            )
    
    def edit_permission(self):
        """编辑权限"""
        current_row = self.table.currentRow()
        if current_row < 0:
            return
        
        perm = self.table.item(current_row, 0).data(Qt.UserRole)
        if not perm:
            return
        
        dialog = PermissionDialog(self, edit_mode=True, permission=perm)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            
            # 更新权限
            result = api_client.grant_permission(
                username=perm.username,
                directory_path=perm.directory_path,
                can_read=data['can_read'],
                can_write=data['can_write'],
                can_delete=data['can_delete'],
                can_execute=data['can_execute'],
                is_recursive=data['is_recursive'],
                note=data['note']
            )
            
            if result.get('success'):
                QMessageBox.information(self, "成功", "权限更新成功")
                self.refresh_permissions()
            else:
                QMessageBox.critical(self, "错误", f"更新权限失败: {result.get('error')}")
    
    def set_windows_acl(self):
        """设置Windows ACL权限（授予权限）"""
        dialog = WindowsACLDialog(self, directory_tab=self.directory_tab)
        if dialog.exec_() == QDialog.Accepted:
            self._execute_acl_setting(dialog.get_data())
    
    def _execute_acl_setting(self, data: dict):
        """执行ACL权限设置（批量处理：多文件夹 × 多用户）"""
        # 获取权限参数（布尔值）
        read = data['read']
        write = data['write']
        modify = data['modify']
        full_control = data['full_control']
        recursive = data['recursive']
        paths = data.get('paths', [])
        usernames = data.get('usernames', [])
        
        # 验证至少选择一项权限
        if not (read or write or modify or full_control):
            QMessageBox.warning(self, "警告", "请至少选择一项权限")
            return
        
        if not paths:
            QMessageBox.warning(self, "警告", "请至少选择一个文件夹路径")
            return
        
        if not usernames:
            QMessageBox.warning(self, "警告", "请至少选择一个用户")
            return
        
        # 构建权限描述（用于显示）
        permissions_desc = []
        if full_control:
            permissions_desc.append('完全控制')
        elif modify:
            permissions_desc.append('修改')
        else:
            if read:
                permissions_desc.append('读取')
            if write:
                permissions_desc.append('写入')
        
        # 使用批量接口：多文件夹 × 多用户
        result = api_client.set_file_permissions_batch(
            file_paths=paths,
            usernames=usernames,
            read=read,
            write=write,
            modify=modify,
            full_control=full_control,
            recursive=recursive
        )
        
        total = len(paths) * len(usernames)
        
        # 如果批量接口返回了 success_count，说明新接口可用
        batch_api_available = 'success_count' in result
        
        if batch_api_available:
            success_count = result.get('success_count', 0)
            fail_count = result.get('fail_count', 0)
            failed_items = [
                f"{r['file_path']} / {r['username']}: {r.get('message', '')}"
                for r in result.get('results', [])
                if not r.get('success')
            ]
        else:
            # 服务器不支持批量接口，回退到逐个调用
            success_count = 0
            failed_items = []
            for path in paths:
                for username in usernames:
                    r = api_client.set_file_permission(
                        file_path=path,
                        username=username,
                        read=read,
                        write=write,
                        modify=modify,
                        full_control=full_control,
                        recursive=recursive
                    )
                    if r.get('success'):
                        success_count += 1
                    else:
                        err = r.get('error') or r.get('message', '未知错误')
                        failed_items.append(f"{path} / {username}: {err}")
            fail_count = total - success_count
        
        # 显示结果
        path_summary = paths[0] if len(paths) == 1 else f"{paths[0]} 等 {len(paths)} 个路径"
        if fail_count == 0:
            QMessageBox.information(self, "成功", 
                f"已为 {len(usernames)} 个用户、{len(paths)} 个文件夹设置权限\n"
                f"路径: {path_summary}\n"
                f"权限: {', '.join(permissions_desc)}")
        elif success_count > 0:
            QMessageBox.warning(self, "部分成功", 
                f"成功: {success_count} 项\n"
                f"失败: {fail_count} 项\n\n"
                f"失败详情:\n" + "\n".join(failed_items[:5]))
        else:
            QMessageBox.critical(self, "失败", 
                f"所有权限设置均失败\n\n" + "\n".join(failed_items[:5]))
        
        self.refresh_permissions()
    
    def revoke_permission(self):
        """撤销权限"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "请选择要撤销的权限")
            return
        
        perm = self.table.item(current_row, 0).data(Qt.UserRole)
        if not perm:
            return
        
        reply = QMessageBox.question(
            self, '确认',
            f'确定要撤销用户 {perm.username} 对 {perm.directory_path} 的权限吗?',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            result = api_client.revoke_permission(perm.username, perm.directory_path)
            
            if result.get('success'):
                QMessageBox.information(self, "成功", "权限已撤销")
                self.refresh_permissions()
            else:
                QMessageBox.critical(self, "错误", f"撤销权限失败: {result.get('error')}")
    
    def create_windows_user(self):
        """创建Windows用户"""
        dialog = CreateUserDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            result = api_client.create_local_user(
                username=data['username'],
                password=data['password'],
                fullname=data['fullname'],
                comment=data['comment']
            )
            
            if result.get('success'):
                # 同步更新配置文件中的用户映射
                username = data['username']
                fullname = data['fullname'] if data['fullname'] else username
                
                try:
                    # 更新内存中的映射
                    config.user_mapping[username] = fullname
                    # 保存到配置文件
                    config.save_config()
                    # 刷新本地映射
                    self.USERNAME_MAP = config.user_mapping
                    
                    QMessageBox.information(
                        self, 
                        "成功", 
                        f"{result.get('message', '用户创建成功')}\n已同步更新配置文件"
                    )
                    # 刷新权限表格
                    self.refresh_permissions()
                except Exception as e:
                    QMessageBox.warning(
                        self,
                        "部分成功",
                        f"用户创建成功，但更新配置文件失败: {str(e)}"
                    )
            else:
                QMessageBox.critical(
                    self, 
                    "错误", 
                    result.get('message', '创建用户失败')
                )
    
    def delete_windows_user(self):
        """删除Windows用户"""
        dialog = DeleteUserDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            username = dialog.get_username()
            
            # 检查用户是否在配置文件中
            if username not in config.user_mapping:
                QMessageBox.warning(
                    self,
                    "警告",
                    f"用户 \"{username}\" 不在配置文件中，无法删除"
                )
                return
            
            # 检查用户是否存在于Windows系统中
            user_exists_in_system = dialog.user_exists_in_system(username)
            
            # 构建确认消息
            if user_exists_in_system:
                confirm_msg = f'确定要删除Windows用户 "{username}" 吗？\n\n此操作不可恢复！\n将同时删除：\n• Windows系统用户\n• 配置文件中的用户映射'
            else:
                confirm_msg = f'用户 "{username}" 仅存在于配置文件中。\n\n确定要从配置文件中移除该用户映射吗？'
            
            # 二次确认
            reply = QMessageBox.question(
                self,
                '确认删除',
                confirm_msg,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                success_msg = []
                error_msg = []
                
                # 尝试删除Windows用户
                if user_exists_in_system:
                    result = api_client.delete_local_user(username)
                    if result.get('success'):
                        success_msg.append("Windows用户已删除")
                    else:
                        error_msg.append(f"删除Windows用户失败: {result.get('message', '未知错误')}")
                
                # 从配置文件中移除用户映射
                try:
                    del config.user_mapping[username]
                    config.save_config()
                    # 刷新本地映射
                    self.USERNAME_MAP = config.user_mapping
                    success_msg.append("已从配置文件中移除")
                except Exception as e:
                    error_msg.append(f"更新配置文件失败: {str(e)}")
                
                # 显示结果
                if success_msg and not error_msg:
                    QMessageBox.information(
                        self,
                        "成功",
                        "删除成功！\n" + "\n".join(success_msg)
                    )
                    # 刷新权限表格
                    self.refresh_permissions()
                elif success_msg and error_msg:
                    QMessageBox.warning(
                        self,
                        "部分成功",
                        "操作部分完成：\n\n成功：\n" + "\n".join(success_msg) + "\n\n失败：\n" + "\n".join(error_msg)
                    )
                    # 即使部分成功也刷新
                    self.refresh_permissions()
                else:
                    QMessageBox.critical(
                        self,
                        "失败",
                        "删除失败：\n" + "\n".join(error_msg)
                    )


class DeleteUserDialog(QDialog):
    """删除Windows用户对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.local_users = []
        self.init_ui()
        self.load_local_users()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("删除Windows用户")
        self.setMinimumWidth(450)
        
        layout = QVBoxLayout(self)
        
        # 警告信息
        warning_label = QLabel("⚠️ 警告：删除用户操作不可恢复，请谨慎操作！")
        warning_label.setStyleSheet("color: #ff6b6b; font-size: 11pt; font-weight: bold; padding: 10px;")
        layout.addWidget(warning_label)
        
        # 用户选择
        user_layout = QVBoxLayout()
        user_layout.addWidget(QLabel("选择要删除的用户:"))
        
        self.user_combo = QComboBox()
        self.user_combo.setMinimumWidth(350)
        user_layout.addWidget(self.user_combo)
        
        # 用户信息显示
        self.user_info_label = QLabel("正在加载本地用户...")
        self.user_info_label.setStyleSheet("color: #888; font-size: 9pt;")
        user_layout.addWidget(self.user_info_label)
        
        layout.addLayout(user_layout)
        
        # 提示信息
        hint_label = QLabel(
            "提示:\n"
            "• 删除用户会永久移除该用户账户\n"
            "• 该用户的所有数据和设置将被删除\n"
            "• 建议删除前先备份重要数据"
        )
        hint_label.setStyleSheet("color: #888; font-size: 9pt; padding: 10px;")
        hint_label.setWordWrap(True)
        layout.addWidget(hint_label)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # 应用样式
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1d23;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
            }
            QComboBox {
                background-color: #252930;
                border: 1px solid #3d4450;
                border-radius: 4px;
                padding: 6px;
                color: #e0e0e0;
            }
            QPushButton {
                background-color: #3d4450;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                color: #e0e0e0;
            }
            QPushButton:hover {
                background-color: #c62828;
            }
        """)
    
    def load_local_users(self):
        """加载配置文件中的所有用户"""
        self.user_info_label.setText("正在加载用户列表...")
        self.user_combo.clear()
        
        # 获取Windows系统用户
        result = api_client.get_local_users()
        system_users = {}
        
        if result.get('success'):
            users = result.get('data', [])
            self.local_users = users
            # 创建系统用户字典，便于查找
            for user in users:
                username = user.get('username', '')
                system_users[username] = user
        
        # 遍历配置文件中的所有用户
        config_users = config.user_mapping
        
        if not config_users:
            self.user_info_label.setText("✗ 配置文件中没有用户")
            return
        
        for username, fullname in config_users.items():
            # 检查用户是否存在于系统中
            if username in system_users:
                user_info = system_users[username]
                is_disabled = user_info.get('is_disabled', False)
                display_text = f"{username} ({fullname})"
                if is_disabled:
                    display_text += " [已禁用]"
            else:
                # 用户不在系统中，只在配置文件中
                display_text = f"{username} ({fullname}) [仅配置文件]"
            
            self.user_combo.addItem(display_text, username)
        
        count = self.user_combo.count()
        self.user_info_label.setText(f"✓ 已加载 {count} 个可删除用户（配置文件中的所有用户）")
    
    def accept(self):
        """验证并接受"""
        if self.user_combo.count() == 0:
            QMessageBox.warning(self, "警告", "没有可删除的用户")
            return
        
        if self.user_combo.currentIndex() < 0:
            QMessageBox.warning(self, "警告", "请选择要删除的用户")
            return
        
        super().accept()
    
    def get_username(self):
        """获取选中的用户名"""
        return self.user_combo.currentData()
    
    def user_exists_in_system(self, username):
        """检查用户是否存在于Windows系统中"""
        for user in self.local_users:
            if user.get('username', '') == username:
                return True
        return False


class CreateUserDialog(QDialog):
    """创建Windows用户对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("创建Windows用户")
        self.setMinimumWidth(450)
        
        layout = QVBoxLayout(self)
        
        # 用户名
        username_layout = QHBoxLayout()
        username_layout.addWidget(QLabel("用户名 *:"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("请输入用户名（必填）")
        username_layout.addWidget(self.username_input)
        layout.addLayout(username_layout)
        
        # 密码
        password_layout = QHBoxLayout()
        password_layout.addWidget(QLabel("密码 *:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("请输入密码（必填，至少8位）")
        password_layout.addWidget(self.password_input)
        layout.addLayout(password_layout)
        
        # 确认密码
        confirm_layout = QHBoxLayout()
        confirm_layout.addWidget(QLabel("确认密码 *:"))
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.setPlaceholderText("请再次输入密码")
        confirm_layout.addWidget(self.confirm_input)
        layout.addLayout(confirm_layout)
        
        # 全名
        fullname_layout = QHBoxLayout()
        fullname_layout.addWidget(QLabel("全名:"))
        self.fullname_input = QLineEdit()
        self.fullname_input.setPlaceholderText("请输入全名（可选）")
        fullname_layout.addWidget(self.fullname_input)
        layout.addLayout(fullname_layout)
        
        # 描述
        comment_layout = QVBoxLayout()
        comment_layout.addWidget(QLabel("描述:"))
        self.comment_input = QTextEdit()
        self.comment_input.setMaximumHeight(80)
        self.comment_input.setPlaceholderText("请输入用户描述（可选）")
        comment_layout.addWidget(self.comment_input)
        layout.addLayout(comment_layout)
        
        # 提示信息
        hint_label = QLabel("提示：密码必须符合Windows系统密码策略（通常至少8位，包含大小写字母、数字）")
        hint_label.setStyleSheet("color: #888; font-size: 9pt;")
        hint_label.setWordWrap(True)
        layout.addWidget(hint_label)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # 应用样式
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1d23;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
            }
            QLineEdit, QTextEdit {
                background-color: #252930;
                border: 1px solid #3d4450;
                border-radius: 4px;
                padding: 6px;
                color: #e0e0e0;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 1px solid #4a9eff;
            }
            QPushButton {
                background-color: #3d4450;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                color: #e0e0e0;
            }
            QPushButton:hover {
                background-color: #4a9eff;
            }
        """)
    
    def accept(self):
        """验证并接受"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        confirm = self.confirm_input.text()
        
        # 验证用户名
        if not username:
            QMessageBox.warning(self, "警告", "请输入用户名")
            self.username_input.setFocus()
            return
        
        # 验证密码
        if not password:
            QMessageBox.warning(self, "警告", "请输入密码")
            self.password_input.setFocus()
            return
        
        if len(password) < 8:
            QMessageBox.warning(self, "警告", "密码长度至少为8位")
            self.password_input.setFocus()
            return
        
        if password != confirm:
            QMessageBox.warning(self, "警告", "两次输入的密码不一致")
            self.confirm_input.setFocus()
            return
        
        super().accept()
    
    def get_data(self):
        """获取表单数据"""
        return {
            'username': self.username_input.text().strip(),
            'password': self.password_input.text(),
            'fullname': self.fullname_input.text().strip(),
            'comment': self.comment_input.toPlainText().strip()
        }

