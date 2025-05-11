import os
import json
import re
import unicodedata


#Provides these core functions
#load_existing_map(MAPFILE)
#u_to_i(token, user_to_int_map)
#i_to_u(token, int_to_user_map)
#load_and_update_mappings(fens, MAPFILE)

MAP_FILE = "piece_map.json"

def generate_unicode_symbols(n=512):
    reserved = set("PSBRQKpsbrqk12345678/")
    symbols = []
    ranges = [
        (0x0250, 0x02AF),  # Phonetic Extensions
        (0x0370, 0x03FF),  # Greek and Coptic
        (0x0400, 0x04FF),  # Cyrillic
        (0x1D00, 0x1D7F),  # Phonetic Extensions Supplement
        (0x2100, 0x214F),  # Letterlike Symbols
    ]

    for start, end in ranges:
        for cp in range(start, end):
            ch = chr(cp)
            name = unicodedata.name(ch, "")
            if ch not in reserved and ch.isprintable() and (
                "LETTER" in name or "SYMBOL" in name or "SCRIPT" in name
            ):
                symbols.append(ch)
            if len(symbols) >= n:
                return symbols
    return symbols

def default_predefined_blocks():
    return {
        "neutral": ["=p", "=b", "=s", "=r", "=q", "=k"],
    }

def load_predefined_blocks(filename="fairy_piece_blocks.json"):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return default_predefined_blocks()

def validate_board_structure(board_part):
    """
    Validates that the board part of a FEN string:
    - Has exactly 8 rows
    - Each row must represent 8 squares (pieces or empty squares represented by digits)
    - Rows are separated by '/' except the last one
    """
    rows = board_part.strip().split('/')
    
    if len(rows) != 8:
        print("❌ FEN invalid: Must have exactly 8 rows.")
        return False

    for i, row in enumerate(rows):
        square_count = 0

        for ch in row:
            if ch.isdigit():  # Add the number of empty squares represented by digits
                square_count += int(ch)
            elif len(ch) == 1:  # Each piece or custom symbol counts as 1 square
                square_count += 1
            else:
                print(f"❌ Invalid character '{ch}' in row {i+1}.")
                return False

        if square_count != 8:
            print(f"❌ Row {i+1} does not contain exactly 8 squares (got {square_count}).")
            return False

    return True

def extract_tokens_from_fens(fen_list):
    """
    Given a list of FEN strings, extract tokens from each using extract_custom_tokens,
    returning a list where each element corresponds to the tokens from one FEN.
    """
    return [single_extract_custom_tokens(fen) for fen in fen_list]

def single_extract_custom_tokens(fen):
    standard_pieces = set("KQRBSPkqrbsp")

    matchers = [
        (re.compile(r'^\.([A-Za-z0-9]{2})$'), '.'),  # .xy-style tokens
        (re.compile(r'^([A-Za-z])$'), ''),  # single-letter tokens
    ]

    board_part, _ = split_epd_from_fen(fen)
    found = set()

    # optional = (i.e. neutral_prefix)
    # then either . followed by 2 alphanumerics
    # or no dot, then just an alpha
    tokens = re.findall(r'(=?\.[A-Za-z0-9]{2}|=?[A-Za-z])', board_part)
    #print(tokens)

    for token in tokens:
        is_prefixed = token.startswith('=')
        core = token[1:] if is_prefixed else token

        for pattern, prefix in matchers:
            match = pattern.match(core)
            if match:
                content = match.group(1)

                # Handle single-letter tokens
                if prefix == '' and not is_prefixed:
                    if content not in standard_pieces:
                        found.add(content.lower())  # Custom single-letter lowercase
                        found.add(content.upper())  # Custom single-letter uppercase
                    # elif content in standard_pieces:
                    # just a normal piece no need to add to the content
                else:
                    final_token = ('=' if is_prefixed else '') + prefix + content
                    if is_prefixed:
                        found.add(final_token) # Neutral so no need for cases
                    else:
                        found.add(final_token.lower()) # Not neutral so want both cases
                        found.add(final_token.upper()) # Not neutral so want both cases
                break  # Stop after first match

    return sorted(found)

