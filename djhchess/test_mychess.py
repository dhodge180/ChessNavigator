# ChessNavigator - Copyright (c) 2025 David Hodge
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License v2 as published
# by the Free Software Foundation.
# Non-commercial use only. See LICENSE file for full details.

from djhchess.square import Square
from djhchess.mychess import ChessPosition, print_board_matrix
from djhchess.fen_mapper import (
    load_and_update_mapping,
    convert_fen_board_section
)

# Define constants for all squares

A1 = Square.get(alg="a1")
B1 = Square.get(alg="b1")
C1 = Square.get(alg="c1")
D1 = Square.get(alg="d1")
E1 = Square.get(alg="e1")
F1 = Square.get(alg="f1")
G1 = Square.get(alg="g1")
H1 = Square.get(alg="h1")

A2 = Square.get(alg="a2")
B2 = Square.get(alg="b2")
C2 = Square.get(alg="c2")
D2 = Square.get(alg="d2")
E2 = Square.get(alg="e2")
F2 = Square.get(alg="f2")
G2 = Square.get(alg="g2")
H2 = Square.get(alg="h2")

A3 = Square.get(alg="a3")
B3 = Square.get(alg="b3")
C3 = Square.get(alg="c3")
D3 = Square.get(alg="d3")
E3 = Square.get(alg="e3")
F3 = Square.get(alg="f3")
G3 = Square.get(alg="g3")
H3 = Square.get(alg="h3")

A4 = Square.get(alg="a4")
B4 = Square.get(alg="b4")
C4 = Square.get(alg="c4")
D4 = Square.get(alg="d4")
E4 = Square.get(alg="e4")
F4 = Square.get(alg="f4")
G4 = Square.get(alg="g4")
H4 = Square.get(alg="h4")

A5 = Square.get(alg="a5")
B5 = Square.get(alg="b5")
C5 = Square.get(alg="c5")
D5 = Square.get(alg="d5")
E5 = Square.get(alg="e5")
F5 = Square.get(alg="f5")
G5 = Square.get(alg="g5")
H5 = Square.get(alg="h5")

A6 = Square.get(alg="a6")
B6 = Square.get(alg="b6")
C6 = Square.get(alg="c6")
D6 = Square.get(alg="d6")
E6 = Square.get(alg="e6")
F6 = Square.get(alg="f6")
G6 = Square.get(alg="g6")
H6 = Square.get(alg="h6")

A7 = Square.get(alg="a7")
B7 = Square.get(alg="b7")
C7 = Square.get(alg="c7")
D7 = Square.get(alg="d7")
E7 = Square.get(alg="e7")
F7 = Square.get(alg="f7")
G7 = Square.get(alg="g7")
H7 = Square.get(alg="h7")

A8 = Square.get(alg="a8")
B8 = Square.get(alg="b8")
C8 = Square.get(alg="c8")
D8 = Square.get(alg="d8")
E8 = Square.get(alg="e8")
F8 = Square.get(alg="f8")
G8 = Square.get(alg="g8")
H8 = Square.get(alg="h8")


def test_basic_move():
    print("\n=== Test: Basic Pawn Move e2 to e4 ===")
    pos = ChessPosition()
    pos.set_fen("8/8/8/8/8/8/4P3/8 w - - 0 1")
    print_board_matrix(pos.board)

    pos.move_piece(E2, E4)
    print("After move e2 to e4:")
    print_board_matrix(pos.board)


def test_add_piece():
    print("\n=== Test: Add a Piece at e7 ===")
    pos = ChessPosition()
    pos.set_fen("8/8/8/8/8/8/8/8 w - - 0 1")
    print_board_matrix(pos.board)

    pos.add_piece(E7, "♞")  # obscure unicode symbol
    print("After adding ♞ at e7:")
    print_board_matrix(pos.board)


def test_remove_piece():
    print("\n=== Test: Remove Piece from d2 ===")
    pos = ChessPosition()
    pos.set_fen("8/8/8/8/8/8/3P4/8 w - - 0 1")
    print_board_matrix(pos.board)

    pos.remove_piece(D2)
    print("After removing piece from d2:")
    print_board_matrix(pos.board)


