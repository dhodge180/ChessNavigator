from pieces import Piece

def main():
    square_size = 80
    all_pieces = Piece.all()

    for piece in sorted(all_pieces, key=lambda p: p.internal_char):
        filename = piece.image_filename(square_size)
        print(f"Piece {piece.user_char} ({piece.long_name}), rotation={piece.rotation} -> Image filename: {filename}")

if __name__ == "__main__":
    main()
