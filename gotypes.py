# -*- coding: utf-8 -*-

import enum
from collections import namedtuple

# Player, Point, classes are all plain data types.
# they don’t contain any game logic


class Player(enum.Enum):
    black = 1
    white = 2

    @property  # property is a way to implement setter and getter from var
    def other(self):
        return Player.black if self == Player.white else Player.white


class Point(namedtuple('Point', 'row col')):
    # /* thanks to named tuples my neighbors array will be:
    # [Point(row=0, col=2), Point(row=2, col=2),
    # Point(row=1, col=1), Point(row=1, col=3)]
    def neighbors(self):
        return [
            Point(self.row - 1, self.col),
            Point(self.row + 1, self.col),
            Point(self.row, self.col - 1),
            Point(self.row, self.col + 1),
        ]


a = Point(1, 2)
b = a.neighbors()
print(b)

white = Player(1)
print(white.other)

