# -*- coding: utf-8 -*-
"""
航空权限管理系统 - 专业航空软件风格 UI
上位机控制端，通过局域网与服务器通信
"""
import os
import sys
import json
from datetime import datetime
import logging
import requests

# Ensure repo root on sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
import config  # noqa: E402

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSettings, QTimer, QDateTime
from PyQt5.QtGui import QFont, QColor, QPalette
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QComboBox, QCheckBox,
    QFileDialog, QMessageBox, QLabel, QGroupBox, QHeaderView, QStatusBar,
    QSplitter, QTextEdit, QFrame
)


class AuditLog:
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.logger = logging.getLogger("PermissionAuditQt")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            log_file = os.path.join(log_dir, f'audit_{datetime.now().strftime("%Y%m%d")}.log')
            fh = logging.FileHandler(log_file, encoding="utf-8")
            fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(fh)

    def log_action(self, action_type, username, details, operator="系统"):
        message = f"操作者: {operator} | 动作: {action_type} | 目标用户: {username} | 详情: {details}"
        self.logger.info(message)
        return message


class ApiWorker(QThread):
    finished = pyqtSignal(object, object)  # (data, error)

    def __init__(self, method: str, path: str, *, base_url: str = None, params=None, json_data=None, timeout=10):
        super().__init__()
        self.method = method
        self.path = path
        self.base_url = base_url
        self.params = params or {}
        self.json_data = json_data
        self.timeout = timeout

    def run(self):
        base = self.base_url or getattr(config, 'SERVER_URL', 'http://localhost:5000')
        url = f"{base}{self.path}"
        try:
            if self.method == 'GET':
                r = requests.get(url, params=self.params, timeout=self.timeout)
            elif self.method == 'POST':
                r = requests.post(url, json=self.json_data, timeout=self.timeout)
            elif self.method == 'DELETE':
                r = requests.delete(url, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported method: {self.method}")
            try:
                data = r.json()
            except Exception:
                data = r.text
            if not (200 <= r.status_code < 300):
                self.finished.emit(None, data)
            else:
                self.finished.emit(data, None)
        except Exception as e:
            self.finished.emit(None, str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🛫 航空权限管理系统 - 控制中心")
        self.resize(1400, 900)
        self.audit_log = AuditLog(log_dir=os.path.join(os.path.dirname(__file__), 'logs'))
        self._workers = []
        self._is_connected = False
        self._heartbeat_timer = QTimer(self)
        self._heartbeat_timer.timeout.connect(self._check_connection)
        self._perm_data = []

        self._init_ui()
        self._wire_events()
        self._apply_aviation_theme()
        
        try:
            self.load_settings()
        except Exception:
            pass
        
        self.log_message("系统启动完成，等待连接服务器...")

    def _init_ui(self):
        central = QWidget(self)
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._create_top_status_bar(main_layout)
        self._create_connection_bar(main_layout)
        self._create_main_workspace(main_layout)
        self._create_log_panel(main_layout)
        
        self.statusBar = QStatusBar(self)
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("就绪")

    def _create_top_status_bar(self, parent_layout):
        """顶部状态栏"""
        top_bar = QFrame()
        top_bar.setObjectName("topStatusBar")
        top_bar.setFixedHeight(40)
        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(15, 5, 15, 5)
        
        title = QLabel("🛫 航空权限管理系统 - 控制中心")
        title.setObjectName("systemTitle")
        layout.addWidget(title)
        layout.addStretch()
        
        self.lbl_sys_time = QLabel()
        self.lbl_sys_time.setObjectName("sysTime")
        self._update_system_time()
        self.time_timer = QTimer(self)
        self.time_timer.timeout.connect(self._update_system_time)
        self.time_timer.start(1000)
        layout.addWidget(self.lbl_sys_time)
        
        user_label = QLabel("👤 操作员: admin")
        user_label.setObjectName("userInfo")
        layout.addWidget(user_label)
        
        parent_layout.addWidget(top_bar)

    def _create_connection_bar(self, parent_layout):
        """服务器连接控制栏"""
        conn_frame = QFrame()
        conn_frame.setObjectName("connectionBar")
        conn_frame.setFixedHeight(60)
        layout = QHBoxLayout(conn_frame)
        layout.setContentsMargins(15, 10, 15, 10)
        
        layout.addWidget(QLabel("🌐 服务器地址:"))
        
        self.ed_base_url = QLineEdit()
        self.ed_base_url.setPlaceholderText("http://192.168.110.77:5000")
        self.ed_base_url.setFixedWidth(300)
        layout.addWidget(self.ed_base_url)
        
        self.btn_connect = QPushButton("🔌 连接")
        self.btn_connect.setObjectName("connectBtn")
        self.btn_connect.setFixedWidth(100)
        layout.addWidget(self.btn_connect)
        
        self.btn_disconnect = QPushButton("🔌 断开")
        self.btn_disconnect.setObjectName("disconnectBtn")
        self.btn_disconnect.setFixedWidth(100)
        self.btn_disconnect.setEnabled(False)
        layout.addWidget(self.btn_disconnect)
        
        self.lbl_led = QLabel("●")
        self.lbl_led.setObjectName("ledIndicator")
        self.lbl_led.setStyleSheet("color: #757575; font-size: 24px;")
        layout.addWidget(self.lbl_led)
        
        self.lbl_conn_status = QLabel("未连接")
        self.lbl_conn_status.setObjectName("connStatus")
        layout.addWidget(self.lbl_conn_status)
        
        layout.addStretch()
        
        self.btn_refresh_all = QPushButton("🔄 刷新数据")
        self.btn_refresh_all.setObjectName("refreshBtn")
        self.btn_refresh_all.setEnabled(False)
        layout.addWidget(self.btn_refresh_all)
        
        parent_layout.addWidget(conn_frame)

    def _create_main_workspace(self, parent_layout):
        """主工作区"""
        splitter = QSplitter(Qt.Horizontal)
        
        left_panel = self._create_permission_list_panel()
        splitter.addWidget(left_panel)
        
        right_panel = self._create_operation_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([800, 600])
        parent_layout.addWidget(splitter, stretch=1)

    def _create_permission_list_panel(self):
        """权限列表面板"""
        panel = QFrame()
        panel.setObjectName("leftPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        header = QHBoxLayout()
        title = QLabel("📋 权限列表")
        title.setObjectName("panelTitle")
        header.addWidget(title)
        header.addStretch()
        
        self.ed_filter = QLineEdit()
        self.ed_filter.setPlaceholderText("🔍 搜索用户名/路径...")
        self.ed_filter.setFixedWidth(250)
        header.addWidget(self.ed_filter)
        layout.addLayout(header)
        
        self.table_perm = QTableWidget(0, 4)
        self.table_perm.setObjectName("permissionTable")
        self.table_perm.setHorizontalHeaderLabels(["用户名", "权限级别", "目标路径", "最后修改"])
        self.table_perm.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_perm.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_perm.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table_perm.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table_perm.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_perm.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_perm.setSortingEnabled(True)
        self.table_perm.setAlternatingRowColors(True)
        layout.addWidget(self.table_perm)
        
        btn_layout = QHBoxLayout()
        self.btn_refresh = QPushButton("🔄 刷新")
        self.btn_delete = QPushButton("🗑️ 删除选中")
        self.btn_delete.setObjectName("deleteBtn")
        btn_layout.addWidget(self.btn_refresh)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        return panel

    def _create_operation_panel(self):
        """右侧操作面板"""
        panel = QFrame()
        panel.setObjectName("rightPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("⚙️ 权限操作")
        title.setObjectName("panelTitle")
        layout.addWidget(title)
        
        form_group = QGroupBox("权限配置")
        form_layout = QVBoxLayout(form_group)
        
        row = QHBoxLayout()
        row.addWidget(QLabel("用户名:"))
        self.ed_username = QLineEdit()
        row.addWidget(self.ed_username)
        form_layout.addLayout(row)
        
        row = QHBoxLayout()
        row.addWidget(QLabel("目标路径:"))
        self.ed_path = QLineEdit()
        row.addWidget(self.ed_path)
        self.btn_browse = QPushButton("📁")
        self.btn_browse.setFixedWidth(40)
        row.addWidget(self.btn_browse)
        self.btn_browse_file = QPushButton("📄")
        self.btn_browse_file.setFixedWidth(40)
        row.addWidget(self.btn_browse_file)
        form_layout.addLayout(row)
        
        row = QHBoxLayout()
        row.addWidget(QLabel("权限级别:"))
        self.cmb_permission = QComboBox()
        self.cmb_permission.addItems(["读取", "写入", "修改", "完全控制"])
        row.addWidget(self.cmb_permission)
        form_layout.addLayout(row)
        
        row = QHBoxLayout()
        self.chk_is_dir = QCheckBox("目标为文件夹")
        self.chk_recursive = QCheckBox("递归应用")
        row.addWidget(self.chk_is_dir)
        row.addWidget(self.chk_recursive)
        row.addStretch()
        form_layout.addLayout(row)
        
        row = QHBoxLayout()
        row.addWidget(QLabel("备注:"))
        self.ed_note = QLineEdit()
        row.addWidget(self.ed_note)
        form_layout.addLayout(row)
        
        layout.addWidget(form_group)
        
        btn_layout = QHBoxLayout()
        self.btn_submit = QPushButton("✅ 提交")
        self.btn_submit.setObjectName("submitBtn")
        self.btn_reset = QPushButton("🔄 重置")
        btn_layout.addWidget(self.btn_submit)
        btn_layout.addWidget(self.btn_reset)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        query_group = QGroupBox("路径访问查询")
        query_layout = QVBoxLayout(query_group)
        
        self.btn_view_users = QPushButton("🔍 查看有权访问的用户")
        query_layout.addWidget(self.btn_view_users)
        
        self.table_users = QTableWidget(0, 6)
        self.table_users.setObjectName("usersTable")
        self.table_users.setHorizontalHeaderLabels(["用户名", "权限", "目录", "递归", "路径", "修改时间"])
        self.table_users.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table_users.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_users.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_users.setMaximumHeight(200)
        query_layout.addWidget(self.table_users)
        
        layout.addWidget(query_group)
        layout.addStretch()
        
        return panel

    def _create_log_panel(self, parent_layout):
        """底部日志面板"""
        log_frame = QFrame()
        log_frame.setObjectName("logPanel")
        log_frame.setMaximumHeight(150)
        layout = QVBoxLayout(log_frame)
        layout.setContentsMargins(10, 5, 10, 5)
        
        header = QHBoxLayout()
        title = QLabel("📝 操作日志")
        title.setObjectName("logTitle")
        header.addWidget(title)
        header.addStretch()
        
        self.btn_clear_log = QPushButton("🗑️ 清空")
        self.btn_clear_log.setFixedWidth(80)
        header.addWidget(self.btn_clear_log)
        layout.addLayout(header)
        
        self.txt_log = QTextEdit()
        self.txt_log.setObjectName("logText")
        self.txt_log.setReadOnly(True)
        self.txt_log.setMaximumHeight(120)
        layout.addWidget(self.txt_log)
        
        parent_layout.addWidget(log_frame)

    def _wire_events(self):
        self.btn_refresh.clicked.connect(self.refresh_permissions)
        self.btn_delete.clicked.connect(self.delete_permission)
        self.btn_browse.clicked.connect(self.browse_path)
        self.btn_browse_file.clicked.connect(self.browse_file)
        self.btn_reset.clicked.connect(self.reset_form)
        self.btn_submit.clicked.connect(self.submit_permission)
        self.btn_view_users.clicked.connect(self.view_path_users)
        self.btn_connect.clicked.connect(self.on_connect_clicked)
        self.btn_disconnect.clicked.connect(self.on_disconnect_clicked)
        self.btn_refresh_all.clicked.connect(self.refresh_all_data)
        self.btn_clear_log.clicked.connect(self.clear_log)
        self.ed_filter.textChanged.connect(self.apply_filter)
        self.table_perm.cellDoubleClicked.connect(self.on_perm_row_dblclick)
        self.table_users.cellDoubleClicked.connect(self.on_users_row_dblclick)

    def _apply_aviation_theme(self):
        """应用航空专业深色主题"""
        self.setStyleSheet("""
            QMainWindow { background-color: #1a1d23; }
            QWidget {
                background-color: #1a1d23;
                color: #e0e0e0;
                font-family: "Consolas", "Microsoft YaHei", monospace;
                font-size: 10pt;
            }
            #topStatusBar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2a3f5f, stop:1 #1a2332);
                border-bottom: 2px solid #4a9eff;
            }
            #systemTitle {
                font-size: 14pt;
                font-weight: bold;
                color: #4a9eff;
            }
            #sysTime, #userInfo {
                color: #a0cfff;
                font-size: 9pt;
                padding: 0 10px;
            }
            #connectionBar {
                background-color: #242830;
                border-bottom: 1px solid #3a3f47;
            }
            #connStatus {
                color: #ffa726;
                font-weight: bold;
            }
            #leftPanel, #rightPanel {
                background-color: #1e2229;
                border: 1px solid #2d3139;
                border-radius: 4px;
            }
            #panelTitle {
                font-size: 12pt;
                font-weight: bold;
                color: #4a9eff;
                padding: 5px 0;
            }
            QTableWidget {
                background-color: #242830;
                alternate-background-color: #2a2f38;
                gridline-color: #3a3f47;
                border: 1px solid #3a3f47;
                border-radius: 4px;
                selection-background-color: #3d5a80;
                color: #e0e0e0;
            }
            QTableWidget::item:hover {
                background-color: #2d3d52;
            }
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3a4552, stop:1 #2a3340);
                color: #a0cfff;
                padding: 6px;
                border: none;
                border-right: 1px solid #4a5562;
                border-bottom: 2px solid #4a9eff;
                font-weight: bold;
            }
            QLineEdit {
                background-color: #2a2f38;
                border: 1px solid #3a3f47;
                border-radius: 4px;
                padding: 6px 10px;
                color: #e0e0e0;
                selection-background-color: #3d5a80;
            }
            QLineEdit:focus {
                border: 2px solid #4a9eff;
                background-color: #2d3240;
            }
            QComboBox {
                background-color: #2a2f38;
                border: 1px solid #3a3f47;
                border-radius: 4px;
                padding: 6px 10px;
                color: #e0e0e0;
            }
            QComboBox:hover {
                border: 1px solid #4a9eff;
            }
            QComboBox QAbstractItemView {
                background-color: #2a2f38;
                border: 1px solid #4a9eff;
                selection-background-color: #3d5a80;
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
            #connectBtn {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2e7d32, stop:1 #1b5e20);
                border: 1px solid #43a047;
            }
            #connectBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #43a047, stop:1 #2e7d32);
            }
            #disconnectBtn {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #d32f2f, stop:1 #b71c1c);
                border: 1px solid #e57373;
            }
            #submitBtn {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1976d2, stop:1 #0d47a1);
                border: 1px solid #2196f3;
            }
            #deleteBtn {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #d84315, stop:1 #bf360c);
                border: 1px solid #ff5722;
            }
            #refreshBtn {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0288d1, stop:1 #01579b);
                border: 1px solid #03a9f4;
            }
            QCheckBox {
                color: #e0e0e0;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #3a3f47;
                border-radius: 3px;
                background-color: #2a2f38;
            }
            QCheckBox::indicator:checked {
                background-color: #4a9eff;
                border-color: #4a9eff;
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
            #logPanel {
                background-color: #1a1d23;
                border-top: 2px solid #3a3f47;
            }
            #logTitle {
                font-size: 10pt;
                font-weight: bold;
                color: #ffa726;
            }
            #logText {
                background-color: #0d0f13;
                border: 1px solid #2a2d33;
                border-radius: 4px;
                color: #a0a0a0;
                font-family: "Consolas", monospace;
                font-size: 9pt;
                padding: 5px;
            }
            QStatusBar {
                background-color: #1a1d23;
                color: #808080;
                border-top: 1px solid #2a2d33;
            }
            QSplitter::handle {
                background-color: #3a3f47;
                width: 2px;
            }
            QSplitter::handle:hover {
                background-color: #4a9eff;
            }
            QScrollBar:vertical {
                background-color: #1a1d23;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #3a3f47;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #4a5562;
            }
        """)

    # === 辅助工具方法 ===
    def _update_system_time(self):
        self.lbl_sys_time.setText(f"⏰ {QDateTime.currentDateTime().toString('yyyy-MM-dd HH:mm:ss')}")

    def log_message(self, msg, level="INFO"):
        """记录操作日志到底部面板"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = {"INFO": "#a0cfff", "SUCCESS": "#66bb6a", "ERROR": "#ef5350", "WARNING": "#ffa726"}.get(level, "#a0a0a0")
        self.txt_log.append(f'<span style="color:{color}">[{timestamp}] {msg}</span>')
        self.txt_log.ensureCursorVisible()

    def clear_log(self):
        self.txt_log.clear()
        self.log_message("日志已清空")

    def set_connection_status(self, connected: bool):
        """设置连接状态"""
        self._is_connected = connected
        if connected:
            self.lbl_led.setStyleSheet("color: #66bb6a; font-size: 24px;")
            self.lbl_conn_status.setText("已连接")
            self.lbl_conn_status.setStyleSheet("color: #66bb6a; font-weight: bold;")
            self.btn_connect.setEnabled(False)
            self.btn_disconnect.setEnabled(True)
            self.btn_refresh_all.setEnabled(True)
            self._heartbeat_timer.start(30000)
            self.log_message("服务器连接成功", "SUCCESS")
        else:
            self.lbl_led.setStyleSheet("color: #ef5350; font-size: 24px;")
            self.lbl_conn_status.setText("未连接")
            self.lbl_conn_status.setStyleSheet("color: #ef5350; font-weight: bold;")
            self.btn_connect.setEnabled(True)
            self.btn_disconnect.setEnabled(False)
            self.btn_refresh_all.setEnabled(False)
            self._heartbeat_timer.stop()
            self.log_message("服务器连接断开", "WARNING")

    def _check_connection(self):
        """心跳检测"""
        def _done(data, err):
            if err is not None:
                self.set_connection_status(False)
                self.log_message("心跳检测失败，连接已断开", "ERROR")
        self._start_worker('GET', '/health', cb=_done, timeout=3)

    # === 网络请求 ===
    def _start_worker(self, method, path, *, params=None, json_data=None, cb=None, timeout=10):
        worker = ApiWorker(method, path, base_url=self.get_base_url(), params=params, json_data=json_data, timeout=timeout)
        worker.finished.connect(cb or (lambda data, err: None))
        worker.finished.connect(lambda *_: self._workers.remove(worker) if worker in self._workers else None)
        self._workers.append(worker)
        worker.start()

    def get_base_url(self):
        url = self.ed_base_url.text().strip()
        return url or getattr(config, 'SERVER_URL', 'http://localhost:5000')

    def get_settings(self):
        return QSettings('AviationPermMgmt', 'PyQtClient')

    def load_settings(self):
        s = self.get_settings()
        base = s.value('server/base_url', type=str)
        if not base:
            base = os.environ.get('PERM_SERVER_URL') or getattr(config, 'SERVER_URL', 'http://localhost:5000')
        self.ed_base_url.setText(base)

    def save_settings(self):
        s = self.get_settings()
        s.setValue('server/base_url', self.ed_base_url.text().strip())

    # === 连接管理 ===
    def on_connect_clicked(self):
        self.save_settings()
        self.log_message(f"正在连接服务器 {self.get_base_url()}...")
        def _done(data, err):
            if err is None:
                self.set_connection_status(True)
                self.refresh_permissions()
            else:
                self.set_connection_status(False)
                QMessageBox.critical(self, "连接失败", f"无法连接到服务器:\n{err}")
        self._start_worker('GET', '/health', cb=_done, timeout=5)

    def on_disconnect_clicked(self):
        self.set_connection_status(False)

    def refresh_all_data(self):
        if not self._is_connected:
            QMessageBox.warning(self, "警告", "请先连接服务器")
            return
        self.refresh_permissions()
        self.log_message("数据刷新完成", "SUCCESS")

    # === 权限管理 ===
    def refresh_permissions(self):
        if not self._is_connected:
            return
        self.log_message("正在刷新权限列表...")
        def _done(data, err):
            if err is not None:
                QMessageBox.critical(self, "错误", f"获取权限列表失败: {err}")
                self.log_message(f"获取权限失败: {err}", "ERROR")
                self.set_connection_status(False)
                return
            rows = data if isinstance(data, list) else []
            self._perm_data = rows
            self.populate_permissions(rows)
            self.log_message(f"权限列表已更新，共 {len(rows)} 条", "SUCCESS")
        self._start_worker('GET', '/permissions', cb=_done, timeout=8)

    def populate_permissions(self, rows):
        sorting = self.table_perm.isSortingEnabled()
        self.table_perm.setSortingEnabled(False)
        self.table_perm.setRowCount(0)
        for perm in rows:
            r = self.table_perm.rowCount()
            self.table_perm.insertRow(r)
            self.table_perm.setItem(r, 0, QTableWidgetItem(str(perm.get('username', ''))))
            self.table_perm.setItem(r, 1, QTableWidgetItem(str(perm.get('permission', ''))))
            self.table_perm.setItem(r, 2, QTableWidgetItem(str(perm.get('path', ''))))
            self.table_perm.setItem(r, 3, QTableWidgetItem(str(perm.get('last_modified', ''))))
        self.table_perm.setSortingEnabled(sorting)

    def apply_filter(self):
        text = self.ed_filter.text().strip().lower()
        if not hasattr(self, '_perm_data'):
            return
        if not text:
            self.populate_permissions(self._perm_data)
            return
        def match(perm):
            return any(text in str(perm.get(k, '')).lower() for k in ('username', 'permission', 'path'))
        filtered = [p for p in self._perm_data if match(p)]
        self.populate_permissions(filtered)

    def submit_permission(self):
        if not self._is_connected:
            QMessageBox.warning(self, "警告", "请先连接服务器")
            return
        username = self.ed_username.text().strip()
        path = self.ed_path.text().strip()
        permission = self.cmb_permission.currentText()
        note = self.ed_note.text().strip()
        is_dir = self.chk_is_dir.isChecked()
        recursive = self.chk_recursive.isChecked()

        if not username:
            QMessageBox.warning(self, "警告", "请输入用户名")
            return
        if not path:
            QMessageBox.warning(self, "警告", "请选择目标文件或目录路径")
            return

        payload = {
            "username": username,
            "permission": permission,
            "path": path,
            "is_directory": bool(is_dir),
            "recursive": bool(recursive),
            "note": note,
        }
        self.log_message(f"正在为用户 {username} 设置权限...")
        def _done(data, err):
            if err is not None:
                QMessageBox.critical(self, "错误", f"设置权限失败: {err}")
                self.log_message(f"设置权限失败: {err}", "ERROR")
                return
            self.audit_log.log_action("添加/修改权限", username, f"设置权限为: {permission}, 备注: {note}, 路径: {path}", operator="admin")
            QMessageBox.information(self, "成功", "权限设置成功")
            self.log_message(f"权限设置成功: {username} - {permission}", "SUCCESS")
            self.reset_form()
            self.refresh_permissions()
        self._start_worker('POST', '/permissions', json_data=payload, cb=_done, timeout=15)

    def delete_permission(self):
        if not self._is_connected:
            QMessageBox.warning(self, "警告", "请先连接服务器")
            return
        row = self.table_perm.currentRow()
        if row < 0:
            QMessageBox.warning(self, "警告", "请先选择要删除的项")
            return
        username = self.table_perm.item(row, 0).text() if self.table_perm.item(row, 0) else ""
        if not username:
            QMessageBox.warning(self, "警告", "未能解析所选行的用户名")
            return
        reply = QMessageBox.question(self, "确认", f"确定要删除用户 {username} 的权限吗？", 
                                       QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        self.log_message(f"正在删除用户 {username} 的权限...")
        def _done(data, err):
            if err is not None:
                QMessageBox.critical(self, "错误", f"删除权限失败: {err}")
                self.log_message(f"删除权限失败: {err}", "ERROR")
                return
            self.audit_log.log_action("删除权限", username, f"删除权限", operator="admin")
            QMessageBox.information(self, "成功", "权限删除成功")
            self.log_message(f"权限删除成功: {username}", "SUCCESS")
            self.refresh_permissions()
        self._start_worker('DELETE', f'/permissions/{username}', cb=_done, timeout=8)

    def browse_path(self):
        directory = QFileDialog.getExistingDirectory(self, "选择文件夹", os.path.expanduser("~"))
        if directory:
            self.ed_path.setText(directory)
            self.chk_is_dir.setChecked(True)

    def browse_file(self):
        fname, _ = QFileDialog.getOpenFileName(self, "选择文件", os.path.expanduser("~"))
        if fname:
            self.ed_path.setText(fname)
            self.chk_is_dir.setChecked(False)

    def view_path_users(self):
        if not self._is_connected:
            QMessageBox.warning(self, "警告", "请先连接服务器")
            return
        path = self.ed_path.text().strip()
        if not path:
            QMessageBox.warning(self, "警告", "请先选择目标文件夹路径")
            return
        self.log_message(f"正在查询路径 {path} 的访问用户...")
        def _done(data, err):
            if err is not None:
                QMessageBox.critical(self, "错误", f"查询访问用户失败: {err}")
                self.log_message(f"查询失败: {err}", "ERROR")
                return
            rows = data if isinstance(data, list) else []
            self.table_users.setRowCount(0)
            for u in rows:
                r = self.table_users.rowCount()
                self.table_users.insertRow(r)
                self.table_users.setItem(r, 0, QTableWidgetItem(str(u.get('username', ''))))
                self.table_users.setItem(r, 1, QTableWidgetItem(str(u.get('permission', ''))))
                self.table_users.setItem(r, 2, QTableWidgetItem(str(u.get('is_directory', False))))
                self.table_users.setItem(r, 3, QTableWidgetItem(str(u.get('recursive', False))))
                self.table_users.setItem(r, 4, QTableWidgetItem(str(u.get('path', ''))))
                self.table_users.setItem(r, 5, QTableWidgetItem(str(u.get('last_modified', ''))))
            self.log_message(f"查询完成，共 {len(rows)} 个用户", "SUCCESS")
        self._start_worker('GET', '/permissions/by-path', params={'path': path}, cb=_done, timeout=8)

    def on_perm_row_dblclick(self, row, _col):
        def get(col):
            item = self.table_perm.item(row, col)
            return item.text() if item else ""
        username = get(0)
        permission = get(1)
        path = get(2)
        self.ed_username.setText(username)
        idx = self.cmb_permission.findText(permission)
        if idx >= 0:
            self.cmb_permission.setCurrentIndex(idx)
        self.ed_path.setText(path)
        self.ed_note.setText("")
        self.log_message(f"已加载用户 {username} 的权限信息")

    def on_users_row_dblclick(self, row, _col):
        def get(col):
            item = self.table_users.item(row, col)
            return item.text() if item else ""
        username = get(0)
        permission = get(1)
        path = get(4)
        is_dir = get(2).lower() in ("true", "1", "yes")
        recursive = get(3).lower() in ("true", "1", "yes")
        self.ed_username.setText(username)
        idx = self.cmb_permission.findText(permission)
        if idx >= 0:
            self.cmb_permission.setCurrentIndex(idx)
        self.ed_path.setText(path)
        self.chk_is_dir.setChecked(is_dir)
        self.chk_recursive.setChecked(recursive)
        self.ed_note.setText("")

    def reset_form(self):
        self.ed_username.setText("")
        self.cmb_permission.setCurrentIndex(0)
        self.ed_note.setText("")


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 使用 Fusion 样式基础
    win = MainWindow()
    win.show()
    win.audit_log.log_action("系统启动", "system", "航空权限管理系统启动", operator="系统")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
