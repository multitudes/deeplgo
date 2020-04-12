# -*- coding: utf-8 -*-
import copy
from gotypes import Player


class Move():
    # clients generally won’t call the Move constructor directly
    # Instead, you usually call Move.play,
    # Move.pass_turn, or Move.resign to construct an instance of a move.
    def __init__(self, point=None, is_pass=False, is_resign=False):
        # Any action a player can play on a turn—is_play, is_pass,
        # or is_resign—
        assert (point is not None) ^ is_pass ^ is_resign
        self.point = point
        self.is_play = (self.point is not None)
        self.is_pass = is_pass
        self.is_resign = is_resign

    # This move places a stone on the board.
    @classmethod
    def play(cls, point):
        return Move(point=point)

    # This move passes.
    @classmethod
    def pass_turn(cls):
        return Move(is_pass=True)

    # This move resigns the current game.
    @classmethod
    def resign(cls):
        return Move(is_resign=True)


class GoString():
    # Tracking connected groups of stones in Go: strings
    # you’ll keep track of groups of connected stones of the same color and
    # their liberties at the same time
    # Go strings are a chain of connected stones of the same color.
    def __init__(self, color, stones, liberties):
        self.color = color
        self.stones = set(stones)
        self.liberties = set(liberties)

    def remove_liberty(self, point):
        self.liberties.remove(point)

    def add_liberty(self, point):
        self.liberties.add(point)

    # Returns a new Go string containing all stones in both strings
    # called when a player connects two of its groups by placing a stone
    def merged_with(self, go_string):
        assert go_string.color == self.color
        combined_stones = self.stones | go_string.stones
        return GoString(
            self.color,
            combined_stones,
            (self.liberties | go_string.liberties) - combined_stones)

    # GoString directly tracks its own liberties,
    # and you can access the number of liberties at any point by calling

    @property
    def num_liberties(self, other):
        return isinstance(other, GoString) and \
            self.stones == other.stones and \
            self.liberties == other.liberties

    def __eq__(self, other):
        return isinstance(other, GoString) and self.color == other.color and \
            self.stones == other.stones and self.liberties == other.liberties


class Board():
    def __init__(self, num_rows, num_cols):
        self.num_rows = num_rows
        self.num_cols = num_cols
        # the private variable _grid, is a dictionary you use to store strings
        # of stones
        self._grid = {}

    def place_Stone(self, player, point):
        # you first have to inspect all neighboring stones of a given point
        # for liberties.
        # Check if in the boundary of the board-
        # is_on_grid is a util method
        assert self.is_on_grid(point)
        # check the place is free for the move
        assert self._grid.get(point) is None
        adjacent_same_color = []
        adjacent_opposite_color = []
        liberties = []
        # check all my neighbors. Update my liberties
        for neighbor in point.neighbors:
            # if the neighbor is not on the board boundaries continue
            if not self.is_on_grid(neighbor):
                continue
            # get the go_string of my neighbor looking in my _grid dict
            neighbor_string = self._grid.get(neighbor)
            # if my neighbour not part of a go_string
            # I get a liberty
            if neighbor_string is None:
                liberties.append(neighbor)
            # else I check if neighbor is my color and if it is
            # I append his string to my adjacent_same_color array
            elif neighbor_string.color == player:
                if neighbor_string not in adjacent_same_color:
                    adjacent_same_color.append(neighbor_string)
            else:
                # my neighbor is not None and not my color so I
                # append to the adjacent_opposite_color
                if neighbor_string not in adjacent_opposite_color:
                    adjacent_opposite_color.append(neighbor_string)
        # init- GoString takes a player a set of points and a set of liberties
        new_string = GoString(player, [point], liberties)
        # now I loop on what I collected in the previous step and merge
        for same_color_string in adjacent_same_color:
            new_string = new_string.merged_with(same_color_string)
        # after merging I go through everypoint in my go_string
        # and add it to my _grid dict as key
        for new_string_point in new_string.stones:
            self._grid[new_string_point] = new_string
        # Here I check what I collected previously
        # adjacent_opposite_color and if any of their liberties
        # is zero I remove them from the board! remove_string is
        # defined below
        for other_color_string in adjacent_opposite_color:
            if other_color_string.num_liberties == 0:
                self._remove_string(other_color_string)

    def _remove_string(self, string):
        # fairly simple but other stones might gain liberties when removing an
        # enemy string - checking every stone
        for point in string.stones:
            # and checking every neighbor
            for neighbor in point.neighbors():
                # _grid is a dict, get is the method to get the gostring value
                neighbor_string = self._grid.get(neighbor)
                if neighbor_string is None:
                    continue
                # if our neighbor string not in the string we want to take out
                # he will get a liberty!
                if neighbor_string is not string:
                    neighbor_string.add_liberty(point)
            # after all this I reset the _grid dict for the current point
            self._grid[point] = None

    def is_on_grid(self, point):
        return 1 <= point.row <= self.num_rows and \
            1 <= point.col <= self.num_cols

    def get(self, point):
        # Returns the content of a point on the board:
        # a Player if a stone is on that point, or else None
        string = self._grid.get(point)
        if string is None:
            return None
        return string.color

    # Returns the entire string of stones at a point:
    # a GoString if a stone is on that point, or else None
    # this returns the string of stones associated with a given point
    def get_go_string(self, point):
        string = self._grid.get(point)
        if string is None:
            return None
        return string


# GameState capturing the current state of a game.
# game state knows about:
# the board position
# the next player
# the previous game state
# and the last move that has been played


class GameState():
    def __init__(self, board, next_Player, previous, move):
        self.board = board
        self.next_Player = next_Player
        self.previous_state = previous
        self.last_move = move

    # a move if play will create a new gamestate keeping the last one,
    # like a tree!
    def apply_move(self, move):
        if move.is_play:
            next_board = copy.deepcopy(self.board)
            next_board.place_Stone(self.next_Player, move.point)
        else:
            next_board = self.board
        return GameState(next_board, self.next_Player.other, self, move)

    @classmethod
    def new_game(cls, board_size):
        if isinstance(board_size, int):
            board_size = (board_size, board_size)
            board = Board(*board_size)
        return GameState(board, Player.black, None, None)

    def is_over(self):
        # game is over if the last two moves are a pass or the last move
        # is resign
        if self.last_move is None:
            return False
        if self.last_move.is_resign:
            return True
        second_last_move = self.previous_state.last_move
        if second_last_move is None:
            return False
        return self.last_move.is_pass and second_last_move.is_pass


# write code to identify which moves are legal.
# Confirm that the point you want to play is empty
# Check that the move isn’t a self­capture.
# Confirm that the move doesn’t violate the ko rule.

