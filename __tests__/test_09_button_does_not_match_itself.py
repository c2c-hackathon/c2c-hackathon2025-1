import pytest

import _utils


def test__button_does_not_match_itself(
    solved_game, game_instance, mock_audio_play, mock_button_board, mock_rgb_led
):
    output_to_buttons = solved_game

    game_instance.play()
    mock_audio_play.reset()  # clear the mock so that we're only checking for sounds played during the test

    first_pair = next(iter(output_to_buttons.values()))
    if len(first_pair) != 2:
        pytest.xfail("Test setup error: not all buttons have pairs")

    button1 = mock_button_board._test_buttons[first_pair[0] - 1]  # First button
    button1.pin.info.number = first_pair[0]  # Mock button number
    for i in range(5):
        game_instance.when_pressed(button1)
        _utils.delay_to_let_game_process()

    button2 = mock_button_board._test_buttons[first_pair[1] - 1]  # Second button
    button2.pin.info.number = first_pair[1]  # Mock button number
    game_instance.when_pressed(button2)
    _utils.delay_to_let_game_process()

    assert len(mock_audio_play.played_audio) in {
        3,
        7,
    }, "Pressing the same button multiple times should not match it with itself"
