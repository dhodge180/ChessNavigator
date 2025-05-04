"""
This is the main Chess Navigator program
"""

import pygame
import chess
#import chess.pgn
import argparse

from pyperclip import copy
import re
import json

import os
import sys

# For moves window
import tkinter as tk
import multiprocessing

# Define the shutdown event
shutdown_event = multiprocessing.Event()

# Passable references to windows
#main_window = None
#moves_windows = None

# Global variable to hold the PROBLEM LIST
# PROBLEM_LIST = []

# Global for fancy multiprocessing mode
# MOVES_WINDOW_VERSION = None

class Config:

    # Default configuration values -- can be changes by config.json
    DEFAULTS = {
        "white_squares": (238, 238, 210),
        "black_squares": (118, 150, 86),
        "panel_colour": (20, 60, 60),
        "square_size": 70,
        "title_font_size": 28,
        "stip_font_size": 28
    }

    # Customizable
    WINDOW_WIDTH = 800
    WINDOW_HEIGHT = 800

    MAIN_HEIGHT = 0
    MAIN_WIDTH = 0

    HEIGHT = 0
    WIDTH = 0

    BOARD_WIDTH = 0
    PANEL_WIDTH = 0

    BOARD_AND_PANEL_WIDTH = 0
    stip_x = 0
    stip_y = 0
    STIP_COORDS = (stip_x, stip_y)
    title_x = 0
    title_y = 0
    TITLE_COORDS = (title_x, title_y)
    title_font_size = 10
    stip_font_size = 10

    # Customizable
    WHITE_SQUARES = (238, 238, 210)
    BLACK_SQUARES = (118, 150, 86)
    PANEL_COLOUR = (20, 60, 60)
    SQUARE_SIZE = 70

    # Genuine fixed
    HEIGHT_PADDING = 5
    BORDER_SIZE = 60
    MOVES_WIDTH = 0
    config_path = "config.json"

    # Global constants for speed
    BOARD_SIZE = 8
    TURN_WHITE = (255, 255, 255) # Used for turn indicator
    TURN_BLACK = (0, 0, 0) # Used for turn indicator

    # FEN position to start from
    START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 0"
    """Default starting position if no PROBLEM_LIST file is found, or specific FEN is passed at CMD line"""

    # Highlighting colours
    RED_HIGHLIGHT = (240, 128, 128)  # Light Coral (soft red)
    """Colour of red square highlight"""
    YELLOW_HIGHLIGHT = (255, 223, 128)  # Pastel Yellow
    """Colour of yellow square highlight"""
    GREEN_HIGHLIGHT = (144, 238, 144)  # Light Green (muted)
    """Colour of green square highlight"""

    KEY_COLOR_MAP = {
        pygame.K_1: RED_HIGHLIGHT,
        pygame.K_2: YELLOW_HIGHLIGHT,
        pygame.K_3: GREEN_HIGHLIGHT,
        pygame.K_0: None
    }
    """Key press / square colour associations"""


    @classmethod
    def set_square_size(cls, new_size):
        """Updates square size and recalculates all dependent values."""
        cls.SQUARE_SIZE = new_size
        cls.update_derived_sizes()

    @classmethod
    def startup(cls, input_path = "config.json"):
        """Three stage startup: load config, derive quantities, check and notify defaults"""

        # STAGE 1

        # These are variables that can be loaded from file
        local_config = cls.DEFAULTS.copy()
        cls.config_path = input_path

        # Load config.json if available
        if os.path.exists(cls.config_path):
            try:
                with open(cls.config_path, "r") as f:
                    user_config = json.load(f)
                    local_config.update(user_config)
            except json.JSONDecodeError as _e:
                print(f"Found config file, but couldn't read it (invalid JSON). Using default settings.")
            except IOError as e:
                print(f"Error reading config file: {e}. Using default settings.")
        else:
            print(f"No config file found at '{cls.config_path}'. Using default settings.")

        # Validate and apply values from the loaded config
        Config.white_squares = Config.validate_rgb(local_config.get("white_squares"))
        """Colour of white squares"""
        Config.black_squares = Config.validate_rgb(local_config.get("black_squares"))
        """Colour of black squares"""
        Config.panel_colour = Config.validate_rgb(local_config.get("panel_colour"))
        """Background colour of panel"""
        Config.square_size = Config.validate_square_size(local_config.get("square_size"))
        """Starting square size"""

        Config.title_font_size = Config.validate_font_size(local_config.get("title_font_size"), min_size=10, max_size=45, font_type="title")
        """For title font size validation"""
        Config.stip_font_size = Config.validate_font_size(local_config.get("stip_font_size"), min_size=10, max_size=45, font_type="stip")
        """For stip font size validation (example if you have stip_font_size in your config)"""

        # STAGE 2

        cls.update_derived_sizes()

        # STAGE 3

        cls.check_and_notify_defaults()

    @classmethod
    def validate_rgb(cls, color):
        #print(f"Info: {color}. Using default value {self.DEFAULTS['white_squares']}.")
        """Validates if a color is a valid RGB tuple/list, otherwise returns the default."""
        if isinstance(color, (tuple, list)) and len(color) == 3:
            # Clamp RGB values to the range 0-255
            return tuple(max(0, min(255, c)) for c in color)
        return cls.DEFAULTS["white_squares"]  # Return the default white color if invalid

    @classmethod
    def validate_square_size(cls, size):
        """Validates the square_size (must be one of 40, 50, ..., 100)."""
        valid_square_sizes = {40, 50, 60, 70, 80, 90, 100}
        if size in valid_square_sizes:
            return size
        return cls.DEFAULTS["square_size"]  # Return the default square_size if invalid
    
    @classmethod
    def validate_font_size(cls, size, min_size=10, max_size=45, font_type="font"):
        """Validates the font size (must be an integer between min_size and max_size, inclusive).
        Rounds down if passed as a float. Falls back to default if invalid.
        
        Args:
            size (int or float): The size to validate.
            min_size (int, optional): The minimum acceptable font size (default is 10).
            max_size (int, optional): The maximum acceptable font size (default is 45).
            font_type (str, optional): The name of the font type (for warning message clarity).
            
        Returns:
            int: The validated font size.
        """
        try:
            size_int = int(float(size))  # Convert to float first to handle decimals, then floor to int
            if min_size <= size_int <= max_size:
                return size_int
            elif size_int > max_size:
                print(f"Warning: {font_type.capitalize()} font size '{size}' is too large. Using {max_size} instead.")
                return max_size
        except (ValueError, TypeError):
            pass

        # If invalid or not in the valid range, fall back to default
        print(f"Warning: Invalid {font_type} font size '{size}'. Using default ({cls.DEFAULTS[f'{font_type}_font_size']}).")
        return cls.DEFAULTS[f"{font_type}_font_size"]

    @classmethod
    def update_derived_sizes(cls):
        """(Re)-Calculates various dimensions based on square_size changes"""

        cls.BOARD_WIDTH = cls.SQUARE_SIZE * cls.BOARD_SIZE
        """Width of just the board"""
        cls.PANEL_WIDTH = 4 * cls.SQUARE_SIZE
        """Side panel with spare pieces (width)"""
        cls.WIDTH = cls.BOARD_WIDTH + cls.PANEL_WIDTH + 2 * cls.BORDER_SIZE + cls.MOVES_WIDTH
        """Full width"""
        cls.HEIGHT = cls.BOARD_WIDTH + 2 * cls.BORDER_SIZE + 2 * cls.HEIGHT_PADDING
        """Full height"""
        cls.MAIN_WIDTH = cls.BOARD_WIDTH + 2 * cls.BORDER_SIZE
        """Width of board with padding"""
        cls.MAIN_HEIGHT = cls.BOARD_WIDTH + 2 * cls.BORDER_SIZE + 2 * cls.HEIGHT_PADDING
        """Height of board with padding"""

        # Text locations
        cls.stip_x = cls.BOARD_WIDTH // 2 + cls.BORDER_SIZE
        cls.stip_y = cls.HEIGHT - cls.HEIGHT_PADDING - cls.BORDER_SIZE // 2
        cls.STIP_COORDS = (cls.stip_x, cls.stip_y)

        cls.title_x = cls.BOARD_WIDTH // 2 + cls.BORDER_SIZE
        cls.title_y = cls.BORDER_SIZE // 2
        cls.TITLE_COORDS = (cls.title_x, cls.title_y)

    @classmethod
    def check_and_notify_defaults(cls):
        """Compares the final values with defaults and notifies the user only if any settings differ from the defaults (i.e., were overridden)."""
        
        overridden_settings = []
        
        # List of config keys to check
        #config_keys = ["white_squares", "black_squares", "panel_colour", "square_size", "title_font_size"]
        
        # Loop through the config keys
        #for key in config_keys:
        for key, default_value in cls.DEFAULTS.items():
            #default_value = cls.DEFAULTS[key]
            current_value = getattr(cls, key)

            # If current value differs from the default, add it to the overridden settings
            if current_value != default_value:
                overridden_settings.append(key)

        # Notify the user if any settings were overridden by user-provided values
        if overridden_settings:
            print(f"Info: The following settings were overridden by the values in your config file: {', '.join(overridden_settings)}.")
        
        # If all values are the same as the defaults, just confirm all is fine
        if not overridden_settings:
            print("All configuration settings were successfully loaded and validated with default values.\n")

