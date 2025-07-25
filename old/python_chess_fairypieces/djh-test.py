import chess

GRASSHOPPER = 7  # Only needed if you're referencing the constant directly

# Load initial board with a white grasshopper at e5
fen = "8/8/8/4g3/8/8/8/8 w - - 0 1"
board = chess.Board(fen)

print("Initial board:")
print(board)

# Place a white grasshopper at e4
board.set_piece_at(chess.E4, chess.Piece(GRASSHOPPER, chess.WHITE))

# Place a black grasshopper at d6
board.set_piece_at(chess.D6, chess.Piece(GRASSHOPPER, chess.BLACK))

# Remove the original at e5
board.remove_piece_at(chess.E5)

# Print updated board
print("\nBoard after placing/removing Grasshoppers:")
print(board)

# Check squares
for square, label in [(chess.E4, "e4"), (chess.D6, "d6"), (chess.E5, "e5")]:
    piece = board.piece_at(square)
    print(f"Square {label}: {piece.symbol() if piece else 'empty'}")

# Bitboards
print("\nWhite Grasshopper bitboard:", bin(board.pieces(GRASSHOPPER, chess.WHITE)))
print("Black Grasshopper bitboard:", bin(board.pieces(GRASSHOPPER, chess.BLACK)))


print("Unicode board display:\n")
print(board.unicode())
