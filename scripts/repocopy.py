#!/usr/bin/env python3

import os
import sys
import subprocess
import tempfile

# Define the options
OPTIONS = [
    ["lib", "test"],
    ["lib", "priv/python", "priv/proto", "examples"]
]

def run_repomix_for_dirs(dirs):
    """Run repomix for each directory and combine outputs"""
    combined_content = ""
    original_cwd = os.getcwd()
    
    for dir_name in dirs:
        dir_path = os.path.join(original_cwd, dir_name)
        if not os.path.exists(dir_path):
            print(f"Warning: Directory '{dir_name}' does not exist, skipping...")
            continue
            
        print(f"Processing {dir_name}...")
        
        # Change to the subdirectory
        os.chdir(dir_path)
        
        # Run repomix
        try:
            print(f"  Running repomix...")
            result = subprocess.run(["repomix"], check=True, capture_output=True, timeout=60)
            if result.stderr:
                print(f"  Repomix stderr: {result.stderr.decode()}")
            
            # Find the repomix output file (usually repomix-output.xml or repomix-output.md)
            repomix_file = None
            for file in os.listdir('.'):
                if file.startswith('repomix') and (file.endswith('.md') or file.endswith('.xml')):
                    repomix_file = file
                    break
            
            if repomix_file:
                # Read the content
                print(f"  Found output file: {repomix_file}")
                with open(repomix_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                combined_content += f"\n\n# === ./{dir_name}/ ===\n\n{content}"
                
                # Remove the file
                os.remove(repomix_file)
                print(f"  Success!")
            else:
                print(f"Warning: Could not find repomix output file in {dir_name}")
                
        except subprocess.TimeoutExpired:
            print(f"  Timeout: Repomix took too long in {dir_name}")
        except subprocess.CalledProcessError as e:
            print(f"  Error running repomix in {dir_name}: {e}")
            if e.stderr:
                print(f"  stderr: {e.stderr.decode()}")
        except Exception as e:
            print(f"  Unexpected error in {dir_name}: {e}")
        
        # Change back to original directory
        os.chdir(original_cwd)
    
    return combined_content

def send_to_clipboard(content):
    """Send content to clipboard"""
    try:
        # Check if we're in WSL
        is_wsl = subprocess.run(['uname', '-r'], capture_output=True, text=True).stdout.lower().find('microsoft') != -1
        
        if is_wsl:
            # Use clip.exe for WSL
            process = subprocess.Popen(['clip.exe'], 
                                       stdin=subprocess.PIPE, 
                                       stdout=subprocess.PIPE, 
                                       stderr=subprocess.PIPE)
            stdout, stderr = process.communicate(input=content.encode(), timeout=5)
            
            if process.returncode != 0:
                print(f"Error copying to clipboard: {stderr.decode()}")
                return False
            return True
        else:
            # Use xclip for native Linux
            process = subprocess.Popen(['xclip', '-selection', 'clipboard'], 
                                       stdin=subprocess.PIPE, 
                                       stdout=subprocess.PIPE, 
                                       stderr=subprocess.PIPE)
            stdout, stderr = process.communicate(input=content.encode(), timeout=5)
            
            if process.returncode != 0:
                print(f"Error copying to clipboard: {stderr.decode()}")
                return False
            return True
    except subprocess.TimeoutExpired:
        process.kill()
        print("Timeout: Clipboard operation took too long")
        # Save to temp file as fallback
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                f.write(content)
                temp_path = f.name
            print(f"Content saved to temporary file: {temp_path}")
            print(f"You can copy it manually with: cat {temp_path} | copy")
            return False
        except Exception as e:
            print(f"Failed to save to temp file: {e}")
            return False
    except Exception as e:
        print(f"Error copying to clipboard: {e}")
        return False

def main():
    # Check if an argument was provided
    if len(sys.argv) > 1:
        try:
            option_num = int(sys.argv[1])
            if 1 <= option_num <= len(OPTIONS):
                selected_dirs = OPTIONS[option_num - 1]
            else:
                print(f"Error: Option must be between 1 and {len(OPTIONS)}")
                sys.exit(1)
        except ValueError:
            print("Error: Argument must be a number")
            sys.exit(1)
    else:
        # Interactive mode
        print("Select an option:")
        for i, option in enumerate(OPTIONS, 1):
            print(f"{i}. {', '.join(option)}")
        
        try:
            choice = input("\nEnter option number: ")
            option_num = int(choice)
            if 1 <= option_num <= len(OPTIONS):
                selected_dirs = OPTIONS[option_num - 1]
            else:
                print(f"Error: Option must be between 1 and {len(OPTIONS)}")
                sys.exit(1)
        except (ValueError, KeyboardInterrupt):
            print("\nInvalid input or cancelled")
            sys.exit(1)
    
    # Run repomix for selected directories
    print(f"\nProcessing directories: {', '.join(selected_dirs)}")
    combined_content = run_repomix_for_dirs(selected_dirs)
    
    if combined_content:
        # Show content size
        content_size = len(combined_content)
        print(f"\nTotal content size: {content_size:,} characters")
        
        # Send to clipboard
        print("Copying to clipboard...")
        if send_to_clipboard(combined_content):
            print("Content copied to clipboard!")
        else:
            print("Failed to copy to clipboard")
    else:
        print("\nNo content to copy")

if __name__ == "__main__":
    main()