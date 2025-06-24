#!/usr/bin/env python3

import argparse
import json
import sys
import os

def prepend_to_line_in_file(file_path, line_number_str):
    """
    Prepends '# ' to a specific line in a file.

    Args:
        file_path (str): The path to the file to modify.
        line_number_str (str): The line number (1-indexed) as a string.

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        line_number = int(line_number_str)
        if line_number < 1:
            print(f"Error: Line number '{line_number_str}' for file '{file_path}' is invalid (must be >= 1). Skipping.", file=sys.stderr)
            return False
    except ValueError:
        print(f"Error: Line number '{line_number_str}' for file '{file_path}' is not a valid integer. Skipping.", file=sys.stderr)
        return False

    # Convert to 0-indexed for list access
    line_index = line_number - 1

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        if 0 <= line_index < len(lines):
            # Prepend '# ' to the line.
            # lines[line_index] already includes a newline if it's not the last line without one.
            original_line = lines[line_index]
            
            # Avoid double-commenting if already commented in this specific way
            # This is a simple check, could be made more robust if needed
            if original_line.lstrip().startswith("# "):
                print(f"Info: Line {line_number} in '{file_path}' already starts with '# '. Skipping prepend.", file=sys.stderr)
                return True # Considered successful as the desired state is achieved

            lines[line_index] = f"# {original_line}" # Original newline is preserved

            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print(f"Successfully prepended '# ' to line {line_number} in '{file_path}'", file=sys.stderr)
            return True
        else:
            print(f"Error: Line number {line_number} is out of range for file '{file_path}' (Total lines: {len(lines)}). Skipping.", file=sys.stderr)
            return False

    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found. Skipping.", file=sys.stderr)
        return False
    except IOError as e:
        print(f"Error processing file '{file_path}': {e}. Skipping.", file=sys.stderr)
        return False
    except Exception as e:
        print(f"An unexpected error occurred while processing '{file_path}' at line {line_number}: {e}. Skipping.", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Parses JSON input (list of objects with 'fileWithPath' and 'lineNumber') "
                    "and prepends '# ' to the specified lines in the files.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "-c", "--text-input",
        metavar="JSON_TEXT",
        help="Direct JSON string input. Useful for small inputs. \n"
             "Example: python prependComment.py -c '[{\"lineNumber\":\"37\", \"fileWithPath\": \"file.ex\"}]'"
    )
    parser.add_argument(
        "input_file",
        nargs="?", # Makes the argument optional
        help="Optional input JSON file to process. \n"
             "If not specified, and no data is piped or provided via --text-input, "
             "the script will expect input from stdin."
    )

    args = parser.parse_args()

    json_input_str = None
    input_source_description = ""

    if args.text_input is not None:
        json_input_str = args.text_input
        input_source_description = "direct text input via --text-input"
    elif args.input_file:
        try:
            with open(args.input_file, 'r', encoding='utf-8') as f:
                json_input_str = f.read()
            input_source_description = f"file '{args.input_file}'"
        except FileNotFoundError:
            print(f"Error: Input file '{args.input_file}' not found.", file=sys.stderr)
            sys.exit(1)
        except IOError as e:
            print(f"Error reading input file '{args.input_file}': {e}", file=sys.stderr)
            sys.exit(1)
    elif not sys.stdin.isatty(): # Check for piped input
        json_input_str = sys.stdin.read()
        input_source_description = "piped stdin"
    else:
        parser.print_help(sys.stderr)
        print(
            "\nError: No JSON input provided. Please use one of the following methods:\n"
            "1. Provide JSON text directly using the --text-input option.\n"
            "2. Specify an input JSON file as a positional argument.\n"
            "3. Pipe JSON data into the script (e.g., cat data.json | script.py).",
            file=sys.stderr
        )
        sys.exit(1)

    if not json_input_str or json_input_str.strip() == "":
        print(f"Error: Received empty input from {input_source_description}. No operations performed.", file=sys.stderr)
        sys.exit(1)
        
    try:
        data_to_process = json.loads(json_input_str)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON received from {input_source_description}: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data_to_process, list):
        print(f"Error: Expected JSON input to be a list of objects, but got {type(data_to_process)}.", file=sys.stderr)
        sys.exit(1)

    modified_count = 0
    error_count = 0

    for item in data_to_process:
        if not isinstance(item, dict):
            print(f"Warning: Skipping non-dictionary item in JSON list: {item}", file=sys.stderr)
            error_count +=1
            continue

        file_path = item.get("fileWithPath")
        line_number_str = item.get("lineNumber")

        if not file_path or not line_number_str:
            print(f"Warning: Skipping item due to missing 'fileWithPath' or 'lineNumber': {item}", file=sys.stderr)
            error_count +=1
            continue
        
        if prepend_to_line_in_file(file_path, line_number_str):
            modified_count += 1
        else:
            error_count += 1
    
    print(f"\nProcessing complete. Successfully modified lines in {modified_count} instances.", file=sys.stderr)
    if error_count > 0:
        print(f"Encountered {error_count} errors or skipped items. See messages above for details.", file=sys.stderr)
        sys.exit(1) # Exit with error code if there were issues

if __name__ == "__main__":
    main()
