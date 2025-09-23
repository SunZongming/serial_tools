import json
import os


class DeviceManager:
    def __init__(self, filename="devices.json"):
        self.filename = filename
        self.devices = {}
        self.device_names = []
        self.current_device = None
        self.load_devices()

    def load_devices(self):
        """加载设备配置"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    self.devices = json.load(f)
            except Exception as e:
                print("加载设备配置失败:", e)

    def add_device(self, name, serial_port="", baud_rate=115200, parity="N", stop_bits=1, bytesize=8):
        """添加新设备"""
        self.devices[name] = {
            "serial_port": serial_port,
            "baud_rate": baud_rate,
            "parity": parity,
            "stop_bits": stop_bits,
            "bytesize": bytesize,
            "commands": []
        }
        self.current_device = self.devices[name]
        self.save_devices()

    def save_devices(self):
        """保存所有设备配置"""
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(self.devices, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print("保存设备配置失败:", e)

    def delete_device(self, name):
        """删除设备"""
        if name in self.devices:
            del self.devices[name]
            self.save_devices()
            self.current_device = None

    def set_current_device(self, name):
        """切换当前设备"""
        if name in self.devices:
            self.current_device = self.devices[name]

    def save_device_commands(self, cmd_list_widget):
        """保存命令列表到当前设备"""
        if self.current_device is None:
            return False
        cmds = [cmd_list_widget.item(i).text() for i in range(cmd_list_widget.count())]
        self.current_device["commands"] = cmds
        self.save_devices()
        return True

    def list_device_names(self):
        """列出所有设备名称"""
        return list(self.devices.keys())