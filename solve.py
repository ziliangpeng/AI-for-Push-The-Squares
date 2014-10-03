

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
"""


