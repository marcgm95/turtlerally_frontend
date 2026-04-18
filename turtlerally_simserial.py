import serial
import time
import random

from turtlerally_config import backend_wheel_perimeter_m

# Method for LINUX BASED
# install 
# sudo apt-get install socat
# Open Serial with following command:
# socat -d -d pty,raw,echo=0 pty,raw,echo=0
# it creates two ports: sender and receiver

#Method for WINDOWS
""" Install application to create virtual ports. HHDVirtualSerialPort Tools is free"
 * Config the input and output ports, as example COM2 and COM3
 * Run this python in parallel to the main application. This one sends info and the other receives info
 """


# Replace with the appropriate virtual serial port
SERIAL_PORT_DEBUG = "COM2"
BAUD_RATE_DEBUG = 115200 # Match the baud rate debug with the one in the main config (turtlerally_config.py)

# Open the serial port
ser = serial.Serial(SERIAL_PORT_DEBUG, BAUD_RATE_DEBUG, timeout=0.2)

def calcFreq(base_speed):
    speed_kmh = base_speed + random.uniform(-0.5, 0.5)
    speed_mps = 1000 / 3600 * speed_kmh
    wheel_diam_m = backend_wheel_perimeter_m
    wheel_perimeter = wheel_diam_m * 3.1415
    freqHz = speed_mps / wheel_perimeter
    
    return freqHz
    
def sim_pulses(freqHz, pulses, pulses_frac, send_s):
    """
    The function enables creation of frames in serial comm to stub sensors
    :param freqHz: Frequency given from the sensor
    :param pulses: Value given from the sensor
    :param send_s: parameter for time period calculation
    :return:
    """
    # Generate fractions of pulse and convert the integer part, not rounding per period
    pulses_frac += freqHz * send_s
    inc = int(pulses_frac)
    pulses_frac -= inc
    pulses += inc
    if pulses > 9999:
        pulses = pulses % 10000
    return pulses, pulses_frac

try:
    pulses = 0
    pulses_frac = 0
    freqHz = 0
    while True:
        # Write the same string to the serial port
        #simulated_data = "00.00 0000 00.00 0000\n"
        freqHz = calcFreq(100)
        pulses, pulses_frac = sim_pulses(freqHz, pulses, pulses_frac, 0.2)
        freqHz_str = f"{freqHz:5.2f}"
        simulated_data = freqHz_str + " " + f"{pulses:04.0f}" + " 00.00 0000\n"
        ser.write(simulated_data.encode('utf-8'))
        print(f"Sent: {simulated_data.strip()}")
        time.sleep(0.2)  # Send data every second
except KeyboardInterrupt:
    print("Simulation stopped.")
finally:
    ser.close()
