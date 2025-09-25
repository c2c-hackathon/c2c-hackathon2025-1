import unittest.mock

import pytest

import _utils


def test__no_button_press_yield_no_audio(game_instance, mock_audio_play, mock_button_board):
    game_instance.play()
    mock_audio_play.reset()  # Ensure audio play was called on button press

    # no action
    _utils.delay_to_let_game_process()

    assert len(mock_audio_play.played_audio) == 0  # Ensure audio play was called on button press


@pytest.fixture()
def game_with_one_button_pressed(game_instance, mock_audio_play, mock_button_board):
    game_instance.play()
    mock_audio_play.reset()  # Ensure audio play was called on button press

    # Simulate button press
    button = mock_button_board._test_buttons[0]  # First button
    button.pin.info.number = 1  # Mock button number
    game_instance.when_pressed(button)
    _utils.delay_to_let_game_process()

    yield game_instance


def test__button_press__sound_is_played(game_with_one_button_pressed, mock_audio_play):
    assert len(mock_audio_play.played_audio) == 1  # Ensure audio play was called on button press


def test__button_press__led_is_lit(game_with_one_button_pressed, mock_button_board, mock_rgb_led):
    led_under_test = mock_rgb_led.leds[0]  # First LED
    assert hasattr(led_under_test, "color") and not isinstance(
        led_under_test.color, unittest.mock.Mock
    )
