from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QComboBox, QGroupBox, QSpinBox,
                             QCheckBox, QDialogButtonBox, QMessageBox, QPushButton)


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("应用设置")
        self.setModal(True)
        self.resize(400, 300)

        # 添加标志来跟踪设置是否更改
        self.settings_changed = False
        self.current_scale = "100%"
        self.current_theme = "系统默认"
        self.temp_theme = "系统默认"

        self.init_ui()
        self.load_settings()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 显示设置组
        display_group = QGroupBox("显示设置")
        display_layout = QVBoxLayout()

        # 缩放设置
        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel("UI缩放比例:"))
        self.scale_combo = QComboBox()
        self.scale_combo.addItems(["100%", "125%", "150%", "175%", "200%", "自定义"])
        self.scale_combo.currentTextChanged.connect(self.on_scale_changed)
        scale_layout.addWidget(self.scale_combo)

        self.custom_scale_spin = QSpinBox()
        self.custom_scale_spin.setRange(50, 300)
        self.custom_scale_spin.setSuffix("%")
        self.custom_scale_spin.setVisible(False)
        self.custom_scale_spin.valueChanged.connect(self.on_custom_scale_changed)
        scale_layout.addWidget(self.custom_scale_spin)

        display_layout.addLayout(scale_layout)

        # 主题设置
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("主题:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["系统默认", "浅色", "深色"])
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        theme_layout.addWidget(self.theme_combo)
        display_layout.addLayout(theme_layout)

        # 实时预览按钮
        self.preview_btn = QPushButton("预览主题")
        self.preview_btn.clicked.connect(self.preview_theme)
        display_layout.addWidget(self.preview_btn)

        display_group.setLayout(display_layout)
        layout.addWidget(display_group)

        # 串口设置组
        serial_group = QGroupBox("串口设置")
        serial_layout = QVBoxLayout()

        # 默认波特率
        baud_layout = QHBoxLayout()
        baud_layout.addWidget(QLabel("默认波特率:"))
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baud_combo.currentTextChanged.connect(self.on_settings_changed)
        baud_layout.addWidget(self.baud_combo)
        serial_layout.addLayout(baud_layout)

        # 自动连接
        self.auto_connect_check = QCheckBox("启动时自动连接串口")
        self.auto_connect_check.stateChanged.connect(self.on_settings_changed)
        serial_layout.addWidget(self.auto_connect_check)

        serial_group.setLayout(serial_layout)
        layout.addWidget(serial_group)

        # 按钮框
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def on_settings_changed(self):
        """当任何设置更改时调用"""
        self.settings_changed = True

    def on_theme_changed(self, theme):
        """主题更改处理"""
        self.settings_changed = True
        self.temp_theme = theme

    def preview_theme(self):
        """预览主题效果"""
        if hasattr(self.parent, 'theme_manager'):
            self.parent.theme_manager.apply_theme(self.theme_combo.currentText())
            self.parent.update_toolbar_icons()
            QMessageBox.information(self, "主题预览",
                                    f"已应用 {self.theme_combo.currentText()} 主题预览。\n"
                                    "点击确定后恢复当前主题。")
            # 恢复原来的主题
            self.parent.theme_manager.apply_theme(self.current_theme)
            self.parent.update_toolbar_icons()

    def on_scale_changed(self, text):
        self.settings_changed = True
        self.custom_scale_spin.setVisible(text == "自定义")

    def on_custom_scale_changed(self, value):
        self.settings_changed = True
        pass  # 可以在这里添加自定义缩放的处理逻辑

    def load_settings(self):
        """从设置中加载值"""
        settings = self.parent.settings if self.parent else QSettings("settings.ini", QSettings.IniFormat)

        # 加载缩放设置
        scale = settings.value("ui/scale", "100%")
        self.current_scale = scale
        self.current_theme = settings.value("ui/theme", "系统默认")
        if scale.endswith("%") and scale != "自定义":
            self.scale_combo.setCurrentText(scale)
        else:
            self.scale_combo.setCurrentText("自定义")
            try:
                scale_value = int(scale.replace("%", ""))
                self.custom_scale_spin.setValue(scale_value)
            except:
                self.custom_scale_spin.setValue(100)

        # 加载其他设置
        self.theme_combo.setCurrentText(settings.value("ui/theme", "系统默认"))
        self.baud_combo.setCurrentText(settings.value("serial/default_baud", "115200"))
        self.auto_connect_check.setChecked(settings.value("serial/auto_connect", False, type=bool))

        # 重置更改标志
        self.settings_changed = False

    def save_settings(self):
        """保存设置到配置文件"""
        settings = self.parent.settings if self.parent else QSettings("settings.ini", QSettings.IniFormat)

        # 保存缩放设置
        if self.scale_combo.currentText() == "自定义":
            settings.setValue("ui/scale", f"{self.custom_scale_spin.value()}%")
        else:
            settings.setValue("ui/scale", self.scale_combo.currentText())

        # 保存其他设置
        settings.setValue("ui/theme", self.theme_combo.currentText())
        settings.setValue("serial/default_baud", self.baud_combo.currentText())
        settings.setValue("serial/auto_connect", self.auto_connect_check.isChecked())

        settings.sync()  # 确保设置立即保存
        return True

    def accept(self):
        """重写accept方法，处理设置保存"""
        if self.settings_changed:
            if self.save_settings():
                # 检查是否需要重启
                current_scale = self.current_scale
                new_scale = self.scale_combo.currentText()
                print(f"当前缩放率: {current_scale}, 新的缩放率: {new_scale}")
                if current_scale != new_scale:
                    # 缩放设置更改需要重启
                    reply = QMessageBox.question(self, "需要重启",
                                                 f"缩放设置已从 {current_scale} 更改为 {new_scale}。\n"
                                                 "需要重启应用才能生效。\n\n"
                                                 "是否立即重启应用？",
                                                 QMessageBox.Yes | QMessageBox.No,
                                                 QMessageBox.No)

                    if reply == QMessageBox.Yes:
                        # 标记需要重启
                        if self.parent:
                            self.parent.need_restart = True
                        # 关闭对话框
                        super().accept()
                        return

                    # 其他设置可以立即应用
                if self.parent:
                    self.parent.apply_settings()

                super().accept()
