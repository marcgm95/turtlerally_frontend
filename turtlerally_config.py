#GENERAL WIFI CONFIG FOR COMMUNICATION WITH RABBIT RALLY
sensors = 1 # Sensors default: [0 = both; 1 = s1; 2 = s2]
send_pulses_to_RR_enable = True
listen_RR_enable = True
listen_RR_IP = "192.168.4.16" # IP from RR to send the alive message (check mobilephone for IP)
listen_RR_PORT = 7532 # Port to listen from RR

#SENSOR INPUT SELECTION
sensor_input_mode = "serial"      # "serial", "wifi", "auto"
wifi_sensor_bind_ip = "0.0.0.0"
wifi_sensor_port = 22334
wifi_sensor_protocol = "tcp"    # o "udp"
wifi_sensor_timeout = 0.1
wifi_sensor_frame_timeout_s = 1.0

#DEBUG MODE SERIAL
SIMULATOR_MODE = True # Change to true to enable simulation mode for Serial communication
if SIMULATOR_MODE:
    serial_port = "COM3" # Replace the port to be used as receiver for simulation
    serial_baudrate = 115200
    serial_timeout = 1
else:
    # Configure Serial Port, Baudrate and timeout (BACKEND)
    serial_port = "COM4" #'/dev/ttyACM0'
    serial_baudrate = 115200
    serial_timeout = 0.2

#DEBUG MODE WIFI (TCP)
WIFI_DEBUG_MODE = True # Change to true to enable simulation mode for Wifi communication

#DEBUG MODE WIFI (UDP) TO LISTEN RR
DEBUG_UDP_MODE = True

#DEBUG FRONTEND MODE
DEBUG_FRONTEND_MODE = False # Change to true to enable simulation mode for frontend values

#BACKEND
backend_serial_message_period_ms = 200.0 #ms
backend_pulses_per_revolution = 1.0
#backend_wheel_perimeter_m = 0.5 * 3.14159265
backend_wheel_perimeter_m = 1.778665672960143
    
#SECTIONS
csv_path = 'turtlerally_sections.csv'

#LED Ring
LEDRing_mode = 0 			# 0=[OFF]; 1=[ON, Source:RR] ; 2=[ON, Source:Backend]
LEDRing_brightness = 0.1 	# max=1
LEDRing_origin = 6 			# From 0 to 11, clockwise. = is the first led.
# Absolute boundaries values, in seconds. List of 12 values, one for each led.
#LEDRING_boundaries = [0.1, 0.2, 0.3, 0.4, 0.5, 0.75, 1, 1.5, 2, 3, 4, 5]
LEDRING_boundaries = [0.1, 0.2, 0.3, 0.5, 0.75, 1, 1.5, 2]