def load_problem_list_from_file(PROBLEM_LIST_inload, filename=None):
    """Load FENs, their titles and stipulations from an external file.
    lots of case handling, only FEN is strictly necessary"""

    blank_non_required = {"title": "", "stip": "", "moves": ""}

    if not os.path.exists(filename):
        print(f"File {filename} not found.")
        return False

    with open(filename, "r") as file:
        lines = file.readlines()
        # Ensure final diagram is always processed properly
        lines.append("\n") # Adds a blank line to the end   

    temp_fen_data = blank_non_required.copy()
    
    for line in lines:
        line = line.strip()  # Remove leading/trailing whitespaces

        # We encounter a Title
        if line.startswith("Title:"):
            if temp_fen_data["title"] != "": # We already have a title!
                if "fen" not in temp_fen_data: # Second title, no FEN yet. Stupid.
                    print("Error, second title before FEN. Wiping entry.")
                elif "fen" in temp_fen_data: # We have a FEN already
                    # Save entry immediately (possibly with Subtext)
                    PROBLEM_LIST_inload.append(temp_fen_data)
                    # Total reset and save new title
                # In both cases now reset and save new title
                print("Resetting for next problem...")
                temp_fen_data = blank_non_required.copy()
                # Ready to store new title
            temp_fen_data["title"] = line[len("Title:"):].strip().strip('"')

        # We encounter a fen
        elif line.startswith("FEN:"):
            if "fen" in temp_fen_data: # We already have a fen!
                # Just save it! And start a new one
                PROBLEM_LIST_inload.append(temp_fen_data) # Save (possibly with subtext)
                print("Resetting for next problem...")
                temp_fen_data = blank_non_required.copy()
            
            # Now if we had a fen or didn't, we need to insert the new fen    
            temp_fen_data["fen"] = line[len("FEN:"):].strip().strip('"')

        # We encounter a non-fen (one of "these")
        elif line.startswith("Subtext:"):
            if temp_fen_data["stip"] != "": # We already have one of these
                if "fen" in temp_fen_data: # Great we already have a FEN.
                    PROBLEM_LIST_inload.append(temp_fen_data)
                elif "fen" not in temp_fen_data: # Second one of these, but no FEN yet.
                    print("Error, second Subtext before FEN. Wiping entry.")
                # In both cases now reset and save new one of these
                print("Resetting for next problem...")
                temp_fen_data = blank_non_required.copy()
            # In both cases ready to accept next one of these
            temp_fen_data["stip"] = line[len("Subtext:"):].strip().strip('"')

        # We encounter a non-fen (one of "these")
        elif line.startswith("Moves:"):
            if temp_fen_data["moves"] != "": # We already have one of these
                if "fen" in temp_fen_data: # Great we already have a FEN.
                    PROBLEM_LIST_inload.append(temp_fen_data)
                elif "fen" not in temp_fen_data: # Second one of these, but no FEN yet.
                    print("Error, second Subtext before FEN. Wiping entry.")
                # In both cases now reset and save new one of these
                print("Resetting for next problem...")
                temp_fen_data = blank_non_required.copy()
            # In both cases ready to accept next one of these
            temp_fen_data["moves"] = line[len("Moves:"):].strip().strip('"')

        # We encounter a blank line
        elif line == "": # a blank line
            # Assume this separates problems
            if "fen" in temp_fen_data: # at least we have a fen
                # Save entry (possible with blank stip
                PROBLEM_LIST_inload.append(temp_fen_data)
                # Wipe it clean for next entry
            temp_fen_data = blank_non_required.copy()

    # Finished reading all lines
    # Need to save final entry, assuming it has at least a fen
    if "fen" in temp_fen_data:
        PROBLEM_LIST_inload.append(temp_fen_data)

    # Print when FENs are loaded
    print(f"Loaded {len(PROBLEM_LIST_inload)} FENs from {filename}.")

    # Detail the loaded list of FENS
    print("Loaded positions:")
    for each_fen_data in PROBLEM_LIST_inload:
        print("------------------------------------------------------------------------------------------------------")
        #print(fen_data)
        print(f"Title: {each_fen_data['title']}")
        print(f"FEN: {each_fen_data['fen']}")
        print(f"Stip: {each_fen_data['stip']}")
        print(f"Moves: {each_fen_data['moves']}")
    print("------------------------------------------------------------------------------------------------------")

    if PROBLEM_LIST_inload:
        print("Successful load from PROBLEM_LIST file")
        return True
    else:
        print("Did not load from PROBLEM_LIST file")
        return False

# Redirect print statements to a file (optional)
if getattr(sys, 'frozen', False):  # Only when running as an executable
    sys.stdout = open('output.log', 'w')
    sys.stderr = sys.stdout

def get_resource_path(relative_path):
    """ Get the correct path for bundled files when running as an executable """
    if getattr(sys, 'frozen', False):
        # If running as a PyInstaller-built executable
        # noinspection PyProtectedMember
        base_path = sys._MEIPASS
    else:
        # If running as a normal Python script
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def test_image_location():
    """Test function to check where piece images are stored"""
    # Example usage
    image_path = get_resource_path("images/wK.png")
    print("Sample Image path to white king:", image_path)
    return 0

# test_image_location()

def parse_arguments():
    """
    Parses command-line arguments for optional customizations.
    Specify a FEN with --fen.
    Specify the problem's title with --title.
    Specify the stipulation with --stip.
    Specify a full problem database file (default = PROBLEM_LIST.txt) --fenlist
    Specify overall title of game window with --window (useful for screensharing)
    """
    parser = argparse.ArgumentParser(description="Chess game with optional FEN input and Window title.")
    parser.add_argument("--fen", type=str, help="Custom starting position in FEN format.")
    parser.add_argument("--title", type=str, default="", help="Set the problem title")
    parser.add_argument("--stip", type=str, default="", help="Set the problem stipulation")
    parser.add_argument("--fenlist", type=str, help="Path to the PROBLEM list file", default="PROBLEM_LIST.txt")
    parser.add_argument("--window", type=str, help="Window name")
    parser.add_argument("--movewindow", action="store_true", help="Launch parallel moves window")
    return parser.parse_args()

