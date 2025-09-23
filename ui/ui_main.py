import os
import platform
import re
import subprocess

import qtawesome as qta
from PyQt5.QtCore import QSettings, Qt, QSize, QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QTextEdit, QListWidget, \
    QListWidgetItem, QSizePolicy, QDialog, QMainWindow, QMessageBox, QApplication, \
    QSpacerItem, QCheckBox, QSpinBox, QInputDialog

from manager.device_manager import DeviceManager
from manager.history_manager import HistoryManager
from manager.log_manager import LogManager
from manager.serial_manager import SerialManager
from manager.theme_manager import ThemeManager
from thread.automation_thread import AutomationThread
from thread.serial_receiver import SerialReceiver
from ui.setting_dialog import SettingsDialog


class SerialTool(QMainWindow):
    def __init__(self):
        super().__init__()

        # 设置无边框窗口
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint | Qt.WindowTitleHint)
        # 启用窗口移动
        self._is_dragging = False
        self._drag_position = None

        # 添加重启标志
        self.need_restart = False

        # 重复发送
        self.repeat_send = False
        self.sending_flag = False

        self.setWindowTitle("硬件测试上位机 v1.0")
        self.resize(1200, 850)

        # 串口管理
        self.serial = SerialManager()
        self.history = HistoryManager()
        self.log_mgr = LogManager()
        self.device_mgr = DeviceManager()
        # 设置
        self.settings = QSettings("settings.ini", QSettings.IniFormat)
        # 初始化主题管理器
        self.theme_manager = ThemeManager(QApplication.instance())
        # self.update_log_path()
        self.auto_thread = None
        self.receiver_thread = None
        self._is_port_open = False

        # 当前硬件配置
        self.current_device = None
        self.device_config = {}

        # 创建状态栏
        self.statusBar().showMessage("就绪")
        self.serial_status_label = QLabel("🔴 串口未连接")
        self.statusBar().addPermanentWidget(self.serial_status_label)

        # 设置中心窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建串口UI
        self.setup_serial_ui(central_widget)

        # 创建自定义标题栏
        self.setup_custom_titlebar()

        # 初始化时加载一次
        self.load_initial_settings()
        self.refresh_ports()
        self.load_history_ui()

    def setup_serial_ui(self, central_widget):
        # UI 布局
        layout = QVBoxLayout()

        # ----------------------串口选择 & 打开 ------------------------------------
        # 串口选择 & 打开
        port_layout = QHBoxLayout()
        port_cb_label = QLabel("端口:")
        port_cb_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        port_layout.addWidget(port_cb_label)
        self.port_cb = QComboBox()
        self.port_cb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        port_layout.addWidget(self.port_cb)
        # 波特率
        port_layout.addWidget(QLabel("波特率:"))
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.baudrate_combo.addItems(
            ["110", "300", "600", "1200", "2400", "4800", "9600", "14400", "19200", "38400", "56000", "57600", "115200",
             "128000", "230400", "256000", "460800", "921600", ])
        self.baudrate_combo.setEditable(True)  # ✅ 用户可输入自定义波特率
        self.baudrate_combo.setCurrentText("115200")  # 设置默认值为115200
        port_layout.addWidget(self.baudrate_combo)
        # 数据位
        port_layout.addWidget(QLabel("数据位:"))
        self.bytesize_combo = QComboBox()
        self.bytesize_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.bytesize_combo.addItems(["5", "6", "7", "8"])
        self.bytesize_combo.setCurrentText("8")
        port_layout.addWidget(self.bytesize_combo)
        # 校验位
        port_layout.addWidget(QLabel("校验:"))
        self.parity_combo = QComboBox()
        self.parity_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.parity_combo.addItems(["N", "E", "O", "M", "S"])  # None, Even, Odd, Mark, Space
        self.parity_combo.setCurrentText("N")
        port_layout.addWidget(self.parity_combo)
        # 停止位
        port_layout.addWidget(QLabel("停止位:"))
        self.stopbits_combo = QComboBox()
        self.stopbits_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.stopbits_combo.addItems(["1", "1.5", "2"])
        self.stopbits_combo.setCurrentText("1")
        port_layout.addWidget(self.stopbits_combo)
        # 刷新串口按钮
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.refresh_ports)
        port_layout.addWidget(self.refresh_btn)
        # 打开/关闭串口按钮
        self.open_btn = QPushButton("打开串口")
        self.open_btn.clicked.connect(self.toggle_serial)
        port_layout.addWidget(self.open_btn)
        layout.addLayout(port_layout)

        # ---------- 硬件配置 & 导入 ----------
        device_layout = QHBoxLayout()
        self.device_cb = QComboBox()
        self.device_cb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.load_devices()
        self.save_device_btn = QPushButton("保存指令集")
        self.save_device_btn.clicked.connect(self.save_device_commands)
        self.import_btn = QPushButton("导入指令文件")
        self.import_btn.clicked.connect(self.import_commands)
        label = QLabel("硬件配置:")
        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        device_layout.addWidget(label)
        device_layout.addWidget(self.device_cb)
        self.add_device_btn = QPushButton("增加硬件配置")
        self.add_device_btn.clicked.connect(self.add_device)
        self.del_device_btn = QPushButton("删除硬件配置")
        self.del_device_btn.clicked.connect(self.del_device)
        device_layout.addWidget(self.add_device_btn)
        device_layout.addWidget(self.del_device_btn)
        device_layout.addWidget(self.save_device_btn)
        device_layout.addWidget(self.import_btn)
        layout.addLayout(device_layout)

        # ----------------------- 历史命令 ------------------------
        lists_layout = QHBoxLayout()
        # 指令列表
        left_col = QVBoxLayout()
        left_col.addWidget(QLabel("指令列表 (双击发送):"))
        self.delete_cmdlist_btn = QPushButton("删除选中指令")
        self.delete_cmdlist_btn.clicked.connect(self.delete_cmdlist_item)
        cmd_layout = QHBoxLayout()
        cmd_layout.addWidget(self.delete_cmdlist_btn)
        self.cmd_list = QListWidget()
        self.cmd_list.itemDoubleClicked.connect(self.send_list_item_command)
        self.device_cb.currentIndexChanged.connect(self.change_device)
        left_col.addLayout(cmd_layout)
        left_col.addWidget(self.cmd_list)

        # 历史命令列表
        right_col = QVBoxLayout()
        right_col.addWidget(QLabel("历史记录 (双击发送):"))
        self.add_history_btn = QPushButton("添加到指令列表")
        self.delete_history_btn = QPushButton("删除选中记录")
        self.clear_history_btn = QPushButton("清空历史记录")
        self.add_history_btn.clicked.connect(self.add_history_to_cmdlist)
        self.delete_history_btn.clicked.connect(self.delete_selected_history)
        self.clear_history_btn.clicked.connect(self.clear_history)

        history_layout = QHBoxLayout()
        history_layout.addWidget(self.add_history_btn)
        history_layout.addWidget(self.delete_history_btn)
        history_layout.addWidget(self.clear_history_btn)
        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self.send_list_item_command)
        right_col.addLayout(history_layout)
        right_col.addWidget(self.history_list)
        lists_layout.addLayout(left_col, 2)
        lists_layout.addLayout(right_col, 1)
        layout.addLayout(lists_layout)

        # ----------------------- 自动化 ------------------------
        # 自动化控制
        auto_layout = QHBoxLayout()
        # 日志保存按钮
        self.save_log_btn = QPushButton("打开日志文件夹")
        self.save_log_btn.clicked.connect(self.open_log_dir)
        self.start_auto_btn = QPushButton("开始自动化")
        self.start_auto_btn.clicked.connect(self.start_automation)
        self.stop_auto_btn = QPushButton("停止自动化")
        self.stop_auto_btn.clicked.connect(self.stop_automation)
        self.stop_auto_btn.setEnabled(False)
        auto_layout.addWidget(self.save_log_btn)
        auto_layout.addWidget(self.start_auto_btn)
        auto_layout.addWidget(self.stop_auto_btn)
        layout.addLayout(auto_layout)

        # 当前日志文件路径显示
        self.log_path_label = QLabel(f"ℹ 当前日志文件: {self.log_mgr.log_file}")
        self.statusBar().addPermanentWidget(self.log_path_label)
        # layout.addWidget(self.log_path_label)

        log_list_layout = QHBoxLayout()
        serial_log_layout = QVBoxLayout()
        operation_log_layout = QVBoxLayout()
        # 日志输出
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        serial_log_layout.addWidget(self.output)

        # 日志输出
        self.op_output = QTextEdit()
        self.op_output.setReadOnly(True)
        operation_log_layout.addWidget(self.op_output)
        log_list_layout.addLayout(serial_log_layout, 2)
        log_list_layout.addLayout(operation_log_layout, 1)
        layout.addLayout(log_list_layout)

        # ----------------------- 命令发送 ------------------------
        # 命令发送区
        cmd_layout = QHBoxLayout()
        self.cmd_input = QTextEdit()
        # 获取每行高度
        line_height = self.cmd_input.fontMetrics().lineSpacing()
        print("每行高度:", line_height)
        self.cmd_input.setMinimumHeight(line_height * 5 + 4)
        self.cmd_input.setMaximumHeight(line_height * 10 + 4)
        self.cmd_input.setPlaceholderText("输入命令...")
        # self.cmd_input.textChanged.connect(lambda: self.adjust_textedit_height(self.cmd_input))
        cmd_layout.addWidget(self.cmd_input)

        # 发送按钮
        btn_list = QVBoxLayout()
        # hex 发送
        self.hex_check_box = QCheckBox("HEX")
        self.hex_check_box.setChecked(False)
        self.hex_check_box.stateChanged.connect(self.hex_check_box_changed)
        # 追加回车
        self.append_enter_check_box = QCheckBox("追加\\n\\r")
        self.append_enter_check_box.setChecked(True)
        self.append_enter_check_box.stateChanged.connect(self.append_enter_check_box_changed)
        # 循环发送选项
        self.repeat_send_check_box = QCheckBox("循环发送")
        self.repeat_send_check_box.stateChanged.connect(self.repeat_send_check_box_changed)
        self.repeat_send_check_box.setChecked(False)
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(10, 10000)  # 10ms ~ 10秒
        self.interval_spin.setValue(100)  # 默认 100ms
        self.interval_spin.setSuffix(" ms")  # 显示单位

        self.send_btn = QPushButton("发送")
        self.send_btn.clicked.connect(self.send_command)
        btn_list.addWidget(self.hex_check_box)
        btn_list.addWidget(self.append_enter_check_box)
        btn_list.addWidget(self.repeat_send_check_box)

        repeat_layout = QHBoxLayout()
        repeat_layout.addWidget(QLabel("间隔:"))
        repeat_layout.addWidget(self.interval_spin)

        btn_list.addLayout(repeat_layout)
        btn_list.addWidget(self.send_btn)
        cmd_layout.addLayout(btn_list)
        layout.addLayout(cmd_layout)

        central_widget.setLayout(layout)

    # ------------------------- 自定义标题栏 -------------------------
    def setup_custom_titlebar(self):
        """创建自定义标题栏"""
        titlebar_widget = QWidget()
        titlebar_widget.setObjectName("TitleBar")
        titlebar_widget.setFixedHeight(30)
        titlebar_layout = QHBoxLayout(titlebar_widget)
        titlebar_layout.setContentsMargins(0, 0, 0, 0)
        titlebar_layout.setSpacing(5)

        self.title_label = QLabel("串口调试工具 V1.0")
        self.title_label.setPixmap(QPixmap("icon/logo.jpeg").scaled(30, 30))
        titlebar_layout.addWidget(self.title_label)

        # ⬅️ 在标题栏放工具按钮
        self.settings_btn = QPushButton("设置")  # ⚙
        self.settings_btn.setObjectName("SettingsBtn")
        self.settings_btn.setIcon(qta.icon("fa5s.cog", color=self.theme_manager.get_icon_color()))
        self.settings_btn.setIconSize(QSize(14, 14))
        self.settings_btn.setFixedHeight(30)
        self.settings_btn.clicked.connect(self.open_settings)
        titlebar_layout.addWidget(self.settings_btn)

        self.connect_btn = QPushButton("连接")  # 🔌
        self.connect_btn.setObjectName("ConnectBtn")
        self.connect_btn.setIcon(qta.icon("fa5s.plug", color=self.theme_manager.get_icon_color()))
        self.connect_btn.setIconSize(QSize(14, 14))
        self.connect_btn.setFixedHeight(30)
        self.connect_btn.clicked.connect(self.toggle_serial)
        titlebar_layout.addWidget(self.connect_btn)

        self.clear_btn = QPushButton("清除")  # 🧹
        self.clear_btn.setObjectName("ClearBtn")
        self.clear_btn.setIcon(qta.icon("fa5s.trash", color=self.theme_manager.get_icon_color()))
        self.clear_btn.setIconSize(QSize(14, 14))
        self.clear_btn.setFixedHeight(30)
        self.clear_btn.clicked.connect(self.clear_all_history)
        titlebar_layout.addWidget(self.clear_btn)

        self.about_btn = QPushButton("关于")
        self.about_btn.setObjectName("AboutBtn")
        self.about_btn.setIcon(qta.icon("fa5s.info-circle", color=self.theme_manager.get_icon_color()))
        self.about_btn.setIconSize(QSize(14, 14))
        self.about_btn.setFixedHeight(30)
        self.about_btn.clicked.connect(self.clear_all_history)
        titlebar_layout.addWidget(self.about_btn)

        titlebar_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.minimize_btn = QPushButton("−")
        self.minimize_btn.setFixedSize(30, 30)
        self.minimize_btn.setObjectName("MinBtn")
        self.minimize_btn.clicked.connect(self.showMinimized)
        titlebar_layout.addWidget(self.minimize_btn)

        self.maximize_btn = QPushButton("□")
        self.maximize_btn.setFixedSize(30, 30)
        self.maximize_btn.setObjectName("MaxBtn")
        self.maximize_btn.clicked.connect(self.toggle_maximize)
        titlebar_layout.addWidget(self.maximize_btn)

        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setObjectName("CloseBtn")
        self.close_btn.clicked.connect(self.close)
        titlebar_layout.addWidget(self.close_btn)

        self.setMenuWidget(titlebar_widget)

    def toggle_maximize(self):
        """切换最大化状态"""
        if self.isMaximized():
            self.showNormal()
            self.maximize_btn.setText("□")
        else:
            self.showMaximized()
            self.maximize_btn.setText("❐")

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            # 检查是否点击在标题栏区域
            if event.pos().y() <= 30:  # 标题栏高度
                self._is_dragging = True
                self._drag_position = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()

    def mouseDoubleClickEvent(self, event):
        """鼠标双击事件"""
        if event.button() == Qt.LeftButton:
            # 检查是否点击在标题栏区域
            if event.pos().y() <= 30:  # 标题栏高度
                self.toggle_maximize()

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if event.buttons() == Qt.LeftButton and self._is_dragging:
            self.move(event.globalPos() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            self._is_dragging = False
            event.accept()

    def update_toolbar_icons(self):
        self.settings_btn.setIcon(qta.icon("fa5s.cog", color=self.theme_manager.get_icon_color()))
        self.connect_btn.setIcon(qta.icon("fa5s.plug", color=self.theme_manager.get_icon_color()))
        self.clear_btn.setIcon(qta.icon("fa5s.trash", color=self.theme_manager.get_icon_color()))
        self.about_btn.setIcon(qta.icon("fa5s.info-circle", color=self.theme_manager.get_icon_color()))

    # ------------------------ 设置 ------------------------
    def open_settings(self):
        """打开设置对话框"""
        dialog = SettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # 检查是否需要重启
            if self.need_restart:
                self.restart_application()
            else:
                self.statusBar().showMessage("设置已应用", 3000)

    def restart_application(self):
        """重启应用"""
        QMessageBox.information(self, "重启提示",
                                "应用需要重启以应用新的缩放设置。\n请关闭后重新打开应用。")
        # 在实际应用中，您可能需要更复杂的重启逻辑
        # 这里只是提示用户手动重启

    def apply_settings(self):
        """应用所有设置"""
        # 更新波特率
        default_baud = self.settings.value("serial/default_baud", "115200")
        self.baudrate_combo.setCurrentText(default_baud)

        # 应用主题
        theme = self.settings.value("ui/theme", "系统默认")
        self.theme_manager.apply_theme(theme)
        self.update_toolbar_icons()

        # 显示设置已应用的消息
        self.statusBar().showMessage("设置已应用", 3000)

    def load_initial_settings(self):
        """应用初始设置"""
        try:
            # 设置默认波特率
            default_baud = self.settings.value("serial/default_baud", "115200")
            self.baudrate_combo.setCurrentText(default_baud)

            # 应用初始缩放设置（环境变量方式）
            scale_setting = self.settings.value("ui/scale", "100%")
            if scale_setting != "100%":
                try:
                    scale_factor = float(scale_setting.replace("%", "")) / 100.0
                    os.environ["QT_SCALE_FACTOR"] = str(scale_factor)
                except:
                    pass
            # 应用主题
            theme = self.settings.value("ui/theme", "系统默认")
            self.theme_manager.apply_theme(theme)
            self.update_toolbar_icons()
        except Exception as e:
            print(f"加载初始设置时出错: {e}")

    # ----------------------- 串口控制 ------------------------
    def refresh_ports(self):
        """刷新串口列表"""
        self.port_cb.clear()
        ports = self.serial.list_ports()
        for p in ports:
            display_text = f"{p.description}"
            self.port_cb.addItem(display_text, p.device)
        self.op_output.append("🔄 串口列表已刷新")

    def toggle_serial(self):
        """打开/关闭串口"""
        if self.serial.ser and self.serial.ser.is_open:
            self.stop_receiver()
            # 已经打开 → 关闭
            self.serial.close()
            self.op_output.append("❌ 串口已关闭")
            self.setSerialStatus(False)
        else:
            # 关闭状态 → 打开
            port = self.port_cb.currentData()
            baud_rate = int(self.baudrate_combo.currentText())
            bytesize = int(self.bytesize_combo.currentText())
            parity = self.parity_combo.currentText()
            stop_bits = float(self.stopbits_combo.currentText())

            if not port:
                self.op_output.append("⚠️ 没有选择串口")
                self.statusBar().showMessage("请选择串口", 2000)
                return
            try:
                status = self.serial.open(port, baud_rate, bytesize, parity, stop_bits)
                if not status:
                    self.setSerialStatus(False)
                    self.op_output.append(f"❌ 串口打开失败: 连接超时")
                    return
                else:
                    self.setSerialStatus(True)
                self.update_log_path()
                self.start_receiver()
            except Exception as e:
                self.op_output.append(f"❌ 打开失败: {e}")
                self.setSerialStatus(False)

    def setSerialStatus(self, status: bool):
        """设置串口状态"""
        port = self.port_cb.currentData()
        baud_rate = int(self.baudrate_combo.currentText())
        bytesize = int(self.bytesize_combo.currentText())
        parity = self.parity_combo.currentText()
        stop_bits = float(self.stopbits_combo.currentText())
        if status:
            self.open_btn.setText("关闭串口")
            self.connect_btn.setText("断开")
            self.op_output.append(f"串口已打开: {port} @ {baud_rate}, {bytesize}{parity}{stop_bits}")
            self.log_mgr.write(f"串口已打开: {port} @ {baud_rate}, {bytesize}{parity}{stop_bits}")
            self.statusBar().showMessage(f"串口已打开: {port} @ {baud_rate}, {bytesize}{parity}{stop_bits}")
            self.serial_status_label.setText(f"🟢 串口已连接: {port} @ {baud_rate}, {bytesize}{parity}{stop_bits}")
        else:
            self.open_btn.setText("打开串口")
            self.connect_btn.setText("连接")
            self.serial_status_label.setText("🔴 串口未连接")

        self._is_port_open = status
        self.refresh_btn.setEnabled(not status)
        self.port_cb.setEnabled(not status)
        self.baudrate_combo.setEnabled(not status)
        self.bytesize_combo.setEnabled(not status)
        self.parity_combo.setEnabled(not status)
        self.stopbits_combo.setEnabled(not status)

    # ----------------------- 命令发送 ------------------------
    def send_command(self):
        """发送命令（支持循环发送）"""
        # 如果已经在发送，就停止
        if hasattr(self, "send_timer") and self.send_timer.isActive():
            self.send_timer.stop()
            self.sending_flag = False
            self.send_btn.setText("发送")
            self.op_output.append("⏹️ 停止发送")
            return
        # 获取命令
        self.lines = [cmd.strip() for cmd in self.cmd_input.toPlainText().splitlines() if cmd.strip()]
        if not self.lines:
            self.op_output.append("⚠️ 没有要发送的命令")
            return

        self.index = 0
        self.sending_flag = True
        self.send_btn.setText("停止发送")  # 按钮切换

        # 获取用户设置
        interval = self.interval_spin.value()
        self.repeat_send = self.repeat_send_check_box.isChecked()

        # 定时器
        self.send_timer = QTimer(self)
        self.send_timer.timeout.connect(self.send_next_command)
        if self.repeat_send:
            self.send_timer.start(interval)
        else:
            self.send_timer.start(0)

    def send_next_command(self):
        """按顺序发送下一条命令"""
        if not self.sending_flag or not self.lines:
            self.send_timer.stop()
            return

        cmd = self.lines[self.index]
        if self.serial.send(cmd):
            self.op_output.append(f"➡️ 已发送: {cmd}")
            self.log_mgr.write(f"➡️ 已发送: {cmd}")
            self.history.save_history(cmd)
            self.load_history_ui()
        else:
            self.op_output.append("❌ 发送失败，串口未打开")
            self.send_timer.stop()
            self.sending_flag = False
            self.send_btn.setText("发送")
            return

        # 处理索引
        self.index += 1
        if self.index >= len(self.lines):
            if self.repeat_send:
                self.index = 0  # 循环
            else:
                self.send_timer.stop()
                self.sending_flag = False
                self.send_btn.setText("发送")

    def send_list_item_command(self, item: QListWidgetItem):
        self.cmd_input.setText(item.text())
        self.send_command()

    def hex_check_box_changed(self):
        if self.hex_check_box.isChecked():
            self.cmd_input.textChanged.connect(self.format_hex_input)
        else:
            self.cmd_input.textChanged.disconnect(self.format_hex_input)

    def append_enter_check_box_changed(self):
        """TODO 追加回车逻辑"""
        pass

    def repeat_send_check_box_changed(self):
        self.repeat_send = self.repeat_send_check_box.isChecked()

    def adjust_textedit_height(self, te: QTextEdit, max_lines=8):
        """调整 QTextEdit 高度，避免卡死"""
        line_height = te.fontMetrics().lineSpacing()
        doc = te.document()
        block_count = doc.blockCount()
        lines = min(block_count, max_lines)
        new_height = lines * line_height + 16  # 8px 边距
        if te.height() <= new_height:
            te.blockSignals(True)  # 阻止 textChanged 信号循环
            te.setFixedHeight(new_height)
            te.blockSignals(False)

    def format_hex_input(self):
        """限制输入16进制，并每两位添加空格"""
        cursor = self.cmd_input.textCursor()
        pos = cursor.position()

        text = self.cmd_input.toPlainText()
        # 保留16进制字符
        text = ''.join(re.findall(r'[0-9A-Fa-f]', text))
        # 每两位加空格
        formatted = ' '.join(text[i:i + 2] for i in range(0, len(text), 2))

        # 防止无限循环触发
        if formatted != self.cmd_input.toPlainText():
            self.cmd_input.blockSignals(True)
            self.cmd_input.setPlainText(formatted)
            self.cmd_input.blockSignals(False)
            # 恢复光标位置
            new_pos = pos + (len(formatted) - len(text))
            cursor.setPosition(new_pos)
            self.cmd_input.setTextCursor(cursor)

    # ----------------------- 硬件配置 ------------------------
    def load_devices(self):
        """加载设备配置信息"""
        for name in self.device_mgr.list_device_names():
            self.device_cb.addItem(name)

    def save_device_commands(self):
        """保存设备配置信息"""
        self.device_mgr.save_device_commands(self.cmd_list)

    def import_commands(self):
        """导入命令"""
        pass

    def add_device(self):
        """增加硬件配置"""
        text, ok = QInputDialog.getText(self, "增加硬件配置", "请输入设备名称：")
        if ok and text:
            if text in self.device_mgr.devices:
                QMessageBox.warning(self, "错误", f"设备{text}已存在")
                return
            self.device_mgr.add_device(text, "COM1", 115200, "N", "1", "8", "0")
            self.save_device_commands()

        pass

    def del_device(self):
        """删除硬件配置"""
        pass

    def delete_cmdlist_item(self):
        """删除命令"""

        pass

    def change_device(self):
        """切换硬件配置"""
        pass

    # ----------------------- 历史记录 ------------------------
    def add_history_to_cmdlist(self):
        """将历史记录添加到命令列表"""
        if self.history_list.currentItem() is None:
            return
        self.cmd_list.insertItem(0, QListWidgetItem(self.history_list.currentItem().text()))

    def delete_selected_history(self):
        """删除选中的历史记录"""
        if self.history_list.currentItem() is None:
            return
        self.history.delete_history(self.history_list.currentItem().text())
        self.load_history_ui()

    def clear_history(self):
        """清空历史记录"""
        self.history.clear_history()
        self.load_history_ui()

    def clear_all_history(self):
        """清空所有历史记录"""
        self.output.setText("")
        self.op_output.setText("")
        self.statusBar().showMessage("数据已清除", 2000)

    def load_history_ui(self):
        self.history_list.clear()
        for cmd in self.history.load_history():
            self.add_history_item(cmd)

    def add_history_item(self, cmd):
        item = QListWidgetItem(cmd)
        self.history_list.insertItem(0, item)

    def open_log_dir(self):
        """打开日志文件夹"""
        log_dir = self.log_mgr.log_dir
        if platform.system() == "Windows":
            os.startfile(log_dir)
        elif platform.system() == "Darwin":  # macOS
            subprocess.call(["open", log_dir])
        else:  # Linux
            subprocess.call(["xdg-open", log_dir])

    def update_log_path(self):
        """更新UI上显示的日志文件路径"""
        self.log_path_label.setText(f"ℹ 当前日志文件: {self.log_mgr.log_file}")

    # ----------------------- 自动化控制 ------------------------
    def start_automation(self):
        if not self._is_port_open:
            self.op_output.append("请先打开串口！")
            return
        if self.auto_thread and self.auto_thread.isRunning():
            self.op_output.append("自动化已在运行")
            return
        cmds = [self.history_list.item(i).text() for i in range(self.history_list.count())]
        if not cmds:
            self.op_output.append("没有可自动发送的命令")
            return

        # 每次启动自动化都新建日志文件
        from manager.log_manager import LogManager
        self.log_mgr = LogManager()
        self.update_log_path()  # 更新 UI 标签

        # 启动自动化线程
        self.auto_thread = AutomationThread(
            cmds,
            serial_mgr=self.serial,
            log_mgr=self.log_mgr,
            interval_ms=500,
            loops=1
        )
        self.auto_thread.log_signal.connect(lambda msg: self.output.append(msg))
        self.auto_thread.finished_signal.connect(self.auto_finished)
        self.auto_thread.start()

        self.start_auto_btn.setEnabled(False)
        self.stop_auto_btn.setEnabled(True)
        self.op_output.append("自动化开始")
        self.log_mgr.write("自动化开始")

    def stop_automation(self):
        if self.auto_thread:
            self.auto_thread.stop()
            self.op_output.append("请求停止自动化...")

    def auto_finished(self):
        self.op_output.append("自动化结束")
        self.start_auto_btn.setEnabled(True)
        self.stop_auto_btn.setEnabled(False)

    # -------------------- 串口接收 --------------------
    def start_receiver(self):
        """启动接收线程"""
        self.receiver_thread = SerialReceiver(self.serial, self.log_mgr)
        self.receiver_thread.received.connect(self.on_received)
        self.receiver_thread.start()

    def stop_receiver(self):
        """停止接收线程"""
        if self.receiver_thread:
            self.receiver_thread.stop()
            self.receiver_thread.wait()
            self.receiver_thread = None

    def on_received(self, msg: str):
        """接收到串口数据"""
        self.output.append(f"⬅️ {msg}")

    # -------------------- 关闭 --------------------
    def closeEvent(self, event):
        if self.auto_thread:
            self.auto_thread.stop()
        self.serial.close()
        self.history.close()
        # 保存窗口大小和位置
        self.settings.setValue("window/size", self.size())
        self.settings.setValue("window/position", self.pos())
        super().closeEvent(event)
