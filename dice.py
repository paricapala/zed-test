import random


def roll_die():
    """Return a random integer from 1 to 6, simulating a single die roll."""
    return random.randint(1, 6)


def roll_two_dice():
    """Roll two dice and return the total."""
    return roll_die() + roll_die()


if __name__ == "__main__":
    total = roll_two_dice()
    print(f"You rolled a total of {total}")
