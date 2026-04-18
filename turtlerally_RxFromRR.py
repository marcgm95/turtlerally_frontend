import socket
import threading
import time
from datetime import datetime

from turtlerally_config import DEBUG_UDP_MODE

class MainApp:
    def __init__(self, config, data_queue_front, trigger_front, data_queue_LEDRing, trigger_LEDRing):
        self.config = config
        self.data_queue_front = data_queue_front
        self.trigger_front = trigger_front
        self.data_queue_LEDRing = data_queue_LEDRing
        self.trigger_LEDRing = trigger_LEDRing
        self.shutdown_event = threading.Event()
        self.message_list = ['','','','','','','','','']
        self.message_list_old = ['','','','','','','','','']
        self.message_list_parsed = [['',''],['',''],['',''],'','','',['',''],'','']
        self.pace = 0.0
        self.pace_old = 0.0

    def start_udp_listener(self):
        """Create and configure socket UDP to listen data from RR"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("", self.config.listen_RR_PORT))
        print(f"Listening for UDP packets on port {self.config.listen_RR_PORT}...")

        try:
            while not self.shutdown_event.is_set():
                sock.settimeout(1)  # Allow periodic checks for shutdown
                try:
                    data, addr = sock.recvfrom(4096)  # Buffer size of 4096 bytes
                    message = data.decode('utf-8', errors='replace')
                    if DEBUG_UDP_MODE:
                        print(f"[UDP_Debug]: From {addr} | raw bytes: {data}")
                        print(f"[UDP_Debug]: Decoded received messages are: {repr(message)}")

                    # Divide each part by '|' and process the complete UDP package
                    fragments = message.split('|')
                    for frag in fragments:
                        frag = frag.strip()
                        if not frag:
                            continue # Ignore empty fragments (no digits)

                        # Detect FIN in any fragment
                        if 'FIN' in frag.upper():
                            if DEBUG_UDP_MODE:
                                print(f"[UDP_Debug]: FIN detected in fragment: {frag}. Stage is finished")
                            #self.fin_received = True # Todo send info to frontend if desired

                        # Obtain first char of any fragment as type
                        type_char = frag[0]
                        # If first character is a digit 0 to 8, use it
                        if type_char in '012345678':
                            type = int(type_char)
                            # Store complete fragment with prefix in corresponding index
                            if type <= 8:
                                self.message_list[type] = frag
                                if DEBUG_UDP_MODE:
                                    print(f"[UDP_Debug]: Stored data as {type}: {frag}")
                            else: # Any other character
                                self.message_list[8] = frag
                                if DEBUG_UDP_MODE:
                                    print(f"[UDP_Debug]: Unknown type (stored in 8): {frag}")
                except socket.timeout:
                    print(f"Socket timeout for UDP listener")
                    continue
        finally:
            sock.close()
            print("UDP listener closed.")
            
    def send_to_frontend(self):
        """Parse and send the received RR data into the TurtleRally frontend"""
        try:
            while not self.shutdown_event.is_set():
                for i in [0,1,2,5,6,7,8]:
                    try:
                        if self.message_list[i] != self.message_list_old[i]:
                            message = self.message_list[i]
                            if not message:
                                continue
                            # Parse by type
                            if i == 0: # Times "0HH:MM:SS;HH:MM:SS"
                                # Clean first '0' character
                                payload = message[1:]
                                parts = payload.split(';') # Split fragment in parts by ';'
                                if len(parts) >= 2:
                                    self.message_list_parsed[0][0] = parts[0].strip() # Global Time
                                    self.message_list_parsed[0][1] = parts[1].strip() # Section Time

                            elif i == 1: # Odometer and current speed









                            if i in [0,1,2]:
                                message = message[1:-1]
                            parts = message.split(';')
                            self.message_list_parsed[i][0] = parts[0] # Global Time
                            self.message_list_parsed[i][1] = parts[1] # Section Time
                        if i == 5:
                            message = message[1:-1]
                            self.message_list_parsed[i] = message
                            
                            #Check if message is convert float
                            try:
                                self.pace = float(message)
                            except ValueError:
                                self.pace = 0.0
                        if i == 6:
                            message = message[1:-1]
                            parts = message.split('>')
                            self.message_list_parsed[i][0] = parts[0] # Current section speed
                            self.message_list_parsed[i][1] = parts[1] # Next section speed
                        if i == 7:
                            message = message[1:-1]
                            self.message_list_parsed[i] = message
                        if i == 8:
                            self.message_list_parsed[i] = message
                        self.message_list_old[i] = message
                    except Exception as e:
                        print(f"[send_to_frontend]: Error parsing type {i}: {e}")
                # Put data to queue
                #print(self.message_list_parsed)
                self.data_queue_front.put(self.message_list_parsed)
                self.trigger_front.set()
                if (self.config.LEDRing_mode == 1) and (self.pace != self.pace_old):
                    # Put data to LEDRing queue
                    self.data_queue_LEDRing.put(self.pace)
                    self.trigger_LEDRing.set()
                    self.pace_old = self.pace
                time.sleep(0.2)
    except Exception as e:
        print(f"Error in send_to_frontend: {e}")
    finally:
        print("Sender to frontend stopped.")

    def send_to_master(self, sock):
        try:
            while not self.shutdown_event.is_set():
                message = "hello"
                sock.sendto(message.encode('utf-8'), (self.config.listen_RR_IP, self.config.listen_RR_PORT))
                time.sleep(5)
        except Exception as e:
            print(f"Error in send_to_master: {e}")
        finally:
            print("Sender to master stopped.")

    def run(self):
        # Create a socket for sending messages
        send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Start the UDP listener in a separate thread
        listener_thread = threading.Thread(target=self.start_udp_listener)
        listener_thread.daemon = True
        listener_thread.start()

        # Start sending messages to the Android Master
        sender_thread = threading.Thread(target=self.send_to_master, args=(send_sock,))
        sender_thread.daemon = True
        sender_thread.start()
        
        # Start sending messages to the frontend
        sender_front_thread = threading.Thread(target=self.send_to_frontend)
        sender_front_thread.daemon = True
        sender_front_thread.start()

        try:
            while True:
                time.sleep(1)  # Keep main thread alive
        except KeyboardInterrupt:
            print("Interrupt received, shutting down...")
        finally:
            # Signal threads to shut down
            self.shutdown_event.set()
            listener_thread.join()
            sender_thread.join()
            sender_front_thread.join()
            send_sock.close()
            print("Clean exit.")

# Usage example:
# Ensure your config object is defined and has the required properties like `listen_RR_IP` and `listen_RR_PORT`.
# config = Config(...)
# app = MainApp(config, data_queue, trigger)
# app.run()
