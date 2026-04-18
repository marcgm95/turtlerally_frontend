import socket
import time
import threading
import keyboard  # Requires `sudo pip install keyboard` on Linux
from datetime import datetime

class SocketServer:
    def __init__(self, host='0.0.0.0', port=11912):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_sockets = []
        self.started = False

    def start(self):
        """Create and configure server TCP to send data to RR"""
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen()
            print(f"TCP Server started on {self.host}:{self.port}")
            self.started = True
            threading.Thread(target=self.accept_clients, daemon=True).start()
        except Exception as e:
            print(f"Error starting TCP server: {e}")

    def accept_clients(self):
        """Connect TCP client to establish communication"""
        while self.started:
            try:
                client_socket, client_address = self.server_socket.accept()
                self.client_sockets.append(client_socket)
                print(f"TCP Client connected: {client_address}")
            except Exception as e:
                print(f"Error accepting TCP client: {e}")

    def send(self, message):
        """Send data via TCP server (TurtleRally) to TCP client"""
        if not self.client_sockets:
            print("No clients connected")
            return

        message_bytes = message.encode('ascii')
        for client_socket in self.client_sockets[:]:
            try:
                client_socket.send(message_bytes)
                #print(f"Sent: {message}")
                # TODO: Handle the debug mode to read the messages sent from server to client
            except Exception as e:
                print(f"Error sending message to {client_socket.getpeername()}: {e}")
                client_socket.close()
                self.client_sockets.remove(client_socket)

    def stop(self):
        """Close TCP communication"""
        self.started = False
        for client_socket in self.client_sockets:
            client_socket.close()
        self.server_socket.close()
        print("Server stopped")


class MainApp:
    def __init__(self, config, data_queue, trigger):
        self.socketServer = SocketServer()
        self.pulsesS1 = 0.0
        self.pulsesS2 = 0.0
        self.data_queue = data_queue
        self.trigger = trigger
        self.start_time = datetime.now()
        self.config = config

        # Setting up key listeners using `keyboard`
        keyboard.add_hotkey('enter', self.on_enter_press)
        keyboard.add_hotkey('page down', self.on_pagedown_press)
        keyboard.add_hotkey('-', self.on_minus_press)
        keyboard.add_hotkey('+', self.on_plus_press)

    def on_enter_press(self):
        print("Enter key pressed")
        message = f"lap={self.pulsesS1:.0f}"
        self.send_fake_message(message)
        
    def on_pagedown_press(self):
        print("Page Down key pressed")
        message = f"ckm={self.pulsesS1:.0f};{self.pulsesS2:.0f}"
        self.send_fake_message(message)

    def on_minus_press(self):
        print("Minus key pressed")
        message = f"btDown={self.pulsesS1:.0f};{self.pulsesS2:.0f}"
        self.send_fake_message(message)

    def on_plus_press(self):
        print("Plus key pressed")
        message = f"btUp={self.pulsesS1:.0f};{self.pulsesS2:.0f}"
        self.send_fake_message(message)

    def send_fake_message(self, message):
        message += "|"  # Ensure message format matches device requirements
        #print(f"Sending fake message: {message}")
        self.socketServer.send(message)

    def send_fake_pulse_message(self):
        elapsed_time = int((datetime.now() - self.start_time).total_seconds() * 1000)
        message = f"pulse={self.pulsesS1:.0f};{self.pulsesS2:.0f};{elapsed_time};0|\n"
        self.send_fake_message(message)

    def start(self):
        self.socketServer.start()

    def stop(self):
        self.socketServer.stop()
        keyboard.unhook_all()  # Unhook all keyboard listeners on exit

    def run(self):
        self.start()
        previous_elapsed = 0
        previous_pulse_count_s1 = 0
        previous_pulse_count_s2 = 0
        try:
            while True:
                time.sleep(0.1)
                #Test
                #time.sleep(1)
                #self.pulsesS1 += 1.0
                #self.pulsesS2 += 1.0
                #self.send_fake_pulse_message()
                if self.trigger.is_set():
                    if not self.data_queue.empty():
                        dq_message = self.data_queue.get()
                        #print(dq_message)
                        # "00.00 0000 00.00 0000" len=21
                        if self.config.send_pulses_to_RR_enable and dq_message[2] =='.' and dq_message[5] ==' ' and dq_message[10] ==' ' and dq_message[13] =='.' and dq_message[16] ==' ' and len(dq_message) == 21:
                            #print(True)
                            pulse_count_s1 = int(dq_message[6:10])
                            pulse_count_s2 = int(dq_message[17:21])
                            if pulse_count_s1 > previous_pulse_count_s1:
                                self.pulsesS1 += pulse_count_s1 - previous_pulse_count_s1
                            else:
                                self.pulsesS1 += previous_pulse_count_s1- pulse_count_s1
                            if pulse_count_s2 > previous_pulse_count_s2:
                                self.pulsesS2 += pulse_count_s2 - previous_pulse_count_s2
                            else:
                                self.pulsesS2 += previous_pulse_count_s2 - pulse_count_s2
                            #print(pulse_count_s1, pulse_count_s2)
                            self.send_fake_pulse_message()
                            previous_pulse_count_s1 = pulse_count_s1
                            previous_pulse_count_s2 = pulse_count_s2
                    self.trigger.clear()
						
        except KeyboardInterrupt:
            print("Stopping server due to KeyboardInterrupt")
            self.stop()
