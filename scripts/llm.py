#!/usr/bin/env python3

# Ported script using the new genai.Client API spec.

# Original google.genai import:
# import google.genai as genai

# New google.genai import (based on spec provided):
from google import genai
# Note: The spec also shows "from google.genai import types" if GenerateContentConfig is used.
# This script does not use GenerateContentConfig as the original script didn't have equivalent functionality.

import os
import sys
import argparse

# --- Configuration ---
# These are the model aliases from your original script.
# You noted them as hypothetical and to confirm availability.
# For this port, we are keeping your defined model names.
# The new API might expect different model name formats or aliases,
# so these might need adjustment based on available models with the new SDK.
DEFAULT_MODEL = "gemini-2.5-flash-lite-preview-06-17"
#DEFAULT_MODEL = "models/gemini-2.5-pro"
FLASH_MODEL = "models/gemini-2.5-flash-lite-preview-06-17"
PRO_MODEL = "models/gemini-2.5-pro"

def main():
    parser = argparse.ArgumentParser(
        description="Query Google Gemini models. "
                    "Reads prompt from stdin or command line arguments."
    )
    parser.add_argument(
        '--pro',
        action='store_true',
        help=f"Use the Gemini Pro model ({PRO_MODEL}) instead of Flash ({DEFAULT_MODEL})."
    )
    parser.add_argument(
        'prompt_parts',
        nargs='*',
        help="The prompt text. If not provided, reads from stdin."
    )
    args = parser.parse_args()

    # 1. Initialize API Client
    client = None
    try:
        api_key = os.environ["GEMINI_API_KEY"]
        # Original SDK initialization: genai.configure(api_key=api_key)
        client = genai.Client(api_key=api_key) # New way to initialize with API key
    except KeyError:
        print("Error: The GEMINI_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error initializing GenAI Client: {e}", file=sys.stderr)
        sys.exit(1)

    # 2. Determine Model
    model_name = PRO_MODEL if args.pro else DEFAULT_MODEL
    print(f"Using model: {model_name}", file=sys.stderr)

    # 3. Get Prompt
    prompt = ""
    if not sys.stdin.isatty():  # Check if data is being piped
        prompt = sys.stdin.read().strip()
        if args.prompt_parts: # If both pipe and args, append args to piped input
            prompt += " " + " ".join(args.prompt_parts)
            print("Warning: Received prompt from both stdin and arguments. Concatenating.", file=sys.stderr)
    elif args.prompt_parts:
        prompt = " ".join(args.prompt_parts)
    
    if not prompt:
        print("Error: No prompt provided.", file=sys.stderr)
        parser.print_help(file=sys.stderr)
        sys.exit(1)

    # print(f"Prompt: \"{prompt}\"", file=sys.stderr) # For debugging

    # 4. Generate Content (Streaming)
    try:
        # Original model initialization:
        # model = genai.GenerativeModel(model_name)
        # Original generation call:
        # response_stream = model.generate_content(prompt, stream=True)

        # New API call for streaming generation:
        # The 'contents' parameter expects an iterable (e.g., a list).
        # For a simple text prompt, it's a list containing one string.
        response_stream = client.models.generate_content_stream(
            model=model_name,
            contents=[prompt] 
        )

        for chunk in response_stream:
            # The original script checked 'if chunk.text:' to handle cases where
            # chunk.text might be None or an empty string. This also helps
            # avoid issues if chunk itself was None (which would be caught by the AttributeError below).
            # This check is good for robustness and kept from the original script.
            # The 'flush=True' is also kept for better interactive terminal output.
            if chunk.text: 
                print(chunk.text, end="", flush=True)
        print() # Add a final newline for cleaner terminal output

    except AttributeError as e:
        # This specific error handling for AttributeError was present in the original script.
        # It suggests that 'chunk' could be None, or 'chunk.text' might be unexpectedly
        # absent or lead to this error (e.g., if chunk.parts is empty or malformed).
        if "'NoneType' object has no attribute 'text'" in str(e):
            print("\nWarning: Received an empty or malformed response part from the API.", file=sys.stderr)
            print("This might happen due to safety filters or an unusual API response structure.", file=sys.stderr)
            # Original script did not exit for this specific warning, so we maintain that behavior.
        else:
            # For other AttributeErrors, the original script treated them as more critical.
            print(f"\nAn AttributeError occurred: {e}", file=sys.stderr)
            print("This might be due to an issue with the model, prompt, or API response structure.", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        # General error handling for API calls or other issues during generation.
        # The specific types of exceptions raised might differ with the new SDK.
        print(f"\nAn error occurred while generating content: {e}", file=sys.stderr)
        # The original script mentioned inspecting `response.prompt_feedback` for non-streaming.
        # For streaming, error details are typically in the exception `e`.
        # The new API spec provided doesn't detail error object structure for streaming in this snippet.
        sys.exit(1)

if __name__ == "__main__":
    main()