class LiveGame:
    """Chess game object: used to keep shown board position in memory"""
    def __init__(self, PROBLEM_LIST_ingame, MWV, fen=None, move_window_queue=None):
        """initialization routine for Chess game object"""
        self.board = chess.Board()
        self.start_pos = Config.START_FEN
        self.clock = pygame.time.Clock()
        self.move_window_queue = move_window_queue
        if fen:
            self.start_pos = fen
            try:
                self.board.set_fen(self.start_pos)
                print("Loaded custom FEN position.")
            except ValueError:
                print("Invalid FEN! Using default starting position.")
        self.move_history = None
        self.tree_position = 0  # Which element of the fen_tree are we at
        self.PROBLEM_LIST_ingame = PROBLEM_LIST_ingame
        self.MOVES_WINDOW_VERSION_ingame = MWV # Passing variable as to whether there is a move window to send messages to
        self._initialize_game_state()

    def _initialize_game_state(self):
        """Common setup method for initializing or resetting the game state."""
        self.legal_moves_enabled = True
        self.move_history = []  # Reset move history
        self.tree_position = 0  # Reset to start the element of the fen_tree are we at
        #self.moves = chess.pgn.Game()  # Reset PGN game
        #self.node = self.moves  # Reset PGN node pointer

    def jump_tree_step(self, target):
        """Jumps to a specific node of the tree and remembers for future arrow navigation"""
        current_fen_tree = self.PROBLEM_LIST_ingame[-1]['fen_tree']
        self.tree_position = target
        self.board.set_fen(current_fen_tree[self.tree_position])

    def advance_tree_step(self, direction):
        """Move through current fen tree. Forwards, backwards or jump to end."""
        current_fen_tree = self.PROBLEM_LIST_ingame[-1]['fen_tree']
        # If there's another move to play
        if direction == 1: # Request to step forwards
            if self.tree_position + 1 < len(current_fen_tree):
                self.tree_position += 1
        elif direction == -1:
            if self.tree_position > 0:
                self.tree_position -= 1
        elif direction is None: # This means jump to the end
            self.tree_position = len(current_fen_tree)-1

        # Move to next position (might be same position if at an end already)
        self.board.set_fen(current_fen_tree[self.tree_position])
        # Could now send news to move window to move highlight marker
        if self.MOVES_WINDOW_VERSION_ingame == True:
            self.move_window_queue.put(('state', self.tree_position))

    def set_new_fen(self, new_fen):
        """Updates the board with a new FEN and resets move history & PGN tracking."""
        try:
            self.board.set_fen(new_fen)
            self.start_pos = new_fen
            self._initialize_game_state()  # Reset game state
            print(f"New diagram set: {new_fen}")
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

    # def get_pgn(self):
    #     pgn = str(self.moves)
    #
    #     # Remove headers
    #     pgn_lines = pgn.splitlines()[8:]
    #
    #     #Re join remaining lines
    #     return '\n'.join(pgn_lines)

    def delete_piece_at(self, start):
        # Legality being off is checked before calling
        self.board.remove_piece_at(start)

    def move_piece(self, start, end):
        move = chess.Move.from_uci(start + end)
        print("Trying to move", move)

        # Case 1: Legal moves are enabled
        if self.legal_moves_enabled:
            piece = self.board.piece_at(chess.parse_square(start))

            # Check if it's a pawn and it's reaching the promotion rank
            if piece.piece_type == chess.PAWN:
                #print("It's a pawn!")
                promotion_rank = 7 if piece.color == chess.WHITE else 0
                #print("Promotion rank for such pieces is", promotion_rank)
                if chess.square_rank(chess.parse_square(end)) == promotion_rank:
                    # This is a promotion move, set promotion piece before legal move check
                    #print("It's a promotion attempt")
                    promotion_piece = self.ask_for_promotion() # Don't need to pass colour, move.promotion won't care
                    #print("You chose", promotion_piece)
                    move.promotion = promotion_piece  # Set the promotion piece

            # Now check if it's a legal move, including any promotion
            if move in self.board.legal_moves:
                _ = self.board.push(move)
                self.add_real_move(move)

            else:
                print("Move not legal!")

        else:
            print("Legality check disabled...")
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

            # All other end values will be squares
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

    def reset_move_history(self):
        self.move_history = []

    def reset_board(self):
        self.board.set_fen(self.start_pos)
        self.reset_move_history()
        self.tree_position = 0

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

    def toggle_legality(self):
        self.legal_moves_enabled = not self.legal_moves_enabled  # Toggle legality mode

