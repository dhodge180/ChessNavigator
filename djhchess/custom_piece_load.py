import os
import yaml

CUSTOM_PIECES_FILE = "custom_pieces.yml"

# Default to be set if no YML file exists
DEFAULT_PIECES = {
    'NeutralBishop': { 'user_char': '=b', 'long_name': 'Neutral Bishop', 'colour': 'neutral', 'type': 'bishop', 'rotation': 0 },
    'NeutralPawn':   { 'user_char': '=p', 'long_name': 'Neutral Pawn',   'colour': 'neutral', 'type': 'pawn',   'rotation': 0 },
    'NeutralRook':   { 'user_char': '=r', 'long_name': 'Neutral Rook',   'colour': 'neutral', 'type': 'rook',   'rotation': 0 },
    'NeutralQueen':  { 'user_char': '=q', 'long_name': 'Neutral Queen',  'colour': 'neutral', 'type': 'queen',  'rotation': 0 },
    'NeutralKing':   { 'user_char': '=k', 'long_name': 'Neutral King',   'colour': 'neutral', 'type': 'king',   'rotation': 0 },
    'NeutralKnight': { 'user_char': '=s', 'long_name': 'Neutral Knight', 'colour': 'neutral', 'type': 'knight', 'rotation': 0 },

    'BlackGrasshopper': { 'user_char': 'g', 'long_name': 'Grasshopper', 'colour': 'black', 'type': 'grasshopper', 'base_type': 'queen', 'rotation': 180 },
    'WhiteGrasshopper': { 'user_char': 'G', 'long_name': 'Grasshopper', 'colour': 'white', 'type': 'grasshopper', 'base_type': 'queen', 'rotation': 180 },

    'WhiteNKnight': { 'user_char': 'N', 'long_name': 'White Knight', 'colour': 'white', 'type': 'knight', 'rotation': 0 },
    'BlackNKnight': { 'user_char': 'n', 'long_name': 'Black Knight', 'colour': 'black', 'type': 'knight', 'rotation': 0 },
}

YAML_HEADER = """# ==============================
# Custom Piece Definitions
# ------------------------------
# - user_char: The character used in FEN strings. (Use quotes if only numbers)
# - long_name: Display name of the piece.
# - colour: "white", "black", or "neutral".
# - type: The piece type (pawn, rook, etc.) for logic
# - base_type: Piece to use as base for image and rotation.
# - rotation: Rotation of the image in degrees (clockwise).
# ==============================
"""

def write_default_yaml():
    with open(CUSTOM_PIECES_FILE, "w", encoding="utf-8") as f:
        f.write(YAML_HEADER)

        keys = list(DEFAULT_PIECES.keys())
        first_key = keys[0]
        first_piece = DEFAULT_PIECES[first_key]

        # First piece with comments
        f.write(f"{first_key}:\n")
        f.write(f"  user_char: '{first_piece['user_char']}' # The character used in FEN strings\n")
        f.write(f"  long_name: {first_piece['long_name']}  # Display name of the piece\n")
        f.write(f"  colour: {first_piece['colour']}  # white, black, or neutral\n")
        f.write(f"  type: {first_piece['type']}  # The piece type (pawn, bishop, knight, rook, queen or king)\n")

        # Optional rotation
        if 'rotation' in first_piece:
            f.write(f"  rotation: {first_piece['rotation']}  # (Optional) Rotation of the image in degrees\n")
        else:
            f.write(f"  # rotation: 0  # (Optional) Rotation of the image in degrees\n")

        # Optional base_type
        if 'base_type' in first_piece:
            f.write(f"  base_type: {first_piece['base_type']}  # (Optional) Piece to use as base for image and rotation\n")
        else:
            f.write(f"  # base_type: queen  # (Optional) Piece to use as base for image and rotation\n")

        f.write("\n")  # <-- blank line after first piece

        # Rest of the pieces with spacing between them
        for k in keys[1:]:
            piece = DEFAULT_PIECES[k]
            yaml.safe_dump({k: piece}, f, sort_keys=False, allow_unicode=True)
            f.write("\n")  # <-- blank line after each piece

if os.path.exists(CUSTOM_PIECES_FILE):
    try:
        with open(CUSTOM_PIECES_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if isinstance(data, dict):
                EXTRA_PIECES = data
            else:
                EXTRA_PIECES = DEFAULT_PIECES
    except yaml.YAMLError:
        EXTRA_PIECES = DEFAULT_PIECES
else:
    write_default_yaml()
    EXTRA_PIECES = DEFAULT_PIECES