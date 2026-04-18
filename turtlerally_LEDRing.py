import time
import board
import neopixel
import bisect

class MainApp:
    def __init__(self, config, data_queue_back, trigger_back, data_queue_RxFromRR, trigger_RxFromRR):
        self.data_queue_back = data_queue_back
        self.trigger_back = trigger_back
        self.data_queue_RxFromRR = data_queue_RxFromRR
        self.trigger_RxFromRR = trigger_RxFromRR
        
        # Data From config
        self.mode = config.LEDRing_mode
        self.brightness = config.LEDRing_brightness
        self.origin = config.LEDRing_origin
        self.boundaries = config.LEDRING_boundaries
        
        #LED ring configuration
        self.LED_COUNT = 12 			# Number of LEDs in the ring
        self.PIN = board.D18 		# GPIO 18 (PIN 12)
        self.ORDER = neopixel.GRB	# LED color order (Green, Red, Blue)
        
        #COLORS
        self.red = (255, 0, 0)
        self.green = (0, 255, 0)
        self.blue = (0, 0, 255)
        
        # Initialize the Neopixel object
        self.pixels = neopixel.NeoPixel(self.PIN, self.LED_COUNT, brightness=self.brightness, auto_write=False, pixel_order=self.ORDER)
    
    def clear_ring(self):
        """ Turn off all LEDs. """
        self.pixels.fill((0,0,0))
        self.pixels.show()
	
    def color_wipe(self, color, wait_ms=50):
        """ Wipe color across display a pixel at a time. """
        for i in range(self.LED_COUNT):
            self.pixels[i] = color
            self.pixels.show()
            time.sleep(wait_ms / 1000.0)
    
    def classify_pace(self, pace, boundaries):
        """
        Classify the pace based on irregular sections, with negative output for negative pace,
        and return max classification if outside range.

        Args:
            pace (float): The pace in seconds, can be positive or negative.

        Returns:
            int: The classification of the pace, positive for positive pace, negative for negative pace,
                 12 for positive outside range, -12 for negative outside range.
        """
        abs_pace = abs(pace)  # Work with the absolute value of pace

        # Use binary search to find the position in the boundaries
        classification = bisect.bisect_left(boundaries, abs_pace)

        # If outside the range, return the maximum classification
        if abs_pace > boundaries[-1]:
            classification = len(boundaries)

        # Return positive for positive pace, negative for negative pace
        return classification if pace >= 0 else -classification
        
    def fill_pixels(self, input_val, origin, color_neg=(255, 0, 0), color_pos=(0, 255, 0), color_zero=(0, 0, 255)):
        """
        Creates a list filled with a specified tuple based on the input value, with the rest as zeros.

        Args:
            input_val (int): An integer between -12 and 12 (inclusive).
            fill_value (tuple): The value to fill the list with (default is (255, 0, 0)).
        
        Returns:
            list: A list of length 12 with the specified tuple and zeros.
        """
        #Invert to have positive values increasing anti-clockwise
        input_val = -input_val
        
        # Initialize a list with 12 zero tuples (0,0,0)
        lst = [(0,0,0),(0,0,0),(0,0,0),(0,0,0),(0,0,0),(0,0,0),(0,0,0),(0,0,0),(0,0,0),(0,0,0),(0,0,0),(0,0,0)]          
        
        if input_val > 0:
            # Fill the first `input_val` indices with the tuple
            lst[:input_val] = [color_neg] * input_val
        elif input_val < 0:
            # Fill the last `abs(input_val)` indices with the tuple
            lst[-abs(input_val):] = [color_pos] * abs(input_val)
            #print(lst)
        else:
            # Fill for case zero
            lst[5:7] = [color_zero] * 2
        lst = lst[-origin:] + lst[:-origin]
        return(lst)

    def run(self):
        try:
            pace = 0.0
            while True:
                if self.mode == 1:
                    if self.trigger_RxFromRR.is_set():
                        if not self.data_queue_RxFromRR.empty():
                            pace = self.data_queue_RxFromRR.get()
                        self.trigger_RxFromRR.clear()
                elif self.mode == 2:
                    if self.trigger_back.is_set():
                        if not self.data_queue_back.empty():
                            pace = self.data_queue_back.get()
                        self.trigger_back.clear()
                else:
                    pace = 0.0
                #Test
                #pace = float(input())
                
                #LED Logic and activation
                classification = self.classify_pace(pace, self.boundaries)
                lst = self.fill_pixels(classification, self.origin, self.red, self.green, self.blue)
                self.pixels[:] = lst[:]
                self.pixels.show()
                time.sleep(0.1)
		
        except KeyboardInterrupt:
            # Clear the LED ring whent the script is interrupted
            self.clear_ring()
        except:
            self.clear_ring()
        finally:
            self.clear_ring()
