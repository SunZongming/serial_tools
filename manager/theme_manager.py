from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QApplication


class ThemeManager:
    def __init__(self, app):
        self.app = app
        self.settings = QSettings("../settings.ini", QSettings.IniFormat)

    def apply_theme(self, theme_name):
        """应用主题"""
        if theme_name == "系统默认":
            self.apply_system_theme()
        elif theme_name == "浅色":
            self.apply_light_theme()
        elif theme_name == "深色":
            self.apply_dark_theme()
        else:
            self.apply_system_theme()

        # 保存主题设置
        self.settings.setValue("ui/theme", theme_name)
        self.settings.sync()

    def apply_system_theme(self):
        """应用系统默认主题"""
        self.app.setStyle("Fusion")  # 使用 Fusion 风格，它支持主题

    def apply_light_theme(self):
        """应用浅色主题"""
        self.app.setStyle("Fusion")

        palette = QPalette()

        # 基础颜色
        base_color = QColor(240, 240, 240)
        text_color = QColor(0, 0, 0)
        highlight_color = QColor(0, 120, 215)

        # 设置调色板
        palette.setColor(QPalette.Window, base_color)
        palette.setColor(QPalette.WindowText, text_color)
        palette.setColor(QPalette.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.AlternateBase, base_color)
        palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 220))
        palette.setColor(QPalette.ToolTipText, text_color)
        palette.setColor(QPalette.Text, text_color)
        palette.setColor(QPalette.Button, base_color)
        palette.setColor(QPalette.ButtonText, text_color)
        palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.Link, highlight_color)
        palette.setColor(QPalette.Highlight, highlight_color)
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))

        # 禁用状态的颜色
        palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(128, 128, 128))
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor(128, 128, 128))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(128, 128, 128))

        self.app.setPalette(palette)

    def apply_dark_theme(self):
        """应用深色主题"""
        self.app.setStyle("Fusion")

        palette = QPalette()

        # 基础颜色
        base_color = QColor(45, 45, 45)
        text_color = QColor(240, 240, 240)
        highlight_color = QColor(42, 130, 218)

        # 设置调色板
        palette.setColor(QPalette.Window, base_color)
        palette.setColor(QPalette.WindowText, text_color)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, base_color)
        palette.setColor(QPalette.ToolTipBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipText, text_color)
        palette.setColor(QPalette.Text, text_color)
        palette.setColor(QPalette.Button, base_color)
        palette.setColor(QPalette.ButtonText, text_color)
        palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.Link, highlight_color)
        palette.setColor(QPalette.Highlight, highlight_color)
        palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))

        # 禁用状态的颜色
        palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(128, 128, 128))
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor(128, 128, 128))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(128, 128, 128))

        self.app.setPalette(palette)

    def get_current_theme(self):
        """获取当前主题"""
        return self.settings.value("ui/theme", "系统默认")