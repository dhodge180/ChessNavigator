import pygame
import chess
import chess.pgn
import argparse
from pyperclip import copy

import os
import sys

# Global variable to hold the FEN list
FEN_LIST = []

def load_fen_list_from_file(filename="FEN_LIST.txt"):
    """Load FENs, their titles and stipulations from an external file.
    lots of case handling, only FEN is strictly necessary"""

    if not os.path.exists(filename):
        print(f"File {filename} not found.")
        return False

    with open(filename, "r") as file:
        lines = file.readlines()

    temp_fen_data = {"stip": ""}
    for line in lines:
        line = line.strip()  # Remove leading/trailing whitespaces

        # We encounter a Title
        if line.startswith("Title:"):
            if "title" in temp_fen_data: # We already have a title!
                if "fen" not in temp_fen_data: # Second title, no FEN yet. Stupid.
                    # Total reset and save new title
                    temp_fen_data = {"title": line[len("Title:"):].strip().strip('"'), "stip": ""}
                elif "fen" in temp_fen_data: # We have a FEN already
                    # Save entry immediately (possibly with Subtext)
                    FEN_LIST.append(temp_fen_data)
                    # Start next entry
                    temp_fen_data = {"title": line[len("Title:"):].strip().strip('"'), "stip": ""}
            elif "title" not in temp_fen_data: # Currently no title
                temp_fen_data["title"] = line[len("Title:"):].strip().strip('"')

        # We encounter a fen
        elif line.startswith("FEN:"):
            if "fen" in temp_fen_data: # We already have a fen!
                if "title" not in temp_fen_data: # No title yet!
                    # Okay, just a pure FEN is fine
                    temp_fen_data["title"] = "" # Insert blank title
                    FEN_LIST.append(temp_fen_data) # Save (possibly with subtext)
                    # Start new entry
                    temp_fen_data = {"fen": line[len("FEN:"):].strip().strip('"'), "stip": ""}
                elif "title" in temp_fen_data: # We have a title already
                    # Save entry immediately (possibly with Subtext)
                    FEN_LIST.append(temp_fen_data)
                    # Start new entry
                    temp_fen_data = {"fen": line[len("FEN:"):].strip().strip('"'), "stip": ""}
            elif "fen" not in temp_fen_data: # We don't have a fen yet
                temp_fen_data["fen"] = line[len("FEN:"):].strip().strip('"')

        # We encounter a Subtext
        elif line.startswith("Subtext:"):
            if temp_fen_data["stip"] != "": # We already have a stip!
                print("Error. Already have a stipulation, overwriting.")
            # Storing subtext (possible overwrite with above warning)
            temp_fen_data["stip"] = line[len("Subtext:"):].strip().strip('"')
            # No need to save yet. If end of file we'll save later

        # We encounter a blank line
        elif line == "": # a blank line
            # Assume this separates problems
            if "fen" in temp_fen_data: # at least we have a fen
                if "title" not in temp_fen_data: # but no title
                    temp_fen_data["title"] = ""  # Insert blank title
                # Save entry (possible with blank stip
                FEN_LIST.append(temp_fen_data)
                # Wipe it clean for next entry
                temp_fen_data = {"stip": ""}
            elif "fen" not in temp_fen_data: # not even a fen
                print("Disregarding this entry without even a FEN")
                # Wipe it clean for next entry
                temp_fen_data = {"stip": ""}

    # Finished reading all lines
    # Need to save final entry, assuming it has at least a fen
    if "fen" in temp_fen_data:
        FEN_LIST.append(temp_fen_data)

    # Print when FENs are loaded
    print(f"Loaded {len(FEN_LIST)} FENs from {filename}.")

    # Detail the loaded list of FENS
    for fen_data in FEN_LIST:
        print(fen_data)
        print(f"Title: {fen_data['title']}, FEN: {fen_data['fen']}", "Stip: {fen_data['stip']}")

    if FEN_LIST:
        print("Successful load from FEN_LIST file")
        return True
    else:
        print("Did not load from FEN_LIST file")
        return False

