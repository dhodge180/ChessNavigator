from djhchess.pieces import Piece

EXTRA_PIECES = {
    'NeutralBishop': { 'user_char': '=b', 'long_name': 'Neutral Bishop', 'colour': 'neutral', 'type': 'bishop', 'rotation': 0 },
    'NeutralPawn':   { 'user_char': '=p', 'long_name': 'Neutral Pawn',   'colour': 'neutral', 'type': 'pawn',   'rotation': 0 },
    'NeutralRook':   { 'user_char': '=r', 'long_name': 'Neutral Rook',   'colour': 'neutral', 'type': 'rook',   'rotation': 0 },
    'NeutralQueen':  { 'user_char': '=q', 'long_name': 'Neutral Queen',  'colour': 'neutral', 'type': 'queen',  'rotation': 0 },
    'NeutralKing':   { 'user_char': '=k', 'long_name': 'Neutral King',   'colour': 'neutral', 'type': 'king',   'rotation': 0 },
    'NeutralKnight': { 'user_char': '=s', 'long_name': 'Neutral Knight', 'colour': 'neutral', 'type': 'knight', 'rotation': 0 },

    'BlackGrasshopper': { 'user_char': 'g', 'long_name': 'Grasshopper', 'colour': 'black', 'type': 'grasshopper', 'base_type': 'queen', 'rotation': 180 },
    'WhiteGrasshopper': { 'user_char': 'G', 'long_name': 'Grasshopper', 'colour': 'white', 'type': 'grasshopper', 'base_type': 'queen', 'rotation': 180 },

    'EastQueen': { 'user_char': '.eq', 'long_name': 'East Queen', 'colour': 'black', 'type': 'Bob', 'base_type': 'queen', 'rotation': 90 },
    'BlackSideRook' : { 'user_char': '.l1', 'long_name': 'Side Rook', 'colour': 'black', 'type': 'rook', 'base_type': 'rook', 'rotation': 90 },
    'WhiteSideRook' : { 'user_char': '.L1', 'long_name': 'Side Rook', 'colour': 'white', 'type': 'rook', 'base_type': 'rook', 'rotation': 90 },

    # If you wish to use 'N' and 'n' in your fens for knights just ensure these next two lines are uncommented
    # This creates two 'fairy' pieces called 'N' and 'n' which look like knights!
    'WhiteNKnight': { 'user_char': 'N', 'long_name': 'White Knight', 'colour': 'white', 'type': 'knight', 'rotation': 0 },
    'BlackNKnight': { 'user_char': 'n', 'long_name': 'Black Knight', 'colour': 'black', 'type': 'knight', 'rotation': 0 },

}

def create_extra_pieces(u_to_i_map):
    """
    This creates the extra pieces defined below and used in the FENs provided.
    This function needs to be fun once to initialize all the identified pieces.
    (In Windows the spawn in multiprocessing means it need to be run after the spawn too)
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