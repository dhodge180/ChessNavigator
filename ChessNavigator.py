# ChessNavigator - Copyright (c) 2025 David Hodge
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License v2 as published
# by the Free Software Foundation.
# Non-commercial use only. See LICENSE file for full details.

"""
This is the main Chess Navigator program
"""

import pygame
import argparse

import os
import sys

# For moves window
import tkinter as tk
import multiprocessing

# For help window
from tkinter import messagebox

# For FEN copying
from pyperclip import copy

# For config file management
import json

from djhchess.fen_mapper import load_and_update_mapping, convert_fen_board_section, validate_all_fens, \
    expand_multiple_blank_rows
# from djhchess.fen_test import print_mapping

# No longer needed
# import chess
# import chess.pgn

# Needed (my new modules)
from djhchess.square import Square
from djhchess.pieces import Piece, create_extra_pieces#, PieceBox
from djhchess.mychess import ProblemListContainer, TempChessPosition

# For click management
from dataclasses import dataclass

# Code to load Fairy pieces saved in the custom_pieces.yaml file
from djhchess.custom_piece_load import EXTRA_PIECES
# EXTRA_PIECES is a dictionary of bonus fairy pieces, not yet given internal names.

@dataclass
class ClickResult:
    type: str                 # "board", "panel", "none", "toggle"
    target: Square | Piece | None = None     # Square or Piece

# Maybe not needed, as they're loaded by mychess when needed
# from djhchess.mychess import ChessPosition, print_board_matrix
# from djhchess.fen_mapper import load_and_update_mapping, convert_fen_board_section, load_existing_map

# Define the shutdown event (to allow one window to close another)
shutdown_event = multiprocessing.Event()

# Passable references to windows
#main_window = None
#moves_windows = None

# Global variable to hold the PROBLEM LIST
# PROBLEM_LIST = []

# Global for fancy multiprocessing mode
MOVES_WINDOW_VERSION = None

class Config:

    # Default configuration values -- can be changes by config.json
    DEFAULTS = {
        "white_squares": (238, 238, 210),
        "black_squares": (118, 150, 86),
        "panel_colour": (20, 60, 60),
        "square_size": 70,
        "title_font_size": 28,
        "stip_font_size": 28,
        "info_font_size": 20
    }

    # Customizable
    WINDOW_WIDTH = 1000
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
    TITLE_FONT_SIZE = 10
    STIP_FONT_SIZE = 10

    # Customizable
    WHITE_SQUARES = (238, 238, 210)
    BLACK_SQUARES = (118, 150, 86)
    PANEL_COLOUR = (20, 60, 60)
    SQUARE_SIZE = 70
    original_size = None # Used to record what original size upon opening was
    original_font = None
    original_stip = None
    original_info = None

    # Genuine fixed
    HEIGHT_PADDING = 10
    BORDER_SIZE = 60
    MOVES_WIDTH = 0
    config_path = "config.json"

    # Global constants for speed
    BOARD_SIZE = 8
    TURN_WHITE = (255, 255, 255) # Used for turn indicator
    TURN_BLACK = (0, 0, 0) # Used for turn indicator

    # FEN position to start from
    START_FEN = "rsbqkbsr/pppppppp/8/8/8/8/PPPPPPPP/RSBQKBSR w KQkq - 0 0"
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
    def change_height_padding(cls, new_size):
        cls.HEIGHT_PADDING = new_size
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
        Config.WHITE_SQUARES = Config.validate_rgb(local_config.get("white_squares"))
        """Colour of white squares"""
        Config.BLACK_SQUARES = Config.validate_rgb(local_config.get("black_squares"))
        """Colour of black squares"""
        Config.PANEL_COLOUR = Config.validate_rgb(local_config.get("panel_colour"))
        """Background colour of panel"""
        Config.SQUARE_SIZE = Config.validate_square_size(local_config.get("square_size"))
        """Starting square size"""

        Config.TITLE_FONT_SIZE= Config.validate_font_size(local_config.get("title_font_size"), min_size=10, max_size=45, font_type="title")
        """For title font size validation"""
        Config.STIP_FONT_SIZE = Config.validate_font_size(local_config.get("stip_font_size"), min_size=10, max_size=45, font_type="stip")
        """For stip font size validation (example if you have stip_font_size in your config)"""
        Config.INFO_FONT_SIZE = Config.validate_font_size(local_config.get("info_font_size"), min_size=8, max_size=45, font_type="info")
        """For text box font size validation"""

        Config.original_size = Config.SQUARE_SIZE
        Config.original_font = Config.TITLE_FONT_SIZE
        Config.original_stip = Config.STIP_FONT_SIZE
        Config.original_info = Config.INFO_FONT_SIZE

        # STAGE 1B: load custom pieces



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
        cls.PANEL_WIDTH = 5 * cls.SQUARE_SIZE
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

        multiplier = 1 + 0.1 * (cls.SQUARE_SIZE - cls.original_size) / 10 # Increase/decrease font by 10% per 10 pixels
        cls.TITLE_FONT_SIZE = Config.validate_font_size(cls.original_font * multiplier, min_size=10,
                                                           max_size=45, font_type="title")
        cls.STIP_FONT_SIZE = Config.validate_font_size(cls.original_stip * multiplier, min_size=10, max_size=45,
                                                          font_type="stip")
        cls.INFO_FONT_SIZE = Config.validate_font_size(cls.original_info * multiplier, min_size=8, max_size=45,
                                                       font_type="info")

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
            current_value = getattr(cls, key.upper())

            # If current value differs from the default, add it to the overridden settings
            if current_value != default_value:
                overridden_settings.append(key)

        # Notify the user if any settings were overridden by user-provided values
        if overridden_settings:
            print(f"Info: The following settings were overridden by the values in your config file: {', '.join(overridden_settings)}.")
        
        # If all values are the same as the defaults, just confirm all is fine
        if not overridden_settings:
            print("All configuration settings were successfully loaded and validated with default values.\n")

## Calculate screen sizes
# Position calculation
pygame_width, pygame_height = 960, 690
tk_width, tk_height = 1100, 150

# Get screen size once
root_temp = tk.Tk()
screen_w = root_temp.winfo_screenwidth()
screen_h = root_temp.winfo_screenheight()
root_temp.destroy()

center_x = (screen_w - pygame_width) // 2
pygame_x = center_x
pygame_y = 50
tk_x = center_x
tk_y = pygame_y + pygame_height + 50

# Export values so the rest of your code can use them
PYGAME_POS = f"{pygame_x},{pygame_y}"
TK_GEOMETRY = f"{tk_width}x{tk_height}+{tk_x}+{tk_y}"

# Initialize before loading pygame
os.environ['SDL_VIDEO_WINDOW_POS'] = PYGAME_POS

def load_problem_list_from_file(PROBLEM_LIST_inload, filename=None):
    """Load FENs, their titles and stipulations from an external file.
    lots of case handling, only FEN is strictly necessary"""

    blank_non_required = {"title": "", "stip": "", "moves": ""}

    if not os.path.exists(filename):
        print(f"File {filename} not found.")
        return False

    with open(filename, "r", encoding="utf-8") as file:
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
            # And check if we need to expand any long numbers in the FEN like 32 becoming 8/8/8/8
            temp_fen_data["fen"] = expand_multiple_blank_rows(temp_fen_data["fen"])

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
    sys.stdout = open('output.log', 'w', encoding='utf-8')
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

def show_help_text(title, text):
    root = tk.Tk()
    root.title(title)
    root.geometry("1100x250")  # Set a reasonable default size
    root.resizable(True, True)

    # Create scrollable text widget
    text_widget = tk.Text(root, wrap="none", font=("Courier", 10))
    text_widget.insert("1.0", text)
    text_widget.config(state="disabled")  # Read-only

    # Add scrollbars
    y_scroll = tk.Scrollbar(root, orient="vertical", command=text_widget.yview)
    x_scroll = tk.Scrollbar(root, orient="horizontal", command=text_widget.xview)
    text_widget.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

    # Layout
    text_widget.grid(row=0, column=0, sticky="nsew")
    y_scroll.grid(row=0, column=1, sticky="ns")
    x_scroll.grid(row=1, column=0, sticky="ew")

    # Make window expandable
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    root.mainloop()


