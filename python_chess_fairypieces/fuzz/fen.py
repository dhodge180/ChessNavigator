import chessf

from pythonfuzz.main import PythonFuzz


@PythonFuzz
def fuzz(buf):
    try:
        fen = buf.decode("utf-8")
    except UnicodeDecodeError:
        pass
    else:
        try:
            board = chessf.Board(fen)
        except ValueError:
            pass
        else:
            sanitized_fen = board.fen()
            board.status()
            list(board.legal_moves)
            sanitized_board = chessf.Board(sanitized_fen)
            assert sanitized_board.fen() == sanitized_fen


if __name__ == "__main__":
    fuzz()
