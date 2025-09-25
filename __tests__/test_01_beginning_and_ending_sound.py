import pytest

import _utils


def test__sound_is_played_to_start_game(
    game_instance,
    mock_audio_play,
):
    game_instance.play()

    assert len(mock_audio_play.played_audio) == 1  # Ensure audio play was called


def test__win_condition(
    solved_game, game_instance, mock_audio_play, mock_button_board, mock_rgb_led
):
    output_to_buttons = solved_game

    game_instance.play()
    mock_audio_play.reset()  # clear the mock so that we're only checking for sounds played during the test

    # Press all buttons in pairs
    for i, buttons in enumerate(output_to_buttons.values()):
        if len(buttons) != 2:
            pytest.xfail("Test setup error: not all buttons have pairs")

        button1 = mock_button_board._test_buttons[buttons[0] - 1]  # First button
        button1.pin.info.number = buttons[0]  # Mock button number
        game_instance.when_pressed(button1)
        _utils.delay_to_let_game_process()
        color1 = mock_rgb_led.leds[buttons[0] - 1].color
        sound1 = mock_audio_play.get_last_played_audio()
        assert sound1 is not None, f"No sound played for button {buttons[0]}"

        button2 = mock_button_board._test_buttons[buttons[1] - 1]  # Second button
        button2.pin.info.number = buttons[1]  # Mock button number
        game_instance.when_pressed(button2)
        _utils.delay_to_let_game_process()  # Give some time for the button presses to be processed
        color2 = next(
            (
                color
                for color in mock_rgb_led.leds[buttons[1] - 1].all_set_colors
                if getattr(color, "html", "#000000") != "#000000"
            ),
            None,
        )
        sound2 = mock_audio_play.get_last_played_audio()
        assert sound2 is not None, f"No sound played for button {buttons[1]}"

        assert color1 == color2, f"Button {buttons[0]} and {buttons[1]} should have the same color"
        assert sound1 == sound2, f"Button {buttons[0]} and {buttons[1]} should have the same sound"

    # Check that the end_of_game sound was played
    assert len(mock_audio_play.played_audio) == 8 * 3 + 1, f"No sound played for end_of_game"
