import os
# import chess
from mychess import ChessPosition, Composition, ProblemListContainer, print_board_matrix
from fen_mapper import load_and_update_mapping, load_existing_map, MAP_FILE, convert_fen_board_section
import re

def print_mapping(title, mapping):
    print(f"\n{title}")
    for k, v in mapping.items():
        print(f"  {k} → {v}")

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
        lines.append("\n")  # Adds a blank line to the end

    temp_fen_data = blank_non_required.copy()

    for line in lines:
        line = line.strip()  # Remove leading/trailing whitespaces

        # We encounter a Title
        if line.startswith("Title:"):
            if temp_fen_data["title"] != "":  # We already have a title!
                if "fen" not in temp_fen_data:  # Second title, no FEN yet. Stupid.
                    print("Error, second title before FEN. Wiping entry.")
                elif "fen" in temp_fen_data:  # We have a FEN already
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
            if "fen" in temp_fen_data:  # We already have a fen!
                # Just save it! And start a new one
                PROBLEM_LIST_inload.append(temp_fen_data)  # Save (possibly with subtext)
                print("Resetting for next problem...")
                temp_fen_data = blank_non_required.copy()

            # Now if we had a fen or didn't, we need to insert the new fen
            temp_fen_data["fen"] = line[len("FEN:"):].strip().strip('"')

        # We encounter a non-fen (one of "these")
        elif line.startswith("Subtext:"):
            if temp_fen_data["stip"] != "":  # We already have one of these
                if "fen" in temp_fen_data:  # Great we already have a FEN.
                    PROBLEM_LIST_inload.append(temp_fen_data)
                elif "fen" not in temp_fen_data:  # Second one of these, but no FEN yet.
                    print("Error, second Subtext before FEN. Wiping entry.")
                # In both cases now reset and save new one of these
                print("Resetting for next problem...")
                temp_fen_data = blank_non_required.copy()
            # In both cases ready to accept next one of these
            temp_fen_data["stip"] = line[len("Subtext:"):].strip().strip('"')

        # We encounter a non-fen (one of "these")
        elif line.startswith("Moves:"):
            if temp_fen_data["moves"] != "":  # We already have one of these
                if "fen" in temp_fen_data:  # Great we already have a FEN.
                    PROBLEM_LIST_inload.append(temp_fen_data)
                elif "fen" not in temp_fen_data:  # Second one of these, but no FEN yet.
                    print("Error, second Subtext before FEN. Wiping entry.")
                # In both cases now reset and save new one of these
                print("Resetting for next problem...")
                temp_fen_data = blank_non_required.copy()
            # In both cases ready to accept next one of these
            temp_fen_data["moves"] = line[len("Moves:"):].strip().strip('"')

        # We encounter a blank line
        elif line == "":  # a blank line
            # Assume this separates problems
            if "fen" in temp_fen_data:  # at least we have a fen
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
    just_fens = [] # Create a list of all the fens loaded to use to make the unicode mapping
    for each_fen_data in PROBLEM_LIST_inload:
        print("------------------------------------------------------------------------------------------------------")
        # print(fen_data)
        print(f"Title: {each_fen_data['title']}")
        print(f"FEN: {each_fen_data['fen']}")
        just_fens.append(each_fen_data['fen'])
        print(f"Stip: {each_fen_data['stip']}")
        print(f"Moves: {each_fen_data['moves']}")
    print("------------------------------------------------------------------------------------------------------")

    print("Now let's generate the unicode mapping")
    user_to_internal,_,_ = load_and_update_mapping(just_fens) # Saved to file, will load later

    # Show mappings
    print_mapping("User → Internal Mapping", user_to_internal)

    for each_fen_data in PROBLEM_LIST_inload:
        each_fen_data['fen'] = convert_fen_board_section(each_fen_data['fen'], user_to_internal)

    if PROBLEM_LIST_inload:
        print("Successful load from PROBLEM_LIST file")
        return True
    else:
        print("Did not load from PROBLEM_LIST file")
        return False

