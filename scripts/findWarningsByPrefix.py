#!/usr/bin/env python3

import re
import sys
import argparse
import json
import os

# --- Debugging Configuration ---
ENABLE_DEBUG_PRINTING = False
# --- End Debugging Configuration ---

def dprint(*args, **kwargs):
    """Prints debug messages to stderr if ENABLE_DEBUG_PRINTING is True."""
    if ENABLE_DEBUG_PRINTING:
        print("DEBUG:", *args, file=sys.stderr, **kwargs)

# Regex patterns that are common
# 2. Line with a line number like " 12 │" - extract digits
line_number_pattern = re.compile(r"^\s*(\d+)\s*│")

# 3. Line starting with "    └─ " and extracting path and file.
#    e.g., "    └─ lib/elixir_scope/foundation/config.ex:12:3"
#    Extracts "lib/elixir_scope/foundation/config.ex"
#file_path_pattern = re.compile(r"^\s*└─ (.*?):\d+:\d+:")
file_path_pattern = re.compile(r"^\s*└─ (.*?):\d+(?::\d+)?")

def process_lines(lines_iterator, warning_pattern):
    """
    Processes lines from an iterator, identifies warning sequences based on the
    provided warning_pattern, and extracts line numbers and file paths.
    """
    results = []
    state = "SEEK_WARNING"
    current_line_number = None
    active_warning_line_content = None

    for line_raw in lines_iterator:
        line = line_raw.rstrip('\n')
        dprint(f"\nProcessing line: '{line}'")
        dprint(f"  State: {state}, Current LNo: {current_line_number}, Active Warn: '{active_warning_line_content}'")

        # Check if the current line is a new top-level warning using the DYNAMIC warning_pattern
        is_new_warning_line = bool(warning_pattern.match(line))

        if state == "SEEK_FILEPATH":
            dprint("  Attempting SEEK_FILEPATH:")
            match_fp = file_path_pattern.match(line)
            if match_fp:
                file_path = match_fp.group(1)
                dprint(f"    SUCCESS: Matched file path: '{file_path}'")
                results.append({
                    "lineNumber": current_line_number,
                    "fileWithPath": file_path
                })
                dprint(f"    Recorded: {{LNo: {current_line_number}, Path: '{file_path}'}}")
                state = "SEEK_WARNING"
                current_line_number = None
                active_warning_line_content = None
                continue
            elif is_new_warning_line: # If a new target warning starts, reset
                dprint(f"    INTERRUPT: New warning line '{line}' encountered while seeking file path for '{active_warning_line_content}' (LNo: {current_line_number}). Previous sequence aborted.")
                active_warning_line_content = line
                current_line_number = None # Reset line number as it wasn't for this new warning
                state = "SEEK_LINENO" # Start seeking line number for this new warning
                continue
            else:
                dprint(f"    SKIP: No file path match. Line is intermediate or unrelated. Staying in SEEK_FILEPATH.")
                continue

        if state == "SEEK_LINENO":
            dprint("  Attempting SEEK_LINENO:")
            match_ln = line_number_pattern.match(line)
            if match_ln:
                current_line_number = match_ln.group(1)
                dprint(f"    SUCCESS: Matched line number: '{current_line_number}' from line '{line}'")
                state = "SEEK_FILEPATH"
                continue
            elif is_new_warning_line: # If a new target warning starts, reset
                dprint(f"    INTERRUPT: New warning line '{line}' encountered while seeking line number for '{active_warning_line_content}'. Previous sequence aborted.")
                active_warning_line_content = line
                # current_line_number is already None or will be (it wasn't found for the previous warning)
                state = "SEEK_LINENO" # Stay/Set to SEEK_LINENO for this new warning.
                continue
            else:
                dprint(f"    SKIP: No line number match. Line is intermediate or unrelated. Staying in SEEK_LINENO.")
                continue

        if state == "SEEK_WARNING":
            dprint("  Attempting SEEK_WARNING:")
            if is_new_warning_line:
                dprint(f"    SUCCESS: Matched new warning line: '{line}'")
                active_warning_line_content = line
                state = "SEEK_LINENO"
                continue
            else:
                dprint(f"    SKIP: No warning match. Line is unrelated. Staying in SEEK_WARNING.")

    if active_warning_line_content and state != "SEEK_WARNING":
        dprint(f"\nEnd of input. Last warning sequence ('{active_warning_line_content}') was incomplete. Final state: {state}")

    return results

