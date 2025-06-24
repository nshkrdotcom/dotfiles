#!/bin/bash

# --- Script Configuration ---
# Set to 'true' to use color, 'false' for monochrome.
# Requires a terminal that supports ANSI color codes.
USE_COLOR=true

# --- Helper Functions ---

# Function to format bytes into a human-readable format (KB, MB, GB...)
# Uses `numfmt` if available for accuracy, otherwise falls back to a simple awk calculation.
format_size() {
    local bytes=$1
    if command -v numfmt &> /dev/null; then
        # Use GNU numfmt for precise, standard formatting
        numfmt --to=iec-i --suffix=B --format="%.1f" "$bytes"
    else
        # Fallback for systems without numfmt (e.g., macOS by default)
        awk -v b="$bytes" 'BEGIN{
            s="B"; if(b>=1024){s="KB"; b/=1024} if(b>=1024){s="MB"; b/=1024} if(b>=1024){s="GB"; b/=1024}
            printf "%.1f%s", b, s
        }'
    fi
}

# The core recursive function to process a directory
# Arguments:
#   $1: directory_path
#   $2: prefix_string (for indentation)
#   $3: is_last_dir (boolean: "true" or "false")
process_directory() {
    local dir_path="$1"
    local prefix="$2"
    local is_last="$3"

    # --- 1. Calculate and format size summary for files in the current directory ---
    local summary
    # The heart of the size calculation:
    # find: gets size and filename for files (-maxdepth 1) in the current directory.
    # awk: sums the sizes for each unique extension.
    # sort: sorts the extensions alphabetically for consistent output.
    summary=$(find "$dir_path" -maxdepth 1 -type f -printf "%s %f\n" 2>/dev/null |
        awk '
        {
            size = $1
            filename = $2
            ext = ".<no_ext>"
            if (match(filename, /\.[^./]+$/)) {
                ext = substr(filename, RSTART)
            }
            total[ext] += size
        }
        END {
            for (e in total) {
                print total[e], e
            }
        }' | sort -k2)

    local summary_string=""
    if [[ -n "$summary" ]]; then
        local parts=()
        while read -r size ext; do
            formatted_size=$(format_size "$size")
            parts+=("$formatted_size $ext")
        done <<< "$summary"
        summary_string="($(IFS=, ; echo "${parts[*]}"))"
    fi

    # --- 2. Print the current directory's line ---
    local dir_name
    dir_name=$(basename "$dir_path")

    # Use color if enabled
    local c_dir="" c_size="" c_reset=""
    if [ "$USE_COLOR" = true ]; then
        c_dir=$'\e[1;34m'  # Bold Blue for directories
        c_size=$'\e[0;32m' # Green for size summary
        c_reset=$'\e[0m'
    fi

    echo "${prefix}${c_dir}./${dir_name}${c_reset} ${c_size}${summary_string}${c_reset}"


    # --- 3. Recurse into subdirectories ---
    local subdirs
    # Read subdirectories into an array to determine the last one
    # The `|| true` prevents the script from exiting if find returns no results
    subdirs=($(find "$dir_path" -maxdepth 1 -mindepth 1 -type d 2>/dev/null | sort || true))
    local num_subdirs=${#subdirs[@]}

    for i in "${!subdirs[@]}"; do
        local subdir="${subdirs[$i]}"
        local new_prefix
        local is_last_subdir="false"

        # Determine the correct prefix characters (├── or └──)
        if (( i == num_subdirs - 1 )); then
            new_prefix="${prefix}    "
            is_last_subdir="true"
            echo "${prefix}└──" | tr -d '\n' # Print the branch and stay on the same line
        else
            new_prefix="${prefix}│   "
            echo "${prefix}├──" | tr -d '\n' # Print the branch and stay on the same line
        fi
        process_directory "$subdir" "$new_prefix" "$is_last_subdir"
    done
}


# --- Main Script Logic ---

# Check for correct number of arguments
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <directory1> <directory2>"
    echo "Compares two directory trees, showing file size summaries by extension."
    exit 1
fi

DIR1="$1"
DIR2="$2"

# Check if arguments are actual directories
if [ ! -d "$DIR1" ]; then
    echo "Error: '$DIR1' is not a valid directory."
    exit 1
fi
if [ ! -d "$DIR2" ]; then
    echo "Error: '$DIR2' is not a valid directory."
    exit 1
fi

# Use secure temporary files for the output of each tree
TMP1=$(mktemp)
TMP2=$(mktemp)

# Ensure temporary files are cleaned up on script exit (even if interrupted)
trap 'rm -f "$TMP1" "$TMP2"' EXIT

# Process each directory and send its output to the corresponding temp file
process_directory "$DIR1" "" "true" > "$TMP1"
process_directory "$DIR2" "" "true" > "$TMP2"

# Use `paste` to merge the two files side-by-side for comparison
# Use `pr` to expand tabs to spaces and set a wide page width to prevent wrapping
echo
pr -t -e4 -w160 <(paste -d'|' "$TMP1" "$TMP2")
echo
