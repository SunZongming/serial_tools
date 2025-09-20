import datetime
import os


class LogManager:
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        # 文件名以时间命名
        self.log_file = os.path.join(self.log_dir, f"log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    def write(self, msg: str):
        """写日志"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {msg}\n")
