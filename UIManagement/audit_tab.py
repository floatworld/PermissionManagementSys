# -*- coding: utf-8 -*-
"""
审计日志标签页 - AuditTab
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QLabel, QLineEdit,
                             QDateTimeEdit, QComboBox, QGroupBox, QHeaderView,
                             QMessageBox, QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QDateTime
from PyQt5.QtGui import QColor
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from UIManagement.api_client import api_client
from UIManagement.data_models import AuditRecord


class AuditLoadWorker(QThread):
    """审计日志加载工作线程"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, username=None, action_type=None, file_path=None, 
                 start_time=None, end_time=None, limit=1000):
        super().__init__()
        self.username = username
        self.action_type = action_type
        self.file_path = file_path
        self.start_time = start_time
        self.end_time = end_time
        self.limit = limit
    
    def run(self):
        try:
            result = api_client.get_audit_logs(
                username=self.username,
                action_type=self.action_type,
                file_path=self.file_path,
                start_time=self.start_time,
                end_time=self.end_time,
                limit=self.limit
            )
            
            if result.get('success'):
                logs_data = result.get('data', [])
                logs = [AuditRecord.from_dict(log) for log in logs_data]
                self.finished.emit(logs)
            else:
                self.error.emit(result.get('error', '未知错误'))
        except Exception as e:
            self.error.emit(str(e))