def parse_arguments():
    """
    Parses command-line arguments for optional customizations.
    Specify a FEN with --fen.
    Specify the problem's title with --title.
    Specify the stipulation with --stip.
    Specify a full problem database file (default = PROBLEM_LIST.txt) --fenlist
    Specify overall title of game window with --window (useful for screensharing)
    """
    parser = argparse.ArgumentParser(description="Allows direct loading a single fen, custom database filename, "
                                                 "window renaming and launching of a separate move navigation window")
    parser.add_argument("--fen", type=str, help="Custom starting position in FEN format (for a single problem)")
    parser.add_argument("--title", type=str, default="", help="Set the problem title (for a single problem)")
    parser.add_argument("--stip", type=str, default="", help="Set the problem stipulation (for a single problem)")
    parser.add_argument("--fenlist", type=str, help="Path to the PROBLEM_LIST.txt file to load any number of problems", default="PROBLEM_LIST.txt")
    parser.add_argument("--window", type=str, help="Set the Window titlebar")
    #parser.add_argument("--movewindow", action="store_true", help="Launch the additional 'moves' window for each navigation")
    parser.add_argument("--nomoves", action="store_true", help="Don't show the additional 'moves' window for each navigation")

    # ✅ Add this to show help popup if requested
    if '--help' in sys.argv or '-h' in sys.argv:
        show_help_text("Help - Chess GUI", parser.format_help())
        sys.exit(0)

    return parser.parse_args()

# class LiveGame:
#     """Chess game object: used to keep shown board position in memory"""
#     def __init__(self, PROBLEM_LIST_ingame, MWV, fen=None, move_window_queue=None):
#         """initialization routine for Chess game object"""
#         self.board = chess.Board()
#         self.start_pos = Config.START_FEN
#         self.clock = pygame.time.Clock()
#         self.move_window_queue = move_window_queue
#         if fen:
#             self.start_pos = fen
#             try:
#                 self.board.set_fen(self.start_pos)
#                 print("Loaded custom FEN position.")
#             except ValueError:
#                 print("Invalid FEN! Using default starting position.")
#         self.move_history = None
#         self.tree_position = 0  # Which element of the fen_tree are we at
#         self.PROBLEM_LIST_ingame = PROBLEM_LIST_ingame
#
#         self.problem_container = PROBLEM_LIST_ingame
#         self.problem_container.set_current("001")
#         self.current_composition = self.problem_container.get_current()
#
#         self.MOVES_WINDOW_VERSION_ingame = MWV # Passing variable as to whether there is a move window to send messages to
#         self._initialize_game_state()
#
#     def _initialize_game_state(self):
#         """Common setup method for initializing or resetting the game state."""
#         self.legal_moves_enabled = True
#         self.move_history = []  # Reset move history
#         self.tree_position = 0  # Reset to start the element of the fen_tree are we at
#         #self.moves = chess.pgn.Game()  # Reset PGN game
#         #self.node = self.moves  # Reset PGN node pointer
#
#     def jump_tree_step(self, target):
#         """Jumps to a specific node of the tree and remembers for future arrow navigation"""
#         current_fen_tree = self.PROBLEM_LIST_ingame[-1]['fen_tree']
#
#         current_comp = self.problem_container.get_current()
#         current_fen_tree = current_comp.fen_tree
#
#         self.tree_position = target
#         self.board.set_fen(current_fen_tree[self.tree_position])
#
#     def advance_tree_step(self, direction):
#         """Move through current fen tree. Forwards, backwards or jump to end."""
#         current_fen_tree = self.PROBLEM_LIST_ingame[-1]['fen_tree']
#
#         current_comp = self.problem_container.get_current()
#         current_fen_tree = current_comp.fen_tree
#
#         # If there's another move to play
#         if direction == 1: # Request to step forwards
#             if self.tree_position + 1 < len(current_fen_tree):
#                 self.tree_position += 1
#         elif direction == -1:
#             if self.tree_position > 0:
#                 self.tree_position -= 1
#         elif direction is None: # This means jump to the end
#             self.tree_position = len(current_fen_tree)-1
#
#         # Move to next position (might be same position if at an end already)
#         self.board.set_fen(current_fen_tree[self.tree_position])
#         # Could now send news to move window to move highlight marker
#         if self.MOVES_WINDOW_VERSION_ingame == True:
#             self.move_window_queue.put(('state', self.tree_position))
#
#     def set_new_fen(self, new_fen):
#         """Updates the board with a new FEN and resets move history & PGN tracking."""
#         try:
#             self.board.set_fen(new_fen)
#             self.start_pos = new_fen
#             self._initialize_game_state()  # Reset game state
#             print(f"New diagram set: {new_fen}")
#         except ValueError:
#             print("Invalid FEN! Keeping the current position.")
#
#     def redefine_start(self):
#         """This forces the current board position to become the reset state"""
#         self.start_pos = self.board.fen()
#
#     def clear_board(self):
#         self.board.clear()
#
#     def add_real_move(self, move):
#         # self.node = self.node.add_variation(move)
#         self.move_history.append(("move", move))
#
#     # def get_pgn(self):
#     #     pgn = str(self.moves)
#     #
#     #     # Remove headers
#     #     pgn_lines = pgn.splitlines()[8:]
#     #
#     #     #Re join remaining lines
#     #     return '\n'.join(pgn_lines)
#
#     def delete_piece_at(self, start):
#         # Legality being off is checked before calling
#         self.board.remove_piece_at(start)
#
#     def move_piece(self, start, end):
#         move = chess.Move.from_uci(start + end)
#         print("Trying to move", move)
#
#         # Case 1: Legal moves are enabled
#         if self.legal_moves_enabled:
#             piece = self.board.piece_at(chess.parse_square(start))
#
#             # Check if it's a pawn and it's reaching the promotion rank
#             if piece.piece_type == chess.PAWN:
#                 #print("It's a pawn!")
#                 promotion_rank = 7 if piece.color == chess.WHITE else 0
#                 #print("Promotion rank for such pieces is", promotion_rank)
#                 if chess.square_rank(chess.parse_square(end)) == promotion_rank:
#                     # This is a promotion move, set promotion piece before legal move check
#                     #print("It's a promotion attempt")
#                     promotion_piece = self.ask_for_promotion() # Don't need to pass colour, move.promotion won't care
#                     #print("You chose", promotion_piece)
#                     move.promotion = promotion_piece  # Set the promotion piece
#
#             # Now check if it's a legal move, including any promotion
#             if move in self.board.legal_moves:
#                 _ = self.board.push(move)
#                 self.add_real_move(move)
#
#             else:
#                 print("Move not legal!")
#
#         else:
#             print("Legality check disabled...")
#             # Handle non-legal moves (when legal moves are disabled)
#             # This can be a custom behavior or just a bypass depending on your needs
#             piece = self.board.piece_at(chess.parse_square(start))
#             if piece is None:
#                 return  # No piece to move
#
#             original_turn = self.board.turn  # Store the current turn
#             piece_color = piece.color  # Get the color of the moving piece
#
#             # Temporarily switch the turn to match the piece's color
#             if piece_color != original_turn:
#                 self.board.turn = piece_color
#
#             # All other end values will be squares
#             self.board.push(move)  # Perform the move
#             self.add_real_move(move)
#             #self.move_history.append(("move", move))
#
#             # Restore the original turn
#             self.board.turn = original_turn
#
#     def ask_for_promotion(self):
#         """Waits for the user to press a key to select a promotion piece."""
#         # Available pieces for promotion
#         promotion_pieces = {
#             'Q': chess.QUEEN,
#             'R': chess.ROOK,
#             'B': chess.BISHOP,
#             'S': chess.KNIGHT,
#             'N': chess.KNIGHT
#         }
#
#         pygame.display.flip()  # Update the display
#
#         running = True
#         selected_piece = None
#
#         while running:
#             for event in pygame.event.get():
#                 if event.type == pygame.QUIT:
#                     running = False
#                 if event.type == pygame.KEYDOWN:
#                     if event.key == pygame.K_q:
#                         selected_piece = promotion_pieces['Q']
#                         running = False
#                     elif event.key == pygame.K_r:
#                         selected_piece = promotion_pieces['R']
#                         running = False
#                     elif event.key == pygame.K_b:
#                         selected_piece = promotion_pieces['B']
#                         running = False
#                     elif event.key == pygame.K_n:
#                         selected_piece = promotion_pieces['S']
#                         running = False
#
#             self.clock.tick(30)
#         return selected_piece
#
#     def undo_move(self):
#         if len(self.board.move_stack) == 0:
#             # No moves to undo.
#             return
#
#         if len(self.move_history) > 0:
#             last_move = self.move_history.pop()
#
#             if last_move[0] == "move":
#                 # Undo a normal move
#                 self.board.pop()
#
#             elif last_move[0] == "add_piece":
#                 # Undo a piece addition
#                 piece_symbol, square, removed_piece = last_move[1]
#                 self.board.set_piece_at(square, removed_piece)  # Restore previous piece
#             else:
#                 raise ValueError("Unknown move type in history")
#
#     def reset_move_history(self):
#         self.move_history = []
#
#     def reset_board(self):
#         self.board.set_fen(self.start_pos)
#         self.reset_move_history()
#         self.tree_position = 0
#
#     def add_piece(self, piece_symbol, square):
#         """Add a piece from the panel to the board and record the action for undo."""
#         # Save the current piece at the square (None if empty)
#         current_piece = self.board.piece_at(square)
#
#         # Add the new piece
#         self.board.set_piece_at(square, chess.Piece.from_symbol(piece_symbol))
#
#         # Add null move
#         self.board.push(chess.Move.null())
#         self.board.push(chess.Move.null())
#
#         # Add the move to history (recording the type of action)
#         self.move_history.append(("add_piece", (piece_symbol, square, current_piece)))
#         # Cannot add this to the PGN!
#
#     def toggle_turn(self):
#         """Toggles the turn by making a null move."""
#         self.board.push(chess.Move.null())
#
#     def toggle_legality(self):
#         self.legal_moves_enabled = not self.legal_moves_enabled  # Toggle legality mode

