import dice


def test_roll_two_dice_in_range():
    # Two dice can total anywhere from 2 (1+1) to 12 (6+6).
    for _ in range(1000):
        total = dice.roll_two_dice()
        assert 2 <= total <= 12


def test_roll_die_in_range():
    for _ in range(1000):
        assert 1 <= dice.roll_die() <= 6
