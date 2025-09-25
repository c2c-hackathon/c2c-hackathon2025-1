import pytest

import _utils


def test__buttons_stay_on_after_match(
    solved_game, game_instance, mock_audio_play, mock_button_board, mock_rgb_led
):
    output_to_buttons = solved_game

    game_instance.play()

    # Press all buttons in pairs
    for i, buttons in enumerate(output_to_buttons.values()):
        if len(buttons) != 2:
            pytest.xfail("Test setup error: not all buttons have pairs")

        button1 = mock_button_board._test_buttons[buttons[0] - 1]  # First button
        button1.pin.info.number = buttons[0]  # Mock button number
        game_instance.when_pressed(button1)
        _utils.delay_to_let_game_process()

        button2 = mock_button_board._test_buttons[buttons[1] - 1]  # Second button
        button2.pin.info.number = buttons[1]  # Mock button number
        game_instance.when_pressed(button2)
        _utils.delay_to_let_game_process()  # Give some time for the button presses to be processed

        leds = [mock_rgb_led.leds[button - 1] for button in buttons]
        assert [
            led.color.html != "#000000" for led in leds
        ], "Lights should stay on after matching button press"


def test__buttons_turn_off_after_non_match(
    solved_game, game_instance, mock_audio_play, mock_button_board, mock_rgb_led
):
    output_to_buttons = solved_game

    game_instance.play()
    mock_audio_play.reset()  # clear the mock so that we're only checking for sounds played during the test

    # Press first button of each pair, then press a non-matching button
    all_buttons = list(output_to_buttons.values())
    for i, buttons in enumerate(all_buttons):
        if len(buttons) != 2:
            pytest.xfail("Test setup error: not all buttons have pairs")
        button1 = mock_button_board._test_buttons[buttons[0] - 1]  # First button of the pair
        button1.pin.info.number = buttons[0]  # Mock button number
        game_instance.when_pressed(button1)
        _utils.delay_to_let_game_process()

        # Find a non-matching button
        non_matching_button_num = all_buttons[(i + 1) % len(all_buttons)][
            0
        ]  # First button of the next pair
        button2 = mock_button_board._test_buttons[non_matching_button_num - 1]
        non_matching_pair = [buttons[0], non_matching_button_num]
        button2.pin.info.number = non_matching_button_num
        game_instance.when_pressed(button2)
        _utils.delay_to_let_game_process()  # Give some time for the button presses to be processed

        leds = [mock_rgb_led.leds[button - 1] for button in non_matching_pair]
        assert [
            led.color.html == "#000000" for led in leds
        ], "Lights should be turned off after non-matching button press"
