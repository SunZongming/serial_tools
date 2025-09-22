from PyQt5.QtCore import QThread, pyqtSignal

from manager.serial_manager import SerialManager


class SerialReceiver(QThread):
    received = pyqtSignal(str)

    def __init__(self, serial: SerialManager, log_mgr=None):
        super().__init__()
        self.serial = serial
        self.log_mgr = log_mgr
        self._running = True

    def run(self):
        while self._running:
            line = self.serial.readline()
            if line:
                msg = f"[接收] {line}"
                self.received.emit(msg)
                if self.log_mgr:
                    self.log_mgr.write(msg)
            self.msleep(50)

    def stop(self):
        self._running = False
        self.quit()
        self.wait()
