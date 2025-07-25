TODO:
Allow Kg1 when not castling, just don't move the rook?
Stip printing borked.
F1/F3 in help popup?
Remove green boxes
_internal folder maintain in .iss file in TempChessNav
Sample PROBLEM_LIST.txt provided (see TempChessNav)

My Chess Navigator program for showing chess problems.

The PROBLEM_LIST.txt file shows the template for autoloading lots of FENs (with optional title and subtext/stipulation).

## Method of move entry

New move entry is by dragging the mouse.

Various shortcuts are currently implemented but not documented.

| Key  | Action                                                     |
|------|------------------------------------------------------------|
| HOME or R | Return to home position                               |
| INSERT | Save current position as home position                   |
| Z    | Zero the board (and turn off legality to allow adding)     |
| F1/F3| Cycle to next/previous FEN in the loaded file              |
| U    | Undo last move (cannot currently undo after add/remove)    |
| L    | Toggle Legality (also clickable)                           |
| T    | Toggle whose turn it is (also clickable)                   |
| (1,2,3,0) | Highlight hovered square: RED, YELLOW, GREEN, NO-HIGHLIGHT |
| Ctrl + C | Copy current position to clipboard as FEN                  |
| +/-  | Decrease/Increase window size                              |
| DELETE | Clear all highlighting                                     |
| ➡    | Step into predefined move tree                             |
| ⬅    | Step back along predefined move tree                       |
| END  | Jump to end of predefined move tree                        |
| rnbq | Select promotion piece  (during promotion attempt)         |

### Adding and removing pieces

Adding new pieces by dragging them from the extra pieces panel requires first toggling "Legality" off.

Removing pieces by dragging them from the board and dropping them off the board requires first toggling "Legality" off.

If you add pieces from the panel using the right-mouse-button you can keep adding more pieces of the same type without returning to the panel.

## For pre-stored analysis

### Predefined tree file

Default file is PROBLEM_LIST.txt, can be overridden with `--fenlist` command-line argument.

### Syntax of tree file

Blank lines and lines not beginning "Title:", "FEN:", "Subtext:" or "Moves:" are ignored.
Sensible to separate problems with blank lines.

Title: Text above the diagram
FEN: FEN of the diagram
Subtext: Text to appear below the diagram
Moves: e2e4 g8f6 e4e5 f6e5 etc.. (see below)

Sample move syntax is as follows:

e2e4 e7e5 g1f3 b8c6 * f1b5 a7a6 < f1c4 f8c5 * b2b4 c5b4 < c2c3 d7d5 << d2d4 e5d4 H g1f3 g7g5 f3g5

| Format | Result                                      |
|--------|---------------------------------------------|
| a1b3   | Move piece from a1 to b3                    |
| a7b8n  | Promote a7b8 to a knight                    |
| *      | Save the current position for future return |
| <      | Go back to last saved position              |
| <<     | Go back to second last saved position       |
| <<<    | Go back to third last saved position        |
| etc..  |                                             |
| H      | Go back to Home position for this problem   |
| +Ra7   | Add a white rook to a7 (capital = white)    |
| -e4    | Remove whatever piece is on e4              |
| &      | Separator for multiple simultaneous moves   |

When using the `--movewindow` additional moves window, you can also navigate the position tree by clicking the moves in that window.

## For customized board colours and start-up window size

### config.json file format - default values

Edit a file with this name in the executable's folder and it will be used instead.

{
    "white_squares": [238, 238, 210],
    "black_squares": [118, 150, 86],
    "panel_colour": [20, 60, 60],
    "square_size": 70,
    "title_font_size": 28,
    "stip_font_size": 28
}

Note, square sizes must be drawn from 40,50,60,70,80,90,100. As anti-aliased piece images exist of these sizes.

## Command line options: examples

--window "New title"     : Specifies window title (used for screen capture)
--movewindow             : Loads the pop-up move window

--fen "8/7R/2K4k/..."    : Passes a single FEN position
--title "My Problem"     : Forces a title for the single FEN passed
--stip "h#2"             : Forces a stipulation for the single FEN passed

--fenlist problems.txt   : Specifies a file with multiple FENs (default is PROBLEM_LIST.txt)

## Fairy pieces

Default names for pieces are KQRBSP for King, Queen, Rook, Bishop, Knight, Pawn

Custom pieces can be created in the file **custom_pieces.yml**

You are recommended to run the program once, which will create a default version of this file for you. You can then edit that file to add your own pieces. Only if no custom_pieces.yml file is present will a new one be automatically created.

You must specify a name for use in the FEN according to the Popeye rules:
    + Either a single letter;
    + Or a dot followed by two letters or numbers;
    + Optionally a = on the front indicates neutral

e.g. 's', 'N', '.ab', '.L1', '.l1' the first letter's case typically determines colour