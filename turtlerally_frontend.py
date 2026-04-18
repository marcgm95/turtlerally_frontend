import tkinter as tk
from tkinter import ttk
import sv_ttk
import random
import datetime
import numpy as np

from turtlerally_config import DEBUG_FRONTEND_MODE


class RallyApp:
    def __init__(self, root, config, sections, data_queue_backtofront, trigger_event_backtofront,
                 data_queue_fronttoback, trigger_event_fronttoback,
                 data_queue_RxFromRRtofront, trigger_event_RxFromRRtofront):
        self.root = root
        self.root.title("Rally App")
        self.root.geometry('1024x600')
        self.config_tr = config

        # Listen Keys
        self.divide_disabled = False  # Flag to disable for 1 second


        self.multiply_disabled = False
        self.add_disabled = False
        self.subtract_disabled = False
        root.bind('<KP_Divide>', self.on_numpad_divide)  # Bind numpad divide key
        root.bind('<KP_Multiply>', self.on_numpad_multiply)
        root.bind('<KP_Add>', self.on_numpad_add)
        root.bind('<KP_Subtract>', self.on_numpad_subtract)

        self.data_queue_in = data_queue_backtofront
        self.trigger_event_in = trigger_event_backtofront
        self.data_queue_out = data_queue_fronttoback
        self.trigger_event_out = trigger_event_fronttoback
        self.data_queue_RxFromRRtofront = data_queue_RxFromRRtofront
        self.trigger_event_RxFromRRtofront = trigger_event_RxFromRRtofront
        self.sections = sections
        self.selectedSectionKey = 'TC1'  # default
        self.selectedSection = self.sections[self.selectedSectionKey]  # default
        self.trackIsWet = False
        self.importSectionData()
        # print(self.selectedSection)

        # CRITICAL Initial Variables
        self.SpeedWheel_kmh = 0.0
        self.totalTraveledDistance_m = 0.0
        self.paceDiff_s = 0.0
        self.timeSinceStart_s = 0.0
        self.rawSerialData = ""
        self.serialInvalidData = False
        self.RR_message_list = []

        # Initial Variables
        self.SpeedWheelStr_kmh = "000.0"
        self.totalTraveledDistanceStr_m = "00000"
        self.nextSegmentDistanceStr_m = "00000"
        self.SpeedTargetStr_kmh = "00.00"
        self.SpeedNextTargetStr_kmh = "00.00"
        self.PaceStr_s = "+999.9"
        self.timeSinceStartStr_s = "0000"
        self.Pace_text = "NONE"

        # Initial RR variables
        self.RR_global_time = '99:99:99'
        self.RR_section_time = '88:88:88'
        self.RR_odo_km_1 = '0.000'
        self.RR_odo_km_2 = '0'
        self.RR_regressive_section_km = '99.999'
        self.RR_regressive_next_ref_km = '9.999'
        self.RR_pace_s = '-0.00'
        self.RR_current_target_speed = 'V99'
        self.RR_current_target_speed_previous = 'V99'
        self.RR_current_target_speed_timer = 0
        self.RR_next_target_speed = 'E99'
        self.RR_number_ref = '999'
        self.RR_unknown_data = ''
        self.RR_odo_km_1_previous = '0.000'
        self.RR_speed_kmh = '00.0'

        # Font for all text in frontend
        self.fontName = 'Consolas'
        # self.fontName = ''

        # Setup the notebook (tab control)
        self.setup_tabs()

        # Populate the tabs
        self.populate_tab1()
        self.populate_tab2()
        self.populate_tab3()
        self.populate_tab4()
        self.populate_tab5()

        # Start the periodic update loop
        self.update_loop()
        self.update_loop_1s()

    ########################################## Section for TK tabs #########################################################
    def setup_tabs(self):
        """Create and organize the tabs"""
        self.tabControl = ttk.Notebook(self.root)

        # Create frames for each tab
        self.tab1 = ttk.Frame(self.tabControl)
        self.tab2 = ttk.Frame(self.tabControl)
        self.tab3 = ttk.Frame(self.tabControl)
        self.tab4 = ttk.Frame(self.tabControl)
        self.tab5 = ttk.Frame(self.tabControl)

        # Add tabs to the notebook
        self.tabControl.add(self.tab2, text='RoadBook')
        self.tabControl.add(self.tab1, text='Speed Sections')
        self.tabControl.add(self.tab3, text='Calibration')
        self.tabControl.add(self.tab4, text='TC Table')
        self.tabControl.add(self.tab5, text='Mode & Sensors')
        self.tabControl.pack(expand=1, fill="both")

    def populate_tab1(self):
        """Populate the 'Speed Sections' tab with widgets"""
        # COL 1-2 (Left)
        self.speed_wheel_label = tk.Label(self.tab1, text=self.SpeedWheelStr_kmh, font=(self.fontName, 120),
                                          relief='solid', anchor="w", width=5)
        self.speed_wheel_label.grid(column=0, columnspan=2, row=0, sticky="w", padx=0, pady=2)
        tk.Label(self.tab1, text="Speed [km/h]", font=(self.fontName, 8)).grid(column=0, columnspan=2, row=0,
                                                                               sticky="s", padx=0, pady=2)
        self.negative_bar = ttk.Progressbar(self.tab1, orient='horizontal', length=230, mode='determinate',
                                            maximum=100).grid(column=0, columnspan=1, row=1, sticky="e", padx=0, pady=5)
        self.positive_bar = ttk.Progressbar(self.tab1, orient='horizontal', length=230, mode='determinate',
                                            maximum=100).grid(column=1, columnspan=1, row=1, sticky="w", padx=0, pady=5)
        self.pace_diff_label = tk.Label(self.tab1, text=self.PaceStr_s, font=(self.fontName, 100), relief='solid',
                                        width=6)
        self.pace_diff_label.grid(column=0, columnspan=2, row=2, sticky="w", padx=0, pady=2)
        tk.Label(self.tab1, text="Pace [s]; Green GAS GAS GAS  //  Red = BRAKE", font=(self.fontName, 8)).grid(column=0,
                                                                                                               columnspan=2,
                                                                                                               row=2,
                                                                                                               sticky="s",
                                                                                                               padx=0,
                                                                                                               pady=2)

        self.rawSerialData_label = tk.Label(self.tab1, text=self.rawSerialData, font=(self.fontName, 11))
        self.rawSerialData_label.grid(column=0, columnspan=2, row=3, sticky="ws", padx=2, pady=10)

        ttk.Separator(self.tab1, orient='vertical').grid(column=2, row=0, rowspan=4, sticky="ns", padx=2, pady=2)

        # Adding ScrollableList to column 3, starting from row 2
        self.scrollable_list = self.ScrollableList(self.tab1,
                                                   self)  # Pass self (RallyApp instance) and self.sections here
        self.scrollable_list.grid(column=3, row=2, rowspan=2, columnspan=4, sticky="nsew", padx=5, pady=5)

        # COL 3
        self.currentSpeedTarget_label = tk.Label(self.tab1, text=self.SpeedTargetStr_kmh, font=(self.fontName, 50),
                                                 highlightthickness=10, highlightbackground="red")
        self.currentSpeedTarget_label.grid(column=3, columnspan=1, row=0, sticky="n", padx=2, pady=2)

        self.nextSpeedTarget_label = tk.Label(self.tab1, text=self.SpeedNextTargetStr_kmh, font=(self.fontName, 25),
                                              relief='solid')
        self.nextSpeedTarget_label.grid(column=3, columnspan=1, row=0, sticky="s", padx=2, pady=2)

        # COL 4
        self.travelledDistance_label = tk.Label(self.tab1, text=self.totalTraveledDistanceStr_m,
                                                font=(self.fontName, 18), relief='solid')
        self.travelledDistance_label.grid(column=4, columnspan=1, row=0, sticky="n", padx=2, pady=2)

        self.nextSegmentDistance_label = tk.Label(self.tab1, text=self.nextSegmentDistanceStr_m,
                                                  font=(self.fontName, 18), relief='solid')
        self.nextSegmentDistance_label.grid(column=4, columnspan=1, row=0, sticky="s", padx=2, pady=2)

        # COL 5
        self.timeSinceStart_label = tk.Label(self.tab1, text=self.timeSinceStartStr_s, font=(self.fontName, 18),
                                             relief='solid')
        self.timeSinceStart_label.grid(column=5, columnspan=1, row=0, sticky="n", padx=2, pady=2)

        self.currentSectionAndTrackConditions_label = tk.Label(self.tab1, text="???", font=(self.fontName, 18),
                                                               relief='solid')
        self.currentSectionAndTrackConditions_label.grid(column=5, columnspan=1, row=0, sticky="s", padx=2, pady=2)

        # Configure grid weights to prevent resizing
        self.tab1.grid_columnconfigure(0, weight=0)  # Prevent resizing
        self.tab1.grid_columnconfigure(1, weight=0)
        self.tab1.grid_columnconfigure(2, weight=0)
        self.tab1.grid_columnconfigure(3, weight=0)
        self.tab1.grid_rowconfigure(0, weight=0)
        self.tab1.grid_rowconfigure(1, weight=0)
        self.tab1.grid_rowconfigure(2, weight=0)
        self.tab1.grid_rowconfigure(3, weight=0)
        self.tab1.grid_rowconfigure(4, weight=0)

    class ScrollableList(tk.Frame):
        def __init__(self, parent, rally_app):
            super().__init__(parent)

            self.rally_app = rally_app  # Store a reference to the RallyApp instance

            # Header Frame (Fixed)
            self.header_frame = tk.Frame(self)
            self.header_frame.pack(side="top", fill="x")
            # print(parent)

            # Create headers
            headers = ["Start km", "End km", "Avg km/h", "Select TC"]
            for header in headers:
                label = tk.Label(self.header_frame, text=header, font=(self.rally_app.fontName, 12), width=12,
                                 anchor="center")
                label.pack(side="left", padx=0)

            # Canvas and Scrollbar
            self.canvas = tk.Canvas(self, borderwidth=0, height=10)
            self.frame = tk.Frame(self.canvas)
            self.vsb = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview, width=32)
            self.canvas.configure(yscrollcommand=self.vsb.set)

            # Pack the Scrollbar and Canvas
            self.vsb.pack(side="right", fill="both")
            self.canvas.pack(side="left", fill="both", expand=True)
            self.canvas.create_window((0, 0), window=self.frame, anchor="center")

            self.frame.bind("<Configure>", self.on_frame_configure)

            # Dictionary to store rows by their start_km
            self.rows = {}

            # Populate the table
            self.populate_table()

        def populate_table(self):

            self.rows = {}

            for widget in self.frame.winfo_children():
                widget.destroy()  # Clear existing content

            """Populate the frame with the starting line row and segment rows."""
            # First Row: Starting Line / No Race Mode
            self.add_row("Start", "Line", "--.--", [10, 0.0], "gray63")

            # Segment data
            # segment_data = [(0.0, 1.676, 30.0), (1.676, 2.1, 20.0), (2.1, 3.329, 45.0), (3.329, 8.206, 29.99)]
            segment_data = self.rally_app.selectedSection
            # print(segment_data)

            for segment in segment_data:
                start_km, end_km, avg_speed_dry, avg_speed_wet = segment
                background_color = ""
                id_message = 12
                if start_km <= 0.0:
                    id_message = 11
                if self.rally_app.trackIsWet:
                    self.add_row(f"{start_km:.3f}", f"{end_km:.3f}", f"{avg_speed_wet:.2f}",
                                 [id_message, start_km * 1000.0], background_color)
                else:
                    self.add_row(f"{start_km:.3f}", f"{end_km:.3f}", f"{avg_speed_dry:.2f}",
                                 [id_message, start_km * 1000.0], background_color)

            self.update_row_colors(0)

        def add_row(self, start_km, end_km, avg_speed, button_value, background_color):
            """Add a row with the given data and button action."""
            row = tk.Frame(self.frame, bg=background_color)

            label1 = tk.Label(row, text=start_km, font=(self.rally_app.fontName, 14), width=11, anchor='w')
            label2 = tk.Label(row, text=end_km, font=(self.rally_app.fontName, 14), width=11, anchor='w')
            label3 = tk.Label(row, text=avg_speed, font=(self.rally_app.fontName, 14), width=10, anchor='w')
            button = tk.Button(row, width=5, text="CAL", command=lambda val=button_value: self.set_total_distance(val),
                               bg="pale green")

            label1.pack(side="left", padx=2)
            label2.pack(side="left", padx=2)
            label3.pack(side="left", padx=2)
            button.pack(side="left", padx=2, fill="both")

            row.pack(side="top", fill="x", pady=5)

            # Store row reference in self.rows
            self.rows[start_km] = row

        def set_total_distance(self, value):
            """Set the totalTraveledDistance_m to the button's associated value."""
            # Put the data in the data_queue_out and event trigger and send it to backend
            self.rally_app.data_queue_out.put(value)
            self.rally_app.trigger_event_out.set()

            # print(self.rally_app.totalTraveledDistance_m)
            self.rally_app.totalTraveledDistance_m = value[1]  # Set distance in m

            print(f"Set total traveled distance to: {self.rally_app.totalTraveledDistance_m}")

        def update_row_colors(self, segment_index):
            """Update the color of each row based on the totalTraveledDistance_m."""
            try:
                i = 0
                # print(self.rows.items())
                for start_km, row in self.rows.items():
                    if row.winfo_exists():  # Check if the widget exists
                        if i == (segment_index + 1):
                            row.config(bg="blue")  # Change to desired color
                        else:
                            row.config(bg="light gray")  # Default color or another color as needed
                    i += 1
            except:
                print(f"Row does not exist.")

        def on_frame_configure(self, event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def populate_tab2(self):
        """Populate the "Roadbook" tab with widgets
           * Description: Main tab used during rally with key info
           * Input arg:
               RB_xx_label: Labels for data
           * Output arg:
               None: None
           * Inout:
               RR_speed_kmh: Speed data received from Rabbit message
        """
        # COL 1-2 (Left)
        # Wheel Speed info
        self.RB_speed_wheel_label = tk.Label(self.tab2, text=self.SpeedWheelStr_kmh, font=(self.fontName, 120),
                                             relief='solid', anchor="w", width=5)
        self.RB_speed_wheel_label.grid(column=0, columnspan=2, row=0, sticky="n", padx=40, pady=20)

        # Info label for wheel speed
        tk.Label(self.tab2, text="Speed [km/h]", font=(self.fontName, 10)).grid(column=0, columnspan=2, row=0,
                                                                                sticky="s", padx=40, pady=0)

        # Separators
        # self.RB_negative_bar = ttk.Progressbar(self.tab2, orient='horizontal', length=230, mode='determinate', maximum=100).grid(column=0, columnspan=1, row=1, sticky="e", padx=0, pady=0)
        # self.RB_positive_bar = ttk.Progressbar(self.tab2, orient='horizontal', length=230, mode='determinate', maximum=100).grid(column=1, columnspan=1, row=1, sticky="w", padx=0, pady=0)

        # Pace data label
        self.RB_pace_diff_label = tk.Label(self.tab2, text=self.RR_pace_s, font=(self.fontName, 100), relief='solid',
                                           width=6)
        self.RB_pace_diff_label.grid(column=0, columnspan=2, row=1, sticky="n", padx=40, pady=0)

        # Pace message text label
        self.Pace_text_label = tk.Label(self.tab2, text=self.Pace_text, font=(self.fontName, 20))
        self.Pace_text_label.grid(column=0, columnspan=2, row=1, sticky="n", padx=0, pady=0)

        # Info label for pace
        tk.Label(self.tab2, text="Pace [s]; Green = GAS; Red = BRAKE", font=(self.fontName, 10)).grid(column=0,
                                                                                                      columnspan=2,
                                                                                                      row=1, sticky="s",
                                                                                                      padx=40, pady=2)

        # Raw data from serial label
        self.RB_rawSerialData_label = tk.Label(self.tab2, text=self.rawSerialData, font=(self.fontName, 11),
                                               highlightthickness=2, highlightbackground="turquoise")
        self.RB_rawSerialData_label.grid(column=0, columnspan=2, row=2, sticky="ws", padx=40, pady=10)

        # Separator
        ttk.Separator(self.tab2, orient='vertical').grid(column=2, row=0, rowspan=5, sticky="ns", padx=0, pady=0)

        # COL 3
        # Current target speed label (Position C3-R0)
        self.RB_currentSpeedTarget_label = tk.Label(self.tab2, text=self.RR_current_target_speed,
                                                    font=(self.fontName, 48), highlightthickness=5,
                                                    highlightbackground="red")
        self.RB_currentSpeedTarget_label.grid(column=3, columnspan=1, row=0, sticky="n", padx=2, pady=50)

        # Info label for current target speed
        tk.Label(self.tab2, text="CURRENT TARGET SPEED", font=(self.fontName, 15, "bold")).grid(column=3, columnspan=1,
                                                                                                row=0, sticky="n",
                                                                                                padx=0, pady=20)

        # Current odometer in km label (Position C3-R1)
        self.RB_travelledDistance_label = tk.Label(self.tab2, text=self.RR_odo_km_1, font=(self.fontName, 60),
                                                   highlightthickness=5, highlightbackground="green")
        self.RB_travelledDistance_label.grid(column=3, columnspan=1, row=1, sticky="n", padx=2, pady=35)

        # Info label current odometer
        tk.Label(self.tab2, text="CURRENT ODOMETER", font=(self.fontName, 15, "bold")).grid(column=3, columnspan=1,
                                                                                            row=1, sticky="n", padx=0,
                                                                                            pady=0)

        # Next target speed label (Position C3-R2)
        self.RB_nextSpeedTarget_label = tk.Label(self.tab2, text=self.RR_next_target_speed, font=(self.fontName, 40),
                                                 highlightthickness=5, highlightbackground="blue")
        self.RB_nextSpeedTarget_label.grid(column=3, columnspan=1, row=2, sticky="s", padx=2, pady=0)

        # Info label for next target speed
        tk.Label(self.tab2, text="NEXT TARGET SPEED", font=(self.fontName, 15, "bold")).grid(column=3, columnspan=1,
                                                                                             row=2, sticky="n", padx=0,
                                                                                             pady=0)

        # COL 4
        # Current time since start of section
        self.RB_timeSinceStart_label = tk.Label(self.tab2, text=self.RR_section_time, font=(self.fontName, 18),
                                                highlightthickness=5, highlightbackground="white")
        self.RB_timeSinceStart_label.grid(column=4, columnspan=1, row=0, sticky="s", padx=2, pady=75)

        # Info label current section time
        tk.Label(self.tab2, text="SECTION TIME", font=(self.fontName, 15, "bold")).grid(column=4, columnspan=1, row=0,
                                                                                        sticky="n", padx=0, pady=120)

        # Regressive distance to next step
        self.RB_nextSegmentDistance_label = tk.Label(self.tab2, text=self.RR_regressive_next_ref_km,
                                                     font=(self.fontName, 18), highlightthickness=5,
                                                     highlightbackground="purple")
        self.RB_nextSegmentDistance_label.grid(column=4, columnspan=1, row=1, sticky="n", padx=2, pady=35)

        # Info label regressive distance to next step
        tk.Label(self.tab2, text="KM NEXT STEP", font=(self.fontName, 15, "bold")).grid(column=4, columnspan=1, row=1,
                                                                                        sticky="n", padx=0, pady=0)

        # Regressive distance to next section
        self.RB_regressive_section_label = tk.Label(self.tab2, text=self.RR_regressive_section_km,
                                                    font=(self.fontName, 18), highlightthickness=5,
                                                    highlightbackground="purple")
        self.RB_regressive_section_label.grid(column=4, columnspan=1, row=1, sticky="s", padx=2, pady=0)

        # Info label regressive distance to next section
        tk.Label(self.tab2, text="KM NEXT SPEED", font=(self.fontName, 15, "bold")).grid(column=4, columnspan=1, row=1,
                                                                                         sticky="s", padx=0, pady=50)

        # COL 5
        # Global time
        self.RB_timeCurrent_label = tk.Label(self.tab2, text=self.RR_global_time, font=(self.fontName, 18),
                                             highlightthickness=5, highlightbackground="white")
        self.RB_timeCurrent_label.grid(column=4, columnspan=1, row=0, sticky="n", padx=2, pady=50)

        # Info label global time
        tk.Label(self.tab2, text="GLOBAL TIME", font=(self.fontName, 15, "bold")).grid(column=4, columnspan=1, row=0,
                                                                                       sticky="n", padx=0, pady=20)

        # TC number info
        self.RB_number_ref_label = tk.Label(self.tab2, text=self.RR_number_ref, font=(self.fontName, 18),
                                            highlightthickness=5, highlightbackground="black")
        self.RB_number_ref_label.grid(column=5, columnspan=1, row=0, sticky="n", padx=2, pady=50)

        # Info label TC
        tk.Label(self.tab2, text="TC#", font=(self.fontName, 15, "bold")).grid(column=5, columnspan=1, row=0,
                                                                               sticky="n", padx=0, pady=20)

        # Configure grid weights to prevent resizing
        self.tab2.grid_columnconfigure(0, weight=0)  # Prevent resizing
        self.tab2.grid_columnconfigure(1, weight=0)
        self.tab2.grid_columnconfigure(2, weight=0)
        self.tab2.grid_columnconfigure(3, weight=0)
        self.tab2.grid_rowconfigure(0, weight=0)
        self.tab2.grid_rowconfigure(1, weight=0)
        self.tab2.grid_rowconfigure(2, weight=0)
        self.tab2.grid_rowconfigure(3, weight=0)
        self.tab2.grid_rowconfigure(4, weight=0)

    def populate_tab3(self):
        """Populate the 'Calibration' tab with widgets
        * Description: This tab is intended to be used for calibration purposes
        * Input arg:
            None: None
        * Output arg:
            None: None
        """
        # Label text for explanation 1
        tk.Label(self.tab3, text="Step 1: Calibration initialization. Set ODO to 0m", font=(self.fontName, 20)).grid(
            column=0, row=0, padx=5, pady=5, sticky="w")

        # Button for resetting current odometer value
        tk.Button(self.tab3, text="Reset ODO", font=(self.fontName, 20),
                  command=lambda val=[98, 0.0]: self.scrollable_list.set_total_distance(val)).grid(column=0, row=1,
                                                                                                   padx=100, pady=5,
                                                                                                   sticky="w")

        # Label text for explanation 2
        tk.Label(self.tab3, text="Step 2: Start driving until finish calibration line", font=(self.fontName, 20)).grid(
            column=0, row=2, padx=5, pady=5, sticky="w")

        # Counter for current travelled distance
        self.odo_label = tk.Label(self.tab3, text=self.totalTraveledDistanceStr_m, font=(self.fontName, 20),
                                  relief='solid')
        self.odo_label.grid(column=0, columnspan=1, row=1, padx=300, pady=2, sticky="w")

        # Label text for explanation 3
        tk.Label(self.tab3, text="Step 3: Stop in the calibration finish line",
                 font=(self.fontName, 20)).grid(column=0, row=4, padx=5, pady=5, sticky="w")

        # Label text for explanation 4
        tk.Label(self.tab3, text="Step 4: Enter the IDEAL distance in METERS and press CAL",
                 font=(self.fontName, 20)).grid(column=0, row=5, padx=5, pady=5, sticky="w")

        # Input text box for distance
        self.CALEntry = tk.Entry(self.tab3, font=(self.fontName, 20))
        self.CALEntry.grid(column=0, row=6, padx=50, pady=20, sticky="w")

        # Button to start calculation of calibration parameter
        self.CALButton = tk.Button(self.tab3, text="Calculate", font=(self.fontName, 20),
                                   command=self.process_CAL_input)
        self.CALButton.grid(column=0, row=6, padx=0, pady=0, sticky="e")

        # Label text for explanation
        tk.Label(self.tab3, text="Remember to hardcode the value in code to avoid losing it",
                 font=(self.fontName, 20)).grid(column=0, row=9, padx=5, pady=5, sticky="w")

    def populate_tab4(self):
        """Populate the 'TC Table' tab with widgets
        * Description: This tab is intended to be used for calibration purposes
        * Input arg:
            None: None
        * Output arg:
            None: None
        """
        # Elements initialization for buttons
        self.radio_var1 = tk.StringVar()
        self.radio_var2 = tk.IntVar()

        # Left column radiobuttons for sections
        for i, key in enumerate(self.sections.keys()):
            tk.Radiobutton(self.tab4, text=key, variable=self.radio_var1, value=key,
                           command=self.on_section_change).grid(column=0, row=i, sticky="w", padx=10, pady=5)

        # Right column radiobuttons for surface type
        tk.Radiobutton(self.tab4, text="Dry", variable=self.radio_var2, value=False,
                       command=self.on_surface_type_change).grid(column=1, row=0, sticky="w", padx=10, pady=5)
        tk.Radiobutton(self.tab4, text="Wet", variable=self.radio_var2, value=True,
                       command=self.on_surface_type_change).grid(column=1, row=1, sticky="w", padx=10, pady=5)

    def populate_tab5(self):
        """Populate the 'Mode & Sensors' tab with widgets
        * Description: This tab is intended to be used for calibration purposes
        * Input arg:
            None: None
        * Output arg:
            None: None
        """
        # Initialize variable for sensors
        self.radio_var3 = tk.IntVar(value=self.config_tr.sensors)  # value=1 means "s1" is default

        # Column radiobuttons for sensors selection
        tk.Radiobutton(self.tab5, text="Sensor1 + Sensor2", variable=self.radio_var3, value=0,
                       command=self.on_sensors_change).grid(column=0, row=0, sticky="w", padx=100, pady=5)
        tk.Radiobutton(self.tab5, text="Sensor1", variable=self.radio_var3, value=1,
                       command=self.on_sensors_change).grid(column=0, row=1, sticky="w", padx=100, pady=5)
        tk.Radiobutton(self.tab5, text="Sensor2", variable=self.radio_var3, value=2,
                       command=self.on_sensors_change).grid(column=0, row=2, sticky="w", padx=100, pady=5)

    def process_CAL_input(self):
        try:
            # Get the number from the entry field
            user_input = self.CALEntry.get()

            # Put the data in the data_queue_out and event trigger and send it to backend
            self.data_queue_out.put([99, float(user_input)])
            self.trigger_event_out.set()

            # Perform some operation with the number (for example, square it)
            # result = number ** 2

            # Show the result in a message box
            # messagebox.showinfo("Result", f"The square of {number} is {result}")

        except ValueError:
            # If the input is not a valid number, show an error
            print("CAL Error - input is not a valid number")

    def on_sensors_change(self):
        """Callback function for sensors radio button changes
        * Description: Process the info selected by the user about the sensors
        * Input arg:
            None: None
        * Output arg:
            None: None
        """
        # Get the value from frontend
        sensors = self.radio_var3.get()

        # Print info message
        print(f"Selected sensors?: {sensors}")

        # Put the data in the data_queue_out and event trigger to send to backend
        self.data_queue_out.put([20, sensors])
        self.trigger_event_out.set()

    def on_surface_type_change(self):
        """Callback function for surface type selection
        * Description: Process the info selected by the user about the surface type
        * Input arg:
            None: None
        * Output arg:
            None: None
        """
        # Get the value from frontend
        self.trackIsWet = self.radio_var2.get()

        # Print info message
        print(f"Is track wet?: {self.trackIsWet}")

        # Put the data in the data_queue_out and event trigger and send it to backend
        self.data_queue_out.put([1, self.trackIsWet])
        self.trigger_event_out.set()

        # Execute function to import the TC data
        self.importSectionData()

        # Populate the table in the scrollable list
        self.scrollable_list.populate_table()

        # Depending on user selection TC average speed changes
        if self.trackIsWet:
            self.currentSectionAndTrackConditions_label.config(text="  " + self.selectedSectionKey + "  \n" + "Wet")
        else:
            self.currentSectionAndTrackConditions_label.config(text="  " + self.selectedSectionKey + "  \n" + "Dry")

    def on_section_change(self):
        """Callback function for section selection
        * Description: Process the info selected by the user about the TC to be used
        * Input arg:
            None: None
        * Output arg:
            None: None
        """
        # Get the value from frontend
        self.selectedSectionKey = self.radio_var1.get()

        # Add TC value selected into the sections table
        self.selectedSection = self.sections[self.selectedSectionKey]

        # Print info message
        print(f"Selected section: {self.selectedSectionKey}")

        # Put the data in the data_queue_out and event trigger and send it to backend
        self.data_queue_out.put([0, self.selectedSectionKey])
        self.trigger_event_out.set()

        # Execute function to import the TC data
        self.importSectionData()

        # Populate the table in the scrollable list
        self.scrollable_list.populate_table()

        # Depending on user selection TC average speed changes
        if self.trackIsWet:
            self.currentSectionAndTrackConditions_label.config(text="  " + self.selectedSectionKey + "  \n" + "Wet")
        else:
            self.currentSectionAndTrackConditions_label.config(text="  " + self.selectedSectionKey + "  \n" + "Dry")

    def updatePaceColor(self):
        """Pace Color function
        * Description: Changes the background color of the pace widget depending on time
        * Input arg:
            None: None
        * Output arg:
            None: None
        """
        # Pace value is between 0.5 and -0.5
        if self.paceDiff_s <= 0.5 and self.paceDiff_s >= -0.5:
            bg_color = "gray10"
        else:
            if self.paceDiff_s < 0:
                if self.paceDiff_s > -2:
                    bg_color = "coral"
                else:
                    bg_color = "red"
            else:
                if self.paceDiff_s < 2:
                    bg_color = "yellow green"
                else:
                    bg_color = "green"
        self.pace_diff_label.config(bg=bg_color)

    def RB_updatePaceColor(self):
        """Pace Color function for received Rabbit data
        * Description: Changes the background color of the pace widget depending on Rabbit data
        * Input arg:
            None: None
        * Output arg:
            None: None
        """
        try:
            # Read pace data from Rabbit decoded message
            pace = float(self.RR_pace_s)
            if pace <= 0.20 and pace >= -0.20:  # Between 0.5/-0.5 seconds
                bg_color = "gray10"
                self.Pace_text = "NICE"
            else:
                if pace < 0:
                    if pace > -2:
                        bg_color = "coral"  # More than -2 seconds
                        self.Pace_text = "BRAKE!"
                    else:
                        bg_color = "red"  # Between 0 and -2 seconds
                        self.Pace_text = "BRAKE BRAKE BRAKE!!!"
                else:
                    if pace < 2:
                        bg_color = "yellow green"  # Less than +2 seconds
                        self.Pace_text = "GAS!"
                    else:
                        bg_color = "green"  # More than +2 seconds
                        self.Pace_text = "GAS GAS GAS!!!"
            self.RB_pace_diff_label.config(bg=bg_color)  # Set color label
            self.Pace_text_label.config(bg=bg_color)  # Set color label
            self.Pace_text_label.config(text=self.Pace_text)
        except:
            self.RB_pace_diff_label.config(bg="gray10")  # Exception color
            self.Pace_text_label.config(bg="gray10")  # Exception color
            self.Pace_text_label.config(text="Error")  # Exception text

    def RR_calc_speed(self):
        """Calculation of speed based on received Rabbit data
        * Description: Calculates current speed based on Rabbit  data
        * Input arg:
            RR_odo_km_1: Current odometer value received from Rabbit data
            RR_odo_km_1_previous: Previous odometer value stored
        * Output arg:
            None: None
        * Inout:
            RR_speed_kmh: Speed data received from Rabbit message
        """
        try:
            if self.RR_odo_km_1 != self.RR_odo_km_1_previous:  # If current odometer is different from previous value
                distance = abs(float(self.RR_odo_km_1) - float(self.RR_odo_km_1_previous))  # Distance is the difference
                self.RR_speed_kmh = str(distance / (0.25 / 3600))  # Speed is distance transformed in km/h
        except:
            self.RR_speed_kmh = '00.0'

    def update_loop(self):
        """Update the speed wheel value and schedule the next update"""
        if self.trigger_event_in.is_set():
            if not self.data_queue_in.empty():
                self.SpeedWheel_kmh, self.totalTraveledDistance_m, self.paceDiff_s, self.timeSinceStart_s, self.rawSerialData, self.serialInvalidData = self.data_queue_in.get()

                self.SpeedWheelStr_kmh = f"{self.SpeedWheel_kmh:5.1f}"
                self.speed_wheel_label.config(text=self.SpeedWheelStr_kmh)
                self.RB_speed_wheel_label.config(text=self.SpeedWheelStr_kmh)
                # self.speed_wheel_labelVelo.config(text=self.SpeedWheelStr_kmh)

                self.PaceStr_s = f"{self.paceDiff_s:5.1f}"
                self.pace_diff_label.config(text=self.PaceStr_s)
                self.updatePaceColor()

                self.totalTraveledDistanceStr_m = f"  Odo[m]  \n{self.totalTraveledDistance_m:06.0f}m"
                self.travelledDistance_label.config(text=self.totalTraveledDistanceStr_m)
                self.odo_label.config(text=self.totalTraveledDistanceStr_m)

                if self.serialInvalidData:
                    self.rawSerialData_label.config(text="Serial: " + self.rawSerialData + " | INVALID DATA!:")
                    self.RB_rawSerialData_label.config(text="Serial: " + self.rawSerialData + " | INVALID DATA!:")
                else:
                    self.rawSerialData_label.config(text="Serial: " + self.rawSerialData + " | DATA OK")
                    self.RB_rawSerialData_label.config(text="Serial: " + self.rawSerialData + " | DATA OK")
            self.trigger_event_in.clear()

        if self.trigger_event_RxFromRRtofront.is_set():
            if not self.data_queue_RxFromRRtofront.empty():
                self.RR_message_list = self.data_queue_RxFromRRtofront.get()
                self.RR_extract_data()
                # print(self.RR_message_list)
                self.RB_pace_diff_label.config(text=self.RR_pace_s)
                self.RB_updatePaceColor()
                # self.RB_travelledDistance_label.config(text = "  Current odo  \n" + self.RR_odo_km_1, font=(self.fontName, 15)) # Print text and data
                self.RB_travelledDistance_label.config(text=self.RR_odo_km_1,
                                                       font=(self.fontName, 15))  # Print data only
                # self.RR_calc_speed() #Not precise enough
                # self.RB_speed_wheel_label.config(text=self.RR_speed_kmh)
                self.RR_odo_km_1_previous = self.RR_odo_km_1
            self.trigger_event_RxFromRRtofront.clear()

        # Schedule the next update after 50 milliseconds
        self.root.after(50, self.update_loop)

    def update_loop_1s(self):
        # self.timeSinceStartStr_s = f"{self.timeSinceStart_s:5.0f}s"
        self.timeSinceStartStr_s = " TC Time \n" + str(datetime.timedelta(seconds=round(self.timeSinceStart_s)))
        self.timeSinceStart_label.config(text=self.timeSinceStartStr_s)

        # Refresh TargetSpeed and NextTargetSpeed
        segment_indices = np.where(self.totalTraveledDistance_m <= self.selectedSectionEndtDist_m)[0]
        if len(segment_indices) == 0:
            segment_index = -1
            self.SpeedTargetStr_kmh = "End TC"
            self.SpeedNextTargetStr_kmh = "End TC"
        else:
            segment_index = segment_indices[0]
            if len(segment_indices) == 1:
                self.SpeedTargetStr_kmh = f"{self.selectedSectionSpeed_kmh[segment_index]:05.2f}"
                self.SpeedNextTargetStr_kmh = "End TC"
            else:
                self.SpeedTargetStr_kmh = f"{self.selectedSectionSpeed_kmh[segment_index]:05.2f}"
                self.SpeedNextTargetStr_kmh = f"{self.selectedSectionSpeed_kmh[segment_index + 1]:05.2f}"
        self.currentSpeedTarget_label.config(text=self.SpeedTargetStr_kmh)
        self.nextSpeedTarget_label.config(text="   Next   \n" + self.SpeedNextTargetStr_kmh)
        # self.currentSpeedTargetVelo_label.config(text=self.SpeedTargetStr_kmh)
        # self.nextSpeedTargetVelo_label.config(text="   Next   \n"+self.SpeedNextTargetStr_kmh)

        # Refresh nextSegmentDistanceStr_m
        if segment_index >= 0:
            distanceToNextSegment_m = self.totalTraveledDistance_m - self.selectedSectionEndtDist_m[segment_index]
        else:
            distanceToNextSegment_m = 0
        self.nextSegmentDistanceStr_m = f" Next Seg \n{distanceToNextSegment_m:5.0f}m"
        self.nextSegmentDistance_label.config(text=self.nextSegmentDistanceStr_m)

        if distanceToNextSegment_m > -200 and distanceToNextSegment_m < 0:
            self.nextSpeedTarget_label.config(bg="yellow", fg="black")
        else:
            self.nextSpeedTarget_label.config(bg="gray10", fg="snow")

        # Refresh scrollable table
        # self.scrollable_list.populate_table()
        self.scrollable_list.update_row_colors(segment_index)  # Call to update row colors

        # RoadBook Refresh Data
        self.RB_timeSinceStart_label.config(text=self.RR_section_time)
        self.RB_timeCurrent_label.config(text=self.RR_global_time)
        self.RB_currentSpeedTarget_label.config(text=self.RR_current_target_speed)
        # self.RB_nextSpeedTarget_label.config(text="   Next   \n"+self.RR_next_target_speed) # Print text and data
        self.RB_nextSpeedTarget_label.config(text=self.RR_next_target_speed)  # Print data only
        self.RB_nextSegmentDistance_label.config(text=self.RR_regressive_next_ref_km)
        self.RB_regressive_section_label.config(text=self.RR_regressive_section_km)
        self.RB_number_ref_label.config(text=self.RR_number_ref)
        try:
            reg_ref_km = float(self.RR_regressive_next_ref_km)
            if reg_ref_km < 0.2:
                self.RB_nextSegmentDistance_label.config(bg='maroon1', fg="black")
            else:
                self.RB_nextSegmentDistance_label.config(bg='gray10', fg="snow")
        except:
            self.RB_nextSegmentDistance_label.config(bg='gray10', fg="snow")
        if self.RR_current_target_speed != self.RR_current_target_speed_previous:
            self.RR_current_target_speed_timer += 1
            self.RB_currentSpeedTarget_label.config(bg='yellow', fg="black")
            self.RB_speed_wheel_label.config(bg='yellow', fg="black")
            if self.RR_current_target_speed_timer >= 5:
                self.RR_current_target_speed_previous = self.RR_current_target_speed
                self.RR_current_target_speed_timer = 0
        else:
            self.RB_currentSpeedTarget_label.config(bg='gray10', fg="snow")
            self.RB_speed_wheel_label.config(bg='gray10', fg="snow")

        # Schedule the next update after 1 second
        self.root.after(1000, self.update_loop_1s)

    def importSectionData(self):
        """Data of TC section import function
        * Description: Change import data from csv TC section
        * Input arg:
            None: None
        * Output arg:
            None: None
        """
        # Parses content of TC csv file
        segments_array = np.array(self.selectedSection)
        # Takes all elements from column "Start" + multiply to convert in meters
        self.selectedSectionStartDist_m = segments_array[:, 0] * 1000

        # Takes all elements from column "End" + multiply to convert in meters
        self.selectedSectionEndtDist_m = segments_array[:, 1] * 1000

        # Takes all elements from column "AvgDry" or "AvgWet" depending on selection
        if self.trackIsWet:
            self.selectedSectionSpeed_kmh = segments_array[:, 3]
        else:
            self.selectedSectionSpeed_kmh = segments_array[:, 2]

    ##################################### Section for numpad functions #####################################################

    def on_numpad_divide(self, event):
        """Function for numpad "/"/Divide key press
        * Description: Function triggered by event of divide key in numpad that recalculates CALIBRATION
        * Input arg:
            event: Each time divide key from numpad is pressed
        * Output arg:
            None: None
        """
        # If divide key is ENABLED
        if not self.divide_disabled:
            # Print message on event
            print("Button CAL pressed")
            segment_indices_end = np.where(self.totalTraveledDistance_m <= self.selectedSectionEndtDist_m)[0]
            segment_indices_start = np.where(self.totalTraveledDistance_m <= self.selectedSectionStartDist_m)[0]
            if self.totalTraveledDistance_m <= 0.0:
                self.scrollable_list.set_total_distance([11, 0.0])
            else:
                if len(segment_indices_end) > 0:
                    segment_index = segment_indices_end[0]
                    distanceToPrevious = self.totalTraveledDistance_m - self.selectedSectionStartDist_m[segment_index]
                    distanceToNext = self.selectedSectionEndtDist_m[segment_index] - self.totalTraveledDistance_m
                    if distanceToPrevious <= distanceToNext and segment_index != 0:
                        self.scrollable_list.set_total_distance([12, self.selectedSectionStartDist_m[segment_index]])
                    else:
                        self.scrollable_list.set_total_distance([12, self.selectedSectionEndtDist_m[segment_index]])
            self.divide_disabled = True  # Disable further triggers
            self.root.after(1000, self.reset_divide)  # Re-enable after 1 second

    def reset_divide(self):
        """Function for numpad "/"/Divide reset key press
        * Description: Function that re-enables the ability for numpad divide key press
        * Input arg:
            None: None
        * Output arg:
            None: None
        """
        self.divide_disabled = False  # Re-enable the enter key handler

    def on_numpad_multiply(self, event):
        """Function for numpad "*"/Multiply key press
        * Description: Function triggered by event of multiply key in numpad that sync odometer from RR into TR
        * Input arg:
            event: Each time multiply key from numpad is pressed
        * Output arg:
            None: None
        """
        # Print message on event
        print("Synchronise Odometer from RR")

        try:
            new_odo = float(self.RR_odo_km_1) * 1000  # Multiplies received odometer in km by 1000
            self.scrollable_list.set_total_distance([12, new_odo])  # Sets new odometer in the current total distance
        except:
            pass

        # Buttons logic
        self.multiply_disabled = True  # Disable further triggers
        self.root.after(1000, self.reset_multiply)  # Re-enable after 1 second using function

    def reset_multiply(self):
        """Function for numpad "*"/Multiply reset key press
        * Description: Function that re-enables the ability for numpad multiply key press
        * Input arg:
            None: None
        * Output arg:
            None: None
        """
        self.multiply_disabled = False

    def on_numpad_add(self, event):
        """Function for numpad "+"/Add key press
        * Description: Function triggered by event of add key in numpad that increases 1m to current odometer
        * Input arg:
            event: Each time add key from numpad is pressed
        * Output arg:
            None: None
        """
        # Print message on event
        print("ODO + 1!")

        # Put the data in the data_queue_out and event trigger and send it to backend
        self.data_queue_out.put([13, 1.0])  # Send increased odometer by 1.0 meter
        self.trigger_event_out.set()

        # Buttons logic
        self.add_disabled = True  # Disable further triggers
        self.root.after(500, self.reset_add)  # Re-enable after 0.5 second using function

    def reset_add(self):
        """Function for numpad "+"/Add reset key press
        * Description: Function that re-enables the ability for numpad add key press
        * Input arg:
            None: None
        * Output arg:
            None: None
        """
        self.add_disabled = False

    def on_numpad_subtract(self, event):
        """Function for numpad "-"/Subtract key press
        * Description: Function triggered by event of subtract key in numpad that decreases 1m to current odometer
        * Input arg:
            event: Each time subtract key from numpad is pressed
        * Output arg:
            None: None
        """
        # Print message on event
        print("ODO - 1!")

        # Put the data in the data_queue_out and event trigger and send it to backend
        self.data_queue_out.put([13, -1.0])  # Send decreased odometer by 1.0 meter
        self.trigger_event_out.set()

        # Buttons logic
        self.subtract_disabled = True  # Disable further triggers
        self.root.after(500, self.reset_subtract)  # Re-enable after 0.5 second using function

    def reset_subtract(self):
        """Function for numpad "-"/Subtract reset key press
        * Description: Function that re-enables the ability for numpad subtract key press
        * Input arg:
            None: None
        * Output arg:
            None: None
        """
        self.subtract_disabled = False

    #################################### End Section for numpad functions ##################################################

    ####################################### Section for RR functions #######################################################
    def RR_extract_data(self):
        """Data extractor from Rabbit messages
        * Description: Stores values in variables from received messages
        * Input arg:
            RR_message_list[x][y]: Data message
        * Output arg:
            RR_global_time: Official global time
            RR_section_time: Total time for the section
            RR_odo_km_1: Current odometer from Rabbit
            RR_odo_km_2:
            RR_regressive_section_km: Pending distance in km for the next section (speed change)
            RR_regressive_next_ref_km: Pending distance in km for the next step (roadbook jump)
            RR_pace_s: Current pace in seconds
            RR_current_target_speed: Target average speed to achieve
            RR_next_target_speed: Target average speed to achieve in the next speed change
            RR_number_ref: Current TC number
            RR_unknown_data: TBD
        * Inout:
            None: None
        """
        # """
        # Assigns self.RR_message_list data to variables
        self.RR_global_time = self.RR_message_list[0][0]
        self.RR_section_time = self.RR_message_list[0][1]
        self.RR_odo_km_1 = self.RR_message_list[1][0]
        self.RR_odo_km_2 = self.RR_message_list[1][1]
        self.RR_regressive_section_km = self.RR_message_list[2][0]
        self.RR_regressive_next_ref_km = self.RR_message_list[2][1]
        self.RR_pace_s = self.RR_message_list[5]

        self.RR_current_target_speed = self.RR_message_list[6][0]
        self.RR_next_target_speed = self.RR_message_list[6][1]
        self.RR_number_ref = self.RR_message_list[7]
        self.RR_unknown_data = self.RR_message_list[8]
        # """
        # Debug variables
        if DEBUG_FRONTEND_MODE:
            self.RR_global_time = '19:19:19'
            self.RR_section_time = '10:10'
            self.RR_odo_km_1 = 2.222
            self.RR_odo_km_2 = 3.333
            self.RR_regressive_section_km = 5.000
            self.RR_regressive_next_ref_km = 10.000
            self.RR_pace_s = 3.0
            self.RR_current_target_speed = 49.121
            self.RR_next_target_speed = 69.99
            self.RR_number_ref = 12
        else: None
##################################### End Section for RR functions #####################################################



