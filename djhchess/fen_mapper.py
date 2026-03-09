# fen_mapper.py

import os
import json
import re
import unicodedata

#Provides these core functions
#load_existing_map(MAPFILE)
#u_to_i(token, user_to_int_map)
#i_to_u(token, int_to_user_map)
#load_and_update_mappings(fens, MAPFILE)

MAP_FILE = "./piece_map.json"

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
        "neutral": ["=k", "=q", "=r", "=b", "=s", "=p"],
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

def old_expand_tokens_with_blocks(tokens, block_data):
    expanded = set(tokens)
    for block_tokens in block_data.values():
        if any(t in tokens for t in block_tokens):
            expanded.update(block_tokens)
    return sorted(expanded)

def expand_tokens_with_blocks(tokens, block_data):
    expanded = []

    # 1️⃣ Add tokens not covered by any block first, in their original order
    for t in tokens:
        if not any(t in block for block in block_data.values()):
            if t not in expanded:
                expanded.append(t)

    # 2️⃣ Then add block tokens in block_data order
    for block_tokens in block_data.values():
        if any(t in tokens for t in block_tokens):
            for t in block_tokens:
                if t not in expanded:
                    expanded.append(t)

    return expanded


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

def expand_multiple_blank_rows(board_part):
    """
       Expand numbers that are multiples of 8 (>=16) in the board part into
       repeated '8' ranks separated by '/'.
       E.g. '24' -> '8/8/8', 'rnbqkbnr/24/8' -> 'rnbqkbnr/8/8/8/8'
    """
    result = []
    i = 0
    while i < len(board_part):
        ch = board_part[i]
        if '0' <= ch <= '9':
            # Consume full multi-digit number
            j = i
            while j < len(board_part) and '0' <= board_part[j] <= '9':
                j += 1
            n = int(board_part[i:j])
            if n % 8 == 0 and n >= 16:
                result.append('/'.join(['8'] * (n // 8)))
            else:
                result.append(board_part[i:j])
            i = j
        else:
            result.append(ch)
            i += 1
    return ''.join(result)


def validate_all_fens(all_fens, permitted_internals, user_chars, u_to_i_dict, i_to_u_dict):
    """
    Validate the board part of every FEN in all_fens.
    permitted_internals: set/list of engine piece codes.
    user_chars: list of user-facing piece codes (for helpful error messages).
    u_to_i_dict: mapping from user char -> internal char.
    i_to_u_dict: mapping from internal char -> user char (for error display).
    """
    valid = True
    errors = []

    for idx, fen in enumerate(all_fens):
        parts = fen.split()
        if not parts:
            errors.append(f"[ERROR] FEN #{idx+1} is empty. A FEN must have at least the board description.")
            valid = False
            continue

        board_part = parts[0]
        # Convert user-facing chars to internal engine chars
        board_part_converted = convert_fen_board_section(board_part, u_to_i_dict)
        board_part_converted = expand_multiple_blank_rows(board_part_converted) # Check for numbers like 24 in FEN
        # and replace with 8/8/8
        ranks = board_part_converted.split('/')

        # Check rank count
        if len(ranks) != 8:
            errors.append(f"[ERROR] FEN #{idx+1}: '{fen}'")
            errors.append("")
            errors.append(f"The board portion '{board_part}' must have exactly 8 ranks separated by '/'.")
            errors.append("")
            errors.append(f"You provided {len(ranks)} ranks.")
            errors.append("")
            errors.append("Tip:")
            errors.append("You can use multiples of 8 to represent empty ranks, e.g. '32' instead of '8/8/8/8'")
            errors.append("but you are not allowed non-multiples of 8, like 20, use 4/16.")
            errors.append("Example valid boards: '8/8/8/8/8/8/8/8' is the same as '64'")
            errors.append("or this complex example '24/k6K/16/pPpP4/8'")
            valid = False
            continue

        # Check each rank
        for r_idx, rank in enumerate(ranks):
            count = 0
            i = 0
            rank_has_error = False

            while i < len(rank):
                ch = rank[i]

                if ch.isdigit():
                    count += int(ch)
                    i += 1
                    continue

                # Match internal piece codes (single or multi-char)
                matched = False
                for piece in sorted(permitted_internals, key=len, reverse=True):
                    if rank.startswith(piece, i):
                        count += 1
                        i += len(piece)
                        matched = True
                        break

                if not matched:
                    bad = rank[i]
                    user_bad = i_to_u_dict.get(bad, bad)
                    offending_rank_user = ''.join(i_to_u_dict.get(ch, ch) for ch in ranks[r_idx])
                    errors.append(f"[ERROR] FEN #{idx+1}, Rank {r_idx+1}: Invalid character at '{user_bad}'.")
                    errors.append(f"        Check this row for invalid characters: '{offending_rank_user}'")
                    errors.append(f"        Allowed pieces: {', '.join(user_chars)}")
                    errors.append("Normal causes are:")
                    errors.append("         (a) using a fairy piece that is not in the file custom_pieces.yml")
                    errors.append("         (b) mis-typing a letter in your FEN")
                    errors.append("Note pieces are case-sensitive.")
                    valid = False
                    rank_has_error = True
                    i += 1  # Skip bad char to avoid infinite loop

            if not rank_has_error and count != 8:
                # Convert internal chars back to user chars for display
                offending_rank_user = ''.join(i_to_u_dict.get(ch, ch) for ch in ranks[r_idx])
                errors.append(f"[ERROR] FEN #{idx+1}, Rank {r_idx+1}: Rank does not describe exactly 8 squares (got {count}).")
                errors.append(f"        Offending rank says: '{offending_rank_user}' which is {count} squares")
                errors.append("        Fix the numbers so each rank totals 8 squares.")
                valid = False

    return valid, errors




def convert_fen_board_section(fen, mapping):
    """Convert only the board layout part of the FEN using the provided mapping."""

    board, fen_tail = split_epd_from_fen(fen)

    # Replace longer tokens first (e.g., .g1 before .g)
    sorted_tokens = sorted(mapping.keys(), key=len, reverse=True)
    for token in sorted_tokens:
        board = board.replace(token, mapping[token])

    return " ".join([board] + fen_tail)

def load_and_update_mapping(fens, map_file=MAP_FILE, extras=None):
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
            extras (list): A list of user_chars for all pieces named in custom_pieces.yml, which we also want to be included

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

    # If passed a single fen string, convert to a list first
    if isinstance(fens, str):
        fens = [fens]

    symbol_pool = generate_unicode_symbols()
    user_to_internal = load_existing_map(map_file)
    existing_symbols = set(user_to_internal.values())

    raw_tokens = extract_tokens_from_fens(fens)
    if raw_tokens is None:
        raw_tokens = extras
    else:
        raw_tokens.append(extras)  # Add the passed extra tokens to include in creations.
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



