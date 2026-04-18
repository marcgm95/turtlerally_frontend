import socket


class WiFiSensorReader:
    """Recibe frames de sensores desde un ESP32 por WiFi.
    Soporta TCP o UDP y entrega exactamente el mismo frame crudo que la UART,
    para reutilizar extract_data() sin tocar la lógica de cálculo.
    """

    def __init__(self, host='0.0.0.0', port=22334, protocol='tcp', timeout=0.1, debug=False):
        self.host = host
        self.port = port
        self.protocol = protocol.lower()
        self.timeout = timeout
        self.server_socket = None
        self.client_socket = None
        self.buffer = ""
        self.debug = debug

    def open(self):
        if self.protocol == 'tcp':
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)
            self.server_socket.settimeout(self.timeout)
            print(f"WiFiSensorReader: TCP escuchando en {self.host}:{self.port}")
        elif self.protocol == 'udp':
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.settimeout(self.timeout)
            print(f"WiFiSensorReader: UDP escuchando en {self.host}:{self.port}")
        else:
            raise ValueError("protocol debe ser 'tcp' o 'udp'")

    def close(self):
        if self.client_socket is not None:
            try:
                self.client_socket.close()
            except Exception:
                pass
            self.client_socket = None
        if self.server_socket is not None:
            try:
                self.server_socket.close()
            except Exception:
                pass
            self.server_socket = None

    def _accept_if_needed(self):
        if self.protocol != 'tcp':
            return True
        if self.client_socket is not None:
            return True
        try:
            self.client_socket, addr = self.server_socket.accept()
            self.client_socket.settimeout(self.timeout)
            print(f"WiFiSensorReader: cliente conectado {addr}")
            return True
        except socket.timeout:
            return False

    def _extract_frame_from_buffer(self):
        for separator in ('\n', '|'):
            if separator in self.buffer:
                frame, self.buffer = self.buffer.split(separator, 1)
                frame = frame.strip()
                if frame:
                    return frame
        return None

    def read_frame(self):
        if self.server_socket is None:
            return None

        if self.protocol == 'tcp':
            if not self._accept_if_needed():
                return None
            try:
                data = self.client_socket.recv(256)
                if not data:
                    self.client_socket.close()
                    self.client_socket = None
                    return None
                self.buffer += data.decode('utf-8', errors='replace')
                frame = self._extract_frame_from_buffer()
                if frame and self.debug:
                    print(f"[Wifi_debug] Frame received: {frame}")
                return frame
            except socket.timeout:
                return None
            except Exception:
                if self.client_socket is not None:
                    self.client_socket.close()
                self.client_socket = None
                return None

        # UDP
        try:
            data, _addr = self.server_socket.recvfrom(256)
            self.buffer += data.decode('utf-8', errors='replace')
            frame = self._extract_frame_from_buffer()
            if frame and self.debug:
                print(f"[WiFi] Frame recibido: {frame}")
            return frame
        except socket.timeout:
            return None