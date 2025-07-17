from mychess import ChessPosition, print_board_matrix
from fen_mapper import (
    load_existing_map,
    load_and_update_mapping,
    convert_fen_board_section
)

def test_basic_move():
    print("\n=== Test: Basic Pawn Move e2 to e4 ===")
    pos = ChessPosition()
    pos.set_fen("8/8/8/8/8/8/4P3/8 w - - 0 1")
    print_board_matrix(pos.board)
    
    pos.move_piece("e2", "e4")
    print("After move e2 to e4:")
    print_board_matrix(pos.board)

def test_add_piece():
    print("\n=== Test: Add a Piece at e7 ===")
    pos = ChessPosition()
    pos.set_fen("8/8/8/8/8/8/8/8 w - - 0 1")
    print_board_matrix(pos.board)
    
    pos.add_piece("e7", "♞")  # obscure unicode symbol
    print("After adding ♞ at e7:")
    print_board_matrix(pos.board)

def test_remove_piece():
    print("\n=== Test: Remove Piece from d2 ===")
    pos = ChessPosition()
    pos.set_fen("8/8/8/8/8/8/3P4/8 w - - 0 1")
    print_board_matrix(pos.board)
    
    pos.remove_piece("d2")
    print("After removing piece from d2:")
    print_board_matrix(pos.board)

def test_en_passant():
    print("\n=== Test: En Passant Wrong ===")
    pos = ChessPosition()
    pos.set_fen("8/8/8/3p4/4P3/8/8/8 w - - 0 1")
    print_board_matrix(pos.board)
    
    pos.move_piece("e4", "e5")  # white pawn advances one squares
    print("After white plays e4 to e5:")
    print_board_matrix(pos.board)
    
    pos.move_piece("d5", "e4")  # black makes illegal capture en passant
    print("After black captures en passant (d5 to e4!?):")
    print_board_matrix(pos.board)

def test_en_passant_real():
    print("\n=== Test: En Passant Real ===")
    pos = ChessPosition()
    pos.set_fen("8/8/8/8/3p4/8/4P3/8 w - - 0 1")
    print_board_matrix(pos.board)
    
    pos.move_piece("e2", "e4")  # white pawn advances one squares
    print("After white plays e2 to e4:")
    print_board_matrix(pos.board)
    
    pos.move_piece("d4", "e3")  # black makes capture en passant
    print("After black captures en passant (d4 to e3):")
    print_board_matrix(pos.board)


def test_castling_kingside():
    print("\n=== Test: Kingside Castling ===")
    pos = ChessPosition()
    pos.set_fen("8/8/8/8/8/8/8/R3K2R w - - 0 1")
    print_board_matrix(pos.board)
    
    pos.move_piece("e1", "g1")
    print("After white castles kingside (e1 to g1):")
    print_board_matrix(pos.board)

def test_castling_queenside():
    print("\n=== Test: Queenside Castling ===")
    pos = ChessPosition()
    pos.set_fen("8/8/8/8/8/8/8/R3K2R w - - 0 1")
    print_board_matrix(pos.board)
    
    pos.move_piece("e1", "c1")
    print("After white castles queenside (e1 to c1):")
    print_board_matrix(pos.board)

def test_black_castling():
    print("\n=== Test: Black Castling (Kingside and Queenside) ===")
    pos = ChessPosition()
    pos.set_fen("r3k2r/8/8/8/8/8/8/8 b KQkq - 0 1")
    print("Initial position:")
    print_board_matrix(pos.board)

    # Black kingside castling
    pos.move_piece("e8", "g8")
    print("\nAfter black castles kingside (e8 to g8):")
    print_board_matrix(pos.board)

    # Black queenside castling -- reset position first
    pos.set_fen("r3k2r/8/8/8/8/8/8/8 b KQkq - 0 1")
    pos.move_piece("e8", "c8")
    print("\nAfter black castles queenside (e8 to c8):")
    print_board_matrix(pos.board)


def test_promotion():
    print("\n=== Test: Pawn Promotion ===")
    pos = ChessPosition()
    pos.set_fen("8/PPPPP3/8/8/8/8/6PP/8 w - - 0 1")
    print_board_matrix(pos.board)
    
    pos.promote_pawn("e7", "e8", "q")
    print("After promoting e7 to e8 as Queen:")
    print_board_matrix(pos.board)


