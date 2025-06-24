#!/usr/bin/env python3

import subprocess
import os
import sys

# --- Configuration ---
DEFAULT_OUTPUT_FILENAME = "my_warnings.txt" # It can still save to a file if desired
# --- End Configuration ---

def run_mix_compile_and_handle_output(output_file_path_for_saving=None):
    """
    Runs 'mix compile', prints its combined stdout/stderr to THIS script's stdout,
    and optionally saves it to a file.

    Args:
        output_file_path_for_saving (str, optional): Path to save the output.
                                                     If None, only prints to stdout.

    Returns:
        int: The return code of the 'mix compile' process.
             Returns a negative number if the script itself had an error
             before or during running 'mix compile'.
    """
    command = ["mix", "compile"]
    # Informative message to stderr for the direct user of saveWarnings.py
    print(f"saveWarnings.py: Running command: {' '.join(command)}", file=sys.stderr)

    try:
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False # We handle the return code
        )

        combined_output = ""
        if process.stdout:
            combined_output += process.stdout
        if process.stderr:
            # Optional: Add a separator if both stdout and stderr from mix compile have content
            # if process.stdout and process.stderr.strip():
            #      combined_output += "\n--- STDERR (from mix compile) ---\n"
            combined_output += process.stderr

        # --- CRITICAL CHANGE: Print combined_output to this script's stdout ---
        sys.stdout.write(combined_output)
        # --- END CRITICAL CHANGE ---

        # Optional: Still print to stderr for direct user feedback
        print(f"\nsaveWarnings.py: --- 'mix compile' Output (also sent to stdout) ---", file=sys.stderr)
        if combined_output.strip():
             print(combined_output, file=sys.stderr)
        else:
            print("saveWarnings.py: (No output from 'mix compile')", file=sys.stderr)
        print(f"saveWarnings.py: --- End 'mix compile' Output ---", file=sys.stderr)

        # Optional: Still save to a file
        if output_file_path_for_saving:
            try:
                with open(output_file_path_for_saving, 'w', encoding='utf-8') as f:
                    f.write(combined_output)
                print(f"saveWarnings.py: Successfully saved 'mix compile' output to '{output_file_path_for_saving}'", file=sys.stderr)
            except IOError as e:
                print(f"saveWarnings.py: Error saving output to file '{output_file_path_for_saving}': {e}", file=sys.stderr)
                # Continue, as the main goal (stdout) was achieved.

        if process.returncode == 0:
            print(f"saveWarnings.py: 'mix compile' completed successfully (exit code {process.returncode}).", file=sys.stderr)
        else:
            print(f"saveWarnings.py: Warning: 'mix compile' finished with a non-zero exit code: {process.returncode}.", file=sys.stderr)
        
        return process.returncode # Return the exit code of 'mix compile'

    except FileNotFoundError:
        print(f"saveWarnings.py: Error: The 'mix' command was not found. Is Elixir installed and in your PATH?", file=sys.stderr)
        return -1 # Indicate script's own error
    except Exception as e:
        print(f"saveWarnings.py: An error occurred: {e}", file=sys.stderr)
        return -2 # Indicate script's own error

def main():
    pwd = os.getcwd()
    # Decide if you want saveWarnings.py to always save a file, or only print to stdout
    # For fixWarnings.py, we only *need* stdout. Saving the file here is optional.
    default_file_to_save = os.path.join(pwd, DEFAULT_OUTPUT_FILENAME)
    
    # Pass the file path if you want it to save, or None if only stdout is needed by default
    # For clarity, let's make it always attempt to save the file as it did before,
    # but the crucial part is that it *also* prints to stdout.
    exit_code = run_mix_compile_and_handle_output(output_file_path_for_saving=default_file_to_save)
    
    sys.exit(exit_code if exit_code >= 0 else 1) # exit with mix compile's code, or 1 for script error

if __name__ == "__main__":
    main()
