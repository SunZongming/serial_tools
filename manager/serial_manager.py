import serial
import serial.tools.list_ports


class SerialManager:
    def __init__(self):
        self.ser = None

    @staticmethod
    def list_ports():
        """返回所有串口信息"""
        return list(serial.tools.list_ports.comports())

    def open(self, port, baud_rate=9600, bytesize=8, parity="N", stop_bits=1, timeout=0.1):
        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=baud_rate,
                bytesize=bytesize,
                parity=parity,
                stopbits=stop_bits,
                timeout=timeout
            )
            return True
        except Exception as e:
            print(f"串口打开失败: {e}")
            self.ser = None
            return False

    def close(self):
        """关闭串口"""
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.ser = None

    def send(self, data: str, hex_flag=False, end=b"\r\n"):
        """发送数据"""
        print(f"发送数据: {data}, hex_flag: {hex_flag}, end: {end}")
        if self.ser and self.ser.is_open:
            if hex_flag:
                data = data.upper().replace(" ", "")
                if len(data) % 2 != 0:
                    data += "0"
                data = bytes.fromhex(data)  # 去空格后转字节
                self.ser.write(data + end)
            else:
                self.ser.write(data.encode("utf-8") + end)  # 默认加换行
            return True
        return False

    def read(self):
        if self.ser and self.ser.is_open and self.ser.in_waiting:
            try:
                return self.ser.readline().decode('utf-8', errors='ignore').strip()
            except Exception as e:
                print(e)
                return None
        return None

    def readline(self):
        """读取一行（非阻塞）"""
        if self.ser and self.ser.is_open and self.ser.in_waiting:
            try:
                return self.ser.readline().decode("utf-8", errors="ignore").strip()
            except Exception:
                return None
        return None