class AuditTab(QWidget):
    """审计日志标签页"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logs = []
        self.worker = None  # 保存worker引用以便清理
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
        
        # 查询表单
        query_form = self._create_query_form()
        layout.addWidget(query_form)
        
        # 统计信息栏
        self.stats_widget = self._create_stats_widget()
        layout.addWidget(self.stats_widget)
        
        # 日志表格
        self.table = self._create_table()
        layout.addWidget(self.table, 1)
        
        # 应用深色主题
        self._apply_dark_theme()
        
        # 初始化统计标签
        self.total_label.setText("总计: 0 条")
        self.success_label.setText("成功: 0")
        self.fail_label.setText("失败: 0")
        self.success_rate_bar.setValue(0)
        self.top_actions_label.setText("暂无数据")
        
        # 自动加载日志
        self.query_logs()
    
    def _create_query_form(self) -> QWidget:
        """创建查询表单"""
        group = QGroupBox("查询条件")
        layout = QVBoxLayout(group)
        
        # 第一行 - 用户名和操作类型
        row1 = QHBoxLayout()
        
        row1.addWidget(QLabel("用户名:"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("输入用户名筛选")
        self.username_input.setMaximumWidth(200)
        row1.addWidget(self.username_input)
        
        row1.addWidget(QLabel("操作类型:"))
        self.action_combo = QComboBox()
        self.action_combo.addItems([
            "全部",
            "授予权限", "撤销权限", "创建文件", "删除文件",
            "修改文件", "移动文件", "创建目录", "删除目录"
        ])
        self.action_combo.setMaximumWidth(150)
        row1.addWidget(self.action_combo)
        
        row1.addStretch()
        layout.addLayout(row1)
        
        # 第二行 - 文件路径
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("文件路径:"))
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("输入文件路径筛选")
        row2.addWidget(self.path_input)
        layout.addLayout(row2)
        
        # 第三行 - 时间范围
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("时间范围:"))
        
        self.start_time = QDateTimeEdit()
        self.start_time.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.start_time.setDateTime(QDateTime.currentDateTime().addDays(-7))
        self.start_time.setMaximumWidth(180)
        row3.addWidget(self.start_time)
        
        row3.addWidget(QLabel("至"))
        
        self.end_time = QDateTimeEdit()
        self.end_time.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.end_time.setDateTime(QDateTime.currentDateTime())
        self.end_time.setMaximumWidth(180)
        row3.addWidget(self.end_time)
        
        row3.addWidget(QLabel("记录数:"))
        self.limit_combo = QComboBox()
        self.limit_combo.addItems(["100", "500", "1000", "5000"])
        self.limit_combo.setCurrentText("1000")
        self.limit_combo.setMaximumWidth(100)
        row3.addWidget(self.limit_combo)
        
        row3.addStretch()
        layout.addLayout(row3)
        
        # 按钮行
        btn_row = QHBoxLayout()
        
        self.query_btn = QPushButton("🔍 查询")
        self.query_btn.clicked.connect(self.query_logs)
        btn_row.addWidget(self.query_btn)
        
        self.refresh_btn = QPushButton("🔄 刷新")
        self.refresh_btn.clicked.connect(self.refresh_logs)
        btn_row.addWidget(self.refresh_btn)
        
        self.export_btn = QPushButton("📥 导出")
        self.export_btn.clicked.connect(self.export_logs)
        btn_row.addWidget(self.export_btn)
        
        self.stats_btn = QPushButton("📊 统计")
        self.stats_btn.clicked.connect(self.show_statistics)
        btn_row.addWidget(self.stats_btn)
        
        btn_row.addStretch()
        layout.addLayout(btn_row)
        
        return group
    
    def _create_stats_widget(self) -> QWidget:
        """创建统计信息组件"""
        widget = QGroupBox("日志统计")
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        
        # 第一行：总数和成功率
        row1 = QHBoxLayout()
        
        self.total_label = QLabel("总计: 0 条")
        self.total_label.setStyleSheet("color: #4a9eff; font-weight: bold; font-size: 11pt;")
        row1.addWidget(self.total_label)
        
        row1.addSpacing(20)
        
        self.success_label = QLabel("成功: 0")
        self.success_label.setStyleSheet("color: #4ade80; font-weight: bold;")
        row1.addWidget(self.success_label)
        
        self.fail_label = QLabel("失败: 0")
        self.fail_label.setStyleSheet("color: #f87171; font-weight: bold;")
        row1.addWidget(self.fail_label)
        
        # 成功率进度条
        row1.addSpacing(10)
        row1.addWidget(QLabel("成功率:"))
        self.success_rate_bar = QProgressBar()
        self.success_rate_bar.setMaximumHeight(20)
        self.success_rate_bar.setMaximumWidth(150)
        self.success_rate_bar.setFormat("%p%")
        self.success_rate_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #3d4450;
                border-radius: 3px;
                background-color: #252930;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #4ade80;
                border-radius: 2px;
            }
        """)
        row1.addWidget(self.success_rate_bar)
        
        row1.addStretch()
        layout.addLayout(row1)
        
        # 第二行：主要操作统计
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("主要操作:"))
        self.top_actions_label = QLabel("加载中...")
        self.top_actions_label.setStyleSheet("color: #e0e0e0;")
        row2.addWidget(self.top_actions_label)
        row2.addStretch()
        layout.addLayout(row2)
        
        return widget
    
    def _create_table(self) -> QTableWidget:
        """创建日志表格"""
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            "时间", "用户", "操作类型", "文件路径", "状态", "IP地址", "详情"
        ])
        
        # 设置列宽
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.Stretch)
        
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setAlternatingRowColors(True)
        
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
            QGroupBox {
                border: 1px solid #3d4450;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                color: #4a9eff;
            }
            QTableWidget {
                background-color: #1e2228;
                border: 1px solid #3d4450;
                border-radius: 4px;
                gridline-color: #3d4450;
            }
            QTableWidget::item {
                padding: 8px;
                color: #ffffff;
                border-bottom: 1px solid #2a2f38;
            }
            QTableWidget::item:selected {
                background-color: #4a9eff;
                color: white;
            }
            QTableWidget::item:alternate {
                background-color: #252930;
            }
            QHeaderView::section {
                background-color: #2a2f38;
                color: #ffffff;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #4a9eff;
                font-weight: bold;
                font-size: 10pt;
            }
            QLineEdit, QComboBox, QDateTimeEdit {
                background-color: #252930;
                border: 1px solid #3d4450;
                border-radius: 4px;
                padding: 6px;
                color: #e0e0e0;
            }
            QLineEdit:focus, QComboBox:focus, QDateTimeEdit:focus {
                border: 1px solid #4a9eff;
            }
            QPushButton {
                background-color: #3d4450;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                color: #e0e0e0;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4a9eff;
            }
            QPushButton:pressed {
                background-color: #3d8fe0;
            }
            QPushButton:disabled {
                background-color: #2a2f38;
                color: #6a6a6a;
            }
        """)
    
    def query_logs(self):
        """查询日志"""
        self.query_btn.setEnabled(False)
        self.query_btn.setText("查询中...")
        
        username = self.username_input.text().strip() or None
        action_type = self.action_combo.currentText()
        if action_type == "全部":
            action_type = None
        
        file_path = self.path_input.text().strip() or None
        start_time = self.start_time.dateTime().toString("yyyy-MM-dd HH:mm:ss") if self.start_time else None
        end_time = self.end_time.dateTime().toString("yyyy-MM-dd HH:mm:ss") if self.end_time else None
        limit = int(self.limit_combo.currentText())
        
        self.worker = AuditLoadWorker(username, action_type, file_path, start_time, end_time, limit)
        self.worker.finished.connect(self.on_logs_loaded)
        self.worker.error.connect(self.on_load_error)
        self.worker.start()
    
    def refresh_logs(self):
        """刷新日志(无筛选)"""
        self.username_input.clear()
        self.action_combo.setCurrentIndex(0)
        self.path_input.clear()
        self.query_logs()
    
    def on_logs_loaded(self, logs):
        """日志加载完成"""
        self.query_btn.setEnabled(True)
        self.query_btn.setText("🔍 查询")
        
        self.logs = logs
        self.update_table(logs)
        self.update_statistics(logs)
    
    def on_load_error(self, error):
        """加载错误"""
        self.query_btn.setEnabled(True)
        self.query_btn.setText("🔍 查询")
        QMessageBox.critical(self, "错误", f"加载日志失败: {error}")
    
    def update_table(self, logs):
        """更新表格"""
        self.table.setRowCount(0)
        self.table.verticalHeader().setVisible(False)  # 隐藏序号列
        
        for log in logs:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # 时间
            time_item = QTableWidgetItem(log.get_formatted_time())
            self.table.setItem(row, 0, time_item)
            
            # 用户
            user_item = QTableWidgetItem(log.username or 'N/A')
            self.table.setItem(row, 1, user_item)
            
            # 操作类型
            action_item = QTableWidgetItem(log.action_type)
            self.table.setItem(row, 2, action_item)
            
            # 文件路径
            path_item = QTableWidgetItem(log.file_path)
            self.table.setItem(row, 3, path_item)
            
            # 状态 - 使用颜色区分
            status_item = QTableWidgetItem(log.get_status_text())
            if log.success:
                status_item.setForeground(QColor("#4ade80"))  # 绿色
            else:
                status_item.setForeground(QColor("#f87171"))  # 红色
            self.table.setItem(row, 4, status_item)
            
            # IP地址
            ip_item = QTableWidgetItem(log.ip_address or 'N/A')
            self.table.setItem(row, 5, ip_item)
            
            # 详情
            details_item = QTableWidgetItem(log.details)
            self.table.setItem(row, 6, details_item)
            
            # 存储日志对象
            time_item.setData(Qt.UserRole, log)
    
    def update_statistics(self, logs):
        """更新统计信息"""
        total = len(logs)
        
        if total == 0:
            self.total_label.setText("总计: 0 条")
            self.success_label.setText("成功: 0")
            self.fail_label.setText("失败: 0")
            self.success_rate_bar.setValue(0)
            self.top_actions_label.setText("暂无数据")
            return
        
        success_count = sum(1 for log in logs if log.success)
        fail_count = total - success_count
        success_rate = int((success_count / total) * 100) if total > 0 else 0
        
        # 更新基本统计
        self.total_label.setText(f"总计: {total} 条")
        self.success_label.setText(f"成功: {success_count}")
        self.fail_label.setText(f"失败: {fail_count}")
        self.success_rate_bar.setValue(success_rate)
        
        # 统计操作类型
        action_counts = {}
        for log in logs:
            action_counts[log.action_type] = action_counts.get(log.action_type, 0) + 1
        
        # 获取Top 3操作
        top_actions = sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        if top_actions:
            actions_list = []
            for action, count in top_actions:
                percentage = int((count / total) * 100)
                actions_list.append(f"{action} {count}次({percentage}%)")
            self.top_actions_label.setText(" | ".join(actions_list))
        else:
            self.top_actions_label.setText("暂无数据")
    
    def export_logs(self):
        """导出日志"""
        if not self.logs:
            QMessageBox.warning(self, "警告", "没有可导出的日志")
            return
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"audit_logs_{timestamp}.csv"
        
        try:
            with open(filename, 'w', encoding='utf-8-sig') as f:
                # 写入表头
                f.write("时间,用户,操作类型,文件路径,状态,IP地址,详情\n")
                
                # 写入数据
                for log in self.logs:
                    f.write(f'"{log.get_formatted_time()}",'
                           f'"{log.username}",'
                           f'"{log.action_type}",'
                           f'"{log.file_path}",'
                           f'"{log.get_status_text()}",'
                           f'"{log.ip_address}",'
                           f'"{log.details}"\n')
            
            QMessageBox.information(self, "成功", f"日志已导出到: {filename}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
    
    def show_statistics(self):
        """显示统计信息"""
        result = api_client.get_audit_statistics()
        
        if result.get('success'):
            stats = result.get('data', {})
            
            msg = f"""
