import logging
import queue
import threading
import time
import typing
from dataclasses import dataclass
import random

import library
from matrix_button_led_controller import MatrixButtonLEDController

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)
USE_LED_HAT = True

@dataclass
class ButtonInfo:
    color: str
    sound: str
    matched: bool = False

class Game:
    def __init__(self, button_pad: MatrixButtonLEDController):
        self.button_pad = button_pad
        self.button_pad.assign_button_events(self.when_pressed, self.when_held, self.when_released)
        self.speaker = library.speaker.Speaker()
        self.play_game = True
        self.queue = queue.Queue()
        self.selections: typing.List[int] = []
        self.pairs: typing.List[typing.List[int]] = []
        self.colors = [
            "red", "yellow", "orange", "green", "blue", "purple", "white", "brown"
        ]
        self.sounds = [
            "thunder2", "fart_z", "baby_x", "slide_whistle_x",
            "arrow2", "phone_pay", "bloop_x", "car_horn_x"
        ]
        self.initialize_button_pad()

    @property
    def correct_sound(self):
        self.speaker.play_preloaded_wav("correct_answer", wait_until_done=True)
        return "correct_answer"

    @property
    def incorrect_sound(self):
        self.speaker.play_preloaded_wav("incorrect", wait_until_done=True)
        return "incorrect"

    @property
    def end_of_game_sound(self):
        self.speaker.play_preloaded_wav("end_of_game", wait_until_done=True)
        return "end_of_game"

    def _get_pair_index(self, button_number: int) -> int:
        for i in range(len(self.pairs)):
            if button_number in self.pairs[i]:
                return i
        return -1

    def _background_logic_checker(self):
        matched_pairs = 0
        total_pairs = len(self.pairs)

        while self.play_game:
            time.sleep(0.005)
            if self.queue.empty():
                continue

            button_number = self.queue.get()
            print(f"Handling button {button_number}")
            pair_index = self._get_pair_index(button_number)

            if pair_index == -1:
                continue  

            self.button_pad.set_button_led_color(
                self.button_pad.get_button(button_number),
                self.colors[pair_index]
            )
            self.speaker.play_preloaded_wav(self.sounds[pair_index], wait_until_done=True)

            self.selections.append(button_number)

            if len(self.selections) == 2:
                first = self.selections[0]
                second = self.selections[1]
                first_idx = self._get_pair_index(first)
                second_idx = self._get_pair_index(second)

                if first == second:
                    self.selections = []
                    continue

                if first_idx == second_idx:
                    print("Correct Match!")
                    self.correct_sound
                    matched_pairs += 1
                else:
                    print("Wrong Match!")
                    self.incorrect_sound
                    time.sleep(0.5)
                    self.button_pad.set_button_led_color(self.button_pad.get_button(first), "black")
                    self.button_pad.set_button_led_color(self.button_pad.get_button(second), "black")

                self.selections = []

                if matched_pairs == total_pairs:
                    print("Game Over - All pairs matched!")
                    self.end()
                    break

    def end(self):
        colors = ["red", "orange", "yellow", "green", "blue", "purple", "red", "orange",
                  "yellow", "green", "blue", "purple", "red", "orange", "yellow", "green"]
        for i in range(1, 17):
            self.button_pad.set_button_led_color(self.button_pad.get_button(i), colors[i - 1])
            time.sleep(0.1)

        self.end_of_game_sound()

    def when_pressed(self, button):
        _logger.info(f"Button {button.pin.info.number} pressed")
        self.queue.put(button.pin.info.number)

    def when_held(self, button):
        if button.pin.info.number == 1:
            self.speaker.play_preloaded_wav("doorbell_x", wait_until_done=True)
            self.button_pad.clear_button_pad()
        elif button.pin.info.number == 2:
            for i in range(8):
                for j in range(2):
                    value = self.pairs[i][j]
                    btn = self.button_pad.get_button(value)
                    self.speaker.play_preloaded_wav(self.sounds[i], wait_until_done=True)
                    self.button_pad.set_button_led_color(btn, self.colors[i])

    def when_released(self, button):
        pass

    def initialize_button_pad(self):
        self.button_pad.clear_button_pad()

    def create_pairs(self):
        self.pairs = []
        numbers1 = [1,2,3,4,5,6,7,8]
        numbers2 = [9,10,11,12,13,14,15,16]
        for _ in range(8):
            v1 = random.choice(numbers1)
            v2 = random.choice(numbers2)
            self.pairs.append([v1, v2])
            numbers1.remove(v1)
            numbers2.remove(v2)
        print("Pairs:", self.pairs)

    def _start_game(self):
        self.thread = threading.Thread(target=self._background_logic_checker)
        self.thread.start()
        self.speaker.play_preloaded_wav("arrow2", wait_until_done=True)

    def play(self):
        self._start_game()
        try:
            input("Press Enter to exit the game...")
        except KeyboardInterrupt:
            print("Exiting game...")
        finally:
            self.play_game = False
            self.thread.join()
            self.button_pad.cleanup()

def _main():
    button_pad = MatrixButtonLEDController(
        scan_delay=0.020, pwm_freq=10000, display_pause=0.001, use_led_hat=USE_LED_HAT
    )

    game = Game(button_pad)
    game.create_pairs()
    game.play()

if __name__ == "__main__":
    _main()
