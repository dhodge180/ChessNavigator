# Changelog

## [latest]

- want to look into antialiasing and single image per piece

## [v3.6.5]

- moving tkinter global loading to find screen size into __main__ [large change]
- adding self to the Ctrl+C user dictionary looked, possible scoping bug
- migrate to pygame-ce from pygame (now works with Python3.14)
- add delay to launch game window until after moves window (was causing initial focus theft)

## [v3.6.4]

- Three new animation options available in config.json
- animation_type controls the easing style of moving pieces (overshoot, ease_out, none)
- animation_ghost toggles the fading ghost piece shown at the origin square during a move
- animate_knight_hops toggles the arcing path for hopper pieces (knights, camels, etc.)

## [v.3.6.3]

- Number of frames per move animation is now called "animation_frames" and in the config.json file
	1 = instant move
	60 = 60 frames (so approx 1 second, since rendering at 60fps)
	30 = half a second per move of piece sliding
- e.p renders on two rows in the move window
- small tidying up of Sample_PROBLEM_LIST.txt

## [v3.6.2]

- Last move correctly clears upon reaching start of problem (when reversing)
- Last move text now render compound moves from PROBLEM_LIST on one line with a -> symbol
- move window uses improved san (algebraic notation)
- compound and compound reverse tree navigation animations work
- Add animation routine for tree forward. new helper functions also used in draw_pieces and draw_board

## [v3.6.1]

## Added
- Redo (via key I) now updates Last Move window (so actually a full history is kept, until it gets overwritten for any reason)
- Last move window begins with Press H for help instruction

## [v3.6]

### Added
- New `InfoBox` class displaying context-sensitive game updates in the bottom-right panel
- Last move shown in InfoBox when navigating tree with arrow keys
- Back moves (`<`, `<<` etc.) now correctly display the label of the move that led to the checkpoint
- En passant moves now render correct SAN notation

### Changed
- Undo no longer jumps back to home position when all manually played moves have been undone
- Tree navigation resets move history root when no manual moves have been played
