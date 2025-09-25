import collections
import functools
import os
import pathlib
import random
import sys
import threading
import time
import typing
import unittest.mock

import pytest
import pytest_mock

import _utils

_MODULE_PATH = pathlib.Path(__file__).parent
_PROJECT_ROOT = _MODULE_PATH.parent

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import game
    import matrix_button_led_controller


def pytest_configure(config):
    """Ensure the project root is on sys.path for imports."""
    if str(_PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(_PROJECT_ROOT))


def pytest_collection_modifyitems(config, items):
    """pytest collection hook."""
    # skip tests marked as 'testing_the_tests' unless explicitly requested
    if not config.option.markexpr or "testing_the_tests" not in config.option.markexpr:
        skip_marker = pytest.mark.skip(
            reason="Skipped: only run when explicitly requested with -m testing_the_tests"
        )
        for item in items:
            if "testing_the_tests" in item.keywords:
                item.add_marker(skip_marker)


@pytest.fixture(autouse=True)
def mock_hardware_libraries(mocker: pytest_mock.MockerFixture):
    """Mock the hardware access libraries that we only install on the Pi."""

    mocker.patch.dict(
        "sys.modules",
        {
            "simpleaudio": unittest.mock.Mock(),
            "gpiozero": unittest.mock.Mock(),
            "gpiozero.pins": unittest.mock.Mock(),
            "gpiozero.compat": unittest.mock.Mock(),
            "gpiozero.threads": unittest.mock.Mock(),
        },
    )


@pytest.fixture()
def mock_input(mocker: pytest_mock.MockerFixture):
    """Mock the stdlib input function to end the game"""
    _mock = mocker.patch("builtins.input")
    yield _mock


@pytest.fixture()
def mock_audio_play(
    mocker: pytest_mock.MockerFixture, mock_hardware_libraries: None
) -> typing.Generator[unittest.mock.Mock, None, None]:  # purely for order
    """Mock the audio play function to avoid playing audio during tests"""
    _mock = mocker.patch("simpleaudio.WaveObject")
    _mock.sounds = []
    _mock.played_audio = collections.deque()
    _mock.game_audio_to_ignore = set()

    def _reset():
        _mock.sounds.clear()
        _mock.played_audio.clear()
        _mock.reset_mock()

    _mock.reset = _reset

    def _store_played_audio(name: str):
        _mock.played_audio.appendleft(name)  # put at beginning for easy access to last played
        return unittest.mock.MagicMock()

    def _from_wave_file(path):
        result = unittest.mock.MagicMock()
        result.play.return_value = unittest.mock.MagicMock()
        result.play.name = path
        result.play.side_effect = lambda: _store_played_audio(path)
        _mock.sounds.append(result)
        return result

    _mock.from_wave_file.side_effect = _from_wave_file

    def get_last_played_audio():
        played_audios = next(
            (name for name in _mock.played_audio if name not in _mock.game_audio_to_ignore),
            None,
        )
        return played_audios if played_audios else None

    _mock.get_last_played_audio = get_last_played_audio
    yield _mock


@pytest.fixture()
def mock_button_board(
    mocker: pytest_mock.MockerFixture,
    mock_hardware_libraries: None,  # purely for order
):
    """Mock the button board function to avoid interacting with hardware during tests"""
    _mock = mocker.patch("gpiozero.ButtonBoard")
    _mock_buttons = [unittest.mock.Mock() for _ in range(16)]
    _mock._test_buttons = _mock_buttons
    _mock.return_value.__getitem__ = lambda self, x: _mock_buttons[x]
    yield _mock


class LoggingRGBHandler:
    def __init__(self, *args, **kwargs):
        if "leds" in kwargs:
            kwargs.pop("leds").append(self)
        self._color = None
        self.all_set_colors = collections.deque()

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, value):
        self._color = value
        self.all_set_colors.appendleft(value)


@pytest.fixture()
def mock_rgb_led(
    mocker: pytest_mock.MockerFixture,
    mock_hardware_libraries: None,  # purely for order
):
    leds = []
    _mock = mocker.patch("gpiozero.RGBLED", new=functools.partial(LoggingRGBHandler, leds=leds))
    _mock.leds = leds

    yield _mock


@pytest.fixture()
def matrix_button_led_controller_instance(
    mock_button_board: unittest.mock.Mock, mock_rgb_led: unittest.mock.Mock
):
    """A setup MatrixButtonLEDController using mock hardware libraries"""
    import matrix_button_led_controller

    button_board = matrix_button_led_controller.MatrixButtonLEDController()
    yield button_board


class ProxyWrapper:
    def __init__(self, obj):
        # Use object.__setattr__ to avoid recursion during initialization
        object.__setattr__(self, "obj", obj)
        object.__setattr__(self, "done", False)
        object.__setattr__(self, "play", None)
        object.__setattr__(self, "restart", None)

    def __getattr__(self, name):
        return getattr(self.obj, name)

    def __setattr__(self, name, value):
        # Handle proxy-specific attributes directly
        if name in {"obj", "done", "play", "restart"}:
            object.__setattr__(self, name, value)
        else:
            # Pass all other attribute writes to the wrapped object
            setattr(self.obj, name, value)


