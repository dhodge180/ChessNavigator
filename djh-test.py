import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
print(sys.path)
import chessf

GRASSHOPPER = 7  # Only needed if you're referencing the constant directly

# Load initial board with a white grasshopper at e5
fen = "8/8/8/4g3/8/8/8/8 w - - 0 1"
board = chessf.Board(fen)

print("Initial board:")
print(board)

# Place a white grasshopper at e4
board.set_piece_at(chessf.E4, chessf.Piece(GRASSHOPPER, chessf.WHITE))

# Place a black grasshopper at d6
board.set_piece_at(chessf.D6, chessf.Piece(GRASSHOPPER, chessf.BLACK))

# Remove the original at e5
board.remove_piece_at(chessf.E5)

# Print updated board
print("\nBoard after placing/removing Grasshoppers:")
print(board)

# Check squares
for square, label in [(chessf.E4, "e4"), (chessf.D6, "d6"), (chessf.E5, "e5")]:
    piece = board.piece_at(square)
    print(f"Square {label}: {piece.symbol() if piece else 'empty'}")

# Bitboards
print("\nWhite Grasshopper bitboard:", bin(board.pieces(GRASSHOPPER, chessf.WHITE)))
print("Black Grasshopper bitboard:", bin(board.pieces(GRASSHOPPER, chessf.BLACK)))


print("Unicode board display:\n")
print(board.unicode())
