from multiprocessing import Process, Queue
from collections import OrderedDict
import re

from djhchess.square import Square
from djhchess.fen_mapper import load_existing_map, load_and_update_mapping
from djhchess.pieces import Piece, PieceBox

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
        self.u_to_i_map = None # Added at composition level (previously only in chessposition)
        self.i_to_u_map = None # Added at composition level (previously only in chessposition)

    def turn_on_move_windows_messaging(self):
        self.move_window_version = True

    def create_position(self):
        # Now passing self to copy the fen maps
        self.position = ChessPosition(parent_comp=self, fen=self.fen)

    def get_position_object(self):
        return self.position

    def advance_tree_step(self, direction, callback_queue=None):
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
        if callback_queue:
            callback_queue.put(('state', self.tree_position))
        #if self.move_window_version == True:
        #    self.move_window_queue.put(('state', self.tree_position))

    def jump_tree_step(self, target, callback_queue=None):

        """Jumps to a specific node of the tree and remembers for future arrow navigation"""
        current_fen_tree = self.fen_tree

        self.tree_position = target
        self.position.set_fen(current_fen_tree[self.tree_position])
        # Could now send news to move window to move highlight marker
        if callback_queue:
            callback_queue.put(('state', self.tree_position))

class ProblemListContainer:
    def __init__(self):
        self.compositions = OrderedDict()
        self.current_index = 0
        self.num_compositions = 0
        self.u_to_i_dict = None
        self.i_to_u_dict = None

    def add_composition(self, title: str, fen: str, moves: str | None, stipulation: str):
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

    def __init__(self, parent_comp=None, fen=None):
        # Board is an 8x8 matrix from 00 to 77, with f2 equal to 15, i.e. [y-coord][x-coord] format
        self.board = []
        self.turn = 'w'
        self.parent_composition = parent_comp
        self.en_passant = None
        self.king_pieces = ["K", "k"]  # Predefined list of king pieces
        self.pawn_pieces = ["P", "p", "=p"]  # Predefined list of en passant and promotion pieces (y is temp name for neutral pawn)
        self.neutral_pieces = ["=p", "=b", "=s", "=q", "=k"]
        self.fen = None
        self.standard_pieces = set("KQRBSPkqrbsp")
        if fen:
            self.set_fen(fen)

        # Currently not used. Not sure the load_existing_map() is working. It's global.
        self.user_to_internal_map = load_existing_map()
        self.internal_to_user_map = {v: k for k, v in self.user_to_internal_map.items()}

        self.legal_moves_enabled = False
        self.start_pos = fen
        self.move_history = [fen]
        self.move_index: int = 0 # Which fen are we on

    def convert_u_to_i(self, token):
        if token in self.standard_pieces:
            return token
        if self.parent_composition:
            return self.parent_composition.u_to_i_map.get(token, '?')
        else:
            return self.user_to_internal_map.get(token, "?")

    def convert_i_to_u(self, token):
        if token in self.standard_pieces:
            return token
        if self.parent_composition:
            return self.parent_composition.i_to_u_map.get(token, "!")
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

        #print("##################################")
        #print("Before doing anything")
        #self.print_hist()

        # History tracking
        if hasattr(self, 'move_history') and hasattr(self, 'move_index'):
            # If we did some undo before this update, remove future FENs
            if self.move_index < len(self.move_history) - 1:
                self.move_history = self.move_history[:self.move_index + 1]

            self.move_history.append(self.fen)
            self.move_index += 1

        else:
            # First time setup if not initialized yet
            self.move_history = [self.fen]
            self.move_index = 0

        #print("After adding one?")
        #self.print_hist()
        #print("##################################")

    def print_hist(self):
        # Print the last 5 FENs for debugging
        print("Last 5 FENs in history:")
        for i, fen_str in enumerate(self.move_history[-5:], start=max(0, self.move_index - 4)):
            marker = "->" if i == self.move_index else "  "
            print(f"{marker} [{i}] {fen_str}")
        print("-" * 40)

    def undo(self):
        if self.move_index > 0:
            self.move_index -= 1
            self.fen = self.move_history[self.move_index]
            self.set_fen(self.fen)

    def redo(self):
        if self.move_index < len(self.move_history) - 1:
            self.move_index += 1
            self.fen = self.move_history[self.move_index]
            self.set_fen(self.fen)

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

    def move_piece(self, start: Square, end: Square, promotion_callback=None):
        start_row, start_col = start.coord
        end_row, end_col = end.coord
        piece = self.board[start_row][start_col]
        #internal_piece = self.convert_u_to_i(piece)
        internal_piece = Piece.get(piece) # Get the true piece from the internal char stored in the board matrix
        #piece_colour = self.get_piece_colour(internal_piece)
        piece_colour = internal_piece.colour

        # Debugging neutral pawn moves from rank 7 to 5 to look for enpassant
        #if start_row == 1 and end_row == 3 and piece_colour == 'neutral':
        #    print("DEBUG ME!")

        # target = self.board[end_row][end_col]

        if piece == '1':
            # Start square empty, no move
            return

        # Castling (execute as two moves)
        if internal_piece.is_king and self.is_castling_move(start, end):
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
        if internal_piece.is_pawn and end == self.en_passant:
            self.capture_en_passant(start, end)
        else:
            # Check here if it's a promotion attempt
            if internal_piece.is_pawn:
                is_promotion = (internal_piece.is_black and end_row == 7) or \
                        (internal_piece.is_white and end_row == 0) or \
                        (internal_piece.is_neutral and end_row in [0, 7])
                if is_promotion:
                    # Only get here if it's a promotion move
                    if promotion_callback:
                        promotion_piece = promotion_callback()
                    else:
                        promotion_piece = 'Q'
                    # Ask for promotion piece
                    # promotion_piece = self.ask_for_promotion()  # Should return something like 'q', 'r', 'b', or 'n'
                    # promotion_piece = 'B'
                    # Perform promotion move instead of normal move
                    self.promote_pawn(start, end, promotion_piece)
                    #self.change_turn()
                    #self.en_passant = None
                    #self.update_fen()
                    return


            # Normal move
            self.move_piece_internal(start, end)

            # En passant target square logic for pawn double moves
            if internal_piece.is_pawn:
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
        new_piece is lowercase user-defined piece symbol (e.g. 'q', 'r', 's', 'b')
        """

        start_row, start_col = start.coord
        end_row, end_col = end.coord
        internal_piece = self.board[start_row][start_col]
        piece = Piece.get(internal_piece)

        if not piece.is_pawn:    
            raise ValueError("Only pawns can be promoted")

        if (piece.is_white and end_row == 0):
            promoted = new_piece.upper()
        elif (piece.is_black and end_row == 7):
            promoted = new_piece.lower()
        elif (piece.is_neutral and end_row in [0,7]):
            promoted = "=" + new_piece.lower()
        else:
            print("Something wrong. Couldn't identify the validity of promotion")
            raise ValueError("Promotion of this piece must happen on last rank")
    
        self.board[start_row][start_col] = '1' # Remove pawn from starting square

        internal_promoted = self.convert_u_to_i(promoted)
        self.board[end_row][end_col] = internal_promoted
        self.en_passant = None
        self.change_turn()
        self.update_fen()

    def get_piece(self, square_sing) -> str:
        row, col = square_sing.coord

        piece = self.board[row][col]
        return None if piece == '1' else piece

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
        row, col = square.coord
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
            user_token = self.convert_i_to_u(internal_token)

        if user_token in (None, '!'):
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

    def reset_move_history(self):
        self.move_history = [self.start_pos]
        self.move_index = 0

    def to_san(self, from_square, to_square):
        """Convert a move to SAN notation, disambiguating if needed (same piece, same colour)."""

        moving_piece = self.get_piece(from_square)
        target_piece = self.get_piece(to_square)

        # Determine prefix: blank for pawns, piece letter for others
        # Convert to user first
        true_piece = Piece.get(moving_piece) # Use internal name to find Piece singleton
        prefix = "" if true_piece.is_pawn else true_piece.user_char.upper()
        #prefix = "" if moving_piece in self.pawn_pieces else moving_piece.upper()

        # Check for ambiguity: same piece, same colour can reach to_square
        ambiguous = False

        for rank in range(8):
            for file in range(8):
                other_sq = Square.get(coord=(rank, file))
                if other_sq is from_square:
                    continue  # Skip the moving piece

                other_piece = self.get_piece(other_sq)
                if other_piece == moving_piece and self.can_reach(true_piece, other_sq, to_square):
                    ambiguous = True
                    break
            if ambiguous:
                break

        # Determine capture symbol
        capture = 'x' if target_piece is not None else ''

        if prefix == "":  # Pawn move
            if capture:
                # Pawn capture includes file of from_square + 'x' + destination square
                move_str = f"{from_square.alg[0]}{capture}{to_square.alg}"
            elif true_piece.is_neutral and ambiguous:
                # Neutral pawn ambiguous move
                move_str = f"{from_square.alg}{to_square.alg}"
            else:
                # Normal pawn move, just the destination square
                move_str = to_square.alg

        else:
            if ambiguous:
                # Disambiguation required: prefix + from_square + 'x' (if capture) + destination square
                move_str = f"{prefix}{from_square.alg}{capture}{to_square.alg}"
            else:
                # Standard piece move with optional 'x'
                move_str = f"{prefix}{capture}{to_square.alg}"

        return move_str

    def squares_in_path(self, start: Square, end: Square):
        """Generate squares strictly between start and end (exclusive) in a straight line (rook, bishop, queen)."""
        start_row, start_col = start.coord
        end_row, end_col = end.coord

        delta_row = end_row - start_row
        delta_col = end_col - start_col

        step_row = 0 if delta_row == 0 else (1 if delta_row > 0 else -1)
        step_col = 0 if delta_col == 0 else (1 if delta_col > 0 else -1)

        path = []
        current_row = start_row + step_row
        current_col = start_col + step_col

        while (current_row, current_col) != (end_row, end_col):
            # Check for valid board coordinates
            if not (0 <= current_row <= 7 and 0 <= current_col <= 7):
                break  # or raise error if you want strict validation

            path.append(Square.get(coord=(current_row, current_col)))
            current_row += step_row
            current_col += step_col

        return path

    def can_reach(self, piece, from_square: Square, to_square: Square):
        """
        Determine if `piece` at `from_square` can move to `to_square` assuming no board constraints.
        For pawns or 'g' pieces, always return True to force disambiguation.
        For sliding pieces, check if path is clear and move type is legal.
        For knights ('s'), check if move matches knight pattern.
        piece will be genuine Piece object
        """

        # Handle pawns or 'g' pieces — always True for disambiguation
        if piece.is_pawn or piece.is_grasshopper:
            return True

        # Handle knights ('s')
        #if piece.lower() == 's':
        if piece.is_knight:
            start_row, start_col = from_square.coord
            end_row, end_col = to_square.coord

            row_diff = abs(end_row - start_row)
            col_diff = abs(end_col - start_col)

            return (row_diff == 2 and col_diff == 1) or (row_diff == 1 and col_diff == 2)

        # Handle sliding pieces (rook, bishop, queen)
        #if piece.lower() in ['r', 'b', 'q']:
        if piece.is_rook or piece.is_bishop or piece.is_queen:
            start_row, start_col = from_square.coord
            end_row, end_col = to_square.coord

            delta_row = end_row - start_row
            delta_col = end_col - start_col

            # Check move legality first (before path check)
            #if piece.lower() == 'r' and (delta_row != 0 and delta_col != 0):
            if piece.is_rook and (delta_row != 0 and delta_col != 0):
                return False  # Rook must move straight

            #if piece.lower() == 'b' and abs(delta_row) != abs(delta_col):
            if piece.is_bishop and abs(delta_row) != abs(delta_col):
                return False  # Bishop must move diagonally

            # Path clearance
            path_squares = self.squares_in_path(from_square, to_square)
            for sq in path_squares:
                if self.get_piece(sq) != '1':  # '1' means empty square
                    return False  # blocked path

            return True

        # For kings or others, return True (or add logic later if needed)
        return True


class TempChessPosition(ChessPosition):
    """ This class is a copy of ChessPosition both with additional functions for creating the fen tree """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # Initialize like ChessPosition
        self.move_handlers: dict[str, callable] = {
            'move': self.handle_move,
            'promotion': self.handle_promotion,
            'save': self.handle_save,
            'home': self.handle_home,
            'skipback': self.handle_skipback,
            'player_turn': self.handle_set_whos_turn,
            'add': self.handle_add,
            'remove': self.handle_remove,
            'and': self.handle_and
        }
        self.move_id = -1
        self.id_record = []  # Vector storing (FEN position number in list, move_id) pairs

        self.generated = []  # This will store the full fens and be returned at the end
        self.add_this_fen()  # Start by adding the initial FEN. Will need to know this later with -> movements
        self.checkpoints = []  # Create checkpoints list
        self.current_checkpoint_index = 0
        self.checkpoints.append(self.fen)  # Start with the home position (shouldn't be necessary)

    # What follows now are operations for parsing the PROBLEM_LIST.txt file

    def add_this_fen(self):
        self.generated.append(self.fen)
        self.move_id += 1
        self.id_record.append(self.move_id)

    def process_move(self, move_str):
        # Global move id to pass around
        # Increment self.move_id += 1 when a new fen is added.

        # Convert the move string
        converted_move = self.convert_move(move_str)
        move_type = converted_move['type']

        button_label = None
        button_fen = None

        # Call the corresponding handler function from the dictionary
        if move_type in self.move_handlers:
            button_label, button_fen = self.move_handlers[move_type](converted_move)

        else:
            print(f"Unknown move type: {move_type}")

        return button_label, button_fen, self.move_id

    def handle_move(self, move):
        """e.g. {'type': 'move', 'from': 'a1', 'to': 'e5'}
        If the move is of uci-format then:
        perform it, and update the game
        save the current FEN into the list"""

        # Updated Square objects
        from_square = Square.get(alg=move['from'])
        to_square = Square.get(alg=move['to'])

        # Move recorded
        print(f"Regular move from {from_square.alg} to {to_square.alg}")

        piece = self.get_piece(from_square)
        target_piece = self.get_piece(to_square)

        if piece is None:
            print("Uhm, there was meant to be a piece here!")
            return None, None

        #internal_piece = self.convert_u_to_i(piece)
        internal_piece = piece # This is already internal nowadays
        piece_color = self.get_piece_colour(internal_piece)
        target_piece_color = self.get_piece_colour(target_piece) if target_piece else None

        if piece_color not in  (self.turn, 'neutral'):
            print("You moved out of turn, but I'll allow it [1].")
            self.change_turn()  # Swap player to move

        if target_piece is not None:
            if piece_color == target_piece_color and target_piece_color != 'neutral':
                print("You're trying to consume one of your own pieces. I'll allow it.")
                deletion_move = self.convert_move("-" + to_square.alg)
                and_move = self.convert_move("&")
                self.move_handlers['remove'](deletion_move)
                self.move_handlers['and'](and_move)

        # Implement the logic for handling regular moves
        # mv = chess.Move.from_uci(from_square + to_square)

        # Move recorded 2
        # san_version = self.board.san(mv)
        # print(f"This move is called {san_version}")
        # button_label = str(san_version)
        # print(f"BUTTON: {button_label}")

        #self.board.push(mv)

        # prefix = piece.upper() if piece not in self.pawn_pieces else ""
        prefix = self.to_san(from_square, to_square)
        fake_san_version = prefix

        self.move_piece(from_square, to_square)
        self.add_this_fen()

        #fake_san_version = prefix+move['from']+move['to']

        return fake_san_version, self.fen

    def handle_promotion(self, move):
        """e.g. {'type': 'promotion', 'from': 'a7', 'to': 'a8', 'promotion_piece': 'Q'}
        If move is promotion do same as move but add all three parts
        """

        from_square = Square.get(alg=move['from'])
        to_square = Square.get(alg=move['to'])

        promotion_piece = move['promotion_piece'].upper() # Standardize always to uppercase

        # Move recorded
        #print(f"Promotion move from {from_square.alg} to {to_square.alg} promoting to {promotion_piece}")

        # Implement the logic for handling promotion

        piece = self.get_piece(from_square)
        target_piece = self.get_piece(to_square)

        if piece is None:
            print("Uhm, there was meant to be a piece here!")
            return None, None

        piece_color = self.get_piece_colour(piece)
        target_piece_color = self.get_piece_colour(target_piece) if target_piece else None

        if piece_color != self.turn and piece_color != 'neutral':
            print("You moved out of turn, but I'll allow it.")
            self.change_turn()

        if target_piece is not None:
            if piece_color == target_piece_color:
                print("You're trying to consume one of your own pieces. I'll allow it.")
                deletion_move = self.convert_move("-" + to_square.alg)
                and_move = self.convert_move("&")
                self.move_handlers['remove'](deletion_move)
                self.move_handlers['and'](and_move)

        #mv = chess.Move.from_uci(from_square + to_square + promotion_piece.lower())

        # Move recorded 2
        #san_version = self.board.san(mv)
        # print(f"This move is called {san_version}")
        #button_label = str(san_version)
        # print(f"BUTTON: {button_label}")
        #self.board.push(mv)

        prefix = self.to_san(from_square, to_square)
        fake_san_version = prefix + promotion_piece.upper()

        self.promote_pawn(from_square, to_square, promotion_piece)
        self.add_this_fen()

        #fake_san_version = move['from'] + move['to'] + promotion_piece.lower()

        return fake_san_version, self.fen

    def handle_save(self, _):
        """ e.g. {'type': 'save'}
        elif the move is to add a checkpoint then:
            add locally save the checkpoint FEN (and keep previous checkpoint)
            save "SaveCheckpoint" into the list
            also save current FEN into the list
        """

        # Move recorded
        print("Saving current position")
        # Implement the logic for saving the current position

        # Remove any future checkpoints if we are not at the end
        self.checkpoints = self.checkpoints[:self.current_checkpoint_index + 1]

        # Save the current position
        self.checkpoints.append(self.fen)

        # Update the current checkpoint index
        self.current_checkpoint_index = len(self.checkpoints) - 1

        # Won't store facts about checkpoints into generated for now, just fens
        # self.generated.append("SaveCheckPoint")
        # Don't need to add a FEN since we already added it? could revisit

        return "*", self.current_checkpoint_index

    def handle_home(self, _):
        """ e.g. {'type': 'home'} """

        # Move recorded
        print("Returning to home position")
        # Implement the logic for returning to the home position
        self.current_checkpoint_index = 0
        self.set_fen(self.checkpoints[self.current_checkpoint_index])
        self.add_this_fen()  # Save the fen to the generated list

        return "H", self.current_checkpoint_index

    def handle_skipback(self, move):
        """ e.g. {'type': 'skipback', 'steps': n} """

        distance = move['steps']
        # Move recorded
        print(f"Skipping back {distance} level(s)")
        # Implement the logic for skipping back
        self.current_checkpoint_index = max(0, self.current_checkpoint_index - distance + 1)
        self.set_fen(self.checkpoints[self.current_checkpoint_index])
        self.add_this_fen()  # Save the fen to the generated list
        # print(self.board)

        return "back", self.current_checkpoint_index

    def handle_and(self, _):
        """{'type': 'and'} """
        # Move recorded
        print(f"...playing another move at the same time...")
        print(f"BUTTON: save current button text for appending next move")
        self.generated.pop()  # This should remove the last element
        self.id_record.pop()  # Copy same behaviour on move_id
        self.move_id -= 1

        return "&", None

    def handle_add(self, move):
        """ {'type': 'add', 'piece': 'B', 'to': 'e5'} """
        to_square = Square.get(alg=move['to'])
        added_piece_symbol = move['piece']

        # Move recorded
        print(f"Add piece ({added_piece_symbol}) to {to_square.alg}")
        button_label = "+" + str(added_piece_symbol) + str(to_square.alg)
        #print(f"BUTTON: {button_label}")

        # Implement the logic for handling capture
        #self.board.set_piece_at(chess.parse_square(to_square), chess.Piece.from_symbol(added_piece))
        self.add_piece(to_square, added_piece_symbol)
        self.add_this_fen()  # Save the fen to the generated list

        return button_label, self.fen

    def handle_remove(self, move):
        """ {'type': 'remove', 'from': 'a1'} """

        from_square = Square.get(alg=move['from'])

        piece_there = self.get_piece(from_square)
        # this is the internal piece name     
        true_piece = Piece.get(piece_there)  # This is the piece (so we can use user_char later)

        if piece_there is None:
            print(f"No piece found at {from_square} to remove!")
            return None, None

        # Move recorded
        print(f"Removing piece from {from_square.alg}")
        button_label = "-" + str(true_piece.user_char) + str(from_square.alg)
        #print(f"BUTTON: {button_label}")

        # Implement the logic for removing a piece
        #self.board.remove_piece_at(chess.parse_square(from_square))

        self.remove_piece(from_square)
        self.add_this_fen()

        return button_label, self.fen

    def handle_set_whos_turn(self, move):
        """e.g. {'type': 'player_turn', 'player': 'B'}
        Request to set whose turn it is
        """
        player_to_move = move['player']
        current_turn = "W" if self.turn == 'w' else "B"  # Find whos turn it current is
        if player_to_move != current_turn:
            # Target player to move means we need to change
            self.change_turn()
            self.add_this_fen()

        return str(player_to_move), None

    def result(self):
        return self.generated, self.id_record

    @staticmethod
    def convert_move(move: str) -> dict[str, str | int]:
        """
        Function to convert different types of move strings to a structured representation.
        Each case will be converted into an appropriate format (e.g., tuple or dict).
        """

        # Case a: letter-number-letter-number (e.g. a1e5) possibly ending +, ++ or #
        if re.fullmatch(r'[a-h][1-8][a-h][1-8](\+{1,2}|#)?$', move):
            move = move.rstrip('+#')  # Strips any + or # at the end
            # This matches a format like 'a1e5'
            return {'type': 'move', 'from': move[:2], 'to': move[2:]}

        # Case b: letter-number-letter-number-letter (e.g. a7a8Q), where last letter is one of prsbQPRSBQ
        # possibly ending +, ++ or #
        elif re.fullmatch(r'[a-h][1-8][a-h][1-8][rbsqkRBSQK](\+{1,2}|#)?$', move):
            move = move.rstrip('+#')  # Strips any + or # at the end
            # This matches a format like 'a7a8Q' with a valid promotion piece
            return {'type': 'promotion', 'from': move[:2], 'to': move[2:4], 'promotion_piece': move[4].lower()}

        # Case c: the string "*" means save checkpoint
        elif move == "*":
            return {'type': 'save'}

        # This case allow multiple moves to be simultaneous
        elif move == "&":
            return {'type': 'and'}  # Plan is to read next move and overwrite, not advancing the tree

        # Case d: the string "H" means return to home
        elif move == "H":
            return {'type': 'home'}

        # Case: setting whose turn it is to move
        elif move in ("W", "B"):
            return {'type': 'player_turn', 'player': move}

        # Case e: a string of consecutive < symbols, e.g. <<< or <
        elif re.fullmatch(r'<+', move):  # any number of < symbols
            return {'type': 'skipback', 'steps': len(move)}

        # Case f: string "+letter-letter-number" (e.g. +Rb2)
        elif re.fullmatch(r'^\+([prnbqPRNBQ])[a-h][1-8]$', move):
            # This matches a format like '+Rb2'
            return {'type': 'add', 'piece': move[1], 'to': move[2:]}
        
        # Case f SPECIAL NEW: '+ANYTHINGa1' format (e.g. +Rb2, +=qh5, +.l2g4
        elif re.fullmatch(r'^\+.+[a-h][1-8]$', move):
            # Extract piece and destination square -- allows for multicharacter pieces
            square = move[-2:]           # Last two chars are the square
            piece = move[1:-2]           # All between '+' and square is the piece
            return {'type': 'add', 'piece': piece, 'to': square}

        # Case g: string "-letter-number" (e.g. -e4)
        elif re.fullmatch(r'^-[a-h][1-8]$', move):
            # This matches a format like '-e4'
            return {'type': 'remove', 'from': move[1:]}

        else:
            return {'type': 'invalid', 'move': move}

def print_board_matrix(board, empty_square_char='.'):
    for row in board:  # print rank 8 to 1
        print(' '.join(empty_square_char if cell == '1' else cell for cell in row))
    print()

## Test worker

# def worker(container, result_q):
#     current = container.get_current()
#     result = {
#         "id": current.id,
#         "piece_count": len(current.fen.replace("/", "").replace("1", "")),  # crude count
#     }
#     result_q.put(result)

# --- Main Program ---

# if __name__ == '__main__':
#     container = ProblemListContainer()
#     container.add_composition("Silly problem", "8/8/8/8/8/8/8/K6k", [], "mate in 1")
#     container.add_composition("Silly problem", "8/8/8/8/8/R7/8/K6k", [], "mate in 2")
#     container.add_composition("Silly problem", "8/8/1ppppp1p/8/8/8/8/K6k", [], "mate in 3")
#     container.set_current(3)
#
#     result_q = Queue()
#     p = Process(target=worker, args=(container, result_q))
#     p.start()
#     p.join()
#
#     result = result_q.get()
#     print(f"Worker result: {result}")



