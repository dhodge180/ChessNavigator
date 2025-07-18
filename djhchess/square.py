# square.py

"""
Square module for chess programming.

Provides a singleton Square system where each square is unique,
precomputed, and can be accessed by:
    - 0–63 index
    - Algebraic notation (e.g., "e4")
    - 2D coordinate (row, col)

Usage:
    from square import Square

    e4 = Square.get(alg="e4")
    print(e4.index)    # 28
    print(e4.coord)    # (3, 4)
    print(e4.alg)      # e4

    # Identity comparison is fast
    assert Square.get(alg="e4") is e4
"""

class Square:
    """
    Represents a chessboard square as a singleton.
    """

    files = 'abcdefgh'

    _squares = {}  # Singleton instances

    # Lookup tables
    index_to_alg = {}
    alg_to_index = {}
    index_to_coord = {}
    coord_to_index = {}

    def _init_internal(self, index):
        """
        Private initializer. Use Square.get() instead.
        """
        self.index = index
        self.coord = Square.index_to_coord[index]
        self.alg = Square.index_to_alg[index]

    @classmethod
    def get(cls, index=None, coord=None, alg=None):
        """
        Retrieves the singleton Square object for the given input.
        Provide either index, coord, or alg (one of them).
        """
        if index is not None:
            return cls._squares[index]
        elif coord is not None:
            return cls._squares[cls.coord_to_index[coord]]
        elif alg is not None:
            return cls._squares[cls.alg_to_index[alg]]
        else:
            raise ValueError("Must provide index, coord, or alg to Square.get()")

    def __repr__(self):
        return f"Square({self.alg})"


# -------------------------------
# Initialize singleton squares and lookup tables

for index in range(64):
    row, col = divmod(index, 8)
    rank = 8 - row
    alg = f"{Square.files[col]}{rank}"
    coord = (row, col)

    Square.index_to_alg[index] = alg
    Square.alg_to_index[alg] = index
    Square.index_to_coord[index] = coord
    Square.coord_to_index[coord] = index

    sq = Square.__new__(Square)          # Bypass __init__
    sq._init_internal(index)              # Use private init
    Square._squares[index] = sq