def test_multiple_promotions():
    print("\n=== Test: Multiple Pawn Promotions ===")
    pos = ChessPosition()
    pos.set_fen("8/PPPPP3/8/8/8/8/2p1p1pp/8 w - - 0 1")
    print("Initial position:")
    print_board_matrix(pos.board)

    # Promote b7 to b8 as Bishop (B)
    pos.promote_pawn("b7", "b8", "b")
    print("\nAfter promoting b7 to b8 as Bishop (B):")
    print_board_matrix(pos.board)

    # Promote c7 to c8 as Knight (S)
    pos.promote_pawn("c7", "c8", "s")
    print("\nAfter promoting c7 to c8 as Knight (S):")
    print_board_matrix(pos.board)

    # Promote g2 to g1 as Queen (Q)
    pos.promote_pawn("g2", "g1", "q")
    print("\nAfter promoting g2 to g1 as Queen (Q):")
    print_board_matrix(pos.board)

    # Promote h2 to h1 as Rook (R)
    pos.promote_pawn("h2", "h1", "r")
    print("\nAfter promoting h2 to h1 as Rook (R):")
    print_board_matrix(pos.board)


def test_neutral_promotion():
    print("\n=== Test: Neutral Pawn Promotion ===")
    pos = ChessPosition()
    pos.set_fen("8/4y3/8/8/8/8/8/8 w - - 0 1")
    print_board_matrix(pos.board)
    
    pos.promote_pawn("e7", "e8", "b")
    print("After promoting e7 to e8 as neutral bishop:")
    print_board_matrix(pos.board)

def test_opera_game():
    print("\n=== Test: Paul Morphy's Opera Game ===")
    pos = ChessPosition()
    pos.set_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")  # Start position

    moves = [
        ("e2", "e4"),  # 1. e4
        ("e7", "e5"),  # ... e5
        ("g1", "f3"),  # 2. Nf3
        ("d7", "d6"),  # ... d6
        ("d2", "d4"),  # 3. d4
        ("c8", "g4"),  # ... Bg4
        ("d4", "e5"),  # 4. dxe5
        ("g4", "f3"),  # ... Bxf3
        ("d1", "f3"),  # 5. Qxf3
        ("d6", "e5"),  # ... dxe5
        ("f1", "c4"),  # 6. Bc4
        ("g8", "f6"),  # ... Nf6
        ("f3", "b3"),  # 7. Qb3
        ("d8", "e7"),  # ... Qe7
        ("b1", "c3"),  # 8. Nc3
        ("c7", "c6"),  # ... c6
        ("c1", "g5"),  # 9. Bg5
        ("b7", "b5"),  # ... b5
        ("c4", "b5"),  # 10. Bxb5
        ("c6", "b5"),  # ... cxb5
        ("c3", "d5"),  # 11. Nd5
        ("f6", "d5"),  # ... Nxd5
        ("e4", "d5"),  # 12. exd5
        ("e7", "b4+"),# ... Qb4+
        ("c2", "c3"),  # 13. c3
        ("b4", "b5"),  # ... Qb5
        ("b5", "b7"),  # 14. Bxb7
        ("a8", "d8"),  # ... Rd8
        ("b7", "c6+"),# 15. Bc6+
        ("b8", "d7"),  # ... Nbd7
        ("d5", "d6"),  # 16. d6
        ("f8", "d6"),  # ... Bxd6
        ("c6", "d7+"),# 17. Bxd7+
        ("e8", "d7"),  # ... Kxd7
        ("a1", "d1"),  # 18. Rd1
        ("d7", "e6"),  # ... Ke6
        ("d1", "d6#")  # 19. Rd6#
    ]

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
    #user_to_internal_map = load_existing_map()
    #internal_to_user_map = {v: k for k, v in user_to_internal_map.items()}
    user_to_internal_map, internal_to_user_map, _ = load_and_update_mapping([start_fen])
    converted = convert_fen_board_section(start_fen, user_to_internal_map)
    
    pos = ChessPosition()
    pos.set_fen(converted)
    move_and_show(pos, "e2", "e4")
    move_and_show(pos, "b8", "c6")
    move_and_show(pos, "e1", "e7")

    squares = ["c6", "e7", "f8", "g8", "e2", "d1", "f1", "g1"]

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