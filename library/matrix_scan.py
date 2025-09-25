from gpiozero import ButtonBoard, LEDBoard
from time import sleep
import threading
from gpiozero.threads import GPIOThread

class MatrixScan(GPIOThread):

    def __init__(self, scan_delay=0.02, use_led_hat=False):
        super().__init__(target=self._run_scan_matrix)
        self.daemon = True

        if use_led_hat:
            # LED-HAT pinout
            self.row1 = 'BOARD38'
            self.row2 = 'BOARD35'
            self.row3 = 'BOARD40'
            self.row4 = 'BOARD37'
            
            self.col1 = 'BOARD7'
            self.col2 = 'BOARD12'
            self.col3 = 'BOARD11'
            self.col4 = 'BOARD15'
        else:
        # Original pinout
            self.row1 = 'BOARD40'
            self.row2 = 'BOARD33'
            self.row3 = 'BOARD21'
            self.row4 = 'BOARD11'
            
            self.col1 = 'BOARD26'
            self.col2 = 'BOARD22'
            self.col3 = 'BOARD16'
            self.col4 = 'BOARD10'

        self.scan_delay = scan_delay
        self.enable_scan = False
        self.scan_count = 0

        self.button_map = {
            1: MatrixScanButton(row=0, col=0),
            2: MatrixScanButton(row=0, col=1),
            3: MatrixScanButton(row=0, col=2),
            4: MatrixScanButton(row=0, col=3),
            5: MatrixScanButton(row=1, col=0),
            6: MatrixScanButton(row=1, col=1),
            7: MatrixScanButton(row=1, col=2),
            8: MatrixScanButton(row=1, col=3),
            9: MatrixScanButton(row=2, col=0),
            10: MatrixScanButton(row=2, col=1),
            11: MatrixScanButton(row=2, col=2),
            12: MatrixScanButton(row=2, col=3),
            13: MatrixScanButton(row=3, col=0),
            14: MatrixScanButton(row=3, col=1),
            15: MatrixScanButton(row=3, col=2),
            16: MatrixScanButton(row=3, col=3)
            }

        self.button_pos_map = {
            1: (0, 0),
            2: (0, 1),
            3: (0, 2),
            4: (0, 3),
            5: (1, 0),
            6: (1, 1),
            7: (1, 2),
            8: (1, 3),
            9: (2, 0),
            10: (2, 1),
            11: (2, 2),
            12: (2, 3),
            13: (3, 0),
            14: (3, 1),
            15: (3, 2),
            16: (3, 3)
            }

        self.pos_button_map = dict((v,k) for k,v in self.button_pos_map.items())
        
        # Button inputs are rows
        self.row_inputs = ButtonBoard(self.row4, self.row3, self.row2, self.row1, pull_up=True)
        # Scan outputs are columns
        self.col_outputs = LEDBoard(self.col1, self.col2, self.col3, self.col4, active_high=False)

        self.disable_scan_columns()

    def lookup_button_number(self, row, col):
        return self.pos_button_map[(row, col)]

    def lookup_button_pos(self, button_num):
        return self.button_pos_map[button_num]

    def stop_scan_matrix(self):
        self.enable_scan = False
        sleep(0.1)
        self.disable_scan_columns()

    def start_scan_matrix(self):
        self.enable_scan = True
    
    def _run_scan_matrix(self):
        while not self.stopping.is_set():
            self.scan_matrix()
                       
    def scan_matrix(self):
        if self.enable_scan and not self.stopping.is_set(): 
            for key in self.button_map.keys():
                self.button_map[key].last_state = self.button_map[key].state
            for col_idx, col in enumerate(self.col_outputs):
                # Enable the scanning column
                col.on()
                # Read each row for the given column and store the state
                for row_idx, row in enumerate(self.row_inputs):
                    button_num = self.lookup_button_number(row_idx, col_idx)
                    # Read the button if its enabled
                    if self.button_map[button_num].en:
                        value = row.is_pressed
                        ticks = row.pin.factory.ticks()
                        self.button_map[button_num].state = value
                        # If the button state changed, log that time and evaluate if the edge needs to be announced
                        if self.button_map[button_num].last_state != value:
                            self.button_map[button_num].state_change_ticks = ticks
                            self.detect_edge(button_num, ticks)
                    # Ignore the buttons
                    else:
                        self.button_map[button_num].state = False
                # Disable the scanning column
                col.off()
                sleep(self.scan_delay)

    def disable_scan_columns(self):
        # Turn off all the columns
        self.col_outputs.off()

    def disable_button(self, button_num):
        self.button_map[button_num].en = False
        self.button_map[button_num].event = None
        self.button_map[button_num].state = False
        self.button_map[button_num].last_state = False
        self.button_map[button_num].det_edge = None
        self.unwatch_button(button_num)

    def enable_button(self, button_num):
        self.button_map[button_num].en = True
        
    def release_scan_matrix(self):
        self.stop_scan_matrix()
        for button_num in self.button_map.keys():
            self.disable_button(button_num)
        self.row_inputs.close()
        self.col_outputs.close()
        self.stop()

    def get_button_state(self, button_num):
        return self.button_map[button_num].state       

    def update_scan_delay(self, scan_delay):
        self.stop_scan_matrix()
        self.scan_delay = scan_delay
        self.start_scan_matrix()

    def set_button_edge_trig(self, button_num, edge):
        self.button_map[button_num].edge_trig = edge
        
    # Configure the button to detect a given edge
    def watch_button(self, button_num, edge):
        if self.button_map[button_num].event is None:
            # Start watching the button
            self.set_button_edge_trig(button_num, edge)
            self.button_map[button_num].event = threading.Event()

    def unwatch_button(self, button_num):
        self.button_map[button_num].event = None
        self.button_map[button_num].edge_trig = None

    def set_callback(self, button_num, callback):
        self.button_map[button_num].change_callback = callback

    def clear_callback(self, button_num):
        self.button_map[button_num].change_callback = None
        
    # Check if a watched edge occured
    def detect_edge(self, button_num, ticks):
        edge_found = self.identify_edge(self.button_map[button_num].state, self.button_map[button_num].last_state)
        self.button_map[button_num].det_edge = edge_found
        # If the edge is the desired edge, trigger the event and store the time
        if self.button_map[button_num].edge_trig == edge_found or self.button_map[button_num].edge_trig == 'both' and edge_found != None:
            self.button_map[button_num].edge_trig_ticks = ticks
            self.button_map[button_num].event.set()
            if self.button_map[button_num].change_callback is not None:
                self.button_map[button_num].change_callback(self.button_map[button_num].state)

    @staticmethod
    def identify_edge(curr_state, last_state):
        if curr_state == last_state:
            return None
        elif curr_state == True and last_state == False:
            return 'rising'
        elif curr_state == False and last_state == True:
            return 'falling'
        
class MatrixScanButton:

    # row: row of button on pad
    # col: column of button on pad
    # en: button is enabledd
    # state: current state of button
    # last_state: last state of button
    # state_change_ticks: Time of when the state last changed
    # det_edge: Detected edge, can be 'rising', 'falling', or None
    # edge_trig: Edge being watched for, can be 'rising', 'falling', 'both', or None
    # edge_trig_ticks: Time of when the detected edge change occured
    # event: Event object to monitor button, None if not being watched
    # change_callback: Reference to MatrixScanPin._call_when_changed function
    
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.en = True
        self.state = False
        self.last_state = False
        self.state_change_ticks = None
        self.det_edge = None
        self.edge_trig = None
        self.edge_trig_ticks = None
        self.event = None
        self.change_callback = None
    
    
