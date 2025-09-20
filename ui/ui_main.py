import os
import platform
import subprocess

from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QTextEdit, QLineEdit, \
    QListWidget, QListWidgetItem, QSizePolicy, QToolBar, QAction, QDialog, QMainWindow, QMessageBox, QApplication

from thread.automation_thread import AutomationThread
from manager.history_manager import HistoryManager
from manager.log_manager import LogManager
from manager.serial_manager import SerialManager
from thread.serial_receiver import SerialReceiver
from ui.setting_dialog import SettingsDialog
from manager.theme_manager import ThemeManager


class SerialTool(QMainWindow):
    def __init__(self):
        super().__init__()

        # 添加重启标志
        self.need_restart = False

        self.setWindowTitle("硬件测试上位机 v1.0")
        self.resize(1200, 850)

        # 串口管理
        self.serial = SerialManager()
        self.history = HistoryManager()
        self.log_mgr = LogManager()
        # 设置
        self.settings = QSettings("../settings.ini", QSettings.IniFormat)
        # 初始化主题管理器
        self.theme_manager = ThemeManager(QApplication.instance())
        # self.update_log_path()
        self.auto_thread = None
        self.receiver_thread = None
        self._is_port_open = False

        # 创建状态栏
        self.statusBar().showMessage("就绪")

        # 创建工具栏
        toolbar = QToolBar("主工具栏")
        self.addToolBar(toolbar)

        # 添加设置按钮
        settings_action = QAction(QIcon(":icon/setting.svg"), "设置", self)
        settings_action.triggered.connect(self.open_settings)
        toolbar.addAction(settings_action)

        # 添加串口连接按钮
        self.connect_action = QAction("连接", self)
        self.connect_action.triggered.connect(self.toggle_serial)
        toolbar.addAction(self.connect_action)

        # 添加分隔线
        toolbar.addSeparator()

        # 添加其他工具按钮
        clear_action = QAction("清除", self)
        clear_action.triggered.connect(self.clear_all_history)
        toolbar.addAction(clear_action)

        # 设置中心窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建串口UI
        self.setup_serial_ui(central_widget)

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
        port_layout.addWidget(QLabel("端口:"))
        self.port_cb = QComboBox()
        port_layout.addWidget(self.port_cb)
        # 波特率
        port_layout.addWidget(QLabel("波特率:"))
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(
            ["110", "300", "600", "1200", "2400", "4800", "9600", "14400", "19200", "38400", "56000", "57600", "115200",
             "128000", "230400", "256000", "460800", "921600", ])
        self.baudrate_combo.setEditable(True)  # ✅ 用户可输入自定义波特率
        self.baudrate_combo.setCurrentText("115200")  # 设置默认值为115200
        port_layout.addWidget(self.baudrate_combo)
        # 数据位
        port_layout.addWidget(QLabel("数据位:"))
        self.bytesize_combo = QComboBox()
        self.bytesize_combo.addItems(["5", "6", "7", "8"])
        self.bytesize_combo.setCurrentText("8")
        port_layout.addWidget(self.bytesize_combo)
        # 校验位
        port_layout.addWidget(QLabel("校验:"))
        self.parity_combo = QComboBox()
        self.parity_combo.addItems(["N", "E", "O", "M", "S"])  # None, Even, Odd, Mark, Space
        self.parity_combo.setCurrentText("N")
        port_layout.addWidget(self.parity_combo)
        # 停止位
        port_layout.addWidget(QLabel("停止位:"))
        self.stopbits_combo = QComboBox()
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

        # ----------------------- 命令发送 ------------------------
        # 命令发送区
        cmd_layout = QHBoxLayout()
        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("输入命令...")
        cmd_layout.addWidget(self.cmd_input)

        # 发送按钮
        self.send_btn = QPushButton("发送")
        self.send_btn.clicked.connect(self.send_command)
        cmd_layout.addWidget(self.send_btn)
        layout.addLayout(cmd_layout)

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
        right_col.addWidget(QLabel("历史记录 (双击复发):"))
        self.add_history_btn = QPushButton("添加到指令列表")
        self.delete_history_btn = QPushButton("删除选中记录")
        self.clear_history_btn = QPushButton("清空历史")
        self.add_history_btn.clicked.connect(self.add_history_to_cmdlist)
        self.delete_history_btn.clicked.connect(self.delete_selected_history)
        self.clear_history_btn.clicked.connect(self.clear_all_history)

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
        self.start_auto_btn = QPushButton("开始自动化")
        self.start_auto_btn.clicked.connect(self.start_automation)
        self.stop_auto_btn = QPushButton("停止自动化")
        self.stop_auto_btn.clicked.connect(self.stop_automation)
        self.stop_auto_btn.setEnabled(False)
        auto_layout.addWidget(self.start_auto_btn)
        auto_layout.addWidget(self.stop_auto_btn)
        layout.addLayout(auto_layout)

        # 当前日志文件路径显示
        self.log_path_label = QLabel(f"当前日志文件: {self.log_mgr.log_file}")
        layout.addWidget(self.log_path_label)

        # 日志输出
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

        # 日志保存按钮
        self.save_log_btn = QPushButton("打开日志文件夹")
        self.save_log_btn.clicked.connect(self.open_log_dir)
        layout.addWidget(self.save_log_btn)

        central_widget.setLayout(layout)

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
        self.output.append("串口列表已刷新")

    def toggle_serial(self):
        """打开/关闭串口"""
        if self.serial.ser and self.serial.ser.is_open:
            self.stop_receiver()
            # 已经打开 → 关闭
            self.serial.close()
            self.open_btn.setText("打开串口")
            self.output.append("串口已关闭")
            self._is_port_open = False
            self.refresh_btn.setEnabled(True)
            self.statusBar().showMessage("串口已关闭", 2000)
        else:
            # 关闭状态 → 打开
            port = self.port_cb.currentData()
            baud_rate = int(self.baudrate_combo.currentText())
            bytesize = int(self.bytesize_combo.currentText())
            parity = self.parity_combo.currentText()
            stop_bits = float(self.stopbits_combo.currentText())

            if not port:
                self.output.append("⚠️ 没有选择串口")
                self.statusBar().showMessage("请选择串口", 2000)
                return
            try:
                self.serial.open(port, baud_rate, bytesize, parity, stop_bits)
                self.open_btn.setText("关闭串口")
                self.output.append(f"串口已打开: {port} @ {baud_rate}, {bytesize}{parity}{stop_bits}")
                self.log_mgr.write(f"串口已打开: {port} @ {baud_rate}, {bytesize}{parity}{stop_bits}")
                self.update_log_path()

                self.start_receiver()
                self._is_port_open = True
                self.refresh_btn.setEnabled(False)
                self.statusBar().showMessage(f"串口已打开: {port} @ {baud_rate}, {bytesize}{parity}{stop_bits}")
            except Exception as e:
                self.output.append(f"❌ 打开失败: {e}")
                self.statusBar().showMessage("串口打开失败", 2000)

    # ----------------------- 命令发送 ------------------------
    def send_command(self):
        cmd = self.cmd_input.text().strip()
        if not cmd or not self._is_port_open:
            return
        if self.serial.send(cmd):
            self.output.append(f"➡️ 已发送: {cmd}")
            self.log_mgr.write(f"➡️ 已发送: {cmd}")
            self.history.save_history(cmd)
            self.add_history_item(cmd)
            self.cmd_input.clear()
        else:
            self.output.append("❌ 发送失败，串口未打开")

    def send_list_item_command(self, item: QListWidgetItem):
        self.cmd_input.setText(item.text())
        self.send_command()

    # ----------------------- 硬件配置 ------------------------
    def load_devices(self):
        """加载设备配置信息"""
        pass

    def save_device_commands(self):
        """保存设备配置信息"""
        pass

    def import_commands(self):
        """导入命令"""
        pass

    def add_device(self):
        """增加硬件配置"""
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
        pass

    def delete_selected_history(self):
        """删除选中的历史记录"""
        pass

    def clear_all_history(self):
        """清空所有历史记录"""
        # TODO
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
        self.log_path_label.setText(f"当前日志文件: {self.log_mgr.log_file}")

    # ----------------------- 自动化控制 ------------------------
    def start_automation(self):
        if not self._is_port_open:
            self.output.append("请先打开串口！")
            return
        if self.auto_thread and self.auto_thread.isRunning():
            self.output.append("自动化已在运行")
            return
        cmds = [self.history_list.item(i).text() for i in range(self.history_list.count())]
        if not cmds:
            self.output.append("没有可自动发送的命令")
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
        self.output.append("自动化开始")
        self.log_mgr.write("自动化开始")

    def stop_automation(self):
        if self.auto_thread:
            self.auto_thread.stop()
            self.output.append("请求停止自动化...")

    def auto_finished(self):
        self.output.append("自动化结束")
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
