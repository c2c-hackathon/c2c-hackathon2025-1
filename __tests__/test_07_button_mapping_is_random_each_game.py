import typing
import unittest.mock

import _utils

if typing.TYPE_CHECKING:
    import game


def solved_random_game(
    game_instance: "game.Game",
    mock_button_board: unittest.mock.Mock,
    mock_rgb_led: unittest.mock.Mock,
    mock_audio_play: unittest.mock.Mock,
) -> typing.Generator[typing.Dict[typing.Tuple[str, str], typing.List[int]], None, None]:
    """A game instance which has been played to completion"""
    # Push every button and log the sound/color, creates mapping
    game_instance.play()
    _utils.delay_to_let_game_process()

    result = dict(
        _utils.solve_game(game_instance, mock_button_board, mock_rgb_led, mock_audio_play)
    )

    mock_audio_play.reset()
    game_instance.restart()

    return result


def test__button_mapping_is_random_each_game(
    game_instance: "game.Game",
    mock_button_board: unittest.mock.Mock,
    mock_rgb_led: unittest.mock.Mock,
    mock_audio_play: unittest.mock.Mock,
):
    """Test that the button mapping is different each game"""
    first_game = solved_random_game(game_instance, mock_button_board, mock_rgb_led, mock_audio_play)

    second_game = solved_random_game(
        game_instance, mock_button_board, mock_rgb_led, mock_audio_play
    )

    assert first_game != second_game, "Button mapping should be different each game"