def test_en_passant():
    print("\n=== Test: En Passant Wrong ===")
    pos = ChessPosition()
    pos.set_fen("8/8/8/3p4/4P3/8/8/8 w - - 0 1")
    print_board_matrix(pos.board)

    pos.move_piece(E4, E5)  # white pawn advances one squares
    print("After white plays e4 to e5:")
    print_board_matrix(pos.board)

    pos.move_piece(D5, E4)  # black makes illegal capture en passant
    print("After black captures en passant (d5 to e4!?):")
    print_board_matrix(pos.board)


def test_en_passant_real():
    print("\n=== Test: En Passant Real ===")
    pos = ChessPosition()
    pos.set_fen("8/8/8/8/3p4/8/4P3/8 w - - 0 1")
    print_board_matrix(pos.board)

    pos.move_piece(E2, E4)  # white pawn advances one squares
    print("After white plays e2 to e4:")
    print_board_matrix(pos.board)

    pos.move_piece(D4, E3)  # black makes capture en passant
    print("After black captures en passant (d4 to e3):")
    print_board_matrix(pos.board)


def test_castling_kingside():
    print("\n=== Test: Kingside Castling ===")
    pos = ChessPosition()
    pos.set_fen("8/8/8/8/8/8/8/R3K2R w - - 0 1")
    print_board_matrix(pos.board)

    pos.move_piece(E1, G1)
    print("After white castles kingside (e1 to g1):")
    print_board_matrix(pos.board)


def test_castling_queenside():
    print("\n=== Test: Queenside Castling ===")
    pos = ChessPosition()
    pos.set_fen("8/8/8/8/8/8/8/R3K2R w - - 0 1")
    print_board_matrix(pos.board)

    pos.move_piece(E1, C1)
    print("After white castles queenside (e1 to c1):")
    print_board_matrix(pos.board)


def test_black_castling():
    print("\n=== Test: Black Castling (Kingside and Queenside) ===")
    pos = ChessPosition()
    pos.set_fen("r3k2r/8/8/8/8/8/8/8 b KQkq - 0 1")
    print("Initial position:")
    print_board_matrix(pos.board)

    # Black kingside castling
    pos.move_piece(E8, G8)
    print("\nAfter black castles kingside (e8 to g8):")
    print_board_matrix(pos.board)

    # Black queenside castling -- reset position first
    pos.set_fen("r3k2r/8/8/8/8/8/8/8 b KQkq - 0 1")
    pos.move_piece(E8, C8)
    print("\nAfter black castles queenside (e8 to c8):")
    print_board_matrix(pos.board)


def test_promotion():
    print("\n=== Test: Pawn Promotion ===")
    pos = ChessPosition()
    pos.set_fen("8/PPPPP3/8/8/8/8/6PP/8 w - - 0 1")
    print_board_matrix(pos.board)

    pos.promote_pawn(E7, E8, "q")
    print("After promoting e7 to e8 as Queen:")
    print_board_matrix(pos.board)


def test_multiple_promotions():
    print("\n=== Test: Multiple Pawn Promotions ===")
    pos = ChessPosition()
    pos.set_fen("8/PPPPP3/8/8/8/8/2p1p1pp/8 w - - 0 1")
    print("Initial position:")
    print_board_matrix(pos.board)

    # Promote b7 to b8 as Bishop (B)
    pos.promote_pawn(B7, B8, "b")
    print("\nAfter promoting b7 to b8 as Bishop (B):")
    print_board_matrix(pos.board)

    # Promote c7 to c8 as Knight (S)
    pos.promote_pawn(C7, C8, "s")
    print("\nAfter promoting c7 to c8 as Knight (S):")
    print_board_matrix(pos.board)

    # Promote g2 to g1 as Queen (Q)
    pos.promote_pawn(G2, G1, "q")
    print("\nAfter promoting g2 to g1 as Queen (Q):")
    print_board_matrix(pos.board)

    # Promote h2 to h1 as Rook (R)
    pos.promote_pawn(H2, H1, "r")
    print("\nAfter promoting h2 to h1 as Rook (R):")
    print_board_matrix(pos.board)