# Redirect print statements to a file (optional)
if getattr(sys, 'frozen', False):  # Only when running as an executable
    sys.stdout = open('output.log', 'w')
    sys.stderr = sys.stdout

def get_resource_path(relative_path):
    """ Get the correct path for bundled files when running as an executable """
    if getattr(sys, 'frozen', False):
        # If running as a PyInstaller-built executable
        base_path = sys._MEIPASS
    else:
        # If running as a normal Python script
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Example usage
image_path = get_resource_path("images/p.png")
print("Image path:", image_path)

# Constants
BOARD_SIZE = 8
SQUARE_SIZE = 107  # 107 is exact png sizes, scaling can cause artifacts
BOARD_WIDTH = SQUARE_SIZE * BOARD_SIZE
BORDER_SIZE = 60
PANEL_WIDTH = 250
PANEL_GAP = 0
MOVES_WIDTH = 50
HEIGHT_PADDING = 5

WIDTH = BOARD_WIDTH + PANEL_WIDTH + 2 * BORDER_SIZE + MOVES_WIDTH  # Extra for border + panel
HEIGHT = BOARD_WIDTH + 2 * BORDER_SIZE + 2 * HEIGHT_PADDING # Extra for border
WHITE = (238, 238, 210)
BLACK = (118, 150, 86)
TRUE_BLACK = (0, 0, 0)
PANEL_COLOR = (20, 60, 60)

# Highlighting colours
RED_HIGHLIGHT = (240, 128, 128)    # Light Coral (soft red)
YELLOW_HIGHLIGHT = (255, 223, 128)  # Pastel Yellow
GREEN_HIGHLIGHT = (144, 238, 144)   # Light Green (muted)

KEY_COLOR_MAP = {
    pygame.K_1: RED_HIGHLIGHT,
    pygame.K_2: YELLOW_HIGHLIGHT,
    pygame.K_3: GREEN_HIGHLIGHT,
    pygame.K_0: None
}

# FEN position to start from
START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 0"

# Load chess pieces
def load_images():
    pieces = {}
    for piece in ['p', 'n', 'b', 'r', 'q', 'k']:
        img_path = get_resource_path(f'images/b{piece.upper()}.png')
        img_black = pygame.image.load(img_path)
        pieces[piece] = pygame.transform.scale(img_black, (SQUARE_SIZE, SQUARE_SIZE))  # Scale to fit squares

        img_path = get_resource_path(f'images/w{piece.upper()}.png')
        img_white =  pygame.image.load(img_path)
        pieces[piece.upper()] = pygame.transform.scale(img_white, (SQUARE_SIZE, SQUARE_SIZE))  # Scale for white pieces
    return pieces

def parse_arguments():
    """Parses command-line arguments for optional FEN input."""
    parser = argparse.ArgumentParser(description="Chess game with optional FEN input and Window title.")
    parser.add_argument("--fen", type=str, help="Custom starting position in FEN format.")
    parser.add_argument("--title", type=str, default="", help="Set the problem title")
    parser.add_argument("--stip", type=str, default="", help="Set the problem stipulation")
    parser.add_argument("--fenlist", type=str, help="Path to the FEN list file", default="FEN_LIST.txt")
    return parser.parse_args()

