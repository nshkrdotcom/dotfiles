#!/usr/bin/env python3
import subprocess
import sys

def run_mix_compile_and_output_to_stdout():
    command = ["mix", "compile"]
    try:
        process = subprocess.run(
            command,
            capture_output=True, # Capture both stdout and stderr of mix compile
            text=True,
            check=False # Don't raise exception on non-zero exit, let warnFix handle
        )
        # Combine stdout and stderr from `mix compile`
        combined_output = ""
        if process.stdout:
            combined_output += process.stdout
        if process.stderr:
            if process.stdout and process.stderr.strip(): # Add separator if both have content
                 combined_output += "\n--- STDERR (from mix compile) ---\n"
            combined_output += process.stderr
        
        sys.stdout.write(combined_output) # Write to this script's stdout
        return process.returncode

    except FileNotFoundError:
        print(f"Error (saveWarnings.py): 'mix' command not found.", file=sys.stderr)
        return -1 # Indicate specific error
    except Exception as e:
        print(f"Error (saveWarnings.py): {e}", file=sys.stderr)
        return -2 # Indicate other error

if __name__ == "__main__":
    exit_code = run_mix_compile_and_output_to_stdout()
    # The orchestrator (warnFix.py) will check the exit code
    # This script itself should exit with the code from mix compile,
    # or a custom code if it had an internal error before running mix.
    sys.exit(exit_code if exit_code >=0 else 1) # Ensure non-negative exit for subprocess, or 1 for internal script error