class InfoBox:
    """
    New class which understands what's going into the info box. Includes rendering, and history and logic
    to decide what to print based on what it has been told has happened.
    """
    def __init__(self):
        # Called from inside GUI to initialize
        self.current_text = ""
        self.surfaces = []
        self.text_history = []
        self.font = pygame.font.SysFont("Arial", Config.INFO_FONT_SIZE)

    def _build_surfaces(self, text):
        # Helper function, so that _render can save history, but that during undo the render of the history doesn't
        # trigger adding to the history
        return [self.font.render(line, True, (232, 232, 232)) for line in text.split("\n")]

    def _render(self, text):
        self.current_text = text
        self.text_history.append(text)
        self.surfaces = []
        self.surfaces = self._build_surfaces(text)

    def resize(self):
        self.font = pygame.font.SysFont("Arial", Config.INFO_FONT_SIZE)
        self.surfaces = self._build_surfaces(self.current_text)

    def update(self, event, data=None):
        if event == "move":
            self._render("Last Move:\n" + data)
        elif event == "add":
            self._render("Add\n" + data)
        elif event == "remove":
            self._render("Delete\n" + data)
        elif event == "undo":
            if self.text_history:
                self.text_history.pop() #Delete current
            if self.text_history:
                self.surfaces = self._build_surfaces(self.text_history[-1])
            else:
                self.surfaces = []
        elif event == "home":
            self.text_history.clear()
            self._render("Home")
        elif event == "tree":
            self._render("Last Move:\n" + data)
        elif event == "clear":
            self.text_history.clear()
            self._render("")
        elif event == "new":
            self.text_history.clear()
            self._render("New Load")
        elif event == "save":
            # Pressed insert to save current position
            self.text_history.clear()
            self._render("Set New Home")

    def draw(self, screen):
        if not self.surfaces:
            return
        # Copied from draw_turn_indicator, to ensure text is to the right of the turn indicator
        line_height = self.font.get_linesize()
        circle_radius = 2 * (Config.SQUARE_SIZE + 20) / 10
        circle_x = Config.MAIN_WIDTH + circle_radius + 5  # - circle_radius # Half-way through panel
        circle_y = Config.HEIGHT - circle_radius - Config.SQUARE_SIZE / 10  # 10px margin from the border
        move_to_right = circle_radius
        y = int(circle_y - line_height)
        x = int(circle_x + circle_radius + move_to_right)  # To right of turn indicator
        for i, surface in enumerate(self.surfaces):
            screen.blit(surface, (x, y + i * line_height))

