import serial


class SerialSensorReader:
    """Lee frames de sensores desde UART/USB serial.

    Devuelve cadenas con el formato que ya espera el backend:
        "00.00 0000 00.00 0000"
    """

    def __init__(self, port, baudrate=115200, timeout=0.2, simulator_mode=False):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.simulator_mode = simulator_mode
        self.ser = None

    def open(self):
        self.ser = serial.Serial(self.port, baudrate=self.baudrate, timeout=self.timeout)
        print(f"SerialSensorReader: puerto abierto {self.port}")

    def close(self):
        if self.ser is not None:
            self.ser.close()
            self.ser = None

    def is_open(self):
        return self.ser is not None and self.ser.is_open

    def read_frame(self):
        if not self.is_open():
            return None
        if self.ser.in_waiting <= 0:
            return None

        if self.simulator_mode:
            data = self.ser.readline().decode('utf-8').rstrip('\n\r')
        else:
            data = self.ser.readline().decode('utf-8', errors='replace').strip()

        if not data:
            return None
        return data