class ChessGame:
    def __init__(self, fen=None):
        self.board = chess.Board()
        self.start_pos = START_FEN
        self.clock = pygame.time.Clock()
        if fen:
            self.start_pos = fen
            try:
                self.board.set_fen(self.start_pos)
                print("Loaded custom FEN position.")
            except ValueError:
                print("Invalid FEN! Using default starting position.")
        self._initialize_game_state()

    def _initialize_game_state(self):
        """Common setup method for initializing or resetting the game state."""
        self.legal_moves_enabled = True
        self.move_history = []  # Reset move history
        self.moves = chess.pgn.Game()  # Reset PGN game
        self.node = self.moves  # Reset PGN node pointer

    def set_new_fen(self, new_fen):
        """Updates the board with a new FEN and resets move history & PGN tracking."""
        try:
            self.board.set_fen(new_fen)
            self.start_pos = new_fen
            self._initialize_game_state()  # Reset game state
            print(f"New FEN set: {new_fen}")
        except ValueError:
            print("Invalid FEN! Keeping the current position.")

    def redefine_start(self):
        """This forces the current board position to become the reset state"""
        self.start_pos = self.board.fen()

    def clear_board(self):
        self.board.clear()

    def add_real_move(self, move):
        # self.node = self.node.add_variation(move)
        self.move_history.append(("move", move))

    def get_pgn(self):
        pgn = str(self.moves)

        # Remove headers
        pgn_lines = pgn.splitlines()[8:]

        #Re join remaining lines
        return '\n'.join(pgn_lines)

    def move_piece(self, start, end):
        move = chess.Move.from_uci(start + end)
        print("Trying to move", move)

        # Case 1: Legal moves are enabled
        if self.legal_moves_enabled:
            piece = self.board.piece_at(chess.parse_square(start))

            # Check if it's a pawn and it's reaching the promotion rank
            if piece.piece_type == chess.PAWN:
                print("It's a pawn!")
                promotion_rank = 7 if piece.color == chess.WHITE else 0
                print("Promotion rank for such pieces is", promotion_rank)
                if chess.square_rank(chess.parse_square(end)) == promotion_rank:
                    # This is a promotion move, set promotion piece before legal move check
                    print("It's a promotion attempt")
                    promotion_piece = self.ask_for_promotion() # Don't need to pass colour, move.promotion won't care
                    move.promotion = promotion_piece  # Set the promotion piece

            # Now check if it's a legal move, including any promotion
            if move in self.board.legal_moves:
                _ = self.board.push(move)
                self.add_real_move(move)

            else:
                print("Move not legal!")

        else:
            print("Not a legal move!")
            # Handle non-legal moves (when legal moves are disabled)
            # This can be a custom behavior or just a bypass depending on your needs
            piece = self.board.piece_at(chess.parse_square(start))
            if piece is None:
                return  # No piece to move

            original_turn = self.board.turn  # Store the current turn
            piece_color = piece.color  # Get the color of the moving piece

            # Temporarily switch the turn to match the piece's color
            if piece_color != original_turn:
                self.board.turn = piece_color

            self.board.push(move)  # Perform the move
            self.add_real_move(move)
            #self.move_history.append(("move", move))

            # Restore the original turn
            self.board.turn = original_turn

    def ask_for_promotion(self):
        """Waits for the user to press a key to select a promotion piece."""
        # Available pieces for promotion
        promotion_pieces = {
            'Q': chess.QUEEN,
            'R': chess.ROOK,
            'B': chess.BISHOP,
            'N': chess.KNIGHT
        }

        pygame.display.flip()  # Update the display

        running = True
        selected_piece = None

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        selected_piece = promotion_pieces['Q']
                        running = False
                    elif event.key == pygame.K_r:
                        selected_piece = promotion_pieces['R']
                        running = False
                    elif event.key == pygame.K_b:
                        selected_piece = promotion_pieces['B']
                        running = False
                    elif event.key == pygame.K_n:
                        selected_piece = promotion_pieces['N']
                        running = False

            self.clock.tick(30)
        return selected_piece

    def undo_move(self):
        if len(self.board.move_stack) == 0:
            # No moves to undo.
            return

        if len(self.move_history) > 0:
            last_move = self.move_history.pop()

            if last_move[0] == "move":
                # Undo a normal move
                self.board.pop()

            elif last_move[0] == "add_piece":
                # Undo a piece addition
                piece_symbol, square, removed_piece = last_move[1]
                self.board.set_piece_at(square, removed_piece)  # Restore previous piece
            else:
                raise ValueError("Unknown move type in history")

    def reset_board(self):
        self.board.set_fen(self.start_pos)
        self.move_history = []

    def add_piece(self, piece_symbol, square):
        """Add a piece from the panel to the board and record the action for undo."""
        # Save the current piece at the square (None if empty)
        current_piece = self.board.piece_at(square)

        # Add the new piece
        self.board.set_piece_at(square, chess.Piece.from_symbol(piece_symbol))

        # Add null move
        self.board.push(chess.Move.null())
        self.board.push(chess.Move.null())

        # Add the move to history (recording the type of action)
        self.move_history.append(("add_piece", (piece_symbol, square, current_piece)))
        # Cannot add this to the PGN!

    def toggle_turn(self):
        """Toggles the turn by making a null move."""
        self.board.push(chess.Move.null())