def generate_fen_path(beginning, moves):
    """Create a sequence of FENs from an initial fen and the list of moves already"""

    # We will include in the FEN sequence non-FENs called "GoToHome", "GoToCheckpoint" and "SaveCheckpoint" for debugging and later flexibility
    # But they will be skipped when loading the next FEN

    # Read all the moves into a list
    # Already done, in moves

    # Load the starting FEN into a chess object, i.e. create a temporary game e.g. via a chess.board(START)
    temp_game = TempGame(beginning)

    # Create the move_tree already in finished arrangement
    grid_data = []  # 2D grid of (label, fen) data
    next_i = 0
    next_j = 0

    checkpoint_data = [1]
    # checkpoint_data.append(1)

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
            next_j = checkpoint_data[loc_checkpoint]  # Should be stored column number for this checkpoint
            # Drop down one row for next move
            next_i += 1
        elif loc_button_label == "H":
            next_j = 0
            next_i += 1
        elif loc_button_label == "&":
            # We are reading an & let's try skipping back two?
            next_j -= 1  # Perfect, except we lose record of text on button, can we append?
            special_label_append = True
        elif loc_button_label == "*":
            print("Save action")
            # loc_button_fen will contain index of checkpoint
            loc_checkpoint = loc_button_fen
            checkpoint_data.insert(loc_checkpoint, next_j)  # Should store current column for this checkpoint number

        else:  # Only create button if not back or * or H
            if special_label_append:  # if we're about to overwrite the first move in an and statement
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

