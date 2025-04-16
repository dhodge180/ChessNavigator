#!/usr/bin/bash

# Names of the chess pieces in order
names=("wG" "bG")

# Desired final sizes (in pixels)
final_sizes=(40 50 60 70 80 90 100)

# Loop through each SVG file in the names array
for name in "${names[@]}"; do
    # Loop through each desired final size
    for size in "${final_sizes[@]}"; do
        # Define the output file name
        output="${name}_${size}px.png"

        # Convert the SVG to PNG with the correct size while maintaining transparency
	cairosvg --output-width $size --output-width $size -o "$output" "${name}.svg"

        echo "Converted ${name}.svg to $output at $size px"
    done
done