<h3>审计统计信息</h3>
<table style="width:100%; border-collapse:collapse;">
<tr><td style="color:#4a9eff;font-weight:bold;padding:5px;">总日志数:</td><td>{stats.get('total_logs', 0)}</td></tr>
<tr><td style="color:#4a9eff;font-weight:bold;padding:5px;">成功率:</td><td>{stats.get('success_rate', 0)}%</td></tr>
</table>

<h4>操作类型统计:</h4>
<table style="width:100%; border-collapse:collapse;">
"""
            for action, count in stats.get('action_counts', {}).items():
                msg += f'<tr><td style="padding:3px;">{action}</td><td style="text-align:right;">{count} 次</td></tr>'
            
            msg += """
</table>

<h4>用户活跃度 (Top 5):</h4>
<table style="width:100%; border-collapse:collapse;">
"""
            user_counts = sorted(stats.get('user_counts', {}).items(), key=lambda x: x[1], reverse=True)[:5]
            for user, count in user_counts:
                msg += f'<tr><td style="padding:3px;">{user}</td><td style="text-align:right;">{count} 次</td></tr>'
            
            msg += "</table>"
            
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("审计统计")
            msg_box.setTextFormat(Qt.RichText)
            msg_box.setText(msg)
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #1a1d23;
                }
                QLabel {
                    color: #e0e0e0;
                    min-width: 500px;
                }
            """)
            msg_box.exec_()
        else:
            QMessageBox.critical(self, "错误", f"获取统计信息失败: {result.get('error')}")
