# ChessNavigator - Copyright (c) 2025 David Hodge
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License v2 as published
# by the Free Software Foundation.
# Non-commercial use only. See LICENSE file for full details.

from djhchess.fen_mapper import (
    load_and_update_mapping,
    convert_fen_board_section,
    load_predefined_blocks,
    extract_tokens_from_fens,
    expand_tokens_with_blocks,
    validate_board_structure, single_extract_custom_tokens,
    load_existing_map,
    u_to_i,
    i_to_u
)

def print_mapping(title, mapping):
    print(f"\n{title}")
    for k, v in mapping.items():
        print(f"  {k} → {v}")


def test_conversion_to_unicode():
    # Test FENs with and without block triggers

    print("=== Demo: FEN Mapper ===")
    print("\nLoaded FENs:")
    for fen in test_fens:
        print(f"  {fen}")

    # Load and update mappings
    user_to_internal, internal_to_user, _ = load_and_update_mapping(test_fens)

    # Show mappings
    print_mapping("User → Internal Mapping", user_to_internal)
    print_mapping("Internal → User Mapping", internal_to_user)

    # Show converted FENs
    for fen in test_fens:
        print(f"\nOriginal FEN:  {fen}")
        converted = convert_fen_board_section(fen, user_to_internal)
        print(f"Internal FEN:  {converted}")
        restored = convert_fen_board_section(converted, internal_to_user)
        print(f"Restored FEN:  {restored}")

    # Re-scan to find new pieces
    user_to_internal, internal_to_user, _ = load_and_update_mapping(test_fens)


def test_valid_fens():

    # Run through each FEN and validate
    for fen in test_fens:
        print("\n=== FEN Validation Analysis ===")
        print(f"\nTest FEN:  {fen}")

        user_to_internal, internal_to_user, _ = load_and_update_mapping([fen])
        converted = convert_fen_board_section(fen, user_to_internal)
        print(f"Internal FEN:  {converted}")
        
        board_part = converted.split(' ')[0]
        
        if validate_board_structure(board_part):
            print("✅ FEN board is structurally valid.")
        else:
            print("❌ FEN board is invalid.")

def test_list_of_fens_to_list_of_fairy_pieces():

    # Step 1: Load existing map and block data
    user_to_internal, internal_to_user, _ = load_and_update_mapping(test_fens, map_file="piece_map.json")

    # Step 2: Initialize results dictionary
    results = {
        'fens_pieces': [],
        'user_to_internal': user_to_internal
    }

    # Step 3: Loop over FENs and process each
    for fen in test_fens:
        # Step 3.1: Extract custom tokens for this FEN
        tokens = single_extract_custom_tokens(fen)
        block_data = load_predefined_blocks()

        # Step 3.2: Expand tokens with blocks
        expanded_tokens = expand_tokens_with_blocks(tokens, block_data)

        # Step 3.3: Store results
        results['fens_pieces'].append({
            'original_tokens': sorted(tokens),
            'expanded_tokens': sorted(expanded_tokens)
        })

    # Display results
    print("Results:")
    for idx, fen in enumerate(test_fens):
        print(f"\nFEN {idx+1}: {fen}")
        print("Original Tokens:", results['fens_pieces'][idx]['original_tokens'])
        print("Expanded Tokens:", results['fens_pieces'][idx]['expanded_tokens'])

    print("\nUpdated user_to_internal mapping:")
    print(results['user_to_internal'])

def test_new_token_extractor():

    print("\nNew custom token extractor code")

    all_token_lists = extract_tokens_from_fens(test_fens)
    block_data = load_predefined_blocks()
    expanded_tokens = [expand_tokens_with_blocks(tokens, block_data) for tokens in all_token_lists]

    #for i, tokens in enumerate(all_token_lists):
    for i, tokens in enumerate(expanded_tokens):
        print(f"FEN {i+1} tokens:", tokens)

    print(f"\nThis is the all_token_list return:\n{all_token_lists}")
    print(f"\nThis is the expanded_tokens return:\n{expanded_tokens}")
    print("you'll see each fen gets its own list")

def test_token_translation_roundtrip():
    user_to_internal_map = load_existing_map()
    internal_to_user_map = {v: k for k, v in user_to_internal_map.items()}

    print("User → Internal symbol map:")
    for user_token, internal_symbol in user_to_internal_map.items():
        print(f"  {user_token} → {internal_symbol}")

    print("\nExamples of roundtrip conversions:")
    for user_token, internal_symbol in list(user_to_internal_map.items())[:10]:  # Just show first 10 for clarity
        forward = u_to_i(user_token, user_to_internal_map)
        backward = i_to_u(forward, internal_to_user_map)
        print(f"  We take this user token '{user_token}', convert it to '{forward}', then back to '{backward}'")



if __name__ == "__main__":
    test_fens = [
        "r1bqkbsr/pppppppp/8/8/8/8/PPPPPPPP/R1BQKBSR w KQkq - 0 1",  # Standard starting position
        "r1bqkbsr/=p=p=p=p=p=p=p=p/8/8/8/8/=p=p=p=p=p=p=p=p/R1BQKBSR w KQkq - 0 1",  # Standard neutral position
        "8/s3s3/8/8/G7/8/8/7.11 w KQkq - 0 1" # Position with a weird piece
        #"r1b.rokbsr/ppppp1pp/8/8/8/8/PPP2PPP/R1BQKBSR w KQkq - 0 1",  # Mid-game example
        #"r2gkbsr/ppp=.ro1ppp/3s4/8/8/8/PPP2PPP/R1BQKBSR w KQkq - 0 1",  # Endgame example
        #"r1bGkbsr/pppPpppp/8/8/8/8/PPPPPPPP/R1BQKBSR w KQkq - 0 1",  # Custom middle game
        #"r2.mak1sr/ppp1pppp/8/8/8/8/PPP2PPP/R1BQKBSR w KQkq - 0 1"  # Checkmate in 1 move position
    ]
    #test_fens = ["rgbqk=bsr/pppppppp/8/8/8/8/PP=pPPPPP/RSB=qKBSR w KQkq - 0 1"]
    #test_conversion_to_unicode()
    #test_valid_fens()
    #test_list_of_fens_to_list_of_fairy_pieces()
    test_new_token_extractor()
    #test_token_translation_roundtrip()
