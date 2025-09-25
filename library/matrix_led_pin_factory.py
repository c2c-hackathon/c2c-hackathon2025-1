from gpiozero.pins import data
from gpiozero import Factory, BoardInfo, HeaderInfo, PinInfo, Pin
from gpiozero import PinInvalidPin, PinInvalidState, PinPWMFixedValue
from gpiozero.compat import frozendict
from time import monotonic
from threading import RLock, Thread
from types import MethodType
from .matrix_led import MatrixLED, ColorMap
from weakref import ref, WeakMethod

class MatrixLEDPinFactory(Factory):

    def __init__(self, use_led_hat=False):
        super().__init__()
        self._info = None
        self.pins = {}
        self.pin_class = MatrixLEDPin
        pwm_freq = 10000
        display_pause = 0.001
        self.matrix_led = MatrixLED(pwm_freq=pwm_freq, display_pause=display_pause, use_led_hat=use_led_hat)
        self.matrix_led.start_led_matrix()
        self.matrix_led.start()
        self.matrix_led.set_pwm_freq(pwm_freq)
        self.matrix_led.update_display_pause(display_pause)

    def ticks(self):
        return monotonic()

    def ticks_diff(self, later, earlier):
        return later - earlier

    def _get_board_info(self):
        if self._info is None:
            self._info = MatrixLEDBoardInfo.return_board_info()
        return self._info

    def close(self):
        self.matrix_led.stop_led_matrix()
        for pin in self.pins.values():
            pin.close()
        self.pins.clear()
        self.matrix_led.release_led_matrix()
        self.matrix_led.stop()

    def pin(self, name):
        for header, info in self.board_info.find_pin(name):
            try:
                pin = self.pins[info]
            except KeyError:
                pin = self.pin_class(self, info)
                self.pins[info] = pin
            return pin
        raise PinInvalidPin(f'{name} is not a valid pin name')


class MatrixLEDPin(Pin):
    
    def __init__(self, factory, info):
        super().__init__()
        if 'RED' in info.name:
            # led_color = 'red'
            led_color = ColorMap.red
            led_color_str = 'red'
        elif 'BLUE' in info.name:
            # led_color = 'blue'
            led_color = ColorMap.blue
            led_color_str = 'blue'
        elif 'GREEN' in info.name:
            # led_color = 'green'
            led_color = ColorMap.green
            led_color_str = 'green'
        else:
            raise PinInvalidPin(f'{info} is not a Matrix LED pin')
        self._factory = factory
        self._info = info
        start_idx = len(led_color_str) + 4
        self._number = int(info.name[start_idx:])
        self._pull = info.pull or 'floating'
        if led_color == None:
            raise MatrixLEDMissingColorError('LED Color missing')
        else:
            self._led_color = led_color
            self._led_color_str = led_color_str
            
    @property
    def info(self):
        return self._info
    
    @property
    def number(self):
        return self._info.name

    def __repr__(self):
        return self._info.name

    @property
    def factory(self):
        return self._factory

    def _get_info(self):
        return self.info

    def _get_state(self):
        return self.factory.matrix_led.get_led_state(self._led_color, self._number)
        
    def _set_function(self, value):
        if value == 'output':
            pass
        else:
            raise PinInvalidState(f'Matrix LED Pin cannot be {value} - output only')

    def _get_function(self):
        return 'output'

    def _get_pull(self):
        return self._pull

    def _set_state(self, value):
        self.factory.matrix_led.set_led_state(self._led_color, self._number, value)

    def _get_frequency(self):
        if self._pwm:
            freq, duty = self._pwm
            return freq
        else:
            return None

    def _set_frequency(self, value):
        self.factory.matrix_led.set_pwm_freq(value)

    def _get_frequency(self):
        return self.factory.matrix_led.get_pwm_freq(value)

class MatrixLEDBoardInfo(BoardInfo):
    __slots__ = () # workaround python issue #24931

    @classmethod
    def return_board_info(cls):
        headers = cls.generate_matrix_headers()
        board = data.BPLUS_BOARD
        return cls(
            revision='a02082', # Dummy revision - Taken from gpiozero mock.py
            model='???', # Dummy model
            pcb_revision='Unknown', # Dummy pcb revision
            released='Unknown', # Dummy released
            soc='Unknown', # Dummy soc
            manufacturer='Unknown', # Dummy manufacturer
            memory=None, # Dummy memory
            storage='MicroSD', # Dummy storage
            usb=4, # Dummy usb
            usb3=0, # Dummy usb3
            ethernet=1, # Dummy ethernet
            eth_speed=0, # Dummy eth_speed
            wifi=False, # Dummy wifi
            bluetooth=False, # Dummy bluetooth
            csi=1, # Dummy csi
            dsi=1, # Dummy dsi
            headers=headers,
            board=board # Dummy board
            )

    @classmethod
    def generate_matrix_headers(cls):
        header_list = ['Red LEDs', 'Blue LEDs', 'Green LEDs']
        rows = 4
        columns = 4
        header_data_list = []
        for header_idx, header in enumerate(header_list):
            header_data = {}
            pin_list = []
            pin_idx = 0
            if 'Red' in header:
                color = 'RED'
            elif 'Blue' in header:
                color = 'BLUE'
            elif 'Green' in header:
                color = 'GREEN'
            for row in range(rows):
                for col in range(columns):
                    pin_idx += 1
                    pin_name = f'{color} LED{pin_idx}'
                    header_data[pin_idx] = {'led': pin_name}
            header_data_list.append(header_data)

        headers = frozendict({
            header_list[hdr_idx]: HeaderInfo(
                name = header_list[hdr_idx], rows=rows, columns=columns,
                pins=frozendict({
                    number: cls._make_pin(
                        header_list[hdr_idx], number, row + 1, col + 1, functions)
                    for number, functions in header_data_list[hdr_idx].items()
                    for row in range(rows)
                    for col in range(columns)
                    })
            )
            for hdr_idx in range(len(header_list))
        })
        return headers

    @staticmethod
    def _make_pin(header, number, row, col, interfaces):
        if 'Red' in header:
            color = 'RED'
        elif 'Blue' in header:
            color = 'BLUE'
        elif 'Green' in header:
            color = 'GREEN'
        name = interfaces['led']
        names = {f'{header}:{name}'}
        start_idx = len(color) + 4
        led = int(name[start_idx:])
        names.add(f'{color.upper()}{led}')
        names.add(f'{color.upper()} {led}')
        names.add(f'{color.upper()} LED{led}')
        pull = 'floating'
        return PinInfo(
            number=number, name=name, names=frozenset(names), pull=pull,
            row=row, col=col, interfaces=frozenset(interfaces))    
        
class MatrixLEDMissingColorError(Exception):
    "Error raised when a MatrixLEDPin is not assigned a color"
