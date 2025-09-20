from PyQt5.QtCore import QThread, pyqtSignal
import time

class AutomationThread(QThread):
    log_signal = pyqtSignal(str)   # 显示到UI
    send_signal = pyqtSignal(str)  # 实际发送到串口
    finished_signal = pyqtSignal()

    def __init__(self, cmds, serial_mgr, log_mgr, interval_ms=500, loops=1):
        super().__init__()
        self.cmds = cmds[:]
        self.serial = serial_mgr
        self.log_mgr = log_mgr
        self.interval_ms = max(1, interval_ms)
        self.loops = max(1, loops)
        self._running = True

    def run(self):
        try:
            total_steps = self.loops * len(self.cmds)
            step = 0
            for loop_idx in range(self.loops):
                if not self._running:
                    self._log("自动化已停止")
                    break
                self._log(f"开始第 {loop_idx+1}/{self.loops} 轮")
                for cmd in self.cmds:
                    if not self._running:
                        break
                    step += 1
                    self._log(f"[自动发送] ({step}/{total_steps}) {cmd}")
                    # 发送指令
                    self.send_signal.emit(cmd)
                    self.serial.send(cmd)
                    # 立即写日志
                    self._log(f"发送: {cmd}")

                    # 接收返回数据
                    time.sleep(0.05)
                    recv_data = self._read_available()
                    if recv_data:
                        for line in recv_data:
                            self._log(f"接收: {line}")

                    time.sleep(self.interval_ms / 1000)
            self._log("自动化任务完成")
        finally:
            self.finished_signal.emit()

    def stop(self):
        self._running = False

    def _read_available(self):
        """非阻塞读取串口所有可用数据"""
        lines = []
        if self.serial.ser and self.serial.ser.is_open:
            while self.serial.ser.in_waiting:
                try:
                    line = self.serial.ser.readline().decode("utf-8", errors="ignore").strip()
                    if line:
                        lines.append(line)
                except Exception:
                    pass
        return lines

    def _log(self, msg):
        """同时写UI和日志文件"""
        self.log_signal.emit(msg)
        if self.log_mgr:
            self.log_mgr.write(msg)
