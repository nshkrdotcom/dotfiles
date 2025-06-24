#!/usr/bin/env python3

import argparse
import subprocess
import os
import sys
import json # For validating JSON from findWarningsByPrefix

# --- Configuration ---
SCRIPTS_DIR = os.path.expanduser("~/scripts")
SAVE_WARNINGS_SCRIPT = os.path.join(SCRIPTS_DIR, "saveWarnings.py")
FIND_WARNINGS_SCRIPT = os.path.join(SCRIPTS_DIR, "findWarningsByPrefix.py")
PREPEND_COMMENT_SCRIPT = os.path.join(SCRIPTS_DIR, "prependComment.py")

ENABLE_DEBUG_PRINTING = False # Global debug flag
# --- End Configuration ---

def dprint(*args, **kwargs):
    """Prints debug messages to stderr if ENABLE_DEBUG_PRINTING is True."""
    if ENABLE_DEBUG_PRINTING:
        print("DEBUG:", *args, file=sys.stderr, **kwargs)

def check_script_exists(script_path):
    """Checks if a script exists and is executable."""
    if not os.path.isfile(script_path):
        print(f"Error: Required script not found: {script_path}", file=sys.stderr)
        return False
    if not os.access(script_path, os.X_OK):
        print(f"Error: Required script is not executable: {script_path}", file=sys.stderr)
        return False
    return True

def run_script_capture_output(script_path, script_args=None, input_data=None):
    """
    Runs a script, optionally providing input_data to its stdin,
    and returns its stdout, stderr, and return code.
    """
    command = [script_path]
    if script_args:
        command.extend(script_args)

    dprint(f"Running command: {' '.join(command)}")
    if input_data:
        dprint(f"  With input data (first 100 chars): {input_data[:100].replace(os.linesep, ' ')}...")

    try:
        process = subprocess.run(
            command,
            input=input_data,
            capture_output=True,
            text=True, # Decodes stdout/stderr to strings
            check=False # We'll check returncode manually for better error messages
        )
        dprint(f"  Return code: {process.returncode}")
        if process.stdout:
            dprint(f"  Stdout (first 100 chars): {process.stdout[:100].replace(os.linesep, ' ')}...")
        if process.stderr:
            dprint(f"  Stderr (first 100 chars): {process.stderr[:100].replace(os.linesep, ' ')}...")
        return process.stdout, process.stderr, process.returncode
    except FileNotFoundError:
        print(f"Error: Command not found: {script_path}. Is it in your PATH or script path correct?", file=sys.stderr)
        return None, None, -1 # Indicate a fundamental error
    except Exception as e:
        print(f"An unexpected error occurred while trying to run {script_path}: {e}", file=sys.stderr)
        return None, None, -1


def main():
    global ENABLE_DEBUG_PRINTING # Allow main to modify the global
    parser = argparse.ArgumentParser(
        description="Orchestrates fixing Elixir compiler warnings by commenting them out.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    warning_type_group = parser.add_mutually_exclusive_group(required=True)
    warning_type_group.add_argument(
        "-a", "--aliases",
        action="store_true",
        help="Fix 'unused alias' warnings."
    )
    warning_type_group.add_argument(
        "-u", "--undefined",
        action="store_true",
        help="Fix '... is undefined or private' warnings."
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable detailed debug output for the orchestration script."
    )

    args = parser.parse_args()

    if args.debug:
        ENABLE_DEBUG_PRINTING = True
        dprint("Debug printing enabled for warnFix.py")

    # --- Validate that all required scripts exist and are executable ---
    required_scripts = [SAVE_WARNINGS_SCRIPT, FIND_WARNINGS_SCRIPT, PREPEND_COMMENT_SCRIPT]
    for script_path in required_scripts:
        if not check_script_exists(script_path):
            sys.exit(1)

    # --- Step 1: Run saveWarnings.py to get compiler output ---
    print("--- Step 1: Getting compiler warnings ---", file=sys.stderr)
    # Assumption: saveWarnings.py prints the raw `mix compile` output to its stdout.
    #             If it also saves to a file, that's fine, but we use its stdout.
    compiler_output_str, save_err, save_rc = run_script_capture_output(SAVE_WARNINGS_SCRIPT)

    if save_rc != 0 or compiler_output_str is None: # compiler_output_str is None if fundamental error
        print(f"Error: {SAVE_WARNINGS_SCRIPT} failed or did not produce output.", file=sys.stderr)
        if save_err:
            print(f"Stderr from {SAVE_WARNINGS_SCRIPT}:\n{save_err.strip()}", file=sys.stderr)
        sys.exit(1)
    
    if not compiler_output_str.strip():
        print("Info: No compiler output (warnings/errors) received from `mix compile` via saveWarnings.py.", file=sys.stderr)
        print("Exiting successfully as there's nothing to process.", file=sys.stderr)
        sys.exit(0)

    dprint(f"Raw compiler output received (length: {len(compiler_output_str)})")

    # --- Step 2: Run findWarningsByPrefix.py to get JSON ---
    print("\n--- Step 2: Identifying target warnings ---", file=sys.stderr)
    find_script_flag = None
    if args.aliases:
        find_script_flag = "--unused-alias"
    elif args.undefined:
        find_script_flag = "--undefined-private"

    json_output_str, find_err, find_rc = run_script_capture_output(
        FIND_WARNINGS_SCRIPT,
        script_args=[find_script_flag],
        input_data=compiler_output_str
    )

    if find_rc != 0 or json_output_str is None:
        print(f"Error: {FIND_WARNINGS_SCRIPT} failed.", file=sys.stderr)
        if find_err:
            print(f"Stderr from {FIND_WARNINGS_SCRIPT}:\n{find_err.strip()}", file=sys.stderr)
        sys.exit(1)

    dprint(f"JSON output received from findWarningsByPrefix.py (length: {len(json_output_str)})")

    # Validate the JSON and check if it's an empty list (no warnings found)
    try:
        parsed_json = json.loads(json_output_str)
        if isinstance(parsed_json, list) and not parsed_json:
            print(f"Info: No '{find_script_flag.replace('--','')}' warnings found by {FIND_WARNINGS_SCRIPT}.", file=sys.stderr)
            print("Exiting successfully as there's nothing to fix.", file=sys.stderr)
            sys.exit(0)
    except json.JSONDecodeError:
        print(f"Error: Output from {FIND_WARNINGS_SCRIPT} was not valid JSON.", file=sys.stderr)
        print(f"Received:\n{json_output_str}", file=sys.stderr)
        if find_err:
            print(f"Stderr from {FIND_WARNINGS_SCRIPT}:\n{find_err.strip()}", file=sys.stderr)
        sys.exit(1)


    # --- Step 3: Run prependComment.py to modify files ---
    print("\n--- Step 3: Commenting out warnings in source files ---", file=sys.stderr)
    _, prepend_err, prepend_rc = run_script_capture_output(
        PREPEND_COMMENT_SCRIPT,
        input_data=json_output_str
    )

    if prepend_rc != 0:
        print(f"Error: {PREPEND_COMMENT_SCRIPT} encountered issues.", file=sys.stderr)
        # prependComment.py prints its own detailed errors to stderr,
        # so we just print its captured stderr if any *additional* info is there.
        if prepend_err:
            print(f"Additional Stderr from {PREPEND_COMMENT_SCRIPT} (if any):\n{prepend_err.strip()}", file=sys.stderr)
        sys.exit(1)
    
    # If prependComment.py also prints success messages to its stdout, we might want to show them.
    # For now, assume its stderr is sufficient for status.

    print("\n--- Warning Fix Pipeline Completed Successfully ---", file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    main()
