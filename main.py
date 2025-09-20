import os
import sys

from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtWidgets import QApplication

from ui.ui_main import SerialTool


# 应用启动配置
def setup_scaling():
    settings = QSettings("settings.ini", QSettings.IniFormat)
    scale_text = settings.value("ui/scale", "100%")
    print(f"缩放率: {scale_text}")

    scale_map = {"100%": 1.0, "125%": 1.25, "150%": 1.5, "175%": 1.75, "200%": 2.0}
    scale_factor = scale_map.get(scale_text, 1.0)

    os.environ["QT_SCALE_FACTOR"] = str(scale_factor)

    # 启用高DPI支持
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)


if __name__ == "__main__":
    setup_scaling()
    app = QApplication(sys.argv)
    w = SerialTool()
    w.show()
    sys.exit(app.exec_())