class TempGame:
    def __init__(self, first_position):
        self.position = ChessPosition()
        self.position.set_fen(first_position)
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
        self.checkpoints.append(first_position)  # Start with the home position (shouldn't be necessary)

    def add_this_fen(self):
        self.generated.append(self.position.fen)
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

        piece = self.position.get_piece(from_square)
        target_piece = self.position.get_piece(to_square)

        piece_colour = self.position.get_piece_colour(piece)
        target_piece_colour = self.position.get_piece_colour(target_piece)
        
        if piece is None:
            print("Uhm, there was meant to be a piece here!")
            return None, None

        if piece_colour != self.position.turn:
            print("You moved out of turn, but I'll allow it.")
            self.position.change_turn() # Swap player to move

        if target_piece is not None:
            if piece_colour == target_piece_colour:
                print("You're trying to consume one of your own pieces. I'll allow it.")
                deletion_move = self.convert_move("-" + to_square)
                and_move = self.convert_move("&")
                self.move_handlers["remove"](deletion_move)
                self.move_handlers["and"](and_move)

        # Implement the logic for handling regular moves
    #mv = chess.Move.from_uci(from_square + to_square)

        # Move recorded 2
    #san_version = self.board.san(mv)
        # print(f"This move is called {san_version}")
    #button_label = str(san_version)
        # print(f"BUTTON: {button_label}")

        move_string = from_square + to_square
        san_version = piece + move_string
        self.position.move_piece(from_square, to_square)

    #self.board.push(mv)
        self.add_this_fen()

        return san_version, self.position.fen

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

        piece = self.position.get_piece(from_square)
        target_piece = self.position.get_piece(to_square)

        piece_colour = self.position.get_piece_colour(piece)
        target_piece_colour = self.position.get_piece_colour(target_piece)

        if piece is None:
            print("Uhm, there was meant to be a piece here!")
            return None, None

        if piece_colour != self.position.turn:
            print("You moved out of turn, but I'll allow it.")
            self.position.change_turn() # Swap player to move

        if target_piece is not None:
            if piece_colour == target_piece_colour:
                print("You're trying to consume one of your own pieces. I'll allow it.")
                deletion_move = self.convert_move("-" + to_square)
                and_move = self.convert_move("&")
                self.move_handlers["remove"](self, deletion_move)
                self.move_handlers["and"](self, and_move)

    #mv = chess.Move.from_uci(from_square + to_square + promotion_piece.lower())

        # Move recorded 2
    # san_version = self.board.san(mv)
        # print(f"This move is called {san_version}")
    # button_label = str(san_version)
        # print(f"BUTTON: {button_label}")

        #internal_promotion_piece = u_to_i(promotion_piece.lower(), self.position.user_to_internal_map)
        move_string = from_square + to_square + promotion_piece.lower()
        san_version = piece + move_string
        self.position.promote_pawn(from_square, to_square, promotion_piece.lower())

    #self.board.push(mv)
        self.add_this_fen()

        return san_version, self.position.fen
    
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
        self.checkpoints.append(self.position.fen)

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
        self.position.set_fen(self.checkpoints[self.current_checkpoint_index])
        self.add_this_fen()  # Save the fen to the generated list

        return "H", self.current_checkpoint_index

    def handle_skipback(self, move):
        """ e.g. {'type': 'skipback', 'steps': n} """

        distance = move['steps']
        # Move recorded
        print(f"Skipping back {distance} level(s)")
        # Implement the logic for skipping back
        self.current_checkpoint_index = max(0, self.current_checkpoint_index - distance + 1)
        self.position.set_fen(self.checkpoints[self.current_checkpoint_index])
        self.add_this_fen()  # Save the fen to the generated list
        # print(self.board)

        return "back", self.current_checkpoint_index

    def handle_and(self, _):
        """{'type': 'and'} """
        # Move recorded
        print(f"...playing another move at the same time...")
        print(f"BUTTON: save current button text for appending next move")
        self.generated.pop()  # This should remove the last element
        self.id_record.pop()  # Copy same behavuour on move_id
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
    #self.board.set_piece_at(chess.parse_square(to_square), chess.Piece.from_symbol(added_piece))
        self.position.add_piece(to_square, added_piece)
        self.add_this_fen()  # Save the fen to the generated list

        return button_label, self.position.fen

    def handle_remove(self, move):
        """ {'type': 'remove', 'from': 'a1'} """

        from_square = move['from']
        piece_there = self.position.get_piece(from_square)
        # Move recorded
        print(f"Removing piece from {from_square}")
        button_label = "-" + str(piece_there) + str(from_square)
        print(f"BUTTON: {button_label}")

        # Implement the logic for removing a piece
    #self.board.remove_piece_at(chess.parse_square(from_square))
        self.position.remove_piece(from_square)
        self.add_this_fen()

        return button_label, self.position.fen

    def handle_set_whos_turn(self, move):
        """e.g. {'type': 'player_turn', 'player': 'B'}
        Request to set whose turn it is
        """
        player_to_move = move['player']
    #current_turn = "w" if self.position.turn == 'w' else "b"  # Find whos turn it current is
        current_turn = self.position.turn
        if player_to_move != current_turn:
            # Target player to move means we need to change
            self.position.change_turn()
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

        # Case b: letter-number-letter-number-letter (e.g. a7a8Q), where last letter is one of prnbQPRNBQ
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
        elif re.fullmatch(r'^\+([prsbqPRSBQ])[a-h][1-8]$', move):
            # This matches a format like '+Rb2'
            return {'type': 'add', 'piece': move[1], 'to': move[2:]}

        # Case g: string "-letter-number" (e.g. -e4)
        elif re.fullmatch(r'^-[a-h][1-8]$', move):
            # This matches a format like '-e4'
            return {'type': 'remove', 'from': move[1:]}

        else:
            return {'type': 'invalid', 'move': move}

def populate_problem_list(PROBLEM_LIST, fen_file = "PROBLEM_LIST.txt"):
    '''Pass me the blank list to fill'''

    # PROBLEM_LIST = []

    passed_fenlist = fen_file
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
    return PROBLEM_LIST

A = []

populate_problem_list(A)
print(f"{A[0]}")

# TODO:
# edit this code so that it uses the Composition and Container class.
#     Also so that it doesn't use chess but uses my new ChessPosition class.
    
#  We will take TempGame and change it into a ChessPosition class?
#  Dual use of ChessPosition class for generating the PROBLEM_LIST list and also later for the GUI diagram?
