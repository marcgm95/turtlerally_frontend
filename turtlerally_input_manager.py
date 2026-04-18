import time


class InputManager:
    """Selecciona la fuente de entrada de sensores.

    Modos:
      - serial: usa solo UART
      - wifi: usa solo ESP32 por WiFi
      - auto: prioriza WiFi y cae a serial si WiFi expira
    """

    def __init__(self, config, serial_reader=None, wifi_reader=None):
        self.config = config
        self.serial_reader = serial_reader
        self.wifi_reader = wifi_reader
        self.mode = getattr(config, 'sensor_input_mode', 'serial')
        self.wifi_frame_timeout_s = getattr(config, 'wifi_sensor_frame_timeout_s', 1.0)
        self.last_wifi_frame = None
        self.last_wifi_timestamp = 0.0
        self.last_serial_frame = None
        self.last_serial_timestamp = 0.0

    def _read_from_serial(self):
        if self.serial_reader is None:
            return None
        frame = self.serial_reader.read_frame()
        if frame:
            self.last_serial_frame = frame
            self.last_serial_timestamp = time.time()
            return ('serial', frame, self.last_serial_timestamp)
        return None

    def _read_from_wifi(self):
        if self.wifi_reader is None:
            return None
        frame = self.wifi_reader.read_frame()
        if frame:
            self.last_wifi_frame = frame
            self.last_wifi_timestamp = time.time()
            return ('wifi', frame, self.last_wifi_timestamp)
        return None

    def _wifi_is_recent(self):
        if self.last_wifi_frame is None:
            return False
        return (time.time() - self.last_wifi_timestamp) <= self.wifi_frame_timeout_s

    def read_frame(self):
        if self.mode == 'serial':
            return self._read_from_serial()
        if self.mode == 'wifi':
            return self._read_from_wifi()
        if self.mode == 'auto':
            wifi_data = self._read_from_wifi()
            if wifi_data is not None:
                return wifi_data
            if self._wifi_is_recent():
                return None
            return self._read_from_serial()
        raise ValueError(f"sensor_input_mode no válido: {self.mode}")