from gpiozero import ButtonBoard, LEDBoard
from typing import List
import random
from time import sleep

class ButtonPad():

    def __init__(self):

        self.row1 = 'BOARD40'
        self.row2 = 'BOARD33'
        self.row3 = 'BOARD21'
        self.row4 = 'BOARD11'

        self.col1 = 'BOARD26'
        self.col2 = 'BOARD22'
        self.col3 = 'BOARD16'
        self.col4 = 'BOARD10'

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
        
        self.row_inputs = ButtonBoard(self.row4, self.row3, self.row2, self.row1, pull_up=True, bounce_time=0.02)
        self.col_outputs = LEDBoard(self.col1, self.col2, self.col3, self.col4, active_high=False)
        self.red_leds = LEDBoard(self.red4, self.red3, self.red2, self.red1, active_high=True)
        self.blue_leds = LEDBoard(self.blue4, self.blue3, self.blue2, self.blue1, active_high = True)
        self.green_leds = LEDBoard(self.green4, self.green3, self.green2, self.green1, active_high = True)
        self.led_cols = LEDBoard(self.led_col1, self.led_col2, self.led_col3, self.led_col4, active_high= False)

        for idx in range(4):
            self.col_outputs.off(idx)
            self.red_leds.off(idx)
            self.blue_leds.off(idx)
            self.green_leds.off(idx)
            self.led_cols.off(idx)

        self.button_state = [[False for _ in range(4)] for _ in range(4)]
        self.last_button_state = self.button_state
        # 0 = Off, 1 = Red, 2 = Blue, 3 = Green
        self.button_color = [[0 for _ in range(4)] for _ in range(4)]
        self.last_button_color = self.button_color

    def set_button_colors(self):
        for button_col in range(4):
            for button_row in range(4):
                if self.button_state[button_row][button_col]:
                    # If the button was pressed last time
                    if self.last_button_color[button_row][button_col] != 0:
                        # Use the same color as last time
                        self.button_color[button_row][button_col] = self.last_button_color[button_row][button_col]
                    # If the button was not pressed last time
                    else:
                        # Pick a random color
                        self.button_color[button_row][button_col] = random.randint(1, 3)
                else:
                    self.button_color[button_row][button_col] = 0
        self.last_button_color = self.button_color       
        
    def read_buttons(self) -> List[List[bool]]:
        self.last_button_state = self.button_state
        for button_col in range(4):
            self.col_outputs.on(button_col)
            for button_row in range(4):
                self.button_state[button_row][button_col] = self.row_inputs[button_row].is_pressed
            self.col_outputs.off(button_col)

    def display_buttons(self):
        self.set_button_colors()
        for button_col in range(4):
            for button_row in range(4):
                if self.button_state[button_row][button_col]:
                    self.led_cols.on(button_col)
                    if self.button_color[button_row][button_col] == 1:
                        self.red_leds.on(button_row)
                        self.red_leds.off(button_row)
                    elif self.button_color[button_row][button_col] == 2:
                        self.blue_leds.on(button_row)
                        self.blue_leds.off(button_row)
                    elif self.button_color[button_row][button_col] == 3:
                        self.green_leds.on(button_row)
                        self.green_leds.off(button_row)
                    self.led_cols.off(button_col)