class ChessGUI:
    def __init__(self, PROB_LIST, MV_WIN_TRUE, fen=None, window_title_bar = "Chess Navigator", 
                 title='', 
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
        
        self.problem_container = PROB_LIST
        self.composition = self.problem_container.set_current(1)
        self.composition = self.problem_container.get_current()
        self.composition.create_position()
        self.position = self.composition.get_position_object()
        
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
        #self.game = LiveGame(self.PROBLEM_LIST_ingui, self.MOVES_WINDOW_VERSION_ingui, fen, moves_window_queue)

        #self.moves_window_queue.put(("load moves grid", 0))  # Value passed is PROBLEM_LIST index of new game
        self.running = True
        self.dragging_piece = None
        self.dragging_pos = (0, 0)
        self.setup_spare_pieces()
        self.clickable_objects = []
        self.dragging_square = None
        self.dragging_piece_symbol = None
        self.chosen_square = None
        self.piece_source = None  # Track if dragging from board or panel
        self.clock = pygame.time.Clock()
        self.target_fps = None
        self.redraw = None
        #self.set_window_title('Chess Navigator')

        # Blank list of piece images. Will be populated in run() once we have loaded fairy pieces.
        self.pieces = []

        # Calculate board colours initially
        self.square_colors = self.precalculate_square_colors()
        self.TRUE_COLORS = [row[:] for row in self.square_colors] # New copy of list

        # Add custom title inside the window
        self.title_font = pygame.font.SysFont("Arial", Config.TITLE_FONT_SIZE)  # Change font and size here
        self.stip_font = pygame.font.SysFont("Arial", Config.STIP_FONT_SIZE)  # Change font and size here
        
        self.custom_title = title  # Or any other dynamic title based on your logic
        self.custom_stip = stip # Text below diagram
        self.text_surfaces = [] # Pre-rendered text for title and stipulation -- rerendered only upon change

        # Initialize the InfoBox
        self.info_box = InfoBox()

        # Load all the piece singletons
        create_extra_pieces(self.problem_container.u_to_i_dict, EXTRA_PIECES)  # This needs to be run again later after a Windows spawn
        self.pieces = load_images()
        # print("Now we see what pieces exist,")
        # print(Piece.all())

        # If no fen was passed but a PROBLEM_LIST exists. Then start the F1 cycle early
        if fen is None and self.fenlist:
            #self.reverse_cycle_fen()
            #self.cycle_fen()
            self.update_after_cycle()

    def run(self):
        """Main loop of the GUI."""
        # Start by recreating the fairy piece singletons once (needed in Windows as spawn lost the ones made earlier)
        # Check what pieces
        #print("Inside the GUI process, first lets see what pieces exist:")
        #print(Piece.all())
        #print("Now we recreate the singletons.")

        self.clickable_objects = self.build_clickable_objects(self.spare_pieces)  # New ClickResult

        # global SQUARE_SIZE
        self.low_fps = 10
        self.high_fps = 60
        self.target_fps = self.high_fps
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
                            self.composition.jump_tree_step(int(message), callback_queue=self.moves_window_queue)
                            self.update_info_for_tree_position()

                            #where_fen = PROBLEM_LIST[-1]["ids"][int(message)]
                            #which_fen = PROBLEM_LIST[-1]["fen_tree"][where_fen]

                            #self.game.set_new_fen(moveid_fen)  # Example: process the message in Pygame

                            self.redraw = True

            if self.dragging_piece or self.redraw: # Redraw everything as something happened
                self.screen.fill((0, 0, 0))
                self.draw_board()
                self.draw_pieces()
                self.setup_spare_pieces()
                self.draw_panel()
                #self.draw_legality_mode()  # Show legality mode status
                self.draw_turn_indicator()
                self.info_box.draw(self.screen)
                # self.draw_pgn_panel()
                
                #self.draw_custom_title()
                #self.draw_custom_stip()
                self.draw_custom_text()

            self.redraw = False # Turn off default drawing of next frame, unless we're dragging

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    self.shutdown_trigger_ingui.set()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.adjust_fps(self.high_fps)
                    self.handle_mouse_down(event.pos)
                elif event.type == pygame.MOUSEMOTION:
                    self.handle_mouse_motion(event.pos)
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.adjust_fps(self.low_fps)
                    self.handle_mouse_up(event.pos, event.button)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_l:
                        #self.game.legal_moves_enabled = not self.game.legal_moves_enabled  # Toggle legality mode
                        self.position.toggle_legality()
                    elif event.key == pygame.K_u:
                        self.position.undo() # Press u move backwards in the board history
                        self.info_box.update("undo")
                    elif event.key == pygame.K_i:
                        self.position.redo()  # Press i move forwards in board history
                    elif event.key == pygame.K_z:
                        self.position.clear() # Press z to zero/clear the board
                        self.info_box.update("clear")
                        self.position.legal_moves_enabled = False # Turn legality to false to allow placement
                    elif event.key == pygame.K_INSERT:
                        self.position.redefine_start() # Press INSERT to redefine root position
                        self.info_box.update("save")
                    elif event.key in (pygame.K_HOME, pygame.K_r):
                        self.position.reset_board() # Press HOME to return to root position
                        self.composition.tree_position = 0
                        self.info_box.update("home")
                    elif event.key == pygame.K_t:
                        self.position.change_turn()  # Toggle the turn on pressing 'T'
                    elif event.key == pygame.K_h:
                        self.show_help_popup() # Press H to pop-up shortcuts
                    elif event.key == pygame.K_F1:  # Press F1 to load next fen from PROBLEM_LIST
                        #print("F1 pressed!")
                        if self.fenlist:
                            self.cycle_fen()
                            self.redraw = True
                    elif event.key == pygame.K_F3:
                        if self.fenlist:
                            self.reverse_cycle_fen()
                    elif event.key == pygame.K_RIGHT:
                        # Recall that PROBLEM_LIST[-1] is always the FEN we're working on
                        if self.fenlist: # Don't try if no fenlist
                            self.composition.advance_tree_step(+1, callback_queue=self.moves_window_queue)
                            self.update_info_for_tree_position()
                    elif event.key == pygame.K_LEFT:
                        if self.fenlist:
                            self.composition.advance_tree_step(-1, callback_queue=self.moves_window_queue)
                            self.update_info_for_tree_position()
                    elif event.key == pygame.K_END:
                        if self.fenlist:
                            self.composition.advance_tree_step(None, callback_queue=self.moves_window_queue)
                            self.update_info_for_tree_position()
                    elif event.key in (pygame.K_KP_MINUS, pygame.K_MINUS):
                        if Config.SQUARE_SIZE > 40:
                            Config.set_square_size(Config.SQUARE_SIZE - 10)
                            Config.update_derived_sizes()
                            self.resize_elements_after_resize()
                            self.screen = pygame.display.set_mode((Config.WIDTH, Config.HEIGHT))
                    elif event.key in (pygame.K_KP_PLUS, pygame.K_EQUALS):
                        if Config.SQUARE_SIZE < 100:
                            Config.set_square_size(Config.SQUARE_SIZE + 10)
                            Config.update_derived_sizes()
                            self.resize_elements_after_resize()
                            self.screen = pygame.display.set_mode((Config.WIDTH, Config.HEIGHT))
                    # Square highlighting
                    elif event.key in Config.KEY_COLOR_MAP: # Presses 1 or 2 or 3 to add a square highlight
                        pos = pygame.mouse.get_pos()
                        square_num = self.get_square_under_mouse(pos)
                        #print(f"Square is {square_tuple}")
                        if square_num is not None:
                            self.change_square_color(square_num, Config.KEY_COLOR_MAP[event.key])
                    elif event.key == pygame.K_DELETE: # Pressed 0 to clean all highlights
                        # Reset all colours, recopy from TRUE_COLORS
                        self.square_colors = [row [:] for row in self.TRUE_COLORS]
                    # Copy FEN to clipboard
                    if event.key == pygame.K_c and (
                            pygame.key.get_pressed()[pygame.K_LCTRL] or pygame.key.get_pressed()[pygame.K_RCTRL]):
                        # Get FEN from the board and copy it to clipboard
                        try:
                            fen = self.position.fen  # Call the board.fen() method from the LiveGame instance
                            user_fen = convert_fen_board_section(fen, problem_container.i_to_u_dict)
                            copy(user_fen)  # Copy the FEN to clipboard
                            print("FEN copied to clipboard:", user_fen)  # Optional: print to console for confirmation
                        except Exception as e:
                            print(f"Error copying FEN to clipboard: {e}")

                self.redraw = True # Some event occurred. Turn on drawing of next frame.

            pygame.display.flip()

            self.clock.tick(self.target_fps)

            loop_counter += 1

    def set_custom_text(self, title_text, stip_text):
        self.custom_title = title_text
        self.custom_stip = stip_text
        self.text_surfaces = []  # clear old cached surfaces

        # Spilling - new border HEIGHT_PADDING?
        title_split = False
        stip_split = False

        # --- Title ---
        _border_size = Config.BORDER_SIZE
        max_width = Config.BOARD_WIDTH

        temp_surface = self.title_font.render(title_text, True, (255, 255, 255))
        if temp_surface.get_width() > max_width:
            words = title_text.split()
            half = len(words) // 2
            title_lines = [" ".join(words[:half]), " ".join(words[half:])]
            title_split = True
        else:
            title_lines = [title_text]

        title_offset = -15 if title_split else 0
        y = _border_size // 2 + title_offset

        for i, line in enumerate(title_lines):
            surface = self.title_font.render(line, True, (255, 255, 255))
            rect = surface.get_rect(center=(Config.BOARD_WIDTH // 2 + _border_size,
                                            y + i * surface.get_height()))
            self.text_surfaces.append((surface, rect))

        # --- Stip ---
        temp_surface = self.stip_font.render(stip_text, True, (255, 255, 255))
        if temp_surface.get_width() > max_width:
            words = stip_text.split()
            half = len(words) // 2
            stip_lines = [" ".join(words[:half]), " ".join(words[half:])]
            stip_split = True
        else:
            stip_lines = [stip_text]

        stip_offset = -15 if stip_split else 0
        base_x, base_y = Config.STIP_COORDS
        base_y = base_y + stip_offset

        for i, line in enumerate(stip_lines):
            surface = self.stip_font.render(line, True, (255, 255, 255))
            rect = surface.get_rect(center=(base_x, base_y + i * surface.get_height()))
            self.text_surfaces.append((surface, rect))

    
    def draw_custom_text(self):
        for surface, rect in self.text_surfaces:
            self.screen.blit(surface, rect)


    def old_draw_custom_title(self):
        """Draw the custom title at the top of the window."""
        _border_size = Config.BORDER_SIZE
        max_width = Config.BOARD_WIDTH - 2 * _border_size  # how wide text can be

        title_surface = self.title_font.render(self.custom_title, True, (255, 255, 255))  # White color
        title_rect = title_surface.get_rect(center=(Config.BOARD_WIDTH // 2 + _border_size,
                                                    _border_size // 2 ))  # Adjust position as needed
        self.screen.blit(title_surface, title_rect)

    def old_draw_custom_stip(self):
        """Draw the custom title at the top of the window."""
        #print("HELP FIX THIS!!!")
        stip_surface = self.stip_font.render(self.custom_stip, True, (255, 255, 255))  # White color
        stip_rect = stip_surface.get_rect(center=Config.STIP_COORDS)  # Adjust position as needed
        self.screen.blit(stip_surface, stip_rect)
        #print("Did it work?")

    def resize_elements_after_resize(self):
        self.pieces = load_images()
        self.setup_spare_pieces()
        self.title_font = pygame.font.SysFont("Arial", Config.TITLE_FONT_SIZE)  # Change font and size here
        self.stip_font = pygame.font.SysFont("Arial", Config.STIP_FONT_SIZE)  # Change font and size here
        self.info_font = pygame.font.SysFont("Arial", Config.INFO_FONT_SIZE) # Change font and size here
        #self.draw_custom_stip()
        #self.draw_custom_title()
        self.set_custom_text(self.custom_title, self.custom_stip)
        self.draw_custom_text()
        self.info_box.resize()
        self.clickable_objects = self.build_clickable_objects(self.spare_pieces)

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
        text = "Legality: ON" if self.position.legal_moves_enabled else "Legality: OFF"
        color = (0, 255, 0) if self.position.legal_moves_enabled else (255, 0, 0)

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
            self.position.toggle_legality()
            

    def draw_turn_indicator(self):
        """Draws the turn indicator circle in the bottom-right corner."""
        # Determine whose turn it is (White or Black)
        turn_color = Config.TURN_WHITE if self.position.turn == 'w' else Config.TURN_BLACK  # 'w' = White's turn, 'b' = Black's turn

        # Coordinates for the bottom-right corner
        circle_radius = 2 * (Config.SQUARE_SIZE+20) / 10
        circle_x = Config.MAIN_WIDTH + circle_radius + 5 #- circle_radius # Half-way through panel
        circle_y = Config.HEIGHT - circle_radius - Config.SQUARE_SIZE / 10  # 10px margin from the border

        # Draw the circle representing the current turn
        pygame.draw.circle(self.screen, turn_color, (circle_x, circle_y), circle_radius)

    def update_info_for_tree_position(self):
        label = self.composition.move_id_to_label.get(self.composition.tree_position)
        if label:
            self.info_box.update("tree", label)
        return

        # DOn't reach here any more

    def check_turn_toggle_click(self, pos):
        # Code copied from draw_turn_indicator
        circle_radius = 2 * Config.SQUARE_SIZE / 10
        circle_x = Config.MAIN_WIDTH + circle_radius + 2 #- circle_radius # Half-way through panel
        circle_y = Config.HEIGHT - circle_radius - Config.SQUARE_SIZE / 10  # 10px margin from the border

        if abs(pos[0]-circle_x) < 2 * circle_radius:
            if abs(pos[1]-circle_y) < 2 * circle_radius:
                self.position.change_turn()
        
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
        if self.chosen_square:
            highlight_color = (255, 0, 0)  # bright red border
            row, col = self.chosen_square.coord
            x = _border_size + col * _square_size
            y = _border_size + _height_padding + row * _square_size

            pygame.draw.rect(
                self.screen,
                highlight_color,
                (x, y, _square_size, _square_size),
                width=4  # thickness of the border
            )

    def draw_pieces(self):
        """Draws pieces inside the board with border offset."""
        _border_size = Config.BORDER_SIZE
        _height_padding = Config.HEIGHT_PADDING
        for row in range(Config.BOARD_SIZE):
            for col in range(Config.BOARD_SIZE):
                #square = chess.square(col, 7 - row)
                square = (7 - row) * 8 + col
                sq = Square.get(coord=(row, col))
                #piece = self.position.get_piece(square)
                piece = self.position.get_piece(sq)
                if piece and (self.dragging_square is not sq):
                    #img = self.pieces[piece.symbol()]
                    user_piece = self.composition.position.convert_i_to_u(piece)
                    if user_piece == "=":
                        print("ERROR! Piece called = detected in internal fen, need to use internals")
                    #print(f"Being asked to draw a {user_piece} known internally as {piece}")
                    img = self.pieces[piece]
                    self.screen.blit(img, (_border_size + col * Config.SQUARE_SIZE,
                                           _border_size + _height_padding + row * Config.SQUARE_SIZE))

        # Draw dragged piece on top
        if self.dragging_piece:
            self.screen.blit(self.dragging_piece, self.dragging_pos)


    def old_setup_spare_pieces(self):
        """Defines positions for the spare pieces on the panel."""
        self.spare_pieces = []
        _panel_width = Config.PANEL_WIDTH
        x_offset_base = _panel_width * 0.1
        piece_order = ['K', 'Q', 'R', 'B', 'S', 'P']  # Display order

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

    def setup_spare_pieces(self, num_columns=4):
        """Defines positions for the spare pieces on the panel with dynamic columns."""
        self.spare_pieces = []  # flat list of (piece, (x, y))
        _panel_width = Config.PANEL_WIDTH
        x_offset_base = _panel_width * 0.1


        #print(f"This composition is called {self.problem_container.current_index}") 
        #print(f"This composition has these fairies to draw: {self.composition.fairies}")
        #print("Gonna debug here")


        # Spacing variables grouped together
        col_spacing = Config.SQUARE_SIZE      # horizontal gap between columns
        y_start = 50                          # starting Y position
        y_spacing = Config.SQUARE_SIZE + 20  # vertical gap between pieces

        # Fixed piece_order with 3 columns of 6 pieces each
        piece_order = [
            ['K', 'Q', 'R', 'B', 'S', 'P'],          # column 0
            ['k', 'q', 'r', 'b', 's', 'p'],          # column 1
            ['.MO', '.mo', '.MA', '.ma', 'G', 'g'],   # column 2
            ['.MO', '.mo', '.MA', '.ma', 'G', 'g']   # column 3
        ]

        # Draw fixed columns 0 and 1
        for col in range(2):
            x_offset = x_offset_base + col * col_spacing
            for i, piece in enumerate(piece_order[col]):
                y = y_start + i * y_spacing
                self.spare_pieces.append((piece, (x_offset, y)))

        # Now to try and draw the specific fairy pieces for this problem
        # First we need to format the list into columns
         # Draw fairies starting at column 2
        fairies = self.composition.fairies or []
        pieces_per_column = 6
        start_col = 2 # col 2 really means the third col as they go 0,1,2,3,...

        for idx, piece in enumerate(fairies):
            # Calculate which column and row within that column this piece goes in
            col = start_col + (idx // pieces_per_column)
            row = idx % pieces_per_column

            x_offset = x_offset_base + col * col_spacing
            y = y_start + row * y_spacing

            # Only draw if within num_columns limit
            if col < num_columns:
                self.spare_pieces.append((piece, (x_offset, y)))


    def build_clickable_objects(self, spare_pieces):
        clickable = []
        panel_x = Config.MAIN_WIDTH

        # Add panel pieces
        for user_char, (x, y) in spare_pieces:
            piece_instance = Piece.get_user(user_char)
            rect = pygame.Rect(panel_x + x, y, Config.SQUARE_SIZE, Config.SQUARE_SIZE)

            clickable.append({
                'location': 'panel',
                'piece': piece_instance,
                'rect': rect,
            })

        # Add toggle turning button
        radius = 2 * (Config.SQUARE_SIZE + 20) / 10
        circle_x = panel_x + radius + 5
        circle_y = Config.HEIGHT - radius - Config.SQUARE_SIZE / 10
        toggle_rect = pygame.Rect(
            circle_x - radius,
            circle_y - radius,
            2 * radius,
            2 * radius
        )

        clickable.append({
            'location': 'toggle',
            'rect': toggle_rect,
        })

        return clickable

    def draw_panel(self):
        # Move the panel to the right to avoid overlapping with the board
        panel_x = Config.MAIN_WIDTH  # Adjusted position
        pygame.draw.rect(self.screen, Config.PANEL_COLOUR, (panel_x, 0, Config.PANEL_WIDTH, Config.HEIGHT))

        # Draw spare pieces in the new panel position
        for piece, pos in self.spare_pieces:
            # Draw the piece at the correct adjusted position inside the panel
            internal_piece = self.composition.position.convert_u_to_i(piece)
            #print(type(self.pieces), internal_piece)
            #print(self.pieces)
            img = self.pieces[internal_piece]
            self.screen.blit(img, (panel_x + pos[0], pos[1]))  # Add panel_x to position the pieces correctly

        # Show clickable areas
        #for entry in self.clickable_objects:
        #    pygame.draw.rect(self.screen, (0, 255, 0), entry['rect'], 1)


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
            #return chess.square(col, 7 - row)  # Convert to chess square notation
            #return (7-row) * 8 + col
            return Square.get(coord=(row, col))

        return None  # If outside the board

    def change_square_color(self, square, new_color):
        """Receives the square under the mouse (0 to 63) and changes colour in the colour vector"""
        row, col = square.coord

        if new_color is not None:
            self.square_colors[row][col] = new_color
        else:
            # Reset to original
            self.square_colors[row][col] = self.get_default_color(row, col)

    def get_piece_from_panel(self, pos):
        """Check if user clicks on a spare piece."""
        panel_x = Config.MAIN_WIDTH

        for piece, piece_pos in self.spare_pieces:
            piece_x, piece_y = piece_pos
            if panel_x + piece_x <= pos[0] <= panel_x + piece_x + Config.SQUARE_SIZE and piece_y <= pos[1] <= piece_y + Config.SQUARE_SIZE:
                return piece
        return None

    def handle_mouse_down(self, pos):

        #self.check_legal_toggle_click(pos)
        #self.check_turn_toggle_click(pos)

        # New Clickable handler -- multi type return ClickResult
        result = self.identify_click_target(pos)
        #print(f"You just clicked {result}")

        # result.target is the Square or Piece

        # if result.type == "board":
        #     print("****Clicked board square:", result.target)
        # elif result.type == "panel":
        #     print("****Clicked panel piece:", result.target.internal_char)
        # else:
        #     print("****Clicked nothing relevant")

        mods = pygame.key.get_mods()
        if mods & pygame.KMOD_CAPS and not self.dragging_piece and result.type == 'board':
            #print("CAPS LOCK IS ON!")
            #print("Not mid-drag")
            #print("Click on board itself")
            if self.chosen_square: # Start square already highlighted
                if self.chosen_square is result.target:
                    # print("Square unselected")
                    self.chosen_square = None
                    return
                #print("Start square exists and it's not the square clicked")
                from_piece = self.position.get_piece(self.chosen_square)
                if from_piece: # there was a piece to move
                    self.position.move_piece(self.chosen_square, result.target,
                                             promotion_callback=self.gui_ask_for_promotion)
                    self.chosen_square = None
                else: # No piece to move
                    #print("Start square had no piece on!")
                    self.chosen_square = None
                    return
            else:
                self.chosen_square = result.target
                #print("Square selected")
                return
            # Get here is capslock is on but the click wasn't on the board
            # Just carry on!

        if result.type == "board":
            piece = self.position.get_piece(result.target)
            if piece:
                self.dragging_piece = self.pieces[piece]
                self.piece_source = "board"
                self.dragging_square = result.target # Square object
                self.dragging_pos = (pos[0] - Config.SQUARE_SIZE // 2, pos[1] - Config.SQUARE_SIZE // 2)
        elif result.type == "panel":
            self.dragging_piece = self.pieces[result.target.internal_char] # result.char = a Piece
            self.dragging_piece_symbol = result.target.user_char # result.chat = a Piece
            self.piece_source = "panel"
            self.dragging_pos = pos
            self.dragging_square = None
        elif result.type == "toggle":
            # Clicked the turn toggle button
            self.position.change_turn()
        elif result.type == "none":
            # print("You clicked nowhere interesting")
            return
        else:
            print("Shouldn't get here.")

        # sq = self.get_square_under_mouse(pos)
        # print(f"Move clicked on {sq}")
        # panel_piece = self.get_piece_from_panel(pos)
        # true_piece = Piece.get_user(panel_piece)
        #
        # if panel_piece:
        #     self.dragging_piece = self.pieces[true_piece.internal_char]
        #     self.dragging_piece_symbol = panel_piece
        #     self.piece_source = "panel"
        #     self.dragging_pos = pos
        #     self.dragging_square = None
        # elif sq is not None:
        #     piece = self.position.get_piece(sq)
        #     if piece:
        #         self.dragging_piece = self.pieces[piece]
        #         self.piece_source = "board"
        #         self.dragging_square = sq
        #         self.dragging_pos = (pos[0] - Config.SQUARE_SIZE // 2, pos[1] - Config.SQUARE_SIZE // 2)

    def handle_mouse_motion(self, pos):
        if self.dragging_piece:
            self.dragging_pos = (pos[0] - Config.SQUARE_SIZE // 2, pos[1] - Config.SQUARE_SIZE // 2)

    def handle_mouse_up(self, pos, button):
        """Handles dropping a piece, ensuring its color is preserved."""
        if not self.dragging_piece:
            return

        destination = self.identify_click_target(pos)
        added_a_piece_from_panel_with_right_click = False

        if self.piece_source == "board" and destination.type == "board":
            new_square = destination.target
            if new_square is not self.dragging_square: # i.e. new square release
                # New: move_piece now returns san
                san = self.position.move_piece(self.dragging_square, new_square, promotion_callback=self.gui_ask_for_promotion)
                if san: #If not None
                    self.info_box.update("move", san)
        elif self.piece_source == "panel" and destination.type == "board":
            new_square = destination.target
            piece_symbol = self.dragging_piece_symbol  # This is the symbol of the piece being dragged
            self.position.add_piece(new_square, piece_symbol)
            self.info_box.update("add", piece_symbol + new_square.alg)
            added_a_piece_from_panel_with_right_click = (button == 3)  # If using secondary mouse button keep piece in hand
        elif self.piece_source == "board" and destination.type != "board":
            self.info_box.update("remove", self.dragging_square.alg)
            self.position.remove_piece(self.dragging_square)

        # new_square = self.get_square_under_mouse(pos)
        #
        # print(f"Dragged piece from {self.piece_source} to {new_square}")
        # if self.piece_source == "board" and new_square is not None:
        #     if new_square is not self.dragging_square:  # Move only if dropped in a new square
        #         self.position.move_piece(self.dragging_square, new_square, promotion_callback=self.gui_ask_for_promotion)
        #
        #
        # elif self.piece_source == "panel" and new_square is not None:
        #     # Add the piece to the board and record the action for undo
        #     # New logic: only allow adding pieces when legality is off
        #     if not self.position.legal_moves_enabled:
        #         piece_symbol = self.dragging_piece_symbol  # This is the symbol of the piece being dragged
        #         self.position.add_piece(new_square, piece_symbol)
        #     else:
        #         print("You tried to drop a piece on the board, but legality was turned off. Turn it off first")
        #
        # elif self.piece_source == "board" and new_square is None: # Dropped piece off the board
        #     # print(f"You dropped the piece from {self.dragging_square} off the board! It will be removed")
        #     # Only allow removing a piece from board when legality is turned off
        #     if not self.position.legal_moves_enabled:
        #         self.position.remove_piece(self.dragging_square)
        #         #self.board.remove_piece_at(self.dragging_square)
        #     else:
        #         print("Dropped piece off board, but it was illegal so not executed")
        #     # self.game.delete_piece_at(self.dragging_square)

        if added_a_piece_from_panel_with_right_click:
            # Don't reset anything if we dropped a piece from the panel with our right mouse button
            # Set fps_high
            self.adjust_fps(self.high_fps)
            return

        # Reset dragging state
        self.dragging_piece = None
        self.dragging_square = None
        self.piece_source = None

    def identify_click_target(self, pos):
        """
        Returns a ClickResult: type = 'board', 'panel', 'toggle', or 'none'
        target = Square instance or Piece instance
        """
        square = self.get_square_under_mouse(pos)
        if square:
            return ClickResult(type="board", target=square)

        #print(f"Clickable pieces/objects before we check to see if we clicked on a panel one are {self.clickable_objects}")
        for entry in self.clickable_objects:
            if entry['rect'].collidepoint(pos):
                return ClickResult(type=entry['location'],
                                   target=entry.get('piece'))

        return ClickResult(type="none")

    def gui_ask_for_promotion(self):
        """Waits for the user to press a key to select a promotion piece."""

        # Available pieces for promotion
        valid_choices = ['Q', 'R', 'B', 'S']

        pygame.display.flip()  # Update the display

        running = True
        selected_piece = None

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    key = pygame.key.name(event.key).upper()
                    if key in valid_choices:
                        selected_piece = key
                        running = False

            self.clock.tick(30)

        return selected_piece

    def reverse_cycle_fen(self):
        """Move back to the previous problem"""

        print("Moving to previous problem")

        if self.problem_container.num_compositions == 1:
            print("Only 1 composition, why are you trying to move?")
            return

        self.problem_container.go_back_one()
        self.update_after_cycle()


    def cycle_fen(self):
        """Cycle through the FEN list and update the game and window title."""

        print("Moving to next problem")

        if self.problem_container.num_compositions == 1:
            print("Only 1 composition, why are you trying to move?")
            return

        self.problem_container.go_forward_one()
        self.update_after_cycle()

    def update_after_cycle(self):
        """Stuff to do after changing the current compositions pointed to by the container"""

        self.composition = self.problem_container.get_current()
        self.composition.create_position()  # fen set automatically by composition
        self.position = self.composition.get_position_object()

        # NEW Update game state
        #self.custom_title = self.composition.title
        #self.custom_stip = self.composition.stipulation
        self.set_custom_text(title_text=self.composition.title, stip_text=self.composition.stipulation)
        self.info_box.update("new")

        #self.draw_custom_stip()
        #self.draw_custom_title()
        self.draw_custom_text()
        self.composition.tree_position = 0

        # Fairy piece panel
        # WE MAY WANT TO RECALC THE CLICKABLE PIECES AND REDO THE setup_panel_pieces here
        self.setup_spare_pieces()
        self.clickable_objects = self.build_clickable_objects(self.spare_pieces)
        self.draw_panel()

        # PROBLEM_LIST[-1] the last element is now the one we're working with
        # PROBLEM_LIST[0] will be loaded when we NEXT run the cycle

        # Redraw tk moves_windows
        if self.composition.move_window_version == True:
            self.moves_window_queue.put(
                #   ("load moves grid", self.PROBLEM_LIST_ingui[-1]["move_tree"]))  # Value passed is PROBLEM_LIST index of new game
                # ("load moves grid", current_fen_data["move_tree"])) # OLD
                ("load moves grid", self.composition.move_tree))  # NEW
            return
        else:
            return

    def adjust_fps(self, new_fps):
        self.target_fps = new_fps
        #print(f"New fps if {new_fps}")

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
            ("F1/F3", "Cycle to next/previous FEN in the loaded file"),
            ("U", "Undo last action/move"),
            ("T", "Toggle whose turn it is"),
            ("1/2/3", "Highlight square RED/YELLOW/GREEN"),
            ("0", "Remove hovered square's highlighting"),
            ("DELETE", "Clear all highlighting"),
            ("Ctrl + C", "Copies current position to clipboard as FEN"),
            ("+ or =", "Increase board size"),
            ("-", "Decrease board size"),
            ("LEFT/RIGHT", "Navigate through pre-loaded sequence"),
            ("END", "Jump to end of pre-loaded sequence"),
            ("H", "Show/Hide this help window"),
            ("Q/R/S/N", "Choose promotion piece during promotion attempt")
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
def old_load_images():
    """
    Loads the png images of all pieces into a vector
    These pngs are available in sizes 40x40 up to 100x100 and were generated from an SVG
    """
    pieces = {}
    square_size: int = Config.SQUARE_SIZE
    for piece in ['p', 's', 'b', 'r', 'q', 'k', 'g']:
        img_path = get_resource_path(f'images/b{piece.upper()}_{square_size}px.png')
        img_black = pygame.image.load(img_path)
        pieces[piece] = pygame.transform.scale(img_black, (square_size, square_size))  # Scale to fit squares

        img_path = get_resource_path(f'images/w{piece.upper()}_{square_size}px.png')
        img_white =  pygame.image.load(img_path)
        pieces[piece.upper()] = pygame.transform.scale(img_white, (square_size, square_size))  # Scale for white pieces
    return pieces

def load_images():
    """
    Loads PNG images for all registered pieces using their internal_char and colour.
    Returns a dict mapping internal_char -> pygame Surface.
    """
    pieces_images = {}
    square_size = Config.SQUARE_SIZE

    for piece in Piece.all():
        img_path = get_resource_path(f'images/{piece.image_filename(square_size)}')

        try:
            image = pygame.image.load(img_path)
        except pygame.error as e:
            print(f"Failed to load image for {piece}: {img_path}\n{e}")
            continue

        image = pygame.transform.scale(image, (square_size, square_size))

        if piece.mirror:
            image = pygame.transform.flip(image, flip_x=True, flip_y=False)  # flip horizontally (before any rotation)

        if piece.rotation != 0:
            # Pad with transparent margin
            padded_size = int(square_size * 1.5)
            padded = pygame.Surface((padded_size, padded_size), pygame.SRCALPHA)
            rect = image.get_rect(center=(padded_size // 2, padded_size // 2))
            padded.blit(image, rect)

            rotated = pygame.transform.rotate(padded, -piece.rotation)

            # Crop back to square_size and center it
            final = pygame.Surface((square_size, square_size), pygame.SRCALPHA)
            rect = rotated.get_rect(center=(square_size // 2, square_size // 2))
            final.blit(rotated, rect)
            image = final

        pieces_images[piece.internal_char] = image

    return pieces_images


def generate_fen_path(beginning, moves):
    """Create a sequence of FENs from an initial fen and the list of moves already"""

    # We will include in the FEN sequence non-FENs called "GoToHome", "GoToCheckpoint" and "SaveCheckpoint" for debugging and later flexibility
    # But they will be skipped when loading the next FEN

    # Read all the moves into a list
    # Already done, in moves

    # Load the starting FEN into a chess object, i.e. create a temporary game e.g. via a chess.board(START)
    # temp_game = TempGame(beginning)
    temp_game = TempChessPosition(fen=beginning)

    # Create the move_tree already in finished arrangement
    grid_data = [] # 2D grid of (label, fen) data
    next_i = 0
    next_j = 0

    # Create dictionary to store text labels for each FEN
    move_id_to_label = {}

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
            move_id_to_label[loc_move_id] = move + " Back" # will be "<" or "<<" or "<<<" etc..
            loc_checkpoint = loc_button_fen
            # Jump back to column of checkpoint we're going to
            next_j = checkpoint_data[loc_checkpoint] # Should be stored column number for this checkpoint
            # Drop down one row for next move
            next_i += 1
        elif loc_button_label == "H":
            move_id_to_label[loc_move_id] = "Home"
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
            move_id_to_label[loc_move_id] = loc_button_label
            # Update next box
            next_j += 1
            if next_j >= max_columns:
                next_j = 0
                next_i += 1

    print("Move grid contents:\n")
    
    for row_idx, row in enumerate(grid_data):
        print(f"Row {row_idx}: ", end="")
        for cell in row:
            if cell is None:
                print(f"[ ]", end=" ")
            else:
                label, fen, id = cell
                print(f"[{id}]", end=" ")
        print()  # Newline after each row

    return temp_game.result(), grid_data, move_id_to_label

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
    root.geometry(TK_GEOMETRY)
    #moves_window = root
    root.title("Moves")

    # Window positioning
    #tk_x = pygame_x + pygame_width
    #tk_y = pygame_y - 30
    #root.geometry(f"+{tk_x}+{tk_y}")

    frame = tk.Frame(root)
    frame.pack(padx=10, pady=10, anchor='nw')

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

def start_processes(MWV, PL):

    if MWV == True:
    # Communication method
        main_window_queue = multiprocessing.Queue()
        moves_window_queue = multiprocessing.Queue()

        # Start both processes
        #gui_process = multiprocessing.Process(target=run_gui, args=(PL.copy(), MWV,
        #    passed_fen, window_title, args.title, args.stip, problem_list_loaded, main_window_queue, moves_window_queue, shutdown_event))
        gui_process = multiprocessing.Process(target=run_gui, args=(PL, MWV,
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
        # ChessGUI(PL.copy(), MWV, passed_fen, window_title, args.title, args.stip, problem_list_loaded, main_window_queue,
        #     moves_window_queue, shutdown_event).run()
        ChessGUI(PL, MWV, passed_fen, window_title, args.title, args.stip, problem_list_loaded, main_window_queue,
            moves_window_queue, shutdown_event).run()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    PROBLEM_LIST = []

    args = parse_arguments()  # Get arguments from command line
    MOVES_WINDOW_VERSION = not args.nomoves # Changed to make --nowindow required to disable
    window_title = args.window if args.window else "Chess Navigator" # Allow window name override
    passed_fen = args.fen if args.fen else None  # Use FEN if provided, otherwise default
    passed_fenlist = args.fenlist if args.fenlist else None
    problem_container = ProblemListContainer()
    problem_list_loaded =  False # Have we loaded problems from a file yet?

    # Read all the fens passed and find fairy pieces
    if passed_fen:
        # Case 1: Passed a single FEN directly
        passed_fen = expand_multiple_blank_rows(passed_fen)
        all_fens = [passed_fen]
        # Passing a fen via --fen should override PROBLEM_LIST
        comp = problem_container.add_composition(
                title=args.title,
                fen=passed_fen,
                moves=None,
                stipulation=args.stip
        )
    else:
        # Not passed a fen, so look for file to load
        problem_list_loaded = load_problem_list_from_file(PROBLEM_LIST, passed_fenlist) # default is PROBLEM_LIST.txt but user could customize
        # Return value is TRUE or FALSE based on success in finding file.

        if not problem_list_loaded:
            # No passed_fen and no passed_fen: need to set a default board
            comp = problem_container.add_composition(
                title=None,
                fen='rsbqkbsr/pppppppp/8/8/8/8/PPPPPPPP/RSBQKBSR',
                moves=None,
                stipulation=None
            )
            all_fens = ['rsbqkbsr/pppppppp/8/8/8/8/PPPPPPPP/RSBQKBSR']
        else: # Here we have filled PROBLEM_LIST will all passed fens from file.
            # Case 3: Loaded multiple problems from file, extract their FENs
            all_fens = [fen_data['fen'] for fen_data in PROBLEM_LIST]     
    
    # full_fenlist contains all fens to be studied
    # so we can create the extra mapping and extra pieces now
    
    # New fen unicode stuff

    # All user_chars in EXTRA_PIECES from custom_pieces.yml
    all_user_chars = [piece_data['user_char'] for piece_data in EXTRA_PIECES.values()]

    # Create global piece_map.json and list new tokens
    problem_container.u_to_i_dict, problem_container.i_to_u_dict, new_tokens = load_and_update_mapping(fens=all_fens, extras=all_user_chars)
    #new_tokens contains n+1 lists, the last is ALL pieces, the first n should be saved with their respective compositions

    if passed_fen: # Special case of command_line fen need to do the conversion for single item
        problem_container.set_current(1)
        only_comp = problem_container.get_current() # Get current (and only) composition
        converted = convert_fen_board_section(only_comp.fen, problem_container.u_to_i_dict)
        only_comp.fairies = new_tokens[0]
        only_comp.fen = converted
        only_comp.u_to_i_map = problem_container.u_to_i_dict
        only_comp.i_to_u_map = problem_container.i_to_u_dict


    #comp.u_to_i_map, comp.i_to_u_map, new_tokens = load_and_update_mapping(fens=all_fens)
    # new_tokens contains all the new-ish pieces we have just seen
    #print(new_tokens)
    # Create singletons for all the pieces
    #print(Piece.all())
    create_extra_pieces(problem_container.u_to_i_dict, EXTRA_PIECES) # This needs to be run again later after a Windows spawn
    #print(Piece.all())
    print(Piece.all_user_chars())
    print(Piece.all_internal_chars())

    # internal pieces
    all_internal_pieces = Piece.all_internal_chars()
    all_user_chars = Piece.all_user_chars()
    valid, errors = validate_all_fens(all_fens, all_internal_pieces, all_user_chars, problem_container.u_to_i_dict, problem_container.i_to_u_dict)

    if not valid:
        # Create a hidden Tk root window
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        messagebox.showerror("Invalid FEN(s)", "\n".join(errors))
        root.destroy()  # Cleanly close Tkinter
        sys.exit(1)  

    if problem_list_loaded:
        # Here we generate move trees from the moves
        # This is only Case 3 above
        """ OLD METHOD
        for fen_data in PROBLEM_LIST:
            given_fen = fen_data['fen']
            move_list = fen_data['moves'].split()
            print("\n*** Analysing given moves for a position ***\n")
            
            ## CORE FUNCTIONS, NOW MOVED TO BELOW
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
        """

        # Put the problem skeletons into the container
        for idx, fen_data in enumerate(PROBLEM_LIST):
            comp = problem_container.add_composition(
                title=fen_data.get('title', ''),  # Use get in case some entries lack these fields
                fen=fen_data['fen'],
                moves=fen_data.get('moves', ''),
                stipulation=fen_data.get('stip', '')
            )
        
            # Test the internal conversion for this fen works
            #print("This fen will be converted to internal format:")
            #print(f"\nOriginal FEN:  {comp.fen}")
            converted = convert_fen_board_section(comp.fen, problem_container.u_to_i_dict)
            #print(f"Internal FEN:  {converted}")
            #restored = convert_fen_board_section(converted, problem_container.i_to_u_dict)
            #print(f"Restored FEN:  {restored}")

            # Overwrite the fen with internal version
            comp.fen = converted
            # Save the global dictionary lookup into the composition
            # (for consistency with existing later code which looks for it there)
            comp.u_to_i_map = problem_container.u_to_i_dict
            comp.i_to_u_map = problem_container.i_to_u_dict

            # Creating specific database of pieces to print for this composition
            #print(f"For composition {idx+1}: pieces {new_tokens[idx]} will be loaded")
            comp.fairies = new_tokens[idx]

            # Show mappings
            #print_mapping("User → Internal Mapping", comp.u_to_i_map)
            #print_mapping("Internal → User Mapping", comp.i_to_u_map)

            # NEW - Generate fen_tree and move tree (used to happen above)
            
            # Generate trees (using new internal fen)
            move_list = comp.moves.split()
            fen_tree, move_tree, move_id_to_label = generate_fen_path(comp.fen, move_list)

            # Store in Composition
            comp.fen_tree = fen_tree[0]
            comp.ids = fen_tree[1]
            comp.move_tree = move_tree
            comp.move_id_to_label = move_id_to_label



            # If moves_window is asked for, enable for this composition
            if MOVES_WINDOW_VERSION:
                comp.turn_on_move_windows_messaging()

    #start_processes(MOVES_WINDOW_VERSION, PROBLEM_LIST)

    #Moving start_processes logic into __main__
    #start_processes(MOVES_WINDOW_VERSION, problem_container)

    MWV = MOVES_WINDOW_VERSION
    PL = problem_container

    if MWV:
    # Communication method
        main_window_queue = multiprocessing.Queue()
        moves_window_queue = multiprocessing.Queue()

        # Start both processes
        #gui_process = multiprocessing.Process(target=run_gui, args=(PL.copy(), MWV,
        #    passed_fen, window_title, args.title, args.stip, problem_list_loaded, main_window_queue, moves_window_queue, shutdown_event))
        gui_process = multiprocessing.Process(target=run_gui, args=(PL, MWV,
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
        # ChessGUI(PL.copy(), MWV, passed_fen, window_title, args.title, args.stip, problem_list_loaded, main_window_queue,
        #     moves_window_queue, shutdown_event).run()
        ChessGUI(PL, MWV, passed_fen, window_title, args.title, args.stip, problem_list_loaded, main_window_queue,
            moves_window_queue, shutdown_event).run()

# TO DO
# Pass the build_buttons the actual move tree for the current game (do it inside the ChessGUI via a message like
# "load_moves" and listener can pass PROBLEMLIST['moves_tree'] to some build function
# need to separate the draw the button frame and draw the buttons (based on a grid)
# Change button code to put fens behind buttons

# When button clicked, pass the fen to the pygame, run function to set fen
