My Chess Navigator program for showing chess problems.

The PROBLEM_LIST.txt file shows the template for autoloading lots of FENs (with optional title and subtext/stipulation).

Various shortcuts are currently implemented but not documented.

| Key  | Action                                                     |
|------|------------------------------------------------------------|
| HOME or R | Return to home position                                    |
| INSERT | Save current position as home position                     |
| Z    | Zero the board                                             |
| F1   | Cycle to next FEN in the loaded file                       |
| U    | Undo last move (cannot currently undo beyond additions     |
| L    | Toggle Legality                                            |
| T    | Toggle whose turn it is                                    |
| (1,2,3,0) | Highlight hovered square: RED, YELLOW, GREEN, NO-HIGHLIGHT |
| Ctrl + C | Copy current position to clipboard as FEN                  |
| + or = | Increase window size                                       |
| -    | Decrease window size                                       |
| DELETE | Clear all highlighting                                     |
| ➡    | Step into predefined move tree                             |
| ⬅    | Step back along predefined move tree                       |
| END  | Jump th end of predefined move tree                        |
| rnbq | Select promotion piece  (during promotion attempt)         |

## For pre-stored analysis

If you wish to be able to navigate a pre-determined tree then the path can be written in PROBLEM_LIST in advance.
Sample syntax is as follows:

e2e4 e7e5 g1f3 b8c6 * f1b5 a7a6 < f1c4 f8c5 * b2b4 c5b4 < c2c3 d7d5 << d2d4 e5d4 H g1f3 g7g5 f3g5

| Format | Result                                      |
|--------|---------------------------------------------|
| a1b3   | Move piece from a1 to b3                    |
| a7b8N  | Promote a7b8 to a knight                    |
| *      | Save the current position for future return |
| <      | Go back to last saved position              |
| <<     | Go back to second last saved position       |
| <<<    | Go back to third last saved position        |
| etc..  |                                             |
| H      | Go back to Home position for this problem   |
| +Ra7   | Add a white rook to a7 (capital = white)    |
| -e4    | Remove whatever piece is on e4              |

## For customized board colours and start-up window size

### config.json file format - default values

{
    "white_squares": [238, 238, 210],
    "black_squares": [118, 150, 86],
    "panel_colour": [20, 60, 60],
    "square_size": 70
}

Note, square sizes must be drawn from 40,50,60,70,80,90,100. As anti-aliased piece images exist of these sizes.

Command line options:

--window "New title" specifies Window title (for screen capture purposes)

--movewindow loads the pop-up move window

--fen passes a single fen
--title forces title of single fen passed
--stip forces stip of single fen passed

--fenlist passes the file to look at (default PROBLEM_LIST.txt is always looked for anyway)

