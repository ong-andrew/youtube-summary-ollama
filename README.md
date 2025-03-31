# YouTube Transcript Summarizer

A Python script that downloads YouTube video subtitles and uses a local Ollama AI model to generate concise summaries.

## Requirements

- Python 3.6+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) (YouTube downloader)
- [Ollama](https://github.com/ollama/ollama)
- Model with large context window recommended (e.g. gemma3:12b, mistral-nemo)

## Usage

1. If Ollama is not running, start the Ollama service: `ollama serve`
2. Run the script: `python main.py`
3. Enter the YouTube URL when prompted

## Configuration

You can modify these variables at the top of the script:
- `OLLAMA_MODEL`: Ollama model to use (default: "gemma3:12b")
- `PROMPT`: Prompt used to generate summary

## Compatibility

- Works on Linux, should work on macOS with minimal adjustments
- May require additional modifications for Windows

## License

This script is released under the Lanun License.
