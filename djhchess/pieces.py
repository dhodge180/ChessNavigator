# pieces.py

class Piece:
    """
    Represents a chess piece (or fairy piece) with colour, type, and symbols.
    Singletons per piece for fast identity and lookup.
    """

    _char_map = {}       # Maps internal_char -> Piece
    _user_char_map = {}  # Maps user_char -> Piece

    def __new__(cls, internal_char, user_char, long_name, colour, type_, base_type=None, rotation=0):
        if internal_char in cls._char_map:
            return cls._char_map[internal_char]

        self = super().__new__(cls)
        cls._char_map[internal_char] = self
        cls._user_char_map[user_char] = self
        return self

    def __init__(self, internal_char, user_char, long_name, colour, type_, base_type=None, rotation=0):
        # Avoid re-initializing singletons
        if hasattr(self, 'initialized'):
            return

        self.internal_char = internal_char  # For board storage (single char)
        self.user_char = user_char          # For display (1-3 chars allowed)
        self.long_name = long_name
        self.colour = colour                # 'white', 'black', 'neutral'
        self.type = type_                   # 'king', 'queen', etc.

        # For images
        self.base_type = base_type if base_type else type_
        self.rotation = rotation

        # Precomputed flags for speed
        self.is_pawn = (type_ == 'pawn')
        self.is_knight = (type_ == 'knight')
        self.is_bishop = (type_ == 'bishop')
        self.is_rook = (type_ == 'rook')
        self.is_queen = (type_ == 'queen')
        self.is_king = (type_ == 'king')
        self.is_grasshopper = (type_ == 'grasshopper')

        self.is_white = (colour == 'white')
        self.is_black = (colour == 'black')
        self.is_neutral = (colour == 'neutral')

        self.initialized = True

    def __repr__(self):
        return f"<{self.long_name} ({self.user_char}), rot={self.rotation}>"

    def image_filename(self, square_size):
        """
        Return the image filename for this piece, given the square size.
        E.g., 'bB_80px.png' for black bishop at 80px
        """
        if self.is_white:
            prefix = 'w'
        elif self.is_black:
            prefix = 'b'
        else:
            prefix = 'n'  # neutral

        piece_letter = self._type_to_letter(self.base_type)

        return f'{prefix}{piece_letter.upper()}_{square_size}px.png'

    def _type_to_letter(self, type_):
        """Maps standard types to letters for images.
        Used only for the image filenames
        """

        mapping = {
            'king': 'K',
            'queen': 'Q',
            'rook': 'R',
            'bishop': 'B',
            'knight': 'S',
            'pawn': 'P'
        }
        return mapping.get(type_, type_[0].upper())  # fallback to first letter

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


STANDARD_PIECES = {
    'WhiteKing':   { 'user_char': 'K', 'long_name': 'King',   'colour': 'white', 'type': 'king',   'rotation': 0 },
    'WhiteQueen':  { 'user_char': 'Q', 'long_name': 'Queen',  'colour': 'white', 'type': 'queen',  'rotation': 0 },
    'WhiteRook':   { 'user_char': 'R', 'long_name': 'Rook',   'colour': 'white', 'type': 'rook',   'rotation': 0 },
    'WhiteBishop': { 'user_char': 'B', 'long_name': 'Bishop', 'colour': 'white', 'type': 'bishop', 'rotation': 0 },
    'WhiteKnight': { 'user_char': 'S', 'long_name': 'Knight', 'colour': 'white', 'type': 'knight', 'rotation': 0 },
    'WhitePawn':   { 'user_char': 'P', 'long_name': 'Pawn',   'colour': 'white', 'type': 'pawn',   'rotation': 0 },

    'BlackKing':   { 'user_char': 'k', 'long_name': 'King',   'colour': 'black', 'type': 'king',   'rotation': 0 },
    'BlackQueen':  { 'user_char': 'q', 'long_name': 'Queen',  'colour': 'black', 'type': 'queen',  'rotation': 0 },
    'BlackRook':   { 'user_char': 'r', 'long_name': 'Rook',   'colour': 'black', 'type': 'rook',   'rotation': 0 },
    'BlackBishop': { 'user_char': 'b', 'long_name': 'Bishop', 'colour': 'black', 'type': 'bishop', 'rotation': 0 },
    'BlackKnight': { 'user_char': 's', 'long_name': 'Knight', 'colour': 'black', 'type': 'knight', 'rotation': 0 },
    'BlackPawn':   { 'user_char': 'p', 'long_name': 'Pawn',   'colour': 'black', 'type': 'pawn',   'rotation': 0 }
}

def create_extra_pieces(u_to_i_map, EXTRA_PIECES):
    """
    This creates the extra pieces defined below and used in the FENs provided.
    This function needs to be run once to initialize all the identified pieces.
    (In Windows the spawn in multiprocessing means it need to be run after the spawn too)
    EXTRA_PIECES is the full database of fairy pieces that it knows about
    EXTRA_PIECES was defined in the custom_piece.yml file
    Every piece present in any of the given FENs will search for a definition here
    Then Piece() is called to actually create the object, which will use the unicode name
    already assigned in the u_to_i_map
    """
    for user_char, internal_char in u_to_i_map.items():
        # Find the extra piece data by matching user_char
        for piece_data in EXTRA_PIECES.values():
            if piece_data['user_char'] == user_char:
                Piece(
                    internal_char=internal_char,
                    user_char=piece_data['user_char'],
                    long_name=piece_data['long_name'],
                    colour=piece_data['colour'],
                    type_=piece_data['type'],
                    base_type=piece_data.get('base_type'), # will return None if not present
                    rotation=piece_data.get('rotation', 0) # will return 0 by default
                )
                break

# This defines all the standard pieces, assuming they will never get other internal names

_load_standard_pieces()

# Extra pieces will only be loaded later when we know their internal names
