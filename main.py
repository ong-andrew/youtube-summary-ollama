#!/usr/bin/env python3
# REQUIREMENTS: ollama, yt-dlp
# Install ollama, check: https://github.com/ollama/ollama?tab=readme-ov-file
# Install yt-dlp, check: https://github.com/yt-dlp/yt-dlp?tab=readme-ov-file#installation

import subprocess, os, re, sys, shutil

# --- Configuration ---
PROMPT = "Please provide a detailed summary of the following YouTube video transcript:"
OLLAMA_MODEL = "gemma3:12b" # Recommended model, has 128k context window
TRANSCRIPT_FILENAME = "transcript.srt"
DELETE_TRANSCRIPT_AFTER_SUMMARY = False


class CommandError(Exception):
    """Custom exception for command execution errors."""
    pass

def check_command_exists(command):
    """Checks if a command exists in the system PATH."""
    if shutil.which(command) is None:
        print(f"Error: Required command '{command}' not found in PATH.")
        print("Please install it and ensure it's accessible.")
        sys.exit(1)

def run_command(command_list, step_name, input_data=None):
    """Runs a command using subprocess, handles errors, and returns output."""
    print(f"Running: {' '.join(command_list)}")
    try:
        result = subprocess.run(
            command_list,
            input=input_data,
            capture_output=True,
            text=True,
            encoding='utf-8',
            check=True
        )
        print(f"{step_name} completed successfully.")
        return result
    except FileNotFoundError:
        raise CommandError(f"Command not found: {command_list[0]}. Is it installed and in PATH?")
    except subprocess.CalledProcessError as e:
        error_msg = f"Error during {step_name}: Command exited with status {e.returncode}\n"
        error_msg += f"Command: {' '.join(e.cmd)}\n"
        error_msg += f"STDERR:\n{e.stderr}\n"
        error_msg += f"STDOUT:\n{e.stdout}"
        raise CommandError(error_msg)
    except Exception as e:
        raise CommandError(f"An unexpected error occurred during {step_name}: {e}")

def clean_srt_file(filename):
    """Cleans the SRT file by removing timestamps, sequence numbers, and tags."""
    print(f"Cleaning transcript file: {filename}")
    try:
        # Define regex patterns
        timestamp_pattern = re.compile(r"^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$")
        seq_num_pattern = re.compile(r"^\d+$")
        tag_pattern = re.compile(r"<[^>]*>")

        with open(filename, 'r', encoding='utf-8') as infile:
            lines = infile.readlines()

        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if timestamp_pattern.match(line) or seq_num_pattern.match(line):
                continue

            # Remove tags from the remaining lines
            line = tag_pattern.sub('', line)

            # Add line if it's not empty after cleaning
            if line.strip():
                cleaned_lines.append(line.strip())

        if not cleaned_lines:
            print("Warning: Transcript file is empty after cleaning.")
            return False

        # Write the cleaned content back to the same file
        with open(filename, 'w', encoding='utf-8') as outfile:
            outfile.write("\n".join(cleaned_lines) + "\n")

        print("Transcript cleaning complete.")
        return True

    except FileNotFoundError:
        print(f"Error: Transcript file '{filename}' not found for cleaning.")
        return False
    except IOError as e:
        print(f"Error reading or writing transcript file '{filename}': {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during cleaning: {e}")
        return False


def download_subtitles(youtube_url):
    """Downloads subtitles using yt-dlp."""
    yt_dlp_command = [
        "yt-dlp",
        "--skip-download",
        "--write-subs",
        "--write-auto-subs",
        "--sub-lang", "en",
        "--sub-format", "ttml",
        "--convert-subs", "srt",
        "--output", TRANSCRIPT_FILENAME,
        youtube_url
    ]

    try:
        run_command(yt_dlp_command, "Subtitle Download (yt-dlp)")

        # Handle potential filename variation
        if os.path.exists("transcript.srt.en.srt"):
            os.rename("transcript.srt.en.srt", TRANSCRIPT_FILENAME)

        # Verify file exists and is not empty
        if not os.path.exists(TRANSCRIPT_FILENAME):
            print(f"Error: Subtitle file '{TRANSCRIPT_FILENAME}' was not created.")
            print("Possible reasons: Video unavailable, no English subtitles found, network issue.")
            return False

        if os.path.getsize(TRANSCRIPT_FILENAME) == 0:
            print(f"Error: Subtitle file '{TRANSCRIPT_FILENAME}' is empty.")
            print("No English subtitles were likely found for this video.")
            try:
                os.remove(TRANSCRIPT_FILENAME)
            except OSError:
                pass
            return False

        return True

    except CommandError as e:
        print(e)
        return False


def summarize_transcript():
    """Summarizes transcript using ollama."""
    try:
        with open(TRANSCRIPT_FILENAME, 'r', encoding='utf-8') as f:
            transcript_content = f.read()

        if not transcript_content.strip():
            print("Error: Transcript content is empty after cleaning. Cannot summarize.")
            return False

        # Define the instruction
        

        # Run ollama command
        ollama_command = [
            "ollama",
            "run",
            OLLAMA_MODEL,
            PROMPT
        ]

        print(f"Sending transcript ({len(transcript_content)} bytes) to ollama via stdin...")
        result = run_command(
            ollama_command,
            "Summarization",
            input_data=transcript_content
        )

        print("\n--- Summary ---")
        print(result.stdout.strip())
        print("---------------")
        return True

    except (FileNotFoundError, IOError) as e:
        print(f"Error with transcript file: {e}")
        return False
    except CommandError as e:
        print(e)
        return False
    except Exception as e:
        print(f"An unexpected error occurred during summarization: {e}")
        return False


def stop_ollama_model():
    """Stops the ollama model to free up resources."""
    print(f"\n--- Stopping ollama Model ({OLLAMA_MODEL}) ---")
    try:
        stop_command = [
            "ollama",
            "stop",
            OLLAMA_MODEL
        ]
        run_command(stop_command, f"Stopping ollama Model ({OLLAMA_MODEL})")
        return True
    except CommandError as e:
        print(f"Warning: Could not stop ollama model: {e}")
        return False


def cleanup():
    """Removes transcript file if configured to do so."""
    if DELETE_TRANSCRIPT_AFTER_SUMMARY:
        try:
            os.remove(TRANSCRIPT_FILENAME)
            print(f"Removed transcript file: {TRANSCRIPT_FILENAME}")
        except OSError as e:
            print(f"Warning: Could not remove transcript file '{TRANSCRIPT_FILENAME}': {e}")


def main():
    # Check prerequisites
    print("Checking prerequisites...")
    check_command_exists("yt-dlp")
    check_command_exists("ollama")

    # Check if ollama service is running
    try:
        subprocess.run(["ollama", "ps"], check=True, capture_output=True, timeout=5)
        print("ollama service appears to be running.")
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        print("Warning: Could not confirm ollama service is running. Attempting to proceed...")

    # Get YouTube URL
    youtube_url = input("Please paste Youtube URL: ").strip()
    if not youtube_url:
        print("Error: No URL provided.")
        sys.exit(1)

    # Process the video
    if not download_subtitles(youtube_url):
        sys.exit(1)

    if not clean_srt_file(TRANSCRIPT_FILENAME):
        sys.exit(1)

    if not summarize_transcript():
        sys.exit(1)

    # Stop the ollama model to free resources
    stop_ollama_model()

    cleanup()
    print("\nScript finished successfully.")


if __name__ == "__main__":
    main()