class ChessGUI:
    def __init__(self, PROB_LIST, MV_WIN_TRUE, fen=None, window_title_bar = "", 
                 title='Chess Navigator', 
                 stip = "", 
                 fenlist = False, #problem_list_loaded
                 main_window_queue = None,
                 moves_window_queue = None,
                 shutdown_trigger_ingui = None):
        self.spare_pieces = None
        #self.config = settings
        self.main_window_queue = main_window_queue
        self.moves_window_queue = moves_window_queue
        self.PROBLEM_LIST_ingui = PROB_LIST # Passed old global here
        self.MOVES_WINDOW_VERSION_ingui = MV_WIN_TRUE # Passed old global here
        self.shutdown_trigger_ingui = shutdown_trigger_ingui

        #self.custom_pieces_enabled = False # Adding custom pieces (grasshoppers)

        pygame.init()
        self.fenlist = fenlist # True/False on whether a fenlist was loaded
        # Window icon
        icon_path = get_resource_path(f'images/icon.png')
        icon = pygame.image.load(icon_path)
        pygame.display.set_icon(icon)
        self.screen = pygame.display.set_mode((Config.WIDTH, Config.HEIGHT))
        pygame.display.set_caption(window_title_bar)
        self.pieces = load_images()
        self.game = LiveGame(self.PROBLEM_LIST_ingui, self.MOVES_WINDOW_VERSION_ingui, fen, moves_window_queue)
        #self.moves_window_queue.put(("load moves grid", 0))  # Value passed is PROBLEM_LIST index of new game
        self.running = True
        self.dragging_piece = None
        self.dragging_pos = (0, 0)
        self.setup_spare_pieces()
        self.dragging_square = None
        self.piece_source = None  # Track if dragging from board or panel
        self.clock = pygame.time.Clock()
        self.target_fps = None
        self.redraw = None
        #self.set_window_title('Chess Navigator')

        # Calculate board colours initially
        self.square_colors = self.precalculate_square_colors()
        self.TRUE_COLORS = [row[:] for row in self.square_colors] # New copy of list

        # Add custom title inside the window
        self.title_font = pygame.font.SysFont("Arial", Config.title_font_size)  # Change font and size here
        self.stip_font = pygame.font.SysFont("Arial", Config.stip_font_size)  # Change font and size here
        self.custom_title = title  # Or any other dynamic title based on your logic
        self.custom_stip = stip

        # If no fen was passed but a PROBLEM_LIST exists. Then start the F1 cycle early
        if fen is None and self.fenlist:
            self.cycle_fen()

    def run(self):
        """Main loop of the GUI."""
        # global SQUARE_SIZE
        low_fps = 10
        high_fps = 60
        self.target_fps = high_fps
        self.redraw = True # should we draw the next frame?

        loop_counter = 0

        while self.running:
            if self.MOVES_WINDOW_VERSION_ingui == True:
                if not self.main_window_queue.empty():
                    recip, message = self.main_window_queue.get()
                    if recip == "new fen":  # Check for messages meant for the main window
                        # print(f"Received message for main_window: {message}")
                        if message:
                            # Let's assume the message is the move_id
                            # move_id is the hidden tag on the button they start at 1

                            # The passed message is the number of which entry of the fen_tree we want
                            #moveid_fen = PROBLEM_LIST[-1]['fen_tree'][int(message)-1]
                            self.game.jump_tree_step(int(message))

                            #where_fen = PROBLEM_LIST[-1]["ids"][int(message)]
                            #which_fen = PROBLEM_LIST[-1]["fen_tree"][where_fen]

                            #self.game.set_new_fen(moveid_fen)  # Example: process the message in Pygame

                            self.redraw = True

            if self.dragging_piece or self.redraw: # Redraw everything as something happened
                self.screen.fill((0, 0, 0))
                self.draw_board()
                self.draw_pieces()
                self.draw_panel()
                self.setup_spare_pieces()
                self.draw_legality_mode()  # Show legality mode status
                self.draw_turn_indicator()
                # self.draw_pgn_panel()
                self.draw_custom_title()
                self.draw_custom_stip()

            self.redraw = False # Turn off default drawing of next frame, unless we're dragging

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    self.shutdown_trigger_ingui.set()
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
                        #self.game.legal_moves_enabled = not self.game.legal_moves_enabled  # Toggle legality mode
                        self.game.toggle_legality()
                    elif event.key == pygame.K_u:
                        self.game.undo_move() # Press u to undo last move
                    elif event.key == pygame.K_z:
                        self.game.clear_board() # Press z to zero/clear the board
                        self.game.legal_moves_enabled = False # Turn legality to false to allow placement
                    elif event.key == pygame.K_INSERT:
                        self.game.redefine_start() # Press INSERT to redefine root position
                    elif event.key in (pygame.K_HOME, pygame.K_r):
                        self.game.reset_board() # Press HOME to return to root position
                    elif event.key == pygame.K_t:
                        self.game.toggle_turn()  # Toggle the turn on pressing 'T'
                    elif event.key == pygame.K_h:
                        self.show_help_popup() # Press H to pop-up shortcuts
                    elif event.key == pygame.K_F1:  # Press F1 to load next fen from PROBLEM_LIST
                        if self.fenlist:
                            self.cycle_fen()
                    elif event.key == pygame.K_F3:
                        if self.fenlist:
                            self.reverse_cycle_fen()
                    elif event.key == pygame.K_RIGHT:
                        # Recall that PROBLEM_LIST[-1] is always the FEN we're working on
                        if self.fenlist: # Don't try if no fenlist
                            self.game.advance_tree_step(+1)
                    elif event.key == pygame.K_LEFT:
                        if self.fenlist:
                            self.game.advance_tree_step(-1)
                    elif event.key == pygame.K_END:
                        if self.fenlist:
                            self.game.advance_tree_step(None)
                    elif event.key in (pygame.K_KP_MINUS, pygame.K_MINUS):
                        if Config.SQUARE_SIZE > 40:
                            Config.set_square_size(Config.SQUARE_SIZE - 10)
                            Config.update_derived_sizes()
                            self.pieces = load_images()
                            self.screen = pygame.display.set_mode((Config.WIDTH, Config.HEIGHT))
                    elif event.key in (pygame.K_KP_PLUS, pygame.K_EQUALS):
                        if Config.SQUARE_SIZE < 100:
                            Config.set_square_size(Config.SQUARE_SIZE + 10)
                            Config.update_derived_sizes()
                            self.pieces = load_images()
                            self.screen = pygame.display.set_mode((Config.WIDTH, Config.HEIGHT))
                    # Square highlighting
                    elif event.key in Config.KEY_COLOR_MAP: # Presses 1 or 2 or 3 to add a square highlight
                        pos = pygame.mouse.get_pos()
                        square = self.get_square_under_mouse(pos)
                        #print(f"Square is {square}")
                        if square is not None:
                            self.change_square_color(square, Config.KEY_COLOR_MAP[event.key])
                    elif event.key == pygame.K_DELETE: # Pressed 0 to clean all highlights
                        # Reset all colours, recopy from TRUE_COLORS
                        self.square_colors = [row [:] for row in self.TRUE_COLORS]
                    # Copy FEN to clipboard
                    if event.key == pygame.K_c and (
                            pygame.key.get_pressed()[pygame.K_LCTRL] or pygame.key.get_pressed()[pygame.K_RCTRL]):
                        # Get FEN from the board and copy it to clipboard
                        try:
                            fen = self.game.board.fen()  # Call the board.fen() method from the LiveGame instance
                            copy(fen)  # Copy the FEN to clipboard
                            print("FEN copied to clipboard:", fen)  # Optional: print to console for confirmation
                        except Exception as e:
                            print(f"Error copying FEN to clipboard: {e}")

                self.redraw = True # Some event occurred. Turn on drawing of next frame.

            pygame.display.flip()

            self.clock.tick(self.target_fps)

            loop_counter += 1

    def draw_custom_title(self):
        """Draw the custom title at the top of the window."""
        _border_size = Config.BORDER_SIZE
        title_surface = self.title_font.render(self.custom_title, True, (255, 255, 255))  # White color
        title_rect = title_surface.get_rect(center=(Config.BOARD_WIDTH // 2 + _border_size,
                                                    _border_size // 2 ))  # Adjust position as needed
        self.screen.blit(title_surface, title_rect)

    def draw_custom_stip(self):
        """Draw the custom title at the top of the window."""
        title_surface = self.stip_font.render(self.custom_stip, True, (255, 255, 255))  # White color
        title_rect = title_surface.get_rect(center=Config.STIP_COORDS)  # Adjust position as needed
        self.screen.blit(title_surface, title_rect)

    def draw_pgn_panel(self): #Unused
        # Plan was to draw moves on far right panel
        font = pygame.font.Font(None, 24)  # Font for the PGN text

        # Create the text surface with the PGN
        text_surface = font.render("", True, (255, 255, 255))  # White text

        # Set the location for the panel (on the right side of the screen)
        panel_x = Config.WIDTH - Config.MOVES_WIDTH
        panel_y = 0  # Start from top with some margin

        # Draw the background for the panel
        pygame.draw.rect(self.screen, (0, 0, 0), (panel_x, panel_y, Config.MOVES_WIDTH, Config.HEIGHT))

        # Draw the PGN text in the panel
        self.screen.blit(text_surface, (panel_x + 10, panel_y+10))  # 10px margin inside the panel

    def get_legality_text(self):
        """Returns the legality text surface and its rectangle for positioning."""
        font = pygame.font.Font(None, 24)  # Smaller text
        # text: str = "Legality: ON" # + str(self.target_fps)
        text = "Legality: ON" if self.game.legal_moves_enabled else "Legality: OFF"
        color = (0, 255, 0) if self.game.legal_moves_enabled else (255, 0, 0)

        text_surface = font.render(text, True, color)
        text_x = Config.WIDTH - Config.MOVES_WIDTH - text_surface.get_width() - 10  # Align to top-right
        text_y = 10  # Small margin from top
        text_rect = text_surface.get_rect(topleft=(text_x, text_y))

        return text_surface, text_rect

    def draw_legality_mode(self):
        """Displays legality mode in the top-right corner, smaller size."""
        y_margin = 10
        x_margin = 10
        text_surface, _ = self.get_legality_text()
        x_left = Config.WIDTH - text_surface.get_width()
        self.screen.blit(text_surface, (x_left - x_margin, y_margin))

    def check_legal_toggle_click(self, pos):
        """Check if the legality label was clicked and toggle legality mode."""
        _, text_rect = self.get_legality_text()

        if text_rect.collidepoint(pos):
            #self.game.legal_moves_enabled = not self.game.legal_moves_enabled
            self.game.toggle_legality()
            

    def draw_turn_indicator(self):
        """Draws the turn indicator circle in the bottom-right corner."""
        # Determine whose turn it is (White or Black)
        turn_color = Config.TURN_WHITE if self.game.board.turn else Config.TURN_BLACK  # True = White's turn, False = Black's turn

        # Coordinates for the bottom-right corner
        circle_radius = 2 * (Config.SQUARE_SIZE+20) / 10
        circle_x = Config.MAIN_WIDTH + circle_radius + 5 #- circle_radius # Half-way through panel
        circle_y = Config.HEIGHT - circle_radius - Config.SQUARE_SIZE / 10  # 10px margin from the border

        # Draw the circle representing the current turn
        pygame.draw.circle(self.screen, turn_color, (circle_x, circle_y), circle_radius)

    def check_turn_toggle_click(self, pos):
        # Code copied from draw_turn_indicator
        circle_radius = 2 * Config.SQUARE_SIZE / 10
        circle_x = Config.MAIN_WIDTH + circle_radius + 2 #- circle_radius # Half-way through panel
        circle_y = Config.HEIGHT - circle_radius - Config.SQUARE_SIZE / 10  # 10px margin from the border

        if abs(pos[0]-circle_x) < 2 * circle_radius:
            if abs(pos[1]-circle_y) < 2 * circle_radius:
                self.game.toggle_turn()
        
        # Don't bother with fancy measuring, just in the square containing the circle
        # Calculate distance from click position to the center of the turn indicator
        # distance = ((pos[0] - circle_x) ** 2 + (pos[1] - circle_y) ** 2) ** 0.5

        # Check if the click is within the circle
        #if distance <= circle_radius:
        #    self.game.toggle_turn()

    def precalculate_square_colors(self):
        """Perform start of program board colour calculations"""
        square_colors = []
        for row in range(Config.BOARD_SIZE):
            row_colors = []
            for col in range(Config.BOARD_SIZE):
                color = self.get_default_color(row, col)
                row_colors.append(color)
            square_colors.append(row_colors)
        return square_colors

    def get_default_color(self, row, col):
        color = Config.WHITE_SQUARES if (row + col) % 2 == 0 else Config.BLACK_SQUARES
        return color

    def draw_board(self):
        """Draws the chessboard inside the border."""
        _square_size = Config.SQUARE_SIZE
        _border_size = Config.BORDER_SIZE
        _height_padding = Config.HEIGHT_PADDING
        for row in range(Config.BOARD_SIZE):
            for col in range(Config.BOARD_SIZE):
                # color = WHITE if (row + col) % 2 == 0 else BLACK
                color = self.square_colors[row][col]
                pygame.draw.rect(
                    self.screen, color,
                    (_border_size + col * _square_size,
                     _border_size + _height_padding + row * _square_size,
                     _square_size,
                     _square_size)
                )

    def draw_pieces(self):
        """Draws pieces inside the board with border offset."""
        _border_size = Config.BORDER_SIZE
        _height_padding = Config.HEIGHT_PADDING
        for row in range(Config.BOARD_SIZE):
            for col in range(Config.BOARD_SIZE):
                square = chess.square(col, 7 - row)
                piece = self.game.board.piece_at(square)
                if piece and (self.dragging_square != square):
                    img = self.pieces[piece.symbol()]
                    self.screen.blit(img, (_border_size + col * Config.SQUARE_SIZE,
                                           _border_size + _height_padding + row * Config.SQUARE_SIZE))

        # Draw dragged piece on top
        if self.dragging_piece:
            self.screen.blit(self.dragging_piece, self.dragging_pos)


    def setup_spare_pieces(self):
        """Defines positions for the spare pieces on the panel."""
        self.spare_pieces = []
        _panel_width = Config.PANEL_WIDTH
        x_offset_base = _panel_width * 0.1
        piece_order = ['K', 'Q', 'R', 'B', 'N', 'P']  # Display order

        for i, piece in enumerate(piece_order):
            y = 50 + i * (Config.SQUARE_SIZE + 20) # y-coordinate of pieces, progressively
            # Place white pieces on the left side of the panel
            self.spare_pieces.append((piece, (x_offset_base, y)))  # White pieces (x offset is 10% of panel)
            # Place black pieces on the right side of the panel
            self.spare_pieces.append((piece.lower(), (x_offset_base+Config.SQUARE_SIZE, y)))  # Black pieces (x offset is 10% of panel)

        # if getattr(self, "custom_pieces_enabled", False):
        #     # Define your custom pieces, for example: 'A', 'B', 'C'
        #     custom_pieces = ['g', 'G']  # You can customize this list
        #     for i, piece in enumerate(custom_pieces):
        #         y = 50 + i * (Config.SQUARE_SIZE + 20)
        #         # Custom pieces in a third column
        #         self.spare_pieces.append((piece, (x_offset_base + 2 * Config.SQUARE_SIZE, y)))


    def draw_panel(self):
        # Move the panel to the right to avoid overlapping with the board
        panel_x = Config.MAIN_WIDTH  # Adjusted position
        pygame.draw.rect(self.screen, Config.PANEL_COLOUR, (panel_x, 0, Config.PANEL_WIDTH, Config.HEIGHT))

        # Draw spare pieces in the new panel position
        for piece, pos in self.spare_pieces:
            # Draw the piece at the correct adjusted position inside the panel
            img = self.pieces[piece]
            self.screen.blit(img, (panel_x + pos[0], pos[1]))  # Add panel_x to position the pieces correctly

    def get_square_under_mouse(self, pos):
        """Converts the mouse click position to a square on the board."""
        x, y = pos
        # Adjust for the border offset
        x -= Config.BORDER_SIZE
        y -= Config.BORDER_SIZE + Config.HEIGHT_PADDING

        if x < 0 or y < 0:  # Outside the board
            return None

        # Check if the click is within the board area (8x8 grid)
        _board_width = Config.BOARD_WIDTH
        if x < _board_width and y < _board_width:
            col = x // Config.SQUARE_SIZE
            row = y // Config.SQUARE_SIZE
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
        panel_x = Config.MAIN_WIDTH

        for piece, piece_pos in self.spare_pieces:
            px, py = piece_pos
            if panel_x + px <= pos[0] <= panel_x + px + Config.SQUARE_SIZE and py <= pos[1] <= py + Config.SQUARE_SIZE:
                return piece
        return None

    def handle_mouse_down(self, pos):

        self.check_legal_toggle_click(pos)
        self.check_turn_toggle_click(pos)

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
                self.dragging_pos = (pos[0] - Config.SQUARE_SIZE // 2, pos[1] - Config.SQUARE_SIZE // 2)

    def handle_mouse_motion(self, pos):
        if self.dragging_piece:
            self.dragging_pos = (pos[0] - Config.SQUARE_SIZE // 2, pos[1] - Config.SQUARE_SIZE // 2)

    def handle_mouse_up(self, pos):
        """Handles dropping a piece, ensuring its color is preserved."""
        if self.dragging_piece:
            new_square = self.get_square_under_mouse(pos)
            # print(f"Dragged piece from {self.piece_source} to {new_square}")
            if self.piece_source == "board" and new_square is not None:
                if new_square != self.dragging_square:  # Move only if dropped in a new square
                    self.game.move_piece(chess.square_name(self.dragging_square), chess.square_name(new_square))


            elif self.piece_source == "panel" and new_square is not None:
                # Add the piece to the board and record the action for undo
                # New logic: only allow adding pieces when legality is off
                if not self.game.legal_moves_enabled:
                    piece_symbol = self.dragging_square  # This is the symbol of the piece being dragged
                    self.game.add_piece(piece_symbol, new_square)
                else:
                    print("You tried to drop a piece on the board, but legality was turned off. Turn it off first")

            elif self.piece_source == "board" and new_square is None: # Dropped piece off the board
                # print(f"You dropped the piece from {self.dragging_square} off the board! It will be removed")
                # Only allow removing a piece from board when legality is turned off
                if not self.game.legal_moves_enabled:
                    self.game.delete_piece_at(self.dragging_square)
                    #self.board.remove_piece_at(self.dragging_square)
                else:
                    print("Dropped piece off board, but it was illegal so not executed")
                # self.game.delete_piece_at(self.dragging_square)

            # Reset dragging state
            self.dragging_piece = None
            self.dragging_square = None
            self.piece_source = None

    def reverse_cycle_fen(self):
        """Move back to the previous problem"""
        # Clever logic says that if self = [C,D,E,F,A,B]... we are staring at B and rather than load C we want to load A
        # So we remove A and B from the end, put tem on the front then do cycle_fen.

        # Handle the 1-element case
        if len(self.PROBLEM_LIST_ingui) == 1:
            print("Only one problem in the list, cannot go back.")
            return

        print("Loading previous diagram from file")
        # Step 1: Remove the last two elements
        last = self.PROBLEM_LIST_ingui.pop()     # B
        second_last = self.PROBLEM_LIST_ingui.pop()  # A

        # Step 2: Put them at the front in reverse order (A, then B)
        self.PROBLEM_LIST_ingui.insert(0, last)        # [B, C, D, E, F]
        self.PROBLEM_LIST_ingui.insert(0, second_last) # [A, B, C, D, E, F]

        # Step 3: Load A using existing logic
        self.cycle_fen()


    def cycle_fen(self):
        """Cycle through the FEN list and update the game and window title."""
        # What this does is take the list [C, D, E, F, A, B] loads C, and moves it to the end. Leaving [D, E, F, A, B, C]

        # This also gets called at program start. So cannot bypass (currently) when list contains 1 element.

        print("Loading diagram from file")

        # Get the current FEN and title
        current_fen_data = self.PROBLEM_LIST_ingui.pop(0)  # Remove the first element
        self.PROBLEM_LIST_ingui.append(current_fen_data)  # Move it to the end for the next cycle

        new_fen = current_fen_data["fen"]
        new_title = current_fen_data["title"]
        subtext = current_fen_data["stip"]

        # Update the game and window title
        self.game.set_new_fen(new_fen)
        self.custom_title = new_title
        self.custom_stip = subtext
        self.draw_custom_title()
        self.draw_custom_stip()
        self.game.tree_position = 0

        # PROBLEM_LIST[-1] the last element is now the one we're working with
        # PROBLEM_LIST[0] will be loaded when we NEXT run the cycle

        # Redraw tk moves_windows
        if self.MOVES_WINDOW_VERSION_ingui == True:
            self.moves_window_queue.put(
            #   ("load moves grid", self.PROBLEM_LIST_ingui[-1]["move_tree"]))  # Value passed is PROBLEM_LIST index of new game
                ("load moves grid", current_fen_data["move_tree"]))
            return
        else:
            return

    def adjust_fps(self, new_fps):
        self.target_fps = new_fps

    def show_help_popup(self):
        """Displays a scalable help popup without cutting any lines, even for small board sizes."""

        popup_width = min(600, int(Config.MAIN_WIDTH * 0.8))  # Max 600px or 80% of screen width
        max_popup_height = int(Config.HEIGHT * 0.9)  # 90% of screen height
        popup_x = int((Config.MAIN_HEIGHT - popup_width) // 2)
        #popup_y = int((MAIN_HEIGHT - max_popup_height) // 2)
        popup_color = (50, 50, 50)  # Dark gray background
        text_color = (255, 255, 255)  # White text

        # List of shortcut keys and actions
        shortcuts = [
            ("Key Press", "Action"),
            ("----------------", "-------------------------------------"),
            ("HOME or R", "Return to home position"),
            ("INSERT", "Save current position as home position"),
            ("Z", "Zero the board (clear all pieces)"),
            ("F1", "Cycle to next FEN in the loaded file"),
            ("U", "Undo last move (not fully functional)"),
            ("L", "Toggle Legality"),
            ("T", "Toggle whose turn it is"),
            ("1/2/3", "Highlight square RED/YELLOW/GREEN"),
            ("0", "Remove hovered square's highlighting"),
            ("DELETE", "Clear all highlighting"),
            ("Ctrl + C", "Copies current position to clipboard as FEN"),
            ("+ or =", "Increase board size"),
            ("-", "Decrease board size"),
            ("LEFT/RIGHT", "Navigate through pre-loaded sequence"),
            ("END", "Jump to end of pre-loaded sequence"),
            ("H", "Show/Hide this help window")
        ]

        total_lines = len(shortcuts)

        # Dynamically calculate font size and spacing
        available_space: int = max_popup_height - 40  # 20px padding at top and bottom
        max_line_gap = int(available_space / total_lines)  # Max height per line
        font_size = int(max(12, min(24, max_line_gap - 4)))  # Keep font readable (12-24px)
        line_gap = int(max(font_size + 2, max_line_gap, 16))  # Ensure spacing is at least 16px

        # Prevent the popup from becoming too small
        popup_height = int(max(total_lines * line_gap + 40, 250))  # Minimum 250px
        popup_y = int((Config.MAIN_HEIGHT - popup_height) // 2)  # Adjust center

        # Set up fonts
        font = pygame.font.Font(None, font_size)
        key_font = pygame.font.Font(None, font_size + 2)
        header_font = pygame.font.Font(None, font_size + 4)

        # Draw the popup background
        pygame.draw.rect(self.screen, popup_color, (popup_x, popup_y, popup_width, popup_height), border_radius=10)

        # Draw text
        y_offset = popup_y + 20
        key_x = popup_x + 20
        action_x = key_x + popup_width * 0.25  # Adjust dynamically for spacing

        for i, (key, action) in enumerate(shortcuts):
            # Use header font for the first two rows
            if i in (0, 1):
                key_surface = header_font.render(key, True, text_color)
                action_surface = header_font.render(action, True, text_color)
            else:
                key_surface = key_font.render(key, True, text_color)
                action_surface = font.render(action, True, text_color)

            self.screen.blit(key_surface, (key_x, y_offset))
            self.screen.blit(action_surface, (action_x, y_offset))

            y_offset += line_gap  # Move down by calculated spacing

        pygame.display.flip()

        # Pause and wait for user to close the popup
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:  # Close window (click corner)
                    self.running = False  # Close the game
                    waiting = False  # Exit popup waiting loop
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_h, pygame.K_ESCAPE):  # Press H or Escape to close
                    waiting = False

# Load chess pieces
def load_images():
    """
    Loads the png images of all pieces into a vector
    These pngs are available in sizes 40x40 up to 100x100 and were generated from an SVG
    """
    pieces = {}
    square_size: int = Config.SQUARE_SIZE
    for piece in ['p', 'n', 'b', 'r', 'q', 'k', 'g']:
        img_path = get_resource_path(f'images/b{piece.upper()}_{square_size}px.png')
        img_black = pygame.image.load(img_path)
        pieces[piece] = pygame.transform.scale(img_black, (square_size, square_size))  # Scale to fit squares

        img_path = get_resource_path(f'images/w{piece.upper()}_{square_size}px.png')
        img_white =  pygame.image.load(img_path)
        pieces[piece.upper()] = pygame.transform.scale(img_white, (square_size, square_size))  # Scale for white pieces
    return pieces


class TempGame:
    def __init__(self, first_position):
        self.board = chess.Board()
        self.board.set_fen(first_position)
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

        self.generated = [] # This will store the full fens and be returned at the end
        self.add_this_fen() # Start by adding the initial FEN. Will need to know this later with -> movements
        self.checkpoints = [] # Create checkpoints list
        self.current_checkpoint_index = 0
        self.checkpoints.append(first_position) # Start with the home position (shouldn't be necessary)

    def add_this_fen(self):
        self.generated.append(self.board.fen())
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
    
        from_square = move['from']
        to_square = move['to']
        # Move recorded
        print(f"Regular move from {from_square} to {to_square}")

        piece = self.board.piece_at(chess.parse_square(from_square))
        target_piece = self.board.piece_at(chess.parse_square(to_square))
        if piece is None:
            print("Uhm, there was meant to be a piece here!")
            return None, None

        if piece.color != self.board.turn:
            print("You moved out of turn, but I'll allow it.")
            self.board.turn = not self.board.turn # Swap player to move

        if target_piece is not None:
            if piece.color == target_piece.color:
                print("You're trying to consume one of your own pieces. I'll allow it.")
                deletion_move = self.convert_move("-" + to_square)
                and_move = self.convert_move("&")
                self.move_handlers["remove"](self, deletion_move)
                self.move_handlers["and"](self, and_move)

        # Implement the logic for handling regular moves
        mv = chess.Move.from_uci(from_square + to_square)
        
        # Move recorded 2
        san_version = self.board.san(mv)
        #print(f"This move is called {san_version}")
        button_label = str(san_version)
        #print(f"BUTTON: {button_label}")
        
        self.board.push(mv)
        self.add_this_fen()

        return san_version, self.board.fen()

    def handle_promotion(self, move):
        """e.g. {'type': 'promotion', 'from': 'a7', 'to': 'a8', 'promotion_piece': 'Q'}
        If move is promotion do same as move but add all three parts
        """

        from_square = move['from']
        to_square = move['to']
        promotion_piece = move['promotion_piece']
        # Move recorded
        print(f"Promotion move from {from_square} to {to_square} promoting to {promotion_piece}")

        # Implement the logic for handling promotion

        piece = self.board.piece_at(chess.parse_square(from_square))
        target_piece = self.board.piece_at(chess.parse_square(to_square))
        if piece is None:
            print("Uhm, there was meant to be a piece here!")
            return None, None

        if piece.color != self.board.turn:
            print("You moved out of turn, but I'll allow it.")
            self.board.turn = not self.board.turn  # Swap player to move

        if target_piece is not None:
            if piece.color == target_piece.color:
                print("You're trying to consume one of your own pieces. I'll allow it.")
                deletion_move = self.convert_move("-" + to_square)
                and_move = self.convert_move("&")
                self.move_handlers['remove'](deletion_move)
                self.move_handlers['and'](and_move)

        mv = chess.Move.from_uci(from_square + to_square + promotion_piece.lower())
        
        # Move recorded 2
        san_version = self.board.san(mv)
        #print(f"This move is called {san_version}")
        button_label = str(san_version)
        #print(f"BUTTON: {button_label}")
        self.board.push(mv)
        self.add_this_fen()

        return san_version, self.board.fen()

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
        self.checkpoints.append(self.board.fen())

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
        self.board.set_fen(self.checkpoints[self.current_checkpoint_index])
        self.add_this_fen() # Save the fen to the generated list

        return "H", self.current_checkpoint_index

    def handle_skipback(self, move):
        """ e.g. {'type': 'skipback', 'steps': n} """

        distance = move['steps']
        # Move recorded
        print(f"Skipping back {distance} level(s)")
        # Implement the logic for skipping back
        self.current_checkpoint_index = max(0, self.current_checkpoint_index - distance + 1)
        self.board.set_fen(self.checkpoints[self.current_checkpoint_index])
        self.add_this_fen()  # Save the fen to the generated list
        #print(self.board)

        return "back", self.current_checkpoint_index

    def handle_and(self, _):
        """{'type': 'and'} """
        # Move recorded
        print(f"...playing another move at the same time...")
        print(f"BUTTON: save current button text for appending next move")
        self.generated.pop() # This should remove the last element
        self.id_record.pop() # Copy same behavuour on move_id
        self.move_id -= 1

        return "&", None

    def handle_add(self, move):
        """ {'type': 'add', 'piece': 'B', 'to': 'e5'} """
        to_square = move['to']
        added_piece = move['piece']

        # Move recorded
        print(f"Add piece ({added_piece}) to {to_square}")
        button_label = "+" + str(added_piece) + str(to_square)
        print(f"BUTTON: {button_label}")

        # Implement the logic for handling capture
        self.board.set_piece_at(chess.parse_square(to_square), chess.Piece.from_symbol(added_piece))
        self.add_this_fen()  # Save the fen to the generated list

        return button_label, self.board.fen()

    def handle_remove(self, move):
        """ {'type': 'remove', 'from': 'a1'} """

        from_square = move['from']
        piece_there = self.board.piece_at(chess.parse_square(from_square))
        # Move recorded
        print(f"Removing piece from {from_square}")
        button_label = "-" + str(piece_there) + str(from_square)
        print(f"BUTTON: {button_label}")

        # Implement the logic for removing a piece
        self.board.remove_piece_at(chess.parse_square(from_square))
        self.add_this_fen()

        return button_label, self.board.fen()

    def handle_set_whos_turn(self, move):
        """e.g. {'type': 'player_turn', 'player': 'B'}
        Request to set whose turn it is
        """
        player_to_move = move['player']
        current_turn = "W" if self.board.turn == chess.WHITE else "B" # Find whos turn it current is
        if player_to_move != current_turn:
            # Target player to move means we need to change
            self.board.turn = not self.board.turn
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
            move = move.rstrip('+#') # Strips any + or # at the end
            # This matches a format like 'a1e5'
            return {'type': 'move', 'from': move[:2], 'to': move[2:]}

        # Case b: letter-number-letter-number-letter (e.g. a7a8Q), where last letter is one of prnbQPRNBQ
        # possibly ending +, ++ or #
        elif re.fullmatch(r'[a-h][1-8][a-h][1-8][rbnqkRBNQK](\+{1,2}|#)?$', move):
            move = move.rstrip('+#')  # Strips any + or # at the end
            # This matches a format like 'a7a8Q' with a valid promotion piece
            return {'type': 'promotion', 'from': move[:2], 'to': move[2:4], 'promotion_piece': move[4].lower()}

        # Case c: the string "*" means save checkpoint
        elif move == "*":
            return {'type': 'save'}

        # This case allow multiple moves to be simultaneous
        elif move == "&":
            return {'type': 'and'} # Plan is to read next move and overwrite, not advancing the tree

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

        # Case g: string "-letter-number" (e.g. -e4)
        elif re.fullmatch(r'^-[a-h][1-8]$', move):
            # This matches a format like '-e4'
            return {'type': 'remove', 'from': move[1:]}

        else:
            return {'type': 'invalid', 'move': move}

def generate_fen_path(beginning, moves):
    """Create a sequence of FENs from an initial fen and the list of moves already"""

    # We will include in the FEN sequence non-FENs called "GoToHome", "GoToCheckpoint" and "SaveCheckpoint" for debugging and later flexibility
    # But they will be skipped when loading the next FEN

    # Read all the moves into a list
    # Already done, in moves

    # Load the starting FEN into a chess object, i.e. create a temporary game e.g. via a chess.board(START)
    temp_game = TempGame(beginning)

    # Create the move_tree already in finished arrangement
    grid_data = [] # 2D grid of (label, fen) data
    next_i = 0
    next_j = 0

    checkpoint_data = [1]
    #checkpoint_data.append(1)

    max_columns = 25

    def ensure_row(i):
        while len(grid_data) <= i:
            grid_data.append([None] * max_columns)

    # noinspection PyUnusedLocal
    loc_button_label = None
    # noinspection PyUnusedLocal
    loc_button_fen = None
    # noinspection PyUnusedLocal
    loc_button_position = None
    # noinspection PyUnusedLocal
    loc_checkpoint = None
    # noinspection PyUnusedLocal
    loc_move_id = None
    
    special_label_append = False

    for move in moves:
        # Create blank row if it doesn't exist yet
        ensure_row(next_i)

        # Save label and fen

        # Save values in (next_i,next_j)
        # temp_game.process_move returns button_label and button_fen
        # process_move also appends the next fen to the self.generated list
        loc_button_label, loc_button_fen, loc_move_id = temp_game.process_move(move)
        if loc_button_label == "back":
            print("Back button")
            loc_checkpoint = loc_button_fen
            # Jump back to column of checkpoint we're going to
            next_j = checkpoint_data[loc_checkpoint] # Should be stored column number for this checkpoint
            # Drop down one row for next move
            next_i += 1
        elif loc_button_label == "H":
            next_j = 0
            next_i += 1
        elif loc_button_label == "&":
            # We are reading an & let's try skipping back two?
            next_j -= 1 # Perfect, except we lose record of text on button, can we append?
            special_label_append = True
        elif loc_button_label == "*":
            print("Save action")
            # loc_button_fen will contain index of checkpoint
            loc_checkpoint = loc_button_fen
            checkpoint_data.insert(loc_checkpoint, next_j) # Should store current column for this checkpoint number

        else: # Only create button if not back or * or H
            if special_label_append: # if we're about to overwrite the first move in an and statement
                loc_button_label = grid_data[next_i][next_j][0] + "\n" + loc_button_label
                special_label_append = False
            grid_data[next_i][next_j] = (loc_button_label, loc_button_fen, loc_move_id)
            # Update next box
            next_j += 1
            if next_j >= max_columns:
                next_j = 0
                next_i += 1

    print("Grid contents:\n")
    
    for row_idx, row in enumerate(grid_data):
        print(f"Row {row_idx}: ", end="")
        for cell in row:
            if cell is None:
                print(f"[ ]", end=" ")
            else:
                label, fen, id = cell
                print(f"[{id}]", end=" ")
        print()  # Newline after each row

    return temp_game.result(), grid_data

def build_button_grid(main_window_queue, moves_window_queue, shutdown_trigger):

    #Config.startup("config.json")

    # Dictionary to store button references for later highlighting (by val[2] ie. move id)
    button_dict = {}
    btn_bg_color = '#d0d0d0'

    def clear_buttons():
        for widget in frame.winfo_children():
            widget.destroy()
        button_dict.clear()

    def move_button_click(param, queue):
            #print(f"Clicked button: {param}")
            highlight_button(param)
            queue.put(("new fen", param))

    def button_height(value):
        return 1+value.count("\n")

    def create_buttons(data):
        """Function takes a move_tree data grid and creates the buttons"""

        for i, row in enumerate(data):
            for j, val in enumerate(row):
                if val is not None:
                    # We're going to pass val[2] which is a move ID as the hidden val on the button
                    # val[0] is the button text
                    # val[1] is the FEN but we're now going to use move_id to allow peristent tree advancing
                    # Need to set all colour to btn_bg_color so that hovering or focus doesn't change it
                    button = tk.Button(frame, text=val[0], width=6, height=button_height(val[0]), padx=2, pady=2,
                                       bg=btn_bg_color, activebackground=btn_bg_color, highlightcolor=btn_bg_color,
                              command=lambda v=val[2]: move_button_click(v, main_window_queue))
                    button.grid(row=i, column=j, padx=2, pady=2)
                    button_dict[val[2]] = button
                else:
                    tk.Label(frame, text="").grid(row=i, column=j)

    root = tk.Tk()
    #moves_window = root
    root.title("Moves")

    # Window positioning
    #tk_x = pygame_x + pygame_width
    #tk_y = pygame_y - 30
    #root.geometry(f"+{tk_x}+{tk_y}")

    frame = tk.Frame(root)
    frame.pack(padx=10, pady=10)

    #data = [[(None, None, None), (None, None, None)], [(None, None, None), (None, None, None)]]
    #create_buttons(data)

    def highlight_button(button_id):
        """Function to highlight a button by changing its background color"""
        # Reset all button backgrounds to default color
        for btn in button_dict.values():
            btn.config(bg="#f0f0f0")  # Reset to default color

        # Highlight the button with the matching button_id
        if button_id in button_dict:
            button = button_dict[button_id]
            button.config(bg="yellow")  # Set the background to yellow (highlight color)

    def check_for_updates(_):
        if shutdown_trigger.is_set():  # If shutdown is requested, destroy the window
            root.destroy()

        # Recheck every 500ms
        if not shutdown_trigger.is_set():
            if not moves_window_queue.empty():
                recip, message = moves_window_queue.get()
                if recip == "load moves grid": # Being asked to create buttons from fenlist grid data
                    #print(f"Moves window received: {message}")
                    # Do something here to this window
                    new_grid_data = message
                    clear_buttons()
                    create_buttons(new_grid_data)
                elif recip == "state": # being told which button is live
                    highlight_button(int(message))

            root.after(200, check_for_updates, 0)

    # Start checking for updates every 100ms
    root.after(200, check_for_updates, 0)

    root.mainloop()

def run_gui(PROB_LIST, MOVES_WINDOW_VERSION, passed_fen, window_title, title, stip, problem_list_loaded, main_window_queue, moves_window_queue, shutdown_event):
    # Initialize Pygame GUI here
    Config.startup("config.json")
    main_window = ChessGUI(PROB_LIST, MOVES_WINDOW_VERSION, passed_fen, window_title, title, stip, problem_list_loaded, main_window_queue, moves_window_queue, shutdown_event)
    main_window.run()

# Function to handle communication from the Pygame process
# def queue_listener(queue):
#     global main_window, moves_windows

#     while not shutdown_event.is_set():
#         if not queue.empty():  # Check if there is any message in the queue
#             recip, message = queue.get()  # Get the message from the queue
#             if recip == "moves":
#                 print("Pygame asked Tkinter to do something:")
#                 print(message)
#             elif recip == "set_this_fen":
#                 print("Moves window asked pygame to do something:")
#                 queue.put()

#         time.sleep(0.1)

def start_processes(MWV, PL):

    if MWV == True:
    # Communication method
        main_window_queue = multiprocessing.Queue()
        moves_window_queue = multiprocessing.Queue()

        # Start both processes
        gui_process = multiprocessing.Process(target=run_gui, args=(PL.copy(), MWV,
            passed_fen, window_title, args.title, args.stip, problem_list_loaded, main_window_queue, moves_window_queue, shutdown_event))
        tk_process = multiprocessing.Process(target=build_button_grid, args=(main_window_queue, moves_window_queue, shutdown_event))

        gui_process.start()  # Start the Pygame GUI process
        tk_process.start()  # Start the Tkinter window process

        # Background process to listen for news from pygame window
        #listening_process = multiprocessing.Process(target=queue_listener, args=(queue, ))
        #listening_process.start()

        # Wait for them to finish
        gui_process.join()  # Wait for the Pygame window to close
        tk_process.join()  # Wait for Tkinter window to close

        print("Both windows have closed, shutting down")

    else:
        main_window_queue = None
        moves_window_queue = None

        # Start just the ChessGUI
        Config.startup("config.json")
        ChessGUI(PL.copy(), MWV, passed_fen, window_title, args.title, args.stip, problem_list_loaded, main_window_queue,
            moves_window_queue, shutdown_event).run()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    PROBLEM_LIST = []

    args = parse_arguments()  # Get arguments from command line
    MOVES_WINDOW_VERSION = args.movewindow # True if passed --movewindow else False. Default set in arg.parse code.
    window_title = args.window if args.window else "Chess Navigator" # Allow window name override
    passed_fen = args.fen if args.fen else None  # Use FEN if provided, otherwise default
    passed_fenlist = args.fenlist if args.fenlist else None
    problem_list_loaded = load_problem_list_from_file(PROBLEM_LIST, passed_fenlist) # default is PROBLEM_LIST.txt but user could customize
    # Return value is TRUE or FALSE based on success
    if problem_list_loaded:
        # Here we generate move trees from the moves
        for fen_data in PROBLEM_LIST:
            given_fen = fen_data['fen']
            move_list = fen_data['moves'].split()
            print("\n*** Analysing given moves for a position ***\n")
            fen_tree, move_tree = generate_fen_path(given_fen, move_list)
            fen_data['fen_tree'] = fen_tree[0]
            fen_data['ids'] = fen_tree[1]
            fen_data['move_tree'] = move_tree
            #print("Debug print:")
            #print(f"fen_tree[0] is length {len(fen_tree[0])}")
            #print(f"fen_tree[1] is length {len(fen_tree[1])}")
            #for item in fen_tree[0]:
            #    print(item)
            #print(fen_tree[1])
            #print("End of Debug")

    start_processes(MOVES_WINDOW_VERSION, PROBLEM_LIST)

# TO DO
# Pass the build_buttons the actual move tree for the current game (do it inside the ChessGUI via a message like
# "load_moves" and listener can pass PROBLEMLIST['moves_tree'] to some build function
# need to separate the draw the button frame and draw the buttons (based on a grid)
# Change button code to put fens behind buttons

# When button clicked, pass the fen to the pygame, run function to set fen