@pytest.fixture()
def game_instance(
    mock_hardware_libraries: None,
    seeded_random: None,
    matrix_button_led_controller_instance: "matrix_button_led_controller.MatrixButtonLEDController",
    mock_input: unittest.mock.Mock,
    mock_audio_play: unittest.mock.Mock,
) -> typing.Generator["game.Game", None, None]:
    """Create a Game instance with the mocked MatrixButtonLEDController"""
    import game

    game_instance = ProxyWrapper(game.Game(matrix_button_led_controller_instance))
    game_instance.done = False  # To control the game loop in tests
    mock_audio_play.game_audio_to_ignore.update(
        [
            os.path.join("sounds", o) + ".wav"
            for o in [
                game_instance.correct_sound,
                game_instance.incorrect_sound,
                game_instance.end_of_game_sound,
            ]
        ]
    )

    def _wait_till_game_done(*_, **__):
        while not game_instance.done:
            _utils.delay_to_let_game_process()
        # exit the game loop

    mock_input.side_effect = _wait_till_game_done

    original_play = game_instance.obj.play
    game_thread = threading.Thread(target=original_play)

    def _background_start_game(*_, **__):
        nonlocal game_thread  # otherwise this holds onto the original
        game_thread = threading.Thread(target=original_play)
        game_thread.start()
        _utils.delay_to_let_game_process()  # Give some time for the game to start

    def _restart():
        nonlocal game_thread, original_play
        # end the current game
        game_instance.done = True

        game_thread.join()

        # make a new game
        game_instance.obj = game.Game(matrix_button_led_controller_instance)
        original_play = game_instance.obj.play
        game_thread = threading.Thread(target=original_play)
        game_instance.done = False  # To control the game loop in tests
        game_instance.play = _background_start_game
        game_instance.restart = _restart  # Allow tests to restart the game
        return game_instance

    game_instance.play = _background_start_game
    game_instance.restart = _restart  # Allow tests to restart the game

    yield game_instance

    game_instance.done = True
    if game_thread.is_alive():
        game_thread.join()


@pytest.fixture()
def seeded_random(mocker: pytest_mock.MockerFixture):
    """Seed the random number generator for consistent test results and allow reseeding."""
    original_random = random.Random
    r = original_random()
    initial_state = r.getstate()
    r.seed(42)

    # Patch random.Random to always return our seeded instance
    _mock_random = mocker.patch("random.Random", return_value=r)
    # Patch random.randint to use our seeded instance
    _mock_randint = mocker.patch("random.randint", side_effect=r.randint)
    _mock_randint._parent = r
    # Patch random.random to use our seeded instance
    _mock_random_func = mocker.patch("random.random", side_effect=r.random)
    _mock_random_func._parent = r
    # Patch random.shuffle to use our seeded instance
    _mock_random_shuffle = mocker.patch("random.shuffle", side_effect=r.shuffle)
    _mock_random_shuffle._parent = r

    def reseed():
        r.setstate(initial_state)
        r.seed(42)
        random.setstate(initial_state)
        random.seed(42)

    # Attach reseed to the fixture for user access
    _mock_random.reseed = reseed
    reseed()

    yield _mock_random

    random.seed()  # Reset the seed after the test


_cached_solution = None


def _cached_solved_game(
    game_instance: "game.Game",
    mock_button_board: unittest.mock.Mock,
    mock_rgb_led: unittest.mock.Mock,
    mock_audio_play: unittest.mock.Mock,
) -> typing.Dict[typing.Tuple[str, str], typing.List[int]]:
    """in-memory cache for solved game fixture"""
    global _cached_solution
    if _cached_solution is not None:
        return _cached_solution

    output_to_buttons = _utils.solve_game(
        game_instance, mock_button_board, mock_rgb_led, mock_audio_play
    )

    _cached_solution = output_to_buttons
    return output_to_buttons


@pytest.fixture()
def solved_game(
    seeded_random: unittest.mock.Mock,
    game_instance: "game.Game",
    mock_button_board: unittest.mock.Mock,
    mock_rgb_led: unittest.mock.Mock,
    mock_audio_play: unittest.mock.Mock,
) -> typing.Generator[typing.Dict[typing.Tuple[str, str], typing.List[int]], None, None]:
    """A game instance which has been played to completion"""
    # Push every button and log the sound/color, creates mapping
    game_instance.play()
    _utils.delay_to_let_game_process()

    result = _cached_solved_game(game_instance, mock_button_board, mock_rgb_led, mock_audio_play)

    mock_audio_play.reset()
    seeded_random.reseed()
    game_instance.restart()

    yield result
