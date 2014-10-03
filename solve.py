import sys
import string
from Queue import Queue

"""
    # version 0.1

    ## Description

    - Several blocks are on a board
    - Each block is a grid on the board, and has a color and a facing directions
    - Destination block is a grid on the board, and has a color
    - Users are expected to move blocks to destinations with the same color
    - In each move, a user can choose a color, and the color block will move 1 step towards its facing direction

    - Portal: are grid that transit blocks, when a block enter a portal grid, it will come out from another portal grid
    - Direction changer: a grid that has a direction, when a block enters a changer grid, the block's facing direction changes

    ## Assumptions:

    - board size is 5x5
    - 1 block and 1 destination for each color
    - 0 or 2 portal

    ## possible grids:

    - SB: Facing (S)outh, (B)lue color block. Facing can be NEWS, and color can be any color
    - O: Portal
    - DB: (D)estination for (B)lue block. color can be any color.
    - CS: (C)hange facing to (S)outh, facing can be NEWS.
    - (empty string): empty grid

    ## Approach

    For each state, just enumerate possible move (pick a color to move), and does a breadth-first search.

    ## Tricks:

    - You can't move a block out of the board. If the edge is on the way, the block stays unmoved.
    - In a chain of moving (block pushes preceding blocks forward), if the forward most block can not move, the whole chain can not move.
    - The forward most block may be pushed into a portal. It should be correctly teleported to the other portal.
"""

PORTAL = 'O'
DIRECTIONS = 'NEWS'

class UnsolvableError(Exception):
    pass

class Solver:

    class Board:
        def __init__(self):
            self.board = [['' for j in range(5)] for i in range(5)]
            self.destinations = {}
            self.portals = []
            self.changer = []

        def set(self, i, j, thing):
            assert self.board[i][j] == '' # cannot set twice
            self.board[i][j] = thing
            if thing[0] == 'D': # A destination
                color = thing[1]
                assert color not in self.destinations
                self.destinations[color] = (i, j)
            elif thing[0] == 'O':
                self.portals.append((i, j))
            elif thing[0] == 'C':
                self.changer.append((i, j, thing[1]))
            else:
                assert False # should not come here


        def get(self, i, j):
            return self.board[i][j]

        def colors(self):
            return set(self.destinations.keys())

        def destination(self, c):
            return self.destinations[c]


    class Status:

        def __init__(self):
            self.pos = {}
            self.facing_map = {}

        def set(self, color, pos, facing):
            assert color not in self.pos
            self.pos[color] = pos
            self.facing_map[color] = facing

        def colors(self):
            return set(self.pos.keys())

        def facing(self, c):
            return self.facing_map[c]

        def position(self, c):
            return self.pos[c]

        def finished(self, board):
            for c in self.colors():
                if self.pos[c] != board.destination(c):
                    return False
            return True

        def __eq__(self, o):
            if self.colors() != o.colors():
                return False
            for c in self.colors():
                if self.position(c) != o.position(c):
                    return False
                if self.facing(c) != o.facing(c):
                    return False
            return True

        def __hash__(self):
            v = 7
            for c in self.colors():
                v = (v << 3) ^ hash(self.position(c)) + (hash(self.facing(c)) << 1)
            return v


    def __init__(self, board):
        assert len(board) == 5
        assert len(board[0]) == len(board[1]) == len(board[2]) == len(board[3]) == len(board[4]) == 5

        init_status = self.Status()

        self.board = self.Board()
        for i in range(5):
            for j in range(5):
                grid = board[i][j]
                if grid == '': # empty block
                    pass
                elif grid[0] in DIRECTIONS: # a color block
                    color = grid[1]
                    facing = grid[0]
                    init_status.set(color, (i, j), facing)
                elif grid[0] == 'O': # portal
                    self.board.set(i, j, grid)
                elif grid[0] == 'D': # destination
                    self.board.set(i, j, grid)
                elif grid[0] == 'C': # face changer
                    self.board.set(i, j, grid)
                else:
                    assert False # Should not come here

        assert init_status.colors() == self.board.colors()

        self.q = Queue()
        self.q.put(init_status)

        self.visited = set()
        self.visited.add(init_status)

        self.path = {}
        self.path[init_status] = ""

    def _move(self, status, color):
        pos = status.position(color)
        facing = status.facing(color)

        move_velocity_map = {
            'N': (-1, 0),
            'E': (0, 1),
            'W': (0, -1),
            'S': (1, 0)
        }
        move_velocity = move_velocity_map[facing]

        if 0 <= pos[0] + move_velocity[0] < 5 and 0 <= pos[1] + move_velocity[1] < 5:
            new_pos = (pos[0] + move_velocity[0], pos[1] + move_velocity[1])
        else:
            new_pos = (pos[0], pos[1])
        new_status = self.Status()
        new_status.set(color, new_pos, facing)
        for c in status.colors():
            if c != color:
                new_status.set(c, status.position(c), status.facing(c))


        # If there are other blocks on the way of the block we want to push, all of them will be pushed forward one step.
        # (TODO):So we first need to find out all the blocks will be push forward, put them into a stack


        # (TODO):move these blocks one by one, in reversed order.
        return new_status # (TODO): replace mock impl

    def solve(self):
        while not self.q.empty():
            status = self.q.get()
            if status.finished(self.board):
                return self.path[status]
            else:
                for next_move_color in status.colors():
                    new_status = self._move(status, next_move_color)
                    if new_status not in self.visited:
                        self.q.put(new_status)
                        self.visited.add(new_status)
                        self.path[new_status] = self.path[status] + next_move_color

        raise UnsolvableError()


if __name__ == '__main__':
    with open(sys.argv[1], 'r') as f:
        board = [map(lambda x:x.strip().upper(), f.readline().split(',')) for i in range(5)]
        solver = Solver(board)

        print solver.solve()

