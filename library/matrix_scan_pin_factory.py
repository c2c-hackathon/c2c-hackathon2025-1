from gpiozero.pins import data
from gpiozero import Factory, BoardInfo, HeaderInfo, PinInfo, Pin
from gpiozero import PinInvalidPin, PinInvalidState, PinSetInput, PinInvalidPull, PinPWMFixedValue, PinInvalidBounce
from gpiozero.compat import frozendict
from time import monotonic
from threading import RLock, Thread
from types import MethodType
from .matrix_scan import MatrixScan
from weakref import ref, WeakMethod


class MatrixScanPinFactory(Factory):

    def __init__(self, use_led_hat=False):
        super().__init__()
        self._info = None
        self.pins = {}
        self.pin_class = MatrixScanPin
        scan_delay = 0.020
        self.matrix_scan = MatrixScan(scan_delay, use_led_hat=use_led_hat)
        self.matrix_scan.start_scan_matrix()
        self.matrix_scan.start()
        self.matrix_scan.update_scan_delay(scan_delay)
        
    def ticks(self):
        return monotonic()

    def ticks_diff(self, later, earlier):
        return later - earlier

    def _get_board_info(self):
        if self._info is None:
            self._info = MatrixScanBoardInfo.return_board_info()
        return self._info
            
    def close(self):
        self.matrix_scan.stop_scan_matrix()
        for pin in self.pins.values():
            pin.close()
        self.pins.clear()
        self.matrix_scan.release_scan_matrix()
        self.matrix_scan.stop()

    def pin(self, name):
        for header, info in self.board_info.find_pin(name):
            try:
                pin = self.pins[info]
            except KeyError:
                pin = self.pin_class(self, info)
                self.pins[info] = pin
                self.matrix_scan.enable_button(name)
                self.matrix_scan.set_callback(name, pin._call_when_changed)
            return pin
        raise PinInvalidPin(f'{name} is not a valid pin name')

class MatrixScanPin(Pin):
    
    def __init__(self, factory, info):
        super().__init__()
        if 'button' not in info.interfaces:
            raise PinInvalidPin(f'{info} is not a Matrix Button pin')
        self._factory = factory
        self._info = info
        self._number = int(info.name[3:])
        self._when_changed_lock = RLock()
        self._when_changed = None
        self._edges = None
        self._bounce = None
        # Dummy properties - These have no use
        self._pull = info.pull or 'floating'
        self._pwm = None
        self._frequency = None
        self._duty_cycle = None
        
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

    # Matrix Scan pins cannot be outputs
    def output_with_state(self, state):
        raise PinSetInput('Matrix Pad Pin does not have an output')

    def _get_state(self):
        return self.factory.matrix_scan.get_button_state(self._number)

    def _set_state(self, value):
        raise PinInvalidState('Cannot Set State on Matrix Pad Pin')

    def _get_function(self):
        return 'input'

    def _set_function(self, value):
        if value == 'input':
            pass
        else:
            raise PinSetInput(f'Matrix Pad Pin cannot be {value} - input only')

    def _get_pull(self):
        return self._pull

    def _set_pull(self, value):
        if value != 'floating':
            raise PinInvalidPull(f'Matrix Pad Pin has no pull option {value} - must be floating')
        else:
            pass

    def _get_frequency(self):
        return self._frequency

    def _set_frequency(self, value):
        if value != None:
            raise PinPWMFixedValue('Matrix Pad Pin cannot have PWM output')
        else:
            pass

    # Dummy method, doesn't do anything
    def _get_bounce(self):
        return self._bounce

    # Dummy method, doesn't do anything
    def _set_bounce(self, value):
        self._bounce = value

    def _get_edges(self):
        return self._edges

    def _set_edges(self, value):
        f = self.when_changed
        self.when_changed = None
        self._edges = value
        self.factory.matrix_scan.set_button_edge_trig(self._number, value)
        self.when_changed = f
        
    def _call_when_changed(self, ticks=None, state=None):
        method = self._when_changed()
        if method is None:
            self.when_changed = None
        else:
            if ticks == None:
                ticks = self.factory.ticks()
            if state == None:
                state = self.state
            method(ticks, state)

    def _get_when_changed(self):
        return None if self._when_changed is None else self._when_changed()

    def _set_when_changed(self, value):
        with self._when_changed_lock:
            if value is None:
                if self._when_changed is not None:
                    self._disable_event_detect()
                self._when_changed = None
            else:
                enabled = self._when_changed is not None
                if isinstance(value, MethodType):
                    self._when_changed = WeakMethod(value)
                else:
                    self._when_changed = ref(value)
                if not enabled:
                    self._enable_event_detect()

    
    def _enable_event_detect(self):
        self.factory.matrix_scan.watch_button(self._number, self._edges)


    def _disable_event_detect(self):
        self.factory.matrix_scan.unwatch_button(self._number)

    def close(self):
        self._disable_event_detect()
        self.factory.matrix_scan.disable_button(self._number)
        self.factory.matrix_scan.clear_callback(self._number)

class MatrixScanBoardInfo(BoardInfo):
    __slots__ = () # workaround python issue #24931

    @classmethod
    def return_board_info(cls):
        headers = cls.generate_matrix_header()
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
    def generate_matrix_header(cls):
        header = 'Matrix Pad'
        rows = 4
        columns = 4

        header_data = {}
        pin_list = []
        
        pin_idx = 0
        for row in range(rows):
            for col in range(columns):
                pin_idx += 1
                pin_name = f'BTN{pin_idx}'
                header_data[pin_idx] = {'button': pin_name}

        headers = frozendict({
            header: HeaderInfo(
                name = header, rows=rows, columns=columns,
                pins=frozendict({
                    number: cls._make_pin(
                        header, number, row + 1, col + 1, functions)
                    for number, functions in header_data.items()
                    for row in range(rows)
                    for col in range(columns)
                    })
            )
        })
        return headers

    @staticmethod
    def _make_pin(header, number, row, col, interfaces):
        name = interfaces['button']
        names = {f'{header}:{name}'}
        button = int(name[3:])
        names.add(button)
        names.add(str(button))
        names.add(f'BUTTON{button}')
        names.add(f'BTN{button}')
        pull = 'floating'
        return PinInfo(
            number=number, name=name, names=frozenset(names), pull=pull,
            row=row, col=col, interfaces=frozenset(interfaces))    
                
class NotMatrixScanError(Exception):
    "Error raised when a MatrixPinFactory is not passed a MatrixScan object"
 
