"""
    Author: Ziliang Peng
    Date: 07 Oct, 2014
"""

import sys
import string
from Queue import Queue
import re
from collections import defaultdict

"""
    # version 0.51

    ## Description

    - Several blocks are on a board
    - Each block is a grid on the board, and has a color and a facing directions
    - Destination block is a grid on the board, and has a color
    - Users are expected to move blocks to destinations with the same color
    - In each move, a user can choose a color, and the color block will move 1 step towards its facing direction
    - (**NEW 0.2**) Starting from level 27, the rule change that blocks of same color will move simultaneously, thus program needs to be adjust.
    - (**NEW 0.3**) obstacles grid may exist on the board
    - (**NEW 0.4**) board size can be arbitrary


    - Portal: are grid that transit blocks, when a block enter a portal grid, it will come out from another portal grid
    - Direction changer: a grid that has a direction, when a block enters a changer grid, the block's facing direction changes

    ## Assumptions:

    - There can be several blocks and several destinations of a color, but the number should match
    - There can be multiple types of portals, 2 portals for each type.

    ## possible grids:

    - SB: Facing (S)outh, (B)lue color block. Facing can be NEWS, and color can be any color
    - O: Portal
    - DB: (D)estination for (B)lue block. color can be any color.
    - CS: (C)hange facing to (S)outh, facing can be NEWS.
    - (empty string): empty grid
    - X: obstacles

    ## Approach

    For each state, just enumerate possible move (pick a color to move), and does a breadth-first search.

    ## Tricks:

    - You can't move a block out of the board. If the edge is on the way, the block stays unmoved.
    - In a chain of moving (block pushes preceding blocks forward), if the forward most block can not move, the whole chain can not move.
    - The forward most block may be pushed into a portal. It should be correctly teleported to the other portal.

    - (**NEW 0.2**) If a block is pushed as a chain, not the mover, the other one with same color will not move, thus the push chain will not grow into a tree.
    - (**NEW 0.2**) if one block is obstacled, the other block of the same color can still move.
"""

PORTAL_PREFIX = 'O'
DIRECTIONS = 'NEWS'
CHANGER_PREFIX = 'C'
DESTINATION_PREFIX = 'D'
OBSTACLE = 'X'

VELOCITIES = {
            'N': (-1, 0),
            'E': (0, 1),
            'W': (0, -1),
            'S': (1, 0)
        }

class UnsolvableError(Exception):
    pass

