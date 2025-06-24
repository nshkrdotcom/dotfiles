#!/bin/bash

# Script: find_large_ex_files.sh
# Description: Finds all files ending in '.ex' that have more than a specified
#              number of lines, displays the line count, and sorts the results.
# Usage: ./find_large_ex_files.sh [MIN_LINES]
#   MIN_LINES: The minimum number of lines a file must have to be included.
#              Defaults to 500 if not provided.

# --- Configuration ---
# Set the default minimum line count if no argument is provided
MIN_LINES=${1:-500}

# --- Script Logic ---
echo "Searching for files ending in '.ex' with more than $MIN_LINES lines..."
echo "---------------------------------------------------------------------"

# Use find to locate files, execute a bash subshell for each file:
# 1. Count the lines in the file using 'wc -l'.
# 2. Check if the line count exceeds the MIN_LINES threshold.
# 3. If it does, print the line count followed by the filename.
# The output of all these commands is then piped to 'sort -n' to sort numerically.
find . -name "*.ex" -exec bash -c '
    # Assign the current file path from find (which is $1 in the subshell)
    file_path="$1"
    # Assign the minimum lines threshold passed as the second argument ($2)
    min_lines_threshold="$2"

    # Count the lines in the file. Using "< $file_path" prevents wc from
    # printing the filename itself, giving us just the number.
    line_count=$(wc -l < "$file_path")

    # Check if the counted lines are greater than the threshold
    if (( line_count > min_lines_threshold )); then
        # Print the line count and the file path, separated by a space.
        # This format is ideal for numerical sorting.
        echo "$line_count $file_path"
    fi
' _ {} "$MIN_LINES" \; | sort -n

echo "---------------------------------------------------------------------"
echo "Search complete."
