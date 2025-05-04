#!/usr/bin/env python3

"""Compute X-ray attacks through more valuable pieces."""

import chessf


def xray_rook_attackers(board: chessf.Board, color: chessf.Color, square: chessf.Square) -> chessf.SquareSet:
    occupied = board.occupied
    rank_pieces = chessf.BB_RANK_MASKS[square] & occupied
    file_pieces = chessf.BB_FILE_MASKS[square] & occupied

    # Find the closest piece for each direction. These may block attacks.
    blockers = chessf.BB_RANK_ATTACKS[square][rank_pieces] | chessf.BB_FILE_ATTACKS[square][file_pieces]

    # Only consider blocking pieces of the victim that are more valuable
    # than rooks.
    blockers &= board.occupied_co[not color] & (board.queens | board.kings)

    # Now just ignore those blocking pieces.
    occupied ^= blockers

    # And compute rook attacks.
    rank_pieces = chessf.BB_RANK_MASKS[square] & occupied
    file_pieces = chessf.BB_FILE_MASKS[square] & occupied
    return chessf.SquareSet(board.occupied_co[color] & board.rooks & (
            chessf.BB_RANK_ATTACKS[square][rank_pieces] |
            chessf.BB_FILE_ATTACKS[square][file_pieces]))


def xray_bishop_attackers(board: chessf.Board, color: chessf.Color, square: chessf.Square) -> chessf.SquareSet:
    occupied = board.occupied
    diag_pieces = chessf.BB_DIAG_MASKS[square] & occupied

    # Find the closest piece for each direction. These may block attacks.
    blockers = chessf.BB_DIAG_ATTACKS[square][diag_pieces]

    # Only consider blocking pieces of the victim that are more valuable
    # than bishops.
    blockers &= board.occupied_co[not color] & (board.rooks | board.queens | board.kings)

    # Now just ignore those blocking pieces.
    occupied ^= blockers

    # And compute bishop attacks.
    diag_pieces = chessf.BB_DIAG_MASKS[square] & occupied
    return chessf.SquareSet(board.occupied_co[color] & board.bishops & chessf.BB_DIAG_ATTACKS[square][diag_pieces])


def example() -> None:
    board = chessf.Board("r3k2r/pp3p2/4p2Q/4q1p1/4P3/P2PK3/6PP/R3R3 w q - 1 2")
    print("rook x-ray, black, h3:")
    print(xray_rook_attackers(board, chessf.BLACK, chessf.H3))

    board = chessf.Board("r1b1r1k1/pp1n1pbp/1qp3p1/B2p4/3P4/Q3PN2/PP2BPPP/R4RK1 b - - 0 1")
    print("bishop x-ray, white, d8:")
    print(xray_bishop_attackers(board, chessf.WHITE, chessf.D8))


if __name__ == "__main__":
    example()