class Solver:

    class Board:
        def __init__(self, board_size):
            # In input, empty are '' for faster key-typing, in Board representation empty is '.' for better index handling.
            # (TODO): This hack may be fixed after project is finished
            self.board = [['.' for j in range(board_size)] for i in range(board_size)]
            self.destinations_map = defaultdict(list)
            self.portals = defaultdict(list)
            self.obstacles = []
            self.changer = []

        def height(self):
            return len(self.board)

        def width(self):
            return len(self.board[0])

        def set(self, i, j, thing):
            assert self.board[i][j] == '.' # cannot set twice
            self.board[i][j] = thing
            if thing[0] == DESTINATION_PREFIX: # A destination
                color = thing[1]
                self.destinations_map[color].append((i, j))
            elif thing[0] == PORTAL_PREFIX:
                portal_name = thing[1:]
                self.portals[portal_name].append((i, j))
            elif thing[0] == OBSTACLE:
                self.obstacles.append((i, j))
            elif thing[0] == CHANGER_PREFIX:
                self.changer.append((i, j, thing[1]))
            else:
                assert False # should not come here

        def get(self, i, j):
            return self.board[i][j]

        def colors(self):
            return set(self.destinations_map.keys())

        def destinations(self, c):
            return set(self.destinations_map[c])

        def is_portal(self, pos):
            return self.board[pos[0]][pos[1]][0] == PORTAL_PREFIX

        def is_obstacle(self, pos):
            return self.board[pos[0]][pos[1]] == OBSTACLE

        def get_another_portal(self, pos):
            for portal_name in self.portals.keys():
                portals = self.portals[portal_name]
                if pos == portals[0]:
                    return portals[1]
                if pos == portals[1]:
                    return portals[0]
            
            raise ValueError()

        def get_facing_change_by_position(self, pos):
            grid = self.board[pos[0]][pos[1]]
            if grid[0] == CHANGER_PREFIX:
                return grid[1]
            else:
                return None


    class Status:

        def __init__(self):
            self.pos = defaultdict(list)
            self.facing_map = {} # since there are several blocks of a color, this changes to map pos -> facing

        def set(self, color, pos, facing):
            self.pos[color].append(pos)
            self.facing_map[pos] = facing

        def colors(self):
            return set(self.pos.keys())

        def facing(self, pos):
            return self.facing_map[pos]

        def positions(self, c):
            return set(self.pos[c])

        def finished(self, board):
            for c in self.colors():
                if self.positions(c) != board.destinations(c):
                    return False
            return True

        def get_color_from_position(self, pos):
            for c in self.pos.keys():
                if pos in self.positions(c):
                    return c
            return None

        def __eq__(self, o):
            if self.colors() != o.colors():
                return False
            for c in self.colors():
                if self.positions(c) != o.positions(c):
                    return False
                for pos in self.positions(c):
                    if self.facing(pos) != o.facing(pos):
                        return False
            return True

        def __hash__(self):
            v = 7
            for c in self.colors():
                for pos in sorted(self.positions(c)):
                    v = (v << 3) ^ hash(pos) + (hash(self.facing(pos)) << 1)
            return v


    def __init__(self, board):
        assert len(board[0]) == len(board[1]) == len(board[2]) == len(board[3]) == len(board[4])

        init_status = self.Status()

        self.board = self.Board(len(board))
        for i in range(len(board)):
            for j in range(len(board[i])):
                grid = board[i][j]
                if grid == '': # empty block
                    pass
                elif grid[0] in DIRECTIONS: # a color block
                    color = grid[1]
                    facing = grid[0]
                    init_status.set(color, (i, j), facing)
                elif grid[0] == PORTAL_PREFIX: # portal
                    self.board.set(i, j, grid)
                elif grid[0] == OBSTACLE: # obstacle
                    self.board.set(i, j, grid)
                elif grid[0] == DESTINATION_PREFIX: # destination
                    self.board.set(i, j, grid)
                elif grid[0] == CHANGER_PREFIX: # face changer
                    self.board.set(i, j, grid)
                else:
                    assert False # Should not come here

        assert self.validate(self.board, init_status)

        self.q = Queue()
        self.q.put(init_status)

        self.visited = set()
        self.visited.add(init_status)

        self.path = {}
        self.path[init_status] = ""

    def validate(self, board, status):
        if board.colors() != status.colors():
            return False
        for c in board.colors():
            if len(board.destinations(c)) != len(status.positions(c)):
                return False
        return True

    def _push_forward(self, pos, towards, original_status, new_status, pos_in_chain, pushed_grids, original_color):
        if pos in pos_in_chain: # I can move it if it's in a loop. Actually I'm guaranteed to be able to.
            return True
        pos_in_chain.add(pos)
        # If there are other blocks on the way of the block we want to push, all of them will be pushed forward one step.
        # So we first need to find out all the blocks will be push forward, put them into a stack

        velocity = VELOCITIES[towards]
        color = original_status.get_color_from_position(pos)
        facing = original_status.facing(pos)

        target_pos = (pos[0] + velocity[0], pos[1] + velocity[1])

        if 0 <= target_pos[0] < self.board.height() and 0 <= target_pos[1] < self.board.width():
            if self.board.is_portal(target_pos): # Teleport if meets portal
                other_portal = self.board.get_another_portal(target_pos)
                target_pos = (other_portal[0] + velocity[0], other_portal[1] + velocity[1])

            if original_status.get_color_from_position(target_pos) and \
                original_status.get_color_from_position(target_pos) not in pushed_grids: # there is a preceding block, and not already moved
                preceding_exist = True

                # to fix #5, if a block of the same color in the chain wants to move to a different direction, let it.
                if original_status.get_color_from_position(target_pos) == color:
                    new_towards = original_status.facing(target_pos)
                else:
                    new_towards = towards
                # but of course the new direction can't be opposite of the original direction.
                if (VELOCITIES[towards][0] + VELOCITIES[new_towards][0], VELOCITIES[towards][1] + VELOCITIES[new_towards][1]) == (0, 0):
                    preceding_removed = False
                else:
                    preceding_removed = self._push_forward(target_pos, new_towards, original_status, new_status, pos_in_chain, pushed_grids, original_color)
            elif self.board.is_obstacle(target_pos): # there is an obstacle
                preceding_exist = True
                preceding_removed = False
            else: # nothing in the way
                preceding_exist = False

            if not preceding_exist or preceding_exist and preceding_removed: # removed obstacles, now can move me
                # see if facing changed
                new_facing = self.board.get_facing_change_by_position(target_pos) or facing
                new_status.set(color, target_pos, new_facing)
                pushed_grids.add(pos)
                return True
            else: # preceding failed, unmove
                new_status.set(color, pos, facing)
                return False
        else: # out of bound, unmove.
            new_status.set(color, pos, facing)
            return False

    def _move(self, status, color):
        positions = status.positions(color)
        new_status = self.Status()
        pos_in_chain = set()
        pushed_grids = set() # to fix #1

        # (HACK): This version (0.2) push the blocks one by one, with the assumption that no 2 blocks will be interested in pushing a same block.
        # This may break with some data, but because its uncertain what the rule is for those situations, the algorithm just leave it for now.
        # This will be fixed if it ever breaks.
        for pos in positions:
            if pos not in pos_in_chain:
                facing = status.facing(pos)
                self._push_forward(pos, facing, status, new_status, pos_in_chain, pushed_grids, color)

        # copy all the unmoved blocks
        for c in status.colors():
            for pos in status.positions(c):
                if pos not in pos_in_chain:
                    new_status.set(c, pos, status.facing(pos))

        return new_status

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
        lines = f.readlines()

        board = [map(lambda x:x.strip().upper(), line.split(',')) for line in lines][:-1] # omit the ending empty line
        solver = Solver(board)

        solution = solver.solve()
        print ' '.join(re.findall('\w{1,4}', solution))

