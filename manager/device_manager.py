class DeviceManager:
    def __init__(self):
        self.devices = []
        self.current_device = None
        self.load_devices()

    def add_device(self, name, port, baud_rate, parity, stop_bits, bytesize, timeout):
        self.devices.append({
            "name": name,
            "port": port,
            "baud_rate": baud_rate,
            "parity": parity,
            "stop_bits": stop_bits,
            "bytesize": bytesize,
        })