def main():
    parser = argparse.ArgumentParser(
        description="Finds Elixir compiler warnings based on a specified prefix, "
                    "extracts their line numbers and file paths, and outputs JSON.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    # Group for mutually exclusive warning type flags
    warning_type_group = parser.add_mutually_exclusive_group(required=True)
    warning_type_group.add_argument(
        "--undefined-private",
        action="store_true",
        help="Search for '... is undefined or private' warnings."
    )
    warning_type_group.add_argument(
        "--unused-alias",
        action="store_true",
        help="Search for 'unused alias ...' warnings."
    )
    # Add more warning types here if needed in the future by adding to this group

    parser.add_argument(
        "-c", "--text-input",
        metavar="TEXT",
        help="Direct multi-line text input. Useful for small inputs."
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        help="Optional input file to process. Defaults to 'WARNINGS.md' or stdin if piped."
    )
    parser.add_argument(
        "--debug-output",
        action="store_true",
        help="Force enable debug prints to stderr for this run."
    )

    args = parser.parse_args()

    if args.debug_output:
        global ENABLE_DEBUG_PRINTING
        ENABLE_DEBUG_PRINTING = True
        dprint("Debug printing force-enabled by --debug-output flag for this run.")

    # Determine the warning pattern based on the flag
    current_warning_pattern = None
    if args.undefined_private:
        # Must end with "is undefined or private"
        current_warning_pattern = re.compile(r"^\s*warning: .* is undefined or private$")
        dprint("Selected pattern: undefined_private")
    elif args.unused_alias:
        # Must start with "warning: unused alias "
        current_warning_pattern = re.compile(r"^\s*warning: unused alias ")
        dprint("Selected pattern: unused_alias")
    # Add more elif conditions here if new flags are added

    # This should not happen due to `required=True` on the group, but good for safety
    if current_warning_pattern is None:
        parser.error("A warning type flag (e.g., --undefined-private or --unused-alias) must be specified.")


    lines_iterator = None
    input_source_description = ""

    if args.text_input is not None:
        lines_iterator = args.text_input.splitlines()
        input_source_description = "direct text input via --text-input"
        dprint(f"Input source: {input_source_description}")
    elif args.input_file:
        input_source_description = f"file '{args.input_file}'"
        dprint(f"Input source: {input_source_description}")
    elif not sys.stdin.isatty():
        lines_iterator = sys.stdin
        input_source_description = "piped stdin"
        dprint(f"Input source: {input_source_description}")
    elif os.path.exists("WARNINGS.md"):
        input_source_description = "default file 'WARNINGS.md'"
        dprint(f"Input source: {input_source_description}")
    else:
        parser.print_help(sys.stderr)
        print(
            "\nError: No input provided. Please use one of the following methods:\n"
            "1. Provide text directly using the --text-input option.\n"
            "2. Specify an input file as a positional argument.\n"
            "3. Pipe data into the script (e.g., cat warnings.txt | script.py).\n"
            "4. Ensure 'WARNINGS.md' exists in the current directory.",
            file=sys.stderr
        )
        sys.exit(1)

    output_data = []
    if lines_iterator:
        output_data = process_lines(lines_iterator, current_warning_pattern)
    else:
        file_to_read = args.input_file if args.input_file else "WARNINGS.md"
        try:
            dprint(f"Attempting to open and read file: {file_to_read}")
            with open(file_to_read, 'r', encoding='utf-8') as f:
                output_data = process_lines(f, current_warning_pattern)
        except FileNotFoundError:
            print(f"Error: Input {input_source_description} ('{file_to_read}') not found.", file=sys.stderr)
            sys.exit(1)
        except IOError as e:
            print(f"Error reading {input_source_description} ('{file_to_read}'): {e}", file=sys.stderr)
            sys.exit(1)

    print(json.dumps(output_data, indent=2))

if __name__ == "__main__":
    main()
