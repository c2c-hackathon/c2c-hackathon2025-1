import random

import pytest


@pytest.fixture()
def number_sequence():
    """A fixed sequence of numbers for testing"""
    yield list(range(1, 51))


@pytest.fixture()
def expected(seeded_random, number_sequence):
    """Expected values for a seeded random instance of the game"""
    r = random.Random()
    values = [r.randint(1, 50) for _ in number_sequence]
    seeded_random.reseed()
    yield values


@pytest.mark.testing_the_tests
@pytest.mark.parametrize("method", [lambda: random, lambda: random.Random()])
def test__seeded_random_works(expected, method, number_sequence):
    """Test that the seeded random instance produces expected values"""
    lazy_loaded_method = method()

    values = [lazy_loaded_method.randint(1, 50) for _ in number_sequence]
    assert values == expected


@pytest.mark.testing_the_tests
@pytest.mark.parametrize("method", [lambda: random, lambda: random.Random()])
def test__seeded_random_works_with_repeats(expected, seeded_random, method, number_sequence):
    """Test that the seeded random instance produces expected values"""
    lazy_loaded_method = method()

    values1 = [lazy_loaded_method.randint(1, 50) for _ in number_sequence]
    seeded_random.reseed()
    values2 = [random.randint(1, 50) for _ in number_sequence]
    seeded_random.reseed()
    r = random.Random()
    values3 = [r.randint(1, 50) for _ in number_sequence]
    assert expected == values1 == values2 == values3


@pytest.mark.testing_the_tests
@pytest.mark.parametrize("method", [lambda: random, lambda: random.Random()])
def test__seeded_random_works_with_shuffles(expected, seeded_random, method, number_sequence):
    """Test that the seeded random instance produces expected values"""
    lazy_loaded_method = method()

    values1 = [lazy_loaded_method.randint(1, 50) for _ in number_sequence]
    seeded_random.reseed()
    values2 = [random.randint(1, 50) for _ in number_sequence]
    seeded_random.reseed()
    r = random.Random()
    values3 = [r.randint(1, 50) for _ in number_sequence]
    seeded_random.reseed()

    random.shuffle(values1)
    seeded_random.reseed()
    random.shuffle(values2)
    seeded_random.reseed()
    r = random.Random()
    r.shuffle(values3)

    assert expected == values1 == values2 == values3
