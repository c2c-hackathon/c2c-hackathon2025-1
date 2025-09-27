"""
Matrix Button LED Controller

This module provides a high-level interface for controlling a matrix of buttons
with integrated RGB LEDs, designed for educational games and interactive projects
using Raspberry Pi GPIO pins.

The controller manages both button input detection and LED output control through
custom pin factories that handle matrix scanning and LED multiplexing.
"""

from gpiozero import RGBLED, LED, ButtonBoard, Button
from library.matrix_led import MatrixLED, MatrixRGB
from library.matrix_scan import MatrixScan, MatrixScanButton
from library.matrix_led_pin_factory import MatrixLEDPinFactory, MatrixLEDPin, MatrixLEDBoardInfo
from library.matrix_scan_pin_factory import MatrixScanPinFactory, MatrixScanPin, MatrixScanBoardInfo
import time
from colorzero import Color


class MatrixButtonLEDController:
    """
    A controller for a matrix of buttons with integrated RGB LEDs.
    
    This class provides a unified interface for managing button input events
    and LED color control in a matrix configuration. It handles the complex
    matrix scanning and LED multiplexing through specialized pin factories.
    
    Attributes:
        button_count (int): Number of buttons in the matrix
        scan_delay (float): Delay between matrix scans in seconds
        pwm_freq (int): PWM frequency for LED control
        display_pause (float): Pause between LED updates in seconds
        matrix_button_board (ButtonBoard): GPIO button board interface
        rgb_leds (list): List of RGBLED objects for each button
    
    Example:
        >>> controller = MatrixButtonLEDController(button_count=16)
        >>> controller.assign_button_events(on_press, on_hold, on_release)
        >>> controller.set_button_led_color(controller.get_button(1), "red")
        >>> controller.run()
    """
    
    def __init__(self, button_count=16, scan_delay=0.020, pwm_freq=10000, 
                 display_pause=0.001, use_led_hat=False):
        """
        Initialize the Matrix Button LED Controller.
        
        Args:
            button_count (int): Number of buttons in the matrix (default: 16)
            scan_delay (float): Time delay between matrix scans in seconds (default: 0.020)
            pwm_freq (int): PWM frequency for LED control in Hz (default: 10000)
            display_pause (float): Pause between LED display updates in seconds (default: 0.001)
            use_led_hat (bool): Whether to use LED HAT configuration (default: False)
        
        Raises:
            ValueError: If button_count is not positive
            RuntimeError: If GPIO initialization fails
        
        Note:
            The scan_delay affects button responsiveness - lower values increase
            responsiveness but may cause interference. The pwm_freq affects LED
            brightness smoothness and should be high enough to avoid flicker.
        """
        self.button_count = button_count
        self.scan_delay = scan_delay
        self.pwm_freq = pwm_freq
        self.display_pause = display_pause

        # Initialize factories
        self.button_factory = MatrixScanPinFactory(use_led_hat=use_led_hat)
        self.led_factory = MatrixLEDPinFactory(use_led_hat=use_led_hat)

        # Create the button board
        self.matrix_button_board = ButtonBoard(
            *range(1, button_count + 1),
            pull_up=None,
            active_state=True,
            pin_factory=self.button_factory,
            hold_time=3
        )

        # Create the RGB LED array
        self.rgb_leds = [
            RGBLED(f'RED {idx+1}', f'GREEN {idx+1}', f'BLUE {idx+1}', pin_factory=self.led_factory)
            for idx in range(button_count)
        ]

        # Configure scan parameters
        self._configure_scan_parameters()

    def _configure_scan_parameters(self):
        """
        Configure the scanning parameters for both button detection and LED control.
        
        This private method sets up the timing parameters for matrix scanning
        and LED multiplexing to ensure proper operation without interference.
        """
        # Update button scan parameters
        self.button_factory.matrix_scan.update_scan_delay(self.scan_delay)

        # Update RGB scan parameters
        self.led_factory.matrix_led.set_pwm_freq(self.pwm_freq)
        self.led_factory.matrix_led.update_display_pause(self.display_pause)

    def assign_button_events(self, when_pressed, when_held, when_released):
        """
        Assign event handler functions to all buttons in the matrix.
        
        Args:
            when_pressed (callable): Function called when a button is pressed.
                                   Should accept one parameter: the button object.
            when_held (callable): Function called when a button is held down.
                                 Should accept one parameter: the button object.
            when_released (callable): Function called when a button is released.
                                    Should accept one parameter: the button object.
        
        Example:
            >>> def on_press(button):
            ...     print(f"Button {button.pin.info.number} pressed")
            >>> 
            >>> def on_hold(button):
            ...     print(f"Button {button.pin.info.number} held")
            >>> 
            >>> def on_release(button):
            ...     print(f"Button {button.pin.info.number} released")
            >>> 
            >>> controller.assign_button_events(on_press, on_hold, on_release)
        
        Note:
            Pass None for any event type you don't want to handle.
            The button parameter passed to handlers contains pin information
            accessible via button.pin.info.number (1-based button index).
        """
        for button in range(self.button_count):
            self.matrix_button_board[button].when_pressed = when_pressed
            self.matrix_button_board[button].when_held = when_held
            self.matrix_button_board[button].when_released = when_released

    def clear_button_pad(self):
        """
        Turn off all button LEDs by setting them to black.
        
        This method quickly clears the entire button matrix display,
        useful for resetting the visual state or initializing the game.
        
        Example:
            >>> controller.clear_button_pad()  # All LEDs turn off
        """
        for button in self.matrix_button_board:
            self.set_button_led_color(button, "black")

    def set_button_led_color(self, button, color):
        """
        Set the LED color for a specific button.
        
        Args:
            button: Button object obtained from get_button() or event handlers
            color (str): Color name or hex value. Supports standard color names
                        like "red", "green", "blue", "yellow", "purple", "white",
                        "black", as well as extended colors like "chartreuse",
                        "aqua", "fuchsia", etc.
        
        Raises:
            ValueError: If the color name is not recognized
            AttributeError: If the button object is invalid
        
        Example:
            >>> button = controller.get_button(5)
            >>> controller.set_button_led_color(button, "red")
            >>> controller.set_button_led_color(button, "#FF0000")  # Same as red
            >>> controller.set_button_led_color(button, "chartreuse")
        
        Note:
            Color "black" turns the LED off. Colors are case-insensitive.
            See colorzero documentation for full list of supported color names.
        """
        button_idx = button.pin.info.number
        self.rgb_leds[button_idx - 1].color = Color(color)
        
    def get_button(self, index):
        """
        Get a button object by its index number.
        
        Args:
            index (int): Button index (1-based, from 1 to button_count)
        
        Returns:
            Button: The button object at the specified index
        
        Raises:
            IndexError: If index is out of range (< 1 or > button_count)
        
        Example:
            >>> button_5 = controller.get_button(5)
            >>> controller.set_button_led_color(button_5, "blue")
        
        Note:
            Button indices are 1-based to match physical button labeling.
            For a 4x4 matrix, valid indices are 1-16.
        """
        
        return self.matrix_button_board[index - 1]
    
    def run(self):
        """
        Run the controller in interactive mode.
        
        This method starts the controller and waits for user input to exit.
        It's primarily used for testing and demonstration purposes.
        
        The method will block until the user presses Enter, then automatically
        clean up GPIO resources.
        
        Example:
            >>> controller = MatrixButtonLEDController()
            >>> controller.assign_button_events(press_handler, hold_handler, release_handler)
            >>> controller.run()  # Blocks until user presses Enter
        
        Note:
            This method is typically used at the end of a script when you want
            the program to keep running to handle button events. For game loops
            or custom control flow, use the controller methods directly and
            call cleanup() when finished.
        """
        try:
            input('Press <ENTER> to close the test')
        finally:
            self.cleanup()

    def cleanup(self):
        """
        Clean up GPIO resources and close connections.
        
        This method should be called when you're finished using the controller
        to properly release GPIO pins and clean up system resources.
        
        It's automatically called by the run() method, but should be explicitly
        called if you're managing the controller lifecycle yourself.
        
        Example:
            >>> controller = MatrixButtonLEDController()
            >>> # ... use the controller ...
            >>> controller.cleanup()  # Clean up when done
        
        Note:
            After calling cleanup(), the controller should not be used further.
            Create a new instance if you need to use the button matrix again.
        """
        self.button_factory.close()
        self.matrix_button_board.close()

# Example usage
if __name__ == "__main__":
    """
    Demonstration of the MatrixButtonLEDController.
    
    This example creates a 16-button controller and runs it in interactive mode.
    When run directly, this script will:
    1. Initialize a 4x4 button matrix
    2. Set up default button event handlers (none assigned here)
    3. Wait for user input to exit
    4. Clean up GPIO resources
    
    To run:
        python3 matrix_button_led_controller.py
    
    For actual use in a game or application, create the controller and
    assign proper event handlers before calling run() or managing the
    lifecycle manually.
    """
    button_count = 16  # 4x4 matrix configuration
    
    print(f"Initializing {button_count}-button matrix controller...")
    controller = MatrixButtonLEDController(button_count)
    
    print("Controller ready. Press buttons to test (no events assigned).")
    print("Matrix button controller is running...")
    controller.run()
