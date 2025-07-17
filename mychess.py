from multiprocessing import Process, Queue
from collections import OrderedDict
from fen_mapper import load_existing_map
from square import Square

## Container for composition database

class Composition:
    def __init__(self, id, title, fen, moves, stipulation):
        self.id = id
        self.fen = fen
        self.moves = moves
        self.title = title
        self.stipulation = stipulation
        self.fen_tree = None
        self.ids = None
        self.move_tree = None
        self.tree_position = 0
        self.position = None
        self.move_window_version = False

    def turn_on_move_windows_messaging(self):
        self.move_window_version = True

    def create_position(self):
        self.position = ChessPosition(self.fen)

    def get_position_object(self):
        return self.position

    def advance_tree_step(self, direction):
        """Move through current fen tree. Forwards, backwards or jump to end."""
        current_fen_tree = self.fen_tree

        # If there's another move to play
        if direction == 1:  # Request to step forwards
            if self.tree_position + 1 < len(current_fen_tree):
                self.tree_position += 1
        elif direction == -1:
            if self.tree_position > 0:
                self.tree_position -= 1
        elif direction is None:  # This means jump to the end
            self.tree_position = len(current_fen_tree) - 1

        # Move to next position (might be same position if at an end already)
        self.position.set_fen(current_fen_tree[self.tree_position])
        # Could now send news to move window to move highlight marker
        if self.move_window_version == True:
            self.move_window_queue.put(('state', self.tree_position))

class ProblemListContainer:
    def __init__(self):
        self.compositions = OrderedDict()
        self.current_index = 0
        self.num_compositions = 0

    def add_composition(self, title: str, fen: str, moves: str, stipulation: str):
        """Add a new composition and return it."""
        # Use the number of compositions as the index (1-based)
        comp_id = self.num_compositions + 1
        comp = Composition(comp_id, title, fen, moves, stipulation)
        self.compositions[comp_id] = comp
        self.num_compositions += 1
        return comp

    def set_current(self, current_index):
        """Set the current problem using an index."""
        if 1 <= current_index <= self.num_compositions:
            self.current_index = current_index
        else:
            raise IndexError("Current index out of range.")

    def get_current(self):
        """Get the current composition."""
        return self.compositions.get(self.current_index)

    def go_forward_one(self):
        """Move to the next problem by advancing the index."""
        if self.num_compositions > 0:
            self.current_index = (self.current_index % self.num_compositions) + 1  # Wrap around when necessary

    def go_back_one(self):
        """Move to the next problem by advancing the index."""
        if self.num_compositions > 0:
            self.current_index = (self.current_index - 2) % self.num_compositions + 1  # Wrap around when necessary


## Chess Position handler (using FEN)