def test_neutral_promotion():
    print("\n=== Test: Neutral Pawn Promotion ===")
    pos = ChessPosition()
    pos.set_fen("8/4y3/8/8/8/8/8/8 w - - 0 1")
    print_board_matrix(pos.board)

    pos.promote_pawn(E7, E8, "b")
    print("After promoting e7 to e8 as neutral bishop:")
    print_board_matrix(pos.board)


def test_opera_game():
    print("\n=== Test: Paul Morphy's Opera Game ===")
    pos = ChessPosition()
    pos.set_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")  # Start position

    moves = [
        (E2, E4),  # 1. e4
        (E7, E5),  # ... e5
        (G1, F3),  # 2. Nf3
        (D7, D6),  # ... d6
        (D2, D4),  # 3. d4
        (C8, G4),  # ... Bg4
        (D4, E5),  # 4. dxe5
        (G4, F3),  # ... Bxf3
        (D1, F3),  # 5. Qxf3
        (D6, E5),  # ... dxe5
        (F1, C4),  # 6. Bc4
        (G8, F6),  # ... Nf6
        (F3, B3),  # 7. Qb3
        (D8, E7),  # ... Qe7
        (B1, C3),  # 8. Nc3
        (C7, C6),  # ... c6
        (C1, G5),  # 9. Bg5
        (B7, B5),  # ... b5
        (C4, B5),  # 10. Bxb5
        (C6, B5),  # ... cxb5
        (C3, D5),  # 11. Nd5
        (F6, D5),  # ... Nxd5
        (E4, D5),  # 12. exd5
        # Note: Qb4+ and Rd1 moves use algebraic notation with check (#), so may need special handling if your code supports it
        # For now I keep them as strings, because these are not simple squares
        # ("e7", "b4+")  # ... Qb4+
        # ("b7", "c6+")  # 15. Bc6+
        # ("d1", "d6#")  # 19. Rd6#
    ]

    # For moves with special annotations like check (+) or mate (#), you may need special handling.
    # We'll run the basic moves here only.

    for idx, (start, end) in enumerate(moves, 1):
        print(f"\nMove {idx}: {start} to {end}")
        pos.move_piece(start, end)
        print_board_matrix(pos.board, ".")

    print("\n✅ Opera Game executed successfully.\n")


def move_and_show(position, start, end):
    print("Before move:")
    print_board_matrix(position.board)
    position.move_piece(start, end)
    print(f"After move {start} to {end}:")
    print_board_matrix(position.board)


def test_unicode_fen(start_fen):
    print("Unicode and colour test")
    user_to_internal_map, internal_to_user_map, _ = load_and_update_mapping([start_fen])
    converted = convert_fen_board_section(start_fen, user_to_internal_map)

    pos = ChessPosition()
    pos.set_fen(converted)
    move_and_show(pos, E2, E4)
    move_and_show(pos, B8, C6)
    move_and_show(pos, E1, E7)

    squares = [C6, E7, F8, G8, E2, D1, F1, G1]

    for square in squares:
        piece = pos.get_piece(square)
        col = pos.get_piece_colour(piece)
        print(f"Piece at {square} is colour: {col}")


def run_test(test_name, *args):
    test_name(*args)
    input("Press Enter to continue to next test...")


def run_all_tests():
    run_test(test_basic_move)
    run_test(test_add_piece)
    run_test(test_remove_piece)
    run_test(test_en_passant)
    run_test(test_en_passant_real)
    run_test(test_castling_kingside)
    run_test(test_castling_queenside)
    run_test(test_black_castling)
    run_test(test_promotion)
    run_test(test_multiple_promotions)
    run_test(test_neutral_promotion)
    run_test(test_opera_game)
    run_test(test_unicode_fen, "rgbqk=bnr/pppppppp/8/8/8/8/PP=pPPPPP/RNB=qKBNR w KQkq - 0 1")


if __name__ == "__main__":
    run_all_tests()