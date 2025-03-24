#!/bin/bash

# Define file names in correct order (2 rows, 6 columns)
names=("wK" "wQ" "wB" "wN" "wR" "wP" "bK" "bQ" "bB" "bN" "bR" "bP")

# Crop parameters
width=45    # Width per piece
height=45   # Height per piece

# Render at high DPI (adjust as needed)
density=300

# Loop through each row and column (2 rows, 6 columns)
index=0
for row in {0..1}; do
    for col in {0..5}; do
        x=$((col * width))
        y=$((row * height))
        output="${names[$index]}.png"
        
        # Crop the specific piece and save it
        magick -density $density chess_pieces.svg -crop ${width}x${height}+$x+$y +repage "$output"

        ((index++))  # Move to next piece
    done
done

echo "Chess pieces saved as PNGs!"