class ChessPosition:
    # Cached Square instances for castling and common usage
    E1 = Square.get(alg="e1")
    H1 = Square.get(alg="h1")
    F1 = Square.get(alg="f1")
    G1 = Square.get(alg="g1")
    A1 = Square.get(alg="a1")
    B1 = Square.get(alg="b1")
    C1 = Square.get(alg="c1")
    D1 = Square.get(alg="d1")

    E8 = Square.get(alg="e8")
    H8 = Square.get(alg="h8")
    F8 = Square.get(alg="f8")
    G8 = Square.get(alg="g8")
    A8 = Square.get(alg="a8")
    B8 = Square.get(alg="b8")
    C8 = Square.get(alg="c8")
    D8 = Square.get(alg="d8")

    CASTLING_MOVES = {
        E1: [G1, C1],
        E8: [G8, C8],
    }

    def __init__(self, fen=None):
        # Board is an 8x8 matrix from 00 to 77, with f2 equal to 15, i.e. [y-coord][x-coord] format
        self.board = []
        self.turn = 'w'
        self.en_passant = None
        self.king_pieces = ["K", "k"]  # Predefined list of king pieces
        self.pawn_pieces = ["P", "p", "=p"]  # Predefined list of en passant and promotion pieces (y is temp name for neutral pawn)
        self.neutral_pieces = ["=p", "=b", "=s", "=q", "=k"]
        self.fen = None
        self.standard_pieces = set("KQRBSPkqrbsp")
        if fen:
            self.set_fen(fen)
        self.user_to_internal_map = load_existing_map()
        self.internal_to_user_map = {v: k for k, v in self.user_to_internal_map.items()}

        self.legal_moves_enabled = False
        self.start_pos = fen
        self.move_history = []

        self.board_index = self.create_index_lookup()


    def convert_u_to_i(self, token):
        if token in self.standard_pieces:
            return token
        else:
            return self.user_to_internal_map.get(token, "?")

    def convert_i_to_u(self, token):
        if token in self.standard_pieces:
            return token
        else:
            return self.internal_to_user_map.get(token, "!")

    def parse_fen(self, fen):
        parts = fen.split()
        board = self.fen_to_board(parts[0])
        if len(parts) == 1:
            # Only been passed the board bit
            parts.append('w') # turn
            parts.append('-') # castling
            parts.append('-') # en passant
        turn = parts[1]
        en_passant = parts[3] if parts[3] != '-' else None
        return board, turn, en_passant

    def change_turn(self):
        self.turn = 'b' if self.turn == 'w' else 'w'

    def set_fen(self, fen):
        """Update the board and internal state with a new FEN."""
        self.fen = fen
        self.board, self.turn, self.en_passant = self.parse_fen(fen)

    def clear(self):
        fen = "8/8/8/8/8/8/8/8 w - - 0 1"
        self.board, self.turn, self.en_passant = self.parse_fen(fen)

    def update_fen(self):
        self.fen = self.board_to_fen()

    def fen_to_board(self, placement):
        rows = placement.split('/')
        board = []
        for row in rows:
            board_row = []
            for char in row:
                if char.isdigit():
                    board_row.extend(['1'] * int(char))
                else:
                    board_row.append(char)
            board.append(board_row)
        #board.reverse()  # Flip so rank 1 is at index 0
        return board

    def board_to_fen(self):
        # rows = list(reversed(self.board))  # Flip back to FEN order
        rows = list(self.board)  # Flip back to FEN order
        fen_rows = []
        for row in rows:
            empty = 0
            fen_row = ''
            for cell in row:
                if cell == '1':
                    empty += 1
                else:
                    if empty:
                        fen_row += str(empty)
                        empty = 0
                    fen_row += cell
            if empty:
                fen_row += str(empty)
            fen_rows.append(fen_row)
        board_part = '/'.join(fen_rows)
        ep = self.en_passant if self.en_passant else '-'
        return f"{board_part} {self.turn} - {ep} 0 1"

    # Move functions

    def is_castling_move(self, start: Square, end: Square) -> bool:
        return end in self.CASTLING_MOVES.get(start, [])

    def capture_en_passant(self, start: Square, end: Square):
        # start_row, start_col = start.coord
        end_row, end_col = end.coord
        # piece = self.board[start_row][start_col]

        # Remove the captured pawn from the en passant square
        if self.turn == 'w':
            # White captures black pawn which is below the end square
            self.board[end_row + 1][end_col] = '1'
        else:
            # Black captures white pawn which is above the end square
            self.board[end_row - 1][end_col] = '1'

        self.move_piece_internal(start, end)  # Move the pawn to the destination square
        self.en_passant = None  # Reset en passant after the capture
        self.update_fen()

    def can_castle(self, side, kingside):
        if side == 'w':
            if kingside:
                return (self.get_piece(self.E1) == 'K' and
                        self.get_piece(self.H1) == 'R' and
                        all(self.is_empty(sq) for sq in [self.F1, self.G1]))
            else:
                return (self.get_piece(self.E1) == 'K' and
                        self.get_piece(self.A1) == 'R' and
                        all(self.is_empty(sq) for sq in [self.B1, self.C1, self.D1]))
        else:
            if kingside:
                return (self.get_piece(self.E8) == 'k' and
                        self.get_piece(self.H8) == 'r' and
                        all(self.is_empty(sq) for sq in [self.F8, self.G8]))
            else:
                return (self.get_piece(self.E8) == 'k' and
                        self.get_piece(self.A8) == 'r' and
                        all(self.is_empty(sq) for sq in [self.B8, self.C8, self.D8]))

    def move_piece_internal(self, start: Square, end: Square):
        start_row, start_col = start.coord
        end_row, end_col = end.coord

        piece = self.board[start_row][start_col]
        self.board[start_row][start_col] = '1'  # Clear start square
        self.board[end_row][end_col] = piece  # Move piece to end square

    def move_piece(self, start: Square, end: Square):
        start_row, start_col = start.coord
        end_row, end_col = end.coord
        piece = self.board[start_row][start_col]
        # target = self.board[end_row][end_col]

        if piece == '1':
            # Start square empty, no move
            return

        # Castling (execute as two moves)
        if piece in self.king_pieces and self.is_castling_move(start, end):
            if start == self.E1:
                if end == self.G1 and self.can_castle('w', True):
                    self.move_piece_internal(self.E1, self.G1)
                    self.move_piece_internal(self.H1, self.F1)
                elif end == self.C1 and self.can_castle('w', False):
                    self.move_piece_internal(self.E1, self.C1)
                    self.move_piece_internal(self.A1, self.D1)
                else:
                    return  # Invalid castling
            elif start == self.E8:
                if end == self.G8 and self.can_castle('b', True):
                    self.move_piece_internal(self.E8, self.G8)
                    self.move_piece_internal(self.H8, self.F8)
                elif end == self.C8 and self.can_castle('b', False):
                    self.move_piece_internal(self.E8, self.C8)
                    self.move_piece_internal(self.A8, self.D8)
                else:
                    return  # Invalid castling

            self.change_turn()
            self.en_passant = None
            self.update_fen()
            return

        # En passant capture
        if piece.lower() in self.pawn_pieces and end == self.en_passant:
            self.capture_en_passant(start, end)
        else:
            # Normal move
            self.move_piece_internal(start, end)

            # En passant target square logic for pawn double moves
            if piece.lower() in self.pawn_pieces:
                if self.turn == 'w' and start_row == 6 and end_row == 4 and end_col == start_col:
                    self.en_passant = Square.get(coord=(5, end_col))  # rank 3 (index 5)
                elif self.turn == 'b' and start_row == 1 and end_row == 3 and end_col == start_col:
                    self.en_passant = Square.get(coord=(2, end_col))  # rank 6 (index 2)
                else:
                    self.en_passant = None
            else:
                self.en_passant = None

        self.change_turn()
        self.update_fen()

    def promote_pawn(self, start: Square, end: Square, new_piece: str):
        """
        new_piece is lowercase user-defined piece symbol (e.g. 'q', 'r', 'n', 'b')
        """

        start_row, start_col = start.coord
        end_row, end_col = end.coord
        internal_piece = self.board[start_row][start_col]
        piece = self.convert_i_to_u(internal_piece)

        if piece.lower() not in self.pawn_pieces:
            raise ValueError("Only pawns can be promoted")

        if (piece == 'P' and end_row == 0) or (piece == 'p' and end_row == 7) or (piece == '=p' and end_row in [0,7]):
            self.board[start_row][start_col] = '1'
             # Determine promoted piece with correct color
            promoted = new_piece.upper() if end_row == 0 else new_piece.lower()
            
            # Keep '=' prefix if the original piece was marked as such
            if piece in self.neutral_pieces:
                promoted = '=' + promoted.lower()

            internal_promoted = self.convert_u_to_i(promoted)
            self.board[end_row][end_col] = internal_promoted
            self.en_passant = None
            self.change_turn()
            self.update_fen()
        else:
            # This indicated an attempt to promote a white pawn on the 1st rank, or black pawn on the 8th rank
            raise ValueError("Promotion of this piece must happen on last rank")

    def get_piece(self, square_sing):
        row, col = square_sing.coord

        piece = self.board[row][col]
        return None if piece == '1' else p

    def is_empty(self, square: Square) -> bool:
        return self.get_piece(square) is None

    def add_piece(self, square: Square, piece: str):
        """Adds a piece to the board at the given square."""
        row, col = square.coord
        internal_piece = self.convert_u_to_i(piece)
        self.board[row][col] = internal_piece
        self.update_fen()

    def get_en_passant(self):
        return self.en_passant

    def get_turn(self):
        return self.turn

    def remove_piece(self, square):
        col, row = square.coord
        self.board[row][col] = '1'
        self.update_fen()

    def get_piece_colour(self, internal_token):
        """
        Determines the side (white, black, or neutral) of a piece based on its internal symbol.

        Args:
            internal_token (str): A single-character internal symbol (Unicode).

        Returns:
            str: 'white', 'black', or 'neutral'
        """
        if internal_token is None or internal_token == '1':
            return None # Empty square
        
        reserved = set("PSBRQKpsbrqk12345678/")
        if internal_token in reserved:
            user_token = internal_token
        else:
            user_token = self.internal_to_user_map.get(internal_token)

        if user_token is None:
            raise ValueError(f"Internal symbol '{internal_token}' not found in mapping.")

        if user_token.startswith('='):
            return 'neutral'

        # Remove leading dot (if present) before checking the first significant character
        core = user_token.lstrip('.')
        if not core:
            return 'error no piece found'  # fallback for malformed token

        first_char = core[0]
        if first_char.isupper():
            return 'w'
        elif first_char.islower():
            return 'b'
        else:
            return 'error unable to determine colour'

    def toggle_legality(self):
        #self.legal_moves_enabled = not self.legal_moves_enabled  # Toggle legality mode
        # NO TOGGLE ANY MORE, ALWAYS OFF
        self.legal_moves_enabled = False

    def undo_move(self):
        print("Not implemented how to undo moves yet")

    def redefine_start(self):
        """This forces the current board position to become the reset state"""
        self.start_pos = self.fen

    def reset_board(self):
        self.set_fen(self.start_pos)
        self.reset_move_history()
        self.tree_position = 0

    def reset_move_history(self):
        self.move_history = []

def print_board_matrix(board, empty_square_char='.'):
    for row in board:  # print rank 8 to 1
        print(' '.join(empty_square_char if cell == '1' else cell for cell in row))
    print()

## Test worker

def worker(container, result_q):
    current = container.get_current()
    result = {
        "id": current.id,
        "piece_count": len(current.fen.replace("/", "").replace("1", "")),  # crude count
    }
    result_q.put(result)

# --- Main Program ---

if __name__ == '__main__':
    container = ProblemListContainer()
    container.add_composition("Silly problem", "8/8/8/8/8/8/8/K6k", [], "mate in 1")
    container.add_composition("Silly problem", "8/8/8/8/8/R7/8/K6k", [], "mate in 2")
    container.add_composition("Silly problem", "8/8/1ppppp1p/8/8/8/8/K6k", [], "mate in 3")
    container.set_current(f"{3:03}")

    result_q = Queue()
    p = Process(target=worker, args=(container, result_q))
    p.start()
    p.join()

    result = result_q.get()
    print(f"Worker result: {result}")



