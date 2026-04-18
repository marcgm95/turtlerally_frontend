import serial
import time
import numpy as np

from turtlerally_config import SIMULATOR_MODE
from turtlerally_config import WIFI_DEBUG_MODE
from turtlerally_input_serial import SerialSensorReader
from turtlerally_input_wifi import WiFiSensorReader
from turtlerally_input_manager import InputManager


def precompute_segment_times_distances(segments, track_is_wet):
    """
    Precompute target times for each segment and cumulative times up to each segment.
    """
    # Convert segments to a NumPy array for efficient operations
    segments_array = np.array(segments)
    
    # Extract start distances, end distances, and speeds
    start_distances_m = segments_array[:, 0] * 1000
    end_distances_m = segments_array[:, 1] * 1000
    speeds_mps = segments_array[:, 2] / 3.6
    if track_is_wet:
        speeds_mps = segments_array[:, 3] / 3.6
    
    # Calculate segment distances and target times
    segment_distances_m = end_distances_m - start_distances_m
    segment_target_times_seconds = segment_distances_m / speeds_mps
    
    # Accumulate target times
    accumulated_target_times_seconds = np.cumsum(segment_target_times_seconds)
    
    return start_distances_m, end_distances_m, speeds_mps, segment_target_times_seconds, accumulated_target_times_seconds, segment_distances_m

def calculate_pace_difference(current_time_seconds, current_distance_m, start_distances_m, end_distances_m, speeds_mps, segment_target_times_seconds, accumulated_target_times_seconds, segment_distances_m):
    """
    Calculate the time difference using precomputed segment times.
    """
    # Find the segment where the current distance falls
    segment_indices = np.where(current_distance_m <= end_distances_m)[0]
    #print("segment_indices ", segment_indices)
    
    if len(segment_indices) == 0:
        # If current distance is beyond all segments
        last_index = len(start_distances_m) - 1
        total_target_time_seconds = accumulated_target_times_seconds[last_index] + \
                            (current_distance_m - end_distances_m[last_index]) / speeds_mps[last_index] * 3600
        time_difference_seconds = current_time_seconds - total_target_time_seconds
        return time_difference_seconds
    
    # Take the first segment index where current_distance is within the segment
    segment_index = segment_indices[0]
    
    # Calculate distance in segment
    distance_in_segment_m = current_distance_m - start_distances_m[segment_index]
    
    # Calculate the target time for the distance covered in the current segment
    segment_target_time_seconds = (distance_in_segment_m / segment_distances_m[segment_index]) * segment_target_times_seconds[segment_index]
    
    # Calculate total target time up to the current distance
    if segment_index > 0:
        accumulated_target_time_seconds = segment_target_time_seconds + accumulated_target_times_seconds[segment_index - 1]
    else:
        accumulated_target_time_seconds = segment_target_time_seconds
    
    # Calculate time difference
    time_difference_seconds = current_time_seconds - accumulated_target_time_seconds
    
    return time_difference_seconds

def precompute_calculation(wheel_perimeter_m, serial_message_period_s, pulses_per_revolution):
    freq_to_mps = wheel_perimeter_m / pulses_per_revolution
    freq_to_kmh = freq_to_mps * 3.6
    freq_to_travelled_distance_m = freq_to_mps * serial_message_period_s
    return freq_to_kmh, freq_to_travelled_distance_m
    
def main_calculation(freq_to_kmh, freq_to_travelled_distance_m, total_travelled_distance_m, freqHz, pulse_count):
    vehicle_speed_kmh = freqHz * freq_to_kmh
    total_travelled_distance_m += freqHz * freq_to_travelled_distance_m
    return total_travelled_distance_m, vehicle_speed_kmh

# def configure_serial_port(port, baudrate=115200, timeout=1):
#     """Configure the serial port to receive data from sensors in serial protocol"""
#     try:
#         ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)
#         print(f"Backend: Serial port {port} opened successfully")
#         return ser
#     except serial.SerialException as e:
#         print(f"Backend: Error opening serial port: {e}")
#         return None

def extract_data(data, sensors):
    freqHz = 0.0
    pulse_count = 0
    invalid_data = False
    #print(data)
    try:
        # "00.00 0000 00.00 0000" len=21
        if data[2] =='.' and data[5] ==' ' and data[10] ==' ' and data[13] =='.' and data[16] ==' ' and len(data) == 21:
            freqHz_s1 = float(data[0:5])
            pulse_count_s1 = int(data[6:10])
            freqHz_s2 = float(data[11:16])
            pulse_count_s2 = int(data[17:21])
            #print(freqHz_s1, pulse_count_s1, freqHz_s2, pulse_count_s2)
            if sensors == 1:
                freqHz = freqHz_s1
                pulse_count = pulse_count_s1
            elif sensors == 2:
                freqHz = freqHz_s2
                pulse_count = pulse_count_s2
            else:
                freqHz = (freqHz_s1 + freqHz_s2) / 2.0
                pulse_count = int((pulse_count_s1 + pulse_count_s2) / 2.0)
        else:
            freqHz = 0.0
            pulse_count = 0
            invalid_data = True
            print("Backend: Received Serial invalid data")
    except:
        freqHz = 0.0
        pulse_count = 0
        invalid_data = True
        print("Backend: Received Serial invalid data")
    return invalid_data, freqHz, pulse_count

