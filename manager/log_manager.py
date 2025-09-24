import datetime
import os


class LogManager:
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        # 文件名以时间命名
        self.log_file = os.path.join(self.log_dir, f"log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        self.logging_flag = True

    def set_logging_flag(self, flag):
        """设置是否记录日志"""
        print(f"设置日志记录状态: {flag}")
        self.logging_flag = flag

    def write(self, msg: str, level="info"):
        """写日志"""
        if not self.logging_flag:
            return
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] [{level}] {msg}\n")