def expand_tokens_with_blocks(tokens, block_data):
    expanded = set(tokens)
    for block_tokens in block_data.values():
        if any(t in tokens for t in block_tokens):
            expanded.update(block_tokens)
    return sorted(expanded)

def load_existing_map(filename=MAP_FILE):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_map(mapping, filename=MAP_FILE):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

def get_next_available_symbols(used, pool):
    return [s for s in pool if s not in used]

def split_epd_from_fen(fen):
    fields = fen.strip().split(" ", 5)
    if len(fields) < 1:
        raise ValueError("Invalid FEN: missing fields")

    return fields[0], fields[1:]

def convert_fen_board_section(fen, mapping):
    """Convert only the board layout part of the FEN using the provided mapping."""

    board, fen_tail = split_epd_from_fen(fen)

    # Replace longer tokens first (e.g., .g1 before .g)
    sorted_tokens = sorted(mapping.keys(), key=len, reverse=True)
    for token in sorted_tokens:
        board = board.replace(token, mapping[token])

    return " ".join([board] + fen_tail)

def load_and_update_mapping(fens, map_file=MAP_FILE):
    """
        Loads an existing mapping of user-defined chess pieces to internal symbols, processes FEN strings to
        extract tokens representing chess pieces, and updates the mapping with any missing tokens using available
        internal symbols.

        This function performs the following steps:
        1. Generates a pool of available Unicode symbols to map to custom tokens.
        2. Loads the existing user-to-internal mapping from a specified file (or default map file).
        3. Extracts raw tokens from the provided FEN strings.
        4. Expands the extracted tokens using predefined block data (e.g., for custom chess pieces).
        5. Identifies any tokens that are missing from the user-to-internal mapping.
        6. Assigns available Unicode symbols to the missing tokens, ensuring there are enough symbols available.
        7. Updates the user-to-internal mapping and saves the updated mapping to the specified map file.
        8. Returns the updated mappings (user-to-internal and internal-to-user) and the list of expanded custom tokens.

        Args:
            fens (list): A list of FEN strings representing the current board state(s) to process.
            map_file (str, optional): The file path where the user-to-internal mapping is stored. Defaults to `MAP_FILE`.

        Returns:
            tuple: A tuple containing:
                - user_to_internal (dict): A dictionary mapping user-defined tokens (e.g., custom pieces) to internal symbols.
                - internal_to_user (dict): A dictionary mapping internal symbols back to user-defined tokens.
                - custom_tokens (list): A list of expanded tokens (after processing FENs and applying block data).

        Raises:
            RuntimeError: If there are not enough available internal symbols to assign to the missing tokens.

        Example:
            user_to_internal, internal_to_user, custom_tokens = load_and_update_mapping(fens)
        """
    symbol_pool = generate_unicode_symbols()
    user_to_internal = load_existing_map(map_file)
    existing_symbols = set(user_to_internal.values())

    raw_tokens = extract_tokens_from_fens(fens)
    block_data = load_predefined_blocks()
    custom_tokens = [expand_tokens_with_blocks(tokens, block_data) for tokens in raw_tokens]

    # Collect missing tokens
    missing_tokens = set(token for tokens in custom_tokens for token in tokens if token not in user_to_internal)

    if missing_tokens:
        available_symbols = get_next_available_symbols(existing_symbols, symbol_pool)
        if len(available_symbols) < len(missing_tokens):
            raise RuntimeError("Not enough internal symbols left for new pieces.")
        for token, symbol in zip(missing_tokens, available_symbols):
            user_to_internal[token] = symbol
        save_map(user_to_internal, map_file)

    internal_to_user = {v: k for k, v in user_to_internal.items()}
    return user_to_internal, internal_to_user, custom_tokens

def u_to_i(token, user_to_int):
    """
    Convert a single user-facing token to its corresponding internal symbol.
    Returns the token itself if not found.
    """
    return user_to_int.get(token, token)

def i_to_u(symbol, int_to_user):
    """
    Convert a single internal symbol (e.g., a Unicode character) to its corresponding
    user-facing token. Returns the symbol itself if not found.
    """
    return int_to_user.get(symbol, symbol)



