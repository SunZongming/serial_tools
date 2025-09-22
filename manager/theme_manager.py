import platform
import subprocess

from PyQt5.QtCore import QSettings


class ThemeManager:
    def __init__(self, app):
        self.app = app
        self.settings = QSettings("settings.ini", QSettings.IniFormat)
        self.icon_color = "#FFFFFF"

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
        if self.is_dark_mode():
            self.apply_dark_theme()
        else:
            self.apply_light_theme()

    def apply_qss(self, theme_file):
        with open(theme_file, "r", encoding="utf-8") as f:
            print("正在加载主题文件:", theme_file)
            # print("主题文件内容:", f.read())
            self.app.setStyleSheet(f.read())

    def apply_light_theme(self):
        """应用浅色主题"""
        self.icon_color = "#000000"
        self.app.setStyle("Fusion")
        self.apply_qss("theme/material_light.qss")

    def apply_dark_theme(self):
        """应用深色主题"""
        self.icon_color = "#FFFFFF"
        self.app.setStyle("Fusion")
        self.apply_qss("theme/material_dark.qss")

    def get_current_theme(self):
        """获取当前主题"""
        return self.settings.value("ui/theme", "系统默认")

    def get_icon_color(self):
        """获取图标颜色"""
        print("图标颜色:", self.icon_color)
        return self.icon_color

    # 判断系统是否暗色模式
    def is_dark_mode(self):
        system = platform.system()

        # Windows
        if system == "Windows":
            try:
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
                )
                # 1 = light, 0 = dark
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                return value == 0
            except Exception:
                return False

        # macOS
        elif system == "Darwin":
            try:
                result = subprocess.run(
                    ["defaults", "read", "-g", "AppleInterfaceStyle"],
                    capture_output=True, text=True
                )
                return "Dark" in result.stdout
            except Exception:
                return False

        # Linux (GNOME/KDE)
        elif system == "Linux":
            try:
                result = subprocess.run(
                    ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
                    capture_output=True, text=True
                )
                return "dark" in result.stdout.lower()
            except Exception:
                return False

        return False  # 默认亮色