def setup_input_manager(config):
    serial_reader = None
    wifi_reader = None
    mode = getattr(config, 'sensor_input_mode', 'serial')

    if mode in ('serial', 'auto'):
        serial_reader = SerialSensorReader(
            port=config.serial_port,
            baudrate=config.serial_baudrate,
            timeout=config.serial_timeout,
            simulator_mode=SIMULATOR_MODE,
        )
        serial_reader.open()

    if mode in ('wifi', 'auto'):
        wifi_reader = WiFiSensorReader(
            host=getattr(config, 'wifi_sensor_bind_ip', '0.0.0.0'),
            port=getattr(config, 'wifi_sensor_port', 22334),
            protocol=getattr(config, 'wifi_sensor_protocol', 'tcp'),
            timeout=getattr(config, 'wifi_sensor_timeout', 0.1),
            debug=getattr(config, 'WIFI_DEBUG_MODE', False)
        )
        wifi_reader.open()

    return InputManager(config, serial_reader=serial_reader, wifi_reader=wifi_reader)

#def read_serial_and_execute_calc(ser, data_queue_out, trigger_event_out, data_queue_in, trigger_event_in, data_queue_backtoTxToRR, trigger_event_backtoTxToRR, data_queue_BackendtoLEDRing, trigger_event_BackendtoLEDRing, sections, wheel_perimeter_m, serial_message_period_ms, pulses_per_revolution, sensors, backtoTxToRR_enable, LEDRing_mode):
def read_input_and_execute_calc(input_manager, data_queue_out, trigger_event_out, data_queue_in, trigger_event_in,
                                    data_queue_backtoTxToRR, trigger_event_backtoTxToRR, data_queue_BackendtoLEDRing,
                                    trigger_event_BackendtoLEDRing, sections, wheel_perimeter_m,
                                    serial_message_period_ms, pulses_per_revolution, sensors, backtoTxToRR_enable,
                                    LEDRing_mode):
    """Process incoming data and handle messages"""
    if input_manager is None:
        print("Backend: Input manager not initialized")
        return
    
    # Init serial read variables
    last_time = time.time()  # Track the last received message time
    last_valid_freqHz = 0.0
    last_valid_pulse_count = 0
    invalid_data = False
    pace_calc_enable = True
    
    # Default first section precompute
    track_is_wet = False
    section_name = list(sections)[0]
    precomp_segments = precompute_segment_times_distances(sections[section_name], track_is_wet)
    
    # Init calc variables
    total_travelled_distance_m = 0
    serial_message_period_s = serial_message_period_ms * 0.001
    freq_to_kmh, freq_to_travelled_distance_m = precompute_calculation(wheel_perimeter_m, serial_message_period_s, pulses_per_revolution)
    start_time_s = time.time()
    time_since_start_s = time.time()
    crono_section_started = False
    general_cal_mode = False
    revolutions_sum_cal_mode = 0.0
    distance_cal_mode_m = 0.0

    while True:
        try:
            frame_info = input_manager.read_frame()

            if frame_info is not None:
                source, data, rx_timestamp = frame_info
                current_time = time.time()
                time_since_start_s = current_time -  start_time_s
                # extract_data
                invalid_data, freqHz, pulse_count = extract_data(data, sensors)  # Coment it if you want to debug
                message_period_ms = int((current_time - last_time) * 1000)  # Calculate interval in milliseconds

                # Update last received time and last valid data
                if not invalid_data:
                    last_time = current_time
                    last_valid_freqHz = freqHz
                    last_valid_pulse_count = pulse_count
                    
                # Handle invalid received serial data
                if invalid_data:
                    if message_period_ms < 3000:
                        freqHz = last_valid_freqHz
                        pulse_count = last_valid_pulse_count
                    else:
                        freqHz = 0.0
                        pulse_count = 0.0
                
                # main_calculation: distance travelled and vehicle speed
                total_travelled_distance_m, vehicle_speed_kmh = main_calculation(freq_to_kmh,
                                                                                 freq_to_travelled_distance_m,
                                                                                 total_travelled_distance_m,
                                                                                 freqHz, pulse_count)
                #print(total_travelled_distance_m)
                
                # pace calculation
                if pace_calc_enable:
                    pace_diff_s = calculate_pace_difference(time_since_start_s, total_travelled_distance_m,
                                                            precomp_segments[0], precomp_segments[1],
                                                            precomp_segments[2], precomp_segments[3],
                                                            precomp_segments[4], precomp_segments[5])
                else:
                    pace_diff_s = 0

                if not crono_section_started:
                    pace_diff_s = 0
                    total_travelled_distance_m = 0
                    
                if general_cal_mode:
                    revolutions_sum_cal_mode += freqHz * serial_message_period_s / pulses_per_revolution
                
                # Pushes the data in the data_queue_out and event trigger (to Frontend)
                data_queue_out.put((vehicle_speed_kmh, total_travelled_distance_m, pace_diff_s,
                                    time_since_start_s, data, invalid_data))
                trigger_event_out.set()
                
                # Push the data in the data_queue_backtoTxToRR and event trigger (to TxToRR)
                if backtoTxToRR_enable:
                    data_queue_backtoTxToRR.put(data)
                    trigger_event_backtoTxToRR.set()
                
                # Put the data in the data_queue_BackendtoLEDRing and event trigger (to LEDRing)
                if LEDRing_mode == 2:
                    data_queue_BackendtoLEDRing.put(pace_diff_s)
                    trigger_event_BackendtoLEDRing.set()
            
            if trigger_event_in.is_set():
                if not data_queue_in.empty():
                    dq_message = data_queue_in.get()
                    if dq_message[0] == 0:
                        # Set TC Section
                        section_name = dq_message[1]
                        precomp_segments = precompute_segment_times_distances(sections[section_name], track_is_wet)
                    elif dq_message[0] == 1:
                        # Set Track Condition
                        track_is_wet = dq_message[1]
                        precomp_segments = precompute_segment_times_distances(sections[section_name], track_is_wet)
                    elif dq_message[0] == 10:
                        # CAL Start Line / No competition
                        crono_section_started = False
                        total_travelled_distance_m = 0
                    elif dq_message[0] == 11:
                        # CAL first section / Start competition
                        crono_section_started = True
                        start_time_s = time.time()
                        total_travelled_distance_m = dq_message[1]
                    elif dq_message[0] == 12:
                        # CAL Intermediate section / Competing
                        crono_section_started = True
                        total_travelled_distance_m = dq_message[1]
                    elif dq_message[0] == 13:
                        total_travelled_distance_m += dq_message[1]
                    elif dq_message[0] == 20:
                        # Set Sensors Config
                        sensors = dq_message[1]
                    elif dq_message[0] == 21:
                        # Set Mode. If True -> calc pace; If False -> No calc pace
                        #Not in use. Thought to save computer load.
                        #pace_calc_enable = dq_message[1]
                        pass
                    elif dq_message[0] == 98:
                        # Start Calibration Process
                        crono_section_started = True
                        total_travelled_distance_m = dq_message[1]
                        general_cal_mode = True
                        revolutions_sum_cal_mode = 0.0
                    elif dq_message[0] == 99:
                        # End Calibration Process
                        crono_section_started = True
                        distance_cal_mode_m = dq_message[1]
                        general_cal_mode = False
                        if revolutions_sum_cal_mode > 0:
                            wheel_perimeter_m = distance_cal_mode_m / revolutions_sum_cal_mode
                            freq_to_kmh, freq_to_travelled_distance_m = precompute_calculation(wheel_perimeter_m, serial_message_period_s, pulses_per_revolution)
                            print("CAL Value:")
                            print(wheel_perimeter_m)
                        else:
                            print("Backend: Calibration Error")
                    trigger_event_in.clear()
                    print("Backend: Message Received")
            
            time.sleep(0.01)  # Small delay to avoid excessive CPU usage
        except Exception as error:
            # handle the exception
            print("Backend: An error occurred in the backend loop:", type(error).__name__, "-", error)
            time.sleep(0.2)  # Delay before attempting to reconnect
            continue
        except KeyboardInterrupt:
            break
            
 

def main(config, sections, data_queue_backtofront, trigger_event_backtofront, data_queue_fronttoback,
         trigger_event_fronttoback, data_queue_backtoTxToRR, trigger_event_backtoTxToRR, data_queue_BackendtoLEDRing,
         trigger_event_BackendtoLEDRing):

    input_manager = setup_input_manager(config)
    #ser = configure_serial_port(config.serial_port, config.serial_baudrate, config.serial_timeout) # Execution of function to configure serial port
    
    # read_serial_data
    read_input_and_execute_calc(input_manager, data_queue_backtofront, trigger_event_backtofront, data_queue_fronttoback,
                                trigger_event_fronttoback, data_queue_backtoTxToRR, trigger_event_backtoTxToRR,
                                data_queue_BackendtoLEDRing, trigger_event_BackendtoLEDRing, sections,
                                config.backend_wheel_perimeter_m, config.backend_serial_message_period_ms,
                                config.backend_pulses_per_revolution, config.sensors, config.send_pulses_to_RR_enable,
                                config.LEDRing_mode)
