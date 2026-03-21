# Changelog

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
