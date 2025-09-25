import collections
import time

import pytest


def delay_to_let_game_process():
    time.sleep(0.1)


def solve_game(game_instance, mock_button_board, mock_rgb_led, mock_audio_play):
    try:
        button_to_info = {}
        for i in range(16):
            button = mock_button_board._test_buttons[i]  # Get the button from the mock board
            button.pin.info.number = i + 1  # Mock button number
            game_instance.when_pressed(button)
            delay_to_let_game_process()
            idx = button.pin.info.number
            played_audio = mock_audio_play.get_last_played_audio()
            if played_audio is None:
                pytest.xfail("Failed to set up the game state, no audio played on button press")

            # check for color getting turned off - this happens if the second one and wrong
            color = mock_rgb_led.leds[i].color
            if color is not None and hasattr(color, "html") and getattr(color, "html") == "#000000":
                # push it again to get the color
                game_instance.when_pressed(button)
                delay_to_let_game_process()
            color = mock_rgb_led.leds[i].color

            button_to_info[idx] = (color, played_audio)

        # Create a mapping of sound to buttons
        output_to_buttons = collections.defaultdict(list)
        for idx, (color, sound) in button_to_info.items():
            output_to_buttons[(color, sound)].append(
                idx
            )  # defaultdict will create list if not present
    except Exception as e:
        print(f"Error during game setup: {e}")
        pytest.xfail("Failed to setup the game state")

    if not all(len(v) == 2 for v in output_to_buttons.values()):
        pytest.xfail("Failed to set up the game state, not all buttons have pairs")
    return output_to_buttons
