from gpiozero import RGBLED, LEDBoard
from colorzero import Color
from typing import List
from time import sleep, monotonic
from gpiozero.threads import GPIOThread
from enum import Enum
from dataclasses import dataclass
from math import floor

class ColorMap(Enum):
        red = 1
        green = 2
        blue = 3

class MatrixLED(GPIOThread):
    
    def __init__(self, pwm_freq = 0, display_pause=0.001, use_led_hat=False):
        super().__init__(target=self._run_led_matrix)
        self.swap_blue_green = True
        self.daemon = True

        self.led_count = 16

        if use_led_hat:
            # With LED Hat
            # NOTE: Green and Blue are swapped
            self.red1 = 'BOARD33'
            self.red2 = 'BOARD31'
            self.red3 = 'BOARD24'
            self.red4 = 'BOARD21'

            if self.swap_blue_green:

                self.green1 = 'BOARD32' 
                self.green2 = 'BOARD29' 
                self.green3 = 'BOARD22' 
                self.green4 = 'BOARD19'

                self.blue1 = 'BOARD36' 
                self.blue2 = 'BOARD26' 
                self.blue3 = 'BOARD23' 
                self.blue4 = 'BOARD18'

            else:
                self.blue1 = 'BOARD32' 
                self.blue2 = 'BOARD29' 
                self.blue3 = 'BOARD22' 
                self.blue4 = 'BOARD19'

                self.green1 = 'BOARD36' 
                self.green2 = 'BOARD26' 
                self.green3 = 'BOARD23' 
                self.green4 = 'BOARD18'
        
            self.led_col1 = 'BOARD10'
            self.led_col2 = 'BOARD8'
            self.led_col3 = 'BOARD16'
            self.led_col4 = 'BOARD13'
            color_logic = False
            anode_logic = True

        else:
            # Original pinout                        
            self.red1 = 'BOARD38'
            self.red2 = 'BOARD31'
            self.red3 = 'BOARD19'
            self.red4 = 'BOARD7'

            self.blue1 = 'BOARD35'
            self.blue2 = 'BOARD23'
            self.blue3 = 'BOARD13'
            self.blue4 = 'BOARD3'

            self.green1 = 'BOARD37'
            self.green2 = 'BOARD29'
            self.green3 = 'BOARD15'
            self.green4 = 'BOARD5'
        
            self.led_col1 = 'BOARD24'
            self.led_col2 = 'BOARD18'
            self.led_col3 = 'BOARD12'
            self.led_col4 = 'BOARD8'

            color_logic = True
            anode_logic = False

        if pwm_freq is None or pwm_freq == 0:
            self.pwm = False
        else:
            self.pwm = True
        self.red_leds = LEDBoard(self.red4, self.red3, self.red2, self.red1, active_high=color_logic, pwm=self.pwm)
        self.blue_leds = LEDBoard(self.blue4, self.blue3, self.blue2, self.blue1, active_high=color_logic, pwm=self.pwm)
        self.green_leds = LEDBoard(self.green4, self.green3, self.green2, self.green1, active_high=color_logic, pwm=self.pwm)
        self.led_cols = LEDBoard(self.led_col1, self.led_col2, self.led_col3, self.led_col4, active_high=anode_logic)
        
        self.enable_leds = False
        self.display_pause = display_pause

        self.led_map = {}
        for led_idx in range(self.led_count):
            led_num = led_idx + 1
            row = floor((led_num - 1)/4)
            col = (led_num - 1) % 4
            self.led_map[led_num] = MatrixRGB(row=row,
                                              col=col,
                                              led_num=led_num,
                                              red_led=self.red_leds[row],
                                              green_led=self.green_leds[row],
                                              blue_led=self.blue_leds[row])
            

        self.led_pos_map = {
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

        self.pos_led_map = dict((v,k) for k,v in self.led_pos_map.items())
        
        self.disable_led_columns()
        self.disable_leds()
        self.set_pwm_freq(pwm_freq)
        
    def disable_led_columns(self):
        self.led_cols.off()

    def disable_leds(self):
        for led in self.led_map.keys():
            self.led_map[led].red_led.off()
            self.led_map[led].green_led.off()
            self.led_map[led].blue_led.off()
            self.led_map[led].red_value = 0
            self.led_map[led].next_red_value = 0
            self.led_map[led].green_value = 0
            self.led_map[led].next_green_value = 0
            self.led_map[led].blue_value = 0
            self.led_map[led].next_blue_value = 0
        
    def lookup_led_number(self, row, col):
        return self.pos_led_map[(row,col)]

    def lookup_led_pos(self, led_number):
        return self.led_pos_map[led_number]

    def stop_led_matrix(self):
        self.enable_leds = False
        sleep(0.1)
        self.disable_led_columns()
        self.disable_leds()

    def start_led_matrix(self):
        self.enable_leds = True

    def _run_led_matrix(self):
        while self.enable_leds and not self.stopping.is_set():
            self.disp_led_matrix()            
            
    def _turn_off_row(self, row_idx):
        self.red_leds[row_idx].off()
        self.blue_leds[row_idx].off()
        self.green_leds[row_idx].off()
                     
    def disp_led_matrix(self):
        if self.enable_leds and not self.stopping.is_set():
            for col_idx, col in enumerate(self.led_cols):
                for row_idx, _ in enumerate(self.red_leds):
                    led_num = self.lookup_led_number(row_idx, col_idx)
                    # Update the LED colors
                    self.led_map[led_num].update_led()
                # Strobe the LED column
                col.on()
                sleep(self.display_pause)
                # Turn off the LEDs
                for row_idx, _ in enumerate(self.red_leds):
                    self._turn_off_row(row_idx)
                col.off()

    def disable_led(self, led_color, led_num):
        self.set_led_state(led_color, led_num, 0)
        
    def enable_led(self, led_color, led_num):
        self.set_led_state(led_color, led_num, 1)
        
    def release_led_matrix(self):
        self.stop_led_matrix()
        self.red_leds.close()
        self.blue_leds.close()
        self.green_leds.close()
        self.led_cols.close()
        self.stop()

    def get_led_state(self, led_color, led_num):
        return self.led_map[led_num].get_led_value(led_color)

    def set_led_state(self, led_color, led_num, state):
        self.led_map[led_num].set_led_value(led_color, state)
    
    def update_display_pause(self, display_pause):
        self.display_pause = display_pause

    def set_pwm_freq(self, value):
        if self.pwm:
            for led in self.red_leds:
                led.frequency = value
            for led in self.blue_leds:
                led.frequency = value
            for led in self.green_leds:
                led.frequency = value
            self.pwm_freq = value

    def get_pwm_freq(self):
        return self.pwm_freq    

class MatrixRGB:
    # row: row of LED on pad
    # col: column of LED on pad
    # led_num: number of the LED
    # red_led: Red LED
    # green_led: Green LED
    # blue_led: Blue LED
    # next_red_value: Next value the Red LED will be set to
    # red_value: value of the Red LED
    # next_green_value: Next value the Green LED will be set to
    # green_value: value of the Green LED
    # next_blue_value: Next value the Blue LED will be set to
    # blue_value: value of the Blue LED
    # red_ticks: Time when the Red LED value last changed
    # green_ticks: Time when the Green LED value last changed
    # blue_ticks: Time when the Blue LED value last changed
    # change_ticks: Time when any value last changed

    def __init__(self,  row, col, led_num, red_led, green_led, blue_led):
        self.row = row
        self.col = col
        self.led_num = led_num
        self.red_led = red_led
        self.green_led = green_led
        self.blue_led = blue_led

        self.red_value = 0
        self.next_red_value = 0
        self.green_value = 0
        self.next_green_value = 0
        self.blue_value = 0
        self.next_blue_value = 0

        self.red_ticks = 0
        self.green_ticks = 0
        self.blue_ticks = 0
        self.change_ticks = 0

    def get_ticks(self):
        return self.red_led.pin.factory.ticks()

    def read_ticks(self, color):
        if color == ColorMap.red:
            return self.red_ticks
        elif color == ColorMap.green:
            return self.green_ticks
        elif color == ColorMap.blue:
            return self.blue_ticks
    
    def get_led_value(self, color):
        if color == ColorMap.red:
            return self.red_value
        elif color == ColorMap.green:
            return self.green_value
        elif color == ColorMap.blue:
            return self.blue_value

    def set_led_value(self, color, value):
        if color == ColorMap.red:
            self.next_red_value = value
        elif color == ColorMap.green:
            self.next_green_value = value
        elif color == ColorMap.blue:
            self.next_blue_value = value
            
    def update_led(self):
        ticks = self.get_ticks()
        update_ticks = False
        if self.red_value != self.next_red_value:
            self.red_ticks = ticks
            self.red_value = self.next_red_value
            update_ticks = True
        if self.green_value != self.next_green_value:
            self.green_ticks = ticks
            self.green_value = self.next_green_value
            update_ticks = True
        if self.blue_value != self.next_blue_value:
            self.blue_ticks = ticks
            self.blue_value = self.next_blue_value
            update_ticks = True
        if update_ticks:
            self.change_ticks = True
        self.red_led.value = self.red_value
        self.green_led.value = self.green_value
        self.blue_led.value = self.blue_value                
