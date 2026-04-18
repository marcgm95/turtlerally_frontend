import tkinter as tk
from tkinter import ttk
import sv_ttk
import threading
import queue

import turtlerally_config as config
import turtlerally_backend
import turtlerally_frontend
import turtlerally_importsections
import turtlerally_TxToRR
import turtlerally_RxFromRR
import turtlerally_LEDRing

# Queue and event for passing data from backend to frontend
data_queue_backtofront = queue.Queue()
trigger_event_backtofront = threading.Event()

# Queue and event for passing data from frontend to backend
data_queue_fronttoback = queue.Queue()
trigger_event_fronttoback = threading.Event()

# Queue and event for passing data from backend to TxToRR
data_queue_backtoTxToRR = queue.Queue()
trigger_event_backtoTxToRR = threading.Event()

# Queue and event for passing data from RxFromRR to frontend
data_queue_RxFromRRtofront = queue.Queue()
trigger_event_RxFromRRtofront = threading.Event()

# Queue and event for passing data from RxFromRR to LEDRing
data_queue_RxFromRRtoLEDRing = queue.Queue()
trigger_event_RxFromRRtoLEDRing = threading.Event()

# Queue and event for passing data from Backend to LEDRing
data_queue_BackendtoLEDRing = queue.Queue()
trigger_event_BackendtoLEDRing = threading.Event()



def main():
    # Import sections
    sections = turtlerally_importsections.processSegments(config.csv_path)
    #print (sections)
    
    # Initialize the GUI
    root = tk.Tk()
    app = turtlerally_frontend.RallyApp(root, config, sections, data_queue_backtofront, trigger_event_backtofront,
                                                                data_queue_fronttoback, trigger_event_fronttoback,
                                                                data_queue_RxFromRRtofront, trigger_event_RxFromRRtofront)

    # Start the backend thread
    backend_thread = threading.Thread(target=turtlerally_backend.main, args=(config, sections, data_queue_backtofront, trigger_event_backtofront, 
                                                                                                data_queue_fronttoback, trigger_event_fronttoback,
                                                                                                data_queue_backtoTxToRR, trigger_event_backtoTxToRR,
                                                                                                data_queue_BackendtoLEDRing, trigger_event_BackendtoLEDRing))
    backend_thread.daemon = True  # Daemonize thread to close when the main program exits
    backend_thread.start()
    
    # Start the TxToRR thread (TurtleRally -> RR)
    TxToRR_app_instance = turtlerally_TxToRR.MainApp(config, data_queue_backtoTxToRR, trigger_event_backtoTxToRR)
    TxToRR_thread = threading.Thread(target=TxToRR_app_instance.run)
    TxToRR_thread.daemon = True  # Daemonize thread to close when the main program exits
    TxToRR_thread.start()
        
    # Start the RxFromRR thread (RR -> TurtleRally)
    if config.listen_RR_enable:
        RxFromRR_app_instance = turtlerally_RxFromRR.MainApp(config, data_queue_RxFromRRtofront, trigger_event_RxFromRRtofront, data_queue_RxFromRRtoLEDRing, trigger_event_RxFromRRtoLEDRing)
        RxFromRR_thread = threading.Thread(target=RxFromRR_app_instance.run)
        RxFromRR_thread.daemon = True  # Daemonize thread to close when the main program exits
        RxFromRR_thread.start()
        
    # Start the LEDRing thread
    if config.LEDRing_mode != 0:
        LEDRing_app_instance = turtlerally_LEDRing.MainApp(config, data_queue_BackendtoLEDRing, trigger_event_BackendtoLEDRing, data_queue_RxFromRRtoLEDRing, trigger_event_RxFromRRtoLEDRing)
        LEDRing_thread = threading.Thread(target=LEDRing_app_instance.run)
        LEDRing_thread.daemon = True  # Daemonize thread to close when the main program exits
        LEDRing_thread.start()
    
    # Dark Theme
    sv_ttk.set_theme("dark")

    # Start the Tkinter main loop
    root.mainloop()

if __name__ == "__main__":
    main()

