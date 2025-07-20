# pieces.py

class Piece:
    """
    Represents a chess piece (or fairy piece) with colour, type, and symbols.
    Singletons per piece for fast identity and lookup.
    """

    _char_map = {}       # Maps internal_char -> Piece
    _user_char_map = {}  # Maps user_char -> Piece

    def __new__(cls, internal_char, user_char, long_name, colour, type_):
        if internal_char in cls._char_map:
            return cls._char_map[internal_char]

        self = super().__new__(cls)
        cls._char_map[internal_char] = self
        cls._user_char_map[user_char] = self
        return self

    def __init__(self, internal_char, user_char, long_name, colour, type_):
        # Avoid re-initializing singletons
        if hasattr(self, 'initialized'):
            return

        self.internal_char = internal_char  # For board storage (single char)
        self.user_char = user_char          # For display (1-3 chars allowed)
        self.long_name = long_name
        self.colour = colour                # 'white', 'black', 'neutral'
        self.type = type_                   # 'king', 'queen', etc.

        # Precomputed flags for speed
        self.is_pawn = (type_ == 'pawn')
        self.is_knight = (type_ == 'knight')
        self.is_bishop = (type_ == 'bishop')
        self.is_rook = (type_ == 'rook')
        self.is_queen = (type_ == 'queen')
        self.is_king = (type_ == 'king')

        self.is_white = (colour == 'white')
        self.is_black = (colour == 'black')
        self.is_neutral = (colour == 'neutral')

        self.initialized = True

    def __repr__(self):
        return f"<{self.long_name} ({self.user_char})>"

    @classmethod
    def get(cls, char):
        """Fast lookup from internal_char."""
        return cls._char_map.get(char)

    @classmethod
    def get_user(cls, user_char):
        """Fast lookup from user display character."""
        return cls._user_char_map.get(user_char)

    @classmethod
    def all(cls):
        """Return all registered pieces."""
        return list(cls._char_map.values())


class PieceBox:
    """
    Keeps track of all pieces used in a given ChessPosition or composition.
    """

    def __init__(self):
        self.used_pieces = set()

    def add(self, piece):
        self.used_pieces.add(piece)

    def __iter__(self):
        return iter(self.used_pieces)

    def __contains__(self, piece):
        return piece in self.used_pieces

    def __repr__(self):
        pieces = ", ".join(sorted(p.user_char for p in self.used_pieces))
        return f"<PieceBox: {pieces}>"

# --------- Automatically load standard chess pieces ---------

def _load_standard_pieces():
    # White pieces
    Piece('K', 'K', 'King', 'white', 'king')
    Piece('Q', 'Q', 'Queen', 'white', 'queen')
    Piece('R', 'R', 'Rook', 'white', 'rook')
    Piece('B', 'B', 'Bishop', 'white', 'bishop')
    Piece('S', 'S', 'Knight', 'white', 'knight')
    Piece('P', 'P', 'Pawn', 'white', 'pawn')

    # Black pieces
    Piece('k', 'k', 'King', 'black', 'king')
    Piece('q', 'q', 'Queen', 'black', 'queen')
    Piece('r', 'r', 'Rook', 'black', 'rook')
    Piece('b', 'b', 'Bishop', 'black', 'bishop')
    Piece('s', 's', 'Knight', 'black', 'knight')
    Piece('p', 'p', 'Pawn', 'black', 'pawn')

    # Neutral examples (optional)
    Piece('z', '=b', 'Neutral Bishop', 'neutral', 'bishop')
    Piece('y', '=p', 'Neutral Pawn', 'neutral', 'pawn')

_load_standard_pieces()