class ChessGUI:
    def __init__(self, fen=None, title='Chess Navigator', stip = "", fenlist = False):
        self.spare_pieces = None
        pygame.init()
        self.fenlist = fenlist # True/False on whether a fenlist was loaded
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption('Chess Navigator')
        self.pieces = load_images()
        self.game = ChessGame(fen)
        self.running = True
        self.dragging_piece = None
        self.dragging_pos = (0, 0)
        self.dragging_square = None
        self.piece_source = None  # Track if dragging from board or panel
        self.setup_spare_pieces()
        self.clock = pygame.time.Clock()
        #self.set_window_title('Chess Navigator')

        # Calculate board colours initially
        self.square_colors = self.precalculate_square_colors()
        self.TRUE_COLORS = [row[:] for row in self.square_colors] # New copy of list

        # Add custom title inside the window
        self.font = pygame.font.SysFont("Arial", 30)  # Change font and size here
        self.custom_title = title  # Or any other dynamic title based on your logic
        self.custom_stip = stip

        # If no fen was passed but a FEN_LIST exists. Then start the F1 cycle early
        if fen is None and self.fenlist:
            self.cycle_fen()

        self.draw_custom_title()
        self.draw_custom_stip()

    #@staticmethod
    #def set_window_title(title):
    #    pygame.display.set_caption(title)

    def draw_custom_title(self):
        """Draw the custom title at the top of the window."""
        title_surface = self.font.render(self.custom_title, True, (255, 255, 255))  # White color
        title_rect = title_surface.get_rect(center=(BOARD_WIDTH // 2 + BORDER_SIZE, BORDER_SIZE // 2 ))  # Adjust position as needed
        self.screen.blit(title_surface, title_rect)

    def draw_custom_stip(self):
        """Draw the custom title at the top of the window."""
        title_surface = self.font.render(self.custom_stip, True, (255, 255, 255))  # White color
        title_rect = title_surface.get_rect(center=(BOARD_WIDTH // 2 + BORDER_SIZE, HEIGHT - HEIGHT_PADDING - BORDER_SIZE // 2))  # Adjust position as needed
        self.screen.blit(title_surface, title_rect)

    def draw_pgn_panel(self):
        """Draws the PGN panel on the right side of the screen."""
        font = pygame.font.Font(None, 24)  # Font for the PGN text
        #pgn = self.game.get_pgn()  # Get the PGN from the game
        #print(pgn)

        # Create the text surface with the PGN
        text_surface = font.render("", True, (255, 255, 255))  # White text

        # Set the location for the panel (on the right side of the screen)
        panel_x = WIDTH - MOVES_WIDTH
        panel_y = 0  # Start from top with some margin

        # Draw the background for the panel
        pygame.draw.rect(self.screen, (0, 0, 0), (panel_x, panel_y, MOVES_WIDTH, HEIGHT))

        # Draw the PGN text in the panel
        self.screen.blit(text_surface, (panel_x + 10, panel_y+10))  # 10px margin inside the panel

    def get_legality_text(self):
        """Returns the legality text surface and its rectangle for positioning."""
        font = pygame.font.Font(None, 24)  # Smaller text
        text = "Legality: ON" if self.game.legal_moves_enabled else "Legality: OFF"
        color = (0, 255, 0) if self.game.legal_moves_enabled else (255, 0, 0)

        text_surface = font.render(text, True, color)
        text_x = WIDTH - MOVES_WIDTH - text_surface.get_width() - 10  # Align to top-right
        text_y = 10  # Small margin from top
        text_rect = text_surface.get_rect(topleft=(text_x, text_y))

        return text_surface, text_rect

    def draw_legality_mode(self):
        """Displays legality mode in the top-right corner, smaller size."""
        y_margin = 10
        x_margin = 10
        text_surface, _ = self.get_legality_text()
        x_left = BOARD_WIDTH + 2 * BORDER_SIZE + PANEL_WIDTH - text_surface.get_width()
        self.screen.blit(text_surface, (x_left - x_margin, y_margin))

    def check_legal_toggle_click(self, pos):
        """Check if the legality label was clicked and toggle legality mode."""
        _, text_rect = self.get_legality_text()

        if text_rect.collidepoint(pos):
            self.game.legal_moves_enabled = not self.game.legal_moves_enabled

    def draw_turn_indicator(self):
        """Draws the turn indicator circle in the bottom-right corner."""
        # Determine whose turn it is (White or Black)
        turn_color = WHITE if self.game.board.turn else TRUE_BLACK  # True = White's turn, False = Black's turn

        # Coordinates for the bottom-right corner
        circle_radius = 20
        circle_x = BOARD_WIDTH + 2 * BORDER_SIZE + PANEL_WIDTH / 2  #- circle_radius # Half-way through panel
        circle_y = HEIGHT - BORDER_SIZE/2 - circle_radius - 10  # 10px margin from the border

        # Draw the circle representing the current turn
        pygame.draw.circle(self.screen, turn_color, (circle_x, circle_y), circle_radius)

    def precalculate_square_colors(self):
        """Perform start of program board colour calculations"""
        square_colors = []
        for row in range(BOARD_SIZE):
            row_colors = []
            for col in range(BOARD_SIZE):
                color = self.get_default_color(row, col)
                row_colors.append(color)
            square_colors.append(row_colors)
        return square_colors

    @staticmethod
    def get_default_color(row, col):
        color = WHITE if (row + col) % 2 == 0 else BLACK
        return color

    def draw_board(self):
        """Draws the chessboard inside the border."""
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                # color = WHITE if (row + col) % 2 == 0 else BLACK
                color = self.square_colors[row][col]
                pygame.draw.rect(
                    self.screen, color,
                    (BORDER_SIZE + col * SQUARE_SIZE, BORDER_SIZE + HEIGHT_PADDING + row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                )

    def draw_pieces(self):
        """Draws pieces inside the board with border offset."""
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                square = chess.square(col, 7 - row)
                piece = self.game.board.piece_at(square)
                if piece and (self.dragging_square != square):
                    img = self.pieces[piece.symbol()]
                    self.screen.blit(img, (BORDER_SIZE + col * SQUARE_SIZE, BORDER_SIZE + HEIGHT_PADDING + row * SQUARE_SIZE))

        # Draw dragged piece on top
        if self.dragging_piece:
            self.screen.blit(self.dragging_piece, self.dragging_pos)

    def setup_spare_pieces(self):
        """Defines positions for the spare pieces on the panel."""
        self.spare_pieces = []
        piece_order = ['K', 'Q', 'R', 'B', 'N', 'P']  # Display order
        for i, piece in enumerate(piece_order):
            # Place white pieces on the left side of the panel
            self.spare_pieces.append((piece, (PANEL_WIDTH*0.1, 50 + i * (SQUARE_SIZE+20))))  # White pieces (x offset is 10% of panel)
            # Place black pieces on the right side of the panel
            self.spare_pieces.append((piece.lower(), (PANEL_WIDTH*0.1+SQUARE_SIZE, 50 + i * (SQUARE_SIZE+20))))  # Black pieces (x offset is 10% of panel)


    def draw_panel(self):
        # Move the panel to the right to avoid overlapping with the board
        panel_x = BOARD_WIDTH + 2 * BORDER_SIZE + PANEL_GAP  # Adjusted position
        pygame.draw.rect(self.screen, PANEL_COLOR, (panel_x, 0, PANEL_WIDTH, HEIGHT))

        # Draw spare pieces in the new panel position
        for piece, pos in self.spare_pieces:
            # Draw the piece at the correct adjusted position inside the panel
            img = self.pieces[piece]
            self.screen.blit(img, (panel_x + pos[0], pos[1]))  # Add panel_x to position the pieces correctly

    @staticmethod
    def get_square_under_mouse(pos):
        """Converts the mouse click position to a square on the board."""
        x, y = pos
        # Adjust for the border offset
        x -= BORDER_SIZE
        y -= BORDER_SIZE + HEIGHT_PADDING

        if x < 0 or y < 0:  # Outside the board
            return None

        # Check if the click is within the board area (8x8 grid)
        if x < BOARD_WIDTH and y < BOARD_WIDTH:
            col = x // SQUARE_SIZE
            row = y // SQUARE_SIZE
            return chess.square(col, 7 - row)  # Convert to chess square notation

        return None  # If outside the board

    def change_square_color(self, chess_square, new_color):
        """Receives the square under the mouse (0 to 63) and changes colour in the colour vector"""
        row = 7 - chess.square_rank(chess_square)
        col = chess.square_file(chess_square)

        if new_color is not None:
            self.square_colors[row][col] = new_color
        else:
            # Reset to original
            self.square_colors[row][col] = self.get_default_color(row, col)

    def get_piece_from_panel(self, pos):
        """Check if user clicks on a spare piece."""
        # The panel_x was calculated with the PANEL_GAP, so we need to adjust this here
        panel_x = BOARD_WIDTH + 2 * BORDER_SIZE + PANEL_GAP

        for piece, piece_pos in self.spare_pieces:
            px, py = piece_pos
            if panel_x + px <= pos[0] <= panel_x + px + SQUARE_SIZE and py <= pos[1] <= py + SQUARE_SIZE:
                return piece
        return None

    def handle_mouse_down(self, pos):

        self.check_legal_toggle_click(pos)

        square = self.get_square_under_mouse(pos)
        panel_piece = self.get_piece_from_panel(pos)

        if panel_piece:
            self.dragging_piece = self.pieces[panel_piece]
            self.piece_source = "panel"
            self.dragging_pos = pos
            self.dragging_square = panel_piece
        elif square is not None:
            piece = self.game.board.piece_at(square)
            if piece:
                self.dragging_piece = self.pieces[piece.symbol()]
                self.piece_source = "board"
                self.dragging_square = square
                self.dragging_pos = (pos[0] - SQUARE_SIZE // 2, pos[1] - SQUARE_SIZE // 2)

    def handle_mouse_motion(self, pos):
        if self.dragging_piece:
            self.dragging_pos = (pos[0] - SQUARE_SIZE // 2, pos[1] - SQUARE_SIZE // 2)

    def handle_mouse_up(self, pos):
        """Handles dropping a piece, ensuring its color is preserved."""
        if self.dragging_piece:
            new_square = self.get_square_under_mouse(pos)

            if self.piece_source == "board" and new_square is not None:
                if new_square != self.dragging_square:  # Move only if dropped in a new square
                    self.game.move_piece(chess.square_name(self.dragging_square), chess.square_name(new_square))


            elif self.piece_source == "panel" and new_square is not None:
                # Add the piece to the board and record the action for undo
                piece_symbol = self.dragging_square  # This is the symbol of the piece being dragged
                self.game.add_piece(piece_symbol, new_square)

            # Reset dragging state
            self.dragging_piece = None
            self.dragging_square = None
            self.piece_source = None

    def run(self):
        """Main loop of the GUI."""
        low_fps = 25
        high_fps = 60
        self.target_fps = low_fps

        while self.running:
            self.screen.fill((0, 0, 0))
            self.draw_board()
            self.draw_pieces()
            self.draw_panel()
            self.draw_legality_mode()  # Show legality mode status
            self.draw_turn_indicator()
            self.draw_pgn_panel()
            self.draw_custom_title()
            self.draw_custom_stip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.adjust_fps(high_fps)
                    self.handle_mouse_down(event.pos)
                elif event.type == pygame.MOUSEMOTION:
                    self.handle_mouse_motion(event.pos)
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.adjust_fps(low_fps)
                    self.handle_mouse_up(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_l:
                        self.game.legal_moves_enabled = not self.game.legal_moves_enabled  # Toggle legality mode
                    elif event.key == pygame.K_u:
                        self.game.undo_move() # Press u to undo last move
                    elif event.key == pygame.K_z:
                        self.game.clear_board() # Press z to zero/clear the board
                    elif event.key == pygame.K_INSERT:
                        self.game.redefine_start() # Press INSERT to redefine root position
                    elif event.key == pygame.K_HOME:
                        self.game.reset_board() # Press HOME to return to root position
                    elif event.key == pygame.K_t:
                        self.game.toggle_turn()  # Toggle the turn on pressing 'T'
                    elif event.key == pygame.K_F1:  # Press F1 to load next fen from FEN_LIST
                        if self.fenlist:
                            self.cycle_fen()
                    # Square highlighting
                    elif event.key in KEY_COLOR_MAP: # Presses 1 or 2 or 3 to add a square highlight
                        pos = pygame.mouse.get_pos()
                        square = self.get_square_under_mouse(pos)
                        #print(f"Square is {square}")
                        if square is not None:
                            self.change_square_color(square, KEY_COLOR_MAP[event.key])
                    elif event.key == pygame.K_DELETE: # Pressed 0 to clean all highlights
                        # Reset all colours, recopy from TRUE_COLORS
                        self.square_colors = [row [:] for row in self.TRUE_COLORS]
                    # Copy FEN to clipboard
                    if event.key == pygame.K_c and (
                            pygame.key.get_pressed()[pygame.K_LCTRL] or pygame.key.get_pressed()[pygame.K_RCTRL]):
                        # Get FEN from the board and copy it to clipboard
                        try:
                            fen = self.game.board.fen()  # Call the board.fen() method from the ChessGame instance
                            copy(fen)  # Copy the FEN to clipboard
                            print("FEN copied to clipboard:", fen)  # Optional: print to console for confirmation
                        except Exception as e:
                            print(f"Error copying FEN to clipboard: {e}")

            pygame.display.flip()
            # print(f"Starting clock at {target_fps}")
            self.clock.tick(self.target_fps)

    def cycle_fen(self):
        """Cycle through the FEN list and update the game and window title."""

        # Get the current FEN and title
        current_fen_data = FEN_LIST.pop(0)  # Get first element
        FEN_LIST.append(current_fen_data)  # Move it to the end for the next cycle

        new_fen = current_fen_data["fen"]
        new_title = current_fen_data["title"]
        subtext = current_fen_data["stip"]

        # Update the game and window title
        self.game.set_new_fen(new_fen)
        self.custom_title = new_title
        self.custom_stip = subtext
        self.draw_custom_title()
        self.draw_custom_stip()

    def adjust_fps(self, new_fps):
        self.target_fps = new_fps

if __name__ == "__main__":
    args = parse_arguments()  # Get arguments from command line
    passed_fen = args.fen if args.fen else None  # Use FEN if provided, otherwise default
    passed_fenlist = args.fenlist if args.fenlist else None
    fen_list_loaded = load_fen_list_from_file(passed_fenlist) # default is FEN_LIST.txt but user could customize
    # Return value is TRUE or FALSE based on success

    ChessGUI(passed_fen, title=args.title, stip=args.stip, fenlist=fen_list_loaded).run()  # Pass the FEN to the GUI and the Window title



