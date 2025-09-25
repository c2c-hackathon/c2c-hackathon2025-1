import pytest

import _utils


@pytest.fixture()
def game_with_one_pair_pressed(solved_game, game_instance, mock_button_board):
    output_to_buttons = solved_game

    game_instance.play()

    first_pair = next(iter(output_to_buttons.values()))
    if len(first_pair) != 2:
        pytest.xfail("Test setup error: not all buttons have pairs")

    button1 = mock_button_board._test_buttons[first_pair[0] - 1]  # First button
    button1.pin.info.number = first_pair[0]  # Mock button number
    game_instance.when_pressed(button1)
    _utils.delay_to_let_game_process()

    button2 = mock_button_board._test_buttons[first_pair[1] - 1]  # Second button
    button2.pin.info.number = first_pair[1]  # Mock button number
    game_instance.when_pressed(button2)
    _utils.delay_to_let_game_process()

    yield game_instance


def test__already_matched_button_does_not_count_towards_matches(
    solved_game, game_with_one_pair_pressed, mock_audio_play, mock_button_board
):
    output_to_buttons = solved_game
    game_instance = game_with_one_pair_pressed

    pairs = iter(output_to_buttons.values())
    first_pair = next(pairs)
    if len(first_pair) != 2:
        pytest.xfail("Test setup error: not all buttons have pairs")
    second_pair = next(pairs)
    if len(second_pair) != 2:
        pytest.xfail("Test setup error: not all buttons have pairs")

    # re-press the first button of the already matched pair
    button0 = mock_button_board._test_buttons[first_pair[0] - 1]  # First button
    button0.pin.info.number = first_pair[0]  # Mock button number
    game_instance.when_pressed(button0)
    _utils.delay_to_let_game_process()

    mock_audio_play.reset()  # clear the mock so that we're only checking for sounds played after this

    button1 = mock_button_board._test_buttons[second_pair[0] - 1]  # First button
    button1.pin.info.number = second_pair[0]  # Mock button number
    game_instance.when_pressed(button1)
    _utils.delay_to_let_game_process()

    button2 = mock_button_board._test_buttons[second_pair[1] - 1]  # Second button
    button2.pin.info.number = second_pair[1]  # Mock button number
    game_instance.when_pressed(button2)
    _utils.delay_to_let_game_process()

    assert (
        len(mock_audio_play.played_audio) == 3
    ), "Pressing a previously matched button should not impact matching logic"
